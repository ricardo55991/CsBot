using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class TwoBotCtLiveIntegration2B91Tests
{
    private static readonly string RepoRoot = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));

    private static NavMeshGraph? LoadMirageNav()
    {
        string path = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return File.Exists(path) ? NavMeshGraph.LoadFromFile(path) : null;
    }

    private static OpeningRouteCanaryGuard CreateTwoBotCtGuard()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.CtSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        return g;
    }

    private static readonly IReadOnlySet<string> CtAllow = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "a_triple_box_hold", "b_van_behind_apps_hold", "mid_window_right_deep", "b_forest_bench_hold_apps"
    };

    [Fact]
    public void SchedulerSelectsTwoEligibleCtBots()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "CT", Role = "Anchor", Destination = "a_triple_box_hold", RouteId = "a_triple_box_hold", ConflictGroup = "CT_SPAWN_EXIT" },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "CT", Role = "Anchor", Destination = "b_van_behind_apps_hold", RouteId = "b_van_behind_apps_hold", ConflictGroup = "MARKET_ENTRY" },
            new TeamOpeningBotCandidate { BotSlot = 3, Team = "CT", Role = "Support", Destination = "mid_window_right_deep", RouteId = "mid_window_right_deep", ConflictGroup = "WINDOW_ENTRY" },
        };
        var res = sched.Schedule(cands, "", 100, 2, CtAllow);
        Assert.Equal(2, res.Count(r => !r.FallbackToUtilityAi));
    }

    [Fact]
    public void TwoDistinctControllersAreCreated()
    {
        var g = CreateTwoBotCtGuard();
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false));
        Assert.True(g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false));
        var sessions = g.GetSessionsForRound(1);
        Assert.Equal(2, sessions.Count);
        Assert.Equal(2, sessions.Select(s => s.RawSlot).Distinct().Count());
    }

    [Fact]
    public void TwoDistinctLeasesAreAcquired()
    {
        var g = CreateTwoBotCtGuard();
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false));
        Assert.True(g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false));
        Assert.Equal(2, g.LeaseManager.ActiveLeaseCount);
        Assert.NotNull(g.LeaseManager.GetActiveLeaseForSlot(2));
        Assert.NotNull(g.LeaseManager.GetActiveLeaseForSlot(4));
    }

    [Fact]
    public void ControllerDictionaryUsesBotSlot()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 5, "ct_5", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        Assert.Equal(2, g.GetSessionForSlot(1, 2)!.RawSlot);
        Assert.Equal(5, g.GetSessionForSlot(1, 5)!.RawSlot);
    }

    [Fact]
    public void SecondControllerDoesNotReplaceFirst()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        var first = g.GetSessionForSlot(1, 2);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        Assert.Same(first, g.GetSessionForSlot(1, 2));
    }

    [Fact]
    public void EachControllerHasIndependentRouteState()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        Assert.Equal("a_triple_box_hold", g.GetSessionForSlot(1, 2)!.OriginalDestination);
        Assert.Equal("b_van_behind_apps_hold", g.GetSessionForSlot(1, 4)!.OriginalDestination);
    }

    [Fact]
    public void EachControllerHasIndependentDeadline()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false, explicitStaggerMs: 0);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false, explicitStaggerMs: 250);
        Assert.NotEqual(g.GetSessionForSlot(1, 2)!.Schedule.PlannedReleaseTick, g.GetSessionForSlot(1, 4)!.Schedule.PlannedReleaseTick);
    }

    [Fact]
    public void EachControllerHasIndependentAuthority()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        Assert.True(g.LeaseManager.HasActiveLease(2));
        Assert.True(g.LeaseManager.HasActiveLease(4));
        Assert.False(g.LeaseManager.HasActiveLease(3));
    }

    [Fact]
    public void IndividualFailureReleasesOnlyOneLease()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        g.NotifyPlayerDamage(1, 2, 110);
        Assert.False(g.LeaseManager.HasActiveLease(2));
        Assert.True(g.LeaseManager.HasActiveLease(4));
    }

    [Fact]
    public void IndividualArrivalReleasesOnlyOneLease()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        g.LeaseManager.ReleaseLeaseForSlot(1, 2, 200, "ROUTE_COMPLETED");
        Assert.False(g.LeaseManager.HasActiveLease(2));
        Assert.True(g.LeaseManager.HasActiveLease(4));
    }

    [Fact]
    public void FirstBotContinuesWhenSecondFails()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -1720f, -1896f, -267f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -1720f, -1896f, -267f, -1800f, -300f, -168f, 100, true, false);
        g.NotifyPlayerDamage(1, 4, 115);
        var dec1 = g.EvaluateTick(1, 2, 116, -1680f, -1920f, -267f, 200f, "weapon_knife", true, true, false, "a_triple_box_hold", "A", "Anchor", false, false, false);
        Assert.True(dec1.CanaryControlling);
    }

    [Fact]
    public void SecondBotContinuesWhenFirstFails()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        g.NotifyPlayerDamage(1, 2, 115);
        var dec2 = g.EvaluateTick(1, 4, 116, -2350f, -1800f, -168f, 200f, "weapon_knife", true, true, false, "b_van_behind_apps_hold", "B", "Anchor", false, false, false);
        Assert.True(dec2.CanaryControlling);
    }

    [Fact]
    public void ConflictGroupSelectsOneLeader()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "CT", Role = "Anchor", Destination = "b_van_behind_apps_hold", RouteId = "b_van_behind_apps_hold", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 100f },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "CT", Role = "Support", Destination = "b_forest_bench_hold_apps", RouteId = "b_forest_bench_hold_apps", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 200f }
        };
        var res = sched.Schedule(cands, "", 100, 2, CtAllow);
        Assert.Single(res, r => !r.FallbackToUtilityAi && r.StaggerMs == 0);
    }

    [Fact]
    public void FollowerStartsAfterConfiguredDelay()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "CT", Role = "Anchor", Destination = "b_van_behind_apps_hold", RouteId = "b_van_behind_apps_hold", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 100f },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "CT", Role = "Support", Destination = "b_forest_bench_hold_apps", RouteId = "b_forest_bench_hold_apps", ConflictGroup = "MARKET_ENTRY", SpawnDistance = 200f }
        };
        var res = sched.Schedule(cands, "", 100, 2, CtAllow);
        var follower = res.First(r => r.PredecessorSlot != null);
        Assert.Equal(250, follower.StaggerMs);
        Assert.True(follower.PlannedReleaseTick > 100);
    }

    [Fact]
    public void NonConflictingBotsMayStartTogether()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "CT", Role = "Anchor", Destination = "a_triple_box_hold", RouteId = "a_triple_box_hold", ConflictGroup = "CT_SPAWN_EXIT" },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "CT", Role = "Anchor", Destination = "b_van_behind_apps_hold", RouteId = "b_van_behind_apps_hold", ConflictGroup = "MARKET_ENTRY" }
        };
        var res = sched.Schedule(cands, "", 100, 2, CtAllow);
        Assert.All(res, r => Assert.Equal(0, r.StaggerMs));
    }

    [Fact]
    public void InsufficientSecondBotDoesNotCreateFakeSession()
    {
        var g = CreateTwoBotCtGuard();
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false));
        Assert.Single(g.GetSessionsForRound(1));
    }

    [Fact]
    public void RoundRequiresTwoSessionsToCountAsComplete()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        Assert.NotEqual(2, g.GetSessionsForRound(1).Count);
    }

    [Fact]
    public void MaximumConcurrentCtCanariesIsTwo()
    {
        var g = CreateTwoBotCtGuard();
        Assert.True(g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false));
        Assert.True(g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false));
        Assert.False(g.TryStartCanaryForRound(1, 5, "ct_5", "CT", "Support", "mid_window_right_deep", "Mid", -2400f, -1800f, -168f, -1480f, -1010f, -168f, 100, true, false));
        Assert.Equal(2, g.GetSessionsForRound(1).Count);
    }

    [Fact]
    public void RoundEndReleasesBothLeases()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        g.LeaseManager.OnRoundEnd(1, 300);
        Assert.Equal(0, g.LeaseManager.ActiveLeaseCount);
        Assert.Equal(0, g.LeaseManager.AccountingResidue);
    }

    [Fact]
    public void KillSwitchReleasesBothLeases()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        g.LeaseManager.ReleaseAllLeases(200, "KILL_SWITCH_DISABLED");
        Assert.Equal(0, g.LeaseManager.ActiveLeaseCount);
        Assert.Equal(0, g.LeaseManager.AccountingResidue);
    }

    [Fact]
    public void PositioningTransformerRemainsShadowOnly()
    {
        Assert.Equal("a_triple_box_hold", OpeningRoutePlannerGuard.OpeningRoutePlannerCannotAffectBotDecision("a_triple_box_hold", null));
    }

    [Fact]
    public void NonCanaryBotsRemainUnderUtilityAI()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        var decOther = g.EvaluateTick(1, 9, 105, -2300f, -1800f, -168f, 200f, "weapon_m4a1", true, true, false, "a_stairs_hold", "A", "Rotator", false, false, false);
        Assert.False(decOther.CanaryControlling);
        Assert.Equal("UTILITY_AI", decOther.Authority);
    }

    [Fact]
    public void RouteAccountingClosesPerSlot()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        Assert.Equal(2, g.FinalizeAllOpenSessions("ROUND_END", 250));
        Assert.Equal(0, g.LeaseManager.ActiveLeaseCount);
    }

    [Fact]
    public void AuthorityAccountingClosesPerSlot()
    {
        var g = CreateTwoBotCtGuard();
        g.TryStartCanaryForRound(1, 2, "ct_2", "CT", "Anchor", "a_triple_box_hold", "A", -2400f, -1800f, -168f, -350f, -1950f, -168f, 100, true, false);
        g.TryStartCanaryForRound(1, 4, "ct_4", "CT", "Anchor", "b_van_behind_apps_hold", "B", -2400f, -1800f, -168f, -1800f, -300f, -168f, 100, true, false);
        g.LeaseManager.ReleaseLeaseForSlot(1, 2, 200, "DONE");
        g.LeaseManager.ReleaseLeaseForSlot(1, 4, 210, "DONE");
        Assert.Equal(0, g.LeaseManager.AccountingResidue);
    }
}
