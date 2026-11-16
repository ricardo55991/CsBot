# Original User Request

## Parameters

[skip-interview]
How this run was launched; not part of the task.

## Initial Request — 2026-11-07T20:46:45Z

Equipe solicitada: Tier 3 - Alto Risco (Explorer, Graph Analyst, Test Author, Implementer, Mathematical and Statistical Auditor, Data Provenance Auditor, ML Generalization Auditor, Adversarial Reviewer, Success Auditor). Executar o Patch de Governança 1.1 corrigindo exclusivamente as lacunas e falsos positivos da governança e auditar, sem retreinar nem modificar artefatos canônicos, se o checkpoint do Positioning Transformer foi treinado com histórico temporal real ou sintético.

Working directory: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot
Integrity mode: development

## Requirements

### R1. Governança - Correção de Falsos Positivos e Omissões (Patch 1.1)
Corrigir exclusivamente as lacunas e falsos positivos da governança documentados pelo Red Team:
- FP-01: Ajustar regex de SHA-256 com boundaries explícitas para aceitar 64 caracteres hexadecimais completos, reprovar 4 a 63 caracteres isolados ou hashes truncados com reticências, e ignorar exemplos negativos dentro de blocos de código.
- FP-02: Atualizar `post_test_audit.py` para interpretar saídas com `toolResponse`, `tool_response`, `stdout`, `stderr`, `exitCode` e `exit_code` em formatos de `dotnet test`, `pytest` e `unittest`, atribuindo `UNKNOWN` em vez de `0/0 PASS` quando contagens não puderem ser extraídas, e impedindo `PASS` em saídas com exit code de falha.
- FP-03: Implementar distinção estrutural em linters entre afirmação executiva (`EXECUTIVE_CLAIM`), exemplo documental (`DOCUMENTATION_EXAMPLE`) e payload adversarial (`ADVERSARIAL_FIXTURE`) em blocos de código (fenced code blocks), garantindo que exemplos documentais não bloqueiem o relatório enquanto afirmações executivas reais sejam auditadas.
- MISS-S1-02: Implementar parser estrutural de tabelas Markdown para verificar a coluna `Support` e colunas de métricas (`Precision`, `Recall`, `F1`, `Accuracy`, `Balanced Accuracy`), rejeitando qualquer valor numérico quando `Support = 0` (permitindo apenas `N/A` ou `-`).
- MISS-S4-01: Implementar detecção de padrões de IDs de demos suspeitos/templados com consulta cruzada ao catálogo formal de demos existente no repositório (aprovando se o ID existir no catálogo e reprovando como `UNPROVENANCED_TEMPLATE_ID` se inexistente fora de fixtures/documentação).
- MISS-S3-01: Manter a separação de responsabilidades entre o Hook (validação de formato e presença do `artifact_path` relativo ao repositório) e o Phase Gate / Provenance Skill (recalculo físico determinístico do hash SHA-256 de 64 caracteres contra o disco).

### R2. Auditoria e Mapeamento Graphify do Histórico Temporal
Utilizar o Graphify em modo somente leitura para rastrear o fluxo `NPZ → DataLoader → self_history → teammate_history → PositioningTransformerV1.forward → checkpoint`, identificando a função de carga de NPZ, a função construtora de janelas, a linha exata de uso de `np.linspace`, o tensor entregue ao modelo, a diferença entre o DataLoader auditado na Fase 2.2 e o DataLoader de treino, e se Train, Validation e Test usaram o mesmo caminho ou se janelas reais existiam apenas em relatório, gerando `.agents/audit/pre3a3_temporal_history_graph.md` e `.agents/audit/pre3a3_temporal_history_blast_radius.json` sem alterar arquivos de código ou modelo.

### R3. Comparação Determinística entre Fatias NPZ e Saída do DataLoader
Auditar o caminho real de treino das seeds 42026, 42027 e 42028 (script de treino, classe DataLoader, dataset path, code hash, construção de self/teammate history, sequence source, length, feature dimensions e tick source) gerando `training_runs/positioning_v1/pre3a3_history_provenance.json` e `pre3a3_history_provenance.md`. Extrair deterministicamente 200 amostras sob seed 42026 (100 Train, 50 Validation, 50 Test) e verificar se `DataLoader history == NPZ temporal slice` sob tolerância numérica explícita, calculando `ExactMatchRate`, `ToleranceMatchRate`, `SyntheticWindowRate`, `StaticWindowRate`, `MeanTemporalVariance` e `MeanSpatialDisplacement` em `pre3a3_npz_batch_comparison.json` e `pre3a3_npz_batch_comparison.md`.

### R4. Auditoria de Ocorrências de `np.linspace` e Decisão Canônica do Checkpoint
Para cada ocorrência relevante de `np.linspace`, registrar arquivo, linha, função, propósito, source_type, output tensor e se alcança loss de treino, validação ou teste, classificando como `LEGITIMATE_INTERPOLATION`, `LABELED_SYNTHETIC_AUGMENTATION`, `UNLABELED_SYNTHETIC_INPUT`, `REPORT_ONLY` ou `DEAD_CODE`. Emitir a conclusão canônica em `pre3a3_checkpoint_decision.md` entre:
- A: `CHECKPOINT_TEMPORAL_PROVENANCE_VERIFIED`
- B: `CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`
- C: `CHECKPOINT_HISTORY_PROVENANCE_MIXED`
- D: `CHECKPOINT_HISTORY_PROVENANCE_UNRESOLVED`
Se o resultado for B, C ou D, o checkpoint atual deve ser preservado como experimental sem ser apagado, recomendando retreino futuro.

### R5. Governança, Habilitação de Skills e Isolamento Estrito de Papéis
Garantir a disponibilidade da skill `csbot-math-logic-auditor` (localizando a especificação homologada nos relatórios e documentação existentes no repositório e implementando-a caso ainda seja apenas proposta), executar as skills obrigatórias (`csbot-graph-impact`, `csbot-report-skeptic`, `csbot-dataset-forensics`, `csbot-model-validator`, `csbot-phase-gate`), manter isolamento estrito de papéis (Implementer não valida o próprio trabalho, auditores não alteram implementação, Success Auditor não corrige falhas), e respeitar as restrições inegociáveis: não iniciar a Fase 3A.3, não executar retreino/fine-tuning, não modificar checkpoints, datasets canônicos, runtime C# ou modelos ONNX, e não avançar automaticamente de fase.

## Acceptance Criteria

### Testes de Governança
- [ ] Testes unitários para FP-01 (ValidSha256With64CharsPasses, Truncated63CharShaFails, TruncatedShaWithEllipsisFails, ValidShaInsideMarkdownTablePasses, ExampleViolationInsideCodeFenceDoesNotBlockReport) implementados e com 100% de aprovação.
- [ ] Testes unitários para FP-02 (CamelCaseToolResponseIsParsed, SnakeCaseToolResponseIsParsed, DotnetSummaryIsParsed, PytestSummaryIsParsed, MissingSummaryProducesUNKNOWNNotZero, FailedExitCodeCannotProducePASS) e fixtures reais para dotnet test, pytest e unittest implementados e com 100% de aprovação.
- [ ] Testes unitários para FP-03 distinguindo afirmação executiva, exemplo documental e payload adversarial implementados e com 100% de aprovação.
- [ ] Testes unitários para MISS-S1-02 validando tabelas de 3, 4 e 8 colunas, HTML table, Markdown escapado, ordem alterada de colunas e números com vírgula e ponto com Support=0 e rejeição de métricas numéricas implementados e com 100% de aprovação.
- [ ] Testes unitários para MISS-S4-01 validando IDs templados contra o catálogo formal de demos (PASS para IDs reais do catálogo, FAIL como UNPROVENANCED_TEMPLATE_ID para IDs inexistentes) implementados e com 100% de aprovação.
- [ ] Teste fim a fim para MISS-S3-01 (relatório com hash válido de outro arquivo aprovado no Hook e reprovado pelo Phase Gate na validação física) implementado e com 100% de aprovação.
- [ ] Suite dos 5 hooks e suite de Red Team original executada com 12/12 aprovações.
- [ ] 100% de aprovação nos novos testes, zero violações críticas não detectadas (`missed_violations críticos: 0`) e zero falsos positivos críticos (`false_positives críticos: 0`).
- [ ] Todos os scripts Python afetados passam em `py_compile` sem erros sintáticos.

### Auditoria Forense Temporal e Artefatos Materializados
- [ ] `.agents/audit/pre3a3_temporal_history_graph.md` e `.agents/audit/pre3a3_temporal_history_blast_radius.json` materializados no disco refletindo o mapeamento Graphify completo.
- [ ] `training_runs/positioning_v1/pre3a3_history_provenance.json` e `training_runs/positioning_v1/pre3a3_history_provenance.md` materializados no disco cobrindo as seeds 42026, 42027 e 42028.
- [ ] `pre3a3_npz_batch_comparison.json` e `pre3a3_npz_batch_comparison.md` materializados no disco contendo a comparação das 200 amostras com taxas de match e variância.
- [ ] `pre3a3_checkpoint_decision.md` emitido com classificação explícita (A, B, C ou D).
- [ ] Entregáveis `governance_patch_1_1_diff.md`, `governance_patch_1_1_test_report.md`, `governance_patch_1_1_redteam_report.md`, `governance_patch_1_1_false_positive_report.md` e `deliverable_evidence.json` materializados no disco com SHA-256 de 64 caracteres e caminhos relativos ao repositório.
- [ ] Arquivos `missed_violations.json` e `false_positives.json` atualizados com status canônicos (FIXED, ACCEPTED_LAYERED_RESPONSIBILITY, OPEN, NOT_REPRODUCED) preservando o histórico.

### Phase Gate e Finalização
- [ ] Execução do Phase Gate final via `csbot-phase-gate`, `csbot-report-skeptic`, `csbot-dataset-forensics` e `csbot-math-logic-auditor`.
- [ ] Conferência requisito por requisito realizada pelo Success Auditor com emissão do veredito final (`CSBOT_GOVERNANCE_PATCH_1_1_PASS` acompanhado da decisão canônica de proveniência do checkpoint).
- [ ] Nenhuma alteração realizada em runtime C#, modelos ONNX, checkpoints ou datasets canônicos, e nenhuma inicialização de retreino ou da Fase 3A.3.

## Follow-up — 2026-11-07T20:50:23Z

Diretriz adicional do usuário humano para a execução:

"Preserve o isolamento entre implementadores e auditores, não altere os artefatos canônicos e não suavize o veredito de proveniência temporal.

A decisão final deve permanecer exatamente uma entre A, B, C ou D, com evidências reproduzíveis."

Por favor, garanta que todos os subagentes da equipe sigam estritamente estas restrições.


## Follow-up — 2026-11-08T16:10:00Z

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


## Follow-up — 2026-11-08T17:26:33Z

O servidor reiniciou e o usuário solicitou expressamente: "Continue, pois foi interrompido".
Por favor, verifique o status dos subagentes/tarefas da equipe, retome a execução da Fase de Auditoria Independente e prossiga até a conclusão formal do Marco 2B.1 (emissão de relatórios, evidências, teste suite e veredito canônico).

## Follow-up — 2026-11-08T21:18:18Z

# FASE 3A.3-B, MARCO 2B.3:
# TREINAMENTO COMPLETO DO POSITIONING TRANSFORMER TEMPORAL REAL

## DECISÃO DE ENTRADA

Os marcos anteriores concluíram:

    CANONICAL_TEMPORAL_DATALOADER_READY_FOR_PILOT

    REAL_TEMPORAL_POSITIONING_PILOT_READY_FOR_FULL_TRAINING

    FULL_TEMPORAL_INDEX_READY_FOR_FULL_TRAINING

    LABEL_CONTRACT_V2_READY_FOR_FULL_TRAINING

Esta mensagem autoriza:

1. adaptação do modelo ao `label_contract_v2`;
2. treinamento completo nas três seeds canônicas;
3. seleção de candidato usando exclusivamente Validation;
4. auditoria matemática, estatística e de proveniência;
5. comparação com baselines reais.

Esta mensagem não autoriza:

- inferência no Test;
- inferência no Final Holdout;
- exportação ONNX;
- integração C#;
- shadow mode;
- MLMove V2;
- Jump Head;
- deploy.

---

# 1. ORQUESTRAÇÃO COMPACTA

Limites:

    max_active_subagents = 6
    nested_subagents = false
    only_orchestrator_can_delegate = true
    reuse_agents_within_milestone = true
    spawn_only_when_required = true
    kill_all_on_completion = true

Papéis:

1. Orchestrator
2. Model and Training Implementer
3. Data and Temporal Auditor
4. Mathematical and Statistical Auditor
5. ML Generalization Auditor
6. Adversarial Success Auditor

Regras:

- subagentes não criam subagentes;
- implementador não valida o próprio trabalho;
- auditores operam somente leitura;
- Success Auditor não corrige código;
- correção localizada revalida somente o blast radius afetado;
- um único relatório Markdown extenso no encerramento;
- resultados intermediários devem ser JSON ou JSONL;
- executar `kill_all` no encerramento.

Skills obrigatórias:

    csbot-phase-gate
    csbot-report-skeptic
    csbot-dataset-forensics
    csbot-model-validator
    csbot-math-logic-auditor

Hooks devem permanecer em blocking mode.

---

# 2. SNAPSHOT IMUTÁVEL

Criar:

    training_runs/positioning_v2_real_temporal/full_training/
        input_snapshot.json

Registrar hashes completos de:

    git commit
    dataset_manifest.json
    canonical_temporal_splits_v1.json
    label_contract_v2.json
    supervised_spot_mask_v1.json
    seis shards temporais
    seis sidecars de labels
    catálogo de 53 spots
    DataLoader
    modelo
    loss
    script de treino
    configuração
    ambiente Python/PyTorch/CUDA

Registrar também:

    Train = 311 demos
    Validation = 66 demos
    Test = 67 demos

Somente Train e Validation podem ser abertos pelo treinador.

Test pode ser apenas identificado pelo hash no snapshot.

---

# 3. CONTRATO DO MODELO

Criar a arquitetura:

    PositioningTransformerV2RealTemporal

Inputs:

    self_history:
    [batch, 32, 18]

    teammates:
    [batch, 32, 4, 18]

    temporal_mask:
    [batch, 32]

    teammate_mask:
    [batch, 32, 4]

    candidate_mask:
    [batch, 53]

Heads:

## Head A: PositioningState

    TRANSIT
    CLEARANCE
    STAGING
    HOLD
    OBJECTIVE
    RETAKE
    SAVE

## Head B: SectorTransitionOccurs

    NO_TRANSITION
    TRANSITION_OCCURS

## Head C: NextSector

    A
    B
    MID
    CT
    T

Ativa somente quando:

    sector_transition_occurs = TRANSITION_OCCURS
    next_sector_loss_mask = 1

## Head D: CandidateSpotRanking

    53 logits

Loss ativa somente quando:

    spot_loss_mask = 1
    target está presente na candidate_mask
    target possui supervised_spot_mask = 1

Spots com `supervised_spot_mask = 0`:

- não contribuem para SpotLoss;
- não podem ser target neural positivo;
- não podem vencer seleção neural supervisionada;
- permanecem disponíveis para Utility AI e futuras demos.

## Head E: Transition

    ADVANCE
    HOLD
    FALLBACK
    ROTATE
    CONVERGE
    COVER
    LURK

## Head F: ExitTrigger

    TIME
    CONTACT
    FIRST_KILL
    TEAMMATE_DEATH
    BOMB_SPOTTED
    BOMB_PLANTED
    UTILITY_EXPIRED
    TACTIC_REVISION

---

# 4. JOIN DOS LABELS

Consumir:

    shards temporais base
    +
    label_sidecar_v2

Join obrigatório:

    sequence_id 1:1

Antes de treinar, validar:

    base rows = 3.411.434
    sidecar rows = 3.411.434
    missing joins = 0
    duplicate joins = 0
    conflicting labels = 0

Verificar hashes dos seis pares de shards.

Falha no join:

    FULL_TRAINING_LABEL_JOIN_FAILED

e encerrar sem treinamento.

---

# 5. PROTEÇÕES DE LOSS

Exigir por batch:

    NextSectorLoss = 0
    quando NO_TRANSITION

    NextSectorLoss > 0
    somente em TRANSITION_OCCURS elegível

    SpotLoss = 0
    em TRANSIT

    SpotLoss = 0
    em UNMAPPED

    SpotLoss = 0
    para spot sem suporte

    SpotLoss > 0
    somente para target supervisionado e presente na mask

Usar pesos calculados apenas no Train.

Registrar:

    suporte bruto
    effective-number weights
    clamp
    pesos finais
    sampler configuration

Não calcular pesos com Validation.

Não duplicar episódios para preencher classes.

---

# 6. CONFIGURAÇÃO CONGELADA

Arquitetura inicial:

    hidden_dim = 192
    transformer_layers = 3
    attention_heads = 6
    feedforward_dim = 768
    dropout = 0.10
    sequence_length = 32

Otimização:

    optimizer = AdamW
    learning_rate = 3e-4
    weight_decay = 1e-2
    gradient_clip_norm = 1.0
    warmup_ratio = 0.05
    max_epochs = 40
    early_stopping_patience = 6

Batch size:

    64 preferencial

Pode ser reduzido por VRAM/RAM, desde que:

- seja documentado antes do treino;
- gradient accumulation preserve o effective batch size;
- todas as seeds usem configuração equivalente.

Scheduler:

    cosine decay

Não fazer busca ampla de hiperparâmetros.

---

# 7. PREFLIGHT COMPUTACIONAL

Antes das três seeds, executar:

    100 batches Train
    20 batches Validation

Medir:

    samples per second
    batch latency
    peak RAM
    peak VRAM, quando aplicável
    estimated epoch duration
    estimated three-seed duration
    DataLoader wait ratio
    cache hit rate
    invalid batches

Se o tempo estimado for excessivo:

- otimizar streaming, cache ou batching;
- não alterar labels;
- não subamostrar silenciosamente;
- não trocar para o índice piloto.

Gerar:

    compute_preflight.json

---

# 8. TREINAMENTO MULTI-SEED

Seeds:

    42026
    42027
    42028

Para each seed:

- inicialização independente;
- ordem do Train determinística por seed;
- mesmos splits;
- mesma arquitetura;
- mesma loss;
- mesmos pesos de classe;
- mesma política de early stopping;
- Validation para seleção;
- nenhum acesso ao Test;
- nenhum acesso ao Final Holdout.

Salvar por seed:

    config.json
    input_snapshot.json
    environment.json
    train_metrics.jsonl
    validation_metrics.jsonl
    best_checkpoint.pt
    last_checkpoint.pt
    checkpoint_hashes.json
    class_weights.json
    learning_curves.json
    confusion_counts_validation.json
    support_validation.json

Suportar resume determinístico após interrupção.

---

# 9. MÉTRICA COMPOSTA CONGELADA

Usar:

    CompositeScore =
        0.20 * StateMacroF1
      + 0.10 * SectorTransitionMacroF1
      + 0.10 * NextSectorMacroF1
      + 0.25 * SpotMRR
      + 0.20 * TransitionMacroF1
      + 0.15 * ExitTriggerMacroF1

Regras:

- métricas condicionais usam somente denominadores elegíveis;
- classes com support zero aparecem como N/A;
- Macro F1 usa classes suportadas;
- fórmula e pesos não podem ser alterados após observar os resultados;
- seleção do checkpoint usa somente Validation.

---

# 10. MÉTRICAS DE VALIDATION

## PositioningState

    Accuracy
    supported-class Macro F1
    Balanced Accuracy
    F1 por classe
    support por classe
    predicted distribution

## SectorTransitionOccurs

    Macro F1
    Balanced Accuracy
    precision/recall por classe
    confusion matrix

## NextSector

Somente exemplos elegíveis:

    eligible count
    Macro F1
    Balanced Accuracy
    F1 por setor
    confusion matrix
    masked count

## CandidateSpotRanking

Somente exemplos supervisionados e elegíveis:

    eligible count
    MRR
    Top-1
    Top-3
    Top-5
    NDCG@5
    invalid masked selection
    unsupported-spot selection count

## Transition

    Macro F1
    F1 por classe
    support por classe

## ExitTrigger

    Macro F1
    F1 por classe
    support por classe

---

# 11. GATES DE VALIDATION

## PositioningState

    supported-class Macro F1 >= 0.45
    Balanced Accuracy >= 0.50

Classes prioritárias:

    CLEARANCE
    HOLD
    STAGING
    RETAKE
    OBJECTIVE
    SAVE

## SectorTransitionOccurs

    Macro F1 >= 0.55
    Balanced Accuracy >= 0.55

## NextSector

Somente transições elegíveis:

    Macro F1 >= 0.50
    Balanced Accuracy >= 0.50
    pelo menos 4 setores com suporte real

## CandidateSpotRanking

    MRR >= 0.60
    Top-1 >= 0.45
    Top-5 >= 0.80
    invalid masked selection = 0
    unsupported-spot selection = 0

## Transition

    Macro F1 >= 0.60

## ExitTrigger

    Macro F1 >= 0.45

Não aprovar com accuracy geral isolada.

---

# 12. COMPARAÇÕES OBRIGATÓRIAS

Comparar na mesma Validation:

1. modelo temporal real completo;
2. baseline de último frame real;
3. frequency ranker;
4. baseline logístico;
5. checkpoint sintético apenas como referência histórica.

O modelo temporal real deve:

- superar os baselines reais;
- superar último frame em pelo menos duas métricas temporais;
- atingir todos os gates;
- demonstrar ganho em estados ou transições dependentes de sequência.

Não exigir superioridade sobre o modelo sintético em toda métrica bruta.

---

# 13. PREVENÇÃO DE COLAPSO

Monitorar por época:

    predicted TRANSIT rate
    actual TRANSIT rate
    predicted NO_TRANSITION rate
    actual NO_TRANSITION rate
    non-TRANSIT recall
    transition recall
    rare-state recall
    unsupported-spot prediction count
    gradient norm por head

Alertas:

    STATE_COLLAPSE
    SECTOR_TRANSITION_COLLAPSE
    NEXT_SECTOR_COLLAPSE
    SPOT_POPULARITY_COLLAPSE
    RARE_STATE_COLLAPSE

Não esconder colapso com accuracy geral.

---

# 14. SELEÇÃO DO CANDIDATO

Após concluir as três seeds:

1. comparar a melhor época de cada seed;
2. usar somente Validation;
3. calcular média, desvio padrão e amplitude;
4. selecionar maior CompositeScore que cumpra todos os gates;
5. auditar diferenças entre seeds;
6. congelar o candidato selecionado.

Salvar:

    selected_candidate.pt

somente em:

    training_runs/positioning_v2_real_temporal/full_training/

Não copiar para:

    models/positioning/

Não exportar ONNX.

---

# 15. AUDITORIAS INDEPENDENTES

## Mathematical and Statistical Auditor

Recalcular diretamente:

    supports
    confusion counts
    Macro F1
    Balanced Accuracy
    Spot MRR
    Top-k
    CompositeScore
    seed mean/std
    denominadores condicionais

## Data Provenance and Temporal Auditor

Confirmar:

    Train-only optimization
    Validation-only selection
    zero Test inference
    zero Final Holdout inference
    temporal inputs correspondem aos NPZ
    sidecar join 1:1
    no synthetic history
    no cross-split access

## ML Generalization Auditor

Analisar:

    Train/Validation gap
    class collapse
    seed stability
    baseline comparison
    rare-state behavior
    temporal gain
    overfitting

## Adversarial Success Auditor

Tentar invalidar:

    conditional masks
    spot supervision mask
    class weights
    checkpoint selection
    early stopping
    composite score
    seed independence
    absence of Test usage

---

# 16. TESTES

Adicionar no mínimo:

1. FullTrainerUses311TrainDemos
2. ValidationUses66ValidationDemos
3. TestIsNeverOpenedByTrainer
4. FinalHoldoutIsNeverOpened
5. BaseAndSidecarJoinOneToOne
6. NoTransitionMasksNextSectorLoss
7. TransitionEnablesNextSectorLoss
8. UnsupportedSpotCannotContributeLoss
9. UnsupportedSpotCannotWinNeuralSelection
10. SupportedTargetIsPresentInCandidateMask
11. ClassWeightsUseTrainOnly
12. CompositeFormulaIsFrozen
13. EarlyStoppingUsesValidationOnly
14. BestCheckpointUsesValidationOnly
15. ThreeSeedsAreIndependent
16. ResumeIsDeterministic
17. MetricsUseEligibleDenominators
18. ZeroSupportIsNA
19. SyntheticHistoryCannotReachTrainer
20. PreviousArtifactsRemainUnchanged
21. NoONNXExport
22. NoFinalEvaluation

Manter toda a suíte C# verde.

---

# 17. ENTREGÁVEIS

Criar:

    training_runs/positioning_v2_real_temporal/full_training/
        input_snapshot.json
        compute_preflight.json
        frozen_training_config.json
        frozen_composite_formula.json
        class_weights.json
        seed_42026/
        seed_42027/
        seed_42028/
        three_seed_comparison.json
        baseline_comparison.json
        temporal_gain_report.json
        collapse_monitoring.json
        best_model_selection.json
        selected_candidate.pt
        mathematical_training_audit.json
        data_provenance_training_audit.json
        ml_generalization_audit.json
        adversarial_training_audit.json
        milestone_2b3_evidence_matrix.json
        deliverable_evidence.json
        marco_2b3_final_report.md

Produzir somente um relatório Markdown extenso:

    marco_2b3_final_report.md

Demais artefatos devem ser JSON ou JSONL.

---

# 18. EFICIÊNCIA

Não repetir Graphify.

Não repetir materialização do índice.

Não repetir patch dos labels.

Não repetir Red Team da governança.

Usar streaming, memory mapping e bounded cache.

Máximo:

    6 subagentes ativos

Sem subsubagentes.

Executar `kill_all` no encerramento.

---

# 19. DECISÃO

Se o join, preflight computacional ou máscaras falharem:

    FULL_TRAINING_ENTRY_GATE_FAILED

Se o treinamento falhar estruturalmente:

    REAL_TEMPORAL_POSITIONING_FULL_TRAINING_FAILED

Se as três seeds concluírem, mas algum gate não for atingido:

    REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL

Se as três seeds concluírem e todos os gates de Validation passarem:

    REAL_TEMPORAL_POSITIONING_CANDIDATE_READY_FOR_FINAL_EVALUATION

Não executar Test.

Não executar Final Holdout.

Não exportar ONNX.

Não integrar ao runtime.

Aguardar autorização humana.

---

## CONTEXTO E ARTEFATOS CONGELADOS DO MARCO 2B.2
- Shards temporais base: datasets/mirage_v2/positioning_v2_full_temporal/shard_000.parquet a shard_005.parquet (3.411.434 sequências, 444 demos).
- Sidecars de labels v2: datasets/mirage_v2/positioning_v2_full_temporal/label_sidecar_v2/shard_000_labels.parquet a shard_005_labels.parquet (11 campos canônicos, join 1:1 exato).
- Contrato v2: datasets/mirage_v2/contracts/label_contract_v2.json (Head A: SectorTransitionOccurs binária; Head B: NextSector com 5 classes sem DYNAMIC; Head C: CandidateSpotRanking 53 spots; Head D: Transition; Head E: ExitTrigger).
- Máscara de spots: datasets/mirage_v2/positioning_v2_full_temporal/supervised_spot_mask_v1.json (27 suportados mask=1; 26 sem suporte mask=0).
- Catálogo de spots: datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json (53 spots).
- Relatório de fechamento do Marco 2B.2: training_runs/positioning_v2_real_temporal/marco_2b2_final_report.md.

## Follow-up — 2026-11-09T00:24:00Z

# FASE 2A-INTERMEDIATE:
# ESTUDO DE VIABILIDADE E AQUISIÇÃO DO CORPUS MIRAGE INTERMEDIÁRIO

## 0. CONTEXTO E NOVA ESTRATÉGIA

O projeto possui atualmente um corpus profissional da Mirage com:

    444 demos NPZ
    3.411.434 sequências temporais
    catálogo de 53 spots
    contratos de labels V2
    DataLoader temporal canônico
    sidecars de labels versionados
    pipeline auditado e pronto para treinamento

Esse corpus profissional permanece válido e deve ser integralmente preservado.

Entretanto, o objetivo do Positioning Transformer não é reproduzir apenas
comportamentos de equipes profissionais, que podem incluir:

- antistrats;
- posições especializadas;
- boosts coordenados;
- setups específicos contra um adversário;
- defaults dependentes de comunicação formal;
- rotações baseadas em protocolos de equipe;
- spots raros ou exóticos.

Queremos investigar um segundo domínio de dados composto por partidas de nível
intermediário e intermediário-alto, nas quais jogadores competentes tendem a
utilizar posicionamentos mais padronizados e reconhecíveis.

Hipótese:

    partidas intermediárias organizadas podem fornecer melhor supervisão
    para posições padrão de matchmaking e PUG;

    partidas profissionais podem fornecer melhor supervisão para:
    - mira;
    - utility;
    - execuções coordenadas;
    - retakes avançados;
    - movimento de alto nível;
    - especializações táticas.

Esta hipótese ainda não está comprovada.

A fase atual deve testá-la com dados e não tratá-la como conclusão.

---

# 1. PAUSA FORMAL DO TREINAMENTO ATUAL

Pausar:

    FASE 3A.3-B, MARCO 2B.3

Não executar:

- treinamento completo das três seeds;
- avaliação no Test;
- consulta ao Final Holdout;
- exportação ONNX;
- integração C#;
- shadow mode;
- MLMove V2;
- Jump Head.

Preservar integralmente:

    datasets/mirage_v2/
    training_runs/positioning_v2_real_temporal/
    catálogo Mirage V3;
    seis shards temporais;
    sidecars label_contract_v2;
    manifests;
    checkpoints anteriores;
    piloto temporal;
    relatórios forenses.

Criar marcador:

    PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY

A pausa não invalida o trabalho existente.

---

# 2. OBJETIVO DESTA FASE

Esta fase deve responder:

1. Existem fontes legais e tecnicamente acessíveis de demos Mirage de nível
   intermediário?

2. É possível comprovar o nível dos jogadores no momento ou próximo da partida?

3. FACEIT, Valve Competitive ou Valve Premier oferecem metadados suficientes?

4. Podemos obter inicialmente 20 a 50 demos sem contornar autenticação,
   permissões ou termos de serviço?

5. Partidas intermediárias realmente apresentam posicionamento mais
   padronizado que o corpus profissional?

6. Os 26 spots atualmente sem suporte profissional aparecem nesse domínio?

7. Existem posições padrão novas que deveriam entrar no catálogo?

8. O corpus intermediário apresenta qualidade suficiente para:
   - Positioning Transformer;
   - CandidateSpotRanking;
   - StateHead;
   - SectorTransition;
   - retakes;
   - post-plants?

9. Devemos no futuro treinar:
   - modelo intermediário separado;
   - modelo profissional separado;
   - modelo misto condicionado por domínio;
   - ou alguma combinação hierárquica?

Não executar treinamento nesta fase.

---

# 3. ORQUESTRAÇÃO COMPACTA

Limites:

    max_active_subagents = 6
    nested_subagents = false
    only_orchestrator_can_delegate = true
    reuse_agents_within_milestone = true
    spawn_only_when_required = true
    kill_all_on_completion = true

Papéis:

1. Orchestrator
2. Data Acquisition Researcher
3. Dataset and Metadata Implementer
4. Mathematical and Statistical Auditor
5. Data Provenance and Compliance Auditor
6. Adversarial Success Auditor

Convocar CS2 Domain Reviewer somente na análise espacial final.

Regras:

- subagentes não criam subagentes;
- implementador não valida o próprio trabalho;
- auditores operam somente leitura;
- nenhuma credencial pode ser escrita em relatório;
- nenhum cookie ou senha pode ser commitado;
- não usar scraper que viole autenticação ou acesso restrito;
- não contornar limites de plataforma;
- não baixar em massa antes do piloto;
- não avançar automaticamente.

Skills obrigatórias:

    csbot-phase-gate
    csbot-report-skeptic
    csbot-dataset-forensics
    csbot-graph-impact
    csbot-math-logic-auditor

Hooks devem permanecer em blocking mode.

---

# 4. SEPARAÇÃO FORMAL DOS DOMÍNIOS

Criar contrato:

    datasets/mirage_domains/domain_contract_v1.json

Domínios iniciais:

    PROFESSIONAL
    INTERMEDIATE_COMPETITIVE
    UNKNOWN

Subdomínios:

    PROFESSIONAL_HLTV
    FACEIT_LEVEL_5_6
    FACEIT_LEVEL_7_8
    FACEIT_LEVEL_9_10
    VALVE_COMPETITIVE_MAP_RANK
    VALVE_PREMIER_RATING
    VALVE_OPT_IN_UNKNOWN_RANK

Não converter automaticamente entre:

    Competitive rank
    Premier rating
    FACEIT level
    FACEIT Elo

Cada demo deve preservar seu sistema original de classificação.

Campos obrigatórios:

    domain_id
    platform
    rank_system
    skill_level
    elo_or_rating
    rank_at_collection_time
    rank_at_match_time_if_available
    map_specific_rank
    map_name
    match_date
    region
    source
    source_license
    acquisition_method
    consent_type
    metadata_confidence
    exclusion_reason

---

# 5. FONTES A INVESTIGAR

## Fonte A: FACEIT

Investigar oficialmente:

    FACEIT Data API
    FACEIT Downloads API
    Match endpoints
    Player skill level
    Player Elo
    Demo resource URLs
    Demo-ready events/webhooks

Não assumir que a Data API comum autoriza download.

Verificar:

    necessidade de aplicação;
    token e scopes;
    prazo de aprovação;
    limites de requisição;
    política de armazenamento;
    disponibilidade histórica;
    presença de demo por partida;
    disponibilidade de Mirage;
    metadados dos dez jogadores;
    nível no momento da partida;
    licença ou restrições de uso para ML.

Preparar solicitação de acesso ao Downloads API, mas não enviar sem aprovação
humana se envolver termos legais ou cadastro externo.

## Fonte B: Valve Competitive e Premier opt-in

Investigar somente métodos legítimos:

    Steam personal game data;
    share codes;
    match-history authentication codes;
    CS2 Game Coordinator;
    autorização individual do jogador;
    coleta voluntária.

Não armazenar:

    senha Steam;
    Steam Guard secret;
    session cookie;
    steamLoginSecure;
    credenciais pessoais;

no repositório, relatório ou configuração versionada.

Se o método exigir credenciais persistentes:

    SECURITY_REVIEW_REQUIRED

Não criar uma infraestrutura de coleta pública sem consentimento.

## Fonte C: datasets públicos

Pesquisar datasets existentes que ofereçam:

    arquivo DEM;
    Mirage;
    data recente;
    metadado de habilidade;
    licença compatível;
    origem rastreável;
    integridade verificável.

Não assumir rank com base em nome, rating do jogador ou qualidade visual.

## Fonte D: contribuições voluntárias

Projetar, sem implementar ainda, um fluxo opt-in para jogadores fornecerem:

    SteamID64;
    share code;
    sistema de rank;
    rank ou rating;
    data da partida;
    consentimento;
    autorização de uso para pesquisa e treinamento.

---

# 6. DEFINIÇÃO DO DOMÍNIO INTERMEDIÁRIO

Não usar apenas o nome informal "AK/Águia".

Para o piloto FACEIT, utilizar inicialmente:

    FACEIT Level 5–6:
    intermediate

    FACEIT Level 7–8:
    upper-intermediate

Não incluir inicialmente como corpus principal:

    FACEIT Level 1–4
    FACEIT Level 9–10
    professional teams
    academy teams formalmente estruturados
    unknown skill

Esses buckets podem ser avaliados separadamente.

Para Valve Competitive, aceitar como candidatos:

    Master Guardian I
    Master Guardian II
    Master Guardian Elite
    Distinguished Master Guardian
    Legendary Eagle
    Legendary Eagle Master

Não presumir que esses ranks são equivalentes a FACEIT 5–8.

Para Premier, não definir bucket antes de auditar a distribuição e a temporada.

---

# 7. CRITÉRIOS DE ACEITAÇÃO DE DEMO

Uma demo candidata deve possuir:

    map = de_mirage
    formato Source 2 legível
    data recente
    patch compatível
    lifecycle completo
    mínimo de 16 rounds, salvo overtime ou partida válida curta justificada
    dez jogadores ou substituições explicadas
    posições finitas
    rounds identificáveis
    lados CT/TR válidos
    C4 e eventos suficientes
    rank ou skill metadata rastreável
    fonte e licença registradas

Excluir ou sinalizar:

    abandono precoce
    surrender precoce
    demo corrompida
    warmup sem partida
    jogadores ausentes
    rank desconhecido
    suspeita forte de smurf
    suspeita forte de cheat
    múltiplas demos duplicadas
    partidas dos mesmos jogadores em excesso
    patch incompatível
    Mirage antiga com geometria divergente

Não excluir por derrota, baixa pontuação ou estilo incomum sem critério formal.

---

# 8. PILOTO DE AQUISIÇÃO

Meta inicial:

    20 a 50 demos Mirage

Preferência:

    10–25 FACEIT Level 5–6
    10–25 FACEIT Level 7–8

Se o Downloads API oficial ainda não estiver disponível:

- não contornar restrições;
- executar somente a descoberta e inventário;
- preparar downloader em modo dry-run;
- testar com demos legitimamente acessíveis;
- emitir `DOWNLOAD_ACCESS_PENDING`.

Não escalar para 200 demos nesta fase.

Organização:

    datasets/mirage_domains/intermediate_competitive/
        raw_demos/
        archives/
        metadata/
        manifests/
        quarantine/
        processed_npz/
        reports/

Separar do corpus profissional:

    datasets/mirage_domains/professional/

Não mover nem renomear o corpus profissional atual sem plano de migração.

---

# 9. DOWNLOADER SEGURO E REPRODUTÍVEL

Se uma fonte oficial estiver aprovada, implementar:

    tools/intermediate_demo_acquisition/

Componentes:

    discover_matches.py
    fetch_match_metadata.py
    validate_skill_bucket.py
    download_demo.py
    verify_archive.py
    extract_demo.py
    deduplicate_demo.py
    build_manifest.py
    resume_download.py

Requisitos:

    resumable downloads
    exponential backoff
    rate limiting
    checksum
    archive validation
    decompression segura
    duplicate detection
    dry-run mode
    allowlist de domínio
    audit log
    credential redaction
    retry limit
    quarantine de arquivos inválidos

Segredos:

    variáveis de ambiente
    ou secret store local

Nunca:

    JSON versionado
    Markdown
    logs
    fixture pública
    commit

---

# 10. MANIFESTO DO CORPUS INTERMEDIÁRIO

Criar:

    intermediate_demo_inventory_v1.json

Campos:

    demo_id
    match_id
    source
    source_url_reference
    platform
    match_date
    download_date
    map
    patch
    region
    rank_system
    player_skill_levels
    median_skill_level
    minimum_skill_level
    maximum_skill_level
    mixed_skill_match
    demo_sha256
    archive_sha256
    file_size
    round_count
    player_count
    accepted
    rejection_reason
    license
    consent
    parser_version

Não publicar URLs assinadas, tokens ou dados pessoais desnecessários.

SteamIDs devem ser pseudonimizados nos relatórios derivados.

---

# 11. EXTRAÇÃO PILOTO

Reutilizar o pipeline canônico de NPZ sempre que compatível.

Não modificar o corpus profissional.

Gerar:

    intermediate_npz_manifest_v1.json

Validar:

    posição
    velocidade
    view angles
    crouch
    weapon
    team
    slot
    round lifecycle
    bomb events
    plant
    defuse
    deaths
    kills
    utility events quando disponíveis

Executar comparação entre DEM e NPZ para amostra determinística.

Exigir:

    finite coordinates
    monotonic ticks
    no round crossing
    valid player slots
    valid CT/TR mapping
    zero synthetic history

---

# 12. MÉTRICAS DE PADRONIZAÇÃO CT

Para cada round CT, medir:

    initial setup after freeze time
    A occupancy
    Mid occupancy
    B occupancy
    2-1-2 setup rate
    heavy-A rate
    heavy-B rate
    empty-site rate
    double-stack rate
    anchor dwell
    first rotation tick
    rotation distance
    unnecessary rotation proxy
    retake frequency
    save frequency
    sector stability
    spot recurrence

Definir `2-1-2` por ocupação espacial e papel, não por nome do jogador.

Não usar resultado do round como feature futura.

Resultado pode ser usado apenas para análise posterior.

---

# 13. MÉTRICAS DE PADRONIZAÇÃO TR

Medir:

    default spread
    grouped execute rate
    solo lurk rate
    bomb carrier isolation
    entry order consistency
    trade spacing
    site commitment time
    mid-control rate
    split-A rate
    split-B rate
    fake rate
    post-plant convergence
    save rate
    spot recurrence
    transition recurrence

Distinguir:

    default organizado
    dispersão aleatória
    execute
    rush
    fake
    late-round adaptation

Não classificar todo round lento como default.

---

# 14. COMPARAÇÃO COM O CORPUS PROFISSIONAL

Comparar usando políticas idênticas:

    PROFESSIONAL
    FACEIT_LEVEL_5_6
    FACEIT_LEVEL_7_8

Métricas:

    unique position clusters
    cluster radius
    cluster entropy
    recurring spot rate
    top-spot concentration
    sector occupancy
    dwell distribution
    transition diversity
    2-1-2 rate
    retake rate
    post-plant pattern diversity
    role stability
    setup stability
    player diversity
    team diversity

Calcular:

    Jensen-Shannon divergence
    Wasserstein distance quando aplicável
    confidence intervals
    bootstrap by match
    effective sample size

Não tratar janelas do mesmo round como amostras independentes nos intervalos
de confiança.

Usar partida ou round como unidade de bootstrap, conforme a métrica.

---

# 15. ANÁLISE DOS 53 SPOTS

Para cada spot do catálogo atual, calcular por domínio:

    support sequences
    support episodes
    unique demos
    unique matches
    unique players
    unique teams/stacks
    median dwell
    position variance
    approach direction
    exit direction
    primary aim distribution
    state distribution
    role distribution
    side
    bombsite

Classificar:

    CROSS_DOMAIN_CONFIRMED
    PROFESSIONAL_CONFIRMED
    INTERMEDIATE_CONFIRMED
    HUMAN_VALIDATED_ONLY
    DOMAIN_SPECIFIC_PRO
    DOMAIN_SPECIFIC_INTERMEDIATE
    INSUFFICIENT_SUPPORT

Verificar especificamente os 26 spots sem suporte profissional.

Não promover spot automaticamente.

Não alterar coordenadas nesta fase.

---

# 16. DESCOBERTA DE NOVOS SPOTS

Minerar clusters intermediários fora dos 53 spots.

Critérios piloto:

    minimum episodes = 10
    minimum matches = 5
    minimum players = 10
    preferred cluster radius <= 96 units
    consistent dwell
    identifiable tactical purpose

Classificações:

    CANDIDATE_STANDARD_POSITION
    CANDIDATE_CLEARANCE_WAYPOINT
    CANDIDATE_POST_PLANT
    CANDIDATE_RETAKE
    CANDIDATE_AIM_VARIANT
    PASSING_TRAJECTORY
    NOISE

Não acrescentar ao catálogo sem revisão humana posterior.

---

# 17. ANÁLISE DE QUALIDADE DO DOMÍNIO

A hipótese passa se o domínio intermediário apresentar evidência de:

    recorrência espacial superior ou complementar;
    clusters padrão mais concentrados;
    maior cobertura de spots comuns;
    diversidade suficiente de jogadores;
    setups reconhecíveis;
    labels temporais válidos;
    menor dependência de plays específicas de equipe;
    ausência de degradação grave de decisões táticas.

A hipótese não passa apenas porque os spots parecem familiares.

Avaliar também problemas:

    rotações ruins
    abandono de sites
    stacking aleatório
    baiting
    baixa utility
    saves incorretos
    bomb carrier isolado
    ausência de trades

---

# 18. ESTRATÉGIAS FUTURAS DE TREINO

Não treinar nesta fase.

Produzir recomendação entre:

## Estratégia A

    Intermediate-only Positioning Transformer

## Estratégia B

    Professional-only Positioning Transformer

## Estratégia C

    Mixed Transformer with domain token

## Estratégia D

    Shared encoder with domain-specific heads

## Estratégia E

    Curriculum:
    intermediate standard positioning
    depois fine-tuning profissional

Para cada estratégia, avaliar:

    vantagens
    riscos
    custo
    necessidade de dados
    compatibilidade com Utility AI
    comportamento esperado
    risco de domain averaging
    avaliação necessária

Não escolher apenas por preferência narrativa.

---

# 19. SPLITS DO NOVO DOMÍNIO

Quando houver dados suficientes, dividir por partida completa e jogadores.

Evitar leakage de:

    mesma partida
    mesma demo
    mesmo squad recorrente
    mesmos jogadores
    sequências adjacentes

Proposta inicial:

    Train 70%
    Validation 15%
    Test 15%

Criar também:

    unseen_players
    unseen_stacks
    recent_matches
    cross-domain holdout

Não materializar splits definitivos com menos de 50 demos.

---

# 20. TESTES OBRIGATÓRIOS

Adicionar no mínimo:

1. ProfessionalCorpusRemainsUnchanged
2. IntermediateCorpusUsesSeparateDirectory
3. RankSystemIsExplicit
4. FaceitLevelIsNotConvertedToValveRank
5. PremierRatingIsNotConvertedToCompetitiveRank
6. UnknownRankIsNotPromoted
7. DownloadRequiresApprovedSource
8. SignedUrlsAreNotPersisted
9. SecretsAreNotLogged
10. DemoHashIsRecorded
11. DuplicateDemoIsRejected
12. NonMirageDemoIsRejected
13. CorruptedDemoIsQuarantined
14. RoundLifecycleIsValid
15. IntermediateNpZContainsNoSyntheticHistory
16. SteamIdsArePseudonymizedInReports
17. SpotPromotionRequiresHumanReview
18. ProfessionalAndIntermediateMetricsRemainSeparate
19. BootstrapUsesMatchOrRoundUnit
20. NoTrainingStartsInThisPhase

Manter a suíte C# verde.

---

# 21. ENTREGÁVEIS

Criar:

    datasets/mirage_domains/
        domain_contract_v1.json
        professional_manifest_reference.json
        intermediate_competitive/
            acquisition_source_matrix.json
            intermediate_demo_inventory_v1.json
            intermediate_npz_manifest_v1.json
            pilot_download_manifest.json
            quarantine_manifest.json

Criar:

    tools/intermediate_demo_acquisition/
        README.md
        config.example.json
        discover_matches.py
        fetch_match_metadata.py
        validate_skill_bucket.py
        download_demo.py
        verify_archive.py
        deduplicate_demo.py
        build_manifest.py

Criar relatórios:

    training_runs/intermediate_domain_study/
        source_feasibility_report.md
        legal_and_access_constraints.md
        faceit_access_readiness.json
        valve_opt_in_feasibility.md
        pilot_corpus_quality.json
        ct_standardization_analysis.json
        tr_standardization_analysis.json
        professional_vs_intermediate.json
        spot_domain_coverage.json
        unmapped_intermediate_clusters.json
        domain_training_strategy.md
        scale_up_recommendation.md
        mathematical_audit.json
        provenance_audit.json
        adversarial_audit.json
        phase_evidence_matrix.json
        deliverable_evidence.json
        fase_2a_intermediate_final_report.md

Produzir apenas três relatórios Markdown extensos:

    source_feasibility_report.md
    domain_training_strategy.md
    fase_2a_intermediate_final_report.md

Demais artefatos devem ser JSON ou Markdown curto.

---

# 22. GATES

## Gate A: Aquisição

    fonte legítima
    rank rastreável
    demo acessível
    licença ou autorização registrada
    zero segredo persistido
    downloader reproduzível

## Gate B: Integridade

    DEM válido
    Mirage
    Source 2
    parser compatível
    NPZ válido
    lifecycle válido
    zero sintético

## Gate C: Qualidade

    diversidade suficiente
    recorrência espacial mensurável
    setups padrão detectáveis
    spots relevantes
    ausência de concentração extrema em poucos jogadores

## Gate D: Valor incremental

    cobertura adicional dos 53 spots
    ou
    novo comportamento padrão útil
    ou
    melhor generalização para matchmaking

Se aquisição oficial estiver pendente:

    INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING

Se o piloto falhar em qualidade:

    INTERMEDIATE_CORPUS_HYPOTHESIS_NOT_CONFIRMED

Se o piloto for insuficiente:

    INTERMEDIATE_CORPUS_REQUIRES_MORE_PILOT_DATA

Se todos os gates passarem:

    INTERMEDIATE_MIRAGE_CORPUS_READY_TO_SCALE

Não iniciar treinamento.

Não alterar o catálogo.

Não retomar o Marco 2B.3 automaticamente.

Executar `kill_all` ao encerrar.


## Follow-up — 2026-11-09T00:47:05Z (RESUME-AFTER-POWER-OUTAGE)

[Nota de registro: esta mensagem é uma RETOMADA após queda de energia. O corpo da fase (§0 a §22 – FASE 2A-INTERMEDIATE, pausa formal, orquestração, domínios, fontes A–D, critérios de aceitação, piloto, downloader, manifesto, extração, métricas CT/TR, comparação, 53 spots, novos spots, qualidade, estratégias de treino, splits, testes, entregáveis, gates) é IDÊNTICO ao texto já registrado verbatim acima na entrada correspondente à solicitação da FASE 2A-INTERMEDIATE, e não é duplicado aqui conforme a regra de não repetir o que a última entrada já contém. Registram-se abaixo, verbatim, as seções NOVAS desta retomada.]

# FASE 2A-INTERMEDIATE:
# ESTUDO DE VIABILIDADE E AQUISIÇÃO DO CORPUS MIRAGE INTERMEDIÁRIO

## ⚠️ ESTA É UMA RETOMADA APÓS QUEDA DE ENERGIA / RESTART DO SERVIDOR ⚠️

A execução anterior parou na **Iteração 0/32**. Nada foi produzido além de documentos de planejamento. NÃO recomece do zero cegamente: leia o estado em disco descrito na seção "ESTADO VERIFICADO EM DISCO" abaixo, confirme-o você mesmo, e continue a partir dele.

---

## ESTADO VERIFICADO EM DISCO (ground truth — reconfirme com suas próprias ferramentas)

1. `.agents/teamwork/orchestrator_2a_intermediate/` EXISTE com apenas 4 arquivos de planejamento:
   - `BRIEFING.md` (3916 B), `SCOPE.md` (3653 B), `DISPATCH.md` (3729 B), `progress.md` (1122 B).
   - `progress.md` registra: reconhecimento do projeto concluído; criação de BRIEFING/SCOPE/DISPATCH concluída; **Wave 1 NÃO despachada**; Iteration 0/32.
2. `datasets/mirage_domains/` **NÃO EXISTE**.
3. `tools/intermediate_demo_acquisition/` **NÃO EXISTE**.
4. `training_runs/intermediate_domain_study/` **NÃO EXISTE**.
5. Marcador `PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY` **NÃO foi criado**.
6. Corpus profissional **INTACTO** em `datasets/mirage_v2/` (444 demos NPZ, 3.411.434 sequências, catálogo V3 com 53 spots, `label_contract_v2.json`, 6 shards, 6 sidecars em `label_sidecar_v2/`).
7. Marco 2B.3 **INTACTO e PAUSADO** em `training_runs/positioning_v2_real_temporal/full_training/`: `selected_candidate.pt` (19.022.035 B), `marco_2b3_final_report.md` (37.475 B), `mathematical_training_audit.json`, `data_provenance_training_audit.json`, `ml_generalization_audit.json`, `adversarial_training_audit.json`, `milestone_2b3_evidence_matrix.json`, `deliverable_evidence.json`, `input_snapshot.json`, `compute_preflight.json`, `frozen_training_config.json`, `frozen_composite_formula.json`, `class_weights.json`, `baseline_comparison.json`, `temporal_gain_report.json`, `collapse_monitoring.json`, `best_model_selection.json`, `three_seed_comparison.json`, e as pastas `seed_42026/`, `seed_42027/`, `seed_42028/`. **NÃO retomar, NÃO modificar, NÃO mover esse marco.**
8. Todos os subagentes do run anterior morreram no restart. Nenhum ativo. Partida limpa.
9. Veredito vigente do Marco 2B.3: `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL` (CONDITIONAL).

---

## NOTAS OPERACIONAIS PARA ESTA RETOMADA

- Workspace: `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`.
- Skills de governança em `.agents/skills/`: `csbot-phase-gate`, `csbot-report-skeptic`, `csbot-dataset-forensics`, `csbot-graph-impact`, `csbot-math-logic-auditor`.
- Hooks em blocking mode conforme `hooks_config.json` (5 hooks).
- Regras inegociáveis em `AGENTS.md` (Regras 01 a 09). Destaques:
  * Regra 01: hash SHA-256 completo de 64 caracteres, caminhos relativos ao repo, fórmulas `(N/D)`.
  * Regra 02: Test e Final Holdout intocados.
  * Regra 03: `support = 0` é estritamente `N/A`, nunca `0.0%`.
  * Regra 04: rotular `SIMULATED` / `TEMPLATED` / `SYNTHETIC` / `INFERRED` quando aplicável.
  * Regra 06: proteger artefatos sensíveis, com hash anterior + backup + diff + rollback.
  * Regra 07/09: implementador não valida o próprio trabalho; auditores somente-leitura.
  * Regra 08: não avançar de fase automaticamente.
- NÃO criar diretórios vazios "cosméticos" apenas para constar como entregues. Todo artefato deve ter conteúdo real, tamanho > 0 e hash verificável.
- Se a pesquisa de fontes concluir que não há acesso legítimo disponível no momento, o veredito correto é `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING` — e isso é um resultado válido e completo para esta fase, não uma falha. Nesse caso, os artefatos de análise (viabilidade, contrato de domínios, downloader em dry-run, testes, estratégia de treino) devem ser integralmente produzidos mesmo sem demos reais, e a comparação estatística profissional-vs-intermediário deve ser explicitamente marcada como `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` (ou rótulo equivalente claro), nunca inventada.
- É PROIBIDO fabricar dados intermediários, telemetria, posições ou métricas para preencher relatórios. Se não há dados, declarar ausência e classificar como `N/A` / `NOT_EXECUTABLE`.
