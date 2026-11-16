import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_2b89_live_cert as r89  # reuse run_solo_route without duplicating server harness

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "tr_step_up_stabilization_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def summarize_route(route_id: str, target_rounds: int, canary_recs, auth_ticks, auth_acct):
    by_rnd = defaultdict(list)
    for rec in canary_recs:
        rnd = rec.get("round")
        if rnd:
            by_rnd[rnd].append(rec)

    rounds_list = sorted(by_rnd.keys())[:target_rounds]
    sessions = []
    arrivals = 0
    on_time = 0
    late = 0
    timeouts = 0
    pending = 0
    failed_step_up = 0
    unauth = sum(1 for r in canary_recs if r.get("unauthorized_overwrite"))
    auth_unauth = sum(1 for r in auth_ticks if r.get("unauthorized_overwrite"))
    cont_jump = max((r.get("continuous_jump_ticks", 0) for r in canary_recs), default=0)

    for rnd in rounds_list:
        recs = by_rnd[rnd]
        last = recs[-1]
        st = last.get("arrival_status", "PENDING")
        fb = last.get("fallback_reason", "")
        if st == "ON_TIME":
            arrivals += 1
            on_time += 1
        elif st == "LATE":
            arrivals += 1
            late += 1
        elif st == "PENDING":
            pending += 1
        if "TIMEOUT" in str(fb):
            timeouts += 1
        if "STEP_UP" in str(fb):
            failed_step_up += 1
        sessions.append({
            "round": rnd,
            "ticks": len(recs),
            "arrival_status": st,
            "executor_state": last.get("executor_state"),
            "fallback_reason": fb,
            "completion_reason": last.get("completion_reason"),
            "elapsed_seconds": last.get("elapsed_seconds"),
            "jump_pulses_issued": last.get("jump_pulses_issued", 0),
            "final_position": last.get("actual_position"),
        })

    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    return {
        "route_id": route_id,
        "data_nature": "REAL",
        "sessions_completed": len(rounds_list),
        "arrivals": arrivals,
        "on_time": on_time,
        "late": late,
        "timeouts": timeouts,
        "pending": pending,
        "failed_step_up": failed_step_up,
        "unauthorized_overwrite_ticks": unauth,
        "authority_tick_overwrites": auth_unauth,
        "continuous_jump_violations": cont_jump,
        "accounting_residue": residue,
        "rounds": sessions,
    }


def run_focal():
    print("=== MARCO 2B.8.10 FOCAL CONFIRMATION: 10 PALACE + 10 KITCHEN ===", flush=True)
    focal_routes = [
        ("palace_step_up_metrics.json", "a_palace_deep_room"),
        ("kitchen_doorway_metrics.json", "tr_b_apps_kitchen_control"),
    ]
    telem_path = OUT_DIR / "focal_live_telemetry.jsonl"
    if telem_path.exists():
        telem_path.unlink()

    all_metrics = {}
    focal_pass = True
    for fname, route_id in focal_routes:
        canary_recs, auth_ticks, auth_acct = r89.run_solo_route(route_id, target_rounds=10, max_wait_s=780)
        with telem_path.open("a", encoding="utf-8") as tf:
            for rec in canary_recs:
                tf.write(json.dumps(rec) + "\n")
        m = summarize_route(route_id, 10, canary_recs, auth_ticks, auth_acct)
        (OUT_DIR / fname).write_text(json.dumps(m, indent=2), encoding="utf-8")
        all_metrics[route_id] = m

        ok_route = (
            m["sessions_completed"] == 10
            and m["arrivals"] == 10
            and m["on_time"] >= 9
            and m["failed_step_up"] == 0
            and m["timeouts"] == 0
            and m["continuous_jump_violations"] == 0
            and m["unauthorized_overwrite_ticks"] == 0
            and m["authority_tick_overwrites"] == 0
            and m["pending"] == 0
            and m["accounting_residue"] == 0
        )
        if not ok_route:
            focal_pass = False
        print(f"[FOCAL {route_id}] pass={ok_route} arrivals={m['arrivals']}/10 on_time={m['on_time']}/10 failed_step_up={m['failed_step_up']} unauth={m['unauthorized_overwrite_ticks']}", flush=True)

    verdict = "FOCAL_CONFIRMATION_PASS" if focal_pass else "STEP_UP_LIVE_CONFIRMATION_FAILED"
    summary = {
        "marco": "2B.8.10",
        "phase": "focal_confirmation",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "routes": all_metrics,
    }
    (OUT_DIR / "focal_live_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"FOCAL_VERDICT={verdict}", flush=True)
    if not focal_pass:
        sys.exit(2)


def run_final():
    print("=== MARCO 2B.8.10 FINAL CERTIFICATION: 40 SESSIONS (10 PER ROUTE) ===", flush=True)
    routes = [
        "a_palace_deep_room",
        "tr_a_ramp_staging_wait",
        "tr_b_apps_kitchen_control",
        "tr_b_apps_house_staging",
    ]
    telem_path = OUT_DIR / "final_certification_telemetry.jsonl"
    if telem_path.exists():
        telem_path.unlink()

    per_route = {}
    tot_sessions = 0
    tot_arrivals = 0
    tot_on_time = 0
    tot_timeouts = 0
    tot_unauth = 0
    tot_auth_unauth = 0
    tot_cont_jump = 0
    tot_pending = 0
    tot_residue = 0

    for route_id in routes:
        canary_recs, auth_ticks, auth_acct = r89.run_solo_route(route_id, target_rounds=10, max_wait_s=780)
        with telem_path.open("a", encoding="utf-8") as tf:
            for rec in canary_recs:
                tf.write(json.dumps(rec) + "\n")
        m = summarize_route(route_id, 10, canary_recs, auth_ticks, auth_acct)
        per_route[route_id] = m
        tot_sessions += m["sessions_completed"]
        tot_arrivals += m["arrivals"]
        tot_on_time += m["on_time"]
        tot_timeouts += m["timeouts"]
        tot_unauth += m["unauthorized_overwrite_ticks"]
        tot_auth_unauth += m["authority_tick_overwrites"]
        tot_cont_jump = max(tot_cont_jump, m["continuous_jump_violations"])
        tot_pending += m["pending"]
        tot_residue += m["accounting_residue"]
        print(f"[FINAL {route_id}] arrivals={m['arrivals']}/10 on_time={m['on_time']}/10 failed_step_up={m['failed_step_up']} unauth={m['unauthorized_overwrite_ticks']}", flush=True)

    all_ge_9 = all(m["arrivals"] >= 9 and m["on_time"] >= 9 for m in per_route.values())
    passed = (
        tot_sessions == 40
        and all_ge_9
        and tot_arrivals >= 38
        and tot_on_time >= 36
        and tot_timeouts == 0
        and tot_unauth == 0
        and tot_auth_unauth == 0
        and tot_cont_jump == 0
        and tot_pending == 0
        and tot_residue == 0
    )
    verdict = "TR_ROUTES_CERTIFIED_FOR_5V5_CANARY" if passed else "TR_ROUTE_LIVE_CERTIFICATION_CONDITIONAL"
    out = {
        "marco": "2B.8.10",
        "phase": "final_certification",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_sessions": tot_sessions,
        "total_arrivals": tot_arrivals,
        "total_on_time": tot_on_time,
        "timeouts": tot_timeouts,
        "unauthorized_overwrite_ticks": tot_unauth,
        "authority_tick_overwrites": tot_auth_unauth,
        "continuous_jump_violations": tot_cont_jump,
        "pending": tot_pending,
        "accounting_residue": tot_residue,
        "verdict": verdict,
        "per_route": per_route,
    }
    (OUT_DIR / "final_certification_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"FINAL_VERDICT={verdict} arrivals={tot_arrivals}/{tot_sessions} on_time={tot_on_time}/{tot_sessions}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--focal", action="store_true")
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    if args.focal:
        run_focal()
    elif args.final:
        run_final()
    else:
        print("Specify --focal or --final")
        sys.exit(1)
