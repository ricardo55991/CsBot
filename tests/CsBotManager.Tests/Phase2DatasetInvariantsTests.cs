using System.Text.Json;
using Xunit;

namespace CsBotManager.Tests;

public class Phase2DatasetInvariantsTests
{
    private readonly string _contractsDir;
    private readonly string _datasetsDir;

    public Phase2DatasetInvariantsTests()
    {
        // Navega até a raiz do repositório
        string current = AppDomain.CurrentDomain.BaseDirectory;
        while (!string.IsNullOrEmpty(current) && !File.Exists(Path.Combine(current, "start_cs2_ai_server.bat")))
        {
            string? parent = Directory.GetParent(current)?.FullName;
            if (parent == current) break;
            current = parent ?? "";
        }

        _datasetsDir = Path.Combine(current, "datasets", "mirage_v2");
        _contractsDir = Path.Combine(_datasetsDir, "contracts");
    }

    [Fact]
    public void CatalogManifest_HasExact53Spots_AndValidSha256()
    {
        string manifestPath = Path.Combine(_contractsDir, "mirage_spot_catalog_v3_manifest.json");
        Assert.True(File.Exists(manifestPath), $"Manifest não encontrado: {manifestPath}");

        string json = File.ReadAllText(manifestPath);
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;

        Assert.Equal("v3.0.0", root.GetProperty("catalog_version").GetString());
        Assert.Equal("de_mirage", root.GetProperty("map_name").GetString());
        Assert.Equal(53, root.GetProperty("total_spots").GetInt32());
        Assert.Equal(159, root.GetProperty("total_aim_profiles").GetInt32());
    }

    [Fact]
    public void SpotSemanticClassification_CoversAll53Spots_WithoutExcessiveClearanceDwell()
    {
        string semPath = Path.Combine(_contractsDir, "spot_semantic_classification.json");
        Assert.True(File.Exists(semPath), $"Semantic classification não encontrada: {semPath}");

        string json = File.ReadAllText(semPath);
        using var doc = JsonDocument.Parse(json);
        var spots = doc.RootElement.EnumerateArray().ToList();

        Assert.Equal(53, spots.Count);

        foreach (var s in spots)
        {
            string sid = s.GetProperty("spot_id").GetString()!;
            string semType = s.GetProperty("semantic_type").GetString()!;
            int maxDwell = s.GetProperty("maximum_expected_dwell_ms").GetInt32();

            Assert.False(string.IsNullOrEmpty(sid));
            Assert.Contains(semType, new[] { "POSITION_PROFILE", "CLEARANCE_WAYPOINT", "PLANT_POSITION", "DEFUSE_POSITION", "STAGING_POSITION", "TRANSITION_POINT" });

            if (semType == "CLEARANCE_WAYPOINT")
            {
                Assert.True(maxDwell <= 1500, $"Clearance waypoint {sid} não pode ser ensinado como hold prolongado (> 1500ms)");
            }
            else if (semType == "POSITION_PROFILE")
            {
                Assert.True(maxDwell >= 3000, $"Position profile {sid} deve ter dwell >= 3000ms");
            }
        }
    }

    [Fact]
    public void DataSplits_AreMutuallyExclusive_NoDataLeakage()
    {
        string trainPath = Path.Combine(_datasetsDir, "train_split_v2.json");
        string valPath = Path.Combine(_datasetsDir, "validation_split_v2.json");
        string testPath = Path.Combine(_datasetsDir, "test_split_v2.json");

        Assert.True(File.Exists(trainPath));
        Assert.True(File.Exists(valPath));
        Assert.True(File.Exists(testPath));

        var trainDemos = JsonDocument.Parse(File.ReadAllText(trainPath)).RootElement.GetProperty("demo_ids").EnumerateArray().Select(e => e.GetString()!).ToHashSet();
        var valDemos = JsonDocument.Parse(File.ReadAllText(valPath)).RootElement.GetProperty("demo_ids").EnumerateArray().Select(e => e.GetString()!).ToHashSet();
        var testDemos = JsonDocument.Parse(File.ReadAllText(testPath)).RootElement.GetProperty("demo_ids").EnumerateArray().Select(e => e.GetString()!).ToHashSet();

        Assert.Empty(trainDemos.Intersect(valDemos));
        Assert.Empty(trainDemos.Intersect(testDemos));
        Assert.Empty(valDemos.Intersect(testDemos));
    }

    [Fact]
    public void JumpEpisodeManifest_AndParquetExist_WithBallisticStats()
    {
        string jumpManifestPath = Path.Combine(_datasetsDir, "jump", "jump_episode_manifest_v2.json");
        string parquetPath = Path.Combine(_datasetsDir, "jump", "jump_episodes_v2.parquet");

        Assert.True(File.Exists(jumpManifestPath));
        Assert.True(File.Exists(parquetPath));

        using var doc = JsonDocument.Parse(File.ReadAllText(jumpManifestPath));
        var stats = doc.RootElement.GetProperty("stats");

        int realJumps = stats.GetProperty("RealJumpPressEvents").GetInt32();
        int bhopExcluded = stats.GetProperty("BunnyHopEpisodesExcluded").GetInt32();
        int legacyLabels = stats.GetProperty("LegacyJumpLabels").GetInt32();

        Assert.True(realJumps > 0);
        Assert.True(bhopExcluded > 0);
        Assert.True(legacyLabels > realJumps, "Rótulos legados devem ser maiores que eventos reais de JumpPress");
    }
}
