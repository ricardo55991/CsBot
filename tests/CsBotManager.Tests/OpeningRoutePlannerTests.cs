using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

namespace CsBotManager.Tests;

public class OpeningRoutePlannerTests
{
    [Fact]
    public void RouteEventCodesHaveCanonicalNames()
    {
        Assert.Equal("PLAYER_DEATH", OpeningRouteEventContract.GetCanonicalClassificationName(6));
        Assert.Equal("NOT_REACHED", OpeningRouteEventContract.GetCanonicalClassificationName(7));
        Assert.Equal("ON_TIME", OpeningRouteEventContract.GetCanonicalClassificationName(1));
        Assert.Equal("CONTACT_INTERRUPTION", OpeningRouteEventContract.GetCanonicalClassificationName(4));
        Assert.Equal("PLAYER_DEATH", OpeningRouteEventContract.GetCanonicalTerminationReasonName(4));
        Assert.Equal("TIMEOUT", OpeningRouteEventContract.GetCanonicalTerminationReasonName(6));
    }

    [Fact]
    public void SpawnMapsToExactlyOneBucket()
    {
        var validBuckets = new HashSet<string>
        {
            "CT_A_FAST", "CT_A_STANDARD", "CT_MID_FAST", "CT_MID_STANDARD", "CT_B_FAST", "CT_B_STANDARD",
            "T_A_FAST", "T_A_STANDARD", "T_MID_FAST", "T_MID_STANDARD", "T_B_FAST", "T_B_STANDARD"
        };

        var samples = new (string Team, float X, float Y, float Z)[]
        {
            ("CT", -1530f, -1991f, -264f),
            ("CT", -1656f, -1800f, -267f),
            ("CT", -1776f, -1800f, -264f),
            ("T", 1136f, -64f, -164f),
            ("T", 1220f, -240f, -168f),
            ("T", 1380f, 40f, -168f),
        };

        foreach (var s in samples)
        {
            string b = SpawnBucketClassifier.Classify(s.Team, s.X, s.Y, s.Z);
            Assert.Contains(b, validBuckets);
        }
    }

    [Fact]
    public void CtRouteUsesCtCorridor()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B",
            -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.StartsWith("CT_", sug!.AllowedCorridor, StringComparison.Ordinal);
        Assert.DoesNotContain(sug.AllowedCorridor, sug.ForbiddenCorridors);
    }

    [Fact]
    public void TRouteUsesTCorridor()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 2, "t_1", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B",
            1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.StartsWith("T_", sug!.AllowedCorridor, StringComparison.Ordinal);
        Assert.DoesNotContain(sug.AllowedCorridor, sug.ForbiddenCorridors);
    }

    [Fact]
    public void RoutePreservesAssignedSector()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 3, "ct_mid", "CT", "AWPer", "mid_window_right_deep", "Janela do Meio",
            -1620f, -1820f, -264f, -1181.4f, -718.5f, -168f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.Equal("MID", sug!.TargetSector);
        Assert.Equal("mid_window_right_deep", sug.TargetSpot);
    }

    [Fact]
    public void RoutePreservesAssignedRole()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 4, "ct_anchor", "CT", "Anchor", "a_firebox_ninja_hold", "Bombsite A",
            -1600f, -1950f, -264f, -381.5f, -2395f, -164f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.Equal("Anchor", sug!.Role);
    }

    [Fact]
    public void MarketDestinationDoesNotRouteThroughWindowShort()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 5, "ct_b", "CT", "Anchor", "ct_retake_b_market_window_site", "Mercado B",
            -1760f, -1820f, -264f, -1776.2f, -622.2f, -168f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.Equal("CT_MARKET_CORRIDOR", sug!.AllowedCorridor);
        Assert.Contains("MID_WINDOW", sug.ForbiddenCorridors);
        Assert.Contains("MID_SHORT", sug.ForbiddenCorridors);
        Assert.Contains("MID_CONNECTOR", sug.ForbiddenCorridors);
    }

    [Fact]
    public void ConflictGroupSelectsSinglePriorityWinner()
    {
        var planner = new OpeningRoutePlanner();
        var batch = new[]
        {
            (RawSlot: 2, PlayerSlot: "ct_slow", Team: "CT", Role: "Rotator", TargetSpot: "b_van_behind_apps_hold", SpotSector: "Bombsite B", StartX: -1550f, StartY: -1950f, StartZ: -264f, TargetX: -1981.9f, TargetY: 702.6f, TargetZ: -48f, Tick: 100),
            (RawSlot: 1, PlayerSlot: "ct_fast", Team: "CT", Role: "Anchor", TargetSpot: "b_site_default_plant_box", SpotSector: "Bombsite B", StartX: -1760f, StartY: -1650f, StartZ: -168f, TargetX: -1956.5f, TargetY: 311.6f, TargetZ: -160f, Tick: 100),
        };
        var results = planner.ResolveBatchConflicts(1, batch);
        Assert.Equal(2, results.Count);
        Assert.Single(results, r => !r.ConflictDetected && r.RouteVariant == "PRIMARY");
        var delayed = Assert.Single(results, r => r.ConflictDetected);
        Assert.Equal(results.First(r => !r.ConflictDetected).PlayerSlot, delayed.PriorityWinner);
        Assert.Equal(delayed.PlayerSlot, delayed.DelayedBot);
        Assert.True(delayed.DelayMs > 0);
    }

    [Fact]
    public void AlternativeRouteRemainsTacticallyValid()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 1, "ct_1", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B",
            -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, out _));
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 2, "ct_2", "CT", "Anchor", "b_van_behind_apps_hold", "Bombsite B",
            -1720f, -1896f, -267f, -1981.9f, 702.6f, -48f, 100, out var alt));
        Assert.NotNull(alt);
        Assert.True(alt!.ConflictDetected);
        Assert.Equal("FALLBACK_STAGGERED", alt.RouteVariant);
        Assert.Equal("B", alt.TargetSector);
        Assert.Equal("CT_MARKET_CORRIDOR", alt.AllowedCorridor);
    }

    [Fact]
    public void KnifeIsNotSuggestedPastThreatLine()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 6, "t_mid", "T", "AWPer", "mid_top_mid_boxes", "Top Mid",
            1220f, -60f, -168f, 368f, -223f, -167.7f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.True(sug!.WeaponSwitchTick < sug.ThreatLineTick);
    }

    [Fact]
    public void WeaponIsReadyBeforePossibleContact()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 7, "t_ramp", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A",
            1220f, -240f, -168f, 320f, -1590f, -168f, 100, out var sug));
        Assert.NotNull(sug);
        Assert.True(sug!.WeaponReadyBeforeContact);
        Assert.True(sug.WeaponSwitchTick < sug.FirstPossibleContactTick);
    }

    [Fact]
    public void ContactInterruptionIsNotClassifiedLate()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        tracker.TryRegisterAssignment(1, 1, "ct_1", "CT", "mid_window_right_deep", -1620f, -1820f, -264f, -1181f, -718f, -168f, 90f, 104, false);
        tracker.UpdateTick(1, 1, 2500, true, -1300f, -900f, -168f, "weapon_awp", hasEnemyContact: true);
        var closed = Assert.Single(tracker.ClosedRoutes);
        Assert.Equal(OpeningRouteClassification.CONTACT_INTERRUPTION, closed.Classification);
        Assert.False(OpeningRouteEventContract.IsPenalizedAsLate(closed.Classification));
    }

    [Fact]
    public void TacticalRedirectIsNotClassifiedNotReached()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        tracker.TryRegisterAssignment(1, 2, "ct_2", "CT", "a_firebox_ninja_hold", 0f, 0f, 0f, 500f, 0f, 0f, 90f, 104, false);
        tracker.TryRegisterAssignment(1, 2, "ct_2", "CT", "b_site_default_plant_box", 100f, 0f, 0f, 800f, 800f, 0f, 90f, 200, false, PostOpeningRepathKind.TACTICAL_ROTATION);
        var closed = Assert.Single(tracker.ClosedRoutes);
        Assert.Equal(OpeningRouteClassification.TACTICAL_REDIRECT, closed.Classification);
        Assert.NotEqual(OpeningRouteClassification.NOT_REACHED, closed.Classification);
    }

    [Fact]
    public void OneOpeningRoutePerPlayerPerRound()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(
            1, 8, "ct_8", "CT", "Anchor", "b_site_default_plant_box", "Bombsite B",
            -1760f, -1820f, -264f, -1956.5f, 311.6f, -160f, 100, out _));
        Assert.False(planner.TryPlanOpeningRouteForRound(
            1, 8, "ct_8", "CT", "Anchor", "b_van_behind_apps_hold", "Bombsite B",
            -1700f, -1500f, -168f, -1981.9f, 702.6f, -48f, 160, out _));
        Assert.Single(planner.AllSuggestions);
    }

    [Fact]
    public void MidroundRepathIsNotOpeningRoute()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);
        Assert.True(tracker.TryRegisterAssignment(1, 9, "t_9", "T", "tr_b_apps_house_staging", 0f, 0f, 0f, 500f, 0f, 0f, 90f, 104, false));
        Assert.False(tracker.TryRegisterAssignment(1, 9, "t_9", "T", "tr_b_apps_kitchen_control", 50f, 0f, 0f, 700f, 0f, 0f, 90f, 160, false, PostOpeningRepathKind.MIDROUND_REPATH));
        Assert.Equal(1, tracker.TotalOpeningRoutesCreated);
        Assert.Equal(1, tracker.UniqueMidroundRepaths);
    }

    [Fact]
    public void PlannerCannotAffectUtilityDecision()
    {
        var planner = new OpeningRoutePlanner();
        planner.TryPlanOpeningRouteForRound(
            1, 10, "ct_10", "CT", "AWPer", "mid_window_left_awp", "Janela do Meio",
            -1620f, -1820f, -264f, -1200f, -597.1f, -168f, 100, out var sug);
        string utilityDecision = "b_site_default_plant_box";
        Assert.Equal(utilityDecision, OpeningRoutePlannerGuard.OpeningRoutePlannerCannotAffectBotDecision(utilityDecision, sug));
        Assert.False(sug!.PlannerControlActive);
        Assert.True(sug.UtilityDecisionPreserved);
    }
}
