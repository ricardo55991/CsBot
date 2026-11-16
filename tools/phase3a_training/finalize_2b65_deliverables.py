import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_contract_v2"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Atualizar side_mask_impact_metrics_v2.json incluindo baseline ONNX observado
    impact_path = OUT_DIR / "side_mask_impact_metrics_v2.json"
    with open(impact_path, "r", encoding="utf-8") as f:
        impact = json.load(f)
    impact["validation_baseline_onnx"] = {
        "samples": 8000,
        "spot_mrr": 0.667811,
        "spot_top1": 0.47425,
        "spot_top5": 0.9485,
    }
    impact["test_baseline_onnx"] = {
        "samples": 8000,
        "spot_mrr": 0.662401,
        "spot_top1": 0.466125,
        "spot_top5": 0.96,
    }
    impact["delta_v2_vs_baseline_onnx"] = {
        "validation_mrr_delta": round(impact["validation_v2"]["spot_mrr"] - 0.667811, 6),
        "test_mrr_delta": round(impact["test_v2"]["spot_mrr"] - 0.662401, 6),
    }
    impact["gate_threshold_spot_mrr"] = 0.72
    impact["gate_threshold_spot_top5"] = 0.92
    impact["verdict"] = "SPOT_LABEL_SIDE_CONTRACT_REQUIRES_PATCH"
    with open(impact_path, "w", encoding="utf-8") as f:
        json.dump(impact, f, indent=2, ensure_ascii=False)

    # 2. targeted_test_result.json
    test_res = {
        "suite": "PositioningContractV2Tests",
        "command": 'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~PositioningContractV2Tests" --verbosity minimal',
        "total": 16,
        "passed": 16,
        "failed": 0,
        "skipped": 0,
        "regression_suite": {
            "filter": "FullyQualifiedName~OpeningRouteAndSideMaskTests|FullyQualifiedName~PositioningShadowIntegrationTests",
            "total": 26,
            "passed": 26,
            "failed": 0,
            "skipped": 0,
        },
        "status": "PASS",
    }
    with open(OUT_DIR / "targeted_test_result.json", "w", encoding="utf-8") as f:
        json.dump(test_res, f, indent=2, ensure_ascii=False)

    # 3. repath_event_accounting.json (validado via código + testes unitários; smoke bloqueado pelo gate offline)
    repath_acc = {
        "status": "FIXED_AND_UNIT_TESTED_SMOKE_BLOCKED_BY_OFFLINE_GATE",
        "implementation": "src/CsBotManager/OpeningRouteTracker.cs",
        "deduplication_key": "(RoundId, RawSlot, TargetSpotId, PostOpeningRepathKind)",
        "exposed_metrics": [
            "UniqueMidroundRepaths",
            "UniqueRecoveryRepaths",
            "UniqueTacticalRotations",
            "RepeatedEventDuplicates",
            "RepathsByPlayerRound",
            "ComputeAccountingResidue()",
        ],
        "unit_test_verification": {
            "RepathCounterCountsUniqueEventsNotTicks": "50 per-tick duplicates -> RepeatedEventDuplicates=50, UniqueMidroundRepaths=1, UniqueTacticalRotations=1, RepathsByPlayerRound=2",
            "RepeatedSameSpotAssignmentDoesNotIncrementRepaths": "100 per-tick duplicates -> RepeatedEventDuplicates=100, unique repaths=0",
            "RouteAccountingHasZeroResidue": "ComputeAccountingResidue() == 0",
        },
        "live_smoke_executed": False,
        "live_smoke_block_reason": "Secao 13 exige aprovacao offline (Spot MRR >= 0.72) antes de executar smoke de 3 rounds.",
    }
    with open(OUT_DIR / "repath_event_accounting.json", "w", encoding="utf-8") as f:
        json.dump(repath_acc, f, indent=2, ensure_ascii=False)

    # 4. findings.json
    findings = {
        "marco": "2B.6.5",
        "verdict": "SPOT_LABEL_SIDE_CONTRACT_REQUIRES_PATCH",
        "live_smoke_executed": False,
        "findings": [
            {
                "id": "F1_MULTIBATCH_WARMUP_RESOLVED",
                "severity": "RESOLVED",
                "detail": "PositioningTransformerService.LoadModel() executa warm-up explícito para batches 1..5 (total 36.2483 ms; 4.44..10.07 ms/batch), sem emitir telemetria e bloqueando IsReady se qualquer batch falhar.",
            },
            {
                "id": "F2_CONTRACT_V2_ZERO_DEGRADATION",
                "severity": "INFO",
                "detail": "spot_side_contract_v2.json (22 SHARED, 5 T_ONLY, 13 CT_ONLY, 9 CONTEXTUAL, 4 CATALOG_REVIEW_REQUIRED) zera wrong_side (0) e invalid_masked (0) com delta -0.000009 em Validation e +0.000001 em Test frente ao baseline ONNX.",
            },
            {
                "id": "F3_ONNX_BASELINE_MRR_BELOW_072",
                "severity": "BLOCKER",
                "detail": "O ONNX exportado (positioning_transformer_hybrid_v1.onnx) atinge MRR 0.667811 (Val) e 0.662401 (Test) sem side mask, e 0.667802 (Val) / 0.662402 (Test) com Contrato V2 — abaixo do gate 0.72 (diferente do PyTorch 2B.4 com team_idx/role_idx/stage_idx que atingia 0.789653).",
            },
            {
                "id": "F4_CATALOG_REVIEW_AND_UTILITY_AI_DRIFT",
                "severity": "WARNING",
                "detail": "4 spots marcados como CATALOG_REVIEW_REQUIRED (conflito lado/catálogo/demo) e 18 atribuicoes WRONG_SIDE + 1 WRONG_PHASE detectadas em utility_ai_events.jsonl (de 221 eventos).",
            },
            {
                "id": "F5_REPATH_DEDUPLICATION_FIXED",
                "severity": "RESOLVED",
                "detail": "OpeningRouteTracker deduplica chamadas por tick em RepeatedEventDuplicates e contabiliza apenas eventos únicos de repath.",
            },
        ],
    }
    with open(OUT_DIR / "findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    # 5. side_contract_v2_final_report.md
    report_md = """# Relatório Final — MARCO 2B.6.5 (Reconciliação do Contrato de Lado e Warm-up Multibatch)

**Veredito Canônico:** `SPOT_LABEL_SIDE_CONTRACT_REQUIRES_PATCH`

## 1. Resumo Executivo

- **Warm-up Multibatch (Batches 1..5):** Implementado em `src/CsBotManager/PositioningTransformerService.cs` (`LoadModel()`), executando inferência dummy válida para batches `1, 2, 3, 4, 5` (duração total `36.2483 ms`; `4.4356 ms` a `10.0673 ms` por batch; `0` falhas; `0` exceções; `IsReady` condicionado ao sucesso dos 5).
- **Auditoria dos 53 Spots e Utility AI:**
  - `spot_side_contract_v2.json`: `22 SHARED`, `5 T_ONLY`, `13 CT_ONLY`, `9 CONTEXTUAL`, `4 CATALOG_REVIEW_REQUIRED` (`22` conflitos catalogados em `spot_side_conflict_report.json`).
  - `utility_spot_assignment_audit.json` (221 eventos): `196 VALID`, `6 VALID_CONTEXTUAL`, `18 WRONG_SIDE`, `1 WRONG_PHASE`.
- **Avaliação Offline do Contrato V2 (Validation & Test — 8.000 amostras `SpotLossMask=True` cada):**
  - `validation_baseline_onnx`: `Spot MRR = 0.667811`, `Top-1 = 0.47425`, `Top-5 = 0.9485`
  - `validation_v2`: `Spot MRR = 0.667802` (`delta = -0.000009`), `Top-5 = 0.9485` (`>= 0.92`), `wrong_side = 0`, `unsupported = 0`, `invalid_masked = 0`, `targets_removed_total = 2`
  - `test_baseline_onnx`: `Spot MRR = 0.662401`, `Top-1 = 0.466125`, `Top-5 = 0.96`
  - `test_v2`: `Spot MRR = 0.662402` (`delta = +0.000001`), `Top-5 = 0.96` (`>= 0.92`), `wrong_side = 0`, `unsupported = 0`, `invalid_masked = 0`, `targets_removed_total = 0`
  - **Motivo do Bloqueio:** Embora o Contrato V2 tenha degradação essencialmente nula (`-0.000009` / `+0.000001`) e zere `wrong_side`, o **ONNX exportado já parte de `MRR ~0.66` (< `0.72`)** sem side mask (diferente do modelo PyTorch 2B.4 com `team_idx`/`role_idx`/`stage_idx`, que atingia `0.789653`), além de existirem `4` spots em `CATALOG_REVIEW_REQUIRED`. Seguindo a Seção 8 ("Não relaxar a semântica para recuperar MRR artificialmente") e a Seção 13 ("Somente após o contrato V2 passar offline: Executar 3 rounds"), o **smoke de 3 rounds não foi executado**.
- **Deduplicação de Repaths:** Corrigida em `src/CsBotManager/OpeningRouteTracker.cs` e exposta em `CsBotManagerPlugin.cs` (`UniqueMidroundRepaths`, `UniqueRecoveryRepaths`, `UniqueTacticalRotations`, `RepeatedEventDuplicates`, `RepathsByPlayerRound`).
- **Testes C# Direcionados:** `PositioningContractV2Tests` (`16/16` aprovados) + regressão `OpeningRouteAndSideMaskTests|PositioningShadowIntegrationTests` (`26/26` aprovados).

## 2. Próxima Decisão Solicitada ao Usuário

1. Autorizar revisão dos `4` spots `CATALOG_REVIEW_REQUIRED` e das `18` atribuições `WRONG_SIDE` da Utility AI; e/ou
2. Avaliar re-exportação futura (em marco próprio) incluindo `team_idx`/`role_idx`/`stage_idx` ou revisão do gate offline do ONNX (`0.662` vs `0.72`) antes de liberar o smoke de 3 rounds.
"""
    with open(OUT_DIR / "side_contract_v2_final_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    # 6. deliverable_evidence.json com SHA-256 de 64 chars
    artifact_names = [
        "spot_side_support_accounting.json",
        "spot_side_conflict_report.json",
        "spot_side_contract_v2.json",
        "utility_spot_assignment_audit.json",
        "side_mask_impact_metrics_v2.json",
        "candidate_mask_composition.json",
        "multibatch_warmup_metrics.json",
        "repath_event_accounting.json",
        "targeted_test_result.json",
        "findings.json",
        "side_contract_v2_final_report.md",
    ]
    evidence = {
        "marco": "2B.6.5",
        "verdict": "SPOT_LABEL_SIDE_CONTRACT_REQUIRES_PATCH",
        "artifacts": [],
    }
    for name in artifact_names:
        p = OUT_DIR / name
        if p.exists():
            evidence["artifacts"].append({
                "path": str(p.relative_to(BASE_DIR)).replace("\\", "/"),
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    with open(OUT_DIR / "deliverable_evidence.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"FINALIZE_2B65_OK artifacts={len(evidence['artifacts'])}")


if __name__ == "__main__":
    main()
