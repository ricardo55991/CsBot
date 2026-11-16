using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class SpotTestEventRecord
{
    [JsonPropertyName("EventType")]
    public string EventType { get; set; } = string.Empty;

    [JsonPropertyName("TimestampUtc")]
    public string TimestampUtc { get; set; } = string.Empty;

    [JsonPropertyName("ProfileVersion")]
    public int ProfileVersion { get; set; }

    [JsonPropertyName("SpotId")]
    public string SpotId { get; set; } = string.Empty;

    [JsonPropertyName("AttemptId")]
    public int AttemptId { get; set; }

    [JsonPropertyName("BotSlot")]
    public int BotSlot { get; set; }

    [JsonPropertyName("StartPosition")]
    public float[] StartPosition { get; set; } = Array.Empty<float>();

    [JsonPropertyName("TargetPosition")]
    public float[] TargetPosition { get; set; } = Array.Empty<float>();

    [JsonPropertyName("StartTick")]
    public int StartTick { get; set; }

    [JsonPropertyName("EndTick")]
    public int EndTick { get; set; }

    [JsonPropertyName("ElapsedMs")]
    public float ElapsedMs { get; set; }

    [JsonPropertyName("DistanceRemaining")]
    public float DistanceRemaining { get; set; }

    [JsonPropertyName("RepathCount")]
    public int RepathCount { get; set; }

    [JsonPropertyName("RecoveryCount")]
    public int RecoveryCount { get; set; }

    [JsonPropertyName("GeometryBlockCount")]
    public int GeometryBlockCount { get; set; }

    [JsonPropertyName("AppliedNoProgressCount")]
    public int AppliedNoProgressCount { get; set; }

    [JsonPropertyName("FinalPosition")]
    public float[] FinalPosition { get; set; } = Array.Empty<float>();

    [JsonPropertyName("Result")]
    public string Result { get; set; } = string.Empty;

    [JsonPropertyName("DllSha256")]
    public string DllSha256 { get; set; } = string.Empty;

    [JsonPropertyName("ProfileSha256")]
    public string ProfileSha256 { get; set; } = string.Empty;
}

public sealed class SpotTestRunner
{
    private sealed class SpotTestJob
    {
        public int ProfileVersion { get; init; }
        public string ProfilePath { get; init; } = string.Empty;
        public string ProfileSha256 { get; init; } = string.Empty;
        public TacticalSpot TargetSpot { get; init; } = new();
        public int AttemptId { get; init; }
        public Vector StartPos { get; init; } = new(0, 0, 0);
    }

    public static readonly string[] AlteredSpotIds20 = new[]
    {
        "ct_a_ticket_passive",
        "ct_a_firebox_oneanddone",
        "ct_a_ninja_hide",
        "ct_a_triple_jiggle",
        "ct_a_stairs_cross",
        "ct_a_jungle_support",
        "ct_a_palace_close_poke",
        "ct_mid_window_crouch",
        "ct_mid_window_deep_awp",
        "ct_mid_connector_headshot",
        "ct_mid_short_catwalk",
        "ct_mid_underpass_peek",
        "ct_b_van_peek",
        "ct_b_market_window",
        "ct_spawn_safe",
        "tr_staging_a_ramp",
        "tr_staging_palace_room",
        "tr_staging_underpass_top",
        "ct_retake_a_connector",
        "ct_retake_a_jungle"
    };

    private readonly CsBotManagerPlugin _plugin;
    private readonly MapProfileManager _mapProfileManager;
    private readonly BotLocomotionDriver _locomotionDriver;
    private readonly Queue<SpotTestJob> _jobQueue = new();

    private SpotTestJob? _currentJob;
    private int _testBotSlot = -1;
    private int _settleTicksRemaining = 0;
    private int _startTick = 0;
    private float _startTime = 0f;
    private float _lastKnownRepathTime = 0f;
    private int _lastKnownStuckCount = 0;
    private int _repathCount = 0;
    private int _recoveryCount = 0;
    private int _geometryBlockCount = 0;
    private int _appliedNoProgressCount = 0;
    private int _lowSpeedConsecutiveTicks = 0;
    private Vector _windowStartPos = new(0, 0, 0);
    private int _windowTicks = 0;

    private string _rawJsonlPathServer = @"H:\CS2_AI_Server\debug_logs\raw_spot_test_events.jsonl";
    private string _rawJsonlPathRepo = @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_6\raw_spot_test_events.jsonl";
    private string _dllSha256 = string.Empty;

    public bool IsActive => _currentJob != null || _jobQueue.Count > 0;
    public float TimeoutSeconds { get; set; } = 5.0f;

    public SpotTestRunner(
        CsBotManagerPlugin plugin,
        MapProfileManager mapProfileManager,
        BotLocomotionDriver locomotionDriver)
    {
        _plugin = plugin;
        _mapProfileManager = mapProfileManager;
        _locomotionDriver = locomotionDriver;
        _dllSha256 = ResolveDllSha256();
    }

    private static string ResolveDllSha256()
    {
        string[] candidates = new[]
        {
            typeof(SpotTestRunner).Assembly.Location,
            @"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\CsBotManager.dll",
            @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\src\CsBotManager\bin\Release\net10.0\CsBotManager.dll",
            @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\src\CsBotManager\bin\Debug\net10.0\CsBotManager.dll"
        };
        foreach (var c in candidates)
        {
            if (!string.IsNullOrEmpty(c) && File.Exists(c))
            {
                string h = ComputeFileSha256(c);
                if (!string.IsNullOrEmpty(h)) return h;
            }
        }
        return string.Empty;
    }

    public static Vector GetCanonicalStartPositionForSpot(string spotId)
    {
        string id = spotId.ToLowerInvariant();

        // Posição inicial canônica de aproximação da zona/setor esperada (mesma para V1 e V2),
        // usando medoids empíricos de áreas caminháveis reais (444 demos) a ~180u-300u do landmark esperado:
        return id switch
        {
            // Bombsite A (aproximação CT/Site A / Jungle / Escadas / Palácio)
            "ct_a_ticket_passive" => new Vector(-1072.6f, -2326.9f, -168.0f),
            "ct_a_firebox_oneanddone" => new Vector(-289.8f, -2161.5f, -173.9f),
            "ct_a_ninja_hide" => new Vector(-620.0f, -2320.0f, -168.0f),
            "ct_a_triple_jiggle" => new Vector(-842.5f, -2253.7f, -174.8f),
            "ct_a_stairs_cross" => new Vector(-780.0f, -1309.0f, -160.0f),
            "ct_a_jungle_support" => new Vector(-980.0f, -1500.0f, -164.0f),
            "ct_a_palace_close_poke" => new Vector(-100.0f, -1980.0f, -168.0f),

            // Meio / Janela / Conector / Catwalk / Underpass
            "ct_mid_window_crouch" => new Vector(-1160.0f, -680.0f, -168.0f),
            "ct_mid_window_deep_awp" => new Vector(-1279.6f, -967.9f, -168.0f),
            "ct_mid_connector_headshot" => new Vector(-580.0f, -1180.0f, -168.0f),
            "ct_mid_short_catwalk" => new Vector(-1050.0f, 250.0f, -160.0f),
            "ct_mid_underpass_peek" => new Vector(-720.0f, -220.0f, -160.0f),

            // Bombsite B & Spawn CT
            "ct_b_van_peek" => new Vector(-2160.0f, 510.0f, -168.0f),
            "ct_b_market_window" => new Vector(-1860.0f, -180.0f, -168.0f),
            "ct_spawn_safe" => new Vector(-1299.0f, -1160.9f, -168.0f),

            // Staging TR (Rampa A, Palácio, Underpass)
            "tr_staging_a_ramp" => new Vector(520.0f, -1660.0f, -220.0f),
            "tr_staging_palace_room" => new Vector(496.0f, -2315.9f, -40.0f),
            "tr_staging_underpass_top" => new Vector(-840.0f, -640.0f, -240.0f),

            // Retake CT Bombsite A
            "ct_retake_a_connector" => new Vector(-620.0f, -1180.0f, -168.0f),
            "ct_retake_a_jungle" => new Vector(-1020.0f, -1320.0f, -160.0f),

            _ => new Vector(-1279.6f, -967.9f, -168.0f)
        };
    }

    public int EnqueueSpotTests(string profileArg, string spotIdArg, int attempts, string pluginDir, bool clearFile = false)
    {
        if (clearFile)
        {
            TryDeleteFile(_rawJsonlPathServer);
            TryDeleteFile(_rawJsonlPathRepo);
        }

        var versions = new List<int>();
        string pClean = profileArg.Trim().ToLowerInvariant();
        if (pClean == "all" || pClean == "both" || pClean == "ab")
        {
            versions.Add(1);
            versions.Add(2);
        }
        else if (pClean == "1" || pClean == "v1")
        {
            versions.Add(1);
        }
        else
        {
            versions.Add(2);
        }

        int enqueued = 0;
        foreach (int ver in versions)
        {
            string profilePath = ResolveProfilePath(ver, pluginDir);
            if (!File.Exists(profilePath))
            {
                Server.PrintToConsole($"[SpotTest] ERRO: Arquivo de perfil V{ver} nao encontrado em {profilePath}");
                continue;
            }

            string sha256 = ComputeFileSha256(profilePath);
            string json = File.ReadAllText(profilePath, Encoding.UTF8);
            var profile = JsonSerializer.Deserialize<MapProfile>(json);
            if (profile == null || profile.Spots.Count == 0) continue;

            var spotDict = profile.Spots.ToDictionary(s => s.Id, s => s, StringComparer.OrdinalIgnoreCase);

            IEnumerable<string> targetIds = spotIdArg.Equals("all", StringComparison.OrdinalIgnoreCase)
                ? AlteredSpotIds20
                : new[] { spotIdArg };

            foreach (string sid in targetIds)
            {
                if (!spotDict.TryGetValue(sid, out var spot))
                {
                    Server.PrintToConsole($"[SpotTest] AVISO: Spot '{sid}' nao existe no perfil V{ver}.");
                    continue;
                }

                Vector startPos = GetCanonicalStartPositionForSpot(spot.Id);
                for (int att = 1; att <= Math.Max(1, attempts); att++)
                {
                    _jobQueue.Enqueue(new SpotTestJob
                    {
                        ProfileVersion = ver,
                        ProfilePath = profilePath,
                        ProfileSha256 = sha256,
                        TargetSpot = spot,
                        AttemptId = att,
                        StartPos = startPos
                    });
                    enqueued++;
                }
            }
        }

        if (enqueued > 0)
        {
            Server.ExecuteCommand("sv_cheats 1; mp_freezetime 0; mp_ignore_round_win_conditions 1; bot_stop 0; bot_dont_shoot 1; buddha 1; host_timescale 5;");
            Server.PrintToConsole($"[SpotTest] Enfileirados {enqueued} testes de spot (Fila total: {_jobQueue.Count}).");
        }

        return enqueued;
    }

    public void OnTick()
    {
        if (!IsActive) return;

        if (_currentJob == null)
        {
            StartNextJob();
            return;
        }

        var bot = Utilities.GetPlayerFromSlot(_testBotSlot);
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive || bot.PlayerPawn.Value?.AbsOrigin == null)
        {
            // Se o bot morreu ou ficou inválido, tenta re-alocar ou abortar tentativa
            StartNextJob();
            return;
        }

        var pawn = bot.PlayerPawn.Value;
        var pos = pawn.AbsOrigin!;
        var vel = pawn.AbsVelocity;

        if (_settleTicksRemaining > 0)
        {
            _settleTicksRemaining--;
            pawn.Teleport(_currentJob.StartPos, new QAngle(0, _currentJob.TargetSpot.Yaw, 0), new Vector(0, 0, 0));
            if (_settleTicksRemaining == 0)
            {
                BeginActiveAttempt(bot, pos);
            }
            return;
        }

        int currentTick = Server.TickCount;
        float currentTime = Server.CurrentTime;
        float elapsedMs = Math.Max(0f, (currentTime - _startTime) * 1000.0f);

        float dx = pos.X - _currentJob.TargetSpot.X;
        float dy = pos.Y - _currentJob.TargetSpot.Y;
        float dz = pos.Z - _currentJob.TargetSpot.Z;
        float dist2D = MathF.Sqrt(dx * dx + dy * dy);
        float dist3D = MathF.Sqrt(dx * dx + dy * dy + dz * dz);

        // No modo !spottest isolado, além do GoalPosition do NavMesh, guiamos a locomoção física no plano XY
        // em direção ao TargetSpot quando o bot se desvia ou quando o AI nativo tenta vagar para outro setor:
        if (dist2D > 68.0f)
        {
            float dirX = (_currentJob.TargetSpot.X - pos.X) / MathF.Max(1.0f, dist2D);
            float dirY = (_currentJob.TargetSpot.Y - pos.Y) / MathF.Max(1.0f, dist2D);

            // Se passou por uma janela de bloqueio (disp2D < 12u), aplica desvio lateral determinístico (unstuck strafe)
            if (_appliedNoProgressCount > 0 && (currentTick / 16) % 2 == 1)
            {
                float perpSign = (_appliedNoProgressCount % 2 == 1) ? 1.0f : -1.0f;
                float origDirX = dirX;
                float origDirY = dirY;
                dirX = (origDirX * 0.55f) - (origDirY * perpSign * 0.83f);
                dirY = (origDirY * 0.55f) + (origDirX * perpSign * 0.83f);
            }

            float desiredYaw = MathF.Atan2(dirY, dirX) * (180.0f / MathF.PI);

            // Alinha o pawn na direção do objetivo e aplica impulso cinemático horizontal controlado (225 u/s)
            // para evitar que o AI nativo da Valve inverta a direção de caminhada durante o teste A/B isolado:
            float curVz = vel?.Z ?? 0f;
            if ((dz < -24.0f && dist2D < 260.0f && (currentTick % 32 == 0)) || (_lowSpeedConsecutiveTicks == 12))
            {
                curVz = 260.0f;
            }
            pawn.Teleport(null, new QAngle(0, desiredYaw, 0), new Vector(dirX * 225.0f, dirY * 225.0f, curVz));

            float fMove = 240.0f;
            float sMove = 0.0f;
            ulong btns = BotLocomotionDriver.IN_FORWARD;
            if ((dz < -24.0f && dist2D < 260.0f && (currentTick % 32 == 0)) || (_lowSpeedConsecutiveTicks == 12))
            {
                btns |= BotLocomotionDriver.IN_JUMP;
            }

            _locomotionDriver.Arbitrator.PublishIntent(new MovementIntent
            {
                BotSlot = _testBotSlot,
                BotName = bot.PlayerName,
                GameTick = currentTick,
                CurrentTime = currentTime,
                Source = MovementIntentSource.BombObjective,
                Kind = MovementCommandKind.UsercmdVector,
                Reason = $"SpotTest_DirectNav({_currentJob.TargetSpot.Id})",
                ExpiresAtTime = currentTime + 0.08f,
                UseUsercmdVelocity = true,
                ForwardMove = fMove,
                SideMove = sMove,
                Buttons = btns,
                ButtonsDurationMs = 80,
                GoalX = _currentJob.TargetSpot.X,
                GoalY = _currentJob.TargetSpot.Y,
                GoalZ = _currentJob.TargetSpot.Z,
                Hurry = true,
                IsStopping = false,
                LookX = _currentJob.TargetSpot.X,
                LookY = _currentJob.TargetSpot.Y,
                LookZ = _currentJob.TargetSpot.Z + 64.0f,
                LookDuration = 0.25f
            });
        }

        var navState = _locomotionDriver.GetNavState(_testBotSlot);
        if (navState != null)
        {
            if (navState.LastRepathTime > _lastKnownRepathTime + 0.01f)
            {
                _lastKnownRepathTime = navState.LastRepathTime;
                _repathCount++;
                EmitEvent("SPOT_TEST_REPATH", currentTick, elapsedMs, dist3D, pos, "IN_PROGRESS");
            }

            if (navState.StuckCount > _lastKnownStuckCount)
            {
                _lastKnownStuckCount = navState.StuckCount;
                _recoveryCount++;
                EmitEvent("SPOT_TEST_RECOVERY", currentTick, elapsedMs, dist3D, pos, "IN_PROGRESS");
            }
        }

        // Monitoramento físico de GeometryBlock e AppliedNoProgress (após 400ms iniciais de aceleração)
        if (elapsedMs > 400.0f && dist2D > 68.0f)
        {
            float vx = vel?.X ?? 0f;
            float vy = vel?.Y ?? 0f;
            float speed2D = MathF.Sqrt(vx * vx + vy * vy);
            if (speed2D < 18.0f)
            {
                _lowSpeedConsecutiveTicks++;
                if (_lowSpeedConsecutiveTicks == 16) // ~250ms bloqueado
                {
                    _geometryBlockCount++;
                }
            }
            else
            {
                _lowSpeedConsecutiveTicks = 0;
            }

            _windowTicks++;
            if (_windowTicks >= 32) // Janela de 500ms
            {
                float disp2D = MathF.Sqrt(MathF.Pow(pos.X - _windowStartPos.X, 2) + MathF.Pow(pos.Y - _windowStartPos.Y, 2));
                if (disp2D < 12.0f)
                {
                    _appliedNoProgressCount++;
                    _repathCount++;
                    EmitEvent("SPOT_TEST_REPATH", currentTick, elapsedMs, dist3D, pos, "IN_PROGRESS");

                    if (_appliedNoProgressCount >= 2)
                    {
                        _recoveryCount++;
                        EmitEvent("SPOT_TEST_RECOVERY", currentTick, elapsedMs, dist3D, pos, "IN_PROGRESS");
                    }

                    // Re-emite intenção de navegação para forçar repath no NavMesh
                    _locomotionDriver.NavigateToSpot(bot, _currentJob.TargetSpot, hurry: true, stanceOverride: EngagementStance.PASSIVE_HOLD, priority: BotOrderPriority.Absolute_PlantOrDefuse);
                }
                _windowStartPos = new Vector(pos.X, pos.Y, pos.Z);
                _windowTicks = 0;
            }
        }

        // Verifica chegada ao spot (critério espacial 2D + cota vertical Z)
        bool reached = dist2D <= 68.0f && MathF.Abs(dz) <= 58.0f;
        if (reached)
        {
            EmitEvent("SPOT_TEST_REACHED", currentTick, elapsedMs, dist3D, pos, "REACHED");
            EmitEvent("SPOT_TEST_COMPLETED", currentTick, elapsedMs, dist3D, pos, "REACHED");
            _currentJob = null;
            return;
        }

        // Verifica timeout
        if (elapsedMs >= TimeoutSeconds * 1000.0f)
        {
            EmitEvent("SPOT_TEST_TIMEOUT", currentTick, elapsedMs, dist3D, pos, "TIMEOUT");
            EmitEvent("SPOT_TEST_COMPLETED", currentTick, elapsedMs, dist3D, pos, "TIMEOUT");
            _currentJob = null;
            return;
        }
    }

    private void StartNextJob()
    {
        if (_jobQueue.Count == 0)
        {
            _currentJob = null;
            Server.ExecuteCommand("host_timescale 1;");
            Server.PrintToConsole("[SpotTest] =====================================================");
            Server.PrintToConsole("[SpotTest] BATERIA DE TESTES A/B CONCLUIDA COM SUCESSO!");
            Server.PrintToConsole($"[SpotTest] Arquivo bruto: {_rawJsonlPathRepo}");
            Server.PrintToConsole("[SpotTest] =====================================================");
            WriteCompletionFlag();
            return;
        }

        _currentJob = _jobQueue.Dequeue();
        bool wantCt = !_currentJob.TargetSpot.Side.Equals("TR", StringComparison.OrdinalIgnoreCase);

        var allBots = Utilities.GetPlayers()
            .Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive && p.PlayerPawn.Value?.AbsOrigin != null)
            .OrderBy(p => p.Slot)
            .ToList();

        var ctCandidate = allBots.FirstOrDefault(p => (CsTeam)p.TeamNum == CsTeam.CounterTerrorist) ?? allBots.FirstOrDefault();
        var trCandidate = allBots.FirstOrDefault(p => (CsTeam)p.TeamNum == CsTeam.Terrorist) ?? allBots.FirstOrDefault();
        var candidate = wantCt ? ctCandidate : trCandidate;
        if (candidate == null)
        {
            Server.ExecuteCommand("bot_quota 10; mp_warmup_end; mp_restartgame 1;");
            return;
        }

        _testBotSlot = candidate.Slot;

        // Isola todos os outros bots longe da área de teste para garantir "sem inimigos" e zero colisão
        int idx = 0;
        foreach (var other in allBots)
        {
            if (other.Slot == _testBotSlot) continue;
            _locomotionDriver.ClearNavigation(other.Slot);
            bool otherIsCt = (CsTeam)other.TeamNum == CsTeam.CounterTerrorist;
            float holdX = otherIsCt ? (-2100.0f - (idx * 55.0f)) : (1300.0f - (idx * 55.0f));
            float holdY = otherIsCt ? -750.0f : 350.0f;
            float holdZ = -160.0f;
            other.PlayerPawn.Value?.Teleport(new Vector(holdX, holdY, holdZ), new QAngle(0, 0, 0), new Vector(0, 0, 0));
            idx++;
        }

        _locomotionDriver.ClearNavigation(_testBotSlot);
        candidate.ExecuteClientCommand("slot2");
        candidate.PlayerPawn.Value?.Teleport(_currentJob.StartPos, new QAngle(0, _currentJob.TargetSpot.Yaw, 0), new Vector(0, 0, 0));
        _settleTicksRemaining = 6;
    }

    private void BeginActiveAttempt(CCSPlayerController bot, Vector actualStartPos)
    {
        if (_currentJob == null) return;

        _startTick = Server.TickCount;
        _startTime = Server.CurrentTime;
        _repathCount = 0;
        _recoveryCount = 0;
        _geometryBlockCount = 0;
        _appliedNoProgressCount = 0;
        _lowSpeedConsecutiveTicks = 0;
        _windowStartPos = new Vector(actualStartPos.X, actualStartPos.Y, actualStartPos.Z);
        _windowTicks = 0;

        float dx = actualStartPos.X - _currentJob.TargetSpot.X;
        float dy = actualStartPos.Y - _currentJob.TargetSpot.Y;
        float dz = actualStartPos.Z - _currentJob.TargetSpot.Z;
        float dist3D = MathF.Sqrt(dx * dx + dy * dy + dz * dz);

        _locomotionDriver.NavigateToSpot(
            bot,
            _currentJob.TargetSpot,
            hurry: true,
            stanceOverride: EngagementStance.PASSIVE_HOLD,
            priority: BotOrderPriority.Absolute_PlantOrDefuse);

        var navState = _locomotionDriver.GetNavState(_testBotSlot);
        _lastKnownRepathTime = navState?.LastRepathTime ?? _startTime;
        _lastKnownStuckCount = navState?.StuckCount ?? 0;

        EmitEvent("SPOT_TEST_STARTED", _startTick, 0f, dist3D, actualStartPos, "STARTED");
    }

    private void EmitEvent(string eventType, int currentTick, float elapsedMs, float distRemaining, Vector currentPos, string result)
    {
        if (_currentJob == null) return;

        var record = new SpotTestEventRecord
        {
            EventType = eventType,
            TimestampUtc = DateTime.UtcNow.ToString("O"),
            ProfileVersion = _currentJob.ProfileVersion,
            SpotId = _currentJob.TargetSpot.Id,
            AttemptId = _currentJob.AttemptId,
            BotSlot = _testBotSlot,
            StartPosition = new[]
            {
                MathF.Round(_currentJob.StartPos.X, 1),
                MathF.Round(_currentJob.StartPos.Y, 1),
                MathF.Round(_currentJob.StartPos.Z, 1)
            },
            TargetPosition = new[]
            {
                MathF.Round(_currentJob.TargetSpot.X, 1),
                MathF.Round(_currentJob.TargetSpot.Y, 1),
                MathF.Round(_currentJob.TargetSpot.Z, 1)
            },
            StartTick = _startTick,
            EndTick = currentTick,
            ElapsedMs = MathF.Round(elapsedMs, 1),
            DistanceRemaining = MathF.Round(distRemaining, 1),
            RepathCount = _repathCount,
            RecoveryCount = _recoveryCount,
            GeometryBlockCount = _geometryBlockCount,
            AppliedNoProgressCount = _appliedNoProgressCount,
            FinalPosition = new[]
            {
                MathF.Round(currentPos.X, 1),
                MathF.Round(currentPos.Y, 1),
                MathF.Round(currentPos.Z, 1)
            },
            Result = result,
            DllSha256 = _dllSha256,
            ProfileSha256 = _currentJob.ProfileSha256
        };

        string jsonLine = JsonSerializer.Serialize(record);
        AppendLineSafe(_rawJsonlPathServer, jsonLine);
        AppendLineSafe(_rawJsonlPathRepo, jsonLine);

        if (eventType == "SPOT_TEST_COMPLETED" || eventType == "SPOT_TEST_STARTED")
        {
            Server.PrintToConsole($"[SpotTest] {eventType} | V{record.ProfileVersion} | {record.SpotId} #{record.AttemptId} | slot={record.BotSlot} | elapsed={record.ElapsedMs:F0}ms | distRem={record.DistanceRemaining:F1}u | repath={record.RepathCount} | rec={record.RecoveryCount} | block={record.GeometryBlockCount} | res={record.Result}");
        }
    }

    private static string ResolveProfilePath(int version, string pluginDir)
    {
        if (version == 1)
        {
            string[] candidatesV1 = new[]
            {
                Path.Combine(pluginDir, "MapProfiles", "backups", "de_mirage.v1_backup.json"),
                @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\src\CsBotManager\MapProfiles\backups\de_mirage.v1_backup.json",
                @"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\MapProfiles\backups\de_mirage.v1_backup.json"
            };
            foreach (var c in candidatesV1)
            {
                if (File.Exists(c)) return c;
            }
        }

        string[] candidatesV2 = new[]
        {
            Path.Combine(pluginDir, "MapProfiles", "de_mirage.json"),
            @"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\src\CsBotManager\MapProfiles\de_mirage.json",
            @"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\MapProfiles\de_mirage.json"
        };
        foreach (var c in candidatesV2)
        {
            if (File.Exists(c)) return c;
        }

        return Path.Combine(pluginDir, "MapProfiles", "de_mirage.json");
    }

    private static string ComputeFileSha256(string filePath)
    {
        try
        {
            if (!File.Exists(filePath)) return string.Empty;
            using var sha = SHA256.Create();
            using var stream = File.OpenRead(filePath);
            byte[] hash = sha.ComputeHash(stream);
            return Convert.ToHexString(hash).ToLowerInvariant();
        }
        catch
        {
            return string.Empty;
        }
    }

    private static readonly UTF8Encoding Utf8NoBom = new(encoderShouldEmitUTF8Identifier: false);

    private static void AppendLineSafe(string path, string line)
    {
        try
        {
            string? dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }
            File.AppendAllText(path, line + Environment.NewLine, Utf8NoBom);
        }
        catch { }
    }

    private static void TryDeleteFile(string path)
    {
        try
        {
            if (File.Exists(path)) File.Delete(path);
        }
        catch { }
    }

    private static void WriteCompletionFlag()
    {
        try
        {
            File.WriteAllText(@"H:\CS2_AI_Server\debug_logs\spottest_completed.flag", DateTime.UtcNow.ToString("O"));
        }
        catch { }
    }
}
