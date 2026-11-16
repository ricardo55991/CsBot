using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public sealed class PositioningShadowIntegrationTests
{
    private static readonly string RepoRoot = FindRepoRoot();
    private static readonly string ModelPath = Path.Combine(RepoRoot, "models", "positioning", "de_mirage_positioning_hybrid_v1_candidate.onnx");
    private static readonly string OutDir = Path.Combine(RepoRoot, "training_runs", "positioning_v2_real_temporal", "csharp_shadow_integration");
    private static readonly string ManifestPath = Path.Combine(OutDir, "model_deployment_manifest.json");
    private static readonly string ParityBundlePath = Path.Combine(OutDir, "parity_reference_bundle.json");

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "AGENTS.md")))
            {
                return dir.FullName;
            }
            dir = dir.Parent;
        }
        throw new InvalidOperationException("Repository root not found.");
    }

    private static string ReadExpectedSha256()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(ManifestPath));
        return doc.RootElement.GetProperty("sha256").GetString()!;
    }

    private static PositioningShadowInferenceInput MakeValidInput(int batchSize, int roundId = 1, bool objectiveEligible = false, bool retakeEligible = false, bool hasRoundBoundaryCrossing = false, bool playerAlive = true)
    {
        int b = batchSize;
        var selfHist = new float[b * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.FeatureCount];
        var teammates = new float[b * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots * PositioningTransformerContract.FeatureCount];
        var tMask = new float[b * PositioningTransformerContract.SequenceLength];
        var tmMask = new float[b * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots];
        var candMask = new bool[b * PositioningTransformerContract.CandidateSpotCount];
        var objElig = new bool[b];
        var retElig = new bool[b];
        var alive = new bool[b];

        for (int i = 0; i < b; i++)
        {
            for (int t = 0; t < PositioningTransformerContract.SequenceLength; t++)
            {
                tMask[i * PositioningTransformerContract.SequenceLength + t] = 1.0f;
                selfHist[(i * PositioningTransformerContract.SequenceLength + t) * PositioningTransformerContract.FeatureCount] = 0.1f * (i + 1);
            }
            for (int s = 0; s < PositioningTransformerContract.CandidateSpotCount; s++)
            {
                candMask[i * PositioningTransformerContract.CandidateSpotCount + s] = true;
            }
            objElig[i] = objectiveEligible;
            retElig[i] = retakeEligible;
            alive[i] = playerAlive;
        }

        return new PositioningShadowInferenceInput
        {
            BatchSize = b,
            MapName = "de_mirage",
            RoundId = roundId,
            HasRoundBoundaryCrossing = hasRoundBoundaryCrossing,
            SelfHistory = selfHist,
            Teammates = teammates,
            TemporalMask = tMask,
            TeammateMask = tmMask,
            CandidateMask = candMask,
            ObjectiveEligible = objElig,
            RetakeEligible = retElig,
            PlayerAlive = alive
        };
    }

    [Fact]
    public void ModelLoadsOnce()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));
        Assert.True(svc.LoadModel(ModelPath, sha));
        Assert.Equal(1, svc.ModelLoadCount);
    }

    [Fact]
    public void ModelHashMatchesManifest()
    {
        string expected = ReadExpectedSha256();
        string actual = PositioningTransformerService.ComputeFileSha256(ModelPath);
        Assert.Equal(expected, actual);
    }

    [Fact]
    public void InvalidHashBlocksLoad()
    {
        using var svc = new PositioningTransformerService();
        bool loaded = svc.LoadModel(ModelPath, new string('0', 64));
        Assert.False(loaded);
        Assert.False(svc.IsModelLoaded);
        Assert.Contains("HASH_MISMATCH", svc.LastLoadError, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void MissingModelFailsGracefully()
    {
        using var svc = new PositioningTransformerService();
        bool loaded = svc.LoadModel(Path.Combine(RepoRoot, "models", "positioning", "does_not_exist.onnx"));
        Assert.False(loaded);
        Assert.False(svc.IsModelLoaded);
        var preds = svc.PredictShadowBatch(MakeValidInput(1));
        Assert.Single(preds);
        Assert.False(preds[0].InferenceSuccess);
        Assert.True(preds[0].SaveFallbackActive);
    }

    [Fact]
    public void InputShapeValidationRejectsBadTensor()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var bad = MakeValidInput(2);
        var broken = new PositioningShadowInferenceInput
        {
            BatchSize = 2,
            MapName = "de_mirage",
            RoundId = 1,
            SelfHistory = new float[10], // wrong length
            Teammates = bad.Teammates,
            TemporalMask = bad.TemporalMask,
            TeammateMask = bad.TeammateMask,
            CandidateMask = bad.CandidateMask,
            ObjectiveEligible = bad.ObjectiveEligible,
            RetakeEligible = bad.RetakeEligible,
            PlayerAlive = bad.PlayerAlive
        };
        var preds = svc.PredictShadowBatch(broken);
        Assert.Equal(2, preds.Length);
        Assert.All(preds, p =>
        {
            Assert.False(p.InputValid);
            Assert.False(p.InferenceSuccess);
            Assert.True(p.SaveFallbackActive);
        });
    }

    [Fact]
    public void NaNAndInfTriggerSafeFallback()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var nanInput = MakeValidInput(1);
        nanInput.SelfHistory[0] = float.NaN;
        var p1 = svc.PredictShadowBatch(nanInput);
        Assert.False(p1[0].InputValid);
        Assert.False(p1[0].InferenceSuccess);

        var infInput = MakeValidInput(1);
        infInput.Teammates[0] = float.PositiveInfinity;
        var p2 = svc.PredictShadowBatch(infInput);
        Assert.False(p2[0].InputValid);
        Assert.False(p2[0].InferenceSuccess);
    }

    [Fact]
    public void CandidateSpotMaskRespected()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var input = MakeValidInput(1);
        Array.Fill(input.CandidateMask, false);
        int allowedSpot = Array.FindIndex(PositioningTransformerContract.DefaultSupervisedSpotMask, x => x);
        Assert.True(allowedSpot >= 0);
        input.CandidateMask[allowedSpot] = true;

        var preds = svc.PredictShadowBatch(input);
        Assert.True(preds[0].InferenceSuccess);
        Assert.Equal(allowedSpot, preds[0].SelectedSpotId);
    }

    [Fact]
    public void SupervisedSpotMaskRespected()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var input = MakeValidInput(5);
        var preds = svc.PredictShadowBatch(input);
        foreach (var p in preds)
        {
            Assert.True(p.InferenceSuccess);
            Assert.NotNull(p.SelectedSpotId);
            Assert.True(PositioningTransformerContract.DefaultSupervisedSpotMask[p.SelectedSpotId!.Value]);
        }
    }

    [Fact]
    public void ObjectiveMaskBlocksIllegalOverride()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var input = MakeValidInput(4, objectiveEligible: false, retakeEligible: false);
        var preds = svc.PredictShadowBatch(input);
        Assert.All(preds, p => Assert.NotEqual(PositioningStateKind.OBJECTIVE, p.FinalState));
    }

    [Fact]
    public void RetakeMaskBlocksIllegalOverride()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var input = MakeValidInput(4, objectiveEligible: false, retakeEligible: false);
        var preds = svc.PredictShadowBatch(input);
        Assert.All(preds, p => Assert.NotEqual(PositioningStateKind.RETAKE, p.FinalState));
    }

    [Fact]
    public void SavePredictionAlwaysDisabled()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var preds = svc.PredictShadowBatch(MakeValidInput(5, objectiveEligible: true, retakeEligible: false));
        Assert.All(preds, p =>
        {
            Assert.NotNull(p.FinalState);
            Assert.InRange((int)p.FinalState!.Value, 0, PositioningTransformerContract.NeuralStateCount - 1);
            Assert.True(p.SaveFallbackActive);
            Assert.Equal("SAVE_FALLBACK_ACTIVE", p.FallbackReason);
        });
    }

    [Fact]
    public void SaveAlwaysDelegatesToUtilityAi()
    {
        var shadowSaveLike = new PositioningShadowPrediction
        {
            InputValid = true,
            InferenceSuccess = true,
            FinalState = PositioningStateKind.HOLD,
            SaveFallbackActive = true,
            FallbackReason = "SAVE_FALLBACK_ACTIVE"
        };
        string decision = ShadowModeGuard.ShadowModeCannotAffectBotDecision("UTILITY_SAVE", shadowSaveLike);
        Assert.Equal("UTILITY_SAVE", decision);
        Assert.True(shadowSaveLike.SaveFallbackActive);
    }

    [Fact]
    public void ShadowModeCannotAffectBotDecision()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));
        var preds = svc.PredictShadowBatch(MakeValidInput(1));
        string utilityChoice = "HOLD_SITE_A_SPOT_3";
        string actual = ShadowModeGuard.ShadowModeCannotAffectBotDecision(utilityChoice, preds[0]);
        Assert.Equal(utilityChoice, actual);
    }

    [Fact]
    public void RoundBoundaryResetsSequenceBuffer()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));
        var preds = svc.PredictShadowBatch(MakeValidInput(1, roundId: 2, hasRoundBoundaryCrossing: true));
        Assert.False(preds[0].InputValid);
        Assert.False(preds[0].InferenceSuccess);
        Assert.Contains("ROUND_BOUNDARY", preds[0].FallbackReason);
    }

    [Fact]
    public void DeadPlayerDoesNotPolluteSequence()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));
        var preds = svc.PredictShadowBatch(MakeValidInput(2, playerAlive: false));
        Assert.All(preds, p =>
        {
            Assert.False(p.InputValid);
            Assert.False(p.InferenceSuccess);
            Assert.Contains("DEAD_PLAYER", p.FallbackReason);
        });
    }

    [Fact]
    public void BufferReuseAvoidsPerTickAllocations()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        var input = MakeValidInput(5);
        _ = svc.PredictShadowBatch(input); // warm-up allocates reusable buffers
        long reuseBefore = svc.GetPerformanceSnapshot().BufferReuseCount;
        for (int i = 0; i < 10; i++)
        {
            _ = svc.PredictShadowBatch(input);
        }
        long reuseAfter = svc.GetPerformanceSnapshot().BufferReuseCount;
        Assert.Equal(10, reuseAfter - reuseBefore);
    }

    [Fact]
    public void BatchInferenceHandlesOneToTenBots()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        for (int b = 1; b <= 10; b++)
        {
            var preds = svc.PredictShadowBatch(MakeValidInput(b));
            Assert.Equal(b, preds.Length);
            Assert.All(preds, p => Assert.True(p.InferenceSuccess));
        }
    }

    [Fact]
    public void TimeoutTriggersSafeFallback()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService { InferenceTimeoutMs = 5 };
        Assert.True(svc.LoadModel(ModelPath, sha));
        svc.TestPreInferenceHook = () => System.Threading.Thread.Sleep(15);

        var preds = svc.PredictShadowBatch(MakeValidInput(1));
        Assert.False(preds[0].InferenceSuccess);
        Assert.True(preds[0].SaveFallbackActive);
        Assert.Contains("TIMEOUT", preds[0].FallbackReason);
        Assert.True(svc.GetPerformanceSnapshot().TimeoutCount >= 1);
    }

    [Fact]
    public void AsyncTelemetryDoesNotBlockTick()
    {
        string tmpLog = Path.Combine(Path.GetTempPath(), $"csbot_shadow_test_{Guid.NewGuid():N}.jsonl");
        try
        {
            using var logger = new PositioningShadowTelemetryLogger(tmpLog);
            var sw = Stopwatch.StartNew();
            for (int i = 0; i < 200; i++)
            {
                logger.Enqueue(new PositioningShadowTelemetryRecord(
                    DateTimeOffset.UtcNow.ToString("O"),
                    "de_mirage",
                    "test_match",
                    1,
                    i,
                    PositioningTransformerContract.PseudonymizePlayerSlot(i % 10, "test_match"),
                    "CT",
                    "sha",
                    PositioningTransformerContract.ContractVersion,
                    true,
                    true,
                    1.2,
                    "HOLD",
                    "HOLD",
                    "A",
                    "A",
                    "spot_1",
                    "spot_1",
                    "HOLD_POSITION",
                    "NONE",
                    new float[] { 0.8f, 0.9f, 0.7f, 0.6f, 0.8f, 0.7f },
                    false,
                    false,
                    true,
                    "SAVE_FALLBACK_ACTIVE"));
            }
            sw.Stop();
            Assert.True(sw.Elapsed.TotalMilliseconds < 50.0, $"Enqueue took {sw.Elapsed.TotalMilliseconds} ms");
            logger.FlushSync();
            Assert.Equal(200, logger.WrittenCount);
        }
        finally
        {
            if (File.Exists(tmpLog)) File.Delete(tmpLog);
        }
    }

    [Fact]
    public void TelemetryContainsRequiredFields()
    {
        string tmpLog = Path.Combine(Path.GetTempPath(), $"csbot_shadow_fields_{Guid.NewGuid():N}.jsonl");
        try
        {
            using (var logger = new PositioningShadowTelemetryLogger(tmpLog))
            {
                logger.Enqueue(new PositioningShadowTelemetryRecord(
                    DateTimeOffset.UtcNow.ToString("O"),
                    "de_mirage",
                    "match_1",
                    1,
                    64,
                    PositioningTransformerContract.PseudonymizePlayerSlot(2, "match_1"),
                    "CT",
                    ReadExpectedSha256(),
                    PositioningTransformerContract.ContractVersion,
                    true,
                    true,
                    2.5,
                    "HOLD",
                    "HOLD",
                    "A",
                    "A",
                    "spot_1",
                    "spot_1",
                    "NONE",
                    "NONE",
                    new float[] { 0.8f, 0.9f, 0.7f, 0.6f, 0.8f, 0.7f },
                    false,
                    false,
                    true,
                    "SAVE_FALLBACK_ACTIVE"));
                logger.FlushSync();
            }

            string line = File.ReadLines(tmpLog).First();
            using var doc = JsonDocument.Parse(line);
            string[] required =
            {
                "timestamp","map","match_id","round_id","tick","player_slot","team",
                "model_hash","contract_version","input_valid","inference_success","latency_ms",
                "utility_state","neural_state","utility_sector","neural_sector",
                "utility_spot","neural_spot","neural_transition","neural_exit_trigger",
                "confidence_by_head","objective_eligible","retake_eligible",
                "save_fallback_active","fallback_reason"
            };
            foreach (string key in required)
            {
                Assert.True(doc.RootElement.TryGetProperty(key, out _), $"Missing field {key}");
            }
        }
        finally
        {
            if (File.Exists(tmpLog)) File.Delete(tmpLog);
        }
    }

    [Fact]
    public void TelemetryContainsNoSecretOrRawPath()
    {
        string tmpLog = Path.Combine(Path.GetTempPath(), $"csbot_shadow_sec_{Guid.NewGuid():N}.jsonl");
        try
        {
            string slot = PositioningTransformerContract.PseudonymizePlayerSlot(3, "match_abc");
            Assert.Equal(12, slot.Length);
            Assert.DoesNotContain("7656119", slot);

            using (var logger = new PositioningShadowTelemetryLogger(tmpLog))
            {
                logger.Enqueue(new PositioningShadowTelemetryRecord(
                    DateTimeOffset.UtcNow.ToString("O"),
                    "de_mirage",
                    "match_abc",
                    1,
                    128,
                    slot,
                    "T",
                    ReadExpectedSha256(),
                    PositioningTransformerContract.ContractVersion,
                    true,
                    true,
                    1.5,
                    "TRANSIT",
                    "TRANSIT",
                    "MID",
                    "MID",
                    "spot_2",
                    "spot_2",
                    "NONE",
                    "NONE",
                    new float[] { 0.8f, 0.9f, 0.7f, 0.6f, 0.8f, 0.7f },
                    false,
                    false,
                    true,
                    "SAVE_FALLBACK_ACTIVE"));
                logger.FlushSync();
            }

            string content = File.ReadAllText(tmpLog);
            Assert.DoesNotContain("C:\\", content);
            Assert.DoesNotContain("H:\\", content);
            Assert.DoesNotContain("token", content, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("7656119", content);
        }
        finally
        {
            if (File.Exists(tmpLog)) File.Delete(tmpLog);
        }
    }

    [Fact]
    public void UnloadDisposesOnnxSession()
    {
        string sha = ReadExpectedSha256();
        var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));
        Assert.True(svc.IsModelLoaded);
        svc.Dispose();
        Assert.False(svc.IsModelLoaded);
        var preds = svc.PredictShadowBatch(MakeValidInput(1));
        Assert.False(preds[0].InferenceSuccess);
    }

    [Fact]
    public void NonMirageMapDoesNotLoadMirageModel()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));
        var dust2 = new PositioningShadowInferenceInput
        {
            BatchSize = 1,
            MapName = "de_dust2",
            RoundId = 1,
            SelfHistory = MakeValidInput(1).SelfHistory,
            Teammates = MakeValidInput(1).Teammates,
            TemporalMask = MakeValidInput(1).TemporalMask,
            TeammateMask = MakeValidInput(1).TeammateMask,
            CandidateMask = MakeValidInput(1).CandidateMask,
            ObjectiveEligible = MakeValidInput(1).ObjectiveEligible,
            RetakeEligible = MakeValidInput(1).RetakeEligible,
            PlayerAlive = MakeValidInput(1).PlayerAlive
        };
        var preds = svc.PredictShadowBatch(dust2);
        Assert.False(preds[0].InputValid);
        Assert.False(preds[0].InferenceSuccess);
        Assert.Contains("NON_MIRAGE_MAP_SKIPPED", preds[0].FallbackReason);
    }

    [Fact]
    public void RuntimeExceptionDoesNotCrashServer()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));
        svc.TestPreInferenceHook = () => throw new InvalidOperationException("Simulated ONNX failure");
        var preds = svc.PredictShadowBatch(MakeValidInput(1));
        Assert.Single(preds);
        Assert.False(preds[0].InferenceSuccess);
        Assert.True(preds[0].SaveFallbackActive);
        Assert.True(svc.GetPerformanceSnapshot().FailureCount >= 1);
    }

    [Fact]
    public void PythonVsCSharpOnnxParityMatchesExactly()
    {
        Assert.True(File.Exists(ParityBundlePath), $"Missing {ParityBundlePath}");
        using var doc = JsonDocument.Parse(File.ReadAllText(ParityBundlePath));
        var root = doc.RootElement;
        int n = root.GetProperty("sample_count").GetInt32();
        bool[] supMask = root.GetProperty("supervised_spot_mask").EnumerateArray().Select(e => e.GetBoolean()).ToArray();
        var inputsEl = root.GetProperty("inputs");
        var expEl = root.GetProperty("expected_outputs");

        var input = new PositioningShadowInferenceInput
        {
            BatchSize = n,
            MapName = "de_mirage",
            RoundId = 1,
            SelfHistory = inputsEl.GetProperty("self_history").EnumerateArray().Select(e => e.GetSingle()).ToArray(),
            Teammates = inputsEl.GetProperty("teammates").EnumerateArray().Select(e => e.GetSingle()).ToArray(),
            TemporalMask = inputsEl.GetProperty("temporal_mask").EnumerateArray().Select(e => e.GetSingle()).ToArray(),
            TeammateMask = inputsEl.GetProperty("teammate_mask").EnumerateArray().Select(e => e.GetSingle()).ToArray(),
            CandidateMask = inputsEl.GetProperty("candidate_mask").EnumerateArray().Select(e => e.GetBoolean()).ToArray(),
            ObjectiveEligible = inputsEl.GetProperty("objective_eligible").EnumerateArray().Select(e => e.GetBoolean()).ToArray(),
            RetakeEligible = inputsEl.GetProperty("retake_eligible").EnumerateArray().Select(e => e.GetBoolean()).ToArray(),
            PlayerAlive = Enumerable.Repeat(true, n).ToArray()
        };

        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService(supMask);
        Assert.True(svc.LoadModel(ModelPath, sha));
        var raw = svc.RunRawOutputsForParity(input);

        static (double maxErr, double meanErr) FloatDiff(float[] actual, float[] expected)
        {
            Assert.Equal(expected.Length, actual.Length);
            double maxE = 0.0;
            double sumE = 0.0;
            for (int i = 0; i < actual.Length; i++)
            {
                double d = Math.Abs((double)actual[i] - (double)expected[i]);
                if (d > maxE) maxE = d;
                sumE += d;
            }
            return (maxE, sumE / Math.Max(1, actual.Length));
        }

        static double Agreement(long[] actual, long[] expected)
        {
            Assert.Equal(expected.Length, actual.Length);
            int eq = 0;
            for (int i = 0; i < actual.Length; i++)
            {
                if (actual[i] == expected[i]) eq++;
            }
            return (double)eq / actual.Length;
        }

        float[] ExpF(string k) => expEl.GetProperty(k).EnumerateArray().Select(e => e.GetSingle()).ToArray();
        long[] ExpI(string k) => expEl.GetProperty(k).EnumerateArray().Select(e => e.GetInt64()).ToArray();

        var fHeads = new Dictionary<string, (double maxErr, double meanErr)>
        {
            ["final_state_logits"] = FloatDiff(raw.FinalStateLogits, ExpF("final_state_logits")),
            ["sector_transition_logits"] = FloatDiff(raw.SectorTransitionLogits, ExpF("sector_transition_logits")),
            ["next_sector_logits"] = FloatDiff(raw.NextSectorLogits, ExpF("next_sector_logits")),
            ["spot_logits"] = FloatDiff(raw.SpotLogits, ExpF("spot_logits")),
            ["transition_logits"] = FloatDiff(raw.TransitionLogits, ExpF("transition_logits")),
            ["exit_trigger_logits"] = FloatDiff(raw.ExitTriggerLogits, ExpF("exit_trigger_logits")),
            ["confidence_by_head"] = FloatDiff(raw.ConfidenceByHead, ExpF("confidence_by_head")),
        };

        var iHeads = new Dictionary<string, double>
        {
            ["final_state_id"] = Agreement(raw.FinalStateId, ExpI("final_state_id")),
            ["sector_transition_id"] = Agreement(raw.SectorTransitionId, ExpI("sector_transition_id")),
            ["next_sector_id"] = Agreement(raw.NextSectorId, ExpI("next_sector_id")),
            ["selected_spot_id"] = Agreement(raw.SelectedSpotId, ExpI("selected_spot_id")),
            ["transition_id"] = Agreement(raw.TransitionId, ExpI("transition_id")),
            ["exit_trigger_id"] = Agreement(raw.ExitTriggerId, ExpI("exit_trigger_id")),
        };

        var report = new
        {
            provenance = "REAL",
            sample_count = n,
            model_sha256 = sha,
            numerical_parity = fHeads.ToDictionary(kv => kv.Key, kv => new { max_abs_error = kv.Value.maxErr, mean_abs_error = kv.Value.meanErr, pass = kv.Value.maxErr <= 1e-4 && kv.Value.meanErr <= 1e-5 }),
            decision_agreement = iHeads.ToDictionary(kv => kv.Key, kv => new { agreement = kv.Value, pass = kv.Value == 1.0 }),
            all_pass = fHeads.Values.All(v => v.maxErr <= 1e-4 && v.meanErr <= 1e-5) && iHeads.Values.All(a => a == 1.0)
        };
        File.WriteAllText(Path.Combine(OutDir, "python_csharp_parity.json"), JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));

        Assert.True(report.all_pass);
    }

    [Fact]
    public void CpuLatencyBenchmarkBatch1And5MeetsBudget()
    {
        string sha = ReadExpectedSha256();
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, sha));

        static object Bench(PositioningTransformerService service, int batchSize, int warmup, int iters)
        {
            var inp = MakeValidInput(batchSize);
            for (int i = 0; i < warmup; i++) _ = service.PredictShadowBatch(inp);

            GC.Collect();
            GC.WaitForPendingFinalizers();
            int g0Before = GC.CollectionCount(0);
            int g1Before = GC.CollectionCount(1);
            int g2Before = GC.CollectionCount(2);
            long allocBefore = GC.GetAllocatedBytesForCurrentThread();

            var latencies = new double[iters];
            var swTotal = Stopwatch.StartNew();
            for (int i = 0; i < iters; i++)
            {
                var sw = Stopwatch.StartNew();
                var preds = service.PredictShadowBatch(inp);
                sw.Stop();
                Assert.True(preds.All(p => p.InferenceSuccess));
                latencies[i] = sw.Elapsed.TotalMilliseconds;
            }
            swTotal.Stop();

            long allocAfter = GC.GetAllocatedBytesForCurrentThread();
            int g0After = GC.CollectionCount(0);
            int g1After = GC.CollectionCount(1);
            int g2After = GC.CollectionCount(2);

            Array.Sort(latencies);
            double Pct(double q)
            {
                int idx = Math.Min(latencies.Length - 1, Math.Max(0, (int)Math.Ceiling(q * latencies.Length) - 1));
                return latencies[idx];
            }

            return new
            {
                batch_size = batchSize,
                iterations = iters,
                p50_ms = Math.Round(Pct(0.50), 4),
                p95_ms = Math.Round(Pct(0.95), 4),
                p99_ms = Math.Round(Pct(0.99), 4),
                mean_ms = Math.Round(latencies.Average(), 4),
                throughput_seq_per_sec = Math.Round((iters * batchSize) / Math.Max(1e-6, swTotal.Elapsed.TotalSeconds), 2),
                allocated_bytes_total = Math.Max(0, allocAfter - allocBefore),
                allocated_bytes_per_call = Math.Round(Math.Max(0, allocAfter - allocBefore) / (double)iters, 1),
                gc_gen0 = g0After - g0Before,
                gc_gen1 = g1After - g1Before,
                gc_gen2 = g2After - g2Before
            };
        }

        var b1 = Bench(svc, 1, 20, 100);
        var b5 = Bench(svc, 5, 20, 100);
        var snap = svc.GetPerformanceSnapshot();

        var perf = new
        {
            provenance = "REAL_CPU_BENCHMARK",
            model_load_time_ms = Math.Round(snap.ModelLoadTimeMs, 3),
            batch_1 = b1,
            batch_5 = b5,
            dropped_requests = snap.DroppedRequests,
            timeout_count = snap.TimeoutCount,
            failure_count = snap.FailureCount,
            buffer_reuse_count = snap.BufferReuseCount
        };
        File.WriteAllText(Path.Combine(OutDir, "performance_metrics.json"), JsonSerializer.Serialize(perf, new JsonSerializerOptions { WriteIndented = true }));
    }
}
