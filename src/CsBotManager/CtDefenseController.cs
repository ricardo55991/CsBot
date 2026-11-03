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
        // Se o plano já foi materializado com as 5 formações pré-validadas do TacticalUtilityIglEngine,
        // preserva os 5 spots distintos e o HoldSiteLocked=true sem sobrescrever!
        if (plan.CtFormationAssignments.Count >= 5)
        {
            TacticalOrderMaterializer.MaterializeCt212Orders(plan, ctBots, _mapProfileManager);
            return;
        }

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
                order2.StagingSpotId = "ct_a_firebox_oneanddone";
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
            Server.PrintToChatAll($" {ChatColors.Yellow}[CT Defesa]{ChatColors.Default} ⚠️ Alerta Nível 1: Pressão no Bomb A sem C4 confirmada! Meio apoia Jungle; Âncora B travado no site!");

            // Se houver defensor avançado na A (ex: perto da Rampa/Palácio em AGGRESSIVE_POKE), recua para ângulo de crossfire seguro (Ticket / Stairs)
            foreach (var bot in ctBots.Where(b => b != null && b.IsValid && b.PawnIsAlive))
            {
                if (IsBotAssignedToSector(bot, plan, "A") && plan.TryGetOrderForBot(bot.Slot, _roleManager.GetBotRole(bot), out var aOrder))
                {
                    if (aOrder.Stance == EngagementStance.AGGRESSIVE_POKE || aOrder.StagingSpotId.Contains("ramp", StringComparison.OrdinalIgnoreCase) || aOrder.StagingSpotId.Contains("palace_close", StringComparison.OrdinalIgnoreCase))
                    {
                        var safeSpotA = _mapProfileManager.GetSpotById("ct_a_ticket")
                                     ?? _mapProfileManager.GetSpotById("ct_a_ticket_passive")
                                     ?? _mapProfileManager.GetSpotById("ct_a_stairs");
                        if (safeSpotA != null)
                        {
                            UpdateBotOrderSpot(bot, plan, "Bombsite A", safeSpotA, EngagementStance.PASSIVE_HOLD, "Recuo tático para crossfire seguro na A sob pressão");
                            _locomotionDriver.NavigateToSpot(bot, safeSpotA, hurry: true, EngagementStance.PASSIVE_HOLD);
                        }
                    }
                }
            }

            // Trava pelo menos 1 Âncora do Bomb B no site contra Fake
            var bAnchor = ctBots.FirstOrDefault(b => b != null && b.IsValid && b.PawnIsAlive && IsBotAssignedToSector(b, plan, "B"));
            if (bAnchor != null && plan.TryGetOrderForBot(bAnchor.Slot, _roleManager.GetBotRole(bAnchor), out var anchorOrd))
            {
                anchorOrd.HoldSiteLocked = true;
                _locomotionDriver.HoldPosition(bAnchor, 8.0f, false);
            }

            // O defensor do Meio desce para a Jungle/Conector para ajudar a A
            var midBot = ctBots.FirstOrDefault(b => b != null && b.IsValid && b.PawnIsAlive && IsBotAssignedToSector(b, plan, "Mid"))
                      ?? _roleManager.GetBotByRole(ctBots, BotRole.Rotator);
            if (midBot != null && midBot.PawnIsAlive)
            {
                var spot = _mapProfileManager.GetSpotById("ct_a_jungle_support")
                        ?? _mapProfileManager.GetSpotById("ct_mid_connector")
                        ?? _mapProfileManager.GetSpotsForSector("Bombsite A", "CT").FirstOrDefault();
                if (spot != null)
                {
                    UpdateBotOrderSpot(midBot, plan, "Bombsite A", spot, EngagementStance.PASSIVE_HOLD, "Apoio do Meio na Jungle/Conector para o Bomb A");
                    _locomotionDriver.NavigateToSpot(midBot, spot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }
            }
        }
        else if (isBombB)
        {
            Server.PrintToChatAll($" {ChatColors.Yellow}[CT Defesa]{ChatColors.Default} ⚠️ Alerta Nível 1: Pressão no Bomb B sem C4 confirmada! Meio apoia Mercado/L; Âncora A travado no site!");

            // Trava pelo menos 1 Âncora do Bomb A no site contra Fake
            var aAnchor = ctBots.FirstOrDefault(b => b != null && b.IsValid && b.PawnIsAlive && IsBotAssignedToSector(b, plan, "A"));
            if (aAnchor != null && plan.TryGetOrderForBot(aAnchor.Slot, _roleManager.GetBotRole(aAnchor), out var anchorOrd))
            {
                anchorOrd.HoldSiteLocked = true;
                _locomotionDriver.HoldPosition(aAnchor, 8.0f, false);
            }

            // O defensor do Meio puxa para o Mercado / Short B para apoiar a B
            var midBot = ctBots.FirstOrDefault(b => b != null && b.IsValid && b.PawnIsAlive && IsBotAssignedToSector(b, plan, "Mid"))
                      ?? _roleManager.GetBotByRole(ctBots, BotRole.Rotator);
            if (midBot != null && midBot.PawnIsAlive)
            {
                var spot = _mapProfileManager.GetSpotById("ct_b_market_door")
                        ?? _mapProfileManager.GetSpotById("ct_b_short_cat")
                        ?? _mapProfileManager.GetSpotsForSector("Bombsite B", "CT").FirstOrDefault();
                if (spot != null)
                {
                    UpdateBotOrderSpot(midBot, plan, "Bombsite B", spot, EngagementStance.PASSIVE_HOLD, "Apoio do Meio para o Bomb B");
                    _locomotionDriver.NavigateToSpot(midBot, spot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }
            }
        }
    }

    /// <summary>
    /// Executa a Rotação em Cadeia Orgânica (Efeito Dominó) quando um defensor CT morre em A, B ou Meio:
    /// - Se morreu 1 no Bomb (resta 1 vivo no Bomb): o sobrevivente recua para ângulo de sobrevivência (Ticket/Mercado),
    ///   o bot do Meio assume o reforço direto no Bomb e 1 dos 2 bots do outro Bomb puxa para o Meio/Conector (mantendo 1 Âncora fixo no bomb oposto).
    /// - Se morreram TODOS os defensores do Bomb (0 vivos no Bomb): os sobreviventes que vêm do outro lado seguram
    ///   nas entradas de contenção (Jungle/CT ou Mercado/L) para reagrupar para o Retake em vez de entrarem de 1 em 1.
    /// </summary>
    public void HandleCtDefenderDeath(
        CCSPlayerController victim,
        string deathSector,
        TacticalPlan plan,
        List<CCSPlayerController> aliveCtBots)
    {
        if (victim == null || aliveCtBots == null || aliveCtBots.Count == 0) return;

        bool diedInA = deathSector.Contains("A", StringComparison.OrdinalIgnoreCase) ||
                       deathSector.Contains("Rampa", StringComparison.OrdinalIgnoreCase) ||
                       deathSector.Contains("Palacio", StringComparison.OrdinalIgnoreCase) ||
                       deathSector.Contains("Caverna", StringComparison.OrdinalIgnoreCase) ||
                       deathSector.Contains("Ticket", StringComparison.OrdinalIgnoreCase);

        bool diedInB = deathSector.Contains("B", StringComparison.OrdinalIgnoreCase) ||
                       deathSector.Contains("Tapete", StringComparison.OrdinalIgnoreCase) ||
                       deathSector.Contains("Mercado", StringComparison.OrdinalIgnoreCase) ||
                       deathSector.Contains("Van", StringComparison.OrdinalIgnoreCase);

        if (!diedInA && !diedInB)
        {
            // Se morreu no Meio/Janela/Conector: um dos defensores secundários da B (Short/L) ou A (Stairs/Connector) fecha o Conector/Jungle
            var supportBot = aliveCtBots
                .Where(b => b != null && b.IsValid && b.PawnIsAlive)
                .FirstOrDefault(b => IsBotAssignedToSector(b, plan, "B") || IsBotAssignedToSector(b, plan, "A"));

            if (supportBot != null)
            {
                var safeMidSpot = _mapProfileManager.GetSpotById("ct_a_jungle_support")
                               ?? _mapProfileManager.GetSpotById("ct_mid_connector")
                               ?? _mapProfileManager.GetSpotById("ct_mid_connector_headshot");
                if (safeMidSpot != null)
                {
                    UpdateBotOrderSpot(supportBot, plan, "Mid Connector", safeMidSpot, EngagementStance.PASSIVE_HOLD, "Cobrindo baixa no Meio a partir da Jungle/Conector");
                    _locomotionDriver.NavigateToSpot(supportBot, safeMidSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }
            }
            return;
        }

        string attackedSite = diedInA ? "A" : "B";
        string otherSite = diedInA ? "B" : "A";

        var survivorsInAttackedSite = aliveCtBots
            .Where(b => b != null && b.IsValid && b.PawnIsAlive && IsBotAssignedToSector(b, plan, attackedSite))
            .ToList();

        var midDefenders = aliveCtBots
            .Where(b => b != null && b.IsValid && b.PawnIsAlive && IsBotAssignedToSector(b, plan, "Mid"))
            .ToList();

        var otherSiteDefenders = aliveCtBots
            .Where(b => b != null && b.IsValid && b.PawnIsAlive && IsBotAssignedToSector(b, plan, otherSite))
            .ToList();

        if (survivorsInAttackedSite.Count >= 1)
        {
            // CASO 1: Caiu 1 defensor no Bomb, mas ainda resta 1 vivo segurando o site!
            var loneSurvivor = survivorsInAttackedSite[0];
            TacticalSpot? survivalSpot = diedInA
                ? (_mapProfileManager.GetSpotById("ct_a_ticket") ?? _mapProfileManager.GetSpotById("ct_a_ticket_passive") ?? _mapProfileManager.GetSpotById("ct_a_ct_spawn"))
                : (_mapProfileManager.GetSpotById("ct_b_bench") ?? _mapProfileManager.GetSpotById("ct_b_bench_deep") ?? _mapProfileManager.GetSpotById("ct_b_market_window"));

            if (survivalSpot != null)
            {
                UpdateBotOrderSpot(loneSurvivor, plan, $"Bombsite {attackedSite}", survivalSpot, EngagementStance.PASSIVE_HOLD, $"Sobrevivente único no Bomb {attackedSite} recuado em ângulo seguro aguardando reforço");
                _locomotionDriver.NavigateToSpot(loneSurvivor, survivalSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
            }

            // O bot do Meio entra para recompor 2 jogadores no Bomb atacado
            var rotatorFromMid = midDefenders.FirstOrDefault();
            if (rotatorFromMid != null)
            {
                TacticalSpot? reinforceSpot = diedInA
                    ? (_mapProfileManager.GetSpotById("ct_a_stairs") ?? _mapProfileManager.GetSpotById("ct_a_jungle_support") ?? _mapProfileManager.GetSpotById("ct_mid_connector"))
                    : (_mapProfileManager.GetSpotById("ct_b_short_cat") ?? _mapProfileManager.GetSpotById("ct_b_market_door"));

                if (reinforceSpot != null)
                {
                    UpdateBotOrderSpot(rotatorFromMid, plan, $"Bombsite {attackedSite}", reinforceSpot, EngagementStance.PASSIVE_HOLD, $"Rotação imediata do Meio para recompor dupla no Bomb {attackedSite}");
                    _locomotionDriver.NavigateToSpot(rotatorFromMid, reinforceSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }
            }

            // Se houver 2 bots no outro Bomb, 1 deles puxa para o Meio/Conector (Efeito Dominó) e o outro fica como Âncora fixo!
            if (otherSiteDefenders.Count >= 2)
            {
                var flexRotator = otherSiteDefenders[0];
                var trueAnchor = otherSiteDefenders[1];

                var midCoverSpot = diedInA
                    ? (_mapProfileManager.GetSpotById("ct_a_jungle_support") ?? _mapProfileManager.GetSpotById("ct_mid_connector"))
                    : (_mapProfileManager.GetSpotById("ct_b_short_cat") ?? _mapProfileManager.GetSpotById("ct_mid_window"));

                if (midCoverSpot != null)
                {
                    UpdateBotOrderSpot(flexRotator, plan, "Mid", midCoverSpot, EngagementStance.PASSIVE_HOLD, $"Puxando do Bomb {otherSite} para cobrir Meio/Rotação rumo ao Bomb {attackedSite}");
                    _locomotionDriver.NavigateToSpot(flexRotator, midCoverSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }

                if (plan.TryGetOrderForBot(trueAnchor.Slot, _roleManager.GetBotRole(trueAnchor), out var anchorOrd))
                {
                    anchorOrd.HoldSiteLocked = true;
                }
            }

            UtilityAndClockCoordinator.PrintTeamChat(
                CsTeam.CounterTerrorist,
                loneSurvivor.PlayerName,
                $"Caiu um aqui no Bomb {attackedSite}! Recuei pro pixel seguro ({survivalSpot?.Name ?? attackedSite}), Meio encosta pra dobrar comigo!");
        }
        else
        {
            // CASO 2: Morreram TODOS os defensores do Bomb atacado (0 vivos no site)!
            // Os CTs restantes NÃO entram de 1 em 1 para morrer: eles seguram nas entradas de contenção (Jungle/CT ou Mercado/L) esperando o Retake em grupo!
            string[] stagingSpotIds = diedInA
                ? new[] { "ct_a_jungle_support", "ct_a_ct_spawn", "ct_mid_connector" }
                : new[] { "ct_b_market_window", "ct_b_market_door", "ct_b_short_cat" };

            int idx = 0;
            foreach (var bot in aliveCtBots.Where(b => b != null && b.IsValid && b.PawnIsAlive))
            {
                string spotId = stagingSpotIds[idx % stagingSpotIds.Length];
                var stagingSpot = _mapProfileManager.GetSpotById(spotId)
                               ?? _mapProfileManager.GetSpotsForSector($"Bombsite {attackedSite}", "CT").FirstOrDefault();
                if (stagingSpot != null)
                {
                    UpdateBotOrderSpot(bot, plan, $"Bombsite {attackedSite}", stagingSpot, EngagementStance.PASSIVE_HOLD, $"Reagrupando na contenção do Bomb {attackedSite} para Retake coordenado");
                    _locomotionDriver.NavigateToSpot(bot, stagingSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
                }
                idx++;
            }

            var speaker = aliveCtBots.FirstOrDefault()?.PlayerName ?? "CT";
            UtilityAndClockCoordinator.PrintTeamChat(
                CsTeam.CounterTerrorist,
                speaker,
                $"Perdemos os defensores do Bomb {attackedSite}! Ninguém entra sozinho — reagrupa na contenção pra fazer o Retake junto!");
        }
    }

    private bool IsBotAssignedToSector(CCSPlayerController bot, TacticalPlan plan, string sectorKeyword)
    {
        if (plan.CtFormationAssignments.TryGetValue(bot.Slot, out var assign))
        {
            if (sectorKeyword.Equals("Mid", StringComparison.OrdinalIgnoreCase))
            {
                return assign.AssignedSite.Contains("Mid", StringComparison.OrdinalIgnoreCase) ||
                       assign.AssignedSite.Contains("Meio", StringComparison.OrdinalIgnoreCase) ||
                       assign.AssignedSite.Contains("Janela", StringComparison.OrdinalIgnoreCase) ||
                       assign.AssignedSite.Contains("Conector", StringComparison.OrdinalIgnoreCase);
            }
            return assign.AssignedSite.Contains(sectorKeyword, StringComparison.OrdinalIgnoreCase);
        }

        var role = _roleManager.GetBotRole(bot);
        if (plan.TryGetOrderForBot(bot.Slot, role, out var order))
        {
            if (sectorKeyword.Equals("Mid", StringComparison.OrdinalIgnoreCase))
            {
                return order.TargetArea.Contains("Mid", StringComparison.OrdinalIgnoreCase) ||
                       order.TargetArea.Contains("Meio", StringComparison.OrdinalIgnoreCase) ||
                       order.TargetArea.Contains("Janela", StringComparison.OrdinalIgnoreCase) ||
                       order.TargetArea.Contains("Conector", StringComparison.OrdinalIgnoreCase);
            }
            return order.TargetArea.Contains(sectorKeyword, StringComparison.OrdinalIgnoreCase);
        }

        return false;
    }

    private void UpdateBotOrderSpot(
        CCSPlayerController bot,
        TacticalPlan plan,
        string newTargetArea,
        TacticalSpot newSpot,
        EngagementStance stance,
        string reason)
    {
        var role = _roleManager.GetBotRole(bot) ?? BotRole.Rotator;
        if (plan.TryGetOrderForBot(bot.Slot, role, out var order))
        {
            order.TargetArea = newTargetArea;
            order.StagingSpotId = newSpot.Id;
            order.ExecuteSpotId = newSpot.Id;
            order.Stance = stance;
            order.RoleAction = reason;
        }

        string slotKey = $"slot_{bot.Slot}";
        if (plan.BotOrders.TryGetValue(slotKey, out var slotOrd))
        {
            slotOrd.TargetArea = newTargetArea;
            slotOrd.StagingSpotId = newSpot.Id;
            slotOrd.ExecuteSpotId = newSpot.Id;
            slotOrd.Stance = stance;
            slotOrd.RoleAction = reason;
        }

        if (plan.CtFormationAssignments.TryGetValue(bot.Slot, out var assign))
        {
            assign.AssignedSite = newTargetArea.Contains("A", StringComparison.OrdinalIgnoreCase)
                ? "A"
                : (newTargetArea.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "Mid");
            assign.InitialSpot = newSpot.Id;
            assign.ExecuteSpot = newSpot.Id;
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
