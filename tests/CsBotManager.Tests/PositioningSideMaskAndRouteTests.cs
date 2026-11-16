using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public sealed class PositioningSideMaskAndRouteTests
{
    private static readonly string RepoRoot = FindRepoRoot();
    private static readonly string SideContractPath = Path.Combine(
        RepoRoot, "training_runs", "positioning_v2_real_temporal", "csharp_shadow_integration", "side_mask_route_fix", "spot_side_contract_v1.json");
    private static readonly string ModelPath = Path.Combine(
        RepoRoot, "models", "positioning", "de_mirage_positioning_hybrid_v1_candidate.onnx");
    private static readonly string ManifestPath = Path.Combine(
        RepoRoot, "training_runs", "positioning_v2_real_temporal", "csharp_shadow_integration", "model_deployment_manifest.json");

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "AGENTS.md"))) return dir.FullName;
            dir = dir.Parent;
        }
        throw new InvalidOperationException("Repo root not found.");
    }

    private static string ReadExpectedSha256()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(ManifestPath));
        return doc.RootElement.GetProperty("sha256").GetString()!;
    }

    [Fact]
    public void CtCannotSelectTOnlySpot()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(SideContractPath));
        var ctMask = PositioningTransformerContract.BuildSideAwareCandidateMask(isTerrorist: false);
        foreach (var sp in doc.RootElement.GetProperty("spots").EnumerateArray())
        {
            int idx = sp.GetProperty("index").GetInt32();
            string sideClass = sp.GetProperty("side_class").GetString()!;
            if (sideClass == "T_ONLY")
            {
                Assert.False(ctMask[idx]);
            }
        }

        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, ReadExpectedSha256()));
        var inp = new PositioningShadowInferenceInput
        {
            BatchSize = 1,
            MapName = "de_mirage",
            RoundId = 1,
            SelfHistory = new float[32 * 18],
            Teammates = new float[32 * 4 * 18],
            TemporalMask = Enumerable.Repeat(1.0f, 32).ToArray(),
            TeammateMask = new float[32 * 4],
            CandidateMask = ctMask,
            ObjectiveEligible = new[] { false },
            RetakeEligible = new[] { false },
            PlayerAlive = new[] { true },
        };
        var preds = svc.PredictShadowBatch(inp);
        Assert.True(preds[0].InferenceSuccess);
        Assert.True(ctMask[preds[0].SelectedSpotId!.Value]);
    }

    [Fact]
    public void TCannotSelectCtOnlySpot()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(SideContractPath));
        var tMask = PositioningTransformerContract.BuildSideAwareCandidateMask(isTerrorist: true);
        foreach (var sp in doc.RootElement.GetProperty("spots").EnumerateArray())
        {
            int idx = sp.GetProperty("index").GetInt32();
            string sideClass = sp.GetProperty("side_class").GetString()!;
            if (sideClass == "CT_ONLY")
            {
                Assert.False(tMask[idx]);
            }
        }

        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, ReadExpectedSha256()));
        var inp = new PositioningShadowInferenceInput
        {
            BatchSize = 1,
            MapName = "de_mirage",
            RoundId = 1,
            SelfHistory = new float[32 * 18],
            Teammates = new float[32 * 4 * 18],
            TemporalMask = Enumerable.Repeat(1.0f, 32).ToArray(),
            TeammateMask = new float[32 * 4],
            CandidateMask = tMask,
            ObjectiveEligible = new[] { false },
            RetakeEligible = new[] { false },
            PlayerAlive = new[] { true },
        };
        var preds = svc.PredictShadowBatch(inp);
        Assert.True(preds[0].InferenceSuccess);
        Assert.True(tMask[preds[0].SelectedSpotId!.Value]);
    }

    [Fact]
    public void SharedSpotRemainsEligible()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(SideContractPath));
        var ctMask = PositioningTransformerContract.BuildSideAwareCandidateMask(isTerrorist: false);
        var tMask = PositioningTransformerContract.BuildSideAwareCandidateMask(isTerrorist: true);
        int sharedCount = 0;
        foreach (var sp in doc.RootElement.GetProperty("spots").EnumerateArray())
        {
            int idx = sp.GetProperty("index").GetInt32();
            if (sp.GetProperty("side_class").GetString() == "SHARED")
            {
                sharedCount++;
                Assert.True(ctMask[idx]);
                Assert.True(tMask[idx]);
            }
        }
        Assert.True(sharedCount > 0);
    }

    [Fact]
    public void CandidateMaskMatchesPythonAndCSharp()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(SideContractPath));
        bool[] pyCt = doc.RootElement.GetProperty("ct_allowed_mask").EnumerateArray().Select(e => e.GetBoolean()).ToArray();
        bool[] pyT = doc.RootElement.GetProperty("t_allowed_mask").EnumerateArray().Select(e => e.GetBoolean()).ToArray();
        bool[] csCt = PositioningTransformerContract.BuildSideAwareCandidateMask(isTerrorist: false);
        bool[] csT = PositioningTransformerContract.BuildSideAwareCandidateMask(isTerrorist: true);
        Assert.Equal(pyCt, csCt);
        Assert.Equal(pyT, csT);
    }

    [Fact]
    public void OneOpeningRoutePerPlayerPerRound()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        Assert.True(tracker.TryRegisterAssignment(1, 2, "slot_a", "CT", "spot_1", 0, 0, 0, 500, 0, 0, 90, 104, false));
        Assert.False(tracker.TryRegisterAssignment(1, 2, "slot_a", "CT", "spot_2", 10, 0, 0, 800, 0, 0, 90, 140, false));
        Assert.Equal(1, tracker.TotalOpeningRoutesCreated);
    }

    [Fact]
    public void MidroundRepathIsNotOpeningRoute()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        Assert.True(tracker.TryRegisterAssignment(1, 3, "slot_b", "T", "spot_a", 0, 0, 0, 500, 0, 0, 90, 104, false));
        // Chamada repetida com mesmo spot e tipo é deduplicada (RepeatedEventDuplicates)
        Assert.False(tracker.TryRegisterAssignment(1, 3, "slot_b", "T", "spot_a", 25, 0, 0, 500, 0, 0, 90, 120, false, PostOpeningRepathKind.MIDROUND_REPATH));
        Assert.Equal(1, tracker.RepeatedEventDuplicates);
        Assert.Equal(0, tracker.PostOpeningRepathCounts[PostOpeningRepathKind.MIDROUND_REPATH]);
        // Mudança real de spot após opening conta como MIDROUND_REPATH único sem criar novo opening route
        Assert.False(tracker.TryRegisterAssignment(1, 3, "slot_b", "T", "spot_b", 50, 0, 0, 700, 0, 0, 90, 160, false, PostOpeningRepathKind.MIDROUND_REPATH));
        Assert.Equal(1, tracker.TotalOpeningRoutesCreated);
        Assert.Equal(1, tracker.PostOpeningRepathCounts[PostOpeningRepathKind.MIDROUND_REPATH]);
    }

    [Fact]
    public void TacticalRedirectIsNotNotReached()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        tracker.TryRegisterAssignment(1, 4, "slot_c", "CT", "spot_a", 0, 0, 0, 500, 0, 0, 90, 104, false);
        tracker.TryRegisterAssignment(1, 4, "slot_c", "CT", "spot_b", 200, 0, 0, 800, 800, 0, 90, 180, false, PostOpeningRepathKind.TACTICAL_ROTATION);
        Assert.Single(tracker.ClosedRoutes);
        Assert.Equal(OpeningRouteTerminationReason.TACTICAL_REDIRECT, tracker.ClosedRoutes[0].TerminationReason);
        Assert.Equal(OpeningRouteClassification.TACTICAL_REDIRECT, tracker.ClosedRoutes[0].Classification);
    }

    [Fact]
    public void PlayerDeathClosesRoute()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        tracker.TryRegisterAssignment(1, 5, "slot_d", "T", "spot_a", 0, 0, 0, 500, 0, 0, 90, 104, false);
        tracker.UpdateTick(1, 5, 130, isAlive: false, 100, 0, 0, "weapon_ak47");
        Assert.Single(tracker.ClosedRoutes);
        Assert.Equal(OpeningRouteTerminationReason.PLAYER_DEATH, tracker.ClosedRoutes[0].TerminationReason);
        Assert.Equal(OpeningRouteClassification.PLAYER_DEATH, tracker.ClosedRoutes[0].Classification);
        Assert.Equal(0, tracker.ComputeAccountingResidue());
    }

    [Fact]
    public void RoundEndClosesRoute()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        tracker.TryRegisterAssignment(1, 6, "slot_e", "CT", "spot_a", 0, 0, 0, 500, 0, 0, 90, 104, false);
        tracker.CloseAllOpenRoutes(1, OpeningRouteTerminationReason.ROUND_END, 500);
        Assert.Single(tracker.ClosedRoutes);
        Assert.Equal(OpeningRouteTerminationReason.ROUND_END, tracker.ClosedRoutes[0].TerminationReason);
        Assert.Equal(0, tracker.ComputeAccountingResidue());
    }

    [Fact]
    public void ArrivalRequiresRadiusAndDwell()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        tracker.TryRegisterAssignment(1, 7, "slot_f", "CT", "spot_a", 0, 0, 0, 500, 0, 0, 90, 104, false);

        // Entra no raio por apenas 1 tick -> não deve fechar ainda
        tracker.UpdateTick(1, 7, 140, true, 490, 0, 0, "weapon_knife");
        Assert.Empty(tracker.ClosedRoutes);

        // Permanece no raio pelos 16 ticks exigidos -> fecha ON_TIME
        for (int i = 1; i <= 16; i++)
        {
            tracker.UpdateTick(1, 7, 140 + i * 4, true, 495, 0, 0, "weapon_ak47");
        }
        Assert.Single(tracker.ClosedRoutes);
        Assert.Equal(OpeningRouteTerminationReason.TARGET_REACHED, tracker.ClosedRoutes[0].TerminationReason);
        Assert.Equal(OpeningRouteClassification.ON_TIME, tracker.ClosedRoutes[0].Classification);
        Assert.NotNull(tracker.ClosedRoutes[0].WeaponSwitchTick);
    }

    [Fact]
    public void FreezeTimeIsExcluded()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        Assert.False(tracker.TryRegisterAssignment(1, 8, "slot_g", "T", "spot_a", 0, 0, 0, 500, 0, 0, 90, 50, isFreezeTime: true));
        Assert.Equal(0, tracker.TotalOpeningRoutesCreated);
    }

    [Fact]
    public void ShadowModeCannotAffectDecisions()
    {
        string utilityDecision = "ROTATE_TO_B";
        var pred = new PositioningShadowPrediction { InferenceSuccess = true, SelectedSpotId = 12 };
        Assert.Equal(utilityDecision, ShadowModeGuard.ShadowModeCannotAffectBotDecision(utilityDecision, pred));
    }
}
