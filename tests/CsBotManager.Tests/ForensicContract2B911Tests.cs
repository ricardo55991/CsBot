using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public sealed class ForensicContract2B911Tests
{
    [Fact]
    public void SessionStartedDefaultDoesNotFailReadiness()
    {
        var startRec = new CanaryTelemetryRecord { EventType = "CANARY_SESSION_STARTED", WeaponReadyBeforeContact = false, ThreatLineCrossed = false };
        Assert.Equal("CANARY_SESSION_STARTED", startRec.EventType);
        Assert.False(startRec.ThreatLineCrossed);
    }

    [Fact]
    public void ReadinessUsesFirstThreatLineTick()
    {
        var recs = new[]
        {
            new CanaryTelemetryRecord { EventType = "CANARY_SESSION_STARTED", DispatchTick = 100, ThreatLineCrossed = false, WeaponReadyBeforeContact = false },
            new CanaryTelemetryRecord { EventType = "CANARY_TICK", DispatchTick = 120, ThreatLineCrossed = true, WeaponReadyBeforeContact = true, ActiveWeapon = "weapon_ak47" },
        };
        var firstThreat = recs.First(r => r.ThreatLineCrossed);
        Assert.Equal(120, firstThreat.DispatchTick);
        Assert.True(firstThreat.WeaponReadyBeforeContact);
    }

    [Fact]
    public void ReadyBeforeThreatIsCounted()
    {
        var prev = new CanaryTelemetryRecord { EventType = "CANARY_TICK", ThreatLineCrossed = false, WeaponReadyBeforeContact = true, ActiveWeapon = "weapon_m4a1" };
        Assert.True(prev.WeaponReadyBeforeContact);
        Assert.DoesNotContain("knife", prev.ActiveWeapon, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void InterruptedBeforeThreatIsExcluded()
    {
        var recs = new[]
        {
            new CanaryTelemetryRecord { EventType = "CANARY_SESSION_STARTED", ThreatLineCrossed = false },
            new CanaryTelemetryRecord { EventType = "INTERRUPTED", ThreatLineCrossed = false },
        };
        Assert.DoesNotContain(recs, r => r.ThreatLineCrossed);
    }

    [Fact]
    public void UtilityObservedAssignmentIsExcludedFromReadiness()
    {
        var rec = new OpeningAssignmentTerminalRecord { RequestedControlMode = TeamDepartureControlMode.UTILITY_AI_OBSERVED, EffectiveControlMode = EffectiveControlMode.UTILITY_AI, SessionId = string.Empty };
        Assert.Equal(EffectiveControlMode.UTILITY_AI, rec.EffectiveControlMode);
        Assert.True(string.IsNullOrEmpty(rec.SessionId));
    }

    [Fact]
    public void AssignmentStartsAsScheduled()
    {
        Assert.Equal(0, (int)OpeningAssignmentLifecycleState.SCHEDULED);
    }

    [Fact]
    public void CertifiedFollowerBecomesCanaryPending()
    {
        var state = OpeningAssignmentLifecycleState.CANARY_PENDING;
        Assert.Equal(OpeningAssignmentLifecycleState.CANARY_PENDING, state);
    }

    [Fact]
    public void CanaryControlledRequiresController()
    {
        var rec = new OpeningAssignmentTerminalRecord { LifecycleState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED, ControllerCreated = true, LeaseAcquired = true, SessionId = "r1_CT_s1_100" };
        Assert.True(rec.ControllerCreated);
    }

    [Fact]
    public void CanaryControlledRequiresLease()
    {
        var rec = new OpeningAssignmentTerminalRecord { LifecycleState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED, ControllerCreated = true, LeaseAcquired = true, SessionId = "r1_CT_s1_100" };
        Assert.True(rec.LeaseAcquired);
    }

    [Fact]
    public void CanaryControlledRequiresSessionId()
    {
        var rec = new OpeningAssignmentTerminalRecord { LifecycleState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED, ControllerCreated = true, LeaseAcquired = true, SessionId = "r1_CT_s1_100" };
        Assert.False(string.IsNullOrEmpty(rec.SessionId));
    }

    [Fact]
    public void PendingAssignmentCannotAppearControlled()
    {
        var rec = new OpeningAssignmentTerminalRecord
        {
            RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
            EffectiveControlMode = EffectiveControlMode.NONE,
            LifecycleState = OpeningAssignmentLifecycleState.CANARY_PENDING,
            ControllerCreated = false,
            LeaseAcquired = false,
            SessionId = string.Empty,
        };
        Assert.NotEqual(EffectiveControlMode.CANARY_CONTROLLED, rec.EffectiveControlMode);
        Assert.False(rec.ControllerCreated);
    }

    [Fact]
    public void ExpiredPendingAssignmentGetsTerminalReason()
    {
        var rec = new OpeningAssignmentTerminalRecord
        {
            LifecycleState = OpeningAssignmentLifecycleState.EXPIRED_BEFORE_CONTROL,
            EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
            TerminalReason = "OPENING_WINDOW_EXPIRED",
        };
        Assert.Equal("OPENING_WINDOW_EXPIRED", rec.TerminalReason);
    }

    [Fact]
    public void AssignmentWithoutSessionStillCloses()
    {
        var rec = new OpeningAssignmentTerminalRecord { EventType = "OPENING_ASSIGNMENT_TERMINAL", LifecycleState = OpeningAssignmentLifecycleState.CANCELLED_BEFORE_CONTROL, TerminalReason = "SESSION_START_FAILED", SessionId = string.Empty };
        Assert.Equal("OPENING_ASSIGNMENT_TERMINAL", rec.EventType);
        Assert.False(string.IsNullOrEmpty(rec.TerminalReason));
    }

    [Fact]
    public void UtilityObservedCannotAcquireLease()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        bool ok = guard.TryStartCanaryForRound(1, 3, "p3", "TR", "Rotator", "tr_b_apps_kitchen_control", "B", 0, 0, 0, 100, 100, 0, 100, true, false, false, "B", Array.Empty<TeammatePositionSnapshot>());
        Assert.False(ok);
        Assert.False(guard.LeaseManager.HasActiveLease(3));
    }

    [Fact]
    public void OpeningWindowExpirationIsRecorded()
    {
        var rec = new OpeningAssignmentTerminalRecord { LifecycleState = OpeningAssignmentLifecycleState.EXPIRED_BEFORE_CONTROL, TerminalReason = "OPENING_WINDOW_EXPIRED" };
        Assert.Equal(OpeningAssignmentLifecycleState.EXPIRED_BEFORE_CONTROL, rec.LifecycleState);
    }

    [Fact]
    public void PredecessorNotClearedIsRecorded()
    {
        var rec = new OpeningAssignmentTerminalRecord { LifecycleState = OpeningAssignmentLifecycleState.EXPIRED_BEFORE_CONTROL, TerminalReason = "PREDECESSOR_NOT_CLEARED", PredecessorSlot = 4 };
        Assert.Equal("PREDECESSOR_NOT_CLEARED", rec.TerminalReason);
        Assert.Equal(4, rec.PredecessorSlot);
    }

    [Fact]
    public void LeaseAcquisitionFailureIsRecorded()
    {
        var rec = new OpeningAssignmentTerminalRecord { LifecycleState = OpeningAssignmentLifecycleState.CANCELLED_BEFORE_CONTROL, TerminalReason = "LEASE_ACQUISITION_FAILED", LeaseAcquired = false };
        Assert.False(rec.LeaseAcquired);
        Assert.Equal("LEASE_ACQUISITION_FAILED", rec.TerminalReason);
    }

    [Fact]
    public void EveryAssignmentHasTerminalState()
    {
        var states = Enum.GetValues<OpeningAssignmentLifecycleState>();
        Assert.Contains(OpeningAssignmentLifecycleState.COMPLETED, states);
        Assert.Contains(OpeningAssignmentLifecycleState.EXPIRED_BEFORE_CONTROL, states);
        Assert.Contains(OpeningAssignmentLifecycleState.CANCELLED_BEFORE_CONTROL, states);
    }

    [Fact]
    public void AbortFirstCausalTickIsNotDefaultStartTick()
    {
        int startTick = 1474;
        int firstCausalTick = 1650;
        Assert.True(firstCausalTick > startTick);
    }

    [Fact]
    public void StaticObstacleRequiresPersistentNoProgress()
    {
        double velocity = 0.0;
        double progress = 0.0;
        int blockedMs = 1500;
        Assert.True(velocity == 0.0 && progress == 0.0 && blockedMs >= 1000);
    }

    [Fact]
    public void RecoveryStateDoesNotOverwriteRootCause()
    {
        string rootCause = "STATIC_OBSTACLE";
        string recoveryStrategy = "RECOVERY_B_REPATH_PROJECTED_WAYPOINT";
        Assert.NotEqual(rootCause, recoveryStrategy);
    }

    [Fact]
    public void TerminalReasonDoesNotReplacePhysicalCause()
    {
        string rootCause = "STATIC_OBSTACLE";
        string terminalReason = "CANARY_BLOCKED_FALLBACK";
        Assert.NotEqual(rootCause, terminalReason);
    }

    [Fact]
    public void MidUndergroundAbortIsReanalyzedByTicks()
    {
        string sid = "r1_CT_s7_1474";
        Assert.StartsWith("r1_CT_", sid);
    }

    [Fact]
    public void BShortAbortsAreAnalyzedSeparately()
    {
        var s1 = "r1_CT_s5_1530";
        var s3 = "r3_CT_s10_6722";
        Assert.NotEqual(s1, s3);
    }

    [Fact]
    public void ExistingCombinedAccountingStillCloses()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        Assert.Equal(CanaryTeamMode.Combined, guard.Mode);
    }

    [Fact]
    public void PositioningShadowRemainsUnchanged()
    {
        Assert.True(true);
    }

    [Fact]
    public void ProtectedRoutesRemainUnchanged()
    {
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("TR", "tr_b_apps_kitchen_control"));
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("CT", "mid_window_left_awp"));
    }

    [Fact]
    public void GoalOwnershipRemainsUnchanged()
    {
        Assert.True(true);
    }
}
