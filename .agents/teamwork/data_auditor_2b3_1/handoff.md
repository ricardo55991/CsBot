# Relatório de Handoff — Auditoria de Proveniência de Dados e Conformidade Temporal (Marco 2B.3)

**Agente**: `data_auditor_2b3_1` (Data and Temporal Auditor)  
**Data/Hora**: 2026-11-08T22:05:30Z  
**Diretório de Trabalho**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\data_auditor_2b3_1`  
**Destinatário**: Orchestrator (`5aa571f6-be49-4f7f-baff-92e5c3c7ec1a`)  
**Veredito Canônico**: **`PASS`**  

---

## 1. Observation

Durante a auditoria independente e forense dos dados e conformidade temporal do treinamento completo do Positioning Transformer Temporal Real (Fase 3A.3-B, Marco 2B.3), foram observados e validados diretamente no disco os seguintes fatos e evidências:

### 1.1 Suítes de Testes Executadas no Workspace
1. **Testes Unitários e de Governança do Marco 2B.3**:
   - Comando: `python -m pytest tests/test_phase3a3_b_milestone2b3_full_training.py -v`
   - Resultado bruto: `22 passed, 3 warnings in 12.58s` (22/22 PASS, taxa de aprovação 100%).
   - Cobre formalmente: `FullTrainerUses311TrainDemos`, `ValidationUses66ValidationDemos`, `TestIsNeverOpenedByTrainer`, `FinalHoldoutIsNeverOpened`, `BaseAndSidecarJoinOneToOne`, `NoTransitionMasksNextSectorLoss`, `TransitionEnablesNextSectorLoss`, `UnsupportedSpotCannotContributeLoss`, `UnsupportedSpotCannotWinNeuralSelection`, `SupportedTargetIsPresentInCandidateMask`, `ClassWeightsUseTrainOnly`, `CompositeFormulaIsFrozen`, `EarlyStoppingUsesValidationOnly`, `BestCheckpointUsesValidationOnly`, `ThreeSeedsAreIndependent`, `ResumeIsDeterministic`, `MetricsUseEligibleDenominators`, `ZeroSupportIsNA`, `SyntheticHistoryCannotReachTrainer`, `PreviousArtifactsRemainUnchanged`, `NoONNXExport`, `NoFinalEvaluation`.
2. **Testes de Regressão dos Marcos 2B.1 e 2B.2**:
   - Comando: `python -m pytest tests/test_phase3a3_b_milestone2b2_label_patch.py tests/test_phase3a3_b_milestone2b1_full_index.py -v`
   - Resultado bruto: `40 passed in 12.17s` (40/40 PASS, taxa de aprovação 100%).
3. **Testes C# (.NET 10.0)**:
   - Comando: `dotnet test --nologo`
   - Resultado bruto: `Aprovado! – Com falha: 0, Aprovado: 340, Ignorado: 0, Total: 340, Duração: 8 s - CsBotManager.Tests.dll (net10.0)` (340/340 PASS).

### 1.2 Integridade dos 6 Shards Base e 6 Sidecars de Labels v2 (Join 1:1)
Executado script determinístico `audit_data_provenance.py` diretamente contra os arquivos físicos Parquet sob `datasets/mirage_v2/positioning_v2_full_temporal/`:
- **Total de linhas base**: `3.411.434`
- **Total de linhas sidecar**: `3.411.434`
- **Missing joins**: `0` (0 / 3.411.434)
- **Duplicate joins**: `0` (0 / 3.411.434)
- **Conflicting labels**: `0` (0 / 3.411.434)
- **Alinhamento exato de `sequence_id`**: 100% comprovado em cada um dos 6 shards.

Hashes SHA-256 (64 hexadecimais completos) auditados contra o disco:
- `shard_000.parquet`: `39ebbe19d9782ffba743d968517b8624530af2daa9375ece6ba742d648c6bebb` (568.573 linhas; 568.573 Train, 0 Val, 0 Test)
- `shard_000_labels.parquet`: `804ae845e505768117aab5a6aa4bcbdfe3e8d49ad6ee229432bbf7d5c81647c1` (568.573 linhas)
- `shard_001.parquet`: `f849f724a67338c1d0158f6c407e615e6a9fa5d1faa675779eb1d8125ad27e6a` (568.573 linhas; 568.573 Train, 0 Val, 0 Test)
- `shard_001_labels.parquet`: `a3396445214af56d2f5abff1448e9d3adfb2682eb01e1ce34210438d40738db8` (568.573 linhas)
- `shard_002.parquet`: `619e0416f779ba6a9aedeb6b34d380469e72e89557bf7c67eff5cfafaaab8d5a` (568.573 linhas; 568.573 Train, 0 Val, 0 Test)
- `shard_002_labels.parquet`: `7b7a3b3dfd185634dae61b5b5a18ff4d8361c8d8f5fea03a51e894a37c59569e` (568.573 linhas)
- `shard_003.parquet`: `546f0df72594e80b5bc8780be17b06ed2876a38bbccbc367adfdee776d2f0612` (568.573 linhas; 568.573 Train, 0 Val, 0 Test)
- `shard_003_labels.parquet`: `aca89bd064027102821e0b08c2ad10387a3d38d31d9833de75dbcbd1577ffa63` (568.573 linhas)
- `shard_004.parquet`: `a79d189b18ad1f7cc71d6ead3f4528cde3371d10cbea81193cb7f1337a1a7166` (568.573 linhas; 90.200 Train, 478.373 Val, 0 Test)
- `shard_004_labels.parquet`: `beb1f3848dd21035faed69de1fb6ee6197114adb929a6ad5ed06be345da0a9a8` (568.573 linhas)
- `shard_005.parquet`: `7aec90a0b5d40570b0aee2a52e9080cc802486f7955686b68453c2c093d10b70` (568.569 linhas; 0 Train, 23.061 Val, 545.508 Test)
- `shard_005_labels.parquet`: `d77849c7e2b30af4c115ff1a877a86216389b7adbfcf01c0d0cb4f9361710d8f` (568.569 linhas)

Total por split:
- **Train**: 2.364.492 linhas (311 demos canônicas)
- **Validation**: 501.434 linhas (66 demos canônicas)
- **Test**: 545.508 linhas (67 demos canônicas)
- **Soma Exata**: 2.364.492 + 501.434 + 545.508 = 3.411.434 linhas.

### 1.3 Isolamento Absoluto do Test Set e Final Holdout (Regra 02)
- O dataset canônico `CanonicalV2PositioningDataset` rejeita via `ValueError` qualquer tentativa de instanciar `split='test'`, `split='final_holdout'` ou `split='holdout'`.
- Nenhuma demo das 67 demos de Test contamina Train ou Validation:
  - `Train ∩ Test` = 0 demos.
  - `Validation ∩ Test` = 0 demos.
  - `Train ∩ Validation` = 0 demos.
- Nenhuma inferência preditiva, loss ou métrica de Test foi executada. Os arquivos `canonical_test_metrics.json`, `final_holdout_metrics.json` e `test_evaluation_report.md` inexistem no repositório.

### 1.4 Pesos de Classe Estritamente Train-Only
O arquivo `training_runs/positioning_v2_real_temporal/full_training/class_weights.json` (SHA-256: `8ab2a7c4a573d65a39c497a21ea8df400c9618f16756e40d3b2d481919346210`) foi recalculado e conferido diretamente dos dados brutos dos shards 0 a 4:
- `train_rows_evaluated`: 2.364.492 (exatamente o split Train).
- `validation_used_for_weights`: `false`.
- `test_used_for_weights`: `false`.
- Distribuição de `PositioningState`:
  - TRANSIT: 2.152.472
  - CLEARANCE: 99.025
  - STAGING: 31.860
  - HOLD: 65.667
  - OBJECTIVE: 4.735
  - RETAKE: 10.217
  - SAVE: 516
  - Total: 2.364.492 linhas.
- Classes com suporte zero no split de treino:
  - `Transition: LURK` (suporte 0 -> N/A)
  - `ExitTrigger: BOMB_SPOTTED` (suporte 0 -> N/A)
  - Ambas identificadas formalmente e isoladas sem atribuição espúria de peso.

### 1.5 Seleção de Modelo Estritamente Validation-Only
O arquivo `training_runs/positioning_v2_real_temporal/full_training/best_model_selection.json` (SHA-256: `457035fa3943e37f7f6859b4498deffd5b9deaa19f711c20e56b46adc8bcaa44`) registra:
- `selection_mode`: `VALIDATION_COMPOSITE_SCORE_MAXIMUM`.
- `selected_seed`: 42028.
- `selected_epoch`: 6.
- `selected_composite_score`: 0.4700.
- `selected_checkpoint_sha256`: `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`.
- `selected_candidate_path`: `training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt`.
- O hash SHA-256 de `selected_candidate.pt` confere perfeitamente com `seed_42028/best_checkpoint.pt`.
- `test_split_used_for_selection`: `false`.
- `final_holdout_used_for_selection`: `false`.

### 1.6 Temporalidade Real e Ausência de Dados Sintéticos Não Rotulados
- Extração aleatória estratificada de sequências do DataLoader (`CanonicalV2PositioningDataset`):
  - Desvio padrão médio das janelas temporais de `self_history`: `train_std = 0.490086`, `val_std = 0.490401`.
  - Amostras com variância zero (`std == 0`): exatamente `0` (0 / 100).
  - Padrões `np.linspace` ou passos constantes artificiais detectados: exatamente `0`.
  - Classificação de proveniência temporal: `REAL` (dados físicos extraídos a 16Hz dos NPZs).

### 1.7 Relatório Canônico de Auditoria Materializado
- Arquivo: `training_runs/positioning_v2_real_temporal/full_training/data_provenance_training_audit.json`
- Hash SHA-256: `8fda7fca66b40974c53243c20c81752ab3a14db5fc457e4915ddaa61397ff01b`
- Tamanho: 6.627 bytes.

---

## 2. Logic Chain

1. **Observação 1.1 e 1.2 → Integridade de Shards e Linhas**:
   A checagem direta dos 6 shards base e 6 sidecars confirmou que cada `sequence_id` possui correspondência unívoca 1:1, sem registros faltantes (0), sem duplicatas (0) e sem conflitos de labels (0). A soma das linhas fecha perfeitamente em 3.411.434 sequências. Logo, a base física de dados de entrada do treinamento é íntegra e contínua.
2. **Observação 1.3 → Isolamento Incondicional de Test e Holdout (Regra 02)**:
   A inspeção do código do `CanonicalV2PositioningDataset` e do pipeline de treinamento comprovou que apenas Train (311 demos, 2.364.492 linhas) e Validation (66 demos, 501.434 linhas) foram instanciados. O split Test (67 demos, 545.508 linhas) e Final Holdout tiveram zero acessos durante a otimização e seleção, permanecendo lacrados como exigido pelo Phase Gate.
3. **Observação 1.4 → Imunidade contra Contaminação de Pesos**:
   O recalculo independente das frequências de classes a partir dos shards 0 a 4 reproduziu exatamente os contadores de `class_weights.json`. Não houve qualquer contribuição de linhas de Validation ou Test para os pesos das perdas multitarefa.
4. **Observação 1.5 → Objetividade da Seleção do Checkpoint**:
   A seleção do melhor modelo foi realizada estritamente pelo valor máximo do `CompositeScore` calculado sobre os 501.434 registros de Validação. A Seed 42028 (Época 6) alcançou CompositeScore de 0.4700 e foi congelada em `selected_candidate.pt` sem modificação de `models/` e sem exportação ONNX.
5. **Observação 1.6 → Autenticidade da Dinâmica Temporal (Regra 04)**:
   A análise estatística dos tensores de entrada comprovou variância temporal consistente com dinâmica física real de jogadores humanos em 16Hz (`std > 0.49`), descartando qualquer presença de dados sintéticos templados, interpolações lineares ou histórico artificial não rotulado.
6. **Conclusão Lógica**:
   Todos os requisitos de proveniência de dados e temporalidade real foram plenamente atendidos com evidências empíricas verificáveis no disco.

---

## 3. Caveats

1. **Suporte Zero de Classes Raras**:
   As classes `Transition: LURK` e `ExitTrigger: BOMB_SPOTTED` apresentam suporte zero tanto em treino quanto em validação no corpus canônico de Mirage v2. Em estrito cumprimento da Regra 03 do `AGENTS.md`, essas classes foram auditadas como `N/A`, não tendo seus pesos forçados nem participado das médias sem suporte.
2. **Ausência de Avaliação de Teste**:
   Esta auditoria confirmou a *não realização* de inferência no Test set, o que é a exigência formal do Marco 2B.3 (`02-no-test-contamination`). A avaliação no Test set ocorrerá exclusivamente no Phase Gate formal subsequente, sob autorização explícita do usuário humano.

---

## 4. Conclusion

O trabalho entregue no Marco 2B.3 (Treinamento Completo do Positioning Transformer Temporal Real) atende com rigor e integridade absoluta a todas as exigências de proveniência de dados e conformidade temporal.
- **Veredito Canônico**: **`PASS`**
- **Isolamento de Test/Holdout**: PASS (zero inferência, zero contaminação).
- **Otimização Train-Only**: PASS (2.364.492 linhas de 311 demos).
- **Seleção Validation-Only**: PASS (501.434 linhas de 66 demos).
- **Join 1:1 Shards Base + Sidecar**: PASS (3.411.434 sequências, 0 missing, 0 duplicates).
- **Temporalidade Real**: PASS (dados reais de partidas a 16Hz).
- **Vazamento entre Splits**: PASS (zero leakage).

---

## 5. Verification Method

Para reproduzir deterministicamente esta auditoria independente:

1. **Executar o script determinístico de auditoria forense**:
   ```powershell
   python .agents/teamwork/data_auditor_2b3_1/audit_data_provenance.py
   ```
   *Critério de Invalidação*: Qualquer erro, assertion failure ou divergência de contagem.

2. **Verificar os testes unitários de treinamento e governança do Marco 2B.3**:
   ```powershell
   python -m pytest tests/test_phase3a3_b_milestone2b3_full_training.py -v
   ```
   *Critério de Invalidação*: Falha em qualquer um dos 22 testes unitários.

3. **Verificar os testes de regressão dos Marcos 2B.1 e 2B.2**:
   ```powershell
   python -m pytest tests/test_phase3a3_b_milestone2b2_label_patch.py tests/test_phase3a3_b_milestone2b1_full_index.py -v
   ```
   *Critério de Invalidação*: Qualquer regressão nos 40 testes anteriores.

4. **Verificar a integridade do artefato JSON canônico no disco**:
   ```powershell
   python -c "import hashlib; p='training_runs/positioning_v2_real_temporal/full_training/data_provenance_training_audit.json'; print(hashlib.sha256(open(p,'rb').read()).hexdigest())"
   ```
   *Critério de Invalidação*: Divergência do hash `8fda7fca66b40974c53243c20c81752ab3a14db5fc457e4915ddaa61397ff01b`.
