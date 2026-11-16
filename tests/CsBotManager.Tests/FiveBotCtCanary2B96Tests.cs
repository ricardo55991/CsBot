using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class FiveBotCtCanary2B96Tests
{
    private static readonly string RepoRoot = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));

    private static NavMeshGraph? LoadMirageNav()
    {
        string path = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return File.Exists(path) ? NavMeshGraph.LoadFromFile(path) : null;
    }

    private static OpeningRouteCanaryGuard CreateFiveBotCtGuard()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 5;
        return g;
    }

    private static readonly IReadOnlySet<string> CtAllow = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "a_triple_box_hold", "a_firebox_ninja_hold", "b_van_behind_apps_hold", "b_forest_bench_hold_apps", "mid_window_right_deep"
    };

    private static List<TeamOpeningBotCandidate> MakeFiveCtCandidates() => new()
    {
        new() { BotSlot = 1, PlayerPseudonym = "ct1", Team = "CT", Role = "Anchor", Destination = "a_triple_box_hold", Sector = "A", RouteId = "a_triple_box_hold", ConflictGroup = "CT_SPAWN_EXIT", SpawnDistance = 100f },
        new() { BotSlot = 2, PlayerPseudonym = "ct2", Team = "CT", Role = "Support", Destination = "a_firebox_ninja_hold", Sector = "A", RouteId = "a_firebox_ninja_hold", ConflictGroup = "CT_SPAWN_EXIT", SpawnDistance = 120f },
        new() { BotSlot = 3, PlayerPseudonym = "ct3", Team = "CT", Role = "Rotator", Destination = "mid_window_right_deep", Sector = "Mid", RouteId = "mid_window_right_deep", ConflictGroup = "WINDOW_ENTRY", SpawnDistance = 140f },
        new() { BotSlot = 4, PlayerPseudonym = "ct4", Team = "CT", Role = "Anchor", Destination = "b_van_behind_apps_hold", Sector = "B", RouteId = "b_van_behind_apps_hold", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 160f },
        new() { BotSlot = 5, PlayerPseudonym = "ct5", Team = "CT", Role = "Support", Destination = "b_forest_bench_hold_apps", Sector = "B", RouteId = "b_forest_bench_hold_apps", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 180f },
    };

    [Fact]
    public void FiveCtBotsCreateFiveControllers()
    {
        var g = CreateFiveBotCtGuard();
        Assert.True(g.TryStartCanaryForRound(1, 1, "ct1", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false));
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Support", "a_firebox_ninja_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false));
        Assert.True(g.TryStartCanaryForRound(1, 3, "ct3", "CT", "Rotator", "mid_window_right_deep", "Mid", -1720f, -1896f, -267f, -1480f, -1010f, -168f, 100, true, false));
        Assert.True(g.TryStartCanaryForRound(1, 4, "ct4", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false));
        Assert.True(g.TryStartCanaryForRound(1, 5, "ct5", "CT", "Support", "a_firebox_ninja_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false));
        Assert.Equal(5, g.GetSessionsForRound(1).Count);
    }

    [Fact]
    public void FiveCtBotsAcquireFiveIndependentLeases()
    {
        var g = CreateFiveBotCtGuard();
        for (int s = 1; s <= 5; s++)
        {
            g.TryStartCanaryForRound(1, s, $"ct{s}", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        }
        Assert.Equal(5, g.LeaseManager.ActiveLeaseCount);
    }

    [Fact]
    public void PortalCannotClearByElapsedTicksAlone()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT", 110f, 500) { RequiresPhysicalPortalClearance = true };
        q.Enqueue(1);
        q.Enqueue(2);
        q.MarkReleased(1, 100);
        q.MarkPortalEntered(1, 102);
        var closeSnaps = new[] { new TeammatePositionSnapshot(1, -1700f, -1900f, -267f), new TeammatePositionSnapshot(2, -1715f, -1896f, -267f) };
        Assert.False(q.CanRelease(2, 160, closeSnaps));
    }

    [Fact]
    public void PortalClearsWhenExitAreaIsReached()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT", 110f, 500) { PortalEntryArea = 10, PortalExitArea = 20 };
        q.Enqueue(1);
        q.Enqueue(2);
        q.MarkReleased(1, 100);
        Assert.True(q.TryConfirmPortalCrossing(1, 115, currentNavArea: 20, exitNavArea: 20, distFromEntry: 50f));
        Assert.True(q.PortalCrossingConfirmed);
        Assert.True(q.CanRelease(2, 116, Array.Empty<TeammatePositionSnapshot>()));
    }

    [Fact]
    public void PortalClearsWhenExitPlaneIsCrossed()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        q.MarkReleased(1, 100);
        Assert.True(q.TryConfirmPortalCrossing(1, 120, currentNavArea: 0, exitNavArea: 0, distFromEntry: 120f));
        Assert.True(q.CanRelease(2, 121, Array.Empty<TeammatePositionSnapshot>()));
    }

    [Fact]
    public void SharedPortalHasExactlyOneLeader()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 5, CtAllow);
        Assert.Single(res.Assignments.Where(a => a.ConflictGroup == "CT_SPAWN_EXIT"), a => a.IsLeader);
        Assert.Single(res.Assignments.Where(a => a.ConflictGroup == "MARKET_ENTRY"), a => a.IsLeader);
    }

    [Fact]
    public void EveryFollowerHasDirectPredecessor()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 5, CtAllow);
        foreach (var a in res.Assignments.Where(a => !a.IsLeader))
        {
            Assert.NotNull(a.PredecessorSlot);
        }
    }

    [Fact]
    public void FiveBotQueueHasUniqueReleaseOrder()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = MakeFiveCtCandidates().Select(c => c with { ConflictGroup = "CT_SPAWN_EXIT" }).ToList();
        var res = sched.ScheduleFullTeamDeparture(1, cands, "", 100, 5, CtAllow);
        Assert.Equal(5, res.Assignments.Select(a => a.PlannedReleaseTick).Distinct().Count());
    }

    [Fact]
    public void FollowersCannotReleaseSimultaneously()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = MakeFiveCtCandidates().Select(c => c with { ConflictGroup = "CT_SPAWN_EXIT" }).ToList();
        var res = sched.ScheduleFullTeamDeparture(1, cands, "", 100, 5, CtAllow);
        var ticks = res.Assignments.Select(a => a.PlannedReleaseTick).OrderBy(t => t).ToList();
        for (int i = 1; i < ticks.Count; i++)
        {
            Assert.True(ticks[i] > ticks[i - 1]);
        }
    }

    [Fact]
    public void PlannedTimeDoesNotOverrideOccupiedPortal()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT", 110f, 500) { RequiresPhysicalPortalClearance = true };
        q.Enqueue(1);
        q.Enqueue(2);
        q.MarkReleased(1, 100);
        q.MarkPortalEntered(1, 101);
        Assert.False(q.CanRelease(2, 200, Array.Empty<TeammatePositionSnapshot>()));
    }

    [Fact]
    public void ScheduledWaitDoesNotCountAsBlocked()
    {
        var g = CreateFiveBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct2", "CT", "Support", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false, explicitStaggerMs: 250);
        var s = g.GetSessionForSlot(1, 2)!;
        s.ActualReleaseTick = 120;
        g.EvaluateTick(1, 2, 117, -1720f, -1896f, -267f, 0f, "weapon_knife", true, true, false, "a_triple_box_hold", "A", "Support", false, false, false);
        Assert.Equal(0, s.BlockedDurationMs);
        Assert.True(s.ScheduledWaitMs > 0);
    }

    [Fact]
    public void IndividualFailureReleasesOnlyOneLease()
    {
        var g = CreateFiveBotCtGuard();
        for (int s = 1; s <= 5; s++)
            g.TryStartCanaryForRound(1, s, $"ct{s}", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        g.NotifyPlayerDamage(1, 3, 120);
        Assert.False(g.LeaseManager.HasActiveLease(3));
        Assert.Equal(4, g.LeaseManager.ActiveLeaseCount);
    }

    [Fact]
    public void InterruptedLeaderPromotesNextFollower()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        q.Enqueue(3);
        q.Remove(1);
        Assert.Equal(2, q.LeaderSlot);
    }

    [Fact]
    public void DifferentCorridorsMayReleaseTogether()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 5, CtAllow);
        Assert.Equal(3, res.Assignments.Count(a => a.PlannedReleaseTick == 100));
    }

    [Fact]
    public void SameCorridorCannotReleaseTogether()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveCtCandidates(), "", 100, 5, CtAllow);
        Assert.NotEqual(res.BySlot[1].PlannedReleaseTick, res.BySlot[2].PlannedReleaseTick);
    }

    [Fact]
    public void FinalApproachRemainsRecognized()
    {
        var g = CreateFiveBotCtGuard();
        g.TryStartCanaryForRound(1, 3, "ct3", "CT", "Rotator", "mid_window_right_deep", "Mid", -1720f, -1896f, -267f, -1480f, -1010f, -168f, 100, true, false);
        var s = g.GetSessionForSlot(1, 3)!;
        s.WaypointIndex = s.Route.OrderedWaypoints.Count - 1;
        var dest = s.Route.OrderedWaypoints[^1];
        Assert.True(OpeningRouteCanaryGuard.TryResolveFinalApproach(s, dest.X + 5f, dest.Y, dest.Z, 5.0, 0.0, 0.0, 7.0, out _));
    }

    [Fact]
    public void GoalOwnershipRemainsExactPerSlot()
    {
        var g = CreateFiveBotCtGuard();
        for (int s = 1; s <= 5; s++)
            g.TryStartCanaryForRound(1, s, $"ct{s}", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        for (int s = 1; s <= 5; s++)
            Assert.True(g.LeaseManager.HasActiveLease(s));
    }

    [Fact]
    public void WeaponReadinessRemainsActivePerSlot()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 1, "ct1", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, out var sug));
        Assert.True(sug!.KnifeAllowedUntil > 0);
    }

    [Fact]
    public void CertifiedRoutesRemainUnchanged()
    {
        Assert.Empty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("A", "a_triple_box_hold", -350f, -1950f, -168f));
        Assert.NotEmpty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("MID_WINDOW", "mid_window_right_deep", -1480f, -1010f, -168f));
    }

    [Fact]
    public void RouteAccountingClosesForFiveSlots()
    {
        var g = CreateFiveBotCtGuard();
        for (int s = 1; s <= 5; s++)
            g.TryStartCanaryForRound(1, s, $"ct{s}", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        Assert.Equal(5, g.FinalizeAllOpenSessions("ROUND_END", 250));
    }

    [Fact]
    public void AuthorityAccountingClosesForFiveSlots()
    {
        var g = CreateFiveBotCtGuard();
        for (int s = 1; s <= 5; s++)
            g.TryStartCanaryForRound(1, s, $"ct{s}", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        for (int s = 1; s <= 5; s++)
            g.LeaseManager.ReleaseLeaseForSlot(1, s, 250, "DONE");
        Assert.Equal(0, g.LeaseManager.AccountingResidue);
    }

    [Fact]
    public void RoundEndReleasesAllFiveLeases()
    {
        var g = CreateFiveBotCtGuard();
        for (int s = 1; s <= 5; s++)
            g.TryStartCanaryForRound(1, s, $"ct{s}", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        g.LeaseManager.OnRoundEnd(1, 300);
        Assert.Equal(0, g.LeaseManager.ActiveLeaseCount);
        Assert.Equal(0, g.LeaseManager.AccountingResidue);
    }

    [Fact]
    public void KillSwitchReleasesAllFiveLeases()
    {
        var g = CreateFiveBotCtGuard();
        for (int s = 1; s <= 5; s++)
            g.TryStartCanaryForRound(1, s, $"ct{s}", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        g.LeaseManager.ReleaseAllLeases(200, "KILL_SWITCH_DISABLED");
        Assert.Equal(0, g.LeaseManager.ActiveLeaseCount);
    }

    [Fact]
    public void NonCanarySystemsRemainUnchanged()
    {
        Assert.Equal("a_triple_box_hold", OpeningRoutePlannerGuard.OpeningRoutePlannerCannotAffectBotDecision("a_triple_box_hold", null));
    }
}
