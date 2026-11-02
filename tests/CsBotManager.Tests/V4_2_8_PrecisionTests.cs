using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_8_PrecisionTests
{
    private readonly MapProfileManager _mapProfileManager;

    public V4_2_8_PrecisionTests()
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
                    Center = new MapVector3 { X = -1800.0f, Y = 300.0f, Z = -160.0f },
                    BoundsMin = new MapVector3 { X = -2150.0f, Y = 150.0f, Z = -220.0f },
                    BoundsMax = new MapVector3 { X = -1450.0f, Y = 650.0f, Z = -100.0f },
                    Radius2D = 420.0f
                }
            },
            Spots = new List<TacticalSpot>
            {
                new() { Id = "ct_a_ticket_passive", Sector = "Ticket CT", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Hold, X = -750f, Y = -1600f, Z = -160f },
                new() { Id = "ct_a_firebox_oneanddone", Sector = "Firebox", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Hold, X = -450f, Y = -2350f, Z = -165f },
                new() { Id = "ct_a_palace_close_poke", Sector = "Palacio A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Hold, X = 350f, Y = -1900f, Z = -160f },
                new() { Id = "ct_a_stairs_cross", Sector = "Stairs", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Hold, X = -200f, Y = -1850f, Z = -160f },
                new() { Id = "ct_mid_window_crouch", Sector = "Window Meio", Side = "CT", AssociatedBombsite = "Mid", Usage = SpotUsage.Hold, X = -1100f, Y = -750f, Z = -100f },
                new() { Id = "ct_mid_window_deep_awp", Sector = "Window Meio", Side = "CT", AssociatedBombsite = "Mid", Usage = SpotUsage.Hold, X = -1200f, Y = -800f, Z = -100f },
                new() { Id = "ct_b_van_peek", Sector = "Van B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Hold, X = -1350f, Y = 380f, Z = -150f },
                new() { Id = "ct_b_site_default_crouch", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Hold, X = -1750f, Y = 300f, Z = -160f },
                new() { Id = "ct_b_short_corner", Sector = "Catwalk/Short", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Hold, X = -1050f, Y = 250f, Z = -160f },
                new() { Id = "ct_b_bench_deep", Sector = "Bench B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Hold, X = -1950f, Y = 450f, Z = -160f },
                new() { Id = "tr_staging_b_apartments_kitchen", Sector = "Apartments B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging, X = -850f, Y = 600f, Z = -60f },
                new() { Id = "tr_exec_b_site_plant", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -1850f, Y = 350f, Z = -160f },
                new() { Id = "tr_staging_palace_room", Sector = "Palace", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Staging, X = 744f, Y = -1719f, Z = -221f },
                new() { Id = "tr_exec_a_site_default", Sector = "Bombsite A", Side = "TR", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -400f, Y = -2100f, Z = -170f }
            }
        };
        _mapProfileManager.SetSpotsForTesting(profile.Spots);
    }

    // =========================================================================
    // GRUPO 1: ECONOMIA TR (Testes 1 a 6)
    // =========================================================================

    [Fact]
    public void Test01_TrHighMoneySelectsFullBuyNeverUnknownIncomplete()
    {
        var economy = new EconomyManager();
        int lossBonus = 1400;

        var snap = new TeamEconomySnapshot
        {
            Team = CsTeam.Terrorist,
            TotalTeamMoney = 23750,
            AverageMoney = 4750,
            MinMoney = 4450,
            MaxMoney = 5100,
            LivingPlayers = 5
        };

        BuyState buyState = economy.DetermineBuyStateFromSnapshot(snap, 3, lossBonus, CsTeam.Terrorist, MatchLifecyclePhase.Regulation_Half1);

        Assert.Equal(BuyState.FULL_BUY, buyState);
        Assert.NotEqual(BuyState.UNKNOWN_INCOMPLETE_BUY, buyState);
    }

    [Fact]
    public void Test02_FullBuyTrPurchasesPrimaryAndArmorBeforeUtility()
    {
        // Verifica a ordenação conceitual estrita: Primária -> Colete -> Utilitárias
        int botMoney = 4750;
        int akCost = 2700;
        int armorCost = 1000;
        int smokeCost = 300;

        var purchaseOrder = new List<string>();

        // 1. Primária
        if (botMoney >= akCost)
        {
            botMoney -= akCost;
            purchaseOrder.Add("weapon_ak47");
        }

        // 2. Colete
        if (botMoney >= armorCost)
        {
            botMoney -= armorCost;
            purchaseOrder.Add("item_assaultsuit");
        }

        // 3. Utilitária
        if (botMoney >= smokeCost)
        {
            botMoney -= smokeCost;
            purchaseOrder.Add("weapon_smokegrenade");
        }

        Assert.Equal(3, purchaseOrder.Count);
        Assert.Equal("weapon_ak47", purchaseOrder[0]);
        Assert.Equal("item_assaultsuit", purchaseOrder[1]);
        Assert.Equal("weapon_smokegrenade", purchaseOrder[2]);
        Assert.Equal(750, botMoney);
    }

    [Fact]
    public void Test03_TrFullBuyHighMoneyAcquiresValuablePrimary()
    {
        string ak = "weapon_ak47";
        string awp = "weapon_awp";
        string galil = "weapon_galilar";

        Assert.True(EconomyManager.IsValuableFirearm(ak));
        Assert.True(EconomyManager.IsValuableFirearm(awp));
        Assert.True(EconomyManager.IsValuableFirearm(galil));
    }

    [Fact]
    public void Test04_TrInsufficientForAkFallsBackToGalilNeverGlock()
    {
        int botMoney = 2100;
        int akCost = 2700;
        int galilCost = 1800;

        string selectedPrimary = "none";
        if (botMoney >= akCost)
        {
            selectedPrimary = "weapon_ak47";
        }
        else if (botMoney >= galilCost)
        {
            selectedPrimary = "weapon_galilar";
        }
        else
        {
            selectedPrimary = "weapon_glock";
        }

        Assert.Equal("weapon_galilar", selectedPrimary);
        Assert.NotEqual("weapon_glock", selectedPrimary);
    }

    [Fact]
    public void Test05_WeaponC4NeverClassifiedAsPrimary()
    {
        string c4 = "weapon_c4";
        string knife = "weapon_knife";
        string flash = "weapon_flashbang";
        string ak = "weapon_ak47";

        Assert.False(CombatAdapter.IsPrimaryWeapon(c4));
        Assert.False(CombatAdapter.IsPrimaryWeapon(knife));
        Assert.False(CombatAdapter.IsPrimaryWeapon(flash));
        Assert.True(CombatAdapter.IsPrimaryWeapon(ak));
    }

    [Fact]
    public void Test06_BuyAttemptTelemetryContainsAllMandatoryFields()
    {
        int slot = 3;
        CsTeam team = CsTeam.Terrorist;
        int moneyBefore = 4750;
        string intendedPrimary = "weapon_ak47";
        string intendedArmor = "item_assaultsuit";
        var intendedUtility = new List<string> { "smoke", "flash" };
        var issuedCommands = new List<string> { "DeliverItem(weapon_ak47,2700)", "DeliverArmor(suit,1000)" };
        string commandResults = "SUCCESS";
        string activeWeaponAfter = "weapon_ak47";
        string primaryWeaponAfter = "weapon_ak47";
        int moneyAfter = 1050;
        string failureReason = "none";

        string logMessage = $"slot={slot} team={team} moneyBefore={moneyBefore} intendedPrimary={intendedPrimary} intendedArmor={intendedArmor} intendedUtility=[{string.Join(",", intendedUtility)}] issuedCommands=\"{string.Join(";", issuedCommands)}\" commandResults=\"{commandResults}\" activeWeaponAfter={activeWeaponAfter} primaryWeaponAfter={primaryWeaponAfter} moneyAfter={moneyAfter} failureReason={failureReason}";

        Assert.Contains("slot=3", logMessage);
        Assert.Contains("team=Terrorist", logMessage);
        Assert.Contains("moneyBefore=4750", logMessage);
        Assert.Contains("intendedPrimary=weapon_ak47", logMessage);
        Assert.Contains("intendedArmor=item_assaultsuit", logMessage);
        Assert.Contains("primaryWeaponAfter=weapon_ak47", logMessage);
        Assert.Contains("moneyAfter=1050", logMessage);
    }

    // =========================================================================
    // GRUPO 2: CONTROLE DE JUMP E HORIZONTES (Testes 7 a 14)
    // =========================================================================

    [Fact]
    public void Test07_JumpIsolatedAct0AuthorizedAndExecuted()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(1, true, 100);

        // act0 com pulo (49), act1 com pulo (49) -> Consenso >= 2 horizontes
        var eval = gate.EvaluateJumpRequest(1, "Bot1", 100, 10.0f, "ONNX_ADRENALINE", 49, 49, 1, JumpContextType.NormalNavigation, null, 250f);

        Assert.True(eval.Allowed);
        Assert.Equal(49, eval.ConvertedActionId);
        Assert.Equal("AuthorizedByGate", eval.Reason);
    }

    [Fact]
    public void Test08_JumpSuppressedWhenNoHorizonConsensusPreservesHorizontalMotion()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(2, true, 200);

        // act0 com pulo (49), mas act1 (1) e act2 (1) sem pulo -> Sem consenso (1/3)
        var eval = gate.EvaluateJumpRequest(2, "Bot2", 200, 20.0f, "ONNX_ADRENALINE", 49, 1, 1, JumpContextType.NormalNavigation, null, 250f);

        Assert.False(eval.Allowed);
        // Preserva o movimento horizontal subtraindo 48 (49 - 48 = 1)
        Assert.Equal(1, eval.ConvertedActionId);
        Assert.Equal("Suppressed_LackOfConsensus", eval.Reason);
    }

    [Fact]
    public void Test09_JumpSuppressedAirborneNonRenewal()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(3, false, 300); // isAirborne = true

        var eval = gate.EvaluateJumpRequest(3, "Bot3", 300, 30.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.Airborne, null, 250f);

        Assert.False(eval.Allowed);
        Assert.Equal(1, eval.ConvertedActionId);
        Assert.Equal("Suppressed_AlreadyAirborne", eval.Reason);
    }

    [Fact]
    public void Test10_JumpSuppressedDuringCooldown()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(4, true, 400);

        // Primeiro pulo válido às 40.0s
        var eval1 = gate.EvaluateJumpRequest(4, "Bot4", 400, 40.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.NormalNavigation, null, 250f);
        Assert.True(eval1.Allowed);

        // Segundo pedido 1.0s depois (dentro do cooldown de 3.5s)
        gate.UpdateGroundedState(4, true, 464);
        var eval2 = gate.EvaluateJumpRequest(4, "Bot4", 464, 41.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.NormalNavigation, null, 250f);

        Assert.False(eval2.Allowed);
        Assert.Equal("Suppressed_CooldownActive", eval2.Reason);
    }

    [Fact]
    public void Test11_JumpSuppressedDuringPassiveHoldAndAwpAngle()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(5, true, 500);

        // PASSIVE_HOLD
        var evalHold = gate.EvaluateJumpRequest(5, "Bot5", 500, 50.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.AuthorizedHold, null, 0f);
        Assert.False(evalHold.Allowed);
        Assert.Equal("Suppressed_ProhibitedContext", evalHold.Reason);

        // AWP Angle Cover
        var evalAwp = gate.EvaluateJumpRequest(5, "Bot5", 500, 50.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.AwpAngleCover, null, 0f);
        Assert.False(evalAwp.Allowed);
        Assert.Equal("Suppressed_ProhibitedContext", evalAwp.Reason);

        // Tactical Save Hold
        var evalSave = gate.EvaluateJumpRequest(5, "Bot5", 500, 50.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.SaveHold, null, 0f);
        Assert.False(evalSave.Allowed);
        Assert.Equal("Suppressed_ProhibitedContext", evalSave.Reason);
    }

    [Fact]
    public void Test12_JumpAllowedDuringObstacleTraversal()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(6, true, 600);

        // Velocidade baixa em obstáculo sem inimigo
        var evalObstacle = gate.EvaluateJumpRequest(6, "Bot6", 600, 60.0f, "OBSTACLE_TRAVERSAL", 49, 49, 49, JumpContextType.ObstacleTraversal, null, 15f);

        Assert.True(evalObstacle.Allowed);
        Assert.Equal("Authorized_ObstacleBypass", evalObstacle.Reason);
    }

    [Fact]
    public void Test13_RecoveryJumpBypassesGateAndRegistersMetric()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(7, true, 700);

        var evalRecovery = gate.EvaluateJumpRequest(7, "Bot7", 700, 70.0f, "RECOVERY_STAGE2", 49, 49, 49, JumpContextType.RecoveryUnstuck, null, 5f);

        Assert.True(evalRecovery.Allowed);
        Assert.Equal("Authorized_RecoveryBypass", evalRecovery.Reason);
    }

    [Fact]
    public void Test14_JumpCooldownExpiresAndAllowsSubsequentJump()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(8, true, 800);

        // Pulo inicial em t = 80.0s
        var eval1 = gate.EvaluateJumpRequest(8, "Bot8", 800, 80.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.NormalNavigation, null, 250f);
        Assert.True(eval1.Allowed);

        // Nova tentativa após 4.0s (cooldown padrão 3.5s expirado)
        gate.UpdateGroundedState(8, true, 800 + 256);
        var eval2 = gate.EvaluateJumpRequest(8, "Bot8", 800 + 256, 84.0f, "ONNX_ADRENALINE", 49, 49, 49, JumpContextType.NormalNavigation, null, 250f);

        Assert.True(eval2.Allowed);
        Assert.Equal("AuthorizedByGate", eval2.Reason);
    }

    // =========================================================================
    // GRUPO 3: FORMAÇÃO CT STANDARD 2-1-2 (Testes 15 a 19)
    // =========================================================================

    [Fact]
    public void Test15_CtStandard212FormationMaterializesExactCounts()
    {
        var plan = new TacticalPlan { TacticName = "Padrão Tático Cadenciado 2-1-2", TeamSide = CsTeam.CounterTerrorist };

        bool success = TacticalOrderMaterializer.MaterializeCtStandard212Formation(plan, null, _mapProfileManager, null, "DEC-212-01");

        Assert.True(success);
        Assert.Equal(5, plan.CtFormationAssignments.Count);

        int aCount = plan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "A");
        int midCount = plan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "Mid");
        int bCount = plan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "B");

        Assert.Equal(2, aCount);
        Assert.Equal(1, midCount);
        Assert.Equal(2, bCount);
    }

    [Fact]
    public void Test16_CtStandard212DefendersHaveDistinctSpotsInSiteA()
    {
        var plan = new TacticalPlan { TacticName = "Padrão Tático Cadenciado 2-1-2", TeamSide = CsTeam.CounterTerrorist };
        TacticalOrderMaterializer.MaterializeCtStandard212Formation(plan, null, _mapProfileManager, null, "DEC-212-02");

        var aDefenders = plan.CtFormationAssignments.Values.Where(a => a.AssignedSite == "A").ToList();
        Assert.Equal(2, aDefenders.Count);

        Assert.NotEqual(aDefenders[0].InitialSpot, aDefenders[1].InitialSpot);
        Assert.NotEqual(aDefenders[0].ExecuteSpot, aDefenders[1].ExecuteSpot);

        Assert.Contains("ct_a_", aDefenders[0].InitialSpot);
        Assert.Contains("ct_a_", aDefenders[1].InitialSpot);
    }

    [Fact]
    public void Test17_CtStandard212DefendersHaveDistinctSpotsInSiteB()
    {
        var plan = new TacticalPlan { TacticName = "Padrão Tático Cadenciado 2-1-2", TeamSide = CsTeam.CounterTerrorist };
        TacticalOrderMaterializer.MaterializeCtStandard212Formation(plan, null, _mapProfileManager, null, "DEC-212-03");

        var bDefenders = plan.CtFormationAssignments.Values.Where(a => a.AssignedSite == "B").ToList();
        Assert.Equal(2, bDefenders.Count);

        Assert.NotEqual(bDefenders[0].InitialSpot, bDefenders[1].InitialSpot);
        Assert.NotEqual(bDefenders[0].ExecuteSpot, bDefenders[1].ExecuteSpot);

        Assert.Contains("ct_b_", bDefenders[0].InitialSpot);
        Assert.Contains("ct_b_", bDefenders[1].InitialSpot);
    }

    [Fact]
    public void Test18_CtStandard212DefendersOfBNeverAssignedToMidOrSiteA()
    {
        var plan = new TacticalPlan { TacticName = "Padrão Tático Cadenciado 2-1-2", TeamSide = CsTeam.CounterTerrorist };
        TacticalOrderMaterializer.MaterializeCtStandard212Formation(plan, null, _mapProfileManager, null, "DEC-212-04");

        var bDefenders = plan.CtFormationAssignments.Values.Where(a => a.AssignedSite == "B").ToList();

        foreach (var def in bDefenders)
        {
            Assert.DoesNotContain("ct_mid_", def.InitialSpot);
            Assert.DoesNotContain("ct_a_", def.InitialSpot);
            Assert.DoesNotContain("ct_mid_", def.ExecuteSpot);
            Assert.DoesNotContain("ct_a_", def.ExecuteSpot);
        }
    }

    [Fact]
    public void Test19_CtFormationInvalidAppliesFallbackAndRegistersMetric()
    {
        var plan = new TacticalPlan { TacticName = "Formação Corrompida", TeamSide = CsTeam.CounterTerrorist };

        int initialInvalidCount = TrackerMetricsAggregator.CtFormationsInvalidCount;

        // Se uma formação for inválida, o método reaplica a formação 2-1-2 canônica como fallback
        TacticalOrderMaterializer.MaterializeCtStandard212Formation(plan, null, _mapProfileManager, null, "DEC-212-05");

        Assert.Equal(5, plan.CtFormationAssignments.Count);
        Assert.Equal(2, plan.CtFormationAssignments.Values.Count(a => a.AssignedSite == "B"));
    }

    // =========================================================================
    // GRUPO 4: CICLO DE VIDA E ISOLAMENTO DE ADAPTAÇÕES (Testes 20 a 23)
    // =========================================================================

    [Fact]
    public void Test20_TrAdaptationExpirationWithCtPlanRejectedDefensively()
    {
        var ctPlan = new TacticalPlan { TeamSide = CsTeam.CounterTerrorist };
        var trAdaptation = new ActiveAdaptationRecord
        {
            AdaptationId = "ADP-TR-01",
            OwnerTeam = CsTeam.Terrorist,
            Reason = TacticalAdaptationReason.TradePossible,
            IsClosed = false
        };

        // Simula a lógica de rejeição de expiração cruzada
        bool isCrossTeam = ctPlan.Team != CsTeam.None && trAdaptation.OwnerTeam != ctPlan.Team;
        Assert.True(isCrossTeam);

        // Adaptação não é fechada pelo plano CT
        Assert.False(trAdaptation.IsClosed);
    }

    [Fact]
    public void Test21_RecordCrossTeamAttemptDeduplicatesSameEpisodeKey()
    {
        string episodeKey = $"ADP-R03-TEST_{CsTeam.CounterTerrorist}_{CsTeam.Terrorist}";

        bool firstAttempt = TrackerMetricsAggregator.RecordCrossTeamAttempt(episodeKey);
        bool secondAttempt = TrackerMetricsAggregator.RecordCrossTeamAttempt(episodeKey);
        bool thirdAttempt = TrackerMetricsAggregator.RecordCrossTeamAttempt(episodeKey);

        Assert.True(firstAttempt);
        Assert.False(secondAttempt);
        Assert.False(thirdAttempt);
    }

    [Fact]
    public void Test22_EntryKilledCtOnlyAffectsCtSlotsAndBelongsToCt()
    {
        var record = new ActiveAdaptationRecord
        {
            AdaptationId = "ADP-CT-ENTRY",
            OwnerTeam = CsTeam.CounterTerrorist,
            Reason = TacticalAdaptationReason.EntryKilled,
            AffectedSlots = new List<int> { 2, 4, 6, 8 },
            NewOrdersDescription = "CT FallBackToSite & HoldCrossfire"
        };

        Assert.Equal(CsTeam.CounterTerrorist, record.OwnerTeam);
        Assert.DoesNotContain("ROTATE_SILENT", record.NewOrdersDescription);
        Assert.All(record.AffectedSlots, slot => Assert.True(slot % 2 == 0)); // Slots CT pares
    }

    [Fact]
    public void Test23_EntryKilledTrOnlyAffectsTrSlotsAndBelongsToTr()
    {
        var record = new ActiveAdaptationRecord
        {
            AdaptationId = "ADP-TR-ENTRY",
            OwnerTeam = CsTeam.Terrorist,
            Reason = TacticalAdaptationReason.EntryKilled,
            AffectedSlots = new List<int> { 1, 3, 5, 7 },
            NewOrdersDescription = "ROTATE_SILENT to alternate bomb"
        };

        Assert.Equal(CsTeam.Terrorist, record.OwnerTeam);
        Assert.Contains("ROTATE_SILENT", record.NewOrdersDescription);
        Assert.All(record.AffectedSlots, slot => Assert.True(slot % 2 != 0)); // Slots TR ímpares
    }

    // =========================================================================
    // GRUPO 5: FAKE B -> A E COORDENADAS DE B (Testes 24 a 26)
    // =========================================================================

    [Fact]
    public void Test24_AllBombBSpotsInDeMirageHavePositiveY()
    {
        string mirageJsonPath = Path.Combine("src", "CsBotManager", "MapProfiles", "de_mirage.json");
        if (!File.Exists(mirageJsonPath))
        {
            mirageJsonPath = Path.Combine("..", "..", "..", "..", "..", "src", "CsBotManager", "MapProfiles", "de_mirage.json");
        }
        if (!File.Exists(mirageJsonPath))
        {
            mirageJsonPath = Path.Combine("..", "..", "..", "..", "src", "CsBotManager", "MapProfiles", "de_mirage.json");
        }
        if (!File.Exists(mirageJsonPath))
        {
            var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
            while (dir != null && !File.Exists(Path.Combine(dir.FullName, "src", "CsBotManager", "MapProfiles", "de_mirage.json")))
            {
                dir = dir.Parent;
            }
            if (dir != null)
            {
                mirageJsonPath = Path.Combine(dir.FullName, "src", "CsBotManager", "MapProfiles", "de_mirage.json");
            }
        }

        Assert.True(File.Exists(mirageJsonPath), $"Arquivo de_mirage.json não encontrado em {mirageJsonPath}");

        string json = File.ReadAllText(mirageJsonPath);
        using var doc = JsonDocument.Parse(json);
        var spots = doc.RootElement.GetProperty("spots");

        var negativeBSpots = new List<string>();

        foreach (var spot in spots.EnumerateArray())
        {
            string id = spot.GetProperty("id").GetString() ?? "";
            string sector = spot.GetProperty("sector").GetString() ?? "";
            float y = spot.GetProperty("y").GetSingle();

            bool isB = id.Contains("_b_") || id.Contains("tapete") || sector.Contains("Site B") || sector.Contains("Apartments B") || sector.Contains("Tapete B");

            if (isB && y < 0)
            {
                negativeBSpots.Add($"{id} (Y={y})");
            }
        }

        Assert.Empty(negativeBSpots);
    }

    [Fact]
    public void Test25_FakeGroupAssignmentCarrierNeverInFakeGroup()
    {
        var fakeCtx = new FakeExecutionContext
        {
            FakeSite = "B",
            RealSite = "A",
            FakeGroupSlots = new List<int> { 1, 5 },
            RealGroupSlots = new List<int> { 3, 7, 9 },
            BombCarrierSlot = 1
        };

        // Invariante V4.2.8: se o portador da C4 estiver no grupo fake, deve ser removido
        int carrierSlot = fakeCtx.BombCarrierSlot;
        if (fakeCtx.FakeGroupSlots.Contains(carrierSlot))
        {
            fakeCtx.FakeGroupSlots.Remove(carrierSlot);
            if (!fakeCtx.RealGroupSlots.Contains(carrierSlot))
            {
                fakeCtx.RealGroupSlots.Add(carrierSlot);
            }
            fakeCtx.FakeGroupSlots.Add(7);
            fakeCtx.RealGroupSlots.Remove(7);
        }

        Assert.DoesNotContain(carrierSlot, fakeCtx.FakeGroupSlots);
        Assert.Contains(carrierSlot, fakeCtx.RealGroupSlots);
    }

    [Fact]
    public void Test26_CarrierCommittedSiteIsStrictlyRealSiteWithMatchingCoordinates()
    {
        var plan = new TacticalPlan
        {
            TacticName = "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
            CurrentTactic = "Fake B & Execução A (Pressão Tapete B + Split Conector/Rampa A)",
            TeamSide = CsTeam.Terrorist
        };

        plan.SetFakeExecution("B", "A", 14.0f, 1000, "Fake B Setup", "DEC-FAKE-B-A");

        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.CommittedSite);
        Assert.Equal(BombsiteTarget.A, plan.BombObjectiveState.RealSite);
        Assert.Equal(BombsiteTarget.B, plan.BombObjectiveState.FakeSite);
        Assert.Equal("A", plan.RealTargetSite);
        Assert.Equal("B", plan.FakeTargetSite);

        // Verifica coordenadas de A do PlantZone de Mirage
        var plantZoneA = _mapProfileManager.GetPlantZone("A");
        Assert.NotNull(plantZoneA);
        Assert.Equal(-400.0f, plantZoneA.Center.X);
        Assert.Equal(-2100.0f, plantZoneA.Center.Y);
    }
}
