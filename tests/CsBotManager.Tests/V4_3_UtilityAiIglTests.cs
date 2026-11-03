using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class V4_3_UtilityAiIglTests
{
    [Fact]
    public void DecideRoundPlans_ExecutesUnderOneMillisecond_WithValidMirageSpots()
    {
        var mapManager = new MapProfileManager();
        string repoSrcDir = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "src", "CsBotManager"));
        mapManager.LoadProfile("de_mirage", repoSrcDir);
        var engine = new TacticalUtilityIglEngine(BotSystemConfig.Default, seed: 42);
        var ctEcon = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.CounterTerrorist,
            PurchaseIntent = BuyState.FULL_BUY,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 5200,
            AwpCount = 1
        };
        var trEcon = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.Terrorist,
            PurchaseIntent = BuyState.FULL_BUY,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 4800,
            AwpCount = 1
        };

        // Warmup JIT
        engine.DecideRoundPlans(1, 1, ctEcon, trEcon, null, null, mapManager, 100);

        var (ctPlan, trPlan) = engine.DecideRoundPlans(2, 2, ctEcon, trEcon, null, null, mapManager, 200);

        Assert.Equal(TacticalDecisionSource.UTILITY_AI_ENGINE, ctPlan.Source);
        Assert.Equal(TacticalDecisionSource.UTILITY_AI_ENGINE, trPlan.Source);
        Assert.False(ctPlan.FallbackUsed);
        Assert.False(trPlan.FallbackUsed);
        Assert.Equal("OK", ctPlan.ParseStatus);
        Assert.Equal("OK", trPlan.ParseStatus);
        Assert.True(ctPlan.LatencyMs < 1.0, $"Expected CT latency < 1ms, got {ctPlan.LatencyMs}ms");
        Assert.True(trPlan.LatencyMs < 1.0, $"Expected TR latency < 1ms, got {trPlan.LatencyMs}ms");
        Assert.Equal(5, ctPlan.CtFormationAssignments.Count);
        Assert.Equal(5, trPlan.BotOrders.Keys.Count(k => k.StartsWith("slot_", StringComparison.OrdinalIgnoreCase)));

        // Todos os spots de TODAS as 7 formações CT e 7 táticas TR devem existir em de_mirage.json
        var profile = mapManager.CurrentProfile;
        var validIds = profile.Spots.Select(s => s.Id).ToHashSet();

        foreach (var bp in engine.CtCatalog)
        {
            Assert.Equal(5, bp.Assignments.Count);
            foreach (var assign in bp.Assignments)
            {
                Assert.Contains(assign.InitialSpot, validIds);
                Assert.Contains(assign.ExecuteSpot, validIds);
            }
        }

        foreach (var bp in engine.TrCatalog)
        {
            Assert.Equal(5, bp.Orders.Count);
            foreach (var ord in bp.Orders)
            {
                Assert.Contains(ord.StagingSpotId, validIds);
                Assert.Contains(ord.ExecuteSpotId, validIds);
            }
        }
    }

    [Fact]
    public void ScoreCalculation_AdaptsToEconomyAndRepeatedBombHistory()
    {
        var engine = new TacticalUtilityIglEngine(BotSystemConfig.Default, seed: 7);
        var trEco = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.Terrorist,
            PurchaseIntent = BuyState.FULL_ECO,
            FinalBuyState = BuyState.FULL_ECO,
            AverageCashBeforeBuy = 1500
        };
        var ctFull = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.CounterTerrorist,
            PurchaseIntent = BuyState.FULL_BUY,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 5500
        };

        var rushB = engine.TrCatalog.First(b => b.TacticId == "TR_EXEC_B_APARTMENTS_RUSH");
        var slowDef = engine.TrCatalog.First(b => b.TacticId == "TR_SLOW_DEFAULT_MAP_CONTROL");

        var rushScore = engine.ScoreTrTactic(rushB, trEco, ctFull, Array.Empty<RoundHistoryItem>());
        var slowScore = engine.ScoreTrTactic(slowDef, trEco, ctFull, Array.Empty<RoundHistoryItem>());

        // Em FULL_ECO, Rush B de curta distância deve ter score muito maior que Slow Default
        Assert.True(rushScore.FinalScore > slowScore.FinalScore + 30.0);

        // Simula 2 ataques seguidos ao Bomb A -> deve bonificar CT_2_1_2_HEAVY_PALACE_RAMP_A e TR_FAKE_A_EXEC_B
        var history = new List<RoundHistoryItem>
        {
            new() { RoundNumber = 1, AttackedSite = "A", PlantedSite = "A", CtTacticId = "CT_STANDARD_2_1_2_BALANCED", TrTacticId = "TR_EXEC_A_PALACE_RAMP_SPLIT" },
            new() { RoundNumber = 2, AttackedSite = "A", PlantedSite = "A", CtTacticId = "CT_MID_AGGRESSIVE_DOMINANCE", TrTacticId = "TR_SPLIT_A_MID_TO_CONNECTOR" }
        };

        var ctHeavyA = engine.CtCatalog.First(b => b.TacticId == "CT_2_1_2_HEAVY_PALACE_RAMP_A");
        var ctHeavyAScore = engine.ScoreCtTactic(ctHeavyA, ctFull, trEco, history);
        Assert.Equal(25.0, ctHeavyAScore.HistoryMindgameAdjustment);

        var trFakeA = engine.TrCatalog.First(b => b.TacticId == "TR_FAKE_A_EXEC_B");
        var trFakeAScore = engine.ScoreTrTactic(trFakeA, ctFull, ctFull, history);
        Assert.Equal(25.0, trFakeAScore.HistoryMindgameAdjustment);
    }

    [Fact]
    public void RepetitionPenalty_PreventsImmediateStagnation()
    {
        var engine = new TacticalUtilityIglEngine(BotSystemConfig.Default, seed: 99);
        var econ = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.Terrorist,
            PurchaseIntent = BuyState.FULL_BUY,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 5000
        };
        var bp = engine.TrCatalog.First(b => b.TacticId == "TR_EXEC_A_PALACE_RAMP_SPLIT");

        var freshScore = engine.ScoreTrTactic(bp, econ, econ, Array.Empty<RoundHistoryItem>());
        var repeatedScore = engine.ScoreTrTactic(bp, econ, econ, new List<RoundHistoryItem>
        {
            new() { RoundNumber = 1, TrTacticId = "TR_EXEC_A_PALACE_RAMP_SPLIT", Winner = CsTeam.CounterTerrorist }
        });

        Assert.Equal(35.0, repeatedScore.RepetitionPenalty);
        Assert.True(repeatedScore.FinalScore <= freshScore.FinalScore - 35.0);
    }

    [Theory]
    [InlineData(CsTeam.Terrorist, "bora rush b tapete", "TR_EXEC_B_APARTMENTS_RUSH")]
    [InlineData(CsTeam.Terrorist, "faz fake a e vai b", "TR_FAKE_A_EXEC_B")]
    [InlineData(CsTeam.Terrorist, "split b pelo meio", "TR_SPLIT_B_MID_TO_SHORT_CATWALK")]
    [InlineData(CsTeam.CounterTerrorist, "joga 2-1-2 padrao", "CT_STANDARD_2_1_2_BALANCED")]
    [InlineData(CsTeam.CounterTerrorist, "domina meio agressivo", "CT_MID_AGGRESSIVE_DOMINANCE")]
    [InlineData(CsTeam.CounterTerrorist, "stack b no eco", "CT_ECO_STACK_GAMBLE_B")]
    public void FastLexicalCommandRouter_MatchesInstantaneously(CsTeam team, string call, string expectedId)
    {
        var engine = new TacticalUtilityIglEngine();
        bool matched = engine.TryRouteHumanCommandLexically(team, call, out string tacticId, out _);

        Assert.True(matched);
        Assert.Equal(expectedId, tacticId);
    }

    [Fact]
    public void MaterializeCtAndTrBlueprints_PreservesNon212Formations_AndIsolates5DistinctTrSlotOrders()
    {
        var mapManager = new MapProfileManager();
        string repoSrcDir = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "src", "CsBotManager"));
        mapManager.LoadProfile("de_mirage", repoSrcDir);
        var engine = new TacticalUtilityIglEngine(BotSystemConfig.Default, seed: 123);

        // 1. Verifica que CT_MID_AGGRESSIVE_DOMINANCE (1-3-1) e CT_ECO_STACK_GAMBLE_A/B (3-1-1)
        // mantêm suas formações específicas sem cair para 2-1-2 em MaterializeCt212Orders
        var midDomPlan = engine.TryMaterializeById(CsTeam.CounterTerrorist, "CT_MID_AGGRESSIVE_DOMINANCE", 1, 1, null, mapManager, 100, TacticalDecisionSource.UTILITY_AI_ENGINE)!;
        Assert.Equal(1, midDomPlan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "A"));
        Assert.Equal(3, midDomPlan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "Mid"));
        Assert.Equal(1, midDomPlan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "B"));

        var stackAPlan = engine.TryMaterializeById(CsTeam.CounterTerrorist, "CT_ECO_STACK_GAMBLE_A", 2, 2, null, mapManager, 200, TacticalDecisionSource.UTILITY_AI_ENGINE)!;
        Assert.Equal(3, stackAPlan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "A"));
        Assert.Equal(1, stackAPlan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "Mid"));
        Assert.Equal(1, stackAPlan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "B"));

        // 2. Verifica que MaterializeTrBlueprint atribui 5 ordens individuais por slot (mesmo com 2 BotRole.Rotator)
        // e que o portador da C4 nunca entra em IsNoiseGroup = true
        foreach (var trBp in engine.TrCatalog)
        {
            var trPlan = engine.TryMaterializeById(CsTeam.Terrorist, trBp.TacticId, 3, 3, null, mapManager, 300, TacticalDecisionSource.UTILITY_AI_ENGINE)!;
            TacticalOrderMaterializer.MaterializeTrOrders(trPlan, null, carrierSlot: 4, mapManager, 300);

            var slotOrders = new List<BotTacticalOrder>();
            for (int slot = 0; slot < 5; slot++)
            {
                // Mesmo passando BotRole.Rotator para dois slots diferentes, cada slot recebe sua ordem individual distinta!
                Assert.True(trPlan.TryGetOrderForBot(slot, BotRole.Rotator, out var ord));
                slotOrders.Add(ord);
            }

            // Garante 5 instâncias distintas de BotTacticalOrder
            Assert.Equal(5, slotOrders.Distinct().Count());

            // O slot 4 (carrierSlot) deve ter HasBomb=true e NUNCA IsNoiseGroup=true
            Assert.True(trPlan.TryGetOrderForBot(4, BotRole.Rotator, out var carrierOrd));
            Assert.True(carrierOrd.HasBomb);
            Assert.False(carrierOrd.IsNoiseGroup);

            if (trPlan.FakeContext != null)
            {
                Assert.Equal(4, trPlan.FakeContext.BombCarrierSlot);
                Assert.DoesNotContain(4, trPlan.FakeContext.FakeGroupSlots);
                Assert.Contains(4, trPlan.FakeContext.RealGroupSlots);
            }
        }
    }

    [Fact]
    public void CtUtilityScoring_Keeps212DominantOnNormalRounds_AndUnlocksVariationsOnLossStreak()
    {
        var engine = new TacticalUtilityIglEngine(BotSystemConfig.Default, seed: 55);
        var ctFull = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.CounterTerrorist,
            PurchaseIntent = BuyState.FULL_BUY,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 5000,
            AwpCount = 1
        };
        var trFull = new TeamEconomySnapshot
        {
            TeamSide = CsTeam.Terrorist,
            PurchaseIntent = BuyState.FULL_BUY,
            FinalBuyState = BuyState.FULL_BUY,
            AverageCashBeforeBuy = 4800
        };

        var std212 = engine.CtCatalog.First(b => b.TacticId == "CT_STANDARD_2_1_2_BALANCED");
        var midDom131 = engine.CtCatalog.First(b => b.TacticId == "CT_MID_AGGRESSIVE_DOMINANCE");

        // Quando o CT venceu o round anterior com 2-1-2, o 2-1-2 continua muito acima de 1-3-1 Mid Dominance
        var winHistory = new List<RoundHistoryItem>
        {
            new() { RoundNumber = 1, CtTacticId = "CT_STANDARD_2_1_2_BALANCED", Winner = CsTeam.CounterTerrorist, SurvivingWinnersCount = 4 }
        };

        var stdScoreAfterWin = engine.ScoreCtTactic(std212, ctFull, trFull, winHistory);
        var midScoreAfterWin = engine.ScoreCtTactic(midDom131, ctFull, trFull, winHistory);
        Assert.True(stdScoreAfterWin.FinalScore > midScoreAfterWin.FinalScore + 30.0);

        // Quando o CT perdeu 2 rounds seguidos com primeira baixa no Meio, o contra-jogo 1-3-1 Mid Dominance ganha bônus forte
        var lossStreakHistory = new List<RoundHistoryItem>
        {
            new() { RoundNumber = 1, CtTacticId = "CT_STANDARD_2_1_2_BALANCED", Winner = CsTeam.Terrorist, FirstCtDeathSector = "Mid" },
            new() { RoundNumber = 2, CtTacticId = "CT_STANDARD_2_1_2_BALANCED", Winner = CsTeam.Terrorist, FirstCtDeathSector = "Mid" }
        };

        var midScoreOnLossStreak = engine.ScoreCtTactic(midDom131, ctFull, trFull, lossStreakHistory);
        Assert.True(midScoreOnLossStreak.FinalScore >= 100.0);
    }

    [Fact]
    public void HumanCommunicationLogger_WritesBothJsonlAndTxtFiles()
    {
        string tempDir = Path.Combine(Path.GetTempPath(), $"csbot_comm_test_{Guid.NewGuid():N}");
        try
        {
            HumanCommunicationLogger.RecordCommunication(
                channel: "VOICE",
                team: CsTeam.CounterTerrorist,
                roundNumber: 5,
                rawText: "vou meio fixo",
                routedLayer: "VOICE_POSITION_SWAP",
                resultAction: "ClaimPosition(meio, fixed=true, claimed=true)",
                latencyMs: 0.01,
                customLogDir: tempDir);

            string jsonlPath = Path.Combine(tempDir, "human_communications_log.jsonl");
            string txtPath = Path.Combine(tempDir, "human_communications_log.txt");

            Assert.True(File.Exists(jsonlPath));
            Assert.True(File.Exists(txtPath));

            string jsonlContent = File.ReadAllText(jsonlPath);
            string txtContent = File.ReadAllText(txtPath);

            Assert.Contains("vou meio fixo", jsonlContent);
            Assert.Contains("VOICE_POSITION_SWAP", jsonlContent);
            Assert.Contains("[R05] [CT] [VOICE] \"vou meio fixo\"", txtContent);
        }
        finally
        {
            if (Directory.Exists(tempDir))
            {
                Directory.Delete(tempDir, recursive: true);
            }
        }
    }
}
