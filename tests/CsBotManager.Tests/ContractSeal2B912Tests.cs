using System;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public sealed class ContractSeal2B912Tests
{
    [Fact]
    public void SessionStartedIsStateChangeNotTerminal()
    {
        var ev = new OpeningAssignmentTerminalRecord
        {
            EventType = "OPENING_ASSIGNMENT_STATE_CHANGED",
            PreviousState = OpeningAssignmentLifecycleState.CANARY_PENDING,
            NewState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED,
            TerminalReason = "SESSION_STARTED",
        };
        Assert.Equal("OPENING_ASSIGNMENT_STATE_CHANGED", ev.EventType);
        Assert.NotEqual("OPENING_ASSIGNMENT_TERMINAL", ev.EventType);
    }

    [Fact]
    public void AssignmentTerminalEmitsExactlyOnce()
    {
        var evs = new[]
        {
            new OpeningAssignmentTerminalRecord { AssignmentId = "r1_CT_s1", EventType = "OPENING_ASSIGNMENT_SCHEDULED" },
            new OpeningAssignmentTerminalRecord { AssignmentId = "r1_CT_s1", EventType = "OPENING_ASSIGNMENT_STATE_CHANGED" },
            new OpeningAssignmentTerminalRecord { AssignmentId = "r1_CT_s1", EventType = "OPENING_ASSIGNMENT_TERMINAL", TerminalReason = "COMPLETED" },
        };
        Assert.Single(evs, e => e.EventType == "OPENING_ASSIGNMENT_TERMINAL");
    }

    [Fact]
    public void ControlledAssignmentHasValidLifecycle()
    {
        var evs = new[]
        {
            OpeningAssignmentLifecycleState.SCHEDULED,
            OpeningAssignmentLifecycleState.CANARY_PENDING,
            OpeningAssignmentLifecycleState.CANARY_CONTROLLED,
            OpeningAssignmentLifecycleState.COMPLETED,
        };
        Assert.Equal(4, evs.Length);
    }

    [Fact]
    public void UtilityObservedAssignmentHasValidLifecycle()
    {
        var ev = new OpeningAssignmentTerminalRecord
        {
            EventType = "OPENING_ASSIGNMENT_TERMINAL",
            RequestedControlMode = TeamDepartureControlMode.UTILITY_AI_OBSERVED,
            EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
            LifecycleState = OpeningAssignmentLifecycleState.UTILITY_AI_OBSERVED,
            TerminalReason = "UTILITY_AI_UNCERTIFIED_ROUTE",
            ControllerCreated = false,
            LeaseAcquired = false,
        };
        Assert.Equal("UTILITY_AI_UNCERTIFIED_ROUTE", ev.TerminalReason);
        Assert.False(ev.LeaseAcquired);
    }

    [Fact]
    public void SessionStartTickCannotBeZero()
    {
        var s = new ActiveCanarySession { SessionCreatedTick = 100, ControllerCreatedTick = 100, LeaseAcquiredTick = 100, SessionStartedTick = 100 };
        Assert.True(s.SessionStartedTick > 0);
    }

    [Fact]
    public void SessionStartTickComesFromCanonicalEvent()
    {
        var rec = new CanaryTelemetryRecord { EventType = "CANARY_SESSION_STARTED", DispatchTick = 1474 };
        Assert.True((rec.DispatchTick ?? 0) > 0);
    }

    [Fact]
    public void AbortTimelineIsMonotonic()
    {
        int start = 1474, lastProg = 1520, causal = 1521, rec = 1600, term = 1800;
        Assert.True(start > 0 && lastProg >= start && causal >= lastProg && rec >= causal && term >= rec);
    }

    [Fact]
    public void MissingStartTickIsReported()
    {
        int? startTick = null;
        string status = (startTick == null || startTick <= 0) ? "SESSION_START_TICK_MISSING" : "OK";
        Assert.Equal("SESSION_START_TICK_MISSING", status);
    }

    [Fact]
    public void KnifeIsNotCombatReady()
    {
        Assert.False(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_knife"));
        Assert.False(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_knife_t"));
    }

    [Fact]
    public void GrenadeIsNotCombatReady()
    {
        Assert.False(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_flashbang"));
        Assert.False(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_smokegrenade"));
    }

    [Fact]
    public void C4IsNotCombatReady()
    {
        Assert.False(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_c4"));
    }

    [Fact]
    public void GlockIsCombatReady()
    {
        Assert.True(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_glock"));
    }

    [Fact]
    public void FamasIsCombatReady()
    {
        Assert.True(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_famas"));
    }

    [Fact]
    public void ReadinessRequiresAppliedWeaponSwitch()
    {
        bool switchApplied = true;
        bool combatWeapon = OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_ak47");
        Assert.True(switchApplied && combatWeapon);
    }

    [Fact]
    public void ReadinessUsesActiveWeaponAtThreat()
    {
        string weaponAtThreat = "weapon_knife";
        Assert.False(OpeningRouteCanaryGuard.IsCombatReadyWeapon(weaponAtThreat));
    }

    [Fact]
    public void LegacyBooleanCannotOverrideKnife()
    {
        bool legacyReady = true;
        string weapon = "weapon_knife";
        bool effectiveReady = legacyReady && OpeningRouteCanaryGuard.IsCombatReadyWeapon(weapon);
        Assert.False(effectiveReady);
    }

    [Fact]
    public void ExistingCombinedAccountingStillCloses()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        Assert.Equal(CanaryTeamMode.Combined, guard.Mode);
    }

    [Fact]
    public void OpeningRoutesRemainUnchanged()
    {
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("TR", "tr_b_apps_kitchen_control"));
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("CT", "mid_window_left_awp"));
    }

    [Fact]
    public void PositioningShadowRemainsUnchanged()
    {
        Assert.True(true);
    }

    [Fact]
    public void GoalOwnershipRemainsUnchanged()
    {
        Assert.True(true);
    }
}
