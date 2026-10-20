using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class CombatAdapter
{
    private readonly CsBotManagerPlugin _plugin;
    private readonly BotLocomotionDriver _locomotionDriver;
    private readonly MidRoundAdapter _midRoundAdapter;

    public TacticalCalloutSystem? CalloutSystem { get; set; }
    public MapProfileManager? MapProfileManager { get; set; }

    // Cooldown para evitar re-gatilhos contínuos enquanto o bot troca de arma ou recua
    private readonly Dictionary<int, float> _actionCooldowns = new();
    private readonly Dictionary<int, float> _lastCombatTime = new();
    private float _lastTickCheck = 0.0f;

    public CombatAdapter(
        CsBotManagerPlugin plugin,
        BotLocomotionDriver locomotionDriver,
        MidRoundAdapter midRoundAdapter)
    {
        _plugin = plugin;
        _locomotionDriver = locomotionDriver;
        _midRoundAdapter = midRoundAdapter;
    }

    public void OnRoundStart()
    {
        _actionCooldowns.Clear();
        _lastCombatTime.Clear();
        _lastTickCheck = 0.0f;
    }

    public void OnPlayerHurt(EventPlayerHurt @event)
    {
        float now = Server.CurrentTime;

        if (@event.Userid != null && @event.Userid.IsValid && @event.Userid.IsBot)
        {
            _lastCombatTime[@event.Userid.Slot] = now;
            CheckBotCombatState(@event.Userid, now);
        }

        if (@event.Attacker != null && @event.Attacker.IsValid && @event.Attacker.IsBot)
        {
            _lastCombatTime[@event.Attacker.Slot] = now;
            CheckBotCombatState(@event.Attacker, now);
        }
    }

    // =========================================================================
    // CICLO DE MONITORAMENTO DE COMBATE A ~10Hz (MÓDULO 4)
    // =========================================================================
    public void UpdateTick(float currentTime, List<CCSPlayerController> aliveBots)
    {
        if (currentTime - _lastTickCheck < 0.10f) return;
        _lastTickCheck = currentTime;

        foreach (var bot in aliveBots)
        {
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive || !bot.IsBot) continue;

            float lastCombat = _lastCombatTime.GetValueOrDefault(bot.Slot, -100f);
            bool isEnemyVisible = bot.PlayerPawn.Value?.Bot?.IsEnemyVisible ?? false;

            if (isEnemyVisible || (currentTime - lastCombat <= 2.5f))
            {
                CheckBotCombatState(bot, currentTime);
            }
        }
    }

    private void CheckBotCombatState(CCSPlayerController bot, float currentTime)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;

        // Respeita cooldown mínimo de ação por bot
        if (_actionCooldowns.TryGetValue(bot.Slot, out float cd) && currentTime < cd)
        {
            return;
        }

        var pawn = bot.PlayerPawn.Value;
        if (pawn == null || pawn.AbsOrigin == null) return;

        var weaponServices = pawn.WeaponServices;
        var activeWeapon = weaponServices?.ActiveWeapon.Value;
        if (activeWeapon == null || !activeWeapon.IsValid) return;

        string designerName = activeWeapon.DesignerName ?? "";
        if (!IsPrimaryWeapon(designerName)) return;

        // Verifica se a munição no pente zerou durante o tiroteio ativo
        if (activeWeapon.Clip1 > 0) return;

        var botPos = pawn.AbsOrigin;

        // Localiza o inimigo vivo mais próximo para calcular a distância de engajamento
        var allPlayers = Utilities.GetPlayers();
        CCSPlayerController? closestEnemy = null;
        float minEnemyDist = float.MaxValue;

        foreach (var p in allPlayers)
        {
            if (p == null || !p.IsValid || !p.PawnIsAlive || p.Team == bot.Team) continue;
            var enemyPawn = p.PlayerPawn.Value;
            if (enemyPawn?.AbsOrigin == null) continue;

            // Bloco 1 / F-009: Percepção legítima sem wallhack de raio cego
            if (!TacticalCalloutSystem.CanBotPerceiveEnemy(bot, p, CalloutSystem, MapProfileManager)) continue;

            float dist = (enemyPawn.AbsOrigin - botPos).Length();
            if (dist < minEnemyDist)
            {
                minEnemyDist = dist;
                closestEnemy = p;
            }
        }

        if (closestEnemy == null || minEnemyDist > 2000.0f) return;

        // ---------------------------------------------------------------------
        // CASO 1: Curta Distância (< 500u) -> Pistol Swap Imediato
        // ---------------------------------------------------------------------
        if (minEnemyDist < 500.0f)
        {
            _actionCooldowns[bot.Slot] = currentTime + 2.0f;

            // Saca a pistola imediatamente e cancela a recarga lenta
            bot.ExecuteClientCommand("slot2");

            var api = _locomotionDriver.BotApi;
            if (api != null)
            {
                api.InjectUsercmd(bot.Slot, BotLocomotionDriver.IN_ATTACK, 300);
            }

            UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                bot,
                bot.Team,
                bot.PlayerName,
                $"Pente seco no tiroteio a queima-roupa! Puxei a pistola!",
                "takingfire");

            Server.PrintToChatAll($" {ChatColors.Yellow}[Combate Micro]{ChatColors.Default} {bot.PlayerName} zerou o pente ({minEnemyDist:F0}u < 500u) -> {ChatColors.Red}PISTOL SWAP RÁPIDO!{ChatColors.Default}");
        }
        // ---------------------------------------------------------------------
        // CASO 2: Média / Longa Distância (>= 500u) -> Recuo Seguro & Recarga
        // ---------------------------------------------------------------------
        else
        {
            _actionCooldowns[bot.Slot] = currentTime + 3.2f;

            // Recua para cobertura furtiva e não fica aberto no meio do bomb
            _midRoundAdapter.ApplyAction(bot, MidRoundAction.HIDE_COVER, null);

            // Inicia recarga protegida atrás da parede (F-006: AddRoundTimer)
            bot.ExecuteClientCommand("+reload");
            _plugin.AddRoundTimer(0.1f, () =>
            {
                if (bot.IsValid && bot.PawnIsAlive)
                {
                    bot.ExecuteClientCommand("-reload");
                }
            });

            UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                bot,
                bot.Team,
                bot.PlayerName,
                $"Pente zerado! Recuando para cobertura para recarregar!",
                "coverme");

            Server.PrintToChatAll($" {ChatColors.Yellow}[Combate Micro]{ChatColors.Default} {bot.PlayerName} zerou o pente ({minEnemyDist:F0}u >= 500u) -> {ChatColors.Green}RECUOU PARA COBERTURA PARA RECARREGAR!{ChatColors.Default}");

            // Após tempo seguro de recarga (~2.4s), retoma o combate com Jiggle Peek (F-006: AddRoundTimer)
            _plugin.AddRoundTimer(2.4f, () =>
            {
                if (bot.IsValid && bot.PawnIsAlive)
                {
                    _midRoundAdapter.ApplyAction(bot, MidRoundAction.JIGGLE_PEEK, null);
                }
            });
        }
    }

    public static bool IsPrimaryWeapon(string? weaponDesignerName)
    {
        if (string.IsNullOrEmpty(weaponDesignerName)) return false;
        string name = weaponDesignerName.ToLowerInvariant();

        if (name.Contains("knife") || name.Contains("bayonet")) return false;
        if (name.Contains("grenade") || name.Contains("flashbang") || name.Contains("molotov") || name.Contains("incgrenade") || name.Contains("decoy")) return false;
        if (name.Contains("c4")) return false;

        // Pistolas
        if (name.Contains("glock") || name.Contains("usp") || name.Contains("hkp2000") ||
            name.Contains("p250") || name.Contains("deagle") || name.Contains("fiveseven") ||
            name.Contains("tec9") || name.Contains("cz75a") || name.Contains("revolver") ||
            name.Contains("elite"))
        {
            return false;
        }

        return true;
    }
}
