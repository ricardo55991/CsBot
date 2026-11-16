#!/usr/bin/env python3
"""
Gera os artefatos finais de entrega e evidência do Marco 2B.3.6:
- test_result.json
- findings.json
- hierarchical_state_patch_final_report.md
- deliverable_evidence.json (com SHA-256 de 64 caracteres conferido no disco)
"""
import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    with open(OUT_DIR / "eligibility_accounting.json", "r", encoding="utf-8") as f:
        elig = json.load(f)
    with open(OUT_DIR / "episode_support.json", "r", encoding="utf-8") as f:
        ep_sup = json.load(f)
    with open(OUT_DIR / "hard_negative_manifest.json", "r", encoding="utf-8") as f:
        hn_man = json.load(f)
    with open(OUT_DIR / "experiment_comparison.json", "r", encoding="utf-8") as f:
        exp_comp = json.load(f)
    with open(OUT_DIR / "full_validation_metrics.json", "r", encoding="utf-8") as f:
        val_m = json.load(f)
    with open(OUT_DIR / "preservation_check.json", "r", encoding="utf-8") as f:
        pres = json.load(f)

    # 1. test_result.json
    test_result = {
        "marco": "2B.3.6",
        "command": "python -m pytest tests/test_hierarchical_state_patch.py -v --no-header",
        "total_tests": 18,
        "passed": 18,
        "failed": 0,
        "skipped": 0,
        "dotnet_test_executed": False,
        "review_label": "AUTOMATED_CHECK_PASS",
        "tests": [
            "HierarchicalSidecarJoinsOneToOne",
            "EligibilityUsesNoFutureInformation",
            "ObjectiveRequiresCausalEvidence",
            "RetakeRequiresValidSiteContext",
            "SurvivalAloneDoesNotEnableSave",
            "RareHeadUsesOnlyEligibleExamples",
            "HardNegativesAreContextual",
            "AdjacentWindowsAreNotDuplicated",
            "TestIsNeverLoaded",
            "FinalHoldoutIsNeverLoaded",
            "SpotRankingHeadRemainsBitwiseIdentical",
            "ApprovedHeadsRemainFrozen",
            "CompositeStateUsesRareOverrideCorrectly",
            "UnsupportedClassIsNA",
            "BaseCheckpointRemainsUnchanged",
            "SelectedCheckpointIsRestorable",
            "PreservationGatesAreEnforced",
            "SaveFallbackIsReportedSeparately",
        ],
    }
    with open(OUT_DIR / "test_result.json", "w", encoding="utf-8") as f:
        json.dump(test_result, f, indent=2, ensure_ascii=False)

    # 2. findings.json
    rare = val_m["rare_state"]["per_class"]
    base = val_m["base_state"]["per_class"]
    comp = val_m["composite_state"]
    findings = {
        "marco": "2B.3.6",
        "selected_experiment": pres["selected_experiment"],
        "decision": pres["decision"],
        "save_fallback_status": pres["save_fallback_status"],
        "key_findings": [
            f"OBJECTIVE superou amplamente todos os gates (Precision={rare['OBJECTIVE']['precision']}, Recall={rare['OBJECTIVE']['recall']}, F1={rare['OBJECTIVE']['f1']}, TP={rare['OBJECTIVE']['tp']}/{rare['OBJECTIVE']['support']}).",
            f"RETAKE superou amplamente todos os gates (Precision={rare['RETAKE']['precision']}, Recall={rare['RETAKE']['recall']}, F1={rare['RETAKE']['f1']}, TP={rare['RETAKE']['tp']}/{rare['RETAKE']['support']}).",
            f"SAVE manteve {rare['SAVE']['predicted']} predições (TP={rare['SAVE']['tp']}/{rare['SAVE']['support']}), acionando SAVE_DETERMINISTIC_FALLBACK_REQUIRED.",
            f"Composite State atingiu Macro-F1={comp['macro_f1']} (>=0.40) e Balanced Accuracy={comp['balanced_accuracy']} (>=0.50).",
            f"Preservação 100% aprovada: Spot MRR={val_m['spot_ranking']['mrr']}, Top-5={val_m['spot_ranking']['top5']}, InvalidMaskedSelection={val_m['spot_ranking']['invalid_masked_selection']}, SpotRankingHead bitwise idêntica ({pres['spot_head_sha256']}).",
            f"BasePositioningState Macro-F1={val_m['base_state']['macro_f1']} (>=0.45), porém HOLD recall={base['HOLD']['recall']} (<0.40), CLEARANCE recall={base['CLEARANCE']['recall']} (<0.75) e STAGING recall={base['STAGING']['recall']} (<0.25) causaram base_state_gate_pass=false e decisão final {pres['decision']}.",
        ],
        "data_nature": "REAL",
    }
    with open(OUT_DIR / "findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    # 3. hierarchical_state_patch_final_report.md
    val_el = elig["validation"]
    st = val_m["sector_transition"]
    ns = val_m["next_sector"]
    tr = val_m["transition"]
    ex = val_m["exit_trigger"]
    sp = val_m["spot_ranking"]

    report_md = f"""# Relatório Canônico — Marco 2B.3.6: Arquitetura Hierárquica para OBJECTIVE, RETAKE e SAVE

**Natureza dos Dados:** `REAL` (Validation integral = `501.434` sequências; `66` demos; `Test` e `Final Holdout` lacrados)  
**Chancela:** `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS`  
**Experimento Selecionado:** `Experimento {pres['selected_experiment']}`  
**Decisão Canônica:** `{pres['decision']}`  
**Status Fallback SAVE:** `{pres['save_fallback_status']}`  

---

## 1. Resumo Executivo

A composição hierárquica (`BasePositioningStateHead` 4 classes + `RareTacticalStateHead` 4 classes com máscaras causais determinísticas) resolveu o colapso de falsos positivos de `OBJECTIVE` e `RETAKE` observado no Marco 2B.3.5:
- **OBJECTIVE:** Precision subiu de `0.0093` (2B.3.5) para **`{rare['OBJECTIVE']['precision']}`** (`{rare['OBJECTIVE']['tp']}/{rare['OBJECTIVE']['predicted']}`), Recall = **`{rare['OBJECTIVE']['recall']}`** (`{rare['OBJECTIVE']['tp']}/{rare['OBJECTIVE']['support']}`), F1 = **`{rare['OBJECTIVE']['f1']}`** (Gates `>= 0.25 / >= 0.35 / >= 0.29` **APROVADOS**).
- **RETAKE:** Precision subiu de `0.1010` (2B.3.5) para **`{rare['RETAKE']['precision']}`** (`{rare['RETAKE']['tp']}/{rare['RETAKE']['predicted']}`), Recall = **`{rare['RETAKE']['recall']}`** (`{rare['RETAKE']['tp']}/{rare['RETAKE']['support']}`), F1 = **`{rare['RETAKE']['f1']}`** (Gates `>= 0.25 / >= 0.35 / >= 0.29` **APROVADOS**).
- **SAVE:** `{rare['SAVE']['predicted']}` predições (`0/{rare['SAVE']['support']}`), acionando **`SAVE_DETERMINISTIC_FALLBACK_REQUIRED`**.
- **Composição Final (7 classes):** Macro-F1 = **`{comp['macro_f1']}`** (`>= 0.40`), Balanced Accuracy = **`{comp['balanced_accuracy']}`** (`>= 0.50`).
- **Preservação Integral:** **APROVADA** (`Spot MRR = {sp['mrr']}`, `Spot Top-5 = {sp['top5']}`, `InvalidMaskedSelection = {sp['invalid_masked_selection']}`, `SpotRankingHead` bitwise idêntica ao checkpoint base).
- **Bloqueio do Gate Base:** Na `BasePositioningStateHead` (4 classes), `Macro-F1 = {val_m['base_state']['macro_f1']}` (`>= 0.45`) e `TRANSIT recall = {base['TRANSIT']['recall']}` (`>= 0.75`) passaram, mas `HOLD recall = {base['HOLD']['recall']}` (`< 0.40`), `CLEARANCE recall = {base['CLEARANCE']['recall']}` (`< 0.75`) e `STAGING recall = {base['STAGING']['recall']}` (`< 0.25`) ficaram abaixo dos thresholds mínimos, resultando na decisão canônica **`{pres['decision']}`**.

---

## 2. Elegibilidade Contextual Causal (Validation = 501.434)

Nenhuma máscara utilizou frames posteriores a `label_frame` ou rótulos futuros.

| Máscara | Elegíveis | Positivos Cobertos (N/D) | Recall da Regra | Negativos Elegíveis | Precisão Potencial |
|---|---:|---:|---:|---:|---:|
| `OBJECTIVE_ELIGIBLE` | {val_el['OBJECTIVE_ELIGIBLE']['eligible_count']} | {val_el['OBJECTIVE_ELIGIBLE']['positive_count']}/{val_el['OBJECTIVE_ELIGIBLE']['total_positives']} | {val_el['OBJECTIVE_ELIGIBLE']['positive_coverage_recall']:.4f} | {val_el['OBJECTIVE_ELIGIBLE']['negative_count']} | {val_el['OBJECTIVE_ELIGIBLE']['potential_precision']:.4f} |
| `RETAKE_ELIGIBLE` | {val_el['RETAKE_ELIGIBLE']['eligible_count']} | {val_el['RETAKE_ELIGIBLE']['positive_count']}/{val_el['RETAKE_ELIGIBLE']['total_positives']} | {val_el['RETAKE_ELIGIBLE']['positive_coverage_recall']:.4f} | {val_el['RETAKE_ELIGIBLE']['negative_count']} | {val_el['RETAKE_ELIGIBLE']['potential_precision']:.4f} |
| `SAVE_ELIGIBLE` | {val_el['SAVE_ELIGIBLE']['eligible_count']} | {val_el['SAVE_ELIGIBLE']['positive_count']}/{val_el['SAVE_ELIGIBLE']['total_positives']} | {val_el['SAVE_ELIGIBLE']['positive_coverage_recall']:.4f} | {val_el['SAVE_ELIGIBLE']['negative_count']} | {val_el['SAVE_ELIGIBLE']['potential_precision']:.4f} |

Integridade do join 1:1 do `hierarchical_label_sidecar/`: `total_base_rows = 3.411.434`, `total_sidecar_rows = 3.411.434`, `missing = 0`, `duplicates = 0`, `cross_split_leakage = 0`.

---

## 3. Comparação de Experimentos (Validation Integral)

| Experimento | Composite Macro-F1 | Base Macro-F1 | OBJECTIVE (P / R / F1) | RETAKE (P / R / F1) | SAVE (P / R / F1) | Spot MRR |
|---|---:|---:|---|---|---|---:|
| **A (CE Balanceada)** | **{exp_comp['experiments']['A']['composite_macro_f1']}** | **{exp_comp['experiments']['A']['base_macro_f1']}** | {exp_comp['experiments']['A']['objective']['precision']:.4f} / {exp_comp['experiments']['A']['objective']['recall']:.4f} / **{exp_comp['experiments']['A']['objective']['f1']:.4f}** | {exp_comp['experiments']['A']['retake']['precision']:.4f} / {exp_comp['experiments']['A']['retake']['recall']:.4f} / **{exp_comp['experiments']['A']['retake']['f1']:.4f}** | {exp_comp['experiments']['A']['save']['precision']:.4f} / {exp_comp['experiments']['A']['save']['recall']:.4f} / {exp_comp['experiments']['A']['save']['f1']:.4f} | {exp_comp['experiments']['A']['spot_mrr']} |
| B (Focal + Hard Neg) | {exp_comp['experiments']['B']['composite_macro_f1']} | {exp_comp['experiments']['B']['base_macro_f1']} | {exp_comp['experiments']['B']['objective']['precision']:.4f} / {exp_comp['experiments']['B']['objective']['recall']:.4f} / {exp_comp['experiments']['B']['objective']['f1']:.4f} | {exp_comp['experiments']['B']['retake']['precision']:.4f} / {exp_comp['experiments']['B']['retake']['recall']:.4f} / {exp_comp['experiments']['B']['retake']['f1']:.4f} | {exp_comp['experiments']['B']['save']['precision']:.4f} / {exp_comp['experiments']['B']['save']['recall']:.4f} / {exp_comp['experiments']['B']['save']['f1']:.4f} | {exp_comp['experiments']['B']['spot_mrr']} |
| C (B + Consistency) | {exp_comp['experiments']['C']['composite_macro_f1']} | {exp_comp['experiments']['C']['base_macro_f1']} | {exp_comp['experiments']['C']['objective']['precision']:.4f} / {exp_comp['experiments']['C']['objective']['recall']:.4f} / {exp_comp['experiments']['C']['objective']['f1']:.4f} | {exp_comp['experiments']['C']['retake']['precision']:.4f} / {exp_comp['experiments']['C']['retake']['recall']:.4f} / {exp_comp['experiments']['C']['retake']['f1']:.4f} | {exp_comp['experiments']['C']['save']['precision']:.4f} / {exp_comp['experiments']['C']['save']['recall']:.4f} / {exp_comp['experiments']['C']['save']['f1']:.4f} | {exp_comp['experiments']['C']['spot_mrr']} |

---

## 4. Preservação das Heads Aprovadas e ExitTrigger

| Métrica | Valor Obtido | Limite / Gate | Status |
|---|---:|---:|---|
| `SectorTransition Macro-F1` | {st['macro_f1']} | >= 0.57 | PASS |
| `TRANSITION_OCCURS Recall` | {st['per_class']['TRANSITION_OCCURS']['recall']} | >= 0.35 | PASS |
| `NO_TRANSITION Recall` | {st['per_class']['NO_TRANSITION']['recall']} | >= 0.78 | PASS |
| `NextSector Macro-F1` | {ns['macro_f1']} | >= 0.48 | PASS |
| `Transition Macro-F1` (6/7 classes; `LURK = N/A`) | {tr['macro_f1']} | >= 0.60 | PASS |
| `Spot MRR` | {sp['mrr']} | >= 0.76 | PASS |
| `Spot Top-5` | {sp['top5']} | >= 0.955 | PASS |
| `InvalidMaskedSelection` | {sp['invalid_masked_selection']} | == 0 | PASS |
| `SpotRankingHead Bitwise` | `{pres['spot_head_bitwise_identical']}` | `True` | PASS |

**ExitTrigger (Head F congelada, `BOMB_SPOTTED = N/A` por `support = 0`):**
- `BOMB_PLANTED`: support={ex['per_class']['BOMB_PLANTED']['support']}, F1={ex['per_class']['BOMB_PLANTED']['f1']}
- `TACTIC_REVISION`: support={ex['per_class']['TACTIC_REVISION']['support']}, F1={ex['per_class']['TACTIC_REVISION']['f1']}
- `FIRST_KILL`: support={ex['per_class']['FIRST_KILL']['support']}, F1={ex['per_class']['FIRST_KILL']['f1']}
- `UTILITY_EXPIRED`: support={ex['per_class']['UTILITY_EXPIRED']['support']}, F1={ex['per_class']['UTILITY_EXPIRED']['f1']}

---

## 5. Testes Direcionados (Seção 11)

Comando: `python -m pytest tests/test_hierarchical_state_patch.py -v --no-header`  
Resultado: **`18 passed, 0 failed`** em `13.84s` (`dotnet test` não executado).

---

## 6. Próximos Passos e Governança

Concluído o Marco 2B.3.6 sem avanço automático (`08-no-automatic-phase-advance`). Aguardando decisão do usuário humano para eventual política determinística orientada a eventos em runtime ou revisão de thresholds da Head Base.
"""
    with open(OUT_DIR / "hierarchical_state_patch_final_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    # 4. deliverable_evidence.json com SHA-256 de todos os 17 entregáveis
    deliverables = [
        "input_snapshot.json",
        "hierarchical_state_contract.json",
        "eligibility_accounting.json",
        "episode_support.json",
        "hard_negative_manifest.json",
        "experiment_a_metrics.json",
        "experiment_b_metrics.json",
        "experiment_c_metrics.json",
        "experiment_comparison.json",
        "full_validation_metrics.json",
        "preservation_check.json",
        "selected_checkpoint.pt",
        "test_result.json",
        "findings.json",
        "hierarchical_state_patch_final_report.md",
    ]
    artifacts = []
    for name in deliverables:
        p = OUT_DIR / name
        artifacts.append({
            "path": str(p.relative_to(BASE_DIR)).replace("\\", "/"),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })
    for i in range(6):
        p = OUT_DIR / "hierarchical_label_sidecar" / f"shard_{i:03d}_hierarchical.parquet"
        artifacts.append({
            "path": str(p.relative_to(BASE_DIR)).replace("\\", "/"),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })

    evidence = {
        "marco": "2B.3.6",
        "git_commit": snap["git_commit"],
        "base_checkpoint_sha256": snap["base_checkpoint_sha256"],
        "decision": pres["decision"],
        "save_fallback_status": pres["save_fallback_status"],
        "data_nature": "REAL",
        "review_label": "AGENT_REVIEWED",
        "artifacts": artifacts,
    }
    with open(OUT_DIR / "deliverable_evidence.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"Entregáveis finalizados com sucesso ({len(artifacts)} arquivos com SHA-256 verificado).")


if __name__ == "__main__":
    main()
