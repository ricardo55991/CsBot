using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class EconomyManager
{
    private readonly Random _random = new();
    public BuyState CurrentBuyState { get; private set; } = BuyState.FULL_BUY;
    public int TeamAverageMoney { get; private set; } = 800;
    public bool IsDoubleAwpActive { get; private set; } = false;

    public void OnRoundStart()
    {
        IsDoubleAwpActive = false;
    }

    public BuyState AnalyzeTeamEconomy(List<CCSPlayerController> teamMembers, int roundNumber, int lossBonus, CsTeam team)
    {
        if (teamMembers.Count == 0) return BuyState.FULL_BUY;

        int totalMoney = 0;
        foreach (var m in teamMembers)
        {
            totalMoney += m.InGameMoneyServices?.Account ?? 0;
        }
        TeamAverageMoney = totalMoney / teamMembers.Count;

        // Rounds de pistola (Rounds 1 e 13)
        if (roundNumber == 1 || roundNumber == 13)
        {
            CurrentBuyState = BuyState.FULL_BUY;
            return CurrentBuyState;
        }

        // Pós-pistol perdido (Round 2 ou 14) -> Force Buy
        if (roundNumber == 2 || roundNumber == 14)
        {
            CurrentBuyState = BuyState.FORCE_BUY;
            return CurrentBuyState;
        }

        // Último round da metade (Round 12 ou 24) -> Force Buy total
        if (roundNumber == 12 || roundNumber == 24)
        {
            CurrentBuyState = BuyState.FORCE_BUY;
            return CurrentBuyState;
        }

        // Lógica de cálculo por lado considerando o Loss Bonus real (I-04E)
        if (team == CsTeam.CounterTerrorist)
        {
            if (TeamAverageMoney >= 4700)
                CurrentBuyState = BuyState.FULL_BUY;
            else if (TeamAverageMoney >= 3000)
                CurrentBuyState = BuyState.HALF_BUY;
            else if (TeamAverageMoney + lossBonus >= 4500)
                CurrentBuyState = BuyState.FULL_ECO; // Eco para garantir Full Buy completo no próximo round
            else if (TeamAverageMoney >= 2200)
                CurrentBuyState = BuyState.FORCE_BUY;
            else
                CurrentBuyState = BuyState.FULL_ECO;
        }
        else // Terrorist
        {
            if (TeamAverageMoney >= 4100)
                CurrentBuyState = BuyState.FULL_BUY;
            else if (TeamAverageMoney >= 2600)
                CurrentBuyState = BuyState.HALF_BUY;
            else if (TeamAverageMoney + lossBonus >= 4100)
                CurrentBuyState = BuyState.FULL_ECO; // Eco para garantir Full Buy no próximo round
            else if (TeamAverageMoney >= 2000)
                CurrentBuyState = BuyState.FORCE_BUY;
            else
                CurrentBuyState = BuyState.FULL_ECO;
        }

        return CurrentBuyState;
    }

    public bool DropWeaponForPlayer(CCSPlayerController player, string? requestedWeapon, List<CCSPlayerController> teamBots)
    {
        if (teamBots.Count == 0 || player == null || !player.IsValid) return false;

        string req = (requestedWeapon ?? string.Empty).Trim().ToLowerInvariant();
        bool isCt = player.Team == CsTeam.CounterTerrorist;

        string weaponToBuy = req switch
        {
            "awp" => "awp",
            "m4" or "m4a1" or "m4a4" => isCt ? "m4a1_silencer" : "ak47",
            "ak" or "ak47" => "ak47",
            "deagle" => "deagle",
            _ => isCt ? "m4a1_silencer" : "ak47"
        };

        int cost = weaponToBuy switch
        {
            "awp" => 4750,
            "ak47" => 2700,
            "m4a1_silencer" => 2900,
            "deagle" => 700,
            _ => 2700
        };

        // C-05B: Exige que o bot doador permaneça com pelo menos $2000 após a doação
        var richestBot = teamBots
            .Where(b => b.IsValid && b.InGameMoneyServices != null && (b.InGameMoneyServices.Account - cost) >= 2000)
            .OrderByDescending(b => b.InGameMoneyServices?.Account ?? 0)
            .FirstOrDefault();

        if (richestBot == null || richestBot.InGameMoneyServices == null)
        {
            return false;
        }

        // Deduz diretamente da conta do bot de forma determinística na engine
        richestBot.InGameMoneyServices.Account -= cost;
        Utilities.SetStateChanged(richestBot, "CCSPlayerController", "m_pInGameMoneyServices");

        // Dá a arma diretamente ao jogador humano (sem arremesso no chão e sem perder a própria arma do bot)
        player.GiveNamedItem($"weapon_{weaponToBuy}");

        player.PrintToChat($" {ChatColors.Green}[CsBot Economy]{ChatColors.Default} {richestBot.PlayerName} comprou e entregou {weaponToBuy.ToUpper()} para você!");
        return true;
    }

    // I-04C: Drop automático de AWP para o sniper designado da equipe
    public void TryCoordinateTeamAwpDrop(List<CCSPlayerController> teamBots, RoleManager roleManager, CsTeam team)
    {
        var awpBot = teamBots.FirstOrDefault(b => b.IsValid && roleManager.GetBotRole(b) == BotRole.AWPer);
        if (awpBot == null || awpBot.InGameMoneyServices == null) return;

        // Se o sniper já tem rifle ou AWP salva, não precisa de drop
        if (HasValuablePrimaryWeapon(awpBot)) return;

        int awpBotMoney = awpBot.InGameMoneyServices.Account;
        if (awpBotMoney >= 4750) return; // Ele mesmo consegue comprar

        // Procura um companheiro rico com >= $6800 para bancar a AWP
        var donorBot = teamBots
            .Where(b => b.IsValid && b.Slot != awpBot.Slot && b.InGameMoneyServices != null && (b.InGameMoneyServices.Account - 4750) >= 2000)
            .OrderByDescending(b => b.InGameMoneyServices?.Account ?? 0)
            .FirstOrDefault();

        if (donorBot != null && donorBot.InGameMoneyServices != null)
        {
            donorBot.InGameMoneyServices.Account -= 4750;
            Utilities.SetStateChanged(donorBot, "CCSPlayerController", "m_pInGameMoneyServices");

            awpBot.GiveNamedItem("weapon_awp");
            UtilityAndClockCoordinator.PrintTeamChat(team, donorBot.PlayerName, $"Comprei AWP pra você, {awpBot.PlayerName}! Destrói eles!");
        }
    }

    // Módulo 1: Setup de "Double AWP" Rico no CT
    public void TryCoordinateDoubleAwpSetup(
        List<CCSPlayerController> teamBots,
        RoleManager roleManager,
        TacticalPlan plan,
        CsTeam team)
    {
        if (team != CsTeam.CounterTerrorist || IsDoubleAwpActive) return;

        // Identifica o bot Âncora (ex: âncora do Bomb B)
        var anchorBot = teamBots.FirstOrDefault(b => b.IsValid && roleManager.GetBotRole(b) == BotRole.Anchor)
                     ?? teamBots.FirstOrDefault(b => b.IsValid && roleManager.GetBotRole(b) == BotRole.Rotator);

        if (anchorBot == null || anchorBot.InGameMoneyServices == null) return;

        // Se o âncora já tem AWP salva, apenas ativa a postura de Double AWP
        bool hasAwp = HasSpecificWeapon(anchorBot, "awp");
        if (!hasAwp)
        {
            int botMoney = anchorBot.InGameMoneyServices.Account;
            if (botMoney >= 4750)
            {
                anchorBot.ExecuteClientCommand("buy awp");
                hasAwp = true;
            }
            else
            {
                // Busca companheiro rico com saldo suficiente para dropar a segunda AWP
                var donorBot = teamBots
                    .Where(b => b.IsValid && b.Slot != anchorBot.Slot && b.InGameMoneyServices != null && (b.InGameMoneyServices.Account - 4750) >= 2000)
                    .OrderByDescending(b => b.InGameMoneyServices?.Account ?? 0)
                    .FirstOrDefault();

                if (donorBot != null && donorBot.InGameMoneyServices != null)
                {
                    donorBot.InGameMoneyServices.Account -= 4750;
                    Utilities.SetStateChanged(donorBot, "CCSPlayerController", "m_pInGameMoneyServices");
                    anchorBot.GiveNamedItem("weapon_awp");
                    hasAwp = true;
                    UtilityAndClockCoordinator.PrintTeamChat(team, donorBot.PlayerName, $"Comprei a segunda AWP pra você, {anchorBot.PlayerName}! Double AWP no setup!");
                }
            }
        }

        if (hasAwp)
        {
            IsDoubleAwpActive = true;
            roleManager.ConfigureDoubleAwpSetup(anchorBot, plan);
            UtilityAndClockCoordinator.PrintTeamChat(team, "IGL", "Economia alta! Vamos de DOUBLE AWP, domina as pontas!");
        }
    }

    public void ExecuteDeterministicBuys(
        List<CCSPlayerController> bots,
        BuyState buyState,
        CsTeam team,
        RoleManager roleManager,
        TacticalPlan plan,
        BotLocomotionDriver? locomotionDriver = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        bool isRushTactic = plan.RoundTempo == RoundTempo.FAST_CONTACT || plan.TacticName.ToLowerInvariant().Contains("rush");

        // Coordena drop automático de AWP entre os bots antes das compras individuais
        if (buyState == BuyState.FULL_BUY)
        {
            TryCoordinateTeamAwpDrop(bots, roleManager, team);

            // Módulo 1: Setup de "Double AWP" Rico no CT (TeamAverageMoney >= $7500 com 35% de chance)
            if (isCt && TeamAverageMoney >= 7500)
            {
                if (_random.Next(100) < 35)
                {
                    TryCoordinateDoubleAwpSetup(bots, roleManager, plan, team);
                }
            }
        }

        foreach (var bot in bots)
        {
            if (!bot.IsValid || !bot.IsBot || bot.InGameMoneyServices == null) continue;

            var role = roleManager.GetBotRole(bot) ?? BotRole.Rotator;
            int botMoney = bot.InGameMoneyServices.Account;
            bool alreadyHasRifleOrSniper = HasValuablePrimaryWeapon(bot);

            switch (buyState)
            {
                case BuyState.FULL_BUY:
                    // I-04D: Prioridade Rifle > Capacete para não falir o bot antes do rifle
                    if (!alreadyHasRifleOrSniper)
                    {
                        if (isCt)
                        {
                            if (role == BotRole.AWPer && botMoney >= 4750)
                            {
                                bot.ExecuteClientCommand("buy awp");
                            }
                            else if (botMoney >= 2900)
                            {
                                bot.ExecuteClientCommand("buy m4a1_silencer");
                            }
                            else
                            {
                                bot.ExecuteClientCommand("buy famas");
                            }

                            // Colete e Defuser se sobrar orçamento
                            if (botMoney >= 3550) bot.ExecuteClientCommand("buy vest");
                            if (botMoney >= 4500) bot.ExecuteClientCommand("buy vesthelm");
                            if (botMoney >= 4300) bot.ExecuteClientCommand("buy defuser");
                        }
                        else // TR
                        {
                            if (botMoney >= 2700)
                            {
                                bot.ExecuteClientCommand("buy ak47");
                            }
                            else if (isRushTactic && role == BotRole.EntryFragger)
                            {
                                bot.ExecuteClientCommand("buy mac10");
                            }
                            else
                            {
                                bot.ExecuteClientCommand("buy galilar");
                            }

                            // Colete após garantir o rifle
                            if (botMoney >= 3700) bot.ExecuteClientCommand("buy vesthelm");
                            else if (botMoney >= 3350) bot.ExecuteClientCommand("buy vest");
                        }
                    }
                    else
                    {
                        // Já possui arma primária salva: garante proteção e utilitárias
                        bot.ExecuteClientCommand("buy vesthelm");
                        if (isCt) bot.ExecuteClientCommand("buy defuser");
                    }

                    // Utilitárias por função
                    bot.ExecuteClientCommand("buy smokegrenade");
                    bot.ExecuteClientCommand("buy flashbang");
                    if (role == BotRole.EntryFragger || role == BotRole.Anchor)
                    {
                        bot.ExecuteClientCommand(isCt ? "buy incgrenade" : "buy molotov");
                    }
                    else
                    {
                        bot.ExecuteClientCommand("buy hegrenade");
                    }
                    break;

                case BuyState.FORCE_BUY:
                    // Garante arma antes do colete no Force Buy
                    if (!alreadyHasRifleOrSniper)
                    {
                        if (isCt)
                        {
                            if (botMoney >= 2900) bot.ExecuteClientCommand("buy m4a1_silencer");
                            else if (botMoney >= 2050) bot.ExecuteClientCommand("buy famas");
                            else bot.ExecuteClientCommand("buy mp9");
                        }
                        else
                        {
                            if (botMoney >= 2700) bot.ExecuteClientCommand("buy ak47");
                            else if (botMoney >= 1800) bot.ExecuteClientCommand("buy galilar");
                            else bot.ExecuteClientCommand("buy mac10");
                        }
                    }
                    bot.ExecuteClientCommand("buy vest");
                    bot.ExecuteClientCommand("buy flashbang");
                    bot.ExecuteClientCommand("buy smokegrenade");
                    break;

                case BuyState.HALF_BUY:
                    // Preserva no mínimo $2000 por bot
                    if (!alreadyHasRifleOrSniper)
                    {
                        if (botMoney > 2650)
                        {
                            bot.ExecuteClientCommand("buy vest");
                            bot.ExecuteClientCommand("buy deagle");
                        }
                        else if (botMoney > 2300)
                        {
                            bot.ExecuteClientCommand(isCt ? "buy fiveseven" : "buy tec9");
                        }
                    }
                    break;

                case BuyState.FULL_ECO:
                    // Trava compra nativa para não gastar saldo no Eco
                    locomotionDriver?.BotApi?.SetBuySkip(bot.Slot);
                    break;
            }
        }
    }

    public bool HasValuablePrimaryWeapon(CCSPlayerController bot)
    {
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null || pawn.WeaponServices == null) return false;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var weapon = handle.Value;
            if (weapon != null && weapon.IsValid && !string.IsNullOrEmpty(weapon.DesignerName))
            {
                string name = weapon.DesignerName.ToLowerInvariant();
                if (name.Contains("awp") || name.Contains("ak47") || name.Contains("m4a1") || name.Contains("m4a4") ||
                    name.Contains("ssg08") || name.Contains("galilar") || name.Contains("famas") || name.Contains("aug") || name.Contains("sg553"))
                {
                    return true;
                }
            }
        }
        return false;
    }

    public bool HasTier1PrimaryWeapon(CCSPlayerController bot)
    {
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null || pawn.WeaponServices == null) return false;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var weapon = handle.Value;
            if (weapon != null && weapon.IsValid && !string.IsNullOrEmpty(weapon.DesignerName))
            {
                string name = weapon.DesignerName.ToLowerInvariant();
                if (name.Contains("awp") || name.Contains("ak47") || name.Contains("m4a1"))
                {
                    return true;
                }
            }
        }
        return false;
    }

    public bool HasSpecificWeapon(CCSPlayerController bot, string weaponSubName)
    {
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null || pawn.WeaponServices == null) return false;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var weapon = handle.Value;
            if (weapon != null && weapon.IsValid && !string.IsNullOrEmpty(weapon.DesignerName))
            {
                if (weapon.DesignerName.Contains(weaponSubName, StringComparison.OrdinalIgnoreCase))
                {
                    return true;
                }
            }
        }
        return false;
    }

    // =========================================================================
    // DISCIPLINA DA C4 NO FREEZE TIME (PARTE A - ITEM 2)
    // =========================================================================
    public void EnforceC4Discipline(List<CCSPlayerController> trBots, CCSPlayerController? human, RoleManager roleManager)
    {
        // Se a C4 estiver com o humano, respeita e não remove
        if (human != null && human.IsValid && BotLocomotionDriver.HasC4(human))
        {
            return;
        }

        var c4Bot = trBots.FirstOrDefault(b => b.IsValid && b.PawnIsAlive && BotLocomotionDriver.HasC4(b));
        if (c4Bot == null) return;

        var role = roleManager.GetBotRole(c4Bot);
        // Entry Fragger ou Anchor/Lurker nunca devem carregar a C4 na linha de frente
        if (role == BotRole.EntryFragger || role == BotRole.Anchor)
        {
            var receiverBot = trBots.FirstOrDefault(b => b.Slot != c4Bot.Slot && b.PawnIsAlive && roleManager.GetBotRole(b) == BotRole.Rotator)
                           ?? trBots.FirstOrDefault(b => b.Slot != c4Bot.Slot && b.PawnIsAlive && roleManager.GetBotRole(b) == BotRole.AWPer)
                           ?? trBots.FirstOrDefault(b => b.Slot != c4Bot.Slot && b.PawnIsAlive);

            if (receiverBot != null)
            {
                var pawn = c4Bot.PlayerPawn.Value;
                if (pawn?.WeaponServices?.MyWeapons != null)
                {
                    foreach (var handle in pawn.WeaponServices.MyWeapons)
                    {
                        var w = handle.Value;
                        if (w != null && w.IsValid && !string.IsNullOrEmpty(w.DesignerName) && w.DesignerName.Contains("c4", StringComparison.OrdinalIgnoreCase))
                        {
                            w.Remove();
                            break;
                        }
                    }
                }

                receiverBot.GiveNamedItem("weapon_c4");
                UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                    c4Bot,
                    CsTeam.Terrorist,
                    c4Bot.PlayerName,
                    $"Passei a C4 pro suporte ({receiverBot.PlayerName}) pra eu abrir espaço na frente!",
                    "affirmative");
            }
        }
    }

    // =========================================================================
    // LOOTING INTELIGENTE DE ARMAS NO FIM DO ROUND (PARTE A - ITEM 3)
    // =========================================================================
    public void PerformPostRoundLooting(List<CCSPlayerController> aliveBots, BotLocomotionDriver locomotionDriver)
    {
        var groundWeapons = Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_ak47")
            .Concat(Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_m4a1_silencer"))
            .Concat(Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_m4a1"))
            .Concat(Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_awp"))
            .Where(w => w.IsValid && (w.OwnerEntity == null || !w.OwnerEntity.IsValid) && w.AbsOrigin != null)
            .ToList();

        if (groundWeapons.Count == 0) return;

        foreach (var bot in aliveBots)
        {
            if (!bot.IsValid || !bot.PawnIsAlive || bot.PlayerPawn.Value == null || bot.PlayerPawn.Value.AbsOrigin == null) continue;

            // Se o bot já possui arma de Tier 1, não precisa de loot
            if (HasTier1PrimaryWeapon(bot)) continue;

            var botPos = bot.PlayerPawn.Value.AbsOrigin;

            // Procura a arma Tier 1 caída mais próxima (<= 600 unidades)
            var bestWeapon = groundWeapons
                .Where(w => w.IsValid && w.AbsOrigin != null)
                .OrderBy(w => (w.AbsOrigin! - botPos).Length())
                .FirstOrDefault();

            if (bestWeapon == null) continue;

            var weaponPos = bestWeapon.AbsOrigin;
            if (weaponPos == null) continue;

            float dist = (weaponPos - botPos).Length();
            if (dist > 600.0f) continue;

            groundWeapons.Remove(bestWeapon); // Evita disputa pela mesma arma

            string designer = bestWeapon.DesignerName;
            string cleanName = designer switch
            {
                "weapon_ak47" => "AK-47",
                "weapon_m4a1_silencer" => "M4A1-S",
                "weapon_m4a1" => "M4A4",
                "weapon_awp" => "AWP",
                _ => "arma superior"
            };

            if (dist <= 140.0f)
            {
                // Coleta imediata
                bot.ExecuteClientCommand("drop");
                bot.GiveNamedItem(designer);
                bestWeapon.Remove();

                UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                    bot,
                    bot.Team,
                    bot.PlayerName,
                    $"Peguei uma {cleanName} do chão pro próximo round!",
                    "cheer");
            }
            else
            {
                // Caminha até a arma para pegar
                locomotionDriver.NavigateToPosition(bot, weaponPos.X, weaponPos.Y, weaponPos.Z, hurry: true);
                Server.NextFrame(() =>
                {
                    if (bot.IsValid && bot.PawnIsAlive && bestWeapon.IsValid)
                    {
                        bot.ExecuteClientCommand("drop");
                        bot.GiveNamedItem(designer);
                        bestWeapon.Remove();
                        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                            bot,
                            bot.Team,
                            bot.PlayerName,
                            $"Peguei uma {cleanName} do chão pro próximo round!",
                            "cheer");
                    }
                });
            }
        }
    }
}
