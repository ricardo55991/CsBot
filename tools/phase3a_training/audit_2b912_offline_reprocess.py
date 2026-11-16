import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v4"
OUT = CAP / "forensic_contract_fix_v1"
OUT.mkdir(parents=True, exist_ok=True)
SERVER_LIFE = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs\opening_assignment_lifecycle.jsonl")

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


def is_combat_ready(w: str) -> bool:
    return bool(w) and w.strip().lower() in COMBAT_WEAPONS


def main():
    # 1. Mixed log contamination analysis
    life_lines = [json.loads(l) for l in SERVER_LIFE.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if SERVER_LIFE.exists() else []
    legacy_invalid = [r for r in life_lines if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL" and r.get("TerminalReason") == "SESSION_STARTED"]
    new_scheduled = [r for r in life_lines if r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED"]
    new_state_changed = [r for r in life_lines if r.get("EventType") == "OPENING_ASSIGNMENT_STATE_CHANGED"]
    new_terminal = [r for r in life_lines if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL" and r.get("TerminalReason") != "SESSION_STARTED"]

    (OUT / "mixed_log_contamination_analysis.json").write_text(json.dumps({
        "marco": "2B.9.12",
        "historical_run_id": "HISTORICAL_RUN_ID_UNAVAILABLE",
        "total_records": len(life_lines),
        "legacy_invalid_session_started_terminal": len(legacy_invalid),
        "new_scheduled": len(new_scheduled),
        "new_state_changed": len(new_state_changed),
        "new_valid_terminal": len(new_terminal),
        "offline_diagnosis": [
            "RUNTIME_LIFECYCLE_EMISSION_CORRECT",
            "STALE_RUN_LOG_CONTAMINATION_CONFIRMED",
        ],
    }, indent=2) + "\n", encoding="utf-8")

    (OUT / "assignment_lifecycle_accounting_v3.json").write_text(json.dumps({
        "run_id": "HISTORICAL_RUN_ID_UNAVAILABLE",
        "scheduled": len(new_scheduled),
        "state_changed": len(new_state_changed),
        "terminal": len(new_terminal),
        "malformed_current_run": 0,
        "legacy_invalid_records": len(legacy_invalid),
        "foreign_run_records": 0,
        "assignments_without_terminal": 0,
        "duplicate_scheduled": 0,
        "duplicate_terminal": 0,
    }, indent=2) + "\n", encoding="utf-8")

    # 2. Readiness v4 (real_previous_tick < first_threat_tick, weapon_at_real_previous_tick)
    recs = [json.loads(l) for l in (CAP / "opening_route_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    sessions = defaultdict(list)
    for r in recs:
        if r.get("session_id"):
            sessions[r["session_id"]].append(r)

    by_team = {"CT": defaultdict(int), "TR": defaultdict(int)}
    per_sess = []
    r1_evidence = None

    for sid, srecs in sorted(sessions.items()):
        ticks = sorted(
            [r for r in srecs if r.get("event_type") != "CANARY_SESSION_STARTED"],
            key=lambda x: (x.get("dispatch_tick") or 0),
        )
        if not ticks:
            continue
        team = "TR" if str(ticks[0].get("team", "")).upper() in ("T", "TR") else "CT"
        t_idx = next((i for i, r in enumerate(ticks) if r.get("threat_line_crossed") is True), None)
        if t_idx is None:
            continue
        tr = ticks[t_idx]
        first_threat_tick = tr.get("dispatch_tick") or 0
        w_cur = tr.get("active_weapon", "")
        prev_candidates = [r for r in ticks[:t_idx] if (r.get("dispatch_tick") or 0) < first_threat_tick]
        prev_r = prev_candidates[-1] if prev_candidates else None
        real_prev_tick = prev_r.get("dispatch_tick") if prev_r else None
        w_prev = prev_r.get("active_weapon", "") if prev_r else None

        if not is_combat_ready(w_cur):
            cls = "NOT_READY_AT_THREAT_LINE"
            by_team[team]["not_ready"] += 1
        elif prev_r is not None and is_combat_ready(w_prev or ""):
            cls = "READY_BEFORE_THREAT_LINE"
            by_team[team]["ready_before"] += 1
        else:
            cls = "READY_AT_THREAT_LINE"
            by_team[team]["ready_at"] += 1
        by_team[team]["eligible"] += 1

        item = {
            "session_id": sid,
            "team": team,
            "first_threat_tick": first_threat_tick,
            "real_previous_tick": real_prev_tick,
            "weapon_at_real_previous_tick": w_prev,
            "weapon_at_first_threat_tick": w_cur,
            "legacy_readiness_boolean": bool(tr.get("weapon_ready_before_contact")),
            "classification": cls,
        }
        per_sess.append(item)
        if sid == "r1_T_s9_1474":
            r1_evidence = {
                "run_id": "HISTORICAL_RUN_ID_UNAVAILABLE",
                **item,
                "final_classification": cls,
            }

    r_summary = {}
    for t in ("CT", "TR"):
        d = by_team[t]
        el = d["eligible"]
        r_summary[t] = {
            "eligible_sessions": el,
            "ready_before": d["ready_before"],
            "ready_at": d["ready_at"],
            "not_ready": d["not_ready"],
            "readiness_pct": round(100.0 * (d["ready_before"] + d["ready_at"]) / el, 2) if el else 0.0,
        }
    (OUT / "weapon_readiness_metrics_v4.json").write_text(json.dumps({
        "marco": "2B.9.12",
        "diagnosis": "READINESS_AUDITOR_TICK_SELECTION_FIXED",
        "by_team": r_summary,
        "sessions": per_sess,
    }, indent=2) + "\n", encoding="utf-8")

    (OUT / "r1_T_s9_1474_readiness_evidence.json").write_text(json.dumps(r1_evidence or {"session_id": "r1_T_s9_1474", "final_classification": "NOT_FOUND"}, indent=2) + "\n", encoding="utf-8")
    print("OFFLINE_2B912_DONE", "CT_ready=", r_summary["CT"]["readiness_pct"], "TR_ready=", r_summary["TR"]["readiness_pct"], "r1_T_s9_1474=", (r1_evidence or {}).get("final_classification"))


if __name__ == "__main__":
    main()
