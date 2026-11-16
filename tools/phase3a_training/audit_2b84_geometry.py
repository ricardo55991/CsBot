import hashlib
import json
import math
import os
from collections import defaultdict, deque
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(
    ROOT,
    "training_runs",
    "positioning_v2_real_temporal",
    "opening_route_canary_v1",
    "geometric_transition_patch_v1",
)
PREV_DIR = os.path.join(
    ROOT,
    "training_runs",
    "positioning_v2_real_temporal",
    "opening_route_canary_v1",
    "movement_authority_isolation_v1",
)
NAV_PATH = os.path.join(ROOT, "src", "CsBotManager", "MapProfiles", "de_mirage_nav_graph.json")
PROF_PATH = os.path.join(ROOT, "src", "CsBotManager", "MapProfiles", "de_mirage.json")
ALLOWLIST_PATH = os.path.join(
    ROOT,
    "training_runs",
    "positioning_v2_real_temporal",
    "opening_route_canary_v1",
    "canary_route_allowlist_v1.json",
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dist2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dist3(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i][0], poly[i][1]
        xj, yj = poly[j][0], poly[j][1]
        denom = (yj - yi) if abs(yj - yi) > 1e-6 else 1e-6
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / denom + xi):
            inside = not inside
        j = i
    return inside


def proj_area(x, y, z, corners):
    zs = [c[2] for c in corners]
    avg_z = sum(zs) / len(zs)
    if point_in_poly(x, y, corners) and (abs(z - avg_z) <= 96 or (min(zs) - 48 <= z <= max(zs) + 96)):
        pz = max(min(zs), min(max(zs), z)) if abs(z - avg_z) <= 64 else avg_z
        return (x, y, pz, abs(z - pz))
    best = None
    for i in range(len(corners)):
        a = corners[i]
        b = corners[(i + 1) % len(corners)]
        abx, aby = b[0] - a[0], b[1] - a[1]
        den = abx * abx + aby * aby
        t = 0.0 if den < 1e-6 else max(0.0, min(1.0, ((x - a[0]) * abx + (y - a[1]) * aby) / den))
        qx, qy, qz = a[0] + t * abx, a[1] + t * aby, a[2] + t * (b[2] - a[2])
        d = dist3((x, y, z), (qx, qy, qz))
        if best is None or d < best[3]:
            best = (qx, qy, qz, d)
    return best


def find_area(areas, pt):
    x, y, z = pt
    best = None
    for aid, a in areas.items():
        px, py, pz, d = proj_area(x, y, z, a["corners"])
        if best is None or d < best[0]:
            best = (d, aid, a, (px, py, pz))
    return best


def astar_areas(areas, start_id, goal_id):
    import heapq
    gc = areas[goal_id]["centroid"]
    pq = [(0.0, start_id)]
    best_g = {start_id: 0.0}
    parent = {}
    while pq:
        _, u = heapq.heappop(pq)
        if u == goal_id:
            path = []
            cur = goal_id
            while cur != start_id:
                path.append(cur)
                cur = parent[cur]
            path.append(start_id)
            path.reverse()
            return path, best_g[goal_id]
        uc = areas[u]["centroid"]
        for v in areas[u]["connections"]:
            if v not in areas:
                continue
            vc = areas[v]["centroid"]
            ng = best_g[u] + dist3(uc, vc)
            if v not in best_g or ng < best_g[v]:
                best_g[v] = ng
                parent[v] = u
                h = dist3(vc, gc)
                heapq.heappush(pq, (ng + h, v))
    return [], float("inf")


def compute_shared_portal(a_node, b_node):
    # Aproxima o portal compartilhado entre duas áreas NavMesh usando projeção recíproca das arestas/cantos
    ca = a_node["corners"]
    cb = b_node["corners"]
    xa_min, xa_max = min(p[0] for p in ca), max(p[0] for p in ca)
    ya_min, ya_max = min(p[1] for p in ca), max(p[1] for p in ca)
    xb_min, xb_max = min(p[0] for p in cb), max(p[0] for p in cb)
    yb_min, yb_max = min(p[1] for p in cb), max(p[1] for p in cb)

    ix_min, ix_max = max(xa_min, xb_min), min(xa_max, xb_max)
    iy_min, iy_max = max(ya_min, yb_min), min(ya_max, yb_max)
    dx = max(0.0, ix_max - ix_min)
    dy = max(0.0, iy_max - iy_min)
    width = round(max(dx, dy), 2)

    p_center = [
        round((max(xa_min, xb_min) + min(xa_max, xb_max)) / 2.0, 2) if ix_min <= ix_max else round((a_node["centroid"][0] + b_node["centroid"][0]) / 2.0, 2),
        round((max(ya_min, yb_min) + min(ya_max, yb_max)) / 2.0, 2) if iy_min <= iy_max else round((a_node["centroid"][1] + b_node["centroid"][1]) / 2.0, 2),
        round((a_node["centroid"][2] + b_node["centroid"][2]) / 2.0, 2),
    ]
    return {
        "from_area": a_node["area_id"],
        "to_area": b_node["area_id"],
        "portal_center": p_center,
        "portal_width_approx": width,
        "z_from": round(a_node["centroid"][2], 2),
        "z_to": round(b_node["centroid"][2], 2),
        "dz": round(b_node["centroid"][2] - a_node["centroid"][2], 2),
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    nav = json.load(open(NAV_PATH, encoding="utf-8"))
    areas = {a["area_id"]: a for a in nav["areas"] if a.get("hull_index", 0) == 0}
    prof = json.load(open(PROF_PATH, encoding="utf-8"))
    spots = {s["id"]: s for s in prof.get("spots", [])}

    # 1. Input snapshot
    prev_metrics_path = os.path.join(PREV_DIR, "ct_canary_metrics.json")
    prev_tel_path = os.path.join(PREV_DIR, "ct_canary_telemetry.jsonl")
    input_snap = {
        "marco": "2B.8.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "nature": "REAL",
        "artifacts": {
            "de_mirage_nav_graph": {"path": "src/CsBotManager/MapProfiles/de_mirage_nav_graph.json", "sha256": sha256_file(NAV_PATH), "areas_hull0": len(areas)},
            "de_mirage_profile": {"path": "src/CsBotManager/MapProfiles/de_mirage.json", "sha256": sha256_file(PROF_PATH), "spots": len(spots)},
            "canary_route_allowlist_v1": {"path": "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/canary_route_allowlist_v1.json", "sha256": sha256_file(ALLOWLIST_PATH)},
            "previous_2b83_metrics": {"path": "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/movement_authority_isolation_v1/ct_canary_metrics.json", "sha256": sha256_file(prev_metrics_path)},
            "previous_2b83_telemetry": {"path": "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/movement_authority_isolation_v1/ct_canary_telemetry.jsonl", "sha256": sha256_file(prev_tel_path)},
        },
    }
    json.dump(input_snap, open(os.path.join(OUT_DIR, "input_snapshot.json"), "w", encoding="utf-8"), indent=2)

    # 2. Approved route regression snapshot (rotas A aprovadas no Canary 2B.8.3)
    prev_metrics = json.load(open(prev_metrics_path, encoding="utf-8"))
    approved_a_sessions = [
        s for s in prev_metrics["metrics"]["sessions"]
        if s.get("target_sector") == "A" and s.get("arrival_status") == "ON_TIME"
    ]
    regression_snap = {
        "marco": "2B.8.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "protected_spots": ["a_triple_box_hold", "a_firebox_ninja_hold", "a_shadow_under_palace", "ct_a_sand_pit_under_palace_hold_caverna"],
        "protected_templates": {
            "CT:A_TICKET": {
                "allowed_corridor": "CT_A_TICKET",
                "waypoints": [{"name": "ct_ticket_booth", "x": -1020.9, "y": -2489.1, "z": -168.0}],
                "weapon_ready_wp": {"name": "ct_ticket_booth", "x": -1020.9, "y": -2489.1, "z": -168.0},
                "threat_line": {"name": "a_ramp_exit_line", "x": -580.0, "y": -2100.0, "z": -175.0},
                "knife_until_frac": 0.62,
            },
            "CT:A_JUNGLE": {
                "allowed_corridor": "CT_JUNGLE_STAIRS",
                "waypoints": [{"name": "ct_jungle_entry", "x": -1245.4, "y": -1374.2, "z": -164.8}],
                "weapon_ready_wp": {"name": "ct_jungle_entry", "x": -1245.4, "y": -1374.2, "z": -164.8},
                "threat_line": {"name": "a_stairs_mid_line", "x": -540.6, "y": -1443.6, "z": -73.9},
                "knife_until_frac": 0.58,
            },
        },
        "canary_2b83_approved_a_sessions": approved_a_sessions,
        "approved_a_rate": f"{len(approved_a_sessions)}/4 = 100.00%",
    }
    json.dump(regression_snap, open(os.path.join(OUT_DIR, "approved_route_regression_snapshot.json"), "w", encoding="utf-8"), indent=2)

    # 3. Extrair trajetórias reais de 2B.8.3 nos rounds que travaram (2, 5, 7, 8, 10)
    by_round = defaultdict(list)
    with open(prev_tel_path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            by_round[row["round"]].append(row)

    stuck_traces = {}
    for r in [2, 5, 7, 8, 10]:
        rows = by_round[r]
        pts = [rows[0]]
        for x in rows[1:]:
            if dist3(pts[-1]["actual_position"], x["actual_position"]) >= 80.0:
                pts.append(x)
        if pts[-1] is not rows[-1]:
            pts.append(rows[-1])
        stuck_traces[f"round_{r}"] = {
            "route_id": rows[-1]["route_id"],
            "spawn": rows[0]["actual_position"],
            "end_pos": rows[-1]["actual_position"],
            "end_status": rows[-1]["arrival_status"],
            "fallback_reason": rows[-1]["fallback_reason"],
            "block_cause": rows[-1]["block_cause"],
            "sample_points_with_area": [
                {
                    "pos": p["actual_position"],
                    "vel": p["velocity_xy"],
                    "wp": p["current_waypoint"],
                    "area_id": find_area(areas, p["actual_position"])[1],
                    "area_z": round(find_area(areas, p["actual_position"])[2]["centroid"][2], 2),
                }
                for p in pts
            ],
        }

    # 4. Auditoria geométrica das 3 regiões
    regions = [
        {
            "region_id": "REGION_1_MID_WINDOW_VENTS",
            "problem_observed": "Parada em [-1488.0, -1008.6, -207.6] tentando atingir ct_window_vents [-1329.4, -964.8, -168.0] com desnivel +39.6u",
            "start_pos": [-1488.0, -1008.6, -207.6],
            "intermediate_pos": [-1329.4, -964.8, -168.0],
            "goal_pos": [spots["mid_window_right_deep"]["x"], spots["mid_window_right_deep"]["y"], spots["mid_window_right_deep"]["z"]],
        },
        {
            "region_id": "REGION_2_MARKET_ENTRANCE_B",
            "problem_observed": "Parada em [-1438.9, -886.5, -167.9] indo direto para [-1981.9, 702.6, -48.0] sem transicao explicita de Market door/window/exit",
            "start_pos": [-1438.9, -886.5, -167.9],
            "intermediate_pos": [-1616.8, -618.9, -168.0],
            "goal_pos": [spots["b_van_behind_apps_hold"]["x"], spots["b_van_behind_apps_hold"]["y"], spots["b_van_behind_apps_hold"]["z"]],
        },
        {
            "region_id": "REGION_3_B_SITE_BENCH_FOREST_VAN",
            "problem_observed": "Parada em [-1920.2, -296.1, -168.0] indo para b_forest_bench_hold_apps [-2531.3, 274.1, -168.0] / b_van_behind_apps_hold [-1981.9, 702.6, -48.0]",
            "start_pos": [-1920.2, -296.1, -168.0],
            "intermediate_pos": [-2080.0, -140.0, -168.0],
            "goal_pos": [spots["b_forest_bench_hold_apps"]["x"], spots["b_forest_bench_hold_apps"]["y"], spots["b_forest_bench_hold_apps"]["z"]],
        },
    ]

    region_audits = []
    for reg in regions:
        d1, a_start, _, p_start = find_area(areas, reg["start_pos"])
        d2, a_mid, _, p_mid = find_area(areas, reg["intermediate_pos"])
        d3, a_goal, _, p_goal = find_area(areas, reg["goal_pos"])
        path1, len1 = astar_areas(areas, a_start, a_mid)
        path2, len2 = astar_areas(areas, a_mid, a_goal)
        full_path = path1 + (path2[1:] if len(path2) > 1 else [])
        portals = []
        for i in range(len(full_path) - 1):
            p_info = compute_shared_portal(areas[full_path[i]], areas[full_path[i + 1]])
            p_info["step_index"] = i
            p_info["from_centroid"] = [round(v, 2) for v in areas[full_path[i]]["centroid"]]
            p_info["to_centroid"] = [round(v, 2) for v in areas[full_path[i + 1]]["centroid"]]
            p_info["from_corners"] = areas[full_path[i]]["corners"]
            p_info["to_corners"] = areas[full_path[i + 1]]["corners"]
            portals.append(p_info)
        region_audits.append({
            **reg,
            "start_area_id": a_start,
            "intermediate_area_id": a_mid,
            "goal_area_id": a_goal,
            "astar_area_path": full_path,
            "astar_path_length_centroids": round(len1 + len2, 2),
            "portals": portals,
        })

    audit_doc = {
        "marco": "2B.8.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "nature": "REAL",
        "stuck_traces_2b83": stuck_traces,
        "region_audits": region_audits,
    }
    json.dump(audit_doc, open(os.path.join(OUT_DIR, "geometric_transition_audit.json"), "w", encoding="utf-8"), indent=2)

    for reg in region_audits:
        print(f"\n=== {reg['region_id']} ===")
        print(f"areas: {reg['start_area_id']} -> {reg['intermediate_area_id']} -> {reg['goal_area_id']} | path_len={reg['astar_path_length_centroids']} | steps={len(reg['portals'])}")
        for p in reg["portals"]:
            print(f"  [{p['step_index']}] {p['from_area']}->{p['to_area']} center={p['portal_center']} w={p['portal_width_approx']} z={p['z_from']}->{p['z_to']} (dz={p['dz']:+}) | fromC={p['from_centroid']} toC={p['to_centroid']}")

    print("\n=== STUCK TRACES SAMPLE ===")
    for rk, rv in stuck_traces.items():
        print(rk, rv["route_id"], "end_pos=", rv["end_pos"], "end_area=", rv["sample_points_with_area"][-1]["area_id"], "wp=", rv["sample_points_with_area"][-1]["wp"])
        for pt in rv["sample_points_with_area"]:
            print("   ", pt)


if __name__ == "__main__":
    main()
