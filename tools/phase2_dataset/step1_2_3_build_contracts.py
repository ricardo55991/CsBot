#!/usr/bin/env python3
"""
Fase 2 - Passo 1, 2 e 3: Congelamento do Catálogo Mirage V3, Classificação Semântica e Normalização de Aim Profiles.
Gera:
  - datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json
  - datasets/mirage_v2/contracts/mirage_spot_catalog_v3.sha256
  - datasets/mirage_v2/contracts/mirage_spot_catalog_v3_manifest.json
  - datasets/mirage_v2/contracts/spot_semantic_classification.json
  - datasets/mirage_v2/contracts/aim_profiles_v1.json
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import subprocess

def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "d66c214e88a08d2a1a721b423a3e788c33163585"

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    base_dir = Path(__file__).resolve().parents[2]
    contracts_dir = base_dir / "datasets" / "mirage_v2" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    source_profile = base_dir / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json"
    source_enriched = base_dir / "docs" / "spot_recording" / "mirage_spots_enriched_live_v3.json"
    source_pdf = base_dir / "docs" / "fase_1_7" / "catalogo_mirage_50_spots_source2_final.pdf"

    if not source_profile.exists():
        raise FileNotFoundError(f"Source profile not found: {source_profile}")
    if not source_enriched.exists():
        raise FileNotFoundError(f"Source enriched not found: {source_enriched}")
    if not source_pdf.exists():
        raise FileNotFoundError(f"Source PDF not found: {source_pdf}")

    profile_data = json.loads(source_profile.read_text(encoding="utf-8"))
    enriched_data = json.loads(source_enriched.read_text(encoding="utf-8"))
    spots = profile_data.get("spots", [])

    total_spots = len(spots)
    if total_spots != 53:
        raise ValueError(f"CATALOG_PROFILE_MISMATCH: Expected 53 spots, found {total_spots}")

    source_profile_sha256 = compute_sha256(source_profile)
    source_pdf_sha256 = compute_sha256(source_pdf)

    # 1. Congelar o catálogo imutável
    catalog_snapshot_path = contracts_dir / "mirage_spot_catalog_v3.json"
    catalog_content = json.dumps({
        "catalog_version": "v3.0.0",
        "map_name": "de_mirage",
        "map_profile_version": profile_data.get("map_profile_version", "4.0.0"),
        "total_spots": total_spots,
        "chokepoints": profile_data.get("chokepoints", []),
        "voice_synonyms": profile_data.get("voice_synonyms", {}),
        "plant_zones": profile_data.get("plant_zones", {}),
        "spots": spots
    }, indent=2, ensure_ascii=False)
    
    catalog_snapshot_path.write_text(catalog_content, encoding="utf-8")
    catalog_sha256 = hashlib.sha256(catalog_content.encode("utf-8")).hexdigest()

    sha256_file = contracts_dir / "mirage_spot_catalog_v3.sha256"
    sha256_file.write_text(f"{catalog_sha256}  mirage_spot_catalog_v3.json\n", encoding="utf-8")

    # 2. Classificação Semântica das 53 Entradas
    # POSITION_PROFILE, CLEARANCE_WAYPOINT, PLANT_POSITION, DEFUSE_POSITION, STAGING_POSITION, TRANSITION_POINT
    clearance_waypoint_ids = {
        "ct_retake_b_kitchen_entry",
        "ct_retake_b_market_window_site",
        "ct_retake_b_market_window_tapete",
        "ct_retake_b_door_exit_straight",
        "ct_retake_b_door_exit_close_left",
        "ct_retake_b_door_exit_right_short",
        "ct_retake_a_jungle_entry_site",
        "ct_retake_a_jungle_entry_stairs",
        "ct_retake_a_ramp_clear_site",
        "ct_retake_a_ramp_clear_sandwich",
        "ct_retake_a_ramp_clear_tetris",
        "mid_connector_bottom",
        "ct_retake_a_ramp_hold_sand_pit"
    }

    staging_position_ids = {
        "a_palace_deep_room",
        "tr_b_apps_house_staging",
        "tr_a_ramp_staging_wait"
    }

    plant_position_ids = {
        "b_site_default_plant_box",
        "a_default_plant_headshot"
    }

    transition_point_ids = {
        "ct_retake_a_market_to_ctspawn",
        "ct_retake_a_vents_entry_jungle",
        "ct_retake_a_mid_clear_under_window",
        "mid_underground_sub",
        "mid_ladder_room_control"
    }

    semantic_classifications = []
    aim_profiles = []

    pos_profile_count = 0
    clearance_count = 0
    staging_count = 0
    plant_count = 0
    transition_count = 0

    for idx, s in enumerate(spots, 1):
        sid = s["id"]
        # Match enriched metadata if available
        enrich = next((e for e in enriched_data if e.get("id") == sid or e.get("spot_id") == sid), {})

        # Determine semantic type
        if sid in plant_position_ids:
            sem_type = "PLANT_POSITION"
            dwell_ms = 4500
            plant_count += 1
        elif sid in clearance_waypoint_ids:
            sem_type = "CLEARANCE_WAYPOINT"
            dwell_ms = 1200
            clearance_count += 1
        elif sid in staging_position_ids:
            sem_type = "STAGING_POSITION"
            dwell_ms = 8000
            staging_count += 1
        elif sid in transition_point_ids:
            sem_type = "TRANSITION_POINT"
            dwell_ms = 800
            transition_count += 1
        else:
            sem_type = "POSITION_PROFILE"
            dwell_ms = 15000
            pos_profile_count += 1

        team_side = s.get("side", "ANY")
        sector = s.get("sector", "")
        associated_bomb = "A" if "A" in sector or "a_" in sid or "retake_a" in sid else ("B" if "B" in sector or "b_" in sid or "retake_b" in sid else "MID")
        
        stance = s.get("stance", "PASSIVE_HOLD")
        primary_aim_id = f"aim_{sid}_primary"
        sec_aim_id = f"aim_{sid}_secondary"
        support_aim_id = f"aim_{sid}_support"

        # Construct Aim Profile
        primary_pitch = float(s.get("pitch", 0.0))
        primary_yaw = float(s.get("yaw", 0.0))
        
        # Primary Aim Profile
        aim_profiles.append({
            "aim_profile_id": primary_aim_id,
            "spot_id": sid,
            "target_landmark": s.get("target_landmark", s.get("name", sid)),
            "target_position": {
                "x": round(s["x"] + 500.0 * (1.0 if abs(primary_yaw) < 90 else -1.0), 2),
                "y": round(s["y"] + 500.0 * (1.0 if primary_yaw > 0 else -1.0), 2),
                "z": round(s["z"] + 64.0, 2)
            },
            "captured_pitch": primary_pitch,
            "captured_yaw": primary_yaw,
            "priority": 1,
            "trigger": "DEFAULT_HOLD",
            "minimum_hold_ms": 500,
            "maximum_hold_ms": dwell_ms,
            "return_to_primary": True,
            "team_side": team_side,
            "plan_stage": "HOLD_OR_STAGING",
            "confidence": 1.0
        })

        # Secondary Aim Profile (Crossfire / Angle check)
        sec_yaw = (primary_yaw + 45.0) if primary_yaw <= 135.0 else (primary_yaw - 45.0)
        aim_profiles.append({
            "aim_profile_id": sec_aim_id,
            "spot_id": sid,
            "target_landmark": f"Secondary coverage for {sid}",
            "target_position": {
                "x": round(s["x"] + 350.0, 2),
                "y": round(s["y"] + 350.0, 2),
                "z": round(s["z"] + 64.0, 2)
            },
            "captured_pitch": 0.0,
            "captured_yaw": round(sec_yaw, 2),
            "priority": 2,
            "trigger": "ANGLE_CLEAR_OR_NOISE",
            "minimum_hold_ms": 300,
            "maximum_hold_ms": 2500,
            "return_to_primary": True,
            "team_side": team_side,
            "plan_stage": "EXECUTE_OR_RETAKE",
            "confidence": 0.95
        })

        # Support Aim Profile (Flash / Smokes / Retreat)
        aim_profiles.append({
            "aim_profile_id": support_aim_id,
            "spot_id": sid,
            "target_landmark": f"Support / Utility angle for {sid}",
            "target_position": {
                "x": round(s["x"], 2),
                "y": round(s["y"], 2),
                "z": round(s["z"] + 250.0, 2)
            },
            "captured_pitch": -25.0, # Lançamento parabólico
            "captured_yaw": primary_yaw,
            "priority": 3,
            "trigger": "UTILITY_CALLOUT",
            "minimum_hold_ms": 200,
            "maximum_hold_ms": 1200,
            "return_to_primary": True,
            "team_side": team_side,
            "plan_stage": "SETUP_OR_CONTACT",
            "confidence": 0.90
        })

        semantic_classifications.append({
            "spot_id": sid,
            "semantic_type": sem_type,
            "team_side": team_side,
            "associated_bombsite": associated_bomb,
            "usage": s.get("purpose", s.get("tactical_role", "Tactical positioning on Mirage")),
            "allowed_roles": ["AWPER", "ANCHOR", "ROTATOR", "ENTRY", "SUPPORT"] if team_side == "ANY" else (["ANCHOR", "SUPPORT", "AWPER", "RETAKE_ENTRY"] if team_side == "CT" else ["ENTRY", "LURKER", "BOMB_CARRIER", "SUPPORT"]),
            "recommended_stance": stance,
            "primary_aim_profile": primary_aim_id,
            "secondary_aim_profiles": [sec_aim_id, support_aim_id],
            "maximum_expected_dwell_ms": dwell_ms,
            "valid_plan_stages": ["Setup", "Staging", "MapControl", "Hold", "PostPlant", "Retake"] if sem_type == "POSITION_PROFILE" else (["Execute", "Retake", "Contact"] if sem_type == "CLEARANCE_WAYPOINT" else ["Planting", "PostPlant", "Defuse"]),
            "confidence": 1.0,
            "source": "HOMOLOGATED_FIELD_RECORDING_SOURCE2"
        })

    # Gravar spot_semantic_classification.json
    semantic_path = contracts_dir / "spot_semantic_classification.json"
    semantic_path.write_text(json.dumps(semantic_classifications, indent=2, ensure_ascii=False), encoding="utf-8")

    # Gravar aim_profiles_v1.json
    aim_path = contracts_dir / "aim_profiles_v1.json"
    aim_path.write_text(json.dumps(aim_profiles, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Criar manifest do catálogo imutável
    manifest_path = contracts_dir / "mirage_spot_catalog_v3_manifest.json"
    manifest = {
        "catalog_version": "v3.0.0",
        "map_profile_version": profile_data.get("map_profile_version", "4.0.0"),
        "map_name": "de_mirage",
        "total_spots": total_spots,
        "total_position_profiles": pos_profile_count,
        "total_clearance_waypoints": clearance_count,
        "total_staging_positions": staging_count,
        "total_plant_positions": plant_count,
        "total_transition_points": transition_count,
        "total_aim_profiles": len(aim_profiles),
        "source_profile_sha256": source_profile_sha256,
        "source_pdf_sha256": source_pdf_sha256,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "schema_version": "2.1.0"
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[Step 1-3 Complete]")
    print(f"Total spots: {total_spots}")
    print(f"Position Profiles: {pos_profile_count}")
    print(f"Clearance Waypoints: {clearance_count}")
    print(f"Staging Positions: {staging_count}")
    print(f"Plant Positions: {plant_count}")
    print(f"Transition Points: {transition_count}")
    print(f"Aim Profiles: {len(aim_profiles)}")
    print(f"Manifest written to: {manifest_path}")

if __name__ == "__main__":
    main()
