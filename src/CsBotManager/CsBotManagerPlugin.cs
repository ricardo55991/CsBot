using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Modules.Commands;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

using CsTimer = CounterStrikeSharp.API.Modules.Timers.Timer;

namespace CsBotManager;

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

    private TacticalPlan _currentPlan = new();
    private int _currentRound = 0;
    private int _ctScore = 0;
    private int _trScore = 0;
    private bool _isFreezeTime = false;
    private bool _isBombPlanted = false;
    private float _roundFreezeEndTime = 0.0f;
    private CsTimer? _hudTimer;
    private CsTimer? _buyTimer;
    private CsTimer? _clockTimer;

    // Rastreamento de Loss Streaks reais (I-04E)
    private int _ctLossStreak = 1;
    private int _trLossStreak = 1;

    // Sequenciamento de requisições Ollama e timers seguros por round (F-001, F-002, F-003, F-006)
    private int _iglRequestSequence = 0;
    private CancellationTokenSource? _roundCts;
    private readonly List<CounterStrikeSharp.API.Modules.Timers.Timer> _activeRoundTimers = new();

    // Cache de renderização HTML da HUD a 1Hz (O-01)
    private string _cachedHudHtml = string.Empty;
    private int _cachedHumanSlot = -1;

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

    public override void Load(bool hotReload)
    {
        base.Load(hotReload);

        _mapProfileManager.LoadProfile(Server.MapName, ModuleDirectory);
        _microMoveEngine?.TryLoadMapModel(Server.MapName);

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
        _microMoveEngine = new MicroMoveEngine(_mapProfileManager, _roleManager)
        {
            TelemetryLogger = _telemetryLogger, CalloutSystem = _calloutSystem
        };
        _microMoveEngine.TryLoadMapModel(Server.MapName);

        _locomotionDriver.PlantController = _clearAndPlantController;
        _locomotionDriver.RetakeBrain = _retakeAndDefuseBrain;
        _locomotionDriver.MicroMoveEngine = _microMoveEngine;
        _locomotionDriver.SetPlugin(this);

        RegisterListener<Listeners.OnMapStart>(mapName =>
        {
            _mapProfileManager.LoadProfile(mapName, ModuleDirectory);
            _microMoveEngine?.TryLoadMapModel(mapName);
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
        _voiceBridge.Start();

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

        Server.PrintToConsole("[CsBotManager] Plugin Fase 4.1 (Locomoção Nativa NavMesh, Thread Safety & Economia Total) inicializado!");
    }

    public override void Unload(bool hotReload)
    {
        _voiceBridge?.Stop();
        _roundCts?.Cancel();
        _roundCts?.Dispose();
        _roundCts = null;
        ClearRoundTimers();
        _locomotionDriver.ResetRound();
        base.Unload(hotReload);
    }

    private void OnTick()
    {
        float currentTime = Server.CurrentTime;
        _locomotionDriver.UpdateTick(currentTime);

        if (!_isFreezeTime)
        {
            var aliveBots = Utilities.GetPlayers().Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive).ToList();
            _mobilityController?.UpdateTick(currentTime, _currentPlan, aliveBots);
            _combatAdapter?.UpdateTick(currentTime, aliveBots);
        }

        // O-01: Exibe o cache HTML a 64Hz sem alocações contínuas de strings
        if (!string.IsNullOrEmpty(_cachedHudHtml) && _cachedHumanSlot != -1)
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
        _currentRound++;
        _isFreezeTime = true;
        _isBombPlanted = false;

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
        _intentTracker?.OnRoundStart();
        _utilityCoordinator?.OnRoundStart();
        _calloutSystem?.OnRoundStart();
        _clearAndPlantController?.OnRoundStart();
        _retakeAndDefuseBrain?.OnRoundStart();
        _trPivotController?.OnRoundStart();
        _economyManager.OnRoundStart();
        _mobilityController?.OnRoundStart();
        _combatAdapter?.OnRoundStart();

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
                // C-04A: Captura os valores na Game Thread antes de despachar para o Task.Run
                string mapName = Server.MapName;
                CsTeam capturedHumanTeam = humanTeam;
                int capturedRound = _currentRound;
                int capturedMoney = _economyManager.TeamAverageMoney;
                int capturedHumanSlot = human?.Slot ?? -1;
                var currentBuyState = _economyManager.CurrentBuyState;

                int requestSeq = Interlocked.Increment(ref _iglRequestSequence);
                var token = _roundCts?.Token ?? CancellationToken.None;

                Task.Run(async () =>
                {
                    TacticalPlan plan;
                    try
                    {
                        plan = await _iglService.GetTacticalDecisionAsync(
                            mapName,
                            capturedHumanTeam,
                            currentBuyState,
                            capturedRound,
                            capturedMoney,
                            null,
                            false,
                            _mapProfileManager,
                            token);
                    }
                    catch (OperationCanceledException)
                    {
                        return;
                    }

                    // C-04B: Retorna para a Game Thread e revalida os ponteiros
                    Server.NextFrame(() =>
                    {
                        if (capturedRound != _currentRound || requestSeq != _iglRequestSequence)
                        {
                            return;
                        }

                        var freshPlayers = GetActivePlayers();
                        var freshHuman = freshPlayers.FirstOrDefault(p => p.Slot == capturedHumanSlot && !p.IsBot);
                        var freshCtBots = freshPlayers.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
                        var freshTrBots = freshPlayers.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();
                        var freshTeamBots = freshPlayers.Where(p => p.Team == capturedHumanTeam && p.IsBot).ToList();

                        _currentPlan = plan;
                        _currentPlan.PlayTier = tacticalDecision.Tier;
                        _currentPlan.PlayId = tacticalDecision.PlayId;
                        _currentPlan.CurrentPhase = RoundPhase.FreezeTime;

                        // C-03: Re-aplica automaticamente posição travada do humano se existir
                        if (_roleManager.IsHumanPositionLocked && freshHuman != null && !string.IsNullOrEmpty(_roleManager.LockedSectorName))
                        {
                            _roleManager.ClaimPositionForPlayer(freshHuman, _roleManager.LockedSectorName, freshTeamBots, _currentPlan, _mapProfileManager);
                        }

                        _ctController?.OnRoundStart(_currentPlan, freshCtBots);
                        _midRoundAdapter?.OnRoundStart(_currentPlan, freshTrBots, freshHuman);

                        UtilityAndClockCoordinator.PrintTeamChat(capturedHumanTeam, iglName, $"⚡ Tática: {plan.TacticName} | {plan.TacticSummary}");
                    });
                });
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

            // Telemetria Forense: Registra resumo inicial completo do round (F-013 / Bloco 8.3)
            _telemetryLogger?.OnRoundStart(
                _currentRound,
                _ctScore,
                _trScore,
                humanTeam == CsTeam.CounterTerrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                humanTeam == CsTeam.Terrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                _currentPlan,
                _currentPlan != null ? _currentPlan.RawJson : string.Empty,
                players);

            if (human != null && _currentPlan != null)
            {
                human.PrintToChat($" {ChatColors.Green}[CsBot IGL]{ChatColors.Default} Tática: {ChatColors.Gold}{_currentPlan.TacticName}{ChatColors.Default} | Ritmo: {ChatColors.LightBlue}{_currentPlan.RoundTempo}{ChatColors.Default}!");
            }

            // 11.5s: Disciplina da C4 no Freeze Time (Parte A - Item 2 / Bloco 5.3)
            AddRoundTimer(0.5f, () =>
            {
                var curPlayers = GetActivePlayers();
                var curHuman = curPlayers.FirstOrDefault(p => !p.IsBot);
                var curTrBots = curPlayers.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();
                _economyManager.EnforceC4Discipline(curTrBots, curHuman, _roleManager);
            });
        });

        return HookResult.Continue;
    }

    private HookResult OnRoundFreezeEnd(EventRoundFreezeEnd @event, GameEventInfo info)
    {
        _isFreezeTime = false;
        _roundFreezeEndTime = Server.CurrentTime;

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

        var winner = (CsTeam)@event.Winner;
        string reason = @event.Reason.ToString();

        // I-04E: Atualiza loss streak e placar
        if (winner == CsTeam.CounterTerrorist)
        {
            _ctScore++;
            _ctLossStreak = Math.Max(1, _ctLossStreak - 1);
            _trLossStreak = Math.Min(5, _trLossStreak + 1);
        }
        else if (winner == CsTeam.Terrorist)
        {
            _trScore++;
            _trLossStreak = Math.Max(1, _trLossStreak - 1);
            _ctLossStreak = Math.Min(5, _ctLossStreak + 1);
        }

        _telemetryLogger?.LogEvent("FIM_ROUND", $"Round finalizado! Vencedor: {winner} | Motivo: {reason} | Placar atual: CT {_ctScore} x {_trScore} TR");
        _iglService.RecordRoundResult(_currentRound, winner, reason, null, _currentPlan.TacticName, _currentPlan.RoundTempo);
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

        var victim = @event.Userid;
        var attacker = @event.Attacker;
        if (victim != null && attacker != null && victim.IsValid && attacker.IsValid)
        {
            float dist = 0.0f;
            if (victim.PlayerPawn.Value?.AbsOrigin != null && attacker.PlayerPawn.Value?.AbsOrigin != null)
            {
                dist = (victim.PlayerPawn.Value.AbsOrigin - attacker.PlayerPawn.Value.AbsOrigin).Length();
            }
            _telemetryLogger?.LogCombat(attacker, victim, @event.Weapon ?? "arma", @event.DmgHealth, @event.Health, dist);
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
            _locomotionDriver.AlertNearbyTeammatesOfThreat(killer.PlayerPawn.Value.AbsOrigin, victim.Slot, victim.Team, 1100f);
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

        if (victim != null && killer != null && victim.IsValid && killer.IsValid)
        {
            string sector = "Transição";
            if (victim.PlayerPawn.Value?.AbsOrigin != null)
            {
                var cp = _mapProfileManager.FindChokepointAt(victim.PlayerPawn.Value.AbsOrigin.X, victim.PlayerPawn.Value.AbsOrigin.Y, victim.PlayerPawn.Value.AbsOrigin.Z);
                sector = cp?.Name ?? "Transição";
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

        player.PrintToChat($" {ChatColors.LightBlue}[CsBot IGL]{ChatColors.Default} Processando call com IA: \"{call}\"...");

        // C-04A: Captura dados da engine na Game Thread
        string mapName = Server.MapName;
        CsTeam pTeam = player.Team;
        int pSlot = player.Slot;
        int capturedRound = _currentRound;
        int capturedMoney = _economyManager.TeamAverageMoney;
        var buyState = _economyManager.CurrentBuyState;
        int requestSeq = Interlocked.Increment(ref _iglRequestSequence);
        var token = _roundCts?.Token ?? CancellationToken.None;

        Task.Run(async () =>
        {
            TacticalPlan newPlan;
            try
            {
                newPlan = await _iglService.GetTacticalDecisionAsync(
                    mapName,
                    pTeam,
                    buyState,
                    capturedRound,
                    capturedMoney,
                    call,
                    false,
                    _mapProfileManager,
                    token);
            }
            catch (OperationCanceledException)
            {
                return;
            }

            // C-04B: Revalida na Game Thread
            Server.NextFrame(() =>
            {
                if (capturedRound != _currentRound || requestSeq != _iglRequestSequence)
                {
                    return;
                }

                var targetPlayer = Utilities.GetPlayerFromSlot(pSlot);
                _currentPlan = newPlan;
                _currentPlan.CurrentPhase = _isFreezeTime ? RoundPhase.FreezeTime : RoundPhase.Staging;

                if (targetPlayer != null && targetPlayer.IsValid)
                {
                    targetPlayer.PrintToChat($" {ChatColors.Green}[CsBot IGL]{ChatColors.Default} Call adaptada: {ChatColors.Gold}{_currentPlan.TacticName}{ChatColors.Default} | Ritmo: {ChatColors.LightBlue}{_currentPlan.RoundTempo}{ChatColors.Default}!");
                }
            });
        });
    }

    [ConsoleCommand("css_rejeitar", "Pede uma tatica alternativa para a IA")]
    public void CommandRejeitar(CCSPlayerController? player, CommandInfo info)
    {
        if (player == null || !player.IsValid) return;

        player.PrintToChat($" {ChatColors.Yellow}[CsBot IGL]{ChatColors.Default} Tática rejeitada. Gerando plano alternativo com IA...");

        // C-04A: Captura dados da engine na Game Thread
        string mapName = Server.MapName;
        CsTeam pTeam = player.Team;
        int pSlot = player.Slot;
        int capturedRound = _currentRound;
        int capturedMoney = _economyManager.TeamAverageMoney;
        var buyState = _economyManager.CurrentBuyState;
        int requestSeq = Interlocked.Increment(ref _iglRequestSequence);
        var token = _roundCts?.Token ?? CancellationToken.None;

        Task.Run(async () =>
        {
            TacticalPlan newPlan;
            try
            {
                newPlan = await _iglService.GetTacticalDecisionAsync(
                    mapName,
                    pTeam,
                    buyState,
                    capturedRound,
                    capturedMoney,
                    null,
                    true,
                    _mapProfileManager,
                    token);
            }
            catch (OperationCanceledException)
            {
                return;
            }

            // C-04B: Revalida na Game Thread
            Server.NextFrame(() =>
            {
                if (capturedRound != _currentRound || requestSeq != _iglRequestSequence)
                {
                    return;
                }

                var targetPlayer = Utilities.GetPlayerFromSlot(pSlot);
                _currentPlan = newPlan;
                _currentPlan.CurrentPhase = _isFreezeTime ? RoundPhase.FreezeTime : RoundPhase.Staging;

                if (targetPlayer != null && targetPlayer.IsValid)
                {
                    targetPlayer.PrintToChat($" {ChatColors.Green}[CsBot IGL]{ChatColors.Default} Nova tática: {ChatColors.Gold}{_currentPlan.TacticName}{ChatColors.Default} | Ritmo: {ChatColors.LightBlue}{_currentPlan.RoundTempo}{ChatColors.Default}!");
                }
            });
        });
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
        if (claimed)
        {
            // Move os bots afetados
            foreach (var bot in teamBots)
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

    private List<CCSPlayerController> GetActivePlayers()
    {
        return Utilities.GetPlayers()
            .Where(p => p != null && p.IsValid && !p.IsHLTV)
            .ToList();
    }
}
