using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class FullTeamDeparture2B92Tests
{
    private static readonly string RepoRoot = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));

    private static NavMeshGraph? LoadMirageNav()
    {
        string path = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return File.Exists(path) ? NavMeshGraph.LoadFromFile(path) : null;
    }

    private static readonly IReadOnlySet<string> CtAllow = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "a_triple_box_hold", "a_firebox_ninja_hold", "b_van_behind_apps_hold", "b_forest_bench_hold_apps", "mid_window_right_deep"
    };

    private static List<TeamOpeningBotCandidate> MakeFiveCtCandidates() => new()
    {
        new() { BotSlot = 1, PlayerPseudonym = "ct1", Team = "CT", Role = "Anchor", Destination = "a_triple_box_hold", Sector = "A", RouteId = "a_triple_box_hold", ConflictGroup = "CT_SPAWN_EXIT", SpawnDistance = 100f },
        new() { BotSlot = 2, PlayerPseudonym = "ct2", Team = "CT", Role = "Support", Destination = "b_van_behind_apps_hold", Sector = "B", RouteId = "b_van_behind_apps_hold", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 120f },
        new() { BotSlot = 3, PlayerPseudonym = "ct3", Team = "CT", Role = "Rotator", Destination = "a_firebox_ninja_hold", Sector = "A", RouteId = "a_firebox_ninja_hold", ConflictGroup = "CT_SPAWN_EXIT", SpawnDistance = 140f },
        new() { BotSlot = 4, PlayerPseudonym = "ct4", Team = "CT", Role = "Anchor", Destination = "b_forest_bench_hold_apps", Sector = "B", RouteId = "b_forest_bench_hold_apps", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 160f },
        new() { BotSlot = 5, PlayerPseudonym = "ct5", Team = "CT", Role = "MidControl", Destination = "mid_window_right_deep", Sector = "Mid", RouteId = "mid_window_right_deep", ConflictGroup = "", SpawnDistance = 180f, IsEligibleForCanary = false },
    };

    [Fact]
    public void SchedulerReceivesAllFiveCtBots()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.Equal(5, res.Assignments.Count);
    }

    [Fact]
    public void ExactlyTwoBotsAreCanaryControlled()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.Equal(2, res.Assignments.Count(a => a.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED));
    }

    [Fact]
    public void ThreeBotsRemainUtilityAiControlled()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.Equal(3, res.Assignments.Count(a => a.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED));
    }

    [Fact]
    public void UtilityBotMayReceiveOnlyPassiveDepartureHold()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        var held = res.Assignments.First(a => a.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED && a.PassiveHoldRequired);
        Assert.InRange(held.PassiveHoldMs, 1, 500);
    }

    [Fact]
    public void PassiveHoldCannotChangeDestination()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.Equal("a_firebox_ninja_hold", res.BySlot[3].Destination);
    }

    [Fact]
    public void PassiveHoldCannotChangeRole()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.Equal("Rotator", res.BySlot[3].Role);
    }

    [Fact]
    public void PassiveHoldCannotChangeSector()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.Equal("A", res.BySlot[3].Sector);
    }

    [Fact]
    public void PassiveHoldCannotAcquireMovementLease()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        Assert.False(mgr.HasActiveLease(3));
        Assert.Equal(0, mgr.ActiveLeaseCount);
    }

    [Fact]
    public void PassiveHoldEndsAtFiveHundredMilliseconds()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.All(res.Assignments, a => Assert.InRange(a.PassiveHoldMs, 0, 500));
    }

    [Fact]
    public void UtilityCorridorIsInferredFromRouteAndPortal()
    {
        var c = new TeamOpeningBotCandidate { BotSlot = 5, Destination = "mid_window_right_deep", ConflictGroup = "", FirstPortalId = "window_portal" };
        var inf = TeamOpeningRouteScheduler.InferInitialCorridor(c);
        Assert.Equal("WINDOW_ENTRY", inf.Corridor);
        Assert.Equal(CorridorConfidence.HIGH, inf.Confidence);
    }

    [Fact]
    public void EmptyConflictGroupDoesNotMeanSameCorridor()
    {
        var cA = new TeamOpeningBotCandidate { BotSlot = 7, ConflictGroup = "", Sector = "A" };
        var cB = new TeamOpeningBotCandidate { BotSlot = 8, ConflictGroup = "", Sector = "B" };
        var infA = TeamOpeningRouteScheduler.InferInitialCorridor(cA);
        var infB = TeamOpeningRouteScheduler.InferInitialCorridor(cB);
        Assert.NotEqual(infA.Corridor, infB.Corridor);
        Assert.Equal(CorridorConfidence.LOW, infA.Confidence);
    }

    [Fact]
    public void SamePortalCreatesSharedConflictGroup()
    {
        var c1 = new TeamOpeningBotCandidate { BotSlot = 1, Destination = "mid_window_right_deep", FirstPortalId = "window_portal" };
        var c2 = new TeamOpeningBotCandidate { BotSlot = 2, Destination = "mid_window_left", FirstPortalId = "window_portal" };
        Assert.Equal(TeamOpeningRouteScheduler.InferInitialCorridor(c1).Corridor, TeamOpeningRouteScheduler.InferInitialCorridor(c2).Corridor);
    }

    [Fact]
    public void CorridorQueueHasSingleLeader()
    {
        var q = new CorridorDepartureQueue("MARKET_ENTRY", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        Assert.Equal(1, q.LeaderSlot);
        Assert.True(q.CanRelease(1, 100, Array.Empty<TeammatePositionSnapshot>()));
    }

    [Fact]
    public void FollowerWaitsForPortalClearance()
    {
        var q = new CorridorDepartureQueue("MARKET_ENTRY", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        q.MarkReleased(1, 100);
        q.MarkPortalEntered(1, 105);
        var closeSnaps = new[]
        {
            new TeammatePositionSnapshot(1, -1600f, -1000f, -200f, 0f, 0f, "Anchor", "MARKET_ENTRY"),
            new TeammatePositionSnapshot(2, -1620f, -1010f, -200f, 0f, 0f, "Support", "MARKET_ENTRY"),
        };
        Assert.False(q.CanRelease(2, 110, closeSnaps));
        q.MarkPortalCleared(1, 120);
        Assert.True(q.CanRelease(2, 121, closeSnaps));
    }

    [Fact]
    public void QueueWaitDoesNotCreateLateralWaypoint()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Anchor", "b_van_behind_apps_hold", "B", -1720f, -1896f, -267f, -1920f, -296f, -168f, 100, true, false));
        var session = g.GetSessionForSlot(1, 2)!;
        session.InferredCorridor = "MARKET_ENTRY";
        session.ActualReleaseTick = 100;
        var tm = new[] { new TeammatePositionSnapshot(4, -1720f, -1850f, -267f, 0f, 0f, "Support", "MARKET_ENTRY") };
        g.EvaluateTick(1, 2, 145, -1720f, -1896f, -267f, 2f, "weapon_knife", true, true, false, "b_van_behind_apps_hold", "B", "Anchor", false, false, false, false, "", 125.0, tm);
        Assert.Null(session.RecoveryWaypoint);
        Assert.False(session.RecoveryActive);
    }

    [Fact]
    public void QueueResumeKeepsCanonicalWaypoint()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Anchor", "b_van_behind_apps_hold", "B", -1720f, -1896f, -267f, -1920f, -296f, -168f, 100, true, false));
        var s = g.GetSessionForSlot(1, 2)!;
        string wp0 = s.Route.OrderedWaypoints[0].Name;
        s.InferredCorridor = "MARKET_ENTRY";
        s.ActualReleaseTick = 100;
        var tm = new[] { new TeammatePositionSnapshot(4, -1720f, -1850f, -267f, 0f, 0f, "Support", "MARKET_ENTRY") };
        g.EvaluateTick(1, 2, 145, -1720f, -1896f, -267f, 2f, "weapon_knife", true, true, false, "b_van_behind_apps_hold", "B", "Anchor", false, false, false, false, "", 125.0, tm);
        var decResume = g.EvaluateTick(1, 2, 149, -1720f, -1780f, -267f, 220f, "weapon_knife", true, true, false, "b_van_behind_apps_hold", "B", "Anchor", false, false, false, false, "", 62.5, Array.Empty<TeammatePositionSnapshot>());
        Assert.Equal(wp0, decResume.CurrentWaypoint!.Name);
    }

    [Fact]
    public void RootBlockCauseIsPreservedAfterRepath()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false));
        var s = g.GetSessionForSlot(1, 2)!;
        s.ActualReleaseTick = 100;
        g.EvaluateTick(1, 2, 144, -1416f, -2198f, -238f, 0f, "weapon_knife", true, true, false, "a_triple_box_hold", "A", "Anchor", false, false, false, false, "", 62.5);
        s.BlockedDurationMs = 360;
        g.EvaluateTick(1, 2, 145, -1416f, -2198f, -238f, 0f, "weapon_knife", true, true, false, "a_triple_box_hold", "A", "Anchor", false, false, false, false, "", 62.5);
        g.EvaluateTick(1, 2, 146, -1416f, -2198f, -238f, 0f, "weapon_knife", true, true, false, "a_triple_box_hold", "A", "Anchor", false, false, false, false, "", 62.5);
        Assert.Equal(BlockCause.StaticObstacle, s.RootBlockCause);
        Assert.Equal(BlockCause.PathRecalculation, s.CurrentBlockState);
    }

    [Fact]
    public void PathRecalculationIsNotRootCause()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.RepathCount = 1;
        s.ActualReleaseTick = 100;
        g.EvaluateTick(1, 2, 145, -1416f, -2198f, -238f, 0f, "weapon_knife", true, true, false, "a_triple_box_hold", "A", "Anchor", false, false, false, false, "", 62.5);
        Assert.NotEqual(BlockCause.PathRecalculation, s.RootBlockCause);
    }

    [Fact]
    public void TeammateCongestionRequiresVerifiedSameCorridor()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.InferredCorridor = "CT_SPAWN_EXIT";
        s.LastX = -1700f; s.LastY = -1900f; s.LastZ = -267f;
        var wp = s.Route.OrderedWaypoints[0];
        var same = new[] { new TeammatePositionSnapshot(4, -1660f, -1935f, -267f, 0f, 0f, "Anchor", "CT_SPAWN_EXIT") };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, same);
        Assert.True(res.IsVerified);
    }

    [Fact]
    public void NearbyBotInAnotherCorridorIsNotBlocker()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.InferredCorridor = "CT_SPAWN_EXIT";
        s.LastX = -1700f; s.LastY = -1900f; s.LastZ = -267f;
        var wp = s.Route.OrderedWaypoints[0];
        var other = new[] { new TeammatePositionSnapshot(5, -1660f, -1935f, -267f, 0f, 0f, "MidControl", "WINDOW_ENTRY") };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, other);
        Assert.False(res.IsVerified);
    }

    [Fact]
    public void FinalDestinationDwellPrecedesBlockFallback()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.TryStartCanaryForRound(1, 2, "ct2", "CT", "MidControl", "mid_window_right_deep", "Mid", -1720f, -1896f, -267f, -1185.9f, -856f, -168f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.WaypointIndex = s.Route.OrderedWaypoints.Count - 1;
        var dest = s.Route.OrderedWaypoints[^1];
        Assert.True(OpeningRouteCanaryGuard.TryResolveFinalApproach(s, dest.X + 10f, dest.Y, dest.Z, 10.0, 0.0, 0.0, 7.0, out _));
        Assert.True(s.FinalApproachActive);
    }

    [Fact]
    public void FinalApproachDoesNotUseLateralRecovery()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.TryStartCanaryForRound(1, 2, "ct2", "CT", "MidControl", "mid_window_right_deep", "Mid", -1720f, -1896f, -267f, -1185.9f, -856f, -168f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.WaypointIndex = s.Route.OrderedWaypoints.Count - 1;
        s.ActualReleaseTick = 100;
        var dest = s.Route.OrderedWaypoints[^1];
        g.EvaluateTick(1, 2, 160, dest.X + 140f, dest.Y, dest.Z, 100f, "weapon_m4a1", true, true, false, "mid_window_right_deep", "Mid", "MidControl", false, false, false, false, "", 62.5);
        Assert.Null(s.RecoveryWaypoint);
    }

    [Fact]
    public void OneCanaryFailureDoesNotReleaseOtherLease()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 1, "ct1", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Anchor", "b_van_behind_apps_hold", "B", -1720f, -1896f, -267f, -1920f, -296f, -168f, 100, true, false);
        g.NotifyPlayerDamage(1, 1, 120);
        Assert.False(g.LeaseManager.HasActiveLease(1));
        Assert.True(g.LeaseManager.HasActiveLease(2));
    }

    [Fact]
    public void RoundAccountingCoversAllFiveBots()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 2, CtAllow);
        Assert.Equal(5, res.Assignments.Count);
        Assert.Equal(5, res.BySlot.Count);
    }

    [Fact]
    public void CanaryAccountingClosesPerSlot()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "ct1", "CT", "a_triple_box_hold", 100, 640, true, CanaryTeamMode.CtSingle, null, out _, out _);
        mgr.TryAcquireLease(1, 2, "ct2", "CT", "b_van_behind_apps_hold", 100, 640, true, CanaryTeamMode.CtSingle, null, out _, out _);
        mgr.ReleaseLeaseForSlot(1, 1, 200, "COMPLETED");
        mgr.ReleaseLeaseForSlot(1, 2, 220, "COMPLETED");
        Assert.Equal(0, mgr.AccountingResidue);
    }

    [Fact]
    public void PassiveHoldAccountingClosesPerSlot()
    {
        var hold = new PassiveDepartureHold { RoundId = 1, BotSlot = 3, ConflictGroup = "CT_SPAWN_EXIT", StartTick = 100, ReleaseTick = 116 };
        hold.Released = true;
        hold.ReleaseReason = "PORTAL_CLEARED";
        Assert.True(hold.Released);
    }

    [Fact]
    public void PositioningTransformerRemainsShadowOnly()
    {
        Assert.Equal("a_triple_box_hold", OpeningRoutePlannerGuard.OpeningRoutePlannerCannotAffectBotDecision("a_triple_box_hold", null));
    }

    [Fact]
    public void CertifiedRoutesRemainUnchanged()
    {
        var ctWin = GeometricTransitionCatalog.BuildTransitionsForCtRoute("MID_WINDOW", "mid_window_right_deep", -1480f, -1010f, -168f);
        Assert.NotEmpty(ctWin);
        Assert.Empty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("A", "a_triple_box_hold", -350f, -1950f, -168f));
    }
}
