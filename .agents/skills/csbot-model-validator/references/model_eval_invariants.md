# Invariantes Matemáticas e Schemas de Avaliação de Modelos (`csbot-model-validator`)

Este documento define as fórmulas exatas, regras de tratamento de `support = 0` e contratos dos 6 arquivos produzidos pela avaliação canônica do `csbot-model-validator`.

---

## 1. Tratamento Matemático de Classes com `support = 0` (`03-zero-support-is-na`)

Seja $K$ o número total de classes no contrato do modelo e $S_k = \sum_{j=1}^{K} C_{k,j}$ o suporte real (contagem de amostras ground-truth) da classe $k$ no split avaliado.

1. **Conjunto de Classes com Suporte Válido**:
   $$\mathcal{K}_{\text{valid}} = \{ k \in \{1, \dots, K\} \mid S_k > 0 \}$$
2. **Métricas por Classe quando $S_k = 0$**:
   - $\text{Recall}_k = \text{"N/A"}$
   - $\text{F1}_k = \text{"N/A"}$
   - $\text{Precision}_k = \text{"N/A"}$ se $\sum_{i=1}^K C_{i,k} = 0$, caso contrário $0.0$ (com registro explícito de falsos positivos sobre classe ausente: `fp_on_zero_support_class`).
3. **Métricas Agregadas Macro (Balanced Accuracy / Macro-F1)**:
   - Calculadas exclusivamente sobre $\mathcal{K}_{\text{valid}}$, reportando obrigatoriamente:
     - `num_total_classes`: $K$
     - `num_valid_support_classes`: $|\mathcal{K}_{\text{valid}}|$
     - `zero_support_classes`: lista nominal das classes com $S_k = 0$
   - É **estritamente proibido** atribuir $0.0$ ou $1.0$ para classes em $\{1, \dots, K\} \setminus \mathcal{K}_{\text{valid}}$ e dividir por $K$.

---

## 2. Especificação dos 6 Artefatos Obrigatórios

### 2.1 `canonical_eval_manifest.json`
```json
{
  "timestamp_utc": "2026-11-07T16:10:00Z",
  "split_name": "val",
  "checkpoint_path": "models/positioning_v2.pt",
  "checkpoint_sha256": "64_hex_chars...",
  "dataset_path": "data/splits/val_positioning.npz",
  "dataset_sha256": "64_hex_chars...",
  "command": "python .agents/skills/csbot-model-validator/scripts/validate_model_canonical.py ...",
  "invariants_enforced": {
    "model_eval_mode": true,
    "torch_no_grad": true,
    "shuffle_disabled": true,
    "augmentation_disabled": true,
    "teacher_forcing_disabled": true,
    "zero_support_as_na": true
  },
  "data_nature": "REAL"
}
```

### 2.2 `canonical_metrics.json`
Deve conter:
- `total_samples`: inteiro exato ($N$)
- `overall_accuracy`: `{"value": float, "numerator": int, "denominator": int, "formula": "correct / total_samples"}`
- `balanced_accuracy_valid_classes`: `{"value": float, "valid_classes_count": int, "total_classes_count": int, "formula": "mean(recall_k for k with support > 0)"}`
- `macro_f1_valid_classes`: `{"value": float, "valid_classes_count": int, "total_classes_count": int}`
- `per_class_metrics`: dicionário indexado por `class_id` contendo `support`, `tp`, `fp`, `fn`, `precision`, `recall` (`float` ou `"N/A"`), `f1` (`float` ou `"N/A"`).

### 2.3 `confusion_counts.csv`
- Cabeçalho: `true_class,pred_0,pred_1,...,pred_K`
- Valores: inteiros não-negativos.
- Invariante: $\sum_{i,j} C_{i,j} == N$ (`total_samples`).

### 2.4 `confusion_normalized.csv`
- Cabeçalho idêntico ao `confusion_counts.csv`.
- Para toda linha $i$ com $S_i > 0$: célula $(i, j)$ formatada com 6 casas decimais representando $C_{i,j} / S_i$, com $\sum_j (C_{i,j}/S_i) = 1.0 \pm 10^{-5}$.
- Para toda linha $i$ com $S_i == 0$: todas as células da linha $i$ devem conter exatamente a string `N/A`.

### 2.5 `calibration.json`
- `ece` (Expected Calibration Error com $M=15$ bins)
- `brier_score`
- `mean_confidence`
- `mean_entropy`
- `bins`: lista com `bin_lower`, `bin_upper`, `count`, `avg_confidence`, `avg_accuracy`.

### 2.6 `checkpoint_comparison.json`
- Registra a comparação entre candidatos para seleção do `best_checkpoint`.
- **Invariante de Bloqueio (`02-no-test-contamination`)**: O campo `"selection_split"` em `checkpoint_comparison.json` deve ser estritamente `"val"` (ou `"validation"`). Se `"selection_split"` for `"test"`, o validador deve abortar e emitir `FAIL`.
