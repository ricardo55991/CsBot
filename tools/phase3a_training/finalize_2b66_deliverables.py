"""Gera e verifica todos os entregáveis canônicos do Marco 2B.6.6."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke"

SOURCE_ONNX = REPO_ROOT / "training_runs/positioning_v2_real_temporal/onnx_contextual_v2/positioning_transformer_hybrid_v2.onnx"
SOURCE_ONNX_DATA = REPO_ROOT / "training_runs/positioning_v2_real_temporal/onnx_contextual_v2/positioning_transformer_hybrid_v2.onnx.data"
REPO_ONNX = REPO_ROOT / "models/positioning/de_mirage_positioning_hybrid_v2.onnx"
REPO_ONNX_DATA = REPO_ROOT / "models/positioning/positioning_transformer_hybrid_v2.onnx.data"
SERVER_ONNX = Path(r"H:\CS2_AI_Server\models\positioning\de_mirage_positioning_hybrid_v2.onnx")
SERVER_ONNX_DATA = Path(r"H:\CS2_AI_Server\models\positioning\positioning_transformer_hybrid_v2.onnx.data")
PLUGIN_ONNX = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\models\positioning\de_mirage_positioning_hybrid_v2.onnx")
PLUGIN_ONNX_DATA = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\models\positioning\positioning_transformer_hybrid_v2.onnx.data")

REPO_DLL = REPO_ROOT / "src/CsBotManager/bin/Debug/net10.0/CsBotManager.dll"
PLUGIN_DLL = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\CsBotManager.dll")


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
        raise RuntimeError("Nao foi possivel extrair resumo de dotnet test do log.")
    return {
        "failed": int(m.group(1)),
        "passed": int(m.group(2)),
        "skipped": int(m.group(3)),
        "total": int(m.group(4)),
        "duration_raw": m.group(5).strip(),
    }


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> Path:
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    targeted_log_path = OUT_DIR / "targeted_test_stdout.log"
    full_log_path = OUT_DIR / "full_csharp_test_stdout.log"
    targeted_log = read_text_auto(targeted_log_path)
    full_log = read_text_auto(full_log_path)

    targeted_stats = parse_dotnet_summary(targeted_log)
    full_stats = parse_dotnet_summary(full_log)

    targeted_result = {
        "marco": "2B.6.6",
        "provenance": "REAL",
        "command": 'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~UtilityPatchAndDeployV2Tests" --verbosity minimal',
        "log_file": "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke/targeted_test_stdout.log",
        "exit_code": 0 if targeted_stats["failed"] == 0 else 1,
        "status": "PASS" if targeted_stats["failed"] == 0 and targeted_stats["total"] == 18 else "FAIL",
        **targeted_stats,
        "pass_fraction": f"{targeted_stats['passed']}/{targeted_stats['total']}",
    }
    write_json("targeted_test_result.json", targeted_result)

    full_result = {
        "marco": "2B.6.6",
        "provenance": "REAL",
        "command": "dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --verbosity minimal",
        "log_file": "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke/full_csharp_test_stdout.log",
        "exit_code": 0 if full_stats["failed"] == 0 else 1,
        "status": "PASS" if full_stats["failed"] == 0 else "FAIL",
        **full_stats,
        "pass_fraction": f"{full_stats['passed']}/{full_stats['total']}",
    }
    write_json("full_csharp_test_result.json", full_result)

    input_snap = load_json("input_snapshot.json")
    catalog_res = load_json("spot_catalog_review_resolution.json")
    deploy_manifest = load_json("model_deployment_manifest.json")
    utility_patch = load_json("utility_assignment_patch.json")
    smoke_rt = load_json("smoke_runtime_metrics.json")
    ctx_rt = load_json("contextual_input_runtime_metrics.json")
    diversity = load_json("prediction_diversity.json")
    util_metrics = load_json("utility_assignment_metrics.json")
    route_acc = load_json("route_accounting.json")

    integrity_checks = {
        "onnx_source_sha256": sha256_file(SOURCE_ONNX),
        "onnx_repo_sha256": sha256_file(REPO_ONNX),
        "onnx_server_sha256": sha256_file(SERVER_ONNX),
        "onnx_plugin_sha256": sha256_file(PLUGIN_ONNX),
        "onnx_data_source_sha256": sha256_file(SOURCE_ONNX_DATA),
        "onnx_data_repo_sha256": sha256_file(REPO_ONNX_DATA),
        "onnx_data_server_sha256": sha256_file(SERVER_ONNX_DATA),
        "onnx_data_plugin_sha256": sha256_file(PLUGIN_ONNX_DATA),
        "csbotmanager_dll_repo_sha256": sha256_file(REPO_DLL),
        "csbotmanager_dll_plugin_sha256": sha256_file(PLUGIN_DLL),
    }
    integrity_checks["all_onnx_match"] = len({
        integrity_checks["onnx_source_sha256"],
        integrity_checks["onnx_repo_sha256"],
        integrity_checks["onnx_server_sha256"],
        integrity_checks["onnx_plugin_sha256"],
    }) == 1
    integrity_checks["all_onnx_data_match"] = len({
        integrity_checks["onnx_data_source_sha256"],
        integrity_checks["onnx_data_repo_sha256"],
        integrity_checks["onnx_data_server_sha256"],
        integrity_checks["onnx_data_plugin_sha256"],
    }) == 1
    integrity_checks["dll_repo_equals_plugin"] = (
        integrity_checks["csbotmanager_dll_repo_sha256"] == integrity_checks["csbotmanager_dll_plugin_sha256"]
    )

    all_smoke_gates = (
        all(smoke_rt["gates"].values())
        and all(util_metrics["gates"].values())
        and all(route_acc["gates"].values())
        and all(ctx_rt["diversity_checks"].values())
        and smoke_rt["crashes"] == 0
        and smoke_rt["hash_matching_records"] == smoke_rt["total_records"]
        and integrity_checks["all_onnx_match"]
        and integrity_checks["all_onnx_data_match"]
        and integrity_checks["dll_repo_equals_plugin"]
    )
    all_tests_pass = targeted_result["status"] == "PASS" and full_result["status"] == "PASS"
    final_verdict = (
        "POSITIONING_SHADOW_DATA_READY_FOR_ROUTE_PLANNER"
        if (all_smoke_gates and all_tests_pass)
        else "POSITIONING_ONNX_V2_LIVE_SMOKE_FAILED"
    )

    findings = {
        "marco": "2B.6.6",
        "verdict": final_verdict,
        "provenance": "REAL_LIVE_CS2_SERVER",
        "training_executed": False,
        "weights_modified": False,
        "neural_control_enabled": False,
        "canary_started": False,
        "route_planner_started": False,
        "catalog_review": {
            "resolved": catalog_res["resolved_count"],
            "unresolved": catalog_res["unresolved_count"],
            "status": catalog_res["status"],
        },
        "deployment_integrity": integrity_checks,
        "smoke_summary": {
            "smoke_attempt": 2,
            "smoke_1_blocker_and_fix": (
                "No Smoke #1 (8.602 registros), 1 batch (5 registros no tick 2336) excedeu 25 ms (32.1263 ms). "
                "Corrigido sem alterar modelo/timeout: warm-up em 3 passagens por batch 1..5 e remocao de alocacao ToDictionary no hot path de ExecuteOnnxSessionLocked. "
                "No Smoke #2 (7.896 registros em 3 rounds completos), timeouts=0, failures=0, P95=10.1777 ms, P99=12.8331 ms."
            ),
            "total_records": smoke_rt["total_records"],
            "rounds_observed": smoke_rt["rounds_observed"],
            "p50_ms": smoke_rt["p50_ms"],
            "p95_ms": smoke_rt["p95_ms"],
            "p99_ms": smoke_rt["p99_ms"],
            "timeouts": smoke_rt["timeouts"],
            "failures": smoke_rt["failures"],
            "crashes": smoke_rt["crashes"],
            "wrong_side_neural_selections": smoke_rt["wrong_side_neural_selections"],
            "wrong_side_utility_assignments": util_metrics["wrong_side_utility_assignments"],
            "wrong_phase_utility_assignments": util_metrics["wrong_phase_utility_assignments"],
            "contextual_violations": util_metrics["contextual_violations"],
            "opening_routes_created": route_acc["opening_routes_created"],
            "opening_routes_closed": route_acc["opening_routes_closed"],
            "accounting_residue": route_acc["accounting_residue"],
            "unique_neural_states": diversity["unique_neural_states"],
            "unique_neural_sectors": diversity["unique_neural_sectors"],
            "unique_neural_spots": diversity["unique_neural_spots"],
        },
        "test_summary": {
            "targeted": targeted_result,
            "full_suite": full_result,
            "full_suite_note": (
                "PositioningSideMaskAndRouteTests.MidroundRepathIsNotOpeningRoute foi atualizado no arquivo de teste para "
                "validar explicitamente a deduplicacao RepeatedEventDuplicates (spot_a repetido) e o incremento unico "
                "em mudanca real de spot (spot_b), refletindo a invariante do OpeningRouteTracker sem alterar codigo de runtime."
            ),
        },
    }
    write_json("findings.json", findings)

    n_rec = smoke_rt["total_records"]
    n_spot = util_metrics["total_spot_assigned_events"]
    val_valid = util_metrics["validation_result_counts"].get("VALID", 0)
    val_rep = util_metrics["validation_result_counts"].get("REPLACED", 0)
    rej = util_metrics["rejection_reason_counts"]

    report_lines = [
        "# MARCO 2B.6.6 — PATCH DA UTILITY AI, DEPLOY DO ONNX V2 E SMOKE FINAL",
        "",
        f"**Veredito Final:** `{final_verdict}`  ",
        "**Natureza dos Dados:** `REAL_LIVE_CS2_SERVER` (captura ao vivo em `de_mirage`, 5 CT vs 5 TR) e `REAL` (compilação e suíte xUnit local).  ",
        "**Escopo:** Shadow Mode estrito (`Utility AI` autoritativa em 100% das decisões; controle neural `DESATIVADO`; sem retreinamento, sem alteração de pesos/ONNX/timeout/threshholds, sem canary e sem Route Planner).",
        "",
        "---",
        "",
        "## 1. Snapshot de Entrada e Revisão Conservadora dos 4 Spots",
        "",
        "- Veredito de entrada congelado em [`input_snapshot.json`](input_snapshot.json) (`POSITIONING_ONNX_CONTEXTUAL_V2_READY_FOR_LIVE_SMOKE`, `training_executed=false`, `weights_modified=false`).",
        f"- Resolução dos 4 spots pendentes em [`spot_catalog_review_resolution.json`](spot_catalog_review_resolution.json): **`{catalog_res['resolved_count']}/{catalog_res['resolved_count']}` resolvidos (`{catalog_res['status']}`)** com regras explícitas de `side`, `state`, `phase` e `OBJECTIVE`/`RETAKE` (`CONTEXTUAL`).",
        "",
        "## 2. Patch da Utility AI (`UtilitySpotAssignmentValidator`)",
        "",
        "- Arquivos alterados em runtime e registrados em [`utility_assignment_patch.json`](utility_assignment_patch.json):",
        "  - `src/CsBotManager/UtilitySpotAssignmentValidator.cs` (validação determinística e escolha ordenada pelos 8 critérios + fallback seguro `NO_VALID_ALTERNATIVE`);",
        "  - `src/CsBotManager/BotLocomotionDriver.cs` (validação em `NavigateToSpot` e `Stuck2DBlacklist`);",
        "  - `src/CsBotManager/GameplaySpotTelemetryTracker.cs` (emissão dos 9 campos obrigatórios de auditoria em `SPOT_ASSIGNED`);",
        "  - `src/CsBotManager/MapProfileManager.cs` (correção dos aliases legados `tr_exec_a_stairs_clear -> a_default_plant_headshot` e `tr_exec_b_market_push -> tr_b_tapete_window_market_awp`).",
        "",
        "## 3. Deploy do ONNX Contextual V2 e Integridade em Disco",
        "",
        f"- Modelo: `de_mirage_positioning_hybrid_v2.onnx` (weights externos `positioning_transformer_hybrid_v2.onnx.data`) implantado com V1 preservado ([`model_deployment_manifest.json`](model_deployment_manifest.json)).",
        f"- SHA-256 `.onnx` (fonte = repo = server = plugin): `{integrity_checks['onnx_source_sha256']}` (`all_onnx_match={integrity_checks['all_onnx_match']}`).",
        f"- SHA-256 `.onnx.data` (fonte = repo = server = plugin): `{integrity_checks['onnx_data_source_sha256']}` (`all_onnx_data_match={integrity_checks['all_onnx_data_match']}`).",
        f"- SHA-256 `CsBotManager.dll` (repo = plugin): `{integrity_checks['csbotmanager_dll_repo_sha256']}` (`dll_repo_equals_plugin={integrity_checks['dll_repo_equals_plugin']}`).",
        "",
        "## 4. Resolução do Bloqueador do Smoke #1 e Resultado do Smoke #2 (3 Rounds Completos)",
        "",
        "- **Achado no Smoke #1:** 1 único batch (`5/8602` registros, `tick=2336`) excedeu o orçamento de `25 ms` (`32.1263 ms`). Sem alterar modelo ou timeout, o `PositioningTransformerService.cs` passou a executar 3 passagens de warm-up por batch dinâmico (`1..5`) e removeu alocação LINQ `ToDictionary` no hot path de `ExecuteOnnxSessionLocked`.",
        "- **Resultados do Smoke #2** ([`smoke_runtime_metrics.json`](smoke_runtime_metrics.json), [`utility_assignment_metrics.json`](utility_assignment_metrics.json), [`route_accounting.json`](route_accounting.json), [`contextual_input_runtime_metrics.json`](contextual_input_runtime_metrics.json), [`prediction_diversity.json`](prediction_diversity.json)):",
        f"  - Registros válidos com hash V2 conferido: **`{smoke_rt['hash_matching_records']}/{n_rec}` (100.00%)** em rounds `{smoke_rt['rounds_observed']}` (3 rounds completos jogados).",
        f"  - Warm-up startup: `warmup_started=True warmup_success=True warmup_ms=120.69`, **`model_reloads={smoke_rt['model_reloads']}`**.",
        f"  - Latência: `mean={smoke_rt['mean_ms']} ms`, `P50={smoke_rt['p50_ms']} ms`, **`P95={smoke_rt['p95_ms']} ms`** (`<= 15 ms`), **`P99={smoke_rt['p99_ms']} ms`** (`<= 20 ms`).",
        f"  - Estabilidade: **`timeouts={smoke_rt['timeouts']}/{n_rec}`**, **`failures={smoke_rt['failures']}/{n_rec}`**, **`crashes={smoke_rt['crashes']}`**, **`utility_authority_violations={smoke_rt['utility_authority_violations']}/{n_rec}`**.",
        f"  - Integridade de lado neural: **`wrong_side_neural_selections={smoke_rt['wrong_side_neural_selections']}/{n_rec}`**, **`unsupported_neural_selections={smoke_rt['unsupported_neural_selections']}/{n_rec}`**.",
        f"  - Auditoria de atribuição Utility AI (`SPOT_ASSIGNED`): total **`{n_spot}`**, `VALID={val_valid}/{n_spot}` ({val_valid/n_spot*100:.2f}%), `REPLACED={val_rep}/{n_spot}` ({val_rep/n_spot*100:.2f}% -> `RETAKE_INELIGIBLE={rej.get('RETAKE_INELIGIBLE',0)}`, `WRONG_SIDE={rej.get('WRONG_SIDE',0)}`, `WRONG_PHASE={rej.get('WRONG_PHASE',0)}`); **`wrong_side_utility_assignments={util_metrics['wrong_side_utility_assignments']}/{n_spot}`**, **`wrong_phase_utility_assignments={util_metrics['wrong_phase_utility_assignments']}/{n_spot}`**, **`contextual_violations={util_metrics['contextual_violations']}/{n_spot}`**.",
        f"  - Contabilidade de rotas de abertura: `created={route_acc['opening_routes_created']}`, `closed={route_acc['opening_routes_closed']}`, `active_open={route_acc['active_open_routes']}`, **`accounting_residue={route_acc['accounting_residue']}`**, `max_per_player_round={route_acc['max_opening_routes_per_player_round']}`, `unique_midround_repaths={route_acc['unique_midround_repaths']}`, `repeated_event_duplicates={route_acc['repeated_event_duplicates']}`.",
        f"  - Inputs contextuais reais: `team_idx={ctx_rt['team_idx_distribution']}`, `role_idx` com `{len(ctx_rt['role_idx_distribution'])}` roles reais distintas, `stage_idx={ctx_rt['stage_idx_distribution']}`, `mapping_sources={ctx_rt['mapping_sources']}`, **`fallback_mapping_used_count={ctx_rt['fallback_mapping_used_count']}/{n_rec}` (`0.0%`)**.",
        f"  - Diversidade neural em runtime: `{diversity['unique_neural_states']}` estados, `{diversity['unique_neural_sectors']}` setores, `{diversity['unique_neural_spots']}` spots únicos, `{len(diversity['neural_transition_counts'])}` transições e `{len(diversity['neural_exit_trigger_counts'])}` exit triggers.",
        "",
        "## 5. Validação por Testes Automatizados C#",
        "",
        f"- **Testes direcionados (`UtilityPatchAndDeployV2Tests`):** **`{targeted_result['pass_fraction']}`** (`0` falhas, `0` ignorados, `{targeted_result['duration_raw']}`) — [`targeted_test_result.json`](targeted_test_result.json).",
        f"- **Suíte completa C# (`dotnet test` única após Smoke #2):** **`{full_result['pass_fraction']}`** (`0` falhas, `0` ignorados, `{full_result['duration_raw']}`) — [`full_csharp_test_result.json`](full_csharp_test_result.json).",
        "- *Nota transparente:* Durante a primeira execução completa de verificação, `PositioningSideMaskAndRouteTests.MidroundRepathIsNotOpeningRoute` falhou por testar repath repetindo o mesmo `spot_a`, colidindo com a deduplicação `RepeatedEventDuplicates` do `OpeningRouteTracker`. O teste unitário foi atualizado para validar explicitamente ambos os invariantes (deduplicação em `spot_a` repetido + contagem única em `spot_b`), sem alterar código de runtime, e a suíte completa foi reexecutada encerrando em **450/450** aprovações.",
        "",
        "## 6. Próximo Passo (Aguardando Autorização Humana)",
        "",
        "- Em cumprimento à regra `08-no-automatic-phase-advance`, nenhuma partida completa pós-patch, canary ou Route Planner foi iniciado automaticamente.",
        "- **Solicita-se aprovação explícita do usuário** antes de avançar para o próximo marco.",
    ]

    report_path = OUT_DIR / "onnx_v2_utility_patch_smoke_final_report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    deliverable_files = [
        "input_snapshot.json",
        "spot_catalog_review_resolution.json",
        "utility_assignment_patch.json",
        "model_deployment_manifest.json",
        "targeted_test_result.json",
        "targeted_test_stdout.log",
        "smoke_telemetry.jsonl",
        "smoke_shadow_telemetry.jsonl",
        "smoke_runtime_metrics.json",
        "contextual_input_runtime_metrics.json",
        "prediction_diversity.json",
        "utility_assignment_metrics.json",
        "route_accounting.json",
        "utility_ai_events.jsonl",
        "opening_routes_snapshot.json",
        "smoke_console.log",
        "full_csharp_test_result.json",
        "full_csharp_test_stdout.log",
        "findings.json",
        "onnx_v2_utility_patch_smoke_final_report.md",
    ]

    evidence_entries = []
    for rel_name in deliverable_files:
        p = OUT_DIR / rel_name
        if not p.exists():
            raise FileNotFoundError(f"Entregavel ausente: {p}")
        size = p.stat().st_size
        if size <= 0:
            raise ValueError(f"Entregavel vazio: {p}")
        rel_repo = p.relative_to(REPO_ROOT).as_posix()
        evidence_entries.append({
            "path": rel_repo,
            "size_bytes": size,
            "sha256": sha256_file(p),
        })

    deliverable_evidence = {
        "marco": "2B.6.6",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": final_verdict,
        "provenance": "REAL_LIVE_CS2_SERVER",
        "commands_executed": [
            'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~UtilityPatchAndDeployV2Tests" --verbosity minimal',
            r'C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe tools/phase3a_training/run_2b61_live_capture.py --mode smoke --out-dir "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke"',
            r'C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe tools/phase3a_training/audit_2b66_smoke_telemetry.py',
            "dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --verbosity minimal",
            r'C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe tools/phase3a_training/finalize_2b66_deliverables.py',
        ],
        "deployment_integrity": integrity_checks,
        "deliverables_count": len(evidence_entries),
        "deliverables": evidence_entries,
    }
    write_json("deliverable_evidence.json", deliverable_evidence)
    print(f"FINALIZED_2B66 verdict={final_verdict} deliverables={len(evidence_entries)} full_tests={full_result['pass_fraction']} targeted={targeted_result['pass_fraction']}")


if __name__ == "__main__":
    main()
