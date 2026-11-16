using System;
using System.Collections.Generic;
using System.Linq;

namespace CsBotManager;

public enum TeamDepartureControlMode
{
    CANARY_CONTROLLED,
    UTILITY_AI_OBSERVED
}

public enum EffectiveControlMode
{
    NONE,
    UTILITY_AI,
    CANARY_CONTROLLED
}

public enum OpeningAssignmentLifecycleState
{
    SCHEDULED,
    UTILITY_AI_OBSERVED,
    CANARY_PENDING,
    CANARY_CONTROLLED,
    COMPLETED,
    INTERRUPTED,
    ABORTED,
    EXPIRED_BEFORE_CONTROL,
    CANCELLED_BEFORE_CONTROL
}

public record OpeningAssignmentLifecycleRecord
{
    public string RunId { get; init; } = string.Empty;
    public string PluginInstanceId { get; init; } = string.Empty;
    public int ProcessId { get; init; }
    public string DllSha256 { get; init; } = string.Empty;
    public string UtcTimestamp { get; init; } = string.Empty;
    public string EventType { get; init; } = "OPENING_ASSIGNMENT_TERMINAL";
    public string AssignmentId { get; init; } = string.Empty;
    public int RoundId { get; init; }
    public string Team { get; init; } = string.Empty;
    public string PlayerPseudonym { get; init; } = string.Empty;
    public string Destination { get; init; } = string.Empty;
    public string RouteId { get; init; } = string.Empty;
    public bool RouteCertified { get; init; }
    public TeamDepartureControlMode RequestedControlMode { get; init; }
    public EffectiveControlMode EffectiveControlMode { get; init; }
    public OpeningAssignmentLifecycleState LifecycleState { get; init; }
    public OpeningAssignmentLifecycleState? PreviousState { get; init; }
    public OpeningAssignmentLifecycleState? NewState { get; init; }
    public string TerminalReason { get; init; } = string.Empty;
    public int? PredecessorSlot { get; init; }
    public string QueueId { get; init; } = string.Empty;
    public int ScheduledTick { get; init; }
    public int PlannedReleaseTick { get; init; }
    public int ExpirationTick { get; init; }
    public int TerminalTick { get; init; }
    public bool ControllerCreated { get; init; }
    public bool LeaseAcquired { get; init; }
    public string SessionId { get; init; } = string.Empty;
}

public sealed record OpeningAssignmentTerminalRecord : OpeningAssignmentLifecycleRecord;

public enum CorridorConfidence
{
    HIGH,
    MEDIUM,
    LOW
}

public sealed record CorridorInferenceResult
{
    public string Corridor { get; init; } = string.Empty;
    public string Source { get; init; } = string.Empty;
    public CorridorConfidence Confidence { get; init; } = CorridorConfidence.LOW;
    public int FirstNavArea { get; init; }
    public string FirstPortalId { get; init; } = string.Empty;
}

public sealed record TeamOpeningBotCandidate
{
    public int BotSlot { get; init; }
    public string PlayerPseudonym { get; init; } = string.Empty;
    public string Team { get; init; } = string.Empty;
    public string Role { get; init; } = string.Empty;
    public string Destination { get; init; } = string.Empty;
    public string Sector { get; init; } = string.Empty;
    public string Bombsite { get; init; } = string.Empty;
    public string RouteId { get; init; } = string.Empty;
    public string SpawnBucket { get; init; } = string.Empty;
    public string ConflictGroup { get; init; } = string.Empty;
    public bool HasC4 { get; init; }
    public float SpawnDistance { get; init; }
    public double DeadlineSeconds { get; init; }
    public bool HasWeaponAwp { get; init; }
    public string AlternativeRouteId { get; init; } = string.Empty;
    public string AlternativeConflictGroup { get; init; } = string.Empty;
    public TeamDepartureControlMode ControlMode { get; init; } = TeamDepartureControlMode.UTILITY_AI_OBSERVED;
    public int FirstNavArea { get; init; }
    public string FirstPortalId { get; init; } = string.Empty;
    public float FirstDirectionX { get; init; }
    public float FirstDirectionY { get; init; }
    public bool IsEligibleForCanary { get; init; } = true;
    public string IneligibilityReason { get; init; } = string.Empty;
}

public sealed record TeamScheduledBotAssignment
{
    public int BotSlot { get; init; }
    public string PlayerPseudonym { get; init; } = string.Empty;
    public string Team { get; init; } = string.Empty;
    public string Role { get; init; } = string.Empty;
    public string Destination { get; init; } = string.Empty;
    public string Sector { get; init; } = string.Empty;
    public string Bombsite { get; init; } = string.Empty;
    public string RouteId { get; init; } = string.Empty;
    public string ConflictGroup { get; init; } = string.Empty;
    public int Priority { get; init; }
    public int PlannedReleaseTick { get; init; }
    public int? PredecessorSlot { get; init; }
    public int StaggerMs { get; init; }
    public bool FallbackToUtilityAi { get; init; }
    public string FallbackReason { get; init; } = string.Empty;
    public bool HasC4 { get; init; }
}

public sealed record FullTeamDepartureAssignment
{
    public int BotSlot { get; init; }
    public string PlayerPseudonym { get; init; } = string.Empty;
    public TeamDepartureControlMode ControlMode { get; init; }
    public string Destination { get; init; } = string.Empty;
    public string Sector { get; init; } = string.Empty;
    public string Role { get; init; } = string.Empty;
    public string RouteId { get; init; } = string.Empty;
    public string ConflictGroup { get; init; } = string.Empty;
    public string InitialDepartureCorridor { get; init; } = string.Empty;
    public string DownstreamConflictGroup { get; init; } = string.Empty;
    public string QueueId { get; init; } = string.Empty;
    public int QueuePosition { get; init; }
    public bool IsLeader { get; init; }
    public string InferredCorridor { get; init; } = string.Empty;
    public string CorridorInferenceSource { get; init; } = string.Empty;
    public CorridorConfidence CorridorConfidence { get; init; } = CorridorConfidence.LOW;
    public int FirstNavArea { get; init; }
    public string FirstPortalId { get; init; } = string.Empty;
    public int Priority { get; init; }
    public int LeaderSlot { get; init; }
    public int? PredecessorSlot { get; init; }
    public int PlannedReleaseTick { get; init; }
    public int StaggerMs { get; init; }
    public bool PassiveHoldRequired { get; init; }
    public int PassiveHoldMs { get; init; }
    public bool FallbackToUtilityAi { get; init; }
    public string FallbackReason { get; init; } = string.Empty;
}

public sealed record FullTeamDepartureSchedule
{
    public int RoundId { get; init; }
    public int RoundStartTick { get; init; }
    public IReadOnlyList<FullTeamDepartureAssignment> Assignments { get; init; } = Array.Empty<FullTeamDepartureAssignment>();
    public IReadOnlyDictionary<int, FullTeamDepartureAssignment> BySlot { get; init; } = new Dictionary<int, FullTeamDepartureAssignment>();
}

public sealed class PassiveDepartureHold
{
    public int RoundId { get; init; }
    public int BotSlot { get; init; }
    public string ConflictGroup { get; init; } = string.Empty;
    public int StartTick { get; init; }
    public int ReleaseTick { get; set; }
    public string HoldReason { get; init; } = "QUEUE_WAIT_FOR_LEADER";
    public bool Released { get; set; }
    public string ReleaseReason { get; set; } = string.Empty;
}

public sealed class PortalTraversalState
{
    public int BotSlot { get; init; }
    public int ReleasedTick { get; set; } = -1;
    public int EnterTick { get; set; } = -1;
    public int ClearTick { get; set; } = -1;
    public bool Entered { get; set; }
    public bool Cleared { get; set; }
    public int EntryArea { get; set; }
    public int ExitArea { get; set; }
    public (float X, float Y, float Z) EntryPosition { get; set; }
    public (float X, float Y, float Z) ClearPosition { get; set; }
    public string ClearReason { get; set; } = string.Empty;
}

public sealed class CorridorDepartureQueue
{
    public string ConflictGroup { get; }
    public string Team { get; init; } = string.Empty;
    public List<int> OrderedSlots { get; } = new();
    public int LeaderSlot { get; private set; } = -1;
    public int CurrentReleasedSlot { get; private set; } = -1;
    public bool PortalOccupied { get; private set; }
    public int LastPortalClearTick { get; private set; } = -1;
    public int PortalEntryArea { get; set; }
    public int PortalExitArea { get; set; }
    public int PortalEnterTick => CurrentReleasedSlot >= 0 && _portalStateBySlot.TryGetValue(CurrentReleasedSlot, out var st) ? st.EnterTick : -1;
    public int PortalClearTick => CurrentReleasedSlot >= 0 && _portalStateBySlot.TryGetValue(CurrentReleasedSlot, out var st) ? st.ClearTick : LastPortalClearTick;
    public bool PortalCrossingConfirmed => CurrentReleasedSlot >= 0 && _portalStateBySlot.TryGetValue(CurrentReleasedSlot, out var st) && st.Cleared;
    public bool RequiresPhysicalPortalClearance { get; set; } = true;
    public float MinimumSpacingUnits { get; }
    public int MaximumHoldMs { get; }
    private readonly Dictionary<int, PortalTraversalState> _portalStateBySlot = new();
    private readonly Dictionary<int, int> _releasedTicks = new();
    private readonly HashSet<int> _portalClearedSlots = new();
    private readonly HashSet<int> _removedSlots = new();
    private int _lastReleaseTick = -1;
    private int _blockedSameTickReleaseMinTick = -1;

    public IReadOnlyDictionary<int, PortalTraversalState> PortalStateBySlot => _portalStateBySlot;
    public IReadOnlyCollection<int> RemovedSlots => _removedSlots;
    public IReadOnlyCollection<int> ClearedSlots => _portalClearedSlots;

    public CorridorDepartureQueue(string conflictGroup, float minimumSpacingUnits = 110f, int maximumHoldMs = 500)
    {
        ConflictGroup = conflictGroup;
        MinimumSpacingUnits = minimumSpacingUnits;
        MaximumHoldMs = Math.Clamp(maximumHoldMs, 0, 500);
    }

    public void Enqueue(int slot)
    {
        if (!OrderedSlots.Contains(slot))
        {
            OrderedSlots.Add(slot);
            if (!_portalStateBySlot.ContainsKey(slot))
            {
                _portalStateBySlot[slot] = new PortalTraversalState
                {
                    BotSlot = slot,
                    EntryArea = PortalEntryArea,
                    ExitArea = PortalExitArea
                };
            }
            if (LeaderSlot < 0)
            {
                LeaderSlot = slot;
                CurrentReleasedSlot = slot;
            }
        }
    }

    public int? GetPredecessor(int slot)
    {
        int idx = OrderedSlots.IndexOf(slot);
        if (idx <= 0) return null;
        return OrderedSlots[idx - 1];
    }

    public bool HasPredecessorCleared(int slot)
    {
        int? pred = GetPredecessor(slot);
        if (!pred.HasValue) return true;
        return _portalStateBySlot.TryGetValue(pred.Value, out var st) && st.Cleared;
    }

    public int? TryAdvanceQueue()
    {
        if (CurrentReleasedSlot >= 0 && _portalStateBySlot.TryGetValue(CurrentReleasedSlot, out var st) && !st.Cleared)
        {
            return null;
        }
        foreach (int s in OrderedSlots)
        {
            if (!_releasedTicks.ContainsKey(s))
            {
                return s;
            }
        }
        return null;
    }

    public bool CanRelease(int slot, int tick, IReadOnlyList<TeammatePositionSnapshot> teamSnapshots)
    {
        if (!OrderedSlots.Contains(slot)) return true;
        if (slot == LeaderSlot) return true;
        if (_releasedTicks.ContainsKey(slot)) return true;
        if (_lastReleaseTick == tick || tick < _blockedSameTickReleaseMinTick) return false;

        int? predOpt = GetPredecessor(slot);
        if (!predOpt.HasValue) return true;
        int predSlot = predOpt.Value;

        if (_portalStateBySlot.TryGetValue(predSlot, out var predState) && predState.Cleared)
        {
            return true;
        }

        // Tempo sozinho nunca pode liberar portal ocupado quando RequiresPhysicalPortalClearance == true
        if (_releasedTicks.TryGetValue(predSlot, out int predReleaseTick))
        {
            if (!RequiresPhysicalPortalClearance)
            {
                int maxWaitTicks = (int)Math.Ceiling(MaximumHoldMs * 64.0 / 1000.0);
                if ((tick - predReleaseTick) >= maxWaitTicks)
                {
                    return true;
                }
            }

            var me = teamSnapshots.FirstOrDefault(t => t.RawSlot == slot);
            var pred = teamSnapshots.FirstOrDefault(t => t.RawSlot == predSlot);
            if (me != null && pred != null && predState != null && predState.Entered)
            {
                double dist = Math.Sqrt((me.X - pred.X) * (me.X - pred.X) + (me.Y - pred.Y) * (me.Y - pred.Y));
                if (dist >= MinimumSpacingUnits && !PortalOccupied)
                {
                    return true;
                }
            }
        }

        return false;
    }

    public bool TryConfirmPortalCrossing(int slot, int tick, int currentNavArea, int exitNavArea, float distFromEntry)
        => TryConfirmPortalCrossing(slot, tick, currentNavArea, PortalEntryArea, exitNavArea, distFromEntry, distFromEntry);

    public bool TryConfirmPortalCrossing(
        int slot,
        int tick,
        int currentNavArea,
        int entryNavArea,
        int exitNavArea,
        float distanceFromPortalEntry,
        float pathProgress)
    {
        if (!_portalStateBySlot.TryGetValue(slot, out var state))
        {
            state = new PortalTraversalState { BotSlot = slot, EntryArea = entryNavArea, ExitArea = exitNavArea };
            _portalStateBySlot[slot] = state;
        }
        if (state.Cleared) return true;

        if (!state.Entered)
        {
            bool areaEntered = entryNavArea > 0 && currentNavArea == entryNavArea;
            bool distEntered = entryNavArea <= 0 && distanceFromPortalEntry > 0f && pathProgress > 0f;
            if (areaEntered || distEntered)
            {
                MarkPortalEntered(slot, tick);
            }
        }

        bool areaExited = exitNavArea > 0 && currentNavArea == exitNavArea;
        bool distAndProgressExited = state.Entered && pathProgress > 0f && distanceFromPortalEntry >= MinimumSpacingUnits;
        if (areaExited || distAndProgressExited)
        {
            string reason = areaExited ? "EXIT_NAV_AREA" : "DIST_AND_PROGRESS";
            MarkPortalCleared(slot, tick, reason);
            return true;
        }
        return false;
    }

    public void MarkReleased(int slot, int tick)
    {
        CurrentReleasedSlot = slot;
        _releasedTicks[slot] = tick;
        _lastReleaseTick = tick;
        if (!_portalStateBySlot.TryGetValue(slot, out var state))
        {
            state = new PortalTraversalState { BotSlot = slot, EntryArea = PortalEntryArea, ExitArea = PortalExitArea };
            _portalStateBySlot[slot] = state;
        }
        state.ReleasedTick = tick;
    }

    public void MarkPortalEntered(int slot, int tick)
    {
        if (!_portalStateBySlot.TryGetValue(slot, out var state))
        {
            state = new PortalTraversalState { BotSlot = slot, EntryArea = PortalEntryArea, ExitArea = PortalExitArea };
            _portalStateBySlot[slot] = state;
        }
        if (!state.Entered)
        {
            state.Entered = true;
            state.EnterTick = tick;
        }
        PortalOccupied = true;
    }

    public void MarkPortalCleared(int slot, int tick, string reason = "PHYSICAL_CROSSING")
    {
        if (!_portalStateBySlot.TryGetValue(slot, out var state))
        {
            state = new PortalTraversalState { BotSlot = slot, EntryArea = PortalEntryArea, ExitArea = PortalExitArea };
            _portalStateBySlot[slot] = state;
        }
        state.Cleared = true;
        state.ClearTick = tick;
        state.ClearReason = reason;
        _portalClearedSlots.Add(slot);
        PortalOccupied = false;
        LastPortalClearTick = tick;
    }

    public bool IsPredecessorCleared(int? predSlot) => predSlot.HasValue && _portalStateBySlot.TryGetValue(predSlot.Value, out var st) && st.Cleared;

    public (bool PredecessorRemoved, bool FollowerPromoted, bool QueueRelinked, int? NewLeaderSlot) MarkRemoved(int predecessorSlot, string reason, int currentTick = -1)
    {
        int idx = OrderedSlots.IndexOf(predecessorSlot);
        if (idx < 0) return (false, false, false, null);

        OrderedSlots.RemoveAt(idx);
        _removedSlots.Add(predecessorSlot);
        if (_portalStateBySlot.TryGetValue(predecessorSlot, out var st))
        {
            st.Cleared = true;
            st.ClearReason = reason;
        }
        PortalOccupied = false;

        bool promoted = false;
        bool relinked = false;
        if (LeaderSlot == predecessorSlot)
        {
            LeaderSlot = OrderedSlots.Count > 0 ? OrderedSlots[0] : -1;
            CurrentReleasedSlot = LeaderSlot;
            promoted = LeaderSlot >= 0;
        }
        else if (idx < OrderedSlots.Count)
        {
            relinked = true;
        }

        if (currentTick >= 0)
        {
            _blockedSameTickReleaseMinTick = currentTick + 1;
        }
        else if (_lastReleaseTick >= 0)
        {
            _blockedSameTickReleaseMinTick = _lastReleaseTick + 1;
        }

        return (true, promoted, relinked, LeaderSlot >= 0 ? LeaderSlot : null);
    }

    public void Remove(int slot) => MarkRemoved(slot, "REMOVED");

    public void ResetRound()
    {
        OrderedSlots.Clear();
        LeaderSlot = -1;
        CurrentReleasedSlot = -1;
        PortalOccupied = false;
        LastPortalClearTick = -1;
        _lastReleaseTick = -1;
        _blockedSameTickReleaseMinTick = -1;
        _portalStateBySlot.Clear();
        _releasedTicks.Clear();
        _portalClearedSlots.Clear();
        _removedSlots.Clear();
    }
}

public sealed class TeamOpeningRouteScheduler
{
    public const int MaxStaggerMs = 500;

    public static readonly IReadOnlySet<string> ValidConflictGroups = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        "CT_SPAWN_EXIT",
        "MARKET_ENTRY",
        "CONNECTOR_ENTRY",
        "WINDOW_ENTRY",
        "T_SPAWN_EXIT",
        "A_RAMP_ENTRY",
        "PALACE_ENTRY",
        "TOP_MID_ENTRY",
        "UNDERPASS_ENTRY",
        "B_APPS_ENTRY",
        "HOUSE_ENTRY"
    };

    public static CorridorInferenceResult InferInitialCorridor(TeamOpeningBotCandidate c)
    {
        // 1. ConflictGroup explícito válido
        if (!string.IsNullOrWhiteSpace(c.ConflictGroup) && ValidConflictGroups.Contains(c.ConflictGroup))
        {
            return new CorridorInferenceResult
            {
                Corridor = c.ConflictGroup.ToUpperInvariant(),
                Source = "EXPLICIT_CONFLICT_GROUP",
                Confidence = CorridorConfidence.HIGH,
                FirstNavArea = c.FirstNavArea,
                FirstPortalId = c.FirstPortalId
            };
        }

        // 2. FirstPortalId
        if (!string.IsNullOrWhiteSpace(c.FirstPortalId))
        {
            string p = c.FirstPortalId.ToLowerInvariant();
            string corr = p.Contains("window") ? "WINDOW_ENTRY"
                : (p.Contains("market") || p.Contains("kitchen")) ? "MARKET_ENTRY"
                : p.Contains("conn") ? "CONNECTOR_ENTRY"
                : "CT_SPAWN_EXIT";
            return new CorridorInferenceResult
            {
                Corridor = corr,
                Source = "FIRST_PORTAL_ID",
                Confidence = CorridorConfidence.HIGH,
                FirstNavArea = c.FirstNavArea,
                FirstPortalId = c.FirstPortalId
            };
        }

        // 4 & 5. RouteId / Destination
        string id = $"{c.RouteId} {c.Destination}".ToLowerInvariant();
        if (!string.IsNullOrWhiteSpace(id.Trim()))
        {
            if (id.Contains("palace"))
            {
                return new CorridorInferenceResult { Corridor = "PALACE_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("a_ramp") || id.Contains("tetris"))
            {
                return new CorridorInferenceResult { Corridor = "A_RAMP_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("underpass"))
            {
                return new CorridorInferenceResult { Corridor = "UNDERPASS_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("top_mid"))
            {
                return new CorridorInferenceResult { Corridor = "TOP_MID_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("house_staging"))
            {
                return new CorridorInferenceResult { Corridor = "HOUSE_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("apps") || id.Contains("tapete"))
            {
                return new CorridorInferenceResult { Corridor = "B_APPS_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("window") || id.Contains("vents") || id.Contains("ladder"))
            {
                return new CorridorInferenceResult { Corridor = "WINDOW_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("market") || id.Contains("b_van") || id.Contains("b_forest") || id.Contains("edward") || id.Contains("jail") || id.Contains("pillar") || id.Contains("b_site") || id.Contains("b_short"))
            {
                return new CorridorInferenceResult { Corridor = "MARKET_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("connector") || id.Contains("jungle") || id.Contains("chair") || id.Contains("short_arch"))
            {
                return new CorridorInferenceResult { Corridor = "CONNECTOR_ENTRY", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.MEDIUM, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
            if (id.Contains("triple_box") || id.Contains("firebox") || id.Contains("stairs") || id.Contains("shadow") || id.Contains("sand_pit") || id.Contains("ticket"))
            {
                return new CorridorInferenceResult { Corridor = "CT_SPAWN_EXIT", Source = "ROUTE_OR_DESTINATION", Confidence = CorridorConfidence.HIGH, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
            }
        }

        // 6. Direção inicial (quando houver vetor)
        if (Math.Abs(c.FirstDirectionX) > 0.1f || Math.Abs(c.FirstDirectionY) > 0.1f)
        {
            string dirCorr = c.FirstDirectionY > 0.45f ? "MARKET_ENTRY" : (c.FirstDirectionX > 0.45f ? "WINDOW_ENTRY" : "CT_SPAWN_EXIT");
            return new CorridorInferenceResult { Corridor = dirCorr, Source = "INITIAL_DIRECTION", Confidence = CorridorConfidence.MEDIUM, FirstNavArea = c.FirstNavArea, FirstPortalId = c.FirstPortalId };
        }

        // 7. Setor isolado (LOW confidence - nunca cria bloqueio de corredor!)
        string sec = string.IsNullOrWhiteSpace(c.Sector) ? $"UNKNOWN_{c.BotSlot}" : $"SECTOR_{c.Sector.ToUpperInvariant()}";
        return new CorridorInferenceResult
        {
            Corridor = sec,
            Source = "SECTOR_ONLY",
            Confidence = CorridorConfidence.LOW,
            FirstNavArea = c.FirstNavArea,
            FirstPortalId = c.FirstPortalId
        };
    }

    public static int ComputePriority(TeamOpeningBotCandidate c, string roundPlanBombsite)
    {
        if (c.HasC4 && IsBombsiteCompatible(c.Bombsite, roundPlanBombsite)) return 1;
        if (c.Role.Contains("Entry", StringComparison.OrdinalIgnoreCase)) return 2;
        if (c.Team.Equals("CT", StringComparison.OrdinalIgnoreCase) && c.DeadlineSeconds > 0 && c.DeadlineSeconds <= 14.0) return 3;
        if (c.HasWeaponAwp || c.Role.Contains("Awp", StringComparison.OrdinalIgnoreCase) || c.Role.Contains("Sniper", StringComparison.OrdinalIgnoreCase)) return 4;
        if (c.Role.Contains("Support", StringComparison.OrdinalIgnoreCase)) return 5;
        return 6;
    }

    public static bool IsBombsiteCompatible(string routeBombsite, string roundPlanBombsite)
    {
        if (string.IsNullOrWhiteSpace(roundPlanBombsite) || string.IsNullOrWhiteSpace(routeBombsite)) return true;
        return string.Equals(routeBombsite.Trim(), roundPlanBombsite.Trim(), StringComparison.OrdinalIgnoreCase);
    }

    public FullTeamDepartureSchedule ScheduleFullTeamDeparture(
        int roundId,
        IReadOnlyList<TeamOpeningBotCandidate> allTeamBots,
        string roundPlanBombsite,
        int roundStartTick,
        int maxControlledBots,
        IReadOnlySet<string> certifiedAllowlist,
        IReadOnlySet<string>? excludedUtilityOnly = null)
    {
        if (allTeamBots == null || allTeamBots.Count == 0)
        {
            return new FullTeamDepartureSchedule { RoundId = roundId, RoundStartTick = roundStartTick };
        }

        var enriched = allTeamBots.Select(c =>
        {
            var inf = InferInitialCorridor(c);
            bool allow = c.IsEligibleForCanary &&
                         (excludedUtilityOnly == null || !excludedUtilityOnly.Contains(c.Destination)) &&
                         (certifiedAllowlist.Contains(c.Destination) || certifiedAllowlist.Contains(c.RouteId)) &&
                         (!c.HasC4 || IsBombsiteCompatible(c.Bombsite, roundPlanBombsite));
            return new { Candidate = c, Inference = inf, Priority = ComputePriority(c, roundPlanBombsite), Eligible = allow };
        })
        .OrderByDescending(x => x.Eligible ? 1 : 0)
        .ThenBy(x => x.Priority)
        .ThenBy(x => x.Candidate.SpawnDistance)
        .ThenBy(x => x.Candidate.BotSlot)
        .ToList();

        int canaryCount = 0;
        var modeBySlot = new Dictionary<int, TeamDepartureControlMode>();
        foreach (var item in enriched)
        {
            if (item.Eligible && canaryCount < maxControlledBots)
            {
                modeBySlot[item.Candidate.BotSlot] = TeamDepartureControlMode.CANARY_CONTROLLED;
                canaryCount++;
            }
            else
            {
                modeBySlot[item.Candidate.BotSlot] = TeamDepartureControlMode.UTILITY_AI_OBSERVED;
            }
        }

        // Organiza filas apenas quando CorridorConfidence == HIGH ou MEDIUM
        var groupQueues = new Dictionary<string, List<int>>(StringComparer.OrdinalIgnoreCase);
        var assignments = new List<FullTeamDepartureAssignment>(enriched.Count);

        // Ordena por prioridade geral de corredor (líderes primeiro, independente de Canary ou Utility)
        var byPriorityAll = enriched
            .OrderBy(x => x.Priority)
            .ThenBy(x => x.Candidate.SpawnDistance)
            .ThenBy(x => x.Candidate.BotSlot)
            .ToList();

        foreach (var item in byPriorityAll)
        {
            var c = item.Candidate;
            var inf = item.Inference;
            var mode = modeBySlot[c.BotSlot];
            string downstreamGroup = inf.Confidence != CorridorConfidence.LOW ? inf.Corridor : $"ISOLATED_{c.BotSlot}";
            // Separa InitialDepartureCorridor de DownstreamConflictGroup:
            // Bots TR que saem pelo T Spawn compartilham InitialDepartureCorridor = T_SPAWN_EXIT mesmo com grupos posteriores distintos.
            string initialCorridor = (c.Team.Equals("T", StringComparison.OrdinalIgnoreCase) && inf.Confidence != CorridorConfidence.LOW)
                ? "T_SPAWN_EXIT"
                : downstreamGroup;
            string groupKey = initialCorridor;

            if (!groupQueues.TryGetValue(groupKey, out var queue))
            {
                queue = new List<int>();
                groupQueues[groupKey] = queue;
            }

            int leaderSlot = queue.Count > 0 ? queue[0] : c.BotSlot;
            int? predSlot = queue.Count > 0 ? queue[^1] : null;
            int posIdx = queue.Count;
            queue.Add(c.BotSlot);

            int staggerMs = posIdx == 0 ? 0 : (mode == TeamDepartureControlMode.CANARY_CONTROLLED ? posIdx * 250 : Math.Min(MaxStaggerMs, posIdx * 250));
            int releaseTick = roundStartTick + (int)Math.Round(staggerMs * 64.0 / 1000.0);
            bool passiveHold = mode == TeamDepartureControlMode.UTILITY_AI_OBSERVED && predSlot.HasValue && staggerMs > 0;

            assignments.Add(new FullTeamDepartureAssignment
            {
                BotSlot = c.BotSlot,
                PlayerPseudonym = c.PlayerPseudonym,
                ControlMode = mode,
                Destination = c.Destination,
                Sector = c.Sector,
                Role = c.Role,
                RouteId = c.RouteId,
                ConflictGroup = groupKey,
                InitialDepartureCorridor = initialCorridor,
                DownstreamConflictGroup = downstreamGroup,
                QueueId = $"Q_{groupKey}",
                QueuePosition = posIdx,
                IsLeader = posIdx == 0,
                InferredCorridor = inf.Corridor,
                CorridorInferenceSource = inf.Source,
                CorridorConfidence = inf.Confidence,
                FirstNavArea = inf.FirstNavArea,
                FirstPortalId = inf.FirstPortalId,
                Priority = item.Priority,
                LeaderSlot = leaderSlot,
                PredecessorSlot = predSlot,
                PlannedReleaseTick = releaseTick,
                StaggerMs = staggerMs,
                PassiveHoldRequired = passiveHold,
                PassiveHoldMs = passiveHold ? Math.Min(MaxStaggerMs, staggerMs) : 0,
                FallbackToUtilityAi = mode == TeamDepartureControlMode.UTILITY_AI_OBSERVED,
                FallbackReason = mode == TeamDepartureControlMode.UTILITY_AI_OBSERVED ? (item.Eligible ? "UTILITY_AI_OBSERVED" : (string.IsNullOrEmpty(c.IneligibilityReason) ? "UNCERTIFIED_ROUTE" : c.IneligibilityReason)) : string.Empty,
            });
        }

        return new FullTeamDepartureSchedule
        {
            RoundId = roundId,
            RoundStartTick = roundStartTick,
            Assignments = assignments,
            BySlot = assignments.ToDictionary(a => a.BotSlot, a => a),
        };
    }

    public IReadOnlyList<TeamScheduledBotAssignment> Schedule(
        IReadOnlyList<TeamOpeningBotCandidate> candidates,
        string roundPlanBombsite,
        int roundStartTick,
        int maxConcurrentLeases,
        IReadOnlySet<string> certifiedAllowlist,
        IReadOnlySet<string>? excludedUtilityOnly = null)
    {
        if (candidates == null || candidates.Count == 0) return Array.Empty<TeamScheduledBotAssignment>();
        var ordered = candidates
            .Select(c => new { Candidate = c, Priority = ComputePriority(c, roundPlanBombsite) })
            .OrderBy(x => x.Priority)
            .ThenBy(x => x.Candidate.SpawnDistance)
            .ThenBy(x => x.Candidate.BotSlot)
            .ToList();

        var groupLeaders = new Dictionary<string, List<int>>(StringComparer.OrdinalIgnoreCase);
        var results = new List<TeamScheduledBotAssignment>(ordered.Count);
        int activeScheduled = 0;

        foreach (var item in ordered)
        {
            var c = item.Candidate;
            if (excludedUtilityOnly != null && excludedUtilityOnly.Contains(c.Destination))
            {
                results.Add(MakeFallback(c, item.Priority, roundStartTick, "UTILITY_AI_ONLY_EXCLUDED"));
                continue;
            }
            if (!certifiedAllowlist.Contains(c.Destination) && !certifiedAllowlist.Contains(c.RouteId))
            {
                results.Add(MakeFallback(c, item.Priority, roundStartTick, "UNCERTIFIED_ROUTE"));
                continue;
            }
            if (c.HasC4 && !IsBombsiteCompatible(c.Bombsite, roundPlanBombsite))
            {
                results.Add(MakeFallback(c, item.Priority, roundStartTick, "C4_BOMBSITE_INCOMPATIBLE"));
                continue;
            }
            if (activeScheduled >= maxConcurrentLeases)
            {
                results.Add(MakeFallback(c, item.Priority, roundStartTick, "MAX_CONCURRENT_LEASES_REACHED"));
                continue;
            }

            string grp = string.IsNullOrWhiteSpace(c.ConflictGroup) ? $"ISOLATED_{c.BotSlot}" : c.ConflictGroup;
            if (!groupLeaders.TryGetValue(grp, out var slotsInGroup))
            {
                slotsInGroup = new List<int>();
                groupLeaders[grp] = slotsInGroup;
            }

            int staggerMs = 0;
            int? predecessor = null;
            string chosenRoute = c.RouteId;
            string chosenGroup = grp;

            if (slotsInGroup.Count == 1)
            {
                predecessor = slotsInGroup[0];
                staggerMs = 250;
            }
            else if (slotsInGroup.Count >= 2)
            {
                if (!string.IsNullOrWhiteSpace(c.AlternativeRouteId) && certifiedAllowlist.Contains(c.AlternativeRouteId))
                {
                    chosenRoute = c.AlternativeRouteId;
                    chosenGroup = string.IsNullOrWhiteSpace(c.AlternativeConflictGroup) ? grp : c.AlternativeConflictGroup;
                    staggerMs = 0;
                }
                else
                {
                    results.Add(MakeFallback(c, item.Priority, roundStartTick, "CONFLICT_NO_ALTERNATIVE"));
                    continue;
                }
            }

            slotsInGroup.Add(c.BotSlot);
            activeScheduled++;
            int releaseTick = roundStartTick + (int)Math.Round(staggerMs * 64.0 / 1000.0);

            results.Add(new TeamScheduledBotAssignment
            {
                BotSlot = c.BotSlot,
                PlayerPseudonym = c.PlayerPseudonym,
                Team = c.Team,
                Role = c.Role,
                Destination = c.Destination,
                Sector = c.Sector,
                Bombsite = c.Bombsite,
                RouteId = chosenRoute,
                ConflictGroup = chosenGroup,
                Priority = item.Priority,
                PlannedReleaseTick = releaseTick,
                PredecessorSlot = predecessor,
                StaggerMs = Math.Clamp(staggerMs, 0, MaxStaggerMs),
                FallbackToUtilityAi = false,
                FallbackReason = string.Empty,
                HasC4 = c.HasC4,
            });
        }

        return results;
    }

    private static TeamScheduledBotAssignment MakeFallback(TeamOpeningBotCandidate c, int priority, int roundStartTick, string reason) =>
        new()
        {
            BotSlot = c.BotSlot,
            PlayerPseudonym = c.PlayerPseudonym,
            Team = c.Team,
            Role = c.Role,
            Destination = c.Destination,
            Sector = c.Sector,
            Bombsite = c.Bombsite,
            RouteId = c.RouteId,
            ConflictGroup = c.ConflictGroup,
            Priority = priority,
            PlannedReleaseTick = roundStartTick,
            PredecessorSlot = null,
            StaggerMs = 0,
            FallbackToUtilityAi = true,
            FallbackReason = reason,
            HasC4 = c.HasC4,
        };
}
