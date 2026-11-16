---
name: csbot-model-validator
description: Reproduz deterministicamente a avaliação canônica de modelos PyTorch/ONNX do CsBot diretamente a partir de checkpoints e arrays brutos, garantindo invariantes de inferência e tratando classes com support zero como N/A. Use sempre para avaliar modelos, comparar checkpoints ou gerar métricas oficiais de Validation e Test.
---

# CsBot Model Validator

Esta Skill executa a avaliação canônica e determinística de modelos do CsBot diretamente a partir dos checkpoints (`*.pt` / `*.onnx`) e dos arrays/matrizes brutos de avaliação, assegurando conformidade total com `01-evidence-before-claims`, `02-no-test-contamination` e `03-zero-support-is-na`.

## Invariantes Obrigatórias de Avaliação

Toda execução de avaliação canônica deve obedecer estritamente às 6 invariantes abaixo:

1. **Modo de Avaliação Estrito (`model.eval()`)**: Desativa `Dropout` e trava estatísticas de normalização antes de qualquer inferência.
2. **Sem Gradientes (`torch.no_grad()`)**: Execução inteiramente sob `torch.no_grad()` sem mutação de pesos.
3. **Determinismo no Split (`Test` sem Shuffle)`: Avaliação com `shuffle=False` e `drop_last=False`.
4. **Sem Augmentation e Sem Teacher Forcing**: Zero ruído estocástico e zero injeção de ground-truth futuro em passos autoregressivos.
5. **Support Zero Igual a `N/A` (`03-zero-support-is-na`)**: Qualquer classe com `support == 0` no split avaliado recebe estritamente `"N/A"` em `Recall`, `F1-Score`, `Balanced Accuracy` e na linha correspondente de `confusion_normalized.csv`.
6. **Uma Única Métrica Canônica por Split**: Proibido reportar múltiplas variantes filtradas ad-hoc para inflar resultados.

Consulte as fórmulas matemáticas e especificações de schema em [model_eval_invariants.md](./references/model_eval_invariants.md).

## Os 6 Artefatos Canônicos Gerados em `--output-dir`

1. `canonical_eval_manifest.json`: Hashes SHA-256 do checkpoint e entrada, comando executado, split e flags das invariantes verificadas.
2. `canonical_metrics.json`: Métricas globais e por classe com `"N/A"` estrito para `support == 0` e fórmulas explícitas.
3. `confusion_counts.csv`: Matriz de confusão em contagens absolutas inteiras ($C_{i,j}$).
4. `confusion_normalized.csv`: Matriz de confusão normalizada por linha, contendo `"N/A"` nas linhas onde `support == 0`.
5. `calibration.json`: ECE, Brier Score, entropia média e bins de confiabilidade.
6. `checkpoint_comparison.json`: Comparação rastreável entre checkpoints candidatos realizada **exclusivamente sobre `Validation`** (`02-no-test-contamination`).

## Procedimento Operacional

1. Audite previamente o dataset com `csbot-dataset-forensics`.
2. Execute o validador canônico [validate_model_canonical.py](./scripts/validate_model_canonical.py) usando os argumentos canônicos:
   ```powershell
   python .agents/skills/csbot-model-validator/scripts/validate_model_canonical.py `
     --checkpoint-path models/positioning_best.pt `
     --metrics-input-json artifacts/eval/raw_eval_inputs.json `
     --split-name val `
     --output-dir artifacts/eval/canonical_val `
     --strict
   ```
   - **Regra de `--dry-run`**: A execução com `--dry-run` realiza autodiagnóstico não-destrutivo e emite veredito **`CONDITIONAL`** com `data_nature: SIMULATED` (em respeito à Regra `01-evidence-before-claims`, pois `PASS` exige execução real sobre checkpoints e artefatos brutos).
3. Registre os hashes SHA-256 dos 6 artefatos gerados na `phase_evidence_matrix.json`.
