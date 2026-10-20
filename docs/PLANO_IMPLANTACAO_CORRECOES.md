# 🛠️ Plano de Implantação Detalhado: Correção Estrutural Completa (`CsBotManager`)

**Data do Plano:** 19 de Outubro de 2026  
**Referência Base:** [RELATORIO_AUDITORIA_TECNICA.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/RELATORIO_AUDITORIA_TECNICA.md)  
**Escopo:** Resolução integral de **100% dos achados da Auditoria Forense** (`C-01A` a `C-01E`, `C-02A`, `C-02B`, `C-03`, `C-04A`, `C-04B`, `C-05A`, `C-05B`, `I-01` a `I-04E`, `O-01` e `O-02`).

---

## 1. Visão Geral da Arquitetura de Correção

O objetivo deste plano é eliminar completamente o "teatro de variáveis" (estados que existem apenas em memória C# ou na HUD), os teletransportes artificiais (`pawn.Teleport()`), as condições de corrida entre threads e as falhas econômicas, conectando o `CsBotManager` diretamente à memória nativa do `CCSBot` (Source 2) e à API compartilhada `BotControllerApi.dll` (`IBotControllerApi`).

```mermaid
flowchart TD
    subgraphBrain["Cérebro Tático (Assíncrono / Safe)"]
        LLM["OllamaIglService (Validado com SpotIds Reais + Lock)"]
        Prob["TacticalProbabilityEngine (72/23/5%)"]
        Econ["EconomyManager (Ambos os Times + Loss Bonus Real + AWP Drop)"]
    end

    subgraphMainThread["Source 2 Game Thread (64Hz Determinístico)"]
        Plan["TacticalPlan Unificado (_currentPlan + Crossfire + Locked Human Spot)"]
        Nav["BotLocomotionDriver (CCSBot.GoalPosition + RepathTimer + LookAtSpot)"]
        Api["IBotControllerApi (InjectUsercmd / StartUsercmdMovement / SetBuyPlan)"]
        Hud["TacticalHudRenderer (Cache 1Hz + Vivo até EventRoundEnd)"]
    end

    LLM -->|Server.NextFrame + Revalidação IsValid| Plan
    Prob --> Plan
    Econ --> Api
    Plan --> Nav
    Plan --> Api
    Plan --> Hud
```

---

## 2. Mapa de Rastreabilidade Total (Todos os 19 Problemas Auditados)

| ID | Severidade | Problema Auditado | Arquivo(s) Alvo | Bloco de Execução |
| :--- | :---: | :--- | :--- | :---: |
| **C-01A** | 🔴 Crítico | `StagingSpotId` nunca move os bots fisicamente após o FreezeTime | `PacingAndFallbackController.cs` | Bloco 1 |
| **C-01B** | 🔴 Crítico | `_enemyBotSpots` é Dead Code (`GetEnemyBotSpot` nunca é chamado) | `CsBotManagerPlugin.cs`, `PacingAndFallbackController.cs` | Bloco 1 |
| **C-01C** | 🔴 Crítico | Uso de `pawn.Teleport()` em vez de locomoção via NavMesh (`GoalPosition`) | `PacingAndFallbackController.cs`, `CtDefenseController.cs`, `MidRoundAdapter.cs` | Bloco 1 |
| **C-01D** | 🔴 Crítico | `EngagementStance` (`PASSIVE_HOLD`, `JIGGLE_INFO`, etc.) é apenas cosmético | `PacingAndFallbackController.cs` | Bloco 1 |
| **C-01E** | 🔴 Crítico | `ExecuteClientCommand("+duck" / "+moveright" / "+speed" / "+attack")` ignorado pelo `CCSBot` | `PacingAndFallbackController.cs`, `CtDefenseController.cs`, `MidRoundAdapter.cs` | Bloco 1 |
| **C-02A** | 🔴 Crítico | Falta de integração com `BotControllerApi.dll` e conflito de 64Hz com `BotAI`/`BotState` | `CsBotManager.csproj`, `BotLocomotionDriver.cs` (Novo) | Bloco 1 |
| **C-02B** | 🔴 Crítico | Bug no `SPLIT_FAKE`: passa `trBots` para `CtDefenseController`, teleportando TR para Jungle CT | `MidRoundAdapter.cs`, `CsBotManagerPlugin.cs` | Bloco 1 |
| **C-03** | 🔴 Crítico | `VoiceCommandBridge` usa `new TacticalPlan()` descartável e Ollama sobrescreve posição humana | `VoiceCommandBridge.cs`, `CsBotManagerPlugin.cs`, `RoleManager.cs` | Bloco 2 |
| **C-04A** | 🔴 Crítico | Acesso a `Server.MapName` e `player.Team` fora da Game Thread (`Task.Run`) | `CsBotManagerPlugin.cs` | Bloco 3 |
| **C-04B** | 🔴 Crítico | Uso de ponteiros `CCSPlayerController` capturados pré-`Task.Run` sem revalidar `IsValid` | `CsBotManagerPlugin.cs` | Bloco 3 |
| **I-02** | 🟠 Importante | Condição de corrida (Race Condition) na lista `_history` sem `lock` | `OllamaIglService.cs` | Bloco 3 |
| **C-05A** | 🔴 Crítico | Time inimigo (`enemyBots`) nunca executa compras pelo `EconomyManager` | `CsBotManagerPlugin.cs`, `EconomyManager.cs` | Bloco 4 |
| **C-05B** | 🔴 Crítico | Drop para humano não checa saldo residual, derruba AWP salva do doador e cai longe | `EconomyManager.cs` | Bloco 4 |
| **I-04A** | 🟠 Importante | Checagem frágil de armas primárias salvas em `HasSavedPrimaryWeapon` | `EconomyManager.cs` | Bloco 4 |
| **I-04B** | 🟠 Importante | Comando `drop` via console falha em bots ou derruba arma errada | `EconomyManager.cs` | Bloco 4 |
| **I-04C** | 🟠 Importante | Ausência de drop automático de AWP de um bot rico para o `BotRole.AWPer` | `EconomyManager.cs` | Bloco 4 |
| **I-04D** | 🟠 Importante | Ordem de compra invertida (`vesthelm` antes do rifle deixa bot de `$3100` sem rifle) | `EconomyManager.cs` | Bloco 4 |
| **I-04E** | 🟠 Importante | `lossBonus` fixo em `1400` e ignorado na decisão de Eco vs. Force Buy | `CsBotManagerPlugin.cs`, `EconomyManager.cs` | Bloco 4 |
| **I-01** | 🟠 Importante | Prompt do LLM sem lista de `SpotIds` do mapa e `EnsureValidBotOrders` não valida existência | `OllamaIglService.cs` | Bloco 5 |
| **I-03** | 🟠 Importante | `_hudTimer` morre após `StagingDuration + 5s`, ocultando alertas de fim de round | `CsBotManagerPlugin.cs` | Bloco 5 |
| **O-01** | 🟡 Otimização | Reconstrução de `StringBuilder` e lookups de HUD a 64Hz na Main Thread | `CsBotManagerPlugin.cs`, `TacticalHudRenderer.cs` | Bloco 5 |
| **O-02** | 🟡 Otimização | Duplicidade estrutural entre `TacticalSpotsManager.cs` e `MapProfileManager.cs` | `TacticalSpotsManager.cs`, `MapProfileManager.cs` | Bloco 5 |

---

## 3. Detalhamento Técnico de Cada Bloco e Como Ajustar

---

### BLOCO 1: Locomoção Física Nativa (`CCSBot`), Integração `BotControllerApi.dll` e Fim dos Teleportes (`C-01A` a `C-02B`)

#### 1.1. Referenciar `BotControllerApi.dll` em [`CsBotManager.csproj`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManager.csproj) (`C-02A`)
A DLL compartilhada em `H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\shared\BotControllerApi\BotControllerApi.dll` expõe a interface `BotControllerApi.IBotControllerApi`, que permite injetar bitmasks reais no `CUserCmd` do bot (`InjectUsercmd`), controlar vetores de movimento (`StartUsercmdMovement`, `UpdateUsercmdMovement`), alternar armas pelo `defIndex` (`SwitchBotWeapon`) e bloquear compras conflitantes (`SetBuyPlan`, `SetBuySkip`).

**Como ajustar no `CsBotManager.csproj`:**
```xml
<ItemGroup>
  <Reference Include="CounterStrikeSharp.API">
    <HintPath>H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\api\CounterStrikeSharp.API.dll</HintPath>
    <Private>false</Private>
  </Reference>
  <Reference Include="BotControllerApi">
    <HintPath>H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\shared\BotControllerApi\BotControllerApi.dll</HintPath>
    <Private>false</Private>
  </Reference>
</ItemGroup>
```

#### 1.2. Criar o Controlador Físico Nativo `BotLocomotionDriver.cs` (`C-01A`, `C-01C`, `C-01D`, `C-01E`, `C-02A`)
Na Source 2, a entidade `CCSBot` (`player.PlayerPawn.Value.Bot`) possui os campos nativos do pathfinder da engine:
- `bot.GoalPosition` (`Vector`): coordenada 3D alvo para o navegador NavMesh.
- `bot.RepathTimer.Timestamp`: definir como `0.0f` força o `CCSBot` a recalcular a rota NavMesh imediatamente.
- `bot.LookAtSpot` (`Vector`), `bot.LookAtSpotDuration` (`float`), `bot.LookAtSpotTimestamp` (`float`), `bot.LookAtSpotAngleTolerance` (`float`), `bot.LookAtSpotClearIfClose` (`bool`): faz o bot mirar fisicamente para o ângulo de pre-aim (`LookX, LookY, LookZ`) do spot tático.
- `bot.WaitTimer` (`Duration` / `Timestamp`), `bot.SneakTimer` (`Duration` / `Timestamp`), `bot.HurryTimer` (`Duration` / `Timestamp`), `bot.MustRunTimer` (`Duration` / `Timestamp`) e `bot.IsStopping` (`bool`): controlam se o bot segura posição imóvel no bomb, anda no Shift (`SneakTimer`) ou corre (`HurryTimer` / `MustRunTimer`).

Além disso, via `PluginCapability<IBotControllerApi> _botControllerCap = new("botcontroller:api")`:
- **Agachar (`+duck`):** `api.InjectUsercmd(slot, 1UL << 2, durationMs)` (`IN_DUCK`).
- **Andar no Shift (`+speed`):** `api.InjectUsercmd(slot, 1UL << 16, durationMs)` (`IN_SPEED`) + `bot.SneakTimer`.
- **Disparar/Lançar Granada (`+attack`):** `api.InjectUsercmd(slot, 1UL << 0, durationMs)` (`IN_ATTACK`).
- **Jiggle Peek (`+moveright` / `+moveleft`):** `api.StartUsercmdMovement(slot, 0f, ±1.0f)` alternando o sinal a cada `350ms` quando o bot chega ao raio do spot de `JIGGLE_INFO`.

**Como ajustar:**
1. Criar `src/CsBotManager/BotLocomotionDriver.cs` que mantém o estado físico de cada `bot.Slot` (coordenada alvo atual, `LookAt` alvo, `EngagementStance` ativo, flag `HoldPosition`, e IDs de `UserCmd` em execução).
2. No método `Tick()` (ou timer de alta frequência `0.25s` + `InjectUsercmd` nativo):
   - Para cada bot vivo (aliado **e** inimigo):
     - Se a distância até o `TargetSpot` for `> 85f`: atualiza `bot.GoalPosition.X/Y/Z`, zera `bot.WaitTimer.Duration = 0f`, define `bot.IsStopping = false` e força `bot.RepathTimer.Timestamp = 0f`.
     - Quando a distância for `<= 85f` (chegou ao Spot):
       - Aplica o `LookAtSpot` para o vetor `(spot.LookX, spot.LookY, spot.LookZ)` caso o bot **não** esteja com inimigo visível (`!bot.IsEnemyVisible`).
       - Executa fisicamente o `EngagementStance`:
         - `PASSIVE_HOLD` / `HoldSiteLocked`: trava `bot.WaitTimer.Duration = 3.0f; bot.WaitTimer.Timestamp = now + 3.0f; bot.IsStopping = true;` e injeta `IN_DUCK` se o spot for de pixel fechado.
         - `JIGGLE_INFO`: alterna `StartUsercmdMovement(slot, 0f, +250f)` e `-250f` em ciclos curtos de `350ms` para pegar informação sem expor o corpo inteiro.
         - `AGGRESSIVE_POKE`: permite avanço controlado com `bot.SneakTimer` ativo (`IN_SPEED`) até detectar contato.
         - `ONE_AND_DONE`: mantém `WaitTimer` até o primeiro disparo/dano e dispara transição imediata de `MoveToSpot(FallbackSpot)` via NavMesh.
3. **Remoção Total de `pawn.Teleport()`:**
   - Em [`PacingAndFallbackController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/PacingAndFallbackController.cs) (linhas 167–174 e 201–209), [`CtDefenseController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CtDefenseController.cs) (linhas 106–110, 179, 226 e 248) e [`MidRoundAdapter.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs) (linha 270): substituir **todas** as chamadas `pawn.Teleport(...)` por `_locomotion.NavigateToSpot(bot, spot, hurry: ...)`!
   - *Exceção única permitida para `Teleport()`:* o comando explícito `!respawn` no meio do round ([`RoleManager.RespawnPlayerIntoBot`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/RoleManager.cs#L315)), onde o jogador humano morto assume o corpo/posição do bot vivo.

#### 1.3. Ativar `_enemyBotSpots` na Engine (`C-01B`)
Em [`PacingAndFallbackController.OnRoundFreezeEnd`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/PacingAndFallbackController.cs#L49-L80):
- Além de iterar sobre `plan.BotOrders` (time do jogador humano), iterar sobre os `enemyBots` consultando `_roleManager.GetEnemyBotSpot(enemyBot.Slot)` e registrar a rota física no `BotLocomotionDriver` para que a equipe adversária também ocupe suas posições de crossfire/domínio de mapa via NavMesh.

#### 1.4. Lançamento Real de Granadas no Mundo 3D (`C-01E`, `C-02A`)
Nos métodos [`ExecuteSynchronizedEntryUtilities`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/PacingAndFallbackController.cs#L228-L265), [`TriggerPostKillRetreat`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs#L244-L287) e [`TriggerSupportFlash`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs#L292-L315):
- Substituir `bot.ExecuteClientCommand("use weapon_flashbang")` + `ExecuteClientCommand("+attack")` por:
  1. Orientar `bot.LookAtSpot` para o ponto de lançamento.
  2. Chamar `_botControllerApi.SwitchBotWeapon(bot.Slot, defIndex)` (`43` = Flashbang, `45` = Smoke, `44` = HE, `46`/`48` = Molotov/IncGrenade).
  3. Chamar `_botControllerApi.InjectUsercmd(bot.Slot, 1UL << 0, 150)` (`IN_ATTACK`) após `0.25s`, garantindo que a granada seja fisicamente arremessada na engine.

#### 1.5. Corrigir o Bug de `SPLIT_FAKE` Passando `trBots` para `CtDefenseController` (`C-02B`)
Em [`MidRoundAdapter.EvaluateMidRoundAdaptation`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs#L19-L90):
- **Problema atual (linha 86):**
  ```csharp
  _ctController.ReportBombPressure("Bombsite A", plan, trBots);
  ```
- **Correção:** Adicionar o parâmetro `List<CCSPlayerController> ctBots` na assinatura de `EvaluateMidRoundAdaptation` e repassar `ctBots` para `_ctController.ReportBombPressure("Bombsite A", plan, ctBots)`.

---

### BLOCO 2: Sincronização de `_currentPlan`, Posição Travada do Humano e Rádio (`C-03`)

#### 2.1. Corrigir Sobrescrita da Posição Fixa do Humano e do Crossfire pelo Retorno Assíncrono do Ollama
Em [`CsBotManagerPlugin.OnRoundStart`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L134-L185):
- **Causa Raiz:** O timer de `0.3s` aplica a posição travada do humano no `_currentPlan` provisório, mas em `~1.8s` o callback `Server.NextFrame` do `Task.Run` faz `_currentPlan = plan;`, descartando as alterações de `0.3s`!
- **Como ajustar:** Extrair um método auxiliar `ApplyHumanSpotAndCrossfireOverrides(TacticalPlan plan, CCSPlayerController? human, List<CCSPlayerController> teamBots)` e invocá-lo **dentro do `Server.NextFrame`** imediatamente após `_currentPlan = plan;` (e também no fallback síncrono):
  ```csharp
  Server.NextFrame(() =>
  {
      _currentPlan = plan;
      ApplyHumanSpotAndCrossfireOverrides(_currentPlan, humanSlot, isHumanCt);
      // ...
  });
  ```

#### 2.2. Eliminar `new TacticalPlan()` Descartável em [`VoiceCommandBridge.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/VoiceCommandBridge.cs#L190-L212)
- **Causa Raiz:** Nas linhas 190 e 210 de `VoiceCommandBridge.cs`, `TriggerCommand` instancia `new TacticalPlan()` vazio ao chamar `_roleManager.ClaimPositionForPlayer(...)` e `_roleManager.RespawnPlayerIntoBot(...)`.
- **Como ajustar:**
  1. No construtor de `VoiceCommandBridge`, receber um `Func<TacticalPlan>` (`_getCurrentPlan`) vindo do `CsBotManagerPlugin`.
  2. Em `TriggerCommand`, obter `var activePlan = _getCurrentPlan();` e passá-lo para `ClaimPositionForPlayer` e `RespawnPlayerIntoBot`.
  3. Quando `ClaimPositionForPlayer` reatribuir o `StagingSpotId` de um bot (porque o humano reivindicou a posição dele via chat ou rádio), notificar imediatamente o `BotLocomotionDriver` para atualizar o `GoalPosition` daquele bot.

---

### BLOCO 3: Thread Safety Estrito na Source 2 e Proteção de Concorrência (`C-04A`, `C-04B`, `I-02`)

#### 3.1. Eliminar Leituras Nativas (`Server.MapName`, `player.Team`) Dentro de `Task.Run` (`C-04A`)
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs):
- **Linha 169 (`OnRoundStart`):** Capturar `string currentMapName = Server.MapName;` na Game Thread antes de `Task.Run(async () => ...)` e passar `currentMapName` como string pura para `_iglService.GenerateRoundPlanAsync(...)`.
- **Linhas 469 e 496 (`OnPlayerSay` / `OnPlayerSayTeam`):** Capturar `bool isCt = player.Team == CsTeam.CounterTerrorist;` e `int playerSlot = player.Slot;` na Game Thread **antes** do `Task.Run`.

#### 3.2. Revalidar Entidades `CCSPlayerController` Dentro de `Server.NextFrame` (`C-04B`)
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L177-L227) e nas callbacks de chat (linhas 472 e 499):
- Não reutilizar referências de `CCSPlayerController` capturadas antes do `await`.
- Dentro do `Server.NextFrame`, reconstruir as listas de bots ativos com `GetTeamBots(CsTeam.CounterTerrorist)` / `GetTeamBots(CsTeam.Terrorist)` e recuperar o humano via `Utilities.GetPlayerFromSlot(humanSlot)` verificando `human != null && human.IsValid`.

#### 3.3. Sincronizar `_history` com `lock` em [`OllamaIglService.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/OllamaIglService.cs#L10-L24) (`I-02`)
- Adicionar `private readonly object _historyLock = new();`.
- Em `RecordRoundOutcome`: envolver `_history.Add(...)` e `_history.RemoveAt(0)` em `lock (_historyLock)`.
- Em `BuildPrompt`: criar um snapshot thread-safe dentro de `lock (_historyLock) { historySnapshot = _history.ToList(); }` antes de iterar no `foreach`.

---

### BLOCO 4: Fidelidade Econômica, Loss Bonus Real e Sistema de Drops (`C-05A`, `C-05B`, `I-04A` a `I-04E`)

#### 4.1. Executar Compras Determinísticas para `enemyBots` e Integrar `IBotControllerApi.SetBuyPlan` (`C-05A`)
Em [`CsBotManagerPlugin.OnRoundStart`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L230-L248):
- Atualmente o timer de `11.0s` chama `_economyManager.ExecuteDeterministicBuys(teamBots, _currentPlan, isCt)` apenas para o time do jogador humano.
- **Como ajustar:**
  1. Calcular a economia da equipe adversária (`enemyAvgMoney`, `enemyLossBonus`) e determinar sua `EconomicDirective` (`FULL_BUY`, `FORCE_BUY`, `HALF_BUY`, `ECO_SAVE`).
  2. Chamar `_economyManager.ExecuteDeterministicBuys(enemyBots, enemyPlan, !isCt)` para que ambos os times comprem com inteligência competitiva e preservem armas salvas.
  3. Em `EconomyManager.ExecuteDeterministicBuys`, registrar também `_botControllerApi?.SetBuySkip(bot.Slot)` quando a diretriz for `ECO_SAVE` ou quando o bot já tiver arma primária salva, garantindo que a IA nativa nunca gaste dinheiro por conta própria.

#### 4.2. Rastrear o Loss Bonus Real (`$1400` a `$3400`) por Equipe (`I-04E`)
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs):
- Adicionar campos `_ctLossStreak = 1` e `_trLossStreak = 1` (resetados em pistol rounds: round 0 e round 12).
- Em `OnRoundEnd`: incrementar o streak do time perdedor (máximo `5`) e decrementar em `1` o do time vencedor (mínimo `1`).
- Calcular `int GetTeamLossBonus(CsTeam team) => 1400 + (streak - 1) * 500;` (`1400, 1900, 2400, 2900, 3400`).
- Em `EconomyManager.ExecuteDeterministicBuys`: se `avgTeamMoney < 3900`, mas `avgTeamMoney + lossBonus >= 4100` (time terá Full Buy garantido no próximo round mesmo se perder, ou está com `$3400` de loss bonus), ajustar o limiar de `ECO_SAVE` vs `HALF_BUY` / `FORCE_BUY` de forma autêntica ao competitivo Tier-1.

#### 4.3. Corrigir Ordem de Compra no `FULL_BUY` (Prioridade Rifle > Capacete) (`I-04D`)
Em [`EconomyManager.BuildBuyLoadout`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs#L152-L202):
- **Causa Raiz:** `commands.Add("buy vesthelm")` estava sendo adicionado antes do rifle. Um bot TR com `$3100` gastava `$1000` no `vesthelm`, sobrava `$2100` e falhava ao comprar a `ak47` (`$2700`), jogando o round armado apenas de Glock!
- **Como ajustar:**
  1. Se `hasSavedPrimary == false`:
     - No lado TR (`money >= 2700` e `< 3700`): comprar `"buy vest"` (`$650`, sobra `$2450` se tinha `$3100` -> se tiver `>= 3350` compra `vest` + `ak47`; se tiver `2700..3349`, compra `galilar` + `vesthelm` ou `ak47` prioritária antes do colete!).
     - No lado CT (`money >= 2900` e `< 3900`): comprar `"buy vest"` (`$650`) + `"buy m4a1_silencer"` (`$2900`) se `money >= 3550`, ou `"buy famas"` (`$2050`) + `"buy vest"` (`$650`) + utilitários se `money < 3550`, comprando `vesthelm` no CT apenas quando `money >= 4500` (já que AK-47 dá HS de 1 tiro mesmo com capacete).

#### 4.4. Reforma Completa de `DropWeaponForPlayer` e Drop Automático de AWP (`C-05B`, `I-04A`, `I-04B`, `I-04C`)
Em [`EconomyManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs#L80-L150):
1. **Proteção de Saldo Residual e de Arma Salva (`C-05B`):**
   - Filtrar candidatos doadores exigindo `bot.InGameMoneyServices.Account - cost >= 2000` (para que o bot doador não fique falido no round).
   - Em vez de executar `bot.ExecuteClientCommand($"buy {weaponToDrop}")` + `"drop"` (que faz um bot com AWP salva derrubar a própria AWP no chão e deixa a arma longe do jogador humano), deduzir o custo diretamente da conta do bot doador:
     ```csharp
     donor.InGameMoneyServices!.Account -= cost;
     Utilities.SetStateChanged(donor, "CCSPlayerController", "m_pInGameMoneyServices");
     humanPlayer.GiveNamedItem($"weapon_{weaponToDrop}");
     ```
   - Isso garante **100% de confiabilidade**: o bot doador paga pela arma de verdade no placar oficial da Source 2, não perde sua própria arma primária salva, e o jogador humano recebe a arma imediatamente em mãos (`I-04B`).
2. **Drop Automático de AWP para o `AWPer` da Equipe (`I-04C`):**
   - Criar `CoordinateTeamAwpDrop(List<CCSPlayerController> teamBots, TacticalPlan plan, bool isCt)` chamado antes das compras individuais em `ExecuteDeterministicBuys`:
   - Se o bot com `BotRole.AWPer` não possui AWP salva e tem `Account < 5400`, mas existe um companheiro com `Account >= 6800`, o companheiro rico desconta `$4750` (`Account -= 4750; SetStateChanged(...)`), entrega `awpBot.GiveNamedItem("weapon_awp")` ao `AWPer`, e anuncia no chat da equipe: `"[TEAM] Comprei AWP pra você, {awpBot.PlayerName}!"`.
3. **Detecção Limpa de Arma Primária Salva (`I-04A`):**
   - Em `HasSavedPrimaryWeapon`, verificar `weapon.IsValid` e inspecionar `weapon.DesignerName` + `weapon.AttributeManager?.Item?.ItemDefinitionIndex` cobrindo todas as variantes da Source 2 (`7` = AK-47, `16` = M4A4, `60` = M4A1-S, `9` = AWP, `10` = FAMAS, `13` = Galil, `8` = AUG, `39` = SG553, `40` = SSG08).

---

### BLOCO 5: Validação Estrita de `SpotIds` no LLM, Ciclo de Vida da HUD e Otimizações 64Hz (`I-01`, `I-03`, `O-01`, `O-02`)

#### 5.1. Injetar e Validar `SpotIds` Reais do Mapa em [`OllamaIglService.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/OllamaIglService.cs) (`I-01`)
1. **Injeção no Prompt (`BuildPrompt`):**
   - Obter a lista de spots válidos para o lado atual (`CT` ou `TR`) via `_spotsManager.GetSpotsForTeam(isCt ? "CT" : "TR")`.
   - Incluir no System Prompt a lista compacta de `SpotId (Setor)` permitidos para aquele lado e usar no exemplo JSON apenas `SpotIds` daquele lado (evitando que o modelo misture `ct_a_ticket` com `tr_a_ramp_poke`).
2. **Validação Estrita em `EnsureValidBotOrders`:**
   - Verificar se `_spotsManager.GetSpotById(order.StagingSpotId)` existe **e** pertence ao time correto (`Spot.Team == expectedTeam`).
   - Caso seja nulo ou de outro time, substituir automaticamente por um `TacticalSpot` válido daquele time/setor via `_spotsManager.PickRandomSpotForSector(...)`. Fazer o mesmo para `order.ExecuteSpotId` e `order.FallbackSpotId`.

#### 5.2. Manter `_hudTimer` Ativo Durante Todo o Round (`I-03`)
Em [`CsBotManagerPlugin.OnRoundFreezeEnd`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L298-L303):
- **Remover** o bloco:
  ```csharp
  AddTimer(_currentPlan.StagingDurationSeconds + 5.0f, () => {
      _hudTimer?.Kill();
      _hudTimer = null;
  });
  ```
- O `_hudTimer` permanecerá ativo durante todo o round (sendo encerrado apenas em `OnRoundEnd` ou no início do round seguinte), permitindo que a HUD exiba em tempo real as transições para `[FASE: EXECUTE]`, `[ALERTA 1: PRESSÃO]`, `[ALERTA 2: C4 CONFIRMADA]`, `[DESESPERO <22s]`, `[SAVE TÁTICO]` e `[CLUTCH HEROICO 5%]`.

#### 5.3. Cache de Renderização da HUD a 1Hz (`O-01`)
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs) e [`TacticalHudRenderer.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/TacticalHudRenderer.cs):
- Em vez de reconstruir o `StringBuilder` e fazer múltiplos `Dictionary.TryGetValue` dentro do listener `OnTick` (64 vezes por segundo), armazenar a string HTML pronta em `private string _cachedHudHtml = string.Empty;` e o `private int _cachedHumanSlot = -1;`.
- O timer de `1.0s` (`_hudTimer`) reconstrói `_cachedHudHtml` apenas **1 vez por segundo** (ou imediatamente quando ocorre mudança de fase/alerta), e o listener `OnTick` apenas chama `human.PrintToCenterHtml(_cachedHudHtml)` com custo de CPU praticamente zero (`O(1)` sem alocação na heap).

#### 5.4. Unificar `TacticalSpotsManager.cs` e `MapProfileManager.cs` (`O-02`)
- Fazer `TacticalSpotsManager` delegar suas consultas (`GetSpotById`, `PickRandomSpotForSector`, `GetSpotsForTeam`) diretamente ao `MapProfile` ativo carregado pelo [`MapProfileManager`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MapProfileManager.cs), eliminando o carregamento duplicado de JSON em memória e centralizando todos os spots em uma única fonte da verdade.

---

## 4. Roteiro de Execução e Validação (Compiler-Driven Development)

A implantação seguirá **5 Etapas Sequenciais** com compilação e verificação rigorosa ao final:

1. **Etapa 1 (Infraestrutura Nativa & Locomoção):**
   - Atualizar [`CsBotManager.csproj`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManager.csproj) com a referência à `BotControllerApi.dll`.
   - Criar `src/CsBotManager/BotLocomotionDriver.cs` integrando `CCSBot` (`GoalPosition`, `RepathTimer`, `LookAtSpot`, `WaitTimer`, `SneakTimer`, `HurryTimer`) e `IBotControllerApi` (`InjectUsercmd`, `StartUsercmdMovement`, `SwitchBotWeapon`, `SetBuySkip`).
   - Refatorar [`PacingAndFallbackController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/PacingAndFallbackController.cs), [`CtDefenseController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CtDefenseController.cs) e [`MidRoundAdapter.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs) substituindo todos os `pawn.Teleport()` de rotação/execução/retreat pelo `BotLocomotionDriver`, ativando `_enemyBotSpots` e corrigindo o bug `trBots -> ctBots` no `SPLIT_FAKE`.
2. **Etapa 2 (Estado Tático, Rádio & Thread Safety):**
   - Corrigir [`VoiceCommandBridge.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/VoiceCommandBridge.cs) para operar sobre o `_currentPlan` real.
   - Proteger a posição travada do humano e o crossfire complementar contra sobrescrita pós-`Task.Run` em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs).
   - Isolar `Server.MapName` e `player.Team` na Game Thread, revalidar `IsValid` dentro de `Server.NextFrame` e adicionar `_historyLock` em [`OllamaIglService.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/OllamaIglService.cs).
3. **Etapa 3 (Economia Competitiva Completa):**
   - Atualizar [`EconomyManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs) e [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs) com compras para `enemyBots`, rastreamento real do Loss Bonus (`$1400`–`$3400`), prioridade Rifle > Colete, entrega direta via `GiveNamedItem` + desconto em `InGameMoneyServices.Account` no drop humano, e drop automático de AWP para o `AWPer`.
4. **Etapa 4 (Validação LLM, Ciclo de Vida da HUD & Unificação de Spots):**
   - Injetar e validar `SpotIds` por time em [`OllamaIglService.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/OllamaIglService.cs).
   - Manter `_hudTimer` ativo até `OnRoundEnd`, aplicar cache HTML de 1Hz em [`TacticalHudRenderer.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/TacticalHudRenderer.cs) e unificar [`TacticalSpotsManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/TacticalSpotsManager.cs) com [`MapProfileManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MapProfileManager.cs).
5. **Etapa 5 (Compilação, Deploy & Validação Final):**
   - Executar `dotnet build -c Release` garantindo **0 Warnings e 0 Errors**.
   - Publicar os binários atualizados em `H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager`.
