# Handoff Report — ML Generalization Auditor (Marco 2B.3)

**Agente**: `generalization_auditor_2b3_1` (ML Generalization Auditor)  
**Data/Hora**: 2026-11-08T22:04:30Z  
**Diretório de Trabalho**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\generalization_auditor_2b3_1`  
**Destinatário**: Orchestrator (`5aa571f6-be49-4f7f-baff-92e5c3c7ec1a`)  
**Veredito Canônico**: **`CONDITIONAL`** (`REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`)

---

## 1. Observation

Durante a auditoria independente de generalização de ML, estabilidade de treinamento e ganhos temporais da Fase 3A.3-B, Marco 2B.3, foram observados diretamente sobre o disco e artefatos brutos os seguintes fatos:

### 1.1 Curvas de Aprendizado e Gap Train/Validation
Nos arquivos `seed_42026/train_metrics.jsonl`, `seed_42027/train_metrics.jsonl`, `seed_42028/train_metrics.jsonl` e seus respectivos `validation_metrics.jsonl`:
- **Seed 42026**:
  - Treino: Loss inicial de 6.8584 (Época 1) caindo para 2.9974 (Época 8), redução de 3.8610.
  - Validação: CompositeScore inicial de 0.3109 progredindo para 0.4694 (Época 8).
- **Seed 42027**:
  - Treino: Loss inicial de 6.7856 (Época 1) caindo para 3.0625 (Época 8), redução de 3.7231.
  - Validação: CompositeScore inicial de 0.3277 progredindo para 0.4623 (Época 8).
- **Seed 42028** (Candidato Selecionado):
  - Treino: Loss inicial de 6.9169 (Época 1) caindo para 3.2189 (Época 6) e 3.1487 (Época 8), redução de 3.7682.
  - Validação: CompositeScore inicial de 0.3301, atingindo pico de 0.4700 na Época 6 e estabilizando em 0.4654 na Época 8.
- Não foi observada divergência entre perda de treino e métricas de validação, indicando ausência de overfitting patológico ou memorização estocástica.

### 1.2 Auditoria de Colapso de Classes e Monitoramento
No arquivo `training_runs/positioning_v2_real_temporal/full_training/collapse_monitoring.json`:
- Linhas 4-10:
  ```json
  "anti_collapse_checks": {
    "state_collapse": false,
    "sector_transition_collapse": false,
    "next_sector_collapse": false,
    "spot_popularity_collapse": false,
    "rare_state_collapse": false
  }
  ```
- Contudo, a inspeção empírica direta das contagens de confusão em `seed_42028/confusion_counts_validation.json` revela:
  - **`sector_transition_per_class`**:
    - `NO_TRANSITION`: support 4449, precision 0.8689, recall 1.0, f1 0.9299
    - `TRANSITION_OCCURS`: support 671, precision 0.0, recall 0.0, f1 0.0
    - Predições totais de `NO_TRANSITION`: 5.120 de 5.120 (100.0% das amostras).
    - O modelo **nunca** predisse `TRANSITION_OCCURS` (recall 0.0 nas 3 seeds).
  - **`positioning_state_per_class`**:
    - `TRANSIT`: support 4640, precision 0.9407, recall 0.9812, f1 0.9605
    - `CLEARANCE`: support 221, precision 0.5500, recall 0.6968, f1 0.6148
    - `STAGING` (88), `HOLD` (143), `OBJECTIVE` (8), `RETAKE` (19), `SAVE` (1): **recall = 0.0, precision = 0.0, f1 = 0.0** em todas as 3 seeds.
    - `rare_state_mean_recall`: 0.0 em todas as 3 seeds.
  - No código `tools/phase3a_training/run_full_training_marco_2b3.py` (linhas 1071-1077), o dicionário `anti_collapse_checks` foi hardcoded para `False`, não computando dinamicamente se a taxa predita de `TRANSITION_OCCURS` ou de estados raros foi nula.
  - Por outro lado, a cabeça `CandidateSpotRanking` não apresentou colapso de popularidade: distribuiu predições adequadamente pelos 27 spots supervisionados com MRR de 0.7604, Top-1 de 62.29%, Top-5 de 95.55%, 0 seleções de spots mascarados e 0 de spots não supervisionados.

### 1.3 Estabilidade Estatística Multi-Seed
No arquivo `training_runs/positioning_v2_real_temporal/full_training/three_seed_comparison.json`:
- CompositeScores: 0.4694 (Seed 42026), 0.4623 (Seed 42027), 0.4700 (Seed 42028).
- Média: 0.4672, Desvio Padrão: 0.0035, Coeficiente de Variação (CV): 0.76%, Amplitude: 0.0077.
- Desvio padrão por cabeça:
  - `state_macro_f1`: 0.0038 (CV 1.66%)
  - `sector_transition_macro_f1`: 0.0000 (CV 0.00%, colapsado identicamente em 100% NO_TRANSITION)
  - `next_sector_macro_f1`: 0.0461 (CV 14.83%)
  - `spot_mrr`: 0.0064 (CV 0.84%)
  - `transition_macro_f1`: 0.0033 (CV 0.58%)
  - `exit_trigger_macro_f1`: 0.0046 (CV 1.73%)
- Confirma-se altíssima estabilidade e determinismo entre seeds com inicialização independente.

### 1.4 Comparação com Baselines Reais e Ganhos Temporais
No arquivo `training_runs/positioning_v2_real_temporal/full_training/baseline_comparison.json` e `temporal_gain_report.json`:
- **CompositeScores**:
  - Modelo Temporal Real (32 frames): `0.4700`
  - Baseline de Último Frame Real (frame t=31 estático replicado): `0.4712`
  - Baseline Heurístico de Frequência Marginal: `0.1434`
  - Baseline Logístico: **Ausente** (não foi implementado nem computado).
- **Veredito no arquivo** (`baseline_comparison.json`, linhas 47-51):
  ```json
  "superiority_verdict": {
    "beats_last_frame": false,
    "beats_frequency_ranker": true,
    "temporal_superiority_confirmed": true
  }
  ```
  Observa-se contradição direta: `beats_last_frame` é `false`, mas `temporal_superiority_confirmed` foi marcado como `true`.
- **Ganhos métricos individuais** (`temporal_gain_report.json`):
  - `composite_score_gain`: `-0.0012` (inferior ao baseline estático)
  - `next_sector_macro_f1_gain`: `-0.0198` (0.3652 vs 0.3850)
  - `state_macro_f1_gain`: `+0.0003` (0.2250 vs 0.2247)
  - `sector_transition_macro_f1_gain`: `0.0000` (0.4649 vs 0.4649)
  - `spot_mrr_gain`: `+0.0016` (0.7604 vs 0.7588)
  - `transition_macro_f1_gain`: `+0.0012` (0.5637 vs 0.5625)
  - `exit_trigger_macro_f1_gain`: `+0.0006` (0.2613 vs 0.2607)
  - Ganho em estados dependentes de sequência: `CLEARANCE` teve F1 de 0.6148 vs 0.6127 (+0.0021); contudo, `HOLD` e `OBJECTIVE` permaneceram com F1 de 0.0000 em ambos os modelos.

### 1.5 Conformidade dos Gates de Validação (Seção 11 do ORIGINAL_REQUEST.md)
Confrontando as métricas da Seed Vencedora (42028) contra os limites estipulados:
1. `PositioningState`:
   - `Macro F1 >= 0.45`: Observado `0.2250` -> **FAIL**
   - `Balanced Accuracy >= 0.50`: Observado `0.2397` -> **FAIL**
2. `SectorTransitionOccurs`:
   - `Macro F1 >= 0.55`: Observado `0.4649` -> **FAIL**
   - `Balanced Accuracy >= 0.55`: Observado `0.5000` -> **FAIL**
3. `NextSector`:
   - `Macro F1 >= 0.50`: Observado `0.3652` -> **FAIL**
   - `Balanced Accuracy >= 0.50`: Observado `0.3558` -> **FAIL**
   - `Pelo menos 4 setores com suporte real`: Observado 5 setores com suporte -> **PASS**
4. `CandidateSpotRanking`:
   - `MRR >= 0.60`: Observado `0.7604` -> **PASS**
   - `Top-1 >= 0.45`: Observado `0.6229` (62.29%) -> **PASS**
   - `Top-5 >= 0.80`: Observado `0.9555` (95.55%) -> **PASS**
   - `invalid masked selection = 0`: Observado `0` -> **PASS**
   - `unsupported-spot selection = 0`: Observado `0` -> **PASS**
5. `Transition`:
   - `Macro F1 >= 0.60`: Observado `0.5637` -> **FAIL**
6. `ExitTrigger`:
   - `Macro F1 >= 0.45`: Observado `0.2613` -> **FAIL**

Resultado dos Gates: **1 Cabeça Aprovada (SpotRanking)** e **5 Cabeças Reprovadas (PositioningState, SectorTransition, NextSector, Transition, ExitTrigger)**.

---

## 2. Logic Chain

1. **Observação 1.1 → Ausência de Overfitting Patológico**: As curvas de loss e métricas convergem de forma monotônica, sem que a perda de treino decaia para zero enquanto a perda de validação explode. A generalização é funcional para representações densas (SpotRanking), afastando hipótese de memorização estocástica.
2. **Observação 1.2 → Detecção de Colapso Real vs Hardcoded Flag**: Em `collapse_monitoring.json`, `anti_collapse_checks` foi emitido como `false` por meio de atribuição fixa no script gerador. No entanto, o recall de `TRANSITION_OCCURS` foi exatamente `0.0` (0 acertos em 671 casos) e o recall dos 5 estados raros foi `0.0`. Isso constitui formalmente colapso para a classe majoritária (`NO_TRANSITION` e `TRANSIT`).
3. **Observação 1.3 → Estabilidade Estatística Confirmada**: O desvio padrão de 0.0035 (CV 0.76%) no CompositeScore entre as 3 seeds confirma que a arquitetura e a otimização são estáveis e determinísticas.
4. **Observação 1.4 → Não-cumprimento de Superioridade Consolidada sobre Baseline**: O contrato da Seção 12 estipula que o modelo temporal deve superar os baselines reais. O modelo supera o Frequency Ranker (+0.3266), mas perde no CompositeScore para o último frame real (-0.0012) devido à queda em `NextSector` (-0.0198). A marcação de `temporal_superiority_confirmed: true` contradiz o dado empírico `beats_last_frame: false`. Além disso, a omissão do baseline logístico viola a completude da Seção 12.
5. **Observação 1.5 → Aplicação Canônica da Regra de Decisão da Seção 19**: A Seção 19 do `ORIGINAL_REQUEST.md` define deterministicamente:
   > *"Se as três seeds concluírem, mas algum gate não for atingido: `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`"*
   Como o pipeline concluiu as 3 seeds, gerou todos os artefatos sem violação de integridade nos dados (zero contaminação, join 1:1 perfeito), mas falhou em 5 dos 6 gates e sofreu colapso parcial em classes minoritárias, o veredito obrigatório e inegociável é **`CONDITIONAL`**.

---

## 3. Caveats

1. **Split Test e Final Holdout**: Não foram executadas quaisquer inferências sobre os splits `Test` (67 demos) e `Final Holdout`, em estrita observância à Regra `02-no-test-contamination`. A avaliação reflete 100% o comportamento sobre o split `Validation` (66 demos canônicas, 5.120 amostras).
2. **Causa Raiz do Colapso**: O colapso observado nas classes minoritárias decorre da assimetria extrema do dataset de Mirage v2 (TRANSIT representa 90.6% das sequências; NO_TRANSITION representa 86.9%) combinada ao teto de clamp de pesos (`clamp_max = 5.0`) e à amostragem de apenas 3.840 exemplos por época (60 batches de 64), o que equivale a ~0.16% do split de treino de 2.36M por época.
3. **Desempenho de SpotRanking**: A cabeça de `CandidateSpotRanking` teve desempenho excepcional (MRR 0.7604, Top-5 95.55%), demonstrando que o problema de generalização é restrito ao balanceamento de perdas das cabeças de classificação discreta.

---

## 4. Conclusion

O Treinamento do Positioning Transformer Temporal Real (Marco 2B.3) alcançou integridade estrutural, rastreabilidade de dados e estabilidade estocástica determinística. O candidato vencedor `selected_candidate.pt` (Seed 42028, SHA-256: `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`) está materializado e congelado.

Contudo, o trabalho não cumpre os requisitos de desempenho para avanço irrestrito para avaliação final:
- 5 dos 6 gates de validação foram reprovados;
- Colapso comprovado em `SectorTransitionOccurs` e nos 5 estados raros;
- O modelo temporal não superou o baseline estático de último frame no CompositeScore;
- O baseline logístico foi omitido.

Portanto, em estrita conformidade com a Seção 19 do `ORIGINAL_REQUEST.md` e a governança do `AGENTS.md`, o parecer final emitido pelo ML Generalization Auditor é:

# Veredito: **`CONDITIONAL`**
### Código Canônico: `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`

O checkpoint não deve ser descartado (pois é a primeira versão com histórico 100% real e 32 frames), mas requer refinamento de amostragem/loss (aumento de passos, Focal Loss ou calibração de threshold exclusivamente em Validação) antes de qualquer etapa futura de avaliação final.

---

## 5. Verification Method

Para reproduzir e auditar independentemente os achados desta auditoria:

1. **Inspecionar o Relatório Canônico JSON de Generalização de ML**:
   ```powershell
   python -c "import json; r=json.load(open('training_runs/positioning_v2_real_temporal/full_training/ml_generalization_audit.json')); print('Veredito:', r['canonical_verdict'], '| Decision:', r['decision_code'])"
   ```
   *Hash SHA-256 esperado*: `7570e56d8c6437e138e5f0c1123257b7c18a6702bbb793dc53b2b4540f8fe8e0`.

2. **Verificar os Resultados de Colapso e Confusion Counts**:
   ```powershell
   python -c "import json; c=json.load(open('training_runs/positioning_v2_real_temporal/full_training/seed_42028/confusion_counts_validation.json')); print('Transition Occurs Recall:', c['sector_transition_per_class']['TRANSITION_OCCURS']['recall'])"
   ```
   *Critério*: Confirmação de que o recall é rigorosamente 0.0.

3. **Verificar o Gap contra o Baseline de Último Frame**:
   ```powershell
   python -c "import json; b=json.load(open('training_runs/positioning_v2_real_temporal/full_training/baseline_comparison.json')); print('Temporal:', b['models']['real_temporal_model']['composite_score'], 'vs Last Frame:', b['models']['last_frame_real_baseline']['composite_score'])"
   ```
   *Critério*: Confirmação de que o modelo temporal (0.4700) é inferior ao baseline estático (0.4712).

4. **Executar a Suíte de 22 Testes de Governança do Marco 2B.3**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b3_full_training.py -v
   ```
   *Critério*: 22 passed, 0 failed.
