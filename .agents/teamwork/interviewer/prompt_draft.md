Orquestração compacta solicitada: equipe de no máximo 5 subagentes ativos (1. Orchestrator, 2. Dataset Index Implementer, 3. Data Provenance and Temporal Auditor, 4. Mathematical and Statistical Auditor, 5. Adversarial Success Auditor) com nested_subagents = false, only_orchestrator_can_delegate = true, spawn_only_when_required = true e kill_all_on_completion = true, sem criar subsubagentes, sem repetir Graphify completo e sem repetir a homologação da Governança 1.1. Materializar os índices temporais reais e canônicos de posicionamento para o corpus completo de Mirage v2 em shards Parquet versionados para ambiente de produção, cobrindo todas as demos disponíveis em cada split (Train = 311, Validation = 66, Test = 67; excluindo formalmente as 8 demos sem NPZ), integrando sequências de Objective/Save e relabelando NextSector com horizonte futuro real, sem executar treinamento de modelos nem inferência preditiva no split Test.

Integrity mode: development

## Requirements

### R1. Preservação do Dataset Piloto e Consumo Estrito da Fonte Canônica de Splits
O dataset piloto anterior (`datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet`, shards, manifests, métricas e checkpoints) não deve ser sobrescrito, devendo manter seus hashes e caminhos preservados e ser catalogado formalmente como `PILOT_SUBSET_25_DEMOS_PER_SPLIT`. A nova versão deve ser gerada exclusivamente sob `datasets/mirage_v2/positioning_v2_full_temporal/`. A fonte canônica de splits a ser consumida é estritamente `datasets/mirage_v2/canonical_temporal_splits_v1.json`, processando todas as demos aceitas (Train = 311, Validation = 66, Test = 67) e excluindo formalmente as 8 entradas com status `RAW_DEM_WITHOUT_NPZ`. É proibido aplicar corte manual de 25 demos ou sampling por split. Para cada demo, registrar `demo_id`, `match_id`, `split`, `npz_path`, `npz_sha256`, `frame_count`, `round_count`, `player slots`, `accepted` e `rejection_reason`.

### R2. Política Única e Idêntica de Janelas Temporais para Todos os Splits
Aplicar rigorosamente a mesma política de janelas para Train, Validation e Test: `sample_rate = 16 Hz`, `sequence_length = 32 frames`, `stride = 16 frames`, `overlap = 50%`. Aplicar identicamente em todos os splits as regras de round boundary checks, slot validation, player alive policy, padding policy, filtros de confiança, elegibilidade de label, construção de candidate mask e tratamento de posições inválidas [0, 0, 0]. Nenhuma divergência entre splits é permitida quanto a stride, filtros, confiança, padding, seleção de classes ou amostragem; a única diferença admitida é o conteúdo das partidas.

### R3. Materialização de Shards Parquet e Integração Canônica de Objective e Save
Materializar o índice em shards Parquet versionados contendo apenas ponteiros e labels, sem duplicar tensores densos NPZ. Cada registro deve conter no mínimo os 21 campos canônicos: `sequence_id`, `demo_id`, `match_id`, `round_id`, `player_id`, `slot`, `split`, `window_start_frame`, `window_end_frame`, `label_frame`, `npz_path`, `PositioningState`, `ObjectiveSubtype`, `SaveSubtype`, `NextSector`, `CandidateSpotId`, `SpotLossMask`, `Transition`, `ExitTrigger`, `confidence`, `provenance_type` e `next_sector_source`. Integrar os registros aprovados de `datasets/mirage_v2/positioning/objective_save_sequences.parquet` ao índice temporal integral, garantindo que cada sequência aponte para o NPZ e janela temporal real sem duplicar janelas existentes. Seguir a ordem de precedência: `direct plant/defuse > OBJECTIVE`, `confirmed save evidence > SAVE`, `OBJECTIVE/SAVE > generic HOLD ou TRANSIT` quando a evidência for válida. Em caso de substituição de label, registrar `old_label`, `new_label`, `precedence_rule` e `provenance`. Sobrevivência isolada não produz SAVE, pós-plant não torna todo jogador OBJECTIVE e coordenadas inválidas [0,0,0] devem ser rejeitadas ou mascaradas.

### R4. Relabeling de NextSector com Horizonte Futuro Real Visitado
Definir `NextSector` como o próximo setor semântico efetivamente visitado pelo jogador após o final da janela dentro do horizonte congelado definido no contrato canônico `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json`. As classes são restritas a {A, B, MID, CT, T, DYNAMIC}. É terminantemente proibido utilizar o setor atual como label futuro (quando não houver transição de setor), frame global fixo, assigned target da Utility AI, candidate spot futuro ou posições futuras como entrada da janela. Para cada sequência, registrar `current_sector`, `next_sector`, `transition_tick`, `horizon_frames`, `next_sector_source` e `confidence`, gerando a distribuição multiclasse por split.

### R5. Contabilidade Integral, Auditoria de Duplicatas e Gates do DataLoader Canônico
Calcular contabilidade integral por split exigindo fechamento exato: `raw_window_candidates = accepted + rejected + explicitly_masked` e `processed_demo_count = expected_demo_count` (com justificativa individual para qualquer rejeição). Auditar duplicatas exigindo `exact duplicate sequences = 0`, `cross-split duplicates = 0` e `conflicting labels for same window = 0` (janelas adjacentes com overlap legítimo de 50% são permitidas). Executar gates determinísticos do DataLoader com seed 42026 em batches de 500 Train, 250 Validation e 250 Test contra fatias NPZ reais, exigindo 100% nas taxas de conformidade estrutural (`ToleranceMatchRate = 100%`, `SyntheticWindowRate = 0%`, `TeammateRealSlotMatchRate = 100%`, `UnmaskedPaddingRate = 0%`, `RoundBoundaryViolationRate = 0%`, `CrossPlayerWindowRate = 0%`, `FutureLeakageRate = 0%`, `MissingNpZRate = 0%`, `ExactDuplicateWindowRate = 0%`). Nenhuma inferência de modelo nem métricas de modelo podem ser executadas no split Test.

### R6. Cobertura de SpotRanking, Comparação Distribucional com o Piloto e Auditorias Especializadas
Calcular distribuição integral das heads (PositioningState, NextSector, Transition, ExitTrigger) tratando classes com suporte zero estritamente como N/A. Para SpotRanking, auditar a cobertura das sequências elegíveis garantindo `label missing from candidate mask = 0` e `invalid candidate masks = 0`. Comparar a distribuição do índice piloto (25 demos/split) com o índice canônico completo via divergência de Jensen-Shannon e diferença absoluta máxima de classes, classificando o piloto como REPRESENTATIVE, PARTIALLY_REPRESENTATIVE ou NON_REPRESENTATIVE sem invalidá-lo retroativamente. Três auditores independentes (Data Provenance and Temporal Auditor, Mathematical and Statistical Auditor, Adversarial Success Auditor) devem auditar a entrega e assinar os relatórios técnicos. O implementador não pode auditar o próprio trabalho.

### R7. Eficiência Operacional, Execução de Testes e Emissão do Veredito Canônico
Operar com streaming, memory mapping, bounded caches e shards Parquet sem carregar todas as janelas densas simultaneamente na RAM. Reutilizar o DataLoader canônico, contratos aprovados, manifests congelados, scripts de auditoria do Marco 1 e as Skills/Hooks já homologados. Produzir apenas um relatório Markdown extenso (`training_runs/positioning_v2_real_temporal/marco_2b1_final_report.md`), gerando os demais 19 entregáveis como JSON ou Parquet. A suíte de 20 testes obrigatórios (`tests/test_phase3a3_b_milestone2b1_full_index.py`) e a suíte C# do CsBot devem permanecer 100% verdes. Emitir veredito final canônico (`FULL_TEMPORAL_INDEX_READY_FOR_FULL_TRAINING` ou `FULL_TEMPORAL_INDEX_NOT_READY`) e aguardar autorização humana, sem iniciar treinamento, sem consultar métricas de Test, sem consultar Final Holdout e sem exportar ONNX. Finalizar encerrando todos os subagentes ativos (`kill_all`).

## Acceptance Criteria

### Integridade dos Splits e Preservação do Piloto
- [ ] O dataset piloto anterior (`datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet`) permanece intacto com hash SHA-256 verificado e catalogado como `PILOT_SUBSET_25_DEMOS_PER_SPLIT`.
- [ ] Todas as 444 demos canônicas são processadas segundo `datasets/mirage_v2/canonical_temporal_splits_v1.json`, com reconciliação exata de 311 Train, 66 Validation e 67 Test.
- [ ] As 8 demos com status `RAW_DEM_WITHOUT_NPZ` são formalmente excluídas e documentadas com `rejection_reason`.

### Políticas de Janelamento e Formato dos Shards
- [ ] As regras de janelamento (`sample_rate = 16 Hz`, `sequence_length = 32`, `stride = 16`, `overlap = 50%`) e de integridade física são comprovadamente idênticas em Train, Validation e Test.
- [ ] Os shards Parquet gerados em `datasets/mirage_v2/positioning_v2_full_temporal/` contêm apenas ponteiros e labels, sem tensores densos duplicados, cobrindo todos os 21 campos mínimos especificados (incluindo `provenance_type` e `next_sector_source`).
- [ ] Sequências com coordenadas inválidas `[0, 0, 0]` são 100% rejeitadas ou mascaradas no índice.

### Integração de Objective e Save
- [ ] As sequências aprovadas de `datasets/mirage_v2/positioning/objective_save_sequences.parquet` estão integradas no índice temporal com registro de substituições, precedência e proveniência.
- [ ] A contabilidade de integração de Objective/Save fecha formalmente (`candidate_windows = integrated + replaced + duplicated + rejected + low_confidence_excluded`).
- [ ] A regra de precedência (`direct plant/defuse > OBJECTIVE`, `confirmed save > SAVE`, `OBJECTIVE/SAVE > generic HOLD/TRANSIT`) é validada deterministicamente.

### Relabeling de NextSector
- [ ] Todo registro de NextSector possui label pertencente a {A, B, MID, CT, T, DYNAMIC} baseado no próximo setor visitado no horizonte definido em `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json`.
- [ ] Nenhuma label de NextSector utiliza o setor atual quando não há transição de setor no horizonte, nem utiliza assigned target de Utility AI ou candidate spots futuros.
- [ ] O campo `next_sector_source` está populado para todas as sequências rotuladas.

### Duplicatas e Fechamento da Contabilidade
- [ ] Contagem de `exact duplicate sequences` é rigorosamente igual a 0 em todos os splits.
- [ ] Contagem de `cross-split duplicate windows` é rigorosamente igual a 0 entre Train, Validation e Test.
- [ ] Contagem de `conflicting labels for same window` é rigorosamente igual a 0.
- [ ] A equação de conservação `raw_window_candidates = accepted + rejected + explicitly_masked` é 100% comprovada para Train, Validation e Test.
- [ ] A igualdade `processed_demo_count = expected_demo_count` é satisfeita para todos os splits.

### Gates do DataLoader Canônico
- [ ] A auditoria determinística do DataLoader (seed 42026: 500 Train, 250 Val, 250 Test) atinge 100% em ToleranceMatchRate e TeammateRealSlotMatchRate, e 0% em SyntheticWindowRate, UnmaskedPaddingRate, RoundBoundaryViolationRate, CrossPlayerWindowRate, FutureLeakageRate, MissingNpZRate e ExactDuplicateWindowRate.
- [ ] O split Test é auditado apenas estruturalmente contra o NPZ, com zero inferências de modelo e zero cálculo de métricas de modelo.

### SpotRanking e Análise Distribucional
- [ ] A métrica `label missing from candidate mask` é igual a 0 em todas as sequências de estados elegíveis.
- [ ] A métrica `invalid candidate masks` é igual a 0.
- [ ] A divergência Jensen-Shannon entre o índice piloto e o índice integral é calculada e reportada com classificação canônica (REPRESENTATIVE, PARTIALLY_REPRESENTATIVE ou NON_REPRESENTATIVE).
- [ ] Classes com suporte zero são estritamente tratadas e exibidas como `N/A`.

### Testes Automatizados e Entregáveis
- [ ] Todos os 20 testes unitários obrigatórios da suíte `tests/test_phase3a3_b_milestone2b1_full_index.py` passam com status verde.
- [ ] A suíte de testes C# do repositório compila sem erros e passa sem regressões.
- [ ] Os 12 artefatos do diretório `datasets/mirage_v2/positioning_v2_full_temporal/` estão materializados no disco com hashes SHA-256 calculados.
- [ ] Os 8 artefatos do diretório `training_runs/positioning_v2_real_temporal/` estão materializados no disco, incluindo os relatórios das 3 auditorias independentes e `marco_2b1_final_report.md`.
- [ ] A execução é concluída emitindo veredito explícito (`FULL_TEMPORAL_INDEX_READY_FOR_FULL_TRAINING` ou `FULL_TEMPORAL_INDEX_NOT_READY`), sem iniciar treino de modelos e sem exportar artefatos ONNX.
