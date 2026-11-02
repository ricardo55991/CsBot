using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_2_FinalAdjustmentsTests
{
    private readonly MapProfileManager _mapProfileManager;

    public V4_2_2_FinalAdjustmentsTests()
    {
        _mapProfileManager = new MapProfileManager();
        var spots = new List<TacticalSpot>
        {
            new() { Id = "tr_staging_b_apartments_kitchen", Sector = "Apartamentos B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging },
            new() { Id = "tr_staging_b_apartments_house", Sector = "Apartamentos B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging },
            new() { Id = "tr_exec_b_site_plant", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Plant },
            new() { Id = "tr_exec_b_van_clear", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute },
            new() { Id = "tr_exec_b_market_push", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute },
            new() { Id = "tr_staging_a_ramp", Sector = "Rampa A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Staging },
            new() { Id = "tr_staging_palace_room", Sector = "Palácio A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Staging },
            new() { Id = "tr_exec_a_site_default", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Plant },
            new() { Id = "tr_exec_a_triple_clear", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute },
            new() { Id = "tr_exec_a_stairs_clear", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute },
            new() { Id = "tr_staging_top_mid_boxes", Sector = "Top Mid", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Staging },
            new() { Id = "tr_staging_underpass_top", Sector = "Underpass", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Staging },
            new() { Id = "tr_exec_mid_connector_push", Sector = "Connector", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Execute },
            new() { Id = "tr_staging_t_roof", Sector = "T Roof", Side = "TR", AssociatedBombsite = "Mid", Usage = SpotUsage.Staging },
            new() { Id = "tr_spawn_safe", Sector = "TR Spawn", Side = "TR", AssociatedBombsite = "None", Usage = SpotUsage.Fallback }
        };
        _mapProfileManager.SetSpotsForTesting(spots);
    }

    [Fact]
    public void Test1_ExecuteBMaterializesBSpots()
    {
        // Act
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Execução B (Tapete / Apartamentos Rápido)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        // Assert
        Assert.True(orders.ContainsKey("bot_entry"));
        Assert.True(orders.ContainsKey("bot_rotator"));
        Assert.Contains("b", orders["bot_entry"].StagingSpotId, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("b", orders["bot_rotator"].StagingSpotId, StringComparison.OrdinalIgnoreCase);
        Assert.Equal("tr_exec_b_site_plant", orders["bot_rotator"].ExecuteSpotId);
        Assert.NotEqual("tr_staging_top_mid_boxes", orders["bot_entry"].StagingSpotId);
    }

    [Fact]
    public void Test2_ExecuteAMaterializesASpots()
    {
        // Act
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Execução A (Palácio + Rampa Sincronizados)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        // Assert
        Assert.True(orders.ContainsKey("bot_entry"));
        Assert.True(orders.ContainsKey("bot_rotator"));
        Assert.Contains("a", orders["bot_entry"].StagingSpotId.ToLowerInvariant() + orders["bot_entry"].TargetArea.ToLowerInvariant());
        Assert.Contains("a", orders["bot_rotator"].StagingSpotId.ToLowerInvariant() + orders["bot_rotator"].TargetArea.ToLowerInvariant());
        Assert.Equal("tr_exec_a_site_default", orders["bot_rotator"].ExecuteSpotId);
        Assert.NotEqual("tr_staging_b_apartments_kitchen", orders["bot_entry"].StagingSpotId);
    }

    [Fact]
    public void Test3_LlmMidOrderIsRepairedForExecuteB()
    {
        // Arrange
        var plan = new TacticalPlan
        {
            CurrentTactic = "Execução B (Tapete / Apartamentos Rápido)",
            TacticName = "Execução B (Tapete / Apartamentos Rápido)"
        };
        plan.BotOrders["bot_entry"] = new BotTacticalOrder
        {
            TargetArea = "Bombsite Mid",
            StagingSpotId = "tr_staging_top_mid_boxes",
            ExecuteSpotId = "tr_staging_top_mid_boxes"
        };
        plan.BotOrders["bot_rotator"] = new BotTacticalOrder
        {
            TargetArea = "Bombsite Mid",
            StagingSpotId = "tr_staging_top_mid_boxes",
            ExecuteSpotId = "tr_staging_top_mid_boxes"
        };

        // Act
        bool wasRepaired = TacticalOrderMaterializer.ValidateAndRepairOrders(
            plan,
            CsTeam.Terrorist,
            _mapProfileManager,
            logger: null,
            decisionId: "DEC-TEST-01");

        // Assert
        Assert.True(wasRepaired);
        Assert.Contains("b", plan.BotOrders["bot_entry"].StagingSpotId, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("b", plan.BotOrders["bot_rotator"].StagingSpotId, StringComparison.OrdinalIgnoreCase);
        Assert.Equal("tr_exec_b_site_plant", plan.BotOrders["bot_rotator"].ExecuteSpotId);
    }

    [Fact]
    public void Test4_ExplicitLurkerMayUseDifferentRoute()
    {
        // Act
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Execução B (Tapete / Apartamentos Rápido)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        // Assert: Anchor (Lurker) atua em Underpass/Mid para cortar rotações, o que é taticamente válido
        Assert.True(orders.ContainsKey("bot_anchor"));
        Assert.Equal("Underpass", orders["bot_anchor"].TargetArea);
        Assert.Equal("tr_staging_underpass_top", orders["bot_anchor"].StagingSpotId);
    }

    [Fact]
    public void Test5_MolotovMaySuspendRush()
    {
        // Arrange
        var plan = new TacticalPlan { TacticRevision = 1 };
        int prevRev = plan.TacticRevision;
        var affectedSlots = new List<int> { 2, 3 };

        // Act
        plan.TacticRevision++;
        int newRev = plan.TacticRevision;

        // Assert
        Assert.Equal(1, prevRev);
        Assert.Equal(2, newRev);
        Assert.Equal(2, affectedSlots.Count);
    }

    [Fact]
    public void Test6_EnemyContactMayPauseEntry()
    {
        // Arrange
        var plan = new TacticalPlan { TacticRevision = 1 };
        var order = new BotTacticalOrder
        {
            Stance = EngagementStance.AGGRESSIVE_POKE,
            MidRoundAction = MidRoundAction.NORMAL
        };

        // Act: Contato com inimigo altera postura temporária para troca de tiro/combate
        order.MidRoundAction = MidRoundAction.JIGGLE_PEEK;
        order.Stance = EngagementStance.JIGGLE_INFO;
        plan.TacticRevision++;

        // Assert
        Assert.Equal(EngagementStance.JIGGLE_INFO, order.Stance);
        Assert.Equal(MidRoundAction.JIGGLE_PEEK, order.MidRoundAction);
        Assert.Equal(2, plan.TacticRevision);
    }

    [Fact]
    public void Test7_AdaptationIncrementsTacticRevision()
    {
        // Arrange
        var plan = new TacticalPlan
        {
            TacticName = "Execução B",
            TacticRevision = 1
        };

        // Act
        int initialRev = plan.TacticRevision;
        plan.ApplyPivotRevision(
            newTacticName: "Pivô Conector -> A",
            newTargetSite: "A",
            changeReason: "MolotovBlocked em B",
            triggeringEvent: "MolotovDetonated",
            gameTick: 1200,
            roundTime: "01:25",
            confidence: 0.85f);

        // Assert
        Assert.Equal(1, initialRev);
        Assert.Equal(2, plan.TacticRevision);
        Assert.Equal("A", plan.CurrentTargetSite);
        Assert.Equal("Pivô Conector -> A", plan.CurrentTactic);
    }

    [Fact]
    public void Test8_CurrentIntentDoesNotShowOldOutcome()
    {
        // Arrange
        var tracker = new MovementExecutionTracker();
        int slot = 2;
        var oldIntent = new MovementIntent
        {
            BotSlot = slot,
            Source = MovementIntentSource.TacticalNavigation,
            Kind = MovementCommandKind.HoldStop,
            Reason = "OldHold",
            IsHoldAuthorized = true
        };

        // Registra e conclui uma amostra anterior
        tracker.RecordIntentIssued(slot, 100, 1.0f, oldIntent, new(0, 0, 0));
        tracker.CompleteSample(slot, PhysicalExecutionOutcome.AuthorizedHoldApplied, details: "OldHoldDone", currentVel2D: 0f, disp32: 0f);

        // Nova intenção atual começa
        var currentIntent = new MovementIntent
        {
            BotSlot = slot,
            Source = MovementIntentSource.Unstuck,
            Kind = MovementCommandKind.UsercmdVector,
            Reason = "Recovery_Stage1"
        };
        tracker.RecordIntentIssued(slot, 200, 2.0f, currentIntent, new(0, 0, 0));

        // Act
        var activeSample = tracker.GetActiveSample(slot);
        var latestMeta = tracker.GetLatestDetailedMetadata(slot);

        // Assert
        Assert.NotNull(activeSample);
        Assert.False(activeSample.IsCompleted); // Amostra atual está em andamento (Pending)
        Assert.Equal(MovementIntentSource.Unstuck, activeSample.WinningIntent.Source);

        Assert.NotNull(latestMeta);
        Assert.Equal(PhysicalExecutionOutcome.AuthorizedHoldApplied, latestMeta.Value.Physical);
        Assert.Equal(100, latestMeta.Value.IssuedTick); // O outcome antigo pertence ao tick 100, NÃO à ação atual!
    }

    [Fact]
    public void Test9_RecoverySuccessRequiresPhysicalProgress()
    {
        // Arrange
        var recoverySuccess = new RecoveryAttempt
        {
            Displacement2DAfter = 22.5f,
            Recovered = true
        };
        var recoveryFailed = new RecoveryAttempt
        {
            Displacement2DAfter = 2.1f,
            Recovered = false
        };

        // Act & Assert
        Assert.True(recoverySuccess.Recovered && recoverySuccess.Displacement2DAfter >= 15.0f);
        Assert.False(recoveryFailed.Recovered);
        Assert.True(recoveryFailed.Displacement2DAfter < 15.0f);
    }

    [Fact]
    public void Test10_OverrideEventIsCountedOnce()
    {
        // Arrange
        var tracker = new MovementExecutionTracker();
        int slot = 4;

        var entity = new EntityIdentity(10, 20, 100, 1);
        var postApply1 = new BotStateFingerprint(slot, 1, 100, false, 100, 100, 0, 0f, 0f, 0f, 0f, 0, 0, 0f, 0f, entity);

        // Act
        tracker.StorePostApplyFingerprint(slot, postApply1);

        // V4.2.4: Requer >= 16 ticks consecutivos de alteração persistente para promover a override
        bool override1 = false;
        BotStateFingerprint? lastPre = null;
        for (int i = 1; i <= 16; i++)
        {
            lastPre = new BotStateFingerprint(slot, 1, 100 + i, true, 500, 500, 0, 0f, 0f, 0f, 0f, 0, 0, 0f, 0f, entity);
            override1 = tracker.CheckAndAuditPreTickOverride(slot, lastPre, null, 1.5f + i * 0.015f);
        }

        tracker.StorePostApplyFingerprint(slot, lastPre);
        var preApply3 = new BotStateFingerprint(slot, 1, 120, true, 500, 500, 0, 0f, 0f, 0f, 0f, 0, 0, 0f, 0f, entity);
        bool override2 = tracker.CheckAndAuditPreTickOverride(slot, preApply3, null, 1.8f);

        // Assert
        Assert.True(override1);
        Assert.False(override2); // Segundo tick após alinhamento não cria outro evento único!
        Assert.Equal(1, tracker.UniqueOverrideEventsCount);
    }
}
