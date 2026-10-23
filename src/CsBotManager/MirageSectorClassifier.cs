using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public sealed class MirageSectorVolume
{
    public string SectorName { get; init; } = string.Empty;
    public string AssociatedBomb { get; init; } = "Mid"; // "A", "B", "Mid", "CT", "TR"
    public float MinX { get; init; }
    public float MaxX { get; init; }
    public float MinY { get; init; }
    public float MaxY { get; init; }
    public float MinZ { get; init; }
    public float MaxZ { get; init; }
    public int Priority { get; init; } = 10; // Menor = mais específico (desempate determinístico)
    public bool IsPlantZone { get; init; }

    public float CenterX => (MinX + MaxX) * 0.5f;
    public float CenterY => (MinY + MaxY) * 0.5f;
    public float CenterZ => (MinZ + MaxZ) * 0.5f;

    public bool Contains3D(float x, float y, float z)
    {
        return x >= MinX && x <= MaxX &&
               y >= MinY && y <= MaxY &&
               z >= MinZ && z <= MaxZ;
    }

    public float DistanceToVolume3D(float x, float y, float z)
    {
        float dx = x < MinX ? (MinX - x) : (x > MaxX ? (x - MaxX) : 0f);
        float dy = y < MinY ? (MinY - y) : (y > MaxY ? (y - MaxY) : 0f);
        float dz = z < MinZ ? (MinZ - z) : (z > MaxZ ? (z - MaxZ) : 0f);
        return MathF.Sqrt(dx * dx + dy * dy + dz * dz);
    }
}

public sealed class SectorClassificationResult
{
    public string SectorName { get; init; } = string.Empty;
    public string AssociatedBomb { get; init; } = "Mid";
    public bool IsPlantZone { get; init; }
    public float Confidence { get; init; } = 1.0f;
    public string Source { get; init; } = "3D_VOLUME";
}

/// <summary>
/// Classificador geográfico 3D completo e determinístico de `de_mirage` (Bug 6 & Bug 11 / Regra 6).
/// Combina `pawn.LastPlaceName` nativo da Source 2 com volumes 3D validados (X, Y e altura Z para Underpass vs Catwalk/Apartments)
/// e fallback de vizinhança contínua para que NENHUMA coordenada válida da Mirage caia em fallback genérico `"o Meio"` ou `"Em Trânsito"`.
/// </summary>
public static class MirageSectorClassifier
{
    private static readonly Dictionary<string, (string Sector, string Bomb, bool IsPlant)> NativePlaceMap = new(StringComparer.OrdinalIgnoreCase)
    {
        { "CTSpawn", ("CT Spawn", "CT", false) },
        { "TSpawn", ("TR Spawn", "TR", false) },
        { "BombsiteA", ("Bomb A", "A", true) },
        { "BombsiteB", ("Bomb B", "B", true) },
        { "PalaceInterior", ("Palácio A", "A", false) },
        { "PalaceAlley", ("Palácio A", "A", false) },
        { "TRamp", ("Rampa A", "A", false) },
        { "Scaffolding", ("Rampa A", "A", false) },
        { "TicketBooth", ("Ticket / CT", "A", false) },
        { "Stairs", ("Escadas A", "A", false) },
        { "Jungle", ("Jungle", "A", false) },
        { "Connector", ("Conector", "Mid", false) },
        { "TopOfMid", ("Top Mid", "Mid", false) },
        { "Middle", ("Meio", "Mid", false) },
        { "SnipersNest", ("Janela", "Mid", false) },
        { "Underpass", ("Underpass", "Mid", false) },
        { "Catwalk", ("Catwalk / Short", "Mid", false) },
        { "Apartments", ("Apartamentos B", "B", false) },
        { "BackAlley", ("Beco", "B", false) },
        { "House", ("Apartamentos B", "B", false) },
        { "Kitchen", ("Mercado / Kitchen", "B", false) },
        { "Market", ("Mercado / Kitchen", "B", false) },
        { "Shop", ("Mercado / Kitchen", "B", false) },
        { "Truck", ("Van", "B", false) },
        { "Courtyard", ("Bomb B", "B", false) },
        { "Balcony", ("Apartamentos B", "B", false) }
    };

    /// <summary>
    /// Volumes 3D calibrados com as coordenadas reais de CS2 `de_mirage` e `de_mirage.json`.
    /// Inclui separação vertical explícita (Z) para Underpass (`Z < -185`) vs Catwalk/Apartamentos (`Z >= -185`).
    /// </summary>
    public static readonly IReadOnlyList<MirageSectorVolume> Volumes = new List<MirageSectorVolume>
    {
        // 1. Zonas de Plant Reais (Prioridade Máxima = 1)
        new() { SectorName = "Bomb A", AssociatedBomb = "A", IsPlantZone = true, Priority = 1,
                MinX = -1360f, MaxX = -280f, MinY = -2350f, MaxY = -1880f, MinZ = -260f, MaxZ = -80f },
        new() { SectorName = "Bomb B", AssociatedBomb = "B", IsPlantZone = true, Priority = 1,
                MinX = -2150f, MaxX = -1420f, MinY = 250f, MaxY = 760f, MinZ = -240f, MaxZ = -40f },
        new() { SectorName = "Bomb B", AssociatedBomb = "B", IsPlantZone = true, Priority = 2,
                MinX = -1650f, MaxX = -1180f, MinY = -300f, MaxY = 120f, MinZ = -220f, MaxZ = -40f },

        // 2. Underpass / Rato (Camada Subterrânea: Z <= -185 tem prioridade 2 sobre Catwalk/Meio)
        new() { SectorName = "Underpass", AssociatedBomb = "Mid", IsPlantZone = false, Priority = 2,
                MinX = -1350f, MaxX = -350f, MinY = -1250f, MaxY = -200f, MinZ = -380f, MaxZ = -185f },

        // 3. Palácio A (Camada Elevada: Z >= -130 no quadrante SE/Leste do A)
        new() { SectorName = "Palácio A", AssociatedBomb = "A", IsPlantZone = false, Priority = 3,
                MinX = -650f, MaxX = 680f, MinY = -2550f, MaxY = -1350f, MinZ = -140f, MaxZ = 120f },
        new() { SectorName = "Palácio A", AssociatedBomb = "A", IsPlantZone = false, Priority = 4,
                MinX = -650f, MaxX = -100f, MinY = -750f, MaxY = -320f, MinZ = -135f, MaxZ = 80f },

        // 4. Rampa A / Caverna
        new() { SectorName = "Rampa A", AssociatedBomb = "A", IsPlantZone = false, Priority = 4,
                MinX = -520f, MaxX = 580f, MinY = -1850f, MaxY = -1050f, MinZ = -260f, MaxZ = -60f },
        new() { SectorName = "Rampa A", AssociatedBomb = "A", IsPlantZone = false, Priority = 5,
                MinX = -550f, MaxX = 100f, MinY = -450f, MaxY = 100f, MinZ = -240f, MaxZ = -60f },

        // 5. Escadas A & Jungle & Ticket / CT
        new() { SectorName = "Escadas A", AssociatedBomb = "A", IsPlantZone = false, Priority = 3,
                MinX = -1080f, MaxX = -620f, MinY = -1880f, MaxY = -1250f, MinZ = -220f, MaxZ = 40f },
        new() { SectorName = "Escadas A", AssociatedBomb = "A", IsPlantZone = false, Priority = 4,
                MinX = -1200f, MaxX = -920f, MinY = -740f, MaxY = -500f, MinZ = -220f, MaxZ = 40f },
        new() { SectorName = "Jungle", AssociatedBomb = "A", IsPlantZone = false, Priority = 4,
                MinX = -1520f, MaxX = -980f, MinY = -1850f, MaxY = -980f, MinZ = -220f, MaxZ = 20f },
        new() { SectorName = "Jungle", AssociatedBomb = "A", IsPlantZone = false, Priority = 5,
                MinX = -1500f, MaxX = -1100f, MinY = -950f, MaxY = -680f, MinZ = -220f, MaxZ = 20f },
        new() { SectorName = "Ticket / CT", AssociatedBomb = "A", IsPlantZone = false, Priority = 3,
                MinX = -2150f, MaxX = -1700f, MinY = -2600f, MaxY = -1650f, MinZ = -280f, MaxZ = 20f },
        new() { SectorName = "Ticket / CT", AssociatedBomb = "A", IsPlantZone = false, Priority = 4,
                MinX = -2150f, MaxX = -1700f, MinY = -950f, MaxY = -500f, MinZ = -240f, MaxZ = 20f },

        // 6. Janela do Meio, Conector, Catwalk / Short, Top Mid e Meio
        new() { SectorName = "Janela", AssociatedBomb = "Mid", IsPlantZone = false, Priority = 3,
                MinX = -1650f, MaxX = -1020f, MinY = -980f, MaxY = -420f, MinZ = -180f, MaxZ = 60f },
        new() { SectorName = "Conector", AssociatedBomb = "Mid", IsPlantZone = false, Priority = 3,
                MinX = -1020f, MaxX = -560f, MinY = -1350f, MaxY = -680f, MinZ = -220f, MaxZ = 20f },
        new() { SectorName = "Catwalk / Short", AssociatedBomb = "Mid", IsPlantZone = false, Priority = 4,
                MinX = -1320f, MaxX = -550f, MinY = -680f, MaxY = 180f, MinZ = -184f, MaxZ = 60f },
        new() { SectorName = "Catwalk / Short", AssociatedBomb = "Mid", IsPlantZone = false, Priority = 5,
                MinX = -1200f, MaxX = -800f, MinY = -1200f, MaxY = -900f, MinZ = -184f, MaxZ = 60f },
        new() { SectorName = "Top Mid", AssociatedBomb = "Mid", IsPlantZone = false, Priority = 4,
                MinX = -200f, MaxX = 880f, MinY = -1150f, MaxY = -150f, MinZ = -220f, MaxZ = 60f },
        new() { SectorName = "Meio", AssociatedBomb = "Mid", IsPlantZone = false, Priority = 6,
                MinX = -980f, MaxX = -150f, MinY = -1050f, MaxY = -150f, MinZ = -220f, MaxZ = 60f },

        // 7. Setores do Bomb B: Van, Mercado / Kitchen, Apartamentos B, Beco
        new() { SectorName = "Van", AssociatedBomb = "B", IsPlantZone = false, Priority = 3,
                MinX = -1550f, MaxX = -1050f, MinY = 120f, MaxY = 850f, MinZ = -220f, MaxZ = 60f },
        new() { SectorName = "Van", AssociatedBomb = "B", IsPlantZone = false, Priority = 4,
                MinX = -1420f, MaxX = -1150f, MinY = -220f, MaxY = 50f, MinZ = -220f, MaxZ = 60f },
        new() { SectorName = "Mercado / Kitchen", AssociatedBomb = "B", IsPlantZone = false, Priority = 3,
                MinX = -2680f, MaxX = -1650f, MinY = -850f, MaxY = 380f, MinZ = -240f, MaxZ = 60f },
        new() { SectorName = "Apartamentos B", AssociatedBomb = "B", IsPlantZone = false, Priority = 3,
                MinX = -1050f, MaxX = 550f, MinY = 150f, MaxY = 920f, MinZ = -160f, MaxZ = 120f },
        new() { SectorName = "Apartamentos B", AssociatedBomb = "B", IsPlantZone = false, Priority = 2,
                MinX = -150f, MaxX = 550f, MinY = -1550f, MaxY = -1100f, MinZ = -120f, MaxZ = 80f },
        new() { SectorName = "Beco", AssociatedBomb = "B", IsPlantZone = false, Priority = 5,
                MinX = 250f, MaxX = 980f, MinY = -150f, MaxY = 750f, MinZ = -220f, MaxZ = 120f },

        // 8. Spawns CT e TR
        new() { SectorName = "CT Spawn", AssociatedBomb = "CT", IsPlantZone = false, Priority = 4,
                MinX = -2680f, MaxX = -1320f, MinY = -2550f, MaxY = -750f, MinZ = -280f, MaxZ = 40f },
        new() { SectorName = "TR Spawn", AssociatedBomb = "TR", IsPlantZone = false, Priority = 4,
                MinX = 680f, MaxX = 1600f, MinY = -1150f, MaxY = 650f, MinZ = -260f, MaxZ = 120f }
    };

    /// <summary>
    /// Classifica uma posição 3D `(x, y, z)` e opcionalmente `nativeLastPlaceName` da Source 2
    /// em um setor oficial de `de_mirage`, sem jamais retornar `"Em Trânsito"` ou `"o Meio"` genérico.
    /// </summary>
    public static SectorClassificationResult Classify(
        float x,
        float y,
        float z,
        string? nativeLastPlaceName = null,
        bool inBombZoneFlag = false)
    {
        // 1. Nome de lugar nativo da Source 2 (nav places) é a verdade de jogo e tem precedência.
        if (!string.IsNullOrWhiteSpace(nativeLastPlaceName) &&
            NativePlaceMap.TryGetValue(nativeLastPlaceName.Trim(), out var mapped))
        {
            return new SectorClassificationResult
            {
                SectorName = mapped.Sector,
                AssociatedBomb = mapped.Bomb,
                IsPlantZone = mapped.IsPlant || inBombZoneFlag,
                Confidence = 0.97f,
                Source = $"NATIVE_PLACE({nativeLastPlaceName})"
            };
        }

        // 2. Volumes 3D (com desempate vertical Z para Underpass vs Catwalk)
        var matchingVolumes = Volumes
            .Where(v => v.Contains3D(x, y, z))
            .OrderBy(v => v.Priority)
            .ToList();

        if (matchingVolumes.Count > 0)
        {
            var bestVol = matchingVolumes[0];
            return new SectorClassificationResult
            {
                SectorName = bestVol.SectorName,
                AssociatedBomb = bestVol.AssociatedBomb,
                IsPlantZone = bestVol.IsPlantZone || inBombZoneFlag,
                Confidence = 1.0f,
                Source = "3D_VOLUME_EXACT"
            };
        }

        // 3. Continuidade de fronteira: seleciona o volume 3D mais próximo (penalizando diferença de cota Z)
        MirageSectorVolume? nearest = null;
        float bestWeightedDist = float.MaxValue;

        foreach (var vol in Volumes)
        {
            float dx = x < vol.MinX ? (vol.MinX - x) : (x > vol.MaxX ? (x - vol.MaxX) : 0f);
            float dy = y < vol.MinY ? (vol.MinY - y) : (y > vol.MaxY ? (y - vol.MaxY) : 0f);
            float dz = z < vol.MinZ ? (vol.MinZ - z) : (z > vol.MaxZ ? (z - vol.MaxZ) : 0f);

            // Peso 2.5x para diferença de altura Z para não confundir Underpass com Catwalk na borda
            float weightedDist = MathF.Sqrt(dx * dx + dy * dy + (dz * 2.5f) * (dz * 2.5f));
            if (weightedDist < bestWeightedDist)
            {
                bestWeightedDist = weightedDist;
                nearest = vol;
            }
        }

        if (nearest != null)
        {
            float conf = Math.Clamp(1.0f - (bestWeightedDist / 800.0f), 0.55f, 0.92f);
            return new SectorClassificationResult
            {
                SectorName = nearest.SectorName,
                AssociatedBomb = nearest.AssociatedBomb,
                IsPlantZone = (nearest.IsPlantZone && bestWeightedDist <= 120f) || inBombZoneFlag,
                Confidence = conf,
                Source = $"3D_VOLUME_NEAREST({bestWeightedDist:F0}u)"
            };
        }

        return new SectorClassificationResult
        {
            SectorName = "Meio",
            AssociatedBomb = "Mid",
            IsPlantZone = false,
            Confidence = 0.50f,
            Source = "FALLBACK_DEFAULT"
        };
    }

    public static SectorClassificationResult ClassifyPlayer(CCSPlayerController? player)
    {
        var pawn = player?.PlayerPawn.Value;
        if (pawn == null || pawn.AbsOrigin == null)
        {
            return new SectorClassificationResult
            {
                SectorName = "CT Spawn",
                AssociatedBomb = "CT",
                IsPlantZone = false,
                Confidence = 0.0f,
                Source = "INVALID_PAWN"
            };
        }

        string? placeName = null;
        bool inBombZone = false;
        try { placeName = pawn.LastPlaceName; } catch { }
        try { inBombZone = pawn.InBombZone; } catch { }

        return Classify(pawn.AbsOrigin.X, pawn.AbsOrigin.Y, pawn.AbsOrigin.Z, placeName, inBombZone);
    }

    /// <summary>
    /// Verifica se uma coordenada 3D está estritamente dentro do perímetro real de plant de um Bombsite ("A" ou "B"),
    /// evitando que um bot em `Ticket / CT`, `Palácio A` ou `Mercado / Kitchen` declare `"Bomb limpo!"` (Bug 6).
    /// </summary>
    public static bool IsInsideBombsitePlantPerimeter(float x, float y, float z, string targetBombSite, bool inBombZoneFlag = false)
    {
        if (inBombZoneFlag)
        {
            var cls = Classify(x, y, z, inBombZoneFlag: true);
            if (cls.AssociatedBomb.Equals(targetBombSite, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        string expectedSector = targetBombSite.Equals("B", StringComparison.OrdinalIgnoreCase) ? "Bomb B" : "Bomb A";
        foreach (var vol in Volumes)
        {
            if (vol.IsPlantZone &&
                vol.SectorName.Equals(expectedSector, StringComparison.OrdinalIgnoreCase) &&
                vol.Contains3D(x, y, z))
            {
                return true;
            }
        }

        return false;
    }
}
