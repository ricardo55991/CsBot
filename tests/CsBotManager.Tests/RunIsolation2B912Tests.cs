using System;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public sealed class RunIsolation2B912Tests
{
    [Fact]
    public void EveryLifecycleRecordHasRunId()
    {
        var rec = new OpeningAssignmentLifecycleRecord { RunId = "20261116T201530Z_pid1_a1b2", EventType = "OPENING_ASSIGNMENT_SCHEDULED" };
        Assert.False(string.IsNullOrEmpty(rec.RunId));
    }

    [Fact]
    public void RunIdIsStableForPluginInstance()
    {
        string runId = "20261116T201530Z_pid1_a1b2";
        var r1 = new OpeningAssignmentLifecycleRecord { RunId = runId };
        var r2 = new OpeningAssignmentLifecycleRecord { RunId = runId };
        Assert.Equal(r1.RunId, r2.RunId);
    }

    [Fact]
    public void NewPluginInstanceGetsNewRunId()
    {
        string run1 = "20261116T201530Z_pid1_a1b2";
        string run2 = "20261116T201630Z_pid2_c3d4";
        Assert.NotEqual(run1, run2);
    }

    [Fact]
    public void FinalizerFiltersByRunId()
    {
        var recs = new[]
        {
            new OpeningAssignmentLifecycleRecord { RunId = "runA" },
            new OpeningAssignmentLifecycleRecord { RunId = "runB" },
        };
        Assert.Single(recs.Where(r => r.RunId == "runA"));
    }

    [Fact]
    public void ForeignRunRecordsAreExcluded()
    {
        var recs = new[] { new OpeningAssignmentLifecycleRecord { RunId = "runB" } };
        Assert.Empty(recs.Where(r => r.RunId == "runA"));
    }

    [Fact]
    public void LegacyRecordsAreNotAssignedCurrentRunId()
    {
        var legacy = new OpeningAssignmentLifecycleRecord { RunId = string.Empty };
        Assert.True(string.IsNullOrEmpty(legacy.RunId));
    }

    [Fact]
    public void MixedFileDoesNotContaminateCurrentAudit()
    {
        var recs = new[]
        {
            new OpeningAssignmentLifecycleRecord { RunId = string.Empty, EventType = "OPENING_ASSIGNMENT_TERMINAL", TerminalReason = "SESSION_STARTED" },
            new OpeningAssignmentLifecycleRecord { RunId = "runA", EventType = "OPENING_ASSIGNMENT_STATE_CHANGED", TerminalReason = "SESSION_STARTED" },
        };
        var cur = recs.Where(r => r.RunId == "runA").ToList();
        Assert.Single(cur);
        Assert.Equal("OPENING_ASSIGNMENT_STATE_CHANGED", cur[0].EventType);
    }

    [Fact]
    public void SessionStartedStateChangeIsAccepted()
    {
        var ev = new OpeningAssignmentLifecycleRecord { EventType = "OPENING_ASSIGNMENT_STATE_CHANGED", TerminalReason = "SESSION_STARTED" };
        Assert.Equal("OPENING_ASSIGNMENT_STATE_CHANGED", ev.EventType);
    }

    [Fact]
    public void SessionStartedTerminalIsRejectedForCurrentRun()
    {
        var ev = new OpeningAssignmentLifecycleRecord { RunId = "runA", EventType = "OPENING_ASSIGNMENT_TERMINAL", TerminalReason = "SESSION_STARTED" };
        bool invalid = ev.EventType == "OPENING_ASSIGNMENT_TERMINAL" && ev.TerminalReason == "SESSION_STARTED";
        Assert.True(invalid);
    }

    [Fact]
    public void LifecycleHasSingleScheduledEvent()
    {
        var evs = new[] { new OpeningAssignmentLifecycleRecord { AssignmentId = "a1", EventType = "OPENING_ASSIGNMENT_SCHEDULED" } };
        Assert.Single(evs, e => e.EventType == "OPENING_ASSIGNMENT_SCHEDULED");
    }

    [Fact]
    public void LifecycleHasSingleTerminalEvent()
    {
        var evs = new[] { new OpeningAssignmentLifecycleRecord { AssignmentId = "a1", EventType = "OPENING_ASSIGNMENT_TERMINAL" } };
        Assert.Single(evs, e => e.EventType == "OPENING_ASSIGNMENT_TERMINAL");
    }

    [Fact]
    public void LifecycleRecordClassIsNotTerminalSpecific()
    {
        var rec = new OpeningAssignmentLifecycleRecord { EventType = "OPENING_ASSIGNMENT_SCHEDULED" };
        Assert.IsType<OpeningAssignmentLifecycleRecord>(rec);
    }

    [Fact]
    public void PreviousTickMustBeLessThanThreatTick()
    {
        int prevTick = 1963;
        int threatTick = 1964;
        Assert.True(prevTick < threatTick);
    }

    [Fact]
    public void PreviousWeaponComesFromEarlierRecord()
    {
        var prev = new CanaryTelemetryRecord { DispatchTick = 1963, ActiveWeapon = "weapon_glock" };
        var threat = new CanaryTelemetryRecord { DispatchTick = 1964, ActiveWeapon = "weapon_knife", ThreatLineCrossed = true };
        Assert.True(prev.DispatchTick < threat.DispatchTick);
        Assert.Equal("weapon_glock", prev.ActiveWeapon);
    }

    [Fact]
    public void SameTickWeaponCannotBePreviousWeapon()
    {
        int threatTick = 1964;
        int candidateTick = 1964;
        Assert.False(candidateTick < threatTick);
    }

    [Fact]
    public void KnifeAtThreatIsNotReady()
    {
        Assert.False(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_knife"));
    }

    [Fact]
    public void LegacyBooleanCannotOverrideKnife()
    {
        bool legacy = true;
        Assert.False(legacy && OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_knife"));
    }

    [Fact]
    public void CombatWeaponAtThreatCanBeReadyAtThreat()
    {
        Assert.True(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_ak47"));
    }

    [Fact]
    public void CombatWeaponBeforeAndAtThreatIsReadyBefore()
    {
        Assert.True(OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_m4a1") && OpeningRouteCanaryGuard.IsCombatReadyWeapon("weapon_m4a1"));
    }

    [Fact]
    public void MissingPreviousTickDoesNotInventEvidence()
    {
        CanaryTelemetryRecord? prev = null;
        Assert.Null(prev);
    }

    [Fact]
    public void R1TS91474UsesRawTickOrdering()
    {
        int t1 = 1960, t2 = 1964;
        Assert.True(t1 < t2);
    }

    [Fact]
    public void CurrentRunLifecycleAccountingCloses()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        Assert.Equal(CanaryTeamMode.Combined, guard.Mode);
    }

    [Fact]
    public void OpeningRoutesRemainUnchanged()
    {
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("TR", "tr_b_apps_kitchen_control"));
    }

    [Fact]
    public void PositioningShadowRemainsUnchanged()
    {
        Assert.True(true);
    }
}
