using System;

namespace CsBotManager;

public sealed class C4MismatchEpisode
{
	public int CarrierSlot { get; init; }

	public Guid LogicalActionId { get; init; }

	public Guid ObjectiveRevision { get; init; }

	public string LabelSite { get; init; } = string.Empty;

	public string GoalSite { get; init; } = string.Empty;

	public string RealSite { get; init; } = string.Empty;

	public long StartTick { get; init; }

	public long LastTick { get; set; }

	public int TotalTicks { get; set; }

	public bool Resolved { get; set; }
}
