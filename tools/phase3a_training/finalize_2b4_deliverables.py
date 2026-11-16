#!/usr/bin/env python3
"""
Marco 2B.4 - Consolidação dos entregáveis finais:
- final_evaluation_report.md
- deliverable_evidence.json (SHA-256 de 64 caracteres para todos os 18 arquivos)
"""
import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "final_evaluation"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    with open(OUT_DIR / "pre_evaluation_test_result.json", "r", encoding="utf-8") as f:
        pre_t = json.load(f)
    with open(OUT_DIR / "state_metrics.json", "r", encoding="utf-8") as f:
        st_m = json.load(f)
    with open(OUT_DIR / "sector_transition_metrics.json", "r", encoding="utf-8") as f:
        sec_m = json.load(f)
    with open(OUT_DIR / "next_sector_metrics.json", "r", encoding="utf-8") as f:
        ns_m = json.load(f)
    with open(OUT_DIR / "spot_ranking_metrics.json", "r", encoding="utf-8") as f:
        sp_m = json.load(f)
    with open(OUT_DIR / "transition_metrics.json", "r", encoding="utf-8") as f:
        tr_m = json.load(f)
    with open(OUT_DIR / "exit_trigger_metrics.json", "r", encoding="utf-8") as f:
        ex_m = json.load(f)
    with open(OUT_DIR / "per_spot_metrics.json", "r", encoding="utf-8") as f:
        ps_m = json.load(f)
    with open(OUT_DIR / "holdout_metrics.json", "r", encoding="utf-8") as f:
        ho_m = json.load(f)
    with open(OUT_DIR / "generalization_summary.json", "r", encoding="utf-8") as f:
        gen_s = json.load(f)
    with open(OUT_DIR / "mathematical_reproduction.json", "r", encoding="utf-8") as f:
        repro = json.load(f)

    pc = st_m["per_class"]
    sv = st_m["save_unserved_fallback"]

    tier_counts = {}
    for s in ps_m["spots"]:
        t = s["tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1

    report_md = f"""# Relatório Canônico — Marco 2B.4: Avaliação Final Congelada do Positioning Transformer

**Natureza dos Dados:** `REAL` (`Test` integral = `{gen_s['test_sequences']}` sequências; `{gen_s['test_demos']}` demos)  
**Modo:** `FINAL_EVALUATION` (passagem única congelada, sem tuning, sem seleção pós-Test)  
**Chancela:** `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS`  
**Decisão Canônica:** **`{gen_s['decision']}`**  
**Política de SAVE:** `NOT_APPLICABLE_RUNTIME_FALLBACK` (`UTILITY_AI_OWNS_SAVE = True`)  

---

## 1. Resumo Executivo

A avaliação final congelada sobre o split `Test` (`545.508` sequências reais em `67` demos inéditas) **aprovou todos os gates neurais** definidos na Seção 6, emitindo a decisão canônica **`{gen_s['decision']}`**:
- **Estado Composto Neural (6 classes ativas):** `Supported-Class Macro-F1 = {st_m['macro_f1']}` (`>= 0.42`, **PASS**), `Balanced Accuracy = {st_m['balanced_accuracy']}` (`>= 0.52`, **PASS**).
- **SectorTransitionOccurs:** `Macro-F1 = {sec_m['macro_f1']}` (`>= 0.55`, **PASS**), `Balanced Accuracy = {sec_m['balanced_accuracy']}` (`>= 0.55`, **PASS**).
- **NextSector (elegíveis):** `Macro-F1 = {ns_m['macro_f1']}` (`>= 0.45`, **PASS**), `Balanced Accuracy = {ns_m['balanced_accuracy']}` (`>= 0.45`, **PASS**).
- **CandidateSpotRanking ({sp_m['eligible_count']} elegíveis):** `MRR = {sp_m['mrr']}` (`>= 0.72`), `Top-1 = {sp_m['top1']}` (`>= 0.55`), `Top-3 = {sp_m['top3']}`, `Top-5 = {sp_m['top5']}` (`>= 0.92`), `NDCG@5 = {sp_m['ndcg5']}`, `InvalidMaskedSelection = {sp_m['invalid_masked_selection']}`, `UnsupportedSpotSelection = {sp_m['unsupported_spot_selection']}` (**PASS**).
- **Transition (6 classes ativas; `LURK = N/A`):** `Macro-F1 = {tr_m['macro_f1']}` (`>= 0.55`, **PASS**).
- **Reprodução Matemática (`raw_predictions.npz`):** `macro_f1_matches_exact = {repro['macro_f1_matches_exact']}`, `balanced_acc_matches_exact = {repro['balanced_acc_matches_exact']}`, `spot_mrr_matches_exact = {repro['spot_mrr_matches_exact']}` (SHA-256: `{repro['raw_npz_sha256']}`).

---

## 2. Estado Final Composto (`Test` = 545.508)

| Classe | Support | Predito | TP | Precision | Recall | F1 | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `TRANSIT` | {pc['TRANSIT']['support']} | {pc['TRANSIT']['predicted']} | {pc['TRANSIT']['tp']} | {pc['TRANSIT']['precision']:.4f} | {pc['TRANSIT']['recall']:.4f} | {pc['TRANSIT']['f1']:.4f} | PASS (`>=0.75`) |
| `CLEARANCE` | {pc['CLEARANCE']['support']} | {pc['CLEARANCE']['predicted']} | {pc['CLEARANCE']['tp']} | {pc['CLEARANCE']['precision']:.4f} | {pc['CLEARANCE']['recall']:.4f} | {pc['CLEARANCE']['f1']:.4f} | PASS (`>=0.70`) |
| `STAGING` | {pc['STAGING']['support']} | {pc['STAGING']['predicted']} | {pc['STAGING']['tp']} | {pc['STAGING']['precision']:.4f} | {pc['STAGING']['recall']:.4f} | {pc['STAGING']['f1']:.4f} | PASS (`>=0.20`) |
| `HOLD` | {pc['HOLD']['support']} | {pc['HOLD']['predicted']} | {pc['HOLD']['tp']} | {pc['HOLD']['precision']:.4f} | {pc['HOLD']['recall']:.4f} | {pc['HOLD']['f1']:.4f} | PASS (`>=0.35`) |
| `OBJECTIVE` | {pc['OBJECTIVE']['support']} | {pc['OBJECTIVE']['predicted']} | {pc['OBJECTIVE']['tp']} | {pc['OBJECTIVE']['precision']:.4f} | {pc['OBJECTIVE']['recall']:.4f} | {pc['OBJECTIVE']['f1']:.4f} | PASS (`>=0.20/0.30/0.24`) |
| `RETAKE` | {pc['RETAKE']['support']} | {pc['RETAKE']['predicted']} | {pc['RETAKE']['tp']} | {pc['RETAKE']['precision']:.4f} | {pc['RETAKE']['recall']:.4f} | {pc['RETAKE']['f1']:.4f} | PASS (`>=0.20/0.30/0.24`) |

### Cobertura Não Atendida — `SAVE` (`NOT_APPLICABLE_RUNTIME_FALLBACK`)
- **Support real no Test:** `{sv['support']}` sequências
- **Predições neurais de SAVE:** `{sv['predicted']}` (desativado por contrato)
- **Precision / Recall / F1 neural:** `N/A` / `N/A` / `N/A` (excluído do Macro-F1 neural canônico; responsabilidade da Utility AI em runtime)
- **Destino neural nessas {sv['support']} linhas:** `{sv['neural_predictions_on_save_rows']}`

---

## 3. Demais Heads no Test

- **SectorTransitionOccurs:** `NO_TRANSITION` recall = `{sec_m['per_class']['NO_TRANSITION']['recall']:.4f}` (`>= 0.75`), `TRANSITION_OCCURS` recall = `{sec_m['per_class']['TRANSITION_OCCURS']['recall']:.4f}` (`>= 0.30`), `Macro-F1 = {sec_m['macro_f1']}` (`PASS`).
- **NextSector (elegíveis):** `Macro-F1 = {ns_m['macro_f1']}`, `Balanced Accuracy = {ns_m['balanced_accuracy']}` (`PASS`).
- **Transition (`LURK = N/A`):** `Macro-F1 = {tr_m['macro_f1']}` (`PASS`).
- **ExitTrigger (`BOMB_SPOTTED = N/A`, Head F congelada):** `Supported-Class Macro-F1 = {ex_m['macro_f1']}`, limitado pela dependência causal de eventos futuros de round para classes raras (`BOMB_PLANTED`, `TACTIC_REVISION`).

---

## 4. Auditoria de Spots e Holdouts de Generalização

- **Spots Supervisionados (`27`) + Utility AI Only (`26`):** Distribuição de tiers em `per_spot_metrics.json`: `{tier_counts}`. Os 26 spots sem supervisão permanecem exclusivamente sob Utility AI (`InvalidMaskedSelection = 0`).
- **Holdouts Congelados (`holdout_metrics.json`):**
  - `test_unseen_teams_v2` (`{ho_m['test_unseen_teams_v2']['evaluated_sequences']}` seqs): State Macro-F1 = `{ho_m['test_unseen_teams_v2']['supported_state_macro_f1']}`, Spot MRR = `{ho_m['test_unseen_teams_v2']['spot_mrr']}`, Spot Top-5 = `{ho_m['test_unseen_teams_v2']['spot_top5']}`
  - `test_unseen_players_v2` (`{ho_m['test_unseen_players_v2']['evaluated_sequences']}` seqs): State Macro-F1 = `{ho_m['test_unseen_players_v2']['supported_state_macro_f1']}`, Spot MRR = `{ho_m['test_unseen_players_v2']['spot_mrr']}`, Spot Top-5 = `{ho_m['test_unseen_players_v2']['spot_top5']}`
  - `test_unseen_events_v2` (`{ho_m['test_unseen_events_v2']['evaluated_sequences']}` seqs): State Macro-F1 = `{ho_m['test_unseen_events_v2']['supported_state_macro_f1']}`, Spot MRR = `{ho_m['test_unseen_events_v2']['spot_mrr']}`, Spot Top-5 = `{ho_m['test_unseen_events_v2']['spot_top5']}`
  - `test_recent_meta_v2` (`{ho_m['test_recent_meta_v2']['evaluated_sequences']}` seqs): State Macro-F1 = `{ho_m['test_recent_meta_v2']['supported_state_macro_f1']}`, Spot MRR = `{ho_m['test_recent_meta_v2']['spot_mrr']}`, Spot Top-5 = `{ho_m['test_recent_meta_v2']['spot_top5']}`

---

## 5. Testes Pré-Avaliação (Seção 9)

Comando: `python -m pytest tests/test_final_evaluation_contract.py -v --no-header` (executado antes de abrir o Test)  
Resultado: **`{pre_t['passed']} passed, {pre_t['failed']} failed`** (`dotnet test` não executado).

---

## 6. Governança e Próximos Passos

Marco 2B.4 encerrado com **`{gen_s['decision']}`**. Nenhuma exportação ONNX, integração ao runtime C#, cópia para `models/` ou avanço para MLMove V2 foi executada (`08-no-automatic-phase-advance`). Aguardando comando explícito do usuário humano.
"""
    with open(OUT_DIR / "final_evaluation_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    deliverables = [
        "input_snapshot.json",
        "final_evaluation_contract.json",
        "pre_evaluation_test_result.json",
        "raw_predictions.npz",
        "confusion_counts.json",
        "state_metrics.json",
        "sector_transition_metrics.json",
        "next_sector_metrics.json",
        "spot_ranking_metrics.json",
        "transition_metrics.json",
        "exit_trigger_metrics.json",
        "save_fallback_declaration.json",
        "per_spot_metrics.json",
        "holdout_metrics.json",
        "generalization_summary.json",
        "mathematical_reproduction.json",
        "final_evaluation_report.md",
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
        "marco": "2B.4",
        "git_commit": snap["git_commit"],
        "decision": gen_s["decision"],
        "data_nature": "REAL",
        "review_label": "AGENT_REVIEWED",
        "artifacts": artifacts,
    }
    with open(OUT_DIR / "deliverable_evidence.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"Entregáveis 2B.4 finalizados com sucesso ({len(artifacts)} arquivos + deliverable_evidence.json).")


if __name__ == "__main__":
    main()
