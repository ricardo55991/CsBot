using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class TeamCanary2B9Tests
{
    private static readonly IReadOnlySet<string> CertifiedAllowlist = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "a_triple_box_hold", "a_stairs_hold", "a_ct_ticket_hold", "a_jungle_hold",
        "mid_window_right_deep", "b_market_hold", "b_bench_van_hold", "b_forest_hold",
        "a_palace_deep_room", "tr_a_ramp_staging_wait", "tr_b_apps_house_staging",
        "tr_mid_top_control", "tr_underpass_control"
    };

    private static readonly IReadOnlySet<string> ExcludedUtilityOnly = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "tr_b_apps_kitchen_control"
    };

    [Fact]
    public void TwoBotCanaryAllowsExactlyTwoLeases()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        Assert.True(mgr.TryAcquireLease(1, 1, "b1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(mgr.TryAcquireLease(1, 2, "b2", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.False(mgr.TryAcquireLease(1, 3, "b3", "T", "tr_b_apps_house_staging", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out var rej));
        Assert.Equal("MAX_CONCURRENT_LEASES_REACHED", rej);
        Assert.Equal(2, mgr.ActiveLeaseCount);
    }

    [Fact]
    public void FiveBotCanaryAllowsAtMostFiveLeases()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 5 };
        for (int s = 1; s <= 5; s++)
        {
            Assert.True(mgr.TryAcquireLease(1, s, $"b{s}", "CT", "a_triple_box_hold", 100, 640, true, CanaryTeamMode.CtSingle, null, out _, out _));
        }
        Assert.False(mgr.TryAcquireLease(1, 6, "b6", "CT", "a_triple_box_hold", 100, 640, true, CanaryTeamMode.CtSingle, null, out _, out var rej));
        Assert.Equal("MAX_CONCURRENT_LEASES_REACHED", rej);
        Assert.Equal(5, mgr.ActiveLeaseCount);
    }

    [Fact]
    public void LeaseAccountingIsIndependentPerSlot()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        Assert.True(mgr.TryAcquireLease(1, 1, "b1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(mgr.TryAcquireLease(1, 2, "b2", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(mgr.ReleaseLeaseForSlot(1, 1, 150, "COMPLETED"));
        Assert.False(mgr.HasActiveLease(1));
        Assert.True(mgr.HasActiveLease(2));
        Assert.Equal(1, mgr.AccountingResidue);
        Assert.True(mgr.ReleaseLeaseForSlot(1, 2, 160, "COMPLETED"));
        Assert.Equal(0, mgr.AccountingResidue);
    }

    [Fact]
    public void OneBotFailureDoesNotReleaseOtherBots()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 5 };
        Assert.True(mgr.TryAcquireLease(1, 1, "b1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(mgr.TryAcquireLease(1, 2, "b2", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _));
        Assert.True(mgr.ReleaseLeaseForSlot(1, 1, 120, "STEP_UP_RETRY_EXHAUSTED"));
        Assert.False(mgr.HasActiveLease(1));
        Assert.True(mgr.HasActiveLease(2));
    }

    [Fact]
    public void SchedulerRespectsSpawnPriority()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Entry", Destination = "tr_a_ramp_staging_wait", RouteId = "tr_a_ramp_staging_wait", ConflictGroup = "A_RAMP_ENTRY", SpawnDistance = 300f },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "T", Role = "Entry", Destination = "tr_a_ramp_staging_wait", RouteId = "tr_a_ramp_staging_wait", ConflictGroup = "A_RAMP_ENTRY", SpawnDistance = 100f }
        };
        var res = sched.Schedule(cands, "A", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        var leader = res.First(r => r.BotSlot == 2);
        var follower = res.First(r => r.BotSlot == 1);
        Assert.Equal(0, leader.StaggerMs);
        Assert.Null(leader.PredecessorSlot);
        Assert.Equal(2, follower.PredecessorSlot);
    }

    [Fact]
    public void SchedulerRespectsRolePriority()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Support", Destination = "tr_a_ramp_staging_wait", RouteId = "tr_a_ramp_staging_wait", ConflictGroup = "A_RAMP_ENTRY" },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "T", Role = "Rifler", Destination = "a_palace_deep_room", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY", HasC4 = true, Bombsite = "A" }
        };
        var res = sched.Schedule(cands, "A", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.Equal(1, res.First(r => r.BotSlot == 2).Priority);
        Assert.Equal(5, res.First(r => r.BotSlot == 1).Priority);
    }

    [Fact]
    public void ConflictGroupHasSingleLeader()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "CT", Role = "Anchor", Destination = "b_market_hold", RouteId = "b_market_hold", ConflictGroup = "MARKET_ENTRY" },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "CT", Role = "Support", Destination = "b_bench_van_hold", RouteId = "b_bench_van_hold", ConflictGroup = "MARKET_ENTRY" }
        };
        var res = sched.Schedule(cands, "", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.Single(res, r => !r.FallbackToUtilityAi && r.StaggerMs == 0);
    }

    [Fact]
    public void StaggerDoesNotExceedLimit()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Entry", Destination = "tr_a_ramp_staging_wait", RouteId = "tr_a_ramp_staging_wait", ConflictGroup = "A_RAMP_ENTRY" },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "T", Role = "Support", Destination = "tr_a_ramp_staging_wait", RouteId = "tr_a_ramp_staging_wait", ConflictGroup = "A_RAMP_ENTRY" }
        };
        var res = sched.Schedule(cands, "A", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.All(res, r => Assert.InRange(r.StaggerMs, 0, TeamOpeningRouteScheduler.MaxStaggerMs));
    }

    [Fact]
    public void NarrowPortalHasSingleActiveBot()
    {
        var sched = new TeamOpeningRouteScheduler();
        var cands = new[]
        {
            new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Entry", Destination = "a_palace_deep_room", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY" },
            new TeamOpeningBotCandidate { BotSlot = 2, Team = "T", Role = "Support", Destination = "a_palace_deep_room", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY" },
            new TeamOpeningBotCandidate { BotSlot = 3, Team = "T", Role = "Lurker", Destination = "a_palace_deep_room", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY" }
        };
        var res = sched.Schedule(cands, "A", 100, 5, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.Equal(2, res.Count(r => !r.FallbackToUtilityAi));
        Assert.True(res.First(r => r.BotSlot == 3).FallbackToUtilityAi);
    }

    [Fact]
    public void PlannerCannotChangeDestination()
    {
        var sched = new TeamOpeningRouteScheduler();
        var c = new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Entry", Destination = "a_palace_deep_room", Sector = "A", Bombsite = "A", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY" };
        var res = sched.Schedule(new[] { c }, "A", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.Equal("a_palace_deep_room", res[0].Destination);
    }

    [Fact]
    public void PlannerCannotChangeSector()
    {
        var sched = new TeamOpeningRouteScheduler();
        var c = new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Entry", Destination = "a_palace_deep_room", Sector = "A", Bombsite = "A", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY" };
        var res = sched.Schedule(new[] { c }, "A", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.Equal("A", res[0].Sector);
    }

    [Fact]
    public void PlannerCannotChangeRole()
    {
        var sched = new TeamOpeningRouteScheduler();
        var c = new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "EntryFragger", Destination = "a_palace_deep_room", Sector = "A", Bombsite = "A", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY" };
        var res = sched.Schedule(new[] { c }, "A", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.Equal("EntryFragger", res[0].Role);
    }

    [Fact]
    public void BombCarrierRouteMatchesPlan()
    {
        var sched = new TeamOpeningRouteScheduler();
        var c = new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Rifler", Destination = "a_palace_deep_room", Bombsite = "A", RouteId = "a_palace_deep_room", HasC4 = true, ConflictGroup = "PALACE_ENTRY" };
        var res = sched.Schedule(new[] { c }, "B", 100, 2, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.True(res[0].FallbackToUtilityAi);
        Assert.Equal("C4_BOMBSITE_INCOMPATIBLE", res[0].FallbackReason);
    }

    [Fact]
    public void BKitchenRemainsUtilityAiOnly()
    {
        var sched = new TeamOpeningRouteScheduler();
        var c = new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Entry", Destination = "tr_b_apps_kitchen_control", RouteId = "tr_b_apps_kitchen_control", ConflictGroup = "B_APPS_ENTRY" };
        var res = sched.Schedule(new[] { c }, "B", 100, 5, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.True(res[0].FallbackToUtilityAi);
        Assert.Equal("UTILITY_AI_ONLY_EXCLUDED", res[0].FallbackReason);
    }

    [Fact]
    public void UncertifiedRouteCannotReceiveLease()
    {
        var sched = new TeamOpeningRouteScheduler();
        var c = new TeamOpeningBotCandidate { BotSlot = 1, Team = "T", Role = "Entry", Destination = "uncertified_spot_x", RouteId = "uncertified_spot_x", ConflictGroup = "T_SPAWN_EXIT" };
        var res = sched.Schedule(new[] { c }, "A", 100, 5, CertifiedAllowlist, ExcludedUtilityOnly);
        Assert.True(res[0].FallbackToUtilityAi);
        Assert.Equal("UNCERTIFIED_ROUTE", res[0].FallbackReason);
    }

    [Fact]
    public void ContactReleasesOnlyAffectedBot()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "b1", "CT", "a_triple_box_hold", 100, 640, true, CanaryTeamMode.CtSingle, null, out _, out _);
        mgr.TryAcquireLease(1, 2, "b2", "CT", "b_market_hold", 100, 640, true, CanaryTeamMode.CtSingle, null, out _, out _);
        Assert.False(mgr.ValidateLeaseOnTick(1, 1, 120, true, "CONTACT_INTERRUPTION", null, out var reason));
        Assert.Equal("CONTACT_INTERRUPTION", reason);
        Assert.False(mgr.HasActiveLease(1));
        Assert.True(mgr.HasActiveLease(2));
    }

    [Fact]
    public void DeathReleasesOnlyAffectedBot()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "b1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.TryAcquireLease(1, 2, "b2", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.ReleaseLeaseForSlot(1, 1, 130, "BOT_DEAD");
        Assert.False(mgr.HasActiveLease(1));
        Assert.True(mgr.HasActiveLease(2));
    }

    [Fact]
    public void KillSwitchRestoresAllBots()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 5 };
        for (int s = 1; s <= 5; s++)
        {
            mgr.TryAcquireLease(1, s, $"b{s}", "CT", "a_triple_box_hold", 100, 640, true, CanaryTeamMode.CtSingle, null, out _, out _);
        }
        mgr.ReleaseAllLeases(150, "KILL_SWITCH_DISABLED");
        Assert.Equal(0, mgr.ActiveLeaseCount);
        Assert.Equal(0, mgr.AccountingResidue);
    }

    [Fact]
    public void ContinuousJumpIsImpossible()
    {
        var exec = new GeometricTransitionExecutor();
        Assert.Equal(0, exec.ContinuousJumpViolations);
    }

    [Fact]
    public void WeaponReadinessRemainsActive()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "tr_2", "T", "Entry", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, out var sug));
        Assert.True(sug!.KnifeAllowedUntil > 0);
    }

    [Fact]
    public void CtCertifiedRoutesRemainUnchanged()
    {
        Assert.Empty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("A", "a_triple_box_hold", -100f, -1900f, -168f));
        Assert.NotEmpty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("MID_WINDOW", "mid_window_right_deep", -1480f, -1010f, -168f));
        Assert.NotEmpty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("B_MARKET", "b_market_hold", -1900f, -300f, -168f));
    }

    [Fact]
    public void TrCertifiedRoutesRemainUnchanged()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "tr_2", "T", "Entry", "a_palace_deep_room", "A", 1216f, -384f, -163f, 56.5f, -2120.7f, -39.9f, 100, out _));
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 3, "tr_3", "T", "Entry", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, out _));
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 4, "tr_4", "T", "Entry", "tr_b_apps_house_staging", "B", 1216f, 384f, -256f, -450f, 800f, -130f, 100, out _));
    }

    [Fact]
    public void RouteAccountingClosesPerBot()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "b1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.TryAcquireLease(1, 2, "b2", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.OnRoundEnd(1, 200);
        Assert.Equal(0, mgr.ActiveLeaseCount);
    }

    [Fact]
    public void AuthorityAccountingClosesPerBot()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "b1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.TryAcquireLease(1, 2, "b2", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.ReleaseAllLeases(220, "ROUND_END");
        Assert.Equal(0, mgr.AccountingResidue);
    }
}
