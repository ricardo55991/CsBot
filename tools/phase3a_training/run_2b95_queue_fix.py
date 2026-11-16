import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_2b93_two_bot_tr as r93

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "two_bot_tr_queue_fix_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_short():
    print("=== MARCO 2B.9.5 SHORT VERIFICATION (3 ROUNDS TR) ===", flush=True)
    recs, dep_rounds, auth_acct = r93.run_tr_live(target_complete_rounds=3, max_observed_rounds=5, max_wait_s=300)
    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    complete_rounds = [rnd for rnd, bots in by_rnd_bot.items() if len(bots) == 2]
    false_cong = sum(1 for r in recs if r.get("root_block_cause") == "TEAMMATE_CONGESTION" and not r.get("verified_same_corridor", True))
    c4_incompat = sum(1 for r in recs if not r.get("c4_compatible", True))
    unauth = sum(1 for r in recs if r.get("unauthorized_overwrite"))
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    sched_timeout = sum(1 for r in recs if r.get("fallback_reason") == "CORRIDOR_QUEUE_TIMEOUT" and r.get("waiting_for_scheduled_release"))
    passed = len(complete_rounds) >= 3 and false_cong == 0 and sched_timeout == 0 and c4_incompat == 0 and unauth == 0 and residue == 0
    res = {
        "marco": "2B.9.5",
        "phase": "short_verification",
        "data_nature": "REAL",
        "complete_rounds": len(complete_rounds),
        "false_congestion": false_cong,
        "scheduled_queue_timeout": sched_timeout,
        "c4_incompatibilities": c4_incompat,
        "unauthorized_overwrites": unauth,
        "accounting_residue": residue,
        "passed": passed,
        "verdict": "SHORT_VERIFICATION_PASS" if passed else "TR_CANARY_SCHEDULER_RELEASE_NOT_ENFORCED",
    }
    (OUT_DIR / "short_verification.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"SHORT_VERDICT={res['verdict']} rounds={len(complete_rounds)} false_cong={false_cong} sched_to={sched_timeout} residue={residue}", flush=True)
    if not passed:
        sys.exit(2)


def run_capture():
    print("=== MARCO 2B.9.5 FINAL TR CAPTURE (10 ROUNDS = 20 SESSIONS) ===", flush=True)
    recs, dep_rounds, auth_acct = r93.run_tr_live(target_complete_rounds=10, max_observed_rounds=20, max_wait_s=900)
    (OUT_DIR / "two_bot_tr_telemetry.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + ("\n" if recs else ""), encoding="utf-8")

    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    complete_rounds = sorted([rnd for rnd, bots in by_rnd_bot.items() if len(bots) == 2])[:10]
    sessions_all = []
    for rnd in complete_rounds:
        for bname, brecs in sorted(by_rnd_bot[rnd].items()):
            last = brecs[-1]
            sessions_all.append({
                "round": rnd,
                "bot": bname,
                "arrival_status": last.get("arrival_status"),
                "fallback_reason": last.get("fallback_reason"),
                "c4_compatible": all(x.get("c4_compatible", True) for x in brecs),
                "detour_ratio": round(last.get("traveled_distance", 0) / max(1.0, last.get("expected_distance", 1.0)), 4) if last.get("expected_distance", 0) > 0 else 0.0,
                "unauthorized_overwrite": any(x.get("unauthorized_overwrite") for x in brecs),
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
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    mean_detour = round(sum(s["detour_ratio"] for s in non_int) / max(1, len(non_int)), 4)
    false_cong = sum(1 for s in sessions_all if s["false_teammate_congestion"])
    c4_incompat = sum(1 for s in sessions_all if not s["c4_compatible"])
    q_timeouts = sum(1 for s in non_int if s["fallback_reason"] == "CORRIDOR_QUEUE_TIMEOUT")
    q_pct = (100.0 * q_timeouts / denom) if denom > 0 else 0.0

    passed = (
        len(complete_rounds) == 10
        and len(sessions_all) == 20
        and arr_pct >= 85.0
        and ot_pct >= 75.0
        and mean_detour <= 1.20
        and false_cong == 0
        and q_pct <= 10.0
        and c4_incompat == 0
        and unauth == 0
        and residue == 0
    )
    verdict = "TWO_BOT_TR_CANARY_APPROVED_FOR_FIVE_BOT_CT" if passed else "TWO_BOT_TR_QUEUE_COORDINATION_FAILED"
    metrics = {
        "marco": "2B.9.5",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete_rounds": len(complete_rounds),
        "canary_sessions": len(sessions_all),
        "non_interrupted_sessions": len(non_int),
        "tactical_interruptions": len(sessions_all) - len(non_int),
        "arrivals": arrivals,
        "arrival_pct": round(arr_pct, 2),
        "on_time": on_time,
        "on_time_pct": round(ot_pct, 2),
        "mean_detour_ratio": mean_detour,
        "false_teammate_congestion": false_cong,
        "queue_timeouts": q_timeouts,
        "c4_incompatibilities": c4_incompat,
        "unauthorized_overwrites": unauth,
        "accounting_residue": residue,
        "verdict": verdict,
    }
    (OUT_DIR / "two_bot_tr_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"FINAL_VERDICT={verdict} arrivals={arrivals}/{denom} ({arr_pct:.1f}%) on_time={on_time}/{denom} ({ot_pct:.1f}%) false_cong={false_cong} q_timeouts={q_timeouts}", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--short", action="store_true")
    p.add_argument("--capture", action="store_true")
    a = p.parse_args()
    if a.short:
        run_short()
    elif a.capture:
        run_capture()
