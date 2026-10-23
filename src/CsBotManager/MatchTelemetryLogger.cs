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
            sb.AppendLine(BotSystemConfig.Default.FormatMarkdownSummary());

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
        if (!_isEnabled)
        {
            string flagFile = @"H:\CS2_AI_Server\debug_logs\auto_debug.flag";
            if (File.Exists(flagFile))
            {
                ToggleLogging(true);
            }
            else
            {
                return;
            }
        }

        _currentRound = roundNumber;

        _roundStartTime = Server.CurrentTime;

        _lowSpeedStartTimes.Clear();

        _lastVelocities.Clear();
        ResetHealthTracking();

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

    /// <summary>Cabeçalho forense V4: lifecycle, economia pré/pós por time, planos CT e TR separados.</summary>
    public void OnRoundStartV4(
        RoundStateRecord rec,
        int ctScore, int trScore,
        TeamEconomySnapshot ctEcon, TeamEconomySnapshot trEcon,
        TacticalPlan ctPlan, TacticalPlan trPlan,
        List<CCSPlayerController> players)
    {
        if (!_isEnabled)
        {
            if (File.Exists(@"H:\CS2_AI_Server\debug_logs\auto_debug.flag")) ToggleLogging(true);
            else return;
        }

        _currentRound = rec.OfficialRoundNumber;
        _roundStartTime = Server.CurrentTime;
        _lowSpeedStartTimes.Clear();
        _lastVelocities.Clear();
        ResetHealthTracking();

        var sb = new StringBuilder();
        string label = rec.MatchPhase == MatchLifecyclePhase.WARMUP ? "Warmup" : $"Round {rec.OfficialRoundNumber}";
        sb.AppendLine($"## 🎮 {label} [Placar: CT {ctScore} x {trScore} TR]");
        sb.AppendLine($"- **internal_round_id:** `{rec.InternalRoundId}` | **display_round_number:** `{rec.OfficialRoundNumber}` | **round_in_half:** `{rec.RoundNumberInHalf}` | **match_phase:** `{rec.MatchPhase}` | **round_phase:** `{rec.RoundPhase}` | **start_tick:** `{rec.StartedAtTick}`");
        sb.AppendLine($"- **Motor Micro-Movimento (16Hz):** `{_locomotionDriver.MicroMoveEngine?.BackendName ?? "PotentialFields-16Hz-CPU"}`");
        sb.AppendLine();

        sb.AppendLine("### 💵 Economia por Time (Pré-compra vs Pós-compra)");
        sb.AppendLine("| Time | PreBuyIntent | FinalBuyState | Completion | Caixa Médio Antes | Caixa Médio Depois | Gasto | Equip Antes | Equip Depois | Primárias | Rifles | SMGs | AWPs | Coletes | Capacetes | Kits | Utilitárias ($) | LossBonus |");
        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");
        foreach (var (tag, e) in new[] { ("CT", ctEcon), ("TR", trEcon) })
        {
            sb.AppendLine($"| {tag} | `{e.PurchaseIntent}` | `{e.FinalBuyState}` | `{e.CompletionState}` | ${e.AverageCashBeforeBuy} | ${e.AverageCashAfterBuy} | ${e.SpentDuringFreezeTime} | ${e.EquipmentValueBeforeBuy} | ${e.EquipmentValueAfterBuy} | {e.PrimaryWeaponCount} | {e.RifleCount} | {e.SmgCount} | {e.AwpCount} | {e.ArmorCount} | {e.HelmetCount} | {e.DefuseKitCount} | ${e.UtilityValue} | ${e.LossBonus} |");
        }
        sb.AppendLine();

        sb.AppendLine("### 💰 Loadout Pós-Compra");
        sb.AppendLine("| Slot | Jogador | Time | Role | Dinheiro | Arma Primária | Arma Secundária | Utilitárias | Colete/Kit |");
        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");
        foreach (var p in players.Where(p => p != null && p.IsValid && (p.Team == CsTeam.CounterTerrorist || p.Team == CsTeam.Terrorist)))
        {
            int money = p.InGameMoneyServices?.Account ?? 0;
            string team = p.Team == CsTeam.CounterTerrorist ? "CT" : "TR";
            string role = _roleManager.GetBotRole(p)?.ToString() ?? (p.IsBot ? "Bot" : "Humano");
            var (primary, secondary, nades, armorKit) = GetPlayerEquipmentStrings(p);
            sb.AppendLine($"| {p.Slot} | {p.PlayerName} | {team} | {role} | ${money} | {primary} | {secondary} | {nades} | {armorKit} |");
        }
        sb.AppendLine();

        foreach (var (tag, plan) in new[] { ("CT", ctPlan), ("TR", trPlan) })
        {
            sb.AppendLine($"#### 🤖 Auditoria IGL {tag}");
            sb.AppendLine($"- **decision_id:** `{plan.DecisionId}` | **source:** `{plan.Source}` | **latency:** `{plan.LatencyMs:F0}ms` | **cache_hit:** `{plan.CacheHit}` | **fallback:** `{plan.FallbackUsed}` ({plan.FallbackReason}) | **parse:** `{plan.ParseStatus}`");
            sb.AppendLine($"- **InitialTactic:** `{plan.InitialTactic}` | **CurrentTactic:** `{plan.CurrentTactic}` | **TacticRevision:** `{plan.TacticRevision}` | **Ritmo:** `{plan.RoundTempo}` | **Tier:** `{plan.PlayTier}`");
            if (plan.CandidateTactics.Count > 0)
            {
                string cands = string.Join("; ", plan.CandidateTactics.Select(c => plan.SelectionScores.TryGetValue(c, out var s) ? $"{c} ({s:F1})" : c));
                sb.AppendLine($"- **Candidatas:** {cands} | **penalidade_repetição:** `{plan.RepetitionPenaltyApplied}`");
            }
            sb.AppendLine($"- **Resumo:** {plan.TacticSummary}");
            if (!string.IsNullOrWhiteSpace(plan.RawJson))
            {
                sb.AppendLine("```json");
                sb.AppendLine(plan.RawJson);
                sb.AppendLine("```");
            }
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

        AppendToFile($"- **`[{clock}]`** `[COMBATE-LEGACY]` {attacker.PlayerName} -> {victim.PlayerName} ({weapon}) raw={damage} hp={remainingHp} dist={distanceUnits:F0}u\n");
    }

    // ==============================================================================
    // Bug 9: Cálculo de dano aplicado vs bruto, deduplicação e impacto sem dano
    // ==============================================================================
    private readonly Dictionary<int, int> _lastKnownPlayerHealth = new();
    private readonly HashSet<(int, int, int, string)> _hurtDedup = new();
    private int _hurtDedupTick = -1;

    public void ResetHealthTracking()
    {
        _lastKnownPlayerHealth.Clear();
        _hurtDedup.Clear();
        _hurtDedupTick = -1;
    }

    public readonly record struct DamageComputation(int HpBefore, int RawDamage, int HpAfter, int AppliedDamage, int OverkillDamage, bool IsDuplicate, string? ZeroDamageReason);

    /// <summary>Lógica pura (testável) de cálculo de dano. Atualiza o HP conhecido da vítima.</summary>
    public static DamageComputation ComputeDamage(
        Dictionary<int, int> lastKnownHealth,
        HashSet<(int, int, int, string)> dedup,
        int tick, int attackerSlot, int victimSlot, string weapon, int rawDamage, int reportedHealth, int armorDamage = 0)
    {
        if (!dedup.Add((tick, attackerSlot, victimSlot, weapon ?? string.Empty)))
            return new DamageComputation(0, rawDamage, 0, 0, 0, true, "DUPLICATE_EVENT_SAME_TICK");

        int hpBefore = lastKnownHealth.TryGetValue(victimSlot, out int hb) ? hb : 100;
        int hpAfter = Math.Clamp(reportedHealth, 0, 100);
        if (hpAfter > hpBefore) hpBefore = hpAfter; // callback fora de ordem: nunca gera dano negativo
        int applied = Math.Max(0, hpBefore - hpAfter);
        int overkill = Math.Max(0, rawDamage - applied);
        lastKnownHealth[victimSlot] = hpAfter;

        string? zeroReason = null;
        if (applied == 0)
        {
            if (hpBefore <= 0) zeroReason = "VICTIM_ALREADY_DEAD";
            else if (rawDamage <= 0 && armorDamage > 0) zeroReason = "ABSORBED_BY_ARMOR";
            else if (rawDamage <= 0) zeroReason = "ZERO_RAW_DAMAGE";
            else zeroReason = "HEALTH_UNCHANGED";
        }
        return new DamageComputation(hpBefore, rawDamage, hpAfter, applied, overkill, false, zeroReason);
    }

    public void LogCombatV4(CCSPlayerController attacker, CCSPlayerController victim, string weapon, int rawDamage, int reportedHealth, float distanceUnits, int armorDamage = 0)
    {
        int tick = Server.TickCount;
        if (tick != _hurtDedupTick) { _hurtDedup.Clear(); _hurtDedupTick = tick; }
        var d = ComputeDamage(_lastKnownPlayerHealth, _hurtDedup, tick, attacker.Slot, victim.Slot, weapon, rawDamage, reportedHealth, armorDamage);
        if (!_isEnabled || d.IsDuplicate) return;

        string clock = GetRoundClockFormatted();
        string sector = MirageSectorClassifier.ClassifyPlayer(victim).SectorName;
        if (d.AppliedDamage == 0)
        {
            AppendToFile($"- **`[{clock}]`** `[IMPACTO SEM DANO]` **{attacker.PlayerName}** atingiu **{victim.PlayerName}** com **{weapon}** a **{distanceUnits:F0}u** (raw={d.RawDamage}, armor={armorDamage}, motivo=`{d.ZeroDamageReason}`, setor: {sector})\n");
            return;
        }
        AppendToFile($"- **`[{clock}]`** `[COMBATE]` **{attacker.PlayerName}** causou **{d.AppliedDamage} HP** em **{victim.PlayerName}** com **{weapon}** a **{distanceUnits:F0}u** (HP {d.HpBefore}→{d.HpAfter}, raw={d.RawDamage}, overkill={d.OverkillDamage}, setor: {sector})\n");
    }

    public static (float Vel2D, float VelZ, float Vel3D) ComputeVelocity(float vx, float vy, float vz)
    {
        float v2 = MathF.Sqrt(vx * vx + vy * vy);
        return (v2, vz, MathF.Sqrt(vx * vx + vy * vy + vz * vz));
    }

    private static string FormatVelocity(Vector? v)
    {
        if (v == null) return "0.0";
        var (v2, vz, v3) = ComputeVelocity(v.X, v.Y, v.Z);
        if (MathF.Abs(vz) > 5f || v3 > 260f)
            return $"{v2:F1} (Z {vz:F0} / 3D {v3:F0} aéreo)";
        return $"{v2:F1}";
    }

    // ==============================================================================
    // Regra 10: Late events em seção de auditoria separada
    // ==============================================================================
    private readonly List<string> _lateEventsAudit = new();

    public void LogLateEvent(EventAdmissionEnvelope env, string eventName, string details)
    {
        lock (_lateEventsAudit)
        {
            _lateEventsAudit.Add($"| {env.EventSequence} | {eventName} | {env.RoundId} | {env.CurrentActiveRoundId} | {env.OriginalGameTick ?? env.GameTick} | {env.GameTick} | {env.SourceComponent} | {env.LateReason} | {env.Disposition} | {details.Replace("|", "/")} |");
        }
    }

    public void FlushLateEventsAudit()
    {
        List<string> rows;
        lock (_lateEventsAudit)
        {
            if (_lateEventsAudit.Count == 0) return;
            rows = _lateEventsAudit.ToList();
            _lateEventsAudit.Clear();
        }
        if (!_isEnabled) return;
        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine("### 🕒 Auditoria de Eventos Atrasados (Late Events)");
        sb.AppendLine("| seq | Evento | Round Original | Round Atual | Tick Original | Tick Processamento | Origem | Motivo | Disposição | Detalhes |");
        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");
        foreach (var r in rows) sb.AppendLine(r);
        sb.AppendLine();
        AppendToFile(sb.ToString());
    }

    public void LogRoundSealed(RoundStateRecord rec)
    {
        if (!_isEnabled) return;
        AppendToFile($"- **`[{GetRoundClockFormatted()}]`** `[FIM_ROUND]` internal_round_id={rec.InternalRoundId} | round_oficial={rec.OfficialRoundNumber} | Vencedor: {rec.Winner} | Motivo: `{rec.EndReasonEnum}` ({rec.EndReasonCode}) — {rec.EndReasonDescription} | Placar: CT {rec.OfficialScoreAfterCt} x {rec.OfficialScoreAfterTr} TR | tick={rec.EndedAtTick}\n");
        FlushLateEventsAudit();
    }

    public void CloseCapture(CaptureEndReason reason, RoundLifecycleManager lifecycle)
    {
        if (!_isEnabled) return;
        FlushLateEventsAudit();
        var hist = lifecycle.RoundHistory;
        int complete = hist.Count(r => r.Sealed && r.RoundEndReceived);
        var partial = hist.LastOrDefault(r => !r.Sealed);
        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine("---");
        sb.AppendLine("## 🏁 Encerramento da Captura");
        sb.AppendLine($"- **capture_end_reason:** `{reason}`");
        sb.AppendLine($"- **captured_rounds:** {hist.Count} | **complete_rounds:** {complete} | **partial_round_id:** {(partial?.InternalRoundId.ToString() ?? "none")}");
        sb.AppendLine($"- **late_events_total:** {lifecycle.LateEventCount}");
        sb.AppendLine($"- **end_tick:** {Server.TickCount} | **end_timestamp:** {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        AppendToFile(sb.ToString());
        _isEnabled = false;
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

        sb.AppendLine("| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Status Locomotion |");

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

            string sector = MirageSectorClassifier.ClassifyPlayer(p).SectorName;

            float pitch = pawn.EyeAngles?.X ?? 0.0f;

            float yaw = pawn.EyeAngles?.Y ?? 0.0f;

            var absVel = pawn.AbsVelocity;
            float speed = absVel != null ? ComputeVelocity(absVel.X, absVel.Y, absVel.Z).Vel2D : 0.0f;
            string speedStr = FormatVelocity(absVel);

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

                locoStatus += $" [{microTraj.ActiveBehaviorTag} | {microTraj.Step0_Now.ToReadableString(yaw)}]";
            }

            sb.AppendLine($"| {p.Slot} | {p.PlayerName} ({role}) | {team} | {hp} | {activeWeapon} | {sector} | `{pos.X:F0},{pos.Y:F0},{pos.Z:F0}` | `{pitch:F0}°,{yaw:F0}°` | {speedStr} | {stance} | {locoStatus} |");

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

        sb.AppendLine("| Slot | Jogador | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (Pitch,Yaw) | Vel 2D (u/s) |");

        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");

        foreach (var p in allPlayers.Where(p => p != null && p.IsValid && p.PawnIsAlive))
        {

            var pawn = p.PlayerPawn.Value;

            if (pawn == null || pawn.AbsOrigin == null) continue;

            string team = p.Team == CsTeam.CounterTerrorist ? "CT" : "TR";

            var pos = pawn.AbsOrigin;

            string sector = MirageSectorClassifier.ClassifyPlayer(p).SectorName;

            var activeWeapon = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName?.Replace("weapon_", "") ?? "none";

            var absVel = pawn.AbsVelocity;
            float speed = absVel != null ? ComputeVelocity(absVel.X, absVel.Y, absVel.Z).Vel2D : 0.0f;
            string speedStr = FormatVelocity(absVel);

            sb.AppendLine($"| {p.Slot} | {p.PlayerName} | {team} | {pawn.Health} | {activeWeapon} | {sector} | `{pos.X:F0},{pos.Y:F0},{pos.Z:F0}` | `{pawn.EyeAngles?.X:F0}°,{pawn.EyeAngles?.Y:F0}°` | {speedStr} |");
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

    private float _lastKnownServerTime = 0.0f;

    public string GetRoundClockFormatted()
    {
        float currentTime;
        try
        {
            currentTime = Server.CurrentTime;
            _lastKnownServerTime = currentTime;
        }
        catch
        {
            currentTime = _lastKnownServerTime;
        }

        float elapsed = currentTime - _roundStartTime;
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
                if (w == null || string.IsNullOrEmpty(w.DesignerName)) continue;

                string rawName = w.DesignerName;
                string wname = rawName.Replace("weapon_", "").ToUpperInvariant();

                if (wname.Contains("KNIFE") || wname.Contains("BAYONET")) continue;

                if (BotLocomotionDriver.IsGrenadeWeapon(rawName) || wname.Contains("DECOY"))
                {
                    nadesList.Add(wname);
                }
                else if (CombatAdapter.IsPrimaryWeapon(rawName))
                {
                    primary = wname;
                }
                else if (CombatAdapter.IsSecondaryWeapon(rawName))
                {
                    secondary = wname;
                }
                else if (wname.Contains("C4"))
                {
                    primary = "C4";
                }
            }
        }

        string nades = nadesList.Count > 0 ? string.Join(", ", nadesList) : "Nenhuma";
        return (primary, secondary, nades, armor);
    }
}
