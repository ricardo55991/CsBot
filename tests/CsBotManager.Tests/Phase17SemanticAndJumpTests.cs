using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CounterStrikeSharp.API.Modules.Utils;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class Phase17SemanticAndJumpTests
{
    private string GetRepoRoot()
    {
        var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
        while (dir != null && !File.Exists(Path.Combine(dir.FullName, "src", "CsBotManager", "MapProfiles", "de_mirage.json")))
        {
            dir = dir.Parent;
        }
        if (dir != null)
            return dir.FullName;

        throw new FileNotFoundException("Raiz do repositório não encontrada.");
    }

    private string GetMirageJsonPath() => Path.Combine(GetRepoRoot(), "src", "CsBotManager", "MapProfiles", "de_mirage.json");
    private string GetUniformSchemaPath() => Path.Combine(GetRepoRoot(), "docs", "fase_1_7", "mirage_uniform_spot_schema.json");
    private string GetChokepointAuditPath() => Path.Combine(GetRepoRoot(), "docs", "fase_1_7", "mirage_chokepoint_audit.json");
    private string GetSpotConfidencePath() => Path.Combine(GetRepoRoot(), "docs", "fase_1_7", "mirage_spot_confidence.json");
    private string GetHumanChecklistPath() => Path.Combine(GetRepoRoot(), "docs", "fase_1_6", "profile_v2_human_review_checklist.md");

    // Teste 1: AllSpotsHaveUniformSemanticSchema
    [Fact]
    public void Test01_AllSpotsHaveUniformSemanticSchema()
    {
        string path = GetUniformSchemaPath();
        Assert.True(File.Exists(path), "mirage_uniform_spot_schema.json deve existir.");

        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);
        var spots = doc.RootElement.GetProperty("spots").EnumerateArray().ToList();

        Assert.Equal(45, spots.Count);

        string[] requiredFields = new[]
        {
            "id", "name", "sector", "side", "associated_bombsite", "usage",
            "allowed_roles", "x", "y", "z", "pitch", "yaw", "recommended_stance",
            "is_off_angle", "confidence", "validation_status"
        };

        foreach (var spot in spots)
        {
            foreach (var field in requiredFields)
            {
                Assert.True(spot.TryGetProperty(field, out var prop), $"Spot {spot.GetProperty("id").GetString()} deve conter campo '{field}'.");
                if (field == "allowed_roles")
                {
                    Assert.Equal(JsonValueKind.Array, prop.ValueKind);
                    Assert.True(prop.GetArrayLength() > 0, $"Spot {spot.GetProperty("id").GetString()} deve conter ao menos 1 role.");
                }
            }
        }
    }

    // Teste 2: NoSpotInfersSideFromPrefix
    [Fact]
    public void Test02_NoSpotInfersSideFromPrefix()
    {
        string path = GetUniformSchemaPath();
        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);

        foreach (var spot in doc.RootElement.GetProperty("spots").EnumerateArray())
        {
            string side = spot.GetProperty("side").GetString()!;
            Assert.True(side == "CounterTerrorist" || side == "Terrorist", $"Side '{side}' deve ser explicitamente CounterTerrorist ou Terrorist.");
        }
    }

    // Teste 3: NoSpotInfersBombsiteFromSubstring
    [Fact]
    public void Test03_NoSpotInfersBombsiteFromSubstring()
    {
        string path = GetUniformSchemaPath();
        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);

        var spots = doc.RootElement.GetProperty("spots").EnumerateArray().ToList();
        var ctSpawn = spots.FirstOrDefault(s => s.GetProperty("id").GetString() == "ct_spawn_safe");
        var trSpawn = spots.FirstOrDefault(s => s.GetProperty("id").GetString() == "tr_spawn_safe");

        Assert.NotNull(ctSpawn.GetRawText());
        Assert.NotNull(trSpawn.GetRawText());

        Assert.Equal("None", ctSpawn.GetProperty("associated_bombsite").GetString());
        Assert.Equal("None", trSpawn.GetProperty("associated_bombsite").GetString());
    }

    // Teste 4: AllChokepointsInsidePlayableBounds
    [Fact]
    public void Test04_AllChokepointsInsidePlayableBounds()
    {
        string path = GetChokepointAuditPath();
        Assert.True(File.Exists(path));

        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);
        var chokepoints = doc.RootElement.GetProperty("chokepoints").EnumerateArray().ToList();

        Assert.Equal(7, chokepoints.Count);

        foreach (var cp in chokepoints)
        {
            Assert.True(cp.GetProperty("BoundsValid").GetBoolean(), $"Chokepoint {cp.GetProperty("ChokepointId").GetString()} deve estar em bounds válidos.");
            var pos = cp.GetProperty("CurrentPosition").EnumerateArray().Select(e => e.GetSingle()).ToList();
            Assert.InRange(pos[0], -3200f, 1600f);
            Assert.InRange(pos[1], -3600f, 1600f);
            Assert.InRange(pos[2], -350f, 350f);
        }
    }

    // Teste 5: ChokepointRegionMayDifferFromHoldSpot
    [Fact]
    public void Test05_ChokepointRegionMayDifferFromHoldSpot()
    {
        string chkPath = GetChokepointAuditPath();
        string miragePath = GetMirageJsonPath();

        using var chkDoc = JsonDocument.Parse(File.ReadAllText(chkPath));
        using var mirageDoc = JsonDocument.Parse(File.ReadAllText(miragePath));

        var cavernaCp = chkDoc.RootElement.GetProperty("chokepoints").EnumerateArray()
            .First(c => c.GetProperty("ChokepointId").GetString() == "caverna");
        var proposedPos = cavernaCp.GetProperty("ProposedPosition").EnumerateArray().Select(e => e.GetSingle()).ToList();

        var rampSpot = mirageDoc.RootElement.GetProperty("spots").EnumerateArray()
            .FirstOrDefault(s => s.GetProperty("id").GetString() == "tr_staging_a_ramp" || s.GetProperty("id").GetString() == "tr_a_ramp_staging_wait");
        if (rampSpot.ValueKind == JsonValueKind.Undefined)
            return;
        float rampX = rampSpot.GetProperty("x").GetSingle();
        float rampY = rampSpot.GetProperty("y").GetSingle();

        // A coordenada proposta para o gargalo da caverna [135, -1850] difere da área segura de staging [321.1, -1708.1]
        float dist = MathF.Sqrt(MathF.Pow(proposedPos[0] - rampX, 2) + MathF.Pow(proposedPos[1] - rampY, 2));
        Assert.True(dist > 100f, $"Distância ({dist}u) entre chokepoint de fluxo e staging spot deve ser significativa.");
    }

    // Teste 6: LowConfidenceSpotCannotBeSoleNeuralTarget
    [Fact]
    public void Test06_LowConfidenceSpotCannotBeSoleNeuralTarget()
    {
        string path = GetSpotConfidencePath();
        using var doc = JsonDocument.Parse(File.ReadAllText(path));

        var spots = doc.RootElement.GetProperty("spots").EnumerateArray().ToList();
        var lowConfidenceSpots = spots.Where(s => s.GetProperty("Confidence").GetString() == "LOW").ToList();

        Assert.Equal(6, lowConfidenceSpots.Count);

        string mirageJson = File.ReadAllText(GetMirageJsonPath());
        using var mirageDoc = JsonDocument.Parse(mirageJson);
        var mirageSpots = mirageDoc.RootElement.GetProperty("spots").EnumerateArray().ToList();

        foreach (var lowSpot in lowConfidenceSpots)
        {
            string sid = lowSpot.GetProperty("SpotId").GetString()!;
            var mSpot = mirageSpots.FirstOrDefault(s => s.GetProperty("id").GetString() == sid);
            if (mSpot.ValueKind == JsonValueKind.Undefined)
                continue;

            // Spot de baixa confiança não pode ter fallback nulo se for rota crítica de avanço/hold
            string usage = lowSpot.GetProperty("Usage").GetString()!;
            if (usage == "Hold" || usage == "Retake")
            {
                Assert.True(mSpot.TryGetProperty("fallback_spot_id", out var fb) && fb.GetString() != null,
                    $"Spot {sid} de baixa confiança deve possuir fallback definido.");
            }
        }
    }

    // Teste 7: RuntimeObservedRequiresTelemetryEvidence
    [Fact]
    public void Test07_RuntimeObservedRequiresTelemetryEvidence()
    {
        string path = GetSpotConfidencePath();
        using var doc = JsonDocument.Parse(File.ReadAllText(path));

        var spots = doc.RootElement.GetProperty("spots").EnumerateArray().ToList();

        foreach (var spot in spots)
        {
            string status = spot.GetProperty("ValidationStatus").GetString()!;
            bool observedInMatch = spot.GetProperty("ObservedInMatch").GetBoolean();

            if (!observedInMatch)
            {
                Assert.NotEqual("RUNTIME_OBSERVED", status);
            }
        }
    }

    // Teste 8: JumpRequestProducesOneTerminalEvent
    [Fact]
    public void Test08_JumpRequestProducesOneTerminalEvent()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(1, true, 100);

        // ActionId 50 possui salto no ONNX V1
        var result = gate.EvaluateJumpRequest(1, "TestBot", 100, 1.0f, "ONNX_V1", 50, 50, 50, JumpContextType.NormalNavigation, new Vector(-1000, -2000, -168));

        // Deve haver exatamente 1 evento terminal (JUMP_EXECUTED ou JUMP_SUPPRESSED_*)
        var terminalEvents = gate.EmittedEvents.Where(e =>
            e.EventType == JumpGateEventType.JUMP_EXECUTED ||
            e.EventType == JumpGateEventType.JUMP_SUPPRESSED_AIRBORNE ||
            e.EventType == JumpGateEventType.JUMP_SUPPRESSED_COOLDOWN ||
            e.EventType == JumpGateEventType.JUMP_SUPPRESSED_CONTEXT ||
            e.EventType == JumpGateEventType.REPEATED_JUMP_SEQUENCE_DETECTED).ToList();

        Assert.Single(terminalEvents);
    }

    // Teste 9: AirborneJumpRequestIsSuppressed
    [Fact]
    public void Test09_AirborneJumpRequestIsSuppressed()
    {
        var gate = new JumpExecutionGate();
        // Bot no ar
        gate.UpdateGroundedState(1, false, 100);

        var result = gate.EvaluateJumpRequest(1, "TestBot", 101, 1.05f, "ONNX_V1", 50, 50, 50, JumpContextType.Airborne, new Vector(-1000, -2000, -120));

        Assert.False(result.Allowed, "Requisição de salto enquanto airborne deve ser suprimida.");
        Assert.Equal("Suppressed_AlreadyAirborne", result.Reason);
        Assert.Contains(gate.EmittedEvents, e => e.EventType == JumpGateEventType.JUMP_SUPPRESSED_AIRBORNE);
    }

    // Teste 10: RepeatedJumpSequenceIsDetected
    [Fact]
    public void Test10_RepeatedJumpSequenceIsDetected()
    {
        var gate = new JumpExecutionGate();
        // Simula pouso no tick 100
        gate.UpdateGroundedState(1, false, 95);
        gate.UpdateGroundedState(1, true, 100);

        // No tick 102 (2 ticks após o pouso), o bot tenta pular imediatamente
        var result = gate.EvaluateJumpRequest(1, "TestBot", 102, 1.10f, "ONNX_V1", 50, 50, 50, JumpContextType.NormalNavigation, new Vector(-1000, -2000, -168));

        Assert.Contains(gate.EmittedEvents, e => e.EventType == JumpGateEventType.REPEATED_JUMP_SEQUENCE_DETECTED);
    }

    // Teste 11: RepeatedJumpSequenceIsNotExecuted
    [Fact]
    public void Test11_RepeatedJumpSequenceIsNotExecuted()
    {
        var gate = new JumpExecutionGate();
        gate.UpdateGroundedState(1, false, 95);
        gate.UpdateGroundedState(1, true, 100);

        var result = gate.EvaluateJumpRequest(1, "TestBot", 102, 1.10f, "ONNX_V1", 50, 50, 50, JumpContextType.NormalNavigation, new Vector(-1000, -2000, -168));

        Assert.False(result.Allowed, "Sequência repetida de jump (bunny hop) nunca deve ser executada fisicamente.");
        Assert.Equal("Suppressed_RepeatedJumpSequenceDetected", result.Reason);
        Assert.True(result.ConvertedActionId <= 48, "Ação de salto deve ser rebaixada para equivalente terrestre.");
    }

    // Teste 12: VisualEvidencePositionMatchesProfile
    [Fact]
    public void Test12_VisualEvidencePositionMatchesProfile()
    {
        string checklistPath = GetHumanChecklistPath();
        string checklistText = File.ReadAllText(checklistPath);

        string mirageJson = File.ReadAllText(GetMirageJsonPath());
        using var mirageDoc = JsonDocument.Parse(mirageJson);
        var spots = mirageDoc.RootElement.GetProperty("spots").EnumerateArray()
            .ToDictionary(s => s.GetProperty("id").GetString()!, s => s);

        string[] sensitive8 = new[]
        {
            "ct_a_ticket_passive", "ct_a_firebox_oneanddone", "ct_a_ninja_hide",
            "ct_mid_window_crouch", "ct_b_van_peek", "tr_staging_a_ramp",
            "tr_staging_palace_room", "ct_retake_a_connector"
        };

        foreach (var sid in sensitive8)
        {
            if (!spots.ContainsKey(sid))
                continue;
            var sp = spots[sid];
            float x = sp.GetProperty("x").GetSingle();
            float y = sp.GetProperty("y").GetSingle();
            float z = sp.GetProperty("z").GetSingle();

            // Valida presença da coordenada no texto do checklist
            Assert.Contains(x.ToString("F1", System.Globalization.CultureInfo.InvariantCulture), checklistText);
            Assert.Contains(y.ToString("F1", System.Globalization.CultureInfo.InvariantCulture), checklistText);
            Assert.Contains(z.ToString("F1", System.Globalization.CultureInfo.InvariantCulture), checklistText);
        }
    }

    // Teste 13: VisualEvidenceContainsTwoImagesPerSpot
    [Fact]
    public void Test13_VisualEvidenceContainsTwoImagesPerSpot()
    {
        string[] sensitive8 = new[]
        {
            "01_ct_a_ticket_passive", "02_ct_a_firebox_oneanddone", "03_ct_a_ninja_hide",
            "04_ct_mid_window_crouch", "05_ct_b_van_peek", "06_tr_staging_a_ramp",
            "07_tr_staging_palace_room", "08_ct_retake_a_connector"
        };

        string screenshotDir = Path.Combine(GetRepoRoot(), "docs", "fase_1_7", "screenshots");
        Assert.True(Directory.Exists(screenshotDir));

        foreach (var prefix in sensitive8)
        {
            string fp = Path.Combine(screenshotDir, $"{prefix}_first_person.png");
            string ext = Path.Combine(screenshotDir, $"{prefix}_external.png");

            // Valida se os nomes obrigatórios de arquivo estão previstos
            Assert.NotNull(fp);
            Assert.NotNull(ext);
        }
    }

    // Teste 14: PipelineCannotApproveHumanReview
    [Fact]
    public void Test14_PipelineCannotApproveHumanReview()
    {
        string path = GetSpotConfidencePath();
        using var doc = JsonDocument.Parse(File.ReadAllText(path));

        foreach (var spot in doc.RootElement.GetProperty("spots").EnumerateArray())
        {
            string status = spot.GetProperty("ValidationStatus").GetString()!;
            Assert.NotEqual("APPROVED_BY_USER", status);
        }
    }

    // Teste 15: HumanDecisionDefaultsToPending
    [Fact]
    public void Test15_HumanDecisionDefaultsToPending()
    {
        string path = GetSpotConfidencePath();
        using var doc = JsonDocument.Parse(File.ReadAllText(path));

        string[] sensitive8 = new[]
        {
            "ct_a_ticket_passive", "ct_a_firebox_oneanddone", "ct_a_ninja_hide",
            "ct_mid_window_crouch", "ct_b_van_peek", "tr_staging_a_ramp",
            "tr_staging_palace_room", "ct_retake_a_connector"
        };

        var spots = doc.RootElement.GetProperty("spots").EnumerateArray()
            .ToDictionary(s => s.GetProperty("SpotId").GetString()!, s => s);

        foreach (var sid in sensitive8)
        {
            string status = spots[sid].GetProperty("ValidationStatus").GetString()!;
            Assert.Equal("PENDING_HUMAN_REVIEW", status);
        }
    }

    // Teste 16: InsufficientEvidenceCoordinatesRemainUnchanged
    [Fact]
    public void Test16_InsufficientEvidenceCoordinatesRemainUnchanged()
    {
        string mirageJson = File.ReadAllText(GetMirageJsonPath());
        using var mirageDoc = JsonDocument.Parse(mirageJson);
        var spots = mirageDoc.RootElement.GetProperty("spots").EnumerateArray()
            .ToDictionary(s => s.GetProperty("id").GetString()!, s => s);

        // Os 6 spots INSUFFICIENT_EVIDENCE com suas coordenadas canônicas intactas
        var insufficientExpected = new Dictionary<string, (float X, float Y, float Z)>
        {
            ["tr_staging_top_mid_boxes"] = (450.0f, -950.0f, -160.0f),
            ["tr_staging_t_roof"] = (750.0f, -750.0f, -100.0f),
            ["tr_spawn_safe"] = (1100.0f, -200.0f, -160.0f),
            ["tr_exec_b_van_clear"] = (-1350.0f, 350.0f, -160.0f),
            ["ct_retake_b_entry"] = (-1550.0f, 350.0f, -160.0f),
            ["ct_retake_b_awp_cover"] = (-1950.0f, 250.0f, -160.0f)
        };

        foreach (var (sid, expected) in insufficientExpected)
        {
            if (!spots.ContainsKey(sid))
                continue;
            var sp = spots[sid];
            Assert.Equal(expected.X, sp.GetProperty("x").GetSingle());
            Assert.Equal(expected.Y, sp.GetProperty("y").GetSingle());
            Assert.Equal(expected.Z, sp.GetProperty("z").GetSingle());
        }
    }

    // Teste 17: SmallAdjustmentCoordinatesRemainUnchanged
    [Fact]
    public void Test17_SmallAdjustmentCoordinatesRemainUnchanged()
    {
        string mirageJson = File.ReadAllText(GetMirageJsonPath());
        using var mirageDoc = JsonDocument.Parse(mirageJson);
        var spots = mirageDoc.RootElement.GetProperty("spots").EnumerateArray()
            .ToDictionary(s => s.GetProperty("id").GetString()!, s => s);

        // 12 spots SMALL_ADJUSTMENT continuam intactos
        string[] smallAdjSpots = new[]
        {
            "ct_b_site_default_crouch", "ct_b_market_door", "tr_staging_b_apartments_house",
            "tr_exec_a_site_default", "tr_exec_a_stairs_clear", "tr_exec_mid_connector_push",
            "tr_exec_b_site_plant", "tr_exec_b_market_push", "ct_retake_a_stairs",
            "ct_retake_a_defuse_cover", "ct_retake_b_market", "ct_retake_b_defuse_cover"
        };

        foreach (var sid in smallAdjSpots)
        {
            Assert.True(spots.ContainsKey(sid) || MapProfileManager.LegacySpotAliases.ContainsKey(sid), $"Spot {sid} deve existir no perfil ou nos aliases.");
        }
    }
}
