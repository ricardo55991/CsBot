using System.Collections.Concurrent;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using BotControllerApi;

namespace CsBotManager;

[Flags]
public enum ExpectedEngineStateChange
{
    None = 0,
    NavigationProgress = 1,
    Repath = 2,
    HoldExpired = 4,
    BombObjectiveChanged = 8,
    PlantStarted = 16,
    DefuseStarted = 32,
    BotDied = 64,
    BotRespawned = 128,
    NewWinningIntent = 256,
    RoundPhaseChanged = 512,
    HoldInitiated = 1024,
    RecoveryInitiated = 2048,
    GoalPositionChanged = 4096,
    EmergencyFallback = 8192
}

public enum TickRateSource
{
    Engine,
    Config,
    Default
}

public readonly record struct EffectiveTickRateInfo(
    float TickRate,
    float TickInterval,
    TickRateSource Source,
    int Ticks125,
    int Ticks250,
    int Ticks500);

public enum PhysicalExecutionOutcome
{
    Pending,
    AuthorizedHoldApplied,
    FullStopApplied,
    AppliedWithProgress,
    AppliedLowProgress,
    AppliedNoProgress,
    BlockedByGeometryOrNavigation,
    BlockedByUnexpectedStopState,
    ReplacedByHigherPriority,
    ReplacedByNewIntent,
    CancelledRoundEnd,
    CancelledBotDeath,
    CancelledEntityChanged,
    CancelledObjectiveAction
}

public enum StateIntegrityOutcome
{
    NotEvaluated,
    NoUnexpectedStateChange,
    EngineStateChangedExpectedly,
    EngineStateChangedUnexplained,
    PossibleExternalControllerOverride
}

public sealed class OverrideEventRecord
{
    public Guid EventId { get; init; } = Guid.NewGuid();
    public int BotSlot { get; init; }
    public long GameTick { get; init; }
    public float GameTime { get; init; }
    public string Details { get; init; } = string.Empty;
    public int SamplesAffectedCount { get; set; }
    public int SnapshotAppearancesCount { get; set; }
}

public sealed class IntegrityEpisode
{
    public string EpisodeId { get; init; } = string.Empty;
    public long InternalRoundId { get; init; }
    public int BotSlot { get; init; }
    public string LogicalActionId { get; init; } = string.Empty;
    public string ChangedFieldsKey { get; init; } = string.Empty;
    public int StartTick { get; init; }
    public int EndTick { get; set; }
    public float StartTime { get; init; }
    public float EndTime { get; set; }
    public int SampleCount { get; set; }
    public bool PersistedAcrossTicks => (EndTick - StartTick) >= 16;
}

public readonly record struct TrackedOutcomeMetadata(
    PhysicalExecutionOutcome Physical,
    StateIntegrityOutcome Integrity,
    string PhysicalReason,
    string StateIntegrityDetails,
    float Vel2D,
    float Disp2D,
    string Details,
    Guid IntentId,
    Guid LogicalActionId,
    MovementIntentSource Source,
    MovementCommandKind Kind,
    long IssuedTick,
    long CompletedTick,
    long InternalRoundId);

public enum MovementExecutionOutcome
{
    Pending,
    AuthorizedHoldApplied,
    FullStopApplied,
    AppliedWithProgress,
    AppliedLowProgress,
    AppliedNoProgress,
    ReplacedByHigherPriority,
    ReplacedByNewIntent,
    CancelledRoundEnd,
    CancelledBotDeath,
    CancelledEntityChanged,
    CancelledObjectiveAction,
    BlockedByUnexpectedStopState,
    BlockedByGeometryOrNavigation,
    EngineStateChangedExpectedly,
    EngineStateChangedUnexplained,
    PossibleExternalControllerOverride
}

public readonly record struct EntityIdentity(
    int ControllerEntityIndex,
    int PawnEntityIndex,
    ulong? SteamId,
    int SpawnGeneration);

public sealed record BotStateFingerprint(
    int BotSlot,
    long InternalRoundId,
    long GameTick,
    bool IsStopping,
    float GoalX,
    float GoalY,
    float GoalZ,
    float WaitTimestamp,
    float WaitDuration,
    float SneakTimestamp,
    float RepathTimestamp,
    ulong Buttons,
    long UsercmdHandle,
    float DesiredForwardMove,
    float DesiredSideMove,
    EntityIdentity Entity);

public sealed class MovementExecutionSample
{
    public int BotSlot { get; init; }
    public EntityIdentity Entity { get; init; }
    public long InternalRoundId { get; init; }
    public int IssuedTick { get; init; }
    public float IssuedTime { get; init; }
    public MovementIntent WinningIntent { get; init; } = null!;
    public Vector InitialPosition { get; init; } = new(0, 0, 0);

    public long LastObservedTick { get; set; }
    public float LastObservedTime { get; set; }
    public Vector LastObservedPosition { get; set; } = new(0, 0, 0);
    public float LastObservedVelocity2D { get; set; }

    public int Ticks125 { get; init; } = 8;
    public int Ticks250 { get; init; } = 16;
    public int Ticks500 { get; init; } = 32;

    public float? ObservedVel2D_125ms { get; set; }
    public float? ObservedDisp2D_250ms { get; set; }
    public float? ObservedDisp2D_500ms { get; set; }

    // V4.2: Dois eixos independentes: Resultado Físico e Integridade do Estado
    public PhysicalExecutionOutcome PhysicalOutcome { get; set; } = PhysicalExecutionOutcome.Pending;
    public StateIntegrityOutcome StateIntegrity { get; set; } = StateIntegrityOutcome.NotEvaluated;
    public string PhysicalOutcomeReason { get; set; } = string.Empty;
    public string StateIntegrityDetails { get; set; } = string.Empty;
    public float Displacement125Ms { get; set; }
    public float Displacement250Ms { get; set; }
    public float Displacement500Ms { get; set; }
    public float Velocity125Ms { get; set; }

    public long OutcomeIssuedTick { get; set; }
    public long OutcomeCompletedTick { get; set; }
    public Guid OutcomeIntentId { get; set; }
    public Guid OutcomeLogicalActionId { get; set; }
    public MovementIntentSource OutcomeSource { get; set; }
    public MovementCommandKind OutcomeKind { get; set; }
    public long OutcomeInternalRoundId { get; set; }

    public MovementExecutionOutcome Outcome
    {
        get
        {
            return PhysicalOutcome switch
            {
                PhysicalExecutionOutcome.Pending => MovementExecutionOutcome.Pending,
                PhysicalExecutionOutcome.AuthorizedHoldApplied => MovementExecutionOutcome.AuthorizedHoldApplied,
                PhysicalExecutionOutcome.FullStopApplied => MovementExecutionOutcome.FullStopApplied,
                PhysicalExecutionOutcome.AppliedWithProgress => MovementExecutionOutcome.AppliedWithProgress,
                PhysicalExecutionOutcome.AppliedLowProgress => MovementExecutionOutcome.AppliedLowProgress,
                PhysicalExecutionOutcome.AppliedNoProgress => MovementExecutionOutcome.AppliedNoProgress,
                PhysicalExecutionOutcome.BlockedByGeometryOrNavigation => MovementExecutionOutcome.BlockedByGeometryOrNavigation,
                PhysicalExecutionOutcome.BlockedByUnexpectedStopState => MovementExecutionOutcome.BlockedByUnexpectedStopState,
                PhysicalExecutionOutcome.ReplacedByHigherPriority => MovementExecutionOutcome.ReplacedByHigherPriority,
                PhysicalExecutionOutcome.ReplacedByNewIntent => MovementExecutionOutcome.ReplacedByNewIntent,
                PhysicalExecutionOutcome.CancelledRoundEnd => MovementExecutionOutcome.CancelledRoundEnd,
                PhysicalExecutionOutcome.CancelledBotDeath => MovementExecutionOutcome.CancelledBotDeath,
                PhysicalExecutionOutcome.CancelledEntityChanged => MovementExecutionOutcome.CancelledEntityChanged,
                PhysicalExecutionOutcome.CancelledObjectiveAction => MovementExecutionOutcome.CancelledObjectiveAction,
                _ => MovementExecutionOutcome.Pending
            };
        }
        set
        {
            PhysicalOutcome = value switch
            {
                MovementExecutionOutcome.AuthorizedHoldApplied => PhysicalExecutionOutcome.AuthorizedHoldApplied,
                MovementExecutionOutcome.FullStopApplied => PhysicalExecutionOutcome.FullStopApplied,
                MovementExecutionOutcome.AppliedWithProgress => PhysicalExecutionOutcome.AppliedWithProgress,
                MovementExecutionOutcome.AppliedLowProgress => PhysicalExecutionOutcome.AppliedLowProgress,
                MovementExecutionOutcome.AppliedNoProgress => PhysicalExecutionOutcome.AppliedNoProgress,
                MovementExecutionOutcome.BlockedByGeometryOrNavigation => PhysicalExecutionOutcome.BlockedByGeometryOrNavigation,
                MovementExecutionOutcome.BlockedByUnexpectedStopState => PhysicalExecutionOutcome.BlockedByUnexpectedStopState,
                MovementExecutionOutcome.ReplacedByHigherPriority => PhysicalExecutionOutcome.ReplacedByHigherPriority,
                MovementExecutionOutcome.ReplacedByNewIntent => PhysicalExecutionOutcome.ReplacedByNewIntent,
                MovementExecutionOutcome.CancelledRoundEnd => PhysicalExecutionOutcome.CancelledRoundEnd,
                MovementExecutionOutcome.CancelledBotDeath => PhysicalExecutionOutcome.CancelledBotDeath,
                MovementExecutionOutcome.CancelledEntityChanged => PhysicalExecutionOutcome.CancelledEntityChanged,
                MovementExecutionOutcome.CancelledObjectiveAction => PhysicalExecutionOutcome.CancelledObjectiveAction,
                _ => PhysicalExecutionOutcome.Pending
            };
        }
    }
    public string Details { get; set; } = string.Empty;
    public bool IsCompleted { get; set; } = false;

    public bool MatchesIntent(MovementIntent intent, EntityIdentity entity)
    {
        if (BotSlot != intent.BotSlot) return false;
        if (InternalRoundId > 0 && intent.InternalRoundId > 0 && InternalRoundId != intent.InternalRoundId) return false;
        if (Entity.ControllerEntityIndex != entity.ControllerEntityIndex) return false;

        // Compara identificadores lógicos estáveis da intenção (Adendo 3)
        if (WinningIntent.IntentId != Guid.Empty && WinningIntent.IntentId == intent.IntentId) return true;
        if (WinningIntent.LogicalActionId != Guid.Empty && WinningIntent.LogicalActionId == intent.LogicalActionId) return true;
        if (WinningIntent.TrajectoryId != Guid.Empty && WinningIntent.TrajectoryId == intent.TrajectoryId && WinningIntent.StepIndex == intent.StepIndex) return true;

        // Se ambos são TacticalNavigation para o mesmo Goal
        if (WinningIntent.Kind == MovementCommandKind.NavigateNavMesh && intent.Kind == MovementCommandKind.NavigateNavMesh)
        {
            if (WinningIntent.GoalX.HasValue && intent.GoalX.HasValue &&
                WinningIntent.GoalY.HasValue && intent.GoalY.HasValue)
            {
                float dx = WinningIntent.GoalX.Value - intent.GoalX.Value;
                float dy = WinningIntent.GoalY.Value - intent.GoalY.Value;
                if ((dx * dx + dy * dy) < 400.0f) // <= 20u do mesmo destino
                {
                    return true;
                }
            }
        }

        return false;
    }
}

public sealed class MovementExecutionTracker
{
    public BotSystemConfig Config { get; set; } = BotSystemConfig.Default;

    private readonly ConcurrentDictionary<int, MovementExecutionSample> _activeSampleBySlot = new();
    private readonly ConcurrentDictionary<int, List<MovementExecutionSample>> _completedSamplesBySlot = new();
    private readonly List<MovementExecutionSample> _matchCompletedSamples = new();
    private readonly object _matchSamplesLock = new();
    private readonly ConcurrentDictionary<int, (PhysicalExecutionOutcome Physical, StateIntegrityOutcome Integrity, float Vel2D, float Disp2D, string Details)> _latestOutcomesBySlot = new();
    private readonly ConcurrentDictionary<int, TrackedOutcomeMetadata> _latestDetailedOutcomesBySlot = new();
    private readonly ConcurrentDictionary<int, BotStateFingerprint> _postApplyFingerprintBySlot = new();
    private readonly ConcurrentDictionary<int, ExpectedEngineStateChange> _expectedEngineStateChangesBySlot = new();
    private readonly ConcurrentDictionary<int, long> _lastOverrideDetectedTickBySlot = new();
    private readonly ConcurrentDictionary<int, float> _lastOverrideLogTimeBySlot = new();
    private readonly ConcurrentDictionary<int, OverrideEventRecord> _currentActiveOverrideBySlot = new();
    private readonly ConcurrentBag<OverrideEventRecord> _uniqueOverrideEvents = new();
    private readonly ConcurrentDictionary<int, int> _consecutiveUnexplainedTicksBySlot = new();
    private long _unexplainedStateChangesCount = 0;
    private long _persistentOverrideEventsCount = 0;

    // V4.2.5: Rastreamento de Incidentes de Integridade Agrupados por Episódio
    private readonly ConcurrentBag<IntegrityEpisode> _completedIntegrityEpisodes = new();
    private readonly Dictionary<(long RoundId, int Slot, string ActionId, string FieldKey), IntegrityEpisode> _activeIntegrityEpisodes = new();

    public IReadOnlyCollection<IntegrityEpisode> GetAllIntegrityEpisodes()
    {
        var list = new List<IntegrityEpisode>(_completedIntegrityEpisodes);
        lock (_activeIntegrityEpisodes)
        {
            list.AddRange(_activeIntegrityEpisodes.Values);
        }
        return list;
    }

    public void RecordIntegritySample(int slot, long roundId, string actionId, string details, int tick, float time)
    {
        lock (_activeIntegrityEpisodes)
        {
            var key = (roundId, slot, actionId, details);
            if (_activeIntegrityEpisodes.TryGetValue(key, out var ep))
            {
                if ((time - ep.EndTime) <= 0.5f)
                {
                    ep.EndTick = tick;
                    ep.EndTime = time;
                    ep.SampleCount++;
                    return;
                }
                else
                {
                    _completedIntegrityEpisodes.Add(ep);
                    _activeIntegrityEpisodes.Remove(key);
                }
            }

            var newEp = new IntegrityEpisode
            {
                EpisodeId = $"EP-{roundId}-{slot}-{Guid.NewGuid().ToString("N")[..6]}",
                InternalRoundId = roundId,
                BotSlot = slot,
                LogicalActionId = actionId,
                ChangedFieldsKey = details,
                StartTick = tick,
                EndTick = tick,
                StartTime = time,
                EndTime = time,
                SampleCount = 1
            };
            _activeIntegrityEpisodes[key] = newEp;
        }
    }

    public IEnumerable<OverrideEventRecord> UniqueOverrideEvents => _uniqueOverrideEvents;
    public int UniqueOverrideEventsCount => _uniqueOverrideEvents.Count;
    public int OverrideSamplesAffectedCount => _uniqueOverrideEvents.Sum(e => e.SamplesAffectedCount);
    public int OverrideSnapshotAppearancesCount => _uniqueOverrideEvents.Sum(e => e.SnapshotAppearancesCount);
    public long UnexplainedStateChangesCount => Interlocked.Read(ref _unexplainedStateChangesCount);
    public long PersistentOverrideEventsCount => Interlocked.Read(ref _persistentOverrideEventsCount);

    private long _totalSamplesTracked = 0;
    private long _totalProgressOutcomes = 0;
    private long _totalBlockedOutcomes = 0;
    private long _totalOverrideOutcomes = 0;
    private long _totalCompletedSamples = 0;

    public long TotalSamplesTracked => Interlocked.Read(ref _totalSamplesTracked);
    public long TotalProgressOutcomes => Interlocked.Read(ref _totalProgressOutcomes);
    public long TotalBlockedOutcomes => Interlocked.Read(ref _totalBlockedOutcomes);
    public long TotalOverrideOutcomes => Interlocked.Read(ref _totalOverrideOutcomes);
    public long TotalCompletedSamples => Interlocked.Read(ref _totalCompletedSamples);

    public int ActiveSamplesCount => _activeSampleBySlot.Count;

    public List<MovementExecutionSample> GetAllCompletedSamples()
    {
        lock (_matchSamplesLock)
        {
            if (_matchCompletedSamples.Count > 0)
            {
                return new List<MovementExecutionSample>(_matchCompletedSamples);
            }
        }
        var result = new List<MovementExecutionSample>();
        foreach (var kvp in _completedSamplesBySlot)
        {
            lock (kvp.Value)
            {
                result.AddRange(kvp.Value);
            }
        }
        return result;
    }

    public void ResetMatch()
    {
        lock (_matchSamplesLock)
        {
            _matchCompletedSamples.Clear();
        }
        lock (_activeIntegrityEpisodes)
        {
            _activeIntegrityEpisodes.Clear();
        }
        _completedIntegrityEpisodes.Clear();
    }

    public static float? EngineTickIntervalOverride { get; set; }
    private static bool _tickRateWarningLogged = false;

    public EffectiveTickRateInfo DetermineEffectiveTickRateInfo()
    {
        float engineInterval = 0f;
        if (EngineTickIntervalOverride.HasValue)
        {
            if (EngineTickIntervalOverride.Value > 0f)
            {
                engineInterval = EngineTickIntervalOverride.Value;
            }
            else
            {
                engineInterval = 0f; // Simula engine indisponível
            }
        }
        else
        {
            try
            {
                engineInterval = CounterStrikeSharp.API.Server.TickInterval;
            }
            catch
            {
                engineInterval = 0f;
            }
        }

        if (engineInterval > 0.0001f && engineInterval < 1.0f && !float.IsNaN(engineInterval) && !float.IsInfinity(engineInterval))
        {
            float rate = 1.0f / engineInterval;
            int t125 = MillisecondsToTicks(125.0, engineInterval);
            int t250 = MillisecondsToTicks(250.0, engineInterval);
            int t500 = MillisecondsToTicks(500.0, engineInterval);
            return new EffectiveTickRateInfo(rate, engineInterval, TickRateSource.Engine, t125, t250, t500);
        }

        if (Config != null && Config.ServerTickRate > 0f)
        {
            float rate = Config.ServerTickRate;
            float interval = 1.0f / rate;
            int t125 = MillisecondsToTicks(125.0, interval);
            int t250 = MillisecondsToTicks(250.0, interval);
            int t500 = MillisecondsToTicks(500.0, interval);
            return new EffectiveTickRateInfo(rate, interval, TickRateSource.Config, t125, t250, t500);
        }

        if (!_tickRateWarningLogged)
        {
            _tickRateWarningLogged = true;
            System.Console.WriteLine("[CsBotManager] WARNING: Tickrate da engine ou config não disponível/inválida. Utilizando 64 Hz como Default.");
        }

        float defaultRate = 64.0f;
        float defaultInterval = 1.0f / defaultRate;
        int dt125 = MillisecondsToTicks(125.0, defaultInterval);
        int dt250 = MillisecondsToTicks(250.0, defaultInterval);
        int dt500 = MillisecondsToTicks(500.0, defaultInterval);
        return new EffectiveTickRateInfo(defaultRate, defaultInterval, TickRateSource.Default, dt125, dt250, dt500);
    }

    public float DetermineEffectiveTickRate() => DetermineEffectiveTickRateInfo().TickRate;
    public float DetermineEffectiveTickInterval() => DetermineEffectiveTickRateInfo().TickInterval;

    public static int MillisecondsToTicks(double milliseconds, double tickIntervalSeconds)
    {
        if (tickIntervalSeconds <= 0)
            throw new ArgumentOutOfRangeException(nameof(tickIntervalSeconds));

        double ticks = milliseconds / (tickIntervalSeconds * 1000.0);
        return Math.Max(1, (int)Math.Round(ticks));
    }

    public void ResetRound()
    {
        _activeSampleBySlot.Clear();
        _completedSamplesBySlot.Clear();
        _latestOutcomesBySlot.Clear();
        _latestDetailedOutcomesBySlot.Clear();
        _postApplyFingerprintBySlot.Clear();
        _expectedEngineStateChangesBySlot.Clear();
        _lastOverrideDetectedTickBySlot.Clear();
        _lastOverrideLogTimeBySlot.Clear();

        lock (_activeIntegrityEpisodes)
        {
            foreach (var ep in _activeIntegrityEpisodes.Values)
            {
                _completedIntegrityEpisodes.Add(ep);
            }
            _activeIntegrityEpisodes.Clear();
        }
    }

    public void RegisterExpectedEngineStateChange(int slot, ExpectedEngineStateChange change)
    {
        _expectedEngineStateChangesBySlot.AddOrUpdate(slot, change, (_, prev) => prev | change);
    }

    public void CancelBotSamples(int slot, PhysicalExecutionOutcome physicalOutcome, string reason = "")
    {
        if (_activeSampleBySlot.TryRemove(slot, out var sample))
        {
            sample.IsCompleted = true;
            sample.PhysicalOutcome = physicalOutcome;
            sample.Details = $"Cancelado ({physicalOutcome}) {reason}".Trim();
            ArchiveCompletedSample(slot, sample);
        }
    }

    public void CancelBotSamples(int slot, MovementExecutionOutcome outcome)
    {
        var physical = outcome switch
        {
            MovementExecutionOutcome.CancelledRoundEnd => PhysicalExecutionOutcome.CancelledRoundEnd,
            MovementExecutionOutcome.CancelledBotDeath => PhysicalExecutionOutcome.CancelledBotDeath,
            MovementExecutionOutcome.CancelledEntityChanged => PhysicalExecutionOutcome.CancelledEntityChanged,
            MovementExecutionOutcome.CancelledObjectiveAction => PhysicalExecutionOutcome.CancelledObjectiveAction,
            MovementExecutionOutcome.AuthorizedHoldApplied => PhysicalExecutionOutcome.AuthorizedHoldApplied,
            MovementExecutionOutcome.FullStopApplied => PhysicalExecutionOutcome.FullStopApplied,
            _ => PhysicalExecutionOutcome.Pending
        };
        CancelBotSamples(slot, physical, outcome.ToString());
    }

    private void ArchiveCompletedSample(int slot, MovementExecutionSample sample)
    {
        Interlocked.Increment(ref _totalCompletedSamples);
        lock (_matchSamplesLock)
        {
            _matchCompletedSamples.Add(sample);
        }
        var list = _completedSamplesBySlot.GetOrAdd(slot, _ => new List<MovementExecutionSample>(6));
        lock (list)
        {
            if (list.Count >= 6)
            {
                list.RemoveAt(0);
            }
            list.Add(sample);
        }
    }

    public void RecordOrUpdateIntentIssued(
        MovementIntent intent,
        EntityIdentity entity,
        long currentTick,
        float currentTime,
        Vector initialPos,
        float velocity2D,
        float tickIntervalSeconds)
    {
        if (intent == null) return;
        int slot = intent.BotSlot;

        float effectiveTickInterval = tickIntervalSeconds > 0 ? tickIntervalSeconds : (1.0f / Math.Max(1.0f, Config.ServerTickRate));
        int ticks125 = MillisecondsToTicks(125.0, effectiveTickInterval);
        int ticks250 = MillisecondsToTicks(250.0, effectiveTickInterval);
        int ticks500 = MillisecondsToTicks(500.0, effectiveTickInterval);

        if (_activeSampleBySlot.TryGetValue(slot, out var existing) && !existing.IsCompleted)
        {
            if (existing.MatchesIntent(intent, entity))
            {
                // Mesma continuidade lógica: atualiza estado observado recente sem reiniciar relógios (Adendo 3)
                existing.LastObservedTick = currentTick;
                existing.LastObservedTime = currentTime;
                existing.LastObservedPosition = initialPos;
                existing.LastObservedVelocity2D = velocity2D;
                return;
            }

            // Ação anterior substituída por uma nova intenção
            existing.IsCompleted = true;
            existing.PhysicalOutcome = (intent.Source < existing.WinningIntent.Source)
                ? PhysicalExecutionOutcome.ReplacedByHigherPriority
                : PhysicalExecutionOutcome.Pending;
            existing.Details = $"Substituído por {intent.Source}:{intent.Kind}";
            ArchiveCompletedSample(slot, existing);
        }

        var newSample = new MovementExecutionSample
        {
            BotSlot = slot,
            Entity = entity,
            InternalRoundId = intent.InternalRoundId,
            IssuedTick = (int)currentTick,
            IssuedTime = currentTime,
            WinningIntent = intent,
            InitialPosition = new Vector(initialPos.X, initialPos.Y, initialPos.Z),
            LastObservedTick = currentTick,
            LastObservedTime = currentTime,
            LastObservedPosition = initialPos,
            LastObservedVelocity2D = velocity2D,
            Ticks125 = ticks125,
            Ticks250 = ticks250,
            Ticks500 = ticks500
        };

        _activeSampleBySlot[slot] = newSample;
        Interlocked.Increment(ref _totalSamplesTracked);
    }

    public void RecordIntentIssued(
        int botSlot,
        int currentTick,
        float currentTime,
        MovementIntent winningIntent,
        Vector initialPos)
    {
        var entity = new EntityIdentity(botSlot, botSlot, 0, 1);
        float tickInterval = 1.0f / Math.Max(1.0f, Config.ServerTickRate);
        RecordOrUpdateIntentIssued(winningIntent, entity, currentTick, currentTime, initialPos, 0f, tickInterval);
    }

    public static BotStateFingerprint? CreateFingerprint(
        int slot,
        CCSPlayerController? controller,
        long internalRoundId,
        long gameTick,
        MovementIntent? intent,
        long usercmdHandle)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return null;
        var pawn = controller.PlayerPawn.Value;
        var bot = pawn?.Bot;
        if (pawn == null || bot == null) return null;

        float gx = 0, gy = 0, gz = 0;
        try
        {
            gx = bot.GoalPosition[0];
            gy = bot.GoalPosition[1];
            gz = bot.GoalPosition[2];
        }
        catch { }

        float waitTs = 0f, waitDur = 0f, sneakTs = 0f, repathTs = 0f;
        try { waitTs = bot.WaitTimer.Timestamp; waitDur = bot.WaitTimer.Duration; } catch { }
        try { sneakTs = bot.SneakTimer.Timestamp; } catch { }
        try { repathTs = bot.RepathTimer.Timestamp; } catch { }

        var identity = new EntityIdentity(
            ControllerEntityIndex: (int)controller.Index,
            PawnEntityIndex: (int)(pawn.Index),
            SteamId: controller.SteamID,
            SpawnGeneration: 1);

        return new BotStateFingerprint(
            BotSlot: slot,
            InternalRoundId: internalRoundId,
            GameTick: gameTick,
            IsStopping: bot.IsStopping,
            GoalX: gx,
            GoalY: gy,
            GoalZ: gz,
            WaitTimestamp: waitTs,
            WaitDuration: waitDur,
            SneakTimestamp: sneakTs,
            RepathTimestamp: repathTs,
            Buttons: intent?.Buttons ?? 0UL,
            UsercmdHandle: usercmdHandle,
            DesiredForwardMove: intent?.ForwardMove ?? 0f,
            DesiredSideMove: intent?.SideMove ?? 0f,
            Entity: identity);
    }

    public void StorePostApplyFingerprint(int slot, BotStateFingerprint? fingerprint)
    {
        if (fingerprint != null)
        {
            _postApplyFingerprintBySlot[slot] = fingerprint;
        }
    }

    public bool CheckAndAuditPreTickOverride(
        int slot,
        BotStateFingerprint currentEnginePreApply,
        MatchTelemetryLogger? telemetry,
        float currentTime)
    {
        if (!_postApplyFingerprintBySlot.TryGetValue(slot, out var lastPostApply))
            return false;

        // Se for o mesmo tick ou mais antigo, não há intervalo de engine a comparar
        if (currentEnginePreApply.GameTick <= lastPostApply.GameTick)
            return false;

        // Se o round mudou, descarta
        if (currentEnginePreApply.InternalRoundId != lastPostApply.InternalRoundId)
            return false;

        // Se a entidade mudou (ex: respawn de bot ou reassociação de slot), descarta
        if (currentEnginePreApply.Entity.ControllerEntityIndex != lastPostApply.Entity.ControllerEntityIndex)
            return false;

        bool isStoppingAltered = lastPostApply.IsStopping != currentEnginePreApply.IsStopping;
        float goalDelta = MathF.Sqrt(
            MathF.Pow(lastPostApply.GoalX - currentEnginePreApply.GoalX, 2) +
            MathF.Pow(lastPostApply.GoalY - currentEnginePreApply.GoalY, 2));
        bool goalAltered = goalDelta > 15.0f;

        // V4.2.4: Usar EngineStateChangedUnexplained como padrão.
        // Promover para PossibleExternalControllerOverride apenas se for campo crítico e persistir por >= 16 ticks.
        if (isStoppingAltered || goalAltered)
        {
            // Verifica se houve uma alteração interna esperada registrada (Adendo 6 / Checkpoint 6)
            if (_expectedEngineStateChangesBySlot.TryRemove(slot, out var expected) && expected != ExpectedEngineStateChange.None)
            {
                _consecutiveUnexplainedTicksBySlot[slot] = 0;
                return false;
            }

            Interlocked.Increment(ref _unexplainedStateChangesCount);
            int consecutiveTicks = _consecutiveUnexplainedTicksBySlot.AddOrUpdate(slot, 1, (_, c) => c + 1);

            bool isCriticalField = isStoppingAltered || goalDelta > 64.0f;
            bool isPersistent = consecutiveTicks >= 16;

            if (!isCriticalField || !isPersistent)
            {
                // Permanece classificado como EngineStateChangedUnexplained sem promover para override externo
                return false;
            }

            Interlocked.Increment(ref _persistentOverrideEventsCount);
            long currentTick = currentEnginePreApply.GameTick;
            bool isNewEvent = !_lastOverrideDetectedTickBySlot.TryGetValue(slot, out long lastTick) || (currentTick - lastTick) > 64;
            _lastOverrideDetectedTickBySlot[slot] = currentTick;

            string diffs = $"IsStopping({lastPostApply.IsStopping}->{currentEnginePreApply.IsStopping}), " +
                           $"Goal(({lastPostApply.GoalX:F0},{lastPostApply.GoalY:F0})->({currentEnginePreApply.GoalX:F0},{currentEnginePreApply.GoalY:F0}), delta={goalDelta:F1}u, consec={consecutiveTicks})";

            if (isNewEvent)
            {
                Interlocked.Increment(ref _totalOverrideOutcomes);
                var overrideRecord = new OverrideEventRecord
                {
                    BotSlot = slot,
                    GameTick = currentTick,
                    GameTime = currentTime,
                    Details = diffs
                };
                _uniqueOverrideEvents.Add(overrideRecord);
                _currentActiveOverrideBySlot[slot] = overrideRecord;
            }

            if (telemetry != null && telemetry.IsEnabled)
            {
                if (!_lastOverrideLogTimeBySlot.TryGetValue(slot, out float lastLog) || (currentTime - lastLog) >= 2.0f)
                {
                    _lastOverrideLogTimeBySlot[slot] = currentTime;
                    telemetry.LogEvent(
                        "FINGERPRINT - SOBREPOSICAO",
                        $"**[POSSIBLE_EXTERNAL_CONTROLLER_OVERRIDE]** Slot `{slot}` modificado externamente entre ticks `{lastPostApply.GameTick}` e `{currentEnginePreApply.GameTick}`: {diffs}");
                }
            }
            return true;
        }
        else
        {
            _consecutiveUnexplainedTicksBySlot[slot] = 0;
        }

        return false;
    }

    public (StateIntegrityOutcome Outcome, string Details) EvaluateStateIntegrity(
        int slot,
        BotStateFingerprint? previousPostApply,
        BotStateFingerprint currentPreApply)
    {
        if (previousPostApply == null)
            return (StateIntegrityOutcome.NoUnexpectedStateChange, "No previous fingerprint");

        bool isStoppingAltered = previousPostApply.IsStopping != currentPreApply.IsStopping;
        bool goalAltered = MathF.Abs(previousPostApply.GoalX - currentPreApply.GoalX) > 2.0f ||
                           MathF.Abs(previousPostApply.GoalY - currentPreApply.GoalY) > 2.0f;
        bool waitTimerAltered = MathF.Abs(previousPostApply.WaitTimestamp - currentPreApply.WaitTimestamp) > 0.05f;

        if (isStoppingAltered || goalAltered || waitTimerAltered)
        {
            if (_expectedEngineStateChangesBySlot.TryGetValue(slot, out var expected) && expected != ExpectedEngineStateChange.None)
            {
                return (StateIntegrityOutcome.EngineStateChangedExpectedly, $"Alteração esperada: {expected}");
            }

            string diffs = $"IsStopping({previousPostApply.IsStopping}->{currentPreApply.IsStopping}), " +
                           $"Goal(({previousPostApply.GoalX:F0},{previousPostApply.GoalY:F0})->({currentPreApply.GoalX:F0},{currentPreApply.GoalY:F0}))";
            return (StateIntegrityOutcome.EngineStateChangedUnexplained, diffs);
        }

        return (StateIntegrityOutcome.NoUnexpectedStateChange, "Clean tick");
    }

    public static (PhysicalExecutionOutcome Physical, string Reason, string Details) ClassifyPhysicalOutcomeDetailed(
        MovementIntent intent,
        float disp500,
        float vel125,
        BotSystemConfig? config = null,
        bool replaced = false,
        bool cancelledRoundEnd = false,
        bool cancelledBotDeath = false,
        bool cancelledEntityChanged = false)
    {
        var cfg = config ?? BotSystemConfig.Default;
        if (cancelledRoundEnd) return (PhysicalExecutionOutcome.CancelledRoundEnd, "CANCELLED_ROUND_END", "Round encerrado");
        if (cancelledBotDeath) return (PhysicalExecutionOutcome.CancelledBotDeath, "CANCELLED_BOT_DEATH", "Bot morreu");
        if (cancelledEntityChanged) return (PhysicalExecutionOutcome.CancelledEntityChanged, "CANCELLED_ENTITY_CHANGED", "Entidade trocada");
        if (replaced) return (PhysicalExecutionOutcome.ReplacedByHigherPriority, "REPLACED_BY_HIGHER_PRIORITY", "Substituído por maior prioridade");

        bool isHoldStop = intent.Kind == MovementCommandKind.HoldStop;

        // V4.2 Checkpoint 1 & 2: Classificação rigorosa de Hold vs Movimento
        if (isHoldStop)
        {
            if (intent.IsHoldAuthorized && !intent.ExpectedMovement)
            {
                if (disp500 < cfg.ExecutionLowProgressDistance500Ms)
                {
                    return (PhysicalExecutionOutcome.AuthorizedHoldApplied, "AUTHORIZED_HOLD_STEADY", $"Hold autorizado ({intent.Reason}): disp500ms={disp500:F1}u");
                }
                else if (vel125 < 30.0f)
                {
                    // Movimento residual/decaimento natural da engine enquanto entra em hold
                    return (PhysicalExecutionOutcome.AuthorizedHoldApplied, "RESIDUAL_MOMENTUM_OR_DECAY", $"Hold autorizado com desaceleração residual ({intent.Reason}): disp500ms={disp500:F1}u, vel125ms={vel125:F1}u/s");
                }
                else
                {
                    return (PhysicalExecutionOutcome.BlockedByUnexpectedStopState, "UNEXPECTED_MOVEMENT_DURING_HOLD", $"Hold autorizado mas movimento detectado ({intent.Reason}): disp500ms={disp500:F1}u, vel125ms={vel125:F1}u/s");
                }
            }
            else
            {
                if (disp500 < cfg.ExecutionLowProgressDistance500Ms)
                {
                    return (PhysicalExecutionOutcome.FullStopApplied, "FULL_STOP_STEADY", $"Parada intencional ({intent.Reason}): disp500ms={disp500:F1}u");
                }
                else
                {
                    return (PhysicalExecutionOutcome.FullStopApplied, "RESIDUAL_MOMENTUM", $"Parada intencional com inércia: disp500ms={disp500:F1}u");
                }
            }
        }

        // Intenção de parada explícita sem ser HoldStop
        if (intent.IsStopping && !intent.ExpectedMovement)
        {
            return (PhysicalExecutionOutcome.FullStopApplied, "EXPLICIT_STOP_FLAG", $"Parada solicitada ({intent.Reason}): disp500ms={disp500:F1}u");
        }

        // Movimento esperado
        if (intent.ExpectedMovement)
        {
            if (disp500 >= cfg.ExecutionProgressDistance500Ms)
            {
                return (PhysicalExecutionOutcome.AppliedWithProgress, "NORMAL_PROGRESS", $"Progresso físico normal: disp500ms={disp500:F1}u, vel125ms={vel125:F1}u/s");
            }
            if (disp500 >= cfg.ExecutionLowProgressDistance500Ms)
            {
                return (PhysicalExecutionOutcome.AppliedLowProgress, "LOW_PROGRESS_OR_SHORT_STRAFE", $"Progresso baixo/strafe curto: disp500ms={disp500:F1}u, vel125ms={vel125:F1}u/s");
            }
            if (intent.IsStopping)
            {
                return (PhysicalExecutionOutcome.BlockedByUnexpectedStopState, "ENGINE_STOPPING_FLAG", $"Comando {intent.Source}:{intent.Kind} impedido por parada: disp500ms={disp500:F1}u");
            }
            return (PhysicalExecutionOutcome.AppliedNoProgress, "APPLIED_NO_PROGRESS", $"Comando {intent.Source}:{intent.Kind} sem deslocamento: disp500ms={disp500:F1}u, vel125ms={vel125:F1}u/s");
        }

        return (PhysicalExecutionOutcome.FullStopApplied, "DEFAULT_STOP", $"Parada padrão: disp500ms={disp500:F1}u");
    }

    public static (PhysicalExecutionOutcome Physical, string Details) ClassifyPhysicalOutcome(
        MovementIntent intent,
        float disp500,
        float vel125,
        BotSystemConfig? config = null,
        bool replaced = false,
        bool cancelledRoundEnd = false,
        bool cancelledBotDeath = false,
        bool cancelledEntityChanged = false)
    {
        var res = ClassifyPhysicalOutcomeDetailed(intent, disp500, vel125, config, replaced, cancelledRoundEnd, cancelledBotDeath, cancelledEntityChanged);
        return (res.Physical, res.Details);
    }

    public void UpdateTick(
        long currentTick,
        float currentTime,
        List<CCSPlayerController> aliveBots,
        MatchTelemetryLogger? telemetry)
    {
        foreach (var bot in aliveBots)
        {
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive) continue;
            var pawn = bot.PlayerPawn.Value;
            if (pawn == null || pawn.AbsOrigin == null) continue;

            int slot = bot.Slot;
            if (!_activeSampleBySlot.TryGetValue(slot, out var sample)) continue;
            if (sample.IsCompleted) continue;

            var absVel = pawn.AbsVelocity;
            float currentVel2D = absVel != null ? MathF.Sqrt(absVel.X * absVel.X + absVel.Y * absVel.Y) : 0f;
            Vector currentPos = pawn.AbsOrigin;

            long elapsedTicks = currentTick - sample.IssuedTick;

            // Amostra ~125ms
            if (elapsedTicks >= sample.Ticks125 && sample.ObservedVel2D_125ms == null)
            {
                sample.ObservedVel2D_125ms = currentVel2D;
                sample.Velocity125Ms = currentVel2D;
                float dx8 = currentPos.X - sample.InitialPosition.X;
                float dy8 = currentPos.Y - sample.InitialPosition.Y;
                sample.Displacement125Ms = MathF.Sqrt(dx8 * dx8 + dy8 * dy8);
            }

            // Amostra ~250ms
            if (elapsedTicks >= sample.Ticks250 && sample.ObservedDisp2D_250ms == null)
            {
                float dx16 = currentPos.X - sample.InitialPosition.X;
                float dy16 = currentPos.Y - sample.InitialPosition.Y;
                sample.ObservedDisp2D_250ms = MathF.Sqrt(dx16 * dx16 + dy16 * dy16);
                sample.Displacement250Ms = sample.ObservedDisp2D_250ms.Value;
            }

            // Amostra ~500ms -> Classificação Final
            if (elapsedTicks >= sample.Ticks500)
            {
                float dx32 = currentPos.X - sample.InitialPosition.X;
                float dy32 = currentPos.Y - sample.InitialPosition.Y;
                float disp32 = MathF.Sqrt(dx32 * dx32 + dy32 * dy32);
                sample.ObservedDisp2D_500ms = disp32;
                sample.Displacement500Ms = disp32;
                if (sample.ObservedDisp2D_250ms.HasValue) sample.Displacement250Ms = sample.ObservedDisp2D_250ms.Value;
                if (sample.ObservedVel2D_125ms.HasValue) sample.Velocity125Ms = sample.ObservedVel2D_125ms.Value;
                sample.IsCompleted = true;

                var (physical, reason, details) = ClassifyPhysicalOutcomeDetailed(sample.WinningIntent, disp32, sample.Velocity125Ms, Config);
                if (physical == PhysicalExecutionOutcome.AppliedWithProgress || physical == PhysicalExecutionOutcome.AppliedLowProgress)
                {
                    Interlocked.Increment(ref _totalProgressOutcomes);
                }
                else if (physical == PhysicalExecutionOutcome.AppliedNoProgress || physical == PhysicalExecutionOutcome.BlockedByGeometryOrNavigation)
                {
                    Interlocked.Increment(ref _totalBlockedOutcomes);
                }

                // PARTE 1: Eixo separado de Integridade do Estado (nunca sobrescreve o resultado físico)
                StateIntegrityOutcome integrity;
                string integrityDetails = string.Empty;

                bool wasOverride = _lastOverrideDetectedTickBySlot.TryGetValue(slot, out long oTick) &&
                                   (oTick >= sample.IssuedTick && oTick <= currentTick);

                if (wasOverride)
                {
                    integrity = StateIntegrityOutcome.PossibleExternalControllerOverride;
                    integrityDetails = $"Modificação externa detectada entre ticks {sample.IssuedTick} e {currentTick}";
                    if (_currentActiveOverrideBySlot.TryGetValue(slot, out var activeOverride))
                    {
                        activeOverride.SamplesAffectedCount++;
                    }
                }
                else if (_expectedEngineStateChangesBySlot.TryGetValue(slot, out var expected) && expected != ExpectedEngineStateChange.None)
                {
                    integrity = StateIntegrityOutcome.EngineStateChangedExpectedly;
                    integrityDetails = $"Mudança esperada registrada: {expected}";
                }
                else
                {
                    integrity = StateIntegrityOutcome.NoUnexpectedStateChange;
                }

                sample.PhysicalOutcome = physical;
                sample.PhysicalOutcomeReason = reason;
                sample.StateIntegrity = integrity;
                sample.StateIntegrityDetails = integrityDetails;
                sample.Details = details;
                sample.OutcomeIssuedTick = sample.IssuedTick;
                sample.OutcomeCompletedTick = currentTick;
                if (sample.WinningIntent != null)
                {
                    sample.OutcomeIntentId = sample.WinningIntent.IntentId;
                    sample.OutcomeLogicalActionId = sample.WinningIntent.LogicalActionId;
                    sample.OutcomeSource = sample.WinningIntent.Source;
                    sample.OutcomeKind = sample.WinningIntent.Kind;
                    sample.OutcomeInternalRoundId = sample.WinningIntent.InternalRoundId;
                }

                if (integrity == StateIntegrityOutcome.PossibleExternalControllerOverride || integrity == StateIntegrityOutcome.EngineStateChangedUnexplained)
                {
                    RecordIntegritySample(slot, sample.InternalRoundId, sample.WinningIntent?.LogicalActionId.ToString() ?? Guid.Empty.ToString(), integrityDetails, (int)currentTick, currentTime);
                }

                var meta = new TrackedOutcomeMetadata(
                    Physical: physical,
                    Integrity: integrity,
                    PhysicalReason: reason,
                    StateIntegrityDetails: integrityDetails,
                    Vel2D: currentVel2D,
                    Disp2D: disp32,
                    Details: details,
                    IntentId: sample.WinningIntent?.IntentId ?? Guid.Empty,
                    LogicalActionId: sample.WinningIntent?.LogicalActionId ?? Guid.Empty,
                    Source: sample.WinningIntent?.Source ?? MovementIntentSource.TacticalNavigation,
                    Kind: sample.WinningIntent?.Kind ?? MovementCommandKind.NavigateNavMesh,
                    IssuedTick: sample.IssuedTick,
                    CompletedTick: currentTick,
                    InternalRoundId: sample.InternalRoundId);

                _latestOutcomesBySlot[slot] = (physical, integrity, currentVel2D, disp32, details);
                _latestDetailedOutcomesBySlot[slot] = meta;
                ArchiveCompletedSample(slot, sample);

                // Remoção condicional da coleção ativa (Item 5)
                _activeSampleBySlot.TryRemove(KeyValuePair.Create(slot, sample));
            }
        }
    }

    public void CompleteSample(
        int slot,
        PhysicalExecutionOutcome physicalOutcome,
        StateIntegrityOutcome integrity = StateIntegrityOutcome.NotEvaluated,
        string details = "",
        float currentVel2D = 0f,
        float disp32 = 0f)
    {
        if (_activeSampleBySlot.TryGetValue(slot, out var sample))
        {
            sample.IsCompleted = true;
            sample.PhysicalOutcome = physicalOutcome;
            sample.PhysicalOutcomeReason = physicalOutcome.ToString();
            sample.StateIntegrity = integrity;
            sample.Details = details;
            sample.Displacement500Ms = disp32;
            sample.OutcomeIssuedTick = sample.IssuedTick;
            sample.OutcomeCompletedTick = sample.LastObservedTick;
            if (sample.WinningIntent != null)
            {
                sample.OutcomeIntentId = sample.WinningIntent.IntentId;
                sample.OutcomeLogicalActionId = sample.WinningIntent.LogicalActionId;
                sample.OutcomeSource = sample.WinningIntent.Source;
                sample.OutcomeKind = sample.WinningIntent.Kind;
                sample.OutcomeInternalRoundId = sample.WinningIntent.InternalRoundId;
            }

            var meta = new TrackedOutcomeMetadata(
                Physical: physicalOutcome,
                Integrity: integrity,
                PhysicalReason: sample.PhysicalOutcomeReason,
                StateIntegrityDetails: sample.StateIntegrityDetails,
                Vel2D: currentVel2D,
                Disp2D: disp32,
                Details: details,
                IntentId: sample.WinningIntent?.IntentId ?? Guid.Empty,
                LogicalActionId: sample.WinningIntent?.LogicalActionId ?? Guid.Empty,
                Source: sample.WinningIntent?.Source ?? MovementIntentSource.TacticalNavigation,
                Kind: sample.WinningIntent?.Kind ?? MovementCommandKind.NavigateNavMesh,
                IssuedTick: sample.IssuedTick,
                CompletedTick: sample.LastObservedTick,
                InternalRoundId: sample.InternalRoundId);

            _latestOutcomesBySlot[slot] = (physicalOutcome, integrity, currentVel2D, disp32, details);
            _latestDetailedOutcomesBySlot[slot] = meta;
            ArchiveCompletedSample(slot, sample);
            _activeSampleBySlot.TryRemove(KeyValuePair.Create(slot, sample));
        }
        else
        {
            var fallbackMeta = new TrackedOutcomeMetadata(
                Physical: physicalOutcome,
                Integrity: integrity,
                PhysicalReason: physicalOutcome.ToString(),
                StateIntegrityDetails: string.Empty,
                Vel2D: currentVel2D,
                Disp2D: disp32,
                Details: details,
                IntentId: Guid.Empty,
                LogicalActionId: Guid.Empty,
                Source: MovementIntentSource.TacticalNavigation,
                Kind: MovementCommandKind.NavigateNavMesh,
                IssuedTick: 0,
                CompletedTick: 0,
                InternalRoundId: 1);

            _latestOutcomesBySlot[slot] = (physicalOutcome, integrity, currentVel2D, disp32, details);
            _latestDetailedOutcomesBySlot[slot] = fallbackMeta;
        }
    }

    public void CompleteSample(int slot, MovementExecutionOutcome outcome, string details, float currentVel2D = 0f, float disp32 = 0f)
    {
        var physical = outcome switch
        {
            MovementExecutionOutcome.AuthorizedHoldApplied => PhysicalExecutionOutcome.AuthorizedHoldApplied,
            MovementExecutionOutcome.FullStopApplied => PhysicalExecutionOutcome.FullStopApplied,
            MovementExecutionOutcome.AppliedWithProgress => PhysicalExecutionOutcome.AppliedWithProgress,
            MovementExecutionOutcome.AppliedLowProgress => PhysicalExecutionOutcome.AppliedLowProgress,
            MovementExecutionOutcome.AppliedNoProgress => PhysicalExecutionOutcome.AppliedNoProgress,
            MovementExecutionOutcome.BlockedByGeometryOrNavigation => PhysicalExecutionOutcome.BlockedByGeometryOrNavigation,
            MovementExecutionOutcome.BlockedByUnexpectedStopState => PhysicalExecutionOutcome.BlockedByUnexpectedStopState,
            MovementExecutionOutcome.ReplacedByHigherPriority => PhysicalExecutionOutcome.ReplacedByHigherPriority,
            MovementExecutionOutcome.CancelledRoundEnd => PhysicalExecutionOutcome.CancelledRoundEnd,
            MovementExecutionOutcome.CancelledBotDeath => PhysicalExecutionOutcome.CancelledBotDeath,
            MovementExecutionOutcome.CancelledEntityChanged => PhysicalExecutionOutcome.CancelledEntityChanged,
            MovementExecutionOutcome.CancelledObjectiveAction => PhysicalExecutionOutcome.CancelledObjectiveAction,
            _ => PhysicalExecutionOutcome.Pending
        };
        var integrity = (outcome == MovementExecutionOutcome.PossibleExternalControllerOverride)
            ? StateIntegrityOutcome.PossibleExternalControllerOverride
            : StateIntegrityOutcome.NotEvaluated;
        CompleteSample(slot, physical, integrity, details, currentVel2D, disp32);
    }

    public (MovementExecutionOutcome Outcome, float Vel2D, float Disp2D, string Details)? GetLatestOutcome(int botSlot)
    {
        if (_latestOutcomesBySlot.TryGetValue(botSlot, out var val))
        {
            var outcome = val.Physical switch
            {
                PhysicalExecutionOutcome.AuthorizedHoldApplied => MovementExecutionOutcome.AuthorizedHoldApplied,
                PhysicalExecutionOutcome.FullStopApplied => MovementExecutionOutcome.FullStopApplied,
                PhysicalExecutionOutcome.AppliedWithProgress => MovementExecutionOutcome.AppliedWithProgress,
                PhysicalExecutionOutcome.AppliedLowProgress => MovementExecutionOutcome.AppliedLowProgress,
                PhysicalExecutionOutcome.AppliedNoProgress => MovementExecutionOutcome.AppliedNoProgress,
                PhysicalExecutionOutcome.BlockedByGeometryOrNavigation => MovementExecutionOutcome.BlockedByGeometryOrNavigation,
                PhysicalExecutionOutcome.BlockedByUnexpectedStopState => MovementExecutionOutcome.BlockedByUnexpectedStopState,
                PhysicalExecutionOutcome.ReplacedByHigherPriority => MovementExecutionOutcome.ReplacedByHigherPriority,
                _ => MovementExecutionOutcome.Pending
            };
            return (outcome, val.Vel2D, val.Disp2D, val.Details);
        }
        return null;
    }

    public (PhysicalExecutionOutcome Physical, StateIntegrityOutcome Integrity, float Vel2D, float Disp2D, string Details)? GetLatestDetailedOutcome(int botSlot)
    {
        return _latestOutcomesBySlot.TryGetValue(botSlot, out var val) ? val : null;
    }

    public TrackedOutcomeMetadata? GetLatestDetailedMetadata(int botSlot)
    {
        return _latestDetailedOutcomesBySlot.TryGetValue(botSlot, out var meta) ? meta : null;
    }

    public MovementExecutionSample? GetActiveSample(int slot)
    {
        return _activeSampleBySlot.TryGetValue(slot, out var sample) ? sample : null;
    }
}
