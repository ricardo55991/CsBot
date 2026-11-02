#pragma warning disable CS8600, CS8602, CS8604
using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Threading;

namespace CsBotManager;

public sealed class C4MismatchEpisodeTracker
{
	private readonly ConcurrentDictionary<int, C4MismatchEpisode> _activeEpisodesByCarrier = new ConcurrentDictionary<int, C4MismatchEpisode>();

	private readonly ConcurrentBag<C4MismatchEpisode> _allEpisodes = new ConcurrentBag<C4MismatchEpisode>();

	private int _semanticMismatchesCount = 0;

	public int UniqueC4MismatchEpisodes => _allEpisodes.Count;

	public int TotalMismatchTicks => _allEpisodes.Sum((C4MismatchEpisode e) => e.TotalTicks);

	public int SemanticMismatchesCount => _semanticMismatchesCount;

	public void RecordSemanticMismatch(int carrierSlot, string committedSite, string materializedRealSite, string carrierTargetSite, long currentTick, MatchTelemetryLogger? logger)
	{
		Interlocked.Increment(ref _semanticMismatchesCount);
		logger?.LogEvent("C4_SEMANTIC_SITE_MISMATCH", $"carrierSlot={carrierSlot} committedSite={committedSite} materializedRealSite={materializedRealSite} carrierTarget={carrierTargetSite} tick={currentTick}");
	}

	public void RecordMismatch(int carrierSlot, Guid logicalActionId, Guid objectiveRevision, string labelSite, string goalSite, string realSite, long currentTick, MatchTelemetryLogger? logger)
	{
		if (_activeEpisodesByCarrier.TryGetValue(carrierSlot, out C4MismatchEpisode value))
		{
			if (value.LogicalActionId == logicalActionId && value.ObjectiveRevision == objectiveRevision && value.LabelSite == labelSite && value.GoalSite == goalSite && value.RealSite == realSite)
			{
				value.LastTick = currentTick;
				value.TotalTicks++;
				return;
			}
			ResolveEpisode(carrierSlot, currentTick, logger);
		}
		C4MismatchEpisode c4MismatchEpisode = new C4MismatchEpisode
		{
			CarrierSlot = carrierSlot,
			LogicalActionId = logicalActionId,
			ObjectiveRevision = objectiveRevision,
			LabelSite = labelSite,
			GoalSite = goalSite,
			RealSite = realSite,
			StartTick = currentTick,
			LastTick = currentTick,
			TotalTicks = 1,
			Resolved = false
		};
		_activeEpisodesByCarrier[carrierSlot] = c4MismatchEpisode;
		_allEpisodes.Add(c4MismatchEpisode);
		logger?.LogEvent("C4_OBJECTIVE_MISMATCH_STARTED", $"carrier={carrierSlot} actionId={logicalActionId} revision={objectiveRevision} labelSite={labelSite} goalSite={goalSite} realSite={realSite} tick={currentTick}");
	}

	public void ResolveEpisode(int carrierSlot, long currentTick, MatchTelemetryLogger? logger)
	{
		if (_activeEpisodesByCarrier.TryRemove(carrierSlot, out C4MismatchEpisode value))
		{
			value.Resolved = true;
			value.LastTick = currentTick;
			logger?.LogEvent("C4_OBJECTIVE_MISMATCH_RESOLVED", $"carrier={carrierSlot} actionId={value.LogicalActionId} durationTicks={currentTick - value.StartTick} totalMismatchTicks={value.TotalTicks} tick={currentTick}");
		}
	}
}
