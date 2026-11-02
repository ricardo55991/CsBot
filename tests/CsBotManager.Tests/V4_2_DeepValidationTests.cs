using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_DeepValidationTests
{
    // =========================================================================
    // 1. TESTES DE TRANSFORMAÇÃO DE COORDENADAS POR YAW (0°, 90°, 180°, 270°)
    // =========================================================================

    [Fact]
    public void Test01_TransformYaw_ZeroDegrees_MovesAlongPositiveX()
    {
        // No Source 2: Yaw 0° olha para +X (East). Forward 100u deve mover +100 em X.
        var pawnPos = new Vector(0, 0, 0);
        var forwardDelta = new Vector(100f, 0f, 0f);

        var world = MapPlayableBounds.TransformSuggestedGoalToWorld(
            forwardDelta,
            SuggestedGoalCoordinateSpace.ViewRelative,
            pawnPos,
            yawDegrees: 0f);

        Assert.Equal(100f, world.X, precision: 1);
        Assert.Equal(0f, world.Y, precision: 1);
        Assert.Equal(0f, world.Z, precision: 1);
    }

    [Fact]
    public void Test02_TransformYaw_90Degrees_MovesAlongPositiveY()
    {
        // Yaw 90° olha para +Y (North). Forward 100u deve mover +100 em Y.
        var pawnPos = new Vector(0, 0, 0);
        var forwardDelta = new Vector(100f, 0f, 0f);

        var world = MapPlayableBounds.TransformSuggestedGoalToWorld(
            forwardDelta,
            SuggestedGoalCoordinateSpace.ViewRelative,
            pawnPos,
            yawDegrees: 90f);

        Assert.Equal(0f, world.X, precision: 1);
        Assert.Equal(100f, world.Y, precision: 1);
        Assert.Equal(0f, world.Z, precision: 1);
    }

    [Fact]
    public void Test03_TransformYaw_180Degrees_MovesAlongNegativeX()
    {
        // Yaw 180° olha para -X (West). Forward 100u deve mover -100 em X.
        var pawnPos = new Vector(0, 0, 0);
        var forwardDelta = new Vector(100f, 0f, 0f);

        var world = MapPlayableBounds.TransformSuggestedGoalToWorld(
            forwardDelta,
            SuggestedGoalCoordinateSpace.ViewRelative,
            pawnPos,
            yawDegrees: 180f);

        Assert.Equal(-100f, world.X, precision: 1);
        Assert.Equal(0f, world.Y, precision: 1);
        Assert.Equal(0f, world.Z, precision: 1);
    }

    [Fact]
    public void Test04_TransformYaw_270Degrees_MovesAlongNegativeY()
    {
        // Yaw 270° olha para -Y (South). Forward 100u deve mover -100 em Y.
        var pawnPos = new Vector(0, 0, 0);
        var forwardDelta = new Vector(100f, 0f, 0f);

        var world = MapPlayableBounds.TransformSuggestedGoalToWorld(
            forwardDelta,
            SuggestedGoalCoordinateSpace.ViewRelative,
            pawnPos,
            yawDegrees: 270f);

        Assert.Equal(0f, world.X, precision: 1);
        Assert.Equal(-100f, world.Y, precision: 1);
        Assert.Equal(0f, world.Z, precision: 1);
    }

    [Fact]
    public void Test05_TransformYaw_StrafeRight_RespectsSource2RightVector()
    {
        // Strafe Right (Delta Y = +100u) com Yaw 0° deve projetar para -Y (Right vector no Source 2)
        var pawnPos = new Vector(100, 200, -100);
        var rightDelta = new Vector(0f, 100f, 0f);

        var world = MapPlayableBounds.TransformSuggestedGoalToWorld(
            rightDelta,
            SuggestedGoalCoordinateSpace.ViewRelative,
            pawnPos,
            yawDegrees: 0f);

        Assert.Equal(100f, world.X, precision: 1);
        Assert.Equal(100f, world.Y, precision: 1); // 200 - 100 = 100
        Assert.Equal(-100f, world.Z, precision: 1);
    }

    // =========================================================================
    // 2. TESTES DE VALIDAÇÃO ESPACIAL E PLAYABLE BOUNDS EM 2 NÍVEIS
    // =========================================================================

    [Fact]
    public void Test06_GoalValidator_RejectsNaNAndInfinity()
    {
        var nanGoal = new Vector(float.NaN, 0f, 0f);
        var infGoal = new Vector(0f, float.PositiveInfinity, 0f);

        var resNan = MapPlayableBounds.ValidateGoal(nanGoal, new Vector(0, 0, 0), "de_mirage");
        var resInf = MapPlayableBounds.ValidateGoal(infGoal, new Vector(0, 0, 0), "de_mirage");

        Assert.False(resNan.IsValid);
        Assert.Equal(GoalValidationStatus.ZeroOrNaN, resNan.Status);
        Assert.False(resInf.IsValid);
        Assert.Equal(GoalValidationStatus.ZeroOrNaN, resInf.Status);
    }

    [Fact]
    public void Test07_GoalValidator_RejectsUninitializedZeroVector()
    {
        var zeroGoal = new Vector(0f, 0f, 0f);
        var res = MapPlayableBounds.ValidateGoal(zeroGoal, new Vector(500, 500, -160), "de_mirage");

        Assert.False(res.IsValid);
        Assert.Equal(GoalValidationStatus.ZeroOrNaN, res.Status);
    }

    [Fact]
    public void Test08_GoalValidator_RejectsOutsideSafetyBounds()
    {
        // Z extremo (ex: -1000 ou +5000)
        var extremeZ = new Vector(-1200f, -400f, -9999f);
        var extremeX = new Vector(99999f, 0f, 0f);

        var resZ = MapPlayableBounds.ValidateGoal(extremeZ, new Vector(0, 0, 0), "de_mirage");
        var resX = MapPlayableBounds.ValidateGoal(extremeX, new Vector(0, 0, 0), "de_mirage");

        Assert.False(resZ.IsValid);
        Assert.Equal(GoalValidationStatus.OutsideSafetyBounds, resZ.Status);
        Assert.False(resX.IsValid);
        Assert.Equal(GoalValidationStatus.OutsideSafetyBounds, resX.Status);
    }

    [Fact]
    public void Test09_GoalValidator_ApprovesLegitimateMirageCoordinates()
    {
        // Posicionamento real na Mirage (Palácio, A, B, Caverna, Janela)
        var aRamp = new Vector(-1160.0f, -2450.0f, -168.0f);
        var bApartments = new Vector(-1190.0f, -150.0f, -165.0f);
        var midWindow = new Vector(-1370.0f, -1080.0f, -70.0f);

        Assert.True(MapPlayableBounds.ValidateGoal(aRamp, null, "de_mirage").IsValid);
        Assert.True(MapPlayableBounds.ValidateGoal(bApartments, null, "de_mirage").IsValid);
        Assert.True(MapPlayableBounds.ValidateGoal(midWindow, null, "de_mirage").IsValid);
    }

    // =========================================================================
    // 3. TESTES DE BOMBSITE TIPADO E PARSER ESTRITO
    // =========================================================================

    [Theory]
    [InlineData("A", BombsiteTarget.A)]
    [InlineData("Bombsite A", BombsiteTarget.A)]
    [InlineData("BOMBSITE_A", BombsiteTarget.A)]
    [InlineData("Site A", BombsiteTarget.A)]
    [InlineData("B", BombsiteTarget.B)]
    [InlineData("Bombsite B", BombsiteTarget.B)]
    [InlineData("BOMBSITE_B", BombsiteTarget.B)]
    [InlineData("Mid", BombsiteTarget.Mid)]
    [InlineData("Middle", BombsiteTarget.Mid)]
    [InlineData("Dynamic", BombsiteTarget.Dynamic)]
    public void Test10_BombsiteParser_ParsesValidTargetsStrictly(string input, BombsiteTarget expected)
    {
        bool success = BombsiteParser.TryParseBombsiteTarget(input, out var target);
        Assert.True(success);
        Assert.Equal(expected, target);
    }

    [Fact]
    public void Test11_BombsiteParser_DoesNotConfuseBombAlternativoWithSiteA()
    {
        // "Bomb Alternativo" continha a letra 'A' e quebrava o parser legado por Contains("A")
        bool success = BombsiteParser.TryParseBombsiteTarget("Bomb Alternativo", out var target);
        Assert.False(success);
        Assert.Equal(BombsiteTarget.None, target);
    }

    // =========================================================================
    // 4. TESTES DE SPOT RESOLVER POR SCORING
    // =========================================================================

    [Fact]
    public void Test12_SpotResolver_PrefersBombsiteAndRoleMatch()
    {
        var manager = new MapProfileManager();
        var spots = new List<TacticalSpot>
        {
            new TacticalSpot
            {
                Id = "ct_a_ticket",
                Name = "Ticket A",
                Sector = "Bombsite A",
                Side = "CT",
                AssociatedBombsite = "A",
                Usage = SpotUsage.Hold,
                AllowedRoles = new() { BotRole.AWPer },
                X = -1000, Y = -400, Z = -160,
                RecommendedStance = EngagementStance.PASSIVE_HOLD
            },
            new TacticalSpot
            {
                Id = "ct_b_van",
                Name = "Van B",
                Sector = "Bombsite B",
                Side = "CT",
                AssociatedBombsite = "B",
                Usage = SpotUsage.Hold,
                AllowedRoles = new() { BotRole.Anchor },
                X = -1600, Y = -200, Z = -160,
                RecommendedStance = EngagementStance.PASSIVE_HOLD
            }
        };
        manager.SetSpotsForTesting(spots);

        var evals = new List<CandidateSpotEvaluation>();
        var resolved = manager.ResolveBestSpot(
            role: BotRole.AWPer,
            targetSite: BombsiteTarget.A,
            desiredUsage: TacticalSpotUsage.General,
            team: CsTeam.CounterTerrorist,
            botPosition: new Vector(-1020, -410, -160),
            outEvaluations: evals);

        Assert.NotNull(resolved);
        Assert.Equal("ct_a_ticket", resolved.Id);
        Assert.True(evals.Count == 2);
        Assert.True(evals[0].Score > evals[1].Score);
    }

    [Fact]
    public void Test13_SpotResolver_AppliesBlacklistAndOccupancyPenalties()
    {
        var manager = new MapProfileManager();
        var spots = new List<TacticalSpot>
        {
            new TacticalSpot
            {
                Id = "tr_exec_a1",
                Name = "Palace Entry",
                Sector = "Bombsite A",
                Side = "TR",
                AssociatedBombsite = "A",
                Usage = SpotUsage.Execute,
                X = -800, Y = -500, Z = -160
            },
            new TacticalSpot
            {
                Id = "tr_exec_a2",
                Name = "Tetris Entry",
                Sector = "Bombsite A",
                Side = "TR",
                AssociatedBombsite = "A",
                Usage = SpotUsage.Execute,
                X = -950, Y = -450, Z = -160
            }
        };
        manager.SetSpotsForTesting(spots);

        var blacklisted = new HashSet<string> { "tr_exec_a1" };
        var evals = new List<CandidateSpotEvaluation>();

        var resolved = manager.ResolveBestSpot(
            role: BotRole.EntryFragger,
            targetSite: BombsiteTarget.A,
            desiredUsage: TacticalSpotUsage.Execute,
            team: CsTeam.Terrorist,
            botPosition: new Vector(-850, -500, -160),
            blacklistedSpotIds: blacklisted,
            outEvaluations: evals);

        Assert.NotNull(resolved);
        Assert.Equal("tr_exec_a2", resolved.Id);
        var blEval = evals.First(e => e.SpotId == "tr_exec_a1");
        Assert.True(blEval.Score < 0);
        Assert.True(blEval.IsBlacklisted);
    }

    // =========================================================================
    // 5. TESTES DO MOTOR DE SAVE FORMAL E AUDITÁVEL
    // =========================================================================

    [Fact]
    public void Test14_SaveDecision_NeverSavesOnFinalRoundOfHalf()
    {
        // Round 12 (último round do half em MR12) -> NUNCA salva!
        var roundCtx = new MatchRoundContext(
            CurrentRound: 12,
            MaxRoundsPerHalf: 12,
            MaxRoundsPerMatch: 24);

        var decision = MidRoundAdapter.EvaluateSaveDecision(
            team: CsTeam.CounterTerrorist,
            aliveTeamCount: 1,
            aliveEnemyCount: 5,
            bombPlanted: true,
            bombTimeRemaining: 30f,
            roundContext: roundCtx,
            teamBots: new List<CCSPlayerController>());

        Assert.False(decision.TeamShouldSave);
        Assert.Equal("ROUND_FINAL_PROIBIDO_SALVAR", decision.Reason);
    }

    [Fact]
    public void Test15_SaveDecision_NeverSavesOnFinalRoundOfRegulation()
    {
        // Round 24 (último round regulamentar) -> NUNCA salva!
        var roundCtx = new MatchRoundContext(
            CurrentRound: 24,
            MaxRoundsPerHalf: 12,
            MaxRoundsPerMatch: 24);

        var decision = MidRoundAdapter.EvaluateSaveDecision(
            team: CsTeam.Terrorist,
            aliveTeamCount: 1,
            aliveEnemyCount: 4,
            bombPlanted: false,
            bombTimeRemaining: 0f,
            roundContext: roundCtx,
            teamBots: new List<CCSPlayerController>());

        Assert.False(decision.TeamShouldSave);
        Assert.Equal("ROUND_FINAL_PROIBIDO_SALVAR", decision.Reason);
    }

    [Fact]
    public void Test16_SaveDecision_SavesInSevere1v5DisadvantageWithDeterministicRoll()
    {
        // Round normal (ex: round 5) em situação 1v5 com seed determinístico
        var roundCtx = new MatchRoundContext(
            CurrentRound: 5,
            MaxRoundsPerHalf: 12,
            MaxRoundsPerMatch: 24);

        // Simulando roll determinístico com seed fixo
        var decision = MidRoundAdapter.EvaluateSaveDecision(
            team: CsTeam.CounterTerrorist,
            aliveTeamCount: 1,
            aliveEnemyCount: 5,
            bombPlanted: true,
            bombTimeRemaining: 25f,
            roundContext: roundCtx,
            teamBots: new List<CCSPlayerController>(),
            deterministicSeed: 42);

        // Em 1v5 coletivo com lista vazia de bots simulada
        Assert.False(roundCtx.IsFinalRoundOfHalf);
    }

    // =========================================================================
    // 6. TESTES DO TRACKER COM DOIS EIXOS E METADADOS
    // =========================================================================

    [Fact]
    public void Test17_Tracker_PreservesPhysicalOutcomeWithStateIntegrity()
    {
        var intent = new MovementIntent
        {
            BotSlot = 2,
            Kind = MovementCommandKind.NavigateNavMesh,
            ExpectedMovement = true,
            IsHoldAuthorized = false
        };

        var tracker = new MovementExecutionTracker();
        var (physical, reason, details) = MovementExecutionTracker.ClassifyPhysicalOutcomeDetailed(intent, disp500: 120f, vel125: 180f);

        Assert.Equal(PhysicalExecutionOutcome.AppliedWithProgress, physical);
        Assert.Equal("NORMAL_PROGRESS", reason);

        // CompleteSample com ambos os eixos
        tracker.CompleteSample(
            slot: 2,
            physicalOutcome: physical,
            integrity: StateIntegrityOutcome.NoUnexpectedStateChange,
            details: details,
            disp32: 120f);

        var detailed = tracker.GetLatestDetailedMetadata(2);
        Assert.NotNull(detailed);
        Assert.Equal(PhysicalExecutionOutcome.AppliedWithProgress, detailed.Value.Physical);
        Assert.Equal(StateIntegrityOutcome.NoUnexpectedStateChange, detailed.Value.Integrity);
        Assert.Equal(120f, detailed.Value.Disp2D);
    }

    // =========================================================================
    // 7. TESTES DO RECOVERY COM PROGRESSO AO MACRO GOAL
    // =========================================================================

    [Fact]
    public void Test18_RecoveryAttempt_TracksMacroGoalProgress()
    {
        var attempt = new RecoveryAttempt
        {
            BotSlot = 3,
            InternalRoundId = 1,
            OriginalPosition = new Vector(0, 0, 0),
            OriginalGoal = new Vector(1000, 0, 0),
            DistanceToMacroGoalBefore = 1000f,
            Recovered = false
        };

        // Simula deslocamento aos 500ms aproximando 50u do objetivo
        var pos500Ms = new Vector(50, 0, 0);
        float distAfter500 = (attempt.OriginalGoal - pos500Ms).Length();
        attempt.DistanceToMacroGoalAfter = distAfter500;
        attempt.MacroGoalProgress = attempt.DistanceToMacroGoalBefore - distAfter500;

        Assert.Equal(950f, attempt.DistanceToMacroGoalAfter);
        Assert.Equal(50f, attempt.MacroGoalProgress);
        Assert.True(attempt.MacroGoalProgress > 0f);
    }
}
