# Handoff Report — Data Provenance Auditor

- **Auditor**: Data Provenance Auditor (`teamwork_auditor`)
- **Fase**: Pré-Fase 3A.3 / Requisito R3
- **Diretório de Trabalho**: `.agents/teamwork/data_provenance_auditor_1`
- **Classificação Canônica**: `AGENT_REVIEWED`
- **Veredito Canônico**: **`CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**
- **Data e Hora UTC**: 2026-11-07T21:50:00Z

---

## 1. Observation

Durante a execução da auditoria forense do Requisito R3, foram observados diretamente e verificados os seguintes fatos materiais:

1. **Caminho Real de Treinamento e Incompatibilidade de Hashes**:
   - O script `tools/phase3a_training/train_full.py` (código SHA-256 `ef9c32d386346dca33fda0b8ff274b2efab09585e53c95405de08481ac02b0d9`) executou o treinamento das seeds 42026, 42027 e 42028.
   - Em `tools/phase3a_training/train_full.py:L42-L43`, o script importou `create_dataset_from_shards` de `tools.phase3a_training.data_utils`.
   - O arquivo `tools/phase3a_training/data_utils.py` possui hash `d15c234e3a2ce73fe01663293b60a8a53166d73e8caf40254b36eef2e4ec8e45`.
   - O arquivo `training_runs/positioning_v1/seed_42026/input_snapshot.json` registrou formalmente a declaração do hash `921836c8a9c4590f91a2ed3aa8da090a4470878bb8f6e66a8dc25997d198183d`.
     Esse valor pertence a `tools/phase2_dataset/dataloaders.py` (`PositioningDatasetV1`), comprovando documentalmente que a classe de dados auditada na Fase 2.2 não foi a que treinou o modelo na Fase 3A.

2. **Injeção de `np.linspace` e Aliados Artificiais no DataLoader Real**:
   - Em `tools/phase3a_training/data_utils.py:L218-L238`:
     O tensor `history` consome a coordenada instantânea `current_pos`, replicada por 32 passos e perturbada no eixo X pelo drift linear de -0.01 a 0.0 gerado por `np.linspace(-0.01, 0.0, 32)`.
     O tensor `teammates` consome clones matemáticos transladados por múltiplos de 0.05 (150 unidades CS2).

3. **Inexistência de Janelas Temporais nos Arquivos Parquet**:
   - No arquivo `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_000.parquet` (hash SHA-256 `7d387973188f257ec20d38a291d68d7cf50d1d4fa3d773d38076023e8fb50d43`), as colunas presentes são estritamente:
     `sequence_id`, `split`, `demo_id`, `round_index`, `slot`, `team`, `role`, `tactic_id`, `plan_stage`, `current_pos`, `assigned_catalog_id`, `semantic_type`, `confidence_weight`, `next_catalog_id`, `next_sector`, `expected_dwell_bucket`.
   - Nenhuma coluna armazena janelas temporais de 32 passos nem histórico pregresso.

4. **Comparação Determinística de 200 Amostras sob Seed 42026**:
   - Executada pelo script `.agents/teamwork/data_provenance_auditor_1/run_batch_comparison.py`.
   - 100 amostras de Train, 50 de Validation e 50 de Test foram extraídas deterministicamente via `np.random.RandomState(42026)`.
   - Os 200 arquivos `.npz` físicos correspondentes em `F:\\CS2_MLMove_Pipeline\\extracted_tensors\\de_mirage\\` foram lidos diretamente no disco.
   - Resultados empíricos computados:
     - ExactMatchRate (18 features): 0 / 200 (0.00%)
     - ExactMatchRate (coordenadas X, Y, Z): 0 / 200 (0.00%)
     - ToleranceMatchRate (todas as 18 features sob tolerâncias 1e-5 a 0.50): 0 / 200 (0.00%)
     - SyntheticWindowRate (drift linear): 200 / 200 (100.00%)
     - DL Y-Z StaticWindowRate: 200 / 200 (100.00%)
     - DL Features 3..17 StaticWindowRate: 200 / 200 (100.00%)
     - DL Teammates StaticWindowRate: 200 / 200 (100.00%)
     - Deslocamento Médio no DataLoader: exatamente 30.00 unidades CS2 (constante)
     - Deslocamento Médio no NPZ: 374.35 unidades CS2 (12,4 vezes superior)
     - Variância Temporal Espacial no DataLoader: 26.61 unidades²
     - Variância Temporal Espacial no NPZ: 37618.14 unidades² (1413,5 vezes superior)

5. **Entregáveis Materializados no Disco**:
   - `training_runs/positioning_v1/pre3a3_history_provenance.json` (SHA-256 `e483666c6d62040b912bf08c45afae7e8d17513388a387e5d767d5cf4e945bba`)
   - `training_runs/positioning_v1/pre3a3_history_provenance.md` (SHA-256 `b38c1578e29fd9b0eaf1793d9955c0313149367f1eb0ae34c67649a2059d161f`)
   - `pre3a3_npz_batch_comparison.json` (SHA-256 `5193ec06c8e93c8b0f59afa59132cb259d4153255793268d823cc3020c7fd0b1`)
   - `pre3a3_npz_batch_comparison.md` (SHA-256 `751fb780dd89e2ce0a0f82051f7af6db8fdf8e4eb5d2dab68f66c6acc9f95523`)

---

## 2. Logic Chain

1. **Premissa de Entrada**: O relatório executivo da Fase 2.2 afirmava que o DataLoader de posicionamento operava via MEMORY_MAPPED_INDEXED_WINDOW e que janelas temporais de 32 frames eram reconstruídas em batch a partir de índices nos dados de partida (Observação 1.3).
2. **Descoberta do Código**: A leitura de `tools/phase3a_training/train_full.py` demonstrou que o treino utilizou `tools/phase3a_training/data_utils.py:load_and_preprocess_shard`, e não o DataLoader declarado em `input_snapshot.json` (Observação 1.1).
3. **Análise de Construção do Tensor**: O código de `load_and_preprocess_shard` (Observação 1.2) aplica uma fórmula puramente sintética sobre uma coordenada pontual: soma `np.linspace(-0.01, 0.0, 32)` ao eixo X e deixa Y e Z constantes, sem acessar arquivos NPZ ou buffers temporais da partida.
4. **Verificação Experimental com 200 Amostras**: A comparação direta e determinística entre a saída desse DataLoader e a fatia temporal correspondente no arquivo NPZ (Observação 1.4) resultou em `ExactMatchRate = 0.0%`, `ToleranceMatchRate = 0.0%` e `SyntheticWindowRate = 100.0%`.
5. **Divergência Física**: O deslocamento real dos jogadores no NPZ (374,35 unidades) e a variância real (37.618 unidades²) são ordens de magnitude superiores à perturbação linear artificial (30,00 unidades e 26,61 unidades²), comprovando que o modelo nunca foi treinado para reconhecer dinâmicas temporais reais.
6. **Conclusão Inescapável**: Todas as três seeds (42026, 42027 e 42028), incluindo o modelo mestre oficial `models/positioning/de_mirage_positioning_v1.pt`, foram treinadas com histórico temporal sintético.

---

## 3. Caveats

1. **Preservação de Checkpoints**: Em cumprimento estrito ao Requisito R4 e às regras do usuário, os checkpoints existentes não foram excluídos nem modificados.
2. **Desempenho Estático vs. Temporal**: O fato de o histórico temporal ser sintético não anula o aprendizado espacial pontual das cabeças do modelo (as correlações entre posição instantânea e spots/setores permanecem válidas, embora a atenção temporal esteja condicionada ao drift artificial).
3. **Ausência de Retreino**: Nenhum retreino foi executado neste estágio, pois retreinamento está estritamente proibido nesta fase pré-3A.3.

---

## 4. Conclusion

- **Veredito Canônico**: **`CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`** (Opção B do Requisito R4).
- **Status do Requisito R3**: **PLENAMENTE ATENDIDO E DOCUMENTADO**.
- **Ação Recomendada**: Preservar os checkpoints como artefatos experimentais sob o selo `EXPERIMENTAL_SYNTHETIC_HISTORY`. Para a entrada formal na Fase 3A.3 ou deploy em runtime C#, planejar um retreino denso com janelas extraídas diretamente dos 444 arquivos `.npz`.

---

## 5. Verification Method

Para reproduzir e verificar de forma independente e determinística os resultados desta auditoria:

1. **Executar a Comparação dos 200 Lotes NPZ**:
   ```powershell
   python .agents/teamwork/data_provenance_auditor_1/run_batch_comparison.py
   ```
   *Condição de Invalidação*: Se `ExactMatchRate > 0.0%` ou `SyntheticWindowRate < 100.0%`.

2. **Verificar os Hashes SHA-256 dos Quatro Entregáveis no Disco**:
   ```powershell
   Get-FileHash -Algorithm SHA256 training_runs/positioning_v1/pre3a3_history_provenance.json
   Get-FileHash -Algorithm SHA256 training_runs/positioning_v1/pre3a3_history_provenance.md
   Get-FileHash -Algorithm SHA256 pre3a3_npz_batch_comparison.json
   Get-FileHash -Algorithm SHA256 pre3a3_npz_batch_comparison.md
   ```

3. **Verificar Compilação Sintática (`py_compile`)**:
   ```powershell
   python -m py_compile .agents/teamwork/data_provenance_auditor_1/run_batch_comparison.py .agents/teamwork/data_provenance_auditor_1/generate_history_provenance.py
   ```
