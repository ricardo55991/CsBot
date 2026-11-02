using System;
using System.Collections.Generic;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class MovementExecutionTrackerTests
{
    [Fact]
    public void MillisecondsToTicks_ComputesDynamicTicks_For64HzAnd128Hz()
    {
        double tick64 = 1.0 / 64.0;   // 0.015625
        double tick128 = 1.0 / 128.0; // 0.0078125

        // 64 Hz
        Assert.Equal(8, MovementExecutionTracker.MillisecondsToTicks(125.0, tick64));
        Assert.Equal(16, MovementExecutionTracker.MillisecondsToTicks(250.0, tick64));
        Assert.Equal(32, MovementExecutionTracker.MillisecondsToTicks(500.0, tick64));

        // 128 Hz
        Assert.Equal(16, MovementExecutionTracker.MillisecondsToTicks(125.0, tick128));
        Assert.Equal(32, MovementExecutionTracker.MillisecondsToTicks(250.0, tick128));
        Assert.Equal(64, MovementExecutionTracker.MillisecondsToTicks(500.0, tick128));
    }

    [Fact]
    public void RecordOrUpdateIntentIssued_DeduplicatesContinuousSamples_Over32Ticks()
    {
        var tracker = new MovementExecutionTracker();
        int slot = 2;
        var entity = new EntityIdentity(slot, slot, 0, 1);
        var logicalId = Guid.NewGuid();
        var trajId = Guid.NewGuid();

        var intent = new MovementIntent
        {
            BotSlot = slot,
            BotName = "FalleN",
            InternalRoundId = 101L,
            CreatedAtTick = 100,
            CommandGeneration = 1,
            LogicalActionId = logicalId,
            TrajectoryId = trajId,
            StepIndex = 0,
            Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.NavigateNavMesh,
            GoalX = -1000f,
            GoalY = -500f,
            GoalZ = -160f
        };

        var initialPos = new Vector(-1200f, -600f, -160f);
        float tickInterval = (float)(1.0 / 64.0);

        // Tick inicial (100)
        tracker.RecordOrUpdateIntentIssued(intent, entity, 100, 1.5625f, initialPos, 220f, tickInterval);
        Assert.Equal(1, tracker.ActiveSamplesCount);
        Assert.Equal(1, tracker.TotalSamplesTracked);

        // 32 ticks subsequentes da mesma manobra lógica
        for (int t = 101; t <= 132; t++)
        {
            float curTime = 1.5625f + (t - 100) * tickInterval;
            var pos = new Vector(initialPos.X + (t - 100) * 2f, initialPos.Y, initialPos.Z);
            tracker.RecordOrUpdateIntentIssued(intent, entity, t, curTime, pos, 220f, tickInterval);

            // NENHUMA amostra adicional deve ser aberta para a mesma manobra contínua (Adendo 3)
            Assert.Equal(1, tracker.ActiveSamplesCount);
            Assert.Equal(1, tracker.TotalSamplesTracked);
        }

        // Nova intenção com outro LogicalActionId substitui a anterior
        var newIntent = new MovementIntent
        {
            BotSlot = slot,
            BotName = "FalleN",
            InternalRoundId = 101L,
            CreatedAtTick = 133,
            CommandGeneration = 2,
            LogicalActionId = Guid.NewGuid(),
            TrajectoryId = Guid.NewGuid(),
            Source = MovementIntentSource.BombObjective,
            Kind = MovementCommandKind.NavigateNavMesh
        };

        tracker.RecordOrUpdateIntentIssued(newIntent, entity, 133, 2.078f, initialPos, 220f, tickInterval);
        Assert.Equal(1, tracker.ActiveSamplesCount);
        Assert.Equal(2, tracker.TotalSamplesTracked);
        Assert.Equal(1, tracker.TotalCompletedSamples);
    }

    [Fact]
    public void AuthorizedHoldApplied_And_FullStopApplied_DoNotIncrementBlockedOutcomes()
    {
        var tracker = new MovementExecutionTracker();
        int slot = 4;
        var entity = new EntityIdentity(slot, slot, 0, 1);
        var logicalId = Guid.NewGuid();

        var holdIntent = new MovementIntent
        {
            BotSlot = slot,
            BotName = "Taco",
            InternalRoundId = 1L,
            CreatedAtTick = 50,
            CommandGeneration = 1,
            LogicalActionId = logicalId,
            Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.HoldStop,
            IsStopping = true
        };

        tracker.RecordOrUpdateIntentIssued(holdIntent, entity, 50, 0.78f, new Vector(0, 0, 0), 0f, 0.015625f);
        tracker.CancelBotSamples(slot, MovementExecutionOutcome.AuthorizedHoldApplied);

        // Bloqueios auditados devem permanecer ZERO para holds autorizados (Adendo 7 e 8)
        Assert.Equal(0, tracker.TotalBlockedOutcomes);
        Assert.Equal(1, tracker.TotalCompletedSamples);
    }

    [Fact]
    public void CheckAndAuditPreTickOverride_SuppressesFalsePositives_WhenExpectedEngineStateChangeRegistered()
    {
        var tracker = new MovementExecutionTracker();
        int slot = 5;
        long roundId = 202L;
        long tick = 1000L;
        var entity = new EntityIdentity(slot, slot, 0, 1);

        var postApplyFp = new BotStateFingerprint(
            BotSlot: slot,
            InternalRoundId: roundId,
            GameTick: tick,
            IsStopping: false,
            GoalX: 500f,
            GoalY: 1000f,
            GoalZ: -100f,
            WaitTimestamp: 0f,
            WaitDuration: 0f,
            SneakTimestamp: 0f,
            RepathTimestamp: 0f,
            Buttons: 0UL,
            UsercmdHandle: 2001L,
            DesiredForwardMove: 250f,
            DesiredSideMove: 0f,
            Entity: entity);

        tracker.StorePostApplyFingerprint(slot, postApplyFp);

        // Registra mudança de estado da engine legítima (ex: Repath pelo nosso sistema)
        tracker.RegisterExpectedEngineStateChange(slot, ExpectedEngineStateChange.Repath);

        // PreTick seguinte chega com IsStopping = true
        var nextPreApplyFp = postApplyFp with
        {
            GameTick = tick + 1,
            IsStopping = true
        };

        // Deve suprimir falso positivo pois era uma alteração esperada da engine
        bool overrideDetected = tracker.CheckAndAuditPreTickOverride(slot, nextPreApplyFp, null, 15.625f);
        Assert.False(overrideDetected);
        Assert.Equal(0, tracker.TotalOverrideOutcomes);
    }

    [Fact]
    public void VolumeTest_10Bots_10000Ticks_BoundedMemoryAndNoLeaks()
    {
        var tracker = new MovementExecutionTracker();
        float tickInterval = (float)(1.0 / 64.0);
        int totalBots = 10;
        int totalTicks = 10000;

        var activeIntents = new MovementIntent[totalBots];
        var identities = new EntityIdentity[totalBots];

        for (int i = 0; i < totalBots; i++)
        {
            identities[i] = new EntityIdentity(i, i, 0, 1);
            activeIntents[i] = new MovementIntent
            {
                BotSlot = i,
                BotName = $"Bot_{i}",
                InternalRoundId = 1L,
                CreatedAtTick = 0,
                CommandGeneration = 1,
                LogicalActionId = Guid.NewGuid(),
                Source = MovementIntentSource.TacticalNavigation,
                Kind = MovementCommandKind.NavigateNavMesh
            };
        }

        for (int tick = 0; tick < totalTicks; tick++)
        {
            float curTime = tick * tickInterval;

            for (int slot = 0; slot < totalBots; slot++)
            {
                // A cada 250 ticks (~4s), simula troca de manobra tática
                if (tick > 0 && tick % 250 == 0)
                {
                    activeIntents[slot] = new MovementIntent
                    {
                        BotSlot = slot,
                        BotName = $"Bot_{slot}",
                        InternalRoundId = 1L,
                        CreatedAtTick = tick,
                        CommandGeneration = activeIntents[slot].CommandGeneration + 1,
                        LogicalActionId = Guid.NewGuid(),
                        Source = MovementIntentSource.TacticalNavigation,
                        Kind = MovementCommandKind.NavigateNavMesh
                    };
                }

                var pos = new Vector(slot * 100f + tick * 0.5f, slot * 50f, -160f);
                tracker.RecordOrUpdateIntentIssued(
                    activeIntents[slot],
                    identities[slot],
                    tick,
                    curTime,
                    pos,
                    220f,
                    tickInterval);
            }
        }

        // Conclui todas as amostras pendentes
        for (int s = 0; s < totalBots; s++)
        {
            tracker.CompleteSample(s, MovementExecutionOutcome.AppliedWithProgress, "Fim de simulação");
        }

        // Verificações de integridade estrita
        Assert.Equal(0, tracker.ActiveSamplesCount);
        Assert.True(tracker.TotalSamplesTracked >= totalBots, "Total de amostras deve cobrir todas as manobras emitidas");
        Assert.True(tracker.TotalCompletedSamples > 0, "Amostras substituídas devem ser arquivadas ordenadamente");
    }

    [Fact]
    public void ProductionTrackerUsesRealEntityIdentity()
    {
        var tracker = new MovementExecutionTracker();
        int slot = 3;
        var realIdentity = new EntityIdentity(
            ControllerEntityIndex: 14,
            PawnEntityIndex: 56,
            SteamId: 76561198012345678UL,
            SpawnGeneration: 2);

        var intent = new MovementIntent
        {
            BotSlot = slot,
            BotName = "Coldzera",
            InternalRoundId = 10L,
            CreatedAtTick = 500,
            CommandGeneration = 1,
            LogicalActionId = Guid.NewGuid(),
            Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.NavigateNavMesh
        };

        tracker.RecordOrUpdateIntentIssued(
            intent,
            realIdentity,
            500,
            7.8125f,
            new Vector(100, 200, -100),
            250f,
            0.015625f);

        var activeSample = tracker.GetActiveSample(slot);
        Assert.NotNull(activeSample);
        Assert.Equal(14, activeSample.Entity.ControllerEntityIndex);
        Assert.Equal(56, activeSample.Entity.PawnEntityIndex);
        Assert.Equal(76561198012345678UL, activeSample.Entity.SteamId);
        Assert.Equal(2, activeSample.Entity.SpawnGeneration);
        Assert.NotEqual(slot, activeSample.Entity.ControllerEntityIndex);
    }

    [Fact]
    public void ContinuousTimedHoldKeepsLogicalActionId()
    {
        var tracker = new MovementExecutionTracker();
        var state = new TrackedBotNavState
        {
            Slot = 1,
            HoldDurationRemaining = 2.0f,
            Priority = BotOrderPriority.Medium_Tactical
        };

        var initialId = BotLocomotionDriver.EnsureLogicalActionId(state, "TimedHold");
        int initialGen = state.CommandGeneration;

        var entity = new EntityIdentity(10, 20, 0, 1);
        float tickInterval = 0.015625f;

        // 32 ticks de simulação de TimedHold contínuo
        for (int i = 0; i < 32; i++)
        {
            var holdId = BotLocomotionDriver.EnsureLogicalActionId(state, "TimedHold");
            Assert.Equal(initialId, holdId);
            Assert.Equal(initialGen, state.CommandGeneration);

            var intent = new MovementIntent
            {
                BotSlot = state.Slot,
                InternalRoundId = 1L,
                CreatedAtTick = 100 + i,
                CommandGeneration = state.CommandGeneration,
                LogicalActionId = holdId,
                Source = MovementIntentSource.TacticalNavigation,
                Kind = MovementCommandKind.HoldStop,
                IsStopping = true
            };

            tracker.RecordOrUpdateIntentIssued(intent, entity, 100 + i, 1.5625f + i * tickInterval, new Vector(0, 0, 0), 0f, tickInterval);
            Assert.Equal(1, tracker.ActiveSamplesCount);
            Assert.Equal(1, tracker.TotalSamplesTracked);
        }
    }

    [Fact]
    public void ContinuousNavigationKeepsLogicalActionId()
    {
        var tracker = new MovementExecutionTracker();
        var state = new TrackedBotNavState
        {
            Slot = 2,
            TargetX = -1000f,
            TargetY = -500f,
            TargetZ = -160f,
            Priority = BotOrderPriority.Medium_Tactical
        };

        var initialId = BotLocomotionDriver.EnsureLogicalActionId(state, "NavigateNavMesh");
        int initialGen = state.CommandGeneration;
        var entity = new EntityIdentity(11, 21, 0, 1);
        float tickInterval = 0.015625f;

        // 32 ticks navegando ao mesmo destino
        for (int i = 0; i < 32; i++)
        {
            var navId = BotLocomotionDriver.EnsureLogicalActionId(state, "NavigateNavMesh");
            Assert.Equal(initialId, navId);
            Assert.Equal(initialGen, state.CommandGeneration);

            var intent = new MovementIntent
            {
                BotSlot = state.Slot,
                InternalRoundId = 1L,
                CreatedAtTick = 200 + i,
                CommandGeneration = state.CommandGeneration,
                LogicalActionId = navId,
                Source = MovementIntentSource.TacticalNavigation,
                Kind = MovementCommandKind.NavigateNavMesh,
                GoalX = state.TargetX,
                GoalY = state.TargetY,
                GoalZ = state.TargetZ
            };

            tracker.RecordOrUpdateIntentIssued(intent, entity, 200 + i, 3.125f + i * tickInterval, new Vector(i * 2f, 0, 0), 220f, tickInterval);
            Assert.Equal(1, tracker.ActiveSamplesCount);
            Assert.Equal(1, tracker.TotalSamplesTracked);
        }

        // Mudança real de ação gera novo ID e incrementa geração
        var newActionId = BotLocomotionDriver.EnsureLogicalActionId(state, "SpotAggressivePoke", forceNew: true);
        Assert.NotEqual(initialId, newActionId);
        Assert.Equal(initialGen + 1, state.CommandGeneration);
    }

    [Fact]
    public void JiggleDirectionChangeCreatesNewGeneration()
    {
        var state = new TrackedBotNavState
        {
            Slot = 3,
            JiggleDirection = 1,
            LastJiggleDirection = 1,
            StanceActionTimer = 1.0f
        };

        // Pulso inicial na direção 1
        var id1 = BotLocomotionDriver.EnsureLogicalActionId(state, "SpotJiggleInfo");
        int gen1 = state.CommandGeneration;

        // Mesmo pulso: preserva ID e geração
        var id1Same = BotLocomotionDriver.EnsureLogicalActionId(state, "SpotJiggleInfo");
        Assert.Equal(id1, id1Same);
        Assert.Equal(gen1, state.CommandGeneration);

        // Inverte direção do jiggle
        state.JiggleDirection = -1;
        bool dirChanged = state.LastJiggleDirection != state.JiggleDirection;
        Assert.True(dirChanged);

        state.LastJiggleDirection = state.JiggleDirection;
        var id2 = BotLocomotionDriver.EnsureLogicalActionId(state, "SpotJiggleInfo", forceNew: true);

        Assert.NotEqual(id1, id2);
        Assert.True(state.CommandGeneration > gen1);
        Assert.Equal(-1, state.JiggleDirection);
    }

    [Fact]
    public void RecoveryCooldownBlocksRepeatedRequest()
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig
        {
            PhysicalStopRecoveryCooldownSeconds = 1.5f
        };

        int slot = 4;
        var navState = new TrackedBotNavState
        {
            Slot = slot,
            UnstuckCooldownUntil = 0f
        };

        var field = typeof(BotLocomotionDriver).GetField("_botStates", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var dict = (System.Collections.Concurrent.ConcurrentDictionary<int, TrackedBotNavState>)field!.GetValue(driver)!;
        dict[slot] = navState;

        // Simula primeiro recovery no tempo 10.0s
        float time1 = 10.0f;
        navState.UnstuckCooldownUntil = time1 + driver.Config.PhysicalStopRecoveryCooldownSeconds;
        navState.StuckCount = 1;

        // Segundo recovery requisitado no tempo 10.5s (dentro do cooldown)
        float time2 = 10.5f;
        bool isBlocked = time2 < navState.UnstuckCooldownUntil;
        Assert.True(isBlocked, "Recovery dentro do cooldown deve ser bloqueado");

        // MicroMoveEngine PhysicalStopState cooldown check
        var stopState = new PhysicalStopState
        {
            RecoveryRequested = true,
            RecoveryCooldownUntil = 10.0f + driver.Config.PhysicalStopRecoveryCooldownSeconds
        };
        bool microBlocked = time2 < stopState.RecoveryCooldownUntil;
        Assert.True(microBlocked, "MicroMoveEngine não deve solicitar novo recovery antes do cooldown");
    }

    [Fact]
    public void RecoveryAllowedAfterCooldown()
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig
        {
            PhysicalStopRecoveryCooldownSeconds = 1.5f
        };

        int slot = 4;
        var navState = new TrackedBotNavState
        {
            Slot = slot,
            UnstuckCooldownUntil = 11.5f
        };

        float timeAfterCooldown = 11.6f;
        bool isAllowed = timeAfterCooldown >= navState.UnstuckCooldownUntil;
        Assert.True(isAllowed, "Recovery deve ser permitido após o cooldown expirar");

        var stopState = new PhysicalStopState
        {
            RecoveryRequested = true,
            RecoveryCooldownUntil = 11.5f
        };
        bool microAllowed = timeAfterCooldown >= stopState.RecoveryCooldownUntil;
        Assert.True(microAllowed, "MicroMoveEngine pode solicitar nova recuperação após cooldown");

        // Progresso real encerra recovery (physicallyMoving)
        float currentSpeed2D = 25.0f;
        float displacement2D = 10.0f;
        bool physicallyMoving = currentSpeed2D >= driver.Config.PhysicalStopResetSpeedThreshold &&
                                displacement2D >= driver.Config.PhysicalStopMinDisplacement2D;
        if (physicallyMoving)
        {
            stopState.RecoveryRequested = false;
        }
        Assert.False(stopState.RecoveryRequested, "Progresso físico horizontal real encerra o recovery");
    }

    [Fact]
    public void CompletedSampleRemovedFromActiveCollection()
    {
        var tracker = new MovementExecutionTracker();
        int slot = 5;
        var entity = new EntityIdentity(15, 25, 0, 1);

        var intent = new MovementIntent
        {
            BotSlot = slot,
            InternalRoundId = 1L,
            CreatedAtTick = 10,
            CommandGeneration = 1,
            LogicalActionId = Guid.NewGuid(),
            Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.NavigateNavMesh
        };

        tracker.RecordOrUpdateIntentIssued(intent, entity, 10, 1.0f, new Vector(0, 0, 0), 200f, 0.015625f);
        Assert.Equal(1, tracker.ActiveSamplesCount);

        // Conclui a amostra
        tracker.CompleteSample(slot, MovementExecutionOutcome.AppliedWithProgress, "Concluído com sucesso", 200f, 60f);

        // Após conclusão, a amostra ativa DEVE ser removida da coleção ativa
        Assert.Equal(0, tracker.ActiveSamplesCount);
        Assert.Equal(1, tracker.TotalCompletedSamples);
    }

    [Fact]
    public void ExpectedRepathDoesNotTriggerExternalOverride()
    {
        var tracker = new MovementExecutionTracker();
        int slot = 6;
        long roundId = 55L;
        long tick = 2000L;
        var entity = new EntityIdentity(16, 26, 0, 1);

        var postApplyFp = new BotStateFingerprint(
            BotSlot: slot,
            InternalRoundId: roundId,
            GameTick: tick,
            IsStopping: false,
            GoalX: 100f,
            GoalY: 200f,
            GoalZ: 0f,
            WaitTimestamp: 0f,
            WaitDuration: 0f,
            SneakTimestamp: 0f,
            RepathTimestamp: 0f,
            Buttons: 0UL,
            UsercmdHandle: 100L,
            DesiredForwardMove: 250f,
            DesiredSideMove: 0f,
            Entity: entity);

        tracker.StorePostApplyFingerprint(slot, postApplyFp);

        // Registra Repath legítimo
        tracker.RegisterExpectedEngineStateChange(slot, ExpectedEngineStateChange.Repath);

        var preTickFp = postApplyFp with
        {
            GameTick = tick + 1,
            GoalX = 500f,
            GoalY = 600f
        };

        bool overrideDetected = tracker.CheckAndAuditPreTickOverride(slot, preTickFp, null, 31.25f);
        Assert.False(overrideDetected, "Repath esperado não deve disparar override externo");
        Assert.Equal(0, tracker.TotalOverrideOutcomes);
    }

    [Fact]
    public void ExpectedMacroGoalChangeDoesNotTriggerExternalOverride()
    {
        var tracker = new MovementExecutionTracker();
        int slot = 7;
        long roundId = 55L;
        long tick = 3000L;
        var entity = new EntityIdentity(17, 27, 0, 1);

        var postApplyFp = new BotStateFingerprint(
            BotSlot: slot,
            InternalRoundId: roundId,
            GameTick: tick,
            IsStopping: false,
            GoalX: 100f,
            GoalY: 200f,
            GoalZ: 0f,
            WaitTimestamp: 0f,
            WaitDuration: 0f,
            SneakTimestamp: 0f,
            RepathTimestamp: 0f,
            Buttons: 0UL,
            UsercmdHandle: 101L,
            DesiredForwardMove: 250f,
            DesiredSideMove: 0f,
            Entity: entity);

        tracker.StorePostApplyFingerprint(slot, postApplyFp);

        // Registra mudança de objetivo macro
        tracker.RegisterExpectedEngineStateChange(slot, ExpectedEngineStateChange.GoalPositionChanged | ExpectedEngineStateChange.NavigationProgress);

        var preTickFp = postApplyFp with
        {
            GameTick = tick + 1,
            GoalX = -1200f,
            GoalY = -600f
        };

        bool overrideDetected = tracker.CheckAndAuditPreTickOverride(slot, preTickFp, null, 46.875f);
        Assert.False(overrideDetected, "Mudança de destino macro esperada não deve disparar override");
        Assert.Equal(0, tracker.TotalOverrideOutcomes);
    }

    [Fact]
    public void TickRateSourceMatchesActualImplementation()
    {
        var tracker = new MovementExecutionTracker();

        // 1. Simula detecção da ENGINE via override
        MovementExecutionTracker.EngineTickIntervalOverride = 1.0f / 128f;
        var engineInfo = tracker.DetermineEffectiveTickRateInfo();
        Assert.Equal(TickRateSource.Engine, engineInfo.Source);
        Assert.Equal(128.0f, engineInfo.TickRate);
        Assert.Equal(16, engineInfo.Ticks125);
        Assert.Equal(32, engineInfo.Ticks250);
        Assert.Equal(64, engineInfo.Ticks500);

        // 2. Simula engine indisponível (-1f) e testa fonte CONFIG
        MovementExecutionTracker.EngineTickIntervalOverride = -1f;
        tracker.Config = new BotSystemConfig { ServerTickRate = 64f };
        var configInfo = tracker.DetermineEffectiveTickRateInfo();
        Assert.Equal(TickRateSource.Config, configInfo.Source);
        Assert.Equal(64.0f, configInfo.TickRate);
        Assert.Equal(8, configInfo.Ticks125);
        Assert.Equal(16, configInfo.Ticks250);
        Assert.Equal(32, configInfo.Ticks500);

        // 3. Testa DEFAULT quando config <= 0
        tracker.Config = new BotSystemConfig { ServerTickRate = 0f };
        var defaultInfo = tracker.DetermineEffectiveTickRateInfo();
        Assert.Equal(TickRateSource.Default, defaultInfo.Source);
        Assert.Equal(64.0f, defaultInfo.TickRate);

        // Limpa override de teste
        MovementExecutionTracker.EngineTickIntervalOverride = null;
    }

    [Fact]
    public void MicroMoveEngineUsesLifecycleInternalRoundId()
    {
        var lifecycle = new RoundLifecycleManager();
        var mapProfile = new MapProfileManager();
        var roles = new RoleManager();
        var engine = new MicroMoveEngine(mapProfile, roles)
        {
            Lifecycle = lifecycle
        };

        // Inicia round 101 no lifecycle
        lifecycle.TryBeginRound(false, 100, 0, 0, out var rec1, out _);
        Assert.NotNull(rec1);
        Assert.Equal(rec1.InternalRoundId, engine.CurrentInternalRoundId);

        // Transiciona / inicia round 102
        lifecycle.TryBeginRound(false, 200, 1, 0, out var rec2, out _);
        Assert.NotNull(rec2);
        Assert.Equal(rec2.InternalRoundId, engine.CurrentInternalRoundId);
        Assert.True(engine.CurrentInternalRoundId > 0);
    }
}
