import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_2b91_two_bot_ct as r91

PLUGIN_LOGS = r91.PLUGIN_LOGS
FULL_DEP_LOG = PLUGIN_LOGS / "full_team_departure_rounds.jsonl"
SHORT_TRACE_LOG = PLUGIN_LOGS / "short_round_departure_trace.json"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "full_team_departure_coordination_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clear_extra_logs():
    for p in (FULL_DEP_LOG, SHORT_TRACE_LOG):
        if p.exists():
            p.unlink()


def read_full_dep_rounds():
    rows = []
    if FULL_DEP_LOG.exists():
        for line in FULL_DEP_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def run_short():
    print("=== MARCO 2B.9.2 SHORT LIVE VERIFICATION (2 ROUNDS) ===", flush=True)
    clear_extra_logs()
    recs, auth_acct = r91.run_live(target_complete_rounds=2, max_observed_rounds=3, max_wait_s=220)
    dep_rounds = read_full_dep_rounds()
    trace = []
    if SHORT_TRACE_LOG.exists():
        try:
            trace = json.loads(SHORT_TRACE_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    (OUT_DIR / "short_round_departure_trace.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")

    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    complete_2bot = sum(1 for bots in by_rnd_bot.values() if len(bots) == 2)
    dep_5ct = [d for d in dep_rounds if d.get("total_cts_planned", 0) == 5]
    lateral_on_congestion = sum(
        1 for r in recs
        if r.get("root_block_cause") == "TEAMMATE_CONGESTION" and "LATERAL" in str(r.get("recovery_strategy", "")).upper()
    )
    max_hold = max(
        (a.get("PassiveHoldMs", 0) for d in dep_rounds for a in d.get("assignments", [])),
        default=0,
    )
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0

    passed = (
        complete_2bot >= 2
        and len(dep_5ct) >= 2
        and lateral_on_congestion == 0
        and max_hold <= 500
        and residue == 0
    )
    res = {
        "marco": "2B.9.2",
        "phase": "short_live_verification",
        "data_nature": "REAL",
        "complete_2bot_rounds": complete_2bot,
        "rounds_with_5ct_schedule": len(dep_5ct),
        "lateral_waypoints_on_congestion": lateral_on_congestion,
        "max_passive_hold_ms": max_hold,
        "accounting_residue": residue,
        "trace_events_count": len(trace),
        "passed": passed,
        "verdict": "SHORT_VERIFICATION_PASS" if passed else "FULL_TEAM_DEPARTURE_COORDINATION_NOT_CONNECTED",
    }
    (OUT_DIR / "short_live_verification.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"SHORT_VERDICT={res['verdict']} 2bot_rounds={complete_2bot} 5ct_schedules={len(dep_5ct)} max_hold={max_hold} lateral={lateral_on_congestion} residue={residue}", flush=True)
    if not passed:
        sys.exit(2)


def run_capture():
    print("=== MARCO 2B.9.2 FULL CAPTURE (10 COMPLETE 2-BOT CT ROUNDS = 20 SESSIONS + 50 CT PLANS) ===", flush=True)
    clear_extra_logs()
    recs, auth_acct = r91.run_live(target_complete_rounds=10, max_observed_rounds=20, max_wait_s=900)
    dep_rounds = read_full_dep_rounds()
    (OUT_DIR / "two_bot_ct_telemetry.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + ("\n" if recs else ""), encoding="utf-8")

    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    complete_rounds = sorted([rnd for rnd, bots in by_rnd_bot.items() if len(bots) == 2])[:10]
    dep_by_rnd = {d["round"]: d for d in dep_rounds if "round" in d}

    sessions_all = []
    dep_entries = 0
    passive_entries = 0
    for rnd in complete_rounds:
        if rnd in dep_by_rnd:
            dep_entries += dep_by_rnd[rnd].get("total_cts_planned", 0)
            passive_entries += dep_by_rnd[rnd].get("utility_observed_count", 0)
        for bname, brecs in sorted(by_rnd_bot[rnd].items()):
            last = brecs[-1]
            sessions_all.append({
                "round": rnd,
                "bot": bname,
                "route_id": last.get("route_id"),
                "destination": last.get("intended_destination"),
                "arrival_status": last.get("arrival_status"),
                "fallback_reason": last.get("fallback_reason"),
                "root_block_cause": last.get("root_block_cause"),
                "current_block_state": last.get("current_block_state"),
                "elapsed_seconds": last.get("elapsed_seconds"),
                "detour_ratio": round(last.get("traveled_distance", 0) / max(1.0, last.get("expected_distance", 1.0)), 4) if last.get("expected_distance", 0) > 0 else 0.0,
                "weapon_ready_before_contact": last.get("weapon_ready_before_contact", True),
                "unauthorized_overwrite": any(x.get("unauthorized_overwrite") for x in brecs),
                "continuous_jump_ticks": max((x.get("continuous_jump_ticks", 0) for x in brecs), default=0),
                "false_teammate_congestion": any(x.get("root_block_cause") == "TEAMMATE_CONGESTION" and not x.get("verified_same_corridor", True) for x in brecs),
            })

    tactical = {"CONTACT_INTERRUPTION", "DAMAGE_INTERRUPTION", "HOSTILE_UTILITY", "UTILITY_CANCELLED", "BOT_DEAD"}
    non_int = [s for s in sessions_all if s["fallback_reason"] not in tactical and s["arrival_status"] != "CONTACT_INTERRUPTION"]
    denom = len(non_int) if non_int else len(sessions_all)
    arrivals = sum(1 for s in non_int if s["arrival_status"] in ("ON_TIME", "LATE"))
    on_time = sum(1 for s in non_int if s["arrival_status"] == "ON_TIME")
    arr_pct = (100.0 * arrivals / denom) if denom > 0 else 0.0
    ot_pct = (100.0 * on_time / denom) if denom > 0 else 0.0
    unauth = sum(1 for s in sessions_all if s["unauthorized_overwrite"])
    cont_jump = max((s["continuous_jump_ticks"] for s in sessions_all), default=0)
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    mean_detour = round(sum(s["detour_ratio"] for s in non_int) / max(1, len(non_int)), 4)
    false_cong = sum(1 for s in sessions_all if s["false_teammate_congestion"])

    integration_ok = len(complete_rounds) == 10 and len(sessions_all) == 20 and dep_entries >= 50 and residue == 0 and unauth == 0 and cont_jump == 0
    perf_ok = integration_ok and arr_pct >= 85.0 and ot_pct >= 75.0 and mean_detour <= 1.20 and false_cong == 0
    verdict = "TWO_BOT_CT_CANARY_APPROVED_FOR_TR" if perf_ok else ("TWO_BOT_CT_CANARY_FAILED" if integration_ok else "FULL_TEAM_DEPARTURE_COORDINATION_FAILED")

    metrics = {
        "marco": "2B.9.2",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete_rounds": len(complete_rounds),
        "canary_sessions": len(sessions_all),
        "departure_schedule_entries": dep_entries,
        "passive_utility_entries": passive_entries,
        "non_interrupted_sessions": len(non_int),
        "tactical_interruptions": len(sessions_all) - len(non_int),
        "arrivals": arrivals,
        "arrival_pct": round(arr_pct, 2),
        "on_time": on_time,
        "on_time_pct": round(ot_pct, 2),
        "mean_detour_ratio": mean_detour,
        "unauthorized_overwrites": unauth,
        "continuous_jump_violations": cont_jump,
        "accounting_residue": residue,
        "false_teammate_congestion": false_cong,
        "verdict": verdict,
    }
    (OUT_DIR / "two_bot_ct_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (OUT_DIR / "full_team_departure_metrics.json").write_text(json.dumps({"marco": "2B.9.2", "rounds_logged": len(dep_rounds), "total_entries": dep_entries, "passive_utility_entries": passive_entries, "rounds": dep_rounds}, indent=2), encoding="utf-8")
    (OUT_DIR / "corridor_queue_metrics.json").write_text(json.dumps({"marco": "2B.9.2", "queue_waits": sum(1 for r in recs if r.get("recovery_strategy") == "QUEUE_WAIT_FOR_PREDECESSOR"), "queue_resumes": sum(1 for r in recs if r.get("recovery_strategy") == "QUEUE_RESUMED"), "queue_timeouts": sum(1 for s in sessions_all if s["fallback_reason"] == "CORRIDOR_QUEUE_TIMEOUT")}, indent=2), encoding="utf-8")
    (OUT_DIR / "passive_hold_metrics.json").write_text(json.dumps({"marco": "2B.9.2", "passive_holds_created": sum(d.get("passive_holds_created", 0) for d in dep_rounds), "max_planned_hold_ms": max((a.get("PassiveHoldMs", 0) for d in dep_rounds for a in d.get("assignments", [])), default=0)}, indent=2), encoding="utf-8")
    (OUT_DIR / "blocker_reclassification.json").write_text(json.dumps({"marco": "2B.9.2", "false_teammate_congestion": false_cong, "root_causes": {c: sum(1 for s in sessions_all if str(s["root_block_cause"]) == c) for c in sorted({str(s["root_block_cause"]) for s in sessions_all})}}, indent=2), encoding="utf-8")
    (OUT_DIR / "fallback_metrics.json").write_text(json.dumps({"marco": "2B.9.2", "reasons": {r: sum(1 for s in sessions_all if str(s["fallback_reason"]) == r) for r in sorted({str(s["fallback_reason"]) for s in sessions_all})}}, indent=2), encoding="utf-8")
    (OUT_DIR / "comparison_with_2b91.json").write_text(json.dumps({"marco": "2B.9.2", "2b91_arrivals": "3/20 (15.0%)", "2b92_arrivals": f"{arrivals}/{denom} ({arr_pct:.2f}%)", "2b92_on_time": f"{on_time}/{denom} ({ot_pct:.2f}%)"}, indent=2), encoding="utf-8")
    print(f"CAPTURE_VERDICT={verdict} rounds={len(complete_rounds)}/10 sessions={len(sessions_all)}/20 dep_entries={dep_entries} arrivals={arrivals}/{denom} ({arr_pct:.1f}%) on_time={on_time}/{denom} ({ot_pct:.1f}%)", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--short", action="store_true")
    p.add_argument("--capture", action="store_true")
    a = p.parse_args()
    if a.short:
        run_short()
    elif a.capture:
        run_capture()
