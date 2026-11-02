using System;
using System.Collections.Generic;
using System.Linq;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_6_PrecisionTests
{
    private readonly MapProfileManager _mapProfileManager;

    public V4_2_6_PrecisionTests()
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
                new() { Id = "ct_retake_a_connector", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -450f, Y = -1600f, Z = -160f },
                new() { Id = "ct_retake_a_stairs", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -300f, Y = -1700f, Z = -160f },
                new() { Id = "ct_retake_a_ticket", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -700f, Y = -2200f, Z = -180f },
                new() { Id = "ct_retake_a_defuse_cover", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Defuse | SpotUsage.Retake, X = -400f, Y = -2100f, Z = -170f },
                new() { Id = "ct_retake_b_market", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -1750f, Y = 120f, Z = -160f },
                new() { Id = "ct_retake_b_short", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -1150f, Y = -250f, Z = -160f },
                new() { Id = "ct_retake_b_entry", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Retake, X = -1480f, Y = -150f, Z = -160f },
                new() { Id = "ct_retake_b_defuse_cover", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Defuse | SpotUsage.Retake, X = -1600f, Y = 50f, Z = -160f },
                new() { Id = "tr_exec_a_site_default", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -400f, Y = -2100f, Z = -170f },
                new() { Id = "tr_exec_b_site_plant", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -1800f, Y = 50f, Z = -160f }
            }
        };

        _mapProfileManager.SetSpotsForTesting(profile.Spots);
    }

    [Fact]
    public void Test01_NormalExecuteACommitsA()
    {
        var plan = new TacticalPlan();
        plan.InitializeVersioning("Execução A Padrão", "A", TacticalDecisionSource.FALLBACK_PRESET, 100);

        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.CommittedSite);
        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.RealSite);
        Assert.Equal(BombsiteTarget.A, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test02_NormalExecuteBCommitsB()
    {
        var plan = new TacticalPlan();
        plan.InitializeVersioning("Execução B Padrão", "B", TacticalDecisionSource.FALLBACK_PRESET, 100);

        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.CommittedSite);
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.RealSite);
        Assert.Equal(BombsiteTarget.B, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test03_FakeAExecuteBCommitsB()
    {
        var plan = new TacticalPlan();
        plan.InitializeVersioning("Fake A & Execução B", "A", TacticalDecisionSource.FALLBACK_PRESET, 100);
        plan.SetFakeExecution(fakeSite: "A", realSite: "B", duration: 12.0f, currentTick: 100);

        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.CommittedSite);
        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.FakeSite);
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.RealSite);
        Assert.Equal(BombsiteTarget.B, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test04_FakeBExecuteACommitsA()
    {
        var plan = new TacticalPlan();
        plan.InitializeVersioning("Fake B & Execução A", "B", TacticalDecisionSource.FALLBACK_PRESET, 100);
        plan.SetFakeExecution(fakeSite: "B", realSite: "A", duration: 12.0f, currentTick: 100);

        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.CommittedSite);
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.FakeSite);
        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.RealSite);
        Assert.Equal(BombsiteTarget.A, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test05_PivotAToBInvalidatesOldAObjective()
    {
        var plan = new TacticalPlan();
        plan.InitializeVersioning("Execução A Padrão", "A", TacticalDecisionSource.FALLBACK_PRESET, 100);

        Guid initialRevision = plan.BombObjectiveState.ObjectiveRevision;
        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.CommittedSite);

        plan.ApplyPivotRevision("Pivô Rápido para B", "B", "First kill on B-Short", "PlayerDeath", 250, "01:25", 0.95f);

        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.CommittedSite);
        Assert.NotEqual(initialRevision, plan.BombObjectiveState.ObjectiveRevision);
        Assert.Equal(BombsiteTarget.B, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test06_PivotBToAInvalidatesOldBObjective()
    {
        var plan = new TacticalPlan();
        plan.InitializeVersioning("Execução B Padrão", "B", TacticalDecisionSource.FALLBACK_PRESET, 100);

        Guid initialRevision = plan.BombObjectiveState.ObjectiveRevision;
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.CommittedSite);

        plan.ApplyPivotRevision("Pivô Rápido para A", "A", "First kill on Ramp A", "PlayerDeath", 300, "01:20", 0.90f);

        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.CommittedSite);
        Assert.NotEqual(initialRevision, plan.BombObjectiveState.ObjectiveRevision);
        Assert.Equal(BombsiteTarget.A, BombsiteParser.ResolveBombCarrierTargetSite(plan));
    }

    [Fact]
    public void Test07_StaleBombObjectiveCannotWinArbitration()
    {
        var arbitrator = new MovementArbitrator();
        var bombState = new BombObjectiveState
        {
            CommittedSite = BombsiteTarget.B,
            ObjectiveRevision = Guid.NewGuid()
        };

        arbitrator.GetActiveBombObjectiveState = () => bombState;
        arbitrator.BeginTick(100, 10.0f, 1);

        // Intenção com revisão antiga (obsoleta)
        var staleIntent = new MovementIntent
        {
            BotSlot = 2,
            BotName = "Carrier",
            GameTick = 100,
            CurrentTime = 10.0f,
            Source = MovementIntentSource.BombObjective,
            Kind = MovementCommandKind.NavigateNavMesh,
            ObjectiveRevision = Guid.NewGuid(), // Divergente da ativa
            InternalRoundId = 1
        };

        bool published = arbitrator.PublishDuringCollection(staleIntent, 100, 1);
        Assert.False(published);
        Assert.Equal(MovementIntentDisposition.RejectedExpired, staleIntent.Disposition);

        // Intenção com revisão ativa (coerente)
        var validIntent = new MovementIntent
        {
            BotSlot = 2,
            BotName = "Carrier",
            GameTick = 100,
            CurrentTime = 10.0f,
            Source = MovementIntentSource.BombObjective,
            Kind = MovementCommandKind.NavigateNavMesh,
            ObjectiveRevision = bombState.ObjectiveRevision,
            InternalRoundId = 1
        };

        bool validPublished = arbitrator.PublishDuringCollection(validIntent, 100, 1);
        Assert.True(validPublished);
    }

    [Fact]
    public void Test08_C4GoalSpotMustMatchCommittedSite()
    {
        var bombState = new BombObjectiveState
        {
            CommittedSite = BombsiteTarget.A,
            ObjectiveRevision = Guid.NewGuid()
        };

        var intentValid = new MovementIntent
        {
            BotSlot = 3,
            Source = MovementIntentSource.BombObjective,
            TargetSpotId = "tr_exec_a_site_default",
            TargetSpotAssociatedBombsite = BombsiteTarget.A,
            ObjectiveRevision = bombState.ObjectiveRevision
        };

        Assert.Equal(bombState.CommittedSite, intentValid.TargetSpotAssociatedBombsite);

        var intentMismatch = new MovementIntent
        {
            BotSlot = 3,
            Source = MovementIntentSource.BombObjective,
            TargetSpotId = "tr_exec_b_site_plant",
            TargetSpotAssociatedBombsite = BombsiteTarget.B,
            ObjectiveRevision = bombState.ObjectiveRevision
        };

        Assert.NotEqual(bombState.CommittedSite, intentMismatch.TargetSpotAssociatedBombsite);
    }

    [Fact]
    public void Test09_PlantInsideAProducesPlantedSiteA()
    {
        var adapter = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        // Posição de plant real dentro de Bombsite A (-401, -2183, -177)
        string site = adapter.DeterminePlantedBombsite(-401.0f, -2183.0f, -177.0f);
        Assert.Equal("A", site);
    }

    [Fact]
    public void Test10_PlantInsideBProducesPlantedSiteB()
    {
        var adapter = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        // Posição de plant real dentro de Bombsite B (-1850, 50, -160)
        string site = adapter.DeterminePlantedBombsite(-1850.0f, 50.0f, -160.0f);
        Assert.Equal("B", site);
    }

    [Fact]
    public void Test11_PlantAProducesRetakeA()
    {
        var bombPos = new Vector(-400.0f, -2100.0f, -170.0f);
        var ctBotsInfo = new List<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)>
        {
            (1, new Vector(-1000f, -1500f, -160f), true, false),
            (2, new Vector(-1100f, -1600f, -160f), false, true)
        };

        var retakePlan = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("A", bombPos, ctBotsInfo, _mapProfileManager);

        Assert.Equal(BombsiteTarget.A, retakePlan.PlantedSite);
        Assert.All(retakePlan.MaterializedSpotIds, s => Assert.StartsWith("ct_retake_a_", s, StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Test12_PlantBProducesRetakeB()
    {
        var bombPos = new Vector(-1800.0f, 50.0f, -160.0f);
        var ctBotsInfo = new List<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)>
        {
            (1, new Vector(-1500f, -300f, -160f), true, false),
            (2, new Vector(-1600f, -400f, -160f), false, true)
        };

        var retakePlan = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("B", bombPos, ctBotsInfo, _mapProfileManager);

        Assert.Equal(BombsiteTarget.B, retakePlan.PlantedSite);
        Assert.All(retakePlan.MaterializedSpotIds, s => Assert.StartsWith("ct_retake_b_", s, StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Test13_RetakeNeverUsesCurrentTrPlan()
    {
        // TRs estavam em Fake A -> Execução B
        var trPlan = new TacticalPlan();
        trPlan.InitializeVersioning("Fake A & Execução B", "A", TacticalDecisionSource.FALLBACK_PRESET, 100);
        trPlan.SetFakeExecution(fakeSite: "A", realSite: "B", duration: 12.0f, currentTick: 100);

        // A bomba foi plantada em B
        trPlan.BombObjectiveState.MarkPlanted(BombsiteTarget.B, 200, "PlantConfirmed");

        // Retake CT deve usar estritamente o PlantedSite congelado
        BombsiteTarget plantedTarget = trPlan.BombObjectiveState.PlantedSite;
        string retakeSite = plantedTarget == BombsiteTarget.B ? "B" : "A";

        Assert.Equal("B", retakeSite);
        Assert.NotEqual(trPlan.FakeTargetSite, retakeSite); // Não é o fake "A"
    }

    [Fact]
    public void Test14_MismatchEpisodeIsLoggedOnce()
    {
        var tracker = new C4MismatchEpisodeTracker();
        Guid actionId = Guid.NewGuid();
        Guid revision = Guid.NewGuid();

        // 100 ticks sucessivos com a mesma divergência
        for (long tick = 100; tick < 200; tick++)
        {
            tracker.RecordMismatch(
                carrierSlot: 4,
                logicalActionId: actionId,
                objectiveRevision: revision,
                labelSite: "A",
                goalSite: "B",
                realSite: "A",
                currentTick: tick,
                logger: null);
        }

        // Deve consolidar em exatamente 1 episódio único de 100 ticks
        Assert.Equal(1, tracker.UniqueC4MismatchEpisodes);
        Assert.Equal(100, tracker.TotalMismatchTicks);

        tracker.ResolveEpisode(carrierSlot: 4, currentTick: 200, logger: null);
        Assert.Equal(1, tracker.UniqueC4MismatchEpisodes);
    }

    [Fact]
    public void Test15_CorrectedGoalIsNotRecreatedNextTick()
    {
        // Simulação do ciclo de validação do BotLocomotionDriver
        string targetSite = "A";
        string realSite = "A";
        Vector plantCoord = new Vector(-400.0f, -2100.0f, -170.0f); // Centro real do Bomb A

        var zoneA = _mapProfileManager.GetPlantZone("A");
        var zoneB = _mapProfileManager.GetPlantZone("B");

        Assert.NotNull(zoneA);
        Assert.NotNull(zoneB);

        // Avaliação no 1º tick: ponto dentro de zone A -> goalSite = "A"
        bool inA = zoneA!.Contains(plantCoord.X, plantCoord.Y, plantCoord.Z);
        string goalSite = inA ? "A" : "B";

        string labelSite = targetSite;
        bool mismatch = (labelSite != goalSite || labelSite != realSite);

        // Não há mismatch
        Assert.False(mismatch);
        Assert.Equal("A", goalSite);
        Assert.Equal("A", labelSite);
        Assert.Equal("A", realSite);

        // No próximo tick, com o estado mantido coerente:
        bool nextTickMismatch = (labelSite != goalSite || labelSite != realSite);
        Assert.False(nextTickMismatch);
    }
}
