using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace CsBotManager;

public enum TransitionWaypointType
{
    FLAT_PORTAL,
    STEP_UP,
    STEP_DOWN,
    NARROW_PASSAGE,
    DOORWAY,
    RAMP,
    VENT_ENTRY,
    VENT_EXIT,
    SITE_ENTRY
}

public enum TransitionMovementAction
{
    NONE,
    ALIGN_CORRIDOR,
    STEP_UP_JUMP_PULSE,
    CLEAR_VENT_OBSTACLE
}

/// <summary>
/// Descreve um waypoint contratual de transição geométrica sobre o NavMesh para o Canary CT.
/// </summary>
public sealed class RouteTransitionWaypoint
{
    [JsonPropertyName("name")] public string Name { get; init; } = string.Empty;
    [JsonPropertyName("x")] public float X { get; init; }
    [JsonPropertyName("y")] public float Y { get; init; }
    [JsonPropertyName("z")] public float Z { get; init; }
    [JsonPropertyName("navmesh_area")] public int NavMeshArea { get; init; }
    [JsonPropertyName("transition_type")] public TransitionWaypointType TransitionType { get; init; } = TransitionWaypointType.FLAT_PORTAL;
    [JsonPropertyName("approach_dir_x")] public float ApproachDirX { get; init; } = 1f;
    [JsonPropertyName("approach_dir_y")] public float ApproachDirY { get; init; }
    [JsonPropertyName("approach_dir_z")] public float ApproachDirZ { get; init; }
    [JsonPropertyName("arrival_radius")] public float ArrivalRadius { get; init; } = 42f;
    [JsonPropertyName("exit_radius")] public float ExitRadius { get; init; } = 50f;
    [JsonPropertyName("minimum_forward_progress")] public float MinimumForwardProgress { get; init; } = 8f;
    [JsonPropertyName("maximum_lateral_error")] public float MaximumLateralError { get; init; } = 48f;
    [JsonPropertyName("movement_action")] public TransitionMovementAction MovementAction { get; init; } = TransitionMovementAction.NONE;
    [JsonPropertyName("timeout_seconds")] public double TimeoutSeconds { get; init; } = 2.5;
    [JsonPropertyName("next_waypoint")] public string NextWaypoint { get; init; } = string.Empty;
    [JsonPropertyName("required_clearance")] public float RequiredClearance { get; init; } = 36f;
    [JsonPropertyName("expected_z_delta")] public float ExpectedZDelta { get; init; }
    [JsonPropertyName("min_z_delta")] public float MinZDelta { get; init; }
    [JsonPropertyName("max_z_delta")] public float MaxZDelta { get; init; }
    [JsonPropertyName("allow_jump_pulse")] public bool AllowJumpPulse { get; init; }
    [JsonPropertyName("use_exact_portal_steering")] public bool UseExactPortalSteering { get; init; }
    [JsonPropertyName("require_crouch")] public bool RequireCrouch { get; init; }
    [JsonPropertyName("is_final_approach_reachable")] public bool IsFinalApproachReachable { get; init; } = true;

    public RouteWaypoint ToRouteWaypoint() => new() { Name = Name, X = X, Y = Y, Z = Z };
}

public sealed class TransitionExecutionEvent
{
    [JsonPropertyName("round_id")] public int RoundId { get; init; }
    [JsonPropertyName("tick")] public int Tick { get; init; }
    [JsonPropertyName("event_type")] public string EventType { get; init; } = string.Empty;
    [JsonPropertyName("transition_id")] public string TransitionId { get; init; } = string.Empty;
    [JsonPropertyName("waypoint_name")] public string WaypointName { get; init; } = string.Empty;
    [JsonPropertyName("transition_type")] public string TransitionType { get; init; } = string.Empty;
    [JsonPropertyName("action")] public string Action { get; init; } = string.Empty;
    [JsonPropertyName("z_delta")] public double ZDelta { get; init; }
    [JsonPropertyName("jump_pulse")] public bool JumpPulse { get; init; }
}

public sealed class TransitionStepEvaluation
{
    public bool Active { get; init; }
    public bool EmitCommand { get; init; }
    public string CommandEventType { get; init; } = string.Empty;
    public bool ShouldEmitJumpPulse { get; init; }
    public bool ShouldEmitAttackPulse { get; init; }
    public bool TransitionCompleted { get; init; }
    public bool SubwaypointAdvanced { get; init; }
    public bool ShouldReturnAuthority { get; init; }
    public string ReturnAuthorityReason { get; init; } = string.Empty;
    public RouteTransitionWaypoint? CurrentWaypoint { get; init; }
}

/// <summary>
/// Catálogo geométrico auditado do NavMesh de de_mirage para as três transições CT do Canary.
/// Mantém rotas aprovadas do setor A (A_TICKET, A_JUNGLE) integralmente congeladas.
/// </summary>
public static class GeometricTransitionCatalog
{
    public static readonly HashSet<string> MarketCorridorSpots = new(StringComparer.OrdinalIgnoreCase)
    {
        "b_forest_bench_hold_apps",
        "b_van_behind_apps_hold",
        "b_short_pillar_hold_apps",
        "b_short_pillar_bomb_control",
        "b_site_default_plant_box",
        "ct_b_edward_under_apps",
        "ct_b_empty_pillar_jail",
    };

    public static readonly HashSet<string> WindowCorridorSpots = new(StringComparer.OrdinalIgnoreCase)
    {
        "mid_window_right_deep",
        "mid_ladder_room_control",
    };

    /// <summary>
    /// Áreas NavMesh proibidas para rotas CT_MARKET_CORRIDOR (proíbe atalhos por Window, Connector, Short e janela do Market).
    /// </summary>
    public static readonly IReadOnlySet<int> MarketForbiddenNavAreas = new HashSet<int>
    {
        // Janela elevada do Market (parapeito +40u -> B Site)
        1733, 1737, 1736,
        // Saídas leste rumo a Window / Vents / Connector / Mid (nunca bloqueia áreas do B Site como 1055/1179)
        1368, 1376, 1381, 1382, 1383, 1390, 1412, 1418, 1419, 1420,
        1359, 1350, 1326, 1304, 1295, 1226, 1187, 1160, 975
    };

    /// <summary>
    /// Áreas NavMesh proibidas para rotas CT_MID_WINDOW (impede desvio para B Market).
    /// </summary>
    public static readonly IReadOnlySet<int> WindowForbiddenNavAreas = new HashSet<int>
    {
        1445, 1446, 1531, 1592, 1690, 1705, 1706, 1868, 2013, 2171, 2172, 2257, 2232, 2233
    };

    public static bool IsProtectedApprovedARoute(string team, string corridorKey) =>
        string.Equals(team, "CT", StringComparison.OrdinalIgnoreCase) &&
        (string.Equals(corridorKey, "A_TICKET", StringComparison.OrdinalIgnoreCase) ||
         string.Equals(corridorKey, "A_JUNGLE", StringComparison.OrdinalIgnoreCase));

    public static IReadOnlySet<int>? GetForbiddenNavAreasForCorridor(string allowedCorridor)
    {
        if (string.Equals(allowedCorridor, "CT_MARKET_CORRIDOR", StringComparison.OrdinalIgnoreCase))
        {
            return MarketForbiddenNavAreas;
        }
        if (string.Equals(allowedCorridor, "CT_MID_WINDOW", StringComparison.OrdinalIgnoreCase))
        {
            return WindowForbiddenNavAreas;
        }
        return null;
    }

    public static List<RouteTransitionWaypoint> BuildTransitionsForCtRoute(
        string corridorKey,
        string targetSpotId,
        float targetX, float targetY, float targetZ)
    {
        if (IsProtectedApprovedARoute("CT", corridorKey))
        {
            return new List<RouteTransitionWaypoint>();
        }

        if (string.Equals(corridorKey, "MID_WINDOW", StringComparison.OrdinalIgnoreCase) &&
            string.Equals(targetSpotId, "mid_window_right_deep", StringComparison.OrdinalIgnoreCase))
        {
            return BuildWindowVentsTransitions(targetSpotId, targetX, targetY, targetZ);
        }

        if (string.Equals(corridorKey, "B_MARKET", StringComparison.OrdinalIgnoreCase))
        {
            return BuildMarketAndBSiteTransitions(targetSpotId, targetX, targetY, targetZ);
        }

        return new List<RouteTransitionWaypoint>();
    }

    public static List<RouteTransitionWaypoint> BuildTransitionsForTrRoute(
        string corridorKey,
        string targetSpotId,
        float targetX, float targetY, float targetZ)
    {
        return (corridorKey ?? string.Empty).ToUpperInvariant() switch
        {
            "A_RAMP" => BuildTrARampTransitions(targetSpotId, targetX, targetY, targetZ),
            "A_PALACE" => BuildTrAPalaceTransitions(targetSpotId, targetX, targetY, targetZ),
            "MID_TOP" => BuildTrTopMidTransitions(targetSpotId, targetX, targetY, targetZ),
            "MID_UNDERPASS" => BuildTrUnderpassTransitions(targetSpotId, targetX, targetY, targetZ),
            "B_APPS" => BuildTrBAppsTransitions(targetSpotId, targetX, targetY, targetZ),
            _ => new List<RouteTransitionWaypoint>(),
        };
    }

    private static List<RouteTransitionWaypoint> BuildTrARampTransitions(
        string targetSpotId, float targetX, float targetY, float targetZ)
    {
        var wps = new List<RouteTransitionWaypoint>
        {
            new()
            {
                Name = "t_spawn_ramp_exit",
                X = 1148.6f, Y = -989.1f, Z = -257.0f,
                NavMeshArea = 1154,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = -0.35f, ApproachDirY = -0.94f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_a_ramp_arch",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_a_ramp_arch",
                X = 733.2f, Y = -1174.4f, Z = -256.5f,
                NavMeshArea = 962,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.91f, ApproachDirY = -0.41f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_a_ramp_doorway",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_a_ramp_doorway",
                X = 722.0f, Y = -1440.0f, Z = -259.0f,
                NavMeshArea = 1242,
                TransitionType = TransitionWaypointType.DOORWAY,
                ApproachDirX = -0.04f, ApproachDirY = -0.99f, ApproachDirZ = 0f,
                ArrivalRadius = 32f, ExitRadius = 40f,
                MinimumForwardProgress = 8f, MaximumLateralError = 60f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_a_ramp_bend",
                RequiredClearance = 44f,
            },
            new()
            {
                Name = "t_a_ramp_bend",
                X = 692.0f, Y = -1516.8f, Z = -258.5f,
                NavMeshArea = 1244,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.71f, ApproachDirY = -0.70f, ApproachDirZ = 0f,
                ArrivalRadius = 84f, ExitRadius = 104f,
                MinimumForwardProgress = 8f, MaximumLateralError = 105f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_a_ramp_mid",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_a_ramp_mid",
                X = 500.0f, Y = -1555.0f, Z = -215.0f,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.98f, ApproachDirY = -0.20f, ApproachDirZ = 0.22f,
                ArrivalRadius = 80f, ExitRadius = 98f,
                MinimumForwardProgress = 8f, MaximumLateralError = 100f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_a_ramp_entry",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_a_ramp_entry",
                X = 320.0f, Y = -1590.0f, Z = -168.0f,
                NavMeshArea = 1133,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.98f, ApproachDirY = -0.20f, ApproachDirZ = 0.05f,
                ArrivalRadius = 72f, ExitRadius = 88f,
                MinimumForwardProgress = 8f, MaximumLateralError = 90f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = targetSpotId,
                RequiredClearance = 64f,
            },
        };

        if (string.Equals(targetSpotId, "a_default_plant_headshot", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(targetSpotId, "a_tetris_top_control", StringComparison.OrdinalIgnoreCase))
        {
            wps.Add(new()
            {
                Name = "a_tetris_corner_approach",
                X = -305.7f, Y = -1606.7f, Z = -168.0f,
                NavMeshArea = 1290,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = -1f, ApproachDirY = 0f, ApproachDirZ = 0f,
                ArrivalRadius = 64f, ExitRadius = 80f,
                MinimumForwardProgress = 8f, MaximumLateralError = 85f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = targetSpotId,
                RequiredClearance = 56f,
            });
        }

        bool isTetrisTop = string.Equals(targetSpotId, "a_tetris_top_control", StringComparison.OrdinalIgnoreCase);
        bool isRampWait = string.Equals(targetSpotId, "tr_a_ramp_staging_wait", StringComparison.OrdinalIgnoreCase);
        wps.Add(new()
        {
            Name = targetSpotId,
            X = targetX, Y = targetY, Z = targetZ,
            NavMeshArea = isTetrisTop ? 1185 : (isRampWait ? 1133 : 0),
            TransitionType = isTetrisTop ? TransitionWaypointType.STEP_UP : TransitionWaypointType.SITE_ENTRY,
            ApproachDirX = -0.5f, ApproachDirY = -0.86f, ApproachDirZ = 0f,
            ArrivalRadius = isTetrisTop ? 58f : 72f, ExitRadius = 88f,
            MinimumForwardProgress = 0f, MaximumLateralError = 95f,
            MovementAction = isTetrisTop ? TransitionMovementAction.STEP_UP_JUMP_PULSE : TransitionMovementAction.NONE,
            AllowJumpPulse = isTetrisTop,
            TimeoutSeconds = 3.5,
            NextWaypoint = string.Empty,
            RequiredClearance = 56f,
            ExpectedZDelta = isTetrisTop ? 114f : 0f,
            MinZDelta = -32f,
            MaxZDelta = 135f,
        });
        return wps;
    }

    private static List<RouteTransitionWaypoint> BuildTrAPalaceTransitions(
        string targetSpotId, float targetX, float targetY, float targetZ)
    {
        var wps = new List<RouteTransitionWaypoint>
        {
            new()
            {
                Name = "t_spawn_ramp_exit",
                X = 1148.6f, Y = -989.1f, Z = -257.0f,
                NavMeshArea = 1154,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = -0.35f, ApproachDirY = -0.94f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_a_ramp_arch",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_a_ramp_arch",
                X = 733.2f, Y = -1174.4f, Z = -256.5f,
                NavMeshArea = 962,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.91f, ApproachDirY = -0.41f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_a_ramp_doorway",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_a_ramp_doorway",
                X = 722.0f, Y = -1440.0f, Z = -259.0f,
                NavMeshArea = 1242,
                TransitionType = TransitionWaypointType.DOORWAY,
                ApproachDirX = -0.04f, ApproachDirY = -0.99f, ApproachDirZ = 0f,
                ArrivalRadius = 32f, ExitRadius = 40f,
                MinimumForwardProgress = 8f, MaximumLateralError = 60f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_a_ramp_bend",
                RequiredClearance = 44f,
            },
            new()
            {
                Name = "t_a_ramp_bend",
                X = 692.0f, Y = -1516.8f, Z = -258.5f,
                NavMeshArea = 1244,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.71f, ApproachDirY = -0.70f, ApproachDirZ = 0f,
                ArrivalRadius = 84f, ExitRadius = 104f,
                MinimumForwardProgress = 8f, MaximumLateralError = 105f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_palace_ramp_approach",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_palace_ramp_approach",
                X = 320.0f, Y = -1640.0f, Z = -168.0f,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.95f, ApproachDirY = -0.30f, ApproachDirZ = 0.20f,
                ArrivalRadius = 80f, ExitRadius = 98f,
                MinimumForwardProgress = 8f, MaximumLateralError = 100f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_palace_corridor_turn",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_palace_corridor_turn",
                X = 169.5f, Y = -1541.0f, Z = -171.3f,
                NavMeshArea = 1113,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.80f, ApproachDirY = 0.60f, ApproachDirZ = 0f,
                ArrivalRadius = 32f, ExitRadius = 48f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_palace_doorway_align",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_palace_doorway_align",
                X = 161.5f, Y = -1637.0f, Z = -168.0f,
                NavMeshArea = 1279,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.10f, ApproachDirY = -0.99f, ApproachDirZ = 0f,
                ArrivalRadius = 36f, ExitRadius = 52f,
                MinimumForwardProgress = 8f, MaximumLateralError = 90f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_palace_ramp_entry",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_palace_ramp_entry",
                X = 43.5f, Y = -1719.5f, Z = -164.0f,
                NavMeshArea = 1427,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.95f, ApproachDirY = -0.30f, ApproachDirZ = 0.08f,
                ArrivalRadius = 48f, ExitRadius = 64f,
                MinimumForwardProgress = 8f, MaximumLateralError = 85f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.5,
                NextWaypoint = "t_palace_box_step_1",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_palace_box_step_1",
                X = -13.5f, Y = -1761.0f, Z = -108.0f,
                NavMeshArea = 1496,
                TransitionType = TransitionWaypointType.STEP_UP,
                ApproachDirX = 0f, ApproachDirY = 0f, ApproachDirZ = 0f,
                ArrivalRadius = 32f, ExitRadius = 48f,
                MinimumForwardProgress = 4f, MaximumLateralError = 80f,
                MovementAction = TransitionMovementAction.STEP_UP_JUMP_PULSE,
                AllowJumpPulse = true,
                TimeoutSeconds = 4.5,
                NextWaypoint = "t_palace_box_step_2",
                RequiredClearance = 48f,
                ExpectedZDelta = 56f,
                MinZDelta = -16f,
                MaxZDelta = 80f,
            },
            new()
            {
                Name = "t_palace_box_step_2",
                X = 28.2f, Y = -1801.0f, Z = -60.0f,
                NavMeshArea = 1529,
                TransitionType = TransitionWaypointType.STEP_UP,
                ApproachDirX = 0f, ApproachDirY = 0f, ApproachDirZ = 0f,
                ArrivalRadius = 44f, ExitRadius = 60f,
                MinimumForwardProgress = 4f, MaximumLateralError = 80f,
                MovementAction = TransitionMovementAction.STEP_UP_JUMP_PULSE,
                AllowJumpPulse = true,
                TimeoutSeconds = 4.5,
                NextWaypoint = "t_palace_upper_entry",
                RequiredClearance = 48f,
                ExpectedZDelta = 48f,
                MinZDelta = -16f,
                MaxZDelta = 80f,
            },
            new()
            {
                Name = "t_palace_upper_entry",
                X = 10.2f, Y = -1864.0f, Z = -36.0f,
                NavMeshArea = 1591,
                TransitionType = TransitionWaypointType.STEP_UP,
                ApproachDirX = 0f, ApproachDirY = 0f, ApproachDirZ = 0f,
                ArrivalRadius = 48f, ExitRadius = 64f,
                MinimumForwardProgress = 4f, MaximumLateralError = 80f,
                MovementAction = TransitionMovementAction.STEP_UP_JUMP_PULSE,
                AllowJumpPulse = true,
                TimeoutSeconds = 4.5,
                NextWaypoint = "t_palace_stairs",
                RequiredClearance = 48f,
                ExpectedZDelta = 24f,
                MinZDelta = -16f,
                MaxZDelta = 64f,
            },
            new()
            {
                Name = "t_palace_stairs",
                X = -19.4f, Y = -1934.5f, Z = -36.0f,
                NavMeshArea = 1668,
                TransitionType = TransitionWaypointType.NARROW_PASSAGE,
                ApproachDirX = -0.28f, ApproachDirY = -0.96f, ApproachDirZ = 0.25f,
                ArrivalRadius = 68f, ExitRadius = 84f,
                MinimumForwardProgress = 6f, MaximumLateralError = 78f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = targetSpotId,
                RequiredClearance = 52f,
            },
            new()
            {
                Name = targetSpotId,
                X = targetX, Y = targetY, Z = targetZ,
                NavMeshArea = string.Equals(targetSpotId, "a_palace_deep_room", StringComparison.OrdinalIgnoreCase) ? 2082 : 1947,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = 0.35f, ApproachDirY = -0.93f, ApproachDirZ = 0f,
                ArrivalRadius = 72f, ExitRadius = 90f,
                MinimumForwardProgress = 0f, MaximumLateralError = 90f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = string.Empty,
                RequiredClearance = 56f,
            },
        };
        return wps;
    }

    private static List<RouteTransitionWaypoint> BuildTrTopMidTransitions(
        string targetSpotId, float targetX, float targetY, float targetZ)
    {
        var wps = new List<RouteTransitionWaypoint>
        {
            new()
            {
                Name = "t_mid_alley_drop",
                X = 1139.1f, Y = 224.0f, Z = -231.7f,
                NavMeshArea = 743,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = -0.30f, ApproachDirY = 0.95f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.0,
                NextWaypoint = "t_mid_alley_corner",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_mid_alley_corner",
                X = 910.7f, Y = 463.9f, Z = -254.0f,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.71f, ApproachDirY = 0.70f, ApproachDirZ = 0f,
                ArrivalRadius = 80f, ExitRadius = 96f,
                MinimumForwardProgress = 8f, MaximumLateralError = 100f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_top_mid_alley",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_top_mid_alley",
                X = 469.3f, Y = 461.6f, Z = -261.0f,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.99f, ApproachDirY = -0.02f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "mid_top_mid_boxes_entry",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = string.Equals(targetSpotId, "mid_top_mid_boxes", StringComparison.OrdinalIgnoreCase) ? targetSpotId : "mid_top_mid_boxes_entry",
                X = 368.0f, Y = -223.0f, Z = -167.7f,
                NavMeshArea = 63,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = -0.15f, ApproachDirY = -0.98f, ApproachDirZ = 0.14f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 0f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = string.Equals(targetSpotId, "mid_top_mid_boxes", StringComparison.OrdinalIgnoreCase) ? string.Empty : targetSpotId,
                RequiredClearance = 64f,
            },
        };

        if (!string.Equals(targetSpotId, "mid_top_mid_boxes", StringComparison.OrdinalIgnoreCase))
        {
            wps.Add(new()
            {
                Name = targetSpotId,
                X = targetX, Y = targetY, Z = targetZ,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = -0.82f, ApproachDirY = -0.57f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 0f, MaximumLateralError = 105f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.5,
                NextWaypoint = string.Empty,
                RequiredClearance = 64f,
            });
        }
        return wps;
    }

    private static List<RouteTransitionWaypoint> BuildTrUnderpassTransitions(
        string targetSpotId, float targetX, float targetY, float targetZ)
    {
        var wps = new List<RouteTransitionWaypoint>
        {
            new()
            {
                Name = "t_mid_alley_drop",
                X = 1139.1f, Y = 224.0f, Z = -231.7f,
                NavMeshArea = 743,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = -0.30f, ApproachDirY = 0.95f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.0,
                NextWaypoint = "t_mid_alley_corner",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_mid_alley_corner",
                X = 910.7f, Y = 463.9f, Z = -254.0f,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.71f, ApproachDirY = 0.70f, ApproachDirZ = 0f,
                ArrivalRadius = 80f, ExitRadius = 96f,
                MinimumForwardProgress = 8f, MaximumLateralError = 100f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_top_mid_alley",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_top_mid_alley",
                X = 469.3f, Y = 461.6f, Z = -261.0f,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.99f, ApproachDirY = -0.02f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_underpass_mid_boxes",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_underpass_mid_boxes",
                X = 368.0f, Y = -223.0f, Z = -167.7f,
                NavMeshArea = 63,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.15f, ApproachDirY = -0.99f, ApproachDirZ = 0.13f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_underpass_mid_ramp",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_underpass_mid_ramp",
                X = 138.2f, Y = -507.6f, Z = -169.4f,
                NavMeshArea = 102,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.63f, ApproachDirY = -0.78f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_underpass_mid_step",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_underpass_mid_step",
                X = -23.0f, Y = -586.5f, Z = -201.3f,
                NavMeshArea = 133,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = -0.82f, ApproachDirY = -0.57f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_underpass_mid_floor",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_underpass_mid_floor",
                X = -499.5f, Y = -600.0f, Z = -269.3f,
                NavMeshArea = 343,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.98f, ApproachDirY = -0.05f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_underpass_entry",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_underpass_entry",
                X = -950.0f, Y = -531.5f, Z = -260.0f,
                NavMeshArea = 715,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.82f, ApproachDirY = 0.57f, ApproachDirZ = -0.25f,
                ArrivalRadius = 64f, ExitRadius = 82f,
                MinimumForwardProgress = 6f, MaximumLateralError = 80f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = targetSpotId,
                RequiredClearance = 52f,
            },
            new()
            {
                Name = targetSpotId,
                X = targetX, Y = targetY, Z = targetZ,
                NavMeshArea = 0,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = -0.5f, ApproachDirY = 0.86f, ApproachDirZ = 0f,
                ArrivalRadius = 76f, ExitRadius = 95f,
                MinimumForwardProgress = 0f, MaximumLateralError = 100f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = string.Empty,
                RequiredClearance = 56f,
            },
        };
        return wps;
    }

    private static List<RouteTransitionWaypoint> BuildTrBAppsTransitions(
        string targetSpotId, float targetX, float targetY, float targetZ)
    {
        var wps = new List<RouteTransitionWaypoint>
        {
            new()
            {
                Name = "t_b_spawn_ledge_exit",
                X = 1136.0f, Y = 336.0f, Z = -258.5f,
                NavMeshArea = 786,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = 0.0f, ApproachDirY = 1.0f, ApproachDirZ = -0.25f,
                ArrivalRadius = 90f, ExitRadius = 110f,
                MinimumForwardProgress = 8f, MaximumLateralError = 110f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_b_spawn_arch_turn",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_b_spawn_arch_turn",
                X = 1047.1f, Y = 590.0f, Z = -258.5f,
                NavMeshArea = 754,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.35f, ApproachDirY = 0.94f, ApproachDirZ = 0f,
                ArrivalRadius = 36f, ExitRadius = 52f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_b_house_stairs_entry",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_b_house_stairs_entry",
                X = 951.1f, Y = 594.5f, Z = -251.0f,
                NavMeshArea = 641,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.75f, ApproachDirY = 0.66f, ApproachDirZ = 0f,
                ArrivalRadius = 40f, ExitRadius = 56f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_b_house_stairs_bot",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_b_house_stairs_bot",
                X = 833.8f, Y = 624.1f, Z = -210.0f,
                NavMeshArea = 574,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = -0.50f, ApproachDirY = 0.86f, ApproachDirZ = 0f,
                ArrivalRadius = 52f, ExitRadius = 68f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_b_apps_hall_east",
                RequiredClearance = 64f,
            },
            new()
            {
                Name = "t_b_apps_hall_east",
                X = 608.9f, Y = 623.0f, Z = -126.5f,
                NavMeshArea = 431,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -1.0f, ApproachDirY = 0.0f, ApproachDirZ = 0.30f,
                ArrivalRadius = 40f, ExitRadius = 56f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_b_apps_hall_north",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_b_apps_hall_north",
                X = 561.5f, Y = 804.0f, Z = -132.0f,
                NavMeshArea = 552,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.25f, ApproachDirY = 0.97f, ApproachDirZ = 0f,
                ArrivalRadius = 40f, ExitRadius = 56f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 4.0,
                NextWaypoint = "t_b_apps_hall_west",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_b_apps_hall_west",
                X = -207.2f, Y = 828.7f, Z = -132.5f,
                NavMeshArea = 399,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -1.0f, ApproachDirY = 0.03f, ApproachDirZ = 0f,
                ArrivalRadius = 44f, ExitRadius = 60f,
                MinimumForwardProgress = 8f, MaximumLateralError = 95f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 5.0,
                NextWaypoint = "t_b_house_stairs_mid",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_b_house_stairs_mid",
                X = -254.9f, Y = 643.1f, Z = -85.0f,
                NavMeshArea = 200,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.95f, ApproachDirY = -0.25f, ApproachDirZ = 0.14f,
                ArrivalRadius = 68f, ExitRadius = 86f,
                MinimumForwardProgress = 8f, MaximumLateralError = 85f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.5,
                NextWaypoint = "t_b_house_entry",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_b_house_entry",
                X = -260.5f, Y = 577.1f, Z = -77.0f,
                NavMeshArea = 146,
                TransitionType = TransitionWaypointType.DOORWAY,
                ApproachDirX = -0.99f, ApproachDirY = -0.05f, ApproachDirZ = 0f,
                ArrivalRadius = 68f, ExitRadius = 86f,
                MinimumForwardProgress = 8f, MaximumLateralError = 85f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = "t_b_apps_house_staging",
                RequiredClearance = 56f,
            },
            new()
            {
                Name = "t_b_apps_house_staging_approach",
                X = -764.4f, Y = 522.1f, Z = -77.0f,
                NavMeshArea = 524,
                TransitionType = TransitionWaypointType.NARROW_PASSAGE,
                ApproachDirX = -0.99f, ApproachDirY = -0.08f, ApproachDirZ = 0f,
                ArrivalRadius = 64f, ExitRadius = 82f,
                MinimumForwardProgress = 6f, MaximumLateralError = 75f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = string.Equals(targetSpotId, "tr_b_apps_house_staging", StringComparison.OrdinalIgnoreCase) ? targetSpotId : "t_b_apps_kitchen_entry_align",
                RequiredClearance = 52f,
            },
        };

        if (string.Equals(targetSpotId, "tr_b_apps_house_staging", StringComparison.OrdinalIgnoreCase))
        {
            wps.Add(new()
            {
                Name = targetSpotId,
                X = targetX, Y = targetY, Z = targetZ,
                NavMeshArea = 524,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = -0.99f, ApproachDirY = -0.08f, ApproachDirZ = 0f,
                ArrivalRadius = 72f, ExitRadius = 90f,
                MinimumForwardProgress = 0f, MaximumLateralError = 90f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 4.0,
                NextWaypoint = string.Empty,
                RequiredClearance = 56f,
            });
            return wps;
        }

        wps.Add(new()
        {
            Name = "t_b_apps_kitchen_entry_align",
            X = -945.0f, Y = 564.0f, Z = -77.0f,
            NavMeshArea = 611,
            TransitionType = TransitionWaypointType.FLAT_PORTAL,
            ApproachDirX = -0.93f, ApproachDirY = 0.37f, ApproachDirZ = 0f,
            ArrivalRadius = 32f, ExitRadius = 48f,
            MinimumForwardProgress = 6f, MaximumLateralError = 75f,
            MovementAction = TransitionMovementAction.NONE,
            TimeoutSeconds = 4.0,
            NextWaypoint = "t_b_apps_kitchen_doorway",
            RequiredClearance = 44f,
        });

        wps.Add(new()
        {
            Name = "t_b_apps_kitchen_doorway",
            X = -985.0f, Y = 563.8f, Z = -76.0f,
            NavMeshArea = 749,
            TransitionType = TransitionWaypointType.STEP_UP,
            ApproachDirX = 0f, ApproachDirY = 0f, ApproachDirZ = 0f,
            ArrivalRadius = 32f, ExitRadius = 48f,
            MinimumForwardProgress = 6f, MaximumLateralError = 52f,
            MovementAction = TransitionMovementAction.STEP_UP_JUMP_PULSE,
            AllowJumpPulse = true,
            TimeoutSeconds = 4.5,
            NextWaypoint = "t_b_apps_kitchen_hall",
            RequiredClearance = 36f,
            ExpectedZDelta = 5.6f,
            MinZDelta = -16f,
            MaxZDelta = 32f,
        });
        wps.Add(new()
        {
            Name = "t_b_apps_kitchen_hall",
            X = -1045.0f, Y = 632.5f, Z = -76.0f,
            NavMeshArea = 794,
            TransitionType = TransitionWaypointType.NARROW_PASSAGE,
            ApproachDirX = -0.94f, ApproachDirY = 0.35f, ApproachDirZ = 0f,
            ArrivalRadius = 72f, ExitRadius = 90f,
            MinimumForwardProgress = 6f, MaximumLateralError = 85f,
            MovementAction = TransitionMovementAction.NONE,
            TimeoutSeconds = 4.5,
            NextWaypoint = string.Equals(targetSpotId, "tr_b_apps_kitchen_control", StringComparison.OrdinalIgnoreCase) ? targetSpotId : "t_b_apps_kitchen_wp",
            RequiredClearance = 44f,
        });

        if (!string.Equals(targetSpotId, "tr_b_apps_kitchen_control", StringComparison.OrdinalIgnoreCase))
        {
            wps.Add(new()
            {
                Name = "t_b_apps_kitchen_wp",
                X = -1111.7f, Y = 687.0f, Z = -80.0f,
                NavMeshArea = 874,
                TransitionType = TransitionWaypointType.DOORWAY,
                ApproachDirX = -0.90f, ApproachDirY = 0.43f, ApproachDirZ = 0f,
                ArrivalRadius = 60f, ExitRadius = 78f,
                MinimumForwardProgress = 6f, MaximumLateralError = 72f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = targetSpotId,
                RequiredClearance = 48f,
            });
        }

        bool isBSiteSpot = targetSpotId.StartsWith("b_", StringComparison.OrdinalIgnoreCase) ||
                           targetSpotId.StartsWith("tr_b_forest", StringComparison.OrdinalIgnoreCase);
        if (isBSiteSpot)
        {
            wps.Add(new()
            {
                Name = "t_b_apps_window_exit",
                X = -1590.2f, Y = 708.2f, Z = -48.0f,
                NavMeshArea = 1364,
                TransitionType = TransitionWaypointType.STEP_DOWN,
                ApproachDirX = -0.99f, ApproachDirY = 0.04f, ApproachDirZ = 0f,
                ArrivalRadius = 60f, ExitRadius = 78f,
                MinimumForwardProgress = 6f, MaximumLateralError = 72f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.5,
                NextWaypoint = targetSpotId,
                RequiredClearance = 48f,
            });
        }

        wps.Add(new()
        {
            Name = targetSpotId,
            X = targetX, Y = targetY, Z = targetZ,
            NavMeshArea = 0,
            TransitionType = TransitionWaypointType.SITE_ENTRY,
            ApproachDirX = -0.95f, ApproachDirY = -0.30f, ApproachDirZ = 0f,
            ArrivalRadius = 72f, ExitRadius = 90f,
            MinimumForwardProgress = 0f, MaximumLateralError = 95f,
            MovementAction = TransitionMovementAction.NONE,
            TimeoutSeconds = 4.0,
            NextWaypoint = string.Empty,
            RequiredClearance = 56f,
        });
        return wps;
    }

    public static List<RouteTransitionWaypoint> BuildWindowVentsTransitions(
        string targetSpotId, float targetX, float targetY, float targetZ)
    {
        return new List<RouteTransitionWaypoint>
        {
            new()
            {
                Name = "ct_window_ramp_approach",
                X = -1545.0f, Y = -990.0f, Z = -203.0f,
                NavMeshArea = 1493,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = 0.99f, ApproachDirY = 0.14f, ApproachDirZ = 0.0f,
                ArrivalRadius = 46f, ExitRadius = 56f,
                MinimumForwardProgress = 8f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_window_step_align",
                RequiredClearance = 64f,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_window_step_align",
                X = -1494.0f, Y = -985.0f, Z = -207.0f,
                NavMeshArea = 1493,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = 0.99f, ApproachDirY = 0.11f, ApproachDirZ = 0.0f,
                ArrivalRadius = 32f, ExitRadius = 40f,
                MinimumForwardProgress = 6f, MaximumLateralError = 38f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 1.8,
                NextWaypoint = "ct_window_step_up_ledge",
                RequiredClearance = 48f,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_window_step_up_ledge",
                X = -1448.0f, Y = -980.0f, Z = -164.0f,
                NavMeshArea = 1419,
                TransitionType = TransitionWaypointType.STEP_UP,
                ApproachDirX = 0.99f, ApproachDirY = 0.11f, ApproachDirZ = 0.45f,
                ArrivalRadius = 40f, ExitRadius = 48f,
                MinimumForwardProgress = 8f, MaximumLateralError = 36f,
                MovementAction = TransitionMovementAction.STEP_UP_JUMP_PULSE,
                TimeoutSeconds = 1.8,
                NextWaypoint = "ct_window_vent_entry",
                RequiredClearance = 44f,
                ExpectedZDelta = 39.6f, MinZDelta = 14.0f, MaxZDelta = 58.0f,
                AllowJumpPulse = true,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_window_vent_entry",
                X = -1385.0f, Y = -974.0f, Z = -164.0f,
                NavMeshArea = 1339,
                TransitionType = TransitionWaypointType.VENT_ENTRY,
                ApproachDirX = 1.0f, ApproachDirY = 0.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 28f, ExitRadius = 36f,
                MinimumForwardProgress = 6f, MaximumLateralError = 22f,
                MovementAction = TransitionMovementAction.CLEAR_VENT_OBSTACLE,
                TimeoutSeconds = 1.8,
                NextWaypoint = "ct_window_vents",
                RequiredClearance = 36f,
                MinZDelta = -10.0f, MaxZDelta = 18.0f,
                AllowJumpPulse = false,
                UseExactPortalSteering = true,
                RequireCrouch = true,
            },
            new()
            {
                Name = "ct_window_vents",
                X = -1337.0f, Y = -974.0f, Z = -164.0f,
                NavMeshArea = 1326,
                TransitionType = TransitionWaypointType.NARROW_PASSAGE,
                ApproachDirX = 1.0f, ApproachDirY = 0.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 22f, ExitRadius = 30f,
                MinimumForwardProgress = 6f, MaximumLateralError = 16f,
                MovementAction = TransitionMovementAction.CLEAR_VENT_OBSTACLE,
                TimeoutSeconds = 2.0,
                NextWaypoint = "ct_window_vent_exit",
                RequiredClearance = 18f,
                UseExactPortalSteering = true,
                RequireCrouch = true,
            },
            new()
            {
                Name = "ct_window_vent_exit",
                X = -1280.0f, Y = -974.0f, Z = -164.0f,
                NavMeshArea = 1226,
                TransitionType = TransitionWaypointType.VENT_EXIT,
                ApproachDirX = 1.0f, ApproachDirY = 0.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 32f, ExitRadius = 40f,
                MinimumForwardProgress = 8f, MaximumLateralError = 28f,
                MovementAction = TransitionMovementAction.CLEAR_VENT_OBSTACLE,
                TimeoutSeconds = 2.0,
                NextWaypoint = "ct_window_nest_entry",
                RequiredClearance = 42f,
                UseExactPortalSteering = true,
                RequireCrouch = true,
            },
            new()
            {
                Name = "ct_window_nest_entry",
                X = -1205.0f, Y = -895.0f, Z = -164.0f,
                NavMeshArea = 1120,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = 0.68f, ApproachDirY = 0.73f, ApproachDirZ = 0.0f,
                ArrivalRadius = 52f, ExitRadius = 60f,
                MinimumForwardProgress = 10f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 2.0,
                NextWaypoint = targetSpotId,
                RequiredClearance = 75f,
                UseExactPortalSteering = false,
            },
            new()
            {
                Name = targetSpotId,
                X = targetX, Y = targetY, Z = targetZ,
                NavMeshArea = 975,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = 0.13f, ApproachDirY = 0.99f, ApproachDirZ = 0.0f,
                ArrivalRadius = 72f, ExitRadius = 90f,
                MinimumForwardProgress = 0f, MaximumLateralError = 96f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.0,
                NextWaypoint = string.Empty,
                RequiredClearance = 75f,
                UseExactPortalSteering = false,
            },
        };
    }

    public static List<RouteTransitionWaypoint> BuildMarketAndBSiteTransitions(
        string targetSpotId, float targetX, float targetY, float targetZ)
    {
        var wps = new List<RouteTransitionWaypoint>
        {
            new()
            {
                Name = "ct_spawn_b_exit_ramp",
                X = -1625.0f, Y = -910.0f, Z = -176.0f,
                NavMeshArea = 1494,
                TransitionType = TransitionWaypointType.RAMP,
                ApproachDirX = -0.15f, ApproachDirY = 0.99f, ApproachDirZ = 0.15f,
                ArrivalRadius = 64f, ExitRadius = 72f,
                MinimumForwardProgress = 12f, MaximumLateralError = 72f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 4.0,
                NextWaypoint = "ct_market_entry",
                RequiredClearance = 96f,
                UseExactPortalSteering = false,
            },
            new()
            {
                Name = "ct_market_entry",
                X = -1620.0f, Y = -680.0f, Z = -164.0f,
                NavMeshArea = 1445,
                TransitionType = TransitionWaypointType.DOORWAY,
                ApproachDirX = 0.0f, ApproachDirY = 1.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 56f, ExitRadius = 64f,
                MinimumForwardProgress = 12f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.0,
                NextWaypoint = "ct_market_corridor_west",
                RequiredClearance = 80f,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_market_corridor_west",
                X = -1860.0f, Y = -654.0f, Z = -164.0f,
                NavMeshArea = 1706,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.99f, ApproachDirY = 0.11f, ApproachDirZ = 0.0f,
                ArrivalRadius = 56f, ExitRadius = 64f,
                MinimumForwardProgress = 12f, MaximumLateralError = 56f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_market_back_hall",
                RequiredClearance = 64f,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_market_back_hall",
                X = -2180.0f, Y = -630.0f, Z = -164.0f,
                NavMeshArea = 2171,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.99f, ApproachDirY = 0.08f, ApproachDirZ = 0.0f,
                ArrivalRadius = 56f, ExitRadius = 64f,
                MinimumForwardProgress = 12f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_market_door_entry",
                RequiredClearance = 70f,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_market_door_entry",
                X = -2295.0f, Y = -555.0f, Z = -164.0f,
                NavMeshArea = 2256,
                TransitionType = TransitionWaypointType.DOORWAY,
                ApproachDirX = -0.35f, ApproachDirY = 0.94f, ApproachDirZ = 0.0f,
                ArrivalRadius = 50f, ExitRadius = 58f,
                MinimumForwardProgress = 10f, MaximumLateralError = 52f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_market_door_exit",
                RequiredClearance = 58f,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_market_door_exit",
                X = -2327.5f, Y = -282.0f, Z = -164.0f,
                NavMeshArea = 2251,
                TransitionType = TransitionWaypointType.NARROW_PASSAGE,
                ApproachDirX = 0.0f, ApproachDirY = 1.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 44f, ExitRadius = 52f,
                MinimumForwardProgress = 10f, MaximumLateralError = 36f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_site_entry",
                RequiredClearance = 51f,
                UseExactPortalSteering = true,
            },
            new()
            {
                Name = "ct_b_site_entry",
                X = -2330.0f, Y = -145.0f, Z = -164.0f,
                NavMeshArea = 2225,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = 0.0f, ApproachDirY = 1.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 56f, ExitRadius = 64f,
                MinimumForwardProgress = 10f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 2.5,
                NextWaypoint = targetSpotId,
                RequiredClearance = 72f,
                UseExactPortalSteering = true,
            },
        };

        if (string.Equals(targetSpotId, "b_forest_bench_hold_apps", StringComparison.OrdinalIgnoreCase))
        {
            wps[^1] = new()
            {
                Name = wps[^1].Name, X = wps[^1].X, Y = wps[^1].Y, Z = wps[^1].Z,
                NavMeshArea = wps[^1].NavMeshArea, TransitionType = wps[^1].TransitionType,
                ApproachDirX = wps[^1].ApproachDirX, ApproachDirY = wps[^1].ApproachDirY, ApproachDirZ = 0f,
                ArrivalRadius = wps[^1].ArrivalRadius, ExitRadius = wps[^1].ExitRadius,
                MinimumForwardProgress = wps[^1].MinimumForwardProgress, MaximumLateralError = wps[^1].MaximumLateralError,
                MovementAction = TransitionMovementAction.NONE, TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_bench_alley_approach", RequiredClearance = 72f,
                UseExactPortalSteering = true,
            };
            wps.Add(new()
            {
                Name = "ct_b_bench_alley_approach",
                X = -2342.0f, Y = 94.0f, Z = -164.0f,
                NavMeshArea = 2169,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.05f, ApproachDirY = 0.99f, ApproachDirZ = 0.0f,
                ArrivalRadius = 48f, ExitRadius = 56f,
                MinimumForwardProgress = 10f, MaximumLateralError = 52f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_bench_back_corner",
                RequiredClearance = 68f,
                UseExactPortalSteering = true,
            });
            wps.Add(new()
            {
                Name = "ct_b_bench_back_corner",
                X = -2516.0f, Y = 164.0f, Z = -164.0f,
                NavMeshArea = 2401,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = -0.92f, ApproachDirY = 0.39f, ApproachDirZ = 0.0f,
                ArrivalRadius = 46f, ExitRadius = 54f,
                MinimumForwardProgress = 10f, MaximumLateralError = 48f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_bench_final_approach",
                RequiredClearance = 60f,
                UseExactPortalSteering = true,
            });
            wps.Add(new()
            {
                Name = "ct_b_bench_final_approach",
                X = -2585.0f, Y = 200.0f, Z = -163.0f,
                NavMeshArea = 2432,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = -0.88f, ApproachDirY = 0.46f, ApproachDirZ = 0.0f,
                ArrivalRadius = 46f, ExitRadius = 54f,
                MinimumForwardProgress = 8f, MaximumLateralError = 48f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 2.5,
                NextWaypoint = targetSpotId,
                RequiredClearance = 64f,
                UseExactPortalSteering = true,
            });
            wps.Add(new()
            {
                Name = targetSpotId,
                X = targetX, Y = targetY, Z = targetZ,
                NavMeshArea = 2431,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = 0.42f, ApproachDirY = 0.90f, ApproachDirZ = 0.0f,
                ArrivalRadius = 72f, ExitRadius = 90f,
                MinimumForwardProgress = 0f, MaximumLateralError = 96f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.0,
                NextWaypoint = string.Empty,
                RequiredClearance = 72f,
                UseExactPortalSteering = true,
            });
            return wps;
        }

        if (string.Equals(targetSpotId, "b_van_behind_apps_hold", StringComparison.OrdinalIgnoreCase))
        {
            wps[^1] = new()
            {
                Name = wps[^1].Name, X = wps[^1].X, Y = wps[^1].Y, Z = wps[^1].Z,
                NavMeshArea = wps[^1].NavMeshArea, TransitionType = wps[^1].TransitionType,
                ApproachDirX = wps[^1].ApproachDirX, ApproachDirY = wps[^1].ApproachDirY, ApproachDirZ = 0f,
                ArrivalRadius = wps[^1].ArrivalRadius, ExitRadius = wps[^1].ExitRadius,
                MinimumForwardProgress = wps[^1].MinimumForwardProgress, MaximumLateralError = wps[^1].MaximumLateralError,
                MovementAction = TransitionMovementAction.NONE, TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_site_van_lane", RequiredClearance = 72f,
                UseExactPortalSteering = true,
            };
            wps.Add(new()
            {
                Name = "ct_b_site_van_lane",
                X = -2335.0f, Y = 175.0f, Z = -164.0f,
                NavMeshArea = 2161,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = 0.0f, ApproachDirY = 1.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 56f, ExitRadius = 64f,
                MinimumForwardProgress = 12f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_site_van_corner",
                RequiredClearance = 80f,
                UseExactPortalSteering = true,
            });
            wps.Add(new()
            {
                Name = "ct_b_site_van_corner",
                X = -2335.0f, Y = 445.0f, Z = -164.0f,
                NavMeshArea = 2207,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = 0.0f, ApproachDirY = 1.0f, ApproachDirZ = 0.0f,
                ArrivalRadius = 56f, ExitRadius = 64f,
                MinimumForwardProgress = 12f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_site_van_approach",
                RequiredClearance = 80f,
                UseExactPortalSteering = true,
            });
            wps.Add(new()
            {
                Name = "ct_b_site_van_approach",
                X = -2162.5f, Y = 498.0f, Z = -164.0f,
                NavMeshArea = 2064,
                TransitionType = TransitionWaypointType.FLAT_PORTAL,
                ApproachDirX = 0.96f, ApproachDirY = 0.28f, ApproachDirZ = 0.0f,
                ArrivalRadius = 56f, ExitRadius = 64f,
                MinimumForwardProgress = 12f, MaximumLateralError = 64f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 2.5,
                NextWaypoint = "ct_b_van_under_apps_entry",
                RequiredClearance = 80f,
                UseExactPortalSteering = true,
            });
            wps.Add(new()
            {
                Name = "ct_b_van_under_apps_entry",
                X = -2020.0f, Y = 589.0f, Z = -164.0f,
                NavMeshArea = 1907,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = 0.85f, ApproachDirY = 0.53f, ApproachDirZ = 0.0f,
                ArrivalRadius = 64f, ExitRadius = 76f,
                MinimumForwardProgress = 10f, MaximumLateralError = 72f,
                MovementAction = TransitionMovementAction.ALIGN_CORRIDOR,
                TimeoutSeconds = 3.0,
                NextWaypoint = targetSpotId,
                RequiredClearance = 80f,
                UseExactPortalSteering = true,
            });
            // Nota geométrica: (-1981.9, 702.6, -48.0) projeta na área 1930 (sacada de Apps one-way drop);
            // mantemos o identificador e coordenadas originais imutáveis, porém marcando que o approach alcançável
            // do subgrafo B Site pelo Market conclui em ct_b_van_under_apps_entry (área 1907, 119u XY).
            wps.Add(new()
            {
                Name = targetSpotId,
                X = targetX, Y = targetY, Z = targetZ,
                NavMeshArea = 1930,
                TransitionType = TransitionWaypointType.SITE_ENTRY,
                ApproachDirX = 0.32f, ApproachDirY = 0.95f, ApproachDirZ = 0.0f,
                ArrivalRadius = 125f, ExitRadius = 135f,
                MinimumForwardProgress = 0f, MaximumLateralError = 125f,
                MovementAction = TransitionMovementAction.NONE,
                TimeoutSeconds = 3.0,
                NextWaypoint = string.Empty,
                RequiredClearance = 75f,
                UseExactPortalSteering = false,
                IsFinalApproachReachable = false,
            });
            return wps;
        }

        // Demais spots B allowlisted (e.g. b_short_pillar_hold_apps, b_site_default_plant_box, ct_b_edward_under_apps, ct_b_empty_pillar_jail)
        wps.Add(new()
        {
            Name = targetSpotId,
            X = targetX, Y = targetY, Z = targetZ,
            NavMeshArea = 0,
            TransitionType = TransitionWaypointType.SITE_ENTRY,
            ApproachDirX = 0.5f, ApproachDirY = 0.86f, ApproachDirZ = 0.0f,
            ArrivalRadius = 72f, ExitRadius = 90f,
            MinimumForwardProgress = 0f, MaximumLateralError = 110f,
            MovementAction = TransitionMovementAction.NONE,
            TimeoutSeconds = 3.5,
            NextWaypoint = string.Empty,
            RequiredClearance = 75f,
            UseExactPortalSteering = false,
        });
        return wps;
    }
}

public enum StepUpPulseState
{
    WAITING_FOR_ALIGNMENT,
    READY_TO_PULSE,
    PULSE_REQUESTED,
    PULSE_APPLIED,
    ASCENT_IN_PROGRESS,
    Z_GAIN_CONFIRMED,
    STEP_COMPLETED,
    PULSE_FAILED
}

/// <summary>
/// Executor localizado das transições geométricas para um único bot canary.
/// Controla apenas o portal atual e emite eventos de movimento somente nos pontos contratuais.
/// </summary>
public sealed class GeometricTransitionExecutor
{
    public const string EventTransitionEntry = "TRANSITION_ENTRY";
    public const string EventSubwaypointChange = "SUBWAYPOINT_CHANGE";
    public const string EventLocalizedAction = "LOCALIZED_ACTION";
    public const string EventTransitionExit = "TRANSITION_EXIT";
    public const string EventTransitionFallback = "TRANSITION_FALLBACK";

    private readonly List<TransitionExecutionEvent> _events = new();
    public IReadOnlyList<TransitionExecutionEvent> Events => _events;

    public int CommandDispatchCount { get; private set; }
    public int JumpPulsesIssued { get; private set; }
    public int ContinuousJumpViolations { get; private set; }
    public int LastJumpPulseTick { get; private set; } = -9999;
    public int LastAttackPulseTick { get; private set; } = -9999;
    public bool StepUpJumpInProgress => _stepUpJumpInProgress;

    public StepUpPulseState PulseState { get; private set; } = StepUpPulseState.WAITING_FOR_ALIGNMENT;
    public int PulseRequestsOnCurrentWp { get; private set; }
    public int PulseApplicationsOnCurrentWp { get; private set; }
    public bool LastPulseWasApplied { get; private set; }
    public bool ObservedZGainOnCurrentWp { get; private set; }
    public bool GroundRecoveredSinceLastPulse { get; private set; } = true;

    private bool _entryDispatched;
    private bool _stepUpJumpInProgress;
    private int _stepUpJumpStartTick = -1;
    private float _stepUpJumpStartZ;
    private int _stepUpAttemptsOnCurrentWp;
    private bool _exitDispatched;
    private double _stepStartSeconds = -1.0;
    private float _lastEvalZ = float.NaN;
    private int _stableGroundTicks;

    public void Reset()
    {
        _events.Clear();
        CommandDispatchCount = 0;
        JumpPulsesIssued = 0;
        ContinuousJumpViolations = 0;
        LastJumpPulseTick = -9999;
        LastAttackPulseTick = -9999;
        PulseState = StepUpPulseState.WAITING_FOR_ALIGNMENT;
        PulseRequestsOnCurrentWp = 0;
        PulseApplicationsOnCurrentWp = 0;
        LastPulseWasApplied = false;
        ObservedZGainOnCurrentWp = false;
        GroundRecoveredSinceLastPulse = true;
        _entryDispatched = false;
        _stepUpJumpInProgress = false;
        _stepUpJumpStartTick = -1;
        _stepUpJumpStartZ = 0f;
        _stepUpAttemptsOnCurrentWp = 0;
        _exitDispatched = false;
        _stepStartSeconds = -1.0;
        _lastEvalZ = float.NaN;
        _stableGroundTicks = 0;
    }

    public void NotifyJumpPulseApplied(int tick, bool inJumpObserved = true)
    {
        if (!inJumpObserved)
        {
            return;
        }
        LastPulseWasApplied = true;
        PulseApplicationsOnCurrentWp++;
        if (PulseState == StepUpPulseState.PULSE_REQUESTED)
        {
            PulseState = StepUpPulseState.PULSE_APPLIED;
        }
    }

    public static bool IsJumpTransitionTypeAllowed(TransitionWaypointType type) =>
        type == TransitionWaypointType.STEP_UP || type == TransitionWaypointType.VENT_ENTRY;

    public static bool CanEmitJumpPulseNow(
        RouteTransitionWaypoint wp,
        float botX, float botY, float botZ,
        int currentTick,
        int lastJumpTick,
        int attemptsThisWp,
        bool teammateBlocking,
        bool exitPathValid,
        out string rejectReason,
        bool isGrounded = true)
    {
        rejectReason = "OK";
        if (!IsJumpTransitionTypeAllowed(wp.TransitionType) || !wp.AllowJumpPulse)
        {
            rejectReason = "UNAUTHORIZED_TRANSITION_TYPE";
            return false;
        }
        if (attemptsThisWp >= 2)
        {
            rejectReason = "MAX_TWO_ATTEMPTS_REACHED";
            return false;
        }
        if (!isGrounded)
        {
            rejectReason = "NOT_GROUNDED";
            return false;
        }
        if ((currentTick - lastJumpTick) < 44) // ~0.69s cooldown entre pulsos a 64Hz
        {
            rejectReason = "COOLDOWN_ACTIVE";
            return false;
        }
        if (teammateBlocking)
        {
            rejectReason = "TEAMMATE_BLOCKING";
            return false;
        }
        if (!exitPathValid)
        {
            rejectReason = "INVALID_EXIT_PATH";
            return false;
        }

        float dz = wp.Z - botZ;
        if (dz < wp.MinZDelta || dz > wp.MaxZDelta)
        {
            rejectReason = $"Z_DELTA_OUT_OF_RANGE:{dz:F1}";
            return false;
        }

        float dx = wp.X - botX;
        float dy = wp.Y - botY;
        float dist2D = MathF.Sqrt(dx * dx + dy * dy);
        if (dist2D > (wp.ArrivalRadius + 36f))
        {
            rejectReason = $"OUTSIDE_ACTIVATION_RADIUS:{dist2D:F1}";
            return false;
        }

        float appLen = MathF.Sqrt(wp.ApproachDirX * wp.ApproachDirX + wp.ApproachDirY * wp.ApproachDirY);
        if (appLen > 0.01f && dist2D > 1.0f)
        {
            float dot = ((dx / dist2D) * (wp.ApproachDirX / appLen)) + ((dy / dist2D) * (wp.ApproachDirY / appLen));
            if (dot < 0.55f)
            {
                rejectReason = $"MISALIGNED_APPROACH:{dot:F2}";
                return false;
            }
        }

        return true;
    }

    public TransitionStepEvaluation EvaluateStep(
        int roundId,
        int tick,
        double elapsedSeconds,
        IReadOnlyList<RouteTransitionWaypoint> transitions,
        ref int currentIndex,
        float x, float y, float z,
        double speed2D,
        bool teammateBlocking,
        bool exitPathValid,
        NavMeshGraph? navMesh,
        bool isGrounded = true)
    {
        if (transitions == null || transitions.Count == 0 || currentIndex >= transitions.Count)
        {
            return new TransitionStepEvaluation { Active = false };
        }

        var wp = transitions[currentIndex];
        if (_stepStartSeconds < 0.0)
        {
            _stepStartSeconds = elapsedSeconds;
        }

        if (!float.IsNaN(_lastEvalZ) && MathF.Abs(z - _lastEvalZ) <= 0.6f)
        {
            _stableGroundTicks++;
        }
        else
        {
            _stableGroundTicks = 0;
        }
        _lastEvalZ = z;
        bool effectiveGrounded = isGrounded && (_stepUpAttemptsOnCurrentWp == 0 || _stableGroundTicks >= 2);
        if (effectiveGrounded && !_stepUpJumpInProgress && _stepUpAttemptsOnCurrentWp > 0)
        {
            GroundRecoveredSinceLastPulse = true;
        }

        // Verifica resultado do pulso de STEP_UP se houver um em curso
        if (_stepUpJumpInProgress)
        {
            float gainedZ = z - _stepUpJumpStartZ;
            int ticksSincePulse = tick - _stepUpJumpStartTick;
            if (LastPulseWasApplied && gainedZ > 2.0f && PulseState < StepUpPulseState.ASCENT_IN_PROGRESS)
            {
                PulseState = StepUpPulseState.ASCENT_IN_PROGRESS;
            }
            if (gainedZ >= 16.0f && z >= wp.Z - 16.0f)
            {
                ObservedZGainOnCurrentWp = true;
                PulseState = StepUpPulseState.Z_GAIN_CONFIRMED;
                _stepUpJumpInProgress = false;
            }
            else if (ticksSincePulse >= 42) // ~0.65s pós-pulso sem ganho suficiente de Z
            {
                _stepUpJumpInProgress = false;
                PulseState = StepUpPulseState.PULSE_FAILED;
                if (_stepUpAttemptsOnCurrentWp >= 2)
                {
                    RecordEvent(roundId, tick, EventTransitionFallback, wp, "STEP_UP_RETRY_EXHAUSTED", gainedZ, false);
                    return new TransitionStepEvaluation
                    {
                        Active = false,
                        EmitCommand = true,
                        CommandEventType = EventTransitionFallback,
                        ShouldReturnAuthority = true,
                        ReturnAuthorityReason = "STEP_UP_RETRY_EXHAUSTED",
                        CurrentWaypoint = wp
                    };
                }
            }
        }

        bool emitCmd = false;
        string cmdType = string.Empty;
        if (!_entryDispatched)
        {
            _entryDispatched = true;
            emitCmd = true;
            cmdType = EventTransitionEntry;
            RecordEvent(roundId, tick, EventTransitionEntry, wp, wp.MovementAction.ToString(), wp.Z - z, false);
        }

        // Checa chegada e avanço estrito do sub-waypoint atual (sem usar raio genérico de 110u)
        double dx = wp.X - x;
        double dy = wp.Y - y;
        double dzAbs = Math.Abs(wp.Z - z);
        double dist2D = Math.Sqrt(dx * dx + dy * dy);
        double dist3D = Math.Sqrt(dx * dx + dy * dy + dzAbs * dzAbs);

        bool areaMatched = true;
        if (navMesh != null && wp.NavMeshArea > 0 && wp.TransitionType == TransitionWaypointType.STEP_UP)
        {
            var proj = navMesh.ProjectPoint(x, y, z, 40f);
            // Para STEP_UP, só considera concluído se subiu fisicamente para perto do plano Z superior e atingiu a área esperada
            areaMatched = proj.AreaId == wp.NavMeshArea || z >= (wp.Z - 14.0f);
        }

        bool wpReached = wp.IsFinalApproachReachable
            ? (dist2D <= wp.ArrivalRadius && dzAbs <= 28.0 && areaMatched)
            : (dist2D <= wp.ArrivalRadius);

        if (wpReached && currentIndex < transitions.Count - 1)
        {
            if (wp.MovementAction == TransitionMovementAction.STEP_UP_JUMP_PULSE)
            {
                PulseState = StepUpPulseState.STEP_COMPLETED;
            }
            currentIndex++;
            _stepUpJumpInProgress = false;
            _stepUpAttemptsOnCurrentWp = 0;
            PulseRequestsOnCurrentWp = 0;
            PulseApplicationsOnCurrentWp = 0;
            LastPulseWasApplied = false;
            ObservedZGainOnCurrentWp = false;
            GroundRecoveredSinceLastPulse = true;
            _stableGroundTicks = 0;
            PulseState = StepUpPulseState.WAITING_FOR_ALIGNMENT;
            _stepStartSeconds = elapsedSeconds;
            var nextWp = transitions[currentIndex];
            RecordEvent(roundId, tick, EventSubwaypointChange, nextWp, nextWp.MovementAction.ToString(), nextWp.Z - z, false);
            return new TransitionStepEvaluation
            {
                Active = true,
                EmitCommand = true,
                CommandEventType = EventSubwaypointChange,
                SubwaypointAdvanced = true,
                CurrentWaypoint = nextWp,
            };
        }

        if (wpReached && currentIndex == transitions.Count - 1)
        {
            if (wp.MovementAction == TransitionMovementAction.STEP_UP_JUMP_PULSE)
            {
                PulseState = StepUpPulseState.STEP_COMPLETED;
            }
            if (!_exitDispatched)
            {
                _exitDispatched = true;
                RecordEvent(roundId, tick, EventTransitionExit, wp, "TRANSITION_COMPLETED", wp.Z - z, false);
            }
            return new TransitionStepEvaluation
            {
                Active = true,
                EmitCommand = true,
                CommandEventType = EventTransitionExit,
                TransitionCompleted = true,
                CurrentWaypoint = wp,
            };
        }

        // Verifica timeout do sub-waypoint STEP_UP (após exaustão de tentativas ou limite absoluto)
        if (wp.TransitionType == TransitionWaypointType.STEP_UP &&
            !_stepUpJumpInProgress &&
            ((_stepUpAttemptsOnCurrentWp >= 2 && (elapsedSeconds - _stepStartSeconds) > wp.TimeoutSeconds) ||
             (elapsedSeconds - _stepStartSeconds) > (wp.TimeoutSeconds + 2.5)))
        {
            PulseState = StepUpPulseState.PULSE_FAILED;
            RecordEvent(roundId, tick, EventTransitionFallback, wp, "STEP_UP_RETRY_EXHAUSTED", wp.Z - z, false);
            return new TransitionStepEvaluation
            {
                Active = false,
                EmitCommand = true,
                CommandEventType = EventTransitionFallback,
                ShouldReturnAuthority = true,
                ReturnAuthorityReason = "STEP_UP_RETRY_EXHAUSTED",
                CurrentWaypoint = wp
            };
        }

        // Avalia ação localizada de STEP_UP (pulso único, máximo 2 tentativas com recuperação de chão)
        bool triggerJumpPulse = false;
        if (wp.MovementAction == TransitionMovementAction.STEP_UP_JUMP_PULSE && !_stepUpJumpInProgress && !ObservedZGainOnCurrentWp)
        {
            bool canRetryGround = _stepUpAttemptsOnCurrentWp == 0 || (GroundRecoveredSinceLastPulse && isGrounded);
            if (canRetryGround &&
                CanEmitJumpPulseNow(wp, x, y, z, tick, LastJumpPulseTick, _stepUpAttemptsOnCurrentWp, teammateBlocking, exitPathValid, out _, isGrounded))
            {
                if (PulseState == StepUpPulseState.WAITING_FOR_ALIGNMENT)
                {
                    PulseState = StepUpPulseState.READY_TO_PULSE;
                }
                // Invariante estrita anti-IN_JUMP contínuo: nunca em ticks consecutivos
                if ((tick - LastJumpPulseTick) <= 2)
                {
                    ContinuousJumpViolations++;
                }
                else
                {
                    triggerJumpPulse = true;
                    JumpPulsesIssued++;
                    PulseRequestsOnCurrentWp++;
                    LastJumpPulseTick = tick;
                    LastPulseWasApplied = false;
                    GroundRecoveredSinceLastPulse = false;
                    _stableGroundTicks = 0;
                    _stepUpAttemptsOnCurrentWp++;
                    _stepUpJumpInProgress = true;
                    _stepUpJumpStartTick = tick;
                    _stepUpJumpStartZ = z;
                    PulseState = StepUpPulseState.PULSE_REQUESTED;
                    RecordEvent(roundId, tick, EventLocalizedAction, wp, "STEP_UP_JUMP_PULSE", wp.Z - z, true);
                    emitCmd = true;
                    cmdType = EventLocalizedAction;
                }
            }
        }

        // Avalia pulso curto de ataque/faca caso uma grade quebrável do Vent esteja bloqueando movimento
        bool triggerAttackPulse = false;
        if (!triggerJumpPulse &&
            wp.MovementAction == TransitionMovementAction.CLEAR_VENT_OBSTACLE &&
            dist2D <= 130.0 &&
            speed2D <= 65.0 &&
            (tick - LastAttackPulseTick) >= 16)
        {
            triggerAttackPulse = true;
            LastAttackPulseTick = tick;
            RecordEvent(roundId, tick, EventLocalizedAction, wp, "CLEAR_VENT_OBSTACLE", wp.Z - z, false);
            emitCmd = true;
            cmdType = EventLocalizedAction;
        }

        return new TransitionStepEvaluation
        {
            Active = true,
            EmitCommand = emitCmd,
            CommandEventType = cmdType,
            ShouldEmitJumpPulse = triggerJumpPulse,
            ShouldEmitAttackPulse = triggerAttackPulse,
            CurrentWaypoint = wp,
        };
    }

    private void RecordEvent(int roundId, int tick, string eventType, RouteTransitionWaypoint wp, string action, double zDelta, bool jumpPulse)
    {
        CommandDispatchCount++;
        _events.Add(new TransitionExecutionEvent
        {
            RoundId = roundId,
            Tick = tick,
            EventType = eventType,
            TransitionId = wp.NextWaypoint.Length > 0 ? $"{wp.Name}->{wp.NextWaypoint}" : wp.Name,
            WaypointName = wp.Name,
            TransitionType = wp.TransitionType.ToString(),
            Action = action,
            ZDelta = Math.Round(zDelta, 2),
            JumpPulse = jumpPulse
        });
    }
}
