using System.Text.Json.Serialization;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public enum CtFormationRole
{
    A1_Anchor,
    A2_Support,
    Mid_Controller,
    B1_Anchor,
    B2_Support
}

public sealed class CtFormationAssignment
{
    public int Slot { get; set; }
    public CtFormationRole FormationRole { get; set; }
    public string AssignedSite { get; set; } = "Mid"; // "A", "Mid", "B"
    public string InitialSpot { get; set; } = string.Empty;
    public string ExecuteSpot { get; set; } = string.Empty;
    public string RotationPolicy { get; set; } = "HoldUntilTrigger";
    public float HoldMinimumDuration { get; set; } = 20.0f;
    public string RotationTrigger { get; set; } = "None";
}

public enum BuyState
{
    PISTOL_ROUND,
    FULL_ECO,
    LIGHT_BUY,
    FORCE_BUY,
    HALF_BUY,
    FULL_BUY,
    SAVE_WITH_WEAPONS,
    NOT_APPLICABLE,
    UNKNOWN_INCOMPLETE_BUY
}

public enum BuyCompletionState
{
    PENDING,
    STABILIZED,
    TIMEOUT,
    INCOMPLETE
}

public enum TacticalDecisionSource
{
    OLLAMA,
    FALLBACK_PRESET,
    CACHE,
    STATIC_DEFAULT,
    RECOVERED_PREVIOUS_VALID_PLAN
}

public enum BotRole
{
    AWPer,
    EntryFragger,
    Rotator,
    Anchor
}

public enum RoundTempo
{
    SLOW_DEFAULT,
    POKE_AND_ROTATE,
    TIMED_EXECUTE,
    FAST_CONTACT
}

public enum EngagementStance
{
    PASSIVE_HOLD,
    JIGGLE_INFO,
    ONE_AND_DONE,
    AGGRESSIVE_POKE
}

public enum RoundPhase
{
    FreezeTime,
    Staging,
    Executing,
    PostPlant
}

public enum AlertLevel
{
    Level0_Default,
    Level1_PressureNoBomb,
    Level2_BombConfirmed
}

public enum CtDuoPlayType
{
    None,
    DominioCavernaRamp,
    DominioMeio,
    HumanPartner
}

public enum TrTacticType
{
    Default,
    SPLIT_FAKE
}

public enum MidRoundAction
{
    NORMAL,
    HIDE_COVER,
    JIGGLE_PEEK,
    ROTATE_SILENT,
    WATCH_FLANK,
    RUSH_TRADE
}

public enum PlayTier
{
    Tier1_Standard,    // 72%
    Tier2_Alternative, // 20%
    Tier2_Moderate,
    Tier3_Unorthodox,  // 8%
    Tier3_Cheese
}

[Flags]
public enum SpotUsage
{
    None = 0,
    Spawn = 1,
    Staging = 2,
    Execute = 4,
    Hold = 8,
    Fallback = 16,
    Plant = 32,
    Retake = 64,
    Lurk = 128,
    Cover = 256,
    Defuse = 512,
    FlankWatch = 1024
}

public class TacticalSpot
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("sector")]
    public string Sector { get; set; } = string.Empty;

    [JsonPropertyName("side")]
    public string Side { get; set; } = "CT"; // "CT", "TR", "ANY"

    [JsonPropertyName("x")]
    public float X { get; set; }

    [JsonPropertyName("y")]
    public float Y { get; set; }

    [JsonPropertyName("z")]
    public float Z { get; set; }

    [JsonPropertyName("pitch")]
    public float Pitch { get; set; }

    [JsonPropertyName("yaw")]
    public float Yaw { get; set; }

    [JsonPropertyName("recommended_stance")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public EngagementStance RecommendedStance { get; set; } = EngagementStance.PASSIVE_HOLD;

    [JsonPropertyName("is_off_angle")]
    public bool IsOffAngle { get; set; } = false;

    [JsonPropertyName("fallback_spot_id")]
    public string? FallbackSpotId { get; set; }

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("associated_bombsite")]
    public string AssociatedBombsite { get; set; } = "None";

    [JsonPropertyName("usage")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public SpotUsage Usage { get; set; } = SpotUsage.Hold;

    [JsonPropertyName("allowed_roles")]
    public List<BotRole> AllowedRoles { get; set; } = new();
}

public class RoundHistoryItem
{
    public int RoundNumber { get; set; }
    public CsTeam Winner { get; set; }
    public string WinReason { get; set; } = string.Empty;
    public string? PlantedSite { get; set; }
    public string TacticUsed { get; set; } = string.Empty;
    public RoundTempo TempoUsed { get; set; } = RoundTempo.SLOW_DEFAULT;
}

public class BotTacticalOrder
{
    [JsonPropertyName("target_area")]
    public string TargetArea { get; set; } = "Bombsite A";

    [JsonPropertyName("role_action")]
    public string RoleAction { get; set; } = "Take position";

    [JsonPropertyName("staging_spot_id")]
    public string StagingSpotId { get; set; } = string.Empty;

    [JsonPropertyName("execute_spot_id")]
    public string ExecuteSpotId { get; set; } = string.Empty;

    [JsonPropertyName("stance")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public EngagementStance Stance { get; set; } = EngagementStance.PASSIVE_HOLD;

    [JsonPropertyName("fallback_spot_id")]
    public string FallbackSpotId { get; set; } = string.Empty;

    [JsonPropertyName("required_utilities")]
    public List<string> RequiredUtilities { get; set; } = new();

    [JsonPropertyName("aggression_level")]
    public string AggressionLevel { get; set; } = "medium";

    [JsonPropertyName("mid_round_action")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public MidRoundAction MidRoundAction { get; set; } = MidRoundAction.NORMAL;

    [JsonIgnore]
    public bool IsFallingBack { get; set; } = false;

    [JsonIgnore]
    public bool HoldSiteLocked { get; set; } = false;

    [JsonIgnore]
    public bool IsNoiseGroup { get; set; } = false;

    [JsonIgnore]
    public bool HasBomb { get; set; } = false;

    [JsonIgnore]
    public bool IsWatchingFlank { get; set; } = false;
}

public class TacticalPlan
{
    [JsonPropertyName("tactic_name")]
    public string TacticName { get; set; } = "Padrão Tático Cadenciado";

    [JsonPropertyName("tactic_summary")]
    public string TacticSummary { get; set; } = "Controle de mapa inicial e execução coordenada.";

    [JsonPropertyName("round_tempo")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public RoundTempo RoundTempo { get; set; } = RoundTempo.SLOW_DEFAULT;

    [JsonPropertyName("staging_duration_seconds")]
    public float StagingDurationSeconds { get; set; } = 18.0f;

    [JsonPropertyName("tr_tactic_type")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public TrTacticType TrTacticType { get; set; } = TrTacticType.Default;

    [JsonPropertyName("ct_duo_play")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public CtDuoPlayType CtDuoPlay { get; set; } = CtDuoPlayType.None;

    [JsonIgnore]
    public PlayTier PlayTier { get; set; } = PlayTier.Tier1_Standard;

    [JsonIgnore]
    public string PlayId { get; set; } = "STANDARD_HOLD";

    [JsonIgnore]
    public RoundPhase CurrentPhase { get; set; } = RoundPhase.FreezeTime;

    [JsonIgnore]
    public AlertLevel CurrentAlertLevel { get; set; } = AlertLevel.Level0_Default;

    [JsonIgnore]
    public string? FakeTargetSite { get; set; }

    [JsonIgnore]
    public string? RealTargetSite { get; set; }

    [JsonIgnore]
    public bool IsClockDesperationActive { get; set; } = false;

    [JsonIgnore]
    public bool IsLateRoundSilenceActive { get; set; } = false;

    [JsonIgnore]
    public bool IsTacticalSaveActive { get; set; } = false;

    [JsonIgnore]
    public bool IsHeroicAttempt { get; set; } = false;

    [JsonIgnore]
    public bool IsHumanPositionLocked { get; set; } = false;

    [JsonIgnore]
    public string HumanLockedSector { get; set; } = string.Empty;

    [JsonIgnore]
    public bool IsFlankCoverActive { get; set; } = false;

    [JsonIgnore]
    public string FlankCoverSpotId { get; set; } = string.Empty;

    [JsonPropertyName("bot_orders")]
    public Dictionary<string, BotTacticalOrder> BotOrders { get; set; } = new();

    [JsonIgnore]
    public Dictionary<int, CtFormationAssignment> CtFormationAssignments { get; } = new();

    [JsonIgnore]
    public FakeExecutionContext? FakeContext { get; set; }

    [JsonIgnore]
    public BombObjectiveState BombObjectiveState { get; set; } = new();

    [JsonIgnore]
    public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

    [JsonIgnore]
    public bool IsCustomPlayerCall { get; set; } = false;

    [JsonIgnore]
    public string RawJson { get; set; } = string.Empty;

    [JsonIgnore]
    public string DecisionId { get; set; } = string.Empty;

    [JsonIgnore]
    public int RoundId { get; set; }

    [JsonIgnore]
    public CsTeam TeamSide { get; set; } = CsTeam.None;



    [JsonIgnore]
    public CsTeam Team
    {
        get => TeamSide;
        set => TeamSide = value;
    }

    [JsonIgnore]
    public int RequestedAtTick { get; set; }

    [JsonIgnore]
    public int CompletedAtTick { get; set; }

    [JsonIgnore]
    public double LatencyMs { get; set; }

    [JsonIgnore]
    public TacticalDecisionSource Source { get; set; } = TacticalDecisionSource.FALLBACK_PRESET;

    [JsonIgnore]
    public bool CacheHit { get; set; }

    [JsonIgnore]
    public string CacheKey { get; set; } = string.Empty;

    [JsonIgnore]
    public bool FallbackUsed { get; set; }

    [JsonIgnore]
    public string FallbackReason { get; set; } = "NONE";

    [JsonIgnore]
    public string ParseStatus { get; set; } = "PENDING";

    [JsonIgnore]
    public string ModelResponseStatus { get; set; } = "PENDING";

    [JsonIgnore]
    public string SelectedTactic { get; set; } = string.Empty;

    [JsonIgnore]
    public List<string> CandidateTactics { get; set; } = new();

    [JsonIgnore]
    public Dictionary<string, double> SelectionScores { get; set; } = new();

    [JsonIgnore]
    public string SelectionReason { get; set; } = string.Empty;

    [JsonIgnore]
    public bool RepetitionPenaltyApplied { get; set; }

    [JsonIgnore]
    public string InitialTactic { get; set; } = "Padrão Tático Cadenciado";

    [JsonIgnore]
    public string CurrentTactic { get; set; } = "Padrão Tático Cadenciado";

    [JsonIgnore]
    public int TacticRevision { get; set; } = 1;

    [JsonIgnore]
    public string TacticSource { get; set; } = "FALLBACK_PRESET";

    [JsonIgnore]
    public int ChangedAtTick { get; set; }

    [JsonIgnore]
    public string ChangedAtRoundTime { get; set; } = "01:55";

    [JsonIgnore]
    public string ChangeReason { get; set; } = "Initial round plan";

    [JsonIgnore]
    public string TriggeringEvent { get; set; } = "RoundStart";

    [JsonIgnore]
    public string PreviousTargetSite { get; set; } = string.Empty;

    [JsonIgnore]
    public string CurrentTargetSite { get; set; } = string.Empty;

    [JsonIgnore]
    public float Confidence { get; set; } = 1.0f;

    public void InitializeVersioning(string tacticName, string targetSite, TacticalDecisionSource source, int tick, string roundTime = "01:55")
    {
        TacticName = tacticName;
        InitialTactic = tacticName;
        CurrentTactic = tacticName;
        SelectedTactic = tacticName;
        TacticRevision = 1;
        Source = source;
        TacticSource = source.ToString();
        ChangedAtTick = tick;
        ChangedAtRoundTime = roundTime;
        ChangeReason = "Initial round plan";
        TriggeringEvent = "RoundStart";
        PreviousTargetSite = targetSite;
        CurrentTargetSite = targetSite;
        RealTargetSite = targetSite;
        if (BombsiteParser.TryParseBombsiteTarget(targetSite, out var tSite))
        {
            BombObjectiveState.InternalRoundId = RoundId;
            BombObjectiveState.RealSite = tSite;
            BombObjectiveState.CommittedSite = tSite;
            BombObjectiveState.ObjectiveRevision = Guid.NewGuid();
            BombObjectiveState.UpdatedAtTick = tick;
            BombObjectiveState.UpdateReason = "Initial round plan";
        }
    }

    public void ApplyPivotRevision(
        string newTacticName,
        string newTargetSite,
        string changeReason,
        string triggeringEvent,
        int gameTick,
        string roundTime,
        float confidence,
        List<string>? candidates = null)
    {
        PreviousTargetSite = CurrentTargetSite;
        CurrentTargetSite = newTargetSite;
        RealTargetSite = newTargetSite;
        TacticName = newTacticName;
        CurrentTactic = newTacticName;
        SelectedTactic = newTacticName;
        TacticRevision++;
        TacticSource = "TACTICAL_PIVOT";
        ChangedAtTick = gameTick;
        ChangedAtRoundTime = roundTime;
        ChangeReason = changeReason;
        TriggeringEvent = triggeringEvent;
        Confidence = confidence;
        if (candidates != null && candidates.Count > 0)
        {
            CandidateTactics = candidates;
        }
        if (BombsiteParser.TryParseBombsiteTarget(newTargetSite, out var newTarget))
        {
            BombObjectiveState.UpdateCommittedSite(newTarget, $"Pivot to {newTarget}: {changeReason}", gameTick);
        }
    }

    public void SetFakeExecution(string fakeSite, string realSite, float duration, long currentTick, string reason = "FakeTacticSetup", string decisionId = "")
    {
        TrTacticType = TrTacticType.SPLIT_FAKE;
        FakeTargetSite = fakeSite;
        RealTargetSite = realSite;
        CurrentTargetSite = realSite;
        FakeContext = new FakeExecutionContext
        {
            FakeSite = fakeSite,
            RealSite = realSite,
            FakeDuration = duration,
            FakeGroupDisposition = FakeGroupDisposition.HoldRotation
        };

        var fs = BombsiteParser.TryParseBombsiteTarget(fakeSite, out var parsedFs) ? parsedFs : BombsiteTarget.A;
        var rs = BombsiteParser.TryParseBombsiteTarget(realSite, out var parsedRs) ? parsedRs : BombsiteTarget.B;

        BombObjectiveState.CommitMaterializedSite(
            !string.IsNullOrEmpty(decisionId) ? decisionId : DecisionId,
            TacticName,
            fs,
            rs,
            currentTick,
            reason);
    }
}

public class VoiceCommandPayload
{
    [JsonPropertyName("text")]
    public string Text { get; set; } = string.Empty;

    [JsonPropertyName("intent")]
    public string? Intent { get; set; }

    [JsonPropertyName("confidence")]
    public float Confidence { get; set; } = 1.0f;

    [JsonPropertyName("timestamp")]
    public long Timestamp { get; set; } = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
}

public enum SuggestedGoalCoordinateSpace
{
    None,
    WorldAbsolute,
    PawnRelative,
    ViewRelative,
    NormalizedDirection
}

public enum BombsiteTarget
{
    None,
    A,
    B,
    Mid,
    Dynamic
}

public static class BombsiteParser
{
    public static bool TryParseBombsiteTarget(string? input, out BombsiteTarget target)
    {
        target = BombsiteTarget.None;
        if (string.IsNullOrWhiteSpace(input)) return false;
        var trimmed = input.Trim().ToUpperInvariant();

        if (trimmed == "A" || trimmed == "BOMBSITE_A" || trimmed == "BOMBSITE A" || trimmed == "SITE A" || trimmed == "SITE_A" || trimmed.StartsWith("A_") || trimmed.EndsWith("_A"))
        {
            target = BombsiteTarget.A;
            return true;
        }
        if (trimmed == "B" || trimmed == "BOMBSITE_B" || trimmed == "BOMBSITE B" || trimmed == "SITE B" || trimmed == "SITE_B" || trimmed.StartsWith("B_") || trimmed.EndsWith("_B"))
        {
            target = BombsiteTarget.B;
            return true;
        }
        if (trimmed == "MID" || trimmed == "MIDDLE" || trimmed == "MEIO")
        {
            target = BombsiteTarget.Mid;
            return true;
        }
        if (trimmed == "DYNAMIC" || trimmed == "FLEX" || trimmed == "ANY")
        {
            target = BombsiteTarget.Dynamic;
            return true;
        }
        return false;
    }

    public static BombsiteTarget ParseOrDefault(string? input, BombsiteTarget fallback = BombsiteTarget.None)
    {
        return TryParseBombsiteTarget(input, out var target) ? target : fallback;
    }

    public static BombsiteTarget ResolveBombCarrierTargetSite(TacticalPlan? trPlan)
    {
        if (trPlan == null) return BombsiteTarget.None;

        // 1. Fonte única autoritativa tipada V4.2.6 / V4.2.7
        if (trPlan.BombObjectiveState != null && trPlan.BombObjectiveState.CommittedSite != BombsiteTarget.None)
        {
            return trPlan.BombObjectiveState.CommittedSite;
        }

        // 2. MaterializedRealSite do BombObjectiveState
        if (trPlan.BombObjectiveState != null && trPlan.BombObjectiveState.MaterializedRealSite != BombsiteTarget.None)
        {
            return trPlan.BombObjectiveState.MaterializedRealSite;
        }

        // 3. Em táticas fake, o objetivo da C4 é SEMPRE e EXCLUSIVAMENTE o RealSite
        if (trPlan.FakeContext != null && !string.IsNullOrWhiteSpace(trPlan.FakeContext.RealSite))
        {
            if (TryParseBombsiteTarget(trPlan.FakeContext.RealSite, out var fakeRealSite))
                return fakeRealSite;
        }

        // 4. RealTargetSite
        if (!string.IsNullOrWhiteSpace(trPlan.RealTargetSite))
        {
            if (TryParseBombsiteTarget(trPlan.RealTargetSite, out var realSite))
                return realSite;
        }

        // 5. TacticId / TacticName tipado (Fakes primeiro!)
        string tactic = trPlan.TacticName ?? trPlan.CurrentTactic ?? string.Empty;
        if (!string.IsNullOrWhiteSpace(tactic))
        {
            if (tactic.Contains("Fake A", StringComparison.OrdinalIgnoreCase)) return BombsiteTarget.B;
            if (tactic.Contains("Fake B", StringComparison.OrdinalIgnoreCase)) return BombsiteTarget.A;
            if (tactic.Contains("Execução B", StringComparison.OrdinalIgnoreCase) || tactic.Contains("Rush B", StringComparison.OrdinalIgnoreCase) || tactic.Contains("Split B", StringComparison.OrdinalIgnoreCase)) return BombsiteTarget.B;
            if (tactic.Contains("Execução A", StringComparison.OrdinalIgnoreCase) || tactic.Contains("Rush A", StringComparison.OrdinalIgnoreCase) || tactic.Contains("Split A", StringComparison.OrdinalIgnoreCase)) return BombsiteTarget.A;
        }

        // 6. CurrentTargetSite (apenas fallback se nenhum dos anteriores resolveu)
        if (!string.IsNullOrWhiteSpace(trPlan.CurrentTargetSite))
        {
            if (TryParseBombsiteTarget(trPlan.CurrentTargetSite, out var currSite))
                return currSite;
        }

        return BombsiteTarget.None;
    }
}

public sealed class MaterializedRetakePlan
{
    public BombsiteTarget PlantedSite { get; init; } = BombsiteTarget.None;
    public Vector BombPosition { get; init; } = new(0, 0, 0);
    public Dictionary<int, BotTacticalOrder> OrdersBySlot { get; init; } = new();
    public Dictionary<int, string> RoleBySlot { get; init; } = new();
    public List<string> MaterializedSpotIds { get; init; } = new();
}

public enum TacticalSpotUsage
{
    General,
    Staging,
    Execute,
    Retake,
    Lurk,
    FlankWatch,
    PostPlant,
    SaveHideout
}

public enum LocalRiskLevel
{
    Safe,
    Suspicious,
    Dangerous,
    Combat
}

public enum GrenadeActionState
{
    Idle,
    Selecting,
    PinPulled,
    Throwing,
    AwaitingRecoveryToWeapon,
    Completed,
    Failed
}

public enum GoalValidationStatus
{
    Valid,
    ClampedToPlayableBounds,
    OutsideSafetyBounds,
    InvalidCoordinates,
    ZeroOrNaN,
    PawnOutOfBoundsOrDead,
    GeometryUnreachable
}

public readonly record struct GoalValidationResult(
    bool IsValid,
    GoalValidationStatus Status,
    Vector SanitizedGoal,
    string Reason);

public sealed record CandidateSpotEvaluation(
    string SpotId,
    string SpotName,
    BombsiteTarget TargetSite,
    TacticalSpotUsage Usage,
    float Score,
    bool IsBlacklisted,
    bool IsOccupied,
    float DistanceToBot,
    string ScoreBreakdown);

public sealed record MatchRoundContext(
    int CurrentRound,
    int MaxRoundsPerHalf = 12,
    int MaxRoundsPerMatch = 24,
    bool IsOvertime = false,
    bool IsWarmup = false,
    int CtScore = 0,
    int TrScore = 0)
{
    public bool IsFinalRoundOfHalf => CurrentRound == MaxRoundsPerHalf;
    public bool IsFinalRoundOfRegulation => CurrentRound == MaxRoundsPerMatch;
    public bool IsMatchPointOrLastChance => IsFinalRoundOfHalf || IsFinalRoundOfRegulation || (CtScore >= 12 && TrScore < 12) || (TrScore >= 12 && CtScore < 12);
}

public sealed record BotSaveDecision(
    int BotSlot,
    bool ShouldSave,
    float SaveProbability,
    float RollValue,
    int EquipmentValue,
    bool HasAwp,
    bool HasDefuseKit,
    float DistanceToBomb,
    string Reason);

public sealed record TeamSaveDecision(
    CsTeam Team,
    bool TeamShouldSave,
    int AliveTeamCount,
    int AliveEnemyCount,
    bool BombPlanted,
    float BombTimeRemaining,
    IReadOnlyList<BotSaveDecision> BotDecisions,
    string Reason);

public enum TacticalAdaptationReason
{
    None,
    MolotovBlocked,
    SmokeObscured,
    EnemyContact,
    EntryKilled,
    AggressorKilled,
    TradePossible,
    TradeRequired,
    RegroupAfterEntryLoss,
    BombDropped,
    UtilityWait,
    SaveDecision,
    RetakeDecision,
    SiteClear,
    TimePressure,
    NumericalAdvantage,
    NumericalDisadvantage,
    FakeTriggered,
    FakeCancelled
}

public enum StandstillClassification
{
    GeometryBlock,
    CombatHold,
    CounterStrafe,
    AuthorizedHold,
    UtilityAction,
    PlantOrDefuse,
    Airborne,
    SmokeOrMolotovWait,
    Unknown
}

public enum FakeGroupDisposition
{
    None,
    HoldRotation,
    FallBack,
    WatchFlank,
    ConvergeLate
}

public class FakeExecutionContext
{
    public string FakeSite { get; set; } = "A";
    public string RealSite { get; set; } = "B";
    public List<int> FakeGroupSlots { get; set; } = new();
    public List<int> RealGroupSlots { get; set; } = new();
    public int BombCarrierSlot { get; set; } = -1;
    public float FakeDuration { get; set; } = 12.0f;
    public string RotationTrigger { get; set; } = "CT_ROTATION_CONFIRMED";
    public FakeGroupDisposition FakeGroupDisposition { get; set; } = FakeGroupDisposition.HoldRotation;
    public bool IsTriggered { get; set; } = false;
    public bool IsCancelled { get; set; } = false;
    public float StartTime { get; set; } = 0.0f;
}

public class EntryDeathContext
{
    public int VictimSlot { get; set; }
    public int KillerSlot { get; set; }
    public uint KillerEntityIndex { get; set; }
    public int DeathTick { get; set; }
    public float DeathTime { get; set; }
    public float TradeDeadlineTime { get; set; }
    public List<int> NearbyAllies { get; set; } = new();
    public string Bombsite { get; set; } = "A";
    public RoundTempo Pace { get; set; } = RoundTempo.SLOW_DEFAULT;
    public float TimeRemaining { get; set; } = 90.0f;
    public bool TradeConfirmed { get; set; } = false;
}

public enum AdaptationDisposition
{
    Active,
    Expired,
    ObjectiveCompleted,
    Replaced,
    Cancelled,
    RoundEnded
}

public class ActiveAdaptationRecord
{
    public string AdaptationId { get; set; } = string.Empty;
    public TacticalAdaptationReason Reason { get; set; }
    public int StartTick { get; set; }
    public int EndTick { get; set; }
    public float StartServerTime { get; set; }
    public float Duration { get; set; }
    public int PreviousRevision { get; set; }
    public int FinalRevision { get; set; }
    public List<int> AffectedSlots { get; set; } = new();
    public string NewOrdersDescription { get; set; } = string.Empty;
    public AdaptationDisposition Disposition { get; set; } = AdaptationDisposition.Active;
    public bool IsClosed { get; set; } = false;
    public CsTeam OwnerTeam { get; set; } = CsTeam.None;
    public string TargetSite { get; set; } = string.Empty;
}

public class PhysicalStopState
{
    public int ConsecutiveUnknownStandstillCycles { get; set; } = 0;
    public float DistanceToMacroGoalAtFirstUnknown { get; set; } = 0f;
}

public class MapPlantZone
{
    [JsonPropertyName("center")]
    public MapVector3 Center { get; set; } = new();

    [JsonPropertyName("bounds_min")]
    public MapVector3 BoundsMin { get; set; } = new();

    [JsonPropertyName("bounds_max")]
    public MapVector3 BoundsMax { get; set; } = new();

    [JsonPropertyName("radius_2d")]
    public float Radius2D { get; set; } = 380.0f;

    public bool Contains(float x, float y, float z)
    {
        bool inX = x >= BoundsMin.X && x <= BoundsMax.X;
        bool inY = y >= BoundsMin.Y && y <= BoundsMax.Y;
        bool inZ = (BoundsMin.Z == 0f && BoundsMax.Z == 0f) || (z >= BoundsMin.Z && z <= BoundsMax.Z);
        return inX && inY && inZ;
    }

    public float Distance2DSquared(float x, float y)
    {
        float dx = x - Center.X;
        float dy = y - Center.Y;
        return dx * dx + dy * dy;
    }
}

public class MapVector3
{
    [JsonPropertyName("x")]
    public float X { get; set; }

    [JsonPropertyName("y")]
    public float Y { get; set; }

    [JsonPropertyName("z")]
    public float Z { get; set; }
}

public sealed class BombObjectiveState
{
    public int InternalRoundId { get; set; }
    public string SourceDecisionId { get; set; } = string.Empty;
    public string SourceTacticId { get; set; } = string.Empty;
    public BombsiteTarget MaterializedRealSite { get; set; } = BombsiteTarget.None;
    public BombsiteTarget FakeSite { get; set; } = BombsiteTarget.None;
    public BombsiteTarget CommittedSite { get; set; } = BombsiteTarget.None;
    public BombsiteTarget RealSite { get; set; } = BombsiteTarget.None;
    public BombsiteTarget PlantedSite { get; set; } = BombsiteTarget.None;
    public Guid ObjectiveRevision { get; set; } = Guid.NewGuid();
    public long UpdatedAtTick { get; set; }
    public string UpdateReason { get; set; } = string.Empty;
    public bool HasLoggedObjectiveCommitted { get; set; } = false;

    public void CommitMaterializedSite(
        string decisionId,
        string tacticId,
        BombsiteTarget fakeSite,
        BombsiteTarget materializedRealSite,
        long currentTick,
        string reason = "TacticMaterialization")
    {
        SourceDecisionId = decisionId;
        SourceTacticId = tacticId;
        FakeSite = fakeSite;
        MaterializedRealSite = materializedRealSite;
        CommittedSite = materializedRealSite;
        RealSite = materializedRealSite;
        ObjectiveRevision = Guid.NewGuid();
        UpdatedAtTick = currentTick;
        UpdateReason = reason;
        HasLoggedObjectiveCommitted = false;
    }

    public void UpdateCommittedSite(BombsiteTarget newSite, string reason, long currentTick)
    {
        if (CommittedSite != newSite)
        {
            CommittedSite = newSite;
            RealSite = newSite;
            ObjectiveRevision = Guid.NewGuid();
            UpdatedAtTick = currentTick;
            UpdateReason = reason;
        }
    }

    public void MarkPlanted(BombsiteTarget plantedSite, long currentTick, string reason)
    {
        PlantedSite = plantedSite;
        ObjectiveRevision = Guid.NewGuid();
        UpdatedAtTick = currentTick;
        UpdateReason = reason;
    }
}


public class MapChokepoint
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("sector")]
    public string Sector { get; set; } = string.Empty;

    [JsonPropertyName("associated_bomb")]
    public string AssociatedBomb { get; set; } = "A"; // "A", "B", "Mid"

    [JsonPropertyName("x")]
    public float X { get; set; }

    [JsonPropertyName("y")]
    public float Y { get; set; }

    [JsonPropertyName("z")]
    public float Z { get; set; }

    [JsonPropertyName("radius")]
    public float Radius { get; set; } = 350.0f;

    [JsonPropertyName("synonyms")]
    public List<string> Synonyms { get; set; } = new();
}

public class ChokepointBlockState
{
    public string ChokepointId { get; set; } = string.Empty;
    public string BlockType { get; set; } = "Smoke"; // "Smoke", "Molotov"
    public float BlockedUntilTime { get; set; }
    public int PlacedByBotSlot { get; set; } = -1;

    public bool IsActive(float currentTime) => currentTime < BlockedUntilTime;
    public bool IsExpiringSoon(float currentTime) => currentTime >= (BlockedUntilTime - 2.5f) && currentTime < BlockedUntilTime;
}

public class TacticalPlayDecision
{
    public PlayTier Tier { get; set; } = PlayTier.Tier1_Standard;
    public string PlayId { get; set; } = "STANDARD_HOLD";
    public string PlayName { get; set; } = "Jogo Padrão Posicional";
    public string Description { get; set; } = "Controle posicional padrão e contenção.";
    public RoundTempo Tempo { get; set; } = RoundTempo.SLOW_DEFAULT;
    public RoundTempo SuggestedTempo { get; set; } = RoundTempo.SLOW_DEFAULT;
    public float StagingDuration { get; set; } = 18.0f;
    public bool IsCheesePlay => Tier == PlayTier.Tier3_Cheese;
    public CtDuoPlayType CtDuo { get; set; } = CtDuoPlayType.None;
    public TrTacticType TrTactic { get; set; } = TrTacticType.Default;
}

public class MapProfile
{
    [JsonPropertyName("map_name")]
    public string MapName { get; set; } = string.Empty;

    [JsonPropertyName("friendly_name")]
    public string FriendlyName { get; set; } = string.Empty;

    [JsonPropertyName("spots")]
    public List<TacticalSpot> Spots { get; set; } = new();

    [JsonPropertyName("chokepoints")]
    public List<MapChokepoint> Chokepoints { get; set; } = new();

    [JsonPropertyName("voice_synonyms")]
    public Dictionary<string, string> VoiceSynonyms { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    [JsonPropertyName("plant_zones")]
    public Dictionary<string, MapPlantZone> PlantZones { get; set; } = new(StringComparer.OrdinalIgnoreCase);
}
