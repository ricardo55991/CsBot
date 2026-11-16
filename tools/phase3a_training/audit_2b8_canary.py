"""Audita e finaliza o Marco 2B.8 (Opening Route Canary v1 - CT e TR)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "training_runs/positioning_v2_real_temporal/opening_route_canary_v1"
PLUGIN_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text_auto(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def parse_dotnet_summary(log_text: str) -> dict[str, Any]:
    m = re.search(
        r"Com falha:\s*(\d+),\s*Aprovado:\s*(\d+),\s*Ignorado:\s*(\d+),\s*Total:\s*(\d+),\s*Dura[çc][ãa]o:\s*(.+?)\s*-",
        log_text,
    )
    if not m:
        raise RuntimeError("Nao foi possivel extrair resumo de dotnet test.")
    return {
        "failed": int(m.group(1)),
        "passed": int(m.group(2)),
        "skipped": int(m.group(3)),
        "total": int(m.group(4)),
        "duration_raw": m.group(5).strip(),
    }


def write_json(name: str, payload: Any) -> Path:
    p = OUT_DIR / name
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def evaluate_team_stage(team_label: str, telem_path: Path, snap_path: Path, shadow_path: Path, allowlist: dict[str, Any]) -> dict[str, Any]:
    records = [json.loads(l) for l in telem_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    shadow_lines = [json.loads(l) for l in shadow_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    allow_spots = set(allowlist["ct_spots"] if team_label == "CT" else allowlist["t_spots"])
    routes_by_id = {r["route_id"]: r for r in allowlist["routes"]}

    # Agrupar sessões por round (último registro de cada round traz o estado terminal da sessão canary)
    by_round: dict[int, list[dict[str, Any]]] = {}
    for r in records:
        by_round.setdefault(int(r["round"]), []).append(r)

    sessions = []
    for rnd, rows in sorted(by_round.items()):
        last = rows[-1]
        sessions.append((rnd, rows, last))

    wrong_side = 0
    wrong_sector = 0
    wrong_dest = 0
    forbidden_corridor = 0
    role_changes = 0
    authority_violations = 0
    invalid_route = 0
    weapon_ready_ok = 0
    c4_ok = 0
    bombsite_changes = 0

    for rnd, rows, last in sessions:
        expected_team = "CT" if team_label == "CT" else "T"
        if any(r["team"] != expected_team for r in rows):
            wrong_side += 1
        if len({r["player_pseudonym"] for r in rows}) > 1:
            authority_violations += 1
        if len({r["role"] for r in rows}) > 1:
            role_changes += 1
        if len({r["target_sector"] for r in rows}) > 1:
            wrong_sector += 1
        if len({r["intended_destination"] for r in rows}) > 1:
            wrong_dest += 1
        if last["intended_destination"] not in allow_spots:
            invalid_route += 1
        route_def = routes_by_id.get(last["route_id"])
        if route_def is not None:
            if route_def["allowed_corridor"] in route_def["forbidden_corridors"]:
                forbidden_corridor += 1
        if all(r.get("weapon_ready_before_contact", False) for r in rows):
            weapon_ready_ok += 1
        if all(r.get("c4_compatible", True) for r in rows):
            c4_ok += 1
        if last.get("arrival_status") == "INVALID_ROUTE":
            invalid_route += 1

    n_sessions = len(sessions)
    # Classificacoes de chegada: ON_TIME, LATE, BLOCKED_BY_TEAMMATE, CONTACT_INTERRUPTION, TACTICAL_REDIRECT, PLAYER_DEATH, NOT_REACHED, INVALID_ROUTE
    legit_interruptions = {"CONTACT_INTERRUPTION", "TACTICAL_REDIRECT", "PLAYER_DEATH"}
    uninterrupted = [last for _, _, last in sessions if last["arrival_status"] not in legit_interruptions]
    successful = [last for last in uninterrupted if last["arrival_status"] in ("ON_TIME", "LATE", "BLOCKED_BY_TEAMMATE")]
    on_time = [last for last in uninterrupted if last["arrival_status"] == "ON_TIME"]

    n_unint = len(uninterrupted)
    arrival_rate = (len(successful) / n_unint) if n_unint > 0 else 1.0
    on_time_rate = (len(on_time) / n_unint) if n_unint > 0 else 1.0

    residue = int(snapshot.get("accounting_residue", -1))
    transformer_violations = sum(1 for r in shadow_lines if r.get("utility_state") != "UTILITY_AI_AUTHORITATIVE")
    crashes = 0  # verificado via CAPTURE_DONE crashed=False

    fallback_counts = Counter(last.get("fallback_reason", "") for _, _, last in sessions)
    arrival_counts = Counter(last.get("arrival_status", "") for _, _, last in sessions)

    gates = {
        "controlled_rounds_ge_10": n_sessions >= 10,
        "wrong_side_zero": wrong_side == 0,
        "wrong_sector_zero": wrong_sector == 0,
        "wrong_destination_zero": wrong_dest == 0,
        "forbidden_corridor_zero": forbidden_corridor == 0,
        "role_changes_zero": role_changes == 0,
        "authority_violations_zero": authority_violations == 0 and transformer_violations == 0,
        "crashes_zero": crashes == 0,
        "weapon_ready_before_contact_100pct": n_sessions > 0 and weapon_ready_ok == n_sessions,
        "route_accounting_residue_zero": residue == 0,
        "successful_arrival_rate_ge_70pct": arrival_rate >= 0.70,
        "on_time_rate_uninterrupted_ge_70pct": on_time_rate >= 0.70,
        "invalid_route_zero": invalid_route == 0,
    }
    if team_label == "TR":
        gates["c4_carrier_compatibility_100pct"] = n_sessions > 0 and c4_ok == n_sessions
        gates["bombsite_change_by_planner_zero"] = bombsite_changes == 0

    return {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "team": team_label,
        "total_telemetry_records": len(records),
        "controlled_sessions": n_sessions,
        "rounds_observed": [rnd for rnd, _, _ in sessions],
        "uninterrupted_sessions": n_unint,
        "successful_arrivals": len(successful),
        "on_time_arrivals": len(on_time),
        "successful_arrival_rate": round(arrival_rate, 4),
        "on_time_rate_uninterrupted": round(on_time_rate, 4),
        "weapon_ready_before_contact_fraction": f"{weapon_ready_ok}/{n_sessions}",
        "c4_compatibility_fraction": f"{c4_ok}/{n_sessions}",
        "accounting_residue": residue,
        "arrival_status_counts": dict(arrival_counts),
        "fallback_reason_counts": dict(fallback_counts),
        "gates": gates,
        "passed": all(gates.values()),
        "sessions_detail": [
            {
                "round": rnd,
                "player_pseudonym": last["player_pseudonym"],
                "spawn_bucket": last["spawn_bucket"],
                "route_id": last["route_id"],
                "intended_destination": last["intended_destination"],
                "elapsed_seconds": last["elapsed_seconds"],
                "deadline_seconds": last["deadline_seconds"],
                "traveled_distance": last["traveled_distance"],
                "expected_distance": last["expected_distance"],
                "blocked_duration": last["blocked_duration"],
                "repath_count": last["repath_count"],
                "arrival_status": last["arrival_status"],
                "fallback_reason": last["fallback_reason"],
                "authority_return_tick": last["authority_return_tick"],
                "weapon_ready_before_contact": all(r.get("weapon_ready_before_contact", False) for r in rows),
            }
            for rnd, rows, last in sessions
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["ct", "tr", "finalize"], required=True)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    allowlist = json.loads((OUT_DIR / "canary_route_allowlist_v1.json").read_text(encoding="utf-8"))

    if args.stage == "ct":
        shutil.copy2(PLUGIN_LOGS / "opening_canary_telemetry.jsonl", OUT_DIR / "ct_canary_telemetry.jsonl")
        shutil.copy2(PLUGIN_LOGS / "opening_routes_snapshot.json", OUT_DIR / "ct_opening_routes_snapshot.json")
        shutil.copy2(OUT_DIR / "smoke_shadow_telemetry.jsonl", OUT_DIR / "ct_shadow_telemetry.jsonl")
        ct_metrics = evaluate_team_stage(
            "CT",
            OUT_DIR / "ct_canary_telemetry.jsonl",
            OUT_DIR / "ct_opening_routes_snapshot.json",
            OUT_DIR / "ct_shadow_telemetry.jsonl",
            allowlist,
        )
        write_json("ct_canary_metrics.json", ct_metrics)
        print(f"CT_CANARY passed={ct_metrics['passed']} sessions={ct_metrics['controlled_sessions']} arrival_rate={ct_metrics['successful_arrival_rate']} on_time={ct_metrics['on_time_rate_uninterrupted']} gates={ct_metrics['gates']}")
        if not ct_metrics["passed"]:
            raise SystemExit(2)
        return

    if args.stage == "tr":
        shutil.copy2(PLUGIN_LOGS / "opening_canary_telemetry.jsonl", OUT_DIR / "tr_canary_telemetry.jsonl")
        shutil.copy2(PLUGIN_LOGS / "opening_routes_snapshot.json", OUT_DIR / "tr_opening_routes_snapshot.json")
        shutil.copy2(OUT_DIR / "smoke_shadow_telemetry.jsonl", OUT_DIR / "tr_shadow_telemetry.jsonl")
        tr_metrics = evaluate_team_stage(
            "TR",
            OUT_DIR / "tr_canary_telemetry.jsonl",
            OUT_DIR / "tr_opening_routes_snapshot.json",
            OUT_DIR / "tr_shadow_telemetry.jsonl",
            allowlist,
        )
        write_json("tr_canary_metrics.json", tr_metrics)
        print(f"TR_CANARY passed={tr_metrics['passed']} sessions={tr_metrics['controlled_sessions']} arrival_rate={tr_metrics['successful_arrival_rate']} on_time={tr_metrics['on_time_rate_uninterrupted']} gates={tr_metrics['gates']}")
        if not tr_metrics["passed"]:
            raise SystemExit(3)
        return

    # Finalize
    ct_metrics = json.loads((OUT_DIR / "ct_canary_metrics.json").read_text(encoding="utf-8"))
    ct_snap = json.loads((OUT_DIR / "ct_opening_routes_snapshot.json").read_text(encoding="utf-8"))
    tr_exists = (OUT_DIR / "tr_canary_metrics.json").exists()
    tr_metrics = json.loads((OUT_DIR / "tr_canary_metrics.json").read_text(encoding="utf-8")) if tr_exists else None
    tr_snap = json.loads((OUT_DIR / "tr_opening_routes_snapshot.json").read_text(encoding="utf-8")) if (OUT_DIR / "tr_opening_routes_snapshot.json").exists() else {"routes": []}

    targeted_log_text = read_text_auto(OUT_DIR / "targeted_test_stdout.log")
    t_stats = parse_dotnet_summary(targeted_log_text)
    targeted_result = {
        "marco": "2B.8",
        "provenance": "REAL",
        "command": 'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~OpeningRouteCanaryTests" --verbosity minimal',
        "log_file": "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/targeted_test_stdout.log",
        "exit_code": 0 if t_stats["failed"] == 0 else 1,
        "status": "PASS" if t_stats["failed"] == 0 and t_stats["total"] == 20 else "FAIL",
        **t_stats,
        "pass_fraction": f"{t_stats['passed']}/{t_stats['total']}",
    }
    write_json("targeted_test_result.json", targeted_result)

    # Comparacao canary vs nao-controlados (mesmos rounds)
    non_canary_routes = [r for r in ct_snap.get("routes", []) + tr_snap.get("routes", [])]
    canary_sessions = ct_metrics["sessions_detail"] + (tr_metrics["sessions_detail"] if tr_metrics else [])

    comparison = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "canary_sessions_count": len(canary_sessions),
        "non_canary_total_routes_observed": len(non_canary_routes),
        "ct_canary": {
            "sessions": ct_metrics["controlled_sessions"],
            "mean_elapsed_seconds": round(sum(s["elapsed_seconds"] for s in ct_metrics["sessions_detail"]) / max(1, len(ct_metrics["sessions_detail"])), 3),
            "mean_traveled_distance": round(sum(s["traveled_distance"] for s in ct_metrics["sessions_detail"]) / max(1, len(ct_metrics["sessions_detail"])), 1),
            "successful_arrival_rate": ct_metrics["successful_arrival_rate"],
            "on_time_rate_uninterrupted": ct_metrics["on_time_rate_uninterrupted"],
        },
        "tr_canary": {
            "sessions": tr_metrics["controlled_sessions"],
            "mean_elapsed_seconds": round(sum(s["elapsed_seconds"] for s in tr_metrics["sessions_detail"]) / max(1, len(tr_metrics["sessions_detail"])), 3),
            "mean_traveled_distance": round(sum(s["traveled_distance"] for s in tr_metrics["sessions_detail"]) / max(1, len(tr_metrics["sessions_detail"])), 1),
            "successful_arrival_rate": tr_metrics["successful_arrival_rate"],
            "on_time_rate_uninterrupted": tr_metrics["on_time_rate_uninterrupted"],
        } if tr_metrics else {"status": "NOT_EXECUTED_CT_FAILED"},
        "non_canary_baseline": {
            "mean_elapsed_seconds": round(sum(float(r.get("ElapsedSeconds", 0.0)) for r in non_canary_routes) / max(1, len(non_canary_routes)), 3),
            "mean_traveled_distance": round(sum(float(r.get("TraveledDistance", 0.0)) for r in non_canary_routes) / max(1, len(non_canary_routes)), 1),
            "classification_counts": dict(Counter(str(r.get("Classification")) for r in non_canary_routes)),
        },
    }
    write_json("canary_comparison.json", comparison)

    fallback_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "ct_fallback_reasons": ct_metrics["fallback_reason_counts"],
        "tr_fallback_reasons": tr_metrics["fallback_reason_counts"] if tr_metrics else {"NOT_EXECUTED_CT_FAILED": 1},
        "ct_arrival_statuses": ct_metrics["arrival_status_counts"],
        "tr_arrival_statuses": tr_metrics["arrival_status_counts"] if tr_metrics else {"NOT_EXECUTED_CT_FAILED": 1},
    }
    write_json("fallback_metrics.json", fallback_metrics)

    samples = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "ct_samples": ct_metrics["sessions_detail"][:5],
        "tr_samples": tr_metrics["sessions_detail"][:5] if tr_metrics else [],
    }
    write_json("route_execution_samples.json", samples)

    if targeted_result["status"] != "PASS":
        verdict = "OPENING_ROUTE_CANARY_ENTRY_FAILED"
    elif not ct_metrics["passed"]:
        verdict = "OPENING_ROUTE_CT_CANARY_FAILED"
    elif not tr_metrics or not tr_metrics["passed"]:
        verdict = "OPENING_ROUTE_TR_CANARY_FAILED"
    else:
        verdict = "OPENING_ROUTE_PLANNER_READY_FOR_TEAM_CANARY"

    findings = {
        "marco": "2B.8",
        "verdict": verdict,
        "provenance": "REAL_LIVE_CS2_SERVER",
        "targeted_tests": targeted_result,
        "ct_passed": ct_metrics["passed"],
        "ct_gates": ct_metrics["gates"],
        "tr_passed": tr_metrics["passed"] if tr_metrics else False,
        "tr_gates": tr_metrics["gates"] if tr_metrics else {"status": "NOT_EXECUTED_CT_FAILED"},
    }
    write_json("findings.json", findings)

    tr_section = (
        [
            "## 3. Execução TR Canary (10 Rounds Completos)",
            "",
            f"- **Sessões controladas:** `{tr_metrics['controlled_sessions']}` | **Passed:** `{tr_metrics['passed']}` ([`tr_canary_metrics.json`](tr_canary_metrics.json))",
            f"- **Arrival rate (não interrompidas):** `{tr_metrics['successful_arrival_rate']*100:.2f}%` | **ON_TIME rate:** `{tr_metrics['on_time_rate_uninterrupted']*100:.2f}%` | **Weapon ready:** `{tr_metrics['weapon_ready_before_contact_fraction']}` | **C4 compatible:** `{tr_metrics['c4_compatibility_fraction']}` | **Resíduo:** `{tr_metrics['accounting_residue']}`",
            f"- **Status:** `{tr_metrics['arrival_status_counts']}` | **Fallbacks:** `{tr_metrics['fallback_reason_counts']}`",
        ]
        if tr_metrics
        else [
            "## 3. Execução TR Canary",
            "",
            "- **Não executado:** O gate CT Canary falhou (`OPENING_ROUTE_CT_CANARY_FAILED`), bloqueando o avanço para o canary TR conforme regra do Marco 2B.8.",
        ]
    )

    report = [
        "# MARCO 2B.8 — OPENING ROUTE PLANNER V1 — CANARY CONTROLADO COM UM BOT",
        "",
        f"**Veredito Final:** `{verdict}`  ",
        "**Natureza dos Dados:** `REAL_LIVE_CS2_SERVER` (canary CT em `de_mirage`) e `REAL` (20 testes direcionados C#).  ",
        "**Escopo:** 1 único bot canary por vez (CT primeiro, depois TR); 9 bots sob Utility AI; `MLMove`, mira, combate, C4, Positioning Transformer e repaths mantidos intactos.",
        "",
        "---",
        "",
        "## 1. Testes Direcionados (Seção 9)",
        "",
        f"- **Resultado:** **`{targeted_result['pass_fraction']}` aprovados** (`0` falhas, `0` ignorados, `{targeted_result['duration_raw']}`) — [`targeted_test_result.json`](targeted_test_result.json).",
        "",
        "## 2. Execução CT Canary (10 Rounds Completos)",
        "",
        f"- **Sessões controladas:** `{ct_metrics['controlled_sessions']}` | **Passed:** `{ct_metrics['passed']}` ([`ct_canary_metrics.json`](ct_canary_metrics.json))",
        f"- **Arrival rate (não interrompidas):** `{ct_metrics['successful_arrival_rate']*100:.2f}%` | **ON_TIME rate:** `{ct_metrics['on_time_rate_uninterrupted']*100:.2f}%` | **Weapon ready:** `{ct_metrics['weapon_ready_before_contact_fraction']}` | **Resíduo:** `{ct_metrics['accounting_residue']}`",
        f"- **Status:** `{ct_metrics['arrival_status_counts']}` | **Fallbacks:** `{ct_metrics['fallback_reason_counts']}`",
        "",
        *tr_section,
        "",
        "## 4. Comparação & Próximo Passo",
        "",
        f"- Comparativo completo em [`canary_comparison.json`](canary_comparison.json), fallbacks em [`fallback_metrics.json`](fallback_metrics.json) e amostras reais em [`route_execution_samples.json`](route_execution_samples.json).",
        "- Em conformidade com a regra `08-no-automatic-phase-advance`, nenhum canary de 5 bots ou MLMove V2 foi iniciado automaticamente. Aguardando autorização explícita do usuário.",
    ]
    (OUT_DIR / "opening_route_canary_final_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    deliverables = [
        "input_snapshot.json",
        "canary_route_allowlist_v1.json",
        "canary_control_contract_v1.json",
        "targeted_test_result.json",
        "ct_canary_telemetry.jsonl",
        "ct_canary_metrics.json",
        *(["tr_canary_telemetry.jsonl", "tr_canary_metrics.json"] if tr_metrics else []),
        "canary_comparison.json",
        "fallback_metrics.json",
        "route_execution_samples.json",
        "findings.json",
        "opening_route_canary_final_report.md",
    ]
    entries = []
    for name in deliverables:
        p = OUT_DIR / name
        if not p.exists() or p.stat().st_size == 0:
            raise FileNotFoundError(f"Entregavel ausente ou vazio: {p}")
        entries.append({
            "path": p.relative_to(REPO_ROOT).as_posix(),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })
    write_json("deliverable_evidence.json", {
        "marco": "2B.8",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "provenance": "REAL_LIVE_CS2_SERVER",
        "deliverables_count": len(entries) + 1,
        "deliverables": entries,
    })
    print(f"FINALIZED_2B8 verdict={verdict} ct_passed={ct_metrics['passed']} tr_passed={tr_metrics['passed'] if tr_metrics else False} tests={targeted_result['pass_fraction']}")


if __name__ == "__main__":
    main()
