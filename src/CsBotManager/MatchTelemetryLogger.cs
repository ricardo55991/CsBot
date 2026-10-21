using System.Text;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class MatchTelemetryLogger
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly BotLocomotionDriver _locomotionDriver;

    private bool _isEnabled = false;
    private string _currentFilePath = string.Empty;
    private readonly object _fileLock = new();

    // Rastreamento para Detector de Anomalias: slot -> (LastMovingTime, LowSpeedDuration)
    private readonly Dictionary<int, float> _lowSpeedStartTimes = new();
    private readonly Dictionary<int, float> _lastVelocities = new();

    private float _roundStartTime = 0.0f;
    private int _currentRound = 0;

    public bool IsEnabled => _isEnabled;
    public string CurrentFilePath => _currentFilePath;

    public MatchTelemetryLogger(
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

    public void ToggleLogging(bool? forceState = null)
    {
        _isEnabled = forceState ?? !_isEnabled;

        if (_isEnabled)
        {
            string logDir = @"H:\CS2_AI_Server\debug_logs";
            if (!Directory.Exists(logDir))
            {
                Directory.CreateDirectory(logDir);
            }

            string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            _currentFilePath = Path.Combine(logDir, $"debug_match_{timestamp}.md");

            var sb = new StringBuilder();
            sb.AppendLine($"# CsBot - Telemetria Forense de Partida");
            sb.AppendLine($"**Data/Hora:** {DateTime.Now:yyyy-MM-dd HH:mm:ss} | **Mapa:** {Server.MapName}");
            string mlMoveBackend = _locomotionDriver.MicroMoveEngine?.BackendName ?? "PotentialFields-16Hz-CPU";
            sb.AppendLine($"**Status:** Gravação Ativa | **Arquivo:** `{Path.GetFileName(_currentFilePath)}` | **Motor MLMove:** `{mlMoveBackend}`");
            sb.AppendLine();
            sb.AppendLine("---");
            sb.AppendLine();

            AppendToFile(sb.ToString());
            Server.PrintToChatAll($" {ChatColors.Green}[CsBot Debug]{ChatColors.Default} Telemetria {ChatColors.Gold}ATIVADA{ChatColors.Default} ({ChatColors.LightBlue}{mlMoveBackend}{ChatColors.Default})! Gravando em: {ChatColors.LightBlue}{Path.GetFileName(_currentFilePath)}{ChatColors.Default}");
            Server.PrintToConsole($"[CsBot Debug] Telemetria forense ATIVADA -> {_currentFilePath} | Motor MLMove: {mlMoveBackend}");
        }
        else
        {
            if (!string.IsNullOrEmpty(_currentFilePath))
            {
                AppendToFile($"\n> [!NOTE]\n> **Gravação de telemetria desativada pelo jogador às {DateTime.Now:HH:mm:ss}.**\n\n");
            }
            Server.PrintToChatAll($" {ChatColors.Red}[CsBot Debug]{ChatColors.Default} Telemetria forense {ChatColors.Grey}DESATIVADA{ChatColors.Default}.");
        }
    }

    public void OnRoundStart(int roundNumber, int ctScore, int trScore, BuyState ctBuy, BuyState trBuy, TacticalPlan plan, string rawIglJson, List<CCSPlayerController> players)
    {
        if (!_isEnabled) return;

        _currentRound = roundNumber;
        _roundStartTime = Server.CurrentTime;
        _lowSpeedStartTimes.Clear();
        _lastVelocities.Clear();

        var sb = new StringBuilder();
        sb.AppendLine($"## 🎮 Round {_currentRound} [Placar: CT {ctScore} x {trScore} TR]");
        sb.AppendLine($"- **BuyState CT:** `{ctBuy}` | **BuyState TR:** `{trBuy}`");
        sb.AppendLine($"- **Tática Escolhida:** `{plan.TacticName}` (Tier: `{plan.PlayTier}`, Ritmo: `{plan.RoundTempo}`)");
        sb.AppendLine($"- **Resumo Tático:** {plan.TacticSummary}");
        sb.AppendLine($"- **Motor Micro-Movimento (16Hz):** `{_locomotionDriver.MicroMoveEngine?.BackendName ?? "PotentialFields-16Hz-CPU"}`");
        sb.AppendLine();

        // Inventário e Economia de Cada Jogador
        sb.AppendLine("### 💰 Economia e Loadout Inicial");
        sb.AppendLine("| Slot | Jogador | Time | Dinheiro | Arma Primária | Arma Secundária | Utilitárias | Colete/Kit |");
        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");

        foreach (var p in players.Where(p => p != null && p.IsValid))
        {
            var moneyServices = p.InGameMoneyServices;
            int money = moneyServices?.Account ?? 0;
            string team = p.Team == CsTeam.CounterTerrorist ? "CT" : "TR";
            string role = _roleManager.GetBotRole(p)?.ToString() ?? (p.IsBot ? "Bot" : "Humano");

            var (primary, secondary, nades, armorKit) = GetPlayerEquipmentStrings(p);
            sb.AppendLine($"| {p.Slot} | {p.PlayerName} ({role}) | {team} | ${money} | {primary} | {secondary} | {nades} | {armorKit} |");
        }

        sb.AppendLine();
        if (!string.IsNullOrEmpty(rawIglJson))
        {
            sb.AppendLine("#### 🤖 Decisão Estruturada da IA (Ollama JSON)");
            sb.AppendLine("```json");
            sb.AppendLine(rawIglJson);
            sb.AppendLine("```");
            sb.AppendLine();
        }

        sb.AppendLine("### ⏱️ Linha do Tempo de Eventos");
        AppendToFile(sb.ToString());
    }

    public void LogEvent(string category, string description)
    {
        if (!_isEnabled) return;

        string clock = GetRoundClockFormatted();
        AppendToFile($"- **`[{clock}]`** `[{category}]` {description}\n");
    }

    public void LogUtilityThrow(CCSPlayerController thrower, string utilityName, Vector origin, float pitch, float yaw, Vector? target)
    {
        if (!_isEnabled) return;

        string clock = GetRoundClockFormatted();
        string targetStr = target != null ? $"-> Destino: `({target.X:F0}, {target.Y:F0}, {target.Z:F0})`" : "";
        AppendToFile($"- **`[{clock}]`** `[UTILITÁRIA]` **{thrower.PlayerName}** lançou **{utilityName}** de `({origin.X:F0}, {origin.Y:F0}, {origin.Z:F0})` [Mira: Pitch {pitch:F1}°, Yaw {yaw:F1}°] {targetStr}\n");
    }

    public void LogCombat(CCSPlayerController attacker, CCSPlayerController victim, string weapon, int damage, int remainingHp, float distanceUnits)
    {
        if (!_isEnabled) return;

        string clock = GetRoundClockFormatted();
        AppendToFile($"- **`[{clock}]`** `[COMBATE]` **{attacker.PlayerName}** causou **{damage} HP** em **{victim.PlayerName}** com **{weapon}** a **{distanceUnits:F0}u** (Vítima: {remainingHp} HP restante)\n");
    }

    public void LogDeath(CCSPlayerController killer, CCSPlayerController victim, string weapon, bool isHeadshot, string sector)
    {
        if (!_isEnabled) return;

        string clock = GetRoundClockFormatted();
        string hsStr = isHeadshot ? " (HEADSHOT 💥)" : "";
        AppendToFile($"- **`[{clock}]`** `[MORTE]` **{killer.PlayerName}** eliminou **{victim.PlayerName}** com **{weapon}**{hsStr} no setor **{sector}**\n");
    }

    // ==============================================================================
    // Snapshots Táticos Compactos a cada 3.0s + Detector de Anomalias
    // ==============================================================================
    public void RecordPeriodicSnapshot(List<CCSPlayerController> players, TacticalPlan? plan)
    {
        if (!_isEnabled) return;

        string clock = GetRoundClockFormatted();
        float now = Server.CurrentTime;

        var alivePlayers = players.Where(p => p != null && p.IsValid && p.PawnIsAlive).ToList();
        if (alivePlayers.Count == 0) return;

        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine($"<details><summary><b>📊 Snapshot Tático das [{clock}] ({alivePlayers.Count} vivos)</b></summary>");
        sb.AppendLine();
        sb.AppendLine("| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel (u/s) | Stance | Status Locomotion |");
        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");

        foreach (var p in alivePlayers)
        {
            var pawn = p.PlayerPawn.Value;
            if (pawn == null || pawn.AbsOrigin == null) continue;

            string role = _roleManager.GetBotRole(p)?.ToString() ?? (p.IsBot ? "Bot" : "Humano");
            string team = p.Team == CsTeam.CounterTerrorist ? "CT" : "TR";
            int hp = pawn.Health;

            var activeWeapon = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName?.Replace("weapon_", "") ?? "none";
            var pos = pawn.AbsOrigin;
            var cp = _mapProfileManager.FindChokepointAt(pos.X, pos.Y, pos.Z);
            string sector = cp?.Name ?? "Transição";

            float pitch = pawn.EyeAngles?.X ?? 0.0f;
            float yaw = pawn.EyeAngles?.Y ?? 0.0f;
            float speed = pawn.AbsVelocity?.Length() ?? 0.0f;

            string stance = "PASSIVE";
            if (p.IsBot && plan != null)
            {
                var r = _roleManager.GetBotRole(p);
                if (r != null && plan.BotOrders.TryGetValue(RoleManager.GetOrderKey(r.Value), out var order))
                {
                    stance = order.Stance.ToString();
                }
            }

            string locoStatus = speed > 15.0f ? "Movendo" : "Parado";
            var microTraj = _locomotionDriver.MicroMoveEngine?.GetTrajectory(p.Slot);
            if (microTraj != null && microTraj.IsOverrideActive)
            {
                locoStatus += $" [{microTraj.ActiveBehaviorTag}]";
            }
            sb.AppendLine($"| {p.Slot} | {p.PlayerName} ({role}) | {team} | {hp} | {activeWeapon} | {sector} | `{pos.X:F0},{pos.Y:F0},{pos.Z:F0}` | `{pitch:F0}°,{yaw:F0}°` | {speed:F1} | {stance} | {locoStatus} |");

            // ======================================================================
            // DETECTOR AUTOMÁTICO DE ANOMALIAS ([⚠️ AUTO-ANOMALY])
            // ======================================================================
            if (p.IsBot)
            {
                // Anomalia 1: Bot deveria estar se movendo com velocidade < 5u/s por mais de 4s
                if (speed < 5.0f && stance.Contains("POKE"))
                {
                    if (!_lowSpeedStartTimes.TryGetValue(p.Slot, out float lowStart))
                    {
                        _lowSpeedStartTimes[p.Slot] = now;
                    }
                    else if (now - lowStart >= 4.0f)
                    {
                        LogAnomaly($"Bot **{p.PlayerName}** ficou com velocidade baixa ({speed:F1}u/s) por {now - lowStart:F1}s em postura {stance} no setor {sector}!");
                        _lowSpeedStartTimes[p.Slot] = now + 10.0f; // Cooldown do alerta
                    }
                }
                else
                {
                    _lowSpeedStartTimes.Remove(p.Slot);
                }
            }
        }

        sb.AppendLine();
        sb.AppendLine("</details>");
        sb.AppendLine();

        AppendToFile(sb.ToString());
    }

    public void LogAnomaly(string message)
    {
        if (!_isEnabled) return;
        string clock = GetRoundClockFormatted();
        AppendToFile($"> [!WARNING]\n> **[⚠️ AUTO-ANOMALY - {clock}]:** {message}\n\n");
    }

    // ==============================================================================
    // Marcador do Jogador (!nota <texto>)
    // ==============================================================================
    public void RecordPlayerNote(CCSPlayerController player, string noteText, List<CCSPlayerController> allPlayers, TacticalPlan? plan)
    {
        if (!_isEnabled)
        {
            // Ativa automaticamente se o jogador usar !nota
            ToggleLogging(true);
        }

        string clock = GetRoundClockFormatted();

        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine($"### 🚩 [MARCADOR DO JOGADOR - Relógio: {clock}]");
        sb.AppendLine($"> **Autor:** {player.PlayerName} ({player.Team})");
        sb.AppendLine($"> **Observação:** *\"{noteText}\"*");
        sb.AppendLine();
        sb.AppendLine("#### 📸 Estado Instantâneo de Todos os Jogadores no Milissegundo:");
        sb.AppendLine("| Slot | Jogador | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (Pitch,Yaw) | Vel (u/s) |");
        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");

        foreach (var p in allPlayers.Where(p => p != null && p.IsValid && p.PawnIsAlive))
        {
            var pawn = p.PlayerPawn.Value;
            if (pawn == null || pawn.AbsOrigin == null) continue;

            string team = p.Team == CsTeam.CounterTerrorist ? "CT" : "TR";
            var pos = pawn.AbsOrigin;
            var cp = _mapProfileManager.FindChokepointAt(pos.X, pos.Y, pos.Z);
            string sector = cp?.Name ?? "Transição";
            var activeWeapon = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName?.Replace("weapon_", "") ?? "none";
            float speed = pawn.AbsVelocity?.Length() ?? 0.0f;

            sb.AppendLine($"| {p.Slot} | {p.PlayerName} | {team} | {pawn.Health} | {activeWeapon} | {sector} | `{pos.X:F0},{pos.Y:F0},{pos.Z:F0}` | `{pawn.EyeAngles?.X:F0}°,{pawn.EyeAngles?.Y:F0}°` | {speed:F1} |");
        }

        sb.AppendLine();
        AppendToFile(sb.ToString());

        player.PrintToChat($" {ChatColors.Green}[CsBot Debug]{ChatColors.Default} 🚩 Nota registrada no log: {ChatColors.Gold}\"{noteText}\"{ChatColors.Default}");
    }

    private void AppendToFile(string text)
    {
        if (string.IsNullOrEmpty(_currentFilePath)) return;
        lock (_fileLock)
        {
            try
            {
                File.AppendAllText(_currentFilePath, text, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Server.PrintToConsole($"[MatchTelemetryLogger] Erro ao gravar log: {ex.Message}");
            }
        }
    }

    private string GetRoundClockFormatted()
    {
        float elapsed = Server.CurrentTime - _roundStartTime;
        float remaining = Math.Max(0.0f, 115.0f - elapsed);
        int mins = (int)(remaining / 60.0f);
        int secs = (int)(remaining % 60.0f);
        return $"{mins:D2}:{secs:D2}";
    }

    private static (string Primary, string Secondary, string Nades, string ArmorKit) GetPlayerEquipmentStrings(CCSPlayerController player)
    {
        string primary = "Nenhuma";
        string secondary = "Pistola Base";
        var nadesList = new List<string>();
        string armor = "Sem Colete";

        var pawn = player.PlayerPawn.Value;
        if (pawn == null) return (primary, secondary, "Nenhuma", armor);

        var itemServices = pawn.ItemServices as CCSPlayer_ItemServices;
        if (pawn.ArmorValue > 0)
        {
            armor = (itemServices?.HasHelmet ?? false) ? $"Colete+Cap ({pawn.ArmorValue})" : $"Colete ({pawn.ArmorValue})";
        }
        if (itemServices?.HasDefuser ?? false)
        {
            armor += " + Kit Defuse";
        }

        var weapons = pawn.WeaponServices?.MyWeapons;
        if (weapons != null)
        {
            foreach (var handle in weapons)
            {
                var w = handle.Value;
                if (w == null || w.DesignerName == null) continue;
                string wname = w.DesignerName.Replace("weapon_", "").ToUpperInvariant();

                if (wname.Contains("KNIFE") || wname.Contains("BAYONET")) continue;

                if (wname.Contains("FLASH") || wname.Contains("SMOKE") || wname.Contains("HEGRENADE") || wname.Contains("MOLOTOV") || wname.Contains("INC"))
                {
                    nadesList.Add(wname);
                }
                else if (wname.Contains("GLOCK") || wname.Contains("USP") || wname.Contains("DEAGLE") || wname.Contains("P250") || wname.Contains("ELITE") || wname.Contains("TEC9") || wname.Contains("CZ75") || wname.Contains("FIVESEVEN"))
                {
                    secondary = wname;
                }
                else
                {
                    primary = wname;
                }
            }
        }

        string nadesStr = nadesList.Count > 0 ? string.Join(", ", nadesList) : "Nenhuma";
        return (primary, secondary, nadesStr, armor);
    }
}
