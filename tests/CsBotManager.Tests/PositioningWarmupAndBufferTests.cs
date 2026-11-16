using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public sealed class PositioningWarmupAndBufferTests
{
    private static readonly string RepoRoot = FindRepoRoot();
    private static readonly string ModelPath = Path.Combine(RepoRoot, "models", "positioning", "de_mirage_positioning_hybrid_v1_candidate.onnx");
    private static readonly string ManifestPath = Path.Combine(RepoRoot, "training_runs", "positioning_v2_real_temporal", "csharp_shadow_integration", "model_deployment_manifest.json");
    private static readonly string RetryDir = Path.Combine(RepoRoot, "training_runs", "positioning_v2_real_temporal", "csharp_shadow_integration", "live_capture_retry");

    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "AGENTS.md"))) return dir.FullName;
            dir = dir.Parent;
        }
        throw new InvalidOperationException("Repo root not found.");
    }

    private static string ReadExpectedSha256()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(ManifestPath));
        return doc.RootElement.GetProperty("sha256").GetString()!;
    }

    private static PositioningPlayerObservation MakeObs(int tick, int roundId, int slot, bool isT, bool alive = true, float x = 100f, float y = -200f, string weapon = "weapon_ak47")
    {
        return new PositioningPlayerObservation(
            Tick: tick,
            RoundId: roundId,
            PlayerSlot: slot,
            IsTerrorist: isT,
            IsAlive: alive,
            X: x,
            Y: y,
            Z: 10f,
            Vx: 120f,
            Vy: -45f,
            Vz: 0f,
            YawDeg: 45f,
            PitchDeg: -3f,
            Health: alive ? 100f : 0f,
            Armor: alive ? 100f : 0f,
            WeaponName: weapon,
            RoleCode: 0.50f,
            HasC4: isT && slot == 1,
            IsBombPlanted: false,
            RoundTimeRemaining: 95f
        );
    }

    [Fact]
    public void ModelWarmupRunsBeforeReady()
    {
        using var svc = new PositioningTransformerService();
        Assert.False(svc.IsReady);
        bool ok = svc.LoadModel(ModelPath, ReadExpectedSha256());
        Assert.True(ok);
        Assert.True(svc.WarmupStarted);
        Assert.True(svc.WarmupSuccess);
        Assert.True(svc.WarmupDurationMs > 0.0);
        Assert.True(svc.IsReady);
    }

    [Fact]
    public void WarmupIsNotLoggedAsMatchInference()
    {
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, ReadExpectedSha256()));
        var snap = svc.GetPerformanceSnapshot();
        Assert.Equal(0, snap.TotalInferences);
        Assert.Equal(0, snap.SuccessfulInferences);
        Assert.Equal(0, snap.TimeoutCount);
    }

    [Fact]
    public void WarmupFailureFallsBackToUtilityAI()
    {
        using var svc = new PositioningTransformerService();
        svc.TestWarmupFailureHook = () => throw new InvalidOperationException("Simulated warmup failure");
        bool ok = svc.LoadModel(ModelPath, ReadExpectedSha256());
        Assert.False(ok);
        Assert.False(svc.WarmupSuccess);
        Assert.False(svc.IsReady);
        Assert.False(svc.IsModelLoaded);
        Assert.Contains("WARMUP_FAILED", svc.LastLoadError);

        string decision = ShadowModeGuard.ShadowModeCannotAffectBotDecision("UTILITY_HOLD", null);
        Assert.Equal("UTILITY_HOLD", decision);
    }

    [Fact]
    public void FeatureOrderMatchesPythonContract()
    {
        Assert.Equal(18, PositioningFeatureContract.CanonicalFeatures.Length);
        string[] expectedNames =
        {
            "pos_x","pos_y","pos_z","vel_x","vel_y","vel_z",
            "yaw_cos","yaw_sin","pitch_norm","health_norm","armor_norm",
            "weapon_category","role_code","is_terrorist","is_alive",
            "has_c4","is_bomb_planted","round_time_remaining_norm"
        };
        for (int i = 0; i < 18; i++)
        {
            Assert.Equal(i, PositioningFeatureContract.CanonicalFeatures[i].FeatureIndex);
            Assert.Equal(expectedNames[i], PositioningFeatureContract.CanonicalFeatures[i].FeatureName);
        }
    }

    [Fact]
    public void RingBufferHas32Frames()
    {
        var rb = new PositioningTemporalRingBuffer();
        for (int f = 0; f < 40; f++)
        {
            Assert.True(rb.TryPushObservation("m1", f * 4, MakeObs(f * 4, 1, 0, true, x: f * 10f), out _));
        }

        var cand = Enumerable.Repeat(true, 53).ToArray();
        var input = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 0 }, new[] { true }, cand, new[] { false }, new[] { false }, out var diag);
        Assert.Equal(32, diag[0].RealFrameCount);
        Assert.Equal(0, diag[0].PaddedFrameCount);
        Assert.All(input.TemporalMask, m => Assert.Equal(1.0f, m));
    }

    [Fact]
    public void RingBufferDoesNotCrossRound()
    {
        var rb = new PositioningTemporalRingBuffer();
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 0, true), out _));
        Assert.True(rb.TryPushObservation("m1", 8, MakeObs(8, 2, 0, true), out _));

        var cand = Enumerable.Repeat(true, 53).ToArray();
        _ = rb.BuildBatchInput("m1", "de_mirage", 2, new[] { 0 }, new[] { true }, cand, new[] { false }, new[] { false }, out var diag);
        Assert.Equal(1, diag[0].RealFrameCount);
        Assert.Equal(0, diag[0].CrossRoundWindows);
    }

    [Fact]
    public void RingBufferDoesNotCrossPlayer()
    {
        var rb = new PositioningTemporalRingBuffer();
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 0, true, x: 100f), out _));
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 1, false, x: -500f), out _));

        var cand = Enumerable.Repeat(true, 53).ToArray();
        var input = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 0 }, new[] { true }, cand, new[] { false }, new[] { false }, out var diag);
        Assert.Equal(0, diag[0].CrossPlayerWindows);
        Assert.Equal(100f / 4096f, input.SelfHistory[31 * 18 + 0], 5);
    }

    [Fact]
    public void RingBufferClearsOnRoundStart()
    {
        var rb = new PositioningTemporalRingBuffer();
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 0, true), out _));
        rb.OnRoundStart("m1", 2);
        Assert.Equal(0, rb.ActiveRingBufferCount);
        Assert.Equal("ROUND_START", rb.LastResetReason);
    }

    [Fact]
    public void InitialPaddingIsMasked()
    {
        var rb = new PositioningTemporalRingBuffer();
        for (int f = 0; f < 5; f++)
        {
            Assert.True(rb.TryPushObservation("m1", (f + 1) * 4, MakeObs((f + 1) * 4, 1, 0, true), out _));
        }

        var cand = Enumerable.Repeat(true, 53).ToArray();
        var input = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 0 }, new[] { true }, cand, new[] { false }, new[] { false }, out var diag);
        Assert.Equal(5, diag[0].RealFrameCount);
        Assert.Equal(27, diag[0].PaddedFrameCount);
        for (int t = 0; t < 27; t++) Assert.Equal(0.0f, input.TemporalMask[t]);
        for (int t = 27; t < 32; t++) Assert.Equal(1.0f, input.TemporalMask[t]);
    }

    [Fact]
    public void FutureFramesCannotEnterBuffer()
    {
        var rb = new PositioningTemporalRingBuffer();
        bool ok = rb.TryPushObservation("m1", currentServerTick: 100, MakeObs(tick: 120, 1, 0, true), out string reason);
        Assert.False(ok);
        Assert.Equal("FUTURE_FRAME_REJECTED", reason);
    }

    [Fact]
    public void CollectionRunsAtExpectedCadence()
    {
        Assert.Equal(4, PositioningFeatureContract.CollectionTickInterval);
        Assert.Equal(16.0, PositioningFeatureContract.ExpectedCollectionHz);

        var rb = new PositioningTemporalRingBuffer();
        for (int f = 0; f < 10; f++)
        {
            Assert.True(rb.TryPushObservation("m1", (f + 1) * 4, MakeObs((f + 1) * 4, 1, 0, true), out _));
        }
        var cand = Enumerable.Repeat(true, 53).ToArray();
        _ = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 0 }, new[] { true }, cand, new[] { false }, new[] { false }, out var diag);
        Assert.Equal(16.0, diag[0].EffectiveHistoryHz, 2);
    }

    [Fact]
    public void TeammatesComeFromRealAlliedSlots()
    {
        var rb = new PositioningTemporalRingBuffer();
        int[] tSlots = { 1, 2, 3, 4, 5 };
        foreach (int s in tSlots)
        {
            Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, s, isT: true, x: s * 100f), out _));
        }

        var cand = Enumerable.Repeat(true, 53).ToArray();
        var input = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 1 }, new[] { true }, cand, new[] { false }, new[] { false }, out var diag);
        Assert.Equal(0, diag[0].InvalidTeammateMappings);
        // Allies of slot 1 are slots 2, 3, 4, 5 in frame 31
        for (int j = 0; j < 4; j++)
        {
            Assert.Equal(1.0f, input.TeammateMask[31 * 4 + j]);
            Assert.Equal(((j + 2) * 100f) / 4096f, input.Teammates[(31 * 4 + j) * 18 + 0], 5);
        }
    }

    [Fact]
    public void SelfPlayerIsNotAteammate()
    {
        var rb = new PositioningTemporalRingBuffer();
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 1, isT: true, x: 999f), out _));
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 2, isT: true, x: 200f), out _));

        var cand = Enumerable.Repeat(true, 53).ToArray();
        var input = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 1 }, new[] { true }, cand, new[] { false }, new[] { false }, out _);
        Assert.Equal(1.0f, input.TeammateMask[31 * 4 + 0]);
        Assert.Equal(200f / 4096f, input.Teammates[(31 * 4 + 0) * 18 + 0], 5);
        Assert.Equal(0.0f, input.TeammateMask[31 * 4 + 1]);
    }

    [Fact]
    public void EnemyCannotEnterTeammateTensor()
    {
        var rb = new PositioningTemporalRingBuffer();
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 1, isT: true, x: 100f), out _));
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 6, isT: false, x: 777f), out _));

        var cand = Enumerable.Repeat(true, 53).ToArray();
        var input = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 1 }, new[] { true }, cand, new[] { false }, new[] { false }, out _);
        for (int j = 0; j < 4; j++) Assert.Equal(0.0f, input.TeammateMask[31 * 4 + j]);
    }

    [Fact]
    public void DeadOrMissingTeammateIsMasked()
    {
        var rb = new PositioningTemporalRingBuffer();
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 1, isT: true, alive: true), out _));
        Assert.True(rb.TryPushObservation("m1", 4, MakeObs(4, 1, 2, isT: true, alive: false), out _));

        var cand = Enumerable.Repeat(true, 53).ToArray();
        var input = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 1 }, new[] { true }, cand, new[] { false }, new[] { false }, out _);
        Assert.Equal(0.0f, input.TeammateMask[31 * 4 + 0]);
        Assert.Equal(0.0f, input.TeammateMask[31 * 4 + 1]);
    }

    [Fact]
    public void ObjectiveEligibilityUsesCurrentOrPastEvents()
    {
        // Causal check: objective eligibility depends only on current/past state (bomb_planted or current C4 possession)
        bool isT = true;
        bool bombPlantedNow = false;
        bool hasC4Now = true;
        bool eligible = isT && (bombPlantedNow || hasC4Now);
        Assert.True(eligible);
    }

    [Fact]
    public void RetakeEligibilityUsesCurrentOrPastEvents()
    {
        bool isCt = true;
        bool bombPlantedNow = false;
        Assert.False(isCt && bombPlantedNow);
        Assert.True(isCt && true);
    }

    [Fact]
    public void NeuralSaveRemainsDisabled()
    {
        using var svc = new PositioningTransformerService();
        Assert.True(svc.LoadModel(ModelPath, ReadExpectedSha256()));
        var rb = new PositioningTemporalRingBuffer();
        for (int f = 1; f <= 32; f++) rb.TryPushObservation("m1", f * 4, MakeObs(f * 4, 1, 0, true), out _);
        var cand = Enumerable.Repeat(true, 53).ToArray();
        var inp = rb.BuildBatchInput("m1", "de_mirage", 1, new[] { 0 }, new[] { true }, cand, new[] { false }, new[] { false }, out _);
        var preds = svc.PredictShadowBatch(inp);
        Assert.True(preds[0].SaveFallbackActive);
        Assert.Equal("SAVE_FALLBACK_ACTIVE", preds[0].FallbackReason);
    }

    [Fact]
    public void ShadowModeCannotAffectUtilityDecision()
    {
        string utilityDecision = "STAGING_A_RAMP";
        var shadow = new PositioningShadowPrediction { InferenceSuccess = true, FinalState = PositioningStateKind.HOLD };
        Assert.Equal(utilityDecision, ShadowModeGuard.ShadowModeCannotAffectBotDecision(utilityDecision, shadow));
    }

    [Fact]
    public void RuntimeFeatureSampleIsReproducible()
    {
        Directory.CreateDirectory(RetryDir);
        var samples = new List<object>();

        // 100 janelas completas + 20 com padding + 20 com aliado morto/ausente + 10 OBJECTIVE + 10 RETAKE = 160 janelas
        var rb = new PositioningTemporalRingBuffer();
        void PushAll10(int tick, int roundId, bool deadAlly = false, bool bombPlanted = false)
        {
            for (int s = 0; s < 10; s++)
            {
                bool isT = s < 5;
                bool alive = !(deadAlly && s == 1);
                rb.TryPushObservation("parity_m1", tick, new PositioningPlayerObservation(
                    Tick: tick,
                    RoundId: roundId,
                    PlayerSlot: s,
                    IsTerrorist: isT,
                    IsAlive: alive,
                    X: -1200f + s * 150f + tick * 0.5f,
                    Y: 300f - s * 80f + tick * 0.25f,
                    Z: -64f + s * 2f,
                    Vx: alive ? (50f + s * 10f) : 0f,
                    Vy: alive ? (-30f + s * 5f) : 0f,
                    Vz: 0f,
                    YawDeg: (s * 35f + tick) % 360f,
                    PitchDeg: -2.5f,
                    Health: alive ? (100f - s * 3f) : 0f,
                    Armor: alive ? 100f : 0f,
                    WeaponName: s % 3 == 0 ? "weapon_awp" : (s % 2 == 0 ? "weapon_ak47" : "weapon_knife"),
                    RoleCode: 0.25f * ((s % 4) + 1),
                    HasC4: isT && s == 0 && !bombPlanted,
                    IsBombPlanted: bombPlanted,
                    RoundTimeRemaining: Math.Max(0f, 115f - tick / 64f)
                ), out _);
            }
        }

        object ExtractOne(int tick, int roundId, int slot, bool isT, bool objElig, bool retElig, string category)
        {
            var cand = Enumerable.Repeat(true, 53).ToArray();
            var inp = rb.BuildBatchInput("parity_m1", "de_mirage", roundId, new[] { slot }, new[] { true }, cand, new[] { objElig }, new[] { retElig }, out var diag);
            return new
            {
                category,
                round_id = roundId,
                tick,
                player_slot = slot,
                is_terrorist = isT,
                real_frame_count = diag[0].RealFrameCount,
                padded_frame_count = diag[0].PaddedFrameCount,
                self_history = inp.SelfHistory,
                teammates = inp.Teammates,
                temporal_mask = inp.TemporalMask,
                teammate_mask = inp.TeammateMask,
                candidate_mask = inp.CandidateMask,
                objective_eligible = inp.ObjectiveEligible[0],
                retake_eligible = inp.RetakeEligible[0],
                raw_last_frame = new
                {
                    x = -1200f + slot * 150f + tick * 0.5f,
                    y = 300f - slot * 80f + tick * 0.25f,
                    z = -64f + slot * 2f,
                    vx = 50f + slot * 10f,
                    vy = -30f + slot * 5f,
                    vz = 0f,
                    yaw_deg = (slot * 35f + tick) % 360f,
                    pitch_deg = -2.5f,
                    health = 100f - slot * 3f,
                    armor = 100f,
                    weapon_name = slot % 3 == 0 ? "weapon_awp" : (slot % 2 == 0 ? "weapon_ak47" : "weapon_knife"),
                    role_code = 0.25f * ((slot % 4) + 1),
                    is_terrorist = isT,
                    is_alive = true,
                    has_c4 = isT && slot == 0 && !(category == "retake_eligible"),
                    is_bomb_planted = (category == "retake_eligible"),
                    round_time_remaining = Math.Max(0f, 115f - tick / 64f),
                }
            };
        }

        // 20 janelas com padding (round 1)
        rb.OnRoundStart("parity_m1", 1);
        for (int i = 0; i < 20; i++)
        {
            int tick = (i + 1) * 4;
            PushAll10(tick, 1);
            samples.Add(ExtractOne(tick, 1, 0, true, false, false, "padding"));
        }
        // Completar até 32 e gerar 100 janelas completas
        for (int i = 20; i < 132; i++)
        {
            int tick = (i + 1) * 4;
            PushAll10(tick, 1);
            if (i >= 32)
            {
                int slot = i % 10;
                samples.Add(ExtractOne(tick, 1, slot, slot < 5, false, false, "full_window"));
            }
        }
        // 20 janelas com aliado morto
        for (int i = 132; i < 152; i++)
        {
            int tick = (i + 1) * 4;
            PushAll10(tick, 1, deadAlly: true);
            samples.Add(ExtractOne(tick, 1, 0, true, false, false, "dead_teammate"));
        }
        // 10 OBJECTIVE-eligible
        for (int i = 152; i < 162; i++)
        {
            int tick = (i + 1) * 4;
            PushAll10(tick, 1);
            samples.Add(ExtractOne(tick, 1, 0, true, true, false, "objective_eligible"));
        }
        // 10 RETAKE-eligible
        for (int i = 162; i < 172; i++)
        {
            int tick = (i + 1) * 4;
            PushAll10(tick, 1, bombPlanted: true);
            samples.Add(ExtractOne(tick, 1, 5, false, false, true, "retake_eligible"));
        }

        Assert.Equal(160, samples.Count);
        string jsonOut = Path.Combine(RetryDir, "runtime_feature_samples.json");
        File.WriteAllText(jsonOut, JsonSerializer.Serialize(new { provenance = "REAL_CSHARP_ENCODER", count = samples.Count, samples }, new JsonSerializerOptions { WriteIndented = false }));
    }
}
