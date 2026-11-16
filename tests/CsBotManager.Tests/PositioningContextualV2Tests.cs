using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Microsoft.ML.OnnxRuntime;
using Xunit;

namespace CsBotManager.Tests;

public sealed class PositioningContextualV2Tests
{
    private static readonly string RepoRoot = FindRepoRoot();
    private static readonly string OutDir = Path.Combine(RepoRoot, "training_runs", "positioning_v2_real_temporal", "onnx_contextual_v2");
    private static readonly string OnnxV2Path = Path.Combine(OutDir, "positioning_transformer_hybrid_v2.onnx");
    private static readonly string OnnxV1Path = Path.Combine(RepoRoot, "training_runs", "positioning_v2_real_temporal", "onnx_export", "positioning_transformer_hybrid_v1.onnx");

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "AGENTS.md"))) return dir.FullName;
            dir = dir.Parent;
        }
        return Directory.GetCurrentDirectory();
    }

    [Fact]
    public void PyTorchUsesContextualInputs()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "contextual_ablation_metrics.json")));
        double ptReal = doc.RootElement.GetProperty("A_pytorch_real_context").GetProperty("spot_mrr").GetDouble();
        double ptZero = doc.RootElement.GetProperty("B_pytorch_zero_context").GetProperty("spot_mrr").GetDouble();
        Assert.True(ptReal - ptZero > 0.05, $"Expected real context MRR ({ptReal}) >> zero context MRR ({ptZero})");
    }

    [Fact]
    public void OnnxV1OmissionIsReproduced()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "contextual_ablation_metrics.json")));
        Assert.True(doc.RootElement.GetProperty("omission_confirmed").GetBoolean());
        Assert.Equal("ONNX_CONTEXTUAL_INPUT_OMISSION_CONFIRMED", doc.RootElement.GetProperty("status").GetString());
        Assert.Equal(1.0, doc.RootElement.GetProperty("B_vs_C_spot_decision_agreement").GetDouble());
    }

    [Fact]
    public void OnnxV2ContainsTeamInput()
    {
        using var sess = new InferenceSession(OnnxV2Path);
        Assert.True(sess.InputMetadata.ContainsKey("team_idx"));
        Assert.Equal(typeof(long), sess.InputMetadata["team_idx"].ElementType);
    }

    [Fact]
    public void OnnxV2ContainsRoleInput()
    {
        using var sess = new InferenceSession(OnnxV2Path);
        Assert.True(sess.InputMetadata.ContainsKey("role_idx"));
        Assert.Equal(typeof(long), sess.InputMetadata["role_idx"].ElementType);
    }

    [Fact]
    public void OnnxV2ContainsStageInput()
    {
        using var sess = new InferenceSession(OnnxV2Path);
        Assert.True(sess.InputMetadata.ContainsKey("stage_idx"));
        Assert.Equal(typeof(long), sess.InputMetadata["stage_idx"].ElementType);
    }

    [Fact]
    public void CSharpTeamMappingMatchesPython()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "positioning_runtime_contract_v2.json")));
        var pyMap = doc.RootElement.GetProperty("inputs").GetProperty("team_idx").GetProperty("mapping");
        Assert.Equal(pyMap.GetProperty("CT").GetInt64(), PositioningTransformerContract.MapTeamNameToIndex("CT", out bool fb0));
        Assert.False(fb0);
        Assert.Equal(pyMap.GetProperty("TR").GetInt64(), PositioningTransformerContract.MapTeamNameToIndex("TR", out bool fb1));
        Assert.False(fb1);
        Assert.Equal(pyMap.GetProperty("ANY").GetInt64(), PositioningTransformerContract.MapTeamNameToIndex("ANY", out bool fb2));
        Assert.False(fb2);
        Assert.Equal(2L, PositioningTransformerContract.MapTeamNameToIndex("UNKNOWN", out bool fb3));
        Assert.True(fb3);
    }

    [Fact]
    public void CSharpRoleMappingMatchesPython()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "positioning_runtime_contract_v2.json")));
        var pyMap = doc.RootElement.GetProperty("inputs").GetProperty("role_idx").GetProperty("mapping");
        foreach (var prop in pyMap.EnumerateObject())
        {
            long csVal = PositioningTransformerContract.MapRoleToIndex(prop.Name, out bool fb);
            Assert.False(fb);
            Assert.Equal(prop.Value.GetInt64(), csVal);
        }
        Assert.Equal(0L, PositioningTransformerContract.MapRoleToIndex("MISSING_ROLE", out bool fbMissing));
        Assert.True(fbMissing);
    }

    [Fact]
    public void CSharpStageMappingMatchesPython()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "positioning_runtime_contract_v2.json")));
        var pyMap = doc.RootElement.GetProperty("inputs").GetProperty("stage_idx").GetProperty("mapping");
        foreach (var prop in pyMap.EnumerateObject())
        {
            long csVal = PositioningTransformerContract.MapStageToIndex(prop.Name, out bool fb);
            Assert.False(fb);
            Assert.Equal(prop.Value.GetInt64(), csVal);
        }
        Assert.Equal(0L, PositioningTransformerContract.MapStageToIndex("MISSING_STAGE", out bool fbMissing));
        Assert.True(fbMissing);
    }

    [Fact]
    public void StageUsesNoFutureInformation()
    {
        // Apenas estado atual/passado: bomba não plantada -> nunca retorna PostPlant nem Retake
        string ctPre = PositioningTransformerContract.DeriveCausalStageName(false, false, false, false, false);
        string trPre = PositioningTransformerContract.DeriveCausalStageName(false, true, false, false, true);
        Assert.Equal("MapControl", ctPre);
        Assert.Equal("Staging", trPre);
        // Bomba plantada -> PostPlant (TR) / Retake (CT)
        Assert.Equal("PostPlant", PositioningTransformerContract.DeriveCausalStageName(true, true, false, false, false));
        Assert.Equal("Retake", PositioningTransformerContract.DeriveCausalStageName(true, false, false, false, false));
    }

    [Fact]
    public void ContextualInputParityIsExact()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "numerical_parity.json")));
        Assert.True(doc.RootElement.GetProperty("all_pass").GetBoolean());
    }

    [Fact]
    public void DecisionParityIsExact()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "decision_parity.json")));
        Assert.True(doc.RootElement.GetProperty("all_pass").GetBoolean());
    }

    [Fact]
    public void MetricParityIsExact()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "metric_parity.json")));
        Assert.True(doc.RootElement.GetProperty("all_pass").GetBoolean());
    }

    [Fact]
    public void SideMaskV2WrongSideIsZero()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "side_mask_v2_metrics.json")));
        Assert.True(doc.RootElement.GetProperty("all_gates_pass").GetBoolean());
        Assert.Equal(0, doc.RootElement.GetProperty("validation").GetProperty("onnx_v2_with_side_mask_v2").GetProperty("wrong_side_selection").GetInt32());
        Assert.Equal(0, doc.RootElement.GetProperty("test").GetProperty("onnx_v2_with_side_mask_v2").GetProperty("wrong_side_selection").GetInt32());
    }

    [Fact]
    public void UnsupportedSpotCannotWin()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "side_mask_v2_metrics.json")));
        Assert.Equal(0, doc.RootElement.GetProperty("validation").GetProperty("onnx_v2_with_side_mask_v2").GetProperty("unsupported_selection").GetInt32());
        Assert.Equal(0, doc.RootElement.GetProperty("test").GetProperty("onnx_v2_with_side_mask_v2").GetProperty("unsupported_selection").GetInt32());
    }

    [Fact]
    public void OnnxV1RemainsUnchanged()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "input_snapshot.json")));
        string expected = doc.RootElement.GetProperty("hashes").GetProperty("training_runs/positioning_v2_real_temporal/onnx_export/positioning_transformer_hybrid_v1.onnx").GetString()!;
        Assert.Equal(expected, PositioningTransformerService.ComputeFileSha256(OnnxV1Path));
    }

    [Fact]
    public void CheckpointsRemainUnchanged()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(OutDir, "input_snapshot.json")));
        var hashes = doc.RootElement.GetProperty("hashes");
        string p34 = "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1/selected_checkpoint.pt";
        string p36 = "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/hierarchical_state_patch_v1/selected_checkpoint.pt";
        Assert.Equal(hashes.GetProperty(p34).GetString(), PositioningTransformerService.ComputeFileSha256(Path.Combine(RepoRoot, p34)));
        Assert.Equal(hashes.GetProperty(p36).GetString(), PositioningTransformerService.ComputeFileSha256(Path.Combine(RepoRoot, p36)));
    }

    [Fact]
    public void WarmupCoversBatchOneThroughFive()
    {
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(OnnxV2Path));
        Assert.True(svc.IsReady);
        Assert.True(svc.WarmupSuccess);
        Assert.True(svc.SupportsContextualInputs);
        Assert.Equal(5, svc.WarmupBatchMetrics.Count);
        for (int i = 0; i < 5; i++)
        {
            Assert.Equal(i + 1, svc.WarmupBatchMetrics[i].BatchSize);
            Assert.True(svc.WarmupBatchMetrics[i].Success);
            Assert.True(svc.WarmupBatchMetrics[i].OutputBoundsValid);
        }

        // Verificar também que C# envia team_idx, role_idx e stage_idx reais no PredictShadowBatch
        var input = new PositioningShadowInferenceInput
        {
            BatchSize = 2,
            MapName = "de_mirage",
            RoundId = 1,
            SelfHistory = new float[2 * 32 * 18],
            Teammates = new float[2 * 32 * 4 * 18],
            TemporalMask = Enumerable.Repeat(1.0f, 2 * 32).ToArray(),
            TeammateMask = Enumerable.Repeat(1.0f, 2 * 32 * 4).ToArray(),
            CandidateMask = PositioningTransformerContract.BuildV2CandidateMask(false).Concat(PositioningTransformerContract.BuildV2CandidateMask(true)).ToArray(),
            ObjectiveEligible = new[] { false, false },
            RetakeEligible = new[] { false, false },
            TeamIdx = new[] { 0L, 1L },
            RoleIdx = new[] { 3L, 5L },
            StageIdx = new[] { 3L, 1L },
        };
        var preds = svc.PredictShadowBatch(input);
        Assert.Equal(2, preds.Length);
        Assert.All(preds, p => Assert.True(p.InferenceSuccess));
    }

    [Fact]
    public void ShadowModeCannotAffectDecision()
    {
        var suggestion = new PositioningShadowPrediction
        {
            InputValid = true,
            InferenceSuccess = true,
            FinalState = PositioningStateKind.HOLD,
            SelectedSpotId = 0,
            SaveFallbackActive = true,
        };
        string decision = ShadowModeGuard.ShadowModeCannotAffectBotDecision("UTILITY_AI_DECISION_HOLD", suggestion);
        Assert.Equal("UTILITY_AI_DECISION_HOLD", decision);
    }
}
