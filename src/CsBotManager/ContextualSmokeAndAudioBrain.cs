using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class ContextualSmokeAndAudioBrain
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly BotLocomotionDriver _locomotionDriver;
    private readonly CtDefenseController _ctController;
    private readonly TacticalCalloutSystem _calloutSystem;

    private readonly Random _random = new();
    private float _lastSmokeDecisionTime = -100.0f;

    public ContextualSmokeAndAudioBrain(
        BasePlugin plugin,
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        BotLocomotionDriver locomotionDriver,
        CtDefenseController ctController,
        TacticalCalloutSystem calloutSystem)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _locomotionDriver = locomotionDriver;
        _ctController = ctController;
        _calloutSystem = calloutSystem;
    }

    public void HandleSmokeDetonation(float smokeX, float smokeY, float smokeZ, List<CCSPlayerController> ctBots, TacticalPlan? currentPlan)
    {
        var cp = _mapProfileManager.FindChokepointAt(smokeX, smokeY, smokeZ);
        string smokeSector = cp?.Name ?? "o setor";
        string bombId = cp?.AssociatedBomb ?? (smokeSector.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A");

        Vector smokePos = new Vector(smokeX, smokeY, smokeZ);

        // Procura bots CTs defensores dentro do raio de impacto da smoke (<= 450u)
        var affectedBots = ctBots
            .Where(b => b.IsValid && b.PawnIsAlive && b.PlayerPawn.Value?.AbsOrigin != null)
            .Where(b => (b.PlayerPawn.Value!.AbsOrigin! - smokePos).Length() <= 450.0f)
            .ToList();

        if (affectedBots.Count == 0) return;

        float now = Server.CurrentTime;
        if (now - _lastSmokeDecisionTime < 2.5f) return;
        _lastSmokeDecisionTime = now;

        foreach (var bot in affectedBots)
        {
            DecideSmokeReaction(bot, smokePos, smokeSector, bombId, ctBots, currentPlan);
        }
    }

    private void DecideSmokeReaction(
        CCSPlayerController bot,
        Vector smokePos,
        string smokeSector,
        string bombId,
        List<CCSPlayerController> allCtBots,
        TacticalPlan? plan)
    {
        var botPawn = bot.PlayerPawn.Value;
        if (botPawn == null || botPawn.AbsOrigin == null) return;

        // ==========================================================================
        // 4 Variáveis em Tempo Real
        // ==========================================================================
        // Var 1: Ouviu áudio em setor adjacente nos últimos 5 segundos?
        bool heardAudioAdjacent = _calloutSystem.HasRecentAudioNear(smokeSector, 5.0f);
        string soundSector = _calloutSystem.GetMostRecentActiveSector(5.0f);
        if (string.IsNullOrEmpty(soundSector)) soundSector = "o chokepoint vizinho";

        // Var 2: Quantos aliados vivos estão no mesmo bombsite?
        int alliesOnSite = CountAliveAlliesOnSite(bot, bombId, allCtBots);

        // Var 3: Arma em mãos
        bool isAwp = HasAwpEquipped(bot);
        bool isSilenced = HasSilencedRifle(bot);

        // Var 4: Colegas estão avançando ou recuados?
        bool alliesPushing = plan != null && plan.CurrentPhase == RoundPhase.Executing && !plan.IsTacticalSaveActive;

        // ==========================================================================
        // CENÁRIO C: Caiu Smoke + O Bot está SOZINHO no Bomb (alliesOnSite <= 1)
        // ==========================================================================
        if (alliesOnSite <= 1)
        {
            int roll = _random.Next(100);

            // 75% Recuo Seguro de Sobrevivência (Solo Anchor Fallback)
            if (roll < 75)
            {
                ExecuteSoloFallback(bot, bombId, smokeSector, plan, allCtBots);
            }
            // 25% Infiltração Furtiva (Ninja Rat Play)
            else
            {
                ExecuteNinjaRatPlay(bot, bombId, smokeSector, plan);
            }
            return;
        }

        // ==========================================================================
        // CENÁRIO A: Caiu Smoke + Barulho em Setor Vizinho nos últimos 5s (alliesOnSite >= 2)
        // ==========================================================================
        if (heardAudioAdjacent)
        {
            int roll = _random.Next(100);

            // Se o bot estiver de AWP, prioriza fortemente recuar para ângulo longo (80%)
            if (isAwp && roll < 80)
            {
                ExecuteRotateToLongAngle(bot, bombId, smokeSector, plan);
                return;
            }

            // 55% Virar Mira para o Som (Shift Focus to Audio Threat)
            if (roll < 55)
            {
                ExecuteShiftFocusToAudio(bot, bombId, smokeSector, soundSector, plan);
            }
            // 25% Rotacionar para Ângulo Longo Limpo
            else if (roll < 80)
            {
                ExecuteRotateToLongAngle(bot, bombId, smokeSector, plan);
            }
            // 20% Pedir Pop-Flash e Picar o Som
            else
            {
                ExecuteFlashAndPeekSound(bot, smokeSector, soundSector, allCtBots);
            }
            return;
        }

        // ==========================================================================
        // CENÁRIO B: Caiu Smoke + Silêncio Total (alliesOnSite >= 2)
        // ==========================================================================
        {
            int roll = _random.Next(100);

            // Se estiver com M4A1-S (silenciada), aumenta peso de Spam na smoke para 50%
            if (isSilenced && roll < 50)
            {
                ExecuteSmokeSpam(bot, smokeSector, smokePos);
                return;
            }

            // 45% Segurar a Borda da Fumaça (Hold Smoke Edge)
            if (roll < 45)
            {
                ExecuteHoldSmokeEdge(bot, smokeSector, plan);
            }
            // 30% Varrer a Smoke (Smoke Spam)
            else if (roll < 75)
            {
                ExecuteSmokeSpam(bot, smokeSector, smokePos);
            }
            // 15% Buscar Elevação / Ângulo Secundário
            else if (roll < 90)
            {
                ExecuteSeekHighAngle(bot, bombId, smokeSector, plan);
            }
            // 10% Atravessar / Marotar na Borda (Timed Smoke Push)
            else
            {
                ExecuteTimedSmokePush(bot, smokeSector, smokePos, plan);
            }
        }
    }

    // ==============================================================================
    // Ações Concretas de Reação
    // ==============================================================================

    // Cenário A1: Virar Mira para o Som
    private void ExecuteShiftFocusToAudio(CCSPlayerController bot, string bombId, string smokeSector, string soundSector, TacticalPlan? plan)
    {
        var role = _roleManager.GetBotRole(bot);
        if (role != null && plan != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
        {
            order.Stance = EngagementStance.PASSIVE_HOLD;
        }

        // Reposiciona o bot ~100 unidades lateralmente para ângulo favorável
        if (bot.PlayerPawn.Value?.AbsOrigin != null)
        {
            var curPos = bot.PlayerPawn.Value.AbsOrigin;
            Vector slightOffset = new Vector(curPos.X - 80.0f, curPos.Y + 60.0f, curPos.Z);
            _locomotionDriver.NavigateToPoint(bot, slightOffset, hurry: false, EngagementStance.PASSIVE_HOLD);
        }

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            bot,
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Smokaram {smokeSector}, mas já tem gente no {bombId}. Virei pra marcar {soundSector} que ouvi barulho!",
            "takingfire");
    }

    // Cenário A2: Rotacionar para Ângulo Longo Limpo
    private void ExecuteRotateToLongAngle(CCSPlayerController bot, string bombId, string smokeSector, TacticalPlan? plan)
    {
        var fallbackSpot = _mapProfileManager.GetFallbackSpot(bombId.Equals("B", StringComparison.OrdinalIgnoreCase) ? "Mercado" : "Ticket") ??
                           _mapProfileManager.GetSpotById(bombId.Equals("B", StringComparison.OrdinalIgnoreCase) ? "mirage_b_market_window" : "mirage_a_ticket_sniper");

        if (fallbackSpot != null)
        {
            _locomotionDriver.NavigateToSpot(bot, fallbackSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
        }

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            bot,
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Smoke fechou minha mira. Recuando pro ângulo longo pra cobrir a entrada do Bomb {bombId}!",
            "fallback");
    }

    // Cenário A3: Pedir Pop-Flash e Picar o Som
    private void ExecuteFlashAndPeekSound(CCSPlayerController bot, string smokeSector, string soundSector, List<CCSPlayerController> allCtBots)
    {
        var helperBot = allCtBots
            .Where(b => b.Slot != bot.Slot && b.PawnIsAlive && b.PlayerPawn.Value?.AbsOrigin != null)
            .OrderBy(b => (b.PlayerPawn.Value!.AbsOrigin! - bot.PlayerPawn.Value!.AbsOrigin!).Length())
            .FirstOrDefault();

        if (helperBot != null)
        {
            _locomotionDriver.ThrowUtility(helperBot, 43); // 43 = Flashbang
        }

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            bot,
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Vou abrir no barulho do {soundSector}, alguém joga flash por cima!",
            "needbackup");
    }

    // Cenário B1: Segurar a Borda da Fumaça
    private void ExecuteHoldSmokeEdge(CCSPlayerController bot, string smokeSector, TacticalPlan? plan)
    {
        var role = _roleManager.GetBotRole(bot);
        if (role != null && plan != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
        {
            order.Stance = EngagementStance.PASSIVE_HOLD;
        }

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            bot,
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Smokaram {smokeSector}, cravado na borda da smoke sem dar a cara.",
            "holdpos");
    }

    // Cenário B2: Varrer a Smoke (Smoke Spam)
    private void ExecuteSmokeSpam(CCSPlayerController bot, string smokeSector, Vector smokeCenter)
    {
        // Simula disparo controlado através do BotLocomotionDriver mirando no centro da fumaça
        if (bot.PlayerPawn.Value?.AbsOrigin != null)
        {
            // Dá um pequeno strafe de posicionamento
            var cur = bot.PlayerPawn.Value.AbsOrigin;
            Vector strafe = new Vector(cur.X + 40.0f, cur.Y - 30.0f, cur.Z);
            _locomotionDriver.NavigateToPoint(bot, strafe, hurry: false, EngagementStance.PASSIVE_HOLD);
        }

        UtilityAndClockCoordinator.PrintTeamChat(
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Varando o meio da smoke do {smokeSector}!");
    }

    // Cenário B3: Buscar Elevação / Ângulo Secundário
    private void ExecuteSeekHighAngle(CCSPlayerController bot, string bombId, string smokeSector, TacticalPlan? plan)
    {
        var highSpot = _mapProfileManager.GetSpotById(bombId.Equals("B", StringComparison.OrdinalIgnoreCase) ? "mirage_b_cat_sniper" : "mirage_a_stairs_cross");
        if (highSpot != null)
        {
            _locomotionDriver.NavigateToSpot(bot, highSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
        }

        UtilityAndClockCoordinator.PrintTeamChat(
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Subindo no pixel alto pra pegar a cabeça de quem passar a smoke!");
    }

    // Cenário B4: Atravessar / Marotar na Borda (Timed Push)
    private void ExecuteTimedSmokePush(CCSPlayerController bot, string smokeSector, Vector smokeCenter, TacticalPlan? plan)
    {
        _locomotionDriver.NavigateToPoint(bot, smokeCenter, hurry: true, EngagementStance.AGGRESSIVE_POKE);

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            bot,
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Vou rasgar a smoke de surpresa, cobre se der!",
            "go");
    }

    // Cenário C1: Recuo Seguro de Sobrevivência (Solo Anchor Fallback)
    private void ExecuteSoloFallback(CCSPlayerController bot, string bombId, string smokeSector, TacticalPlan? plan, List<CCSPlayerController> allCtBots)
    {
        var safeSpot = _mapProfileManager.GetFallbackSpot(bombId.Equals("B", StringComparison.OrdinalIgnoreCase) ? "Van" : "Ticket") ??
                       _mapProfileManager.GetSpotById(bombId.Equals("B", StringComparison.OrdinalIgnoreCase) ? "mirage_b_site_safe" : "mirage_a_ticket_sniper");

        if (safeSpot != null)
        {
            _locomotionDriver.NavigateToSpot(bot, safeSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
        }

        // Notifica o controlador CT para elevar o alerta do bomb
        if (plan != null)
        {
            _ctController.ReportBombPressure(bombId, plan, allCtBots);
        }

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            bot,
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Tô SOZINHO no Bomb {bombId} e smokaram tudo! Recuei pro fundo pra esperar vocês, gira rápido!",
            "needbackup");
    }

    // Cenário C2: Infiltração Furtiva (Ninja Rat Play)
    private void ExecuteNinjaRatPlay(CCSPlayerController bot, string bombId, string smokeSector, TacticalPlan? plan)
    {
        var ninjaSpot = _mapProfileManager.GetSpotById(bombId.Equals("B", StringComparison.OrdinalIgnoreCase) ? "mirage_b_bench_passive" : "mirage_a_ninja_hide");
        if (ninjaSpot != null)
        {
            // Entra agachado/silencioso no ponto cego
            _locomotionDriver.NavigateToSpot(bot, ninjaSpot, hurry: false, EngagementStance.PASSIVE_HOLD);
        }

        UtilityAndClockCoordinator.PrintTeamChat(
            CsTeam.CounterTerrorist,
            bot.PlayerName,
            $"Shiu! Marotei no canto do Bomb {bombId} na smoke deles. Deixa entrar que pego de costas!");
    }

    // ==============================================================================
    // Métodos Auxiliares
    // ==============================================================================
    private int CountAliveAlliesOnSite(CCSPlayerController bot, string bombId, List<CCSPlayerController> allCtBots)
    {
        int count = 0;
        foreach (var ally in allCtBots)
        {
            if (!ally.IsValid || !ally.PawnIsAlive || ally.PlayerPawn.Value?.AbsOrigin == null) continue;

            var pos = ally.PlayerPawn.Value.AbsOrigin;
            var cp = _mapProfileManager.FindChokepointAt(pos.X, pos.Y, pos.Z);
            string site = cp?.AssociatedBomb ?? (cp?.Name?.Contains("B", StringComparison.OrdinalIgnoreCase) == true ? "B" : "A");

            if (site.Equals(bombId, StringComparison.OrdinalIgnoreCase))
            {
                count++;
            }
        }
        return count;
    }

    private static bool HasAwpEquipped(CCSPlayerController bot)
    {
        var weaponServices = bot.PlayerPawn.Value?.WeaponServices;
        var activeWeapon = weaponServices?.ActiveWeapon.Value;
        string name = activeWeapon?.DesignerName ?? "";
        return name.Contains("awp", StringComparison.OrdinalIgnoreCase) || name.Contains("scout", StringComparison.OrdinalIgnoreCase) || name.Contains("ssg08", StringComparison.OrdinalIgnoreCase);
    }

    private static bool HasSilencedRifle(CCSPlayerController bot)
    {
        var weaponServices = bot.PlayerPawn.Value?.WeaponServices;
        var activeWeapon = weaponServices?.ActiveWeapon.Value;
        string name = activeWeapon?.DesignerName ?? "";
        return name.Contains("m4a1", StringComparison.OrdinalIgnoreCase) || name.Contains("usp", StringComparison.OrdinalIgnoreCase);
    }
}
