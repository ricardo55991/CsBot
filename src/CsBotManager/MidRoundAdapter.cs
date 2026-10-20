using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Timers;
using CounterStrikeSharp.API.Modules.Utils;

using CsTimer = CounterStrikeSharp.API.Modules.Timers.Timer;

namespace CsBotManager;

public class MidRoundAdapter
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly CtDefenseController _ctController;
    private readonly BotLocomotionDriver _locomotionDriver;
    private readonly Random _random = new();

    private CsTimer? _fakeTimer;

    public MidRoundAdapter(
        BasePlugin plugin,
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        CtDefenseController ctController,
        BotLocomotionDriver locomotionDriver)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _ctController = ctController;
        _locomotionDriver = locomotionDriver;
    }

    public void OnRoundStart(TacticalPlan plan, List<CCSPlayerController> trBots, CCSPlayerController? human)
    {
        _fakeTimer?.Kill();
        _fakeTimer = null;

        if (plan.TrTacticType == TrTacticType.SPLIT_FAKE)
        {
            plan.FakeTargetSite = "A";
            plan.RealTargetSite = "B";
            Server.PrintToChatAll($" {ChatColors.Gold}[TR Tática]{ChatColors.Default} Plano definido: {ChatColors.Yellow}SPLIT FAKE (Simula A -> Executa B){ChatColors.Default}!");
        }
    }

    public void OnRoundFreezeEnd(TacticalPlan plan, List<CCSPlayerController> trBots, List<CCSPlayerController> ctBots, CCSPlayerController? human)
    {
        if (plan.TrTacticType != TrTacticType.SPLIT_FAKE || trBots.Count < 2) return;

        // Identifica portador da C4
        CCSPlayerController? bombCarrier = trBots.FirstOrDefault(b => HasC4(b));
        if (bombCarrier == null && human != null && HasC4(human))
        {
            bombCarrier = human;
        }

        // Separa Grupo Barulho (2 bots sem C4)
        var noiseBots = trBots
            .Where(b => bombCarrier == null || b.Slot != bombCarrier.Slot)
            .Take(2)
            .ToList();

        foreach (var bot in noiseBots)
        {
            var role = _roleManager.GetBotRole(bot);
            if (role != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
            {
                order.IsNoiseGroup = true;
                order.TargetArea = "Bombsite A";
                order.Stance = EngagementStance.AGGRESSIVE_POKE;
            }
        }

        Server.PrintToChatAll($" {ChatColors.Yellow}[TR Fake Group]{ChatColors.Default} Grupo Barulho ({string.Join(", ", noiseBots.Select(b => b.PlayerName))}) avançando para simular entrada no Bomb A!");

        // 6.0s após saída do spawn: Grupo Barulho faz barulho em A e em seguida recua
        _fakeTimer = _plugin.AddTimer(6.0f, () =>
        {
            foreach (var bot in noiseBots)
            {
                if (!bot.IsValid || !bot.PawnIsAlive) continue;
                _locomotionDriver.ThrowUtility(bot, 45); // 45 = Smoke
            }

            // C-02B: Correção do bug de friendly-fire lógico. Passa ctBots para o CtDefenseController!
            _ctController.ReportBombPressure("Bombsite A", plan, ctBots);
            Server.PrintToChatAll($" {ChatColors.Gold}[TR Fake]{ChatColors.Default} Utilitárias caíram no A! Barulho concluído. Grupo de barulho recuando com vida!");

            // 4.0s depois do fake: Grupo Silencioso com C4 explode no Bomb B
            _plugin.AddTimer(4.0f, () =>
            {
                Server.PrintToChatAll($" {ChatColors.Green}[TR Fake]{ChatColors.Default} ⚡ {ChatColors.Gold}HORA DO VERDADEIRO EXECUTE NO BOMB B!{ChatColors.Default} Entrada coordenada!");

                foreach (var bot in trBots.Where(b => !noiseBots.Contains(b)))
                {
                    ApplyAction(bot, MidRoundAction.RUSH_TRADE, "Bombsite B");
                }
            });
        });
    }

    public void ApplyAction(CCSPlayerController bot, MidRoundAction action, string? targetArea = null)
    {
        if (!bot.IsValid || !bot.PawnIsAlive || bot.PlayerPawn.Value == null || bot.PlayerPawn.Value.AbsOrigin == null) return;
        var origin = bot.PlayerPawn.Value.AbsOrigin;

        switch (action)
        {
            case MidRoundAction.HIDE_COVER:
                _locomotionDriver.HoldPosition(bot, 4.0f, true);
                Server.PrintToChatAll($" {ChatColors.Yellow}[Micro Ação]{ChatColors.Default} {bot.PlayerName} adotou cobertura furtiva ({ChatColors.Gold}HIDE_COVER{ChatColors.Default}).");
                break;

            case MidRoundAction.JIGGLE_PEEK:
                _locomotionDriver.NavigateToPosition(bot, origin.X, origin.Y, origin.Z, stance: EngagementStance.JIGGLE_INFO);
                break;

            case MidRoundAction.ROTATE_SILENT:
                string targetSector = (targetArea != null && targetArea.Contains("A")) ? "Bombsite A" : "Bombsite B";
                var rotateSpot = _mapProfileManager.GetSpotsForSector(targetSector, bot.Team == CsTeam.CounterTerrorist ? "CT" : "TR").FirstOrDefault();
                if (rotateSpot != null)
                {
                    _locomotionDriver.NavigateToSpot(bot, rotateSpot, hurry: false, EngagementStance.AGGRESSIVE_POKE);
                }
                Server.PrintToChatAll($" {ChatColors.LightBlue}[Micro Ação]{ChatColors.Default} {bot.PlayerName} rotacionando em modo silencioso ({ChatColors.Green}ROTATE_SILENT{ChatColors.Default}) para {targetArea ?? "bomb alternativo"}!");
                break;

            case MidRoundAction.WATCH_FLANK:
                _locomotionDriver.HoldPosition(bot, 5.0f, false);
                Server.PrintToChatAll($" {ChatColors.Gold}[Micro Ação]{ChatColors.Default} {bot.PlayerName} assumiu a marcação de costas ({ChatColors.Yellow}WATCH_FLANK{ChatColors.Default})!");
                break;

            case MidRoundAction.RUSH_TRADE:
                string execSector = (targetArea != null && targetArea.Contains("A")) ? "Bombsite A" : "Bombsite B";
                var execSpot = _mapProfileManager.GetSpotsForSector(execSector, "TR").FirstOrDefault();
                if (execSpot != null)
                {
                    _locomotionDriver.NavigateToSpot(bot, execSpot, hurry: true, EngagementStance.AGGRESSIVE_POKE);
                }
                break;
        }
    }

    public void HandlePlayerDeath(EventPlayerDeath @event, TacticalPlan plan, List<CCSPlayerController> teamBots)
    {
        var victim = @event.Userid;
        var killer = @event.Attacker;

        if (victim != null && victim.IsValid && victim.IsBot && _roleManager.GetBotRole(victim) == BotRole.EntryFragger)
        {
            var speaker = teamBots.FirstOrDefault(b => b.PawnIsAlive && b.Slot != victim.Slot)?.PlayerName ?? "IGL";
            UtilityAndClockCoordinator.PrintTeamChat(victim.Team, speaker, "Entry Fragger caiu na entrada! Ataque miou -> Rotação no SHIFT pro outro bomb!");
            foreach (var bot in teamBots.Where(b => b.PawnIsAlive && b.Slot != victim.Slot))
            {
                ApplyAction(bot, MidRoundAction.ROTATE_SILENT, "Bomb Alternativo");
            }
        }

        // Senso de Sobrevivência pós-kill do Bot (Quebra do Trade Kill via NavMesh) (C-01C)
        if (killer != null && killer.IsValid && killer.IsBot && killer.PawnIsAlive && killer.PlayerPawn.Value != null)
        {
            var pawn = killer.PlayerPawn.Value;
            var origin = pawn.AbsOrigin;

            // Recua 250 unidades via NavMesh para quebrar o trade kill sem teleporte
            if (origin != null && pawn.EyeAngles != null)
            {
                float yawRad = (float)(pawn.EyeAngles.Y * Math.PI / 180.0);
                float backX = origin.X - (float)Math.Cos(yawRad) * 250.0f;
                float backY = origin.Y - (float)Math.Sin(yawRad) * 250.0f;
                _locomotionDriver.NavigateToPosition(killer, backX, backY, origin.Z, hurry: true, stance: EngagementStance.PASSIVE_HOLD);
                Server.PrintToConsole($"[MidRoundAdapter] {killer.PlayerName} abateu um inimigo e recuou 250u via NavMesh quebrando o trade kill.");
            }

            int actionRoll = _random.Next(100);
            if (actionRoll < 25)
            {
                // Pop-flash e repique
                _locomotionDriver.ThrowUtility(killer, 43); // 43 = Flashbang
                _plugin.AddTimer(1.5f, () =>
                {
                    if (killer.IsValid && killer.PawnIsAlive)
                    {
                        ApplyAction(killer, MidRoundAction.JIGGLE_PEEK, null);
                    }
                });
            }
            else if (actionRoll < 60)
            {
                // Lança fogo ou fumaça de contenção
                _locomotionDriver.ThrowUtility(killer, 46); // 46 = Molotov
            }
        }
    }

    public void HandleBombPlanted(EventBombPlanted @event, TacticalPlan plan, List<CCSPlayerController> ctBots, List<CCSPlayerController> trBots)
    {
        string site = @event.Site == 0 ? "A" : "B";
        _ctController.ReportBombConfirmed(site, plan, ctBots);

        var aliveCts = ctBots.Where(b => b.PawnIsAlive).ToList();
        var aliveTrs = trBots.Where(b => b.PawnIsAlive).ToList();
        var ctSpeaker = aliveCts.FirstOrDefault()?.PlayerName ?? "CT IGL";

        // Decisão orgânica de Retake CT vs. Save com 6% de heroísmo
        bool isCtSevereDisadvantage = aliveCts.Count <= 2 && aliveTrs.Count >= 3;

        if (isCtSevereDisadvantage)
        {
            int roll = _random.Next(100);
            var ctSpeakerBot = aliveCts.FirstOrDefault();
            if (roll < 6)
            {
                // 6%: Tentativa heroica de retake no clutch
                plan.IsHeroicAttempt = true;
                plan.IsTacticalSaveActive = false;
                UtilityAndClockCoordinator.PrintTeamChatAndRadio(ctSpeakerBot, CsTeam.CounterTerrorist, ctSpeaker, $"Bomba plantada no {site}! Tamo em {aliveCts.Count}x{aliveTrs.Count}, mas vamo tentar o retake heroico no clutch!", "go");
            }
            else
            {
                // 94%: Save inteligente de CT
                plan.IsTacticalSaveActive = true;
                UtilityAndClockCoordinator.PrintTeamChatAndRadio(ctSpeakerBot, CsTeam.CounterTerrorist, ctSpeaker, $"Bomba plantada no {site} e tamo em {aliveCts.Count}x{aliveTrs.Count}... Impossível retake! SALVA AS ARMAS E KITS! (SAVE)", "fallback");

                foreach (var bot in aliveCts)
                {
                    ApplyAction(bot, MidRoundAction.HIDE_COVER, "Base CT (Save)");
                }
            }
        }
        else
        {
            plan.IsTacticalSaveActive = false;
            UtilityAndClockCoordinator.PrintTeamChatAndRadio(aliveCts.FirstOrDefault(), CsTeam.CounterTerrorist, ctSpeaker, $"Bomba plantada no {site}! Retake coordenado com kits e utilitárias!", "needbackup");
        }

        // Marcação de costas após o plant
        var flankBot = trBots.FirstOrDefault(b => b.PawnIsAlive);
        if (flankBot != null)
        {
            ApplyAction(flankBot, MidRoundAction.WATCH_FLANK, null);
        }
    }

    // =========================================================================
    // INTELIGÊNCIA CONTRA FAKE DEFUSE NO PÓS-PLANT (PARTE A - ITEM 4)
    // =========================================================================
    public void HandleBombBeginDefuse(EventBombBegindefuse @event, TacticalPlan plan, List<CCSPlayerController> trBots, List<CCSPlayerController> ctBots)
    {
        var aliveTrs = trBots.Where(b => b.IsValid && b.PawnIsAlive && b.PlayerPawn.Value?.AbsOrigin != null).ToList();
        if (aliveTrs.Count == 0) return;

        var defuser = @event.Userid;
        bool hasKit = @event.Haskit;

        // Delay humano calculado: 70% chance de esperar 1.8s a 2.4s (anti-fake); 30% checagem rápida após 1.1s se sem kit
        float delay = (_random.Next(100) < 70)
            ? (1.8f + (float)_random.NextDouble() * 0.6f)
            : (1.1f + (float)_random.NextDouble() * 0.3f);

        Vector? defuserPos = defuser?.PlayerPawn.Value?.AbsOrigin;

        // Encontra o bot Terrorista vivo mais próximo da C4/defuser
        var checkerBot = (defuserPos != null)
            ? aliveTrs.OrderBy(b => (b.PlayerPawn.Value!.AbsOrigin! - defuserPos).Length()).First()
            : aliveTrs.First();

        // Demais defensores TR mantêm postura firme e ângulo travado
        foreach (var bot in aliveTrs.Where(b => b.Slot != checkerBot.Slot))
        {
            _locomotionDriver.HoldPosition(bot, 4.0f, false);
        }

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            checkerBot,
            CsTeam.Terrorist,
            checkerBot.PlayerName,
            "CT tocou na defuse! Segura o pixel que pode ser fake... vou espiar no tempo!",
            "holdpos");

        _plugin.AddTimer(delay, () =>
        {
            if (checkerBot.IsValid && checkerBot.PawnIsAlive)
            {
                ApplyAction(checkerBot, MidRoundAction.JIGGLE_PEEK, null);
            }
        });
    }

    public void TriggerSilentRotate(string targetSite, List<CCSPlayerController> teamBots)
    {
        Server.PrintToChatAll($" {ChatColors.Yellow}[Voz Tática]{ChatColors.Default} Ordem de rotação silenciosa recebida! Todo o time no {ChatColors.Gold}SHIFT para o Bomb {targetSite.ToUpper()}{ChatColors.Default}!");
        foreach (var bot in teamBots.Where(b => b.PawnIsAlive))
        {
            ApplyAction(bot, MidRoundAction.ROTATE_SILENT, $"Bomb {targetSite.ToUpper()}");
        }
    }

    private bool HasC4(CCSPlayerController player)
    {
        if (player.PlayerPawn.Value == null || player.PlayerPawn.Value.WeaponServices == null) return false;
        var weapons = player.PlayerPawn.Value.WeaponServices.MyWeapons;
        if (weapons == null) return false;

        foreach (var w in weapons)
        {
            if (w.Value != null && w.Value.DesignerName.Contains("c4", StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }
        return false;
    }
}
