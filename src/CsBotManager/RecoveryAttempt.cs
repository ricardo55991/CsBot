using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class RecoveryAttempt
{
    public Guid RecoveryId { get; init; } = Guid.NewGuid();
    public long InternalRoundId { get; init; }
    public int BotSlot { get; init; }
    public int Stage { get; set; } = 1;
    public long TriggerTick { get; init; }
    public float TriggerTime { get; init; }
    public Vector OriginalPosition { get; init; } = new(0, 0, 0);
    public Vector OriginalGoal { get; init; } = new(0, 0, 0);
    public string OriginalWaypointId { get; init; } = string.Empty;
    public string TriggerReason { get; init; } = string.Empty;
    public string BlacklistedWaypointId { get; set; } = string.Empty;
    public string AlternativeWaypointId { get; set; } = string.Empty;
    public MovementIntent? WinningIntent { get; set; }
    public float Displacement500Ms { get; set; }
    public float Displacement1000Ms { get; set; }
    public float Displacement2DBefore { get; set; }
    public float Displacement2DAfter { get; set; }
    public string OverwrittenBy { get; set; } = "NONE";
    public float DistanceToMacroGoalBefore { get; set; }
    public float DistanceToMacroGoalAfter { get; set; }
    public float MacroGoalProgress { get; set; }
    public long StageAppliedTick { get; set; }
    public float StageAppliedTime { get; set; }
    public float EndTime { get; set; }
    public float DurationMs => EndTime > TriggerTime ? (EndTime - TriggerTime) * 1000f : 0f;
    public bool Recovered { get; set; }
    public string FailureReason { get; set; } = string.Empty;
}
