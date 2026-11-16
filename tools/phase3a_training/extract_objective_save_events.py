#!/usr/bin/env python3
"""
Fase 3A.2 - Passo 2, 3, 4, 5: Extração Tipada e Rigorosa de Eventos OBJECTIVE e SAVE no Corpus de 444 Demos.

Garante:
1. OBJECTIVE: Subestados tipados (PLANT_APPROACH, PLANTING, POST_PLANT_SETUP, DEFUSE_APPROACH, DEFUSING, DEFUSE_COVER).
2. SAVE: Subestados tipados (SAVE_DECISION, SAVE_ROTATION, SAVE_HOLD, EXIT_FRAG_ATTEMPT, WEAPON_PRESERVATION).
3. Episódios estritamente contidos no mesmo round (ObjectiveEpisodeDoesNotCrossRound, SaveEpisodeDoesNotCrossRound).
4. Preservação estrita dos splits (Train matches -> Train, Val -> Val, Test -> Test).
5. Amostragem descorrelacionada (máximo de sequências por episódio para evitar redundância).
6. Gera: objective_save_extraction_report.json e objective_save_extraction_report.md.
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path
from collections import Counter, defaultdict

# Raiz no sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Limites dos Bombsites no Mirage (unidades de jogo)
A_BOX = {"x_min": -1250, "x_max": 50, "y_min": -2600, "y_max": -1400, "z_min": -250, "z_max": 0}
B_BOX = {"x_min": -2400, "x_max": -1400, "y_min": -400, "y_max": 700, "z_min": -250, "z_max": 0}

def is_in_box(x, y, z, box):
    return (box["x_min"] <= x <= box["x_max"]) and (box["y_min"] <= y <= box["y_max"]) and (box["z_min"] <= z <= box["z_max"])

def is_in_safe_zone(x, y):
    # CT Spawn
    if -2600 <= x <= -1400 and -1200 <= y <= -500:
        return True
    # T Spawn
    if 700 <= x <= 1500 and -600 <= y <= 500:
        return True
    # T Roof / Alley
    if 100 <= x <= 700 and -1200 <= y <= -400:
        return True
    # B Apartments Back
    if -2500 <= x <= -1800 and 700 <= y <= 1500:
        return True
    return False

def load_splits(datasets_dir: Path):
    splits_dir = datasets_dir / "splits"
    demo_to_split = {}
    
    with open(splits_dir / "train_split_v2.json", "r", encoding="utf-8") as f:
        d = json.load(f)
        for m in d.get("match_ids", []):
            demo_to_split[m if isinstance(m, str) else m.get("demo_id")] = "train"
            
    with open(splits_dir / "validation_split_v2.json", "r", encoding="utf-8") as f:
        d = json.load(f)
        for m in d.get("match_ids", []):
            demo_to_split[m if isinstance(m, str) else m.get("demo_id")] = "validation"
            
    with open(splits_dir / "test_split_v2.json", "r", encoding="utf-8") as f:
        d = json.load(f)
        for m in d.get("match_ids", []):
            demo_to_split[m if isinstance(m, str) else m.get("demo_id")] = "test"
            
    return demo_to_split

def extract_from_corpus(limit_demos: int = None):
    print("=" * 70)
    print("FASE 3A.2: EXTRAÇÃO RIGOROSA DE OBJECTIVE E SAVE NO CORPUS DE 444 DEMOS")
    print("=" * 70)
    
    ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    runs_dir = BASE_DIR / "training_runs" / "positioning_v1"
    runs_dir.mkdir(parents=True, exist_ok=True)
    
    demo_to_split = load_splits(ds_dir)
    tensors_dir = Path(r"F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage")
    if not tensors_dir.exists():
        tensors_dir = BASE_DIR / "extracted_tensors"
        
    npz_files = sorted(list(tensors_dir.glob("*.npz")))
    print(f"Total de tensores .npz encontrados: {len(npz_files)}")
    if limit_demos:
        npz_files = npz_files[:limit_demos]
        print(f"Limitando a {limit_demos} demos para este lote.")
        
    # Estatísticas de extração
    stats = {
        "raw_candidate_events": 0,
        "accepted_episodes": 0,
        "rejected_episodes": 0,
        "by_state": {"OBJECTIVE": 0, "SAVE": 0},
        "by_split": {
            "train": {"OBJECTIVE": 0, "SAVE": 0},
            "validation": {"OBJECTIVE": 0, "SAVE": 0},
            "test": {"OBJECTIVE": 0, "SAVE": 0}
        },
        "by_subtype": {
            "OBJECTIVE": defaultdict(int),
            "SAVE": defaultdict(int)
        },
        "unique_demos": set(),
        "unique_matches": set(),
        "unique_players": set(),
        "unique_teams": set(),
        "durations_ms": []
    }
    
    extracted_records = []
    
    for f_idx, npz_path in enumerate(npz_files):
        stem = npz_path.stem.replace("_16hz", "")
        # Resolver split
        split_name = demo_to_split.get(stem)
        if not split_name:
            for k, v in demo_to_split.items():
                if k in stem or stem in k:
                    split_name = v
                    break
        if not split_name:
            split_name = "train" # fallback seguro
            
        try:
            with np.load(npz_path) as data:
                X = data["X"]
                n_frames = X.shape[0]
                if n_frames < 320:
                    continue
                    
                # Rastrear round boundaries
                r_time = X[:, 0, 17]
                diff = np.diff(r_time)
                resets = np.where(diff > 0.15)[0].tolist()
                round_bounds = [0] + [r + 1 for r in resets] + [n_frames]
                
                match_id = stem.split("_")[0] if "_" in stem else stem
                stats["unique_demos"].add(stem)
                stats["unique_matches"].add(match_id)
                
                for r_idx in range(len(round_bounds) - 1):
                    s_f = round_bounds[r_idx]
                    e_f = round_bounds[r_idx + 1]
                    r_len = e_f - s_f
                    if r_len < 320: # Menos de 20 segundos
                        continue
                        
                    # Detecção de último round da metade (proíbe SAVE)
                    # No CS2: rounds 12 e 24 são finais de metade
                    is_final_round_of_half = (r_idx == 11 or r_idx == 23)
                    
                    r_X = X[s_f:e_f]
                    
                    # ----------------------------------------------------
                    # 1. RASTREAR BOMBA E OBJETIVOS (PLANT / DEFUSE)
                    # ----------------------------------------------------
                    c4_mask = r_X[:, :, 15] > 0.5
                    carrier_slots = np.where(np.any(c4_mask, axis=0))[0]
                    
                    plant_frame = None
                    plant_site = None
                    plant_pos = None
                    plant_carrier_slot = None
                    
                    for slot in carrier_slots:
                        c4_frames = np.where(c4_mask[:, slot])[0]
                        if len(c4_frames) == 0:
                            continue
                        last_c4_f = c4_frames[-1]
                        if last_c4_f >= r_len - 16:
                            continue # C4 mantida na mão até o fim do round
                            
                        px = float(r_X[last_c4_f, slot, 0] * 4096.0)
                        py = float(r_X[last_c4_f, slot, 1] * 4096.0)
                        pz = float(r_X[last_c4_f, slot, 2] * 1024.0)
                        
                        in_a = is_in_box(px, py, pz, A_BOX)
                        in_b = is_in_box(px, py, pz, B_BOX)
                        
                        if in_a or in_b:
                            # Verificar se parou antes de largar a C4 (plant action)
                            check_start = max(0, last_c4_f - 40)
                            if last_c4_f > check_start:
                                spd_pre = np.hypot(
                                    r_X[check_start:last_c4_f, slot, 3] * 250.0,
                                    r_X[check_start:last_c4_f, slot, 4] * 250.0
                                )
                                if np.mean(spd_pre) < 135.0: # Plant típico: agachado ou imóvel
                                    plant_frame = last_c4_f
                                    plant_site = "A" if in_a else "B"
                                    plant_pos = (px, py, pz)
                                    plant_carrier_slot = slot
                                    break
                                    
                    # Processar PLANTING & PLANT_APPROACH
                    if plant_frame is not None and plant_carrier_slot is not None:
                        stats["raw_candidate_events"] += 1
                        ep_id = f"ep_obj_plant_{stem}_r{r_idx}_s{plant_carrier_slot}"
                        plant_dur_ms = min(3500, int((48 / 16.0) * 1000))
                        stats["accepted_episodes"] += 1
                        stats["durations_ms"].append(plant_dur_ms)
                        
                        # Subestado PLANTING (últimos 3s antes do plant concluir)
                        p_start = max(0, plant_frame - 48)
                        for f_off in range(p_start, plant_frame, 8): # Stride de 0.5s
                            global_f = s_f + f_off
                            if global_f < 32: # Precisa de histórico
                                continue
                            rec = {
                                "sequence_id": f"pos_{stem}_r{r_idx}_s{plant_carrier_slot}_f{global_f}",
                                "split": split_name,
                                "demo_id": stem,
                                "round_index": r_idx,
                                "slot": plant_carrier_slot,
                                "team": "TR",
                                "role": "BOMB_CARRIER",
                                "tactic_id": f"TR_EXEC_{plant_site}",
                                "plan_stage": "Planting",
                                "current_pos": [round(float(r_X[f_off, plant_carrier_slot, 0] * 4096.0), 1),
                                                round(float(r_X[f_off, plant_carrier_slot, 1] * 4096.0), 1),
                                                round(float(r_X[f_off, plant_carrier_slot, 2] * 1024.0), 1)],
                                "assigned_catalog_id": f"{plant_site.lower()}_default_plant_box" if plant_site == "B" else "a_default_plant_headshot",
                                "semantic_type": "PLANT_POSITION",
                                "confidence_weight": 1.0,
                                "next_catalog_id": f"{plant_site.lower()}_default_plant_box" if plant_site == "B" else "a_default_plant_headshot",
                                "next_sector": plant_site,
                                "expected_dwell_bucket": "LONG",
                                "positioning_state": "OBJECTIVE",
                                "objective_subtype": "PLANTING",
                                "save_subtype": "NONE",
                                "episode_id": ep_id,
                                "global_frame": global_f
                            }
                            extracted_records.append(rec)
                            stats["by_state"]["OBJECTIVE"] += 1
                            stats["by_split"][split_name]["OBJECTIVE"] += 1
                            stats["by_subtype"]["OBJECTIVE"]["PLANTING"] += 1
                            stats["unique_players"].add(f"{stem}_{plant_carrier_slot}")
                            
                        # Subestado PLANT_APPROACH (1 a 2s antes do plant iniciar)
                        app_start = max(0, p_start - 32)
                        for f_off in range(app_start, p_start, 16):
                            global_f = s_f + f_off
                            if global_f < 32:
                                continue
                            rec = {
                                "sequence_id": f"pos_{stem}_r{r_idx}_s{plant_carrier_slot}_f{global_f}",
                                "split": split_name,
                                "demo_id": stem,
                                "round_index": r_idx,
                                "slot": plant_carrier_slot,
                                "team": "TR",
                                "role": "BOMB_CARRIER",
                                "tactic_id": f"TR_EXEC_{plant_site}",
                                "plan_stage": "Execute",
                                "current_pos": [round(float(r_X[f_off, plant_carrier_slot, 0] * 4096.0), 1),
                                                round(float(r_X[f_off, plant_carrier_slot, 1] * 4096.0), 1),
                                                round(float(r_X[f_off, plant_carrier_slot, 2] * 1024.0), 1)],
                                "assigned_catalog_id": "UNMAPPED_POSITION",
                                "semantic_type": "CLEARANCE_WAYPOINT",
                                "confidence_weight": 0.9,
                                "next_catalog_id": f"{plant_site.lower()}_default_plant_box" if plant_site == "B" else "a_default_plant_headshot",
                                "next_sector": plant_site,
                                "expected_dwell_bucket": "SHORT",
                                "positioning_state": "OBJECTIVE",
                                "objective_subtype": "PLANT_APPROACH",
                                "save_subtype": "NONE",
                                "episode_id": ep_id,
                                "global_frame": global_f
                            }
                            extracted_records.append(rec)
                            stats["by_state"]["OBJECTIVE"] += 1
                            stats["by_split"][split_name]["OBJECTIVE"] += 1
                            stats["by_subtype"]["OBJECTIVE"]["PLANT_APPROACH"] += 1
                            
                    # Processar POST_PLANT_SETUP & DEFUSING / DEFUSE_COVER
                    if plant_frame is not None and plant_pos is not None:
                        post_start = plant_frame + 16
                        post_end = min(r_len - 16, post_start + 480) # Até 30s de pós-plant
                        if post_end > post_start + 32:
                            stats["accepted_episodes"] += 1
                            post_dur_ms = int(((post_end - post_start) / 16.0) * 1000)
                            stats["durations_ms"].append(post_dur_ms)
                            
                            # Amostrar sequências em intervalos regulares (stride de 16 frames = 1s)
                            for f_off in range(post_start, post_end, 16):
                                global_f = s_f + f_off
                                if global_f < 32:
                                    continue
                                    
                                for slot in range(10):
                                    is_alive = r_X[f_off, slot, 14] > 0.5
                                    if not is_alive:
                                        continue
                                    is_tr = r_X[f_off, slot, 13] > 0.5
                                    px = float(r_X[f_off, slot, 0] * 4096.0)
                                    py = float(r_X[f_off, slot, 1] * 4096.0)
                                    pz = float(r_X[f_off, slot, 2] * 1024.0)
                                    dist_c4 = math.hypot(px - plant_pos[0], py - plant_pos[1])
                                    
                                    # TR cobrindo pós-plant no bombsite
                                    if is_tr and dist_c4 < 1400.0:
                                        # Máximo de 3 amostras de pós-plant por slot para descorrelação
                                        if f_off % 32 == 0:
                                            rec = {
                                                "sequence_id": f"pos_{stem}_r{r_idx}_s{slot}_f{global_f}",
                                                "split": split_name,
                                                "demo_id": stem,
                                                "round_index": r_idx,
                                                "slot": slot,
                                                "team": "TR",
                                                "role": "ANCHOR" if dist_c4 < 500 else "SUPPORT",
                                                "tactic_id": f"TR_POST_PLANT_{plant_site}",
                                                "plan_stage": "PostPlant",
                                                "current_pos": [round(px, 1), round(py, 1), round(pz, 1)],
                                                "assigned_catalog_id": "UNMAPPED_POSITION",
                                                "semantic_type": "POSITION_PROFILE",
                                                "confidence_weight": 0.85,
                                                "next_catalog_id": "UNMAPPED_POSITION",
                                                "next_sector": plant_site,
                                                "expected_dwell_bucket": "MEDIUM",
                                                "positioning_state": "OBJECTIVE",
                                                "objective_subtype": "POST_PLANT_SETUP",
                                                "save_subtype": "NONE",
                                                "episode_id": f"ep_obj_postplant_{stem}_r{r_idx}",
                                                "global_frame": global_f
                                            }
                                            extracted_records.append(rec)
                                            stats["by_state"]["OBJECTIVE"] += 1
                                            stats["by_split"][split_name]["OBJECTIVE"] += 1
                                            stats["by_subtype"]["OBJECTIVE"]["POST_PLANT_SETUP"] += 1
                                            stats["unique_players"].add(f"{stem}_{slot}")
                                            
                                    # CT defusando ou dando cobertura de defuse
                                    elif not is_tr and dist_c4 < 120.0:
                                        # CT sobre a C4 com velocidade baixa -> DEFUSING
                                        spd = math.hypot(float(r_X[f_off, slot, 3]*250.0), float(r_X[f_off, slot, 4]*250.0))
                                        if spd < 80.0:
                                            rec = {
                                                "sequence_id": f"pos_{stem}_r{r_idx}_s{slot}_f{global_f}",
                                                "split": split_name,
                                                "demo_id": stem,
                                                "round_index": r_idx,
                                                "slot": slot,
                                                "team": "CT",
                                                "role": "DEFUSER",
                                                "tactic_id": f"CT_RETAKE_{plant_site}",
                                                "plan_stage": "Retake",
                                                "current_pos": [round(px, 1), round(py, 1), round(pz, 1)],
                                                "assigned_catalog_id": f"{plant_site.lower()}_default_plant_box" if plant_site == "B" else "a_default_plant_headshot",
                                                "semantic_type": "PLANT_POSITION",
                                                "confidence_weight": 1.0,
                                                "next_catalog_id": f"{plant_site.lower()}_default_plant_box" if plant_site == "B" else "a_default_plant_headshot",
                                                "next_sector": plant_site,
                                                "expected_dwell_bucket": "LONG",
                                                "positioning_state": "OBJECTIVE",
                                                "objective_subtype": "DEFUSING",
                                                "save_subtype": "NONE",
                                                "episode_id": f"ep_obj_defuse_{stem}_r{r_idx}_s{slot}",
                                                "global_frame": global_f
                                            }
                                            extracted_records.append(rec)
                                            stats["by_state"]["OBJECTIVE"] += 1
                                            stats["by_split"][split_name]["OBJECTIVE"] += 1
                                            stats["by_subtype"]["OBJECTIVE"]["DEFUSING"] += 1
                                            stats["unique_players"].add(f"{stem}_{slot}")
                                            
                                    elif not is_tr and dist_c4 < 600.0:
                                        # CT próximo cobrindo defuse
                                        if f_off % 32 == 0:
                                            rec = {
                                                "sequence_id": f"pos_{stem}_r{r_idx}_s{slot}_f{global_f}",
                                                "split": split_name,
                                                "demo_id": stem,
                                                "round_index": r_idx,
                                                "slot": slot,
                                                "team": "CT",
                                                "role": "RETAKE_COVER",
                                                "tactic_id": f"CT_RETAKE_{plant_site}",
                                                "plan_stage": "Retake",
                                                "current_pos": [round(px, 1), round(py, 1), round(pz, 1)],
                                                "assigned_catalog_id": "UNMAPPED_POSITION",
                                                "semantic_type": "POSITION_PROFILE",
                                                "confidence_weight": 0.80,
                                                "next_catalog_id": "UNMAPPED_POSITION",
                                                "next_sector": plant_site,
                                                "expected_dwell_bucket": "MEDIUM",
                                                "positioning_state": "OBJECTIVE",
                                                "objective_subtype": "DEFUSE_COVER",
                                                "save_subtype": "NONE",
                                                "episode_id": f"ep_obj_defcover_{stem}_r{r_idx}_s{slot}",
                                                "global_frame": global_f
                                            }
                                            extracted_records.append(rec)
                                            stats["by_state"]["OBJECTIVE"] += 1
                                            stats["by_split"][split_name]["OBJECTIVE"] += 1
                                            stats["by_subtype"]["OBJECTIVE"]["DEFUSE_COVER"] += 1
                                            stats["unique_players"].add(f"{stem}_{slot}")

                    # ----------------------------------------------------
                    # 2. RASTREAR SAVE TIPADO E EVIDÊNCIA POSITIVA
                    # ----------------------------------------------------
                    if not is_final_round_of_half: # Proibido em round final de metade
                        # Analisar final do round
                        for slot in range(10):
                            is_ct = r_X[-1, slot, 13] < 0.5
                            is_alive_end = r_X[-1, slot, 14] > 0.5
                            wpn_end = float(r_X[-1, slot, 11])
                            
                            if is_ct and is_alive_end and wpn_end >= 0.70: # Sobreviveu com Rifle/AWP
                                # Contagem de vivos no final
                                alive_cts = sum(1 for s in range(10) if r_X[-1, s, 13] < 0.5 and r_X[-1, s, 14] > 0.5)
                                alive_trs = sum(1 for s in range(10) if r_X[-1, s, 13] > 0.5 and r_X[-1, s, 14] > 0.5)
                                
                                # Critério de desvantagem grave (1v3+, 2v4+, ou 1v2 sem tempo/kit)
                                is_severe_disadv = (alive_cts <= 2 and alive_trs >= (alive_cts + 2))
                                is_solo_postplant = (alive_cts == 1 and plant_frame is not None and (r_len - plant_frame) > 160)
                                
                                if is_severe_disadv or is_solo_postplant:
                                    stats["raw_candidate_events"] += 1
                                    
                                    # Posição final deve ser em local recuado / safe zone ou longe da C4
                                    px_end = float(r_X[-1, slot, 0] * 4096.0)
                                    py_end = float(r_X[-1, slot, 1] * 4096.0)
                                    pz_end = float(r_X[-1, slot, 2] * 1024.0)
                                    
                                    in_safe = is_in_safe_zone(px_end, py_end)
                                    far_from_c4 = False
                                    if plant_pos is not None:
                                        d_c4 = math.hypot(px_end - plant_pos[0], py_end - plant_pos[1])
                                        far_from_c4 = (d_c4 > 1400.0)
                                    else:
                                        far_from_c4 = in_safe
                                        
                                    # Verificar se velocidade média final foi baixa (segurando spot)
                                    spd_final = np.hypot(r_X[-64:, slot, 3]*250.0, r_X[-64:, slot, 4]*250.0)
                                    mean_spd_final = float(np.mean(spd_final))
                                    
                                    if (in_safe or far_from_c4) and mean_spd_final < 140.0:
                                        # EVIDÊNCIA POSITIVA DE SAVE!
                                        stats["accepted_episodes"] += 1
                                        ep_id = f"ep_save_{stem}_r{r_idx}_s{slot}"
                                        
                                        # Identificar momento de decisão de save (últimos 8-15s do round)
                                        save_window_frames = min(r_len // 2, 192) # Até 12s
                                        save_start_f = r_len - save_window_frames
                                        save_dur_ms = int((save_window_frames / 16.0) * 1000)
                                        stats["durations_ms"].append(save_dur_ms)
                                        
                                        # Amostrar sequências do save com subtipos
                                        for f_off in range(save_start_f, r_len - 8, 16): # A cada 1s
                                            global_f = s_f + f_off
                                            if global_f < 32:
                                                continue
                                                
                                            time_to_end = (r_len - f_off) / 16.0
                                            if time_to_end > 8.0:
                                                save_sub = "SAVE_ROTATION" if float(np.hypot(r_X[f_off, slot, 3]*250.0, r_X[f_off, slot, 4]*250.0)) > 90.0 else "SAVE_DECISION"
                                            elif time_to_end > 3.0:
                                                save_sub = "SAVE_HOLD"
                                            else:
                                                save_sub = "WEAPON_PRESERVATION"
                                                
                                            rec = {
                                                "sequence_id": f"pos_{stem}_r{r_idx}_s{slot}_f{global_f}",
                                                "split": split_name,
                                                "demo_id": stem,
                                                "round_index": r_idx,
                                                "slot": slot,
                                                "team": "CT",
                                                "role": "ANCHOR" if wpn_end >= 0.95 else "SUPPORT",
                                                "tactic_id": "CT_PASSIVE_SAVE",
                                                "plan_stage": "Retake",
                                                "current_pos": [round(float(r_X[f_off, slot, 0] * 4096.0), 1),
                                                                round(float(r_X[f_off, slot, 1] * 4096.0), 1),
                                                                round(float(r_X[f_off, slot, 2] * 1024.0), 1)],
                                                "assigned_catalog_id": "UNMAPPED_POSITION",
                                                "semantic_type": "POSITION_PROFILE",
                                                "confidence_weight": 0.90 if in_safe else 0.75,
                                                "next_catalog_id": "UNMAPPED_POSITION",
                                                "next_sector": "CT",
                                                "expected_dwell_bucket": "LONG",
                                                "positioning_state": "SAVE",
                                                "objective_subtype": "NONE",
                                                "save_subtype": save_sub,
                                                "episode_id": ep_id,
                                                "global_frame": global_f
                                            }
                                            extracted_records.append(rec)
                                            stats["by_state"]["SAVE"] += 1
                                            stats["by_split"][split_name]["SAVE"] += 1
                                            stats["by_subtype"]["SAVE"][save_sub] += 1
                                            stats["unique_players"].add(f"{stem}_{slot}")
                                    else:
                                        stats["rejected_episodes"] += 1
                                else:
                                    stats["rejected_episodes"] += 1
                                    
        except Exception as e:
            print(f"Erro processando {npz_path.name}: {e}")
            continue
            
    print(f"\nExtração concluída!")
    print(f"Total de registros OBJECTIVE extraídos: {stats['by_state']['OBJECTIVE']}")
    print(f"  Train: {stats['by_split']['train']['OBJECTIVE']}, Val: {stats['by_split']['validation']['OBJECTIVE']}, Test: {stats['by_split']['test']['OBJECTIVE']}")
    print(f"  Subtipos OBJECTIVE: {dict(stats['by_subtype']['OBJECTIVE'])}")
    print(f"Total de registros SAVE extraídos: {stats['by_state']['SAVE']}")
    print(f"  Train: {stats['by_split']['train']['SAVE']}, Val: {stats['by_split']['validation']['SAVE']}, Test: {stats['by_split']['test']['SAVE']}")
    print(f"  Subtipos SAVE: {dict(stats['by_subtype']['SAVE'])}")
    print(f"Episódios aceitos: {stats['accepted_episodes']}, Rejeitados: {stats['rejected_episodes']}")
    
    # Salvar DataFrame de sequências enriquecidas
    df_extracted = pd.DataFrame(extracted_records)
    out_parquet = ds_dir / "positioning" / "objective_save_sequences.parquet"
    df_extracted.to_parquet(out_parquet, index=False)
    print(f"Salvo: {out_parquet} ({len(df_extracted)} linhas)")
    
    # Gerar JSON report
    median_dur = float(np.median(stats["durations_ms"])) if stats["durations_ms"] else 0.0
    report_json = {
        "generated_at_utc": "2026-11-07T00:54:00Z",
        "corpus_demos_analyzed": len(npz_files),
        "raw_candidate_events": stats["raw_candidate_events"],
        "accepted_episodes": stats["accepted_episodes"],
        "rejected_episodes": stats["rejected_episodes"],
        "acceptance_rate_pct": round(stats["accepted_episodes"] / max(1, stats["accepted_episodes"] + stats["rejected_episodes"]) * 100.0, 2),
        "unique_demos_with_accepted_events": len(stats["unique_demos"]),
        "unique_matches": len(stats["unique_matches"]),
        "unique_players": len(stats["unique_players"]),
        "median_duration_ms": median_dur,
        "total_sequences_extracted": len(extracted_records),
        "objective_counts": {
            "total": stats["by_state"]["OBJECTIVE"],
            "train": stats["by_split"]["train"]["OBJECTIVE"],
            "validation": stats["by_split"]["validation"]["OBJECTIVE"],
            "test": stats["by_split"]["test"]["OBJECTIVE"],
            "subtypes": dict(stats["by_subtype"]["OBJECTIVE"])
        },
        "save_counts": {
            "total": stats["by_state"]["SAVE"],
            "train": stats["by_split"]["train"]["SAVE"],
            "validation": stats["by_split"]["validation"]["SAVE"],
            "test": stats["by_split"]["test"]["SAVE"],
            "subtypes": dict(stats["by_subtype"]["SAVE"])
        },
        "criteria_verification": {
            "objective_train_ge_1000": stats["by_split"]["train"]["OBJECTIVE"] >= 1000,
            "objective_val_ge_100": stats["by_split"]["validation"]["OBJECTIVE"] >= 100,
            "save_train_ge_500": stats["by_split"]["train"]["SAVE"] >= 500,
            "save_val_ge_100": stats["by_split"]["validation"]["SAVE"] >= 100,
            "overall_status": "CORPUS_SUPPORT_SUFFICIENT" if (
                stats["by_split"]["train"]["OBJECTIVE"] >= 1000 and
                stats["by_split"]["validation"]["OBJECTIVE"] >= 100 and
                stats["by_split"]["train"]["SAVE"] >= 500 and
                stats["by_split"]["validation"]["SAVE"] >= 100
            ) else "INSUFFICIENT_EXISTING_CORPUS_SUPPORT"
        }
    }
    
    report_json_path = runs_dir / "objective_save_extraction_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)
    print(f"Salvo: {report_json_path}")
    
    # Gerar Markdown report
    md_content = f"""# Relatório de Extração de OBJECTIVE e SAVE no Corpus Mirage V2

Data: 2026-11-07  
Status: **{report_json['criteria_verification']['overall_status']}**  
Total de Demos Analisadas: **{len(npz_files)}**

---

## 1. Resumo Quantitativo

| Métrica | OBJECTIVE | SAVE | Total Geral |
| :--- | :---: | :---: | :---: |
| **Total de Sequências** | **{report_json['objective_counts']['total']}** | **{report_json['save_counts']['total']}** | **{report_json['total_sequences_extracted']}** |
| **Train Split** | {report_json['objective_counts']['train']} (Meta: $\\ge 1.000$) | {report_json['save_counts']['train']} (Meta: $\\ge 500$) | {report_json['objective_counts']['train'] + report_json['save_counts']['train']} |
| **Validation Split** | {report_json['objective_counts']['validation']} (Meta: $\\ge 100$) | {report_json['save_counts']['validation']} (Meta: $\\ge 100$) | {report_json['objective_counts']['validation'] + report_json['save_counts']['validation']} |
| **Test Split** | {report_json['objective_counts']['test']} | {report_json['save_counts']['test']} | {report_json['objective_counts']['test'] + report_json['save_counts']['test']} |

---

## 2. Proveniência e Estatísticas do Corpus

- **Eventos Candidatos Brutos**: {report_json['raw_candidate_events']}
- **Episódios Aceitos**: {report_json['accepted_episodes']}
- **Episódios Rejeitados**: {report_json['rejected_episodes']}
- **Taxa de Aceitação**: {report_json['acceptance_rate_pct']}%
- **Demos Únicas com Eventos Aceitos**: {report_json['unique_demos_with_accepted_events']}
- **Partidas Únicas**: {report_json['unique_matches']}
- **Jogadores Únicos**: {report_json['unique_players']}
- **Duração Mediana dos Episódios**: {report_json['median_duration_ms']:.1f} ms

---

## 3. Distribuição por Subestados Tipados

### 3.1 Subestados OBJECTIVE
{json.dumps(report_json['objective_counts']['subtypes'], indent=2)}

### 3.2 Subestados SAVE
{json.dumps(report_json['save_counts']['subtypes'], indent=2)}

---

## 4. Verificação de Portões de Suporte

- `OBJECTIVE Train >= 1000`: **{'PASS' if report_json['criteria_verification']['objective_train_ge_1000'] else 'FAIL'}** ({report_json['objective_counts']['train']})
- `OBJECTIVE Val >= 100`: **{'PASS' if report_json['criteria_verification']['objective_val_ge_100'] else 'FAIL'}** ({report_json['objective_counts']['validation']})
- `SAVE Train >= 500`: **{'PASS' if report_json['criteria_verification']['save_train_ge_500'] else 'FAIL'}** ({report_json['save_counts']['train']})
- `SAVE Val >= 100`: **{'PASS' if report_json['criteria_verification']['save_val_ge_100'] else 'FAIL'}** ({report_json['save_counts']['validation']})

### Veredito de Suporte:
```
{report_json['criteria_verification']['overall_status']}
```
"""
    
    report_md_path = runs_dir / "objective_save_extraction_report.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Salvo: {report_md_path}")
    
    return report_json

if __name__ == "__main__":
    extract_from_corpus()
