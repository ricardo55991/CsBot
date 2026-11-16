using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CounterStrikeSharp.API.Modules.Utils;
using CsBotManager;
using Xunit;

namespace CsBotManager.Tests;

public class V4_2_9_MirageV2ProfileTests
{
    private string GetMirageJsonPath()
    {
        string[] candidates = new[]
        {
            Path.Combine("src", "CsBotManager", "MapProfiles", "de_mirage.json"),
            Path.Combine("..", "..", "..", "..", "..", "src", "CsBotManager", "MapProfiles", "de_mirage.json"),
            Path.Combine("..", "..", "..", "..", "src", "CsBotManager", "MapProfiles", "de_mirage.json")
        };

        foreach (var candidate in candidates)
        {
            if (File.Exists(candidate))
                return candidate;
        }

        var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
        while (dir != null && !File.Exists(Path.Combine(dir.FullName, "src", "CsBotManager", "MapProfiles", "de_mirage.json")))
        {
            dir = dir.Parent;
        }
        if (dir != null)
        {
            return Path.Combine(dir.FullName, "src", "CsBotManager", "MapProfiles", "de_mirage.json");
        }

        throw new FileNotFoundException("de_mirage.json não foi encontrado.");
    }

    [Fact]
    public void Test01_DeMirageProfileVersionIs2()
    {
        string path = GetMirageJsonPath();
        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);

        Assert.True(doc.RootElement.TryGetProperty("map_profile_version", out var versionProp));
        Assert.True(versionProp.GetInt32() >= 2);
    }

    [Fact]
    public void Test02_All45SpotIdsAreUnique()
    {
        string path = GetMirageJsonPath();
        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);

        var spots = doc.RootElement.GetProperty("spots").EnumerateArray().ToList();
        Assert.True(spots.Count >= 45);

        var ids = spots.Select(s => s.GetProperty("id").GetString()).ToList();
        var uniqueIds = ids.Distinct().ToList();

        Assert.Equal(ids.Count, uniqueIds.Count);
    }

    [Fact]
    public void Test03_AllSpotsAreWithinPlayableBounds()
    {
        string path = GetMirageJsonPath();
        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);

        var bounds = MapPlayableBounds.GetBoundsForMap("de_mirage");

        foreach (var spot in doc.RootElement.GetProperty("spots").EnumerateArray())
        {
            string id = spot.GetProperty("id").GetString() ?? "";
            float x = spot.GetProperty("x").GetSingle();
            float y = spot.GetProperty("y").GetSingle();
            float z = spot.GetProperty("z").GetSingle();

            Assert.InRange(x, bounds.MinPlayableX, bounds.MaxPlayableX);
            Assert.InRange(y, bounds.MinPlayableY, bounds.MaxPlayableY);
            Assert.InRange(z, bounds.MinPlayableZ, bounds.MaxPlayableZ);
        }
    }

    [Fact]
    public void Test04_AllSpotsHaveValidTeamSideUsageAndAssociatedBombsite()
    {
        string path = GetMirageJsonPath();
        string json = File.ReadAllText(path);
        var profile = JsonSerializer.Deserialize<MapProfile>(json);
        Assert.NotNull(profile);
        Assert.True(profile.Spots.Count >= 45);

        var violations = new List<string>();

        foreach (var spot in profile.Spots)
        {
            // 1. Validação primária: TeamSide
            string side = (spot.Side ?? "").ToUpperInvariant();
            if (side != "CT" && side != "TR" && side != "ANY")
                violations.Add($"{spot.Id}: TeamSide inválido ({spot.Side})");
            if (spot.Id.StartsWith("ct_", StringComparison.OrdinalIgnoreCase) && side != "CT" && side != "ANY")
                violations.Add($"{spot.Id}: Spot ct_ com TeamSide={side}");
            if (spot.Id.StartsWith("tr_", StringComparison.OrdinalIgnoreCase) && side != "TR" && side != "ANY")
                violations.Add($"{spot.Id}: Spot tr_ com TeamSide={side}");

            // 2. Validação primária: Usage
            if (spot.Usage == SpotUsage.None)
                violations.Add($"{spot.Id}: Usage não pode ser SpotUsage.None");

            // 3. Validação primária: AssociatedBombsite
            string site = PresetSpatialValidator.DetermineSpotBombsite(spot);
            if (spot.Id.Contains("_retake_a_", StringComparison.OrdinalIgnoreCase))
            {
                if (site != "A")
                    violations.Add($"{spot.Id}: AssociatedBombsite esperado 'A', obtido '{site}'");
            }
            else if (spot.Id.Contains("_a_", StringComparison.OrdinalIgnoreCase) && site != "A")
                violations.Add($"{spot.Id}: AssociatedBombsite esperado 'A', obtido '{site}'");
            else if (spot.Id.Contains("_b_", StringComparison.OrdinalIgnoreCase) && site != "B")
                violations.Add($"{spot.Id}: AssociatedBombsite esperado 'B', obtido '{site}'");
            else if (spot.Id.Contains("_mid_", StringComparison.OrdinalIgnoreCase) && site != "Mid")
                violations.Add($"{spot.Id}: AssociatedBombsite esperado 'Mid', obtido '{site}'");
        }

        Assert.Empty(violations);
    }

    [Fact]
    public void Test04b_MirageSpecificSanityCheck_AllBombBSpotsHavePositiveY()
    {
        // Sanity check específico da geometria de de_mirage (não generalizável como invariante global para outros mapas)
        string path = GetMirageJsonPath();
        string json = File.ReadAllText(path);
        using var doc = JsonDocument.Parse(json);

        var violations = new List<string>();

        foreach (var spot in doc.RootElement.GetProperty("spots").EnumerateArray())
        {
            string id = spot.GetProperty("id").GetString() ?? "";
            string sector = spot.GetProperty("sector").GetString() ?? "";
            float y = spot.GetProperty("y").GetSingle();

            bool isMarket = id.Contains("kitchen") || id.Contains("market") || id.Contains("door") || id.Contains("jail");
            bool isB = id.Contains("_b_") || sector.Contains("Site B") || sector.Contains("Apartments B");
            if (isB && !isMarket && y < 0)
            {
                violations.Add($"{id} (Y={y})");
            }
        }

        Assert.Empty(violations);
    }

    [Fact]
    public void Test05_CtStandard212FormationSpacingExceeds150Units()
    {
        string path = GetMirageJsonPath();
        string json = File.ReadAllText(path);
        var profile = JsonSerializer.Deserialize<MapProfile>(json);
        Assert.NotNull(profile);

        var mgr = new MapProfileManager();
        mgr.LoadProfile("de_mirage", Path.GetDirectoryName(path));
        mgr.SetSpotsForTesting(profile.Spots);

        var plan = new TacticalPlan { TacticName = "Defesa Padrão 2-1-2 Equilibrada", TeamSide = CsTeam.CounterTerrorist };
        bool ok = TacticalOrderMaterializer.MaterializeCtStandard212Formation(plan, null, mgr, null, "TEST-SPACING");
        Assert.True(ok);

        var aDefenders = plan.CtFormationAssignments.Values.Where(a => a.AssignedSite == "A").ToList();
        Assert.Equal(2, aDefenders.Count);

        var spotA1 = mgr.GetSpotById(aDefenders[0].InitialSpot);
        var spotA2 = mgr.GetSpotById(aDefenders[1].InitialSpot);
        Assert.NotNull(spotA1);
        Assert.NotNull(spotA2);

        float distA = MathF.Sqrt(MathF.Pow(spotA1.X - spotA2.X, 2) + MathF.Pow(spotA1.Y - spotA2.Y, 2));
        Assert.True(distA >= 150f, $"Distância entre A1 e A2 deve ser >= 150u, obtido {distA:F1}u");

        var bDefenders = plan.CtFormationAssignments.Values.Where(a => a.AssignedSite == "B").ToList();
        Assert.Equal(2, bDefenders.Count);

        var spotB1 = mgr.GetSpotById(bDefenders[0].InitialSpot);
        var spotB2 = mgr.GetSpotById(bDefenders[1].InitialSpot);
        Assert.NotNull(spotB1);
        Assert.NotNull(spotB2);

        float distB = MathF.Sqrt(MathF.Pow(spotB1.X - spotB2.X, 2) + MathF.Pow(spotB1.Y - spotB2.Y, 2));
        Assert.True(distB >= 150f, $"Distância entre B1 e B2 deve ser >= 150u, obtido {distB:F1}u");
    }

    [Fact]
    public void Test06_PresetStartupAuditCompletesWithZeroMissingSpots()
    {
        string path = GetMirageJsonPath();
        string json = File.ReadAllText(path);
        var profile = JsonSerializer.Deserialize<MapProfile>(json);
        Assert.NotNull(profile);

        var mgr = new MapProfileManager();
        mgr.LoadProfile("de_mirage", Path.GetDirectoryName(path));
        mgr.SetSpotsForTesting(profile.Spots);

        var igl = new OllamaIglService();
        var audit = PresetSpatialValidator.RunStartupAudit(mgr, igl);

        Assert.Equal(0, audit.MissingSpots);
        Assert.True(audit.PresetsTotal > 0);
    }
}
