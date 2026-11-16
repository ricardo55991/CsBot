using System;
using System.IO;
using System.Text.Json;
using Xunit;

namespace CsBotManager.Tests;

public class Phase2TrainingInputsTests
{
    private readonly string _datasetsDir;
    private readonly string _contractsDir;

    public Phase2TrainingInputsTests()
    {
        string current = AppDomain.CurrentDomain.BaseDirectory;
        while (!string.IsNullOrEmpty(current) && !File.Exists(Path.Combine(current, "start_cs2_ai_server.bat")))
        {
            string? parent = Directory.GetParent(current)?.FullName;
            if (parent == current) break;
            current = parent ?? "";
        }

        _datasetsDir = Path.Combine(current, "datasets", "mirage_v2");
        _contractsDir = Path.Combine(_datasetsDir, "contracts");
    }

    [Fact]
    public void Test_01_ParquetSchemaMatchesDeclaredContract()
    {
        var auditFile = Path.Combine(_datasetsDir, "parquet_physical_schema_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(auditFile));
        var datasets = doc.RootElement.GetProperty("datasets");
        Assert.True(datasets.TryGetProperty("positioning_sequences_v1", out _));
        Assert.True(datasets.TryGetProperty("movement_sequences_v2", out _));
        Assert.True(datasets.TryGetProperty("jump_episodes_v2", out _));
    }

    [Fact]
    public void Test_02_TemporalWindowIsMaterialized()
    {
        var auditFile = Path.Combine(_datasetsDir, "parquet_physical_schema_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(auditFile));
        var meta = doc.RootElement.GetProperty("datasets").GetProperty("positioning_sequences_v1").GetProperty("sequence_metadata");
        Assert.Equal(32, meta.GetProperty("sequence_length").GetInt32());
        Assert.Equal(18, meta.GetProperty("feature_dimension").GetInt32());
    }

    [Fact]
    public void Test_03_DataloaderBuildsExpectedBatchShapes()
    {
        var reportFile = Path.Combine(_datasetsDir, "dataloader_validation_report.md");
        var text = File.ReadAllText(reportFile);
        Assert.Contains("[64, 32, 18]", text);
        Assert.Contains("[64, 53]", text);
        Assert.Contains("[64, 16, 18]", text);
    }

    [Fact]
    public void Test_04_TicksAreStrictlyMonotonic()
    {
        var sampleFile = Path.Combine(_datasetsDir, "temporal_window_forensic_sample.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(sampleFile));
        var pos = doc.RootElement.GetProperty("datasets").GetProperty("positioning_sequences_v1");
        foreach (var elem in pos.EnumerateArray())
        {
            Assert.True(elem.GetProperty("monotonic_ticks").GetBoolean());
        }
    }

    [Fact]
    public void Test_05_SequenceDoesNotCrossRoundBoundary()
    {
        var sampleFile = Path.Combine(_datasetsDir, "temporal_window_forensic_sample.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(sampleFile));
        var pos = doc.RootElement.GetProperty("datasets").GetProperty("positioning_sequences_v1");
        foreach (var elem in pos.EnumerateArray())
        {
            Assert.True(elem.GetProperty("no_round_boundary_cross").GetBoolean());
        }
    }

    [Fact]
    public void Test_06_CandidateMaskHasValidSpotWhenEligible()
    {
        var contractFile = Path.Combine(_contractsDir, "positioning_multitask_contract_v1.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(contractFile));
        var rules = doc.RootElement.GetProperty("neural_safety_rules");
        Assert.True(rules.GetProperty("candidate_mask_enforces_sector_validity").GetBoolean());
    }

    [Fact]
    public void Test_07_TransitMasksSpotLoss()
    {
        var contractFile = Path.Combine(_contractsDir, "positioning_multitask_contract_v1.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(contractFile));
        var headC = doc.RootElement.GetProperty("heads").GetProperty("Head_C_CandidateSpotRanking");
        Assert.Contains("MASCARADA", headC.GetProperty("masking_rule").GetString());
    }

    [Fact]
    public void Test_08_UnmappedIsNeverPositiveSpotClass()
    {
        var contractFile = Path.Combine(_contractsDir, "positioning_multitask_contract_v1.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(contractFile));
        var rules = doc.RootElement.GetProperty("neural_safety_rules");
        Assert.True(rules.GetProperty("unmapped_is_never_spot_class").GetBoolean());
    }

    [Fact]
    public void Test_09_PositioningStateExistsForEverySequence()
    {
        var distFile = Path.Combine(_datasetsDir, "positioning_head_distribution_v1.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(distFile));
        var crit = doc.RootElement.GetProperty("audit_criteria_verification");
        Assert.True(crit.GetProperty("all_sequences_have_valid_positioning_state").GetBoolean());
    }

    [Fact]
    public void Test_10_NextSectorExistsOrIsMasked()
    {
        var distFile = Path.Combine(_datasetsDir, "positioning_head_distribution_v1.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(distFile));
        var crit = doc.RootElement.GetProperty("audit_criteria_verification");
        Assert.True(crit.GetProperty("all_sequences_have_valid_next_sector").GetBoolean());
    }

    [Fact]
    public void Test_11_AimHumanCaptureRequiresCaptureEvent()
    {
        var provFile = Path.Combine(_datasetsDir, "aim_profile_provenance_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(provFile));
        var counts = doc.RootElement.GetProperty("counts_by_provenance");
        Assert.Equal(0, counts.GetProperty("HUMAN_CAPTURE_IN_GAME").GetInt32());
    }

    [Fact]
    public void Test_12_VisualApprovalIsNotHumanCapture()
    {
        var provFile = Path.Combine(_datasetsDir, "aim_profile_provenance_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(provFile));
        var counts = doc.RootElement.GetProperty("counts_by_provenance");
        Assert.Equal(53, counts.GetProperty("HUMAN_VISUAL_APPROVAL").GetInt32());
    }

    [Fact]
    public void Test_13_TemplateAimIsNotExpertEligible()
    {
        var eligFile = Path.Combine(_datasetsDir, "aim_profile_training_eligibility_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(eligFile));
        foreach (var elem in doc.RootElement.GetProperty("profiles").EnumerateArray())
        {
            if (elem.GetProperty("provenance_category").GetString() == "TEMPLATE_DEFAULT")
            {
                Assert.False(elem.GetProperty("is_expert_training_label").GetBoolean());
                Assert.Equal(0.0, elem.GetProperty("confidence_weight").GetDouble());
            }
        }
    }

    [Fact]
    public void Test_14_TrainBatchContainsOnlyTrainMatches()
    {
        var trainDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "train_split_v2.json")));
        var trainIds = trainDoc.RootElement.GetProperty("demo_ids").EnumerateArray();
        Assert.NotEmpty(trainIds);
    }

    [Fact]
    public void Test_15_ValidationBatchContainsOnlyValidationMatches()
    {
        var valDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "validation_split_v2.json")));
        var valIds = valDoc.RootElement.GetProperty("demo_ids").EnumerateArray();
        Assert.NotEmpty(valIds);
    }

    [Fact]
    public void Test_16_TestBatchContainsOnlyTestMatches()
    {
        var testDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "test_split_v2.json")));
        var testIds = testDoc.RootElement.GetProperty("demo_ids").EnumerateArray();
        Assert.NotEmpty(testIds);
    }

    [Fact]
    public void Test_17_NoFutureFeatureLeakageInWindows()
    {
        var sampleFile = Path.Combine(_datasetsDir, "temporal_window_forensic_sample.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(sampleFile));
        var pos = doc.RootElement.GetProperty("datasets").GetProperty("positioning_sequences_v1");
        foreach (var elem in pos.EnumerateArray())
        {
            Assert.True(elem.GetProperty("no_future_feature_leakage").GetBoolean());
        }
    }

    [Fact]
    public void Test_18_JumpPressRemainsRareAndEdgeBased()
    {
        var baselineFile = Path.Combine(_datasetsDir, "baseline_jump_metrics.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(baselineFile));
        var alwaysNo = doc.RootElement.GetProperty("baselines").GetProperty("AlwaysNoJump");
        Assert.True(alwaysNo.GetProperty("overall_accuracy").GetDouble() > 0.99);
    }

    [Fact]
    public void Test_19_AirborneReissueIsNeverAccepted()
    {
        var baselineFile = Path.Combine(_datasetsDir, "baseline_jump_metrics.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(baselineFile));
        var ruleJump = doc.RootElement.GetProperty("baselines").GetProperty("RuleBasedGroundedEdge");
        Assert.Equal(0.0, ruleJump.GetProperty("airborne_reissue_rate").GetDouble());
    }

    [Fact]
    public void Test_20_BaselineMetricsAreReproducible()
    {
        var baselineFile = Path.Combine(_datasetsDir, "baseline_positioning_metrics.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(baselineFile));
        var mf = doc.RootElement.GetProperty("baselines").GetProperty("MostFrequentState").GetProperty("metrics");
        Assert.True(mf.GetProperty("accuracy").GetDouble() > 0.90);
    }
}
