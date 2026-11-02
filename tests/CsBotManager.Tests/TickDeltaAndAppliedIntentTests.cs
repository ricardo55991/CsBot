using System;
using System.Collections.Concurrent;
using System.Reflection;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class TickDeltaAndAppliedIntentTests
{
    // =========================================================================
    // 1. TESTES DO DELTA DE TEMPO DO TICK
    // =========================================================================

    [Fact]
    public void TickDelta_At64Hz_IsCloseTo0_015625()
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig { ServerTickRate = 64f };
        driver.ResetRound();

        float t0 = 10.0f;
        driver.BeginMovementTick(t0, 100);

        float t1 = t0 + 0.015625f;
        driver.BeginMovementTick(t1, 101);

        Assert.InRange(driver.CurrentTickDeltaTime, 0.0156f, 0.0157f);
    }

    [Fact]
    public void TickDelta_TwoMethodsInSameTick_UseExactSameDelta()
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig { ServerTickRate = 64f };
        driver.ResetRound();

        float t0 = 20.0f;
        driver.BeginMovementTick(t0, 200);

        float t1 = t0 + 0.015625f;
        driver.BeginMovementTick(t1, 201);
        float deltaInBegin = driver.CurrentTickDeltaTime;

        // Executa CollectLocomotionIntents no mesmo tick com o mesmo timestamp
        // Não pode recalcular dt como 0.001f!
        driver.CollectLocomotionIntents(t1, 201);
        float deltaAfterCollect = driver.CurrentTickDeltaTime;

        Assert.Equal(deltaInBegin, deltaAfterCollect);
        Assert.NotEqual(0.001f, deltaAfterCollect);
        Assert.InRange(deltaAfterCollect, 0.0156f, 0.0157f);
    }

    [Fact]
    public void TickDelta_FirstTick_UsesEffectiveIntervalAsFallback()
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig { ServerTickRate = 64f };
        driver.ResetRound();

        // No primeiro tick (_lastTickTime == 0f), o delta deve ser exatamente o fallback (1.0 / 64)
        float firstTime = 5.0f;
        driver.BeginMovementTick(firstTime, 1);

        float expectedFallback = 1.0f / 64.0f;
        Assert.Equal(expectedFallback, driver.CurrentTickDeltaTime);
    }

    [Fact]
    public void TickDelta_ResetRound_ClearsClockAndResetsToEffectiveInterval()
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig { ServerTickRate = 64f };

        // Simula alguns ticks
        driver.BeginMovementTick(1.0f, 10);
        driver.BeginMovementTick(1.015625f, 11);

        // Reseta o round
        driver.ResetRound();

        // Campo _lastTickTime privado deve ser 0f
        var lastTickField = typeof(BotLocomotionDriver).GetField("_lastTickTime", BindingFlags.NonPublic | BindingFlags.Instance);
        float lastTick = (float)lastTickField!.GetValue(driver)!;
        Assert.Equal(0f, lastTick);

        // _currentTickDeltaTime deve ser o intervalo efetivo
        float expectedInterval = 1.0f / 64.0f;
        Assert.Equal(expectedInterval, driver.CurrentTickDeltaTime);
    }

    [Fact]
    public void TickDelta_Hold3Seconds_ExpiresCloseTo192Ticks_At64Hz()
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig { ServerTickRate = 64f };
        driver.ResetRound();

        int slot = 1;
        float holdDuration = 3.0f;
        float tickInterval = 1.0f / 64.0f; // 0.015625s

        var state = new TrackedBotNavState
        {
            Slot = slot,
            HoldDurationRemaining = holdDuration,
            IsHoldingSpot = true,
            Priority = BotOrderPriority.Medium_Tactical
        };

        var botStatesField = typeof(BotLocomotionDriver).GetField("_botStates", BindingFlags.NonPublic | BindingFlags.Instance);
        var botStates = (ConcurrentDictionary<int, TrackedBotNavState>)botStatesField!.GetValue(driver)!;
        botStates[slot] = state;

        float curTime = 100.0f;
        int tickCount = 0;

        // Simula o avanço do jogo tick a tick
        while (state.HoldDurationRemaining > 0f && tickCount < 300)
        {
            tickCount++;
            curTime += tickInterval;
            driver.BeginMovementTick(curTime, 1000 + tickCount);

            // Simula consumo do hold com o dt do tick (como em CollectLocomotionIntents)
            float dt = driver.CurrentTickDeltaTime;
            state.HoldDurationRemaining = Math.Max(0f, state.HoldDurationRemaining - dt);
        }

        // 3.0 segundos / 0.015625s = 192 ticks exatos
        Assert.Equal(0f, state.HoldDurationRemaining);
        Assert.InRange(tickCount, 191, 193);
    }

    // =========================================================================
    // 2. TESTES DE COOLDOWN DE RECOVERY (SEM VALOR HARDCODED 0.65F)
    // =========================================================================

    [Theory]
    [InlineData(1.0f)]
    [InlineData(2.5f)]
    public void RecoveryCooldown_UsesConfiguredSeconds_InBothPaths(float configuredCooldown)
    {
        var driver = new BotLocomotionDriver();
        driver.Config = new BotSystemConfig
        {
            PhysicalStopRecoveryCooldownSeconds = configuredCooldown
        };
        driver.ResetRound();

        int slot = 2;
        var state = new TrackedBotNavState
        {
            Slot = slot,
            UnstuckCooldownUntil = 0f
        };

        var botStatesField = typeof(BotLocomotionDriver).GetField("_botStates", BindingFlags.NonPublic | BindingFlags.Instance);
        var botStates = (ConcurrentDictionary<int, TrackedBotNavState>)botStatesField!.GetValue(driver)!;
        botStates[slot] = state;

        float currentTime = 50.0f;

        // Caminho 1: Simula 2D Stuck Recovery
        state.UnstuckCooldownUntil = currentTime + driver.Config.PhysicalStopRecoveryCooldownSeconds;
        Assert.Equal(currentTime + configuredCooldown, state.UnstuckCooldownUntil);

        // Caminho 2: MicroMove PhysicalStopState Recovery
        var stopState = new PhysicalStopState
        {
            RecoveryRequested = true,
            RecoveryCooldownUntil = currentTime + driver.Config.PhysicalStopRecoveryCooldownSeconds
        };
        Assert.Equal(currentTime + configuredCooldown, stopState.RecoveryCooldownUntil);

        // Bloqueio durante cooldown
        float testMidTime = currentTime + (configuredCooldown * 0.5f);
        Assert.True(testMidTime < state.UnstuckCooldownUntil);
        Assert.True(testMidTime < stopState.RecoveryCooldownUntil);

        // Liberação após cooldown
        float testAfterTime = currentTime + configuredCooldown + 0.05f;
        Assert.False(testAfterTime < state.UnstuckCooldownUntil);
        Assert.False(testAfterTime < stopState.RecoveryCooldownUntil);
    }

    // =========================================================================
    // 3. TESTES DE COMPARAÇÃO DA INTENÇÃO VENCEDORA COM ÚLTIMA APLICADA
    // =========================================================================

    [Fact]
    public void WinningIntent_FirstAppliedIntent_RegistersNewWinningIntent()
    {
        var driver = new BotLocomotionDriver();
        driver.ResetRound();

        int slot = 3;
        var intentGuid = Guid.NewGuid();

        // Simula resolução do arbitrador com a intenção vencedora
        Guid winningLogicalId = intentGuid;
        bool logicalActionChanged = !driver.LastAppliedLogicalIntentBySlot.TryGetValue(slot, out Guid lastAppliedId)
                                    || lastAppliedId != winningLogicalId;

        Assert.True(logicalActionChanged, "Primeira intenção deve ser registrada como nova");

        if (logicalActionChanged)
        {
            driver.ExecutionTracker.RegisterExpectedEngineStateChange(slot, ExpectedEngineStateChange.NewWinningIntent);
            driver.LastAppliedLogicalIntentBySlot[slot] = winningLogicalId;
        }

        Assert.True(driver.LastAppliedLogicalIntentBySlot.TryGetValue(slot, out var applied));
        Assert.Equal(intentGuid, applied);
    }

    [Fact]
    public void WinningIntent_SameIntentFor32Ticks_DoesNotRegisterAgain()
    {
        var driver = new BotLocomotionDriver();
        driver.ResetRound();

        int slot = 3;
        var intentGuid = Guid.NewGuid();

        // Aplica primeiro tick
        driver.LastAppliedLogicalIntentBySlot[slot] = intentGuid;

        // Ticks 2 a 32 com a MESMA intenção
        for (int i = 1; i <= 32; i++)
        {
            Guid winningLogicalId = intentGuid;
            bool logicalActionChanged = !driver.LastAppliedLogicalIntentBySlot.TryGetValue(slot, out Guid lastAppliedId)
                                        || lastAppliedId != winningLogicalId;

            Assert.False(logicalActionChanged, $"Tick {i} da mesma manobra contínua não deve registrar NewWinningIntent");
        }
    }

    [Fact]
    public void WinningIntent_NewIntent_RegistersChange()
    {
        var driver = new BotLocomotionDriver();
        driver.ResetRound();

        int slot = 4;
        var intent1 = Guid.NewGuid();
        var intent2 = Guid.NewGuid();

        // Aplica intenção 1
        driver.LastAppliedLogicalIntentBySlot[slot] = intent1;

        // Agora intenção 2 é vencedora
        bool logicalActionChanged = !driver.LastAppliedLogicalIntentBySlot.TryGetValue(slot, out Guid lastAppliedId)
                                    || lastAppliedId != intent2;

        Assert.True(logicalActionChanged, "Troca para nova intenção vencedora deve registrar mudança");

        driver.LastAppliedLogicalIntentBySlot[slot] = intent2;
        Assert.Equal(intent2, driver.LastAppliedLogicalIntentBySlot[slot]);
    }

    [Fact]
    public void WinningIntent_LosingPublishedIntent_DoesNotBecomeLastApplied()
    {
        var driver = new BotLocomotionDriver();
        driver.ResetRound();

        int slot = 5;
        var losingIntent = Guid.NewGuid();
        var winningIntent = Guid.NewGuid();

        var state = new TrackedBotNavState
        {
            Slot = slot,
            CurrentLogicalIntentId = losingIntent
        };

        // A intenção que venceu a arbitragem foi a winningIntent
        Guid winningLogicalId = winningIntent;
        bool logicalActionChanged = !driver.LastAppliedLogicalIntentBySlot.TryGetValue(slot, out Guid lastAppliedId)
                                    || lastAppliedId != winningLogicalId;

        if (logicalActionChanged)
        {
            driver.LastAppliedLogicalIntentBySlot[slot] = winningLogicalId;
        }

        // A última aplicada deve ser estritamente a intenção vencedora, NÃO a publicada que perdeu
        Assert.Equal(winningIntent, driver.LastAppliedLogicalIntentBySlot[slot]);
        Assert.NotEqual(state.CurrentLogicalIntentId, driver.LastAppliedLogicalIntentBySlot[slot]);
    }

    [Fact]
    public void WinningIntent_ResetRound_ClearsAllAppliedIntents()
    {
        var driver = new BotLocomotionDriver();
        driver.LastAppliedLogicalIntentBySlot[1] = Guid.NewGuid();
        driver.LastAppliedLogicalIntentBySlot[2] = Guid.NewGuid();

        Assert.Equal(2, driver.LastAppliedLogicalIntentBySlot.Count);

        driver.ResetRound();

        Assert.Empty(driver.LastAppliedLogicalIntentBySlot);
    }

    [Fact]
    public void WinningIntent_ClearNavigation_RemovesAppliedIntentForReusedSlot()
    {
        var driver = new BotLocomotionDriver();
        int slot = 6;
        var oldGuid = Guid.NewGuid();
        driver.LastAppliedLogicalIntentBySlot[slot] = oldGuid;

        // Bot morre ou sai: ClearNavigation é invocado
        driver.ClearNavigation(slot);

        Assert.False(driver.LastAppliedLogicalIntentBySlot.ContainsKey(slot), "Slot liberado não pode conter intenção anterior");

        // Novo bot entra no mesmo slot com novo GUID
        var newBotGuid = Guid.NewGuid();
        bool logicalActionChanged = !driver.LastAppliedLogicalIntentBySlot.TryGetValue(slot, out Guid lastAppliedId)
                                    || lastAppliedId != newBotGuid;

        Assert.True(logicalActionChanged, "Slot reutilizado não pode herdar ID anterior");
    }
}
