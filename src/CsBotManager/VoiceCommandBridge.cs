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
            return;
        }

        // 1. Comando de Execução / Entrada Rápida
        if (lower.Contains("executa") || lower.Contains("entra") || lower.Contains("vai") || lower.Contains("go"))
        {
            _pacingController.TriggerExecute($"Voz do IGL: \"{text}\"", teamBots);
            return;
        }

        // 2. Comando de Recuo / Rotação Silenciosa
        if (lower.Contains("miou") || lower.Contains("recua") || lower.Contains("shift") || lower.Contains("rotaciona") || lower.Contains("gira"))
        {
            string targetSite = lower.Contains("a") ? "A" : "B";
            _midRoundAdapter.TriggerSilentRotate(targetSite, teamBots);
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
            return;
        }

        // 4. Comando de Cobertura / Salvar Arma
        if (lower.Contains("esconde") || lower.Contains("guarda") || lower.Contains("salva"))
        {
            foreach (var bot in teamBots.Where(b => b.PawnIsAlive))
            {
                _midRoundAdapter.ApplyAction(bot, MidRoundAction.HIDE_COVER, null);
            }
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
                if (role != null && activePlan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                {
                    var spot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                    if (spot != null)
                    {
                        _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, order.Stance);
                    }
                }
            }
            return;
        }

        // 7. Assumir Posição Fixa ou Temporária (C-03: opera sobre activePlan real)
        foreach (var key in _mapProfileManager.CurrentProfile.VoiceSynonyms.Keys)
        {
            if (lower.Contains(key))
            {
                if (lower.Contains("estou") || lower.Contains("meu") || lower.Contains("fixo") || lower.Contains("fico"))
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
                    // Move fisicamente o bot que cedeu a posição
                    foreach (var bot in teamBots)
                    {
                        if (!bot.IsValid || !bot.PawnIsAlive) continue;
                        var role = _roleManager.GetBotRole(bot);
                        if (role != null && activePlan.BotOrders.TryGetValue(RoleManager.GetOrderKey(role.Value), out var order))
                        {
                            var spot = _mapProfileManager.GetSpotById(order.StagingSpotId);
                            if (spot != null)
                            {
                                _locomotionDriver.NavigateToSpot(bot, spot, hurry: false, order.Stance);
                            }
                        }
                    }
                }
                return;
            }
        }

        human.PrintToChat($" {ChatColors.LightBlue}[Ollama IGL]{ChatColors.Default} Interpretando call tática por voz...");
    }
}
