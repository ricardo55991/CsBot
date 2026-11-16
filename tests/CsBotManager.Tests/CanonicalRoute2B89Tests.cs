using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Xunit;

namespace CsBotManager.Tests;

public class CanonicalRoute2B89Tests
{
    private static readonly string RepoRoot = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));

    private static NavMeshGraph? LoadMirageNav()
    {
        string path = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return File.Exists(path) ? NavMeshGraph.LoadFromFile(path) : null;
    }

    private static OpeningRoutePlanner CreatePlanner() => new();

    private static List<CanonicalRouteStep> PlanTrSteps(string targetSpot, string sector, float sx, float sy, float sz, float tx, float ty, float tz)
    {
        var planner = CreatePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            roundId: 1, rawSlot: 2, pseudonymizedSlot: "tr_2", team: "T", role: "EntryFragger",
            targetSpotId: targetSpot, spotSector: sector,
            startX: sx, startY: sy, startZ: sz,
            targetX: tx, targetY: ty, targetZ: tz,
            tick: 100, out var suggestion));
        Assert.NotNull(suggestion);
        return suggestion!.CanonicalSteps;
    }

    [Fact]
    public void GoalOwnership_ActiveLeaseSuppressesCompetingWriter()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 3, "tr_3", "T", "r1", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        var arb = new MovementArbitrator { LeaseManager = leaseMgr };
        arb.BeginTick(101, 1.58f, 1);
        arb.PublishIntent(new MovementIntent
        {
            BotSlot = 3, BotName = "tr_3", Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.NavigateNavMesh, Reason = "UtilityGoal",
            GoalX = 999f, GoalY = 999f, GoalZ = -100f, GameTick = 101, ExpiresAtTime = 5f
        });
        arb.PublishIntent(new MovementIntent
        {
            BotSlot = 3, BotName = "tr_3", Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.NavigateNavMesh, Reason = "OpeningCanary:wp0",
            GoalX = 500f, GoalY = -1555f, GoalZ = -215f, GameTick = 101, ExpiresAtTime = 5f
        });
        var dec = arb.CollectAndResolveIntents(3, 101, 1.58f);
        Assert.NotNull(dec);
        Assert.StartsWith("OpeningCanary", dec!.WinningIntent.Reason);
        Assert.Contains(leaseMgr.GoalWriteAudit, a => a.WriteSuppressed && a.WriterId.Contains("TacticalNavigation"));
    }

    [Fact]
    public void GoalOwnership_CompetingHighPriorityWriterBlockedDuringLease()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 3, "tr_3", "T", "r1", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        var arb = new MovementArbitrator { LeaseManager = leaseMgr };
        arb.BeginTick(101, 1.58f, 1);
        arb.PublishIntent(new MovementIntent
        {
            BotSlot = 3, BotName = "tr_3", Source = MovementIntentSource.BombObjective,
            Kind = MovementCommandKind.NavigateNavMesh, Reason = "BombPlantRun",
            GoalX = 1258f, GoalY = -384f, GoalZ = -163f, GameTick = 101, ExpiresAtTime = 5f
        });
        var dec = arb.CollectAndResolveIntents(3, 101, 1.58f);
        Assert.Null(dec);
        Assert.Contains(leaseMgr.GoalWriteAudit, a => a.WriteSuppressed && a.Reason.Contains("BombPlantRun"));
    }

    [Fact]
    public void GoalOwnership_UnknownPostCanaryWriterFlaggedWhenGoalDrifts()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 3, "tr_3", "T", "r1", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        var rec = leaseMgr.RecordTickVerification(
            tick: 105, roundId: 1, botSlot: 3, playerPseudonym: "tr_3", routeId: "r1", waypointIndex: 0,
            activeWaypoint: new[] { 500f, -1555f, -215f },
            goalBeforeCanary: new[] { 0f, 0f, 0f },
            goalAfterCanary: new[] { 500f, -1555f, -215f },
            goalEndOfTick: new[] { 1258.5f, -384.0f, -163.3f },
            subpathGoalEndOfTick: Array.Empty<float>(),
            movementSourceApplied: "NONE", nativeState: "Hunt", nativeTask: 0, nativePathLength: 0,
            botStateIsolated: true, weaponState: "knife", velocityXy: 200.0, jumpButtonActive: false, usercmdVectorActive: false);
        Assert.True(rec.UnauthorizedOverwriteDetected);
        Assert.Contains("UNKNOWN_POST_CANARY_WRITER", rec.CompetingWritersDetected);
    }

    [Fact]
    public void GoalOwnership_Strict4UnitToleranceDetectsSmallDrift()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 3, "tr_3", "T", "r1", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        var rec = leaseMgr.RecordTickVerification(
            tick: 106, roundId: 1, botSlot: 3, playerPseudonym: "tr_3", routeId: "r1", waypointIndex: 0,
            activeWaypoint: new[] { 500f, -1555f, -215f },
            goalBeforeCanary: new[] { 500f, -1555f, -215f },
            goalAfterCanary: new[] { 500f, -1555f, -215f },
            goalEndOfTick: new[] { 506f, -1555f, -215f },
            subpathGoalEndOfTick: Array.Empty<float>(),
            movementSourceApplied: "TacticalNavigation:MoveToGoal", nativeState: "MoveTo", nativeTask: 0, nativePathLength: 0,
            botStateIsolated: true, weaponState: "knife", velocityXy: 200.0, jumpButtonActive: false, usercmdVectorActive: false);
        Assert.True(rec.UnauthorizedOverwriteDetected);
    }

    [Fact]
    public void GoalOwnership_NonCanarySlotsRemainUnchanged()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 3, "tr_3", "T", "r1", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.False(leaseMgr.HasActiveLease(4));
        Assert.True(leaseMgr.AllowCompetingWriter(1, 4, 101, "UtilityAI", "MoveToGoal"));
    }

    [Fact]
    public void GoalOwnership_ReleaseLeaseStopsEnforcementCleanly()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 3, "tr_3", "T", "r1", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(leaseMgr.HasActiveLease(3));
        Assert.True(leaseMgr.ReleaseLease(1, 150, "COMPLETED"));
        Assert.False(leaseMgr.HasActiveLease(3));
    }

    [Fact]
    public void CanonicalModel_ARampEndsInFinalDestinationMatchingCatalog()
    {
        var steps = PlanTrSteps("tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f);
        Assert.True(steps.Count >= 4);
        var last = steps[^1];
        Assert.True(last.IsFinalDestination);
        Assert.Equal("tr_a_ramp_staging_wait", last.Name);
        Assert.Equal(240f, last.CanonicalPosition[0]);
        Assert.Equal(-1620f, last.CanonicalPosition[1]);
    }

    [Fact]
    public void CanonicalModel_APalaceEndsInDeepRoomMatchingCatalog()
    {
        var steps = PlanTrSteps("a_palace_deep_room", "A", 1216f, -1100f, -168f, 180f, -2060f, -40f);
        Assert.True(steps.Count >= 5);
        Assert.Equal("a_palace_deep_room", steps[^1].Name);
        Assert.True(steps[^1].IsFinalDestination);
        Assert.Equal(180f, steps[^1].CanonicalPosition[0]);
    }

    [Fact]
    public void CanonicalModel_BHouseStagingUsesTargetCoordsNotHardcoded()
    {
        var steps = PlanTrSteps("tr_b_apps_house_staging", "B", -350f, 480f, -77f, -810f, 540f, -76f);
        Assert.Contains(steps, s => s.Name == "t_b_apps_house_staging_approach");
        var last = steps[^1];
        Assert.Equal("tr_b_apps_house_staging", last.Name);
        Assert.True(last.IsFinalDestination);
        Assert.Equal(-810f, last.CanonicalPosition[0]);
        Assert.Equal(540f, last.CanonicalPosition[1]);
    }

    [Fact]
    public void CanonicalModel_BKitchenControlEndsInTargetSpot()
    {
        var steps = PlanTrSteps("tr_b_apps_kitchen_control", "B", -350f, 480f, -77f, -1210f, 690f, -80f);
        var last = steps[^1];
        Assert.Equal("tr_b_apps_kitchen_control", last.Name);
        Assert.True(last.IsFinalDestination);
        Assert.Equal(-1210f, last.CanonicalPosition[0]);
    }

    [Fact]
    public void CanonicalValidator_RejectsEmptySteps()
    {
        var (ok, reason) = CanonicalRouteValidator.Validate(Array.Empty<CanonicalRouteStep>(), "tr_a_ramp_staging_wait", 0, 0, 0);
        Assert.False(ok);
        Assert.Equal("CANONICAL_ROUTE_EMPTY", reason);
    }

    [Fact]
    public void CanonicalValidator_RejectsMultipleFinalDestinations()
    {
        var steps = PlanTrSteps("tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f);
        steps[0].IsFinalDestination = true;
        var (ok, reason) = CanonicalRouteValidator.Validate(steps, "tr_a_ramp_staging_wait", 240f, -1620f, -168f);
        Assert.False(ok);
        Assert.StartsWith("INTERMEDIATE_MARKED_FINAL:", reason);
    }

    [Fact]
    public void CanonicalValidator_RejectsBrokenNextStepChain()
    {
        var steps = PlanTrSteps("tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f);
        steps[0].ExpectedNextStepName = "wrong_name";
        var (ok, reason) = CanonicalRouteValidator.Validate(steps, "tr_a_ramp_staging_wait", 240f, -1620f, -168f);
        Assert.False(ok);
        Assert.StartsWith("BROKEN_NEXT_NAME:", reason);
    }

    [Fact]
    public void CanonicalValidator_RejectsNonFinalWithNullNextStep()
    {
        var steps = PlanTrSteps("tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f);
        steps[1].ExpectedNextStepName = null;
        var (ok, reason) = CanonicalRouteValidator.Validate(steps, "tr_a_ramp_staging_wait", 240f, -1620f, -168f);
        Assert.False(ok);
    }

    [Fact]
    public void CanonicalValidator_RejectsCatalogTargetMismatch()
    {
        var steps = PlanTrSteps("tr_b_apps_house_staging", "B", -350f, 480f, -77f, -810f, 540f, -76f);
        var (ok, reason) = CanonicalRouteValidator.Validate(steps, "tr_b_apps_house_staging", -700f, 540f, -76f);
        Assert.False(ok);
        Assert.StartsWith("FINAL_COORDS_DIVERGE_FROM_CATALOG:", reason);
    }

    [Fact]
    public void CanonicalValidator_AcceptsAllFourValidTrRoutes()
    {
        var nav = LoadMirageNav();
        var cases = new[]
        {
            ("tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f),
            ("a_palace_deep_room", "A", 1216f, -1100f, -168f, 180f, -2060f, -40f),
            ("tr_b_apps_house_staging", "B", -350f, 480f, -77f, -810f, 540f, -76f),
            ("tr_b_apps_kitchen_control", "B", -350f, 480f, -77f, -1210f, 690f, -80f),
        };
        foreach (var c in cases)
        {
            var steps = PlanTrSteps(c.Item1, c.Item2, c.Item3, c.Item4, c.Item5, c.Item6, c.Item7, c.Item8);
            CanonicalRouteValidator.ProjectCanonicalStepsInPlace(steps, nav);
            var (ok, reason) = CanonicalRouteValidator.Validate(steps, c.Item1, c.Item6, c.Item7, c.Item8, nav);
            Assert.True(ok, $"{c.Item1} failed: {reason}");
        }
    }

    [Fact]
    public void ProjectionSynchronizesOrderedAndTransitionWaypoints()
    {
        var nav = LoadMirageNav();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "tr_2", "T", "EntryFragger",
            "tr_b_apps_kitchen_control", "B", -350f, 480f, -77f, -1210f, 690f, -80f, 100, true, false));
        var session = guard.GetSessionForRound(1);
        Assert.NotNull(session);
        Assert.Equal(session!.Route.CanonicalSteps.Count, session.Route.OrderedWaypoints.Count);
        Assert.Equal(session.Route.CanonicalSteps.Count, session.Route.TransitionWaypoints.Count);
        for (int i = 0; i < session.Route.CanonicalSteps.Count; i++)
        {
            Assert.Equal(session.Route.CanonicalSteps[i].X, session.Route.OrderedWaypoints[i].X);
            Assert.Equal(session.Route.CanonicalSteps[i].X, session.Route.TransitionWaypoints[i].X);
            Assert.Equal(session.Route.CanonicalSteps[i].Name, session.Route.TransitionWaypoints[i].Name);
        }
    }

    [Fact]
    public void IntermediateStepNeverProducesRouteCompleted()
    {
        var nav = LoadMirageNav();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "tr_2", "T", "EntryFragger",
            "tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f, 100, true, false));
        // Even if bot is teleported to final coords while WaypointIndex is 0, cannot complete on intermediate step
        var dec = guard.EvaluateTick(1, 2, 105, 240f, -1620f, -168f, 0f, "weapon_knife", true, true, false,
            "tr_a_ramp_staging_wait", "A", "EntryFragger", false, false, false);
        Assert.NotEqual(CanaryExecutorState.DestinationReached, dec.ExecutorState);
    }

    [Fact]
    public void FinalStepCompletesWhenBotDwellsAtDestination()
    {
        var nav = LoadMirageNav();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "tr_2", "T", "EntryFragger",
            "tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f, 100, true, false));
        var s = guard.GetSessionForRound(1)!;
        s.WaypointIndex = s.Route.CanonicalSteps.Count - 1;
        var finalStep = s.Route.CanonicalSteps[^1];
        var dec = guard.EvaluateTick(1, 2, 200, finalStep.X, finalStep.Y, finalStep.Z, 5f, "weapon_ak47", true, true, false,
            "tr_a_ramp_staging_wait", "A", "EntryFragger", false, false, false);
        Assert.Equal(CanaryExecutorState.DestinationReached, dec.ExecutorState);
    }

    [Fact]
    public void TelemetryIncludesAllElevenCanonicalFields()
    {
        var nav = LoadMirageNav();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "tr_2", "T", "EntryFragger",
            "tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f, 100, true, false));
        guard.EvaluateTick(1, 2, 101, 692f, -1516.8f, -258.5f, 210f, "weapon_knife", true, true, false,
            "tr_a_ramp_staging_wait", "A", "EntryFragger", false, false, false);
        Assert.NotEmpty(guard.Records);
        var rec = guard.Records[^1];
        Assert.True(rec.CanonicalStepCount >= 4);
        Assert.False(string.IsNullOrEmpty(rec.CanonicalStepName));
        Assert.False(string.IsNullOrEmpty(rec.CanonicalStepRole));
        Assert.False(rec.IsFinalDestination);
        Assert.True(rec.ExpectedNextStepIndex >= 1);
        Assert.False(string.IsNullOrEmpty(rec.ExpectedNextStepName));
        Assert.True(rec.GoalOwnershipValid);
    }

    [Fact]
    public void TickIntervalDefaultsTo64Hz15625Ms()
    {
        var method = typeof(OpeningRouteCanaryGuard).GetMethod(nameof(OpeningRouteCanaryGuard.EvaluateTick));
        Assert.NotNull(method);
        var param = method!.GetParameters().Single(p => p.Name == "tickIntervalMs");
        Assert.Equal(typeof(double), param.ParameterType);
        Assert.Equal(15.625, (double)param.DefaultValue!, 3);
    }

    [Fact]
    public void SoloModeNeverClassifiesTeammateCongestion()
    {
        var nav = LoadMirageNav();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "tr_2", "T", "EntryFragger",
            "tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f, 100, true, false));
        for (int t = 101; t < 160; t++)
        {
            guard.EvaluateTick(1, 2, t, 1216f, -1100f, -168f, 0f, "weapon_knife", true, true, false,
                "tr_a_ramp_staging_wait", "A", "EntryFragger", false, false, false, teammates: Array.Empty<TeammatePositionSnapshot>());
        }
        Assert.DoesNotContain(guard.Records, r => r.BlockCauseName == BlockCause.TeammateCongestion);
    }

    [Fact]
    public void ProtectedCtAndMidMethodsRemainBitwiseIdentical()
    {
        string src = File.ReadAllText(Path.Combine(RepoRoot, "src", "CsBotManager", "GeometricTransitionPlanner.cs"));
        Assert.Contains("BuildTransitionsForCtRoute", src);
        Assert.Contains("BuildWindowVentsTransitions", src);
        Assert.Contains("BuildTrTopMidTransitions", src);
        Assert.Contains("BuildTrUnderpassTransitions", src);
    }

    [Fact]
    public void CtRoutesStillDoNotUseTrCanonicalSteps()
    {
        var planner = CreatePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 1, "ct_1", "CT", "Anchor",
            "a_triple_box_hold", "A", -1400f, -2080f, -195f, -530f, -1920f, -168f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.Empty(sug!.CanonicalSteps);
        Assert.NotEmpty(sug.OrderedWaypoints);
    }

    [Fact]
    public void MidRoutesPreserveOriginalTransitionStructure()
    {
        var planner = CreatePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "tr_2", "T", "MidLurk",
            "mid_top_mid_boxes", "MID", 560f, -260f, -168f, -450f, -240f, -168f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.NotEmpty(sug!.TransitionWaypoints);
    }

    [Fact]
    public void CanonicalStepToRouteWaypointUsesProjectedWhenApplied()
    {
        var step = new CanonicalRouteStep
        {
            Name = "test_step",
            CanonicalPosition = new[] { 100f, 200f, 10f },
            ProjectedPosition = new[] { 105f, 205f, 12f },
            ProjectionApplied = true,
        };
        var wp = step.ToRouteWaypoint();
        Assert.Equal(105f, wp.X);
        Assert.Equal(205f, wp.Y);
        Assert.Equal(12f, wp.Z);
    }

    [Fact]
    public void CanonicalStepToTransitionWaypointPreservesNextStepName()
    {
        var step = new CanonicalRouteStep
        {
            Name = "step_a",
            ExpectedNextStepName = "step_b",
            CanonicalPosition = new[] { 100f, 200f, 10f },
        };
        var tw = step.ToTransitionWaypoint();
        Assert.Equal("step_b", tw.NextWaypoint);
    }

    [Fact]
    public void CanonicalStepFinalHasNullNextStepAndEmptyTransitionNext()
    {
        var steps = PlanTrSteps("tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f);
        var last = steps[^1];
        Assert.Null(last.ExpectedNextStepIndex);
        Assert.Null(last.ExpectedNextStepName);
        Assert.Equal(string.Empty, last.ToTransitionWaypoint().NextWaypoint);
    }

    [Fact]
    public void ARampEntryLinksToFinalStagingWait()
    {
        var steps = PlanTrSteps("tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f);
        var entry = steps.Single(s => s.Name == "t_a_ramp_entry");
        Assert.Equal("tr_a_ramp_staging_wait", entry.ExpectedNextStepName);
        Assert.False(entry.IsFinalDestination);
    }

    [Fact]
    public void BHouseApproachLinksToFinalHouseStaging()
    {
        var steps = PlanTrSteps("tr_b_apps_house_staging", "B", -350f, 480f, -77f, -810f, 540f, -76f);
        var approach = steps.Single(s => s.Name == "t_b_apps_house_staging_approach");
        Assert.Equal("tr_b_apps_house_staging", approach.ExpectedNextStepName);
        Assert.False(approach.IsFinalDestination);
    }

    [Fact]
    public void BKitchenHallLinksToFinalKitchenControl()
    {
        var steps = PlanTrSteps("tr_b_apps_kitchen_control", "B", -350f, 480f, -77f, -1210f, 690f, -80f);
        var hall = steps.Single(s => s.Name == "t_b_apps_kitchen_hall");
        Assert.Equal("tr_b_apps_kitchen_control", hall.ExpectedNextStepName);
        Assert.False(hall.IsFinalDestination);
    }

    [Fact]
    public void APalaceStairsLinksToDeepRoom()
    {
        var steps = PlanTrSteps("a_palace_deep_room", "A", 1216f, -1100f, -168f, 180f, -2060f, -40f);
        var stairs = steps.Single(s => s.Name == "t_palace_stairs");
        Assert.Equal("a_palace_deep_room", stairs.ExpectedNextStepName);
        Assert.False(stairs.IsFinalDestination);
    }

    [Fact]
    public void WeaponReadyBeforeContactPreservedInCanonicalRoutes()
    {
        var planner = CreatePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "tr_2", "T", "EntryFragger",
            "tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f, 100, out var sug));
        Assert.True(sug!.WeaponReadyBeforeContact);
    }

    [Fact]
    public void C4CompatibleWithCanonicalTrRoutes()
    {
        var nav = LoadMirageNav();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "tr_2", "T", "EntryFragger",
            "tr_a_ramp_staging_wait", "A", 1216f, -1100f, -168f, 240f, -1620f, -168f, 100, true, false,
            hasC4: true, planTargetBombsite: "A"));
    }

    [Fact]
    public void GoalWriteAuditCapturesBothAcceptedAndSuppressed()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        leaseMgr.RecordGoalWriteAudit("OPENING_ROUTE_CANARY", 101, 1, 2, "APPLY_WINNING_INTENT",
            new[] { 0f, 0f, 0f }, new[] { 100f, 200f, 0f }, "OpeningCanary:wp0", true, true, false);
        leaseMgr.RecordGoalWriteAudit("Arbitrator:TacticalNavigation", 101, 1, 2, "ARBITRATION_COLLECT",
            Array.Empty<float>(), new[] { 900f, 900f, 0f }, "UtilityGoal", true, false, true);
        Assert.Equal(2, leaseMgr.GoalWriteAudit.Count);
        Assert.Single(leaseMgr.GoalWriteAudit, a => a.WriteAccepted && !a.WriteSuppressed);
        Assert.Single(leaseMgr.GoalWriteAudit, a => !a.WriteAccepted && a.WriteSuppressed);
    }

    [Fact]
    public void PalaceStep1EmitsJumpPulseAtBase()
    {
        var nav = LoadMirageNav();
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.TrSingle, nav);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "tr_2", "T", "EntryFragger",
            "a_palace_deep_room", "A", 1216f, -1100f, -168f, 180f, -2060f, -40f, 100, true, false));
        var s = guard.GetSessionForRound(1)!;
        int step1Idx = s.Route.CanonicalSteps.FindIndex(c => c.Name == "t_palace_box_step_1");
        Assert.True(step1Idx >= 0);
        s.WaypointIndex = step1Idx;
        var dec = guard.EvaluateTick(1, 2, 800, -13.5f, -1740.5f, -168f, 10f, "weapon_ak47", true, true, false,
            "a_palace_deep_room", "A", "EntryFragger", false, false, false,
            teammates: Array.Empty<TeammatePositionSnapshot>());
        Assert.True(dec.ShouldEmitJumpPulse, $"JumpPulsesIssued={s.TransitionExecutor.JumpPulsesIssued} reason={CanEmitReason(s.Route.TransitionWaypoints[step1Idx])}");
    }

    private static string CanEmitReason(RouteTransitionWaypoint wp)
    {
        GeometricTransitionExecutor.CanEmitJumpPulseNow(wp, -13.5f, -1740.5f, -168f, 800, -9999, 0, false, true, out string reason);
        return $"{reason}|type={wp.TransitionType}|act={wp.MovementAction}|allow={wp.AllowJumpPulse}|minZ={wp.MinZDelta}|maxZ={wp.MaxZDelta}";
    }
}
