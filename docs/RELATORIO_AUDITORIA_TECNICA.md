# Relatório de Auditoria Forense Técnica: Arquitetura, Engine Source 2 e Performance (`CsBotManager`)

**Data da Auditoria:** 19 de Outubro de 2026  
**Escopo:** Auditoria linha por linha de todos os módulos em `src/CsBotManager/` e integrações binárias em `H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\`.  
**Perfil de Análise:** Engenharia Sênior de Sistemas de Jogos (Source 2 / CounterStrikeSharp .NET 10 / Concorrência 64Hz / Integração LLM Local).

---

## Sumário Executivo (Veredito Forense)

A inspeção implacável do código-fonte atual revela uma **discrepância severa entre a camada de orquestração em C# (estados, timers, sorteios e mensagens de chat) e a camada de execução motora real na engine Source 2 (`CCSPlayerPawn` / `CCSBot`)**.

Embora a modelagem de dados, os cálculos de probabilidade (`TacticalProbabilityEngine`), a estrutura de arquivos JSON (`MapProfiles`) e os avisos visuais no chat/HUD estejam bem estruturados, **grande parte do controle físico dos bots hoje opera de forma simulada (*Mock / State-Only*) ou utiliza atalhos artificiais (`Teleport` seco e `ExecuteClientCommand` ineficazes para bots)**, além de sofrer interferência direta do plugin `BotAI` (`CS2-Bot-Improver`) que continua ativo e sobrescrevendo as decisões tick a tick.

Abaixo encontra-se o diagnóstico forense detalhado dos **7 Critérios de Auditoria**, com provas extraídas diretamente do código-fonte atual.

---

## 1. Controle Real da Engine vs. "Código Simulado (Mock)"

### 1.1. Movimentação para `StagingSpotId`, `ExecuteSpotId` e `FallbackSpotId`

#### 🔴 ACHADO CRÍTICO 1A: `StagingSpotId` é 100% Simulado (Zero Efeito Motor no Jogo)
Durante a fase de preparação (`RoundPhase.Staging`), **nenhum método do plugin move ou guia os bots até as coordenadas `(X, Y, Z)` do `StagingSpotId`**.

Em [`PacingAndFallbackController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/PacingAndFallbackController.cs#L49-L80), o método `OnRoundFreezeEnd` apenas altera variáveis internas em C#, imprime texto no chat e inicia um cronômetro regressivo:

```csharp
// PacingAndFallbackController.cs (Linhas 49-80)
_currentPlan.CurrentPhase = RoundPhase.Staging;
_isExecuting = false;
_stagingTimeRemaining = plan.StagingDurationSeconds;
// ... (Apenas altera order.IsWatchingFlank = true e imprime no chat)
Server.PrintToChatAll($" {ChatColors.Green}[CsBot Maestro]{ChatColors.Default} Fase de Staging Iniciada ({_stagingTimeRemaining:F0}s). Aguardando confirmações e utilitárias!");

_stagingTimer = _plugin.AddTimer(1.0f, () =>
{
    _stagingTimeRemaining -= 1.0f;
    if (_stagingTimeRemaining <= 0)
    {
        TriggerExecute("Tempo de Staging concluído", teamBots);
    }
}, TimerFlags.REPEAT);
```

* **Consequência Prática:** Todas as atribuições de `StagingSpotId` feitas pelo `OllamaIglService`, pelo Crossfire CT (`ct_b_van_peek`, `ct_b_short_corner` em [`CtDefenseController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CtDefenseController.cs#L75-L105)), pelo Dynamic Swap ([`RoleManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/RoleManager.cs#L106)) e pelo comando `!respawn` ([`RoleManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/RoleManager.cs#L151-L175)) **existem apenas como texto no `TacticalHudRenderer.cs`**. O boneco (`CCSPlayerPawn`) dentro do servidor jamais recebe ordem de caminhar até lá.

#### 🔴 ACHADO CRÍTICO 1B: Setup do Time Adversário (`_enemyBotSpots`) é Código 100% Morto (*Dead Code*)
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L129-L130), o plugin sorteia 20+ variações de micro-posições para o time inimigo e salva no `RoleManager`:

```csharp
// CsBotManagerPlugin.cs (Linhas 129-130)
var enemySetup = _mapProfileManager.GenerateEnemyTeamSetup(enemyBots, enemyTeam);
_roleManager.SetEnemyBotSpots(enemySetup);
```

Porém, ao inspecionar [`RoleManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/RoleManager.cs#L53-L65), o método `GetEnemyBotSpot(int botSlot)` **não é chamado em absolutamente nenhum lugar de toda a solução C#**. Os spots sorteados para os bots inimigos ficam guardados em um dicionário privado na memória RAM e nunca são aplicados aos bots no servidor.

#### 🔴 ACHADO CRÍTICO 1C: Uso de `pawn.Teleport()` em vez de Navegação NavMesh no `ExecuteSpotId` e `FallbackSpotId`
Quando o código realmente altera a posição espacial de um bot (em `ApplyExecuteOrders`, `HandlePlayerHurt`, `CtDefenseController` e `MidRoundAdapter`), ele **não** utiliza pathfinding no NavMesh; ele invoca teletransporte instantâneo (`CCSPlayerPawn.Teleport`):

```csharp
// PacingAndFallbackController.cs (Linhas 201-209)
var execSpot = _mapProfileManager.GetSpotById(order.ExecuteSpotId);
if (execSpot != null && bot.PlayerPawn.Value != null)
{
    var pawn = bot.PlayerPawn.Value;
    pawn.Teleport(
        new Vector(execSpot.X, execSpot.Y, execSpot.Z),
        new QAngle(execSpot.Pitch, execSpot.Yaw, 0),
        new Vector(0, 0, 0));
}
```

* **Consequência Prática:** Quando os 18 segundos de Staging terminam (ou quando o jogador digita `!go`), os 4 bots aliados **desaparecem instantaneamente de onde estão e se materializam dentro do Bombsite (`tr_exec_a_site_default`)**, atravessando paredes e ignorando completamente o deslocamento físico pelo mapa. O mesmo ocorre quando um bot leva tiro (`HandlePlayerHurt` nas linhas 167-174): ele "pisca" e desaparece da frente do inimigo, teletransportando-se para o `FallbackSpotId`.

### 1.2. Posturas (`EngagementStance`) e Micro-Ações (`MidRoundAction`)

#### 🔴 ACHADO CRÍTICO 1D: `EngagementStance` é puramente Cosmético (Sem Loop de 64Hz)
Os estados `PASSIVE_HOLD`, `JIGGLE_INFO`, `ONE_AND_DONE` e `AGGRESSIVE_POKE` definidos no enum `EngagementStance` ([`Models.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/Models.cs#L30-L36)) **não possuem nenhuma implementação motora contínua**. Eles são lidos exclusivamente em:
1. [`TacticalHudRenderer.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/TacticalHudRenderer.cs#L129-L136): apenas para exibir o rótulo `(Passivo)`, `(Jiggle)`, `(One&Done)` ou `(Poke)` no HUD HTML.
2. [`PacingAndFallbackController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/PacingAndFallbackController.cs#L144): apenas um booleano `bool isOneAndDone = order.Stance == EngagementStance.ONE_AND_DONE` para decidir se teletransporta o bot quando ele sofre dano.

#### 🔴 ACHADO CRÍTICO 1E: Comandos `+duck`, `+moveright`, `+speed`, `+forward` e `+attack` via `ExecuteClientCommand` não controlam `CCSBot` na Source 2
Em [`MidRoundAdapter.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs#L102-L142) e [`PacingAndFallbackController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/PacingAndFallbackController.cs#L103), as micro-ações foram escritas usando comandos de console de cliente:

```csharp
// MidRoundAdapter.cs (Linhas 108-140)
case MidRoundAction.HIDE_COVER:
    bot.ExecuteClientCommand("+duck");
    _plugin.AddTimer(4.0f, () => { if (bot.IsValid) bot.ExecuteClientCommand("-duck"); });
    break;

case MidRoundAction.JIGGLE_PEEK:
    bot.ExecuteClientCommand("+moveright");
    // ...
case MidRoundAction.ROTATE_SILENT:
    bot.ExecuteClientCommand("+speed");
    break;
```

* **Por que falha na Engine Source 2:** Na arquitetura da Source 2 (`server.dll`), comandos de ação iniciados por `+` (`+duck`, `+forward`, `+moveright`, `+speed`, `+attack`) são processados pelo `CInput` do **cliente humano** para compor o bitmask `CUserCmd::buttons` enviado ao servidor a cada tick. Para uma entidade `CCSBot` (que roda no servidor sem `CInput` de cliente), o `CCSBot::Update()` reconstrói e sobrescreve o bitmask `IN_Buttons` do bot a cada tick (64 vezes por segundo). Logo, chamar `bot.ExecuteClientCommand("+duck")` ou `+attack; -attack` não mantém o botão pressionado no `UserCmd` do bot e não dispara granadas nem agacha o boneco de forma confiável.

---

## 2. Conflito ou Integração com os Plugins do `CS2-Bot-Improver`

A auditoria do diretório `H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\` confirma os seguintes binários carregados simultaneamente:
* `plugins/BotAI/BotAI.dll`
* `plugins/BotAimImprover/BotAimImprover.dll`
* `plugins/BotControllerImpl/BotControllerImpl.dll`
* `plugins/BotState/BotState.dll`
* `plugins/NadeSystem/NadeSystem.dll`
* `shared/BotControllerApi/BotControllerApi.dll`

### 🔴 ACHADO CRÍTICO 2A: Guerra de Controle com `BotAI` e Falta de Referência ao `BotControllerApi.dll`
1. **Inexistência de Integração:** O arquivo [`CsBotManager.csproj`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManager.csproj#L12-L17) referencia **apenas** `CounterStrikeSharp.API.dll`. Ele **não referencia `BotControllerApi.dll`** nem consome a interface `IBotController` do `CS2-Bot-Improver`.
2. **Sobrescrita a 64Hz pelo `BotAI`:** O plugin `BotAI` do `CS2-Bot-Improver` (junto à IA nativa `CCSBot`) opera em loop contínuo controlando a navegação dos bots. Quando o `CsBotManager` decreta que o Âncora do B está travado (`order.HoldSiteLocked = true` em [`CtDefenseController.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CtDefenseController.cs#L214)) ou em modo `SAVE TÁTICO`, **`HoldSiteLocked` é apenas um `bool` dentro de uma classe C# do nosso plugin**. O `BotAI` não faz ideia de que esse booleano existe e continua movendo o bot livremente pelo mapa ou mandando-o rotacionar/rushar no tick seguinte!
3. **Isolamento do `NadeSystem`:** O `NadeSystem` (que detém as 3.703 lineups de granadas) roda 100% isolado. O `CsBotManager` nunca invoca a API do `NadeSystem` para pedir que um bot execute uma lineup real (ex: Smoke Janela ou Smoke CT na Mirage).

### 🔴 ACHADO CRÍTICO 2B: Bug de Fogo Amigo Lógico no `SPLIT_FAKE` (Teletransportando Bot TR para Defesa CT!)
Em [`MidRoundAdapter.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MidRoundAdapter.cs#L86), durante a execução da tática Terrorista `SPLIT_FAKE`, o código notifica pressão no Bomb A passando a lista **`trBots` (bots Terroristas)** para um método que espera **`ctBots` (bots Counter-Terrorists)**:

```csharp
// MidRoundAdapter.cs (Linha 86) - Passando trBots no lugar de ctBots!
_ctController.ReportBombPressure("Bombsite A", plan, trBots);
```

Dentro de [`CtDefenseController.ReportBombPressure`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CtDefenseController.cs#L219-L230), o método busca o `BotRole.Rotator` dentro da lista recebida (`trBots`) e o **teletransporta para `ct_a_jungle_support` (dentro da Jungle dos CTs)**! Ou seja: o próprio bot Terrorista é teletransportado para a posição de defesa CT no meio da rodada!

---

## 3. Segurança de Threads na Source 2 (`Server.NextFrame` / Crash Risk)

Tocar em ponteiros nativos da Source 2 fora da Game Thread causa `Access Violation (0xC0000005)` imediato no `cs2.exe`. A auditoria encontrou **3 violações graves de Thread Safety e Ciclo de Vida de Entidades**:

### 🔴 ACHADO CRÍTICO 3A: Leitura de `Server.MapName` e `player.Team` Fora da Main Thread (Dentro de `Task.Run`)
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs), em três pontos distintos (`OnRoundStart` na linha 169, `CommandTatica` na linha 469 e `CommandRejeitar` na linha 496), propriedades nativas da engine (`Server.MapName` e `player.Team`) são avaliadas **dentro da Worker Thread do `Task.Run`**:

```csharp
// CsBotManagerPlugin.cs (Linhas 466-475) - Executando em Background Thread!
Task.Run(async () =>
{
    var newPlan = await _iglService.GetTacticalDecisionAsync(
        Server.MapName, // <-- P/Invoke para gpGlobals fora da Game Thread!
        player.Team,    // <-- Leitura de CBaseEntity->m_iTeamNum fora da Game Thread!
        _economyManager.CurrentBuyState,
        _currentRound,
        _economyManager.TeamAverageMoney,
        call,
        false);
```

### 🔴 ACHADO CRÍTICO 3B: Captura de Ponteiros `CCSPlayerController` em Closures Assíncronas Sem Revalidação
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L114-L186):
1. As listas `ctBots`, `trBots` e a referência `human` são criadas aos `0.3s` do round (antes do `Task.Run`).
2. A chamada HTTP ao Ollama pode demorar de `1.5s` a `4.5s`.
3. Quando o `Server.NextFrame` roda segundos depois ([linhas 184-185](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L184-L185)), ele passa as listas `ctBots` e `trBots` capturadas no passado sem verificar se as entidades ainda são válidas (`IsValid`).
4. Nas [linhas 481 e 508](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L481), `player.PrintToChat(...)` é chamado dentro do `Server.NextFrame` pós-await sem checar `if (!player.IsValid) return;`.

### 🟠 ACHADO IMPORTANTE 3C: *Data Race* na Lista `_history` em `OllamaIglService.cs`
Em [`OllamaIglService.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/OllamaIglService.cs#L10), `private readonly List<RoundHistoryItem> _history = new();` é modificada na Game Thread (`RecordRoundResult` nas linhas 23-36) e lida simultaneamente sem `lock` na Worker Thread (`_history.LastOrDefault()` na linha 48 e `_history.Select(...)` na linha 54).

---

## 4. Fidelidade do `EconomyManager.cs` (Compras e Drops Reais)

A inspeção de [`EconomyManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs) revelou **5 falhas graves na lógica financeira e de inventário**:

### 🔴 ACHADO CRÍTICO 4A: Bots Inimigos (`enemyBots`) Nunca Executam Compras Determinísticas
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L239-L240), o timer de compra aos `11.0s` filtra apenas `teamBots` (os 4 bots do time do jogador humano):

```csharp
// CsBotManagerPlugin.cs (Linhas 239-240)
var teamBots = players.Where(p => p.Team == humanTeam && p.IsBot).ToList();
_economyManager.ExecuteDeterministicBuys(teamBots, _economyManager.CurrentBuyState, humanTeam, _roleManager, _currentPlan);
```

Como o plugin `BotBuy` original foi desativado na Fase 2 para dar autoridade exclusiva ao `CsBotManager`, **os 5 bots adversários (`enemyTeam`) nunca passam pelo `EconomyManager`**!

### 🔴 ACHADO CRÍTICO 4B: `DropWeaponForPlayer` Desarma o Bot Doador ou Joga Fora a Arma Dele
Em [`EconomyManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs#L93-L105):

```csharp
// EconomyManager.cs (Linhas 93-105)
var richestBot = teamBots
    .OrderByDescending(b => b.InGameMoneyServices?.Account ?? 0)
    .FirstOrDefault();

if (richestBot == null || (richestBot.InGameMoneyServices?.Account ?? 0) < cost)
    return false;

richestBot.ExecuteClientCommand($"buy {weaponToBuy}");
richestBot.ExecuteClientCommand("drop");
```

1. **Suicídio Econômico do Bot Doador:** Se o jogador pedir `!drop ak` (`cost = $2700`) aos `5.0s` do Freeze Time e o `richestBot` tiver `$3100`, a condição `3100 < 2700` passa. O bot gasta `$2700` para dropar a AK para o humano e **sobra com apenas `$400` para si mesmo**, ficando sem rifle e sem colete aos `11.0s`! O bot só deveria doar se sobrasse saldo para o próprio equipamento (`Account >= cost + 3700`).
2. **Descarte Acidental de Arma Sobrevivente:** Se o `richestBot` sobreviveu ao round anterior segurando uma **AWP (`$4750`)** e tem `$4000` no banco, ao executar `buy ak47`, a engine do CS2 faz o bot **jogar sua AWP no chão para segurar a AK-47 recém-comprada**, e na linha seguinte (`drop`) ele **joga a AK-47 no chão também**, terminando de pistola!
3. **Drop Longe do Jogador:** O comando `drop` joga a arma no pé do bot no spawn dele, sem entregá-la diretamente ao jogador humano (`GiveNamedItem`) ou mirar nele.

### 🟠 ACHADO IMPORTANTE 4C: Falta de Drop Automático de AWP para o `BotRole.AWPer`
Embora previsto na especificação da Fase 2 (*"bot de maior saldo compra e solta AWP no pé do sniper"*), **não existe nenhuma implementação dessa funcionalidade em `EconomyManager.cs`**.

### 🟠 ACHADO IMPORTANTE 4D: Compra Cega no `FULL_BUY` Deixa Bots com Pouco Saldo Sem Rifle
Em [`EconomyManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs#L126-L158), como `FULL_BUY` é decidido pela **média do time** (`>= $4100`), se um bot individual tiver `$3200`, ele executa `buy vesthelm` (`-$1000`, sobra `$2200`), falha ao tentar `buy ak47` (`$2700`), e em seguida gasta `$900` em granadas (`smoke + flash + molotov`). Ele vai para o round de Full Buy **sem arma primária (apenas de Glock/USP)** em vez de comprar uma Galil/Famas (`$1800`/`$2050`) ou colete 1 + AK-47!

### 🟠 ACHADO IMPORTANTE 4E: Parâmetro `lossBonus` Hardcoded em `1400`
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L132), a chamada `_economyManager.AnalyzeTeamEconomy(teamMembers, _currentRound, 1400, humanTeam)` passa `1400` fixo em todos os rounds, e o parâmetro `lossBonus` sequer é utilizado dentro de `AnalyzeTeamEconomy` ([`EconomyManager.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/EconomyManager.cs#L12)).

---

## 5. Performance de 64 Ticks e Zero-Allocation (`OnTick` / HUD / Loops)

### 5.1. Custo por Tick e Alocações de Memória (GC Pressure)
* **Listeners `OnTick`:** Atualmente `0` listeners registrados (custo em ticks ociosos = `0.00 ms`).
* **Timers Repetitivos (`_hudTimer` a `2.5 Hz` / `0.4s` e `_clockTimer` a `2.0 Hz` / `0.5s`):**
  * Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L558-L563), `GetActivePlayers()` chama `Utilities.GetPlayers().Where(...).ToList()`, alocando duas listas e um enumerador LINQ a cada chamada (`4.5 vezes por segundo`).
  * Em [`UtilityAndClockCoordinator.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/UtilityAndClockCoordinator.cs#L84), `OrderBy(b => (b.PlayerPawn.Value!.AbsOrigin! - new Vector(cp.X, cp.Y, cp.Z)).Length())` aloca objetos `Vector` gerenciados e closures de ordenação.
  * Custo estimado nos frames onde os timers disparam: **`~0.18 ms a 0.35 ms`** (seguro para o budget de `15.6 ms` de 64Hz, mas pode ser reduzido a `< 0.03 ms` com listas pré-alocadas e `StringBuilder`).

### 🟠 ACHADO IMPORTANTE 5A: O `_hudTimer` é Morto Antes do Late-Round (Badges de `<22s` e `SAVE` Nunca Aparecem!)
Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L298-L303):

```csharp
// CsBotManagerPlugin.cs (Linhas 298-303)
float hudTotalDuration = _currentPlan.StagingDurationSeconds + 5.0f;
AddTimer(hudTotalDuration, () =>
{
    _hudTimer?.Kill();
    _hudTimer = null;
});
```

* **Consequência Prática:** Como `StagingDurationSeconds` dura de `12s` a `22s`, o `_hudTimer` é destruído aos **~25 segundos de round** (quando ainda restam ~1m30s no relógio). Portanto, quando o round entra em *Late-Round Silence* (`<= 65s`), *Desespero de Relógio* (`< 22s`), *Save Tático* ou *Retake Pós-Plant*, **o HUD já está morto** e nenhuma das badges (`[SAVE TÁTICO]`, `[CLUTCH HEROICO 5%]`, `[DESESPERO <22s]`, `[ALERTA 2: C4 CONFIRMADA]`) em [`TacticalHudRenderer.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/TacticalHudRenderer.cs#L63-L90) é renderizada para o jogador!

---

## 6. Qualidade da Engenharia de Prompt e Robustez do `OllamaIglService.cs`

### 🔴 ACHADO CRÍTICO 6A: O System Prompt Não Informa os `SpotIds` do Mapa Atual e Mistura CT com TR
Em [`OllamaIglService.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/OllamaIglService.cs#L61-L118):
1. O prompt enviado ao `qwen2.5:3b` **não injeta a lista de `SpotIds` existentes no `MapProfileManager.CurrentProfile`**.
2. Pior: o JSON de exemplo no prompt mistura spots de **CT** (`ct_mid_window_deep_awp`, `ct_mid_connector_headshot`, `ct_b_bench_deep`) com spot de **TR** (`tr_staging_palace_room`, `tr_exec_a_site_default`) dentro do mesmo time!
3. Se o servidor estiver rodando `de_dust2` ou `de_inferno`, o prompt continua mostrando apenas os IDs hardcoded de `de_mirage` no exemplo, fazendo o `qwen2.5:3b` responder com spots de Mirage dentro da Dust2/Inferno ou alucinar nomes inexistentes!

### 🔴 ACHADO CRÍTICO 6B: `EnsureValidBotOrders` Não Valida se o `SpotId` Existe no Mapa!
Em [`OllamaIglService.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/OllamaIglService.cs#L180-L189):

```csharp
// OllamaIglService.cs (Linhas 180-189)
var order = plan.BotOrders[key];
if (string.IsNullOrEmpty(order.StagingSpotId))
{
    var def = GetDefaultOrderForRoleKey(key, isCt);
    order.StagingSpotId = def.StagingSpotId;
    // ...
}
```

* **Consequência Prática:** Se o `qwen2.5:3b` alucinar `"staging_spot_id": "mid_window_1"` (ou retornar `"ct_mid_window_deep_awp"` quando o time é Terrorista, ou quando o mapa é `de_dust2`), `string.IsNullOrEmpty` retorna `false`! O `SpotId` inválido não é corrigido pelo fallback semântico (`MapProfileManager.GetMatchingSpotForOrder`), resultando em `GetSpotById(...) == null` durante toda a rodada.

### 🔴 ACHADO CRÍTICO 6C: Bugs de Sobrescrita e Descarte de Plano em `VoiceCommandBridge` e `OnRoundStart`
1. **Comandos de Voz de Posição e Respawn Descartam o Plano (`new TacticalPlan()`):**
   Em [`VoiceCommandBridge.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/VoiceCommandBridge.cs#L190-L210):
   ```csharp
   // VoiceCommandBridge.cs (Linha 190 e Linha 210)
   _roleManager.AssignPositionsBySpawn(teamBots, new TacticalPlan(), _mapProfileManager);
   // ...
   _roleManager.ClaimPositionForPlayer(human, key, teamBots, new TacticalPlan(), _mapProfileManager);
   ```
   Como é passado um `new TacticalPlan()` vazio e descartável (em vez do `_currentPlan` ativo da partida), **falar *"vamos jogar respawn"* ou *"estou meio"* no microfone tem efeito ZERO nas ordens dos bots**!
2. **Task do Ollama Sobrescreve a Posição Fixa do Humano no `OnRoundStart`:**
   Em [`CsBotManagerPlugin.cs`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/CsBotManagerPlugin.cs#L135-L189), `ClaimPositionForPlayer` da posição fixa roda aos `0.3s` (linha 137), mas quando a Task assíncrona do Ollama retorna aos `~1.8s` (linha 179), ela faz `_currentPlan = plan;`, **apagando a troca de posição que havia sido aplicada aos `0.3s`**!

---

## 7. Plano de Correção e Otimização (Priorizado por Severidade)

| Severidade | ID | Módulo / Arquivo | Problema Detectado na Auditoria | Solução de Engenharia Definitiva |
| :--- | :--- | :--- | :--- | :--- |
| 🔴 **Crítico** | **C-01** | `CsBotManager.csproj` / `PacingAndFallbackController.cs` | `StagingSpotId` e `_enemyBotSpots` são 100% simulados (Mock); `ExecuteSpotId` usa `Teleport()` seco; `BotAI` sobrescreve ordens no tick seguinte; `+duck`/`+attack` via `ExecuteClientCommand` ignorados por `CCSBot`. | Referenciar `BotControllerApi.dll` ou implementar controlador motor em `OnTick` / `OnPlayerRunCmd` manipulando `CCSBot` e `UserCmd` reais (navegação ao `StagingSpotId`, trava real de `HoldSiteLocked`, agachamento e jiggle peek físicos). |
| 🔴 **Crítico** | **C-02** | `MidRoundAdapter.cs` (Linha 86) | No `SPLIT_FAKE`, `_ctController.ReportBombPressure("Bombsite A", plan, trBots)` passa a lista `trBots` em vez de `ctBots`, teletransportando um bot Terrorista para a defesa CT na Jungle. | Passar a lista real de `ctBots` para `ReportBombPressure` e manter os `trBots` no fluxo de ataque/recuo do Fake. |
| 🔴 **Crítico** | **C-03** | `VoiceCommandBridge.cs` (Linhas 190, 210) & `CsBotManagerPlugin.cs` (Linha 179) | `VoiceCommandBridge` passa `new TacticalPlan()` vazio e descartável para `AssignPositionsBySpawn` e `ClaimPositionForPlayer`. `OnRoundStart` sobrescreve o lock de posição quando o Ollama retorna. | Expor referência ao `_currentPlan` ativo no `VoiceCommandBridge` e reaplicar `ClaimPositionForPlayer` dentro do `Server.NextFrame` após o retorno do `_iglService.GetTacticalDecisionAsync`. |
| 🔴 **Crítico** | **C-04** | `CsBotManagerPlugin.cs` (Linhas 169, 469, 496) | `Server.MapName` e `player.Team` lidos dentro de `Task.Run` (Worker Thread), e entidades `ctBots`/`trBots`/`player` usadas após `await` sem revalidar `IsValid`. | Capturar `string mapName = Server.MapName;` e `CsTeam team = player.Team;` **antes** do `Task.Run` (na Game Thread) e revalidar todas as entidades (`IsValid`) dentro do `Server.NextFrame`. |
| 🔴 **Crítico** | **C-05** | `EconomyManager.cs` (Linhas 93-105, 111) & `CsBotManagerPlugin.cs` (Linha 240) | 1) `enemyBots` nunca executam compras; 2) `DropWeaponForPlayer` gasta todo o dinheiro do bot doador ou faz ele dropar a própria AWP sobrevivente no chão; 3) `FULL_BUY` sem checar saldo individual deixa bot pobre sem rifle. | 1) Executar `ExecuteDeterministicBuys` para ambos os times; 2) No drop, exigir saldo residual (`Account >= cost + 3700`) e entregar a arma ao humano via `GiveNamedItem` debitando `InGameMoneyServices.Account` + `Utilities.SetStateChanged`; 3) Adicionar fallback de Galil/Famas se `botMoney < 2700` no `FULL_BUY` e drop automático de AWP para o `AWPer`. |
| 🟠 **Importante** | **I-01** | `OllamaIglService.cs` (Linhas 61-191) | O prompt não envia os `SpotIds` do mapa atual, mistura spots CT/TR no exemplo e `EnsureValidBotOrders` não valida se o `SpotId` existe no `MapProfileManager`. | Injetar a lista compacta de `SpotIds` válidos do mapa/lado atual no prompt e validar cada `SpotId` recebido via `MapProfileManager.GetSpotById`, usando `GetMatchingSpotForOrder` como fallback semântico. |
| 🟠 **Importante** | **I-02** | `OllamaIglService.cs` (Linha 10) & `CsBotManagerPlugin.cs` (Linha 322) | Lista `_history` acessada sem `lock` entre Game Thread e Worker Thread; site da C4 passado sempre como `null` em `RecordRoundResult`. | Proteger `_history` com `lock (_historyLock)` e registrar `_lastPlantedSite` em `OnBombPlanted` para alimentar a memória de 5 rounds com precisão. |
| 🟠 **Importante** | **I-03** | `CsBotManagerPlugin.cs` (Linhas 298-303) | `_hudTimer` é destruído após `StagingDurationSeconds + 5.0f`, impedindo que badges de `<22s`, `SAVE TÁTICO`, `CLUTCH HEROICO` e `ALERTA C4` apareçam no meio/fim do round. | Manter o `_hudTimer` vivo durante o round ou reativá-lo dinamicamente em mudanças de estado críticas (por janelas de 6s) para exibir os avisos de Mid/Late-Round sem poluir a tela. |
| 🟡 **Otimização** | **O-01** | `TacticalSpotsManager.cs` & `CsBotManagerPlugin.cs` | Código legado duplicado (`TacticalSpotsManager.cs`) ainda presente no projeto; alocações repetitivas em `GetActivePlayers()`. | Remover `TacticalSpotsManager.cs` (unificando 100% no `MapProfileManager.cs`) e reutilizar buffers de listas pré-alocados nos timers de `0.4s`/`0.5s`. |
