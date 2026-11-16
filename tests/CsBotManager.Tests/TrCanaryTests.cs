using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class TrCanaryTests
{
    private static OpeningRouteCanaryGuard CreateTrGuard() => new(CanaryTeamMode.TrSingle);

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "src", "CsBotManager", "MapProfiles", "de_mirage.json")))
            {
                return dir.FullName;
            }
            dir = dir.Parent;
        }
        return @"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot";
    }

    [Fact]
    public void OnlyOneTrBotCanBeCanary()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false));
        Assert.False(guard.TryStartCanaryForRound(1, 3, "t_3", "T", "Rotator", "tr_b_apps_house_staging", "Apartamentos B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false));
        Assert.False(guard.LeaseManager.TryAcquireLease(1, 3, "t_3", "T", "r2", 101, 600, true, CanaryTeamMode.TrSingle, null, out _, out string rej));
        Assert.Equal("ACTIVE_LEASE_ALREADY_EXISTS", rej);
    }

    [Fact]
    public void TrCanaryRequiresAllowlistedRoute()
    {
        var guard = CreateTrGuard();
        Assert.False(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "ct_retake_a_ramp_clear_site", "Rampa A", 1248f, -352f, -168f, 301.7f, -1492.3f, -176f, 100, true, false));
        Assert.False(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_window_left_awp", "Janela do Meio", 1248f, -352f, -168f, -1200f, -597.1f, -168f, 100, true, false));
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1248f, -352f, -168f, 368f, -223f, -167.7f, 100, true, false));
    }

    [Fact]
    public void IneligibleTrSelectsAnotherCandidate()
    {
        var guard = CreateTrGuard();
        // Primeiro candidato: C4 com plano B tentando ir para A -> inelegível
        Assert.False(guard.TryStartCanaryForRound(1, 2, "t_c4", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false, hasC4: true, planTargetBombsite: "B", bombCarrierSlot: 2));
        // Segundo candidato elegível no mesmo round assume
        Assert.True(guard.TryStartCanaryForRound(1, 3, "t_3", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false, hasC4: false, planTargetBombsite: "B", bombCarrierSlot: 2));
        Assert.Equal(3, guard.GetSessionForRound(1)?.RawSlot);
    }

    [Fact]
    public void NoEligibleTrCreatesNoFakeSession()
    {
        var guard = CreateTrGuard();
        Assert.False(guard.TryStartCanaryForRound(5, 1, "t_1", "T", "EntryFragger", "nonexistent_spot", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false));
        guard.RecordNoEligibleRound(5, "T", candidatesChecked: 5);
        Assert.Null(guard.GetSessionForRound(5));
        Assert.Empty(guard.Records);
        Assert.True(guard.NoEligibleRounds.TryGetValue(5, out var noElig));
        Assert.Equal("NO_ELIGIBLE_TR_CANARY", noElig!.Reason);
    }

    [Fact]
    public void BombCarrierRouteMatchesPlan()
    {
        var guard = CreateTrGuard();
        // Portador da C4 com plano B não pode ir para Palace A nem ser Lurker
        Assert.False(guard.TryStartCanaryForRound(1, 2, "t_c4", "T", "EntryFragger", "a_palace_deep_room", "Palácio A", 1248f, -352f, -168f, 90f, -2244.6f, -40f, 100, true, false, hasC4: true, planTargetBombsite: "B", bombCarrierSlot: 2));
        Assert.False(guard.TryStartCanaryForRound(1, 2, "t_c4", "T", "Lurker", "tr_b_apps_house_staging", "Apartamentos B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false, hasC4: true, planTargetBombsite: "B", bombCarrierSlot: 2));
        // Compatível com plano B
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_c4", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false, hasC4: true, planTargetBombsite: "B", bombCarrierSlot: 2));
        var session = guard.GetSessionForRound(1)!;
        Assert.True(session.CanaryIsBombCarrier);
        Assert.Equal(2, session.BombCarrierSlot);
        Assert.Equal("B", session.PlannedBombsite);
        Assert.Equal("B", session.RouteBombsite);
        Assert.True(session.BombsiteCompatible);
        Assert.True(session.BombPathPreserved);
    }

    [Fact]
    public void PlannerCannotChangeBombsite()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_c4", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false, hasC4: true, planTargetBombsite: "A", bombCarrierSlot: 2));
        // Se Utility AI muda o plano para B em andamento, Canary devolve autoridade com C4_ROUTE_INCOMPATIBLE
        var dec = guard.EvaluateTick(1, 2, 110, 900f, -900f, -180f, 240f, "weapon_knife", true, true, false,
            currentDestination: "tr_a_ramp_staging_wait", currentSector: "A", currentRole: "EntryFragger",
            hasContact: false, tookDamage: false, hostileUtility: false, hasC4: true, planTargetBombsite: "B");
        Assert.False(dec.CanaryControlling);
        Assert.Equal("UTILITY_AI", dec.Authority);
        Assert.Equal("C4_ROUTE_INCOMPATIBLE", dec.AbortOrCompletionReason);
        Assert.False(guard.Records[0].BombsiteCompatible);
    }

    [Fact]
    public void PlannerCannotDropBomb()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_c4", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false, hasC4: true, planTargetBombsite: "A", bombCarrierSlot: 2));
        var dec = guard.EvaluateTick(1, 2, 112, 1100f, -650f, -210f, 235f, "weapon_knife", true, true, false,
            currentDestination: "tr_a_ramp_staging_wait", currentSector: "A", currentRole: "EntryFragger",
            hasContact: false, tookDamage: false, hostileUtility: false, hasC4: true, planTargetBombsite: "A");
        Assert.True(dec.CanaryControlling);
        Assert.DoesNotContain("DROP", dec.DispatchReason, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("DROP", dec.TransitionCommandEvent, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void PlannerCannotTriggerPlant()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_c4", "T", "EntryFragger", "a_default_plant_headshot", "Bombsite A", 1248f, -352f, -168f, -632.7f, -2183.1f, -180f, 100, true, false, hasC4: true, planTargetBombsite: "A", bombCarrierSlot: 2));
        var dec = guard.EvaluateTick(1, 2, 120, -632.7f, -2183.1f, -180f, 0f, "weapon_ak47", true, true, false,
            currentDestination: "a_default_plant_headshot", currentSector: "Bombsite A", currentRole: "EntryFragger",
            hasContact: false, tookDamage: false, hostileUtility: false, hasC4: true, planTargetBombsite: "A");
        Assert.DoesNotContain("PLANT", dec.DispatchReason, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("IN_USE", dec.TransitionCommandEvent, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void TrRoutePreservesRole()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_awp", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1248f, -352f, -168f, 368f, -223f, -167.7f, 100, out var sug));
        Assert.Equal("AWPer", sug!.Role);

        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_awp", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1248f, -352f, -168f, 368f, -223f, -167.7f, 100, true, false));
        var dec = guard.EvaluateTick(1, 2, 110, 1100f, -200f, -200f, 240f, "weapon_knife", true, true, false,
            currentDestination: "mid_top_mid_boxes", currentSector: "MID", currentRole: "Lurker",
            hasContact: false, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("CANARY_ABORTED:ROLE_IMMUTABLE", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void TrRoutePreservesSector()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false));
        var dec = guard.EvaluateTick(1, 2, 110, 900f, 400f, -180f, 240f, "weapon_knife", true, true, false,
            currentDestination: "tr_b_apps_house_staging", currentSector: "Bombsite A", currentRole: "EntryFragger",
            hasContact: false, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("CANARY_ABORTED:SECTOR_IMMUTABLE", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void ARampUsesAuthorizedCorridor()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, out var sug));
        Assert.Equal("T_A_RAMP", sug!.AllowedCorridor);
        Assert.Contains("B_APPS", sug.ForbiddenCorridors);
        Assert.Contains("CT_SPAWN", sug.ForbiddenCorridors);
    }

    [Fact]
    public void PalaceUsesAuthorizedCorridor()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "Lurker", "a_palace_deep_room", "Palácio A", 1248f, -352f, -168f, 90f, -2244.6f, -40f, 100, out var sug));
        Assert.Equal("T_A_PALACE", sug!.AllowedCorridor);
        Assert.Contains("t_palace_ramp_entry", sug.OrderedWaypoints.Select(w => w.Name));
    }

    [Fact]
    public void TopMidUsesAuthorizedCorridor()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "MidControl", "mid_top_mid_boxes", "Top Mid", 1248f, -352f, -168f, 368f, -223f, -167.7f, 100, out var sug));
        Assert.Equal("T_TOP_MID", sug!.AllowedCorridor);
        Assert.Contains("t_top_mid_alley", sug.OrderedWaypoints.Select(w => w.Name));
    }

    [Fact]
    public void BAppsUsesAuthorizedCorridor()
    {
        var planner = new OpeningRoutePlanner();
        Assert.True(planner.TryPlanOpeningRouteForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_kitchen_control", "Apartamentos B", 1136f, -64f, -164f, -1111.7f, 687f, -80f, 100, out var sug));
        Assert.Equal("T_B_APPS", sug!.AllowedCorridor);
        Assert.Contains("t_b_house_entry", sug.OrderedWaypoints.Select(w => w.Name));
    }

    [Fact]
    public void TrGeometricTransitionsProjectToNavMesh()
    {
        var nav = NavMeshGraph.Default!;
        var planner = new OpeningRoutePlanner();
        var guard = CreateTrGuard();

        var spots = new (string Id, string Sector, float X, float Y, float Z)[]
        {
            ("tr_a_ramp_staging_wait", "Rampa A", 320f, -1590f, -168f),
            ("a_palace_deep_room", "Palácio A", 90f, -2244.6f, -40f),
            ("a_tetris_corner_ramp_palace", "Bombsite A", -305.7f, -1606.7f, -168f),
            ("mid_top_mid_boxes", "Top Mid", 368f, -223f, -167.7f),
            ("mid_underground_sub", "Underground", -1030.2f, -428.9f, -321.5f),
            ("mid_connector_bottom", "Conector", -576.2f, -1082.4f, -168f),
            ("tr_b_apps_house_staging", "Apartamentos B", -764.4f, 522.1f, -77f),
            ("tr_b_apps_kitchen_control", "Apartamentos B", -1111.7f, 687f, -80f),
            ("tr_b_tapete_window_market_awp", "Apartamentos B", -1590.2f, 708.2f, -48f),
        };

        int round = 1;
        foreach (var s in spots)
        {
            Assert.True(planner.TryPlanOpeningRouteForRound(round++, 2, "t_2", "T", "EntryFragger", s.Id, s.Sector, 1248f, -352f, -168f, s.X, s.Y, s.Z, 100, out var sug));
            Assert.True(guard.ValidateRouteWaypointsOnNavMesh(sug!, out _, out var reason), $"{s.Id}: {reason}");
            foreach (var wp in sug!.OrderedWaypoints)
            {
                var proj = nav.ProjectPoint(wp.X, wp.Y, wp.Z, maxSnapUnits: 32f);
                Assert.True(proj.AreaId > 0, $"{s.Id}/{wp.Name} failed NavMesh projection");
                Assert.True(proj.DeltaUnits <= 32f, $"{s.Id}/{wp.Name} delta {proj.DeltaUnits} > 32u");
            }
        }
    }

    [Fact]
    public void KnifeCannotCrossTrThreatLine()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "AWPer", "mid_top_mid_boxes", "Top Mid", 1248f, -352f, -168f, 368f, -223f, -167.7f, 100, true, false));
        var session = guard.GetSessionForRound(1)!;
        var tl = session.Route.WeaponReadyWaypoint;
        var dec = guard.EvaluateTick(1, 2, session.Route.ThreatLineTick, tl.X, tl.Y, tl.Z, 240f, "weapon_knife", true, true, false,
            currentDestination: "mid_top_mid_boxes", currentSector: "MID", currentRole: "AWPer",
            hasContact: false, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("WEAPON_SWITCH_FAILED", dec.AbortOrCompletionReason);
    }

    [Fact]
    public void ContactReleasesLease()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false));
        var dec = guard.EvaluateTick(1, 2, 120, 800f, -1000f, -180f, 240f, "weapon_ak47", true, true, false,
            currentDestination: "tr_a_ramp_staging_wait", currentSector: "A", currentRole: "EntryFragger",
            hasContact: true, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("CONTACT_INTERRUPTION", dec.AbortOrCompletionReason);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
    }

    [Fact]
    public void UtilityPlanChangeReleasesLease()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_b_apps_house_staging", "Apartamentos B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, 100, true, false));
        var dec = guard.EvaluateTick(1, 2, 120, 800f, 500f, -200f, 240f, "weapon_knife", true, true, false,
            currentDestination: "tr_a_ramp_staging_wait", currentSector: "Apartamentos B", currentRole: "EntryFragger",
            hasContact: false, tookDamage: false, hostileUtility: false);
        Assert.False(dec.CanaryControlling);
        Assert.Equal("CANARY_ABORTED:UTILITY_PLAN_CHANGED", dec.AbortOrCompletionReason);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
    }

    [Fact]
    public void ContinuousJumpIsImpossible()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "a_tetris_top_control", "Bombsite A", 1248f, -352f, -168f, -203.5f, -1600.8f, -54f, 100, true, false));
        var session = guard.GetSessionForRound(1)!;
        // Avança até o waypoint final (STEP_UP)
        session.WaypointIndex = session.Route.OrderedWaypoints.Count - 1;
        int jumpTicks = 0;
        for (int t = 200; t < 260; t++)
        {
            var dec = guard.EvaluateTick(1, 2, t, -290f, -1605f, -168f, 18f, "weapon_ak47", true, true, false,
                currentDestination: "a_tetris_top_control", currentSector: "Bombsite A", currentRole: "EntryFragger",
                hasContact: false, tookDamage: false, hostileUtility: false);
            if (dec.ShouldEmitJumpPulse) jumpTicks++;
            if (!dec.CanaryControlling) break;
        }
        Assert.True(jumpTicks <= 1);
        Assert.Equal(0, session.TransitionExecutor.ContinuousJumpViolations);
    }

    [Fact]
    public void NonCanaryBotsRemainUtilityControlled()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false));
        for (int slot = 0; slot < 10; slot++)
        {
            if (slot == 2) continue;
            Assert.False(guard.IsSlotActiveCanary(1, slot));
            Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(slot, 1));
        }
    }

    [Fact]
    public void CtApprovedRoutesRemainUnchanged()
    {
        var ctPlanner = new OpeningRoutePlanner();
        Assert.True(ctPlanner.TryPlanOpeningRouteForRound(1, 0, "ct_0", "CT", "Rotator", "a_triple_box_hold", "Bombsite A", -1400f, -2080f, -195f, -660.9f, -2198.9f, -180f, 100, out var aRoute));
        Assert.Equal("CT_A_TICKET", aRoute!.AllowedCorridor);
        Assert.Empty(aRoute.TransitionWaypoints);
        Assert.Equal("ct_ticket_booth", aRoute.OrderedWaypoints[0].Name);
        Assert.True(GeometricTransitionCatalog.IsProtectedApprovedARoute("CT", "A_TICKET"));
        Assert.True(GeometricTransitionCatalog.IsProtectedApprovedARoute("CT", "A_JUNGLE"));
        Assert.Contains("b_forest_bench_hold_apps", OpeningRouteCanaryAllowlist.CtAllowedSpots);
        Assert.Contains("mid_window_right_deep", OpeningRouteCanaryAllowlist.CtAllowedSpots);
    }

    [Fact]
    public void RouteAndAuthorityAccountingClose()
    {
        var guard = CreateTrGuard();
        Assert.True(guard.TryStartCanaryForRound(1, 2, "t_2", "T", "EntryFragger", "tr_a_ramp_staging_wait", "Rampa A", 1248f, -352f, -168f, 320f, -1590f, -168f, 100, true, false));
        var session = guard.GetSessionForRound(1)!;
        session.WaypointIndex = session.Route.OrderedWaypoints.Count - 1;
        CanaryTickDecision? lastDec = null;
        for (int t = 180; t <= 186; t++)
        {
            lastDec = guard.EvaluateTick(1, 2, t, 320f, -1590f, -168f, 0f, "weapon_ak47", true, true, false,
                currentDestination: "tr_a_ramp_staging_wait", currentSector: "A", currentRole: "EntryFragger",
                hasContact: false, tookDamage: false, hostileUtility: false);
            if (!lastDec.CanaryControlling) break;
        }
        Assert.NotNull(lastDec);
        Assert.False(lastDec!.CanaryControlling);
        Assert.Equal("ROUTE_COMPLETED", lastDec.AbortOrCompletionReason);
        Assert.Single(guard.Records);
        Assert.NotNull(guard.Records[0].AuthorityReturnTick);
        Assert.Null(guard.LeaseManager.ActiveLease);
        Assert.False(guard.LeaseManager.IsSlotLeasedByCanary(2, 1));
    }

    [Fact]
    public void TrGeometricHarnessSimulationPassesGates()
    {
        var specs = new (string Group, string SpotId, string Sector, string CanonicalSector, float Sx, float Sy, float Sz, float Tx, float Ty, float Tz, bool HasC4, string PlanSite)[]
        {
            ("A_Ramp_Palace", "tr_a_ramp_staging_wait", "Rampa A", "A", 1248f, -352f, -168f, 320f, -1590f, -168f, false, "A"),
            ("A_Ramp_Palace", "a_palace_deep_room", "Palácio A", "A", 1248f, -352f, -168f, 90f, -2244.6f, -40f, false, "A"),
            ("TopMid_Underpass", "mid_top_mid_boxes", "Top Mid", "MID", 1248f, -352f, -168f, 368f, -223f, -167.7f, false, "A"),
            ("TopMid_Underpass", "mid_underground_sub", "Underground", "MID", 1248f, -352f, -168f, -1030.2f, -428.9f, -321.5f, false, "B"),
            ("B_Apps_House", "tr_b_apps_house_staging", "Apartamentos B", "B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, false, "B"),
            ("B_Apps_House", "tr_b_apps_kitchen_control", "Apartamentos B", "B", 1136f, -64f, -164f, -1111.7f, 687f, -80f, false, "B"),
            ("C4_Compatible", "tr_a_ramp_staging_wait", "Rampa A", "A", 1248f, -352f, -168f, 320f, -1590f, -168f, true, "A"),
            ("C4_Compatible", "tr_b_apps_house_staging", "Apartamentos B", "B", 1136f, -64f, -164f, -764.4f, 522.1f, -77f, true, "B"),
        };

        var byGroup = new Dictionary<string, (int Reps, int Completed, int InvalidPath, int AuthViol, int ContJump, int DestChange, int SiteChange, int C4Incompat)>();
        int totalCompleted = 0;
        int totalReps = 0;

        int roundCounter = 1;
        foreach (var sp in specs)
        {
            if (!byGroup.ContainsKey(sp.Group)) byGroup[sp.Group] = (0, 0, 0, 0, 0, 0, 0, 0);
            for (int r = 0; r < 5; r++)
            {
                totalReps++;
                var guard = CreateTrGuard();
                bool started = guard.TryStartCanaryForRound(
                    roundCounter, 2, "t_sim", "T", "EntryFragger",
                    sp.SpotId, sp.Sector, sp.Sx, sp.Sy, sp.Sz, sp.Tx, sp.Ty, sp.Tz,
                    100, true, false, hasC4: sp.HasC4, planTargetBombsite: sp.PlanSite, bombCarrierSlot: sp.HasC4 ? 2 : null);

                var cur = byGroup[sp.Group];
                cur.Reps++;
                if (!started)
                {
                    cur.InvalidPath++;
                    byGroup[sp.Group] = cur;
                    roundCounter++;
                    continue;
                }

                var session = guard.GetSessionForRound(roundCounter)!;
                float x = sp.Sx, y = sp.Sy, z = sp.Sz;
                bool completed = false;
                bool switchedWeapon = false;
                for (int t = 101; t < 1600; t++)
                {
                    var wps = session.Route.OrderedWaypoints;
                    var wp = wps[Math.Min(session.WaypointIndex, wps.Count - 1)];
                    float dx = wp.X - x, dy = wp.Y - y, dz = wp.Z - z;
                    float d = MathF.Sqrt(dx * dx + dy * dy + dz * dz);
                    if (d > 1f)
                    {
                        float step = MathF.Min(d, 3.7f);
                        x += dx / d * step;
                        y += dy / d * step;
                        z += dz / d * step;
                    }
                    string weap = (switchedWeapon || t >= session.Route.WeaponSwitchTick - 4) ? "weapon_ak47" : "weapon_knife";
                    var dec = guard.EvaluateTick(roundCounter, 2, t, x, y, z, 235f, weap, true, true, false,
                        currentDestination: sp.SpotId, currentSector: sp.CanonicalSector, currentRole: "EntryFragger",
                        hasContact: false, tookDamage: false, hostileUtility: false, hasC4: sp.HasC4, planTargetBombsite: sp.PlanSite);
                    if (dec.ShouldSwitchToWeapon) switchedWeapon = true;
                    if (!dec.CanaryControlling)
                    {
                        completed = dec.AbortOrCompletionReason == "ROUTE_COMPLETED";
                        break;
                    }
                }

                if (completed) { cur.Completed++; totalCompleted++; }
                cur.ContJump += session.TransitionExecutor.ContinuousJumpViolations;
                if (guard.Records.Any(rec => rec.IntendedDestination != sp.SpotId)) cur.DestChange++;
                if (guard.Records.Any(rec => rec.PlannedBombsite != sp.PlanSite)) cur.SiteChange++;
                if (guard.Records.Any(rec => !rec.BombsiteCompatible)) cur.C4Incompat++;
                byGroup[sp.Group] = cur;
                roundCounter++;
            }
        }

        string outDir = Path.Combine(FindRepoRoot(), "training_runs", "positioning_v2_real_temporal", "opening_route_canary_v1", "tr_canary_v1");
        Directory.CreateDirectory(outDir);
        var payload = new
        {
            marco = "2B.8.5",
            data_nature = "SIMULATED",
            generated_at_utc = DateTime.UtcNow.ToString("O"),
            total_repetitions = totalReps,
            total_completed = totalCompleted,
            completion_rate = Math.Round((double)totalCompleted / totalReps, 4),
            invalid_path_total = byGroup.Values.Sum(v => v.InvalidPath),
            authority_violation_total = byGroup.Values.Sum(v => v.AuthViol),
            continuous_jump_total = byGroup.Values.Sum(v => v.ContJump),
            destination_changed_total = byGroup.Values.Sum(v => v.DestChange),
            bombsite_changed_total = byGroup.Values.Sum(v => v.SiteChange),
            c4_incompatibilities_total = byGroup.Values.Sum(v => v.C4Incompat),
            gates_passed = byGroup.Values.All(v => v.Completed >= 9 && v.InvalidPath == 0 && v.AuthViol == 0 && v.ContJump == 0 && v.DestChange == 0 && v.SiteChange == 0 && v.C4Incompat == 0),
            by_group = byGroup.ToDictionary(
                kv => kv.Key,
                kv => new
                {
                    repetitions = kv.Value.Reps,
                    completed = kv.Value.Completed,
                    completion_rate = Math.Round((double)kv.Value.Completed / kv.Value.Reps, 4),
                    invalid_path_count = kv.Value.InvalidPath,
                    authority_violation_count = kv.Value.AuthViol,
                    continuous_jump_count = kv.Value.ContJump,
                    destination_changed_count = kv.Value.DestChange,
                    bombsite_changed_count = kv.Value.SiteChange,
                    c4_incompatibilities = kv.Value.C4Incompat,
                })
        };
        File.WriteAllText(Path.Combine(outDir, "geometric_harness_metrics.json"), JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));

        Assert.Equal(40, totalReps);
        Assert.True(payload.gates_passed);
    }
}
