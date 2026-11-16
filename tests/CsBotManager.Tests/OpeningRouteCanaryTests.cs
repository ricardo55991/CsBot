using System;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class OpeningRouteCanaryTests
{
    private static OpeningRouteCanaryGuard CreateCtGuard() => new(CanaryTeamMode.CtSingle);
    private static OpeningRouteCanaryGuard CreateTrGuard() => new(CanaryTeamMode.TrSingle);

    [Fact]
    public void OnlyOneBotCanBeCanary()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, true, false));
        Assert.False(guard.TryStartCanaryForRound(1, 2, "ct_2", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio", -1620f, -1820f, -264f, -1181.4f, -718.5f, -168f, 100, true, false));
        Assert.False(guard.TryStartCanaryForRound(1, 3, "t_3", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false));
    }

    [Fact]
    public void CanaryOnlyControlsOpeningPhase()
    {
        var guard = CreateCtGuard();
        Assert.False(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, isOpeningPhase: false, isBombPlanted: false));
        Assert.False(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, isOpeningPhase: true, isBombPlanted: true));
    }

    [Fact]
    public void CanaryRouteMustBeAllowlisted()
    {
        var guard = CreateCtGuard();
        // mid_window_left_awp e mid_top_mid_boxes são CATALOG_REVIEW_REQUIRED -> proibidos na allowlist
        Assert.False(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "AWPer", "mid_window_left_awp", "Janela do Meio", -1620f, -1820f, -264f, -1200f, -597.1f, -168f, 100, true, false));
        Assert.False(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "tr_b_apps_house_staging", "Apartamentos B", -1760f, -1820f, -264f, -764.4f, 522.1f, -77f, 100, true, false));
    }

    [Fact]
    public void CanaryCannotChangeDestination()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, true, false));
        var dec = guard.EvaluateTick(1, 1, 110, -1750f, -1600f, -168f, 240f, "weapon_knife", true, true, false,
            currentDestination: "a_firebox_ninja_hold", currentSector: "B", currentRole: "Anchor", hasContact: false, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
        Assert.Contains("CANARY_ABORTED", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void CanaryCannotChangeSector()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, true, false));
        var dec = guard.EvaluateTick(1, 1, 110, -1750f, -1600f, -168f, 240f, "weapon_knife", true, true, false,
            currentDestination: "b_site_default_plant_box", currentSector: "A", currentRole: "Anchor", hasContact: false, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
        Assert.Contains("SECTOR_IMMUTABLE", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void CanaryCannotChangeRole()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, true, false));
        var dec = guard.EvaluateTick(1, 1, 110, -1750f, -1600f, -168f, 240f, "weapon_knife", true, true, false,
            currentDestination: "b_site_default_plant_box", currentSector: "B", currentRole: "AWPer", hasContact: false, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
        Assert.Contains("ROLE_IMMUTABLE", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void UtilityCanCancelCanary()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, true, false));
        guard.NotifyUtilityCancel(1, 1, 115, "UTILITY_OVERRIDE");
        Assert.False(guard.IsSlotActiveCanary(1, 1));
        Assert.Equal("UTILITY_AI", guard.GetSessionForRound(1)!.Authority);
    }

    [Fact]
    public void ContactImmediatelyReturnsAuthority()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio", -1620f, -1820f, -264f, -1181.4f, -718.5f, -168f, 100, true, false));
        var dec = guard.EvaluateTick(1, 1, 120, -1400f, -1200f, -168f, 240f, "weapon_awp", true, true, false,
            "mid_window_right_deep", "MID", "AWPer", hasContact: true, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
        Assert.Equal("CONTACT_INTERRUPTION", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void DamageImmediatelyReturnsAuthority()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio", -1620f, -1820f, -264f, -1181.4f, -718.5f, -168f, 100, true, false));
        guard.NotifyPlayerDamage(1, 1, 125, isHostileUtility: false);
        Assert.False(guard.IsSlotActiveCanary(1, 1));
        Assert.Equal("DAMAGE_INTERRUPTION", guard.GetSessionForRound(1)!.FallbackReason);
    }

    [Fact]
    public void HostileUtilityReturnsAuthority()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio", -1620f, -1820f, -264f, -1181.4f, -718.5f, -168f, 100, true, false));
        guard.NotifyPlayerDamage(1, 1, 125, isHostileUtility: true);
        Assert.False(guard.IsSlotActiveCanary(1, 1));
        Assert.Equal("HOSTILE_UTILITY", guard.GetSessionForRound(1)!.FallbackReason);
    }

    [Fact]
    public void BlockTimeoutReturnsAuthority()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, true, false));
        CanaryTickDecision? last = null;
        for (int i = 1; i <= 25; i++)
        {
            last = guard.EvaluateTick(1, 1, 100 + i * 4, -1760f, -1820f, -264f, 0f, "weapon_knife", true, true, false,
                "b_site_default_plant_box", "B", "Anchor", false, false, false, tickIntervalMs: 62);
            if (!last.CanaryControlling) break;
        }
        Assert.NotNull(last);
        Assert.False(last!.CanaryControlling);
        Assert.Equal("CANARY_BLOCKED_FALLBACK", last.AbortOrCompletionReason);
    }

    [Fact]
    public void KnifeCannotCrossThreatLine()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio", -1620f, -1820f, -264f, -1181.4f, -718.5f, -168f, 100, true, false));
        var s = guard.GetSessionForRound(1)!;
        var dec = guard.EvaluateTick(1, 1, s.Route.ThreatLineTick + 5, -1280f, -840f, -168f, 240f, "weapon_knife", true, true, false,
            "mid_window_right_deep", "MID", "AWPer", false, false, false);
        Assert.False(dec.CanaryControlling);
        Assert.True(dec.ShouldSwitchToWeapon);
        Assert.Equal("WEAPON_SWITCH_FAILED", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void WeaponIsReadyBeforeContact()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio", -1620f, -1820f, -264f, -1181.4f, -718.5f, -168f, 100, true, false));
        var s = guard.GetSessionForRound(1)!;
        var dec = guard.EvaluateTick(1, 1, s.Route.WeaponSwitchTick, -1350f, -1000f, -168f, 215f, "weapon_m4a1", true, true, false,
            "mid_window_right_deep", "MID", "AWPer", false, false, false);
        Assert.True(dec.CanaryControlling);
        Assert.True(dec.ShouldSwitchToWeapon);
        Assert.True(guard.Records.Last().WeaponReadyBeforeContact);
    }

    [Fact]
    public void ConflictGroupPriorityIsRespected()
    {
        var planner = new OpeningRoutePlanner();
        var batch = new[]
        {
            (2, "ct_slow", "CT", "Rotator", "b_van_behind_apps_hold", "Bombsite B", -1550f, -1950f, -264f, -1981.9f, 702.6f, -48f, 100),
            (1, "ct_fast", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1650f, -168f, -1956.5f, 311.6f, -160f, 100),
        };
        var res = planner.ResolveBatchConflicts(1, batch);
        Assert.Equal("ct_fast", res[0].PlayerSlot);
        Assert.False(res[0].ConflictDetected);
        Assert.True(res[1].ConflictDetected);
        Assert.Equal("ct_fast", res[1].PriorityWinner);
    }

    [Fact]
    public void CanaryCannotControlCombat()
    {
        string combatDecision = "FIRE_AT_ENEMY";
        Assert.Equal(combatDecision, OpeningRouteCanaryGuard.GuardCombatOrC4Authority(combatDecision, true));
    }

    [Fact]
    public void CanaryCannotControlC4Decision()
    {
        var guard = CreateTrGuard();
        // Portador da C4 com plano no Bombsite A tentando rota em B -> bloqueado pelo guard
        Assert.False(guard.TryStartCanaryForRound(1, 4, "t_c4", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B",
            1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false, hasC4: true, planTargetBombsite: "A"));
        string c4Decision = "PLANT_AT_A";
        Assert.Equal(c4Decision, OpeningRouteCanaryGuard.GuardCombatOrC4Authority(c4Decision, true));
    }

    [Fact]
    public void NonCanaryBotsRemainUnchanged()
    {
        var guard = CreateCtGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, true, false));
        var other = guard.EvaluateTick(1, 5, 110, -1500f, -1700f, -200f, 240f, "weapon_knife", true, true, false,
            "a_firebox_ninja_hold", "A", "Anchor", false, false, false);
        Assert.False(other.CanaryControlling);
        Assert.Equal("UTILITY_AI", other.Authority);
    }

    [Fact]
    public void RouteAccountingCloses()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        tracker.TryRegisterAssignment(1, 1, "ct_1", "CT", "b_site_default_plant_box", -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 90f, 104, false);
        tracker.CloseAllOpenRoutes(1, OpeningRouteTerminationReason.ROUND_END, 800);
        Assert.Equal(0, tracker.ComputeAccountingResidue());
    }

    [Fact]
    public void CanaryFailureDoesNotCrashServer()
    {
        var guard = CreateCtGuard();
        var dec = guard.EvaluateTick(99, 99, 100, 0f, 0f, 0f, 0f, "", false, false, false, "", "", "", false, false, false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
    }

    [Fact]
    public void PositioningTransformerRemainsShadowOnly()
    {
        string utilityDecision = "ROTATE_TO_B";
        var pred = new PositioningShadowPrediction { InferenceSuccess = true, SelectedSpotId = 10 };
        Assert.Equal(utilityDecision, ShadowModeGuard.ShadowModeCannotAffectBotDecision(utilityDecision, pred));
    }
}
