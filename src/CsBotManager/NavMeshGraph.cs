using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace CsBotManager;

public sealed class NavMeshAreaDto
{
    [JsonPropertyName("area_id")] public int AreaId { get; init; }
    [JsonPropertyName("hull_index")] public int HullIndex { get; init; }
    [JsonPropertyName("flags")] public uint Flags { get; init; }
    [JsonPropertyName("centroid")] public float[] Centroid { get; init; } = Array.Empty<float>();
    [JsonPropertyName("corners")] public float[][] Corners { get; init; } = Array.Empty<float[]>();
    [JsonPropertyName("connections")] public int[] Connections { get; init; } = Array.Empty<int>();
}

public sealed class NavMeshGraphFileDto
{
    [JsonPropertyName("version")] public int Version { get; init; }
    [JsonPropertyName("sub_version")] public int SubVersion { get; init; }
    [JsonPropertyName("area_count")] public int AreaCount { get; init; }
    [JsonPropertyName("ladder_count")] public int LadderCount { get; init; }
    [JsonPropertyName("areas")] public List<NavMeshAreaDto> Areas { get; init; } = new();
}

public sealed record NavMeshProjectionResult(
    int AreaId,
    float ProjectedX,
    float ProjectedY,
    float ProjectedZ,
    float DeltaUnits,
    bool WithinMaxSnap)
{
    public bool IsValid => AreaId > 0 && WithinMaxSnap;
}

public sealed class NavMeshGraph
{
    private sealed record AreaNode(
        int AreaId,
        float Cx,
        float Cy,
        float Cz,
        float[][] Corners,
        int[] Connections);

    private readonly Dictionary<int, AreaNode> _areas = new();
    private readonly List<AreaNode> _areaList = new();
    private readonly ConcurrentDictionary<(int From, int To), (bool Connected, double Length, int[] Path)> _pathCache = new();

    private static readonly Lazy<NavMeshGraph?> DefaultLazy = new(TryLoadDefaultInternal);

    public int AreaCount => _areas.Count;
    public int Version { get; }

    private NavMeshGraph(NavMeshGraphFileDto dto)
    {
        Version = dto.Version;
        foreach (var a in dto.Areas)
        {
            if (a.HullIndex != 0 || a.Centroid.Length < 3 || a.Corners.Length < 3)
            {
                continue;
            }
            var node = new AreaNode(
                a.AreaId,
                a.Centroid[0],
                a.Centroid[1],
                a.Centroid[2],
                a.Corners,
                a.Connections ?? Array.Empty<int>());
            if (_areas.TryAdd(a.AreaId, node))
            {
                _areaList.Add(node);
            }
        }
    }

    public static NavMeshGraph? Default => DefaultLazy.Value;

    public static NavMeshGraph LoadFromFile(string path)
    {
        string json = File.ReadAllText(path);
        var dto = JsonSerializer.Deserialize<NavMeshGraphFileDto>(json)
            ?? throw new InvalidDataException($"Falha ao desserializar NavMesh graph: {path}");
        return new NavMeshGraph(dto);
    }

    private static NavMeshGraph? TryLoadDefaultInternal()
    {
        try
        {
            foreach (var candidate in EnumerateCandidatePaths())
            {
                if (string.IsNullOrWhiteSpace(candidate) || !File.Exists(candidate))
                {
                    continue;
                }
                try
                {
                    return LoadFromFile(candidate);
                }
                catch
                {
                    // tenta próximo caminho candidato
                }
            }
        }
        catch
        {
            // fallback seguro caso o runtime não exponha diretório base
        }
        return null;
    }

    private static IEnumerable<string> EnumerateCandidatePaths()
    {
        string? asmDir = null;
        try
        {
            string loc = typeof(NavMeshGraph).Assembly.Location;
            if (!string.IsNullOrWhiteSpace(loc))
            {
                asmDir = Path.GetDirectoryName(loc);
            }
        }
        catch
        {
        }

        if (!string.IsNullOrWhiteSpace(asmDir))
        {
            yield return Path.Combine(asmDir, "MapProfiles", "de_mirage_nav_graph.json");
            yield return Path.Combine(asmDir, "de_mirage_nav_graph.json");
        }

        string? baseDir = AppContext.BaseDirectory;
        if (!string.IsNullOrWhiteSpace(baseDir))
        {
            yield return Path.Combine(baseDir, "MapProfiles", "de_mirage_nav_graph.json");
            yield return Path.Combine(baseDir, "de_mirage_nav_graph.json");
        }

        string cwd = Directory.GetCurrentDirectory();
        if (!string.IsNullOrWhiteSpace(cwd))
        {
            yield return Path.Combine(cwd, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
        }

        // Caminho dedicado do servidor CS2 local e subpastas CounterStrikeSharp
        yield return @"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\MapProfiles\de_mirage_nav_graph.json";
        yield return @"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\src\CsBotManager\MapProfiles\de_mirage_nav_graph.json";

        string? rootWalk = !string.IsNullOrWhiteSpace(asmDir) ? asmDir : baseDir;
        if (!string.IsNullOrWhiteSpace(rootWalk))
        {
            var dir = new DirectoryInfo(rootWalk);
            for (int depth = 0; depth < 7 && dir != null; depth++, dir = dir.Parent)
            {
                yield return Path.Combine(dir.FullName, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
                yield return Path.Combine(dir.FullName, "MapProfiles", "de_mirage_nav_graph.json");
                yield return Path.Combine(dir.FullName, "csgo", "addons", "counterstrikesharp", "plugins", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
                yield return Path.Combine(dir.FullName, "addons", "counterstrikesharp", "plugins", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json");
            }
        }
    }

    public NavMeshProjectionResult ProjectPoint(float x, float y, float z, float maxSnapUnits = 32f)
    {
        if (float.IsNaN(x) || float.IsNaN(y) || float.IsNaN(z) || _areaList.Count == 0)
        {
            return new NavMeshProjectionResult(0, x, y, z, float.PositiveInfinity, false);
        }

        AreaNode? bestArea = null;
        float bestPx = x, bestPy = y, bestPz = z;
        double bestDist = double.MaxValue;

        foreach (var a in _areaList)
        {
            if (Math.Abs(x - a.Cx) > 650f || Math.Abs(y - a.Cy) > 650f)
            {
                continue;
            }
            var (px, py, pz, d) = ProjectOntoArea(x, y, z, a.Corners);
            if (d < bestDist)
            {
                bestDist = d;
                bestArea = a;
                bestPx = px;
                bestPy = py;
                bestPz = pz;
            }
        }

        if (bestArea == null)
        {
            foreach (var a in _areaList)
            {
                var (px, py, pz, d) = ProjectOntoArea(x, y, z, a.Corners);
                if (d < bestDist)
                {
                    bestDist = d;
                    bestArea = a;
                    bestPx = px;
                    bestPy = py;
                    bestPz = pz;
                }
            }
        }

        if (bestArea == null)
        {
            return new NavMeshProjectionResult(0, x, y, z, float.PositiveInfinity, false);
        }

        float delta = MathF.Round((float)bestDist, 2);
        return new NavMeshProjectionResult(
            bestArea.AreaId,
            MathF.Round(bestPx, 2),
            MathF.Round(bestPy, 2),
            MathF.Round(bestPz, 2),
            delta,
            delta <= maxSnapUnits);
    }

    public bool TryGetNextSteerTargetAlongPath(
        float x, float y, float z,
        float goalX, float goalY, float goalZ,
        out float steerX, out float steerY)
    {
        steerX = goalX;
        steerY = goalY;
        var pStart = ProjectPoint(x, y, z, 64f);
        var pGoal = ProjectPoint(goalX, goalY, goalZ, 64f);
        if (pStart.AreaId <= 0 || pGoal.AreaId <= 0 || pStart.AreaId == pGoal.AreaId)
        {
            return false;
        }
        var (connected, _, areaPath) = FindShortestAreaPath(pStart.AreaId, pGoal.AreaId);
        if (!connected || areaPath.Length < 2)
        {
            return false;
        }
        for (int i = 1; i < areaPath.Length; i++)
        {
            if (_areas.TryGetValue(areaPath[i], out var node))
            {
                float dx = node.Cx - x;
                float dy = node.Cy - y;
                if ((dx * dx + dy * dy) >= (42f * 42f))
                {
                    steerX = node.Cx;
                    steerY = node.Cy;
                    return true;
                }
            }
        }
        return false;
    }

    public (bool Connected, double PathLength, int[] AreaPath) FindShortestAreaPath(int startAreaId, int goalAreaId)
    {
        if (startAreaId <= 0 || goalAreaId <= 0 || !_areas.ContainsKey(startAreaId) || !_areas.ContainsKey(goalAreaId))
        {
            return (false, double.PositiveInfinity, Array.Empty<int>());
        }
        if (startAreaId == goalAreaId)
        {
            return (true, 0.0, new[] { startAreaId });
        }

        return _pathCache.GetOrAdd((startAreaId, goalAreaId), k => ComputeShortestAreaPath(k.From, k.To, null, double.PositiveInfinity));
    }

    public (bool Connected, double PathLength, int[] AreaPath) FindShortestAreaPath(
        int startAreaId,
        int goalAreaId,
        IReadOnlySet<int>? forbiddenAreas,
        double maxStepUpZ = double.PositiveInfinity)
    {
        if ((forbiddenAreas == null || forbiddenAreas.Count == 0) && double.IsPositiveInfinity(maxStepUpZ))
        {
            return FindShortestAreaPath(startAreaId, goalAreaId);
        }
        if (startAreaId <= 0 || goalAreaId <= 0 || !_areas.ContainsKey(startAreaId) || !_areas.ContainsKey(goalAreaId))
        {
            return (false, double.PositiveInfinity, Array.Empty<int>());
        }
        if (forbiddenAreas != null && forbiddenAreas.Contains(goalAreaId))
        {
            return (false, double.PositiveInfinity, Array.Empty<int>());
        }
        if (startAreaId == goalAreaId)
        {
            return (true, 0.0, new[] { startAreaId });
        }
        return ComputeShortestAreaPath(startAreaId, goalAreaId, forbiddenAreas, maxStepUpZ);
    }

    private (bool Connected, double Length, int[] Path) ComputeShortestAreaPath(
        int start,
        int goal,
        IReadOnlySet<int>? forbiddenAreas,
        double maxStepUpZ)
    {
        var goalNode = _areas[goal];
        var pq = new PriorityQueue<int, double>();
        var bestG = new Dictionary<int, double> { [start] = 0.0 };
        var parent = new Dictionary<int, int>();
        pq.Enqueue(start, 0.0);

        while (pq.Count > 0)
        {
            int u = pq.Dequeue();
            if (u == goal)
            {
                var stack = new List<int>();
                int cur = goal;
                while (cur != start)
                {
                    stack.Add(cur);
                    cur = parent[cur];
                }
                stack.Add(start);
                stack.Reverse();
                return (true, Math.Round(bestG[goal], 2), stack.ToArray());
            }

            if (!bestG.TryGetValue(u, out double g))
            {
                continue;
            }
            var uNode = _areas[u];
            foreach (int v in uNode.Connections)
            {
                if (forbiddenAreas != null && forbiddenAreas.Contains(v))
                {
                    continue;
                }
                if (!_areas.TryGetValue(v, out var vNode))
                {
                    continue;
                }
                if (!double.IsPositiveInfinity(maxStepUpZ) && (vNode.Cz - uNode.Cz) > maxStepUpZ)
                {
                    continue;
                }
                double step = Dist3(uNode.Cx, uNode.Cy, uNode.Cz, vNode.Cx, vNode.Cy, vNode.Cz);
                double ng = g + step;
                if (!bestG.TryGetValue(v, out double prevG) || ng < prevG)
                {
                    bestG[v] = ng;
                    parent[v] = u;
                    double h = Dist3(vNode.Cx, vNode.Cy, vNode.Cz, goalNode.Cx, goalNode.Cy, goalNode.Cz);
                    pq.Enqueue(v, ng + h);
                }
            }
        }

        return (false, double.PositiveInfinity, Array.Empty<int>());
    }

    public double? GetNavDistance(
        float x1, float y1, float z1,
        float x2, float y2, float z2,
        float maxSnapUnits = 96f,
        IReadOnlySet<int>? forbiddenAreas = null,
        double maxStepUpZ = double.PositiveInfinity)
    {
        var p1 = ProjectPoint(x1, y1, z1, maxSnapUnits);
        var p2 = ProjectPoint(x2, y2, z2, maxSnapUnits);
        if (p1.AreaId <= 0 || p2.AreaId <= 0 || !p1.WithinMaxSnap || !p2.WithinMaxSnap)
        {
            return null;
        }

        if (p1.AreaId == p2.AreaId)
        {
            return Dist3(p1.ProjectedX, p1.ProjectedY, p1.ProjectedZ, p2.ProjectedX, p2.ProjectedY, p2.ProjectedZ);
        }

        var (connected, length, path) = FindShortestAreaPath(p1.AreaId, p2.AreaId, forbiddenAreas, maxStepUpZ);
        if (!connected || path.Length == 0)
        {
            return null;
        }

        if (path.Length == 2)
        {
            // Áreas diretamente conectadas por portal: distância euclidiana projetada é suave e contínua
            return Dist3(p1.ProjectedX, p1.ProjectedY, p1.ProjectedZ, p2.ProjectedX, p2.ProjectedY, p2.ProjectedZ);
        }

        // Soma suave do próximo centroide até o penúltimo centroide + extremos projetados
        var second = _areas[path[1]];
        var penult = _areas[path[^2]];
        double startToSecond = Dist3(p1.ProjectedX, p1.ProjectedY, p1.ProjectedZ, second.Cx, second.Cy, second.Cz);
        double penultToGoal = Dist3(penult.Cx, penult.Cy, penult.Cz, p2.ProjectedX, p2.ProjectedY, p2.ProjectedZ);

        var firstNode = _areas[path[0]];
        var lastNode = _areas[path[^1]];
        double firstEdge = Dist3(firstNode.Cx, firstNode.Cy, firstNode.Cz, second.Cx, second.Cy, second.Cz);
        double lastEdge = Dist3(penult.Cx, penult.Cy, penult.Cz, lastNode.Cx, lastNode.Cy, lastNode.Cz);
        double middle = Math.Max(0.0, length - firstEdge - lastEdge);
        return Math.Round(startToSecond + middle + penultToGoal, 2);
    }

    public (float X, float Y, float Z) GetNextSteerTarget(
        float x1, float y1, float z1,
        float x2, float y2, float z2,
        float minLookaheadUnits = 72f,
        IReadOnlySet<int>? forbiddenAreas = null,
        double maxStepUpZ = double.PositiveInfinity)
    {
        var p1 = ProjectPoint(x1, y1, z1, 140f);
        var p2 = ProjectPoint(x2, y2, z2, 140f);
        if (p1.AreaId <= 0 || p2.AreaId <= 0 || p1.AreaId == p2.AreaId)
        {
            return (x2, y2, z2);
        }

        var (connected, _, path) = FindShortestAreaPath(p1.AreaId, p2.AreaId, forbiddenAreas, maxStepUpZ);
        if (!connected || path.Length == 0)
        {
            return (x2, y2, z2);
        }

        double minSq = (double)minLookaheadUnits * minLookaheadUnits;
        for (int i = 1; i < path.Length; i++)
        {
            if (!_areas.TryGetValue(path[i], out var nextArea)) continue;
            if (_areas.TryGetValue(path[i - 1], out var prevArea))
            {
                // Calcula o ponto no portal (borda da área seguinte mais próxima da posição atual / área anterior)
                float refX = i == 1 ? p1.ProjectedX : prevArea.Cx;
                float refY = i == 1 ? p1.ProjectedY : prevArea.Cy;
                float refZ = i == 1 ? p1.ProjectedZ : prevArea.Cz;
                var (portalX, portalY, portalZ, _) = ProjectOntoArea(refX, refY, refZ, nextArea.Corners);
                float steerX = 0.72f * portalX + 0.28f * nextArea.Cx;
                float steerY = 0.72f * portalY + 0.28f * nextArea.Cy;
                float steerZ = 0.72f * portalZ + 0.28f * nextArea.Cz;
                double pdx = steerX - x1;
                double pdy = steerY - y1;
                if ((pdx * pdx + pdy * pdy) >= minSq)
                {
                    return (steerX, steerY, steerZ);
                }
            }

            if (i < path.Length - 1)
            {
                double dx = nextArea.Cx - x1;
                double dy = nextArea.Cy - y1;
                if ((dx * dx + dy * dy) >= minSq)
                {
                    return (nextArea.Cx, nextArea.Cy, nextArea.Cz);
                }
            }
        }

        return (x2, y2, z2);
    }

    private static (float Px, float Py, float Pz, double Dist) ProjectOntoArea(float px, float py, float pz, float[][] corners)
    {
        float minZ = float.MaxValue, maxZ = float.MinValue;
        double sumZ = 0;
        for (int i = 0; i < corners.Length; i++)
        {
            float cz = corners[i][2];
            if (cz < minZ) minZ = cz;
            if (cz > maxZ) maxZ = cz;
            sumZ += cz;
        }
        float avgZ = (float)(sumZ / corners.Length);

        if (PointInPolygon2D(px, py, corners))
        {
            if (Math.Abs(pz - avgZ) <= 96f || (pz >= minZ - 48f && pz <= maxZ + 96f))
            {
                float projZ = Math.Abs(pz - avgZ) <= 64f ? Math.Clamp(pz, minZ, maxZ) : avgZ;
                return (px, py, projZ, Math.Abs(pz - projZ));
            }
        }

        float bestX = corners[0][0], bestY = corners[0][1], bestZ = corners[0][2];
        double bestDist = double.MaxValue;
        for (int i = 0; i < corners.Length; i++)
        {
            var a = corners[i];
            var b = corners[(i + 1) % corners.Length];
            var (qx, qy, qz) = ClosestPointOnSegment(px, py, a[0], a[1], a[2], b[0], b[1], b[2]);
            double d = Dist3(px, py, pz, qx, qy, qz);
            if (d < bestDist)
            {
                bestDist = d;
                bestX = qx;
                bestY = qy;
                bestZ = qz;
            }
        }
        return (bestX, bestY, bestZ, bestDist);
    }

    private static bool PointInPolygon2D(float px, float py, float[][] corners)
    {
        bool inside = false;
        int n = corners.Length;
        int j = n - 1;
        for (int i = 0; i < n; i++)
        {
            float xi = corners[i][0], yi = corners[i][1];
            float xj = corners[j][0], yj = corners[j][1];
            float denom = Math.Abs(yj - yi) > 1e-6f ? (yj - yi) : 1e-6f;
            if (((yi > py) != (yj > py)) && (px < (xj - xi) * (py - yi) / denom + xi))
            {
                inside = !inside;
            }
            j = i;
        }
        return inside;
    }

    private static (float X, float Y, float Z) ClosestPointOnSegment(
        float px, float py, float ax, float ay, float az, float bx, float by, float bz)
    {
        float abx = bx - ax;
        float aby = by - ay;
        float denom = abx * abx + aby * aby;
        if (denom < 1e-6f) return (ax, ay, az);
        float t = Math.Clamp(((px - ax) * abx + (py - ay) * aby) / denom, 0f, 1f);
        return (ax + t * abx, ay + t * aby, az + t * (bz - az));
    }

    private static double Dist3(double x1, double y1, double z1, double x2, double y2, double z2)
    {
        double dx = x2 - x1;
        double dy = y2 - y1;
        double dz = z2 - z1;
        return Math.Sqrt(dx * dx + dy * dy + dz * dz);
    }
}
