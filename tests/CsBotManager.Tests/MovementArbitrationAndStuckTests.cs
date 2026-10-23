using Xunit;

namespace CsBotManager.Tests;

public class MovementArbitrationAndStuckTests
{
    [Fact]
    public void MovementArbitrator_ResolvesPriorityHierarchyDeterministicallyAndAppliesOncePerTick()
    {
        var arbitrator = new MovementArbitrator();
        int slot = 4;
        int tick = 2000;
        float now = 31.25f;

        // Publica 3 intenções concorrentes no mesmo tick: TacticalNavigation, MicroMove e Unstuck
        arbitrator.PublishIntent(new MovementIntent
        {
            BotSlot = slot,
            BotName = "Steel",
            GameTick = tick,
            CurrentTime = now,
            Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.NavigateNavMesh,
            Reason = "TransitTo(ct_a_stairs_cross)",
            ExpiresAtTime = now + 0.10f,
            GoalX = -1200f,
            GoalY = -800f,
            GoalZ = -160f
        });

        arbitrator.PublishIntent(new MovementIntent
        {
            BotSlot = slot,
            BotName = "Steel",
            GameTick = tick,
            CurrentTime = now,
            Source = MovementIntentSource.MicroMove,
            Kind = MovementCommandKind.HoldStop,
            Reason = "ONNX_Hotzone_StandStill",
            ExpiresAtTime = now + 0.25f,
            IsStopping = true
        });

        arbitrator.PublishIntent(new MovementIntent
        {
            BotSlot = slot,
            BotName = "Steel",
            GameTick = tick,
            CurrentTime = now,
            Source = MovementIntentSource.Unstuck,
            Kind = MovementCommandKind.UsercmdVector,
            Reason = "STAGE1_CANCEL_MICROMOVE_AND_STRAFE_UNSTUCK",
            ExpiresAtTime = now + 0.45f,
            UseUsercmdVelocity = true,
            ForwardMove = 140f,
            SideMove = 220f
        });

        var decision = arbitrator.CollectAndResolveIntents(slot, tick, now);
        Assert.NotNull(decision);
        Assert.Equal(MovementIntentSource.Unstuck, decision!.WinningIntent.Source);
        Assert.Equal(2, decision.SuppressedIntents.Count);

        // ApplyWinningIntent deve retornar true na 1ª aplicação do tick e false se chamado de novo no mesmo tick
        bool firstApply = arbitrator.ApplyWinningIntent(decision, controller: null, api: null);
        bool duplicateApplySameTick = arbitrator.ApplyWinningIntent(decision, controller: null, api: null);

        Assert.True(firstApply);
        Assert.False(duplicateApplySameTick);
    }

    [Fact]
    public void EvaluateStuck2DWindow_Detects2DStuckEvenWhenBotJumpsInPlaceAndEscalatesToBlacklist()
    {
        var config = BotSystemConfig.Default;

        // Bot pulou verticalmente (Z variou), mas X e Y só variaram 12 unidades em 3.6s (< 40u) longe do alvo
        var stage1 = BotLocomotionDriver.EvaluateStuck2DWindow(
            curX: -1450f,
            curY: -1950f,
            targetX: -600f,
            targetY: -1200f,
            checkStartX: -1458f,
            checkStartY: -1959f,
            checkStartDistToTarget2D: 1140f,
            elapsedSeconds: 3.6f,
            previousStuckCount: 0,
            config: config);

        Assert.True(stage1.IsStuck2D);
        Assert.Equal(1, stage1.NewStuckStage);
        Assert.False(stage1.ShouldBlacklistCurrentWaypoint);

        // Segunda janela consecutiva sem progresso 2D -> escala para Stage 2 e blacklista o waypoint
        var stage2 = BotLocomotionDriver.EvaluateStuck2DWindow(
            curX: -1445f,
            curY: -1948f,
            targetX: -600f,
            targetY: -1200f,
            checkStartX: -1450f,
            checkStartY: -1950f,
            checkStartDistToTarget2D: 1130f,
            elapsedSeconds: 3.6f,
            previousStuckCount: stage1.NewStuckStage,
            config: config);

        Assert.True(stage2.IsStuck2D);
        Assert.Equal(2, stage2.NewStuckStage);
        Assert.True(stage2.ShouldBlacklistCurrentWaypoint);
    }

    [Fact]
    public void TradeSpacing_RespectsPairCooldownSingleYieldingBotAndWideSwingWindow()
    {
        var mapMgr = new MapProfileManager();
        var roleMgr = new RoleManager();
        var engine = new MicroMoveEngine(mapMgr, roleMgr);

        // Dois bots na mesma coordenada (Dist2D = 0u -> SharedTargetDetected = true)
        // Slot 2 é EntryFragger (prioritário), Slot 5 é Rotator (deve ceder)
        var nonYieldingAttempt = engine.TryEvaluatePairRepulsion(
            currentBotSlot: 2,
            curX: 100f, curY: 200f, curZ: -160f,
            currentHasC4: false, currentInCombat: false, currentRole: BotRole.EntryFragger,
            allySlot: 5,
            allyX: 100f, allyY: 200f, allyZ: -160f,
            allyHasC4: false, allyInCombat: false, allyRole: BotRole.Rotator,
            currentTime: 10.0f,
            out int actionForPriorityBot);

        // O bot prioritário (Slot 2) NÃO cede espaço
        Assert.Null(nonYieldingAttempt);
        Assert.Equal(0, actionForPriorityBot);

        // O bot que cede (Slot 5) recebe a ação de repulsão e registra o cooldown de 2.5s do par
        var yieldingAttempt = engine.TryEvaluatePairRepulsion(
            currentBotSlot: 5,
            curX: 100f, curY: 200f, curZ: -160f,
            currentHasC4: false, currentInCombat: false, currentRole: BotRole.Rotator,
            allySlot: 2,
            allyX: 100f, allyY: 200f, allyZ: -160f,
            allyHasC4: false, allyInCombat: false, allyRole: BotRole.EntryFragger,
            currentTime: 10.0f,
            out int actionForYieldingBot);

        Assert.NotNull(yieldingAttempt);
        Assert.True(yieldingAttempt!.SharedTargetDetected);
        Assert.Equal(2, yieldingAttempt.PriorityBotSlot);
        Assert.Equal(5, yieldingAttempt.YieldingBotSlot);
        Assert.NotEqual(0, actionForYieldingBot);

        // Nova tentativa 0.5s depois (10.5s < 12.5s cooldown) para o mesmo par -> bloqueada pelo cooldown!
        var spamAttempt = engine.TryEvaluatePairRepulsion(
            currentBotSlot: 5,
            curX: 105f, curY: 205f, curZ: -160f,
            currentHasC4: false, currentInCombat: false, currentRole: BotRole.Rotator,
            allySlot: 2,
            allyX: 100f, allyY: 200f, allyZ: -160f,
            allyHasC4: false, allyInCombat: false, allyRole: BotRole.EntryFragger,
            currentTime: 10.5f,
            out _);

        Assert.Null(spamAttempt);

        // Valida janela estrita de Wide Swing [250u, 400u]: 58u e 122u NUNCA podem entrar!
        Assert.False(engine.IsWithinWideSwingWindow(58.0f));
        Assert.False(engine.IsWithinWideSwingWindow(122.0f));
        Assert.False(engine.IsWithinWideSwingWindow(249.9f));
        Assert.True(engine.IsWithinWideSwingWindow(250.0f));
        Assert.True(engine.IsWithinWideSwingWindow(325.0f));
        Assert.True(engine.IsWithinWideSwingWindow(400.0f));
        Assert.False(engine.IsWithinWideSwingWindow(400.1f));
    }

    [Fact]
    public void CounterStrafe_RequiresStrictImminentEngagementAndEnforcesCooldown()
    {
        var mapMgr = new MapProfileManager();
        var roleMgr = new RoleManager();
        var engine = new MicroMoveEngine(mapMgr, roleMgr);

        // 1. Sem linha de visão -> suprimido
        var noLos = engine.EvaluateCounterStrafeEligibility(
            botSlot: 3, currentTime: 20.0f, speed2D: 215f, vx: 215f, vy: 0f,
            weaponName: "weapon_ak47", isPrecisionWeapon: true,
            hasValidAliveTarget: true, hasLineOfSight: false, aimErrorDegrees: 8.0f,
            weaponReady: true, ammoAvailable: 30, isReloading: false, attackIntent: true, targetDistance2D: 650f);
        Assert.False(noLos.Triggered);
        Assert.Equal("NO_LINE_OF_SIGHT", noLos.SuppressionReason);

        // 2. Erro de mira > 16 graus -> suprimido
        var highAimError = engine.EvaluateCounterStrafeEligibility(
            botSlot: 3, currentTime: 20.0f, speed2D: 215f, vx: 215f, vy: 0f,
            weaponName: "weapon_ak47", isPrecisionWeapon: true,
            hasValidAliveTarget: true, hasLineOfSight: true, aimErrorDegrees: 24.5f,
            weaponReady: true, ammoAvailable: 30, isReloading: false, attackIntent: true, targetDistance2D: 650f);
        Assert.False(highAimError.Triggered);
        Assert.Contains("AIM_ERROR_TOO_HIGH", highAimError.SuppressionReason);

        // 3. Munição zerada -> suprimido
        var noAmmo = engine.EvaluateCounterStrafeEligibility(
            botSlot: 3, currentTime: 20.0f, speed2D: 215f, vx: 215f, vy: 0f,
            weaponName: "weapon_ak47", isPrecisionWeapon: true,
            hasValidAliveTarget: true, hasLineOfSight: true, aimErrorDegrees: 6.0f,
            weaponReady: true, ammoAvailable: 0, isReloading: true, attackIntent: true, targetDistance2D: 650f);
        Assert.False(noAmmo.Triggered);

        // 4. Engajamento legítimo iminente -> acionado!
        var valid = engine.EvaluateCounterStrafeEligibility(
            botSlot: 3, currentTime: 20.0f, speed2D: 215f, vx: 215f, vy: 0f,
            weaponName: "weapon_ak47", isPrecisionWeapon: true,
            hasValidAliveTarget: true, hasLineOfSight: true, aimErrorDegrees: 7.5f,
            weaponReady: true, ammoAvailable: 28, isReloading: false, attackIntent: true, targetDistance2D: 650f);
        Assert.True(valid.Triggered);
        Assert.Equal("NONE", valid.SuppressionReason);

        // 5. Tentativa imediata 0.5s depois (20.5s < 22.5s cooldown de 2.5s) -> bloqueada pelo cooldown!
        var onCooldown = engine.EvaluateCounterStrafeEligibility(
            botSlot: 3, currentTime: 20.5f, speed2D: 215f, vx: 215f, vy: 0f,
            weaponName: "weapon_ak47", isPrecisionWeapon: true,
            hasValidAliveTarget: true, hasLineOfSight: true, aimErrorDegrees: 5.0f,
            weaponReady: true, ammoAvailable: 27, isReloading: false, attackIntent: true, targetDistance2D: 640f);
        Assert.False(onCooldown.Triggered);
        Assert.Equal("COOLDOWN_ACTIVE", onCooldown.SuppressionReason);
    }
}
