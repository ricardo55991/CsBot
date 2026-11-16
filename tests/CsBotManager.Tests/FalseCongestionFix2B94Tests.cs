using System;
using System.Collections.Generic;
using System.IO;
using Xunit;

namespace CsBotManager.Tests;

public class FalseCongestionFix2B94Tests
{
    private static readonly string RepoRoot = Path.GetFullPath(
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));

    private static NavMeshGraph? LoadMirageNav()
    {
        string path = Path.Combine(RepoRoot, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        return File.Exists(path) ? NavMeshGraph.LoadFromFile(path) : null;
    }

    private static ActiveCanarySession MakeSession(string corridor = "T_SPAWN_EXIT", string conf = "HIGH")
    {
        var g = new OpeningRouteCanaryGuard(mode: CanaryTeamMode.TrSingle, navMesh: LoadMirageNav());
        g.TryStartCanaryForRound(1, 2, "tr2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "A", 1216f, -384f, -163f, 260f, -940f, -150f, 100, true, false);
        var s = g.GetSessionForSlot(1, 2)!;
        s.InferredCorridor = corridor;
        s.CorridorConfidenceName = conf;
        s.LastX = 1100f; s.LastY = -384f; s.LastZ = -163f;
        return s;
    }

    [Fact]
    public void SameCorridorAndPortalCanBlock()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "A_RAMP_ENTRY", 105) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106);
        Assert.True(res.IsVerified);
    }

    [Fact]
    public void DifferentPortalCannotBlock()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "PALACE_ENTRY", 105) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106);
        Assert.False(res.IsVerified);
    }

    [Fact]
    public void BotBehindCannotBlock()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1140f, -384f, -163f, 0f, 0f, "Entry", "A_RAMP_ENTRY", 105) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106);
        Assert.False(res.IsVerified);
    }

    [Fact]
    public void BotBesideCannotBlock()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1095f, -310f, -163f, 0f, 0f, "Entry", "A_RAMP_ENTRY", 105) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106);
        Assert.False(res.IsVerified);
    }

    [Fact]
    public void LowConfidenceCorridorCannotBlock()
    {
        var s = MakeSession("SECTOR_A", "LOW");
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "SECTOR_A", 105) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106);
        Assert.False(res.IsVerified);
        Assert.Equal("CORRIDOR_RELATION_UNCERTAIN", res.Reason);
    }

    [Fact]
    public void StaleSnapshotCannotBlock()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        // 10 ticks = 156.25 ms (> 100 ms)
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "A_RAMP_ENTRY", 100) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 110);
        Assert.False(res.IsVerified);
    }

    [Fact]
    public void DistanceAloneCannotBlock()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "", 105) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106);
        Assert.False(res.IsVerified);
    }

    [Fact]
    public void FinalApproachCannotBecomeFalseCongestion()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        s.FinalApproachActive = true;
        var wp = new RouteWaypoint { Name = "wp", X = 900f, Y = -384f, Z = -163f };
        var tm = new[] { new TeammatePositionSnapshot(4, 1050f, -384f, -163f, 0f, 0f, "Entry", "A_RAMP_ENTRY", 105) };
        var res = OpeningRouteCanaryGuard.FindVerifiedCorridorBlocker(s, wp, tm, currentTick: 106);
        Assert.False(res.IsVerified);
    }

    [Fact]
    public void RootCauseRemainsPreserved()
    {
        var s = MakeSession("A_RAMP_ENTRY", "HIGH");
        s.RootBlockCause = BlockCause.StaticObstacle;
        s.CurrentBlockState = BlockCause.PathRecalculation;
        Assert.Equal(BlockCause.StaticObstacle, s.RootBlockCause);
    }

    [Fact]
    public void CtCoordinationRemainsUnchanged()
    {
        Assert.Empty(GeometricTransitionCatalog.BuildTransitionsForCtRoute("A", "a_triple_box_hold", -350f, -1950f, -168f));
    }

    [Fact]
    public void C4CompatibilityRemainsUnchanged()
    {
        Assert.Equal("C4_CARRIER_COMPATIBLE", OpeningRouteCanaryGuard.EvaluatePlanRouteCompatibility("a_palace_deep_room", "A", "EntryFragger", true));
    }

    [Fact]
    public void RouteAndAuthorityAccountingClose()
    {
        var mgr = new MovementAuthorityLeaseManager { MaxConcurrentLeases = 2 };
        mgr.TryAcquireLease(1, 1, "tr1", "T", "a_palace_deep_room", 100, 640, true, CanaryTeamMode.TrSingle, null, out _, out _);
        mgr.ReleaseLeaseForSlot(1, 1, 150, "DONE");
        Assert.Equal(0, mgr.AccountingResidue);
    }
}
