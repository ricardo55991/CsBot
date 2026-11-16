using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace CsBotManager;

public static class OpeningRouteEventContract
{
    public const string ContractVersion = "opening_route_event_contract_v2";

    public static string GetCanonicalClassificationName(int code) => code switch
    {
        0 => nameof(OpeningRouteClassification.PENDING),
        1 => nameof(OpeningRouteClassification.ON_TIME),
        2 => nameof(OpeningRouteClassification.LATE),
        3 => nameof(OpeningRouteClassification.TACTICAL_REDIRECT),
        4 => nameof(OpeningRouteClassification.CONTACT_INTERRUPTION),
        5 => nameof(OpeningRouteClassification.BLOCKED_BY_TEAMMATE),
        6 => nameof(OpeningRouteClassification.PLAYER_DEATH),
        7 => nameof(OpeningRouteClassification.NOT_REACHED),
        8 => nameof(OpeningRouteClassification.INVALID_ROUTE),
        _ => $"UNKNOWN_CLASSIFICATION_{code}"
    };

    public static string GetCanonicalTerminationReasonName(int code) => code switch
    {
        0 => nameof(OpeningRouteTerminationReason.NONE),
        1 => nameof(OpeningRouteTerminationReason.TARGET_REACHED),
        2 => nameof(OpeningRouteTerminationReason.TACTICAL_REDIRECT),
        3 => nameof(OpeningRouteTerminationReason.CONTACT_INTERRUPTION),
        4 => nameof(OpeningRouteTerminationReason.PLAYER_DEATH),
        5 => nameof(OpeningRouteTerminationReason.ROUND_END),
        6 => nameof(OpeningRouteTerminationReason.TIMEOUT),
        7 => nameof(OpeningRouteTerminationReason.INVALIDATED),
        _ => $"UNKNOWN_TERMINATION_{code}"
    };

    public static bool IsPenalizedAsLate(OpeningRouteClassification classification)
    {
        return classification == OpeningRouteClassification.LATE;
    }
}

public sealed class RouteWaypoint
{
    [JsonPropertyName("name")] public string Name { get; init; } = string.Empty;
    [JsonPropertyName("x")] public float X { get; init; }
    [JsonPropertyName("y")] public float Y { get; init; }
    [JsonPropertyName("z")] public float Z { get; init; }
}

public sealed class OpeningRouteDefinition
{
    [JsonPropertyName("route_id")] public string RouteId { get; init; } = string.Empty;
    [JsonPropertyName("map")] public string Map { get; init; } = "de_mirage";
    [JsonPropertyName("team")] public string Team { get; init; } = string.Empty;
    [JsonPropertyName("spawn_bucket")] public string SpawnBucket { get; init; } = string.Empty;
    [JsonPropertyName("role")] public string Role { get; init; } = string.Empty;
    [JsonPropertyName("target_spot")] public string TargetSpot { get; init; } = string.Empty;
    [JsonPropertyName("target_sector")] public string TargetSector { get; init; } = string.Empty;
    [JsonPropertyName("route_variant")] public string RouteVariant { get; init; } = "PRIMARY";
    [JsonPropertyName("ordered_waypoints")] public List<RouteWaypoint> OrderedWaypoints { get; init; } = new();
    [JsonPropertyName("transition_waypoints")] public List<RouteTransitionWaypoint> TransitionWaypoints { get; init; } = new();
    [JsonPropertyName("canonical_steps")] public List<CanonicalRouteStep> CanonicalSteps { get; init; } = new();
    [JsonPropertyName("allowed_corridor")] public string AllowedCorridor { get; init; } = string.Empty;
    [JsonPropertyName("forbidden_corridors")] public List<string> ForbiddenCorridors { get; init; } = new();
    [JsonPropertyName("expected_distance")] public double ExpectedDistance { get; init; }
    [JsonPropertyName("expected_arrival_seconds")] public double ExpectedArrivalSeconds { get; init; }
    [JsonPropertyName("deadline_seconds")] public double DeadlineSeconds { get; init; }
    [JsonPropertyName("knife_allowed_until")] public double KnifeAllowedUntil { get; init; }
    [JsonPropertyName("weapon_ready_waypoint")] public RouteWaypoint WeaponReadyWaypoint { get; init; } = new();
    [JsonPropertyName("first_threat_line")] public RouteWaypoint FirstThreatLine { get; init; } = new();
    [JsonPropertyName("first_preaim_target")] public string FirstPreaimTarget { get; init; } = string.Empty;
    [JsonPropertyName("fallback_route")] public string FallbackRoute { get; init; } = string.Empty;
    [JsonPropertyName("conflict_group")] public string ConflictGroup { get; init; } = string.Empty;
    [JsonPropertyName("contract_version")] public string ContractVersion { get; init; } = "opening_route_catalog_v1";
}

public sealed class OpeningRouteSuggestion
{
    [JsonPropertyName("round_id")] public int RoundId { get; init; }
    [JsonPropertyName("player_slot")] public string PlayerSlot { get; init; } = string.Empty;
    [JsonPropertyName("raw_slot")] public int RawSlot { get; init; }
    [JsonPropertyName("team")] public string Team { get; init; } = string.Empty;
    [JsonPropertyName("role")] public string Role { get; init; } = string.Empty;
    [JsonPropertyName("spawn_bucket")] public string SpawnBucket { get; init; } = string.Empty;
    [JsonPropertyName("target_spot")] public string TargetSpot { get; init; } = string.Empty;
    [JsonPropertyName("target_sector")] public string TargetSector { get; init; } = string.Empty;
    [JsonPropertyName("route_id")] public string RouteId { get; init; } = string.Empty;
    [JsonPropertyName("route_variant")] public string RouteVariant { get; init; } = "PRIMARY";
    [JsonPropertyName("allowed_corridor")] public string AllowedCorridor { get; init; } = string.Empty;
    [JsonPropertyName("forbidden_corridors")] public List<string> ForbiddenCorridors { get; init; } = new();
    [JsonPropertyName("ordered_waypoints")] public List<RouteWaypoint> OrderedWaypoints { get; init; } = new();
    [JsonPropertyName("transition_waypoints")] public List<RouteTransitionWaypoint> TransitionWaypoints { get; init; } = new();
    [JsonPropertyName("canonical_steps")] public List<CanonicalRouteStep> CanonicalSteps { get; init; } = new();
    [JsonPropertyName("weapon_ready_waypoint")] public RouteWaypoint WeaponReadyWaypoint { get; init; } = new();
    [JsonPropertyName("first_threat_line")] public RouteWaypoint FirstThreatLine { get; init; } = new();
    [JsonPropertyName("expected_distance")] public double ExpectedDistance { get; init; }
    [JsonPropertyName("expected_arrival_seconds")] public double ExpectedArrivalSeconds { get; init; }
    [JsonPropertyName("deadline_seconds")] public double DeadlineSeconds { get; init; }
    [JsonPropertyName("knife_allowed_until")] public double KnifeAllowedUntil { get; init; }
    [JsonPropertyName("knife_start_tick")] public int KnifeStartTick { get; init; }
    [JsonPropertyName("weapon_switch_tick")] public int WeaponSwitchTick { get; init; }
    [JsonPropertyName("threat_line_tick")] public int ThreatLineTick { get; init; }
    [JsonPropertyName("first_possible_contact_tick")] public int FirstPossibleContactTick { get; init; }
    [JsonPropertyName("distance_to_threat_at_switch")] public double DistanceToThreatAtSwitch { get; init; }
    [JsonPropertyName("weapon_ready_before_contact")] public bool WeaponReadyBeforeContact { get; init; }
    [JsonPropertyName("first_preaim_target")] public string FirstPreaimTarget { get; init; } = string.Empty;
    [JsonPropertyName("conflict_group")] public string ConflictGroup { get; init; } = string.Empty;
    [JsonPropertyName("conflict_detected")] public bool ConflictDetected { get; init; }
    [JsonPropertyName("priority_winner")] public string PriorityWinner { get; init; } = string.Empty;
    [JsonPropertyName("delayed_bot")] public string DelayedBot { get; init; } = string.Empty;
    [JsonPropertyName("alternative_route")] public string AlternativeRoute { get; init; } = string.Empty;
    [JsonPropertyName("delay_ms")] public int DelayMs { get; init; }
    [JsonPropertyName("blocked_duration_ms")] public int BlockedDurationMs { get; init; }
    [JsonPropertyName("planner_control_active")] public bool PlannerControlActive { get; init; } = false;
    [JsonPropertyName("utility_decision_preserved")] public bool UtilityDecisionPreserved { get; init; } = true;
}

public static class SpawnBucketClassifier
{
    public static string Classify(string team, float x, float y, float z)
    {
        string t = (team.Equals("T", StringComparison.OrdinalIgnoreCase) || team.Equals("TR", StringComparison.OrdinalIgnoreCase)) ? "T" : "CT";

        (string corr, float ax, float ay, float az, float fastThresh)[] anchors = t == "CT"
            ? new[]
            {
                ("A", -1400f, -2080f, -195f, 510f),
                ("MID", -1480f, -1520f, -200f, 520f),
                ("B", -1760f, -1420f, -168f, 560f),
            }
            : new[]
            {
                ("A", 780f, -1100f, -168f, 1020f),
                ("MID", 560f, -260f, -168f, 680f),
                ("B", -350f, 480f, -77f, 1550f),
            };

        string bestCorr = anchors[0].corr;
        float bestDist = float.MaxValue;
        float bestThresh = anchors[0].fastThresh;

        foreach (var a in anchors)
        {
            float d = MathF.Sqrt((x - a.ax) * (x - a.ax) + (y - a.ay) * (y - a.ay) + (z - a.az) * (z - a.az));
            if (d < bestDist)
            {
                bestDist = d;
                bestCorr = a.corr;
                bestThresh = a.fastThresh;
            }
        }

        string tier = bestDist <= bestThresh ? "FAST" : "STANDARD";
        return $"{t}_{bestCorr}_{tier}";
    }
}

public static class OpeningRoutePlannerGuard
{
    public static string OpeningRoutePlannerCannotAffectBotDecision(string utilityDecision, OpeningRouteSuggestion? suggestion)
    {
        // Shadow Mode estrito: a sugestão do planner é apenas observacional e nunca altera a decisão da Utility AI.
        _ = suggestion;
        return utilityDecision;
    }
}

public sealed class OpeningRoutePlanner
{
    private sealed record CorridorTemplate(
        string Corridor,
        string[] Forbidden,
        RouteWaypoint[] Waypoints,
        RouteWaypoint WeaponReadyWp,
        RouteWaypoint ThreatLine,
        string Preaim,
        string ConflictGroup,
        double KnifeUntilFrac,
        string Sector);

    private static readonly Dictionary<(string Team, string Key), CorridorTemplate> Templates = new()
    {
        [("CT", "A_TICKET")] = new("CT_A_TICKET", new[] { "MID_WINDOW", "MID_CONNECTOR", "MID_SHORT", "B_MARKET", "B_APPS" },
            new[] { new RouteWaypoint { Name = "ct_ticket_booth", X = -1020.9f, Y = -2489.1f, Z = -168.0f } },
            new RouteWaypoint { Name = "ct_ticket_booth", X = -1020.9f, Y = -2489.1f, Z = -168.0f },
            new RouteWaypoint { Name = "a_ramp_exit_line", X = -580f, Y = -2100f, Z = -175f },
            "A_RAMP_OR_PALACE", "CT_SPAWN_EXIT", 0.62, "A"),

        [("CT", "A_JUNGLE")] = new("CT_JUNGLE_STAIRS", new[] { "MID_WINDOW", "B_MARKET", "B_APPS", "A_RAMP_TR" },
            new[] { new RouteWaypoint { Name = "ct_jungle_entry", X = -1245.4f, Y = -1374.2f, Z = -164.8f } },
            new RouteWaypoint { Name = "ct_jungle_entry", X = -1245.4f, Y = -1374.2f, Z = -164.8f },
            new RouteWaypoint { Name = "a_stairs_mid_line", X = -540.6f, Y = -1443.6f, Z = -73.9f },
            "A_RAMP_AND_PALACE", "CONNECTOR_ENTRY", 0.58, "A"),

        [("CT", "MID_WINDOW")] = new("CT_MID_WINDOW", new[] { "B_MARKET", "B_APPS", "A_RAMP", "A_PALACE" },
            new[] { new RouteWaypoint { Name = "ct_window_vents", X = -1329.4f, Y = -964.8f, Z = -168.0f } },
            new RouteWaypoint { Name = "ct_window_vents", X = -1329.4f, Y = -964.8f, Z = -168.0f },
            new RouteWaypoint { Name = "mid_window_sightline", X = -1181.4f, Y = -718.5f, Z = -168.0f },
            "TOP_MID_BOXES", "WINDOW_ENTRY", 0.56, "MID"),

        [("CT", "MID_SHORT")] = new("CT_B_SHORT_MID", new[] { "A_RAMP", "A_PALACE", "T_SPAWN" },
            new[] { new RouteWaypoint { Name = "ct_market_back", X = -1616.8f, Y = -618.9f, Z = -168.0f }, new RouteWaypoint { Name = "ct_short_arch", X = -1489.5f, Y = 259.9f, Z = -167.0f } },
            new RouteWaypoint { Name = "ct_short_arch", X = -1489.5f, Y = 259.9f, Z = -167.0f },
            new RouteWaypoint { Name = "mid_catwalk_sightline", X = -902.8f, Y = 191.2f, Z = -172.8f },
            "TOP_MID_CATWALK", "MARKET_ENTRY", 0.65, "MID"),

        [("CT", "B_MARKET")] = new("CT_MARKET_CORRIDOR", new[] { "MID_WINDOW", "MID_CONNECTOR", "MID_SHORT", "A_RAMP", "A_JUNGLE" },
            new[] { new RouteWaypoint { Name = "ct_market_entry", X = -1616.8f, Y = -618.9f, Z = -168.0f } },
            new RouteWaypoint { Name = "ct_market_entry", X = -1616.8f, Y = -618.9f, Z = -168.0f },
            new RouteWaypoint { Name = "b_apps_window_line", X = -1888.0f, Y = 250.5f, Z = -160.0f },
            "B_APPS_WINDOW", "MARKET_ENTRY", 0.64, "B"),

        [("T", "A_RAMP")] = new("T_A_RAMP", new[] { "CT_SPAWN", "B_APPS", "B_MARKET", "MID_WINDOW" },
            new[] { new RouteWaypoint { Name = "t_a_ramp_entry", X = 320.0f, Y = -1590.0f, Z = -168.0f } },
            new RouteWaypoint { Name = "t_a_ramp_entry", X = 320.0f, Y = -1590.0f, Z = -168.0f },
            new RouteWaypoint { Name = "a_ramp_choke", X = 93.7f, Y = -1685.3f, Z = -168.0f },
            "A_STAIRS_OR_TICKET", "A_RAMP_ENTRY", 0.55, "A"),

        [("T", "A_PALACE")] = new("T_A_PALACE", new[] { "CT_SPAWN", "B_APPS", "B_MARKET", "MID_WINDOW" },
            new[] { new RouteWaypoint { Name = "t_palace_stairs", X = 90.0f, Y = -2244.6f, Z = -40.0f } },
            new RouteWaypoint { Name = "t_palace_stairs", X = 90.0f, Y = -2244.6f, Z = -40.0f },
            new RouteWaypoint { Name = "a_palace_exit", X = -99.6f, Y = -2138.1f, Z = -168.0f },
            "A_SITE_AND_JUNGLE", "PALACE_ENTRY", 0.54, "A"),

        [("T", "MID_TOP")] = new("T_TOP_MID", new[] { "CT_SPAWN", "B_MARKET", "A_PALACE" },
            new[] { new RouteWaypoint { Name = "t_top_mid_alley", X = 455.0f, Y = -348.1f, Z = -161.5f } },
            new RouteWaypoint { Name = "t_top_mid_alley", X = 455.0f, Y = -348.1f, Z = -161.5f },
            new RouteWaypoint { Name = "top_mid_window_line", X = 280.0f, Y = -223.0f, Z = -167.7f },
            "MID_WINDOW_AND_CONNECTOR", "TOP_MID_ENTRY", 0.30, "MID"),

        [("T", "MID_UNDERPASS")] = new("T_UNDERPASS", new[] { "CT_SPAWN", "B_MARKET", "A_RAMP" },
            new[] { new RouteWaypoint { Name = "t_top_mid_alley", X = 455.0f, Y = -348.1f, Z = -161.5f } },
            new RouteWaypoint { Name = "t_top_mid_alley", X = 455.0f, Y = -348.1f, Z = -161.5f },
            new RouteWaypoint { Name = "underpass_connector_line", X = -544.0f, Y = -518.5f, Z = -140.0f },
            "UNDERPASS_EXIT_OR_SHORT", "UNDERPASS_ENTRY", 0.22, "MID"),

        [("T", "B_APPS")] = new("T_B_APPS", new[] { "CT_SPAWN", "CT_MARKET", "A_RAMP", "A_PALACE" },
            new[] { new RouteWaypoint { Name = "t_b_house_entry", X = -764.4f, Y = 522.1f, Z = -77.0f } },
            new RouteWaypoint { Name = "t_b_house_entry", X = -764.4f, Y = 522.1f, Z = -77.0f },
            new RouteWaypoint { Name = "b_apps_tv_choke", X = -1111.7f, Y = 687.0f, Z = -80.0f },
            "B_APPS_VAN_AND_MARKET", "B_APPS_ENTRY", 0.62, "B"),
    };

    private readonly Dictionary<(int RoundId, int RawSlot), OpeningRouteSuggestion> _roundSuggestions = new();
    private readonly Dictionary<(int RoundId, string Team, string ConflictGroup), OpeningRouteSuggestion> _conflictWinners = new();
    private readonly List<OpeningRouteSuggestion> _allSuggestions = new();

    public IReadOnlyList<OpeningRouteSuggestion> AllSuggestions => _allSuggestions;

    public bool TryPlanOpeningRouteForRound(
        int roundId,
        int rawSlot,
        string pseudonymizedSlot,
        string team,
        string role,
        string targetSpotId,
        string spotSector,
        float startX, float startY, float startZ,
        float targetX, float targetY, float targetZ,
        int tick,
        out OpeningRouteSuggestion? suggestion)
    {
        suggestion = null;
        string normTeam = (team.Equals("T", StringComparison.OrdinalIgnoreCase) || team.Equals("TR", StringComparison.OrdinalIgnoreCase)) ? "T" : "CT";

        // No máximo 1 sugestão de Opening Route por jogador/round
        if (_roundSuggestions.TryGetValue((roundId, rawSlot), out var existing))
        {
            suggestion = existing;
            return false;
        }

        // Validação estrita de lado: nunca sugerir rota de lado incompatível
        var ctx = new UtilitySpotValidationContext
        {
            MapName = "de_mirage",
            RequestedSide = normTeam == "T" ? "TR" : "CT",
            RequestedState = "HOLD",
            RequestedPhase = "Staging",
            Role = role,
        };
        var sideCheck = UtilitySpotAssignmentValidator.ValidateCandidate(
            new TacticalSpot { Id = targetSpotId, Sector = spotSector, Side = "ANY" }, ctx);
        if (!sideCheck.IsValid && sideCheck.Reason == SpotAssignmentRejectionReason.WRONG_SIDE)
        {
            return false;
        }

        string spawnBucket = SpawnBucketClassifier.Classify(normTeam, startX, startY, startZ);
        string corrKey = PickCorridorKey(normTeam, targetSpotId, spotSector);
        var tpl = Templates[(normTeam, corrKey)];

        var transitionWps = normTeam == "CT"
            ? GeometricTransitionCatalog.BuildTransitionsForCtRoute(corrKey, targetSpotId, targetX, targetY, targetZ)
            : GeometricTransitionCatalog.BuildTransitionsForTrRoute(corrKey, targetSpotId, targetX, targetY, targetZ);

        var canonicalSteps = new List<CanonicalRouteStep>();
        if (normTeam == "T" && transitionWps.Count > 0)
        {
            for (int i = 0; i < transitionWps.Count; i++)
            {
                var tw = transitionWps[i];
                bool isLast = i == transitionWps.Count - 1;
                var roleEnum = isLast
                    ? CanonicalSemanticRole.FinalDestination
                    : (i == 0
                        ? CanonicalSemanticRole.RouteEntry
                        : (tw.TransitionType == TransitionWaypointType.STEP_UP ||
                           tw.TransitionType == TransitionWaypointType.STEP_DOWN ||
                           tw.TransitionType == TransitionWaypointType.DOORWAY ||
                           tw.TransitionType == TransitionWaypointType.NARROW_PASSAGE)
                            ? CanonicalSemanticRole.PortalEntry
                            : CanonicalSemanticRole.FinalApproach);

                canonicalSteps.Add(new CanonicalRouteStep
                {
                    Index = i,
                    Name = tw.Name,
                    SemanticRole = roleEnum,
                    CanonicalPosition = new[] { tw.X, tw.Y, tw.Z },
                    ProjectedPosition = new[] { tw.X, tw.Y, tw.Z },
                    NavMeshArea = tw.NavMeshArea,
                    TransitionType = tw.TransitionType,
                    MovementAction = tw.MovementAction,
                    ArrivalRadius = tw.ArrivalRadius,
                    ExitRadius = tw.ExitRadius,
                    TimeoutSeconds = tw.TimeoutSeconds,
                    RequireCrouch = tw.RequireCrouch,
                    AllowJumpPulse = tw.AllowJumpPulse,
                    UseExactPortalSteering = tw.UseExactPortalSteering,
                    IsFinalDestination = isLast,
                    ExpectedNextStepIndex = isLast ? null : i + 1,
                    ExpectedNextStepName = isLast ? null : transitionWps[i + 1].Name,
                    FinalTargetSpotId = isLast ? targetSpotId : string.Empty,
                    ExpectedZDelta = tw.ExpectedZDelta,
                    MinZDelta = tw.MinZDelta,
                    MaxZDelta = tw.MaxZDelta,
                    RequiredClearance = tw.RequiredClearance,
                    MinimumForwardProgress = tw.MinimumForwardProgress,
                    MaximumLateralError = tw.MaximumLateralError,
                    ApproachDirX = tw.ApproachDirX,
                    ApproachDirY = tw.ApproachDirY,
                    ApproachDirZ = tw.ApproachDirZ,
                });
            }
        }

        var waypoints = transitionWps.Count > 0
            ? transitionWps.Select(t => t.ToRouteWaypoint()).ToList()
            : new List<RouteWaypoint>(tpl.Waypoints)
            {
                new() { Name = targetSpotId, X = targetX, Y = targetY, Z = targetZ }
            };

        double expDist = ComputePolylineLength(startX, startY, startZ, waypoints);
        double navPathFactor = (normTeam == "T" && corrKey == "B_APPS") ? 1.12 : 1.0;
        double expSec = Math.Max(2.0, (expDist * navPathFactor) / 235.0);
        double deadlineSec = expSec * 1.45 + 1.8;
        double knifeUntil = expSec * tpl.KnifeUntilFrac;

        int knifeStartTick = tick;
        int threatLineTick = tick + Math.Max(1, (int)Math.Round(expSec * Math.Min(0.85, tpl.KnifeUntilFrac + 0.10) * 64.0));
        int firstPossibleContactTick = tick + Math.Max(2, (int)Math.Round(expSec * Math.Min(0.95, tpl.KnifeUntilFrac + 0.16) * 64.0));
        int weaponSwitchTick = tick + Math.Max(1, (int)Math.Round(knifeUntil * 64.0));
        if (weaponSwitchTick >= threatLineTick)
        {
            weaponSwitchTick = Math.Max(knifeStartTick, threatLineTick - 16);
        }

        double distThreatAtSwitch = Math.Sqrt(
            (tpl.ThreatLine.X - tpl.WeaponReadyWp.X) * (tpl.ThreatLine.X - tpl.WeaponReadyWp.X) +
            (tpl.ThreatLine.Y - tpl.WeaponReadyWp.Y) * (tpl.ThreatLine.Y - tpl.WeaponReadyWp.Y) +
            (tpl.ThreatLine.Z - tpl.WeaponReadyWp.Z) * (tpl.ThreatLine.Z - tpl.WeaponReadyWp.Z));

        bool weaponReadyBeforeContact = weaponSwitchTick < firstPossibleContactTick && weaponSwitchTick <= threatLineTick;

        // Resolução determinística de conflito no mesmo ConflictGroup + Team + Round
        var cgKey = (roundId, normTeam, tpl.ConflictGroup);
        bool conflictDetected = false;
        string priorityWinner = pseudonymizedSlot;
        string delayedBot = string.Empty;
        string altRoute = string.Empty;
        string routeVariant = "PRIMARY";
        int delayMs = 0;

        if (_conflictWinners.TryGetValue(cgKey, out var currentLeader))
        {
            conflictDetected = true;
            if (ComparePriority(spawnBucket, role, rawSlot, currentLeader.SpawnBucket, currentLeader.Role, currentLeader.RawSlot) > 0)
            {
                // Novo candidato teria prioridade maior se avaliado junto; em runtime sequencial, novo bot usa variante STAGGERED_FALLBACK
                priorityWinner = currentLeader.PlayerSlot;
                delayedBot = pseudonymizedSlot;
            }
            else
            {
                priorityWinner = currentLeader.PlayerSlot;
                delayedBot = pseudonymizedSlot;
            }
            routeVariant = "FALLBACK_STAGGERED";
            altRoute = $"{normTeam.ToLowerInvariant()}_{spawnBucket.ToLowerInvariant()}_to_{targetSpotId}_fallback";
            delayMs = 450;
        }

        string routeId = routeVariant == "PRIMARY"
            ? $"{normTeam.ToLowerInvariant()}_{spawnBucket.ToLowerInvariant()}_to_{targetSpotId}_primary"
            : altRoute;

        suggestion = new OpeningRouteSuggestion
        {
            RoundId = roundId,
            PlayerSlot = pseudonymizedSlot,
            RawSlot = rawSlot,
            Team = normTeam,
            Role = role,
            SpawnBucket = spawnBucket,
            TargetSpot = targetSpotId,
            TargetSector = tpl.Sector,
            RouteId = routeId,
            RouteVariant = routeVariant,
            AllowedCorridor = tpl.Corridor,
            ForbiddenCorridors = new List<string>(tpl.Forbidden),
            OrderedWaypoints = waypoints,
            TransitionWaypoints = transitionWps,
            CanonicalSteps = canonicalSteps,
            WeaponReadyWaypoint = tpl.WeaponReadyWp,
            FirstThreatLine = tpl.ThreatLine,
            ExpectedDistance = Math.Round(expDist, 1),
            ExpectedArrivalSeconds = Math.Round(expSec, 2),
            DeadlineSeconds = Math.Round(deadlineSec, 2),
            KnifeAllowedUntil = Math.Round(knifeUntil, 2),
            KnifeStartTick = knifeStartTick,
            WeaponSwitchTick = weaponSwitchTick,
            ThreatLineTick = threatLineTick,
            FirstPossibleContactTick = firstPossibleContactTick,
            DistanceToThreatAtSwitch = Math.Round(distThreatAtSwitch, 1),
            WeaponReadyBeforeContact = weaponReadyBeforeContact,
            FirstPreaimTarget = tpl.Preaim,
            ConflictGroup = tpl.ConflictGroup,
            ConflictDetected = conflictDetected,
            PriorityWinner = priorityWinner,
            DelayedBot = delayedBot,
            AlternativeRoute = altRoute,
            DelayMs = delayMs,
            BlockedDurationMs = 0,
            PlannerControlActive = false,
            UtilityDecisionPreserved = true,
        };

        _roundSuggestions[(roundId, rawSlot)] = suggestion;
        if (!_conflictWinners.ContainsKey(cgKey))
        {
            _conflictWinners[cgKey] = suggestion;
        }
        _allSuggestions.Add(suggestion);
        return true;
    }

    public IReadOnlyList<OpeningRouteSuggestion> ResolveBatchConflicts(
        int roundId,
        IEnumerable<(int RawSlot, string PlayerSlot, string Team, string Role, string TargetSpot, string SpotSector, float StartX, float StartY, float StartZ, float TargetX, float TargetY, float TargetZ, int Tick)> candidates)
    {
        var ordered = candidates
            .OrderByDescending(c => SpawnBucketClassifier.Classify(c.Team, c.StartX, c.StartY, c.StartZ).EndsWith("_FAST", StringComparison.Ordinal))
            .ThenByDescending(c => RolePriorityRank(c.Role))
            .ThenBy(c => c.RawSlot)
            .ToList();

        var results = new List<OpeningRouteSuggestion>(ordered.Count);
        foreach (var c in ordered)
        {
            if (TryPlanOpeningRouteForRound(
                    roundId, c.RawSlot, c.PlayerSlot, c.Team, c.Role,
                    c.TargetSpot, c.SpotSector,
                    c.StartX, c.StartY, c.StartZ,
                    c.TargetX, c.TargetY, c.TargetZ,
                    c.Tick, out var sug) && sug != null)
            {
                results.Add(sug);
            }
        }
        return results;
    }

    public static int ComparePriority(string bucketA, string roleA, int slotA, string bucketB, string roleB, int slotB)
    {
        int fastA = bucketA.EndsWith("_FAST", StringComparison.Ordinal) ? 1 : 0;
        int fastB = bucketB.EndsWith("_FAST", StringComparison.Ordinal) ? 1 : 0;
        if (fastA != fastB) return fastA.CompareTo(fastB);

        int rankA = RolePriorityRank(roleA);
        int rankB = RolePriorityRank(roleB);
        if (rankA != rankB) return rankA.CompareTo(rankB);

        return slotB.CompareTo(slotA);
    }

    public static int RolePriorityRank(string role) => role switch
    {
        "AWPer" => 4,
        "EntryFragger" => 3,
        "Anchor" => 2,
        _ => 1,
    };

    private static string PickCorridorKey(string normTeam, string spotId, string sector)
    {
        if (normTeam == "CT")
        {
            if (spotId.Contains("b_short_arch", StringComparison.Ordinal)) return "MID_SHORT";
            if (spotId.Contains("market", StringComparison.Ordinal) || spotId.Contains("b_", StringComparison.Ordinal) ||
                sector.Contains("Bombsite B", StringComparison.OrdinalIgnoreCase) || sector.Contains("Mercado B", StringComparison.OrdinalIgnoreCase) ||
                sector.Contains("Apartamentos B", StringComparison.OrdinalIgnoreCase))
            {
                return "B_MARKET";
            }
            if (spotId.Contains("window", StringComparison.Ordinal) || spotId.Contains("ladder", StringComparison.Ordinal) ||
                spotId.Contains("underground", StringComparison.Ordinal) || spotId.Contains("chair", StringComparison.Ordinal) ||
                spotId.Contains("catwalk", StringComparison.Ordinal))
            {
                return "MID_WINDOW";
            }
            if (spotId.Contains("jungle", StringComparison.Ordinal) || spotId.Contains("vents", StringComparison.Ordinal) ||
                spotId.Contains("stairs", StringComparison.Ordinal) || spotId.Contains("connector", StringComparison.Ordinal))
            {
                return "A_JUNGLE";
            }
            return "A_TICKET";
        }

        if (spotId.Contains("palace", StringComparison.Ordinal) && !spotId.Contains("tetris", StringComparison.Ordinal)) return "A_PALACE";
        if (spotId.Contains("underground", StringComparison.Ordinal) || spotId.Contains("catwalk", StringComparison.Ordinal)) return "MID_UNDERPASS";
        if (spotId.Contains("mid_", StringComparison.Ordinal)) return "MID_TOP";
        if (spotId.Contains("b_", StringComparison.Ordinal) || sector.Contains("Bombsite B", StringComparison.OrdinalIgnoreCase) ||
            sector.Contains("Apartamentos B", StringComparison.OrdinalIgnoreCase) || sector.Contains("Mercado B", StringComparison.OrdinalIgnoreCase))
        {
            return "B_APPS";
        }
        return "A_RAMP";
    }

    private static double ComputePolylineLength(float sx, float sy, float sz, List<RouteWaypoint> wps)
    {
        double total = 0.0;
        float px = sx, py = sy, pz = sz;
        foreach (var w in wps)
        {
            total += Math.Sqrt((w.X - px) * (w.X - px) + (w.Y - py) * (w.Y - py) + (w.Z - pz) * (w.Z - pz));
            px = w.X;
            py = w.Y;
            pz = w.Z;
        }
        return total;
    }

    public void FlushJsonl(string path)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        using var sw = new StreamWriter(path, append: false);
        foreach (var s in _allSuggestions)
        {
            sw.WriteLine(JsonSerializer.Serialize(s));
        }
    }
}
