using System;
using System.Collections.Concurrent;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace CsBotManager;

public sealed record PositioningShadowTelemetryRecord(
    string timestamp,
    string map,
    string match_id,
    int round_id,
    int tick,
    string player_slot,
    string team,
    string model_hash,
    string contract_version,
    bool input_valid,
    bool inference_success,
    double latency_ms,
    string utility_state,
    string neural_state,
    string utility_sector,
    string neural_sector,
    string utility_spot,
    string neural_spot,
    string neural_transition,
    string neural_exit_trigger,
    float[] confidence_by_head,
    bool objective_eligible,
    bool retake_eligible,
    bool save_fallback_active,
    string fallback_reason,
    int ring_buffer_count = 0,
    int real_frame_count = 0,
    int padded_frame_count = 0,
    double effective_history_hz = 0.0,
    int self_history_nonzero_count = 0,
    int teammate_history_nonzero_count = 0,
    double temporal_variance = 0.0,
    string buffer_reset_reason = "NONE",
    string feature_contract_version = PositioningFeatureContract.FeatureContractVersion,
    double warmup_duration_ms = 0.0,
    long team_idx = 2,
    long role_idx = 0,
    long stage_idx = 0,
    string mapping_source = "AUTHORITATIVE",
    bool fallback_mapping_used = false,
    string utility_destination = "UNKNOWN",
    string utility_plan_site = "NONE",
    string utility_role = "UNKNOWN",
    int utility_decision_tick = 0,
    string utility_decision_source = "NONE",
    bool utility_decision_available = false
);

public sealed record UtilityPositioningDecision
{
    public string UtilityState { get; init; } = "UNKNOWN";
    public string UtilitySector { get; init; } = "UNKNOWN";
    public string UtilitySpot { get; init; } = "UNKNOWN";
    public string UtilityDestination { get; init; } = "UNKNOWN";
    public string UtilityPlanSite { get; init; } = "NONE";
    public string UtilityRole { get; init; } = "UNKNOWN";
    public int UtilityDecisionTick { get; init; }
    public string UtilityDecisionSource { get; init; } = "NONE";
    public bool UtilityDecisionAvailable { get; init; }
}

public sealed class PositioningShadowTelemetryLogger : IDisposable
{
    private readonly ConcurrentQueue<string> _queue = new();
    private readonly string _outputPath;
    private readonly CancellationTokenSource _cts = new();
    private readonly Task _writerTask;
    private long _writtenCount;
    private bool _disposed;

    public long WrittenCount => Interlocked.Read(ref _writtenCount);
    public string OutputPath => _outputPath;

    public PositioningShadowTelemetryLogger(string outputPath)
    {
        _outputPath = outputPath;
        string? dir = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);
        _writerTask = Task.Run(DrainLoopAsync);
    }

    public void Enqueue(PositioningShadowTelemetryRecord record)
    {
        if (_disposed) return;
        if (_queue.Count > 2048) return; // bounded non-blocking
        string json = JsonSerializer.Serialize(record);
        _queue.Enqueue(json);
    }

    private async Task DrainLoopAsync()
    {
        try
        {
            await using var sw = new StreamWriter(_outputPath, append: true);
            while (!_cts.IsCancellationRequested || !_queue.IsEmpty)
            {
                bool any = false;
                while (_queue.TryDequeue(out string? line))
                {
                    await sw.WriteLineAsync(line);
                    Interlocked.Increment(ref _writtenCount);
                    any = true;
                }
                if (any)
                {
                    await sw.FlushAsync();
                }
                else
                {
                    await Task.Delay(25, _cts.Token);
                }
            }
        }
        catch (OperationCanceledException)
        {
            // Normal shutdown
        }
        catch
        {
            // Telemetria nunca pode derrubar o servidor
        }
    }

    public void FlushSync()
    {
        int spins = 0;
        while (!_queue.IsEmpty && spins < 40)
        {
            Thread.Sleep(15);
            spins++;
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        FlushSync();
        _cts.Cancel();
        try { _writerTask.Wait(1000); } catch { }
        _cts.Dispose();
    }
}
