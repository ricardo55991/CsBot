using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class MobilityController
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly BotLocomotionDriver _locomotionDriver;

    // Estado da faca e histórico de perigo por slot de bot
    private readonly Dictionary<int, bool> _isKnifeDrawn = new();
    private readonly Dictionary<int, float> _lastDangerTime = new();
    private float _lastCheckTime = 0.0f;

    public MobilityController(BasePlugin plugin, MapProfileManager mapProfileManager, BotLocomotionDriver locomotionDriver)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _locomotionDriver = locomotionDriver;
    }

    public void OnRoundStart()
    {
        _isKnifeDrawn.Clear();
        _lastDangerTime.Clear();
        _lastCheckTime = 0.0f;
    }

    public void RegisterDanger(int botSlot)
    {
        _lastDangerTime[botSlot] = Server.CurrentTime;

        if (_isKnifeDrawn.TryGetValue(botSlot, out bool drawn) && drawn)
        {
            _isKnifeDrawn[botSlot] = false;
            var bot = Utilities.GetPlayerFromSlot(botSlot);
            if (bot != null && bot.IsValid && bot.PawnIsAlive)
            {
                EquipCombatWeapon(bot);
            }
        }
    }

    public void OnPlayerHurt(EventPlayerHurt @event)
    {
        if (@event.Userid != null && @event.Userid.IsValid && @event.Userid.IsBot)
        {
            RegisterDanger(@event.Userid.Slot);
        }
        if (@event.Attacker != null && @event.Attacker.IsValid && @event.Attacker.IsBot)
        {
            RegisterDanger(@event.Attacker.Slot);
        }
    }

    public void OnPlayerFootstep(EventPlayerFootstep @event)
    {
        var walker = @event.Userid;
        if (walker == null || !walker.IsValid || walker.PlayerPawn.Value?.AbsOrigin == null) return;

        var footstepPos = walker.PlayerPawn.Value.AbsOrigin;
        float now = Server.CurrentTime;

        // Avisa perigo aos bots inimigos próximos ao passo (<= 750 unidades)
        var allPlayers = Utilities.GetPlayers();
        foreach (var player in allPlayers)
        {
            if (player == null || !player.IsValid || !player.IsBot || !player.PawnIsAlive || player.Team == walker.Team) continue;
            var botPos = player.PlayerPawn.Value?.AbsOrigin;
            if (botPos == null) continue;

            float dist = (botPos - footstepPos).Length();
            if (dist <= 750.0f)
            {
                RegisterDanger(player.Slot);
            }
        }
    }

    // =========================================================================
    // CICLO DE MOBILIDADE INTELIGENTE COM FACA & FREIO TÁTICO (MÓDULO 3)
    // =========================================================================
    public void UpdateTick(float currentTime, TacticalPlan plan, List<CCSPlayerController> aliveBots)
    {
        // Throttling de checagem a ~6Hz para poupar ciclos de CPU
        if (currentTime - _lastCheckTime < 0.16f) return;
        _lastCheckTime = currentTime;

        foreach (var bot in aliveBots)
        {
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive || !bot.IsBot) continue;

            var pawn = bot.PlayerPawn.Value;
            if (pawn == null || pawn.AbsOrigin == null) continue;

            // Se for portador da C4 ou se estiver perto do plant/defuse, garante arma de combate em mãos
            if (BotLocomotionDriver.HasC4(bot) && plan.CurrentPhase == RoundPhase.Executing)
            {
                ApplyTacticalBrake(bot);
                continue;
            }

            var navState = _locomotionDriver.GetNavState(bot.Slot);
            if (navState == null || navState.HasReachedDestination || navState.HoldDurationRemaining > 0 || navState.Priority >= BotOrderPriority.High_CombatFallback)
            {
                // Parado, segurando hold ou em prioridade de combate/save/plant/defuse: nunca fica de faca na mão
                ApplyTacticalBrake(bot);
                continue;
            }

            var botPos = pawn.AbsOrigin;
            float dx = botPos.X - navState.TargetX;
            float dy = botPos.Y - navState.TargetY;
            float distToTarget = MathF.Sqrt(dx * dx + dy * dy);

            var nearestCp = _mapProfileManager.GetNearestChokepoint(botPos);
            float distToChokepoint = nearestCp != null
                ? MathF.Sqrt(MathF.Pow(botPos.X - nearestCp.X, 2) + MathF.Pow(botPos.Y - nearestCp.Y, 2))
                : 9999f;

            float lastDanger = _lastDangerTime.GetValueOrDefault(bot.Slot, -100f);
            bool recentDanger = (currentTime - lastDanger) <= 6.0f;
            bool isEnemyVisible = pawn.Bot?.IsEnemyVisible ?? false;

            if (isEnemyVisible)
            {
                _lastDangerTime[bot.Slot] = currentTime;
                recentDanger = true;
            }

            // Contextos táticos de alta velocidade de deslocamento
            bool isHighMobilityContext = (plan.RoundTempo == RoundTempo.FAST_CONTACT)
                || (navState.Stance == EngagementStance.AGGRESSIVE_POKE)
                || (plan.CurrentPhase == RoundPhase.Staging)
                || (plan.CurrentPhase == RoundPhase.Executing && distToTarget > 600.0f);

            // CRITÉRIO DE FACA NA MÃO: Rota segura, longa distância (>600u) e sem perigo nos últimos 6s
            if (isHighMobilityContext && !recentDanger && !isEnemyVisible && distToTarget > 600.0f && distToChokepoint > 600.0f)
            {
                if (!_isKnifeDrawn.GetValueOrDefault(bot.Slot, false))
                {
                    bot.ExecuteClientCommand("slot3");
                    _isKnifeDrawn[bot.Slot] = true;
                }
            }
            else
            {
                // FREIO TÁTICO: Aproximou-se a <= 600u da zona de contato ou detectou inimigo/passos
                ApplyTacticalBrake(bot);
            }
        }
    }

    private void ApplyTacticalBrake(CCSPlayerController bot)
    {
        if (_isKnifeDrawn.TryGetValue(bot.Slot, out bool drawn) && drawn)
        {
            _isKnifeDrawn[bot.Slot] = false;
            EquipCombatWeapon(bot);
        }
    }

    public static void EquipCombatWeapon(CCSPlayerController bot)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;

        bot.ExecuteClientCommand("slot1");
        Server.NextFrame(() =>
        {
            if (bot.IsValid && bot.PawnIsAlive)
            {
                var pawn = bot.PlayerPawn.Value;
                var active = pawn?.WeaponServices?.ActiveWeapon.Value;
                if (active != null && active.IsValid && !string.IsNullOrEmpty(active.DesignerName) && active.DesignerName.Contains("knife", StringComparison.OrdinalIgnoreCase))
                {
                    bot.ExecuteClientCommand("slot2");
                }
            }
        });
    }
}
