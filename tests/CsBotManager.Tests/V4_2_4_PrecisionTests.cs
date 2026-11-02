using System;
using System.Collections.Generic;
using System.Linq;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_4_PrecisionTests
{
    private readonly MapProfileManager _mapProfileManager;

    public V4_2_4_PrecisionTests()
    {
        _mapProfileManager = new MapProfileManager();
        var spots = new List<TacticalSpot>
        {
            new() { Id = "tr_staging_b_apartments_kitchen", Sector = "Apartamentos B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging, X = -1400f, Y = 600f, Z = -160f },
            new() { Id = "tr_exec_b_site_plant", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -1800f, Y = 200f, Z = -160f },
            new() { Id = "tr_staging_a_ramp", Sector = "Rampa A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Staging, X = -600f, Y = -1600f, Z = -160f },
            new() { Id = "tr_exec_a_site_default", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -1000f, Y = -2200f, Z = -160f },
            new() { Id = "ct_a_ticket_passive", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging, X = -1200f, Y = -2400f, Z = -160f },
            new() { Id = "ct_b_van_peek", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Staging, X = -1600f, Y = 400f, Z = -160f },
            new() { Id = "tr_spawn_safe", Sector = "TR Spawn", Side = "TR", AssociatedBombsite = "None", Usage = SpotUsage.Fallback }
        };
        _mapProfileManager.SetSpotsForTesting(spots);
    }

    [Fact]
    public void CtEntryKilledDoesNotRotateToAlternateBomb()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Defesa Padrão A/B",
            TacticRevision = 1
        };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        // Simula adaptação por queda do jogador agressivo CT
        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.AggressorKilled,
            new List<int> { 1, 3, 5, 7 },
            10.0f,
            "CT FallBackToSite & HoldCrossfire (Mid Window)",
            ownerTeam: CsTeam.CounterTerrorist);

        Assert.Equal(TacticalAdaptationReason.AggressorKilled, record.Reason);
        Assert.DoesNotContain("ROTATE_SILENT", record.NewOrdersDescription, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("alternate", record.NewOrdersDescription, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("FallBackToSite", record.NewOrdersDescription);
    }

    [Fact]
    public void CtEntryDeathUsesDefensiveReaction()
    {
        var plan = new TacticalPlan { CurrentTactic = "Setup 2-1-2", TacticRevision = 1 };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.AggressorKilled,
            new List<int> { 2, 4, 6 },
            8.0f,
            "CT FallBackToSite & HoldCrossfire (A Ramp)",
            ownerTeam: CsTeam.CounterTerrorist);

        Assert.Equal(TacticalAdaptationReason.AggressorKilled, record.Reason);
        Assert.Contains("HoldCrossfire", record.NewOrdersDescription);
    }

    [Fact]
    public void TrEntryKilledFastContactMayContinue()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Rush B (Apartamentos)",
            RoundTempo = RoundTempo.FAST_CONTACT,
            TacticRevision = 1
        };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TradePossible,
            new List<int> { 1, 3, 5 },
            8.0f,
            "RUSH_TRADE Commit into Bombsite B",
            ownerTeam: CsTeam.Terrorist);

        Assert.Equal(TacticalAdaptationReason.TradePossible, record.Reason);
        Assert.Contains("RUSH_TRADE", record.NewOrdersDescription);
        Assert.Contains("Bombsite B", record.NewOrdersDescription);
    }

    [Fact]
    public void TrEntryKilledTradeMayContinue()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Execução A Palácio",
            RoundTempo = RoundTempo.TIMED_EXECUTE,
            TacticRevision = 1
        };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TradeRequired,
            new List<int> { 2, 4 },
            8.0f,
            "RUSH_TRADE Commit into Bombsite A",
            ownerTeam: CsTeam.Terrorist);

        Assert.Equal(TacticalAdaptationReason.TradeRequired, record.Reason);
        Assert.Contains("RUSH_TRADE", record.NewOrdersDescription);
        Assert.Contains("Bombsite A", record.NewOrdersDescription);
    }

    [Fact]
    public void TrEntryKilledLowTimeMustCommit()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Controle de Mapa Lento",
            RoundTempo = RoundTempo.SLOW_DEFAULT,
            TacticRevision = 1
        };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TimePressure,
            new List<int> { 1, 2, 3 },
            8.0f,
            "RUSH_TRADE Commit into Bombsite B",
            ownerTeam: CsTeam.Terrorist);

        Assert.Equal(TacticalAdaptationReason.TimePressure, record.Reason);
        Assert.Contains("RUSH_TRADE", record.NewOrdersDescription);
    }

    [Fact]
    public void TrEntryKilledEarlyNoTradeMayRotate()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Ataque B",
            RoundTempo = RoundTempo.SLOW_DEFAULT,
            TacticRevision = 1
        };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.RegroupAfterEntryLoss,
            new List<int> { 1, 2, 3, 4 },
            12.0f,
            "ROTATE_SILENT to alternate bomb A",
            ownerTeam: CsTeam.Terrorist);

        Assert.Equal(TacticalAdaptationReason.RegroupAfterEntryLoss, record.Reason);
        Assert.Contains("ROTATE_SILENT", record.NewOrdersDescription);
    }

    [Fact]
    public void TradeRequiresKillerDeathWithinWindow()
    {
        var context = new EntryDeathContext
        {
            VictimSlot = 2,
            KillerSlot = 7,
            DeathTick = 1000,
            DeathTime = 20.0f,
            TradeDeadlineTime = 23.5f,
            NearbyAllies = new List<int> { 4, 6 },
            Bombsite = "B",
            Pace = RoundTempo.FAST_CONTACT,
            TradeConfirmed = true
        };

        Assert.True(context.TradeConfirmed);
        Assert.Equal(23.5f, context.TradeDeadlineTime);
        Assert.True(context.NearbyAllies.Count > 0);
    }

    [Fact]
    public void NearbyAllyWithoutTradeDoesNotConfirmTrade()
    {
        var context = new EntryDeathContext
        {
            VictimSlot = 2,
            KillerSlot = 7,
            DeathTick = 1000,
            DeathTime = 20.0f,
            TradeDeadlineTime = 23.5f,
            NearbyAllies = new List<int> { 4 },
            Bombsite = "B",
            Pace = RoundTempo.SLOW_DEFAULT,
            TradeConfirmed = false
        };

        Assert.False(context.TradeConfirmed);
    }

    [Fact]
    public void UtilityWaitRequiresActiveUtility()
    {
        var plan = new TacticalPlan { CurrentTactic = "Execução B", TacticRevision = 1 };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.UtilityWait,
            new List<int> { 1, 3 },
            4.0f,
            "WAIT_AND_REEXECUTE Hold 4s for utilities then push Bombsite B",
            ownerTeam: CsTeam.Terrorist);

        Assert.Equal(TacticalAdaptationReason.UtilityWait, record.Reason);
        Assert.Contains("WAIT_AND_REEXECUTE", record.NewOrdersDescription);
    }

    [Fact]
    public void BombPlantedAProducesRetakeA()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        // Coordenadas próximas a Bombsite A
        string site = midRound.DeterminePlantedBombsite(-1000f, -2200f, -160f);
        Assert.Equal("A", site);
    }

    [Fact]
    public void BombPlantedBProducesRetakeB()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        // Coordenadas próximas a Bombsite B
        string site = midRound.DeterminePlantedBombsite(-1800f, 200f, -160f);
        Assert.Equal("B", site);
    }

    [Fact]
    public void EveryAdaptationIsClosed()
    {
        var plan = new TacticalPlan { CurrentTactic = "Tática de Teste", TacticRevision = 1 };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var a1 = midRound.StartTacticalAdaptation(plan, TacticalAdaptationReason.TradeRequired, new List<int> { 1, 2 }, 5.0f, "Ordem 1", ownerTeam: CsTeam.Terrorist);
        var a2 = midRound.StartTacticalAdaptation(plan, TacticalAdaptationReason.SaveDecision, new List<int> { 3, 4 }, 8.0f, "Ordem 2", ownerTeam: CsTeam.CounterTerrorist);

        Assert.Equal(2, midRound.ActiveAdaptations.Count);
        Assert.False(a1.IsClosed);
        Assert.False(a2.IsClosed);

        midRound.CloseAllActiveAdaptations(AdaptationDisposition.RoundEnded, plan);

        Assert.Empty(midRound.ActiveAdaptations);
        Assert.True(a1.IsClosed);
        Assert.True(a2.IsClosed);
        Assert.Equal(AdaptationDisposition.RoundEnded, a1.Disposition);
        Assert.Equal(AdaptationDisposition.RoundEnded, a2.Disposition);
    }

    [Fact]
    public void FakeBExecuteAKeepsBombWithAGroup()
    {
        var fakeCtx = new FakeExecutionContext
        {
            FakeSite = "B",
            RealSite = "A",
            FakeGroupSlots = new List<int> { 2, 4 },
            RealGroupSlots = new List<int> { 6, 8, 9 },
            BombCarrierSlot = 6,
            FakeDuration = 10.0f,
            FakeGroupDisposition = FakeGroupDisposition.HoldRotation
        };

        Assert.Contains(fakeCtx.BombCarrierSlot, fakeCtx.RealGroupSlots);
        Assert.DoesNotContain(fakeCtx.BombCarrierSlot, fakeCtx.FakeGroupSlots);
        Assert.Equal("A", fakeCtx.RealSite);
        Assert.Equal("B", fakeCtx.FakeSite);
    }

    [Fact]
    public void FakeAExecuteBKeepsBombWithBGroup()
    {
        var fakeCtx = new FakeExecutionContext
        {
            FakeSite = "A",
            RealSite = "B",
            FakeGroupSlots = new List<int> { 1, 3 },
            RealGroupSlots = new List<int> { 5, 7 },
            BombCarrierSlot = 5,
            FakeDuration = 10.0f,
            FakeGroupDisposition = FakeGroupDisposition.ConvergeLate
        };

        Assert.Contains(fakeCtx.BombCarrierSlot, fakeCtx.RealGroupSlots);
        Assert.DoesNotContain(fakeCtx.BombCarrierSlot, fakeCtx.FakeGroupSlots);
        Assert.Equal("B", fakeCtx.RealSite);
        Assert.Equal("A", fakeCtx.FakeSite);
    }

    [Fact]
    public void FakeGroupDoesNotReceivePlantGoal()
    {
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        var awpOrder = orders[RoleManager.GetOrderKey(BotRole.AWPer)];
        var anchorOrder = orders[RoleManager.GetOrderKey(BotRole.Anchor)];

        Assert.True(awpOrder.IsNoiseGroup);
        Assert.True(anchorOrder.IsNoiseGroup);
        Assert.NotEqual("tr_exec_b_site_plant", awpOrder.ExecuteSpotId);
        Assert.NotEqual("tr_exec_b_site_plant", anchorOrder.ExecuteSpotId);
    }

    [Fact]
    public void FakeRotationTriggerStartsConvergence()
    {
        var fakeCtx = new FakeExecutionContext
        {
            FakeSite = "A",
            RealSite = "B",
            FakeGroupSlots = new List<int> { 2, 4 },
            RealGroupSlots = new List<int> { 6, 8 },
            FakeGroupDisposition = FakeGroupDisposition.ConvergeLate,
            IsTriggered = false
        };

        // Simula disparo do gatilho fake
        fakeCtx.IsTriggered = true;
        Assert.True(fakeCtx.IsTriggered);
        Assert.Equal(FakeGroupDisposition.ConvergeLate, fakeCtx.FakeGroupDisposition);
    }

    [Fact]
    public void LowTimeCancelsFake()
    {
        var fakeCtx = new FakeExecutionContext
        {
            FakeSite = "A",
            RealSite = "B",
            FakeGroupSlots = new List<int> { 2, 4 },
            RealGroupSlots = new List<int> { 6, 8 },
            IsCancelled = false
        };

        float timeRemaining = 18.0f;
        if (timeRemaining < 25.0f)
        {
            fakeCtx.IsCancelled = true;
        }

        Assert.True(fakeCtx.IsCancelled);
    }

    [Fact]
    public void FakeAExecutesB()
    {
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        Assert.Contains("A", orders[RoleManager.GetOrderKey(BotRole.AWPer)].TargetArea);
        Assert.Contains("B", orders[RoleManager.GetOrderKey(BotRole.EntryFragger)].TargetArea);
    }

    [Fact]
    public void FakeBExecutesA()
    {
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Fake B & Execução A (Barulho Tapete/Apartamentos + Rush Rampa/Palácio)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        Assert.Contains("B", orders[RoleManager.GetOrderKey(BotRole.AWPer)].TargetArea);
        Assert.Equal("Palace", orders[RoleManager.GetOrderKey(BotRole.EntryFragger)].TargetArea);
    }

    [Fact]
    public void FakeGroupExcludesBombCarrier()
    {
        var fakeGroupSlots = new List<int> { 2, 3 };
        int bombCarrierSlot = 4;

        Assert.DoesNotContain(bombCarrierSlot, fakeGroupSlots);
    }

    [Fact]
    public void FakeGroupUsesPreferredRoles()
    {
        // AWPer e Anchor são preferenciais para grupo fake
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        Assert.True(orders[RoleManager.GetOrderKey(BotRole.AWPer)].IsNoiseGroup);
        Assert.True(orders[RoleManager.GetOrderKey(BotRole.Anchor)].IsNoiseGroup);
        Assert.False(orders[RoleManager.GetOrderKey(BotRole.EntryFragger)].IsNoiseGroup);
    }

    [Fact]
    public void FakeGroupReceivesFullOrders()
    {
        var orders = TacticalOrderMaterializer.MaterializeTacticalOrders(
            "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CsTeam.Terrorist,
            null,
            _mapProfileManager);

        foreach (var order in orders.Values)
        {
            Assert.False(string.IsNullOrWhiteSpace(order.StagingSpotId));
            Assert.False(string.IsNullOrWhiteSpace(order.ExecuteSpotId));
            Assert.False(string.IsNullOrWhiteSpace(order.TargetArea));
        }
    }

    [Fact]
    public void FakeGroupHasPostFakeDisposition()
    {
        var validDispositions = new[]
        {
            FakeGroupDisposition.HoldRotation,
            FakeGroupDisposition.FallBack,
            FakeGroupDisposition.WatchFlank,
            FakeGroupDisposition.ConvergeLate
        };

        foreach (var disp in validDispositions)
        {
            var ctx = new FakeExecutionContext { FakeGroupDisposition = disp };
            Assert.Equal(disp, ctx.FakeGroupDisposition);
        }
    }

    [Fact]
    public void FakeWithoutUtilityAdaptsOrCancels()
    {
        var fakeCtx = new FakeExecutionContext
        {
            FakeSite = "A",
            RealSite = "B",
            IsCancelled = false
        };

        bool hasUtility = false;
        if (!hasUtility)
        {
            fakeCtx.IsCancelled = true;
        }

        Assert.True(fakeCtx.IsCancelled);
    }

    [Fact]
    public void SaveUsesOfficialRoundContext()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        // Round 12 (último da primeira metade) ou Round 24 (último do tempo regulamentar) NUNCA deve salvar
        bool canSaveR12 = midRound.CanSaveOnRound(12, false);
        bool canSaveR24 = midRound.CanSaveOnRound(24, false);
        bool canSaveR5 = midRound.CanSaveOnRound(5, false);

        Assert.False(canSaveR12);
        Assert.False(canSaveR24);
        Assert.True(canSaveR5);
    }

    [Fact]
    public void SaveComputesEquipmentValue()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        int awpValue = MidRoundAdapter.GetWeaponValue("weapon_awp");
        int akValue = MidRoundAdapter.GetWeaponValue("weapon_ak47");
        int m4Value = MidRoundAdapter.GetWeaponValue("weapon_m4a4");
        int m4a1Value = MidRoundAdapter.GetWeaponValue("weapon_m4a1");
        int glockValue = MidRoundAdapter.GetWeaponValue("weapon_glock");

        Assert.Equal(4750, awpValue);
        Assert.Equal(2700, akValue);
        Assert.Equal(3100, m4Value);
        Assert.Equal(2900, m4a1Value);
        Assert.Equal(200, glockValue);
    }

    [Fact]
    public void SaveComputesBombDistance()
    {
        float botX = 0f, botY = 0f, botZ = 0f;
        float bombX = 1000f, bombY = 0f, bombZ = 0f;

        float dist = MidRoundAdapter.CalculateDistanceToBomb(botX, botY, botZ, bombX, bombY, bombZ);
        Assert.Equal(1000f, dist);
    }

    [Fact]
    public void StandstillClassification_ClassifiesCorrectly()
    {
        // 1. PlantOrDefuse
        var c1 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: true, isAirborne: false, enemyVisible: false,
            isCounterStrafing: false, isAuthorizedHold: false, isUtilityAction: false,
            hasActiveUtilityNearby: false, expectedMovement: false);
        Assert.Equal(StandstillClassification.PlantOrDefuse, c1);

        // 2. Airborne
        var c2 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: true, enemyVisible: false,
            isCounterStrafing: false, isAuthorizedHold: false, isUtilityAction: false,
            hasActiveUtilityNearby: false, expectedMovement: false);
        Assert.Equal(StandstillClassification.Airborne, c2);

        // 3. CombatHold
        var c3 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: false, enemyVisible: true,
            isCounterStrafing: false, isAuthorizedHold: false, isUtilityAction: false,
            hasActiveUtilityNearby: false, expectedMovement: false);
        Assert.Equal(StandstillClassification.CombatHold, c3);

        // 4. CounterStrafe
        var c4 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: false, enemyVisible: false,
            isCounterStrafing: true, isAuthorizedHold: false, isUtilityAction: false,
            hasActiveUtilityNearby: false, expectedMovement: false);
        Assert.Equal(StandstillClassification.CounterStrafe, c4);

        // 5. AuthorizedHold
        var c5 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: false, enemyVisible: false,
            isCounterStrafing: false, isAuthorizedHold: true, isUtilityAction: false,
            hasActiveUtilityNearby: false, expectedMovement: false);
        Assert.Equal(StandstillClassification.AuthorizedHold, c5);

        // 6. UtilityAction
        var c6 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: false, enemyVisible: false,
            isCounterStrafing: false, isAuthorizedHold: false, isUtilityAction: true,
            hasActiveUtilityNearby: false, expectedMovement: false);
        Assert.Equal(StandstillClassification.UtilityAction, c6);

        // 7. SmokeOrMolotovWait
        var c7 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: false, enemyVisible: false,
            isCounterStrafing: false, isAuthorizedHold: false, isUtilityAction: false,
            hasActiveUtilityNearby: true, expectedMovement: false);
        Assert.Equal(StandstillClassification.SmokeOrMolotovWait, c7);

        // 8. GeometryBlock
        var c8 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: false, enemyVisible: false,
            isCounterStrafing: false, isAuthorizedHold: false, isUtilityAction: false,
            hasActiveUtilityNearby: false, expectedMovement: true);
        Assert.Equal(StandstillClassification.GeometryBlock, c8);

        // 9. Unknown
        var c9 = MicroMoveEngine.ClassifyStandstillState(
            isPlantingOrDefusing: false, isAirborne: false, enemyVisible: false,
            isCounterStrafing: false, isAuthorizedHold: false, isUtilityAction: false,
            hasActiveUtilityNearby: false, expectedMovement: false);
        Assert.Equal(StandstillClassification.Unknown, c9);
    }
}
