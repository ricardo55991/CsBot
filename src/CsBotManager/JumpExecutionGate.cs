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
    public bool JumpPressedLastTick { get; set; } = false;
    public int ConsecutiveJumpPredictions { get; set; } = 0;
    public string LastJumpReason { get; set; } = "None";
    public Vector? LastJumpPosition { get; set; } = null;
    public int ConsecutiveAirborneTicks { get; set; } = 0;
    public bool IsGrounded { get; set; } = true;
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

    public JumpGateState GetOrCreateState(int slot)
    {
        return _states.GetOrAdd(slot, _ => new JumpGateState());
    }

    public void UpdateGroundedState(int slot, bool isGrounded, int currentTick)
    {
        var state = GetOrCreateState(slot);
        state.IsGrounded = isGrounded;
        if (isGrounded)
        {
            state.LastGroundedTick = currentTick;
            state.ConsecutiveAirborneTicks = 0;
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
        float currentSpeed2D = 250f)
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

        // 1. Bypass para Recovery de Stuck ou Obstáculo Físico Mapeado
        if (context == JumpContextType.StuckRecovery || context == JumpContextType.RecoveryUnstuck || source.Contains("Recovery", StringComparison.OrdinalIgnoreCase))
        {
            state.LastJumpReason = "Recovery";
            state.LastJumpIssuedTick = currentTick;
            state.JumpPressedLastTick = true;
            state.LastJumpPosition = botPosition;

            MetricsAggregator?.RecordJump(slot, executed: true, suppressedAirborne: false, suppressedCooldown: false, suppressedContext: false, "Recovery");
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: true, "Authorized_RecoveryBypass");
            return (true, "Authorized_RecoveryBypass", actionId0);
        }

        if (context == JumpContextType.ObstacleTraversal || source.Contains("OBSTACLE", StringComparison.OrdinalIgnoreCase))
        {
            if (state.IsGrounded)
            {
                state.LastJumpReason = "ObstacleTraversal";
                state.LastJumpIssuedTick = currentTick;
                state.JumpPressedLastTick = true;
                state.LastJumpPosition = botPosition;

                MetricsAggregator?.RecordJump(slot, executed: true, suppressedAirborne: false, suppressedCooldown: false, suppressedContext: false, "ObstacleTraversal");
                LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: true, "Authorized_ObstacleBypass");
                return (true, "Authorized_ObstacleBypass", actionId0);
            }
        }

        // Se actionId0 não tiver Jump e não for bypass, não há salto a avaliar
        if (!onnxHasJump0)
        {
            return (false, "NoJumpRequested", actionId0);
        }

        // 3. Não renovar enquanto airborne (IsGrounded == false ou context == Airborne)
        if (!state.IsGrounded || context == JumpContextType.Airborne)
        {
            state.JumpPressedLastTick = false;
            MetricsAggregator?.RecordJump(slot, executed: false, suppressedAirborne: true, suppressedCooldown: false, suppressedContext: false, "Airborne");
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: false, "Suppressed_AlreadyAirborne");
            return (false, "Suppressed_AlreadyAirborne", terrestrialAction);
        }

        // 4. Cooldown contextual (3.5s = ~224 ticks a 64Hz)
        int cooldownTicks = (int)(JumpCooldownSeconds * 64);
        if (currentTick - state.LastJumpIssuedTick < cooldownTicks)
        {
            state.JumpPressedLastTick = false;
            MetricsAggregator?.RecordJump(slot, executed: false, suppressedAirborne: false, suppressedCooldown: true, suppressedContext: false, "CooldownActive");
            LogJumpRequested(slot, source, horizonVotes, state.IsGrounded, context, allowed: false, "Suppressed_CooldownActive");
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
