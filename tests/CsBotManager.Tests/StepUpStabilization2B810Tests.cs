using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class StepUpStabilization2B810Tests
{
    private static readonly string RepoRoot = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));

    private static NavMeshGraph? LoadMirageNav()
    {
        string path = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return File.Exists(path) ? NavMeshGraph.LoadFromFile(path) : null;
    }

    private static OpeningRouteSuggestion PlanRoute(string targetSpot, string sector, float sx, float sy, float sz, float tx, float ty, float tz)
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            roundId: 1, rawSlot: 2, pseudonymizedSlot: "tr_2", team: "T", role: "EntryFragger",
            targetSpotId: targetSpot, spotSector: sector,
            startX: sx, startY: sy, startZ: sz,
            targetX: tx, targetY: ty, targetZ: tz,
            tick: 100, out var suggestion));
        Assert.NotNull(suggestion);
        return suggestion!;
    }

    private static RouteTransitionWaypoint MakeStepUpWp(string name, float x, float y, float z, int navArea = 0)
    {
        return new RouteTransitionWaypoint
        {
            Name = name,
            X = x,
            Y = y,
            Z = z,
            TransitionType = TransitionWaypointType.STEP_UP,
            MovementAction = TransitionMovementAction.STEP_UP_JUMP_PULSE,
            AllowJumpPulse = true,
            ArrivalRadius = 32f,
            ExitRadius = 48f,
            TimeoutSeconds = 3.0f,
            NavMeshArea = navArea,
            IsFinalApproachReachable = true,
            ApproachDirX = -1.0f,
            ApproachDirY = 0.0f,
            MinZDelta = 12f,
            MaxZDelta = 90f,
        };
    }

    [Fact]
    public void PalaceStepOneUsesExplicitPulseStateMachine()
    {
        var sug = PlanRoute("a_palace_deep_room", "A", 1216f, -384f, -163f, 56.5f, -2120.7f, -39.9f);
        var step1 = sug.TransitionWaypoints.First(w => w.Name == "t_palace_box_step_1");
        Assert.Equal(TransitionWaypointType.STEP_UP, step1.TransitionType);
        Assert.Equal(TransitionMovementAction.STEP_UP_JUMP_PULSE, step1.MovementAction);
        Assert.True(step1.AllowJumpPulse);

        var exec = new GeometricTransitionExecutor();
        Assert.Equal(StepUpPulseState.WAITING_FOR_ALIGNMENT, exec.PulseState);

        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { step1, sug.TransitionWaypoints.Last() };
        var eval = exec.EvaluateStep(1, 100, 1.56, list, ref idx, step1.X + 20f, step1.Y, step1.Z - 60f, 200.0, false, true, null);
        Assert.True(eval.ShouldEmitJumpPulse);
        Assert.Equal(StepUpPulseState.PULSE_REQUESTED, exec.PulseState);
    }

    [Fact]
    public void KitchenDoorwayUsesCorrectTransitionType()
    {
        var sug = PlanRoute("tr_b_apps_kitchen_control", "B", 1216f, 384f, -256f, -1018.3f, 597.1f, -79.9f);
        var door = sug.TransitionWaypoints.First(w => w.Name == "t_b_apps_kitchen_doorway");
        Assert.Equal(TransitionWaypointType.STEP_UP, door.TransitionType);
        Assert.Equal(TransitionMovementAction.STEP_UP_JUMP_PULSE, door.MovementAction);
        Assert.True(door.AllowJumpPulse);
    }

    [Fact]
    public void PulseRequestIsDifferentFromPulseApplication()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        var eval = exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X + 20f, wp.Y, -168f, 180.0, false, true, null);
        Assert.True(eval.ShouldEmitJumpPulse);
        Assert.Equal(1, exec.PulseRequestsOnCurrentWp);
        Assert.Equal(0, exec.PulseApplicationsOnCurrentWp);
        Assert.False(exec.LastPulseWasApplied);
        Assert.Equal(StepUpPulseState.PULSE_REQUESTED, exec.PulseState);
    }

    [Fact]
    public void PulseApplicationIsRecorded()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X + 20f, wp.Y, -168f, 180.0, false, true, null);
        exec.NotifyJumpPulseApplied(100, inJumpObserved: true);
        Assert.Equal(1, exec.PulseApplicationsOnCurrentWp);
        Assert.True(exec.LastPulseWasApplied);
        Assert.Equal(StepUpPulseState.PULSE_APPLIED, exec.PulseState);
    }

    [Fact]
    public void StepRequiresObservedZGain()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X + 5f, wp.Y, -168f, 180.0, false, true, null);
        Assert.Equal(0, idx);
        Assert.False(exec.ObservedZGainOnCurrentWp);

        exec.NotifyJumpPulseApplied(100, true);
        exec.EvaluateStep(1, 110, 1.65, list, ref idx, wp.X + 2f, wp.Y, -112f, 160.0, false, true, null);
        Assert.Equal(1, idx);
    }

    [Fact]
    public void StepRequiresExpectedExitNavArea()
    {
        var nav = LoadMirageNav();
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f, navArea: 999999);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X, wp.Y, -168f, 180.0, false, true, nav);
        Assert.Equal(0, idx);
    }

    [Fact]
    public void SecondPulseRequiresFirstPulseFailure()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        var e1 = exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null);
        Assert.True(e1.ShouldEmitJumpPulse);

        var eMid = exec.EvaluateStep(1, 120, 1.8, list, ref idx, wp.X + 12f, wp.Y, -168f, 180.0, false, true, null);
        Assert.False(eMid.ShouldEmitJumpPulse);
        Assert.False(eMid.ShouldReturnAuthority);
    }

    [Fact]
    public void SecondPulseRequiresGroundRecovery()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null);
        var eFail1 = exec.EvaluateStep(1, 143, 2.2, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null);
        Assert.False(eFail1.ShouldReturnAuthority);
        Assert.Equal(StepUpPulseState.PULSE_FAILED, exec.PulseState);

        var eAir = exec.EvaluateStep(1, 145, 2.25, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null, isGrounded: false);
        Assert.False(eAir.ShouldEmitJumpPulse);

        var e2 = exec.EvaluateStep(1, 146, 2.27, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null, isGrounded: true);
        Assert.True(e2.ShouldEmitJumpPulse);
        Assert.Equal(2, exec.JumpPulsesIssued);
    }

    [Fact]
    public void MaximumTwoPulsesPerStep()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        Assert.True(exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null).ShouldEmitJumpPulse);
        exec.EvaluateStep(1, 142, 2.15, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null);
        Assert.True(exec.EvaluateStep(1, 145, 2.20, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null).ShouldEmitJumpPulse);

        var eEx = exec.EvaluateStep(1, 189, 2.9, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null);
        Assert.True(eEx.ShouldReturnAuthority);
        Assert.Equal("STEP_UP_RETRY_EXHAUSTED", eEx.ReturnAuthorityReason);
        Assert.Equal(2, exec.JumpPulsesIssued);
    }

    [Fact]
    public void ConsecutiveTickJumpIsImpossible()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        Assert.False(GeometricTransitionExecutor.CanEmitJumpPulseNow(wp, wp.X + 10f, wp.Y, -168f, 101, 100, 1, false, true, out string reason));
        Assert.Equal("COOLDOWN_ACTIVE", reason);
    }

    [Fact]
    public void ContinuousJumpIsImpossible()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        int pulseCount = 0;
        for (int t = 100; t <= 200; t++)
        {
            var e = exec.EvaluateStep(1, t, t / 64.0, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null);
            if (e.ShouldEmitJumpPulse) pulseCount++;
            if (e.ShouldReturnAuthority) break;
        }
        Assert.Equal(0, exec.ContinuousJumpViolations);
        Assert.InRange(pulseCount, 1, 2);
    }

    [Fact]
    public void SuccessfulStepDoesNotEmitSecondPulse()
    {
        var wp = MakeStepUpWp("t_palace_box_step_1", -13.5f, -1761.0f, -108.0f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -50f, -1761f, -108f) };

        Assert.True(exec.EvaluateStep(1, 100, 1.5, list, ref idx, wp.X + 15f, wp.Y, -168f, 180.0, false, true, null).ShouldEmitJumpPulse);
        exec.NotifyJumpPulseApplied(100, true);
        exec.EvaluateStep(1, 118, 1.8, list, ref idx, wp.X, wp.Y, -110f, 150.0, false, true, null);
        Assert.Equal(1, idx);
        Assert.Equal(1, exec.JumpPulsesIssued);
    }

    [Fact]
    public void FailedStepReturnsAuthorityAfterRetryExhaustion()
    {
        var wp = MakeStepUpWp("t_b_apps_kitchen_doorway", -962f, 563f, -45f);
        var exec = new GeometricTransitionExecutor();
        int idx = 0;
        var list = new List<RouteTransitionWaypoint> { wp, MakeStepUpWp("next", -1018f, 597f, -80f) };

        TransitionStepEvaluation? last = null;
        for (int t = 100; t <= 260; t++)
        {
            last = exec.EvaluateStep(1, t, t / 64.0, list, ref idx, wp.X + 15f, wp.Y, -81.7f, 150.0, false, true, null);
            if (last.ShouldReturnAuthority) break;
        }
        Assert.NotNull(last);
        Assert.True(last!.ShouldReturnAuthority);
        Assert.Equal("STEP_UP_RETRY_EXHAUSTED", last.ReturnAuthorityReason);
        Assert.Equal(2, exec.JumpPulsesIssued);
    }

    [Fact]
    public void ContactCancelsStepImmediately()
    {
        var ctrl = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        Assert.True(ctrl.TryStartCanaryForRound(
            roundId: 1, rawSlot: 2, playerPseudonym: "tr_2", team: "T", role: "EntryFragger",
            targetSpotId: "tr_a_ramp_staging_wait", spotSector: "A",
            startX: 1216f, startY: -384f, startZ: -163f,
            targetX: 260f, targetY: -940f, targetZ: -150f,
            tick: 100, isOpeningPhase: true, isBombPlanted: false));
        var dec = ctrl.EvaluateTick(1, 2, 101, 1200f, -384f, -163f, 200f, "weapon_ak47", true, true, false,
            "tr_a_ramp_staging_wait", "A", "EntryFragger", hasContact: true, tookDamage: false, hostileUtility: false, hasC4: false, "A");
        Assert.False(dec.CanaryControlling);
        Assert.Equal("CONTACT_INTERRUPTION", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void ARampRoutesRemainUnchanged()
    {
        var sug = PlanRoute("tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f);
        Assert.NotEmpty(sug.TransitionWaypoints);
        Assert.Equal("tr_a_ramp_staging_wait", sug.TransitionWaypoints[^1].Name);
        Assert.All(sug.TransitionWaypoints, w => Assert.False(w.AllowJumpPulse));
    }

    [Fact]
    public void BHouseRoutesRemainUnchanged()
    {
        var sug = PlanRoute("tr_b_apps_house_staging", "B", 1216f, 384f, -256f, -450f, 800f, -130f);
        Assert.NotEmpty(sug.TransitionWaypoints);
        Assert.Equal("tr_b_apps_house_staging", sug.TransitionWaypoints[^1].Name);
        Assert.DoesNotContain(sug.TransitionWaypoints, w => w.Name == "t_b_apps_kitchen_doorway");
    }

    [Fact]
    public void MidRoutesRemainUnchanged()
    {
        var sug = PlanRoute("tr_mid_top_control", "Mid", 1216f, -100f, -200f, -380f, -1380f, -140f);
        Assert.NotEmpty(sug.TransitionWaypoints);
        Assert.Equal("tr_mid_top_control", sug.TransitionWaypoints[^1].Name);
    }

    [Fact]
    public void CtRoutesRemainUnchanged()
    {
        var ctA = GeometricTransitionCatalog.BuildTransitionsForCtRoute("A", "a_triple_box_hold", -100f, -1900f, -168f);
        var ctWin = GeometricTransitionCatalog.BuildTransitionsForCtRoute("MID_WINDOW", "mid_window_right_deep", -1480f, -1010f, -168f);
        var ctMkt = GeometricTransitionCatalog.BuildTransitionsForCtRoute("B_MARKET", "b_market_hold", -1900f, -300f, -168f);
        Assert.Empty(ctA);
        Assert.NotEmpty(ctWin);
        Assert.NotEmpty(ctMkt);
    }

    [Fact]
    public void GoalOwnershipRemainsExact()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 2, "Bot", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(leaseMgr.HasActiveLease(2));
        Assert.True(leaseMgr.ReleaseLease(1, 150, "COMPLETED"));
        Assert.False(leaseMgr.HasActiveLease(2));
    }

    [Fact]
    public void RouteAndAuthorityAccountingClose()
    {
        var leaseMgr = new MovementAuthorityLeaseManager();
        Assert.True(leaseMgr.TryAcquireLease(1, 3, "Bot", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(leaseMgr.ReleaseLease(1, 200, "ROUTE_COMPLETED"));
        Assert.False(leaseMgr.HasActiveLease(3));
        Assert.Null(leaseMgr.ActiveLease);
    }
}
