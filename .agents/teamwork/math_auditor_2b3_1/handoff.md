# Handoff Report — Auditoria Matemática e Estatística (Fase 3A.3-B, Marco 2B.3)

**Agente**: `math_auditor_2b3_1` (Mathematical and Statistical Auditor)  
**Data/Hora**: 2026-11-08T22:06:00Z  
**Diretório de Trabalho**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\math_auditor_2b3_1`  
**Destinatário**: Orchestrator (`5aa571f6-be49-4f7f-baff-92e5c3c7ec1a`)  
**Veredito Canônico**: `PASS_MATHEMATICAL_INTEGRITY_CONDITIONAL_TARGETS` (Mapeado como `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL` conforme Seção 19 do `ORIGINAL_REQUEST.md`)

---

## 1. Observation

Durante a auditoria matemática e estatística independente do Marco 2B.3 (`training_runs/positioning_v2_real_temporal/full_training/`), foram inspecionados, recalculados e verificados os seguintes artefatos brutos no disco:

### 1.1 Artefatos Auditados e Hashes SHA-256 Verificados no Disco
- `training_runs/positioning_v2_real_temporal/full_training/frozen_composite_formula.json`: `8e344ad4ae452b4733d2941737f61f87c292114af7c0fb7a9c9acdc8b38c1bf3`
- `training_runs/positioning_v2_real_temporal/full_training/three_seed_comparison.json`: `4096a8626fb8c347b0fff21703dd86a327af85573c6f672a7a03b8095b0685e5`
- `training_runs/positioning_v2_real_temporal/full_training/best_model_selection.json`: `457035fa3943e37f7f6859b4498deffd5b9deaa19f711c20e56b46adc8bcaa44`
- `training_runs/positioning_v2_real_temporal/full_training/baseline_comparison.json`: `1b8270d4539007c4cf0cb0ecfd716985ba59e6086ef46345dd2b3a49e567fa9a`
- `training_runs/positioning_v2_real_temporal/full_training/collapse_monitoring.json`: `0ba1020c5c6dde09527d63831c5f1c4742b6e582eefa5fe35ab5f6255a15f7e1`
- `training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt`: `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`
- `training_runs/positioning_v2_real_temporal/full_training/seed_42028/best_checkpoint.pt`: `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`
- `training_runs/positioning_v2_real_temporal/full_training/mathematical_training_audit.json`: `b14cbc74f2859840273be9e763625d14b26466e5e8aac0402e4299f8120ba8ab` (materializado pelo auditor independente).

### 1.2 Recálculo Determinístico das Matrizes de Confusão e Métricas
Execução independente através de `.agents/teamwork/math_auditor_2b3_1/audit_mathematical_integrity.py` contra as 5.120 amostras do split de Validation (66 demos canônicas):

#### Seed 42026 (Melhor Época: 8)
- `State Macro-F1`: 0.2289 (7 classes ativas) | `Balanced Acc`: 0.2318
- `SectorTransition Macro-F1`: 0.4649 (2 classes ativas) | `Balanced Acc`: 0.5000
- `NextSector Macro-F1`: 0.3149 (5 classes ativas, 671 amostras elegíveis) | `Balanced Acc`: 0.3196
- `Spot MRR`: 0.7694 (472 amostras elegíveis)
- `Transition Macro-F1`: 0.5670 (6 classes ativas) | `Balanced Acc`: 0.5622
- `ExitTrigger Macro-F1`: 0.2658 (6 classes ativas) | `Balanced Acc`: 0.2692
- **CompositeScore Recalculado**:
  0.20 * 0.2289 + 0.10 * 0.4649 + 0.10 * 0.3149 + 0.25 * 0.7694 + 0.20 * 0.5670 + 0.15 * 0.2658 = 0.4694

#### Seed 42027 (Melhor Época: 8)
- `State Macro-F1`: 0.2343 (7 classes ativas) | `Balanced Acc`: 0.2504
- `SectorTransition Macro-F1`: 0.4649 (2 classes ativas) | `Balanced Acc`: 0.5000
- `NextSector Macro-F1`: 0.2525 (5 classes ativas, 671 amostras elegíveis) | `Balanced Acc`: 0.2846
- `Spot MRR`: 0.7538 (472 amostras elegíveis)
- `Transition Macro-F1`: 0.5718 (6 classes ativas) | `Balanced Acc`: 0.5817
- `ExitTrigger Macro-F1`: 0.2725 (6 classes ativas) | `Balanced Acc`: 0.2900
- **CompositeScore Recalculado**:
  0.20 * 0.2343 + 0.10 * 0.4649 + 0.10 * 0.2525 + 0.25 * 0.7538 + 0.20 * 0.5718 + 0.15 * 0.2725 = 0.4623

#### Seed 42028 (Melhor Época: 6) — Candidato Vencedor Selecionado
- `State Macro-F1`: 0.2250 (7 classes ativas) | `Balanced Acc`: 0.2397
- `SectorTransition Macro-F1`: 0.4649 (2 classes ativas) | `Balanced Acc`: 0.5000
- `NextSector Macro-F1`: 0.3652 (5 classes ativas, 671 amostras elegíveis) | `Balanced Acc`: 0.3558
- `Spot MRR`: 0.7604 (Top-1: 62.29%, Top-3: 88.35%, Top-5: 95.55%, NDCG@5: 0.8123)
- `Transition Macro-F1`: 0.5637 (6 classes ativas) | `Balanced Acc`: 0.5684
- `ExitTrigger Macro-F1`: 0.2613 (6 classes ativas) | `Balanced Acc`: 0.2756
- **CompositeScore Recalculado**:
  0.20 * 0.2250 + 0.10 * 0.4649 + 0.10 * 0.3652 + 0.25 * 0.7604 + 0.20 * 0.5637 + 0.15 * 0.2613 = 0.4700

### 1.3 Classes sem Suporte no Split de Validação (Regra 03)
Conforme verificado em `support_validation.json` e `confusion_counts_validation.json`, as seguintes classes possuem suporte nulo e foram estritamente rotuladas como `N/A`:

| Classe | Support | Precision | Recall | F1-Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Transition: LURK` | 0 | N/A | N/A | N/A | N/A |
| `ExitTrigger: BOMB_SPOTTED` | 0 | N/A | N/A | N/A | N/A |
| `ExitTrigger: TACTIC_REVISION` | 0 | N/A | N/A | N/A | N/A |
| `Spot: 26 spots mascarados` | 0 | N/A | N/A | N/A | N/A |

### 1.4 Reconciliação Estatística das Três Seeds
- `CompositeScore`: Scores = `[0.4694, 0.4623, 0.4700]`, Média = `0.4672`, Desvio Padrão = `0.0035`, Amplitude = `0.0077` (Mín: 0.4623, Máx: 0.4700).
- `NextSector Macro-F1`: Média = `0.3109`, Desvio Padrão = `0.0461`.
- `Spot MRR`: Média = `0.7612`, Desvio Padrão = `0.0064`.
- `Transition Macro-F1`: Média = `0.5675`, Desvio Padrão = `0.0033`.
- `ExitTrigger Macro-F1`: Média = `0.2665`, Desvio Padrão = `0.0046`.

### 1.5 Suíte de Testes Automatizados Executada
1. `pytest tests/test_phase3a3_b_milestone2b3_full_training.py -v`:
   - Resultado: 22 passed em 22 testes descobertos (22/22 PASS).
2. `pytest tests/test_phase3a3_b_milestone2b2_label_patch.py tests/test_phase3a3_b_milestone2b1_full_index.py -v`:
   - Resultado: 40 passed em 40 testes descobertos (40/40 PASS).

---

## 2. Logic Chain

1. **Observação 1.1 e 1.2 → Integridade da Fórmula Congelada**: A fórmula de CompositeScore registrada em `frozen_composite_formula.json` possui pesos com soma exata de 1.00 (`0.20 + 0.10 + 0.10 + 0.25 + 0.20 + 0.15 = 1.00`). O recálculo determinístico termo a termo das 3 seeds conferiu com precisão de 4 casas decimais em 100% dos casos.
2. **Observação 1.2 e 1.4 → Ótimo Canônico e Seleção da Seed 42028**: Entre as três seeds treinadas, a Seed 42028 atingiu o maior CompositeScore válido (0.4700 vs 0.4694 e 0.4623). A verificação física de hash SHA-256 no disco comprovou que `selected_candidate.pt` é idêntico byte-a-byte ao `seed_42028/best_checkpoint.pt` (`4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`).
3. **Observação 1.2 → Denominadores Condicionais Auditados**:
   - Para `NextSector`: O filtro `(sector_transition_occurs == 1) & (next_sector_loss_mask > 0.5)` selecionou rigorosamente 671 de 5.120 amostras de validação. A soma dos suportes por setor (A: 136, B: 128, MID: 330, CT: 43, T: 34) totaliza exatamente 671, comprovando conservação exata e ausência de contaminação por frames sem transição.
   - Para `CandidateSpotRanking`: O filtro `spot_loss_mask == True` selecionou exatamente 472 amostras elegíveis. Zero amostras com spot mascarado ou não supervisionado venceram a seleção (`invalid_masked_selections = 0`, `unsupported_spot_selections = 0`).
4. **Observação 1.3 → Conformidade com a Regra 03 (`03-zero-support-is-na`)**:
   - As classes ausentes foram integralmente marcadas como `N/A`.
   - As médias macro dividiram estritamente pelo número de classes ativas: 6 classes para Transition e 6 classes para ExitTrigger.
5. **Observação 1.2 e Conformance Gates (Seção 11 vs Seção 19 do ORIGINAL_REQUEST.md)**:
   - Os gates de Spot Ranking foram superados (MRR: 0.7604 >= 0.60; Top-1: 62.29% >= 45%; Top-5: 95.55% >= 80%).
   - Porém, as heads de State (F1 0.2250 < 0.45), SectorTransition (F1 0.4649 < 0.55), NextSector (F1 0.3652 < 0.50), Transition (F1 0.5637 < 0.60) e ExitTrigger (F1 0.2613 < 0.45) não atingiram os limiares aspiracionais dos gates.
   - Conforme a Seção 19 do `ORIGINAL_REQUEST.md`, quando o treinamento conclui com sucesso mas algum gate não é atingido, o status canônico mandatório é `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`.

---

## 3. Caveats

1. **Discrepância Documental no Relatório do Implementador**: No relatório `implementer_2b3_1/handoff.md`, a seção 1.3 mencionou textualmente `denominador de classes ativas: 7 de 8` para ExitTrigger. A auditoria matemática verificou que o cálculo numérico real dividiu rigorosamente por 6 (`1.5677 / 6 = 0.26128`), pois duas classes possuem suporte zero. A integridade matemática do código e dos JSONs está 100% perfeita; tratava-se de um detalhe textual no relatório markdown do implementador devidamente esclarecido no relatório de auditoria.
2. **Desempenho Relativo ao Último Frame**: Conforme `baseline_comparison.json`, o modelo temporal real superou o baseline de último frame em 5 de 6 métricas individuais (State, Spot MRR, Spot Top-1, Spot Top-5, Transition, ExitTrigger), cumprindo a exigência de superar em pelo menos duas métricas temporais. Contudo, devido a uma diferença em NextSector (0.3652 vs 0.3850), o CompositeScore global ficou em 0.4700 vs 0.4712 (`beats_last_frame: false`).
3. **Avaliação Estritamente em Validation**: Nenhum cálculo matemático utilizou o split `Test` (545.508 linhas, 67 demos), respeitando de forma absoluta a Regra 02 do `AGENTS.md`.

---

## 4. Conclusion

A auditoria matemática e estatística independente do Marco 2B.3 emite veredito de:
**`PASS` em Integridade Matemática, Estatística e Governança**, com classificação canônica de fase:
**`REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`**.

- A reconciliação das matrizes de confusão, suportes, somas e macro-médias possui 100% de consistência determinística.
- A Regra 03 (`zero-support-is-na`) foi rigorosamente respeitada.
- O candidato selecionado (Seed 42028, Época 6) é o verdadeiro maximizador do CompositeScore (0.4700).
- O arquivo canônico de auditoria foi gravado em `training_runs/positioning_v2_real_temporal/full_training/mathematical_training_audit.json` com SHA-256 `b14cbc74f2859840273be9e763625d14b26466e5e8aac0402e4299f8120ba8ab`.

---

## 5. Verification Method

Para verificar independentemente os resultados da auditoria matemática:

1. **Executar o script determinístico de auditoria matemática**:
   ```powershell
   python .agents/teamwork/math_auditor_2b3_1/audit_mathematical_integrity.py
   ```
   *Critério de Invalidação*: Divergência em qualquer assert de F1, CompositeScore ou SHA-256.

2. **Verificar os testes unitários automatizados do Marco 2B.3**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b3_full_training.py -v
   ```
   *Critério de Invalidação*: Qualquer teste com status diferente de PASS (22/22 esperado).

3. **Inspecionar o relatório canônico gerado**:
   Visualizar `training_runs/positioning_v2_real_temporal/full_training/mathematical_training_audit.json` e conferir a decomposição termo a termo e a matriz de gates.
