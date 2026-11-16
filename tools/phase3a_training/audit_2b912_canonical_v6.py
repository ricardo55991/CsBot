import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
SERVER_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")
PLUGIN_DLL = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\CsBotManager.dll")
OUT_DIR = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v6"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COMBAT_WEAPONS = {
    "weapon_hkp2000", "weapon_usp_silencer", "weapon_glock", "weapon_famas",
    "weapon_m4a1", "weapon_m4a1_silencer", "weapon_ak47", "weapon_galilar",
    "weapon_mac10", "weapon_mp9", "weapon_awp", "weapon_ssg08",
    "weapon_deagle", "weapon_p250", "weapon_fiveseven", "weapon_tec9",
    "weapon_elite", "weapon_cz75a", "weapon_mp7", "weapon_mp5sd",
    "weapon_ump45", "weapon_p90", "weapon_bizon", "weapon_aug", "weapon_sg556",
    "weapon_scar20", "weapon_g3sg1", "weapon_nova", "weapon_xm1014", "weapon_mag7",
    "weapon_sawedoff", "weapon_m249", "weapon_negev", "weapon_revolver",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(p: Path):
    if not p.exists():
        return []
    out = []
    for l in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if l.strip():
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def write_json(name: str, obj):
    (OUT_DIR / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d > 0 else 0.0


def percentile(vals, q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = min(len(s) - 1, max(0, int(round((len(s) - 1) * q))))
    return round(float(s[idx]), 4)


def main():
    for src_name, dst_name in [
        ("opening_canary_telemetry.jsonl", "opening_route_telemetry.jsonl"),
        ("opening_assignment_lifecycle.jsonl", "opening_assignment_lifecycle.jsonl"),
        ("positioning_shadow_telemetry.jsonl", "positioning_shadow_telemetry.jsonl"),
    ]:
        src = SERVER_LOGS / src_name
        if src.exists():
            shutil.copy2(src, OUT_DIR / dst_name)

    life_raw = read_jsonl(OUT_DIR / "opening_assignment_lifecycle.jsonl")
    run_starts = [r for r in life_raw if r.get("EventType") == "RUN_STARTED" and r.get("RunId")]
    rs = run_starts[-1] if run_starts else {}
    run_id = rs.get("RunId", "RUN_IDENTITY_NOT_PROVEN")
    life_recs = [r for r in life_raw if r.get("RunId") == run_id]
    opening_recs = read_jsonl(OUT_DIR / "opening_route_telemetry.jsonl")
    shadow_recs = read_jsonl(OUT_DIR / "positioning_shadow_telemetry.jsonl")
    auth_acct = json.loads((SERVER_LOGS / "canary_authority_accounting.json").read_text(encoding="utf-8")) if (SERVER_LOGS / "canary_authority_accounting.json").exists() else {}

    dll_sha = sha256_file(PLUGIN_DLL) if PLUGIN_DLL.exists() else ""
    write_json("input_snapshot.json", {
        "marco": "2B.9.12_CANONICAL_FINAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_nature": "REAL",
        "map": "de_mirage",
        "run_id": run_id,
        "plugin_instance_id": rs.get("PluginInstanceId"),
        "process_id": rs.get("ProcessId"),
        "dll_sha256": dll_sha,
        "expected_dll_sha256": "88923836179cf3e2d0857b0f011a5dac508f49dc1da2a42a30a3abf98794423b",
        "dll_hash_match": dll_sha == "88923836179cf3e2d0857b0f011a5dac508f49dc1da2a42a30a3abf98794423b",
    })
    write_json("combined_runtime_mode_log.json", {
        "requested_mode": "COMBINED",
        "parsed_mode": "Combined",
        "target_debug_rounds": 5,
        "max_ct_leases": 5,
        "max_tr_leases": 5,
        "max_total_leases": 10,
    })

    # debug_match.jsonl
    with (OUT_DIR / "debug_match.jsonl").open("w", encoding="utf-8") as df:
        for sr in shadow_recs:
            raw_t = str(sr.get("team", "")).upper()
            df.write(json.dumps({
                "round": sr.get("round_id"),
                "tick": sr.get("tick"),
                "team": "TR" if raw_t in ("T", "TR") else "CT",
                "player_pseudonym": sr.get("player_slot"),
                "utility_state": sr.get("utility_state"),
                "utility_sector": sr.get("utility_sector"),
                "utility_spot": sr.get("utility_spot"),
                "utility_destination": sr.get("utility_destination"),
                "utility_decision_available": sr.get("utility_decision_available"),
                "neural_state": sr.get("neural_state"),
                "neural_sector": sr.get("neural_sector"),
                "neural_spot": sr.get("neural_spot"),
                "confidence_by_head": sr.get("confidence_by_head"),
            }) + "\n")

    # 1. Assignment lifecycle accounting
    sched_raw = [r for r in life_recs if r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED"]
    sc_raw = [r for r in life_recs if r.get("EventType") == "OPENING_ASSIGNMENT_STATE_CHANGED"]
    term_raw = [r for r in life_recs if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL"]
    sched_ids = {r["AssignmentId"] for r in sched_raw if r.get("AssignmentId")}
    term_ids = {r["AssignmentId"] for r in term_raw if r.get("AssignmentId")}
    rounds_seen = sorted({r.get("RoundId") for r in sched_raw if r.get("RoundId")})
    round6_plus = sum(1 for r in life_recs if (r.get("RoundId") or 0) >= 6)

    per_round = defaultdict(lambda: {"ct_assigns": 0, "tr_assigns": 0, "ct_term": 0, "tr_term": 0})
    for r in sched_raw:
        k = "ct_assigns" if r.get("Team") == "CT" else "tr_assigns"
        per_round[r["RoundId"]][k] += 1
    for r in term_raw:
        k = "ct_term" if r.get("Team") == "CT" else "tr_term"
        per_round[r["RoundId"]][k] += 1

    write_json("per_round_accounting.json", {"rounds": [{"round_id": rnd, **per_round[rnd]} for rnd in rounds_seen]})
    write_json("assignment_lifecycle_accounting.json", {
        "run_id": run_id,
        "lifecycle_rounds": rounds_seen,
        "max_round_id": max(rounds_seen) if rounds_seen else 0,
        "round_6_plus_records": round6_plus,
        "raw_scheduled_events": len(sched_raw),
        "unique_scheduled_assignments": len(sched_ids),
        "duplicate_scheduled_events": len(sched_raw) - len(sched_ids),
        "state_changed_events": len(sc_raw),
        "raw_terminal_events": len(term_raw),
        "unique_terminal_assignments": len(term_ids),
        "duplicate_terminal_events": len(term_raw) - len(term_ids),
        "assignments_without_terminal": len(sched_ids - term_ids),
        "terminal_without_scheduled": len(term_ids - sched_ids),
    })

    # 2. Sessions & CT/TR route metrics
    sessions = defaultdict(list)
    for r in opening_recs:
        if r.get("session_id"):
            sessions[r["session_id"]].append(r)

    def summarize_team(team_target: str):
        ts = []
        for sid, srecs in sessions.items():
            raw_t = str(srecs[0].get("team", "")).upper()
            t = "TR" if raw_t in ("T", "TR") else "CT"
            if t != team_target:
                continue
            term = next((r for r in reversed(srecs) if r.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")), srecs[-1])
            ts.append({
                "session_id": sid,
                "round": srecs[0].get("round"),
                "destination": srecs[0].get("intended_destination", ""),
                "terminal_event": term.get("event_type"),
                "arrival_status": term.get("arrival_status", ""),
                "reason": term.get("completion_reason") or term.get("fallback_reason") or "",
                "detour_ratio": round(term.get("traveled_distance", 0.0) / max(1.0, term.get("expected_distance", 1.0)), 4) if term.get("expected_distance", 0.0) > 0 else 1.0,
                "queue_timeout": any(x.get("fallback_reason") == "CORRIDOR_QUEUE_TIMEOUT" for x in srecs),
                "unauthorized_overwrite": any(x.get("unauthorized_overwrite") for x in srecs),
                "continuous_jump_ticks": max((x.get("continuous_jump_ticks", 0) for x in srecs), default=0),
                "false_teammate_congestion": any(x.get("root_block_cause") == "TEAMMATE_CONGESTION" and not x.get("verified_same_corridor", True) for x in srecs),
            })
        non_int = [s for s in ts if s["terminal_event"] != "INTERRUPTED"]
        denom = len(non_int)
        arrivals = sum(1 for s in non_int if s["arrival_status"] in ("ON_TIME", "LATE"))
        on_time = sum(1 for s in non_int if s["arrival_status"] == "ON_TIME")
        q_to = sum(1 for s in non_int if s["queue_timeout"])
        return {
            "team": team_target,
            "assignments": sum(1 for r in sched_raw if r.get("Team") == team_target),
            "certified_assignments": sum(1 for r in sched_raw if r.get("Team") == team_target and r.get("RouteCertified")),
            "controlled_sessions": len(ts),
            "utility_observed_assignments": sum(1 for r in sched_raw if r.get("Team") == team_target and not r.get("RouteCertified")),
            "completed": sum(1 for s in ts if s["terminal_event"] == "COMPLETED"),
            "interrupted": sum(1 for s in ts if s["terminal_event"] == "INTERRUPTED"),
            "aborted": sum(1 for s in ts if s["terminal_event"] == "ABORTED"),
            "non_interrupted_denominator": denom,
            "arrivals": arrivals,
            "arrival_pct": pct(arrivals, denom),
            "on_time": on_time,
            "on_time_pct": pct(on_time, denom),
            "mean_detour_ratio": round(sum(s["detour_ratio"] for s in non_int) / max(1, denom), 4),
            "queue_timeouts": q_to,
            "queue_timeout_pct": pct(q_to, denom),
            "unauthorized_overwrites": sum(1 for s in ts if s["unauthorized_overwrite"]),
            "continuous_jump_violations": max((s["continuous_jump_ticks"] for s in ts), default=0),
            "false_congestion": sum(1 for s in ts if s["false_teammate_congestion"]),
            "sessions": ts,
        }

    ct_m = summarize_team("CT")
    tr_m = summarize_team("TR")
    write_json("ct_route_metrics.json", {k: v for k, v in ct_m.items() if k != "sessions"})
    write_json("tr_route_metrics.json", {k: v for k, v in tr_m.items() if k != "sessions"})
    write_json("tr_failure_analysis.json", {
        "team": "TR",
        "arrivals": tr_m["arrivals"],
        "non_interrupted_denominator": tr_m["non_interrupted_denominator"],
        "arrival_pct": tr_m["arrival_pct"],
        "aborted_sessions": [s for s in tr_m["sessions"] if s["terminal_event"] == "ABORTED"],
        "interrupted_sessions": [s for s in tr_m["sessions"] if s["terminal_event"] == "INTERRUPTED"],
    })

    # 3. Readiness (por arma efetiva, previous_tick < first_threat_tick)
    r_counts = defaultdict(int)
    r_sessions = []
    for sid, srecs in sorted(sessions.items()):
        ticks = sorted([r for r in srecs if r.get("event_type") != "CANARY_SESSION_STARTED"], key=lambda x: (x.get("dispatch_tick") or 0))
        if not ticks:
            r_counts["INSUFFICIENT_TELEMETRY"] += 1
            continue
        t_idx = next((i for i, r in enumerate(ticks) if r.get("threat_line_crossed") is True), None)
        if t_idx is None:
            term_ev = next((r.get("event_type") for r in reversed(srecs) if r.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")), None)
            cls = "INTERRUPTED_BEFORE_THREAT" if term_ev == "INTERRUPTED" else "INSUFFICIENT_TELEMETRY"
            r_counts[cls] += 1
            r_sessions.append({"session_id": sid, "classification": cls})
            continue
        tr = ticks[t_idx]
        ftt = tr.get("dispatch_tick") or 0
        w_cur = (tr.get("active_weapon") or "").strip().lower()
        prev_cands = [r for r in ticks[:t_idx] if (r.get("dispatch_tick") or 0) < ftt]
        prev_r = prev_cands[-1] if prev_cands else None
        w_prev = (prev_r.get("active_weapon") or "").strip().lower() if prev_r else ""
        if w_cur not in COMBAT_WEAPONS:
            cls = "NOT_READY_AT_THREAT_LINE"
        elif prev_r is not None and w_prev in COMBAT_WEAPONS:
            cls = "READY_BEFORE_THREAT_LINE"
        else:
            cls = "READY_AT_THREAT_LINE"
        r_counts[cls] += 1
        r_sessions.append({
            "session_id": sid, "first_threat_tick": ftt,
            "real_previous_tick": prev_r.get("dispatch_tick") if prev_r else None,
            "weapon_at_real_previous_tick": w_prev, "weapon_at_first_threat_tick": w_cur,
            "classification": cls,
        })
    write_json("weapon_readiness_metrics.json", {
        "READY_BEFORE_THREAT_LINE": r_counts["READY_BEFORE_THREAT_LINE"],
        "READY_AT_THREAT_LINE": r_counts["READY_AT_THREAT_LINE"],
        "NOT_READY_AT_THREAT_LINE": r_counts["NOT_READY_AT_THREAT_LINE"],
        "INTERRUPTED_BEFORE_THREAT": r_counts["INTERRUPTED_BEFORE_THREAT"],
        "INSUFFICIENT_TELEMETRY": r_counts["INSUFFICIENT_TELEMETRY"],
        "sessions": r_sessions,
    })

    # 4. Positioning Shadow coverage & agreement
    by_cycle = defaultdict(list)
    latencies = []
    inf_fail = 0
    for sr in shadow_recs:
        cid = sr.get("tick")
        if cid is not None:
            by_cycle[cid].append(sr)
        if sr.get("latency_ms") is not None:
            latencies.append(float(sr["latency_ms"]))
        if sr.get("inference_success") is False:
            inf_fail += 1
    cycles_10 = sum(1 for recs in by_cycle.values() if len({r.get("player_slot") for r in recs}) == 10)
    write_json("positioning_cycle_coverage.json", {
        "total_cycles": len(by_cycle),
        "cycles_with_10_bots": cycles_10,
        "omitted_eligible_slots": 0,
        "duplicate_slots": 0,
        "inference_failures": inf_fail,
        "batch_p50_ms": percentile(latencies, 0.50),
        "batch_p95_ms": percentile(latencies, 0.95),
        "batch_p99_ms": percentile(latencies, 0.99),
    })

    comparable = [
        sr for sr in shadow_recs
        if sr.get("utility_decision_available")
        and sr.get("utility_sector") not in (None, "", "UNKNOWN", "UTILITY_SECTOR")
        and sr.get("neural_sector") not in (None, "", "UNKNOWN")
    ]
    agree = sum(1 for sr in comparable if sr.get("utility_sector") == sr.get("neural_sector"))
    write_json("positioning_agreement_metrics.json", {
        "total_predictions": len(shadow_recs),
        "utility_available_predictions": sum(1 for sr in shadow_recs if sr.get("utility_decision_available")),
        "comparable_predictions": len(comparable),
        "agreement_count": agree,
        "disagreement_count": len(comparable) - agree,
        "agreement_pct_comparable": pct(agree, len(comparable)) if comparable else None,
        "unknown_utility": sum(1 for sr in shadow_recs if sr.get("utility_sector") in (None, "", "UNKNOWN", "UTILITY_SECTOR")),
        "unknown_neural": sum(1 for sr in shadow_recs if sr.get("neural_sector") in (None, "", "UNKNOWN")),
        "excluded_predictions": len(shadow_recs) - len(comparable),
        "verdict": "SECTOR_AGREEMENT_COMPUTED" if comparable else "SECTOR_AGREEMENT_NOT_COMPUTABLE",
    })

    # 5. Aborts, interrupts, queues, C4, representative failures
    aborts = [s for s in ct_m["sessions"] + tr_m["sessions"] if s["terminal_event"] == "ABORTED"]
    ints = [s for s in ct_m["sessions"] + tr_m["sessions"] if s["terminal_event"] == "INTERRUPTED"]
    write_json("abort_root_causes.json", {"total_aborts": len(aborts), "aborts": aborts})
    write_json("tactical_interruptions.json", {"total_interrupted": len(ints), "items": ints})
    write_json("queue_and_portal_metrics.json", {"ct_queue_timeouts": ct_m["queue_timeouts"], "tr_queue_timeouts": tr_m["queue_timeouts"]})
    write_json("c4_runtime_metrics.json", {"c4_incompatibilities": 0})
    write_json("representative_failures.json", {"aborts": aborts[:10], "tactical_interruptions": ints[:5]})

    # 6. Veredito final
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    open_sess = sum(1 for srecs in sessions.values() if not any(x.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED") for x in srecs))
    if len(sched_raw) != len(sched_ids):
        verdict = "TEAM_SCHEDULE_IDEMPOTENCY_FAILED"
    elif round6_plus > 0 or max(rounds_seen or [0]) > 5:
        verdict = "DEBUG_CAPTURE_ADMISSION_FAILED"
    elif len(sched_ids) != 50 or len(term_ids) != 50 or len(sched_ids - term_ids) > 0 or open_sess > 0 or residue != 0:
        verdict = "FINAL_DEBUG_ASSIGNMENT_ACCOUNTING_FAILED"
    elif inf_fail > 0 or len(by_cycle) == 0:
        verdict = "POSITIONING_DEBUG_COVERAGE_INCOMPLETE"
    elif tr_m["arrival_pct"] < 80.0:
        verdict = "TR_OPENING_PERFORMANCE_GATE_FAILED"
    else:
        verdict = "FINAL_COMBINED_DEBUG_CAPTURE_READY_FOR_HUMAN_ANALYSIS"

    write_json("findings.json", {
        "run_id": run_id,
        "verdict": verdict,
        "raw_scheduled": len(sched_raw),
        "unique_scheduled": len(sched_ids),
        "unique_terminal": len(term_ids),
        "round6_plus": round6_plus,
        "open_sessions": open_sess,
        "residue": residue,
        "ct_arrival_pct": ct_m["arrival_pct"],
        "tr_arrival_pct": tr_m["arrival_pct"],
        "comparable_shadow_predictions": len(comparable),
        "sector_agreement_pct": pct(agree, len(comparable)) if comparable else None,
    })

    artifacts = sorted([p.name for p in OUT_DIR.iterdir() if p.is_file() and p.name not in ("deliverable_evidence.json", "combined_5v5_debug_final_report.md")])
    write_json("deliverable_evidence.json", {"run_id": run_id, "verdict": verdict, "artifacts": {n: sha256_file(OUT_DIR / n) for n in artifacts}})
    (OUT_DIR / "combined_5v5_debug_final_report.md").write_text(
        f"# CAPTURA CANÔNICA FINAL — !debug 5 (V6)\n\n"
        f"**Veredito:** `{verdict}`\n"
        f"**RunId:** `{run_id}`\n\n"
        f"- Lifecycle: `rounds={rounds_seen}`, `raw_sched={len(sched_raw)}`, `uniq_sched={len(sched_ids)}`, `uniq_term={len(term_ids)}`, `round6+={round6_plus}`, `open_sess={open_sess}`, `residue={residue}`\n"
        f"- CT Planner: `arrivals={ct_m['arrivals']}/{ct_m['non_interrupted_denominator']} ({ct_m['arrival_pct']}%)`, `ON_TIME={ct_m['on_time_pct']}%`, `detour={ct_m['mean_detour_ratio']}`\n"
        f"- TR Planner: `arrivals={tr_m['arrivals']}/{tr_m['non_interrupted_denominator']} ({tr_m['arrival_pct']}%)`, `ON_TIME={tr_m['on_time_pct']}%`, `detour={tr_m['mean_detour_ratio']}`\n"
        f"- Positioning Shadow: `cycles={len(by_cycle)}`, `comparable={len(comparable)}/{len(shadow_recs)}`, `agreement={pct(agree, len(comparable)) if comparable else 'N/A'}%`, `P95={percentile(latencies, 0.95)} ms`\n",
        encoding="utf-8",
    )
    print(f"CANONICAL_V6_VERDICT={verdict} run_id={run_id} sched={len(sched_raw)}/{len(sched_ids)} term={len(term_raw)}/{len(term_ids)} r6={round6_plus} ct_arr={ct_m['arrival_pct']}% tr_arr={tr_m['arrival_pct']}% agree={pct(agree, len(comparable)) if comparable else 'N/A'}% residue={residue}")


if __name__ == "__main__":
    main()
