using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class HumanCommunicationLogEntry
{
    [JsonPropertyName("timestamp")]
    public string Timestamp { get; init; } = string.Empty;

    [JsonPropertyName("channel")]
    public string Channel { get; init; } = string.Empty; // VOICE, CHAT_TATICA, CHAT_POS, CHAT_COMMAND, AUTO_INTENT

    [JsonPropertyName("team")]
    public string Team { get; init; } = string.Empty;

    [JsonPropertyName("round_number")]
    public int RoundNumber { get; init; }

    [JsonPropertyName("raw_text")]
    public string RawText { get; init; } = string.Empty;

    [JsonPropertyName("routed_layer")]
    public string RoutedLayer { get; init; } = string.Empty; // VOICE_SWAP, FAST_LEXICAL_ROUTER, OLLAMA_CLASSIFIER, BUILTIN_COMMAND

    [JsonPropertyName("result_action")]
    public string ResultAction { get; init; } = string.Empty;

    [JsonPropertyName("latency_ms")]
    public double LatencyMs { get; init; }
}

/// <summary>
/// Grava de forma permanente todas as comunicações humanas (transcrições de voz e comandos de chat)
/// tanto em formato estruturado JSONL (para scripts de análise e evolução da Camada 1 FastLexicalCommandRouter)
/// quanto em formato legível .txt em H:\CS2_AI_Server\debug_logs\.
/// </summary>
public static class HumanCommunicationLogger
{
    private static readonly object _writeLock = new();
    public static string DefaultLogDirectory { get; set; } = @"H:\CS2_AI_Server\debug_logs";

    public static void RecordCommunication(
        string channel,
        CsTeam team,
        int roundNumber,
        string rawText,
        string routedLayer,
        string resultAction,
        double latencyMs = 0.0,
        string? customLogDir = null)
    {
        if (string.IsNullOrWhiteSpace(rawText)) return;

        string targetDir = customLogDir ?? DefaultLogDirectory;
        var entry = new HumanCommunicationLogEntry
        {
            Timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
            Channel = channel,
            Team = team == CsTeam.CounterTerrorist ? "CT" : (team == CsTeam.Terrorist ? "TR" : team.ToString()),
            RoundNumber = roundNumber,
            RawText = rawText.Trim(),
            RoutedLayer = routedLayer,
            ResultAction = resultAction,
            LatencyMs = Math.Round(latencyMs, 3)
        };

        try
        {
            lock (_writeLock)
            {
                if (!Directory.Exists(targetDir))
                {
                    Directory.CreateDirectory(targetDir);
                }

                string jsonlPath = Path.Combine(targetDir, "human_communications_log.jsonl");
                string txtPath = Path.Combine(targetDir, "human_communications_log.txt");

                string jsonLine = JsonSerializer.Serialize(entry);
                File.AppendAllText(jsonlPath, jsonLine + Environment.NewLine, Encoding.UTF8);

                string txtLine = $"[{entry.Timestamp}] [R{entry.RoundNumber:D2}] [{entry.Team}] [{entry.Channel}] \"{entry.RawText}\" -> Camada: {entry.RoutedLayer} | Resultado: {entry.ResultAction} ({entry.LatencyMs:F2}ms)";
                File.AppendAllText(txtPath, txtLine + Environment.NewLine, Encoding.UTF8);
            }
        }
        catch
        {
            // Evita que falhas de I/O de disco interrompam a partida
        }
    }
}
