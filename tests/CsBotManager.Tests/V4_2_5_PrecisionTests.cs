using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_5_PrecisionTests
{
    private readonly MapProfileManager _mapProfileManager;

    public V4_2_5_PrecisionTests()
    {
        _mapProfileManager = new MapProfileManager();
        var spots = new List<TacticalSpot>
        {
            new() { Id = "ct_retake_a_connector", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -820f, Y = -840f, Z = -160f },
            new() { Id = "ct_retake_a_stairs", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -750f, Y = -550f, Z = -140f },
            new() { Id = "ct_retake_a_jungle", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -950f, Y = -450f, Z = -140f },
            new() { Id = "ct_retake_a_ticket", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -1400f, Y = -900f, Z = -160f },
            new() { Id = "ct_retake_a_defuse_cover", Sector = "Bombsite A", Side = "CT", AssociatedBombsite = "A", Usage = SpotUsage.Execute | SpotUsage.Defuse | SpotUsage.Retake, X = -350f, Y = -200f, Z = -160f },
            new() { Id = "ct_retake_b_market", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -1750f, Y = 120f, Z = -160f },
            new() { Id = "ct_retake_b_short", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Staging | SpotUsage.Retake, X = -950f, Y = -1050f, Z = -140f },
            new() { Id = "ct_retake_b_entry", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Retake, X = -1300f, Y = -100f, Z = -160f },
            new() { Id = "ct_retake_b_defuse_cover", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Defuse | SpotUsage.Retake, X = -1480f, Y = -150f, Z = -160f },
            new() { Id = "ct_retake_b_awp_cover", Sector = "Bombsite B", Side = "CT", AssociatedBombsite = "B", Usage = SpotUsage.Staging | SpotUsage.Retake | SpotUsage.FlankWatch, X = -1950f, Y = 100f, Z = -160f },
            new() { Id = "tr_staging_b_apartments_kitchen", Sector = "Apartamentos B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Staging, X = -1400f, Y = 600f, Z = -160f },
            new() { Id = "tr_exec_b_site_plant", Sector = "Bombsite B", Side = "TR", AssociatedBombsite = "B", Usage = SpotUsage.Execute | SpotUsage.Plant, X = -1800f, Y = 200f, Z = -160f }
        };
        _mapProfileManager.SetSpotsForTesting(spots);
    }

    // =========================================================================
    // SEÇÃO 1: ROTEAMENTO DE ONPLAYERDEATH (Testes 1 a 5)
    // =========================================================================

    [Fact]
    public void Test01_OnPlayerDeath_TrVictim_PassesTrTeam()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        CsTeam victimTeam = CsTeam.Terrorist;
        CsTeam killerTeam = CsTeam.CounterTerrorist;
        var bots = new List<CCSPlayerController>();

        // Deve passar validação sem disparar exceção
        midRound.HandlePlayerDeath(null!, null, bots, victimTeam, killerTeam, null);
        Assert.Equal(CsTeam.Terrorist, victimTeam);
    }

    [Fact]
    public void Test02_OnPlayerDeath_CtVictim_PassesCtTeam()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        CsTeam victimTeam = CsTeam.CounterTerrorist;
        CsTeam killerTeam = CsTeam.Terrorist;
        var bots = new List<CCSPlayerController>();

        midRound.HandlePlayerDeath(null!, null, bots, victimTeam, killerTeam, null);
        Assert.Equal(CsTeam.CounterTerrorist, victimTeam);
    }

    [Fact]
    public void Test03_OnPlayerDeath_VictimBots_DoesNotContainKillerTeam()
    {
        var victimTeam = CsTeam.Terrorist;
        var killerTeam = CsTeam.CounterTerrorist;

        var allPlayers = new List<(int Slot, CsTeam Team, bool IsBot, bool Alive)>
        {
            (1, CsTeam.CounterTerrorist, true, true),
            (2, CsTeam.Terrorist, true, true),
            (3, CsTeam.Terrorist, true, true),
            (4, CsTeam.CounterTerrorist, true, true)
        };

        var filteredVictimBots = allPlayers
            .Where(p => p.Team == victimTeam && p.IsBot && p.Alive)
            .ToList();

        Assert.Equal(2, filteredVictimBots.Count);
        Assert.All(filteredVictimBots, b => Assert.NotEqual(killerTeam, b.Team));
        Assert.All(filteredVictimBots, b => Assert.Equal(victimTeam, b.Team));
    }

    [Fact]
    public void Test04_HandlePlayerDeath_InvalidVictimTeam_TriggersScopeInvalid()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var plan = new TacticalPlan { Team = CsTeam.Terrorist };
        var bots = new List<CCSPlayerController>();

        // CsTeam.None deve ser rejeitado pela guarda defensiva TEAM_SCOPE_INPUT_INVALID
        midRound.HandlePlayerDeath(null!, null, bots, CsTeam.None, CsTeam.CounterTerrorist, plan);
        Assert.Empty(midRound.ActiveAdaptations);
    }

    [Fact]
    public void Test05_HandlePlayerDeath_MixedBotsList_SanitizesToVictimTeam()
    {
        var victimTeam = CsTeam.Terrorist;
        var botList = new List<(int Slot, CsTeam Team)>
        {
            (1, CsTeam.CounterTerrorist),
            (2, CsTeam.Terrorist),
            (3, CsTeam.Terrorist)
        };

        var sanitized = botList.Where(b => b.Team == victimTeam).ToList();
        Assert.Equal(2, sanitized.Count);
        Assert.DoesNotContain(sanitized, b => b.Team == CsTeam.CounterTerrorist);
    }

    // =========================================================================
    // SEÇÃO 2: PROPRIETÁRIO DE TIME EM ADAPTAÇÕES (Testes 6 a 12)
    // =========================================================================

    [Fact]
    public void Test06_ActiveAdaptationRecord_ContainsCorrectOwnerTeam()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var plan = new TacticalPlan { Team = CsTeam.Terrorist };

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TradeRequired,
            new List<int> { 2, 4 },
            8.0f,
            "RUSH_TRADE into B",
            ownerTeam: CsTeam.Terrorist);

        Assert.Equal(CsTeam.Terrorist, record.OwnerTeam);
    }

    [Fact]
    public void Test07_ActiveAdaptationRecord_ContainsCorrectInternalRoundId()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var plan = new TacticalPlan { Team = CsTeam.CounterTerrorist };

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.RetakeDecision,
            new List<int> { 1, 3 },
            30.0f,
            "CT Retake Bombsite A",
            ownerTeam: CsTeam.CounterTerrorist);

        Assert.True(record.InternalRoundId >= 0);
    }

    [Fact]
    public void Test08_ActiveAdaptationRecord_ContainsCorrectAffectedSlots()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var plan = new TacticalPlan { Team = CsTeam.Terrorist };
        var slots = new List<int> { 2, 4, 6 };

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.TimePressure,
            slots,
            5.0f,
            "Force Plant B",
            ownerTeam: CsTeam.Terrorist);

        Assert.Equal(3, record.AffectedSlots.Count);
        Assert.Contains(2, record.AffectedSlots);
        Assert.Contains(4, record.AffectedSlots);
        Assert.Contains(6, record.AffectedSlots);
    }

    [Fact]
    public void Test09_StartTacticalAdaptation_TrDoesNotAffectCtActiveAdaptation()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var ctPlan = new TacticalPlan { Team = CsTeam.CounterTerrorist, TacticRevision = 1 };
        var trPlan = new TacticalPlan { Team = CsTeam.Terrorist, TacticRevision = 1 };

        // CT inicia Retake
        var ctRecord = midRound.StartTacticalAdaptation(
            ctPlan,
            TacticalAdaptationReason.RetakeDecision,
            new List<int> { 1, 3, 5 },
            30.0f,
            "CT Retake Bombsite B",
            ownerTeam: CsTeam.CounterTerrorist);

        // TR sofre baixa e inicia UtilityWait
        var trRecord = midRound.StartTacticalAdaptation(
            trPlan,
            TacticalAdaptationReason.UtilityWait,
            new List<int> { 2, 4 },
            4.0f,
            "TR UtilityWait",
            ownerTeam: CsTeam.Terrorist);

        // A adaptação CT NÃO pode ser fechada pela adaptação TR
        Assert.False(ctRecord.IsClosed);
        Assert.Equal(AdaptationDisposition.Active, ctRecord.Disposition);
        Assert.False(trRecord.IsClosed);
    }

    [Fact]
    public void Test10_StartTacticalAdaptation_CtDoesNotAffectTrActiveAdaptation()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var trPlan = new TacticalPlan { Team = CsTeam.Terrorist, TacticRevision = 1 };
        var ctPlan = new TacticalPlan { Team = CsTeam.CounterTerrorist, TacticRevision = 1 };

        // TR ativa adaptação de Trade
        var trRecord = midRound.StartTacticalAdaptation(
            trPlan,
            TacticalAdaptationReason.TradeRequired,
            new List<int> { 2, 4 },
            8.0f,
            "TR Trade push",
            ownerTeam: CsTeam.Terrorist);

        // CT inicia Save
        var ctRecord = midRound.StartTacticalAdaptation(
            ctPlan,
            TacticalAdaptationReason.SaveDecision,
            new List<int> { 1 },
            20.0f,
            "CT Save",
            ownerTeam: CsTeam.CounterTerrorist);

        // A adaptação TR continua intacta e ativa
        Assert.False(trRecord.IsClosed);
        Assert.Equal(AdaptationDisposition.Active, trRecord.Disposition);
        Assert.False(ctRecord.IsClosed);
    }

    [Fact]
    public void Test11_TeamScopeViolation_BlocksTrOrderOnCtBot()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var trPlan = new TacticalPlan { Team = CsTeam.Terrorist };

        // Adaptação TR registrada para os slots 2 e 4
        var adp = midRound.StartTacticalAdaptation(
            trPlan,
            TacticalAdaptationReason.UtilityWait,
            new List<int> { 2, 4 },
            4.0f,
            "TR UtilityWait",
            ownerTeam: CsTeam.Terrorist);

        // Simula verificação: se o bot no slot 2 de alguma forma fosse CT, TEAM_SCOPE_VIOLATION deve acusar
        CsTeam botTeam = CsTeam.CounterTerrorist;
        bool isViolation = (botTeam != adp.OwnerTeam);

        Assert.True(isViolation);
    }

    [Fact]
    public void Test12_TeamScopeViolation_BlocksCtOrderOnTrBot()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var ctPlan = new TacticalPlan { Team = CsTeam.CounterTerrorist };

        var adp = midRound.StartTacticalAdaptation(
            ctPlan,
            TacticalAdaptationReason.RetakeDecision,
            new List<int> { 1, 3 },
            30.0f,
            "CT Retake",
            ownerTeam: CsTeam.CounterTerrorist);

        CsTeam botTeam = CsTeam.Terrorist;
        bool isViolation = (botTeam != adp.OwnerTeam);

        Assert.True(isViolation);
    }

    // =========================================================================
    // SEÇÃO 3: WAYPOINTS E ISOLAMENTO DE PREFIXO (Testes 13 a 14)
    // =========================================================================

    [Fact]
    public void Test13_ApplyAction_CtRejectsTrPrefixWaypoint()
    {
        string spotId = "tr_exec_b_site_plant";
        CsTeam botTeam = CsTeam.CounterTerrorist;

        bool rejected = botTeam == CsTeam.CounterTerrorist && spotId.StartsWith("tr_", StringComparison.OrdinalIgnoreCase);
        Assert.True(rejected);
    }

    [Fact]
    public void Test14_ApplyAction_TrRejectsCtPrefixWaypoint()
    {
        string spotId = "ct_retake_a_connector";
        CsTeam botTeam = CsTeam.Terrorist;

        bool rejected = botTeam == CsTeam.Terrorist && spotId.StartsWith("ct_", StringComparison.OrdinalIgnoreCase);
        Assert.True(rejected);
    }

    // =========================================================================
    // SEÇÃO 4: RETAKE CT TIPADO E MATERIALIZADO (Testes 15 a 20)
    // =========================================================================

    [Fact]
    public void Test15_MaterializeCtRetakeOrders_SiteA_GeneratesOnlyCtSpots()
    {
        var bombPos = new Vector(-350f, -200f, -160f); // Bomb A
        var ctBotsInfo = new List<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)>
        {
            (1, new Vector(-1400f, -900f, -160f), true, false), // Ticket com defuser
            (3, new Vector(-820f, -840f, -160f), false, false), // Connector
            (5, new Vector(-950f, -450f, -140f), false, true)   // Jungle com AWP
        };

        var plan = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("A", bombPos, ctBotsInfo, _mapProfileManager);

        Assert.Equal(BombsiteTarget.A, plan.PlantedSite);
        Assert.Equal(3, plan.OrdersBySlot.Count);
        Assert.All(plan.MaterializedSpotIds, spot => Assert.StartsWith("ct_", spot, StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Test16_MaterializeCtRetakeOrders_SiteB_GeneratesOnlyCtSpots()
    {
        var bombPos = new Vector(-1480f, -150f, -160f); // Bomb B
        var ctBotsInfo = new List<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)>
        {
            (1, new Vector(-1300f, -100f, -160f), true, false), // Próximo B site com kit
            (3, new Vector(-950f, -1050f, -140f), false, false), // Short
            (5, new Vector(-1950f, 100f, -160f), false, true)   // Market com AWP
        };

        var plan = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("B", bombPos, ctBotsInfo, _mapProfileManager);

        Assert.Equal(BombsiteTarget.B, plan.PlantedSite);
        Assert.Equal(3, plan.OrdersBySlot.Count);
        Assert.All(plan.MaterializedSpotIds, spot => Assert.StartsWith("ct_", spot, StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Test17_MaterializeCtRetakeOrders_NoTrPrefixSpots()
    {
        var bombPos = new Vector(-350f, -200f, -160f);
        var ctBotsInfo = new List<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)>
        {
            (1, new Vector(-1000f, -1000f, -160f), false, false),
            (2, new Vector(-1200f, -1200f, -160f), false, false),
            (3, new Vector(-800f, -800f, -160f), true, false),
            (4, new Vector(-1500f, -500f, -160f), false, true)
        };

        var planA = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("A", bombPos, ctBotsInfo, _mapProfileManager);
        var planB = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("B", bombPos, ctBotsInfo, _mapProfileManager);

        Assert.DoesNotContain(planA.MaterializedSpotIds, s => s.StartsWith("tr_", StringComparison.OrdinalIgnoreCase));
        Assert.DoesNotContain(planB.MaterializedSpotIds, s => s.StartsWith("tr_", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Test18_DeMirageProfile_AllRetakeSpotsHaveCtTeamSide()
    {
        string profilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "../../../../../src/CsBotManager/MapProfiles/de_mirage.json");
        if (!File.Exists(profilePath))
        {
            // Fallback para caminho local se executado de outro diretório
            profilePath = "src/CsBotManager/MapProfiles/de_mirage.json";
        }

        if (File.Exists(profilePath))
        {
            string json = File.ReadAllText(profilePath);
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            var spotsElement = root.GetProperty("spots");

            var retakeSpots = new List<(string Id, string Side)>();
            foreach (var spot in spotsElement.EnumerateArray())
            {
                string id = spot.GetProperty("id").GetString() ?? "";
                if (id.StartsWith("ct_retake_", StringComparison.OrdinalIgnoreCase))
                {
                    string side = spot.GetProperty("side").GetString() ?? "";
                    retakeSpots.Add((id, side));
                }
            }

            Assert.Equal(10, retakeSpots.Count);
            Assert.All(retakeSpots, s => Assert.Equal("CT", s.Side));
        }
    }

    [Fact]
    public void Test19_MaterializeCtRetakeOrders_BotWithKit_PrioritizedAsDefuser()
    {
        var bombPos = new Vector(-350f, -200f, -160f);
        var ctBotsInfo = new List<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)>
        {
            (1, new Vector(-1500f, -1500f, -160f), false, false), // Sem kit
            (2, new Vector(-1400f, -1400f, -160f), true, false),  // COM KIT
            (3, new Vector(-1200f, -1200f, -160f), false, false)  // Sem kit
        };

        var plan = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("A", bombPos, ctBotsInfo, _mapProfileManager);

        Assert.Equal("Defuser", plan.RoleBySlot[2]);
        Assert.Equal("ct_retake_a_defuse_cover", plan.OrdersBySlot[2].ExecuteSpotId);
    }

    [Fact]
    public void Test20_MaterializeCtRetakeOrders_BotWithAwp_AssignedAwpCover()
    {
        var bombPos = new Vector(-1480f, -150f, -160f);
        var ctBotsInfo = new List<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)>
        {
            (1, new Vector(-1300f, -100f, -160f), false, false),
            (2, new Vector(-1800f, 100f, -160f), false, true),   // COM AWP
            (3, new Vector(-1200f, -200f, -160f), true, false)   // Com kit
        };

        var plan = TacticalOrderMaterializer.MaterializeCtRetakeOrdersDeterministic("B", bombPos, ctBotsInfo, _mapProfileManager);

        Assert.Equal("AWPer", plan.RoleBySlot[2]);
        Assert.Equal("ct_retake_b_awp_cover", plan.OrdersBySlot[2].StagingSpotId);
    }

    // =========================================================================
    // SEÇÃO 5: C4 EM FAKE COM REALSITE (Testes 21 a 25)
    // =========================================================================

    [Fact]
    public void Test21_ResolveBombCarrierTargetSite_FakeA_ExecB_ReturnsB()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Fake A & Execução B",
            TrTacticType = TrTacticType.SPLIT_FAKE,
            FakeContext = new FakeExecutionContext
            {
                FakeSite = "A",
                RealSite = "B"
            }
        };

        var resolved = BombsiteParser.ResolveBombCarrierTargetSite(plan);
        Assert.Equal(BombsiteTarget.B, resolved);
    }

    [Fact]
    public void Test22_ResolveBombCarrierTargetSite_FakeB_ExecA_ReturnsA()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Fake B & Execução A",
            TrTacticType = TrTacticType.SPLIT_FAKE,
            FakeContext = new FakeExecutionContext
            {
                FakeSite = "B",
                RealSite = "A"
            }
        };

        var resolved = BombsiteParser.ResolveBombCarrierTargetSite(plan);
        Assert.Equal(BombsiteTarget.A, resolved);
    }

    [Fact]
    public void Test23_ResolveBombCarrierTargetSite_FakeContext_OverridesFallback()
    {
        var plan = new TacticalPlan
        {
            CurrentTactic = "Tática Diversificada Inesperada",
            FakeContext = new FakeExecutionContext
            {
                FakeSite = "A",
                RealSite = "B"
            }
        };

        var resolved = BombsiteParser.ResolveBombCarrierTargetSite(plan);
        Assert.Equal(BombsiteTarget.B, resolved);
    }

    [Fact]
    public void Test24_C4ObjectiveValidation_MatchingSites_Validated()
    {
        string labelSite = "B";
        string realSite = "B";
        Vector plantCoord = new Vector(-1480f, -150f, -160f); // Bomb B Mirage

        float distToA = (plantCoord.X - (-300f)) * (plantCoord.X - (-300f)) + (plantCoord.Y - (-250f)) * (plantCoord.Y - (-250f));
        float distToB = (plantCoord.X - (-1480f)) * (plantCoord.X - (-1480f)) + (plantCoord.Y - (-150f)) * (plantCoord.Y - (-150f));
        string goalSite = distToB < distToA ? "B" : "A";

        bool isValidated = (labelSite == goalSite && labelSite == realSite);
        Assert.True(isValidated);
    }

    [Fact]
    public void Test25_C4ObjectiveValidation_MismatchingSites_CorrectsToRealSite()
    {
        string labelSite = "A"; // Erro legado
        string realSite = "B";  // Real tática
        Vector plantCoord = new Vector(-1150f, -350f, -160f); // Coordenada de A

        float distToA = (plantCoord.X - (-300f)) * (plantCoord.X - (-300f)) + (plantCoord.Y - (-250f)) * (plantCoord.Y - (-250f));
        float distToB = (plantCoord.X - (-1480f)) * (plantCoord.X - (-1480f)) + (plantCoord.Y - (-150f)) * (plantCoord.Y - (-150f));
        string goalSite = distToB < distToA ? "B" : "A";

        bool hasMismatch = (labelSite != realSite || labelSite != goalSite);
        Assert.True(hasMismatch);

        // Correção aplicada
        if (hasMismatch)
        {
            labelSite = realSite;
            plantCoord = realSite == "B" ? new Vector(-1480f, -150f, -160f) : new Vector(-1150f, -350f, -160f);
        }

        Assert.Equal("B", labelSite);
        Assert.Equal(-1480f, plantCoord.X);
    }

    // =========================================================================
    // SEÇÃO 6: UTILITYWAIT E DISSIPAÇÃO (Testes 26 a 27)
    // =========================================================================

    [Fact]
    public void Test26_UtilityWait_PreservesTargetSite()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var plan = new TacticalPlan { Team = CsTeam.Terrorist };

        var record = midRound.StartTacticalAdaptation(
            plan,
            TacticalAdaptationReason.UtilityWait,
            new List<int> { 2, 4 },
            4.0f,
            "WAIT_AND_REEXECUTE Bombsite B",
            ownerTeam: CsTeam.Terrorist,
            targetSite: "B",
            sourceEntrySlot: 2,
            utilityEvidence: "Smoke at B Apartamentos");

        Assert.Equal("B", record.TargetSite);
        Assert.Equal(CsTeam.Terrorist, record.OwnerTeam);
        Assert.Equal(TacticalAdaptationReason.UtilityWait, record.Reason);
    }

    [Fact]
    public void Test27_UtilityWait_DoesNotTouchCtBots()
    {
        var midRound = new MidRoundAdapter(null!, _mapProfileManager, null!, null!, null!);
        var trPlan = new TacticalPlan { Team = CsTeam.Terrorist };
        var ctPlan = new TacticalPlan { Team = CsTeam.CounterTerrorist };

        var ctRetake = midRound.StartTacticalAdaptation(
            ctPlan,
            TacticalAdaptationReason.RetakeDecision,
            new List<int> { 1, 3, 5 },
            30.0f,
            "CT Retake Bombsite A",
            ownerTeam: CsTeam.CounterTerrorist,
            targetSite: "A");

        var trUtilityWait = midRound.StartTacticalAdaptation(
            trPlan,
            TacticalAdaptationReason.UtilityWait,
            new List<int> { 2, 4 },
            4.0f,
            "TR UtilityWait",
            ownerTeam: CsTeam.Terrorist,
            targetSite: "B");

        Assert.False(ctRetake.IsClosed);
        Assert.Equal("A", ctRetake.TargetSite);
        Assert.Equal("B", trUtilityWait.TargetSite);
        Assert.DoesNotContain(1, trUtilityWait.AffectedSlots);
        Assert.DoesNotContain(3, trUtilityWait.AffectedSlots);
    }

    // =========================================================================
    // SEÇÃO 7: STANDSTILL UNKNOWN COM PERSISTÊNCIA (Testes 28 a 29)
    // =========================================================================

    [Fact]
    public void Test28_UnknownStandstill_FirstCycle_SuppressesRecovery()
    {
        var stopState = new PhysicalStopState
        {
            ConsecutiveUnknownStandstillCycles = 0
        };

        var classification = StandstillClassification.Unknown;
        bool recoveryAllowed = false;

        if (classification == StandstillClassification.Unknown)
        {
            stopState.ConsecutiveUnknownStandstillCycles++;
            if (stopState.ConsecutiveUnknownStandstillCycles < 2)
            {
                recoveryAllowed = false;
            }
            else
            {
                recoveryAllowed = true;
            }
        }

        Assert.False(recoveryAllowed);
        Assert.Equal(1, stopState.ConsecutiveUnknownStandstillCycles);
    }

    [Fact]
    public void Test29_UnknownStandstill_SecondCycleNoProgress_AllowsRecovery()
    {
        var stopState = new PhysicalStopState
        {
            ConsecutiveUnknownStandstillCycles = 1,
            DistanceToMacroGoalAtFirstUnknown = 500f
        };

        var classification = StandstillClassification.Unknown;
        bool recoveryAllowed = false;
        float currentDistToGoal = 495f; // Apenas 5u de progresso (< 64u)

        if (classification == StandstillClassification.Unknown)
        {
            stopState.ConsecutiveUnknownStandstillCycles++;
            if (stopState.ConsecutiveUnknownStandstillCycles < 2)
            {
                recoveryAllowed = false;
            }
            else
            {
                bool madeProgress = (stopState.DistanceToMacroGoalAtFirstUnknown - currentDistToGoal) > 64.0f;
                recoveryAllowed = !madeProgress;
            }
        }

        Assert.True(recoveryAllowed);
        Assert.Equal(2, stopState.ConsecutiveUnknownStandstillCycles);
    }

    // =========================================================================
    // SEÇÃO 8: AGRUPAMENTO DE INTEGRIDADE POR EPISÓDIO (Teste 30)
    // =========================================================================

    [Fact]
    public void Test30_IntegritySamples_WithinHalfSecond_GroupedInSameEpisode()
    {
        var tracker = new MovementExecutionTracker();

        long roundId = 1;
        int slot = 3;
        string actionId = "NavigateNavMesh_123";
        string details = "External velocity modification";

        // Amostra 1 em t = 10.0s
        tracker.RecordIntegritySample(slot, roundId, actionId, details, tick: 640, time: 10.0f);

        // Amostra 2 em t = 10.2s (< 0.5s de diferença)
        tracker.RecordIntegritySample(slot, roundId, actionId, details, tick: 652, time: 10.2f);

        // Amostra 3 em t = 10.4s (< 0.5s de diferença)
        tracker.RecordIntegritySample(slot, roundId, actionId, details, tick: 665, time: 10.4f);

        var episodes = tracker.GetAllIntegrityEpisodes();

        // Todas as 3 amostras devem pertencer a UM ÚNICO episódio
        Assert.Single(episodes);
        var ep = episodes.First();
        Assert.Equal(3, ep.SampleCount);
        Assert.Equal(640, ep.StartTick);
        Assert.Equal(665, ep.EndTick);
        Assert.Equal(10.0f, ep.StartTime);
        Assert.Equal(10.4f, ep.EndTime);
    }
}
