using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class OrganicRushesAndFakesTests
{
    private readonly MapProfileManager _mapProfileManager;

    public OrganicRushesAndFakesTests()
    {
        _mapProfileManager = new MapProfileManager();
        var spots = new List<TacticalSpot>
        {
            new() { Id = "tr_staging_b_apartments_kitchen", Sector = "Apartamentos B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging },
            new() { Id = "tr_staging_b_apartments_house", Sector = "Apartamentos B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging },
            new() { Id = "tr_exec_b_site_plant", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Plant },
            new() { Id = "tr_exec_b_van_clear", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute },
            new() { Id = "tr_exec_b_market_push", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute },
            new() { Id = "tr_staging_a_ramp", Sector = "Rampa A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Staging },
            new() { Id = "tr_staging_palace_room", Sector = "Palácio A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Staging },
            new() { Id = "tr_exec_a_site_default", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Plant },
            new() { Id = "tr_exec_a_triple_clear", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute },
            new() { Id = "tr_exec_a_stairs_clear", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute },
            new() { Id = "tr_staging_top_mid_boxes", Sector = "Top Mid", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Staging },
            new() { Id = "tr_staging_underpass_top", Sector = "Underpass", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Staging },
            new() { Id = "tr_exec_mid_connector_push", Sector = "Connector", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Execute },
            new() { Id = "tr_staging_t_roof", Sector = "T Roof", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Staging },
            new() { Id = "tr_spawn_safe", Sector = "TR Spawn", Side = "TR", AssociatedBombsite = "None", Usage = SpotUsage.Fallback }
        };
        _mapProfileManager.SetSpotsForTesting(spots);
    }

    [Fact]
    public void Test1_FakeA_MaterializesA_ForDistraction_And_B_ForPlant()
    {
        // Act
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        // Assert
        Assert.True(orders.ContainsKey("bot_awper"));
        Assert.True(orders.ContainsKey("bot_anchor"));
        Assert.True(orders.ContainsKey("bot_entry"));
        Assert.True(orders.ContainsKey("bot_rotator"));

        // AWPer e Anchor fazem a finta no Bomb A
        Assert.Equal("tr_staging_a_ramp", orders["bot_awper"].StagingSpotId);
        Assert.Equal("tr_staging_palace_room", orders["bot_anchor"].StagingSpotId);

        // EntryFragger e Rotator (C4) executam a invasão real no Bomb B
        Assert.Equal("tr_staging_b_apartments_kitchen", orders["bot_entry"].StagingSpotId);
        Assert.Equal("tr_exec_b_site_plant", orders["bot_entry"].ExecuteSpotId);
        Assert.Equal("tr_staging_b_apartments_kitchen", orders["bot_rotator"].StagingSpotId);
        Assert.Equal("tr_exec_b_site_plant", orders["bot_rotator"].ExecuteSpotId);
    }

    [Fact]
    public void Test2_FakeB_MaterializesB_ForDistraction_And_A_ForPlant()
    {
        // Act
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        // Assert
        Assert.True(orders.ContainsKey("bot_awper"));
        Assert.True(orders.ContainsKey("bot_anchor"));
        Assert.True(orders.ContainsKey("bot_entry"));
        Assert.True(orders.ContainsKey("bot_rotator"));

        // AWPer e Anchor fazem a finta no Bomb B
        Assert.Equal("tr_staging_b_apartments_house", orders["bot_awper"].StagingSpotId);
        Assert.Equal("tr_staging_underpass_top", orders["bot_anchor"].StagingSpotId);

        // EntryFragger e Rotator (C4) executam a invasão real no Bomb A
        Assert.Equal("tr_staging_palace_room", orders["bot_entry"].StagingSpotId);
        Assert.Equal("tr_exec_a_site_default", orders["bot_entry"].ExecuteSpotId);
        Assert.Equal("tr_staging_a_ramp", orders["bot_rotator"].StagingSpotId);
        Assert.Equal("tr_exec_a_site_default", orders["bot_rotator"].ExecuteSpotId);
    }

    [Fact]
    public void Test3_ValidateAndRepair_RepairsMidSpoofInFakeA()
    {
        // Arrange
        var plan = new TacticalPlan
        {
            CurrentTactic = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            BotOrders = new Dictionary<string, BotTacticalOrder>
            {
                ["bot_entry"] = new()
                {
                    TargetArea = "Bombsite Mid",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_staging_top_mid_boxes"
                },
                ["bot_rotator"] = new()
                {
                    TargetArea = "Bombsite Mid",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_staging_top_mid_boxes"
                }
            }
        };

        // Act: Na Fake A, o ataque real é em B. O validador deve reparar as ordens de Mid para Bombsite B!
        bool repaired = TacticalOrderMaterializer.ValidateAndRepairOrders(
            plan,
            CsTeam.Terrorist,
            _mapProfileManager,
            null,
            "DEC-TEST-FAKE-A");

        // Assert
        Assert.True(repaired);
        Assert.Equal("tr_staging_b_apartments_kitchen", plan.BotOrders["bot_entry"].StagingSpotId);
        Assert.Equal("tr_exec_b_site_plant", plan.BotOrders["bot_entry"].ExecuteSpotId);
        Assert.Equal("tr_staging_b_apartments_kitchen", plan.BotOrders["bot_rotator"].StagingSpotId);
        Assert.Equal("tr_exec_b_site_plant", plan.BotOrders["bot_rotator"].ExecuteSpotId);
    }

    [Fact]
    public void Test4_ValidateAndRepair_RepairsMidSpoofInFakeB()
    {
        // Arrange
        var plan = new TacticalPlan
        {
            CurrentTactic = "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
            BotOrders = new Dictionary<string, BotTacticalOrder>
            {
                ["bot_entry"] = new()
                {
                    TargetArea = "Bombsite Mid",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_staging_top_mid_boxes"
                },
                ["bot_rotator"] = new()
                {
                    TargetArea = "Bombsite Mid",
                    StagingSpotId = "tr_staging_top_mid_boxes",
                    ExecuteSpotId = "tr_staging_top_mid_boxes"
                }
            }
        };

        // Act: Na Fake B, o ataque real é em A. O validador deve reparar as ordens de Mid para Bombsite A!
        bool repaired = TacticalOrderMaterializer.ValidateAndRepairOrders(
            plan,
            CsTeam.Terrorist,
            _mapProfileManager,
            null,
            "DEC-TEST-FAKE-B");

        // Assert
        Assert.True(repaired);
        Assert.Equal("tr_staging_palace_room", plan.BotOrders["bot_entry"].StagingSpotId);
        Assert.Equal("tr_exec_a_site_default", plan.BotOrders["bot_entry"].ExecuteSpotId);
        Assert.Equal("tr_staging_a_ramp", plan.BotOrders["bot_rotator"].StagingSpotId);
        Assert.Equal("tr_exec_a_site_default", plan.BotOrders["bot_rotator"].ExecuteSpotId);
    }

    [Fact]
    public void Test5_EvaluateCandidateTactics_IncludesFakeA_And_FakeB()
    {
        // Arrange
        var igl = new OllamaIglService();

        // Act
        var candidates = igl.EvaluateCandidateTactics(
            CsTeam.Terrorist,
            BuyState.FULL_BUY,
            roundNumber: 3,
            avgMoney: 4500,
            lossStreak: 1,
            lastBombSite: "A");

        // Assert
        Assert.Contains(candidates, c => c.TacticName.Contains("Fake A", StringComparison.OrdinalIgnoreCase));
        Assert.Contains(candidates, c => c.TacticName.Contains("Fake B", StringComparison.OrdinalIgnoreCase));

        var fakeA = candidates.First(c => c.TacticName.Contains("Fake A", StringComparison.OrdinalIgnoreCase));
        Assert.True(fakeA.BaseContextualScore >= 80.0f);
        Assert.Equal(RoundTempo.POKE_AND_ROTATE, fakeA.RecommendedTempo);
    }

    [Fact]
    public void Test6_BuildPlanFromCandidate_FakeA_BuildsCorrectPlan()
    {
        // Arrange
        var igl = new OllamaIglService();
        var candidate = new CandidateTacticScore
        {
            TacticName = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            Summary = "Finta no Bomb A com utilitárias na Rampa/Palácio e invasão veloz pelo Tapete B",
            RecommendedTempo = RoundTempo.POKE_AND_ROTATE,
            RecommendedStagingSeconds = 10.0f
        };

        // Act
        var plan = igl.BuildPlanFromCandidate(candidate, CsTeam.Terrorist, _mapProfileManager);

        // Assert
        Assert.Equal(candidate.TacticName, plan.TacticName);
        Assert.True(plan.BotOrders.ContainsKey("bot_entry"));
        Assert.True(plan.BotOrders.ContainsKey("bot_rotator"));
        Assert.Equal("tr_staging_b_apartments_kitchen", plan.BotOrders["bot_entry"].StagingSpotId);
        Assert.Equal("tr_staging_b_apartments_kitchen", plan.BotOrders["bot_rotator"].StagingSpotId);
        Assert.Equal("tr_exec_b_site_plant", plan.BotOrders["bot_rotator"].ExecuteSpotId);
    }

    [Fact]
    public void Test7_BuildPlanFromCandidate_FakeB_BuildsCorrectPlan()
    {
        // Arrange
        var igl = new OllamaIglService();
        var candidate = new CandidateTacticScore
        {
            TacticName = "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
            Summary = "Finta no Bomb B pelo Tapete/Underpass chamando rotação CT e invasão pelo Palácio/Rampa A",
            RecommendedTempo = RoundTempo.POKE_AND_ROTATE,
            RecommendedStagingSeconds = 12.0f
        };

        // Act
        var plan = igl.BuildPlanFromCandidate(candidate, CsTeam.Terrorist, _mapProfileManager);

        // Assert
        Assert.Equal(candidate.TacticName, plan.TacticName);
        Assert.True(plan.BotOrders.ContainsKey("bot_entry"));
        Assert.True(plan.BotOrders.ContainsKey("bot_rotator"));
        Assert.Equal("tr_staging_palace_room", plan.BotOrders["bot_entry"].StagingSpotId);
        Assert.Equal("tr_staging_a_ramp", plan.BotOrders["bot_rotator"].StagingSpotId);
        Assert.Equal("tr_exec_a_site_default", plan.BotOrders["bot_rotator"].ExecuteSpotId);
    }

    [Fact]
    public void Test8_OrganicAdaptation_TracksTradeRequired_OnFastContact()
    {
        // Arrange
        var plan = new TacticalPlan
        {
            CurrentTactic = "Execução B (Tapete / Apartamentos Rápido)",
            RoundTempo = RoundTempo.FAST_CONTACT,
            TacticRevision = 1
        };

        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        // Act
        midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TradeRequired,
            new List<int> { 2, 4, 6 },
            8.0f,
            "RUSH_TRADE Commit into Bombsite B",
            ownerTeam: CsTeam.Terrorist);

        // Assert
        Assert.Equal(2, plan.TacticRevision);
    }

    [Fact]
    public void Test9_OrganicAdaptation_TracksUtilityWait_OnPause()
    {
        // Arrange
        var plan = new TacticalPlan
        {
            CurrentTactic = "Split A (Top Mid + Conector + Palácio)",
            RoundTempo = RoundTempo.SLOW_DEFAULT,
            TacticRevision = 1
        };

        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        // Act
        midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.UtilityWait,
            new List<int> { 2, 4, 6 },
            4.0f,
            "WAIT_AND_REEXECUTE Hold 4s for utilities then push Bombsite A",
            ownerTeam: CsTeam.Terrorist);

        // Assert
        Assert.Equal(2, plan.TacticRevision);
    }

    [Fact]
    public void Test10_TacticalAdaptationReason_EnumValues_Integrity()
    {
        // Assert: garante que todos os valores chave de adaptação estão disponíveis
        Assert.True(Enum.IsDefined(typeof(TacticalAdaptationReason), TacticalAdaptationReason.TradeRequired));
        Assert.True(Enum.IsDefined(typeof(TacticalAdaptationReason), TacticalAdaptationReason.UtilityWait));
        Assert.True(Enum.IsDefined(typeof(TacticalAdaptationReason), TacticalAdaptationReason.EntryKilled));
        Assert.True(Enum.IsDefined(typeof(TacticalAdaptationReason), TacticalAdaptationReason.TimePressure));
        Assert.True(Enum.IsDefined(typeof(TacticalAdaptationReason), TacticalAdaptationReason.SaveDecision));
        Assert.True(Enum.IsDefined(typeof(TacticalAdaptationReason), TacticalAdaptationReason.RetakeDecision));
    }
}
