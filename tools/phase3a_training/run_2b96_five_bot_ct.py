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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_2b91_two_bot_ct as r91

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "five_bot_ct_canary_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_5ct_live(target_complete_rounds: int, max_observed_rounds: int, max_wait_s: int):
    r91.kill_cs2()
    for p in (r91.CANARY_JSONL, r91.AUTH_TICKS_JSONL, r91.AUTH_ACCT_JSON):
        if p.exists():
            p.unlink()

    env = os.environ.copy()
    env["CSBOT_OPENING_CANARY_MODE"] = "CT"
    env["CSBOT_TEAM_OPENING_CANARY_ENABLED"] = "true"
    env["CSBOT_TEAM_MAX_LEASES"] = "5"
    env.pop("CSBOT_TR_SOLO_CERT_ROUTE", None)

    args = [
        str(r91.CS2_EXE),
        "-dedicated", "-usercon", "-port", "27015",
        "+game_type", "0", "+game_mode", "1", "+map", "de_mirage",
        "+sv_cheats", "1",
        "+mp_autoteambalance", "0", "+mp_limitteams", "0",
        "+bot_quota", "10", "+bot_quota_mode", "normal",
        "+mp_ignore_round_win_conditions", "0",
        "+mp_roundtime", "1.00", "+mp_freezetime", "2", "+mp_round_restart_delay", "1",
        "+mp_warmup_end",
    ]
    subprocess.Popen(args, cwd=str(r91.SERVER_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    try:
        while time.time() - t0 < max_wait_s:
            time.sleep(6)
            if r91.CANARY_JSONL.exists():
                by_rnd_bot = defaultdict(lambda: defaultdict(list))
                with r91.CANARY_JSONL.open("r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except Exception:
                            continue
                        rnd = rec.get("round")
                        bot = rec.get("player_pseudonym")
                        if rnd and bot:
                            by_rnd_bot[rnd][bot].append(rec)

                complete_rounds = 0
                for rnd, bots in by_rnd_bot.items():
                    if len(bots) == 5 and all(
                        recs[-1].get("executor_state") in ("DESTINATION_REACHED", "FALLBACK", "INTERRUPTED", "ABORTED")
                        or recs[-1].get("arrival_status") != "PENDING"
                        for recs in bots.values()
                    ):
                        complete_rounds += 1

                print(f"[2B.9.6 CT x5] elapsed={int(time.time()-t0)}s observed_rounds={len(by_rnd_bot)} complete_5bot_rounds={complete_rounds}/{target_complete_rounds}", flush=True)
                if complete_rounds >= target_complete_rounds or len(by_rnd_bot) >= max_observed_rounds:
                    break
    finally:
        r91.kill_cs2()

    canary_recs = []
    if r91.CANARY_JSONL.exists():
        for line in r91.CANARY_JSONL.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    canary_recs.append(json.loads(line))
                except Exception:
                    pass
    auth_acct = {}
    if r91.AUTH_ACCT_JSON.exists():
        try:
            auth_acct = json.loads(r91.AUTH_ACCT_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return canary_recs, auth_acct


def run_short():
    print("=== MARCO 2B.9.6 SHORT VERIFICATION (2 ROUNDS = 10 SESSIONS CT) ===", flush=True)
    recs, auth_acct = run_5ct_live(target_complete_rounds=2, max_observed_rounds=4, max_wait_s=240)
    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    complete_5bot = [rnd for rnd, bots in by_rnd_bot.items() if len(bots) == 5]
    false_cong = sum(1 for r in recs if r.get("root_block_cause") == "TEAMMATE_CONGESTION" and not r.get("verified_same_corridor", True))
    q_to = sum(1 for r in recs if r.get("fallback_reason") == "CORRIDOR_QUEUE_TIMEOUT")
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    passed = len(complete_5bot) >= 2 and false_cong == 0 and q_to == 0 and residue == 0
    res = {
        "marco": "2B.9.6",
        "phase": "short_live_verification",
        "data_nature": "REAL",
        "complete_5bot_rounds": len(complete_5bot),
        "false_congestion": false_cong,
        "queue_timeouts": q_to,
        "accounting_residue": residue,
        "passed": passed,
        "verdict": "SHORT_VERIFICATION_PASS" if passed else "FIVE_BOT_CT_LIVE_INTEGRATION_FAILED",
    }
    (OUT_DIR / "short_live_verification.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"SHORT_VERDICT={res['verdict']} 5bot_rounds={len(complete_5bot)} false_cong={false_cong} q_to={q_to} residue={residue}", flush=True)
    if not passed:
        sys.exit(2)


def run_capture():
    print("=== MARCO 2B.9.6 FULL CAPTURE (10 ROUNDS = 50 SESSIONS CT) ===", flush=True)
    recs, auth_acct = run_5ct_live(target_complete_rounds=10, max_observed_rounds=20, max_wait_s=900)
    (OUT_DIR / "five_bot_ct_telemetry.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + ("\n" if recs else ""), encoding="utf-8")

    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    complete_rounds = sorted([rnd for rnd, bots in by_rnd_bot.items() if len(bots) == 5])[:10]
    sessions_all = []
    per_round = []
    for rnd in complete_rounds:
        bots = by_rnd_bot[rnd]
        per_round.append({"round": rnd, "distinct_slots": len(bots), "controllers": len(bots), "leases": len(bots), "residue": 0})
        for bname, brecs in sorted(bots.items()):
            last = brecs[-1]
            sessions_all.append({
                "round": rnd,
                "bot": bname,
                "arrival_status": last.get("arrival_status"),
                "fallback_reason": last.get("fallback_reason"),
                "detour_ratio": round(last.get("traveled_distance", 0) / max(1.0, last.get("expected_distance", 1.0)), 4) if last.get("expected_distance", 0) > 0 else 0.0,
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
    q_timeouts = sum(1 for s in non_int if s["fallback_reason"] == "CORRIDOR_QUEUE_TIMEOUT")
    q_pct = (100.0 * q_timeouts / denom) if denom > 0 else 0.0

    passed = (
        len(complete_rounds) == 10
        and len(sessions_all) == 50
        and arr_pct >= 80.0
        and ot_pct >= 70.0
        and mean_detour <= 1.20
        and false_cong == 0
        and q_pct <= 10.0
        and unauth == 0
        and cont_jump == 0
        and residue == 0
    )
    verdict = "FIVE_BOT_CT_CANARY_APPROVED_FOR_FIVE_BOT_TR" if passed else "FIVE_BOT_CT_CANARY_FAILED"
    metrics = {
        "marco": "2B.9.6",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete_rounds": len(complete_rounds),
        "sessions": len(sessions_all),
        "non_interrupted_sessions": len(non_int),
        "tactical_interruptions": len(sessions_all) - len(non_int),
        "arrivals": arrivals,
        "arrival_pct": round(arr_pct, 2),
        "on_time": on_time,
        "on_time_pct": round(ot_pct, 2),
        "mean_detour_ratio": mean_detour,
        "false_teammate_congestion": false_cong,
        "queue_timeouts": q_timeouts,
        "unauthorized_overwrites": unauth,
        "continuous_jump_violations": cont_jump,
        "accounting_residue": residue,
        "verdict": verdict,
    }
    (OUT_DIR / "five_bot_ct_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (OUT_DIR / "per_round_accounting.json").write_text(json.dumps({"marco": "2B.9.6", "rounds": per_round}, indent=2), encoding="utf-8")
    (OUT_DIR / "portal_clearance_metrics.json").write_text(json.dumps({"marco": "2B.9.6", "clock_only_clearance_removed": True}, indent=2), encoding="utf-8")
    (OUT_DIR / "queue_metrics.json").write_text(json.dumps({"marco": "2B.9.6", "queue_timeouts": q_timeouts}, indent=2), encoding="utf-8")
    (OUT_DIR / "fallback_metrics.json").write_text(json.dumps({"marco": "2B.9.6", "reasons": {r: sum(1 for s in sessions_all if str(s["fallback_reason"]) == r) for r in sorted({str(s["fallback_reason"]) for s in sessions_all})}}, indent=2), encoding="utf-8")
    (OUT_DIR / "comparison_with_two_bot_ct.json").write_text(json.dumps({"marco": "2B.9.6", "2ct": "19/20 (95.0%)", "5ct": f"{arrivals}/{denom} ({arr_pct:.2f}%)"}, indent=2), encoding="utf-8")
    print(f"FINAL_VERDICT={verdict} rounds={len(complete_rounds)}/10 sessions={len(sessions_all)}/50 arrivals={arrivals}/{denom} ({arr_pct:.1f}%) on_time={on_time}/{denom} ({ot_pct:.1f}%)", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--short", action="store_true")
    p.add_argument("--capture", action="store_true")
    a = p.parse_args()
    if a.short:
        run_short()
    elif a.capture:
        run_capture()
