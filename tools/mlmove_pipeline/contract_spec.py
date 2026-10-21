"""
Contrato Estrito C# <-> Python para o Motor MLMove 16Hz (Fase 6A / 6B / 6C).
Espelha bit-a-bit as definições de `src/CsBotManager/MicroMoveEngine.cs`:
- Input Tensor: `input_state` shape `[batch_size, 10, 18]`, dtype `float32`
- Output Tensor: `output_logits` shape `[batch_size, 10, 3, 97]`, dtype `float32`
- Espaço de 97 Ações:
    * ActionId 0: StandStill (Parado)
    * ActionId 1..96: 1 + (jump_idx * 48) + (speed_idx * 16) + dir_idx
      onde dir_idx in [0..15] (fatias angulares de 22.5 graus no plano global XY),
      speed_idx in [0=Run (250u/s), 1=WalkShift (130u/s), 2=Crouch (85u/s)],
      jump_idx in [0=Ground, 1=Jump]
- Simetria Anti-Wallhack (Fog of War):
    * Inimigos fora do cone de visão (LOS/FOV) e sem evento sonoro recente (<= 1000u nos últimos 4.0s)
      têm as features [0..12] e [15] zeradas ([0.0]).
"""

from __future__ import annotations
import math
import numpy as np

MAX_PLAYERS: int = 10
FEATURE_DIM: int = 18
HORIZONS_COUNT: int = 3
ACTION_SPACE_SIZE: int = 97

ONNX_INPUT_NAME: str = "input_state"
ONNX_OUTPUT_NAME: str = "output_logits"

# Diretórios obrigatórios no NVMe D:\ (Regra de Armazenamento)
PIPELINE_ROOT_D: str = r"D:\CS2_MLMove_Pipeline"
RAW_DEMOS_DIR_D: str = r"D:\CS2_MLMove_Pipeline\raw_demos"
EXTRACTED_TENSORS_DIR_D: str = r"D:\CS2_MLMove_Pipeline\extracted_tensors"
CHECKPOINTS_DIR_D: str = r"D:\CS2_MLMove_Pipeline\checkpoints"
SERVER_MODELS_DIR_H: str = r"H:\CS2_AI_Server\models"

SPEED_TIER_RUN: int = 0
SPEED_TIER_WALK_SHIFT: int = 1
SPEED_TIER_CROUCH: int = 2


def quantize_angle_to_direction_index(angle_rad: float) -> int:
    """Converte um ângulo em radianos no plano XY para o índice discreto 0..15 (22.5 graus por fatia)."""
    deg = angle_rad * (180.0 / math.pi)
    if deg < 0.0:
        deg += 360.0
    idx = int(round(deg / 22.5)) % 16
    return idx


def encode_action(dir_index: int, speed_tier: int, is_jump: bool) -> int:
    """Codifica (dir_index, speed_tier, is_jump) no ActionId [0..96] idêntico ao MicroMoveStep.EncodeAction em C#."""
    if dir_index < 0:
        return 0
    clamped_dir = ((dir_index % 16) + 16) % 16
    speed_idx = max(0, min(2, int(speed_tier)))
    jump_idx = 1 if is_jump else 0
    return 1 + (jump_idx * 48) + (speed_idx * 16) + clamped_dir


def decode_action(action_id: int) -> tuple[int, int, bool]:
    """Decodifica ActionId [0..96] em (dir_index, speed_tier, is_jump)."""
    if action_id <= 0 or action_id > 96:
        return (-1, SPEED_TIER_RUN, False)
    zero_based = action_id - 1
    jump_idx = zero_based // 48
    rem = zero_based % 48
    speed_idx = rem // 16
    dir_idx = rem % 16
    return (dir_idx, speed_idx, jump_idx == 1)


def velocity_to_action_id(
    vx: float,
    vy: float,
    vz: float,
    is_ducking: bool = False,
    is_walking_shift: bool = False,
    is_airborne_or_jump: bool = False,
) -> int:
    """
    Converte a velocidade real do jogador no tick futuro para o ActionId discreto (0..96).
    """
    speed_2d = math.hypot(vx, vy)
    is_jump = is_airborne_or_jump or (abs(vz) > 45.0)

    if speed_2d < 18.0 and not is_jump:
        return 0  # StandStill

    angle_rad = math.atan2(vy, vx)
    dir_idx = quantize_angle_to_direction_index(angle_rad)

    if is_ducking or speed_2d < 102.0:
        speed_tier = SPEED_TIER_CROUCH
    elif is_walking_shift or speed_2d < 165.0:
        speed_tier = SPEED_TIER_WALK_SHIFT
    else:
        speed_tier = SPEED_TIER_RUN

    return encode_action(dir_idx, speed_tier, is_jump)


def encode_weapon_category(weapon_name: str) -> float:
    """Mesma normalização de categoria de arma de MicroMoveEngine.EncodeWeaponCategory em C#."""
    if not weapon_name:
        return 0.0
    w = weapon_name.lower()
    if "knife" in w or "bayonet" in w:
        return 0.2
    if "awp" in w or "ssg08" in w:
        return 1.0
    if any(k in w for k in ("ak47", "m4a1", "galilar", "famas", "aug", "sg556")):
        return 0.8
    if any(k in w for k in ("mac10", "mp9", "mp7", "ump45", "p90", "bizon")):
        return 0.6
    return 0.4


def can_team_perceive_enemy_2d(
    ally_positions: np.ndarray,
    ally_yaws_deg: np.ndarray,
    ally_alive: np.ndarray,
    enemy_pos: np.ndarray,
    enemy_speed_2d: float,
    enemy_fired_recently: bool = False,
) -> bool:
    """
    Filtro Anti-Wallhack Simétrico (Fog of War) para treinamento:
    Verifica se algum aliado vivo percebe legitimamente o inimigo via:
    1) Cone visual frontal (FOV <= 105 graus e distância <= 2600u sem obstrução grosseira de nível Z)
    2) Pista sonora legítima (inimigo correndo > 135 u/s ou atirando a <= 1050 unidades de distância).
    """
    for idx in range(len(ally_alive)):
        if not ally_alive[idx]:
            continue
        ax, ay, az = ally_positions[idx]
        dx = enemy_pos[0] - ax
        dy = enemy_pos[1] - ay
        dz = enemy_pos[2] - az
        dist_2d = math.hypot(dx, dy)

        # Gatilho de Áudio Legítimo (~1000u passos correndo ou tiro)
        if dist_2d <= 1050.0 and (enemy_speed_2d > 138.0 or enemy_fired_recently):
            return True

        # Gatilho de Visão (Cone de FOV humano ~100 graus e proximidade de combate)
        if dist_2d <= 2400.0 and abs(dz) <= 280.0:
            yaw_rad = ally_yaws_deg[idx] * (math.pi / 180.0)
            fx = math.cos(yaw_rad)
            fy = math.sin(yaw_rad)
            if dist_2d > 1e-3:
                cos_angle = (dx * fx + dy * fy) / dist_2d
                if cos_angle >= 0.38:  # ~67.5 graus para cada lado do centro da mira
                    return True
    return False


def build_standardized_player_row(
    x: float,
    y: float,
    z: float,
    vx: float,
    vy: float,
    vz: float,
    yaw_deg: float,
    pitch_deg: float,
    health: float,
    armor: float,
    weapon_name: str,
    role_code: float,
    is_terrorist: bool,
    is_alive: bool,
    has_c4: bool,
    is_bomb_planted: bool,
    round_time_remaining: float,
    is_masked_enemy: bool = False,
) -> np.ndarray:
    """
    Gera o vetor de 18 features float32 idêntico a `BuildStandardizedInputTensor` / `BuildFogOfWarInputTensorForTeam` em C#.
    """
    row = np.zeros(FEATURE_DIM, dtype=np.float32)
    row[13] = 1.0 if is_terrorist else 0.0
    row[14] = 1.0 if is_alive else 0.0
    row[16] = 1.0 if is_bomb_planted else 0.0
    row[17] = float(np.clip(round_time_remaining / 115.0, 0.0, 1.0))

    if not is_alive or is_masked_enemy:
        # Venda nos olhos da IA: inimigo não detectado ou jogador morto mantém [0..12] e [15] zerados!
        return row

    row[0] = float(np.clip(x / 4096.0, -1.5, 1.5))
    row[1] = float(np.clip(y / 4096.0, -1.5, 1.5))
    row[2] = float(np.clip(z / 1024.0, -1.5, 1.5))

    row[3] = float(np.clip(vx / 250.0, -1.5, 1.5))
    row[4] = float(np.clip(vy / 250.0, -1.5, 1.5))
    row[5] = float(np.clip(vz / 250.0, -1.5, 1.5))

    yaw_rad = yaw_deg * (math.pi / 180.0)
    row[6] = math.cos(yaw_rad)
    row[7] = math.sin(yaw_rad)
    row[8] = float(np.clip(pitch_deg / 90.0, -1.0, 1.0))

    row[9] = float(np.clip(health / 100.0, 0.0, 1.0))
    row[10] = float(np.clip(armor / 100.0, 0.0, 1.0))
    row[11] = encode_weapon_category(weapon_name)
    row[12] = float(np.clip(role_code, 0.25, 1.0))
    row[15] = 1.0 if has_c4 else 0.0
    return row
