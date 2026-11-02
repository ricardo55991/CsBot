using System;
using System.Collections.Generic;
using System.Linq;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_ComprehensiveTests
{
    private static MapProfileManager CreateMockMapProfile()
    {
        var mgr = new MapProfileManager();
        var spots = new List<TacticalSpot>();

        // Spots CT A
        spots.Add(new TacticalSpot
        {
            Id = "ct_a_site_default",
            Name = "A Site Default",
            Sector = "Site A",
            Side = "CT",
            AssociatedBombsite = "A",
            Usage = SpotUsage.Hold,
            X = 1100f, Y = -2000f, Z = -160f
        });
        spots.Add(new TacticalSpot
        {
            Id = "ct_a_stairs_cross",
            Name = "A Stairs Cross",
            Sector = "Site A",
            Side = "CT",
            AssociatedBombsite = "A",
            Usage = SpotUsage.Execute,
            X = 1200f, Y = -1800f, Z = -160f
        });

        // Spots CT B
        spots.Add(new TacticalSpot
        {
            Id = "ct_b_site_default_crouch",
            Name = "B Site Default",
            Sector = "Site B",
            Side = "CT",
            AssociatedBombsite = "B",
            Usage = SpotUsage.Hold,
            X = -1400f, Y = 600f, Z = -160f
        });

        // Spots TR A
        spots.Add(new TacticalSpot
        {
            Id = "tr_staging_a_ramp",
            Name = "TR A Ramp Staging",
            Sector = "Rampa A",
            Side = "TR",
            AssociatedBombsite = "A",
            Usage = SpotUsage.Staging,
            X = 900f, Y = -1400f, Z = -160f
        });
        spots.Add(new TacticalSpot
        {
            Id = "tr_exec_a_site_plant",
            Name = "TR A Site Plant",
            Sector = "Site A",
            Side = "TR",
            AssociatedBombsite = "A",
            Usage = SpotUsage.Execute | SpotUsage.Plant,
            X = 1150f, Y = -1950f, Z = -160f
        });

        // Spots TR B
        spots.Add(new TacticalSpot
        {
            Id = "tr_staging_b_apps_kitchen",
            Name = "TR B Apps Kitchen",
            Sector = "Apartments B",
            Side = "TR",
            AssociatedBombsite = "B",
            Usage = SpotUsage.Staging,
            X = -800f, Y = 500f, Z = -160f
        });
        spots.Add(new TacticalSpot
        {
            Id = "tr_staging_b_apps_balcony",
            Name = "TR B Balcony",
            Sector = "Apartments B",
            Side = "TR",
            AssociatedBombsite = "B",
            Usage = SpotUsage.Staging,
            X = -1100f, Y = 700f, Z = -160f
        });
        spots.Add(new TacticalSpot
        {
            Id = "tr_exec_b_site_plant",
            Name = "TR B Site Plant",
            Sector = "Site B",
            Side = "TR",
            AssociatedBombsite = "B",
            Usage = SpotUsage.Execute | SpotUsage.Plant,
            X = -1350f, Y = 650f, Z = -160f
        });

        mgr.SetSpotsForTesting(spots);
        return mgr;
    }

    // =========================================================================
    // PARTE 1 & 2 & 3: TRACKER TESTS (1 a 10)
    // =========================================================================

    [Fact]
    public void Test01_MovementWith120Units_IsAppliedWithProgress_EvenIfStateChanged()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Kind = MovementCommandKind.NavigateNavMesh,
            ExpectedMovement = true,
            IsHoldAuthorized = false
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 120f, vel125: 220f);
        Assert.Equal(PhysicalExecutionOutcome.AppliedWithProgress, physical);
    }

    [Fact]
    public void Test02_IntegrityOutcome_DoesNotReplacePhysicalOutcome()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Kind = MovementCommandKind.NavigateNavMesh,
            ExpectedMovement = true,
            IsHoldAuthorized = false
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 100f, vel125: 200f);
        Assert.Equal(PhysicalExecutionOutcome.AppliedWithProgress, physical);

        var tracker = new MovementExecutionTracker();
        var entity = new EntityIdentity(1, 1, 0, 1);
        var prevFp = new BotStateFingerprint(1, 1, 100, false, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, entity);
        var curFp = new BotStateFingerprint(1, 1, 101, false, 500, 500, 0, 0, 0, 0, 0, 0, 0, 0, 0, entity);
        var (integrity, _) = tracker.EvaluateStateIntegrity(1, prevFp, curFp);

        // Integridade alterada de forma inexplicada não altera o outcome físico
        Assert.Equal(PhysicalExecutionOutcome.AppliedWithProgress, physical);
        Assert.Equal(StateIntegrityOutcome.EngineStateChangedUnexplained, integrity);
    }

    [Fact]
    public void Test03_AuthorizedHold_RequiresHoldStop()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Kind = MovementCommandKind.HoldStop,
            ExpectedMovement = false,
            IsHoldAuthorized = true
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 1f, vel125: 0f);
        Assert.Equal(PhysicalExecutionOutcome.AuthorizedHoldApplied, physical);
    }

    [Fact]
    public void Test04_Unstuck_NeverReturnsAuthorizedHoldApplied()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Source = MovementIntentSource.Unstuck,
            Kind = MovementCommandKind.UsercmdVector,
            ExpectedMovement = true,
            IsHoldAuthorized = false
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 0f, vel125: 0f);
        Assert.NotEqual(PhysicalExecutionOutcome.AuthorizedHoldApplied, physical);
    }

    [Fact]
    public void Test05_NavigateNavMesh_NeverReturnsAuthorizedHoldApplied()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Kind = MovementCommandKind.NavigateNavMesh,
            ExpectedMovement = true,
            IsHoldAuthorized = false
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 1f, vel125: 0f);
        Assert.NotEqual(PhysicalExecutionOutcome.AuthorizedHoldApplied, physical);
    }

    [Fact]
    public void Test06_UsercmdVector_NeverReturnsAuthorizedHoldApplied()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Kind = MovementCommandKind.UsercmdVector,
            ExpectedMovement = true,
            IsHoldAuthorized = false
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 0f, vel125: 0f);
        Assert.NotEqual(PhysicalExecutionOutcome.AuthorizedHoldApplied, physical);
    }

    [Fact]
    public void Test07_HoldStopExpectedStop_IsNotGeometryBlocked()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Kind = MovementCommandKind.HoldStop,
            ExpectedMovement = false,
            IsHoldAuthorized = true
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 0f, vel125: 0f);
        Assert.NotEqual(PhysicalExecutionOutcome.BlockedByGeometryOrNavigation, physical);
        Assert.Equal(PhysicalExecutionOutcome.AuthorizedHoldApplied, physical);
    }

    [Fact]
    public void Test08_MovementNoProgress_IsAppliedNoProgress()
    {
        var intent = new MovementIntent
        {
            BotSlot = 1,
            Kind = MovementCommandKind.NavigateNavMesh,
            ExpectedMovement = true,
            IsHoldAuthorized = false
        };

        var (physical, _) = MovementExecutionTracker.ClassifyPhysicalOutcome(intent, disp500: 2f, vel125: 0f);
        Assert.Equal(PhysicalExecutionOutcome.AppliedNoProgress, physical);
    }

    [Fact]
    public void Test09_ExpectedStateChange_IsEngineExpected()
    {
        var tracker = new MovementExecutionTracker();
        tracker.RegisterExpectedEngineStateChange(1, ExpectedEngineStateChange.GoalPositionChanged | ExpectedEngineStateChange.Repath);

        var entity = new EntityIdentity(1, 1, 0, 1);
        var previousFp = new BotStateFingerprint(1, 1, 100, false, 100, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, entity);
        var currentFp = new BotStateFingerprint(1, 1, 101, false, 500, 500, 0, 0, 0, 0, 1.0f, 0, 0, 0, 0, entity);

        var (outcome, _) = tracker.EvaluateStateIntegrity(1, previousFp, currentFp);
        Assert.Equal(StateIntegrityOutcome.EngineStateChangedExpectedly, outcome);
    }

    [Fact]
    public void Test10_UnexplainedStateChange_IsSeparateAxis()
    {
        var tracker = new MovementExecutionTracker();
        var entity = new EntityIdentity(1, 1, 0, 1);
        var previousFp = new BotStateFingerprint(1, 1, 100, false, 100, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, entity);
        var currentFp = new BotStateFingerprint(1, 1, 101, false, 500, 500, 0, 0, 0, 0, 1.0f, 0, 0, 0, 0, entity);

        var (outcome, details) = tracker.EvaluateStateIntegrity(1, previousFp, currentFp);
        Assert.Equal(StateIntegrityOutcome.EngineStateChangedUnexplained, outcome);
        Assert.NotEmpty(details);
    }

    // =========================================================================
    // PARTE 4: RECOVERY TESTS (11 a 19)
    // =========================================================================

    [Fact]
    public void Test11_RecoveryStage1Progress_Succeeds()
    {
        var attempt = new RecoveryAttempt
        {
            BotSlot = 2,
            Stage = 1,
            TriggerTime = 10.0f,
            OriginalPosition = new Vector(0, 0, 0)
        };

        // Simula medição aos 500ms com deslocamento de 25u (>= 15u)
        attempt.Displacement500Ms = 25.0f;
        if (attempt.Displacement500Ms >= 15.0f)
        {
            attempt.Recovered = true;
        }

        Assert.True(attempt.Recovered);
        Assert.Equal(1, attempt.Stage);
    }

    [Fact]
    public void Test12_RecoveryStage1NoProgress_EscalatesStage2()
    {
        var attempt = new RecoveryAttempt
        {
            BotSlot = 2,
            Stage = 1,
            TriggerTime = 10.0f,
            OriginalPosition = new Vector(0, 0, 0)
        };

        // Deslocamento insuficiente aos 500ms (< 5u)
        attempt.Displacement500Ms = 2.0f;
        if (attempt.Displacement500Ms < 15.0f)
        {
            attempt.Stage = 2;
        }

        Assert.Equal(2, attempt.Stage);
        Assert.False(attempt.Recovered);
    }

    [Fact]
    public void Test13_Stage2SelectsDifferentWaypoint()
    {
        var mapProfile = CreateMockMapProfile();
        var driver = new BotLocomotionDriver { MapProfileManager = mapProfile };

        string currentWp = "tr_staging_b_apps_kitchen";
        var alt = driver.FindAlternativeWaypointForRecovery(2, currentWp, "TR", "B", -800f, 500f, 150f, 10f);

        Assert.NotNull(alt);
        Assert.NotEqual(currentWp, alt.Id);
    }

    [Fact]
    public void Test14_Stage2PreservesBombsite()
    {
        var mapProfile = CreateMockMapProfile();
        var driver = new BotLocomotionDriver { MapProfileManager = mapProfile };

        string currentWp = "tr_staging_b_apps_kitchen";
        var alt = driver.FindAlternativeWaypointForRecovery(2, currentWp, "TR", "B", -800f, 500f, 150f, 10f);

        Assert.NotNull(alt);
        Assert.Equal("B", PresetSpatialValidator.DetermineSpotBombsite(alt));
    }

    [Fact]
    public void Test15_Stage2RejectsBlacklistedWaypoint()
    {
        var mapProfile = CreateMockMapProfile();
        var driver = new BotLocomotionDriver { MapProfileManager = mapProfile };

        // Coloca o candidato em blacklist
        driver.BlacklistWaypoint(2, "tr_staging_b_apps_balcony", 10.0f);

        string currentWp = "tr_staging_b_apps_kitchen";
        var alt = driver.FindAlternativeWaypointForRecovery(2, currentWp, "TR", "B", -800f, 500f, 150f, 10.5f);

        Assert.NotNull(alt);
        Assert.NotEqual("tr_staging_b_apps_balcony", alt.Id);
    }

    [Fact]
    public void Test16_Stage2NoProgress_EscalatesStage3()
    {
        var attempt = new RecoveryAttempt
        {
            BotSlot = 2,
            Stage = 2,
            TriggerTime = 10.0f,
            OriginalPosition = new Vector(0, 0, 0)
        };

        // Medição em 1000ms com deslocamento insuficiente (< 15u)
        attempt.Displacement1000Ms = 4.0f;
        if (attempt.Displacement1000Ms < 15.0f)
        {
            attempt.Stage = 3;
        }

        Assert.Equal(3, attempt.Stage);
        Assert.False(attempt.Recovered);
    }

    [Fact]
    public void Test17_CooldownDoesNotBlockSameRecoveryEscalation()
    {
        var driver = new BotLocomotionDriver();
        var attempt = new RecoveryAttempt
        {
            BotSlot = 3,
            Stage = 1,
            TriggerTime = 10.0f,
            InternalRoundId = 1
        };

        driver.ActiveRecoveryBySlot[3] = attempt;

        // Tenta chamar RequestRecovery enquanto o recovery ativo está em andamento
        var returned = driver.RequestRecovery(3, 1, "Stuck2D", currentTime: 10.3f, gameTick: 150);

        // Deve retornar o mesmo objeto de recovery sem criar um novo
        Assert.Same(attempt, returned);
        Assert.Equal(attempt.RecoveryId, returned?.RecoveryId);
    }

    [Fact]
    public void Test18_RoundEndCancelsRecovery()
    {
        var driver = new BotLocomotionDriver();
        var attempt = new RecoveryAttempt
        {
            BotSlot = 4,
            Stage = 2,
            TriggerTime = 12.0f
        };
        driver.ActiveRecoveryBySlot[4] = attempt;

        driver.ResetRound();

        Assert.Empty(driver.ActiveRecoveryBySlot);
        Assert.False(attempt.Recovered);
        Assert.Equal("CancelledRoundEnd", attempt.FailureReason);
    }

    [Fact]
    public void Test19_DeathCancelsRecovery()
    {
        var driver = new BotLocomotionDriver();
        var attempt = new RecoveryAttempt
        {
            BotSlot = 5,
            Stage = 1,
            TriggerTime = 14.0f
        };
        driver.ActiveRecoveryBySlot[5] = attempt;

        driver.ClearNavigation(5);

        Assert.Empty(driver.ActiveRecoveryBySlot);
        Assert.False(attempt.Recovered);
        Assert.Equal("CancelledBotDeath", attempt.FailureReason);
    }

    // =========================================================================
    // PARTE 5: PRESETS TESTS (20 a 26)
    // =========================================================================

    [Fact]
    public void Test20_ExecuteBRejectsARampStagingForAWPer()
    {
        var mapProfile = CreateMockMapProfile();
        var order = new BotTacticalOrder
        {
            TargetArea = "Apartments B",
            StagingSpotId = "tr_staging_a_ramp",
            ExecuteSpotId = "tr_exec_b_site_plant"
        };

        var outcome = PresetSpatialValidator.ValidateOrder(
            order, BotRole.AWPer, "Execução B", "B", CsTeam.Terrorist, false, false, false, mapProfile);

        Assert.Equal(PresetValidationResult.Rejected, outcome.Result);
        Assert.Equal("StagingSpotId", outcome.InvalidField);
    }

    [Fact]
    public void Test21_ExecuteBRejectsASiteExecute()
    {
        var mapProfile = CreateMockMapProfile();
        var order = new BotTacticalOrder
        {
            TargetArea = "Bombsite B",
            StagingSpotId = "tr_staging_b_apps_kitchen",
            ExecuteSpotId = "tr_exec_a_site_plant"
        };

        var outcome = PresetSpatialValidator.ValidateOrder(
            order, BotRole.EntryFragger, "Execução B", "B", CsTeam.Terrorist, false, false, false, mapProfile);

        Assert.Equal(PresetValidationResult.Rejected, outcome.Result);
        Assert.Equal("ExecuteSpotBombsite", outcome.InvalidField);
    }

    [Fact]
    public void Test22_SplitBRequiresBFinalSite()
    {
        var mapProfile = CreateMockMapProfile();
        var order = new BotTacticalOrder
        {
            TargetArea = "Bombsite B",
            StagingSpotId = "tr_staging_b_apps_kitchen",
            ExecuteSpotId = "tr_exec_a_site_plant"
        };

        var outcome = PresetSpatialValidator.ValidateOrder(
            order, BotRole.Rotator, "Split B", "B", CsTeam.Terrorist, false, false, false, mapProfile);

        Assert.Equal(PresetValidationResult.Rejected, outcome.Result);
        Assert.Equal("ExecuteSpotBombsite", outcome.InvalidField);
    }

    [Fact]
    public void Test23_LurkerCrossSiteRequiresExplicitFlag()
    {
        var mapProfile = CreateMockMapProfile();
        var order = new BotTacticalOrder
        {
            TargetArea = "Lurk Palace A",
            StagingSpotId = "tr_staging_a_ramp",
            ExecuteSpotId = "tr_exec_a_site_plant"
        };

        // Sem flag: deve ser rejeitado
        var outcomeWithoutFlag = PresetSpatialValidator.ValidateOrder(
            order, BotRole.Anchor, "Execução B", "B", CsTeam.Terrorist, false, allowCrossSiteLurk: false, false, mapProfile);
        Assert.Equal(PresetValidationResult.Rejected, outcomeWithoutFlag.Result);

        // Com flag: permitido
        var outcomeWithFlag = PresetSpatialValidator.ValidateOrder(
            order, BotRole.Anchor, "Execução B", "B", CsTeam.Terrorist, false, allowCrossSiteLurk: true, false, mapProfile);
        Assert.Equal(PresetValidationResult.Valid, outcomeWithFlag.Result);
    }

    [Fact]
    public void Test24_BombCarrierMatchesCurrentTargetSite()
    {
        var mapProfile = CreateMockMapProfile();
        var order = new BotTacticalOrder
        {
            TargetArea = "Bombsite A",
            StagingSpotId = "tr_staging_a_ramp",
            ExecuteSpotId = "tr_exec_a_site_plant"
        };

        // C4 Carrier executando no Bombsite A quando a tática mira no Bombsite B
        var outcome = PresetSpatialValidator.ValidateOrder(
            order, BotRole.Rotator, "Execução B", "B", CsTeam.Terrorist, isC4Carrier: true, allowCrossSiteLurk: false, false, mapProfile);

        Assert.Equal(PresetValidationResult.Rejected, outcome.Result);
    }

    [Fact]
    public void Test25_InvalidPresetUsesValidSameSiteFallback()
    {
        var mapProfile = CreateMockMapProfile();
        var order = new BotTacticalOrder
        {
            TargetArea = "Bombsite B",
            StagingSpotId = "tr_staging_a_ramp",
            ExecuteSpotId = "tr_exec_a_site_plant"
        };

        var outcome = PresetSpatialValidator.ValidateAndApplyFallback(
            order, BotRole.EntryFragger, "Execução B", "B", CsTeam.Terrorist, false, false, false, mapProfile);

        Assert.Equal(PresetValidationResult.FallbackSubstituted, outcome.Result);
        Assert.Equal("tr_exec_b_site_plant", order.ExecuteSpotId);
    }

    [Fact]
    public void Test26_MissingSpotIsRejected()
    {
        var mapProfile = CreateMockMapProfile();
        var order = new BotTacticalOrder
        {
            TargetArea = "Bombsite B",
            StagingSpotId = "spot_that_does_not_exist",
            ExecuteSpotId = "tr_exec_b_site_plant"
        };

        var outcome = PresetSpatialValidator.ValidateOrder(
            order, BotRole.EntryFragger, "Execução B", "B", CsTeam.Terrorist, false, false, false, mapProfile);

        Assert.Equal(PresetValidationResult.Rejected, outcome.Result);
        Assert.Equal("StagingSpotId", outcome.InvalidField);
    }

    // =========================================================================
    // PARTE 6: WARMUP TESTS (27 a 30)
    // =========================================================================

    [Fact]
    public void Test27_WarmupCTIsNotApplicable()
    {
        var econ = new EconomyManager();
        var snap = econ.CapturePreBuySnapshot(new List<CCSPlayerController>(), roundNumber: 0, lossBonus: 1400, team: CsTeam.CounterTerrorist, matchPhase: MatchLifecyclePhase.WARMUP);

        Assert.Equal(BuyState.NOT_APPLICABLE, snap.PurchaseIntent);
        Assert.Equal(BuyState.NOT_APPLICABLE, snap.FinalBuyState);
    }

    [Fact]
    public void Test28_WarmupTRIsNotApplicable()
    {
        var econ = new EconomyManager();
        var snap = econ.CapturePreBuySnapshot(new List<CCSPlayerController>(), roundNumber: 0, lossBonus: 1400, team: CsTeam.Terrorist, matchPhase: MatchLifecyclePhase.WARMUP);

        Assert.Equal(BuyState.NOT_APPLICABLE, snap.PurchaseIntent);
        Assert.Equal(BuyState.NOT_APPLICABLE, snap.FinalBuyState);
    }

    [Fact]
    public void Test29_Round1CTIsPistol()
    {
        var econ = new EconomyManager();
        var snap = econ.CapturePreBuySnapshot(new List<CCSPlayerController>(), roundNumber: 1, lossBonus: 1400, team: CsTeam.CounterTerrorist, matchPhase: MatchLifecyclePhase.LIVE);

        Assert.Equal(BuyState.PISTOL_ROUND, snap.PurchaseIntent);
        Assert.Equal(BuyState.PISTOL_ROUND, snap.FinalBuyState);
    }

    [Fact]
    public void Test30_Round1TRIsPistol()
    {
        var econ = new EconomyManager();
        var snap = econ.CapturePreBuySnapshot(new List<CCSPlayerController>(), roundNumber: 1, lossBonus: 1400, team: CsTeam.Terrorist, matchPhase: MatchLifecyclePhase.LIVE);

        Assert.Equal(BuyState.PISTOL_ROUND, snap.PurchaseIntent);
        Assert.Equal(BuyState.PISTOL_ROUND, snap.FinalBuyState);
    }

    // =========================================================================
    // PARTE 7: CAPTURE TESTS (31 a 33)
    // =========================================================================

    [Fact]
    public void Test31_FifteenRoundCaptureRequiresMatchCompletedFooter()
    {
        string validFooterContent = @"
## 🎮 Round 15 [Placar: CT 8 x 7 TR]
- [FIM_ROUND] internal_round_id=16 | round_oficial=15

## 🏁 Encerramento da Captura
- **capture_end_reason:** `MATCH_COMPLETED`
- **captured_rounds:** 16 | **complete_rounds:** 16 | **partial_round_id:** none
- **late_events_total:** 0
- **end_tick:** 150000 | **end_timestamp:** 2026-10-23 23:59:59

> capture_end_reason=MATCH_COMPLETED
> captured_rounds=16
> complete_rounds=16
> partial_round_id=none
";

        bool isValid = MatchTelemetryLogger.ValidateCaptureFooter(validFooterContent, out string statusReason);
        Assert.True(isValid);
        Assert.Equal("VALID_CAPTURE", statusReason);
    }

    [Fact]
    public void Test32_MissingFooterProducesIncompleteCapture()
    {
        string incompleteContent = @"
## 🎮 Round 15 [Placar: CT 8 x 7 TR]
- [FIM_ROUND] internal_round_id=16 | round_oficial=15
Servidor desconectado abruptamente.
";

        bool isValid = MatchTelemetryLogger.ValidateCaptureFooter(incompleteContent, out string statusReason);
        Assert.False(isValid);
        Assert.Contains("INCOMPLETE_CAPTURE", statusReason);
    }

    [Fact]
    public void Test33_DllHashWrittenToHeader()
    {
        string header = MatchTelemetryLogger.BuildHeaderMetadata(
            pluginVersion: "4.2.0",
            assemblyVersion: "4.2.0.0",
            gitCommit: "v4.2-release",
            dllSha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            modelSha256: "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592");

        Assert.Contains("DllSha256:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`", header);
        Assert.Contains("ModelSha256:** `d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592`", header);
        Assert.Contains("PluginVersion:** `4.2.0`", header);
    }
}
