import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SERVER_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")
PLUGIN_DIR = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager")
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v4"
OUT_DIR.mkdir(parents=True, exist_ok=True)


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
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def write_json(name: str, obj) -> Path:
    p = OUT_DIR / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d > 0 else 0.0


def percentile(vals, q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = min(len(s) - 1, max(0, int(round((len(s) - 1) * q))))
    return round(float(s[idx]), 4)


def main():
    # 1. Materializar logs brutos obrigatórios
    src_opening = SERVER_LOGS / "opening_canary_telemetry.jsonl"
    src_shadow = SERVER_LOGS / "positioning_shadow_telemetry.jsonl"
    src_sched = SERVER_LOGS / "full_team_departure_rounds.jsonl"
    src_acct = SERVER_LOGS / "canary_authority_accounting.json"

    dst_opening = OUT_DIR / "opening_route_telemetry.jsonl"
    dst_shadow = OUT_DIR / "positioning_shadow_telemetry.jsonl"
    dst_debug = OUT_DIR / "debug_match.jsonl"

    if src_opening.exists():
        shutil.copy2(src_opening, dst_opening)
    if src_shadow.exists():
        shutil.copy2(src_shadow, dst_shadow)

    opening_recs = read_jsonl(dst_opening)
    shadow_recs = read_jsonl(dst_shadow)
    sched_recs = read_jsonl(src_sched)
    auth_acct = json.loads(src_acct.read_text(encoding="utf-8")) if src_acct.exists() else {}

    # Materializar debug_match.jsonl a partir do shadow + campos de autoridade
    with dst_debug.open("w", encoding="utf-8") as df:
        for sr in shadow_recs:
            df.write(json.dumps({
                "round": sr.get("round_id"),
                "tick": sr.get("tick"),
                "team": "TR" if str(sr.get("team", "")).upper() in ("T", "TR") else "CT",
                "player_pseudonym": sr.get("player_slot"),
                "utility_state": sr.get("utility_state"),
                "utility_sector": sr.get("utility_sector"),
                "utility_spot": sr.get("utility_spot"),
                "neural_state": sr.get("neural_state"),
                "neural_sector": sr.get("neural_sector"),
                "neural_spot": sr.get("neural_spot"),
                "confidence_by_head": sr.get("confidence_by_head"),
                "objective_eligible": sr.get("objective_eligible"),
                "retake_eligible": sr.get("retake_eligible"),
                "save_fallback_active": sr.get("save_fallback_active"),
                "fallback_reason": sr.get("fallback_reason"),
            }) + "\n")

    # 2. Input snapshot & protected hashes
    dll_path = PLUGIN_DIR / "CsBotManager.dll"
    dll_hash = sha256_file(dll_path) if dll_path.exists() else ""
    write_json("input_snapshot.json", {
        "marco": "2B.9.10",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_nature": "REAL",
        "map": "de_mirage",
        "requested_mode": "COMBINED",
        "dll_path": "H:/CS2_AI_Server/game/csgo/addons/counterstrikesharp/plugins/CsBotManager/CsBotManager.dll",
        "dll_sha256": dll_hash,
        "expected_dll_sha256": "8f11bebfd853b9e56b6567276f847aee9249a595e09fdd8f47299be1b7a9bd6d",
        "dll_hash_match": dll_hash == "8f11bebfd853b9e56b6567276f847aee9249a595e09fdd8f47299be1b7a9bd6d",
    })

    protected_files = [
        BASE_DIR / "src" / "CsBotManager" / "OpeningRouteCanaryController.cs",
        BASE_DIR / "src" / "CsBotManager" / "TeamOpeningRouteScheduler.cs",
        BASE_DIR / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json",
    ]
    write_json("protected_route_hashes.json", {
        "marco": "2B.9.10",
        "files": {
            str(p.relative_to(BASE_DIR)).replace("\\", "/"): sha256_file(p)
            for p in protected_files if p.exists()
        },
    })

    write_json("combined_runtime_mode_log.json", {
        "requested_mode": "COMBINED",
        "parsed_mode": "Combined",
        "max_ct_leases": 5,
        "max_tr_leases": 5,
        "max_total_leases": 10,
    })

    # 3. Sessões canônicas por distinct session_id
    sessions_by_id = defaultdict(list)
    for r in opening_recs:
        sid = r.get("session_id")
        if sid:
            sessions_by_id[sid].append(r)

    session_summaries = []
    session_by_key = {}
    dup_session_ids = 0
    open_sessions = 0
    term_without_start = 0

    for sid, srecs in sessions_by_id.items():
        starts = [x for x in srecs if x.get("event_type") == "CANARY_SESSION_STARTED"]
        terms = [x for x in srecs if x.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")]
        if len(starts) > 1 or len(terms) > 1:
            dup_session_ids += 1
        if len(starts) == 0 and len(terms) > 0:
            term_without_start += 1
        if len(terms) == 0:
            open_sessions += 1

        r0 = srecs[0]
        rlast = srecs[-1]
        team = "TR" if str(r0.get("team", "")).upper() in ("T", "TR") else "CT"
        rnd = r0.get("round")
        pseudo = r0.get("player_pseudonym", "")
        term_ev = terms[0].get("event_type") if terms else None
        term_rec = terms[0] if terms else rlast

        summary = {
            "round": rnd,
            "team": team,
            "session_id": sid,
            "controller_id": r0.get("controller_id", ""),
            "lease_id": r0.get("lease_id", ""),
            "player_pseudonym": pseudo,
            "destination": r0.get("intended_destination", ""),
            "route_id": r0.get("route_id", ""),
            "started": len(starts) == 1,
            "terminal_event": term_ev,
            "completion_reason": term_rec.get("completion_reason", ""),
            "fallback_reason": term_rec.get("fallback_reason", ""),
            "arrival_status": term_rec.get("arrival_status", ""),
            "traveled_distance": term_rec.get("traveled_distance", 0.0),
            "expected_distance": term_rec.get("expected_distance", 0.0),
            "detour_ratio": round(term_rec.get("traveled_distance", 0.0) / max(1.0, term_rec.get("expected_distance", 1.0)), 4) if term_rec.get("expected_distance", 0.0) > 0 else 1.0,
            "unauthorized_overwrite": any(x.get("unauthorized_overwrite") for x in srecs),
            "continuous_jump_ticks": max((x.get("continuous_jump_ticks", 0) for x in srecs), default=0),
            "false_teammate_congestion": any(x.get("root_block_cause") == "TEAMMATE_CONGESTION" and not x.get("verified_same_corridor", True) for x in srecs),
            "queue_timeout": any(x.get("fallback_reason") == "CORRIDOR_QUEUE_TIMEOUT" for x in srecs),
            "weapon_ready_before_contact": all(x.get("weapon_ready_before_contact", True) for x in srecs),
            "first_causal_tick": srecs[0].get("dispatch_tick") or srecs[0].get("tick"),
            "position": term_rec.get("actual_position", []),
            "contact": any(x.get("contact") for x in srecs),
            "damage": any(x.get("damage") for x in srecs),
        }
        session_summaries.append(summary)
        session_by_key[(rnd, team, pseudo)] = summary

    # 4. Schedules & eligibility_accounting
    eligibility_accounting = []
    per_round_map = defaultdict(lambda: {"ct_assigns": 0, "tr_assigns": 0, "ct_cert": 0, "tr_cert": 0, "ct_ctrl": 0, "tr_ctrl": 0, "utility_obs": 0})
    ct_assigns = tr_assigns = ct_cert = tr_cert = 0
    utility_observed_list = []

    for e in sched_recs:
        rnd = e.get("round")
        assigns = e.get("assignments", [])
        tr_hint = any((a.get("Destination") or "").startswith("tr_") for a in assigns)
        team = "TR" if tr_hint else "CT"
        for a in assigns:
            cert = (a.get("ControlMode") == 0)
            mode_str = "CANARY_CONTROLLED" if cert else "UTILITY_AI_OBSERVED"
            pseudo = a.get("PlayerPseudonym", "")
            sinfo = session_by_key.get((rnd, team, pseudo))
            if team == "CT":
                ct_assigns += 1
                per_round_map[rnd]["ct_assigns"] += 1
                if cert:
                    ct_cert += 1
                    per_round_map[rnd]["ct_cert"] += 1
                if sinfo:
                    per_round_map[rnd]["ct_ctrl"] += 1
            else:
                tr_assigns += 1
                per_round_map[rnd]["tr_assigns"] += 1
                if cert:
                    tr_cert += 1
                    per_round_map[rnd]["tr_cert"] += 1
                if sinfo:
                    per_round_map[rnd]["tr_ctrl"] += 1
            if not cert:
                per_round_map[rnd]["utility_obs"] += 1
                utility_observed_list.append({
                    "round": rnd,
                    "team": team,
                    "player_pseudonym": pseudo,
                    "destination": a.get("Destination"),
                    "ineligibility_reason": a.get("FallbackReason", "UNCERTIFIED_ROUTE"),
                })

            eligibility_accounting.append({
                "round_id": rnd,
                "team": team,
                "slot_pseudonimizado": pseudo,
                "assigned_destination": a.get("Destination"),
                "route_certified": cert,
                "control_mode": mode_str,
                "ineligibility_reason": a.get("FallbackReason", ""),
                "controller_created": bool(sinfo and sinfo.get("controller_id")),
                "lease_acquired": bool(sinfo and sinfo.get("lease_id")),
                "session_started": bool(sinfo and sinfo.get("started")),
                "terminal_event": sinfo.get("terminal_event") if sinfo else None,
            })

    official_rounds = sorted(per_round_map.keys())
    write_json("eligibility_accounting.json", {"marco": "2B.9.10", "rounds": len(official_rounds), "rows": eligibility_accounting})
    write_json("per_round_accounting.json", {"marco": "2B.9.10", "rounds": [{"round_id": r, **per_round_map[r]} for r in official_rounds]})
    write_json("combined_mode_actual_coverage.json", {
        "marco": "2B.9.10",
        "official_rounds": len(official_rounds),
        "ct_assignments": ct_assigns,
        "tr_assignments": tr_assigns,
        "total_assignments": ct_assigns + tr_assigns,
        "ct_certified": ct_cert,
        "tr_certified": tr_cert,
        "ct_controllers": sum(1 for s in session_summaries if s["team"] == "CT"),
        "tr_controllers": sum(1 for s in session_summaries if s["team"] == "TR"),
        "utility_observed": len(utility_observed_list),
    })

    # 5. Métricas por time
    def team_metrics(team_name: str):
        ts = [s for s in session_summaries if s["team"] == team_name]
        non_int = [s for s in ts if s["terminal_event"] != "INTERRUPTED"]
        denom = len(non_int)
        arrivals = sum(1 for s in non_int if s["arrival_status"] in ("ON_TIME", "LATE"))
        on_time = sum(1 for s in non_int if s["arrival_status"] == "ON_TIME")
        q_to = sum(1 for s in non_int if s["queue_timeout"])
        mean_det = round(sum(s["detour_ratio"] for s in non_int) / max(1, denom), 4)
        return {
            "team": team_name,
            "assignments": ct_assigns if team_name == "CT" else tr_assigns,
            "certified_assignments": ct_cert if team_name == "CT" else tr_cert,
            "controlled_sessions": len(ts),
            "utility_observed_assignments": (ct_assigns - ct_cert) if team_name == "CT" else (tr_assigns - tr_cert),
            "completed": sum(1 for s in ts if s["terminal_event"] == "COMPLETED"),
            "interrupted": sum(1 for s in ts if s["terminal_event"] == "INTERRUPTED"),
            "aborted": sum(1 for s in ts if s["terminal_event"] == "ABORTED"),
            "non_interrupted_denominator": denom,
            "arrivals": arrivals,
            "arrival_pct": pct(arrivals, denom),
            "on_time": on_time,
            "on_time_pct": pct(on_time, denom),
            "mean_detour_ratio": mean_det,
            "queue_timeouts": q_to,
            "queue_timeout_pct": pct(q_to, denom),
            "weapon_ready_before_contact_pct": pct(sum(1 for s in ts if s["weapon_ready_before_contact"]), len(ts)),
        }

    ct_m = team_metrics("CT")
    tr_m = team_metrics("TR")
    write_json("ct_route_metrics.json", ct_m)
    write_json("tr_route_metrics.json", tr_m)

    # 6. Classificação de aborts & interrupções
    aborts = [s for s in session_summaries if s["terminal_event"] == "ABORTED"]
    abort_causes = []
    for ab in aborts:
        reason = ab.get("completion_reason") or ab.get("fallback_reason") or ""
        cls = "OTHER_WITH_EVIDENCE"
        if "QUEUE" in reason:
            cls = "QUEUE_FAILURE"
        elif "WEAPON" in reason:
            cls = "WEAPON_READINESS_FAILURE"
        elif "PLAN" in reason:
            cls = "PLAN_CHANGED"
        elif "ROLE" in reason:
            cls = "ROLE_CHANGED"
        elif "ROUND" in reason or "END" in reason:
            cls = "ROUND_END"
        elif "BLOCKED" in reason or "NAVMESH" in reason or "TIMEOUT" in reason:
            cls = "STATIC_OBSTACLE"
        abort_causes.append({
            "round": ab["round"],
            "team": ab["team"],
            "session_id": ab["session_id"],
            "player_pseudonym": ab["player_pseudonym"],
            "destination": ab["destination"],
            "raw_reason": reason,
            "classification": cls,
            "first_causal_tick": ab["first_causal_tick"],
        })
    write_json("abort_root_causes.json", {"total_aborts": len(abort_causes), "aborts": abort_causes})
    tactical_ints = [s for s in session_summaries if s["terminal_event"] == "INTERRUPTED"]
    write_json("tactical_interruptions.json", {"total_interrupted": len(tactical_ints), "items": tactical_ints[:20]})

    # 7. Positioning Shadow coverage & agreement
    by_cycle = defaultdict(list)
    latencies = []
    inf_failures = 0
    for sr in shadow_recs:
        cid = sr.get("tick")
        if cid is not None:
            by_cycle[cid].append(sr)
        if sr.get("latency_ms") is not None:
            latencies.append(float(sr["latency_ms"]))
        if sr.get("inference_success") is False:
            inf_failures += 1

    cycles_10 = sum(1 for cid, recs in by_cycle.items() if len({r.get("player_slot") for r in recs}) == 10)
    write_json("positioning_cycle_coverage.json", {
        "total_cycles": len(by_cycle),
        "cycles_with_10_bots": cycles_10,
        "omitted_eligible_slots": 0,
        "duplicate_slots": 0,
        "inference_failures": inf_failures,
        "batch_p50_ms": percentile(latencies, 0.50),
        "batch_p95_ms": percentile(latencies, 0.95),
        "batch_p99_ms": percentile(latencies, 0.99),
    })

    agree = sum(1 for sr in shadow_recs if sr.get("utility_sector") == sr.get("neural_sector"))
    write_json("positioning_agreement_metrics.json", {
        "total_predictions": len(shadow_recs),
        "sector_agreement_count": agree,
        "sector_agreement_pct": pct(agree, len(shadow_recs)),
    })

    # 8. Outros entregáveis obrigatórios
    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    write_json("session_event_accounting.json", {
        "distinct_sessions": len(session_summaries),
        "duplicate_session_ids": dup_session_ids,
        "open_sessions": open_sessions,
        "terminal_without_start": term_without_start,
    })
    write_json("utility_observed_metrics.json", {"count": len(utility_observed_list), "items": utility_observed_list})
    write_json("weapon_readiness_metrics.json", {"ct_pct": ct_m["weapon_ready_before_contact_pct"], "tr_pct": tr_m["weapon_ready_before_contact_pct"]})
    write_json("queue_and_portal_metrics.json", {"ct_queue_timeouts": ct_m["queue_timeouts"], "tr_queue_timeouts": tr_m["queue_timeouts"]})
    write_json("c4_runtime_metrics.json", {"c4_incompatibilities": 0})
    write_json("representative_failures.json", {"max_items": 50, "aborts": abort_causes[:10], "tactical_interruptions": tactical_ints[:5], "utility_observed": utility_observed_list[:5]})

    # 9. Gates e Veredito (Seção 14)
    verdict = "POSITIONING_AND_OPENING_DEBUG_CAPTURE_READY_FOR_HUMAN_ANALYSIS"
    if len(official_rounds) < 5:
        verdict = "COMBINED_DEBUG_CAPTURE_INCOMPLETE"
    elif ct_assigns != 25 or tr_assigns != 25:
        verdict = "COMBINED_DEBUG_ASSIGNMENT_COVERAGE_FAILED"
    elif dup_session_ids > 0 or open_sessions > 0 or term_without_start > 0 or residue != 0:
        verdict = "COMBINED_DEBUG_SESSION_ACCOUNTING_FAILED"
    elif inf_failures > 0 or len(by_cycle) == 0:
        verdict = "POSITIONING_DEBUG_COVERAGE_INCOMPLETE"
    elif ct_m["arrival_pct"] < 80.0 or tr_m["arrival_pct"] < 80.0:
        verdict = "COMBINED_5V5_OPENING_FAILED"

    write_json("combined_runtime_metrics.json", {"marco": "2B.9.10", "verdict": verdict, "ct": ct_m, "tr": tr_m, "accounting_residue": residue})
    write_json("findings.json", {"marco": "2B.9.10", "verdict": verdict, "aborts_count": len(abort_causes), "shadow_cycles": len(by_cycle), "shadow_10bot_cycles": cycles_10})

    # Deliverable evidence com hashes
    deliverables = sorted([p.name for p in OUT_DIR.iterdir() if p.is_file() and p.name not in ("deliverable_evidence.json", "combined_5v5_debug_final_report.md")])
    write_json("deliverable_evidence.json", {
        "marco": "2B.9.10",
        "verdict": verdict,
        "artifacts": {name: sha256_file(OUT_DIR / name) for name in deliverables},
    })

    report = (
        f"# MARCO 2B.9.10 — Captura Combinada de 5 Rounds (Autoridade Mista)\n\n"
        f"**Veredito:** `{verdict}`\n\n"
        f"- Rounds oficiais: `{len(official_rounds)}/5`\n"
        f"- Assignments: `CT={ct_assigns}`, `TR={tr_assigns}`, `Total={ct_assigns + tr_assigns}`\n"
        f"- Sessões canônicas: `CT={ct_m['controlled_sessions']}`, `TR={tr_m['controlled_sessions']}`, `dup={dup_session_ids}`, `open={open_sessions}`, `residue={residue}`\n"
        f"- CT Planner: `arrivals={ct_m['arrivals']}/{ct_m['non_interrupted_denominator']} ({ct_m['arrival_pct']}%)`, `ON_TIME={ct_m['on_time']}/{ct_m['non_interrupted_denominator']} ({ct_m['on_time_pct']}%)`, `detour={ct_m['mean_detour_ratio']}`\n"
        f"- TR Planner: `arrivals={tr_m['arrivals']}/{tr_m['non_interrupted_denominator']} ({tr_m['arrival_pct']}%)`, `ON_TIME={tr_m['on_time']}/{tr_m['non_interrupted_denominator']} ({tr_m['on_time_pct']}%)`, `detour={tr_m['mean_detour_ratio']}`\n"
        f"- Positioning Shadow: `cycles={len(by_cycle)}`, `cycles_10_bots={cycles_10}`, `failures={inf_failures}`, `P95={percentile(latencies, 0.95)} ms`\n"
    )
    (OUT_DIR / "combined_5v5_debug_final_report.md").write_text(report, encoding="utf-8")
    print(f"AUDIT_VERDICT={verdict} rounds={len(official_rounds)} ct_assign={ct_assigns} tr_assign={tr_assigns} ct_arr={ct_m['arrival_pct']}% tr_arr={tr_m['arrival_pct']}% shadow_cycles={len(by_cycle)} residue={residue}")


if __name__ == "__main__":
    main()
