# Protocolo de Auditoria Forense de Datasets (`csbot-dataset-forensics`)

Este documento especifica as invariantes matemáticas, verificações de integridade e contratos de saída dos 6 scripts da Skill `csbot-dataset-forensics`.

---

## 1. Auditoria de Vazamento entre Splits (`check_split_leakage.py`)

### Invariantes Obrigatórias
1. **Disjunção de Identificadores de Partida/Demo**:
   $$\text{Set}(\text{Train}_{\text{demo\_id}}) \cap \text{Set}(\text{Test}_{\text{demo\_id}}) = \emptyset$$
   $$\text{Set}(\text{Val}_{\text{demo\_id}}) \cap \text{Set}(\text{Test}_{\text{demo\_id}}) = \emptyset$$
   $$\text{Set}(\text{Train}_{\text{demo\_id}}) \cap \text{Set}(\text{Val}_{\text{demo\_id}}) = \emptyset$$
2. **Disjunção de Hashes de Feature Vectors**:
   - Calcula o hash SHA-256 de cada linha/janela de features para detectar amostras duplicadas exatas entre splits mesmo que renomeadas.
3. **Proibição de Preenchimento Artificial de Suporte (`03-zero-support-is-na`)**:
   - Verifica se alguma amostra em `Test` compartilha `(demo_id, round_num, tick)` ou vizinhança imediata ($\Delta \text{tick} < W$) com `Train` ou `Validation`.

---

## 2. Reconciliação Contábil de Amostras (`reconcile_dataset_counts.py`)

### Equação de Conservação do Pipeline
Para todo pipeline de extração e filtragem:
$$N_{\text{raw\_extracted}} = N_{\text{train}} + N_{\text{val}} + N_{\text{test}} + \sum_{k} N_{\text{rejected\_reason\_}k}$$

- Toda amostra descartada (ex: `warmup_round`, `knife_round`, `corrupted_tick`, `invalid_navmesh_spot`, `short_sequence`) deve ser contabilizada nominalmente no dicionário `rejection_ledger`.
- **Diferença não reconciliada (`unaccounted_delta != 0`) resulta em `FAIL` imediato.**

---

## 3. Auditoria de Parquet, NPZ e Sequências (`audit_parquet_rows.py`)

### Verificações Estruturais
1. **Alinhamento Cardinal**: O número de registros no `.parquet` de índice deve coincidir exatamente com a dimensão $N$ (axis 0) de todos os arrays em `.npz` (`X`, `y`, `masks`, `sample_ids`).
2. **Sanidade Numérica**: Zero ocorrências de `NaN`, `+Inf` ou `-Inf` em tensores de entrada e alvos válidos.
3. **Integridade Temporal de Sequências**:
   - Dentro de cada janela de sequência $S_i = [t_1, t_2, \dots, t_L]$, os ticks devem ser estritamente crescentes ($t_{k+1} > t_k$) e pertencer ao mesmo `(demo_id, round_id, player_steamid)`.
   - Proibido cruzar fronteiras de round ou morte/respawn de jogador dentro da mesma janela contínua sem máscara explícita de padding.

---

## 4. Verificação de Proveniência (`verify_sample_provenance.py`)

- Cada amostra deve conter metadados rastreáveis: `source_file`, `source_sha256`, `round_id`, `tick_start`, `tick_end` e `data_nature` (`REAL`, `SIMULATED`, `SYNTHETIC`).
- O script amostra ou varre integralmente o dataset verificando se `source_file` existe no catálogo bruto e se o `source_sha256` confere com o registro oficial de demos/logs.

---

## 5. Detecção de Dados Templados ou Sintéticos (`detect_templated_outputs.py`)

Verifica sinais clássicos de dados forjados, interpolados ou gerados por loop de template:
1. **Taxa de Colisão de Coordenadas/Vetores**: Proporção anormal de linhas idênticas ou espaçadas com passo aritmético constante ($\Delta x = c, \Delta y = c$).
2. **Variância Zero em Canais Dinâmicos**: Velocidade, viewangles ou posições idênticas ao longo de centenas de ticks marcados como `REAL`.
3. **Padrões Ciclicamente Repetidos**: Sequências de ações/labels que se repetem periodicamente (`A -> B -> C -> A -> B -> C`) sem variação orgânica de partida.

---

## 6. Auditoria de Suporte de Labels e Amostragem Visual (`audit_label_support.py`)

- Gera a tabela completa de suporte por classe (`class_id`, `class_name`, `train_count`, `val_count`, `test_count`).
- Para qualquer classe onde `test_count == 0` ou `val_count == 0`, grava a flag `"eval_status": "N/A_ZERO_SUPPORT"` para consumo obrigatório pelo `csbot-model-validator`.
- Exporta um subconjunto determinístico de amostras estratificadas (`visual_audit_samples.json`) com coordenadas `(x, y, z)`, spot atribuído e estado do jogo para auditoria visual/espacial.
