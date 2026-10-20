using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

/// <summary>
/// Provedor unificado de micro-posições táticas.
/// Delega para o MapProfileManager para evitar duplicação em memória (O-02).
/// </summary>
public class TacticalSpotsManager
{
    private readonly MapProfileManager _mapProfileManager;

    public TacticalSpotsManager(MapProfileManager mapProfileManager)
    {
        _mapProfileManager = mapProfileManager;
    }

    public void LoadSpots(string mapName, string? pluginDir = null)
    {
        _mapProfileManager.LoadProfile(mapName, pluginDir);
    }

    public TacticalSpot? GetSpotById(string? id) => _mapProfileManager.GetSpotById(id);

    public List<TacticalSpot> GetSpotsForSector(string sector, string side) => _mapProfileManager.GetSpotsForSector(sector, side);

    public List<TacticalSpot> GetSpotsForTeam(string side) => _mapProfileManager.GetSpotsForTeam(side);

    public TacticalSpot? GetFallbackSpot(string currentSpotId) => _mapProfileManager.GetFallbackSpot(currentSpotId);

    public Dictionary<int, TacticalSpot> GenerateEnemyTeamSetup(List<CCSPlayerController> enemyBots, CsTeam enemyTeam) =>
        _mapProfileManager.GenerateEnemyTeamSetup(enemyBots, enemyTeam);

    public TacticalSpot? GetMatchingSpotForOrder(BotRole role, string targetArea, CsTeam team, bool isStaging) =>
        _mapProfileManager.GetMatchingSpotForOrder(role, targetArea, team, isStaging);
}
