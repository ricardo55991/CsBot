using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public sealed class PositioningContractV2Tests
{
    private static readonly string RepoRoot = FindRepoRoot();
    private static readonly string ModelPath = Path.Combine(RepoRoot, "models", "positioning", "de_mirage_positioning_hybrid_v1_candidate.onnx");
    private static readonly string OutDir = Path.Combine(RepoRoot, "training_runs", "positioning_v2_real_temporal", "csharp_shadow_integration", "side_contract_v2");
    private static readonly string ContractV2Path = Path.Combine(OutDir, "spot_side_contract_v2.json");

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
        return Directory.GetCurrentDirectory();
    }

    private static PositioningShadowInferenceInput MakeValidInput(int batchSize, bool isTerrorist = false)
    {
        var selfHist = new float[batchSize * 32 * 18];
        var tm = new float[batchSize * 32 * 4 * 18];
        var tmask = new float[batchSize * 32];
        var tmaskTm = new float[batchSize * 32 * 4];
        var candMask = new bool[batchSize * PositioningTransformerContract.CandidateSpotCount];
        var objElig = new bool[batchSize];
        var retElig = new bool[batchSize];

        var v2Mask = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist, "HOLD", false, false);
        for (int b = 0; b < batchSize; b++)
        {
            for (int t = 0; t < 32; t++)
            {
                tmask[b * 32 + t] = 1.0f;
                int baseOff = (b * 32 + t) * 18;
                selfHist[baseOff + 13] = isTerrorist ? 1.0f : 0.0f;
                selfHist[baseOff + 14] = isTerrorist ? 0.0f : 1.0f;
                for (int j = 0; j < 4; j++)
                {
                    tmaskTm[(b * 32 + t) * 4 + j] = 1.0f;
                }
            }
            Array.Copy(v2Mask, 0, candMask, b * PositioningTransformerContract.CandidateSpotCount, PositioningTransformerContract.CandidateSpotCount);
        }

        return new PositioningShadowInferenceInput
        {
            BatchSize = batchSize,
            MapName = "de_mirage",
            RoundId = 1,
            SelfHistory = selfHist,
            Teammates = tm,
            TemporalMask = tmask,
            TeammateMask = tmaskTm,
            CandidateMask = candMask,
            ObjectiveEligible = objElig,
            RetakeEligible = retElig,
        };
    }

    [Fact]
    public void WarmupCoversBatchOneThroughFive()
    {
        using var svc = new PositioningTransformerService();
        bool loaded = svc.LoadModel(ModelPath);
        Assert.True(loaded);
        Assert.True(svc.IsReady);
        Assert.True(svc.WarmupSuccess);
        Assert.Equal(5, svc.WarmupBatchMetrics.Count);
        for (int i = 0; i < 5; i++)
        {
            var m = svc.WarmupBatchMetrics[i];
            Assert.Equal(i + 1, m.BatchSize);
            Assert.True(m.Success);
            Assert.True(m.OutputBoundsValid);
            Assert.True(m.WarmupDurationMs >= 0.0);
            Assert.Equal(string.Empty, m.Exception);
        }

        if (Directory.Exists(OutDir))
        {
            var payload = new
            {
                warmup_success = svc.WarmupSuccess,
                total_warmup_duration_ms = svc.WarmupDurationMs,
                batches = svc.WarmupBatchMetrics,
            };
            File.WriteAllText(
                Path.Combine(OutDir, "multibatch_warmup_metrics.json"),
                JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        }
    }

    [Fact]
    public void WarmupDoesNotEmitTelemetry()
    {
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath));
        var perf = svc.GetPerformanceSnapshot();
        Assert.Equal(0, perf.TotalInferences);
        Assert.Equal(0, perf.FailureCount);
        Assert.Equal(0, perf.TimeoutCount);
        Assert.Equal(0, perf.DroppedRequests);
    }

    [Fact]
    public void WarmupFailurePreventsReadyState()
    {
        using var svc = new PositioningTransformerService();
        bool loaded = svc.LoadModel(Path.Combine(RepoRoot, "models", "positioning", "non_existent_model.onnx"));
        Assert.False(loaded);
        Assert.False(svc.IsReady);
        Assert.False(svc.WarmupSuccess);
        Assert.False(string.IsNullOrEmpty(svc.LastLoadError));
    }

    [Fact]
    public void FirstRealBatchAfterWarmupWithinBudget()
    {
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath));
        for (int b = 1; b <= 5; b++)
        {
            var input = MakeValidInput(b, isTerrorist: b % 2 == 0);
            var sw = Stopwatch.StartNew();
            var res = svc.PredictShadowBatch(input);
            sw.Stop();
            Assert.NotNull(res);
            Assert.Equal(b, res.Length);
            Assert.Equal(0, svc.GetPerformanceSnapshot().TimeoutCount);
            Assert.True(sw.Elapsed.TotalMilliseconds <= 25.0,
                $"Batch {b} latency {sw.Elapsed.TotalMilliseconds:F2} ms exceeded timeout 25.0 ms");
        }
    }

    [Fact]
    public void SpotSideContractClassifiesAll53Spots()
    {
        Assert.Equal(53, PositioningTransformerContract.V2SpotClassifications.Length);
        Assert.Equal(53, PositioningTransformerContract.V2CtRules.Length);
        Assert.Equal(53, PositioningTransformerContract.V2TRules.Length);

        var allowed = new HashSet<string> { "CT_ONLY", "T_ONLY", "SHARED", "CONTEXTUAL", "CATALOG_REVIEW_REQUIRED" };
        foreach (var cls in PositioningTransformerContract.V2SpotClassifications)
        {
            Assert.Contains(cls, allowed);
        }
    }

    [Fact]
    public void CtOnlySpotMaskedOutForT()
    {
        var maskT = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: true, "HOLD", false, false);
        for (int i = 0; i < 53; i++)
        {
            if (PositioningTransformerContract.V2SpotClassifications[i] == "CT_ONLY")
            {
                Assert.False(maskT[i]);
            }
        }
    }

    [Fact]
    public void TOnlySpotMaskedOutForCt()
    {
        var maskCt = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: false, "HOLD", false, false);
        for (int i = 0; i < 53; i++)
        {
            if (PositioningTransformerContract.V2SpotClassifications[i] == "T_ONLY")
            {
                Assert.False(maskCt[i]);
            }
        }
    }

    [Fact]
    public void SharedSpotAllowedForBothTeams()
    {
        var maskCt = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: false);
        var maskT = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: true);
        for (int i = 0; i < 53; i++)
        {
            if (PositioningTransformerContract.V2SpotClassifications[i] == "SHARED")
            {
                Assert.True(maskCt[i]);
                Assert.True(maskT[i]);
            }
        }
    }

    [Fact]
    public void ContextualSpotAllowedOnlyWhenConditionHolds()
    {
        // Index 6 has CT_RULE=RETAKE_ONLY, T_RULE=OBJECTIVE_OR_POSTPLANT
        var ctNoRetake = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: false, "HOLD", false, retakeEligible: false);
        var ctRetake = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: false, "RETAKE", false, retakeEligible: true);
        Assert.False(ctNoRetake[6]);
        Assert.True(ctRetake[6]);

        var tTransit = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: true, "TRANSIT", objectiveEligible: false, retakeEligible: false);
        var tObj = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: true, "OBJECTIVE", objectiveEligible: true, retakeEligible: false);
        Assert.False(tTransit[6]);
        Assert.True(tObj[6]);
    }

    [Fact]
    public void CatalogReviewRequiredSpotIsExplicitlyTracked()
    {
        int count = PositioningTransformerContract.V2SpotClassifications.Count(c => c == "CATALOG_REVIEW_REQUIRED");
        Assert.Equal(4, count);
    }

    [Fact]
    public void LayerMaskOrderMatchesSpecification()
    {
        var supMask = new bool[53];
        supMask[0] = true; // SHARED
        supMask[6] = true; // CONTEXTUAL
        supMask[1] = false; // Unsupervised SHARED

        var res = PositioningTransformerContract.BuildV2CandidateMask(
            isTerrorist: false,
            positioningState: "HOLD",
            objectiveEligible: false,
            retakeEligible: false,
            supervisedMask: supMask);

        Assert.True(res[0]);
        Assert.False(res[1]); // Layer 1 (supervised_spot_mask) bloqueia antes de Layer 2
        Assert.False(res[6]); // Layer 4 (phase_mask) bloqueia RETAKE_ONLY sem retakeEligible
    }

    [Fact]
    public void UtilityAiSpotAssignmentRespectsSideContract()
    {
        // Garante que BuildV2CandidateMask bloqueia qualquer spot FORBIDDEN (CT em T_ONLY e T em CT_ONLY)
        var maskCt = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: false, "OBJECTIVE", true, true);
        var maskT = PositioningTransformerContract.BuildV2CandidateMask(isTerrorist: true, "OBJECTIVE", true, true);
        for (int i = 0; i < 53; i++)
        {
            if (PositioningTransformerContract.V2CtRules[i] == "FORBIDDEN") Assert.False(maskCt[i]);
            if (PositioningTransformerContract.V2TRules[i] == "FORBIDDEN") Assert.False(maskT[i]);
        }
    }

    [Fact]
    public void RepathCounterCountsUniqueEventsNotTicks()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(100);

        Assert.True(tracker.TryRegisterAssignment(1, 0, "p0", "CT", "ct_a_site_stairs", 0, 0, 0, 100, 0, 0, 64, 101, false));
        // 50 ticks repetindo o mesmo spot
        for (int t = 102; t <= 151; t++)
        {
            Assert.False(tracker.TryRegisterAssignment(1, 0, "p0", "CT", "ct_a_site_stairs", 0, 0, 0, 100, 0, 0, 64, t, false));
        }
        // 1 mudança real de spot (MIDROUND_REPATH)
        Assert.False(tracker.TryRegisterAssignment(1, 0, "p0", "CT", "ct_b_site_van", 0, 0, 0, 200, 0, 0, 64, 152, false, PostOpeningRepathKind.MIDROUND_REPATH));
        // 1 mudança para TACTICAL_ROTATION
        Assert.False(tracker.TryRegisterAssignment(1, 0, "p0", "CT", "mid_window", 0, 0, 0, 300, 0, 0, 64, 153, false, PostOpeningRepathKind.TACTICAL_ROTATION));

        Assert.Equal(1, tracker.UniqueMidroundRepaths);
        Assert.Equal(0, tracker.UniqueRecoveryRepaths);
        Assert.Equal(1, tracker.UniqueTacticalRotations);
        Assert.Equal(50, tracker.RepeatedEventDuplicates);
        Assert.Equal(2, tracker.RepathsByPlayerRound[(1, "p0")]);
    }

    [Fact]
    public void RepeatedSameSpotAssignmentDoesNotIncrementRepaths()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(10);

        Assert.True(tracker.TryRegisterAssignment(1, 2, "p2", "T", "tr_b_apps_kitchen_control", 0, 0, 0, 100, 0, 0, 64, 11, false));
        for (int t = 12; t < 112; t++)
        {
            tracker.TryRegisterAssignment(1, 2, "p2", "T", "tr_b_apps_kitchen_control", 0, 0, 0, 100, 0, 0, 64, t, false);
        }

        Assert.Equal(0, tracker.UniqueMidroundRepaths);
        Assert.Equal(0, tracker.UniqueRecoveryRepaths);
        Assert.Equal(0, tracker.UniqueTacticalRotations);
        Assert.Equal(100, tracker.RepeatedEventDuplicates);
    }

    [Fact]
    public void RouteAccountingHasZeroResidue()
    {
        var tracker = new OpeningRouteTracker();
        tracker.OnRoundStart(1);
        tracker.OnFreezeTimeEnded(10);
        tracker.TryRegisterAssignment(1, 0, "p0", "CT", "ct_a_site_stairs", 0, 0, 0, 100, 0, 0, 64, 11, false);
        tracker.TryRegisterAssignment(1, 1, "p1", "CT", "ct_b_site_van", 0, 0, 0, 100, 0, 0, 64, 12, false);
        tracker.CloseAllOpenRoutes(1, OpeningRouteTerminationReason.ROUND_END, 500);

        Assert.Equal(0, tracker.ComputeAccountingResidue());
        Assert.Equal(2, tracker.ClosedRoutes.Count);
        Assert.Equal(0, tracker.ActiveOpenRoutes);
    }

    [Fact]
    public void TestIsNotUsedForContractSelection()
    {
        Assert.True(File.Exists(ContractV2Path));
        using var doc = JsonDocument.Parse(File.ReadAllText(ContractV2Path));
        var root = doc.RootElement;
        Assert.Equal("spot_side_contract_v2", root.GetProperty("contract_version").GetString());
        // Garante que o contrato V2 não incorpora métricas de Test nem seleção baseada em Test
        Assert.False(root.TryGetProperty("test_mrr", out _));
        Assert.False(root.TryGetProperty("test_top5", out _));
        Assert.Equal(53, root.GetProperty("spots").GetArrayLength());
    }
}
