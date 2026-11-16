import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
SERVER_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")
OUT_DIR = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v5"
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
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def write_json(name: str, obj):
    (OUT_DIR / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d > 0 else 0.0


def main():
    # 1. Materializar logs brutos
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
    run_id = run_starts[-1]["RunId"] if run_starts else "RUN_IDENTITY_NOT_PROVEN"

    life_recs = [r for r in life_raw if r.get("RunId") == run_id and r.get("RoundId", 0) in (1, 2, 3, 4, 5)]
    opening_recs = [r for r in read_jsonl(OUT_DIR / "opening_route_telemetry.jsonl") if r.get("round") in (1, 2, 3, 4, 5)]
    shadow_recs = [r for r in read_jsonl(OUT_DIR / "positioning_shadow_telemetry.jsonl") if r.get("round_id") in (1, 2, 3, 4, 5)]
    auth_acct = json.loads((SERVER_LOGS / "canary_authority_accounting.json").read_text(encoding="utf-8")) if (SERVER_LOGS / "canary_authority_accounting.json").exists() else {}

    # Materializar debug_match.jsonl
    team_alias_used = False
    with (OUT_DIR / "debug_match.jsonl").open("w", encoding="utf-8") as df:
        for sr in shadow_recs:
            raw_t = str(sr.get("team", "")).upper()
            if raw_t == "T":
                team_alias_used = True
            df.write(json.dumps({
                "round": sr.get("round_id"),
                "tick": sr.get("tick"),
                "team": "TR" if raw_t in ("T", "TR") else "CT",
                "player_pseudonym": sr.get("player_slot"),
                "utility_state": sr.get("utility_state"),
                "utility_sector": sr.get("utility_sector"),
                "utility_spot": sr.get("utility_spot"),
                "neural_state": sr.get("neural_state"),
                "neural_sector": sr.get("neural_sector"),
                "neural_spot": sr.get("neural_spot"),
                "confidence_by_head": sr.get("confidence_by_head"),
            }) + "\n")

    # 2. Assignment lifecycle accounting (rounds 1..5)
    by_assign = defaultdict(list)
    for r in life_recs:
        if r.get("AssignmentId"):
            by_assign[r["AssignmentId"]].append(r)

    scheduled = sum(1 for r in life_recs if r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED")
    state_changed = sum(1 for r in life_recs if r.get("EventType") == "OPENING_ASSIGNMENT_STATE_CHANGED")
    terminal = sum(1 for r in life_recs if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL")
    without_term = sum(1 for recs in by_assign.values() if not any(r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL" for r in recs))
    dup_term = sum(max(0, sum(1 for r in recs if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL") - 1) for recs in by_assign.values())

    write_json("assignment_lifecycle_accounting.json", {
        "run_id": run_id,
        "official_rounds": [1, 2, 3, 4, 5],
        "scheduled": scheduled,
        "state_changed": state_changed,
        "terminal": terminal,
        "assignments_without_terminal": without_term,
        "duplicate_terminals": dup_term,
        "team_label_alias_used": "TEAM_LABEL_ALIAS_USED" if team_alias_used else "NONE",
    })

    # 3. Sessões & métricas por time
    sessions = defaultdict(list)
    for r in opening_recs:
        if r.get("session_id"):
            sessions[r["session_id"]].append(r)

    def summarize_team(team_name: str):
        ts = []
        for sid, srecs in sessions.items():
            raw_t = str(srecs[0].get("team", "")).upper()
            t = "TR" if raw_t in ("T", "TR") else "CT"
            if t != team_name:
                continue
            rlast = srecs[-1]
            term = next((r for r in reversed(srecs) if r.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")), rlast)
            ts.append({
                "session_id": sid,
                "round": srecs[0].get("round"),
                "destination": srecs[0].get("intended_destination", ""),
                "terminal_event": term.get("event_type"),
                "arrival_status": term.get("arrival_status", ""),
                "detour_ratio": round(term.get("traveled_distance", 0.0) / max(1.0, term.get("expected_distance", 1.0)), 4) if term.get("expected_distance", 0.0) > 0 else 1.0,
            })
        non_int = [s for s in ts if s["terminal_event"] != "INTERRUPTED"]
        denom = len(non_int)
        arrivals = sum(1 for s in non_int if s["arrival_status"] in ("ON_TIME", "LATE"))
        on_time = sum(1 for s in non_int if s["arrival_status"] == "ON_TIME")
        return {
            "team": team_name,
            "controlled_sessions": len(ts),
            "completed": sum(1 for s in ts if s["terminal_event"] == "COMPLETED"),
            "interrupted": sum(1 for s in ts if s["terminal_event"] == "INTERRUPTED"),
            "aborted": sum(1 for s in ts if s["terminal_event"] == "ABORTED"),
            "non_interrupted_denominator": denom,
            "arrivals": arrivals,
            "arrival_pct": pct(arrivals, denom),
            "on_time": on_time,
            "on_time_pct": pct(on_time, denom),
            "mean_detour_ratio": round(sum(s["detour_ratio"] for s in non_int) / max(1, denom), 4),
        }

    ct_m = summarize_team("CT")
    tr_m = summarize_team("TR")
    write_json("ct_route_metrics.json", ct_m)
    write_json("tr_route_metrics.json", tr_m)

    # 4. Weapon readiness (destacando todas as 5 categorias)
    readiness_counts = defaultdict(int)
    for sid, srecs in sessions.items():
        ticks = sorted([r for r in srecs if r.get("event_type") != "CANARY_SESSION_STARTED"], key=lambda x: (x.get("dispatch_tick") or 0))
        if not ticks:
            readiness_counts["INSUFFICIENT_TELEMETRY"] += 1
            continue
        t_idx = next((i for i, r in enumerate(ticks) if r.get("threat_line_crossed") is True), None)
        if t_idx is None:
            term_ev = next((r.get("event_type") for r in reversed(srecs) if r.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")), None)
            if term_ev == "INTERRUPTED":
                readiness_counts["INTERRUPTED_BEFORE_THREAT"] += 1
            else:
                readiness_counts["INSUFFICIENT_TELEMETRY"] += 1
            continue
        w_cur = (ticks[t_idx].get("active_weapon") or "").strip().lower()
        prev_r = ticks[t_idx - 1] if t_idx > 0 else None
        w_prev = (prev_r.get("active_weapon") or "").strip().lower() if prev_r else ""
        if w_cur not in COMBAT_WEAPONS:
            readiness_counts["NOT_READY_AT_THREAT_LINE"] += 1
        elif w_prev in COMBAT_WEAPONS:
            readiness_counts["READY_BEFORE_THREAT_LINE"] += 1
        else:
            readiness_counts["READY_AT_THREAT_LINE"] += 1

    write_json("weapon_readiness_metrics.json", {
        "READY_BEFORE_THREAT_LINE": readiness_counts["READY_BEFORE_THREAT_LINE"],
        "READY_AT_THREAT_LINE": readiness_counts["READY_AT_THREAT_LINE"],
        "NOT_READY_AT_THREAT_LINE": readiness_counts["NOT_READY_AT_THREAT_LINE"],
        "INTERRUPTED_BEFORE_THREAT": readiness_counts["INTERRUPTED_BEFORE_THREAT"],
        "INSUFFICIENT_TELEMETRY": readiness_counts["INSUFFICIENT_TELEMETRY"],
    })

    # 5. Aborts, Positioning Shadow, Representative Failures, Findings
    aborts = []
    for sid, srecs in sessions.items():
        term = next((r for r in reversed(srecs) if r.get("event_type") == "ABORTED"), None)
        if term:
            aborts.append({"session_id": sid, "round": term.get("round"), "destination": term.get("intended_destination"), "reason": term.get("completion_reason") or term.get("fallback_reason")})
    write_json("abort_root_causes.json", {"total_aborts": len(aborts), "aborts": aborts})

    agree = sum(1 for sr in shadow_recs if sr.get("utility_sector") == sr.get("neural_sector"))
    write_json("positioning_agreement_metrics.json", {
        "total_predictions": len(shadow_recs),
        "sector_agreement_count": agree,
        "sector_agreement_pct": pct(agree, len(shadow_recs)),
    })
    write_json("representative_failures.json", {"aborts": aborts[:10]})

    residue = auth_acct.get("accounting_residue", 0) if isinstance(auth_acct, dict) else 0
    verdict = "FINAL_COMBINED_DEBUG_CAPTURE_READY_FOR_HUMAN_ANALYSIS" if (scheduled == 50 and terminal == 50 and without_term == 0 and dup_term == 0 and residue == 0) else "FINAL_COMBINED_DEBUG_CAPTURE_INCOMPLETE"
    write_json("findings.json", {
        "run_id": run_id,
        "verdict": verdict,
        "scheduled": scheduled,
        "terminal": terminal,
        "without_term": without_term,
        "residue": residue,
        "team_label_alias_used": "TEAM_LABEL_ALIAS_USED" if team_alias_used else "NONE",
    })

    artifacts = [p.name for p in OUT_DIR.iterdir() if p.is_file() and p.name not in ("deliverable_evidence.json", "combined_5v5_debug_final_report.md")]
    write_json("deliverable_evidence.json", {"run_id": run_id, "verdict": verdict, "artifacts": {n: sha256_file(OUT_DIR / n) for n in sorted(artifacts)}})

    (OUT_DIR / "combined_5v5_debug_final_report.md").write_text(
        f"# Captura Final Combinada de 5 Rounds (!debug 5)\n\n"
        f"**Veredito:** `{verdict}`\n"
        f"**RunId:** `{run_id}`\n\n"
        f"- Assignments (Rounds 1–5): `scheduled={scheduled}/50`, `terminal={terminal}/50`, `without_term={without_term}`, `dup={dup_term}`, `residue={residue}`\n"
        f"- CT Planner: `arrivals={ct_m['arrivals']}/{ct_m['non_interrupted_denominator']} ({ct_m['arrival_pct']}%)`, `ON_TIME={ct_m['on_time_pct']}%`, `detour={ct_m['mean_detour_ratio']}`\n"
        f"- TR Planner: `arrivals={tr_m['arrivals']}/{tr_m['non_interrupted_denominator']} ({tr_m['arrival_pct']}%)`, `ON_TIME={tr_m['on_time_pct']}%`, `detour={tr_m['mean_detour_ratio']}`\n"
        f"- Positioning Shadow: `predictions={len(shadow_recs)}`, `sector_agreement={pct(agree, len(shadow_recs))}%`\n",
        encoding="utf-8",
    )
    print(f"FINAL_AUDIT_VERDICT={verdict} run_id={run_id} sched={scheduled} term={terminal} without_term={without_term} ct_arr={ct_m['arrival_pct']}% tr_arr={tr_m['arrival_pct']}% shadow={len(shadow_recs)} residue={residue}")


if __name__ == "__main__":
    main()
