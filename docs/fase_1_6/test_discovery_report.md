# Fase 1.6.1 — Relatório de Descoberta e Execução da Suíte Completa de Testes (`test_discovery_report.md`)

> [!IMPORTANT]
> **Status da Suíte de Testes**: **100% Restaurada e Aprovada (`274 / 274` testes passando em `CsBot.slnx`)**
> Nenhum filtro (`--filter`) foi utilizado. Todos os 16 arquivos de teste do projeto `CsBotManager.Tests` agora compilam e executam integralmente.

---

## 1. Resumo da Execução Completa (`dotnet test CsBot.slnx`)

| Parâmetro Obrigatório | Valor Verificado |
| :--- | :--- |
| **`command`** | `dotnet test CsBot.slnx --nologo` |
| **`test assemblies`** | `C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\tests\CsBotManager.Tests\bin\Debug\net10.0\CsBotManager.Tests.dll` (`.NETCoreApp,Version=v10.0`) |
| **`discovered`** | **274** |
| **`passed`** | **274** |
| **`failed`** | **0** |
| **`skipped`** | **0** |
| **`duration`** | **~3–4 s** |

---

## 2. Causa Raiz: Por que a Execução da Fase 1.6 Encontrou Apenas 86 Testes?

Durante a auditoria forense do histórico Git e do arquivo de projeto [`tests/CsBotManager.Tests/CsBotManager.Tests.csproj`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tests/CsBotManager.Tests/CsBotManager.Tests.csproj), identificamos a causa exata pela qual a Fase 1.6 reportou apenas **86 testes** (72 anteriores + 14 novos da Fase 1.6) enquanto builds anteriores reportavam mais de 200 testes:

1. **Exclusão Silenciosa via `<Compile Remove="..." />` no Commit `5175b389`**:
   No commit `5175b38902888ae4c343c3beb248be37a352e042` (`feat(v4.2.8): Structural Spatial Audit, NavMesh Pathing & Tactical Cohesion`), 10 arquivos de teste legados foram excluídos da compilação do `.csproj` através de um bloco `<ItemGroup>` contendo tags `<Compile Remove="..." />`:
   - `BotIntelligenceEvolutionTests.cs` (24 testes)
   - `EconomyAndRoleTests.cs` (9 testes)
   - `HotfixRegressionTests.cs` (21 testes)
   - `MapProfileAndSpatialTests.cs` (13 testes)
   - `MidRoundAndCalloutTests.cs` (9 testes)
   - `MovementArbitrationAndStuckTests.cs` (15 testes)
   - `OperationalFixesV41Tests.cs` (26 testes)
   - `PacingAndFallbackTests.cs` (6 testes)
   - `Phase1To3HardeningTests.cs` (54 testes)
   - `TacticalProbabilityAndCheeseTests.cs` (10 testes)
   - **Total ocultado por `<Compile Remove>`**: **187 testes**.

2. **Aritmética Exata da Discrepância (`86` vs `273/274`)**:
   - Com os 10 arquivos removidos no `.csproj`, restavam apenas **6 arquivos ativos** na compilação da Fase 1.6:
     - `V4_2_6_CriticalFixesTests.cs` (17 testes)
     - `V4_2_7_RootCauseFixesTests.cs` (21 testes)
     - `V4_2_8_StructuralAuditTests.cs` (9 testes)
     - `V4_3_UtilityIglTests.cs` (25 testes)
     - `V4_2_9_MovementContractV2Tests.cs` (8 testes adicionados na Fase 1.6)
     - `V4_2_9_MirageV2ProfileTests.cs` (6 testes na Fase 1.6, expandidos para 7 na Fase 1.6.1)
   - Soma na Fase 1.6: `17 + 21 + 9 + 25 + 8 + 6 = 86 testes`.
   - Soma após restauração completa dos 10 arquivos excluídos: `86 + 187 = 273 testes` (`274` com o novo teste `Test04b_MirageSpecificSanityCheck_AllBombBSpotsHavePositiveY` da Fase 1.6.1).

---

## 3. Correções Aplicadas para Restaurar 100% da Suíte (274 Testes)

Para remover todas as diretivas `<Compile Remove="..." />` de [`CsBotManager.Tests.csproj`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tests/CsBotManager.Tests/CsBotManager.Tests.csproj) mantendo compatibilidade total com a arquitetura V4.2.8/V4.3, foram restaurados os membros e assinaturas de compatibilidade que haviam sido alterados no commit `5175b389`:

1. **[`tests/CsBotManager.Tests/CsBotManager.Tests.csproj`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tests/CsBotManager.Tests/CsBotManager.Tests.csproj)**:
   - Removido integralmente o `<ItemGroup>` que continha os 10 `<Compile Remove="..." />`.
2. **[`src/CsBotManager/EconomyManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs)**:
   - Restaurada a propriedade `SanitizedFrameZeroPurchasesCount` e o método puro `ShouldSanitizeBlockedRound1Weapon(int currentRound, string weaponName, out int refundAmount)`.
   - Restauradas as sobrecargas `BuildBuyLoadout(TeamBuyState, TacticalRole, CsTeam, int, bool, bool)` e `SelectTargetPrimaryWeapon(..., bool forceAwp)`.
3. **[`src/CsBotManager/Models.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/Models.cs)**:
   - Restauradas as propriedades `BombObjectiveState.LastSeenTime` e `BombObjectiveState.AssignedCarrierSlot` (sincronizadas com `ConfirmedCarrierSlot`).
4. **[`src/CsBotManager/MidRoundAdapter.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs)**:
   - Restaurado o helper estático `EvaluateLooseC4RetrievePolicy(BombObjectiveState, int, float, float, float, int, int)`.
5. **[`src/CsBotManager/BotLocomotionDriver.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs)** & **[`src/CsBotManager/MicroMoveEngine.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MicroMoveEngine.cs)**:
   - Restaurados `BeginMovementTick`, `CollectLocomotionIntents`, `LastAppliedLogicalIntentBySlot`, `EnsureLogicalActionId`, `ShouldMonitorForStuck`, `FindAlternativeWaypointForRecovery`, `RequestRecovery`, `ActiveRecoveryBySlot`, `AllRecoveryAttempts`, `C4MismatchTracker` e `ShouldSuppressOnnxJump`.

---

## 4. Inventário Completo por Arquivo de Teste (`274` Testes Descobertos e Aprovados)

| # | Arquivo de Teste | Qtd. de Testes (`[Fact]` / `[Theory]`) | Status |
| :-: | :--- | :-: | :-: |
| 1 | `BotIntelligenceEvolutionTests.cs` | 24 | PASS |
| 2 | `EconomyAndRoleTests.cs` | 9 | PASS |
| 3 | `HotfixRegressionTests.cs` | 21 | PASS |
| 4 | `MapProfileAndSpatialTests.cs` | 13 | PASS |
| 5 | `MidRoundAndCalloutTests.cs` | 9 | PASS |
| 6 | `MovementArbitrationAndStuckTests.cs` | 15 | PASS |
| 7 | `OperationalFixesV41Tests.cs` | 26 | PASS |
| 8 | `PacingAndFallbackTests.cs` | 6 | PASS |
| 9 | `Phase1To3HardeningTests.cs` | 54 | PASS |
| 10 | `TacticalProbabilityAndCheeseTests.cs` | 10 | PASS |
| 11 | `V4_2_6_CriticalFixesTests.cs` | 17 | PASS |
| 12 | `V4_2_7_RootCauseFixesTests.cs` | 21 | PASS |
| 13 | `V4_2_8_StructuralAuditTests.cs` | 9 | PASS |
| 14 | `V4_2_9_MirageV2ProfileTests.cs` | 7 | PASS |
| 15 | `V4_2_9_MovementContractV2Tests.cs` | 8 | PASS |
| 16 | `V4_3_UtilityIglTests.cs` | 25 | PASS |
| **Total** | **16 classes de teste em `CsBotManager.Tests.dll`** | **274** | **274 PASS / 0 FAIL / 0 SKIP** |
