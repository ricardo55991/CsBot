using System.Diagnostics;
using CounterStrikeSharp.API.Modules.Entities.Constants;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public enum MatchLifecyclePhase
{
    WARMUP,
    LIVE,
    RESTART_PENDING,
    MATCH_ENDED,
    MAP_CHANGE,
    PLUGIN_SHUTDOWN
}

public enum RoundLifecyclePhase
{
    NONE,
    FREEZE_TIME,
    ROUND_ACTIVE,
    ROUND_ENDED,
    POST_ROUND
}

public enum LateEventReason
{
    NONE,
    CALLBACK_DELAY,
    ASYNC_COMPLETION,
    QUEUE_BACKLOG,
    TICK_AFTER_SEAL,
    UNKNOWN_ROUND,
    LOGGER_FLUSH_DELAY
}

public enum CaptureEndReason
{
    MATCH_COMPLETED,
    MANUAL_STOP,
    PLUGIN_UNLOAD,
    SERVER_SHUTDOWN,
    MAP_CHANGE,
    PROCESS_CRASH_RECOVERY,
    IO_FAILURE,
    UNKNOWN
}

public sealed class RoundStateRecord
{
    public int InternalRoundId { get; init; }
    public int OfficialRoundNumber { get; set; }
    public int RoundNumberInHalf { get; set; }
    public MatchLifecyclePhase MatchPhase { get; set; }
    public RoundLifecyclePhase RoundPhase { get; set; }
    public int StartedAtTick { get; init; }
    public int EndedAtTick { get; set; }
    public bool RoundEndReceived { get; set; }
    public bool Sealed { get; set; }
    public int OfficialScoreBeforeCt { get; set; }
    public int OfficialScoreBeforeTr { get; set; }
    public int OfficialScoreAfterCt { get; set; }
    public int OfficialScoreAfterTr { get; set; }
    public CsTeam Winner { get; set; } = CsTeam.None;
    public int EndReasonCode { get; set; }
    public string EndReasonEnum { get; set; } = "NONE";
    public string EndReasonDescription { get; set; } = "Em andamento";
}

public sealed class EventAdmissionEnvelope
{
    public int RoundId { get; init; }
    public int OfficialRoundNumber { get; init; }
    public int CurrentActiveRoundId { get; init; }
    public int GameTick { get; init; }
    public int? OriginalGameTick { get; init; }
    public long MonotonicTimestampMs { get; init; }
    public long EventSequence { get; init; }
    public string RoundTimeFormatted { get; init; } = "00:00";
    public RoundLifecyclePhase EventPhase { get; init; }
    public bool LateEvent { get; init; }
    public LateEventReason LateReason { get; init; }
    public string SourceComponent { get; init; } = "Core";
    public string Disposition { get; init; } = "NORMAL"; // NORMAL, AUDITED_LATE, DISCARDED_DUPLICATE
}

public sealed class RoundLifecycleManager
{
    private readonly object _lock = new();
    private readonly Stopwatch _monotonicClock = Stopwatch.StartNew();
    private long _eventSequence = 0;
    private int _internalRoundCounter = 0;
    private int _officialRoundCounter = 0;
    private int _lastRoundStartTick = -1;
    private int _lastRoundEndTick = -1;
    private int _lateEventCount = 0;
    private int _pendingEventCount = 0;

    public MatchLifecyclePhase CurrentMatchPhase { get; private set; } = MatchLifecyclePhase.WARMUP;
    public RoundStateRecord? CurrentRound { get; private set; }
    public List<RoundStateRecord> RoundHistory { get; } = new();

    public int LateEventCount => Interlocked.CompareExchange(ref _lateEventCount, 0, 0);
    public int PendingEventCount => Interlocked.CompareExchange(ref _pendingEventCount, 0, 0);
    public long CurrentEventSequence => Interlocked.Read(ref _eventSequence);
    public long ElapsedMonotonicMs => _monotonicClock.ElapsedMilliseconds;

    public bool IsRoundActiveAndUnsealed
    {
        get
        {
            lock (_lock)
            {
                return CurrentRound != null
                    && !CurrentRound.Sealed
                    && (CurrentRound.RoundPhase == RoundLifecyclePhase.FREEZE_TIME || CurrentRound.RoundPhase == RoundLifecyclePhase.ROUND_ACTIVE);
            }
        }
    }

    public bool IsMovementAllowed
    {
        get
        {
            lock (_lock)
            {
                return CurrentRound != null
                    && !CurrentRound.Sealed
                    && CurrentRound.RoundPhase == RoundLifecyclePhase.ROUND_ACTIVE
                    && (CurrentMatchPhase == MatchLifecyclePhase.LIVE || CurrentMatchPhase == MatchLifecyclePhase.WARMUP);
            }
        }
    }

    public void ResetForMapChange(int gameTick)
    {
        lock (_lock)
        {
            if (CurrentRound != null && !CurrentRound.Sealed)
            {
                CurrentRound.Sealed = true;
                CurrentRound.EndedAtTick = gameTick;
                CurrentRound.RoundPhase = RoundLifecyclePhase.POST_ROUND;
                CurrentRound.EndReasonEnum = "MAP_CHANGE";
                CurrentRound.EndReasonDescription = "Encerrado por mudança de mapa";
            }
            CurrentMatchPhase = MatchLifecyclePhase.MAP_CHANGE;
            _officialRoundCounter = 0;
            _lastRoundStartTick = -1;
            _lastRoundEndTick = -1;
        }
    }

    public void NotifyMatchRestartPending(int gameTick)
    {
        lock (_lock)
        {
            if (CurrentRound != null && !CurrentRound.Sealed)
            {
                CurrentRound.Sealed = true;
                CurrentRound.RoundEndReceived = true;
                CurrentRound.EndedAtTick = gameTick;
                CurrentRound.RoundPhase = RoundLifecyclePhase.POST_ROUND;
                CurrentRound.EndReasonCode = 16;
                CurrentRound.EndReasonEnum = "GameCommencing";
                CurrentRound.EndReasonDescription = "Reinício oficial da partida / fim do warmup";
            }
            CurrentMatchPhase = MatchLifecyclePhase.RESTART_PENDING;
            _officialRoundCounter = 0;
        }
    }

    public void NotifyPluginShutdown(int gameTick)
    {
        lock (_lock)
        {
            if (CurrentRound != null && !CurrentRound.Sealed)
            {
                CurrentRound.Sealed = true;
                CurrentRound.EndedAtTick = gameTick;
                CurrentRound.RoundPhase = RoundLifecyclePhase.POST_ROUND;
                CurrentRound.EndReasonEnum = "PLUGIN_SHUTDOWN";
                CurrentRound.EndReasonDescription = "Plugin descarregado durante round ativo";
            }
            CurrentMatchPhase = MatchLifecyclePhase.PLUGIN_SHUTDOWN;
        }
    }

    /// <summary>
    /// Inicia um novo round com guarda estrita de idempotência.
    /// Retorna false se for um callback duplicado de RoundStart para o mesmo ciclo.
    /// </summary>
    public bool TryBeginRound(
        bool isWarmup,
        int gameTick,
        int currentCtScore,
        int currentTrScore,
        out RoundStateRecord roundRecord,
        out RoundStateRecord? autoSealedPreviousRound)
    {
        autoSealedPreviousRound = null;
        lock (_lock)
        {
            // Guarda de idempotência contra callback duplicado no mesmo tick ou já em FreezeTime sem término anterior
            if (CurrentRound != null &&
                !CurrentRound.RoundEndReceived &&
                !CurrentRound.Sealed &&
                CurrentRound.RoundPhase == RoundLifecyclePhase.FREEZE_TIME &&
                (gameTick == _lastRoundStartTick || Math.Abs(gameTick - _lastRoundStartTick) <= 2) &&
                (CurrentRound.MatchPhase == (isWarmup ? MatchLifecyclePhase.WARMUP : MatchLifecyclePhase.LIVE)))
            {
                roundRecord = CurrentRound;
                return false;
            }

            // Se havia um round anterior (ex: Warmup ou Restart) que não recebeu EventRoundEnd, sela-o antes de abrir o novo
            if (CurrentRound != null && !CurrentRound.Sealed)
            {
                CurrentRound.Sealed = true;
                CurrentRound.RoundEndReceived = true;
                CurrentRound.EndedAtTick = gameTick;
                CurrentRound.RoundPhase = RoundLifecyclePhase.POST_ROUND;
                CurrentRound.OfficialScoreAfterCt = currentCtScore;
                CurrentRound.OfficialScoreAfterTr = currentTrScore;
                if (CurrentRound.MatchPhase == MatchLifecyclePhase.WARMUP && !isWarmup)
                {
                    CurrentRound.EndReasonCode = 16;
                    CurrentRound.EndReasonEnum = "GameCommencing";
                    CurrentRound.EndReasonDescription = "Transição de Warmup para Partida Oficial (Live)";
                }
                else
                {
                    CurrentRound.EndReasonCode = 10;
                    CurrentRound.EndReasonEnum = "RoundRestartOrDraw";
                    CurrentRound.EndReasonDescription = "Fechamento automático por início de novo round / restart";
                }
                autoSealedPreviousRound = CurrentRound;
            }

            _lastRoundStartTick = gameTick;
            _internalRoundCounter++;

            if (isWarmup)
            {
                CurrentMatchPhase = MatchLifecyclePhase.WARMUP;
                roundRecord = new RoundStateRecord
                {
                    InternalRoundId = _internalRoundCounter,
                    OfficialRoundNumber = 0,
                    RoundNumberInHalf = 0,
                    MatchPhase = MatchLifecyclePhase.WARMUP,
                    RoundPhase = RoundLifecyclePhase.ROUND_ACTIVE,
                    StartedAtTick = gameTick,
                    OfficialScoreBeforeCt = currentCtScore,
                    OfficialScoreBeforeTr = currentTrScore,
                    OfficialScoreAfterCt = currentCtScore,
                    OfficialScoreAfterTr = currentTrScore
                };
            }
            else
            {
                // Se o placar voltou a 0x0 (início da partida após warmup ou mp_restartgame), garante OfficialRoundNumber = 1
                if (currentCtScore == 0 && currentTrScore == 0)
                {
                    _officialRoundCounter = 1;
                }
                else
                {
                    _officialRoundCounter = Math.Max(_officialRoundCounter + 1, currentCtScore + currentTrScore + 1);
                }

                CurrentMatchPhase = MatchLifecyclePhase.LIVE;
                int roundInHalf = ((_officialRoundCounter - 1) % 12) + 1;

                roundRecord = new RoundStateRecord
                {
                    InternalRoundId = _internalRoundCounter,
                    OfficialRoundNumber = _officialRoundCounter,
                    RoundNumberInHalf = roundInHalf,
                    MatchPhase = MatchLifecyclePhase.LIVE,
                    RoundPhase = RoundLifecyclePhase.FREEZE_TIME,
                    StartedAtTick = gameTick,
                    OfficialScoreBeforeCt = currentCtScore,
                    OfficialScoreBeforeTr = currentTrScore,
                    OfficialScoreAfterCt = currentCtScore,
                    OfficialScoreAfterTr = currentTrScore
                };
            }

            CurrentRound = roundRecord;
            RoundHistory.Add(roundRecord);
            return true;
        }
    }

    public bool TryTransitionToActivePhase(int gameTick)
    {
        lock (_lock)
        {
            if (CurrentRound == null || CurrentRound.Sealed)
                return false;

            if (CurrentRound.RoundPhase == RoundLifecyclePhase.ROUND_ACTIVE)
                return false;

            CurrentRound.RoundPhase = RoundLifecyclePhase.ROUND_ACTIVE;
            return true;
        }
    }

    /// <summary>
    /// Sela o round atual no recebimento de EventRoundEnd.
    /// Estritamente idempotente: nunca emite dois FIM_ROUND, nunca altera placar duas vezes e nunca reabre round selado.
    /// </summary>
    public bool TrySealRound(
        int reasonCode,
        CsTeam winner,
        int gameTick,
        ref int ctScore,
        ref int trScore,
        ref int ctLossStreak,
        ref int trLossStreak,
        out RoundStateRecord? sealedRecord)
    {
        lock (_lock)
        {
            // Se for GameCommencing (16) disparado no fim do Warmup, marca transição sem somar placar
            if (reasonCode == 16 || (CurrentRound != null && CurrentRound.MatchPhase == MatchLifecyclePhase.WARMUP))
            {
                if (CurrentRound != null && !CurrentRound.Sealed)
                {
                    var (code, enumName, desc) = TranslateRoundEndReason(reasonCode);
                    CurrentRound.RoundEndReceived = true;
                    CurrentRound.Sealed = true;
                    CurrentRound.EndedAtTick = gameTick;
                    CurrentRound.RoundPhase = RoundLifecyclePhase.POST_ROUND;
                    CurrentRound.Winner = winner;
                    CurrentRound.EndReasonCode = code;
                    CurrentRound.EndReasonEnum = enumName;
                    CurrentRound.EndReasonDescription = desc;
                    CurrentRound.OfficialScoreAfterCt = ctScore;
                    CurrentRound.OfficialScoreAfterTr = trScore;
                    sealedRecord = CurrentRound;
                    _lastRoundEndTick = gameTick;
                    if (reasonCode == 16)
                    {
                        CurrentMatchPhase = MatchLifecyclePhase.RESTART_PENDING;
                        _officialRoundCounter = 0;
                    }
                    return true;
                }
                sealedRecord = CurrentRound;
                return false;
            }

            // Idempotência: se não há round, ou já está selado, ou já recebeu RoundEnd, rejeita!
            if (CurrentRound == null || CurrentRound.Sealed || CurrentRound.RoundEndReceived || gameTick == _lastRoundEndTick)
            {
                sealedRecord = CurrentRound;
                return false;
            }

            _lastRoundEndTick = gameTick;
            CurrentRound.OfficialScoreBeforeCt = ctScore;
            CurrentRound.OfficialScoreBeforeTr = trScore;

            if (winner == CsTeam.CounterTerrorist)
            {
                ctScore++;
                ctLossStreak = Math.Max(1, ctLossStreak - 1);
                trLossStreak = Math.Min(5, trLossStreak + 1);
            }
            else if (winner == CsTeam.Terrorist)
            {
                trScore++;
                trLossStreak = Math.Max(1, trLossStreak - 1);
                ctLossStreak = Math.Min(5, ctLossStreak + 1);
            }

            var (rCode, rEnum, rDesc) = TranslateRoundEndReason(reasonCode);
            CurrentRound.Winner = winner;
            CurrentRound.EndReasonCode = rCode;
            CurrentRound.EndReasonEnum = rEnum;
            CurrentRound.EndReasonDescription = rDesc;
            CurrentRound.OfficialScoreAfterCt = ctScore;
            CurrentRound.OfficialScoreAfterTr = trScore;
            CurrentRound.EndedAtTick = gameTick;
            CurrentRound.RoundEndReceived = true;
            CurrentRound.Sealed = true;
            CurrentRound.RoundPhase = RoundLifecyclePhase.POST_ROUND;

            sealedRecord = CurrentRound;
            return true;
        }
    }

    public EventAdmissionEnvelope CreateEventEnvelope(
        int gameTick,
        string roundTimeFormatted,
        string sourceComponent,
        int? originatingRoundId = null,
        int? originatingGameTick = null,
        LateEventReason suggestedLateReason = LateEventReason.TICK_AFTER_SEAL)
    {
        long seq = Interlocked.Increment(ref _eventSequence);
        long monoMs = _monotonicClock.ElapsedMilliseconds;

        lock (_lock)
        {
            if (CurrentRound == null)
            {
                Interlocked.Increment(ref _lateEventCount);
                return new EventAdmissionEnvelope
                {
                    RoundId = originatingRoundId ?? 0,
                    OfficialRoundNumber = 0,
                    CurrentActiveRoundId = 0,
                    GameTick = gameTick,
                    OriginalGameTick = originatingGameTick,
                    MonotonicTimestampMs = monoMs,
                    EventSequence = seq,
                    RoundTimeFormatted = roundTimeFormatted,
                    EventPhase = RoundLifecyclePhase.NONE,
                    LateEvent = true,
                    LateReason = LateEventReason.UNKNOWN_ROUND,
                    SourceComponent = sourceComponent,
                    Disposition = "AUDITED_LATE"
                };
            }

            bool isFromOlderRound = originatingRoundId.HasValue && originatingRoundId.Value != CurrentRound.InternalRoundId;
            bool isAfterSeal = CurrentRound.Sealed || CurrentRound.RoundPhase == RoundLifecyclePhase.POST_ROUND || CurrentRound.RoundPhase == RoundLifecyclePhase.ROUND_ENDED;

            if (isFromOlderRound || isAfterSeal)
            {
                Interlocked.Increment(ref _lateEventCount);
                LateEventReason reason = isFromOlderRound
                    ? (suggestedLateReason != LateEventReason.TICK_AFTER_SEAL ? suggestedLateReason : LateEventReason.ASYNC_COMPLETION)
                    : suggestedLateReason;

                return new EventAdmissionEnvelope
                {
                    RoundId = originatingRoundId ?? CurrentRound.InternalRoundId,
                    OfficialRoundNumber = CurrentRound.OfficialRoundNumber,
                    CurrentActiveRoundId = CurrentRound.InternalRoundId,
                    GameTick = gameTick,
                    OriginalGameTick = originatingGameTick ?? gameTick,
                    MonotonicTimestampMs = monoMs,
                    EventSequence = seq,
                    RoundTimeFormatted = roundTimeFormatted,
                    EventPhase = CurrentRound.RoundPhase,
                    LateEvent = true,
                    LateReason = reason,
                    SourceComponent = sourceComponent,
                    Disposition = "AUDITED_LATE"
                };
            }

            return new EventAdmissionEnvelope
            {
                RoundId = CurrentRound.InternalRoundId,
                OfficialRoundNumber = CurrentRound.OfficialRoundNumber,
                CurrentActiveRoundId = CurrentRound.InternalRoundId,
                GameTick = gameTick,
                OriginalGameTick = originatingGameTick ?? gameTick,
                MonotonicTimestampMs = monoMs,
                EventSequence = seq,
                RoundTimeFormatted = roundTimeFormatted,
                EventPhase = CurrentRound.RoundPhase,
                LateEvent = false,
                LateReason = LateEventReason.NONE,
                SourceComponent = sourceComponent,
                Disposition = "NORMAL"
            };
        }
    }

    public static (int Code, string EnumName, string Description) TranslateRoundEndReason(int code)
    {
        string? apiEnumName = null;
        try
        {
            if (Enum.IsDefined(typeof(RoundEndReason), (RoundEndReason)code))
            {
                apiEnumName = ((RoundEndReason)code).ToString();
            }
        }
        catch
        {
            // Fallback para tabela determinística se o runtime não carregar o enum nativo em ambiente de teste isolado
        }

        return code switch
        {
            1 => (1, apiEnumName ?? "TargetBombed", "C4 detonada com sucesso (Alvo destruído pelos Terroristas)"),
            2 => (2, apiEnumName ?? "VIPEscaped", "VIP escapou"),
            3 => (3, apiEnumName ?? "VIPAssassinated", "VIP eliminado"),
            4 => (4, apiEnumName ?? "TerroristsEscaped", "Terroristas escaparam"),
            5 => (5, apiEnumName ?? "CTsPreventEscape", "Contraterroristas impediram a fuga"),
            6 => (6, apiEnumName ?? "EscapingTerroristsNeutralized", "Terroristas em fuga neutralizados"),
            7 => (7, apiEnumName ?? "BombDefused", "C4 desarmada pelos Contraterroristas"),
            8 => (8, apiEnumName ?? "CTsWin", "Eliminação total dos Terroristas pelos Contraterroristas"),
            9 => (9, apiEnumName ?? "TerroristsWin", "Eliminação total dos Contraterroristas pelos Terroristas"),
            10 => (10, apiEnumName ?? "RoundDraw", "Round empatado / reiniciado"),
            11 => (11, apiEnumName ?? "HostagesRescued", "Todos os reféns foram resgatados"),
            12 => (12, apiEnumName ?? "TargetSaved", "Tempo do round esgotado (Bombsite salvo pelos Contraterroristas)"),
            13 => (13, apiEnumName ?? "HostagesNotRescued", "Reféns não foram resgatados a tempo"),
            14 => (14, apiEnumName ?? "TerroristsNotEscaped", "Terroristas não escaparam"),
            15 => (15, apiEnumName ?? "VIPNotEscaped", "VIP não escapou"),
            16 => (16, apiEnumName ?? "GameCommencing", "Início da partida oficial (Fim do Warmup)"),
            17 => (17, apiEnumName ?? "TerroristsSurrender", "Rendição dos Terroristas"),
            18 => (18, apiEnumName ?? "CTsSurrender", "Rendição dos Contraterroristas"),
            19 => (19, apiEnumName ?? "TerroristsPlanted", "Terroristas plantaram a C4"),
            20 => (20, apiEnumName ?? "CTsReachedHostage", "Contraterroristas alcançaram o refém"),
            _ => (code, apiEnumName ?? $"UNKNOWN_{code}", $"Motivo não mapeado (UNKNOWN_{code})")
        };
    }
}
