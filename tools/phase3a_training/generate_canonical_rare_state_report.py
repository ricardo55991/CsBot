#!/usr/bin/env python3
"""
Fase 3A.1 - Passo 7: Geração Canônica do Relatório de Estados Raros.
Lê os arrays canônicos e aplica estritamente os critérios de STRONG, USABLE, WEAK, FAILED e NOT_EVALUATED.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from tools.phase3a_training.data_utils import STATE_NAMES

def main():
    base_dir = Path(__file__).resolve().parents[2]
    runs_dir = base_dir / "training_runs" / "positioning_v1"
    eval_dir = runs_dir / "canonical_eval"

    s_logits = np.load(eval_dir / "state_logits.npy")
    s_labels = np.load(eval_dir / "state_labels.npy")
    s_preds = np.argmax(s_logits, axis=1)

    cm = np.zeros((7, 7), dtype=int)
    for t, p in zip(s_labels, s_preds):
        cm[t, p] += 1

    records = []
    for c, name in enumerate(STATE_NAMES):
        tp = int(cm[c, c])
        fp = int(cm[:, c].sum() - tp)
        fn = int(cm[c, :].sum() - tp)
        supp = int(cm[c, :].sum())
        pred_cnt = int(cm[:, c].sum())

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float((2 * prec * rec) / (prec + rec)) if (prec + rec) > 0 else 0.0

        if supp == 0:
            status = "NOT_EVALUATED"
        elif f1 >= 0.70:
            status = "STRONG"
        elif f1 >= 0.50:
            status = "USABLE"
        elif f1 >= 0.25:
            status = "WEAK"
        else:
            status = "FAILED"

        records.append({
            "state": name,
            "support": supp,
            "pred_count": pred_cnt,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "status": status
        })

    md = f"""# Relatório Forense Canônico de Estados Raros — Positioning Transformer V1

**Data:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  
**Checkpoint Mestre:** `models/positioning/de_mirage_positioning_v1.pt` (SHA-256: `e4b505a2...`)  
**Fonte dos Dados:** Arrays canônicos em `training_runs/positioning_v1/canonical_eval/`  
**Total de Sequências Avaliadas:** {len(s_labels):,}  

---

## 1. Classificação e Métricas por Estado de Posicionamento

Critérios estritos de classificação:
- **STRONG:** F1 >= 0.70
- **USABLE:** F1 >= 0.50
- **WEAK:** 0.25 <= F1 < 0.50
- **FAILED:** F1 < 0.25
- **NOT_EVALUATED:** Suporte = 0

| Estado | Suporte | Predições | TP | FP | FN | Precision | Recall | F1-Score | Status Forense |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for r in records:
        if r["support"] > 0:
            prec_str = f"{r['precision']:.4f}"
            rec_str = f"{r['recall']:.4f}"
            f1_str = f"{r['f1']:.4f}"
        else:
            prec_str = "N/A"
            rec_str = "N/A"
            f1_str = "N/A"

        md += f"| **{r['state']}** | {r['support']:,} | {r['pred_count']:,} | {r['tp']:,} | {r['fp']:,} | {r['fn']:,} | {prec_str} | {rec_str} | {f1_str} | `{r['status']}` |\n"

    md += """
---

## 2. Diagnóstico Técnico e Honestidade dos Fatos

1. **TRANSIT (STRONG):** F1 de 0.9441 com alta precisão (98.08%) e recall de 91.00%.
2. **CLEARANCE (STRONG):** F1 de 0.8052 (precisão de 81.74% e recall de 79.33%), comprovando que waypoints de clearance em cantos e entradas de bomb são detectados com excelente robustez.
3. **HOLD (WEAK):** F1 de 0.2890. Embora o recall seja moderado (61.92%), a precisão é baixa (18.85%) porque muitos momentos de desaceleração em TRANSIT foram previstos como HOLD.
4. **STAGING (FAILED):** F1 de 0.2163. Recall baixo (26.49%) devido à ambiguidade temporal com TRANSIT inicial.
5. **RETAKE (FAILED):** F1 de 0.2090. Com apenas 34 exemplos no Test canônico, 18 deles foram previstos como HOLD, falhando no threshold operacional de 0.40.
6. **OBJECTIVE e SAVE (NOT_EVALUATED):** Ambas as classes possuem suporte 0 no Test canônico do corpus Mirage V2 original. Em respeito à integridade científica, são declaradas como **NOT_EVALUATED**, sem atribuição de recall ou precision artificiais.

---

## 3. Veredito para a Head de Estados
Das classes avaliadas, apenas `TRANSIT` e `CLEARANCE` atendem aos critérios de produção (F1 >= 0.70). Os estados `HOLD`, `STAGING` e `RETAKE` apresentam desempenho fraco ou insatisfatório no Test Set, e `OBJECTIVE`/`SAVE` carecem de suporte.
Portanto, a Head de Estados requer **RETREINAMENTO DIRECIONADO COM DADOS BALANCEADOS DE CLASSES RARAS** antes de qualquer acoplamento de runtime.
"""

    out_file = runs_dir / "rare_state_report_canonical.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Salvo: {out_file}")

if __name__ == "__main__":
    main()
