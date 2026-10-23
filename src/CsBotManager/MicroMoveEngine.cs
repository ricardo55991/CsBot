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
    None_SafeTransitGps = 0, // Fora de perigo: GPS (NavMesh) conduz 100% da viagem longa
    Vision_Spotted = 1,      // Gatilho 1: Visão legítima (SpottedByMask / IsEnemyVisible)
    Audio_HeardCue = 2,      // Gatilho 2: Pista sonora legítima (~1000u passos / tiros recentes no setor)
    Hotzone_PreMapped = 3    // Gatilho 3: Zona de Perigo / Staging Area pré-mapeada ("fatiando a torta")
}

public sealed class TradeSpacingPairState
{
    public int BotSlotA { get; init; }
    public int BotSlotB { get; init; }
    public float LastTriggeredAtTime { get; set; }
    public float CooldownUntilTime { get; set; }
    public float DistanceBefore2D { get; set; }
    public float DistanceAfter2D { get; set; }
    public int YieldingBotSlot { get; set; }
    public int PriorityBotSlot { get; set; }
    public string ActionApplied { get; set; } = string.Empty;
    public bool SharedTargetDetected { get; set; }
    public Vector OffsetTargetPosition { get; set; } = new(0, 0, 0);
}

public sealed class CounterStrafeDiagnostic
{
    public bool Triggered { get; init; }
    public string SuppressionReason { get; init; } = "NONE";
    public float SpeedBefore2D { get; init; }
    public float TargetDistance2D { get; init; }
    public float AimErrorDegrees { get; init; }
    public bool HasLineOfSight { get; init; }
    public bool WeaponReady { get; init; }
    public int AmmoAvailable { get; init; }
    public bool AttackIntent { get; init; }
    public int ReverseActionId { get; init; }
    public float PulseDurationMs { get; init; }
}

public struct MicroMoveStep
{
    public int ActionId { get; set; }
    public int DirectionIndex { get; set; }
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

    public readonly string ToReadableString(float botYaw = 0f)
    {
        if (ActionId <= 0 || ActionId > 96)
            return "Parado (0u)";

        float worldAngleDeg = DirectionIndex * 22.5f;
        float relAngle = worldAngleDeg - botYaw;
        while (relAngle > 180f) relAngle -= 360f;
        while (relAngle < -180f) relAngle += 360f;

        string dirName = relAngle switch
        {
            >= -22.5f and <= 22.5f => "Avanco",
            > 22.5f and <= 67.5f => "Diag-Dir",
            > 67.5f and <= 112.5f => "Strafe-Dir",
            > 112.5f and <= 157.5f => "Recuo-Dir",
            < -22.5f and >= -67.5f => "Diag-Esq",
            < -67.5f and >= -112.5f => "Strafe-Esq",
            < -112.5f and >= -157.5f => "Recuo-Esq",
            _ => "Recuo"
        };

        string speedName = SpeedTier switch
        {
            MicroSpeedTier.Run => "250u",
            MicroSpeedTier.WalkShift => "Shift",
            MicroSpeedTier.Crouch => "Duck",
            _ => "Run"
        };

        string extra = IsJump ? "+Jump" : "";
        return $"{dirName}({speedName}{extra})";
    }

    public readonly (float ForwardMove, float SideMove) ToBotRelativeMoves(float botYawDegrees)
    {
        if (ActionId == 0 || SpeedScale <= 0.01f)
        {
            return (0f, 0f);
        }

        float yawRad = botYawDegrees * (MathF.PI / 180.0f);
        float forwardX = MathF.Cos(yawRad);
        float forwardY = MathF.Sin(yawRad);
        float rightX = MathF.Sin(yawRad);
        float rightY = -MathF.Cos(yawRad);

        float forwardMove = (WorldDirX * forwardX + WorldDirY * forwardY) * SpeedScale;
        float sideMove = (WorldDirX * rightX + WorldDirY * rightY) * SpeedScale;

        return (forwardMove, sideMove);
    }
}

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
    public MovementIntentSource IntentPriority { get; set; } = MovementIntentSource.MicroMove;
    public Vector? SuggestedGoalOverride { get; set; }

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

public class MicroMoveEngine : IMicroMovePredictor, IDisposable
{
    public CsBotManagerPlugin? Plugin { get; set; }
    public BotSystemConfig Config { get; set; } = BotSystemConfig.Default;
    public MovementArbitrator? Arbitrator { get; set; }

    private readonly Dictionary<(int Slot, string ChokepointName), float> _hotzoneEntryTimes = new();
    private readonly Dictionary<(int Slot, string ChokepointName), float> _hotzoneCooldowns = new();
    private readonly Dictionary<int, (Vector Pos, float SinceTime)> _stationaryTrackers = new();
    private readonly Dictionary<int, float> _standStillAccumulatedSeconds = new();
    private readonly Dictionary<(int SlotA, int SlotB), TradeSpacingPairState> _pairSpacingStates = new();

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
    private readonly float[,] _ctFogInputTensor = new float[MaxPlayers, FeatureDim];
    private readonly float[,] _trFogInputTensor = new float[MaxPlayers, FeatureDim];
    private readonly float[] _onnxBatchInputBuffer = new float[2 * MaxPlayers * FeatureDim];
    private readonly float[,,,] _onnxBatchOutputLogits = new float[2, MaxPlayers, HorizonsCount, ActionSpaceSize];
    private InferenceSession? _onnxSession;
    private static bool _nativeOnnxLoaded;

    private readonly Dictionary<int, float> _counterStrafeCooldownUntil = new();
    private readonly Dictionary<int, float> _entryContactStartTime = new();
    private readonly Dictionary<int, float> _lastDebugLogTime = new();

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

    /// <summary>
    /// Determina deterministicamente qual bot tem prioridade e qual bot deve ceder espaço no par (Bug 4).
    /// Hierarquia de prioridade: Portador da C4 > Em Combate Ativo > EntryFragger > AWPer > Menor Slot.
    /// Retorna (PriorityBotSlot, YieldingBotSlot).
    /// </summary>
    public static (int PrioritySlot, int YieldingSlot) ResolvePairPriority(
        int slotA,
        bool aHasC4,
        bool aInCombat,
        BotRole roleA,
        int slotB,
        bool bHasC4,
        bool bInCombat,
        BotRole roleB)
    {
        if (aHasC4 != bHasC4)
            return aHasC4 ? (slotA, slotB) : (slotB, slotA);

        if (aInCombat != bInCombat)
            return aInCombat ? (slotA, slotB) : (slotB, slotA);

        int rankA = GetRolePriorityRank(roleA);
        int rankB = GetRolePriorityRank(roleB);
        if (rankA != rankB)
            return rankA < rankB ? (slotA, slotB) : (slotB, slotA);

        return slotA < slotB ? (slotA, slotB) : (slotB, slotA);
    }

    private static int GetRolePriorityRank(BotRole role) => role switch
    {
        BotRole.EntryFragger => 1,
        BotRole.AWPer => 2,
        BotRole.Rotator => 3,
        BotRole.Anchor => 4,
        _ => 5
    };

    /// <summary>
    /// Avalia se o par (slotA, slotB) pode acionar repulsão de Trade Spacing agora, respeitando cooldown de par (2.5s),
    /// registrando `shared_target_detected` quando `dist2D < 1.0f` e deslocando o destino no NavMesh para o bot que cede.
    /// </summary>
    public TradeSpacingPairState? TryEvaluatePairRepulsion(
        int currentBotSlot,
        float curX,
        float curY,
        float curZ,
        bool currentHasC4,
        bool currentInCombat,
        BotRole currentRole,
        int allySlot,
        float allyX,
        float allyY,
        float allyZ,
        bool allyHasC4,
        bool allyInCombat,
        BotRole allyRole,
        float currentTime,
        out int repulseActionId)
    {
        repulseActionId = 0;
        float dx = curX - allyX;
        float dy = curY - allyY;
        float dist2D = MathF.Sqrt(dx * dx + dy * dy);

        var pairKey = currentBotSlot < allySlot ? (currentBotSlot, allySlot) : (allySlot, currentBotSlot);
        if (_pairSpacingStates.TryGetValue(pairKey, out var existingState))
        {
            existingState.DistanceAfter2D = dist2D;
            if (currentTime < existingState.CooldownUntilTime)
            {
                return null;
            }
        }

        if (dist2D >= Config.TradeSpacingMinDist2D)
        {
            return null;
        }

        var (prioritySlot, yieldingSlot) = ResolvePairPriority(
            currentBotSlot, currentHasC4, currentInCombat, currentRole,
            allySlot, allyHasC4, allyInCombat, allyRole);

        // Apenas o bot que cede (YieldingSlot) executa o recuo/offset lateral; o bot prioritário mantém sua rota!
        if (currentBotSlot != yieldingSlot)
        {
            return null;
        }

        bool sharedTarget = dist2D < 1.5f;
        float awayAngle = sharedTarget
            ? ((yieldingSlot % 2 == 0) ? (MathF.PI * 0.5f) : -(MathF.PI * 0.5f))
            : MathF.Atan2(dy, dx) + ((yieldingSlot % 2 == 0) ? 0.55f : -0.55f);

        int repulseDirIdx = MicroMoveStep.QuantizeAngleToDirectionIndex(awayAngle);
        repulseActionId = MicroMoveStep.EncodeAction(repulseDirIdx, MicroSpeedTier.Run, isJump: false);

        float offsetDist = Config.TradeSpacingNavOffsetUnits;
        var offsetPos = new Vector(
            curX + MathF.Cos(awayAngle) * offsetDist,
            curY + MathF.Sin(awayAngle) * offsetDist,
            curZ);

        var state = new TradeSpacingPairState
        {
            BotSlotA = pairKey.Item1,
            BotSlotB = pairKey.Item2,
            LastTriggeredAtTime = currentTime,
            CooldownUntilTime = currentTime + Config.TradeSpacingPairCooldownSeconds,
            DistanceBefore2D = dist2D,
            DistanceAfter2D = dist2D,
            PriorityBotSlot = prioritySlot,
            YieldingBotSlot = yieldingSlot,
            ActionApplied = $"RepulseAction_{repulseActionId}_Offset_{offsetDist:F0}u",
            SharedTargetDetected = sharedTarget,
            OffsetTargetPosition = offsetPos
        };

        _pairSpacingStates[pairKey] = state;
        return state;
    }

    /// <summary>
    /// Verifica se a distância 2D ao aliado em combate está estritamente dentro da janela configurada de Wide Swing [250u, 400u].
    /// </summary>
    public bool IsWithinWideSwingWindow(float dist2D)
    {
        return dist2D >= Config.WideSwingMinDist2D && dist2D <= Config.WideSwingMaxDist2D;
    }

    /// <summary>
    /// Avalia de forma pura e determinística todos os critérios de engajamento real iminente para Counter-Strafe (Bug 4).
    /// </summary>
    public CounterStrafeDiagnostic EvaluateCounterStrafeEligibility(
        int botSlot,
        float currentTime,
        float speed2D,
        float vx,
        float vy,
        string weaponName,
        bool isPrecisionWeapon,
        bool hasValidAliveTarget,
        bool hasLineOfSight,
        float aimErrorDegrees,
        bool weaponReady,
        int ammoAvailable,
        bool isReloading,
        bool attackIntent,
        float targetDistance2D)
    {
        if (_counterStrafeCooldownUntil.TryGetValue(botSlot, out float cdUntil) && currentTime < cdUntil)
        {
            return new CounterStrafeDiagnostic { Triggered = false, SuppressionReason = "COOLDOWN_ACTIVE", SpeedBefore2D = speed2D };
        }
        if (!isPrecisionWeapon)
        {
            return new CounterStrafeDiagnostic { Triggered = false, SuppressionReason = "NOT_PRECISION_WEAPON", SpeedBefore2D = speed2D };
        }
        if (speed2D < Config.CounterStrafeMinSpeed2D)
        {
            return new CounterStrafeDiagnostic { Triggered = false, SuppressionReason = "SPEED_BELOW_THRESHOLD", SpeedBefore2D = speed2D };
        }
        if (!hasValidAliveTarget)
        {
            return new CounterStrafeDiagnostic { Triggered = false, SuppressionReason = "NO_VALID_TARGET", SpeedBefore2D = speed2D };
        }
        if (!hasLineOfSight)
        {
            return new CounterStrafeDiagnostic { Triggered = false, SuppressionReason = "NO_LINE_OF_SIGHT", SpeedBefore2D = speed2D };
        }
        if (!weaponReady || isReloading || ammoAvailable <= 0)
        {
            return new CounterStrafeDiagnostic
            {
                Triggered = false,
                SuppressionReason = "WEAPON_NOT_READY_OR_EMPTY",
                SpeedBefore2D = speed2D,
                WeaponReady = weaponReady,
                AmmoAvailable = ammoAvailable
            };
        }
        if (!attackIntent)
        {
            return new CounterStrafeDiagnostic { Triggered = false, SuppressionReason = "NO_ATTACK_INTENT", SpeedBefore2D = speed2D };
        }
        if (aimErrorDegrees > Config.CounterStrafeMaxAimErrorDegrees)
        {
            return new CounterStrafeDiagnostic
            {
                Triggered = false,
                SuppressionReason = $"AIM_ERROR_TOO_HIGH({aimErrorDegrees:F1}>{Config.CounterStrafeMaxAimErrorDegrees:F1})",
                SpeedBefore2D = speed2D,
                AimErrorDegrees = aimErrorDegrees
            };
        }

        float reverseAngleRad = MathF.Atan2(-vy, -vx);
        int reverseDirIdx = MicroMoveStep.QuantizeAngleToDirectionIndex(reverseAngleRad);
        int reverseActionId = MicroMoveStep.EncodeAction(reverseDirIdx, MicroSpeedTier.Run, isJump: false);
        float pulseDurationMs = Math.Clamp(speed2D * 0.45f, 80.0f, 120.0f);

        _counterStrafeCooldownUntil[botSlot] = currentTime + Config.CounterStrafeCooldownSeconds;

        return new CounterStrafeDiagnostic
        {
            Triggered = true,
            SuppressionReason = "NONE",
            SpeedBefore2D = speed2D,
            TargetDistance2D = targetDistance2D,
            AimErrorDegrees = aimErrorDegrees,
            HasLineOfSight = hasLineOfSight,
            WeaponReady = weaponReady,
            AmmoAvailable = ammoAvailable,
            AttackIntent = attackIntent,
            ReverseActionId = reverseActionId,
            PulseDurationMs = pulseDurationMs
        };
    }

    public static float ComputeAimErrorDegrees2D(float botX, float botY, float botYawDeg, float targetX, float targetY)
    {
        float dx = targetX - botX;
        float dy = targetY - botY;
        if (MathF.Abs(dx) < 0.001f && MathF.Abs(dy) < 0.001f) return 0f;

        float desiredYawDeg = MathF.Atan2(dy, dx) * (180.0f / MathF.PI);
        float diff = desiredYawDeg - botYawDeg;
        while (diff > 180f) diff -= 360f;
        while (diff < -180f) diff += 360f;
        return MathF.Abs(diff);
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
            Interlocked.Exchange(ref _pendingModelReloadAtMs, Environment.TickCount64 + 1200L);
        }
    }

    public void ResetRound(IBotControllerApi? api)
    {
        _trajectories.Clear();
        _counterStrafeCooldownUntil.Clear();
        _entryContactStartTime.Clear();
        _lastDebugLogTime.Clear();
        _hotzoneEntryTimes.Clear();
        _hotzoneCooldowns.Clear();
        _stationaryTrackers.Clear();
        _standStillAccumulatedSeconds.Clear();
        _pairSpacingStates.Clear();
        _tickCounter = 0;
    }

    public void Dispose()
    {
        if (_onnxWatcher != null)
        {
            try
            {
                _onnxWatcher.EnableRaisingEvents = false;
                _onnxWatcher.Dispose();
            }
            catch { }
        }
        lock (_onnxLock)
        {
            _onnxSession?.Dispose();
            _onnxSession = null;
        }
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

        if (currentCp != null)
        {
            float nowTime = Server.CurrentTime;
            var hzKey = (bot.Slot, currentCp.Name);

            if (_hotzoneCooldowns.TryGetValue(hzKey, out float cdExpire) && nowTime < cdExpire)
            {
                return AdrenalineTriggerType.None_SafeTransitGps;
            }

            if (!_hotzoneEntryTimes.TryGetValue(hzKey, out float entryTime))
            {
                _hotzoneEntryTimes[hzKey] = nowTime;
                return AdrenalineTriggerType.Hotzone_PreMapped;
            }

            if ((nowTime - entryTime) > Config.HotzoneMaxActiveSeconds)
            {
                _hotzoneCooldowns[hzKey] = nowTime + Config.HotzoneCooldownSeconds;
                _hotzoneEntryTimes.Remove(hzKey);
                return AdrenalineTriggerType.None_SafeTransitGps;
            }

            return AdrenalineTriggerType.Hotzone_PreMapped;
        }
        else
        {
            var keysToRemove = _hotzoneEntryTimes.Keys.Where(k => k.Slot == bot.Slot).ToList();
            foreach (var k in keysToRemove) _hotzoneEntryTimes.Remove(k);
        }

        return AdrenalineTriggerType.None_SafeTransitGps;
    }

    /// <summary>
    /// Chamado no OnTick principal (64Hz).
    /// A cada 4 ticks (16Hz = 62.5ms), reconstrói os tensores [10, 18] e publica MovementIntents no MovementArbitrator.
    /// NENHUMA escrita direta é feita em CCSBot.IsStopping, WaitTimer ou StartUsercmdMovement aqui (Regra 3).
    /// </summary>
    public void UpdateTick(
        float currentTime,
        float roundTimeRemaining,
        bool isBombPlanted,
        ConcurrentDictionary<int, TrackedBotNavState> navStates,
        IBotControllerApi? botApi)
    {
        _tickCounter++;
        int gameTick = Server.TickCount;

        long reloadTargetMs = Interlocked.Read(ref _pendingModelReloadAtMs);
        if (reloadTargetMs > 0L && Environment.TickCount64 >= reloadTargetMs)
        {
            Interlocked.Exchange(ref _pendingModelReloadAtMs, 0L);
            TryLoadMapModel(_loadedMapName, DefaultModelsDir);
        }

        if (_tickCounter % 4 == 0)
        {
            var allPlayers = Utilities.GetPlayers()
                .Where(p => p != null && p.IsValid && (p.Team == CsTeam.CounterTerrorist || p.Team == CsTeam.Terrorist))
                .OrderBy(p => p.Team)
                .ThenBy(p => p.Slot)
                .Take(MaxPlayers)
                .ToList();

            BuildFogOfWarInputTensorForTeam(_ctFogInputTensor, CsTeam.CounterTerrorist, allPlayers, roundTimeRemaining, isBombPlanted);
            BuildFogOfWarInputTensorForTeam(_trFogInputTensor, CsTeam.Terrorist, allPlayers, roundTimeRemaining, isBombPlanted);

            PredictBatch16Hz(_ctFogInputTensor, _trFogInputTensor, allPlayers, _trajectories, currentTime);
        }

        if (Arbitrator == null) return;

        foreach (var kvp in _trajectories)
        {
            int slot = kvp.Key;
            var traj = kvp.Value;

            if (!traj.IsOverrideActive || currentTime > traj.OverrideExpiresAt)
            {
                traj.IsOverrideActive = false;
                continue;
            }

            var bot = Utilities.GetPlayerFromSlot(slot);
            if (bot == null || !bot.IsValid || !bot.PawnIsAlive)
            {
                traj.IsOverrideActive = false;
                continue;
            }

            var pawn = bot.PlayerPawn.Value;
            if (pawn == null || pawn.AbsOrigin == null) continue;
            bool isDefusing = false;
            try { isDefusing = pawn.IsDefusing; } catch { }
            if (isDefusing) continue;

            // Cancelamento imediato de Counter-Strafe se o inimigo morreu ou saiu de visão (Bug 4)
            if (traj.ActiveBehaviorTag == "CounterStrafe" && !(pawn.Bot?.IsEnemyVisible ?? false))
            {
                traj.IsOverrideActive = false;
                continue;
            }

            var activeStep = traj.GetStepForElapsed(currentTime);

            if (activeStep.ActionId == 0 || activeStep.SpeedScale <= 0.1f)
            {
                bool isTrObjectiveBot = bot.Team == CsTeam.Terrorist &&
                    (BotLocomotionDriver.HasC4(bot) ||
                     pawn.InBombZone ||
                     (Plugin?.CurrentPlan?.CurrentPhase == RoundPhase.Executing) ||
                     (Plugin?.TrPivotController?.HasPivotedThisRound == true));

                if (isTrObjectiveBot && !(pawn.Bot?.IsEnemyVisible ?? false))
                {
                    traj.IsOverrideActive = false;
                    continue;
                }

                // Teto contextual de StandStill (Bug 3: impede congelar indefinidamente em StandStill sem contato)
                float dt = 0.015625f;
                float accum = _standStillAccumulatedSeconds.GetValueOrDefault(slot, 0f) + dt;
                _standStillAccumulatedSeconds[slot] = accum;
                float maxAllowedStandStill = (pawn.Bot?.IsEnemyVisible ?? false)
                    ? Config.StandStillMaxDefensiveSeconds
                    : Config.StandStillMaxAggressiveSeconds;

                if (accum > maxAllowedStandStill)
                {
                    traj.IsOverrideActive = false;
                    _standStillAccumulatedSeconds[slot] = 0f;
                    continue;
                }

                Arbitrator.PublishIntent(new MovementIntent
                {
                    BotSlot = slot,
                    BotName = bot.PlayerName,
                    GameTick = gameTick,
                    CurrentTime = currentTime,
                    Source = traj.IntentPriority,
                    Kind = MovementCommandKind.HoldStop,
                    Reason = $"{traj.ActiveBehaviorTag}_StandStill",
                    ExpiresAtTime = traj.OverrideExpiresAt,
                    IsStopping = true,
                    WaitDurationSeconds = 0.12f,
                    GoalX = traj.SuggestedGoalOverride?.X,
                    GoalY = traj.SuggestedGoalOverride?.Y,
                    GoalZ = traj.SuggestedGoalOverride?.Z
                });
            }
            else
            {
                _standStillAccumulatedSeconds[slot] = 0f;
                float botYaw = pawn.EyeAngles?.Y ?? 0.0f;
                var (forwardMove, sideMove) = activeStep.ToBotRelativeMoves(botYaw);

                Arbitrator.PublishIntent(new MovementIntent
                {
                    BotSlot = slot,
                    BotName = bot.PlayerName,
                    GameTick = gameTick,
                    CurrentTime = currentTime,
                    Source = traj.IntentPriority,
                    Kind = MovementCommandKind.UsercmdVector,
                    Reason = $"{traj.ActiveBehaviorTag}_Act{activeStep.ActionId}",
                    ExpiresAtTime = traj.OverrideExpiresAt,
                    UseUsercmdVelocity = true,
                    ForwardMove = forwardMove,
                    SideMove = sideMove,
                    Buttons = activeStep.Buttons,
                    ButtonsDurationMs = (int)Math.Clamp(activeStep.DurationMs, 60f, 150f),
                    GoalX = traj.SuggestedGoalOverride?.X,
                    GoalY = traj.SuggestedGoalOverride?.Y,
                    GoalZ = traj.SuggestedGoalOverride?.Z
                });
            }
        }
    }

    public void BuildStandardizedInputTensor(
        float[,] targetTensor,
        CsTeam observerTeam,
        List<CCSPlayerController> orderedPlayers,
        float roundTimeRemaining,
        bool isBombPlanted)
    {
        BuildFogOfWarInputTensorForTeam(targetTensor, observerTeam, orderedPlayers, roundTimeRemaining, isBombPlanted);
    }

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

    public void PredictBatch16Hz(
        float[,] ctFogTensor,
        float[,] trFogTensor,
        List<CCSPlayerController> orderedPlayers,
        ConcurrentDictionary<int, MicroMoveTrajectory> trajectories,
        float currentTime)
    {
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

        bool onnxRan = _isNeuralModelLoaded && RunOnnxBatchInference(ctFogTensor, trFogTensor);

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
            traj.SuggestedGoalOverride = null;

            if (traj.IsOverrideActive &&
                traj.ActiveBehaviorTag == "CounterStrafe" &&
                currentTime < traj.OverrideExpiresAt &&
                csBot.IsEnemyVisible)
            {
                continue;
            }

            var trigger = EvaluateLegitimateAdrenalineTrigger(bot, orderedPlayers);
            traj.LastTrigger = trigger;

            if (trigger == AdrenalineTriggerType.None_SafeTransitGps)
            {
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
            float botYaw = pawn.EyeAngles?.Y ?? 0f;

            var activeWep = pawn.WeaponServices?.ActiveWeapon.Value;
            string weaponName = activeWep?.DesignerName ?? "";
            int ammoClip = activeWep?.Clip1 ?? 0;

            bool isStationary = false;
            if (_stationaryTrackers.TryGetValue(bot.Slot, out var stPosTime))
            {
                float dX = curX - stPosTime.Pos.X;
                float dY = curY - stPosTime.Pos.Y;
                float distMoved2D = MathF.Sqrt(dX * dX + dY * dY);
                if (distMoved2D > 50.0f)
                {
                    _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);
                }
                else if ((currentTime - stPosTime.SinceTime) > 3.0f)
                {
                    isStationary = true;
                }
            }
            else
            {
                _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);
            }

            // =========================================================================
            // 1. COUNTER-STRAFE COM CRITÉRIOS ESTRITOS DE ENGAJAMENTO IMINENTE (Bug 4)
            // =========================================================================
            if (trigger == AdrenalineTriggerType.Vision_Spotted && csBot.IsEnemyVisible)
            {
                CCSPlayerController? bestEnemy = null;
                float bestEnemyDist2D = float.MaxValue;
                float bestAimError = 180.0f;

                foreach (var enemy in orderedPlayers)
                {
                    if (enemy == null || !enemy.IsValid || !enemy.PawnIsAlive || enemy.Team == bot.Team) continue;
                    var eOrigin = enemy.PlayerPawn.Value?.AbsOrigin;
                    if (eOrigin == null) continue;
                    if (!TacticalCalloutSystem.CanBotPerceiveEnemy(bot, enemy, CalloutSystem, _mapProfileManager)) continue;

                    float edx = eOrigin.X - curX;
                    float edy = eOrigin.Y - curY;
                    float eDist2D = MathF.Sqrt(edx * edx + edy * edy);
                    float aimErr = ComputeAimErrorDegrees2D(curX, curY, botYaw, eOrigin.X, eOrigin.Y);
                    if (aimErr < bestAimError)
                    {
                        bestAimError = aimErr;
                        bestEnemyDist2D = eDist2D;
                        bestEnemy = enemy;
                    }
                }

                var csDiag = EvaluateCounterStrafeEligibility(
                    botSlot: bot.Slot,
                    currentTime: currentTime,
                    speed2D: speed2D,
                    vx: vx,
                    vy: vy,
                    weaponName: weaponName,
                    isPrecisionWeapon: IsPrecisionWeapon(weaponName),
                    hasValidAliveTarget: bestEnemy != null,
                    hasLineOfSight: csBot.IsEnemyVisible && bestEnemy != null,
                    aimErrorDegrees: bestAimError,
                    weaponReady: !BotLocomotionDriver.IsGrenadeWeapon(weaponName) && !weaponName.Contains("knife", StringComparison.OrdinalIgnoreCase),
                    ammoAvailable: ammoClip,
                    isReloading: ammoClip <= 0,
                    attackIntent: csBot.IsEnemyVisible && bestAimError <= Config.CounterStrafeMaxAimErrorDegrees,
                    targetDistance2D: bestEnemyDist2D);

                if (csDiag.Triggered && bestEnemy != null)
                {
                    traj.Step0_Now = MicroMoveStep.FromActionId(csDiag.ReverseActionId, durationMs: csDiag.PulseDurationMs);
                    traj.Step1_125ms = MicroMoveStep.StandStill(durationMs: 110.0f);
                    traj.Step2_250ms = MicroMoveStep.StandStill(durationMs: 90.0f);
                    traj.GeneratedAtTime = currentTime;
                    traj.IsOverrideActive = true;
                    traj.ActiveBehaviorTag = "CounterStrafe";
                    traj.IntentPriority = MovementIntentSource.CounterStrafe;
                    traj.OverrideExpiresAt = currentTime + Config.CounterStrafeDurationSeconds;

                    LogDebugWithCooldown(
                        bot.Slot,
                        currentTime,
                        Config.CounterStrafeCooldownSeconds,
                        "MLMOVE - COUNTER-STRAFE",
                        $"**{bot.PlayerName}** aplicou *Velocity Zeroing* contra **{bestEnemy.PlayerName}** (`dist_2d={csDiag.TargetDistance2D:F0}u`, `aim_error={csDiag.AimErrorDegrees:F1}° <= {Config.CounterStrafeMaxAimErrorDegrees:F0}°`, `vel_before={csDiag.SpeedBefore2D:F0} u/s`, `ammo={csDiag.AmmoAvailable}`, `pulso={csDiag.PulseDurationMs:F0}ms`, `action={csDiag.ReverseActionId}`) com `{weaponName.Replace("weapon_", "")}`.");
                    continue;
                }
            }

            // =========================================================================
            // 2. MATRIZ N x N DE TRADE SPACING (Repulsão c/ Cooldown por Par e Wide Swing [250u, 400u])
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
                if (allyInFirefight && IsWithinWideSwingWindow(dist2D) && dist2D < combatAllyDist)
                {
                    combatAllyDist = dist2D;
                    combatAllyInFront = other;
                }
            }

            // 2A. Repulsão Lateral Anti-Stack com Cooldown por Par (2.5s) e Cede-Vez Único
            if (closestAlly != null && closestAllyDist < Config.TradeSpacingMinDist2D && closestAlly.PlayerPawn.Value?.AbsOrigin != null)
            {
                var allyOrigin = closestAlly.PlayerPawn.Value.AbsOrigin;
                var pairState = TryEvaluatePairRepulsion(
                    currentBotSlot: bot.Slot,
                    curX: curX,
                    curY: curY,
                    curZ: curZ,
                    currentHasC4: BotLocomotionDriver.HasC4(bot),
                    currentInCombat: csBot.IsEnemyVisible,
                    currentRole: _roleManager.GetBotRole(bot) ?? BotRole.Rotator,
                    allySlot: closestAlly.Slot,
                    allyX: allyOrigin.X,
                    allyY: allyOrigin.Y,
                    allyZ: allyOrigin.Z,
                    allyHasC4: BotLocomotionDriver.HasC4(closestAlly),
                    allyInCombat: closestAlly.PlayerPawn.Value?.Bot?.IsEnemyVisible ?? false,
                    allyRole: _roleManager.GetBotRole(closestAlly) ?? BotRole.Rotator,
                    currentTime: currentTime,
                    out int repulseAction);

                if (pairState != null && repulseAction != 0)
                {
                    traj.Step0_Now = MicroMoveStep.FromActionId(repulseAction, 95f);
                    traj.Step1_125ms = MicroMoveStep.FromActionId(repulseAction, 95f);
                    traj.Step2_250ms = MicroMoveStep.StandStill(60f);
                    traj.GeneratedAtTime = currentTime;
                    traj.IsOverrideActive = true;
                    traj.ActiveBehaviorTag = "TradeSpacing_Repulsion";
                    traj.IntentPriority = MovementIntentSource.TradeSpacing;
                    traj.SuggestedGoalOverride = pairState.OffsetTargetPosition;
                    traj.OverrideExpiresAt = currentTime + 0.19f;

                    LogDebugWithCooldown(
                        bot.Slot,
                        currentTime,
                        Config.TradeSpacingPairCooldownSeconds,
                        "MLMOVE - TRADE SPACING",
                        $"**{bot.PlayerName}** (`yielding_slot={pairState.YieldingBotSlot}`) cedeu espaço para **{closestAlly.PlayerName}** (`priority_slot={pairState.PriorityBotSlot}`) | `dist_before={pairState.DistanceBefore2D:F0}u < {Config.TradeSpacingMinDist2D:F0}u` | `shared_target={pairState.SharedTargetDetected}` | `cooldown={Config.TradeSpacingPairCooldownSeconds:F1}s` | `action={repulseAction}`.");
                    continue;
                }
            }

            // 2B. Trade Kill Window ESTRITAMENTE dentro de [WideSwingMinDist2D, WideSwingMaxDist2D] (250u-400u)
            if (combatAllyInFront != null &&
                IsWithinWideSwingWindow(combatAllyDist) &&
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
                float wideSwingAngle = baseAngleToAlly + swingOffsetRad;
                int swingDirIdx = MicroMoveStep.QuantizeAngleToDirectionIndex(wideSwingAngle);

                logits.Fill(-10.0f);
                int primaryAction = MicroMoveStep.EncodeAction(swingDirIdx, MicroSpeedTier.Run, isJump: false);
                int altAction = MicroMoveStep.EncodeAction((swingDirIdx + 1) % 16, MicroSpeedTier.Run, isJump: false);
                logits[primaryAction] = 2.2f;
                logits[altAction] = 1.1f;
                int sampledSwingAction = SampleActionFromLogits(logits, temperature: 0.85f);

                traj.Step0_Now = MicroMoveStep.FromActionId(sampledSwingAction, 125f);
                traj.Step1_125ms = MicroMoveStep.FromActionId(sampledSwingAction, 125f);
                traj.Step2_250ms = MicroMoveStep.StandStill(100f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = "TradeSpacing_WideSwing";
                traj.IntentPriority = MovementIntentSource.TradeSpacing;
                traj.OverrideExpiresAt = currentTime + 0.25f;

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    4.0f,
                    "MLMOVE - TRADE SPACING",
                    $"**{bot.PlayerName}** iniciou *Wide Swing* escalonado (`+0.6s`, Dist2D: `{combatAllyDist:F0}u` dentro da janela `[{Config.WideSwingMinDist2D:F0}u, {Config.WideSwingMaxDist2D:F0}u]`, Action `{sampledSwingAction}`) para cobrir/trocar **{combatAllyInFront.PlayerName}**!");
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
                        traj.IntentPriority = MovementIntentSource.MicroMove;
                        traj.OverrideExpiresAt = currentTime + 0.14f;
                        continue;
                    }
                }
            }

            // =========================================================================
            // 4. INFERÊNCIA DIRETA DO TRANSFORMER ONNX (Multi-Horizonte: 0ms, 125ms, 250ms)
            // =========================================================================
            if (onnxRan && (trigger == AdrenalineTriggerType.Vision_Spotted || trigger == AdrenalineTriggerType.Audio_HeardCue || trigger == AdrenalineTriggerType.Hotzone_PreMapped))
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

                if (act0 == 0 && speed2D < 25.0f)
                {
                    if (act1 != 0)
                    {
                        act0 = act1;
                    }
                    else if (act2 != 0)
                    {
                        act0 = act2;
                    }
                    else
                    {
                        int bestAct = 0;
                        float bestLogit = float.NegativeInfinity;
                        int secondAct = 0;
                        float secondLogit = float.NegativeInfinity;
                        for (int a = 0; a < ActionSpaceSize; a++)
                        {
                            float val = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 0, a];
                            if (val > bestLogit)
                            {
                                secondLogit = bestLogit;
                                secondAct = bestAct;
                                bestLogit = val;
                                bestAct = a;
                            }
                            else if (val > secondLogit)
                            {
                                secondLogit = val;
                                secondAct = a;
                            }
                        }
                        if (secondAct != 0 && (bestLogit - secondLogit) < 2.5f)
                        {
                            act0 = secondAct;
                        }
                    }
                }

                bool isTrObjective = bot.Team == CsTeam.Terrorist &&
                    (BotLocomotionDriver.HasC4(bot) ||
                     pawn.InBombZone ||
                     (Plugin?.CurrentPlan?.CurrentPhase == RoundPhase.Executing) ||
                     (Plugin?.TrPivotController?.HasPivotedThisRound == true) ||
                     (isStationary && !csBot.IsEnemyVisible));

                if (isTrObjective && trigger == AdrenalineTriggerType.Hotzone_PreMapped)
                {
                    if (act0 == 0)
                    {
                        if (act1 != 0) act0 = act1;
                        else if (act2 != 0) act0 = act2;
                        else
                        {
                            traj.IsOverrideActive = false;
                            traj.ActiveBehaviorTag = "NavMesh_TR_Advance";
                            continue;
                        }
                    }
                }

                traj.Step0_Now = MicroMoveStep.FromActionId(act0, 125f);
                traj.Step1_125ms = MicroMoveStep.FromActionId(act1, 125f);
                traj.Step2_250ms = MicroMoveStep.FromActionId(act2, 125f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = $"ONNX_{trigger}";
                traj.IntentPriority = MovementIntentSource.MicroMove;
                traj.OverrideExpiresAt = currentTime + 0.25f;

                string h0 = traj.Step0_Now.ToReadableString(botYaw);
                string h1 = traj.Step1_125ms.ToReadableString(botYaw);
                string h2 = traj.Step2_250ms.ToReadableString(botYaw);

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    3.0f,
                    "MLMOVE - ONNX 16HZ",
                    $"`[Modo ONNX Ativo]` **{bot.PlayerName}** acionou `{trigger}` em `({curX:F0}, {curY:F0}, {curZ:F0})` [Mira: Yaw {botYaw:F0}° | CPU: `{LastInferenceLatencyMs:F2}ms`] -> Horizontes: **0ms:** `{h0}` | **125ms:** `{h1}` | **250ms:** `{h2}`");
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

    public static bool IsPrecisionWeapon(string weaponDesignerName)
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
