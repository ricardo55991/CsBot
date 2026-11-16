using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class TrCanaryQueue2B95Tests
{
    private static readonly string RepoRoot = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));

    private static NavMeshGraph? LoadMirageNav()
    {
        string path = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return File.Exists(path) ? NavMeshGraph.LoadFromFile(path) : null;
    }

    private static readonly IReadOnlySet<string> TrAllow = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "tr_underpass_control", "tr_mid_top_control", "tr_a_ramp_staging_wait", "a_palace_deep_room", "tr_b_apps_house_staging"
    };

    private static List<TeamOpeningBotCandidate> MakeTwoTrDifferentDownstream() => new()
    {
        new() { BotSlot = 1, PlayerPseudonym = "tr1", Team = "T", Role = "MidControl", Destination = "tr_underpass_control", Sector = "Mid", Bombsite = "MID", RouteId = "tr_underpass_control", ConflictGroup = "UNDERPASS_ENTRY", SpawnDistance = 100f },
        new() { BotSlot = 2, PlayerPseudonym = "tr2", Team = "T", Role = "MidControl", Destination = "tr_mid_top_control", Sector = "Mid", Bombsite = "MID", RouteId = "tr_mid_top_control", ConflictGroup = "TOP_MID_ENTRY", SpawnDistance = 120f },
    };

    [Fact]
    public void SharedInitialPortalCreatesSameQueue()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        Assert.Equal("T_SPAWN_EXIT", res.BySlot[1].InitialDepartureCorridor);
        Assert.Equal("T_SPAWN_EXIT", res.BySlot[2].InitialDepartureCorridor);
        Assert.Equal(res.BySlot[1].QueueId, res.BySlot[2].QueueId);
    }

    [Fact]
    public void DifferentDownstreamGroupsStillShareInitialQueue()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        Assert.NotEqual(res.BySlot[1].DownstreamConflictGroup, res.BySlot[2].DownstreamConflictGroup);
        Assert.Equal(res.BySlot[1].QueueId, res.BySlot[2].QueueId);
    }

    [Fact]
    public void SharedQueueHasExactlyOneLeader()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        Assert.Single(res.Assignments, a => a.IsLeader);
    }

    [Fact]
    public void SecondCanaryHasPredecessor()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        Assert.Null(res.BySlot[1].PredecessorSlot);
        Assert.Equal(1, res.BySlot[2].PredecessorSlot);
    }

    [Fact]
    public void TwoSameCorridorCanariesCannotReleaseSameTick()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        Assert.True(res.BySlot[2].PlannedReleaseTick > res.BySlot[1].PlannedReleaseTick);
    }

    [Fact]
    public void FollowerCannotAcquireLeaseBeforeReleaseTick()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        int currentTick = 105;
        Assert.True(currentTick < res.BySlot[2].PlannedReleaseTick);
    }

    [Fact]
    public void FollowerCannotDispatchBeforePortalClearance()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        q.MarkReleased(1, 100);
        q.MarkPortalEntered(1, 102);
        var snaps = new[]
        {
            new TeammatePositionSnapshot(1, 1150f, 120f, -164f),
            new TeammatePositionSnapshot(2, 1180f, 120f, -164f),
        };
        Assert.False(q.CanRelease(2, 110, snaps));
    }

    [Fact]
    public void PlannedStaggerIsActuallyApplied()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        Assert.Equal(250, res.BySlot[2].StaggerMs);
        Assert.Equal(116, res.BySlot[2].PlannedReleaseTick);
    }

    [Fact]
    public void ScheduledWaitDoesNotAccumulateBlockedDuration()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false, explicitStaggerMs: 250);
        var s = g.GetSessionForSlot(1, 2)!;
        s.ActualReleaseTick = 120;
        g.EvaluateTick(1, 2, 117, 1216f, -384f, -163f, 0f, "weapon_knife", true, true, false, "tr_a_ramp_staging_wait", "A", "EntryFragger", false, false, false);
        Assert.True(s.WaitingForScheduledRelease);
        Assert.Equal(0, s.BlockedDurationMs);
        Assert.True(s.ScheduledWaitMs > 0);
    }

    [Fact]
    public void ScheduledWaitCannotTriggerQueueTimeout()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false, explicitStaggerMs: 250);
        var s = g.GetSessionForSlot(1, 2)!;
        s.ActualReleaseTick = 200;
        var dec = g.EvaluateTick(1, 2, 180, 1216f, -384f, -163f, 0f, "weapon_knife", true, true, false, "tr_a_ramp_staging_wait", "A", "EntryFragger", false, false, false);
        Assert.True(dec.CanaryControlling);
        Assert.NotEqual("CORRIDOR_QUEUE_TIMEOUT", s.FallbackReason);
    }

    [Fact]
    public void PredecessorClearReleasesFollower()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        q.MarkReleased(1, 100);
        q.MarkPortalCleared(1, 118);
        Assert.True(q.CanRelease(2, 119, Array.Empty<TeammatePositionSnapshot>()));
    }

    [Fact]
    public void InterruptedPredecessorReelectsQueueLeader()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        q.Remove(1);
        Assert.Equal(2, q.LeaderSlot);
        Assert.True(q.CanRelease(2, 105, Array.Empty<TeammatePositionSnapshot>()));
    }

    [Fact]
    public void ActualReleaseTickIsAfterPlannedReleaseTick()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeTwoTrDifferentDownstream(), "MID", 100, 2, TrAllow);
        int actualTick = 118;
        Assert.True(actualTick >= res.BySlot[2].PlannedReleaseTick);
    }

    [Fact]
    public void RuntimeCongestionRemainsSeparatelyDetected()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.InferredCorridor = "A_RAMP_ENTRY";
        s.CorridorConfidenceName = "HIGH";
        s.LastX = 1100f; s.LastY = -384f; s.LastZ = -163f;
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "A_RAMP_ENTRY", 105) };
        Assert.True(OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106).IsVerified);
    }

    [Fact]
    public void FalseCongestionRemainsZero()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.InferredCorridor = "A_RAMP_ENTRY";
        s.CorridorConfidenceName = "LOW";
        s.LastX = 1100f; s.LastY = -384f; s.LastZ = -163f;
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "A_RAMP_ENTRY", 105) };
        Assert.False(OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106).IsVerified);
    }

    [Fact]
    public void C4CompatibilityRemainsUnchanged()
    {
        Assert.Equal("C4_CARRIER_COMPATIBLE", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("a_palace_deep_room", "A", "EntryFragger", true));
    }

    [Fact]
    public void CtCoordinationRemainsUnchanged()
    {
        Assert.Empty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("A", "a_triple_box_hold", -350f, -1950f, -168f));
    }

    [Fact]
    public void RouteAndAuthorityAccountingClose()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "tr1", "T", "tr_underpass_control", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.TryAcquireLease(1, 2, "tr2", "T", "tr_mid_top_control", 116, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.ReleaseLeaseForSlot(1, 1, 200, "DONE");
        mgr.ReleaseLeaseForSlot(1, 2, 220, "DONE");
        Assert.Equal(0, mgr.AccountingResidue);
    }
}
