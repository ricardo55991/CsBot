from pathlib import Path
import re

extract_path = Path("tools/mlmove_pipeline/extract_16hz_tensors.py")
with open(extract_path, "r", encoding="utf-8") as f:
    code = f.read()

# Fix imports to work both as script and module
import_old = """from contract_spec import (
    EXTRACTED_TENSORS_DIR_D,
    FEATURE_DIM,
    HORIZONS_COUNT,
    MAX_PLAYERS,
    RAW_DEMOS_DIR_D,
    build_standardized_player_row,
    can_team_perceive_enemy_2d,
     encode_weapon_category,
    velocity_to_action_id,
)"""

import_new = """try:
    from contract_spec import (
        EXTRACTED_TENSORS_DIR_D,
        FEATURE_DIM,
        HORIZONS_COUNT,
        MAX_PLAYERS,
        RAW_DEMOS_DIR_D,
        build_standardized_player_row,
        can_team_perceive_enemy_2d,
        encode_weapon_category,
        velocity_to_action_id,
    )
except ImportError:
    from tools.mlmove_pipeline.contract_spec import (
        EXTRACTED_TENSORS_DIR_D,
        FEATURE_DIM,
        HORIZONS_COUNT,
        MAX_PLAYERS,
        RAW_DEMOS_DIR_D,
        build_standardized_player_row,
        can_team_perceive_enemy_2d,
        encode_weapon_category,
        velocity_to_action_id,
    )
import math
from typing import Any

def safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except Exception:
        return default
"""

code = code.replace(import_old, import_new)

# Fix is_Freeze_period -> is_freeze_period
code = code.replace('"is_Freeze_period"', '"is_freeze_period"')

# Update player extraction loop to use safe_float
old_loop_chunk = """            teams[idx] = int(p.get("team_num", 0) or 0)
            positions[idx, 0] = float(p.get("X", 0.0) or 0.0)
            positions[idx, 1] = float(p.get("Y", 0.0) or 0.0)
            positions[idx, 2] = float(p.get("Z", 0.0) or 0.0)
            yaws[idx] = float(p.get("yaw", 0.0) or 0.0)

            vx0 = float(p.get("velocity_X", 0.0) or 0.0)
            vy0 = float(p.get("velocity_Y", 0.0) or 0.0)
            vz0 = float(p.get("velocity_Z", 0.0) or 0.0)
            speeds_2d[idx] = float(np.hypot(vx0, vy0))

            if alive:
                duck0 = float(p.get("duck_amount", 0.0) or 0.0) > 0.45
                walk0 = bool(p.get("is_walking", False))
                actions_3h[idx, 0] = velocity_to_action_id(vx0, vy0, vz0, duck0, walk0)

                p1 = g1_map.get(sid, p)
                vx1 = float(p1.get("velocity_X", 0.0) or 0.0)
                vy1 = float(p1.get("velocity_Y", 0.0) or 0.0)
                vz1 = float(p1.get("velocity_Z", 0.0) or 0.0)
                duck1 = float(p1.get("duck_amount", 0.0) or 0.0) > 0.45
                walk1 = bool(p1.get("is_walking", False))
                actions_3h[idx, 1] = velocity_to_action_id(vx1, vy1, vz1, duck1, walk1)

                p2 = g2_map.get(sid, p)
                vx2 = float(p2.get("velocity_X", 0.0) or 0.0)
                vy2 = float(p2.get("velocity_Y", 0.0) or 0.0)
                vz2 = float(p2.get("velocity_Z", 0.0) or 0.0)
                duck2 = float(p2.get("duck_amount", 0.0) or 0.0) > 0.45
                walk2 = bool(p2.get("is_walking", False))
                actions_3h[idx, 2] = velocity_to_action_id(vx2, vy2, vz2, duck2, walk2)"""

new_loop_chunk = """            teams[idx] = int(safe_float(p.get("team_num", 0)))
            positions[idx, 0] = safe_float(p.get("X", 0.0))
            positions[idx, 1] = safe_float(p.get("Y", 0.0))
            positions[idx, 2] = safe_float(p.get("Z", 0.0))
            yaws[idx] = safe_float(p.get("yaw", 0.0))

            vx0 = safe_float(p.get("velocity_X", 0.0))
            vy0 = safe_float(p.get("velocity_Y", 0.0))
            vz0 = safe_float(p.get("velocity_Z", 0.0))
            speeds_2d[idx] = float(np.hypot(vx0, vy0))

            if alive:
                duck0 = safe_float(p.get("duck_amount", 0.0)) > 0.45
                walk0 = bool(p.get("is_walking", False))
                actions_3h[idx, 0] = velocity_to_action_id(vx0, vy0, vz0, duck0, walk0)

                p1 = g1_map.get(sid, p)
                vx1 = safe_float(p1.get("velocity_X", 0.0))
                vy1 = safe_float(p1.get("velocity_Y", 0.0))
                vz1 = safe_float(p1.get("velocity_Z", 0.0))
                duck1 = safe_float(p1.get("duck_amount", 0.0)) > 0.45
                walk1 = bool(p1.get("is_walking", False))
                actions_3h[idx, 1] = velocity_to_action_id(vx1, vy1, vz1, duck1, walk1)

                p2 = g2_map.get(sid, p)
                vx2 = safe_float(p2.get("velocity_X", 0.0))
                vy2 = safe_float(p2.get("velocity_Y", 0.0))
                vz2 = safe_float(p2.get("velocity_Z", 0.0))
                duck2 = safe_float(p2.get("duck_amount", 0.0)) > 0.45
                walk2 = bool(p2.get("is_walking", False))
                actions_3h[idx, 2] = velocity_to_action_id(vx2, vy2, vz2, duck2, walk2)"""

code = code.replace(old_loop_chunk, new_loop_chunk)

# Also update build_standardized_player_row call with safe_float
old_build_call = """                tensor_step[idx] = build_standardized_player_row(
                    x=float(positions[idx, 0]),
                    y=float(positions[idx, 1]),
                    z=float(positions[idx, 2]),
                    vx=float(p.get("velocity_X", 0.0) or 0.0),
                    vy=float(p.get("velocity_Y", 0.0) or 0.0),
                    vz=float(p.get("velocity_Z", 0.0) or 0.0),
                    yaw_deg=float(yaws[idx]),
                    pitch_deg=float(p.get("pitch", 0.0) or 0.0),
                    health=float(p.get("health", 0.0) or 0.0),
                    armor=float(p.get("armor_value", 0.0) or 0.0),
                    weapon_name=str(p.get("active_weapon_name", "") or ""),
                    role_code=role_cycle[idx % len(role_cycle)],
                    is_terrorist=(teams[idx] == 2),
                    is_alive=bool(alive_flags[idx]),
                    has_c4=("c4" in str(p.get("active_weapon_name", "") or "").lower()),
                    is_bomb_planted=False,
                    round_time_remaining=max(5.0, 115.0 - ((t0 - all_ticks[0]) % (115 * 64)) / 64.0),
                    is_masked_enemy=is_masked,
                )"""

new_build_call = """                tensor_step[idx] = build_standardized_player_row(
                    x=safe_float(positions[idx, 0]),
                    y=safe_float(positions[idx, 1]),
                    z=safe_float(positions[idx, 2]),
                    vx=safe_float(p.get("velocity_X", 0.0)),
                    vy=safe_float(p.get("velocity_Y", 0.0)),
                    vz=safe_float(p.get("velocity_Z", 0.0)),
                    yaw_deg=safe_float(yaws[idx]),
                    pitch_deg=safe_float(p.get("pitch", 0.0)),
                    health=safe_float(p.get("health", 0.0)),
                    armor=safe_float(p.get("armor_value", 0.0)),
                    weapon_name=str(p.get("active_weapon_name", "") or ""),
                    role_code=role_cycle[idx % len(role_cycle)],
                    is_terrorist=(teams[idx] == 2),
                    is_alive=bool(alive_flags[idx]),
                    has_c4=("c4" in str(p.get("active_weapon_name", "") or "").lower()),
                    is_bomb_planted=False,
                    round_time_remaining=max(5.0, 115.0 - ((t0 - all_ticks[0]) % (115 * 64)) / 64.0),
                    is_masked_enemy=is_masked,
                )"""

code = code.replace(old_build_call, new_build_call)

with open(extract_path, "w", encoding="utf-8") as f:
    f.write(code)

print("extract_16hz_tensors.py updated successfully.")
