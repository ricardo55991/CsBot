import json
import os
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
SERVER_DIR = Path(r"H:\CS2_AI_Server")
CS2_EXE = SERVER_DIR / "game" / "bin" / "win64" / "cs2.exe"
PLUGIN_LOGS = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "logs"
CANARY_JSONL = PLUGIN_LOGS / "opening_canary_telemetry.jsonl"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "tr_live_route_certification_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROUTES = [
    ("palace_certification_metrics.json", "a_palace_deep_room"),
    ("a_ramp_certification_metrics.json", "tr_a_ramp_staging_wait"),
    ("b_kitchen_certification_metrics.json", "tr_b_apps_kitchen_control"),
    ("b_house_certification_metrics.json", "tr_b_apps_house_staging"),
]


def kill_cs2():
    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)


def run_solo_route(route_id: str, target_rounds: int = 10, max_wait_s: int = 600):
    kill_cs2()
    if CANARY_JSONL.exists():
        CANARY_JSONL.unlink()

    env = os.environ.copy()
    env["CSBOT_OPENING_CANARY_MODE"] = "TR"
    env["CSBOT_TR_SOLO_CERT_ROUTE"] = route_id

    args = [
        str(CS2_EXE),
        "-dedicated", "-usercon", "-port", "27015",
        "+game_type", "0", "+game_mode", "1", "+map", "de_mirage",
        "+sv_cheats", "1",
        "+mp_autoteambalance", "0", "+mp_limitteams", "0",
        "+bot_quota", "1", "+bot_quota_mode", "normal", "+bot_join_team", "t",
        "+mp_ignore_round_win_conditions", "1",
        "+mp_roundtime", "0.50", "+mp_freezetime", "2", "+mp_round_restart_delay", "1",
        "+mp_warmup_end",
    ]
    proc = subprocess.Popen(args, cwd=str(SERVER_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    seen_rounds = {}
    try:
        while time.time() - t0 < max_wait_s:
            time.sleep(10)
            if CANARY_JSONL.exists():
                by_rnd = defaultdict(list)
                with CANARY_JSONL.open("r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except Exception:
                            continue
                        if rec.get("round"):
                            by_rnd[rec["round"]].append(rec)
                seen_rounds = {r: recs[-1].get("arrival_status", "PENDING") for r, recs in by_rnd.items()}
                finished_cnt = sum(1 for r, recs in by_rnd.items() if recs[-1].get("executor_state") in ("DESTINATION_REACHED", "FALLBACK", "INTERRUPTED", "ABORTED") or recs[-1].get("arrival_status") != "PENDING")
                print(f"[2B.8.7 SOLO {route_id}] elapsed={int(time.time()-t0)}s rounds={len(by_rnd)} finished={finished_cnt} statuses={seen_rounds}", flush=True)
                if len(by_rnd) >= target_rounds and finished_cnt >= target_rounds:
                    break
                if len(by_rnd) > target_rounds:
                    break
    finally:
        kill_cs2()

    lines = []
    if CANARY_JSONL.exists():
        with CANARY_JSONL.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    lines.append(line.strip())
    return lines


def analyze_route(route_id: str, lines: list[str], out_name: str):
    by_rnd = defaultdict(list)
    for line in lines:
        rec = json.loads(line)
        r = rec.get("round")
        if r:
            by_rnd[r].append(rec)

    sessions = []
    root_causes = []
    for r in sorted(by_rnd.keys())[:10]:
        recs = by_rnd[r]
        last = recs[-1]
        status = last.get("arrival_status", "PENDING")
        reason = last.get("completion_reason", "")
        exp_d = float(last.get("expected_distance", 0) or 0)
        trav_d = float(last.get("traveled_distance", 0) or 0)
        detour = round(trav_d / exp_d, 4) if exp_d > 0 else 0.0
        arrived = status in ("ON_TIME", "LATE") or reason == "DESTINATION_REACHED"
        on_time = status == "ON_TIME"
        sessions.append({
            "round": r,
            "route_id": last.get("route_id", ""),
            "spawn_bucket": last.get("spawn_bucket", ""),
            "arrival_status": status,
            "completion_reason": reason,
            "arrived": arrived,
            "on_time": on_time,
            "detour_ratio": detour,
            "elapsed_seconds": last.get("elapsed_seconds", 0),
            "weapon_ready_before_contact": bool(last.get("weapon_ready_before_contact", False)),
            "unauthorized_overwrite": bool(last.get("unauthorized_overwrite", False)),
            "continuous_jump_ticks": int(last.get("continuous_jump_ticks", 0) or 0),
            "last_wp": last.get("current_waypoint", ""),
        })
        if not arrived:
            root_causes.append({
                "route": route_id,
                "round": r,
                "last_wp": last.get("current_waypoint", ""),
                "blocker": last.get("blocker", ""),
                "completion_reason": reason,
                "cause": "WAYPOINT_ADVANCE_FAILED" if reason == "TIMEOUT" else "NO_PROGRESS",
            })

    n = len(sessions)
    arr_cnt = sum(1 for s in sessions if s["arrived"])
    ot_cnt = sum(1 for s in sessions if s["on_time"])
    mean_det = round(sum(s["detour_ratio"] for s in sessions) / n, 4) if n else 0.0
    pending_cnt = sum(1 for s in sessions if s["arrival_status"] == "PENDING" or not s["completion_reason"])
    passed = n >= 10 and arr_cnt >= 9 and ot_cnt >= 8 and mean_det <= 1.20 and pending_cnt == 0
    metrics = {
        "marco": "2B.8.7",
        "data_nature": "REAL",
        "route": route_id,
        "repetitions": n,
        "completions": arr_cnt,
        "completion_formula": f"{arr_cnt}/{n}",
        "on_time": ot_cnt,
        "on_time_formula": f"{ot_cnt}/{n}",
        "mean_detour_ratio": mean_det,
        "pending_sessions": pending_cnt,
        "authority_violations": sum(1 for s in sessions if s["unauthorized_overwrite"]),
        "continuous_jump": sum(s for s in (x["continuous_jump_ticks"] for x in sessions) if s > 1),
        "teammate_blocks": 0,
        "passed": passed,
        "sessions": sessions,
    }
    (OUT_DIR / out_name).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics, root_causes


def main():
    all_lines = []
    all_metrics = []
    all_causes = []
    for out_name, route_id in ROUTES:
        lines = run_solo_route(route_id, target_rounds=10)
        for line in lines:
            rec = json.loads(line)
            rec["cert_route"] = route_id
            all_lines.append(json.dumps(rec))
        m, causes = analyze_route(route_id, lines, out_name)
        all_metrics.append(m)
        all_causes.extend(causes)

    (OUT_DIR / "solo_route_telemetry.jsonl").write_text("\n".join(all_lines) + ("\n" if all_lines else ""), encoding="utf-8")
    (OUT_DIR / "live_failure_root_causes.json").write_text(json.dumps({
        "marco": "2B.8.7",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "causes": all_causes,
    }, indent=2), encoding="utf-8")

    summary = {m["route"]: {"completion": m["completion_formula"], "on_time": m["on_time_formula"], "detour": m["mean_detour_ratio"], "passed": m["passed"]} for m in all_metrics}
    print("SOLO_CERT_DONE:", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
