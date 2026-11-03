using System.Net;
using System.Text;
using System.Text.Json;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class VoiceCommandBridge
{
    private readonly BasePlugin _plugin;
    private readonly EconomyManager _economyManager;
    private readonly RoleManager _roleManager;
    private readonly OllamaIglService _iglService;
    private readonly MapProfileManager _mapProfileManager;
    private readonly PacingAndFallbackController _pacingController;
    private readonly CtDefenseController _ctController;
    private readonly MidRoundAdapter _midRoundAdapter;
    private readonly BotLocomotionDriver _locomotionDriver;
    private readonly Func<TacticalPlan> _getCurrentPlan;

    private HttpListener? _listener;
    private bool _isRunning = false;
    private const string ListenerUri = "http://127.0.0.1:27080/voice/";

    public string LastVoiceCommand { get; private set; } = string.Empty;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }

    public VoiceCommandBridge(
        BasePlugin plugin,
        EconomyManager economyManager,
        RoleManager roleManager,
        OllamaIglService iglService,
        MapProfileManager mapProfileManager,
        PacingAndFallbackController pacingController,
        CtDefenseController ctController,
        MidRoundAdapter midRoundAdapter,
        BotLocomotionDriver locomotionDriver,
        Func<TacticalPlan> getCurrentPlan)
    {
        _plugin = plugin;
        _economyManager = economyManager;
        _roleManager = roleManager;
        _iglService = iglService;
        _mapProfileManager = mapProfileManager;
        _pacingController = pacingController;
        _ctController = ctController;
        _midRoundAdapter = midRoundAdapter;
        _locomotionDriver = locomotionDriver;
        _getCurrentPlan = getCurrentPlan;
    }

    public void Start()
    {
        try
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add(ListenerUri);
            _listener.Start();
            _isRunning = true;

            _listener.BeginGetContext(OnContextReceived, null);
            Server.PrintToConsole($"[VoiceCommandBridge] Listener de voz iniciado com sucesso em {ListenerUri}");
        }
        catch (Exception ex)
        {
            Server.PrintToConsole($"[VoiceCommandBridge] Aviso ao iniciar HTTP Listener: {ex.Message}");
        }
    }

    public void Stop()
    {
        _isRunning = false;
        try
        {
            _listener?.Stop();
            _listener?.Close();
        }
        catch { }
    }

    private void OnContextReceived(IAsyncResult ar)
    {
        if (!_isRunning || _listener == null) return;

        try
        {
            var context = _listener.EndGetContext(ar);
            _listener.BeginGetContext(OnContextReceived, null);

            if (context.Request.HttpMethod == "POST")
            {
                using var reader = new StreamReader(context.Request.InputStream, context.Request.ContentEncoding);
                string jsonBody = reader.ReadToEnd();

                var payload = JsonSerializer.Deserialize<VoiceCommandPayload>(jsonBody);
                if (payload != null && !string.IsNullOrWhiteSpace(payload.Text))
                {
                    Server.NextFrame(() =>
                    {
                        ProcessVoiceCommand(payload.Text);
                    });
                }

                string responseString = "{\"status\":\"ok\",\"message\":\"Comando processado com sucesso\"}";
                byte[] buffer = Encoding.UTF8.GetBytes(responseString);
                context.Response.ContentType = "application/json";
                context.Response.ContentLength64 = buffer.Length;
                context.Response.OutputStream.Write(buffer, 0, buffer.Length);
                context.Response.OutputStream.Close();
            }
            else
            {
                context.Response.StatusCode = 405;
                context.Response.Close();
            }
        }
        catch (Exception ex)
        {
            Server.PrintToConsole($"[VoiceCommandBridge] Erro ao processar requisição: {ex.Message}");
        }
    }

    public void ProcessVoiceCommand(string text)
    {
        LastVoiceCommand = text;
        string lower = text.ToLowerInvariant().Trim();

        var players = Utilities.GetPlayers().Where(p => p != null && p.IsValid && !p.IsHLTV).ToList();
        var human = players.FirstOrDefault(p => !p.IsBot);
        if (human == null) return;

        var teamBots = players.Where(p => p.Team == human.Team && p.IsBot).ToList();
        var activePlan = _getCurrentPlan();
        int roundNum = Math.Max(1, activePlan.RoundId);

        human.PrintToChat($" {ChatColors.Green}🎙️ [Voz IGL]{ChatColors.Default} \"{text}\"");

        // 0. Nota de Debug / Telemetria Forense por Voz
        if (lower.Contains("nota de debug") || lower.Contains("anota aí") || lower.Contains("anota ai") || lower.StartsWith("nota"))
        {
            string noteText = text.Replace("nota de debug", "", StringComparison.OrdinalIgnoreCase)
                                  .Replace("anota aí", "", StringComparison.OrdinalIgnoreCase)
                                  .Replace("anota ai", "", StringComparison.OrdinalIgnoreCase)
                                  .Replace("nota", "", StringComparison.OrdinalIgnoreCase)
                                  .Trim(':', ' ', ',');
            if (string.IsNullOrEmpty(noteText)) noteText = text;

            var allPlayers = Utilities.GetPlayers().Where(p => p != null && p.IsValid && !p.IsHLTV).ToList();
            TelemetryLogger?.RecordPlayerNote(human, noteText, allPlayers, activePlan);
            HumanCommunicationLogger.RecordCommunication("VOICE", human.Team, roundNum, text, "DEBUG_NOTE", $"Nota registrada: {noteText}", 0.01);
            return;
        }

        // 1. Comando de Execução / Entrada Rápida
        if (lower.Contains("executa") || lower.Contains("entra") || lower.Contains("vai") || lower.Contains("go"))
        {
            _pacingController.TriggerExecute($"Voz do IGL: \"{text}\"", teamBots);
            HumanCommunicationLogger.RecordCommunication("VOICE", human.Team, roundNum, text, "BUILTIN_COMMAND", "TriggerExecute", 0.01);
            return;
        }

        // 2. Comando de Recuo / Rotação Silenciosa
        if (lower.Contains("miou") || lower.Contains("recua") || lower.Contains("shift") || lower.Contains("rotaciona") || lower.Contains("gira"))
        {
            string targetSite = lower.Contains("a") ? "A" : "B";
            _midRoundAdapter.TriggerSilentRotate(targetSite, teamBots);
            HumanCommunicationLogger.RecordCommunication("VOICE", human.Team, roundNum, text, "BUILTIN_COMMAND", $"TriggerSilentRotate({targetSite})", 0.01);
            return;
        }

        // 3. Comando de Pop-Flash em Dupla
        if (lower.Contains("banga") || lower.Contains("flash"))
        {
            string sector = "caverna";
            if (lower.Contains("meio") || lower.Contains("janela")) sector = "meio";
            else if (lower.Contains("palacio")) sector = "palácio";
            else if (lower.Contains("tapete") || lower.Contains("b")) sector = "tapete";

            _ctController.RequestHumanDuoFlash(human, sector, teamBots);
            HumanCommunicationLogger.RecordCommunication("VOICE", human.Team, roundNum, text, "BUILTIN_COMMAND", $"RequestHumanDuoFlash({sector})", 0.01);
            return;
        }

        // 4. Comando de Cobertura / Salvar Arma
        if (lower.Contains("esconde") || lower.Contains("guarda") || lower.Contains("salva"))
        {
            foreach (var bot in teamBots.Where(b => b.PawnIsAlive))
            {
                _midRoundAdapter.ApplyAction(bot, MidRoundAction.HIDE_COVER, null);
            }
            HumanCommunicationLogger.RecordCommunication("VOICE", human.Team, roundNum, text, "BUILTIN_COMMAND", "HIDE_COVER", 0.01);
            return;
        }

        // 5. Pedido de Drop
        if (lower.Contains("drop") || lower.Contains("arma") || lower.Contains("ak") || lower.Contains("m4") || lower.Contains("awp"))
        {
            string? weapon = null;
            if (lower.Contains("awp")) weapon = "awp";
            else if (lower.Contains("ak")) weapon = "ak47";
            else if (lower.Contains("m4")) weapon = "m4";

            bool dropped = _economyManager.DropWeaponForPlayer(human, weapon, teamBots);
            if (!dropped)
            {
                human.PrintToChat($" {ChatColors.Red}[CsBot]{ChatColors.Default} Nenhum bot com saldo para drop no momento.");
            }
            HumanCommunicationLogger.RecordCommunication("VOICE", human.Team, roundNum, text, "BUILTIN_COMMAND", $"DropWeapon({weapon ?? "auto"}, dropped={dropped})", 0.01);
            return;
        }

        // 6. Comando "Jogar Respawn" (C-03: opera sobre activePlan real)
        if (lower.Contains("respawn"))
        {
            _roleManager.AssignPositionsBySpawn(teamBots, activePlan, _mapProfileManager);
            foreach (var bot in teamBots)
            {
                if (!bot.IsValid || !bot.PawnIsAlive) continue;
                var role = _roleManager.GetBotRole(bot);
                if (activePlan.TryGetOrderForBot(bot.Slot, role, out var order))
                {
                    var spot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                    if (spot != null)
                    {
                        _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, order.Stance);
                    }
                }
            }
            HumanCommunicationLogger.RecordCommunication("VOICE", human.Team, roundNum, text, "BUILTIN_COMMAND", "AssignPositionsBySpawn", 0.01);
            return;
        }

        // 7. Assumir Posição Fixa ou Temporária (apenas quando houver verbo claro de posição individual: vou, estou, meu, fixo, fico, marcar, seguro, cuido)
        bool hasSelfPositionIntent = lower.Contains("vou ") || lower.StartsWith("vou") ||
                                     lower.Contains("estou") || lower.Contains("to ") ||
                                     lower.Contains("meu") || lower.Contains("minha") ||
                                     lower.Contains("fixo") || lower.Contains("fico") ||
                                     lower.Contains("marcar") || lower.Contains("marco") ||
                                     lower.Contains("seguro") || lower.Contains("cuido");

        if (hasSelfPositionIntent)
        {
            foreach (var key in _mapProfileManager.CurrentProfile.VoiceSynonyms.Keys)
            {
                if (lower.Contains(key))
                {
                    bool isFixedLock = lower.Contains("estou") || lower.Contains("meu") || lower.Contains("fixo") || lower.Contains("fico");
                    if (isFixedLock)
                    {
                        _roleManager.LockHumanPosition(key);
                        human.PrintToChat($" {ChatColors.Green}🎙️ [Voz Swap]{ChatColors.Default} Posição {key.ToUpper()} {ChatColors.Gold}TRAVADA COMO SUA POSIÇÃO FIXA{ChatColors.Default}!");
                    }
                    else
                    {
                        human.PrintToChat($" {ChatColors.Green}🎙️ [Voz Swap]{ChatColors.Default} Posição {key.ToUpper()} assumida por voz!");
                    }

                    bool claimed = _roleManager.ClaimPositionForPlayer(human, key, teamBots, activePlan, _mapProfileManager);
                    if (claimed)
                    {
                        // Move fisicamente os bots usando a ordem individualizada do slot (V4.3)
                        foreach (var bot in teamBots)
                        {
                            if (!bot.IsValid || !bot.PawnIsAlive) continue;
                            var role = _roleManager.GetBotRole(bot);
                            if (activePlan.TryGetOrderForBot(bot.Slot, role, out var order))
                            {
                                var spot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                                if (spot != null)
                                {
                                    _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, order.Stance);
                                }
                            }
                        }
                    }

                    HumanCommunicationLogger.RecordCommunication(
                        "VOICE",
                        human.Team,
                        roundNum,
                        text,
                        "VOICE_POSITION_SWAP",
                        $"ClaimPosition({key}, fixed={isFixedLock}, claimed={claimed})",
                        0.01);
                    return;
                }
            }
        }

        // 8. Roteador Tático V4.3 (Camada 1 Léxica 0.01ms -> Camada 2 Classificador Ollama < 300ms)
        var pTeam = human.Team;
        int currentTick = Server.TickCount;
        if (_iglService.UtilityEngine.TryRouteHumanCommandLexically(pTeam, text, out string lexicalTacticId, out string lexicalReason))
        {
            var lexicalPlan = _iglService.UtilityEngine.TryMaterializeById(
                pTeam,
                lexicalTacticId,
                activePlan.RoundId,
                activePlan.RoundId,
                teamBots,
                _mapProfileManager,
                currentTick,
                TacticalDecisionSource.FAST_LEXICAL_ROUTER,
                0.01);

            if (lexicalPlan != null)
            {
                lexicalPlan.SelectionReason = $"{lexicalReason} (voice=\"{text}\")";
                if (pTeam == CsTeam.CounterTerrorist)
                    _ctController.OnRoundStart(lexicalPlan, teamBots);
                else
                    _midRoundAdapter.OnRoundStart(lexicalPlan, teamBots, human);

                HumanCommunicationLogger.RecordCommunication(
                    "VOICE",
                    pTeam,
                    roundNum,
                    text,
                    "FAST_LEXICAL_ROUTER",
                    $"{lexicalPlan.SelectedTactic} ({lexicalReason})",
                    lexicalPlan.LatencyMs);

                human.PrintToChat($" {ChatColors.Green}🎙️ [Voz IGL]{ChatColors.Default} Tática aplicada ({lexicalPlan.Source}, {lexicalPlan.LatencyMs:F2}ms): {ChatColors.Gold}{lexicalPlan.TacticName}{ChatColors.Default}!");
                return;
            }
        }

        human.PrintToChat($" {ChatColors.LightBlue}[Ollama IGL]{ChatColors.Default} Classificando call de voz complexa via IA...");
        int humanSlot = human.Slot;
        var ownEcon = _economyManager.GetTeamSnapshot(pTeam);
        var enemyEcon = _economyManager.GetTeamSnapshot(pTeam == CsTeam.CounterTerrorist ? CsTeam.Terrorist : CsTeam.CounterTerrorist);
        int capturedRoundId = activePlan.RoundId;

        Task.Run(async () =>
        {
            var classifiedPlan = await _iglService.ProcessHumanCommandAsync(
                pTeam,
                text,
                capturedRoundId,
                capturedRoundId,
                ownEcon,
                enemyEcon,
                null,
                _mapProfileManager,
                currentTick);

            HumanCommunicationLogger.RecordCommunication(
                "VOICE",
                pTeam,
                roundNum,
                text,
                classifiedPlan.Source.ToString(),
                $"{classifiedPlan.SelectedTactic} ({classifiedPlan.SelectionReason})",
                classifiedPlan.LatencyMs);

            Server.NextFrame(() =>
            {
                var freshHuman = Utilities.GetPlayerFromSlot(humanSlot);
                var freshBots = Utilities.GetPlayers().Where(p => p != null && p.IsValid && p.IsBot && p.Team == pTeam).ToList();
                if (pTeam == CsTeam.CounterTerrorist)
                {
                    _ctController.OnRoundStart(classifiedPlan, freshBots);
                }
                else
                {
                    _midRoundAdapter.OnRoundStart(classifiedPlan, freshBots, freshHuman);
                }

                if (freshHuman != null && freshHuman.IsValid)
                {
                    freshHuman.PrintToChat($" {ChatColors.Green}🎙️ [Voz IGL]{ChatColors.Default} Tática aplicada ({classifiedPlan.Source}, {classifiedPlan.LatencyMs:F1}ms): {ChatColors.Gold}{classifiedPlan.TacticName}{ChatColors.Default}!");
                }
            });
        });
    }
}
