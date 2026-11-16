# Math & Logic Audit Contract

Este documento formaliza as especificações matemáticas, estatísticas e lógicas para auditorias executadas pela skill `csbot-math-logic-auditor`, em estrita observância às regras `01-evidence-before-claims` e `03-zero-support-is-na` de `AGENTS.md`.

---

## 1. Contrato Matemático e Estatístico (Confusion Matrix & Calibration)

### 1.1 Invariantes de Matriz de Confusão

Seja $\mathcal{C} = \{1, \dots, K\}$ o conjunto de classes do modelo (ex: estados táticos ou spots).
Seja $C \in \mathbb{N}^{K \times K}$ a matriz de contagens absolutas onde $C_{i,j}$ é o número de amostras com ground-truth $i$ preditas como $j$.

1. **Definição de Support**:
   $$\text{Support}_i = \sum_{j=1}^K C_{i,j}$$
2. **Normalização por Linha**:
   Para qualquer classe $i$ onde $\text{Support}_i > 0$:
   $$\hat{C}_{i,j} = \frac{C_{i,j}}{\text{Support}_i}, \quad \sum_{j=1}^K \hat{C}_{i,j} = 1.0 \pm 10^{-3}$$
3. **Invariante de Support Zero (`03-zero-support-is-na`)**:
   Para qualquer classe $i$ onde $\text{Support}_i = 0$:
   - A linha normalizada inteira deve conter exclusivamente `"N/A"`, isto é:
     $$\forall j \in \{1, \dots, K\}, \quad \hat{C}_{i,j} = \text{"N/A"}$$
   - É expressamente proibido preencher com $0.0$, $0.0\%$, médias de coluna ou interpolações.

### 1.2 Invariantes de Métricas Derivadas

Para cada classe $i \in \mathcal{C}$:
- $\text{TP}_i = C_{i,i}$
- $\text{FP}_i = \sum_{k \neq i} C_{k,i}$
- $\text{FN}_i = \sum_{k \neq i} C_{i,k}$

Se $\text{Support}_i > 0$:
- $\text{Recall}_i = \frac{\text{TP}_i}{\text{Support}_i}$
- $\text{Precision}_i = \frac{\text{TP}_i}{\text{TP}_i + \text{FP}_i}$ (se $\text{TP}_i + \text{FP}_i > 0$ senão $0.0$)
- $\text{F1}_i = 2 \cdot \frac{\text{Precision}_i \cdot \text{Recall}_i}{\text{Precision}_i + \text{Recall}_i}$ (se $\text{Precision}_i + \text{Recall}_i > 0$ senão $0.0$)

Se $\text{Support}_i = 0$:
- $\text{Recall}_i = \text{"N/A"}$
- $\text{Precision}_i = \text{"N/A"}$
- $\text{F1}_i = \text{"N/A"}$
- $\text{Balanced Accuracy}_i = \text{"N/A"}$

### 1.3 Macro-Médias Estritas
Seja $\mathcal{C}_{\text{active}} = \{i \in \mathcal{C} \mid \text{Support}_i > 0\}$. O cálculo de médias macro deve utilizar estritamente $|\mathcal{C}_{\text{active}}|$ no denominador:
$$\text{Macro-F1} = \frac{1}{|\mathcal{C}_{\text{active}}|} \sum_{i \in \mathcal{C}_{\text{active}}} \text{F1}_i$$

### 1.4 Calibração Probabilística
1. **Expected Calibration Error (ECE)**:
   Dividindo o intervalo de confiança $[0, 1]$ em $M=10$ bins uniformes $B_m = \left(\frac{m-1}{M}, \frac{m}{M}\right]$:
   $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
2. **Brier Score Multiclasse**:
   $$\text{Brier} = \frac{1}{N} \sum_{n=1}^N \sum_{k=1}^K (p_{n,k} - y_{n,k})^2$$

---

## 2. Contrato de Lógica Temporal e FSM (Finite State Machine)

### 2.1 Grafo Canônico de Estados do CsBot
Os estados autorizados para o controlador tático no CS2 são:
1. `SPAWN`: Spawn inicial do round ou congelamento de freeze time.
2. `NAVIGATE`: Movimentação e deslocamento pelo mapa.
3. `HOLD_ANGLE`: Marcação estática de mira ou spot de camp.
4. `SEARCH`: Busca ativa de oponentes ou exploração de área.
5. `ENGAGE_COMBAT`: Engajamento de tiro direto contra oponente visível.
6. `PLANT_C4`: Execução da ação contínua de plant da bomba (exclusivo Terroristas).
7. `DEFUSE_C4`: Execução da ação contínua de defuse da bomba (exclusivo Contra-Terroristas).
8. `RETAKE`: Posicionamento coordenado para retomada de bombsite.
9. `POST_ROUND`: Fim de round, vitória ou eliminação.

### 2.2 Transições Proibidas (Adversariais / Bugs de Lógica)
- `SPAWN` $\to$ `PLANT_C4` (impossível armar bomba no instante do spawn sem navegar até o bombsite).
- `SPAWN` $\to$ `DEFUSE_C4` (impossível defusar bomba no instante do spawn).
- `HOLD_ANGLE` $\to$ `DEFUSE_C4` (sem aproximação/navegação ao bombsite).
- `ENGAGE_COMBAT` $\to$ `PLANT_C4` (impossível armar a bomba enquanto atira simultaneamente).

### 2.3 Invariantes de Tempo de Motor (CS2 Engine Timings)
- **Duração Mínima de Plant**: $t_{\text{plant}} \ge 3.0\text{ s}$ contínuos sem interrupção.
- **Duração Mínima de Defuse com Kit**: $t_{\text{defuse}} \ge 5.0\text{ s}$ contínuos.
- **Duração Mínima de Defuse sem Kit**: $t_{\text{defuse}} \ge 10.0\text{ s}$ contínuos.

---

## 3. Schema de Saída JSON

Todo script da skill `csbot-math-logic-auditor` emite arquivo JSON com o seguinte schema canônico:

```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "2026-11-07T21:30:00.000000+00:00",
  "dry_run": false,
  "data_nature": "REAL",
  "verdict": "PASS",
  "violations_count": 0,
  "violations": [],
  "details": {
    "total_classes_evaluated": 9,
    "active_classes_count": 8,
    "zero_support_classes_count": 1,
    "confusion_matrix_row_sum_verified": true,
    "zero_support_na_verified": true,
    "macro_f1_calculated": 0.884,
    "ece_calculated": 0.032,
    "brier_score_calculated": 0.115
  }
}
```
