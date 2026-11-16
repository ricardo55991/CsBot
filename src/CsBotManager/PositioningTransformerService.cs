using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Threading;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;

namespace CsBotManager;

public sealed record WarmupBatchMetric(
    int BatchSize,
    double WarmupDurationMs,
    bool Success,
    bool OutputBoundsValid,
    long AllocatedBytes,
    string Exception
);

public sealed class PositioningPerformanceSnapshot
{
    public long TotalInferences { get; init; }
    public long SuccessfulInferences { get; init; }
    public long FallbackCount { get; init; }
    public long DroppedRequests { get; init; }
    public long TimeoutCount { get; init; }
    public long FailureCount { get; init; }
    public long BufferReuseCount { get; init; }
    public int ModelLoadCount { get; init; }
    public double ModelLoadTimeMs { get; init; }
    public double P50Ms { get; init; }
    public double P95Ms { get; init; }
    public double P99Ms { get; init; }
    public double MeanMs { get; init; }
    public double ThroughputSeqPerSec { get; init; }
}

public sealed class PositioningRawParityOutputs
{
    public float[] FinalStateLogits { get; init; } = Array.Empty<float>();
    public long[] FinalStateId { get; init; } = Array.Empty<long>();
    public float[] SectorTransitionLogits { get; init; } = Array.Empty<float>();
    public long[] SectorTransitionId { get; init; } = Array.Empty<long>();
    public float[] NextSectorLogits { get; init; } = Array.Empty<float>();
    public long[] NextSectorId { get; init; } = Array.Empty<long>();
    public float[] SpotLogits { get; init; } = Array.Empty<float>();
    public long[] SelectedSpotId { get; init; } = Array.Empty<long>();
    public float[] TransitionLogits { get; init; } = Array.Empty<float>();
    public long[] TransitionId { get; init; } = Array.Empty<long>();
    public float[] ExitTriggerLogits { get; init; } = Array.Empty<float>();
    public long[] ExitTriggerId { get; init; } = Array.Empty<long>();
    public float[] ConfidenceByHead { get; init; } = Array.Empty<float>();
}

public sealed class PositioningTransformerService : IDisposable
{
    private readonly SemaphoreSlim _sessionGate = new(1, 1);
    private readonly object _metricsLock = new();
    private readonly List<double> _latenciesMs = new(4096);
    private readonly bool[] _supervisedSpotMask;

    private InferenceSession? _session;
    private string _loadedModelPath = string.Empty;
    private string _loadedModelSha256 = string.Empty;
    private int _modelLoadCount;
    private double _modelLoadTimeMs;
    private int _pendingRequests;
    private bool _disposed;

    // Buffers reutilizáveis pré-alocados (sem alocar a cada inferência)
    private int _bufferBatchCapacity;
    private float[] _selfBuf = Array.Empty<float>();
    private float[] _tmBuf = Array.Empty<float>();
    private float[] _tmaskBuf = Array.Empty<float>();
    private float[] _tmmaskBuf = Array.Empty<float>();
    private bool[] _candBuf = Array.Empty<bool>();
    private bool[] _objBuf = Array.Empty<bool>();
    private bool[] _retBuf = Array.Empty<bool>();
    private long[] _teamBuf = Array.Empty<long>();
    private long[] _roleBuf = Array.Empty<long>();
    private long[] _stageBuf = Array.Empty<long>();
    private bool _supportsContextualInputs;
    private long _bufferReuseCount;

    private long _totalInferences;
    private long _successfulInferences;
    private long _fallbackCount;
    private long _droppedRequests;
    private long _timeoutCount;
    private long _failureCount;

    public int InferenceTimeoutMs { get; set; } = PositioningTransformerContract.DefaultInferenceTimeoutMs;
    public int MaxPendingRequests { get; set; } = PositioningTransformerContract.DefaultMaxPendingRequests;
    public float MinConfidenceThreshold { get; set; } = 0.0f;
    public bool IsModelLoaded => _session != null && !_disposed;
    public bool WarmupStarted { get; private set; }
    public bool WarmupSuccess { get; private set; }
    public double WarmupDurationMs { get; private set; }
    public IReadOnlyList<WarmupBatchMetric> WarmupBatchMetrics => _warmupBatchMetrics;
    private readonly List<WarmupBatchMetric> _warmupBatchMetrics = new(5);
    public bool IsReady => IsModelLoaded && WarmupSuccess;
    public bool SupportsContextualInputs => _supportsContextualInputs;
    public string LoadedModelSha256 => _loadedModelSha256;
    public string LastLoadError { get; private set; } = string.Empty;
    public int ModelLoadCount => _modelLoadCount;

    // Hook opcional apenas para simular atraso determinístico em teste de timeout
    internal Action? TestPreInferenceHook { get; set; }
    internal Action? TestWarmupFailureHook { get; set; }

    public PositioningTransformerService(bool[]? supervisedSpotMask = null)
    {
        if (supervisedSpotMask != null && supervisedSpotMask.Length == PositioningTransformerContract.CandidateSpotCount)
        {
            _supervisedSpotMask = (bool[])supervisedSpotMask.Clone();
        }
        else
        {
            _supervisedSpotMask = (bool[])PositioningTransformerContract.DefaultSupervisedSpotMask.Clone();
        }
        EnsureBufferCapacity(PositioningTransformerContract.DefaultPreferredBatchSize, countReuse: false);
    }

    private void EnsureBufferCapacity(int batchSize, bool countReuse)
    {
        if (batchSize <= _bufferBatchCapacity)
        {
            if (countReuse) Interlocked.Increment(ref _bufferReuseCount);
            return;
        }
        _bufferBatchCapacity = batchSize;
        _selfBuf = new float[batchSize * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.FeatureCount];
        _tmBuf = new float[batchSize * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots * PositioningTransformerContract.FeatureCount];
        _tmaskBuf = new float[batchSize * PositioningTransformerContract.SequenceLength];
        _tmmaskBuf = new float[batchSize * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots];
        _candBuf = new bool[batchSize * PositioningTransformerContract.CandidateSpotCount];
        _objBuf = new bool[batchSize];
        _retBuf = new bool[batchSize];
        _teamBuf = new long[batchSize];
        _roleBuf = new long[batchSize];
        _stageBuf = new long[batchSize];
    }

    public static string ComputeFileSha256(string path)
    {
        using var fs = File.OpenRead(path);
        byte[] hash = SHA256.HashData(fs);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    public bool LoadModel(string modelPath, string? expectedSha256 = null)
    {
        if (_disposed) { LastLoadError = "SERVICE_DISPOSED"; return false; }
        try
        {
            if (string.IsNullOrWhiteSpace(modelPath) || !File.Exists(modelPath))
            {
                LastLoadError = "MODEL_MISSING";
                return false;
            }

            string actualSha = ComputeFileSha256(modelPath);
            if (!string.IsNullOrWhiteSpace(expectedSha256) &&
                !string.Equals(actualSha, expectedSha256.Trim(), StringComparison.OrdinalIgnoreCase))
            {
                LastLoadError = "HASH_MISMATCH";
                return false;
            }

            // Se exatamente o mesmo modelo e hash já está carregado, não recarregar
            if (_session != null &&
                string.Equals(_loadedModelSha256, actualSha, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }

            long t0 = Stopwatch.GetTimestamp();
            var opts = new SessionOptions
            {
                IntraOpNumThreads = 4,
                InterOpNumThreads = 1,
                ExecutionMode = ExecutionMode.ORT_SEQUENTIAL,
                GraphOptimizationLevel = GraphOptimizationLevel.ORT_ENABLE_ALL
            };
            var newSession = new InferenceSession(modelPath, opts);

            // Validar nomes de inputs e outputs do contrato
            var inputKeys = newSession.InputMetadata.Keys.ToHashSet(StringComparer.Ordinal);
            foreach (string reqIn in PositioningTransformerContract.ExpectedInputNames)
            {
                if (!inputKeys.Contains(reqIn))
                {
                    newSession.Dispose();
                    LastLoadError = $"INCOMPATIBLE_CONTRACT_MISSING_INPUT:{reqIn}";
                    return false;
                }
            }
            var outputKeys = newSession.OutputMetadata.Keys.ToHashSet(StringComparer.Ordinal);
            foreach (string reqOut in PositioningTransformerContract.ExpectedOutputNames)
            {
                if (!outputKeys.Contains(reqOut))
                {
                    newSession.Dispose();
                    LastLoadError = $"INCOMPATIBLE_CONTRACT_MISSING_OUTPUT:{reqOut}";
                    return false;
                }
            }

            bool supportsCtx = inputKeys.Contains("team_idx") && inputKeys.Contains("role_idx") && inputKeys.Contains("stage_idx");

            // Warm-up explícito multibatch (1..5) antes de marcar o serviço como Ready
            WarmupStarted = true;
            WarmupSuccess = false;
            WarmupDurationMs = 0.0;
            _warmupBatchMetrics.Clear();
            long wt0 = Stopwatch.GetTimestamp();
            try
            {
                TestWarmupFailureHook?.Invoke();
                for (int wb = 1; wb <= 5; wb++)
                {
                    long bt0 = Stopwatch.GetTimestamp();
                    long alloc0 = GC.GetAllocatedBytesForCurrentThread();
                    var wSelf = new DenseTensor<float>(new float[wb * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.FeatureCount],
                        new[] { wb, PositioningTransformerContract.SequenceLength, PositioningTransformerContract.FeatureCount });
                    var wTm = new DenseTensor<float>(new float[wb * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots * PositioningTransformerContract.FeatureCount],
                        new[] { wb, PositioningTransformerContract.SequenceLength, PositioningTransformerContract.TeammateSlots, PositioningTransformerContract.FeatureCount });
                    var wTMaskArr = new float[wb * PositioningTransformerContract.SequenceLength];
                    Array.Fill(wTMaskArr, 1.0f);
                    var wTMask = new DenseTensor<float>(wTMaskArr, new[] { wb, PositioningTransformerContract.SequenceLength });
                    var wTmMask = new DenseTensor<float>(new float[wb * PositioningTransformerContract.SequenceLength * PositioningTransformerContract.TeammateSlots],
                        new[] { wb, PositioningTransformerContract.SequenceLength, PositioningTransformerContract.TeammateSlots });
                    var wCandArr = new bool[wb * PositioningTransformerContract.CandidateSpotCount];
                    Array.Fill(wCandArr, true);
                    var wCand = new DenseTensor<bool>(wCandArr, new[] { wb, PositioningTransformerContract.CandidateSpotCount });
                    var wObj = new DenseTensor<bool>(new bool[wb], new[] { wb });
                    var wRet = new DenseTensor<bool>(new bool[wb], new[] { wb });

                    var warmupInputs = new List<NamedOnnxValue>(supportsCtx ? 10 : 7)
                    {
                        NamedOnnxValue.CreateFromTensor("self_history", wSelf),
                        NamedOnnxValue.CreateFromTensor("teammates", wTm),
                        NamedOnnxValue.CreateFromTensor("temporal_mask", wTMask),
                        NamedOnnxValue.CreateFromTensor("teammate_mask", wTmMask),
                        NamedOnnxValue.CreateFromTensor("candidate_mask", wCand),
                        NamedOnnxValue.CreateFromTensor("objective_eligible", wObj),
                        NamedOnnxValue.CreateFromTensor("retake_eligible", wRet),
                    };
                    if (supportsCtx)
                    {
                        warmupInputs.Add(NamedOnnxValue.CreateFromTensor("team_idx", new DenseTensor<long>(new long[wb], new[] { wb })));
                        warmupInputs.Add(NamedOnnxValue.CreateFromTensor("role_idx", new DenseTensor<long>(new long[wb], new[] { wb })));
                        warmupInputs.Add(NamedOnnxValue.CreateFromTensor("stage_idx", new DenseTensor<long>(new long[wb], new[] { wb })));
                    }
                    bool boundsValid = true;
                    for (int pass = 0; pass < 3; pass++)
                    {
                        using var warmupResults = newSession.Run(warmupInputs);
                        foreach (var r in warmupResults)
                        {
                            if (r.Name == "final_state_id")
                            {
                                foreach (long v in r.AsTensor<long>())
                                    if (v < 0 || v >= PositioningTransformerContract.NeuralStateCount) boundsValid = false;
                            }
                            else if (r.Name == "selected_spot_id")
                            {
                                foreach (long v in r.AsTensor<long>())
                                    if (v < 0 || v >= PositioningTransformerContract.CandidateSpotCount) boundsValid = false;
                            }
                        }
                    }
                    double bMs = (Stopwatch.GetTimestamp() - bt0) * 1000.0 / Stopwatch.Frequency;
                    long allocDelta = Math.Max(0L, GC.GetAllocatedBytesForCurrentThread() - alloc0);
                    _warmupBatchMetrics.Add(new WarmupBatchMetric(wb, Math.Round(bMs, 4), boundsValid, boundsValid, allocDelta, string.Empty));
                    if (!boundsValid)
                    {
                        throw new InvalidOperationException($"Warmup batch {wb} produced out-of-bounds output.");
                    }
                }
                WarmupDurationMs = (Stopwatch.GetTimestamp() - wt0) * 1000.0 / Stopwatch.Frequency;
                WarmupSuccess = _warmupBatchMetrics.Count == 5 && _warmupBatchMetrics.All(m => m.Success);
            }
            catch (Exception wex)
            {
                WarmupDurationMs = (Stopwatch.GetTimestamp() - wt0) * 1000.0 / Stopwatch.Frequency;
                WarmupSuccess = false;
                if (_warmupBatchMetrics.Count < 5)
                {
                    _warmupBatchMetrics.Add(new WarmupBatchMetric(_warmupBatchMetrics.Count + 1, Math.Round(WarmupDurationMs, 4), false, false, 0, $"{wex.GetType().Name}: {wex.Message}"));
                }
                newSession.Dispose();
                LastLoadError = $"WARMUP_FAILED:{wex.GetType().Name}:{wex.Message}";
                return false;
            }

            _sessionGate.Wait();
            try
            {
                var old = _session;
                _session = newSession;
                old?.Dispose();
                _loadedModelPath = modelPath;
                _loadedModelSha256 = actualSha;
                _supportsContextualInputs = supportsCtx;
                _modelLoadTimeMs = (Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency;
                _modelLoadCount++;
                LastLoadError = string.Empty;
            }
            finally
            {
                _sessionGate.Release();
            }
            return true;
        }
        catch (Exception ex)
        {
            LastLoadError = $"LOAD_EXCEPTION:{ex.GetType().Name}";
            return false;
        }
    }

    public PositioningShadowPrediction[] PredictShadowBatch(PositioningShadowInferenceInput input)
    {
        int b = Math.Max(1, input?.BatchSize ?? 1);
        PositioningShadowPrediction[] MakeFallback(string reason, bool inputValid = false, double latMs = 0.0)
        {
            Interlocked.Increment(ref _fallbackCount);
            var res = new PositioningShadowPrediction[b];
            for (int i = 0; i < b; i++)
            {
                res[i] = new PositioningShadowPrediction
                {
                    InputValid = inputValid,
                    InferenceSuccess = false,
                    SaveFallbackActive = true,
                    FallbackReason = reason,
                    LatencyMs = latMs
                };
            }
            return res;
        }

        if (_disposed || _session == null || !WarmupSuccess)
            return MakeFallback(string.IsNullOrEmpty(LastLoadError) ? "MODEL_NOT_LOADED" : LastLoadError);

        var (isValid, reason) = PositioningInputValidator.Validate(input!);
        if (!isValid)
            return MakeFallback(reason, inputValid: false);

        int pending = Interlocked.Increment(ref _pendingRequests);
        if (pending > MaxPendingRequests)
        {
            Interlocked.Decrement(ref _pendingRequests);
            Interlocked.Increment(ref _droppedRequests);
            return MakeFallback("DROPPED_QUEUE_FULL", inputValid: true);
        }

        bool lockAcquired = false;
        try
        {
            lockAcquired = _sessionGate.Wait(InferenceTimeoutMs);
            if (!lockAcquired)
            {
                Interlocked.Increment(ref _timeoutCount);
                return MakeFallback("INFERENCE_TIMEOUT_LOCK", inputValid: true);
            }
            if (_session == null || _disposed)
                return MakeFallback("MODEL_NOT_LOADED", inputValid: true);

            Interlocked.Increment(ref _totalInferences);
            long t0 = Stopwatch.GetTimestamp();
            TestPreInferenceHook?.Invoke();
            double preElapsed = (Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency;
            if (preElapsed > InferenceTimeoutMs)
            {
                Interlocked.Increment(ref _timeoutCount);
                return MakeFallback("INFERENCE_TIMEOUT", inputValid: true, latMs: preElapsed);
            }

            var raw = ExecuteOnnxSessionLocked(input!);
            double latMs = (Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency;
            if (latMs > InferenceTimeoutMs)
            {
                Interlocked.Increment(ref _timeoutCount);
                return MakeFallback("INFERENCE_TIMEOUT", inputValid: true, latMs: latMs);
            }

            lock (_metricsLock)
            {
                _latenciesMs.Add(latMs);
            }

            var preds = new PositioningShadowPrediction[b];
            for (int i = 0; i < b; i++)
            {
                if (input!.PlayerAlive.Length == b && !input.PlayerAlive[i])
                {
                    Interlocked.Increment(ref _fallbackCount);
                    preds[i] = new PositioningShadowPrediction
                    {
                        InputValid = true,
                        InferenceSuccess = false,
                        SaveFallbackActive = true,
                        FallbackReason = "DEAD_PLAYER_SKIPPED",
                        LatencyMs = latMs
                    };
                    continue;
                }

                long stId = raw.FinalStateId[i];
                long secTrId = raw.SectorTransitionId[i];
                long nextSecId = raw.NextSectorId[i];
                long spotId = raw.SelectedSpotId[i];
                long transId = raw.TransitionId[i];
                long trigId = raw.ExitTriggerId[i];

                // Bounds & invariantes de segurança (Seções 5 e 10)
                if (stId == 6)
                {
                    Interlocked.Increment(ref _fallbackCount);
                    preds[i] = new PositioningShadowPrediction
                    {
                        InputValid = true, InferenceSuccess = false, SaveFallbackActive = true,
                        FallbackReason = "SAVE_FALLBACK_ACTIVE", LatencyMs = latMs
                    };
                    continue;
                }
                if (stId < 0 || stId >= PositioningTransformerContract.NeuralStateCount ||
                    secTrId < 0 || secTrId > 1 ||
                    nextSecId < 0 || nextSecId > 4 ||
                    spotId < 0 || spotId >= PositioningTransformerContract.CandidateSpotCount ||
                    transId < 0 || transId > 6 ||
                    trigId < 0 || trigId > 7)
                {
                    Interlocked.Increment(ref _fallbackCount);
                    preds[i] = new PositioningShadowPrediction
                    {
                        InputValid = true, InferenceSuccess = false, SaveFallbackActive = true,
                        FallbackReason = "OUTPUT_OUT_OF_BOUNDS", LatencyMs = latMs
                    };
                    continue;
                }

                if (stId == (long)PositioningStateKind.OBJECTIVE && !input.ObjectiveEligible[i])
                {
                    Interlocked.Increment(ref _fallbackCount);
                    preds[i] = new PositioningShadowPrediction
                    {
                        InputValid = true, InferenceSuccess = false, SaveFallbackActive = true,
                        FallbackReason = "OBJECTIVE_WITHOUT_ELIGIBILITY_REJECTED", LatencyMs = latMs
                    };
                    continue;
                }
                if (stId == (long)PositioningStateKind.RETAKE && !input.RetakeEligible[i])
                {
                    Interlocked.Increment(ref _fallbackCount);
                    preds[i] = new PositioningShadowPrediction
                    {
                        InputValid = true, InferenceSuccess = false, SaveFallbackActive = true,
                        FallbackReason = "RETAKE_WITHOUT_ELIGIBILITY_REJECTED", LatencyMs = latMs
                    };
                    continue;
                }

                bool spotAllowedInCand = input.CandidateMask[i * PositioningTransformerContract.CandidateSpotCount + (int)spotId];
                if (!spotAllowedInCand || !_supervisedSpotMask[spotId])
                {
                    Interlocked.Increment(ref _fallbackCount);
                    preds[i] = new PositioningShadowPrediction
                    {
                        InputValid = true, InferenceSuccess = false, SaveFallbackActive = true,
                        FallbackReason = "UNSUPPORTED_SPOT_REJECTED", LatencyMs = latMs
                    };
                    continue;
                }

                var conf = new float[6];
                Array.Copy(raw.ConfidenceByHead, i * 6, conf, 0, 6);
                if (conf[0] < MinConfidenceThreshold)
                {
                    Interlocked.Increment(ref _fallbackCount);
                    preds[i] = new PositioningShadowPrediction
                    {
                        InputValid = true, InferenceSuccess = false, SaveFallbackActive = true,
                        ConfidenceByHead = conf, FallbackReason = "LOW_CONFIDENCE_FALLBACK", LatencyMs = latMs
                    };
                    continue;
                }

                Interlocked.Increment(ref _successfulInferences);
                preds[i] = new PositioningShadowPrediction
                {
                    InputValid = true,
                    InferenceSuccess = true,
                    FinalState = (PositioningStateKind)stId,
                    SectorTransition = (SectorTransitionKind)secTrId,
                    NextSector = (NextSectorKind)nextSecId,
                    SelectedSpotId = (int)spotId,
                    Transition = (TransitionKind)transId,
                    ExitTrigger = (ExitTriggerKind)trigId,
                    ConfidenceByHead = conf,
                    SaveFallbackActive = true,
                    FallbackReason = "SAVE_FALLBACK_ACTIVE",
                    LatencyMs = latMs
                };
            }
            return preds;
        }
        catch (Exception ex)
        {
            Interlocked.Increment(ref _failureCount);
            return MakeFallback($"ONNX_RUNTIME_EXCEPTION:{ex.GetType().Name}", inputValid: true);
        }
        finally
        {
            if (lockAcquired) _sessionGate.Release();
            Interlocked.Decrement(ref _pendingRequests);
        }
    }

    public PositioningRawParityOutputs RunRawOutputsForParity(PositioningShadowInferenceInput input)
    {
        if (_disposed || _session == null || !WarmupSuccess)
            throw new InvalidOperationException("ONNX session not loaded.");
        _sessionGate.Wait();
        try
        {
            return ExecuteOnnxSessionLocked(input);
        }
        finally
        {
            _sessionGate.Release();
        }
    }

    private PositioningRawParityOutputs ExecuteOnnxSessionLocked(PositioningShadowInferenceInput input)
    {
        int b = input.BatchSize;
        EnsureBufferCapacity(b, countReuse: true);

        Array.Copy(input.SelfHistory, _selfBuf, input.SelfHistory.Length);
        Array.Copy(input.Teammates, _tmBuf, input.Teammates.Length);
        Array.Copy(input.TemporalMask, _tmaskBuf, input.TemporalMask.Length);
        Array.Copy(input.TeammateMask, _tmmaskBuf, input.TeammateMask.Length);
        Array.Copy(input.CandidateMask, _candBuf, input.CandidateMask.Length);
        Array.Copy(input.ObjectiveEligible, _objBuf, input.ObjectiveEligible.Length);
        Array.Copy(input.RetakeEligible, _retBuf, input.RetakeEligible.Length);

        var inputs = new List<NamedOnnxValue>(_supportsContextualInputs ? 10 : 7)
        {
            NamedOnnxValue.CreateFromTensor("self_history", new DenseTensor<float>(new Memory<float>(_selfBuf, 0, input.SelfHistory.Length), new[] { b, 32, 18 })),
            NamedOnnxValue.CreateFromTensor("teammates", new DenseTensor<float>(new Memory<float>(_tmBuf, 0, input.Teammates.Length), new[] { b, 32, 4, 18 })),
            NamedOnnxValue.CreateFromTensor("temporal_mask", new DenseTensor<float>(new Memory<float>(_tmaskBuf, 0, input.TemporalMask.Length), new[] { b, 32 })),
            NamedOnnxValue.CreateFromTensor("teammate_mask", new DenseTensor<float>(new Memory<float>(_tmmaskBuf, 0, input.TeammateMask.Length), new[] { b, 32, 4 })),
            NamedOnnxValue.CreateFromTensor("candidate_mask", new DenseTensor<bool>(new Memory<bool>(_candBuf, 0, input.CandidateMask.Length), new[] { b, 53 })),
            NamedOnnxValue.CreateFromTensor("objective_eligible", new DenseTensor<bool>(new Memory<bool>(_objBuf, 0, b), new[] { b })),
            NamedOnnxValue.CreateFromTensor("retake_eligible", new DenseTensor<bool>(new Memory<bool>(_retBuf, 0, b), new[] { b }))
        };

        if (_supportsContextualInputs)
        {
            if (input.TeamIdx.Length == b) Array.Copy(input.TeamIdx, _teamBuf, b);
            else Array.Fill(_teamBuf, 2L, 0, b); // Fallback explícito ANY=2

            if (input.RoleIdx.Length == b) Array.Copy(input.RoleIdx, _roleBuf, b);
            else Array.Fill(_roleBuf, 0L, 0, b); // Fallback explícito SUPPORT=0

            if (input.StageIdx.Length == b) Array.Copy(input.StageIdx, _stageBuf, b);
            else Array.Fill(_stageBuf, 0L, 0, b); // Fallback explícito MapControl=0

            inputs.Add(NamedOnnxValue.CreateFromTensor("team_idx", new DenseTensor<long>(new Memory<long>(_teamBuf, 0, b), new[] { b })));
            inputs.Add(NamedOnnxValue.CreateFromTensor("role_idx", new DenseTensor<long>(new Memory<long>(_roleBuf, 0, b), new[] { b })));
            inputs.Add(NamedOnnxValue.CreateFromTensor("stage_idx", new DenseTensor<long>(new Memory<long>(_stageBuf, 0, b), new[] { b })));
        }

        using var results = _session!.Run(inputs);
        float[] finalStateLogits = Array.Empty<float>();
        long[] finalStateId = Array.Empty<long>();
        float[] secTransLogits = Array.Empty<float>();
        long[] secTransId = Array.Empty<long>();
        float[] nextSecLogits = Array.Empty<float>();
        long[] nextSecId = Array.Empty<long>();
        float[] spotLogits = Array.Empty<float>();
        long[] selSpotId = Array.Empty<long>();
        float[] transLogits = Array.Empty<float>();
        long[] transId = Array.Empty<long>();
        float[] exitTrigLogits = Array.Empty<float>();
        long[] exitTrigId = Array.Empty<long>();
        float[] confByHead = Array.Empty<float>();

        foreach (var r in results)
        {
            switch (r.Name)
            {
                case "final_state_logits": finalStateLogits = r.AsTensor<float>().ToArray(); break;
                case "final_state_id": finalStateId = r.AsTensor<long>().ToArray(); break;
                case "sector_transition_logits": secTransLogits = r.AsTensor<float>().ToArray(); break;
                case "sector_transition_id": secTransId = r.AsTensor<long>().ToArray(); break;
                case "next_sector_logits": nextSecLogits = r.AsTensor<float>().ToArray(); break;
                case "next_sector_id": nextSecId = r.AsTensor<long>().ToArray(); break;
                case "spot_logits": spotLogits = r.AsTensor<float>().ToArray(); break;
                case "selected_spot_id": selSpotId = r.AsTensor<long>().ToArray(); break;
                case "transition_logits": transLogits = r.AsTensor<float>().ToArray(); break;
                case "transition_id": transId = r.AsTensor<long>().ToArray(); break;
                case "exit_trigger_logits": exitTrigLogits = r.AsTensor<float>().ToArray(); break;
                case "exit_trigger_id": exitTrigId = r.AsTensor<long>().ToArray(); break;
                case "confidence_by_head": confByHead = r.AsTensor<float>().ToArray(); break;
            }
        }

        return new PositioningRawParityOutputs
        {
            FinalStateLogits = finalStateLogits,
            FinalStateId = finalStateId,
            SectorTransitionLogits = secTransLogits,
            SectorTransitionId = secTransId,
            NextSectorLogits = nextSecLogits,
            NextSectorId = nextSecId,
            SpotLogits = spotLogits,
            SelectedSpotId = selSpotId,
            TransitionLogits = transLogits,
            TransitionId = transId,
            ExitTriggerLogits = exitTrigLogits,
            ExitTriggerId = exitTrigId,
            ConfidenceByHead = confByHead
        };
    }

    public PositioningPerformanceSnapshot GetPerformanceSnapshot()
    {
        double[] sorted;
        lock (_metricsLock)
        {
            sorted = _latenciesMs.OrderBy(x => x).ToArray();
        }
        double Pct(double p)
        {
            if (sorted.Length == 0) return 0.0;
            int idx = Math.Clamp((int)Math.Ceiling(p * sorted.Length) - 1, 0, sorted.Length - 1);
            return sorted[idx];
        }
        double mean = sorted.Length > 0 ? sorted.Average() : 0.0;
        return new PositioningPerformanceSnapshot
        {
            TotalInferences = Interlocked.Read(ref _totalInferences),
            SuccessfulInferences = Interlocked.Read(ref _successfulInferences),
            FallbackCount = Interlocked.Read(ref _fallbackCount),
            DroppedRequests = Interlocked.Read(ref _droppedRequests),
            TimeoutCount = Interlocked.Read(ref _timeoutCount),
            FailureCount = Interlocked.Read(ref _failureCount),
            BufferReuseCount = Interlocked.Read(ref _bufferReuseCount),
            ModelLoadCount = _modelLoadCount,
            ModelLoadTimeMs = Math.Round(_modelLoadTimeMs, 3),
            P50Ms = Math.Round(Pct(0.50), 4),
            P95Ms = Math.Round(Pct(0.95), 4),
            P99Ms = Math.Round(Pct(0.99), 4),
            MeanMs = Math.Round(mean, 4),
            ThroughputSeqPerSec = mean > 0 ? Math.Round(1000.0 / mean, 2) : 0.0
        };
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _sessionGate.Wait();
        try
        {
            _session?.Dispose();
            _session = null;
        }
        finally
        {
            _sessionGate.Release();
            _sessionGate.Dispose();
        }
    }
}
