# Regra 02: No Test Contamination (`02-no-test-contamination`)

Os conjuntos `Test` e `Holdout Final` são estritamente reservados para avaliação canônica final e **não podem participar** de:
- Treinamento direto ou indireto;
- Escolha de época ou seleção de checkpoint (`best_checkpoint`);
- Seleção entre experimentos, hiperparâmetros ou seeds;
- Calibração de probabilidades, dropout ou temperatura;
- Definição ou ajuste de thresholds operacionais;
- Tuning de pesos de loss ou curriculum;
- Escolha de arquitetura, cabeças (heads) ou features.

> **Exceção e Liberação Condicional Canônica**:
> O conjunto `Test` pode ser referenciado e executado **exclusivamente** quando TODAS as seguintes condições forem verdadeiras simultaneamente:
> 1. `mode = FINAL_EVALUATION`;
> 2. `checkpoint_frozen = true`;
> 3. `config_frozen = true`;
> 4. `thresholds_frozen = true`.
>
> **Regra de Bloqueio**: O hook `pre-training-gate` abortará qualquer comando de treinamento, fit, fine-tuning ou busca de hiperparâmetros se houver tentativa de uso do split `Test`. Qualquer violação invalida imediatamente a avaliação final e exige descarte do experimento.
