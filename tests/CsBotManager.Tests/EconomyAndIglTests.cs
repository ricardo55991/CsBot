using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class EconomyAndIglTests
{
    [Fact]
    public void ClassifyPostBuySnapshot_DistinguishesPistolFullBuyForceBuyEcoAndSaved()
    {
        var config = BotSystemConfig.Default;

        // 1. Pistol Round (Round 1)
        var pistolSnap = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.CounterTerrorist,
            RoundNumberInHalf = 1,
            PistolRound = true,
            AverageCashBeforeBuy = 800,
            AverageCashAfterBuy = 150,
            ArmorCount = 4,
            PrimaryWeaponCount = 0,
            EquipmentValueAfterBuy = 3600,
            CompletionState = BuyCompletionState.STABILIZED
        };
        Assert.Equal(BuyState.PISTOL_ROUND, EconomyManager.ClassifyPostBuySnapshot(pistolSnap, config));

        // 2. Full Buy CT (4 Rifles + 1 AWP + 5 Armors)
        var fullBuySnap = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.CounterTerrorist,
            RoundNumberInHalf = 4,
            PistolRound = false,
            AverageCashBeforeBuy = 5200,
            AverageCashAfterBuy = 600,
            RifleCount = 4,
            AwpCount = 1,
            PrimaryWeaponCount = 5,
            ArmorCount = 5,
            HelmetCount = 5,
            EquipmentValueAfterBuy = 24500,
            CompletionState = BuyCompletionState.STABILIZED
        };
        Assert.Equal(BuyState.FULL_BUY, EconomyManager.ClassifyPostBuySnapshot(fullBuySnap, config));

        // 3. Force Buy TR (3 SMGs + 1 Galil, low remaining cash)
        var forceBuySnap = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.Terrorist,
            RoundNumberInHalf = 2,
            PistolRound = false,
            PurchaseIntent = BuyState.FORCE_BUY,
            AverageCashBeforeBuy = 2050,
            AverageCashAfterBuy = 250,
            RifleCount = 1,
            SmgCount = 3,
            PrimaryWeaponCount = 4,
            ArmorCount = 4,
            EquipmentValueAfterBuy = 11200,
            CompletionState = BuyCompletionState.STABILIZED
        };
        Assert.Equal(BuyState.FORCE_BUY, EconomyManager.ClassifyPostBuySnapshot(forceBuySnap, config));

        // 4. Save With Weapons (3 saved rifles, minimal spend)
        var savedSnap = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.CounterTerrorist,
            RoundNumberInHalf = 6,
            PistolRound = false,
            SavedWeaponCount = 3,
            SpentDuringFreezeTime = 1200,
            PrimaryWeaponCount = 3,
            RifleCount = 3,
            ArmorCount = 3,
            EquipmentValueAfterBuy = 13500,
            CompletionState = BuyCompletionState.STABILIZED
        };
        Assert.Equal(BuyState.SAVE_WITH_WEAPONS, EconomyManager.ClassifyPostBuySnapshot(savedSnap, config));

        // 5. Pending incomplete buy with high cash -> UNKNOWN_INCOMPLETE_BUY
        var incompleteSnap = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.Terrorist,
            RoundNumberInHalf = 5,
            PistolRound = false,
            PurchaseIntent = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 4800,
            AverageCashAfterBuy = 4800,
            PrimaryWeaponCount = 0,
            CompletionState = BuyCompletionState.PENDING
        };
        Assert.Equal(BuyState.UNKNOWN_INCOMPLETE_BUY, EconomyManager.ClassifyPostBuySnapshot(incompleteSnap, config));
    }

    [Fact]
    public void EvaluateCandidateTactics_PenalizesRepeatedTacticsAndVariesSelection()
    {
        var igl = new OllamaIglService();

        var round1Candidates = igl.EvaluateCandidateTactics(
            CsTeam.CounterTerrorist,
            BuyState.FULL_BUY,
            roundNumber: 1,
            avgMoney: 800,
            lossStreak: 0,
            recentTeamTactics: new List<string>());

        string firstSelected = round1Candidates[0].TacticName;

        var round2Candidates = igl.EvaluateCandidateTactics(
            CsTeam.CounterTerrorist,
            BuyState.FULL_BUY,
            roundNumber: 2,
            avgMoney: 4800,
            lossStreak: 0,
            recentTeamTactics: new List<string> { firstSelected });

        var penalizedEntry = round2Candidates.First(c => c.TacticName == firstSelected);
        Assert.True(penalizedEntry.RepetitionPenalty >= BotSystemConfig.Default.TacticRepetitionPenaltyScore);
        Assert.NotEqual(firstSelected, round2Candidates[0].TacticName);
    }

    [Fact]
    public void GenerateDeterministicFallbackPlan_PopulatesFullAuditMetadataAndNeverMixesSides()
    {
        var igl = new OllamaIglService();

        var ctPlan = igl.GenerateDeterministicFallbackPlan(
            CsTeam.CounterTerrorist,
            BuyState.FULL_BUY,
            mapProfileManager: null,
            reason: "UNIT_TEST_FALLBACK",
            roundNumber: 3,
            internalRoundId: 3,
            requestedAtTick: 1000,
            completedAtTick: 1005,
            latencyMs: 12.5);

        var trPlan = igl.GenerateDeterministicFallbackPlan(
            CsTeam.Terrorist,
            BuyState.FULL_BUY,
            mapProfileManager: null,
            reason: "UNIT_TEST_FALLBACK",
            roundNumber: 3,
            internalRoundId: 3,
            requestedAtTick: 1000,
            completedAtTick: 1005,
            latencyMs: 14.2);

        Assert.Equal(CsTeam.CounterTerrorist, ctPlan.TeamSide);
        Assert.Equal(CsTeam.Terrorist, trPlan.TeamSide);
        Assert.NotEqual(ctPlan.DecisionId, trPlan.DecisionId);
        Assert.NotEqual(ctPlan.RawJson, trPlan.RawJson);
        Assert.Equal(TacticalDecisionSource.FALLBACK_PRESET, ctPlan.Source);
        Assert.True(ctPlan.FallbackUsed);
        Assert.Equal(ctPlan.TacticName, ctPlan.InitialTactic);
        Assert.Equal(ctPlan.TacticName, ctPlan.CurrentTactic);
        Assert.Equal(1, ctPlan.TacticRevision);
        Assert.NotEmpty(ctPlan.CandidateTactics);
        Assert.NotEmpty(ctPlan.SelectionScores);
    }
}
