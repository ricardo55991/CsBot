using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

/// <summary>
/// Controlador de Gravação Interativa de Spots no CS2.
/// Permite ao jogador voar livremente (ALT noclip), posicionar a mira,
/// e digitar "!spot_28" (ou "!spot 28") no chat para capturar com delay de 2s.
/// </summary>
public sealed class SpotRecordingController
{
    private readonly BasePlugin _plugin;
    private readonly string _moduleDirectory;
    private const string WorkspaceDir = @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot";
    private readonly string _recordedLogPath = Path.Combine(WorkspaceDir, "docs", "spot_recording", "recorded_spots_live.json");

    private static readonly Regex SpotCommandRegex = new(
        @"^[!/](?:spot[_ ]?(\d+)|spot\s+(\d+))$",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public bool IsRecordingModeActive { get; set; } = false;

    public SpotRecordingController(BasePlugin plugin, string moduleDirectory)
    {
        _plugin = plugin;
        _moduleDirectory = moduleDirectory;
        Directory.CreateDirectory(Path.GetDirectoryName(_recordedLogPath)!);
    }

    /// <summary>
    /// Configura o jogador humano ao spawnar apenas se o modo de gravação estiver ativado.
    /// Em partidas normais, permanece desativado garantindo bots normais e sem god mode.
    /// </summary>
    public void OnPlayerSpawn(CCSPlayerController player)
    {
        if (!IsRecordingModeActive) return;
        if (player == null || !player.IsValid || player.IsBot) return;

        player.ExecuteClientCommand("bind ALT noclip");
        Server.ExecuteCommand("sv_cheats 1; buddha 1; sv_falldamage_scale 0; sv_regeneration_force_on 1; bot_quota 0; bot_kick;");

        if (player.PlayerPawn.Value != null)
        {
            var pawn = player.PlayerPawn.Value;
            pawn.Health = 99999;
            pawn.MaxHealth = 99999;
            try { pawn.TakesDamage = false; } catch { }
        }

        player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Modo God / Imortalidade Ativado! HP: 99999. Pressione {ChatColors.Yellow}[ALT]{ChatColors.Default} para voar.");
        player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Ao encontrar o spot, mire e digite no chat: {ChatColors.Lime}!spot_XX{ChatColors.Default}");
    }

    /// <summary>
    /// Intercepta mensagens de chat procurando comandos como "!spot_28" ou "!spot 28".
    /// </summary>
    public bool TryHandleChatCommand(CCSPlayerController player, string message)
    {
        if (player == null || !player.IsValid || string.IsNullOrWhiteSpace(message))
            return false;

        string trimmed = message.Trim();
        if (trimmed.Equals("!gravador on", StringComparison.OrdinalIgnoreCase))
        {
            IsRecordingModeActive = true;
            Server.ExecuteCommand("sv_cheats 1; buddha 1; sv_falldamage_scale 0; sv_regeneration_force_on 1; bot_quota 0; bot_kick;");
            player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Modo Gravador ATIVADO! Bots expulsos e Modo God ligado.");
            return true;
        }

        if (trimmed.Equals("!gravador off", StringComparison.OrdinalIgnoreCase))
        {
            IsRecordingModeActive = false;
            Server.ExecuteCommand("sv_cheats 0; buddha 0; bot_quota 10; bot_quota_mode fill; exec ai_competitive.cfg;");
            player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Modo Gravador DESATIVADO! Partida competitiva restaurada com 10 bots.");
            return true;
        }

        if (!IsRecordingModeActive)
            return false;

        if (trimmed.Equals("!god", StringComparison.OrdinalIgnoreCase))
        {
            Server.ExecuteCommand("sv_cheats 1; buddha 1; sv_falldamage_scale 0; sv_regeneration_force_on 1;");
            if (player.PlayerPawn.Value != null)
            {
                player.PlayerPawn.Value.Health = 99999;
                player.PlayerPawn.Value.MaxHealth = 99999;
                try { player.PlayerPawn.Value.TakesDamage = false; } catch { }
            }
            player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Modo God ativado! HP: 99999.");
            return true;
        }

        if (trimmed.Equals("!noclip", StringComparison.OrdinalIgnoreCase) || trimmed.Equals("!fly", StringComparison.OrdinalIgnoreCase))
        {
            player.ExecuteClientCommand("noclip");
            player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Noclip (Voo) alternado!");
            return true;
        }

        if (trimmed.Equals("!kick", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Equals("!botkick", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Equals("!bot_kick", StringComparison.OrdinalIgnoreCase) ||
            trimmed.Equals("!kickbots", StringComparison.OrdinalIgnoreCase))
        {
            Server.ExecuteCommand("bot_quota 0; bot_kick;");
            player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Todos os bots foram expulsos!");
            return true;
        }

        var match = SpotCommandRegex.Match(trimmed);
        if (!match.Success)
            return false;

        string numStr = !string.IsNullOrEmpty(match.Groups[1].Value) ? match.Groups[1].Value : match.Groups[2].Value;
        if (!int.TryParse(numStr, out int spotNumber) || spotNumber <= 0)
        {
            player.PrintToChat($" {ChatColors.Red}[CsBot Gravador]{ChatColors.Default} Número de spot inválido: '{numStr}'. Use: !spot_28");
            return true;
        }

        ScheduleSpotCapture(player, spotNumber);
        return true;
    }

    /// <summary>
    /// Agenda a captura do spot com contagem regressiva de 2 segundos para o jogador firmar a mira.
    /// </summary>
    private void ScheduleSpotCapture(CCSPlayerController player, int spotNumber)
    {
        player.PrintToChat($" {ChatColors.Green}[CsBot Gravador]{ChatColors.Default} Gravando {ChatColors.Yellow}Spot #{spotNumber:D2}{ChatColors.Default} em {ChatColors.LightRed}2 segundos...{ChatColors.Default}");
        player.PrintToChat($" {ChatColors.DarkRed}► Mantenha a mira fixa no alvo e a postura (em pé ou agachado)!{ChatColors.Default}");
        player.PrintToCenter($"GRAVANDO SPOT #{spotNumber:D2} EM 2s...\nFique na mira e postura!");

        _plugin.AddTimer(2.0f, () =>
        {
            ExecuteCapture(player, spotNumber);
        });
    }

    /// <summary>
    /// Executa a leitura exata de posição, ângulos e agachamento, salvando nos perfis de mapa.
    /// </summary>
    private void ExecuteCapture(CCSPlayerController player, int spotNumber)
    {
        if (player == null || !player.IsValid || !player.PawnIsAlive || player.PlayerPawn.Value == null)
        {
            player?.PrintToChat($" {ChatColors.Red}[CsBot Gravador] Erro:{ChatColors.Default} Jogador inválido ou morto no momento da captura.");
            return;
        }

        var pawn = player.PlayerPawn.Value;
        var origin = pawn.AbsOrigin ?? new Vector(0, 0, 0);
        var angles = pawn.EyeAngles ?? new QAngle(0, 0, 0);

        // Detecção de postura (FL_DUCKING = 2 no Source Engine)
        bool isDucking = (pawn.Flags & 2) != 0;
        string stanceText = isDucking ? "Agachado" : "Em pé";
        string stanceEnum = isDucking ? "PASSIVE_HOLD" : "AGGRESSIVE_POKE";

        float x = (float)Math.Round(origin.X, 1);
        float y = (float)Math.Round(origin.Y, 1);
        float z = (float)Math.Round(origin.Z, 1);
        float pitch = (float)Math.Round(angles.X, 1);
        float yaw = (float)Math.Round(angles.Y, 1);

        // 1. Atualizar arquivo de perfil de_mirage.json no servidor e no workspace
        string spotId = UpdateProfileMirage(spotNumber, x, y, z, pitch, yaw, stanceEnum);

        // 2. Gravar no log de auditoria live
        AppendLiveRecord(spotNumber, spotId, x, y, z, pitch, yaw, stanceText);

        // 3. Notificar o jogador com destaque
        player.PrintToChat($" {ChatColors.Green}===================================================={ChatColors.Default}");
        player.PrintToChat($" {ChatColors.Lime}✔ SPOT #{spotNumber:D2} ({spotId}) GRAVADO COM SUCESSO!{ChatColors.Default}");
        player.PrintToChat($" {ChatColors.Default}► Coords: [{x:F1}, {y:F1}, {z:F1}] | Mira: Yaw {yaw:+0.0;-0.0;0.0}°, Pitch {pitch:+0.0;-0.0;0.0}°");
        player.PrintToChat($" {ChatColors.Default}► Postura: {ChatColors.Yellow}{stanceText}{ChatColors.Default}");
        player.PrintToChat($" {ChatColors.Gold}★ PODE IR PARA O PRÓXIMO! ★{ChatColors.Default}");
        player.PrintToChat($" {ChatColors.Green}===================================================={ChatColors.Default}");

        player.PrintToCenter($"✔ SPOT #{spotNumber:D2} GRAVADO!\nPODE IR PARA O PRÓXIMO!");

        // Som de confirmação
        player.ExecuteClientCommand("play sounds/ui/weapon_achievement.vsnd");

        Server.PrintToConsole($"[CsBot Gravador] Spot #{spotNumber:D2} ({spotId}) salvo: [{x}, {y}, {z}] Yaw={yaw} Pitch={pitch} Stance={stanceText}. Pode ir para o proximo.");
    }

    private string UpdateProfileMirage(int spotNumber, float x, float y, float z, float pitch, float yaw, string stanceEnum)
    {
        string[] targetPaths = new[]
        {
            Path.Combine(_moduleDirectory, "MapProfiles", "de_mirage.json"),
            Path.Combine(WorkspaceDir, "src", "CsBotManager", "MapProfiles", "de_mirage.json")
        };

        string spotId = $"spot_{spotNumber:D2}";

        foreach (var path in targetPaths)
        {
            if (!File.Exists(path)) continue;

            try
            {
                string jsonText = File.ReadAllText(path);
                var rootNode = JsonNode.Parse(jsonText);
                if (rootNode is not JsonObject rootObj) continue;

                if (rootObj["spots"] is JsonArray spotsArray)
                {
                    int index = spotNumber - 1;
                    JsonObject? targetSpot = null;

                    if (index >= 0 && index < spotsArray.Count && spotsArray[index] is JsonObject directSpot)
                    {
                        targetSpot = directSpot;
                    }
                    else
                    {
                        foreach (var node in spotsArray)
                        {
                            if (node is JsonObject sObj && sObj["id"]?.ToString() == spotId)
                            {
                                targetSpot = sObj;
                                break;
                            }
                        }
                    }

                    if (targetSpot != null)
                    {
                        spotId = targetSpot["id"]?.ToString() ?? spotId;
                        targetSpot["x"] = x;
                        targetSpot["y"] = y;
                        targetSpot["z"] = z;
                        targetSpot["pitch"] = pitch;
                        targetSpot["yaw"] = yaw;
                        targetSpot["recommended_stance"] = stanceEnum;
                        targetSpot["confidence"] = "HIGH";
                        targetSpot["validation_status"] = "HUMAN_LIVE_CALIBRATED";

                        var options = new JsonSerializerOptions { WriteIndented = true };
                        File.WriteAllText(path, rootNode.ToJsonString(options));
                    }
                }
            }
            catch (Exception ex)
            {
                Server.PrintToConsole($"[CsBot Gravador] Erro ao salvar perfil {path}: {ex.Message}");
            }
        }

        return spotId;
    }

    private void AppendLiveRecord(int spotNumber, string spotId, float x, float y, float z, float pitch, float yaw, string stance)
    {
        try
        {
            var record = new
            {
                timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                spot_number = spotNumber,
                spot_id = spotId,
                coords = new[] { x, y, z },
                aim = new { pitch, yaw },
                stance = stance
            };

            List<object> records = new();
            if (File.Exists(_recordedLogPath))
            {
                try
                {
                    string existingJson = File.ReadAllText(_recordedLogPath);
                    var parsed = JsonSerializer.Deserialize<List<object>>(existingJson);
                    if (parsed != null) records = parsed;
                }
                catch { }
            }

            records.Add(record);
            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(_recordedLogPath, JsonSerializer.Serialize(records, options));
        }
        catch (Exception ex)
        {
            Server.PrintToConsole($"[CsBot Gravador] Erro ao gravar log live: {ex.Message}");
        }
    }
}
