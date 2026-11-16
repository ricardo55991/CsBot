using System;
using System.Collections.Concurrent;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class GameplaySpotEventRecord
{
    [JsonPropertyName("EventType")]
    public string EventType { get; set; } = string.Empty;

    [JsonPropertyName("TimestampUtc")]
    public string TimestampUtc { get; set; } = string.Empty;

    [JsonPropertyName("InternalRoundId")]
    public long InternalRoundId { get; set; }

    [JsonPropertyName("OfficialRoundNumber")]
    public int OfficialRoundNumber { get; set; }

    [JsonPropertyName("Team")]
    public string Team { get; set; } = string.Empty;

    [JsonPropertyName("BotSlot")]
    public int BotSlot { get; set; }

    [JsonPropertyName("Role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("TacticId")]
    public string TacticId { get; set; } = string.Empty;

    [JsonPropertyName("TacticRevision")]
    public int TacticRevision { get; set; }

    [JsonPropertyName("PlanStage")]
    public string PlanStage { get; set; } = string.Empty;

    [JsonPropertyName("SpotId")]
    public string SpotId { get; set; } = string.Empty;

    [JsonPropertyName("SpotUsage")]
    public string SpotUsage { get; set; } = string.Empty;

    [JsonPropertyName("AssociatedBombsite")]
    public string AssociatedBombsite { get; set; } = string.Empty;

    [JsonPropertyName("StartPosition")]
    public float[] StartPosition { get; set; } = Array.Empty<float>();

    [JsonPropertyName("TargetPosition")]
    public float[] TargetPosition { get; set; } = Array.Empty<float>();

    [JsonPropertyName("FinalPosition")]
    public float[] FinalPosition { get; set; } = Array.Empty<float>();

    [JsonPropertyName("StartTick")]
    public int StartTick { get; set; }

    [JsonPropertyName("EndTick")]
    public int EndTick { get; set; }

    [JsonPropertyName("ElapsedMs")]
    public float ElapsedMs { get; set; }

    [JsonPropertyName("DistanceRemaining")]
    public float DistanceRemaining { get; set; }

    [JsonPropertyName("RepathCount")]
    public int RepathCount { get; set; }

    [JsonPropertyName("RecoveryCount")]
    public int RecoveryCount { get; set; }

    [JsonPropertyName("AbandonReason")]
    public string AbandonReason { get; set; } = string.Empty;

    [JsonPropertyName("ReplacementSpotId")]
    public string ReplacementSpotId { get; set; } = string.Empty;

    [JsonPropertyName("requested_spot")]
    public string RequestedSpot { get; set; } = string.Empty;

    [JsonPropertyName("requested_side")]
    public string RequestedSide { get; set; } = string.Empty;

    [JsonPropertyName("requested_state")]
    public string RequestedState { get; set; } = string.Empty;

    [JsonPropertyName("requested_phase")]
    public string RequestedPhase { get; set; } = string.Empty;

    [JsonPropertyName("validation_result")]
    public string ValidationResult { get; set; } = "VALID";

    [JsonPropertyName("rejection_reason")]
    public string RejectionReason { get; set; } = "NONE";

    [JsonPropertyName("replacement_spot")]
    public string ReplacementSpot { get; set; } = string.Empty;

    [JsonPropertyName("replacement_reason")]
    public string ReplacementReason { get; set; } = string.Empty;

    [JsonPropertyName("fallback_used")]
    public bool FallbackUsed { get; set; }
}

public sealed class GameplaySpotTelemetryTracker
{
    private sealed class ActiveSpotEpisode
    {
        public TacticalSpot Spot { get; set; } = new();
        public int BotSlot { get; set; }
        public string Team { get; set; } = string.Empty;
        public string Role { get; set; } = string.Empty;
        public string TacticId { get; set; } = string.Empty;
        public int TacticRevision { get; set; }
        public string PlanStage { get; set; } = string.Empty;
        public string Usage { get; set; } = string.Empty;
        public string Bombsite { get; set; } = string.Empty;
        public Vector StartPos { get; set; } = new(0, 0, 0);
        public int StartTick { get; set; }
        public float StartTime { get; set; }
        public int RepathCount { get; set; }
        public int RecoveryCount { get; set; }
        public bool Reached { get; set; }
        public bool Holding { get; set; }
        public float HoldStartTime { get; set; }
        public UtilitySpotValidationOutcome? ValidationOutcome { get; set; }
    }

    private readonly CsBotManagerPlugin? _plugin;
    private readonly ConcurrentDictionary<int, ActiveSpotEpisode> _episodesBySlot = new();
    private static readonly UTF8Encoding Utf8NoBom = new(false);
    private readonly object _writeLock = new();

    private readonly string _repoLogPath = @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_6\profile_v2_normal_match_events.jsonl";
    private readonly string _serverLogPath = @"H:\CS2_AI_Server\debug_logs\profile_v2_normal_match_events.jsonl";

    public GameplaySpotTelemetryTracker(CsBotManagerPlugin? plugin)
    {
        _plugin = plugin;
    }

    public UtilitySpotValidationContext BuildValidationContext(
        CCSPlayerController bot,
        Vector? currentPos,
        ISet<string>? occupiedSpots = null,
        ISet<string>? blacklistedSpots = null)
    {
        bool isT = bot.Team == CsTeam.Terrorist;
        bool isCt = bot.Team == CsTeam.CounterTerrorist;
        bool isBombPlanted = _plugin?.IsBombPlantedState ?? false;
        bool isFreezeTime = _plugin?.IsFreezeTimeState ?? false;
        bool hasC4 = bot.PlayerPawn.Value?.WeaponServices?.ActiveWeapon.Value?.DesignerName?.Contains("c4", StringComparison.OrdinalIgnoreCase) == true;
        string phase = isBombPlanted
            ? (isT ? "PostPlant" : "Retake")
            : (isFreezeTime ? "Setup" : (_plugin?.CurrentPlan?.RoundTempo.ToString() ?? "MapControl"));
        string state = isBombPlanted
            ? (isCt ? "RETAKE" : "HOLD")
            : (isT && hasC4 ? "OBJECTIVE" : "HOLD");
        string role = _plugin?.RoleManager?.GetBotRole(bot)?.ToString() ?? "Rotator";

        return new UtilitySpotValidationContext
        {
            MapName = "de_mirage",
            RequestedSide = isT ? "TR" : "CT",
            RequestedState = state,
            RequestedPhase = phase,
            Role = role,
            ObjectiveEligible = isT && (isBombPlanted || hasC4),
            RetakeEligible = isCt && isBombPlanted,
            IsBombPlanted = isBombPlanted,
            CurrentX = currentPos?.X ?? 0f,
            CurrentY = currentPos?.Y ?? 0f,
            CurrentZ = currentPos?.Z ?? 0f,
            OccupiedSpotIds = occupiedSpots ?? new HashSet<string>(StringComparer.OrdinalIgnoreCase),
            BlacklistedSpotIds = blacklistedSpots ?? new HashSet<string>(StringComparer.OrdinalIgnoreCase),
        };
    }

    public void OnSpotAssigned(int slot, CCSPlayerController bot, TacticalSpot spot, Vector startPos, int gameTick, float currentTime, UtilitySpotValidationOutcome? validationOutcome = null)
    {
        var episode = CreateEpisode(slot, bot, spot, startPos, gameTick, currentTime, validationOutcome);
        _episodesBySlot[slot] = episode;

        EmitEvent("SPOT_ASSIGNED", episode, startPos, gameTick, currentTime);
        EmitEvent("SPOT_NAVIGATION_STARTED", episode, startPos, gameTick, currentTime);
    }

    public void OnSpotReached(int slot, CCSPlayerController bot, Vector curPos, int gameTick, float currentTime)
    {
        if (!_episodesBySlot.TryGetValue(slot, out var ep)) return;
        if (ep.Reached) return;

        ep.Reached = true;
        ep.Holding = true;
        ep.HoldStartTime = currentTime;

        EmitEvent("SPOT_REACHED", ep, curPos, gameTick, currentTime);
        EmitEvent("SPOT_HOLD_STARTED", ep, curPos, gameTick, currentTime);
    }

    public void OnSpotHoldEnded(int slot, CCSPlayerController bot, Vector curPos, int gameTick, float currentTime, string reason)
    {
        if (!_episodesBySlot.TryGetValue(slot, out var ep)) return;
        if (!ep.Holding) return;

        ep.Holding = false;
        EmitEvent("SPOT_HOLD_ENDED", ep, curPos, gameTick, currentTime, abandonReason: reason);
    }

    public void OnSpotRepath(int slot, CCSPlayerController bot, Vector curPos, int gameTick, float currentTime)
    {
        if (!_episodesBySlot.TryGetValue(slot, out var ep)) return;
        ep.RepathCount++;
        EmitEvent("SPOT_REPATH", ep, curPos, gameTick, currentTime);
    }

    public void OnSpotRecovery(int slot, CCSPlayerController bot, Vector curPos, int gameTick, float currentTime)
    {
        if (!_episodesBySlot.TryGetValue(slot, out var ep)) return;
        ep.RecoveryCount++;
        EmitEvent("SPOT_RECOVERY", ep, curPos, gameTick, currentTime);
    }

    public void OnSpotReplaced(int slot, CCSPlayerController bot, TacticalSpot newSpot, Vector curPos, int gameTick, float currentTime, string reason, UtilitySpotValidationOutcome? validationOutcome = null)
    {
        if (!_episodesBySlot.TryGetValue(slot, out var oldEp)) return;

        EmitEvent("SPOT_REPLACED", oldEp, curPos, gameTick, currentTime, abandonReason: reason, replacementSpotId: newSpot.Id);

        var newEp = CreateEpisode(slot, bot, newSpot, curPos, gameTick, currentTime, validationOutcome);
        _episodesBySlot[slot] = newEp;

        EmitEvent("SPOT_ASSIGNED", newEp, curPos, gameTick, currentTime);
        EmitEvent("SPOT_NAVIGATION_STARTED", newEp, curPos, gameTick, currentTime);
    }

    public void OnSpotAbandoned(int slot, CCSPlayerController bot, Vector curPos, int gameTick, float currentTime, string reason)
    {
        if (!_episodesBySlot.TryRemove(slot, out var ep)) return;

        if (ep.Holding)
        {
            EmitEvent("SPOT_HOLD_ENDED", ep, curPos, gameTick, currentTime, abandonReason: reason);
        }
        EmitEvent("SPOT_ABANDONED", ep, curPos, gameTick, currentTime, abandonReason: reason);
    }

    public void OnRoundEnd()
    {
        _episodesBySlot.Clear();
    }

    private ActiveSpotEpisode CreateEpisode(int slot, CCSPlayerController bot, TacticalSpot spot, Vector startPos, int gameTick, float currentTime, UtilitySpotValidationOutcome? validationOutcome = null)
    {
        string teamStr = bot.Team == CsTeam.CounterTerrorist ? "CT" : "TR";
        string roleStr = _plugin?.RoleManager?.GetBotRole(bot)?.ToString() ?? "Rifle";
        var plan = _plugin?.CurrentPlan;
        string tacticId = plan?.TacticName ?? (teamStr == "CT" ? "CT_STANDARD_2_1_2_BALANCED" : "TR_DEFAULT_DEFAULT");
        int tacticRev = plan?.TacticRevision ?? 1;
        string planStage = plan?.RoundTempo.ToString() ?? "Staging";
        string usageStr = spot.Usage.ToString();
        string bombsite = PresetSpatialValidator.DetermineSpotBombsite(spot);

        return new ActiveSpotEpisode
        {
            Spot = spot,
            BotSlot = slot,
            Team = teamStr,
            Role = roleStr,
            TacticId = tacticId,
            TacticRevision = tacticRev,
            PlanStage = planStage,
            Usage = usageStr,
            Bombsite = bombsite,
            StartPos = new Vector(startPos.X, startPos.Y, startPos.Z),
            StartTick = gameTick,
            StartTime = currentTime,
            RepathCount = 0,
            RecoveryCount = 0,
            Reached = false,
            Holding = false,
            HoldStartTime = 0f,
            ValidationOutcome = validationOutcome
        };
    }

    private void EmitEvent(
        string eventType,
        ActiveSpotEpisode ep,
        Vector curPos,
        int gameTick,
        float currentTime,
        string abandonReason = "",
        string replacementSpotId = "")
    {
        long internalRoundId = _plugin?.LifecycleManager?.CurrentInternalRoundId ?? 1L;
        int officialRound = _plugin?.LifecycleManager?.CurrentRound?.OfficialRoundNumber ?? 1;

        float dx = curPos.X - ep.Spot.X;
        float dy = curPos.Y - ep.Spot.Y;
        float dz = curPos.Z - ep.Spot.Z;
        float distRem = MathF.Sqrt(dx * dx + dy * dy + dz * dz);
        float elapsedMs = Math.Max(0f, (currentTime - ep.StartTime) * 1000f);

        var record = new GameplaySpotEventRecord
        {
            EventType = eventType,
            TimestampUtc = DateTime.UtcNow.ToString("O"),
            InternalRoundId = internalRoundId,
            OfficialRoundNumber = officialRound,
            Team = ep.Team,
            BotSlot = ep.BotSlot,
            Role = ep.Role,
            TacticId = ep.TacticId,
            TacticRevision = ep.TacticRevision,
            PlanStage = ep.PlanStage,
            SpotId = ep.Spot.Id,
            SpotUsage = ep.Usage,
            AssociatedBombsite = ep.Bombsite,
            StartPosition = new[]
            {
                MathF.Round(ep.StartPos.X, 1),
                MathF.Round(ep.StartPos.Y, 1),
                MathF.Round(ep.StartPos.Z, 1)
            },
            TargetPosition = new[]
            {
                MathF.Round(ep.Spot.X, 1),
                MathF.Round(ep.Spot.Y, 1),
                MathF.Round(ep.Spot.Z, 1)
            },
            FinalPosition = new[]
            {
                MathF.Round(curPos.X, 1),
                MathF.Round(curPos.Y, 1),
                MathF.Round(curPos.Z, 1)
            },
            StartTick = ep.StartTick,
            EndTick = gameTick,
            ElapsedMs = MathF.Round(elapsedMs, 1),
            DistanceRemaining = MathF.Round(distRem, 1),
            RepathCount = ep.RepathCount,
            RecoveryCount = ep.RecoveryCount,
            AbandonReason = abandonReason,
            ReplacementSpotId = replacementSpotId,
            RequestedSpot = ep.ValidationOutcome?.RequestedSpot ?? ep.Spot.Id,
            RequestedSide = ep.ValidationOutcome?.RequestedSide ?? ep.Team,
            RequestedState = ep.ValidationOutcome?.RequestedState ?? ep.Usage,
            RequestedPhase = ep.ValidationOutcome?.RequestedPhase ?? ep.PlanStage,
            ValidationResult = ep.ValidationOutcome?.ValidationResult ?? "VALID",
            RejectionReason = (ep.ValidationOutcome?.RejectionReason ?? SpotAssignmentRejectionReason.NONE).ToString(),
            ReplacementSpot = ep.ValidationOutcome?.ReplacementSpot ?? replacementSpotId,
            ReplacementReason = ep.ValidationOutcome?.ReplacementReason ?? string.Empty,
            FallbackUsed = ep.ValidationOutcome?.FallbackUsed ?? false
        };

        string jsonLine = JsonSerializer.Serialize(record);
        WriteLineSafe(jsonLine);
    }

    private void WriteLineSafe(string line)
    {
        lock (_writeLock)
        {
            TryAppendLine(_repoLogPath, line);
            TryAppendLine(_serverLogPath, line);
        }
    }

    private static void TryAppendLine(string path, string line)
    {
        try
        {
            string? dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }
            File.AppendAllText(path, line + Environment.NewLine, Utf8NoBom);
        }
        catch { }
    }
}
