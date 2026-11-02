using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;

namespace CsBotManager;

public sealed class TrackerMetricsAggregator
{
	public static readonly ConcurrentDictionary<StandstillClassification, int> StandstillByClassification = new ConcurrentDictionary<StandstillClassification, int>();

	public static readonly ConcurrentDictionary<StandstillClassification, int> RecoveryByClassification = new ConcurrentDictionary<StandstillClassification, int>();

	private static int _falseRecoverySuppressedCount = 0;

	private static int _staleObjectivesRejectedCount = 0;

	private static int _retakeSiteMismatchesCount = 0;

	private static int _jumpRequestedCount = 0;

	private static int _jumpExecutedCount = 0;

	private static int _jumpSuppressedAirborneCount = 0;

	private static int _jumpSuppressedCooldownCount = 0;

	private static int _jumpSuppressedContextCount = 0;

	private static int _repeatedJumpSequencesCount = 0;

	public static readonly ConcurrentDictionary<string, int> JumpByReason = new ConcurrentDictionary<string, int>();

	private static int _crossTeamAttemptsCount = 0;

	private static int _repeatedAttemptsSuppressedCount = 0;

	private static readonly ConcurrentDictionary<string, bool> _crossTeamEpisodes = new ConcurrentDictionary<string, bool>();

	private static int _ctFormationsMaterializedCount = 0;

	private static int _ctFormationsInvalidCount = 0;

	public int TotalSamples { get; set; }

	public int AppliedWithProgress { get; set; }

	public int AppliedLowProgress { get; set; }

	public int AppliedNoProgress { get; set; }

	public int AuthorizedHoldApplied { get; set; }

	public int FullStopApplied { get; set; }

	public int BlockedByGeometryOrNavigation { get; set; }

	public int PossibleExternalControllerOverride { get; set; }

	public int RecoveryStarted { get; set; }

	public int RecoverySucceeded { get; set; }

	public int RecoveryEscalatedStage2 { get; set; }

	public int RecoveryEscalatedStage3 { get; set; }

	public int RecoveryFailed { get; set; }

	public float MedianRecoveryTimeMs { get; set; }

	public float MedianRecoveryDisplacement { get; set; }

	public int RepeatedRecoverySameSlot { get; set; }

	public int UnexplainedStateChanges { get; set; }

	public int UniqueOverrideEvents { get; set; }

	public int PersistentOverrideEvents { get; set; }

	public int SamplesAffected { get; set; }

	public int SnapshotAppearances { get; set; }

	public int GeometryBlockDetected { get; set; }

	public int GeometryBlockRecoveryStarted { get; set; }

	public int GeometryBlockRecovered { get; set; }

	public int GeometryBlockFailed { get; set; }

	public int TotalIntegrityEpisodes { get; set; }

	public int TransientEpisodes { get; set; }

	public int PersistentEpisodes { get; set; }

	public int SamplesInEpisodes { get; set; }

	public float MeanEpisodeDurationMs { get; set; }

	public int UniqueC4MismatchEpisodes { get; set; }

	public int TotalMismatchTicks { get; set; }

	public int StaleObjectivesRejected { get; set; }

	public int RetakeSiteMismatches { get; set; }

	public int C4SemanticMismatches { get; set; }

	public int JumpRequested { get; set; }

	public int JumpExecuted { get; set; }

	public int JumpSuppressedAirborne { get; set; }

	public int JumpSuppressedCooldown { get; set; }

	public int JumpSuppressedContext { get; set; }

	public int RepeatedJumpSequences { get; set; }

	public int CrossTeamReplacementAttempts { get; set; }

	public int UniqueCrossTeamReplacementEpisodes { get; set; }

	public int RepeatedAttemptsSuppressed { get; set; }

	public int CtFormationsMaterialized { get; set; }

	public int CtFormationsInvalidFallback { get; set; }

	public static int FalseRecoverySuppressedCount => _falseRecoverySuppressedCount;

	public static int StaleObjectivesRejectedCount => _staleObjectivesRejectedCount;

	public static int JumpRequestedCount => _jumpRequestedCount;

	public static int JumpExecutedCount => _jumpExecutedCount;

	public static int JumpSuppressedAirborneCount => _jumpSuppressedAirborneCount;

	public static int JumpSuppressedCooldownCount => _jumpSuppressedCooldownCount;

	public static int JumpSuppressedContextCount => _jumpSuppressedContextCount;

	public static int RepeatedJumpSequencesCount => _repeatedJumpSequencesCount;

	public static int CrossTeamAttemptsCount => _crossTeamAttemptsCount;

	public static int UniqueCrossTeamEpisodesCount => _crossTeamEpisodes.Count;

	public static int RepeatedAttemptsSuppressedCount => _repeatedAttemptsSuppressedCount;

	public static int CtFormationsMaterializedCount => _ctFormationsMaterializedCount;

	public static int CtFormationsInvalidCount => _ctFormationsInvalidCount;

	public static int RetakeSiteMismatchesCount => _retakeSiteMismatchesCount;

	public static void IncrementStaleObjectivesRejected()
	{
		Interlocked.Increment(ref _staleObjectivesRejectedCount);
	}

	public void RecordJump(int slot, bool executed, bool suppressedAirborne, bool suppressedCooldown, bool suppressedContext, string reason)
	{
		Interlocked.Increment(ref _jumpRequestedCount);
		if (executed)
		{
			Interlocked.Increment(ref _jumpExecutedCount);
			JumpByReason.AddOrUpdate(reason, 1, (string _, int c) => c + 1);
		}
		if (suppressedAirborne)
		{
			Interlocked.Increment(ref _jumpSuppressedAirborneCount);
		}
		if (suppressedCooldown)
		{
			Interlocked.Increment(ref _jumpSuppressedCooldownCount);
		}
		if (suppressedContext)
		{
			Interlocked.Increment(ref _jumpSuppressedContextCount);
		}
	}

	public static void IncrementRepeatedJumpSequences()
	{
		Interlocked.Increment(ref _repeatedJumpSequencesCount);
	}

	public static bool RecordCrossTeamAttempt(string episodeKey)
	{
		Interlocked.Increment(ref _crossTeamAttemptsCount);
		if (_crossTeamEpisodes.TryAdd(episodeKey, value: true))
		{
			return true;
		}
		Interlocked.Increment(ref _repeatedAttemptsSuppressedCount);
		return false;
	}

	public static void RecordCtFormation(bool isValid)
	{
		Interlocked.Increment(ref _ctFormationsMaterializedCount);
		if (!isValid)
		{
			Interlocked.Increment(ref _ctFormationsInvalidCount);
		}
	}

	public static void IncrementRetakeSiteMismatches()
	{
		Interlocked.Increment(ref _retakeSiteMismatchesCount);
	}

	public static void RecordStandstillClassification(StandstillClassification classification, bool recoveryAllowed)
	{
		StandstillByClassification.AddOrUpdate(classification, 1, (StandstillClassification _, int c) => c + 1);
		if (recoveryAllowed)
		{
			RecoveryByClassification.AddOrUpdate(classification, 1, (StandstillClassification _, int c) => c + 1);
		}
		else
		{
			Interlocked.Increment(ref _falseRecoverySuppressedCount);
		}
	}

	public static void ResetClassificationMetrics()
	{
		StandstillByClassification.Clear();
		RecoveryByClassification.Clear();
		Interlocked.Exchange(ref _falseRecoverySuppressedCount, 0);
		Interlocked.Exchange(ref _staleObjectivesRejectedCount, 0);
		Interlocked.Exchange(ref _retakeSiteMismatchesCount, 0);
		Interlocked.Exchange(ref _jumpRequestedCount, 0);
		Interlocked.Exchange(ref _jumpExecutedCount, 0);
		Interlocked.Exchange(ref _jumpSuppressedAirborneCount, 0);
		Interlocked.Exchange(ref _jumpSuppressedCooldownCount, 0);
		Interlocked.Exchange(ref _jumpSuppressedContextCount, 0);
		Interlocked.Exchange(ref _repeatedJumpSequencesCount, 0);
		JumpByReason.Clear();
		Interlocked.Exchange(ref _crossTeamAttemptsCount, 0);
		Interlocked.Exchange(ref _repeatedAttemptsSuppressedCount, 0);
		_crossTeamEpisodes.Clear();
		Interlocked.Exchange(ref _ctFormationsMaterializedCount, 0);
		Interlocked.Exchange(ref _ctFormationsInvalidCount, 0);
	}

	public static string GenerateAggregatedReport(IEnumerable<MovementExecutionSample> samples, BotLocomotionDriver? driver = null)
	{
		List<MovementExecutionSample> list = samples.ToList();
		TrackerMetricsAggregator trackerMetricsAggregator = new TrackerMetricsAggregator
		{
			TotalSamples = list.Count
		};
		foreach (MovementExecutionSample item in list)
		{
			switch (item.PhysicalOutcome)
			{
			case PhysicalExecutionOutcome.AppliedWithProgress:
				trackerMetricsAggregator.AppliedWithProgress++;
				break;
			case PhysicalExecutionOutcome.AppliedLowProgress:
				trackerMetricsAggregator.AppliedLowProgress++;
				break;
			case PhysicalExecutionOutcome.AppliedNoProgress:
				trackerMetricsAggregator.AppliedNoProgress++;
				break;
			case PhysicalExecutionOutcome.AuthorizedHoldApplied:
				trackerMetricsAggregator.AuthorizedHoldApplied++;
				break;
			case PhysicalExecutionOutcome.FullStopApplied:
				trackerMetricsAggregator.FullStopApplied++;
				break;
			case PhysicalExecutionOutcome.BlockedByGeometryOrNavigation:
				trackerMetricsAggregator.BlockedByGeometryOrNavigation++;
				break;
			}
			if (item.StateIntegrity == StateIntegrityOutcome.PossibleExternalControllerOverride)
			{
				trackerMetricsAggregator.PossibleExternalControllerOverride++;
			}
		}
		if (driver != null)
		{
			List<RecoveryAttempt> list2 = driver.AllRecoveryAttempts.ToList();
			trackerMetricsAggregator.RecoveryStarted = list2.Count;
			trackerMetricsAggregator.RecoverySucceeded = list2.Count((RecoveryAttempt r) => r.Recovered && r.Displacement2DAfter >= 15f);
			trackerMetricsAggregator.RecoveryEscalatedStage2 = list2.Count((RecoveryAttempt r) => r.Stage >= 2);
			trackerMetricsAggregator.RecoveryEscalatedStage3 = list2.Count((RecoveryAttempt r) => r.Stage >= 3);
			trackerMetricsAggregator.RecoveryFailed = list2.Count((RecoveryAttempt r) => !r.Recovered);
			List<float> values = (from r in list2
				select r.DurationMs into d
				where d > 0f
				select d).ToList();
			trackerMetricsAggregator.MedianRecoveryTimeMs = ComputeMedian(values);
			List<float> values2 = list2.Select((RecoveryAttempt r) => r.Displacement2DAfter).ToList();
			trackerMetricsAggregator.MedianRecoveryDisplacement = ComputeMedian(values2);
			trackerMetricsAggregator.RepeatedRecoverySameSlot = (from r in list2
				group r by (InternalRoundId: r.InternalRoundId, BotSlot: r.BotSlot)).Count((IGrouping<(long InternalRoundId, int BotSlot), RecoveryAttempt> g) => g.Count() > 1);
			if (driver.ExecutionTracker != null)
			{
				IReadOnlyCollection<IntegrityEpisode> allIntegrityEpisodes = driver.ExecutionTracker.GetAllIntegrityEpisodes();
				trackerMetricsAggregator.TotalIntegrityEpisodes = allIntegrityEpisodes.Count;
				trackerMetricsAggregator.TransientEpisodes = allIntegrityEpisodes.Count((IntegrityEpisode e) => !e.PersistedAcrossTicks);
				trackerMetricsAggregator.PersistentEpisodes = allIntegrityEpisodes.Count((IntegrityEpisode e) => e.PersistedAcrossTicks);
				trackerMetricsAggregator.SamplesInEpisodes = allIntegrityEpisodes.Sum((IntegrityEpisode e) => e.SampleCount);
				trackerMetricsAggregator.MeanEpisodeDurationMs = (allIntegrityEpisodes.Any() ? allIntegrityEpisodes.Average((IntegrityEpisode e) => (e.EndTime - e.StartTime) * 1000f) : 0f);
				trackerMetricsAggregator.UnexplainedStateChanges = (int)driver.ExecutionTracker.UnexplainedStateChangesCount;
				trackerMetricsAggregator.UniqueOverrideEvents = driver.ExecutionTracker.UniqueOverrideEventsCount;
				trackerMetricsAggregator.PersistentOverrideEvents = (int)driver.ExecutionTracker.PersistentOverrideEventsCount;
				trackerMetricsAggregator.SamplesAffected = trackerMetricsAggregator.PossibleExternalControllerOverride;
				trackerMetricsAggregator.SnapshotAppearances = driver.ExecutionTracker.OverrideSnapshotAppearancesCount;
			}
			trackerMetricsAggregator.GeometryBlockDetected = (StandstillByClassification.TryGetValue(StandstillClassification.GeometryBlock, out var value) ? value : 0);
			trackerMetricsAggregator.GeometryBlockRecoveryStarted = (RecoveryByClassification.TryGetValue(StandstillClassification.GeometryBlock, out var value2) ? value2 : 0);
			List<RecoveryAttempt> source = list2.Where((RecoveryAttempt r) => r.TriggerReason.Contains("GeometryBlock", StringComparison.OrdinalIgnoreCase)).ToList();
			if (source.Any())
			{
				trackerMetricsAggregator.GeometryBlockRecovered = source.Count((RecoveryAttempt r) => r.Recovered);
				trackerMetricsAggregator.GeometryBlockFailed = source.Count((RecoveryAttempt r) => !r.Recovered);
			}
			else
			{
				trackerMetricsAggregator.GeometryBlockRecovered = trackerMetricsAggregator.RecoverySucceeded;
				trackerMetricsAggregator.GeometryBlockFailed = trackerMetricsAggregator.RecoveryFailed;
			}
			if (driver.C4MismatchTracker != null)
			{
				trackerMetricsAggregator.UniqueC4MismatchEpisodes = driver.C4MismatchTracker.UniqueC4MismatchEpisodes;
				trackerMetricsAggregator.TotalMismatchTicks = driver.C4MismatchTracker.TotalMismatchTicks;
				trackerMetricsAggregator.C4SemanticMismatches = driver.C4MismatchTracker.SemanticMismatchesCount;
			}
			trackerMetricsAggregator.StaleObjectivesRejected = StaleObjectivesRejectedCount;
			trackerMetricsAggregator.RetakeSiteMismatches = RetakeSiteMismatchesCount;
		}
		StringBuilder stringBuilder = new StringBuilder();
		stringBuilder.AppendLine("### \ud83d\udcc8 Resumo Agregado do MovementExecutionTracker (V4.2.6)");
		stringBuilder.AppendLine("| Métrica | Total | Percentual |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		float num = Math.Max(1, trackerMetricsAggregator.TotalSamples);
		StringBuilder stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder3 = stringBuilder2;
		StringBuilder.AppendInterpolatedStringHandler handler = new StringBuilder.AppendInterpolatedStringHandler(34, 1, stringBuilder2);
		handler.AppendLiteral("| **TotalSamples** | `");
		handler.AppendFormatted(trackerMetricsAggregator.TotalSamples);
		handler.AppendLiteral("` | 100.0% |");
		stringBuilder3.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder4 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(36, 2, stringBuilder2);
		handler.AppendLiteral("| **AppliedWithProgress** | `");
		handler.AppendFormatted(trackerMetricsAggregator.AppliedWithProgress);
		handler.AppendLiteral("` | ");
		handler.AppendFormatted((float)trackerMetricsAggregator.AppliedWithProgress / num * 100f, "F1");
		handler.AppendLiteral("% |");
		stringBuilder4.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder5 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(35, 2, stringBuilder2);
		handler.AppendLiteral("| **AppliedLowProgress** | `");
		handler.AppendFormatted(trackerMetricsAggregator.AppliedLowProgress);
		handler.AppendLiteral("` | ");
		handler.AppendFormatted((float)trackerMetricsAggregator.AppliedLowProgress / num * 100f, "F1");
		handler.AppendLiteral("% |");
		stringBuilder5.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder6 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(34, 2, stringBuilder2);
		handler.AppendLiteral("| **AppliedNoProgress** | `");
		handler.AppendFormatted(trackerMetricsAggregator.AppliedNoProgress);
		handler.AppendLiteral("` | ");
		handler.AppendFormatted((float)trackerMetricsAggregator.AppliedNoProgress / num * 100f, "F1");
		handler.AppendLiteral("% |");
		stringBuilder6.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder7 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(38, 2, stringBuilder2);
		handler.AppendLiteral("| **AuthorizedHoldApplied** | `");
		handler.AppendFormatted(trackerMetricsAggregator.AuthorizedHoldApplied);
		handler.AppendLiteral("` | ");
		handler.AppendFormatted((float)trackerMetricsAggregator.AuthorizedHoldApplied / num * 100f, "F1");
		handler.AppendLiteral("% |");
		stringBuilder7.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder8 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(32, 2, stringBuilder2);
		handler.AppendLiteral("| **FullStopApplied** | `");
		handler.AppendFormatted(trackerMetricsAggregator.FullStopApplied);
		handler.AppendLiteral("` | ");
		handler.AppendFormatted((float)trackerMetricsAggregator.FullStopApplied / num * 100f, "F1");
		handler.AppendLiteral("% |");
		stringBuilder8.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder9 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(46, 2, stringBuilder2);
		handler.AppendLiteral("| **BlockedByGeometryOrNavigation** | `");
		handler.AppendFormatted(trackerMetricsAggregator.BlockedByGeometryOrNavigation);
		handler.AppendLiteral("` | ");
		handler.AppendFormatted((float)trackerMetricsAggregator.BlockedByGeometryOrNavigation / num * 100f, "F1");
		handler.AppendLiteral("% |");
		stringBuilder9.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder10 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(51, 2, stringBuilder2);
		handler.AppendLiteral("| **PossibleExternalControllerOverride** | `");
		handler.AppendFormatted(trackerMetricsAggregator.PossibleExternalControllerOverride);
		handler.AppendLiteral("` | ");
		handler.AppendFormatted((float)trackerMetricsAggregator.PossibleExternalControllerOverride / num * 100f, "F1");
		handler.AppendLiteral("% |");
		stringBuilder10.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83e\uddf1 Auditoria de Bloqueio Geométrico e Ciclo de Vida (V4.2.5)");
		stringBuilder.AppendLine("| Métrica | Valor | Descrição |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder11 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(77, 1, stringBuilder2);
		handler.AppendLiteral("| **GeometryBlockDetected** | `");
		handler.AppendFormatted(trackerMetricsAggregator.GeometryBlockDetected);
		handler.AppendLiteral("` | Total de classificações de GeometryBlock |");
		stringBuilder11.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder12 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(82, 1, stringBuilder2);
		handler.AppendLiteral("| **GeometryBlockRecoveryStarted** | `");
		handler.AppendFormatted(trackerMetricsAggregator.GeometryBlockRecoveryStarted);
		handler.AppendLiteral("` | Quantidade que iniciou recovery físico |");
		stringBuilder12.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder13 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(87, 1, stringBuilder2);
		handler.AppendLiteral("| **GeometryBlockRecovered** | `");
		handler.AppendFormatted(trackerMetricsAggregator.GeometryBlockRecovered);
		handler.AppendLiteral("` | Quantidade que recuperou movimentação com sucesso |");
		stringBuilder13.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder14 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(79, 1, stringBuilder2);
		handler.AppendLiteral("| **GeometryBlockFailed** | `");
		handler.AppendFormatted(trackerMetricsAggregator.GeometryBlockFailed);
		handler.AppendLiteral("` | Falhas definitivas de recuperação geométrica |");
		stringBuilder14.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder15 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(97, 1, stringBuilder2);
		handler.AppendLiteral("| **PhysicalSamplesFinalizedAsBlocked** | `");
		handler.AppendFormatted(trackerMetricsAggregator.BlockedByGeometryOrNavigation);
		handler.AppendLiteral("` | Amostras físicas que finalizaram como bloqueadas |");
		stringBuilder15.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83d\uded1 Auditoria de Classificação de Standstill e Recovery (V4.2.4)");
		stringBuilder.AppendLine("| Classificação | Standstill Detectado | Recovery Permitido | Recovery Suprimido |");
		stringBuilder.AppendLine("| :--- | :--- | :--- | :--- |");
		StandstillClassification[] values3 = Enum.GetValues<StandstillClassification>();
		foreach (StandstillClassification standstillClassification in values3)
		{
			int num3 = (StandstillByClassification.TryGetValue(standstillClassification, out var value3) ? value3 : 0);
			int num4 = (RecoveryByClassification.TryGetValue(standstillClassification, out var value4) ? value4 : 0);
			int value5 = num3 - num4;
			if (num3 > 0)
			{
				stringBuilder2 = stringBuilder;
				StringBuilder stringBuilder16 = stringBuilder2;
				handler = new StringBuilder.AppendInterpolatedStringHandler(15, 4, stringBuilder2);
				handler.AppendLiteral("| `");
				handler.AppendFormatted(standstillClassification);
				handler.AppendLiteral("` | ");
				handler.AppendFormatted(num3);
				handler.AppendLiteral(" | ");
				handler.AppendFormatted(num4);
				handler.AppendLiteral(" | ");
				handler.AppendFormatted(value5);
				handler.AppendLiteral(" |");
				stringBuilder16.AppendLine(ref handler);
			}
		}
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder17 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(49, 1, stringBuilder2);
		handler.AppendLiteral("| **FalseRecoverySuppressedTotal** | - | - | `");
		handler.AppendFormatted(FalseRecoverySuppressedCount);
		handler.AppendLiteral("` |");
		stringBuilder17.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83d\udd04 Auditoria de Recovery por Resultado (V4.2.4)");
		stringBuilder.AppendLine("| Métrica de Recovery | Valor |");
		stringBuilder.AppendLine("| :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder18 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(28, 1, stringBuilder2);
		handler.AppendLiteral("| **RecoveryStarted** | `");
		handler.AppendFormatted(trackerMetricsAggregator.RecoveryStarted);
		handler.AppendLiteral("` |");
		stringBuilder18.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder19 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(30, 1, stringBuilder2);
		handler.AppendLiteral("| **RecoverySucceeded** | `");
		handler.AppendFormatted(trackerMetricsAggregator.RecoverySucceeded);
		handler.AppendLiteral("` |");
		stringBuilder19.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder20 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(36, 1, stringBuilder2);
		handler.AppendLiteral("| **RecoveryEscalatedStage2** | `");
		handler.AppendFormatted(trackerMetricsAggregator.RecoveryEscalatedStage2);
		handler.AppendLiteral("` |");
		stringBuilder20.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder21 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(36, 1, stringBuilder2);
		handler.AppendLiteral("| **RecoveryEscalatedStage3** | `");
		handler.AppendFormatted(trackerMetricsAggregator.RecoveryEscalatedStage3);
		handler.AppendLiteral("` |");
		stringBuilder21.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder22 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(27, 1, stringBuilder2);
		handler.AppendLiteral("| **RecoveryFailed** | `");
		handler.AppendFormatted(trackerMetricsAggregator.RecoveryFailed);
		handler.AppendLiteral("` |");
		stringBuilder22.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder23 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(36, 1, stringBuilder2);
		handler.AppendLiteral("| **MedianRecoveryTimeMs** | `");
		handler.AppendFormatted(trackerMetricsAggregator.MedianRecoveryTimeMs, "F1");
		handler.AppendLiteral(" ms` |");
		stringBuilder23.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder24 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(41, 1, stringBuilder2);
		handler.AppendLiteral("| **MedianRecoveryDisplacement** | `");
		handler.AppendFormatted(trackerMetricsAggregator.MedianRecoveryDisplacement, "F1");
		handler.AppendLiteral(" u` |");
		stringBuilder24.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder25 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(37, 1, stringBuilder2);
		handler.AppendLiteral("| **RepeatedRecoverySameSlot** | `");
		handler.AppendFormatted(trackerMetricsAggregator.RepeatedRecoverySameSlot);
		handler.AppendLiteral("` |");
		stringBuilder25.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83d\udee1\ufe0f Auditoria de Integridade por Episódio (V4.2.5)");
		stringBuilder.AppendLine("| Métrica | Valor | Detalhes |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder26 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(82, 1, stringBuilder2);
		handler.AppendLiteral("| **TotalIntegrityEpisodes** | `");
		handler.AppendFormatted(trackerMetricsAggregator.TotalIntegrityEpisodes);
		handler.AppendLiteral("` | Incidentes reais consolidados de integridade |");
		stringBuilder26.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder27 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(92, 1, stringBuilder2);
		handler.AppendLiteral("| **TransientEpisodes (< 16 ticks)** | `");
		handler.AppendFormatted(trackerMetricsAggregator.TransientEpisodes);
		handler.AppendLiteral("` | Incidentes transitórios rapidamente corrigidos |");
		stringBuilder27.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder28 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(93, 1, stringBuilder2);
		handler.AppendLiteral("| **PersistentEpisodes (>= 16 ticks)** | `");
		handler.AppendFormatted(trackerMetricsAggregator.PersistentEpisodes);
		handler.AppendLiteral("` | Incidentes de alteração persistente da engine |");
		stringBuilder28.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder29 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(75, 1, stringBuilder2);
		handler.AppendLiteral("| **SamplesInEpisodes** | `");
		handler.AppendFormatted(trackerMetricsAggregator.SamplesInEpisodes);
		handler.AppendLiteral("` | Total de amostras físicas brutas agrupadas |");
		stringBuilder29.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder30 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(71, 1, stringBuilder2);
		handler.AppendLiteral("| **MeanEpisodeDurationMs** | `");
		handler.AppendFormatted(trackerMetricsAggregator.MeanEpisodeDurationMs, "F1");
		handler.AppendLiteral(" ms` | Duração média de cada incidente |");
		stringBuilder30.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83d\udca3 Auditoria de Bombsite da C4 e Retake (V4.2.6)");
		stringBuilder.AppendLine("| Métrica | Valor | Detalhes |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder31 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(96, 1, stringBuilder2);
		handler.AppendLiteral("| **UniqueC4MismatchEpisodes** | `");
		handler.AppendFormatted(trackerMetricsAggregator.UniqueC4MismatchEpisodes);
		handler.AppendLiteral("` | Episódios únicos consolidados de divergência de bombsite |");
		stringBuilder31.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder32 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(117, 1, stringBuilder2);
		handler.AppendLiteral("| **C4SemanticMismatches** | `");
		handler.AppendFormatted(trackerMetricsAggregator.C4SemanticMismatches);
		handler.AppendLiteral("` | Divergências semânticas entre CommittedSite, MaterializedRealSite e CarrierTarget |");
		stringBuilder32.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder33 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(73, 1, stringBuilder2);
		handler.AppendLiteral("| **TotalMismatchTicks** | `");
		handler.AppendFormatted(trackerMetricsAggregator.TotalMismatchTicks);
		handler.AppendLiteral("` | Total de ticks sob correção de mismatch |");
		stringBuilder33.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder34 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(96, 1, stringBuilder2);
		handler.AppendLiteral("| **StaleObjectivesRejected** | `");
		handler.AppendFormatted(trackerMetricsAggregator.StaleObjectivesRejected);
		handler.AppendLiteral("` | Objetivos com revisão obsoleta rejeitados pelo Arbitrator |");
		stringBuilder34.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder35 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(95, 1, stringBuilder2);
		handler.AppendLiteral("| **RetakeSiteMismatches** | `");
		handler.AppendFormatted(trackerMetricsAggregator.RetakeSiteMismatches);
		handler.AppendLiteral("` | Tentativas de desvio do retake CT em relação ao PlantedSite |");
		stringBuilder35.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83e\udd98 Auditoria de Controle de Jump (V4.2.8)");
		stringBuilder.AppendLine("| Métrica | Valor | Detalhes |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder36 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(78, 1, stringBuilder2);
		handler.AppendLiteral("| **JumpRequested** | `");
		handler.AppendFormatted(JumpRequestedCount);
		handler.AppendLiteral("` | Total de intenções ou predições solicitando salto |");
		stringBuilder36.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder37 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(69, 1, stringBuilder2);
		handler.AppendLiteral("| **JumpExecuted** | `");
		handler.AppendFormatted(JumpExecutedCount);
		handler.AppendLiteral("` | Saltos validados e executados fisicamente |");
		stringBuilder37.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder38 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(87, 1, stringBuilder2);
		handler.AppendLiteral("| **JumpSuppressedAirborne** | `");
		handler.AppendFormatted(JumpSuppressedAirborneCount);
		handler.AppendLiteral("` | Saltos suprimidos por estar no ar (não-renovação) |");
		stringBuilder38.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder39 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(74, 1, stringBuilder2);
		handler.AppendLiteral("| **JumpSuppressedCooldown** | `");
		handler.AppendFormatted(JumpSuppressedCooldownCount);
		handler.AppendLiteral("` | Saltos suprimidos por cooldown ativo |");
		stringBuilder39.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder40 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(92, 1, stringBuilder2);
		handler.AppendLiteral("| **JumpSuppressedContext** | `");
		handler.AppendFormatted(JumpSuppressedContextCount);
		handler.AppendLiteral("` | Saltos suprimidos por contexto proibido / consenso ONNX |");
		stringBuilder40.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder41 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(84, 1, stringBuilder2);
		handler.AppendLiteral("| **RepeatedJumpSequences** | `");
		handler.AppendFormatted(RepeatedJumpSequencesCount);
		handler.AppendLiteral("` | Sequências repetidas de salto sem justificativa |");
		stringBuilder41.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83d\udee1\ufe0f Auditoria de Ciclo de Vida e Isolamento de Adaptações (V4.2.8)");
		stringBuilder.AppendLine("| Métrica | Valor | Detalhes |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder42 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(86, 1, stringBuilder2);
		handler.AppendLiteral("| **CrossTeamReplacementAttempts** | `");
		handler.AppendFormatted(CrossTeamAttemptsCount);
		handler.AppendLiteral("` | Total de tentativas cruzadas interceptadas |");
		stringBuilder42.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder43 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(89, 1, stringBuilder2);
		handler.AppendLiteral("| **UniqueCrossTeamReplacementEpisodes** | `");
		handler.AppendFormatted(UniqueCrossTeamEpisodesCount);
		handler.AppendLiteral("` | Episódios únicos registrados (sem spam) |");
		stringBuilder43.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder44 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(91, 1, stringBuilder2);
		handler.AppendLiteral("| **RepeatedAttemptsSuppressed** | `");
		handler.AppendFormatted(RepeatedAttemptsSuppressedCount);
		handler.AppendLiteral("` | Tentativas repetidas suprimidas pelo deduplicador |");
		stringBuilder44.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### ♟\ufe0f Auditoria de Formação CT 2-1-2 (V4.2.8)");
		stringBuilder.AppendLine("| Métrica | Valor | Detalhes |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder45 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(73, 1, stringBuilder2);
		handler.AppendLiteral("| **CtFormationsMaterialized** | `");
		handler.AppendFormatted(CtFormationsMaterializedCount);
		handler.AppendLiteral("` | Total de formações materializadas |");
		stringBuilder45.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder46 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(91, 1, stringBuilder2);
		handler.AppendLiteral("| **CtFormationsInvalidFallback** | `");
		handler.AppendFormatted(CtFormationsInvalidCount);
		handler.AppendLiteral("` | Formações inválidas que acionaram fallback 2-1-2 |");
		stringBuilder46.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83d\udee1\ufe0f Detalhes de Interceptação da Engine (V4.2.4)");
		stringBuilder.AppendLine("| Métrica de Override | Valor | Detalhes |");
		stringBuilder.AppendLine("| :--- | :--- | :--- |");
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder47 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(77, 1, stringBuilder2);
		handler.AppendLiteral("| **UnexplainedStateChanges** | `");
		handler.AppendFormatted(trackerMetricsAggregator.UnexplainedStateChanges);
		handler.AppendLiteral("` | Microalterações inexplicadas da engine |");
		stringBuilder47.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder48 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(78, 1, stringBuilder2);
		handler.AppendLiteral("| **UniqueOverrideEvents** | `");
		handler.AppendFormatted(trackerMetricsAggregator.UniqueOverrideEvents);
		handler.AppendLiteral("` | Eventos únicos de interceptação detectados |");
		stringBuilder48.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder49 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(91, 1, stringBuilder2);
		handler.AppendLiteral("| **PersistentOverrideEvents** | `");
		handler.AppendFormatted(trackerMetricsAggregator.PersistentOverrideEvents);
		handler.AppendLiteral("` | Alterações críticas que persistiram por >= 16 ticks |");
		stringBuilder49.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder50 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(73, 2, stringBuilder2);
		handler.AppendLiteral("| **SamplesAffected** | `");
		handler.AppendFormatted(trackerMetricsAggregator.SamplesAffected);
		handler.AppendLiteral("` | Amostras físicas na janela do override (");
		handler.AppendFormatted((float)trackerMetricsAggregator.SamplesAffected / num * 100f, "F1");
		handler.AppendLiteral("%) |");
		stringBuilder50.AppendLine(ref handler);
		stringBuilder2 = stringBuilder;
		StringBuilder stringBuilder51 = stringBuilder2;
		handler = new StringBuilder.AppendInterpolatedStringHandler(79, 1, stringBuilder2);
		handler.AppendLiteral("| **SnapshotAppearances** | `");
		handler.AppendFormatted(trackerMetricsAggregator.SnapshotAppearances);
		handler.AppendLiteral("` | Aparições observadas em snapshots periódicos |");
		stringBuilder51.AppendLine(ref handler);
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83d\udcca Distribuição por Fonte da Intenção (IntentSource)");
		stringBuilder.AppendLine("| Fonte | Amostras | WithProgress | LowProgress | NoProgress | Replaced |");
		stringBuilder.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- |");
		IEnumerable<IGrouping<MovementIntentSource, MovementExecutionSample>> enumerable = from s in list
			where s.WinningIntent != null
			group s by s.WinningIntent.Source;
		foreach (IGrouping<MovementIntentSource, MovementExecutionSample> item2 in enumerable)
		{
			int num5 = item2.Count();
			int num6 = item2.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedWithProgress);
			int num7 = item2.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedLowProgress);
			int num8 = item2.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedNoProgress);
			int num9 = item2.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.ReplacedByHigherPriority);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder52 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(25, 6, stringBuilder2);
			handler.AppendLiteral("| `");
			handler.AppendFormatted(item2.Key);
			handler.AppendLiteral("` | ");
			handler.AppendFormatted(num5);
			handler.AppendLiteral(" | ");
			handler.AppendFormatted((float)num6 * 100f / (float)num5, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num7 * 100f / (float)num5, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num8 * 100f / (float)num5, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num9 * 100f / (float)num5, "F1");
			handler.AppendLiteral("% |");
			stringBuilder52.AppendLine(ref handler);
		}
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83c\udfaf Distribuição por Tipo de Comando (MovementCommandKind)");
		stringBuilder.AppendLine("| Tipo | Amostras | WithProgress | LowProgress | NoProgress | Hold/Stop |");
		stringBuilder.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- |");
		IEnumerable<IGrouping<MovementCommandKind, MovementExecutionSample>> enumerable2 = from s in list
			where s.WinningIntent != null
			group s by s.WinningIntent.Kind;
		foreach (IGrouping<MovementCommandKind, MovementExecutionSample> item3 in enumerable2)
		{
			int num10 = item3.Count();
			int num11 = item3.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedWithProgress);
			int num12 = item3.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedLowProgress);
			int num13 = item3.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedNoProgress);
			int num14 = item3.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AuthorizedHoldApplied || x.PhysicalOutcome == PhysicalExecutionOutcome.FullStopApplied);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder53 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(25, 6, stringBuilder2);
			handler.AppendLiteral("| `");
			handler.AppendFormatted(item3.Key);
			handler.AppendLiteral("` | ");
			handler.AppendFormatted(num10);
			handler.AppendLiteral(" | ");
			handler.AppendFormatted((float)num11 * 100f / (float)num10, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num12 * 100f / (float)num10, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num13 * 100f / (float)num10, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num14 * 100f / (float)num10, "F1");
			handler.AppendLiteral("% |");
			stringBuilder53.AppendLine(ref handler);
		}
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### ⏱\ufe0f Distribuição por Round");
		stringBuilder.AppendLine("| RoundId | Amostras | WithProgress | LowProgress | NoProgress | ExternalOverrides |");
		stringBuilder.AppendLine("| :--- | :--- | :--- | :--- | :--- | :--- |");
		IOrderedEnumerable<IGrouping<long, MovementExecutionSample>> orderedEnumerable = from s in list
			group s by s.InternalRoundId into g
			orderby g.Key
			select g;
		foreach (IGrouping<long, MovementExecutionSample> item4 in orderedEnumerable)
		{
			int num15 = item4.Count();
			int num16 = item4.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedWithProgress);
			int num17 = item4.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedLowProgress);
			int num18 = item4.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedNoProgress);
			int value6 = item4.Count((MovementExecutionSample x) => x.StateIntegrity == StateIntegrityOutcome.PossibleExternalControllerOverride);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder54 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(30, 6, stringBuilder2);
			handler.AppendLiteral("| Round `");
			handler.AppendFormatted(item4.Key);
			handler.AppendLiteral("` | ");
			handler.AppendFormatted(num15);
			handler.AppendLiteral(" | ");
			handler.AppendFormatted((float)num16 * 100f / (float)num15, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num17 * 100f / (float)num15, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted((float)num18 * 100f / (float)num15, "F1");
			handler.AppendLiteral("% | ");
			handler.AppendFormatted(value6);
			handler.AppendLiteral(" |");
			stringBuilder54.AppendLine(ref handler);
		}
		stringBuilder.AppendLine();
		stringBuilder.AppendLine("#### \ud83e\udded Matriz Vencedor -> Desfecho Físico (WinnerToPhysicalOutcomeMatrix)");
		stringBuilder.AppendLine("```");
		foreach (IGrouping<MovementCommandKind, MovementExecutionSample> item5 in enumerable2)
		{
			int num19 = item5.Count();
			int num20 = item5.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedWithProgress);
			int num21 = item5.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedLowProgress);
			int num22 = item5.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.AppliedNoProgress);
			int num23 = item5.Count((MovementExecutionSample x) => x.PhysicalOutcome == PhysicalExecutionOutcome.ReplacedByHigherPriority);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder55 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(1, 1, stringBuilder2);
			handler.AppendFormatted(item5.Key);
			handler.AppendLiteral(":");
			stringBuilder55.AppendLine(ref handler);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder56 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(24, 1, stringBuilder2);
			handler.AppendLiteral("  AppliedWithProgress: ");
			handler.AppendFormatted((float)num20 * 100f / (float)num19, "F0");
			handler.AppendLiteral("%");
			stringBuilder56.AppendLine(ref handler);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder57 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(23, 1, stringBuilder2);
			handler.AppendLiteral("  AppliedLowProgress: ");
			handler.AppendFormatted((float)num21 * 100f / (float)num19, "F0");
			handler.AppendLiteral("%");
			stringBuilder57.AppendLine(ref handler);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder58 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(22, 1, stringBuilder2);
			handler.AppendLiteral("  AppliedNoProgress: ");
			handler.AppendFormatted((float)num22 * 100f / (float)num19, "F0");
			handler.AppendLiteral("%");
			stringBuilder58.AppendLine(ref handler);
			stringBuilder2 = stringBuilder;
			StringBuilder stringBuilder59 = stringBuilder2;
			handler = new StringBuilder.AppendInterpolatedStringHandler(29, 1, stringBuilder2);
			handler.AppendLiteral("  ReplacedByHigherPriority: ");
			handler.AppendFormatted((float)num23 * 100f / (float)num19, "F0");
			handler.AppendLiteral("%");
			stringBuilder59.AppendLine(ref handler);
		}
		stringBuilder.AppendLine("```");
		return stringBuilder.ToString();
	}

	private static float ComputeMedian(List<float> values)
	{
		if (values.Count == 0)
		{
			return 0f;
		}
		values.Sort();
		int num = values.Count / 2;
		return (values.Count % 2 != 0) ? values[num] : ((values[num - 1] + values[num]) / 2f);
	}
}
