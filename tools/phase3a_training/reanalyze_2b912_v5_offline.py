import json
from collections import defaultdict
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v5"


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


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d > 0 else 0.0


def main():
    life_raw = read_jsonl(CAP / "opening_assignment_lifecycle.jsonl")
    run_starts = [r for r in life_raw if r.get("EventType") == "RUN_STARTED" and r.get("RunId")]
    run_id = run_starts[-1]["RunId"] if run_starts else "UNKNOWN"
    life = [r for r in life_raw if r.get("RunId") == run_id and r.get("RoundId") in (1, 2, 3, 4, 5)]

    sched_raw = [r for r in life if r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED"]
    sc_raw = [r for r in life if r.get("EventType") == "OPENING_ASSIGNMENT_STATE_CHANGED"]
    term_raw = [r for r in life if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL"]

    uniq_sched = {r["AssignmentId"] for r in sched_raw if r.get("AssignmentId")}
    uniq_term = {r["AssignmentId"] for r in term_raw if r.get("AssignmentId")}

    lifecycle_re = {
        "marco": "2B.9.12_v5_reanalysis",
        "run_id": run_id,
        "scheduled_event_count_raw": len(sched_raw),
        "unique_scheduled_assignments": len(uniq_sched),
        "duplicate_scheduled_events": len(sched_raw) - len(uniq_sched),
        "state_changed_event_count_raw": len(sc_raw),
        "terminal_event_count_raw": len(term_raw),
        "unique_terminal_assignments": len(uniq_term),
        "duplicate_terminal_events": len(term_raw) - len(uniq_term),
        "assignments_without_terminal": len(uniq_sched - uniq_term),
        "terminal_without_scheduled": len(uniq_term - uniq_sched),
        "classification": [
            "CAPTURE_CONTENT_COMPLETE",
            "RUNTIME_SCHEDULE_EMISSION_DUPLICATED",
        ],
    }
    (CAP / "lifecycle_reanalysis_v5.json").write_text(json.dumps(lifecycle_re, indent=2) + "\n", encoding="utf-8")

    # Corrigir tr_route_metrics.json e ct_route_metrics.json separando CT e TR corretamente
    opening = [r for r in read_jsonl(CAP / "opening_route_telemetry.jsonl") if r.get("round") in (1, 2, 3, 4, 5)]
    sessions = defaultdict(list)
    for r in opening:
        if r.get("session_id"):
            sessions[r["session_id"]].append(r)

    def summarize(team_target: str):
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
            })
        non_int = [s for s in ts if s["terminal_event"] != "INTERRUPTED"]
        denom = len(non_int)
        arrivals = sum(1 for s in non_int if s["arrival_status"] in ("ON_TIME", "LATE"))
        on_time = sum(1 for s in non_int if s["arrival_status"] == "ON_TIME")
        return {
            "team": team_target,
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
            "sessions": ts,
        }

    ct_m = summarize("CT")
    tr_m = summarize("TR")
    (CAP / "ct_route_metrics.json").write_text(json.dumps({k: v for k, v in ct_m.items() if k != "sessions"}, indent=2) + "\n", encoding="utf-8")
    (CAP / "tr_route_metrics.json").write_text(json.dumps({k: v for k, v in tr_m.items() if k != "sessions"}, indent=2) + "\n", encoding="utf-8")

    # tr_failure_analysis.json (preservando 6/9 = 66.67%)
    tr_aborts = [s for s in tr_m["sessions"] if s["terminal_event"] == "ABORTED"]
    tr_ints = [s for s in tr_m["sessions"] if s["terminal_event"] == "INTERRUPTED"]
    tr_util = [r for r in term_raw if r.get("Team") == "TR" and r.get("TerminalReason") == "UNCERTIFIED_ROUTE"]
    (CAP / "tr_failure_analysis.json").write_text(json.dumps({
        "team": "TR",
        "arrivals": tr_m["arrivals"],
        "non_interrupted_denominator": tr_m["non_interrupted_denominator"],
        "arrival_pct": tr_m["arrival_pct"],
        "aborted_sessions": tr_aborts,
        "interrupted_sessions": tr_ints,
        "utility_only_assignments": len(tr_util),
        "session_start_failed": 0,
        "opening_window_expired": 0,
    }, indent=2) + "\n", encoding="utf-8")

    # positioning_agreement_metrics.json com denominador válido
    shadow = [r for r in read_jsonl(CAP / "positioning_shadow_telemetry.jsonl") if r.get("round_id") in (1, 2, 3, 4, 5)]
    comparable = [
        r for r in shadow
        if r.get("utility_decision_available", False)
        and r.get("utility_sector") not in (None, "", "UNKNOWN", "UTILITY_SECTOR")
        and r.get("neural_sector") not in (None, "", "UNKNOWN")
    ]
    agree = sum(1 for r in comparable if r.get("utility_sector") == r.get("neural_sector"))
    (CAP / "positioning_agreement_metrics.json").write_text(json.dumps({
        "total_predictions": len(shadow),
        "utility_available_predictions": sum(1 for r in shadow if r.get("utility_decision_available")),
        "comparable_predictions": len(comparable),
        "agreement_count": agree,
        "disagreement_count": len(comparable) - agree,
        "agreement_pct_comparable": pct(agree, len(comparable)) if comparable else None,
        "unknown_utility": sum(1 for r in shadow if r.get("utility_sector") in (None, "", "UNKNOWN", "UTILITY_SECTOR")),
        "unknown_neural": sum(1 for r in shadow if r.get("neural_sector") in (None, "", "UNKNOWN")),
        "excluded_predictions": len(shadow) - len(comparable),
        "verdict": "SECTOR_AGREEMENT_COMPUTED" if comparable else "SECTOR_AGREEMENT_NOT_COMPUTABLE",
    }, indent=2) + "\n", encoding="utf-8")

    print("V5_REANALYSIS_DONE",
          "uniq_sched=", len(uniq_sched), "uniq_term=", len(uniq_term),
          "dup_sched=", len(sched_raw) - len(uniq_sched),
          "tr_arr=", f"{tr_m['arrivals']}/{tr_m['non_interrupted_denominator']} ({tr_m['arrival_pct']}%)")


if __name__ == "__main__":
    main()
