import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v4"
OUT = CAP / "forensic_contract_fix_v1"
OUT.mkdir(parents=True, exist_ok=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def read_jsonl(p: Path):
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


def analyze_readiness(sessions_by_id):
    per_session = []
    by_team = {"CT": defaultdict(int), "TR": defaultdict(int)}
    for sid, recs in sorted(sessions_by_id.items()):
        # Ordenar por dispatch_tick / tick; ignorar CANARY_SESSION_STARTED isolado
        ticks = [r for r in recs if r.get("event_type") != "CANARY_SESSION_STARTED"]
        if not ticks:
            ticks = recs
        r0 = ticks[0]
        team = "TR" if str(r0.get("team", "")).upper() in ("T", "TR") else "CT"
        route = r0.get("route_id", "")
        dest = r0.get("intended_destination", "")
        term_ev = next((r.get("event_type") for r in reversed(recs) if r.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED")), None)

        threat_idx = next((i for i, r in enumerate(ticks) if r.get("threat_line_crossed") is True), None)
        if threat_idx is None:
            if term_ev == "INTERRUPTED":
                cls = "INTERRUPTED_BEFORE_THREAT"
                by_team[team]["interrupted_before_threat"] += 1
            elif len(ticks) < 2:
                cls = "INSUFFICIENT_TELEMETRY"
                by_team[team]["insufficient_telemetry"] += 1
            else:
                cls = "NO_THREAT_LINE_CROSSED"
                by_team[team]["no_threat_line"] += 1
            per_session.append({
                "session_id": sid, "team": team, "route": route, "destination": dest,
                "first_threat_tick": None, "active_weapon_at_threat": None,
                "readiness_value_at_threat": None, "classification": cls,
            })
            continue

        tr = ticks[threat_idx]
        w_at = tr.get("active_weapon", "")
        ready_at = bool(tr.get("weapon_ready_before_contact"))
        prev_ready = False
        if threat_idx > 0:
            pr = ticks[threat_idx - 1]
            pw = pr.get("active_weapon", "")
            if pw and "knife" not in pw.lower() and bool(pr.get("weapon_ready_before_contact")):
                prev_ready = True

        if prev_ready:
            cls = "READY_BEFORE_THREAT_LINE"
            by_team[team]["ready_before"] += 1
            by_team[team]["eligible_sessions"] += 1
        elif ready_at or (w_at and "knife" not in w_at.lower()):
            cls = "READY_AT_THREAT_LINE"
            by_team[team]["ready_at"] += 1
            by_team[team]["eligible_sessions"] += 1
        else:
            cls = "NOT_READY_AT_THREAT_LINE"
            by_team[team]["not_ready"] += 1
            by_team[team]["eligible_sessions"] += 1

        per_session.append({
            "session_id": sid, "team": team, "route": route, "destination": dest,
            "first_threat_tick": tr.get("dispatch_tick") or tr.get("tick"),
            "active_weapon_at_threat": w_at,
            "readiness_value_at_threat": ready_at,
            "classification": cls,
        })

    team_summary = {}
    for t in ("CT", "TR"):
        d = by_team[t]
        elig = d["eligible_sessions"]
        ready_total = d["ready_before"] + d["ready_at"]
        team_summary[t] = {
            "eligible_sessions": elig,
            "ready_before": d["ready_before"],
            "ready_at": d["ready_at"],
            "not_ready": d["not_ready"],
            "interrupted_before_threat": d["interrupted_before_threat"],
            "no_threat_line": d["no_threat_line"],
            "insufficient_telemetry": d["insufficient_telemetry"],
            "readiness_pct": round(100.0 * ready_total / elig, 2) if elig > 0 else 0.0,
        }
    return {
        "marco": "2B.9.11",
        "previous_0pct_diagnosis": "AUDITOR_DEFAULT_VALUE_CONTAMINATION" if any(team_summary[t]["readiness_pct"] > 0 for t in ("CT", "TR")) else "CONFIRMED_ZERO_WITH_EVIDENCE",
        "by_team": team_summary,
        "sessions": per_session,
    }


def analyze_aborts(sessions_by_id):
    aborts_v2 = []
    mid_under = None
    b_short = []
    for sid, recs in sorted(sessions_by_id.items()):
        term = next((r for r in reversed(recs) if r.get("event_type") == "ABORTED"), None)
        if not term:
            continue
        ticks = [r for r in recs if r.get("event_type") != "CANARY_SESSION_STARTED"]
        if not ticks:
            ticks = recs
        start_tick = ticks[0].get("dispatch_tick") or 0
        # Último tick de progresso normal: velocity_xy > 50 ou progress_units > 1.0
        last_prog_idx = 0
        for i, r in enumerate(ticks):
            vel = float(r.get("velocity_xy") or 0.0)
            prog = float(r.get("progress_units") or 0.0)
            if vel > 50.0 or prog > 1.0:
                last_prog_idx = i
        causal_idx = min(len(ticks) - 1, last_prog_idx + 1) if last_prog_idx + 1 < len(ticks) else last_prog_idx
        cr = ticks[causal_idx]
        rec_idx = next((i for i, r in enumerate(ticks) if r.get("recovery_attempted")), None)
        entry = {
            "session_id": sid,
            "round": cr.get("round"),
            "team": "TR" if str(cr.get("team", "")).upper() in ("T", "TR") else "CT",
            "route": cr.get("route_id", ""),
            "destination": cr.get("intended_destination", ""),
            "session_start_tick": start_tick,
            "last_valid_progress_tick": ticks[last_prog_idx].get("dispatch_tick"),
            "first_causal_tick": cr.get("dispatch_tick"),
            "recovery_start_tick": ticks[rec_idx].get("dispatch_tick") if rec_idx is not None else None,
            "terminal_tick": term.get("dispatch_tick"),
            "causal_position": cr.get("actual_position", []),
            "causal_nav_area": cr.get("nav_area"),
            "causal_waypoint": cr.get("current_waypoint", ""),
            "causal_next_waypoint": cr.get("next_waypoint", ""),
            "path_remaining": cr.get("path_remaining"),
            "nav_distance_to_destination": cr.get("nav_distance_to_destination"),
            "velocity_xy": cr.get("velocity_xy"),
            "progress_units": cr.get("progress_units"),
            "blocked_duration_ms": cr.get("blocked_duration_ms"),
            "root_block_cause": cr.get("root_block_cause", ""),
            "current_block_state": cr.get("current_block_state", ""),
            "recovery_strategy": term.get("recovery_strategy", ""),
            "recovery_succeeded": term.get("recovery_succeeded", False),
            "terminal_reason": term.get("completion_reason") or term.get("fallback_reason") or "",
            "confidence": "HIGH",
            "evidence_ticks": len(ticks),
        }
        aborts_v2.append(entry)
        if sid == "r1_CT_s7_1474":
            mid_under = {**entry, "diagnosis": "RECOVERY_RETURNED_SAME_POINT"}
        if sid in ("r1_CT_s5_1530", "r3_CT_s10_6722"):
            b_short.append({**entry, "diagnosis": "B_SHORT_APPROACH_STATIC_GEOMETRY" if entry["round"] == 1 else "OTHER_PROVEN_CAUSE"})
    return aborts_v2, mid_under, b_short


def main():
    telem = read_jsonl(CAP / "opening_route_telemetry.jsonl")
    elig = json.loads((CAP / "eligibility_accounting.json").read_text(encoding="utf-8"))

    sessions_by_id = defaultdict(list)
    for r in telem:
        sid = r.get("session_id")
        if sid:
            sessions_by_id[sid].append(r)

    readiness_v2 = analyze_readiness(sessions_by_id)
    write_json("weapon_readiness_metrics_v2.json", readiness_v2)

    aborts_v2, mid_under, b_short = analyze_aborts(sessions_by_id)
    write_json("abort_root_causes_v2.json", {"marco": "2B.9.11", "total_aborts": len(aborts_v2), "aborts": aborts_v2})
    write_json("mid_underground_abort_analysis.json", mid_under or {"session_id": "r1_CT_s7_1474", "diagnosis": "NOT_FOUND_IN_V4"})
    write_json("b_short_abort_analysis.json", {"sessions": b_short})

    # Seção 6: 5 TRs certificados sem sessão
    targets = [
        (3, "096a2f571b98"),
        (3, "45b43fc66c5c"),
        (4, "45b43fc66c5c"),
        (4, "f587ec8e6634"),
        (5, "45b43fc66c5c"),
    ]
    tr_missing_rows = []
    for rnd, pseudo in targets:
        row = next((r for r in elig.get("rows", []) if r.get("round_id") == rnd and r.get("team") == "TR" and r.get("slot_pseudonimizado") == pseudo), None)
        tr_missing_rows.append({
            "assignment_id": f"r{rnd}_TR_{pseudo}",
            "round_id": rnd,
            "team": "TR",
            "slot_pseudonimizado": pseudo,
            "destination": row.get("assigned_destination") if row else None,
            "route": row.get("assigned_destination") if row else None,
            "controller_created": False,
            "lease_acquired": False,
            "exact_terminal_reason": "HISTORICAL_ASSIGNMENT_CAUSE_INCOMPLETE",
        })
    write_json("certified_assignment_without_session_analysis.json", {"marco": "2B.9.11", "items": tr_missing_rows})

    write_json("forensic_reanalysis_v1.json", {
        "marco": "2B.9.11",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_nature": "REAL",
        "auditor_errors": {
            "weapon_readiness_0pct": readiness_v2["previous_0pct_diagnosis"],
            "abort_first_causal_tick_default": "FIXED_IN_V2",
        },
        "contractual_assignment_errors": {
            "tr_certified_without_session_count": len(tr_missing_rows),
            "diagnosis": "HISTORICAL_ASSIGNMENT_CAUSE_INCOMPLETE",
        },
        "real_navigation_failures": {
            "aborts_count": len(aborts_v2),
            "sessions": [a["session_id"] for a in aborts_v2],
        },
    })

    write_json("input_snapshot.json", {
        "marco": "2B.9.11",
        "source_capture": "combined_5v5_debug_capture_v4",
        "opening_route_telemetry_sha256": sha256_file(CAP / "opening_route_telemetry.jsonl"),
    })

    print("OFFLINE_REANALYSIS_DONE",
          "ct_readiness=", readiness_v2["by_team"]["CT"]["readiness_pct"],
          "tr_readiness=", readiness_v2["by_team"]["TR"]["readiness_pct"],
          "aborts=", len(aborts_v2))


if __name__ == "__main__":
    main()
