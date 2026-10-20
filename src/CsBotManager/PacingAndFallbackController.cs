using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

using CsTimer = CounterStrikeSharp.API.Modules.Timers.Timer;

namespace CsBotManager;

public class PacingAndFallbackController
{
    private readonly CsBotManagerPlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly BotLocomotionDriver _locomotionDriver;

    private TacticalPlan? _currentPlan;
    private CsTimer? _stagingTimer;
    private float _stagingTimeRemaining = 0.0f;
    private bool _isExecuting = false;
    private readonly Random _random = new();

    public float StagingTimeRemaining => _stagingTimeRemaining;
    public bool IsExecuting => _isExecuting;
    public Action<TacticalPlan>? OnExecuteStarted { get; set; }

    public PacingAndFallbackController(
        CsBotManagerPlugin plugin,
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        BotLocomotionDriver locomotionDriver)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _locomotionDriver = locomotionDriver;
    }

    public void OnRoundFreezeEnd(TacticalPlan plan, List<CCSPlayerController> teamBots, List<CCSPlayerController> enemyBots)
    {
        _currentPlan = plan;
        _stagingTimer?.Kill();
        _stagingTimer = null;

        // C-01B: Despacha movimentação física via NavMesh para a equipe adversária (enemyBots)
        foreach (var enemyBot in enemyBots)
        {
            if (!enemyBot.IsValid || !enemyBot.PawnIsAlive) continue;
            var enemySpot = _roleManager.GetEnemyBotSpot(enemyBot.Slot);
            if (enemySpot != null)
            {
                _locomotionDriver.NavigateToSpot(enemyBot, enemySpot, hurry: false, enemySpot.RecommendedStance);
            }
        }

        if (plan.RoundTempo == RoundTempo.FAST_CONTACT || plan.StagingDurationSeconds <= 0)
        {
            _currentPlan.CurrentPhase = RoundPhase.Executing;
            _isExecuting = true;
            _stagingTimeRemaining = 0.0f;

            Server.PrintToChatAll($" {ChatColors.Red}[CsBot Maestro]{ChatColors.Default} Ritmo: {ChatColors.Gold}FAST CONTACT{ChatColors.Default}! Invasão imediata sem staging!");
            ApplyExecuteOrders(teamBots);
            return;
        }

        _currentPlan.CurrentPhase = RoundPhase.Staging;
        _isExecuting = false;
        _stagingTimeRemaining = plan.StagingDurationSeconds;

        // C-01A: Despacha movimentação física via NavMesh para os bots aliados (teamBots) até seus StagingSpots
        foreach (var bot in teamBots)
        {
            if (!bot.IsValid || !bot.PawnIsAlive) continue;
            var role = _roleManager.GetBotRole(bot);
            if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
            {
                var stagingSpot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                if (stagingSpot != null)
                {
                    _locomotionDriver.NavigateToSpot(bot, stagingSpot, hurry: false, order.Stance);
                }
            }
        }

        // Marcação de Costas (Anti-Rush) no TR
        var firstBot = teamBots.FirstOrDefault(b => b.PawnIsAlive);
        if (firstBot != null && firstBot.Team == CsTeam.Terrorist && teamBots.Count >= 2 && _random.Next(100) < 75)
        {
            var flankBot = teamBots.FirstOrDefault(b => _roleManager.GetBotRole(b) == BotRole.Anchor) ?? teamBots.Last();
            var role = _roleManager.GetBotRole(flankBot);
            if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
            {
                order.IsWatchingFlank = true;
                order.Stance = EngagementStance.PASSIVE_HOLD;
                plan.IsFlankCoverActive = true;
                UtilityAndClockCoordinator.PrintTeamChat(CsTeam.Terrorist, flankBot.PlayerName, "Vou segurar as costas contra avanço/rush CT! Podem alinhar as utilitárias!");
            }
        }

        Server.PrintToChatAll($" {ChatColors.Green}[CsBot Maestro]{ChatColors.Default} Fase de Staging Iniciada ({_stagingTimeRemaining:F0}s). Aguardando confirmações e utilitárias!");

        // Loop de verificação a cada 1 segundo
        _stagingTimer = _plugin.AddTimer(1.0f, () =>
        {
            _stagingTimeRemaining -= 1.0f;

            if (_stagingTimeRemaining <= 0)
            {
                TriggerExecute("Tempo de Staging concluído", teamBots);
            }
        }, TimerFlags.REPEAT);
    }

    public void TriggerExecute(string reason, List<CCSPlayerController> teamBots)
    {
        if (_isExecuting) return;

        _stagingTimer?.Kill();
        _stagingTimer = null;
        _isExecuting = true;
        _stagingTimeRemaining = 0.0f;

        if (_currentPlan != null)
        {
            _currentPlan.CurrentPhase = RoundPhase.Executing;
            OnExecuteStarted?.Invoke(_currentPlan);

            // Sincronização física real de utilitárias via BotLocomotionDriver (C-01E, C-02A)
            foreach (var bot in teamBots.Where(b => b.PawnIsAlive))
            {
                var role = _roleManager.GetBotRole(bot);
                if (role != null && _currentPlan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                {
                    if (!order.IsWatchingFlank)
                    {
                        // 45 = Smoke, 46/48 = Molotov
                        _locomotionDriver.ThrowUtility(bot, 45);
                    }
                }
            }

            _plugin.AddRoundTimer(0.8f, () =>
            {
                var flasher = teamBots.FirstOrDefault(b => b.PawnIsAlive);
                if (flasher != null)
                {
                    _locomotionDriver.ThrowUtility(flasher, 43); // 43 = Flashbang
                    UtilityAndClockCoordinator.PrintTeamChat(flasher.Team, flasher.PlayerName, "Granadas lançadas em sincronia! Entrem colados no estouro da flash!");
                }
            });
        }

        Server.PrintToChatAll($" {ChatColors.Gold}[CsBot Maestro]{ChatColors.Default} ⚡ {ChatColors.Green}EXECUTE DISPARADO!{ChatColors.Default} ({reason}) Avanço total para os bombsites!");

        ApplyExecuteOrders(teamBots);
    }

    public void HandlePlayerHurt(EventPlayerHurt @event, List<CCSPlayerController> teamBots)
    {
        var victim = @event.Userid;
        if (victim == null || !victim.IsValid || !victim.IsBot || !victim.PawnIsAlive) return;

        var role = _roleManager.GetBotRole(victim);
        if (role == null || _currentPlan == null) return;

        string key = RoleManager.GetOrderKey(role.Value);
        if (!_currentPlan.BotOrders.TryGetValue(key, out var order)) return;

        if (order.IsFallingBack) return;

        if (_currentPlan.IsClockDesperationActive && victim.Team == CsTeam.Terrorist)
        {
            return;
        }

        int currentHp = @event.Health;
        bool isOneAndDone = order.Stance == EngagementStance.ONE_AND_DONE;
        bool isLowHp = currentHp < 55;

        if (isOneAndDone || isLowHp)
        {
            order.IsFallingBack = true;
            order.Stance = EngagementStance.PASSIVE_HOLD;

            var fallbackSpot = _mapProfileManager.GetFallbackSpot(order.StagingSpotId) ??
                               _mapProfileManager.GetSpotById(order.FallbackSpotId) ??
                               _mapProfileManager.GetFallbackSpot(order.ExecuteSpotId);

            string spotName = fallbackSpot?.Name ?? "cobertura segura";

            if (isOneAndDone)
            {
                Server.PrintToChatAll($" {ChatColors.Yellow}[CsBot One&Done]{ChatColors.Default} {victim.PlayerName} disparou de surpresa e recuou com vida para {ChatColors.Gold}{spotName}{ChatColors.Default}!");
            }
            else
            {
                Server.PrintToChatAll($" {ChatColors.Red}[CsBot Sobrevivência]{ChatColors.Default} {victim.PlayerName} tomou dano ({currentHp} HP) e recuou para {ChatColors.Gold}{spotName}{ChatColors.Default}!");
            }

            // C-01C: Recuo físico via NavMesh no lugar de Teleport()
            if (fallbackSpot != null)
            {
                _locomotionDriver.NavigateToSpot(victim, fallbackSpot, hurry: true, EngagementStance.PASSIVE_HOLD);
            }
        }
    }

    public void ResetRound()
    {
        _stagingTimer?.Kill();
        _stagingTimer = null;
        _isExecuting = false;
        _stagingTimeRemaining = 0.0f;
    }

    private void ApplyExecuteOrders(List<CCSPlayerController> teamBots)
    {
        if (_currentPlan == null) return;

        foreach (var bot in teamBots)
        {
            if (!bot.IsValid || !bot.PawnIsAlive) continue;
            var role = _roleManager.GetBotRole(bot);
            if (role != null)
            {
                string key = RoleManager.GetOrderKey(role.Value);
                if (_currentPlan.BotOrders.TryGetValue(key, out var order))
                {
                    if (!order.IsFallingBack)
                    {
                        order.Stance = EngagementStance.AGGRESSIVE_POKE;
                        var execSpot = _mapProfileManager.GetSpotById(order.ExecuteSpotId);
                        // C-01C: Avanço físico via NavMesh no lugar de Teleport()
                        if (execSpot != null)
                        {
                            _locomotionDriver.NavigateToSpot(bot, execSpot, hurry: true, EngagementStance.AGGRESSIVE_POKE);
                        }
                    }
                }
            }
        }
    }
}
