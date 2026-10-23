using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class BotRoleAssignmentState
{
    public int Slot { get; init; }
    public string PlayerName { get; set; } = string.Empty;
    public BotRole ProfileRole { get; set; } = BotRole.Rotator;
    public BotRole RoundRole { get; set; } = BotRole.Rotator;
    public BotRole AssignedWeaponRole { get; set; } = BotRole.Rotator;
    public string CurrentWeapon { get; set; } = "none";
    public string RoleAssignmentReason { get; set; } = "INITIAL_PROFILE_ROLE";
    public bool EconomyOverride { get; set; }
    public bool PickupOverride { get; set; }

    public string FormatRoleSummary()
    {
        if (ProfileRole == RoundRole && !EconomyOverride && !PickupOverride)
        {
            return $"{RoundRole}";
        }
        string flags = "";
        if (PickupOverride) flags += ",pickup_override=true";
        if (EconomyOverride) flags += ",econ_override=true";
        return $"{RoundRole} [perfil:{ProfileRole}, arma_role:{AssignedWeaponRole}, motivo:{RoleAssignmentReason}{flags}]";
    }
}

public class RoleManager
{
    private readonly Dictionary<int, BotRole> _botRoles = new();
    private readonly Dictionary<int, BotRoleAssignmentState> _roleStates = new();
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
            _roleStates.Clear();
        }

        var roles = new[] { BotRole.AWPer, BotRole.EntryFragger, BotRole.Rotator, BotRole.Anchor, BotRole.Rotator };
        var validBots = bots.Where(b => b != null && b.IsValid).OrderBy(b => b.Slot).ToList();

        int roleIdx = 0;
        foreach (var bot in validBots)
        {
            var assigned = roles[roleIdx % roles.Length];
            _botRoles[bot.Slot] = assigned;
            _roleStates[bot.Slot] = new BotRoleAssignmentState
            {
                Slot = bot.Slot,
                PlayerName = bot.PlayerName ?? $"Bot_{bot.Slot}",
                ProfileRole = assigned,
                RoundRole = assigned,
                AssignedWeaponRole = assigned,
                CurrentWeapon = "none",
                RoleAssignmentReason = "INITIAL_PROFILE_ROLE",
                EconomyOverride = false,
                PickupOverride = false
            };
            roleIdx++;
        }
    }

    public void AssignInitialRoleForSlot(int slot, string playerName, BotRole profileRole)
    {
        _botRoles[slot] = profileRole;
        _roleStates[slot] = new BotRoleAssignmentState
        {
            Slot = slot,
            PlayerName = playerName,
            ProfileRole = profileRole,
            RoundRole = profileRole,
            AssignedWeaponRole = profileRole,
            CurrentWeapon = "none",
            RoleAssignmentReason = "INITIAL_PROFILE_ROLE",
            EconomyOverride = false,
            PickupOverride = false
        };
    }

    public void ReconcileWeaponRoleOverride(
        int slot,
        string currentWeapon,
        bool hasSavedAwp,
        bool teamAlreadyHasSavedAwpOnTeammate,
        bool couldNotAffordAwp)
    {
        if (!_roleStates.TryGetValue(slot, out var state))
        {
            var baseRole = _botRoles.GetValueOrDefault(slot, BotRole.Rotator);
            state = new BotRoleAssignmentState
            {
                Slot = slot,
                ProfileRole = baseRole,
                RoundRole = baseRole,
                AssignedWeaponRole = baseRole
            };
            _roleStates[slot] = state;
        }

        state.CurrentWeapon = currentWeapon;
        bool holdingAwp = currentWeapon.Contains("awp", StringComparison.OrdinalIgnoreCase) || hasSavedAwp;

        if (holdingAwp && state.ProfileRole != BotRole.AWPer)
        {
            state.RoundRole = BotRole.AWPer;
            state.AssignedWeaponRole = BotRole.AWPer;
            state.PickupOverride = true;
            state.EconomyOverride = false;
            state.RoleAssignmentReason = "SAVED_AWP_PICKUP_OVERRIDE";
            _botRoles[slot] = BotRole.AWPer;
        }
        else if (!holdingAwp && state.ProfileRole == BotRole.AWPer)
        {
            if (teamAlreadyHasSavedAwpOnTeammate)
            {
                state.RoundRole = BotRole.Rotator;
                state.AssignedWeaponRole = BotRole.Rotator;
                state.PickupOverride = true;
                state.EconomyOverride = couldNotAffordAwp;
                state.RoleAssignmentReason = "TEAMMATE_SAVED_AWP_ROLE_SWAP";
                _botRoles[slot] = BotRole.Rotator;
            }
            else if (couldNotAffordAwp)
            {
                state.RoundRole = BotRole.Rotator;
                state.AssignedWeaponRole = BotRole.Rotator;
                state.EconomyOverride = true;
                state.RoleAssignmentReason = "ECONOMY_OVERRIDE_NO_AWP_FUNDS";
            }
        }
        else
        {
            state.RoundRole = state.ProfileRole;
            state.AssignedWeaponRole = holdingAwp ? BotRole.AWPer : state.ProfileRole;
            state.EconomyOverride = false;
            state.PickupOverride = false;
            state.RoleAssignmentReason = "PROFILE_MATCHED";
            _botRoles[slot] = state.RoundRole;
        }
    }

    public BotRoleAssignmentState? GetRoleAssignmentState(int slot)
    {
        return _roleStates.TryGetValue(slot, out var state) ? state : null;
    }

    public BotRole? GetBotRole(CCSPlayerController bot)
    {
        if (_roleStates.TryGetValue(bot.Slot, out var st))
        {
            return st.RoundRole;
        }
        if (_botRoles.TryGetValue(bot.Slot, out var role))
        {
            return role;
        }
        return null;
    }

    public BotRole? GetBotProfileRole(int slot)
    {
        if (_roleStates.TryGetValue(slot, out var st))
        {
            return st.ProfileRole;
        }
        return _botRoles.TryGetValue(slot, out var r) ? r : null;
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
