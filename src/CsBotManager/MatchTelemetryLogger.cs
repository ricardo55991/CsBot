using System.Text;

using CounterStrikeSharp.API;

using CounterStrikeSharp.API.Core;

using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public enum TelemetryAdmissionResult
{
    ACCEPT_NORMAL,
    ACCEPT_ADMINISTRATIVE,
    ACCEPT_LATE_AUDIT,
    REJECT_WRONG_ROUND,
    REJECT_AFTER_SEAL,
    REJECT_CAPTURE_CLOSED,
    REJECT_INVALID_SEQUENCE
}

public class MatchTelemetryLogger
{
    private readonly BasePlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly BotLocomotionDriver _locomotionDriver;
    public RoundLifecycleManager? Lifecycle { get; set; }

    private bool _isEnabled = false;
    private string _currentFilePath = string.Empty;
    private readonly object _fileLock = new();
    private readonly HashSet<long> _sealedInternalRoundIds = new();

    // Rastreamento seguro de Thread Principal para invocações assíncronas (ex: IGL Timeout/Continuation)
    private static int _mainThreadId = -1;
    private static int _lastMainThreadTick = 0;
    private static float _lastMainThreadTime = 0.0f;

    public static void RecordMainThreadTick(int tick, float time)
    {
        _mainThreadId = Environment.CurrentManagedThreadId;
        _lastMainThreadTick = tick;
        _lastMainThreadTime = time;
    }

    public static bool IsMainThread => _mainThreadId > 0 && Environment.CurrentManagedThreadId == _mainThreadId;

    public static int SafeTickCount
    {
        get
        {
            if (IsMainThread)
            {
                try { _lastMainThreadTick = Server.TickCount; } catch { }
            }
            return _lastMainThreadTick;
        }
    }

    public static float SafeCurrentTime
    {
        get
        {
            if (IsMainThread)
            {
                try { _lastMainThreadTime = Server.CurrentTime; } catch { }
            }
            return _lastMainThreadTime;
        }
    }

    public static void SafePrintToConsole(string message)
    {
        if (IsMainThread)
        {
            try { Server.PrintToConsole(message); } catch { }
        }
        else
        {
            Console.WriteLine(message);
        }
    }

    // Rastreamento para Detector de Anomalias: slot -> (LastMovingTime, LowSpeedDuration)
    private readonly Dictionary<int, float> _lowSpeedStartTimes = new();
    private readonly Dictionary<int, float> _lastVelocities = new();
    private float _roundStartTime = 0.0f;
    private long _currentInternalRoundId = 0;
    private int _currentOfficialRoundNumber = 0;

    public bool IsEnabled => _isEnabled;
    public string CurrentFilePath => _currentFilePath;

    public MatchTelemetryLogger(
        BasePlugin plugin,
        MapProfileManager mapProfileManager,
        RoleManager roleManager,
        BotLocomotionDriver locomotionDriver,
        RoundLifecycleManager? lifecycle = null)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        _locomotionDriver = locomotionDriver;
        Lifecycle = lifecycle;
    }

    public TelemetryAdmissionResult Admit(
        string eventType,
        long? sourceRoundId,
        int? sourceTick,
        string sourceComponent,
        out EventAdmissionEnvelope envelope)
    {
        if (!_isEnabled)
        {
            envelope = null!;
            return TelemetryAdmissionResult.REJECT_CAPTURE_CLOSED;
        }

        int currentTick = SafeTickCount;
        if (currentTick == 0 && sourceTick.HasValue) currentTick = sourceTick.Value;
        string clock = GetRoundClockFormatted();

        if (Lifecycle == null)
        {
            envelope = new EventAdmissionEnvelope
            {
                RoundId = sourceRoundId ?? _currentInternalRoundId,
                OfficialRoundNumber = _currentOfficialRoundNumber,
                CurrentActiveRoundId = _currentInternalRoundId,
                GameTick = currentTick,
                OriginalGameTick = sourceTick ?? currentTick,
                MonotonicTimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                EventSequence = 0,
                RoundTimeFormatted = clock,
                EventPhase = RoundLifecyclePhase.ROUND_ACTIVE,
                LateEvent = false,
                LateReason = LateEventReason.NONE,
                SourceComponent = sourceComponent,
                Disposition = "NORMAL"
            };
            return TelemetryAdmissionResult.ACCEPT_NORMAL;
        }

        envelope = Lifecycle.CreateEventEnvelope(
            gameTick: currentTick,
            roundTimeFormatted: clock,
            sourceComponent: sourceComponent,
            originatingRoundId: sourceRoundId,
            originatingGameTick: sourceTick);

        if (envelope.LateEvent || _sealedInternalRoundIds.Contains(envelope.RoundId))
        {
            return TelemetryAdmissionResult.ACCEPT_LATE_AUDIT;
        }

        return TelemetryAdmissionResult.ACCEPT_NORMAL;
    }

    // Rotinas internas de baixo nível (únicas autorizadas a invocar AppendToFile)
    private void WriteNormal(string text) => AppendToFile(text);
    private void WriteAdministrative(string text) => AppendToFile(text);
    private void WriteLateAudit(string text) => AppendToFile(text);
    private void WriteFooter(string text) => AppendToFile(text);

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

            string[] dllCandidates = new[]
            {
                typeof(MatchTelemetryLogger).Assembly.Location,
                Path.Combine(AppContext.BaseDirectory, "CsBotManager.dll"),
                _plugin?.ModuleDirectory != null ? Path.Combine(_plugin.ModuleDirectory, "CsBotManager.dll") : null,
                @"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\CsBotManager.dll",
                Path.Combine(Directory.GetCurrentDirectory(), "CsBotManager.dll")
            }.Where(s => !string.IsNullOrWhiteSpace(s)).Select(s => s!).ToArray();

            string dllSha = ResolveFileSha256(dllCandidates, out string resolvedDllPath);

            string mapClean = Server.MapName?.ToLowerInvariant().Trim() ?? "de_mirage";
            string[] modelCandidates = new[]
            {
                Path.Combine(MicroMoveEngine.DefaultModelsDir, $"mlmove_{mapClean}.onnx"),
                Path.Combine(MicroMoveEngine.DefaultModelsDir, "mlmove_de_mirage.onnx"),
                @"H:\CS2_AI_Server\models\mlmove_de_mirage.onnx",
                @"H:\CS2_AI_Server\game\csgo\models\mlmove_de_mirage.onnx",
                @"H:\CS2_AI_Server\game\csgo\models\mlmove_cs2.onnx",
                @"H:\CS2_AI_Server\models\mlmove_cs2.onnx"
            };

            string modelSha = ResolveFileSha256(modelCandidates, out string resolvedModelPath);

            string pluginVer = _plugin?.ModuleVersion ?? "4.2.0";
            string assemblyVer = typeof(MatchTelemetryLogger).Assembly.GetName().Version?.ToString() ?? "4.2.0.0";
            string gitCommit = "v4.2-release";

            var sb = new StringBuilder();

            sb.AppendLine($"# CsBot - Telemetria Forense de Partida");
            sb.AppendLine($"**Data/Hora:** {DateTime.Now:yyyy-MM-dd HH:mm:ss} | **Mapa:** {Server.MapName}");

            string mlMoveBackend = _locomotionDriver.MicroMoveEngine?.BackendName ?? "PotentialFields-16Hz-CPU";

            sb.AppendLine($"**Status:** Gravação Ativa | **Arquivo:** `{Path.GetFileName(_currentFilePath)}` | **Motor MLMove:** `{mlMoveBackend}`");
            sb.AppendLine();
            sb.AppendLine(BuildHeaderMetadata(pluginVer, assemblyVer, gitCommit, dllSha, modelSha));
            sb.AppendLine();
            sb.AppendLine(BotSystemConfig.Default.FormatMarkdownSummary());

            sb.AppendLine();

            sb.AppendLine("---");

            sb.AppendLine();

            WriteAdministrative(sb.ToString());

            Server.PrintToChatAll($" {ChatColors.Green}[CsBot Debug]{ChatColors.Default} Telemetria {ChatColors.Gold}ATIVADA{ChatColors.Default} ({ChatColors.LightBlue}{mlMoveBackend}{ChatColors.Default})! Gravando em: {ChatColors.LightBlue}{Path.GetFileName(_currentFilePath)}{ChatColors.Default}");

            Server.PrintToConsole($"[CsBot Debug] Telemetria forense ATIVADA -> {_currentFilePath} | Motor MLMove: {mlMoveBackend}");
        }

        else
        {

            if (!string.IsNullOrEmpty(_currentFilePath))
            {

                WriteAdministrative($"\n> [!NOTE]\n> **Gravação de telemetria desativada pelo jogador às {DateTime.Now:HH:mm:ss}.**\n\n");
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

        _currentOfficialRoundNumber = roundNumber;
        _currentInternalRoundId = roundNumber;
        _roundStartTime = Server.CurrentTime;
        _lowSpeedStartTimes.Clear();
        _lastVelocities.Clear();
        ResetHealthTracking();

        var sb = new StringBuilder();
        sb.AppendLine($"## 🎮 Round {_currentOfficialRoundNumber} [Placar: CT {ctScore} x {trScore} TR]");

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

        WriteAdministrative(sb.ToString());
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

        _currentOfficialRoundNumber = rec.OfficialRoundNumber;
        _currentInternalRoundId = rec.InternalRoundId;
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
        WriteAdministrative(sb.ToString());
    }

    public void LogEvent(string category, string description)
    {
        if (!_isEnabled) return;
        var res = Admit(category, null, null, category, out var env);
        if (res == TelemetryAdmissionResult.ACCEPT_NORMAL)
        {
            WriteNormal($"- **`[{env.RoundTimeFormatted}]`** `[{category}]` {description}\n");
        }
        else if (res == TelemetryAdmissionResult.ACCEPT_LATE_AUDIT)
        {
            LogLateEvent(env, category, description);
        }
    }

    public void LogUtilityThrow(CCSPlayerController thrower, string utilityName, Vector origin, float pitch, float yaw, Vector? target)
    {
        if (!_isEnabled) return;
        var res = Admit("UTILITÁRIA", null, null, "BotLocomotionDriver", out var env);
        string targetStr = target != null ? $"-> Destino: `({target.X:F0}, {target.Y:F0}, {target.Z:F0})`" : "";
        string desc = $"**{thrower.PlayerName}** lançou **{utilityName}** de `({origin.X:F0}, {origin.Y:F0}, {origin.Z:F0})` [Mira: Pitch {pitch:F1}°, Yaw {yaw:F1}°] {targetStr}";

        if (res == TelemetryAdmissionResult.ACCEPT_NORMAL)
        {
            WriteNormal($"- **`[{env.RoundTimeFormatted}]`** `[UTILITÁRIA]` {desc}\n");
        }
        else if (res == TelemetryAdmissionResult.ACCEPT_LATE_AUDIT)
        {
            LogLateEvent(env, "UTILITÁRIA", desc);
        }
    }

    public void LogCombat(CCSPlayerController attacker, CCSPlayerController victim, string weapon, int damage, int remainingHp, float distanceUnits)
    {
        if (!_isEnabled) return;
        var res = Admit("COMBATE", null, null, "CombatLegacy", out var env);
        string desc = $"{attacker.PlayerName} -> {victim.PlayerName} ({weapon}) raw={damage} hp={remainingHp} dist={distanceUnits:F0}u";

        if (res == TelemetryAdmissionResult.ACCEPT_NORMAL)
        {
            WriteNormal($"- **`[{env.RoundTimeFormatted}]`** `[COMBATE-LEGACY]` {desc}\n");
        }
        else if (res == TelemetryAdmissionResult.ACCEPT_LATE_AUDIT)
        {
            LogLateEvent(env, "COMBATE-LEGACY", desc);
        }
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
        int tick = SafeTickCount;
        if (tick != _hurtDedupTick) { _hurtDedup.Clear(); _hurtDedupTick = tick; }
        var d = ComputeDamage(_lastKnownPlayerHealth, _hurtDedup, tick, attacker.Slot, victim.Slot, weapon, rawDamage, reportedHealth, armorDamage);
        if (!_isEnabled || d.IsDuplicate) return;

        var res = Admit("COMBATE", null, tick, "CombatAdapter", out var env);
        string sector = MirageSectorClassifier.ClassifyPlayer(victim).SectorName;
        if (d.AppliedDamage == 0)
        {
            string line = $"**{attacker.PlayerName}** atingiu **{victim.PlayerName}** com **{weapon}** a **{distanceUnits:F0}u** (raw={d.RawDamage}, armor={armorDamage}, motivo=`{d.ZeroDamageReason}`, setor: {sector})";
            if (res == TelemetryAdmissionResult.ACCEPT_NORMAL)
                WriteNormal($"- **`[{env.RoundTimeFormatted}]`** `[IMPACTO SEM DANO]` {line}\n");
            else if (res == TelemetryAdmissionResult.ACCEPT_LATE_AUDIT)
                LogLateEvent(env, "IMPACTO SEM DANO", line);
            return;
        }

        string hitLine = $"**{attacker.PlayerName}** causou **{d.AppliedDamage} HP** em **{victim.PlayerName}** com **{weapon}** a **{distanceUnits:F0}u** (HP {d.HpBefore}→{d.HpAfter}, raw={d.RawDamage}, overkill={d.OverkillDamage}, setor: {sector})";
        if (res == TelemetryAdmissionResult.ACCEPT_NORMAL)
            WriteNormal($"- **`[{env.RoundTimeFormatted}]`** `[COMBATE]` {hitLine}\n");
        else if (res == TelemetryAdmissionResult.ACCEPT_LATE_AUDIT)
            LogLateEvent(env, "COMBATE", hitLine);
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
        WriteLateAudit(sb.ToString());
    }

    public void LogRoundSealed(RoundStateRecord rec)
    {
        if (!_isEnabled) return;
        if (!_sealedInternalRoundIds.Add(rec.InternalRoundId)) return;
        WriteAdministrative($"- **`[{GetRoundClockFormatted()}]`** `[FIM_ROUND]` internal_round_id={rec.InternalRoundId} | round_oficial={rec.OfficialRoundNumber} | Vencedor: {rec.Winner} | Motivo: `{rec.EndReasonEnum}` ({rec.EndReasonCode}) — {rec.EndReasonDescription} | Placar: CT {rec.OfficialScoreAfterCt} x {rec.OfficialScoreAfterTr} TR | tick={rec.EndedAtTick}\n");
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
        sb.AppendLine($"- **end_tick:** {SafeTickCount} | **end_timestamp:** {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        sb.AppendLine();
        sb.AppendLine($"> [!NOTE]\n> capture_end_reason={reason}\n> captured_rounds={hist.Count}\n> complete_rounds={complete}\n> partial_round_id={(partial?.InternalRoundId.ToString() ?? "none")}");
        sb.AppendLine();

        // V4.2 Parte 8: Resumo Agregado do Tracker
        var allSamples = _locomotionDriver.ExecutionTracker.GetAllCompletedSamples();
        sb.AppendLine(TrackerMetricsAggregator.GenerateAggregatedReport(allSamples, _locomotionDriver));

        WriteFooter(sb.ToString());
        _isEnabled = false;
    }

    public static string ResolveFileSha256(string[] candidatePaths, out string resolvedPath)
    {
        var searched = new List<string>();
        foreach (var p in candidatePaths)
        {
            if (string.IsNullOrWhiteSpace(p)) continue;
            searched.Add(p);
            if (File.Exists(p))
            {
                try
                {
                    using var sha = System.Security.Cryptography.SHA256.Create();
                    using var stream = File.OpenRead(p);
                    byte[] hash = sha.ComputeHash(stream);
                    resolvedPath = p;
                    return Convert.ToHexStringLower(hash);
                }
                catch (Exception ex)
                {
                    resolvedPath = p;
                    return $"ERROR_{ex.GetType().Name}";
                }
            }
        }
        resolvedPath = string.Empty;
        return $"NOT_FOUND(Searched: {string.Join(" | ", searched)})";
    }

    public static string ComputeFileSha256(string? path)
    {
        if (string.IsNullOrEmpty(path) || !File.Exists(path)) return "NOT_FOUND";
        try
        {
            using var sha = System.Security.Cryptography.SHA256.Create();
            using var stream = File.OpenRead(path);
            byte[] hash = sha.ComputeHash(stream);
            return Convert.ToHexStringLower(hash);
        }
        catch (Exception ex)
        {
            return $"ERROR_{ex.GetType().Name}";
        }
    }

    public static string BuildHeaderMetadata(
        string pluginVersion,
        string assemblyVersion,
        string gitCommit,
        string dllSha256,
        string modelSha256)
    {
        var sb = new StringBuilder();
        sb.AppendLine("### 🛡️ Identificadores de Versão e Integridade");
        sb.AppendLine($"- **PluginVersion:** `{pluginVersion}`");
        sb.AppendLine($"- **AssemblyVersion:** `{assemblyVersion}`");
        sb.AppendLine($"- **GitCommit:** `{gitCommit}`");
        sb.AppendLine($"- **DllSha256:** `{dllSha256}`");
        sb.AppendLine($"- **ModelSha256:** `{modelSha256}`");
        return sb.ToString();
    }

    public static bool ValidateCaptureFooter(string content, out string statusReason, int? expectedCompleteRounds = null)
    {
        if (string.IsNullOrEmpty(content))
        {
            statusReason = "INCOMPLETE_CAPTURE: empty content";
            return false;
        }

        bool hasReason = content.Contains("capture_end_reason=MATCH_COMPLETED") ||
                         content.Contains("capture_end_reason:** `MATCH_COMPLETED`") ||
                         content.Contains("capture_end_reason: MATCH_COMPLETED");

        bool hasCapturedRounds = false;
        bool hasCompleteRounds = false;

        if (expectedCompleteRounds.HasValue)
        {
            int exp = expectedCompleteRounds.Value;
            hasCapturedRounds = content.Contains($"captured_rounds={exp}") ||
                                content.Contains($"captured_rounds:** {exp}") ||
                                content.Contains($"captured_rounds: {exp}");

            hasCompleteRounds = content.Contains($"complete_rounds={exp}") ||
                                content.Contains($"complete_rounds:** {exp}") ||
                                content.Contains($"complete_rounds: {exp}");
        }
        else
        {
            hasCapturedRounds = System.Text.RegularExpressions.Regex.IsMatch(content, @"captured_rounds(\*\*|\s)*[=:]\s*(`)?\d+");
            hasCompleteRounds = System.Text.RegularExpressions.Regex.IsMatch(content, @"complete_rounds(\*\*|\s)*[=:]\s*(`)?\d+");
        }

        bool hasNoPartial = content.Contains("partial_round_id=none") ||
                            content.Contains("partial_round_id:** none") ||
                            content.Contains("partial_round_id: none");

        if (hasReason && hasCapturedRounds && hasCompleteRounds && hasNoPartial)
        {
            statusReason = "VALID_CAPTURE";
            return true;
        }

        statusReason = "INCOMPLETE_CAPTURE: missing required completion markers";
        return false;
    }

    public void LogDeath(CCSPlayerController killer, CCSPlayerController victim, string weapon, bool isHeadshot, string sector)
    {
        if (!_isEnabled) return;
        var res = Admit("MORTE", null, null, "GameEvent", out var env);
        string hsStr = isHeadshot ? " (HEADSHOT 💥)" : "";
        string desc = $"**{killer.PlayerName}** eliminou **{victim.PlayerName}** com **{weapon}**{hsStr} no setor **{sector}**";

        if (res == TelemetryAdmissionResult.ACCEPT_NORMAL)
        {
            WriteNormal($"- **`[{env.RoundTimeFormatted}]`** `[MORTE]` {desc}\n");
        }
        else if (res == TelemetryAdmissionResult.ACCEPT_LATE_AUDIT)
        {
            LogLateEvent(env, "MORTE", desc);
        }
    }

    // ==============================================================================

    // Snapshots Táticos Compactos a cada 3.0s + Detector de Anomalias

    // ==============================================================================

    public void RecordPeriodicSnapshot(List<CCSPlayerController> players, TacticalPlan? plan)
    {
        if (!_isEnabled) return;
        if (Lifecycle != null && !Lifecycle.AllowsRuntimeGameplay()) return;
        if (_sealedInternalRoundIds.Contains(_currentInternalRoundId)) return;

        var res = Admit("SNAPSHOT", null, null, "Telemetry", out var env);
        if (res != TelemetryAdmissionResult.ACCEPT_NORMAL) return;

        string clock = env.RoundTimeFormatted;
        float now = SafeCurrentTime;

        var alivePlayers = players.Where(p => p != null && p.IsValid && p.PawnIsAlive).ToList();
        if (alivePlayers.Count == 0) return;

        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine($"<details><summary><b>📊 Snapshot Tático das [{clock}] ({alivePlayers.Count} vivos)</b></summary>");
        sb.AppendLine();
        sb.AppendLine("| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |");
        sb.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |");

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

            var microTraj = _locomotionDriver?.MicroMoveEngine?.GetTrajectory(p.Slot);
            string predAction = (microTraj != null && microTraj.IsOverrideActive)
                ? $"{microTraj.ActiveBehaviorTag} | {microTraj.Step0_Now.ToReadableString(yaw)}"
                : "Nenhuma";

            var lastDecision = _locomotionDriver?.Arbitrator?.GetLastDecision(p.Slot);
            string winningIntent = lastDecision != null
                ? $"{lastDecision.WinningIntent.Source}:{lastDecision.WinningIntent.Kind}({lastDecision.WinningIntent.Reason})"
                : "Nenhuma";

            long currentTick = SafeTickCount;

            var activeSample = _locomotionDriver?.ExecutionTracker?.GetActiveSample(p.Slot);
            string currentIntentOutcome = "Pending";
            if (activeSample != null && !activeSample.IsCompleted)
            {
                long sampleAge = currentTick > activeSample.IssuedTick ? (currentTick - activeSample.IssuedTick) : 0;
                currentIntentOutcome = $"Pending ({sampleAge}t/32t)";
            }

            var latestMeta = _locomotionDriver?.ExecutionTracker?.GetLatestDetailedMetadata(p.Slot);
            var latestExec = _locomotionDriver?.ExecutionTracker?.GetLatestOutcome(p.Slot);

            string lastCompletedOutcome;
            if (latestMeta != null)
            {
                long ageTicks = currentTick > latestMeta.Value.CompletedTick ? (currentTick - latestMeta.Value.CompletedTick) : 0;
                string actId = latestMeta.Value.LogicalActionId != Guid.Empty ? latestMeta.Value.LogicalActionId.ToString()[..8] : "none";
                string reasonStr = !string.IsNullOrEmpty(latestMeta.Value.PhysicalReason) ? $" [{latestMeta.Value.PhysicalReason}]" : "";
                lastCompletedOutcome = $"{latestMeta.Value.Physical} ({latestMeta.Value.Disp2D:F0}u/500ms, Age={ageTicks}t, Action={actId}, Kind={latestMeta.Value.Kind}){reasonStr}";
            }
            else
            {
                lastCompletedOutcome = latestExec != null
                    ? $"{latestExec.Value.Outcome} ({latestExec.Value.Disp2D:F0}u/500ms)"
                    : (speed > 15.0f ? "Movendo" : "None");
            }

            sb.AppendLine($"| {p.Slot} | {p.PlayerName} ({role}) | {team} | {hp} | {activeWeapon} | {sector} | `{pos.X:F0},{pos.Y:F0},{pos.Z:F0}` | `{pitch:F0}°,{yaw:F0}°` | {speedStr} | {stance} | {predAction} | {winningIntent} | {currentIntentOutcome} | {lastCompletedOutcome} |");

            // ======================================================================
            // DETECTOR AUTOMÁTICO DE ANOMALIAS ([⚠️ AUTO-ANOMALY] - Ajuste 9)
            // ======================================================================
            if (p.IsBot)
            {
                var navState = _locomotionDriver?.GetNavState(p.Slot);
                bool isAuthorizedHold = stance.Contains("PASSIVE") ||
                    (navState?.IsHoldingSpot == true && navState?.HoldDurationRemaining > 0f) ||
                    latestExec?.Outcome == MovementExecutionOutcome.AuthorizedHoldApplied ||
                    latestExec?.Outcome == MovementExecutionOutcome.FullStopApplied;

                if (speed < 5.0f && !isAuthorizedHold)
                {
                    if (!_lowSpeedStartTimes.TryGetValue(p.Slot, out float lowStart))
                    {
                        _lowSpeedStartTimes[p.Slot] = now;
                    }
                    else if (now - lowStart >= BotSystemConfig.Default.StuckTimeWindowSeconds)
                    {
                        string classification = latestExec?.Outcome == MovementExecutionOutcome.PossibleExternalControllerOverride
                            ? "POSSIBLE_EXTERNAL_CONTROLLER_OVERRIDE"
                            : ((latestExec?.Outcome == MovementExecutionOutcome.BlockedByGeometryOrNavigation || latestExec?.Outcome == MovementExecutionOutcome.BlockedByUnexpectedStopState)
                                ? "BLOCKED_BY_GEOMETRY_OR_NAV"
                                : "STANDSTILL_LIMIT_EXCEEDED");

                        LogAnomaly($"Bot **{p.PlayerName}** (`slot={p.Slot}`) sem progresso físico ({speed:F1}u/s por {now - lowStart:F1}s) em postura `{stance}` no setor `{sector}`! Classificação: `{classification}`");
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
        WriteNormal(sb.ToString());
    }

    public void LogAnomaly(string message)
    {
        if (!_isEnabled) return;
        var res = Admit("ANOMALY", null, null, "AnomalyDetector", out var env);
        if (res == TelemetryAdmissionResult.ACCEPT_NORMAL)
        {
            WriteNormal($"> [!WARNING]\n> **[⚠️ AUTO-ANOMALY - {env.RoundTimeFormatted}]:** {message}\n\n");
        }
        else if (res == TelemetryAdmissionResult.ACCEPT_LATE_AUDIT)
        {
            LogLateEvent(env, "AUTO-ANOMALY", message);
        }
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
        WriteAdministrative(sb.ToString());

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
                SafePrintToConsole($"[MatchTelemetryLogger] Erro ao gravar log: {ex.Message}");
            }
        }
    }

    public string GetRoundClockFormatted()
    {
        float currentTime = SafeCurrentTime;
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
        bool hasC4 = false;

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

                if (wname.Contains("C4"))
                {
                    hasC4 = true;
                }
                else if (BotLocomotionDriver.IsGrenadeWeapon(rawName) || wname.Contains("DECOY"))
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
            }
        }

        if (hasC4)
        {
            armor += " + 💣 C4 (Bomba)";
        }

        string nades = nadesList.Count > 0 ? string.Join(", ", nadesList) : "Nenhuma";
        return (primary, secondary, nades, armor);
    }
}
