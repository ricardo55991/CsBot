# Plan — Marco 2B.1: Materialização dos Índices Temporais Canônicos de Mirage v2

## Contexto e Objetivos
Materializar os índices temporais reais e canônicos de posicionamento para o corpus completo de Mirage v2 em shards Parquet versionados para ambiente de produção, cobrindo todas as demos disponíveis em cada split (Train = 311, Validation = 66, Test = 67; excluindo formalmente as 8 demos sem NPZ), integrando sequências de Objective/Save e relabelando NextSector com horizonte futuro real, sem executar treinamento de modelos nem inferência preditiva no split Test.

## Pipeline Operacional Compacto

### Milestone 1: Implementação do Índice Temporal Completo e Suíte de Testes
- **Agente**: Dataset Index Implementer (`teamwork_worker`)
- **Escopo**:
  1. Preservação formal do dataset piloto (`datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet`) como `PILOT_SUBSET_25_DEMOS_PER_SPLIT`.
  2. Implementação do script de materialização em streaming/mmap em `tools/phase3a_training/materialize_full_temporal_index.py`.
  3. Consumo estrito de `datasets/mirage_v2/canonical_temporal_splits_v1.json` (311 Train, 66 Validation, 67 Test; 8 excluídas `RAW_DEM_WITHOUT_NPZ`).
  4. Política de janelas idêntica para todos os splits: 16 Hz, 32 frames, stride 16, overlap 50%.
  5. Integração de `datasets/mirage_v2/positioning/objective_save_sequences.parquet` com regras de precedência (`direct plant/defuse > OBJECTIVE`, `confirmed save > SAVE`, `OBJECTIVE/SAVE > generic HOLD/TRANSIT`).
  6. Relabeling de `NextSector` restrito a {A, B, MID, CT, T, DYNAMIC} com próximo setor visitado no horizonte de `mirage_spot_catalog_v3.json` (sem usar setor atual se não houver transição).
  7. Rejeição/mascaramento de posições inválidas [0, 0, 0].
  8. Materialização dos 12 artefatos de `datasets/mirage_v2/positioning_v2_full_temporal/` (shards Parquet e companion JSONs).
  9. Implementação da suíte de 20 testes unitários em `tests/test_phase3a3_b_milestone2b1_full_index.py`.
  10. Execução de testes (`pytest` e `dotnet test`) e geração de dados preliminares em `training_runs/positioning_v2_real_temporal/`.

### Milestone 2: Auditoria de Proveniência de Dados e Lógica Temporal
- **Agente**: Data Provenance and Temporal Auditor (`teamwork_auditor`)
- **Escopo**:
  1. Auditoria exaustiva dos splits: 311 Train, 66 Val, 67 Test, 8 excluídas `RAW_DEM_WITHOUT_NPZ`.
  2. Verificação de integridade física dos NPZ (hashes SHA-256 e paths).
  3. Auditoria da política de janelas (16Hz, 32 frames, stride 16, 50% overlap).
  4. Auditoria de duplicatas: exact duplicate sequences = 0, cross-split duplicates = 0, conflicting labels = 0.
  5. Auditoria da precedência de Objective e Save e registro de substituição.
  6. Auditoria de NextSector e proveniência do horizonte futuro.
  7. Emissão de `training_runs/positioning_v2_real_temporal/data_provenance_temporal_audit.json`.

### Milestone 3: Auditoria Matemática e Estatística
- **Agente**: Mathematical and Statistical Auditor (`teamwork_auditor`)
- **Escopo**:
  1. Fechamento exato da equação de conservação: `raw_window_candidates = accepted + rejected + explicitly_masked`.
  2. Igualdade `processed_demo_count = expected_demo_count`.
  3. Distribuição das heads (PositioningState, NextSector, Transition, ExitTrigger) com classes com support zero tratadas estritamente como `N/A`.
  4. Auditoria de SpotRanking: `label missing from candidate mask = 0`, `invalid candidate masks = 0`.
  5. Comparação distribucional Piloto vs Full Index via divergência de Jensen-Shannon e classificação (REPRESENTATIVE, etc.).
  6. Emissão de `training_runs/positioning_v2_real_temporal/mathematical_statistical_audit.json`.

### Milestone 4: Auditoria Adversarial, Gates do DataLoader e Relatório Final
- **Agente**: Adversarial Success Auditor (`teamwork_challenger` / `teamwork_auditor`)
- **Escopo**:
  1. Execução determinística dos gates do DataLoader (seed 42026: 500 Train, 250 Val, 250 Test contra fatias NPZ reais) com 100% nas taxas de conformidade.
  2. Execução da suíte de 20 testes unitários `tests/test_phase3a3_b_milestone2b1_full_index.py` (20/20 PASS).
  3. Execução da suíte C# do CsBot (100% verde).
  4. Verificação de isolamento do split Test (zero inferências, zero métricas de modelo).
  5. Conferência dos 20 entregáveis (12 em datasets/ e 8 em training_runs/) e recálculo dos 20 hashes SHA-256 de 64 caracteres.
  6. Emissão de `training_runs/positioning_v2_real_temporal/adversarial_success_audit.json`.
  7. Redação do único relatório Markdown extenso: `training_runs/positioning_v2_real_temporal/marco_2b1_final_report.md`.

### Milestone 5: Gate Final, Emissão de Veredito Canônico e Limpeza
- **Agente**: Orchestrator
- **Escopo**:
  1. Avaliação do `GATE_STATUS.md` com base nos relatórios dos 3 auditores.
  2. Emissão do veredito canônico: `FULL_TEMPORAL_INDEX_READY_FOR_FULL_TRAINING`.
  3. Execução de `manage_subagents(Action="kill_all")`.
  4. Envio de relatório final ao parent via `send_message`.
