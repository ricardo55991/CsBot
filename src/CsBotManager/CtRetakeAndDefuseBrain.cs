using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public enum DefuseAction
{
    NormalStick,
    SmokeTapAndStepOut,
    ClassicFakeTapAndBait,
    HalfDefuseBait,
    CriticalColdStick
}

public class CtRetakeAndDefuseBrain
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly BotLocomotionDriver _locomotionDriver;

    private readonly Random _random = new();

    // Estado do Retake atual
    private bool _hasSmokedC4 = false;
    private float _smokeDetonatedTime = -100.0f;
    private bool _isFakeDefuseInProgress = false;
    private DefuseAction _chosenDefuseAction = DefuseAction.NormalStick;
    private float _defuseStartTime = 0.0f;
    private int _defusingBotSlot = -1;

    // Prioridade Inteligente de Defuse (Módulo 2)
    private int _blockedDefuserSlot = -1;
    private int _priorityKitCarrierSlot = -1;

    public bool HasSmokedC4 => _hasSmokedC4;
    public bool IsFakeDefuseInProgress => _isFakeDefuseInProgress;
    public DefuseAction CurrentDefuseAction => _chosenDefuseAction;
    public int BlockedDefuserSlot => _blockedDefuserSlot;
    public int PriorityKitCarrierSlot => _priorityKitCarrierSlot;

    public CtRetakeAndDefuseBrain(
        BasePlugin plugin,
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        BotLocomotionDriver locomotionDriver)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _locomotionDriver = locomotionDriver;
    }

    public void OnRoundStart()
    {
        _hasSmokedC4 = false;
        _smokeDetonatedTime = -100.0f;
        _isFakeDefuseInProgress = false;
        _chosenDefuseAction = DefuseAction.NormalStick;
        _defuseStartTime = 0.0f;
        _defusingBotSlot = -1;
        _blockedDefuserSlot = -1;
        _priorityKitCarrierSlot = -1;
    }

    // ==============================================================================
    // 1. Smoke na C4 Antes do Defuse (Smoke Defuse)
    // ==============================================================================
    public bool TryDeploySmokeOnC4(CCSPlayerController defuserBot, Vector bombPos, float bombTimeRemaining, List<CCSPlayerController> ctBots)
    {
        if (_hasSmokedC4) return false;

        bool hasKit = HasDefuser(defuserBot);
        float minTimeNeeded = hasKit ? 8.0f : 13.0f;

        // Se tempo restante da C4 não permitir, não joga smoke (stick de desespero)
        if (bombTimeRemaining < minTimeNeeded) return false;

        // Procura se o desarmador ou colega próximo possui smoke
        CCSPlayerController? smokerBot = null;
        if (HasSmokeGrenade(defuserBot))
        {
            smokerBot = defuserBot;
        }
        else
        {
            smokerBot = ctBots.FirstOrDefault(b => b.PawnIsAlive && b.PlayerPawn.Value?.AbsOrigin != null &&
                (b.PlayerPawn.Value.AbsOrigin - bombPos).Length() <= 450.0f && HasSmokeGrenade(b));
        }

        if (smokerBot == null) return false;

        // Lança smoke diretamente na coordenada da C4
        _locomotionDriver.ThrowUtility(smokerBot, 45, bombPos); // 45 = Smoke
        _hasSmokedC4 = true;
        _smokeDetonatedTime = Server.CurrentTime + 1.2f; // ~1.2s para expandir

        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            smokerBot,
            CsTeam.CounterTerrorist,
            smokerBot.PlayerName,
            "Smokei a C4! Vou tentar no meio da fumaça, cobre o spam!",
            "takingfire");

        return true;
    }

    // ==============================================================================
    // 2. Roleta Estatística de Fake Defuse vs. Stick Defuse
    // ==============================================================================
    public DefuseAction DecideDefuseStrategy(CCSPlayerController defuserBot, Vector bombPos, float bombTimeRemaining, int aliveTrs)
    {
        bool hasKit = HasDefuser(defuserBot);
        float criticalTime = hasKit ? 7.5f : 11.5f;

        // Tempo crítico: 100% Cold Stick
        if (bombTimeRemaining <= criticalTime || aliveTrs == 0)
        {
            _chosenDefuseAction = DefuseAction.CriticalColdStick;
            return _chosenDefuseAction;
        }

        float now = Server.CurrentTime;
        bool isUnderSmoke = _hasSmokedC4 && (now - _smokeDetonatedTime >= 0.8f && now - _smokeDetonatedTime <= 18.0f);

        int roll = _random.Next(100);

        // CASO 1: C4 coberta por Smoke
        if (isUnderSmoke)
        {
            if (roll < 55)
            {
                // 55% Stick Defuse ("Pros Don't Fake")
                _chosenDefuseAction = DefuseAction.NormalStick;
            }
            else
            {
                // 45% Smoke Tap & Step-Out
                _chosenDefuseAction = DefuseAction.SmokeTapAndStepOut;
            }
        }
        // CASO 2: C4 no ABERTO (Sem Smoke)
        else
        {
            if (roll < 60)
            {
                // 60% Fake Defuse Clássico (Tap & Bait)
                _chosenDefuseAction = DefuseAction.ClassicFakeTapAndBait;
            }
            else if (roll < 85)
            {
                // 25% Half-Defuse Bait (Segura 2.8s e Solta)
                _chosenDefuseAction = DefuseAction.HalfDefuseBait;
            }
            else
            {
                // 15% Cold Stick
                _chosenDefuseAction = DefuseAction.NormalStick;
            }
        }

        return _chosenDefuseAction;
    }

    public void OnDefuseTapped(CCSPlayerController defuserBot, Vector bombPos, float bombTimeRemaining, int aliveTrs)
    {
        _defuseStartTime = Server.CurrentTime;
        _defusingBotSlot = defuserBot.Slot;

        var action = DecideDefuseStrategy(defuserBot, bombPos, bombTimeRemaining, aliveTrs);

        if (action == DefuseAction.SmokeTapAndStepOut)
        {
            // Toca por 0.5s e dá passo lateral com rifle
            _isFakeDefuseInProgress = true;
            _plugin.AddTimer(0.5f, () =>
            {
                if (!defuserBot.IsValid || !defuserBot.PawnIsAlive) return;

                // Cancela o defuse soltando IN_USE e dá passo de 80u
                var botPawn = defuserBot.PlayerPawn.Value;
                if (botPawn?.AbsOrigin != null)
                {
                    Vector stepOut = new Vector(botPawn.AbsOrigin.X + 80.0f, botPawn.AbsOrigin.Y - 60.0f, botPawn.AbsOrigin.Z);
                    _locomotionDriver.NavigateToPoint(defuserBot, stepOut, hurry: false, EngagementStance.PASSIVE_HOLD);
                }

                _plugin.AddTimer(2.0f, () =>
                {
                    _isFakeDefuseInProgress = false; // Retoma o defuse real
                });
            });
        }
        else if (action == DefuseAction.ClassicFakeTapAndBait)
        {
            // Toca por 0.5s para fazer barulho, cancela e crava mira por 2.5s
            _isFakeDefuseInProgress = true;
            _plugin.AddTimer(0.5f, () =>
            {
                if (!defuserBot.IsValid || !defuserBot.PawnIsAlive) return;

                // Mira no chokepoint suspeito
                var botPawn = defuserBot.PlayerPawn.Value;
                if (botPawn?.AbsOrigin != null)
                {
                    _locomotionDriver.HoldPosition(defuserBot, duration: 2.5f, crouch: true);
                }

                _plugin.AddTimer(2.5f, () =>
                {
                    _isFakeDefuseInProgress = false; // Retoma o defuse real
                });
            });
        }
        else if (action == DefuseAction.HalfDefuseBait)
        {
            // Segura por 2.8s e solta
            _isFakeDefuseInProgress = false;
            _plugin.AddTimer(2.8f, () =>
            {
                if (!defuserBot.IsValid || !defuserBot.PawnIsAlive) return;

                _isFakeDefuseInProgress = true;
                _locomotionDriver.HoldPosition(defuserBot, duration: 2.0f, crouch: false);

                _plugin.AddTimer(2.0f, () =>
                {
                    _isFakeDefuseInProgress = false; // Retoma defuse final
                });
            });
        }
        else
        {
            // Stick até o fim
            _isFakeDefuseInProgress = false;
        }
    }

    // ==============================================================================
    // 3. Prioridade Inteligente de Defuse (Módulo 2)
    // ==============================================================================
    public bool CheckAndEnforceSmartDefusePriority(CCSPlayerController currentDefuser, Vector bombPos, List<CCSPlayerController> ctBots)
    {
        if (currentDefuser == null || !currentDefuser.IsValid || !currentDefuser.PawnIsAlive) return false;

        // Se o bot desarmador já possui kit, ele mesmo conclui a defuse rápida
        if (HasDefuser(currentDefuser)) return false;

        // Procura aliado CT vivo com kit num raio <= 400 unidades da C4
        var kitCarrier = ctBots.FirstOrDefault(b =>
            b.IsValid &&
            b.PawnIsAlive &&
            b.Slot != currentDefuser.Slot &&
            b.PlayerPawn.Value?.AbsOrigin != null &&
            HasDefuser(b) &&
            (b.PlayerPawn.Value.AbsOrigin - bombPos).Length() <= 400.0f);

        if (kitCarrier == null) return false;

        // Bloqueia o bot sem kit e transfere a responsabilidade para o bot com kit
        _blockedDefuserSlot = currentDefuser.Slot;
        _priorityKitCarrierSlot = kitCarrier.Slot;
        _defusingBotSlot = kitCarrier.Slot;

        // Força o bot sem kit a cancelar a defusação e adotar postura de cobertura protegendo a C4
        _locomotionDriver.HoldPosition(currentDefuser, duration: 4.0f, crouch: true);

        // Manda o bot com kit navegar urgentemente até a coordenada da C4
        _locomotionDriver.NavigateToPoint(kitCarrier, bombPos, hurry: true, EngagementStance.PASSIVE_HOLD);

        // Comunicação tática orgânica no chat de equipe e rádio nativo
        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
            kitCarrier,
            CsTeam.CounterTerrorist,
            kitCarrier.PlayerName,
            "Deixa pra mim que eu tenho Kit! Cobre a defuse!",
            "affirmative");

        Server.PrintToChatAll($" {ChatColors.Green}[CT Defuse Smart]{ChatColors.Default} {kitCarrier.PlayerName} (com Kit) assumiu a defuse no lugar de {currentDefuser.PlayerName}!");

        return true;
    }

    public bool ShouldInjectDefuseInput(CCSPlayerController defuserBot)
    {
        // Se o bot foi bloqueado para ceder o defuse para quem tem kit, NÃO injeta IN_USE
        if (defuserBot.Slot == _blockedDefuserSlot)
        {
            return false;
        }

        // Se estiver em fake defuse (soltou a bomba para caçar), NÃO injeta IN_USE
        if (_isFakeDefuseInProgress && defuserBot.Slot == _defusingBotSlot)
        {
            return false;
        }
        return true;
    }

    public static bool HasDefuser(CCSPlayerController player)
    {
        var itemServices = player.PlayerPawn.Value?.ItemServices as CCSPlayer_ItemServices;
        if (itemServices == null) return false;
        try
        {
            return itemServices.HasDefuser;
        }
        catch
        {
            return false;
        }
    }

    private static bool HasSmokeGrenade(CCSPlayerController player)
    {
        var weaponServices = player.PlayerPawn.Value?.WeaponServices;
        if (weaponServices?.MyWeapons == null) return false;

        foreach (var handle in weaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w != null && w.DesignerName != null && w.DesignerName.Contains("smoke", StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }
        return false;
    }
}
