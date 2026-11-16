import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
SERVER_DIR = Path(r"H:\CS2_AI_Server")
CS2_EXE = SERVER_DIR / "game" / "bin" / "win64" / "cs2.exe"
PLUGIN_LOGS = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "logs"
CANARY_JSONL = PLUGIN_LOGS / "opening_canary_telemetry.jsonl"
AUTH_TICKS_JSONL = PLUGIN_LOGS / "canary_authority_ticks.jsonl"
AUTH_ACCT_JSON = PLUGIN_LOGS / "canary_authority_accounting.json"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "tr_canonical_route_runtime_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROUTES = [
    ("palace_certification_metrics.json", "a_palace_deep_room"),
    ("a_ramp_certification_metrics.json", "tr_a_ramp_staging_wait"),
    ("b_kitchen_certification_metrics.json", "tr_b_apps_kitchen_control"),
    ("b_house_certification_metrics.json", "tr_b_apps_house_staging"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def kill_cs2():
    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)


def run_solo_route(route_id: str, target_rounds: int, max_wait_s: int):
    kill_cs2()
    for p in (CANARY_JSONL, AUTH_TICKS_JSONL, AUTH_ACCT_JSON):
        if p.exists():
            p.unlink()

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
    subprocess.Popen(args, cwd=str(SERVER_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    try:
        while time.time() - t0 < max_wait_s:
            time.sleep(6)
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
                finished_cnt = sum(
                    1 for recs in by_rnd.values()
                    if recs[-1].get("executor_state") in ("DESTINATION_REACHED", "FALLBACK", "INTERRUPTED", "ABORTED")
                    or recs[-1].get("arrival_status") != "PENDING"
                )
                seen_rounds = {r: recs[-1].get("arrival_status", "PENDING") for r, recs in by_rnd.items()}
                print(f"[2B.8.9 SOLO {route_id}] elapsed={int(time.time()-t0)}s rounds={len(by_rnd)} finished={finished_cnt} statuses={seen_rounds}", flush=True)
                if finished_cnt >= target_rounds:
                    break
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

    auth_ticks = []
    if AUTH_TICKS_JSONL.exists():
        with AUTH_TICKS_JSONL.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        auth_ticks.append(json.loads(line))
                    except Exception:
                        pass

    auth_acct = {}
    if AUTH_ACCT_JSON.exists():
        try:
            auth_acct = json.loads(AUTH_ACCT_JSON.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            pass

    return canary_recs, auth_ticks, auth_acct


def summarize_route(route_id: str, canary_recs: list, auth_ticks: list, auth_acct: dict, target_rounds: int):
    by_rnd = defaultdict(list)
    for r in canary_recs:
        if r.get("round"):
            by_rnd[r["round"]].append(r)

    rounds_summary = []
    arrived = 0
    on_time = 0
    late = 0
    timeouts = 0
    fallbacks = 0
    unauth = 0
    cont_jump = 0

    for rnd in sorted(by_rnd.keys())[:target_rounds]:
        recs = by_rnd[rnd]
        last = recs[-1]
        st = last.get("arrival_status", "PENDING")
        if st in ("ON_TIME", "LATE"):
            arrived += 1
        if st == "ON_TIME":
            on_time += 1
        elif st == "LATE":
            late += 1
        if last.get("fallback_reason") == "TIMEOUT":
            timeouts += 1
        if last.get("executor_state") == "FALLBACK":
            fallbacks += 1
        rnd_unauth = sum(1 for x in recs if x.get("unauthorized_overwrite"))
        rnd_jump = sum(1 for x in recs if x.get("continuous_jump_ticks", 0) > 2)
        unauth += rnd_unauth
        cont_jump += rnd_jump
        rounds_summary.append({
            "round": rnd,
            "ticks": len(recs),
            "arrival_status": st,
            "executor_state": last.get("executor_state"),
            "fallback_reason": last.get("fallback_reason"),
            "completion_reason": last.get("completion_reason"),
            "canonical_step_index": last.get("canonical_step_index"),
            "canonical_step_count": last.get("canonical_step_count"),
            "canonical_step_name": last.get("canonical_step_name"),
            "is_final_destination": last.get("is_final_destination"),
            "elapsed_seconds": last.get("elapsed_seconds"),
            "deadline_seconds": last.get("deadline_seconds"),
            "traveled_distance": last.get("traveled_distance"),
            "expected_distance": last.get("expected_distance"),
            "unauthorized_overwrite_ticks": rnd_unauth,
            "final_position": last.get("actual_position"),
        })

    n = len(rounds_summary)
    auth_unauth = sum(1 for t in auth_ticks if t.get("unauthorized_overwrite_detected"))
    acct_summary = auth_acct.get("summary", {})
    return {
        "route_id": route_id,
        "data_nature": "REAL",
        "sessions_completed": n,
        "arrivals": arrived,
        "on_time": on_time,
        "late": late,
        "timeouts": timeouts,
        "fallbacks": fallbacks,
        "unauthorized_overwrite_ticks": unauth,
        "authority_tick_overwrites": auth_unauth,
        "continuous_jump_violations": cont_jump,
        "authority_residue": acct_summary.get("authority_residue", 0),
        "suppressed_writer_attempts": acct_summary.get("suppressed_writer_attempts", 0),
        "rounds": rounds_summary,
    }


def write_json(name: str, obj: dict):
    p = OUT_DIR / name
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return p


def run_phase1():
    print("=== MARCO 2B.8.9 PHASE 1: SINGLE-ROUTE STRUCTURAL VALIDATION (4 ROUTES) ===", flush=True)
    all_canary = []
    all_auth_ticks = []
    all_goal_audits = []
    route_results = {}
    phase1_pass = True

    for _, route_id in ROUTES:
        crecs, aticks, aacct = run_solo_route(route_id, target_rounds=1, max_wait_s=180)
        all_canary.extend(crecs)
        all_auth_ticks.extend(aticks)
        all_goal_audits.extend(aacct.get("goal_write_audit", []))
        summary = summarize_route(route_id, crecs, aticks, aacct, target_rounds=1)
        route_ok = (
            summary["sessions_completed"] == 1
            and summary["arrivals"] == 1
            and summary["unauthorized_overwrite_ticks"] == 0
            and summary["authority_tick_overwrites"] == 0
            and summary["continuous_jump_violations"] == 0
            and summary["authority_residue"] == 0
            and summary["rounds"][0]["is_final_destination"] is True
        )
        summary["structural_pass"] = route_ok
        route_results[route_id] = summary
        if not route_ok:
            phase1_pass = False

    (OUT_DIR / "phase1_solo_telemetry.jsonl").write_text(
        "\n".join(json.dumps(r) for r in all_canary) + ("\n" if all_canary else ""),
        encoding="utf-8",
    )
    write_json("single_route_structural_validation.json", {
        "marco": "2B.8.9",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase1_pass": phase1_pass,
        "routes": route_results,
    })
    write_json("movement_goal_writer_audit.json", {
        "marco": "2B.8.9",
        "data_nature": "REAL",
        "total_audit_entries": len(all_goal_audits),
        "accepted_writes": sum(1 for a in all_goal_audits if a.get("write_accepted")),
        "suppressed_writes": sum(1 for a in all_goal_audits if a.get("write_suppressed")),
        "unknown_post_canary_writers": sum(1 for a in all_goal_audits if a.get("writer_id") == "UNKNOWN_POST_CANARY_WRITER"),
        "sample_entries": all_goal_audits[:50],
    })
    write_json("runtime_tick_contract.json", {
        "marco": "2B.8.9",
        "tick_rate_hz": 64,
        "tick_interval_ms": 15.625,
        "observed_ticks": len(all_canary),
    })

    print(f"PHASE1_GATE={'PASS' if phase1_pass else 'FAIL'}", flush=True)
    for rid, res in route_results.items():
        print(f"  {rid}: pass={res['structural_pass']} arrivals={res['arrivals']}/1 status={res['rounds'][0]['arrival_status'] if res['rounds'] else 'NONE'} unauth={res['unauthorized_overwrite_ticks']} auth_unauth={res['authority_tick_overwrites']}", flush=True)
    sys.exit(0 if phase1_pass else 2)


def run_phase2():
    print("=== MARCO 2B.8.9 PHASE 2: 40-REPETITION SOLO CERTIFICATION ===", flush=True)
    all_canary = []
    all_auth_ticks = []
    all_goal_audits = []
    all_summaries = {}

    for filename, route_id in ROUTES:
        crecs, aticks, aacct = run_solo_route(route_id, target_rounds=10, max_wait_s=780)
        all_canary.extend(crecs)
        all_auth_ticks.extend(aticks)
        all_goal_audits.extend(aacct.get("goal_write_audit", []))
        summary = summarize_route(route_id, crecs, aticks, aacct, target_rounds=10)
        write_json(filename, summary)
        all_summaries[route_id] = summary

    (OUT_DIR / "solo_route_telemetry.jsonl").write_text(
        "\n".join(json.dumps(r) for r in all_canary) + ("\n" if all_canary else ""),
        encoding="utf-8",
    )

    total_sessions = sum(s["sessions_completed"] for s in all_summaries.values())
    total_arrivals = sum(s["arrivals"] for s in all_summaries.values())
    total_on_time = sum(s["on_time"] for s in all_summaries.values())
    total_unauth = sum(s["unauthorized_overwrite_ticks"] for s in all_summaries.values())
    total_auth_unauth = sum(s["authority_tick_overwrites"] for s in all_summaries.values())
    total_jump = sum(s["continuous_jump_violations"] for s in all_summaries.values())
    total_res = sum(s["authority_residue"] for s in all_summaries.values())

    verdict = (
        "TR_ROUTES_CERTIFIED_FOR_5V5_CANARY"
        if (total_sessions == 40 and total_arrivals >= 38 and total_unauth == 0 and total_auth_unauth == 0 and total_jump == 0 and total_res == 0)
        else "TR_ROUTE_LIVE_CERTIFICATION_FAILED"
    )

    agg = {
        "marco": "2B.8.9",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_sessions": total_sessions,
        "total_arrivals": total_arrivals,
        "total_on_time": total_on_time,
        "unauthorized_overwrite_ticks": total_unauth,
        "authority_tick_overwrites": total_auth_unauth,
        "continuous_jump_violations": total_jump,
        "authority_residue": total_res,
        "verdict": verdict,
        "per_route": {k: {
            "sessions": v["sessions_completed"],
            "arrivals": v["arrivals"],
            "on_time": v["on_time"],
            "late": v["late"],
            "timeouts": v["timeouts"],
            "unauth": v["unauthorized_overwrite_ticks"],
        } for k, v in all_summaries.items()},
    }
    write_json("deliverable_evidence.json", agg)
    print(f"PHASE2_VERDICT={verdict} arrivals={total_arrivals}/{total_sessions} on_time={total_on_time}/{total_sessions}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1", action="store_true")
    parser.add_argument("--phase2", action="store_true")
    args = parser.parse_args()
    if args.phase1:
        run_phase1()
    elif args.phase2:
        run_phase2()
    else:
        print("Specify --phase1 or --phase2")
        sys.exit(1)
