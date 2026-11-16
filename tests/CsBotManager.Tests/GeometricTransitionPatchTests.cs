using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Xunit;

namespace CsBotManager.Tests;

public class GeometricTransitionPatchTests
{
    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "src", "CsBotManager", "CsBotManager.csproj")))
                return dir.FullName;
            dir = dir.Parent;
        }
        return @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot";
    }

    private static NavMeshGraph LoadNavMesh()
    {
        if (NavMeshGraph.Default != null) return NavMeshGraph.Default;
        var path = Path.Combine(FindRepoRoot(), "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return NavMeshGraph.LoadFromFile(path);
    }

    private static string PatchDir()
    {
        var dir = Path.Combine(
            FindRepoRoot(),
            "training_runs",
            "positioning_v2_real_temporal",
            "opening_route_canary_v1",
            "geometric_transition_patch_v1");
        Directory.CreateDirectory(dir);
        return dir;
    }

    private static OpeningRouteSuggestion PlanCt(string spotId, float sx, float sy, float sz, float tx, float ty, float tz, string sector, string role)
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 1, "ct_test", "CT", role, spotId, sector, sx, sy, sz, tx, ty, tz, 100, out var suggestion));
        return suggestion!;
    }

    [Fact]
    public void ApprovedARoutesRemainUnchanged()
    {
        var snapPath = Path.Combine(PatchDir(), "approved_route_regression_snapshot.json");
        Assert.True(File.Exists(snapPath), "Snapshot das rotas A aprovadas deve existir.");
        using var doc = JsonDocument.Parse(File.ReadAllText(snapPath));
        var ticketTpl = doc.RootElement.GetProperty("protected_templates").GetProperty("CT:A_TICKET");
        var jungleTpl = doc.RootElement.GetProperty("protected_templates").GetProperty("CT:A_JUNGLE");

        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 1, "ct_a1", "CT", "Rotator", "a_triple_box_hold", "Bombsite A", -1380f, -2060f, -264f, -660.9f, -2198.9f, -180.0f, 100, out var triple));
        Assert.True(planner.TryPlanOpeningRouteForRound(2, 1, "ct_a2", "CT", "Anchor", "a_firebox_ninja_hold", "Bombsite A", -1420f, -2100f, -264f, -1100f, -2200f, -168f, 100, out var firebox));
        Assert.True(planner.TryPlanOpeningRouteForRound(3, 1, "ct_a3", "CT", "Rotator", "a_jungle_stairs_hold", "A - Selva", -1410f, -2050f, -264f, -1180f, -1440f, -168f, 100, out var jungle));
        Assert.True(planner.TryPlanOpeningRouteForRound(4, 1, "ct_a4", "CT", "Anchor", "ct_a_sand_pit_under_palace_hold_caverna", "Bombsite A", -1450f, -2040f, -264f, -900f, -1950f, -168f, 100, out var caverna));

        foreach (var route in new[] { triple!, firebox!, jungle!, caverna! })
        {
            Assert.Empty(route.TransitionWaypoints);
        }

        Assert.Equal("CT_A_TICKET", triple!.AllowedCorridor);
        Assert.Equal(2, triple.OrderedWaypoints.Count);
        Assert.Equal(ticketTpl.GetProperty("waypoints")[0].GetProperty("x").GetDouble(), triple.OrderedWaypoints[0].X, 2);
        Assert.Equal(ticketTpl.GetProperty("waypoints")[0].GetProperty("y").GetDouble(), triple.OrderedWaypoints[0].Y, 2);
        Assert.Equal(ticketTpl.GetProperty("waypoints")[0].GetProperty("z").GetDouble(), triple.OrderedWaypoints[0].Z, 2);
        Assert.Equal("a_triple_box_hold", triple.OrderedWaypoints[1].Name);

        Assert.Equal("CT_JUNGLE_STAIRS", jungle!.AllowedCorridor);
        Assert.Equal(jungleTpl.GetProperty("waypoints")[0].GetProperty("x").GetDouble(), jungle.OrderedWaypoints[0].X, 2);
    }

    [Fact]
    public void EveryTransitionWaypointProjectsToNavMesh()
    {
        var nav = LoadNavMesh();
        var window = PlanCt("mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, "Janela do Meio", "AWPer");
        var market = PlanCt("b_short_pillar_hold_apps", -1760f, -1420f, -200f, -1463.8f, 179.5f, -167.0f, "Bombsite B", "Rotator");
        var bench = PlanCt("b_forest_bench_hold_apps", -1760f, -1420f, -200f, -2531.3f, 274.1f, -168.0f, "Bombsite B", "Anchor");
        var van = PlanCt("b_van_behind_apps_hold", -1760f, -1420f, -200f, -1981.9f, 702.6f, -48.0f, "Bombsite B", "Anchor");

        foreach (var suggestion in new[] { window, market, bench, van })
        {
            Assert.NotEmpty(suggestion.TransitionWaypoints);
            foreach (var tw in suggestion.TransitionWaypoints)
            {
                var proj = nav.ProjectPoint(tw.X, tw.Y, tw.Z, maxSnapUnits: 32f);
                Assert.True(proj.AreaId > 0, $"Waypoint {tw.Name} falhou projeção");
                Assert.True(proj.DeltaUnits <= 32f, $"Waypoint {tw.Name} excedeu 32u de projeção ({proj.DeltaUnits:F1}u)");
            }
        }
    }

    [Fact]
    public void WindowVentsHasNoZeroZDeltaStepUpDirectJump()
    {
        var window = PlanCt("mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, "Janela do Meio", "AWPer");
        var tws = window.TransitionWaypoints;
        int stepUpIdx = tws.FindIndex(w => w.TransitionType == TransitionWaypointType.STEP_UP);
        Assert.True(stepUpIdx > 0, "STEP_UP deve ser precedido por approach e alinhamento");
        var align = tws[stepUpIdx - 1];
        var stepUp = tws[stepUpIdx];
        Assert.True(stepUp.Z - align.Z >= 30.0f, $"STEP_UP deve ter delta Z positivo real (+30u+): {stepUp.Z - align.Z}");
        Assert.Equal(TransitionMovementAction.STEP_UP_JUMP_PULSE, stepUp.MovementAction);
        Assert.All(tws.Take(stepUpIdx), w => Assert.False(w.AllowJumpPulse));
    }

    [Fact]
    public void StepUpJumpTriggeredOnlyInsideWindowZone()
    {
        var window = PlanCt("mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, "Janela do Meio", "AWPer");
        var stepUp = window.TransitionWaypoints.First(w => w.TransitionType == TransitionWaypointType.STEP_UP);
        var flat = window.TransitionWaypoints.First(w => w.TransitionType == TransitionWaypointType.FLAT_PORTAL);

        Assert.False(GeometricTransitionExecutor.CanEmitJumpPulseNow(flat, flat.X, flat.Y, flat.Z, 200, -9999, 0, false, true, out _));
        Assert.False(GeometricTransitionExecutor.CanEmitJumpPulseNow(stepUp, -1550f, -1550f, -200f, 200, -9999, 0, false, true, out _));
        Assert.False(GeometricTransitionExecutor.CanEmitJumpPulseNow(stepUp, stepUp.X - 30f, stepUp.Y, stepUp.Z, 200, -9999, 0, false, true, out _));

        // Alinhado no piso inferior (-1485, -974.5, -199) olhando +X para o ledge (-1445, -974.5, -164)
        Assert.True(GeometricTransitionExecutor.CanEmitJumpPulseNow(
            stepUp, -1485f, -974.5f, -199.0f, 200, -9999, 0, false, true, out string okReason), okReason);
    }

    [Fact]
    public void NoContinuousInJumpDuringTransition()
    {
        var nav = LoadNavMesh();
        var window = PlanCt("mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, "Janela do Meio", "AWPer");
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        int jumpTicks = 0;
        int consecutiveJumpTicks = 0;
        bool prevJump = false;

        float x = -1488f, y = -974.5f, z = -199f;
        idx = window.TransitionWaypoints.FindIndex(w => w.TransitionType == TransitionWaypointType.STEP_UP);
        for (int t = 120; t <= 165; t++)
        {
            var eval = exec.EvaluateStep(1, t, (t - 100) / 64.0, window.TransitionWaypoints, ref idx, x, y, z, 180.0, false, true, nav);
            if (eval.ShouldEmitJumpPulse)
            {
                jumpTicks++;
                if (prevJump) consecutiveJumpTicks++;
                z = -164f;
                x = -1440f;
            }
            prevJump = eval.ShouldEmitJumpPulse;
        }

        Assert.Equal(1, jumpTicks);
        Assert.Equal(0, consecutiveJumpTicks);
        Assert.Equal(0, exec.ContinuousJumpViolations);
    }

    [Fact]
    public void VentEntryAndExitStayConnected()
    {
        var nav = LoadNavMesh();
        var window = PlanCt("mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, "Janela do Meio", "AWPer");
        int startIdx = window.TransitionWaypoints.FindIndex(w => w.TransitionType == TransitionWaypointType.STEP_UP);
        Assert.True(startIdx >= 0);

        for (int i = startIdx; i < window.TransitionWaypoints.Count - 1; i++)
        {
            var a = nav.ProjectPoint(window.TransitionWaypoints[i].X, window.TransitionWaypoints[i].Y, window.TransitionWaypoints[i].Z, 32f);
            var b = nav.ProjectPoint(window.TransitionWaypoints[i + 1].X, window.TransitionWaypoints[i + 1].Y, window.TransitionWaypoints[i + 1].Z, 32f);
            var (conn, _, _) = nav.FindShortestAreaPath(a.AreaId, b.AreaId, GeometricTransitionCatalog.WindowForbiddenNavAreas);
            Assert.True(conn, $"Segmento {window.TransitionWaypoints[i].Name}->{window.TransitionWaypoints[i + 1].Name} desconectado");
        }
    }

    [Fact]
    public void MarketRouteNeverBacktracksAfterEntry()
    {
        var market = PlanCt("b_short_pillar_hold_apps", -1760f, -1420f, -200f, -1463.8f, 179.5f, -167.0f, "Bombsite B", "Rotator");
        var tws = market.TransitionWaypoints;
        int doorEntryIdx = tws.FindIndex(w => w.Name == "ct_market_door_entry");
        Assert.True(doorEntryIdx > 0);
        for (int i = doorEntryIdx; i < tws.Count - 1; i++)
        {
            Assert.True(tws[i].Y > -700f, $"Waypoint {tws[i].Name} regrediu após Market");
            Assert.False(tws[i].X > -1500f && tws[i].Y < -500f, $"Backtrack para Window detectado em {tws[i].Name}");
        }
    }

    [Fact]
    public void MarketDoorPortalHasValidClearance()
    {
        var market = PlanCt("b_short_pillar_hold_apps", -1760f, -1420f, -200f, -1463.8f, 179.5f, -167.0f, "Bombsite B", "Rotator");
        var doorEntry = market.TransitionWaypoints.First(w => w.Name == "ct_market_door_entry");
        var doorExit = market.TransitionWaypoints.First(w => w.Name == "ct_market_door_exit");
        Assert.True(doorEntry.RequiredClearance >= 50f);
        Assert.True(doorExit.RequiredClearance >= 50f);
        Assert.True(doorEntry.UseExactPortalSteering);
        Assert.True(doorExit.UseExactPortalSteering);
        Assert.True(doorExit.ApproachDirY > 0.8f);
    }

    [Fact]
    public void MarketRouteDoesNotLeakToMid()
    {
        var nav = LoadNavMesh();
        var bench = PlanCt("b_forest_bench_hold_apps", -1760f, -1420f, -200f, -2531.3f, 274.1f, -168.0f, "Bombsite B", "Anchor");
        for (int i = 0; i < bench.TransitionWaypoints.Count - 1; i++)
        {
            var a = nav.ProjectPoint(bench.TransitionWaypoints[i].X, bench.TransitionWaypoints[i].Y, bench.TransitionWaypoints[i].Z, 32f);
            var b = nav.ProjectPoint(bench.TransitionWaypoints[i + 1].X, bench.TransitionWaypoints[i + 1].Y, bench.TransitionWaypoints[i + 1].Z, 32f);
            var (conn, _, path) = nav.FindShortestAreaPath(a.AreaId, b.AreaId, GeometricTransitionCatalog.MarketForbiddenNavAreas);
            Assert.True(conn);
            Assert.DoesNotContain(path, id => GeometricTransitionCatalog.MarketForbiddenNavAreas.Contains(id));
        }
    }

    [Fact]
    public void BenchForestRouteReachesFinalPointWithout168Trap()
    {
        var nav = LoadNavMesh();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(10, 1, "ct_bench", "CT", "Anchor", "b_forest_bench_hold_apps", "Bombsite B",
            -1760f, -1420f, -200f, -2531.3f, 274.1f, -168.0f, 100, true, false, explicitStaggerMs: 0));
        var res = SimulateSession(guard, nav, roundId: 10, slot: 1, sx: -1760f, sy: -1420f, sz: -200f);
        Assert.Equal("ON_TIME", res.FinalArrivalStatus);
        Assert.Equal(CanaryExecutorState.DestinationReached, res.FinalExecutorState);
        Assert.DoesNotContain(res.VisitedPositions, p => Math.Abs(p.X + 1920.2f) < 25f && Math.Abs(p.Y + 296.1f) < 25f);
    }

    [Fact]
    public void BVanBehindAppsRouteHandlesOneWayBalconyApproachWithoutFallback()
    {
        var nav = LoadNavMesh();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(11, 2, "ct_van", "CT", "Anchor", "b_van_behind_apps_hold", "Bombsite B",
            -1760f, -1420f, -200f, -1981.9f, 702.6f, -48.0f, 100, true, false, explicitStaggerMs: 0));
        var session = guard.GetSessionForRound(11)!;
        Assert.Equal("b_van_behind_apps_hold", session.OriginalDestination);
        Assert.False(session.Route.TransitionWaypoints[^1].IsFinalApproachReachable);

        var res = SimulateSession(guard, nav, roundId: 11, slot: 2, sx: -1760f, sy: -1420f, sz: -200f);
        Assert.Equal("ON_TIME", res.FinalArrivalStatus);
        Assert.Equal(CanaryExecutorState.DestinationReached, res.FinalExecutorState);
    }

    [Fact]
    public void ContinuousMovementAcrossTransitionsUsesBoundedStepForward()
    {
        var nav = LoadNavMesh();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(12, 1, "ct_win", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio",
            -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, 100, true, false, explicitStaggerMs: 0));
        var res = SimulateSession(guard, nav, roundId: 12, slot: 1, sx: -1550f, sy: -1550f, sz: -200f);
        Assert.Equal("ON_TIME", res.FinalArrivalStatus);
        for (int i = 1; i < res.VisitedPositions.Count; i++)
        {
            float dxy = MathF.Sqrt(
                MathF.Pow(res.VisitedPositions[i].X - res.VisitedPositions[i - 1].X, 2) +
                MathF.Pow(res.VisitedPositions[i].Y - res.VisitedPositions[i - 1].Y, 2));
            Assert.True(dxy <= 30.0f, $"Passo XY excessivo por tick: {dxy:F1}u");
        }
    }

    [Fact]
    public void TeammateBlockingDefersJump()
    {
        var window = PlanCt("mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, "Janela do Meio", "AWPer");
        var stepUp = window.TransitionWaypoints.First(w => w.TransitionType == TransitionWaypointType.STEP_UP);
        bool allowed = GeometricTransitionExecutor.CanEmitJumpPulseNow(
            stepUp, -1485f, -974.5f, -199.0f, 200, -9999, 0, teammateBlocking: true, exitPathValid: true, out string reason);
        Assert.False(allowed);
        Assert.Equal("TEAMMATE_BLOCKING", reason);
    }

    [Fact]
    public void FailedStepUpReturnsAuthority()
    {
        var nav = LoadNavMesh();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(13, 1, "ct_fail", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio",
            -1495f, -974.5f, -199f, -1181.4f, -718.5f, -168.0f, 100, true, false, explicitStaggerMs: 0));
        var s = guard.GetSessionForRound(13)!;
        s.WaypointIndex = s.Route.TransitionWaypoints.FindIndex(w => w.TransitionType == TransitionWaypointType.STEP_UP);

        CanaryTickDecision last = new();
        for (int t = 110; t <= 185; t++)
        {
            last = guard.EvaluateTick(13, 1, t, -1485f, -974.5f, -199f, 20f, "weapon_awp", true, true, false,
                "mid_window_right_deep", s.OriginalSector, "AWPer", false, false, false, tickIntervalMs: 16);
            if (!last.CanaryControlling) break;
        }

        Assert.False(last.CanaryControlling);
        Assert.Equal("UTILITY_AI", last.Authority);
        Assert.Equal(CanaryExecutorState.Fallback, last.ExecutorState);
        Assert.Equal("FAILED_STEP_UP_RETURNS_AUTHORITY", last.AbortOrCompletionReason);
    }

    [Fact]
    public void OnlyOneBotControlsOpeningCanary()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, LoadNavMesh());
        Assert.True(guard.TryStartCanaryForRound(14, 1, "ct_1", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio",
            -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, 100, true, false));
        Assert.False(guard.TryStartCanaryForRound(14, 2, "ct_2", "CT", "Anchor", "b_forest_bench_hold_apps", "Bombsite B",
            -1760f, -1420f, -200f, -2531.3f, 274.1f, -168.0f, 100, true, false));
        Assert.False(guard.IsSlotActiveCanary(14, 2));
    }

    [Fact]
    public void ThreatLineSwitchesToWeaponEvenWithTransitionActive()
    {
        var nav = LoadNavMesh();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(15, 1, "ct_w", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio",
            -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, 100, true, false, explicitStaggerMs: 0));
        var res = SimulateSession(guard, nav, roundId: 15, slot: 1, sx: -1550f, sy: -1550f, sz: -200f, honorWeaponSwitch: true);
        Assert.True(res.WeaponSwitchedBeforeFinish);
        Assert.Equal(CanaryExecutorState.DestinationReached, res.FinalExecutorState);
    }

    [Fact]
    public void RouteDoesNotChangeOriginalDestinationOrRole()
    {
        var nav = LoadNavMesh();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(16, 1, "ct_b", "CT", "Anchor", "b_forest_bench_hold_apps", "Bombsite B",
            -1760f, -1420f, -200f, -2531.3f, 274.1f, -168.0f, 100, true, false, explicitStaggerMs: 0));
        var s = guard.GetSessionForRound(16)!;
        _ = SimulateSession(guard, nav, roundId: 16, slot: 1, sx: -1760f, sy: -1420f, sz: -200f);
        Assert.Equal("b_forest_bench_hold_apps", s.OriginalDestination);
        Assert.Equal("B", s.OriginalSector);
        Assert.Equal("Anchor", s.Role);
    }

    [Fact]
    public void MovementAuthorityLeaseStaysUnbrokenAcrossSubWaypoints()
    {
        var nav = LoadNavMesh();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(17, 1, "ct_m", "CT", "Rotator", "b_short_pillar_hold_apps", "Bombsite B",
            -1760f, -1420f, -200f, -1463.8f, 179.5f, -167.0f, 100, true, false, explicitStaggerMs: 0));
        Assert.True(guard.LeaseManager.IsSlotLeasedByCanary(1, 17));
        bool suppressed = !guard.LeaseManager.AllowCompetingWriter(17, 1, 105, "CCSBot::HuntState", "Bot.GoalPosition");
        Assert.True(suppressed);

        var res = SimulateSession(guard, nav, roundId: 17, slot: 1, sx: -1760f, sy: -1420f, sz: -200f);
        Assert.Equal(CanaryExecutorState.DestinationReached, res.FinalExecutorState);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(1, 17));
        Assert.True(guard.LeaseManager.SuppressedAttempts.Count >= 1);
    }

    [Fact]
    public void GeometricHarnessSimulationPassesGates()
    {
        var nav = LoadNavMesh();
        var scenarios = new (string Bucket, string SpotId, string Sector, string Role, float Sx, float Sy, float Sz, float Tx, float Ty, float Tz)[]
        {
            ("Window/Vents", "mid_window_right_deep", "Janela do Meio", "AWPer", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f),
            ("Market/B", "b_short_pillar_hold_apps", "Bombsite B", "Rotator", -1760f, -1420f, -200f, -1463.8f, 179.5f, -167.0f),
            ("Bench/Forest", "b_forest_bench_hold_apps", "Bombsite B", "Anchor", -1760f, -1420f, -200f, -2531.3f, 274.1f, -168.0f),
            ("Van/Apps", "b_van_behind_apps_hold", "Bombsite B", "Anchor", -1760f, -1420f, -200f, -1981.9f, 702.6f, -48.0f),
        };

        var harnessSummary = new Dictionary<string, object>();
        int roundCounter = 100;
        int totalReps = 0;
        int totalCompleted = 0;
        int totalContinuousJump = 0;
        int totalInvalidPath = 0;
        int totalAuthorityViolations = 0;
        int totalDestChanged = 0;

        foreach (var sc in scenarios)
        {
            int completed = 0;
            int contJump = 0;
            int maxJumpPerRep = 0;
            int invPath = 0;
            int authViol = 0;
            int destChanged = 0;

            for (int rep = 0; rep < 10; rep++)
            {
                roundCounter++;
                totalReps++;
                float jx = ((rep % 5) - 2) * 14f;
                float jy = (((rep / 5) % 2) == 0 ? -1 : 1) * 12f;

                var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
                Assert.True(guard.TryStartCanaryForRound(roundCounter, 1, $"sim_{rep}", "CT", sc.Role, sc.SpotId, sc.Sector,
                    sc.Sx + jx, sc.Sy + jy, sc.Sz, sc.Tx, sc.Ty, sc.Tz, 100, true, false, explicitStaggerMs: 0));
                var s = guard.GetSessionForRound(roundCounter)!;
                if (!string.Equals(s.OriginalDestination, sc.SpotId, StringComparison.OrdinalIgnoreCase)) destChanged++;

                var res = SimulateSession(guard, nav, roundCounter, 1, sc.Sx + jx, sc.Sy + jy, sc.Sz);
                if (res.FinalExecutorState == CanaryExecutorState.DestinationReached) completed++;
                contJump += s.TransitionExecutor.ContinuousJumpViolations;
                maxJumpPerRep = Math.Max(maxJumpPerRep, s.TransitionExecutor.JumpPulsesIssued);
                if (s.LastBlockCause == BlockCause.NavmeshFailure) invPath++;
                if (s.LastUnauthorizedOverwrite) authViol++;
            }

            totalCompleted += completed;
            totalContinuousJump += contJump;
            totalInvalidPath += invPath;
            totalAuthorityViolations += authViol;
            totalDestChanged += destChanged;

            Assert.True(completed >= 9, $"{sc.Bucket} completou {completed}/10 (< 9/10)");
            Assert.Equal(0, contJump);
            Assert.True(maxJumpPerRep <= 1);
            Assert.Equal(0, invPath);
            Assert.Equal(0, authViol);
            Assert.Equal(0, destChanged);

            harnessSummary[sc.Bucket] = new
            {
                repetitions = 10,
                completed,
                completion_rate = Math.Round(completed / 10.0, 4),
                continuous_jump_count = contJump,
                max_jump_pulses_per_attempt = maxJumpPerRep,
                invalid_path_count = invPath,
                authority_violation_count = authViol,
                destination_unchanged_pct = 100.0
            };
        }

        WriteTransitionArtifacts(nav, harnessSummary, totalReps, totalCompleted, totalContinuousJump, totalInvalidPath, totalAuthorityViolations, totalDestChanged);
    }

    [Fact]
    public void RouteAccountingCloses()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(50);
        tracker.OnFreezeTimeEnded(100);
        Assert.True(tracker.TryRegisterAssignment(50, 1, "ct_1", "CT", "mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168f, 180f, 100, false));
        Assert.True(tracker.TryRegisterAssignment(50, 2, "ct_2", "CT", "b_forest_bench_hold_apps", -1760f, -1420f, -200f, -2531.3f, 274.1f, -168f, 220f, 100, false));
        tracker.CloseAllOpenRoutes(50, OpeningRouteTerminationReason.ROUND_END, 900);
        Assert.Equal(0, tracker.ComputeAccountingResidue());
    }

    private sealed class SimResult
    {
        public string FinalExecutorState { get; init; } = string.Empty;
        public string FinalArrivalStatus { get; init; } = string.Empty;
        public bool WeaponSwitchedBeforeFinish { get; init; }
        public List<(float X, float Y, float Z)> VisitedPositions { get; } = new();
    }

    private static SimResult SimulateSession(
        OpeningRouteCanaryGuard guard,
        NavMeshGraph nav,
        int roundId,
        int slot,
        float sx, float sy, float sz,
        bool honorWeaponSwitch = true)
    {
        var session = guard.GetSessionForRound(roundId)!;
        float x = sx, y = sy, z = sz;
        string weapon = "weapon_knife";
        bool weaponSwitched = false;
        var visited = new List<(float X, float Y, float Z)> { (x, y, z) };
        CanaryTickDecision dec = new() { CanaryControlling = true };

        for (int t = 101; t <= 1250; t++)
        {
            dec = guard.EvaluateTick(
                roundId, slot, t, x, y, z, 220f, weapon,
                isAlive: true, isOpeningPhase: true, isBombPlanted: false,
                session.OriginalDestination, session.OriginalSector, session.Role,
                hasContact: false, tookDamage: false, hostileUtility: false, hasC4: false,
                tickIntervalMs: 16);

            if (!dec.CanaryControlling)
            {
                break;
            }

            if (honorWeaponSwitch && dec.ShouldSwitchToWeapon)
            {
                weapon = "weapon_m4a1";
                weaponSwitched = true;
            }

            if (!dec.HoldingForStagger && dec.CurrentWaypoint != null)
            {
                var wp = dec.CurrentWaypoint;
                float tx = wp.X, ty = wp.Y, tz = wp.Z;
                if (!dec.UseExactPortalSteering)
                {
                    (tx, ty, tz) = nav.GetNextSteerTarget(x, y, z, wp.X, wp.Y, wp.Z, 42f, dec.ForbiddenNavAreas);
                }

                float dx = tx - x;
                float dy = ty - y;
                float dist2D = MathF.Sqrt(dx * dx + dy * dy);
                float step = MathF.Min(dist2D, 3.6f); // ~230 u/s a 64Hz
                if (dist2D > 0.1f)
                {
                    x += (dx / dist2D) * step;
                    y += (dy / dist2D) * step;
                }

                if (dec.ShouldEmitJumpPulse)
                {
                    z = wp.Z;
                }
                else if (dec.ActiveTransitionType != TransitionWaypointType.STEP_UP)
                {
                    var proj = nav.ProjectPoint(x, y, z, 64f);
                    if (proj.AreaId > 0) z = proj.ProjectedZ;
                }
                else
                {
                    float dzStep = Math.Clamp(tz - z, -4.0f, 4.0f);
                    z += dzStep;
                }

                visited.Add((x, y, z));
            }
        }

        var result = new SimResult
        {
            FinalExecutorState = session.ExecutorState,
            FinalArrivalStatus = session.ArrivalStatus,
            WeaponSwitchedBeforeFinish = weaponSwitched,
        };
        result.VisitedPositions.AddRange(visited);
        return result;
    }

    private static void WriteTransitionArtifacts(
        NavMeshGraph nav,
        Dictionary<string, object> harnessSummary,
        int totalReps,
        int totalCompleted,
        int totalContinuousJump,
        int totalInvalidPath,
        int totalAuthorityViolations,
        int totalDestChanged)
    {
        var outDir = PatchDir();
        var opts = new JsonSerializerOptions { WriteIndented = true };

        var contract = new
        {
            schema = "transition_waypoint_contract_v1",
            generated_at_utc = DateTime.UtcNow.ToString("O"),
            data_nature = "REAL_CONTRACT",
            allowed_transition_types = Enum.GetNames<TransitionWaypointType>(),
            allowed_movement_actions = Enum.GetNames<TransitionMovementAction>(),
            required_fields = new[]
            {
                "name", "x", "y", "z", "navmesh_area", "transition_type",
                "approach_dir_x", "approach_dir_y", "approach_dir_z",
                "arrival_radius", "exit_radius", "minimum_forward_progress",
                "maximum_lateral_error", "movement_action", "timeout_seconds",
                "next_waypoint", "required_clearance", "use_exact_portal_steering",
                "allow_jump_pulse", "min_z_delta", "max_z_delta", "is_final_approach_reachable"
            },
            command_events = new[]
            {
                GeometricTransitionExecutor.EventTransitionEntry,
                GeometricTransitionExecutor.EventSubwaypointChange,
                GeometricTransitionExecutor.EventLocalizedAction,
                GeometricTransitionExecutor.EventTransitionExit,
                GeometricTransitionExecutor.EventTransitionFallback,
            },
            forbidden_behaviors = new[]
            {
                "CONTINUOUS_IN_JUMP",
                "STEP_UP_WITH_TEAMMATE_BLOCKING",
                "GENERIC_110U_RADIUS_SKIP",
                "MARKET_SHORTCUT_THROUGH_WINDOW_1733",
                "CHANGE_ORIGINAL_DESTINATION"
            }
        };
        File.WriteAllText(Path.Combine(outDir, "transition_waypoint_contract_v1.json"), JsonSerializer.Serialize(contract, opts));

        var window = PlanCt("mid_window_right_deep", -1550f, -1550f, -200f, -1181.4f, -718.5f, -168.0f, "Janela do Meio", "AWPer");
        File.WriteAllText(Path.Combine(outDir, "window_vents_transition.json"), JsonSerializer.Serialize(new
        {
            route_id = window.RouteId,
            intended_destination = "mid_window_right_deep",
            forbidden_nav_areas = GeometricTransitionCatalog.WindowForbiddenNavAreas.OrderBy(x => x).ToArray(),
            transition_waypoints = window.TransitionWaypoints
        }, opts));

        var market = PlanCt("b_short_pillar_hold_apps", -1760f, -1420f, -200f, -1463.8f, 179.5f, -167.0f, "Bombsite B", "Rotator");
        File.WriteAllText(Path.Combine(outDir, "market_b_transition.json"), JsonSerializer.Serialize(new
        {
            route_id = market.RouteId,
            intended_destination = "b_short_pillar_hold_apps",
            forbidden_nav_areas = GeometricTransitionCatalog.MarketForbiddenNavAreas.OrderBy(x => x).ToArray(),
            transition_waypoints = market.TransitionWaypoints
        }, opts));

        var bench = PlanCt("b_forest_bench_hold_apps", -1760f, -1420f, -200f, -2531.3f, 274.1f, -168.0f, "Bombsite B", "Anchor");
        var van = PlanCt("b_van_behind_apps_hold", -1760f, -1420f, -200f, -1981.9f, 702.6f, -48.0f, "Bombsite B", "Anchor");
        File.WriteAllText(Path.Combine(outDir, "b_site_bench_forest_transition.json"), JsonSerializer.Serialize(new
        {
            bench_route = new { route_id = bench.RouteId, intended_destination = "b_forest_bench_hold_apps", transition_waypoints = bench.TransitionWaypoints },
            van_route = new { route_id = van.RouteId, intended_destination = "b_van_behind_apps_hold", transition_waypoints = van.TransitionWaypoints }
        }, opts));

        var harnessPayload = new
        {
            marco = "2B.8.4",
            data_nature = "SIMULATED",
            generated_at_utc = DateTime.UtcNow.ToString("O"),
            total_repetitions = totalReps,
            total_completed = totalCompleted,
            completion_rate = Math.Round(totalCompleted / (double)totalReps, 4),
            continuous_jump_total = totalContinuousJump,
            invalid_path_total = totalInvalidPath,
            authority_violation_total = totalAuthorityViolations,
            destination_changed_total = totalDestChanged,
            gates_passed = totalCompleted >= 36 && totalContinuousJump == 0 && totalInvalidPath == 0 && totalAuthorityViolations == 0 && totalDestChanged == 0,
            by_transition = harnessSummary
        };
        File.WriteAllText(Path.Combine(outDir, "geometric_harness_metrics.json"), JsonSerializer.Serialize(harnessPayload, opts));
    }
}
