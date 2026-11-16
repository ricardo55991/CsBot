using System.Collections.Concurrent;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Capabilities;
using CounterStrikeSharp.API.Modules.Utils;
using BotControllerApi;

namespace CsBotManager;

public enum BotOrderPriority
{
    Low_Default = 10,
    Medium_Tactical = 30,
    High_CombatFallback = 50,
    Critical_SaveOrPivot = 80,
    Absolute_PlantOrDefuse = 100
}

public class TrackedBotNavState
{
    public int Slot { get; set; }
    public TacticalSpot? TargetSpot { get; set; }
    public float TargetX { get; set; }
    public float TargetY { get; set; }
    public float TargetZ { get; set; }
    public float? LookX { get; set; }
    public float? LookY { get; set; }
    public float? LookZ { get; set; }
    public EngagementStance Stance { get; set; } = EngagementStance.PASSIVE_HOLD;
    public bool Hurry { get; set; }
    public float LastRepathTime { get; set; }
    public float StanceActionTimer { get; set; }
    public int JiggleDirection { get; set; } = 1;
    public long ActiveMovementId { get; set; }
    public bool HasReachedDestination { get; set; }
    public bool IsHoldingSpot { get; set; }
    public float HoldingSinceTime { get; set; }
    public float HoldDurationRemaining { get; set; }
    public bool ForceCrouch { get; set; }
    public BotOrderPriority Priority { get; set; } = BotOrderPriority.Medium_Tactical;
    public float LastCheckX { get; set; }
    public float LastCheckY { get; set; }
    public float LastCheckDistToTarget2D { get; set; }
    public float LastCheckTime { get; set; }
    public int StuckCount { get; set; }
    public float LastEnemyVisibleTime { get; set; }
    public float UnstuckCooldownUntil { get; set; }
    public int CommandGeneration { get; set; } = 1;
    public Guid CurrentLogicalIntentId { get; set; } = Guid.Empty;
    public string CurrentLogicalActionType { get; set; } = string.Empty;
    public int LastJiggleDirection { get; set; } = 1;
    public bool UseExactPortalSteering { get; set; }
    public IReadOnlySet<int>? ForbiddenNavAreas { get; set; }
    public int? SingleJumpPulseTick { get; set; }
    public int? SingleAttackPulseTick { get; set; }
}

public sealed class Stuck2DEvaluationResult
{
    public bool IsStuck2D { get; init; }
    public float ElapsedWindowSeconds { get; init; }
    public float Displacement2D { get; init; }
    public float TargetProgress2D { get; init; }
    public int NewStuckStage { get; init; }
    public bool ShouldBlacklistCurrentWaypoint { get; init; }
    public string ActionRecommended { get; init; } = "NONE";
}

public class BotLocomotionDriver
{
    private CsBotManagerPlugin? _plugin;
    public void SetPlugin(CsBotManagerPlugin plugin) => _plugin = plugin;

    public BotSystemConfig Config { get; set; } = BotSystemConfig.Default;
    public MovementArbitrator Arbitrator { get; } = new();
    public MovementExecutionTracker ExecutionTracker { get; } = new();
    private float _currentTickDeltaTime = 0.015625f;
    public float CurrentTickDeltaTime => _currentTickDeltaTime;
    private readonly System.Collections.Concurrent.ConcurrentDictionary<int, Guid> _lastAppliedLogicalIntentBySlot = new();
    public System.Collections.Concurrent.ConcurrentDictionary<int, Guid> LastAppliedLogicalIntentBySlot => _lastAppliedLogicalIntentBySlot;

    public void BeginMovementTick(float currentTime, int gameTick)
    {
        float fallbackDelta = 0.015625f;
        _currentTickDeltaTime = _lastTickTime > 0f
            ? Math.Clamp(currentTime - _lastTickTime, 0.001f, 0.1f)
            : fallbackDelta;
        _lastTickTime = currentTime;
    }

    public void CollectLocomotionIntents(float currentTime, int gameTick)
    {
        // Snapshot intent tracking
    }
    public C4MismatchEpisodeTracker C4MismatchTracker { get; } = new();
    private readonly System.Collections.Concurrent.ConcurrentDictionary<int, RecoveryAttempt> _activeRecoveryBySlot = new();
    public System.Collections.Concurrent.ConcurrentDictionary<int, RecoveryAttempt> ActiveRecoveryBySlot => _activeRecoveryBySlot;
    private readonly System.Collections.Concurrent.ConcurrentBag<RecoveryAttempt> _allRecoveryAttempts = new();
    public System.Collections.Generic.IEnumerable<RecoveryAttempt> AllRecoveryAttempts => _allRecoveryAttempts;
    public MatchTelemetryLogger? TelemetryLogger
    {
        get => Arbitrator.TelemetryLogger;
        set => Arbitrator.TelemetryLogger = value;
    }

    private readonly PluginCapability<IBotControllerApi> _botControllerApiCap = new("botcontroller:api");
    private readonly ConcurrentDictionary<int, TrackedBotNavState> _botStates = new();
    private readonly ConcurrentDictionary<(int Slot, string SpotId), float> _waypointBlacklistUntil = new();
    private readonly ConcurrentDictionary<(int Slot, string SpotId), int> _waypointFailureCounts = new();
    private IBotControllerApi? _cachedApi;

    private bool _isBombPlanted = false;
    private Vector? _bombPosition = null;
    private bool _isTacticalSaveActive = false;
    private float _lastTickTime = 0f;
    private readonly ConcurrentDictionary<int, float> _grenadeHoldStartTime = new();

    public SiteClearAndPlantController? PlantController { get; set; }
    public CtRetakeAndDefuseBrain? RetakeBrain { get; set; }
    public UtilityAndClockCoordinator? UtilityCoordinator { get; set; }
    public MapProfileManager? MapProfileManager { get; set; }
    public GameplaySpotTelemetryTracker? SpotTelemetryTracker { get; set; }
    public Func<int, bool>? IsOpeningCanaryActiveSlot { get; set; }
    public MovementAuthorityLeaseManager? LeaseManager { get; set; }
    public Func<int>? GetCurrentRoundId { get; set; }

    private MicroMoveEngine? _microMoveEngine;
    public MicroMoveEngine? MicroMoveEngine
    {
        get => _microMoveEngine;
        set
        {
            _microMoveEngine = value;
            if (_microMoveEngine != null)
            {
                _microMoveEngine.Arbitrator = Arbitrator;
                _microMoveEngine.Config = Config;
                _microMoveEngine.IsSlotProtectedFromOverride = s => IsOpeningCanaryActiveSlot?.Invoke(s) == true;
            }
        }
    }

    public float RoundTimeRemaining { get; set; } = 115.0f;
    public float RoundStartTime { get; set; } = 0f;
    private readonly ConcurrentDictionary<int, float> _lastHurtTime = new();

    public const ulong IN_ATTACK = 1UL << 0;
    public const ulong IN_JUMP = 1UL << 1;
    public const ulong IN_DUCK = 1UL << 2;
    public const ulong IN_FORWARD = 1UL << 3;
    public const ulong IN_BACK = 1UL << 4;
    public const ulong IN_USE = 1UL << 5;
    public const ulong IN_MOVELEFT = 1UL << 9;
    public const ulong IN_MOVERIGHT = 1UL << 10;
    public const ulong IN_SPEED = 1UL << 16;

    public IBotControllerApi? BotApi
    {
        get
        {
            if (_cachedApi != null) return _cachedApi;
            try
            {
                _cachedApi = _botControllerApiCap.Get();
            }
            catch
            {
                _cachedApi = null;
            }
            return _cachedApi;
        }
    }

    /// <summary>
    /// Avalia de forma pura e determinística se o bot está travado no plano 2D (XY),
    /// ignorando completamente oscilações verticais (Z) de pulo na mesma parede/caixa (Bug 3).
    /// </summary>
    public static Stuck2DEvaluationResult EvaluateStuck2DWindow(
        float curX,
        float curY,
        float targetX,
        float targetY,
        float checkStartX,
        float checkStartY,
        float checkStartDistToTarget2D,
        float elapsedSeconds,
        int previousStuckCount,
        BotSystemConfig? config = null)
    {
        var cfg = config ?? BotSystemConfig.Default;
        float dxMoved = curX - checkStartX;
        float dyMoved = curY - checkStartY;
        float displacement2D = MathF.Sqrt(dxMoved * dxMoved + dyMoved * dyMoved);

        float curDxTarget = targetX - curX;
        float curDyTarget = targetY - curY;
        float curDistToTarget2D = MathF.Sqrt(curDxTarget * curDxTarget + curDyTarget * curDyTarget);
        float targetProgress2D = checkStartDistToTarget2D - curDistToTarget2D;

        if (elapsedSeconds < cfg.StuckTimeWindowSeconds)
        {
            return new Stuck2DEvaluationResult
            {
                IsStuck2D = false,
                ElapsedWindowSeconds = elapsedSeconds,
                Displacement2D = displacement2D,
                TargetProgress2D = targetProgress2D,
                NewStuckStage = previousStuckCount,
                ShouldBlacklistCurrentWaypoint = false,
                ActionRecommended = "WINDOW_NOT_ELAPSED"
            };
        }

        bool isStuck = displacement2D < cfg.StuckMinDisplacement2D &&
                       targetProgress2D < cfg.StuckMinTargetProgress2D &&
                       curDistToTarget2D > 85.0f;

        if (!isStuck)
        {
            return new Stuck2DEvaluationResult
            {
                IsStuck2D = false,
                ElapsedWindowSeconds = elapsedSeconds,
                Displacement2D = displacement2D,
                TargetProgress2D = targetProgress2D,
                NewStuckStage = 0,
                ShouldBlacklistCurrentWaypoint = false,
                ActionRecommended = "MOVING_NORMALLY_2D"
            };
        }

        int newStage = previousStuckCount + 1;
        bool shouldBlacklist = newStage >= cfg.MaxWaypointFailuresBeforeEscalate;
        string action = newStage switch
        {
            1 => "STAGE1_CANCEL_MICROMOVE_AND_STRAFE_UNSTUCK",
            2 => "STAGE2_BLACKLIST_WAYPOINT_AND_SELECT_ALTERNATIVE",
            _ => "STAGE3_FALLBACK_SECTOR_REPATH"
        };

        return new Stuck2DEvaluationResult
        {
            IsStuck2D = true,
            ElapsedWindowSeconds = elapsedSeconds,
            Displacement2D = displacement2D,
            TargetProgress2D = targetProgress2D,
            NewStuckStage = newStage,
            ShouldBlacklistCurrentWaypoint = shouldBlacklist,
            ActionRecommended = action
        };
    }

    public bool IsWaypointBlacklisted(int botSlot, string? spotId, float currentTime)
    {
        if (string.IsNullOrEmpty(spotId)) return false;
        if (_waypointBlacklistUntil.TryGetValue((botSlot, spotId), out float until))
        {
            if (currentTime < until) return true;
            _waypointBlacklistUntil.TryRemove((botSlot, spotId), out _);
        }
        return false;
    }

    public void BlacklistWaypoint(int botSlot, string? spotId, float currentTime)
    {
        if (string.IsNullOrEmpty(spotId)) return;
        var key = (botSlot, spotId);
        int failures = _waypointFailureCounts.AddOrUpdate(key, 1, (_, c) => c + 1);
        float cooldown = Config.WaypointBlacklistCooldownSeconds * Math.Min(3, failures);
        _waypointBlacklistUntil[key] = currentTime + cooldown;
    }

    public static Guid EnsureLogicalActionId(TrackedBotNavState state, string actionType, bool forceNew = false)
    {
        if (forceNew || state.CurrentLogicalIntentId == Guid.Empty || !string.Equals(state.CurrentLogicalActionType, actionType, StringComparison.Ordinal))
        {
            if (state.CurrentLogicalIntentId != Guid.Empty)
            {
                state.CommandGeneration++;
            }
            state.CurrentLogicalIntentId = Guid.NewGuid();
            state.CurrentLogicalActionType = actionType;
        }
        return state.CurrentLogicalIntentId;
    }

    public static bool ShouldMonitorForStuck(
        bool isHoldingSpot,
        float holdDurationRemaining,
        EngagementStance stance,
        float dist2DToTarget,
        bool isBombPlanted,
        bool isDefusing,
        bool isPlanting,
        bool hasReachedDestination)
    {
        if (isDefusing || isPlanting) return false;
        if (hasReachedDestination && dist2DToTarget <= 85f) return false;
        if (isHoldingSpot && holdDurationRemaining > 0f && stance != EngagementStance.AGGRESSIVE_POKE) return false;
        return dist2DToTarget > 85f;
    }

    public TacticalSpot? FindAlternativeWaypointForRecovery(
        int botSlot,
        string? currentSpotId,
        string teamSide,
        string bombsite,
        float botX,
        float botY,
        float minDistanceFromCurrent,
        float currentTime)
    {
        if (MapProfileManager == null) return null;
        var candidates = MapProfileManager.GetSpotsForTeam(teamSide);
        foreach (var spot in candidates)
        {
            if (string.Equals(spot.Id, currentSpotId, StringComparison.OrdinalIgnoreCase)) continue;
            if (IsWaypointBlacklisted(botSlot, spot.Id, currentTime)) continue;
            string spotSite = PresetSpatialValidator.DetermineSpotBombsite(spot);
            if (!string.IsNullOrEmpty(bombsite) && bombsite != "None" && !string.Equals(spotSite, bombsite, StringComparison.OrdinalIgnoreCase))
                continue;
            return spot;
        }
        return null;
    }

    public RecoveryAttempt? RequestRecovery(int botSlot, long internalRoundId, string triggerReason, float currentTime, int gameTick)
    {
        if (_activeRecoveryBySlot.TryGetValue(botSlot, out var existing) && !existing.Recovered && string.IsNullOrEmpty(existing.FailureReason))
        {
            return existing;
        }
        var attempt = new RecoveryAttempt
        {
            BotSlot = botSlot,
            InternalRoundId = internalRoundId,
            TriggerReason = triggerReason,
            TriggerTime = currentTime,
            TriggerTick = gameTick,
            Stage = 1
        };
        _activeRecoveryBySlot[botSlot] = attempt;
        _allRecoveryAttempts.Add(attempt);
        return attempt;
    }

    public void NotifyBombState(bool isPlanted, Vector? bombPosition, bool isSaveActive, List<CCSPlayerController>? ctBots = null)
    {
        _isBombPlanted = isPlanted;
        _bombPosition = bombPosition;
        _isTacticalSaveActive = isSaveActive;

        if (isPlanted)
        {
            float now = Server.CurrentTime;
            int tick = Server.TickCount;

            foreach (var kvp in _botStates)
            {
                var s = kvp.Value;
                s.HoldDurationRemaining = 0f;
                s.HasReachedDestination = false;
                s.IsHoldingSpot = false;
                s.LastCheckTime = 0f;
                s.StuckCount = 0;
                Arbitrator.ClearBotState(kvp.Key, BotApi);
            }

            var allPlayers = Utilities.GetPlayers();
            foreach (var p in allPlayers)
            {
                if (p != null && p.IsValid && p.IsBot && p.PawnIsAlive)
                {
                    Arbitrator.PublishIntent(new MovementIntent
                    {
                        BotSlot = p.Slot,
                        BotName = p.PlayerName,
                        GameTick = tick,
                        CurrentTime = now,
                        Source = MovementIntentSource.RoundLifecycle,
                        Kind = MovementCommandKind.ReleaseHoldAndRepath,
                        Reason = "BombPlanted_ReleaseAllHolds",
                        ExpiresAtTime = now + 0.15f,
                        IsStopping = false,
                        ForceRepath = true
                    });
                }
            }

            if (!isSaveActive && bombPosition != null && ctBots != null)
            {
                foreach (var ct in ctBots)
                {
                    if (ct == null || !ct.IsValid || !ct.PawnIsAlive || ct.PlayerPawn.Value?.AbsOrigin == null) continue;
                    float dist = (ct.PlayerPawn.Value.AbsOrigin - bombPosition).Length();
                    if (dist > 350.0f)
                    {
                        NavigateToPosition(ct, bombPosition.X, bombPosition.Y, bombPosition.Z, hurry: true, stance: EngagementStance.AGGRESSIVE_POKE, priority: BotOrderPriority.Critical_SaveOrPivot);
                    }
                }
            }
        }
    }

    public void NotifySaveState(bool isSaveActive)
    {
        _isTacticalSaveActive = isSaveActive;
    }

    public void ResetRound()
    {
        _isBombPlanted = false;
        _bombPosition = null;
        _isTacticalSaveActive = false;
        _lastTickTime = 0f;
        _currentTickDeltaTime = 1.0f / Math.Max(1f, Config.ServerTickRate);

        foreach (var kvp in _activeRecoveryBySlot)
        {
            if (!kvp.Value.Recovered && string.IsNullOrEmpty(kvp.Value.FailureReason))
            {
                kvp.Value.FailureReason = "CancelledRoundEnd";
            }
        }
        _activeRecoveryBySlot.Clear();
        _lastAppliedLogicalIntentBySlot.Clear();

        var api = BotApi;
        Arbitrator.ResetRound(api);
        _botStates.Clear();
        _waypointBlacklistUntil.Clear();
        _waypointFailureCounts.Clear();
        _grenadeHoldStartTime.Clear();
        SpotTelemetryTracker?.OnRoundEnd();
        MicroMoveEngine?.ResetRound(api);
    }

    public void ClearNavigation(int slot)
    {
        if (_activeRecoveryBySlot.TryRemove(slot, out var rec))
        {
            if (!rec.Recovered && string.IsNullOrEmpty(rec.FailureReason))
            {
                rec.FailureReason = "CancelledBotDeath";
            }
        }
        _lastAppliedLogicalIntentBySlot.TryRemove(slot, out _);
        _botStates.TryRemove(slot, out _);
        Arbitrator.ClearBotState(slot, BotApi);
    }

    public TrackedBotNavState? GetNavState(int slot)
    {
        return _botStates.TryGetValue(slot, out var s) ? s : null;
    }

    public void NavigateToSpot(CCSPlayerController controller, TacticalSpot spot, bool hurry = false, EngagementStance? stanceOverride = null, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        if (IsOpeningCanaryActiveSlot?.Invoke(controller.Slot) == true && priority < BotOrderPriority.Critical_SaveOrPivot)
        {
            int rnd = GetCurrentRoundId?.Invoke() ?? 1;
            if (LeaseManager == null || !LeaseManager.AllowCompetingWriter(rnd, controller.Slot, Server.TickCount, "BotLocomotionDriver.NavigateToSpot", $"Spot:{spot.Id}"))
            {
                return;
            }
        }

        float now = Server.CurrentTime;
        UtilitySpotValidationOutcome? validationOutcome = null;
        if (MapProfileManager != null)
        {
            var occupied = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var kv in _botStates)
            {
                if (kv.Key != controller.Slot && kv.Value.TargetSpot != null)
                {
                    occupied.Add(kv.Value.TargetSpot.Id);
                }
            }
            var valCtx = SpotTelemetryTracker != null
                ? SpotTelemetryTracker.BuildValidationContext(controller, controller.PlayerPawn.Value?.AbsOrigin, occupied)
                : new UtilitySpotValidationContext
                {
                    MapName = "de_mirage",
                    RequestedSide = controller.Team == CsTeam.Terrorist ? "TR" : "CT",
                    OccupiedSpotIds = occupied,
                };
            validationOutcome = UtilitySpotAssignmentValidator.ValidateAndResolve(spot, valCtx, MapProfileManager.CurrentProfile.Spots);
            if (validationOutcome.ApprovedSpot != null)
            {
                spot = validationOutcome.ApprovedSpot;
            }
            else if (validationOutcome.FallbackUsed)
            {
                return; // NO_VALID_ALTERNATIVE: nunca atribuir spot inválido
            }
        }

        if (IsWaypointBlacklisted(controller.Slot, spot.Id, now) && !string.IsNullOrEmpty(spot.FallbackSpotId))
        {
            var alt = MapProfileManager?.GetSpotById(spot.FallbackSpotId);
            if (alt != null && !IsWaypointBlacklisted(controller.Slot, alt.Id, now) && MapProfileManager != null)
            {
                var altCheck = UtilitySpotAssignmentValidator.ValidateCandidate(
                    alt,
                    SpotTelemetryTracker != null
                        ? SpotTelemetryTracker.BuildValidationContext(controller, controller.PlayerPawn.Value?.AbsOrigin)
                        : new UtilitySpotValidationContext { RequestedSide = controller.Team == CsTeam.Terrorist ? "TR" : "CT" });
                if (altCheck.IsValid)
                {
                    spot = alt;
                }
            }
        }

        if (_botStates.TryGetValue(controller.Slot, out var existingState))
        {
            if (existingState.Priority > priority && (existingState.HoldDurationRemaining > 0 || !existingState.HasReachedDestination))
            {
                return;
            }
        }

        float? lookX = null;
        float? lookY = null;
        float? lookZ = null;

        if (spot.Yaw != 0 || spot.Pitch != 0)
        {
            double pitchRad = spot.Pitch * Math.PI / 180.0;
            double yawRad = spot.Yaw * Math.PI / 180.0;
            lookX = spot.X + (float)(Math.Cos(pitchRad) * Math.Cos(yawRad) * 400.0);
            lookY = spot.Y + (float)(Math.Cos(pitchRad) * Math.Sin(yawRad) * 400.0);
            lookZ = spot.Z + 64.0f + (float)(Math.Sin(-pitchRad) * 400.0);
        }

        var state = new TrackedBotNavState
        {
            Slot = controller.Slot,
            TargetSpot = spot,
            TargetX = spot.X,
            TargetY = spot.Y,
            TargetZ = spot.Z,
            LookX = lookX,
            LookY = lookY,
            LookZ = lookZ,
            Stance = stanceOverride ?? spot.RecommendedStance,
            Hurry = hurry,
            LastRepathTime = 0,
            StanceActionTimer = 0,
            JiggleDirection = 1,
            ActiveMovementId = 0,
            HasReachedDestination = false,
            HoldDurationRemaining = 0,
            ForceCrouch = spot.IsOffAngle && spot.RecommendedStance == EngagementStance.PASSIVE_HOLD,
            Priority = priority
        };

        _botStates[controller.Slot] = state;
        if (SpotTelemetryTracker != null && controller.PlayerPawn.Value?.AbsOrigin != null)
        {
            SpotTelemetryTracker.OnSpotAssigned(controller.Slot, controller, spot, controller.PlayerPawn.Value.AbsOrigin, Server.TickCount, now, validationOutcome);
        }
        PublishImmediateNavmeshIntent(controller, state);
    }

    public void NavigateToPosition(CCSPlayerController controller, float x, float y, float z, float? lookX = null, float? lookY = null, float? lookZ = null, bool hurry = false, EngagementStance stance = EngagementStance.PASSIVE_HOLD, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        if (IsOpeningCanaryActiveSlot?.Invoke(controller.Slot) == true && priority < BotOrderPriority.Critical_SaveOrPivot)
        {
            int rnd = GetCurrentRoundId?.Invoke() ?? 1;
            if (LeaseManager == null || !LeaseManager.AllowCompetingWriter(rnd, controller.Slot, Server.TickCount, "BotLocomotionDriver.NavigateToPosition", $"Pos:({x:F0},{y:F0},{z:F0})"))
            {
                return;
            }
        }

        if (_botStates.TryGetValue(controller.Slot, out var existingState))
        {
            if (existingState.Priority > priority && (existingState.HoldDurationRemaining > 0 || !existingState.HasReachedDestination))
            {
                return;
            }
        }

        var state = new TrackedBotNavState
        {
            Slot = controller.Slot,
            TargetSpot = null,
            TargetX = x,
            TargetY = y,
            TargetZ = z,
            LookX = lookX,
            LookY = lookY,
            LookZ = lookZ,
            Stance = stance,
            Hurry = hurry,
            LastRepathTime = 0,
            StanceActionTimer = 0,
            JiggleDirection = 1,
            ActiveMovementId = 0,
            HasReachedDestination = false,
            HoldDurationRemaining = 0,
            ForceCrouch = false,
            Priority = priority
        };

        _botStates[controller.Slot] = state;
        PublishImmediateNavmeshIntent(controller, state);
    }

    public void NavigateToPoint(CCSPlayerController controller, Vector point, bool hurry = false, EngagementStance stance = EngagementStance.PASSIVE_HOLD, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        NavigateToPosition(controller, point.X, point.Y, point.Z, null, null, null, hurry, stance, priority);
    }

    public void DispatchOpeningCanaryWaypoint(
        CCSPlayerController controller,
        float x, float y, float z,
        TacticalSpot? finalSpot,
        bool hurry,
        EngagementStance stance = EngagementStance.PASSIVE_HOLD)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        float? lookX = null;
        float? lookY = null;
        float? lookZ = null;
        if (finalSpot != null && (finalSpot.Yaw != 0 || finalSpot.Pitch != 0))
        {
            double pitchRad = finalSpot.Pitch * Math.PI / 180.0;
            double yawRad = finalSpot.Yaw * Math.PI / 180.0;
            lookX = finalSpot.X + (float)(Math.Cos(pitchRad) * Math.Cos(yawRad) * 400.0);
            lookY = finalSpot.Y + (float)(Math.Cos(pitchRad) * Math.Sin(yawRad) * 400.0);
            lookZ = finalSpot.Z + 64.0f + (float)(Math.Sin(-pitchRad) * 400.0);
        }

        var state = new TrackedBotNavState
        {
            Slot = controller.Slot,
            TargetSpot = finalSpot,
            TargetX = x,
            TargetY = y,
            TargetZ = z,
            LookX = lookX,
            LookY = lookY,
            LookZ = lookZ,
            Stance = stance,
            Hurry = hurry,
            LastRepathTime = 0f,
            StanceActionTimer = 0f,
            JiggleDirection = 1,
            ActiveMovementId = 0,
            HasReachedDestination = false,
            IsHoldingSpot = false,
            HoldDurationRemaining = 0f,
            ForceCrouch = false,
            Priority = BotOrderPriority.High_CombatFallback
        };
        _botStates[controller.Slot] = state;
        PublishImmediateNavmeshIntent(controller, state);
    }

    public void ConfigureCanaryTransitionState(
        int slot,
        bool hurry,
        bool forceCrouch,
        bool useExactPortalSteering,
        IReadOnlySet<int>? forbiddenAreas,
        int? singleJumpPulseTick = null,
        int? singleAttackPulseTick = null)
    {
        if (_botStates.TryGetValue(slot, out var state))
        {
            state.Hurry = hurry;
            state.ForceCrouch = forceCrouch;
            state.UseExactPortalSteering = useExactPortalSteering;
            state.ForbiddenNavAreas = forbiddenAreas;
            state.SingleJumpPulseTick = singleJumpPulseTick;
            state.SingleAttackPulseTick = singleAttackPulseTick;
        }
    }

    public void HoldOpeningCanaryForStagger(CCSPlayerController controller, float holdSeconds = 0.06f)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        var origin = controller.PlayerPawn.Value?.AbsOrigin;
        float x = origin?.X ?? 0f;
        float y = origin?.Y ?? 0f;
        float z = origin?.Z ?? 0f;
        if (!_botStates.TryGetValue(controller.Slot, out var state))
        {
            state = new TrackedBotNavState
            {
                Slot = controller.Slot,
                TargetX = x,
                TargetY = y,
                TargetZ = z,
                Priority = BotOrderPriority.High_CombatFallback
            };
            _botStates[controller.Slot] = state;
        }
        state.HoldDurationRemaining = Math.Max(state.HoldDurationRemaining, holdSeconds);
        state.IsHoldingSpot = false;
        state.HasReachedDestination = false;
        state.ForceCrouch = false;
    }

    public void HoldPosition(CCSPlayerController controller, float duration = 3.0f, bool crouch = false, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        if (IsOpeningCanaryActiveSlot?.Invoke(controller.Slot) == true && priority < BotOrderPriority.Critical_SaveOrPivot)
        {
            int rnd = GetCurrentRoundId?.Invoke() ?? 1;
            if (LeaseManager == null || !LeaseManager.AllowCompetingWriter(rnd, controller.Slot, Server.TickCount, "BotLocomotionDriver.HoldPosition", $"Hold:{duration:F1}s"))
            {
                return;
            }
        }

        if (_botStates.TryGetValue(controller.Slot, out var state))
        {
            if (state.Priority > priority && state.HoldDurationRemaining > 0)
            {
                return;
            }
            state.HoldDurationRemaining = duration;
            state.ForceCrouch = crouch;
            state.Priority = priority;
            state.IsHoldingSpot = true;
        }
        else
        {
            var pawn = controller.PlayerPawn.Value;
            if (pawn != null && pawn.AbsOrigin != null)
            {
                var curPos = pawn.AbsOrigin;
                NavigateToPosition(controller, curPos.X, curPos.Y, curPos.Z, null, null, null, false, EngagementStance.PASSIVE_HOLD, priority);
                if (_botStates.TryGetValue(controller.Slot, out var created))
                {
                    created.HoldDurationRemaining = duration;
                    created.ForceCrouch = crouch;
                    created.Priority = priority;
                    created.IsHoldingSpot = true;
                }
            }
        }

        float now = Server.CurrentTime;
        Arbitrator.PublishIntent(new MovementIntent
        {
            BotSlot = controller.Slot,
            BotName = controller.PlayerName,
            GameTick = Server.TickCount,
            CurrentTime = now,
            Source = priority >= BotOrderPriority.High_CombatFallback
                ? MovementIntentSource.EmergencyFallback
                : MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.HoldStop,
            Reason = $"HoldPosition({duration:F1}s,crouch={crouch})",
            ExpiresAtTime = now + Math.Min(duration, 0.25f),
            IsStopping = true,
            WaitDurationSeconds = duration,
            Buttons = crouch ? IN_DUCK : 0UL,
            ButtonsDurationMs = (int)Math.Clamp(duration * 1000f, 150f, 800f)
        });
    }

    private void PublishImmediateNavmeshIntent(CCSPlayerController controller, TrackedBotNavState state)
    {
        float now = Server.CurrentTime;
        var source = state.Priority switch
        {
            >= BotOrderPriority.Absolute_PlantOrDefuse => MovementIntentSource.BombObjective,
            >= BotOrderPriority.Critical_SaveOrPivot => MovementIntentSource.EmergencyFallback,
            _ => MovementIntentSource.TacticalNavigation
        };

        bool isCanary = IsOpeningCanaryActiveSlot?.Invoke(controller.Slot) == true;
        Arbitrator.PublishIntent(new MovementIntent
        {
            BotSlot = controller.Slot,
            BotName = controller.PlayerName,
            GameTick = Server.TickCount,
            CurrentTime = now,
            Source = source,
            Kind = MovementCommandKind.NavigateNavMesh,
            Reason = isCanary ? $"OpeningCanaryImmediate({state.TargetSpot?.Id ?? "Waypoint"})" : $"NavigateImmediate({state.TargetSpot?.Id ?? "Pos"})",
            ExpiresAtTime = now + 0.15f,
            GoalX = state.TargetX,
            GoalY = state.TargetY,
            GoalZ = state.TargetZ,
            ForceRepath = true,
            IsStopping = false,
            Hurry = state.Hurry,
            Sneak = !state.Hurry && state.Stance == EngagementStance.AGGRESSIVE_POKE
        });
    }

    public static bool HasC4(CCSPlayerController controller)
    {
        var pawn = controller.PlayerPawn.Value;
        if (pawn?.WeaponServices?.MyWeapons == null) return false;
        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w != null && w.IsValid && !string.IsNullOrEmpty(w.DesignerName) && w.DesignerName.Contains("c4", StringComparison.OrdinalIgnoreCase))
                return true;
        }
        return false;
    }

    public void UpdateTick(float currentTime)
    {
        var api = BotApi;
        int gameTick = Server.TickCount;
        float dt = _lastTickTime > 0f ? Math.Clamp(currentTime - _lastTickTime, 0.001f, 0.1f) : 0.015625f;
        _lastTickTime = currentTime;

        if (Arbitrator.CurrentPhase != ArbitrationWindowPhase.Collecting)
        {
            Arbitrator.BeginTick(gameTick, currentTime);
        }

        // Etapa A: Coleta intenções do MicroMoveEngine (16Hz / 64Hz interpolation)
        if (_plugin?.IsSpotTestActive != true)
        {
            MicroMoveEngine?.UpdateTick(currentTime, RoundTimeRemaining, _isBombPlanted, _botStates, api);
        }

        // Etapa B: Avalia estado de navegação, objetivos de C4 e Stuck 2D de cada bot e publica intenções no Arbitrator
        foreach (var kvp in _botStates)
        {
            int slot = kvp.Key;
            var state = kvp.Value;

            var controller = Utilities.GetPlayerFromSlot(slot);
            if (controller == null || !controller.IsValid || !controller.PawnIsAlive)
            {
                ClearNavigation(slot);
                continue;
            }

            var pawn = controller.PlayerPawn.Value;
            var bot = pawn?.Bot;
            if (pawn == null || bot == null || pawn.AbsOrigin == null) continue;

            float curX = pawn.AbsOrigin.X;
            float curY = pawn.AbsOrigin.Y;
            float curZ = pawn.AbsOrigin.Z;

            // Watchdog de granada na mão
            var activeWp = pawn.WeaponServices?.ActiveWeapon.Value;
            string currentWpName = activeWp?.DesignerName ?? "";
            if (IsGrenadeWeapon(currentWpName))
            {
                if (!_grenadeHoldStartTime.TryGetValue(slot, out float gStart))
                {
                    _grenadeHoldStartTime[slot] = currentTime;
                }
                else if ((currentTime - gStart) >= 2.2f || bot.IsEnemyVisible)
                {
                    ForceSwitchToBestCombatWeapon(controller);
                    _grenadeHoldStartTime.TryRemove(slot, out _);
                }
            }
            else
            {
                _grenadeHoldStartTime.TryRemove(slot, out _);
            }

            // =========================================================================
            // 1. PRIORIDADE MÁXIMA DE OBJETIVO - C4 PLANT (TR) & C4 DEFUSE/SAVE (CT)
            // =========================================================================
            bool objectivePublished = false;
            if (_plugin?.IsSpotTestActive == true)
            {
                // Isola o teste A/B de spot contra lógica de C4/Plant/Save
            }
            else if (controller.Team == CsTeam.Terrorist && HasC4(controller))
            {
                bool isNearSiteOrPlanting = false;
                try { isNearSiteOrPlanting = pawn.InBombZone; } catch { }

                if (isNearSiteOrPlanting)
                {
                    var allPlayers = Utilities.GetPlayers();
                    bool isAuthorized = PlantController == null || PlantController.IsSiteSafeToPlant(controller, RoundTimeRemaining, allPlayers);

                    if (isAuthorized)
                    {
                        if (PlantController != null && !PlantController.HasAnnouncedPlant)
                        {
                            int aliveTrs = allPlayers.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.Terrorist);
                            int aliveCts = allPlayers.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist);
                            PlantController.AnnounceAndStartPlant(controller, "A", aliveTrs, aliveCts);
                        }

                        Arbitrator.PublishIntent(new MovementIntent
                        {
                            BotSlot = slot,
                            BotName = controller.PlayerName,
                            GameTick = gameTick,
                            CurrentTime = currentTime,
                            Source = MovementIntentSource.BombObjective,
                            Kind = MovementCommandKind.ReleaseHoldAndRepath,
                            Reason = "C4Carrier_InBombZone_AuthorizedToPlant",
                            ExpiresAtTime = currentTime + 0.10f,
                            IsStopping = false
                        });
                        objectivePublished = true;
                    }
                }
                else
                {
                    bool isExecuting = _plugin?.PacingController?.IsExecuting == true || _plugin?.CurrentPlan?.CurrentPhase == RoundPhase.Executing;
                    if (isExecuting || RoundTimeRemaining <= 45.0f)
                    {
                        string targetSite = (_plugin?.CurrentPlan?.TacticName ?? "").Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
                        var plantCoord = targetSite == "B" ? new Vector(-1190.0f, -150.0f, -165.0f) : new Vector(-1160.0f, -2450.0f, -168.0f);
                        float plantDist = (plantCoord - pawn.AbsOrigin).Length();
                        if (plantDist > 120.0f)
                        {
                            state.TargetX = plantCoord.X;
                            state.TargetY = plantCoord.Y;
                            state.TargetZ = plantCoord.Z;
                            state.Hurry = true;
                            state.Priority = BotOrderPriority.Absolute_PlantOrDefuse;
                            Arbitrator.PublishIntent(new MovementIntent
                            {
                                BotSlot = slot,
                                BotName = controller.PlayerName,
                                GameTick = gameTick,
                                CurrentTime = currentTime,
                                Source = MovementIntentSource.BombObjective,
                                Kind = MovementCommandKind.NavigateNavMesh,
                                Reason = $"C4Carrier_AdvanceToSite_{targetSite}",
                                ExpiresAtTime = currentTime + 0.15f,
                                GoalX = plantCoord.X,
                                GoalY = plantCoord.Y,
                                GoalZ = plantCoord.Z,
                                Hurry = true,
                                IsStopping = false
                            });
                            objectivePublished = true;
                        }
                    }
                }
            }
            else if (controller.Team == CsTeam.CounterTerrorist)
            {
                if (_isTacticalSaveActive)
                {
                    bool isDefusing = false;
                    try { isDefusing = pawn.IsDefusing; } catch { }
                    if (isDefusing) controller.ExecuteClientCommand("-use; slot1");

                    Arbitrator.PublishIntent(new MovementIntent
                    {
                        BotSlot = slot,
                        BotName = controller.PlayerName,
                        GameTick = gameTick,
                        CurrentTime = currentTime,
                        Source = MovementIntentSource.EmergencyFallback,
                        Kind = MovementCommandKind.HoldStop,
                        Reason = "CT_TacticalSave_Hold",
                        ExpiresAtTime = currentTime + 0.25f,
                        IsStopping = true,
                        WaitDurationSeconds = 0.8f
                    });
                    objectivePublished = true;
                }
                else if (_isBombPlanted)
                {
                    bool isDefusing = false;
                    try { isDefusing = pawn.IsDefusing; } catch { }

                    float distToBombSq = float.MaxValue;
                    if (_bombPosition != null)
                    {
                        float bx = curX - _bombPosition.X;
                        float by = curY - _bombPosition.Y;
                        float bz = curZ - _bombPosition.Z;
                        distToBombSq = (bx * bx) + (by * by) + (bz * bz);
                    }

                    if (isDefusing || distToBombSq <= (220.0f * 220.0f))
                    {
                        var allPlayers = Utilities.GetPlayers();
                        int aliveTrs = allPlayers.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.Terrorist);
                        var ctBots = allPlayers.Where(p => p != null && p.IsValid && p.IsBot && p.Team == CsTeam.CounterTerrorist).ToList();
                        ulong defuseButtons = 0UL;

                        if (RetakeBrain != null && _bombPosition != null)
                        {
                            float bombTimeRemaining = GetBombTimeRemaining();
                            RetakeBrain.TryDeploySmokeOnC4(controller, _bombPosition, bombTimeRemaining, ctBots);
                            if (!CtRetakeAndDefuseBrain.HasDefuser(controller))
                            {
                                RetakeBrain.CheckAndEnforceSmartDefusePriority(controller, _bombPosition, ctBots);
                            }
                            if (isDefusing && RetakeBrain.CurrentDefuseAction == DefuseAction.NormalStick)
                            {
                                RetakeBrain.OnDefuseTapped(controller, _bombPosition, bombTimeRemaining, aliveTrs);
                            }
                            if (RetakeBrain.ShouldInjectDefuseInput(controller))
                            {
                                defuseButtons = IN_USE;
                            }
                        }
                        else
                        {
                            defuseButtons = IN_USE;
                        }

                        Arbitrator.PublishIntent(new MovementIntent
                        {
                            BotSlot = slot,
                            BotName = controller.PlayerName,
                            GameTick = gameTick,
                            CurrentTime = currentTime,
                            Source = MovementIntentSource.BombObjective,
                            Kind = MovementCommandKind.NavigateNavMesh,
                            Reason = "CT_DefuseObjective",
                            ExpiresAtTime = currentTime + 0.15f,
                            GoalX = _bombPosition?.X ?? curX,
                            GoalY = _bombPosition?.Y ?? curY,
                            GoalZ = _bombPosition?.Z ?? curZ,
                            IsStopping = false,
                            Buttons = defuseButtons,
                            ButtonsDurationMs = 300
                        });
                        objectivePublished = true;
                    }
                }
            }

            // =========================================================================
            // 2. DETECTOR DE STUCK 2D CONTÍNUO (Bug 3: NUNCA é silenciado pelo MicroMove/ONNX!)
            // =========================================================================
            float dxTarget = state.TargetX - curX;
            float dyTarget = state.TargetY - curY;
            float dzTarget = state.TargetZ - curZ;
            float dist2DToTarget = MathF.Sqrt(dxTarget * dxTarget + dyTarget * dyTarget);
            float distSq3D = (dxTarget * dxTarget) + (dyTarget * dyTarget) + (dzTarget * dzTarget);

            // Se TradeSpacing sugeriu um offset lateral no NavMesh, aplica ao destino tático do bot
            bool isCanarySlot = IsOpeningCanaryActiveSlot?.Invoke(slot) == true;
            var microTraj = MicroMoveEngine?.GetTrajectory(slot);
            if (!isCanarySlot && _plugin?.IsSpotTestActive != true && microTraj != null && microTraj.IsOverrideActive && microTraj.SuggestedGoalOverride != null)
            {
                state.TargetX = microTraj.SuggestedGoalOverride.X;
                state.TargetY = microTraj.SuggestedGoalOverride.Y;
                state.TargetZ = microTraj.SuggestedGoalOverride.Z;
            }

            bool isIntendingToMove = !isCanarySlot && !state.IsHoldingSpot && state.HoldDurationRemaining <= 0f && dist2DToTarget > 85.0f;
            if (isIntendingToMove)
            {
                if (state.LastCheckTime <= 0f)
                {
                    state.LastCheckX = curX;
                    state.LastCheckY = curY;
                    state.LastCheckDistToTarget2D = dist2DToTarget;
                    state.LastCheckTime = currentTime;
                }
                else
                {
                    float elapsedCheck = currentTime - state.LastCheckTime;
                    if (elapsedCheck >= Config.StuckTimeWindowSeconds)
                    {
                        var stuckEval = EvaluateStuck2DWindow(
                            curX: curX,
                            curY: curY,
                            targetX: state.TargetX,
                            targetY: state.TargetY,
                            checkStartX: state.LastCheckX,
                            checkStartY: state.LastCheckY,
                            checkStartDistToTarget2D: state.LastCheckDistToTarget2D,
                            elapsedSeconds: elapsedCheck,
                            previousStuckCount: state.StuckCount,
                            config: Config);

                        state.LastCheckX = curX;
                        state.LastCheckY = curY;
                        state.LastCheckDistToTarget2D = dist2DToTarget;
                        state.LastCheckTime = currentTime;
                        state.StuckCount = stuckEval.NewStuckStage;

                        if (stuckEval.IsStuck2D)
                        {
                            // Cancela imediatamente qualquer override do MicroMove/ONNX que esteja prendendo o bot
                            if (microTraj != null)
                            {
                                microTraj.IsOverrideActive = false;
                            }

                            string oldSpotId = state.TargetSpot?.Id ?? $"({state.TargetX:F0},{state.TargetY:F0})";
                            string newSpotId = oldSpotId;

                            if (_plugin?.IsSpotTestActive != true && stuckEval.ShouldBlacklistCurrentWaypoint && state.TargetSpot != null)
                            {
                                BlacklistWaypoint(slot, state.TargetSpot.Id, currentTime);
                                TacticalSpot? replacementSpot = null;
                                UtilitySpotValidationOutcome? repOutcome = null;
                                if (MapProfileManager != null)
                                {
                                    var occupied = _botStates.Where(kv => kv.Key != slot && kv.Value.TargetSpot != null).Select(kv => kv.Value.TargetSpot!.Id).ToHashSet(StringComparer.OrdinalIgnoreCase);
                                    var bl = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { state.TargetSpot.Id };
                                    var valCtx = SpotTelemetryTracker != null
                                        ? SpotTelemetryTracker.BuildValidationContext(controller, pawn.AbsOrigin, occupied, bl)
                                        : new UtilitySpotValidationContext { RequestedSide = controller.Team == CsTeam.Terrorist ? "TR" : "CT", OccupiedSpotIds = occupied, BlacklistedSpotIds = bl };
                                    var requestedForRep = !string.IsNullOrEmpty(state.TargetSpot.FallbackSpotId)
                                        ? MapProfileManager.GetSpotById(state.TargetSpot.FallbackSpotId) ?? state.TargetSpot
                                        : state.TargetSpot;
                                    repOutcome = UtilitySpotAssignmentValidator.ValidateAndResolve(requestedForRep, valCtx, MapProfileManager.CurrentProfile.Spots);
                                    if (repOutcome.ApprovedSpot != null && !IsWaypointBlacklisted(slot, repOutcome.ApprovedSpot.Id, currentTime))
                                    {
                                        replacementSpot = repOutcome.ApprovedSpot;
                                    }
                                }

                                if (replacementSpot != null)
                                {
                                    state.TargetSpot = replacementSpot;
                                    state.TargetX = replacementSpot.X;
                                    state.TargetY = replacementSpot.Y;
                                    state.TargetZ = replacementSpot.Z;
                                    newSpotId = replacementSpot.Id;
                                    if (SpotTelemetryTracker != null && pawn.AbsOrigin != null)
                                    {
                                        SpotTelemetryTracker.OnSpotReplaced(slot, controller, replacementSpot, pawn.AbsOrigin, gameTick, currentTime, "Stuck2DBlacklist", repOutcome);
                                    }
                                }
                            }

                            float strafeSpeed = (state.StuckCount % 2 == 0) ? 220f : -220f;
                            state.UnstuckCooldownUntil = currentTime + 0.65f;
                            if (SpotTelemetryTracker != null && pawn.AbsOrigin != null)
                            {
                                SpotTelemetryTracker.OnSpotRecovery(slot, controller, pawn.AbsOrigin, gameTick, currentTime);
                            }

                            TelemetryLogger?.LogEvent(
                                "UNSTUCK - 2D RECOVERY",
                                $"**{controller.PlayerName}** (`slot={slot}`) detectado em **Stuck 2D** após `{stuckEval.ElapsedWindowSeconds:F1}s` (`deslocamento_2d={stuckEval.Displacement2D:F1}u < {Config.StuckMinDisplacement2D:F0}u`, `progresso_alvo={stuckEval.TargetProgress2D:F1}u`) em `({curX:F0}, {curY:F0}, {curZ:F0})` | Estágio=`{stuckEval.NewStuckStage}` (`{stuckEval.ActionRecommended}`) | Waypoint: `{oldSpotId}` -> `{newSpotId}`.");

                            Arbitrator.PublishIntent(new MovementIntent
                            {
                                BotSlot = slot,
                                BotName = controller.PlayerName,
                                GameTick = gameTick,
                                CurrentTime = currentTime,
                                Source = MovementIntentSource.Unstuck,
                                Kind = MovementCommandKind.UsercmdVector,
                                Reason = stuckEval.ActionRecommended,
                                ExpiresAtTime = currentTime + 0.45f,
                                UseUsercmdVelocity = true,
                                ForwardMove = 140f,
                                SideMove = strafeSpeed,
                                Buttons = IN_JUMP | IN_FORWARD,
                                ButtonsDurationMs = 220,
                                GoalX = state.TargetX,
                                GoalY = state.TargetY,
                                GoalZ = state.TargetZ,
                                ForceRepath = true,
                                Hurry = true,
                                IsStopping = false
                            });
                        }
                    }
                }
            }
            else
            {
                state.LastCheckTime = 0f;
            }

            if (objectivePublished)
            {
                continue;
            }

            // =========================================================================
            // 3. HOLD EXPLICITO COM TETO DE DURAÇÃO
            // =========================================================================
            if (state.HoldDurationRemaining > 0f)
            {
                state.HoldDurationRemaining = Math.Max(0f, state.HoldDurationRemaining - dt);
                Arbitrator.PublishIntent(new MovementIntent
                {
                    BotSlot = slot,
                    BotName = controller.PlayerName,
                    GameTick = gameTick,
                    CurrentTime = currentTime,
                    Source = state.Priority >= BotOrderPriority.High_CombatFallback
                        ? MovementIntentSource.EmergencyFallback
                        : MovementIntentSource.TacticalNavigation,
                    Kind = MovementCommandKind.HoldStop,
                    Reason = $"TimedHold({state.HoldDurationRemaining:F1}s)",
                    ExpiresAtTime = currentTime + 0.10f,
                    IsStopping = true,
                    WaitDurationSeconds = state.HoldDurationRemaining,
                    Buttons = state.ForceCrouch ? IN_DUCK : 0UL,
                    ButtonsDurationMs = 200
                });
                continue;
            }

            // =========================================================================
            // 4. URGÊNCIA CRÍTICA DE FIM DE ROUND (<= 45s TR / RETAKE CT)
            // =========================================================================
            if (_plugin?.IsSpotTestActive != true && controller.Team == CsTeam.Terrorist && RoundTimeRemaining <= 45.0f && !_isBombPlanted)
            {
                if (state.TargetSpot != null && SpotTelemetryTracker != null && pawn.AbsOrigin != null)
                {
                    SpotTelemetryTracker.OnSpotAbandoned(slot, controller, pawn.AbsOrigin, gameTick, currentTime, "TimePressureFallback");
                }
                state.IsHoldingSpot = false;
                state.HasReachedDestination = false;
                state.HoldingSinceTime = 0f;

                Vector? targetSitePos = null;
                var allPls = Utilities.GetPlayers();
                var c4Holder = allPls.FirstOrDefault(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.Terrorist && HasC4(p));
                if (c4Holder != null && c4Holder.Slot != controller.Slot && c4Holder.PlayerPawn.Value?.AbsOrigin != null)
                {
                    targetSitePos = c4Holder.PlayerPawn.Value.AbsOrigin;
                }
                else
                {
                    string targetSite = (_plugin?.CurrentPlan?.TacticName ?? "").Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
                    targetSitePos = targetSite == "B" ? new Vector(-1190.0f, -150.0f, -165.0f) : new Vector(-1160.0f, -2450.0f, -168.0f);
                }

                if (targetSitePos != null && pawn.AbsOrigin != null && (targetSitePos - pawn.AbsOrigin).Length() > 150f)
                {
                    state.TargetX = targetSitePos.X;
                    state.TargetY = targetSitePos.Y;
                    state.TargetZ = targetSitePos.Z;
                    state.Hurry = true;
                    state.Priority = BotOrderPriority.Critical_SaveOrPivot;
                }
            }

            if (controller.Team == CsTeam.CounterTerrorist && _isBombPlanted && !_isTacticalSaveActive)
            {
                Vector? bombPos = _bombPosition;
                if (bombPos == null)
                {
                    var pC4 = Utilities.FindAllEntitiesByDesignerName<CPlantedC4>("planted_c4").FirstOrDefault(c => c.IsValid && c.AbsOrigin != null);
                    if (pC4 != null) bombPos = pC4.AbsOrigin;
                }

                if (bombPos != null && pawn.AbsOrigin != null && (bombPos - pawn.AbsOrigin).Length() > 350.0f)
                {
                    state.IsHoldingSpot = false;
                    state.HasReachedDestination = false;
                    state.HoldingSinceTime = 0f;
                    state.TargetX = bombPos.X;
                    state.TargetY = bombPos.Y;
                    state.TargetZ = bombPos.Z;
                    state.Hurry = true;
                    state.Priority = BotOrderPriority.Critical_SaveOrPivot;
                }
            }

            // Expiração rigorosa de IsHoldingSpot APENAS para Terroristas (CTs mantêm o ângulo no spot até rotação/retake!)
            if (_plugin?.IsSpotTestActive != true && state.IsHoldingSpot && controller.Team == CsTeam.Terrorist && !_isBombPlanted)
            {
                float holdDuration = currentTime - state.HoldingSinceTime;
                float maxHoldTime = (!bot.IsEnemyVisible || state.Stance == EngagementStance.AGGRESSIVE_POKE)
                    ? Config.StandStillMaxDefensiveSeconds
                    : 12.0f;

                if (state.HoldingSinceTime > 0f && holdDuration >= maxHoldTime)
                {
                    if (SpotTelemetryTracker != null && pawn.AbsOrigin != null)
                    {
                        SpotTelemetryTracker.OnSpotHoldEnded(slot, controller, pawn.AbsOrigin, gameTick, currentTime, "TrHoldTimeout");
                    }
                    state.IsHoldingSpot = false;
                    state.HasReachedDestination = false;
                    state.HoldingSinceTime = 0f;

                    string targetSite = (_plugin?.CurrentPlan?.TacticName ?? "").Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
                    Vector nextTarget = targetSite == "B" ? new Vector(-1190.0f, -150.0f, -165.0f) : new Vector(-1160.0f, -2450.0f, -168.0f);
                    state.TargetX = nextTarget.X;
                    state.TargetY = nextTarget.Y;
                    state.TargetZ = nextTarget.Z;
                    state.Hurry = true;
                }
            }

            // =========================================================================
            // 5. INTENÇÃO DE NAVEGAÇÃO TÁTICA (EM TRÂNSITO vs. NO SPOT)
            // =========================================================================
            if (isCanarySlot || distSq3D > (85.0f * 85.0f))
            {
                state.HasReachedDestination = false;
                state.IsHoldingSpot = false;

                float? lookX = null;
                float? lookY = null;
                float? lookZ = null;
                bool clearLook = false;

                if (isCanarySlot)
                {
                    float steerX = state.TargetX;
                    float steerY = state.TargetY;
                    float steerZ = state.TargetZ;
                    var navGraph = NavMeshGraph.Default;
                    if (!state.UseExactPortalSteering && navGraph != null)
                    {
                        (steerX, steerY, steerZ) = navGraph.GetNextSteerTarget(
                            curX, curY, curZ,
                            state.TargetX, state.TargetY, state.TargetZ,
                            minLookaheadUnits: 42f,
                            forbiddenAreas: state.ForbiddenNavAreas);
                    }
                    lookX = steerX;
                    lookY = steerY;
                    lookZ = curZ + 62.0f;
                    clearLook = false;
                }
                else if (bot.IsEnemyVisible)
                {
                    state.LastEnemyVisibleTime = currentTime;
                }
                else if (currentTime - state.LastEnemyVisibleTime > 1.5f)
                {
                    clearLook = true;
                    if (pawn.AbsVelocity != null && pawn.AbsVelocity.Length() > 100.0f)
                    {
                        lookX = curX + pawn.AbsVelocity.X;
                        lookY = curY + pawn.AbsVelocity.Y;
                        lookZ = curZ + 64.0f;
                        clearLook = false;
                    }
                }

                bool shouldRepath = false;
                float repathInterval = isCanarySlot ? 0.35f : 1.2f;
                if (currentTime - state.LastRepathTime > repathInterval)
                {
                    shouldRepath = true;
                    state.LastRepathTime = currentTime;
                    if (SpotTelemetryTracker != null && pawn.AbsOrigin != null)
                    {
                        SpotTelemetryTracker.OnSpotRepath(slot, controller, pawn.AbsOrigin, gameTick, currentTime);
                    }
                }

                float intentGoalX = state.TargetX;
                float intentGoalY = state.TargetY;
                float intentGoalZ = state.TargetZ;

                if (isCanarySlot)
                {
                    var navGraph = NavMeshGraph.Default;
                    if (!state.UseExactPortalSteering && navGraph != null)
                    {
                        (intentGoalX, intentGoalY, intentGoalZ) = navGraph.GetNextSteerTarget(
                            curX, curY, curZ,
                            state.TargetX, state.TargetY, state.TargetZ,
                            minLookaheadUnits: 42f,
                            forbiddenAreas: state.ForbiddenNavAreas);
                    }
                    float[] moveToGoal = NativeCcsBotLocomotionBridge.GetMoveToGoal(bot.Handle, bot);
                    bool goalDrifted = MathF.Abs(moveToGoal[0] - intentGoalX) > 15.0f
                        || MathF.Abs(moveToGoal[1] - intentGoalY) > 15.0f;
                    if (goalDrifted)
                    {
                        shouldRepath = true;
                    }
                }

                bool emitJumpNow = isCanarySlot && state.SingleJumpPulseTick.HasValue && state.SingleJumpPulseTick.Value == gameTick;
                bool emitAttackNow = isCanarySlot && state.SingleAttackPulseTick.HasValue && state.SingleAttackPulseTick.Value == gameTick;
                ulong canaryButtons = IN_FORWARD;
                if (state.ForceCrouch)
                {
                    canaryButtons |= IN_DUCK;
                }
                if (emitJumpNow)
                {
                    canaryButtons |= 0x2UL;
                    state.SingleJumpPulseTick = null;
                }
                if (emitAttackNow)
                {
                    canaryButtons |= 0x1UL;
                    state.SingleAttackPulseTick = null;
                }

                string canaryReason = emitJumpNow
                    ? $"OpeningCanaryTransit({state.TargetSpot?.Id ?? "Waypoint"})|TransitionStepUpJumpPulse"
                    : $"OpeningCanaryTransit({state.TargetSpot?.Id ?? "Waypoint"})";

                Arbitrator.PublishIntent(new MovementIntent
                {
                    BotSlot = slot,
                    BotName = controller.PlayerName,
                    GameTick = gameTick,
                    CurrentTime = currentTime,
                    Source = state.Priority >= BotOrderPriority.Critical_SaveOrPivot
                        ? MovementIntentSource.EmergencyFallback
                        : MovementIntentSource.TacticalNavigation,
                    Kind = MovementCommandKind.NavigateNavMesh,
                    Reason = isCanarySlot ? canaryReason : $"TransitTo({state.TargetSpot?.Id ?? "Target"})",
                    ExpiresAtTime = currentTime + 0.08f,
                    GoalX = intentGoalX,
                    GoalY = intentGoalY,
                    GoalZ = intentGoalZ,
                    ForceRepath = shouldRepath,
                    IsStopping = false,
                    Hurry = state.Hurry,
                    Sneak = !state.Hurry && state.Stance == EngagementStance.AGGRESSIVE_POKE,
                    Buttons = isCanarySlot ? canaryButtons : 0UL,
                    ButtonsDurationMs = isCanarySlot ? 64 : 0,
                    LookX = lookX,
                    LookY = lookY,
                    LookZ = lookZ,
                    LookDuration = 0.25f,
                    LookTolerance = isCanarySlot ? 1.5f : 3.0f,
                    ClearLookIfClose = clearLook
                });
            }
            else
            {
                state.HasReachedDestination = true;
                if (!state.IsHoldingSpot)
                {
                    state.IsHoldingSpot = true;
                    state.HoldingSinceTime = currentTime;
                    if (SpotTelemetryTracker != null && pawn.AbsOrigin != null)
                    {
                        SpotTelemetryTracker.OnSpotReached(slot, controller, pawn.AbsOrigin, gameTick, currentTime);
                    }
                }
                state.LastCheckTime = 0f;
                state.StuckCount = 0;

                float? lookX = (!bot.IsEnemyVisible && state.LookX.HasValue) ? state.LookX : null;
                float? lookY = (!bot.IsEnemyVisible && state.LookY.HasValue) ? state.LookY : null;
                float? lookZ = (!bot.IsEnemyVisible && state.LookZ.HasValue) ? state.LookZ : null;

                switch (state.Stance)
                {
                    case EngagementStance.PASSIVE_HOLD:
                    case EngagementStance.ONE_AND_DONE:
                        Arbitrator.PublishIntent(new MovementIntent
                        {
                            BotSlot = slot,
                            BotName = controller.PlayerName,
                            GameTick = gameTick,
                            CurrentTime = currentTime,
                            Source = MovementIntentSource.TacticalNavigation,
                            Kind = MovementCommandKind.HoldStop,
                            Reason = $"SpotHold_{state.Stance}",
                            ExpiresAtTime = currentTime + 0.10f,
                            GoalX = curX,
                            GoalY = curY,
                            GoalZ = curZ,
                            IsStopping = true,
                            WaitDurationSeconds = 1.5f,
                            Buttons = state.ForceCrouch ? IN_DUCK : 0UL,
                            ButtonsDurationMs = 200,
                            LookX = lookX,
                            LookY = lookY,
                            LookZ = lookZ,
                            LookDuration = 1.5f
                        });
                        break;

                    case EngagementStance.JIGGLE_INFO:
                        if (currentTime - state.StanceActionTimer > 0.35f)
                        {
                            state.JiggleDirection = -state.JiggleDirection;
                            state.StanceActionTimer = currentTime;
                        }
                        Arbitrator.PublishIntent(new MovementIntent
                        {
                            BotSlot = slot,
                            BotName = controller.PlayerName,
                            GameTick = gameTick,
                            CurrentTime = currentTime,
                            Source = MovementIntentSource.TacticalNavigation,
                            Kind = MovementCommandKind.UsercmdVector,
                            Reason = "SpotJiggleInfo",
                            ExpiresAtTime = currentTime + 0.12f,
                            GoalX = curX,
                            GoalY = curY,
                            GoalZ = curZ,
                            UseUsercmdVelocity = true,
                            ForwardMove = 0f,
                            SideMove = state.JiggleDirection * 220f,
                            IsStopping = false,
                            LookX = lookX,
                            LookY = lookY,
                            LookZ = lookZ,
                            LookDuration = 1.0f
                        });
                        break;

                    case EngagementStance.AGGRESSIVE_POKE:
                        Arbitrator.PublishIntent(new MovementIntent
                        {
                            BotSlot = slot,
                            BotName = controller.PlayerName,
                            GameTick = gameTick,
                            CurrentTime = currentTime,
                            Source = MovementIntentSource.TacticalNavigation,
                            Kind = MovementCommandKind.NavigateNavMesh,
                            Reason = "SpotAggressivePoke",
                            ExpiresAtTime = currentTime + 0.10f,
                            GoalX = curX,
                            GoalY = curY,
                            GoalZ = curZ,
                            IsStopping = false,
                            Sneak = true,
                            LookX = lookX,
                            LookY = lookY,
                            LookZ = lookZ,
                            LookDuration = 1.0f
                        });
                        break;
                }
            }
        }

        // Etapa C (Única Autoridade Final - Regra 3 e 4): Resolve e aplica exatamente 1 decisão por bot e por tick
        foreach (var kvp in _botStates)
        {
            int slot = kvp.Key;
            var controller = Utilities.GetPlayerFromSlot(slot);
            var decision = Arbitrator.CollectAndResolveIntents(slot, gameTick, currentTime);
            if (decision != null)
            {
                Arbitrator.ApplyWinningIntent(decision, controller, api);
            }
        }
        Arbitrator.EndTick();
    }

    public void AlertNearbyTeammatesOfThreat(Vector threatPos, int victimSlot, CsTeam team, float radius = 950f)
    {
        float now = Server.CurrentTime;
        int tick = Server.TickCount;
        var allPlayers = Utilities.GetPlayers();
        foreach (var p in allPlayers)
        {
            if (p == null || !p.IsValid || !p.IsBot || !p.PawnIsAlive || p.Team != team || p.Slot == victimSlot) continue;
            var pawn = p.PlayerPawn.Value;
            if (pawn?.AbsOrigin == null) continue;

            float dist = (pawn.AbsOrigin - threatPos).Length();
            if (dist <= radius)
            {
                if (_botStates.TryGetValue(p.Slot, out var state))
                {
                    state.LookX = threatPos.X;
                    state.LookY = threatPos.Y;
                    state.LookZ = threatPos.Z + 64.0f;
                    state.TargetX = threatPos.X;
                    state.TargetY = threatPos.Y;
                    state.TargetZ = threatPos.Z;
                    state.Stance = EngagementStance.AGGRESSIVE_POKE;
                    state.HoldDurationRemaining = 0f;
                    state.Hurry = true;
                }

                Arbitrator.PublishIntent(new MovementIntent
                {
                    BotSlot = p.Slot,
                    BotName = p.PlayerName,
                    GameTick = tick,
                    CurrentTime = now,
                    Source = MovementIntentSource.EmergencyFallback,
                    Kind = MovementCommandKind.NavigateNavMesh,
                    Reason = "AlertNearbyTeammatesOfThreat_TradeFocus",
                    ExpiresAtTime = now + 0.30f,
                    GoalX = threatPos.X,
                    GoalY = threatPos.Y,
                    GoalZ = threatPos.Z,
                    ForceRepath = true,
                    Hurry = true,
                    IsStopping = false,
                    LookX = threatPos.X,
                    LookY = threatPos.Y,
                    LookZ = threatPos.Z + 64.0f,
                    LookDuration = 3.0f,
                    LookTolerance = 4.0f
                });
            }
        }
    }

    public void ThrowUtility(CCSPlayerController controller, int weaponDefIndex, Vector target)
    {
        ThrowUtility(controller, weaponDefIndex, target.X, target.Y, target.Z);
    }

    public void ThrowUtility(CCSPlayerController controller, int weaponDefIndex, float? aimX = null, float? aimY = null, float? aimZ = null)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        if (IsOpeningCanaryActiveSlot?.Invoke(controller.Slot) == true)
        {
            int rnd = GetCurrentRoundId?.Invoke() ?? 1;
            if (LeaseManager == null || !LeaseManager.AllowCompetingWriter(rnd, controller.Slot, Server.TickCount, "BotLocomotionDriver.ThrowUtility", $"UtilityDef:{weaponDefIndex}"))
            {
                return;
            }
        }

        var api = BotApi;
        var pawn = controller.PlayerPawn.Value;
        var bot = pawn?.Bot;
        if (pawn == null || bot == null || pawn.AbsOrigin == null) return;

        float eyeX = pawn.AbsOrigin.X;
        float eyeY = pawn.AbsOrigin.Y;
        float eyeZ = pawn.AbsOrigin.Z + 64.0f;

        float targetLookX;
        float targetLookY;
        float targetLookZ;

        if (aimX.HasValue && aimY.HasValue && aimZ.HasValue)
        {
            float dx = aimX.Value - eyeX;
            float dy = aimY.Value - eyeY;
            float dist2D = MathF.Sqrt(dx * dx + dy * dy);
            float parabolicArcZ = Math.Clamp(dist2D * 0.40f, 160f, 650f);
            targetLookX = aimX.Value;
            targetLookY = aimY.Value;
            targetLookZ = aimZ.Value + parabolicArcZ;
        }
        else
        {
            float yawDeg = pawn.EyeAngles?.Y ?? 0f;
            float yawRad = yawDeg * MathF.PI / 180f;
            targetLookX = eyeX + MathF.Cos(yawRad) * 450f;
            targetLookY = eyeY + MathF.Sin(yawRad) * 450f;
            targetLookZ = eyeZ + 240f;
        }

        if (weaponDefIndex == 45 || weaponDefIndex == 46 || weaponDefIndex == 48)
        {
            string utilType = weaponDefIndex == 45 ? "Smoke" : "Molotov";
            float checkX = aimX ?? targetLookX;
            float checkY = aimY ?? targetLookY;
            float checkZ = aimZ ?? (targetLookZ - 240f);

            var cp = MapProfileManager?.FindChokepointAt(checkX, checkY, checkZ);
            if (cp != null && UtilityCoordinator != null)
            {
                if (!UtilityCoordinator.CanThrowUtilityAt(cp.Id, utilType))
                {
                    return;
                }
                UtilityCoordinator.RegisterUtilityDetonation(checkX, checkY, checkZ, utilType, controller.Slot);
            }
        }

        bot.LookAtSpot[0] = targetLookX;
        bot.LookAtSpot[1] = targetLookY;
        bot.LookAtSpot[2] = targetLookZ;
        bot.LookAtSpotDuration = 1.6f;
        bot.LookAtSpotTimestamp = Server.CurrentTime;
        bot.LookAtSpotAngleTolerance = 3.0f;
        bot.LookAtSpotClearIfClose = false;

        if (api != null)
        {
            api.SwitchBotWeapon(controller.Slot, weaponDefIndex);
            _plugin?.AddRoundTimer(0.80f, () =>
            {
                if (controller.IsValid && controller.PawnIsAlive)
                {
                    var activeDef = controller.PlayerPawn.Value?.WeaponServices?.ActiveWeapon.Value?.AttributeManager.Item.ItemDefinitionIndex;
                    if (activeDef.HasValue && activeDef.Value == (ushort)weaponDefIndex)
                    {
                        api.InjectUsercmd(controller.Slot, IN_ATTACK, 250);
                    }
                    else
                    {
                        _plugin?.AddRoundTimer(0.20f, () =>
                        {
                            if (controller.IsValid && controller.PawnIsAlive)
                            {
                                var retryDef = controller.PlayerPawn.Value?.WeaponServices?.ActiveWeapon.Value?.AttributeManager.Item.ItemDefinitionIndex;
                                if (retryDef.HasValue && retryDef.Value == (ushort)weaponDefIndex)
                                {
                                    api.InjectUsercmd(controller.Slot, IN_ATTACK, 250);
                                }
                            }
                        });
                    }
                }
            });
            // Re-equipa arma de fogo apenas APÓS o arremesso completo da utilitária (1.35s)
            _plugin?.AddRoundTimer(1.35f, () =>
            {
                if (controller.IsValid && controller.PawnIsAlive)
                {
                    ForceEquipBestFirearm(controller);
                }
            });
        }
        else
        {
            string slotCmd = weaponDefIndex switch
            {
                44 => "slot6",
                43 => "slot7",
                45 => "slot8",
                47 => "slot9",
                46 or 48 => "slot10",
                _ => "slot4"
            };
            controller.ExecuteClientCommand(slotCmd);
            _plugin?.AddRoundTimer(0.80f, () =>
            {
                if (controller.IsValid && controller.PawnIsAlive)
                {
                    controller.ExecuteClientCommand("+attack");
                    _plugin?.AddRoundTimer(0.30f, () =>
                    {
                        if (controller.IsValid) controller.ExecuteClientCommand("-attack");
                    });
                }
            });
            _plugin?.AddRoundTimer(1.40f, () =>
            {
                if (controller.IsValid && controller.PawnIsAlive)
                {
                    ForceEquipBestFirearm(controller);
                }
            });
        }
    }

    public static bool IsGrenadeWeapon(string weaponName)
    {
        if (string.IsNullOrEmpty(weaponName)) return false;
        return weaponName.Contains("grenade", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("flashbang", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("molotov", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("incgrenade", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("decoy", StringComparison.OrdinalIgnoreCase);
    }

    public void CheckGrenadeEquipWatchdog(CCSPlayerController controller, float currentTime)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        var pawn = controller.PlayerPawn.Value;
        var activeWeapon = pawn?.WeaponServices?.ActiveWeapon.Value;
        string wName = activeWeapon?.DesignerName ?? "";
        int slot = controller.Slot;

        bool isKnife = wName.Contains("knife", StringComparison.OrdinalIgnoreCase) || wName.Contains("bayonet", StringComparison.OrdinalIgnoreCase);
        if (isKnife && (_isBombPlanted || (currentTime - RoundStartTime >= 10.0f) || RoundTimeRemaining <= 105.0f))
        {
            if (IsOpeningCanaryActiveSlot?.Invoke(slot) == true && !_isBombPlanted)
            {
                int rnd = GetCurrentRoundId?.Invoke() ?? 1;
                if (LeaseManager == null || !LeaseManager.AllowCompetingWriter(rnd, slot, Server.TickCount, "BotLocomotionDriver.CheckGrenadeEquipWatchdog", "ForceEquipBestFirearmOnKnife"))
                {
                    return;
                }
            }
            ForceEquipBestFirearm(controller);
            return;
        }

        bool isGrenade = IsGrenadeWeapon(wName);
        if (isGrenade)
        {
            bool wasHurtRecently = _lastHurtTime.TryGetValue(slot, out float hTime) && (currentTime - hTime) <= 3.0f;
            if (!_grenadeHoldStartTime.TryGetValue(slot, out float gStart))
            {
                _grenadeHoldStartTime[slot] = currentTime;
            }
            else
            {
                float heldTime = currentTime - gStart;
                bool enemyVisible = pawn?.Bot?.IsEnemyVisible ?? false;

                if (heldTime >= 2.0f || enemyVisible || wasHurtRecently)
                {
                    ForceEquipBestFirearm(controller);

                    if (heldTime >= 2.8f || enemyVisible || wasHurtRecently)
                    {
                        try
                        {
                            activeWeapon?.Remove();
                        }
                        catch { }
                        ForceEquipBestFirearm(controller);
                        _grenadeHoldStartTime.TryRemove(slot, out _);
                    }
                }
            }
        }
        else
        {
            _grenadeHoldStartTime.TryRemove(slot, out _);
        }
    }

    public void CheckGrenadeHurtWatchdog(CCSPlayerController controller)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        _lastHurtTime[controller.Slot] = Server.CurrentTime;

        var pawn = controller.PlayerPawn.Value;
        var activeWeapon = pawn?.WeaponServices?.ActiveWeapon.Value;
        string wName = activeWeapon?.DesignerName ?? "";
        if (IsGrenadeWeapon(wName))
        {
            try
            {
                activeWeapon?.Remove();
            }
            catch { }
            ForceEquipBestFirearm(controller);
            _grenadeHoldStartTime.TryRemove(controller.Slot, out _);
        }
    }

    public void ForceSwitchToBestCombatWeapon(CCSPlayerController controller)
    {
        ForceEquipBestFirearm(controller);
    }

    public void ForceEquipKnifeForCanary(CCSPlayerController bot)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;
        var api = BotApi;
        if (api != null)
        {
            api.SwitchBotWeapon(bot.Slot, 9001);
        }
        bot.ExecuteClientCommand("slot3");
    }

    public void ForceEquipBestFirearm(CCSPlayerController bot)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;
        var pawn = bot.PlayerPawn.Value;
        if (pawn?.WeaponServices?.MyWeapons == null) return;

        ushort? primaryDefIndex = null;
        ushort? secondaryDefIndex = null;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w == null || !w.IsValid || string.IsNullOrEmpty(w.DesignerName)) continue;
            string dName = w.DesignerName;

            if (CombatAdapter.IsPrimaryWeapon(dName))
            {
                primaryDefIndex = (ushort)w.AttributeManager.Item.ItemDefinitionIndex;
                break;
            }
            else if (CombatAdapter.IsSecondaryWeapon(dName) && !secondaryDefIndex.HasValue)
            {
                secondaryDefIndex = (ushort)w.AttributeManager.Item.ItemDefinitionIndex;
            }
        }

        ushort? targetDef = primaryDefIndex ?? secondaryDefIndex;
        if (targetDef.HasValue)
        {
            var api = BotApi;
            if (api != null)
            {
                api.SwitchBotWeapon(bot.Slot, (int)targetDef.Value);
            }
            else
            {
                bot.ExecuteClientCommand(primaryDefIndex.HasValue ? "slot1" : "slot2");
            }
        }
    }

    private static float GetBombTimeRemaining()
    {
        var planted = Utilities.FindAllEntitiesByDesignerName<CPlantedC4>("planted_c4").FirstOrDefault();
        if (planted != null && planted.IsValid)
        {
            try
            {
                return Math.Max(0.0f, planted.C4Blow - Server.CurrentTime);
            }
            catch { }
        }
        return 30.0f;
    }
}
