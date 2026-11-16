# Decisão Canônica sobre a Proveniência Temporal do Checkpoint Positioning Transformer V1

- **Documento**: `pre3a3_checkpoint_decision.md`
- **Fase de Governança**: Pré-Fase 3A.3 / Requisito R4 (Milestone 4)
- **Autor / Auditor**: ML Generalization Auditor (Tier 3 - Alto Risco)
- **Data e Hora UTC**: 2026-11-07T21:15:00Z
- **Classificação Canônica de Homologação**: `AGENT_REVIEWED` (em estrito cumprimento à Regra `05-human-review-integrity`)
- **Natureza dos Dados Analisados**: `REAL` (arquivos de código, manifests, tensores Parquet e checkpoints em disco)
- **Decisão Canônica de Proveniência**: **`B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**

---

## 1. Declaração Canônica da Decisão

Em estrito cumprimento aos requisitos de governança do projeto CsBot (`AGENTS.md`) e à especificação mandatória do Requisito R4 documentada em `.agents/teamwork/ORIGINAL_REQUEST.md`, o **ML Generalization Auditor** emite formal e categoricamente a seguinte conclusão:

```
========================================================================================
DECISÃO CANÔNICA DE PROVENIÊNCIA TEMPORAL:
B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY
========================================================================================
```

### Justificativa Epistêmica e Resumo Executivo:
A auditoria forense independente, baseada na inspeção do grafo computacional PyTorch, na revisão do código executável e no rastreamento determinístico de tensores do pipeline de treinamento das seeds 42026, 42027 e 42028, comprovou empiricamente que:
1. **Ausência de Janelas Históricas Reais nos Datasets de Entrada**: Os arquivos Parquet de treino, validação e teste (`datasets/mirage_v2/positioning/positioning_sequences_v1/shard_*.parquet` e `canonical_test_set.parquet`) armazenam única e exclusivamente o vetor de posição pontual instantânea do tick amostrado (`current_pos = [cur_x, cur_y, cur_z]`). Nenhuma janela temporal histórica contendo os 32 frames anteriores extraídos dos 444 arquivos `.npz` físicos foi persistida nesses arquivos.
2. **Injeção de Histórico Sintético Não Rotulado**: A função de carregamento `tools/phase3a_training/data_utils.py:load_and_preprocess_shard` (L217-L228) sintetizou artificialmente o tensor `history` `[N, 32, 18]` replicando a posição atual nos 32 timesteps e somando uma rampa de inclinação linear fixa através de `step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32)` exclusivamente na coordenada X (Feature 0). As coordenadas Y e Z permaneceram constantes (`std == 0`), Health e IsAlive foram forçados como `1.0`, e as features 5 a 17 foram deixadas integralmente zeradas.
3. **Companheiros de Equipe Fictícios (Clones Deslocados)**: O tensor `teammates` `[N, 32, 4, 18]` foi sintetizado (L230-L238) duplicando a posição do jogador com translações determinísticas escalonadas `(i + 1) * 0.05` em X e `-(i + 1) * 0.05` em Y, sem qualquer fundamentação nas trajetórias reais dos aliados da partida de CS2.
4. **Propagação Direta para a Perda e Gradientes**: Esses tensores artificiais foram passados diretamente para o método `PositioningTransformerV1.forward` e alimentaram as 5 cabeças de perda em `PositioningMultitaskLoss.forward`, gerando os gradientes que otimizaram os pesos do modelo durante o treinamento de todas as 3 seeds (`train_full.py:L159-L180`).
5. **Uniformidade em Todos os Splits**: O split de treinamento (`train`), o split de validação (`validation`) e o split canônico de teste (`test`) foram processados rigorosamente pela mesma função `load_and_preprocess_shard`, demonstrando que nenhum dado temporal autêntico de partida real foi consumido pelo modelo em qualquer etapa do ciclo de modelagem.

---

## 2. Inventário e Auditoria Forense Rigorosa de `np.linspace`

Foi conduzida uma varredura exaustiva em todo o código-fonte, scripts de treinamento, utilitários, ferramentas de avaliação e testes unitários do repositório CsBot. Foram identificadas 6 ocorrências de `linspace` (5 em NumPy e 1 em PyTorch).

Abaixo consta a auditoria detalhada de cada ocorrência, com sua classificação taxonômica estrita conforme o Requisito R4:

| # | Arquivo (Relativo à Raiz) | Linha | Função / Escopo | Expressão Exata | Source Type | Output Tensor (Shape, Dtype) | Reaches Training Loss? | Reaches Validation Loss? | Reaches Test Evaluation? | Classificação Canônica |
|---|---|---|---|---|---|---|:---:|:---:|:---:|---|
| 1 | `tools/phase3a_training/data_utils.py` | 226 | `load_and_preprocess_shard` | `np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1)` | `SYNTHETIC` | `step_drift` `[1, 32, 1]`, float32 -> `history` `[N, 32, 18]`, float32 | **SIM** | **SIM** | **SIM** | **`UNLABELED_SYNTHETIC_INPUT`** |
| 2 | `tools/phase3a_training/reconcile_ablation_and_calibration.py` | 37 | `compute_ece_and_brier` | `np.linspace(0.0, 1.0, num_bins + 1)` | `REAL` | `bins` `[11]`, float64 | Não | Não | Não | **`LEGITIMATE_INTERPOLATION`** |
| 3 | `tools/phase3a_training/reconcile_ablation_and_calibration.py` | 71 | `compute_ece_and_brier` | `np.linspace(0, 100, num_bins + 1)` | `REAL` | `quantiles` `[11]`, float64 | Não | Não | Não | **`LEGITIMATE_INTERPOLATION`** |
| 4 | `tools/phase3a_training/reconcile_ablation_and_calibration.py` | 324 | `main` (Temperature Scaling) | `np.linspace(0.5, 3.0, 51)` | `REAL` | `t_candidates` `[51]`, float64 | Não | Não | Não | **`LEGITIMATE_INTERPOLATION`** |
| 5 | `tools/phase3a_training/evaluate.py` | 287 | Bloco de calibração ECE | `np.linspace(0.0, 1.0, 11)` | `REAL` | `bins` `[11]`, float64 | Não | Não | Não | **`REPORT_ONLY`** |
| 6 | `tools/phase3a_training/finetune_state_head.py` | 325 | `expected_calibration_error` | `torch.linspace(0, 1, n_bins + 1)` | `REAL` | `bin_boundaries` `[16]`, float32 | Não | Não | Não | **`LEGITIMATE_INTERPOLATION`** |

### 2.1 Análise Aprofundada da Ocorrência Crítica (Linha 226 de `data_utils.py`)

- **Código Verbatim** (`tools/phase3a_training/data_utils.py:L218-L227`):
  ```python
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
  ```
- **Propósito Real**: Injetar artificialmente uma variação temporal determinística (drift linear) na dimensão X do jogador, para mascarar o fato de que os shards Parquet da Fase 2 continham apenas posições estáticas pontuais (`current_pos`). Sem essa rampa, a variância temporal em todas as dimensões seria rigorosamente zero (`std == 0`).
- **Violação de Governança Identificada**:
  - Enquadra-se formalmente na Regra `04-synthetic-data-labeling` do `AGENTS.md` como dado sintético não rotulado (`UNLABELED_SYNTHETIC_INPUT`), pois o artefato e os relatórios executivos da Fase 3A apresentavam essa entrada como decorrente de janelas temporais de partidas de CS2.
  - Viola o Requisito R4 por entregar dados artificiais diretamente à perda de treinamento.
- **Rastreamento de Propagação do Tensor**:
  1. `history_arr` é convertido para tensor PyTorch na linha 294: `"history": torch.from_numpy(history_arr)`.
  2. Em `InMemoryPositioningDataset.__getitem__`, o tensor é empacotado em `batch["history"]`.
  3. No loop de treino de `train_full.py` (L159-L168), `batch["history"]` é alimentado em `model(history=batch["history"], ...)`.
  4. Dentro do modelo (`positioning_model.py:L142-L144`), `history` passa pela projeção linear `self.player_proj(history)`, gerando tokens latentes de dimensão 192 que atravessam as 3 camadas de Transformer Encoder com 6 heads de atenção.
  5. A saída do Transformer alimenta os classificadores das 5 cabeças (`positioning_state`, `next_sector`, `candidate_spot_idx`, `transition`, `exit_trigger`), cuja perda multitarefa agregada `loss_total` executa `loss.backward()`, atualizando todos os pesos neurais da rede com base no sinal sintético.

### 2.2 Análise das Ocorrências Legítimas (Linhas de Calibração e Métricas)

- As ocorrências 2, 3, 4, 5 e 6 atuam exclusivamente como operações matemáticas auxiliares:
  - Discretização de intervalos para binning de calibração estatística (ECE padrão e adaptativo);
  - Grade de candidatos para Temperature Scaling $T^*$ executado estritamente sobre logits de validação em conformidade com a Regra `02-no-test-contamination`;
  - Renderização diagnóstica de curvas de calibração em relatórios executivos.
- Nenhuma dessas 5 ocorrências gera tensores de entrada para a rede neural, nem participa do cálculo da perda de otimização de gradientes. Portanto, são rigorosamente legítimas.

---

## 3. Rastreamento e Mapeamento do Fluxo de Dados: NPZ -> Parquet -> DataLoader -> Checkpoint

A investigação forense mapeou toda a linhagem física dos dados através do repositório:

```
[444 Arquivos .npz em Disco Externo F:\]
(F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\*.npz)
       │
       ▼  [tools/phase2_dataset/step9_to_18_build_datasets.py:L108-L115]
       │  Leitura pontual de X[f_idx]
       │  L268: grava APENAS "current_pos": [round(cur_x, 1), round(cur_y, 1), round(cur_z, 1)]
       │  (NENHUM frame dos 32 passos anteriores foi copiado para o Parquet)
       ▼
[datasets/mirage_v2/positioning/positioning_sequences_v1/shard_*.parquet]
(6 shards contendo 40.000 sequências com posições pontuais isoladas)
       │
       ▼  [tools/phase3a_training/data_utils.py:load_and_preprocess_shard]
       ├── self_history: cur_pos repetido 32x + np.linspace(-0.01, 0.0, 32) no eixo X (L226-L227)
       └── teammate_history: cur_pos repetido 32x + offsets fixos (i+1)*0.05 em X e Y (L231-L238)
       │
       ▼
[InMemoryPositioningDataset] (tools/phase3a_training/data_utils.py:L139)
       │
       ▼  (DataLoader com batch_size=64 em tools/phase3a_training/train_full.py:L121)
[PositioningTransformerV1.forward] (tools/phase3a_training/positioning_model.py:L136)
       ├── player_proj: Linear(18, 192)
       ├── teammate_proj: Linear(18, 192)
       ├── TransformerEncoder: 3 camadas, 6 heads
       └── 5 Heads de Predição
       │
       ▼  (Otimização AdamW com backpropagation em train_full.py:L178-L180)
[Checkpoints Materializados no Disco]
├── training_runs/positioning_v1/seed_42026/best_checkpoint.pt
├── training_runs/positioning_v1/seed_42027/best_checkpoint.pt  <─── IDÊNTICO AO MESTRE
├── training_runs/positioning_v1/seed_42028/best_checkpoint.pt
└── models/positioning/de_mirage_positioning_v1.pt (Checkpoint Mestre de Produção)
```

### 3.1 Composição Exata dos Tensores de Entrada Entregues ao Modelo

A tabela abaixo documenta a natureza física exata de cada componente do tensor recebido por `PositioningTransformerV1.forward`:

| Nome do Tensor | Formato (Shape) | Tipo (Dtype) | Classificação de Natureza | Detalhamento dos Canais de Entrada | Variância Temporal Física |
|---|---|---|---|---|---|
| `history` | `[B, 32, 18]` | `torch.float32` | `TEMPLATED_AND_SYNTHETIC` | Feat 0: `pos_x / 3000.0 + np.linspace(-0.01, 0.0, 32)`<br>Feat 1: `pos_y / 3000.0` (estático)<br>Feat 2: `pos_z / 3000.0` (estático)<br>Feat 3: `1.0` (Health fixo)<br>Feat 4: `1.0` (IsAlive fixo)<br>Feat 5..17: `0.0` (zeradas) | Feat 0: Artificial linear (`std > 0`)<br>Feats 1..17: Nula (`std == 0`) |
| `teammates` | `[B, 32, 4, 18]` | `torch.float32` | `SYNTHETIC` | Para aliado $i \in \{0, 1, 2, 3\}$:<br>Feat 0: `(pos_x / 3000.0) + (i + 1) * 0.05`<br>Feat 1: `(pos_y / 3000.0) - (i + 1) * 0.05`<br>Feat 2: `pos_z / 3000.0`<br>Feat 3..4: `1.0`<br>Feat 5..17: `0.0` | Nula nos 32 timesteps para todos os 4 aliados (`std == 0`) |
| `candidate_mask` | `[B, 53]` | `torch.bool` | `SYNTHETIC` | 100% dos 53 bits habilitados como `True` | N/A |
| `team_idx` | `[B]` | `torch.int64` | `REAL` | 0 (CT), 1 (TR), 2 (ANY) | N/A |
| `role_idx` | `[B]` | `torch.int64` | `INFERRED` | 0 a 9 conforme categorização heurística | N/A |
| `stage_idx` | `[B]` | `torch.int64` | `INFERRED` | 0 a 5 conforme estágio do round | N/A |

---

## 4. Comparação entre os DataLoaders: Fase 2.2 vs. Fase 3A Real

A investigação identificou uma substituição silenciosa de implementação entre a Fase 2.2 e o treinamento real da Fase 3A:

| Aspecto de Engenharia | DataLoader Auditado na Fase 2.2 (`dataloaders.py:PositioningDatasetV1`) | DataLoader Efetivo de Treino na Fase 3A (`data_utils.py:InMemoryPositioningDataset`) | Análise Crítica de Generalização |
|---|---|---|---|
| **Módulo e Classe** | `tools/phase2_dataset/dataloaders.py`<br>`PositioningDatasetV1` | `tools/phase3a_training/data_utils.py`<br>`InMemoryPositioningDataset` | A classe de produção homologada na Fase 2.2 foi descartada e substituída no treino |
| **Histórico do Jogador** | Replicava `cur_pos / 3000.0` 32 vezes sem drift linear (`std == 0`). `np.linspace` não era chamado. | Adicionou `np.linspace(-0.01, 0.0, 32)` no eixo X (`history_arr[:, :, 0] += step_drift`). | O drift sintético foi introduzido ad-hoc na Fase 3A |
| **Histórico de Aliados** | Matriz inteiramente zerada: `np.zeros((32, 4, 18))`. | Matriz sintética com offsets espaciais estáticos `(i+1)*0.05`. | Aliados sintéticos introduzidos ad-hoc na Fase 3A |
| **Contexto Categórico** | Inexistente (sem `team_idx`, `role_idx`, `stage_idx`). | Incluído (`team_idx`, `role_idx`, `stage_idx`). | Ampliação das entradas do modelo |
| **Cabeças Supervisionadas** | 3 cabeças (`state`, `sector`, `candidate_spot`). | 5 cabeças (+ `transition` e `exit_trigger`). | Expansão multitarefa |

---

## 5. Uniformidade de Caminho entre Todos os Splits (Inexistência de Janelas Reais)

A hipótese de que splits de validação ou teste pudessem ter consumido janelas temporais reais da partida foi integralmente rejeitada:

1. **Split `train`** (`train_full.py:L316`): Carregado via `create_dataset_from_shards(..., split="train")` -> executa `load_and_preprocess_shard` com `np.linspace`.
2. **Split `validation`** (`train_full.py:L317`): Carregado via `create_dataset_from_shards(..., split="validation")` -> executa `load_and_preprocess_shard` com `np.linspace`.
3. **Split `test` Canônico** (`evaluate_positioning_v1_canonical.py:L83`): Carregado via `load_and_preprocess_shard(test_parquet_path, spot_to_idx)` -> executa `load_and_preprocess_shard` com `np.linspace`.
4. **Split `challenge_v2`** (`finetune_state_head.py:L378`): Carregado via `load_and_preprocess_shard` com `np.linspace`.

**Conclusão sobre a Unicidade de Caminho**:
- Todos os splits sem exceção foram submetidos ao mesmo gerador artificial de histórico.
- A alegação constante no relatório executivo da Fase 2 (`datasets/mirage_v2/parquet_physical_schema_audit.json:L26`) de que o pipeline operava com *"MEMORY_MAPPED_INDEXED_WINDOW"* e reconstruía janelas do NPZ em tempo de execução de batch era meramente documental e **nunca foi materializada em código executável**.

---

## 6. Impacto na Generalização de ML e nas Camadas do Transformer

Como auditor especialista em Generalização de Machine Learning, documentam-se os seguintes impactos técnicos decorrentes dessa proveniência sintética:

1. **Vício Estrutural das Projeções Lineares**:
   As camadas `player_proj` e `teammate_proj` (camadas `Linear(18, 192)` que convertem cada frame histórico no espaço de embedding) foram otimizadas contra um gradiente temporal puramente artificial de passo linear em X e zero em Y e Z.
2. **Degradação de Atenção sob Dinâmica Física Real**:
   Em partidas reais de CS2, a locomoção de 16Hz envolve oscilações de footstep, acelerações tangenciais ao espreitar quinas (peeking), saltos com variação brusca em Z e desacelerações de contra-strafe. Se um tensor com dinâmica física real for injetado no modelo atual, a matriz de auto-atenção ($Q K^T / \sqrt{d}$) apresentará divergência distributiva severa (out-of-distribution temporal).
3. **Companheiros Fictícios Paralelos**:
   Os 4 aliados aprendidos pelo modelo comportam-se como clones estáticos viajando paralelamente ao jogador a uma distância fixa, o que impede a rede de aprender relações táticas genuínas de cobertura cruzada (crossfire), trocas de abate (refrag) e formação tática em equipe.
4. **Status das Métricas Reportadas na Fase 3A**:
   Todas as métricas numéricas registradas nos relatórios da Fase 3A (ex: F1 de State, Top-1 Spot Accuracy, MRR e Calibração ECE) foram aferidas sobre dados sintéticos avaliados contra si mesmos. Embora as métricas reflitam que a arquitetura aprendeu a tarefa proposta sob essa distribuição sintética, **elas não atestam generalização sobre partidas competitivas reais de CS2**.

---

## 7. Determinações Mandatórias de Preservação e Retreino Futuro

Em cumprimento estrito às instruções do usuário humano e às regras do Requisito R4:

### 7.1 Preservação Experimental Sem Deleção
1. **Os checkpoints atuais NÃO devem ser apagados, sobrescritos nem descartados**.
2. Os seguintes arquivos devem ser **estritamente preservados no disco** e formalmente etiquetados como artefatos experimentais de baseline com histórico sintético:
   - `models/positioning/de_mirage_positioning_v1.pt` (SHA-256: `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0`)
   - `training_runs/positioning_v1/seed_42026/best_checkpoint.pt` (SHA-256: `d7dc58ef216935d5c8202b3e4395ef5c0a80c790984a9758612031a17aaf79d0`)
   - `training_runs/positioning_v1/seed_42027/best_checkpoint.pt` (SHA-256: `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0`)
   - `training_runs/positioning_v1/seed_42028/best_checkpoint.pt` (SHA-256: `af99069189952aef0fe2a9070d328dd2179b131b046501036b4bfb0c590c779e`)
3. A preservação desses checkpoints é essencial para servir como baseline comparativo (ablation baseline) quando o retreino com janelas reais for executado.

### 7.2 Bloqueio de Exportação para Produção e Deploy em C#
- É **terminantemente proibido** exportar o checkpoint atual para ONNX de produção visando integração no runtime C# (`src/CsBotManager/`) como modelo tático definitivo.
- O avanço para a Fase 3A.3 ou etapas de inferência no servidor real de CS2 utilizando os pesos atuais fica **bloqueado para homologação final**, sendo permitido apenas para testes técnicos de integração de pipeline C# sem validação tática.

### 7.3 Recomendação Canônica para Retreino Futuro
Para restabelecer a integridade científica e de generalização tática do Positioning Transformer, recomenda-se:
1. **Materialização das Janelas NPZ no Disco**: Modificar o pipeline de geração de datasets (`tools/phase2_dataset/`) para extrair os 32 frames históricos autênticos (`X[f_idx-31 : f_idx+1]`) diretamente dos 444 arquivos `.npz` físicos e persistir tensores densos `[32, 18]` para o jogador e `[32, 4, 18]` para os aliados reais presentes na demo.
2. **Eliminação Definitiva de `step_drift`**: Remover a linha 226 (`step_drift = np.linspace(...)`) de `tools/phase3a_training/data_utils.py` e substituir pela leitura direta da janela temporal real persistida.
3. **Re-execução das 3 Seeds**: Re-executar o treinamento das seeds 42026, 42027 e 42028 sob a distribuição física real, avaliando a verdadeira capacidade preditiva do modelo multitarefa.

---

## 8. Matriz de Evidências Físicas e Hashes SHA-256 Completos

Todos os arquivos abaixo foram conferidos diretamente no disco em tempo de execução. Nenhum hash está truncado e todos contêm exatamente 64 caracteres hexadecimais, em estrito cumprimento à Regra `01-evidence-before-claims`:

| Arquivo Auditado (Caminho Relativo ao Repositório) | Natureza do Dado | Tamanho (Bytes) | Hash SHA-256 Completo (64 caracteres) | Papel no Pipeline Auditado |
|---|---|---|---|---|
| `tools/phase3a_training/data_utils.py` | `REAL` | 18.406 | `d15c234e3a2ce73fe01663293b60a8a53166d73e8caf40254b36eef2e4ec8e45` | Contém L226 com `np.linspace` e sintetizador de aliados |
| `tools/phase3a_training/train_full.py` | `REAL` | 14.893 | `ef9c32d386346dca33fda0b8ff274b2efab09585e53c95405de08481ac02b0d9` | Script de treinamento das seeds 42026, 42027 e 42028 |
| `tools/phase3a_training/positioning_model.py` | `REAL` | 11.238 | `d98b6e4526a18a32a31702f88825899c950189a4243d365fb25cab0064371e9b` | Arquitetura neural do PositioningTransformerV1 e Loss |
| `tools/phase3a_training/evaluate_positioning_v1_canonical.py` | `REAL` | 8.503 | `1751469a8a43619e9d7c309fa79abf49f3d518efd5d173b99f13f8372fe1bf93` | Script de avaliação canônica sobre o Test Set |
| `tools/phase3a_training/reconcile_ablation_and_calibration.py` | `REAL` | 22.884 | `69613759f0b944bcc1a31f85617da10ed826b5d65d2150d401b6066b4114da66` | Cálculos legítimos de ECE, AECE e grid de temperatura |
| `tools/phase3a_training/evaluate.py` | `REAL` | 18.885 | `6fd694c99645e84ee203ec70f5a3d9286d32c20fd49705923f5583a0f24e7c24` | Avaliação e geração de relatórios com tabulação ECE |
| `tools/phase3a_training/finetune_state_head.py` | `REAL` | 39.378 | `e4747dff9458f33ad328b2e53fbcd0a58612307689627fa34dbae3e109371700` | Fine-tuning com bins de ECE em PyTorch |
| `tools/phase3a_training/dry_run.py` | `REAL` | 7.914 | `df7893fee3c1b875230b012974334548a9aa482285f4699b2ffbe225601f4c54` | Script de dry-run executado na preparação da Fase 3A |
| `tools/phase2_dataset/dataloaders.py` | `REAL` | 13.756 | `921836c8a9c4590f91a2ed3aa8da090a4470878bb8f6e66a8dc25997d198183d` | DataLoader da Fase 2.2 com posições puramente estáticas |
| `tools/phase2_dataset/step9_to_18_build_datasets.py` | `REAL` | 23.473 | `81aa57a2c2e34aa785aeab67a5ccdca498247c5f39f322c5f9f9997b60e05b25` | Extração de NPZ gravando apenas current_pos em Parquet |
| `models/positioning/de_mirage_positioning_v1.pt` | `REAL` | 4.887.893 | `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0` | Checkpoint mestre oficial (idêntico à Seed 42027) |
| `training_runs/positioning_v1/seed_42026/best_checkpoint.pt` | `REAL` | 4.887.893 | `d7dc58ef216935d5c8202b3e4395ef5c0a80c790984a9758612031a17aaf79d0` | Checkpoint da Seed 42026 treinado com histórico sintético |
| `training_runs/positioning_v1/seed_42027/best_checkpoint.pt` | `REAL` | 4.887.893 | `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0` | Checkpoint da Seed 42027 treinado com histórico sintético |
| `training_runs/positioning_v1/seed_42028/best_checkpoint.pt` | `REAL` | 4.887.893 | `af99069189952aef0fe2a9070d328dd2179b131b046501036b4bfb0c590c779e` | Checkpoint da Seed 42028 treinado com histórico sintético |
| `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_000.parquet` | `REAL` | 2.511.412 | `7d387973188f257ec20d38a291d68d7cf50d1d4fa3d773d38076023e8fb50d43` | Shard Parquet contendo posições isoladas sem janelas |
| `datasets/mirage_v2/positioning/canonical_test_set.parquet` | `REAL` | 632.701 | `3a6de89c3ba5a91b2f494f37dbcc7a76ef366639262d2f991fc7f1f95aa60eb4` | Test set canônico Parquet sem janelas históricas |
| `graphify-out/graph.json` | `REAL` | 3.842.105 | `7a09693f1f6568803fa7f2ae7a0286cbe38c09f3900d08b96c6538f4eaa264f0` | Grafo de conhecimento Graphify com 2.627 nós e 5.533 arestas |
| `.agents/audit/pre3a3_temporal_history_graph.md` | `REAL` | 26.306 | `56e54f9a7eb4423b4976c66cf17fbb858ce105d1bb6d1eb2b85fa1b6fa20f18d` | Relatório canônico do Graph Analyst |
| `.agents/audit/pre3a3_temporal_history_blast_radius.json` | `REAL` | 16.339 | `e837fcf037ae6cb896ee81c3cceb68e918c5e64850ae22c1ea35ffcba657803e` | Mapeamento JSON de raio de impacto temporal |

---

## 9. Veredito Final de Engenharia

O **ML Generalization Auditor** sela este documento na raiz do repositório em conformidade irrestrita com os critérios de aceite do Requisito R4:
- Classificação Canônica emitida: **`B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**;
- Preservação experimental compulsória: **Checkpoints mantidos intactos sem deleção nem sobrescrita**;
- Bloqueio de produção ativo: **Fase 3A.3 e C# deploy condicionados a retreino com dados temporais autênticos**.
