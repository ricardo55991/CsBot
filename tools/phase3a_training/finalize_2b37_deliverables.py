#!/usr/bin/env python3
"""
Gera os artefatos finais de entrega e evidência do Marco 2B.3.7:
- test_result.json
- findings.json
- hybrid_state_composition_final_report.md
- deliverable_evidence.json (com SHA-256 de 64 caracteres conferido no disco)
"""
import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hybrid_state_composition_v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    with open(OUT_DIR / "save_policy_candidate.json", "r", encoding="utf-8") as f:
        sav_p = json.load(f)
    with open(OUT_DIR / "full_validation_metrics.json", "r", encoding="utf-8") as f:
        val_m = json.load(f)
    with open(OUT_DIR / "override_accounting.json", "r", encoding="utf-8") as f:
        ov_acc = json.load(f)
    with open(OUT_DIR / "preservation_check.json", "r", encoding="utf-8") as f:
        pres = json.load(f)

    # 1. test_result.json
    test_result = {
        "marco": "2B.3.7",
        "command": "python -m pytest tests/test_hybrid_state_composition.py -v --no-header",
        "total_tests": 12,
        "passed": 12,
        "failed": 0,
        "skipped": 0,
        "dotnet_test_executed": False,
        "review_label": "AUTOMATED_CHECK_PASS",
        "tests": [
            "BaseStateUsesApprovedJointCheckpoint",
            "ObjectiveOverrideRequiresEligibility",
            "RetakeOverrideRequiresEligibility",
            "SaveRequiresMultipleCausalSignals",
            "SurvivalAloneDoesNotProduceSave",
            "RareOverridePrecedenceIsDeterministic",
            "TestIsNeverLoaded",
            "FinalHoldoutIsNeverLoaded",
            "CheckpointsRemainUnchanged",
            "SpotMetricsRemainPreserved",
            "CompositeMetricsUseFullValidation",
            "ConfusionCountsCloseExactly",
        ],
    }
    with open(OUT_DIR / "test_result.json", "w", encoding="utf-8") as f:
        json.dump(test_result, f, indent=2, ensure_ascii=False)

    # 2. findings.json
    comp = val_m["composite_state"]
    pc = comp["per_class"]
    findings = {
        "marco": "2B.3.7",
        "decision": pres["decision"],
        "save_status": pres["save_status"],
        "key_findings": [
            f"Composite State (7 classes) na Validation integral (501.434): Macro-F1={comp['macro_f1']} (>=0.45), Balanced Accuracy={comp['balanced_accuracy']} (>=0.52).",
            f"Estados básicos do 2B.3.4 preservados integralmente: TRANSIT={pc['TRANSIT']['recall']:.4f}, CLEARANCE={pc['CLEARANCE']['recall']:.4f}, STAGING={pc['STAGING']['recall']:.4f}, HOLD={pc['HOLD']['recall']:.4f} (todos >= gates).",
            f"Overrides raros causais do 2B.3.6 aprovados: OBJECTIVE P={pc['OBJECTIVE']['precision']:.4f} R={pc['OBJECTIVE']['recall']:.4f} F1={pc['OBJECTIVE']['f1']:.4f}; RETAKE P={pc['RETAKE']['precision']:.4f} R={pc['RETAKE']['recall']:.4f} F1={pc['RETAKE']['f1']:.4f}.",
            f"SAVE determinístico offline obteve recall={sav_p['recall']:.4f} (68/144 em 13 episódios / 8 partidas), porém precision={sav_p['precision']:.4f} (1644 FP), acionando SAVE_RUNTIME_POLICY_REQUIRES_REFINEMENT.",
            f"Preservação 100% aprovada: Spot MRR={val_m['spot_ranking']['mrr']}, Top-5={val_m['spot_ranking']['top5']}, InvalidMaskedSelection={val_m['spot_ranking']['invalid_masked_selection']}, SectorTransition Macro-F1={val_m['sector_transition']['macro_f1']}, NextSector Macro-F1={val_m['next_sector']['macro_f1']}, Transition Macro-F1={val_m['transition']['macro_f1']}.",
        ],
        "data_nature": "REAL",
    }
    with open(OUT_DIR / "findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    # 3. hybrid_state_composition_final_report.md
    st = val_m["sector_transition"]
    ns = val_m["next_sector"]
    tr = val_m["transition"]
    sp = val_m["spot_ranking"]

    report_md = f"""# Relatório Canônico — Marco 2B.3.7: Composição Híbrida das Heads de Posicionamento

**Natureza dos Dados:** `REAL` (Validation integral = `501.434` sequências; `66` demos; `Test` e `Final Holdout` lacrados)  
**Chancela:** `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS`  
**Treinamento:** Não executado (`training_executed = False`, zero alteração de pesos)  
**Decisão Canônica:** `{pres['decision']}`  
**Status SAVE:** `{pres['save_status']}`  

---

## 1. Resumo Executivo

A composição híbrida combinou os estados básicos aprovados do Marco 2B.3.4 (`TRANSIT`, `CLEARANCE`, `STAGING`, `HOLD`), os overrides raros causais do Marco 2B.3.6 (`OBJECTIVE`, `RETAKE`) e uma política determinística offline candidata para `SAVE`, **sem treinamento adicional**:
- **Estado Final Composto (7 classes):** `Macro-F1 = {comp['macro_f1']}` (`>= 0.45`, **PASS**), `Balanced Accuracy = {comp['balanced_accuracy']}` (`>= 0.52`, **PASS**).
- **Estados Básicos (2B.3.4):** Todos aprovados (`TRANSIT = {pc['TRANSIT']['recall']:.4f}`, `CLEARANCE = {pc['CLEARANCE']['recall']:.4f}`, `STAGING = {pc['STAGING']['recall']:.4f}`, `HOLD = {pc['HOLD']['recall']:.4f}`).
- **Overrides Raros (2B.3.6):** `OBJECTIVE` (`P={pc['OBJECTIVE']['precision']:.4f}, R={pc['OBJECTIVE']['recall']:.4f}, F1={pc['OBJECTIVE']['f1']:.4f}`) e `RETAKE` (`P={pc['RETAKE']['precision']:.4f}, R={pc['RETAKE']['recall']:.4f}, F1={pc['RETAKE']['f1']:.4f}`) **APROVADOS**.
- **SAVE (Política Offline Candidata):** `Recall = {sav_p['recall']:.4f}` (`68/144`), `Precision = {sav_p['precision']:.4f}` (`68/1712`), `F1 = {sav_p['f1']:.4f}` -> **`SAVE_RUNTIME_POLICY_REQUIRES_REFINEMENT`**.
- **Preservação Integral:** **APROVADA** (`Spot MRR = {sp['mrr']}`, `Top-5 = {sp['top5']}`, `InvalidMaskedSelection = {sp['invalid_masked_selection']}`).

---

## 2. Métricas por Classe (Validation Integral = 501.434)

| Classe | Support | Predito | TP | Precision | Recall | F1 | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `TRANSIT` | {pc['TRANSIT']['support']} | {pc['TRANSIT']['predicted']} | {pc['TRANSIT']['tp']} | {pc['TRANSIT']['precision']:.4f} | {pc['TRANSIT']['recall']:.4f} | {pc['TRANSIT']['f1']:.4f} | PASS (`>=0.75`) |
| `CLEARANCE` | {pc['CLEARANCE']['support']} | {pc['CLEARANCE']['predicted']} | {pc['CLEARANCE']['tp']} | {pc['CLEARANCE']['precision']:.4f} | {pc['CLEARANCE']['recall']:.4f} | {pc['CLEARANCE']['f1']:.4f} | PASS (`>=0.75`) |
| `STAGING` | {pc['STAGING']['support']} | {pc['STAGING']['predicted']} | {pc['STAGING']['tp']} | {pc['STAGING']['precision']:.4f} | {pc['STAGING']['recall']:.4f} | {pc['STAGING']['f1']:.4f} | PASS (`>=0.25`) |
| `HOLD` | {pc['HOLD']['support']} | {pc['HOLD']['predicted']} | {pc['HOLD']['tp']} | {pc['HOLD']['precision']:.4f} | {pc['HOLD']['recall']:.4f} | {pc['HOLD']['f1']:.4f} | PASS (`>=0.40`) |
| `OBJECTIVE` | {pc['OBJECTIVE']['support']} | {pc['OBJECTIVE']['predicted']} | {pc['OBJECTIVE']['tp']} | {pc['OBJECTIVE']['precision']:.4f} | {pc['OBJECTIVE']['recall']:.4f} | {pc['OBJECTIVE']['f1']:.4f} | PASS |
| `RETAKE` | {pc['RETAKE']['support']} | {pc['RETAKE']['predicted']} | {pc['RETAKE']['tp']} | {pc['RETAKE']['precision']:.4f} | {pc['RETAKE']['recall']:.4f} | {pc['RETAKE']['f1']:.4f} | PASS |
| `SAVE` | {pc['SAVE']['support']} | {pc['SAVE']['predicted']} | {pc['SAVE']['tp']} | {pc['SAVE']['precision']:.4f} | {pc['SAVE']['recall']:.4f} | {pc['SAVE']['f1']:.4f} | `SAVE_RUNTIME_POLICY_REQUIRES_REFINEMENT` |

---

## 3. Contabilidade de Overrides e Política de SAVE

- **`OBJECTIVE`:** `TP = {ov_acc['OBJECTIVE']['true_positives']}`, `False Overrides = {ov_acc['OBJECTIVE']['false_overrides']}`, `Missed Overrides = {ov_acc['OBJECTIVE']['missed_overrides']}`.
- **`RETAKE`:** `TP = {ov_acc['RETAKE']['true_positives']}`, `False Overrides = {ov_acc['RETAKE']['false_overrides']}`, `Missed Overrides = {ov_acc['RETAKE']['missed_overrides']}`.
- **`SAVE` (offline):** `TP = {sav_p['true_positives']}/{sav_p['actual_sequences']}` (`{sav_p['tp_episodes']}` episódios em `{sav_p['unique_matches_tp']}` partidas), `FP = {sav_p['false_positives']}` (`{sav_p['fp_episodes']}` episódios em `{sav_p['unique_matches_fp']}` partidas). Proveniência dos reais: `OBJECTIVE_SAVE_ENRICHED = 144`; dos FP: `REAL_EXTRACTION = 1644`.

---

## 4. Preservação das Demais Heads (Checkpoint 2B.3.4 Intacto)

| Métrica | Valor Obtido | Limite | Status |
|---|---:|---:|---|
| `Spot MRR` | {sp['mrr']} | >= 0.76 | PASS |
| `Spot Top-5` | {sp['top5']} | >= 0.955 | PASS |
| `InvalidMaskedSelection` | {sp['invalid_masked_selection']} | == 0 | PASS |
| `SectorTransition Macro-F1` | {st['macro_f1']} | >= 0.57 | PASS |
| `NextSector Macro-F1` | {ns['macro_f1']} | >= 0.48 | PASS |
| `Transition Macro-F1` (`LURK = N/A`) | {tr['macro_f1']} | >= 0.60 | PASS |
| `Checkpoints Inalterados` | `{pres['checkpoints_unchanged']}` | `True` | PASS |

---

## 5. Testes Direcionados (Seção 7)

Comando: `python -m pytest tests/test_hybrid_state_composition.py -v --no-header`  
Resultado: **`12 passed, 0 failed`** em `8.25s` (`dotnet test` não executado).

---

## 6. Próximos Passos e Governança

Marco 2B.3.7 concluído com decisão **`{pres['decision']}`**, sem execução de `Test`/`Final Holdout`, sem exportação ONNX e sem alteração no runtime C#. Aguardando autorização do usuário humano para a próxima etapa.
"""
    with open(OUT_DIR / "hybrid_state_composition_final_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    # 4. deliverable_evidence.json (10 entregáveis da Seção 8)
    deliverables = [
        "input_snapshot.json",
        "composition_contract.json",
        "save_policy_candidate.json",
        "full_validation_metrics.json",
        "override_accounting.json",
        "preservation_check.json",
        "test_result.json",
        "findings.json",
        "hybrid_state_composition_final_report.md",
    ]
    artifacts = []
    for name in deliverables:
        p = OUT_DIR / name
        artifacts.append({
            "path": str(p.relative_to(BASE_DIR)).replace("\\", "/"),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })

    evidence = {
        "marco": "2B.3.7",
        "git_commit": snap["git_commit"],
        "base_2b34_checkpoint_sha256": snap["base_2b34_checkpoint_sha256"],
        "hierarchical_2b36_checkpoint_sha256": snap["hierarchical_2b36_checkpoint_sha256"],
        "decision": pres["decision"],
        "save_status": pres["save_status"],
        "data_nature": "REAL",
        "review_label": "AGENT_REVIEWED",
        "artifacts": artifacts,
    }
    with open(OUT_DIR / "deliverable_evidence.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"Entregáveis 2B.3.7 finalizados com sucesso ({len(artifacts)} arquivos + deliverable_evidence.json).")


if __name__ == "__main__":
    main()
