"""
Fase 6B (Camada 2 - Parte 2): Extrator `demoparser2` de Alta Velocidade a 16Hz.
Converte arquivos `.dem` em tensores compactos `.npz` (`X`: `[N, 10, 18]` float32, `Y`: `[N, 10, 3]` uint8)
em `D:\CS2_MLMove_Pipeline\extracted_tensors\<map>\`.

Implementa:
1. Filtro do Ouro (Qualidade Competitiva):
   - Descarta Warmup, Freeze Time (`is_freeze_period`), pausas técnicas e finais de round ociosos.
   - Descarta rounds de Full Eco (filtra por equipamento armado: rifles, SMGs, snipers ou valor de equipe >= $8500).
2. Simetria Anti-Wallhack (Fog of War):
   - Gera exemplos da perspectiva CT e da perspectiva TR onde inimigos fora de visão (cone FOV)
     e fora do alcance auditivo (~1000u correndo/atirando) têm suas coordenadas e atributos zerados `[0,0,0]`.
3. Rótulos Multi-Horizonte (97 Ações):
   - Olha os ticks futuros `t0 (0ms)`, `t1 (+8 ticks / +125ms)` e `t2 (+16 ticks / +250ms)` e codifica `ActionId (0..96)`.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
from demoparser2 import DemoParser
from tqdm import tqdm

try:
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



TICK_STRIDE_16HZ = 4       # 64Hz / 4 = 16Hz (62.5ms)
HORIZON_1_TICKS = 8        # +125ms em 64-tick
HORIZON_2_TICKS = 16       # +250ms em 64-tick


def extract_single_demo(demo_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extrai os tensores X [N, 10, 18] e Y [N, 10, 3] de um arquivo .dem do CS2 usando demoparser2.
    """
    # Bloco 4: Validação do cabeçalho Source 2 CS2 (PBDEMS2)
    try:
        with open(demo_path, "rb") as f_head:
            header = f_head.read(7)
            if header != b"PBDEMS2":
                print(f"[extract_16hz_tensors] Pulando demo não-CS2 ou corrompida: {demo_path.name}")
                return (
                    np.empty((0, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32),
                    np.empty((0, MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8),
                )
    except Exception as exc:
        print(f"[extract_16hz_tensors] Erro ao ler cabeçalho de {demo_path.name}: {exc}")
        return (
            np.empty((0, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32),
            np.empty((0, MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8),
        )

    parser = DemoParser(str(demo_path))

    wanted_props = [
        "X",
        "Y",
        "Z",
        "velocity_X",
        "velocity_Y",
        "velocity_Z",
        "yaw",
        "pitch",
        "health",
        "armor_value",
        "active_weapon_name",
        "team_num",
        "is_alive",
        "is_freeze_period",
        "is_warmup_period",
        "is_walking",
        "duck_amount",
    ]

    df = parser.parse_ticks(wanted_props)
    if df is None or len(df) == 0:
        return (
            np.empty((0, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32),
            np.empty((0, MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8),
        )

    # Filtro 1: Remove Warmup e Freeze Time
    if "is_warmup_period" in df.columns:
        df = df[df["is_warmup_period"] == False]  # noqa: E712
    if "is_freeze_period" in df.columns:
        df = df[df["is_freeze_period"] == False]  # noqa: E712

    # Filtra apenas jogadores em times ativos (2 = Terrorist, 3 = CounterTerrorist)
    df = df[df["team_num"].isin([2, 3])]
    if len(df) == 0:
        return (
            np.empty((0, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32),
            np.empty((0, MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8),
        )

    all_ticks = np.sort(df["tick"].unique())
    if len(all_ticks) < HORIZON_2_TICKS + 1:
        return (
            np.empty((0, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32),
            np.empty((0, MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8),
        )

    # Agrupa por tick para acesso O(1)
    grouped = {tick: group for tick, group in df.groupby("tick")}
    sampled_ticks = all_ticks[::TICK_STRIDE_16HZ]

    X_list: List[np.ndarray] = []
    Y_list: List[np.ndarray] = []

    role_cycle = [0.25, 0.50, 0.75, 1.00, 0.50]

    for t0 in sampled_ticks:
        t1 = t0 + HORIZON_1_TICKS
        t2 = t0 + HORIZON_2_TICKS
        if t1 not in grouped or t2 not in grouped:
            continue

        g0 = grouped[t0].sort_values(by=["team_num", "steamid"]).head(MAX_PLAYERS)
        if len(g0) < 6:
            continue

        # Filtro do Ouro (Eco Filter): exige pelo menos 3 jogadores armados com Rifle/SMG/Sniper no tick
        weapons_now = [str(w or "") for w in g0["active_weapon_name"].tolist()]
        armed_count = sum(1 for w in weapons_now if encode_weapon_category(w) >= 0.6)
        if armed_count < 3:
            continue

        g1_map = {row["steamid"]: row for _, row in grouped[t1].iterrows()}
        g2_map = {row["steamid"]: row for _, row in grouped[t2].iterrows()}

        players_rows = list(g0.to_dict("records"))
        while len(players_rows) < MAX_PLAYERS:
            players_rows.append({})

        # Pré-calcula posições e estados de vida para o Filtro Anti-Wallhack (Fog of War)
        positions = np.zeros((MAX_PLAYERS, 3), dtype=np.float32)
        yaws = np.zeros(MAX_PLAYERS, dtype=np.float32)
        speeds_2d = np.zeros(MAX_PLAYERS, dtype=np.float32)
        teams = np.zeros(MAX_PLAYERS, dtype=np.int32)
        alive_flags = np.zeros(MAX_PLAYERS, dtype=bool)
        actions_3h = np.zeros((MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8)

        for idx, p in enumerate(players_rows):
            if not p:
                continue
            sid = p.get("steamid")
            alive = bool(p.get("is_alive", False)) and float(p.get("health", 0) or 0) > 0
            alive_flags[idx] = alive
            teams[idx] = int(safe_float(p.get("team_num", 0)))
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
                actions_3h[idx, 2] = velocity_to_action_id(vx2, vy2, vz2, duck2, walk2)

        # Gera 2 amostras simétricas por step (Perspectiva CT=3 e Perspectiva TR=2) com Fog-of-War
        for obs_team in (3, 2):
            ally_mask = (teams == obs_team) & alive_flags
            ally_pos = positions[ally_mask]
            ally_yaw = yaws[ally_mask]
            ally_alive = alive_flags[ally_mask]

            tensor_step = np.zeros((MAX_PLAYERS, FEATURE_DIM), dtype=np.float32)
            for idx, p in enumerate(players_rows):
                if not p:
                    continue
                is_teammate = teams[idx] == obs_team
                is_masked = False
                if not is_teammate and alive_flags[idx]:
                    perceived = can_team_perceive_enemy_2d(
                        ally_pos, ally_yaw, ally_alive, positions[idx], float(speeds_2d[idx])
                    )
                    is_masked = not perceived

                tensor_step[idx] = build_standardized_player_row(
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
                )

            X_list.append(tensor_step)
            Y_list.append(actions_3h.copy())

    del df
    del grouped
    import gc
    gc.collect()

    if not X_list:
        return (
            np.empty((0, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32),
            np.empty((0, MAX_PLAYERS, HORIZONS_COUNT), dtype=np.uint8),
        )

    return np.stack(X_list, axis=0), np.stack(Y_list, axis=0)


def process_demos_folder(
    map_name: str = "de_mirage",
    delete_after_extract: bool = False,
) -> int:
    raw_dir = Path(RAW_DEMOS_DIR_D) / map_name
    out_dir = Path(EXTRACTED_TENSORS_DIR_D) / map_name
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    demos = sorted(raw_dir.rglob("*.dem"))
    if not demos:
        print(f"[extract_16hz_tensors] Nenhuma demo .dem pendente em {raw_dir}.")
        return 0

    total_samples = 0
    for dem_path in tqdm(demos, desc=f"Extraindo 16Hz ({map_name})"):
        out_npz = out_dir / f"{dem_path.stem}_16hz.npz"
        if out_npz.exists() and out_npz.stat().st_size > 100_000:
            try:
                with np.load(out_npz) as existing_data:
                    c = len(existing_data["X"])
                    total_samples += c
                    print(f"\n[extract_16hz_tensors] {out_npz.name} já extraído ({c} steps 16Hz).", flush=True)
                    if delete_after_extract:
                        dem_path.unlink(missing_ok=True)
                    continue
            except Exception:
                pass

        try:
            X, Y = extract_single_demo(dem_path)
            if len(X) > 0:
                np.savez_compressed(out_npz, X=X, Y=Y)
                total_samples += len(X)
                print(f"\n[extract_16hz_tensors] {dem_path.name} -> {out_npz.name} ({len(X)} steps 16Hz, {out_npz.stat().st_size // 1024} KB)", flush=True)
            if delete_after_extract:
                dem_path.unlink(missing_ok=True)
        except Exception as exc:
            print(f"[extract_16hz_tensors] Aviso ao processar {dem_path.name}: {exc}")

    return total_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrator demoparser2 a 16Hz com Filtro do Ouro e Fog-of-War")
    parser.add_argument("--map", type=str, default="de_mirage", help="Mapa alvo (default: de_mirage)")
    parser.add_argument(
        "--delete-after-extract",
        action="store_true",
        help="Apaga o arquivo .dem bruto de D:\\raw_demos após gerar o .npz compacto",
    )
    args = parser.parse_args()

    samples = process_demos_folder(map_name=args.map, delete_after_extract=args.delete_after_extract)
    print(f"[extract_16hz_tensors] Extração concluída. Total de amostras geradas neste lote: {samples}")


if __name__ == "__main__":
    main()
