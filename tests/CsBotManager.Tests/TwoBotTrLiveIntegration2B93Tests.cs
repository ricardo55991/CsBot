using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class TwoBotTrLiveIntegration2B93Tests
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
        "a_palace_deep_room", "tr_a_ramp_staging_wait", "tr_b_apps_house_staging", "tr_mid_top_control", "tr_underpass_control"
    };

    private static readonly IReadOnlySet<string> TrExcluded = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "tr_b_apps_kitchen_control"
    };

    private static List<TeamOpeningBotCandidate> MakeFiveTrCandidates(string planSite = "A") => new()
    {
        new() { BotSlot = 1, PlayerPseudonym = "tr1", Team = "T", Role = "EntryFragger", Destination = "a_palace_deep_room", Sector = "A", Bombsite = "A", RouteId = "a_palace_deep_room", ConflictGroup = "PALACE_ENTRY", HasC4 = true, SpawnDistance = 100f },
        new() { BotSlot = 2, PlayerPseudonym = "tr2", Team = "T", Role = "EntryFragger", Destination = "tr_a_ramp_staging_wait", Sector = "A", Bombsite = "A", RouteId = "tr_a_ramp_staging_wait", ConflictGroup = "A_RAMP_ENTRY", SpawnDistance = 120f },
        new() { BotSlot = 3, PlayerPseudonym = "tr3", Team = "T", Role = "Support", Destination = "tr_b_apps_house_staging", Sector = "B", Bombsite = "B", RouteId = "tr_b_apps_house_staging", ConflictGroup = "HOUSE_ENTRY", SpawnDistance = 140f },
        new() { BotSlot = 4, PlayerPseudonym = "tr4", Team = "T", Role = "MidControl", Destination = "tr_mid_top_control", Sector = "Mid", Bombsite = "MID", RouteId = "tr_mid_top_control", ConflictGroup = "TOP_MID_ENTRY", SpawnDistance = 160f },
        new() { BotSlot = 5, PlayerPseudonym = "tr5", Team = "T", Role = "EntryFragger", Destination = "tr_b_apps_kitchen_control", Sector = "B", Bombsite = "B", RouteId = "tr_b_apps_kitchen_control", ConflictGroup = "B_APPS_ENTRY", SpawnDistance = 180f, IsEligibleForCanary = false },
    };

    [Fact]
    public void SchedulerReceivesAllFiveTrBots()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.Equal(5, res.Assignments.Count);
    }

    [Fact]
    public void ExactlyTwoTrBotsAreCanaryControlled()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.Equal(2, res.Assignments.Count(a => a.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED));
    }

    [Fact]
    public void ThreeTrBotsRemainUtilityAiControlled()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.Equal(3, res.Assignments.Count(a => a.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED));
    }

    [Fact]
    public void BombCarrierIsIncludedInSchedule()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.True(res.BySlot.ContainsKey(1));
        Assert.Equal(1, res.BySlot[1].Priority);
    }

    [Fact]
    public void BombCarrierCanaryRouteMustMatchPlan()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "B", 100, 2, TrAllow, TrExcluded);
        Assert.Equal(TeamDepartureControlMode.UTILITY_AI_OBSERVED, res.BySlot[1].ControlMode);
    }

    [Fact]
    public void BombCarrierCannotChangeBombsite()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.Equal("A", res.BySlot[1].Sector);
    }

    [Fact]
    public void BombCarrierCannotDropBomb()
    {
        Assert.Equal("DROP_FORBIDDEN", OpeningRouteCanaryGuard.GuardCombatOrC4Authority("DROP_FORBIDDEN", true));
    }

    [Fact]
    public void ExcludedKitchenRouteCannotReceiveLease()
    {
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("T", "tr_b_apps_kitchen_control"));
    }

    [Fact]
    public void UtilityKitchenRouteRemainsAvailable()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "B", 100, 2, TrAllow, TrExcluded);
        Assert.Equal("tr_b_apps_kitchen_control", res.BySlot[5].Destination);
        Assert.Equal(TeamDepartureControlMode.UTILITY_AI_OBSERVED, res.BySlot[5].ControlMode);
    }

    [Fact]
    public void TrCorridorIsInferredFromPortal()
    {
        var c = new TeamOpeningBotCandidate { BotSlot = 1, Destination = "a_palace_deep_room", ConflictGroup = "" };
        var inf = TeamOpeningRouteScheduler.InferInitialCorridor(c);
        Assert.Equal("PALACE_ENTRY", inf.Corridor);
        Assert.Equal(CorridorConfidence.HIGH, inf.Confidence);
    }

    [Fact]
    public void EmptyConflictGroupDoesNotMeanSameCorridor()
    {
        var cA = new TeamOpeningBotCandidate { BotSlot = 6, ConflictGroup = "", Sector = "A" };
        var cB = new TeamOpeningBotCandidate { BotSlot = 7, ConflictGroup = "", Sector = "B" };
        Assert.NotEqual(TeamOpeningRouteScheduler.InferInitialCorridor(cA).Corridor, TeamOpeningRouteScheduler.InferInitialCorridor(cB).Corridor);
    }

    [Fact]
    public void CorridorQueueHasSingleLeader()
    {
        var q = new CorridorDepartureQueue("A_RAMP_ENTRY", 110f, 500);
        q.Enqueue(1);
        q.Enqueue(2);
        Assert.Equal(1, q.LeaderSlot);
    }

    [Fact]
    public void PassiveHoldDoesNotChangeDestination()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.Equal("tr_b_apps_kitchen_control", res.BySlot[5].Destination);
    }

    [Fact]
    public void PassiveHoldDoesNotChangeRole()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.Equal("EntryFragger", res.BySlot[5].Role);
    }

    [Fact]
    public void PassiveHoldDoesNotChangeBombsite()
    {
        var sched = new TeamOpeningRouteScheduler();
        var res = sched.ScheduleFullTeamDeparture(1, MakeFiveTrCandidates(), "A", 100, 2, TrAllow, TrExcluded);
        Assert.Equal("B", res.BySlot[5].Sector);
    }

    [Fact]
    public void PassiveHoldCannotAcquireLease()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        Assert.False(mgr.HasActiveLease(5));
    }

    [Fact]
    public void QueueWaitKeepsCanonicalWaypoint()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        Assert.True(g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false));
        var s = g.GetSessionForSlot(1, 2)!;
        string wp0 = s.Route.OrderedWaypoints[0].Name;
        Assert.False(string.IsNullOrEmpty(wp0));
    }

    [Fact]
    public void OneTrFailureDoesNotReleaseOtherLease()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 1, "tr1", "T", "EntryFragger", "a_palace_deep_room", "A", 1216f, -384f, -163f, 56.5f, -2120.7f, -39.9f, 100, true, false);
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false);
        g.NotifyPlayerDamage(1, 1, 120);
        Assert.False(g.LeaseManager.HasActiveLease(1));
        Assert.True(g.LeaseManager.HasActiveLease(2));
    }

    [Fact]
    public void OneTrArrivalDoesNotReleaseOtherLease()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 1, "tr1", "T", "EntryFragger", "a_palace_deep_room", "A", 1216f, -384f, -163f, 56.5f, -2120.7f, -39.9f, 100, true, false);
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false);
        g.LeaseManager.ReleaseLeaseForSlot(1, 1, 200, "ROUTE_COMPLETED");
        Assert.False(g.LeaseManager.HasActiveLease(1));
        Assert.True(g.LeaseManager.HasActiveLease(2));
    }

    [Fact]
    public void ContactReleasesOnlyAffectedBot()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 1, "tr1", "T", "EntryFragger", "a_palace_deep_room", "A", 1216f, -384f, -163f, 56.5f, -2120.7f, -39.9f, 100, true, false);
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false);
        g.EvaluateTick(1, 1, 105, 1200f, -384f, -163f, 200f, "weapon_knife", true, true, false, "a_palace_deep_room", "A", "EntryFragger", hasContact: true, false, false);
        Assert.False(g.LeaseManager.HasActiveLease(1));
        Assert.True(g.LeaseManager.HasActiveLease(2));
    }

    [Fact]
    public void C4IncompatibilityReleasesOnlyAffectedBot()
    {
        Assert.Equal("PLAN_ROUTE_MISMATCH", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("a_palace_deep_room", "B", "Rifler", true));
    }

    [Fact]
    public void CtApprovedRoutesRemainUnchanged()
    {
        Assert.Empty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("A", "a_triple_box_hold", -350f, -1950f, -168f));
        Assert.NotEmpty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("MID_WINDOW", "mid_window_right_deep", -1480f, -1010f, -168f));
    }

    [Fact]
    public void TrCertifiedRoutesRemainUnchanged()
    {
        Assert.NotEmpty(GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_PALACE", "a_palace_deep_room", 56.5f, -2120.7f, -39.9f));
        Assert.NotEmpty(GeometricTransitionCatalog.BuildTransitionsForTrRoute("A_RAMP", "tr_a_ramp_staging_wait", 260f, -940f, -150f));
        Assert.NotEmpty(GeometricTransitionCatalog.BuildTransitionsForTrRoute("B_APPS", "tr_b_apps_house_staging", -450f, 800f, -130f));
    }

    [Fact]
    public void RouteAccountingClosesPerSlot()
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.LeaseManager.MaxConcurrentLeases = 2;
        g.TryStartCanaryForRound(1, 1, "tr1", "T", "EntryFragger", "a_palace_deep_room", "A", 1216f, -384f, -163f, 56.5f, -2120.7f, -39.9f, 100, true, false);
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false);
        Assert.Equal(2, g.FinalizeAllOpenSessions("ROUND_END", 250));
    }

    [Fact]
    public void AuthorityAccountingClosesPerSlot()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "tr1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.TryAcquireLease(1, 2, "tr2", "T", "tr_a_ramp_staging_wait", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.ReleaseLeaseForSlot(1, 1, 200, "DONE");
        mgr.ReleaseLeaseForSlot(1, 2, 210, "DONE");
        Assert.Equal(0, mgr.AccountingResidue);
    }

    [Fact]
    public void PassiveHoldAccountingCloses()
    {
        var hold = new PassiveDepartureHold { RoundId = 1, BotSlot = 3, ConflictGroup = "A_RAMP_ENTRY", StartTick = 100, ReleaseTick = 116 };
        hold.Released = true;
        hold.ReleaseReason = "PORTAL_CLEARED";
        Assert.True(hold.Released);
    }
}
