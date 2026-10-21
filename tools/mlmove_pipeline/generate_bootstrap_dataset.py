"""
Fase 6C / Etapa 5 (Bootstrap Dataset Generator):
Gera em `D:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\bootstrap_mirage_16hz.npz` um dataset tático inicial
de trajetórias coordenadas da `de_mirage` a 16Hz, lendo os 35 Spots e 13 Chokepoints reais de
`src/CsBotManager/MapProfiles/de_mirage.json` (e também extraindo demos `.dem` locais se existirem).

Cobre os 5 arquétipos fundamentais do MLMove com máscara Anti-Wallhack (Fog of War):
1. Counter-Strafe (Velocity Zeroing): parada brusca (t=0ms pulso reverso Run -> t=+125ms StandStill -> t=+250ms StandStill) ao avistar inimigo com Rifle/AWP.
2. Trade Spacing Repulsion (< 140u): separação lateral coordenada quando dois aliados colam na mesma esquina.
3. Trade Kill Wide Swing (250-400u): abertura em arco escalonada (+60 graus) quando o Entry na frente entra em combate.
4. Wall-Hugging ("Fatiar a Torta"): tangenciamento de paredes nos 13 Chokepoints da Mirage (Palácio, Caverna, Janela, Liga, Tapete).
5. Post-Plant Retake & Anchor Jiggle Peek: aproximação furtiva (WalkShift) seguida de abertura rápida (Run -> StandStill).
"""

from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from contract_spec import (
    EXTRACTED_TENSORS_DIR_D,
    FEATURE_DIM,
    HORIZONS_COUNT,
    MAX_PLAYERS,
    SPEED_TIER_CROUCH,
    SPEED_TIER_RUN,
    SPEED_TIER_WALK_SHIFT,
    build_standardized_player_row,
    encode_action,
    quantize_angle_to_direction_index,
)
from extract_16hz_tensors import process_demos_folder


REPO_ROOT = Path(__file__).resolve().parents[2]
MIRAGE_PROFILE_PATH = REPO_ROOT / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json"


def load_mirage_geometry() -> Tuple[List[Dict], List[Dict]]:
    if not MIRAGE_PROFILE_PATH.exists():
        raise FileNotFoundError(f"Perfil de mapa não encontrado: {MIRAGE_PROFILE_PATH}")
    data = json.loads(MIRAGE_PROFILE_PATH.read_text(encoding="utf-8"))
    spots = data.get("spots") or data.get("tactical_spots") or []
    chokepoints = data.get("chokepoints", [])
    return spots, chokepoints


def generate_mirage_tactical_bootstrap(num_samples: int = 24000, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    spots, chokepoints = load_mirage_geometry()

    X = np.zeros((num_samples, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32)
    Y = np.zeros((num_samples, MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8)

    ct_weapons = ["weapon_m4a1", "weapon_m4a1_silencer", "weapon_awp", "weapon_famas", "weapon_mp9"]
    tr_weapons = ["weapon_ak47", "weapon_awp", "weapon_galilar", "weapon_mac10", "weapon_deagle"]
    roles = [0.25, 0.50, 0.75, 1.00, 0.50]

    for s_idx in range(num_samples):
        scenario_type = s_idx % 5
        round_time = float(rng.uniform(18.0, 110.0))
        bomb_planted = bool(scenario_type == 4 or rng.random() < 0.22)
        obs_is_terrorist = bool(s_idx % 2 == 1)

        # Escolhe um Chokepoint e Spots de referência reais da de_mirage
        cp = chokepoints[int(rng.integers(0, len(chokepoints)))]
        cp_x, cp_y, cp_z = float(cp["x"]), float(cp["y"]), float(cp["z"])

        for p_idx in range(MAX_PLAYERS):
            is_tr = p_idx >= 5
            is_teammate_of_obs = (is_tr == obs_is_terrorist)
            role_code = roles[p_idx % 5]
            weapon = tr_weapons[p_idx % 5] if is_tr else ct_weapons[p_idx % 5]
            is_alive = bool(rng.random() < 0.90 or p_idx in (0, 1, 5, 6))

            if not is_alive:
                X[s_idx, p_idx] = build_standardized_player_row(
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", role_code, is_tr, False, False, bomb_planted, round_time
                )
                Y[s_idx, p_idx, :] = 0
                continue

            spot = spots[int(rng.integers(0, len(spots)))]
            base_x = float(spot["x"]) + float(rng.normal(0.0, 65.0))
            base_y = float(spot["y"]) + float(rng.normal(0.0, 65.0))
            base_z = float(spot["z"])
            yaw_deg = float(spot.get("yaw", spot.get("look_at_yaw", rng.uniform(-180.0, 180.0)))) + float(rng.normal(0.0, 12.0))
            pitch_deg = float(spot.get("pitch", spot.get("look_at_pitch", 0.0))) + float(rng.normal(0.0, 3.0))
            hp = float(rng.integers(35, 101))
            armor = float(rng.integers(50, 101))
            has_c4 = bool(is_tr and (p_idx == 5) and not bomb_planted)

            # Define velocidade e ação multi-horizonte baseada no arquétipo tático
            if scenario_type == 0:
                # Arquétipo 1: COUNTER-STRAFE (Velocity Zeroing ao avistar inimigo com rifle/AWP)
                move_angle = float(rng.uniform(-math.pi, math.pi))
                speed = float(rng.uniform(135.0, 245.0))
                vx = math.cos(move_angle) * speed
                vy = math.sin(move_angle) * speed
                vz = 0.0

                rev_angle = math.atan2(-vy, -vx)
                rev_dir = quantize_angle_to_direction_index(rev_angle)
                act0 = encode_action(rev_dir, SPEED_TIER_RUN, False)
                act1 = 0  # StandStill (+125ms)
                act2 = 0  # StandStill (+250ms)
                is_masked = False

            elif scenario_type == 1:
                # Arquétipo 2: TRADE SPACING REPULSION (< 140u de aliado no mesmo setor)
                base_x = cp_x + float(rng.uniform(-75.0, 75.0))
                base_y = cp_y + float(rng.uniform(-75.0, 75.0))
                base_z = cp_z
                away_angle = math.atan2(base_y - cp_y, base_x - cp_x) + (0.55 if p_idx % 2 == 0 else -0.55)
                vx = math.cos(away_angle) * 180.0
                vy = math.sin(away_angle) * 180.0
                vz = 0.0

                rep_dir = quantize_angle_to_direction_index(away_angle)
                rep_act = encode_action(rep_dir, SPEED_TIER_RUN, False)
                act0 = rep_act
                act1 = rep_act
                act2 = 0
                is_masked = bool(not is_teammate_of_obs and rng.random() < 0.5)

            elif scenario_type == 2:
                # Arquétipo 3: TRADE KILL WIDE SWING (250-400u de distância do Entry)
                offset_dist = float(rng.uniform(250.0, 395.0))
                approach_angle = float(rng.uniform(-math.pi, math.pi))
                base_x = cp_x - math.cos(approach_angle) * offset_dist
                base_y = cp_y - math.sin(approach_angle) * offset_dist
                base_z = cp_z

                swing_offset = (math.pi / 3.2) if (p_idx % 2 == 0) else -(math.pi / 3.2)
                swing_angle = approach_angle + swing_offset
                vx = math.cos(approach_angle) * 215.0
                vy = math.sin(approach_angle) * 215.0
                vz = 0.0

                swing_dir = quantize_angle_to_direction_index(swing_angle)
                swing_act = encode_action(swing_dir, SPEED_TIER_RUN, False)
                act0 = swing_act
                act1 = swing_act
                act2 = 0
                is_masked = False

            elif scenario_type == 3:
                # Arquétipo 4: WALL-HUGGING ("Fatiando a Torta" nos Chokepoints da Mirage sem inimigo visível)
                base_x = cp_x + float(rng.uniform(-85.0, 85.0))
                base_y = cp_y + float(rng.uniform(-85.0, 85.0))
                base_z = cp_z
                move_angle = math.atan2(cp_y - base_y, cp_x - base_x)
                vx = math.cos(move_angle) * 195.0
                vy = math.sin(move_angle) * 195.0
                vz = 0.0

                hug_angle = move_angle + (0.38 if p_idx % 2 == 0 else -0.38)
                hug_dir = quantize_angle_to_direction_index(hug_angle)
                hug_act = encode_action(hug_dir, SPEED_TIER_RUN, False)
                act0 = hug_act
                act1 = hug_act
                act2 = hug_act
                # Na aproximação silenciosa de Hotzone, inimigos distantes estão mascarados pelo Fog of War!
                is_masked = not is_teammate_of_obs

            else:
                # Arquétipo 5: POST-PLANT RETAKE / ANCHOR PEEK (WalkShift -> Run Peek -> Crouch/StandStill)
                move_angle = math.atan2(cp_y - base_y, cp_x - base_x)
                vx = math.cos(move_angle) * 125.0
                vy = math.sin(move_angle) * 125.0
                vz = 0.0

                dir_idx = quantize_angle_to_direction_index(move_angle)
                act0 = encode_action(dir_idx, SPEED_TIER_WALK_SHIFT, False)
                act1 = encode_action(dir_idx, SPEED_TIER_RUN, False)
                act2 = encode_action(dir_idx, SPEED_TIER_CROUCH, False) if rng.random() < 0.5 else 0
                is_masked = bool(not is_teammate_of_obs and rng.random() < 0.65)

            X[s_idx, p_idx] = build_standardized_player_row(
                x=base_x,
                y=base_y,
                z=base_z,
                vx=vx,
                vy=vy,
                vz=vz,
                yaw_deg=yaw_deg,
                pitch_deg=pitch_deg,
                health=hp,
                armor=armor,
                weapon_name=weapon,
                role_code=role_code,
                is_terrorist=is_tr,
                is_alive=True,
                has_c4=has_c4,
                is_bomb_planted=bomb_planted,
                round_time_remaining=round_time,
                is_masked_enemy=is_masked,
            )
            Y[s_idx, p_idx, 0] = act0
            Y[s_idx, p_idx, 1] = act1
            Y[s_idx, p_idx, 2] = act2

    return X, Y


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerador de Dataset Bootstrap 16Hz para de_mirage no disco D:\\")
    parser.add_argument("--map", type=str, default="de_mirage")
    parser.add_argument("--samples", type=int, default=24000, help="Quantidade de janelas 16Hz (default: 24000)")
    args = parser.parse_args()

    out_dir = Path(EXTRACTED_TENSORS_DIR_D) / args.map
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Processa demos .dem reais caso existam em D:\CS2_MLMove_Pipeline\raw_demos\de_mirage
    real_samples = process_demos_folder(map_name=args.map, delete_after_extract=False)

    # 2. Gera o dataset bootstrap estruturado sobre os 35 Spots e 13 Chokepoints da de_mirage
    print(f"[generate_bootstrap_dataset] Gerando {args.samples:,} snapshots táticos 16Hz da {args.map}...")
    X, Y = generate_mirage_tactical_bootstrap(num_samples=args.samples)
    out_path = out_dir / f"bootstrap_{args.map}_16hz.npz"
    np.savez_compressed(out_path, X=X, Y=Y)

    size_kb = out_path.stat().st_size / 1024.0
    print(f"[generate_bootstrap_dataset] Salvo em: {out_path} ({size_kb:.1f} KB)")
    print(f"[generate_bootstrap_dataset] Shapes -> X: {X.shape} (float32) | Y: {Y.shape} (uint8) | Demos reais extraídas: {real_samples}")


if __name__ == "__main__":
    main()
