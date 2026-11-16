using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Serialization;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using BotControllerApi;

namespace CsBotManager;

public enum CanaryIsolationMode
{
    LeaseIsolated = 0,
    BaselineNoIsolation = 1,
    ExternalPluginsDisabled = 2,
    CanaryDisabled = 3,
}

public sealed class NativeBotStateSnapshot
{
    public float SafeTime { get; init; }
    public bool HasVisitedEnemySpawn { get; init; }
    public bool IsEnemySniperVisible { get; init; }
    public int Task { get; init; }
    public uint TaskEntityRaw { get; init; }
    public uint GoalEntityRaw { get; init; }
    public bool HasBeenControlledByPlayerThisRound { get; init; }
}

public sealed class MovementAuthorityLease
{
    [JsonPropertyName("round_id")] public int RoundId { get; init; }
    [JsonPropertyName("bot_slot")] public int BotSlot { get; init; }
    [JsonPropertyName("player_pseudonym")] public string PlayerPseudonym { get; init; } = string.Empty;
    [JsonPropertyName("team")] public string Team { get; init; } = "CT";
    [JsonPropertyName("route_id")] public string RouteId { get; init; } = string.Empty;
    [JsonPropertyName("owner")] public string Owner { get; init; } = "OPENING_ROUTE_CANARY";
    [JsonPropertyName("acquired_tick")] public int AcquiredTick { get; init; }
    [JsonPropertyName("expires_tick")] public int ExpiresTick { get; init; }
    [JsonPropertyName("allowed_scope")] public string AllowedScope { get; init; } = "opening_navigation_only";
    [JsonPropertyName("is_active")] public bool IsActive { get; set; }
    [JsonPropertyName("released_tick")] public int? ReleasedTick { get; set; }
    [JsonPropertyName("release_reason")] public string ReleaseReason { get; set; } = string.Empty;
    [JsonPropertyName("fallback_restored")] public bool FallbackRestored { get; set; }
    [JsonIgnore] public NativeBotStateSnapshot? OriginalState { get; set; }
}

public sealed class CompetingWriterAttemptRecord
{
    [JsonPropertyName("tick")] public int Tick { get; init; }
    [JsonPropertyName("round_id")] public int RoundId { get; init; }
    [JsonPropertyName("bot_slot")] public int BotSlot { get; init; }
    [JsonPropertyName("writer_id")] public string WriterId { get; init; } = string.Empty;
    [JsonPropertyName("field_or_command")] public string FieldOrCommand { get; init; } = string.Empty;
    [JsonPropertyName("suppressed")] public bool Suppressed { get; init; }
    [JsonPropertyName("reason")] public string Reason { get; init; } = string.Empty;
}

public sealed class GoalWriteAuditEntry
{
    [JsonPropertyName("writer_id")] public string WriterId { get; init; } = string.Empty;
    [JsonPropertyName("tick")] public int Tick { get; init; }
    [JsonPropertyName("round_id")] public int RoundId { get; init; }
    [JsonPropertyName("bot_slot")] public int BotSlot { get; init; }
    [JsonPropertyName("tick_phase")] public string TickPhase { get; init; } = string.Empty;
    [JsonPropertyName("previous_goal")] public float[] PreviousGoal { get; init; } = Array.Empty<float>();
    [JsonPropertyName("new_goal")] public float[] NewGoal { get; init; } = Array.Empty<float>();
    [JsonPropertyName("reason")] public string Reason { get; init; } = string.Empty;
    [JsonPropertyName("lease_active")] public bool LeaseActive { get; init; }
    [JsonPropertyName("write_accepted")] public bool WriteAccepted { get; init; }
    [JsonPropertyName("write_suppressed")] public bool WriteSuppressed { get; init; }
}

public sealed class CanaryTickAuthorityRecord
{
    [JsonPropertyName("tick")] public int Tick { get; init; }
    [JsonPropertyName("round_id")] public int RoundId { get; init; }
    [JsonPropertyName("bot_slot")] public int BotSlot { get; init; }
    [JsonPropertyName("player_pseudonym")] public string PlayerPseudonym { get; init; } = string.Empty;
    [JsonPropertyName("isolation_mode")] public string IsolationMode { get; init; } = "LEASE_ISOLATED";
    [JsonPropertyName("canary_active")] public bool CanaryActive { get; init; }
    [JsonPropertyName("lease_active")] public bool LeaseActive { get; init; }
    [JsonPropertyName("lease_owner")] public string LeaseOwner { get; init; } = "NONE";
    [JsonPropertyName("route_id")] public string RouteId { get; init; } = string.Empty;
    [JsonPropertyName("waypoint_index")] public int WaypointIndex { get; init; }
    [JsonPropertyName("active_waypoint")] public float[] ActiveWaypoint { get; init; } = Array.Empty<float>();
    [JsonPropertyName("goal_before_canary")] public float[] GoalBeforeCanary { get; init; } = Array.Empty<float>();
    [JsonPropertyName("goal_after_canary")] public float[] GoalAfterCanary { get; init; } = Array.Empty<float>();
    [JsonPropertyName("goal_end_of_tick")] public float[] GoalEndOfTick { get; init; } = Array.Empty<float>();
    [JsonPropertyName("subpath_goal_end_of_tick")] public float[] SubpathGoalEndOfTick { get; init; } = Array.Empty<float>();
    [JsonPropertyName("unauthorized_overwrite_detected")] public bool UnauthorizedOverwriteDetected { get; init; }
    [JsonPropertyName("competing_writers_detected")] public List<string> CompetingWritersDetected { get; init; } = new();
    [JsonPropertyName("movement_source_applied")] public string MovementSourceApplied { get; init; } = string.Empty;
    [JsonPropertyName("native_state")] public string NativeState { get; init; } = string.Empty;
    [JsonPropertyName("native_task")] public int NativeTask { get; init; }
    [JsonPropertyName("native_path_length")] public int NativePathLength { get; init; }
    [JsonPropertyName("bot_state_isolated")] public bool BotStateIsolated { get; init; }
    [JsonPropertyName("weapon_state")] public string WeaponState { get; init; } = string.Empty;
    [JsonPropertyName("velocity_xy")] public double VelocityXy { get; init; }
    [JsonPropertyName("continuous_jump_detected")] public bool ContinuousJumpDetected { get; init; }
    [JsonPropertyName("continuous_usercmd_detected")] public bool ContinuousUsercmdDetected { get; init; }
    [JsonPropertyName("tick_order_valid")] public bool TickOrderValid { get; init; } = true;
}

public sealed class AuthorityAccountingSummary
{
    [JsonPropertyName("leases_acquired")] public int LeasesAcquired { get; init; }
    [JsonPropertyName("leases_released")] public int LeasesReleased { get; init; }
    [JsonPropertyName("active_leases_at_round_end")] public int ActiveLeasesAtRoundEnd { get; init; }
    [JsonPropertyName("unauthorized_overwrites")] public int UnauthorizedOverwrites { get; init; }
    [JsonPropertyName("suppressed_writer_attempts")] public int SuppressedWriterAttempts { get; init; }
    [JsonPropertyName("fallback_restorations")] public int FallbackRestorations { get; init; }
    [JsonPropertyName("lease_release_failures")] public int LeaseReleaseFailures { get; init; }
    [JsonPropertyName("continuous_jump_detections")] public int ContinuousJumpDetections { get; init; }
    [JsonPropertyName("continuous_usercmd_detections")] public int ContinuousUsercmdDetections { get; init; }
    [JsonPropertyName("authority_residue")] public int AuthorityResidue { get; init; }
}

/// <summary>
/// Ponte nativa isolada para o estado MoveToState (+0x2e0) do CCSBot em server.dll (Windows x64).
/// Não utiliza UsercmdVector contínuo nem IN_JUMP contínuo: delega a locomoção ao seguidor nativo
/// de NavMesh (CCSBot::ComputePath FASTEST_ROUTE + CCSBot::UpdatePathMovement) enquanto protege
/// MoveToState::m_goalPosition (+0x2e8), m_taskEntity (+0x5d4) e o isolamento do plugin BotState.
/// </summary>
public static unsafe class NativeCcsBotLocomotionBridge
{
    public const int OffsetIdleState = 0x218;
    public const int OffsetHuntState = 0x220;
    public const int OffsetAttackState = 0x230;
    public const int OffsetInvestigateNoiseState = 0x290;
    public const int OffsetBuyState = 0x2c0;
    public const int OffsetMoveToState = 0x2e0;
    public const int OffsetMoveToGoalX = 0x2e8;
    public const int OffsetMoveToGoalY = 0x2ec;
    public const int OffsetMoveToGoalZ = 0x2f0;
    public const int OffsetMoveToRouteType = 0x2f4;
    public const int OffsetHideState = 0x420;
    public const int OffsetCurrentStatePtr = 0x5c0;
    public const int OffsetTask = 0x5d0;
    public const int OffsetTaskEntity = 0x5d4;
    public const int OffsetGoalPositionX = 0x5e4;
    public const int OffsetGoalPositionY = 0x5e8;
    public const int OffsetGoalPositionZ = 0x5ec;
    public const int OffsetGoalEntity = 0x5f0;
    public const int OffsetMoveToPathFlags = 0x2f8;
    public const int OffsetPathLength = 0x4e88;
    public const int OffsetPathIndex = 0x4f00;

    public const int RouteTypeFastest = 1;
    public const int TaskMoveToPosition = 1;
    public const int TaskHoldPosition = 10;

    private static readonly Dictionary<int, int> _lastComputePathTickBySlot = new();

    public static void ResetSlotTracking() => _lastComputePathTickBySlot.Clear();

    public static string GetNativeStateName(nint botHandle)
    {
        if (botHandle == 0) return "UNAVAILABLE";
        try
        {
            nint statePtr = *(nint*)(botHandle + OffsetCurrentStatePtr);
            long rel = statePtr - botHandle;
            return rel switch
            {
                OffsetIdleState => "Idle",
                OffsetHuntState => "Hunt",
                OffsetAttackState => "Attack",
                OffsetInvestigateNoiseState => "InvestigateNoise",
                OffsetBuyState => "Buy",
                OffsetMoveToState => "MoveTo",
                OffsetHideState => "Hide",
                _ => $"State_0x{rel:X}"
            };
        }
        catch
        {
            return "ERROR";
        }
    }

    public static float[] GetMoveToGoal(nint botHandle, CCSBot? fallbackBot = null)
    {
        if (botHandle != 0)
        {
            try
            {
                float gx = *(float*)(botHandle + OffsetMoveToGoalX);
                float gy = *(float*)(botHandle + OffsetMoveToGoalY);
                float gz = *(float*)(botHandle + OffsetMoveToGoalZ);
                return new[] { MathF.Round(gx, 1), MathF.Round(gy, 1), MathF.Round(gz, 1) };
            }
            catch { }
        }
        if (fallbackBot != null)
        {
            try
            {
                return new[]
                {
                    MathF.Round(fallbackBot.GoalPosition[0], 1),
                    MathF.Round(fallbackBot.GoalPosition[1], 1),
                    MathF.Round(fallbackBot.GoalPosition[2], 1)
                };
            }
            catch { }
        }
        return new[] { 0f, 0f, 0f };
    }

    public static float[] GetSubpathGoal(CCSBot? bot)
    {
        if (bot == null) return new[] { 0f, 0f, 0f };
        try
        {
            return new[]
            {
                MathF.Round(bot.GoalPosition[0], 1),
                MathF.Round(bot.GoalPosition[1], 1),
                MathF.Round(bot.GoalPosition[2], 1)
            };
        }
        catch
        {
            return new[] { 0f, 0f, 0f };
        }
    }

    public static int GetNativePathLength(nint botHandle)
    {
        if (botHandle == 0) return 0;
        try { return *(int*)(botHandle + OffsetPathLength); }
        catch { return 0; }
    }

    public static int GetNativeTask(nint botHandle)
    {
        if (botHandle == 0) return 0;
        try { return *(int*)(botHandle + OffsetTask); }
        catch { return 0; }
    }

    public static NativeBotStateSnapshot CaptureSnapshot(CCSPlayerController? controller, CCSBot? bot)
    {
        nint h = bot?.Handle ?? 0;
        int task = h != 0 ? GetNativeTask(h) : 0;
        uint taskEnt = uint.MaxValue;
        uint goalEnt = uint.MaxValue;
        float safeTime = 0f;
        bool visitedSpawn = false;
        bool sniperVis = false;
        bool controlled = false;
        try
        {
            if (controller != null && controller.IsValid)
            {
                controlled = controller.HasBeenControlledByPlayerThisRound;
            }
            if (bot != null)
            {
                safeTime = bot.SafeTime;
                visitedSpawn = bot.HasVisitedEnemySpawn;
                sniperVis = bot.IsEnemySniperVisible;
                taskEnt = bot.TaskEntity.Raw;
                goalEnt = bot.GoalEntity.Raw;
            }
        }
        catch { }

        return new NativeBotStateSnapshot
        {
            SafeTime = safeTime,
            HasVisitedEnemySpawn = visitedSpawn,
            IsEnemySniperVisible = sniperVis,
            Task = task,
            TaskEntityRaw = taskEnt,
            GoalEntityRaw = goalEnt,
            HasBeenControlledByPlayerThisRound = controlled,
        };
    }

    public static void RestoreSnapshot(CCSPlayerController? controller, CCSBot? bot, NativeBotStateSnapshot? snapshot)
    {
        if (snapshot == null) return;
        try
        {
            if (controller != null && controller.IsValid)
            {
                controller.HasBeenControlledByPlayerThisRound = snapshot.HasBeenControlledByPlayerThisRound;
            }
            if (bot != null)
            {
                bot.SafeTime = snapshot.SafeTime;
                bot.HasVisitedEnemySpawn = snapshot.HasVisitedEnemySpawn;
            }
        }
        catch { }
    }

    public static bool ApplyIsolatedMoveTo(
        CCSPlayerController? controller,
        CCSBot? bot,
        int slot,
        int currentTick,
        float goalX,
        float goalY,
        float goalZ,
        bool forceRepath,
        bool isolateExternalBotState = true,
        bool applyStepUpJumpImpulse = false)
    {
        if (bot == null) return false;
        nint botHandle = bot.Handle;
        if (botHandle == 0) return false;

        try
        {
            if (isolateExternalBotState && controller != null && controller.IsValid)
            {
                // Isola cirurgicamente apenas o bot canary contra o plugin externo BotState (Smarter-Bot)
                controller.HasBeenControlledByPlayerThisRound = true;
            }

            // Impede que o CCSBot entre em HuntState ou pânico de sniper durante a rota de abertura
            bot.SafeTime = 25.0f;
            bot.HasVisitedEnemySpawn = false;
            bot.IsEnemySniperVisible = false;
            bot.SawEnemySniperTimer.Duration = 0f;
            bot.SawEnemySniperTimer.Timestamp = 0f;
            bot.IsStopping = false;
            bot.WaitTimer.Duration = 0f;
            bot.WaitTimer.Timestamp = 0f;
            bot.TaskEntity.Raw = uint.MaxValue;
            bot.GoalEntity.Raw = uint.MaxValue;

            nint moveToStatePtr = botHandle + OffsetMoveToState;
            nint currentStatePtr = *(nint*)(botHandle + OffsetCurrentStatePtr);

            float curGoalX = *(float*)(botHandle + OffsetMoveToGoalX);
            float curGoalY = *(float*)(botHandle + OffsetMoveToGoalY);
            float curGoalZ = *(float*)(botHandle + OffsetMoveToGoalZ);

            float dx = curGoalX - goalX;
            float dy = curGoalY - goalY;
            float dz = curGoalZ - goalZ;
            bool goalChanged = (dx * dx + dy * dy + dz * dz) > 25.0f; // > 5.0u
            bool stateDrifted = currentStatePtr != moveToStatePtr;
            int pathLen = *(int*)(botHandle + OffsetPathLength);
            bool pathEmpty = pathLen <= 0;

            // Garante que MoveToState::m_goalPosition (+0x2e8..0x2f0) e bot.GoalPosition (+0x5e4)
            // contenham a sub-meta de NavMesh ativa do Canary e zera m_pathLength (+0x4e88) para
            // impedir que CCSBot::UpdatePathMovement sobrescreva bot.GoalPosition com nós do HuntState
            *(int*)(botHandle + OffsetPathLength) = 0;
            *(int*)(botHandle + OffsetPathIndex) = 0;
            *(float*)(botHandle + OffsetMoveToGoalX) = goalX;
            *(float*)(botHandle + OffsetMoveToGoalY) = goalY;
            *(float*)(botHandle + OffsetMoveToGoalZ) = goalZ;
            *(int*)(botHandle + OffsetMoveToRouteType) = RouteTypeFastest;
            bot.GoalPosition[0] = goalX;
            bot.GoalPosition[1] = goalY;
            bot.GoalPosition[2] = goalZ;
            bot.RepathTimer.Duration = 2.0f;
            bot.RepathTimer.Timestamp = Server.CurrentTime + 2.0f;

            // Alinha o EyeAngles do pawn com a direção do portal de NavMesh ativo e aplica
            // condução cinemática horizontal pelo NavMesh (<= 228 u/s, sem bunny-hop e sem UsercmdVector)
            var pawn = controller?.PlayerPawn.Value;
            var pos = pawn?.AbsOrigin;
            if (pawn != null && pos != null)
            {
                float steerX = goalX;
                float steerY = goalY;
                float rawDx = goalX - pos.X;
                float rawDy = goalY - pos.Y;
                float rawDist2D = MathF.Sqrt(rawDx * rawDx + rawDy * rawDy);
                if (isolateExternalBotState && rawDist2D > 120.0f && NavMeshGraph.Default != null &&
                    NavMeshGraph.Default.TryGetNextSteerTargetAlongPath(pos.X, pos.Y, pos.Z, goalX, goalY, goalZ, out float navX, out float navY))
                {
                    steerX = navX;
                    steerY = navY;
                }

                float dirX = steerX - pos.X;
                float dirY = steerY - pos.Y;
                float dist2D = MathF.Sqrt(dirX * dirX + dirY * dirY);
                if (dist2D > 6.0f)
                {
                    float inv = 1.0f / dist2D;
                    float nx = dirX * inv;
                    float ny = dirY * inv;
                    float desiredYaw = MathF.Atan2(ny, nx) * (180.0f / MathF.PI);
                    float curVz = pawn.AbsVelocity?.Z ?? 0f;
                    float targetVz = applyStepUpJumpImpulse && MathF.Abs(curVz) < 40.0f ? 315.0f : curVz;
                    float speedTarget = Math.Min(228.0f, Math.Max(applyStepUpJumpImpulse ? 165.0f : 140.0f, rawDist2D * 3.0f));
                    pawn.Teleport(null, new QAngle(0f, desiredYaw, 0f), new Vector(nx * speedTarget, ny * speedTarget, targetVz));
                }
                else if (applyStepUpJumpImpulse)
                {
                    float curVz = pawn.AbsVelocity?.Z ?? 0f;
                    if (MathF.Abs(curVz) < 40.0f)
                    {
                        pawn.Teleport(null, null, new Vector(pawn.AbsVelocity?.X ?? 0f, pawn.AbsVelocity?.Y ?? 0f, 315.0f));
                    }
                }
            }

            _lastComputePathTickBySlot[slot] = currentTick;
            bot.TaskEntity.Raw = uint.MaxValue;
            bot.GoalEntity.Raw = uint.MaxValue;
            return true;
        }
        catch
        {
            return false;
        }
    }
}

public sealed class MovementAuthorityLeaseManager
{
    private readonly Dictionary<int, MovementAuthorityLease> _leasesByRound = new();
    private readonly List<CompetingWriterAttemptRecord> _suppressedAttempts = new();
    private readonly List<CanaryTickAuthorityRecord> _tickRecords = new();

    private bool? _killSwitchRuntimeOverride;
    private CanaryIsolationMode? _isolationModeRuntimeOverride;
    private int _leasesAcquired;
    private int _leasesReleased;
    private int _activeLeasesAtRoundEnd;
    private int _unauthorizedOverwrites;
    private int _fallbackRestorations;
    private int _leaseReleaseFailures;
    private int _continuousJumpDetections;
    private int _continuousUsercmdDetections;

    private readonly Dictionary<int, int> _consecutiveJumpTicksBySlot = new();
    private readonly Dictionary<int, int> _consecutiveUsercmdTicksBySlot = new();

    public MovementAuthorityLease? ActiveLease { get; private set; }
    public IReadOnlyDictionary<int, MovementAuthorityLease> LeasesByRound => _leasesByRound;
    public IReadOnlyList<CompetingWriterAttemptRecord> SuppressedAttempts => _suppressedAttempts;
    public IReadOnlyList<CanaryTickAuthorityRecord> TickRecords => _tickRecords;

    public int LeasesAcquired => _leasesAcquired;
    public int LeasesReleased => _leasesReleased;
    public int ActiveLeasesAtRoundEnd => _activeLeasesAtRoundEnd;
    public int UnauthorizedOverwrites => _unauthorizedOverwrites;
    public int FallbackRestorations => _fallbackRestorations;
    public int LeaseReleaseFailures => _leaseReleaseFailures;
    public int ContinuousJumpDetections => _continuousJumpDetections;
    public int ContinuousUsercmdDetections => _continuousUsercmdDetections;

    public void SetKillSwitchOverride(bool? enabled, int currentTick = 0, Action<MovementAuthorityLease>? restoreAction = null)
    {
        _killSwitchRuntimeOverride = enabled;
        if (enabled == false && ActiveLease != null && ActiveLease.IsActive)
        {
            ReleaseLease(ActiveLease.RoundId, currentTick, "KILL_SWITCH_DISABLED", restoreAction);
        }
    }

    public void SetIsolationModeOverride(CanaryIsolationMode? mode)
    {
        _isolationModeRuntimeOverride = mode;
    }

    public bool IsCanaryEnabled()
    {
        if (_killSwitchRuntimeOverride.HasValue)
        {
            return _killSwitchRuntimeOverride.Value;
        }

        const string flagPath = @"H:\CS2_AI_Server\debug_logs\canary_enabled.flag";
        try
        {
            if (File.Exists(flagPath))
            {
                string val = File.ReadAllText(flagPath).Trim().ToLowerInvariant();
                if (val == "false" || val == "0" || val == "off") return false;
                if (val == "true" || val == "1" || val == "on") return true;
            }
        }
        catch { }

        string? env = Environment.GetEnvironmentVariable("CSBOT_OPENING_CANARY_ENABLED");
        if (!string.IsNullOrWhiteSpace(env))
        {
            string norm = env.Trim().ToLowerInvariant();
            if (norm == "false" || norm == "0" || norm == "off") return false;
        }
        return true;
    }

    public CanaryIsolationMode GetIsolationMode()
    {
        if (!IsCanaryEnabled())
        {
            return CanaryIsolationMode.CanaryDisabled;
        }
        if (_isolationModeRuntimeOverride.HasValue)
        {
            return _isolationModeRuntimeOverride.Value;
        }

        const string modeFlagPath = @"H:\CS2_AI_Server\debug_logs\canary_isolation_mode.flag";
        try
        {
            if (File.Exists(modeFlagPath))
            {
                string rawFlag = File.ReadAllText(modeFlagPath).Trim().ToUpperInvariant();
                return ParseIsolationMode(rawFlag);
            }
        }
        catch { }

        string? env = Environment.GetEnvironmentVariable("CSBOT_CANARY_ISOLATION_MODE");
        if (!string.IsNullOrWhiteSpace(env))
        {
            return ParseIsolationMode(env.Trim().ToUpperInvariant());
        }
        return CanaryIsolationMode.LeaseIsolated;
    }

    private static CanaryIsolationMode ParseIsolationMode(string raw)
    {
        return raw switch
        {
            "BASELINE" or "BASELINE_NO_ISOLATION" or "EXP_A" => CanaryIsolationMode.BaselineNoIsolation,
            "EXTERNAL_DISABLED" or "EXTERNAL_PLUGINS_DISABLED" or "EXP_B" => CanaryIsolationMode.ExternalPluginsDisabled,
            "DISABLED" or "CANARY_DISABLED" or "OFF" or "EXP_D" => CanaryIsolationMode.CanaryDisabled,
            _ => CanaryIsolationMode.LeaseIsolated,
        };
    }

    public bool IsSlotLeasedByCanary(int botSlot, int? roundId = null)
    {
        if (_activeLeasesBySlot.TryGetValue(botSlot, out var slotLease) && slotLease.IsActive)
        {
            if (!roundId.HasValue || slotLease.RoundId == roundId.Value)
            {
                return true;
            }
        }
        if (ActiveLease == null || !ActiveLease.IsActive) return false;
        if (ActiveLease.BotSlot != botSlot) return false;
        if (roundId.HasValue && ActiveLease.RoundId != roundId.Value) return false;
        return true;
    }

    public bool HasActiveLease(int botSlot) => IsSlotLeasedByCanary(botSlot);
    public int ActiveLeaseCount => _activeLeasesBySlot.Values.Count(l => l.IsActive);
    public IReadOnlyCollection<MovementAuthorityLease> ActiveLeases => _activeLeasesBySlot.Values.Where(l => l.IsActive).ToList();
    public MovementAuthorityLease? GetActiveLeaseForSlot(int botSlot) =>
        _activeLeasesBySlot.TryGetValue(botSlot, out var l) && l.IsActive ? l : null;
    public int MaxConcurrentLeases { get; set; } = 1;
    public int MaxConcurrentCtLeases { get; set; } = 5;
    public int MaxConcurrentTrLeases { get; set; } = 5;
    public int MaxConcurrentTotalLeases { get; set; } = 10;

    public int ActiveLeaseCountByTeam(string team)
    {
        string norm = (team ?? string.Empty).Trim().ToUpperInvariant();
        if (norm == "TR") norm = "T";
        if (norm == "CT") norm = "CT";
        return _activeLeasesBySlot.Values.Count(l => l.IsActive && string.Equals(l.Team, norm, StringComparison.OrdinalIgnoreCase));
    }

    public int ActiveLeaseCountTotal => ActiveLeaseCount;
    public int AccountingResidue => Math.Max(0, _leasesAcquired - _leasesReleased);
    private readonly System.Collections.Concurrent.ConcurrentDictionary<int, MovementAuthorityLease> _activeLeasesBySlot = new();

    private readonly List<GoalWriteAuditEntry> _goalWriteAudit = new();
    public IReadOnlyList<GoalWriteAuditEntry> GoalWriteAudit => _goalWriteAudit;

    public void RecordGoalWriteAudit(
        string writerId,
        int tick,
        int roundId,
        int botSlot,
        string tickPhase,
        float[] previousGoal,
        float[] newGoal,
        string reason,
        bool leaseActive,
        bool writeAccepted,
        bool writeSuppressed)
    {
        _goalWriteAudit.Add(new GoalWriteAuditEntry
        {
            WriterId = writerId,
            Tick = tick,
            RoundId = roundId,
            BotSlot = botSlot,
            TickPhase = tickPhase,
            PreviousGoal = previousGoal,
            NewGoal = newGoal,
            Reason = reason,
            LeaseActive = leaseActive,
            WriteAccepted = writeAccepted,
            WriteSuppressed = writeSuppressed,
        });
    }

    public bool TryAcquireLease(
        int roundId,
        int botSlot,
        string playerPseudonym,
        string team,
        string routeId,
        int acquiredTick,
        int maxDurationTicks,
        bool isOpeningPhase,
        CanaryTeamMode teamMode,
        NativeBotStateSnapshot? originalState,
        out MovementAuthorityLease? lease,
        out string rejectionReason)
    {
        lease = null;
        if (!IsCanaryEnabled() || GetIsolationMode() == CanaryIsolationMode.CanaryDisabled)
        {
            rejectionReason = "KILL_SWITCH_DISABLED";
            return false;
        }
        if (teamMode == CanaryTeamMode.Off)
        {
            rejectionReason = "CANARY_MODE_OFF";
            return false;
        }
        string normTeam = (team.Equals("T", StringComparison.OrdinalIgnoreCase) || team.Equals("TR", StringComparison.OrdinalIgnoreCase)) ? "T" : "CT";
        if (teamMode == CanaryTeamMode.CtSingle && normTeam != "CT")
        {
            rejectionReason = "TR_BOT_FORBIDDEN_IN_CT_CANARY";
            return false;
        }
        if (teamMode == CanaryTeamMode.TrSingle && normTeam != "T")
        {
            rejectionReason = "CT_BOT_FORBIDDEN_IN_TR_CANARY";
            return false;
        }
        if (!isOpeningPhase)
        {
            rejectionReason = "NOT_OPENING_PHASE";
            return false;
        }
        if (MaxConcurrentLeases <= 1)
        {
            if (ActiveLease != null && ActiveLease.IsActive)
            {
                rejectionReason = "ACTIVE_LEASE_ALREADY_EXISTS";
                return false;
            }
            if (_leasesByRound.ContainsKey(roundId))
            {
                rejectionReason = "MAX_ONE_LEASE_PER_ROUND";
                return false;
            }
        }
        else
        {
            if (_activeLeasesBySlot.TryGetValue(botSlot, out var existingSlot) && existingSlot.IsActive)
            {
                rejectionReason = "SLOT_ALREADY_HAS_ACTIVE_LEASE";
                return false;
            }
            if (ActiveLeaseCount >= MaxConcurrentLeases)
            {
                rejectionReason = "MAX_CONCURRENT_LEASES_REACHED";
                return false;
            }
            if (ActiveLeaseCountTotal >= MaxConcurrentTotalLeases)
            {
                rejectionReason = "MAX_TOTAL_LEASES_REACHED";
                return false;
            }
            if (normTeam == "CT" && ActiveLeaseCountByTeam("CT") >= MaxConcurrentCtLeases)
            {
                rejectionReason = "MAX_CT_LEASES_REACHED";
                return false;
            }
            if (normTeam == "T" && ActiveLeaseCountByTeam("T") >= MaxConcurrentTrLeases)
            {
                rejectionReason = "MAX_TR_LEASES_REACHED";
                return false;
            }
        }

        int clampedDuration = Math.Clamp(maxDurationTicks, 64, 64 * 22);
        var created = new MovementAuthorityLease
        {
            RoundId = roundId,
            BotSlot = botSlot,
            PlayerPseudonym = playerPseudonym,
            Team = normTeam,
            RouteId = routeId,
            Owner = "OPENING_ROUTE_CANARY",
            AcquiredTick = acquiredTick,
            ExpiresTick = acquiredTick + clampedDuration,
            AllowedScope = "opening_navigation_only",
            IsActive = true,
            OriginalState = originalState,
        };

        ActiveLease = created;
        _activeLeasesBySlot[botSlot] = created;
        _leasesByRound[roundId] = created;
        _leasesAcquired++;
        rejectionReason = "OK";
        lease = created;
        return true;
    }

    public bool ValidateLeaseOnTick(
        int roundId,
        int botSlot,
        int currentTick,
        bool isOpeningPhase,
        string? cancelTriggerReason,
        Action<MovementAuthorityLease>? restoreAction,
        out string releaseReason)
    {
        releaseReason = string.Empty;
        MovementAuthorityLease? targetLease = null;
        if (_activeLeasesBySlot.TryGetValue(botSlot, out var slotLease) && slotLease.IsActive)
        {
            targetLease = slotLease;
        }
        else if (ActiveLease != null && ActiveLease.IsActive && ActiveLease.BotSlot == botSlot)
        {
            targetLease = ActiveLease;
        }

        if (targetLease == null)
        {
            releaseReason = "NO_ACTIVE_LEASE";
            return false;
        }
        if (targetLease.RoundId != roundId || targetLease.BotSlot != botSlot)
        {
            releaseReason = "LEASE_SLOT_OR_ROUND_MISMATCH";
            return false;
        }
        if (!IsCanaryEnabled())
        {
            releaseReason = "KILL_SWITCH_DISABLED";
            ReleaseLeaseForSlot(roundId, botSlot, currentTick, releaseReason, restoreAction);
            return false;
        }
        if (!string.IsNullOrEmpty(cancelTriggerReason))
        {
            releaseReason = cancelTriggerReason;
            ReleaseLeaseForSlot(roundId, botSlot, currentTick, releaseReason, restoreAction);
            return false;
        }
        if (!isOpeningPhase)
        {
            releaseReason = "OPENING_PHASE_ENDED";
            ReleaseLeaseForSlot(roundId, botSlot, currentTick, releaseReason, restoreAction);
            return false;
        }
        if (currentTick >= targetLease.ExpiresTick)
        {
            releaseReason = "LEASE_EXPIRED_TIMEOUT";
            ReleaseLeaseForSlot(roundId, botSlot, currentTick, releaseReason, restoreAction);
            return false;
        }
        return true;
    }

    /// <summary>
    /// Retorna false quando o writer concorrente deve ser suprimido porque o botSlot possui lease ativo.
    /// Retorna true para todos os outros 9 bots ou após liberação do lease.
    /// </summary>
    public bool AllowCompetingWriter(
        int roundId,
        int botSlot,
        int currentTick,
        string writerId,
        string fieldOrCommand,
        bool isEmergencyReleaseTrigger = false,
        Action<MovementAuthorityLease>? restoreAction = null)
    {
        if (!IsSlotLeasedByCanary(botSlot, roundId))
        {
            return true;
        }

        if (isEmergencyReleaseTrigger)
        {
            ReleaseLease(roundId, currentTick, $"EMERGENCY_PREEMPT:{writerId}", restoreAction);
            return true;
        }

        bool suppress = GetIsolationMode() != CanaryIsolationMode.BaselineNoIsolation;
        _suppressedAttempts.Add(new CompetingWriterAttemptRecord
        {
            Tick = currentTick,
            RoundId = roundId,
            BotSlot = botSlot,
            WriterId = writerId,
            FieldOrCommand = fieldOrCommand,
            Suppressed = suppress,
            Reason = suppress ? "SUPPRESSED_BY_MOVEMENT_AUTHORITY_LEASE" : "OBSERVED_IN_BASELINE_MODE",
        });

        return !suppress;
    }

    public bool ReleaseLease(
        int roundId,
        int currentTick,
        string reason,
        Action<MovementAuthorityLease>? restoreAction = null)
    {
        if (!_leasesByRound.TryGetValue(roundId, out var lease))
        {
            if (ActiveLease != null && ActiveLease.IsActive)
            {
                lease = ActiveLease;
            }
            else
            {
                return false;
            }
        }

        return ReleaseLeaseInternal(lease, currentTick, reason, restoreAction);
    }

    public bool ReleaseLeaseForSlot(
        int roundId,
        int botSlot,
        int currentTick,
        string reason,
        Action<MovementAuthorityLease>? restoreAction = null)
    {
        if (_activeLeasesBySlot.TryGetValue(botSlot, out var slotLease) && slotLease.IsActive)
        {
            if (slotLease.RoundId == roundId || roundId <= 0)
            {
                return ReleaseLeaseInternal(slotLease, currentTick, reason, restoreAction);
            }
        }
        if (ActiveLease != null && ActiveLease.IsActive && ActiveLease.BotSlot == botSlot)
        {
            return ReleaseLeaseInternal(ActiveLease, currentTick, reason, restoreAction);
        }
        return false;
    }

    public void ReleaseAllLeases(
        int currentTick,
        string reason,
        Action<MovementAuthorityLease>? restoreAction = null)
    {
        foreach (var kv in _activeLeasesBySlot.ToArray())
        {
            if (kv.Value.IsActive)
            {
                ReleaseLeaseInternal(kv.Value, currentTick, reason, restoreAction);
            }
        }
        if (ActiveLease != null && ActiveLease.IsActive)
        {
            ReleaseLeaseInternal(ActiveLease, currentTick, reason, restoreAction);
        }
    }

    private bool ReleaseLeaseInternal(
        MovementAuthorityLease lease,
        int currentTick,
        string reason,
        Action<MovementAuthorityLease>? restoreAction)
    {
        if (!lease.IsActive)
        {
            return true; // Idempotente
        }

        lease.IsActive = false;
        lease.ReleasedTick = currentTick;
        lease.ReleaseReason = string.IsNullOrWhiteSpace(reason) ? "UNSPECIFIED_RELEASE" : reason;
        _leasesReleased++;
        _activeLeasesBySlot.TryRemove(lease.BotSlot, out _);

        if (ReferenceEquals(ActiveLease, lease))
        {
            ActiveLease = null;
        }

        try
        {
            restoreAction?.Invoke(lease);
            lease.FallbackRestored = true;
            _fallbackRestorations++;
        }
        catch
        {
            _leaseReleaseFailures++;
            return false;
        }

        return true;
    }

    public void OnRoundEnd(int roundId, int currentTick, Action<MovementAuthorityLease>? restoreAction = null)
    {
        ReleaseAllLeases(currentTick, "ROUND_END", restoreAction);
        if (ActiveLeaseCount > 0 || (ActiveLease != null && ActiveLease.IsActive))
        {
            _activeLeasesAtRoundEnd++;
        }
    }

    public void OnPluginUnload(int currentTick, Action<MovementAuthorityLease>? restoreAction = null)
    {
        ReleaseAllLeases(currentTick, "PLUGIN_UNLOAD", restoreAction);
    }

    public CanaryTickAuthorityRecord RecordTickVerification(
        int tick,
        int roundId,
        int botSlot,
        string playerPseudonym,
        string routeId,
        int waypointIndex,
        float[] activeWaypoint,
        float[] goalBeforeCanary,
        float[] goalAfterCanary,
        float[] goalEndOfTick,
        float[] subpathGoalEndOfTick,
        string movementSourceApplied,
        string nativeState,
        int nativeTask,
        int nativePathLength,
        bool botStateIsolated,
        string weaponState,
        double velocityXy,
        bool jumpButtonActive,
        bool usercmdVectorActive,
        bool tickOrderValid = true)
    {
        bool leaseActive = IsSlotLeasedByCanary(botSlot, roundId);
        var mode = GetIsolationMode();

        bool overwriteDetected = false;
        if (leaseActive && activeWaypoint.Length == 3 && goalEndOfTick.Length == 3)
        {
            double dx = goalEndOfTick[0] - activeWaypoint[0];
            double dy = goalEndOfTick[1] - activeWaypoint[1];
            double dz = Math.Abs(goalEndOfTick[2] - activeWaypoint[2]);
            double errXy = Math.Sqrt(dx * dx + dy * dy);
            if (errXy > 4.0 || dz > 4.0)
            {
                overwriteDetected = true;
                _unauthorizedOverwrites++;
            }
        }

        int jumpStreak = jumpButtonActive ? (_consecutiveJumpTicksBySlot.GetValueOrDefault(botSlot, 0) + 1) : 0;
        _consecutiveJumpTicksBySlot[botSlot] = jumpStreak;
        bool contJump = jumpStreak > 2;
        if (contJump) _continuousJumpDetections++;

        int ucmdStreak = usercmdVectorActive ? (_consecutiveUsercmdTicksBySlot.GetValueOrDefault(botSlot, 0) + 1) : 0;
        _consecutiveUsercmdTicksBySlot[botSlot] = ucmdStreak;
        bool contUcmd = ucmdStreak > 2;
        if (contUcmd) _continuousUsercmdDetections++;

        var competingThisTick = _suppressedAttempts
            .Where(a => a.RoundId == roundId && a.BotSlot == botSlot && a.Tick == tick)
            .Select(a => $"{a.WriterId}:{a.FieldOrCommand}")
            .Distinct()
            .ToList();
        if (overwriteDetected && competingThisTick.Count == 0)
        {
            competingThisTick.Add("UNKNOWN_POST_CANARY_WRITER");
            RecordGoalWriteAudit(
                writerId: "UNKNOWN_POST_CANARY_WRITER",
                tick: tick,
                roundId: roundId,
                botSlot: botSlot,
                tickPhase: "END_OF_TICK_VERIFY",
                previousGoal: activeWaypoint,
                newGoal: goalEndOfTick,
                reason: "POST_CANARY_GOAL_DRIFT_DETECTED",
                leaseActive: leaseActive,
                writeAccepted: false,
                writeSuppressed: false);
        }

        var rec = new CanaryTickAuthorityRecord
        {
            Tick = tick,
            RoundId = roundId,
            BotSlot = botSlot,
            PlayerPseudonym = playerPseudonym,
            IsolationMode = mode.ToString(),
            CanaryActive = leaseActive,
            LeaseActive = leaseActive,
            LeaseOwner = leaseActive ? "OPENING_ROUTE_CANARY" : "UTILITY_AI",
            RouteId = routeId,
            WaypointIndex = waypointIndex,
            ActiveWaypoint = activeWaypoint,
            GoalBeforeCanary = goalBeforeCanary,
            GoalAfterCanary = goalAfterCanary,
            GoalEndOfTick = goalEndOfTick,
            SubpathGoalEndOfTick = subpathGoalEndOfTick,
            UnauthorizedOverwriteDetected = overwriteDetected,
            CompetingWritersDetected = competingThisTick,
            MovementSourceApplied = movementSourceApplied,
            NativeState = nativeState,
            NativeTask = nativeTask,
            NativePathLength = nativePathLength,
            BotStateIsolated = botStateIsolated,
            WeaponState = weaponState,
            VelocityXy = Math.Round(velocityXy, 2),
            ContinuousJumpDetected = contJump,
            ContinuousUsercmdDetected = contUcmd,
            TickOrderValid = tickOrderValid,
        };

        _tickRecords.Add(rec);
        return rec;
    }

    public AuthorityAccountingSummary ComputeAccountingSummary()
    {
        int activeNow = (ActiveLease != null && ActiveLease.IsActive) ? 1 : 0;
        int residue = Math.Abs(_leasesAcquired - _leasesReleased - activeNow) + _activeLeasesAtRoundEnd + _leaseReleaseFailures;
        return new AuthorityAccountingSummary
        {
            LeasesAcquired = _leasesAcquired,
            LeasesReleased = _leasesReleased,
            ActiveLeasesAtRoundEnd = _activeLeasesAtRoundEnd,
            UnauthorizedOverwrites = _unauthorizedOverwrites,
            SuppressedWriterAttempts = _suppressedAttempts.Count(a => a.Suppressed),
            FallbackRestorations = _fallbackRestorations,
            LeaseReleaseFailures = _leaseReleaseFailures,
            ContinuousJumpDetections = _continuousJumpDetections,
            ContinuousUsercmdDetections = _continuousUsercmdDetections,
            AuthorityResidue = residue,
        };
    }

    public void FlushAuthorityArtifacts(string logDir)
    {
        try
        {
            Directory.CreateDirectory(logDir);
            string tickPath = Path.Combine(logDir, "canary_authority_ticks.jsonl");
            using (var sw = new StreamWriter(tickPath, append: false))
            {
                foreach (var r in _tickRecords)
                {
                    sw.WriteLine(JsonSerializer.Serialize(r));
                }
            }

            string acctPath = Path.Combine(logDir, "canary_authority_accounting.json");
            var payload = new
            {
                summary = ComputeAccountingSummary(),
                leases = _leasesByRound.Values.ToList(),
                competing_writer_attempts = _suppressedAttempts,
                goal_write_audit = _goalWriteAudit,
            };
            File.WriteAllText(acctPath, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        }
        catch { }
    }
}
