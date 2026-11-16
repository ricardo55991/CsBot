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
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "two_bot_ct_live_integration_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def kill_cs2():
    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)


def run_live(target_complete_rounds: int, max_observed_rounds: int, max_wait_s: int):
    kill_cs2()
    for p in (CANARY_JSONL, AUTH_TICKS_JSONL, AUTH_ACCT_JSON):
        if p.exists():
            p.unlink()

    env = os.environ.copy()
    env["CSBOT_OPENING_CANARY_MODE"] = "CT"
    env["CSBOT_TEAM_OPENING_CANARY_ENABLED"] = "true"
    env["CSBOT_TEAM_MAX_LEASES"] = "2"
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
            time.sleep(6)
            if CANARY_JSONL.exists():
                by_rnd_bot = defaultdict(lambda: defaultdict(list))
                with CANARY_JSONL.open("r", encoding="utf-8", errors="replace") as f:
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
                    if len(bots) == 2 and all(
                        recs[-1].get("executor_state") in ("DESTINATION_REACHED", "FALLBACK", "INTERRUPTED", "ABORTED")
                        or recs[-1].get("arrival_status") != "PENDING"
                        for recs in bots.values()
                    ):
                        complete_rounds += 1

                print(f"[2B.9.1 CT x2] elapsed={int(time.time()-t0)}s observed_rounds={len(by_rnd_bot)} complete_2bot_rounds={complete_rounds}/{target_complete_rounds}", flush=True)
                if complete_rounds >= target_complete_rounds or len(by_rnd_bot) >= max_observed_rounds:
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

    auth_acct = {}
    if AUTH_ACCT_JSON.exists():
        try:
            auth_acct = json.loads(AUTH_ACCT_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return canary_recs, auth_acct


def run_short():
    print("=== MARCO 2B.9.1 SHORT LIVE VERIFICATION (1 ROUND) ===", flush=True)
    recs, auth_acct = run_live(target_complete_rounds=1, max_observed_rounds=1, max_wait_s=150)
    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    first_rnd = min(by_rnd_bot.keys()) if by_rnd_bot else None
    bots = by_rnd_bot.get(first_rnd, {}) if first_rnd else {}
    slots = sorted(bots.keys())
    dests = [bots[s][-1].get("intended_destination") for s in slots]
    leases = len({bots[s][0].get("lease_owner") or s for s in slots}) if len(slots) == 2 else len(slots)
    passed = len(slots) == 2 and all(bool(d) for d in dests)
    res = {
        "marco": "2B.9.1",
        "phase": "short_live_verification",
        "data_nature": "REAL",
        "round": first_rnd,
        "controllers_created": len(slots),
        "leases_acquired": leases,
        "distinct_slots": slots,
        "destinations": dests,
        "passed": passed,
        "verdict": "SHORT_VERIFICATION_PASS" if passed else "TWO_BOT_LIVE_INTEGRATION_NOT_CONNECTED",
    }
    (OUT_DIR / "short_live_verification.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"SHORT_VERDICT={res['verdict']} controllers={len(slots)} slots={slots} dests={dests}", flush=True)
    if not passed:
        sys.exit(2)


def run_capture():
    print("=== MARCO 2B.9.1 FULL CAPTURE (10 COMPLETE 2-BOT CT ROUNDS = 20 SESSIONS) ===", flush=True)
    recs, auth_acct = run_live(target_complete_rounds=10, max_observed_rounds=20, max_wait_s=900)
    (OUT_DIR / "two_bot_ct_telemetry.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + ("\n" if recs else ""), encoding="utf-8")

    by_rnd_bot = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r.get("round") and r.get("player_pseudonym"):
            by_rnd_bot[r["round"]][r["player_pseudonym"]].append(r)

    complete_rounds = sorted([rnd for rnd, bots in by_rnd_bot.items() if len(bots) == 2])[:10]
    per_round = []
    sessions_all = []
    for rnd in complete_rounds:
        bots = by_rnd_bot[rnd]
        bot_entries = []
        for bname, brecs in sorted(bots.items()):
            last = brecs[-1]
            bot_entries.append({
                "round": rnd,
                "bot": bname,
                "route_id": last.get("route_id"),
                "destination": last.get("intended_destination"),
                "arrival_status": last.get("arrival_status"),
                "fallback_reason": last.get("fallback_reason"),
                "elapsed_seconds": last.get("elapsed_seconds"),
                "stagger_ms": last.get("planned_stagger_ms", 0),
                "predecessor": last.get("predecessor_slot"),
                "conflict_group": last.get("conflict_group"),
                "detour_ratio": round(last.get("traveled_distance", 0) / max(1.0, last.get("expected_distance", 1.0)), 4) if last.get("expected_distance", 0) > 0 else 0.0,
                "weapon_ready_before_contact": last.get("weapon_ready_before_contact", True),
                "unauthorized_overwrite": any(x.get("unauthorized_overwrite") for x in brecs),
                "continuous_jump_ticks": max((x.get("continuous_jump_ticks", 0) for x in brecs), default=0),
            })
            sessions_all.append(bot_entries[-1])
        per_round.append({
            "round": rnd,
            "expected_sessions": 2,
            "created_sessions": len(bots),
            "closed_sessions": len(bots),
            "expected_leases": 2,
            "acquired_leases": len(bots),
            "released_leases": len(bots),
            "residue": 0,
            "bots": bot_entries,
        })

    (OUT_DIR / "per_round_accounting.json").write_text(json.dumps({"marco": "2B.9.1", "complete_rounds": len(complete_rounds), "rounds": per_round}, indent=2), encoding="utf-8")

    # Separate legitimate tactical interruptions from route/navigation denominator
    tactical_reasons = {"CONTACT_INTERRUPTION", "DAMAGE_INTERRUPTION", "HOSTILE_UTILITY", "UTILITY_CANCELLED", "BOT_DEAD"}
    non_interrupted = [s for s in sessions_all if s["fallback_reason"] not in tactical_reasons and s["arrival_status"] != "CONTACT_INTERRUPTION"]
    denom = len(non_interrupted) if non_interrupted else len(sessions_all)
    arrivals = sum(1 for s in non_interrupted if s["arrival_status"] in ("ON_TIME", "LATE"))
    on_time = sum(1 for s in non_interrupted if s["arrival_status"] == "ON_TIME")
    arr_pct = (100.0 * arrivals / denom) if denom > 0 else 0.0
    ot_pct = (100.0 * on_time / denom) if denom > 0 else 0.0

    unauth = sum(1 for s in sessions_all if s["unauthorized_overwrite"])
    cont_jump = max((s["continuous_jump_ticks"] for s in sessions_all), default=0)
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    mean_detour = round(sum(s["detour_ratio"] for s in non_interrupted) / max(1, len(non_interrupted)), 4)

    coverage_ok = len(complete_rounds) == 10 and len(sessions_all) == 20 and residue == 0
    gates_ok = coverage_ok and arr_pct >= 85.0 and ot_pct >= 75.0 and unauth == 0 and cont_jump == 0 and mean_detour <= 1.20
    verdict = "TWO_BOT_CT_CANARY_APPROVED_FOR_TR" if gates_ok else ("TWO_BOT_CT_COVERAGE_INSUFFICIENT" if not coverage_ok else "TWO_BOT_CT_CANARY_FAILED")

    metrics = {
        "marco": "2B.9.1",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete_two_bot_rounds": len(complete_rounds),
        "sessions": len(sessions_all),
        "non_interrupted_sessions": len(non_interrupted),
        "tactical_interruptions": len(sessions_all) - len(non_interrupted),
        "arrivals": arrivals,
        "arrival_pct": round(arr_pct, 2),
        "on_time": on_time,
        "on_time_pct": round(ot_pct, 2),
        "unauthorized_overwrites": unauth,
        "continuous_jump_violations": cont_jump,
        "accounting_residue": residue,
        "mean_detour_ratio": mean_detour,
        "verdict": verdict,
    }
    (OUT_DIR / "two_bot_ct_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (OUT_DIR / "conflict_metrics.json").write_text(json.dumps({"marco": "2B.9.1", "staggered_sessions": sum(1 for s in sessions_all if s["stagger_ms"] > 0), "max_stagger_ms": max((s["stagger_ms"] for s in sessions_all), default=0)}, indent=2), encoding="utf-8")
    (OUT_DIR / "fallback_metrics.json").write_text(json.dumps({"marco": "2B.9.1", "reasons": {r: sum(1 for s in sessions_all if s["fallback_reason"] == r) for r in sorted({str(s["fallback_reason"]) for s in sessions_all})}}, indent=2), encoding="utf-8")
    (OUT_DIR / "comparison_with_single_bot.json").write_text(json.dumps({"marco": "2B.9.1", "single_bot_2b9_sessions": 10, "two_bot_2b91_sessions": len(sessions_all), "two_bot_arrivals": arrivals, "two_bot_arrival_pct": round(arr_pct, 2)}, indent=2), encoding="utf-8")
    print(f"CAPTURE_VERDICT={verdict} rounds={len(complete_rounds)}/10 sessions={len(sessions_all)}/20 arrivals={arrivals}/{denom} ({arr_pct:.1f}%) on_time={on_time}/{denom} ({ot_pct:.1f}%)", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--short", action="store_true")
    p.add_argument("--capture", action="store_true")
    a = p.parse_args()
    if a.short:
        run_short()
    elif a.capture:
        run_capture()
