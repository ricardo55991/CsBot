using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace CsBotManager;

public enum CanaryTeamMode
{
    Off,
    CtSingle,
    TrSingle,
    Combined
}

public static class CanaryExecutorState
{
    public const string NotStarted = "NOT_STARTED";
    public const string CommandDispatched = "COMMAND_DISPATCHED";
    public const string Moving = "MOVING";
    public const string WaypointReached = "WAYPOINT_REACHED";
    public const string NextWaypoint = "NEXT_WAYPOINT";
    public const string DestinationReached = "DESTINATION_REACHED";
    public const string Interrupted = "INTERRUPTED";
    public const string Fallback = "FALLBACK";
}

public static class BlockCause
{
    public const string None = "NONE";
    public const string TeammateCongestion = "TEAMMATE_CONGESTION";
    public const string NavmeshFailure = "NAVMESH_FAILURE";
    public const string StaticObstacle = "STATIC_OBSTACLE";
    public const string PathRecalculation = "PATH_RECALCULATION";
    public const string NoProgressUnknown = "NO_PROGRESS_UNKNOWN";
}

public sealed record TeammatePositionSnapshot(
    int RawSlot,
    float X,
    float Y,
    float Z,
    float Vx = 0f,
    float Vy = 0f,
    string Role = "",
    string ConflictGroup = "",
    int SnapshotTick = 0);

public sealed record StaggerScheduleEntry(
    int SpawnPriority,
    int RolePriority,
    string ConflictGroup,
    int PlannedStaggerMs,
    int PlannedReleaseTick,
    double MinimumSpacingUnits,
    int? PredecessorSlot);

public sealed class NoEligibleCanaryRecord
{
    [JsonPropertyName("round")] public int Round { get; init; }
    [JsonPropertyName("team")] public string Team { get; init; } = string.Empty;
    [JsonPropertyName("reason")] public string Reason { get; init; } = "NO_ELIGIBLE_CT_CANARY";
    [JsonPropertyName("candidates_checked")] public int CandidatesChecked { get; init; }
}

public sealed class CanaryTelemetryRecord
{
    [JsonPropertyName("round")] public int Round { get; init; }
    [JsonPropertyName("session_id")] public string SessionId { get; init; } = string.Empty;
    [JsonPropertyName("controller_id")] public string ControllerId { get; init; } = string.Empty;
    [JsonPropertyName("lease_id")] public string LeaseId { get; init; } = string.Empty;
    [JsonPropertyName("event_type")] public string EventType { get; init; } = "CANARY_TICK";
    [JsonPropertyName("player_pseudonym")] public string PlayerPseudonym { get; init; } = string.Empty;
    [JsonPropertyName("team")] public string Team { get; init; } = string.Empty;
    [JsonPropertyName("canary_enabled")] public bool CanaryEnabled { get; init; }
    [JsonPropertyName("authority")] public string Authority { get; init; } = "UTILITY_AI";
    [JsonPropertyName("executor_state")] public string ExecutorState { get; init; } = CanaryExecutorState.NotStarted;
    [JsonPropertyName("command_id")] public int CommandId { get; init; }
    [JsonPropertyName("dispatch_tick")] public int? DispatchTick { get; init; }
    [JsonPropertyName("movement_started_tick")] public int? MovementStartedTick { get; init; }
    [JsonPropertyName("path_created")] public bool PathCreated { get; init; }
    [JsonPropertyName("path_length")] public double PathLength { get; init; }
    [JsonPropertyName("waypoint_reached_tick")] public int? WaypointReachedTick { get; init; }
    [JsonPropertyName("completion_reason")] public string CompletionReason { get; init; } = string.Empty;
    [JsonPropertyName("waypoint_radius_used")] public double WaypointRadiusUsed { get; init; }
    [JsonPropertyName("destination_dwell_ticks")] public int DestinationDwellTicks { get; init; }
    [JsonPropertyName("spawn_bucket")] public string SpawnBucket { get; init; } = string.Empty;
    [JsonPropertyName("route_id")] public string RouteId { get; init; } = string.Empty;
    [JsonPropertyName("waypoint_index")] public int WaypointIndex { get; init; }
    [JsonPropertyName("current_waypoint")] public string CurrentWaypoint { get; init; } = string.Empty;
    [JsonPropertyName("next_waypoint")] public string NextWaypoint { get; init; } = string.Empty;
    [JsonPropertyName("nav_area")] public int NavArea { get; init; }
    [JsonPropertyName("nav_distance")] public double NavDistance { get; init; }
    [JsonPropertyName("path_remaining")] public double PathRemaining { get; init; }
    [JsonPropertyName("movement_command")] public string MovementCommand { get; init; } = string.Empty;
    [JsonPropertyName("intended_destination")] public string IntendedDestination { get; init; } = string.Empty;
    [JsonPropertyName("actual_position")] public float[] ActualPosition { get; init; } = Array.Empty<float>();
    [JsonPropertyName("elapsed_seconds")] public double ElapsedSeconds { get; init; }
    [JsonPropertyName("expected_travel_time")] public double ExpectedTravelTime { get; init; }
    [JsonPropertyName("actual_movement_start_delay")] public double ActualMovementStartDelay { get; init; }
    [JsonPropertyName("verified_congestion_delay")] public double VerifiedCongestionDelay { get; init; }
    [JsonPropertyName("navigation_failure_time")] public double NavigationFailureTime { get; init; }
    [JsonPropertyName("interruption_time")] public double InterruptionTime { get; init; }
    [JsonPropertyName("deadline_seconds")] public double DeadlineSeconds { get; init; }
    [JsonPropertyName("base_deadline_seconds")] public double BaseDeadlineSeconds { get; init; }
    [JsonPropertyName("planned_stagger_ms")] public int PlannedStaggerMs { get; init; }
    [JsonPropertyName("verified_congestion_allowance_seconds")] public double VerifiedCongestionAllowanceSeconds { get; init; }
    [JsonPropertyName("effective_deadline_seconds")] public double EffectiveDeadlineSeconds { get; init; }
    [JsonPropertyName("deadline_margin_seconds")] public double DeadlineMarginSeconds { get; init; }
    [JsonPropertyName("conflict_group")] public string ConflictGroup { get; init; } = string.Empty;
    [JsonPropertyName("spawn_priority")] public int SpawnPriority { get; init; }
    [JsonPropertyName("role_priority")] public int RolePriority { get; init; }
    [JsonPropertyName("planned_release_tick")] public int PlannedReleaseTick { get; init; }
    [JsonPropertyName("minimum_spacing_units")] public double MinimumSpacingUnits { get; init; }
    [JsonPropertyName("predecessor_slot")] public int? PredecessorSlot { get; init; }
    [JsonPropertyName("active_weapon")] public string ActiveWeapon { get; init; } = string.Empty;
    [JsonPropertyName("threat_line_crossed")] public bool ThreatLineCrossed { get; init; }
    [JsonPropertyName("contact")] public bool Contact { get; init; }
    [JsonPropertyName("damage")] public bool Damage { get; init; }
    [JsonPropertyName("hostile_utility")] public bool HostileUtility { get; init; }
    [JsonPropertyName("blocked_duration")] public int BlockedDuration { get; init; }
    [JsonPropertyName("blocked_duration_ms")] public int BlockedDurationMs { get; init; }
    [JsonPropertyName("blocker_slot")] public int? BlockerSlot { get; init; }
    [JsonPropertyName("distance_to_blocker")] public double? DistanceToBlocker { get; init; }
    [JsonPropertyName("progress_units")] public double ProgressUnits { get; init; }
    [JsonPropertyName("block_cause")] public string BlockCauseName { get; init; } = BlockCause.None;
    [JsonPropertyName("recovery_attempted")] public bool RecoveryAttempted { get; init; }
    [JsonPropertyName("recovery_succeeded")] public bool RecoverySucceeded { get; init; }
    [JsonPropertyName("recovery_waypoint")] public string RecoveryWaypoint { get; init; } = string.Empty;
    [JsonPropertyName("recovery_strategy")] public string RecoveryStrategy { get; init; } = "NONE";
    [JsonPropertyName("dispatch_reason")] public string DispatchReason { get; init; } = string.Empty;
    [JsonPropertyName("repath_count")] public int RepathCount { get; init; }
    [JsonPropertyName("arrival_status")] public string ArrivalStatus { get; init; } = "PENDING";
    [JsonPropertyName("fallback_reason")] public string FallbackReason { get; init; } = string.Empty;
    [JsonPropertyName("authority_return_tick")] public int? AuthorityReturnTick { get; init; }
    [JsonPropertyName("target_sector")] public string TargetSector { get; init; } = string.Empty;
    [JsonPropertyName("role")] public string Role { get; init; } = string.Empty;
    [JsonPropertyName("has_c4")] public bool HasC4 { get; init; }
    [JsonPropertyName("c4_compatible")] public bool C4Compatible { get; init; } = true;
    [JsonPropertyName("bomb_carrier_slot")] public int? BombCarrierSlot { get; init; }
    [JsonPropertyName("canary_is_bomb_carrier")] public bool CanaryIsBombCarrier { get; init; }
    [JsonPropertyName("planned_bombsite")] public string PlannedBombsite { get; init; } = string.Empty;
    [JsonPropertyName("assigned_route")] public string AssignedRoute { get; init; } = string.Empty;
    [JsonPropertyName("route_bombsite")] public string RouteBombsite { get; init; } = string.Empty;
    [JsonPropertyName("bombsite_compatible")] public bool BombsiteCompatible { get; init; } = true;
    [JsonPropertyName("bomb_path_preserved")] public bool BombPathPreserved { get; init; } = true;
    [JsonPropertyName("weapon_ready_before_contact")] public bool WeaponReadyBeforeContact { get; init; }
    [JsonPropertyName("traveled_distance")] public double TraveledDistance { get; init; }
    [JsonPropertyName("expected_distance")] public double ExpectedDistance { get; init; }
    [JsonPropertyName("lease_active")] public bool LeaseActive { get; init; }
    [JsonPropertyName("lease_owner")] public string LeaseOwner { get; init; } = "NONE";
    [JsonPropertyName("isolation_mode")] public string IsolationMode { get; init; } = "LeaseIsolated";
    [JsonPropertyName("goal_before_canary")] public float[] GoalBeforeCanary { get; init; } = Array.Empty<float>();
    [JsonPropertyName("goal_after_canary")] public float[] GoalAfterCanary { get; init; } = Array.Empty<float>();
    [JsonPropertyName("goal_end_of_tick")] public float[] GoalEndOfTick { get; init; } = Array.Empty<float>();
    [JsonPropertyName("unauthorized_overwrite")] public bool UnauthorizedOverwrite { get; init; }
    [JsonPropertyName("competing_writers_suppressed")] public int CompetingWritersSuppressed { get; init; }
    [JsonPropertyName("native_state")] public string NativeState { get; init; } = "MoveTo";
    [JsonPropertyName("velocity_xy")] public double VelocityXy { get; init; }
    [JsonPropertyName("jump_pulses_issued")] public int JumpPulsesIssued { get; init; }
    [JsonPropertyName("continuous_jump_ticks")] public int ContinuousJumpTicks { get; init; }
    [JsonPropertyName("transition_type")] public string TransitionType { get; init; } = string.Empty;
    [JsonPropertyName("transition_action")] public string TransitionAction { get; init; } = string.Empty;
    [JsonPropertyName("transition_event_type")] public string TransitionEventType { get; init; } = string.Empty;
    [JsonPropertyName("canonical_step_index")] public int CanonicalStepIndex { get; init; }
    [JsonPropertyName("canonical_step_count")] public int CanonicalStepCount { get; init; }
    [JsonPropertyName("canonical_step_name")] public string CanonicalStepName { get; init; } = string.Empty;
    [JsonPropertyName("canonical_step_role")] public string CanonicalStepRole { get; init; } = string.Empty;
    [JsonPropertyName("is_final_destination")] public bool IsFinalDestination { get; init; }
    [JsonPropertyName("expected_next_step_index")] public int ExpectedNextStepIndex { get; init; } = -1;
    [JsonPropertyName("expected_next_step_name")] public string? ExpectedNextStepName { get; init; }
    [JsonPropertyName("goal_ownership_valid")] public bool GoalOwnershipValid { get; init; } = true;
    [JsonPropertyName("portal_crossed")] public bool PortalCrossed { get; init; }
    [JsonPropertyName("current_nav_area")] public int CurrentNavArea { get; init; }
    [JsonPropertyName("expected_exit_nav_area")] public int ExpectedExitNavArea { get; init; }
    [JsonPropertyName("transition_command_count")] public int TransitionCommandCount { get; init; }
    [JsonPropertyName("departure_control_mode")] public string DepartureControlMode { get; init; } = "CANARY_CONTROLLED";
    [JsonPropertyName("inferred_corridor")] public string InferredCorridor { get; init; } = string.Empty;
    [JsonPropertyName("corridor_inference_source")] public string CorridorInferenceSource { get; init; } = string.Empty;
    [JsonPropertyName("corridor_confidence")] public string CorridorConfidence { get; init; } = string.Empty;
    [JsonPropertyName("actual_release_tick")] public int? ActualReleaseTick { get; init; }
    [JsonPropertyName("root_block_cause")] public string RootBlockCause { get; init; } = BlockCause.None;
    [JsonPropertyName("current_block_state")] public string CurrentBlockState { get; init; } = BlockCause.None;
    [JsonPropertyName("blocker_control_mode")] public string BlockerControlMode { get; init; } = string.Empty;
    [JsonPropertyName("verified_same_corridor")] public bool VerifiedSameCorridor { get; init; }
    [JsonPropertyName("final_approach_active")] public bool FinalApproachActive { get; init; }
    [JsonPropertyName("nav_distance_to_destination")] public double NavDistanceToDestination { get; init; }
    [JsonPropertyName("initial_departure_corridor")] public string InitialDepartureCorridor { get; init; } = string.Empty;
    [JsonPropertyName("downstream_conflict_group")] public string DownstreamConflictGroup { get; init; } = string.Empty;
    [JsonPropertyName("queue_id")] public string QueueId { get; init; } = string.Empty;
    [JsonPropertyName("queue_position")] public int QueuePosition { get; init; }
    [JsonPropertyName("leader_slot")] public int? LeaderSlot { get; init; }
    [JsonPropertyName("predecessor_enter_tick")] public int? PredecessorEnterTick { get; init; }
    [JsonPropertyName("predecessor_clear_tick")] public int? PredecessorClearTick { get; init; }
    [JsonPropertyName("release_condition")] public string ReleaseCondition { get; init; } = string.Empty;
    [JsonPropertyName("waiting_for_scheduled_release")] public bool WaitingForScheduledRelease { get; init; }
    [JsonPropertyName("scheduled_wait_ms")] public int ScheduledWaitMs { get; init; }
    [JsonPropertyName("runtime_congestion_ms")] public int RuntimeCongestionMs { get; init; }
}

public sealed class CanaryTickDecision
{
    public bool CanaryControlling { get; init; }
    public string Authority { get; init; } = "UTILITY_AI";
    public string ExecutorState { get; init; } = CanaryExecutorState.NotStarted;
    public int CommandId { get; init; }
    public double PathLength { get; init; }
    public RouteWaypoint? CurrentWaypoint { get; init; }
    public bool WaypointChanged { get; init; }
    public string DispatchReason { get; init; } = string.Empty;
    public bool HoldingForStagger { get; init; }
    public bool ShouldSwitchToWeapon { get; init; }
    public bool KnifeAllowed { get; init; }
    public string AbortOrCompletionReason { get; init; } = string.Empty;
    public bool ShouldEmitJumpPulse { get; init; }
    public bool ShouldEmitAttackPulse { get; init; }
    public bool UseExactPortalSteering { get; init; }
    public bool RequireCrouch { get; init; }
    public IReadOnlySet<int>? ForbiddenNavAreas { get; init; }
    public TransitionWaypointType ActiveTransitionType { get; init; } = TransitionWaypointType.FLAT_PORTAL;
    public TransitionMovementAction ActiveMovementAction { get; init; } = TransitionMovementAction.NONE;
    public string TransitionCommandEvent { get; init; } = string.Empty;
}

public sealed class ActiveCanarySession
{
    public string SessionId { get; init; } = string.Empty;
    public string AssignmentId { get; init; } = string.Empty;
    public string ControllerId { get; init; } = string.Empty;
    public string LeaseId { get; init; } = string.Empty;
    public bool StartedEventEmitted { get; set; }
    public bool TerminalEventEmitted { get; set; }
    public int SessionCreatedTick { get; init; }
    public int ControllerCreatedTick { get; init; }
    public int LeaseAcquiredTick { get; init; }
    public int SessionStartedTick { get; init; }
    public int RoundId { get; init; }
    public int RawSlot { get; init; }
    public string PlayerPseudonym { get; init; } = string.Empty;
    public string Team { get; init; } = string.Empty;
    public string Role { get; init; } = string.Empty;
    public string OriginalDestination { get; init; } = string.Empty;
    public string OriginalSector { get; init; } = string.Empty;
    public OpeningRouteSuggestion Route { get; init; } = new();
    public int StartTick { get; init; }
    public int WaypointIndex { get; set; }
    public int LastDispatchedWaypointIndex { get; set; } = -1;
    public string Authority { get; set; } = "OPENING_ROUTE_PLANNER";
    public string ExecutorState { get; set; } = CanaryExecutorState.NotStarted;
    public int CommandId { get; set; }
    public int? DispatchTick { get; set; }
    public int? MovementStartedTick { get; set; }
    public bool PathCreated { get; set; }
    public double CurrentPathLength { get; set; }
    public int? WaypointReachedTick { get; set; }
    public string CompletionReason { get; set; } = string.Empty;
    public int DestinationDwellTicks { get; set; }
    public bool ThreatLineCrossed { get; set; }
    public bool WeaponReadyConfirmed { get; set; }
    public bool HadWeaponReadyOnce { get; set; }
    public int PostReadyKnifeTicks { get; set; }
    public int? BombCarrierSlot { get; set; }
    public bool CanaryIsBombCarrier { get; set; }
    public string PlannedBombsite { get; set; } = string.Empty;
    public string RouteBombsite { get; set; } = string.Empty;
    public bool BombsiteCompatible { get; set; } = true;
    public bool BombPathPreserved { get; set; } = true;
    public bool PendingDamage { get; set; }
    public bool PendingHostileUtility { get; set; }
    public int BlockedDurationMs { get; set; }
    public double NavigationFailureSeconds { get; set; }
    public int RepathCount { get; set; }
    public float LastX { get; set; }
    public float LastY { get; set; }
    public float LastZ { get; set; }
    public double LastDistToWaypoint { get; set; } = double.MaxValue;
    public int LastTrackedWaypointIndex { get; set; } = -1;
    public double TraveledDistance { get; set; }
    public string ArrivalStatus { get; set; } = "PENDING";
    public string FallbackReason { get; set; } = string.Empty;
    public int? AuthorityReturnTick { get; set; }
    public StaggerScheduleEntry Schedule { get; init; } = new(1, 1, string.Empty, 0, 0, 160.0, null);
    public double VerifiedCongestionAllowanceSeconds { get; set; }
    public int? LastBlockerSlot { get; set; }
    public double? LastDistanceToBlocker { get; set; }
    public double LastProgressUnits { get; set; }
    public string LastBlockCause { get; set; } = BlockCause.None;
    public bool RecoveryAttempted { get; set; }
    public bool RecoveryActive { get; set; }
    public bool RecoverySucceeded { get; set; }
    public RouteWaypoint? RecoveryWaypoint { get; set; }
    public string RecoveryStrategy { get; set; } = "NONE";
    public bool RecoveryDispatched { get; set; }
    public int RecoveryStartTick { get; set; }
    public float[] LastGoalBefore { get; set; } = Array.Empty<float>();
    public float[] LastGoalAfter { get; set; } = Array.Empty<float>();
    public float[] LastGoalEndOfTick { get; set; } = Array.Empty<float>();
    public string LastNativeState { get; set; } = "MoveTo";
    public bool LastUnauthorizedOverwrite { get; set; }
    public double LastSpeed2D { get; set; }
    public GeometricTransitionExecutor TransitionExecutor { get; } = new();
    public TransitionStepEvaluation? LastTransitionStep { get; set; }
    public string RootBlockCause { get; set; } = BlockCause.None;
    public string CurrentBlockState { get; set; } = BlockCause.None;
    public int? RootBlockTick { get; set; }
    public int? RootBlockerSlot { get; set; }
    public string RootBlockerControlMode { get; set; } = string.Empty;
    public bool VerifiedSameCorridor { get; set; }
    public int? ActualReleaseTick { get; set; }
    public string InferredCorridor { get; set; } = string.Empty;
    public string CorridorInferenceSource { get; set; } = string.Empty;
    public string CorridorConfidenceName { get; set; } = string.Empty;
    public bool FinalApproachActive { get; set; }
    public double LastNavDistanceToDestination { get; set; }
    public bool QueueResumedPending { get; set; }
    public string InitialDepartureCorridor { get; set; } = string.Empty;
    public string DownstreamConflictGroup { get; set; } = string.Empty;
    public string QueueId { get; set; } = string.Empty;
    public int QueuePosition { get; set; }
    public int? LeaderSlot { get; set; }
    public int? PredecessorEnterTick { get; set; }
    public int? PredecessorClearTick { get; set; }
    public string ReleaseCondition { get; set; } = string.Empty;
    public bool WaitingForScheduledRelease { get; set; }
    public int ScheduledWaitMs { get; set; }
    public int RuntimeCongestionMs { get; set; }
    public double EffectiveDeadlineSeconds =>
        Route.DeadlineSeconds + (Schedule.PlannedStaggerMs / 1000.0) + Math.Min(1.500, VerifiedCongestionAllowanceSeconds);
    public bool IsFinished => Authority != "OPENING_ROUTE_PLANNER";
}

public sealed record VerifiedBlockerResult
{
    public bool IsVerified { get; init; }
    public int? BlockerSlot { get; init; }
    public string BlockerControlMode { get; init; } = string.Empty;
    public bool SameCorridor { get; init; }
    public bool IsAhead { get; init; }
    public double? Distance { get; init; }
    public float BlockerX { get; init; }
    public float BlockerY { get; init; }
    public bool PortalOccupied { get; init; }
    public string Confidence { get; init; } = "LOW";
    public string Reason { get; init; } = "NONE";
}

public static class OpeningRouteCanaryAllowlist
{
    public static readonly HashSet<string> CtAllowedSpots = new(StringComparer.OrdinalIgnoreCase)
    {
        "a_firebox_ninja_hold",
        "a_triple_box_hold",
        "a_shadow_under_palace",
        "ct_a_sand_pit_under_palace_hold_caverna",
        "a_tetris_corner_ramp_palace",
        "b_van_behind_apps_hold",
        "b_forest_bench_hold_apps",
        "b_short_pillar_hold_apps",
        "b_short_pillar_bomb_control",
        "b_site_default_plant_box",
        "ct_b_edward_under_apps",
        "ct_b_empty_pillar_jail",
        "mid_window_right_deep",
        "mid_connector_bottom",
        "mid_catwalk_short",
        "mid_underground_sub",
        "mid_chair_delpan_hold",
        "mid_ladder_room_control",
        "ct_b_short_arch_hold_mid",
    };

    public static readonly HashSet<string> TrAllowedSpots = new(StringComparer.OrdinalIgnoreCase)
    {
        "tr_a_ramp_staging_wait",
        "a_palace_deep_room",
        "a_palace_balcony_tr",
        "a_tetris_corner_ramp_palace",
        "a_tetris_top_control",
        "a_default_plant_headshot",
        "mid_top_mid_boxes",
        "mid_catwalk_short",
        "mid_underground_sub",
        "mid_connector_bottom",
        "mid_chair_delpan_hold",
        "tr_b_apps_house_staging",
        "tr_b_tapete_window_market_awp",
        "tr_b_tapete_window_bomb_curve",
        "b_site_default_plant_box",
        "b_van_behind_bomb_hold",
        "tr_b_forest_hold_short",
        "tr_b_forest_hold_market",
    };

    public static bool IsAllowlisted(string team, string spotId)
    {
        if (string.IsNullOrWhiteSpace(spotId)) return false;
        string t = (team.Equals("T", StringComparison.OrdinalIgnoreCase) || team.Equals("TR", StringComparison.OrdinalIgnoreCase)) ? "T" : "CT";
        return t == "CT" ? CtAllowedSpots.Contains(spotId) : TrAllowedSpots.Contains(spotId);
    }
}

public sealed class OpeningRouteCanaryGuard
{
    public CanaryTeamMode Mode { get; private set; }
    public double WaypointRadiusUnits { get; }
    public double DestinationRadiusUnits { get; }
    public int DestinationDwellMinTicks { get; }
    public bool LateralRecoveryEnabled { get; }
    public NavMeshGraph? NavMesh { get; }
    public MovementAuthorityLeaseManager LeaseManager { get; } = new();
    public Action<ActiveCanarySession, string, int>? OnSessionTerminal { get; set; }

    private readonly OpeningRoutePlanner _planner = new();
    private readonly Dictionary<int, ActiveCanarySession> _sessionsByRound = new();
    private readonly Dictionary<(int RoundId, int BotSlot), ActiveCanarySession> _sessionsByRoundAndSlot = new();
    private readonly List<CanaryTelemetryRecord> _records = new();
    private readonly Dictionary<int, NoEligibleCanaryRecord> _noEligibleRounds = new();

    public OpeningRouteCanaryGuard(
        CanaryTeamMode? mode = null,
        NavMeshGraph? navMesh = null,
        double waypointRadius = 110.0,
        double destinationRadius = 135.0,
        int destinationDwellMinTicks = 2,
        bool enableLegacyLateralRecovery = false)
    {
        Mode = mode ?? ParseEnvMode();
        NavMesh = navMesh ?? NavMeshGraph.Default;
        WaypointRadiusUnits = Math.Clamp(waypointRadius, 32.0, 128.0);
        DestinationRadiusUnits = Math.Clamp(destinationRadius, 64.0, 200.0);
        DestinationDwellMinTicks = Math.Max(1, destinationDwellMinTicks);
        string? maxLeasesEnv = Environment.GetEnvironmentVariable("CSBOT_TEAM_MAX_LEASES");
        if (int.TryParse(maxLeasesEnv, out int parsedMax) && parsedMax > 1)
        {
            LeaseManager.MaxConcurrentLeases = Math.Clamp(parsedMax, 1, 10);
        }
        if (int.TryParse(Environment.GetEnvironmentVariable("CSBOT_TEAM_MAX_CT_LEASES"), out int ctMax) && ctMax > 0)
        {
            MaxConcurrentCtLeases = ctMax;
        }
        if (int.TryParse(Environment.GetEnvironmentVariable("CSBOT_TEAM_MAX_TR_LEASES"), out int trMax) && trMax > 0)
        {
            MaxConcurrentTrLeases = trMax;
        }
        if (int.TryParse(Environment.GetEnvironmentVariable("CSBOT_TEAM_MAX_TOTAL_LEASES"), out int totMax) && totMax > 0)
        {
            MaxConcurrentTotalLeases = totMax;
        }
        LeaseManager.MaxConcurrentCtLeases = MaxConcurrentCtLeases;
        LeaseManager.MaxConcurrentTrLeases = MaxConcurrentTrLeases;
        LeaseManager.MaxConcurrentTotalLeases = MaxConcurrentTotalLeases;
        if (Mode == CanaryTeamMode.Combined)
        {
            LeaseManager.MaxConcurrentLeases = Math.Max(LeaseManager.MaxConcurrentLeases, MaxConcurrentTotalLeases);
        }
        LateralRecoveryEnabled = enableLegacyLateralRecovery;
    }

    public IReadOnlyList<CanaryTelemetryRecord> Records => _records;
    public IReadOnlyDictionary<int, NoEligibleCanaryRecord> NoEligibleRounds => _noEligibleRounds;

    public void RecordNoEligibleRound(int roundId, string team, int candidatesChecked)
    {
        if (_sessionsByRound.ContainsKey(roundId) || _noEligibleRounds.ContainsKey(roundId))
        {
            return;
        }
        string normTeam = (team.Equals("T", StringComparison.OrdinalIgnoreCase) || team.Equals("TR", StringComparison.OrdinalIgnoreCase)) ? "T" : "CT";
        _noEligibleRounds[roundId] = new NoEligibleCanaryRecord
        {
            Round = roundId,
            Team = normTeam,
            Reason = normTeam == "CT" ? "NO_ELIGIBLE_CT_CANARY" : "NO_ELIGIBLE_TR_CANARY",
            CandidatesChecked = candidatesChecked,
        };
    }

    public static int GetRolePriority(string role)
    {
        string r = (role ?? string.Empty).Trim().ToUpperInvariant();
        return r switch
        {
            "ENTRY" or "AWPER" or "MIDCONTROL" or "MID_CONTROL" => 1,
            "ROTATOR" => 2,
            "ANCHOR" => 3,
            "SUPPORT" or "LURKER" => 4,
            _ => 3,
        };
    }

    public static double GetCorridorWidthFactor(string conflictGroup)
    {
        return (conflictGroup ?? string.Empty).ToUpperInvariant() switch
        {
            "WINDOW_ENTRY" or "PALACE_ENTRY" or "MARKET_ENTRY" => 1.25,
            "CONNECTOR_ENTRY" or "A_RAMP_ENTRY" => 1.15,
            _ => 1.0,
        };
    }

    public static StaggerScheduleEntry ComputeStaggerSchedule(
        int rawSlot,
        string role,
        OpeningRouteSuggestion route,
        float startX, float startY, float startZ,
        int startTick,
        IReadOnlyList<TeammatePositionSnapshot>? teammates,
        int? explicitStaggerMs = null)
    {
        string cg = route.ConflictGroup ?? string.Empty;
        int rolePriority = GetRolePriority(role);
        double minSpacing = cg.Contains("MARKET", StringComparison.OrdinalIgnoreCase) || cg.Contains("WINDOW", StringComparison.OrdinalIgnoreCase)
            ? 175.0
            : 155.0;

        if (explicitStaggerMs.HasValue)
        {
            int clampedExplicit = Math.Max(0, explicitStaggerMs.Value);
            int relTick = startTick + (int)Math.Round(clampedExplicit / 1000.0 * 64.0);
            return new StaggerScheduleEntry(1, rolePriority, cg, clampedExplicit, relTick, minSpacing, null);
        }

        if (teammates == null || teammates.Count == 0 || route.OrderedWaypoints.Count == 0)
        {
            return new StaggerScheduleEntry(1, rolePriority, cg, 0, startTick, minSpacing, null);
        }

        var entryWp = route.OrderedWaypoints[0];
        double selfDistToEntry = Dist3(startX, startY, startZ, entryWp.X, entryWp.Y, entryWp.Z);

        int aheadCount = 0;
        int? closestPredSlot = null;
        double closestPredDist = double.MaxValue;

        foreach (var tm in teammates)
        {
            if (tm.RawSlot == rawSlot) continue;
            bool sameGroup = string.IsNullOrEmpty(tm.ConflictGroup) || string.Equals(tm.ConflictGroup, cg, StringComparison.OrdinalIgnoreCase);
            if (!sameGroup) continue;

            double distBetween = Dist3(tm.X, tm.Y, tm.Z, startX, startY, startZ);
            double tmDistToEntry = Dist3(tm.X, tm.Y, tm.Z, entryWp.X, entryWp.Y, entryWp.Z);
            bool tmIsAhead = tmDistToEntry + 10.0 < selfDistToEntry || (Math.Abs(tmDistToEntry - selfDistToEntry) <= 10.0 && tm.RawSlot < rawSlot);

            if (tmIsAhead && distBetween <= minSpacing * 1.45)
            {
                aheadCount++;
                if (distBetween < closestPredDist)
                {
                    closestPredDist = distBetween;
                    closestPredSlot = tm.RawSlot;
                }
            }
        }

        int spawnPriority = aheadCount + 1;
        int plannedStaggerMs = 0;
        if (aheadCount > 0)
        {
            double widthFactor = GetCorridorWidthFactor(cg);
            double proximityRatio = Math.Clamp(1.0 - (closestPredDist / (minSpacing * 1.5)), 0.0, 1.0);
            int baseMs = (int)Math.Round((100.0 + 110.0 * proximityRatio) * widthFactor + (aheadCount - 1) * 35.0);
            plannedStaggerMs = Math.Clamp(baseMs, 100, 250);
        }

        int releaseTick = startTick + (int)Math.Round(plannedStaggerMs / 1000.0 * 64.0);
        return new StaggerScheduleEntry(spawnPriority, rolePriority, cg, plannedStaggerMs, releaseTick, minSpacing, closestPredSlot);
    }

    public void SetMode(CanaryTeamMode mode) => Mode = mode;

    private static readonly HashSet<string> CombatReadyWeapons = new(StringComparer.OrdinalIgnoreCase)
    {
        "weapon_hkp2000", "weapon_usp_silencer", "weapon_glock", "weapon_famas",
        "weapon_m4a1", "weapon_m4a1_silencer", "weapon_ak47", "weapon_galilar",
        "weapon_mac10", "weapon_mp9", "weapon_awp", "weapon_ssg08",
        "weapon_deagle", "weapon_p250", "weapon_fiveseven", "weapon_tec9",
        "weapon_elite", "weapon_cz75a", "weapon_mp7", "weapon_mp5sd",
        "weapon_ump45", "weapon_p90", "weapon_bizon", "weapon_aug", "weapon_sg556",
        "weapon_scar20", "weapon_g3sg1", "weapon_nova", "weapon_xm1014", "weapon_mag7",
        "weapon_sawedoff", "weapon_m249", "weapon_negev", "weapon_revolver",
    };

    public static bool IsCombatReadyWeapon(string? weaponName)
    {
        if (string.IsNullOrWhiteSpace(weaponName)) return false;
        return CombatReadyWeapons.Contains(weaponName.Trim());
    }

    public static CanaryTeamMode ParseEnvMode()
    {
        string raw = (Environment.GetEnvironmentVariable("CSBOT_OPENING_CANARY_MODE") ?? "OFF").Trim().ToUpperInvariant();
        var parsed = raw switch
        {
            "OFF" => CanaryTeamMode.Off,
            "CT" or "CT_SINGLE" => CanaryTeamMode.CtSingle,
            "TR" or "T" or "TR_SINGLE" => CanaryTeamMode.TrSingle,
            "COMBINED" => CanaryTeamMode.Combined,
            _ => CanaryTeamMode.Off,
        };
        if (parsed == CanaryTeamMode.Off && raw != "OFF")
        {
            Console.WriteLine($"[CsBotManager] INVALID_CANARY_TEAM_MODE requested={raw} parsed={parsed}");
        }
        else
        {
            Console.WriteLine($"[CsBotManager] CANARY_MODE_PARSED requested={raw} parsed={parsed}");
        }
        Console.WriteLine($"[CANARY_RUNTIME_MODE] {{\"requested_mode\":\"{raw}\",\"parsed_mode\":\"{parsed}\"}}");
        return parsed;
    }

    public ActiveCanarySession? GetSessionForRound(int roundId) =>
        _sessionsByRound.TryGetValue(roundId, out var s) ? s : null;

    public ActiveCanarySession? GetSessionForSlot(int roundId, int rawSlot) =>
        _sessionsByRoundAndSlot.TryGetValue((roundId, rawSlot), out var s) ? s : null;

    private readonly HashSet<(int RoundId, string Team)> _startedTeamRounds = new();
    public int MaxConcurrentCtLeases { get; set; } = 5;
    public int MaxConcurrentTrLeases { get; set; } = 5;
    public int MaxConcurrentTotalLeases { get; set; } = 10;

    public static bool IsTeamEnabledForCanary(CanaryTeamMode mode, string team)
    {
        string t = (team ?? string.Empty).Trim().ToUpperInvariant();
        return mode switch
        {
            CanaryTeamMode.CtSingle => t == "CT",
            CanaryTeamMode.TrSingle => t == "TR" || t == "T",
            CanaryTeamMode.Combined => t == "CT" || t == "TR" || t == "T",
            _ => false,
        };
    }

    public bool HasStartedTeamRound(int roundId, string team)
    {
        string t = (team ?? string.Empty).Trim().ToUpperInvariant();
        if (t == "T") t = "TR";
        return _startedTeamRounds.Contains((roundId, t)) ||
               _sessionsByRoundAndSlot.Any(kv => kv.Key.RoundId == roundId && string.Equals(kv.Value.Team, t, StringComparison.OrdinalIgnoreCase));
    }

    public void MarkTeamRoundStarted(int roundId, string team)
    {
        string t = (team ?? string.Empty).Trim().ToUpperInvariant();
        if (t == "T") t = "TR";
        _startedTeamRounds.Add((roundId, t));
    }

    public IReadOnlyList<ActiveCanarySession> GetSessionsForRoundAndTeam(int roundId, string team)
    {
        string t = (team ?? string.Empty).Trim().ToUpperInvariant();
        if (t == "T") t = "TR";
        return _sessionsByRoundAndSlot
            .Where(kv => kv.Key.RoundId == roundId && string.Equals(kv.Value.Team, t, StringComparison.OrdinalIgnoreCase))
            .Select(kv => kv.Value)
            .ToList();
    }

    public IReadOnlyList<ActiveCanarySession> GetSessionsForRound(int roundId) =>
        _sessionsByRoundAndSlot.Where(kv => kv.Key.RoundId == roundId).Select(kv => kv.Value).ToList();

    public bool HasStartedRound(int roundId) =>
        _sessionsByRoundAndSlot.Keys.Any(k => k.RoundId == roundId) || _sessionsByRound.ContainsKey(roundId);

    public bool IsSlotActiveCanary(int roundId, int rawSlot) =>
        _sessionsByRoundAndSlot.TryGetValue((roundId, rawSlot), out var s) && !s.IsFinished;

    public static string GetRouteBombsite(string spotId, string sector = "")
    {
        string id = (spotId ?? string.Empty).ToLowerInvariant();
        string sec = (sector ?? string.Empty).ToLowerInvariant();
        if (id.StartsWith("a_") || id.Contains("_a_") || id.Contains("palace") || id.Contains("tetris") ||
            sec.Contains("bombsite a") || sec.Contains("rampa a") || sec.Contains("palácio a"))
        {
            return "A";
        }
        if (id.StartsWith("b_") || id.Contains("_b_") || id.Contains("apps") || id.Contains("kitchen") ||
            id.Contains("tapete") || id.Contains("forest") || sec.Contains("bombsite b") ||
            sec.Contains("apartamentos b") || sec.Contains("mercado b"))
        {
            return "B";
        }
        return "MID";
    }

    public static bool IsC4Compatible(string spotId, string planTargetBombsite, string role = "")
    {
        if (!string.IsNullOrWhiteSpace(role) && role.Trim().Equals("Lurker", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }
        if (string.IsNullOrWhiteSpace(planTargetBombsite) ||
            planTargetBombsite.Equals("None", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }
        string site = planTargetBombsite.Trim().ToUpperInvariant();
        string id = (spotId ?? string.Empty).ToLowerInvariant();
        if (site == "A") return !id.Contains("_b_") && !id.StartsWith("b_") && !id.Contains("apps") && !id.Contains("kitchen") && !id.Contains("tapete") && !id.Contains("catwalk");
        if (site == "B") return !id.Contains("_a_") && !id.StartsWith("a_") && !id.Contains("palace") && !id.Contains("tetris") && !id.Contains("connector");
        return true;
    }

    public bool ValidateRouteWaypointsOnNavMesh(
        OpeningRouteSuggestion suggestion,
        out List<RouteWaypoint> validatedWaypoints,
        out string reason)
    {
        validatedWaypoints = new List<RouteWaypoint>(suggestion.OrderedWaypoints.Count);
        reason = "OK";
        if (suggestion.OrderedWaypoints.Count == 0)
        {
            reason = "EMPTY_WAYPOINTS";
            return false;
        }
        if (NavMesh == null)
        {
            validatedWaypoints.AddRange(suggestion.OrderedWaypoints);
            return true;
        }

        var forbiddenAreas = GeometricTransitionCatalog.GetForbiddenNavAreasForCorridor(suggestion.AllowedCorridor);
        bool hasTransitions = suggestion.TransitionWaypoints.Count == suggestion.OrderedWaypoints.Count;
        int? prevArea = null;
        for (int i = 0; i < suggestion.OrderedWaypoints.Count; i++)
        {
            var wp = suggestion.OrderedWaypoints[i];
            if (float.IsNaN(wp.X) || float.IsNaN(wp.Y) || float.IsNaN(wp.Z))
            {
                reason = "NAN_WAYPOINT";
                return false;
            }

            bool isUnreachableFinalUpper = hasTransitions &&
                                           i == suggestion.OrderedWaypoints.Count - 1 &&
                                           !suggestion.TransitionWaypoints[i].IsFinalApproachReachable;
            var proj = NavMesh.ProjectPoint(wp.X, wp.Y, wp.Z, maxSnapUnits: 32f);
            if (proj.AreaId <= 0)
            {
                reason = $"UNPROJECTABLE_WAYPOINT:{wp.Name}";
                return false;
            }
            if (prevArea.HasValue && !isUnreachableFinalUpper)
            {
                var (connected, _, _) = NavMesh.FindShortestAreaPath(prevArea.Value, proj.AreaId, forbiddenAreas);
                if (!connected)
                {
                    reason = $"DISCONNECTED_NAVMESH_SEGMENT:{wp.Name}";
                    return false;
                }
            }
            if (!isUnreachableFinalUpper)
            {
                prevArea = proj.AreaId;
            }
            validatedWaypoints.Add(proj.DeltaUnits <= 32f
                ? wp
                : new RouteWaypoint { Name = wp.Name, X = proj.ProjectedX, Y = proj.ProjectedY, Z = proj.ProjectedZ });
        }

        return true;
    }

    public bool TryStartCanaryForRound(
        int roundId,
        int rawSlot,
        string playerPseudonym,
        string team,
        string role,
        string targetSpotId,
        string spotSector,
        float startX, float startY, float startZ,
        float targetX, float targetY, float targetZ,
        int tick,
        bool isOpeningPhase,
        bool isBombPlanted,
        bool hasC4 = false,
        string planTargetBombsite = "",
        IReadOnlyList<TeammatePositionSnapshot>? teammates = null,
        int? explicitStaggerMs = null,
        int? bombCarrierSlot = null)
    {
        if (Mode == CanaryTeamMode.Off) return false;
        if (!LeaseManager.IsCanaryEnabled() || LeaseManager.GetIsolationMode() == CanaryIsolationMode.CanaryDisabled) return false;

        string normTeam = (team.Equals("T", StringComparison.OrdinalIgnoreCase) || team.Equals("TR", StringComparison.OrdinalIgnoreCase)) ? "T" : "CT";
        if (Mode == CanaryTeamMode.CtSingle && normTeam != "CT") return false;
        if (Mode == CanaryTeamMode.TrSingle && normTeam != "T") return false;

        if (_sessionsByRoundAndSlot.ContainsKey((roundId, rawSlot))) return false;
        if (GetSessionsForRound(roundId).Count >= LeaseManager.MaxConcurrentLeases) return false;
        if (!isOpeningPhase || isBombPlanted) return false;
        if (!OpeningRouteCanaryAllowlist.IsAllowlisted(normTeam, targetSpotId)) return false;
        if (normTeam == "T" && EvaluatePlanRouteCompatibility(targetSpotId, planTargetBombsite, role, hasC4) == "PLAN_ROUTE_MISMATCH") return false;

        if (float.IsNaN(startX) || float.IsNaN(startY) || float.IsNaN(startZ) ||
            float.IsNaN(targetX) || float.IsNaN(targetY) || float.IsNaN(targetZ))
        {
            return false;
        }

        if (!_planner.TryPlanOpeningRouteForRound(
                roundId, rawSlot, playerPseudonym, normTeam, role,
                targetSpotId, spotSector, startX, startY, startZ,
                targetX, targetY, targetZ, tick, out var suggestion) || suggestion == null)
        {
            return false;
        }

        if (suggestion.CanonicalSteps.Count > 0)
        {
            CanonicalRouteValidator.ProjectCanonicalStepsInPlace(suggestion.CanonicalSteps, NavMesh);
            var (canonValid, _) = CanonicalRouteValidator.Validate(
                suggestion.CanonicalSteps, targetSpotId, targetX, targetY, targetZ, NavMesh);
            if (!canonValid)
            {
                return false;
            }
            suggestion.OrderedWaypoints.Clear();
            suggestion.OrderedWaypoints.AddRange(suggestion.CanonicalSteps.Select(cs => cs.ToRouteWaypoint()));
            suggestion.TransitionWaypoints.Clear();
            suggestion.TransitionWaypoints.AddRange(suggestion.CanonicalSteps.Select(cs => cs.ToTransitionWaypoint()));
        }
        else
        {
            if (!ValidateRouteWaypointsOnNavMesh(suggestion, out var validatedWps, out _))
            {
                return false;
            }
            suggestion.OrderedWaypoints.Clear();
            suggestion.OrderedWaypoints.AddRange(validatedWps);
        }

        var schedule = ComputeStaggerSchedule(rawSlot, role, suggestion, startX, startY, startZ, tick, teammates, explicitStaggerMs);
        if (schedule.PlannedStaggerMs > 500)
        {
            return false;
        }

        _noEligibleRounds.Remove(roundId);
        var (initDist, initValid) = ComputeNavDistance(startX, startY, startZ, suggestion.OrderedWaypoints[0]);

        string assignTeam = normTeam == "T" ? "TR" : normTeam;
        var session = new ActiveCanarySession
        {
            RoundId = roundId,
            SessionId = $"r{roundId}_{normTeam}_s{rawSlot}_{tick}",
            AssignmentId = $"r{roundId}_{assignTeam}_s{rawSlot}",
            ControllerId = $"ctrl_{normTeam}_{rawSlot}_r{roundId}",
            LeaseId = $"lease_{normTeam}_{rawSlot}_r{roundId}_{tick}",
            RawSlot = rawSlot,
            PlayerPseudonym = playerPseudonym,
            Team = normTeam,
            Role = role,
            OriginalDestination = targetSpotId,
            OriginalSector = suggestion.TargetSector,
            Route = suggestion,
            StartTick = tick,
            SessionCreatedTick = tick,
            ControllerCreatedTick = tick,
            LeaseAcquiredTick = tick,
            SessionStartedTick = tick,
            WaypointIndex = 0,
            Authority = "OPENING_ROUTE_PLANNER",
            ExecutorState = CanaryExecutorState.NotStarted,
            PathCreated = initValid,
            CurrentPathLength = initDist,
            LastX = startX,
            LastY = startY,
            LastZ = startZ,
            LastDistToWaypoint = initDist,
            LastTrackedWaypointIndex = 0,
            Schedule = schedule,
            BombCarrierSlot = bombCarrierSlot ?? (hasC4 ? rawSlot : null),
            CanaryIsBombCarrier = hasC4,
            PlannedBombsite = string.IsNullOrWhiteSpace(planTargetBombsite) ? "None" : planTargetBombsite,
            RouteBombsite = GetRouteBombsite(targetSpotId, suggestion.TargetSector),
            BombsiteCompatible = !hasC4 || IsC4Compatible(targetSpotId, planTargetBombsite, role),
            BombPathPreserved = true,
        };

        int maxLeaseTicks = (int)Math.Ceiling(session.EffectiveDeadlineSeconds * 1.5 * 64.0) + 16;
        if (!LeaseManager.TryAcquireLease(
                roundId, rawSlot, playerPseudonym, normTeam, suggestion.RouteId,
                tick, maxLeaseTicks, isOpeningPhase, Mode, originalState: null, out _, out _))
        {
            return false;
        }

        session.StartedEventEmitted = true;
        _records.Add(new CanaryTelemetryRecord
        {
            Round = roundId,
            SessionId = session.SessionId,
            ControllerId = session.ControllerId,
            LeaseId = session.LeaseId,
            EventType = "CANARY_SESSION_STARTED",
            PlayerPseudonym = playerPseudonym,
            Team = normTeam,
            CanaryEnabled = true,
            Authority = session.Authority,
            ExecutorState = session.ExecutorState,
            RouteId = suggestion.RouteId,
            IntendedDestination = targetSpotId,
            ActualPosition = new[] { startX, startY, startZ },
            DispatchTick = tick,
            LeaseActive = true,
            LeaseOwner = "OPENING_ROUTE_PLANNER",
            IsolationMode = LeaseManager.GetIsolationMode().ToString(),
        });

        _sessionsByRound.TryAdd(roundId, session);
        _sessionsByRoundAndSlot[(roundId, rawSlot)] = session;
        return true;
    }

    public void NotifyPlayerDamage(int roundId, int rawSlot, int tick, bool isHostileUtility = false)
    {
        if (_sessionsByRoundAndSlot.TryGetValue((roundId, rawSlot), out var s) && !s.IsFinished)
        {
            s.PendingDamage = true;
            if (isHostileUtility) s.PendingHostileUtility = true;
            s.ExecutorState = CanaryExecutorState.Interrupted;
            s.CompletionReason = isHostileUtility ? "HOSTILE_UTILITY" : "DAMAGE_INTERRUPTION";
            AbortSession(s, s.CompletionReason, "CONTACT_INTERRUPTION", tick);
        }
    }

    public void NotifyUtilityCancel(int roundId, int rawSlot, int tick, string reason = "UTILITY_CANCELLED")
    {
        if (_sessionsByRoundAndSlot.TryGetValue((roundId, rawSlot), out var s) && !s.IsFinished)
        {
            s.ExecutorState = CanaryExecutorState.Interrupted;
            s.CompletionReason = reason;
            AbortSession(s, reason, "TACTICAL_REDIRECT", tick);
        }
    }

    public static string EvaluatePlanRouteCompatibility(
        string spotId, string planTargetBombsite, string role, bool isBombCarrier)
    {
        if (!string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("CSBOT_TR_SOLO_CERT_ROUTE")))
        {
            return isBombCarrier ? "C4_CARRIER_COMPATIBLE" : "NON_CARRIER_SECONDARY_ROUTE_COMPATIBLE";
        }
        string routeSite = GetRouteBombsite(spotId);
        string planned = (planTargetBombsite ?? string.Empty).Trim().ToUpperInvariant();
        string normRole = (role ?? string.Empty).Trim().ToUpperInvariant();
        if (isBombCarrier)
        {
            return IsC4Compatible(spotId, planned, normRole)
                ? "C4_CARRIER_COMPATIBLE"
                : "PLAN_ROUTE_MISMATCH";
        }
        if (string.IsNullOrEmpty(planned) ||
            string.Equals(routeSite, planned, StringComparison.OrdinalIgnoreCase) ||
            string.Equals(routeSite, "MID", StringComparison.OrdinalIgnoreCase) ||
            normRole.Contains("LURK", StringComparison.Ordinal) ||
            normRole.Contains("FAKE", StringComparison.Ordinal))
        {
            return "NON_CARRIER_SECONDARY_ROUTE_COMPATIBLE";
        }
        return "PLAN_ROUTE_MISMATCH";
    }

    public bool FinalizeActiveSession(int roundId, string reason, int tick = 0)
    {
        bool any = false;
        string finalReason = string.IsNullOrWhiteSpace(reason) ? "CAPTURE_ENDED" : reason;
        foreach (var s in GetSessionsForRound(roundId))
        {
            if (s.IsFinished) continue;
            s.ExecutorState = CanaryExecutorState.Fallback;
            AbortSession(s, finalReason, finalReason, tick);
            RecordTick(s, tick, s.LastX, s.LastY, s.LastZ, Math.Max(0.0, (tick - s.StartTick) / 64.0), string.Empty, false, false, false, s.CanaryIsBombCarrier, s.BombsiteCompatible, finalReason);
            any = true;
        }
        return any;
    }

    public int FinalizeAllOpenSessions(string reason, int tick = 0)
    {
        int closed = 0;
        string finalReason = string.IsNullOrWhiteSpace(reason) ? "CAPTURE_ENDED" : reason;
        foreach (var kv in _sessionsByRoundAndSlot.ToList())
        {
            if (!kv.Value.IsFinished)
            {
                kv.Value.ExecutorState = CanaryExecutorState.Fallback;
                AbortSession(kv.Value, finalReason, finalReason, tick);
                RecordTick(kv.Value, tick, kv.Value.LastX, kv.Value.LastY, kv.Value.LastZ, Math.Max(0.0, (tick - kv.Value.StartTick) / 64.0), string.Empty, false, false, false, kv.Value.CanaryIsBombCarrier, kv.Value.BombsiteCompatible, finalReason);
                closed++;
            }
        }
        return closed;
    }

    private (double Distance, bool ValidNavPath) ComputeNavDistance(
        float x, float y, float z, RouteWaypoint wp, IReadOnlySet<int>? forbiddenAreas = null)
    {
        if (float.IsNaN(x) || float.IsNaN(y) || float.IsNaN(z) || float.IsNaN(wp.X) || float.IsNaN(wp.Y) || float.IsNaN(wp.Z))
        {
            return (double.PositiveInfinity, false);
        }

        double euclid = Dist3(x, y, z, wp.X, wp.Y, wp.Z);
        if (NavMesh != null)
        {
            double? navDist = NavMesh.GetNavDistance(x, y, z, wp.X, wp.Y, wp.Z, maxSnapUnits: 120f, forbiddenAreas: forbiddenAreas);
            if (navDist.HasValue)
            {
                double eff = Math.Abs(z - wp.Z) <= 96f ? Math.Min(navDist.Value, euclid) : navDist.Value;
                return (eff, true);
            }
            return (euclid, false);
        }

        return (euclid, Math.Abs(z - wp.Z) <= 260f);
    }

    private RouteWaypoint ProjectRecoveryWaypoint(RouteWaypoint wp)
    {
        if (NavMesh == null) return wp;
        var p = NavMesh.ProjectPoint(wp.X, wp.Y, wp.Z, maxSnapUnits: 64f);
        if (p.AreaId > 0)
        {
            return new RouteWaypoint { Name = wp.Name, X = p.ProjectedX, Y = p.ProjectedY, Z = p.ProjectedZ };
        }
        return wp;
    }

    public CanaryTickDecision EvaluateTick(
        int roundId,
        int rawSlot,
        int tick,
        float x, float y, float z,
        float speed2D,
        string activeWeapon,
        bool isAlive,
        bool isOpeningPhase,
        bool isBombPlanted,
        string currentDestination,
        string currentSector,
        string currentRole,
        bool hasContact,
        bool tookDamage,
        bool hostileUtility,
        bool hasC4 = false,
        string planTargetBombsite = "",
        double tickIntervalMs = 15.625,
        IReadOnlyList<TeammatePositionSnapshot>? teammates = null,
        FullTeamDepartureSchedule? teamSchedule = null,
        CorridorDepartureQueue? corridorQueue = null)
    {
        if (!_sessionsByRoundAndSlot.TryGetValue((roundId, rawSlot), out var s))
        {
            return new CanaryTickDecision { CanaryControlling = false, Authority = "UTILITY_AI" };
        }

        if (s.IsFinished)
        {
            return new CanaryTickDecision
            {
                CanaryControlling = false,
                Authority = "UTILITY_AI",
                ExecutorState = s.ExecutorState,
                CommandId = s.CommandId,
                AbortOrCompletionReason = s.FallbackReason,
            };
        }

        double stepDist = Dist3(x, y, z, s.LastX, s.LastY, s.LastZ);
        if (!double.IsNaN(stepDist))
        {
            s.TraveledDistance += stepDist;
        }
        s.LastX = x;
        s.LastY = y;
        s.LastZ = z;

        double elapsedSec = Math.Max(0.0, (tick - s.StartTick) / 64.0);
        s.LastSpeed2D = speed2D;
        bool isKnife = !string.IsNullOrEmpty(activeWeapon) &&
                       (activeWeapon.Contains("knife", StringComparison.OrdinalIgnoreCase) ||
                        activeWeapon.Contains("bayonet", StringComparison.OrdinalIgnoreCase));
        if (isKnife)
        {
            s.WeaponReadyConfirmed = false;
            if (s.HadWeaponReadyOnce)
            {
                s.PostReadyKnifeTicks++;
            }
        }
        else if (!string.IsNullOrEmpty(activeWeapon))
        {
            s.WeaponReadyConfirmed = true;
            s.HadWeaponReadyOnce = true;
            s.PostReadyKnifeTicks = 0;
        }

        if (s.DispatchTick.HasValue && !s.MovementStartedTick.HasValue && (stepDist >= 1.5 || speed2D >= 25.0f))
        {
            s.MovementStartedTick = tick;
            s.ExecutorState = CanaryExecutorState.Moving;
        }

        // Checagens imediatas de devolução de autoridade à Utility AI
        if (!LeaseManager.IsCanaryEnabled())
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "KILL_SWITCH_DISABLED", "TACTICAL_REDIRECT", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "FALLBACK");
        }
        if (!isAlive)
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "PLAYER_DEATH", "PLAYER_DEATH", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, false, "FALLBACK");
        }
        if (!isOpeningPhase || isBombPlanted)
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "OPENING_PHASE_ENDED", "TACTICAL_REDIRECT", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, false, "FALLBACK");
        }
        if (!string.Equals(currentDestination, s.OriginalDestination, StringComparison.OrdinalIgnoreCase))
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "CANARY_ABORTED:UTILITY_PLAN_CHANGED", "TACTICAL_REDIRECT", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, false, "FALLBACK");
        }
        if (!string.IsNullOrEmpty(currentSector) && !string.Equals(currentSector, s.OriginalSector, StringComparison.OrdinalIgnoreCase))
        {
            return FinishAndRecord(s, CanaryExecutorState.Fallback, "CANARY_ABORTED:SECTOR_IMMUTABLE", "INVALID_ROUTE", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, false, "FALLBACK");
        }
        if (!string.IsNullOrEmpty(currentRole) && !string.Equals(currentRole, s.Role, StringComparison.OrdinalIgnoreCase))
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "CANARY_ABORTED:ROLE_IMMUTABLE", "TACTICAL_REDIRECT", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, false, "FALLBACK");
        }
        bool isSoloCert = !string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("CSBOT_TR_SOLO_CERT_ROUTE"));
        if (s.Team == "T" && hasC4 && !isSoloCert && !IsC4Compatible(s.OriginalDestination, planTargetBombsite, currentRole))
        {
            s.CanaryIsBombCarrier = true;
            s.PlannedBombsite = string.IsNullOrWhiteSpace(planTargetBombsite) ? s.PlannedBombsite : planTargetBombsite;
            s.BombsiteCompatible = false;
            s.BombPathPreserved = false;
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "C4_ROUTE_INCOMPATIBLE", "C4_ROUTE_INCOMPATIBLE", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, false, false, "FALLBACK");
        }
        if (s.Team == "T" && hasC4)
        {
            s.CanaryIsBombCarrier = true;
            if (!string.IsNullOrWhiteSpace(planTargetBombsite))
            {
                s.PlannedBombsite = planTargetBombsite;
            }
        }
        if (hasContact)
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "CONTACT_INTERRUPTION", "CONTACT_INTERRUPTION", tick, x, y, z, elapsedSec, activeWeapon, true, tookDamage, hostileUtility, hasC4, true, true, "FALLBACK");
        }
        if (tookDamage || s.PendingDamage)
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "DAMAGE_INTERRUPTION", "CONTACT_INTERRUPTION", tick, x, y, z, elapsedSec, activeWeapon, hasContact, true, hostileUtility, hasC4, true, true, "FALLBACK");
        }
        if (hostileUtility || s.PendingHostileUtility)
        {
            return FinishAndRecord(s, CanaryExecutorState.Interrupted, "HOSTILE_UTILITY", "CONTACT_INTERRUPTION", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, true, hasC4, true, true, "FALLBACK");
        }

        var wps = s.Route.OrderedWaypoints;
        var transitions = s.Route.TransitionWaypoints;
        bool hasTransitions = transitions != null && transitions.Count == wps.Count && transitions.Count > 0;
        var forbiddenAreas = GeometricTransitionCatalog.GetForbiddenNavAreasForCorridor(s.Route.AllowedCorridor);

        // Threat line e troca de arma antes do contato
        var tl = (hasTransitions && !string.IsNullOrEmpty(s.Route.WeaponReadyWaypoint.Name))
            ? s.Route.WeaponReadyWaypoint
            : (wps.Count > 1 ? wps[^2] : wps[0]);
        double distToThreat = Dist3(x, y, z, tl.X, tl.Y, tl.Z);
        bool shouldSwitchWeapon = elapsedSec >= s.Route.KnifeAllowedUntil || tick >= (s.Route.WeaponSwitchTick - 8) || distToThreat <= 360.0;
        if (tick >= s.Route.ThreatLineTick || distToThreat <= 160.0)
        {
            s.ThreatLineCrossed = true;
            shouldSwitchWeapon = true;
            bool persistentKnifeFailure = !s.HadWeaponReadyOnce || s.PostReadyKnifeTicks >= 6;
            if (isKnife && !s.WeaponReadyConfirmed && persistentKnifeFailure)
            {
                return FinishAndRecord(s, CanaryExecutorState.Fallback, "WEAPON_SWITCH_FAILED", "INVALID_ROUTE", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "FALLBACK");
            }
        }

        // Chegada canônica ao destino final (para rotas com TransitionWaypoints exige concluir sub-waypoints anteriores; para b_van usa ponto alcançável final)
        var finalWp = wps[^1];
        bool finalUnreachableUpper = hasTransitions && !transitions![^1].IsFinalApproachReachable;
        var arrivalTargetWp = (finalUnreachableUpper && wps.Count >= 2) ? wps[^2] : finalWp;
        double navDistFinal;
        bool navValidFinal;
        if (finalUnreachableUpper)
        {
            navDistFinal = Dist3(x, y, z, arrivalTargetWp.X, arrivalTargetWp.Y, arrivalTargetWp.Z);
            navValidFinal = Math.Abs(z - arrivalTargetWp.Z) <= 96f;
        }
        else
        {
            (navDistFinal, navValidFinal) = ComputeNavDistance(x, y, z, finalWp, forbiddenAreas);
        }

        var canonSteps = s.Route.CanonicalSteps;
        bool hasCanonical = canonSteps != null && canonSteps.Count > 0;
        int minWpIdxForDest = hasCanonical
            ? canonSteps!.Count - 1
            : (hasTransitions
                ? (finalUnreachableUpper ? Math.Max(0, wps.Count - 2) : Math.Max(0, wps.Count - 1))
                : 0);
        bool currentStepIsFinal = !hasCanonical || (s.WaypointIndex >= 0 && s.WaypointIndex < canonSteps!.Count && canonSteps[s.WaypointIndex].IsFinalDestination);
        bool withinDestRadius = s.WaypointIndex >= minWpIdxForDest && currentStepIsFinal && navValidFinal && navDistFinal <= DestinationRadiusUnits;
        if (withinDestRadius)
        {
            s.DestinationDwellTicks++;
            bool stableStopOnPoint = speed2D <= 15.0f && navDistFinal <= 32.0;
            if (s.DestinationDwellTicks >= DestinationDwellMinTicks || stableStopOnPoint)
            {
                s.WaypointIndex = wps.Count;
                s.WaypointReachedTick = tick;
                string arr = elapsedSec <= s.EffectiveDeadlineSeconds ? "ON_TIME" : "LATE";
                return FinishAndRecord(s, CanaryExecutorState.DestinationReached, "ROUTE_COMPLETED", arr, tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, false, "COMPLETED");
            }
            s.ExecutorState = CanaryExecutorState.WaypointReached;
            s.WaypointReachedTick = tick;
            s.LastBlockCause = BlockCause.None;
            RecordTick(s, tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, "DWELL_AT_DESTINATION");
            return new CanaryTickDecision
            {
                CanaryControlling = true,
                Authority = "OPENING_ROUTE_PLANNER",
                ExecutorState = s.ExecutorState,
                CommandId = s.CommandId,
                PathLength = Math.Round(navDistFinal, 1),
                CurrentWaypoint = arrivalTargetWp,
                WaypointChanged = false,
                DispatchReason = "DWELL_AT_DESTINATION",
                HoldingForStagger = false,
                ShouldSwitchToWeapon = shouldSwitchWeapon,
                KnifeAllowed = !shouldSwitchWeapon && !s.ThreatLineCrossed,
                ForbiddenNavAreas = forbiddenAreas,
            };
        }
        else
        {
            s.DestinationDwellTicks = 0;
        }

        // Escalonamento de saída (stagger) sem mascarar deadline nem soltar bot para Utility AI
        if (elapsedSec > 0.500 && tick < s.Schedule.PlannedReleaseTick)
        {
            return FinishAndRecord(s, CanaryExecutorState.Fallback, "CANARY_STAGGER_EXCEEDED_500MS", "BLOCKED_BY_TEAMMATE", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "FALLBACK");
        }

        if (tick < s.Schedule.PlannedReleaseTick)
        {
            s.ExecutorState = CanaryExecutorState.NotStarted;
            s.LastBlockCause = BlockCause.None;
            s.LastProgressUnits = stepDist;
            RecordTick(s, tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, "STAGGER_HOLD");
            return new CanaryTickDecision
            {
                CanaryControlling = true,
                Authority = "OPENING_ROUTE_PLANNER",
                ExecutorState = s.ExecutorState,
                CommandId = s.CommandId,
                PathLength = s.CurrentPathLength,
                CurrentWaypoint = null,
                WaypointChanged = false,
                DispatchReason = "STAGGER_HOLD",
                HoldingForStagger = true,
                ShouldSwitchToWeapon = shouldSwitchWeapon,
                KnifeAllowed = !shouldSwitchWeapon && !s.ThreatLineCrossed,
            };
        }

        // Avanço estrito de waypoints intermediários via GeometricTransitionExecutor (quando presente) ou raio validado
        bool advancedWaypoint = false;
        TransitionStepEvaluation? transEval = null;
        if (hasTransitions)
        {
            var preStepWp = wps[Math.Min(s.WaypointIndex, wps.Count - 1)];
            var blk = FindBlockerInCorridor(x, y, z, preStepWp, teammates);
            bool teammateBlockingNow = blk.Slot.HasValue && (blk.Dist ?? 999.0) <= 58.0;
            int wpIdxCopy = s.WaypointIndex;
            transEval = s.TransitionExecutor.EvaluateStep(
                s.RoundId,
                tick,
                elapsedSec,
                transitions!,
                ref wpIdxCopy,
                x, y, z,
                speed2D,
                teammateBlockingNow,
                exitPathValid: true,
                NavMesh);
            if (wpIdxCopy != s.WaypointIndex)
            {
                s.WaypointReachedTick = tick;
                s.ExecutorState = CanaryExecutorState.WaypointReached;
                s.WaypointIndex = wpIdxCopy;
                advancedWaypoint = true;
                if (s.RecoveryActive)
                {
                    s.RecoveryActive = false;
                    s.RecoverySucceeded = true;
                }
            }
            s.LastTransitionStep = transEval;
            if (transEval.ShouldReturnAuthority)
            {
                return FinishAndRecord(
                    s,
                    CanaryExecutorState.Fallback,
                    string.IsNullOrEmpty(transEval.ReturnAuthorityReason) ? "FAILED_STEP_UP_RETURNS_AUTHORITY" : transEval.ReturnAuthorityReason,
                    "NOT_REACHED",
                    tick, x, y, z, elapsedSec,
                    activeWeapon, hasContact, tookDamage, hostileUtility, hasC4,
                    true, true, "FALLBACK");
            }
        }
        else
        {
            while (s.WaypointIndex < wps.Count - 1)
            {
                var wp = wps[s.WaypointIndex];
                var (navDistWp, validWp) = ComputeNavDistance(x, y, z, wp, forbiddenAreas);
                if (validWp && navDistWp <= WaypointRadiusUnits)
                {
                    s.WaypointReachedTick = tick;
                    s.ExecutorState = CanaryExecutorState.WaypointReached;
                    s.WaypointIndex++;
                    advancedWaypoint = true;
                    if (s.RecoveryActive)
                    {
                        s.RecoveryActive = false;
                        s.RecoverySucceeded = true;
                    }
                }
                else
                {
                    break;
                }
            }
        }
        if (advancedWaypoint)
        {
            s.ExecutorState = CanaryExecutorState.NextWaypoint;
        }

        var targetWp = wps[Math.Min(s.WaypointIndex, wps.Count - 1)];
        var activeTransWp = hasTransitions ? transitions![Math.Min(s.WaypointIndex, transitions.Count - 1)] : null;
        if (activeTransWp != null && !activeTransWp.IsFinalApproachReachable && wps.Count >= 2)
        {
            // Para b_van_behind_apps_hold mantém steering para o ponto alcançável debaixo do Apps, preservando IntendedDestination
            targetWp = wps[^2];
        }

        // Se Recovery A/B ou legacy estava ativo, verifica conclusão de recuperação
        if (s.RecoveryActive && s.RecoveryWaypoint != null)
        {
            var (distToOrigWp, _) = ComputeNavDistance(x, y, z, targetWp, forbiddenAreas);
            bool recoveredProgress = (s.LastDistToWaypoint - distToOrigWp) >= 12.0;
            bool recoveryTimedOut = (tick - s.RecoveryStartTick) >= 20;
            if (recoveredProgress || recoveryTimedOut)
            {
                s.RecoveryActive = false;
                if (recoveredProgress) s.RecoverySucceeded = true;
                if (LateralRecoveryEnabled)
                {
                    s.LastDispatchedWaypointIndex = -1;
                }
            }
        }

        var activeNavWp = (s.RecoveryActive && s.RecoveryWaypoint != null) ? s.RecoveryWaypoint : targetWp;
        var (currDistToWp, hasValidNavPath) = ComputeNavDistance(x, y, z, activeNavWp, forbiddenAreas);
        if (!hasValidNavPath && activeTransWp != null && Math.Abs(z - activeNavWp.Z) <= 96f)
        {
            currDistToWp = Dist3(x, y, z, activeNavWp.X, activeNavWp.Y, activeNavWp.Z);
            hasValidNavPath = true;
        }
        s.PathCreated = hasValidNavPath;
        s.CurrentPathLength = double.IsFinite(currDistToWp) ? Math.Round(currDistToWp, 1) : 0.0;

        if (s.LastTrackedWaypointIndex != s.WaypointIndex)
        {
            s.LastTrackedWaypointIndex = s.WaypointIndex;
            s.LastDistToWaypoint = currDistToWp;
            s.BlockedDurationMs = 0;
        }

        double progressUnits = double.IsFinite(s.LastDistToWaypoint) && double.IsFinite(currDistToWp)
            ? s.LastDistToWaypoint - currDistToWp
            : 0.0;
        s.LastProgressUnits = progressUnits;
        s.LastDistToWaypoint = currDistToWp;

        // Bloqueio exige evidência contínua + separação rigorosa de causas (sem falso bloqueio por aliado nem sobrescrever RootBlockCause)
        bool navInvalid = !hasValidNavPath || float.IsNaN(x) || float.IsNaN(activeNavWp.X) || Math.Abs(z - activeNavWp.Z) > 260f;
        int relTick = s.ActualReleaseTick ?? s.Schedule.PlannedReleaseTick;
        if (tick < relTick)
        {
            s.WaitingForScheduledRelease = true;
            s.ScheduledWaitMs += (int)Math.Round(tickIntervalMs);
            s.LastBlockCause = BlockCause.None;
            goto SkipBlockFallback;
        }
        s.WaitingForScheduledRelease = false;
        double releaseOffsetSec = Math.Max(0.0, (relTick - s.StartTick) / 64.0);
        bool pastMovementGrace = elapsedSec > (releaseOffsetSec + 0.50);
        double tickScale = Math.Max(0.20, tickIntervalMs / 62.5);
        double minProgressTick = 1.5 * tickScale;
        double minStepTick = 2.5 * tickScale;
        bool lackOfProgress = !s.TransitionExecutor.StepUpJumpInProgress &&
                              (navInvalid || (progressUnits < minProgressTick && stepDist < minStepTick && pastMovementGrace));

        // Atualiza distância até destino final e avalia Final Approach antes de qualquer fallback
        var finalDestWp = wps[^1];
        var (navDistToFinal, _) = ComputeNavDistance(x, y, z, finalDestWp, forbiddenAreas);
        s.LastNavDistanceToDestination = double.IsFinite(navDistToFinal) ? Math.Round(navDistToFinal, 1) : 0.0;

        if (lackOfProgress)
        {
            if (TryResolveFinalApproach(s, x, y, z, navDistToFinal, progressUnits, stepDist, elapsedSec, out bool reachedFinalNow))
            {
                if (reachedFinalNow)
                {
                    s.ExecutorState = CanaryExecutorState.DestinationReached;
                    s.CompletionReason = "ROUTE_COMPLETED";
                    string arrStatus = elapsedSec <= s.EffectiveDeadlineSeconds ? "ON_TIME" : "LATE";
                    return FinishAndRecord(s, CanaryExecutorState.DestinationReached, "ROUTE_COMPLETED", arrStatus, tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "FINAL_APPROACH_DWELL_COMPLETED");
                }
                s.LastBlockCause = BlockCause.None;
                s.CurrentBlockState = "FINAL_APPROACH_ACTIVE";
                goto SkipBlockFallback;
            }

            var verifiedBlk = FindVerifiedCorridorBlocker(s, activeNavWp, teammates, teamSchedule, corridorQueue, tick);
            s.LastBlockerSlot = verifiedBlk.BlockerSlot;
            s.LastDistanceToBlocker = verifiedBlk.Distance;
            s.VerifiedSameCorridor = verifiedBlk.SameCorridor;
            if (verifiedBlk.IsVerified)
            {
                s.RootBlockerControlMode = verifiedBlk.BlockerControlMode;
            }
            else if (s.RootBlockCause == BlockCause.TeammateCongestion)
            {
                // Colega já desocupou o trecho; encerra espera de fila e reclassifica se continuar parado
                s.RootBlockCause = BlockCause.None;
                s.QueueResumedPending = true;
            }

            string rootCause;
            if (navInvalid)
            {
                rootCause = BlockCause.NavmeshFailure;
                s.NavigationFailureSeconds += tickIntervalMs / 1000.0;
            }
            else if (verifiedBlk.IsVerified && hasValidNavPath)
            {
                rootCause = BlockCause.TeammateCongestion;
            }
            else if (speed2D < 15.0f)
            {
                rootCause = BlockCause.StaticObstacle;
            }
            else
            {
                rootCause = BlockCause.NoProgressUnknown;
            }

            // Congela a primeira causa raiz comprovada; RepathCount > 0 altera apenas CurrentBlockState
            if (s.RootBlockCause == BlockCause.None || s.RootBlockCause == BlockCause.NoProgressUnknown)
            {
                s.RootBlockCause = rootCause;
                s.RootBlockTick = tick;
                s.RootBlockerSlot = verifiedBlk.BlockerSlot;
            }

            s.CurrentBlockState = (s.RepathCount > 0 && rootCause != BlockCause.NavmeshFailure)
                ? BlockCause.PathRecalculation
                : rootCause;
            s.LastBlockCause = s.RootBlockCause;
            s.BlockedDurationMs += (int)Math.Round(tickIntervalMs);

            if (s.RootBlockCause == BlockCause.TeammateCongestion)
            {
                bool isScheduledCanaryPredecessor = verifiedBlk.BlockerControlMode == "CANARY_CONTROLLED" &&
                                                    s.Schedule.PredecessorSlot.HasValue &&
                                                    verifiedBlk.BlockerSlot == s.Schedule.PredecessorSlot;
                s.VerifiedCongestionAllowanceSeconds = Math.Min(1.500, s.VerifiedCongestionAllowanceSeconds + (tickIntervalMs / 1000.0));
                s.RecoveryAttempted = true;
                s.RecoveryActive = false;
                s.RecoveryWaypoint = null;
                s.RecoveryStrategy = isScheduledCanaryPredecessor ? "SCHEDULED_PREDECESSOR_WAIT" : "QUEUE_WAIT_FOR_PREDECESSOR";
                s.QueueResumedPending = true;

                if (!isScheduledCanaryPredecessor)
                {
                    s.RuntimeCongestionMs += (int)Math.Round(tickIntervalMs);
                    if (s.BlockedDurationMs > 1500)
                    {
                        return FinishAndRecord(s, CanaryExecutorState.Fallback, "CORRIDOR_QUEUE_TIMEOUT", "BLOCKED_BY_TEAMMATE", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "CORRIDOR_QUEUE_TIMEOUT");
                    }
                }
            }
            else if (s.RootBlockCause == BlockCause.NavmeshFailure)
            {
                return FinishAndRecord(s, CanaryExecutorState.Fallback, "CANARY_BLOCKED_FALLBACK", "NOT_REACHED", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "NAVMESH_FAILURE");
            }
            else
            {
                if (s.RootBlockCause == BlockCause.StaticObstacle &&
                    s.BlockedDurationMs > 350 &&
                    !s.RecoveryAttempted)
                {
                    s.RecoveryAttempted = true;
                    s.RepathCount++;
                    s.RecoveryActive = true;
                    s.RecoveryDispatched = false;
                    s.RecoveryStartTick = tick;
                    s.RecoveryStrategy = "RECOVERY_B_REPATH_PROJECTED_WAYPOINT";
                    s.RecoveryWaypoint = ProjectRecoveryWaypoint(targetWp);
                }

                if (s.BlockedDurationMs > 900)
                {
                    return FinishAndRecord(s, CanaryExecutorState.Fallback, "CANARY_BLOCKED_FALLBACK", "NOT_REACHED", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "FALLBACK");
                }
            }
        }
        else
        {
            if (s.QueueResumedPending)
            {
                s.QueueResumedPending = false;
                s.RecoveryStrategy = "QUEUE_RESUMED";
                s.RecoverySucceeded = true;
            }
            s.RootBlockCause = BlockCause.None;
            s.CurrentBlockState = BlockCause.None;
            s.LastBlockCause = BlockCause.None;
            s.LastBlockerSlot = null;
            s.LastDistanceToBlocker = null;
            s.BlockedDurationMs = Math.Max(0, s.BlockedDurationMs - (int)Math.Round(tickIntervalMs));
        }
        SkipBlockFallback:

        if (elapsedSec > s.EffectiveDeadlineSeconds * 1.5)
        {
            return FinishAndRecord(s, CanaryExecutorState.Fallback, "TIMEOUT", "NOT_REACHED", tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, true, "FALLBACK");
        }

        var dispatchWp = (s.RecoveryActive && s.RecoveryWaypoint != null) ? s.RecoveryWaypoint : targetWp;
        bool wpChanged = false;
        string dispatchReason = "NONE";
        if (s.RecoveryActive && !s.RecoveryDispatched)
        {
            wpChanged = true;
            s.RecoveryDispatched = true;
            dispatchReason = "RECOVERY_AUTHORIZED";
            s.CommandId++;
            s.DispatchTick = tick;
            s.ExecutorState = CanaryExecutorState.CommandDispatched;
        }
        else if ((!s.RecoveryActive || !LateralRecoveryEnabled) && s.LastDispatchedWaypointIndex != s.WaypointIndex)
        {
            wpChanged = true;
            dispatchReason = s.LastDispatchedWaypointIndex == -1 ? "ROUTE_START" : "WAYPOINT_CHANGED";
            s.LastDispatchedWaypointIndex = s.WaypointIndex;
            s.CommandId++;
            s.DispatchTick = tick;
            s.ExecutorState = CanaryExecutorState.CommandDispatched;
        }
        else if (s.MovementStartedTick.HasValue && s.ExecutorState != CanaryExecutorState.WaypointReached)
        {
            s.ExecutorState = CanaryExecutorState.Moving;
        }

        RecordTick(s, tick, x, y, z, elapsedSec, activeWeapon, hasContact, tookDamage, hostileUtility, hasC4, true, dispatchReason);
        return new CanaryTickDecision
        {
            CanaryControlling = true,
            Authority = "OPENING_ROUTE_PLANNER",
            ExecutorState = s.ExecutorState,
            CommandId = s.CommandId,
            PathLength = s.CurrentPathLength,
            CurrentWaypoint = dispatchWp,
            WaypointChanged = wpChanged,
            DispatchReason = dispatchReason,
            HoldingForStagger = false,
            ShouldSwitchToWeapon = shouldSwitchWeapon,
            KnifeAllowed = !shouldSwitchWeapon && !s.ThreatLineCrossed,
            ShouldEmitJumpPulse = transEval?.ShouldEmitJumpPulse ?? false,
            ShouldEmitAttackPulse = transEval?.ShouldEmitAttackPulse ?? false,
            UseExactPortalSteering = activeTransWp?.UseExactPortalSteering ?? false,
            RequireCrouch = activeTransWp?.RequireCrouch ?? false,
            ForbiddenNavAreas = forbiddenAreas,
            ActiveTransitionType = activeTransWp?.TransitionType ?? TransitionWaypointType.FLAT_PORTAL,
            ActiveMovementAction = activeTransWp?.MovementAction ?? TransitionMovementAction.NONE,
            TransitionCommandEvent = transEval?.CommandEventType ?? string.Empty,
        };
    }

    public static bool TryResolveFinalApproach(
        ActiveCanarySession s,
        float x, float y, float z,
        double navDistToFinal,
        double progressUnits,
        double stepDist,
        double elapsedSec,
        out bool reachedFinalNow)
    {
        reachedFinalNow = false;
        var wps = s.Route.OrderedWaypoints;
        if (wps.Count == 0 || s.WaypointIndex < wps.Count - 1)
        {
            return false;
        }
        var destWp = wps[^1];
        double directDist = Dist3(x, y, z, destWp.X, destWp.Y, destWp.Z);
        double effDist = Math.Min(directDist, double.IsFinite(navDistToFinal) ? navDistToFinal : directDist);
        if (effDist <= 135.0)
        {
            s.FinalApproachActive = true;
            s.DestinationDwellTicks++;
            if (s.DestinationDwellTicks >= 2)
            {
                reachedFinalNow = true;
            }
            return true;
        }
        // Se está na aproximação final (<= 155u, como mid_window_right_deep a 137.6u) e com orçamento de tempo válido
        if (effDist <= 155.0 && elapsedSec < s.EffectiveDeadlineSeconds && (progressUnits > 0.2 || stepDist > 0.2 || s.BlockedDurationMs < 650))
        {
            s.FinalApproachActive = true;
            return true;
        }
        return false;
    }

    public static VerifiedBlockerResult FindVerifiedCorridorBlocker(
        ActiveCanarySession session,
        RouteWaypoint wp,
        IReadOnlyList<TeammatePositionSnapshot>? teammates,
        FullTeamDepartureSchedule? schedule = null,
        CorridorDepartureQueue? queue = null,
        int currentTick = 0)
    {
        if (session.FinalApproachActive)
        {
            return new VerifiedBlockerResult { IsVerified = false, Reason = "FINAL_APPROACH_ACTIVE" };
        }
        if (teammates == null || teammates.Count == 0)
        {
            return new VerifiedBlockerResult { IsVerified = false, Reason = "NO_TEAMMATES" };
        }
        double dirX = wp.X - session.LastX;
        double dirY = wp.Y - session.LastY;
        double norm = Math.Sqrt(dirX * dirX + dirY * dirY);
        if (norm < 1e-3) return new VerifiedBlockerResult { IsVerified = false, Reason = "ZERO_VECTOR" };
        dirX /= norm;
        dirY /= norm;

        string selfCorridor = !string.IsNullOrWhiteSpace(session.InferredCorridor)
            ? session.InferredCorridor
            : session.Schedule.ConflictGroup;

        if (string.Equals(session.CorridorConfidenceName, "LOW", StringComparison.OrdinalIgnoreCase))
        {
            return new VerifiedBlockerResult { IsVerified = false, Reason = "CORRIDOR_RELATION_UNCERTAIN" };
        }

        int? bestSlot = null;
        double bestDist = double.MaxValue;
        float bx = 0f, by = 0f;
        string bestMode = string.Empty;
        string bestConf = "LOW";

        foreach (var tm in teammates)
        {
            if (tm.RawSlot == session.RawSlot) continue;
            if (currentTick > 0 && tm.SnapshotTick > 0)
            {
                double ageMs = (currentTick - tm.SnapshotTick) * (1000.0 / 64.0);
                if (ageMs > 100.0) continue;
            }
            if (Math.Abs(tm.Z - session.LastZ) > 22.0f) continue;
            double dist = Dist3(tm.X, tm.Y, tm.Z, session.LastX, session.LastY, session.LastZ);
            if (dist < 1.0 || dist > 125.0) continue;

            // Regra estrita: ConflictGroup vazio nunca é tratado como mesmo corredor!
            bool sameCorridor = false;
            string tmMode = "UTILITY_AI_OBSERVED";
            string tmConf = "LOW";
            if (schedule != null && schedule.BySlot.TryGetValue(tm.RawSlot, out var tmAssign))
            {
                tmMode = tmAssign.ControlMode.ToString();
                tmConf = tmAssign.CorridorConfidence.ToString();
                sameCorridor = tmAssign.CorridorConfidence != CorridorConfidence.LOW &&
                               !string.IsNullOrWhiteSpace(selfCorridor) &&
                               string.Equals(tmAssign.InferredCorridor, selfCorridor, StringComparison.OrdinalIgnoreCase);
            }
            else if (!string.IsNullOrWhiteSpace(tm.ConflictGroup) && !string.IsNullOrWhiteSpace(selfCorridor))
            {
                sameCorridor = string.Equals(tm.ConflictGroup, selfCorridor, StringComparison.OrdinalIgnoreCase);
                tmConf = "MEDIUM";
            }

            if (!sameCorridor) continue;

            double dx = tm.X - session.LastX;
            double dy = tm.Y - session.LastY;
            double forwardProj = dx * dirX + dy * dirY;
            double lateralDist = Math.Abs(dx * (-dirY) + dy * dirX);
            if (forwardProj >= 12.0 && lateralDist <= 56.0 && dist < bestDist)
            {
                bestDist = dist;
                bestSlot = tm.RawSlot;
                bx = tm.X;
                by = tm.Y;
                bestMode = tmMode;
                bestConf = tmConf;
            }
        }

        if (!bestSlot.HasValue)
        {
            return new VerifiedBlockerResult { IsVerified = false, Reason = "NO_SAME_CORRIDOR_AHEAD_BLOCKER" };
        }
        return new VerifiedBlockerResult
        {
            IsVerified = true,
            BlockerSlot = bestSlot,
            BlockerControlMode = bestMode,
            SameCorridor = true,
            IsAhead = true,
            Distance = Math.Round(bestDist, 1),
            BlockerX = bx,
            BlockerY = by,
            PortalOccupied = queue?.PortalOccupied ?? false,
            Confidence = bestConf,
            Reason = "VERIFIED_CORRIDOR_BLOCKER"
        };
    }

    private static (int? Slot, double? Dist, float Bx, float By) FindBlockerInCorridor(
        float x, float y, float z, RouteWaypoint wp, IReadOnlyList<TeammatePositionSnapshot>? teammates)
    {
        if (teammates == null || teammates.Count == 0) return (null, null, 0f, 0f);
        double dirX = wp.X - x;
        double dirY = wp.Y - y;
        double norm = Math.Sqrt(dirX * dirX + dirY * dirY);
        if (norm < 1e-3) return (null, null, 0f, 0f);
        dirX /= norm;
        dirY /= norm;

        int? bestSlot = null;
        double bestDist = double.MaxValue;
        float bx = 0f, by = 0f;
        foreach (var tm in teammates)
        {
            if (Math.Abs(tm.Z - z) > 22.0f) continue;
            double dist = Dist3(tm.X, tm.Y, tm.Z, x, y, z);
            if (dist < 1.0 || dist > 140.0) continue;
            double dx = tm.X - x;
            double dy = tm.Y - y;
            double dot = (dx * dirX + dy * dirY) / Math.Max(1.0, Math.Sqrt(dx * dx + dy * dy));
            if (dot >= 0.35 && dist < bestDist)
            {
                bestDist = dist;
                bestSlot = tm.RawSlot;
                bx = tm.X;
                by = tm.Y;
            }
        }
        return bestSlot.HasValue ? (bestSlot, Math.Round(bestDist, 1), bx, by) : (null, null, 0f, 0f);
    }

    private static RouteWaypoint ComputeLegacyLateralWaypoint(
        float x, float y, float z, RouteWaypoint wp, float blockerX, float blockerY)
    {
        double dirX = wp.X - x;
        double dirY = wp.Y - y;
        double norm = Math.Sqrt(dirX * dirX + dirY * dirY);
        if (norm < 1e-3)
        {
            return new RouteWaypoint { Name = $"{wp.Name}_lateral", X = x + 55f, Y = y, Z = z };
        }
        dirX /= norm;
        dirY /= norm;
        double perpX = -dirY;
        double perpY = dirX;
        double sign = (blockerX != 0f || blockerY != 0f) && ((blockerX - x) * perpX + (blockerY - y) * perpY > 0) ? -1.0 : 1.0;

        float latX = (float)(x + dirX * Math.Min(50.0, norm * 0.35) + perpX * (40.0 * sign));
        float latY = (float)(y + dirY * Math.Min(50.0, norm * 0.35) + perpY * (40.0 * sign));
        return new RouteWaypoint { Name = $"{wp.Name}_lateral", X = latX, Y = latY, Z = z };
    }

    public static string GuardCombatOrC4Authority(string utilityAction, bool isCanaryControlling)
    {
        _ = isCanaryControlling;
        return utilityAction;
    }

    private void AbortSession(ActiveCanarySession s, string reason, string arrivalStatus, int tick)
    {
        s.Authority = "UTILITY_AI";
        s.FallbackReason = reason;
        s.CompletionReason = reason;
        s.ArrivalStatus = arrivalStatus;
        s.AuthorityReturnTick = tick;
        LeaseManager.ReleaseLeaseForSlot(s.RoundId, s.RawSlot, tick, reason);
    }

    private CanaryTickDecision FinishAndRecord(
        ActiveCanarySession s,
        string finalExecutorState,
        string reason,
        string arrivalStatus,
        int tick,
        float x, float y, float z,
        double elapsedSec,
        string activeWeapon,
        bool contact,
        bool damage,
        bool hostileUtility,
        bool hasC4,
        bool c4Compatible,
        bool forceWeaponSwitch,
        string dispatchReason)
    {
        s.ExecutorState = finalExecutorState;
        AbortSession(s, reason, arrivalStatus, tick);
        RecordTick(s, tick, x, y, z, elapsedSec, activeWeapon, contact, damage, hostileUtility, hasC4, c4Compatible, dispatchReason);
        return new CanaryTickDecision
        {
            CanaryControlling = false,
            Authority = "UTILITY_AI",
            ExecutorState = s.ExecutorState,
            CommandId = s.CommandId,
            PathLength = s.CurrentPathLength,
            DispatchReason = dispatchReason,
            ShouldSwitchToWeapon = forceWeaponSwitch,
            KnifeAllowed = false,
            AbortOrCompletionReason = reason,
        };
    }

    private void RecordTick(
        ActiveCanarySession s,
        int tick,
        float x, float y, float z,
        double elapsedSec,
        string activeWeapon,
        bool contact,
        bool damage,
        bool hostileUtility,
        bool hasC4,
        bool c4Compatible,
        string dispatchReason)
    {
        bool weaponReadyBeforeContact = !contact || s.WeaponReadyConfirmed || !activeWeapon.Contains("knife", StringComparison.OrdinalIgnoreCase);
        var wps = s.Route.OrderedWaypoints;
        string curWpName = (s.RecoveryActive && s.RecoveryWaypoint != null)
            ? s.RecoveryWaypoint.Name
            : (s.WaypointIndex < wps.Count ? wps[s.WaypointIndex].Name : (wps.Count > 0 ? wps[^1].Name : string.Empty));
        var canonSteps = s.Route.CanonicalSteps;
        var activeCanon = (canonSteps != null && s.WaypointIndex >= 0 && s.WaypointIndex < canonSteps.Count)
            ? canonSteps[s.WaypointIndex]
            : null;
        string nextWpName = activeCanon != null
            ? (activeCanon.ExpectedNextStepName ?? string.Empty)
            : ((s.WaypointIndex + 1 < wps.Count) ? wps[s.WaypointIndex + 1].Name : string.Empty);
        int navArea = NavMesh != null ? NavMesh.ProjectPoint(x, y, z, maxSnapUnits: 120f).AreaId : 0;
        int expectedExitNavArea = activeCanon != null
            ? (activeCanon.ExpectedNextStepIndex is int nextIdx && nextIdx >= 0 && nextIdx < canonSteps!.Count
                ? canonSteps[nextIdx].NavMeshArea
                : activeCanon.NavMeshArea)
            : 0;
        bool portalCrossed = activeCanon != null && activeCanon.ExpectedNextStepIndex >= 0 &&
            expectedExitNavArea > 0 && navArea == expectedExitNavArea;
        double effDeadline = s.EffectiveDeadlineSeconds;
        double moveDelay = s.MovementStartedTick.HasValue && s.DispatchTick.HasValue
            ? Math.Max(0.0, (s.MovementStartedTick.Value - s.DispatchTick.Value) / 64.0)
            : 0.0;
        double interruptTime = s.ExecutorState == CanaryExecutorState.Interrupted ? elapsedSec : 0.0;

        string evType = "CANARY_TICK";
        bool fireTerminalHook = false;
        if (s.IsFinished && !s.TerminalEventEmitted)
        {
            s.TerminalEventEmitted = true;
            evType = s.ExecutorState == CanaryExecutorState.DestinationReached
                ? "COMPLETED"
                : (s.ExecutorState == CanaryExecutorState.Interrupted ? "INTERRUPTED" : "ABORTED");
            fireTerminalHook = true;
        }

        _records.Add(new CanaryTelemetryRecord
        {
            Round = s.RoundId,
            SessionId = s.SessionId,
            ControllerId = s.ControllerId,
            LeaseId = s.LeaseId,
            EventType = evType,
            PlayerPseudonym = s.PlayerPseudonym,
            Team = s.Team,
            CanaryEnabled = true,
            Authority = s.Authority,
            ExecutorState = s.ExecutorState,
            CommandId = s.CommandId,
            DispatchTick = s.DispatchTick,
            MovementStartedTick = s.MovementStartedTick,
            PathCreated = s.PathCreated,
            PathLength = s.CurrentPathLength,
            WaypointReachedTick = s.WaypointReachedTick,
            CompletionReason = s.CompletionReason,
            WaypointRadiusUsed = WaypointRadiusUnits,
            DestinationDwellTicks = s.DestinationDwellTicks,
            SpawnBucket = s.Route.SpawnBucket,
            RouteId = s.Route.RouteId,
            WaypointIndex = s.WaypointIndex,
            CurrentWaypoint = curWpName,
            NextWaypoint = nextWpName,
            NavArea = navArea,
            CanonicalStepIndex = s.WaypointIndex,
            CanonicalStepCount = canonSteps?.Count ?? wps.Count,
            CanonicalStepName = activeCanon?.Name ?? curWpName,
            CanonicalStepRole = activeCanon?.SemanticRole.ToString() ?? string.Empty,
            IsFinalDestination = activeCanon?.IsFinalDestination ?? (s.WaypointIndex >= wps.Count - 1),
            ExpectedNextStepIndex = activeCanon?.ExpectedNextStepIndex ?? (s.WaypointIndex + 1 < wps.Count ? s.WaypointIndex + 1 : -1),
            ExpectedNextStepName = activeCanon != null ? activeCanon.ExpectedNextStepName : (string.IsNullOrEmpty(nextWpName) ? null : nextWpName),
            GoalOwnershipValid = !s.LastUnauthorizedOverwrite,
            PortalCrossed = portalCrossed,
            CurrentNavArea = navArea,
            ExpectedExitNavArea = expectedExitNavArea,
            NavDistance = Math.Round(s.CurrentPathLength, 1),
            PathRemaining = Math.Round(s.CurrentPathLength, 1),
            MovementCommand = dispatchReason,
            IntendedDestination = s.OriginalDestination,
            ActualPosition = new[] { MathF.Round(x, 1), MathF.Round(y, 1), MathF.Round(z, 1) },
            ElapsedSeconds = Math.Round(elapsedSec, 3),
            ExpectedTravelTime = Math.Round(s.Route.ExpectedArrivalSeconds, 3),
            ActualMovementStartDelay = Math.Round(moveDelay, 3),
            VerifiedCongestionDelay = Math.Round(s.VerifiedCongestionAllowanceSeconds, 3),
            NavigationFailureTime = Math.Round(s.NavigationFailureSeconds, 3),
            InterruptionTime = Math.Round(interruptTime, 3),
            DeadlineSeconds = Math.Round(effDeadline, 3),
            BaseDeadlineSeconds = Math.Round(s.Route.DeadlineSeconds, 3),
            PlannedStaggerMs = s.Schedule.PlannedStaggerMs,
            VerifiedCongestionAllowanceSeconds = Math.Round(s.VerifiedCongestionAllowanceSeconds, 3),
            EffectiveDeadlineSeconds = Math.Round(effDeadline, 3),
            DeadlineMarginSeconds = Math.Round(effDeadline - elapsedSec, 3),
            ConflictGroup = s.Schedule.ConflictGroup,
            SpawnPriority = s.Schedule.SpawnPriority,
            RolePriority = s.Schedule.RolePriority,
            PlannedReleaseTick = s.Schedule.PlannedReleaseTick,
            MinimumSpacingUnits = s.Schedule.MinimumSpacingUnits,
            PredecessorSlot = s.Schedule.PredecessorSlot,
            ActiveWeapon = activeWeapon,
            ThreatLineCrossed = s.ThreatLineCrossed,
            Contact = contact,
            Damage = damage,
            HostileUtility = hostileUtility,
            BlockedDuration = s.BlockedDurationMs,
            BlockedDurationMs = s.BlockedDurationMs,
            BlockerSlot = s.LastBlockerSlot,
            DistanceToBlocker = s.LastDistanceToBlocker,
            ProgressUnits = Math.Round(s.LastProgressUnits, 2),
            BlockCauseName = s.LastBlockCause,
            RecoveryAttempted = s.RecoveryAttempted,
            RecoverySucceeded = s.RecoverySucceeded,
            RecoveryWaypoint = s.RecoveryWaypoint?.Name ?? string.Empty,
            RecoveryStrategy = s.RecoveryStrategy,
            DispatchReason = dispatchReason,
            RepathCount = s.RepathCount,
            ArrivalStatus = s.ArrivalStatus,
            FallbackReason = s.FallbackReason,
            AuthorityReturnTick = s.AuthorityReturnTick,
            TargetSector = s.OriginalSector,
            Role = s.Role,
            HasC4 = hasC4,
            C4Compatible = c4Compatible,
            BombCarrierSlot = s.BombCarrierSlot,
            CanaryIsBombCarrier = hasC4 || s.CanaryIsBombCarrier,
            PlannedBombsite = s.PlannedBombsite,
            AssignedRoute = s.Route.RouteId,
            RouteBombsite = s.RouteBombsite,
            BombsiteCompatible = c4Compatible && s.BombsiteCompatible,
            BombPathPreserved = c4Compatible && s.BombPathPreserved,
            WeaponReadyBeforeContact = weaponReadyBeforeContact,
            TraveledDistance = Math.Round(s.TraveledDistance, 1),
            ExpectedDistance = s.Route.ExpectedDistance,
            LeaseActive = LeaseManager.IsSlotLeasedByCanary(s.RawSlot, s.RoundId),
            LeaseOwner = LeaseManager.IsSlotLeasedByCanary(s.RawSlot, s.RoundId) ? "OPENING_ROUTE_CANARY" : "UTILITY_AI",
            IsolationMode = LeaseManager.GetIsolationMode().ToString(),
            GoalBeforeCanary = s.LastGoalBefore,
            GoalAfterCanary = s.LastGoalAfter,
            GoalEndOfTick = s.LastGoalEndOfTick,
            UnauthorizedOverwrite = s.LastUnauthorizedOverwrite,
            CompetingWritersSuppressed = LeaseManager.SuppressedAttempts.Count(a => a.RoundId == s.RoundId && a.BotSlot == s.RawSlot && a.Suppressed),
            NativeState = s.LastNativeState,
            VelocityXy = Math.Round(s.LastSpeed2D, 2),
            JumpPulsesIssued = s.TransitionExecutor.JumpPulsesIssued,
            ContinuousJumpTicks = s.TransitionExecutor.ContinuousJumpViolations,
            TransitionType = s.LastTransitionStep?.CurrentWaypoint?.TransitionType.ToString() ?? string.Empty,
            TransitionAction = s.LastTransitionStep?.CurrentWaypoint?.MovementAction.ToString() ?? string.Empty,
            TransitionEventType = s.LastTransitionStep?.CommandEventType ?? string.Empty,
            TransitionCommandCount = s.TransitionExecutor.CommandDispatchCount,
            DepartureControlMode = "CANARY_CONTROLLED",
            InferredCorridor = string.IsNullOrEmpty(s.InferredCorridor) ? s.Schedule.ConflictGroup : s.InferredCorridor,
            CorridorInferenceSource = s.CorridorInferenceSource,
            CorridorConfidence = s.CorridorConfidenceName,
            ActualReleaseTick = s.ActualReleaseTick ?? s.Schedule.PlannedReleaseTick,
            RootBlockCause = s.RootBlockCause,
            CurrentBlockState = s.CurrentBlockState,
            BlockerControlMode = s.RootBlockerControlMode,
            VerifiedSameCorridor = s.VerifiedSameCorridor,
            FinalApproachActive = s.FinalApproachActive,
            NavDistanceToDestination = s.LastNavDistanceToDestination,
            InitialDepartureCorridor = s.InitialDepartureCorridor,
            DownstreamConflictGroup = s.DownstreamConflictGroup,
            QueueId = s.QueueId,
            QueuePosition = s.QueuePosition,
            LeaderSlot = s.LeaderSlot,
            PredecessorEnterTick = s.PredecessorEnterTick,
            PredecessorClearTick = s.PredecessorClearTick,
            ReleaseCondition = s.ReleaseCondition,
            WaitingForScheduledRelease = s.WaitingForScheduledRelease,
            ScheduledWaitMs = s.ScheduledWaitMs,
            RuntimeCongestionMs = s.RuntimeCongestionMs,
        });
        if (fireTerminalHook)
        {
            OnSessionTerminal?.Invoke(s, evType, tick);
        }
    }

    public IReadOnlyList<TransitionExecutionEvent> GetTransitionEvents() =>
        _sessionsByRound.Values.SelectMany(s => s.TransitionExecutor.Events).ToList();

    public void FlushJsonl(string path)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        using var sw = new StreamWriter(path, append: false);
        foreach (var r in _records)
        {
            sw.WriteLine(JsonSerializer.Serialize(r));
        }
        var noEligiblePath = Path.Combine(dir ?? ".", "opening_canary_no_eligible.json");
        File.WriteAllText(noEligiblePath, JsonSerializer.Serialize(_noEligibleRounds.Values.ToList(), new JsonSerializerOptions { WriteIndented = true }));
    }

    private static double Dist3(double x1, double y1, double z1, double x2, double y2, double z2)
    {
        double dx = x2 - x1;
        double dy = y2 - y1;
        double dz = z2 - z1;
        return Math.Sqrt(dx * dx + dy * dy + dz * dz);
    }
}
