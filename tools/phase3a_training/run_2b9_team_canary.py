import argparse
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SERVER_DIR = Path(r"H:\CS2_AI_Server")
CS2_EXE = SERVER_DIR / "game" / "bin" / "win64" / "cs2.exe"
PLUGIN_LOGS = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "logs"
CANARY_JSONL = PLUGIN_LOGS / "opening_canary_telemetry.jsonl"
AUTH_TICKS_JSONL = PLUGIN_LOGS / "canary_authority_ticks.jsonl"
AUTH_ACCT_JSON = PLUGIN_LOGS / "canary_authority_accounting.json"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "team_canary_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def kill_cs2():
    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)


def run_team_session(team_mode: str, max_leases: int, target_rounds: int, max_wait_s: int, out_telem_name: str, out_metrics_name: str, min_arrival_pct: float, min_ontime_pct: float):
    kill_cs2()
    for p in (CANARY_JSONL, AUTH_TICKS_JSONL, AUTH_ACCT_JSON):
        if p.exists():
            p.unlink()

    env = os.environ.copy()
    env["CSBOT_OPENING_CANARY_MODE"] = team_mode
    env["CSBOT_TEAM_OPENING_CANARY_ENABLED"] = "true"
    env["CSBOT_TEAM_MAX_LEASES"] = str(max_leases)
    env.pop("CSBOT_TR_SOLO_CERT_ROUTE", None)

    args = [
        str(CS2_EXE),
        "-dedicated", "-usercon", "-port", "27015",
        "+game_type", "0", "+game_mode", "1", "+map", "de_mirage",
        "+sv_cheats", "1",
        "+mp_autoteambalance", "0", "+mp_limitteams", "0",
        "+bot_quota", "10", "+bot_quota_mode", "normal",
        "+mp_ignore_round_win_conditions", "0",
        "+mp_roundtime", "1.00", "+mp_freezetime", "2", "+mp_round_restart_delay", "1",
        "+mp_warmup_end",
    ]
    subprocess.Popen(args, cwd=str(SERVER_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    try:
        while time.time() - t0 < max_wait_s:
            time.sleep(8)
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
                if len(by_rnd) >= target_rounds:
                    last_rnd = max(by_rnd.keys())
                    last_recs = by_rnd[last_rnd]
                    if last_recs and (last_recs[-1].get("executor_state") in ("DESTINATION_REACHED", "FALLBACK", "INTERRUPTED", "ABORTED") or last_recs[-1].get("arrival_status") != "PENDING"):
                        print(f"[2B.9 {team_mode} x{max_leases}] elapsed={int(time.time()-t0)}s rounds={len(by_rnd)}/{target_rounds} DONE", flush=True)
                        break
                print(f"[2B.9 {team_mode} x{max_leases}] elapsed={int(time.time()-t0)}s rounds={len(by_rnd)}/{target_rounds}", flush=True)
    finally:
        kill_cs2()

    canary_recs = []
    if CANARY_JSONL.exists():
        with CANARY_JSONL.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        canary_recs.append(json.loads(line))
                    except Exception:
                        pass

    (OUT_DIR / out_telem_name).write_text("\n".join(json.dumps(r) for r in canary_recs) + ("\n" if canary_recs else ""), encoding="utf-8")

    by_sess = defaultdict(list)
    for r in canary_recs:
        by_sess[(r.get("round"), r.get("player_pseudonym"))].append(r)

    sessions = len(by_sess)
    arrivals = sum(1 for recs in by_sess.values() if recs[-1].get("arrival_status") in ("ON_TIME", "LATE"))
    on_time = sum(1 for recs in by_sess.values() if recs[-1].get("arrival_status") == "ON_TIME")
    timeouts = sum(1 for recs in by_sess.values() if "TIMEOUT" in str(recs[-1].get("fallback_reason", "")))
    unauth = sum(1 for r in canary_recs if r.get("unauthorized_overwrite"))
    cont_jump = max((r.get("continuous_jump_ticks", 0) for r in canary_recs), default=0)
    weapon_ready = sum(1 for recs in by_sess.values() if recs[-1].get("weapon_ready_before_contact", True))
    detours = [recs[-1].get("traveled_distance", 0) / max(1.0, recs[-1].get("expected_distance", 1.0)) for recs in by_sess.values() if recs[-1].get("expected_distance", 0) > 0]
    mean_detour = round(sum(detours) / len(detours), 4) if detours else 0.0

    auth_acct = {}
    if AUTH_ACCT_JSON.exists():
        try:
            auth_acct = json.loads(AUTH_ACCT_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0

    arr_pct = (100.0 * arrivals / sessions) if sessions > 0 else 0.0
    ot_pct = (100.0 * on_time / sessions) if sessions > 0 else 0.0
    passed = (
        sessions >= target_rounds
        and arr_pct >= min_arrival_pct
        and ot_pct >= min_ontime_pct
        and timeouts == 0
        and unauth == 0
        and residue == 0
        and cont_jump == 0
    )

    metrics = {
        "marco": "2B.9",
        "team_mode": team_mode,
        "max_leases": max_leases,
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sessions": sessions,
        "arrivals": arrivals,
        "arrival_pct": round(arr_pct, 2),
        "on_time": on_time,
        "on_time_pct": round(ot_pct, 2),
        "timeouts": timeouts,
        "unauthorized_overwrites": unauth,
        "accounting_residue": residue,
        "continuous_jump_violations": cont_jump,
        "weapon_ready_before_contact": weapon_ready,
        "mean_detour_ratio": mean_detour,
        "passed": passed,
    }
    (OUT_DIR / out_metrics_name).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"[2B.9 RESULT {out_metrics_name}] passed={passed} sessions={sessions} arrivals={arrivals} ({arr_pct:.1f}%) on_time={on_time} ({ot_pct:.1f}%) unauth={unauth} residue={residue}", flush=True)
    return passed


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--phaseA-ct", action="store_true")
    p.add_argument("--phaseA-tr", action="store_true")
    p.add_argument("--phaseB-ct", action="store_true")
    p.add_argument("--phaseB-tr", action="store_true")
    a = p.parse_args()
    if a.phaseA_ct:
        ok = run_team_session("CT", 2, 10, 600, "two_bot_ct_telemetry.jsonl", "two_bot_ct_metrics.json", 85.0, 75.0)
        sys.exit(0 if ok else 2)
    elif a.phaseA_tr:
        ok = run_team_session("TR", 2, 10, 600, "two_bot_tr_telemetry.jsonl", "two_bot_tr_metrics.json", 85.0, 75.0)
        sys.exit(0 if ok else 2)
    elif a.phaseB_ct:
        ok = run_team_session("CT", 5, 10, 600, "five_bot_ct_telemetry.jsonl", "five_bot_ct_metrics.json", 80.0, 70.0)
        sys.exit(0 if ok else 2)
    elif a.phaseB_tr:
        ok = run_team_session("TR", 5, 10, 600, "five_bot_tr_telemetry.jsonl", "five_bot_tr_metrics.json", 80.0, 70.0)
        sys.exit(0 if ok else 2)
