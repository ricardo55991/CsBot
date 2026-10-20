using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

using CsTimer = CounterStrikeSharp.API.Modules.Timers.Timer;

namespace CsBotManager;

public class CtDefenseController
{
    private readonly CsBotManagerPlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly BotLocomotionDriver _locomotionDriver;

    private AlertLevel _currentAlertLevel = AlertLevel.Level0_Default;
    private float _lastPressureTimeA = -100.0f;
    private float _lastPressureTimeB = -100.0f;
    private CsTimer? _duoTimer;
    private readonly Random _random = new();

    public AlertLevel CurrentAlertLevel => _currentAlertLevel;

    public CtDefenseController(
        CsBotManagerPlugin plugin,
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        BotLocomotionDriver locomotionDriver)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _locomotionDriver = locomotionDriver;
    }

    public void OnRoundStart(TacticalPlan plan, List<CCSPlayerController> ctBots)
    {
        _currentAlertLevel = AlertLevel.Level0_Default;
        plan.CurrentAlertLevel = AlertLevel.Level0_Default;
        _lastPressureTimeA = -100.0f;
        _lastPressureTimeB = -100.0f;
        _duoTimer?.Kill();
        _duoTimer = null;

        ApplyComplementaryCrossfire(plan, ctBots);
    }

    public void ApplyComplementaryCrossfire(TacticalPlan plan, List<CCSPlayerController> ctBots)
    {
        var bBots = new List<CCSPlayerController>();
        var aBots = new List<CCSPlayerController>();

        foreach (var bot in ctBots)
        {
            var role = _roleManager.GetBotRole(bot);
            if (role == null) continue;

            string key = RoleManager.GetOrderKey(role.Value);
            if (plan.BotOrders.TryGetValue(key, out var order))
            {
                order.HoldSiteLocked = false;
                if (order.TargetArea.Contains("B", StringComparison.OrdinalIgnoreCase))
                    bBots.Add(bot);
                else if (order.TargetArea.Contains("A", StringComparison.OrdinalIgnoreCase))
                    aBots.Add(bot);
            }
        }

        // Se houver 2 defensores no Bomb B: cria Fogo Cruzado Tapete x L/Mercado
        if (bBots.Count >= 2)
        {
            var bot1 = bBots[0];
            var bot2 = bBots[1];
            var role1 = _roleManager.GetBotRole(bot1);
            var role2 = _roleManager.GetBotRole(bot2);

            if (role1 != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role1.Value), out var order1))
            {
                order1.StagingSpotId = "ct_b_van_peek"; // Marca saída do Tapete
                order1.Stance = EngagementStance.JIGGLE_INFO;
            }
            if (role2 != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role2.Value), out var order2))
            {
                order2.StagingSpotId = "ct_b_short_corner"; // Marca L e cruza com a Van
                order2.Stance = EngagementStance.PASSIVE_HOLD;
            }
            Server.PrintToConsole($"[CtDefenseController] Crossfire B armado: {bot1.PlayerName} (Van/Tapete) x {bot2.PlayerName} (Short/L).");
        }

        // Se houver 2 defensores no Bomb A: cria Fogo Cruzado Degrau x Firebox
        if (aBots.Count >= 2)
        {
            var bot1 = aBots[0];
            var bot2 = aBots[1];
            var role1 = _roleManager.GetBotRole(bot1);
            var role2 = _roleManager.GetBotRole(bot2);

            if (role1 != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role1.Value), out var order1))
            {
                order1.StagingSpotId = "ct_a_stairs_cross";
                order1.Stance = EngagementStance.PASSIVE_HOLD;
            }
            if (role2 != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role2.Value), out var order2))
            {
                order2.StagingSpotId = "ct_a_firebox_headshot";
                order2.Stance = EngagementStance.ONE_AND_DONE;
            }
            Server.PrintToConsole($"[CtDefenseController] Crossfire A armado: {bot1.PlayerName} (Stairs) x {bot2.PlayerName} (Firebox).");
        }
    }

    public void OnRoundFreezeEnd(TacticalPlan plan, List<CCSPlayerController> ctBots)
    {
        if (plan.CtDuoPlay == CtDuoPlayType.None || ctBots.Count < 2) return;

        var supportBot = _roleManager.GetBotByRole(ctBots, BotRole.Rotator) ??
                         _roleManager.GetBotByRole(ctBots, BotRole.AWPer) ??
                         ctBots[0];

        var entryBot = _roleManager.GetBotByRole(ctBots, BotRole.EntryFragger) ??
                       ctBots.FirstOrDefault(b => b.Slot != supportBot.Slot) ??
                       ctBots[1];

        if (supportBot == null || entryBot == null) return;

        string duoName = plan.CtDuoPlay == CtDuoPlayType.DominioCavernaRamp ? "Caverna/Rampa A" : "Meio/Conector";
        Server.PrintToChatAll($" {ChatColors.Green}[CT Duo Play]{ChatColors.Default} Jogada ensaiada ativada: {ChatColors.Gold}{duoName}{ChatColors.Default} ({supportBot.PlayerName} + {entryBot.PlayerName})!");

        // 1.5s após freeze: Support prepara e arremessa a flash de domínio (F-006: AddRoundTimer)
        _duoTimer = _plugin.AddRoundTimer(1.5f, () =>
        {
            if (!supportBot.IsValid || !entryBot.IsValid) return;

            _locomotionDriver.ThrowUtility(supportBot, 43); // 43 = Flashbang
            Server.PrintToChatAll($" {ChatColors.LightBlue}[CT Duo Play]{ChatColors.Default} {supportBot.PlayerName} arremessou POP-FLASH de domínio no setor {duoName}!");

            // 1.0s após a flash: Entry avança para o pixel agressivo via NavMesh (C-01C)
            _plugin.AddRoundTimer(1.0f, () =>
            {
                if (!entryBot.IsValid || !entryBot.PawnIsAlive) return;

                string aggressiveSpotId = plan.CtDuoPlay == CtDuoPlayType.DominioCavernaRamp
                    ? "ct_a_palace_close_poke"
                    : "ct_mid_short_catwalk";

                var spot = _mapProfileManager.GetSpotById(aggressiveSpotId);
                if (spot != null)
                {
                    _locomotionDriver.NavigateToSpot(entryBot, spot, hurry: true, EngagementStance.ONE_AND_DONE);

                    var role = _roleManager.GetBotRole(entryBot);
                    if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                    {
                        order.Stance = EngagementStance.ONE_AND_DONE;
                    }

                    Server.PrintToChatAll($" {ChatColors.Gold}[CT Duo Play]{ChatColors.Default} {entryBot.PlayerName} dominou o espaço em postura {ChatColors.Green}ONE_AND_DONE{ChatColors.Default}!");
                }
            });

            // 6.0s após o avanço: Support volta para sua posição segura via NavMesh (C-01C)
            _plugin.AddRoundTimer(6.0f, () =>
            {
                if (!supportBot.IsValid || !supportBot.PawnIsAlive) return;

                string fallbackId = plan.CtDuoPlay == CtDuoPlayType.DominioCavernaRamp
                    ? "ct_a_stairs_cross"
                    : "ct_jungle_safe";

                var safeSpot = _mapProfileManager.GetSpotById(fallbackId);
                if (safeSpot != null)
                {
                    _locomotionDriver.NavigateToSpot(supportBot, safeSpot, hurry: false, EngagementStance.PASSIVE_HOLD);
                    Server.PrintToChatAll($" {ChatColors.LightBlue}[CT Duo Play]{ChatColors.Default} {supportBot.PlayerName} concluiu o suporte e retornou para reforçar o setor base.");
                }
            });
        });
    }

    public void ReportBombPressure(string sector, TacticalPlan plan, List<CCSPlayerController> ctBots)
    {
        if (_currentAlertLevel == AlertLevel.Level2_BombConfirmed) return;

        float now = Server.CurrentTime;
        bool isBombA = sector.Contains("A") || sector.Contains("Rampa") || sector.Contains("Palacio") || sector.Contains("Fundo");
        bool isBombB = sector.Contains("B") || sector.Contains("Tapete") || sector.Contains("Van") || sector.Contains("Banana") || sector.Contains("Escuro");

        if (isBombA) _lastPressureTimeA = now;
        if (isBombB) _lastPressureTimeB = now;

        // Se houver barulho em ambos os bombs nos últimos 5 segundos, é suspeita de Split/Fake -> ninguém roda!
        if (Math.Abs(_lastPressureTimeA - _lastPressureTimeB) < 5.0f && _lastPressureTimeA > 0 && _lastPressureTimeB > 0)
        {
            Server.PrintToChatAll($" {ChatColors.Yellow}[CT Defesa]{ChatColors.Default} Pressão simultânea detectada em A e B! {ChatColors.Gold}ANTI-FAKE ATIVADO: Todos os defensores mantêm suas posições!{ChatColors.Default}");
            return;
        }

        // Alerta Nível 1: Pressão em um bomb SEM a C4 confirmada
        _currentAlertLevel = AlertLevel.Level1_PressureNoBomb;
        plan.CurrentAlertLevel = AlertLevel.Level1_PressureNoBomb;

        if (isBombA)
        {
            Server.PrintToChatAll($" {ChatColors.Yellow}[CT Defesa]{ChatColors.Default} ⚠️ Alerta Nível 1: Pressão no Bomb A sem C4 confirmada! Rotator apoia; Âncora B travado no site!");

            var anchorBot = _roleManager.GetBotByRole(ctBots, BotRole.Anchor);
            if (anchorBot != null)
            {
                var role = _roleManager.GetBotRole(anchorBot);
                if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                {
                    order.HoldSiteLocked = true;
                    _locomotionDriver.HoldPosition(anchorBot, 8.0f, false);
                }
            }

            var rotatorBot = _roleManager.GetBotByRole(ctBots, BotRole.Rotator);
            if (rotatorBot != null && rotatorBot.PawnIsAlive)
            {
                var spot = _mapProfileManager.GetSpotById("ct_a_jungle_support") ?? _mapProfileManager.GetSpotsForSector("Bombsite A", "CT").FirstOrDefault();
                if (spot != null)
                {
                    _locomotionDriver.NavigateToSpot(rotatorBot, spot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }
            }
        }
        else if (isBombB)
        {
            Server.PrintToChatAll($" {ChatColors.Yellow}[CT Defesa]{ChatColors.Default} ⚠️ Alerta Nível 1: Pressão no Bomb B sem C4 confirmada! Rotator apoia; Âncora A travado no site!");

            var anchorBot = _roleManager.GetBotByRole(ctBots, BotRole.Anchor);
            if (anchorBot != null)
            {
                var role = _roleManager.GetBotRole(anchorBot);
                if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                {
                    order.HoldSiteLocked = true;
                    _locomotionDriver.HoldPosition(anchorBot, 8.0f, false);
                }
            }

            var rotatorBot = _roleManager.GetBotByRole(ctBots, BotRole.Rotator);
            if (rotatorBot != null && rotatorBot.PawnIsAlive)
            {
                var spot = _mapProfileManager.GetSpotById("ct_b_market_door") ?? _mapProfileManager.GetSpotsForSector("Bombsite B", "CT").FirstOrDefault();
                if (spot != null)
                {
                    _locomotionDriver.NavigateToSpot(rotatorBot, spot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }
            }
        }
    }

    public void ReportBombConfirmed(string site, TacticalPlan plan, List<CCSPlayerController> ctBots)
    {
        _currentAlertLevel = AlertLevel.Level2_BombConfirmed;
        plan.CurrentAlertLevel = AlertLevel.Level2_BombConfirmed;

        Server.PrintToChatAll($" {ChatColors.Red}[CT Defesa]{ChatColors.Default} 🚨 {ChatColors.Gold}ALERTA NÍVEL 2: C4 CONFIRMADA NO BOMB {site.ToUpper()}!{ChatColors.Default} Rotação total para Retake!");

        string targetSector = site.ToUpper() == "A" ? "Bombsite A" : "Bombsite B";
        var retakeSpots = _mapProfileManager.GetSpotsForSector(targetSector, "CT");

        int spotIdx = 0;
        foreach (var bot in ctBots)
        {
            if (!bot.IsValid || !bot.PawnIsAlive) continue;

            var role = _roleManager.GetBotRole(bot);
            if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
            {
                order.HoldSiteLocked = false;
                order.Stance = EngagementStance.AGGRESSIVE_POKE;
            }

            if (retakeSpots.Count > 0)
            {
                var spot = retakeSpots[spotIdx % retakeSpots.Count];
                _locomotionDriver.NavigateToSpot(bot, spot, hurry: true, EngagementStance.AGGRESSIVE_POKE);
                spotIdx++;
            }
        }
    }

    public bool RequestHumanDuoFlash(CCSPlayerController human, string sector, List<CCSPlayerController> ctBots)
    {
        if (ctBots.Count == 0 || human.PlayerPawn.Value == null || human.PlayerPawn.Value.AbsOrigin == null) return false;

        var closestBot = ctBots
            .Where(b => b.PawnIsAlive && b.PlayerPawn.Value != null && b.PlayerPawn.Value.AbsOrigin != null)
            .OrderBy(b => (b.PlayerPawn.Value!.AbsOrigin! - human.PlayerPawn.Value!.AbsOrigin!).Length())
            .FirstOrDefault();

        if (closestBot == null) return false;

        _locomotionDriver.ThrowUtility(closestBot, 43); // 43 = Flashbang
        Server.PrintToChatAll($" {ChatColors.Green}[CT Duo com Humano]{ChatColors.Default} {closestBot.PlayerName} preparando POP-FLASH para {human.PlayerName} abrir {sector.ToUpper()}!");

        _plugin.AddRoundTimer(1.2f, () =>
        {
            human.PrintToCenterHtml("<font color='#00FF66' size='4'><b>⚡ FLASH LANÇADA! ABRA O PIXEL AGORA! ⚡</b></font>");
        });

        return true;
    }

    public void HandleWindowSmokeDetonation(List<CCSPlayerController> ctBots, TacticalPlan plan)
    {
        var windowBot = ctBots.FirstOrDefault(b =>
        {
            if (!b.PawnIsAlive) return false;
            var role = _roleManager.GetBotRole(b);
            if (role == null) return false;
            return plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var o) &&
                   o.TargetArea.Contains("Mid", StringComparison.OrdinalIgnoreCase);
        });

        if (windowBot == null || !windowBot.PawnIsAlive) return;

        int roll = _random.Next(100);
        if (roll < 35)
        {
            // 35%: Arremessa HE para abrir a fumaça
            _locomotionDriver.ThrowUtility(windowBot, 44); // 44 = HE
            UtilityAndClockCoordinator.PrintTeamChat(CsTeam.CounterTerrorist, windowBot.PlayerName, "Janelão smokado! Joguei HE na fumaça pra abrir mira! Fica esperto no meio!");
        }
        else
        {
            // 65%: Recuo inteligente via NavMesh para conector ou jungle (C-01C)
            var safeSpot = _mapProfileManager.GetSpotById("ct_mid_connector_headshot") ??
                           _mapProfileManager.GetSpotById("ct_jungle_safe");

            if (safeSpot != null)
            {
                _locomotionDriver.NavigateToSpot(windowBot, safeSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
                UtilityAndClockCoordinator.PrintTeamChat(CsTeam.CounterTerrorist, windowBot.PlayerName, "Smoke caiu na Janela! Recuei pro Conector pra marcar a passagem em segurança!");
            }
        }
    }

    public bool RequestBotSupportFlash(CCSPlayerController requester, string targetSector, List<CCSPlayerController> ctBots)
    {
        if (!requester.IsValid || !requester.PawnIsAlive || requester.PlayerPawn.Value == null || requester.PlayerPawn.Value.AbsOrigin == null) return false;

        var supporter = ctBots
            .Where(b => b.PawnIsAlive && b.Slot != requester.Slot && b.PlayerPawn.Value != null && b.PlayerPawn.Value.AbsOrigin != null)
            .OrderBy(b => (b.PlayerPawn.Value!.AbsOrigin! - requester.PlayerPawn.Value!.AbsOrigin!).Length())
            .FirstOrDefault();

        if (supporter == null) return false;

        float now = Server.CurrentTime;
        bool isSupporterSectorSafe = (now - _lastPressureTimeA > 5.0f) && (now - _lastPressureTimeB > 5.0f);

        if (!isSupporterSectorSafe)
        {
            UtilityAndClockCoordinator.PrintTeamChat(CsTeam.CounterTerrorist, supporter.PlayerName, "Não consigo apoiar de flash agora, tem barulho no meu bomb!");
            return false;
        }

        _locomotionDriver.ThrowUtility(supporter, 43); // 43 = Flashbang
        UtilityAndClockCoordinator.PrintTeamChat(CsTeam.CounterTerrorist, supporter.PlayerName, $"Bangei por cima do {targetSector} pra você repicar, {requester.PlayerName}!");
        return true;
    }
}
