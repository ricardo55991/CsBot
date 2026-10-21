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
    public float HoldDurationRemaining { get; set; }
    public bool ForceCrouch { get; set; }
    public BotOrderPriority Priority { get; set; } = BotOrderPriority.Medium_Tactical;
    public float LastCheckX { get; set; }
    public float LastCheckY { get; set; }
    public float LastCheckTime { get; set; }
    public int StuckCount { get; set; }
}

public class BotLocomotionDriver
{
    private CsBotManagerPlugin? _plugin;
    public void SetPlugin(CsBotManagerPlugin plugin) => _plugin = plugin;

    private readonly PluginCapability<IBotControllerApi> _botControllerApiCap = new("botcontroller:api");
    private readonly ConcurrentDictionary<int, TrackedBotNavState> _botStates = new();
    private IBotControllerApi? _cachedApi;

    // Salvaguardas de Plant e Defuse
    private bool _isBombPlanted = false;
    private Vector? _bombPosition = null;
    private bool _isTacticalSaveActive = false;
    private float _lastTickTime = 0f;

    // Controladores Integrados
    public SiteClearAndPlantController? PlantController { get; set; }
    public CtRetakeAndDefuseBrain? RetakeBrain { get; set; }
    public UtilityAndClockCoordinator? UtilityCoordinator { get; set; }
    public MapProfileManager? MapProfileManager { get; set; }
    public MicroMoveEngine? MicroMoveEngine { get; set; }
    public float RoundTimeRemaining { get; set; } = 115.0f;

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

    public void NotifyBombState(bool isPlanted, Vector? bombPosition, bool isSaveActive, List<CCSPlayerController>? ctBots = null)
    {
        _isBombPlanted = isPlanted;
        _bombPosition = bombPosition;
        _isTacticalSaveActive = isSaveActive;

        if (isPlanted)
        {
            // PONTO 1, 2 e 5 (Item 3): Libera locks de parada, holding e timers ao plantar a C4
            foreach (var kvp in _botStates)
            {
                var s = kvp.Value;
                s.HoldDurationRemaining = 0f;
                s.HasReachedDestination = false;
                s.IsHoldingSpot = false;
                s.LastCheckTime = 0f;
                s.StuckCount = 0;
                if (s.ActiveMovementId != 0 && BotApi != null)
                {
                    try { BotApi.CancelUsercmdMovement(kvp.Key, s.ActiveMovementId); } catch { }
                    s.ActiveMovementId = 0;
                }
            }

            var allPlayers = Utilities.GetPlayers();
            foreach (var p in allPlayers)
            {
                if (p != null && p.IsValid && p.IsBot && p.PawnIsAlive)
                {
                    var bot = p.PlayerPawn.Value?.Bot;
                    if (bot != null)
                    {
                        bot.IsStopping = false;
                        bot.WaitTimer.Duration = 0f;
                        bot.WaitTimer.Timestamp = 0f;
                        bot.SneakTimer.Timestamp = 0f;
                    }
                }
            }

            // CTs longe do bomb desarmam o setup defensivo e avançam para Retake
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

        var api = BotApi;
        foreach (var kvp in _botStates)
        {
            if (api != null && kvp.Value.ActiveMovementId != 0)
            {
                try
                {
                    api.CancelUsercmdMovement(kvp.Key, kvp.Value.ActiveMovementId);
                }
                catch { }
            }
        }
        _botStates.Clear();
        MicroMoveEngine?.ResetRound(api);
    }

    public void ClearNavigation(int slot)
    {
        if (_botStates.TryRemove(slot, out var state))
        {
            if (state.ActiveMovementId != 0)
            {
                try
                {
                    BotApi?.CancelUsercmdMovement(slot, state.ActiveMovementId);
                }
                catch { }
            }
        }
    }

    public TrackedBotNavState? GetNavState(int slot)
    {
        return _botStates.TryGetValue(slot, out var s) ? s : null;
    }

    public void NavigateToSpot(CCSPlayerController controller, TacticalSpot spot, bool hurry = false, EngagementStance? stanceOverride = null, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;

        if (_botStates.TryGetValue(controller.Slot, out var existingState))
        {
            if (existingState.Priority > priority && (existingState.HoldDurationRemaining > 0 || !existingState.HasReachedDestination))
            {
                return;
            }
            if (existingState.ActiveMovementId != 0)
            {
                try
                {
                    BotApi?.CancelUsercmdMovement(controller.Slot, existingState.ActiveMovementId);
                }
                catch { }
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
        ApplyImmediateNavmeshTarget(controller, state);
    }

    public void NavigateToPosition(CCSPlayerController controller, float x, float y, float z, float? lookX = null, float? lookY = null, float? lookZ = null, bool hurry = false, EngagementStance stance = EngagementStance.PASSIVE_HOLD, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;

        if (_botStates.TryGetValue(controller.Slot, out var existingState))
        {
            if (existingState.Priority > priority && (existingState.HoldDurationRemaining > 0 || !existingState.HasReachedDestination))
            {
                return;
            }
            if (existingState.ActiveMovementId != 0)
            {
                try
                {
                    BotApi?.CancelUsercmdMovement(controller.Slot, existingState.ActiveMovementId);
                }
                catch { }
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
        ApplyImmediateNavmeshTarget(controller, state);
    }

    public void NavigateToPoint(CCSPlayerController controller, Vector point, bool hurry = false, EngagementStance stance = EngagementStance.PASSIVE_HOLD, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        NavigateToPosition(controller, point.X, point.Y, point.Z, null, null, null, hurry, stance, priority);
    }

    public void HoldPosition(CCSPlayerController controller, float duration = 3.0f, bool crouch = false, BotOrderPriority priority = BotOrderPriority.Medium_Tactical)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;

        if (_botStates.TryGetValue(controller.Slot, out var state))
        {
            if (state.Priority > priority && state.HoldDurationRemaining > 0)
            {
                return;
            }
            if (state.ActiveMovementId != 0)
            {
                try
                {
                    BotApi?.CancelUsercmdMovement(controller.Slot, state.ActiveMovementId);
                }
                catch { }
                state.ActiveMovementId = 0;
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

        var botPawn = controller.PlayerPawn.Value;
        var bot = botPawn?.Bot;
        if (bot != null)
        {
            bot.WaitTimer.Duration = duration;
            bot.WaitTimer.Timestamp = Server.CurrentTime + duration;
            bot.IsStopping = true;
        }

        if (crouch)
        {
            BotApi?.InjectUsercmd(controller.Slot, IN_DUCK, (int)(duration * 1000f));
        }
    }

    private void ApplyImmediateNavmeshTarget(CCSPlayerController controller, TrackedBotNavState state)
    {
        var pawn = controller.PlayerPawn.Value;
        var bot = pawn?.Bot;
        if (bot == null) return;

        bot.GoalPosition[0] = state.TargetX;
        bot.GoalPosition[1] = state.TargetY;
        bot.GoalPosition[2] = state.TargetZ;
        bot.RepathTimer.Timestamp = 0f;
        bot.IsStopping = false;

        if (state.Hurry)
        {
            bot.HurryTimer.Duration = 3.0f;
            bot.HurryTimer.Timestamp = Server.CurrentTime + 3.0f;
            bot.MustRunTimer.Duration = 3.0f;
            bot.MustRunTimer.Timestamp = Server.CurrentTime + 3.0f;
        }
        else if (state.Stance == EngagementStance.AGGRESSIVE_POKE)
        {
            bot.SneakTimer.Duration = 2.0f;
            bot.SneakTimer.Timestamp = Server.CurrentTime + 2.0f;
        }
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
        float dt = _lastTickTime > 0f ? Math.Clamp(currentTime - _lastTickTime, 0.001f, 0.1f) : 0.015625f;
        _lastTickTime = currentTime;

        // Fase 6A: Motor de Micro-Movimento Coordenado a 16Hz (MLMove Camada 1)
        MicroMoveEngine?.UpdateTick(currentTime, RoundTimeRemaining, _isBombPlanted, _botStates, api);

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

            // =========================================================================
            // SEMÂNTICA DETERMINÍSTICA DE HOLD (F-016)
            // =========================================================================
            if (state.HoldDurationRemaining > 0f)
            {
                state.HoldDurationRemaining = Math.Max(0f, state.HoldDurationRemaining - dt);
                bot.WaitTimer.Duration = state.HoldDurationRemaining;
                bot.WaitTimer.Timestamp = currentTime + state.HoldDurationRemaining;
                bot.IsStopping = true;
                if (state.ForceCrouch && api != null)
                {
                    api.InjectUsercmd(slot, IN_DUCK, 250);
                }
                continue;
            }

            // =========================================================================
            // SALVAGUARDA 1: PRIORIDADE MÁXIMA DE OBJETIVO - C4 PLANT (SISTEMA 1)
            // =========================================================================
            if (controller.Team == CsTeam.Terrorist && HasC4(controller))
            {
                bool isNearSiteOrPlanting = false;
                try
                {
                    isNearSiteOrPlanting = pawn.InBombZone;
                }
                catch { }

                if (isNearSiteOrPlanting)
                {
                    var allPlayers = Utilities.GetPlayers();
                    bool isAuthorized = PlantController == null || PlantController.IsSiteSafeToPlant(controller, RoundTimeRemaining, allPlayers);

                    if (isAuthorized)
                    {
                        // Autorizado a plantar: aciona anúncio do pixel e libera o plant
                        if (PlantController != null && !PlantController.HasAnnouncedPlant)
                        {
                            int aliveTrs = allPlayers.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.Terrorist);
                            int aliveCts = allPlayers.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.CounterTerrorist);
                            PlantController.AnnounceAndStartPlant(controller, "A", aliveTrs, aliveCts);
                        }

                        bot.IsStopping = false;
                        bot.WaitTimer.Duration = 0f;
                        bot.WaitTimer.Timestamp = 0f;
                        if (state.ActiveMovementId != 0 && api != null)
                        {
                            api.CancelUsercmdMovement(slot, state.ActiveMovementId);
                            state.ActiveMovementId = 0;
                        }
                        continue;
                    }
                    else
                    {
                        // Limpeza do bomb em andamento: não para e não planta no aberto!
                        bot.IsStopping = false;
                    }
                }
            }

            // =========================================================================
            // SALVAGUARDA 2: PRIORIDADE MÁXIMA DE OBJETIVO - C4 DEFUSE & SAVE CT (SISTEMA 2 / F-005)
            // =========================================================================
            if (controller.Team == CsTeam.CounterTerrorist)
            {
                if (_isTacticalSaveActive)
                {
                    // No SAVE TÁTICO, bloqueia imediatamente qualquer tentativa de defuse ou corrida para a C4
                    bool isDefusing = false;
                    try
                    {
                        isDefusing = pawn.IsDefusing;
                    }
                    catch { }

                    if (isDefusing)
                    {
                        controller.ExecuteClientCommand("-use; slot1");
                    }

                    if (state.ActiveMovementId != 0 && api != null)
                    {
                        try
                        {
                            api.CancelUsercmdMovement(slot, state.ActiveMovementId);
                        }
                        catch { }
                        state.ActiveMovementId = 0;
                    }

                    bot.IsStopping = true;
                    bot.WaitTimer.Duration = 0.8f;
                    bot.WaitTimer.Timestamp = currentTime + 0.8f;
                    continue;
                }
                else if (_isBombPlanted)
                {
                    bool isDefusing = false;
                    try
                    {
                        isDefusing = pawn.IsDefusing;
                    }
                    catch { }

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
                        bot.IsStopping = false;
                        bot.WaitTimer.Duration = 0f;
                        bot.WaitTimer.Timestamp = 0f;

                        var allPlayers = Utilities.GetPlayers();
                        int aliveTrs = allPlayers.Count(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.Terrorist);
                        var ctBots = allPlayers.Where(p => p != null && p.IsValid && p.IsBot && p.Team == CsTeam.CounterTerrorist).ToList();

                        if (RetakeBrain != null && _bombPosition != null)
                        {
                            float bombTimeRemaining = GetBombTimeRemaining();
                            RetakeBrain.TryDeploySmokeOnC4(controller, _bombPosition, bombTimeRemaining, ctBots);

                            // Prioridade inteligente de Defuse (Módulo 2): cede a vez caso não tenha kit e um aliado com kit esteja próximo
                            if (!CtRetakeAndDefuseBrain.HasDefuser(controller))
                            {
                                RetakeBrain.CheckAndEnforceSmartDefusePriority(controller, _bombPosition, ctBots);
                            }

                            if (isDefusing && RetakeBrain.CurrentDefuseAction == DefuseAction.NormalStick)
                            {
                                RetakeBrain.OnDefuseTapped(controller, _bombPosition, bombTimeRemaining, aliveTrs);
                            }

                            if (RetakeBrain.ShouldInjectDefuseInput(controller) && api != null)
                            {
                                api.InjectUsercmd(slot, IN_USE, 300);
                            }
                        }
                        else if (api != null)
                        {
                            api.InjectUsercmd(slot, IN_USE, 300);
                        }
                        continue;
                    }
                }
            }

            // Se o MicroMoveEngine (16Hz) estiver executando manobra ativa (Counter-Strafe / Trade Spacing / Wall-Hug),
            // cede o controle fino nos 3 horizontes (0ms, 125ms, 250ms) sem sobrescrever com o NavMesh
            var microTraj = MicroMoveEngine?.GetTrajectory(slot);
            if (microTraj != null && microTraj.IsOverrideActive && currentTime <= microTraj.OverrideExpiresAt)
            {
                continue;
            }

            float dx = curX - state.TargetX;
            float dy = curY - state.TargetY;
            float dz = curZ - state.TargetZ;
            float distSq = (dx * dx) + (dy * dy) + (dz * dz);

            if (distSq > (85.0f * 85.0f))
            {
                // Em trânsito para o spot
                state.HasReachedDestination = false;
                state.IsHoldingSpot = false;

                // Item 4: Detector de Unstuck por PositionDelta (2.0s < 35u)
                if (state.LastCheckTime <= 0f)
                {
                    state.LastCheckX = curX;
                    state.LastCheckY = curY;
                    state.LastCheckTime = currentTime;
                }
                else if (currentTime - state.LastCheckTime >= 2.0f)
                {
                    float deltaX = curX - state.LastCheckX;
                    float deltaY = curY - state.LastCheckY;
                    float displacement2D = MathF.Sqrt(deltaX * deltaX + deltaY * deltaY);

                    if (displacement2D < 35.0f)
                    {
                        // Bot travado na quina / parede! Aciona descolamento imediato
                        state.StuckCount++;
                        bot.RepathTimer.Timestamp = 0f;
                        bot.IsStopping = false;
                        bot.WaitTimer.Duration = 0f;
                        bot.WaitTimer.Timestamp = 0f;

                        if (state.ActiveMovementId != 0 && api != null)
                        {
                            try { api.CancelUsercmdMovement(slot, state.ActiveMovementId); } catch { }
                            state.ActiveMovementId = 0;
                        }

                        if (api != null)
                        {
                            api.InjectUsercmd(slot, IN_JUMP | IN_FORWARD, 250);
                            float strafeSpeed = (state.StuckCount % 2 == 0) ? 220f : -220f;
                            state.ActiveMovementId = api.StartUsercmdMovement(slot, 120f, strafeSpeed);
                        }

                        bot.HurryTimer.Duration = 2.5f;
                        bot.HurryTimer.Timestamp = currentTime + 2.5f;
                        bot.MustRunTimer.Duration = 2.5f;
                        bot.MustRunTimer.Timestamp = currentTime + 2.5f;
                    }
                    else
                    {
                        state.StuckCount = 0;
                    }

                    state.LastCheckX = curX;
                    state.LastCheckY = curY;
                    state.LastCheckTime = currentTime;
                }
                bot.GoalPosition[0] = state.TargetX;
                bot.GoalPosition[1] = state.TargetY;
                bot.GoalPosition[2] = state.TargetZ;
                bot.IsStopping = false;

                // CORREÇÃO MOONWALK (Ponto 3): Em trânsito, NUNCA travar a cabeça no ângulo do pixel final!
                // O bot deve olhar naturalmente para a frente na direção em que se desloca.
                if (!bot.IsEnemyVisible)
                {
                    bot.LookAtSpotClearIfClose = true;
                    bot.LookAtSpotDuration = 0f;
                    bot.LookAtSpotTimestamp = 0f;
                }

                if (currentTime - state.LastRepathTime > 1.2f)
                {
                    bot.RepathTimer.Timestamp = 0f;
                    state.LastRepathTime = currentTime;
                }

                if (state.Hurry)
                {
                    bot.HurryTimer.Duration = 2.0f;
                    bot.HurryTimer.Timestamp = currentTime + 2.0f;
                    bot.MustRunTimer.Duration = 2.0f;
                    bot.MustRunTimer.Timestamp = currentTime + 2.0f;
                }
                else if (state.Stance == EngagementStance.AGGRESSIVE_POKE)
                {
                    bot.SneakTimer.Duration = 1.0f;
                    bot.SneakTimer.Timestamp = currentTime + 1.0f;
                }
            }
            else
            {
                // Chegou ao spot alvo (Ponto 2: Crava o pixel e congela movimentação de patrulha)
                state.HasReachedDestination = true;
                state.IsHoldingSpot = true;
                state.LastCheckTime = 0f;
                state.StuckCount = 0;

                // Fixa GoalPosition na posição atual para desativar a navegação livre do Source 2
                bot.GoalPosition[0] = curX;
                bot.GoalPosition[1] = curY;
                bot.GoalPosition[2] = curZ;

                if (!bot.IsEnemyVisible && state.LookX.HasValue && state.LookY.HasValue && state.LookZ.HasValue)
                {
                    bot.LookAtSpot[0] = state.LookX.Value;
                    bot.LookAtSpot[1] = state.LookY.Value;
                    bot.LookAtSpot[2] = state.LookZ.Value;
                    bot.LookAtSpotDuration = 2.0f;
                    bot.LookAtSpotTimestamp = currentTime;
                    bot.LookAtSpotAngleTolerance = 5.0f;
                    bot.LookAtSpotClearIfClose = false;
                }

                switch (state.Stance)
                {
                    case EngagementStance.PASSIVE_HOLD:
                    case EngagementStance.ONE_AND_DONE:
                        bot.IsStopping = true;
                        if (bot.WaitTimer.Timestamp < currentTime)
                        {
                            bot.WaitTimer.Duration = 3.0f;
                            bot.WaitTimer.Timestamp = currentTime + 3.0f;
                        }
                        if (state.ActiveMovementId != 0 && api != null)
                        {
                            api.CancelUsercmdMovement(slot, state.ActiveMovementId);
                            state.ActiveMovementId = 0;
                        }
                        if (state.ForceCrouch && api != null)
                        {
                            api.InjectUsercmd(slot, IN_DUCK, 250);
                        }
                        break;

                    case EngagementStance.JIGGLE_INFO:
                        bot.WaitTimer.Duration = 1.0f;
                        bot.WaitTimer.Timestamp = currentTime + 1.0f;
                        if (currentTime - state.StanceActionTimer > 0.35f)
                        {
                            state.JiggleDirection = -state.JiggleDirection;
                            state.StanceActionTimer = currentTime;
                            if (api != null)
                            {
                                if (state.ActiveMovementId != 0)
                                {
                                    api.CancelUsercmdMovement(slot, state.ActiveMovementId);
                                    state.ActiveMovementId = 0;
                                }
                                state.ActiveMovementId = api.StartUsercmdMovement(slot, 0f, state.JiggleDirection * 250f);
                            }
                        }
                        break;

                    case EngagementStance.AGGRESSIVE_POKE:
                        bot.SneakTimer.Duration = 2.0f;
                        bot.SneakTimer.Timestamp = currentTime + 2.0f;
                        break;
                }
            }
        }
    }

    // =========================================================================
    // ARCO PARABÓLICO DE ELEVAÇÃO VERTICAL E GATE ANTI-DUPLA SMOKE (PARTE A - ITEM 1 / F-015)
    // =========================================================================
    // =========================================================================
    // ALERTA DE AMEAÇA IMEDIATA / TRADE KILL FOCUS (PONTO 6)
    // =========================================================================
    public void AlertNearbyTeammatesOfThreat(Vector threatPos, int victimSlot, CsTeam team, float radius = 950f)
    {
        var allPlayers = Utilities.GetPlayers();
        foreach (var p in allPlayers)
        {
            if (p == null || !p.IsValid || !p.IsBot || !p.PawnIsAlive || p.Team != team || p.Slot == victimSlot) continue;
            var pawn = p.PlayerPawn.Value;
            var bot = pawn?.Bot;
            if (pawn?.AbsOrigin == null || bot == null) continue;

            float dist = (pawn.AbsOrigin - threatPos).Length();
            if (dist <= radius)
            {
                // Entra em COMBAT_THREAT_FOCUS: mira imediatamente no agressor
                bot.LookAtSpot[0] = threatPos.X;
                bot.LookAtSpot[1] = threatPos.Y;
                bot.LookAtSpot[2] = threatPos.Z + 64.0f;
                bot.LookAtSpotDuration = 3.0f;
                bot.LookAtSpotTimestamp = Server.CurrentTime;
                bot.LookAtSpotAngleTolerance = 4.0f;
                bot.LookAtSpotClearIfClose = false;

                if (_botStates.TryGetValue(p.Slot, out var state))
                {
                    state.LookX = threatPos.X;
                    state.LookY = threatPos.Y;
                    state.LookZ = threatPos.Z + 64.0f;
                    state.Stance = EngagementStance.AGGRESSIVE_POKE;
                    state.HoldDurationRemaining = 0f;
                }

                bot.IsStopping = false;
                bot.GoalPosition[0] = threatPos.X;
                bot.GoalPosition[1] = threatPos.Y;
                bot.GoalPosition[2] = threatPos.Z;
                bot.RepathTimer.Timestamp = 0f;
                bot.HurryTimer.Duration = 2.5f;
                bot.HurryTimer.Timestamp = Server.CurrentTime + 2.5f;
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

            // Arco parabólico: elevação vertical proporcional à distância (simula pitch -20° a -35°)
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
            targetLookZ = eyeZ + 240f; // elevação vertical de ~28 graus
        }

        // Gate Anti-Dupla Smoke / Molotov (F-015)
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
                    return; // Chokepoint já bloqueado; suprime arremesso redundante
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
            // PONTO 4: Ciclo visual e físico realista (Saque -> Puxada de pino ~0.5s -> Arremesso)
            api.SwitchBotWeapon(controller.Slot, weaponDefIndex);
            _plugin?.AddRoundTimer(0.55f, () =>
            {
                if (controller.IsValid && controller.PawnIsAlive)
                {
                    api.InjectUsercmd(controller.Slot, IN_ATTACK, 250);
                }
            });
        }
        else
        {
            controller.ExecuteClientCommand("+attack");
            _plugin?.AddRoundTimer(0.55f, () =>
            {
                if (controller.IsValid) controller.ExecuteClientCommand("-attack");
            });
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
