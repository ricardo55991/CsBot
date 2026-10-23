using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class BombsiteClearanceEvaluation
{
    public bool IsCleared { get; init; }
    public string RejectionReason { get; init; } = "NONE";
    public string ClaimantSector { get; init; } = string.Empty;
    public string TargetBombSite { get; init; } = string.Empty;
    public bool InsidePlantPerimeter { get; init; }
    public float DwellSeconds { get; init; }
    public float TimeSinceLastDamageSeconds { get; init; }
    public int NearbyEnemiesCount { get; init; }
    public float Confidence { get; init; }
}

public sealed class PivotDecisionContext
{
    public string KillerName { get; init; } = string.Empty;
    public string KillerSector { get; init; } = string.Empty;
    public string VictimName { get; init; } = string.Empty;
    public string VictimSector { get; init; } = string.Empty;
    public string BombCarrierName { get; init; } = string.Empty;
    public string BombCarrierSector { get; init; } = string.Empty;
    public float DistanceC4ToSiteA2D { get; init; }
    public float DistanceC4ToSiteB2D { get; init; }
    public int AliveTrCount { get; init; }
    public int AliveCtCount { get; init; }
    public float RoundTimeRemaining { get; init; }
    public string PreviousTargetSite { get; init; } = "A";
    public string SelectedTargetSite { get; init; } = "A";
    public string SelectedTacticName { get; init; } = string.Empty;
    public float Confidence { get; init; }
}

public class TrMacroPivotController
{
    private readonly CsBotManagerPlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly MidRoundAdapter _midRoundAdapter;
    private readonly PacingAndFallbackController _pacingController;
    private readonly BotLocomotionDriver _locomotionDriver;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }
    public BotSystemConfig Config { get; set; } = BotSystemConfig.Default;

    private readonly Random _random = new();

    private bool _hasPivotedThisRound = false;
    public bool HasPivotedThisRound => _hasPivotedThisRound;
    private float _executeStartTime = -100.0f;
    private bool _hasTriggeredFirstKillExploit = false;

    private readonly Dictionary<int, (float KillTime, string Bombsite, Vector KillPos)> _pendingLurkerChecks = new();
    private readonly Dictionary<int, float> _lastDamageTimeBySlot = new();

    private static readonly Vector BombACenter = new(-1160.0f, -2150.0f, -168.0f);
    private static readonly Vector BombBCenter = new(-1750.0f, 380.0f, -160.0f);

    public TrMacroPivotController(
        CsBotManagerPlugin plugin,
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

    /// <summary>
    /// Avalia de forma pura e determinística se um bot pode declarar `SITE CLEAR` em um Bombsite (Bug 6).
    /// Exige que o bot esteja fisicamente dentro do perímetro real de plant do Bombsite,
    /// sem inimigos próximos, com tempo de permanência >= `BombsiteClearMinDwellSeconds` (`2.0s`)
    /// e sem sofrer dano nos últimos `BombsiteClearNoDamageWindowSeconds` (`3.0s`).
    /// </summary>
    public static BombsiteClearanceEvaluation EvaluateSiteClearance(
        float botX,
        float botY,
        float botZ,
        string? nativeLastPlaceName,
        bool inBombZoneFlag,
        string claimedBombSite,
        float dwellSeconds,
        float timeSinceLastDamageSeconds,
        int nearbyEnemiesCount,
        BotSystemConfig? config = null)
    {
        var cfg = config ?? BotSystemConfig.Default;
        var sectorInfo = MirageSectorClassifier.Classify(botX, botY, botZ, nativeLastPlaceName, inBombZoneFlag);
        bool insidePlantPerimeter = MirageSectorClassifier.IsInsideBombsitePlantPerimeter(botX, botY, botZ, claimedBombSite, inBombZoneFlag);

        if (!insidePlantPerimeter)
        {
            return new BombsiteClearanceEvaluation
            {
                IsCleared = false,
                RejectionReason = $"OUTSIDE_PLANT_PERIMETER(current_sector={sectorInfo.SectorName},claimed={claimedBombSite})",
                ClaimantSector = sectorInfo.SectorName,
                TargetBombSite = claimedBombSite,
                InsidePlantPerimeter = false,
                DwellSeconds = dwellSeconds,
                TimeSinceLastDamageSeconds = timeSinceLastDamageSeconds,
                NearbyEnemiesCount = nearbyEnemiesCount,
                Confidence = 0.0f
            };
        }

        if (nearbyEnemiesCount > 0)
        {
            return new BombsiteClearanceEvaluation
            {
                IsCleared = false,
                RejectionReason = $"ENEMIES_PRESENT_IN_SITE({nearbyEnemiesCount})",
                ClaimantSector = sectorInfo.SectorName,
                TargetBombSite = claimedBombSite,
                InsidePlantPerimeter = true,
                DwellSeconds = dwellSeconds,
                TimeSinceLastDamageSeconds = timeSinceLastDamageSeconds,
                NearbyEnemiesCount = nearbyEnemiesCount,
                Confidence = 0.1f
            };
        }

        if (dwellSeconds < cfg.BombsiteClearMinDwellSeconds)
        {
            return new BombsiteClearanceEvaluation
            {
                IsCleared = false,
                RejectionReason = $"INSUFFICIENT_DWELL_TIME({dwellSeconds:F2}s<{cfg.BombsiteClearMinDwellSeconds:F2}s)",
                ClaimantSector = sectorInfo.SectorName,
                TargetBombSite = claimedBombSite,
                InsidePlantPerimeter = true,
                DwellSeconds = dwellSeconds,
                TimeSinceLastDamageSeconds = timeSinceLastDamageSeconds,
                NearbyEnemiesCount = 0,
                Confidence = 0.45f
            };
        }

        if (timeSinceLastDamageSeconds < cfg.BombsiteClearNoDamageWindowSeconds)
        {
            return new BombsiteClearanceEvaluation
            {
                IsCleared = false,
                RejectionReason = $"RECENT_DAMAGE({timeSinceLastDamageSeconds:F2}s<{cfg.BombsiteClearNoDamageWindowSeconds:F2}s)",
                ClaimantSector = sectorInfo.SectorName,
                TargetBombSite = claimedBombSite,
                InsidePlantPerimeter = true,
                DwellSeconds = dwellSeconds,
                TimeSinceLastDamageSeconds = timeSinceLastDamageSeconds,
                NearbyEnemiesCount = 0,
                Confidence = 0.50f
            };
        }

        float confidence = Math.Clamp(0.75f + Math.Min(0.20f, (dwellSeconds - cfg.BombsiteClearMinDwellSeconds) * 0.08f), 0.75f, 0.98f);
        return new BombsiteClearanceEvaluation
        {
            IsCleared = confidence >= cfg.BombsiteClearMinConfidence,
            RejectionReason = "NONE",
            ClaimantSector = sectorInfo.SectorName,
            TargetBombSite = claimedBombSite,
            InsidePlantPerimeter = true,
            DwellSeconds = dwellSeconds,
            TimeSinceLastDamageSeconds = timeSinceLastDamageSeconds,
            NearbyEnemiesCount = 0,
            Confidence = confidence
        };
    }

    /// <summary>
    /// Resolve de forma pura e determinística qual Bombsite ("A" ou "B") deve ser o alvo de um pivô por First Kill,
    /// sem nenhum valor hardcoded `"o Meio"` ou `"A"`, considerando o setor real da vítima, do killer e a posição da C4 (Bug 6).
    /// </summary>
    public static PivotDecisionContext ResolveFirstKillExploitContext(
        string killerName,
        float killerX, float killerY, float killerZ, string? killerNativePlace,
        string victimName,
        float victimX, float victimY, float victimZ, string? victimNativePlace,
        string bombCarrierName,
        float c4X, float c4Y, float c4Z, string? c4NativePlace,
        int aliveTrCount,
        int aliveCtCount,
        float roundTimeRemaining,
        string currentTargetSite)
    {
        var killerSec = MirageSectorClassifier.Classify(killerX, killerY, killerZ, killerNativePlace);
        var victimSec = MirageSectorClassifier.Classify(victimX, victimY, victimZ, victimNativePlace);
        var c4Sec = MirageSectorClassifier.Classify(c4X, c4Y, c4Z, c4NativePlace);

        float distToA = MathF.Sqrt((c4X - BombACenter.X) * (c4X - BombACenter.X) + (c4Y - BombACenter.Y) * (c4Y - BombACenter.Y));
        float distToB = MathF.Sqrt((c4X - BombBCenter.X) * (c4X - BombBCenter.X) + (c4Y - BombBCenter.Y) * (c4Y - BombBCenter.Y));

        string selectedSite;
        if (victimSec.AssociatedBomb == "A" || victimSec.AssociatedBomb == "B")
        {
            selectedSite = victimSec.AssociatedBomb;
        }
        else if (killerSec.AssociatedBomb == "A" || killerSec.AssociatedBomb == "B")
        {
            selectedSite = killerSec.AssociatedBomb;
        }
        else if (victimSec.SectorName.Contains("Catwalk", StringComparison.OrdinalIgnoreCase) ||
                 victimSec.SectorName.Contains("Underpass", StringComparison.OrdinalIgnoreCase))
        {
            selectedSite = "B";
        }
        else if (victimSec.SectorName.Contains("Conector", StringComparison.OrdinalIgnoreCase) ||
                 victimSec.SectorName.Contains("Janela", StringComparison.OrdinalIgnoreCase))
        {
            selectedSite = distToB < distToA * 0.85f ? "B" : "A";
        }
        else
        {
            selectedSite = distToB < distToA ? "B" : "A";
        }

        string newTacticName = selectedSite == "B"
            ? $"Exploit 5v4 -> Execução Bomb B (Pick em {victimSec.SectorName})"
            : $"Exploit 5v4 -> Execução Bomb A (Pick em {victimSec.SectorName})";

        return new PivotDecisionContext
        {
            KillerName = killerName,
            KillerSector = killerSec.SectorName,
            VictimName = victimName,
            VictimSector = victimSec.SectorName,
            BombCarrierName = bombCarrierName,
            BombCarrierSector = c4Sec.SectorName,
            DistanceC4ToSiteA2D = distToA,
            DistanceC4ToSiteB2D = distToB,
            AliveTrCount = aliveTrCount,
            AliveCtCount = aliveCtCount,
            RoundTimeRemaining = roundTimeRemaining,
            PreviousTargetSite = string.IsNullOrEmpty(currentTargetSite) ? "A" : currentTargetSite,
            SelectedTargetSite = selectedSite,
            SelectedTacticName = newTacticName,
            Confidence = 0.88f
        };
    }

    public void CheckBrickWallOnEntryDeath(CCSPlayerController victim, CCSPlayerController? killer, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (_hasPivotedThisRound) return;
        if (plan.CurrentPhase != RoundPhase.Executing && !_pacingController.IsExecuting) return;

        float timeSinceExecute = Server.CurrentTime - _executeStartTime;
        bool isEarlyEntryDeath = timeSinceExecute >= 0.0f && timeSinceExecute <= 3.5f;

        var role = _roleManager.GetBotRole(victim);
        bool isEntry = role == BotRole.EntryFragger || role == BotRole.Rotator;

        if (isEarlyEntryDeath && isEntry)
        {
            var victimSec = MirageSectorClassifier.ClassifyPlayer(victim);
            TriggerBrickWallPivot(plan, trBots, $"Entry Fragger ({victim.PlayerName}) eliminado sem trade em {victimSec.SectorName}", "EntryDeathNoTrade");
        }
    }

    public void CheckBrickWallOnHeavyUtility(float utilX, float utilY, float utilZ, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (_hasPivotedThisRound) return;
        if (plan.CurrentPhase != RoundPhase.Executing && !_pacingController.IsExecuting) return;

        var utilSec = MirageSectorClassifier.Classify(utilX, utilY, utilZ);
        string currentSite = plan.CurrentTargetSite;
        if (string.IsNullOrEmpty(currentSite))
        {
            currentSite = plan.TacticName.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
        }

        if (utilSec.AssociatedBomb.Equals(currentSite, StringComparison.OrdinalIgnoreCase))
        {
            int trsNearBlock = trBots.Count(b => b.PawnIsAlive && b.PlayerPawn.Value?.AbsOrigin != null &&
                (b.PlayerPawn.Value.AbsOrigin - new Vector(utilX, utilY, utilZ)).Length() <= 650.0f);

            if (trsNearBlock >= 2)
            {
                TriggerBrickWallPivot(plan, trBots, $"Paredão de utilitárias em {utilSec.SectorName} bloqueando Bomb {currentSite}", "HeavyUtilityBlock");
            }
        }
    }

    private void TriggerBrickWallPivot(TacticalPlan plan, List<CCSPlayerController> trBots, string reason, string triggerEvent)
    {
        if (_hasPivotedThisRound) return;
        _hasPivotedThisRound = true;

        var aliveTrs = trBots.Where(b => b.PawnIsAlive).ToList();
        if (aliveTrs.Count == 0) return;

        var iglBot = aliveTrs.FirstOrDefault();
        string iglName = iglBot?.PlayerName ?? "IGL";
        string currentSite = !string.IsNullOrEmpty(plan.CurrentTargetSite)
            ? plan.CurrentTargetSite
            : (plan.TacticName.Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A");
        string otherSite = currentSite == "A" ? "B" : "A";

        int roll = _random.Next(100);
        if (roll < 60)
        {
            ExecuteHoldAndReExecute(iglBot, iglName, plan, aliveTrs, currentSite, reason, triggerEvent);
        }
        else if (roll < 94)
        {
            ExecuteResetToDefault(iglBot, iglName, plan, aliveTrs, currentSite, reason, triggerEvent);
        }
        else
        {
            ExecuteHardPivotSilent(iglBot, iglName, plan, aliveTrs, otherSite, reason, triggerEvent);
        }
    }

    private void ExecuteHoldAndReExecute(
        CCSPlayerController? iglBot,
        string iglName,
        TacticalPlan plan,
        List<CCSPlayerController> aliveTrs,
        string currentSite,
        string reason,
        string triggerEvent)
    {
        string newTactic = $"Hold & Re-Execute Bomb {currentSite}";
        plan.ApplyPivotRevision(
            newTacticName: newTactic,
            newTargetSite: currentSite,
            changeReason: reason,
            triggeringEvent: triggerEvent,
            gameTick: Server.TickCount,
            roundTime: TelemetryLogger?.GetRoundClockFormatted() ?? "01:00",
            confidence: 0.80f);

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            "Muitas granadas! Segura no safe, marca avanço e espera a fumaça abrir pra repicar!",
            "holdpos");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR",
            $"Brick Wall em Bomb {currentSite}: `HOLD_AND_RE_EXECUTE` | `rev={plan.TacticRevision}` | `initial={plan.InitialTactic}` -> `current={plan.CurrentTactic}` | `motivo={reason}`.");

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

        _plugin.AddRoundTimer(16.0f, () =>
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

    private void ExecuteResetToDefault(
        CCSPlayerController? iglBot,
        string iglName,
        TacticalPlan plan,
        List<CCSPlayerController> aliveTrs,
        string currentSite,
        string reason,
        string triggerEvent)
    {
        string newTactic = $"Reset Default & Pick (Ex-Bomb {currentSite})";
        plan.ApplyPivotRevision(
            newTacticName: newTactic,
            newTargetSite: currentSite,
            changeReason: reason,
            triggeringEvent: triggerEvent,
            gameTick: Server.TickCount,
            roundTime: TelemetryLogger?.GetRoundClockFormatted() ?? "01:00",
            confidence: 0.78f);

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            "O bomb tá intransponível, recua geral e vamo jogar padrão buscando kill solto!",
            "fallback");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR",
            $"Brick Wall em Bomb {currentSite}: `RESET_TO_DEFAULT` | `rev={plan.TacticRevision}` | `initial={plan.InitialTactic}` -> `current={plan.CurrentTactic}` | `motivo={reason}`.");

        plan.CurrentPhase = RoundPhase.Staging;
        plan.RoundTempo = RoundTempo.SLOW_DEFAULT;

        string[] neutralSectors = { "Mid", "Bombsite A", "Bombsite B" };
        int idx = 0;
        foreach (var bot in aliveTrs)
        {
            string sec = neutralSectors[idx % neutralSectors.Length];
            idx++;
            var spot = _mapProfileManager.GetSpotsForSector(sec, "TR").FirstOrDefault();
            if (spot != null)
            {
                _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, EngagementStance.JIGGLE_INFO);
            }
        }
    }

    private void ExecuteHardPivotSilent(
        CCSPlayerController? iglBot,
        string iglName,
        TacticalPlan plan,
        List<CCSPlayerController> aliveTrs,
        string otherSite,
        string reason,
        string triggerEvent)
    {
        string newTactic = $"Hard Pivot Silencioso -> Bomb {otherSite}";
        plan.ApplyPivotRevision(
            newTacticName: newTactic,
            newTargetSite: otherSite,
            changeReason: reason,
            triggeringEvent: triggerEvent,
            gameTick: Server.TickCount,
            roundTime: TelemetryLogger?.GetRoundClockFormatted() ?? "01:00",
            confidence: 0.85f);

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            $"Esquece esse bomb! Vira tudo pro Bomb {otherSite} no Shift!",
            "go");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR",
            $"Brick Wall: `HARD_PIVOT_SILENT` para Bomb {otherSite} | `rev={plan.TacticRevision}` | `initial={plan.InitialTactic}` -> `current={plan.CurrentTactic}` | `motivo={reason}`.");

        string targetSector = otherSite == "B" ? "Bombsite B" : "Bombsite A";
        foreach (var bot in aliveTrs)
        {
            _midRoundAdapter.ApplyAction(bot, MidRoundAction.ROTATE_SILENT, targetSector);
        }
    }

    // ==============================================================================
    // 2. Oportunismo do Lurker com Validação Real de Bombsite (Bug 6)
    // ==============================================================================
    public void CheckLurkerSiteClearance(CCSPlayerController killer, CCSPlayerController victim, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (killer.Team != CsTeam.Terrorist || victim.Team != CsTeam.CounterTerrorist) return;

        var killerPawn = killer.PlayerPawn.Value;
        if (killerPawn?.AbsOrigin == null) return;

        string? placeName = null;
        bool inBombZone = false;
        try { placeName = killerPawn.LastPlaceName; } catch { }
        try { inBombZone = killerPawn.InBombZone; } catch { }

        var killerSec = MirageSectorClassifier.Classify(
            killerPawn.AbsOrigin.X,
            killerPawn.AbsOrigin.Y,
            killerPawn.AbsOrigin.Z,
            placeName,
            inBombZone);

        // Só agenda verificação de "Bomb Limpo" se o killer estiver de fato no Bomb A ou Bomb B
        if (killerSec.AssociatedBomb == "A" || killerSec.AssociatedBomb == "B")
        {
            string bombCandidate = killerSec.AssociatedBomb;
            _pendingLurkerChecks[killer.Slot] = (
                Server.CurrentTime,
                bombCandidate,
                new Vector(killerPawn.AbsOrigin.X, killerPawn.AbsOrigin.Y, killerPawn.AbsOrigin.Z));

            float waitSeconds = Math.Max(2.2f, Config.BombsiteClearMinDwellSeconds + 0.2f);
            _plugin.AddRoundTimer(waitSeconds, () =>
            {
                ValidateLurkerClearance(killer, bombCandidate, plan, trBots);
            });
        }
    }

    private void ValidateLurkerClearance(CCSPlayerController lurker, string clearedBomb, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (!lurker.IsValid || !lurker.PawnIsAlive || lurker.PlayerPawn.Value?.AbsOrigin == null) return;
        if (!_pendingLurkerChecks.TryGetValue(lurker.Slot, out var checkInfo)) return;

        float now = Server.CurrentTime;
        float dwellSeconds = now - checkInfo.KillTime;
        float lastDmg = _lastDamageTimeBySlot.GetValueOrDefault(lurker.Slot, -100.0f);
        float timeSinceDamage = now - lastDmg;

        var lurkerPawn = lurker.PlayerPawn.Value;
        var lurkerPos = lurkerPawn.AbsOrigin!;
        string? nativePlace = null;
        bool inBombZone = false;
        try { nativePlace = lurkerPawn.LastPlaceName; } catch { }
        try { inBombZone = lurkerPawn.InBombZone; } catch { }

        var allPlayers = Utilities.GetPlayers();
        int nearbyEnemies = allPlayers
            .Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist &&
                        p.PlayerPawn.Value?.AbsOrigin != null &&
                        (p.PlayerPawn.Value.AbsOrigin - lurkerPos).Length() <= 800.0f);

        var eval = EvaluateSiteClearance(
            botX: lurkerPos.X,
            botY: lurkerPos.Y,
            botZ: lurkerPos.Z,
            nativeLastPlaceName: nativePlace,
            inBombZoneFlag: inBombZone,
            claimedBombSite: clearedBomb,
            dwellSeconds: dwellSeconds,
            timeSinceLastDamageSeconds: timeSinceDamage,
            nearbyEnemiesCount: nearbyEnemies,
            config: Config);

        if (!eval.IsCleared)
        {
            TelemetryLogger?.LogEvent("PIVOT TÁTICO TR - REJEITADO",
                $"Declaração de `SITE CLEAR` em `Bomb {clearedBomb}` por **{lurker.PlayerName}** rejeitada: `{eval.RejectionReason}` (`setor_atual={eval.ClaimantSector}`, `dwell={eval.DwellSeconds:F1}s`, `inimigos_proximos={eval.NearbyEnemiesCount}`).");
            return;
        }

        _hasPivotedThisRound = true;
        string newTactic = $"Convergência C4 -> Bomb {clearedBomb} Limpo por {lurker.PlayerName}";
        plan.ApplyPivotRevision(
            newTacticName: newTactic,
            newTargetSite: clearedBomb,
            changeReason: $"Lurker {lurker.PlayerName} confirmed Bomb {clearedBomb} clear (dwell={eval.DwellSeconds:F1}s, conf={eval.Confidence:F2})",
            triggeringEvent: "LurkerSiteClearance",
            gameTick: Server.TickCount,
            roundTime: TelemetryLogger?.GetRoundClockFormatted() ?? "01:00",
            confidence: eval.Confidence);

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            lurker,
            CsTeam.Terrorist,
            lurker.PlayerName,
            $"Limpei o Bomb {clearedBomb} ({eval.ClaimantSector}) e tá livre! Traz a C4 rápido, tô marcando a rotação!",
            "sectorclear");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR",
            $"Lurker (**{lurker.PlayerName}**, setor=`{eval.ClaimantSector}`, `in_plant_zone={eval.InsidePlantPerimeter}`, `dwell={eval.DwellSeconds:F1}s`, `conf={eval.Confidence:F2}`) confirmou **Bomb {clearedBomb} limpo** | `rev={plan.TacticRevision}` | `initial={plan.InitialTactic}` -> `current={plan.CurrentTactic}`.");

        var retakeHoldSpot = _mapProfileManager.GetSpotsForSector(clearedBomb == "B" ? "Bombsite B" : "Bombsite A", "TR").FirstOrDefault();
        if (retakeHoldSpot != null)
        {
            _locomotionDriver.NavigateToSpot(lurker, retakeHoldSpot, hurry: false, EngagementStance.PASSIVE_HOLD);
        }

        string targetSector = clearedBomb == "B" ? "Bombsite B" : "Bombsite A";
        foreach (var bot in trBots.Where(b => b.PawnIsAlive && b.Slot != lurker.Slot))
        {
            _locomotionDriver.HoldPosition(bot, 0.15f);
            _midRoundAdapter.ApplyAction(bot, MidRoundAction.RUSH_TRADE, targetSector);
        }
    }

    // ==============================================================================
    // 3. Conversão de Pick em Execução Sem Hardcode (Bug 6)
    // ==============================================================================
    public void CheckMidRoundExploitPick(CCSPlayerController killer, CCSPlayerController victim, TacticalPlan plan, List<CCSPlayerController> trBots)
    {
        if (_hasTriggeredFirstKillExploit) return;
        if (killer.Team != CsTeam.Terrorist || victim.Team != CsTeam.CounterTerrorist) return;

        if (plan.RoundTempo != RoundTempo.SLOW_DEFAULT && plan.CurrentPhase != RoundPhase.Staging) return;

        var allPlayers = Utilities.GetPlayers();
        int deadCts = allPlayers.Count(p => p != null && p.IsValid && !p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist);
        if (deadCts != 1) return;

        _hasTriggeredFirstKillExploit = true;

        var killerPawn = killer.PlayerPawn.Value;
        var victimPawn = victim.PlayerPawn.Value;
        if (killerPawn?.AbsOrigin == null || victimPawn?.AbsOrigin == null) return;

        var aliveTrs = trBots.Where(b => b.PawnIsAlive).ToList();
        var aliveCts = allPlayers.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist);
        var c4Carrier = aliveTrs.FirstOrDefault(b => BotLocomotionDriver.HasC4(b)) ?? killer;
        var c4Origin = c4Carrier.PlayerPawn.Value?.AbsOrigin ?? killerPawn.AbsOrigin;

        string? killerPlace = null, victimPlace = null, c4Place = null;
        try { killerPlace = killerPawn.LastPlaceName; } catch { }
        try { victimPlace = victimPawn.LastPlaceName; } catch { }
        try { c4Place = c4Carrier.PlayerPawn.Value?.LastPlaceName; } catch { }

        var ctx = ResolveFirstKillExploitContext(
            killerName: killer.PlayerName,
            killerX: killerPawn.AbsOrigin.X, killerY: killerPawn.AbsOrigin.Y, killerZ: killerPawn.AbsOrigin.Z, killerNativePlace: killerPlace,
            victimName: victim.PlayerName,
            victimX: victimPawn.AbsOrigin.X, victimY: victimPawn.AbsOrigin.Y, victimZ: victimPawn.AbsOrigin.Z, victimNativePlace: victimPlace,
            bombCarrierName: c4Carrier.PlayerName,
            c4X: c4Origin.X, c4Y: c4Origin.Y, c4Z: c4Origin.Z, c4NativePlace: c4Place,
            aliveTrCount: aliveTrs.Count,
            aliveCtCount: aliveCts,
            roundTimeRemaining: _locomotionDriver.RoundTimeRemaining,
            currentTargetSite: plan.CurrentTargetSite);

        plan.ApplyPivotRevision(
            newTacticName: ctx.SelectedTacticName,
            newTargetSite: ctx.SelectedTargetSite,
            changeReason: $"First Kill by {ctx.KillerName} ({ctx.KillerSector}) on {ctx.VictimName} ({ctx.VictimSector}); C4 with {ctx.BombCarrierName} in {ctx.BombCarrierSector}",
            triggeringEvent: "FirstKillMidRoundExploit",
            gameTick: Server.TickCount,
            roundTime: TelemetryLogger?.GetRoundClockFormatted() ?? "01:15",
            confidence: ctx.Confidence);

        var iglBot = aliveTrs.FirstOrDefault();
        string iglName = iglBot?.PlayerName ?? "IGL";

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            iglBot,
            CsTeam.Terrorist,
            iglName,
            $"First kill em {ctx.VictimSector}! C4 em {ctx.BombCarrierSector}, junta todo mundo e Executa Bomb {ctx.SelectedTargetSite} agora!",
            "go");

        TelemetryLogger?.LogEvent("PIVOT TÁTICO TR",
            $"First Kill conquistado por **{ctx.KillerName}** (`setor_killer={ctx.KillerSector}`) sobre **{ctx.VictimName}** (`setor_vitima={ctx.VictimSector}`) | C4: **{ctx.BombCarrierName}** (`setor_c4={ctx.BombCarrierSector}`, `distA={ctx.DistanceC4ToSiteA2D:F0}u`, `distB={ctx.DistanceC4ToSiteB2D:F0}u`) | Vivos: `{ctx.AliveTrCount}v{ctx.AliveCtCount}` | Transição imediata `rev={plan.TacticRevision}`: `{plan.InitialTactic}` -> `{plan.CurrentTactic}` (Alvo: **Bomb {ctx.SelectedTargetSite}**, `conf={ctx.Confidence:F2}`).");

        _pacingController.TriggerExecute($"Pick de abertura em {ctx.VictimSector} -> Bomb {ctx.SelectedTargetSite}", aliveTrs);
    }
}
