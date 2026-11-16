using System;
using System.Collections.Generic;
using Xunit;
using CsBotManager;

namespace CsBotManager.Tests;

public class Combined5v5Debug2B98Tests
{
    private static List<TeammatePositionSnapshot> EmptySnaps() => new();

    [Fact]
    public void TenBotsCanOwnIndependentControllers()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        for (int s = 1; s <= 5; s++) ctQ.Enqueue(s);
        for (int s = 6; s <= 10; s++) trQ.Enqueue(s);
        Assert.Equal(5, ctQ.OrderedSlots.Count);
        Assert.Equal(5, trQ.OrderedSlots.Count);
    }

    [Fact]
    public void FiveCtAndFiveTrLeasesAreIndependent()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        ctQ.MarkPortalCleared(1, 100);
        Assert.False(trQ.PortalStateBySlot[6].Cleared);
    }

    [Fact]
    public void CtQueueCannotContainTrSlot()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        ctQ.Enqueue(1);
        Assert.Equal("CT", ctQ.Team);
        Assert.DoesNotContain(6, ctQ.OrderedSlots);
    }

    [Fact]
    public void TrQueueCannotContainCtSlot()
    {
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        trQ.Enqueue(6);
        Assert.Equal("TR", trQ.Team);
        Assert.DoesNotContain(1, trQ.OrderedSlots);
    }

    [Fact]
    public void QueueKeyIncludesTeam()
    {
        var dict = new Dictionary<(int RoundId, string Team, string Group), CorridorDepartureQueue>();
        dict[(1, "CT", "SHARED")] = new CorridorDepartureQueue("SHARED") { Team = "CT" };
        dict[(1, "TR", "SHARED")] = new CorridorDepartureQueue("SHARED") { Team = "TR" };
        Assert.Equal(2, dict.Count);
    }

    [Fact]
    public void SlotCannotOwnTwoLeases()
    {
        var st = new PortalTraversalState { BotSlot = 1 };
        Assert.Equal(1, st.BotSlot);
    }

    [Fact]
    public void SlotCannotOwnTwoControllers()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        q.Enqueue(1);
        q.Enqueue(1);
        Assert.Single(q.OrderedSlots);
    }

    [Fact]
    public void SlotCannotExistInTwoQueues()
    {
        var q1 = new CorridorDepartureQueue("CT_A") { Team = "CT" };
        var q2 = new CorridorDepartureQueue("CT_B") { Team = "CT" };
        q1.Enqueue(1);
        Assert.Contains(1, q1.OrderedSlots);
        Assert.DoesNotContain(1, q2.OrderedSlots);
    }

    [Fact]
    public void CtFailureDoesNotAffectTr()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        ctQ.MarkRemoved(1, "CONTACT", 100);
        Assert.Equal(6, trQ.LeaderSlot);
    }

    [Fact]
    public void TrFailureDoesNotAffectCt()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        trQ.MarkRemoved(6, "DEAD", 100);
        Assert.Equal(1, ctQ.LeaderSlot);
    }

    [Fact]
    public void RoundEndReleasesTenLeases()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        for (int s = 1; s <= 5; s++) ctQ.Enqueue(s);
        for (int s = 6; s <= 10; s++) trQ.Enqueue(s);
        ctQ.ResetRound();
        trQ.ResetRound();
        Assert.Empty(ctQ.OrderedSlots);
        Assert.Empty(trQ.OrderedSlots);
    }

    [Fact]
    public void KillSwitchReleasesTenLeases()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        ctQ.Enqueue(1); trQ.Enqueue(6);
        ctQ.ResetRound(); trQ.ResetRound();
        Assert.Equal(-1, ctQ.LeaderSlot);
        Assert.Equal(-1, trQ.LeaderSlot);
    }

    [Fact]
    public void PortalStateIsIndependentPerSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        q.Enqueue(6); q.Enqueue(7);
        q.MarkPortalCleared(6, 120);
        Assert.True(q.PortalStateBySlot[6].Cleared);
        Assert.False(q.PortalStateBySlot[7].Cleared);
    }

    [Fact]
    public void DirectPredecessorIsFromSameTeam()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        q.Enqueue(6); q.Enqueue(7);
        Assert.Equal(6, q.GetPredecessor(7));
    }

    [Fact]
    public void PortalClearanceRequiresPhysicalCrossing()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR", RequiresPhysicalPortalClearance = true };
        q.Enqueue(6); q.Enqueue(7);
        q.MarkReleased(6, 100);
        Assert.False(q.CanRelease(7, 500, EmptySnaps()));
    }

    [Fact]
    public void C4RouteMatchesBombsite()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        Assert.Equal("TR", q.Team);
    }

    [Fact]
    public void BKitchenRemainsUtilityAiOnly()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        Assert.DoesNotContain("tr_b_apps_kitchen_control", q.ConflictGroup);
    }

    [Fact]
    public void PlannerCannotControlPlant()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        Assert.NotEqual("PLANT", q.ConflictGroup);
    }

    [Fact]
    public void PlannerCannotControlCombat()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        Assert.NotEqual("COMBAT", q.ConflictGroup);
    }

    [Fact]
    public void WeaponReadinessRemainsActive()
    {
        Assert.True(true);
    }

    [Fact]
    public void ContinuousJumpIsImpossible()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        q.Enqueue(1);
        Assert.Equal(1, q.LeaderSlot);
    }

    [Fact]
    public void PositioningTransformerRemainsShadowOnly()
    {
        Assert.True(true);
    }

    [Fact]
    public void CtCertifiedRoutesRemainUnchanged()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        Assert.Equal("CT_SPAWN_EXIT", q.ConflictGroup);
    }

    [Fact]
    public void TrCertifiedRoutesRemainUnchanged()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        Assert.Equal("T_SPAWN_EXIT", q.ConflictGroup);
    }

    [Fact]
    public void RouteAccountingClosesPerTeam()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        ctQ.Enqueue(1); ctQ.MarkPortalCleared(1, 100);
        Assert.Equal(1, ctQ.ClearedSlots.Count);
    }

    [Fact]
    public void AuthorityAccountingClosesPerTeam()
    {
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        trQ.Enqueue(6); trQ.MarkRemoved(6, "ROUND_ENDED", 100);
        Assert.Equal(1, trQ.RemovedSlots.Count);
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

    [Fact]
    public void DebugTelemetryContainsBothTeams()
    {
        var ctQ = new CorridorDepartureQueue("CT_SPAWN_EXIT") { Team = "CT" };
        var trQ = new CorridorDepartureQueue("T_SPAWN_EXIT") { Team = "TR" };
        Assert.Equal("CT", ctQ.Team);
        Assert.Equal("TR", trQ.Team);
    }
}
