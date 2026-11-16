# Relatório Canônico de Mapeamento Graphify do Fluxo de Histórico Temporal

- **Fase**: Pré-Fase 3A.3 / Requisito R2
- **Autor / Auditor**: Graph Analyst (Explorer 2)
- **Modo**: Somente Leitura (Read-Only Architectural Investigation)
- **Classificação Canônica da Validação**: `AGENT_REVIEWED`
- **Veredito Canônico do Fluxo**: `CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`
- **Data e Hora UTC**: 2026-11-07T21:10:00Z
- **Base de Conhecimento Utilizada**: `graphify-out/graph.json` (SHA-256: `7a09693f1f6568803fa7f2ae7a0286cbe38c09f3900d08b96c6538f4eaa264f0`)
- **Artefato JSON Complementar**: `.agents/audit/pre3a3_temporal_history_blast_radius.json`

---

## 1. Sumário Executivo

A investigação arquitetural determinística e forense conduzida pelo Graph Analyst sobre a base de conhecimento do Graphify (`graphify-out/graph.json`) e o código-fonte do repositório concluiu conclusivamente que:

1. **Inexistência de Carga de NPZ no Treinamento**: Os 444 arquivos `.npz` de locomoção contínua a 16Hz (armazenados em `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\`, contendo tensores `X` de shape `[num_frames, 10, 18]`) foram lidos uma única vez durante a Fase 2 (`tools/phase2_dataset/step9_to_18_build_datasets.py:L108-L115`), onde **apenas um vetor de posição pontual `current_pos = [cur_x, cur_y, cur_z]` no frame amostrado foi salvo no arquivo Parquet** (`shard_*.parquet`, L268). Os 32 frames históricos anteriores do tensor `X` **nunca foram persistidos em Parquet nem lidos durante o treinamento**.
2. **Fabricação Sintética de Histórico no DataLoader**: Durante o treinamento do `PositioningTransformerV1` nas seeds 42026, 42027 e 42028 (`tools/phase3a_training/train_full.py`), a função `tools/phase3a_training/data_utils.py:load_and_preprocess_shard` (L217-L238) **sintetizou artificialmente** o histórico do jogador (`self_history` `[N, 32, 18]`) repetindo a posição do tick atual nos 32 timesteps e adicionando um drift linear fixo `step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32)` no eixo X (L226-L227), mantendo as features 5..17 zeradas.
3. **Companheiros de Equipe Fictícios (Clones Deslocados)**: O tensor de aliados `teammate_history` `[N, 32, 4, 18]` foi sintetizado clonando a posição do próprio jogador e somando offsets escalonados `(i + 1) * 0.05` para cada aliado `i` nos 32 passos (L231-L238), sem qualquer relação com a posição ou trajetória real dos aliados da partida.
4. **Discrepância Estrutural entre DataLoaders**: O DataLoader auditado na Fase 2.2 (`tools/phase2_dataset/dataloaders.py:PositioningDatasetV1`) gerava `history` puramente estático (`cur_pos / 3000.0` sem drift, `std == 0`) e `teammates` inteiramente preenchido com zeros. Já o DataLoader real de treinamento da Fase 3A (`tools/phase3a_training/data_utils.py:InMemoryPositioningDataset`) substituiu o DataLoader anterior, introduzindo o drift linear de `np.linspace` e companheiros sintéticos com offset.
5. **Uniformidade Falsa entre Splits**: Todos os splits (`train`, `validation`, `test` canônico e `challenge_v2`) utilizaram rigorosamente o mesmo gerador sintético (`load_and_preprocess_shard`). Janelas temporais reais da partida **existiam exclusivamente em documentação narrativa e relatórios executivos** (notadamente em `datasets/mirage_v2/parquet_physical_schema_audit.json`), mas nunca integraram o grafo computacional de treinamento ou avaliação.

---

## 2. Diagrama do Grafo Arquitetural do Fluxo Temporal

O grafo abaixo mapeia o fluxo físico real verificado no repositório versus a camada de documentação fictícia:

```
[444 Arquivos .npz em Disco F:\] (REAL, F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\)
       │
       ▼  (Leitura pontual em tools/phase2_dataset/step9_to_18_build_datasets.py:L108)
       │  (Apenas current_pos [x,y,z] gravado; NENHUMA janela temporal salva em Parquet)
       ▼
[datasets/mirage_v2/positioning/positioning_sequences_v1/shard_*.parquet] (REAL, 6 shards)
       │
       ├─── [Relatório Parquet Schema Audit] ───► AFIRMAÇÃO FICÇÃO: "MEMORY_MAPPED_INDEXED_WINDOW"
       │                                         (datasets/mirage_v2/parquet_physical_schema_audit.json:L26)
       │                                         (Nunca materializada em código executável)
       │
       ├──► [Fase 2.2 DataLoader Audit] 
       │    └── tools/phase2_dataset/dataloaders.py:PositioningDatasetV1 (L66-L109)
       │        ├── self_history: [32, 18] -> cur_pos repetido 32x (std == 0, sem np.linspace)
       │        └── teammate_history: [32, 4, 18] -> 100% zeros (np.zeros)
       │
       └──► [Fase 3A DataLoader Real de Treino e Avaliação]
            └── tools/phase3a_training/data_utils.py:load_and_preprocess_shard (L191-L309)
                ├── self_history: [N, 32, 18] -> cur_pos + np.linspace(-0.01, 0.0, 32) (L226-L227)
                ├── teammate_history: [N, 32, 4, 18] -> cur_pos + offset (i+1)*0.05 (L231-L238)
                └── categorical: team_idx, role_idx, stage_idx
                     │
                     ▼
            [InMemoryPositioningDataset] (tools/phase3a_training/data_utils.py:L139)
                     │
                     ▼  (Batch size 64 em tools/phase3a_training/train_full.py:L121)
            [PositioningTransformerV1.forward] (tools/phase3a_training/positioning_model.py:L136)
                     ├── player_proj: Linear(18, 192) consome self_history sintético
                     ├── teammate_proj: Linear(18, 192) consome teammate_history sintético
                     ├── TransformerEncoder: 3 camadas, 6 heads, GELU
                     └── 5 Heads Multitarefa (State, Sector, Spot, Transition, ExitTrigger)
                               │
                               ▼
            [Checkpoints Treinados]
            ├── training_runs/positioning_v1/seed_42026/best_checkpoint.pt
            ├── training_runs/positioning_v1/seed_42027/best_checkpoint.pt
            ├── training_runs/positioning_v1/seed_42028/best_checkpoint.pt
            └── models/positioning/de_mirage_positioning_v1.pt (Mestre = Seed 42027)
```

---

## 3. Identificação Cirúrgica dos 6 Componentes de Código

### 3.1 Função Exata de Carga de NPZ

No ciclo de vida do projeto, a carga de arquivos NPZ foi identificada exclusivamente em dois locais:

1. **Construção dos Datasets Parquet (Fase 2, Passos 9-18)**:
   - **Arquivo**: `tools/phase2_dataset/step9_to_18_build_datasets.py`
   - **Linhas**: 108 a 115
   - **Código verbatim**:
     ```python
     108:         try:
     109:             with np.load(fpath) as data:
     110:                 X = data["X"]
     111:                 Y = data["Y"]
     112:                 n_frames = X.shape[0]
     ```
   - **Destino dos dados**: Na linha 268, o script armazena estritamente a posição instantânea:
     ```python
     268:                 "current_pos": [round(cur_x, 1), round(cur_y, 1), round(cur_z, 1)],
     ```
     Nenhuma janela de histórico anterior a `f_idx` foi extraída do array `X` para o posicionamento tático.
2. **Mineração Offline de Eventos Raros (Fase 3A.2)**:
   - **Arquivo**: `tools/phase3a_training/extract_objective_save_events.py`
   - **Linhas**: 131 a 135
   - **Função**: Leitura offline auxiliar para extrair frames de plant e save.
3. **Pipeline de Treinamento e Avaliação do Positioning Transformer (Fase 3A)**:
   - **Resultado da Auditoria**: **NENHUMA** função de carga de NPZ existe em `tools/phase3a_training/data_utils.py`, `train_full.py`, `train_pilot.py`, `dry_run.py` ou `evaluate_positioning_v1_canonical.py`. A busca textual e de AST por `np.load` ou `.npz` nesses módulos retorna **0 correspondências (0/5 scripts)**.

---

### 3.2 Função Construtora de Janelas Temporais

A construção da janela temporal entregue ao modelo ocorre em:

- **Arquivo**: `tools/phase3a_training/data_utils.py`
- **Função**: `load_and_preprocess_shard` (L191-L309)
- **Linhas de Construção**: 217 a 238
- **Código verbatim**:
  ```python
  217:     # Histórico temporal [N, 32, 18]
  218:     history_arr = np.zeros((n, 32, 18), dtype=np.float32)
  219:     history_arr[:, :, 0] = (pos_arr[:, 0:1] / 3000.0)
  220:     history_arr[:, :, 1] = (pos_arr[:, 1:2] / 3000.0)
  221:     history_arr[:, :, 2] = (pos_arr[:, 2:3] / 3000.0)
  222:     history_arr[:, :, 3] = 1.0 # Health normalizado
  223:     history_arr[:, :, 4] = 1.0 # Is alive
  224: 
  225:     # Trajetória suave nos últimos passos
  226:     step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1)
  227:     history_arr[:, :, 0] += step_drift[:, :, 0]
  228: 
  229:     # Teammates [N, 32, 4, 18]
  230:     teammates_arr = np.zeros((n, 32, 4, 18), dtype=np.float32)
  231:     for i in range(4):
  232:         offset = (i + 1) * 0.05
  233:         teammates_arr[:, :, i, 0] = (pos_arr[:, 0:1] / 3000.0) + offset
  234:         teammates_arr[:, :, i, 1] = (pos_arr[:, 1:2] / 3000.0) - offset
  235:         teammates_arr[:, :, i, 2] = (pos_arr[:, 2:3] / 3000.0)
  236:         teammates_arr[:, :, i, 3] = 1.0
  237:         teammates_arr[:, :, i, 4] = 1.0
  ```

---

### 3.3 Linha Exata e Contexto de Chamada de `np.linspace`

- **Arquivo**: `tools/phase3a_training/data_utils.py`
- **Linha Exata**: **Linha 226**
- **Linha de Aplicação**: **Linha 227**
- **Código literal**:
  ```python
  226:     step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1)
  227:     history_arr[:, :, 0] += step_drift[:, :, 0]
  ```
- **Contexto Operacional**:
  - `step_drift` gera um vetor 1D linear de 32 pontos iniciando em `-0.01` e terminando em `0.0`.
  - Esse deslocamento linear constante é adicionado exclusivamente à coordenada X normalizada do jogador.
  - As coordenadas Y e Z permanecem perfeitamente planas/estáticas ao longo de todos os 32 frames (`std == 0`).
  - As features 3 (Health) e 4 (Is Alive) são forçadas como `1.0` constante.
  - As features 5 a 17 (Yaw, Pitch, Velocidades, Armas, etc.) são deixadas integralmente com `0.0`.
- **Classificação Canônica de R4**: `UNLABELED_SYNTHETIC_INPUT`.
- **Alcance**: Esse tensor gerado na linha 226 alcança diretamente o forward de treino (Loss de treino), validação (Loss de validação e seleção de checkpoint) e teste canônico.

#### Inventário Completo de Ocorrências de `linspace` no Repositório

| Arquivo | Linha | Função / Escopo | Expressão | Classificação | Reaches Model Input? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tools/phase3a_training/data_utils.py` | 226 | `load_and_preprocess_shard` | `np.linspace(-0.01, 0.0, 32, ...)` | `UNLABELED_SYNTHETIC_INPUT` | **SIM (Treino, Val, Test)** |
| `tools/phase3a_training/reconcile_ablation_and_calibration.py` | 37 | `compute_ece` | `np.linspace(0.0, 1.0, num_bins + 1)` | `LEGITIMATE_INTERPOLATION` | Não (Métrica ECE) |
| `tools/phase3a_training/reconcile_ablation_and_calibration.py` | 71 | `compute_adaptive_ece` | `np.linspace(0, 100, num_bins + 1)` | `LEGITIMATE_INTERPOLATION` | Não (Quantis ECE) |
| `tools/phase3a_training/reconcile_ablation_and_calibration.py` | 324 | `main` | `np.linspace(0.5, 3.0, 51)` | `LEGITIMATE_INTERPOLATION` | Não (Temperature Grid) |
| `tools/phase3a_training/evaluate.py` | 287 | `plot_calibration_curve` | `np.linspace(0.0, 1.0, 11)` | `REPORT_ONLY` | Não (Plot de calibração) |
| `tools/phase3a_training/finetune_state_head.py` | 325 | `expected_calibration_error` | `torch.linspace(0, 1, n_bins + 1)` | `LEGITIMATE_INTERPOLATION` | Não (Bins de calibração) |

---

### 3.4 Tensor Exato Entregue ao Modelo `PositioningTransformerV1.forward`

No arquivo `tools/phase3a_training/positioning_model.py` (L136-L206), a assinatura do método `forward` recebe:

```python
def forward(
    self,
    history: torch.Tensor,        # [B, 32, 18]
    teammates: torch.Tensor,      # [B, 32, 4, 18]
    candidate_mask: torch.Tensor, # [B, 53] (bool)
    team_idx: torch.Tensor,       # [B]
    role_idx: torch.Tensor,       # [B]
    stage_idx: torch.Tensor       # [B]
)
```

A composição detalhada dos tensores entregues é especificada na tabela a seguir:

| Tensor | Shape | Dtype | Natureza | Composição Exata das Dimensões | Variância Temporal |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `history` | `[B, 32, 18]` | `torch.float32` | `TEMPLATED_AND_SYNTHETIC` | Feat 0: `(pos_x/3000.0) + linspace(-0.01, 0.0, 32)`<br>Feat 1: `pos_y/3000.0`<br>Feat 2: `pos_z/3000.0`<br>Feat 3: `1.0` (Health)<br>Feat 4: `1.0` (IsAlive)<br>Feat 5..17: `0.0` | Feat 0: Artificial linear (`std > 0`)<br>Feats 1..17: Zero absoluto (`std == 0`) |
| `teammates` | `[B, 32, 4, 18]` | `torch.float32` | `SYNTHETIC` | Para cada aliado `i \in {0..3}`:<br>Feat 0: `(pos_x/3000.0) + (i+1)*0.05`<br>Feat 1: `(pos_y/3000.0) - (i+1)*0.05`<br>Feat 2: `pos_z/3000.0`<br>Feat 3..4: `1.0`<br>Feat 5..17: `0.0` | Zero absoluto nos 32 passos de tempo para os 4 aliados (`std == 0`) |
| `candidate_mask` | `[B, 53]` | `torch.bool` | `SYNTHETIC` | 100% dos 53 bits ativos como `True` (`np.ones((n, 53), dtype=bool)`) | N/A (Estático) |
| `team_idx` | `[B]` | `torch.int64` | `REAL` | Mapeado de `df["team"]`: CT=0, TR=1, ANY=2 | N/A |
| `role_idx` | `[B]` | `torch.int64` | `INFERRED` | Mapeado de `df["role"]` via heurística de compra | N/A |
| `stage_idx` | `[B]` | `torch.int64` | `INFERRED` | Mapeado de `df["plan_stage"]` via percentual de tempo | N/A |

---

### 3.5 Diferença Exata entre o DataLoader da Fase 2.2 e o DataLoader Real de Treino

A investigação identificou uma bifurcação estrutural entre o DataLoader homologado no relatório da Fase 2.2 e o DataLoader que de fato executou o treinamento das seeds na Fase 3A:

| Dimensão de Comparação | DataLoader Auditado na Fase 2.2 (`dataloaders.py:PositioningDatasetV1`) | DataLoader Real de Treino na Fase 3A (`data_utils.py:InMemoryPositioningDataset`) | Impacto Arquitetural |
| :--- | :--- | :--- | :--- |
| **Módulo e Classe** | `tools/phase2_dataset/dataloaders.py`<br>`PositioningDatasetV1` | `tools/phase3a_training/data_utils.py`<br>`InMemoryPositioningDataset` | Código de produção da Fase 2.2 foi ignorado no treino |
| **Padrão de I/O** | `__getitem__` sob demanda iterando sobre Pandas DataFrame | Pré-carregamento total em tensores PyTorch na memória RAM (`create_dataset_from_shards`) | Otimização de vazão de GPU/CPU |
| **Histórico do Jogador (`self_history`)** | `history[:, 0..2] = cur_pos / 3000.0`<br>`history[:, 3..4] = 1.0`<br>`np.linspace` **NÃO é chamado**.<br>Variância temporal nas 32 posições: `std == 0`. | `history_arr[:, :, 0] += step_drift`<br>Aplica `np.linspace(-0.01, 0.0, 32)` ao eixo X.<br>Variância temporal em X: artificial constante. | O drift linear foi introduzido exclusivamente na Fase 3A |
| **Features de Aliados (`teammate_history`)** | `teammates = np.zeros((32, 4, 18))` (Matriz **100% zerada**) | Sintetiza 4 aliados fictícios aplicando offsets fixos `(i+1)*0.05` em X e Y | Aliados fictícios introduzidos na Fase 3A |
| **Contexto Categórico** | Nenhum (`team_idx`, `role_idx`, `stage_idx` não existiam) | Tensores `team_idx`, `role_idx`, `stage_idx` incorporados | Modelo da Fase 2.2 não suportava embeddings categóricos |
| **Cabeças Supervisionadas** | 3 cabeças (`positioning_state`, `next_sector`, `candidate_spot_idx`) | 5 cabeças (+ `transition` e `exit_trigger`) | Expansão de objetivos multitarefa na Fase 3A |

---

### 3.6 Unicidade do Caminho entre Splits e Inexistência de Janelas Reais

A auditoria verificou o fluxo de dados para todos os splits avaliados no projeto CsBot:

1. **Split `train`**:
   - Carregado por `tools/phase3a_training/train_full.py:L316` via `create_dataset_from_shards(ds_dir, split="train", max_samples=16000)`.
   - Executa `load_and_preprocess_shard`, recebendo `np.linspace` e aliados sintéticos.
2. **Split `validation`**:
   - Carregado por `tools/phase3a_training/train_full.py:L317` via `create_dataset_from_shards(ds_dir, split="validation", max_samples=4000)`.
   - Executa `load_and_preprocess_shard`, recebendo `np.linspace` e aliados sintéticos.
3. **Split `test` Canônico**:
   - Carregado por `tools/phase3a_training/evaluate_positioning_v1_canonical.py:L83` via `load_and_preprocess_shard(test_parquet_path, spot_to_idx)`.
   - Executa rigorosamente o mesmo código com `np.linspace` e aliados sintéticos.
4. **Split `challenge_v2`**:
   - Carregado por `tools/phase3a_training/build_and_evaluate_challenge_set.py:L151` e `finetune_state_head.py:L378` via `load_and_preprocess_shard`.
   - Executa o mesmo código com `np.linspace`.

**Conclusão sobre a Unicidade de Caminho**:
- **Train, Validation, Test e Challenge compartilharam exatamente o mesmo caminho de montagem de tensores sintéticos**.
- **Não houve caminho alternativo**: Nenhuma ramificação condicional (`if split == 'test'`) utilizou tensores temporais reais do NPZ.
- **Janelas temporais reais existiam apenas nos relatórios**: O texto do relatório `datasets/mirage_v2/parquet_physical_schema_audit.json` afirmando que o DataLoader operava via *"MEMORY_MAPPED_INDEXED_WINDOW"* e *"NPZ_RECONSTRUCTED_AT_BATCH_TIME"* era uma declaração de intenção arquitetural não implementada no código de treinamento.

---

## 4. As 10 Dimensões de Mapeamento de Impacto (`csbot-graph-impact`)

Em estrito cumprimento à Skill `csbot-graph-impact`, as 10 dimensões arquiteturais para o fluxo do Positioning Transformer são:

1. **`entry_points`**:
   - `tools/phase3a_training/train_full.py:run_full_training` (L302-L378)
   - `tools/phase3a_training/train_full.py:train_single_seed` (L62-L300)
   - `tools/phase3a_training/evaluate_positioning_v1_canonical.py:run_canonical_inference` (L47-L222)
   - `tools/phase3a_training/finetune_state_head.py:main` (L362-L610)
   - `tools/phase3a_training/dry_run.py:main` (L30-L202)
2. **`writers`**:
   - `tools/phase2_dataset/step9_to_18_build_datasets.py:build_datasets_and_reports` (L22-L519; grava coordenadas isoladas no Parquet)
   - `tools/phase3a_training/data_utils.py:load_and_preprocess_shard` (L191-L309; sintetiza tensores `history` e `teammates`)
   - `tools/phase3a_training/train_full.py:train_single_seed` (L62-L300; otimiza os pesos neurais através da loss)
   - `tools/phase3a_training/train_full.py:run_full_training` (L302-L378; persiste `models/positioning/de_mirage_positioning_v1.pt`)
3. **`readers`**:
   - `tools/phase3a_training/positioning_model.py:PositioningTransformerV1.forward` (L136-L206)
   - `tools/phase3a_training/positioning_model.py:PositioningMultitaskLoss.forward` (L228-L280)
   - `tools/phase3a_training/evaluate_positioning_v1_canonical.py` (L47-L222)
   - `tools/phase3a_training/finetune_state_head.py` (L362-L610)
   - `tools/phase3a_training/reconcile_ablation_and_calibration.py` (L115-L350)
   - `src/CsBotManager/CsBotManagerPlugin.cs` (Consumidor downstream planejado em C#)
4. **`authoritative_state`**:
   - `models/positioning/de_mirage_positioning_v1.pt:model_state_dict` (Pesos mestre atuais)
   - `training_runs/positioning_v1/seed_42027/best_checkpoint.pt:model_state_dict` (Origem da seed vencedora)
   - `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_*.parquet` (Verdade das anotações supervisionadas)
5. **`fallbacks`**:
   - `tools/phase3a_training/positioning_model.py:PositioningTransformerV1.forward` (L159-L165; preenchimento com zeros para categorias nulas)
   - `tools/phase3a_training/positioning_model.py:PositioningTransformerV1.forward` (L190-L197; penalização `-1e9` na máscara de spots)
   - `src/CsBotManager/MapProfileManager.cs` (Fallback C# determinístico para spots fixos de `de_mirage.json`)
6. **`caches`**:
   - `tools/phase3a_training/data_utils.py:InMemoryPositioningDataset` (Cache em memória RAM de todos os tensores)
   - `models/positioning/de_mirage_positioning_v1.pt` (Cache persistido no disco do melhor modelo)
7. **`side_effects`**:
   - **Vício de Representação**: As projeções lineares `player_proj` e `teammate_proj` do Transformer aprenderam pesos condicionados a um gradiente fixo de inclinação linear de -0.01 a 0.0 no eixo X.
   - **Incompatibilidade com Dados Reais**: Se tensores reais de 16Hz (com ruído físico de passo, saltos e acelerações) forem injetados na rede sem retreino, a distribuição das atenções será severamente perturbada.
   - **Invalidade das Métricas de Validação/Teste**: As métricas de acurácia, F1 e MRR obtidas nos relatórios da Fase 3A foram mensuradas sobre esses tensores fabricados.
8. **`telemetry`**:
   - `training_runs/positioning_v1/seed_*/metrics_train.jsonl`
   - `training_runs/positioning_v1/seed_*/metrics_validation.jsonl`
   - `training_runs/positioning_v1/seed_*/training_log.txt`
   - `training_runs/positioning_v1/best_model_selection.json`
9. **`tests`**:
   - `tests/test_phase3a_positioning_training.py`
   - `tests/test_phase3a_1_forensic_reconciliation.py`
   - `tests/test_phase3a_2_objective_save_enrichment.py`
10. **`blast_radius`**:
    - Todos os 10 checkpoints de treinamento (`models/positioning/*.pt`, `training_runs/positioning_v1/**/*.pt`).
    - Todos os relatórios de avaliação de desempenho da Fase 3A.
    - Scripts de exportação ONNX e integração em runtime C# (quando forem materializados na Fase 3A.3).

---

## 5. Matriz de Evidências Brutas e Hashes SHA-256 Verificados no Disco

Todos os arquivos abaixo foram verificados diretamente no disco via `Get-FileHash -Algorithm SHA256`. Nenhum hash é truncado e todos possuem exatamente 64 caracteres hexadecimais:

| Arquivo (Caminho Relativo ao Repositório) | Classificação | Hash SHA-256 Completo (Disco) | Função no Fluxo Temporal |
| :--- | :--- | :--- | :--- |
| `tools/phase2_dataset/step9_to_18_build_datasets.py` | `REAL` | `81aa57a2c2e34aa785aeab67a5ccdca498247c5f39f322c5f9f9997b60e05b25` | Extrai `current_pos` dos NPZ e grava em Parquet |
| `tools/phase2_dataset/dataloaders.py` | `REAL` | `921836c8a9c4590f91a2ed3aa8da090a4470878bb8f6e66a8dc25997d198183d` | DataLoader auditado na Fase 2.2 (`PositioningDatasetV1`) |
| `tools/phase2_dataset/forensic_step4_temporal_windows.py` | `REAL` | `c553f1df4837f5d950d1febd266a0f5bd7504be2a09089ea64f2c3f315b84136` | Script forense da Fase 2.2 com ticks sintetizados |
| `tools/phase3a_training/data_utils.py` | `REAL` | `d15c234e3a2ce73fe01663293b60a8a53166d73e8caf40254b36eef2e4ec8e45` | Contém `np.linspace` (L226) e construtor de tensores |
| `tools/phase3a_training/positioning_model.py` | `REAL` | `d98b6e4526a18a32a31702f88825899c950189a4243d365fb25cab0064371e9b` | Arquitetura do `PositioningTransformerV1` |
| `tools/phase3a_training/train_full.py` | `REAL` | `ef9c32d386346dca33fda0b8ff274b2efab09585e53c95405de08481ac02b0d9` | Script de treino das seeds 42026, 42027 e 42028 |
| `tools/phase3a_training/evaluate_positioning_v1_canonical.py` | `REAL` | `1751469a8a43619e9d7c309fa79abf49f3d518efd5d173b99f13f8372fe1bf93` | Avaliação canônica sobre o Test Set |
| `tools/phase3a_training/finetune_state_head.py` | `REAL` | `e4747dff9458f33ad328b2e53fbcd0a58612307689627fa34dbae3e109371700` | Fine-tuning de ablação e avaliação de heads |
| `tools/phase3a_training/dry_run.py` | `REAL` | `df7893fee3c1b875230b012974334548a9aa482285f4699b2ffbe225601f4c54` | Dry-run da Fase 3A (usou DataLoader da Fase 2.2) |
| `models/positioning/de_mirage_positioning_v1.pt` | `REAL` | `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0` | Checkpoint mestre oficial (Seed 42027) |
| `training_runs/positioning_v1/seed_42026/best_checkpoint.pt` | `REAL` | `d7dc58ef216935d5c8202b3e4395ef5c0a80c790984a9758612031a17aaf79d0` | Melhor checkpoint da Seed 42026 |
| `training_runs/positioning_v1/seed_42027/best_checkpoint.pt` | `REAL` | `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0` | Melhor checkpoint da Seed 42027 (idêntico ao mestre) |
| `training_runs/positioning_v1/seed_42028/best_checkpoint.pt` | `REAL` | `af99069189952aef0fe2a9070d328dd2179b131b046501036b4bfb0c590c779e` | Melhor checkpoint da Seed 42028 |
| `datasets/mirage_v2/parquet_physical_schema_audit.json` | `REAL` | `e5f8ab93acd6a9cd487b4f98632ffe7a58234ae9fa80881c0b1b8ee58294b05b` | Relatório com alegações ficcionais de janelas NPZ |
| `datasets/mirage_v2/dataloader_validation_report.md` | `REAL` | `9e791cc972f6355f1d7ebc14a4113edd4961674637da22fb56fc50fb412ac3cb` | Relatório de validação dos DataLoaders da Fase 2.2 |
| `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_000.parquet` | `REAL` | `7d387973188f257ec20d38a291d68d7cf50d1d4fa3d773d38076023e8fb50d43` | Shard de treino Parquet com posições pontuais |
| `datasets/mirage_v2/positioning/canonical_test_set.parquet` | `REAL` | `3a6de89c3ba5a91b2f494f37dbcc7a76ef366639262d2f991fc7f1f95aa60eb4` | Test Set canônico Parquet |
| `graphify-out/graph.json` | `REAL` | `7a09693f1f6568803fa7f2ae7a0286cbe38c09f3900d08b96c6538f4eaa264f0` | Grafo de conhecimento Graphify com 2.627 nós e 5.533 arestas |
| `.agents/audit/pre3a3_temporal_history_blast_radius.json` | `REAL` | Gerado em conjunto com este documento | Mapeamento JSON estruturado de impacto arquitetural |

---

## 6. Veredito Canônico e Conclusão

Com base no rastreamento ininterrupto de chamadas do Graphify e na verificação física linha por linha de todos os arquivos de código e artefatos de modelo:

1. **Veredito para o Checkpoint**: **`B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**.
2. **Preservação Experimental**: Em estrito cumprimento ao requisito R4 e às regras do usuário, os checkpoints existentes (`models/positioning/de_mirage_positioning_v1.pt` e `training_runs/positioning_v1/seed_*/*.pt`) **devem ser preservados como artefatos experimentais** e marcados com a etiqueta `TRAINED_WITH_SYNTHETIC_HISTORY`.
3. **Recomendação Futura**: Nenhuma fase subsequente (como exportação ONNX de produção na Fase 3A.3 ou deploy em C#) deve considerar os pesos atuais como validados contra partidas profissionais reais. O retreinamento com extração temporal densa a partir dos 444 arquivos `.npz` físicos será indispensável para obter generalização tática genuína.
