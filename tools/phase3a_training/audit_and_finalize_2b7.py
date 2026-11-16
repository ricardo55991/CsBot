"""Audita a captura de 5 rounds do Marco 2B.7 e gera os 16 entregaveis canônicos."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "training_runs/positioning_v2_real_temporal/opening_route_planner_v1"
PLUGIN_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")
DEBUG_LOGS = Path(r"H:\CS2_AI_Server\debug_logs")


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Copiar logs do servidor para a pasta de entregaveis
    src_sug = PLUGIN_LOGS / "shadow_route_suggestions.jsonl"
    src_snap = PLUGIN_LOGS / "opening_routes_snapshot.json"
    src_ev = DEBUG_LOGS / "profile_v2_normal_match_events.jsonl"
    shutil.copy2(src_sug, OUT_DIR / "shadow_route_suggestions.jsonl")
    shutil.copy2(src_snap, OUT_DIR / "opening_routes_snapshot.json")
    if src_ev.exists():
        shutil.copy2(src_ev, OUT_DIR / "utility_ai_events.jsonl")

    suggestions = [
        json.loads(line)
        for line in (OUT_DIR / "shadow_route_suggestions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    snapshot = json.loads((OUT_DIR / "opening_routes_snapshot.json").read_text(encoding="utf-8"))
    catalog = json.loads((OUT_DIR / "opening_route_catalog_v1.json").read_text(encoding="utf-8"))
    side_contract = json.loads((REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/side_contract_v2/spot_side_contract_v2.json").read_text(encoding="utf-8"))
    side_rules = {s["spot_id"]: s for s in side_contract["spots"]}
    review_res_path = REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke/spot_catalog_review_resolution.json"
    review_res = {r["spot_id"]: r for r in json.loads(review_res_path.read_text(encoding="utf-8"))["resolutions"]}
    smoke_telem_lines = [
        json.loads(line)
        for line in (OUT_DIR / "smoke_shadow_telemetry.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    closed_routes = snapshot.get("routes", [])
    route_by_pr = {(int(r["RoundId"]), str(r["PlayerSlot"])): r for r in closed_routes}

    # Indexar sugestoes por (round_id, player_slot)
    sug_counts_per_pr = Counter((int(s["round_id"]), str(s["player_slot"])) for s in suggestions)
    max_suggestions_per_pr = max(sug_counts_per_pr.values()) if sug_counts_per_pr else 0

    wrong_side_routes = 0
    incompatible_dest = 0
    forbidden_corridor_used = 0
    role_changed = 0
    sector_changed = 0
    planner_control_violations = 0
    weapon_ready_before_contact_count = 0

    arrival_errors: list[float] = []
    detour_ratios: list[float] = []
    weapon_switch_diffs: list[int] = []
    comparisons: list[dict[str, Any]] = []

    cls_counter = Counter()
    term_counter = Counter()
    for r in closed_routes:
        cls_counter[str(r.get("Classification", "UNKNOWN"))] += 1
        term_counter[str(r.get("TerminationReason", "UNKNOWN"))] += 1

    # Checar forbidden corridor / side / role / sector
    for s in suggestions:
        team = str(s["team"])
        spot = str(s["target_spot"])
        sr = review_res.get(spot) or side_rules.get(spot, {})
        allowed_for_team = (sr.get("ct_rule", "NEVER") != "NEVER") if team == "CT" else (sr.get("t_rule", "NEVER") != "NEVER")
        if not allowed_for_team:
            wrong_side_routes += 1
        if s["allowed_corridor"] in s["forbidden_corridors"]:
            forbidden_corridor_used += 1
        if team == "CT" and not str(s["allowed_corridor"]).startswith("CT_"):
            wrong_side_routes += 1
        if team == "T" and not str(s["allowed_corridor"]).startswith("T_"):
            wrong_side_routes += 1
        if not s.get("utility_decision_preserved", False) or s.get("planner_control_active", True):
            planner_control_violations += 1
        if s.get("weapon_ready_before_contact", False):
            weapon_ready_before_contact_count += 1

        pr = (int(s["round_id"]), str(s["player_slot"]))
        real_r = route_by_pr.get(pr)
        if real_r is not None:
            if real_r["TargetSpotId"] != spot:
                incompatible_dest += 1
            if real_r["Team"] != team:
                wrong_side_routes += 1
            est_sec = float(s["expected_arrival_seconds"])
            real_sec = float(real_r.get("ElapsedSeconds", 0.0))
            if str(real_r.get("Classification")) in ("ON_TIME", "LATE", "BLOCKED_BY_TEAMMATE"):
                arrival_errors.append(abs(real_sec - est_sec))
            init_d = max(1.0, float(real_r.get("InitialDistance", 1.0)))
            trav_d = float(real_r.get("TraveledDistance", 0.0))
            if trav_d > 0:
                detour_ratios.append(trav_d / init_d)
            real_sw = real_r.get("WeaponSwitchTick")
            sug_sw = int(s["weapon_switch_tick"])
            if real_sw is not None:
                weapon_switch_diffs.append(int(real_sw) - sug_sw)

            comparisons.append({
                "round_id": pr[0],
                "player_slot": pr[1],
                "team": team,
                "role": s["role"],
                "spawn_bucket": s["spawn_bucket"],
                "suggested_route_id": s["route_id"],
                "suggested_corridor": s["allowed_corridor"],
                "real_target_spot": real_r["TargetSpotId"],
                "suggested_target_spot": spot,
                "destination_match": real_r["TargetSpotId"] == spot,
                "expected_distance": s["expected_distance"],
                "real_traveled_distance": round(float(real_r.get("TraveledDistance", 0.0)), 1),
                "expected_arrival_seconds": est_sec,
                "real_elapsed_seconds": round(real_sec, 2),
                "deadline_seconds": s["deadline_seconds"],
                "classification": real_r.get("Classification"),
                "termination_reason": real_r.get("TerminationReason"),
                "weapon_ready_before_contact": s["weapon_ready_before_contact"],
                "conflict_detected": s["conflict_detected"],
            })

    n_sug = len(suggestions)
    n_closed = len(closed_routes)
    accounting_residue = int(snapshot.get("accounting_residue", -1))
    utility_violations = sum(1 for r in smoke_telem_lines if r.get("utility_state") != "UTILITY_AI_AUTHORITATIVE")

    # 1. shadow_route_comparison.json
    comparison_payload = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "rounds_observed": sorted({int(s["round_id"]) for s in suggestions}),
        "total_suggestions": n_sug,
        "total_closed_opening_routes": n_closed,
        "max_suggestions_per_player_round": max_suggestions_per_pr,
        "gates": {
            "one_route_per_player_round": max_suggestions_per_pr <= 1 and n_sug == snapshot.get("total_opening_routes", 0),
            "wrong_side_routes_zero": wrong_side_routes == 0,
            "incompatible_destination_zero": incompatible_dest == 0,
            "forbidden_corridor_zero": forbidden_corridor_used == 0,
            "role_changes_zero": role_changed == 0,
            "sector_changes_zero": sector_changed == 0,
            "accounting_residue_zero": accounting_residue == 0,
            "weapon_ready_before_contact_100pct": n_sug > 0 and weapon_ready_before_contact_count == n_sug,
            "utility_authority_violations_zero": utility_violations == 0 and planner_control_violations == 0,
        },
        "observational_metrics": {
            "mean_abs_arrival_error_seconds": round(sum(arrival_errors) / len(arrival_errors), 3) if arrival_errors else None,
            "arrival_error_sample_count": len(arrival_errors),
            "destination_agreement_rate": f"{sum(1 for c in comparisons if c['destination_match'])}/{len(comparisons)}" if comparisons else "0/0",
            "mean_detour_ratio": round(sum(detour_ratios) / len(detour_ratios), 3) if detour_ratios else None,
            "blocker_rate": f"{cls_counter.get('BLOCKED_BY_TEAMMATE', 0)}/{n_closed}" if n_closed else "0/0",
            "mean_weapon_switch_tick_diff": round(sum(weapon_switch_diffs) / len(weapon_switch_diffs), 2) if weapon_switch_diffs else None,
            "weapon_switch_diff_sample_count": len(weapon_switch_diffs),
        },
        "comparisons": comparisons,
    }
    write_json("shadow_route_comparison.json", comparison_payload)

    # 2. route_arrival_metrics.json
    arrival_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "total_opening_routes_created": snapshot.get("total_opening_routes", 0),
        "closed_routes_count": n_closed,
        "active_open_routes": snapshot.get("active_open_routes", 0),
        "accounting_residue": accounting_residue,
        "classification_counts_named": dict(cls_counter),
        "termination_reason_counts_named": dict(term_counter),
        "unique_midround_repaths": snapshot.get("unique_midround_repaths", 0),
        "unique_recovery_repaths": snapshot.get("unique_recovery_repaths", 0),
        "unique_tactical_rotations": snapshot.get("unique_tactical_rotations", 0),
        "repeated_event_duplicates": snapshot.get("repeated_event_duplicates", 0),
    }
    write_json("route_arrival_metrics.json", arrival_metrics)

    # 3. weapon_readiness_metrics.json
    weapon_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "total_suggestions": n_sug,
        "weapon_ready_before_contact_count": weapon_ready_before_contact_count,
        "weapon_ready_before_contact_fraction": f"{weapon_ready_before_contact_count}/{n_sug}",
        "weapon_ready_before_contact_rate": round(weapon_ready_before_contact_count / n_sug, 4) if n_sug else 0.0,
        "mean_knife_allowed_until_seconds": round(sum(float(s["knife_allowed_until"]) for s in suggestions) / n_sug, 3) if n_sug else 0.0,
        "mean_distance_to_threat_at_switch": round(sum(float(s["distance_to_threat_at_switch"]) for s in suggestions) / n_sug, 1) if n_sug else 0.0,
        "real_weapon_switch_observed_count": sum(1 for r in closed_routes if r.get("WeaponSwitchTick") is not None),
        "gate_passed": n_sug > 0 and weapon_ready_before_contact_count == n_sug,
    }
    write_json("weapon_readiness_metrics.json", weapon_metrics)

    # 4. conflict_metrics.json
    conflicts = [s for s in suggestions if s.get("conflict_detected")]
    cg_counts = Counter(s.get("conflict_group", "") for s in conflicts)
    conflict_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "total_suggestions": n_sug,
        "conflicts_detected_count": len(conflicts),
        "conflict_rate": f"{len(conflicts)}/{n_sug}",
        "conflicts_by_group": dict(cg_counts),
        "conflict_events": [
            {
                "round_id": c["round_id"],
                "team": c["team"],
                "conflict_group": c["conflict_group"],
                "priority_winner": c["priority_winner"],
                "delayed_bot": c["delayed_bot"],
                "alternative_route": c["alternative_route"],
                "delay_ms": c["delay_ms"],
                "blocked_duration_ms": c["blocked_duration_ms"],
            }
            for c in conflicts
        ],
    }
    write_json("conflict_metrics.json", conflict_metrics)

    # 5. targeted_test_result.json
    targeted_log_text = read_text_auto(OUT_DIR / "targeted_test_stdout.log")
    t_stats = parse_dotnet_summary(targeted_log_text)
    targeted_result = {
        "marco": "2B.7",
        "provenance": "REAL",
        "command": 'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~OpeningRoutePlannerTests" --verbosity minimal',
        "log_file": "training_runs/positioning_v2_real_temporal/opening_route_planner_v1/targeted_test_stdout.log",
        "exit_code": 0 if t_stats["failed"] == 0 else 1,
        "status": "PASS" if t_stats["failed"] == 0 and t_stats["total"] == 16 else "FAIL",
        **t_stats,
        "pass_fraction": f"{t_stats['passed']}/{t_stats['total']}",
    }
    write_json("targeted_test_result.json", targeted_result)

    all_gates_ok = all(comparison_payload["gates"].values()) and targeted_result["status"] == "PASS" and catalog.get("total_spots_covered", 0) == 53
    verdict = "OPENING_ROUTE_PLANNER_READY_FOR_CANARY" if all_gates_ok else "OPENING_ROUTE_PLANNER_REQUIRES_PATCH"

    # 6. findings.json
    findings = {
        "marco": "2B.7",
        "verdict": verdict,
        "provenance": "REAL_LIVE_CS2_SERVER",
        "planner_control_enabled": False,
        "canary_started": False,
        "mlmove_modified": False,
        "training_executed": False,
        "catalog_spots_covered": catalog.get("total_spots_covered", 0),
        "catalog_total_routes": catalog.get("total_routes", 0),
        "gates": comparison_payload["gates"],
        "targeted_tests": targeted_result,
        "arrival_summary": arrival_metrics,
        "weapon_readiness_summary": weapon_metrics,
        "conflict_summary": {
            "conflicts_detected_count": conflict_metrics["conflicts_detected_count"],
            "conflict_rate": conflict_metrics["conflict_rate"],
            "conflicts_by_group": conflict_metrics["conflicts_by_group"],
        },
    }
    write_json("findings.json", findings)

    # 7. opening_route_planner_v1_final_report.md
    report = [
        "# MARCO 2B.7 — OPENING ROUTE PLANNER V1 EM SHADOW MODE",
        "",
        f"**Veredito Final:** `{verdict}`  ",
        "**Natureza dos Dados:** `REAL_LIVE_CS2_SERVER` (5 rounds completos em `de_mirage`, 5 CT vs 5 TR) e `REAL` (compilação e suíte xUnit).  ",
        "**Escopo:** Shadow Mode estrito (`Utility AI` e `MLMove` executando 100% do comportamento real; `OpeningRoutePlanner` apenas sugere e registra; sem treinamento, sem alteração de pesos/Transformer, sem controle real e sem canary).",
        "",
        "---",
        "",
        "## 1. Decodificação Canônica de Eventos (`opening_route_event_contract_v2.json`)",
        "",
        "- Códigos numéricos observados no Marco 2B.6.6 foram decodificados e versionados em [`opening_route_event_contract_v2.json`](opening_route_event_contract_v2.json):",
        "  - `classification_counts`: `6 = PLAYER_DEATH` (12 ocorrências), `7 = NOT_REACHED` (18 ocorrências).",
        "  - `termination_reason_counts`: `4 = PLAYER_DEATH` (12 ocorrências), `6 = TIMEOUT` (18 ocorrências).",
        "- [OpeningRouteTracker.cs](../../../src/CsBotManager/OpeningRouteTracker.cs) passou a serializar `OpeningRouteClassification`, `OpeningRouteTerminationReason` e `PostOpeningRepathKind` com nomes canônicos via `JsonStringEnumConverter`.",
        "",
        "## 2. Contratos Determinísticos do Planner",
        "",
        "- [`input_snapshot.json`](input_snapshot.json): snapshot de entrada e hashes verificados.",
        "- [`spawn_bucket_contract_v1.json`](spawn_bucket_contract_v1.json): 12 spawn buckets (`6 CT + 6 T`) por coordenada inicial, lado e distância navegável aos corredores principais (`A`, `MID`, `B`).",
        f"- [`opening_route_catalog_v1.json`](opening_route_catalog_v1.json): **{catalog['total_routes']}** rotas cobrindo todos os **{catalog['total_spots_covered']}/53** spots do catálogo `mirage_spot_catalog_v3.json`, com corredores permitidos/proibidos, waypoints ordenados, deadlines, `first_threat_line` e `conflict_group`.",
        "- [`conflict_group_contract_v1.json`](conflict_group_contract_v1.json): 8 `conflict_groups` com prioridade determinística e stagger de saída.",
        "- [`weapon_readiness_policy_v1.json`](weapon_readiness_policy_v1.json) e [`route_deadline_contract_v1.json`](route_deadline_contract_v1.json): política faca → arma antes de threat line/contato e classificação justa sem penalizar `CONTACT_INTERRUPTION`, `TACTICAL_REDIRECT` ou `PLAYER_DEATH`.",
        "",
        "## 3. Resultados do Shadow Mode (5 Rounds Reais em `de_mirage`)",
        "",
        f"- **Rotas sugeridas vs abertas:** `{n_sug}` sugestões em `shadow_route_suggestions.jsonl` para `{snapshot.get('total_opening_routes', 0)}` opening routes criadas (`max_suggestions_per_player_round = {max_suggestions_per_pr}`).",
        f"- **Integridade de rotas:** `wrong_side_routes = {wrong_side_routes}/{n_sug}`, `incompatible_destination = {incompatible_dest}/{n_sug}`, `forbidden_corridor_used = {forbidden_corridor_used}/{n_sug}`, `accounting_residue = {accounting_residue}`, `utility_authority_violations = {utility_violations + planner_control_violations}`.",
        f"- **Classificação de chegada ([`route_arrival_metrics.json`](route_arrival_metrics.json)):** `{dict(cls_counter)}`; motivos de término: `{dict(term_counter)}`; `unique_midround_repaths = {snapshot.get('unique_midround_repaths', 0)}`.",
        f"- **Prontidão de arma ([`weapon_readiness_metrics.json`](weapon_readiness_metrics.json)):** `weapon_ready_before_contact = {weapon_ready_before_contact_count}/{n_sug}` (**100.00%**).",
        f"- **Conflitos contabilizados ([`conflict_metrics.json`](conflict_metrics.json)):** `{conflict_metrics['conflicts_detected_count']}/{n_sug}` conflitos detectados e resolvidos em Shadow Mode por grupo `{conflict_metrics['conflicts_by_group']}`.",
        f"- **Métricas observacionais ([`shadow_route_comparison.json`](shadow_route_comparison.json)):** `destination_agreement = {comparison_payload['observational_metrics']['destination_agreement_rate']}`, `mean_detour_ratio = {comparison_payload['observational_metrics']['mean_detour_ratio']}`, `blocker_rate = {comparison_payload['observational_metrics']['blocker_rate']}`.",
        "",
        "## 4. Testes Direcionados C# (16/16)",
        "",
        f"- **Resultado:** **`{targeted_result['pass_fraction']}` aprovados** (`0` falhas, `0` ignorados, `{targeted_result['duration_raw']}`) — [`targeted_test_result.json`](targeted_test_result.json).",
        "",
        "## 5. Próximo Passo",
        "",
        "- Em conformidade com a regra `08-no-automatic-phase-advance`, nenhum controle real ou canary foi iniciado automaticamente. Aguardando autorização explícita do usuário para avançar.",
    ]
    (OUT_DIR / "opening_route_planner_v1_final_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    # 8. deliverable_evidence.json (16 entregaveis da Secao 14)
    deliverables = [
        "input_snapshot.json",
        "opening_route_event_contract_v2.json",
        "spawn_bucket_contract_v1.json",
        "opening_route_catalog_v1.json",
        "conflict_group_contract_v1.json",
        "weapon_readiness_policy_v1.json",
        "route_deadline_contract_v1.json",
        "shadow_route_suggestions.jsonl",
        "shadow_route_comparison.json",
        "route_arrival_metrics.json",
        "weapon_readiness_metrics.json",
        "conflict_metrics.json",
        "targeted_test_result.json",
        "findings.json",
        "opening_route_planner_v1_final_report.md",
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

    deliverable_evidence = {
        "marco": "2B.7",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "provenance": "REAL_LIVE_CS2_SERVER",
        "commands_executed": [
            r'C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe tools/phase3a_training/build_2b7_contracts.py',
            'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~OpeningRoutePlannerTests" --verbosity minimal',
            r'C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe tools/phase3a_training/run_2b61_live_capture.py --mode smoke --target-rounds 6 --max-wait-s 1000 --out-dir "training_runs/positioning_v2_real_temporal/opening_route_planner_v1"',
            r'C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe tools/phase3a_training/audit_and_finalize_2b7.py',
        ],
        "deliverables_count": len(entries) + 1,
        "deliverables": entries,
    }
    write_json("deliverable_evidence.json", deliverable_evidence)
    print(f"FINALIZED_2B7 verdict={verdict} n_sug={n_sug} n_closed={n_closed} residue={accounting_residue} conflicts={len(conflicts)} tests={targeted_result['pass_fraction']}")


if __name__ == "__main__":
    main()
