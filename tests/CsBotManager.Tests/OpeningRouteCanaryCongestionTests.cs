using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class OpeningRouteCanaryCongestionTests
{
    private const string CtDest = "a_firebox_ninja_hold";
    private const float StartX = -1750f;
    private const float StartY = -2000f;
    private const float StartZ = -168f;
    private const float TargetX = -450f;
    private const float TargetY = -2250f;
    private const float TargetZ = -168f;

    [Fact]
    public void CanarySelectsEligibleCtBot()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        bool started = guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        Assert.True(started);
        Assert.True(guard.IsSlotActiveCanary(1, 2));
    }

    [Fact]
    public void IneligibleCandidateSelectsAnotherBot()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        // Candidato 1 inelegível (spot retake fora da allowlist)
        bool first = guard.TryStartCanaryForRound(1, 1, "p1", "CT", "Rotator", "ct_retake_a_ramp_clear_tetris", "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        Assert.False(first);
        // Candidato 2 elegível no mesmo round
        bool second = guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        Assert.True(second);
        Assert.Equal(2, guard.GetSessionForRound(1)?.RawSlot);
    }

    [Fact]
    public void NoEligibleBotDoesNotCreateFakeSession()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        bool started = guard.TryStartCanaryForRound(9, 1, "p1", "CT", "Anchor", "ct_retake_a_ramp_clear_site", "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        Assert.False(started);
        guard.RecordNoEligibleRound(9, "CT", 5);
        Assert.Null(guard.GetSessionForRound(9));
        Assert.True(guard.NoEligibleRounds.ContainsKey(9));
        Assert.Equal("NO_ELIGIBLE_CT_CANARY", guard.NoEligibleRounds[9].Reason);
        Assert.Empty(guard.Records);
    }

    [Fact]
    public void ConflictGroupAppliesDeterministicStagger()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        var teammates = new List<TeammatePositionSnapshot>
        {
            new(1, -1650f, -2050f, -168f, 200f, 0f, "Entry", "CT_SPAWN_EXIT")
        };
        bool started = guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false, teammates: teammates);
        Assert.True(started);
        var session = guard.GetSessionForRound(1)!;
        Assert.InRange(session.Schedule.PlannedStaggerMs, 100, 250);
        Assert.Equal(1, session.Schedule.PredecessorSlot);

        // Durante stagger, segura posição sem contar bloqueio
        var hold = guard.EvaluateTick(1, 2, 104, StartX, StartY, StartZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.True(hold.CanaryControlling);
        Assert.True(hold.HoldingForStagger);
        Assert.False(hold.WaypointChanged);
        Assert.Equal(0, session.BlockedDurationMs);
    }

    [Fact]
    public void CanaryDoesNotDispatchNavigationEveryTick()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        var d1 = guard.EvaluateTick(1, 2, 104, -1700f, -2020f, -168f, 220f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        var d2 = guard.EvaluateTick(1, 2, 108, -1640f, -2050f, -168f, 220f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        var d3 = guard.EvaluateTick(1, 2, 112, -1580f, -2080f, -168f, 220f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.True(d1.WaypointChanged);
        Assert.Equal("ROUTE_START", d1.DispatchReason);
        Assert.False(d2.WaypointChanged);
        Assert.False(d3.WaypointChanged);
    }

    [Fact]
    public void TeammateBlockRequiresContinuousEvidence()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        // Velocidade baixa isolada logo no início (< 0.35s) não marca bloqueio
        guard.EvaluateTick(1, 2, 110, StartX, StartY, StartZ, 10f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(0, guard.GetSessionForRound(1)!.BlockedDurationMs);

        // Se houver progresso contínuo mesmo com velocidade baixa reportada, não acumula bloqueio
        guard.EvaluateTick(1, 2, 140, -1720f, -2010f, -168f, 18f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(0, guard.GetSessionForRound(1)!.BlockedDurationMs);
    }

    [Fact]
    public void RecoveryUsesValidatedLateralWaypoint()
    {
        // Compatibilidade legada 2B.8.1 (opt-in explícito); padrão em 2B.8.2 é LateralRecoveryEnabled = false.
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle, enableLegacyLateralRecovery: true);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        var blocker = new List<TeammatePositionSnapshot> { new(-1 + 2, -1680f, -2030f, -168f) };

        CanaryTickDecision? recDecision = null;
        for (int i = 1; i <= 12; i++)
        {
            var dec = guard.EvaluateTick(1, 2, 140 + i * 4, StartX, StartY, StartZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, teammates: blocker);
            if (dec.DispatchReason == "RECOVERY_AUTHORIZED")
            {
                recDecision = dec;
                break;
            }
        }
        Assert.NotNull(recDecision);
        Assert.True(recDecision!.WaypointChanged);
        Assert.Contains("_lateral", recDecision.CurrentWaypoint!.Name);
    }

    [Fact]
    public void RecoveryCannotChangeCorridor()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        string origCorridor = guard.GetSessionForRound(1)!.Route.AllowedCorridor;
        var blocker = new List<TeammatePositionSnapshot> { new(3, -1680f, -2030f, -168f) };
        for (int i = 1; i <= 10; i++)
        {
            guard.EvaluateTick(1, 2, 140 + i * 4, StartX, StartY, StartZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, teammates: blocker);
        }
        Assert.Equal(origCorridor, guard.GetSessionForRound(1)!.Route.AllowedCorridor);
    }

    [Fact]
    public void RecoveryCannotChangeDestination()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        var blocker = new List<TeammatePositionSnapshot> { new(3, -1680f, -2030f, -168f) };
        for (int i = 1; i <= 10; i++)
        {
            guard.EvaluateTick(1, 2, 140 + i * 4, StartX, StartY, StartZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, teammates: blocker);
        }
        var session = guard.GetSessionForRound(1)!;
        Assert.Equal(CtDest, session.OriginalDestination);
        Assert.Equal("A", session.OriginalSector);
    }

    [Fact]
    public void RecoveryAttemptIsLimitedToOne()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        var blocker = new List<TeammatePositionSnapshot> { new(3, -1680f, -2030f, -168f) };
        int recoveryDispatches = 0;
        for (int i = 1; i <= 25; i++)
        {
            var dec = guard.EvaluateTick(1, 2, 140 + i * 4, StartX, StartY, StartZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, teammates: blocker);
            if (dec.DispatchReason == "RECOVERY_AUTHORIZED") recoveryDispatches++;
            if (!dec.CanaryControlling) break;
        }
        Assert.Equal(1, recoveryDispatches);
        Assert.Equal("CANARY_BLOCKED_FALLBACK", guard.GetSessionForRound(1)!.FallbackReason);
    }

    [Fact]
    public void DeadlineIncludesOnlyVerifiedDelay()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        var teammates = new List<TeammatePositionSnapshot>
        {
            new(1, -1660f, -2050f, -168f, 200f, 0f, "Entry", "CT_SPAWN_EXIT")
        };
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false, teammates: teammates);
        var session = guard.GetSessionForRound(1)!;
        double basePlusStagger = session.Route.DeadlineSeconds + (session.Schedule.PlannedStaggerMs / 1000.0);

        // Sem congestionamento de aliado (NO_PROGRESS_UNKNOWN / STATIC_OBSTACLE), não estende VerifiedCongestionAllowanceSeconds
        guard.EvaluateTick(1, 2, 160, StartX, StartY, StartZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.Equal(0.0, session.VerifiedCongestionAllowanceSeconds, 4);
        Assert.Equal(basePlusStagger, session.EffectiveDeadlineSeconds, 4);

        // Com congestionamento de aliado verificado, estende apenas o delay verificado
        var blocker = new List<TeammatePositionSnapshot> { new(3, -1680f, -2030f, -168f) };
        guard.EvaluateTick(1, 2, 164, StartX, StartY, StartZ, 0f, "weapon_knife", true, true, false, CtDest, "A", "Anchor", false, false, false, teammates: blocker);
        Assert.True(session.VerifiedCongestionAllowanceSeconds > 0.0);
        Assert.True(session.EffectiveDeadlineSeconds <= basePlusStagger + 0.900);
    }

    [Fact]
    public void TimeoutCannotBeHiddenByUnlimitedExtension()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        var session = guard.GetSessionForRound(1)!;
        session.VerifiedCongestionAllowanceSeconds = 5.0; // tentativa artificial
        Assert.True(session.EffectiveDeadlineSeconds <= session.Route.DeadlineSeconds + (session.Schedule.PlannedStaggerMs / 1000.0) + 0.9001);

        // Tick muito além de 1.5x effective deadline dispara TIMEOUT
        var dec = guard.EvaluateTick(1, 2, 100 + 2500, -1000f, -2100f, -168f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("TIMEOUT", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void ContactReturnsAuthorityImmediately()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        var dec = guard.EvaluateTick(1, 2, 140, -1400f, -2100f, -168f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", true, false, false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
        Assert.Equal("CONTACT_INTERRUPTION", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void WeaponIsReadyBeforeContact()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        guard.EvaluateTick(1, 2, 140, -1400f, -2100f, -168f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        guard.EvaluateTick(1, 2, 144, -1350f, -2100f, -168f, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", true, false, false);
        Assert.All(guard.Records, r => Assert.True(r.WeaponReadyBeforeContact));
    }

    [Fact]
    public void RouteAccountingCloses()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        guard.EvaluateTick(1, 2, 140, TargetX, TargetY, TargetZ, 0f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        var last = guard.Records[^1];
        Assert.Equal("ROUTE_COMPLETED", last.FallbackReason);
        Assert.NotNull(last.AuthorityReturnTick);
        Assert.Equal("UTILITY_AI", last.Authority);
    }

    [Fact]
    public void NonCanaryBotsRemainUtilityControlled()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", StartX, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        Assert.False(guard.IsSlotActiveCanary(1, 3));
        var d = guard.EvaluateTick(1, 3, 140, StartX, StartY, StartZ, 220f, "weapon_m4a1", true, true, false, CtDest, "A", "Anchor", false, false, false);
        Assert.False(d.CanaryControlling);
        Assert.Equal("UTILITY_AI", d.Authority);
    }

    [Fact]
    public void PositioningTransformerRemainsShadowOnly()
    {
        string utilityDecision = "ROTATE_TO_B";
        var pred = new PositioningShadowPrediction { InferenceSuccess = true, SelectedSpotId = 10 };
        Assert.Equal(utilityDecision, ShadowModeGuard.ShadowModeCannotAffectBotDecision(utilityDecision, pred));
    }

    [Fact]
    public void CanaryFailureDoesNotCrashServer()
    {
        var guard = new OpeningRouteCanaryGuard(CanaryTeamMode.CtSingle);
        bool badCoords = guard.TryStartCanaryForRound(1, 2, "p2", "CT", "Anchor", CtDest, "A", float.NaN, StartY, StartZ, TargetX, TargetY, TargetZ, 100, true, false);
        Assert.False(badCoords);
        var tmp = Path.Combine(Path.GetTempPath(), $"canary_2b81_{Guid.NewGuid():N}.jsonl");
        guard.FlushJsonl(tmp);
        Assert.True(File.Exists(tmp));
        File.Delete(tmp);
    }
}
