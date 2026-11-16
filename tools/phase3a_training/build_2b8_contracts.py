"""Gera os contratos iniciais do Marco 2B.8 (Opening Route Canary v1)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "training_runs/positioning_v2_real_temporal/opening_route_canary_v1"
CATALOG_2B7_PATH = REPO_ROOT / "training_runs/positioning_v2_real_temporal/opening_route_planner_v1/opening_route_catalog_v1.json"
SIDE_CONTRACT_V2_PATH = REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/side_contract_v2/spot_side_contract_v2.json"
SPOT_CATALOG_V3_PATH = REPO_ROOT / "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json"
DE_MIRAGE_PATH = REPO_ROOT / "src/CsBotManager/MapProfiles/de_mirage.json"

CT_ALLOWLIST_SPOTS = {
    # A: Site / Hold / Stairs-Palace cover (sem ct_retake_* que exigem PostPlant/Retake)
    "a_firebox_ninja_hold",
    "a_triple_box_hold",
    "a_shadow_under_palace",
    "ct_a_sand_pit_under_palace_hold_caverna",
    "a_tetris_corner_ramp_palace",
    # B: Market / Van / Bench / Pillar / Site anchor
    "b_van_behind_apps_hold",
    "b_forest_bench_hold_apps",
    "b_short_pillar_hold_apps",
    "b_short_pillar_bomb_control",
    "b_site_default_plant_box",
    "ct_b_edward_under_apps",
    "ct_b_empty_pillar_jail",
    # Meio: Window / Connector / Short / Underpass
    "mid_window_right_deep",
    "mid_connector_bottom",
    "mid_catwalk_short",
    "mid_underground_sub",
    "mid_chair_delpan_hold",
    "mid_ladder_room_control",
    "ct_b_short_arch_hold_mid",
}

T_ALLOWLIST_SPOTS = {
    # A: A Ramp / Palace / Tetris
    "tr_a_ramp_staging_wait",
    "a_palace_deep_room",
    "a_palace_balcony_tr",
    "a_tetris_corner_ramp_palace",
    "a_tetris_top_control",
    # Meio: Catwalk / Underpass / Connector / Chair (sem mid_top_mid_boxes por ser CATALOG_REVIEW_REQUIRED)
    "mid_catwalk_short",
    "mid_underground_sub",
    "mid_connector_bottom",
    "mid_chair_delpan_hold",
    # B: B Apps / House / Kitchen / Window AWP / Van-Forest
    "tr_b_apps_house_staging",
    "tr_b_apps_kitchen_control",
    "tr_b_tapete_window_market_awp",
    "b_van_behind_bomb_hold",
    "tr_b_forest_hold_short",
    "tr_b_forest_hold_market",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    catalog_2b7 = json.loads(CATALOG_2B7_PATH.read_text(encoding="utf-8"))
    side_contract = json.loads(SIDE_CONTRACT_V2_PATH.read_text(encoding="utf-8"))
    side_by_id = {s["spot_id"]: s for s in side_contract["spots"]}

    # Garantir que nenhum spot CATALOG_REVIEW_REQUIRED entre na allowlist
    for sid in CT_ALLOWLIST_SPOTS | T_ALLOWLIST_SPOTS:
        sc = side_by_id.get(sid)
        if sc is None:
            raise ValueError(f"Spot ausente no side_contract_v2: {sid}")
        if sc["classification"] == "CATALOG_REVIEW_REQUIRED":
            raise ValueError(f"Spot CATALOG_REVIEW_REQUIRED proibido no canary allowlist: {sid}")

    allowlisted_routes: list[dict[str, Any]] = []
    for r in catalog_2b7["routes"]:
        team = r["team"]
        spot = r["target_spot"]
        if (team == "CT" and spot in CT_ALLOWLIST_SPOTS) or (team == "T" and spot in T_ALLOWLIST_SPOTS):
            if not r.get("first_threat_line") or not r.get("fallback_route"):
                raise ValueError(f"Rota sem threat_line ou fallback: {r['route_id']}")
            allowlisted_routes.append({
                "route_id": r["route_id"],
                "team": team,
                "spawn_bucket": r["spawn_bucket"],
                "target_spot": spot,
                "target_sector": r["target_sector"],
                "allowed_corridor": r["allowed_corridor"],
                "forbidden_corridors": r["forbidden_corridors"],
                "ordered_waypoints": r["ordered_waypoints"],
                "expected_distance": r["expected_distance"],
                "expected_arrival_seconds": r["expected_arrival_seconds"],
                "deadline_seconds": r["deadline_seconds"],
                "knife_allowed_until": r["knife_allowed_until"],
                "weapon_ready_waypoint": r["weapon_ready_waypoint"],
                "first_threat_line": r["first_threat_line"],
                "fallback_route": r["fallback_route"],
                "conflict_group": r["conflict_group"],
            })

    input_snapshot = {
        "marco": "2B.8",
        "entry_verdict": "OPENING_ROUTE_PLANNER_READY_FOR_CANARY",
        "training_executed": False,
        "mlmove_modified": False,
        "positioning_transformer_authority": False,
        "hashes": {
            "training_runs/positioning_v2_real_temporal/opening_route_planner_v1/opening_route_catalog_v1.json": sha256_file(CATALOG_2B7_PATH),
            "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/side_contract_v2/spot_side_contract_v2.json": sha256_file(SIDE_CONTRACT_V2_PATH),
            "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json": sha256_file(SPOT_CATALOG_V3_PATH),
            "src/CsBotManager/MapProfiles/de_mirage.json": sha256_file(DE_MIRAGE_PATH),
        },
    }
    (OUT_DIR / "input_snapshot.json").write_text(json.dumps(input_snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    allowlist_payload = {
        "contract_version": "canary_route_allowlist_v1",
        "map": "de_mirage",
        "ct_spots": sorted(CT_ALLOWLIST_SPOTS),
        "t_spots": sorted(T_ALLOWLIST_SPOTS),
        "total_allowlisted_routes": len(allowlisted_routes),
        "excludes_catalog_review_required": True,
        "routes": allowlisted_routes,
    }
    (OUT_DIR / "canary_route_allowlist_v1.json").write_text(json.dumps(allowlist_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    control_contract = {
        "contract_version": "canary_control_contract_v1",
        "max_canary_bots_per_round": 1,
        "simultaneous_ct_and_tr_allowed": False,
        "phases_controlled": ["OPENING_PHASE_ONLY"],
        "limits": {
            "blocked_duration_ms_max": 500,
            "repath_attempts_max": 1,
            "weapon_ready_before_contact_required": 1.0,
        },
        "immediate_abort_triggers": [
            "CONTACT",
            "DAMAGE",
            "ENEMY_DETECTED",
            "HOSTILE_UTILITY",
            "UTILITY_PLAN_CHANGED",
            "C4_RELEVANT_OR_INCOMPATIBLE",
            "CANARY_BLOCKED_FALLBACK",
            "TIMEOUT",
            "INVALID_ROUTE",
            "NAVIGATION_FAILURE",
            "CANARY_ABORTED",
        ],
        "utility_ai_exclusive_authority": [
            "destination",
            "role",
            "sector",
            "combat",
            "aim",
            "grenades",
            "c4",
            "tactical_decisions",
            "repaths",
            "post_interruption_route",
            "save",
        ],
    }
    (OUT_DIR / "canary_control_contract_v1.json").write_text(json.dumps(control_contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"BUILT_2B8_CONTRACTS ct_spots={len(CT_ALLOWLIST_SPOTS)} t_spots={len(T_ALLOWLIST_SPOTS)} routes={len(allowlisted_routes)}")


if __name__ == "__main__":
    main()
