"""
Fase 1: Inventário, Auditoria Espacial e Catalogação das 444 Demos Profissionais de Mirage.

Objetivos:
1. Auditar os 444 arquivos .npz (16Hz) e as 8 demos .dem brutas em F:\\CS2_MLMove_Pipeline:
   - Verificar integridade, duplicatas, contagem de ticks, horas de jogo e rounds estimados.
2. Auditar o comportamento de Pulo (Jump), Queda (Drop) e Bunny Hop nos 444 jogos:
   - Quantificar quantos frames atualmente têm bit de Jump ativo no Y vs. quantos são impulsos reais de salto,
     quantos são frames planando no ar/caindo (vz < 0) e quantos são episódios de Bunny Hop.
3. Extrair da telemetria oficial da Valve (last_place_name nas 8 .dem + clusters de parada nos 444 .npz)
   as coordenadas exatas dos Spots de Mirage e auditar cada spot do nosso `de_mirage.json`.
4. Calcular o `PositionGeneralityScore` (% das 444 partidas profissionais que ocupam cada posição/setor)
   para separar Fundamentos Universais de jogadas raras.
"""

from __future__ import annotations
import glob
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from demoparser2 import DemoParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PIPELINE_DIR = Path(r"F:\CS2_MLMove_Pipeline")
NPZ_DIR = PIPELINE_DIR / "extracted_tensors" / "de_mirage"
RAW_DEM_DIR = PIPELINE_DIR / "raw_demos" / "de_mirage"
MIRAGE_JSON_PATH = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\src\CsBotManager\MapProfiles\de_mirage.json")
REPORT_JSON_OUT = PIPELINE_DIR / "catalog_mirage_report.json"


def audit_raw_demos_places(dem_files: List[Path]) -> Dict[str, Any]:
    """
    Usa demoparser2 nas demos brutas (.dem) para extrair os limites exatos e os hotspots
    de parada (velocidade < 25 u/s) em cada `last_place_name` oficial do NavMesh da Valve na Mirage.
    """
    place_coords_ct: Dict[str, List[Tuple[float, float, float, float]]] = {}
    place_coords_tr: Dict[str, List[Tuple[float, float, float, float]]] = {}
    place_all_coords: Dict[str, List[Tuple[float, float, float]]] = {}

    for dem_path in dem_files:
        try:
            parser = DemoParser(str(dem_path))
            df = parser.parse_ticks([
                "X", "Y", "Z", "velocity_X", "velocity_Y", "velocity_Z",
                "yaw", "last_place_name", "team_num", "is_alive",
                "is_freeze_period", "is_warmup_period"
            ])
            if df is None or len(df) == 0:
                continue
            if "is_warmup_period" in df.columns:
                df = df[df["is_warmup_period"] == False]  # noqa: E712
            if "is_freeze_period" in df.columns:
                df = df[df["is_freeze_period"] == False]  # noqa: E712
            df = df[df["is_alive"] == True]  # noqa: E712
            df = df[df["team_num"].isin([2, 3])]

            # Amostra a cada 8 ticks para velocidade
            df_sub = df.iloc[::8]
            speeds = np.hypot(df_sub["velocity_X"].fillna(0), df_sub["velocity_Y"].fillna(0))
            df_sub = df_sub.assign(speed2d=speeds)

            for place, grp in df_sub.groupby("last_place_name"):
                if not place or len(grp) < 10:
                    continue
                pts = list(zip(grp["X"].tolist(), grp["Y"].tolist(), grp["Z"].tolist()))
                place_all_coords.setdefault(place, []).extend(pts)

                # Jogadores segurando posição / parados (speed2d < 30 u/s)
                hold_grp = grp[grp["speed2d"] < 30.0]
                ct_hold = hold_grp[hold_grp["team_num"] == 3]
                tr_hold = hold_grp[hold_grp["team_num"] == 2]

                if len(ct_hold) > 0:
                    place_coords_ct.setdefault(place, []).extend(
                        zip(ct_hold["X"].tolist(), ct_hold["Y"].tolist(), ct_hold["Z"].tolist(), ct_hold["yaw"].tolist())
                    )
                if len(tr_hold) > 0:
                    place_coords_tr.setdefault(place, []).extend(
                        zip(tr_hold["X"].tolist(), tr_hold["Y"].tolist(), tr_hold["Z"].tolist(), tr_hold["yaw"].tolist())
                    )
        except Exception as exc:
            print(f"[Aviso] Falha ao ler demo bruta {dem_path.name}: {exc}")

    summary: Dict[str, Any] = {}
    for place, pts in sorted(place_all_coords.items()):
        arr = np.array(pts, dtype=np.float32)
        ct_arr = np.array(place_coords_ct.get(place, []), dtype=np.float32)
        tr_arr = np.array(place_coords_tr.get(place, []), dtype=np.float32)
        summary[place] = {
            "total_samples": int(len(arr)),
            "median_xyz": [round(float(np.median(arr[:, 0])), 1), round(float(np.median(arr[:, 1])), 1), round(float(np.median(arr[:, 2])), 1)],
            "bbox_min_xyz": [round(float(np.percentile(arr[:, 0], 5)), 1), round(float(np.percentile(arr[:, 1], 5)), 1), round(float(np.percentile(arr[:, 2], 5)), 1)],
            "bbox_max_xyz": [round(float(np.percentile(arr[:, 0], 95)), 1), round(float(np.percentile(arr[:, 1], 95)), 1), round(float(np.percentile(arr[:, 2], 95)), 1)],
            "ct_hold_samples": int(len(ct_arr)),
            "ct_hold_median_xyz": [
                round(float(np.median(ct_arr[:, 0])), 1),
                round(float(np.median(ct_arr[:, 1])), 1),
                round(float(np.median(ct_arr[:, 2])), 1),
            ] if len(ct_arr) > 0 else None,
            "tr_hold_samples": int(len(tr_arr)),
            "tr_hold_median_xyz": [
                round(float(np.median(tr_arr[:, 0])), 1),
                round(float(np.median(tr_arr[:, 1])), 1),
                round(float(np.median(tr_arr[:, 2])), 1),
            ] if len(tr_arr) > 0 else None,
        }
    return summary


# Regiões canônicas reais de Mirage no Source 2 (derivadas do NavMesh / last_place_name da Valve)
REAL_MIRAGE_ZONES: Dict[str, Dict[str, Any]] = {
    # Bombsite A (CT & TR)
    "A_Ticket":        {"x": -960.0,  "y": -2240.0, "z": -168.0, "r": 240.0, "sector": "Bombsite A", "place": "BombsiteA"},
    "A_Firebox":       {"x": -220.0,  "y": -2230.0, "z": -168.0, "r": 180.0, "sector": "Bombsite A", "place": "BombsiteA"},
    "A_Ninja":         {"x": -340.0,  "y": -2080.0, "z": -168.0, "r": 160.0, "sector": "Bombsite A", "place": "BombsiteA"},
    "A_Triple_Default":{"x": -440.0,  "y": -1970.0, "z": -168.0, "r": 220.0, "sector": "Bombsite A", "place": "BombsiteA"},
    "A_Stairs":        {"x": -500.0,  "y": -1465.0, "z": -55.0,  "r": 200.0, "sector": "Bombsite A", "place": "Stairs"},
    "A_Jungle":        {"x": -970.0,  "y": -1375.0, "z": -168.0, "r": 260.0, "sector": "Bombsite A", "place": "Jungle"},
    "A_UnderPalace":   {"x": -90.0,   "y": -1980.0, "z": -168.0, "r": 200.0, "sector": "Bombsite A", "place": "Scaffolding"},
    "A_Ramp":          {"x": 385.0,   "y": -1660.0, "z": -205.0, "r": 260.0, "sector": "Bombsite A", "place": "TRamp"},
    "A_PalaceInterior":{"x": 420.0,   "y": -1970.0, "z": -40.0,  "r": 320.0, "sector": "Bombsite A", "place": "PalaceInterior"},
    # Meio (Mid)
    "Mid_Window":      {"x": -1185.0, "y": -660.0,  "z": -168.0, "r": 220.0, "sector": "Mid",        "place": "SnipersNest"},
    "Mid_Connector":   {"x": -695.0,  "y": -1120.0, "z": -168.0, "r": 240.0, "sector": "Mid",        "place": "Connector"},
    "Mid_Catwalk":     {"x": -795.0,  "y": -140.0,  "z": -167.0, "r": 260.0, "sector": "Mid",        "place": "Catwalk"},
    "Mid_TopMid":      {"x": 265.0,   "y": -255.0,  "z": -164.0, "r": 300.0, "sector": "Mid",        "place": "TopofMid"},
    "Mid_Middle":      {"x": -630.0,  "y": -720.0,  "z": -260.0, "r": 280.0, "sector": "Mid",        "place": "Middle"},
    "Mid_Underpass":   {"x": -965.0,  "y": 210.0,   "z": -354.0, "r": 260.0, "sector": "Mid",        "place": "Underpass"},
    # Bombsite B (CT & TR)
    "B_Van_Truck":     {"x": -2175.0, "y": 735.0,   "z": -123.0, "r": 200.0, "sector": "Bombsite B", "place": "Truck"},
    "B_Bench":         {"x": -2310.0, "y": 260.0,   "z": -168.0, "r": 200.0, "sector": "Bombsite B", "place": "BombsiteB"},
    "B_Default_Site":  {"x": -1980.0, "y": 340.0,   "z": -166.0, "r": 240.0, "sector": "Bombsite B", "place": "BombsiteB"},
    "B_Market_Shop":   {"x": -1890.0, "y": -530.0,  "z": -168.0, "r": 280.0, "sector": "Bombsite B", "place": "Shop"},
    "B_Short_Corner":  {"x": -1420.0, "y": 140.0,   "z": -168.0, "r": 240.0, "sector": "Bombsite B", "place": "BombsiteB"},
    "B_Apartments":    {"x": -1520.0, "y": 738.0,   "z": -48.0,  "r": 340.0, "sector": "Bombsite B", "place": "Apartments"},
    "B_BackAlley":     {"x": -450.0,  "y": 565.0,   "z": -80.0,  "r": 280.0, "sector": "Bombsite B", "place": "BackAlley"},
    # Spawns
    "CT_Spawn":        {"x": -1656.0, "y": -1896.0, "z": -264.0, "r": 350.0, "sector": "CT Spawn",   "place": "CTSpawn"},
    "TR_Spawn":        {"x": 1216.0,  "y": -160.0,  "z": -165.0, "r": 350.0, "sector": "TR Spawn",   "place": "TSpawn"},
}


def audit_444_npz_dataset(npz_files: List[Path], mirage_json_spots: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_valid_files = 0
    corrupted_files = 0
    duplicate_files = 0
    seen_hashes = set()

    total_ticks_16hz = 0
    total_rounds_estimated = 0

    # Estatísticas de Movimento e Salto
    total_player_frames = 0
    old_jump_labeled_frames = 0
    true_jump_onset_frames = 0
    false_jump_falling_frames = 0
    false_jump_airborne_hold_frames = 0
    bunny_hop_frames = 0

    stand_still_frames = 0
    run_frames = 0
    walk_shift_frames = 0
    crouch_frames = 0

    # Cobertura por Zona Canônica Real de Mirage (quantas demos usam cada zona e quantos frames de Hold)
    zone_demo_presence_ct: Dict[str, int] = {k: 0 for k in REAL_MIRAGE_ZONES}
    zone_demo_presence_tr: Dict[str, int] = {k: 0 for k in REAL_MIRAGE_ZONES}
    zone_hold_frames_ct: Dict[str, int] = {k: 0 for k in REAL_MIRAGE_ZONES}
    zone_hold_frames_tr: Dict[str, int] = {k: 0 for k in REAL_MIRAGE_ZONES}
    zone_coord_accum_ct: Dict[str, List[ np.ndarray ]] = {k: [] for k in REAL_MIRAGE_ZONES}
    zone_coord_accum_tr: Dict[str, List[ np.ndarray ]] = {k: [] for k in REAL_MIRAGE_ZONES}

    # Pré-prepara matriz das zonas reais [Z, 3] e raios [Z]
    zone_names = list(REAL_MIRAGE_ZONES.keys())
    zone_centers = np.array([[REAL_MIRAGE_ZONES[k]["x"], REAL_MIRAGE_ZONES[k]["y"], REAL_MIRAGE_ZONES[k]["z"]] for k in zone_names], dtype=np.float32)
    zone_radii = np.array([REAL_MIRAGE_ZONES[k]["r"] for k in zone_names], dtype=np.float32)

    # Pré-prepara matriz dos spots atuais do de_mirage.json
    json_spot_ids = [s["id"] for s in mirage_json_spots]
    json_spot_centers = np.array([[float(s["x"]), float(s["y"]), float(s["z"])] for s in mirage_json_spots], dtype=np.float32)
    json_spot_demo_hits: Dict[str, int] = {sid: 0 for sid in json_spot_ids}
    json_spot_frame_hits: Dict[str, int] = {sid: 0 for sid in json_spot_ids}

    # Distribuição de formações CT no início dos rounds (ex: 2-1-2, 3-1-1, 1-3-1, etc.)
    formation_counts: Dict[str, int] = {}

    t_start = time.time()
    for idx, npz_path in enumerate(npz_files, 1):
        try:
            # Verifica hash rápido dos primeiros 64KB + tamanho para detectar duplicatas exatas
            fsize = npz_path.stat().st_size
            with open(npz_path, "rb") as f:
                h = hashlib.md5(f.read(65536) + str(fsize).encode()).hexdigest()
            if h in seen_hashes:
                duplicate_files += 1
                continue
            seen_hashes.add(h)

            with np.load(npz_path) as data:
                X = data["X"]  # [N, 10, 18]
                Y = data["Y"]  # [N, 10, 3]
        except Exception:
            corrupted_files += 1
            continue

        if len(X) < 20:
            corrupted_files += 1
            continue

        total_valid_files += 1

        # Como extract_16hz_tensors gerou 2 amostras por step (índice par = CT obs, índice ímpar = TR obs),
        # pegamos os passos pares para ler os 5 CTs sem máscara e os ímpares para ler os 5 TRs sem máscara!
        X_ct_obs = X[0::2]  # [T, 10, 18]
        Y_steps = Y[0::2]   # [T, 10, 3] (Y é idêntico para par e ímpar)
        X_tr_obs = X[1::2]  # [T, 10, 18]

        T = min(len(X_ct_obs), len(X_tr_obs))
        total_ticks_16hz += T

        # Reconstrói estado completo sem máscara combinando os CTs de X_ct_obs e os TRs de X_tr_obs
        # CTs têm feature[13] == 0.0; TRs têm feature[13] == 1.0
        # Em extract_16hz_tensors, g0 foi ordenado por ["team_num", "steamid"], então 0..4 são TR (team 2) e 5..9 são CT (team 3)
        full_X = np.where(X_ct_obs[:T, :, 13:14] < 0.5, X_ct_obs[:T], X_tr_obs[:T])

        # Detecta fronteiras de round quando o número de jogadores vivos sobe abruptamente (ex: de <= 6 para >= 9)
        # ou quando a distância média dos jogadores salta > 800 unidades em 1 step
        alive_mask = full_X[:, :, 14] > 0.5  # [T, 10]
        alive_counts = alive_mask.sum(axis=1)
        pos_x = full_X[:, :, 0] * 4096.0
        pos_y = full_X[:, :, 1] * 4096.0
        pos_z = full_X[:, :, 2] * 1024.0
        vx = full_X[:, :, 3] * 250.0
        vy = full_X[:, :, 4] * 250.0
        vz = full_X[:, :, 5] * 250.0

        # Diferença de posição entre t e t-1 para detectar teleporte de novo round
        dx_step = np.abs(np.diff(pos_x, axis=0)).max(axis=1)
        dy_step = np.abs(np.diff(pos_y, axis=0)).max(axis=1)
        round_Reset_indices = np.where((dx_step > 900.0) | (dy_step > 900.0))[0] + 1
        # Filtra resets muito próximos (< 48 steps = 3s)
        clean_resets = [0]
        for r_idx in round_Reset_indices:
            if r_idx - clean_resets[-1] >= 48:
                clean_resets.append(int(r_idx))
        total_rounds_estimated += len(clean_resets)

        # Avalia formação CT ~12 segundos (192 steps a 16Hz) após o início de cada round
        for r_start in clean_resets:
            check_t = r_start + 160  # ~10s após freeze end
            if check_t < T:
                ct_slots = (full_X[check_t, :, 13] < 0.5) & (full_X[check_t, :, 14] > 0.5)
                if ct_slots.sum() == 5:
                    cx = pos_x[check_t, ct_slots]
                    cy = pos_y[check_t, ct_slots]
                    # Classifica cada CT em A, Mid ou B pelas coordenadas reais de Mirage:
                    # Bombsite A / Jungle / Stairs / Ticket: Y < -1200
                    # Bombsite B / Truck / Bench / Shop / Catwalk B: X < -1350 e Y > -650
                    # Mid (Window, Connector, Middle, Catwalk Mid): demais
                    a_cnt = int(np.sum(cy < -1200.0))
                    b_cnt = int(np.sum((cx < -1300.0) & (cy >= -700.0)))
                    mid_cnt = 5 - a_cnt - b_cnt
                    form_key = f"{a_cnt}A-{mid_cnt}Mid-{b_cnt}B"
                    formation_counts[form_key] = formation_counts.get(form_key, 0) + 1

        # Auditoria de Pulo, Queda e BunnyHop em Y_steps[:, :, 0] (horizonte t0)
        act_t0 = Y_steps[:T, :, 0]  # [T, 10]
        alive_b = alive_mask[:T]
        total_player_frames += int(alive_b.sum())

        # ActionId: 0 = StandStill; 1..48 = Ground; 49..96 = Jump
        is_old_jump = (act_t0 >= 49) & alive_b
        old_jump_labeled_frames += int(is_old_jump.sum())

        is_stand = (act_t0 == 0) & alive_b
        stand_still_frames += int(is_stand.sum())

        # Decodifica speed_tier para frames vivos > 0
        rem = (np.maximum(act_t0, 1) - 1) % 48
        speed_idx = rem // 16
        run_frames += int(((act_t0 > 0) & (speed_idx == 0) & alive_b).sum())
        walk_shift_frames += int(((act_t0 > 0) & (speed_idx == 1) & alive_b).sum())
        crouch_frames += int(((act_t0 > 0) & (speed_idx == 2) & alive_b).sum())

        # Separa os frames rotulados como Jump em:
        # 1) Queda / descida (vz < -10 u/s) -> Falso Pulo (Drop/Falling)
        # 2) Impulso legítimo de subida (vz > 140 u/s no frame t e no frame t-1 não estava subindo)
        # 3) Planando no ar após o impulso inicial
        falling_jump = is_old_jump & (vz < -10.0)
        false_jump_falling_frames += int(falling_jump.sum())

        rising = is_old_jump & (vz >= 140.0)
        prev_not_jumping = np.zeros_like(is_old_jump)
        prev_not_jumping[0] = True
        prev_not_jumping[1:] = ~is_old_jump[:-1] | (vz[:-1] < 50.0)

        jump_onset = rising & prev_not_jumping
        true_jump_onset_frames += int(jump_onset.sum())

        airborne_hold = is_old_jump & (~falling_jump) & (~jump_onset)
        false_jump_airborne_hold_frames += int(airborne_hold.sum())

        # Detecta Bunny Hop: 2 ou mais jump_onsets do mesmo jogador dentro de 20 steps (1.25s)
        for p_slot in range(10):
            onsets = np.where(jump_onset[:, p_slot])[0]
            if len(onsets) > 1:
                diffs = np.diff(onsets)
                bhop_hits = np.sum(diffs <= 20)
                bunny_hop_frames += int(bhop_hits)

        # Amostragem espacial a 2Hz (a cada 8 steps de 16Hz = 0.5s) para cobertura de Spots e Zonas
        sub_slice = slice(0, T, 8)
        px_sub = pos_x[sub_slice]       # [Ts, 10]
        py_sub = pos_y[sub_slice]
        pz_sub = pos_z[sub_slice]
        spd_sub = np.hypot(vx[sub_slice], vy[sub_slice])
        alive_sub = alive_b[sub_slice]
        is_tr_sub = full_X[sub_slice, :, 13] > 0.5

        pts_3d = np.stack([px_sub, py_sub, pz_sub], axis=-1)  # [Ts, 10, 3]

        # 1) Distância 2D para as 24 Zonas Canônicas Reais de Mirage
        # pts_3d: [Ts, 10, 1, 3], zone_centers: [1, 1, Z, 3]
        d_xy = np.hypot(
            pts_3d[:, :, None, 0] - zone_centers[None, None, :, 0],
            pts_3d[:, :, None, 1] - zone_centers[None, None, :, 1],
        )  # [Ts, 10, Z]
        d_z = np.abs(pts_3d[:, :, None, 2] - zone_centers[None, None, :, 2])
        in_zone = (d_xy <= zone_radii[None, None, :]) & (d_z <= 120.0) & alive_sub[:, :, None]

        is_holding = spd_sub < 35.0  # Jogador segurando ângulo / parado no spot
        ct_hold_zone = in_zone & (~is_tr_sub[:, :, None]) & is_holding[:, :, None]
        tr_hold_zone = in_zone & (is_tr_sub[:, :, None]) & is_holding[:, :, None]

        for z_idx, z_name in enumerate(zone_names):
            ct_cnt = int(ct_hold_zone[:, :, z_idx].sum())
            tr_cnt = int(tr_hold_zone[:, :, z_idx].sum())
            if ct_cnt > 0:
                zone_demo_presence_ct[z_name] += 1
                zone_hold_frames_ct[z_name] += ct_cnt
                if len(zone_coord_accum_ct[z_name]) < 2000:
                    matched_pts = pts_3d[ct_hold_zone[:, :, z_idx]]
                    zone_coord_accum_ct[z_name].append(matched_pts[:20])
            if tr_cnt > 0:
                zone_demo_presence_tr[z_name] += 1
                zone_hold_frames_tr[z_name] += tr_cnt
                if len(zone_coord_accum_tr[z_name]) < 2000:
                    matched_pts = pts_3d[tr_hold_zone[:, :, z_idx]]
                    zone_coord_accum_tr[z_name].append(matched_pts[:20])

        # 2) Distância 2D para os Spots atuais do `de_mirage.json` (raio de 220u e |dz| <= 120u)
        d_spot_xy = np.hypot(
            pts_3d[:, :, None, 0] - json_spot_centers[None, None, :, 0],
            pts_3d[:, :, None, 1] - json_spot_centers[None, None, :, 1],
        )
        d_spot_z = np.abs(pts_3d[:, :, None, 2] - json_spot_centers[None, None, :, 2])
        in_spot = (d_spot_xy <= 220.0) & (d_spot_z <= 120.0) & alive_sub[:, :, None]
        for s_idx, sid in enumerate(json_spot_ids):
            scnt = int(in_spot[:, :, s_idx].sum())
            if scnt > 0:
                json_spot_demo_hits[sid] += 1
                json_spot_frame_hits[sid] += scnt

        if idx % 100 == 0 or idx == len(npz_files):
            elapsed = time.time() - t_start
            print(f"[Auditoria NPZ] Processados {idx}/{len(npz_files)} arquivos ({elapsed:.1f}s)...", flush=True)

    # Consolida estatísticas de cada Zona Canônica Real e PositionGeneralityScore
    zones_report: Dict[str, Any] = {}
    for z_name, z_meta in REAL_MIRAGE_ZONES.items():
        ct_pres = zone_demo_presence_ct[z_name]
        tr_pres = zone_demo_presence_tr[z_name]
        ct_pct = round(100.0 * ct_pres / max(1, total_valid_files), 1)
        tr_pct = round(100.0 * tr_pres / max(1, total_valid_files), 1)

        ct_med = None
        if zone_coord_accum_ct[z_name]:
            cat = np.concatenate(zone_coord_accum_ct[z_name], axis=0)
            ct_med = [round(float(np.median(cat[:, 0])), 1), round(float(np.median(cat[:, 1])), 1), round(float(np.median(cat[:, 2])), 1)]

        tr_med = None
        if zone_coord_accum_tr[z_name]:
            cat = np.concatenate(zone_coord_accum_tr[z_name], axis=0)
            tr_med = [round(float(np.median(cat[:, 0])), 1), round(float(np.median(cat[:, 1])), 1), round(float(np.median(cat[:, 2])), 1)]

        generality_score = round(max(ct_pct, tr_pct) / 100.0, 3)
        tier = "STANDARD_FUNDAMENTAL" if generality_score >= 0.65 else ("CONTEXTUAL_VARIATION" if generality_score >= 0.25 else "RARE_SPECIALIZED")

        zones_report[z_name] = {
            "sector": z_meta["sector"],
            "valve_place": z_meta["place"],
            "reference_xyz": [z_meta["x"], z_meta["y"], z_meta["z"]],
            "ct_demos_count": ct_pres,
            "ct_demos_pct": ct_pct,
            "ct_hold_samples_2hz": zone_hold_frames_ct[z_name],
            "ct_pro_median_xyz": ct_med,
            "tr_demos_count": tr_pres,
            "tr_demos_pct": tr_pct,
            "tr_hold_samples_2hz": zone_hold_frames_tr[z_name],
            "tr_pro_median_xyz": tr_med,
            "position_generality_score": generality_score,
            "behavior_category": tier,
        }

    # Audita os spots atuais do de_mirage.json
    json_spots_audit: List[Dict[str, Any]] = []
    for s in mirage_json_spots:
        sid = s["id"]
        sx, sy, sz = float(s["x"]), float(s["y"]), float(s["z"])
        hits = json_spot_demo_hits[sid]
        pct = round(100.0 * hits / max(1, total_valid_files), 1)
        json_spots_audit.append({
            "id": sid,
            "name": s.get("name", ""),
            "side": s.get("side", ""),
            "sector": s.get("sector", ""),
            "current_xyz": [sx, sy, sz],
            "demos_with_activity_pct": pct,
            "samples_2hz": json_spot_frame_hits[sid],
        })

    total_hours = round((total_ticks_16hz / 16.0) / 3600.0, 2)
    return {
        "dataset_summary": {
            "total_npz_files_scanned": len(npz_files),
            "valid_unique_demos": total_valid_files,
            "duplicate_demos": duplicate_files,
            "corrupted_demos": corrupted_files,
            "total_steps_16hz": total_ticks_16hz,
            "total_combat_hours": total_hours,
            "estimated_valid_rounds": total_rounds_estimated,
        },
        "movement_and_jump_audit": {
            "total_alive_player_frames": total_player_frames,
            "stand_still_pct": round(100.0 * stand_still_frames / max(1, total_player_frames), 2),
            "run_pct": round(100.0 * run_frames / max(1, total_player_frames), 2),
            "walk_shift_pct": round(100.0 * walk_shift_frames / max(1, total_player_frames), 2),
            "crouch_pct": round(100.0 * crouch_frames / max(1, total_player_frames), 2),
            "old_jump_labeled_frames": old_jump_labeled_frames,
            "old_jump_pct_of_all_frames": round(100.0 * old_jump_labeled_frames / max(1, total_player_frames), 2),
            "true_jump_onset_frames": true_jump_onset_frames,
            "true_jump_onset_pct_of_all_frames": round(100.0 * true_jump_onset_frames / max(1, total_player_frames), 3),
            "false_jump_falling_frames": false_jump_falling_frames,
            "false_jump_airborne_hold_frames": false_jump_airborne_hold_frames,
            "jump_noise_inflation_factor": round(old_jump_labeled_frames / max(1, true_jump_onset_frames), 2),
            "bunny_hop_episodes_detected": bunny_hop_frames,
        },
        "ct_formations_top10": dict(sorted(formation_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        "canonical_mirage_zones": zones_report,
        "current_de_mirage_json_audit": json_spots_audit,
    }


def main() -> None:
    print("================================================================================")
    print(" FASE 1: INVENTÁRIO E AUDITORIA PROFUNDA DAS DEMOS DE MIRAGE (CS2)")
    print("================================================================================")

    with open(MIRAGE_JSON_PATH, "r", encoding="utf-8") as f:
        mirage_profile = json.load(f)
    mirage_spots = mirage_profile.get("spots", [])
    print(f"[*] Perfil atual de_mirage.json carregado: {len(mirage_spots)} spots.")

    raw_dems = sorted(RAW_DEM_DIR.rglob("*.dem"))
    print(f"[*] Demos .dem brutas encontradas para extração de callouts oficiais (last_place_name): {len(raw_dems)}")
    valve_places = audit_raw_demos_places(raw_dems)

    npz_files = sorted(NPZ_DIR.glob("*_16hz.npz"))
    print(f"[*] Arquivos de tensores 16Hz (.npz) encontrados em {NPZ_DIR}: {len(npz_files)}")
    npz_audit = audit_444_npz_dataset(npz_files, mirage_spots)

    full_report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "map": "de_mirage",
        "valve_navmesh_places_reference": valve_places,
        **npz_audit,
    }

    with open(REPORT_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)

    print(f"\n[+] Relatório JSON gravado em: {REPORT_JSON_OUT}")
    ds = npz_audit["dataset_summary"]
    mj = npz_audit["movement_and_jump_audit"]
    print(f"  -> Demos únicas válidas: {ds['valid_unique_demos']} (Duplicadas: {ds['duplicate_demos']}, Corrompidas: {ds['corrupted_demos']})")
    print(f"  -> Rounds válidos estimados: {ds['estimated_valid_rounds']} ({ds['total_combat_hours']} horas de jogo útil a 16Hz)")
    print(f"  -> Frames rotulados como Jump no V1: {mj['old_jump_labeled_frames']} ({mj['old_jump_pct_of_all_frames']}%)")
    print(f"  -> Impulsos reais de Jump (Onset):   {mj['true_jump_onset_frames']} ({mj['true_jump_onset_pct_of_all_frames']}%)")
    print(f"  -> Fator de inflação de pulos no V1: {mj['jump_noise_inflation_factor']}x (Falsos pulos em queda: {mj['false_jump_falling_frames']}, No ar: {mj['false_jump_airborne_hold_frames']}, BunnyHops: {mj['bunny_hop_episodes_detected']})")


if __name__ == "__main__":
    main()
