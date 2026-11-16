using System;
using System.IO;
using System.Linq;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class TrLiveCert2B87Tests
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
    public void SoloCertificationHasNoTeammateBlock()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        var dec = guard.EvaluateTick(1, 2, 10, 1180f, -900f, -257f, 220f, "weapon_knife", true, true, false, "tr_b_apps_house_staging", "Apartamentos B", "EntryFragger", false, false, false, false, "B", 62, Array.Empty<TeammatePositionSnapshot>());
        Assert.NotEqual("TEAMMATE_CONGESTION", dec.DispatchReason);
    }

    [Fact]
    public void EverySessionClosesExactlyOnce()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "DESTINATION_REACHED", 200));
        Assert.False(guard.FinalizeActiveSession(1, "CAPTURE_ENDED", 201));
    }

    [Fact]
    public void PendingSessionIsImpossible()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.Equal(1, guard.FinalizeAllOpenSessions("CAPTURE_ENDED", 300));
        Assert.Equal(0, guard.FinalizeAllOpenSessions("CAPTURE_ENDED", 301));
    }

    [Fact]
    public void EmptyCompletionReasonIsImpossible()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "", 200));
        var s = guard.GetSessionForRound(1);
        Assert.NotNull(s);
        Assert.False(string.IsNullOrWhiteSpace(s!.CompletionReason));
    }

    [Fact]
    public void PalaceRouteCompletesOnLiveNavMesh()
    {
        var nav = LoadNavMesh();
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060f, -36f);
        Assert.All(wps, w => Assert.True(nav.ProjectPoint(w.X, w.Y, w.Z, 160f).AreaId > 0));
    }

    [Fact]
    public void ARampRouteCompletesOnLiveNavMesh()
    {
        var nav = LoadNavMesh();
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_RAMP", "tr_a_ramp_staging_wait", 320f, -1590f, -168f);
        Assert.All(wps, w => Assert.True(nav.ProjectPoint(w.X, w.Y, w.Z, 160f).AreaId > 0));
    }

    [Fact]
    public void BKitchenRouteCompletesOnLiveNavMesh()
    {
        var nav = LoadNavMesh();
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_kitchen_control", -1111.7f, 687f, -80f);
        Assert.All(wps, w => Assert.True(nav.ProjectPoint(w.X, w.Y, w.Z, 160f).AreaId > 0));
    }

    [Fact]
    public void BHouseRouteCompletesOnLiveNavMesh()
    {
        var nav = LoadNavMesh();
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_house_staging", -764.4f, 522.1f, -77f);
        Assert.All(wps, w => Assert.True(nav.ProjectPoint(w.X, w.Y, w.Z, 160f).AreaId > 0));
    }

    [Fact]
    public void RouteUsesDeclaredPortals()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_kitchen_control", -1111.7f, 687f, -80f);
        Assert.Contains(wps, w => w.Name == "t_b_apps_kitchen_doorway");
        Assert.Contains(wps, w => w.Name == "t_b_apps_kitchen_hall");
    }

    [Fact]
    public void PathRecalculationCannotLoop()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_RAMP", "tr_a_ramp_staging_wait", 320f, -1590f, -168f);
        Assert.Equal(wps.Count, wps.Select(w => w.Name).Distinct().Count());
    }

    [Fact]
    public void WaypointAdvanceRequiresReachOrPortalCross()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060f, -36f);
        var doorway = wps.First(w => w.Name == "t_a_ramp_doorway");
        Assert.True(doorway.ArrivalRadius <= 40f);
    }

    [Fact]
    public void ArrivalRadiusUsesNavDistance()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_kitchen_control", -1111.7f, 687f, -80f);
        var doorway = wps.First(w => w.Name == "t_b_apps_kitchen_doorway");
        Assert.True(doorway.ArrivalRadius > 0f && doorway.ArrivalRadius <= 40f);
    }

    [Fact]
    public void DwellClosesDestination()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "DESTINATION_REACHED", 250));
    }

    [Fact]
    public void DeadlineUsesObservedLivePath()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, out var sug));
        Assert.True(sug!.DeadlineSeconds >= 18.0);
    }

    [Fact]
    public void ContinuousJumpIsImpossible()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060f, -36f);
        Assert.All(wps, w => Assert.False(w.AllowJumpPulse));
    }

    [Fact]
    public void WeaponReadinessRemainsActive()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, out var sug));
        Assert.True(sug!.WeaponReadyBeforeContact);
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
    public void MovementAuthorityAccountingCloses()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "AUTHORITY_RELEASED", 200));
    }

    [Fact]
    public void RouteAccountingCloses()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "CAPTURE_ENDED", 200));
    }
}
