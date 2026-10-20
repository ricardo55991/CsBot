using System.Reflection;
using System.Text.Json;
using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class MapProfileManager
{
    private Dictionary<string, TacticalSpot> _spotsById = new(StringComparer.OrdinalIgnoreCase);
    private readonly object _profileLock = new();
    private readonly Random _random = new();

    public MapProfile CurrentProfile { get; private set; } = new();

    public void LoadProfile(string mapName, string? pluginDir = null)
    {
        string cleanMap = mapName.ToLowerInvariant().Trim();
        string fileName = $"{cleanMap}.json";
        string filePath = string.Empty;

        var candidatePaths = new List<string>();

        if (!string.IsNullOrEmpty(pluginDir))
        {
            candidatePaths.Add(Path.Combine(pluginDir, "MapProfiles", fileName));
            candidatePaths.Add(Path.Combine(pluginDir, fileName));
        }

        string assemblyDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
        if (!string.IsNullOrEmpty(assemblyDir))
        {
            candidatePaths.Add(Path.Combine(assemblyDir, "MapProfiles", fileName));
            candidatePaths.Add(Path.Combine(assemblyDir, fileName));
        }

        foreach (var p in candidatePaths)
        {
            if (File.Exists(p))
            {
                filePath = p;
                break;
            }
        }

        if (File.Exists(filePath))
        {
            try
            {
                string json = File.ReadAllText(filePath);
                var profile = JsonSerializer.Deserialize<MapProfile>(json);
                if (profile != null && profile.Spots.Count > 0)
                {
                    var newSpots = new Dictionary<string, TacticalSpot>(StringComparer.OrdinalIgnoreCase);
                    foreach (var spot in profile.Spots)
                    {
                        newSpots[spot.Id] = spot;
                    }

                    lock (_profileLock)
                    {
                        CurrentProfile = profile;
                        _spotsById = newSpots;
                    }

                    Server.PrintToConsole($"[MapProfileManager] Perfil universal '{profile.FriendlyName}' carregado ({newSpots.Count} spots, {profile.Chokepoints.Count} chokepoints).");
                    return;
                }
            }
            catch (Exception ex)
            {
                Server.PrintToConsole($"[MapProfileManager] Erro ao ler perfil '{fileName}': {ex.Message}. Carregando perfil de contingência.");
            }
        }

        // Se o mapa não tiver um JSON específico, gera um perfil padrão genérico (Fallback Universal)
        var fallbackProfile = GenerateUniversalFallbackProfile(cleanMap);
        var fallbackSpots = new Dictionary<string, TacticalSpot>(StringComparer.OrdinalIgnoreCase);
        foreach (var spot in fallbackProfile.Spots)
        {
            fallbackSpots[spot.Id] = spot;
        }

        lock (_profileLock)
        {
            CurrentProfile = fallbackProfile;
            _spotsById = fallbackSpots;
        }

        Server.PrintToConsole($"[MapProfileManager] Perfil genérico universal ativado para '{cleanMap}' ({fallbackSpots.Count} spots).");
    }

    public TacticalSpot? GetSpotById(string? id)
    {
        if (string.IsNullOrEmpty(id)) return null;
        lock (_profileLock)
        {
            return _spotsById.TryGetValue(id, out var spot) ? spot : null;
        }
    }

    public List<TacticalSpot> GetSpotsForSector(string sector, string side)
    {
        lock (_profileLock)
        {
            return _spotsById.Values
                .Where(s => s.Sector.Equals(sector, StringComparison.OrdinalIgnoreCase) &&
                           (s.Side.Equals(side, StringComparison.OrdinalIgnoreCase) || s.Side.Equals("ANY", StringComparison.OrdinalIgnoreCase)))
                .ToList();
        }
    }

    public List<TacticalSpot> GetSpotsForTeam(string side)
    {
        lock (_profileLock)
        {
            return _spotsById.Values
                .Where(s => s.Side.Equals(side, StringComparison.OrdinalIgnoreCase) || s.Side.Equals("ANY", StringComparison.OrdinalIgnoreCase))
                .ToList();
        }
    }

    public TacticalSpot? PickRandomSpotForSector(string sector, string side)
    {
        var spots = GetSpotsForSector(sector, side);
        if (spots.Count == 0)
        {
            spots = GetSpotsForTeam(side);
        }
        return spots.Count > 0 ? spots[_random.Next(spots.Count)] : null;
    }

    public TacticalSpot? GetFallbackSpot(string currentSpotId)
    {
        TacticalSpot? current = null;
        lock (_profileLock)
        {
            if (_spotsById.TryGetValue(currentSpotId, out var found))
            {
                current = found;
            }
        }

        if (current != null && !string.IsNullOrEmpty(current.FallbackSpotId))
        {
            return GetSpotById(current.FallbackSpotId);
        }

        if (current != null)
        {
            string defaultSafeId = current.Side == "CT" ? "ct_spawn_safe" : "tr_spawn_safe";
            return GetSpotById(defaultSafeId);
        }

        return null;
    }

    public MapChokepoint? FindChokepointAt(float x, float y, float z)
    {
        foreach (var cp in CurrentProfile.Chokepoints)
        {
            float dx = x - cp.X;
            float dy = y - cp.Y;
            float dz = z - cp.Z;
            float distSq = (dx * dx) + (dy * dy) + (dz * dz);
            if (distSq <= (cp.Radius * cp.Radius))
            {
                return cp;
            }
        }
        return null;
    }

    public MapChokepoint? GetNearestChokepoint(Vector pos)
    {
        MapChokepoint? nearest = null;
        float minDistSq = float.MaxValue;
        foreach (var cp in CurrentProfile.Chokepoints)
        {
            float dx = pos.X - cp.X;
            float dy = pos.Y - cp.Y;
            float dz = pos.Z - cp.Z;
            float distSq = (dx * dx) + (dy * dy) + (dz * dz);
            if (distSq < minDistSq)
            {
                minDistSq = distSq;
                nearest = cp;
            }
        }
        return nearest;
    }

    public MapChokepoint? FindChokepointByNameOrSynonym(string query)
    {
        string q = query.Trim().ToLowerInvariant();
        foreach (var cp in CurrentProfile.Chokepoints)
        {
            if (cp.Id.Equals(q, StringComparison.OrdinalIgnoreCase) ||
                cp.Name.ToLowerInvariant().Contains(q))
            {
                return cp;
            }
            if (cp.Synonyms.Any(s => s.Equals(q, StringComparison.OrdinalIgnoreCase) || q.Contains(s)))
            {
                return cp;
            }
        }
        return null;
    }

    public string ResolveVoiceSynonym(string query)
    {
        string q = query.Trim().ToLowerInvariant();
        if (CurrentProfile.VoiceSynonyms.TryGetValue(q, out var target))
        {
            return target;
        }
        foreach (var kvp in CurrentProfile.VoiceSynonyms)
        {
            if (q.Contains(kvp.Key.ToLowerInvariant()))
            {
                return kvp.Value;
            }
        }
        return query;
    }

    public Dictionary<int, TacticalSpot> GenerateEnemyTeamSetup(List<CCSPlayerController> enemyBots, CsTeam enemyTeam)
    {
        var result = new Dictionary<int, TacticalSpot>();
        if (enemyBots.Count == 0) return result;

        bool isCt = enemyTeam == CsTeam.CounterTerrorist;

        if (isCt)
        {
            var aSpots = GetSpotsForSector("Bombsite A", "CT").OrderBy(_ => _random.Next()).ToList();
            var midSpots = GetSpotsForSector("Mid", "CT").OrderBy(_ => _random.Next()).ToList();
            var bSpots = GetSpotsForSector("Bombsite B", "CT").OrderBy(_ => _random.Next()).ToList();

            var assignedSpots = new List<TacticalSpot>();

            if (aSpots.Count >= 2)
            {
                assignedSpots.Add(aSpots[0]);
                assignedSpots.Add(aSpots[1]);
            }
            else if (aSpots.Count == 1) assignedSpots.Add(aSpots[0]);

            if (midSpots.Count >= 1) assignedSpots.Add(midSpots[0]);

            if (bSpots.Count >= 2)
            {
                assignedSpots.Add(bSpots[0]);
                assignedSpots.Add(bSpots[1]);
            }
            else if (bSpots.Count == 1) assignedSpots.Add(bSpots[0]);

            for (int i = 0; i < enemyBots.Count && i < assignedSpots.Count; i++)
            {
                result[enemyBots[i].Slot] = assignedSpots[i];
            }
        }
        else // TR
        {
            List<TacticalSpot> trSpots;
            lock (_profileLock)
            {
                trSpots = _spotsById.Values
                    .Where(s => s.Side == "TR" && (s.Id.StartsWith("tr_staging_") || s.Id.Contains("staging")))
                    .OrderBy(_ => _random.Next())
                    .ToList();
            }

            for (int i = 0; i < enemyBots.Count && i < trSpots.Count; i++)
            {
                result[enemyBots[i].Slot] = trSpots[i];
            }
        }

        return result;
    }

    public TacticalSpot? GetMatchingSpotForOrder(BotRole role, string targetArea, CsTeam team, bool isStaging)
    {
        string side = team == CsTeam.CounterTerrorist ? "CT" : "TR";
        string normalizedArea = targetArea.ToLowerInvariant();

        string sector = normalizedArea switch
        {
            var s when s.Contains("a") || s.Contains("rampa") || s.Contains("palacio") || s.Contains("fundo") || s.Contains("areia") => "Bombsite A",
            var s when s.Contains("b") || s.Contains("tapete") || s.Contains("van") || s.Contains("banana") || s.Contains("escuro") => "Bombsite B",
            _ => "Mid"
        };

        List<TacticalSpot> matching;
        lock (_profileLock)
        {
            matching = _spotsById.Values
                .Where(s => s.Sector.Equals(sector, StringComparison.OrdinalIgnoreCase) &&
                           (s.Side.Equals(side, StringComparison.OrdinalIgnoreCase) || s.Side.Equals("ANY", StringComparison.OrdinalIgnoreCase)))
                .ToList();

            if (side == "TR")
            {
                var filtered = matching.Where(s => isStaging ? s.Id.Contains("staging") : (s.Id.Contains("exec") || s.Id.Contains("plant"))).ToList();
                if (filtered.Count > 0) matching = filtered;
            }

            if (matching.Count == 0)
            {
                matching = _spotsById.Values.Where(s => s.Side.Equals(side, StringComparison.OrdinalIgnoreCase)).ToList();
            }
        }

        if (matching.Count == 0) return null;

        if (role == BotRole.AWPer)
        {
            var awpSpot = matching.FirstOrDefault(s => s.Id.Contains("window") || s.Id.Contains("ticket") || s.Id.Contains("car") || s.Id.Contains("doors"));
            if (awpSpot != null) return awpSpot;
        }

        if (role == BotRole.EntryFragger)
        {
            var entrySpot = matching.FirstOrDefault(s => s.RecommendedStance == EngagementStance.AGGRESSIVE_POKE || s.IsOffAngle);
            if (entrySpot != null) return entrySpot;
        }

        if (role == BotRole.Anchor)
        {
            var anchorSpot = matching.FirstOrDefault(s => s.RecommendedStance == EngagementStance.PASSIVE_HOLD);
            if (anchorSpot != null) return anchorSpot;
        }

        return matching[_random.Next(matching.Count)];
    }

    private MapProfile GenerateUniversalFallbackProfile(string mapName)
    {
        var profile = new MapProfile
        {
            MapName = mapName,
            FriendlyName = mapName.ToUpperInvariant()
        };

        // Adiciona chokepoints e spots genéricos universais
        profile.Chokepoints.Add(new MapChokepoint
        {
            Id = "chokepoint_a",
            Name = "Entrada Bombsite A",
            Sector = "Bombsite A",
            AssociatedBomb = "A",
            X = -1000.0f,
            Y = -400.0f,
            Z = -160.0f,
            Radius = 400.0f,
            Synonyms = new() { "a", "bomb a" }
        });

        profile.Chokepoints.Add(new MapChokepoint
        {
            Id = "chokepoint_b",
            Name = "Entrada Bombsite B",
            Sector = "Bombsite B",
            AssociatedBomb = "B",
            X = -1500.0f,
            Y = -200.0f,
            Z = -160.0f,
            Radius = 400.0f,
            Synonyms = new() { "b", "bomb b" }
        });

        // Spots padrão
        profile.Spots.Add(new TacticalSpot { Id = "ct_a_default", Name = "Defesa A Padrão", Sector = "Bombsite A", Side = "CT", X = -1200, Y = -400, Z = -160, RecommendedStance = EngagementStance.PASSIVE_HOLD });
        profile.Spots.Add(new TacticalSpot { Id = "ct_b_default", Name = "Defesa B Padrão", Sector = "Bombsite B", Side = "CT", X = -1600, Y = -200, Z = -160, RecommendedStance = EngagementStance.PASSIVE_HOLD });
        profile.Spots.Add(new TacticalSpot { Id = "ct_mid_default", Name = "Controle Meio", Sector = "Mid", Side = "CT", X = -900, Y = -800, Z = -160, RecommendedStance = EngagementStance.JIGGLE_INFO });
        profile.Spots.Add(new TacticalSpot { Id = "tr_staging_default", Name = "Staging TR", Sector = "Mid", Side = "TR", X = 400, Y = -800, Z = -160, RecommendedStance = EngagementStance.PASSIVE_HOLD });
        profile.Spots.Add(new TacticalSpot { Id = "tr_exec_a_default", Name = "Execução A", Sector = "Bombsite A", Side = "TR", X = -1100, Y = -350, Z = -160, RecommendedStance = EngagementStance.AGGRESSIVE_POKE });
        profile.Spots.Add(new TacticalSpot { Id = "tr_exec_b_default", Name = "Execução B", Sector = "Bombsite B", Side = "TR", X = -1500, Y = -150, Z = -160, RecommendedStance = EngagementStance.AGGRESSIVE_POKE });

        return profile;
    }
}
