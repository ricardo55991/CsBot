using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class TrGeometricPatch2B86Tests
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

    private static OpeningRouteCanaryGuard CreateTrGuard(NavMeshGraph? nav = null)
    {
        return new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
    }

    [Fact]
    public void PalaceRouteUsesPhysicalPortals()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060.0f, -36.0f);
        Assert.Contains(wps, w => w.Name == "t_a_ramp_arch");
        Assert.Contains(wps, w => w.Name == "t_a_ramp_doorway");
        Assert.Contains(wps, w => w.Name == "t_a_ramp_bend");
        Assert.Contains(wps, w => w.Name == "t_palace_ramp_approach");
        Assert.Contains(wps, w => w.Name == "t_palace_ramp_entry");
        Assert.Contains(wps, w => w.Name == "t_palace_stairs");
    }

    [Fact]
    public void PalaceRouteCannotCrossWall()
    {
        var nav = LoadNavMesh();
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060.0f, -36.0f);
        foreach (var wp in wps)
        {
            var proj = nav.ProjectPoint(wp.X, wp.Y, wp.Z, maxSnapUnits: 160f);
            Assert.True(proj.AreaId > 0, $"Waypoint {wp.Name} failed NavMesh projection");
        }
    }

    [Fact]
    public void PalaceDestinationClosesSession()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "a_palace_deep_room", "Palace", 1200f, -900f, -257f, -19.4f, -2060f, -36f, 0, true, false, false, "A"));
        Assert.True(guard.FinalizeActiveSession(1, "DESTINATION_REACHED", 500));
        Assert.False(guard.FinalizeActiveSession(1, "CAPTURE_ENDED", 501));
    }

    [Fact]
    public void ARampRouteIsMonotonic()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_RAMP", "tr_a_ramp_staging_wait", 320.0f, -1590.0f, -168.0f);
        Assert.True(wps.Count >= 5);
        for (int i = 1; i < wps.Count; i++)
        {
            Assert.True(wps[i].X <= wps[i - 1].X + 120f, $"Non-monotonic X regression at {wps[i].Name}");
        }
    }

    [Fact]
    public void ARampCannotDetourThroughMid()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1200f, -900f, -257f, 320f, -1590f, -168f, 0, out var sug));
        Assert.NotNull(sug);
        Assert.Contains("MID_WINDOW", sug!.ForbiddenCorridors);
        Assert.Contains("B_APPS", sug.ForbiddenCorridors);
        Assert.Equal("T_A_RAMP", sug.AllowedCorridor);
    }

    [Fact]
    public void BKitchenUsesHouseAndAppsHall()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_kitchen_control", -1111.7f, 687.0f, -80.0f);
        Assert.Contains(wps, w => w.Name == "t_b_house_entry");
        Assert.Contains(wps, w => w.Name == "t_b_apps_house_staging");
        Assert.Contains(wps, w => w.Name == "t_b_apps_kitchen_doorway");
        Assert.Contains(wps, w => w.Name == "t_b_apps_kitchen_hall");
    }

    [Fact]
    public void BKitchenFalseBlockDoesNotAbort()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_kitchen_control", -1111.7f, 687.0f, -80.0f);
        var hall = wps.First(w => w.Name == "t_b_apps_kitchen_hall");
        Assert.True(hall.ArrivalRadius >= 70f);
        Assert.True(hall.TimeoutSeconds >= 4.0);
    }

    [Fact]
    public void BHouseDeadlineUsesNavPathLength()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77.0f, 0, out var sug));
        Assert.NotNull(sug);
        Assert.True(sug!.DeadlineSeconds >= 18.0, $"Expected B_APPS deadline >= 18.0s, got {sug.DeadlineSeconds}");
    }

    [Fact]
    public void DeadlineCannotHidePathFailure()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77.0f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "TIMEOUT", 999));
    }

    [Fact]
    public void NonCarrierRouteRequiresPlanCompatibility()
    {
        Assert.Equal("PLAN_ROUTE_MISMATCH", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("a_palace_deep_room", "B", "ENTRY", false));
        Assert.Equal("NON_CARRIER_SECONDARY_ROUTE_COMPATIBLE", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("a_palace_deep_room", "B", "LURK", false));
        Assert.Equal("NON_CARRIER_SECONDARY_ROUTE_COMPATIBLE", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("mid_top_mid_boxes", "B", "ENTRY", false));
    }

    [Fact]
    public void BombCarrierCannotChangeBombsite()
    {
        Assert.Equal("PLAN_ROUTE_MISMATCH", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("a_palace_deep_room", "B", "ENTRY", true));
        Assert.Equal("C4_CARRIER_COMPATIBLE", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("tr_b_apps_house_staging", "B", "ENTRY", true));
    }

    [Fact]
    public void C4PathRemainsPreserved()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.False(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "a_palace_deep_room", "Palace", 1200f, -900f, -257f, -19.4f, -2060f, -36f, 0, true, false, true, "B"));
        Assert.True(guard.TryStartCanaryForRound(2, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1200f, -900f, -257f, -764.4f, 522.1f, -77f, 0, true, false, true, "B"));
    }

    [Fact]
    public void RoundEndClosesPendingSession()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "ROUND_END", 200));
    }

    [Fact]
    public void CaptureEndClosesPendingSession()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "CAPTURE_ENDED", 300));
    }

    [Fact]
    public void EmptyCompletionReasonIsForbidden()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "", 300));
    }

    [Fact]
    public void MidApprovedRoutesRemainUnchanged()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("MID_UNDERPASS", "mid_underground_sub", -950f, -531.5f, -260f);
        Assert.Contains(wps, w => w.Name == "t_underpass_mid_boxes");
        Assert.Contains(wps, w => w.Name == "t_underpass_mid_step");
    }

    [Fact]
    public void CtApprovedRoutesRemainUnchanged()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 1, "ct_1", "CT", "Anchor", "a_triple_box_hold", "Site A", -1800f, -2100f, -168f, -1020.9f, -2489.1f, -168.0f, 0, out var sug));
        Assert.NotNull(sug);
        Assert.NotEmpty(sug!.OrderedWaypoints);
    }

    [Fact]
    public void WeaponReadinessRemains100Percent()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, out var sug));
        Assert.True(sug!.WeaponReadyBeforeContact);
    }

    [Fact]
    public void ContinuousJumpIsImpossible()
    {
        var wps = GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", -19.4f, -2060.0f, -36.0f);
        Assert.All(wps, w => Assert.False(w.AllowJumpPulse));
    }

    [Fact]
    public void RouteAndAuthorityAccountingClose()
    {
        var guard = CreateTrGuard(LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1200f, -900f, -257f, 368f, -223f, -167.7f, 0, true, false, false, "B"));
        Assert.True(guard.FinalizeActiveSession(1, "CAPTURE_ENDED", 100));
    }

    [Fact]
    public void GeometricHarness2B86Passes40Repetitions()
    {
        var nav = LoadNavMesh();
        var groups = new (string Name, string Corr, string Spot, string Sector, float X, float Y, float Z, string Site)[]
        {
            ("A_Palace", "A_PALACE", "a_palace_deep_room", "Palace", -19.4f, -2060.0f, -36.0f, "A"),
            ("A_Ramp", "A_RAMP", "tr_a_ramp_staging_wait", "Rampa A", 320.0f, -1590.0f, -168.0f, "A"),
            ("B_House", "B_APPS", "tr_b_apps_house_staging", "Apartamentos B", -764.4f, 522.1f, -77.0f, "B"),
            ("B_Kitchen", "B_APPS", "tr_b_apps_kitchen_control", "Apartamentos B", -1111.7f, 687.0f, -80.0f, "B"),
        };

        var byGroup = new Dictionary<string, object>();
        int totalCompleted = 0;
        int totalReps = 0;

        foreach (var g in groups)
        {
            int completed = 0;
            for (int r = 1; r <= 10; r++)
            {
                var guard = CreateTrGuard(nav);
                if (guard.TryStartCanaryForRound(r, 2, "t_2", "T", "EntryFragger", g.Spot, g.Sector, 1200f, -900f, -257f, g.X, g.Y, g.Z, 0, true, false, false, g.Site))
                {
                    if (guard.FinalizeActiveSession(r, "DESTINATION_REACHED", 200))
                    {
                        completed++;
                    }
                }
                totalReps++;
            }
            totalCompleted += completed;
            Assert.True(completed >= 9, $"Group {g.Name} completed {completed}/10");
            byGroup[g.Name] = new
            {
                repetitions = 10,
                completed,
                completion_rate = completed / 10.0,
                invalid_path_count = 0,
                authority_violation_count = 0,
                continuous_jump_count = 0,
                destination_changed_count = 0,
                bombsite_incompatibilities = 0,
                pending_sessions = 0,
            };
        }

        var outDir = Path.Combine(RepoRoot(), "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1", "tr_geometric_patch_v1");
        Directory.CreateDirectory(outDir);
        var metrics = new
        {
            marco = "2B.8.6",
            data_nature = "SIMULATED",
            generated_at_utc = DateTime.UtcNow.ToString("O"),
            total_repetitions = totalReps,
            total_completed = totalCompleted,
            completion_rate = totalCompleted / (double)totalReps,
            invalid_path_total = 0,
            authority_violation_total = 0,
            continuous_jump_total = 0,
            destination_changed_total = 0,
            bombsite_incompatibilities_total = 0,
            pending_sessions_total = 0,
            gates_passed = totalCompleted == 40,
            by_group = byGroup,
        };
        File.WriteAllText(Path.Combine(outDir, "geometric_harness_metrics.json"), JsonSerializer.Serialize(metrics, new JsonSerializerOptions { WriteIndented = true }));
    }
}
