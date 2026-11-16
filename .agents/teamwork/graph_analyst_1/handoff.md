# Handoff Report — Graph Analyst (Explorer 2)

- **Fase / Marco**: Pré-Fase 3A.3 / Requisito R2 — Mapeamento Graphify do Fluxo de Histórico Temporal e Blast Radius
- **Autor**: Graph Analyst (Explorer 2)
- **Tipo de Handoff**: Hard Handoff (Tarefa Concluída)
- **Veredito Canônico de Provêniencia**: `B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`
- **Classificação de Validação**: `AGENT_REVIEWED`
- **Data e Hora UTC**: 2026-11-07T21:20:00Z
- **Diretório do Agente**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\graph_analyst_1`
- **Artefatos Entregues**:
  1. `.agents/audit/pre3a3_temporal_history_graph.md` (SHA-256: `f726a91b53c780b92b7c38ebed3275deaa1df41f075d9b5c65d9c6657fd8a6c3`)
  2. `.agents/audit/pre3a3_temporal_history_blast_radius.json` (SHA-256: `7de3a63af87a85fb4d43b41c146bf11706abdecc50f1d2b3708508e89de88d9f`)

---

## 1. Observation

Durante a investigação puramente somente-leitura sobre o repositório e a base Graphify (`graphify-out/graph.json`), foram observados os seguintes fatos físicos diretamente no código e nos artefatos:

1. **Localização e Shape dos Arquivos NPZ Brutos**:
   - Diretório: `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\`
   - Contagem: 444 arquivos `.npz` materializados no disco.
   - Chaves internas: `['X', 'Y']` com `X.shape = (num_frames, 10, 18)` em `float32` e `Y.shape = (num_frames, 10, 3)`.
2. **Ponto de Leitura de NPZ na Fase 2**:
   - Arquivo: `tools/phase2_dataset/step9_to_18_build_datasets.py`
   - Linhas 108-112: `with np.load(fpath) as data: X = data["X"]; Y = data["Y"]`.
   - Linha 268: O script grava nos arquivos Parquet (`shard_*.parquet`) exclusivamente a coordenada instantânea pontual:
     ```python
     "current_pos": [round(cur_x, 1), round(cur_y, 1), round(cur_z, 1)],
     ```
     Nenhuma janela temporal anterior ao frame `f_idx` foi gravada em Parquet.
3. **Ausência Absoluta de Carga de NPZ no Treinamento da Fase 3A**:
   - Arquivos: `tools/phase3a_training/data_utils.py`, `tools/phase3a_training/train_full.py`, `tools/phase3a_training/train_pilot.py`, `tools/phase3a_training/dry_run.py`, `tools/phase3a_training/evaluate_positioning_v1_canonical.py`.
   - Resultado: Nenhuma chamada a `np.load` ou referência a arquivos `.npz` existe nesses arquivos. A busca textual e por AST retornou exatamente 0 correspondências (0/5 scripts).
4. **Construção Sintética dos Tensores no DataLoader Real de Treino**:
   - Arquivo: `tools/phase3a_training/data_utils.py`
   - Função: `load_and_preprocess_shard` (L191-L309)
   - Linha 215: `pos_arr = np.array(df["current_pos"].tolist(), dtype=np.float32) # [N, 3]`
   - Linhas 218-224: `history_arr = np.zeros((n, 32, 18), dtype=np.float32)` preenchendo colunas 0..2 com `pos_arr / 3000.0`, coluna 3 com `1.0` e coluna 4 com `1.0`.
   - Linhas 226-227:
     ```python
     step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1)
     history_arr[:, :, 0] += step_drift[:, :, 0]
     ```
   - Linhas 230-238:
     ```python
     teammates_arr = np.zeros((n, 32, 4, 18), dtype=np.float32)
     for i in range(4):
         offset = (i + 1) * 0.05
         teammates_arr[:, :, i, 0] = (pos_arr[:, 0:1] / 3000.0) + offset
         teammates_arr[:, :, i, 1] = (pos_arr[:, 1:2] / 3000.0) - offset
         teammates_arr[:, :, i, 2] = (pos_arr[:, 2:3] / 3000.0)
         teammates_arr[:, :, i, 3] = 1.0
         teammates_arr[:, :, i, 4] = 1.0
     ```
   - Features 5 a 17 de `history_arr` e `teammates_arr`: Permanecem exatamente 0.0 em todos os 32 frames.
5. **DataLoader Auditado na Fase 2.2**:
   - Arquivo: `tools/phase2_dataset/dataloaders.py`
   - Classe: `PositioningDatasetV1` (L36-L109)
   - Linhas 72-77: Preenche `history` com `cur_pos / 3000.0` nos 32 timesteps SEM drift linear (`std == 0`).
   - Linha 80: Preenche `teammates = np.zeros((32, 4, 18), dtype=np.float32)` (100% zerado).
   - Não fornece `team_idx`, `role_idx`, `stage_idx`, `transition` ou `exit_trigger`.
6. **Uniformidade de Caminho entre Splits**:
   - `train_full.py` (L316-L317) carrega `train` e `validation` chamando `create_dataset_from_shards`, que executa `load_and_preprocess_shard`.
   - `evaluate_positioning_v1_canonical.py` (L83) carrega `test` chamando `load_and_preprocess_shard(test_parquet_path, spot_to_idx)`.
   - `build_and_evaluate_challenge_set.py` (L151) e `finetune_state_head.py` (L378) carregam `challenge_v2` chamando `load_and_preprocess_shard`.
   - Todos os splits (4/4) receberam o mesmo gerador sintético.
7. **Narrativa Ficcional em Relatórios Pré-existentes**:
   - Arquivo: `datasets/mirage_v2/parquet_physical_schema_audit.json`
   - Linhas 5, 26, 31: Afirma que o DataLoader reconstrói janelas temporais usando ponteiros exatos nos arquivos NPZ via `"MEMORY_MAPPED_INDEXED_WINDOW"` e `"NPZ_RECONSTRUCTED_AT_BATCH_TIME"`. Essa mecânica nunca foi codificada no pipeline de treinamento.
8. **Hashes SHA-256 Verificados no Disco**:
   - `tools/phase2_dataset/step9_to_18_build_datasets.py`: `81aa57a2c2e34aa785aeab67a5ccdca498247c5f39f322c5f9f9997b60e05b25`
   - `tools/phase2_dataset/dataloaders.py`: `921836c8a9c4590f91a2ed3aa8da090a4470878bb8f6e66a8dc25997d198183d`
   - `tools/phase2_dataset/forensic_step4_temporal_windows.py`: `c553f1df4837f5d950d1febd266a0f5bd7504be2a09089ea64f2c3f315b84136`
   - `tools/phase3a_training/data_utils.py`: `d15c234e3a2ce73fe01663293b60a8a53166d73e8caf40254b36eef2e4ec8e45`
   - `tools/phase3a_training/positioning_model.py`: `d98b6e4526a18a32a31702f88825899c950189a4243d365fb25cab0064371e9b`
   - `tools/phase3a_training/train_full.py`: `ef9c32d386346dca33fda0b8ff274b2efab09585e53c95405de08481ac02b0d9`
   - `tools/phase3a_training/evaluate_positioning_v1_canonical.py`: `1751469a8a43619e9d7c309fa79abf49f3d518efd5d173b99f13f8372fe1bf93`
   - `tools/phase3a_training/dry_run.py`: `df7893fee3c1b875230b012974334548a9aa482285f4699b2ffbe225601f4c54`
   - `models/positioning/de_mirage_positioning_v1.pt`: `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0`
   - `training_runs/positioning_v1/seed_42026/best_checkpoint.pt`: `d7dc58ef216935d5c8202b3e4395ef5c0a80c790984a9758612031a17aaf79d0`
   - `training_runs/positioning_v1/seed_42027/best_checkpoint.pt`: `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0`
   - `training_runs/positioning_v1/seed_42028/best_checkpoint.pt`: `af99069189952aef0fe2a9070d328dd2179b131b046501036b4bfb0c590c779e`
   - `graphify-out/graph.json`: `7a09693f1f6568803fa7f2ae7a0286cbe38c09f3900d08b96c6538f4eaa264f0`

---

## 2. Logic Chain

1. **Premissa 1 (Observação 2 e 3)**: Se os shards Parquet contêm apenas `current_pos` e os scripts de treinamento da Fase 3A não importam `np.load` nem leem arquivos `.npz`, então nenhuma janela temporal densa pré-existente nos arquivos NPZ físicos foi utilizada no treinamento do modelo.
2. **Premissa 2 (Observação 4)**: Se o tensor `self_history` entregue ao modelo `PositioningTransformerV1.forward` é gerado por `pos_arr + np.linspace(-0.01, 0.0, 32)` em X com Y, Z estáticos e `teammates_arr` é composto por clones escalonados com offset `(i+1)*0.05`, então os dados temporais consumidos pelas camadas de atenção do Transformer durante o backward são de natureza sintética e templada.
3. **Premissa 3 (Observação 6)**: Se os splits `train`, `validation`, `test` e `challenge_v2` foram todos processados pela mesma função `load_and_preprocess_shard`, então nenhum split possui histórico temporal real e a validação do modelo foi realizada sobre a mesma distribuição sintética do treino.
4. **Premissa 4 (Observação 7)**: Se os relatórios anteriores alegavam que os DataLoaders reconstruíam janelas temporais diretamente dos NPZ via ponteiros indexados, mas essa rotina inexiste no código-fonte, trata-se de um achado documental crítico de desacoplamento entre documentação e implementação.
5. **Conclusão Lógica**: O checkpoint mestre `models/positioning/de_mirage_positioning_v1.pt` e os checkpoints das seeds 42026, 42027 e 42028 foram treinados com histórico temporal sintético. O veredito canônico para R4 é categoricamente **`B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**.

---

## 3. Caveats

- **Integridade Física dos Arquivos NPZ**: Os 444 arquivos `.npz` existem fisicamente no disco em `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\` e contêm locomoção contínua autêntica a 16Hz. Eles não foram apagados ou corrompidos; o problema reside exclusivamente no fato de que o pipeline de posicionamento da Fase 3A não os consumiu.
- **Outras Cabeças do Modelo**: As cabeças `head_spot` (CandidateSpotRanking) e `head_sector` (NextSector) operam fortemente sobre a coordenada pontual `current_pos / 3000.0` e rótulos de mapas (`assigned_catalog_id`), explicando a convergência satisfatória dessas heads apesar da ausência de histórico temporal real.
- **Escopo Read-Only**: Em estrita observância à governança e às restrições do Explorer 2, nenhum código-fonte, modelo ou checkpoint foi alterado ou retreinado.

---

## 4. Conclusion

1. **Requisito R2 Plenamente Cumprido**: O fluxo completo `NPZ → DataLoader → self_history → teammate_history → PositioningTransformerV1.forward → checkpoint` foi rastreado e mapeado com precisão cirúrgica de arquivos e números de linhas.
2. **Artefatos Canônicos Materializados**:
   - `.agents/audit/pre3a3_temporal_history_graph.md` (SHA-256: `f726a91b53c780b92b7c38ebed3275deaa1df41f075d9b5c65d9c6657fd8a6c3`)
   - `.agents/audit/pre3a3_temporal_history_blast_radius.json` (SHA-256: `7de3a63af87a85fb4d43b41c146bf11706abdecc50f1d2b3708508e89de88d9f`)
3. **Decisão do Checkpoint para a Equipe**: O veredito canônico é **`B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**. Os checkpoints devem ser preservados como experimentais e o retreinamento com extração temporal real dos NPZ é formalmente recomendado para fases futuras.

---

## 5. Verification Method

Para reproduzir e verificar independentemente estas conclusões no workspace CsBot:

1. **Verificação de Ausência de Carga de NPZ no Treinamento**:
   ```powershell
   Select-String -Path "tools/phase3a_training/*.py" -Pattern "np\.load|\.npz"
   ```
   *Condição de Validação*: Apenas `audit_errors_and_episodes.py` (npy de logits), `extract_objective_save_events.py` (script offline auxiliar) e `generate_canonical_confusion_pdf.py` retornam ocorrências; `train_full.py` e `data_utils.py` retornam zero correspondências.
2. **Verificação da Chamada de `np.linspace` no DataLoader**:
   ```powershell
   Get-Content -Path "tools/phase3a_training/data_utils.py" | Select-String -Pattern "linspace" -Context 2,2
   ```
   *Condição de Validação*: Exibe a linha 226 `step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1)`.
3. **Verificação de Hashes SHA-256 dos Artefatos Entregues**:
   ```powershell
   Get-FileHash -Algorithm SHA256 ".agents/audit/pre3a3_temporal_history_graph.md", ".agents/audit/pre3a3_temporal_history_blast_radius.json"
   ```
   *Condição de Validação*: Hashes idênticos a `f726a91b53c780b92b7c38ebed3275deaa1df41f075d9b5c65d9c6657fd8a6c3` e `7de3a63af87a85fb4d43b41c146bf11706abdecc50f1d2b3708508e89de88d9f`.
4. **Condição de Invalidação**:
   - Se for comprovado que `tools/phase3a_training/train_full.py` ou `data_utils.py` lê tensores históricos dos 444 arquivos `.npz` a cada lote de treinamento, o veredito B estaria invalidado.
