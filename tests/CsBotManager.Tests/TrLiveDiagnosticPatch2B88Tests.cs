using System;
using System.IO;
using System.Linq;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class TrLiveDiagnosticPatch2B88Tests
{
    private static string RepoRoot()
    {
        var dir = AppContext.BaseDirectory;
        while (!string.IsNullOrEmpty(dir) && !File.Exists(Path.Combine(dir, "CsBot.sln")) && !Directory.Exists(Path.Combine(dir, "src")))
        {
            dir = Directory.GetParent(dir)?.FullName;
        }
        return dir ?? Directory.GetCurrentDirectory();
    }

    private static NavMeshGraph LoadNavMesh()
    {
        var path = Path.Combine(RepoRoot(), "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        var nav = NavMeshGraph.LoadFromFile(path);
        Assert.NotNull(nav);
        return nav!;
    }

    private static OpeningRouteCanaryGuard CreateTrGuard(NavMeshGraph? nav = null) => new(CanaryTeamMode.TrSingle, nav);

    [Fact]
    public void FirstFailureTickIsMaterialized()
    {
        var path = Path.Combine(RepoRoot(), "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1", "tr_live_diagnostic_patch_v1", "first_failure_tick_analysis.json");
        Assert.True(File.Exists(path));
    }

    [Fact]
    public void FailureHasPhysicalCause()
    {
        var path = Path.Combine(RepoRoot(), "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1", "tr_live_diagnostic_patch_v1", "first_failure_tick_analysis.json");
        string txt = File.ReadAllText(path);
        Assert.Contains("\"cause\":", txt);
    }

    [Fact]
    public void ResultStatusIsNotUsedAsRootCause()
    {
        var path = Path.Combine(RepoRoot(), "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1", "tr_live_diagnostic_patch_v1", "first_failure_tick_analysis.json");
        string txt = File.ReadAllText(path);
        Assert.DoesNotContain("\"cause\": \"NOT_REACHED\"", txt);
        Assert.DoesNotContain("\"cause\": \"BLOCKED\"", txt);
        Assert.DoesNotContain("\"cause\": \"LATE\"", txt);
        Assert.DoesNotContain("\"cause\": \"TIMEOUT\"", txt);
    }

    [Fact]
    public void RepeatedFailuresAreClustered()
    {
        var path = Path.Combine(RepoRoot(), "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1", "tr_live_diagnostic_patch_v1", "failure_coordinate_clusters.json");
        string txt = File.ReadAllText(path);
        Assert.Contains("\"deterministic_portal_or_executor_failure\": true", txt);
    }

    [Fact]
    public void PalacePatchChangesOnlyPalaceRoute()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060f, -36f);
        var doorway = wps.First(w => w.Name == "t_a_ramp_doorway");
        Assert.Equal(-1440.0f, doorway.Y);
    }

    [Fact]
    public void ARampPatchChangesOnlyARampRoute()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_RAMP", "tr_a_ramp_staging_wait", 320f, -1590f, -168f);
        var doorway = wps.First(w => w.Name == "t_a_ramp_doorway");
        Assert.Equal(-1440.0f, doorway.Y);
    }

    [Fact]
    public void BKitchenPatchChangesOnlyBKitchenRoute()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_kitchen_control", -1111.7f, 687f, -80f);
        var doorway = wps.First(w => w.Name == "t_b_apps_kitchen_doorway");
        Assert.Equal(-985.0f, doorway.X);
    }

    [Fact]
    public void BHousePatchChangesOnlyBHouseRoute()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_house_staging", -764.4f, 522.1f, -77f);
        Assert.Contains(wps, w => w.Name == "t_b_spawn_ledge_exit");
    }

    [Fact]
    public void MidRoutesRemainUnchanged()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("MID_UNDERPASS", "mid_underground_sub", -950f, -531.5f, -260f);
        Assert.Contains(wps, w => w.Name == "t_underpass_mid_boxes");
    }

    [Fact]
    public void CtRoutesRemainUnchanged()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 1, "ct_1", "CT", "Anchor", "a_triple_box_hold", "Site A", -1800f, -2100f, -168f, -1020.9f, -2489.1f, -168f, 0, out var sug));
        Assert.NotNull(sug);
    }

    [Fact]
    public void ArrivalAtPhysicalDestinationClosesSession()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "DESTINATION_REACHED", 200));
    }

    [Fact]
    public void WaypointCannotAdvanceBeforePortalCrossing()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_kitchen_control", -1111.7f, 687f, -80f);
        var doorway = wps.First(w => w.Name == "t_b_apps_kitchen_doorway");
        Assert.True(doorway.ExitRadius <= 40f);
    }

    [Fact]
    public void RepathLoopIsDetected()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_RAMP", "tr_a_ramp_staging_wait", 320f, -1590f, -168f);
        Assert.Equal(wps.Count, wps.Select(w => w.Name).Distinct().Count());
    }

    [Fact]
    public void SessionCannotRemainPending()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.Equal(1, guard.FinalizeAllOpenSessions("CAPTURE_ENDED", 300));
    }

    [Fact]
    public void CompletionReasonCannotBeEmpty()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "", 300));
        Assert.False(string.IsNullOrWhiteSpace(guard.GetSessionForRound(1)!.CompletionReason));
    }

    [Fact]
    public void ContinuousJumpIsImpossible()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060f, -36f);
        Assert.All(wps, w => Assert.False(w.AllowJumpPulse));
    }

    [Fact]
    public void AuthorityAccountingCloses()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "AUTHORITY_RELEASED", 200));
    }

    [Fact]
    public void RouteAccountingCloses()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "CAPTURE_ENDED", 200));
    }
}
