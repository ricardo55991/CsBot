using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class RoleManager
{
    private readonly Dictionary<int, BotRole> _botRoles = new();
    private readonly Dictionary<int, string> _claimedPositions = new();
    private readonly Dictionary<int, TacticalSpot> _enemyBotSpots = new();

    public bool IsHumanPositionLocked { get; private set; } = false;
    public string LockedSectorName { get; private set; } = string.Empty;

    public void LockHumanPosition(string sector)
    {
        IsHumanPositionLocked = true;
        LockedSectorName = sector;
    }

    public void UnlockHumanPosition()
    {
        IsHumanPositionLocked = false;
        LockedSectorName = string.Empty;
    }

    public void AssignRolesToBots(List<CCSPlayerController> bots, bool clearExisting = false)
    {
        if (clearExisting)
        {
            _botRoles.Clear();
        }

        var roles = new[] { BotRole.AWPer, BotRole.EntryFragger, BotRole.Rotator, BotRole.Anchor, BotRole.Rotator };

        for (int i = 0; i < bots.Count; i++)
        {
            if (bots[i] == null || !bots[i].IsValid) continue;
            var role = roles[i % roles.Length];
            _botRoles[bots[i].Slot] = role;
        }
    }

    public BotRole? GetBotRole(CCSPlayerController bot)
    {
        if (_botRoles.TryGetValue(bot.Slot, out var role))
        {
            return role;
        }
        return null;
    }

    public CCSPlayerController? GetBotByRole(List<CCSPlayerController> bots, BotRole role)
    {
        return bots.FirstOrDefault(b => _botRoles.TryGetValue(b.Slot, out var r) && r == role);
    }

    public void SetEnemyBotSpots(Dictionary<int, TacticalSpot> setup)
    {
        _enemyBotSpots.Clear();
        foreach (var kvp in setup)
        {
            _enemyBotSpots[kvp.Key] = kvp.Value;
        }
    }

    public TacticalSpot? GetEnemyBotSpot(int botSlot)
    {
        return _enemyBotSpots.TryGetValue(botSlot, out var spot) ? spot : null;
    }

    public bool ClaimPositionForPlayer(
        CCSPlayerController player,
        string sectorName,
        List<CCSPlayerController> teamBots,
        TacticalPlan plan,
        MapProfileManager mapProfileManager)
    {
        string resolvedTarget = mapProfileManager.ResolveVoiceSynonym(sectorName);
        var cp = mapProfileManager.FindChokepointByNameOrSynonym(resolvedTarget);
        if (cp != null)
        {
            resolvedTarget = cp.Name;
        }

        _claimedPositions[player.Slot] = resolvedTarget;

        foreach (var bot in teamBots)
        {
            if (_botRoles.TryGetValue(bot.Slot, out var role))
            {
                string key = GetOrderKey(role);
                if (plan.BotOrders.TryGetValue(key, out var order))
                {
                    if (order.TargetArea.Equals(resolvedTarget, StringComparison.OrdinalIgnoreCase) ||
                        order.TargetArea.Contains(sectorName, StringComparison.OrdinalIgnoreCase) ||
                        resolvedTarget.Contains(order.TargetArea, StringComparison.OrdinalIgnoreCase))
                    {
                        string alternativeArea = (player.Team == CsTeam.CounterTerrorist)
                            ? (resolvedTarget.Contains("Mid") || resolvedTarget.Contains("Janela") ? "Conector" : "Bombsite A")
                            : (resolvedTarget.Contains("A") ? "Bombsite B" : "Top Mid");

                        order.TargetArea = alternativeArea;
                        order.RoleAction = $"Cedendo {resolvedTarget} para {player.PlayerName}; reforçando {alternativeArea}";

                        var newStagingSpot = mapProfileManager.GetMatchingSpotForOrder(role, alternativeArea, player.Team, true);
                        var newExecSpot = mapProfileManager.GetMatchingSpotForOrder(role, alternativeArea, player.Team, false);

                        if (newStagingSpot != null)
                        {
                            order.StagingSpotId = newStagingSpot.Id;
                            order.Stance = newStagingSpot.RecommendedStance;
                            order.FallbackSpotId = newStagingSpot.FallbackSpotId ?? order.FallbackSpotId;
                        }
                        if (newExecSpot != null)
                        {
                            order.ExecuteSpotId = newExecSpot.Id;
                        }

                        return true;
                    }
                }
            }
        }

        return false;
    }

    // Ponto 4: "Vamos jogar respawn" com Consciência de Arma
    public void AssignPositionsBySpawn(List<CCSPlayerController> ctBots, TacticalPlan plan, MapProfileManager mapProfileManager)
    {
        var midChokepoint = mapProfileManager.FindChokepointByNameOrSynonym("meio") ?? mapProfileManager.FindChokepointByNameOrSynonym("janela");
        var bChokepoint = mapProfileManager.FindChokepointByNameOrSynonym("b") ?? mapProfileManager.FindChokepointByNameOrSynonym("tapete");
        var aChokepoint = mapProfileManager.FindChokepointByNameOrSynonym("a") ?? mapProfileManager.FindChokepointByNameOrSynonym("caverna");

        foreach (var bot in ctBots)
        {
            if (!bot.IsValid || bot.PlayerPawn.Value == null || bot.PlayerPawn.Value.AbsOrigin == null) continue;
            var pos = bot.PlayerPawn.Value.AbsOrigin;

            float distMid = midChokepoint != null ? (pos - new Vector(midChokepoint.X, midChokepoint.Y, midChokepoint.Z)).Length() : 99999f;
            float distB = bChokepoint != null ? (pos - new Vector(bChokepoint.X, bChokepoint.Y, bChokepoint.Z)).Length() : 99999f;
            float distA = aChokepoint != null ? (pos - new Vector(aChokepoint.X, aChokepoint.Y, aChokepoint.Z)).Length() : 99999f;

            var role = GetBotRole(bot) ?? BotRole.Rotator;
            string key = GetOrderKey(role);

            if (plan.BotOrders.TryGetValue(key, out var order))
            {
                if (distMid <= distB && distMid <= distA)
                {
                    // Spawn mais perto do Meio
                    order.TargetArea = "Mid Window";
                    if (role == BotRole.AWPer)
                    {
                        order.StagingSpotId = "ct_mid_window_deep_awp";
                        order.Stance = EngagementStance.PASSIVE_HOLD;
                    }
                    else
                    {
                        // Rifler no Meio: Consciência de Arma (Não dar a cara aberta; jiggle info e mira recuada)
                        order.StagingSpotId = "ct_mid_connector_headshot";
                        order.Stance = EngagementStance.JIGGLE_INFO;
                        order.RoleAction = "Marcando subida do L / Conector com Jiggle Peek de informação (sem trocação aberta com AWP)";
                    }
                }
                else if (distB <= distA)
                {
                    // Spawn mais perto do B
                    order.TargetArea = "Bombsite B";
                    order.StagingSpotId = "ct_b_bench_deep";
                    order.Stance = EngagementStance.PASSIVE_HOLD;
                }
                else
                {
                    // Spawn mais perto do A
                    order.TargetArea = "Bombsite A";
                    order.StagingSpotId = "ct_a_stairs_cross";
                    order.Stance = EngagementStance.PASSIVE_HOLD;
                }
            }
        }

        UtilityAndClockCoordinator.PrintTeamChat(CsTeam.CounterTerrorist, "IGL", "Ordem aceita: JOGANDO PELO RESPAWN! Cada um no pixel mais próximo sem se expor!");
    }

    // Módulo 1: Setup de "Double AWP" Rico no CT
    public void ConfigureDoubleAwpSetup(CCSPlayerController anchorBot, TacticalPlan plan)
    {
        var role = GetBotRole(anchorBot) ?? BotRole.Anchor;
        string key = GetOrderKey(role);

        if (plan.BotOrders.TryGetValue(key, out var order))
        {
            if (order.TargetArea.Contains("A", StringComparison.OrdinalIgnoreCase))
            {
                order.StagingSpotId = "ct_a_ticket_passive";
                order.Stance = EngagementStance.PASSIVE_HOLD;
                order.RoleAction = "Double AWP CT: Cravado de sniper longa distância no Ticket A";
            }
            else
            {
                order.StagingSpotId = "ct_b_van_peek";
                order.Stance = EngagementStance.PASSIVE_HOLD;
                order.RoleAction = "Double AWP CT: Cravado de sniper longa distância na Van B";
            }
        }
    }

    public static string GetOrderKey(BotRole role) => role switch
    {
        BotRole.AWPer => "bot_awper",
        BotRole.EntryFragger => "bot_entry",
        BotRole.Rotator => "bot_rotator",
        BotRole.Anchor => "bot_anchor",
        _ => "bot_rotator"
    };
}
