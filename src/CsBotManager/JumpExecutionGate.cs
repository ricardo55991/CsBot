using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class JumpGateState
{
    public int LastJumpIssuedTick { get; set; } = -9999;
    public int LastGroundedTick { get; set; } = 0;
    public int LastLandingTick { get; set; } = -9999;
    public bool JumpPressedLastTick { get; set; } = false;
    public int ConsecutiveJumpPredictions { get; set; } = 0;
    public string LastJumpReason { get; set; } = "None";
    public Vector? LastJumpPosition { get; set; } = null;
    public int ConsecutiveAirborneTicks { get; set; } = 0;
    public bool IsGrounded { get; set; } = true;
    public bool RepeatedJumpSequenceDetected { get; set; } = false;
}

public enum JumpGateEventType
{
    JUMP_REQUESTED,
    JUMP_EXECUTED,
    JUMP_SUPPRESSED_AIRBORNE,
    JUMP_SUPPRESSED_COOLDOWN,
    JUMP_SUPPRESSED_CONTEXT,
    JUMP_SUPPRESSED_NO_JUMP_ZONE,
    JUMP_LANDED,
    REPEATED_JUMP_SEQUENCE_DETECTED
}

public sealed class JumpGateEvent
{
    public JumpGateEventType EventType { get; set; }
    public string InternalRoundId { get; set; } = string.Empty;
    public int OfficialRoundNumber { get; set; }
    public int Tick { get; set; }
    public int Slot { get; set; }
    public string Team { get; set; } = "None";
    public string Role { get; set; } = "None";
    public string Source { get; set; } = "None";
    public string JumpReason { get; set; } = "None";
    public bool Grounded { get; set; }
    public bool Airborne { get; set; }
    public bool Falling { get; set; }
    public int LastJumpTick { get; set; }
    public int LastLandingTick { get; set; }
    public float CooldownRemaining { get; set; }
    public bool Allowed { get; set; }
    public string SuppressionReason { get; set; } = "None";
    public Vector? Position { get; set; }
    public float Velocity2D { get; set; }
    public float VelocityZ { get; set; }
    public string TacticId { get; set; } = "None";
    public string PlanStage { get; set; } = "None";
}

public enum JumpContextType
{
    NormalNavigation,
    RampOrStairTraversal,
    AuthorizedHold,
    CounterStrafe,
    AwpAngleCover,
    PlantOrDefuse,
    UtilityWait,
    SaveHold,
    Airborne,
    StuckRecovery,
    RecoveryUnstuck = StuckRecovery,
    ObstacleTraversal,
    JumpPeekCorner,
    VerticalTraversal,
    TacticalJump
}

public sealed class JumpExecutionGate
{
    private readonly ConcurrentDictionary<int, JumpGateState> _states = new();

    public float JumpCooldownSeconds { get; set; } = 3.5f;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }
    public TrackerMetricsAggregator? MetricsAggregator { get; set; }

    public List<JumpGateEvent> EmittedEvents { get; } = new();
    public string CurrentInternalRoundId { get; set; } = Guid.NewGuid().ToString();
    public int CurrentOfficialRoundNumber { get; set; } = 1;
    public string CurrentTacticId { get; set; } = "None";
    public string CurrentPlanStage { get; set; } = "Setup";

    public JumpGateState GetOrCreateState(int slot)
    {
        return _states.GetOrAdd(slot, _ => new JumpGateState());
    }

    public JumpGateEvent RecordEvent(
        JumpGateEventType eventType,
        int tick,
        int slot,
        string team,
        string role,
        string source,
        string jumpReason,
        bool grounded,
        bool airborne,
        bool falling,
        int lastJumpTick,
        int lastLandingTick,
        float cooldownRemaining,
        bool allowed,
        string suppressionReason,
        Vector? position,
        float velocity2D,
        float velocityZ)
    {
        var evt = new JumpGateEvent
        {
            EventType = eventType,
            InternalRoundId = CurrentInternalRoundId,
            OfficialRoundNumber = CurrentOfficialRoundNumber,
            Tick = tick,
            Slot = slot,
            Team = team,
            Role = role,
            Source = source,
            JumpReason = jumpReason,
            Grounded = grounded,
            Airborne = airborne,
            Falling = falling,
            LastJumpTick = lastJumpTick,
            LastLandingTick = lastLandingTick,
            CooldownRemaining = cooldownRemaining,
            Allowed = allowed,
            SuppressionReason = suppressionReason,
            Position = position,
            Velocity2D = velocity2D,
            VelocityZ = velocityZ,
            TacticId = CurrentTacticId,
            PlanStage = CurrentPlanStage
        };
        EmittedEvents.Add(evt);
        return evt;
    }

    public void UpdateGroundedState(int slot, bool isGrounded, int currentTick, float vz = 0f, Vector? position = null)
    {
        var state = GetOrCreateState(slot);
        bool wasAirborne = !state.IsGrounded;
        state.IsGrounded = isGrounded;

        if (isGrounded)
        {
            state.LastGroundedTick = currentTick;
            state.ConsecutiveAirborneTicks = 0;
            if (wasAirborne)
            {
                state.LastLandingTick = currentTick;
                RecordEvent(
                    JumpGateEventType.JUMP_LANDED,
                    currentTick,
                    slot,
                    "Unknown",
                    "Unknown",
                    "PhysicsEngine",
                    state.LastJumpReason,
                    grounded: true,
                    airborne: false,
                    falling: false,
                    state.LastJumpIssuedTick,
                    currentTick,
                    cooldownRemaining: 0f,
                    allowed: true,
                    suppressionReason: "None",
                    position,
                    velocity2D: 0f,
                    velocityZ: vz);
            }
        }
        else
        {
            state.ConsecutiveAirborneTicks++;
        }
    }

    public bool IsGrounded(int slot)
    {
        return GetOrCreateState(slot).IsGrounded;
    }

    /// <summary>
    /// Avalia a requisição de salto.
    /// Se for permitida, retorna Allowed=true.
    /// Se for suprimida, converte actionId do ONNX (49..96 -> 1..48) preservando o movimento horizontal.
    /// </summary>
    public (bool Allowed, string Reason, int ConvertedActionId) EvaluateJumpRequest(
        int slot,
        string botName,
        int currentTick,
        float currentTime,
        string source,
        int actionId0,
        int actionId1,
        int actionId2,
        JumpContextType context,
        Vector? botPosition,
        float currentSpeed2D = 250f,
        float vz = 0f,
        string team = "CounterTerrorist",
        string role = "Rifle")
    {
        var state = GetOrCreateState(slot);

        // Se a ação tiver Jump (49..96), prepara o equivalente terrestre caso o jump seja suprimido
        if (actionId0 >= 49 && actionId0 <= 96)
        {
            state.ConsecutiveJumpPredictions++;
        }
        else
        {
            state.ConsecutiveJumpPredictions = 0;
        }

        bool onnxHasJump0 = (actionId0 >= 49 && actionId0 <= 96);
        bool onnxHasJump1 = (actionId1 >= 49 && actionId1 <= 96);
        bool onnxHasJump2 = (actionId2 >= 49 && actionId2 <= 96);
        int horizonVotes = (onnxHasJump0 ? 1 : 0) + (onnxHasJump1 ? 1 : 0) + (onnxHasJump2 ? 1 : 0);

        int terrestrialAction = (actionId0 >= 49 && actionId0 <= 96) ? (actionId0 - 48) : actionId0;
        int cooldownTicks = (int)(JumpCooldownSeconds * 64);
        int elapsedSinceJump = currentTick - state.LastJumpIssuedTick;
        float cooldownRem = MathF.Max(0f, JumpCooldownSeconds - (elapsedSinceJump / 64f));

        // 1. Bypass para Recovery de Stuck ou Obstáculo Físico Mapeado
        if (context == JumpContextType.StuckRecovery || context == JumpContextType.RecoveryUnstuck || source.Contains("Recovery", StringComparison.OrdinalIgnoreCase))
        {
            RecordEvent(JumpGateEventType.JUMP_REQUESTED, currentTick, slot, team, role, source, "Recovery", state.IsGrounded, !state.IsGrounded, vz < 0f, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, true, "None", botPosition, currentSpeed2D, vz);

            state.LastJumpReason = "Recovery";
            state.LastJumpIssuedTick = currentTick;
            state.JumpPressedLastTick = true;
            state.LastJumpPosition = botPosition;

            MetricsAggregator?.RecordJump(slot, executed: true, suppressedAirborne: false, suppressedCooldown: false, suppressedContext: false, "Recovery");
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: true, "Authorized_RecoveryBypass");

            RecordEvent(JumpGateEventType.JUMP_EXECUTED, currentTick, slot, team, role, source, "Recovery", state.IsGrounded, !state.IsGrounded, vz < 0f, currentTick, state.LastLandingTick, 0f, true, "None", botPosition, currentSpeed2D, vz);
            return (true, "Authorized_RecoveryBypass", actionId0);
        }

        if (context == JumpContextType.ObstacleTraversal || source.Contains("OBSTACLE", StringComparison.OrdinalIgnoreCase))
        {
            if (state.IsGrounded)
            {
                RecordEvent(JumpGateEventType.JUMP_REQUESTED, currentTick, slot, team, role, source, "ObstacleTraversal", state.IsGrounded, false, false, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, true, "None", botPosition, currentSpeed2D, vz);

                state.LastJumpReason = "ObstacleTraversal";
                state.LastJumpIssuedTick = currentTick;
                state.JumpPressedLastTick = true;
                state.LastJumpPosition = botPosition;

                MetricsAggregator?.RecordJump(slot, executed: true, suppressedAirborne: false, suppressedCooldown: false, suppressedContext: false, "ObstacleTraversal");
                LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: true, "Authorized_ObstacleBypass");

                RecordEvent(JumpGateEventType.JUMP_EXECUTED, currentTick, slot, team, role, source, "ObstacleTraversal", state.IsGrounded, false, false, currentTick, state.LastLandingTick, 0f, true, "None", botPosition, currentSpeed2D, vz);
                return (true, "Authorized_ObstacleBypass", actionId0);
            }
        }

        // Se actionId0 não tiver Jump e não for bypass, não há salto a avaliar
        if (!onnxHasJump0)
        {
            return (false, "NoJumpRequested", actionId0);
        }

        // Registra a solicitação do ONNX
        RecordEvent(JumpGateEventType.JUMP_REQUESTED, currentTick, slot, team, role, source, context.ToString(), state.IsGrounded, !state.IsGrounded, vz < 0f, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, false, "PendingEvaluation", botPosition, currentSpeed2D, vz);

        // 2. Proteção Anti-Bunny Hop (Sequência repetida imediatamente após o pouso)
        bool repeatedLandingSpam = (currentTick - state.LastLandingTick < 5 && state.LastLandingTick > 0);
        bool excessiveJumpSequence = (state.ConsecutiveJumpPredictions > 3);
        if (repeatedLandingSpam || excessiveJumpSequence)
        {
            state.JumpPressedLastTick = false;
            state.RepeatedJumpSequenceDetected = true;
            RecordEvent(JumpGateEventType.REPEATED_JUMP_SEQUENCE_DETECTED, currentTick, slot, team, role, source, context.ToString(), state.IsGrounded, !state.IsGrounded, vz < 0f, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, false, "Suppressed_RepeatedJumpSequenceDetected", botPosition, currentSpeed2D, vz);
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: false, "Suppressed_RepeatedJumpSequenceDetected");
            return (false, "Suppressed_RepeatedJumpSequenceDetected", terrestrialAction);
        }

        // 3. Não renovar enquanto airborne (IsGrounded == false ou context == Airborne)
        if (!state.IsGrounded || context == JumpContextType.Airborne)
        {
            state.JumpPressedLastTick = false;
            MetricsAggregator?.RecordJump(slot, executed: false, suppressedAirborne: true, suppressedCooldown: false, suppressedContext: false, "Airborne");
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: false, "Suppressed_AlreadyAirborne");
            RecordEvent(JumpGateEventType.JUMP_SUPPRESSED_AIRBORNE, currentTick, slot, team, role, source, context.ToString(), state.IsGrounded, true, vz < 0f, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, false, "Suppressed_AlreadyAirborne", botPosition, currentSpeed2D, vz);
            return (false, "Suppressed_AlreadyAirborne", terrestrialAction);
        }

        // 4. Cooldown contextual (3.5s = ~224 ticks a 64Hz)
        if (elapsedSinceJump < cooldownTicks)
        {
            state.JumpPressedLastTick = false;
            MetricsAggregator?.RecordJump(slot, executed: false, suppressedAirborne: false, suppressedCooldown: true, suppressedContext: false, "CooldownActive");
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: false, "Suppressed_CooldownActive");
            RecordEvent(JumpGateEventType.JUMP_SUPPRESSED_COOLDOWN, currentTick, slot, team, role, source, context.ToString(), state.IsGrounded, false, false, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, false, "Suppressed_CooldownActive", botPosition, currentSpeed2D, vz);
            return (false, "Suppressed_CooldownActive", terrestrialAction);
        }

        // 5. Suprimir em contextos proibidos
        if (context == JumpContextType.AuthorizedHold ||
            context == JumpContextType.CounterStrafe ||
            context == JumpContextType.AwpAngleCover ||
            context == JumpContextType.PlantOrDefuse ||
            context == JumpContextType.UtilityWait ||
            context == JumpContextType.SaveHold)
        {
            state.JumpPressedLastTick = false;
            MetricsAggregator?.RecordJump(slot, executed: false, suppressedAirborne: false, suppressedCooldown: false, suppressedContext: true, context.ToString());
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: false, "Suppressed_ProhibitedContext");
            RecordEvent(JumpGateEventType.JUMP_SUPPRESSED_CONTEXT, currentTick, slot, team, role, source, context.ToString(), state.IsGrounded, false, false, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, false, "Suppressed_ProhibitedContext", botPosition, currentSpeed2D, vz);
            return (false, "Suppressed_ProhibitedContext", terrestrialAction);
        }

        // 6. Consenso de horizontes do ONNX: Horizon 0ms + Maioria (>= 2 de 3 votos)
        if (source.Contains("ONNX", StringComparison.OrdinalIgnoreCase))
        {
            if (!onnxHasJump0 || horizonVotes < 2)
            {
                state.JumpPressedLastTick = false;
                MetricsAggregator?.RecordJump(slot, executed: false, suppressedAirborne: false, suppressedCooldown: false, suppressedContext: true, "HorizonConsensusFailed");
                LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: false, "Suppressed_LackOfConsensus");
                RecordEvent(JumpGateEventType.JUMP_SUPPRESSED_CONTEXT, currentTick, slot, team, role, source, context.ToString(), state.IsGrounded, false, false, state.LastJumpIssuedTick, state.LastLandingTick, cooldownRem, false, "Suppressed_LackOfConsensus", botPosition, currentSpeed2D, vz);
                return (false, "Suppressed_LackOfConsensus", terrestrialAction);
            }
        }

        // 7. Autorizado pelo gate
        state.LastJumpReason = context.ToString();
        state.LastJumpIssuedTick = currentTick;
        state.JumpPressedLastTick = true;
        state.LastJumpPosition = botPosition;

        MetricsAggregator?.RecordJump(slot, executed: true, suppressedAirborne: false, suppressedCooldown: false, suppressedContext: false, context.ToString());
        LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: true, "AuthorizedByGate");
        RecordEvent(JumpGateEventType.JUMP_EXECUTED, currentTick, slot, team, role, source, context.ToString(), state.IsGrounded, false, false, currentTick, state.LastLandingTick, 0f, true, "None", botPosition, currentSpeed2D, vz);
        return (true, "AuthorizedByGate", actionId0);
    }

    public void RecordJumpExecuted(int slot, int currentTick, string reason, Vector? position)
    {
        var state = GetOrCreateState(slot);
        state.LastJumpIssuedTick = currentTick;
        state.JumpPressedLastTick = true;
        state.LastJumpReason = reason;
        state.LastJumpPosition = position;
    }

    public void ResetRound()
    {
        _states.Clear();
    }

    public void ResetBot(int slot)
    {
        _states.TryRemove(slot, out _);
    }

    private void LogJumpRequested(
        int slot,
        string source,
        int horizonVotes,
        bool grounded,
        JumpContextType context,
        bool allowed,
        string suppressionReason)
    {
        TelemetryLogger?.LogEvent("JUMP_REQUESTED",
            $"slot={slot} source={source} horizonVotes={horizonVotes}/3 grounded={grounded} context={context} allowed={allowed} suppressionReason={suppressionReason}");
    }
}
