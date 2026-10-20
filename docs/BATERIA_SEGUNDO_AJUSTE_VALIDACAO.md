# Bateria de Validação — 2º Ajuste (Revalidação Final)

Data: 2026-10-20  
Base validada: branch `main` após ajustes aplicados nesta sessão

## Resultado consolidado

- **Blocos validados:** 8
- **Concluídos corretamente:** 8
- **Parcialmente concluídos:** 0
- **Pendências abertas:** 0

## Matriz por bloco

| Bloco | Status | Evidência principal |
|---|---|---|
| Bloco 1 (passos aliados + percepção legítima) | ✅ Concluído | `TacticalCalloutSystem.CanBotPerceiveEnemy` sem atalho de distância cega + `HandleFootstep` com filtro de time + `HandleWeaponFire` integrado. |
| Bloco 2 (gate anti-dupla smoke) | ✅ Concluído | Gate `CanThrowUtilityAt` ligado ao `ThrowUtility` com bloqueio e registro de detonação. |
| Bloco 3 (save CT x defuse) | ✅ Concluído | Ordem em `OnBombPlanted` correta e branch de save no locomotion interrompe tentativa de defuse/corrida. |
| Bloco 4 (prioridade/cancelamento atômico) | ✅ Concluído | `BotOrderPriority`, cancelamento de `ActiveMovementId` e semântica de `HoldDurationRemaining` aplicados. |
| Bloco 5 (round guard/seq/lock/timers) | ✅ Concluído | `requestSeq + round guard + CTS`, locks em `MapProfileManager`, timers centrais de round para fluxos encadeados. |
| Bloco 6 (invariantes inventário/C4) | ✅ Concluído | Remoção prévia de primária, C4 única com confirmação de remoção, looting com remoção de drop + arma anterior. |
| Bloco 7 (HUD + validação defensiva) | ✅ Concluído | `HtmlEncode` no HUD e validações `IsValid` reforçadas em pontos críticos. |
| Bloco 8 (JSON/legado/rawIglJson) | ✅ Concluído | IDs órfãos corrigidos, `TacticalSpots_de_mirage.json` removido, `RawJson` propagado ao logger. |

---

## Evidências de fechamento (arquivo:linhas)

### Bloco 1
- `TacticalCalloutSystem.cs`
  - Helper central de percepção legítima: `CanBotPerceiveEnemy(...)`  
    (FOV + spotted/geometria plausível + bloqueio por smoke recente + trilha sonora recente)
  - `HandleFootstep(...)` com distinção correta aliado/inimigo
  - `HandleWeaponFire(...)` adicionado para trilha sonora de combate

### Bloco 2
- `BotLocomotionDriver.cs`
  - `ThrowUtility(...)` com gate anti-duplicação:
    - `UtilityCoordinator.CanThrowUtilityAt(...)`
    - `UtilityCoordinator.RegisterUtilityDetonation(...)`

### Bloco 3
- `CsBotManagerPlugin.cs`
  - `OnBombPlanted(...)`: `HandleBombPlanted(...)` ocorre antes de `NotifyBombState(...)`
- `BotLocomotionDriver.cs`
  - Branch CT com `_isTacticalSaveActive` interrompe fluxo de defuse/aproximação no tick (`continue`)
- `MidRoundAdapter.cs` e `UtilityAndClockCoordinator.cs`
  - sincronização de save para locomotion via `NotifySaveState(...)`

### Bloco 4
- `BotLocomotionDriver.cs`
  - enum `BotOrderPriority`
  - cancelamento atômico de `ActiveMovementId` em troca de ordem
  - consumo temporal real de `HoldDurationRemaining`
- `MobilityController.cs`
  - trava de faca com prioridade `>= High_CombatFallback`

### Bloco 5
- `CsBotManagerPlugin.cs`
  - `_iglRequestSequence`, `_roundCts`, `_activeRoundTimers`
  - guard: `capturedRound != _currentRound || requestSeq != _iglRequestSequence`
  - `ClearRoundTimers()` em `OnRoundStart`, `OnRoundEnd`, `Unload`
  - migração da análise 0.3s para `AddRoundTimer(...)`
- `OllamaIglService.cs`
  - `catch (OperationCanceledException) { throw; }` antes do fallback
- `MapProfileManager.cs`
  - locks em acessos críticos de `_spotsById` (incluindo fallback/matching/setup)
- `PacingAndFallbackController.cs`
  - staging repeat migrado para `AddRoundTimer(...)`

### Bloco 6
- `EconomyManager.cs`
  - `RemovePrimaryWeapons(...)` aplicado antes de grants de primária
  - `EnforceC4Discipline(...)` com `c4Removed` antes de `GiveNamedItem("weapon_c4")`
  - `PerformPostRoundLooting(...)` remove drop e primária antiga antes de equipar nova

### Bloco 7
- `TacticalHudRenderer.cs`
  - `System.Net.WebUtility.HtmlEncode(...)` em `LastVoiceCommand`, `TacticName`, `TacticSummary`
- `CtRetakeAndDefuseBrain.cs`, `TacticalCalloutSystem.cs`, `MobilityController.cs`
  - reforços de validação `IsValid` nos pontos mapeados

### Bloco 8
- `MapProfiles/de_dust2.json` e `MapProfiles/de_inferno.json`
  - IDs de fallback órfãos resolvidos com spots válidos
- Remoção de legado:
  - `src/CsBotManager/TacticalSpots_de_mirage.json` removido
- `OllamaIglService.cs` + `Models.cs` + `CsBotManagerPlugin.cs`
  - `RawJson` capturado e enviado a `MatchTelemetryLogger.OnRoundStart(...)`

---

## Conclusão

A implementação atual atende integralmente os 8 blocos cirúrgicos definidos no Plano de Execução Definitivo do relatório V2, sem pendências técnicas abertas nesta bateria de 2º ajuste.
