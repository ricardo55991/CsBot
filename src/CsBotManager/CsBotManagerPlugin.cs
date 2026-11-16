using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Modules.Commands;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

using CsTimer = CounterStrikeSharp.API.Modules.Timers.Timer;

namespace CsBotManager;

internal sealed record CanaryCandidate(
    CCSPlayerController Bot,
    TacticalSpot Spot,
    string PseudoSlot,
    string Team,
    string Role,
    float X,
    float Y,
    float Z,
    bool HasC4,
    string PlanSite,
    string Corridor,
    float AnchorDist);

[MinimumApiVersion(300)]
public class CsBotManagerPlugin : BasePlugin
{
    public override string ModuleName => "CsBotManager";
    public override string ModuleVersion => "1.3.0";
    public override string ModuleAuthor => "CsBot AI Team";

    private readonly EconomyManager _economyManager = new();
    private readonly RoleManager _roleManager = new();
    private readonly OllamaIglService _iglService = new();
    private readonly MapProfileManager _mapProfileManager = new();
    private readonly TacticalProbabilityEngine _probabilityEngine = new();
    private readonly BotLocomotionDriver _locomotionDriver = new();

    private PacingAndFallbackController? _pacingController;
    private CtDefenseController? _ctController;
    private MidRoundAdapter? _midRoundAdapter;
    private PlayerIntentTracker? _intentTracker;
    private VoiceCommandBridge? _voiceBridge;
    private UtilityAndClockCoordinator? _utilityCoordinator;
    private TacticalCalloutSystem? _calloutSystem;
    private ContextualSmokeAndAudioBrain? _smokeAudioBrain;
    private SiteClearAndPlantController? _clearAndPlantController;
    private CtRetakeAndDefuseBrain? _retakeAndDefuseBrain;
    private MatchTelemetryLogger? _telemetryLogger;
    private TrMacroPivotController? _trPivotController;
    private MobilityController? _mobilityController;
    private CombatAdapter? _combatAdapter;
    private MicroMoveEngine? _microMoveEngine;
    private SpotTestRunner? _spotTestRunner;
    private GameplaySpotTelemetryTracker? _spotTelemetryTracker;
    private SpotRecordingController? _spotRecorder;
    private PositioningTransformerService? _positioningTransformerService;
    private PositioningShadowTelemetryLogger? _positioningShadowTelemetry;
    private readonly PositioningTemporalRingBuffer _positioningRingBuffer = new();
    private readonly OpeningRouteTracker _openingRouteTracker = new();
    private readonly OpeningRoutePlanner _openingRoutePlanner = new();
    private readonly OpeningRouteCanaryGuard _openingCanaryGuard = new();
    private readonly HashSet<string> _coveredCanaryCorridors = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<int, int> _lastCanaryEvalTickBySlot = new();
    private readonly Dictionary<(int RoundId, string Team), FullTeamDepartureSchedule> _fullTeamScheduleByRound = new();
    private readonly Dictionary<(int RoundId, string Team, string Group), CorridorDepartureQueue> _corridorQueuesByRound = new();
    private readonly Dictionary<(int RoundId, string Team, int BotSlot), PassiveDepartureHold> _passiveDepartureHolds = new();
    private readonly Dictionary<(int RoundId, string Team, int BotSlot), (CanaryCandidate Cand, FullTeamDepartureAssignment Assign)> _pendingCanaryFollowers = new();
    private readonly List<object> _departureTraceEvents = new();
    private double _positioningRoundStartTime = 0.0;
    private readonly string _positioningMatchId = $"mirage_shadow_{DateTimeOffset.UtcNow:yyyyMMdd_HHmmss}";
    private long _positioningShadowSequenceId;

    private TacticalPlan _currentPlan = new();

    private TacticalPlan _currentTrPlan = new();
    private TacticalPlan _currentCtPlan = new();

    // V4: ciclo de vida idempotente de rounds e captura limitada por rounds
    private readonly RoundLifecycleManager _lifecycle = new();
    private int _debugTargetRounds = 0;
    private int _debugRoundsSealed = 0;
    private bool _debugCaptureAdmissionClosed = false;
    private int _debugLastAdmittedRoundId = int.MaxValue;
    private bool _matchCompletedFlagWritten = false;

    private readonly HashSet<(int RoundId, string Team)> _createdTeamSchedules = new();
    private readonly HashSet<string> _scheduledAssignments = new(StringComparer.OrdinalIgnoreCase);
    public int DuplicateTeamScheduleAttempts { get; private set; }
    public int DuplicateScheduledAttempts { get; private set; }

    private static string NormalizeAssignmentTeam(string? team)
    {
        string t = (team ?? string.Empty).Trim().ToUpperInvariant();
        if (t == "T" || t == "TR") return "TR";
        if (t == "CT") return "CT";
        return t;
    }

    private bool HasCreatedTeamSchedule(int roundId, string team)
    {
        string norm = NormalizeAssignmentTeam(team);
        if (norm != "CT" && norm != "TR") return false;
        return _createdTeamSchedules.Contains((roundId, norm));
    }

    private bool TryMarkTeamScheduleCreated(int roundId, string team)
    {
        string norm = NormalizeAssignmentTeam(team);
        if (norm != "CT" && norm != "TR") return false;
        return _createdTeamSchedules.Add((roundId, norm));
    }

    private static bool IsEngineWarmup()
    {
        try
        {
            var rules = Utilities.FindAllEntitiesByDesignerName<CCSGameRulesProxy>("cs_gamerules").FirstOrDefault()?.GameRules;
            return rules?.WarmupPeriod ?? false;
        }
        catch { return false; }
    }

    /// <summary>Verifica admissão do evento no round atual. Eventos atrasados vão para a auditoria separada.</summary>
    private bool AdmitEvent(string eventName, string details)
    {
        var env = _lifecycle.CreateEventEnvelope(Server.TickCount, _telemetryLogger?.GetRoundClockFormatted() ?? "00:00", eventName);
        if (env.LateEvent)
        {
            _telemetryLogger?.LogLateEvent(env, eventName, details);
            return false;
        }
        return true;
    }

    public bool IsSpotTestActive => _spotTestRunner != null && _spotTestRunner.IsActive;

    public TrMacroPivotController? TrPivotController => _trPivotController;
    public PacingAndFallbackController? PacingController => _pacingController;
    public BotLocomotionDriver LocomotionDriver => _locomotionDriver;
    public RoleManager RoleManager => _roleManager;
    public RoundLifecycleManager LifecycleManager => _lifecycle;

    public TacticalPlan CurrentPlan => _currentPlan;
    public TacticalPlan? CurrentTrPlan => _currentTrPlan ?? _currentPlan;
    public TacticalPlan? CurrentCtPlan => _currentCtPlan ?? _currentPlan;
    public SiteClearAndPlantController? SiteClearController => _clearAndPlantController;
    internal bool IsBombPlantedState => _isBombPlanted;
    internal bool IsFreezeTimeState => _isFreezeTime;
    private int _currentRound = 0;
    private int _ctScore = 0;
    private int _trScore = 0;
    private bool _isFreezeTime = false;
    private bool _isBombPlanted = false;
    private bool _isGameManuallyPaused = false;
    private bool _isHudEnabled = false;
    private LiveRadarTelemetryService? _radarTelemetryService;
    private float _roundFreezeEndTime = 0.0f;
    private CsTimer? _hudTimer;
    private CsTimer? _buyTimer;
    private CsTimer? _clockTimer;

    // Rastreamento de Loss Streaks reais (I-04E)
    private int _ctLossStreak = 1;
    private int _trLossStreak = 1;
    private string _firstCtDeathSectorInRound = "None";

    // Sequenciamento de requisições Ollama e timers seguros por round (F-001, F-002, F-003, F-006)
    private int _iglRequestSequence = 0;
    private CancellationTokenSource? _roundCts;
    private readonly List<CounterStrikeSharp.API.Modules.Timers.Timer> _activeRoundTimers = new();

    // Cache de renderização HTML da HUD a 1Hz (O-01)
    private string _cachedHudHtml = string.Empty;
    private int _cachedHumanSlot = -1;
    private readonly Dictionary<int, float> _lastHurtThreatAlertTime = new();

    public int GetLossBonus(int streak) => Math.Clamp(1400 + (streak - 1) * 500, 1400, 3400);

    public CounterStrikeSharp.API.Modules.Timers.Timer AddRoundTimer(float delay, Action callback, TimerFlags flags = 0)
    {
        CounterStrikeSharp.API.Modules.Timers.Timer? timer = null;
        timer = AddTimer(delay, () =>
        {
            if (timer != null && (flags & TimerFlags.REPEAT) == 0)
            {
                lock (_activeRoundTimers)
                {
                    _activeRoundTimers.Remove(timer);
                }
            }
            callback();
        }, flags);

        lock (_activeRoundTimers)
        {
            _activeRoundTimers.Add(timer);
        }
        return timer;
    }

    public void ClearRoundTimers()
    {
        lock (_activeRoundTimers)
        {
            foreach (var t in _activeRoundTimers)
            {
                try
                {
                    t.Kill();
                }
                catch { }
            }
            _activeRoundTimers.Clear();
        }
    }

    private string _runId = string.Empty;
    private string _pluginInstanceId = string.Empty;
    private int _processId;
    private string _dllSha256 = string.Empty;
    private string _runStartedUtc = string.Empty;

    public override void Load(bool hotReload)
    {
        base.Load(hotReload);
        _processId = Environment.ProcessId;
        _pluginInstanceId = Guid.NewGuid().ToString("N")[..8];
        _runStartedUtc = DateTime.UtcNow.ToString("O");
        _runId = $"{DateTime.UtcNow:yyyyMMddTHHmmssZ}_pid{_processId}_{_pluginInstanceId[..4]}";
        try
        {
            string dllPath = Path.Combine(ModuleDirectory, "CsBotManager.dll");
            if (File.Exists(dllPath))
            {
                using var sha = System.Security.Cryptography.SHA256.Create();
                _dllSha256 = Convert.ToHexString(sha.ComputeHash(File.ReadAllBytes(dllPath))).ToLowerInvariant();
            }
        }
        catch { }
        EmitRunMarker("RUN_STARTED", cleanShutdown: false);
        _openingCanaryGuard.OnSessionTerminal = (session, reason, termTick) =>
            FinalizeAssignmentFromSession(session, reason, termTick);

        _mapProfileManager.LoadProfile(Server.MapName, ModuleDirectory);
        // Bloco 1: MicroMoveEngine e carregado apos sua instanciacao completa abaixo

        _pacingController = new PacingAndFallbackController(this, _mapProfileManager, _roleManager, _locomotionDriver);
        _ctController = new CtDefenseController(this, _mapProfileManager, _roleManager, _locomotionDriver);
        _midRoundAdapter = new MidRoundAdapter(this, _mapProfileManager, _roleManager, _ctController, _locomotionDriver);
        _intentTracker = new PlayerIntentTracker(this, _roleManager, _mapProfileManager);
        _utilityCoordinator = new UtilityAndClockCoordinator(this, _mapProfileManager, _roleManager);
        _calloutSystem = new TacticalCalloutSystem(this, _mapProfileManager, _roleManager);
        _smokeAudioBrain = new ContextualSmokeAndAudioBrain(this, _mapProfileManager, _roleManager, _locomotionDriver, _ctController, _calloutSystem);
        _clearAndPlantController = new SiteClearAndPlantController(this, _mapProfileManager, _roleManager, _locomotionDriver);
        _retakeAndDefuseBrain = new CtRetakeAndDefuseBrain(this, _mapProfileManager, _roleManager, _locomotionDriver);
        _telemetryLogger = new MatchTelemetryLogger(this, _mapProfileManager, _roleManager, _locomotionDriver);
        _trPivotController = new TrMacroPivotController(this, _mapProfileManager, _roleManager, _midRoundAdapter, _pacingController, _locomotionDriver);
        _trPivotController.TelemetryLogger = _telemetryLogger;
        _pacingController.OnExecuteStarted = plan => _trPivotController?.OnExecuteStarted(plan);

        _mobilityController = new MobilityController(this, _mapProfileManager, _locomotionDriver);
        _combatAdapter = new CombatAdapter(this, _locomotionDriver, _midRoundAdapter);
        _spotTestRunner = new SpotTestRunner(this, _mapProfileManager, _locomotionDriver);
        _spotTelemetryTracker = new GameplaySpotTelemetryTracker(this);
        _locomotionDriver.SpotTelemetryTracker = _spotTelemetryTracker;
        _microMoveEngine = new MicroMoveEngine(_mapProfileManager, _roleManager)
        {
            TelemetryLogger = _telemetryLogger, CalloutSystem = _calloutSystem, Plugin = this
        };
        _iglService.TelemetryLogger = _telemetryLogger;
        _microMoveEngine.TryLoadMapModel(Server.MapName);
        InitializePositioningShadowMode(Server.MapName);

        _locomotionDriver.PlantController = _clearAndPlantController;
        _locomotionDriver.RetakeBrain = _retakeAndDefuseBrain;
        _locomotionDriver.MicroMoveEngine = _microMoveEngine;
        _locomotionDriver.LeaseManager = _openingCanaryGuard.LeaseManager;
        _locomotionDriver.Arbitrator.LeaseManager = _openingCanaryGuard.LeaseManager;
        _locomotionDriver.GetCurrentRoundId = () => Math.Max(1, _ctScore + _trScore + 1);
        _locomotionDriver.IsOpeningCanaryActiveSlot = slot => !_isFreezeTime && _openingCanaryGuard.IsSlotActiveCanary(Math.Max(1, _ctScore + _trScore + 1), slot);
        _locomotionDriver.SetPlugin(this);

        RegisterListener<Listeners.OnMapStart>(mapName =>
        {
            _mapProfileManager.LoadProfile(mapName, ModuleDirectory);
            _microMoveEngine?.TryLoadMapModel(mapName);
            _positioningRingBuffer.ResetAll("MAP_CHANGE");
            InitializePositioningShadowMode(mapName);
            Server.PrintToConsole("================================================================================");
            Server.PrintToConsole($" [CsBot] Mapa '{mapName}' pronto para conexao!");
            Server.PrintToConsole(" [CsBot] >>> NO CONSOLE DO CS2 DIGITE: connect 127.0.0.1:27016 <<<");
            Server.PrintToConsole("================================================================================");
        });
        _locomotionDriver.UtilityCoordinator = _utilityCoordinator;
        _locomotionDriver.MapProfileManager = _mapProfileManager;
        if (_utilityCoordinator != null)
        {
            _utilityCoordinator.LocomotionDriver = _locomotionDriver;
        }
        _clearAndPlantController.CalloutSystem = _calloutSystem;
        _combatAdapter.CalloutSystem = _calloutSystem;
        _combatAdapter.MapProfileManager = _mapProfileManager;

        _voiceBridge = new VoiceCommandBridge(
            this,
            _economyManager,
            _roleManager,
            _iglService,
            _mapProfileManager,
            _pacingController,
            _ctController,
            _midRoundAdapter,
            _locomotionDriver,
            () => _currentPlan);
        _voiceBridge.TelemetryLogger = _telemetryLogger;
        _radarTelemetryService = new LiveRadarTelemetryService(
            _mapProfileManager,
            _roleManager,
            _economyManager,
            _pacingController,
            () => _currentPlan,
            _voiceBridge);
        _voiceBridge.RadarTelemetry = _radarTelemetryService;
        _voiceBridge.Start();

        _spotRecorder = new SpotRecordingController(this, ModuleDirectory);
        RegisterEventHandler<EventPlayerSpawn>(OnPlayerSpawn);
        AddCommandListener("say", OnPlayerSay);
        AddCommandListener("say_team", OnPlayerSay);

        RegisterEventHandler<EventRoundStart>(OnRoundStart);
        RegisterEventHandler<EventRoundFreezeEnd>(OnRoundFreezeEnd);
        RegisterEventHandler<EventRoundEnd>(OnRoundEnd);
        RegisterEventHandler<EventPlayerHurt>(OnPlayerHurt);
        RegisterEventHandler<EventPlayerDeath>(OnPlayerDeath);
        RegisterEventHandler<EventPlayerFootstep>(OnPlayerFootstep);
        RegisterEventHandler<EventWeaponFire>(OnWeaponFire);
        RegisterEventHandler<EventBombPlanted>(OnBombPlanted);
        RegisterEventHandler<EventBombBegindefuse>(OnBombBeginDefuse);
        RegisterEventHandler<EventSmokegrenadeDetonate>(OnSmokeGrenadeDetonate);

        RegisterListener<Listeners.OnTick>(OnTick);

        AddCommand("tatica", "Define uma call tatica para os bots", CommandTatica);
        AddCommand("rejeitar", "Pede uma tatica alternativa para a IA", CommandRejeitar);
        AddCommand("drop", "Pede arma para o bot mais rico", CommandDrop);
        AddCommand("pos", "Assume um setor e os bots cedem a posicao", CommandPos);
        AddCommand("executar", "Dispara o avanco imediato da equipe (cancela staging)", CommandExecutar);
        AddCommand("go", "Dispara o avanco imediato da equipe (alias !executar)", CommandExecutar);
        AddCommand("flash", "Pede pop-flash em dupla para o bot mais proximo", CommandFlash);
        AddCommand("miou", "Dispara rotacao silenciosa no shift para o outro bomb", CommandMiou);
        AddCommand("respawn", "Faz os bots jogarem de acordo com a proximidade do spawn", CommandRespawn);
        AddCommand("debug", "Liga ou desliga a telemetria forense da partida (!debug on/off)", CommandDebug);
        AddCommand("nota", "Registra uma nota do jogador no log de debug com snapshot instantâneo", CommandNota);
        AddCommand("pause", "Pausa o jogo completamente sem limite de tempo", CommandPause);
        AddCommand("pausar", "Pausa o jogo completamente sem limite de tempo", CommandPause);
        AddCommand("continue", "Retoma o jogo pausado", CommandContinue);
        AddCommand("unpause", "Retoma o jogo pausado", CommandContinue);
        AddCommand("despausar", "Retoma o jogo pausado", CommandContinue);
        AddCommand("retomar", "Retoma o jogo pausado", CommandContinue);
        AddCommand("hud", "Liga ou desliga o HUD central na tela (!hud on / !hud off)", CommandToggleHud);
        AddCommand("spottest", "Executa teste A/B de spots (!spottest <profileVersion> <spotId> <attempts>)", CommandSpotTest);

        Server.PrintToConsole("================================================================================");
        Server.PrintToConsole("[CsBotManager] Plugin Fase 4.1 inicializado com sucesso!");
        Server.PrintToConsole("[CsBotManager] >>> NO CONSOLE DO CS2 DIGITE: connect 127.0.0.1:27016 <<<");
        Server.PrintToConsole("================================================================================");
    }

    public override void Unload(bool hotReload)
    {
        _openingCanaryGuard.LeaseManager.OnPluginUnload(Server.TickCount, lease =>
        {
            var bot = Utilities.GetPlayerFromSlot(lease.BotSlot);
            NativeCcsBotLocomotionBridge.RestoreSnapshot(bot, bot?.PlayerPawn.Value?.Bot, lease.OriginalState);
        });
        _openingCanaryGuard.FinalizeAllOpenSessions("CAPTURE_ENDED", Server.TickCount);
        foreach (var pkv in _pendingCanaryFollowers.ToList())
        {
            var (cand, fa) = pkv.Value;
            string assignId = $"r{pkv.Key.RoundId}_{pkv.Key.Team}_s{cand.Bot.Slot}";
            if (_terminatedAssignments.Add($"{_runId}:{assignId}"))
            {
                EmitAssignmentLifecycleRecord(new OpeningAssignmentLifecycleRecord
                {
                    EventType = "OPENING_ASSIGNMENT_TERMINAL",
                    AssignmentId = assignId,
                    RoundId = pkv.Key.RoundId,
                    Team = pkv.Key.Team,
                    PlayerPseudonym = cand.PseudoSlot,
                    Destination = cand.Spot.Id,
                    RouteId = cand.Spot.Id,
                    RouteCertified = true,
                    RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
                    EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
                    LifecycleState = OpeningAssignmentLifecycleState.CANCELLED_BEFORE_CONTROL,
                    TerminalReason = "CAPTURE_ENDED",
                    PredecessorSlot = fa.PredecessorSlot,
                    QueueId = fa.QueueId,
                    ScheduledTick = Server.TickCount,
                    PlannedReleaseTick = fa.PlannedReleaseTick,
                    ExpirationTick = Server.TickCount,
                    TerminalTick = Server.TickCount,
                    ControllerCreated = false,
                    LeaseAcquired = false,
                    SessionId = string.Empty,
                });
            }
        }
        _corridorQueuesByRound.Clear();
        _passiveDepartureHolds.Clear();
        _pendingCanaryFollowers.Clear();
        _fullTeamScheduleByRound.Clear();
        _lastCanaryEvalTickBySlot.Clear();
        _voiceBridge?.Stop();
        _lifecycle.NotifyPluginShutdown(Server.TickCount);
        _telemetryLogger?.CloseCapture(CaptureEndReason.PLUGIN_UNLOAD, _lifecycle);
        EmitRunMarker("RUN_FINISHED", cleanShutdown: true);
        _createdTeamSchedules.Clear();
        _scheduledAssignments.Clear();
        _terminatedAssignments.Clear();
        _roundCts?.Cancel();
        _roundCts?.Dispose();
        _roundCts = null;
        ClearRoundTimers();
        _locomotionDriver.ResetRound();
        _microMoveEngine?.Dispose();
        _microMoveEngine = null;
        _positioningTransformerService?.Dispose();
        _positioningTransformerService = null;
        _positioningShadowTelemetry?.Dispose();
        _positioningShadowTelemetry = null;
        _lastHurtThreatAlertTime.Clear();
        base.Unload(hotReload);
    }

    private void OnTick()
    {
        if (_isGameManuallyPaused)
        {
            if (_cachedHumanSlot != -1)
            {
                var human = Utilities.GetPlayerFromSlot(_cachedHumanSlot);
                if (human != null && human.IsValid && !human.IsBot)
                {
                    human.PrintToCenterHtml("<font color='#FF4444' size='5'><b>[JOGO PAUSADO]</b></font><br><font color='#DDDDDD'>Digite <b>!continue</b> no chat para retomar</font>");
                }
            }
            return;
        }

        float currentTime = Server.CurrentTime;

        if (_spotTestRunner != null && !_spotTestRunner.IsActive && Server.TickCount % 64 == 0)
        {
            const string flagPath = @"H:\CS2_AI_Server\debug_logs\auto_spottest.flag";
            if (System.IO.File.Exists(flagPath))
            {
                var aliveBots = Utilities.GetPlayers().Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive).ToList();
                if (aliveBots.Count >= 2)
                {
                    try { System.IO.File.Delete(flagPath); } catch { }
                    _isFreezeTime = false;
                    _spotTestRunner.EnqueueSpotTests("all", "all", 3, ModuleDirectory, clearFile: true);
                }
                else
                {
                    Server.ExecuteCommand("bot_quota 10; mp_warmup_end; mp_freezetime 0;");
                }
            }
        }

        if (_spotTestRunner != null && _spotTestRunner.IsActive)
        {
            _locomotionDriver.Arbitrator.BeginTick(Server.TickCount, currentTime);
            _spotTestRunner.OnTick();
            _locomotionDriver?.UpdateTick(currentTime);
            return;
        }

        _locomotionDriver.Arbitrator.BeginTick(Server.TickCount, currentTime);

        bool isShadowSampleTick = (Server.TickCount % PositioningFeatureContract.CollectionTickInterval) == 0;
        if (!_isFreezeTime)
        {
            // Etapas 1 a 5 do Tick Order Contract: Coleta mundo, checa gatilhos de interrupção do Canary,
            // valida MovementAuthorityLease e publica intenção do Canary ANTES de writers concorrentes
            UpdateOpeningRouteControlAndShadowTick(runShadowSampling: isShadowSampleTick);

            // Etapa 4: Writers concorrentes avaliam apenas slots não-isolados (ou são suprimidos no slot com lease ativo)
            var aliveBots = Utilities.GetPlayers().Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive).ToList();
            foreach (var b in aliveBots)
            {
                _locomotionDriver?.CheckGrenadeEquipWatchdog(b, currentTime);
            }
            _mobilityController?.UpdateTick(currentTime, _currentPlan, aliveBots);
            _combatAdapter?.UpdateTick(currentTime, aliveBots);
        }

        // Etapas 6 e 7: Arbitragem e aplicação única à engine (incluindo NativeCcsBotLocomotionBridge no slot com lease)
        _locomotionDriver?.UpdateTick(currentTime);

        // Etapas 8 e 9: Verificação de goal_end_of_tick e telemetria por tick de autoridade
        if (!_isFreezeTime)
        {
            VerifyAndRecordCanaryEndOfTickAuthority();
        }

        if (isShadowSampleTick)
        {
            CollectPositioningFeatureFrame();
        }

        if (Server.TickCount % 16 == 0)
        {
            UpdatePositioningShadowObservation();
        }

        // Atualiza a telemetria do radar ao vivo (segunda tela) a cada 3 ticks (~21Hz)
        _radarTelemetryService?.UpdateTick(
            currentTime,
            Server.TickCount,
            Math.Max(1, _currentRound),
            _ctScore,
            _trScore,
            IsEngineWarmup(),
            _isFreezeTime,
            _isGameManuallyPaused);

        // O-01: Exibe o cache HTML na tela do jogo apenas se ativado manualmente (!hud on)
        if (_isHudEnabled && !string.IsNullOrEmpty(_cachedHudHtml) && _cachedHumanSlot != -1)
        {
            var human = Utilities.GetPlayerFromSlot(_cachedHumanSlot);
            if (human != null && human.IsValid && !human.IsBot)
            {
                human.PrintToCenterHtml(_cachedHudHtml);
            }
        }
    }

    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo info)
    {
        if (_spotTestRunner != null && _spotTestRunner.IsActive)
        {
            _isFreezeTime = false;
            return HookResult.Continue;
        }

        bool isWarmup = IsEngineWarmup();
        if (!_lifecycle.TryBeginRound(isWarmup, Server.TickCount, _ctScore, _trScore, out var roundRecord, out var autoSealed))
        {
            // Callback duplicado de RoundStart: idempotência V4
            return HookResult.Continue;
        }
        if (autoSealed != null)
        {
            _telemetryLogger?.LogRoundSealed(autoSealed);
        }
        if (!isWarmup && roundRecord.OfficialRoundNumber == 1)
        {
            _ctScore = 0;
            _trScore = 0;
        }

        string autoDebugFlag = @"H:\CS2_AI_Server\debug_logs\auto_debug.flag";
        if (!_debugCaptureAdmissionClosed && _debugTargetRounds == 0 && File.Exists(autoDebugFlag))
        {
            try
            {
                string content = File.ReadAllText(autoDebugFlag).Trim();
                if (int.TryParse(content, out int r) && r > 0)
                {
                    _debugTargetRounds = r;
                    _debugRoundsSealed = 0;
                    _debugCaptureAdmissionClosed = false;
                    _debugLastAdmittedRoundId = int.MaxValue;
                    _matchCompletedFlagWritten = false;
                    _telemetryLogger?.ToggleLogging(true);
                }
            }
            catch { }
        }

        if (isWarmup && File.Exists(autoDebugFlag))
        {
            AddTimer(4.0f, () => Server.ExecuteCommand("mp_warmup_end; mp_freezetime 2;"));
        }
        if (File.Exists(@"H:\CS2_AI_Server\debug_logs\canary_fast_rounds.flag"))
        {
            Server.ExecuteCommand("mp_freezetime 12; mp_roundtime 0.45; mp_roundtime_defuse 0.45; mp_round_restart_delay 2;");
            if (isWarmup)
            {
                AddTimer(3.0f, () => Server.ExecuteCommand("mp_warmup_end; mp_freezetime 12; mp_roundtime 0.45; mp_roundtime_defuse 0.45; mp_round_restart_delay 2;"));
            }
        }
        _currentRound = isWarmup ? 0 : roundRecord.OfficialRoundNumber;
        var capturedRoundRecord = roundRecord;
        _isFreezeTime = true;
        _isBombPlanted = false;
        _positioningRoundStartTime = Server.CurrentTime;
        int shadowRoundId = Math.Max(1, _ctScore + _trScore + 1);
        _positioningRingBuffer.OnRoundStart(_positioningMatchId, shadowRoundId);
        _openingRouteTracker.OnRoundStart(shadowRoundId);
        _firstCtDeathSectorInRound = "None";

        // Correcao 3: Bloqueia compra autonoma nativa no frame 0
        Server.ExecuteCommand("bot_eco_limit 16000; bot_autobuy 0;");

        ClearRoundTimers();
        _roundCts?.Cancel();
        _roundCts?.Dispose();
        _roundCts = new CancellationTokenSource();

        if (_currentRound == 1 || _currentRound == 13)
        {
            _ctLossStreak = 1;
            _trLossStreak = 1;
        }

        _hudTimer?.Kill();
        _buyTimer?.Kill();
        _clockTimer?.Kill();
        _pacingController?.ResetRound();
        _locomotionDriver.ResetRound();
        _isGameManuallyPaused = false;
        _lastHurtThreatAlertTime.Clear();
        _intentTracker?.OnRoundStart();
        _utilityCoordinator?.OnRoundStart();
        _calloutSystem?.OnRoundStart();
        _clearAndPlantController?.OnRoundStart();
        _retakeAndDefuseBrain?.OnRoundStart();
        _trPivotController?.OnRoundStart();
        _economyManager.OnRoundStart();
        _mobilityController?.OnRoundStart();
        _combatAdapter?.OnRoundStart();

                var currentPlayersList = GetActivePlayers();
        _currentPlan.CurrentPhase = RoundPhase.FreezeTime;

        _mapProfileManager.LoadProfile(Server.MapName, ModuleDirectory);

        // 0.05s: Higienizacao preventiva de compras frame-0 nativas da Valve
        AddRoundTimer(0.05f, () =>
        {
            var pList = GetActivePlayers().Where(p => p.IsBot).ToList();
            _economyManager.SanitizeNativePurchasesAndRefund(pList);
        });

        // 0.3s: Análise Econômica e Decisão Tática
        AddRoundTimer(0.3f, () =>
        {
            if (_spotTestRunner != null && _spotTestRunner.IsActive) return;
            var players = GetActivePlayers();
            var human = players.FirstOrDefault(p => !p.IsBot);
            bool isSpectatorMode = (human == null || human.Team == CsTeam.Spectator || human.Team == CsTeam.None);
            var humanTeam = isSpectatorMode ? CsTeam.CounterTerrorist : (human?.Team ?? CsTeam.CounterTerrorist);
            var enemyTeam = humanTeam == CsTeam.CounterTerrorist ? CsTeam.Terrorist : CsTeam.CounterTerrorist;

            var teamMembers = players.Where(p => p.Team == humanTeam).ToList();
            var teamBots = teamMembers.Where(p => p.IsBot).ToList();
            var enemyBots = players.Where(p => p.Team == enemyTeam && p.IsBot).ToList();

            var ctBots = players.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
            var trBots = players.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();

            // Item 1: Limpa qualquer arma bloqueada comprada no frame-0 e estorna saldo antes da analise
            _economyManager.SanitizeNativePurchasesAndRefund(players.Where(p => p.IsBot).ToList());

            // Item 2: Atribui papeis taticos a AMBOS os times (5 slots sem duplicar AWPer)
            _roleManager.AssignRolesToBots(ctBots, clearExisting: true);
            _roleManager.AssignRolesToBots(trBots, clearExisting: false);

            if (isSpectatorMode)
            {
                // Modo Espectador (Steam Link): Atribui spots TR para trBots
                var enemySetup = _mapProfileManager.GenerateEnemyTeamSetup(trBots, CsTeam.Terrorist);
                _roleManager.SetEnemyBotSpots(enemySetup);
            }
            else
            {
                var enemySetup = _mapProfileManager.GenerateEnemyTeamSetup(enemyBots, enemyTeam);
                _roleManager.SetEnemyBotSpots(enemySetup);
            }

            int humanLossBonus = humanTeam == CsTeam.CounterTerrorist ? GetLossBonus(_ctLossStreak) : GetLossBonus(_trLossStreak);
            var buyState = _economyManager.AnalyzeTeamEconomy(teamMembers, _currentRound, humanLossBonus, humanTeam);

            if (_roleManager.IsHumanPositionLocked && human != null && !string.IsNullOrEmpty(_roleManager.LockedSectorName))
            {
                _roleManager.ClaimPositionForPlayer(human, _roleManager.LockedSectorName, teamBots, _currentPlan, _mapProfileManager);
            }

            var tacticalDecision = _probabilityEngine.DecidePlayForRound(_currentRound, humanTeam, buyState);
            _currentPlan.PlayTier = tacticalDecision.Tier;
            _currentPlan.PlayId = tacticalDecision.PlayId;

            var iglBot = teamBots.FirstOrDefault(b => b.PawnIsAlive) ?? teamBots.FirstOrDefault();
            string iglName = iglBot?.PlayerName ?? "Capitão IGL";

            if (tacticalDecision.IsCheesePlay)
            {
                _currentPlan.TacticName = $"[CHEESE] {tacticalDecision.PlayName}";
                _currentPlan.TacticSummary = tacticalDecision.Description;
                _currentPlan.RoundTempo = tacticalDecision.SuggestedTempo;
                _currentPlan.StagingDurationSeconds = tacticalDecision.StagingDuration;

                if (humanTeam == CsTeam.CounterTerrorist)
                    _ctController?.OnRoundStart(_currentPlan, ctBots);
                else
                    _midRoundAdapter?.OnRoundStart(_currentPlan, trBots, human);

                UtilityAndClockCoordinator.PrintTeamChat(humanTeam, iglName, $"🧀 JOGADA CHEESE: {tacticalDecision.PlayName}! {tacticalDecision.Description}");
            }
            else
            {
                // V4.3: Decisão de início de round 100% síncrona e instantânea (< 0.05ms) na Game Thread via TacticalUtilityIglEngine!
                int capturedInternalId = (int)capturedRoundRecord.InternalRoundId;

                var ctMembers = players.Where(p => p.Team == CsTeam.CounterTerrorist).ToList();
                var trMembers = players.Where(p => p.Team == CsTeam.Terrorist).ToList();
                var ctEcon = _economyManager.CapturePreBuySnapshot(ctMembers, Math.Max(1, _currentRound), GetLossBonus(_ctLossStreak), CsTeam.CounterTerrorist);
                var trEcon = _economyManager.CapturePreBuySnapshot(trMembers, Math.Max(1, _currentRound), GetLossBonus(_trLossStreak), CsTeam.Terrorist);

                var (ctPlan, trPlan) = _iglService.UtilityEngine.DecideRoundPlans(
                    capturedInternalId,
                    Math.Max(1, _currentRound),
                    ctEcon,
                    trEcon,
                    ctBots,
                    trBots,
                    _mapProfileManager,
                    Server.TickCount);

                _iglService.RecordTeamTacticUsed(CsTeam.CounterTerrorist, ctPlan.TacticName);
                _iglService.RecordTeamTacticUsed(CsTeam.Terrorist, trPlan.TacticName);

                _currentCtPlan = ctPlan;
                _currentTrPlan = trPlan;
                _currentPlan = (humanTeam == CsTeam.CounterTerrorist) ? ctPlan : trPlan;
                _currentPlan.PlayTier = tacticalDecision.Tier;
                _currentPlan.CurrentPhase = RoundPhase.FreezeTime;
                _currentTrPlan.CurrentPhase = RoundPhase.FreezeTime;
                _currentCtPlan.CurrentPhase = RoundPhase.FreezeTime;

                if (_roleManager.IsHumanPositionLocked && human != null && !string.IsNullOrEmpty(_roleManager.LockedSectorName))
                {
                    _roleManager.ClaimPositionForPlayer(human, _roleManager.LockedSectorName, teamBots, _currentPlan, _mapProfileManager);
                }

                _ctController?.OnRoundStart(ctPlan, ctBots);
                _midRoundAdapter?.OnRoundStart(trPlan, trBots, human);

                Server.PrintToConsole($"[UTILITY_IGL_DECISION] R{Math.Max(1, _currentRound)} | CT={ctPlan.SelectedTactic} ({ctPlan.LatencyMs:F3}ms) | TR={trPlan.SelectedTactic} ({trPlan.LatencyMs:F3}ms)");
                UtilityAndClockCoordinator.PrintTeamChat(humanTeam, iglName, $"⚡ Tática: {_currentPlan.TacticName} ({_currentPlan.LatencyMs:F2}ms) | {_currentPlan.TacticSummary}");
            }

            // O-01: Atualiza o cache HTML da HUD a 1Hz (I-03: permanece ativo durante todo o round)
            _hudTimer = AddTimer(1.0f, () =>
            {
                var currentPlayers = GetActivePlayers();
                CCSPlayerController? currentHuman = currentPlayers.FirstOrDefault(p => !p.IsBot);

                if (currentHuman != null && _pacingController != null)
                {
                    _cachedHumanSlot = currentHuman.Slot;
                    var currentTeamBots = currentPlayers.Where(p => p.IsBot && p.Team == currentHuman.Team).ToList();

                    _cachedHudHtml = TacticalHudRenderer.BuildChipHudHtml(
                        _economyManager.CurrentBuyState,
                        _currentPlan,
                        _roleManager,
                        _mapProfileManager,
                        _pacingController,
                        currentTeamBots,
                        _voiceBridge);
                }
                else
                {
                    _cachedHumanSlot = -1;
                    _cachedHudHtml = string.Empty;
                }
            }, TimerFlags.REPEAT);
        });

        // 11.0s: Executa compras determinísticas para AMBOS os times (C-05A)
        _buyTimer = AddTimer(11.0f, () =>
        {
            if (_spotTestRunner != null && _spotTestRunner.IsActive) return;
            var players = GetActivePlayers();
            var human = players.FirstOrDefault(p => !p.IsBot);
            var humanTeam = human?.Team ?? CsTeam.CounterTerrorist;
            var enemyTeam = humanTeam == CsTeam.CounterTerrorist ? CsTeam.Terrorist : CsTeam.CounterTerrorist;

            var teamBots = players.Where(p => p.Team == humanTeam && p.IsBot).ToList();
            var enemyBots = players.Where(p => p.Team == enemyTeam && p.IsBot).ToList();

            var ctBots = players.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();

            // Compra dos aliados
            _economyManager.ExecuteDeterministicBuys(teamBots, _economyManager.CurrentBuyState, humanTeam, _roleManager, _currentPlan, _locomotionDriver);

            // Setup de Double AWP no CT se economia permitir (Módulo 1)
            _economyManager.TryCoordinateDoubleAwpSetup(ctBots, _roleManager, _currentPlan, humanTeam);

            // C-05A: Compra dos inimigos com IA econômica determinística
            int enemyLossBonus = enemyTeam == CsTeam.CounterTerrorist ? GetLossBonus(_ctLossStreak) : GetLossBonus(_trLossStreak);
            var enemyMembers = players.Where(p => p.Team == enemyTeam).ToList();
            var enemyBuyState = _economyManager.AnalyzeTeamEconomy(enemyMembers, _currentRound, enemyLossBonus, enemyTeam);
            _economyManager.ExecuteDeterministicBuys(enemyBots, enemyBuyState, enemyTeam, _roleManager, _currentPlan, _locomotionDriver);

            // V4: consolida snapshots pós-compra independentes por time e registra cabeçalho forense
            // (RawJson CT e TR nunca são cruzados entre times)
            AddRoundTimer(0.6f, () =>
            {
                var postPlayers = GetActivePlayers();
                var ctPost = _economyManager.ConsolidatePostBuySnapshot(postPlayers.Where(p => p.Team == CsTeam.CounterTerrorist).ToList(), CsTeam.CounterTerrorist);
                var trPost = _economyManager.ConsolidatePostBuySnapshot(postPlayers.Where(p => p.Team == CsTeam.Terrorist).ToList(), CsTeam.Terrorist);

                _telemetryLogger?.OnRoundStartV4(
                    capturedRoundRecord,
                    _ctScore,
                    _trScore,
                    ctPost,
                    trPost,
                    _currentCtPlan ?? new TacticalPlan(),
                    _currentTrPlan ?? new TacticalPlan(),
                    postPlayers);
            });

            if (human != null && _currentPlan != null)
            {
                human.PrintToChat($" {ChatColors.Green}[CsBot IGL]{ChatColors.Default} Tática: {ChatColors.Gold}{_currentPlan.TacticName}{ChatColors.Default} | Ritmo: {ChatColors.LightBlue}{_currentPlan.RoundTempo}{ChatColors.Default}!");
            }

            // 11.5s: Disciplina da C4 no Freeze Time e Garantia de Arma em Maos (Correcao 3)
            AddRoundTimer(0.5f, () =>
            {
                var curPlayers = GetActivePlayers();
                foreach (var b in curPlayers.Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive))
                {
                    if (!_isFreezeTime && _openingCanaryGuard.LeaseManager.IsSlotLeasedByCanary(b.Slot))
                        continue;
                    EconomyManager.EquipBestWeapon(b);
                }

                var curHuman = curPlayers.FirstOrDefault(p => !p.IsBot);
                var curTrBots = curPlayers.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();
                _economyManager.EnforceC4Discipline(curTrBots, curHuman, _roleManager);
            });
        });

        return HookResult.Continue;
    }

    private HookResult OnRoundFreezeEnd(EventRoundFreezeEnd @event, GameEventInfo info)
    {
        if (_spotTestRunner != null && _spotTestRunner.IsActive)
        {
            _isFreezeTime = false;
            return HookResult.Continue;
        }

        _lifecycle.TryTransitionToActivePhase(Server.TickCount);
        _isFreezeTime = false;
        _roundFreezeEndTime = Server.CurrentTime;
        _lastCanaryEvalTickBySlot.Clear();
        _corridorQueuesByRound.Clear();
        _passiveDepartureHolds.Clear();
        _pendingCanaryFollowers.Clear();
        _fullTeamScheduleByRound.Clear();
        NativeCcsBotLocomotionBridge.ResetSlotTracking();
        if (!IsEngineWarmup())
        {
            _openingRouteTracker.OnFreezeTimeEnded(Server.TickCount);

            // Adquire MovementAuthorityLease para o único bot Canary CT antes do disparo de ordens de freeze end
            UpdateOpeningRouteControlAndShadowTick(runShadowSampling: true);
        }

        var players = GetActivePlayers();
        var human = players.FirstOrDefault(p => !p.IsBot);
        bool isSpectatorMode = (human == null || human.Team == CsTeam.Spectator || human.Team == CsTeam.None);
        var humanTeam = isSpectatorMode ? CsTeam.CounterTerrorist : (human?.Team ?? CsTeam.CounterTerrorist);
        var enemyTeam = humanTeam == CsTeam.CounterTerrorist ? CsTeam.Terrorist : CsTeam.CounterTerrorist;

        var teamBots = players.Where(p => p.Team == humanTeam && p.IsBot).ToList();
        var enemyBots = players.Where(p => p.Team == enemyTeam && p.IsBot).ToList();

        var ctBots = players.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
        var trBots = players.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();

        if (isSpectatorMode)
        {
            // Modo Espectador (Steam Link): Ambos os times entram em combate tático coordenado
            _ctController?.OnRoundFreezeEnd(_currentPlan, ctBots);
            _pacingController?.OnRoundFreezeEnd(_currentPlan, ctBots, trBots);
            _midRoundAdapter?.OnRoundFreezeEnd(_currentPlan, trBots, ctBots, null);
        }
        else
        {
            // C-01A & C-01B: Despacha posições físicas via NavMesh para aliados E inimigos
            _pacingController?.OnRoundFreezeEnd(_currentPlan, teamBots, enemyBots);
            _ctController?.OnRoundFreezeEnd(_currentPlan, ctBots);
            _midRoundAdapter?.OnRoundFreezeEnd(_currentPlan, trBots, ctBots, human);
            _intentTracker?.OnRoundFreezeEnd(_currentPlan, human, teamBots);
        }

        // Clock Sense Tracker
        _clockTimer?.Kill();
        _clockTimer = AddTimer(0.5f, () =>
        {
            if (_isFreezeTime) return;

            float elapsed = Server.CurrentTime - _roundFreezeEndTime;
            float remaining = Math.Max(0.0f, 115.0f - elapsed);

            _locomotionDriver.RoundTimeRemaining = remaining;

            var activePlayers = GetActivePlayers();
            var currentCtBots = activePlayers.Where(p => p.IsBot && p.Team == CsTeam.CounterTerrorist).ToList();
            var currentTrBots = activePlayers.Where(p => p.IsBot && p.Team == CsTeam.Terrorist).ToList();

            _utilityCoordinator?.UpdateClockSense(remaining, _isBombPlanted, _currentPlan, currentCtBots, currentTrBots);

            // Snapshot tático a cada ~3.0s durante round ativo
            if ((int)elapsed > 0 && (int)elapsed % 3 == 0 && Math.Abs(elapsed - (int)elapsed) < 0.55f)
            {
                _telemetryLogger?.RecordPeriodicSnapshot(activePlayers, _currentPlan);
            }
        }, TimerFlags.REPEAT);

        // I-03: NÃO mata o _hudTimer após Staging! Ele permanece ativo durante todo o round para exibir badges de fim de round.
        return HookResult.Continue;
    }

    private HookResult OnRoundEnd(EventRoundEnd @event, GameEventInfo info)
    {
        _isFreezeTime = false;
        int endRoundId = Math.Max(1, _ctScore + _trScore + 1);
        _openingCanaryGuard.LeaseManager.OnRoundEnd(endRoundId, Server.TickCount, lease =>
        {
            var bot = Utilities.GetPlayerFromSlot(lease.BotSlot);
            NativeCcsBotLocomotionBridge.RestoreSnapshot(bot, bot?.PlayerPawn.Value?.Bot, lease.OriginalState);
        });
        _openingCanaryGuard.FinalizeActiveSession(endRoundId, "AUTHORITY_RELEASED", Server.TickCount);
        foreach (var remSess in _openingCanaryGuard.GetSessionsForRound(endRoundId))
        {
            string remReason = remSess.ExecutorState == CanaryExecutorState.DestinationReached
                ? "COMPLETED"
                : (remSess.ExecutorState == CanaryExecutorState.Interrupted ? "INTERRUPTED" : "ABORTED");
            FinalizeAssignmentFromSession(remSess, remReason, Server.TickCount);
        }
        foreach (var pkv in _pendingCanaryFollowers.ToList())
        {
            if (pkv.Key.RoundId != endRoundId) continue;
            _pendingCanaryFollowers.Remove(pkv.Key);
            var (cand, fa) = pkv.Value;
            string assignId = $"r{endRoundId}_{pkv.Key.Team}_s{cand.Bot.Slot}";
            if (_terminatedAssignments.Add($"{_runId}:{assignId}"))
            {
                EmitAssignmentLifecycleRecord(new OpeningAssignmentLifecycleRecord
                {
                    EventType = "OPENING_ASSIGNMENT_TERMINAL",
                    AssignmentId = assignId,
                    RoundId = endRoundId,
                    Team = pkv.Key.Team,
                    PlayerPseudonym = cand.PseudoSlot,
                    Destination = cand.Spot.Id,
                    RouteId = cand.Spot.Id,
                    RouteCertified = true,
                    RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
                    EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
                    LifecycleState = OpeningAssignmentLifecycleState.CANCELLED_BEFORE_CONTROL,
                    TerminalReason = "ROUND_ENDED_BEFORE_START",
                    PredecessorSlot = fa.PredecessorSlot,
                    QueueId = fa.QueueId,
                    ScheduledTick = Server.TickCount,
                    PlannedReleaseTick = fa.PlannedReleaseTick,
                    ExpirationTick = Server.TickCount,
                    TerminalTick = Server.TickCount,
                    ControllerCreated = false,
                    LeaseAcquired = false,
                    SessionId = string.Empty,
                });
            }
        }
        _openingRouteTracker.CloseAllOpenRoutes(endRoundId, OpeningRouteTerminationReason.ROUND_END, Server.TickCount);
        _createdTeamSchedules.RemoveWhere(k => k.RoundId < endRoundId);
        FlushOpeningRouteSnapshot();
        _roundCts?.Cancel();
        _roundCts?.Dispose();
        _roundCts = null;
        ClearRoundTimers();

        _hudTimer?.Kill();
        _hudTimer = null;
        _cachedHudHtml = string.Empty;
        _cachedHumanSlot = -1;

        _buyTimer?.Kill();
        _buyTimer = null;
        _clockTimer?.Kill();
        _clockTimer = null;
        _pacingController?.ResetRound();

        var activePlayers = GetActivePlayers();
        var aliveBots = activePlayers.Where(p => p.IsBot && p.PawnIsAlive).ToList();

        // Looting inteligente de armas no fim do round (Parte A - Item 3)
        _economyManager.PerformPostRoundLooting(aliveBots, _locomotionDriver);

        _locomotionDriver.ResetRound();
        _lastHurtThreatAlertTime.Clear();

        var winner = (CsTeam)@event.Winner;
        int reasonCode = @event.Reason;

        // V4 (Bug 1): selagem idempotente — nunca soma placar ou emite FIM_ROUND duas vezes
        if (!_lifecycle.TrySealRound(reasonCode, winner, Server.TickCount, ref _ctScore, ref _trScore, ref _ctLossStreak, ref _trLossStreak, out var sealedRec) || sealedRec == null)
        {
            var env = _lifecycle.CreateEventEnvelope(Server.TickCount, _telemetryLogger?.GetRoundClockFormatted() ?? "00:00", "EventRoundEnd");
            _telemetryLogger?.LogLateEvent(env, "RoundEnd(duplicado)", $"winner={winner} reason={reasonCode}");
            return HookResult.Continue;
        }

        _telemetryLogger?.LogRoundSealed(sealedRec);

        int survivingWinners = activePlayers.Count(p => p.PawnIsAlive && p.Team == winner);
        string? plantedSiteStr = _currentTrPlan.BombObjectiveState.PlantedSite != BombsiteTarget.None
            ? _currentTrPlan.BombObjectiveState.PlantedSite.ToString()
            : null;
        string attackedSiteStr = plantedSiteStr
            ?? (_currentTrPlan.BombObjectiveState.CommittedSite != BombsiteTarget.None
                ? _currentTrPlan.BombObjectiveState.CommittedSite.ToString()
                : (_currentTrPlan.RealTargetSite ?? "None"));

        _iglService.RecordRoundResult(
            _currentRound,
            winner,
            sealedRec.EndReasonEnum,
            plantedSiteStr,
            _currentPlan.TacticName,
            _currentPlan.RoundTempo,
            _currentCtPlan.SelectedTactic,
            _currentTrPlan.SelectedTactic,
            attackedSiteStr,
            _firstCtDeathSectorInRound,
            survivingWinners);

        if (reasonCode != 16 && sealedRec.MatchPhase == MatchLifecyclePhase.LIVE && _debugTargetRounds > 0 && !_debugCaptureAdmissionClosed && _telemetryLogger != null && _telemetryLogger.IsEnabled)
        {
            _debugRoundsSealed++;
            if (_debugRoundsSealed >= _debugTargetRounds)
            {
                _debugCaptureAdmissionClosed = true;
                _debugLastAdmittedRoundId = endRoundId;
                _openingCanaryGuard.FinalizeAllOpenSessions("CAPTURE_ENDED", Server.TickCount);
                _telemetryLogger.CloseCapture(CaptureEndReason.MATCH_COMPLETED, _lifecycle);
                Console.WriteLine($"[CsBotManager] DEBUG_CAPTURE_ADMISSION_CLOSED target={_debugTargetRounds} sealed={_debugRoundsSealed} last_admitted_round={_debugLastAdmittedRoundId} tick={Server.TickCount}");
                Server.PrintToConsole($"[CsBot Debug] Captura encerrada automaticamente após {_debugRoundsSealed} rounds.");
                if (!_matchCompletedFlagWritten)
                {
                    _matchCompletedFlagWritten = true;
                    try { File.WriteAllText(@"H:\CS2_AI_Server\debug_logs\match_completed.flag", DateTime.UtcNow.ToString("O")); } catch { }
                }
            }
        }
        return HookResult.Continue;
    }

    private HookResult OnPlayerHurt(EventPlayerHurt @event, GameEventInfo info)
    {
        var players = GetActivePlayers();
        var human = players.FirstOrDefault(p => !p.IsBot);
        var humanTeam = human?.Team ?? CsTeam.CounterTerrorist;
        var teamBots = players.Where(p => p.Team == humanTeam && p.IsBot).ToList();

        _pacingController?.HandlePlayerHurt(@event, teamBots);
        _calloutSystem?.HandlePlayerHurt(@event, _currentPlan);
        _clearAndPlantController?.OnPlayerHurt(@event);
        _trPivotController?.OnPlayerHurt(@event);
        _mobilityController?.OnPlayerHurt(@event);
        _combatAdapter?.OnPlayerHurt(@event);

        if (@event.Userid != null && @event.Userid.IsValid && @event.Userid.IsBot)
        {
            _locomotionDriver?.CheckGrenadeHurtWatchdog(@event.Userid);
            string hurtWeapon = @event.Weapon ?? string.Empty;
            bool isHostileUtil = hurtWeapon.Contains("hegrenade", StringComparison.OrdinalIgnoreCase)
                || hurtWeapon.Contains("inferno", StringComparison.OrdinalIgnoreCase)
                || hurtWeapon.Contains("molotov", StringComparison.OrdinalIgnoreCase)
                || hurtWeapon.Contains("flashbang", StringComparison.OrdinalIgnoreCase);
            int hurtRoundId = Math.Max(1, _ctScore + _trScore + 1);
            bool wasActiveCanary = _openingCanaryGuard.IsSlotActiveCanary(hurtRoundId, @event.Userid.Slot);
            _openingCanaryGuard.NotifyPlayerDamage(hurtRoundId, @event.Userid.Slot, Server.TickCount, isHostileUtil);
            if (wasActiveCanary)
            {
                RestoreCanaryBotToUtilityAi(@event.Userid, hurtRoundId, Server.TickCount, isHostileUtil ? "HOSTILE_UTILITY" : "DAMAGE_INTERRUPTION");
            }
        }

        var victim = @event.Userid;
        var attacker = @event.Attacker;
        if (victim != null && attacker != null && victim.IsValid && attacker.IsValid)
        {
            float dist = 0.0f;
            var victimPawn = victim.PlayerPawn.Value;
            var attackerPawn = attacker.PlayerPawn.Value;
            if (victimPawn?.AbsOrigin != null && attackerPawn?.AbsOrigin != null)
            {
                var attackerPos = attackerPawn.AbsOrigin;
                dist = (victimPawn.AbsOrigin - attackerPos).Length();

                if (!_lastHurtThreatAlertTime.TryGetValue(attacker.Slot, out float lastAlert) || (Server.CurrentTime - lastAlert) >= 1.0f)
                {
                    _lastHurtThreatAlertTime[attacker.Slot] = Server.CurrentTime;
                    _locomotionDriver?.AlertNearbyTeammatesOfThreat(attackerPos, victim.Slot, victim.Team, 950f);
                }
            }
            _telemetryLogger?.LogCombatV4(attacker, victim, @event.Weapon ?? "arma", @event.DmgHealth, @event.Health, dist, @event.DmgArmor);
        }

        return HookResult.Continue;
    }

    private HookResult OnPlayerDeath(EventPlayerDeath @event, GameEventInfo info)
    {
        var players = GetActivePlayers();
        var human = players.FirstOrDefault(p => !p.IsBot);
        var humanTeam = human?.Team ?? CsTeam.CounterTerrorist;
        var teamBots = players.Where(p => p.Team == humanTeam && p.IsBot).ToList();

        _midRoundAdapter?.HandlePlayerDeath(@event, _currentPlan, teamBots);
        _calloutSystem?.HandlePlayerDeath(@event, _currentPlan);

        var victim = @event.Userid;
        var killer = @event.Attacker;

        // PONTO 6: Trade Kill e Alerta de Ameaça Imediata para aliados próximos (< 1100u)
        if (victim != null && killer != null && killer.IsValid && killer.PlayerPawn.Value?.AbsOrigin != null)
        {
            _locomotionDriver?.AlertNearbyTeammatesOfThreat(killer.PlayerPawn.Value.AbsOrigin, victim.Slot, victim.Team, 1100f);
        }

        var allTrBots = players.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();
        if (victim != null && victim.Team == CsTeam.Terrorist)
        {
            _trPivotController?.CheckBrickWallOnEntryDeath(victim, killer, _currentPlan, allTrBots);
        }
        else if (killer != null && killer.Team == CsTeam.Terrorist && victim != null)
        {
            _trPivotController?.CheckLurkerSiteClearance(killer, victim, _currentPlan, allTrBots);
            _trPivotController?.CheckMidRoundExploitPick(killer, victim, _currentPlan, allTrBots);
        }

        if (victim != null && killer != null && victim.IsValid && killer.IsValid && AdmitEvent("EventPlayerDeath", $"{killer.PlayerName} -> {victim.PlayerName}"))
        {
            string sector = MirageSectorClassifier.ClassifyPlayer(victim).SectorName;
            if (victim.Team == CsTeam.CounterTerrorist)
            {
                if (_firstCtDeathSectorInRound == "None")
                {
                    if (sector.Contains("Meio", StringComparison.OrdinalIgnoreCase) || sector.Contains("Janela", StringComparison.OrdinalIgnoreCase) || sector.Contains("Conector", StringComparison.OrdinalIgnoreCase))
                        _firstCtDeathSectorInRound = "Mid";
                    else if (sector.Contains("B", StringComparison.OrdinalIgnoreCase) || sector.Contains("Tapete", StringComparison.OrdinalIgnoreCase) || sector.Contains("Mercado", StringComparison.OrdinalIgnoreCase))
                        _firstCtDeathSectorInRound = "B";
                    else
                        _firstCtDeathSectorInRound = "A";
                }

                if (!_isBombPlanted)
                {
                    var aliveCtBots = players.Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist && p.Slot != victim.Slot).ToList();
                    _ctController?.HandleCtDefenderDeath(victim, sector, _currentCtPlan, aliveCtBots);
                }
            }
            _telemetryLogger?.LogDeath(killer, victim, @event.Weapon ?? "arma", @event.Headshot, sector);
        }

        return HookResult.Continue;
    }

    private HookResult OnPlayerFootstep(EventPlayerFootstep @event, GameEventInfo info)
    {
        _calloutSystem?.HandleFootstep(@event);
        _mobilityController?.OnPlayerFootstep(@event);
        return HookResult.Continue;
    }

    private HookResult OnWeaponFire(EventWeaponFire @event, GameEventInfo info)
    {
        _calloutSystem?.HandleWeaponFire(@event);
        return HookResult.Continue;
    }

    private HookResult OnBombPlanted(EventBombPlanted @event, GameEventInfo info)
    {
        _isBombPlanted = true;

        var players = GetActivePlayers();
        var ctBots = players.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
        var trBots = players.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();

        // Salvaguarda de objetivo: registra posição da bomba para auxílio no Defuse
        Vector? bombPos = null;
        var plantedEntities = Utilities.FindAllEntitiesByDesignerName<CPlantedC4>("planted_c4");
        var c4 = plantedEntities.FirstOrDefault();
        if (c4 != null && c4.IsValid && c4.AbsOrigin != null)
        {
            bombPos = c4.AbsOrigin;
        }

        _telemetryLogger?.LogEvent("BOMBA", "C4 plantada no bombsite!");

        // Bloco 3 / F-005: Executa HandleBombPlanted para definir se o time entrou em SAVE TÁTICO antes de notificar o locomotionDriver
        _midRoundAdapter?.HandleBombPlanted(@event, _currentPlan, ctBots, trBots);
        _locomotionDriver.NotifyBombState(true, bombPos, _currentPlan.IsTacticalSaveActive, ctBots);

        return HookResult.Continue;
    }

    private HookResult OnBombBeginDefuse(EventBombBegindefuse @event, GameEventInfo info)
    {
        var players = GetActivePlayers();
        var ctBots = players.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
        var trBots = players.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();

        _telemetryLogger?.LogEvent("DEFUSE", $"Jogador {@event.Userid?.PlayerName} iniciou desarme da C4!");

        // Módulo 2: Prioridade Inteligente de Defuse (Se bot começou sem kit e há companheiro com kit <= 400u, cede a vez)
        if (@event.Userid != null && !@event.Haskit)
        {
            var plantedEntities = Utilities.FindAllEntitiesByDesignerName<CPlantedC4>("planted_c4");
            var c4 = plantedEntities.FirstOrDefault();
            if (c4?.AbsOrigin != null && _retakeAndDefuseBrain != null)
            {
                _retakeAndDefuseBrain.CheckAndEnforceSmartDefusePriority(@event.Userid, c4.AbsOrigin, ctBots);
            }
        }

        // Inteligência contra Fake Defuse (Parte A - Item 4)
        _midRoundAdapter?.HandleBombBeginDefuse(@event, _currentPlan, trBots, ctBots);
        return HookResult.Continue;
    }

    private HookResult OnSmokeGrenadeDetonate(EventSmokegrenadeDetonate @event, GameEventInfo info)
    {
        float x = @event.X;
        float y = @event.Y;
        float z = @event.Z;

        _utilityCoordinator?.RegisterUtilityDetonation(x, y, z, "Smoke");

        var players = GetActivePlayers();
        var ctBots = players.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();

        _utilityCoordinator?.CheckReactiveMolotovOnSmokeDetonation(x, y, z, ctBots);

        var cp = _mapProfileManager.FindChokepointAt(x, y, z);
        string sector = cp?.Name ?? "Meio";

        // Macro-Pivô TR: Reação a paredão de utilitárias na entrada
        var trBots = players.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();
        _trPivotController?.CheckBrickWallOnHeavyUtility(x, y, z, _currentPlan, trBots);

        // Sistema 2: Matriz Contextual e Probabilística de Reação a Smokes e Sons
        _smokeAudioBrain?.HandleSmokeDetonation(x, y, z, ctBots, _currentPlan);

        // Registra áudio no sistema de callout
        _calloutSystem?.RecordAudioActivity(sector, -1, isEnemy: true, isGrenade: true);

        if (sector.Contains("Janela", StringComparison.OrdinalIgnoreCase) || sector.Contains("Meio", StringComparison.OrdinalIgnoreCase))
        {
            _ctController?.HandleWindowSmokeDetonation(ctBots, _currentPlan);
        }

        _ctController?.ReportBombPressure(sector, _currentPlan, ctBots);
        return HookResult.Continue;
    }

    [ConsoleCommand("css_respawn", "Posiciona os bots de acordo com a proximidade do spawn")]
    public void CommandRespawn(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        if (player.Team != CsTeam.CounterTerrorist)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} O comando de jogar pelo respawn é exclusivo do lado CT!");
            return;
        }

        var ctBots = GetActivePlayers().Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
        _roleManager.AssignPositionsBySpawn(ctBots, _currentPlan, _mapProfileManager);

        foreach (var bot in ctBots)
        {
            if (!bot.IsValid || !bot.PawnIsAlive) continue;
            var role = _roleManager.GetBotRole(bot);
            if (role != null && _currentPlan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
            {
                var spot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                if (spot != null)
                {
                    _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, order.Stance);
                }
            }
        }
    }

    [ConsoleCommand("css_executar", "Dispara o avanco imediato da equipe")]
    [ConsoleCommand("css_go", "Dispara o avanco imediato da equipe")]
    public void CommandExecutar(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        if (_isFreezeTime)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} Aguarde o fim do congelamento para disparar o execute!");
            return;
        }

        var teamBots = GetActivePlayers().Where(p => p.Team == player.Team && p.IsBot).ToList();
        _pacingController?.TriggerExecute($"Ordem do Capitão Humano ({player.PlayerName})", teamBots);
    }

    [ConsoleCommand("css_flash", "Pede pop-flash em dupla para o bot mais proximo")]
    public void CommandFlash(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        string sector = info.ArgCount >= 2 ? info.GetArg(1) : "setor";
        var teamBots = GetActivePlayers().Where(p => p.Team == player.Team && p.IsBot).ToList();

        bool asked = _ctController?.RequestHumanDuoFlash(player, sector, teamBots) ?? false;
        if (!asked)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} Nenhum bot próximo para realizar a jogada em dupla.");
        }
    }

    [ConsoleCommand("css_miou", "Dispara rotacao silenciosa para o outro bomb")]
    public void CommandMiou(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        string targetSite = info.ArgCount >= 2 ? info.GetArg(1) : "B";
        var teamBots = GetActivePlayers().Where(p => p.Team == player.Team && p.IsBot).ToList();

        _midRoundAdapter?.TriggerSilentRotate(targetSite, teamBots);
    }

    [ConsoleCommand("css_tatica", "Define call tatica para os bots")]
    public void CommandTatica(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        if (info.ArgCount < 2)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} Uso correto: !tatica <sua call aqui>");
            return;
        }

        string call = info.GetArg(1);
        for (int i = 2; i < info.ArgCount; i++)
        {
            call += " " + info.GetArg(i);
        }

        // V4.3: Roteador de 3 Camadas (Camada 1 Léxica em 0.01ms na Game Thread; Camada 2 Classificador Ollama < 300ms)
        CsTeam pTeam = player.Team;
        int pSlot = player.Slot;
        int capturedRound = Math.Max(1, _currentRound);
        int capturedInternalId = (int)_lifecycle.CurrentInternalRoundId;
        int currentTick = Server.TickCount;
        var activePlayers = GetActivePlayers();
        var teamBots = activePlayers.Where(p => p.IsBot && p.Team == pTeam).ToList();

        if (_iglService.UtilityEngine.TryRouteHumanCommandLexically(pTeam, call, out string lexicalTacticId, out string lexicalReason))
        {
            var lexicalPlan = _iglService.UtilityEngine.TryMaterializeById(
                pTeam,
                lexicalTacticId,
                capturedInternalId,
                capturedRound,
                teamBots,
                _mapProfileManager,
                currentTick,
                TacticalDecisionSource.FAST_LEXICAL_ROUTER,
                0.01);

            if (lexicalPlan != null)
            {
                lexicalPlan.SelectionReason = $"{lexicalReason} (input=\"{call}\")";
                HumanCommunicationLogger.RecordCommunication(
                    "CHAT_TATICA",
                    pTeam,
                    capturedRound,
                    call,
                    "FAST_LEXICAL_ROUTER",
                    $"{lexicalPlan.SelectedTactic} ({lexicalReason})",
                    lexicalPlan.LatencyMs);
                ApplyHumanSelectedPlan(player, pTeam, lexicalPlan, teamBots);
                return;
            }
        }

        player.PrintToChat($" {ChatColors.LightBlue}[CsBot IGL]{ChatColors.Default} Classificando call complexa via IA: \"{call}\"...");

        var ownEcon = _economyManager.GetTeamSnapshot(pTeam);
        var enemyEcon = _economyManager.GetTeamSnapshot(pTeam == CsTeam.CounterTerrorist ? CsTeam.Terrorist : CsTeam.CounterTerrorist);
        int requestSeq = Interlocked.Increment(ref _iglRequestSequence);
        var token = _roundCts?.Token ?? CancellationToken.None;

        Task.Run(async () =>
        {
            TacticalPlan newPlan;
            try
            {
                newPlan = await _iglService.ProcessHumanCommandAsync(
                    pTeam,
                    call,
                    capturedInternalId,
                    capturedRound,
                    ownEcon,
                    enemyEcon,
                    null,
                    _mapProfileManager,
                    currentTick,
                    token);
            }
            catch (OperationCanceledException)
            {
                return;
            }

            HumanCommunicationLogger.RecordCommunication(
                "CHAT_TATICA",
                pTeam,
                capturedRound,
                call,
                newPlan.Source.ToString(),
                $"{newPlan.SelectedTactic} ({newPlan.SelectionReason})",
                newPlan.LatencyMs);

            Server.NextFrame(() =>
            {
                if (capturedRound != Math.Max(1, _currentRound) || requestSeq != _iglRequestSequence)
                {
                    return;
                }

                var targetPlayer = Utilities.GetPlayerFromSlot(pSlot);
                var freshBots = GetActivePlayers().Where(p => p.IsBot && p.Team == pTeam).ToList();
                ApplyHumanSelectedPlan(targetPlayer, pTeam, newPlan, freshBots);
            });
        });
    }

    private void ApplyHumanSelectedPlan(CCSPlayerController? humanPlayer, CsTeam team, TacticalPlan newPlan, List<CCSPlayerController> teamBots)
    {
        newPlan.CurrentPhase = _isFreezeTime ? RoundPhase.FreezeTime : RoundPhase.Staging;
        _currentPlan = newPlan;
        if (team == CsTeam.CounterTerrorist)
        {
            _currentCtPlan = newPlan;
            _ctController?.OnRoundStart(newPlan, teamBots);
        }
        else
        {
            _currentTrPlan = newPlan;
            _midRoundAdapter?.OnRoundStart(newPlan, teamBots, humanPlayer);
        }

        if (humanPlayer != null && humanPlayer.IsValid)
        {
            humanPlayer.PrintToChat($" {ChatColors.Green}[CsBot IGL]{ChatColors.Default} Call aplicada ({newPlan.Source}, {newPlan.LatencyMs:F2}ms): {ChatColors.Gold}{newPlan.TacticName}{ChatColors.Default} | Ritmo: {ChatColors.LightBlue}{newPlan.RoundTempo}{ChatColors.Default}!");
        }
    }

    [ConsoleCommand("css_rejeitar", "Pede uma tatica alternativa para a IA")]
    public void CommandRejeitar(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        CsTeam pTeam = player.Team;
        var teamBots = GetActivePlayers().Where(p => p.IsBot && p.Team == pTeam).ToList();
        var ownEcon = _economyManager.GetTeamSnapshot(pTeam);
        var enemyEcon = _economyManager.GetTeamSnapshot(pTeam == CsTeam.CounterTerrorist ? CsTeam.Terrorist : CsTeam.CounterTerrorist);
        string currentTacticId = (pTeam == CsTeam.CounterTerrorist ? _currentCtPlan : _currentTrPlan).SelectedTactic;

        var altPlan = _iglService.UtilityEngine.DecideTeamPlan(
            pTeam,
            _lifecycle.CurrentInternalRoundId,
            Math.Max(1, _currentRound),
            ownEcon,
            enemyEcon,
            teamBots,
            _mapProfileManager,
            Server.TickCount,
            excludeTacticId: currentTacticId);

        altPlan.IsCustomPlayerCall = true;
        ApplyHumanSelectedPlan(player, pTeam, altPlan, teamBots);
    }

    [ConsoleCommand("css_drop", "Pede arma para o bot mais rico")]
    public void CommandDrop(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        if (!_isFreezeTime)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} Pedidos de drop só podem ser feitos durante o Freeze Time!");
            return;
        }

        string? weapon = info.ArgCount >= 2 ? info.GetArg(1) : null;
        var teamBots = GetActivePlayers().Where(p => p.Team == player.Team && p.IsBot).ToList();

        bool dropped = _economyManager.DropWeaponForPlayer(player, weapon, teamBots);
        if (!dropped)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} Nenhum bot do seu time possui saldo suficiente para este drop no momento.");
        }
    }

    [ConsoleCommand("css_pos", "Assume um setor no mapa e os bots cedem a posicao")]
    public void CommandPos(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        if (info.ArgCount < 2)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} Uso correto: !pos <setor> (ex: !pos janela, !pos b, !pos a, !pos conector)");
            return;
        }

        string sector = info.GetArg(1);
        var teamBots = GetActivePlayers().Where(p => p.Team == player.Team && p.IsBot).ToList();
        bool claimed = _roleManager.ClaimPositionForPlayer(player, sector, teamBots, _currentPlan, _mapProfileManager);
        HumanCommunicationLogger.RecordCommunication(
            "CHAT_POS",
            player.Team,
            Math.Max(1, _currentRound),
            $"!pos {sector}",
            "CHAT_POSITION_SWAP",
            $"ClaimPosition({sector}, claimed={claimed})",
            0.01);

        if (claimed)
        {
            // Move os bots afetados usando a ordem individual do slot (V4.3)
            foreach (var bot in teamBots)
            {
                if (!bot.IsValid || !bot.PawnIsAlive) continue;
                var role = _roleManager.GetBotRole(bot);
                var activePlan = bot.TeamNum == 3 ? _currentPlan : _currentTrPlan;
                if (activePlan.TryGetOrderForBot(bot.Slot, role, out var order))
                {
                    var spot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                    if (spot != null)
                    {
                        _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, order.Stance);
                    }
                }
            }
            player.PrintToChat($" {ChatColors.Green}[CsBot Dynamic Swap]{ChatColors.Default} Posição {ChatColors.Gold}{sector.ToUpper()}{ChatColors.Default} assumida por você. Os bots reorganizaram a defesa!");
        }
        else
        {
            player.PrintToChat($" {ChatColors.Yellow}[CsBot Dynamic Swap]{ChatColors.Default} Setor {sector.ToUpper()} registrado. Bots alinhados.");
        }
    }

    [ConsoleCommand("css_debug", "Liga ou desliga a telemetria forense da partida")]
    public void CommandDebug(CCSPlayerController? player, CommandInfo info)
    {
        bool? force = null;
        if (info.ArgCount >= 2)
        {
            string arg = info.GetArg(1).ToLowerInvariant();
            if (arg == "on" || arg == "1" || arg == "true") force = true;
            else if (arg == "off" || arg == "0" || arg == "false") force = false;
            else if (int.TryParse(arg, out int rounds) && rounds > 0)
            {
                // !debug <N>: captura N rounds oficiais e encerra automaticamente com rodapé
                force = true;
                _debugCaptureAdmissionClosed = false;
                _debugTargetRounds = rounds;
                _debugRoundsSealed = 0;
                _debugLastAdmittedRoundId = int.MaxValue;
                _matchCompletedFlagWritten = false;
            }
        }
        if (force == false && _telemetryLogger != null && _telemetryLogger.IsEnabled)
        {
            _telemetryLogger.CloseCapture(CaptureEndReason.MANUAL_STOP, _lifecycle);
            return;
        }
        _telemetryLogger?.ToggleLogging(force);
    }

    [ConsoleCommand("css_nota", "Registra uma nota do jogador no log de debug com snapshot instantâneo")]
    public void CommandNota(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        if (info.ArgCount < 2)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot Debug]{ChatColors.Default} Uso correto: !nota <sua observação>");
            return;
        }

        string noteText = string.Join(" ", Enumerable.Range(1, info.ArgCount - 1).Select(i => info.GetArg(i)));
        _telemetryLogger?.RecordPlayerNote(player, noteText, GetActivePlayers(), _currentPlan);
    }

    [ConsoleCommand("css_mlmove", "Exibe status e benchmark do motor MLMove 16Hz / ONNX")]
    [ConsoleCommand("css_mlmove_status", "Exibe status e benchmark do motor MLMove 16Hz / ONNX")]
    public void CommandMlMoveStatus(CCSPlayerController? player, CommandInfo info)
    {
        if (_microMoveEngine == null) return;
        _microMoveEngine.TryLoadMapModel(Server.MapName);
        string status = _microMoveEngine.BackendName;
        string msg = $"[CsBot MLMove 16Hz] Status: {status} | Inferências Totais: {_microMoveEngine.TotalOnnxInferences} | Última Latência CPU: {_microMoveEngine.LastInferenceLatencyMs:F2}ms";
        Server.PrintToConsole(msg);
        if (player != null && player.IsValid)
        {
            player.PrintToChat($" {ChatColors.Green}[CsBot MLMove]{ChatColors.Default} {status} (Inferências: {_microMoveEngine.TotalOnnxInferences})");
        }
        else
        {
            Server.PrintToChatAll($" {ChatColors.Green}[CsBot MLMove]{ChatColors.Default} {status}");
        }
    }

    [ConsoleCommand("css_gravardemo", "Inicia ou para gravacao de demo CSTV para o pipeline MLMove")]
    public void CommandGravarDemo(CCSPlayerController? player, CommandInfo info)
    {
        string arg = info.ArgCount >= 2 ? info.GetArg(1).ToLowerInvariant() : "start";
        if (arg == "stop" || arg == "parar" || arg == "0")
        {
            Server.ExecuteCommand("tv_stoprecord");
            Server.PrintToChatAll($" {ChatColors.Yellow}[CsBot CSTV]{ChatColors.Default} Gravação de demo CSTV encerrada.");
        }
        else
        {
            string demoName = $"csbot_{Server.MapName}_{DateTime.Now:yyyyMMdd_HHmmss}";
            Server.ExecuteCommand($"tv_record {demoName}");
            Server.PrintToChatAll($" {ChatColors.Green}[CsBot CSTV]{ChatColors.Default} Gravando demo CSTV: {ChatColors.Gold}{demoName}.dem{ChatColors.Default}");
        }
    }

    [ConsoleCommand("css_pause", "Pausa o jogo por completo sem limite de tempo")]
    [ConsoleCommand("css_pausar", "Pausa o jogo por completo sem limite de tempo")]
    public void CommandPause(CCSPlayerController? player, CommandInfo info)
    {
        if (_isGameManuallyPaused)
        {
            CommandContinue(player, info);
            return;
        }

        _isGameManuallyPaused = true;
        Server.ExecuteCommand("sv_pausable 1; sv_unpause_on_console_close 0; pause; mp_pause_match;");

        string caller = player != null && player.IsValid ? player.PlayerName : "Servidor";
        Server.PrintToChatAll($" {ChatColors.Green}[CsBot]{ChatColors.Default} Jogo {ChatColors.DarkRed}PAUSADO{ChatColors.Default} por {ChatColors.Gold}{caller}{ChatColors.Default} (sem tempo limite).");
        Server.PrintToChatAll($" {ChatColors.Green}[CsBot]{ChatColors.Default} Para retomar a partida, digite {ChatColors.Green}!continue{ChatColors.Default} ou {ChatColors.Green}!unpause{ChatColors.Default}.");
    }

    [ConsoleCommand("css_continue", "Retoma o jogo pausado")]
    [ConsoleCommand("css_unpause", "Retoma o jogo pausado")]
    [ConsoleCommand("css_despausar", "Retoma o jogo pausado")]
    [ConsoleCommand("css_retomar", "Retoma o jogo pausado")]
    public void CommandContinue(CCSPlayerController? player, CommandInfo info)
    {
        if (!_isGameManuallyPaused)
        {
            if (player != null && player.IsValid)
            {
                player.PrintToChat($" {ChatColors.Yellow}[CsBot]{ChatColors.Default} O jogo nao esta pausado no momento.");
            }
            return;
        }

        _isGameManuallyPaused = false;
        Server.ExecuteCommand("sv_pausable 1; unpause; mp_unpause_match;");

        string caller = player != null && player.IsValid ? player.PlayerName : "Servidor";
        Server.PrintToChatAll($" {ChatColors.Green}[CsBot]{ChatColors.Default} Jogo {ChatColors.Green}RETOMADO{ChatColors.Default} por {ChatColors.Gold}{caller}{ChatColors.Default}. Bom jogo!");
    }

    [ConsoleCommand("css_spottest", "Executa teste A/B de spots (!spottest <profileVersion> <spotId> <attempts>)")]
    public void CommandSpotTest(CCSPlayerController? player, CommandInfo info)
    {
        string profileArg = info.ArgCount >= 2 ? info.GetArg(1) : "all";
        string spotIdArg = info.ArgCount >= 3 ? info.GetArg(2) : "all";
        int attempts = 3;
        if (info.ArgCount >= 4 && int.TryParse(info.GetArg(3), out int parsedAttempts) && parsedAttempts > 0)
        {
            attempts = parsedAttempts;
        }

        bool clearFile = profileArg.Equals("all", StringComparison.OrdinalIgnoreCase) && spotIdArg.Equals("all", StringComparison.OrdinalIgnoreCase);
        int count = _spotTestRunner?.EnqueueSpotTests(profileArg, spotIdArg, attempts, ModuleDirectory, clearFile) ?? 0;

        string msg = $"[SpotTest] Enfileiradas {count} tentativas (profile={profileArg}, spot={spotIdArg}, attempts={attempts}).";
        Server.PrintToConsole(msg);
        if (player != null && player.IsValid)
        {
            player.PrintToChat($" {ChatColors.Green}[SpotTest]{ChatColors.Default} {msg}");
        }
    }

    [ConsoleCommand("css_hud", "Liga ou desliga o HUD central na tela")]
    public void CommandToggleHud(CCSPlayerController? player, CommandInfo info)
    {
        if (info.ArgCount > 1)
        {
            string arg = info.GetArg(1).ToLowerInvariant();
            if (arg == "on" || arg == "1" || arg == "true" || arg == "ligar")
            {
                _isHudEnabled = true;
            }
            else if (arg == "off" || arg == "0" || arg == "false" || arg == "desligar")
            {
                _isHudEnabled = false;
                if (player != null && player.IsValid)
                {
                    player.PrintToCenterHtml("");
                }
            }
        }
        else
        {
            _isHudEnabled = !_isHudEnabled;
            if (!_isHudEnabled && player != null && player.IsValid)
            {
                player.PrintToCenterHtml("");
            }
        }

        string status = _isHudEnabled ? $"{ChatColors.Green}ATIVADO{ChatColors.Default}" : $"{ChatColors.Red}DESATIVADO{ChatColors.Default} (modo limpo para segunda tela)";
        if (player != null && player.IsValid)
        {
            player.PrintToChat($" {ChatColors.Green}[CsBot]{ChatColors.Default} HUD central na tela {status}.");
        }
    }

    private List<CCSPlayerController> GetActivePlayers()
    {
        return Utilities.GetPlayers()
            .Where(p => p != null && p.IsValid && !p.IsHLTV)
            .ToList();
    }

    private HookResult OnPlayerSay(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return HookResult.Continue;
        string msg = info.GetArg(1);
        if (_spotRecorder != null && _spotRecorder.TryHandleChatCommand(player, msg))
        {
            return HookResult.Handled;
        }
        return HookResult.Continue;
    }

    private HookResult OnPlayerSpawn(EventPlayerSpawn @event, GameEventInfo info)
    {
        var player = @event.Userid;
        if (player != null && player.IsValid && !player.IsBot)
        {
            _spotRecorder?.OnPlayerSpawn(player);
        }
        return HookResult.Continue;
    }

    private void InitializePositioningShadowMode(string? mapName)
    {
        string cleanMap = string.IsNullOrWhiteSpace(mapName) ? string.Empty : mapName.Trim().ToLowerInvariant();
        if (cleanMap != "de_mirage")
        {
            return;
        }

        _positioningTransformerService ??= new PositioningTransformerService();
        if (!_positioningTransformerService.IsReady)
        {
            string candidate1 = Path.Combine(ModuleDirectory, "models", "positioning", "de_mirage_positioning_hybrid_v2.onnx");
            string candidate2 = @"H:\CS2_AI_Server\models\positioning\de_mirage_positioning_hybrid_v2.onnx";
            string modelPath = File.Exists(candidate1) ? candidate1 : candidate2;
            const string expectedSha256 = "72689b2200065a44a8d7e346a7dcc81b6a670f7f7e2797cb94f676f4d17725a4";

            if (File.Exists(modelPath))
            {
                bool loaded = _positioningTransformerService.LoadModel(modelPath, expectedSha256);
                Console.WriteLine($"[CsBotManager][PositioningShadow] LoadModel(V2)={loaded} ctx={_positioningTransformerService.SupportsContextualInputs} warmup_started={_positioningTransformerService.WarmupStarted} warmup_success={_positioningTransformerService.WarmupSuccess} warmup_ms={_positioningTransformerService.WarmupDurationMs:F2} err='{_positioningTransformerService.LastLoadError}'");
            }
        }

        if (_positioningShadowTelemetry == null)
        {
            string logDir = Path.Combine(ModuleDirectory, "logs");
            string logPath = Path.Combine(logDir, "positioning_shadow_telemetry.jsonl");
            _positioningShadowTelemetry = new PositioningShadowTelemetryLogger(logPath);
        }
    }

    private void CollectPositioningFeatureFrame()
    {
        if (_positioningTransformerService == null || !_positioningTransformerService.IsReady)
        {
            return;
        }

        string cleanMap = (Server.MapName ?? string.Empty).Trim().ToLowerInvariant();
        if (cleanMap != "de_mirage")
        {
            return;
        }

        int roundId = Math.Max(1, _ctScore + _trScore + 1);
        int tick = Server.TickCount;
        float roundTimeRemaining = Math.Max(0.0f, 115.0f - (float)(Server.CurrentTime - _positioningRoundStartTime));

        foreach (var p in Utilities.GetPlayers())
        {
            if (p == null || !p.IsValid || p.TeamNum < 2 || p.TeamNum > 3)
            {
                continue;
            }

            bool isTerrorist = p.TeamNum == 2;
            var pawn = p.PlayerPawn.Value;
            bool isAlive = p.PawnIsAlive && pawn != null && pawn.AbsOrigin != null;

            float x = 0f, y = 0f, z = 0f, vx = 0f, vy = 0f, vz = 0f, yaw = 0f, pitch = 0f, hp = 0f, armor = 0f, roleCode = 0.50f;
            string weaponName = string.Empty;
            bool hasC4 = false;

            if (isAlive && pawn != null && pawn.AbsOrigin != null)
            {
                x = pawn.AbsOrigin.X;
                y = pawn.AbsOrigin.Y;
                z = pawn.AbsOrigin.Z;
                vx = pawn.AbsVelocity?.X ?? 0f;
                vy = pawn.AbsVelocity?.Y ?? 0f;
                vz = pawn.AbsVelocity?.Z ?? 0f;
                yaw = pawn.EyeAngles?.Y ?? 0f;
                pitch = pawn.EyeAngles?.X ?? 0f;
                hp = pawn.Health;
                armor = pawn.ArmorValue;
                weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? string.Empty;
                if (isTerrorist && pawn.WeaponServices != null)
                {
                    foreach (var w in pawn.WeaponServices.MyWeapons)
                    {
                        if (w.Value?.DesignerName?.Contains("c4", StringComparison.OrdinalIgnoreCase) == true)
                        {
                            hasC4 = true;
                            break;
                        }
                    }
                }
                var role = _roleManager.GetBotRole(p);
                roleCode = role switch
                {
                    BotRole.AWPer => 0.25f,
                    BotRole.EntryFragger => 0.50f,
                    BotRole.Rotator => 0.75f,
                    BotRole.Anchor => 1.00f,
                    _ => 0.50f
                };
            }

            var obs = new PositioningPlayerObservation(
                Tick: tick,
                RoundId: roundId,
                PlayerSlot: p.Slot,
                IsTerrorist: isTerrorist,
                IsAlive: isAlive,
                X: x,
                Y: y,
                Z: z,
                Vx: vx,
                Vy: vy,
                Vz: vz,
                YawDeg: yaw,
                PitchDeg: pitch,
                Health: hp,
                Armor: armor,
                WeaponName: weaponName,
                RoleCode: roleCode,
                HasC4: hasC4,
                IsBombPlanted: _isBombPlanted,
                RoundTimeRemaining: roundTimeRemaining
            );

            _positioningRingBuffer.TryPushObservation(_positioningMatchId, tick, obs, out _);
        }
    }

    private void UpdatePositioningShadowObservation()
    {
        if (_positioningTransformerService == null || !_positioningTransformerService.IsReady)
        {
            return;
        }

        string cleanMap = (Server.MapName ?? string.Empty).Trim().ToLowerInvariant();
        if (cleanMap != "de_mirage")
        {
            return;
        }

        var allAliveBots = Utilities.GetPlayers()
            .Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive)
            .OrderBy(p => p.TeamNum)
            .ThenBy(p => p.Slot)
            .ToList();
        if (allAliveBots.Count == 0)
        {
            return;
        }

        int cycleBotCount = allAliveBots.Count;
        int maxBatch = PositioningTransformerContract.DefaultPreferredBatchSize;
        int batchCount = (cycleBotCount + maxBatch - 1) / maxBatch;
        long cycleId = Interlocked.Increment(ref _positioningShadowSequenceId);
        int cycleTick = Server.TickCount;
        for (int batchIndex = 0; batchIndex < batchCount; batchIndex++)
        {
            var aliveBots = allAliveBots.Skip(batchIndex * maxBatch).Take(maxBatch).ToList();
            RunPositioningShadowBatch(aliveBots, cleanMap, cycleId, cycleTick, batchIndex, batchCount, cycleBotCount);
        }
    }

    private void RunPositioningShadowBatch(List<CCSPlayerController> aliveBots, string cleanMap, long cycleId, int cycleTick, int batchIndex, int batchCount, int cycleBotCount)
    {
        _ = cycleId;
        _ = cycleTick;
        _ = batchIndex;
        _ = batchCount;
        _ = cycleBotCount;

        int b = aliveBots.Count;
        int roundId = Math.Max(1, _ctScore + _trScore + 1);
        var targetSlots = aliveBots.Select(p => p.Slot).ToList();
        var targetAlive = aliveBots.Select(p => p.PawnIsAlive).ToList();

        var candidateMask = new bool[b * PositioningTransformerContract.CandidateSpotCount];
        var objectiveEligible = new bool[b];
        var retakeEligible = new bool[b];
        var teamIdx = new long[b];
        var roleIdx = new long[b];
        var stageIdx = new long[b];
        int contextFallbackCount = 0;
        for (int i = 0; i < b; i++)
        {
            var bot = aliveBots[i];
            bool isT = bot.TeamNum == 2;
            bool isCt = bot.TeamNum == 3;
            bool hasC4 = bot.PlayerPawn.Value?.WeaponServices?.ActiveWeapon.Value?.DesignerName?.Contains("c4", StringComparison.OrdinalIgnoreCase) == true;
            // Estritamente causal: apenas eventos atuais/passados (_isBombPlanted ou posse atual de C4)
            bool objElig = isT && (_isBombPlanted || hasC4);
            bool retElig = isCt && _isBombPlanted;
            objectiveEligible[i] = objElig;
            retakeEligible[i] = retElig;
            var v2Mask = PositioningTransformerContract.BuildV2CandidateMask(isT, positioningState: null, objectiveEligible: objElig, retakeEligible: retElig);
            Array.Copy(v2Mask, 0, candidateMask, i * PositioningTransformerContract.CandidateSpotCount, PositioningTransformerContract.CandidateSpotCount);

            teamIdx[i] = PositioningTransformerContract.MapTeamToIndex(bot.TeamNum, out bool fbT);
            if (fbT) contextFallbackCount++;

            // Papel autoritativo do RoleManager (jamais inferido pelo spot previsto)
            var authRole = _roleManager.GetBotRole(bot);
            string? roleName = hasC4 ? "BOMB_CARRIER" : authRole switch
            {
                BotRole.AWPer => "AWPER",
                BotRole.EntryFragger => isCt && _isBombPlanted ? "RETAKE_ENTRY" : "ENTRY",
                BotRole.Rotator => "ROTATOR",
                BotRole.Anchor => "ANCHOR",
                _ => isCt && _isBombPlanted ? "RETAKE_COVER" : "SUPPORT",
            };
            roleIdx[i] = PositioningTransformerContract.MapRoleToIndex(roleName, out bool fbR);
            if (fbR) contextFallbackCount++;

            // Estágio causal do plano/round (sem informação futura e sem reutilizar PositioningState previsto)
            string stageName = PositioningTransformerContract.DeriveCausalStageName(
                isBombPlanted: _isBombPlanted,
                isTerrorist: isT,
                isFreezeTime: false,
                hasSeenEnemyRecently: false,
                inSiteOrObjectiveZone: false);
            stageIdx[i] = PositioningTransformerContract.MapStageToIndex(stageName, out bool fbS);
            if (fbS) contextFallbackCount++;
        }

        var input = _positioningRingBuffer.BuildBatchInput(
            _positioningMatchId,
            cleanMap,
            roundId,
            targetSlots,
            targetAlive,
            candidateMask,
            objectiveEligible,
            retakeEligible,
            out var diagnostics,
            teamIdx,
            roleIdx,
            stageIdx,
            contextFallbackCount);

        var predictions = _positioningTransformerService.PredictShadowBatch(input);
        // cycleId já incrementado uma única vez por ciclo em UpdatePositioningShadowObservation

        for (int i = 0; i < b && i < predictions.Length; i++)
        {
            var bot = aliveBots[i];
            var pred = predictions[i];
            var diag = diagnostics[i];
            TryGetCurrentUtilityPositioningDecision(bot, out var utilDec);
            string utilityDecision = ShadowModeGuard.ShadowModeCannotAffectBotDecision(utilDec.UtilityState, pred);
            _positioningShadowTelemetry?.Enqueue(new PositioningShadowTelemetryRecord(
                timestamp: DateTimeOffset.UtcNow.ToString("O"),
                map: cleanMap,
                match_id: _positioningMatchId,
                round_id: input.RoundId,
                tick: Server.TickCount,
                player_slot: PositioningTransformerContract.PseudonymizePlayerSlot(bot.Slot, _positioningMatchId),
                team: bot.TeamNum == 3 ? "CT" : "TR",
                model_hash: _positioningTransformerService.LoadedModelSha256,
                contract_version: PositioningTransformerContract.ContractVersion,
                input_valid: pred.InputValid,
                inference_success: pred.InferenceSuccess,
                latency_ms: pred.LatencyMs,
                utility_state: utilityDecision,
                neural_state: pred.FinalState?.ToString() ?? "FALLBACK",
                utility_sector: utilDec.UtilitySector,
                neural_sector: pred.NextSector?.ToString() ?? "FALLBACK",
                utility_spot: utilDec.UtilitySpot,
                neural_spot: pred.SelectedSpotId?.ToString() ?? "FALLBACK",
                neural_transition: pred.Transition?.ToString() ?? "FALLBACK",
                neural_exit_trigger: pred.ExitTrigger?.ToString() ?? "FALLBACK",
                confidence_by_head: pred.ConfidenceByHead,
                objective_eligible: input.ObjectiveEligible[i],
                retake_eligible: input.RetakeEligible[i],
                save_fallback_active: pred.SaveFallbackActive,
                fallback_reason: pred.FallbackReason,
                ring_buffer_count: diag.RingBufferCount,
                real_frame_count: diag.RealFrameCount,
                padded_frame_count: diag.PaddedFrameCount,
                effective_history_hz: diag.EffectiveHistoryHz,
                self_history_nonzero_count: diag.SelfHistoryNonZeroCount,
                teammate_history_nonzero_count: diag.TeammateHistoryNonZeroCount,
                temporal_variance: diag.TemporalVariance,
                buffer_reset_reason: diag.BufferResetReason,
                feature_contract_version: PositioningFeatureContract.FeatureContractVersion,
                warmup_duration_ms: _positioningTransformerService.WarmupDurationMs,
                team_idx: input.TeamIdx.Length > i ? input.TeamIdx[i] : 2L,
                role_idx: input.RoleIdx.Length > i ? input.RoleIdx[i] : 0L,
                stage_idx: input.StageIdx.Length > i ? input.StageIdx[i] : 0L,
                mapping_source: "RoleManager+CausalRoundState",
                fallback_mapping_used: input.ContextFallbackCount > 0,
                utility_destination: utilDec.UtilityDestination,
                utility_plan_site: utilDec.UtilityPlanSite,
                utility_role: utilDec.UtilityRole,
                utility_decision_tick: utilDec.UtilityDecisionTick,
                utility_decision_source: utilDec.UtilityDecisionSource,
                utility_decision_available: utilDec.UtilityDecisionAvailable
            ));
        }
    }

    private static string NormalizePositioningSector(string? rawSector, string? spotId)
    {
        string s = (rawSector ?? string.Empty).Trim().ToUpperInvariant();
        if (s.Contains("A", StringComparison.Ordinal) && !s.Contains("SPAWN", StringComparison.Ordinal))
        {
            if (s == "A" || s.Contains("BOMBSITE A") || s.Contains("RAMPA A") || s.Contains("PAL")) return "A";
        }
        if (s == "B" || s.Contains("BOMBSITE B") || s.Contains("APPS") || s.Contains("MERCADO") || s.Contains("MARKET")) return "B";
        if (s.Contains("MID") || s.Contains("MEIO") || s.Contains("UNDERGROUND") || s.Contains("CONECTOR") || s.Contains("JANELA") || s.Contains("WINDOW")) return "MID";
        if (s.Contains("SPAWN")) return "SPAWN";

        string id = (spotId ?? string.Empty).ToLowerInvariant();
        if (id.StartsWith("a_") || id.StartsWith("ct_a_") || id.StartsWith("tr_a_")) return "A";
        if (id.StartsWith("b_") || id.StartsWith("ct_b_") || id.StartsWith("tr_b_")) return "B";
        if (id.StartsWith("mid_")) return "MID";
        if (id.Contains("spawn")) return "SPAWN";
        return "UNKNOWN";
    }

    private bool TryGetCurrentUtilityPositioningDecision(CCSPlayerController bot, out UtilityPositioningDecision decision)
    {
        var role = _roleManager.GetBotRole(bot);
        var activePlan = bot.TeamNum == 3 ? _currentPlan : _currentTrPlan;
        if (activePlan != null && activePlan.TryGetOrderForBot(bot.Slot, role, out var order))
        {
            var spot = !string.IsNullOrWhiteSpace(order.StagingSpotId)
                ? _mapProfileManager.GetSpotById(order.StagingSpotId)
                : null;
            string dest = !string.IsNullOrWhiteSpace(order.StagingSpotId) ? order.StagingSpotId : "UNKNOWN";
            string sector = NormalizePositioningSector(spot?.Sector, dest);
            string spotId = spot?.Id ?? dest;
            decision = new UtilityPositioningDecision
            {
                UtilityState = activePlan.CurrentPhase.ToString(),
                UtilitySector = sector,
                UtilitySpot = spotId,
                UtilityDestination = dest,
                UtilityPlanSite = BombsiteParser.ResolveBombCarrierTargetSite(activePlan).ToString(),
                UtilityRole = role?.ToString() ?? "UNKNOWN",
                UtilityDecisionTick = Server.TickCount,
                UtilityDecisionSource = bot.TeamNum == 3 ? "_currentPlan" : "_currentTrPlan",
                UtilityDecisionAvailable = sector != "UNKNOWN" && spotId != "UNKNOWN",
            };
            return decision.UtilityDecisionAvailable;
        }

        decision = new UtilityPositioningDecision
        {
            UtilityState = activePlan?.CurrentPhase.ToString() ?? "UNKNOWN",
            UtilitySector = "UNKNOWN",
            UtilitySpot = "UNKNOWN",
            UtilityDestination = "UNKNOWN",
            UtilityPlanSite = "NONE",
            UtilityRole = role?.ToString() ?? "UNKNOWN",
            UtilityDecisionTick = Server.TickCount,
            UtilityDecisionSource = "NONE",
            UtilityDecisionAvailable = false,
        };
        return false;
    }

    private static string ClassifyCtCanaryCorridor(string spotId)
    {
        string id = (spotId ?? string.Empty).ToLowerInvariant();
        if (id.StartsWith("a_") || id.StartsWith("ct_a_")) return "A";
        if (id.Contains("bench") || id.Contains("van") || id.Contains("edward") || id.Contains("default_plant")) return "B_BENCH_VAN";
        if ((id.StartsWith("b_") || id.StartsWith("ct_b_")) && !id.Contains("short_arch_hold_mid")) return "B_MARKET";
        return "MID_WINDOW";
    }

    private static float DistanceToCtCorridorAnchor(string corridor, float x, float y)
    {
        (float ax, float ay) = corridor switch
        {
            "A" => (-1400f, -2080f),
            "B_MARKET" => (-1760f, -1420f),
            "B_BENCH_VAN" => (-1820f, -1380f),
            _ => (-1480f, -1520f),
        };
        float dx = x - ax;
        float dy = y - ay;
        return MathF.Sqrt(dx * dx + dy * dy);
    }

    private static string ClassifyTrCanaryCorridor(string spotId)
    {
        string id = (spotId ?? string.Empty).ToLowerInvariant();
        if (id.StartsWith("a_") || id.StartsWith("tr_a_") || id.Contains("palace") || id.Contains("tetris") || id.Contains("ramp")) return "A";
        if (id.StartsWith("b_") || id.StartsWith("tr_b_") || id.Contains("apps") || id.Contains("kitchen") || id.Contains("tapete") || id.Contains("forest")) return "B";
        return "MID";
    }

    private static float DistanceToTrCorridorAnchor(string corridor, float x, float y)
    {
        (float ax, float ay) = corridor switch
        {
            "A" => (780f, -1100f),
            "B" => (-350f, 480f),
            _ => (560f, -260f),
        };
        float dx = x - ax;
        float dy = y - ay;
        return MathF.Sqrt(dx * dx + dy * dy);
    }

    private void RestoreCanaryBotToUtilityAi(CCSPlayerController? bot, int roundId, int tick, string reason)
    {
        if (bot != null)
        {
            _openingCanaryGuard.LeaseManager.ReleaseLeaseForSlot(roundId, bot.Slot, tick, reason, lease =>
            {
                NativeCcsBotLocomotionBridge.RestoreSnapshot(bot, bot?.PlayerPawn.Value?.Bot, lease.OriginalState);
            });
        }
        else
        {
            _openingCanaryGuard.LeaseManager.ReleaseLease(roundId, tick, reason);
        }

        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;

        var existing = _locomotionDriver.GetNavState(bot.Slot);
        if (existing != null)
        {
            existing.Priority = BotOrderPriority.Medium_Tactical;
            existing.HoldDurationRemaining = 0f;
        }

        _locomotionDriver.ForceEquipBestFirearm(bot);

        var role = _roleManager.GetBotRole(bot);
        var activePlan = bot.TeamNum == 3 ? _currentPlan : _currentTrPlan;
        if (activePlan != null && activePlan.TryGetOrderForBot(bot.Slot, role, out var curOrder))
        {
            var curSpot = _mapProfileManager.GetSpotById(curOrder.StagingSpotId);
            if (curSpot != null)
            {
                _locomotionDriver.NavigateToSpot(bot, curSpot, hurry: false, stanceOverride: curOrder.Stance, priority: BotOrderPriority.Medium_Tactical);
            }
        }
    }

    private void VerifyAndRecordCanaryEndOfTickAuthority()
    {
        foreach (var lease in _openingCanaryGuard.LeaseManager.ActiveLeases)
        {
            if (lease == null || !lease.IsActive) continue;

            int roundId = lease.RoundId;
            var session = _openingCanaryGuard.GetSessionForSlot(roundId, lease.BotSlot)
                          ?? _openingCanaryGuard.GetSessionForRound(roundId);
            if (session == null || session.IsFinished) continue;

            var bot = Utilities.GetPlayerFromSlot(lease.BotSlot);
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive) continue;
            var pawn = bot.PlayerPawn.Value;
            var nativeBot = pawn?.Bot;
            if (pawn == null || nativeBot == null) continue;

        nint botHandle = nativeBot.Handle;
        var wps = session.Route.OrderedWaypoints;
        var activeWp = (session.RecoveryActive && session.RecoveryWaypoint != null)
            ? session.RecoveryWaypoint
            : (wps.Count > 0 ? wps[Math.Min(session.WaypointIndex, wps.Count - 1)] : null);

        float[] activeWpArr = activeWp != null
            ? new[] { MathF.Round(activeWp.X, 1), MathF.Round(activeWp.Y, 1), MathF.Round(activeWp.Z, 1) }
            : Array.Empty<float>();

        float[] goalEnd = NativeCcsBotLocomotionBridge.GetMoveToGoal(botHandle, nativeBot);
        float[] subpathEnd = NativeCcsBotLocomotionBridge.GetSubpathGoal(nativeBot);
        string nativeState = NativeCcsBotLocomotionBridge.GetNativeStateName(botHandle);
        int nativeTask = NativeCcsBotLocomotionBridge.GetNativeTask(botHandle);
        int nativePathLen = NativeCcsBotLocomotionBridge.GetNativePathLength(botHandle);
        string weapon = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? string.Empty;
        float vx = pawn.AbsVelocity?.X ?? 0f;
        float vy = pawn.AbsVelocity?.Y ?? 0f;
        double speed2D = Math.Sqrt(vx * vx + vy * vy);

        var lastDec = _locomotionDriver.Arbitrator.GetLastDecision(bot.Slot);
        string movSource = lastDec != null ? $"{lastDec.WinningIntent.Source}:{lastDec.WinningIntent.Kind}" : "NONE";
        bool jumpActive = lastDec != null && (lastDec.WinningIntent.Buttons & BotLocomotionDriver.IN_JUMP) != 0;
        bool ucmdActive = _locomotionDriver.Arbitrator.GetActiveUsercmdHandle(bot.Slot) != 0;

        float[] canonicalGoal = activeWpArr.Length == 3 ? activeWpArr : session.LastGoalAfter;
        bool hasActiveLease = _openingCanaryGuard.LeaseManager.HasActiveLease(bot.Slot);

        // Path B: Se algum writer nativo/pós-arbitragem desviou o goal durante o tick (> 4u XY ou > 4u Z),
        // registra auditoria e restaura deterministicamente o goal canônico antes de fechar o tick.
        if (hasActiveLease && canonicalGoal.Length == 3 && goalEnd.Length == 3)
        {
            double dx = goalEnd[0] - canonicalGoal[0];
            double dy = goalEnd[1] - canonicalGoal[1];
            double dz = Math.Abs(goalEnd[2] - canonicalGoal[2]);
            double errXy = Math.Sqrt(dx * dx + dy * dy);
            if (errXy > 4.0 || dz > 4.0)
            {
                float[] driftedGoal = goalEnd;
                _openingCanaryGuard.LeaseManager.RecordGoalWriteAudit(
                    writerId: "UNKNOWN_POST_CANARY_WRITER",
                    tick: Server.TickCount,
                    roundId: roundId,
                    botSlot: bot.Slot,
                    tickPhase: "END_OF_TICK_VERIFY",
                    previousGoal: canonicalGoal,
                    newGoal: driftedGoal,
                    reason: $"POST_CANARY_GOAL_DRIFT_XY={errXy:F1}_Z={dz:F1}",
                    leaseActive: true,
                    writeAccepted: false,
                    writeSuppressed: false);

                var ccsBot = pawn.Bot;
                if (ccsBot != null)
                {
                    NativeCcsBotLocomotionBridge.ApplyIsolatedMoveTo(
                        bot,
                        ccsBot,
                        bot.Slot,
                        Server.TickCount,
                        canonicalGoal[0],
                        canonicalGoal[1],
                        canonicalGoal[2],
                        forceRepath: false,
                        isolateExternalBotState: true,
                        applyStepUpJumpImpulse: false);
                    goalEnd = NativeCcsBotLocomotionBridge.GetMoveToGoal(ccsBot.Handle);
                    _openingCanaryGuard.LeaseManager.RecordGoalWriteAudit(
                        writerId: "OPENING_ROUTE_CANARY",
                        tick: Server.TickCount,
                        roundId: roundId,
                        botSlot: bot.Slot,
                        tickPhase: "POST_ARBITRATION_ENFORCEMENT",
                        previousGoal: driftedGoal,
                        newGoal: goalEnd,
                        reason: "PATH_B_END_OF_TICK_RESTORE",
                        leaseActive: true,
                        writeAccepted: true,
                        writeSuppressed: false);
                }
            }
        }

        var rec = _openingCanaryGuard.LeaseManager.RecordTickVerification(
            tick: Server.TickCount,
            roundId: roundId,
            botSlot: bot.Slot,
            playerPseudonym: session.PlayerPseudonym,
            routeId: session.Route.RouteId,
            waypointIndex: session.WaypointIndex,
            activeWaypoint: activeWpArr,
            goalBeforeCanary: session.LastGoalBefore,
            goalAfterCanary: canonicalGoal,
            goalEndOfTick: goalEnd,
            subpathGoalEndOfTick: subpathEnd,
            movementSourceApplied: movSource,
            nativeState: nativeState,
            nativeTask: nativeTask,
            nativePathLength: nativePathLen,
            botStateIsolated: bot.HasBeenControlledByPlayerThisRound,
            weaponState: weapon,
            velocityXy: speed2D,
            jumpButtonActive: jumpActive,
            usercmdVectorActive: ucmdActive,
            tickOrderValid: true);

        session.LastGoalEndOfTick = goalEnd;
        session.LastNativeState = nativeState;
        session.LastUnauthorizedOverwrite = rec.UnauthorizedOverwriteDetected;
        }
    }

    private void UpdateOpeningRouteControlAndShadowTick(bool runShadowSampling)
    {
        if (_isFreezeTime || _currentPlan == null || IsEngineWarmup())
        {
            return;
        }

        int roundId = Math.Max(1, _ctScore + _trScore + 1);
        int tick = Server.TickCount;
        bool ctEnabled = OpeningRouteCanaryGuard.IsTeamEnabledForCanary(_openingCanaryGuard.Mode, "CT");
        bool trEnabled = OpeningRouteCanaryGuard.IsTeamEnabledForCanary(_openingCanaryGuard.Mode, "TR");
        bool ctScheduleCreated = HasCreatedTeamSchedule(roundId, "CT");
        bool trScheduleCreated = HasCreatedTeamSchedule(roundId, "TR");
        bool needCtSchedule = ctEnabled && !ctScheduleCreated && !_debugCaptureAdmissionClosed && roundId <= _debugLastAdmittedRoundId;
        bool needTrSchedule = trEnabled && !trScheduleCreated && !_debugCaptureAdmissionClosed && roundId <= _debugLastAdmittedRoundId;
        bool needCanaryScan = _openingCanaryGuard.Mode != CanaryTeamMode.Off && _openingCanaryGuard.LeaseManager.IsCanaryEnabled();
        bool anyTeamNeedsSchedule = needCtSchedule || needTrSchedule;
        bool anyActiveTeamSession = _openingCanaryGuard.GetSessionsForRound(roundId).Count > 0;
        if (!runShadowSampling && !needCanaryScan && !anyTeamNeedsSchedule && !anyActiveTeamSession)
        {
            return;
        }

        var allPlayers = Utilities.GetPlayers();
        var ctTeammates = new List<TeammatePositionSnapshot>(6);
        var tTeammates = new List<TeammatePositionSnapshot>(6);
        foreach (var p in allPlayers)
        {
            if (p == null || !p.IsValid || !p.IsBot || !p.PawnIsAlive) continue;
            var pp = p.PlayerPawn.Value;
            if (pp?.AbsOrigin == null) continue;
            var snap = new TeammatePositionSnapshot(
                p.Slot,
                pp.AbsOrigin.X, pp.AbsOrigin.Y, pp.AbsOrigin.Z,
                pp.AbsVelocity?.X ?? 0f, pp.AbsVelocity?.Y ?? 0f,
                _roleManager.GetBotRole(p)?.ToString() ?? string.Empty);
            if (p.TeamNum == 3) ctTeammates.Add(snap);
            else if (p.TeamNum == 2) tTeammates.Add(snap);
        }

        int? trBombCarrierSlot = null;
        foreach (var p in allPlayers)
        {
            if (p != null && p.IsValid && p.PawnIsAlive && p.TeamNum == 2 && BotLocomotionDriver.HasC4(p))
            {
                trBombCarrierSlot = p.Slot;
                break;
            }
        }

        int targetCandidatesChecked = 0;
        var ctCanaryCandidates = new List<CanaryCandidate>();
        var trCanaryCandidates = new List<CanaryCandidate>();

        foreach (var bot in allPlayers)
        {
            if (bot == null || !bot.IsValid || !bot.IsBot || bot.TeamNum < 2 || bot.TeamNum > 3)
            {
                continue;
            }

            var pawn = bot.PlayerPawn.Value;
            bool isAlive = bot.PawnIsAlive && pawn != null && pawn.AbsOrigin != null;
            float x = pawn?.AbsOrigin?.X ?? 0f;
            float y = pawn?.AbsOrigin?.Y ?? 0f;
            float z = pawn?.AbsOrigin?.Z ?? 0f;
            string weapon = pawn?.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? string.Empty;
            string teamStr = bot.TeamNum == 3 ? "CT" : "TR";
            bool teamEnabled = OpeningRouteCanaryGuard.IsTeamEnabledForCanary(_openingCanaryGuard.Mode, teamStr);
            bool teamNeedsSchedule = teamStr == "CT" ? needCtSchedule : needTrSchedule;
            bool shouldCollectCandidate = isAlive && (runShadowSampling || (needCanaryScan && teamNeedsSchedule));

            if (shouldCollectCandidate)
            {
                var role = _roleManager.GetBotRole(bot);
                var activePlan = bot.TeamNum == 3 ? _currentPlan : _currentTrPlan;
                if (activePlan.TryGetOrderForBot(bot.Slot, role, out var order))
                {
                    var spot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                    if (spot != null)
                    {
                        var valCtx = _spotTelemetryTracker?.BuildValidationContext(bot, pawn?.AbsOrigin)
                            ?? new UtilitySpotValidationContext
                            {
                                MapName = "de_mirage",
                                RequestedSide = bot.TeamNum == 3 ? "CT" : "TR",
                            };
                        var valOut = UtilitySpotAssignmentValidator.ValidateAndResolve(spot, valCtx, _mapProfileManager.CurrentProfile.Spots);
                        if (valOut.ApprovedSpot != null)
                        {
                            spot = valOut.ApprovedSpot;
                        }

                        string pseudoSlot = PositioningTransformerContract.PseudonymizePlayerSlot(bot.Slot, _positioningMatchId);
                        if (runShadowSampling)
                        {
                            bool createdOpening = _openingRouteTracker.TryRegisterAssignment(
                                roundId: roundId,
                                rawSlot: bot.Slot,
                                pseudonymizedSlot: pseudoSlot,
                                team: teamStr,
                                spotId: spot.Id,
                                startX: x, startY: y, startZ: z,
                                targetX: spot.X, targetY: spot.Y, targetZ: spot.Z,
                                spotRadius: 90.0f,
                                tick: tick,
                                isFreezeTime: _isFreezeTime);
                            if (createdOpening)
                            {
                                _openingRoutePlanner.TryPlanOpeningRouteForRound(
                                    roundId: roundId,
                                    rawSlot: bot.Slot,
                                    pseudonymizedSlot: pseudoSlot,
                                    team: teamStr,
                                    role: role?.ToString() ?? "Rotator",
                                    targetSpotId: spot.Id,
                                    spotSector: spot.Sector,
                                    startX: x, startY: y, startZ: z,
                                    targetX: spot.X, targetY: spot.Y, targetZ: spot.Z,
                                    tick: tick,
                                    out var shadowSuggestion);
                                _ = OpeningRoutePlannerGuard.OpeningRoutePlannerCannotAffectBotDecision(spot.Id, shadowSuggestion);
                            }
                        }

                        if (needCanaryScan && teamEnabled && teamNeedsSchedule)
                        {
                            double sinceFreezeEnd = _roundFreezeEndTime > 0 ? Math.Max(0.0, Server.CurrentTime - _roundFreezeEndTime) : (Server.CurrentTime - _positioningRoundStartTime);
                            bool isTr = teamStr == "TR";
                            bool isOpeningStartWindow = !_isBombPlanted &&
                                (isTr
                                    ? (!_isFreezeTime && _roundFreezeEndTime > 0 && sinceFreezeEnd <= 4.0)
                                    : (activePlan.CurrentPhase is RoundPhase.FreezeTime or RoundPhase.Staging || sinceFreezeEnd <= 6.0));
                            if (isOpeningStartWindow)
                            {
                                targetCandidatesChecked++;
                                string? soloCertRoute = isTr
                                    ? Environment.GetEnvironmentVariable("CSBOT_TR_SOLO_CERT_ROUTE")?.Trim()
                                    : null;
                                var candidateSpot = !string.IsNullOrEmpty(soloCertRoute)
                                    ? (_mapProfileManager.CurrentProfile?.Spots?.FirstOrDefault(s => string.Equals(s.Id, soloCertRoute, StringComparison.OrdinalIgnoreCase)) ?? spot)
                                    : spot;
                                bool allowSpot = OpeningRouteCanaryAllowlist.IsAllowlisted(teamStr, candidateSpot.Id);
                                string corr = isTr
                                    ? ClassifyTrCanaryCorridor(candidateSpot.Id)
                                    : ClassifyCtCanaryCorridor(candidateSpot.Id);
                                float anchorDist = isTr
                                    ? DistanceToTrCorridorAnchor(corr, x, y)
                                    : DistanceToCtCorridorAnchor(corr, x, y);
                                var cand = new CanaryCandidate(
                                    bot,
                                    candidateSpot,
                                    pseudoSlot,
                                    teamStr,
                                    role?.ToString() ?? "Rotator",
                                    x, y, z,
                                    BotLocomotionDriver.HasC4(bot),
                                    BombsiteParser.ResolveBombCarrierTargetSite(activePlan).ToString(),
                                    allowSpot ? corr : string.Empty,
                                    anchorDist);
                                if (isTr) trCanaryCandidates.Add(cand);
                                else ctCanaryCandidates.Add(cand);
                            }
                        }
                    }
                }
            }

            if (runShadowSampling)
            {
                _openingRouteTracker.UpdateTick(roundId, bot.Slot, tick, isAlive, x, y, z, weapon);
            }
        }

        // Agendamento independente por time: CT e TR no mesmo round, sem gate global.
        if (needCtSchedule && ctCanaryCandidates.Count > 0)
        {
            TryCreateTeamOpeningSchedule(roundId, tick, "CT", ctCanaryCandidates, ctTeammates, _openingCanaryGuard.MaxConcurrentCtLeases, trBombCarrierSlot);
        }
        if (needTrSchedule && trCanaryCandidates.Count > 0)
        {
            TryCreateTeamOpeningSchedule(roundId, tick, "TR", trCanaryCandidates, tTeammates, _openingCanaryGuard.MaxConcurrentTrLeases, trBombCarrierSlot);
        }

        // Passo 3-5 da ordem do tick: atualizar filas dos portais e aplicar hold passivo (<= 500 ms) aos seguidores Utility AI
        foreach (var qkv in _corridorQueuesByRound)
        {
            if (qkv.Key.RoundId != roundId) continue;
            var q = qkv.Value;
            var queueTeammates = string.Equals(q.Team, "TR", StringComparison.OrdinalIgnoreCase) ? tTeammates : ctTeammates;
            int activeSlot = q.CurrentReleasedSlot >= 0 ? q.CurrentReleasedSlot : q.LeaderSlot;
            if (activeSlot >= 0)
            {
                var activeSnap = queueTeammates.FirstOrDefault(t => t.RawSlot == activeSlot);
                var activeSession = _openingCanaryGuard.GetSessionForSlot(roundId, activeSlot);
                if (activeSnap != null)
                {
                    float distMoved = activeSession != null ? (float)activeSession.TraveledDistance : 0f;
                    int curArea = NavMeshGraph.Default?.ProjectPoint(activeSnap.X, activeSnap.Y, activeSnap.Z, 48f).AreaId ?? 0;
                    if (q.TryConfirmPortalCrossing(activeSlot, tick, curArea, q.PortalEntryArea, q.PortalExitArea, distMoved, distMoved))
                    {
                        _departureTraceEvents.Add(new { tick, roundId, ev = "portal_cleared", slot = activeSlot, group = q.ConflictGroup, dist_moved = Math.Round(distMoved, 1), area = curArea });
                        int? nextSlot = q.TryAdvanceQueue();
                        if (nextSlot.HasValue && q.CanRelease(nextSlot.Value, tick, queueTeammates))
                        {
                            q.MarkReleased(nextSlot.Value, tick);
                            _departureTraceEvents.Add(new { tick, roundId, ev = "follower_released", slot = nextSlot.Value, reason = "PREDECESSOR_PORTAL_CLEARED" });
                        }
                    }
                }
            }
        }

        foreach (var hkv in _passiveDepartureHolds)
        {
            if (hkv.Key.RoundId != roundId) continue;
            var hold = hkv.Value;
            if (hold.Released) continue;
            var uBot = Utilities.GetPlayerFromSlot(hold.BotSlot);
            bool contactOrDead = uBot == null || !uBot.IsValid || !uBot.PawnIsAlive || (uBot.PlayerPawn.Value?.Bot?.IsEnemyVisible ?? false) || _isBombPlanted;
            string hTeam = hkv.Key.Team;
            _corridorQueuesByRound.TryGetValue((roundId, hTeam, hold.ConflictGroup), out var q);
            var holdTeammates = hTeam == "TR" ? tTeammates : ctTeammates;
            bool queueReady = q == null || q.CanRelease(hold.BotSlot, tick, holdTeammates);
            bool maxHoldExpired = tick >= hold.ReleaseTick || (tick - hold.StartTick) >= 32; // <= 500 ms (32 ticks @ 64Hz)
            if (contactOrDead || queueReady || maxHoldExpired)
            {
                hold.Released = true;
                hold.ReleaseReason = contactOrDead ? "CONTACT_OR_DEAD" : (queueReady ? "PORTAL_CLEARED" : "MAX_HOLD_500MS_ELAPSED");
                q?.MarkReleased(hold.BotSlot, tick);
                _departureTraceEvents.Add(new { tick, roundId, ev = "follower_released", slot = hold.BotSlot, reason = hold.ReleaseReason });
            }
            else if (uBot != null && !_openingCanaryGuard.LeaseManager.HasActiveLease(hold.BotSlot))
            {
                _locomotionDriver.Arbitrator.PublishIntent(new MovementIntent
                {
                    BotSlot = hold.BotSlot,
                    BotName = uBot.PlayerName,
                    GameTick = tick,
                    CurrentTime = (float)Server.CurrentTime,
                    Source = MovementIntentSource.TeamDeparturePassiveHold,
                    Kind = MovementCommandKind.HoldStop,
                    IsStopping = true,
                    WaitDurationSeconds = 0.12f,
                    Reason = "TEAM_DEPARTURE_PASSIVE_HOLD",
                    ExpiresAtTime = (float)Server.CurrentTime + 0.08f,
                });
            }
        }

        // Libera seguidores Canary pendentes somente quando tick >= PlannedReleaseTick AND portal liberado
        foreach (var pkv in _pendingCanaryFollowers.ToList())
        {
            if (pkv.Key.RoundId != roundId) continue;
            var (cand, fa) = pkv.Value;
            string fTeam = pkv.Key.Team;
            _corridorQueuesByRound.TryGetValue((roundId, fTeam, fa.ConflictGroup), out var fq);
            bool predInterrupted = fa.PredecessorSlot.HasValue &&
                (_openingCanaryGuard.GetSessionForSlot(roundId, fa.PredecessorSlot.Value)?.IsFinished ?? false);
            if (predInterrupted && fa.PredecessorSlot.HasValue)
            {
                fq?.Remove(fa.PredecessorSlot.Value);
            }
            var faTeammates = fTeam == "TR" ? tTeammates : ctTeammates;
            bool portalReady = fq == null || fq.CanRelease(cand.Bot.Slot, tick, faTeammates);
            if (tick >= fa.PlannedReleaseTick && (portalReady || predInterrupted))
            {
                _pendingCanaryFollowers.Remove(pkv.Key);
                var teamSnaps = fTeam == "TR" ? tTeammates : ctTeammates;
                if (_openingCanaryGuard.TryStartCanaryForRound(
                    roundId: roundId, rawSlot: cand.Bot.Slot, playerPseudonym: cand.PseudoSlot,
                    team: cand.Team, role: cand.Role, targetSpotId: cand.Spot.Id, spotSector: cand.Spot.Sector,
                    startX: cand.X, startY: cand.Y, startZ: cand.Z, targetX: cand.Spot.X, targetY: cand.Spot.Y, targetZ: cand.Spot.Z,
                    tick: tick, isOpeningPhase: true, isBombPlanted: _isBombPlanted, hasC4: cand.HasC4,
                    planTargetBombsite: cand.PlanSite, teammates: teamSnaps, explicitStaggerMs: fa.StaggerMs, bombCarrierSlot: trBombCarrierSlot))
                {
                    fq?.MarkReleased(cand.Bot.Slot, tick);
                    var pawn = cand.Bot.PlayerPawn.Value;
                    var lease = _openingCanaryGuard.LeaseManager.GetActiveLeaseForSlot(cand.Bot.Slot);
                    if (lease != null) lease.OriginalState = NativeCcsBotLocomotionBridge.CaptureSnapshot(cand.Bot, pawn?.Bot);
                    var session = _openingCanaryGuard.GetSessionForSlot(roundId, cand.Bot.Slot);
                    if (session != null)
                    {
                        session.InferredCorridor = fa.InferredCorridor;
                        session.CorridorInferenceSource = fa.CorridorInferenceSource;
                        session.CorridorConfidenceName = fa.CorridorConfidence.ToString();
                        session.ActualReleaseTick = tick;
                        session.InitialDepartureCorridor = fa.InitialDepartureCorridor;
                        session.DownstreamConflictGroup = fa.DownstreamConflictGroup;
                        session.QueueId = fa.QueueId;
                        session.QueuePosition = fa.QueuePosition;
                        session.LeaderSlot = fa.LeaderSlot;
                        session.PredecessorClearTick = fq?.LastPortalClearTick;
                        session.ReleaseCondition = predInterrupted ? "PREDECESSOR_INTERRUPTED" : "PORTAL_CLEARED_AND_STAGGER";
                        EmitAssignmentLifecycleRecord(new OpeningAssignmentTerminalRecord
                        {
                            EventType = "OPENING_ASSIGNMENT_STATE_CHANGED",
                            AssignmentId = $"r{roundId}_{fTeam}_s{cand.Bot.Slot}",
                            RoundId = roundId,
                            Team = fTeam,
                            PlayerPseudonym = cand.PseudoSlot,
                            Destination = cand.Spot.Id,
                            RouteId = cand.Spot.Id,
                            RouteCertified = true,
                            RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
                            EffectiveControlMode = EffectiveControlMode.CANARY_CONTROLLED,
                            LifecycleState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED,
                            PreviousState = OpeningAssignmentLifecycleState.CANARY_PENDING,
                            NewState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED,
                            TerminalReason = "SESSION_STARTED",
                            PredecessorSlot = fa.PredecessorSlot,
                            QueueId = fa.QueueId,
                            ScheduledTick = tick,
                            PlannedReleaseTick = fa.PlannedReleaseTick,
                            ExpirationTick = tick,
                            ControllerCreated = true,
                            LeaseAcquired = true,
                            SessionId = session.SessionId,
                        });
                    }
                    _departureTraceEvents.Add(new { tick, roundId, ev = "FOLLOWER_RELEASED", slot = cand.Bot.Slot, pred = fa.PredecessorSlot, actual_release_tick = tick, planned_release_tick = fa.PlannedReleaseTick });
                }
                else
                {
                    EmitAssignmentLifecycleRecord(new OpeningAssignmentTerminalRecord
                    {
                        EventType = "OPENING_ASSIGNMENT_TERMINAL",
                        AssignmentId = $"r{roundId}_{fTeam}_s{cand.Bot.Slot}",
                        RoundId = roundId,
                        Team = fTeam,
                        PlayerPseudonym = cand.PseudoSlot,
                        Destination = cand.Spot.Id,
                        RouteId = cand.Spot.Id,
                        RouteCertified = true,
                        RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
                        EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
                        LifecycleState = OpeningAssignmentLifecycleState.CANCELLED_BEFORE_CONTROL,
                        TerminalReason = "SESSION_START_FAILED",
                        PredecessorSlot = fa.PredecessorSlot,
                        QueueId = fa.QueueId,
                        ScheduledTick = tick,
                        PlannedReleaseTick = fa.PlannedReleaseTick,
                        ExpirationTick = tick,
                        ControllerCreated = false,
                        LeaseAcquired = false,
                        SessionId = string.Empty,
                    });
                }
            }
            else if (_isBombPlanted || (_roundFreezeEndTime > 0 && (Server.CurrentTime - _roundFreezeEndTime) > 6.5))
            {
                _pendingCanaryFollowers.Remove(pkv.Key);
                EmitAssignmentLifecycleRecord(new OpeningAssignmentTerminalRecord
                {
                    EventType = "OPENING_ASSIGNMENT_TERMINAL",
                    AssignmentId = $"r{roundId}_{fTeam}_s{cand.Bot.Slot}",
                    RoundId = roundId,
                    Team = fTeam,
                    PlayerPseudonym = cand.PseudoSlot,
                    Destination = cand.Spot.Id,
                    RouteId = cand.Spot.Id,
                    RouteCertified = true,
                    RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
                    EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
                    LifecycleState = OpeningAssignmentLifecycleState.EXPIRED_BEFORE_CONTROL,
                    TerminalReason = "OPENING_WINDOW_EXPIRED",
                    PredecessorSlot = fa.PredecessorSlot,
                    QueueId = fa.QueueId,
                    ScheduledTick = tick,
                    PlannedReleaseTick = fa.PlannedReleaseTick,
                    ExpirationTick = tick,
                    ControllerCreated = false,
                    LeaseAcquired = false,
                    SessionId = string.Empty,
                });
            }
        }

        // Avalia todos os bots Canary ativos do round (1 a 5 slots independentes)
        foreach (var activeSession in _openingCanaryGuard.GetSessionsForRound(roundId))
        {
        if (activeSession != null && !activeSession.IsFinished)
        {
            var bot = Utilities.GetPlayerFromSlot(activeSession.RawSlot);
            if (bot != null && bot.IsValid && bot.IsBot)
            {
                var pawn = bot.PlayerPawn.Value;
                bool isAlive = bot.PawnIsAlive && pawn != null && pawn.AbsOrigin != null;
                float x = pawn?.AbsOrigin?.X ?? 0f;
                float y = pawn?.AbsOrigin?.Y ?? 0f;
                float z = pawn?.AbsOrigin?.Z ?? 0f;
                string weapon = pawn?.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? string.Empty;
                var role = _roleManager.GetBotRole(bot);
                var activePlan = bot.TeamNum == 3 ? _currentPlan : _currentTrPlan;
                bool isSoloCert = _openingCanaryGuard.Mode == CanaryTeamMode.TrSingle &&
                    !string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("CSBOT_TR_SOLO_CERT_ROUTE"));
                bool hasCurOrder = activePlan.TryGetOrderForBot(bot.Slot, role, out var curOrder);
                string curDest = isSoloCert
                    ? activeSession.OriginalDestination
                    : (hasCurOrder ? curOrder!.StagingSpotId : string.Empty);
                string curRole = isSoloCert ? activeSession.Role : (role?.ToString() ?? "Rotator");
                if (!isSoloCert && !string.IsNullOrEmpty(curDest) && !string.Equals(curDest, activeSession.OriginalDestination, StringComparison.OrdinalIgnoreCase))
                {
                    var reqSpot = _mapProfileManager.GetSpotById(curDest);
                    if (reqSpot != null)
                    {
                        var valCtx = _spotTelemetryTracker?.BuildValidationContext(bot, pawn?.AbsOrigin)
                            ?? new UtilitySpotValidationContext { MapName = "de_mirage", RequestedSide = bot.TeamNum == 3 ? "CT" : "TR" };
                        var valOut = UtilitySpotAssignmentValidator.ValidateAndResolve(reqSpot, valCtx, _mapProfileManager.CurrentProfile.Spots);
                        if (valOut.ApprovedSpot != null && string.Equals(valOut.ApprovedSpot.Id, activeSession.OriginalDestination, StringComparison.OrdinalIgnoreCase))
                        {
                            curDest = activeSession.OriginalDestination;
                        }
                    }
                }

                var curSpot = !string.IsNullOrEmpty(curDest) ? _mapProfileManager.GetSpotById(curDest) : null;
                float vx = pawn?.AbsVelocity?.X ?? 0f;
                float vy = pawn?.AbsVelocity?.Y ?? 0f;
                float speed2D = MathF.Sqrt(vx * vx + vy * vy);
                bool hasContact = pawn?.Bot?.IsEnemyVisible ?? false;
                double elapsedSinceFreezeEnd = _roundFreezeEndTime > 0 ? Math.Max(0.0, Server.CurrentTime - _roundFreezeEndTime) : (Server.CurrentTime - _positioningRoundStartTime);
                double maxOpeningWindow = Math.Max(22.0, activeSession.Route.DeadlineSeconds + 2.0);
                bool isOpeningPhase = !_isBombPlanted &&
                    (activePlan.CurrentPhase is RoundPhase.FreezeTime or RoundPhase.Staging
                     || elapsedSinceFreezeEnd <= maxOpeningWindow);
                bool hasC4 = BotLocomotionDriver.HasC4(bot);
                string curSector = activeSession.OriginalSector;
                var teamSnaps = !string.IsNullOrEmpty(Environment.GetEnvironmentVariable("CSBOT_TR_SOLO_CERT_ROUTE"))
                    ? new List<TeammatePositionSnapshot>()
                    : (bot.TeamNum == 3 ? ctTeammates : tTeammates);

                nint botHandle = pawn?.Bot?.Handle ?? 0;
                activeSession.LastGoalBefore = NativeCcsBotLocomotionBridge.GetMoveToGoal(botHandle, pawn?.Bot);

                bool immediateTrigger = !isAlive || !isOpeningPhase || _isBombPlanted || hasContact ||
                                        activeSession.PendingDamage || activeSession.PendingHostileUtility ||
                                        !_openingCanaryGuard.LeaseManager.IsCanaryEnabled() ||
                                        !string.Equals(curDest, activeSession.OriginalDestination, StringComparison.OrdinalIgnoreCase) ||
                                        !string.Equals(curRole, activeSession.Role, StringComparison.OrdinalIgnoreCase);

                int lastSlotEvalTick = _lastCanaryEvalTickBySlot.TryGetValue(bot.Slot, out int prevSlotTick) ? prevSlotTick : -100;
                bool shouldRunStepEval = immediateTrigger ||
                                         !activeSession.DispatchTick.HasValue ||
                                         activeSession.Route.TransitionWaypoints.Count > 0 ||
                                         (tick - lastSlotEvalTick) >= 4;

                if (shouldRunStepEval)
                {
                    if (_locomotionDriver.Arbitrator.TryConsumeAppliedCanaryJumpTick(bot.Slot, out int appliedJumpTick))
                    {
                        activeSession.TransitionExecutor.NotifyJumpPulseApplied(appliedJumpTick, inJumpObserved: true);
                    }

                    double dtMs = lastSlotEvalTick > 0
                        ? Math.Clamp((tick - lastSlotEvalTick) * (1000.0 / 64.0), 1000.0 / 64.0, 125.0)
                        : (1000.0 / 64.0);
                    _lastCanaryEvalTickBySlot[bot.Slot] = tick;

                    CorridorDepartureQueue? activeQueue = null;
                    if (!string.IsNullOrEmpty(activeSession.InferredCorridor))
                    {
                        _corridorQueuesByRound.TryGetValue((roundId, activeSession.Team, activeSession.InferredCorridor), out activeQueue);
                    }

                    var canaryDec = _openingCanaryGuard.EvaluateTick(
                        roundId: roundId,
                        rawSlot: bot.Slot,
                        tick: tick,
                        x: x, y: y, z: z,
                        speed2D: speed2D,
                        activeWeapon: weapon,
                        isAlive: isAlive,
                        isOpeningPhase: isOpeningPhase,
                        isBombPlanted: _isBombPlanted,
                        currentDestination: curDest,
                        currentSector: curSector,
                        currentRole: curRole,
                        hasContact: hasContact,
                        tookDamage: false,
                        hostileUtility: false,
                        hasC4: hasC4,
                        planTargetBombsite: BombsiteParser.ResolveBombCarrierTargetSite(activePlan).ToString(),
                        tickIntervalMs: dtMs,
                        teammates: teamSnaps,
                        teamSchedule: _fullTeamScheduleByRound.TryGetValue((roundId, activeSession.Team), out var teamSched) ? teamSched : null,
                        corridorQueue: activeQueue);

                    if (canaryDec.CanaryControlling && isAlive)
                    {
                        ApplyCanaryControllingTick(
                            bot, pawn, activeSession, tick,
                            canaryDec.CurrentWaypoint, canaryDec.WaypointChanged,
                            canaryDec.HoldingForStagger, canaryDec.ShouldSwitchToWeapon, canaryDec.KnifeAllowed,
                            canaryDec.RequireCrouch,
                            canaryDec.UseExactPortalSteering, canaryDec.ForbiddenNavAreas,
                            canaryDec.ShouldEmitJumpPulse, canaryDec.ShouldEmitAttackPulse,
                            weapon, curSpot, curOrder.Stance);
                    }
                    else
                    {
                        RestoreCanaryBotToUtilityAi(bot, roundId, tick, canaryDec.AbortOrCompletionReason);
                    }
                }
                else if (isAlive)
                {
                    var wps = activeSession.Route.OrderedWaypoints;
                    var curWp = (activeSession.RecoveryActive && activeSession.RecoveryWaypoint != null)
                        ? activeSession.RecoveryWaypoint
                        : (wps.Count > 0 ? wps[Math.Min(activeSession.WaypointIndex, wps.Count - 1)] : null);
                    double elapsedSec = Math.Max(0.0, (tick - activeSession.StartTick) / 64.0);
                    var tl = (activeSession.Route.TransitionWaypoints.Count > 0 && !string.IsNullOrEmpty(activeSession.Route.WeaponReadyWaypoint.Name))
                        ? activeSession.Route.WeaponReadyWaypoint
                        : (wps.Count > 1 ? wps[^2] : wps[0]);
                    double distToThreat = Math.Sqrt((x - tl.X) * (x - tl.X) + (y - tl.Y) * (y - tl.Y) + (z - tl.Z) * (z - tl.Z));
                    bool shouldSwitch = elapsedSec >= activeSession.Route.KnifeAllowedUntil || tick >= (activeSession.Route.WeaponSwitchTick - 8) || distToThreat <= 360.0;
                    bool knifeAllowed = !shouldSwitch && !activeSession.ThreatLineCrossed;
                    bool holdingStagger = tick < activeSession.Schedule.PlannedReleaseTick;

                    ApplyCanaryControllingTick(
                        bot, pawn, activeSession, tick,
                        curWp, waypointChanged: false,
                        holdingStagger, shouldSwitch, knifeAllowed,
                        requireCrouch: false,
                        useExactPortalSteering: false,
                        forbiddenAreas: GeometricTransitionCatalog.GetForbiddenNavAreasForCorridor(activeSession.Route.AllowedCorridor),
                        emitJumpPulse: false, emitAttackPulse: false,
                        weapon, curSpot, curOrder.Stance);
                }
            }
        }
        }

        if (_openingCanaryGuard.Mode != CanaryTeamMode.Off &&
            (_roundFreezeEndTime > 0 ? (Server.CurrentTime - _roundFreezeEndTime) : (Server.CurrentTime - _positioningRoundStartTime)) > 6.0)
        {
            if (ctEnabled && !ctScheduleCreated && ctCanaryCandidates.Count == 0)
            {
                _openingCanaryGuard.RecordNoEligibleRound(roundId, "CT", targetCandidatesChecked);
            }
            if (trEnabled && !trScheduleCreated && trCanaryCandidates.Count == 0)
            {
                _openingCanaryGuard.RecordNoEligibleRound(roundId, "TR", targetCandidatesChecked);
            }
        }
    }

    private void TryCreateTeamOpeningSchedule(
        int roundId,
        int tick,
        string team,
        IReadOnlyList<CanaryCandidate> candidates,
        IReadOnlyList<TeammatePositionSnapshot> teamSnapshots,
        int maxLeases,
        int? trBombCarrierSlot)
    {
        string normTeam = NormalizeAssignmentTeam(team);
        if (normTeam != "CT" && normTeam != "TR")
        {
            Console.WriteLine($"[CsBotManager] QUEUE_TEAM_CONTRACT_VIOLATION invalid_team={team}");
            return;
        }
        if (_debugCaptureAdmissionClosed || roundId > _debugLastAdmittedRoundId)
        {
            return;
        }
        if (HasCreatedTeamSchedule(roundId, normTeam))
        {
            DuplicateTeamScheduleAttempts++;
            _departureTraceEvents.Add(new { tick, roundId, team = normTeam, ev = "DUPLICATE_TEAM_SCHEDULE_CREATION_ATTEMPT" });
            return;
        }

        int targetBucketCount = normTeam == "TR" ? 3 : 4;
        if (_coveredCanaryCorridors.Count >= targetBucketCount)
        {
            _coveredCanaryCorridors.Clear();
        }

        var orderedCandidates = normTeam == "TR"
            ? candidates
                .OrderBy(c => string.IsNullOrEmpty(c.Corridor) ? 1 : 0)
                .ThenBy(c => _coveredCanaryCorridors.Contains(c.Corridor) ? 1 : 0)
                .ThenBy(c => c.AnchorDist)
                .ToList()
            : candidates
                .OrderBy(c => string.IsNullOrEmpty(c.Corridor) ? 1 : 0)
                .ThenBy(c => _coveredCanaryCorridors.Contains(c.Corridor) ? 1 : 0)
                .ThenBy(c => string.Equals(c.Spot.Id, "mid_window_right_deep", StringComparison.OrdinalIgnoreCase)
                           || string.Equals(c.Spot.Id, "b_forest_bench_hold_apps", StringComparison.OrdinalIgnoreCase)
                           || string.Equals(c.Spot.Id, "b_van_behind_apps_hold", StringComparison.OrdinalIgnoreCase) ? 0 : 1)
                .ThenBy(c => c.AnchorDist)
                .ToList();

        var staggerBySlot = new Dictionary<int, int>();
        var assignBySlot = new Dictionary<int, FullTeamDepartureAssignment>();
        if (maxLeases > 1)
        {
            var sched = new TeamOpeningRouteScheduler();
            var allowSet = orderedCandidates
                .Where(c => OpeningRouteCanaryAllowlist.IsAllowlisted(c.Team, c.Spot.Id))
                .Select(c => c.Spot.Id)
                .ToHashSet(StringComparer.OrdinalIgnoreCase);
            var schedInputs = orderedCandidates.Select(c =>
            {
                bool eligibleSpot = allowSet.Contains(c.Spot.Id);
                string cg = !eligibleSpot ? string.Empty : (c.Corridor switch
                {
                    "MID_WINDOW" => "WINDOW_ENTRY",
                    "B_MARKET" or "B_BENCH_VAN" => "MARKET_ENTRY",
                    "A_RAMP" => "A_RAMP_ENTRY",
                    "A_PALACE" => "PALACE_ENTRY",
                    "B_APPS" => "B_APPS_ENTRY",
                    _ => c.Team == "CT" ? "CT_SPAWN_EXIT" : "T_SPAWN_EXIT",
                });
                float dx = c.Spot.X - c.X;
                float dy = c.Spot.Y - c.Y;
                float dnorm = MathF.Sqrt(dx * dx + dy * dy);
                return new TeamOpeningBotCandidate
                {
                    BotSlot = c.Bot.Slot,
                    PlayerPseudonym = c.PseudoSlot,
                    Team = c.Team,
                    Role = c.Role,
                    Destination = c.Spot.Id,
                    Sector = c.Spot.Sector,
                    Bombsite = OpeningRouteCanaryGuard.GetRouteBombsite(c.Spot.Id, c.Spot.Sector),
                    RouteId = c.Spot.Id,
                    ConflictGroup = cg,
                    HasC4 = c.HasC4,
                    SpawnDistance = c.AnchorDist,
                    DeadlineSeconds = 18.0,
                    FirstDirectionX = dnorm > 1f ? dx / dnorm : 0f,
                    FirstDirectionY = dnorm > 1f ? dy / dnorm : 0f,
                    IsEligibleForCanary = eligibleSpot,
                    IneligibilityReason = eligibleSpot ? string.Empty : "UNCERTIFIED_ROUTE"
                };
            }).ToList();

            var fullSchedule = sched.ScheduleFullTeamDeparture(
                roundId, schedInputs, orderedCandidates[0].PlanSite, tick, maxLeases, allowSet,
                new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "tr_b_apps_kitchen_control" });
            _fullTeamScheduleByRound[(roundId, normTeam)] = fullSchedule;
            if (!TryMarkTeamScheduleCreated(roundId, normTeam))
            {
                DuplicateTeamScheduleAttempts++;
                _departureTraceEvents.Add(new { tick, roundId, team = normTeam, ev = "DUPLICATE_TEAM_SCHEDULE_CREATION_ATTEMPT" });
                return;
            }

            var selectedSet = new HashSet<int>();
            foreach (var a in fullSchedule.Assignments)
            {
                assignBySlot[a.BotSlot] = a;
                if (a.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED)
                {
                    selectedSet.Add(a.BotSlot);
                    staggerBySlot[a.BotSlot] = a.StaggerMs;
                }
                if (!a.ConflictGroup.StartsWith("ISOLATED_", StringComparison.Ordinal))
                {
                    string qTeam = normTeam;
                    if (!_corridorQueuesByRound.TryGetValue((roundId, qTeam, a.ConflictGroup), out var q))
                    {
                        q = new CorridorDepartureQueue(a.ConflictGroup, 110f, 500) { Team = qTeam };
                        _corridorQueuesByRound[(roundId, qTeam, a.ConflictGroup)] = q;
                    }
                    q.Enqueue(a.BotSlot);
                    if (a.StaggerMs == 0)
                    {
                        q.MarkReleased(a.BotSlot, tick);
                        _departureTraceEvents.Add(new { tick, roundId, team = normTeam, ev = "leader_released", slot = a.BotSlot, group = a.ConflictGroup });
                    }
                    else if (a.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED && a.PassiveHoldRequired)
                    {
                        _passiveDepartureHolds[(roundId, normTeam, a.BotSlot)] = new PassiveDepartureHold
                        {
                            RoundId = roundId,
                            BotSlot = a.BotSlot,
                            ConflictGroup = a.ConflictGroup,
                            StartTick = tick,
                            ReleaseTick = tick + (int)Math.Ceiling(a.PassiveHoldMs * 64.0 / 1000.0),
                            HoldReason = "QUEUE_WAIT_FOR_PREDECESSOR",
                        };
                        _departureTraceEvents.Add(new { tick, roundId, team = normTeam, ev = "follower_held", slot = a.BotSlot, mode = "UTILITY_AI_OBSERVED", group = a.ConflictGroup, max_ms = a.PassiveHoldMs });
                    }
                }
            }
            _departureTraceEvents.Add(new { tick, roundId, team = normTeam, ev = "schedule_created", total = fullSchedule.Assignments.Count, canary = fullSchedule.Assignments.Count(x => x.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED), utility = fullSchedule.Assignments.Count(x => x.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED) });
            PersistFullTeamDepartureRoundLog(roundId, fullSchedule);
            foreach (var a in fullSchedule.Assignments)
            {
                string assignId = $"r{roundId}_{normTeam}_s{a.BotSlot}";
                if (!_scheduledAssignments.Add($"{_runId}:{assignId}"))
                {
                    DuplicateScheduledAttempts++;
                    _departureTraceEvents.Add(new { tick, roundId, team = normTeam, ev = "DUPLICATE_SCHEDULED_EVENT_ATTEMPT", assignment_id = assignId });
                    continue;
                }
                EmitAssignmentLifecycleRecord(new OpeningAssignmentLifecycleRecord
                {
                    EventType = "OPENING_ASSIGNMENT_SCHEDULED",
                    AssignmentId = assignId,
                    RoundId = roundId,
                    Team = normTeam,
                    PlayerPseudonym = a.PlayerPseudonym,
                    Destination = a.Destination,
                    RouteId = a.RouteId,
                    RouteCertified = a.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED,
                    RequestedControlMode = a.ControlMode,
                    EffectiveControlMode = EffectiveControlMode.NONE,
                    LifecycleState = OpeningAssignmentLifecycleState.SCHEDULED,
                    TerminalReason = string.Empty,
                    PredecessorSlot = a.PredecessorSlot,
                    QueueId = a.QueueId,
                    ScheduledTick = tick,
                    PlannedReleaseTick = a.PlannedReleaseTick,
                    ExpirationTick = tick,
                    ControllerCreated = false,
                    LeaseAcquired = false,
                    SessionId = string.Empty,
                });
                if (a.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED)
                {
                    EmitAssignmentLifecycleRecord(new OpeningAssignmentTerminalRecord
                    {
                        EventType = "OPENING_ASSIGNMENT_TERMINAL",
                        AssignmentId = $"r{roundId}_{normTeam}_s{a.BotSlot}",
                        RoundId = roundId,
                        Team = normTeam,
                        PlayerPseudonym = a.PlayerPseudonym,
                        Destination = a.Destination,
                        RouteId = a.RouteId,
                        RouteCertified = false,
                        RequestedControlMode = TeamDepartureControlMode.UTILITY_AI_OBSERVED,
                        EffectiveControlMode = EffectiveControlMode.UTILITY_AI,
                        LifecycleState = OpeningAssignmentLifecycleState.UTILITY_AI_OBSERVED,
                        TerminalReason = string.IsNullOrWhiteSpace(a.FallbackReason) ? "UTILITY_AI_UNCERTIFIED_ROUTE" : a.FallbackReason,
                        PredecessorSlot = a.PredecessorSlot,
                        QueueId = a.QueueId,
                        ScheduledTick = tick,
                        PlannedReleaseTick = a.PlannedReleaseTick,
                        ExpirationTick = tick,
                        ControllerCreated = false,
                        LeaseAcquired = false,
                        SessionId = string.Empty,
                    });
                }
            }
            orderedCandidates = orderedCandidates.Where(c => selectedSet.Contains(c.Bot.Slot)).ToList();
        }

        int startedCount = 0;
        foreach (var cand in orderedCandidates)
        {
            if (_openingCanaryGuard.GetSessionsForRoundAndTeam(roundId, normTeam).Count >= maxLeases) break;
            if (assignBySlot.TryGetValue(cand.Bot.Slot, out var faPend) &&
                faPend.PredecessorSlot.HasValue &&
                tick < faPend.PlannedReleaseTick)
            {
                _pendingCanaryFollowers[(roundId, normTeam, cand.Bot.Slot)] = (cand, faPend);
                _departureTraceEvents.Add(new { tick, roundId, team = normTeam, ev = "RELEASE_WAIT_STARTED", slot = cand.Bot.Slot, pred = faPend.PredecessorSlot, planned_release_tick = faPend.PlannedReleaseTick });
                continue;
            }
            int explicitStagger = staggerBySlot.TryGetValue(cand.Bot.Slot, out int stMs) ? stMs : 0;
            if (_openingCanaryGuard.TryStartCanaryForRound(
                roundId: roundId,
                rawSlot: cand.Bot.Slot,
                playerPseudonym: cand.PseudoSlot,
                team: normTeam,
                role: cand.Role,
                targetSpotId: cand.Spot.Id,
                spotSector: cand.Spot.Sector,
                startX: cand.X, startY: cand.Y, startZ: cand.Z,
                targetX: cand.Spot.X, targetY: cand.Spot.Y, targetZ: cand.Spot.Z,
                tick: tick,
                isOpeningPhase: true,
                isBombPlanted: _isBombPlanted,
                hasC4: cand.HasC4,
                planTargetBombsite: cand.PlanSite,
                teammates: teamSnapshots,
                explicitStaggerMs: explicitStagger,
                bombCarrierSlot: trBombCarrierSlot))
            {
                startedCount++;
                _coveredCanaryCorridors.Add(cand.Corridor);
                var pawn = cand.Bot.PlayerPawn.Value;
                var lease = _openingCanaryGuard.LeaseManager.GetActiveLeaseForSlot(cand.Bot.Slot);
                if (lease != null)
                {
                    lease.OriginalState = NativeCcsBotLocomotionBridge.CaptureSnapshot(cand.Bot, pawn?.Bot);
                }
                var session = _openingCanaryGuard.GetSessionForSlot(roundId, cand.Bot.Slot);
                if (session != null && assignBySlot.TryGetValue(cand.Bot.Slot, out var fa))
                {
                    session.InferredCorridor = fa.InferredCorridor;
                    session.CorridorInferenceSource = fa.CorridorInferenceSource;
                    session.CorridorConfidenceName = fa.CorridorConfidence.ToString();
                    session.ActualReleaseTick = tick;
                    session.InitialDepartureCorridor = fa.InitialDepartureCorridor;
                    session.DownstreamConflictGroup = fa.DownstreamConflictGroup;
                    session.QueueId = fa.QueueId;
                    session.QueuePosition = fa.QueuePosition;
                    session.LeaderSlot = fa.LeaderSlot;
                    session.ReleaseCondition = "LEADER_IMMEDIATE";
                    EmitAssignmentLifecycleRecord(new OpeningAssignmentTerminalRecord
                    {
                        EventType = "OPENING_ASSIGNMENT_STATE_CHANGED",
                        AssignmentId = $"r{roundId}_{normTeam}_s{cand.Bot.Slot}",
                        RoundId = roundId,
                        Team = normTeam,
                        PlayerPseudonym = cand.PseudoSlot,
                        Destination = cand.Spot.Id,
                        RouteId = cand.Spot.Id,
                        RouteCertified = true,
                        RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
                        EffectiveControlMode = EffectiveControlMode.CANARY_CONTROLLED,
                        LifecycleState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED,
                        PreviousState = OpeningAssignmentLifecycleState.CANARY_PENDING,
                        NewState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED,
                        TerminalReason = "SESSION_STARTED",
                        PredecessorSlot = fa.PredecessorSlot,
                        QueueId = fa.QueueId,
                        ScheduledTick = tick,
                        PlannedReleaseTick = fa.PlannedReleaseTick,
                        ExpirationTick = tick,
                        ControllerCreated = true,
                        LeaseAcquired = true,
                        SessionId = session.SessionId,
                    });
                }
                var mode = _openingCanaryGuard.LeaseManager.GetIsolationMode();
                if (session != null && session.Route.OrderedWaypoints.Count > 0)
                {
                    var wp0 = session.Route.OrderedWaypoints[0];
                    _locomotionDriver.DispatchOpeningCanaryWaypoint(
                        cand.Bot,
                        wp0.X,
                        wp0.Y,
                        wp0.Z,
                        finalSpot: null,
                        hurry: true,
                        stance: EngagementStance.PASSIVE_HOLD);

                    if (mode == CanaryIsolationMode.LeaseIsolated || mode == CanaryIsolationMode.ExternalPluginsDisabled)
                    {
                        NativeCcsBotLocomotionBridge.ApplyIsolatedMoveTo(
                            cand.Bot,
                            pawn?.Bot,
                            cand.Bot.Slot,
                            tick,
                            wp0.X, wp0.Y, wp0.Z,
                            forceRepath: true,
                            isolateExternalBotState: mode == CanaryIsolationMode.LeaseIsolated);
                    }
                }
            }
        }

        if (startedCount > 0)
        {
            _openingCanaryGuard.MarkTeamRoundStarted(roundId, normTeam);
        }
    }

    private void ApplyCanaryControllingTick(
        CCSPlayerController bot,
        CCSPlayerPawn? pawn,
        ActiveCanarySession session,
        int tick,
        RouteWaypoint? currentWaypoint,
        bool waypointChanged,
        bool holdingForStagger,
        bool shouldSwitchToWeapon,
        bool knifeAllowed,
        bool requireCrouch,
        bool useExactPortalSteering,
        IReadOnlySet<int>? forbiddenAreas,
        bool emitJumpPulse,
        bool emitAttackPulse,
        string activeWeapon,
        TacticalSpot? curSpot,
        EngagementStance targetStance)
    {
        bool isKnife = activeWeapon.Contains("knife", StringComparison.OrdinalIgnoreCase) ||
                       activeWeapon.Contains("bayonet", StringComparison.OrdinalIgnoreCase);

        if (shouldSwitchToWeapon && isKnife)
        {
            _locomotionDriver.ForceEquipBestFirearm(bot);
        }
        else if (knifeAllowed && !shouldSwitchToWeapon && !isKnife)
        {
            _locomotionDriver.ForceEquipKnifeForCanary(bot);
        }

        if (holdingForStagger)
        {
            _locomotionDriver.HoldOpeningCanaryForStagger(bot, 0.06f);
        }
        else if (currentWaypoint != null)
        {
            session.LastGoalAfter = new[] { MathF.Round(currentWaypoint.X, 1), MathF.Round(currentWaypoint.Y, 1), MathF.Round(currentWaypoint.Z, 1) };
            var navState = _locomotionDriver.GetNavState(bot.Slot);
            bool targetDrifted = navState == null
                || navState.HoldDurationRemaining > 0f
                || MathF.Abs(navState.TargetX - currentWaypoint.X) > 12f
                || MathF.Abs(navState.TargetY - currentWaypoint.Y) > 12f;

            if (waypointChanged || targetDrifted)
            {
                bool isFinalSpot = curSpot != null && string.Equals(currentWaypoint.Name, curSpot.Id, StringComparison.OrdinalIgnoreCase);
                _locomotionDriver.DispatchOpeningCanaryWaypoint(
                    bot,
                    currentWaypoint.X,
                    currentWaypoint.Y,
                    currentWaypoint.Z,
                    finalSpot: isFinalSpot ? curSpot : null,
                    hurry: !shouldSwitchToWeapon,
                    stance: isFinalSpot ? targetStance : EngagementStance.PASSIVE_HOLD);
            }

            _locomotionDriver.ConfigureCanaryTransitionState(
                bot.Slot,
                hurry: !shouldSwitchToWeapon,
                forceCrouch: requireCrouch,
                useExactPortalSteering,
                forbiddenAreas,
                singleJumpPulseTick: emitJumpPulse ? tick : null,
                singleAttackPulseTick: emitAttackPulse ? tick : null);
        }
    }

    private void PersistFullTeamDepartureRoundLog(int roundId, FullTeamDepartureSchedule schedule)
    {
        try
        {
            string logDir = Path.Combine(ModuleDirectory, "logs");
            Directory.CreateDirectory(logDir);
            string roundsPath = Path.Combine(logDir, "full_team_departure_rounds.jsonl");
            var row = new
            {
                round = roundId,
                total_cts_planned = schedule.Assignments.Count,
                canary_controlled_count = schedule.Assignments.Count(a => a.ControlMode == TeamDepartureControlMode.CANARY_CONTROLLED),
                utility_observed_count = schedule.Assignments.Count(a => a.ControlMode == TeamDepartureControlMode.UTILITY_AI_OBSERVED),
                passive_holds_created = schedule.Assignments.Count(a => a.PassiveHoldRequired),
                assignments = schedule.Assignments
            };
            File.AppendAllText(roundsPath, System.Text.Json.JsonSerializer.Serialize(row) + "\n");
            string tracePath = Path.Combine(logDir, "short_round_departure_trace.json");
            File.WriteAllText(tracePath, System.Text.Json.JsonSerializer.Serialize(_departureTraceEvents, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
        }
        catch { }
    }

    private readonly HashSet<string> _terminatedAssignments = new(StringComparer.OrdinalIgnoreCase);
    private int _duplicateTerminalAttempts;
    public int DuplicateTerminalAttempts => _duplicateTerminalAttempts;

    public bool FinalizeAssignmentFromSession(ActiveCanarySession session, string terminalReason, int terminalTick)
    {
        if (session == null) return false;
        string normAssignTeam = NormalizeAssignmentTeam(session.Team);
        string assignId = !string.IsNullOrWhiteSpace(session.AssignmentId)
            ? session.AssignmentId
            : $"r{session.RoundId}_{normAssignTeam}_s{session.RawSlot}";
        string key = $"{_runId}:{assignId}";
        if (_terminatedAssignments.Contains(key))
        {
            _duplicateTerminalAttempts++;
            return false;
        }
        string reason = string.IsNullOrWhiteSpace(terminalReason) ? "ABORTED" : terminalReason;
        var lifeState = reason switch
        {
            "COMPLETED" => OpeningAssignmentLifecycleState.COMPLETED,
            "INTERRUPTED" => OpeningAssignmentLifecycleState.INTERRUPTED,
            _ => OpeningAssignmentLifecycleState.ABORTED,
        };
        return EmitAssignmentLifecycleRecord(new OpeningAssignmentLifecycleRecord
        {
            EventType = "OPENING_ASSIGNMENT_TERMINAL",
            AssignmentId = assignId,
            RoundId = session.RoundId,
            Team = normAssignTeam,
            PlayerPseudonym = session.PlayerPseudonym,
            Destination = session.OriginalDestination,
            RouteId = session.Route?.RouteId ?? session.OriginalDestination,
            RouteCertified = true,
            RequestedControlMode = TeamDepartureControlMode.CANARY_CONTROLLED,
            EffectiveControlMode = EffectiveControlMode.CANARY_CONTROLLED,
            LifecycleState = lifeState,
            PreviousState = OpeningAssignmentLifecycleState.CANARY_CONTROLLED,
            NewState = lifeState,
            TerminalReason = reason,
            PredecessorSlot = session.Schedule?.PredecessorSlot,
            QueueId = session.QueueId ?? string.Empty,
            ScheduledTick = session.StartTick,
            PlannedReleaseTick = session.Schedule?.PlannedReleaseTick ?? session.StartTick,
            ExpirationTick = terminalTick,
            TerminalTick = terminalTick,
            ControllerCreated = true,
            LeaseAcquired = true,
            SessionId = session.SessionId,
        });
    }

    private void EmitRunMarker(string eventType, bool cleanShutdown)
    {
        try
        {
            string logDir = Path.Combine(ModuleDirectory, "logs");
            Directory.CreateDirectory(logDir);
            string path = Path.Combine(logDir, "opening_assignment_lifecycle.jsonl");
            var obj = new
            {
                EventType = eventType,
                RunId = _runId,
                PluginInstanceId = _pluginInstanceId,
                ProcessId = _processId,
                DllSha256 = _dllSha256,
                StartedUtc = _runStartedUtc,
                FinishedUtc = cleanShutdown ? DateTime.UtcNow.ToString("O") : string.Empty,
                CanaryMode = _openingCanaryGuard.Mode.ToString(),
                CleanShutdown = cleanShutdown,
            };
            File.AppendAllText(path, System.Text.Json.JsonSerializer.Serialize(obj) + "\n");
        }
        catch { }
    }

    private bool EmitAssignmentLifecycleRecord(OpeningAssignmentLifecycleRecord rec)
    {
        try
        {
            if (rec.EventType == "OPENING_ASSIGNMENT_TERMINAL" && !_terminatedAssignments.Add($"{_runId}:{rec.AssignmentId}"))
            {
                _duplicateTerminalAttempts++;
                return false;
            }
            var enriched = rec with
            {
                RunId = _runId,
                PluginInstanceId = _pluginInstanceId,
                ProcessId = _processId,
                DllSha256 = _dllSha256,
                UtcTimestamp = DateTime.UtcNow.ToString("O"),
            };
            string logDir = Path.Combine(ModuleDirectory, "logs");
            Directory.CreateDirectory(logDir);
            string path = Path.Combine(logDir, "opening_assignment_lifecycle.jsonl");
            File.AppendAllText(path, System.Text.Json.JsonSerializer.Serialize(enriched) + "\n");
            return true;
        }
        catch
        {
            return false;
        }
    }

    private void FlushOpeningRouteSnapshot()
    {
        try
        {
            string logDir = Path.Combine(ModuleDirectory, "logs");
            Directory.CreateDirectory(logDir);
            string outPath = Path.Combine(logDir, "opening_routes_snapshot.json");
            var payload = new
            {
                total_opening_routes = _openingRouteTracker.TotalOpeningRoutesCreated,
                closed_routes_count = _openingRouteTracker.ClosedRoutes.Count,
                active_open_routes = _openingRouteTracker.ActiveOpenRoutes,
                accounting_residue = _openingRouteTracker.ComputeAccountingResidue(),
                post_opening_repaths = _openingRouteTracker.PostOpeningRepathCounts,
                unique_midround_repaths = _openingRouteTracker.UniqueMidroundRepaths,
                unique_recovery_repaths = _openingRouteTracker.UniqueRecoveryRepaths,
                unique_tactical_rotations = _openingRouteTracker.UniqueTacticalRotations,
                repeated_event_duplicates = _openingRouteTracker.RepeatedEventDuplicates,
                repaths_by_player_round = _openingRouteTracker.RepathsByPlayerRound.ToDictionary(kv => $"{kv.Key.RoundId}:{kv.Key.PlayerSlot}", kv => kv.Value),
                routes = _openingRouteTracker.ClosedRoutes,
            };
            File.WriteAllText(outPath, System.Text.Json.JsonSerializer.Serialize(payload, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
            _openingRoutePlanner.FlushJsonl(Path.Combine(logDir, "shadow_route_suggestions.jsonl"));
            _openingCanaryGuard.FlushJsonl(Path.Combine(logDir, "opening_canary_telemetry.jsonl"));
            File.WriteAllText(
                Path.Combine(logDir, "opening_canary_transition_events.json"),
                System.Text.Json.JsonSerializer.Serialize(_openingCanaryGuard.GetTransitionEvents(), new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
            _openingCanaryGuard.LeaseManager.FlushAuthorityArtifacts(logDir);
        }
        catch { }
    }
}
