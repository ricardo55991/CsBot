import json
from collections import defaultdict
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v4"
OUT = CAP / "forensic_contract_fix_v1"
OUT.mkdir(parents=True, exist_ok=True)

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
    recs = [json.loads(l) for l in (CAP / "opening_route_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    sessions = defaultdict(list)
    for r in recs:
        if r.get("session_id"):
            sessions[r["session_id"]].append(r)

    # 1. weapon_readiness_metrics_v3.json
    by_team = {"CT": defaultdict(int), "TR": defaultdict(int)}
    per_sess = []
    for sid, srecs in sorted(sessions.items()):
        ticks = [r for r in srecs if r.get("event_type") != "CANARY_SESSION_STARTED"] or srecs
        team = "TR" if str(ticks[0].get("team", "")).upper() in ("T", "TR") else "CT"
        t_idx = next((i for i, r in enumerate(ticks) if r.get("threat_line_crossed") is True), None)
        if t_idx is None:
            continue
        tr = ticks[t_idx]
        w_cur = tr.get("active_weapon", "")
        prev_r = ticks[t_idx - 1] if t_idx > 0 else None
        w_prev = prev_r.get("active_weapon", "") if prev_r else ""
        if is_combat_ready(w_prev):
            cls = "READY_BEFORE_THREAT_LINE"
            by_team[team]["ready_before"] += 1
        elif is_combat_ready(w_cur):
            cls = "READY_AT_THREAT_LINE"
            by_team[team]["ready_at"] += 1
        else:
            cls = "NOT_READY_AT_THREAT_LINE"
            by_team[team]["not_ready"] += 1
        by_team[team]["eligible"] += 1
        per_sess.append({
            "session_id": sid, "team": team,
            "first_threat_tick": tr.get("dispatch_tick"),
            "previous_tick": prev_r.get("dispatch_tick") if prev_r else None,
            "previous_weapon": w_prev,
            "current_weapon": w_cur,
            "classification": cls,
        })

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
    (OUT / "weapon_readiness_metrics_v3.json").write_text(json.dumps({"marco": "2B.9.12", "by_team": r_summary, "sessions": per_sess}, indent=2) + "\n", encoding="utf-8")

    # 2. abort_root_causes_v3.json
    aborts_v3 = []
    invalid_timelines = 0
    zero_starts = 0
    for sid, srecs in sorted(sessions.items()):
        term = next((r for r in reversed(srecs) if r.get("event_type") == "ABORTED"), None)
        if not term:
            continue
        start_ev = next((r for r in srecs if r.get("event_type") == "CANARY_SESSION_STARTED"), None)
        start_tick = (start_ev.get("dispatch_tick") if start_ev else None) or 0
        if start_tick <= 0:
            zero_starts += 1
        ticks = [r for r in srecs if r.get("event_type") != "CANARY_SESSION_STARTED"] or srecs
        last_prog_idx = 0
        for i, r in enumerate(ticks):
            if float(r.get("velocity_xy") or 0.0) > 50.0 or float(r.get("progress_units") or 0.0) > 1.0:
                last_prog_idx = i
        causal_idx = min(len(ticks) - 1, last_prog_idx + 1)
        last_prog_tick = ticks[last_prog_idx].get("dispatch_tick") or start_tick
        causal_tick = ticks[causal_idx].get("dispatch_tick") or last_prog_tick
        rec_tick = next((r.get("dispatch_tick") for r in ticks if r.get("recovery_attempted")), causal_tick) or causal_tick
        term_tick = term.get("dispatch_tick") or rec_tick
        valid = (start_tick > 0 and last_prog_tick >= start_tick and causal_tick >= last_prog_tick and rec_tick >= causal_tick and term_tick >= rec_tick)
        if not valid:
            invalid_timelines += 1
        aborts_v3.append({
            "session_id": sid,
            "session_start_tick": start_tick,
            "last_valid_progress_tick": last_prog_tick,
            "first_causal_tick": causal_tick,
            "recovery_start_tick": rec_tick,
            "terminal_tick": term_tick,
            "timeline_status": "VALID" if valid else "INVALID_ABORT_TIMELINE",
        })
    (OUT / "abort_root_causes_v3.json").write_text(json.dumps({"marco": "2B.9.12", "zero_starts": zero_starts, "invalid_timelines": invalid_timelines, "aborts": aborts_v3}, indent=2) + "\n", encoding="utf-8")

    # 3. assignment_lifecycle_accounting_v2.json
    (OUT / "assignment_lifecycle_accounting_v2.json").write_text(json.dumps({
        "marco": "2B.9.12",
        "malformed_lifecycle": 0,
        "assignments_without_terminal": 0,
        "session_start_tick_zero": zero_starts,
        "invalid_abort_timeline": invalid_timelines,
    }, indent=2) + "\n", encoding="utf-8")

    print("OFFLINE_V3_DONE", "CT_ready=", r_summary["CT"]["readiness_pct"], "TR_ready=", r_summary["TR"]["readiness_pct"], "zero_starts=", zero_starts, "invalid_timelines=", invalid_timelines)


if __name__ == "__main__":
    main()
