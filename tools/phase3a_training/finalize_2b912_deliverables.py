import hashlib
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v4"
OUT = CAP / "forensic_contract_fix_v1"
OUT.mkdir(parents=True, exist_ok=True)
SERVER_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")
SERVER_LIFE = SERVER_LOGS / "opening_assignment_lifecycle.jsonl"
SERVER_CANARY = SERVER_LOGS / "opening_canary_telemetry.jsonl"
DLL_PATH = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\CsBotManager.dll")


def main():
    lines = [json.loads(l) for l in SERVER_LIFE.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if SERVER_LIFE.exists() else []
    run_starts = [r for r in lines if r.get("EventType") == "RUN_STARTED" and r.get("RunId")]
    if not run_starts:
        print("FINALIZE_2B912_VERDICT=RUN_IDENTITY_NOT_PROVEN")
        return

    expected_run_id = run_starts[-1]["RunId"]
    dll_sha = hashlib.sha256(DLL_PATH.read_bytes()).hexdigest() if DLL_PATH.exists() else ""

    filtered = []
    legacy_excluded = 0
    foreign_excluded = 0
    for r in lines:
        rid = r.get("RunId")
        if not rid:
            legacy_excluded += 1
        elif rid != expected_run_id:
            foreign_excluded += 1
        else:
            filtered.append(r)

    dst = OUT / "short_assignment_telemetry.jsonl"
    dst.write_text("\n".join(json.dumps(r) for r in filtered) + ("\n" if filtered else ""), encoding="utf-8")

    by_assign = defaultdict(list)
    for r in filtered:
        aid = r.get("AssignmentId")
        if aid:
            by_assign[aid].append(r)

    scheduled = sum(1 for r in filtered if r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED")
    state_changed = sum(1 for r in filtered if r.get("EventType") == "OPENING_ASSIGNMENT_STATE_CHANGED")
    terminal = sum(1 for r in filtered if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL")
    invalid_term = sum(1 for r in filtered if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL" and r.get("TerminalReason") == "SESSION_STARTED")

    controlled_assigns = 0
    controlled_terminals = 0
    utility_assigns = 0
    utility_terminals = 0
    without_terminal = 0
    dup_terminals = 0
    term_without_sched = 0

    for aid, recs in by_assign.items():
        has_sched = any(r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED" for r in recs)
        terms = [r for r in recs if r.get("EventType") == "OPENING_ASSIGNMENT_TERMINAL"]
        is_ctrl = any(r.get("EventType") == "OPENING_ASSIGNMENT_STATE_CHANGED" and r.get("TerminalReason") == "SESSION_STARTED" for r in recs)
        is_util = any(r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED" and not r.get("RouteCertified") for r in recs)
        if is_ctrl:
            controlled_assigns += 1
            if len(terms) == 1:
                controlled_terminals += 1
        elif is_util:
            utility_assigns += 1
            if len(terms) == 1:
                utility_terminals += 1
        if len(terms) == 0:
            without_terminal += 1
        elif len(terms) > 1:
            dup_terminals += len(terms) - 1
        if terms and not has_sched:
            term_without_sched += 1

    crecs = [json.loads(l) for l in SERVER_CANARY.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if SERVER_CANARY.exists() else []
    csess = defaultdict(list)
    for r in crecs:
        if r.get("session_id"):
            csess[r["session_id"]].append(r)
    open_sessions = sum(1 for srecs in csess.values() if not any(x.get("event_type") in ("COMPLETED", "INTERRUPTED", "ABORTED") for x in srecs))

    passed = (
        scheduled == 10
        and terminal == 10
        and controlled_assigns == controlled_terminals
        and utility_assigns == utility_terminals
        and without_terminal == 0
        and dup_terminals == 0
        and term_without_sched == 0
        and invalid_term == 0
        and open_sessions == 0
    )
    verdict = "DEBUG_TELEMETRY_LIFECYCLE_FULLY_SEALED" if passed else "ASSIGNMENT_TERMINAL_FLUSH_TIMEOUT"

    acct = {
        "run_id": expected_run_id,
        "source_dll_sha256": dll_sha,
        "verdict": verdict,
        "scheduled": scheduled,
        "state_changed": state_changed,
        "terminal": terminal,
        "controlled_assignments": controlled_assigns,
        "controlled_session_terminals": controlled_terminals,
        "utility_observed_assignments": utility_assigns,
        "utility_observed_terminals": utility_terminals,
        "assignments_without_terminal": without_terminal,
        "duplicate_terminals": dup_terminals,
        "terminal_without_scheduled": term_without_sched,
        "malformed_current_run": invalid_term,
        "open_sessions": open_sessions,
        "legacy_records_excluded": legacy_excluded,
        "foreign_run_records_excluded": foreign_excluded,
        "mixed_source_log_filtered": (legacy_excluded > 0 or foreign_excluded > 0),
    }
    (OUT / "assignment_lifecycle_accounting_v3.json").write_text(json.dumps(acct, indent=2) + "\n", encoding="utf-8")
    print(f"FINALIZE_2B912_VERDICT={verdict} run_id={expected_run_id} scheduled={scheduled} state_changed={state_changed} terminal={terminal} ctrl={controlled_terminals}/{controlled_assigns} util={utility_terminals}/{utility_assigns} without_term={without_terminal} dup={dup_terminals} open_sess={open_sessions}")


if __name__ == "__main__":
    main()
