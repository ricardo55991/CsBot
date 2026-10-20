using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class SiteClearAndPlantController
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly BotLocomotionDriver _locomotionDriver;

    private float _siteEntryTime = 0.0f;
    private float _lastDamageInSiteTime = -100.0f;
    private bool _hasAnnouncedPlant = false;
    private bool _isClearingActive = false;

    public bool IsClearingActive => _isClearingActive;
    public bool HasAnnouncedPlant => _hasAnnouncedPlant;

    public SiteClearAndPlantController(
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
        _siteEntryTime = 0.0f;
        _lastDamageInSiteTime = -100.0f;
        _hasAnnouncedPlant = false;
        _isClearingActive = false;
    }

    public void OnPlayerHurt(EventPlayerHurt @event)
    {
        var victim = @event.Userid;
        if (victim == null || !victim.IsValid || victim.Team != CsTeam.Terrorist) return;

        // Se um aliado tomou dano dentro ou próximo do bombsite
        if (victim.PlayerPawn.Value?.AbsOrigin != null)
        {
            var pos = victim.PlayerPawn.Value.AbsOrigin;
            var cp = _mapProfileManager.FindChokepointAt(pos.X, pos.Y, pos.Z);
            if (cp != null && (cp.AssociatedBomb == "A" || cp.AssociatedBomb == "B"))
            {
                _lastDamageInSiteTime = Server.CurrentTime;
            }
        }
    }

    // ==============================================================================
    // Validação de Segurança para Plantar (IsSiteSafeToPlant)
    // ==============================================================================
    public bool IsSiteSafeToPlant(CCSPlayerController carrierBot, float roundTimeRemaining, List<CCSPlayerController> allPlayers)
    {
        if (carrierBot == null || !carrierBot.IsValid || !carrierBot.PawnIsAlive) return false;

        float now = Server.CurrentTime;

        // 1. DESESPERO DE TEMPO (< 12s): Força o plant imediato independente de risco
        if (roundTimeRemaining <= 12.0f)
        {
            return true;
        }

        var botPawn = carrierBot.PlayerPawn.Value;
        if (botPawn == null || botPawn.AbsOrigin == null) return false;

        var botPos = botPawn.AbsOrigin;
        var cp = _mapProfileManager.FindChokepointAt(botPos.X, botPos.Y, botPos.Z);
        string bombId = cp?.AssociatedBomb ?? "A";

        // Inicia contagem de tempo de varredura se estiver entrando agora
        if (_siteEntryTime <= 0.0f)
        {
            _siteEntryTime = now;
            _isClearingActive = true;
        }

        // a) Condição: Nenhum dano sofrido por aliados no bomb nos últimos 2.0s
        if (now - _lastDamageInSiteTime < 2.0f)
        {
            return false;
        }

        // b) Condição: Nenhum CT visível ou vivo dentro da área imediata do bomb (raio <= 750u)
        bool enemyInSite = allPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist)
            .Any(p => p.PlayerPawn.Value?.AbsOrigin != null &&
                      (p.PlayerPawn.Value.AbsOrigin - botPos).Length() <= 750.0f);

        if (enemyInSite)
        {
            return false;
        }

        // c) Condição: Pelo menos 1 aliado vivo cobrindo a entrada OU 3.5s de varredura sem contato
        float timeInSite = now - _siteEntryTime;
        bool hasAlliesCovering = allPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.Terrorist && p.Slot != carrierBot.Slot)
            .Any(p => p.PlayerPawn.Value?.AbsOrigin != null &&
                      (p.PlayerPawn.Value.AbsOrigin - botPos).Length() <= 900.0f);

        if (hasAlliesCovering || timeInSite >= 3.5f)
        {
            return true;
        }

        return false;
    }

    // ==============================================================================
    // Escolha de Pixel de Plant (Safe vs. Aberto) & Execução
    // ==============================================================================
    public (Vector TargetPos, bool IsOpen, string DominantSector) GetPlantPosition(CCSPlayerController carrierBot, string bombId, int aliveTrs, int aliveCts)
    {
        var botPawn = carrierBot.PlayerPawn.Value;
        Vector fallbackPos = botPawn?.AbsOrigin != null
            ? new Vector(botPawn.AbsOrigin.X, botPawn.AbsOrigin.Y, botPawn.AbsOrigin.Z)
            : new Vector(-1280.0f, -420.0f, -160.0f);

        bool isBombA = bombId.Equals("A", StringComparison.OrdinalIgnoreCase);

        // Se paridade numérica ou desvantagem (TRs <= 2 ou CTs >= TRs): Plant Safe / Fechado
        bool chooseSafe = (aliveTrs <= 2) || (aliveCts >= aliveTrs);

        if (isBombA)
        {
            if (chooseSafe)
            {
                // Safe Default A (atrás da caixa tripla)
                return (new Vector(-1280.0f, -420.0f, -160.0f), false, "Caverna");
            }
            else
            {
                // Aberto pra Caverna e Palácio
                return (new Vector(-1080.0f, -460.0f, -160.0f), true, "Caverna e Palácio");
            }
        }
        else
        {
            if (chooseSafe)
            {
                // Safe Default B (colado na van / caixa)
                return (new Vector(-220.0f, 580.0f, -160.0f), false, "Tapete");
            }
            else
            {
                // Aberto pros Tapetes e L
                return (new Vector(-120.0f, 700.0f, -160.0f), true, "Tapetes e L");
            }
        }
    }

    public void AnnounceAndStartPlant(CCSPlayerController carrierBot, string bombId, int aliveTrs, int aliveCts)
    {
        if (_hasAnnouncedPlant) return;
        _hasAnnouncedPlant = true;
        _isClearingActive = false;

        var plantDecision = GetPlantPosition(carrierBot, bombId, aliveTrs, aliveCts);

        // Comunicação no chat de equipe
        if (plantDecision.IsOpen)
        {
            UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                carrierBot,
                CsTeam.Terrorist,
                carrierBot.PlayerName,
                $"Bomb limpo! Plantando aberto pra {plantDecision.DominantSector}, me cobre!",
                "go");
        }
        else
        {
            UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                carrierBot,
                CsTeam.Terrorist,
                carrierBot.PlayerName,
                $"Risco de retake! Plantando safe atrás da cobertura no Bomb {bombId}, segura a entrada!",
                "holdpos");
        }

        // Move fisicamente o bot até o pixel exato de plant
        _locomotionDriver.NavigateToPoint(carrierBot, plantDecision.TargetPos, hurry: true, EngagementStance.PASSIVE_HOLD);
    }
}
