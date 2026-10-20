using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class UtilityAndClockCoordinator
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    public BotLocomotionDriver? LocomotionDriver { get; set; }

    private readonly Dictionary<string, ChokepointBlockState> _activeBlocks = new(StringComparer.OrdinalIgnoreCase);
    private readonly Random _random = new();
    private float _lastReactiveMolotovTime = -100.0f;
    private bool _hasAnnouncedDesperation = false;
    private bool _hasAnnouncedLateSilence = false;
    private bool _hasAnnouncedSave = false;

    public UtilityAndClockCoordinator(BasePlugin plugin, MapProfileManager mapProfileManager, RoleManager roleManager)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
    }

    public void OnRoundStart()
    {
        _activeBlocks.Clear();
        _lastReactiveMolotovTime = -100.0f;
        _hasAnnouncedDesperation = false;
        _hasAnnouncedLateSilence = false;
        _hasAnnouncedSave = false;
    }

    public bool CanThrowUtilityAt(string chokepointId, string utilityType)
    {
        float now = Server.CurrentTime;
        if (_activeBlocks.TryGetValue(chokepointId, out var state))
        {
            // Se o bloqueio ainda tem mais de 2.5s de duração, proíbe gastar outra granada (Anti-Duplicação)
            if (now < state.BlockedUntilTime - 2.5f)
            {
                return false;
            }

            // Se faltam menos de 2.5s para a smoke dissipar, permite renovação (Ciclo de Contenção)
            if (now >= state.BlockedUntilTime - 2.5f && now < state.BlockedUntilTime)
            {
                return true;
            }
        }
        return true;
    }

    public void RegisterUtilityDetonation(float x, float y, float z, string utilityType, int throwerSlot = -1)
    {
        var cp = _mapProfileManager.FindChokepointAt(x, y, z);
        if (cp == null) return;

        float duration = utilityType.Equals("Molotov", StringComparison.OrdinalIgnoreCase) ? 7.0f : 18.0f;
        float now = Server.CurrentTime;

        _activeBlocks[cp.Id] = new ChokepointBlockState
        {
            ChokepointId = cp.Id,
            BlockType = utilityType,
            BlockedUntilTime = now + duration,
            PlacedByBotSlot = throwerSlot
        };

        Server.PrintToConsole($"[UtilityCoordinator] {utilityType} registrado em '{cp.Name}'. Bloqueado por {duration}s até {now + duration:F1}s.");
    }

    public void CheckReactiveMolotovOnSmokeDetonation(float smokeX, float smokeY, float smokeZ, List<CCSPlayerController> ctBots)
    {
        var cp = _mapProfileManager.FindChokepointAt(smokeX, smokeY, smokeZ);
        if (cp == null) return;

        float now = Server.CurrentTime;
        // Cooldown de 8 segundos entre molotovs reativas
        if (now - _lastReactiveMolotovTime < 8.0f) return;

        // Procura um bot CT próximo do chokepoint com postura de âncora ou rotador
        var candidateBot = ctBots
            .Where(b => b.PawnIsAlive && b.PlayerPawn.Value != null)
            .OrderBy(b => (b.PlayerPawn.Value!.AbsOrigin! - new Vector(cp.X, cp.Y, cp.Z)).Length())
            .FirstOrDefault();

        if (candidateBot != null && candidateBot.PlayerPawn.Value != null)
        {
            float dist = (candidateBot.PlayerPawn.Value.AbsOrigin! - new Vector(cp.X, cp.Y, cp.Z)).Length();
            if (dist < 1200.0f)
            {
                _lastReactiveMolotovTime = now;
                candidateBot.ExecuteClientCommand("use weapon_molotov; use weapon_incgrenade; +attack; -attack");
                RegisterUtilityDetonation(cp.X, cp.Y, cp.Z, "Molotov", candidateBot.Slot);

                Server.PrintToChatAll($" {ChatColors.Gold}[Contra-Execução CT]{ChatColors.Default} {candidateBot.PlayerName} lançou {ChatColors.Red}MOLOTOV REATIVA{ChatColors.Default} na boca de {ChatColors.Green}{cp.Name}{ChatColors.Default} para quebrar a execução!");
            }
        }
    }

    public void UpdateClockSense(float roundTimeRemaining, bool isBombPlanted, TacticalPlan plan, List<CCSPlayerController> ctBots, List<CCSPlayerController> trBots)
    {
        bool previousSaveState = plan.IsTacticalSaveActive;

        if (isBombPlanted)
        {
            plan.IsClockDesperationActive = false;
            plan.IsLateRoundSilenceActive = false;
            if (previousSaveState != plan.IsTacticalSaveActive)
            {
                LocomotionDriver?.NotifySaveState(plan.IsTacticalSaveActive);
            }
            return;
        }

        // 1. Silêncio e Disciplina de Late-Round (entre 65s e 22s)
        if (roundTimeRemaining <= 65.0f && roundTimeRemaining > 22.0f)
        {
            plan.IsLateRoundSilenceActive = true;
            if (!_hasAnnouncedLateSilence)
            {
                _hasAnnouncedLateSilence = true;
                Server.PrintToConsole("[ClockCoordinator] Late-Round Silencioso ativo: CTs mantêm disciplina e off-angles.");
            }
        }
        else
        {
            plan.IsLateRoundSilenceActive = false;
        }

        // 2. Desespero de Relógio (< 22s sem plant) vs. Lógica Orgânica de Save Tático
        if (roundTimeRemaining < 22.0f && roundTimeRemaining > 0.0f)
        {
            var aliveTrs = trBots.Where(b => b.PawnIsAlive).ToList();
            var aliveCts = ctBots.Where(b => b.PawnIsAlive).ToList();
            var speakerBot = aliveTrs.FirstOrDefault();
            var speaker = speakerBot?.PlayerName ?? "IGL";

            // Situação de desvantagem crítica (ex: 1v3, 1v4, 1v5, 2v4, 2v5)
            bool isSevereDisadvantage = aliveTrs.Count <= 2 && aliveCts.Count >= (aliveTrs.Count + 2);

            if (isSevereDisadvantage)
            {
                // Chance remota de 6% de tentativa heroica conjunta
                int roll = _random.Next(100);
                if (roll < 6)
                {
                    plan.IsHeroicAttempt = true;
                    plan.IsClockDesperationActive = true;
                    plan.IsTacticalSaveActive = false;

                    if (!_hasAnnouncedDesperation)
                    {
                        _hasAnnouncedDesperation = true;
                        PrintTeamChatAndRadio(speakerBot, CsTeam.Terrorist, speaker, "Faltam menos de 20s e tamo em desvantagem, mas vamo tentar o milagre juntos! RUSH B!", "go");
                        foreach (var bot in aliveTrs)
                        {
                            var role = _roleManager.GetBotRole(bot);
                            if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                            {
                                order.IsFallingBack = false;
                                order.Stance = EngagementStance.AGGRESSIVE_POKE;
                            }
                        }
                    }
                }
                else
                {
                    // 94% das vezes: Inteligência de Save Competitivo
                    plan.IsTacticalSaveActive = true;
                    plan.IsClockDesperationActive = false;

                    if (!_hasAnnouncedSave)
                    {
                        _hasAnnouncedSave = true;
                        PrintTeamChatAndRadio(speakerBot, CsTeam.Terrorist, speaker, $"Menos de 20s e {aliveTrs.Count}x{aliveCts.Count}! Não dá tempo... GUARDA AS ARMAS PRO PRÓXIMO ROUND! (SAVE)", "fallback");
                        foreach (var bot in aliveTrs)
                        {
                            var role = _roleManager.GetBotRole(bot);
                            if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                            {
                                order.IsFallingBack = true;
                                order.Stance = EngagementStance.PASSIVE_HOLD;
                                order.MidRoundAction = MidRoundAction.HIDE_COVER;
                            }
                        }
                    }
                }
            }
            else
            {
                // Paridade ou vantagem numérica: avanço para o plant da C4
                plan.IsClockDesperationActive = true;
                plan.IsTacticalSaveActive = false;

                if (!_hasAnnouncedDesperation)
                {
                    _hasAnnouncedDesperation = true;
                    PrintTeamChatAndRadio(speakerBot, CsTeam.Terrorist, speaker, "⏰ Menos de 20s galera, avanço total pra plantar a C4!", "go");
                    foreach (var bot in aliveTrs)
                    {
                        var role = _roleManager.GetBotRole(bot);
                        if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                        {
                            order.IsFallingBack = false;
                            order.Stance = EngagementStance.AGGRESSIVE_POKE;
                        }
                    }
                }
            }
        }
        else if (roundTimeRemaining >= 22.0f)
        {
            plan.IsClockDesperationActive = false;
            plan.IsTacticalSaveActive = false;
        }

        if (previousSaveState != plan.IsTacticalSaveActive)
        {
            LocomotionDriver?.NotifySaveState(plan.IsTacticalSaveActive);
        }
    }

    public static void PrintTeamChat(CsTeam team, string speakerName, string message)
    {
        string prefix = team == CsTeam.Terrorist
            ? $" {ChatColors.Yellow}(Terrorista) {ChatColors.Green}{speakerName}{ChatColors.Default}: "
            : $" {ChatColors.LightBlue}(Contraterrorista) {ChatColors.Green}{speakerName}{ChatColors.Default}: ";

        var players = Utilities.GetPlayers();
        foreach (var p in players)
        {
            if (p != null && p.IsValid && !p.IsHLTV && p.Team == team)
            {
                p.PrintToChat(prefix + message);
            }
        }
    }

    public static void PrintTeamChatAndRadio(CCSPlayerController? speakerBot, CsTeam team, string speakerName, string message, string? radioCommand = null)
    {
        PrintTeamChat(team, speakerName, message);
        if (speakerBot != null && speakerBot.IsValid && !string.IsNullOrEmpty(radioCommand))
        {
            speakerBot.ExecuteClientCommand(radioCommand);
        }
    }
}
