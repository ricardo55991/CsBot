using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace CsBotManager;

public static class CanonicalSemanticRole
{
    public const string RouteEntry = "ROUTE_ENTRY";
    public const string PortalEntry = "PORTAL_ENTRY";
    public const string PortalExit = "PORTAL_EXIT";
    public const string Turn = "TURN";
    public const string Ramp = "RAMP";
    public const string Step = "STEP";
    public const string NarrowPassage = "NARROW_PASSAGE";
    public const string FinalApproach = "FINAL_APPROACH";
    public const string FinalDestination = "FINAL_DESTINATION";
}

public static class CanonicalStepState
{
    public const string NotDispatched = "NOT_DISPATCHED";
    public const string Dispatched = "DISPATCHED";
    public const string Moving = "MOVING";
    public const string EnteredRadius = "ENTERED_RADIUS";
    public const string PortalCrossed = "PORTAL_CROSSED";
    public const string Completed = "COMPLETED";
}

public static class CanonicalRouteState
{
    public const string Active = "ACTIVE";
    public const string FinalApproach = "FINAL_APPROACH";
    public const string DestinationDwell = "DESTINATION_DWELL";
    public const string Completed = "COMPLETED";
    public const string Interrupted = "INTERRUPTED";
    public const string Fallback = "FALLBACK";
}

public sealed class CanonicalRouteStep
{
    [JsonPropertyName("index")] public int Index { get; set; }
    [JsonPropertyName("name")] public string Name { get; set; } = string.Empty;
    [JsonPropertyName("semantic_role")] public string SemanticRole { get; set; } = CanonicalSemanticRole.PortalEntry;
    [JsonPropertyName("canonical_position")] public float[] CanonicalPosition { get; set; } = new float[3];
    [JsonPropertyName("projected_position")] public float[] ProjectedPosition { get; set; } = new float[3];
    [JsonPropertyName("navmesh_area")] public int NavMeshArea { get; set; }
    [JsonPropertyName("transition_type")] public TransitionWaypointType TransitionType { get; set; } = TransitionWaypointType.FLAT_PORTAL;
    [JsonPropertyName("movement_action")] public TransitionMovementAction MovementAction { get; set; } = TransitionMovementAction.NONE;
    [JsonPropertyName("arrival_radius")] public float ArrivalRadius { get; set; } = 72f;
    [JsonPropertyName("exit_radius")] public float ExitRadius { get; set; } = 90f;
    [JsonPropertyName("timeout")] public double TimeoutSeconds { get; set; } = 4.0;
    [JsonPropertyName("require_crouch")] public bool RequireCrouch { get; set; }
    [JsonPropertyName("allow_jump_pulse")] public bool AllowJumpPulse { get; set; }
    [JsonPropertyName("use_exact_portal_steering")] public bool UseExactPortalSteering { get; set; }
    [JsonPropertyName("is_final_destination")] public bool IsFinalDestination { get; set; }
    [JsonPropertyName("expected_next_step_index")] public int? ExpectedNextStepIndex { get; set; }
    [JsonPropertyName("expected_next_step_name")] public string? ExpectedNextStepName { get; set; }
    [JsonPropertyName("projection_delta")] public double ProjectionDelta { get; set; }
    [JsonPropertyName("projection_applied")] public bool ProjectionApplied { get; set; }
    [JsonPropertyName("final_target_spot_id")] public string FinalTargetSpotId { get; set; } = string.Empty;
    [JsonPropertyName("expected_z_delta")] public float ExpectedZDelta { get; set; }
    [JsonPropertyName("min_z_delta")] public float MinZDelta { get; set; } = -32f;
    [JsonPropertyName("max_z_delta")] public float MaxZDelta { get; set; } = 96f;
    [JsonPropertyName("required_clearance")] public float RequiredClearance { get; set; } = 48f;
    [JsonPropertyName("minimum_forward_progress")] public float MinimumForwardProgress { get; set; } = 4f;
    [JsonPropertyName("maximum_lateral_error")] public float MaximumLateralError { get; set; } = 90f;
    [JsonPropertyName("approach_dir_x")] public float ApproachDirX { get; set; }
    [JsonPropertyName("approach_dir_y")] public float ApproachDirY { get; set; }
    [JsonPropertyName("approach_dir_z")] public float ApproachDirZ { get; set; }

    [JsonIgnore] public float X => ProjectionApplied ? ProjectedPosition[0] : CanonicalPosition[0];
    [JsonIgnore] public float Y => ProjectionApplied ? ProjectedPosition[1] : CanonicalPosition[1];
    [JsonIgnore] public float Z => ProjectionApplied ? ProjectedPosition[2] : CanonicalPosition[2];
    [JsonIgnore] public string State { get; set; } = CanonicalStepState.NotDispatched;

    public RouteWaypoint ToRouteWaypoint() => new()
    {
        Name = Name,
        X = X,
        Y = Y,
        Z = Z,
    };

    public RouteTransitionWaypoint ToTransitionWaypoint() => new()
    {
        Name = Name,
        X = X,
        Y = Y,
        Z = Z,
        NavMeshArea = NavMeshArea,
        TransitionType = TransitionType,
        ArrivalRadius = ArrivalRadius,
        ExitRadius = ExitRadius,
        TimeoutSeconds = TimeoutSeconds,
        RequireCrouch = RequireCrouch,
        AllowJumpPulse = AllowJumpPulse,
        MovementAction = MovementAction,
        NextWaypoint = ExpectedNextStepName ?? string.Empty,
        ExpectedZDelta = ExpectedZDelta,
        MinZDelta = MinZDelta,
        MaxZDelta = MaxZDelta,
        RequiredClearance = RequiredClearance,
        MinimumForwardProgress = MinimumForwardProgress,
        MaximumLateralError = MaximumLateralError,
        ApproachDirX = ApproachDirX,
        ApproachDirY = ApproachDirY,
        ApproachDirZ = ApproachDirZ,
    };
}

public static class CanonicalRouteValidator
{
    public static (bool IsValid, string Reason) Validate(
        IReadOnlyList<CanonicalRouteStep> steps,
        string expectedTargetSpotId,
        float catalogX,
        float catalogY,
        float catalogZ,
        NavMeshGraph? nav = null)
    {
        if (steps == null || steps.Count == 0)
            return (false, "CANONICAL_ROUTE_EMPTY");

        int entryCount = 0;
        int finalCount = 0;
        var seenNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (int i = 0; i < steps.Count; i++)
        {
            var s = steps[i];
            if (s.Index != i)
                return (false, $"MISSING_OR_MISMATCHED_INDEX:{i}!={s.Index}");
            if (string.IsNullOrWhiteSpace(s.Name))
                return (false, $"EMPTY_STEP_NAME:{i}");
            if (!seenNames.Add(s.Name))
                return (false, $"DUPLICATE_STEP_NAME:{s.Name}");
            if (s.SemanticRole == CanonicalSemanticRole.RouteEntry)
                entryCount++;
            if (s.IsFinalDestination)
                finalCount++;

            if (i < steps.Count - 1)
            {
                if (s.IsFinalDestination)
                    return (false, $"INTERMEDIATE_MARKED_FINAL:{s.Name}");
                if (!s.ExpectedNextStepIndex.HasValue || s.ExpectedNextStepIndex.Value != i + 1)
                    return (false, $"BROKEN_NEXT_INDEX:{s.Name}");
                if (s.ExpectedNextStepIndex.Value == i)
                    return (false, $"SELF_REFERENTIAL_STEP:{s.Name}");
                if (!string.Equals(s.ExpectedNextStepName, steps[i + 1].Name, StringComparison.Ordinal))
                    return (false, $"BROKEN_NEXT_NAME:{s.Name}");
            }
            else
            {
                if (!s.IsFinalDestination)
                    return (false, $"LAST_STEP_NOT_FINAL:{s.Name}");
                if (s.ExpectedNextStepIndex.HasValue || s.ExpectedNextStepName != null)
                    return (false, $"FINAL_STEP_HAS_NEXT:{s.Name}");
                if (!string.Equals(s.FinalTargetSpotId, expectedTargetSpotId, StringComparison.OrdinalIgnoreCase))
                    return (false, $"FINAL_TARGET_MISMATCH:{s.FinalTargetSpotId}!={expectedTargetSpotId}");

                double dx = Math.Abs(s.CanonicalPosition[0] - catalogX);
                double dy = Math.Abs(s.CanonicalPosition[1] - catalogY);
                double dz = Math.Abs(s.CanonicalPosition[2] - catalogZ);
                if (dx > 1.0 || dy > 1.0 || dz > 1.0)
                    return (false, $"FINAL_COORDS_DIVERGE_FROM_CATALOG:{s.Name}");
            }

            if (nav != null)
            {
                var proj = nav.ProjectPoint(s.CanonicalPosition[0], s.CanonicalPosition[1], s.CanonicalPosition[2], maxSnapUnits: 160f);
                if (proj.AreaId <= 0)
                    return (false, $"UNPROJECTABLE_STEP:{s.Name}");
            }
        }

        if (entryCount != 1)
            return (false, $"INVALID_ROUTE_ENTRY_COUNT:{entryCount}");
        if (finalCount != 1)
            return (false, $"INVALID_FINAL_DESTINATION_COUNT:{finalCount}");

        return (true, "VALID");
    }

    public static void ProjectCanonicalStepsInPlace(IList<CanonicalRouteStep> steps, NavMeshGraph? nav)
    {
        if (steps == null || steps.Count == 0 || nav == null) return;
        foreach (var s in steps)
        {
            if (s.IsFinalDestination)
            {
                // Preserva coordenadas canônicas do catálogo no destino final
                s.ProjectedPosition = new[] { s.CanonicalPosition[0], s.CanonicalPosition[1], s.CanonicalPosition[2] };
                s.ProjectionDelta = 0.0;
                s.ProjectionApplied = false;
                var fp = nav.ProjectPoint(s.CanonicalPosition[0], s.CanonicalPosition[1], s.CanonicalPosition[2], maxSnapUnits: 120f);
                if (fp.AreaId > 0 && s.NavMeshArea <= 0) s.NavMeshArea = fp.AreaId;
                continue;
            }
            var proj = nav.ProjectPoint(s.CanonicalPosition[0], s.CanonicalPosition[1], s.CanonicalPosition[2], maxSnapUnits: 96f);
            if (proj.AreaId > 0)
            {
                double delta = Math.Sqrt(
                    Math.Pow(proj.ProjectedX - s.CanonicalPosition[0], 2) +
                    Math.Pow(proj.ProjectedY - s.CanonicalPosition[1], 2) +
                    Math.Pow(proj.ProjectedZ - s.CanonicalPosition[2], 2));
                s.ProjectedPosition = new[] { proj.ProjectedX, proj.ProjectedY, proj.ProjectedZ };
                s.ProjectionDelta = Math.Round(delta, 2);
                s.ProjectionApplied = true;
                if (s.NavMeshArea <= 0) s.NavMeshArea = proj.AreaId;
            }
            else
            {
                s.ProjectedPosition = new[] { s.CanonicalPosition[0], s.CanonicalPosition[1], s.CanonicalPosition[2] };
                s.ProjectionDelta = 0.0;
                s.ProjectionApplied = false;
            }
        }
    }
}
