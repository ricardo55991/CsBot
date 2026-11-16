# Relatório Forense de Nós Sem Cobertura, Ciclos, APIs Legadas e Pontos de Mutação de Alto Risco (`uncovered_high_risk_nodes.md`)

- **Data de Geração**: `2026-11-07T18:12:00Z`
- **Status de Revisão**: `AGENT_REVIEWED` (`csbot-explorer`, `csbot-graph-analyst`, `csbot-adversarial-reviewer`)
- **Natureza dos Dados**: `REAL` (inspeção direta de código e grafo AST `graphify-out/graph.json`, SHA-256 `7a09693f1f6568803fa7f2ae7a0286cbe38c09f3900d08b96c6538f4eaa264f0`) + `INFERRED` (nós planejados de exportação/runtime do Positioning Transformer).
- **Isolamento Estrito**: Nenhum arquivo de código-fonte em `src/`, `tools/` ou `tests/` foi alterado.

---

## 1. Pontos de Mutação e Desconexão de Altíssimo Risco (`CRITICAL` / `HIGH`)

A auditoria cruzada entre o grafo AST (`graphify-out/graph.json`) e a leitura linha-a-linha dos 6 fluxos revelou **9 vulnerabilidades arquiteturais críticas** onde componentes validados isoladamente em testes unitários estão desconectados ou sofrem mutação/inconsistência no runtime real:

### 1.1 `[CRITICAL-01]` `JumpExecutionGate` Está Desconectado do Runtime (Dead Code em Produção)
- **Fluxo Afetado**: Fluxo 3 (`Jump: previsão → JumpExecutionGate → comando → landing`)
- **Localização**: `src/CsBotManager/JumpExecutionGate.cs` (L80-L384, SHA-256 `55e2ff88b2e13aad3739219ba6b7b2697f9da7b8e84ccc1e199ff4102637259d`)
- **Evidência**:
  - A classe `JumpExecutionGate` implementa o rastreamento por slot em `_states` (`ConcurrentDictionary<int, JumpGateState>`, L82), `UpdateGroundedState` (L148), `EvaluateJumpRequest` (L198) e `RecordJumpExecuted` (L353), sendo testada em `tests/CsBotManager.Tests/Phase17SemanticAndJumpTests.cs` (L89-L210).
  - Contudo, nenhuma classe de produção (`src/CsBotManager/CsBotManagerPlugin.cs`, `src/CsBotManager/MicroMoveEngine.cs`, `src/CsBotManager/BotLocomotionDriver.cs` ou `src/CsBotManager/MovementArbitrator.cs`) instancia ou invoca `JumpExecutionGate`.
  - No runtime real:
    1. `MicroMoveEngine.PredictBatch16Hz` (L1496, L1567-L1569) converte qualquer `act0 > 48` diretamente em `IsJump = true` e `Buttons |= 1UL << 1` via `MicroMoveStep.FromActionId` (L100-L142), sem consultar `JumpExecutionGate.EvaluateJumpRequest`.
    2. `BotLocomotionDriver.UpdateTick` (L992) publica `MovementIntent` de Stuck 2D com `Buttons = IN_JUMP | IN_FORWARD`.
    3. `SpotTestRunner.OnTick` (L362-L372) aplica impulso vertical `curVz = 260.0f` via `pawn.Teleport` (L362) e publica `btns |= BotLocomotionDriver.IN_JUMP` (L369) no `MovementArbitrator.PublishIntent` (L372).

### 1.2 `[CRITICAL-02]` `MovementArbitrator.GetActiveBombObjectiveState` Nunca É Conectado no Plugin Real
- **Fluxo Afetado**: Fluxo 4 (`C4: eventos → BombObjectiveState → materialização → movimento → plant/retake`)
- **Localização**: `src/CsBotManager/MovementArbitrator.cs` (L146, L314-L333, SHA-256 `9326c8c62a50560dd3fd3d07bf4901aa9fbe97097f5d4208bd098c2d364dcb35`) e `src/CsBotManager/CsBotManagerPlugin.cs` (L158-L279, SHA-256 `18a69c9d0127c8acec95f68298038dc0a8f705da030a5d20700fcfe9e3a327fb`)
- **Evidência**:
  - `MovementArbitrator` possui o delegate `public Func<BombObjectiveState?>? GetActiveBombObjectiveState { get; set; }` (L146), consultado em `PublishDuringCollection` (L314-L333) para rejeitar intents com `ObjectiveRevision` ou `TargetSpotAssociatedBombsite` obsoletos em relação ao `BombObjectiveState`.
  - Em `CsBotManagerPlugin.Load` (L158-L279), esse delegate nunca é atribuído (`GetActiveBombObjectiveState` permanece `null` no servidor CS2). Ele só é configurado manualmente nos testes unitários `tests/CsBotManager.Tests/V4_2_7_PrecisionTests.cs` e `tests/CsBotManager.Tests/V4_2_8_PrecisionTests.cs`.

### 1.3 `[CRITICAL-03]` Hardcoding `"A"` no Plant e Leitura de `_plugin?.CurrentPlan` (Plano do Humano) pelo Bot TR
- **Fluxo Afetado**: Fluxo 4 (`C4`)
- **Localização**: `src/CsBotManager/BotLocomotionDriver.cs` (L735, L758-L760, L1063, L1117, SHA-256 `7a5b9115cfa1239adcf8576093639e06f27f525f435e3fdac2d74da777b92d0b`)
- **Evidência**:
  - Na linha `L735`, ao iniciar o plant da C4, `BotLocomotionDriver.UpdateTick` executa `PlantController.AnnounceAndStartPlant(controller, "A", aliveTrs, aliveCts)` com a string literal `"A"` hardcoded, mesmo quando o bot está plantando no Bombsite B.
  - Nas linhas `L758`, `L1063` e `L1117`, o código decide o bombsite lendo `(_plugin?.CurrentPlan?.TacticName ?? "").Contains("B", StringComparison.OrdinalIgnoreCase)`. Como `_plugin._currentPlan` recebe `(humanTeam == CsTeam.CounterTerrorist) ? ctPlan : trPlan` em `CsBotManagerPlugin.OnRoundStart` (L560), se o humano estiver jogando de CT, os bots TR leem o nome da tática CT para escolher o bombsite da C4.

### 1.4 `[CRITICAL-04]` `BotLocomotionDriver.UpdateTick` Não Invoca `RequestRecovery` / `FindAlternativeWaypointForRecovery`
- **Fluxo Afetado**: Fluxo 5 (`Recovery: detecção → classificação → stages → resultado físico`)
- **Localização**: `src/CsBotManager/BotLocomotionDriver.cs` (L295-L337 vs L895-L1004)
- **Evidência**:
  - Os métodos `FindAlternativeWaypointForRecovery` (L295-L317) e `RequestRecovery` (L319-L337, que instancia `RecoveryAttempt` e grava em `_activeRecoveryBySlot` e `_allRecoveryAttempts`) foram criados para rastrear episódios de recovery, mas nunca são invocados dentro de `BotLocomotionDriver.UpdateTick` (L895-L1004).
  - Em vez disso, `UpdateTick` chama `EvaluateStuck2DWindow` (L910), faz a substituição inline de `state.TargetSpot` (L939-L966) e publica `MovementIntent` (`Source = MovementIntentSource.Unstuck`, `Buttons = IN_JUMP | IN_FORWARD`, L979-L1000) sem registrar `RecoveryAttempt` em `_activeRecoveryBySlot`. Além disso, `FindAlternativeWaypointForRecovery` (L304) compara `s.Side.Equals(botTeam.ToString())` (`"CounterTerrorist"` / `"Terrorist"`) contra spots cujo campo `Side` no JSON é `"CT"` / `"TR"`.

### 1.5 `[CRITICAL-05]` `EconomyManager.CurrentBuyState` Sempre Retorna o Snapshot CT e `OnRoundStart` Troca os Planos Econômicos/Táticos
- **Fluxo Afetado**: Fluxo 6 (`Economy: plano econômico → comando → inventário confirmado`)
- **Localização**: `src/CsBotManager/EconomyManager.cs` (L62-L64, SHA-256 `032f34410ea4d2f15bef8b40934956805fac378c7326c625421d81c5371cdf5c`) e `src/CsBotManager/CsBotManagerPlugin.cs` (L621-L630)
- **Evidência**:
  - `EconomyManager.CurrentBuyState` (L62-L64) é definido como `_ctSnapshot.FinalBuyState != BuyState.UNKNOWN_INCOMPLETE_BUY ? _ctSnapshot.FinalBuyState : _ctSnapshot.PurchaseIntent`, lendo exclusivamente `_ctSnapshot`.
  - Em `CsBotManagerPlugin.OnRoundStart` (L621), o timer de `11.0s` chama `_economyManager.ExecuteDeterministicBuys(teamBots, _economyManager.CurrentBuyState, humanTeam, _roleManager, _currentPlan, _locomotionDriver)`, aplicando o estado de compra CT aos bots aliados mesmo quando `humanTeam` é TR.
  - Na linha `L630`, para `enemyBots`, o plugin passa `_currentPlan` (plano do time do humano) em vez do plano correspondente ao `enemyTeam` (`_currentTrPlan` ou `_currentCtPlan`).

### 1.6 `[CRITICAL-06]` Síntese Linear de `self_history` e `teammate_features` no DataLoader do Positioning Transformer (`SYNTHETIC` / `TEMPLATED`)
- **Fluxo Afetado**: Fluxo 1 (`Positioning Transformer`)
- **Localização**: `tools/phase3a_training/data_utils.py` (`load_and_preprocess_shard`, L217-L238, SHA-256 `d15c234e3a2ce73fe01663293b60a8a53166d73e8caf40254b36eef2e4ec8e45`) e `tools/phase2_dataset/dataloaders.py` (`PositioningDatasetV1.__getitem__`, L70-L81, SHA-256 `921836c8a9c4590f91a2ed3aa8da090a4470878bb8f6e66a8dc25997d198183d`)
- **Evidência**:
  - Em `load_and_preprocess_shard` (L217-L238), o tensor `self_history` `[N, 32, 18]` não reconstrói 32 ticks históricos reais a partir dos `.npz`: ele repete a posição do tick atual adicionando um drift linear sintético `np.linspace(-0.01, 0.0, 32)`, fixa `health = 1.0`, `is_alive = 1.0` e mantém as colunas `5..17` zeradas.
  - O tensor `teammate_features` `[N, 32, 4, 18]` é sintetizado somando `(i + 1) * 0.05` à posição do próprio jogador (L234), e `candidate_spot_mask` `[N, 53]` é preenchido com `np.ones((n, 53), dtype=bool)` (L253).

### 1.7 `[HIGH-07]` Perfis de Mira `SECONDARY` e `SUPPORT_UTILITY_LINEUP` Gerados por Offset Fixo (`TEMPLATED`)
- **Fluxo Afetado**: Fluxo 1 (`Positioning Transformer`)
- **Localização**: `tools/phase2_dataset/step1_2_3_build_contracts.py` (L186-L229, SHA-256 `6aac31f8a05c0027cc6e24752b8095bed30677e7fbf26c22948eb7372cd994cc`)
- **Evidência**:
  - Enquanto os ângulos `PRIMARY_HOLD` foram reconciliados com clusters reais na Fase 2.2, os perfis `SECONDARY` (`primary_yaw +/- 45.0`) e `SUPPORT_UTILITY_LINEUP` (`pitch = -25.0`) em `aim_profiles_v1.json` permanecem gerados por fórmula geométrica determinística.

### 1.8 `[HIGH-08]` Quebra de Desempacotamento em `run_mining_and_training_loop.py`
- **Fluxo Afetado**: Fluxo 2 (`MLMove V1`)
- **Localização**: `tools/mlmove_pipeline/run_mining_and_training_loop.py` (L202, SHA-256 `e3d22c0609f12104b85c9676aa05b7ea7dc14611e10a48925e40144ca285245e`)
- **Evidência**:
  - A linha `X, Y = load_dataset_for_map(map_name)` falha em tempo de execução porque `load_dataset_for_map` (`tools/mlmove_pipeline/train_and_export_onnx.py`, L198-L207) retorna um único objeto `ShardedMemmapDataset`, e não uma tupla `(X, Y)`.

### 1.9 `[HIGH-09]` Tensor Instantâneo `[2, 10, 18]` em `MicroMoveEngine` vs Janela `[B, 32, 10, 18]` em `contract_spec.py`
- **Fluxo Afetado**: Fluxo 2 (`MLMove V1`)
- **Localização**: `src/CsBotManager/MicroMoveEngine.cs` (L291-L293, L717-L801) vs `tools/mlmove_pipeline/contract_spec.py` (L22-L26)
- **Evidência**:
  - Em `MicroMoveEngine.cs`, `_ctFogInputTensor` e `_trFogInputTensor` possuem dimensão `[10, 18]` (`_onnxBatchInputBuffer` de tamanho `2 * 10 * 18 = 360` floats, ou replicado no eixo temporal dentro de `RunOnnxBatchInference` L717-L801), enquanto `contract_spec.py` define `SEQ_LEN = 32` ticks históricos reais `[B, 32, 10, 18]`.

---

## 2. Nós Sem Cobertura de Testes Automatizados (`uncovered_nodes`)

| Fluxo | Arquivo | Método / Símbolo Sem Cobertura Direta | Linhas | Motivo / Impacto |
|---|---|---|---|---|
| **1. Positioning** | *(Ponte Futura `INFERRED`)* | `PLANNED_FUTURE_NODE`: Exportador ONNX + Sessão ONNX C# de Posicionamento | N/A | Ainda não implementado; `PositioningTransformerV1` opera apenas em PyTorch offline. |
| **1. Positioning** | `tools/phase3a_training/data_utils.py` | Ramo de `candidate_spot_mask` restritiva em `load_and_preprocess_shard` | `L253` | Shards Parquet usam `np.ones((n, 53), dtype=bool)` em 100% (`1/1`) das linhas carregadas. |
| **2. MLMove V1** | `src/CsBotManager/MicroMoveEngine.cs` | `RunOnnxBatchInference` & `EnsureModelsDirectory` / `OnModelFileDetected` | `L583-L613`, `L717-L801` | Testes xUnit C# não carregam um arquivo `.onnx` real em `InferenceSession`. |
| **2. MLMove V1** | `src/CsBotManager/MovementArbitrator.cs` | Camada nativa de `ApplyWinningIntent` (`api.StartUsercmdMovement` / `api.InjectUsercmd`) | `L640-L763` | Depende de ponteiros nativos `CCSPlayerController`/`CCSPlayerPawn` do servidor CS2. |
| **3. Jump** | `src/CsBotManager/JumpExecutionGate.cs` | Integração de `JumpExecutionGate` com `MicroMoveEngine` / `MovementArbitrator` | `L80-L384` | `JumpExecutionGate` é testado isoladamente, mas tem `0` chamadas no código de produção. |
| **4. C4** | `src/CsBotManager/BotLocomotionDriver.cs` | Bloco de Plant/Defuse/C4 em `UpdateTick` | `L719-L875` | Opera sobre `CCSPlayerController` real; ocultou o hardcoding `"A"` (L735) e leitura de `_plugin?.CurrentPlan` (L758). |
| **5. Recovery** | `src/CsBotManager/BotLocomotionDriver.cs` | Bloco de Stuck 2D em `UpdateTick` | `L895-L1004` | Testes cobrem `EvaluateStuck2DWindow` e `RequestRecovery` isoladamente, mas `UpdateTick` não invoca `RequestRecovery`. |
| **6. Economy** | `src/CsBotManager/EconomyManager.cs` & `src/CsBotManager/CsBotManagerPlugin.cs` | `ExecuteDeterministicBuys`, `InspectPlayerInventory` e timer de `11.0s` em `OnRoundStart` | `L796-L1002`, `L477-L551`, `L607-L669` | Dependem de `CCSPlayerController` nativo; ocultaram o uso de `CurrentBuyState` CT para o time TR. |

---

## 3. Ciclos Arquiteturais e Loops de Feedback (`cycles`)

- **Ciclos de Importação Estática (`Import Cycles` em `graphify-out/graph.json`)**: `0` ciclos direcionados de importação detectados.
- **Ciclos Estruturais Não-Direcionados (`nx.cycle_basis`)**: `3.065` ciclos na projeção não-direcionada do grafo completo (`2.627` nós, `5.533` arestas).
- **4 Loops Fechados de Runtime e Pipeline**:
  1. **Loop Físico 64Hz/16Hz (`MLMove V1`)**: `MicroMoveEngine.PredictBatch16Hz` (L1171) → `MicroMoveEngine.UpdateTick` (L933) → `MovementArbitrator.ApplyWinningIntent` (`api.StartUsercmdMovement` + `api.InjectUsercmd`, L592) → física Source 2 → `MicroMoveEngine.BuildStandardizedInputTensor` (L1075).
  2. **Ciclo da Máquina de Estados de Pulo (`JumpExecutionGate`)**: `IsGrounded = true` → `EvaluateJumpRequest` (L198) + `RecordJumpExecuted` (L353) → `UpdateGroundedState` (`isGrounded = false`, `ConsecutiveAirborneTicks++`, L148) → pouso (`isGrounded = true`, `LastLandingTick = currentTick`, `JumpGateEventType.JumpLanded`) → cooldown `JumpCooldownSeconds` (`3.5f` s).
  3. **Loop de Pivô e Reconciliação de Objetivo (`C4`)**: `TrMacroPivotController` (`TriggerBrickWallPivot` L317 / `CheckMidRoundExploitPick` L608) → `TacticalPlan.ApplyPivotRevision` (L546) + `BombObjectiveState.UpdateCommittedSite` (L1020) → `TacticalOrderMaterializer.MaterializeTrOrders` (L632) → `BotLocomotionDriver.NavigateToSpot` (L449).
  4. **Loop de Escalonamento de Stuck 2D (`Recovery`)**: `BotLocomotionDriver.EvaluateStuck2DWindow` (L170) → `state.StuckCount = stuckEval.NewStuckStage` (L926) → `BlacklistWaypoint` (L941) + substituição de `state.TargetSpot` (L943-L965) → `MovementArbitrator.PublishIntent` (`Source = MovementIntentSource.Unstuck`, L979).

---

## 4. APIs Legadas e Contratos Duplicados (`legacy_apis`)

1. **Dois DataLoaders de Posicionamento em Paralelo**:
   - `tools/phase2_dataset/dataloaders.py` (`PositioningDatasetV1`, L36-L110) vs `tools/phase3a_training/data_utils.py` (`InMemoryPositioningDataset`, L139-L182).
2. **Dois Contratos de Ação de Movimento (97 classes c/ Jump vs Movimento Terrestre + Jump Episódico)**:
   - `tools/mlmove_pipeline/contract_spec.py` (L43-L61, usado por `src/CsBotManager/MicroMoveEngine.cs`) vs `tools/phase2_dataset/step6_7_8_jump_and_movement.py` (L140-L225).
3. **Métodos de Recovery Desacoplados de `UpdateTick`**:
   - `BotLocomotionDriver.RequestRecovery` (`src/CsBotManager/BotLocomotionDriver.cs`, L319-L337) e `FindAlternativeWaypointForRecovery` (L295-L317) coexistem com a lógica inline de substituição de spot em `BotLocomotionDriver.UpdateTick` (L939-L966).
4. **Propriedade Monotime `EconomyManager.CurrentBuyState`**:
   - `src/CsBotManager/EconomyManager.cs` (L62-L64) retorna apenas `_ctSnapshot`, coexistindo com `GetTeamBuyState(CsTeam team)` (L74-L80).
5. **Caminho Hardcoded de Servidor em `MicroMoveEngine.cs`**:
   - `DefaultModelsDir = @"H:\CS2_AI_Server\models"` em `src/CsBotManager/MicroMoveEngine.cs` (L280).
