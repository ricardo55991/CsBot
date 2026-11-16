using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Microsoft.ML.OnnxRuntime;
using Xunit;

namespace CsBotManager.Tests;

public sealed class UtilityPatchAndDeployV2Tests
{
    private static readonly string RepoRoot = FindRepoRoot();
    private static readonly string SmokeOutDir = Path.Combine(
        RepoRoot, "training_runs", "positioning_v2_real_temporal", "csharp_shadow_integration", "onnx_v2_utility_patch_smoke");
    private static readonly string MirageProfilePath = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage.json");
    private static readonly string DeployRepoV2Path = Path.Combine(RepoRoot, "models", "positioning", "de_mirage_positioning_hybrid_v2.onnx");

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "AGENTS.md"))) return dir.FullName;
            dir = dir.Parent;
        }
        return Directory.GetCurrentDirectory();
    }

    private static IReadOnlyList<TacticalSpot> LoadMirageSpots()
    {
        var json = File.ReadAllText(MirageProfilePath);
        using var doc = JsonDocument.Parse(json);
        var opts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        return JsonSerializer.Deserialize<List<TacticalSpot>>(doc.RootElement.GetProperty("spots").GetRawText(), opts)!;
    }

    [Fact]
    public void AllCatalogReviewSpotsAreResolved()
    {
        string path = Path.Combine(SmokeOutDir, "spot_catalog_review_resolution.json");
        Assert.True(File.Exists(path));
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        Assert.Equal("ALL_CATALOG_REVIEW_SPOTS_RESOLVED", doc.RootElement.GetProperty("status").GetString());
        Assert.Equal(4, doc.RootElement.GetProperty("resolved_count").GetInt32());
        Assert.Equal(0, doc.RootElement.GetProperty("unresolved_count").GetInt32());
    }

    [Fact]
    public void UtilityCtCannotAssignTOnlySpot()
    {
        var spots = LoadMirageSpots();
        var tOnly = spots.First(s => s.Id == "tr_b_apps_kitchen_control");
        var ctx = new UtilitySpotValidationContext { RequestedSide = "CT", RequestedState = "HOLD", RequestedPhase = "MapControl" };
        var res = UtilitySpotAssignmentValidator.ValidateAndResolve(tOnly, ctx, spots);
        Assert.NotEqual("VALID", res.ValidationResult);
        Assert.Equal(SpotAssignmentRejectionReason.WRONG_SIDE, res.RejectionReason);
        Assert.NotNull(res.ApprovedSpot);
        Assert.NotEqual("tr_b_apps_kitchen_control", res.ApprovedSpot!.Id);
    }

    [Fact]
    public void UtilityTCannotAssignCtOnlySpot()
    {
        var spots = LoadMirageSpots();
        var ctOnly = spots.First(s => s.Id == "ct_retake_a_jungle_entry_site");
        var ctx = new UtilitySpotValidationContext { RequestedSide = "TR", RequestedState = "HOLD", RequestedPhase = "MapControl" };
        var res = UtilitySpotAssignmentValidator.ValidateAndResolve(ctOnly, ctx, spots);
        Assert.Equal("REPLACED", res.ValidationResult);
        Assert.Equal(SpotAssignmentRejectionReason.WRONG_SIDE, res.RejectionReason);
        Assert.True(UtilitySpotAssignmentValidator.ValidateCandidate(res.ApprovedSpot, ctx).IsValid);
    }

    [Fact]
    public void ContextualSpotRequiresValidState()
    {
        var spots = LoadMirageSpots();
        var conn = spots.First(s => s.Id == "mid_connector_top_stairs");
        var badCtx = new UtilitySpotValidationContext { RequestedSide = "CT", RequestedState = "TRANSIT", RequestedPhase = "Free" };
        Assert.False(UtilitySpotAssignmentValidator.ValidateCandidate(conn, badCtx).IsValid);
        var okCtx = new UtilitySpotValidationContext { RequestedSide = "CT", RequestedState = "HOLD", RequestedPhase = "Setup" };
        Assert.True(UtilitySpotAssignmentValidator.ValidateCandidate(conn, okCtx).IsValid);
    }

    [Fact]
    public void ContextualSpotRequiresValidPhase()
    {
        var spots = LoadMirageSpots();
        var plantBox = spots.First(s => s.Id == "b_site_default_plant_box");
        var badCtPhase = new UtilitySpotValidationContext
        {
            RequestedSide = "CT", RequestedState = "HOLD", RequestedPhase = "FAST_CONTACT",
            IsBombPlanted = false, RetakeEligible = false,
        };
        var chk = UtilitySpotAssignmentValidator.ValidateCandidate(plantBox, badCtPhase);
        Assert.False(chk.IsValid);
        Assert.Equal(SpotAssignmentRejectionReason.WRONG_PHASE, chk.Reason);

        var okCtRetake = new UtilitySpotValidationContext
        {
            RequestedSide = "CT", RequestedState = "RETAKE", RequestedPhase = "Retake",
            IsBombPlanted = true, RetakeEligible = true,
        };
        Assert.True(UtilitySpotAssignmentValidator.ValidateCandidate(plantBox, okCtRetake).IsValid);
    }

    [Fact]
    public void InvalidAssignmentIsRejected()
    {
        var spots = LoadMirageSpots();
        var ctRetake = spots.First(s => s.Id == "ct_retake_b_door_exit_straight");
        var ctx = new UtilitySpotValidationContext { RequestedSide = "TR", RequestedState = "HOLD", RequestedPhase = "MapControl" };
        var res = UtilitySpotAssignmentValidator.ValidateAndResolve(ctRetake, ctx, spots);
        Assert.Equal("REPLACED", res.ValidationResult);
        Assert.Equal(SpotAssignmentRejectionReason.WRONG_SIDE, res.RejectionReason);
        Assert.False(string.IsNullOrEmpty(res.ReplacementSpot));
    }

    [Fact]
    public void ReplacementPreservesSector()
    {
        var spots = LoadMirageSpots();
        var badB = spots.First(s => s.Id == "ct_retake_b_door_exit_straight");
        var ctx = new UtilitySpotValidationContext { RequestedSide = "TR", RequestedState = "HOLD", RequestedPhase = "MapControl", Role = "Rotator" };
        var res = UtilitySpotAssignmentValidator.ValidateAndResolve(badB, ctx, spots);
        Assert.NotNull(res.ApprovedSpot);
        Assert.Equal(badB.AssociatedBombsite, res.ApprovedSpot!.AssociatedBombsite);
    }

    [Fact]
    public void ReplacementPreservesRole()
    {
        var spots = LoadMirageSpots();
        var badB = spots.First(s => s.Id == "ct_retake_b_door_exit_straight");
        var ctx = new UtilitySpotValidationContext { RequestedSide = "TR", RequestedState = "HOLD", RequestedPhase = "MapControl", Role = "EntryFragger" };
        var res = UtilitySpotAssignmentValidator.ValidateAndResolve(badB, ctx, spots);
        Assert.NotNull(res.ApprovedSpot);
        Assert.Contains("Entry", res.ApprovedSpot!.AllowedRoles.Select(r => r.ToString()), StringComparer.OrdinalIgnoreCase);
    }

    [Fact]
    public void NoValidAlternativeUsesSafeFallback()
    {
        var ctOnlyList = new List<TacticalSpot>
        {
            new() { Id = "ct_a_stairs", Side = "CT", Sector = "Bombsite A", AssociatedBombsite = "A" },
            new() { Id = "tr_spawn_safe", Side = "TR", Sector = "Base TR", AssociatedBombsite = "None" }
        };
        var ctx = new UtilitySpotValidationContext { RequestedSide = "TR", RequestedState = "HOLD", RequestedPhase = "MapControl" };
        var res = UtilitySpotAssignmentValidator.ValidateAndResolve(ctOnlyList[0], ctx, ctOnlyList);
        Assert.Equal("FALLBACK", res.ValidationResult);
        Assert.True(res.FallbackUsed);
        Assert.Equal("NO_VALID_ALTERNATIVE", res.ReplacementReason);
        Assert.Equal("tr_spawn_safe", res.ApprovedSpot?.Id);
    }

    [Fact]
    public void OnnxV2HashMatchesDeployment()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(SmokeOutDir, "model_deployment_manifest.json")));
        string expected = doc.RootElement.GetProperty("sha256").GetString()!;
        Assert.Equal(expected, PositioningTransformerService.ComputeFileSha256(DeployRepoV2Path));
        string srvPath = @"H:\CS2_AI_Server\models\positioning\de_mirage_positioning_hybrid_v2.onnx";
        if (File.Exists(srvPath))
        {
            Assert.Equal(expected, PositioningTransformerService.ComputeFileSha256(srvPath));
        }
    }

    [Fact]
    public void OnnxV2ContainsContextualInputs()
    {
        using var sess = new InferenceSession(DeployRepoV2Path);
        Assert.True(sess.InputMetadata.ContainsKey("team_idx"));
        Assert.True(sess.InputMetadata.ContainsKey("role_idx"));
        Assert.True(sess.InputMetadata.ContainsKey("stage_idx"));
    }

    [Fact]
    public void TeamMappingMatchesPython()
    {
        Assert.Equal(0L, PositioningTransformerContract.MapTeamToIndex(3, out bool fbCt));
        Assert.False(fbCt);
        Assert.Equal(1L, PositioningTransformerContract.MapTeamToIndex(2, out bool fbTr));
        Assert.False(fbTr);
        Assert.Equal(2L, PositioningTransformerContract.MapTeamToIndex(0, out bool fbAny));
        Assert.True(fbAny);
    }

    [Fact]
    public void RoleMappingMatchesPython()
    {
        Assert.Equal(0L, PositioningTransformerContract.MapRoleToIndex("SUPPORT", out _));
        Assert.Equal(1L, PositioningTransformerContract.MapRoleToIndex("BOMB_CARRIER", out _));
        Assert.Equal(3L, PositioningTransformerContract.MapRoleToIndex("ANCHOR", out _));
        Assert.Equal(5L, PositioningTransformerContract.MapRoleToIndex("ENTRY", out _));
        Assert.Equal(7L, PositioningTransformerContract.MapRoleToIndex("AWPER", out _));
        Assert.Equal(8L, PositioningTransformerContract.MapRoleToIndex("ROTATOR", out _));
    }

    [Fact]
    public void StageMappingMatchesPython()
    {
        Assert.Equal(0L, PositioningTransformerContract.MapStageToIndex("MapControl", out _));
        Assert.Equal(1L, PositioningTransformerContract.MapStageToIndex("Staging", out _));
        Assert.Equal(2L, PositioningTransformerContract.MapStageToIndex("Contact", out _));
        Assert.Equal(3L, PositioningTransformerContract.MapStageToIndex("Setup", out _));
        Assert.Equal(4L, PositioningTransformerContract.MapStageToIndex("PostPlant", out _));
        Assert.Equal(5L, PositioningTransformerContract.MapStageToIndex("Retake", out _));
    }

    [Fact]
    public void WarmupCoversBatchesOneThroughFive()
    {
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(DeployRepoV2Path));
        Assert.True(svc.IsReady);
        Assert.True(svc.SupportsContextualInputs);
        Assert.Equal(5, svc.WarmupBatchMetrics.Count);
        Assert.All(svc.WarmupBatchMetrics, m => Assert.True(m.Success && m.OutputBoundsValid));
    }

    [Fact]
    public void ShadowModeCannotAffectBotDecision()
    {
        var pred = new PositioningShadowPrediction { InputValid = true, InferenceSuccess = true, SelectedSpotId = 3 };
        Assert.Equal("UTILITY_KEEP", ShadowModeGuard.ShadowModeCannotAffectBotDecision("UTILITY_KEEP", pred));
    }

    [Fact]
    public void OpeningRouteAccountingStillCloses()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(50);
        Assert.True(tracker.TryRegisterAssignment(1, 0, "p0", "CT", "ct_a_stairs_cross", 0, 0, 0, 100, 0, 0, 64, 51, false));
        tracker.CloseAllOpenRoutes(1, OpeningRouteTerminationReason.ROUND_END, 200);
        Assert.Equal(0, tracker.ComputeAccountingResidue());
    }

    [Fact]
    public void RepathEventsRemainDeduplicated()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(50);
        Assert.True(tracker.TryRegisterAssignment(1, 0, "p0", "CT", "ct_a_stairs_cross", 0, 0, 0, 100, 0, 0, 64, 51, false));
        for (int i = 0; i < 20; i++)
        {
            Assert.False(tracker.TryRegisterAssignment(1, 0, "p0", "CT", "ct_a_stairs_cross", 0, 0, 0, 100, 0, 0, 64, 52 + i, false));
        }
        Assert.Equal(0, tracker.UniqueMidroundRepaths);
        Assert.Equal(20, tracker.RepeatedEventDuplicates);
    }
}
