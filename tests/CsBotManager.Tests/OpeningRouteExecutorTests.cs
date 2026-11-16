using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class OpeningRouteExecutorTests
{
    private const string CtDest = "a_firebox_ninja_hold";
    private const float SpawnX = -1660f;
    private const float SpawnY = -1980f;
    private const float SpawnZ = -267f;
    private const float FireboxX = -450f;
    private const float FireboxY = -2250f;
    private const float FireboxZ = -168f;

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        for (int i = 0; i < 8 && dir != null; i++, dir = dir.Parent)
        {
            if (File.Exists(Path.Combine(dir.FullName, "CsBot.slnx")) || Directory.Exists(Path.Combine(dir.FullName, "src", "CsBotManager")))
            {
                return dir.FullName;
            }
        }
        throw new DirectoryNotFoundException("Repo root not found from test BaseDirectory.");
    }

    [Fact]
    public void EveryAllowlistedWaypointProjectsToNavMesh()
    {
        var nav = NavMeshGraph.Default;
        Assert.NotNull(nav);
        Assert.True(nav!.AreaCount >= 2500);

        string repo = FindRepoRoot();
        string manifestPath = Path.Combine(
            repo, "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1",
            "route_executor_patch_v1", "waypoint_projection_manifest.json");
        Assert.True(File.Exists(manifestPath));

        using var doc = JsonDocument.Parse(File.ReadAllText(manifestPath));
        Assert.True(doc.RootElement.GetProperty("templates_and_spots_within_32u").GetBoolean());
        Assert.True(doc.RootElement.GetProperty("all_entries_valid_after_projection_le_32u").GetBoolean());

        foreach (var wp in doc.RootElement.GetProperty("waypoints").EnumerateArray())
        {
            var proj = wp.GetProperty("projected");
            float px = proj[0].GetSingle();
            float py = proj[1].GetSingle();
            float pz = proj[2].GetSingle();
            var res = nav.ProjectPoint(px, py, pz, maxSnapUnits: 32f);
            Assert.True(res.IsValid, $"Waypoint {wp.GetProperty("id").GetString()} falhou projeção <=32u (delta={res.DeltaUnits}).");
        }
    }

    [Fact]
    public void EveryAllowlistedRouteHasValidNavPath()
    {
        var nav = NavMeshGraph.Default;
        Assert.NotNull(nav);
        string repo = FindRepoRoot();
        string valPath = Path.Combine(
            repo, "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1",
            "route_executor_patch_v1", "route_navmesh_validation.json");
        Assert.True(File.Exists(valPath));

        using var doc = JsonDocument.Parse(File.ReadAllText(valPath));
        int total = doc.RootElement.GetProperty("total_ct_allowlist_routes_checked").GetInt32();
        int connected = doc.RootElement.GetProperty("routes_complete_nav_connectivity").GetInt32();
        int validProj = doc.RootElement.GetProperty("routes_valid_post_projection_le_32u").GetInt32();
        Assert.True(total > 0);
        Assert.Equal(total, connected);
        Assert.Equal(total, validProj);

        // Além do manifesto pré-auditado, valida todas as 19 rotas CT diretamente via OpeningRouteCanaryGuard + NavMeshGraph
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        var planner = new OpeningRoutePlanner();
        var profile = JsonDocument.Parse(File.ReadAllText(Path.Combine(repo, "src", "CsBotManager", "MapProfiles", "de_mirage.json")));
        var spots = profile.RootElement.GetProperty("spots").EnumerateArray()
            .ToDictionary(s => s.GetProperty("id").GetString()!, s => s);

        int rnd = 1;
        foreach (var sid in OpeningRouteCanaryAllowlist.CtAllowedSpots)
        {
            var s = spots[sid];
            Assert.True(planner.TryPlanOpeningRouteForRound(
                rnd++, 1, "ct_test", "CT", "Rotator", sid, s.GetProperty("sector").GetString()!,
                SpawnX, SpawnY, SpawnZ,
                s.GetProperty("x").GetSingle(), s.GetProperty("y").GetSingle(), s.GetProperty("z").GetSingle(),
                100, out var suggestion) && suggestion != null);
            Assert.True(guard.ValidateRouteWaypointsOnNavMesh(suggestion!, out _, out var reason), $"Rota {sid} inválida no NavMesh: {reason}");
        }
    }

    [Fact]
    public void NoWaypointIsInsideWallOrOutOfBounds()
    {
        var nav = NavMeshGraph.Default!;
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, nav);
        Assert.False(guard.LateralRecoveryEnabled);

        // Um ponto fora do mapa / parede distante (> 32u do NavMesh) deve ser rejeitado pelo ProjectPoint strict (32u)
        var outOfBounds = nav.ProjectPoint(9999f, 9999f, -168f, maxSnapUnits: 32f);
        Assert.False(outOfBounds.IsValid);

        // Nenhum waypoint de template CT do planner excede 32u nem contém "_lateral"
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "p2", "CT", "AWPer", "mid_window_right_deep", "MID",
            SpawnX, SpawnY, SpawnZ, -1181.4f, -718.5f, -168f, 100, out var sug) && sug != null);
        foreach (var wp in sug!.OrderedWaypoints)
        {
            Assert.DoesNotContain("_lateral", wp.Name);
            Assert.True(nav.ProjectPoint(wp.X, wp.Y, wp.Z, 32f).IsValid);
        }
    }

    [Fact]
    public void ExecutorTracksEightExplicitStates()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        var blocker = new List<TeammatePositionSnapshot> { new(1, -1550f, -2060f, -256f, 200f, 0f, "Entry", "CT_SPAWN_EXIT") };
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false, teammates: blocker));
        var s = guard.GetSessionForRound(1)!;
        Assert.Equal(CanaryExecutorState.NotStarted, s.ExecutorState);

        var dHold = guard.EvaluateTick(1, 2, 102, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(CanaryExecutorState.NotStarted, dHold.ExecutorState);

        var dDispatch = guard.EvaluateTick(1, 2, 120, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(CanaryExecutorState.CommandDispatched, dDispatch.ExecutorState);
        Assert.Equal(1, dDispatch.CommandId);

        var dMove = guard.EvaluateTick(1, 2, 124, -1500f, -2100f, -256f, 240f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(CanaryExecutorState.Moving, dMove.ExecutorState);

        // Avança pelo waypoint intermediário ct_ticket_booth (-1020.9, -2489.1, -168) já com arma primária pronta -> NEXT_WAYPOINT / COMMAND_DISPATCHED
        var dNext = guard.EvaluateTick(1, 2, 180, -1020.9f, -2489.1f, -168f, 240f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.True(dNext.WaypointChanged);
        Assert.Equal("WAYPOINT_CHANGED", dNext.DispatchReason);
        Assert.Equal(2, dNext.CommandId);

        // Primeiro tick no destino -> WAYPOINT_REACHED (aguardando dwell)
        var dArrive1 = guard.EvaluateTick(1, 2, 240, FireboxX, FireboxY, FireboxZ, 180f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(CanaryExecutorState.WaypointReached, dArrive1.ExecutorState);

        // Segundo tick no destino -> DESTINATION_REACHED
        var dArrive2 = guard.EvaluateTick(1, 2, 244, FireboxX, FireboxY, FireboxZ, 120f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(CanaryExecutorState.DestinationReached, dArrive2.ExecutorState);

        // Verifica constantes INTERRUPTED e FALLBACK também presentes no contrato
        Assert.Equal("INTERRUPTED", CanaryExecutorState.Interrupted);
        Assert.Equal("FALLBACK", CanaryExecutorState.Fallback);
    }

    [Fact]
    public void NavigationDispatchIsFollowedByActualMovement()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        var d1 = guard.EvaluateTick(1, 2, 104, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal("ROUTE_START", d1.DispatchReason);

        var d2 = guard.EvaluateTick(1, 2, 112, -1620f, -2030f, -264f, 230f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(CanaryExecutorState.Moving, d2.ExecutorState);
        var s = guard.GetSessionForRound(1)!;
        Assert.NotNull(s.DispatchTick);
        Assert.NotNull(s.MovementStartedTick);
        Assert.True(s.MovementStartedTick!.Value >= s.DispatchTick!.Value);
        Assert.True(s.PathCreated);
    }

    [Fact]
    public void IntermediateWaypointAdvancesReliably()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default, waypointRadius: 64.0);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);

        // Longe de ct_ticket_booth (-1020.9, -2489.1, -168) -> ainda waypoint 0
        guard.EvaluateTick(1, 2, 110, -1400f, -2200f, -250f, 240f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(0, guard.GetSessionForRound(1)!.WaypointIndex);

        // Dentro do raio validado (<= 64u) -> avança para waypoint 1 (destino final) e dispara WAYPOINT_CHANGED
        var dec = guard.EvaluateTick(1, 2, 160, -1010f, -2470f, -168f, 240f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(1, guard.GetSessionForRound(1)!.WaypointIndex);
        Assert.True(dec.WaypointChanged);
        Assert.Equal("WAYPOINT_CHANGED", dec.DispatchReason);
    }

    [Fact]
    public void DestinationReachedRequiresDwellOrStableArrival()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default, destinationDwellMinTicks: 2);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);

        // Tick único em alta velocidade (220 u/s) passando pelo destino NÃO deve completar ainda
        var pass1 = guard.EvaluateTick(1, 2, 180, FireboxX + 40f, FireboxY, FireboxZ, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.True(pass1.CanaryControlling);
        Assert.Equal(CanaryExecutorState.WaypointReached, pass1.ExecutorState);

        // Permanência no tick seguinte completa a chegada canônica
        var pass2 = guard.EvaluateTick(1, 2, 184, FireboxX + 35f, FireboxY, FireboxZ, 180f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.False(pass2.CanaryControlling);
        Assert.Equal(CanaryExecutorState.DestinationReached, pass2.ExecutorState);
        Assert.Equal("ROUTE_COMPLETED", pass2.AbortOrCompletionReason);
    }

    [Fact]
    public void StaggerHoldsBeforeReleaseWithoutMovementDrift()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        var teammates = new List<TeammatePositionSnapshot>
        {
            new(1, -1550f, -2060f, -256f, 200f, 0f, "Entry", "CT_SPAWN_EXIT")
        };
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false, teammates: teammates);

        var dHold = guard.EvaluateTick(1, 2, 104, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.True(dHold.HoldingForStagger);
        Assert.Null(dHold.CurrentWaypoint);
        Assert.False(dHold.WaypointChanged);
        Assert.Equal("STAGGER_HOLD", dHold.DispatchReason);
        Assert.Equal(0, guard.GetSessionForRound(1)!.BlockedDurationMs);
    }

    [Fact]
    public void RealTeammateBlockerRequiresAllConditions()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        // Blocker diretamente no corredor à frente (<= 140u), em caminho NavMesh válido, sem progresso contínuo
        var blocker = new List<TeammatePositionSnapshot> { new(3, -1590f, -2040f, -264f) };
        CanaryTickDecision? last = null;
        for (int i = 1; i <= 25; i++)
        {
            last = guard.EvaluateTick(1, 2, 130 + i * 4, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, tickIntervalMs: 62, teammates: blocker);
            if (!last.CanaryControlling) break;
        }
        var s = guard.GetSessionForRound(1)!;
        Assert.Equal(BlockCause.TeammateCongestion, s.LastBlockCause);
        Assert.Equal("BLOCKED_BY_TEAMMATE", s.ArrivalStatus);
        Assert.True(s.VerifiedCongestionAllowanceSeconds > 0);
    }

    [Fact]
    public void FalseTeammateBlockIsRejected()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);

        // Caso 1: aliado próximo LATERAL/ATRÁS (fora do corredor à frente) não pode acusar TEAMMATE_CONGESTION
        var sideAlly = new List<TeammatePositionSnapshot> { new(3, SpawnX - 90f, SpawnY + 90f, SpawnZ) };
        guard.EvaluateTick(1, 2, 150, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, tickIntervalMs: 62, teammates: sideAlly);
        Assert.NotEqual(BlockCause.TeammateCongestion, guard.GetSessionForRound(1)!.LastBlockCause);

        // Caso 2: posição fora do NavMesh (9999, 9999) com aliado perto -> NAVMESH_FAILURE, nunca TEAMMATE_CONGESTION
        var offMeshAlly = new List<TeammatePositionSnapshot> { new(4, 9999f, 9999f, -200f) };
        guard.EvaluateTick(1, 2, 160, 9999f, 9999f, -200f, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, tickIntervalMs: 62, teammates: offMeshAlly);
        Assert.Equal(BlockCause.NavmeshFailure, guard.GetSessionForRound(1)!.LastBlockCause);
        Assert.Equal(0.0, guard.GetSessionForRound(1)!.VerifiedCongestionAllowanceSeconds);
    }

    [Fact]
    public void LateralRecoveryIsDisabled()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        Assert.False(guard.LateralRecoveryEnabled);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        var blocker = new List<TeammatePositionSnapshot> { new(3, -1590f, -2040f, -264f) };

        for (int i = 1; i <= 20; i++)
        {
            var dec = guard.EvaluateTick(1, 2, 130 + i * 4, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, tickIntervalMs: 62, teammates: blocker);
            if (dec.CurrentWaypoint != null)
            {
                Assert.DoesNotContain("_lateral", dec.CurrentWaypoint.Name);
            }
            if (!dec.CanaryControlling) break;
        }
        Assert.All(guard.Records, r => Assert.DoesNotContain("_lateral", r.CurrentWaypoint));
        Assert.All(guard.Records, r => Assert.DoesNotContain("_lateral", r.RecoveryWaypoint));
    }

    [Fact]
    public void ValidRepathRecoveryStaysWithinCorridor()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        string origCorridor = guard.GetSessionForRound(1)!.Route.AllowedCorridor;
        var blocker = new List<TeammatePositionSnapshot> { new(3, -1590f, -2040f, -264f) };

        CanaryTickDecision? recDec = null;
        for (int i = 1; i <= 15; i++)
        {
            var dec = guard.EvaluateTick(1, 2, 140 + i * 4, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, tickIntervalMs: 62, teammates: blocker);
            if (dec.DispatchReason == "RECOVERY_AUTHORIZED")
            {
                recDec = dec;
                break;
            }
        }
        Assert.NotNull(recDec);
        Assert.Equal("ct_ticket_booth", recDec!.CurrentWaypoint!.Name);
        Assert.Equal(origCorridor, guard.GetSessionForRound(1)!.Route.AllowedCorridor);
        Assert.True(NavMeshGraph.Default!.ProjectPoint(recDec.CurrentWaypoint.X, recDec.CurrentWaypoint.Y, recDec.CurrentWaypoint.Z, 32f).IsValid);
    }

    [Fact]
    public void TacticalRoleOrDestinationChangeIsClassifiedAsRedirect()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        var dRole = guard.EvaluateTick(1, 2, 120, SpawnX, SpawnY, SpawnZ, 200f, "weapon_knife", true, true, false, CtDest, "A", "Rotator", false, false, false);
        Assert.False(dRole.CanaryControlling);
        Assert.Equal("UTILITY_AI", dRole.Authority);
        Assert.Equal("CANARY_ABORTED:ROLE_IMMUTABLE", dRole.AbortOrCompletionReason);
        Assert.Equal("TACTICAL_REDIRECT", guard.GetSessionForRound(1)!.ArrivalStatus);

        var guard2 = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard2.TryStartCanaryForRound(2, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        var dDest = guard2.EvaluateTick(2, 2, 120, SpawnX, SpawnY, SpawnZ, 200f, "weapon_knife", true, true, false, "b_site_default_plant_box", "A", "Anchor", false, false, false);
        Assert.False(dDest.CanaryControlling);
        Assert.Equal("TACTICAL_REDIRECT", guard2.GetSessionForRound(2)!.ArrivalStatus);
    }

    [Fact]
    public void BaseDeadlineIsPreservedWithoutExtensionMasking()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        var s = guard.GetSessionForRound(1)!;
        double baseDeadline = s.Route.DeadlineSeconds;
        Assert.Equal(baseDeadline, s.EffectiveDeadlineSeconds, 4);

        // NO_PROGRESS_UNKNOWN nunca estende deadline
        guard.EvaluateTick(1, 2, 160, SpawnX, SpawnY, SpawnZ, 10f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(baseDeadline, s.Route.DeadlineSeconds, 4);
        Assert.Equal(0.0, s.VerifiedCongestionAllowanceSeconds, 4);
    }

    [Fact]
    public void LatencyBreakdownAccountsForTotalTime()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        guard.EvaluateTick(1, 2, 104, SpawnX, SpawnY, SpawnZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        guard.EvaluateTick(1, 2, 112, -1620f, -2030f, -264f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        var rec = guard.Records[^1];
        Assert.True(rec.ExpectedTravelTime > 0);
        Assert.True(rec.ActualMovementStartDelay >= 0);
        Assert.Equal(0.0, rec.NavigationFailureTime);
    }

    [Fact]
    public void ContactStillReturnsAuthorityImmediately()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        var dec = guard.EvaluateTick(1, 2, 140, -1000f, -2400f, -168f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", true, false, false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
        Assert.Equal("CONTACT_INTERRUPTION", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void WeaponIsReadyBeforeContact()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        guard.EvaluateTick(1, 2, 140, -1000f, -2400f, -168f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        guard.EvaluateTick(1, 2, 144, -950f, -2400f, -168f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", true, false, false);
        Assert.All(guard.Records, r => Assert.True(r.WeaponReadyBeforeContact));
    }

    [Fact]
    public void NonCanaryBotsRemainUtilityControlled()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        Assert.False(guard.IsSlotActiveCanary(1, 5));
        var d = guard.EvaluateTick(1, 5, 120, SpawnX, SpawnY, SpawnZ, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.False(d.CanaryControlling);
        Assert.Equal("UTILITY_AI", d.Authority);
    }

    [Fact]
    public void PositioningTransformerRemainsShadowOnly()
    {
        string utilityDecision = "HOLD_FIREBOX";
        var pred = new PositioningShadowPrediction { InferenceSuccess = true, SelectedSpotId = 7 };
        Assert.Equal(utilityDecision, ShadowModeGuard.ShadowModeCannotAffectBotDecision(utilityDecision, pred));
    }

    [Fact]
    public void CanaryCannotControlCombat()
    {
        string combatDecision = "ENGAGE_ENEMY_MID";
        Assert.Equal(combatDecision, OpeningRouteCanaryGuard.GuardCombatOrC4Authority(combatDecision, true));
    }
}
