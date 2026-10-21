using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.InteropServices;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using BotControllerApi;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;

namespace CsBotManager;

public enum MicroSpeedTier
{
    Run = 0,        // 250 u/s (Velocidade máxima padrão)
    WalkShift = 1,  // 130 u/s (+speed / Shift silencioso)
    Crouch = 2      // 85 u/s  (+duck / Agachado)
}

public enum AdrenalineTriggerType
{
    None_SafeTransitGps = 0, // Fora de perigo: GPS (NavMesh) conduz 100% da viagem longa (evita Covariate Shift)
    Vision_Spotted = 1,      // Gatilho 1: Visão legítima (SpottedByMask / IsEnemyVisible)
    Audio_HeardCue = 2,      // Gatilho 2: Pista sonora legítima (~1000u passos / tiros recentes no setor)
    Hotzone_PreMapped = 3    // Gatilho 3: Zona de Perigo / Staging Area pré-mapeada ("fatiando a torta")
}

/// <summary>
/// Representa 1 passo discreto dentro do espaço de 97 ações do MLMove (David Durst, Stanford):
/// - ActionId 0: Stand Still (Parado)
/// - ActionId 1..96: 16 direções angulares (22.5° cada) x 3 velocidades (Run, Walk, Crouch) x 2 estados de pulo (Ground, Jump)
/// </summary>
public struct MicroMoveStep
{
    public int ActionId { get; set; }
    public int DirectionIndex { get; set; } // -1 para StandStill, 0..15 para 0°..337.5°
    public MicroSpeedTier SpeedTier { get; set; }
    public bool IsJump { get; set; }
    public float WorldDirX { get; set; }
    public float WorldDirY { get; set; }
    public float SpeedScale { get; set; }
    public ulong Buttons { get; set; }
    public float DurationMs { get; set; }

    public static MicroMoveStep StandStill(float durationMs = 125f) => new()
    {
        ActionId = 0,
        DirectionIndex = -1,
        SpeedTier = MicroSpeedTier.Run,
        IsJump = false,
        WorldDirX = 0f,
        WorldDirY = 0f,
        SpeedScale = 0f,
        Buttons = 0UL,
        DurationMs = durationMs
    };

    public static int EncodeAction(int dirIndex, MicroSpeedTier speedTier, bool isJump)
    {
        if (dirIndex < 0) return 0;
        int clampedDir = ((dirIndex % 16) + 16) % 16;
        int speedIdx = Math.Clamp((int)speedTier, 0, 2);
        int jumpIdx = isJump ? 1 : 0;
        return 1 + (jumpIdx * 48) + (speedIdx * 16) + clampedDir;
    }

    public static int QuantizeAngleToDirectionIndex(float angleRad)
    {
        float deg = angleRad * (180.0f / MathF.PI);
        if (deg < 0f) deg += 360.0f;
        int idx = (int)MathF.Round(deg / 22.5f) % 16;
        return idx;
    }

    public static MicroMoveStep FromActionId(int actionId, float durationMs = 125f)
    {
        if (actionId <= 0 || actionId > 96)
        {
            return StandStill(durationMs);
        }

        int zeroBased = actionId - 1;
        int jumpIdx = zeroBased / 48;
        int rem = zeroBased % 48;
        int speedIdx = rem / 16;
        int dirIdx = rem % 16;

        bool isJump = jumpIdx == 1;
        var speedTier = (MicroSpeedTier)speedIdx;
        float angleRad = dirIdx * (22.5f * MathF.PI / 180.0f);

        float speedScale = speedTier switch
        {
            MicroSpeedTier.Run => 250.0f,
            MicroSpeedTier.WalkShift => 130.0f,
            MicroSpeedTier.Crouch => 85.0f,
            _ => 250.0f
        };

        ulong buttons = 0UL;
        if (speedTier == MicroSpeedTier.WalkShift) buttons |= BotLocomotionDriver.IN_SPEED;
        if (speedTier == MicroSpeedTier.Crouch) buttons |= BotLocomotionDriver.IN_DUCK;
        if (isJump) buttons |= BotLocomotionDriver.IN_JUMP;

        return new MicroMoveStep
        {
            ActionId = actionId,
            DirectionIndex = dirIdx,
            SpeedTier = speedTier,
            IsJump = isJump,
            WorldDirX = MathF.Cos(angleRad),
            WorldDirY = MathF.Sin(angleRad),
            SpeedScale = speedScale,
            Buttons = buttons,
            DurationMs = durationMs
        };
    }

    /// <summary>
    /// Converte o vetor de direção global (WorldDirX, WorldDirY) para comandos relativos ao EyeAngles.Y (Yaw) do bot
    /// para injeção direta no UserCmd (forwardmove, sidemove).
    /// </summary>
    public readonly (float ForwardMove, float SideMove) ToBotRelativeMoves(float botYawDegrees)
    {
        if (ActionId == 0 || SpeedScale <= 0.01f)
        {
            return (0f, 0f);
        }

        float yawRad = botYawDegrees * (MathF.PI / 180.0f);
        float forwardX = MathF.Cos(yawRad);
        float forwardY = MathF.Sin(yawRad);

        // Na Source 2, o eixo Direito (Right / +SideMove) está a -90 graus do Forward no plano XY
        float rightX = MathF.Sin(yawRad);
        float rightY = -MathF.Cos(yawRad);

        float forwardMove = (WorldDirX * forwardX + WorldDirY * forwardY) * SpeedScale;
        float sideMove = (WorldDirX * rightX + WorldDirY * rightY) * SpeedScale;

        return (forwardMove, sideMove);
    }
}

/// <summary>
/// Buffer de Inércia Multi-Horizonte (t=0ms, t=+125ms, t=+250ms) por bot.
/// Evita o tremor (jitter) de decisões isoladas a cada tick.
/// </summary>
public class MicroMoveTrajectory
{
    public int Slot { get; set; }
    public MicroMoveStep Step0_Now { get; set; } = MicroMoveStep.StandStill(100f);
    public MicroMoveStep Step1_125ms { get; set; } = MicroMoveStep.StandStill(125f);
    public MicroMoveStep Step2_250ms { get; set; } = MicroMoveStep.StandStill(125f);
    public float GeneratedAtTime { get; set; }
    public bool IsOverrideActive { get; set; }
    public string ActiveBehaviorTag { get; set; } = "None";
    public AdrenalineTriggerType LastTrigger { get; set; } = AdrenalineTriggerType.None_SafeTransitGps;
    public float OverrideExpiresAt { get; set; }

    public MicroMoveStep GetStepForElapsed(float currentTime)
    {
        float elapsedMs = (currentTime - GeneratedAtTime) * 1000.0f;
        if (elapsedMs < Step0_Now.DurationMs)
        {
            return Step0_Now;
        }
        if (elapsedMs < Step0_Now.DurationMs + Step1_125ms.DurationMs)
        {
            return Step1_125ms;
        }
        return Step2_250ms;
    }
}

/// <summary>
/// Interface padronizada de predição multi-agente para o motor de 16Hz (execução 100% em CPU / L3 Cache).
/// Permite alternar sem atrito entre o Modelo Neural .ONNX (Camadas 2/3) e o Motor de Campos Potenciais (Camada 1).
/// </summary>
public interface IMicroMovePredictor
{
    string BackendName { get; }
    bool IsNeuralModelLoaded { get; }
    bool TryLoadMapModel(string mapName, string modelsDir);
    void PredictBatch16Hz(
        float[,] ctFogTensor,
        float[,] trFogTensor,
        List<CCSPlayerController> orderedPlayers,
        ConcurrentDictionary<int, MicroMoveTrajectory> trajectories,
        float currentTime);
}

/// <summary>
/// Fase 6A (Camada 1 da Arquitetura MLMove):
/// Motor de Micro-Movimento Coordenado a 16Hz (a cada 4 ticks / 62.5ms) em CPU (Cache L3) com:
/// - Anti-Wallhack Fog-of-War Tensor Masking ([0,0,0] para inimigos não percebidos legitimamente)
/// - 3 Gatilhos de Percepção Legítima (Visão SpottedByMask, Áudio ~1000u, Hotzones pré-mapeadas)
/// - Amostragem Estocástica Softmax ("Dado Viciado") sobre 97 ações em 3 horizontes (0ms, 125ms, 250ms)
/// - Wall-Hugging, Trade Spacing (N x N) e Counter-Strafe (Velocity Zeroing).
/// </summary>
public class MicroMoveEngine : IMicroMovePredictor
{
    public const int MaxPlayers = 10;
    public const int FeatureDim = 18;
    public const int HorizonsCount = 3;
    public const int ActionSpaceSize = 97;
    public const string OnnxInputName = "input_state";
    public const string OnnxOutputName = "output_logits";
    public const string DefaultModelsDir = @"H:\CS2_AI_Server\models";

    private readonly MapProfileManager _mapProfileManager;
    private readonly RoleManager _roleManager;
    private readonly Random _random = new();
    private readonly object _onnxLock = new();

    public MatchTelemetryLogger? TelemetryLogger { get; set; }
    public TacticalCalloutSystem? CalloutSystem { get; set; }

    private readonly ConcurrentDictionary<int, MicroMoveTrajectory> _trajectories = new();

    // Tensores separados com "Venda nos Olhos" (Fog of War) para CT e TR: inimigos não vistos/ouvidos recebem [0,0,0]
    private readonly float[,] _ctFogInputTensor = new float[MaxPlayers, FeatureDim];
    private readonly float[,] _trFogInputTensor = new float[MaxPlayers, FeatureDim];

    // Buffers pré-alocados para inferência ONNX em lote [2, 10, 18] -> [2, 10, 3, 97] (zero GC no loop de 16Hz)
    private readonly float[] _onnxBatchInputBuffer = new float[2 * MaxPlayers * FeatureDim];
    private readonly float[,,,] _onnxBatchOutputLogits = new float[2, MaxPlayers, HorizonsCount, ActionSpaceSize];
    private InferenceSession? _onnxSession;
    private static bool _nativeOnnxLoaded;

    // Rastreamento temporal para Counter-Strafe, Trade Swing (0.6s delay) e Cooldowns de Telemetria
    private readonly Dictionary<int, float> _counterStrafeCooldownUntil = new();
    private readonly Dictionary<int, float> _entryContactStartTime = new();
    private readonly Dictionary<int, float> _lastDebugLogTime = new();
    private readonly ConcurrentDictionary<int, long> _activeMicroMoveCmdIds = new();

    private int _tickCounter = 0;
    private long _pendingModelReloadAtMs = 0;
    private string _loadedMapName = string.Empty;
    private string _loadedOnnxPath = string.Empty;
    private bool _isNeuralModelLoaded = false;
    private FileSystemWatcher? _onnxWatcher;

    public float LastInferenceLatencyMs { get; private set; }
    public long TotalOnnxInferences { get; private set; }

    public string BackendName => _isNeuralModelLoaded
        ? $"[Modo ONNX Ativo] ONNX-CPU-L3 ({Path.GetFileName(_loadedOnnxPath)} | {LastInferenceLatencyMs:F2}ms)"
        : "PotentialFields-16Hz-CPU (FogOfWar + 3Triggers + Softmax97)";

    public bool IsNeuralModelLoaded => _isNeuralModelLoaded;

    public MicroMoveEngine(MapProfileManager mapProfileManager, RoleManager roleManager)
    {
        _mapProfileManager = mapProfileManager;
        _roleManager = roleManager;
        EnsureModelsDirectory();
    }

    private static void EnsureNativeOnnxRuntimeLoaded()
    {
        if (_nativeOnnxLoaded) return;
        try
        {
            string? asmDir = Path.GetDirectoryName(typeof(MicroMoveEngine).Assembly.Location);
            if (!string.IsNullOrEmpty(asmDir))
            {
                string candidate1 = Path.Combine(asmDir, "onnxruntime.dll");
                string candidate2 = Path.Combine(asmDir, "runtimes", "win-x64", "native", "onnxruntime.dll");
                if (File.Exists(candidate1) && NativeLibrary.TryLoad(candidate1, out _))
                {
                    _nativeOnnxLoaded = true;
                    return;
                }
                if (File.Exists(candidate2) && NativeLibrary.TryLoad(candidate2, out _))
                {
                    _nativeOnnxLoaded = true;
                    return;
                }
            }
        }
        catch { }
    }

    private void EnsureModelsDirectory()
    {
        try
        {
            if (!Directory.Exists(DefaultModelsDir))
            {
                Directory.CreateDirectory(DefaultModelsDir);
            }

            if (_onnxWatcher == null)
            {
                _onnxWatcher = new FileSystemWatcher(DefaultModelsDir, "mlmove_*.onnx")
                {
                    NotifyFilter = NotifyFilters.FileName | NotifyFilters.LastWrite | NotifyFilters.Size,
                    EnableRaisingEvents = true
                };
                _onnxWatcher.Created += (_, e) => OnModelFileDetected(e.FullPath);
                _onnxWatcher.Changed += (_, e) => OnModelFileDetected(e.FullPath);
            }
        }
        catch { }
    }

    private void OnModelFileDetected(string fullPath)
    {
        if (!string.IsNullOrEmpty(_loadedMapName) &&
            fullPath.Contains(_loadedMapName, StringComparison.OrdinalIgnoreCase))
        {
            // Agenda o hot-swap para a Game Thread (debounce de 1.2s após término da gravação do arquivo .onnx)
            Interlocked.Exchange(ref _pendingModelReloadAtMs, Environment.TickCount64 + 1200L);
        }
    }

    public void ResetRound(IBotControllerApi? api)
    {
        if (api != null)
        {
            foreach (var kvp in _activeMicroMoveCmdIds)
            {
                if (kvp.Value != 0)
                {
                    try { api.CancelUsercmdMovement(kvp.Key, kvp.Value); } catch { }
                }
            }
        }

        _activeMicroMoveCmdIds.Clear();
        _trajectories.Clear();
        _counterStrafeCooldownUntil.Clear();
        _entryContactStartTime.Clear();
        _lastDebugLogTime.Clear();
        _tickCounter = 0;
    }

    public bool TryLoadMapModel(string? mapName, string modelsDir = DefaultModelsDir)
    {
        string cleanMap = string.IsNullOrWhiteSpace(mapName) ? "de_mirage" : mapName.ToLowerInvariant().Trim();
        _loadedMapName = cleanMap;

        try
        {
            if (!Directory.Exists(modelsDir))
            {
                Directory.CreateDirectory(modelsDir);
            }

            string candidatePath = Path.Combine(modelsDir, $"mlmove_{cleanMap}.onnx");
            if (File.Exists(candidatePath))
            {
                var info = new FileInfo(candidatePath);
                if (info.Length > 1024)
                {
                    EnsureNativeOnnxRuntimeLoaded();

                    byte[] modelBytes;
                    using (var fs = new FileStream(candidatePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                    {
                        modelBytes = new byte[fs.Length];
                        int offset = 0;
                        while (offset < modelBytes.Length)
                        {
                            int read = fs.Read(modelBytes, offset, modelBytes.Length - offset);
                            if (read <= 0) break;
                            offset += read;
                        }
                    }

                    var sessionOptions = new SessionOptions
                    {
                        IntraOpNumThreads = 4,
                        InterOpNumThreads = 1,
                        ExecutionMode = ExecutionMode.ORT_SEQUENTIAL,
                        GraphOptimizationLevel = GraphOptimizationLevel.ORT_ENABLE_ALL
                    };

                    var newSession = new InferenceSession(modelBytes, sessionOptions);

                    lock (_onnxLock)
                    {
                        var oldSession = _onnxSession;
                        _onnxSession = newSession;
                        oldSession?.Dispose();
                        _loadedOnnxPath = candidatePath;
                        _isNeuralModelLoaded = true;
                    }

                    // Warmup pass imediato no Cache L3 da CPU para zerar jitter no primeiro tick de combate
                    RunOnnxBatchInference(_ctFogInputTensor, _trFogInputTensor);

                    Server.PrintToConsole($"[MicroMoveEngine] [Modo ONNX Ativo] Modelo ONNX (CPU L3 Cache) carregado para {cleanMap}: {candidatePath} ({info.Length / 1024} KB | Warmup: {LastInferenceLatencyMs:F2}ms).");
                    TelemetryLogger?.LogEvent("MLMOVE-ONNX", $"**[Modo ONNX Ativo]** Modelo neural `{Path.GetFileName(candidatePath)}` ({info.Length / 1024} KB) carregado em CPU para `{cleanMap}` (Latência 16Hz: `{LastInferenceLatencyMs:F2}ms`).");
                    return true;
                }
            }
        }
        catch (Exception ex)
        {
            Server.PrintToConsole($"[MicroMoveEngine] Aviso ao carregar modelo ONNX: {ex.Message}");
        }

        _isNeuralModelLoaded = false;
        _loadedOnnxPath = string.Empty;
        return false;
    }

    /// <summary>
    /// Executa a inferência em lote [2, 10, 18] (Batch 0 = Perspectiva CT com Fog-of-War, Batch 1 = Perspectiva TR com Fog-of-War)
    /// diretamente no Cache L3 da CPU via Microsoft.ML.OnnxRuntime, preenchendo _onnxBatchOutputLogits [2, 10, 3, 97].
    /// </summary>
    public bool RunOnnxBatchInference(float[,] ctFogTensor, float[,] trFogTensor)
    {
        if (!_isNeuralModelLoaded || _onnxSession == null) return false;

        lock (_onnxLock)
        {
            if (_onnxSession == null) return false;

            try
            {
                long t0 = Stopwatch.GetTimestamp();

                int idx = 0;
                for (int p = 0; p < MaxPlayers; p++)
                {
                    for (int f = 0; f < FeatureDim; f++)
                    {
                        _onnxBatchInputBuffer[idx++] = ctFogTensor[p, f];
                    }
                }
                for (int p = 0; p < MaxPlayers; p++)
                {
                    for (int f = 0; f < FeatureDim; f++)
                    {
                        _onnxBatchInputBuffer[idx++] = trFogTensor[p, f];
                    }
                }

                var inputTensor = new DenseTensor<float>(_onnxBatchInputBuffer, new[] { 2, MaxPlayers, FeatureDim });
                var inputs = new List<NamedOnnxValue>(1)
                {
                    NamedOnnxValue.CreateFromTensor(OnnxInputName, inputTensor)
                };

                using var results = _onnxSession.Run(inputs);
                var firstOutput = results.FirstOrDefault()?.AsTensor<float>();
                if (firstOutput == null) return false;

                if (firstOutput is DenseTensor<float> denseOut)
                {
                    ReadOnlySpan<float> outSpan = denseOut.Buffer.Span;
                    int outIdx = 0;
                    for (int b = 0; b < 2; b++)
                    {
                        for (int p = 0; p < MaxPlayers; p++)
                        {
                            for (int h = 0; h < HorizonsCount; h++)
                            {
                                for (int a = 0; a < ActionSpaceSize; a++)
                                {
                                    _onnxBatchOutputLogits[b, p, h, a] = outSpan[outIdx++];
                                }
                            }
                        }
                    }
                }
                else
                {
                    for (int b = 0; b < 2; b++)
                    {
                        for (int p = 0; p < MaxPlayers; p++)
                        {
                            for (int h = 0; h < HorizonsCount; h++)
                            {
                                for (int a = 0; a < ActionSpaceSize; a++)
                                {
                                    _onnxBatchOutputLogits[b, p, h, a] = firstOutput[b, p, h, a];
                                }
                            }
                        }
                    }
                }

                long t1 = Stopwatch.GetTimestamp();
                // Latência por lote de 10 jogadores (média das 2 perspectivas CT e TR processadas juntas)
                LastInferenceLatencyMs = (float)((t1 - t0) * 500.0 / Stopwatch.Frequency);
                TotalOnnxInferences++;
                return true;
            }
            catch (Exception ex)
            {
                Server.PrintToConsole($"[MicroMoveEngine] Erro na inferência ONNX: {ex.Message}");
                return false;
            }
        }
    }

    public MicroMoveTrajectory? GetTrajectory(int slot)
    {
        return _trajectories.TryGetValue(slot, out var traj) ? traj : null;
    }

    /// <summary>
    /// Amostrador Estocástico ("Dado Viciado" com Temperatura Softmax) sobre o espaço de 97 ações.
    /// Evita comportamento robótico previsível: se a distribuição indicar [70% Recuar, 25% Jiggle, 5% Avançar],
    /// sorteia proporcionalmente às probabilidades.
    /// </summary>
    public int SampleActionFromLogits(ReadOnlySpan<float> logits, float temperature = 0.85f)
    {
        int len = Math.Min(logits.Length, ActionSpaceSize);
        if (len == 0) return 0;

        float temp = Math.Max(0.05f, temperature);
        float maxLogit = float.MinValue;
        for (int i = 0; i < len; i++)
        {
            if (logits[i] > maxLogit) maxLogit = logits[i];
        }

        Span<float> probs = stackalloc float[ActionSpaceSize];
        float sum = 0f;
        for (int i = 0; i < len; i++)
        {
            float p = MathF.Exp((logits[i] - maxLogit) / temp);
            probs[i] = p;
            sum += p;
        }

        if (sum <= 1e-6f) return 0;

        float roll = (float)_random.NextDouble() * sum;
        float cumulative = 0f;
        for (int i = 0; i < len; i++)
        {
            cumulative += probs[i];
            if (roll <= cumulative)
            {
                return i;
            }
        }

        return len - 1;
    }

    /// <summary>
    /// Avalia os 3 Filtros de Percepção Legítima (Sem Wallhack por distância cega) para decidir se o
    /// Piloto de Fuga (MicroMoveEngine/ONNX) assume o teclado ou deixa o GPS (NavMesh) conduzir:
    /// 1) Gatilho de Visão (SpottedByMask / IsEnemyVisible)
    /// 2) Gatilho de Áudio (Passos ~1000u / Tiros / Dano recente no setor via TacticalCalloutSystem)
    /// 3) Gatilho de Hotzone (Chokepoint / Staging Area pré-mapeada onde pros abrem "fatiando a torta")
    /// </summary>
    public AdrenalineTriggerType EvaluateLegitimateAdrenalineTrigger(
        CCSPlayerController bot,
        List<CCSPlayerController> allPlayers)
    {
        var pawn = bot.PlayerPawn.Value;
        var csBot = pawn?.Bot;
        if (pawn?.AbsOrigin == null || csBot == null)
        {
            return AdrenalineTriggerType.None_SafeTransitGps;
        }

        // 1. Gatilho de Visão Direta (SpottedByMask / IsEnemyVisible)
        if (csBot.IsEnemyVisible)
        {
            return AdrenalineTriggerType.Vision_Spotted;
        }

        foreach (var other in allPlayers)
        {
            if (other == null || !other.IsValid || !other.PawnIsAlive || other.Team == bot.Team) continue;
            if (TacticalCalloutSystem.CanBotPerceiveEnemy(bot, other, CalloutSystem, _mapProfileManager))
            {
                return AdrenalineTriggerType.Vision_Spotted;
            }
        }

        // 2. Gatilho de Áudio Legítimo (Passos / Tiros ouvidos no setor ou aliado próximo <= 600u trocando tiro)
        float curX = pawn.AbsOrigin.X;
        float curY = pawn.AbsOrigin.Y;
        float curZ = pawn.AbsOrigin.Z;
        var currentCp = _mapProfileManager.FindChokepointAt(curX, curY, curZ);

        if (CalloutSystem != null && currentCp != null && CalloutSystem.HasRecentEnemyAudioInSector(currentCp.Name, 4.0f))
        {
            return AdrenalineTriggerType.Audio_HeardCue;
        }

        foreach (var ally in allPlayers)
        {
            if (ally == null || !ally.IsValid || !ally.PawnIsAlive || ally.Team != bot.Team || ally.Slot == bot.Slot) continue;
            bool allyInCombat = ally.PlayerPawn.Value?.Bot?.IsEnemyVisible ?? false;
            if (allyInCombat && ally.PlayerPawn.Value?.AbsOrigin != null)
            {
                float distToAlly = (ally.PlayerPawn.Value.AbsOrigin - pawn.AbsOrigin).Length();
                if (distToAlly <= 600.0f)
                {
                    return AdrenalineTriggerType.Audio_HeardCue;
                }
            }
        }

        // 3. Gatilho de "Zona de Perigo" (Hotzone pré-mapeada: boca da Caverna, Palácio, Janela, Conector, Tapete)
        if (currentCp != null)
        {
            return AdrenalineTriggerType.Hotzone_PreMapped;
        }

        return AdrenalineTriggerType.None_SafeTransitGps;
    }

    /// <summary>
    /// Chamado no OnTick principal (64Hz).
    /// A cada 4 ticks (16Hz = 62.5ms), reconstrói os tensores [10, 18] com Fog-of-War Anti-Wallhack
    /// e atualiza as trajetórias de todos os 10 bots em lote na CPU.
    /// </summary>
    public void UpdateTick(
        float currentTime,
        float roundTimeRemaining,
        bool isBombPlanted,
        ConcurrentDictionary<int, TrackedBotNavState> navStates,
        IBotControllerApi? botApi)
    {
        _tickCounter++;

        long reloadTargetMs = Interlocked.Read(ref _pendingModelReloadAtMs);
        if (reloadTargetMs > 0L && Environment.TickCount64 >= reloadTargetMs)
        {
            Interlocked.Exchange(ref _pendingModelReloadAtMs, 0L);
            TryLoadMapModel(_loadedMapName, DefaultModelsDir);
        }

        // Ciclo de 16 Hz (1x a cada 4 ticks do servidor 64-tick -> 62.5ms)
        if (_tickCounter % 4 == 0)
        {
            var allPlayers = Utilities.GetPlayers()
                .Where(p => p != null && p.IsValid && (p.Team == CsTeam.CounterTerrorist || p.Team == CsTeam.Terrorist))
                .OrderBy(p => p.Team)
                .ThenBy(p => p.Slot)
                .Take(MaxPlayers)
                .ToList();

            // Monta os tensores com "Venda nos Olhos" (Fog of War): inimigos ocultos viram [0,0,0]
            BuildFogOfWarInputTensorForTeam(_ctFogInputTensor, CsTeam.CounterTerrorist, allPlayers, roundTimeRemaining, isBombPlanted);
            BuildFogOfWarInputTensorForTeam(_trFogInputTensor, CsTeam.Terrorist, allPlayers, roundTimeRemaining, isBombPlanted);

            PredictBatch16Hz(_ctFogInputTensor, _trFogInputTensor, allPlayers, _trajectories, currentTime);
        }

        // Aplicação suave dos horizontes (Step0_Now, Step1_125ms, Step2_250ms) para bots com override micro ativo
        if (botApi == null) return;

        foreach (var kvp in _trajectories)
        {
            int slot = kvp.Key;
            var traj = kvp.Value;

            if (!traj.IsOverrideActive || currentTime > traj.OverrideExpiresAt)
            {
                if (_activeMicroMoveCmdIds.TryRemove(slot, out long oldCmdId) && oldCmdId != 0)
                {
                    try { botApi.CancelUsercmdMovement(slot, oldCmdId); } catch { }
                }
                traj.IsOverrideActive = false;
                continue;
            }

            var bot = Utilities.GetPlayerFromSlot(slot);
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive)
            {
                _activeMicroMoveCmdIds.TryRemove(slot, out _);
                continue;
            }

            // Salvaguarda: Nunca interrompe bot plantando ou defusando a C4
            var pawn = bot.PlayerPawn.Value;
            if (pawn == null || pawn.AbsOrigin == null) continue;
            bool isDefusing = false;
            try { isDefusing = pawn.IsDefusing; } catch { }
            if (isDefusing) continue;

            var activeStep = traj.GetStepForElapsed(currentTime);

            // Se a ação for StandStill (ex: metade final do Counter-Strafe para precisão de tiro)
            if (activeStep.ActionId == 0 || activeStep.SpeedScale <= 0.1f)
            {
                if (_activeMicroMoveCmdIds.TryRemove(slot, out long prevId) && prevId != 0)
                {
                    try { botApi.CancelUsercmdMovement(slot, prevId); } catch { }
                }

                if (pawn.Bot != null)
                {
                    pawn.Bot.IsStopping = true;
                    pawn.Bot.WaitTimer.Duration = 0.12f;
                    pawn.Bot.WaitTimer.Timestamp = currentTime + 0.12f;
                }
            }
            else
            {
                float botYaw = pawn.EyeAngles?.Y ?? 0.0f;
                var (forwardMove, sideMove) = activeStep.ToBotRelativeMoves(botYaw);

                if (_activeMicroMoveCmdIds.TryGetValue(slot, out long prevId) && prevId != 0)
                {
                    try { botApi.CancelUsercmdMovement(slot, prevId); } catch { }
                }

                try
                {
                    long newCmdId = botApi.StartUsercmdMovement(slot, forwardMove, sideMove);
                    _activeMicroMoveCmdIds[slot] = newCmdId;

                    if (activeStep.Buttons != 0UL)
                    {
                        botApi.InjectUsercmd(slot, activeStep.Buttons, (int)Math.Clamp(activeStep.DurationMs, 60f, 150f));
                    }
                }
                catch { }
            }
        }
    }

    /// <summary>
    /// Contrato oficial C# &lt;-&gt; Python (Etapa 1): Monta o tensor padronizado [10, 18] com Fog-of-War Anti-Wallhack.
    /// </summary>
    public void BuildStandardizedInputTensor(
        float[,] targetTensor,
        CsTeam observerTeam,
        List<CCSPlayerController> orderedPlayers,
        float roundTimeRemaining,
        bool isBombPlanted)
    {
        BuildFogOfWarInputTensorForTeam(targetTensor, observerTeam, orderedPlayers, roundTimeRemaining, isBombPlanted);
    }

    /// <summary>
    /// Monta o tensor de entrada padronizado [10, 18] com "Venda nos Olhos" (Anti-Wallhack / Fog of War):
    /// Se um jogador pertence ao time adversário e NENHUM bot vivo do observerTeam o viu (SpottedByMask/FOV)
    /// ou ouviu (Audio cue legítimo), suas coordenadas X,Y,Z, velocidade, mira e arma são ZERADAS ([0,0,0])!
    /// </summary>
    public void BuildFogOfWarInputTensorForTeam(
        float[,] targetTensor,
        CsTeam observerTeam,
        List<CCSPlayerController> orderedPlayers,
        float roundTimeRemaining,
        bool isBombPlanted)
    {
        Array.Clear(targetTensor, 0, targetTensor.Length);
        float normTime = Math.Clamp(roundTimeRemaining / 115.0f, 0f, 1f);
        float plantedFlag = isBombPlanted ? 1.0f : 0.0f;

        var aliveAllies = orderedPlayers
            .Where(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == observerTeam)
            .ToList();

        for (int i = 0; i < orderedPlayers.Count && i < MaxPlayers; i++)
        {
            var p = orderedPlayers[i];
            if (p == null || !p.IsValid) continue;

            var pawn = p.PlayerPawn.Value;
            bool isAlive = p.PawnIsAlive && pawn != null && pawn.AbsOrigin != null;
            bool isTeammate = p.Team == observerTeam;

            targetTensor[i, 13] = p.Team == CsTeam.Terrorist ? 1.0f : 0.0f;
            targetTensor[i, 14] = isAlive ? 1.0f : 0.0f;
            targetTensor[i, 16] = plantedFlag;
            targetTensor[i, 17] = normTime;

            if (!isAlive || pawn == null || pawn.AbsOrigin == null) continue;

            // Filtro Anti-Wallhack (Item 1): Se for inimigo, verifica se algum aliado tem Percepção Legítima dele
            if (!isTeammate)
            {
                bool isPerceivedByTeam = false;
                foreach (var ally in aliveAllies)
                {
                    if (TacticalCalloutSystem.CanBotPerceiveEnemy(ally, p, CalloutSystem, _mapProfileManager))
                    {
                        isPerceivedByTeam = true;
                        break;
                    }
                }

                if (!isPerceivedByTeam)
                {
                    // Venda nos olhos da IA: zera coordenadas [0,0,0], velocidade, mira e arma do inimigo oculto!
                    continue;
                }
            }

            targetTensor[i, 0] = Math.Clamp(pawn.AbsOrigin.X / 4096.0f, -1.5f, 1.5f);
            targetTensor[i, 1] = Math.Clamp(pawn.AbsOrigin.Y / 4096.0f, -1.5f, 1.5f);
            targetTensor[i, 2] = Math.Clamp(pawn.AbsOrigin.Z / 1024.0f, -1.5f, 1.5f);

            float vx = pawn.AbsVelocity?.X ?? 0f;
            float vy = pawn.AbsVelocity?.Y ?? 0f;
            float vz = pawn.AbsVelocity?.Z ?? 0f;
            targetTensor[i, 3] = Math.Clamp(vx / 250.0f, -1.5f, 1.5f);
            targetTensor[i, 4] = Math.Clamp(vy / 250.0f, -1.5f, 1.5f);
            targetTensor[i, 5] = Math.Clamp(vz / 250.0f, -1.5f, 1.5f);

            float yawRad = (pawn.EyeAngles?.Y ?? 0f) * (MathF.PI / 180.0f);
            float pitch = pawn.EyeAngles?.X ?? 0f;
            targetTensor[i, 6] = MathF.Cos(yawRad);
            targetTensor[i, 7] = MathF.Sin(yawRad);
            targetTensor[i, 8] = Math.Clamp(pitch / 90.0f, -1.0f, 1.0f);

            targetTensor[i, 9] = Math.Clamp(pawn.Health / 100.0f, 0f, 1f);
            targetTensor[i, 10] = Math.Clamp(pawn.ArmorValue / 100.0f, 0f, 1f);

            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";
            targetTensor[i, 11] = EncodeWeaponCategory(weaponName);

            var role = _roleManager.GetBotRole(p);
            targetTensor[i, 12] = role switch
            {
                BotRole.AWPer => 0.25f,
                BotRole.EntryFragger => 0.50f,
                BotRole.Rotator => 0.75f,
                BotRole.Anchor => 1.00f,
                _ => 0.50f
            };

            targetTensor[i, 15] = BotLocomotionDriver.HasC4(p) ? 1.0f : 0.0f;
        }
    }

    /// <summary>
    /// Executa a predição em lote (16Hz) das trajetórias nos 3 horizontes (0ms, 125ms, 250ms) para os 10 bots.
    /// Só assume o volante quando ativado por um dos 3 Gatilhos de Percepção Legítima (Visão, Áudio ou Hotzone).
    /// </summary>
    public void PredictBatch16Hz(
        float[,] ctFogTensor,
        float[,] trFogTensor,
        List<CCSPlayerController> orderedPlayers,
        ConcurrentDictionary<int, MicroMoveTrajectory> trajectories,
        float currentTime)
    {
        // Fase 1 da Matriz N x N: Atualiza timestamps de contato de aliados (para o delay de 0.6s do Wide Swing de Trade)
        foreach (var p in orderedPlayers)
        {
            if (p == null || !p.IsValid || !p.PawnIsAlive || !p.IsBot) continue;
            bool seesEnemy = p.PlayerPawn.Value?.Bot?.IsEnemyVisible ?? false;
            if (seesEnemy)
            {
                if (!_entryContactStartTime.ContainsKey(p.Slot))
                {
                    _entryContactStartTime[p.Slot] = currentTime;
                }
            }
            else
            {
                _entryContactStartTime.Remove(p.Slot);
            }
        }

        // Executa inferência neural ONNX em lote [2, 10, 18] -> [2, 10, 3, 97] no Cache L3 da CPU (~0.25ms)
        bool onnxRan = _isNeuralModelLoaded && RunOnnxBatchInference(ctFogTensor, trFogTensor);

        // Fase 2 da Matriz N x N: Calcula as 97 ações em 3 horizontes para cada bot vivo
        Span<float> logits = stackalloc float[ActionSpaceSize];
        for (int playerRowIdx = 0; playerRowIdx < orderedPlayers.Count && playerRowIdx < MaxPlayers; playerRowIdx++)
        {
            var bot = orderedPlayers[playerRowIdx];
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive || !bot.IsBot) continue;
            int teamBatchIdx = bot.Team == CsTeam.CounterTerrorist ? 0 : 1;

            var pawn = bot.PlayerPawn.Value;
            var csBot = pawn?.Bot;
            if (pawn == null || csBot == null || pawn.AbsOrigin == null) continue;

            var traj = trajectories.GetOrAdd(bot.Slot, s => new MicroMoveTrajectory { Slot = s });

            // Se um pulso crítico de Counter-Strafe ainda estiver em execução (< 160ms), preserva até concluir
            if (traj.IsOverrideActive &&
                traj.ActiveBehaviorTag == "CounterStrafe" &&
                currentTime < traj.OverrideExpiresAt)
            {
                continue;
            }

            // ITEM 4 & ITEM 9: Sinergia GPS (NavMesh) vs. Piloto de Fuga (MicroMove/ONNX)
            // Verifica os 3 Filtros de Percepção Legítima (Visão, Áudio ~1000u ou Hotzone pré-mapeada)
            var trigger = EvaluateLegitimateAdrenalineTrigger(bot, orderedPlayers);
            traj.LastTrigger = trigger;

            if (trigger == AdrenalineTriggerType.None_SafeTransitGps)
            {
                // Fora de zona de perigo e sem pistas visuais/sonoras: o GPS (NavMesh) conduz 100% da rota
                traj.IsOverrideActive = false;
                traj.ActiveBehaviorTag = "NavMesh_GPS";
                continue;
            }

            float curX = pawn.AbsOrigin.X;
            float curY = pawn.AbsOrigin.Y;
            float curZ = pawn.AbsOrigin.Z;
            float vx = pawn.AbsVelocity?.X ?? 0f;
            float vy = pawn.AbsVelocity?.Y ?? 0f;
            float speed2D = MathF.Sqrt(vx * vx + vy * vy);
            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";

            // =========================================================================
            // 1. COUNTER-STRAFE NO ÁPICE DO MOVIMENTO (Velocity Zeroing: t=0ms Reverse -> Stand Still)
            // =========================================================================
            bool isRifleOrSniper = IsPrecisionWeapon(weaponName);
            bool canCounterStrafe = !_counterStrafeCooldownUntil.TryGetValue(bot.Slot, out float csCd) || currentTime >= csCd;

            if (trigger == AdrenalineTriggerType.Vision_Spotted && isRifleOrSniper && speed2D >= 65.0f && canCounterStrafe)
            {
                float reverseAngleRad = MathF.Atan2(-vy, -vx);
                int reverseDirIdx = MicroMoveStep.QuantizeAngleToDirectionIndex(reverseAngleRad);
                int reverseActionId = MicroMoveStep.EncodeAction(reverseDirIdx, MicroSpeedTier.Run, isJump: false);

                float pulseDurationMs = Math.Clamp(speed2D * 0.45f, 80.0f, 120.0f);

                traj.Step0_Now = MicroMoveStep.FromActionId(reverseActionId, durationMs: pulseDurationMs);
                traj.Step1_125ms = MicroMoveStep.StandStill(durationMs: 125.0f);
                traj.Step2_250ms = MicroMoveStep.StandStill(durationMs: 125.0f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = "CounterStrafe";
                traj.OverrideExpiresAt = currentTime + 0.24f;

                _counterStrafeCooldownUntil[bot.Slot] = currentTime + 1.35f;

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    2.5f,
                    "MLMOVE - COUNTER-STRAFE",
                    $"**{bot.PlayerName}** aplicou *Velocity Zeroing* (Vel: `{speed2D:F0} u/s -> 0 u/s`, Pulso `{pulseDurationMs:F0}ms` Action `{reverseActionId}` -> `StandStill`) com `{weaponName.Replace("weapon_", "")}`.");
                continue;
            }

            // =========================================================================
            // 2. MATRIZ N x N DE TRADE SPACING (Repulsão < 140u e Wide Swing 250-400u após 0.6s)
            // =========================================================================
            CCSPlayerController? closestAlly = null;
            float closestAllyDist = float.MaxValue;
            CCSPlayerController? combatAllyInFront = null;
            float combatAllyDist = float.MaxValue;

            foreach (var other in orderedPlayers)
            {
                if (other == null || !other.IsValid || !other.PawnIsAlive || other.Slot == bot.Slot || other.Team != bot.Team)
                    continue;

                var otherOrigin = other.PlayerPawn.Value?.AbsOrigin;
                if (otherOrigin == null) continue;

                float dx = otherOrigin.X - curX;
                float dy = otherOrigin.Y - curY;
                float dz = otherOrigin.Z - curZ;
                if (MathF.Abs(dz) > 160.0f) continue;

                float dist2D = MathF.Sqrt(dx * dx + dy * dy);
                if (dist2D < closestAllyDist)
                {
                    closestAllyDist = dist2D;
                    closestAlly = other;
                }

                bool allyInFirefight = other.PlayerPawn.Value?.Bot?.IsEnemyVisible ?? false;
                if (allyInFirefight && dist2D < combatAllyDist && dist2D <= 600.0f)
                {
                    combatAllyDist = dist2D;
                    combatAllyInFront = other;
                }
            }

            // 2A. Repulsão Lateral Anti-Stack / Anti-Spray Duplo (< 140 unidades em Hotzone/Combate)
            if (closestAlly != null && closestAllyDist < 140.0f && closestAlly.PlayerPawn.Value?.AbsOrigin != null)
            {
                var allyPos = closestAlly.PlayerPawn.Value.AbsOrigin;
                float awayX = curX - allyPos.X;
                float awayY = curY - allyPos.Y;

                float awayAngle = MathF.Atan2(awayY, awayX) + (bot.Slot % 2 == 0 ? 0.55f : -0.55f);
                int repulseDirIdx = MicroMoveStep.QuantizeAngleToDirectionIndex(awayAngle);
                int repulseAction = MicroMoveStep.EncodeAction(repulseDirIdx, MicroSpeedTier.Run, isJump: false);

                traj.Step0_Now = MicroMoveStep.FromActionId(repulseAction, 90f);
                traj.Step1_125ms = MicroMoveStep.FromActionId(repulseAction, 90f);
                traj.Step2_250ms = MicroMoveStep.StandStill(80f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = "TradeSpacing_Repulsion";
                traj.OverrideExpiresAt = currentTime + 0.18f;

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    4.0f,
                    "MLMOVE - TRADE SPACING",
                    $"**{bot.PlayerName}** aplicou repulsão lateral de **{closestAlly.PlayerName}** (Dist: `{closestAllyDist:F0}u < 140u`, Action `{repulseAction}`, Gatilho: `{trigger}`) evitando spray duplo.");
                continue;
            }

            // 2B. Trade Kill Window (250 a 400 unidades) + Wide Swing Coordenado após 0.6s de contato do Entry
            if (combatAllyInFront != null &&
                !csBot.IsEnemyVisible &&
                combatAllyInFront.PlayerPawn.Value?.AbsOrigin != null &&
                _entryContactStartTime.TryGetValue(combatAllyInFront.Slot, out float contactStart) &&
                (currentTime - contactStart) >= 0.60f)
            {
                var allyPos = combatAllyInFront.PlayerPawn.Value.AbsOrigin;
                float toAllyX = allyPos.X - curX;
                float toAllyY = allyPos.Y - curY;
                float baseAngleToAlly = MathF.Atan2(toAllyY, toAllyX);

                float swingOffsetRad = (bot.Slot % 2 == 0) ? (MathF.PI / 3.2f) : -(MathF.PI / 3.2f);
                if (combatAllyDist > 400.0f)
                {
                    swingOffsetRad *= 0.45f;
                }
                else if (combatAllyDist < 250.0f)
                {
                    swingOffsetRad *= 1.35f;
                }

                float wideSwingAngle = baseAngleToAlly + swingOffsetRad;
                int swingDirIdx = MicroMoveStep.QuantizeAngleToDirectionIndex(wideSwingAngle);

                // Usa amostragem estocástica ("dado viciado") entre a direção principal do Wide Swing e a adjacente
                logits.Fill(-10.0f);
                int primaryAction = MicroMoveStep.EncodeAction(swingDirIdx, MicroSpeedTier.Run, isJump: false);
                int altAction = MicroMoveStep.EncodeAction((swingDirIdx + 1) % 16, MicroSpeedTier.Run, isJump: false);
                logits[primaryAction] = 2.2f; // ~75% probabilidade
                logits[altAction] = 1.1f;     // ~25% probabilidade
                int sampledSwingAction = SampleActionFromLogits(logits, temperature: 0.85f);

                traj.Step0_Now = MicroMoveStep.FromActionId(sampledSwingAction, 125f);
                traj.Step1_125ms = MicroMoveStep.FromActionId(sampledSwingAction, 125f);
                traj.Step2_250ms = MicroMoveStep.StandStill(100f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = "TradeSpacing_WideSwing";
                traj.OverrideExpiresAt = currentTime + 0.28f;

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    4.0f,
                    "MLMOVE - TRADE SPACING",
                    $"**{bot.PlayerName}** iniciou *Wide Swing* escalonado (`+0.6s`, Dist: `{combatAllyDist:F0}u` na janela `250-400u`, Action `{sampledSwingAction}`) para cobrir/trocar **{combatAllyInFront.PlayerName}**!");
                continue;
            }

            // =========================================================================
            // 3. WALL-HUGGING / "FATIANDO A TORTA" EM HOTZONES E PISTAS SONORAS
            // =========================================================================
            if (!csBot.IsEnemyVisible && speed2D > 80.0f)
            {
                var nearCp = _mapProfileManager.FindChokepointAt(curX, curY, curZ);
                if (nearCp != null)
                {
                    float toCenterX = nearCp.X - curX;
                    float toCenterY = nearCp.Y - curY;
                    float distToCenter = MathF.Sqrt(toCenterX * toCenterX + toCenterY * toCenterY);

                    if (distToCenter < 95.0f && distToCenter > 5.0f)
                    {
                        float moveAngle = MathF.Atan2(vy, vx);
                        float wallHugAngle = moveAngle + (bot.Slot % 2 == 0 ? 0.38f : -0.38f);
                        int hugDirIdx = MicroMoveStep.QuantizeAngleToDirectionIndex(wallHugAngle);
                        int hugAction = MicroMoveStep.EncodeAction(hugDirIdx, MicroSpeedTier.Run, isJump: false);

                        if (onnxRan)
                        {
                            for (int a = 0; a < ActionSpaceSize; a++)
                                logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 0, a];
                            logits[hugAction] += 2.0f;
                            hugAction = SampleActionFromLogits(logits, temperature: 0.80f);
                        }

                        traj.Step0_Now = MicroMoveStep.FromActionId(hugAction, 100f);
                        traj.Step1_125ms = MicroMoveStep.FromActionId(hugAction, 100f);
                        traj.Step2_250ms = MicroMoveStep.FromActionId(hugAction, 100f);
                        traj.GeneratedAtTime = currentTime;
                        traj.IsOverrideActive = true;
                        traj.ActiveBehaviorTag = onnxRan ? "ONNX_WallHugging" : "WallHugging_Hotzone";
                        traj.OverrideExpiresAt = currentTime + 0.14f;
                        continue;
                    }
                }
            }

            // =========================================================================
            // 4. INFERÊNCIA DIRETA DO TRANSFORMER ONNX (Multi-Horizonte: 0ms, 125ms, 250ms)
            // =========================================================================
            if (onnxRan && (trigger == AdrenalineTriggerType.Vision_Spotted || trigger == AdrenalineTriggerType.Audio_HeardCue))
            {
                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 0, a];
                int act0 = SampleActionFromLogits(logits, temperature: 0.85f);

                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 1, a];
                int act1 = SampleActionFromLogits(logits, temperature: 0.85f);

                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 2, a];
                int act2 = SampleActionFromLogits(logits, temperature: 0.85f);

                traj.Step0_Now = MicroMoveStep.FromActionId(act0, 125f);
                traj.Step1_125ms = MicroMoveStep.FromActionId(act1, 125f);
                traj.Step2_250ms = MicroMoveStep.FromActionId(act2, 125f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = $"ONNX_{trigger}";
                traj.OverrideExpiresAt = currentTime + 0.25f;

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    4.0f,
                    "MLMOVE - ONNX 16HZ",
                    $"`[Modo ONNX Ativo]` **{bot.PlayerName}** ({trigger}, Latência CPU: `{LastInferenceLatencyMs:F2}ms`) -> Horizontes `[{act0}, {act1}, {act2}]`.");
                continue;
            }

            traj.IsOverrideActive = false;
            traj.ActiveBehaviorTag = "NavMesh_GPS";
        }
    }

    private void LogDebugWithCooldown(int slot, float currentTime, float cooldownSec, string category, string message)
    {
        if (TelemetryLogger == null || !TelemetryLogger.IsEnabled) return;

        if (_lastDebugLogTime.TryGetValue(slot, out float lastTime) && (currentTime - lastTime) < cooldownSec)
        {
            return;
        }

        _lastDebugLogTime[slot] = currentTime;
        TelemetryLogger.LogEvent(category, message);
    }

    private static bool IsPrecisionWeapon(string weaponDesignerName)
    {
        if (string.IsNullOrEmpty(weaponDesignerName)) return false;
        return weaponDesignerName.Contains("ak47", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("m4a1", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("awp", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("ssg08", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("galilar", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("famas", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("aug", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("sg556", StringComparison.OrdinalIgnoreCase) ||
               weaponDesignerName.Contains("deagle", StringComparison.OrdinalIgnoreCase);
    }

    private static float EncodeWeaponCategory(string weaponDesignerName)
    {
        if (string.IsNullOrEmpty(weaponDesignerName)) return 0.0f;
        if (weaponDesignerName.Contains("knife", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("bayonet", StringComparison.OrdinalIgnoreCase)) return 0.2f;
        if (weaponDesignerName.Contains("awp", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("ssg08", StringComparison.OrdinalIgnoreCase)) return 1.0f;
        if (weaponDesignerName.Contains("ak47", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("m4a1", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("galilar", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("famas", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("aug", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("sg556", StringComparison.OrdinalIgnoreCase)) return 0.8f;
        if (weaponDesignerName.Contains("mac10", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("mp9", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("mp7", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("ump45", StringComparison.OrdinalIgnoreCase) ||
            weaponDesignerName.Contains("p90", StringComparison.OrdinalIgnoreCase)) return 0.6f;
        return 0.4f;
    }
}
