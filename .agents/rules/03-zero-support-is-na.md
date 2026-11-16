# Regra 03: Zero Support is N/A (`03-zero-support-is-na`)

Qualquer classe, estado, setor ou spot que apresente `support = 0` no split avaliado deve ser reportado exclusivamente como **`N/A`**.

Para qualquer classe com `support = 0`, **é estritamente proibido calcular, exibir como número ou incluir em médias globais sem ressalva**:
- `Recall` (é estritamente proibido exibir `0.0%`, `100.0%` ou qualquer float);
- `F1-Score` (nunca substituir `0/0` por `0.0` ou `1.0`);
- `Balanced Accuracy` sobre classes ausentes;
- Percentual normalizado de linha na matriz de confusão (`confusion_normalized.csv`).

> **Regras de Bloqueio**:
> 1. Macro-médias devem explicitar o denominador de classes ativas: ex: `Macro-F1 = 0.7845 (sobre 3 de 5 classes com suporte > 0; classes raras N/A)`.
> 2. Substituir `0 / 0` por número, preencher classes ausentes copiando de outros splits ou mascarar silenciosamente o suporte zero invalida metodologicamente o relatório e resulta em veredito `FAIL`.
