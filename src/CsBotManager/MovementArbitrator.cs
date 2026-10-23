using System.Collections.Concurrent;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using BotControllerApi;

namespace CsBotManager;

/// <summary>
/// Hierarquia de prioridades explícita da Arbitragem Centralizada de Movimento (Bug 3).
/// Menor valor numérico = maior precedência.
/// </summary>
public enum MovementIntentSource
{
    RoundLifecycle = 1,
    BombObjective = 2,
    Unstuck = 3,
    CounterStrafe = 4,
    EmergencyFallback = 5,
    TradeSpacing = 6,
    MicroMove = 7,
    TacticalNavigation = 8
}

public enum MovementCommandKind
{
    NavigateNavMesh,
    HoldStop,
    UsercmdVector,
    ReleaseHoldAndRepath
}

public sealed class MovementIntent
{
    public int BotSlot { get; init; }
    public string BotName { get; init; } = string.Empty;
    public int GameTick { get; init; }
    public float CurrentTime { get; init; }
    public MovementIntentSource Source { get; init; }
    public MovementCommandKind Kind { get; init; }
    public string Reason { get; init; } = string.Empty;
    public float ExpiresAtTime { get; init; }

    // Parâmetros de NavMesh / Objetivo
    public float? GoalX { get; init; }
    public float? GoalY { get; init; }
    public float? GoalZ { get; init; }
    public bool ForceRepath { get; init; }
    public bool Hurry { get; init; }
    public bool Sneak { get; init; }

    // Parâmetros de Parada / Hold
    public bool IsStopping { get; init; }
    public float WaitDurationSeconds { get; init; }

    // Parâmetros de Usercmd / BotControllerApi
    public bool UseUsercmdVelocity { get; init; }
    public float ForwardMove { get; init; }
    public float SideMove { get; init; }
    public ulong Buttons { get; init; }
    public int ButtonsDurationMs { get; init; } = 120;

    // Parâmetros de LookAt (opcional)
    public float? LookX { get; init; }
    public float? LookY { get; init; }
    public float? LookZ { get; init; }
    public float LookDuration { get; init; } = 0.5f;
    public float LookTolerance { get; init; } = 5.0f;
    public bool ClearLookIfClose { get; init; }
}

public sealed class ArbitratedMovementDecision
{
    public int BotSlot { get; init; }
    public int GameTick { get; init; }
    public MovementIntent WinningIntent { get; init; } = null!;
    public List<MovementIntent> SuppressedIntents { get; init; } = new();
    public bool HysteresisPreservedPreviousWinner { get; init; }
    public bool AppliedToEngine { get; set; }
}

/// <summary>
/// Autoridade única de decisão e aplicação de movimento por bot e por game_tick (Regras 3 e 4).
/// Nenhuma outra classe pode escrever diretamente em CCSBot.IsStopping, CCSBot.GoalPosition,
/// CCSBot.WaitTimer, InjectUsercmd de movimento ou StartUsercmdMovement fora de ApplyWinningIntent.
/// </summary>
public sealed class MovementArbitrator
{
    public BotSystemConfig Config { get; set; } = BotSystemConfig.Default;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }

    private readonly ConcurrentDictionary<int, List<MovementIntent>> _pendingIntentsBySlot = new();
    private readonly ConcurrentDictionary<int, ArbitratedMovementDecision> _lastDecisionsBySlot = new();
    private readonly ConcurrentDictionary<int, long> _activeUsercmdHandleBySlot = new();
    private readonly ConcurrentDictionary<int, int> _lastAppliedTickBySlot = new();
    private readonly ConcurrentDictionary<int, float> _lastConflictLogTimeBySlot = new();

    private long _totalResolvedIntents = 0;
    private long _totalConflictsSuppressed = 0;
    private long _totalApplications = 0;

    public long TotalResolvedIntents => Interlocked.Read(ref _totalResolvedIntents);
    public long TotalConflictsSuppressed => Interlocked.Read(ref _totalConflictsSuppressed);
    public long TotalApplications => Interlocked.Read(ref _totalApplications);

    public void ResetRound(IBotControllerApi? api)
    {
        if (api != null)
        {
            foreach (var kvp in _activeUsercmdHandleBySlot)
            {
                if (kvp.Value != 0)
                {
                    try { api.CancelUsercmdMovement(kvp.Key, kvp.Value); } catch { }
                }
            }
        }

        _activeUsercmdHandleBySlot.Clear();
        _pendingIntentsBySlot.Clear();
        _lastDecisionsBySlot.Clear();
        _lastAppliedTickBySlot.Clear();
        _lastConflictLogTimeBySlot.Clear();
    }

    public void ClearBotState(int slot, IBotControllerApi? api)
    {
        _pendingIntentsBySlot.TryRemove(slot, out _);
        _lastDecisionsBySlot.TryRemove(slot, out _);
        _lastAppliedTickBySlot.TryRemove(slot, out _);
        if (_activeUsercmdHandleBySlot.TryRemove(slot, out long handle) && handle != 0 && api != null)
        {
            try { api.CancelUsercmdMovement(slot, handle); } catch { }
        }
    }

    public void PublishIntent(MovementIntent intent)
    {
        if (intent == null) return;
        var list = _pendingIntentsBySlot.GetOrAdd(intent.BotSlot, _ => new List<MovementIntent>(4));
        lock (list)
        {
            list.Add(intent);
        }
    }

    /// <summary>
    /// Etapa 1 (Pura/Determinística): Coleta todas as intenções publicadas para o bot no tick atual,
    /// aplica hierarquia de prioridades e histerese anti-flip-flop e devolve a decisão vencedora.
    /// </summary>
    public ArbitratedMovementDecision? CollectAndResolveIntents(int botSlot, int gameTick, float currentTime)
    {
        List<MovementIntent>? candidates = null;
        if (_pendingIntentsBySlot.TryRemove(botSlot, out var rawList))
        {
            lock (rawList)
            {
                candidates = rawList.Where(i => i.ExpiresAtTime <= 0f || currentTime <= i.ExpiresAtTime).ToList();
            }
        }

        if (candidates == null || candidates.Count == 0)
        {
            // Se houver decisão anterior ainda dentro da janela de expiração e com histerese ativa, preserva
            if (_lastDecisionsBySlot.TryGetValue(botSlot, out var prevDec) &&
                prevDec.WinningIntent.ExpiresAtTime > currentTime &&
                (gameTick - prevDec.GameTick) <= Config.ArbitrationHysteresisTicks &&
                prevDec.WinningIntent.Source <= MovementIntentSource.TradeSpacing)
            {
                return new ArbitratedMovementDecision
                {
                    BotSlot = botSlot,
                    GameTick = gameTick,
                    WinningIntent = prevDec.WinningIntent,
                    SuppressedIntents = new List<MovementIntent>(),
                    HysteresisPreservedPreviousWinner = true
                };
            }
            return null;
        }

        // Ordena deterministicamente: menor Source (maior prioridade) -> comando mais recente -> não-StandStill
        var ordered = candidates
            .OrderBy(c => (int)c.Source)
            .ThenByDescending(c => c.GameTick)
            .ThenBy(c => c.IsStopping ? 1 : 0)
            .ToList();

        var winner = ordered[0];
        bool hysteresisUsed = false;

        // Histerese anti-flip-flop: se havia um vencedor recente de prioridade próxima e ainda válido,
        // evita alternar entre MicroMove e TacticalNavigation a cada 1 tick se o vencedor atual for de baixa prioridade.
        if (_lastDecisionsBySlot.TryGetValue(botSlot, out var lastDec) &&
            lastDec.WinningIntent.ExpiresAtTime > currentTime &&
            (gameTick - lastDec.GameTick) < Config.ArbitrationHysteresisTicks)
        {
            var prevWinner = lastDec.WinningIntent;
            if ((int)prevWinner.Source < (int)winner.Source)
            {
                winner = prevWinner;
                hysteresisUsed = true;
            }
        }

        var suppressed = ordered.Where(c => !ReferenceEquals(c, winner)).ToList();
        Interlocked.Increment(ref _totalResolvedIntents);
        if (suppressed.Count > 0)
        {
            Interlocked.Add(ref _totalConflictsSuppressed, suppressed.Count);
        }

        var decision = new ArbitratedMovementDecision
        {
            BotSlot = botSlot,
            GameTick = gameTick,
            WinningIntent = winner,
            SuppressedIntents = suppressed,
            HysteresisPreservedPreviousWinner = hysteresisUsed
        };

        _lastDecisionsBySlot[botSlot] = decision;
        return decision;
    }

    /// <summary>
    /// Etapa 2 (Única Autoridade de Escrita no Bot): Aplica a intenção vencedora exatamente 1 vez por bot e por tick.
    /// </summary>
    public bool ApplyWinningIntent(
        ArbitratedMovementDecision decision,
        CCSPlayerController? controller,
        IBotControllerApi? api)
    {
        if (decision == null) return false;

        int slot = decision.BotSlot;
        int tick = decision.GameTick;

        // Garante aplicação exatamente 1 vez por bot e por tick (Regra 4)
        if (_lastAppliedTickBySlot.TryGetValue(slot, out int prevTick) && prevTick == tick)
        {
            return false;
        }
        _lastAppliedTickBySlot[slot] = tick;
        decision.AppliedToEngine = true;
        Interlocked.Increment(ref _totalApplications);

        var intent = decision.WinningIntent;

        // Log de auditoria quando há conflito real suprimido (ex.: MicroMove vs Unstuck ou Hold vs Objective)
        if (decision.SuppressedIntents.Count > 0 && TelemetryLogger != null && TelemetryLogger.IsEnabled)
        {
            bool hasDistinctSourceConflict = decision.SuppressedIntents.Any(s => s.Source != intent.Source);
            if (hasDistinctSourceConflict)
            {
                float now = intent.CurrentTime;
                if (!_lastConflictLogTimeBySlot.TryGetValue(slot, out float lastLog) || (now - lastLog) >= 2.5f)
                {
                    _lastConflictLogTimeBySlot[slot] = now;
                    string suppressedSummary = string.Join(", ", decision.SuppressedIntents.Select(s => $"{s.Source}:{s.Kind}({s.Reason})"));
                    TelemetryLogger.LogEvent(
                        "ARBITRAGEM - MOVIMENTO",
                        $"**{intent.BotName}** (`slot={slot}`, `tick={tick}`): Vencedor=`{intent.Source}:{intent.Kind}` (`{intent.Reason}`) | Suprimidos=[`{suppressedSummary}`] | Histerese=`{decision.HysteresisPreservedPreviousWinner}`");
                }
            }
        }

        if (controller == null || !controller.IsValid || !controller.PawnIsAlive)
        {
            return true;
        }

        var pawn = controller.PlayerPawn.Value;
        var bot = pawn?.Bot;
        if (pawn == null || bot == null) return true;

        // 1. Gerencia UsercmdMovement ativo via BotControllerApi
        if (intent.UseUsercmdVelocity && api != null)
        {
            if (_activeUsercmdHandleBySlot.TryGetValue(slot, out long oldHandle) && oldHandle != 0)
            {
                try { api.CancelUsercmdMovement(slot, oldHandle); } catch { }
            }

            // Clamp de velocidade 2D máxima (Bug 10: impede somar vetores artificiais > 250 u/s)
            float fMove = intent.ForwardMove;
            float sMove = intent.SideMove;
            float mag = MathF.Sqrt(fMove * fMove + sMove * sMove);
            if (mag > Config.MaxArtificialSpeed2D && mag > 0.001f)
            {
                float scale = Config.MaxArtificialSpeed2D / mag;
                fMove *= scale;
                sMove *= scale;
            }

            try
            {
                long newHandle = api.StartUsercmdMovement(slot, fMove, sMove);
                _activeUsercmdHandleBySlot[slot] = newHandle;
            }
            catch { }
        }
        else
        {
            if (_activeUsercmdHandleBySlot.TryRemove(slot, out long oldHandle) && oldHandle != 0 && api != null)
            {
                try { api.CancelUsercmdMovement(slot, oldHandle); } catch { }
            }
        }

        // 2. Aplica botões (IN_JUMP, IN_DUCK, IN_SPEED, IN_USE) se solicitados
        if (intent.Buttons != 0UL && api != null)
        {
            try
            {
                api.InjectUsercmd(slot, intent.Buttons, Math.Clamp(intent.ButtonsDurationMs, 50, 1000));
            }
            catch { }
        }

        // 3. Aplica parada ou liberação no CCSBot
        if (intent.Kind == MovementCommandKind.HoldStop || intent.IsStopping)
        {
            bot.IsStopping = true;
            float waitDur = Math.Max(0.10f, intent.WaitDurationSeconds);
            bot.WaitTimer.Duration = waitDur;
            bot.WaitTimer.Timestamp = intent.CurrentTime + waitDur;
        }
        else
        {
            bot.IsStopping = false;
            bot.WaitTimer.Duration = 0f;
            bot.WaitTimer.Timestamp = 0f;
        }

        // 4. Aplica GoalPosition e Repath no NavMesh
        if (intent.GoalX.HasValue && intent.GoalY.HasValue && intent.GoalZ.HasValue)
        {
            bot.GoalPosition[0] = intent.GoalX.Value;
            bot.GoalPosition[1] = intent.GoalY.Value;
            bot.GoalPosition[2] = intent.GoalZ.Value;
        }

        if (intent.ForceRepath || intent.Kind == MovementCommandKind.ReleaseHoldAndRepath)
        {
            bot.RepathTimer.Timestamp = 0f;
        }

        if (intent.Hurry)
        {
            bot.HurryTimer.Duration = 2.5f;
            bot.HurryTimer.Timestamp = intent.CurrentTime + 2.5f;
            bot.MustRunTimer.Duration = 2.5f;
            bot.MustRunTimer.Timestamp = intent.CurrentTime + 2.5f;
            bot.SneakTimer.Timestamp = 0f;
        }
        else if (intent.Sneak)
        {
            bot.SneakTimer.Duration = 1.5f;
            bot.SneakTimer.Timestamp = intent.CurrentTime + 1.5f;
        }

        // 5. Aplica LookAtSpot se presente
        if (intent.LookX.HasValue && intent.LookY.HasValue && intent.LookZ.HasValue)
        {
            bot.LookAtSpot[0] = intent.LookX.Value;
            bot.LookAtSpot[1] = intent.LookY.Value;
            bot.LookAtSpot[2] = intent.LookZ.Value;
            bot.LookAtSpotDuration = intent.LookDuration;
            bot.LookAtSpotTimestamp = intent.CurrentTime;
            bot.LookAtSpotAngleTolerance = intent.LookTolerance;
            bot.LookAtSpotClearIfClose = intent.ClearLookIfClose;
        }
        else if (intent.ClearLookIfClose)
        {
            bot.LookAtSpotClearIfClose = true;
            bot.LookAtSpotDuration = 0f;
            bot.LookAtSpotTimestamp = 0f;
        }

        return true;
    }

    public ArbitratedMovementDecision? GetLastDecision(int botSlot)
    {
        return _lastDecisionsBySlot.TryGetValue(botSlot, out var d) ? d : null;
    }
}
