import math
from pathlib import Path
import re

contract_path = Path("tools/mlmove_pipeline/contract_spec.py")
with open(contract_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Clean up empty lines excess
cleaned_lines = []
last_empty = False
for line in lines:
    stripped = line.strip()
    if not stripped:
        if not last_empty:
            cleaned_lines.append("\n")
            last_empty = True
    else:
        cleaned_lines.append(line.rstrip() + "\n")
        last_empty = False

content = "".join(cleaned_lines)

# Ensure quantize_angle_to_direction_index is NaN resilient
quantize_func_old = """def quantize_angle_to_direction_index(angle_rad: float) -> int:
    \"\"\"Converte um ângulo em radianos no plano XY para o índice discreto 0..15 (22.5 graus por fatia).\"\"\"
    deg = angle_rad * (180.0 / math.pi)
    if deg < 0.0:
        deg += 360.0
    idx = int(round(deg / 22.5)) % 16
    return idx"""

quantize_func_new = """def quantize_angle_to_direction_index(angle_rad: float) -> int:
    \"\"\"Converte um ângulo em radianos no plano XY para o índice discreto 0..15 (22.5 graus por fatia).\"\"\"
    if math.isnan(angle_rad) or math.isinf(angle_rad):
        return 0
    deg = angle_rad * (180.0 / math.pi)
    if deg < 0.0:
        deg += 360.0
    idx = int(round(deg / 22.5)) % 16
    return idx"""

if quantize_func_old in content:
    content = content.replace(quantize_func_old, quantize_func_new)
else:
    print("Warning: quantize_func_old not found directly, performing regex replacement")
    pattern = r"def quantize_angle_to_direction_index\(angle_rad: float\) -> int:.*?(?=def encode_action)"
    replacement = quantize_func_new + "\n\n\n"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Ensure velocity_to_action_id is NaN resilient
velocity_func_pattern = r"def velocity_to_action_id\(.*?-> int:.*?(?=def encode_weapon_category)"
velocity_func_new = """def velocity_to_action_id(
    vx: float,
    vy: float,
    vz: float,
    is_ducking: bool,
    is_walking_shift: bool,
    is_airborne_or_jump: bool = False,
) -> int:
    \"\"\"
    Converte a velocidade real do jogador no tick futuro para o ActionId discreto (0..96).
    \"\"\"
    if math.isnan(vx) or math.isnan(vy) or math.isnan(vz):
        return 0
    speed_2d = float(math.hypot(vx, vy))
    if math.isnan(speed_2d) or (speed_2d < 18.0 and not is_airborne_or_jump and abs(vz) <= 45.0):
        return 0  # StandStill

    is_jump = is_airborne_or_jump or (abs(vz) > 45.0)

    angle_rad = math.atan2(vy, vx)
    dir_idx = quantize_angle_to_direction_index(angle_rad)

    if is_ducking or speed_2d < 102.0:
        speed_tier = SPEED_TIER_CROUCH
    elif is_walking_shift or speed_2d < 165.0:
        speed_tier = SPEED_TIER_WALK_SHIFT
    else:
        speed_tier = SPEED_TIER_RUN

    return encode_action(dir_idx, speed_tier, is_jump)

"""

content = re.sub(velocity_func_pattern, velocity_func_new, content, flags=re.DOTALL)

with open(contract_path, "w", encoding="utf-8") as f:
    f.write(content)
print("contract_spec.py updated successfully.")
