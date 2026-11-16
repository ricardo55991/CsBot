using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class MovementAuthorityIsolationTests
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

    private static string GetOutDir() =>
        Path.Combine(FindRepoRoot(), "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1", "movement_authority_isolation_v1");

    [Fact]
    public void MovementWriterInventoryCoversAllKnownWriters()
    {
        string path = Path.Combine(GetOutDir(), "movement_writer_inventory.json");
        Assert.True(File.Exists(path), $"Arquivo ausente: {path}");
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        var root = doc.RootElement;
        Assert.Equal("movement_writer_inventory_v1", root.GetProperty("schema_version").GetString());

        var writers = root.GetProperty("writers").EnumerateArray().ToList();
        Assert.True(writers.Count >= 11);

        var layers = writers.Select(w => w.GetProperty("layer").GetString()!).ToHashSet();
        Assert.Contains("INTERNAL_CSBOTMANAGER", layers);
        Assert.Contains("EXTERNAL_CSSHARP_PLUGIN", layers);
        Assert.Contains("NATIVE_SERVER_DLL", layers);

        var ids = writers.Select(w => w.GetProperty("writer_id").GetString()!).ToHashSet();
        Assert.Contains("INTERNAL_OPENING_ROUTE_CANARY_CONTROLLER", ids);
        Assert.Contains("INTERNAL_BOT_LOCOMOTION_DRIVER_NAVIGATE", ids);
        Assert.Contains("INTERNAL_MOBILITY_CONTROLLER_KNIFE_LOGIC", ids);
        Assert.Contains("INTERNAL_PACING_AND_FALLBACK_CONTROLLER", ids);
        Assert.Contains("INTERNAL_CT_DEFENSE_CONTROLLER", ids);
        Assert.Contains("EXTERNAL_PLUGIN_BOTSTATE_SMARTER_BOT", ids);
        Assert.Contains("NATIVE_CCSBOT_UPDATE_PATH_MOVEMENT", ids);
        Assert.Contains("NATIVE_CCSBOT_MOVETOSTATE_ONUPDATE_TASK_ENTITY", ids);
    }

    [Fact]
    public void MovementAuthorityGraphHasNoUncontrolledWriterDuringCanary()
    {
        string graphPath = Path.Combine(GetOutDir(), "movement_authority_graph.json");
        string invPath = Path.Combine(GetOutDir(), "movement_writer_inventory.json");
        Assert.True(File.Exists(graphPath));
        Assert.True(File.Exists(invPath));

        using var invDoc = JsonDocument.Parse(File.ReadAllText(invPath));
        foreach (var w in invDoc.RootElement.GetProperty("writers").EnumerateArray())
        {
            bool conflicts = w.GetProperty("conflicts_with_canary").GetBoolean();
            string action = w.GetProperty("isolation_action").GetString() ?? string.Empty;
            Assert.False(string.IsNullOrWhiteSpace(action));
            if (conflicts)
            {
                Assert.NotEqual("NONE", action);
            }
        }

        using var graphDoc = JsonDocument.Parse(File.ReadAllText(graphPath));
        var edges = graphDoc.RootElement.GetProperty("edges").EnumerateArray().ToList();
        Assert.Contains(edges, e => e.GetProperty("from").GetString() == "MovementAuthorityLeaseManager" &&
                                    e.GetProperty("to").GetString() == "BotState_SmarterBot");
        Assert.Contains(edges, e => e.GetProperty("from").GetString() == "NativeCcsBotLocomotionBridge" &&
                                    e.GetProperty("to").GetString() == "CCSBot_MoveToState_0x2E0");
    }

    [Fact]
    public void MovementAuthorityLeaseAcquiresOnlyForSingleCtCanary()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        guard.LeaseManager.SetIsolationModeOverride(CanaryIsolationMode.LeaseIsolated);

        bool started = guard.TryStartCanaryForRound(
            1, 2, "player_2", "CT", "Anchor", CtDest, "A",
            SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ,
            tick: 100, isOpeningPhase: true, isBombPlanted: false);

        Assert.True(started);
        var lease = guard.LeaseManager.ActiveLease;
        Assert.NotNull(lease);
        Assert.True(lease!.IsActive);
        Assert.Equal(1, lease.RoundId);
        Assert.Equal(2, lease.BotSlot);
        Assert.Equal("CT", lease.Team);
        Assert.Equal("OPENING_ROUTE_CANARY", lease.Owner);
        Assert.Equal("opening_navigation_only", lease.AllowedScope);
        Assert.Equal(100, lease.AcquiredTick);
        Assert.True(lease.ExpiresTick > lease.AcquiredTick);
    }

    [Fact]
    public void MovementAuthorityLeaseRejectsSecondBotInSameRound()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);

        Assert.True(guard.TryStartCanaryForRound(
            1, 2, "player_2", "CT", "Anchor", CtDest, "A",
            SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ,
            100, true, false));

        bool secondAttempt = guard.LeaseManager.TryAcquireLease(
            1, 3, "player_3", "CT", "route_2", 102, 500, true, CanaryTeamMode.CtSingle, null, out var lease2, out var reason);

        Assert.False(secondAttempt);
        Assert.Null(lease2);
        Assert.Equal("ACTIVE_LEASE_ALREADY_EXISTS", reason);
        Assert.Equal(1, guard.LeaseManager.LeasesAcquired);
    }

    [Fact]
    public void MovementAuthorityLeaseRejectsTrBotInCtCanary()
    {
        var mgr = new MovementAuthorityLeaseManager();
        mgr.SetKillSwitchOverride(true);

        bool ok = mgr.TryAcquireLease(
            1, 4, "player_4", "TR", "tr_route", 100, 500, true, CanaryTeamMode.CtSingle, null, out var lease, out var reason);

        Assert.False(ok);
        Assert.Null(lease);
        Assert.Equal("TR_BOT_FORBIDDEN_IN_CT_CANARY", reason);
        Assert.Equal(0, mgr.LeasesAcquired);
    }

    [Fact]
    public void MovementAuthorityLeaseRejectsPostOpeningPhase()
    {
        var mgr = new MovementAuthorityLeaseManager();
        mgr.SetKillSwitchOverride(true);

        bool ok = mgr.TryAcquireLease(
            1, 2, "player_2", "CT", "ct_route", 800, 500, isOpeningPhase: false, CanaryTeamMode.CtSingle, null, out var lease, out var reason);

        Assert.False(ok);
        Assert.Null(lease);
        Assert.Equal("NOT_OPENING_PHASE", reason);
    }

    [Fact]
    public void MovementAuthorityLeaseSuppressesCompetingNavigationWriters()
    {
        var mgr = new MovementAuthorityLeaseManager();
        mgr.SetKillSwitchOverride(true);
        mgr.SetIsolationModeOverride(CanaryIsolationMode.LeaseIsolated);

        Assert.True(mgr.TryAcquireLease(1, 2, "player_2", "CT", "ct_route", 100, 600, true, CanaryTeamMode.CtSingle, null, out _, out _));

        // Writers concorrentes no slot 2 (canary) devem ser suprimidos
        Assert.False(mgr.AllowCompetingWriter(1, 2, 110, "PacingAndFallbackController", "NavigateToSpot:exec"));
        Assert.False(mgr.AllowCompetingWriter(1, 2, 112, "CtDefenseController.DuoPlay", "ThrowUtility:43"));
        Assert.False(mgr.AllowCompetingWriter(1, 2, 114, "MobilityController.UpdateTick", "WeaponMobilitySlotSwitch"));

        // Arbitrator também suprime intents não-Canary para o slot 2 enquanto o lease está ativo
        var arb = new MovementArbitrator { LeaseManager = mgr };
        arb.BeginTick(116, 2.0f, 1L);
        arb.PublishIntent(new MovementIntent
        {
            InternalRoundId = 1L,
            BotSlot = 2,
            BotName = "CanaryBot",
            GameTick = 116,
            CurrentTime = 2.0f,
            Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.NavigateNavMesh,
            Reason = "OpeningCanaryImmediate(ct_ticket_booth)",
            GoalX = -1020.9f, GoalY = -2489.1f, GoalZ = -168f
        });
        arb.PublishIntent(new MovementIntent
        {
            InternalRoundId = 1L,
            BotSlot = 2,
            BotName = "CanaryBot",
            GameTick = 116,
            CurrentTime = 2.0f,
            Source = MovementIntentSource.Unstuck,
            Kind = MovementCommandKind.UsercmdVector,
            Reason = "CompetingUnstuck",
            UseUsercmdVelocity = true,
            ForwardMove = 200f
        });

        var dec = arb.CollectAndResolveIntents(2, 116, 2.0f);
        Assert.NotNull(dec);
        Assert.StartsWith("OpeningCanary", dec!.WinningIntent.Reason);
        Assert.True(mgr.ComputeAccountingSummary().SuppressedWriterAttempts >= 4);
    }

    [Fact]
    public void GoalEndOfTickMatchesCanaryWaypointWhileLeaseActive()
    {
        var mgr = new MovementAuthorityLeaseManager();
        mgr.SetKillSwitchOverride(true);
        mgr.SetIsolationModeOverride(CanaryIsolationMode.LeaseIsolated);
        mgr.TryAcquireLease(1, 2, "p2", "CT", "r1", 100, 600, true, CanaryTeamMode.CtSingle, null, out _, out _);

        var wp = new[] { -1020.9f, -2489.1f, -168.0f };
        var rec = mgr.RecordTickVerification(
            tick: 108,
            roundId: 1,
            botSlot: 2,
            playerPseudonym: "p2",
            routeId: "r1",
            waypointIndex: 0,
            activeWaypoint: wp,
            goalBeforeCanary: wp,
            goalAfterCanary: wp,
            goalEndOfTick: wp,
            subpathGoalEndOfTick: new[] { -1200f, -2300f, -200f },
            movementSourceApplied: "TacticalNavigation:NavigateNavMesh",
            nativeState: "MoveTo",
            nativeTask: NativeCcsBotLocomotionBridge.TaskHoldPosition,
            nativePathLength: 6,
            botStateIsolated: true,
            weaponState: "weapon_knife",
            velocityXy: 248.5,
            jumpButtonActive: false,
            usercmdVectorActive: false);

        Assert.False(rec.UnauthorizedOverwriteDetected);
        Assert.Equal(wp, rec.GoalEndOfTick);
        Assert.Equal(0, mgr.UnauthorizedOverwrites);
    }

    [Fact]
    public unsafe void NativeNavigationDoesNotOverwriteCanaryGoal()
    {
        // Valida os offsets nativos da struct CCSBot::MoveToState verificados em server.dll
        Assert.Equal(0x2e0, NativeCcsBotLocomotionBridge.OffsetMoveToState);
        Assert.Equal(0x2e8, NativeCcsBotLocomotionBridge.OffsetMoveToGoalX);
        Assert.Equal(0x2ec, NativeCcsBotLocomotionBridge.OffsetMoveToGoalY);
        Assert.Equal(0x2f0, NativeCcsBotLocomotionBridge.OffsetMoveToGoalZ);
        Assert.Equal(0x2f4, NativeCcsBotLocomotionBridge.OffsetMoveToRouteType);
        Assert.Equal(0x5c0, NativeCcsBotLocomotionBridge.OffsetCurrentStatePtr);
        Assert.Equal(0x5d0, NativeCcsBotLocomotionBridge.OffsetTask);
        Assert.Equal(0x5d4, NativeCcsBotLocomotionBridge.OffsetTaskEntity);
        Assert.Equal(0x4e88, NativeCcsBotLocomotionBridge.OffsetPathLength);

        // Simula bloco de memória de CCSBot para verificar leitura determinística de estado e MoveToGoal
        byte[] fakeBotMem = new byte[0x5000];
        fixed (byte* ptr = fakeBotMem)
        {
            nint h = (nint)ptr;
            *(nint*)(h + NativeCcsBotLocomotionBridge.OffsetCurrentStatePtr) = h + NativeCcsBotLocomotionBridge.OffsetMoveToState;
            *(float*)(h + NativeCcsBotLocomotionBridge.OffsetMoveToGoalX) = -1020.9f;
            *(float*)(h + NativeCcsBotLocomotionBridge.OffsetMoveToGoalY) = -2489.1f;
            *(float*)(h + NativeCcsBotLocomotionBridge.OffsetMoveToGoalZ) = -168.0f;
            *(int*)(h + NativeCcsBotLocomotionBridge.OffsetTask) = NativeCcsBotLocomotionBridge.TaskHoldPosition;
            *(int*)(h + NativeCcsBotLocomotionBridge.OffsetPathLength) = 5;

            Assert.Equal("MoveTo", NativeCcsBotLocomotionBridge.GetNativeStateName(h));
            Assert.Equal(new[] { -1020.9f, -2489.1f, -168.0f }, NativeCcsBotLocomotionBridge.GetMoveToGoal(h));
            Assert.Equal(10, NativeCcsBotLocomotionBridge.GetNativeTask(h));
            Assert.Equal(5, NativeCcsBotLocomotionBridge.GetNativePathLength(h));
        }
    }

    [Fact]
    public void ExternalPluginCannotOverwriteCanaryGoalWhileLeaseActive()
    {
        // Enquanto o lease está ativo, HasBeenControlledByPlayerThisRound = true isola o bot contra BotState (Smarter-Bot)
        // e a restauração ao liberar o lease devolve o valor original (false)
        var snapshot = new NativeBotStateSnapshot
        {
            SafeTime = 0f,
            HasVisitedEnemySpawn = true,
            IsEnemySniperVisible = false,
            Task = 0,
            TaskEntityRaw = uint.MaxValue,
            GoalEntityRaw = uint.MaxValue,
            HasBeenControlledByPlayerThisRound = false,
        };

        var mgr = new MovementAuthorityLeaseManager();
        mgr.SetKillSwitchOverride(true);
        Assert.True(mgr.TryAcquireLease(1, 2, "p2", "CT", "r1", 100, 500, true, CanaryTeamMode.CtSingle, snapshot, out var lease, out _));
        Assert.NotNull(lease!.OriginalState);
        Assert.False(lease.OriginalState!.HasBeenControlledByPlayerThisRound);

        bool restoredFlag = true;
        mgr.ReleaseLease(1, 200, "CANARY_ARRIVED", l => restoredFlag = l.OriginalState!.HasBeenControlledByPlayerThisRound);
        Assert.False(restoredFlag);
        Assert.True(lease.FallbackRestored);
    }

    [Fact]
    public void CanaryLocomotionDoesNotUseContinuousJump()
    {
        var mgr = new MovementAuthorityLeaseManager();
        mgr.SetKillSwitchOverride(true);
        mgr.TryAcquireLease(1, 2, "p2", "CT", "r1", 100, 500, true, CanaryTeamMode.CtSingle, null, out _, out _);

        var wp = new[] { -1020.9f, -2489.1f, -168f };
        for (int t = 100; t <= 140; t += 4)
        {
            var rec = mgr.RecordTickVerification(t, 1, 2, "p2", "r1", 0, wp, wp, wp, wp, wp, "TacticalNavigation:NavigateNavMesh", "MoveTo", 10, 4, true, "weapon_knife", 248.0, jumpButtonActive: false, usercmdVectorActive: false);
            Assert.False(rec.ContinuousJumpDetected);
        }
        Assert.Equal(0, mgr.ContinuousJumpDetections);
    }

    [Fact]
    public void CanaryLocomotionDoesNotUseContinuousUsercmdOverride()
    {
        var mgr = new MovementAuthorityLeaseManager();
        mgr.SetKillSwitchOverride(true);
        mgr.TryAcquireLease(1, 2, "p2", "CT", "r1", 100, 500, true, CanaryTeamMode.CtSingle, null, out _, out _);

        var wp = new[] { -1020.9f, -2489.1f, -168f };
        for (int t = 100; t <= 140; t += 4)
        {
            var rec = mgr.RecordTickVerification(t, 1, 2, "p2", "r1", 0, wp, wp, wp, wp, wp, "TacticalNavigation:NavigateNavMesh", "MoveTo", 10, 4, true, "weapon_knife", 248.0, jumpButtonActive: false, usercmdVectorActive: false);
            Assert.False(rec.ContinuousUsercmdDetected);
        }
        Assert.Equal(0, mgr.ContinuousUsercmdDetections);
    }

    [Fact]
    public void EnemySightReleasesLeaseImmediately()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));
        Assert.True(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));

        var dec = guard.EvaluateTick(1, 2, 132, -1200f, -2300f, -200f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", hasContact: true, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
        Assert.Equal("CONTACT_INTERRUPTION", guard.LeaseManager.LeasesByRound[1].ReleaseReason);
    }

    [Fact]
    public void DamageReleasesLeaseImmediately()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));

        guard.NotifyPlayerDamage(1, 2, 128, isHostileUtility: false);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
        Assert.Equal("DAMAGE_INTERRUPTION", guard.LeaseManager.LeasesByRound[1].ReleaseReason);
    }

    [Fact]
    public void HostileUtilityReleasesLeaseImmediately()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));

        guard.NotifyPlayerDamage(1, 2, 130, isHostileUtility: true);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
        Assert.Equal("HOSTILE_UTILITY", guard.LeaseManager.LeasesByRound[1].ReleaseReason);
    }

    [Fact]
    public void C4OrPlanChangeReleasesLeaseImmediately()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));

        var dec = guard.EvaluateTick(1, 2, 140, -1200f, -2300f, -200f, 220f, "weapon_m4a1", true, true, isBombPlanted: true, CtDest, "A", "Anchor", false, false, false);
        Assert.False(dec.CanaryControlling);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
        Assert.Equal("OPENING_PHASE_ENDED", guard.LeaseManager.LeasesByRound[1].ReleaseReason);
    }

    [Fact]
    public void ArrivalReleasesLeaseAndRestoresUtilityAi()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default, destinationDwellMinTicks: 2);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));

        guard.EvaluateTick(1, 2, 220, FireboxX, FireboxY, FireboxZ, 180f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.True(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));

        var dDone = guard.EvaluateTick(1, 2, 224, FireboxX, FireboxY, FireboxZ, 60f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.False(dDone.CanaryControlling);
        Assert.Equal("UTILITY_AI", dDone.Authority);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
        Assert.Equal("ROUTE_COMPLETED", guard.LeaseManager.LeasesByRound[1].ReleaseReason);
    }

    [Fact]
    public void TimeoutReleasesLeaseAndRestoresUtilityAi()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));

        // Simula tick além de 1.5x do deadline efetivo
        var dTimeout = guard.EvaluateTick(1, 2, 100 + 64 * 25, -1200f, -2200f, -200f, 180f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.False(dTimeout.CanaryControlling);
        Assert.Equal("UTILITY_AI", dTimeout.Authority);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
        Assert.Equal("TIMEOUT", guard.LeaseManager.LeasesByRound[1].ReleaseReason);
    }

    [Fact]
    public void RoundEndReleasesAllLeases()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));
        Assert.True(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));

        guard.LeaseManager.OnRoundEnd(1, 900);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
        Assert.Equal(0, guard.LeaseManager.ActiveLeasesAtRoundEnd);
        Assert.Equal("ROUND_END", guard.LeaseManager.LeasesByRound[1].ReleaseReason);
    }

    [Fact]
    public void CanaryDisabledEnvFlagPreventsAllLeases()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(false);

        bool started = guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false);
        Assert.False(started);
        Assert.Null(guard.LeaseManager.ActiveLease);
        Assert.Equal(0, guard.LeaseManager.LeasesAcquired);
    }

    [Fact]
    public void NonCanaryBotsKeepFullNativeAndUtilityBehavior()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default);
        guard.LeaseManager.SetKillSwitchOverride(true);
        Assert.True(guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100, true, false));

        // Demais 9 bots (slots 0,1,3..9) têm 100% de permissão para todos os writers da Utility AI e nativos
        for (int slot = 0; slot < 10; slot++)
        {
            if (slot == 2) continue;
            Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(slot, 1));
            Assert.True(guard.LeaseManager.AllowCompetingWriter(1, slot, 110, "PacingAndFallbackController", "NavigateToSpot"));
            Assert.True(guard.LeaseManager.AllowCompetingWriter(1, slot, 110, "CtDefenseController", "ThrowUtility"));
            Assert.True(guard.LeaseManager.AllowCompetingWriter(1, slot, 110, "MobilityController", "KnifeSwitch"));
        }
    }

    [Fact]
    public void MovementAuthorityTelemetryCloses()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, NavMeshGraph.Default, destinationDwellMinTicks: 2);
        guard.LeaseManager.SetKillSwitchOverride(true);

        for (int rnd = 1; rnd <= 3; rnd++)
        {
            Assert.True(guard.TryStartCanaryForRound(rnd, 2, "p2", "CT", "Anchor", CtDest, "A", SpawnX, SpawnY, SpawnZ, FireboxX, FireboxY, FireboxZ, 100 * rnd, true, false));
            guard.EvaluateTick(rnd, 2, 100 * rnd + 80, FireboxX, FireboxY, FireboxZ, 160f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
            guard.EvaluateTick(rnd, 2, 100 * rnd + 84, FireboxX, FireboxY, FireboxZ, 40f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
            guard.LeaseManager.OnRoundEnd(rnd, 100 * rnd + 200);
        }

        var summary = guard.LeaseManager.ComputeAccountingSummary();
        Assert.Equal(3, summary.LeasesAcquired);
        Assert.Equal(3, summary.LeasesReleased);
        Assert.Equal(0, summary.ActiveLeasesAtRoundEnd);
        Assert.Equal(0, summary.LeaseReleaseFailures);
        Assert.Equal(0, summary.AuthorityResidue);
    }
}
