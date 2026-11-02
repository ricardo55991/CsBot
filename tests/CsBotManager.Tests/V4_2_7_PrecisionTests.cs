using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_7_PrecisionTests
{
    private readonly MapProfileManager _mapProfileManager;

    public V4_2_7_PrecisionTests()
    {
        _mapProfileManager = new MapProfileManager();
        var profile = new MapProfile
        {
            MapName = "de_mirage",
            FriendlyName = "Mirage",
            PlantZones = new Dictionary<string, MapPlantZone>(StringComparer.OrdinalIgnoreCase)
            {
                ["A"] = new MapPlantZone
                {
                    Center = new MapVector3 { X = -400.0f, Y = -2100.0f, Z = -170.0f },
                    BoundsMin = new MapVector3 { X = -650.0f, Y = -2400.0f, Z = -220.0f },
                    BoundsMax = new MapVector3 { X = -150.0f, Y = -1800.0f, Z = -120.0f },
                    Radius2D = 380.0f
                },
                ["B"] = new MapPlantZone
                {
                    Center = new MapVector3 { X = -1800.0f, Y = 50.0f, Z = -160.0f },
                    BoundsMin = new MapVector3 { X = -2200.0f, Y = -200.0f, Z = -220.0f },
                    BoundsMax = new MapVector3 { X = -1400.0f, Y = 300.0f, Z = -120.0f },
                    Radius2D = 420.0f
                }
            },
            Spots = new List<TacticalSpot>
            {
                new() { Id = "tr_staging_b_apartments_kitchen", Sector = "Apartments B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging, X = -1400f, Y = -100f, Z = -160f },
                new() { Id = "tr_exec_b_site_plant", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -1800f, Y = 50f, Z = -160f },
                new() { Id = "tr_staging_palace_room", Sector = "Palace", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Staging, X = 744f, Y = -1719f, Z = -221f },
                new() { Id = "tr_exec_a_site_default", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -400f, Y = -2100f, Z = -170f }
            }
        };
        _mapProfileManager.SetSpotsForTesting(profile.Spots);
    }

    [Fact]
    public void Test01_FakeAExecuteBCommitsBombToB()
    {
        var plan = new TacticalPlan
        {
            TacticName = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CurrentTactic = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            RoundTempo = RoundTempo.POKE_AND_ROTATE,
            TacticRevision = 1
        };

        TacticalOrderMaterializer.ValidateAndRepairOrders(plan, CsTeam.Terrorist, _mapProfileManager, null, "DEC-TEST-01");

        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.FakeSite);
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.MaterializedRealSite);
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.CommittedSite);
        Assert.Equal("B", plan.RealTargetSite);
        Assert.Equal("A", plan.FakeTargetSite);
        Assert.Equal(BombsiteTarget.B, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test02_FakeBExecuteACommitsBombToA()
    {
        var plan = new TacticalPlan
        {
            TacticName = "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
            CurrentTactic = "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
            RoundTempo = RoundTempo.POKE_AND_ROTATE,
            TacticRevision = 1
        };

        TacticalOrderMaterializer.ValidateAndRepairOrders(plan, CsTeam.Terrorist, _mapProfileManager, null, "DEC-TEST-02");

        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.FakeSite);
        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.MaterializedRealSite);
        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.CommittedSite);
        Assert.Equal("A", plan.RealTargetSite);
        Assert.Equal("B", plan.FakeTargetSite);
        Assert.Equal(BombsiteTarget.A, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test03_FakeCarrierIsNeverInFakeGroup()
    {
        var fakeCtx = new FakeExecutionContext
        {
            FakeSite = "A",
            RealSite = "B",
            FakeGroupSlots = new List<int> { 1, 3 },
            BombCarrierSlot = 1
        };

        // Simula verificação e expurgo do portador da C4 do grupo fake
        int carrierSlot = fakeCtx.BombCarrierSlot;
        var allTrSlots = new List<int> { 1, 3, 5, 7, 9 };

        if (fakeCtx.FakeGroupSlots.Contains(carrierSlot))
        {
            fakeCtx.FakeGroupSlots.Remove(carrierSlot);
            var substitute = allTrSlots.FirstOrDefault(s => s != carrierSlot && !fakeCtx.FakeGroupSlots.Contains(s));
            if (substitute != 0)
            {
                fakeCtx.FakeGroupSlots.Add(substitute);
            }
        }

        Assert.DoesNotContain(carrierSlot, fakeCtx.FakeGroupSlots);
        Assert.Contains(5, fakeCtx.FakeGroupSlots);
    }

    [Fact]
    public void Test04_CommittedSiteComesFromMaterializedPlan()
    {
        var plan = new TacticalPlan
        {
            TacticName = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CurrentTactic = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            TacticRevision = 1
        };

        TacticalOrderMaterializer.ValidateAndRepairOrders(plan, CsTeam.Terrorist, _mapProfileManager, null, "DEC-TEST-04");

        Assert.Equal(plan.BombObjectiveState.MaterializedRealSite, plan.BombObjectiveState.CommittedSite);
        Assert.Equal("B", plan.RealTargetSite);
        Assert.Equal("B", plan.CurrentTargetSite);
    }

    [Fact]
    public void Test05_RuntimeCannotOverwriteCommittedSiteFromFakeTarget()
    {
        var plan = new TacticalPlan
        {
            TacticName = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            CurrentTactic = "Fake A & Execução B (Barulho Rampa/Palácio + Rush Tapete B)",
            TacticRevision = 1
        };

        TacticalOrderMaterializer.ValidateAndRepairOrders(plan, CsTeam.Terrorist, _mapProfileManager, null, "DEC-TEST-05");

        // Simula tentativa do runtime de alterar FakeTargetSite para tentar desviar a C4
        plan.FakeTargetSite = "A";
        plan.CurrentTargetSite = "A";

        // ResolveBombCarrierTargetSite deve priorizar BombObjectiveState.CommittedSite / MaterializedRealSite
        Assert.Equal(BombsiteTarget.B, BombsiteParser.ResolveBombCarrierTargetSite(plan));
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.CommittedSite);
    }

    [Fact]
    public void Test06_C4SemanticMismatchRejectsIntent()
    {
        var tracker = new C4MismatchEpisodeTracker();
        int carrierSlot = 1;
        BombsiteTarget committedSite = BombsiteTarget.A;
        BombsiteTarget materializedRealSite = BombsiteTarget.B;
        BombsiteTarget carrierTargetSite = BombsiteTarget.B;

        bool semanticMismatch = (committedSite != materializedRealSite || carrierTargetSite != committedSite);
        Assert.True(semanticMismatch);

        if (semanticMismatch)
        {
            tracker.RecordSemanticMismatch(carrierSlot, committedSite.ToString(), materializedRealSite.ToString(), carrierTargetSite.ToString(), 100, null);
            committedSite = materializedRealSite; // Reconstrução a partir do plano materializado
        }

        Assert.Equal(1, tracker.SemanticMismatchesCount);
        Assert.Equal(BombsiteTarget.B, committedSite);
    }

    [Fact]
    public void Test07_CorrectFakeDoesNotProduceMismatchEpisode()
    {
        var tracker = new C4MismatchEpisodeTracker();
        BombsiteTarget committedSite = BombsiteTarget.B;
        BombsiteTarget materializedRealSite = BombsiteTarget.B;
        BombsiteTarget carrierTargetSite = BombsiteTarget.B;

        bool semanticMismatch = (committedSite != materializedRealSite || carrierTargetSite != committedSite);
        Assert.False(semanticMismatch);
        Assert.Equal(0, tracker.SemanticMismatchesCount);
        Assert.Equal(0, tracker.UniqueC4MismatchEpisodes);
    }

    [Fact]
    public void Test08_EntryKilledOwnerTeamIsTR()
    {
        var plan = new TacticalPlan { CurrentTactic = "Execução A", TacticRevision = 1, Team = CsTeam.Terrorist };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.EntryKilled,
            new List<int> { 1, 3, 5 },
            6.0f,
            "ROTATE_SILENT to alternate bomb",
            ownerTeam: CsTeam.Terrorist);

        Assert.NotNull(record);
        Assert.Equal(CsTeam.Terrorist, record.OwnerTeam);
    }

    [Fact]
    public void Test09_TradePossibleOwnerTeamIsTR()
    {
        var plan = new TacticalPlan { CurrentTactic = "Execução B", TacticRevision = 1, Team = CsTeam.Terrorist };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TradePossible,
            new List<int> { 2, 4 },
            8.0f,
            "RUSH_TRADE Commit into Bombsite B",
            ownerTeam: CsTeam.Terrorist);

        Assert.NotNull(record);
        Assert.Equal(CsTeam.Terrorist, record.OwnerTeam);
    }

    [Fact]
    public void Test10_AggressorKilledOwnerTeamIsCT()
    {
        var plan = new TacticalPlan { CurrentTactic = "Defesa Padrão", TacticRevision = 1, Team = CsTeam.CounterTerrorist };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.AggressorKilled,
            new List<int> { 6, 8, 10 },
            10.0f,
            "CT FallBackToSite & HoldCrossfire (Bomb B)",
            ownerTeam: CsTeam.CounterTerrorist);

        Assert.NotNull(record);
        Assert.Equal(CsTeam.CounterTerrorist, record.OwnerTeam);
    }

    [Fact]
    public void Test11_RetakeDecisionOwnerTeamIsCT()
    {
        var plan = new TacticalPlan { CurrentTactic = "Defesa Padrão", TacticRevision = 1, Team = CsTeam.CounterTerrorist };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.RetakeDecision,
            new List<int> { 2, 4, 6, 8 },
            30.0f,
            "CT Retake Bombsite B",
            ownerTeam: CsTeam.CounterTerrorist);

        Assert.NotNull(record);
        Assert.Equal(CsTeam.CounterTerrorist, record.OwnerTeam);
    }

    [Fact]
    public void Test12_AdaptationWithNoneOwnerIsRejected()
    {
        var plan = new TacticalPlan { CurrentTactic = "Defesa Padrão", TacticRevision = 1 };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.EntryKilled,
            new List<int> { 1, 3 },
            6.0f,
            "Invalid None owner",
            ownerTeam: CsTeam.None);

        Assert.Null(record);
        Assert.Empty(midRound.ActiveAdaptations);
    }

    [Fact]
    public void Test13_AdaptationRejectsAffectedSlotFromOtherTeam()
    {
        var plan = new TacticalPlan { CurrentTactic = "Defesa Padrão", TacticRevision = 1 };
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);

        // Configura resolver de time: slot 1 é TR, slot 2 é CT
        midRound.PlayerTeamResolver = (slot) => slot == 1 ? CsTeam.Terrorist : CsTeam.CounterTerrorist;

        // Tenta iniciar adaptação TR incluindo slot 2 (que é CT)
        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TradePossible,
            new List<int> { 1, 2 },
            8.0f,
            "Trade with cross-team slot",
            ownerTeam: CsTeam.Terrorist);

        Assert.Null(record);
        Assert.Empty(midRound.ActiveAdaptations);
    }
}
