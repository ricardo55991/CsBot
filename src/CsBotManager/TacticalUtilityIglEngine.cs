using System.Diagnostics;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class UtilityScoreBreakdown
{
    public string TacticId { get; init; } = string.Empty;
    public string DisplayName { get; init; } = string.Empty;
    public double BaseScore { get; set; } = 50.0;
    public double EconomyAdjustment { get; set; }
    public double WeaponCompositionAdjustment { get; set; }
    public double EnemyEconomyAdjustment { get; set; }
    public double HistoryMindgameAdjustment { get; set; }
    public double WinMomentumAdjustment { get; set; }
    public double RepetitionPenalty { get; set; }
    public double FinalScore => Math.Clamp(
        BaseScore + EconomyAdjustment + WeaponCompositionAdjustment +
        EnemyEconomyAdjustment + HistoryMindgameAdjustment +
        WinMomentumAdjustment - RepetitionPenalty, 1.0, 100.0);
    public double SoftmaxProbability { get; set; }
    public List<string> Factors { get; } = new();

    public string FormatAuditSummary()
    {
        string reasons = Factors.Count > 0 ? string.Join(", ", Factors) : "Baseline";
        return $"{TacticId}={FinalScore:F1}pts (P={SoftmaxProbability:P0} | {reasons})";
    }
}

public sealed class CtTacticBlueprint
{
    public string TacticId { get; init; } = string.Empty;
    public string TacticName { get; init; } = string.Empty;
    public string TacticSummary { get; init; } = string.Empty;
    public RoundTempo Tempo { get; init; } = RoundTempo.SLOW_DEFAULT;
    public float StagingDuration { get; init; } = 18.0f;
    public CtDuoPlayType DuoPlay { get; init; } = CtDuoPlayType.None;
    public string FocusSector { get; init; } = "BALANCED"; // "BALANCED", "A", "B", "MID", "RETAKE"
    public bool IsEcoStackGamble { get; init; }
    public bool PrefersAwp { get; init; }
    public bool IsAntiEcoFriendly { get; init; }
    public List<CtFormationAssignment> Assignments { get; init; } = new();
}

public sealed class TrBotBlueprintOrder
{
    public string RoleKey { get; init; } = string.Empty;
    public string TargetArea { get; init; } = "Bombsite A";
    public string RoleAction { get; init; } = string.Empty;
    public string StagingSpotId { get; init; } = string.Empty;
    public string ExecuteSpotId { get; init; } = string.Empty;
    public string FallbackSpotId { get; init; } = "tr_spawn_safe";
    public EngagementStance Stance { get; init; } = EngagementStance.AGGRESSIVE_POKE;
    public List<string> RequiredUtilities { get; init; } = new();
    public bool IsNoiseGroup { get; init; }
}

public sealed class TrTacticBlueprint
{
    public string TacticId { get; init; } = string.Empty;
    public string TacticName { get; init; } = string.Empty;
    public string TacticSummary { get; init; } = string.Empty;
    public RoundTempo Tempo { get; init; } = RoundTempo.TIMED_EXECUTE;
    public float StagingDuration { get; init; } = 12.0f;
    public TrTacticType TacticType { get; init; } = TrTacticType.Default;
    public string TargetSite { get; init; } = "A"; // "A", "B", "Dynamic"
    public string? FakeSite { get; init; }
    public string? RealSite { get; init; }
    public bool IsFastCloseRange { get; init; }
    public bool IsSlowLongRange { get; init; }
    public bool IsSplitPlay { get; init; }
    public List<TrBotBlueprintOrder> Orders { get; init; } = new();
}

public sealed class TacticalUtilityIglEngine
{
    private readonly BotSystemConfig _config;
    private readonly Random _rng;
    private readonly List<RoundHistoryItem> _matchHistory = new();
    private readonly object _historyLock = new();

    private readonly Dictionary<string, IMapTacticalCatalog> _catalogsByMap = new(StringComparer.OrdinalIgnoreCase);
    private readonly IMapTacticalCatalog _defaultCatalog;

    public TacticalUtilityIglEngine(BotSystemConfig? config = null, int? seed = null)
    {
        _config = config ?? BotSystemConfig.Default;
        _rng = seed.HasValue ? new Random(seed.Value) : new Random();

        // Registra catálogos modulares por mapa (atualmente de_mirage; pronto para de_dust2, de_inferno, de_nuke, etc.)
        var mirageCatalog = new MirageTacticalCatalog();
        _defaultCatalog = mirageCatalog;
        RegisterMapCatalog(mirageCatalog);
    }

    public void RegisterMapCatalog(IMapTacticalCatalog catalog)
    {
        if (catalog == null || string.IsNullOrWhiteSpace(catalog.MapName)) return;
        _catalogsByMap[catalog.MapName.Trim()] = catalog;
    }

    public IMapTacticalCatalog GetCatalogForMap(string? mapName)
    {
        if (!string.IsNullOrWhiteSpace(mapName) && _catalogsByMap.TryGetValue(mapName.Trim(), out var catalog))
        {
            return catalog;
        }
        return _defaultCatalog;
    }

    public IReadOnlyList<CtTacticBlueprint> CtCatalog => _defaultCatalog.CtTactics;
    public IReadOnlyList<TrTacticBlueprint> TrCatalog => _defaultCatalog.TrTactics;

    public void ResetMatchMemory()
    {
        lock (_historyLock)
        {
            _matchHistory.Clear();
        }
    }

    public void RecordRoundOutcome(RoundHistoryItem item)
    {
        lock (_historyLock)
        {
            _matchHistory.Add(item);
            if (_matchHistory.Count > 12)
            {
                _matchHistory.RemoveAt(0);
            }
        }
    }

    public IReadOnlyList<RoundHistoryItem> GetRecentHistory(int maxCount = 4)
    {
        lock (_historyLock)
        {
            return _matchHistory.TakeLast(maxCount).ToList();
        }
    }

    /// <summary>
    /// Decide instantaneamente (< 0.05ms) os planos táticos de CT e TR no início do round.
    /// Zero chamadas HTTP, zero alocação pesada, 100% determinístico nos spots validados do mapa ativo.
    /// </summary>
    public (TacticalPlan CtPlan, TacticalPlan TrPlan) DecideRoundPlans(
        long internalRoundId,
        int displayRound,
        TeamEconomySnapshot ctEcon,
        TeamEconomySnapshot trEcon,
        List<CCSPlayerController>? ctBots,
        List<CCSPlayerController>? trBots,
        MapProfileManager? mapProfileManager,
        int currentTick,
        string? mapName = null)
    {
        string resolvedMap = mapName ?? mapProfileManager?.CurrentProfile?.MapName ?? "de_mirage";

        var swCt = Stopwatch.StartNew();
        var ctPlan = DecideTeamPlan(
            CsTeam.CounterTerrorist,
            internalRoundId,
            displayRound,
            ctEcon,
            trEcon,
            ctBots,
            mapProfileManager,
            currentTick,
            excludeTacticId: null,
            mapName: resolvedMap);
        swCt.Stop();
        ctPlan.LatencyMs = Math.Round(swCt.Elapsed.TotalMilliseconds, 4);

        var swTr = Stopwatch.StartNew();
        var trPlan = DecideTeamPlan(
            CsTeam.Terrorist,
            internalRoundId,
            displayRound,
            trEcon,
            ctEcon,
            trBots,
            mapProfileManager,
            currentTick,
            excludeTacticId: null,
            mapName: resolvedMap);
        swTr.Stop();
        trPlan.LatencyMs = Math.Round(swTr.Elapsed.TotalMilliseconds, 4);

        return (ctPlan, trPlan);
    }

    public TacticalPlan DecideTeamPlan(
        CsTeam team,
        long internalRoundId,
        int displayRound,
        TeamEconomySnapshot ownEcon,
        TeamEconomySnapshot enemyEcon,
        List<CCSPlayerController>? teamBots,
        MapProfileManager? mapProfileManager,
        int currentTick,
        string? excludeTacticId = null,
        string? mapName = null)
    {
        var sw = Stopwatch.StartNew();
        var recentHistory = GetRecentHistory(4);
        var catalog = GetCatalogForMap(mapName ?? mapProfileManager?.CurrentProfile?.MapName);

        if (team == CsTeam.CounterTerrorist)
        {
            var breakdowns = catalog.CtTactics
                .Where(bp => string.IsNullOrEmpty(excludeTacticId) || !bp.TacticId.Equals(excludeTacticId, StringComparison.OrdinalIgnoreCase))
                .Select(bp => ScoreCtTactic(bp, ownEcon, enemyEcon, recentHistory))
                .OrderByDescending(b => b.FinalScore)
                .ToList();

            var top3 = breakdowns.Take(3).ToList();
            var selectedBreakdown = SelectWithTemperatureSoftmax(top3, _config.UtilitySoftmaxTemperature);
            var selectedBlueprint = catalog.CtTactics.First(b => b.TacticId == selectedBreakdown.TacticId);

            var plan = MaterializeCtBlueprint(
                selectedBlueprint,
                internalRoundId,
                displayRound,
                teamBots,
                mapProfileManager,
                currentTick,
                TacticalDecisionSource.UTILITY_AI_ENGINE);

            PopulateAuditMetadata(plan, selectedBreakdown, top3, sw.Elapsed.TotalMilliseconds);
            return plan;
        }
        else
        {
            var breakdowns = catalog.TrTactics
                .Where(bp => string.IsNullOrEmpty(excludeTacticId) || !bp.TacticId.Equals(excludeTacticId, StringComparison.OrdinalIgnoreCase))
                .Select(bp => ScoreTrTactic(bp, ownEcon, enemyEcon, recentHistory))
                .OrderByDescending(b => b.FinalScore)
                .ToList();

            var top3 = breakdowns.Take(3).ToList();
            var selectedBreakdown = SelectWithTemperatureSoftmax(top3, _config.UtilitySoftmaxTemperature);
            var selectedBlueprint = catalog.TrTactics.First(b => b.TacticId == selectedBreakdown.TacticId);

            var plan = MaterializeTrBlueprint(
                selectedBlueprint,
                internalRoundId,
                displayRound,
                teamBots,
                mapProfileManager,
                currentTick,
                TacticalDecisionSource.UTILITY_AI_ENGINE);

            PopulateAuditMetadata(plan, selectedBreakdown, top3, sw.Elapsed.TotalMilliseconds);
            return plan;
        }
    }

    /// <summary>
    /// Materializa diretamente um plano pelo seu TacticId no catálogo do mapa ativo.
    /// </summary>
    public TacticalPlan? TryMaterializeById(
        CsTeam team,
        string tacticId,
        long internalRoundId,
        int displayRound,
        List<CCSPlayerController>? teamBots,
        MapProfileManager? mapProfileManager,
        int currentTick,
        TacticalDecisionSource source,
        double latencyMs = 0.01,
        string? mapName = null)
    {
        var catalog = GetCatalogForMap(mapName ?? mapProfileManager?.CurrentProfile?.MapName);

        if (team == CsTeam.CounterTerrorist)
        {
            var bp = catalog.CtTactics.FirstOrDefault(b => b.TacticId.Equals(tacticId, StringComparison.OrdinalIgnoreCase));
            if (bp == null) return null;
            var plan = MaterializeCtBlueprint(bp, internalRoundId, displayRound, teamBots, mapProfileManager, currentTick, source);
            plan.LatencyMs = Math.Round(latencyMs, 4);
            plan.IsCustomPlayerCall = true;
            plan.ParseStatus = "OK";
            plan.ModelResponseStatus = source.ToString();
            plan.FallbackUsed = false;
            plan.FallbackReason = "NONE";
            return plan;
        }
        else
        {
            var bp = catalog.TrTactics.FirstOrDefault(b => b.TacticId.Equals(tacticId, StringComparison.OrdinalIgnoreCase));
            if (bp == null) return null;
            var plan = MaterializeTrBlueprint(bp, internalRoundId, displayRound, teamBots, mapProfileManager, currentTick, source);
            plan.LatencyMs = Math.Round(latencyMs, 4);
            plan.IsCustomPlayerCall = true;
            plan.ParseStatus = "OK";
            plan.ModelResponseStatus = source.ToString();
            plan.FallbackUsed = false;
            plan.FallbackReason = "NONE";
            return plan;
        }
    }

    // =========================================================================
    // MOTOR DE PONTUAÇÃO DINÂMICA (UTILITY SCORE 0..100 + MEMÓRIA + ANTI-REPETIÇÃO)
    // =========================================================================

    public UtilityScoreBreakdown ScoreCtTactic(
        CtTacticBlueprint bp,
        TeamEconomySnapshot ctEcon,
        TeamEconomySnapshot trEcon,
        IReadOnlyList<RoundHistoryItem> recentHistory)
    {
        var score = new UtilityScoreBreakdown
        {
            TacticId = bp.TacticId,
            DisplayName = bp.TacticName,
            BaseScore = 50.0
        };

        BuyState effectiveBuy = ctEcon.FinalBuyState != BuyState.UNKNOWN_INCOMPLETE_BUY
            ? ctEcon.FinalBuyState
            : ctEcon.PurchaseIntent;

        bool isEcoOrPistol = effectiveBuy == BuyState.FULL_ECO || effectiveBuy == BuyState.PISTOL_ROUND || effectiveBuy == BuyState.LIGHT_BUY;
        bool isFullBuy = effectiveBuy == BuyState.FULL_BUY || effectiveBuy == BuyState.SAVE_WITH_WEAPONS;
        bool hasAwp = ctEcon.AwpCount > 0 || (isFullBuy && ctEcon.AverageCashBeforeBuy >= 4750);
        bool enemyEstimatedEco = !trEcon.PistolRound && trEcon.LossBonus <= 1900 && trEcon.AverageCashBeforeBuy < 2400;

        // 1. Fator Econômico e Preferência Forte pela Família 2-1-2 Padrão CT
        bool isStandard212Family = bp.TacticId == "CT_STANDARD_2_1_2_BALANCED" ||
                                   bp.TacticId == "CT_2_1_2_HEAVY_ANCHOR_B" ||
                                   bp.TacticId == "CT_2_1_2_HEAVY_PALACE_RAMP_A";

        int consecutiveCtLosses = 0;
        for (int i = recentHistory.Count - 1; i >= 0; i--)
        {
            if (recentHistory[i].Winner == CsTeam.Terrorist) consecutiveCtLosses++;
            else break;
        }

        if (isEcoOrPistol)
        {
            if (bp.IsEcoStackGamble)
            {
                score.EconomyAdjustment += 40.0;
                score.Factors.Add("EcoGambleBoost(+40)");
            }
            else if (bp.FocusSector == "RETAKE")
            {
                score.EconomyAdjustment += 20.0;
                score.Factors.Add("EcoRetakeSave(+20)");
            }
            else if (bp.PrefersAwp)
            {
                score.EconomyAdjustment -= 35.0;
                score.Factors.Add("NoAwpInEco(-35)");
            }
        }
        else
        {
            if (bp.IsEcoStackGamble)
            {
                score.EconomyAdjustment -= 60.0;
                score.Factors.Add("AvoidGambleOnBuyRound(-60)");
            }

            if (bp.TacticId == "CT_STANDARD_2_1_2_BALANCED")
            {
                score.EconomyAdjustment += 28.0;
                score.Factors.Add("PreferredDefault212(+28)");
            }
            else if (isStandard212Family)
            {
                score.EconomyAdjustment += 18.0;
                score.Factors.Add("Standard212Family(+18)");
            }
            else if (consecutiveCtLosses < 2)
            {
                // Formações fora do 2-1-2 (1-3-1 Mid Dominance ou Retake Passivo) são raras:
                // penalizadas quando o CT está ganhando ou empatando, liberadas apenas em contra-jogo (lossStreak >= 2)
                score.EconomyAdjustment -= 30.0;
                score.Factors.Add("Keep212UnlessCounterPlay(-30)");
            }
            else
            {
                score.EconomyAdjustment += 15.0;
                score.Factors.Add($"CounterPlayLossStreak{consecutiveCtLosses}(+15)");
            }
        }

        // 2. Composição de Armamento (AWP)
        if (hasAwp && bp.PrefersAwp)
        {
            score.WeaponCompositionAdjustment += 25.0;
            score.Factors.Add("AwpLongSightlines(+25)");
        }

        // 3. Anti-Eco contra inimigo quebrado
        if (enemyEstimatedEco && bp.IsAntiEcoFriendly)
        {
            score.EnemyEconomyAdjustment += 30.0;
            score.Factors.Add("AntiEcoCrossfire(+30)");
        }

        // 4. Memória de Partida (Últimos 4 rounds)
        if (recentHistory.Count > 0)
        {
            var last2 = recentHistory.TakeLast(2).ToList();
            int attacksA = last2.Count(r => string.Equals(r.AttackedSite, "A", StringComparison.OrdinalIgnoreCase) ||
                                            string.Equals(r.PlantedSite, "A", StringComparison.OrdinalIgnoreCase));
            int attacksB = last2.Count(r => string.Equals(r.AttackedSite, "B", StringComparison.OrdinalIgnoreCase) ||
                                            string.Equals(r.PlantedSite, "B", StringComparison.OrdinalIgnoreCase));

            if (attacksA >= 2 && bp.FocusSector == "A")
            {
                score.HistoryMindgameAdjustment += 25.0;
                score.Factors.Add("CounterRepeatedTrAttackA(+25)");
            }
            else if (attacksB >= 2 && bp.FocusSector == "B")
            {
                score.HistoryMindgameAdjustment += 25.0;
                score.Factors.Add("CounterRepeatedTrAttackB(+25)");
            }

            var lastRound = recentHistory[^1];
            if (lastRound.FirstCtDeathSector == "Mid" && bp.FocusSector == "MID" && consecutiveCtLosses >= 2)
            {
                score.HistoryMindgameAdjustment += 22.0;
                score.Factors.Add("ReinforceMidAfterRepeatedLoss(+22)");
            }

            bool usedTwoTimesInARow = recentHistory.Count >= 2 &&
                                      recentHistory[^1].CtTacticId == bp.TacticId &&
                                      recentHistory[^2].CtTacticId == bp.TacticId;

            if (!usedTwoTimesInARow &&
                lastRound.Winner == CsTeam.CounterTerrorist &&
                lastRound.CtTacticId == bp.TacticId &&
                lastRound.SurvivingWinnersCount >= 3)
            {
                score.WinMomentumAdjustment += 10.0;
                score.Factors.Add("ConvincingWinMomentum(+10)");
            }

            // 5. Penalidade Anti-Repetição (Suavizada para CT_STANDARD_2_1_2_BALANCED quando CT vence, mantendo 2-1-2 como espinha dorsal)
            if (lastRound.CtTacticId == bp.TacticId)
            {
                double effectivePenalty = (bp.TacticId == "CT_STANDARD_2_1_2_BALANCED" && lastRound.Winner == CsTeam.CounterTerrorist && !usedTwoTimesInARow)
                    ? 12.0
                    : _config.RepetitionPenaltyImmediate;
                score.RepetitionPenalty += effectivePenalty;
                score.Factors.Add($"RepetitionR-1(-{effectivePenalty:F0})");
            }
            else if (recentHistory.Count >= 2 && recentHistory[^2].CtTacticId == bp.TacticId)
            {
                double effectivePenalty2 = bp.TacticId == "CT_STANDARD_2_1_2_BALANCED"
                    ? 5.0
                    : _config.RepetitionPenaltyTwoRoundsAgo;
                score.RepetitionPenalty += effectivePenalty2;
                score.Factors.Add($"RepetitionR-2(-{effectivePenalty2:F0})");
            }
        }

        return score;
    }

    public UtilityScoreBreakdown ScoreTrTactic(
        TrTacticBlueprint bp,
        TeamEconomySnapshot trEcon,
        TeamEconomySnapshot ctEcon,
        IReadOnlyList<RoundHistoryItem> recentHistory)
    {
        var score = new UtilityScoreBreakdown
        {
            TacticId = bp.TacticId,
            DisplayName = bp.TacticName,
            BaseScore = 50.0
        };

        BuyState effectiveBuy = trEcon.FinalBuyState != BuyState.UNKNOWN_INCOMPLETE_BUY
            ? trEcon.FinalBuyState
            : trEcon.PurchaseIntent;

        bool isEcoOrPistol = effectiveBuy == BuyState.FULL_ECO || effectiveBuy == BuyState.PISTOL_ROUND || effectiveBuy == BuyState.LIGHT_BUY;
        bool isForceOrHalf = effectiveBuy == BuyState.FORCE_BUY || effectiveBuy == BuyState.HALF_BUY;
        bool isFullBuy = effectiveBuy == BuyState.FULL_BUY || effectiveBuy == BuyState.SAVE_WITH_WEAPONS;
        bool hasAwp = trEcon.AwpCount > 0;
        bool enemyEstimatedEco = !ctEcon.PistolRound && ctEcon.LossBonus <= 1900 && ctEcon.AverageCashBeforeBuy < 2600;

        // 1. Fator Econômico
        if (isEcoOrPistol)
        {
            if (bp.IsFastCloseRange)
            {
                score.EconomyAdjustment += 40.0;
                score.Factors.Add("EcoFastBurstBoost(+40)");
            }
            if (bp.IsSlowLongRange)
            {
                score.EconomyAdjustment -= 35.0;
                score.Factors.Add("EcoSlowDefaultPenalty(-35)");
            }
        }
        else if (isForceOrHalf)
        {
            if (bp.IsSplitPlay || bp.TacticType == TrTacticType.SPLIT_FAKE)
            {
                score.EconomyAdjustment += 22.0;
                score.Factors.Add("ForceBuyDeceptionOrSplit(+22)");
            }
        }
        else if (isFullBuy)
        {
            if (!bp.IsFastCloseRange)
            {
                score.EconomyAdjustment += 18.0;
                score.Factors.Add("FullBuyStructuredExec(+18)");
            }
        }

        // 2. Composição de Armamento (AWP)
        if (hasAwp && bp.IsSlowLongRange)
        {
            score.WeaponCompositionAdjustment += 25.0;
            score.Factors.Add("TrAwpPickPlay(+25)");
        }

        // 3. Anti-Eco contra CT em Eco
        if (enemyEstimatedEco && bp.IsSlowLongRange)
        {
            score.EnemyEconomyAdjustment += 30.0;
            score.Factors.Add("AntiEcoAvoidStackWithDefault(+30)");
        }

        // 4. Memória de Partida (Mindgame dos últimos 4 rounds)
        if (recentHistory.Count > 0)
        {
            var last2 = recentHistory.TakeLast(2).ToList();
            int attacksA = last2.Count(r => string.Equals(r.AttackedSite, "A", StringComparison.OrdinalIgnoreCase) ||
                                            string.Equals(r.PlantedSite, "A", StringComparison.OrdinalIgnoreCase));
            int attacksB = last2.Count(r => string.Equals(r.AttackedSite, "B", StringComparison.OrdinalIgnoreCase) ||
                                            string.Equals(r.PlantedSite, "B", StringComparison.OrdinalIgnoreCase));

            if (attacksA >= 2)
            {
                if (bp.TacticId == "TR_FAKE_A_EXEC_B" || bp.TargetSite == "B")
                {
                    score.HistoryMindgameAdjustment += 25.0;
                    score.Factors.Add("MindgameExploitHeavyCtA(+25)");
                }
            }
            else if (attacksB >= 2)
            {
                if (bp.TacticId == "TR_FAKE_B_EXEC_A" || bp.TargetSite == "A")
                {
                    score.HistoryMindgameAdjustment += 25.0;
                    score.Factors.Add("MindgameExploitHeavyCtB(+25)");
                }
            }

            var lastRound = recentHistory[^1];
            bool usedTwoTimesInARow = recentHistory.Count >= 2 &&
                                      recentHistory[^1].TrTacticId == bp.TacticId &&
                                      recentHistory[^2].TrTacticId == bp.TacticId;

            if (!usedTwoTimesInARow &&
                lastRound.Winner == CsTeam.Terrorist &&
                lastRound.TrTacticId == bp.TacticId &&
                lastRound.SurvivingWinnersCount >= 3)
            {
                score.WinMomentumAdjustment += 10.0;
                score.Factors.Add("ConvincingWinMomentum(+10)");
            }

            // 5. Penalidade Anti-Repetição
            if (lastRound.TrTacticId == bp.TacticId)
            {
                score.RepetitionPenalty += _config.RepetitionPenaltyImmediate; // 35 pts
                score.Factors.Add($"RepetitionR-1(-{_config.RepetitionPenaltyImmediate:F0})");
            }
            else if (recentHistory.Count >= 2 && recentHistory[^2].TrTacticId == bp.TacticId)
            {
                score.RepetitionPenalty += _config.RepetitionPenaltyTwoRoundsAgo; // 15 pts
                score.Factors.Add($"RepetitionR-2(-{_config.RepetitionPenaltyTwoRoundsAgo:F0})");
            }
        }

        return score;
    }

    // =========================================================================
    // ROLETA PONDERADA (TEMPERATURE SOFTMAX SAMPLING)
    // =========================================================================

    public UtilityScoreBreakdown SelectWithTemperatureSoftmax(
        List<UtilityScoreBreakdown> topCandidates,
        float temperature = 0.65f)
    {
        if (topCandidates.Count == 0)
            throw new InvalidOperationException("Candidate list for Softmax cannot be empty.");

        if (topCandidates.Count == 1)
        {
            topCandidates[0].SoftmaxProbability = 1.0;
            return topCandidates[0];
        }

        double maxScore = topCandidates.Max(c => c.FinalScore);
        double safeTemp = Math.Max(0.10, temperature);

        double[] expWeights = new double[topCandidates.Count];
        double sumExp = 0.0;

        for (int i = 0; i < topCandidates.Count; i++)
        {
            double scaledDelta = (topCandidates[i].FinalScore - maxScore) / (10.0 * safeTemp);
            expWeights[i] = Math.Exp(scaledDelta);
            sumExp += expWeights[i];
        }

        for (int i = 0; i < topCandidates.Count; i++)
        {
            topCandidates[i].SoftmaxProbability = expWeights[i] / sumExp;
        }

        double roll = _rng.NextDouble();
        double cumulative = 0.0;

        for (int i = 0; i < topCandidates.Count; i++)
        {
            cumulative += topCandidates[i].SoftmaxProbability;
            if (roll <= cumulative)
            {
                return topCandidates[i];
            }
        }

        return topCandidates[0];
    }

    // =========================================================================
    // ROTEADOR LÉXICO INSTANTÂNEO DE COMANDOS HUMANOS POR MAPA (0.01ms)
    // =========================================================================

    public bool TryRouteHumanCommandLexically(
        CsTeam team,
        string rawCommand,
        out string matchedTacticId,
        out string matchedReason,
        string? mapName = null)
    {
        matchedTacticId = string.Empty;
        matchedReason = string.Empty;

        if (string.IsNullOrWhiteSpace(rawCommand))
            return false;

        string text = rawCommand.Trim().ToLowerInvariant();
        var catalog = GetCatalogForMap(mapName);
        return catalog.TryRouteMapSpecificLexicalCall(team, text, out matchedTacticId, out matchedReason);
    }

    // =========================================================================
    // MATERIALIZAÇÃO DE PLANOS CT E TR (5 SPOTS DISTINTOS GARANTIDOS)
    // =========================================================================

    private TacticalPlan MaterializeCtBlueprint(
        CtTacticBlueprint bp,
        long internalRoundId,
        int displayRound,
        List<CCSPlayerController>? ctBots,
        MapProfileManager? mapProfileManager,
        int currentTick,
        TacticalDecisionSource source)
    {
        var plan = new TacticalPlan
        {
            RoundId = displayRound,
            DecisionId = $"R{internalRoundId}_CT_{bp.TacticId}_{Guid.NewGuid().ToString("N")[..6]}",
            TeamSide = CsTeam.CounterTerrorist,
            PlayId = bp.TacticId,
            TacticName = bp.TacticName,
            TacticSummary = bp.TacticSummary,
            RoundTempo = bp.Tempo,
            StagingDurationSeconds = bp.StagingDuration,
            CtDuoPlay = bp.DuoPlay,
            RequestedAtTick = currentTick,
            CompletedAtTick = currentTick,
            Source = source,
            ParseStatus = "OK",
            ModelResponseStatus = source.ToString(),
            FallbackUsed = false,
            FallbackReason = "NONE"
        };

        plan.InitializeVersioning(bp.TacticName, bp.FocusSector, source, currentTick);
        plan.SelectedTactic = bp.TacticId;

        var slots = ctBots != null && ctBots.Count > 0
            ? ctBots.Where(b => b != null && b.IsValid).Select(b => b.Slot).OrderBy(s => s).ToList()
            : new List<int> { 0, 1, 2, 3, 4 };

        while (slots.Count < 5)
        {
            int nextSlot = slots.Count == 0 ? 0 : slots.Max() + 1;
            slots.Add(nextSlot);
        }

        string[] roleOrder = { "AWPer", "EntryFragger", "Rotator", "Anchor_1", "Anchor_2" };

        for (int i = 0; i < Math.Min(5, bp.Assignments.Count); i++)
        {
            var srcAssign = bp.Assignments[i];
            int botSlot = slots[i];

            var assign = new CtFormationAssignment
            {
                Slot = botSlot,
                FormationRole = srcAssign.FormationRole,
                AssignedSite = srcAssign.AssignedSite,
                InitialSpot = srcAssign.InitialSpot,
                ExecuteSpot = srcAssign.ExecuteSpot,
                RotationPolicy = srcAssign.RotationPolicy,
                HoldMinimumDuration = srcAssign.HoldMinimumDuration,
                RotationTrigger = srcAssign.RotationTrigger
            };
            plan.CtFormationAssignments[botSlot] = assign;

            string targetArea = srcAssign.AssignedSite switch
            {
                "A" => "Bombsite A",
                "B" => "Bombsite B",
                _ => "Middle"
            };

            string roleKey = roleOrder[i];
            var ctOrder = new BotTacticalOrder
            {
                TargetArea = targetArea,
                RoleAction = $"Hold {srcAssign.AssignedSite} ({srcAssign.FormationRole}) at {srcAssign.InitialSpot}",
                StagingSpotId = srcAssign.InitialSpot,
                ExecuteSpotId = srcAssign.ExecuteSpot,
                FallbackSpotId = srcAssign.AssignedSite == "B" ? "ct_b_market_door" : "ct_jungle_safe",
                Stance = srcAssign.FormationRole == CtFormationRole.Mid_Controller
                    ? EngagementStance.JIGGLE_INFO
                    : EngagementStance.PASSIVE_HOLD,
                HoldSiteLocked = true,
                RequiredUtilities = new List<string> { "smoke", "flashbang", "incgrenade" }
            };

            plan.BotOrders[roleKey] = ctOrder;
            plan.BotOrders[$"slot_{botSlot}"] = ctOrder;
        }

        if (plan.BotOrders.TryGetValue("AWPer", out var awpOrd))
            plan.BotOrders[RoleManager.GetOrderKey(BotRole.AWPer)] = awpOrd;
        if (plan.BotOrders.TryGetValue("EntryFragger", out var entOrd))
            plan.BotOrders[RoleManager.GetOrderKey(BotRole.EntryFragger)] = entOrd;
        if (plan.BotOrders.TryGetValue("Rotator", out var rotOrd))
            plan.BotOrders[RoleManager.GetOrderKey(BotRole.Rotator)] = rotOrd;
        if (plan.BotOrders.TryGetValue("Anchor_1", out var ancOrd))
            plan.BotOrders[RoleManager.GetOrderKey(BotRole.Anchor)] = ancOrd;

        TacticalOrderMaterializer.MaterializeCt212Orders(plan, ctBots, mapProfileManager);

        return plan;
    }

    private TacticalPlan MaterializeTrBlueprint(
        TrTacticBlueprint bp,
        long internalRoundId,
        int displayRound,
        List<CCSPlayerController>? trBots,
        MapProfileManager? mapProfileManager,
        int currentTick,
        TacticalDecisionSource source)
    {
        var plan = new TacticalPlan
        {
            RoundId = displayRound,
            DecisionId = $"R{internalRoundId}_TR_{bp.TacticId}_{Guid.NewGuid().ToString("N")[..6]}",
            TeamSide = CsTeam.Terrorist,
            PlayId = bp.TacticId,
            TacticName = bp.TacticName,
            TacticSummary = bp.TacticSummary,
            RoundTempo = bp.Tempo,
            StagingDurationSeconds = bp.StagingDuration,
            TrTacticType = bp.TacticType,
            RequestedAtTick = currentTick,
            CompletedAtTick = currentTick,
            Source = source,
            ParseStatus = "OK",
            ModelResponseStatus = source.ToString(),
            FallbackUsed = false,
            FallbackReason = "NONE"
        };

        string effectiveTargetSite = !string.IsNullOrEmpty(bp.RealSite) ? bp.RealSite : bp.TargetSite;
        plan.InitializeVersioning(bp.TacticName, effectiveTargetSite, source, currentTick);
        plan.SelectedTactic = bp.TacticId;

        foreach (var ord in bp.Orders)
        {
            plan.BotOrders[ord.RoleKey] = new BotTacticalOrder
            {
                TargetArea = ord.TargetArea,
                RoleAction = ord.RoleAction,
                StagingSpotId = ord.StagingSpotId,
                ExecuteSpotId = ord.ExecuteSpotId,
                FallbackSpotId = ord.FallbackSpotId,
                Stance = ord.Stance,
                IsNoiseGroup = ord.IsNoiseGroup,
                HasBomb = ord.RoleKey == "Rotator" && !ord.IsNoiseGroup,
                RequiredUtilities = new List<string>(ord.RequiredUtilities)
            };
        }

        if (bp.TacticType == TrTacticType.SPLIT_FAKE && !string.IsNullOrEmpty(bp.FakeSite) && !string.IsNullOrEmpty(bp.RealSite))
        {
            plan.SetFakeExecution(bp.FakeSite, bp.RealSite, bp.StagingDuration, currentTick, $"UtilityAI:{bp.TacticId}", plan.DecisionId);
        }
        else if (BombsiteParser.TryParseBombsiteTarget(effectiveTargetSite, out var parsedRealSite) &&
                 (parsedRealSite == BombsiteTarget.A || parsedRealSite == BombsiteTarget.B))
        {
            plan.BombObjectiveState.CommitMaterializedSite(
                plan.DecisionId,
                bp.TacticId,
                BombsiteTarget.None,
                parsedRealSite,
                currentTick,
                $"UtilityAI:{bp.TacticId}");
        }

        int carrierSlot = trBots != null && trBots.Count > 0 ? FindBombCarrierSlot(trBots) : -1;
        TacticalOrderMaterializer.MaterializeTrOrders(plan, trBots, carrierSlot, mapProfileManager, currentTick);

        return plan;
    }

    private static int FindBombCarrierSlot(List<CCSPlayerController> trBots)
    {
        foreach (var bot in trBots)
        {
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive) continue;
            var weapons = bot.PlayerPawn.Value?.WeaponServices?.MyWeapons;
            if (weapons == null) continue;
            foreach (var w in weapons)
            {
                if (w?.Value?.DesignerName != null &&
                    w.Value.DesignerName.Contains("weapon_c4", StringComparison.OrdinalIgnoreCase))
                {
                    return bot.Slot;
                }
            }
        }
        return trBots.FirstOrDefault(b => b != null && b.IsValid)?.Slot ?? -1;
    }

    private void PopulateAuditMetadata(
        TacticalPlan plan,
        UtilityScoreBreakdown winner,
        List<UtilityScoreBreakdown> top3,
        double elapsedMs)
    {
        plan.LatencyMs = Math.Round(elapsedMs, 4);
        plan.CandidateTactics = top3.Select(c => c.TacticId).ToList();
        plan.SelectionScores.Clear();
        foreach (var c in top3)
        {
            plan.SelectionScores[c.TacticId] = Math.Round(c.FinalScore, 2);
        }
        plan.RepetitionPenaltyApplied = top3.Any(c => c.RepetitionPenalty > 0);
        plan.SelectionReason = $"Winner={winner.TacticId} ({winner.FinalScore:F1}pts, P={winner.SoftmaxProbability:P0}) | Top3=[{string.Join(" ; ", top3.Select(t => t.FormatAuditSummary()))}]";
    }
}
