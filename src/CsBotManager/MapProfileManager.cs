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

    public void SetSpotsForTesting(IEnumerable<TacticalSpot> spots)
    {
        lock (_profileLock)
        {
            _spotsById = spots.ToDictionary(s => s.Id, s => s, StringComparer.OrdinalIgnoreCase);
        }
    }

    public void LoadProfile(string? mapName, string? pluginDir = null)
    {
        string cleanMap = string.IsNullOrWhiteSpace(mapName) ? "de_mirage" : mapName.ToLowerInvariant().Trim();
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

    public MapPlantZone? GetPlantZone(string? site)
    {
        if (string.IsNullOrWhiteSpace(site)) return null;
        lock (_profileLock)
        {
            if (CurrentProfile.PlantZones != null && CurrentProfile.PlantZones.TryGetValue(site.Trim(), out var zone))
            {
                return zone;
            }
            // Fallback determinístico se não estiver explícito no profile carregado
            if (site.Equals("A", StringComparison.OrdinalIgnoreCase))
            {
                return new MapPlantZone
                {
                    Center = new MapVector3 { X = -400.0f, Y = -2100.0f, Z = -170.0f },
                    BoundsMin = new MapVector3 { X = -650.0f, Y = -2400.0f, Z = -220.0f },
                    BoundsMax = new MapVector3 { X = -150.0f, Y = -1800.0f, Z = -120.0f },
                    Radius2D = 380.0f
                };
            }
            if (site.Equals("B", StringComparison.OrdinalIgnoreCase))
            {
                return new MapPlantZone
                {
                    Center = new MapVector3 { X = -1800.0f, Y = 50.0f, Z = -160.0f },
                    BoundsMin = new MapVector3 { X = -2200.0f, Y = -200.0f, Z = -220.0f },
                    BoundsMax = new MapVector3 { X = -1400.0f, Y = 300.0f, Z = -120.0f },
                    Radius2D = 420.0f
                };
            }
            return null;
        }
    }

    public MapPlantZone? GetPlantZone(BombsiteTarget site)
    {
        return site switch
        {
            BombsiteTarget.A => GetPlantZone("A"),
            BombsiteTarget.B => GetPlantZone("B"),
            _ => null
        };
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

    public IReadOnlyList<MapChokepoint> GetChokepoints() => CurrentProfile.Chokepoints;

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

    public TacticalSpot? ResolveBestSpot(
        BotRole role,
        BombsiteTarget targetSite,
        TacticalSpotUsage desiredUsage,
        CsTeam team,
        Vector botPosition,
        HashSet<string>? blacklistedSpotIds = null,
        HashSet<string>? occupiedSpotIds = null,
        List<CandidateSpotEvaluation>? outEvaluations = null)
    {
        string side = team == CsTeam.CounterTerrorist ? "CT" : "TR";
        List<TacticalSpot> spots;
        lock (_profileLock)
        {
            spots = _spotsById.Values.ToList();
        }

        if (spots.Count == 0) return null;

        TacticalSpot? bestSpot = null;
        float bestScore = float.NegativeInfinity;

        foreach (var spot in spots)
        {
            float score = 0f;
            var sb = new List<string>();

            // 1. Blacklist check
            bool isBlacklisted = blacklistedSpotIds != null && blacklistedSpotIds.Contains(spot.Id);
            if (isBlacklisted)
            {
                score -= 1000f;
                sb.Add("Blacklisted(-1000)");
            }

            // 2. Side matching
            if (!spot.Side.Equals("ANY", StringComparison.OrdinalIgnoreCase) &&
                !spot.Side.Equals(side, StringComparison.OrdinalIgnoreCase))
            {
                score -= 500f;
                sb.Add($"WrongSide:{spot.Side}(-500)");
            }
            else
            {
                score += 30f;
                sb.Add("SideMatch(+30)");
            }

            // 3. Bombsite Target matching
            var spotSite = PresetSpatialValidator.DetermineSpotBombsiteTarget(spot);
            if (targetSite != BombsiteTarget.None && targetSite != BombsiteTarget.Dynamic)
            {
                if (spotSite == targetSite)
                {
                    score += 100f;
                    sb.Add($"SiteMatch:{targetSite}(+100)");
                }
                else if (spotSite != BombsiteTarget.None && spotSite != BombsiteTarget.Mid)
                {
                    score -= 150f;
                    sb.Add($"WrongSite:{spotSite}vs{targetSite}(-150)");
                }
                else if (spotSite == BombsiteTarget.Mid && targetSite == BombsiteTarget.Mid)
                {
                    score += 80f;
                    sb.Add("MidMatch(+80)");
                }
            }

            // 4. Usage matching
            if (desiredUsage == TacticalSpotUsage.Staging)
            {
                if ((spot.Usage & SpotUsage.Staging) != 0 || spot.Id.Contains("staging", StringComparison.OrdinalIgnoreCase))
                {
                    score += 60f;
                    sb.Add("StagingUsage(+60)");
                }
            }
            else if (desiredUsage == TacticalSpotUsage.Execute)
            {
                if ((spot.Usage & (SpotUsage.Execute | SpotUsage.Plant)) != 0 ||
                    spot.Id.Contains("exec", StringComparison.OrdinalIgnoreCase) ||
                    spot.Id.Contains("plant", StringComparison.OrdinalIgnoreCase))
                {
                    score += 60f;
                    sb.Add("ExecuteUsage(+60)");
                }
            }
            else if (desiredUsage == TacticalSpotUsage.Retake)
            {
                if ((spot.Usage & SpotUsage.Retake) != 0 || spot.Id.Contains("retake", StringComparison.OrdinalIgnoreCase))
                {
                    score += 60f;
                    sb.Add("RetakeUsage(+60)");
                }
            }
            else if (desiredUsage == TacticalSpotUsage.Lurk)
            {
                if ((spot.Usage & SpotUsage.Lurk) != 0 || spot.Id.Contains("lurk", StringComparison.OrdinalIgnoreCase))
                {
                    score += 60f;
                    sb.Add("LurkUsage(+60)");
                }
            }

            // 5. BotRole matching
            if (spot.AllowedRoles.Contains(role))
            {
                score += 40f;
                sb.Add($"AllowedRole:{role}(+40)");
            }
            if (role == BotRole.AWPer && (spot.Id.Contains("window") || spot.Id.Contains("ticket") || spot.Id.Contains("car") || spot.Id.Contains("doors")))
            {
                score += 50f;
                sb.Add("AwpVantage(+50)");
            }
            if (role == BotRole.EntryFragger && (spot.RecommendedStance == EngagementStance.AGGRESSIVE_POKE || spot.IsOffAngle))
            {
                score += 35f;
                sb.Add("EntryAggressive(+35)");
            }
            if (role == BotRole.Anchor && spot.RecommendedStance == EngagementStance.PASSIVE_HOLD)
            {
                score += 35f;
                sb.Add("AnchorHold(+35)");
            }

            // 6. Occupancy penalty
            bool isOccupied = occupiedSpotIds != null && occupiedSpotIds.Contains(spot.Id);
            if (isOccupied)
            {
                score -= 80f;
                sb.Add("OccupiedPenalty(-80)");
            }

            // 7. Distance scoring (proximidade razoável)
            float dx = spot.X - botPosition.X;
            float dy = spot.Y - botPosition.Y;
            float dist2D = MathF.Sqrt(dx * dx + dy * dy);
            float distScore = Math.Clamp(60f - (dist2D / 60f), -30f, 30f);
            score += distScore;
            sb.Add($"Dist:{dist2D:F0}u({distScore:F1})");

            string breakdown = string.Join("; ", sb);

            outEvaluations?.Add(new CandidateSpotEvaluation(
                SpotId: spot.Id,
                SpotName: spot.Name,
                TargetSite: spotSite,
                Usage: desiredUsage,
                Score: score,
                IsBlacklisted: isBlacklisted,
                IsOccupied: isOccupied,
                DistanceToBot: dist2D,
                ScoreBreakdown: breakdown));

            if (score > bestScore)
            {
                bestScore = score;
                bestSpot = spot;
            }
        }

        return bestSpot;
    }

    public TacticalSpot? GetMatchingSpotForOrder(BotRole role, string targetArea, CsTeam team, bool isStaging)
    {
        BombsiteTarget siteTarget = BombsiteTarget.None;
        if (!BombsiteParser.TryParseBombsiteTarget(targetArea, out siteTarget))
        {
            string clean = targetArea.Trim().ToLowerInvariant();
            if (clean.Contains("rampa") || clean.Contains("palacio") || clean.Contains("fundo") || clean.Contains("areia") || clean.Contains("cabecinha") || clean.Contains("tetris"))
            {
                siteTarget = BombsiteTarget.A;
            }
            else if (clean.Contains("tapete") || clean.Contains("van") || clean.Contains("banana") || clean.Contains("apartments") || clean.Contains("catwalk"))
            {
                siteTarget = BombsiteTarget.B;
            }
            else if (clean.Contains("mid") || clean.Contains("meio") || clean.Contains("top mid") || clean.Contains("connector") || clean.Contains("window"))
            {
                siteTarget = BombsiteTarget.Mid;
            }
        }

        var desiredUsage = isStaging ? TacticalSpotUsage.Staging : TacticalSpotUsage.Execute;
        return ResolveBestSpot(role, siteTarget, desiredUsage, team, new Vector(0, 0, 0));
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
