using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class MapPlayableBounds
{
    public string MapName { get; init; } = "de_mirage";

    // Nível 1: Bounds amplos de segurança (detectam corrupção, sentinel values e pawns fora do mundo)
    public float MinSafeX { get; init; } = -3500f;
    public float MaxSafeX { get; init; } = 3500f;
    public float MinSafeY { get; init; } = -3500f;
    public float MaxSafeY { get; init; } = 3500f;
    public float MinSafeZ { get; init; } = -450f;
    public float MaxSafeZ { get; init; } = 1200f;

    // Nível 2: Regiões jogáveis táticas/NavMesh
    public float MinPlayableX { get; init; } = -2700f;
    public float MaxPlayableX { get; init; } = 2400f;
    public float MinPlayableY { get; init; } = -2700f;
    public float MaxPlayableY { get; init; } = 2400f;
    public float MinPlayableZ { get; init; } = -280f;
    public float MaxPlayableZ { get; init; } = 400f;

    private static readonly Dictionary<string, MapPlayableBounds> KnownMapBounds = new(StringComparer.OrdinalIgnoreCase)
    {
        ["de_mirage"] = new MapPlayableBounds
        {
            MapName = "de_mirage",
            MinSafeX = -3500f,
            MaxSafeX = 3500f,
            MinSafeY = -3500f,
            MaxSafeY = 3500f,
            MinSafeZ = -450f,
            MaxSafeZ = 1200f,
            MinPlayableX = -2700f,
            MaxPlayableX = 2400f,
            MinPlayableY = -2700f,
            MaxPlayableY = 2400f,
            MinPlayableZ = -280f,
            MaxPlayableZ = 400f
        },
        ["de_dust2"] = new MapPlayableBounds
        {
            MapName = "de_dust2",
            MinSafeX = -3200f,
            MaxSafeX = 3200f,
            MinSafeY = -3200f,
            MaxSafeY = 3200f,
            MinSafeZ = -400f,
            MaxSafeZ = 1200f,
            MinPlayableX = -2500f,
            MaxPlayableX = 2500f,
            MinPlayableY = -2500f,
            MaxPlayableY = 2500f,
            MinPlayableZ = -200f,
            MaxPlayableZ = 450f
        },
        ["de_inferno"] = new MapPlayableBounds
        {
            MapName = "de_inferno",
            MinSafeX = -3500f,
            MaxSafeX = 3500f,
            MinSafeY = -3500f,
            MaxSafeY = 3500f,
            MinSafeZ = -400f,
            MaxSafeZ = 1200f,
            MinPlayableX = -2600f,
            MaxPlayableX = 2600f,
            MinPlayableY = -2600f,
            MaxPlayableY = 2600f,
            MinPlayableZ = -200f,
            MaxPlayableZ = 450f
        }
    };

    public static MapPlayableBounds GetBoundsForMap(string? mapName)
    {
        if (string.IsNullOrWhiteSpace(mapName))
        {
            return KnownMapBounds["de_mirage"];
        }

        string clean = mapName.Trim().ToLowerInvariant();
        if (clean.StartsWith("workshop/"))
        {
            int lastSlash = clean.LastIndexOf('/');
            if (lastSlash >= 0 && lastSlash + 1 < clean.Length)
            {
                clean = clean.Substring(lastSlash + 1);
            }
        }

        foreach (var kvp in KnownMapBounds)
        {
            if (clean.Contains(kvp.Key))
            {
                return kvp.Value;
            }
        }

        return KnownMapBounds["de_mirage"];
    }

    /// <summary>
    /// Transforma uma coordenada de objetivo sugerida de seu espaço específico para coordenadas absolutas de mundo.
    /// Suporta WorldAbsolute, PawnRelative, ViewRelative (com yaw) e NormalizedDirection.
    /// </summary>
    public static Vector TransformSuggestedGoalToWorld(
        Vector inputCoord,
        SuggestedGoalCoordinateSpace space,
        Vector pawnPos,
        float yawDegrees)
    {
        switch (space)
        {
            case SuggestedGoalCoordinateSpace.WorldAbsolute:
                return inputCoord;

            case SuggestedGoalCoordinateSpace.PawnRelative:
                return new Vector(pawnPos.X + inputCoord.X, pawnPos.Y + inputCoord.Y, pawnPos.Z + inputCoord.Z);

            case SuggestedGoalCoordinateSpace.ViewRelative:
            {
                // CS2 / Source 2: yaw 0° = +X (East), yaw 90° = +Y (North), yaw 180° = -X (West), yaw 270° = -Y (South)
                // Forward vector = (cos, sin, 0)
                // Right vector = (sin, -cos, 0)
                float yawRad = yawDegrees * (MathF.PI / 180.0f);
                float cos = MathF.Cos(yawRad);
                float sin = MathF.Sin(yawRad);

                float worldX = pawnPos.X + (cos * inputCoord.X + sin * inputCoord.Y);
                float worldY = pawnPos.Y + (sin * inputCoord.X - cos * inputCoord.Y);
                float worldZ = pawnPos.Z + inputCoord.Z;
                return new Vector(worldX, worldY, worldZ);
            }

            case SuggestedGoalCoordinateSpace.NormalizedDirection:
            {
                float len = MathF.Sqrt(inputCoord.X * inputCoord.X + inputCoord.Y * inputCoord.Y + inputCoord.Z * inputCoord.Z);
                if (len < 0.0001f) return pawnPos;
                float normX = inputCoord.X / len;
                float normY = inputCoord.Y / len;
                float normZ = inputCoord.Z / len;
                return new Vector(pawnPos.X + normX * 64f, pawnPos.Y + normY * 64f, pawnPos.Z + normZ * 64f);
            }

            default:
                return pawnPos;
        }
    }

    public static GoalValidationResult ValidateGoal(
        Vector goal,
        Vector? currentPawnPos = null,
        string? mapName = null,
        string context = "General")
    {
        if (float.IsNaN(goal.X) || float.IsNaN(goal.Y) || float.IsNaN(goal.Z) ||
            float.IsInfinity(goal.X) || float.IsInfinity(goal.Y) || float.IsInfinity(goal.Z))
        {
            return new GoalValidationResult(
                IsValid: false,
                Status: GoalValidationStatus.ZeroOrNaN,
                SanitizedGoal: currentPawnPos ?? new Vector(0, 0, 0),
                Reason: $"Coordenadas com NaN/Infinity no contexto '{context}'");
        }

        if (MathF.Abs(goal.X) < 0.001f && MathF.Abs(goal.Y) < 0.001f && MathF.Abs(goal.Z) < 0.001f)
        {
            return new GoalValidationResult(
                IsValid: false,
                Status: GoalValidationStatus.ZeroOrNaN,
                SanitizedGoal: currentPawnPos ?? new Vector(0, 0, 0),
                Reason: $"Goal é exatamente zero (origem inválida/não inicializada) no contexto '{context}'");
        }

        var bounds = GetBoundsForMap(mapName);

        // Nível 1: Verificação de Bounds Amplos de Segurança
        if (goal.X < bounds.MinSafeX || goal.X > bounds.MaxSafeX ||
            goal.Y < bounds.MinSafeY || goal.Y > bounds.MaxSafeY ||
            goal.Z < bounds.MinSafeZ || goal.Z > bounds.MaxSafeZ)
        {
            return new GoalValidationResult(
                IsValid: false,
                Status: GoalValidationStatus.OutsideSafetyBounds,
                SanitizedGoal: currentPawnPos ?? new Vector(0, 0, 0),
                Reason: $"Goal fora dos limites amplos de segurança ({goal.X:F0},{goal.Y:F0},{goal.Z:F0}) vs SafeZ [{bounds.MinSafeZ:F0},{bounds.MaxSafeZ:F0}] no contexto '{context}'");
        }

        // Se o pawn de origem foi fornecido, validar se a distância até o goal não é absurda
        if (currentPawnPos != null)
        {
            float dx = goal.X - currentPawnPos.X;
            float dy = goal.Y - currentPawnPos.Y;
            float dz = goal.Z - currentPawnPos.Z;
            float distSq = dx * dx + dy * dy + dz * dz;

            // Se a distância for > 8000u (diagonal máxima do mapa é ~6000u), coordenada corrompida
            if (distSq > 64000000.0f)
            {
                return new GoalValidationResult(
                    IsValid: false,
                    Status: GoalValidationStatus.OutsideSafetyBounds,
                    SanitizedGoal: currentPawnPos,
                    Reason: $"Goal excessivamente distante do pawn ({MathF.Sqrt(distSq):F0}u > 8000u) no contexto '{context}'");
            }
        }

        return new GoalValidationResult(
            IsValid: true,
            Status: GoalValidationStatus.Valid,
            SanitizedGoal: goal,
            Reason: "Objetivo válido dentro dos limites do mapa");
    }

    /// <summary>
    /// Instrumenta anomalia de Z extremo ou pawn fora do mundo com todos os 21 campos requeridos para diagnóstico forense.
    /// </summary>
    public static void LogExtremeCoordinateAnomaly(
        MatchTelemetryLogger? telemetry,
        long internalRoundId,
        long gameTick,
        int botSlot,
        int controllerIndex,
        int pawnIndex,
        bool pawnValid,
        int pawnLifeState,
        Vector? absOrigin,
        Vector? absVelocity,
        Vector? goalPosition,
        float targetX,
        float targetY,
        float targetZ,
        string activeWaypointId,
        string selectedRecoveryWaypoint,
        string suggestedGoalRaw,
        string suggestedGoalInterpreted,
        MovementIntentSource intentSource,
        MovementCommandKind intentKind,
        string movementScope,
        PhysicalExecutionOutcome physicalOutcome,
        bool deathState,
        float timeSinceDeath,
        string mapName)
    {
        if (telemetry == null || !telemetry.IsEnabled) return;

        string originStr = absOrigin != null ? $"{absOrigin.X:F1},{absOrigin.Y:F1},{absOrigin.Z:F1}" : "NULL";
        string velStr = absVelocity != null ? $"{absVelocity.X:F1},{absVelocity.Y:F1},{absVelocity.Z:F1}" : "NULL";
        string goalStr = goalPosition != null ? $"{goalPosition.X:F1},{goalPosition.Y:F1},{goalPosition.Z:F1}" : "NULL";

        string anomalyReport =
            $"**[⚠️ ANOMALIA DE COORDENADA/Z EXTREMO DETECTADA]**\n" +
            $"- InternalRoundId: {internalRoundId}\n" +
            $"- GameTick: {gameTick}\n" +
            $"- BotSlot: {botSlot}\n" +
            $"- ControllerEntityIndex: {controllerIndex}\n" +
            $"- PawnEntityIndex: {pawnIndex}\n" +
            $"- PawnValidity: {pawnValid}\n" +
            $"- PawnLifeState: {pawnLifeState}\n" +
            $"- PawnAbsOrigin: `{originStr}`\n" +
            $"- PawnAbsVelocity: `{velStr}`\n" +
            $"- GoalPosition: `{goalStr}`\n" +
            $"- TargetX/Y/Z: `{targetX:F1},{targetY:F1},{targetZ:F1}`\n" +
            $"- ActiveWaypointId: `{activeWaypointId}`\n" +
            $"- SelectedRecoveryWaypoint: `{selectedRecoveryWaypoint}`\n" +
            $"- SuggestedGoalRaw: `{suggestedGoalRaw}`\n" +
            $"- SuggestedGoalInterpreted: `{suggestedGoalInterpreted}`\n" +
            $"- MovementIntentSource: {intentSource}\n" +
            $"- MovementIntentKind: {intentKind}\n" +
            $"- MovementScope: {movementScope}\n" +
            $"- PhysicalOutcome: {physicalOutcome}\n" +
            $"- DeathState: {deathState}\n" +
            $"- TimeSinceDeath: {timeSinceDeath:F2}s\n" +
            $"- MapName: {mapName}";

        telemetry.LogAnomaly(anomalyReport);
    }
}
