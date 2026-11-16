---
name: csbot-math-logic-auditor
description: Audita a consistência matemática e lógica temporal de avaliações do CsBot, verificando matrizes de confusão, calibração probabilística (ECE e Brier score), invariantes de support zero e transições físicas de estados temporais na FSM do agente. Use sempre para auditar a integridade matemática e lógica de modelos e controladores antes de gates de fase.
---

# CsBot Math & Logic Auditor

Esta Skill implementa a auditoria matemática, estatística e de lógica temporal estipulada em `AGENTS.md` (Regras `01-evidence-before-claims` e `03-zero-support-is-na`) e no contrato de papéis de governança Tier 3/Tier 4 para os subagentes:
1. **Revisor Matemático e Estatístico**: validação estrita de matrizes de confusão, invariantes de linhas e colunas, support zero como `N/A`, métricas macro ponderadas apenas sobre classes ativas, e calibração de probabilidades (ECE - Expected Calibration Error e Brier Score).
2. **Revisor de Lógica Temporal e Máquina de Estados (FSM)**: validação de transições válidas na máquina de estados de tomada de decisão do CS2 e plausibilidade física de durações temporais (ex: planting/defusing de C4, tempo de reação e progressão espacial).

## Invariantes Auditadas

### 1. Invariantes Matemáticas e Estatísticas
- **Soma de Linha vs Support**: Na matriz de contagens absolutas ($C_{i,j}$), $\sum_j C_{i,j} = \text{Support}_i$ para cada classe $i$.
- **Normalização por Linha**: Na matriz normalizada, $\sum_j \hat{C}_{i,j} = 1.0$ (tolerância numérica $\pm 10^{-3}$) para qualquer classe com $\text{Support}_i > 0$.
- **Support Zero como `N/A` (`03-zero-support-is-na`)**: Qualquer classe com $\text{Support}_i = 0$ deve apresentar linha inteira de matriz normalizada preenchida estritamente com `"N/A"` (nunca `0.0`, `0.0%` ou valores interpolados).
- **Métricas Isoladas**: Se $\text{Support}_i = 0$, as métricas `Precision`, `Recall`, `F1-Score` e `Balanced Accuracy` correspondentes devem ser estritamente `"N/A"`.
- **Macro-Averaging sem Suporte Fantasma**: A média macro deve dividir estritamente pelo número de classes com $\text{Support} > 0$.
- **Calibração Determinística**: Cálculo verificado de ECE com $M=10$ bins uniformes em $[0, 1]$ e Brier Score quadrático médio.

### 2. Invariantes de Lógica Temporal e FSM
- **Grafo de Adjacência de Estados**: Toda transição $S_t \to S_{t+1}$ deve pertencer ao grafo permitido da FSM de combate/tática do CS2 (ex: proibido saltar instantaneamente de `SPAWN` para `DEFUSE_C4` sem `NAVIGATE`/`RETAKE`).
- **Plausibilidade Física de Durações**: Ações de longa duração devem respeitar tempos mínimos de motor do CS2:
  - Armar bomba (Plant): tempo contínuo $\ge 3.0$ segundos.
  - Desarmar bomba (Defuse): tempo contínuo $\ge 5.0$ segundos (com kit) ou $\ge 10.0$ segundos (sem kit).

Consulte os contratos matemáticos e de FSM detalhados em [math_logic_audit_contract.md](./references/math_logic_audit_contract.md).

## Scripts Disponíveis

1. `audit_confusion_and_calibration.py`: Auditoria de matrizes de confusão e calibração.
2. `audit_temporal_transitions.py`: Auditoria de transições de estado e durações da FSM.
3. `audit_math_logic.py`: Runner unificado que executa ambas as auditorias e gera relatório consolidado.

## Exemplos de Execução

### Auditoria de Matrizes e Calibração
```powershell
python .agents/skills/csbot-math-logic-auditor/scripts/audit_confusion_and_calibration.py `
  --confusion-counts artifacts/eval/confusion_counts.csv `
  --confusion-normalized artifacts/eval/confusion_normalized.csv `
  --metrics-json artifacts/eval/canonical_metrics.json `
  --output-json artifacts/audit/confusion_calibration_audit.json `
  --strict
```

### Auditoria de Transições Temporais
```powershell
python .agents/skills/csbot-math-logic-auditor/scripts/audit_temporal_transitions.py `
  --transitions-json artifacts/eval/fsm_transitions.json `
  --output-json artifacts/audit/temporal_transitions_audit.json `
  --strict
```

### Autodiagnóstico em Modo `--dry-run`
```powershell
python .agents/skills/csbot-math-logic-auditor/scripts/audit_math_logic.py --dry-run
```
Em conformidade com a Regra `01-evidence-before-claims`, execuções com `--dry-run` emitem veredito máximo **`CONDITIONAL`** e marcam `data_nature: "SIMULATED"`.
