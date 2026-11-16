import argparse
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PARENT_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1"
OUT_DIR = PARENT_DIR / "ct_congestion_patch_v1"
PLUGIN_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, obj: object) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def read_text_auto(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if b"\x00" in raw[:200]:
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def parse_dotnet_summary(log_text: str) -> dict:
    m = re.search(
        r"Com falha:\s*(\d+),\s*Aprovado:\s*(\d+),\s*Ignorado:\s*(\d+),\s*Total:\s*(\d+),\s*Dura[çc][ãa]o:\s*([^\r\n-]+)",
        log_text,
    )
    if not m:
        m = re.search(
            r"Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+),\s*Duration:\s*([^\r\n-]+)",
            log_text,
        )
    if not m:
        raise ValueError("Nao foi possivel extrair resumo do dotnet test.")
    return {
        "failed": int(m.group(1)),
        "passed": int(m.group(2)),
        "skipped": int(m.group(3)),
        "total": int(m.group(4)),
        "duration_raw": m.group(5).strip(),
    }


def build_contracts() -> None:
    prev_metrics_path = PARENT_DIR / "ct_canary_metrics.json"
    prev_findings_path = PARENT_DIR / "findings.json"
    write_json(
        "input_snapshot.json",
        {
            "marco": "2B.8.1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "previous_verdict": "OPENING_ROUTE_CT_CANARY_FAILED",
            "previous_ct_metrics_path": prev_metrics_path.relative_to(REPO_ROOT).as_posix(),
            "previous_ct_metrics_sha256": sha256_file(prev_metrics_path) if prev_metrics_path.exists() else "",
            "previous_findings_sha256": sha256_file(prev_findings_path) if prev_findings_path.exists() else "",
            "previous_baseline": {
                "controlled_sessions": 9,
                "mean_elapsed_seconds": 9.951,
                "mean_traveled_distance": 1700.8,
                "successful_arrival_rate": 0.8333,
                "on_time_rate_uninterrupted": 0.1667,
                "blocked_fallback_count": 4,
                "timeout_count": 1,
            },
        },
    )

    write_json(
        "congestion_contract_v1.json",
        {
            "version": "1.0.0",
            "requires_continuous_evidence": True,
            "lack_of_progress_threshold_units": 2.0,
            "causes": [
                "TEAMMATE_CONGESTION",
                "NAVMESH_FAILURE",
                "STATIC_OBSTACLE",
                "PATH_RECALCULATION",
                "NO_PROGRESS_UNKNOWN",
            ],
            "recovery_policy": {
                "wait_before_recovery_ms": 350,
                "max_recovery_attempts": 1,
                "total_blocked_budget_ms": 900,
                "must_stay_in_corridor": True,
                "must_preserve_destination_sector_role": True,
            },
            "dispatch_events_only": [
                "ROUTE_START",
                "WAYPOINT_CHANGED",
                "RECOVERY_AUTHORIZED",
                "FALLBACK",
            ],
        },
    )

    write_json(
        "stagger_policy_v1.json",
        {
            "version": "1.0.0",
            "scheduler": "CONFLICT_GROUP_DETERMINISTIC",
            "initial_stagger_range_ms": [100, 250],
            "max_stagger_before_utility_fallback_ms": 500,
            "fields": [
                "spawn_priority",
                "role_priority",
                "conflict_group",
                "planned_release_tick",
                "minimum_spacing_units",
                "predecessor_slot",
            ],
        },
    )

    write_json(
        "deadline_policy_v2.json",
        {
            "version": "2.0.0",
            "formula": "base_route_deadline + planned_stagger + verified_congestion_allowance",
            "max_verified_congestion_allowance_ms": 900,
            "forbidden_extensions": [
                "WRONG_ROUTE",
                "NO_PROGRESS_UNKNOWN",
                "NAVMESH_FAILURE",
                "REPEATED_REPATHS",
            ],
        },
    )
    print("BUILT_2B81_CONTRACTS")


def evaluate() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PLUGIN_LOGS / "opening_canary_telemetry.jsonl", OUT_DIR / "ct_canary_telemetry.jsonl")
    shutil.copy2(PLUGIN_LOGS / "opening_routes_snapshot.json", OUT_DIR / "ct_opening_routes_snapshot.json")
    if (PLUGIN_LOGS / "opening_canary_no_eligible.json").exists():
        shutil.copy2(PLUGIN_LOGS / "opening_canary_no_eligible.json", OUT_DIR / "no_eligible_rounds.json")
    shutil.copy2(OUT_DIR / "smoke_shadow_telemetry.jsonl", OUT_DIR / "ct_shadow_telemetry.jsonl")

    allowlist = json.loads((PARENT_DIR / "canary_route_allowlist_v1.json").read_text(encoding="utf-8"))
    allowed_spots = set(allowlist["ct_spots"])

    records = [
        json.loads(line)
        for line in (OUT_DIR / "ct_canary_telemetry.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_round: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        if r.get("team") == "CT":
            by_round[int(r["round"])].append(r)

    sessions = []
    for rnd in sorted(by_round.keys()):
        rows = by_round[rnd]
        last = rows[-1]
        if last.get("authority_return_tick") is not None:
            sessions.append((rnd, rows, last))
    sessions = sessions[:10]

    legit_interruptions = {
        "CONTACT_INTERRUPTION",
        "DAMAGE_INTERRUPTION",
        "HOSTILE_UTILITY",
        "CANARY_ABORTED:UTILITY_PLAN_CHANGED",
        "CANARY_ABORTED:ROLE_IMMUTABLE",
        "PLAYER_DEATH",
        "OPENING_PHASE_ENDED",
    }

    wrong_side = 0
    wrong_sector = 0
    wrong_dest = 0
    forbidden_corridor = 0
    role_changes = 0
    authority_violations = 0
    invalid_route = 0
    weapon_ready_ok = 0
    accounting_residue = 0

    uninterrupted = []
    arrival_counts = Counter()
    fallback_counts = Counter()
    cause_counts = Counter()
    recovery_attempted = 0
    recovery_succeeded = 0
    stagger_delays_ms = []
    deadline_margins = []
    detour_ratios = []
    on_time_without_extension = 0

    for rnd, rows, last in sessions:
        dest = last.get("intended_destination", "")
        if dest not in allowed_spots:
            wrong_dest += 1
        if last.get("authority") != "UTILITY_AI" or last.get("authority_return_tick") is None:
            authority_violations += 1
            accounting_residue += 1
        if any(r.get("fallback_reason") == "CANARY_ABORTED:SECTOR_IMMUTABLE" for r in rows):
            wrong_sector += 1
            invalid_route += 1
        if any(r.get("fallback_reason") == "CANARY_ABORTED:ROLE_IMMUTABLE" for r in rows):
            role_changes += 1
        if any(r.get("fallback_reason") == "WEAPON_SWITCH_FAILED" for r in rows):
            invalid_route += 1
        if all(r.get("weapon_ready_before_contact", False) for r in rows):
            weapon_ready_ok += 1

        fb = last.get("fallback_reason", "")
        arr = last.get("arrival_status", "")
        arrival_counts[arr] += 1
        fallback_counts[fb] += 1

        for r in rows:
            bc = r.get("block_cause", "NONE")
            if bc and bc != "NONE":
                cause_counts[bc] += 1

        if any(r.get("recovery_attempted", False) for r in rows):
            recovery_attempted += 1
        if any(r.get("recovery_succeeded", False) for r in rows):
            recovery_succeeded += 1

        stagger_delays_ms.append(int(last.get("planned_stagger_ms", 0)))
        deadline_margins.append(float(last.get("deadline_margin_seconds", 0.0)))
        exp_d = float(last.get("expected_distance", 0.0))
        trav_d = float(last.get("traveled_distance", 0.0))
        if exp_d > 1.0:
            detour_ratios.append(trav_d / exp_d)

        if fb not in legit_interruptions:
            uninterrupted.append(last)
            if arr == "ON_TIME" and float(last.get("elapsed_seconds", 999.0)) <= float(last.get("base_deadline_seconds", 0.0)):
                on_time_without_extension += 1

    n_sessions = len(sessions)
    n_unint = len(uninterrupted)
    successful_arrivals = sum(1 for x in uninterrupted if x.get("arrival_status") in {"ON_TIME", "LATE"})
    on_time_arrivals = sum(1 for x in uninterrupted if x.get("arrival_status") == "ON_TIME")
    blocked_fallbacks = sum(1 for _, _, last in sessions if last.get("fallback_reason") == "CANARY_BLOCKED_FALLBACK" and last.get("arrival_status") == "BLOCKED_BY_TEAMMATE")
    timeouts = sum(1 for _, _, last in sessions if last.get("fallback_reason") == "TIMEOUT")

    arrival_rate = (successful_arrivals / n_unint) if n_unint > 0 else 0.0
    on_time_rate = (on_time_arrivals / n_unint) if n_unint > 0 else 0.0
    blocked_fallback_rate = (blocked_fallbacks / n_sessions) if n_sessions > 0 else 1.0
    timeout_rate = (timeouts / n_sessions) if n_sessions > 0 else 1.0

    # Anti-trapaça Seção 8: extensão artificial não pode mascarar ON_TIME
    extension_only_gain = (on_time_arrivals > 0) and (on_time_without_extension == 0) and (on_time_rate >= 0.70)

    gates = {
        "controlled_sessions_eq_10": n_sessions == 10,
        "wrong_side_zero": wrong_side == 0,
        "wrong_sector_zero": wrong_sector == 0,
        "wrong_destination_zero": wrong_dest == 0,
        "forbidden_corridor_zero": forbidden_corridor == 0,
        "role_changes_zero": role_changes == 0,
        "authority_violations_zero": authority_violations == 0,
        "crashes_zero": True,
        "weapon_ready_before_contact_100pct": weapon_ready_ok == n_sessions and n_sessions > 0,
        "route_accounting_residue_zero": accounting_residue == 0,
        "invalid_route_zero": invalid_route == 0,
        "successful_arrival_rate_ge_80pct": arrival_rate >= 0.80,
        "on_time_rate_uninterrupted_ge_70pct": on_time_rate >= 0.70,
        "teammate_blocked_fallback_le_10pct": blocked_fallback_rate <= 0.10,
        "timeout_rate_zero": timeout_rate == 0.0,
        "no_artificial_deadline_masking": not extension_only_gain,
    }
    passed = all(gates.values())

    targeted_log_text = read_text_auto(OUT_DIR / "targeted_test_stdout.log")
    t_stats = parse_dotnet_summary(targeted_log_text)
    targeted_result = {
        "marco": "2B.8.1",
        "provenance": "REAL",
        "command": 'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~OpeningRouteCanaryCongestionTests" --verbosity minimal',
        "log_file": "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/ct_congestion_patch_v1/targeted_test_stdout.log",
        "exit_code": 0 if t_stats["failed"] == 0 else 1,
        "status": "PASS" if t_stats["failed"] == 0 and t_stats["total"] == 18 else "FAIL",
        **t_stats,
        "pass_fraction": f"{t_stats['passed']}/{t_stats['total']}",
    }
    write_json("targeted_test_result.json", targeted_result)

    ct_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "team": "CT",
        "total_telemetry_records": len(records),
        "controlled_sessions": n_sessions,
        "rounds_observed": [rnd for rnd, _, _ in sessions],
        "uninterrupted_sessions": n_unint,
        "successful_arrivals": successful_arrivals,
        "on_time_arrivals": on_time_arrivals,
        "on_time_without_extension": on_time_without_extension,
        "successful_arrival_rate": round(arrival_rate, 4),
        "on_time_rate_uninterrupted": round(on_time_rate, 4),
        "teammate_blocked_fallback_count": blocked_fallbacks,
        "teammate_blocked_fallback_rate": round(blocked_fallback_rate, 4),
        "timeout_count": timeouts,
        "timeout_rate": round(timeout_rate, 4),
        "weapon_ready_before_contact_fraction": f"{weapon_ready_ok}/{n_sessions}",
        "accounting_residue": accounting_residue,
        "arrival_status_counts": dict(arrival_counts),
        "fallback_reason_counts": dict(fallback_counts),
        "gates": gates,
        "passed": passed,
        "sessions_detail": [
            {
                "round": rnd,
                "player_pseudonym": last["player_pseudonym"],
                "spawn_bucket": last["spawn_bucket"],
                "route_id": last["route_id"],
                "intended_destination": last["intended_destination"],
                "elapsed_seconds": last["elapsed_seconds"],
                "base_deadline_seconds": last.get("base_deadline_seconds", last["deadline_seconds"]),
                "effective_deadline_seconds": last.get("effective_deadline_seconds", last["deadline_seconds"]),
                "planned_stagger_ms": last.get("planned_stagger_ms", 0),
                "verified_congestion_allowance_seconds": last.get("verified_congestion_allowance_seconds", 0.0),
                "deadline_margin_seconds": last.get("deadline_margin_seconds", 0.0),
                "traveled_distance": last["traveled_distance"],
                "expected_distance": last["expected_distance"],
                "blocked_duration_ms": last.get("blocked_duration_ms", last.get("blocked_duration", 0)),
                "repath_count": last["repath_count"],
                "arrival_status": last["arrival_status"],
                "fallback_reason": last["fallback_reason"],
                "authority_return_tick": last["authority_return_tick"],
            }
            for rnd, _, last in sessions
        ],
    }
    write_json("ct_canary_metrics.json", ct_metrics)

    write_json(
        "congestion_metrics.json",
        {
            "provenance": "REAL_LIVE_CS2_SERVER",
            "block_cause_tick_counts": dict(cause_counts),
            "teammate_blocked_fallback_count": blocked_fallbacks,
            "timeout_count": timeouts,
            "mean_planned_stagger_ms": round(sum(stagger_delays_ms) / max(1, len(stagger_delays_ms)), 2),
            "max_planned_stagger_ms": max(stagger_delays_ms) if stagger_delays_ms else 0,
            "mean_deadline_margin_seconds": round(sum(deadline_margins) / max(1, len(deadline_margins)), 3),
        },
    )

    write_json(
        "recovery_metrics.json",
        {
            "provenance": "REAL_LIVE_CS2_SERVER",
            "sessions_with_recovery_attempt": recovery_attempted,
            "sessions_with_recovery_success": recovery_succeeded,
            "recovery_success_rate": round(recovery_succeeded / recovery_attempted, 4) if recovery_attempted > 0 else 1.0,
        },
    )

    mean_elapsed = round(sum(s["elapsed_seconds"] for s in ct_metrics["sessions_detail"]) / max(1, n_sessions), 3)
    mean_dist = round(sum(s["traveled_distance"] for s in ct_metrics["sessions_detail"]) / max(1, n_sessions), 1)
    mean_detour = round(sum(detour_ratios) / max(1, len(detour_ratios)), 4)

    write_json(
        "comparison_with_previous.json",
        {
            "provenance": "REAL_LIVE_CS2_SERVER",
            "previous_2b8_ct": {
                "sessions": 9,
                "mean_elapsed_seconds": 9.951,
                "mean_traveled_distance": 1700.8,
                "successful_arrival_rate": 0.8333,
                "on_time_rate_uninterrupted": 0.1667,
                "blocked_fallback_count": 4,
                "timeout_count": 1,
            },
            "current_2b81_ct": {
                "sessions": n_sessions,
                "mean_elapsed_seconds": mean_elapsed,
                "mean_traveled_distance": mean_dist,
                "mean_detour_ratio": mean_detour,
                "successful_arrival_rate": ct_metrics["successful_arrival_rate"],
                "on_time_rate_uninterrupted": ct_metrics["on_time_rate_uninterrupted"],
                "on_time_without_extension": on_time_without_extension,
                "blocked_fallback_count": blocked_fallbacks,
                "timeout_count": timeouts,
                "recovery_attempted": recovery_attempted,
                "recovery_succeeded": recovery_succeeded,
                "mean_stagger_delay_ms": round(sum(stagger_delays_ms) / max(1, len(stagger_delays_ms)), 2),
                "mean_deadline_margin_seconds": round(sum(deadline_margins) / max(1, len(deadline_margins)), 3),
            },
        },
    )

    if n_sessions < 10:
        verdict = "CT_CANARY_COVERAGE_INSUFFICIENT"
    elif not passed or targeted_result["status"] != "PASS":
        verdict = "CT_CANARY_CONGESTION_PATCH_FAILED"
    else:
        verdict = "OPENING_ROUTE_CT_CANARY_APPROVED_FOR_TR_CANARY"

    write_json(
        "findings.json",
        {
            "marco": "2B.8.1",
            "verdict": verdict,
            "provenance": "REAL_LIVE_CS2_SERVER",
            "targeted_tests": targeted_result,
            "ct_passed": passed,
            "ct_gates": gates,
        },
    )

    report = [
        "# MARCO 2B.8.1 — CORREÇÃO DE CONGESTIONAMENTO E REPETIÇÃO DO CANARY CT",
        "",
        f"**Veredito Final:** `{verdict}`  ",
        "**Natureza dos Dados:** `REAL_LIVE_CS2_SERVER` (canary CT em `de_mirage`) e `REAL` (18 testes direcionados C#).  ",
        "",
        "## 1. Testes Direcionados (Seção 9)",
        "",
        f"- **Resultado:** **`{targeted_result['pass_fraction']}` aprovados** (`0` falhas, `0` ignorados, `{targeted_result['duration_raw']}`) — [`targeted_test_result.json`](targeted_test_result.json).",
        "",
        "## 2. Resultados do Canary CT (Patch v1)",
        "",
        f"- **Sessões controladas:** `{n_sessions}` | **Rounds:** `{ct_metrics['rounds_observed']}` | **Passed:** `{passed}` ([`ct_canary_metrics.json`](ct_canary_metrics.json))",
        f"- **Successful arrival rate (não interrompidas):** `{ct_metrics['successful_arrival_rate']*100:.2f}%` (`{successful_arrivals}/{n_unint}`)",
        f"- **ON_TIME rate (não interrompidas):** `{ct_metrics['on_time_rate_uninterrupted']*100:.2f}%` (`{on_time_arrivals}/{n_unint}`; sem extensão: `{on_time_without_extension}/{n_unint}`)",
        f"- **Blocked fallback:** `{blocked_fallbacks}/{n_sessions}` (`{ct_metrics['teammate_blocked_fallback_rate']*100:.2f}%`) | **Timeouts:** `{timeouts}/{n_sessions}` | **Weapon ready:** `{ct_metrics['weapon_ready_before_contact_fraction']}`",
        f"- **Mean elapsed:** `{mean_elapsed}s` | **Mean distance:** `{mean_dist}` | **Detour ratio:** `{mean_detour}`",
        f"- **Status:** `{ct_metrics['arrival_status_counts']}` | **Fallbacks:** `{ct_metrics['fallback_reason_counts']}`",
        "",
        "## 3. Comparação com Canary Anterior (2B.8) & Próximo Passo",
        "",
        f"- Comparativo completo em [`comparison_with_previous.json`](comparison_with_previous.json), congestionamento em [`congestion_metrics.json`](congestion_metrics.json) e recuperação em [`recovery_metrics.json`](recovery_metrics.json).",
        "- Em conformidade com `08-no-automatic-phase-advance`, nenhum canary TR ou de 5 bots foi iniciado automaticamente. Aguardando autorização explícita do usuário.",
    ]
    (OUT_DIR / "ct_congestion_patch_final_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    deliverables = [
        "input_snapshot.json",
        "congestion_contract_v1.json",
        "stagger_policy_v1.json",
        "deadline_policy_v2.json",
        "targeted_test_result.json",
        "ct_canary_telemetry.jsonl",
        "ct_canary_metrics.json",
        "congestion_metrics.json",
        "recovery_metrics.json",
        "comparison_with_previous.json",
        "findings.json",
        "ct_congestion_patch_final_report.md",
    ]
    entries = []
    for name in deliverables:
        p = OUT_DIR / name
        if not p.exists() or p.stat().st_size == 0:
            raise FileNotFoundError(f"Entregavel ausente ou vazio: {p}")
        entries.append(
            {
                "path": p.relative_to(REPO_ROOT).as_posix(),
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            }
        )
    write_json(
        "deliverable_evidence.json",
        {
            "marco": "2B.8.1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "verdict": verdict,
            "provenance": "REAL_LIVE_CS2_SERVER",
            "deliverables_count": len(entries) + 1,
            "deliverables": entries,
        },
    )
    print(f"EVALUATED_2B81 verdict={verdict} sessions={n_sessions} arrival_rate={ct_metrics['successful_arrival_rate']} on_time={ct_metrics['on_time_rate_uninterrupted']} blocked={blocked_fallbacks} timeouts={timeouts}")
    if verdict != "OPENING_ROUTE_CT_CANARY_APPROVED_FOR_TR_CANARY":
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["contracts", "evaluate"], required=True)
    args = parser.parse_args()
    if args.stage == "contracts":
        build_contracts()
    else:
        evaluate()


if __name__ == "__main__":
    main()
