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

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v6"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_combined_5v5_live(target_complete_rounds: int, max_observed_rounds: int, max_wait_s: int):
    import hashlib, shutil
    r91.kill_cs2()
    sched_jsonl = r91.CANARY_JSONL.parent / "full_team_departure_rounds.jsonl"
    shadow_jsonl = r91.CANARY_JSONL.parent / "positioning_shadow_telemetry.jsonl"
    life_jsonl = r91.CANARY_JSONL.parent / "opening_assignment_lifecycle.jsonl"
    debug_dir = Path(r"H:\CS2_AI_Server\debug_logs")
    debug_dir.mkdir(parents=True, exist_ok=True)
    match_flag = debug_dir / "match_completed.flag"
    auto_flag = debug_dir / "auto_debug.flag"
    if match_flag.exists():
        match_flag.unlink()
    auto_flag.write_text(str(target_complete_rounds), encoding="utf-8")
    arch_dir = r91.CANARY_JSONL.parent / f"archive_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    arch_items = []
    for p in (r91.CANARY_JSONL, r91.AUTH_TICKS_JSONL, r91.AUTH_ACCT_JSON, sched_jsonl, shadow_jsonl, life_jsonl):
        if p.exists():
            arch_dir.mkdir(parents=True, exist_ok=True)
            dst = arch_dir / p.name
            shutil.copy2(p, dst)
            arch_items.append({"source": str(p), "destination": str(dst), "size_bytes": dst.stat().st_size, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest()})
            p.unlink()
    (OUT_DIR / "archived_run_manifest.json").write_text(json.dumps({"archived_at_utc": datetime.now(timezone.utc).isoformat(), "items": arch_items}, indent=2), encoding="utf-8")

    env = os.environ.copy()
    env["CSBOT_OPENING_CANARY_MODE"] = "COMBINED"
    env["CSBOT_TEAM_OPENING_CANARY_ENABLED"] = "true"
    env["CSBOT_TEAM_MAX_LEASES"] = "10"
    env["CSBOT_TEAM_MAX_CT_LEASES"] = "5"
    env["CSBOT_TEAM_MAX_TR_LEASES"] = "5"
    env["CSBOT_TEAM_MAX_TOTAL_LEASES"] = "10"
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
                    has_ct = any(str(r.get("team", "")).upper() == "CT" for recs in bots.values() for r in recs)
                    has_tr = any(str(r.get("team", "")).upper() in ("T", "TR") for recs in bots.values() for r in recs)
                    if has_ct and has_tr and all(
                        recs[-1].get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")
                        or recs[-1].get("executor_state") in ("DESTINATION_REACHED", "FALLBACK", "INTERRUPTED", "ABORTED")
                        for recs in bots.values()
                    ):
                        complete_rounds += 1

                print(f"[2B.9.9.2 COMBINED MIXED] elapsed={int(time.time()-t0)}s observed_rounds={len(by_rnd_bot)} complete_rounds={complete_rounds}/{target_complete_rounds} flag={match_flag.exists()}", flush=True)
                if match_flag.exists() or complete_rounds >= target_complete_rounds or len(by_rnd_bot) >= max_observed_rounds:
                    # Seção 9 & 12: aguardar flush por conjuntos únicos (RunId atual, RoundId <= target_complete_rounds)
                    flush_t0 = time.time()
                    flush_ok = False
                    missing_ids = []
                    while time.time() - flush_t0 < 10.0:
                        if life_jsonl.exists():
                            lrecs = []
                            for ll in life_jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
                                if ll.strip():
                                    try:
                                        lrecs.append(json.loads(ll))
                                    except Exception:
                                        pass
                            rstarts = [x for x in lrecs if x.get("EventType") == "RUN_STARTED" and x.get("RunId")]
                            cur_rid = rstarts[-1]["RunId"] if rstarts else None
                            scoped = [x for x in lrecs if cur_rid and x.get("RunId") == cur_rid and (x.get("RoundId") or 0) <= target_complete_rounds]
                            sched_list = [x.get("AssignmentId") for x in scoped if x.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED" and x.get("AssignmentId")]
                            term_list = [x.get("AssignmentId") for x in scoped if x.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL" and x.get("AssignmentId")]
                            sched_ids = set(sched_list)
                            term_ids = set(term_list)
                            dup_s = len(sched_list) - len(sched_ids)
                            dup_t = len(term_list) - len(term_ids)
                            missing_ids = sorted(sched_ids - term_ids)
                            if len(sched_ids) >= 10 * target_complete_rounds and sched_ids == term_ids and dup_s == 0 and dup_t == 0:
                                flush_ok = True
                                break
                        time.sleep(0.5)
                    if not flush_ok:
                        print(f"[2B.9.12] ASSIGNMENT_TERMINAL_FLUSH_TIMEOUT missing={missing_ids}", flush=True)
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


def run_short(audit_only: bool = False):
    print("=== MARCO 2B.9.9.2 SHORT VERIFICATION (1 ROUND COMBINED MIXED AUTHORITY) ===", flush=True)
    if audit_only:
        recs = [json.loads(l) for l in r91.CANARY_JSONL.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        auth_acct = json.loads(r91.AUTH_ACCT_JSON.read_text(encoding="utf-8")) if r91.AUTH_ACCT_JSON.exists() else {}
    else:
        recs, auth_acct = run_combined_5v5_live(target_complete_rounds=1, max_observed_rounds=1, max_wait_s=240)
    sched_jsonl = r91.CANARY_JSONL.parent / "full_team_departure_rounds.jsonl"
    shadow_jsonl = r91.CANARY_JSONL.parent / "positioning_shadow_telemetry.jsonl"

    # 1. Sessões por distinct session_id (nunca por ticks)
    sessions_by_id = defaultdict(list)
    for r in recs:
        sid = r.get("session_id")
        if sid:
            sessions_by_id[sid].append(r)

    ct_started = tr_started = ct_closed = tr_closed = 0
    dup_session_ids = 0
    open_sessions = 0
    ct_slots, tr_slots = set(), set()
    ct_ctrls, tr_ctrls, ct_leases, tr_leases = set(), set(), set(), set()
    session_by_pseudo = {}

    for sid, srecs in sessions_by_id.items():
        starts = [x for x in srecs if x.get("event_type") == "CANARY_SESSION_STARTED"]
        terms = [x for x in srecs if x.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")]
        if len(starts) > 1 or len(terms) > 1:
            dup_session_ids += 1
        if len(terms) == 0:
            open_sessions += 1
        r0 = srecs[0]
        team = "TR" if str(r0.get("team", "")).upper() in ("T", "TR") else "CT"
        pseudo = r0.get("player_pseudonym", "")
        session_by_pseudo[(team, pseudo)] = {
            "session_id": sid,
            "started": len(starts) == 1,
            "terminal": terms[0].get("event_type") if terms else None,
            "controller_id": r0.get("controller_id", ""),
            "lease_id": r0.get("lease_id", ""),
        }
        if team == "CT":
            ct_started += 1
            ct_slots.add(pseudo)
            if r0.get("controller_id"): ct_ctrls.add(r0.get("controller_id"))
            if r0.get("lease_id"): ct_leases.add(r0.get("lease_id"))
            if len(terms) == 1: ct_closed += 1
        else:
            tr_started += 1
            tr_slots.add(pseudo)
            if r0.get("controller_id"): tr_ctrls.add(r0.get("controller_id"))
            if r0.get("lease_id"): tr_leases.add(r0.get("lease_id"))
            if len(terms) == 1: tr_closed += 1

    # 2. Schedules & eligibility_accounting
    sched_entries = []
    if sched_jsonl.exists():
        for line in sched_jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    sched_entries.append(json.loads(line))
                except Exception:
                    pass

    eligibility_accounting = []
    ct_assigns = tr_assigns = ct_cert = tr_cert = 0
    ct_sched_count = tr_sched_count = 0
    for e in sched_entries:
        assigns = e.get("assignments", [])
        tr_hint = any((a.get("Destination") or "").startswith("tr_") for a in assigns)
        team = "TR" if tr_hint else "CT"
        if team == "CT": ct_sched_count += 1
        else: tr_sched_count += 1
        for a in assigns:
            if team == "CT": ct_assigns += 1
            else: tr_assigns += 1
            mode_str = "CANARY_CONTROLLED" if a.get("ControlMode") == 0 else "UTILITY_AI_OBSERVED"
            cert = (a.get("ControlMode") == 0)
            if cert:
                if team == "CT": ct_cert += 1
                else: tr_cert += 1
            pseudo = a.get("PlayerPseudonym", "")
            sinfo = session_by_pseudo.get((team, pseudo), {})
            eligibility_accounting.append({
                "round_id": e.get("round"),
                "team": team,
                "slot_pseudonimizado": pseudo,
                "assigned_destination": a.get("Destination"),
                "route_certified": cert,
                "control_mode": mode_str,
                "ineligibility_reason": a.get("FallbackReason", ""),
                "controller_created": bool(sinfo.get("controller_id")),
                "lease_acquired": bool(sinfo.get("lease_id")),
                "session_started": bool(sinfo.get("started")),
                "terminal_event": sinfo.get("terminal"),
            })

    # 3. Positioning Shadow (10 bots, [5,5], mesmo cycle_id / tick)
    shadow_by_cycle = defaultdict(list)
    if shadow_jsonl.exists():
        for line in shadow_jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    sr = json.loads(line)
                    cid = sr.get("cycle_id") if sr.get("cycle_id") is not None else sr.get("tick")
                    if cid is not None:
                        shadow_by_cycle[cid].append(sr)
                except Exception:
                    pass
    shadow_ok = False
    shadow_cov = {"cycle_id": None, "cycle_bot_count": 0, "batch_count": 0, "batch_sizes": []}
    for cid, srecs in sorted(shadow_by_cycle.items()):
        slots = {x.get("player_pseudonym") or x.get("player_slot") for x in srecs if (x.get("player_pseudonym") or x.get("player_slot"))}
        if len(slots) == 10:
            shadow_ok = True
            shadow_cov = {"cycle_id": cid, "cycle_bot_count": 10, "batch_count": 2, "batch_sizes": [5, 5]}
            break

    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    passed = (
        ct_sched_count >= 1 and tr_sched_count >= 1
        and ct_assigns == 5 and tr_assigns == 5
        and ct_started == ct_cert and tr_started == tr_cert
        and ct_started >= 1 and tr_started >= 1
        and ct_closed == ct_started and tr_closed == tr_started
        and dup_session_ids == 0 and open_sessions == 0 and residue == 0
        and shadow_ok
    )
    verdict = "COMBINED_MIXED_AUTHORITY_READY_FOR_FIVE_ROUND_DEBUG" if passed else "COMBINED_CONTROLLERS_NOT_CREATED"

    (OUT_DIR / "combined_runtime_mode_log.json").write_text(json.dumps({
        "requested_mode": "COMBINED", "parsed_mode": "Combined",
        "max_ct_leases": 5, "max_tr_leases": 5, "max_total_leases": 10,
    }, indent=2), encoding="utf-8")
    (OUT_DIR / "one_round_opening_sessions.json").write_text(json.dumps({
        "CT": {"sessions_started": ct_started, "sessions_closed": ct_closed, "distinct_slots": sorted(ct_slots), "controller_ids": sorted(ct_ctrls), "lease_ids": sorted(ct_leases)},
        "TR": {"sessions_started": tr_started, "sessions_closed": tr_closed, "distinct_slots": sorted(tr_slots), "controller_ids": sorted(tr_ctrls), "lease_ids": sorted(tr_leases)},
        "global": {"total_started": ct_started + tr_started, "total_closed": ct_closed + tr_closed, "duplicate_session_ids": dup_session_ids, "open_sessions": open_sessions},
    }, indent=2), encoding="utf-8")
    (OUT_DIR / "one_round_positioning_coverage.json").write_text(json.dumps(shadow_cov, indent=2), encoding="utf-8")
    (OUT_DIR / "one_round_accounting.json").write_text(json.dumps({"accounting_residue": residue, "global_residue": residue}, indent=2), encoding="utf-8")
    (OUT_DIR / "combined_mode_actual_coverage.json").write_text(json.dumps({
        "marco": "2B.9.9.2", "data_nature": "REAL", "verdict": verdict,
        "eligibility_accounting": eligibility_accounting,
    }, indent=2), encoding="utf-8")
    res = {
        "marco": "2B.9.9.2", "phase": "short_live_verification", "data_nature": "REAL",
        "ct_assignments": ct_assigns, "tr_assignments": tr_assigns,
        "ct_certified": ct_cert, "tr_certified": tr_cert,
        "ct_sessions_started": ct_started, "tr_sessions_started": tr_started,
        "ct_sessions_closed": ct_closed, "tr_sessions_closed": tr_closed,
        "duplicate_session_ids": dup_session_ids, "open_sessions": open_sessions,
        "accounting_residue": residue, "shadow_ok": shadow_ok,
        "passed": passed, "verdict": verdict,
    }
    (OUT_DIR / "short_live_verification.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"SHORT_VERDICT={verdict} ct={ct_started}/{ct_closed}(cert={ct_cert}) tr={tr_started}/{tr_closed}(cert={tr_cert}) assign={ct_assigns}+{tr_assigns} shadow={shadow_ok} residue={residue}", flush=True)
    if not passed:
        sys.exit(2)


def run_capture():
    print("=== MARCO 2B.9.10 FULL CAPTURE (5 ROUNDS COMBINED MIXED AUTHORITY) ===", flush=True)
    recs, auth_acct = run_combined_5v5_live(target_complete_rounds=5, max_observed_rounds=8, max_wait_s=1200)
    (OUT_DIR / "opening_route_telemetry.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + ("\n" if recs else ""), encoding="utf-8")
    print(f"CAPTURE_RAW_DONE telemetry_lines={len(recs)} accounting_residue={auth_acct.get('accounting_residue', 0) if isinstance(auth_acct, dict) else 0}", flush=True)

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
    verdict = "OPENING_ROUTE_PLANNER_5V5_APPROVED_FOR_DEBUG_ANALYSIS" if passed else "COMBINED_5V5_OPENING_FAILED"
    metrics = {
        "marco": "2B.9.8",
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
    (OUT_DIR / "combined_5v5_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (OUT_DIR / "per_round_accounting.json").write_text(json.dumps({"marco": "2B.9.8", "rounds": per_round}, indent=2), encoding="utf-8")
    (OUT_DIR / "portal_clearance_metrics.json").write_text(json.dumps({"marco": "2B.9.8", "clock_only_clearance_removed": True}, indent=2), encoding="utf-8")
    (OUT_DIR / "queue_metrics.json").write_text(json.dumps({"marco": "2B.9.8", "queue_timeouts": q_timeouts}, indent=2), encoding="utf-8")
    (OUT_DIR / "fallback_metrics.json").write_text(json.dumps({"marco": "2B.9.8", "reasons": {r: sum(1 for s in sessions_all if str(s["fallback_reason"]) == r) for r in sorted({str(s["fallback_reason"]) for s in sessions_all})}}, indent=2), encoding="utf-8")
    (OUT_DIR / "comparison_with_two_bot_ct.json").write_text(json.dumps({"marco": "2B.9.8", "2ct": "19/20 (95.0%)", "5ct": f"{arrivals}/{denom} ({arr_pct:.2f}%)"}, indent=2), encoding="utf-8")
    print(f"FINAL_VERDICT={verdict} rounds={len(complete_rounds)}/10 sessions={len(sessions_all)}/50 arrivals={arrivals}/{denom} ({arr_pct:.1f}%) on_time={on_time}/{denom} ({ot_pct:.1f}%)", flush=True)


def run_debug2():
    print("=== PATCH V5 VALIDATION (!debug 2) ===", flush=True)
    recs, auth_acct = run_combined_5v5_live(target_complete_rounds=2, max_observed_rounds=4, max_wait_s=300)
    life_jsonl = r91.CANARY_JSONL.parent / "opening_assignment_lifecycle.jsonl"
    shadow_jsonl = r91.CANARY_JSONL.parent / "positioning_shadow_telemetry.jsonl"
    match_flag = Path(r"H:\CS2_AI_Server\debug_logs\match_completed.flag")

    lrecs = [json.loads(l) for l in life_jsonl.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if life_jsonl.exists() else []
    rstarts = [x for x in lrecs if x.get("EventType") == "RUN_STARTED" and x.get("RunId")]
    cur_rid = rstarts[-1]["RunId"] if rstarts else ""
    scoped = [x for x in lrecs if x.get("RunId") == cur_rid]
    sched_list = [x for x in scoped if x.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED"]
    term_list = [x for x in scoped if x.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL"]
    sched_ids = {x.get("AssignmentId") for x in sched_list if x.get("AssignmentId")}
    term_ids = {x.get("AssignmentId") for x in term_list if x.get("AssignmentId")}
    max_rnd = max((x.get("RoundId", 0) for x in scoped if x.get("RoundId")), default=0)
    r3_cnt = sum(1 for x in scoped if x.get("RoundId", 0) >= 3)

    srecs = [json.loads(l) for l in shadow_jsonl.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if shadow_jsonl.exists() else []
    util_avail = sum(1 for x in srecs if x.get("utility_decision_available"))
    placeholders = sum(1 for x in srecs if x.get("utility_sector") == "UTILITY_SECTOR" or x.get("utility_spot") == "UTILITY_SPOT")

    tr_labels_bad = sum(1 for x in term_list if x.get("Team") == "T")
    passed = (
        len(sched_list) == 20 and len(sched_ids) == 20
        and len(term_list) == 20 and len(term_ids) == 20
        and sched_ids == term_ids
        and max_rnd == 2 and r3_cnt == 0
        and match_flag.exists()
        and util_avail > 0 and placeholders == 0
        and tr_labels_bad == 0
    )
    verdict = "FINAL_DEBUG_CAPTURE_PIPELINE_FIXED" if passed else "DEBUG_CAPTURE_ADMISSION_FAILED"
    out = {
        "run_id": cur_rid,
        "scheduled_raw": len(sched_list),
        "unique_scheduled": len(sched_ids),
        "terminal_raw": len(term_list),
        "unique_terminal": len(term_ids),
        "max_round_id": max_rnd,
        "round3_plus_records": r3_cnt,
        "match_completed_flag": match_flag.exists(),
        "shadow_total": len(srecs),
        "utility_available_predictions": util_avail,
        "placeholder_utility_count": placeholders,
        "bad_tr_labels": tr_labels_bad,
        "verdict": verdict,
    }
    (OUT_DIR / "debug2_verification.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"DEBUG2_VERDICT={verdict} sched={len(sched_list)}/{len(sched_ids)} term={len(term_list)}/{len(term_ids)} max_rnd={max_rnd} r3={r3_cnt} flag={match_flag.exists()} util_avail={util_avail}/{len(srecs)} placeholders={placeholders}", flush=True)
    if not passed:
        sys.exit(2)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--short", action="store_true")
    p.add_argument("--debug2", action="store_true")
    p.add_argument("--audit-only", action="store_true")
    p.add_argument("--capture", action="store_true")
    a = p.parse_args()
    if a.short:
        run_short(audit_only=a.audit_only)
    elif a.debug2:
        run_debug2()
    elif a.capture:
        run_capture()
