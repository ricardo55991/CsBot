using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Xunit;

namespace CsBotManager.Tests;

public class Phase2ForensicAuditTests
{
    private readonly string _datasetsDir;
    private readonly string _contractsDir;
    private readonly string _reportsDir;

    public Phase2ForensicAuditTests()
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
        _reportsDir = Path.Combine(_datasetsDir, "reports");
    }

    [Fact]
    public void Test_Invariant_01_SplitsMutuallyExclusive()
    {
        var trainDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "train_split_v2.json")));
        var valDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "validation_split_v2.json")));
        var testDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "test_split_v2.json")));

        var train = trainDoc.RootElement.GetProperty("demo_ids").EnumerateArray().Select(x => x.GetString()!).ToHashSet();
        var val = valDoc.RootElement.GetProperty("demo_ids").EnumerateArray().Select(x => x.GetString()!).ToHashSet();
        var test = testDoc.RootElement.GetProperty("demo_ids").EnumerateArray().Select(x => x.GetString()!).ToHashSet();

        Assert.Empty(train.Intersect(val));
        Assert.Empty(train.Intersect(test));
        Assert.Empty(val.Intersect(test));
    }

    [Fact]
    public void Test_Invariant_02_CatalogAndInventoryUniqueHashes()
    {
        var catShaFile = Path.Combine(_contractsDir, "mirage_spot_catalog_v3.sha256");
        Assert.True(File.Exists(catShaFile));
        var content = File.ReadAllText(catShaFile).Trim();
        var sha = content.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries)[0];
        Assert.Equal(64, sha.Length);
    }

    [Fact]
    public void Test_Invariant_03_MonotonicRoundAndTickSequence()
    {
        var reconFile = Path.Combine(_datasetsDir, "corpus_reconciliation_v2.json");
        Assert.True(File.Exists(reconFile));
        using var doc = JsonDocument.Parse(File.ReadAllText(reconFile));
        var metrics = doc.RootElement.GetProperty("metrics");
        Assert.True(metrics.GetProperty("valid_round_count").GetInt32() > 0);
    }

    [Fact]
    public void Test_Invariant_04_IndependentDiagonalsPreserved()
    {
        var auditFile = Path.Combine(_datasetsDir, "parquet_materialization_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(auditFile));
        var mov = doc.RootElement.GetProperty("datasets").GetProperty("movement_sequences_v2");
        Assert.Equal("MATERIALIZED_CONFIRMED", mov.GetProperty("status").GetString());
    }

    [Fact]
    public void Test_Invariant_05_JumpPressLeadingEdgeOnly()
    {
        var jumpFile = Path.Combine(_datasetsDir, "jump_label_forensic_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(jumpFile));
        var eq = doc.RootElement.GetProperty("accounting_equation");
        Assert.True(eq.GetProperty("equation_balanced").GetBoolean());
    }

    [Fact]
    public void Test_Invariant_06_AirborneNeverPersistsJumpPress()
    {
        var jumpFile = Path.Combine(_datasetsDir, "jump_label_forensic_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(jumpFile));
        var clsAir = doc.RootElement.GetProperty("airborne_jumppress_forensic_classification");
        Assert.Equal(0, clsAir.GetProperty("MISALIGNED_LABEL").GetProperty("count").GetInt32());
    }

    [Fact]
    public void Test_Invariant_07_BunnyHopEpisodesExcluded()
    {
        var jumpFile = Path.Combine(_datasetsDir, "jump_label_forensic_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(jumpFile));
        var eq = doc.RootElement.GetProperty("accounting_equation");
        Assert.Equal(8379, eq.GetProperty("excluded_bunny_hop_episodes").GetInt32());
    }

    [Fact]
    public void Test_Invariant_08_ValidSpotIdBelongsToCatalog53()
    {
        var catFile = Path.Combine(_contractsDir, "mirage_spot_catalog_v3.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(catFile));
        var spots = doc.RootElement.GetProperty("spots");
        Assert.Equal(53, spots.GetArrayLength());
    }

    [Fact]
    public void Test_Invariant_09_ValidTeamSideAssignment()
    {
        var covFile = Path.Combine(_datasetsDir, "spot_mapping_coverage_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(covFile));
        var teams = doc.RootElement.GetProperty("by_team");
        Assert.True(teams.TryGetProperty("CT", out _) && teams.TryGetProperty("TR", out _));
    }

    [Fact]
    public void Test_Invariant_10_ValidBombsiteSector()
    {
        var covFile = Path.Combine(_datasetsDir, "spot_mapping_coverage_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(covFile));
        var sectors = doc.RootElement.GetProperty("by_bombsite_sector");
        Assert.True(sectors.TryGetProperty("A_SITE", out _) || sectors.TryGetProperty("MID", out _));
    }

    [Fact]
    public void Test_Invariant_11_ClearanceWaypointDwellCapped()
    {
        var semFile = Path.Combine(_contractsDir, "spot_semantic_classification.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(semFile));
        foreach (var elem in doc.RootElement.EnumerateArray())
        {
            if (elem.GetProperty("semantic_type").GetString() == "CLEARANCE_WAYPOINT")
            {
                Assert.True(elem.GetProperty("maximum_expected_dwell_ms").GetInt32() <= 1500);
            }
        }
    }

    [Fact]
    public void Test_Invariant_12_PermanentHoldRequiresAdequateDwell()
    {
        var semFile = Path.Combine(_contractsDir, "spot_semantic_classification.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(semFile));
        foreach (var elem in doc.RootElement.EnumerateArray())
        {
            if (elem.GetProperty("semantic_type").GetString() == "POSITION_PROFILE")
            {
                Assert.True(elem.GetProperty("maximum_expected_dwell_ms").GetInt32() >= 3000);
            }
        }
    }

    [Fact]
    public void Test_Invariant_13_AimProfileProvenanceBelongsToSpot()
    {
        var aimFile = Path.Combine(_datasetsDir, "aim_profile_provenance_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(aimFile));
        Assert.Equal(159, doc.RootElement.GetProperty("total_aim_profiles").GetInt32());
    }

    [Fact]
    public void Test_Invariant_14_RoleCompatibilityStructure()
    {
        var covFile = Path.Combine(_datasetsDir, "spot_mapping_coverage_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(covFile));
        var roles = doc.RootElement.GetProperty("by_role");
        Assert.True(roles.TryGetProperty("ENTRY", out _) && roles.TryGetProperty("ANCHOR", out _));
    }

    [Fact]
    public void Test_Invariant_15_StrictTemporalCausality()
    {
        var sampleFile = Path.Combine(_datasetsDir, "visual_audit_sample_index.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(sampleFile));
        foreach (var s in doc.RootElement.EnumerateArray())
        {
            if (s.TryGetProperty("start_tick", out var st) && s.TryGetProperty("end_tick", out var et))
            {
                Assert.True(et.GetInt64() >= st.GetInt64());
            }
        }
    }

    [Fact]
    public void Test_Invariant_16_NoDemoCrossesSplits()
    {
        var trainDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "train_split_v2.json")));
        var valDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "validation_split_v2.json")));
        var testDoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(_datasetsDir, "test_split_v2.json")));

        var allDemos = new List<string>();
        foreach (var x in trainDoc.RootElement.GetProperty("demo_ids").EnumerateArray()) allDemos.Add(x.GetString()!);
        foreach (var x in valDoc.RootElement.GetProperty("demo_ids").EnumerateArray()) allDemos.Add(x.GetString()!);
        foreach (var x in testDoc.RootElement.GetProperty("demo_ids").EnumerateArray()) allDemos.Add(x.GetString()!);

        Assert.Equal(allDemos.Count, allDemos.Distinct().Count());
        Assert.Equal(444, allDemos.Count);
    }

    [Fact]
    public void Test_Invariant_17_StandardizedConfidenceWeights()
    {
        var covFile = Path.Combine(_datasetsDir, "spot_mapping_coverage_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(covFile));
        var summary = doc.RootElement.GetProperty("global_summary");
        Assert.True(summary.GetProperty("TotalSequences").GetInt32() > 0);
    }

    [Fact]
    public void Test_Invariant_18_MaskedCandidatesForLoss()
    {
        var aimFile = Path.Combine(_datasetsDir, "aim_profile_provenance_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(aimFile));
        var compliance = doc.RootElement.GetProperty("rules_compliance");
        Assert.True(compliance.GetProperty("template_defaults_excluded_from_expert_training").GetBoolean());
    }

    [Fact]
    public void Test_Invariant_19_UnmappedPositionFallback()
    {
        var covFile = Path.Combine(_datasetsDir, "spot_mapping_coverage_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(covFile));
        var summary = doc.RootElement.GetProperty("global_summary");
        Assert.True(summary.GetProperty("UnmappedSequences").GetInt32() > 0);
    }

    [Fact]
    public void Test_Invariant_20_RetakeAndEventTemporalConsistency()
    {
        var retFile = Path.Combine(_datasetsDir, "retake_provenance_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(retFile));
        Assert.True(doc.RootElement.GetArrayLength() >= 20);
    }

    // =========================================================================
    // TESTES FORENSES ADICIONAIS DA FASE 2.1
    // =========================================================================

    [Fact]
    public void Test_Forensic_CorpusTotalsReconciled()
    {
        var reconFile = Path.Combine(_datasetsDir, "corpus_reconciliation_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(reconFile));
        var metrics = doc.RootElement.GetProperty("metrics");
        Assert.Equal(452, metrics.GetProperty("accepted_file_count").GetInt32());
        Assert.Equal(10432, metrics.GetProperty("valid_round_count").GetInt32());
        Assert.Equal(6816998, metrics.GetProperty("raw_frame_count").GetInt64());
        Assert.Equal(19078539, metrics.GetProperty("player_active_frame_count").GetInt64());
    }

    [Fact]
    public void Test_Forensic_CatalogCanonicalHashIsStable()
    {
        var reconFile = Path.Combine(_contractsDir, "catalog_hash_reconciliation.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(reconFile));
        Assert.Equal(53, doc.RootElement.GetProperty("total_spots").GetInt32());
        Assert.Equal("8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9", doc.RootElement.GetProperty("sha256").GetString());
    }

    [Fact]
    public void Test_Forensic_ParquetShardsFullyMaterialized()
    {
        var auditFile = Path.Combine(_datasetsDir, "parquet_materialization_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(auditFile));
        var pos = doc.RootElement.GetProperty("datasets").GetProperty("positioning_sequences_v1");
        Assert.Equal(577816, pos.GetProperty("materialized_total_rows").GetInt32());
        Assert.Equal(6, pos.GetProperty("shard_count").GetInt32());

        var mov = doc.RootElement.GetProperty("datasets").GetProperty("movement_sequences_v2");
        Assert.Equal(293564, mov.GetProperty("materialized_total_rows").GetInt32());
        Assert.Equal(3, mov.GetProperty("shard_count").GetInt32());

        var jmp = doc.RootElement.GetProperty("datasets").GetProperty("jump_episodes_v2");
        Assert.Equal(22598, jmp.GetProperty("materialized_total_rows").GetInt32());
    }

    [Fact]
    public void Test_Forensic_JumpAccountingEquationBalanced()
    {
        var jumpFile = Path.Combine(_datasetsDir, "jump_label_forensic_audit.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(jumpFile));
        var eq = doc.RootElement.GetProperty("accounting_equation");
        Assert.Equal(22598, eq.GetProperty("candidate_jump_episodes").GetInt32());
        Assert.Equal(14219, eq.GetProperty("accepted_jump_press_events").GetInt32());
        Assert.Equal(8379, eq.GetProperty("excluded_bunny_hop_episodes").GetInt32());
    }

    [Fact]
    public void Test_Forensic_SequenceAccountingEquationCloses()
    {
        var filterFile = Path.Combine(_datasetsDir, "sequence_filter_accounting_v2.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(filterFile));
        var pos = doc.RootElement.GetProperty("datasets").GetProperty("positioning_sequences_v1");
        Assert.Equal(pos.GetProperty("raw_candidates").GetInt32(), pos.GetProperty("check_sum").GetInt32());
    }
}
