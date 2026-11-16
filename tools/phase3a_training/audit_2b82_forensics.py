import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIR_2B8 = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1"
DIR_2B81 = DIR_2B8 / "ct_congestion_patch_v1"
DIR_2B82 = DIR_2B8 / "route_executor_patch_v1"

NAV_GRAPH_PATH = DIR_2B82 / "de_mirage_nav_graph.json"
PROFILE_PATH = REPO_ROOT / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json"
ALLOWLIST_PATH = DIR_2B8 / "canary_route_allowlist_v1.json"

# Mesmos Templates CT de OpeningRoutePlanner.cs
CT_TEMPLATE_WAYPOINTS = {
    "CT_A_TICKET": [{"name": "ct_ticket_booth", "x": -1020.9, "y": -2489.1, "z": -168.0}],
    "CT_JUNGLE_STAIRS": [{"name": "ct_jungle_entry", "x": -1245.4, "y": -1374.2, "z": -164.8}],
    "CT_MID_WINDOW": [{"name": "ct_window_vents", "x": -1329.4, "y": -964.8, "z": -168.0}],
    "CT_B_SHORT_MID": [
        {"name": "ct_market_back", "x": -1616.8, "y": -618.9, "z": -168.0},
        {"name": "ct_short_arch", "x": -1489.5, "y": 259.9, "z": -167.0},
    ],
    "CT_MARKET_CORRIDOR": [{"name": "ct_market_entry", "x": -1616.8, "y": -618.9, "z": -168.0}],
}


def dist3(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def point_in_poly_2d(px, py, corners):
    inside = False
    n = len(corners)
    j = n - 1
    for i in range(n):
        xi, yi = corners[i][0], corners[i][1]
        xj, yj = corners[j][0], corners[j][1]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / ((yj - yi) if abs(yj - yi) > 1e-9 else 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def closest_point_on_segment_2d(px, py, ax, ay, az, bx, by, bz):
    abx, aby = bx - ax, by - ay
    denom = abx * abx + aby * aby
    if denom < 1e-9:
        return ax, ay, az
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / denom))
    return ax + t * abx, ay + t * aby, az + t * (bz - az)


def project_point_to_area(pt, area):
    px, py, pz = pt
    corners = area["corners"]
    if not corners:
        return None, 1e9
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    zs = [c[2] for c in corners]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    if point_in_poly_2d(px, py, corners):
        avg_z = sum(zs) / len(zs)
        if abs(pz - avg_z) <= 96.0 or (min_z - 48.0 <= pz <= max_z + 96.0):
            # Interpola Z pelo corner mais próximo ou centroide
            proj_z = max(min_z, min(max_z, pz)) if abs(pz - avg_z) <= 64.0 else avg_z
            return [round(px, 2), round(py, 2), round(proj_z, 2)], abs(pz - proj_z)

    best_pt = None
    best_d = 1e9
    n = len(corners)
    for i in range(n):
        a = corners[i]
        b = corners[(i + 1) % n]
        qx, qy, qz = closest_point_on_segment_2d(px, py, a[0], a[1], a[2], b[0], b[1], b[2])
        d = dist3((px, py, pz), (qx, qy, qz))
        if d < best_d:
            best_d = d
            best_pt = [round(qx, 2), round(qy, 2), round(qz, 2)]
    return best_pt, best_d


class NavMeshQuery:
    def __init__(self, graph_path: Path):
        data = json.loads(graph_path.read_text(encoding="utf-8"))
        # Hull 0 é o hull humano padrão
        self.areas = {int(a["area_id"]): a for a in data["areas"] if int(a.get("hull_index", 0)) == 0}
        # Construir adjacência bidirecional ou usar direcionada (adicionamos reversa se diferença de altura pequena para conectividade geral, mas mantemos direcionada como principal)
        self.area_list = list(self.areas.values())

    def project(self, pt):
        best_area = None
        best_proj = None
        best_dist = 1e9
        px, py, pz = pt
        for a in self.area_list:
            cx, cy, cz = a["centroid"]
            if abs(px - cx) > 650.0 or abs(py - cy) > 650.0:
                continue
            proj, d = project_point_to_area(pt, a)
            if d < best_dist:
                best_dist = d
                best_area = a
                best_proj = proj
        if best_area is None:
            for a in self.area_list:
                proj, d = project_point_to_area(pt, a)
                if d < best_dist:
                    best_dist = d
                    best_area = a
                    best_proj = proj
        return best_area, best_proj, round(best_dist, 2)

    def shortest_path(self, start_area_id: int, goal_area_id: int):
        if start_area_id == goal_area_id:
            return [start_area_id], 0.0
        if start_area_id not in self.areas or goal_area_id not in self.areas:
            return None, float("inf")
        goal_c = self.areas[goal_area_id]["centroid"]
        pq = [(0.0, 0.0, start_area_id)]
        best_g = {start_area_id: 0.0}
        parent = {}
        while pq:
            _, g, u = heapq.heappop(pq)
            if u == goal_area_id:
                path = []
                cur = u
                while cur in parent:
                    path.append(cur)
                    cur = parent[cur]
                path.append(start_area_id)
                path.reverse()
                return path, round(g, 1)
            if g > best_g.get(u, float("inf")):
                continue
            uc = self.areas[u]["centroid"]
            for v in self.areas[u]["connections"]:
                v = int(v)
                if v not in self.areas:
                    continue
                vc = self.areas[v]["centroid"]
                ng = g + dist3(uc, vc)
                if ng < best_g.get(v, float("inf")):
                    best_g[v] = ng
                    parent[v] = u
                    h = dist3(vc, goal_c)
                    heapq.heappush(pq, (ng + h, ng, v))
        return None, float("inf")


def main():
    nav = NavMeshQuery(NAV_GRAPH_PATH)
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    spots_by_id = {s["id"]: s for s in profile["spots"]}
    allowlist = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    ct_spots = allowlist["ct_spots"]

    # 1. Validação de waypoints de template e spots allowlisted no NavMesh real
    wp_manifest = []
    for corr, wps in CT_TEMPLATE_WAYPOINTS.items():
        for wp in wps:
            area, proj, delta = nav.project((wp["x"], wp["y"], wp["z"]))
            wp_manifest.append({
                "kind": "CORRIDOR_WAYPOINT",
                "corridor": corr,
                "id": wp["name"],
                "original": [wp["x"], wp["y"], wp["z"]],
                "projected": proj,
                "delta_units": delta,
                "navmesh_area_id": int(area["area_id"]),
                "within_32u": delta <= 32.0,
            })

    for sid in ct_spots:
        s = spots_by_id[sid]
        area, proj, delta = nav.project((s["x"], s["y"], s["z"]))
        wp_manifest.append({
            "kind": "DESTINATION_SPOT",
            "corridor": s["sector"],
            "id": sid,
            "original": [s["x"], s["y"], s["z"]],
            "projected": proj,
            "delta_units": delta,
            "navmesh_area_id": int(area["area_id"]),
            "within_32u": delta <= 32.0,
        })

    # Verificar rotas allowlisted CT (spawn -> waypoints -> spot)
    ct_routes = [r for r in allowlist["routes"] if r["team"] == "CT"]
    # Coordenadas representativas reais dos spawns CT observados na telemetria
    ct_spawn_samples = {
        "CT_A_FAST": (-1660.0, -1980.0, -267.0),
        "CT_MID_FAST": (-1650.0, -1720.0, -267.0),
        "CT_B_FAST": (-1660.0, -1480.0, -267.0),
    }

    route_validations = []
    for r in ct_routes:
        sb = r["spawn_bucket"]
        spawn_pt = ct_spawn_samples.get(sb, (-1660.0, -1950.0, -267.0))
        dest_id = r["target_spot"]
        s = spots_by_id[dest_id]
        corr = r["allowed_corridor"]
        wps = CT_TEMPLATE_WAYPOINTS.get(corr, [])
        chain = [("spawn", spawn_pt)] + [(w["name"], (w["x"], w["y"], w["z"])) for w in wps] + [(dest_id, (s["x"], s["y"], s["z"]))]

        seg_ok = True
        total_nav_len = 0.0
        max_proj_delta = 0.0
        segs = []
        for idx in range(len(chain) - 1):
            n1, p1 = chain[idx]
            n2, p2 = chain[idx + 1]
            a1, _, d1 = nav.project(p1)
            a2, _, d2 = nav.project(p2)
            max_proj_delta = max(max_proj_delta, d1, d2)
            path, plen = nav.shortest_path(int(a1["area_id"]), int(a2["area_id"]))
            ok = path is not None
            if not ok:
                seg_ok = False
            else:
                total_nav_len += plen
            segs.append({
                "from": n1,
                "to": n2,
                "from_area": int(a1["area_id"]),
                "to_area": int(a2["area_id"]),
                "path_exists": ok,
                "nav_hops": len(path) if path else 0,
                "nav_length": plen if ok else None,
            })
        route_validations.append({
            "route_id": r["route_id"],
            "spawn_bucket": sb,
            "allowed_corridor": corr,
            "destination": dest_id,
            "all_waypoints_projectable_le_32u": max_proj_delta <= 32.0,
            "max_projection_delta": round(max_proj_delta, 2),
            "all_segments_connected": seg_ok,
            "total_nav_length": round(total_nav_len, 1) if seg_ok else None,
            "segments": segs,
        })

    # 2. Analisar todas as 10 sessões CT do 2B.8.1 + comparar 2B.8 vs 2B.8.1
    recs_2b8 = [json.loads(l) for l in (DIR_2B8 / "ct_canary_telemetry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    recs_2b81 = [json.loads(l) for l in (DIR_2B81 / "ct_canary_telemetry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

    by_rnd_2b81 = defaultdict(list)
    for rec in recs_2b81:
        by_rnd_2b81[int(rec["round"])].append(rec)

    shadow_2b81 = defaultdict(lambda: defaultdict(list))
    for line in (DIR_2B81 / "ct_shadow_telemetry.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        sr = json.loads(line)
        if sr.get("team") == "CT":
            shadow_2b81[int(sr.get("round_id", 0))][sr.get("player_slot_pseudonym", "")].append(sr)

    session_root_causes = []
    blocker_reclass = []
    rounds_sorted = sorted(by_rnd_2b81.keys())[:10]
    for rnd in rounds_sorted:
        rows = by_rnd_2b81[rnd]
        last = rows[-1]
        dest = last["intended_destination"]
        spot = spots_by_id[dest]
        dest_pt = (spot["x"], spot["y"], spot["z"])
        dest_area, _, _ = nav.project(dest_pt)

        rec_rows = [r for r in rows if r.get("recovery_attempted")]
        lateral_rows = [r for r in rows if "_lateral" in r.get("current_waypoint", "")]
        dispatches = [r for r in rows if r.get("dispatch_reason") not in ("NONE", "STAGGER_HOLD", "COMPLETED", "FALLBACK", "")]

        first_pos = rows[0]["actual_position"]
        last_pos = last["actual_position"]
        last_area, last_proj, last_proj_d = nav.project(last_pos)
        _, rem_nav = nav.shortest_path(int(last_area["area_id"]), int(dest_area["area_id"]))
        rem_euclid = dist3(last_pos, dest_pt)

        # Classificar causa raiz da sessão
        fb = last["fallback_reason"]
        if fb == "ROUTE_COMPLETED":
            root_cause = "SUCCESS"
        elif fb == "CANARY_ABORTED:ROLE_IMMUTABLE":
            root_cause = "ROLE_CHANGED"
        elif fb == "CANARY_ABORTED:UTILITY_PLAN_CHANGED":
            root_cause = "DESTINATION_CHANGED"
        elif lateral_rows:
            # Bot recebeu waypoint lateral improvisado não projetado no NavMesh
            root_cause = "PATH_REPLACED"  # recovery lateral improvisado substituiu o waypoint do corredor sem projeção NavMesh!
        elif fb == "TIMEOUT":
            exp_d = float(last.get("expected_distance", 0.0))
            trav_d = float(last.get("traveled_distance", 0.0))
            # Em R2 e R11, bot percorreu 2816u-3056u (~2.3x a rota esperada de ~1240-1300u) na direção de B/Market após TradeSpacing/Pacing sobrescrever target_xyz e canary não rearmar
            root_cause = "PATH_REPLACED" if (rec_rows or trav_d > exp_d * 1.5) else "DEADLINE_TOO_SHORT"
        else:
            root_cause = "UNKNOWN"

        # Checar se houve falso bloqueio
        teammate_blocked_rows = [r for r in rows if r.get("block_cause") == "TEAMMATE_CONGESTION"]
        non_tm_blocked_rows = [r for r in rows if r.get("block_cause") not in ("NONE", "TEAMMATE_CONGESTION", None)]

        if fb == "CANARY_BLOCKED_FALLBACK":
            blocker_reclass.append({
                "round": rnd,
                "destination": dest,
                "reported_arrival_status": last["arrival_status"],
                "reported_blocked_ms": last.get("blocked_duration_ms", 0),
                "had_lateral_waypoint_override": bool(lateral_rows),
                "lateral_waypoint": lateral_rows[0]["current_waypoint"] if lateral_rows else None,
                "teammate_blocker_ticks": len(teammate_blocked_rows),
                "non_teammate_block_ticks": len(non_tm_blocked_rows),
                "ground_truth_classification": "FALSE_TEAMMATE_BLOCK_AFTER_LATERAL_OVERRIDE" if lateral_rows else ("REAL_TEAMMATE_BLOCK" if last["arrival_status"] == "BLOCKED_BY_TEAMMATE" else "FALSE_BLOCK_STATIC_OR_PATH"),
            })

        session_root_causes.append({
            "round": rnd,
            "player": last["player_pseudonym"],
            "spawn_bucket": last["spawn_bucket"],
            "route_id": last["route_id"],
            "destination": dest,
            "fallback_reason": fb,
            "arrival_status": last["arrival_status"],
            "root_cause": root_cause,
            "elapsed_seconds": last["elapsed_seconds"],
            "traveled_distance": last["traveled_distance"],
            "expected_distance": last["expected_distance"],
            "remaining_euclid_to_dest": round(rem_euclid, 1),
            "remaining_nav_to_dest": rem_nav,
            "dispatches_count": len(dispatches),
            "lateral_recovery_triggered": bool(rec_rows),
            "ticks_spent_on_lateral_wp": len(lateral_rows),
            "final_pos": last_pos,
            "final_nav_area": int(last_area["area_id"]),
        })

    out_nav = {
        "provenance": "REAL_CS2_NAVMESH_V36",
        "navmesh_areas_hull0": len(nav.areas),
        "total_routes_checked": len(route_validations),
        "routes_with_valid_projection_le_32u": sum(1 for x in route_validations if x["all_waypoints_projectable_le_32u"]),
        "routes_with_complete_nav_connectivity": sum(1 for x in route_validations if x["all_segments_connected"]),
        "bad_waypoints": [m for m in wp_manifest if not m["within_32u"]],
        "routes": route_validations,
    }
    (DIR_2B82 / "route_navmesh_validation.json").write_text(json.dumps(out_nav, indent=2) + "\n", encoding="utf-8")
    (DIR_2B82 / "waypoint_projection_manifest.json").write_text(json.dumps({"provenance": "REAL_CS2_NAVMESH_V36", "waypoints": wp_manifest}, indent=2) + "\n", encoding="utf-8")
    (DIR_2B82 / "failed_session_root_causes.json").write_text(json.dumps({"provenance": "REAL_LIVE_CS2_SERVER+NAVMESH_V36", "sessions": session_root_causes}, indent=2) + "\n", encoding="utf-8")
    (DIR_2B82 / "blocker_reclassification.json").write_text(json.dumps({"provenance": "REAL_LIVE_CS2_SERVER", "reclassified_fallbacks": blocker_reclass}, indent=2) + "\n", encoding="utf-8")

    # Resumo no stdout cirúrgico
    bad_wps = [f"{m['id']}:{m['delta_units']}" for m in wp_manifest if not m["within_32u"]]
    disconn = [r["route_id"] for r in route_validations if not r["all_segments_connected"]]
    print(f"NAV_AREAS={len(nav.areas)} ROUTES={len(route_validations)} BAD_WPS={bad_wps} DISCONNECTED={len(disconn)}")
    for s in session_root_causes:
        print(f"  R{s['round']}: {s['destination']} fb={s['fallback_reason']} cause={s['root_cause']} lat_ticks={s['ticks_spent_on_lateral_wp']} rem_euclid={s['remaining_euclid_to_dest']} rem_nav={s['remaining_nav_to_dest']}")


if __name__ == "__main__":
    main()
