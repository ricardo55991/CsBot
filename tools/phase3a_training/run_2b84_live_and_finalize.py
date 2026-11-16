import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
SERVER_DIR = Path(r"H:\CS2_AI_Server")
CS2_EXE = SERVER_DIR / "game" / "bin" / "win64" / "cs2.exe"
PLUGINS_DIR = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins"
PLUGIN_LOGS = PLUGINS_DIR / "CsBotManager" / "logs"
DEBUG_LOGS = SERVER_DIR / "debug_logs"

CANARY_BASE = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1"
PATCH_DIR = CANARY_BASE / "geometric_transition_patch_v1"
PREV_2B83_DIR = CANARY_BASE / "movement_authority_isolation_v1"

CANARY_JSONL = PLUGIN_LOGS / "opening_canary_telemetry.jsonl"
TRANS_EVENTS_JSON = PLUGIN_LOGS / "opening_canary_transition_events.json"
AUTH_TICKS_JSONL = PLUGIN_LOGS / "canary_authority_ticks.jsonl"
AUTH_ACC_JSON = PLUGIN_LOGS / "canary_authority_accounting.json"
COMP_WRITERS_JSON = PLUGIN_LOGS / "competing_writer_attempts.json"
ROUTES_SNAP_JSON = PLUGIN_LOGS / "opening_routes_snapshot.json"
NO_ELIGIBLE_JSON = PLUGIN_LOGS / "opening_canary_no_eligible.json"

ALL_16_DELIVERABLES = [
    "input_snapshot.json",
    "approved_route_regression_snapshot.json",
    "geometric_transition_audit.json",
    "transition_waypoint_contract_v1.json",
    "window_vents_transition.json",
    "market_b_transition.json",
    "b_site_bench_forest_transition.json",
    "geometric_harness_metrics.json",
    "targeted_test_result.json",
    "ct_canary_telemetry.jsonl",
    "ct_canary_metrics.json",
    "transition_runtime_metrics.json",
    "comparison_with_previous.json",
    "findings.json",
    "deliverable_evidence.json",
    "geometric_transition_patch_final_report.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def kill_existing_cs2() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], capture_output=True)
    time.sleep(2)


def restore_external_plugins() -> None:
    for name in ["BotState", "BotRandomizer"]:
        disabled = PLUGINS_DIR / f"{name}.disabled"
        active = PLUGINS_DIR / name
        if disabled.exists() and not active.exists():
            disabled.rename(active)


def clear_plugin_logs() -> None:
    PLUGIN_LOGS.mkdir(parents=True, exist_ok=True)
    for p in [
        CANARY_JSONL,
        TRANS_EVENTS_JSON,
        AUTH_TICKS_JSONL,
        AUTH_ACC_JSON,
        COMP_WRITERS_JSON,
        ROUTES_SNAP_JSON,
        NO_ELIGIBLE_JSON,
    ]:
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass


def set_flags(enabled: bool = True, isolation_mode: str = "LEASE_ISOLATED", fast_rounds: bool = True) -> None:
    DEBUG_LOGS.mkdir(parents=True, exist_ok=True)
    (DEBUG_LOGS / "canary_enabled.flag").write_text("true" if enabled else "false", encoding="utf-8")
    (DEBUG_LOGS / "canary_isolation_mode.flag").write_text(isolation_mode, encoding="utf-8")
    fast_flag = DEBUG_LOGS / "canary_fast_rounds.flag"
    if fast_rounds:
        fast_flag.write_text("1", encoding="utf-8")
    elif fast_flag.exists():
        fast_flag.unlink()


def classify_bucket(dest: str) -> str:
    d = (dest or "").lower()
    if d.startswith("a_") or d.startswith("ct_a_"):
        return "A"
    if any(k in d for k in ("bench", "van", "edward", "default_plant")):
        return "B_BENCH_VAN"
    if (d.startswith("b_") or d.startswith("ct_b_")) and "short_arch_hold_mid" not in d:
        return "B_MARKET"
    return "MID_WINDOW"


def read_live_canary_progress(path: Path) -> tuple[set[int], dict[int, str], Counter]:
    if not path.exists():
        return set(), {}, Counter()
    finished_rounds: set[int] = set()
    status_by_round: dict[int, str] = {}
    dest_by_round: dict[int, str] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            r = int(rec.get("round", 0))
            if r <= 0:
                continue
            dest = str(rec.get("intended_destination", ""))
            if dest:
                dest_by_round[r] = dest
            st = str(rec.get("arrival_status", "PENDING"))
            status_by_round[r] = st
            if rec.get("authority_return_tick") is not None or st != "PENDING":
                finished_rounds.add(r)

    bucket_counts: Counter = Counter()
    for r in finished_rounds:
        st = status_by_round.get(r, "")
        if not st.startswith("INTERRUPTED_"):
            bucket_counts[classify_bucket(dest_by_round.get(r, ""))] += 1
    return finished_rounds, status_by_round, bucket_counts


def run_live_canary10(max_rounds: int = 20, max_wait_s: int = 720) -> dict:
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    restore_external_plugins()
    kill_existing_cs2()
    clear_plugin_logs()
    set_flags(enabled=True, isolation_mode="LEASE_ISOLATED", fast_rounds=True)

    console_log = DEBUG_LOGS / "2b84_ct_canary10_console.log"
    if console_log.exists():
        try:
            console_log.unlink()
        except Exception:
            pass

    cmd = [
        str(CS2_EXE),
        "-dedicated",
        "-insecure",
        "+sv_lan", "1",
        "-port", "27016",
        "+game_type", "0",
        "+game_mode", "1",
        "+map", "de_mirage",
        "+bot_quota", "10",
        "+bot_quota_mode", "fill",
        "+exec", "ai_competitive.cfg",
        "+mp_warmuptime", "4",
        "+mp_freezetime", "12",
        "+mp_roundtime", "0.45",
        "+mp_roundtime_defuse", "0.45",
        "+mp_round_restart_delay", "2",
    ]
    env = os.environ.copy()
    env["CSBOT_OPENING_CANARY_MODE"] = "CT"

    t0 = time.time()
    try:
        with open(console_log, "w", encoding="utf-8", errors="replace") as log_f:
            proc = subprocess.Popen(
                cmd,
                cwd=str(SERVER_DIR),
                env=env,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            last_report = 0.0
            while True:
                elapsed = time.time() - t0
                if proc.poll() is not None:
                    print(f"[2B.8.4 canary] CS2 exited rc={proc.returncode} elapsed={elapsed:.1f}s", flush=True)
                    break

                finished, status_by_round, buckets = read_live_canary_progress(CANARY_JSONL)
                non_int = sum(1 for r in finished if not status_by_round.get(r, "").startswith("INTERRUPTED_"))
                all_buckets_hit = (
                    buckets["A"] >= 2
                    and buckets["MID_WINDOW"] >= 2
                    and buckets["B_MARKET"] >= 2
                    and buckets["B_BENCH_VAN"] >= 2
                )

                if elapsed - last_report >= 15.0:
                    print(
                        f"[2B.8.4 canary] elapsed={elapsed:.0f}s rounds_done={len(finished)} "
                        f"non_int={non_int} buckets={dict(buckets)} statuses={status_by_round}",
                        flush=True,
                    )
                    last_report = elapsed

                if (len(finished) >= 10 and non_int >= 8 and all_buckets_hit) or len(finished) >= max_rounds:
                    time.sleep(4.0)
                    print(
                        f"[2B.8.4 canary] Stopping cleanly: rounds_done={len(finished)} "
                        f"non_int={non_int} buckets={dict(buckets)} elapsed={elapsed:.1f}s",
                        flush=True,
                    )
                    break

                if elapsed >= max_wait_s:
                    print(f"[2B.8.4 canary] Timeout max_wait_s={max_wait_s} reached.", flush=True)
                    break

                time.sleep(2.0)
    finally:
        kill_existing_cs2()
        set_flags(enabled=True, isolation_mode="LEASE_ISOLATED", fast_rounds=False)

    copy_map = {
        CANARY_JSONL: PATCH_DIR / "ct_canary_telemetry.jsonl",
        TRANS_EVENTS_JSON: PATCH_DIR / "live_transition_events.json",
        AUTH_TICKS_JSONL: PATCH_DIR / "live_authority_ticks.jsonl",
        AUTH_ACC_JSON: PATCH_DIR / "live_authority_accounting.json",
        COMP_WRITERS_JSON: PATCH_DIR / "live_competing_writers.json",
        ROUTES_SNAP_JSON: PATCH_DIR / "ct_opening_routes_snapshot.json",
        NO_ELIGIBLE_JSON: PATCH_DIR / "live_no_eligible.json",
    }
    for src, dst in copy_map.items():
        if src.exists():
            shutil.copy2(src, dst)

    finished, status_by_round, buckets = read_live_canary_progress(PATCH_DIR / "ct_canary_telemetry.jsonl")
    return {
        "elapsed_s": round(time.time() - t0, 2),
        "rounds_done": len(finished),
        "buckets": dict(buckets),
        "status_by_round": {str(k): v for k, v in sorted(status_by_round.items())},
    }


def parse_targeted_trx() -> dict:
    trx_dir = PATCH_DIR / "_trx"
    trx_files = sorted(trx_dir.glob("*.trx")) if trx_dir.exists() else []
    if not trx_files:
        return {"passed": 0, "failed": 0, "skipped": 0, "total": 0, "all_passed": False, "source": "MISSING"}
    latest = trx_files[-1]
    tree = ET.parse(latest)
    root = tree.getroot()
    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
    counters = root.find(".//t:Counters", ns)
    total = int(counters.attrib.get("total", 0)) if counters is not None else 0
    passed = int(counters.attrib.get("passed", 0)) if counters is not None else 0
    failed = int(counters.attrib.get("failed", 0)) if counters is not None else 0
    not_exec = int(counters.attrib.get("notExecuted", 0)) if counters is not None else 0

    tests_list = []
    for res in root.findall(".//t:UnitTestResult", ns):
        tests_list.append({
            "test_name": res.attrib.get("testName", ""),
            "outcome": res.attrib.get("outcome", ""),
            "duration": res.attrib.get("duration", ""),
        })

    payload = {
        "marco": "2B.8.4",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "trx_path": str(latest.relative_to(BASE_DIR)).replace("\\", "/"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": not_exec,
        "all_passed": (total >= 20 and failed == 0 and passed == total),
        "geometric_transition_tests_passed": sum(
            1 for t in tests_list if t["outcome"] == "Passed"
        ),
        "sample_tests": tests_list,
    }
    (PATCH_DIR / "targeted_test_result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def finalize_metrics_and_report() -> dict:
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    test_summary = parse_targeted_trx()

    harness_path = PATCH_DIR / "geometric_harness_metrics.json"
    harness = json.loads(harness_path.read_text(encoding="utf-8")) if harness_path.exists() else {}

    telem_path = PATCH_DIR / "ct_canary_telemetry.jsonl"
    by_round: dict[int, list[dict]] = defaultdict(list)
    if telem_path.exists():
        with open(telem_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                r = int(rec.get("round", 0))
                if r > 0:
                    by_round[r].append(rec)

    sessions = []
    for r in sorted(by_round):
        ticks = by_round[r]
        last = ticks[-1]
        dest = str(last.get("intended_destination", ""))
        bucket = classify_bucket(dest)
        status = str(last.get("arrival_status", "PENDING"))
        reason = str(last.get("fallback_reason", ""))
        exp = float(last.get("expected_distance", 0.0) or 0.0)
        trav = float(last.get("traveled_distance", 0.0) or 0.0)
        detour = round(trav / exp, 4) if exp > 0 else 1.0
        unauth = any(bool(t.get("unauthorized_overwrite", False)) for t in ticks)
        cont_jump = max(int(t.get("continuous_jump_ticks", 0) or 0) for t in ticks)
        jump_pulses = max(int(t.get("jump_pulses_issued", 0) or 0) for t in ticks)
        cmd_count = max(int(t.get("transition_command_count", 0) or 0) for t in ticks)
        weapon_ready = bool(last.get("weapon_ready_before_contact", False))
        interrupted = status.startswith("INTERRUPTED_") or reason in (
            "CONTACT_INTERRUPTION", "DAMAGE_INTERRUPTION", "HOSTILE_UTILITY", "PLAYER_DEATH", "OPENING_PHASE_ENDED"
        )
        sessions.append({
            "round": r,
            "route_id": last.get("route_id", ""),
            "intended_destination": dest,
            "bucket": bucket,
            "arrival_status": status,
            "fallback_reason": reason,
            "executor_state": last.get("executor_state", ""),
            "interrupted_by_combat_or_phase": interrupted,
            "arrived": last.get("executor_state") == "DESTINATION_REACHED",
            "on_time": status == "ON_TIME",
            "timeout": reason == "TIMEOUT",
            "detour_ratio": detour,
            "traveled_distance": trav,
            "expected_distance": exp,
            "elapsed_seconds": last.get("elapsed_seconds", 0.0),
            "effective_deadline_seconds": last.get("effective_deadline_seconds", 0.0),
            "weapon_ready_before_contact": weapon_ready,
            "unauthorized_overwrite": unauth,
            "jump_pulses_issued": jump_pulses,
            "continuous_jump_ticks": cont_jump,
            "transition_command_count": cmd_count,
            "ticks": len(ticks),
        })

    non_int = [s for s in sessions if not s["interrupted_by_combat_or_phase"]]
    denom = len(non_int)
    arrived_n = sum(1 for s in non_int if s["arrived"])
    on_time_n = sum(1 for s in non_int if s["on_time"])
    timeout_n = sum(1 for s in non_int if s["timeout"])
    weapon_n = sum(1 for s in non_int if s["weapon_ready_before_contact"])
    unauth_n = sum(1 for s in sessions if s["unauthorized_overwrite"])
    cont_jump_n = sum(s["continuous_jump_ticks"] for s in sessions)

    routes_snap_path = PATCH_DIR / "ct_opening_routes_snapshot.json"
    acc_residue = None
    if routes_snap_path.exists():
        rs = json.loads(routes_snap_path.read_text(encoding="utf-8"))
        acc_residue = int(rs.get("accounting_residue", 0))

    mean_detour = round(sum(s["detour_ratio"] for s in non_int) / denom, 4) if denom > 0 else None

    bucket_summary = {}
    for b in ["A", "MID_WINDOW", "B_MARKET", "B_BENCH_VAN"]:
        bs = [s for s in non_int if s["bucket"] == b]
        bd = len(bs)
        ba = sum(1 for s in bs if s["arrived"])
        bo = sum(1 for s in bs if s["on_time"])
        bucket_summary[b] = {
            "non_interrupted": bd,
            "arrived": ba,
            "on_time": bo,
            "arrival_rate_formula": f"{ba}/{bd}" if bd > 0 else "N/A",
            "on_time_rate_formula": f"{bo}/{bd}" if bd > 0 else "N/A",
            "arrival_rate": round(ba / bd, 4) if bd > 0 else None,
            "on_time_rate": round(bo / bd, 4) if bd > 0 else None,
        }

    arrival_rate = round(arrived_n / denom, 4) if denom > 0 else 0.0
    on_time_rate = round(on_time_n / denom, 4) if denom > 0 else 0.0
    weapon_rate = round(weapon_n / denom, 4) if denom > 0 else 0.0

    ct_metrics = {
        "marco": "2B.8.4",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_sessions": len(sessions),
        "non_interrupted_sessions": denom,
        "arrivals": arrived_n,
        "arrival_formula": f"{arrived_n}/{denom}",
        "arrival_rate": arrival_rate,
        "on_time": on_time_n,
        "on_time_formula": f"{on_time_n}/{denom}",
        "on_time_rate": on_time_rate,
        "timeouts": timeout_n,
        "authority_violations": unauth_n,
        "mean_detour_ratio": mean_detour,
        "weapon_ready_before_contact": weapon_n,
        "weapon_ready_formula": f"{weapon_n}/{denom}",
        "weapon_ready_rate": weapon_rate,
        "continuous_in_jump_ticks": cont_jump_n,
        "accounting_residue": acc_residue,
        "bucket_coverage": bucket_summary,
        "sessions": sessions,
    }
    (PATCH_DIR / "ct_canary_metrics.json").write_text(json.dumps(ct_metrics, indent=2), encoding="utf-8")

    # transition_runtime_metrics.json
    live_events_path = PATCH_DIR / "live_transition_events.json"
    live_events = json.loads(live_events_path.read_text(encoding="utf-8")) if live_events_path.exists() else []
    events_by_type = Counter(e.get("event_type", "") for e in live_events)
    trans_runtime = {
        "marco": "2B.8.4",
        "data_nature": "REAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_transition_events": len(live_events),
        "events_by_type": dict(events_by_type),
        "jump_pulses_total": sum(s["jump_pulses_issued"] for s in sessions),
        "continuous_jump_violations": cont_jump_n,
        "by_bucket": bucket_summary,
    }
    (PATCH_DIR / "transition_runtime_metrics.json").write_text(json.dumps(trans_runtime, indent=2), encoding="utf-8")

    # comparison_with_previous.json
    prev_canary_path = PREV_2B83_DIR / "ct_canary_metrics.json"
    prev_canary = json.loads(prev_canary_path.read_text(encoding="utf-8")) if prev_canary_path.exists() else {}
    comparison = {
        "marco": "2B.8.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "previous_2b83_canary10": prev_canary.get("summary", prev_canary),
        "current_2b84_canary": {
            "arrival_formula": ct_metrics["arrival_formula"],
            "arrival_rate": arrival_rate,
            "on_time_formula": ct_metrics["on_time_formula"],
            "on_time_rate": on_time_rate,
            "timeouts": timeout_n,
            "authority_violations": unauth_n,
            "mean_detour_ratio": mean_detour,
            "continuous_in_jump_ticks": cont_jump_n,
            "weapon_ready_rate": weapon_rate,
        },
        "harness_simulated_summary": harness,
    }
    (PATCH_DIR / "comparison_with_previous.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")

    # Evaluate formal gates (Section 13)
    tests_ok = bool(test_summary.get("all_passed", False))
    harness_ok = bool(harness.get("gates_passed", False))
    coverage_ok = (
        bucket_summary["A"]["non_interrupted"] >= 2
        and bucket_summary["MID_WINDOW"]["non_interrupted"] >= 2
        and bucket_summary["B_MARKET"]["non_interrupted"] >= 2
        and bucket_summary["B_BENCH_VAN"]["non_interrupted"] >= 2
    )
    a_protected_ok = bucket_summary["A"]["non_interrupted"] >= 2 and bucket_summary["A"]["on_time"] == bucket_summary["A"]["non_interrupted"]
    live_ok = (
        denom >= 8
        and arrival_rate >= 0.80
        and on_time_rate >= 0.70
        and timeout_n == 0
        and unauth_n == 0
        and (mean_detour is not None and mean_detour <= 1.20)
        and weapon_rate >= 1.0
        and cont_jump_n == 0
        and acc_residue in (0, None)
    )

    if not tests_ok or not harness_ok:
        verdict = "GEOMETRIC_TRANSITION_PATCH_FAILED"
    elif live_ok and coverage_ok and a_protected_ok:
        verdict = "OPENING_ROUTE_CT_CANARY_APPROVED_FOR_TR_CANARY"
    else:
        verdict = "GEOMETRIC_TRANSITION_LIVE_CANARY_FAILED"

    findings = {
        "marco": "2B.8.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "gates": {
            "targeted_tests_passed": tests_ok,
            "harness_passed": harness_ok,
            "live_canary_passed": live_ok,
            "bucket_coverage_ok": coverage_ok,
            "approved_a_routes_preserved": a_protected_ok,
        },
        "live_failures": [
            f"{s['intended_destination']}:round={s['round']}:{s['arrival_status']}:{s['fallback_reason']}"
            for s in non_int if not s["on_time"]
        ],
    }
    (PATCH_DIR / "findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")

    # Write canonical markdown report
    md = [
        "# MARCO 2B.8.4 — Relatório Final do Patch Geométrico das Rotas CT",
        "",
        f"**Veredito Canônico:** `{verdict}`",
        "",
        "## 1. Resumo dos Testes Direcionados (Natureza: `REAL`)",
        f"- Testes executados: `{test_summary.get('passed', 0)}/{test_summary.get('total', 0)}` aprovados (`failed = {test_summary.get('failed', 0)}`).",
        f"- Evidência: `training_runs/positioning_v2_real_temporal/opening_route_canary_v1/geometric_transition_patch_v1/targeted_test_result.json`",
        "",
        "## 2. Geometric Harness Offline (Natureza: `SIMULATED`)",
        f"- Repetições completadas: `{harness.get('total_completed', 0)}/{harness.get('total_repetitions', 0)}` (`gates_passed = {harness.get('gates_passed', False)}`).",
        f"- Continuous jump total: `{harness.get('continuous_jump_total', 0)}` | Invalid path: `{harness.get('invalid_path_total', 0)}` | Authority violations: `{harness.get('authority_violation_total', 0)}`",
        "",
        "## 3. Canary CT ao Vivo em Servidor CS2 (Natureza: `REAL`)",
        f"- Sessões válidas não-interrompidas: `{denom}` (total sessões observadas: `{len(sessions)}`)",
        f"- Chegadas (`DESTINATION_REACHED`): `{arrived_n}/{denom}` (`{arrival_rate * 100:.2f}%`)",
        f"- No prazo (`ON_TIME`): `{on_time_n}/{denom}` (`{on_time_rate * 100:.2f}%`)",
        f"- Timeouts: `{timeout_n}` | Violações de autoridade: `{unauth_n}` | Resíduo contábil: `{acc_residue}`",
        f"- Mean detour ratio: `{mean_detour}` | Weapon ready before contact: `{weapon_n}/{denom}` (`{weapon_rate * 100:.2f}%`)",
        f"- Ticks de `IN_JUMP` contínuo: `{cont_jump_n}`",
        "",
        "### Cobertura por Corredor",
        "| Corredor | Não-Interrompidas | Chegadas (N/D) | ON_TIME (N/D) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for b in ["A", "MID_WINDOW", "B_MARKET", "B_BENCH_VAN"]:
        bs = bucket_summary[b]
        md.append(f"| `{b}` | {bs['non_interrupted']} | `{bs['arrival_rate_formula']}` | `{bs['on_time_rate_formula']}` |")

    md.extend([
        "",
        "### Sessões Registradas",
        "| Round | Corredor | Destino Original | Status | Motivo | Detour | Jump Pulses |",
        "| ---: | --- | --- | --- | --- | ---: | ---: |",
    ])
    for s in sessions:
        md.append(
            f"| {s['round']} | `{s['bucket']}` | `{s['intended_destination']}` | `{s['arrival_status']}` | "
            f"`{s['fallback_reason']}` | {s['detour_ratio']} | {s['jump_pulses_issued']} |"
        )

    report_path = PATCH_DIR / "geometric_transition_patch_final_report.md"
    report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    # Build deliverable_evidence.json AFTER writing all other 14 artifacts + report
    evidence_entries = []
    # Self-entry placeholder first, then recompute self after write if desired, or verify all 15 concrete siblings
    for name in ALL_16_DELIVERABLES:
        if name == "deliverable_evidence.json":
            continue
        p = PATCH_DIR / name
        rel = str(p.relative_to(BASE_DIR)).replace("\\", "/")
        exists = p.exists()
        size = p.stat().st_size if exists else 0
        evidence_entries.append({
            "file": name,
            "path": rel,
            "exists": exists,
            "size_bytes": size,
            "sha256": sha256_file(p) if exists and size > 0 else "",
        })

    ev_path = PATCH_DIR / "deliverable_evidence.json"
    ev_payload = {
        "marco": "2B.8.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "all_deliverables_verified": all(e["exists"] and e["size_bytes"] > 0 and len(e["sha256"]) == 64 for e in evidence_entries),
        "deliverables": evidence_entries,
    }
    ev_path.write_text(json.dumps(ev_payload, indent=2), encoding="utf-8")
    return {"verdict": verdict, "live": ct_metrics, "tests": test_summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()

    if args.live:
        res = run_live_canary10()
        print("LIVE_RUN_DONE:", json.dumps(res), flush=True)
    if args.finalize:
        res = finalize_metrics_and_report()
        print("FINALIZE_DONE:", json.dumps({
            "verdict": res["verdict"],
            "arrival": res["live"]["arrival_formula"],
            "on_time": res["live"]["on_time_formula"],
            "timeouts": res["live"]["timeouts"],
            "authority_violations": res["live"]["authority_violations"],
            "tests": f"{res['tests'].get('passed', 0)}/{res['tests'].get('total', 0)}",
        }), flush=True)


if __name__ == "__main__":
    main()
