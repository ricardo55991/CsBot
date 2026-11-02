using System.Collections.Concurrent;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
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

public enum ArbitrationWindowPhase
{
    NotStarted,
    Collecting,
    Resolved,
    Applied,
    Closed
}

public enum MovementScope
{
    MacroNavigation,
    LocalMicroMove,
    FullStop,
    Recovery
}

public enum MovementIntentDisposition
{
    PublishedDuringCollection,
    QueuedForNextTick,
    RejectedWrongRound,
    RejectedExpired,
    RejectedAfterResolution,
    RejectedInvalidBot,
    RejectedRoundSealed,
    RejectedQueueFull
}

public enum IntentPublishChannel
{
    ExpectedBetweenTicks,
    UnexpectedAfterResolution
}

public sealed class MovementIntent
{
    public long InternalRoundId { get; set; }
    public int BotSlot { get; init; }
    public string BotName { get; init; } = string.Empty;
    public int GameTick { get; init; }
    public float CurrentTime { get; init; }
    public long CreatedAtTick { get; init; }
    public long EarliestApplicableTick { get; init; }
    public long ExpiresAtTick { get; init; }
    public float ExpiresAtTime { get; init; }
    public Guid IntentId { get; init; } = Guid.NewGuid();
    public Guid TrajectoryId { get; init; } = Guid.Empty;
    public int StepIndex { get; init; } = 0;
    public int CommandGeneration { get; init; } = 0;
    public Guid LogicalActionId { get; init; } = Guid.Empty;
    public MovementIntentDisposition Disposition { get; set; } = MovementIntentDisposition.PublishedDuringCollection;

    public MovementIntentSource Source { get; init; }
    public MovementCommandKind Kind { get; init; }
    public MovementScope Scope { get; init; } = MovementScope.MacroNavigation;
    public string Reason { get; init; } = string.Empty;

    // Parâmetros de NavMesh / Objetivo
    public float? GoalX { get; init; }
    public float? GoalY { get; init; }
    public float? GoalZ { get; init; }
    public SuggestedGoalCoordinateSpace GoalCoordinateSpace { get; init; } = SuggestedGoalCoordinateSpace.WorldAbsolute;
    public bool ForceRepath { get; init; }
    public bool Hurry { get; init; }
    public bool Sneak { get; init; }

    // V4.2.6: Rastreamento autoritativo de objetivo da C4 e Bombsite
    public string TargetSpotId { get; init; } = string.Empty;
    public BombsiteTarget TargetSpotAssociatedBombsite { get; init; } = BombsiteTarget.None;
    public Guid ObjectiveRevision { get; init; } = Guid.Empty;

    // Parâmetros de Parada / Hold
    public bool IsStopping { get; init; }
    public float WaitDurationSeconds { get; init; }
    public bool IsHoldAuthorized { get; init; } = false;
    public bool ExpectedMovement { get; init; } = true;

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
    public Func<BombObjectiveState?>? GetActiveBombObjectiveState { get; set; }

    public const int MaxQueuedIntentsPerSlot = 8;

    private readonly ConcurrentDictionary<int, List<MovementIntent>> _collectingIntentsBySlot = new();
    private readonly ConcurrentDictionary<int, List<MovementIntent>> _queuedIntentsForNextTickBySlot = new();
    private readonly ConcurrentDictionary<int, ArbitratedMovementDecision> _lastDecisionsBySlot = new();
    private readonly ConcurrentDictionary<int, long> _activeUsercmdHandleBySlot = new();
    private readonly ConcurrentDictionary<int, int> _lastAppliedTickBySlot = new();
    private readonly ConcurrentDictionary<int, float> _lastConflictLogTimeBySlot = new();
    private readonly ConcurrentDictionary<int, float> _lastQueueFullWarnTimeBySlot = new();

    private long _totalResolvedIntents = 0;
    private long _totalConflictsSuppressed = 0;
    private long _totalApplications = 0;
    private long _totalDiscardedQueueIntents = 0;

    public long TotalResolvedIntents => Interlocked.Read(ref _totalResolvedIntents);
    public long TotalConflictsSuppressed => Interlocked.Read(ref _totalConflictsSuppressed);
    public long TotalApplications => Interlocked.Read(ref _totalApplications);
    public long TotalDiscardedQueueIntents => Interlocked.Read(ref _totalDiscardedQueueIntents);

    public long GetActiveUsercmdHandle(int slot) => _activeUsercmdHandleBySlot.TryGetValue(slot, out long h) ? h : 0L;

    public ArbitrationWindowPhase CurrentPhase { get; private set; } = ArbitrationWindowPhase.NotStarted;
    public int CurrentGameTick { get; private set; } = 0;
    public float CurrentTickTime { get; private set; } = 0f;
    public long CurrentInternalRoundId { get; private set; } = 0;
    private long _totalIntentsRejectedAfterResolution = 0;
    public long TotalIntentsRejectedAfterResolution => Interlocked.Read(ref _totalIntentsRejectedAfterResolution);

    public int GetQueuedCount(int slot) => _queuedIntentsForNextTickBySlot.TryGetValue(slot, out var l) ? l.Count : 0;
    public int GetCollectingCount(int slot) => _collectingIntentsBySlot.TryGetValue(slot, out var l) ? l.Count : 0;

    public void BeginTick(long gameTick, float currentTime, long internalRoundId)
    {
        CurrentGameTick = (int)gameTick;
        CurrentTickTime = currentTime;
        CurrentInternalRoundId = internalRoundId;
        CurrentPhase = ArbitrationWindowPhase.Collecting;

        _collectingIntentsBySlot.Clear();

        // Importa intenções enfileiradas previamente para o tick atual
        foreach (var kvp in _queuedIntentsForNextTickBySlot)
        {
            int slot = kvp.Key;
            var queuedList = kvp.Value;
            lock (queuedList)
            {
                for (int i = queuedList.Count - 1; i >= 0; i--)
                {
                    var queued = queuedList[i];

                    if (internalRoundId > 0 && queued.InternalRoundId > 0 && queued.InternalRoundId != internalRoundId)
                    {
                        queued.Disposition = MovementIntentDisposition.RejectedWrongRound;
                        queuedList.RemoveAt(i);
                        Interlocked.Increment(ref _totalDiscardedQueueIntents);
                        continue;
                    }

                    if (queued.ExpiresAtTick > 0 && queued.ExpiresAtTick < gameTick)
                    {
                        queued.Disposition = MovementIntentDisposition.RejectedExpired;
                        queuedList.RemoveAt(i);
                        Interlocked.Increment(ref _totalDiscardedQueueIntents);
                        continue;
                    }

                    if (queued.ExpiresAtTime > 0f && queued.ExpiresAtTime < currentTime)
                    {
                        queued.Disposition = MovementIntentDisposition.RejectedExpired;
                        queuedList.RemoveAt(i);
                        Interlocked.Increment(ref _totalDiscardedQueueIntents);
                        continue;
                    }

                    if (queued.EarliestApplicableTick > gameTick)
                    {
                        // Intenção para tick futuro, mantém na fila
                        continue;
                    }

                    queued.Disposition = MovementIntentDisposition.PublishedDuringCollection;
                    var collecting = _collectingIntentsBySlot.GetOrAdd(slot, _ => new List<MovementIntent>(4));
                    lock (collecting)
                    {
                        collecting.Add(queued);
                    }
                    queuedList.RemoveAt(i);
                }
            }
        }
    }

    public void BeginTick(int gameTick, float currentTime)
    {
        BeginTick(gameTick, currentTime, CurrentInternalRoundId > 0 ? CurrentInternalRoundId : 1L);
    }

    public void ResetRound(IBotControllerApi? api)
    {
        CurrentPhase = ArbitrationWindowPhase.NotStarted;
        CurrentGameTick = 0;
        CurrentTickTime = 0f;
        CurrentInternalRoundId = 0;

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
        _collectingIntentsBySlot.Clear();
        _queuedIntentsForNextTickBySlot.Clear();
        _lastDecisionsBySlot.Clear();
        _lastAppliedTickBySlot.Clear();
        _lastConflictLogTimeBySlot.Clear();
        _lastQueueFullWarnTimeBySlot.Clear();
    }

    public void ClearBotState(int slot, IBotControllerApi? api)
    {
        _collectingIntentsBySlot.TryRemove(slot, out _);
        _queuedIntentsForNextTickBySlot.TryRemove(slot, out _);
        _lastDecisionsBySlot.TryRemove(slot, out _);
        _lastAppliedTickBySlot.TryRemove(slot, out _);
        _lastQueueFullWarnTimeBySlot.TryRemove(slot, out _);
        if (_activeUsercmdHandleBySlot.TryRemove(slot, out long handle) && handle != 0 && api != null)
        {
            try { api.CancelUsercmdMovement(slot, handle); } catch { }
        }
    }

    public bool PublishDuringCollection(MovementIntent intent, long currentTick, long internalRoundId)
    {
        if (intent == null) return false;

        if (CurrentPhase != ArbitrationWindowPhase.Collecting)
        {
            Interlocked.Increment(ref _totalIntentsRejectedAfterResolution);
            intent.Disposition = MovementIntentDisposition.RejectedAfterResolution;
            TelemetryLogger?.LogEvent(
                "ARBITRAGEM - REJEICAO",
                $"**[INTENT_REJECTED_AFTER_RESOLUTION]** Bot **{intent.BotName}** (`slot={intent.BotSlot}`) tentou PublishDuringCollection fora da fase Collecting (Fase `{CurrentPhase}`, tick `{currentTick}`)!");
            return false;
        }

        if (intent.InternalRoundId <= 0 && internalRoundId > 0)
        {
            intent.Disposition = MovementIntentDisposition.RejectedWrongRound;
            TelemetryLogger?.LogEvent(
                "ARBITRAGEM - REJEICAO_SEM_ROUND",
                $"**[INTENT_REJECTED_ZERO_ROUND]** Bot **{intent.BotName}** (`slot={intent.BotSlot}`) intenção criada sem InternalRoundId!");
            return false;
        }

        if (intent.InternalRoundId > 0 && internalRoundId > 0 && intent.InternalRoundId != internalRoundId)
        {
            intent.Disposition = MovementIntentDisposition.RejectedWrongRound;
            TelemetryLogger?.LogEvent(
                "ARBITRAGEM - REJEICAO",
                $"**[INTENT_REJECTED_WRONG_ROUND]** Bot **{intent.BotName}** (`slot={intent.BotSlot}`) intenção com round incorreto ({intent.InternalRoundId} != {internalRoundId})!");
            return false;
        }

        if (intent.ExpiresAtTick > 0 && intent.ExpiresAtTick < currentTick)
        {
            intent.Disposition = MovementIntentDisposition.RejectedExpired;
            return false;
        }

        if (intent.ExpiresAtTime > 0f && intent.ExpiresAtTime < CurrentTickTime)
        {
            intent.Disposition = MovementIntentDisposition.RejectedExpired;
            return false;
        }

        // V4.2.6: Rejeição de STALE_BOMB_OBJECTIVE se a revisão do objetivo foi incrementada
        if (intent.Source == MovementIntentSource.BombObjective && intent.ObjectiveRevision != Guid.Empty)
        {
            var activeBombState = GetActiveBombObjectiveState?.Invoke();
            if (activeBombState != null && activeBombState.ObjectiveRevision != Guid.Empty && intent.ObjectiveRevision != activeBombState.ObjectiveRevision)
            {
                intent.Disposition = MovementIntentDisposition.RejectedExpired;
                TelemetryLogger?.LogEvent(
                    "STALE_BOMB_OBJECTIVE",
                    $"intentRevision={intent.ObjectiveRevision} activeRevision={activeBombState.ObjectiveRevision} bot={intent.BotSlot} reason=StaleObjectiveRevisionRejected");
                return false;
            }
        }

        intent.Disposition = MovementIntentDisposition.PublishedDuringCollection;
        var list = _collectingIntentsBySlot.GetOrAdd(intent.BotSlot, _ => new List<MovementIntent>(4));
        lock (list)
        {
            list.Add(intent);
        }
        return true;
    }

    public bool QueueForNextTick(
        MovementIntent intent,
        long currentTick,
        long internalRoundId,
        IntentPublishChannel channel = IntentPublishChannel.ExpectedBetweenTicks)
    {
        if (intent == null) return false;

        // Produtores síncronos que deveriam executar durante Collecting NÃO podem usar a fila futura para esconder erro de ordenação (Adendo 5)
        if (channel == IntentPublishChannel.UnexpectedAfterResolution)
        {
            Interlocked.Increment(ref _totalIntentsRejectedAfterResolution);
            intent.Disposition = MovementIntentDisposition.RejectedAfterResolution;
            TelemetryLogger?.LogEvent(
                "ARBITRAGEM - REJEICAO_ORDENACAO",
                $"**[UNEXPECTED_AFTER_RESOLUTION]** Produtor síncrono do Bot **{intent.BotName}** (`slot={intent.BotSlot}`) tentou enfileirar após resolução no tick `{currentTick}`!");
            return false;
        }

        if (intent.InternalRoundId <= 0 && internalRoundId > 0)
        {
            intent.Disposition = MovementIntentDisposition.RejectedWrongRound;
            return false;
        }

        if (intent.InternalRoundId > 0 && internalRoundId > 0 && intent.InternalRoundId != internalRoundId)
        {
            intent.Disposition = MovementIntentDisposition.RejectedWrongRound;
            return false;
        }

        if (intent.ExpiresAtTick > 0 && intent.ExpiresAtTick <= currentTick)
        {
            intent.Disposition = MovementIntentDisposition.RejectedExpired;
            return false;
        }

        var list = _queuedIntentsForNextTickBySlot.GetOrAdd(intent.BotSlot, _ => new List<MovementIntent>(MaxQueuedIntentsPerSlot));
        lock (list)
        {
            // Deduplicação: se já existe intenção equivalente (mesma Source, Kind e Scope), substitui pela mais recente ou mais prioritária
            int existingIndex = list.FindIndex(i => i.Source == intent.Source && i.Kind == intent.Kind && i.Scope == intent.Scope);
            if (existingIndex >= 0)
            {
                list[existingIndex] = intent;
                intent.Disposition = MovementIntentDisposition.QueuedForNextTick;
                return true;
            }

            if (list.Count >= MaxQueuedIntentsPerSlot)
            {
                Interlocked.Increment(ref _totalDiscardedQueueIntents);
                intent.Disposition = MovementIntentDisposition.RejectedQueueFull;
                float now = CurrentTickTime;
                if (!_lastQueueFullWarnTimeBySlot.TryGetValue(intent.BotSlot, out float lastWarn) || (now - lastWarn) >= 3.0f)
                {
                    _lastQueueFullWarnTimeBySlot[intent.BotSlot] = now;
                    TelemetryLogger?.LogEvent(
                        "ARBITRAGEM - FILA_CHEIA",
                        $"**[QUEUE_LIMIT_EXCEEDED]** Fila do bot {intent.BotName} ({intent.BotSlot}) excedeu {MaxQueuedIntentsPerSlot} intenções. Intenção descartada.");
                }
                return false;
            }

            intent.Disposition = MovementIntentDisposition.QueuedForNextTick;
            list.Add(intent);
        }
        return true;
    }

    public bool PublishIntent(MovementIntent intent)
    {
        if (intent == null) return false;

        // Se InternalRoundId não foi preenchido explicitamente e o Arbitrator possui round ativo, vincula-o
        if (intent.InternalRoundId <= 0 && CurrentInternalRoundId > 0)
        {
            intent.InternalRoundId = CurrentInternalRoundId;
        }

        long effectiveRoundId = intent.InternalRoundId > 0 ? intent.InternalRoundId : CurrentInternalRoundId;

        if (CurrentPhase == ArbitrationWindowPhase.Collecting)
        {
            return PublishDuringCollection(intent, CurrentGameTick, effectiveRoundId);
        }

        if (CurrentPhase == ArbitrationWindowPhase.NotStarted)
        {
            return QueueForNextTick(intent, CurrentGameTick, effectiveRoundId, IntentPublishChannel.ExpectedBetweenTicks);
        }

        // Se a fase já é Resolved, Applied ou Closed, chamada genérica para PublishIntent após a resolução é rejeitada (Adendo 5)
        return QueueForNextTick(intent, CurrentGameTick, effectiveRoundId, IntentPublishChannel.UnexpectedAfterResolution);
    }

    public void CloseCollectionWindow()
    {
        if (CurrentPhase == ArbitrationWindowPhase.Collecting)
        {
            CurrentPhase = ArbitrationWindowPhase.Resolved;
        }
    }

    public Dictionary<int, ArbitratedMovementDecision> ResolveAllIntents(int gameTick, float currentTime)
    {
        CurrentPhase = ArbitrationWindowPhase.Resolved;
        var decisions = new Dictionary<int, ArbitratedMovementDecision>();

        var allSlots = new HashSet<int>(_collectingIntentsBySlot.Keys);
        foreach (var s in _lastDecisionsBySlot.Keys) allSlots.Add(s);

        foreach (int slot in allSlots)
        {
            var decision = CollectAndResolveIntents(slot, gameTick, currentTime);
            if (decision != null)
            {
                decisions[slot] = decision;
            }
        }

        return decisions;
    }

    public void ApplyAllDecisions(
        Dictionary<int, ArbitratedMovementDecision> decisions,
        Func<int, CCSPlayerController?> getPlayer,
        IBotControllerApi? api)
    {
        CurrentPhase = ArbitrationWindowPhase.Applied;
        foreach (var kvp in decisions)
        {
            var controller = getPlayer(kvp.Key);
            ApplyWinningIntent(kvp.Value, controller, api);
        }
    }

    public void EndTick()
    {
        CurrentPhase = ArbitrationWindowPhase.Closed;
    }

    /// <summary>
    /// Etapa 1 (Pura/Determinística): Coleta todas as intenções publicadas para o bot no tick atual,
    /// aplica hierarquia de prioridades e histerese anti-flip-flop e devolve a decisão vencedora.
    /// </summary>
    public ArbitratedMovementDecision? CollectAndResolveIntents(int botSlot, int gameTick, float currentTime)
    {
        List<MovementIntent>? candidates = null;
        if (_collectingIntentsBySlot.TryRemove(botSlot, out var rawList))
        {
            lock (rawList)
            {
                candidates = rawList.Where(i => (i.ExpiresAtTime <= 0f || currentTime <= i.ExpiresAtTime) &&
                                                (i.ExpiresAtTick <= 0 || gameTick <= i.ExpiresAtTick)).ToList();
            }
        }

        var activeBombState = GetActiveBombObjectiveState?.Invoke();
        if (activeBombState != null && activeBombState.ObjectiveRevision != Guid.Empty && candidates != null)
        {
            candidates = candidates.Where(i => i.Source != MovementIntentSource.BombObjective ||
                                               i.ObjectiveRevision == Guid.Empty ||
                                               i.ObjectiveRevision == activeBombState.ObjectiveRevision).ToList();
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

        // 4. Aplica GoalPosition e Repath no NavMesh apenas se Scope não for LocalMicroMove (Ajuste 2)
        if (intent.Scope != MovementScope.LocalMicroMove)
        {
            if (intent.GoalX.HasValue && intent.GoalY.HasValue && intent.GoalZ.HasValue)
            {
                var rawGoal = new Vector(intent.GoalX.Value, intent.GoalY.Value, intent.GoalZ.Value);
                Vector? currentOrigin = pawn.AbsOrigin;
                Vector worldGoal = rawGoal;

                if (intent.GoalCoordinateSpace != SuggestedGoalCoordinateSpace.WorldAbsolute &&
                    intent.GoalCoordinateSpace != SuggestedGoalCoordinateSpace.None &&
                    currentOrigin != null)
                {
                    float botYaw = pawn.EyeAngles?.Y ?? 0.0f;
                    worldGoal = MapPlayableBounds.TransformSuggestedGoalToWorld(rawGoal, intent.GoalCoordinateSpace, currentOrigin, botYaw);
                }

                var valResult = MapPlayableBounds.ValidateGoal(worldGoal, currentOrigin, null, $"{intent.Source}:{intent.Kind}");
                if (valResult.IsValid)
                {
                    bot.GoalPosition[0] = valResult.SanitizedGoal.X;
                    bot.GoalPosition[1] = valResult.SanitizedGoal.Y;
                    bot.GoalPosition[2] = valResult.SanitizedGoal.Z;
                }
            }

            if (intent.ForceRepath || intent.Kind == MovementCommandKind.ReleaseHoldAndRepath)
            {
                bot.RepathTimer.Timestamp = 0f;
            }
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
