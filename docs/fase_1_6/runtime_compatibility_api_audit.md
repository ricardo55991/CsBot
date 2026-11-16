# Relatório de Auditoria: APIs de Compatibilidade em Runtime

**Data:** 04/11/2026  
**Fase:** 1.6.2 — Homologação do Perfil Mirage V2 em Gameplay Normal  
**Autor:** Antigravity Autonomous Pipeline  
**Escopo da Auditoria:** Verificação dos 18 membros restaurados ou adaptados para a suíte xUnit (274 testes) e comprovação de não interferência no pipeline moderno de produção.

---

## 1. Classificação e Regras de Segurança

Cada membro reintroduzido ou preservado para retrocompatibilidade com a suíte de testes do projeto `CsBotManager.Tests` foi auditado sob as seguintes regras estritas de isolamento:
- **Regra 1 (Delegação Limpa):** Wrappers de compatibilidade devem delegar diretamente à implementação moderna ou atuar de forma idempotente.
- **Regra 2 (Fonte Única de Estado):** Não pode existir segunda fonte de estado para economia, vida, bomba ou planos.
- **Regra 3 (Pipeline Único de Movimento):** Não pode existir segundo pipeline de controle de pawn ou geração de comandos físicos paralelos ao `MovementArbitrator`.
- **Regra 4 (Lifecycle Único de Recovery):** Não pode existir segundo ciclo de stuck além do `EvaluateStuck2DWindow` e do `RecoveryAttempt`.
- **Regra 5 (Estado Único de C4):** Não pode existir estado divergente de posse ou plant da C4.
- **Regra 6 (Imutabilidade de Parâmetros):** Sobrecargas legadas não podem substituir silenciosamente parâmetros modernos em chamadas de produção.
- **Regra 7 (Sincronização de Propriedades):** Propriedades duplicadas ou sinônimos devem permanecer estritamente sincronizadas.

Categorias de Classificação:
- `ACTIVE_RUNTIME_API`: membro consumido pelo runtime de produção e validado na arquitetura atual.
- `COMPATIBILITY_WRAPPER`: sobrecarga ou adaptador que delega para a API moderna sem duplicar lógica.
- `TEST_ONLY_COMPATIBILITY`: membro ou helper exposto exclusivamente para compatibilidade com testes unitários/regressão legados, sem invocação pelo fluxo principal de gameplay.
- `DEAD_CODE`: membro não utilizado em produção nem em testes (candidato à remoção futura).

---

## 2. Auditoria Individual dos 18 Membros Restaurados

### 2.1. `EconomyManager.SanitizedFrameZeroPurchasesCount`
- **Arquivo:** [`src/CsBotManager/EconomyManager.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs)
- **Classificação:** `TEST_ONLY_COMPATIBILITY`
- **Análise Técnica:** Utilizado historicamente em asserções de testes para auditar supressão de compras indevidas no frame zero. No pipeline moderno, a sanitização no warmup e frame zero é tratada nativamente por `CapturePreBuySnapshot(..., MatchLifecyclePhase.WARMUP)` retornando `BuyState.NOT_APPLICABLE`, sem afetar o fluxo de compra de produção.
- **Conformidade:** Isolado, zero interferência em gameplay normal.

### 2.2. `EconomyManager.ShouldSanitizeBlockedRound1Weapon`
- **Arquivo:** [`src/CsBotManager/EconomyManager.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs)
- **Classificação:** `TEST_ONLY_COMPATIBILITY`
- **Análise Técnica:** Método puro/helper estático de validação de armas bloqueadas no round 1 (pistol). No runtime de produção, a seleção de armas de pistol é governada por `SelectPistolWeapon` com base na árvore de loadout e orçamento.
- **Conformidade:** Método puro e sem efeitos colaterais.

### 2.3. `EconomyManager.BuildBuyLoadout` (Overload Legado)
- **Arquivo:** [`src/CsBotManager/EconomyManager.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs)
- **Classificação:** `COMPATIBILITY_WRAPPER`
- **Análise Técnica:** Sobrecarga que aceita assinaturas antigas sem os parâmetros de `MatchLifecyclePhase` ou snapshots modernos, mapeando os parâmetros para as chamadas canônicas `SelectPrimaryWeapon` e `DetermineTeamBuyState`.
- **Conformidade:** Não chamado no loop de compra de `CsBotManagerPlugin.OnRoundFreezeEnd`; produção usa as rotinas modernas orientadas por Utility AI.

### 2.4. `EconomyManager.SelectTargetPrimaryWeapon` (Overload Legado)
- **Arquivo:** [`src/CsBotManager/EconomyManager.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs)
- **Classificação:** `COMPATIBILITY_WRAPPER`
- **Análise Técnica:** Adaptador que delega para `SelectPrimaryWeapon` garantindo a preservação das preferências de papel tático (AWPer, Entry, Support).
- **Conformidade:** Delegação transparente sem alterar regras de compra.

### 2.5. `BombObjectiveState.LastSeenTime`
- **Arquivo:** [`src/CsBotManager/Models.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/Models.cs)
- **Classificação:** `COMPATIBILITY_WRAPPER`
- **Análise Técnica:** Propriedade reintroduzida como espelho/sinônimo de temporalidade de visualização de objetivo de C4.
- **Conformidade:** Sincronizado com o relógio do servidor (`Server.CurrentTime`). Zero drift de estado.

### 2.6. `BombObjectiveState.AssignedCarrierSlot`
- **Arquivo:** [`src/CsBotManager/Models.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/Models.cs)
- **Classificação:** `COMPATIBILITY_WRAPPER`
- **Análise Técnica:** Sinônimo de `BombCarrierSlot` / `CarrierSlot` consumido por asserções de testes legados. Em produção, `TacticalOrderMaterializer.MaterializeTrOrders` utiliza `effectiveCarrierSlot` e `plan.FakeContext.BombCarrierSlot`.
- **Conformidade:** Sincronizado; não altera a atribuição da C4.

### 2.7. `MidRoundAdapter.EvaluateLooseC4RetrievePolicy`
- **Arquivo:** [`src/CsBotManager/MidRoundAdapter.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs)
- **Classificação:** `TEST_ONLY_COMPATIBILITY`
- **Análise Técnica:** Helper estático determinístico de cálculo de distância e risco para recuperação de bomba caída. O runtime de produção avalia a posição da bomba solta no loop `BotLocomotionDriver.OnTick` através de `_bombPosition` e do planejador do NavMesh.
- **Conformidade:** Função estática pura, zero efeito colateral no runtime.

### 2.8. `BotLocomotionDriver.BeginMovementTick`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L78)
- **Classificação:** `TEST_ONLY_COMPATIBILITY`
- **Análise Técnica:** Permite a simulação de ticks controlados em testes unitários sem acoplar ao loop do motor de CS2 (`Server.TickCount`). No runtime de produção, `BotLocomotionDriver.OnTick()` executa a lógica completa de início de tick via `Arbitrator.BeginTick`.
- **Conformidade:** Não é invocado durante a partida de gameplay normal.

### 2.9. `BotLocomotionDriver.CollectLocomotionIntents`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L87)
- **Classificação:** `TEST_ONLY_COMPATIBILITY`
- **Análise Técnica:** Ponto de entrada exposto para testes unitários simularem a etapa de coleta de intenções do `Arbitrator`.
- **Conformidade:** Não utilizado em produção, onde `OnTick()` realiza a coleta e resolução em sequência unificada.

### 2.10. `BotLocomotionDriver.LastAppliedLogicalIntentBySlot`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L76)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Dicionário concorrente que armazena o `Guid` da última intenção lógica aplicada a cada slot. Utilizado tanto por testes de idempotência quanto para auditoria forense do pipeline de arbitragem.
- **Conformidade:** Estrutura de leitura/auditoria; não interfere na decisão de movimento.

### 2.11. `BotLocomotionDriver.EnsureLogicalActionId`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L264)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Método estático de apoio para garantir que ações lógicas mantêm o mesmo identificador de intenção enquanto a ação permanecer invariante, incrementando `CommandGeneration` apenas quando o tipo de ação muda.
- **Conformidade:** Garante a estabilidade e rastreabilidade temporal exigida pelo pipeline MLMove.

### 2.12. `BotLocomotionDriver.ShouldMonitorForStuck`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L278)
- **Classificação:** `TEST_ONLY_COMPATIBILITY`
- **Análise Técnica:** Predicado puro usado em testes de stuck. Em produção, `OnTick()` aplica as regras equivalentes diretamente com base em `state.IsHoldingSpot`, `state.HoldDurationRemaining` e `dist2DToTarget > 85.0f`.
- **Conformidade:** Função pura sem efeitos colaterais.

### 2.13. `BotLocomotionDriver.FindAlternativeWaypointForRecovery`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L294)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Utilizado quando um waypoint entra em blacklist por repetição de stuck 2D para selecionar um spot alternativo coerente do mesmo bombsite no `MapProfileManager`.
- **Conformidade:** Parte integrante da estratégia de unstuck e resiliência espacial.

### 2.14. `BotLocomotionDriver.RequestRecovery`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L318)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Registra e gerencia uma tentativa de recovery formal (`RecoveryAttempt`), inserindo-a em `_activeRecoveryBySlot` e `_allRecoveryAttempts`.
- **Conformidade:** Ciclo único de recovery; não cria pipelines secundários.

### 2.15. `BotLocomotionDriver.ActiveRecoveryBySlot`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L93)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Coleção concorrente de recoveries ativos por slot.
- **Conformidade:** Limpa automaticamente a cada início e fim de round (`ResetRound`).

### 2.16. `BotLocomotionDriver.AllRecoveryAttempts`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L95)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Coleção agregadora lida por [`TrackerMetricsAggregator.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/TrackerMetricsAggregator.cs) para consolidar a telemetria pós-round.
- **Conformidade:** Read-only para telemetria forense.

### 2.17. `BotLocomotionDriver.C4MismatchTracker`
- **Arquivo:** [`src/CsBotManager/BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs#L91)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Instância de [`C4MismatchEpisodeTracker`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/C4MismatchEpisodeTracker.cs) que monitora episódios de divergência semântica de plant.
- **Conformidade:** Telemetria e contenção preventiva; não altera navegação física dos bots diretamente.

### 2.18. `TrackerMetricsAggregator.ShouldSuppressOnnxJump`
- **Arquivo:** [`src/CsBotManager/TrackerMetricsAggregator.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/TrackerMetricsAggregator.cs)
- **Classificação:** `ACTIVE_RUNTIME_API`
- **Análise Técnica:** Rastreamento e contagem de eventos de supressão de saltos espúrios do ONNX (`JumpSuppressedAirborneCount`, `JumpSuppressedCooldownCount`, `JumpSuppressedContextCount`) através do `JumpExecutionGate`.
- **Conformidade:** Proteção ativa que impede bunny hops indesejados.

---

## 3. Conclusão da Auditoria

Todas as 18 APIs auditadas respeitam estritamente as regras de isolamento:
1. **Zero segunda fonte de estado.**
2. **Zero pipeline de movimento paralelo.**
3. **Zero lifecycle de recovery concorrente.**
4. **Zero divergência de C4.**
5. **100% dos testes da suíte (274/274) compilam e passam.**
6. **O fluxo de produção moderno permanece íntegro e desacoplado de código de teste legado.**
