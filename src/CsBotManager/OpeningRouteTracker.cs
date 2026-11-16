using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;

namespace CsBotManager;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum OpeningRouteTerminationReason
{
    NONE,
    TARGET_REACHED,
    TACTICAL_REDIRECT,
    CONTACT_INTERRUPTION,
    PLAYER_DEATH,
    ROUND_END,
    TIMEOUT,
    INVALIDATED
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum OpeningRouteClassification
{
    PENDING,
    ON_TIME,
    LATE,
    TACTICAL_REDIRECT,
    CONTACT_INTERRUPTION,
    BLOCKED_BY_TEAMMATE,
    PLAYER_DEATH,
    NOT_REACHED,
    INVALID_ROUTE
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum PostOpeningRepathKind
{
    MIDROUND_REPATH,
    RECOVERY_REPATH,
    TACTICAL_ROTATION
}

public sealed class OpeningRouteState
{
    public int RoundId { get; init; }
    public string PlayerSlot { get; init; } = string.Empty;
    public int RawSlot { get; init; }
    public string Team { get; init; } = string.Empty;
    public string TargetSpotId { get; init; } = string.Empty;
    public float TargetX { get; init; }
    public float TargetY { get; init; }
    public float TargetZ { get; init; }
    public float SpotRadius { get; init; } = 90.0f;
    public int RequiredDwellTicks { get; init; } = 16; // ~0.25s a 64 ticks/s
    public double DeadlineSeconds { get; init; } = 15.0;

    public int StartTick { get; init; }
    public int FreezeEndTick { get; init; }
    public int TargetLockTick { get; init; }
    public int? ArrivalTick { get; set; }
    public double ElapsedSeconds { get; set; }
    public float InitialDistance { get; init; }
    public float TraveledDistance { get; set; }
    public float MinimumDistance { get; set; }
    public int DwellTicks { get; set; }
    public bool HadTeammateBlock { get; set; }
    public float LastX { get; set; }
    public float LastY { get; set; }
    public float LastZ { get; set; }

    // Telemetria Faca / Readiness (Seção 5, sem controlar bot)
    public string ActiveWeapon { get; set; } = string.Empty;
    public bool KnifeEquipped { get; set; }
    public int? WeaponSwitchTick { get; set; }
    public int? FirstThreatLineTick { get; set; }
    public int? FirstPossibleContactTick { get; set; }
    public int? FirstActualContactTick { get; set; }
    public float? DistanceRemainingAtWeaponSwitch { get; set; }

    public bool IsClosed { get; set; }
    public OpeningRouteTerminationReason TerminationReason { get; set; } = OpeningRouteTerminationReason.NONE;
    public OpeningRouteClassification Classification { get; set; } = OpeningRouteClassification.PENDING;
}

public sealed class OpeningRouteTracker
{
    private readonly Dictionary<(int RoundId, int RawSlot), OpeningRouteState> _openingRoutes = new();
    private readonly List<OpeningRouteState> _closedRoutes = new();
    private readonly Dictionary<PostOpeningRepathKind, int> _postOpeningRepathCounts = new()
    {
        [PostOpeningRepathKind.MIDROUND_REPATH] = 0,
        [PostOpeningRepathKind.RECOVERY_REPATH] = 0,
        [PostOpeningRepathKind.TACTICAL_ROTATION] = 0,
    };
    private readonly Dictionary<(int RoundId, int RawSlot), (string SpotId, PostOpeningRepathKind Kind)> _lastRegisteredSpotAndKind = new();
    private readonly Dictionary<(int RoundId, string PlayerSlot), int> _repathsByPlayerRound = new();
    private int _repeatedEventDuplicates = 0;
    private int _freezeEndTick = -1;
    private bool _inFreezeTime = true;
    private int _activeRoundId = 0;

    public IReadOnlyList<OpeningRouteState> ClosedRoutes => _closedRoutes;
    public IReadOnlyDictionary<PostOpeningRepathKind, int> PostOpeningRepathCounts => _postOpeningRepathCounts;
    public int UniqueMidroundRepaths => _postOpeningRepathCounts[PostOpeningRepathKind.MIDROUND_REPATH];
    public int UniqueRecoveryRepaths => _postOpeningRepathCounts[PostOpeningRepathKind.RECOVERY_REPATH];
    public int UniqueTacticalRotations => _postOpeningRepathCounts[PostOpeningRepathKind.TACTICAL_ROTATION];
    public int RepeatedEventDuplicates => _repeatedEventDuplicates;
    public IReadOnlyDictionary<(int RoundId, string PlayerSlot), int> RepathsByPlayerRound => _repathsByPlayerRound;
    public int TotalOpeningRoutesCreated => _openingRoutes.Count;
    public int ActiveOpenRoutes
    {
        get
        {
            int c = 0;
            foreach (var r in _openingRoutes.Values) if (!r.IsClosed) c++;
            return c;
        }
    }

    public void OnRoundStart(int roundId)
    {
        CloseAllOpenRoutes(roundId > 1 ? _activeRoundId : roundId, OpeningRouteTerminationReason.ROUND_END);
        _activeRoundId = roundId;
        _inFreezeTime = true;
        _freezeEndTick = -1;
    }

    public void OnFreezeTimeEnded(int tick)
    {
        _inFreezeTime = false;
        if (_freezeEndTick < 0) _freezeEndTick = tick;
    }

    public bool TryRegisterAssignment(
        int roundId,
        int rawSlot,
        string pseudonymizedSlot,
        string team,
        string spotId,
        float startX, float startY, float startZ,
        float targetX, float targetY, float targetZ,
        float spotRadius,
        int tick,
        bool isFreezeTime,
        PostOpeningRepathKind repathKind = PostOpeningRepathKind.MIDROUND_REPATH)
    {
        if (isFreezeTime || _inFreezeTime)
        {
            return false; // Regra estrita: freeze time excluído
        }

        var key = (roundId, rawSlot);
        if (_openingRoutes.TryGetValue(key, out var existing))
        {
            // Já existe 1 opening route para este jogador neste round!
            // Contabilizar apenas eventos únicos (mudança real de spot ou tipo de repath);
            // chamadas repetidas por tick para o mesmo spot/tipo vão para RepeatedEventDuplicates.
            if (_lastRegisteredSpotAndKind.TryGetValue(key, out var last)
                && string.Equals(last.SpotId, spotId, StringComparison.Ordinal)
                && last.Kind == repathKind)
            {
                _repeatedEventDuplicates++;
                return false;
            }

            _lastRegisteredSpotAndKind[key] = (spotId, repathKind);
            _postOpeningRepathCounts[repathKind] = _postOpeningRepathCounts.GetValueOrDefault(repathKind) + 1;
            var prKey = (roundId, pseudonymizedSlot);
            _repathsByPlayerRound[prKey] = _repathsByPlayerRound.GetValueOrDefault(prKey) + 1;

            if (!existing.IsClosed && repathKind == PostOpeningRepathKind.TACTICAL_ROTATION && existing.TargetSpotId != spotId)
            {
                CloseRoute(existing, tick, OpeningRouteTerminationReason.TACTICAL_REDIRECT, OpeningRouteClassification.TACTICAL_REDIRECT);
            }
            else if (!existing.IsClosed && repathKind == PostOpeningRepathKind.RECOVERY_REPATH)
            {
                existing.HadTeammateBlock = true;
            }
            return false;
        }

        float dist = MathF.Sqrt(
            (targetX - startX) * (targetX - startX) +
            (targetY - startY) * (targetY - startY) +
            (targetZ - startZ) * (targetZ - startZ));

        var state = new OpeningRouteState
        {
            RoundId = roundId,
            PlayerSlot = pseudonymizedSlot,
            RawSlot = rawSlot,
            Team = team,
            TargetSpotId = spotId,
            TargetX = targetX,
            TargetY = targetY,
            TargetZ = targetZ,
            SpotRadius = Math.Max(32.0f, spotRadius),
            StartTick = tick,
            FreezeEndTick = _freezeEndTick >= 0 ? _freezeEndTick : tick,
            TargetLockTick = tick,
            InitialDistance = dist,
            MinimumDistance = dist,
            LastX = startX,
            LastY = startY,
            LastZ = startZ,
        };
        _openingRoutes[key] = state;
        _lastRegisteredSpotAndKind[key] = (spotId, repathKind);
        return true;
    }

    public void UpdateTick(
        int roundId,
        int rawSlot,
        int tick,
        bool isAlive,
        float x, float y, float z,
        string activeWeapon,
        bool hasEnemyContact = false,
        bool hasThreatLine = false)
    {
        if (!_openingRoutes.TryGetValue((roundId, rawSlot), out var route) || route.IsClosed)
        {
            return;
        }

        if (!isAlive)
        {
            CloseRoute(route, tick, OpeningRouteTerminationReason.PLAYER_DEATH, OpeningRouteClassification.PLAYER_DEATH);
            return;
        }

        float stepDist = MathF.Sqrt((x - route.LastX) * (x - route.LastX) + (y - route.LastY) * (y - route.LastY) + (z - route.LastZ) * (z - route.LastZ));
        route.TraveledDistance += stepDist;
        route.LastX = x;
        route.LastY = y;
        route.LastZ = z;

        float remDist = MathF.Sqrt((route.TargetX - x) * (route.TargetX - x) + (route.TargetY - y) * (route.TargetY - y) + (route.TargetZ - z) * (route.TargetZ - z));
        if (remDist < route.MinimumDistance) route.MinimumDistance = remDist;

        bool isKnife = !string.IsNullOrEmpty(activeWeapon) &&
                       (activeWeapon.Contains("knife", StringComparison.OrdinalIgnoreCase) ||
                        activeWeapon.Contains("bayonet", StringComparison.OrdinalIgnoreCase));
        if (route.KnifeEquipped && !isKnife && route.WeaponSwitchTick == null)
        {
            route.WeaponSwitchTick = tick;
            route.DistanceRemainingAtWeaponSwitch = remDist;
        }
        route.ActiveWeapon = activeWeapon;
        route.KnifeEquipped = isKnife;

        if (hasThreatLine && route.FirstThreatLineTick == null) route.FirstThreatLineTick = tick;
        if (hasEnemyContact)
        {
            route.FirstPossibleContactTick ??= tick;
            route.FirstActualContactTick ??= tick;
            CloseRoute(route, tick, OpeningRouteTerminationReason.CONTACT_INTERRUPTION, OpeningRouteClassification.CONTACT_INTERRUPTION);
            return;
        }

        double elapsedSec = Math.Max(0.0, (tick - route.StartTick) / 64.0);
        route.ElapsedSeconds = elapsedSec;

        if (remDist <= route.SpotRadius)
        {
            route.DwellTicks++;
            if (route.DwellTicks >= route.RequiredDwellTicks)
            {
                route.ArrivalTick = tick;
                var cls = route.HadTeammateBlock
                    ? OpeningRouteClassification.BLOCKED_BY_TEAMMATE
                    : (elapsedSec <= route.DeadlineSeconds ? OpeningRouteClassification.ON_TIME : OpeningRouteClassification.LATE);
                CloseRoute(route, tick, OpeningRouteTerminationReason.TARGET_REACHED, cls);
                return;
            }
        }
        else
        {
            route.DwellTicks = 0;
        }

        if (elapsedSec > route.DeadlineSeconds * 2.0)
        {
            CloseRoute(route, tick, OpeningRouteTerminationReason.TIMEOUT, OpeningRouteClassification.NOT_REACHED);
        }
    }

    public void CloseAllOpenRoutes(int roundId, OpeningRouteTerminationReason reason, int tick = 0)
    {
        foreach (var route in _openingRoutes.Values)
        {
            if (!route.IsClosed && route.RoundId == roundId)
            {
                var cls = reason == OpeningRouteTerminationReason.INVALIDATED
                    ? OpeningRouteClassification.INVALID_ROUTE
                    : OpeningRouteClassification.NOT_REACHED;
                CloseRoute(route, tick > 0 ? tick : route.StartTick, reason, cls);
            }
        }
    }

    private void CloseRoute(OpeningRouteState route, int tick, OpeningRouteTerminationReason reason, OpeningRouteClassification cls)
    {
        if (route.IsClosed) return;
        route.IsClosed = true;
        route.TerminationReason = reason;
        route.Classification = cls;
        route.ElapsedSeconds = Math.Max(route.ElapsedSeconds, Math.Max(0.0, (tick - route.StartTick) / 64.0));
        _closedRoutes.Add(route);
    }

    public int ComputeAccountingResidue()
    {
        // Todo opening route criado deve estar exatamente em (ClosedRoutes) ou (ActiveOpenRoutes)
        return _openingRoutes.Count - (_closedRoutes.Count + ActiveOpenRoutes);
    }
}
