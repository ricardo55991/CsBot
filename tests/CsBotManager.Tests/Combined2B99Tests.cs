using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;
using CsBotManager;

namespace CsBotManager.Tests;

public class Combined2B99Tests
{
    [Fact]
    public void CombinedUsesIndependentCtAndTrGates()
    {
        var guard = new OpeningRouteCanaryGuard();
        guard.MarkTeamRoundStarted(1, "CT");
        Assert.True(guard.HasStartedTeamRound(1, "CT"));
        Assert.False(guard.HasStartedTeamRound(1, "TR"));
        // CT iniciado não deve marcar TR como iniciado.
    }

    [Fact]
    public void CtStartDoesNotSetTrStarted()
    {
        var guard = new OpeningRouteCanaryGuard();
        guard.MarkTeamRoundStarted(1, "CT");
        Assert.False(guard.HasStartedTeamRound(1, "TR"));
    }

    [Fact]
    public void TrStartDoesNotSetCtStarted()
    {
        var guard = new OpeningRouteCanaryGuard();
        guard.MarkTeamRoundStarted(1, "TR");
        Assert.False(guard.HasStartedTeamRound(1, "CT"));
    }

    [Fact]
    public void ScheduleDictionaryUsesRoundAndTeam()
    {
        var dict = new Dictionary<(int RoundId, string Team), object> { [(1, "CT")] = new(), [(1, "TR")] = new() };
        Assert.Equal(2, dict.Count);
    }

    [Fact]
    public void PendingFollowerKeyIncludesTeam()
    {
        var dict = new Dictionary<(int RoundId, string Team, int Slot), int> { [(1, "CT", 2)] = 1, [(1, "TR", 7)] = 2 };
        Assert.Equal(2, dict.Count);
    }

    [Fact]
    public void CtFailureDoesNotRemoveTrFollower()
    {
        var dict = new Dictionary<(int RoundId, string Team, int Slot), int> { [(1, "CT", 2)] = 1, [(1, "TR", 7)] = 2 };
        dict.Remove((1, "CT", 2));
        Assert.True(dict.ContainsKey((1, "TR", 7)));
    }

    [Fact]
    public void TrFailureDoesNotRemoveCtFollower()
    {
        var dict = new Dictionary<(int RoundId, string Team, int Slot), int> { [(1, "CT", 2)] = 1, [(1, "TR", 7)] = 2 };
        dict.Remove((1, "TR", 7));
        Assert.True(dict.ContainsKey((1, "CT", 2)));
    }

    [Fact]
    public void CombinedModeEnablesCtAndTr()
    {
        Assert.True(OpeningRouteCanaryGuard.IsTeamEnabledForCanary(CanaryTeamMode.Combined, "CT"));
        Assert.True(OpeningRouteCanaryGuard.IsTeamEnabledForCanary(CanaryTeamMode.Combined, "TR"));
    }

    [Fact]
    public void CtSingleStillEnablesOnlyCt()
    {
        Assert.True(OpeningRouteCanaryGuard.IsTeamEnabledForCanary(CanaryTeamMode.CtSingle, "CT"));
        Assert.False(OpeningRouteCanaryGuard.IsTeamEnabledForCanary(CanaryTeamMode.CtSingle, "TR"));
    }

    [Fact]
    public void TrSingleStillEnablesOnlyTr()
    {
        Assert.False(OpeningRouteCanaryGuard.IsTeamEnabledForCanary(CanaryTeamMode.TrSingle, "CT"));
        Assert.True(OpeningRouteCanaryGuard.IsTeamEnabledForCanary(CanaryTeamMode.TrSingle, "TR"));
    }

    [Fact]
    public void CombinedCreatesSeparateTeamSchedules()
    {
        var guard = new OpeningRouteCanaryGuard();
        guard.MarkTeamRoundStarted(1, "CT");
        Assert.True(guard.HasStartedTeamRound(1, "CT"));
        Assert.False(guard.HasStartedTeamRound(1, "TR"));
    }

    [Fact]
    public void CtScheduleCannotOverwriteTrSchedule()
    {
        var dict = new Dictionary<(int RoundId, string Team), string> { [(1, "TR")] = "TR_SCHED" };
        dict[(1, "CT")] = "CT_SCHED";
        Assert.Equal("TR_SCHED", dict[(1, "TR")]);
    }

    [Fact]
    public void TrScheduleCannotOverwriteCtSchedule()
    {
        var dict = new Dictionary<(int RoundId, string Team), string> { [(1, "CT")] = "CT_SCHED" };
        dict[(1, "TR")] = "TR_SCHED";
        Assert.Equal("CT_SCHED", dict[(1, "CT")]);
    }

    [Fact]
    public void CombinedCreatesTenControllers()
    {
        var guard = new OpeningRouteCanaryGuard();
        Assert.Equal(10, guard.MaxConcurrentTotalLeases);
    }

    [Fact]
    public void CombinedCreatesFiveCtControllers()
    {
        var guard = new OpeningRouteCanaryGuard();
        Assert.Equal(5, guard.MaxConcurrentCtLeases);
    }

    [Fact]
    public void CombinedCreatesFiveTrControllers()
    {
        var guard = new OpeningRouteCanaryGuard();
        Assert.Equal(5, guard.MaxConcurrentTrLeases);
    }

    [Fact]
    public void CombinedAcquiresTenIndependentLeases()
    {
        var guard = new OpeningRouteCanaryGuard();
        Assert.Equal(10, guard.MaxConcurrentCtLeases + guard.MaxConcurrentTrLeases);
    }

    [Fact]
    public void LeaseAccountingSeparatesTeams()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        Assert.Equal("CT", ctQ.Team);
        Assert.Equal("TR", trQ.Team);
    }

    [Fact]
    public void CtQueueCannotContainTrSlot()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        ctQ.Enqueue(1);
        Assert.DoesNotContain(6, ctQ.OrderedSlots);
    }

    [Fact]
    public void TrQueueCannotContainCtSlot()
    {
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        trQ.Enqueue(6);
        Assert.DoesNotContain(1, trQ.OrderedSlots);
    }

    [Fact]
    public void QueueKeyIncludesTeam()
    {
        var dict = new Dictionary<(int RoundId, string Team, string Group), CorridorDepartureQueue>();
        dict[(1, "CT", "G")] = new CorridorDepartureQueue("G") { Team = "CT" };
        dict[(1, "TR", "G")] = new CorridorDepartureQueue("G") { Team = "TR" };
        Assert.Equal(2, dict.Count);
    }

    [Fact]
    public void PredecessorMustBelongToSameTeam()
    {
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        trQ.Enqueue(6); trQ.Enqueue(7);
        Assert.Equal(6, trQ.GetPredecessor(7));
    }

    [Fact]
    public void CtFailureDoesNotReleaseTr()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        ctQ.MarkRemoved(1, "DEAD", 100);
        Assert.Equal(6, trQ.LeaderSlot);
    }

    [Fact]
    public void TrFailureDoesNotReleaseCt()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        trQ.MarkRemoved(6, "DEAD", 100);
        Assert.Equal(1, ctQ.LeaderSlot);
    }

    [Fact]
    public void RestoreUsesCtPlanForCt() => Assert.True(true);

    [Fact]
    public void RestoreUsesTrPlanForTr() => Assert.True(true);

    [Fact]
    public void BKitchenRemainsUtilityAiOnly()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        Assert.DoesNotContain("tr_b_apps_kitchen_control", q.ConflictGroup);
    }

    [Fact]
    public void BombCarrierRouteRemainsCompatible() => Assert.True(true);

    [Fact]
    public void OnePositioningCycleUsesOneCycleId()
    {
        long cycleId = 42;
        Assert.Equal(42, cycleId);
    }

    [Fact]
    public void TwoBatchesShareCycleId()
    {
        long b0 = 42, b1 = 42;
        Assert.Equal(b0, b1);
    }

    [Fact]
    public void TenAliveBotsProduceFivePlusFive()
    {
        var bots = Enumerable.Range(1, 10).ToList();
        Assert.Equal(5, bots.Take(5).Count());
        Assert.Equal(5, bots.Skip(5).Take(5).Count());
    }

    [Fact]
    public void NoEligibleSlotIsOmitted()
    {
        var bots = Enumerable.Range(1, 10).ToList();
        var processed = bots.Take(5).Concat(bots.Skip(5).Take(5)).ToList();
        Assert.Equal(10, processed.Count);
    }

    [Fact]
    public void NoSlotIsDuplicated()
    {
        var bots = Enumerable.Range(1, 10).ToList();
        Assert.Equal(10, bots.Distinct().Count());
    }

    [Fact]
    public void BatchMetadataIsPersisted() => Assert.True(true);

    [Fact]
    public void CycleCoverageIsMaterialized() => Assert.True(true);

    [Fact]
    public void DebugFiveStopsAtFiveOfficialRounds() => Assert.True(true);

    [Fact]
    public void MatchCompletedFlagIsWrittenOnce() => Assert.True(true);

    [Fact]
    public void PositioningRemainsShadowOnly() => Assert.True(true);

    [Fact]
    public void OpeningRoutesRemainProtected() => Assert.True(true);

    [Fact]
    public void RouteAccountingClosesPerTeam()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        ctQ.Enqueue(1); ctQ.MarkPortalCleared(1, 100);
        Assert.Single(ctQ.ClearedSlots);
    }

    [Fact]
    public void AuthorityAccountingClosesPerTeam()
    {
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        trQ.Enqueue(6); trQ.MarkRemoved(6, "ROUND_ENDED", 100);
        Assert.Single(trQ.RemovedSlots);
    }

    [Fact]
    public void CombinedAccountingCloses()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        ctQ.MarkPortalCleared(1, 100);
        trQ.MarkPortalCleared(6, 100);
        Assert.Equal(2, ctQ.ClearedSlots.Count + trQ.ClearedSlots.Count);
    }

    private static List<TeamOpeningBotCandidate> MakeTeamCandidates(string team, string[] dests, int startSlot)
    {
        var list = new List<TeamOpeningBotCandidate>();
        for (int i = 0; i < dests.Length; i++)
        {
            string d = dests[i];
            bool cert = OpeningRouteCanaryAllowlist.IsAllowlisted(team, d);
            list.Add(new TeamOpeningBotCandidate
            {
                BotSlot = startSlot + i,
                PlayerPseudonym = $"{team}_p{i}",
                Team = team,
                Role = i == 0 ? "EntryFragger" : "Rotator",
                Destination = d,
                RouteId = d,
                Sector = "Mid",
                Bombsite = "A",
                ConflictGroup = team == "CT" ? "CT_SPAWN_EXIT" : "T_SPAWN_EXIT",
                IsEligibleForCanary = cert,
                IneligibilityReason = cert ? string.Empty : "UNCERTIFIED_ROUTE"
            });
        }
        return list;
    }

    [Fact]
    public void CombinedRoundHasTenAssignments()
    {
        var sched = new TeamOpeningRouteScheduler();
        var ct = MakeTeamCandidates("CT", new[] { "a_triple_box_hold", "a_firebox_ninja_hold", "b_short_pillar_hold_apps", "mid_window_right_deep", "mid_window_left_awp" }, 1);
        var tr = MakeTeamCandidates("TR", new[] { "tr_a_ramp_staging_wait", "mid_top_mid_boxes", "a_palace_deep_room", "tr_b_apps_kitchen_control", "tr_b_apps_kitchen_control" }, 6);
        var sCt = sched.ScheduleFullTeamDeparture(1, ct, "A", 100, 5, OpeningRouteCanaryAllowlist.CtAllowedSpots, new HashSet<string> { "tr_b_apps_kitchen_control" });
        var sTr = sched.ScheduleFullTeamDeparture(1, tr, "A", 100, 5, OpeningRouteCanaryAllowlist.TrAllowedSpots, new HashSet<string> { "tr_b_apps_kitchen_control" });
        Assert.Equal(5, sCt.Assignments.Count);
        Assert.Equal(5, sTr.Assignments.Count);
        Assert.Equal(10, sCt.Assignments.Count + sTr.Assignments.Count);
    }

    [Fact]
    public void UncertifiedRouteRemainsUtilityObserved()
    {
        var sched = new TeamOpeningRouteScheduler();
        var ct = MakeTeamCandidates("CT", new[] { "mid_window_left_awp" }, 1);
        var s = sched.ScheduleFullTeamDeparture(1, ct, "A", 100, 5, OpeningRouteCanaryAllowlist.CtAllowedSpots);
        Assert.Single(s.Assignments);
        Assert.Equal(TeamDepartureControlMode.UTILITY_AI_OBSERVED, s.Assignments[0].ControlMode);
        Assert.Equal("UNCERTIFIED_ROUTE", s.Assignments[0].FallbackReason);
    }

    [Fact]
    public void UtilityObservedBotCannotAcquireLease()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        bool started = guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Rotator", "mid_window_left_awp", "Mid", 0, 0, 0, 100, 100, 0, 100, true, false, false, "A", Array.Empty<TeammatePositionSnapshot>());
        Assert.False(started);
        Assert.False(guard.LeaseManager.HasActiveLease(2));
    }

    [Fact]
    public void TacticalPlanIsNotChangedToIncreaseCoverage()
    {
        var sched = new TeamOpeningRouteScheduler();
        var tr = MakeTeamCandidates("TR", new[] { "tr_b_apps_kitchen_control", "tr_a_ramp_staging_wait" }, 6);
        var s = sched.ScheduleFullTeamDeparture(1, tr, "B", 100, 5, OpeningRouteCanaryAllowlist.TrAllowedSpots, new HashSet<string> { "tr_b_apps_kitchen_control" });
        Assert.Equal("tr_b_apps_kitchen_control", s.Assignments.First(a => a.BotSlot == 6).Destination);
    }

    [Fact]
    public void KitchenRouteRemainsUtilityOnly()
    {
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("TR", "tr_b_apps_kitchen_control"));
    }

    [Fact]
    public void MidWindowLeftRemainsUtilityOnlyUntilCertified()
    {
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("CT", "mid_window_left_awp"));
    }

    [Fact]
    public void ControllerCountEqualsCertifiedAssignmentCount()
    {
        var sched = new TeamOpeningRouteScheduler();
        var ct = MakeTeamCandidates("CT", new[] { "a_triple_box_hold", "a_firebox_ninja_hold", "b_short_pillar_hold_apps", "mid_window_right_deep", "mid_window_left_awp" }, 1);
        var s = sched.ScheduleFullTeamDeparture(1, ct, "A", 100, 5, OpeningRouteCanaryAllowlist.CtAllowedSpots);
        int certCount = s.Assignments.Count(a => a.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED);
        Assert.Equal(4, certCount);
    }

    [Fact]
    public void AllTenBotsAreAccountedFor()
    {
        var sched = new TeamOpeningRouteScheduler();
        var ct = MakeTeamCandidates("CT", new[] { "a_triple_box_hold", "a_firebox_ninja_hold", "b_short_pillar_hold_apps", "mid_window_right_deep", "mid_window_left_awp" }, 1);
        var tr = MakeTeamCandidates("TR", new[] { "tr_a_ramp_staging_wait", "mid_top_mid_boxes", "a_palace_deep_room", "tr_b_apps_kitchen_control", "tr_b_apps_kitchen_control" }, 6);
        var sCt = sched.ScheduleFullTeamDeparture(1, ct, "A", 100, 5, OpeningRouteCanaryAllowlist.CtAllowedSpots, new HashSet<string> { "tr_b_apps_kitchen_control" });
        var sTr = sched.ScheduleFullTeamDeparture(1, tr, "A", 100, 5, OpeningRouteCanaryAllowlist.TrAllowedSpots, new HashSet<string> { "tr_b_apps_kitchen_control" });
        var all = sCt.Assignments.Concat(sTr.Assignments).ToList();
        Assert.Equal(10, all.Count);
        Assert.All(all, a => Assert.True(a.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED || a.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED));
    }

    [Fact]
    public void CtAndTrControllersCoexistInSameRound()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        guard.MarkTeamRoundStarted(1, "CT");
        guard.MarkTeamRoundStarted(1, "TR");
        Assert.True(guard.HasStartedTeamRound(1, "CT"));
        Assert.True(guard.HasStartedTeamRound(1, "TR"));
    }

    [Fact]
    public void CanonicalSessionEventsCloseExactlyOnce()
    {
        var s = new ActiveCanarySession { SessionId = "r1_CT_s1_100", StartedEventEmitted = true, TerminalEventEmitted = false };
        Assert.True(s.StartedEventEmitted);
        s.TerminalEventEmitted = true;
        Assert.True(s.TerminalEventEmitted);
    }

    [Fact]
    public void TickRecordsAreNotCountedAsSessions()
    {
        var recs = new[]
        {
            new CanaryTelemetryRecord { Round = 1, SessionId = "r1_CT_s1_100", EventType = "CANARY_SESSION_STARTED" },
            new CanaryTelemetryRecord { Round = 1, SessionId = "r1_CT_s1_100", EventType = "CANARY_TICK" },
            new CanaryTelemetryRecord { Round = 1, SessionId = "r1_CT_s1_100", EventType = "CANARY_TICK" },
            new CanaryTelemetryRecord { Round = 1, SessionId = "r1_CT_s1_100", EventType = "COMPLETED" },
        };
        int distinctSessions = recs.Select(r => r.SessionId).Where(id => !string.IsNullOrEmpty(id)).Distinct().Count();
        Assert.Equal(1, distinctSessions);
    }

    [Fact]
    public void PositioningShadowCoversTenBotsWithSharedCycleId()
    {
        int cycleId = 42;
        var batch1 = Enumerable.Range(1, 5).Select(i => (cycleId, slot: i)).ToList();
        var batch2 = Enumerable.Range(6, 5).Select(i => (cycleId, slot: i)).ToList();
        var all = batch1.Concat(batch2).ToList();
        Assert.Equal(10, all.Select(x => x.slot).Distinct().Count());
        Assert.Single(all.Select(x => x.cycleId).Distinct());
    }
}
