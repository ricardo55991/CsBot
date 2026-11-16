using System;
using System.Collections.Generic;
using System.Linq;

namespace CsBotManager;

public enum PositioningFeatureIndex
{
    PosX = 0,
    PosY = 1,
    PosZ = 2,
    VelX = 3,
    VelY = 4,
    VelZ = 5,
    YawCos = 6,
    YawSin = 7,
    PitchNorm = 8,
    HealthNorm = 9,
    ArmorNorm = 10,
    WeaponCategory = 11,
    RoleCode = 12,
    IsTerrorist = 13,
    IsAlive = 14,
    HasC4 = 15,
    IsBombPlanted = 16,
    RoundTimeRemainingNorm = 17
}

public sealed record PositioningFeatureSpec(
    int FeatureIndex,
    string FeatureName,
    string Source,
    string Normalization,
    float MinValid,
    float MaxValid,
    string MissingBehavior
);

public readonly record struct PositioningPlayerObservation(
    int Tick,
    int RoundId,
    int PlayerSlot,
    bool IsTerrorist,
    bool IsAlive,
    float X,
    float Y,
    float Z,
    float Vx,
    float Vy,
    float Vz,
    float YawDeg,
    float PitchDeg,
    float Health,
    float Armor,
    string WeaponName,
    float RoleCode,
    bool HasC4,
    bool IsBombPlanted,
    float RoundTimeRemaining
);

public sealed class PositioningWindowDiagnostics
{
    public int PlayerSlot { get; init; }
    public int RingBufferCount { get; init; }
    public int RealFrameCount { get; init; }
    public int PaddedFrameCount { get; init; }
    public double EffectiveHistoryHz { get; init; }
    public int SelfHistoryNonZeroCount { get; init; }
    public int TeammateHistoryNonZeroCount { get; init; }
    public double TemporalVariance { get; init; }
    public string BufferResetReason { get; init; } = "NONE";
    public int CrossRoundWindows { get; init; }
    public int CrossPlayerWindows { get; init; }
    public int InvalidTeammateMappings { get; init; }
}

public static class PositioningFeatureContract
{
    public const string FeatureContractVersion = "positioning_feature_contract_18ch_v1";
    public const double ExpectedCollectionHz = 16.0;
    public const int CollectionTickInterval = 4; // 64 / 4 = 16 Hz

    public static readonly PositioningFeatureSpec[] CanonicalFeatures =
    {
        new(0,  "pos_x",                    "pawn.AbsOrigin.X",     "clip(x / 4096.0, -1.5, 1.5)",      -1.5f, 1.5f, "0.0 if dead/missing"),
        new(1,  "pos_y",                    "pawn.AbsOrigin.Y",     "clip(y / 4096.0, -1.5, 1.5)",      -1.5f, 1.5f, "0.0 if dead/missing"),
        new(2,  "pos_z",                    "pawn.AbsOrigin.Z",     "clip(z / 1024.0, -1.5, 1.5)",      -1.5f, 1.5f, "0.0 if dead/missing"),
        new(3,  "vel_x",                    "pawn.AbsVelocity.X",   "clip(vx / 250.0, -1.5, 1.5)",      -1.5f, 1.5f, "0.0 if dead/missing"),
        new(4,  "vel_y",                    "pawn.AbsVelocity.Y",   "clip(vy / 250.0, -1.5, 1.5)",      -1.5f, 1.5f, "0.0 if dead/missing"),
        new(5,  "vel_z",                    "pawn.AbsVelocity.Z",   "clip(vz / 250.0, -1.5, 1.5)",      -1.5f, 1.5f, "0.0 if dead/missing"),
        new(6,  "yaw_cos",                  "pawn.EyeAngles.Y",     "cos(yaw_deg * pi / 180.0)",        -1.0f, 1.0f, "0.0 if dead/missing"),
        new(7,  "yaw_sin",                  "pawn.EyeAngles.Y",     "sin(yaw_deg * pi / 180.0)",        -1.0f, 1.0f, "0.0 if dead/missing"),
        new(8,  "pitch_norm",               "pawn.EyeAngles.X",     "clip(pitch_deg / 90.0, -1.0, 1.0)",-1.0f, 1.0f, "0.0 if dead/missing"),
        new(9,  "health_norm",              "pawn.Health",          "clip(health / 100.0, 0.0, 1.0)",    0.0f, 1.0f, "0.0 if dead/missing"),
        new(10, "armor_norm",               "pawn.ArmorValue",      "clip(armor / 100.0, 0.0, 1.0)",     0.0f, 1.0f, "0.0 if dead/missing"),
        new(11, "weapon_category",          "ActiveWeapon",         "EncodeWeaponCategory(weapon)",      0.0f, 1.0f, "0.0 if dead/empty"),
        new(12, "role_code",                "RoleManager",          "clip(role_code, 0.25, 1.0)",        0.0f, 1.0f, "0.0 if dead/missing"),
        new(13, "is_terrorist",             "player.Team",          "1.0 if T else 0.0",                 0.0f, 1.0f, "0.0 if CT"),
        new(14, "is_alive",                 "player.PawnIsAlive",   "1.0 if alive else 0.0",             0.0f, 1.0f, "0.0 if dead"),
        new(15, "has_c4",                   "WeaponServices/C4",    "1.0 if has_c4 else 0.0",            0.0f, 1.0f, "0.0 if dead/no C4"),
        new(16, "is_bomb_planted",          "Plugin._isBombPlanted","1.0 if planted else 0.0",           0.0f, 1.0f, "0.0 if not planted"),
        new(17, "round_time_remaining_norm","RoundClock",           "clip(rt / 115.0, 0.0, 1.0)",        0.0f, 1.0f, "0.0 if <= 0"),
    };

    public static float EncodeWeaponCategory(string? weaponName)
    {
        if (string.IsNullOrEmpty(weaponName)) return 0.0f;
        string w = weaponName.ToLowerInvariant();
        if (w.Contains("knife") || w.Contains("bayonet")) return 0.2f;
        if (w.Contains("awp") || w.Contains("ssg08")) return 1.0f;
        if (w.Contains("ak47") || w.Contains("m4a1") || w.Contains("galilar") ||
            w.Contains("famas") || w.Contains("aug") || w.Contains("sg556")) return 0.8f;
        if (w.Contains("mac10") || w.Contains("mp9") || w.Contains("mp7") ||
            w.Contains("ump45") || w.Contains("p90")) return 0.6f;
        return 0.4f;
    }

    public static bool TryEncodeStandardizedPlayerRow(in PositioningPlayerObservation obs, Span<float> dst)
    {
        if (dst.Length < PositioningTransformerContract.FeatureCount)
        {
            return false;
        }

        if (float.IsNaN(obs.X) || float.IsInfinity(obs.X) ||
            float.IsNaN(obs.Y) || float.IsInfinity(obs.Y) ||
            float.IsNaN(obs.Z) || float.IsInfinity(obs.Z) ||
            float.IsNaN(obs.Vx) || float.IsInfinity(obs.Vx) ||
            float.IsNaN(obs.Vy) || float.IsInfinity(obs.Vy) ||
            float.IsNaN(obs.Vz) || float.IsInfinity(obs.Vz) ||
            float.IsNaN(obs.YawDeg) || float.IsInfinity(obs.YawDeg) ||
            float.IsNaN(obs.PitchDeg) || float.IsInfinity(obs.PitchDeg) ||
            float.IsNaN(obs.Health) || float.IsInfinity(obs.Health) ||
            float.IsNaN(obs.Armor) || float.IsInfinity(obs.Armor) ||
            float.IsNaN(obs.RoleCode) || float.IsInfinity(obs.RoleCode) ||
            float.IsNaN(obs.RoundTimeRemaining) || float.IsInfinity(obs.RoundTimeRemaining))
        {
            return false;
        }

        dst.Slice(0, PositioningTransformerContract.FeatureCount).Clear();
        dst[13] = obs.IsTerrorist ? 1.0f : 0.0f;
        dst[14] = obs.IsAlive ? 1.0f : 0.0f;
        dst[16] = obs.IsBombPlanted ? 1.0f : 0.0f;
        dst[17] = Math.Clamp(obs.RoundTimeRemaining / 115.0f, 0.0f, 1.0f);

        if (!obs.IsAlive)
        {
            return true;
        }

        dst[0] = Math.Clamp(obs.X / 4096.0f, -1.5f, 1.5f);
        dst[1] = Math.Clamp(obs.Y / 4096.0f, -1.5f, 1.5f);
        dst[2] = Math.Clamp(obs.Z / 1024.0f, -1.5f, 1.5f);
        dst[3] = Math.Clamp(obs.Vx / 250.0f, -1.5f, 1.5f);
        dst[4] = Math.Clamp(obs.Vy / 250.0f, -1.5f, 1.5f);
        dst[5] = Math.Clamp(obs.Vz / 250.0f, -1.5f, 1.5f);

        float yawRad = obs.YawDeg * (MathF.PI / 180.0f);
        dst[6] = MathF.Cos(yawRad);
        dst[7] = MathF.Sin(yawRad);
        dst[8] = Math.Clamp(obs.PitchDeg / 90.0f, -1.0f, 1.0f);
        dst[9] = Math.Clamp(obs.Health / 100.0f, 0.0f, 1.0f);
        dst[10] = Math.Clamp(obs.Armor / 100.0f, 0.0f, 1.0f);
        dst[11] = EncodeWeaponCategory(obs.WeaponName);
        dst[12] = Math.Clamp(obs.RoleCode, 0.25f, 1.0f);
        dst[15] = obs.HasC4 ? 1.0f : 0.0f;

        return true;
    }
}

public sealed class PositioningTemporalRingBuffer
{
    private sealed class SlotFrame
    {
        public int Tick { get; init; }
        public int RoundId { get; init; }
        public int PlayerSlot { get; init; }
        public bool IsTerrorist { get; init; }
        public bool IsAlive { get; init; }
        public float[] Features { get; init; } = new float[PositioningTransformerContract.FeatureCount];
    }

    private sealed class PlayerSlotBuffer
    {
        public string MatchId { get; set; } = string.Empty;
        public int RoundId { get; set; } = -1;
        public int PlayerSlot { get; set; }
        public bool IsTerrorist { get; set; }
        public int LastTick { get; set; } = int.MinValue;
        public List<SlotFrame> Frames { get; } = new(PositioningTransformerContract.SequenceLength + 1);
    }

    private readonly Dictionary<int, PlayerSlotBuffer> _buffers = new();
    private string _activeMatchId = string.Empty;
    private int _activeRoundId = -1;
    private string _lastResetReason = "INITIAL";

    public string LastResetReason => _lastResetReason;
    public int ActiveRingBufferCount => _buffers.Count;

    public void ResetAll(string reason)
    {
        _buffers.Clear();
        _activeRoundId = -1;
        _lastResetReason = reason;
    }

    public void OnRoundStart(string matchId, int roundId)
    {
        _activeMatchId = matchId;
        _activeRoundId = roundId;
        _buffers.Clear();
        _lastResetReason = "ROUND_START";
    }

    public void RemoveSlot(int playerSlot, string reason = "DISCONNECT_OR_REUSE")
    {
        if (_buffers.Remove(playerSlot))
        {
            _lastResetReason = reason;
        }
    }

    public bool TryPushObservation(string matchId, int currentServerTick, in PositioningPlayerObservation obs, out string rejectReason)
    {
        if (obs.Tick > currentServerTick)
        {
            rejectReason = "FUTURE_FRAME_REJECTED";
            return false;
        }

        if (_activeMatchId != matchId || _activeRoundId != obs.RoundId)
        {
            _activeMatchId = matchId;
            _activeRoundId = obs.RoundId;
            _buffers.Clear();
            _lastResetReason = "ROUND_BOUNDARY_RESET";
        }

        var encoded = new float[PositioningTransformerContract.FeatureCount];
        if (!PositioningFeatureContract.TryEncodeStandardizedPlayerRow(obs, encoded))
        {
            rejectReason = "NAN_OR_INF_FEATURE_REJECTED";
            return false;
        }

        if (!_buffers.TryGetValue(obs.PlayerSlot, out var buf))
        {
            buf = new PlayerSlotBuffer
            {
                MatchId = matchId,
                RoundId = obs.RoundId,
                PlayerSlot = obs.PlayerSlot,
                IsTerrorist = obs.IsTerrorist,
            };
            _buffers[obs.PlayerSlot] = buf;
        }
        else if (buf.IsTerrorist != obs.IsTerrorist || buf.RoundId != obs.RoundId || buf.MatchId != matchId)
        {
            buf.Frames.Clear();
            buf.MatchId = matchId;
            buf.RoundId = obs.RoundId;
            buf.IsTerrorist = obs.IsTerrorist;
            buf.LastTick = int.MinValue;
            _lastResetReason = "SLOT_REUSE_OR_TEAM_CHANGE";
        }

        if (obs.Tick <= buf.LastTick)
        {
            rejectReason = "NON_INCREASING_TICK_REJECTED";
            return false;
        }

        buf.LastTick = obs.Tick;
        if (buf.Frames.Count >= PositioningTransformerContract.SequenceLength)
        {
            buf.Frames.RemoveAt(0);
        }
        buf.Frames.Add(new SlotFrame
        {
            Tick = obs.Tick,
            RoundId = obs.RoundId,
            PlayerSlot = obs.PlayerSlot,
            IsTerrorist = obs.IsTerrorist,
            IsAlive = obs.IsAlive,
            Features = encoded,
        });

        rejectReason = string.Empty;
        return true;
    }

    public PositioningShadowInferenceInput BuildBatchInput(
        string matchId,
        string mapName,
        int roundId,
        IReadOnlyList<int> targetSlots,
        IReadOnlyList<bool> targetAlive,
        bool[] candidateMask,
        bool[] objectiveEligible,
        bool[] retakeEligible,
        out PositioningWindowDiagnostics[] diagnostics,
        long[]? teamIdx = null,
        long[]? roleIdx = null,
        long[]? stageIdx = null,
        int contextFallbackCount = 0)
    {
        int b = targetSlots.Count;
        const int T = PositioningTransformerContract.SequenceLength;
        const int F = PositioningTransformerContract.FeatureCount;
        const int M = PositioningTransformerContract.TeammateSlots;

        var selfHistory = new float[b * T * F];
        var teammates = new float[b * T * M * F];
        var temporalMask = new float[b * T];
        var teammateMask = new float[b * T * M];
        diagnostics = new PositioningWindowDiagnostics[b];

        for (int bi = 0; bi < b; bi++)
        {
            int selfSlot = targetSlots[bi];
            if (!_buffers.TryGetValue(selfSlot, out var selfBuf) ||
                selfBuf.RoundId != roundId ||
                selfBuf.MatchId != matchId ||
                selfBuf.Frames.Count == 0)
            {
                diagnostics[bi] = new PositioningWindowDiagnostics
                {
                    PlayerSlot = selfSlot,
                    RingBufferCount = _buffers.Count,
                    RealFrameCount = 0,
                    PaddedFrameCount = T,
                    EffectiveHistoryHz = 0.0,
                    SelfHistoryNonZeroCount = 0,
                    TeammateHistoryNonZeroCount = 0,
                    TemporalVariance = 0.0,
                    BufferResetReason = _lastResetReason,
                };
                continue;
            }

            int k = Math.Min(T, selfBuf.Frames.Count);
            int pad = T - k;

            // Selecionar até 4 aliados reais do mesmo time, ordenados deterministicamente por slot, excluindo self
            var alliedSlots = _buffers.Values
                .Where(x => x.MatchId == matchId &&
                            x.RoundId == roundId &&
                            x.IsTerrorist == selfBuf.IsTerrorist &&
                            x.PlayerSlot != selfSlot)
                .Select(x => x.PlayerSlot)
                .OrderBy(s => s)
                .Take(M)
                .ToList();

            int crossRound = 0;
            int crossPlayer = 0;
            int invalidTm = 0;
            int selfNonZero = 0;
            int tmNonZero = 0;

            double sumX = 0.0;
            double sumX2 = 0.0;
            long deltaTicksSum = 0;
            int deltaCount = 0;

            for (int i = 0; i < k; i++)
            {
                int tDst = pad + i;
                var frame = selfBuf.Frames[selfBuf.Frames.Count - k + i];
                if (frame.RoundId != roundId) crossRound++;
                if (frame.PlayerSlot != selfSlot) crossPlayer++;

                temporalMask[bi * T + tDst] = 1.0f;
                int selfOffset = (bi * T + tDst) * F;
                Array.Copy(frame.Features, 0, selfHistory, selfOffset, F);

                for (int c = 0; c < F; c++)
                {
                    if (MathF.Abs(frame.Features[c]) > 1e-7f) selfNonZero++;
                }

                double px = frame.Features[0];
                sumX += px;
                sumX2 += px * px;
                if (i > 0)
                {
                    int prevTick = selfBuf.Frames[selfBuf.Frames.Count - k + i - 1].Tick;
                    int dt = frame.Tick - prevTick;
                    if (dt > 0)
                    {
                        deltaTicksSum += dt;
                        deltaCount++;
                    }
                }

                for (int j = 0; j < alliedSlots.Count; j++)
                {
                    int allySlot = alliedSlots[j];
                    if (!_buffers.TryGetValue(allySlot, out var allyBuf) ||
                        allyBuf.IsTerrorist != selfBuf.IsTerrorist ||
                        allyBuf.PlayerSlot == selfSlot)
                    {
                        invalidTm++;
                        continue;
                    }

                    // Frame mais recente do aliado com tick <= frame.Tick no mesmo round
                    SlotFrame? matched = null;
                    for (int af = allyBuf.Frames.Count - 1; af >= 0; af--)
                    {
                        var cand = allyBuf.Frames[af];
                        if (cand.RoundId == roundId && cand.Tick <= frame.Tick)
                        {
                            matched = cand;
                            break;
                        }
                    }

                    if (matched != null && matched.IsAlive)
                    {
                        teammateMask[(bi * T + tDst) * M + j] = 1.0f;
                        int tmOffset = ((bi * T + tDst) * M + j) * F;
                        Array.Copy(matched.Features, 0, teammates, tmOffset, F);
                        for (int c = 0; c < F; c++)
                        {
                            if (MathF.Abs(matched.Features[c]) > 1e-7f) tmNonZero++;
                        }
                    }
                }
            }

            double effHz = deltaCount > 0 ? 64.0 / (deltaTicksSum / (double)deltaCount) : 0.0;
            double meanX = k > 0 ? sumX / k : 0.0;
            double variance = k > 1 ? Math.Max(0.0, (sumX2 / k) - meanX * meanX) : 0.0;

            diagnostics[bi] = new PositioningWindowDiagnostics
            {
                PlayerSlot = selfSlot,
                RingBufferCount = _buffers.Count,
                RealFrameCount = k,
                PaddedFrameCount = pad,
                EffectiveHistoryHz = Math.Round(effHz, 3),
                SelfHistoryNonZeroCount = selfNonZero,
                TeammateHistoryNonZeroCount = tmNonZero,
                TemporalVariance = Math.Round(variance, 8),
                BufferResetReason = _lastResetReason,
                CrossRoundWindows = crossRound,
                CrossPlayerWindows = crossPlayer,
                InvalidTeammateMappings = invalidTm,
            };
        }

        return new PositioningShadowInferenceInput
        {
            BatchSize = b,
            MapName = mapName,
            RoundId = roundId,
            HasRoundBoundaryCrossing = false,
            SelfHistory = selfHistory,
            Teammates = teammates,
            TemporalMask = temporalMask,
            TeammateMask = teammateMask,
            CandidateMask = candidateMask,
            ObjectiveEligible = objectiveEligible,
            RetakeEligible = retakeEligible,
            PlayerAlive = targetAlive.ToArray(),
            TeamIdx = teamIdx ?? Array.Empty<long>(),
            RoleIdx = roleIdx ?? Array.Empty<long>(),
            StageIdx = stageIdx ?? Array.Empty<long>(),
            ContextFallbackCount = contextFallbackCount,
        };
    }
}
