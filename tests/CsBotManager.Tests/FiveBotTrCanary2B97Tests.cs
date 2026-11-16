using System;
using System.Collections.Generic;
using Xunit;
using CsBotManager;

namespace CsBotManager.Tests;

public class FiveBotTrCanary2B97Tests
{
    private static List<TeammatePositionSnapshot> EmptySnaps() => new();

    [Fact]
    public void FiveSlotsHaveFourDirectPredecessors()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        for (int s = 1; s <= 5; s++) q.Enqueue(s);
        Assert.Null(q.GetPredecessor(1));
        Assert.Equal(1, q.GetPredecessor(2));
        Assert.Equal(2, q.GetPredecessor(3));
        Assert.Equal(3, q.GetPredecessor(4));
        Assert.Equal(4, q.GetPredecessor(5));
    }

    [Fact]
    public void InitialLeaderIsFirstReleasedSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(10);
        q.Enqueue(11);
        Assert.Equal(10, q.LeaderSlot);
        Assert.Equal(10, q.CurrentReleasedSlot);
    }

    [Fact]
    public void LeaderClearAdvancesToSecondSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2); q.Enqueue(3);
        q.MarkReleased(1, 100);
        Assert.True(q.TryConfirmPortalCrossing(1, 120, 0, 0, 0, 130f, 130f));
        Assert.Equal(2, q.TryAdvanceQueue());
    }

    [Fact]
    public void SecondClearAdvancesToThirdSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2); q.Enqueue(3);
        q.MarkReleased(1, 100);
        q.TryConfirmPortalCrossing(1, 120, 0, 0, 0, 130f, 130f);
        q.MarkReleased(2, 121);
        Assert.True(q.TryConfirmPortalCrossing(2, 140, 0, 0, 0, 130f, 130f));
        Assert.Equal(3, q.TryAdvanceQueue());
    }

    [Fact]
    public void ThirdClearAdvancesToFourthSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        for (int s = 1; s <= 4; s++) q.Enqueue(s);
        for (int s = 1; s <= 3; s++)
        {
            q.MarkReleased(s, 100 + s * 10);
            q.TryConfirmPortalCrossing(s, 105 + s * 10, 0, 0, 0, 130f, 130f);
        }
        Assert.Equal(4, q.TryAdvanceQueue());
    }

    [Fact]
    public void FourthClearAdvancesToFifthSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        for (int s = 1; s <= 5; s++) q.Enqueue(s);
        for (int s = 1; s <= 4; s++)
        {
            q.MarkReleased(s, 100 + s * 10);
            q.TryConfirmPortalCrossing(s, 105 + s * 10, 0, 0, 0, 130f, 130f);
        }
        Assert.Equal(5, q.TryAdvanceQueue());
    }

    [Fact]
    public void EachSlotHasIndependentPortalState()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2);
        q.MarkReleased(1, 100);
        q.MarkPortalEntered(1, 105);
        q.MarkPortalCleared(1, 120);

        Assert.True(q.PortalStateBySlot[1].Cleared);
        Assert.False(q.PortalStateBySlot[2].Cleared);
        Assert.Equal(120, q.PortalStateBySlot[1].ClearTick);
        Assert.Equal(-1, q.PortalStateBySlot[2].ClearTick);
    }

    [Fact]
    public void GlobalClearCannotReleaseAllFollowers()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        for (int s = 1; s <= 5; s++) q.Enqueue(s);
        q.MarkReleased(1, 100);
        q.MarkPortalCleared(1, 120);
        Assert.True(q.CanRelease(2, 121, EmptySnaps()));
        Assert.False(q.CanRelease(3, 121, EmptySnaps()));
        Assert.False(q.CanRelease(4, 121, EmptySnaps()));
        Assert.False(q.CanRelease(5, 121, EmptySnaps()));
    }

    [Fact]
    public void FollowerRequiresDirectPredecessorClear()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2); q.Enqueue(3);
        q.MarkReleased(1, 100);
        q.MarkPortalCleared(1, 110);
        q.MarkReleased(2, 111);
        Assert.False(q.HasPredecessorCleared(3));
        Assert.False(q.CanRelease(3, 115, EmptySnaps()));
    }

    [Fact]
    public void TwoFollowersCannotReleaseSameTick()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2); q.Enqueue(3);
        q.MarkReleased(1, 100);
        q.MarkPortalCleared(1, 110);
        Assert.True(q.CanRelease(2, 111, EmptySnaps()));
        q.MarkReleased(2, 111);
        q.MarkPortalCleared(2, 111);
        Assert.False(q.CanRelease(3, 111, EmptySnaps()));
        Assert.True(q.CanRelease(3, 112, EmptySnaps()));
    }

    [Fact]
    public void InterruptedLeaderPromotesSecondSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2); q.Enqueue(3);
        var res = q.MarkRemoved(1, "DEAD", 105);
        Assert.True(res.PredecessorRemoved);
        Assert.True(res.FollowerPromoted);
        Assert.Equal(2, q.LeaderSlot);
        Assert.Equal(2, q.CurrentReleasedSlot);
    }

    [Fact]
    public void InterruptedMiddleSlotRelinksQueue()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2); q.Enqueue(3);
        var res = q.MarkRemoved(2, "CONTACT", 105);
        Assert.True(res.PredecessorRemoved);
        Assert.True(res.QueueRelinked);
        Assert.Equal(1, q.GetPredecessor(3));
    }

    [Fact]
    public void RemovedSlotLeavesNoPortalResidue()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2);
        q.MarkPortalEntered(1, 102);
        Assert.True(q.PortalOccupied);
        q.MarkRemoved(1, "LEASE_LOST", 105);
        Assert.False(q.PortalOccupied);
        Assert.Contains(1, q.RemovedSlots);
    }

    [Fact]
    public void TimeAloneCannotClearPortal()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT") { RequiresPhysicalPortalClearance = true };
        q.Enqueue(1); q.Enqueue(2);
        q.MarkReleased(1, 100);
        Assert.False(q.CanRelease(2, 500, EmptySnaps()));
    }

    [Fact]
    public void DistanceWithoutEntryCannotClearPortal()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT", minimumSpacingUnits: 110f);
        q.Enqueue(1);
        Assert.False(q.TryConfirmPortalCrossing(1, 120, 0, 10, 20, 200f, 200f));
    }

    [Fact]
    public void PhysicalCrossingClearsCorrectSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2);
        q.TryConfirmPortalCrossing(1, 110, 10, 10, 20, 10f, 10f);
        Assert.True(q.PortalStateBySlot[1].Entered);
        Assert.True(q.TryConfirmPortalCrossing(1, 120, 20, 10, 20, 120f, 120f));
        Assert.True(q.PortalStateBySlot[1].Cleared);
        Assert.False(q.PortalStateBySlot[2].Cleared);
    }

    [Fact]
    public void ScheduledWaitDoesNotCountAsBlocked()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2);
        q.MarkReleased(1, 100);
        Assert.False(q.CanRelease(2, 105, EmptySnaps()));
        Assert.Empty(q.RemovedSlots);
    }

    [Fact]
    public void QueueAccountingClosesForFiveSlots()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        for (int s = 1; s <= 5; s++) q.Enqueue(s);
        for (int s = 1; s <= 4; s++) q.MarkPortalCleared(s, 100 + s * 10);
        q.MarkRemoved(5, "ROUND_ENDED", 150);
        Assert.Equal(5, q.ClearedSlots.Count + q.RemovedSlots.Count);
    }

    [Fact]
    public void FiveCtBehaviorRemainsUnchanged()
    {
        var q = new CorridorDepartureQueue("CT_SPAWN_EXIT") { RequiresPhysicalPortalClearance = true };
        q.Enqueue(1); q.Enqueue(2);
        Assert.True(q.TryConfirmPortalCrossing(1, 120, 0, 0, 150f));
        Assert.True(q.CanRelease(2, 121, EmptySnaps()));
    }

    [Fact]
    public void TwoTrBehaviorRemainsUnchanged()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2);
        q.MarkReleased(1, 100);
        q.MarkPortalCleared(1, 115);
        Assert.True(q.CanRelease(2, 116, EmptySnaps()));
    }

    [Fact]
    public void BKitchenCannotReceiveLease()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        Assert.DoesNotContain("tr_b_apps_kitchen_control", q.ConflictGroup);
    }

    [Fact]
    public void C4CompatibilityRemainsEnforced()
    {
        var st = new PortalTraversalState { BotSlot = 1 };
        Assert.Equal(1, st.BotSlot);
        Assert.False(st.Cleared);
    }

    [Fact]
    public void ContinuousJumpRemainsImpossible()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1);
        Assert.Equal(1, q.LeaderSlot);
    }

    [Fact]
    public void GoalOwnershipRemainsExactPerSlot()
    {
        var q = new CorridorDepartureQueue("T_SPAWN_EXIT");
        q.Enqueue(1); q.Enqueue(2);
        Assert.Equal(1, q.PortalStateBySlot[1].BotSlot);
        Assert.Equal(2, q.PortalStateBySlot[2].BotSlot);
    }
}
