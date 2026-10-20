using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

using CsTimer = CounterStrikeSharp.API.Modules.Timers.Timer;

namespace CsBotManager;

public class TrMacroPivotController
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly MidRoundAdapter _midRoundAdapter;
    private readonly PacingAndFallbackController _pacingController;
    private readonly BotLocomotionDriver _locomotionDriver;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }

    private readonly Random _random = new();

    // Rastreamento de estado por round
    private bool _hasPivotedThisRound = false;
    private float _executeStartTime = -100.0f;
    private bool _hasTriggeredFirstKillExploit = false;

    // Rastreamento para Clearance do Lurker: lurkerSlot -> (killTime, site, victimPos)
    private readonly Dictionary<int, (float KillTime, string Bombsite, Vector KillPos)> _pendingLurkerChecks = new();
    private readonly Dictionary<int, float> _lastDamageTimeBySlot = new();

    public TrMacroPivotController(
        BasePlugin plugin,
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        MidRoundAdapter midRoundAdapter,
        PacingAndFallbackController pacingController,
        BotLocomotionDriver locomotionDriver)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _midRoundAdapter = midRoundAdapter;
        _pacingController = pacingController;
        _locomotionDriver = locomotionDriver;
    }

    public void OnRoundStart()
    {
        _hasPivotedThisRound = false;
        _executeStartTime = -100.0f;
        _hasTriggeredFirstKillExploit = false;
        _pendingLurkerChecks.Clear();
        _lastDamageTimeBySlot.Clear();
    }

    public void OnExecuteStarted(TacticalPlan plan)
    {
        _executeStartTime = Server.CurrentTime;
    }

    public void OnPlayerHurt(EventPlayerHurt @event)
    {
        var victim = @event.Userid;
        if (victim != null && victim.IsValid)
        {
            _lastDamageTimeBySlot[victim.Slot] = Server.CurrentTime;
        }
    }

    // ==============================================================================
    // 1. Reação ao "Paredão de Utilitárias" (Brick Wall Pivot)
    // ==============================================================================
    public void CheckBrickWallOnEntryDeath(CCSPlayerController victim, CCSPlayerController? killer, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (_hasPivotedThisRound) return;
        if (plan.CurrentPhase != RoundPhase.Executing && !_pacingController.IsExecuting) return;

        // Se o execute começou há menos de 3.5 segundos e quem morreu é Entry Fragger ou quem abriu a fila
        float timeSinceExecute = Server.CurrentTime - _executeStartTime;
        bool isEarlyEntryDeath = timeSinceExecute >= 0.0f && timeSinceExecute <= 3.5f;

        var role = _roleManager.GetBotRole(victim);
        bool isEntry = role == BotRole.EntryFragger || role == BotRole.Rotator;

        if (isEarlyEntryDeath && isEntry)
        {
            TriggerBrickWallPivot(plan, trBots, "Entry Fragger eliminado sem trade na entrada do bomb");
        }
    }

    public void CheckBrickWallOnHeavyUtility(float utilX, float utilY, float utilZ, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (_hasPivotedThisRound) return;
        if (plan.CurrentPhase != RoundPhase.Executing && !_pacingController.IsExecuting) return;

        // Verifica se a granada caiu no chokepoint principal da invasão
        var cp = _mapProfileManager.FindChokepointAt(utilX, utilY, utilZ);
        if (cp == null) return;

        string currentSite = plan.TacticName.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
        if (cp.AssociatedBomb.Equals(currentSite, StringComparison.OrdinalIgnoreCase))
        {
            // Se houver 3 ou mais bots TRs no raio de impacto/bloqueio
            int trsNearBlock = trBots.Count(b => b.PawnIsAlive && b.PlayerPawn.Value?.AbsOrigin != null &&
                (b.PlayerPawn.Value.AbsOrigin - new Vector(utilX, utilY, utilZ)).Length() <= 650.0f);

            if (trsNearBlock >= 2)
            {
                TriggerBrickWallPivot(plan, trBots, $"Paredão de utilitárias bloqueando entrada do Bomb {currentSite}");
            }
        }
    }

    private void TriggerBrickWallPivot(TacticalPlan plan, List<CCSPlayerController> trBots, string reason)
    {
        if (_hasPivotedThisRound) return;
        _hasPivotedThisRound = true;

        var aliveTrs = trBots.Where(b => b.PawnIsAlive).ToList();
        if (aliveTrs.Count == 0) return;

        var iglBot = aliveTrs.FirstOrDefault();
        string iglName = iglBot?.PlayerName ?? "IGL";
        string currentSite = plan.TacticName.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
        string otherSite = currentSite == "A" ? "B" : "A";

        int roll = _random.Next(100);

        // 60% HOLD_AND_RE_EXECUTE (Congelar e Repicar)
        if (roll < 60)
        {
            ExecuteHoldAndReExecute(iglBot, iglName, plan, aliveTrs, currentSite);
        }
        // 34% RESET_TO_DEFAULT (Recuar e Buscar Pick)
        else if (roll < 94)
        {
            ExecuteResetToDefault(iglBot, iglName, plan, aliveTrs, currentSite);
        }
        // 6% HARD_PIVOT_SILENT (Giro Surpresa)
        else
        {
            ExecuteHardPivotSilent(iglBot, iglName, plan, aliveTrs, otherSite);
        }
    }

    private void ExecuteHoldAndReExecute(CCSPlayerController? iglBot, string iglName, TacticalPlan plan, List<CCSPlayerController> aliveTrs, string currentSite)
    {
        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            "Muitas granadas! Segura no safe, marca avanço e espera a fumaça abrir pra repicar!",
            "holdpos");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR", $"Brick Wall em Bomb {currentSite}: HOLD_AND_RE_EXECUTE (60%). Time recuando para Staging e segurando por 16s.");

        foreach (var bot in aliveTrs)
        {
            var role = _roleManager.GetBotRole(bot);
            if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
            {
                order.Stance = EngagementStance.PASSIVE_HOLD;
                var stagingSpot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                if (stagingSpot != null)
                {
                    _locomotionDriver.NavigateToSpot(bot, stagingSpot, hurry: false, EngagementStance.PASSIVE_HOLD);
                }
            }
        }

        // Aguarda 16s (fumaças dissiparem) e repete o avanço
        _plugin.AddTimer(16.0f, () =>
        {
            var currentAlive = aliveTrs.Where(b => b.IsValid && b.PawnIsAlive).ToList();
            if (currentAlive.Count > 0 && !plan.IsTacticalSaveActive)
            {
                var speaker = currentAlive.FirstOrDefault();
                UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                    speaker,
                    CsTeam.Terrorist,
                    speaker?.PlayerName ?? "IGL",
                    "Fumaça abriu! Bora repicar o bomb agora, avanço total!",
                    "go");
                _pacingController.TriggerExecute("Repique coordenado pós-utilitárias", currentAlive);
            }
        });
    }

    private void ExecuteResetToDefault(CCSPlayerController? iglBot, string iglName, TacticalPlan plan, List<CCSPlayerController> aliveTrs, string currentSite)
    {
        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            "O bomb tá intransponível, recua geral e vamo jogar padrão buscando kill solto!",
            "fallback");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR", $"Brick Wall em Bomb {currentSite}: RESET_TO_DEFAULT (34%). Abortando execute e espalhando em rotas padrão.");

        plan.CurrentPhase = RoundPhase.Staging;
        plan.RoundTempo = RoundTempo.SLOW_DEFAULT;

        // Espalha os bots pelas posições neutras de Default (Meio, Caverna, Tapete)
        string[] neutralSectors = { "Meio", "Caverna", "Tapete", "Palácio" };
        int idx = 0;
        foreach (var bot in aliveTrs)
        {
            string sec = neutralSectors[idx % neutralSectors.Length];
            idx++;
            var spot = _mapProfileManager.GetSpotsForSector(sec, "TR").FirstOrDefault() ??
                       _mapProfileManager.GetSpotsForSector("Bombsite A", "TR").FirstOrDefault();
            if (spot != null)
            {
                _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, EngagementStance.JIGGLE_INFO);
            }
        }
    }

    private void ExecuteHardPivotSilent(CCSPlayerController? iglBot, string iglName, TacticalPlan plan, List<CCSPlayerController> aliveTrs, string otherSite)
    {
        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            $"Esquece esse bomb! Vira tudo pro Bomb {otherSite} no Shift!",
            "go");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR", $"Brick Wall: HARD_PIVOT_SILENT (6%). Giro surpresa total no Shift para Bomb {otherSite}.");

        string targetSector = otherSite == "B" ? "Bombsite B" : "Bombsite A";
        foreach (var bot in aliveTrs)
        {
            _midRoundAdapter.ApplyAction(bot, MidRoundAction.ROTATE_SILENT, targetSector);
        }
    }

    // ==============================================================================
    // 2. Oportunismo do Lurker (Site Clearance Call)
    // ==============================================================================
    public void CheckLurkerSiteClearance(CCSPlayerController killer, CCSPlayerController victim, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (killer.Team != CsTeam.Terrorist || victim.Team != CsTeam.CounterTerrorist) return;

        var role = _roleManager.GetBotRole(killer);
        bool isLurker = role == BotRole.Anchor || role == BotRole.Rotator;

        var killerPawn = killer.PlayerPawn.Value;
        if (killerPawn?.AbsOrigin == null) return;

        var cp = _mapProfileManager.FindChokepointAt(killerPawn.AbsOrigin.X, killerPawn.AbsOrigin.Y, killerPawn.AbsOrigin.Z);
        string bombKilledIn = cp?.AssociatedBomb ?? "";

        // Se abate ocorreu dentro ou colado em um bombsite (A ou B)
        if (bombKilledIn == "A" || bombKilledIn == "B")
        {
            string currentPlanSite = plan.TacticName.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";

            // Se o abate foi no bomb OPOSTO ao destino atual da C4 (oportunismo puro!)
            if (!bombKilledIn.Equals(currentPlanSite, StringComparison.OrdinalIgnoreCase) || isLurker)
            {
                _pendingLurkerChecks[killer.Slot] = (Server.CurrentTime, bombKilledIn, new Vector(killerPawn.AbsOrigin.X, killerPawn.AbsOrigin.Y, killerPawn.AbsOrigin.Z));

                // Validação de Limpeza (Clearance Check de 2.5s)
                _plugin.AddTimer(2.5f, () =>
                {
                    ValidateLurkerClearance(killer, bombKilledIn, plan, trBots);
                });
            }
        }
    }

    private void ValidateLurkerClearance(CCSPlayerController lurker, string clearedBomb, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (!lurker.IsValid || !lurker.PawnIsAlive || lurker.PlayerPawn.Value?.AbsOrigin == null) return;

        float now = Server.CurrentTime;

        // Se tomou dano nos últimos 2.5s, não está limpo
        if (_lastDamageTimeBySlot.TryGetValue(lurker.Slot, out float lastDmg) && now - lastDmg < 2.5f)
        {
            return;
        }

        var lurkerPos = lurker.PlayerPawn.Value.AbsOrigin;
        var allPlayers = Utilities.GetPlayers();

        // Checa se há CTs vivos no raio do bomb (raio <= 800u)
        bool hasEnemyNear = allPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist)
            .Any(p => p.PlayerPawn.Value?.AbsOrigin != null &&
                      (p.PlayerPawn.Value.AbsOrigin - lurkerPos).Length() <= 800.0f);

        if (hasEnemyNear) return;

        // Bomb oficialmente limpo pelo Lurker!
        _hasPivotedThisRound = true;

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            lurker,
            CsTeam.Terrorist,
            lurker.PlayerName,
            $"Limpei o Bomb {clearedBomb} e tá livre! Traz a C4 rápido, tô marcando a rotação!",
            "sectorclear");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR", $"Lurker ({lurker.PlayerName}) limpou Bomb {clearedBomb}. Time TR abortando plano anterior e convergindo com a C4 para Bomb {clearedBomb}.");

        // Lurker crava mira na rota de Retake dos CTs
        var retakeHoldSpot = _mapProfileManager.GetSpotById(clearedBomb == "B" ? "mirage_b_cat_sniper" : "mirage_a_ticket_sniper") ??
                             _mapProfileManager.GetSpotsForSector(clearedBomb == "B" ? "Bombsite B" : "Bombsite A", "TR").FirstOrDefault();
        if (retakeHoldSpot != null)
        {
            _locomotionDriver.NavigateToSpot(lurker, retakeHoldSpot, hurry: false, EngagementStance.PASSIVE_HOLD);
        }

        // Equipe TR inteira (e C4) converge para o bomb limpo
        string targetSector = clearedBomb == "B" ? "Bombsite B" : "Bombsite A";
        foreach (var bot in trBots.Where(b => b.PawnIsAlive && b.Slot != lurker.Slot))
        {
            _locomotionDriver.HoldPosition(bot, 0.2f);
            _midRoundAdapter.ApplyAction(bot, MidRoundAction.RUSH_TRADE, targetSector);
        }
    }

    // ==============================================================================
    // 3. Conversão de Pick em Execução (Mid-Round Exploit)
    // ==============================================================================
    public void CheckMidRoundExploitPick(CCSPlayerController killer, CCSPlayerController victim, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (_hasTriggeredFirstKillExploit) return;
        if (killer.Team != CsTeam.Terrorist || victim.Team != CsTeam.CounterTerrorist) return;

        // Verifica se é rodada lenta (SLOW_DEFAULT ou Staging)
        if (plan.RoundTempo != RoundTempo.SLOW_DEFAULT && plan.CurrentPhase != RoundPhase.Staging) return;

        // Verifica se é o First Kill do round (vantagem numérica 5v4)
        var allPlayers = Utilities.GetPlayers();
        int deadCts = allPlayers.Count(p => p != null && p.IsValid && !p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist);
        if (deadCts != 1) return; // Só ativa exatamente no First Kill

        _hasTriggeredFirstKillExploit = true;

        // Identifica o setor da morte
        Vector? victimPos = victim.PlayerPawn.Value?.AbsOrigin;
        string sectorName = "o Meio";
        string targetBomb = "A";

        if (victimPos != null)
        {
            var cp = _mapProfileManager.FindChokepointAt(victimPos.X, victimPos.Y, victimPos.Z);
            if (cp != null)
            {
                sectorName = cp.Name;
                targetBomb = cp.AssociatedBomb == "B" ? "B" : "A";
            }
        }

        var aliveTrs = trBots.Where(b => b.PawnIsAlive).ToList();
        var iglBot = aliveTrs.FirstOrDefault();
        string iglName = iglBot?.PlayerName ?? "IGL";

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            $"Abrimos vantagem no {sectorName}! Junta todo mundo e Executa Bomb {targetBomb} agora!",
            "go");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR", $"First Kill conquistado no setor {sectorName} por {killer.PlayerName}. Transição imediata de DEFAULT para EXECUTE no Bomb {targetBomb}.");

        // Transição imediata para Execute
        _pacingController.TriggerExecute($"Pick de abertura no {sectorName}", aliveTrs);
    }
}
