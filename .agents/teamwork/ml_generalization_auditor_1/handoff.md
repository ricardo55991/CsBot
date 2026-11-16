# Handoff Report — ML Generalization Auditor (Requisito R4)

- **Fase / Tarefa**: Milestone 4 / Requisito R4 — Auditoria de `np.linspace` e Decisão Canônica do Checkpoint
- **Auditor**: ML Generalization Auditor (`teamwork_auditor`)
- **Diretório de Trabalho**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ml_generalization_auditor_1`
- **Artefato Principal Entregue**: `pre3a3_checkpoint_decision.md` (na raiz do repositório)
- **Data e Hora UTC**: 2026-11-07T21:25:00Z
- **Classificação Canônica de Homologação**: `AGENT_REVIEWED`

---

## 1. Observation (O que foi observado diretamente)

1. **Ocorrência de `np.linspace` no Pipeline de Treinamento**:
   - Arquivo: `tools/phase3a_training/data_utils.py`
   - Linha 226-227:
     ```python
     226:     step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1)
     227:     history_arr[:, :, 0] += step_drift[:, :, 0]
     ```
   - Linhas 230-238 (construção de companheiros sintéticos):
     ```python
     230:     teammates_arr = np.zeros((n, 32, 4, 18), dtype=np.float32)
     231:     for i in range(4):
     232:         offset = (i + 1) * 0.05
     233:         teammates_arr[:, :, i, 0] = (pos_arr[:, 0:1] / 3000.0) + offset
     234:         teammates_arr[:, :, i, 1] = (pos_arr[:, 1:2] / 3000.0) - offset
     ```
   - Linha 294: `"history": torch.from_numpy(history_arr)`.

2. **Propagação dos Tensores para a Perda de Treinamento e Seleção de Checkpoint**:
   - Em `tools/phase3a_training/train_full.py`:
     - Linhas 159-179:
       ```python
       159:         for batch in train_loader:
       160:             optimizer.zero_grad()
       161:             outputs = model(
       162:                 history=batch["history"],
       163:                 teammates=batch["teammates"],
       ...
       178:             loss = loss_dict["loss_total"]
       179:             loss.backward()
       ```
     - Linhas 216-234 (loop de validação com os mesmos tensores sintéticos):
       ```python
       216:             for batch in val_loader:
       217:                 outputs = model(history=batch["history"], teammates=batch["teammates"], ...)
       233:                 loss_dict = criterion(outputs, targets)
       ```
     - Linhas 273-285: seleção do `best_checkpoint.pt` guiada por `best_composite_score` computado sobre as previsões da validação com tensores sintéticos.

3. **Caminho Canônico de Avaliação no Test Set**:
   - Em `tools/phase3a_training/evaluate_positioning_v1_canonical.py`:
     - Linha 83: `prep = load_and_preprocess_shard(test_parquet_path, spot_to_idx)`
     - Linha 85: constrói `test_ds` usando `prep["history"]` e `prep["teammates"]`, que passam pela linha 226 de `data_utils.py`.

4. **Inventário Completo de Ocorrências de `linspace` no Repositório**:
   - `tools/phase3a_training/data_utils.py:226`: `np.linspace(-0.01, 0.0, 32, dtype=np.float32)` -> `UNLABELED_SYNTHETIC_INPUT` (alimenta treino, validação e teste).
   - `tools/phase3a_training/reconcile_ablation_and_calibration.py:37`: `np.linspace(0.0, 1.0, num_bins + 1)` -> `LEGITIMATE_INTERPOLATION` (ECE bins).
   - `tools/phase3a_training/reconcile_ablation_and_calibration.py:71`: `np.linspace(0, 100, num_bins + 1)` -> `LEGITIMATE_INTERPOLATION` (quantis adaptativos).
   - `tools/phase3a_training/reconcile_ablation_and_calibration.py:324`: `np.linspace(0.5, 3.0, 51)` -> `LEGITIMATE_INTERPOLATION` (candidatos de temperatura $T^*$).
   - `tools/phase3a_training/evaluate.py:287`: `np.linspace(0.0, 1.0, 11)` -> `REPORT_ONLY` (tabela de calibração).
   - `tools/phase3a_training/finetune_state_head.py:325`: `torch.linspace(0, 1, n_bins + 1)` -> `LEGITIMATE_INTERPOLATION` (ECE bins em PyTorch).

5. **Identidade de Hashes SHA-256 e Checkpoint Mestre**:
   - Checkpoint Mestre: `models/positioning/de_mirage_positioning_v1.pt` (SHA-256: `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0`).
   - Checkpoint Seed 42027: `training_runs/positioning_v1/seed_42027/best_checkpoint.pt` (SHA-256: `e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0`).
   - Checkpoint Seed 42026: `training_runs/positioning_v1/seed_42026/best_checkpoint.pt` (SHA-256: `d7dc58ef216935d5c8202b3e4395ef5c0a80c790984a9758612031a17aaf79d0`).
   - Checkpoint Seed 42028: `training_runs/positioning_v1/seed_42028/best_checkpoint.pt` (SHA-256: `af99069189952aef0fe2a9070d328dd2179b131b046501036b4bfb0c590c779e`).
   - Entregável gerado: `pre3a3_checkpoint_decision.md` (SHA-256: `0d02d3d1efb3c5655b3a0134ccc57ee6034a5c86c069eae36c91b26046845772`).

6. **Execução de Testes Unitários do Repositório**:
   - `pytest tests/test_phase3a_positioning_training.py` -> 20 passed em 3.30s.
   - `pytest tests/test_phase2_2_training_inputs.py` -> 20 passed em 1.72s.
   - `pytest tests/test_phase3a_1_forensic_reconciliation.py tests/test_phase3a_2_objective_save_enrichment.py` -> 40 passed em 4.29s.
   - `python -m py_compile` em todos os scripts do pipeline de treinamento -> 0 erros sintáticos.

---

## 2. Logic Chain (Cadeia Lógica de Raciocínio)

1. A partir da Observação 1, verificou-se que `load_and_preprocess_shard` lê posições pontuais dos shards Parquet e gera o histórico temporal de 32 frames injetando determinísticamente um drift linear constante via `np.linspace(-0.01, 0.0, 32)` na dimensão X, além de duplicar a posição do jogador para criar 4 aliados artificiais com offsets fixos.
2. A partir da Observação 2, constatou-se que os tensores `history` e `teammates` gerados por essa função foram fornecidos como entrada primária ao método `forward` do modelo `PositioningTransformerV1`, propagando-se pelas camadas de projeção (`player_proj`, `teammate_proj`), encoder do transformer e classificadores multitarefa.
3. A perda multitarefa calculada sobre esses batches gerou gradientes via `loss.backward()` que atualizaram os parâmetros neurais de todas as 3 seeds (42026, 42027 e 42028) durante as épocas de treinamento.
4. A partir das Observações 2 e 3, observou-se que tanto o loop de validação quanto o script de avaliação canônica no Test Set utilizaram a exata mesma função geradora sintética. Nenhum split utilizou dados extraídos dos 444 arquivos `.npz` físicos de locomoção contínua.
5. A partir da Observação 5, o checkpoint oficial `models/positioning/de_mirage_positioning_v1.pt` é idêntico bit a bit à seed 42027 treinada sob esse pipeline sintético.
6. Portanto, a proveniência temporal do checkpoint não é real (invalidando a Opção A), não é mista (invalidando a Opção C) e não é incerta (invalidando a Opção D, pois o código, hashes e rastreabilidade são 100% determinísticos).
7. Conclui-se de forma unívoca e necessária que o veredito canônico é **`B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**.
8. Conforme exigido pela regra R4, a emissão do veredito B implica que o checkpoint existente deve ser mantido como experimental para efeito de comparação (ablation baseline), sem deleção ou sobrescrita, recomendando-se retreino futuro com janelas densas autênticas extraídas dos arquivos `.npz`.

---

## 3. Caveats (Ressalvas e Limitações)

1. **Ablação com Dados NPZ Reais**: Não foi executado teste de inferência injetando janelas temporais reais dos 444 arquivos `.npz` no checkpoint atual, em estrito respeito às restrições inegociáveis de governança (auditor somente-leitura; proibição de iniciar a Fase 3A.3 ou modificar artefatos canônicos). O cálculo da divergência exata de desempenho sob tensores reais fica reservado para a fase de retreino.
2. **Desempenho Estático**: O modelo aprendeu correlações válidas para as features estáticas pontuais (`current_pos`, `team_idx`, `role_idx`, `stage_idx`), de modo que as predições de spots táticos refletem a geografia do mapa de Mirage sob condições estacionárias, embora careçam de sensibilidade à aceleração e velocidade física real.
3. "No other caveats."

---

## 4. Conclusion (Conclusão Canônica)

1. **Decisão do Checkpoint**: Emitida a classificação canônica formal **`B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**.
2. **Entregável Materializado**: O documento `pre3a3_checkpoint_decision.md` foi materializado na raiz do repositório contendo todas as evidências, o inventário exaustivo de `np.linspace`, as classificações taxonômicas e a matriz de hashes SHA-256 de 64 caracteres.
3. **Preservação Experimental**: Os checkpoints em `models/positioning/` e `training_runs/positioning_v1/` foram preservados sem nenhuma modificação ou deleção.
4. **Condição de Bloqueio para Produção**: Qualquer avanço para exportação ONNX de produção na Fase 3A.3 ou deploy em runtime C# fica formalmente condicionado ao retreinamento do modelo com janelas temporais de 32 frames extraídas dos arquivos físicos `.npz`.

---

## 5. Verification Method (Como Verificar Independentemente)

Para verificar independentemente todas as conclusões deste relatório:

1. **Conferir o Hash do Entregável**:
   ```powershell
   Get-FileHash pre3a3_checkpoint_decision.md -Algorithm SHA256
   # Esperado: 0D02D3D1EFB3C5655B3A0134CCC57EE6034A5C86C069EAE36C91B26046845772
   ```

2. **Inspecionar a Ocorrência Sintética de `np.linspace`**:
   ```powershell
   Select-String -Path tools/phase3a_training/data_utils.py -Pattern "np.linspace" -Context 2,2
   # Linha 226: step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1)
   ```

3. **Verificar a Conexão com o Loop de Treinamento**:
   ```powershell
   Select-String -Path tools/phase3a_training/train_full.py -Pattern "batch\[.history.\]" -Context 1,2
   # Linha 162: history=batch["history"]
   ```

4. **Executar a Suíte de Testes da Fase 3A**:
   ```powershell
   pytest tests/test_phase3a_positioning_training.py
   # Esperado: 20 passed em ~3s
   ```

5. **Condição de Invalidação**:
   Este laudo seria invalidado se for comprovado que existe no código de `train_full.py` uma rotina de carga de tensores do disco que lê diretamente arrays `X` dos arquivos `.npz` e os entrega ao `PositioningTransformerV1`. Conforme auditado pelo Graph Analyst e verificado por este auditor, tal rotina inexiste no pipeline da Fase 3A (0 correspondências de `np.load` em `tools/phase3a_training/`).
