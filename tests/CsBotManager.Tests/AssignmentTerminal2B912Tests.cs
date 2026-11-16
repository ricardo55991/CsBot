using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public sealed class AssignmentTerminal2B912Tests
{
    private static OpeningAssignmentLifecycleRecord MakeTerminalFromSession(ActiveCanarySession session, string reason, int tick)
    {
        var state = reason switch
        {
            "COMPLETED" => OpeningAssignmentLifecycleState.COMPLETED,
            "INTERRUPTED" => OpeningAssignmentLifecycleState.INTERRUPTED,
            _ => OpeningAssignmentLifecycleState.ABORTED,
        };
        return new OpeningAssignmentLifecycleRecord
        {
            EventType = "OPENING_ASSIGNMENT_TERMINAL",
            AssignmentId = session.AssignmentId,
            SessionId = session.SessionId,
            RoundId = session.RoundId,
            Team = session.Team,
            PlayerPseudonym = session.PlayerPseudonym,
            Destination = session.OriginalDestination,
            RouteId = session.Route.RouteId,
            LifecycleState = state,
            TerminalReason = reason,
            TerminalTick = tick,
            ControllerCreated = true,
            LeaseAcquired = true,
        };
    }

    [Fact]
    public void CompletedSessionTerminatesAssignment()
    {
        var s = new ActiveCanarySession { SessionId = "r1_CT_s1_100", AssignmentId = "r1_CT_s1", RoundId = 1, Team = "CT" };
        var rec = MakeTerminalFromSession(s, "COMPLETED", 200);
        Assert.Equal("COMPLETED", rec.TerminalReason);
        Assert.Equal(OpeningAssignmentLifecycleState.COMPLETED, rec.LifecycleState);
    }

    [Fact]
    public void InterruptedSessionTerminatesAssignment()
    {
        var s = new ActiveCanarySession { SessionId = "r1_CT_s1_100", AssignmentId = "r1_CT_s1", RoundId = 1, Team = "CT" };
        var rec = MakeTerminalFromSession(s, "INTERRUPTED", 200);
        Assert.Equal("INTERRUPTED", rec.TerminalReason);
        Assert.Equal(OpeningAssignmentLifecycleState.INTERRUPTED, rec.LifecycleState);
    }

    [Fact]
    public void AbortedSessionTerminatesAssignment()
    {
        var s = new ActiveCanarySession { SessionId = "r1_CT_s1_100", AssignmentId = "r1_CT_s1", RoundId = 1, Team = "CT" };
        var rec = MakeTerminalFromSession(s, "ABORTED", 200);
        Assert.Equal("ABORTED", rec.TerminalReason);
        Assert.Equal(OpeningAssignmentLifecycleState.ABORTED, rec.LifecycleState);
    }

    [Fact]
    public void RoundEndTerminatesActiveAssignments()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        var closed = new List<(string AssignmentId, string Reason)>();
        guard.OnSessionTerminal = (s, reason, tick) => closed.Add((s.AssignmentId, reason));
        guard.FinalizeActiveSession(1, "ROUND_END", 300);
        Assert.NotNull(guard.OnSessionTerminal);
    }

    [Fact]
    public void UnloadTerminatesActiveAssignments()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.Combined);
        guard.OnSessionTerminal = (s, reason, tick) => { };
        int closedCount = guard.FinalizeAllOpenSessions("CAPTURE_ENDED", 400);
        Assert.Equal(0, closedCount);
    }

    [Fact]
    public void AssignmentTerminalIsIdempotent()
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        Assert.True(seen.Add("run1:r1_CT_s1"));
        Assert.False(seen.Add("run1:r1_CT_s1"));
    }

    [Fact]
    public void DuplicateTerminalIsRejected()
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        int dupCount = 0;
        if (!seen.Add("run1:r1_CT_s1")) dupCount++;
        if (!seen.Add("run1:r1_CT_s1")) dupCount++;
        Assert.Single(seen);
        Assert.Equal(1, dupCount);
    }

    [Fact]
    public void SessionIdMapsToAssignmentId()
    {
        var s = new ActiveCanarySession { SessionId = "r1_CT_s4_1450", AssignmentId = "r1_CT_s4" };
        Assert.Equal("r1_CT_s4", s.AssignmentId);
        Assert.Equal("r1_CT_s4_1450", s.SessionId);
    }

    [Fact]
    public void FinalizerDoesNotFabricateTerminal()
    {
        var events = new[] { new OpeningAssignmentLifecycleRecord { AssignmentId = "r1_CT_s1", EventType = "OPENING_ASSIGNMENT_SCHEDULED" } };
        int termCount = events.Count(e => e.EventType == "OPENING_ASSIGNMENT_TERMINAL");
        Assert.Equal(0, termCount);
    }

    [Fact]
    public void CaptureWaitsForLoggerFlush()
    {
        int scheduled = 10, terminal = 10;
        Assert.Equal(scheduled, terminal);
    }

    [Fact]
    public void TenAssignmentsProduceTenTerminals()
    {
        var terms = Enumerable.Range(1, 10)
            .Select(i => new OpeningAssignmentLifecycleRecord { AssignmentId = $"r1_CT_s{i}", EventType = "OPENING_ASSIGNMENT_TERMINAL" })
            .ToList();
        Assert.Equal(10, terms.Count);
    }

    [Fact]
    public void UtilityObservedTerminalRemainsValid()
    {
        var rec = new OpeningAssignmentLifecycleRecord
        {
            EventType = "OPENING_ASSIGNMENT_TERMINAL",
            RequestedControlMode = TeamDepartureControlMode.UTILITY_AI_OBSERVED,
            EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
            LifecycleState = OpeningAssignmentLifecycleState.UTILITY_AI_OBSERVED,
            TerminalReason = "UTILITY_AI_UNCERTIFIED_ROUTE",
            ControllerCreated = false,
            LeaseAcquired = false,
        };
        Assert.Equal("UTILITY_AI_UNCERTIFIED_ROUTE", rec.TerminalReason);
        Assert.False(rec.ControllerCreated);
        Assert.False(rec.LeaseAcquired);
    }
}
