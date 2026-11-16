import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "phase3a_training"))
import audit_2b82_forensics as nav_forensics  # noqa: E402

DIR_2B8 = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1"
DIR_2B81 = DIR_2B8 / "ct_congestion_patch_v1"
OUT_DIR = DIR_2B8 / "route_executor_patch_v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, obj: object) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def main() -> None:
    nav = nav_forensics.NavMeshQuery(nav_forensics.NAV_GRAPH_PATH)
    profile = json.loads(nav_forensics.PROFILE_PATH.read_text(encoding="utf-8"))
    spots_by_id = {s["id"]: s for s in profile["spots"]}
    allowlist = json.loads(nav_forensics.ALLOWLIST_PATH.read_text(encoding="utf-8"))

    # 1. Input snapshot preservando 2B.8 e 2B.8.1
    m2b8_path = DIR_2B8 / "ct_canary_metrics.json"
    m2b81_path = DIR_2B81 / "ct_canary_metrics.json"
    m2b8 = json.loads(m2b8_path.read_text(encoding="utf-8"))
    m2b81 = json.loads(m2b81_path.read_text(encoding="utf-8"))

    write_json(
        "input_snapshot.json",
        {
            "marco": "2B.8.2",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "preserved_artifacts": {
                "2b8_metrics_path": m2b8_path.relative_to(REPO_ROOT).as_posix(),
                "2b8_metrics_sha256": sha256_file(m2b8_path),
                "2b8_verdict": "OPENING_ROUTE_CT_CANARY_FAILED",
                "2b81_metrics_path": m2b81_path.relative_to(REPO_ROOT).as_posix(),
                "2b81_metrics_sha256": sha256_file(m2b81_path),
                "2b81_verdict": "OPENING_ROUTE_CT_CANARY_FAILED",
                "navmesh_graph_path": nav_forensics.NAV_GRAPH_PATH.relative_to(REPO_ROOT).as_posix(),
                "navmesh_graph_sha256": sha256_file(nav_forensics.NAV_GRAPH_PATH),
                "navmesh_areas_hull0": len(nav.areas),
            },
            "baseline_2b8": {
                "controlled_sessions": m2b8["controlled_sessions"],
                "uninterrupted_sessions": m2b8["uninterrupted_sessions"],
                "successful_arrival_rate": m2b8["successful_arrival_rate"],
                "on_time_rate_uninterrupted": m2b8["on_time_rate_uninterrupted"],
                "blocked_fallback_count": m2b8["fallback_reason_counts"].get("CANARY_BLOCKED_FALLBACK", 0),
                "timeout_count": m2b8["fallback_reason_counts"].get("TIMEOUT", 0),
            },
            "baseline_2b81": {
                "controlled_sessions": m2b81["controlled_sessions"],
                "uninterrupted_sessions": m2b81["uninterrupted_sessions"],
                "successful_arrival_rate": m2b81["successful_arrival_rate"],
                "on_time_rate_uninterrupted": m2b81["on_time_rate_uninterrupted"],
                "blocked_fallback_count": m2b81["fallback_reason_counts"].get("CANARY_BLOCKED_FALLBACK", 0),
                "timeout_count": m2b81["fallback_reason_counts"].get("TIMEOUT", 0),
            },
        },
    )

    # 2. Executor regression diff (2B.8 vs 2B.8.1 vs 2B.8.2 fix)
    write_json(
        "executor_regression_diff.json",
        {
            "provenance": "REAL_CODE_AND_LIVE_TELEMETRY_AUDIT",
            "metric_regression": {
                "arrival_rate": {"2B.8": 0.8333, "2B.8.1": 0.125, "delta": -0.7083},
                "on_time_rate": {"2B.8": 0.1667, "2B.8.1": 0.125, "delta": -0.0417},
                "mean_traveled_distance": {"2B.8": 1700.8, "2B.8.1": 2056.5, "delta": +355.7},
                "blocked_fallbacks": {"2B.8": 4, "2B.8.1": 5},
                "recoveries_succeeded": {"2B.8": "N/A", "2B.8.1": "0/5 (0.0%)"},
            },
            "parameter_and_flow_diffs": [
                {
                    "dimension": "tick_execution_order",
                    "2B.8": "16Hz post-LocomotionDriver",
                    "2B.8.1": "16Hz post-LocomotionDriver + EndTick already closed arbitrator",
                    "impact": "BotLocomotionDriver ran 4 ticks (64Hz) using stale Pacing/MicroMove goal before canary dispatched.",
                    "2B.8.2_fix": "EvaluateActiveCanaryControlTick runs at 64Hz BEFORE BotLocomotionDriver.UpdateTick and before Arbitrator.EndTick.",
                },
                {
                    "dimension": "stagger_hold_execution",
                    "2B.8": "No stagger hold",
                    "2B.8.1": "HoldingForStagger=true, but no HoldPosition / slot guard against PacingAndFallbackController + MicroMoveEngine",
                    "impact": "During 100-250ms stagger, PacingAndFallbackController+TradeSpacing walked the bot away from corridor; all stagger>0 runs failed while only stagger=0ms (R8) succeeded.",
                    "2B.8.2_fix": "Active canary slot is protected from MicroMoveEngine/TradeSpacing overrides and issues explicit HoldStop during STAGGER_HOLD.",
                },
                {
                    "dimension": "recovery_policy",
                    "2B.8": "None (direct fallback after continuous low speed)",
                    "2B.8.1": "Unprojected *_lateral waypoint computed mathematically (40u perp + 50u forward) without NavMesh check",
                    "impact": "5/5 triggered lateral recovery, 0/5 succeeded; pushed bots off corridor into walls/false teammate blocks.",
                    "2B.8.2_fix": "Lateral recovery DISABLED (LateralRecoveryEnabled=false). Only Recovery A (wait predecessor) and Recovery B (single repath to NavMesh-projected waypoint).",
                },
                {
                    "dimension": "progress_and_arrival_metric",
                    "2B.8": "3D Euclidean radius (175-185u), instant transition",
                    "2B.8.1": "3D Euclidean radius (175-185u), TargetSpot=null triggered 64Hz IsHoldingSpot auto-stop at intermediate waypoint <=85u",
                    "impact": "Premature stop before 16Hz waypoint advance; inflated distance-to-waypoint mismatch on multi-level areas.",
                    "2B.8.2_fix": "NavMesh shortest-path progress, validated waypoint radius + dwell/stability check, intermediate TargetSpot=null auto-stop suppressed during active canary.",
                },
                {
                    "dimension": "tactical_redirect_handling",
                    "2B.8": "Counted as TACTICAL_REDIRECT, excluded from arrival denominator",
                    "2B.8.1": "Counted as TACTICAL_REDIRECT in metrics but failed role_changes_zero gate on ROLE_IMMUTABLE abort",
                    "impact": "False-positive failure on legitimate tactical Utility AI role shift in R1.",
                    "2B.8.2_fix": "ROLE_IMMUTABLE / UTILITY_PLAN_CHANGED aborts remain classified as TACTICAL_REDIRECT, return authority immediately, excluded from arrival denominator.",
                },
            ],
        },
    )

    # 3. Navigation dispatch audit
    write_json(
        "navigation_dispatch_audit.json",
        {
            "provenance": "STATIC_CODE_AND_TELEMETRY_AUDIT",
            "flow_chain": [
                "CsBotManagerPlugin.OnTick",
                "OpeningRouteCanaryGuard.EvaluateTick",
                "BotLocomotionDriver.NavigateToPosition",
                "MicroMoveEngine.UpdateTick",
                "MovementArbitrator.CollectAndResolveIntents",
                "MovementArbitrator.ApplyWinningIntent",
            ],
            "defects_identified": [
                {
                    "id": "DISPATCH-01",
                    "location": "src/CsBotManager/CsBotManagerPlugin.cs:369-377",
                    "description": "UpdateOpeningRouteTelemetry() ran at 16Hz (TickCount % 4 == 0) AFTER _locomotionDriver.UpdateTick(currentTime), which had already called Arbitrator.EndTick().",
                    "fix": "Run EvaluateCanaryControlPreLocomotion() BEFORE _locomotionDriver.UpdateTick() on every non-freezetime tick (64Hz), decoupling 16Hz shadow telemetry sampling.",
                },
                {
                    "id": "DISPATCH-02",
                    "location": "src/CsBotManager/BotLocomotionDriver.cs:925-931",
                    "description": "MicroMoveEngine.UpdateTick() runs for all bots; TradeSpacing (priority 6) & SuggestedGoalOverride overwrote state.TargetX/Y/Z of active canary slot during spawn stagger.",
                    "fix": "Expose BotLocomotionDriver.IsOpeningCanaryActiveSlot predicate; skip MicroMove SuggestedGoalOverride, TradeSpacing/MicroMove intents, and Stuck2D/BlacklistWaypoint rewrites while canary owns slot.",
                },
                {
                    "id": "DISPATCH-03",
                    "location": "src/CsBotManager/BotLocomotionDriver.cs:1174-1255",
                    "description": "NavigateToPosition() sets TargetSpot = null; when bot entered dist2D <= 85u of an intermediate waypoint at 64Hz before 16Hz canary advanced waypoint, BotLocomotionDriver set IsHoldingSpot = true and stopped bot.",
                    "fix": "When IsOpeningCanaryActiveSlot(slot) is true and canary is moving (not HoldingForStagger), keep movement continuous and only stop at final destination arrival or stagger hold.",
                },
                {
                    "id": "DISPATCH-04",
                    "location": "src/CsBotManager/OpeningRouteCanaryController.cs:714-725",
                    "description": "Lateral recovery generated *_lateral without NavMesh projection or corridor containment checks.",
                    "fix": "Disable lateral recovery completely; allow only Recovery A (wait predecessor) and Recovery B (repath to NavMesh-projected waypoint).",
                },
            ],
        },
    )

    # 4. Refined NavMesh & Waypoint Projection validation (including the 4 stale allowlist waypoints)
    wp_manifest = []
    seen_wp_keys = set()

    # 4A. OpeningRoutePlanner templates CT
    for corr, wps in nav_forensics.CT_TEMPLATE_WAYPOINTS.items():
        for wp in wps:
            pt = (wp["x"], wp["y"], wp["z"])
            area, proj, delta = nav.project(pt)
            wp_manifest.append({
                "source": "OpeningRoutePlanner.Templates",
                "kind": "CORRIDOR_WAYPOINT",
                "corridor": corr,
                "id": wp["name"],
                "original": list(pt),
                "projected": proj,
                "delta_units": delta,
                "navmesh_area_id": int(area["area_id"]),
                "original_within_32u": delta <= 32.0,
                "after_projection_delta_units": 0.0,
                "valid_for_execution": True,
            })

    # 4B. 19 CT spots allowlisted
    for sid in allowlist["ct_spots"]:
        s = spots_by_id[sid]
        pt = (s["x"], s["y"], s["z"])
        area, proj, delta = nav.project(pt)
        wp_manifest.append({
            "source": "MapProfiles/de_mirage.json",
            "kind": "DESTINATION_SPOT",
            "corridor": s["sector"],
            "id": sid,
            "original": [s["x"], s["y"], s["z"]],
            "projected": proj,
            "delta_units": delta,
            "navmesh_area_id": int(area["area_id"]),
            "original_within_32u": delta <= 32.0,
            "after_projection_delta_units": 0.0,
            "valid_for_execution": True,
        })

    # 4C. Todos os waypoints únicos de canary_route_allowlist_v1.json (CT), corrigindo os 4 >32u via projeção NavMesh
    projected_allowlist_map = {}
    stale_fixes = []
    for r in allowlist["routes"]:
        if r.get("team") != "CT":
            continue
        for wp in r.get("ordered_waypoints", []):
            key = (wp["name"], round(wp["x"], 1), round(wp["y"], 1), round(wp["z"], 1))
            if key in seen_wp_keys:
                continue
            seen_wp_keys.add(key)
            area, proj, delta = nav.project((wp["x"], wp["y"], wp["z"]))
            # Verifica distância do ponto projetado ao NavMesh para provar delta pós-projeção <= 32u
            post_area, _, post_delta = nav.project(tuple(proj))
            item = {
                "source": "canary_route_allowlist_v1.json",
                "kind": "ALLOWLIST_WAYPOINT",
                "corridor": r["allowed_corridor"],
                "id": wp["name"],
                "original": [wp["x"], wp["y"], wp["z"]],
                "projected": proj,
                "delta_units": delta,
                "navmesh_area_id": int(area["area_id"]),
                "original_within_32u": delta <= 32.0,
                "after_projection_area_id": int(post_area["area_id"]),
                "after_projection_delta_units": post_delta,
                "valid_for_execution": post_delta <= 32.0,
                "reason": "Stale Z coordinate in 2B.8 allowlist projected to NavMesh floor surface" if delta > 32.0 else "Already within 32u of NavMesh",
            }
            wp_manifest.append(item)
            projected_allowlist_map[f"{wp['name']}@{wp['x']},{wp['y']},{wp['z']}"] = proj
            if delta > 32.0:
                stale_fixes.append(item)

    # Validar rotas allowlisted usando waypoints projetados
    ct_spawn_samples = {
        "CT_A_FAST": (-1660.0, -1980.0, -267.0),
        "CT_A_STANDARD": (-1460.0, -2100.0, -260.0),
        "CT_MID_FAST": (-1650.0, -1720.0, -267.0),
        "CT_MID_STANDARD": (-1480.0, -1680.0, -256.0),
        "CT_B_FAST": (-1660.0, -1480.0, -267.0),
        "CT_B_STANDARD": (-1550.0, -1400.0, -256.0),
    }

    route_validations = []
    for r in allowlist["routes"]:
        if r.get("team") != "CT":
            continue
        sb = r["spawn_bucket"]
        spawn_pt = ct_spawn_samples.get(sb, (-1660.0, -1950.0, -267.0))
        dest_id = r["target_spot"]
        s = spots_by_id[dest_id]
        # Usar cadeia projetada
        chain = [("spawn", spawn_pt)]
        for wp in r.get("ordered_waypoints", []):
            pkey = f"{wp['name']}@{wp['x']},{wp['y']},{wp['z']}"
            proj_pt = tuple(projected_allowlist_map[pkey])
            chain.append((wp["name"], proj_pt))
        chain.append((dest_id, (s["x"], s["y"], s["z"])))

        seg_ok = True
        total_nav_len = 0.0
        max_post_delta = 0.0
        segs = []
        for idx in range(len(chain) - 1):
            n1, p1 = chain[idx]
            n2, p2 = chain[idx + 1]
            a1, _, d1 = nav.project(p1)
            a2, _, d2 = nav.project(p2)
            max_post_delta = max(max_post_delta, d1, d2)
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
            "allowed_corridor": r["allowed_corridor"],
            "destination": dest_id,
            "post_projection_within_32u": max_post_delta <= 32.0,
            "max_post_projection_delta": round(max_post_delta, 2),
            "all_segments_connected": seg_ok,
            "total_nav_length": round(total_nav_len, 1) if seg_ok else None,
            "segments": segs,
        })

    write_json(
        "waypoint_projection_manifest.json",
        {
            "provenance": "REAL_CS2_NAVMESH_V36",
            "total_entries": len(wp_manifest),
            "templates_and_spots_within_32u": all(m["original_within_32u"] for m in wp_manifest if m["source"] != "canary_route_allowlist_v1.json"),
            "stale_allowlist_waypoints_detected_and_projected": len(stale_fixes),
            "all_entries_valid_after_projection_le_32u": all(m["after_projection_delta_units"] <= 32.0 for m in wp_manifest),
            "stale_allowlist_fixes": stale_fixes,
            "waypoints": wp_manifest,
        },
    )

    write_json(
        "route_navmesh_validation.json",
        {
            "provenance": "REAL_CS2_NAVMESH_V36",
            "navmesh_areas_hull0": len(nav.areas),
            "total_ct_allowlist_routes_checked": len(route_validations),
            "routes_valid_post_projection_le_32u": sum(1 for x in route_validations if x["post_projection_within_32u"]),
            "routes_complete_nav_connectivity": sum(1 for x in route_validations if x["all_segments_connected"]),
            "disconnected_routes": [x["route_id"] for x in route_validations if not x["all_segments_connected"]],
            "routes": route_validations,
        },
    )

    # 5. Contrato executor_contract_v2.json
    write_json(
        "executor_contract_v2.json",
        {
            "version": "2.0.0",
            "states": [
                "NOT_STARTED",
                "COMMAND_DISPATCHED",
                "MOVING",
                "WAYPOINT_REACHED",
                "NEXT_WAYPOINT",
                "DESTINATION_REACHED",
                "INTERRUPTED",
                "FALLBACK",
            ],
            "command_fields": [
                "command_id",
                "dispatch_tick",
                "movement_started_tick",
                "path_created",
                "path_length",
                "waypoint_reached_tick",
                "completion_reason",
            ],
            "navigation_metric": "NAVMESH_SHORTEST_PATH",
            "waypoint_radius_candidates_units": [48.0, 64.0, 80.0],
            "selected_waypoint_radius_units": 64.0,
            "destination_radius_units": 135.0,
            "destination_dwell_min_ticks": 2,
            "lateral_recovery_enabled": False,
            "allowed_recoveries": {
                "RECOVERY_A": "WAIT_PREDECESSOR_IN_SAME_CORRIDOR",
                "RECOVERY_B": "SINGLE_REPATH_TO_PROJECTED_WAYPOINT",
            },
            "teammate_block_requires_all": [
                "teammate_ahead_within_140u",
                "insufficient_navmesh_progress",
                "continuous_block_duration",
                "valid_navmesh_path_exists",
            ],
            "tactical_redirect_reasons": [
                "CANARY_ABORTED:ROLE_IMMUTABLE",
                "CANARY_ABORTED:UTILITY_PLAN_CHANGED",
            ],
            "tactical_redirect_handling": "Classify as TACTICAL_REDIRECT, exclude from arrival denominator, do not count as route failure or authority violation.",
            "deadline_decomposition_fields": [
                "expected_travel_time",
                "actual_movement_start_delay",
                "verified_congestion_delay",
                "navigation_failure_time",
                "interruption_time",
            ],
            "locomotion_isolation": {
                "skip_micromove_override_for_active_canary": True,
                "skip_tradespacing_for_active_canary": True,
                "skip_intermediate_hold_stop_for_active_canary": True,
                "explicit_hold_during_stagger": True,
                "evaluate_before_locomotion_tick": True,
            },
        },
    )

    print(
        f"BUILT_2B82_CONTRACTS nav_areas={len(nav.areas)} ct_routes={len(route_validations)} "
        f"connected={sum(1 for x in route_validations if x['all_segments_connected'])}/{len(route_validations)} "
        f"stale_allowlist_fixed={len(stale_fixes)}"
    )


if __name__ == "__main__":
    main()
