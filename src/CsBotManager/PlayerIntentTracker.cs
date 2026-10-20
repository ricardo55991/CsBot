using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

using CsTimer = CounterStrikeSharp.API.Modules.Timers.Timer;

namespace CsBotManager;

public class PlayerIntentTracker
{
    private readonly BasePlugin _plugin;
    private readonly RoleManager _roleManager;
    private readonly MapProfileManager _mapProfileManager;

    private CsTimer? _trackingTimer;
    private float _roundStartTime = 0.0f;
    private bool _hasSwappedThisRound = false;

    public PlayerIntentTracker(BasePlugin plugin, RoleManager roleManager, MapProfileManager mapProfileManager)
    {
        _plugin = plugin;
        _roleManager = roleManager;
        _mapProfileManager = mapProfileManager;
    }

    public void OnRoundStart()
    {
        _trackingTimer?.Kill();
        _trackingTimer = null;
        _hasSwappedThisRound = false;
        _roundStartTime = 0.0f;
    }

    public void OnRoundFreezeEnd(TacticalPlan plan, CCSPlayerController? human, List<CCSPlayerController> teamBots)
    {
        _roundStartTime = Server.CurrentTime;
        _hasSwappedThisRound = false;

        if (human == null || !human.IsValid) return;

        // Monitora o deslocamento do jogador a cada 0.4s durante os primeiros 6 segundos
        _trackingTimer = _plugin.AddTimer(0.4f, () =>
        {
            if (_hasSwappedThisRound || human == null || !human.IsValid || human.PlayerPawn.Value == null)
            {
                return;
            }

            float elapsed = Server.CurrentTime - _roundStartTime;
            if (elapsed > 6.0f)
            {
                _trackingTimer?.Kill();
                _trackingTimer = null;
                return;
            }

            var playerPos = human.PlayerPawn.Value.AbsOrigin;
            if (playerPos == null) return;

            // Utiliza dinamicamente os chokepoints do perfil ativo do mapa
            foreach (var chokepoint in _mapProfileManager.CurrentProfile.Chokepoints)
            {
                var targetVec = new Vector(chokepoint.X, chokepoint.Y, chokepoint.Z);
                float dist = (playerPos - targetVec).Length();
                if (dist <= chokepoint.Radius + 150.0f)
                {
                    bool swapped = _roleManager.ClaimPositionForPlayer(human, chokepoint.Name, teamBots, plan, _mapProfileManager);
                    if (swapped)
                    {
                        _hasSwappedThisRound = true;
                        _trackingTimer?.Kill();
                        _trackingTimer = null;

                        Server.PrintToChatAll($" {ChatColors.Green}🔄 [Swap Automático]{ChatColors.Default} Movimento detectado! Você assumiu {ChatColors.Gold}{chokepoint.Name.ToUpper()}{ChatColors.Default}. Bots reorganizados!");
                        human.PrintToCenterHtml($"<font color='#00FFCC' size='4'><b>🔄 [Swap Automático] Assumiu: {chokepoint.Name.ToUpper()}!</b></font>");
                        break;
                    }
                }
            }
        }, TimerFlags.REPEAT);
    }
}
