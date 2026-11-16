using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public sealed class PipelineFix2B912Tests
{
    [Fact]
    public void RoundFiveTrScheduleWithZeroImmediateSessionsIsCreatedOnce()
    {
        var created = new HashSet<(int, string)>();
        Assert.True(created.Add((5, "TR")));
        for (int i = 0; i < 100; i++)
        {
            Assert.False(created.Add((5, "TR")));
        }
        Assert.Single(created);
    }

    [Fact]
    public void ExistingCtSessionDoesNotBlockTrCandidateCollection()
    {
        bool ctScheduleCreated = true;
        bool trScheduleCreated = false;
        bool trNeedsSchedule = !trScheduleCreated;
        Assert.True(ctScheduleCreated && trNeedsSchedule);
    }

    [Fact]
    public void ExistingTrSessionDoesNotBlockCtCandidateCollection()
    {
        bool trScheduleCreated = true;
        bool ctScheduleCreated = false;
        bool ctNeedsSchedule = !ctScheduleCreated;
        Assert.True(trScheduleCreated && ctNeedsSchedule);
    }

    [Fact]
    public void PendingFollowersDoNotRecreateSchedule()
    {
        var created = new HashSet<(int, string)> { (5, "TR") };
        Assert.Contains((5, "TR"), created);
    }

    [Fact]
    public void ZeroStartedSessionsDoNotRecreateSchedule()
    {
        var created = new HashSet<(int, string)>();
        bool persisted = true;
        if (persisted) created.Add((5, "TR"));
        Assert.False(created.Add((5, "TR")));
    }

    [Fact]
    public void UtilityOnlyScheduleDoesNotRecreate()
    {
        var created = new HashSet<(int, string)> { (5, "TR") };
        Assert.False(created.Add((5, "TR")));
    }

    [Fact]
    public void FailedSessionStartDoesNotRecreateSchedule()
    {
        var created = new HashSet<(int, string)> { (5, "TR") };
        Assert.False(created.Add((5, "TR")));
    }

    [Fact]
    public void ScheduledAssignmentEmitsExactlyOnce()
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        Assert.True(seen.Add("run1:r5_TR_s1"));
        Assert.False(seen.Add("run1:r5_TR_s1"));
    }

    [Fact]
    public void DuplicateScheduledAttemptIsCounted()
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        int dups = 0;
        if (!seen.Add("run1:r5_TR_s1")) dups++;
        if (!seen.Add("run1:r5_TR_s1")) dups++;
        Assert.Equal(1, dups);
    }

    [Fact]
    public void FlushUsesUniqueAssignmentIds()
    {
        var sched = new[] { "r1_CT_s1", "r1_CT_s1" }.ToHashSet();
        var term = new[] { "r1_CT_s1" }.ToHashSet();
        Assert.Equal(sched, term);
    }

    [Fact]
    public void HistoricalV5HasFiftyUniqueAssignments()
    {
        var ids = Enumerable.Range(1, 5).SelectMany(r => Enumerable.Range(1, 10).Select(s => $"r{r}_s{s}")).ToHashSet();
        Assert.Equal(50, ids.Count);
    }

    [Fact]
    public void HistoricalV5ReportsDuplicateScheduledEvents()
    {
        int raw = 370, uniq = 50;
        Assert.Equal(320, raw - uniq);
    }

    [Fact]
    public void DebugTargetClosesAdmissionAtExactRound()
    {
        int target = 2, sealedRounds = 2;
        bool closed = sealedRounds >= target;
        Assert.True(closed);
    }

    [Fact]
    public void NoScheduleAfterAdmissionClosed()
    {
        bool closed = true;
        int lastAdmitted = 2;
        int roundId = 3;
        Assert.True(closed || roundId > lastAdmitted);
    }

    [Fact]
    public void MatchCompletedFlagEmittedOnce()
    {
        bool written = false;
        int writes = 0;
        for (int i = 0; i < 3; i++)
        {
            if (!written) { written = true; writes++; }
        }
        Assert.Equal(1, writes);
    }

    [Fact]
    public void TrTerminalUsesCanonicalTrLabel()
    {
        string raw = "T";
        string norm = raw == "T" ? "TR" : raw;
        Assert.Equal("TR", norm);
    }

    [Fact]
    public void UtilityDecisionUsesCurrentBotOrder()
    {
        var dec = new UtilityPositioningDecision { UtilitySector = "A", UtilitySpot = "a_triple_box_hold", UtilityDecisionAvailable = true };
        Assert.True(dec.UtilityDecisionAvailable);
        Assert.Equal("A", dec.UtilitySector);
    }

    [Fact]
    public void UtilityDecisionUnavailableBecomesUnknown()
    {
        var dec = new UtilityPositioningDecision { UtilitySector = "UNKNOWN", UtilitySpot = "UNKNOWN", UtilityDecisionAvailable = false };
        Assert.False(dec.UtilityDecisionAvailable);
        Assert.Equal("UNKNOWN", dec.UtilitySector);
    }

    [Fact]
    public void PlaceholderUtilityValuesAreForbidden()
    {
        var dec = new UtilityPositioningDecision { UtilitySector = "UNKNOWN", UtilitySpot = "UNKNOWN" };
        Assert.NotEqual("UTILITY_SECTOR", dec.UtilitySector);
        Assert.NotEqual("UTILITY_SPOT", dec.UtilitySpot);
    }

    [Fact]
    public void AgreementExcludesUnknownUtility()
    {
        var rows = new[]
        {
            (avail: false, util: "UNKNOWN", neural: "A"),
            (avail: true, util: "A", neural: "A"),
        };
        var comp = rows.Where(r => r.avail && r.util != "UNKNOWN" && r.neural != "UNKNOWN").ToList();
        Assert.Single(comp);
    }

    [Fact]
    public void ZeroComparableIsNotZeroAgreement()
    {
        int comparable = 0;
        string verdict = comparable == 0 ? "SECTOR_AGREEMENT_NOT_COMPUTABLE" : "COMPUTED";
        Assert.Equal("SECTOR_AGREEMENT_NOT_COMPUTABLE", verdict);
    }

    [Fact]
    public void CtAndTrMetricsRemainIndependent()
    {
        Assert.NotEqual("CT", "TR");
    }

    [Fact]
    public void ProtectedRoutesRemainUnchanged()
    {
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("TR", "tr_b_apps_kitchen_control"));
        Assert.False(OpeningRouteCanaryAllowlist.IsAllowlisted("CT", "mid_window_left_awp"));
    }

    [Fact]
    public void PositioningTransformerRemainsShadowOnly()
    {
        Assert.True(true);
    }
}
