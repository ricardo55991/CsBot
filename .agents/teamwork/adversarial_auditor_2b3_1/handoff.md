# Handoff Report — Adversarial Success Auditor (Marco 2B.3)

**Agente**: `adversarial_auditor_2b3_1` (Adversarial Success Auditor)  
**Data/Hora**: 2026-11-08T22:06:00Z  
**Diretório de Trabalho**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\adversarial_auditor_2b3_1`  
**Destinatário**: Orchestrator (`5aa571f6-be49-4f7f-baff-92e5c3c7ec1a`)  
**Veredito Canônico**: **`CONDITIONAL`** (`REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`)  

---

## 1. Observation

Durante a auditoria adversarial impiedosa do treinamento do Positioning Transformer Temporal Real (Marco 2B.3), foram executados testes empíricos diretos, scripts adversariais e verificações forenses sobre os artefatos em `training_runs/positioning_v2_real_temporal/full_training/`. Foram observados diretamente os seguintes fatos:

### 1.1 Testes Adversariais sobre as 7 Diretrizes de Integridade
1. **Máscaras Condicionais (Loss Protections)**:
   - Foram construídos tensores sintéticos com logits extremos (+100.0) e rótulos corrompidos passados à classe `PositioningTransformerV2Loss`.
   - Sob `sector_transition_occurs == 0` (`NO_TRANSITION`) ou `next_sector_loss_mask == 0.0`, a perda `NextSectorLoss` foi exatamente `0.0` (zero amostras válidas).
   - Sob `PositioningState == TRANSIT`, com `spot_loss_mask == False`, com alvo ausente da `candidate_mask`, ou com alvo pertencente aos 26 spots desprovidos de suporte (`supervised_spot_mask == 0`), a perda `SpotLoss` foi rigorosamente `0.0`.
   - Veredito da checagem: **PASS**.

2. **Máscara de Spots Supervisionados e Seleção Neural**:
   - O contrato em `supervised_spot_mask_v1.json` possui 53 spots: exatamente 27 supervisionados (`mask = 1`) e 26 não supervisionados (`mask = 0`).
   - Na camada de inferência `PositioningTransformerV2RealTemporal`, os 26 spots desprovidos de suporte são penalizados com logit `-1e9` (`-1000000000.0`).
   - Ao avaliar batches com candidate mask totalmente aberta (53 spots elegíveis) sobre o checkpoint mestre `selected_candidate.pt`, o logit máximo de qualquer spot não supervisionado foi `-1e9`. Zero spots não supervisionados venceram seleção neural por argmax.
   - Em todas as 3 seeds (42026, 42027, 42028), `invalid_masked_selections = 0` e `unsupported_spot_selections = 0`.
   - Veredito da checagem: **PASS**.

3. **Cálculo de Pesos de Classe e Sampler (Isolamento Train-Only)**:
   - `class_weights.json` registra `train_rows_evaluated: 2364492`, `validation_used_for_weights: false`, `test_used_for_weights: false`.
   - A contagem física direta dos 5 shards de treino (`shard_000.parquet` a `shard_004.parquet`) onde `split == 'train'` somou exatamente 2.364.492 linhas (311 demos canônicas).
   - Nenhuma linha do split de Validação (501.434 linhas) ou do split de Teste (545.508 linhas) foi incluída nos contadores de frequência.
   - Veredito da checagem: **PASS**.

4. **Seleção de Checkpoint e Isolamento Absoluto de Test**:
   - `best_model_selection.json` registra seleção baseada no critério `VALIDATION_COMPOSITE_SCORE_MAXIMUM`.
   - A Seed 42028 foi selecionada na Época 6 com `CompositeScore = 0.4700` (maior valor entre as seeds: 42026=0.4694, 42027=0.4623, 42028=0.4700).
   - O arquivo `selected_candidate.pt` possui hash SHA-256 byte a byte idêntico a `seed_42028/best_checkpoint.pt`:
     `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`.
   - A tentativa direta de instanciar `CanonicalV2PositioningDataset(split='test')` disparou `ValueError` imediato ("Acesso ao split 'test' é estritamente proibido durante o treinamento! Regra 02"). Zero inferências de teste foram geradas.
   - Veredito da checagem: **PASS**.

5. **Fórmula do CompositeScore**:
   - A fórmula em `frozen_composite_formula.json` define:
     `0.20 * StateMacroF1 + 0.10 * SectorTransitionMacroF1 + 0.10 * NextSectorMacroF1 + 0.25 * SpotMRR + 0.20 * TransitionMacroF1 + 0.15 * ExitTriggerMacroF1`.
   - O recálculo aritmético exato produziu:
     - Seed 42026: Calculado `0.46942` vs Reportado `0.4694` (diferença: 0.00002).
     - Seed 42027: Calculado `0.462315` vs Reportado `0.4623` (diferença: 0.000015).
     - Seed 42028: Calculado `0.470045` vs Reportado `0.4700` (diferença: 0.000045).
   - Veredito da checagem: **PASS**.

6. **Independência Estocástica das 3 Seeds**:
   - Os tensores de parâmetros dos checkpoints `best_checkpoint.pt` das seeds {42026, 42027, 42028} foram comparados no espaço euclidiano e angular:
     - Distância L2 dos pesos de Spot: (26 vs 27) = 6.6111; (26 vs 28) = 6.4691; (27 vs 28) = 6.4465.
     - Similaridade de cosseno: (26 vs 27) = 0.0202; (26 vs 28) = 0.0428; (27 vs 28) = 0.0605.
     - Perdas de treino finais distintas: 26 = 2.9974, 27 = 3.0625, 28 = 3.1487.
   - Veredito da checagem: **PASS**.

7. **Evidência Física e Rastreabilidade (Regras 01, 03 e 05)**:
   - Foram recalculados no disco os hashes SHA-256 de todos os artefatos de topo em `training_runs/positioning_v2_real_temporal/full_training/`:
     - `1b8270d4539007c4cf0cb0ecfd716985ba59e6086ef46345dd2b3a49e567fa9a`  `baseline_comparison.json`
     - `457035fa3943e37f7f6859b4498deffd5b9deaa19f711c20e56b46adc8bcaa44`  `best_model_selection.json`
     - `8ab2a7c4a573d65a39c497a21ea8df400c9618f16756e40d3b2d481919346210`  `class_weights.json`
     - `0ba1020c5c6dde09527d63831c5f1c4742b6e582eefa5fe35ab5f6255a15f7e1`  `collapse_monitoring.json`
     - `8322d8eff8d635d98cbb63c9e02ac6a887f5a289fab0629f1c3474ff178fc464`  `compute_preflight.json`
     - `8e344ad4ae452b4733d2941737f61f87c292114af7c0fb7a9c9acdc8b38c1bf3`  `frozen_composite_formula.json`
     - `79dd3db45c4512bbc21a86db1ba318bc44d564338bd64b08a40f722f9aaec707`  `frozen_training_config.json`
     - `35e0421c7ccf9836615eef1d29d9c6ebbb4a823077373b8afab072d25599297d`  `input_snapshot.json`
     - `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`  `selected_candidate.pt`
     - `0708555fcab35907dfdc31452f62e4aefee2ba871c2a7cb9eeb4c12e97357c24`  `temporal_gain_report.json`
     - `4096a8626fb8c347b0fff21703dd86a327af85573c6f672a7a03b8095b0685e5`  `three_seed_comparison.json`
     - `99a2a0f6af2c78f6d63a1e751c2a2e6a8bb38ec6013339c12cef7bef807209ba`  `adversarial_training_audit.json`
   - Nenhuma divergência de hash foi encontrada. Classes com suporte zero (`LURK`, `BOMB_SPOTTED`, `TACTIC_REVISION`) foram estritamente rotuladas como `N/A`. Nenhum selo humano foi forjado.
   - Veredito da checagem: **PASS**.

---

### 1.2 Vulnerabilidades e Invalidações Adversariais Detectadas

1. **Reprovação em 5 de 6 Gates de Validação Obrigatórios (Seção 11 do ORIGINAL_REQUEST.md)**:
   - `PositioningState Macro-F1`: **0.2250** (meta: `>= 0.45`) — **FAIL**
   - `PositioningState Balanced Accuracy`: **0.2397** (meta: `>= 0.50`) — **FAIL**
   - `SectorTransitionOccurs Macro-F1`: **0.4649** (meta: `>= 0.55`) — **FAIL**
   - `SectorTransitionOccurs Balanced Accuracy`: **0.5000** (meta: `>= 0.55`) — **FAIL**
   - `NextSector Macro-F1`: **0.3652** (meta: `>= 0.50`) — **FAIL**
   - `Transition Macro-F1`: **0.5637** (meta: `>= 0.60`) — **FAIL**
   - `ExitTrigger Macro-F1`: **0.2613** (meta: `>= 0.45`) — **FAIL**
   - Apenas `CandidateSpotRanking` atingiu e superou todas as metas (MRR: 0.7604 vs 0.60; Top-1: 62.29% vs 45%; Top-5: 95.55% vs 80%; 0 seleções inválidas).

2. **Colapso da Classe `TRANSITION_OCCURS` e Contradição em `collapse_monitoring.json`**:
   - No split de validação, existem 671 transições de setor reais (`TRANSITION_OCCURS`) e 4.449 instâncias de `NO_TRANSITION`.
   - Nas 3 seeds, o recall de `TRANSITION_OCCURS` foi exatamente **`0.0`** (o modelo previu 100% dos exemplos como `NO_TRANSITION`).
   - Contudo, `collapse_monitoring.json` registrou no cabeçalho `"sector_transition_collapse": false` e `"rare_state_collapse": false`. Isso constitui uma contradição interna direta (Padrão 1 do `csbot-report-skeptic`).

3. **Contradição de Superioridade Temporal em `baseline_comparison.json`**:
   - O CompositeScore do modelo temporal real é **`0.4700`**, enquanto o baseline estático de último frame real atingiu **`0.4712`** (delta de `-0.0012`).
   - O campo `beats_last_frame` é reportado como `false`, mas o campo `temporal_superiority_confirmed` foi registrado como `true`.
   - O relatório `temporal_gain_report.json` proclama ganho categórico sem ressalvar que o CompositeScore total regrediu e que NextSector caiu em `-0.0198`.

4. **Omissão do Baseline Logístico**:
   - A Seção 12 item 4 do `ORIGINAL_REQUEST.md` exige formalmente a comparação contra "baseline logístico". Esse baseline foi omitido dos artefatos entregues.

5. **Reprovação do Handoff do Implementador no Script Canônico (`csbot-report-skeptic`)**:
   - A execução de `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py` sobre `implementer_2b3_1/handoff.md` emitiu veredito **`FAIL`** com 2 violações do Vetor 11 (`percentage_100_without_denominator` nas linhas 83 e 100).

---

## 2. Logic Chain

1. **Observação 1.1 → Conformidade Estrutural e Forense**: Todas as verificações de engenharia exigidas pelo dispatch foram rigorosamente comprovadas: isolamento do Test set, máscaras condicionais matematicamente testadas, pesos Train-only sem contaminação, fórmulas congeladas e independência estocástica. Portanto, o pipeline não é fraudulento nem simulado.
2. **Observação 1.2 (Item 1) → Falha dos Gates de Validação**: A Seção 11 do `ORIGINAL_REQUEST.md` estabelece limiares contratuais mínimos de Macro-F1 para cada uma das cabeças. O modelo alcançou as metas com excelência apenas na cabeça de spots (SpotRanking), mas falhou nas outras 5 cabeças com ampla margem (State 0.225 vs 0.45; SectorTransition 0.4649 vs 0.55; NextSector 0.3652 vs 0.50; Transition 0.5637 vs 0.60; ExitTrigger 0.2613 vs 0.45).
3. **Observação 1.2 (Item 2 e 3) → Padrões de Falha do csbot-report-skeptic**: A presença de recall 0.0 rotulado como ausência de colapso, a contradição entre `beats_last_frame: false` e `temporal_superiority_confirmed: true`, e as alegações de 100% sem denominador no handoff violam os padrões 1 e 11 do ceticismo metodológico.
4. **Observação 1.2 e Seção 19 do ORIGINAL_REQUEST.md → Veredito Mandatório**:
   - A Seção 19 é categórica:
     - *"Se as três seeds concluírem, mas algum gate não for atingido: `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`"*
     - *"Se as três seeds concluírem e todos os gates de Validation passarem: `REAL_TEMPORAL_POSITIONING_CANDIDATE_READY_FOR_FINAL_EVALUATION`"*
   - Como múltiplos gates de validação falharam, a emissão de `READY_FOR_FINAL_EVALUATION` é estritamente proibida. O único veredito canônico admitido pelas regras é **`CONDITIONAL`** (`REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`).

---

## 3. Caveats

1. **Desbalanceamento Extremo de Classes**: A falha nas cabeças de State, SectorTransition e ExitTrigger não decorre de erro de código, mas do desbalanceamento severo inerente ao corpus de CS2 (onde TRANSIT representa >90% dos frames e NO_TRANSITION representa 86.9% dos frames) combinado com o clamping conservador dos pesos de classe (0.25 a 8.0) e o pequeno volume de amostragem por época (3.840 frames por época de um universo de 2.36M).
2. **Isolamento de Test Preservado**: Nenhuma violação da Regra 02 (contaminação do Test Set) ocorreu. O candidato gerado é legítimo e pode ser refinado sem necessidade de descarte da base de dados.
3. **Ambiente Somente-Leitura**: Em estrita conformidade com a Regra 09 do `AGENTS.md`, este auditor não modificou código-fonte (`src/`, `tools/`) nem artefatos de dados.

---

## 4. Conclusion

O veredito da Auditoria Adversarial para a Fase 3A.3-B, Marco 2B.3 é:

# **`CONDITIONAL`**
### Código Canônico: **`REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`**

**Resumo das Condicionalidades e Bloqueadores**:
1. O checkpoint candidato `selected_candidate.pt` NÃO está autorizado para avaliação no split Test (`NoFinalEvaluation`).
2. O checkpoint candidato NÃO está autorizado para exportação ONNX nem integração C# ao runtime do servidor CS2.
3. Para futura homologação `READY_FOR_FINAL_EVALUATION`, a equipe de implementação deverá resolver:
   - O colapso da classe `TRANSITION_OCCURS` (adotar calibração de threshold ou Focal Loss);
   - A convergência das classes raras de PositioningState;
   - A implementação formal do baseline logístico;
   - A retificação das contradições documentais em `collapse_monitoring.json` e `baseline_comparison.json`.

Conforme a **Regra 08** (`08-no-automatic-phase-advance`), o processo deve parar imediatamente aqui, aguardando a decisão e comando expresso do usuário humano.

---

## 5. Verification Method

Para reproduzir deterministicamente os testes adversariais desta auditoria:

1. **Executar a Suíte Adversarial Independente**:
   ```powershell
   python .agents/teamwork/adversarial_auditor_2b3_1/run_adversarial_suite.py
   ```
   *Critério de Invalidação*: Qualquer assert disparado nos 7 testes adversariais.

2. **Executar o Script Canônico do Skeptic**:
   ```powershell
   python -X utf8 .agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py `
     --report-path .agents/teamwork/implementer_2b3_1/handoff.md `
     --workspace-root . `
     --output-json .agents/teamwork/adversarial_auditor_2b3_1/skeptic_handoff_audit.json
   ```
   *Critério de Invalidação*: Verificação dos 2 alertas de `percentage_100_without_denominator`.

3. **Verificar os Hashes SHA-256 no Disco**:
   ```powershell
   python -c "import hashlib; print(hashlib.sha256(open('training_runs/positioning_v2_real_temporal/full_training/adversarial_training_audit.json','rb').read()).hexdigest())"
   ```
   *Critério de Invalidação*: Divergência do hash `99a2a0f6af2c78f6d63a1e751c2a2e6a8bb38ec6013339c12cef7bef807209ba`.
