#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 1: Auditoria Forense do DataLoader Temporal Canônico de 32 Frames.

Valida deterministicamente 500 sequências amostradas sob seed 42026:
- 250 amostras do split Train
- 125 amostras do split Validation
- 125 amostras do split Test

Compara item a item cada amostra produzida pelo DataLoader contra os tensores brutos NPZ
em F:\\CS2_MLMove_Pipeline\\extracted_tensors\\de_mirage\\{demo_id}_16hz.npz.

Métricas Canônicas Auditadas:
1. ToleranceMatchRate (meta: 100.0%)
2. SyntheticWindowRate (meta: 0.0%)
3. UnmaskedPaddingRate (meta: 0.0%)
4. RoundBoundaryViolationRate (meta: 0.0%)
5. FutureLeakageRate (meta: 0.0%)
6. TeammateRealSlotMatchRate (meta: 100.0%)
7. MeanSpatialDisplacement (unidades do CS2 e normalizadas)
8. MeanTemporalVariance (unidades do CS2 e normalizadas)

Gera:
- training_runs/positioning_v1/temporal_dataloader_metrics.json
- training_runs/positioning_v1/npz_window_batch_audit.json
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import torch
from torch.utils.data import Subset, DataLoader

# Raiz no sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    CanonicalTemporalPositioningDataset,
    create_canonical_temporal_dataloader,
    canonical_collate_fn,
    NPZCacheManager,
    DEFAULT_NPZ_DIR
)


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_audit(seed: int = 42026, npz_dir: Path = DEFAULT_NPZ_DIR) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    print("=" * 80)
    print("FASE 3A.3-B (MARCO 1): AUDITORIA FORENSE DO DATALOADER TEMPORAL CANÔNICO")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Seed Determinística: {seed}")
    print(f"Diretório NPZ: {npz_dir}")
    print("=" * 80)

    ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    runs_dir = BASE_DIR / "training_runs" / "positioning_v1"
    runs_dir.mkdir(parents=True, exist_ok=True)

    cache_manager = NPZCacheManager(npz_dir=npz_dir)

    # 1. Carregar os 3 Datasets
    print("\n[Passo 1/4] Carregando datasets dos três splits...")
    t0 = time.time()

    train_ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="train",
        cache_manager=cache_manager,
        preload_npz=False
    )
    val_ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="validation",
        cache_manager=cache_manager,
        preload_npz=False
    )
    test_ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="test",
        cache_manager=cache_manager,
        preload_npz=False
    )

    print(f"  -> Train pool: {len(train_ds):,} sequências")
    print(f"  -> Validation pool: {len(val_ds):,} sequências")
    print(f"  -> Test pool: {len(test_ds):,} sequências")
    print(f"  -> Datasets indexados em {time.time() - t0:.2f}s")

    # 2. Amostragem determinística sob seed 42026
    print(f"\n[Passo 2/4] Amostrando 500 instâncias deterministicamente sob seed {seed}...")
    rng = np.random.RandomState(seed)

    n_train = 250
    n_val = 125
    n_test = 125
    total_samples = n_train + n_val + n_test

    train_indices = rng.choice(len(train_ds), size=n_train, replace=False).tolist()
    val_indices = rng.choice(len(val_ds), size=n_val, replace=False).tolist()
    test_indices = rng.choice(len(test_ds), size=n_test, replace=False).tolist()

    sub_train = Subset(train_ds, train_indices)
    sub_val = Subset(val_ds, val_indices)
    sub_test = Subset(test_ds, test_indices)

    batch_size = 32
    train_loader = DataLoader(sub_train, batch_size=batch_size, shuffle=False, collate_fn=canonical_collate_fn)
    val_loader = DataLoader(sub_val, batch_size=batch_size, shuffle=False, collate_fn=canonical_collate_fn)
    test_loader = DataLoader(sub_test, batch_size=batch_size, shuffle=False, collate_fn=canonical_collate_fn)

    # 3. Execução da Auditoria Forense Amostra por Amostra
    print(f"\n[Passo 3/4] Auditando tensores emitidos pelos DataLoaders contra tensores crus NPZ...")

    expected_linspace = np.linspace(-0.01, 0.0, 32, dtype=np.float32)

    sample_audit_records: List[Dict[str, Any]] = []

    # Contadores globais
    tolerance_matches = 0
    synthetic_windows = 0
    unmasked_paddings = 0
    round_boundary_violations = 0
    future_leakage_violations = 0
    teammate_slot_matches = 0
    total_teammates_evaluated = 0

    spatial_displacements_norm: List[float] = []
    spatial_displacements_world: List[float] = []
    temporal_variances_norm: List[float] = []
    temporal_variances_world: List[float] = []

    split_stats = {
        "train": {"total": 0, "matches": 0, "synthetic": 0, "unmasked_pad": 0, "round_viol": 0, "future_leak": 0, "tm_matches": 0, "tm_total": 0, "padded": 0},
        "validation": {"total": 0, "matches": 0, "synthetic": 0, "unmasked_pad": 0, "round_viol": 0, "future_leak": 0, "tm_matches": 0, "tm_total": 0, "padded": 0},
        "test": {"total": 0, "matches": 0, "synthetic": 0, "unmasked_pad": 0, "round_viol": 0, "future_leak": 0, "tm_matches": 0, "tm_total": 0, "padded": 0}
    }

    # Cache de arquivos crus lidos diretamente do disco
    raw_npz_cache: Dict[str, Dict[str, Any]] = {}

    def get_raw_npz_data(demo_id: str) -> Dict[str, Any]:
        if demo_id not in raw_npz_cache:
            p = npz_dir / f"{demo_id}_16hz.npz"
            if not p.exists():
                p = npz_dir / f"{demo_id}.npz"
            sha256 = compute_sha256(p)
            with np.load(p) as d:
                raw_X = d["X"] # [total_frames, 10, 18]
            r_time = raw_X[:, 0, 17]
            diffs = np.diff(r_time)
            resets = np.where(diffs > 0.15)[0]
            bounds = [0] + [int(r + 1) for r in resets] + [len(r_time)]
            raw_npz_cache[demo_id] = {
                "X": raw_X,
                "path": str(p),
                "sha256": sha256,
                "round_bounds": bounds,
                "n_frames": len(raw_X)
            }
        return raw_npz_cache[demo_id]

    loaders = [
        ("train", train_loader, n_train),
        ("validation", val_loader, n_val),
        ("test", test_loader, n_test)
    ]

    global_sample_idx = 0

    for split_name, loader, expected_n in loaders:
        print(f"  Auditando split '{split_name}' ({expected_n} amostras)...")
        for batch in loader:
            batch_history = batch["history"].numpy()       # [B, 32, 18]
            batch_teammates = batch["teammates"].numpy()   # [B, 32, 4, 18]
            batch_mask = batch["temporal_mask"].numpy()    # [B, 32]
            batch_meta = batch["metadata"]                 # List[Dict]

            b_size = batch_history.shape[0]
            for b in range(b_size):
                meta = batch_meta[b]
                dl_hist = batch_history[b]
                dl_tm = batch_teammates[b]
                dl_m = batch_mask[b]

                demo_id = meta["demo_id"]
                round_idx = meta["round_index"]
                slot = meta["slot"]
                f_idx = meta["frame_index"]
                seq_id = meta["sequence_id"]

                # Carregar diretamente do disco
                raw_info = get_raw_npz_data(demo_id)
                raw_X = raw_info["X"]
                raw_bounds = raw_info["round_bounds"]

                # Determinar SEMPRE e OBRIGATORIAMENTE a fronteira usando f_idx via busca determinística
                r_det = int(np.searchsorted(raw_bounds, f_idx, side="right") - 1)
                r_det = max(0, min(r_det, len(raw_bounds) - 2))
                start_f = int(raw_bounds[r_det])
                end_f = int(raw_bounds[r_det + 1])

                k = f_idx - start_f + 1
                is_padded = k < 32
                padding_len = max(0, 32 - k)

                # Aliados esperados
                if slot < 5:
                    expected_tm_slots = [s for s in range(5) if s != slot]
                else:
                    expected_tm_slots = [s for s in range(5, 10) if s != slot]

                # Construir ground truth esperado
                if not is_padded:
                    expected_hist = raw_X[f_idx - 31 : f_idx + 1, slot, :]
                    expected_tm = raw_X[f_idx - 31 : f_idx + 1, expected_tm_slots, :]
                    expected_m = np.ones(32, dtype=np.float32)
                else:
                    expected_hist = np.zeros((32, 18), dtype=np.float32)
                    expected_tm = np.zeros((32, 4, 18), dtype=np.float32)
                    expected_m = np.zeros(32, dtype=np.float32)
                    if k > 0:
                        expected_hist[32 - k :] = raw_X[start_f : f_idx + 1, slot, :]
                        expected_tm[32 - k :] = raw_X[start_f : f_idx + 1, expected_tm_slots, :]
                        expected_m[32 - k :] = 1.0

                # 1. ToleranceMatchRate (meta: 100.0%)
                max_diff_hist = float(np.max(np.abs(dl_hist - expected_hist)))
                max_diff_tm = float(np.max(np.abs(dl_tm - expected_tm)))
                max_diff_m = float(np.max(np.abs(dl_m - expected_m)))
                is_tolerance_match = bool(max_diff_hist < 1e-5 and max_diff_tm < 1e-5 and max_diff_m < 1e-5)

                if is_tolerance_match:
                    tolerance_matches += 1
                    split_stats[split_name]["matches"] += 1

                # 2. SyntheticWindowRate (meta: 0.0%)
                # Verificar drift linear artificial e clones transladados
                drift_x = dl_hist[:, 0] - dl_hist[-1, 0]
                is_linear_drift = bool(np.allclose(drift_x, expected_linspace, atol=1e-5))

                is_tm_clone = False
                for tm_idx in range(4):
                    expected_clone_offset = (tm_idx + 1) * 0.05
                    actual_offset_x = dl_tm[:, tm_idx, 0] - dl_hist[:, 0]
                    if np.allclose(actual_offset_x, expected_clone_offset, atol=1e-4):
                        is_tm_clone = True
                        break

                is_synthetic = is_linear_drift or is_tm_clone
                if is_synthetic:
                    synthetic_windows += 1
                    split_stats[split_name]["synthetic"] += 1

                # 3. UnmaskedPaddingRate (meta: 0.0%)
                # Ocorre se algum frame de padding tiver dl_m > 0.0
                unmasked_pad_count = 0
                if is_padded:
                    unmasked_pad_count = int(np.sum(dl_m[:padding_len] > 0.0))

                has_unmasked_padding = unmasked_pad_count > 0
                if has_unmasked_padding:
                    unmasked_paddings += 1
                    split_stats[split_name]["unmasked_pad"] += 1

                if is_padded:
                    split_stats[split_name]["padded"] += 1

                # 4. RoundBoundaryViolationRate (meta: 0.0%)
                # Ocorre se a janela leu frames de rounds anteriores (t < start_f)
                # Na janela canônica, para k < 32, os frames 0..32-k devem ser zeros
                is_round_viol = False
                if is_padded:
                    if not np.all(dl_hist[:padding_len] == 0.0) or not np.all(dl_tm[:padding_len] == 0.0):
                        is_round_viol = True
                if is_round_viol:
                    round_boundary_violations += 1
                    split_stats[split_name]["round_viol"] += 1

                # 5. FutureLeakageRate (meta: 0.0%)
                # Ocorre se o último frame dl_hist[-1] não corresponder a f_idx
                # ou se houver leitura de frames posteriores a f_idx
                is_future_leak = False
                # O frame 31 deve ser exatamente o frame f_idx
                if not np.allclose(dl_hist[31], raw_X[f_idx, slot], atol=1e-5):
                    is_future_leak = True
                # Verificar se algum frame pós f_idx vazou
                if f_idx + 1 < raw_info["n_frames"]:
                    future_frame = raw_X[f_idx + 1, slot]
                    # Se frame 31 for idêntico ao futuro mas diferente do presente (em frame de movimento)
                    if np.allclose(dl_hist[31], future_frame, atol=1e-5) and not np.allclose(raw_X[f_idx, slot], future_frame, atol=1e-5):
                        is_future_leak = True

                if is_future_leak:
                    future_leakage_violations += 1
                    split_stats[split_name]["future_leak"] += 1

                # 6. TeammateRealSlotMatchRate (meta: 100.0%)
                matching_tm_count = 0
                for tm_idx in range(4):
                    real_slot = expected_tm_slots[tm_idx]
                    total_teammates_evaluated += 1
                    split_stats[split_name]["tm_total"] += 1

                    if not is_padded:
                        raw_tm_slice = raw_X[f_idx - 31 : f_idx + 1, real_slot, :]
                        match = bool(np.allclose(dl_tm[:, tm_idx, :], raw_tm_slice, atol=1e-5))
                    else:
                        match_valid = bool(np.allclose(dl_tm[32 - k :, tm_idx, :], raw_X[start_f : f_idx + 1, real_slot, :], atol=1e-5))
                        match_pad = bool(np.all(dl_tm[: 32 - k, tm_idx, :] == 0.0))
                        match = match_valid and match_pad

                    if match:
                        matching_tm_count += 1
                        teammate_slot_matches += 1
                        split_stats[split_name]["tm_matches"] += 1

                # 7. MeanSpatialDisplacement & MeanTemporalVariance
                first_valid_t = 32 - k if is_padded else 0
                valid_hist = dl_hist[first_valid_t:, :3]

                disp_norm = float(np.linalg.norm(dl_hist[31, :3] - dl_hist[first_valid_t, :3]))
                disp_world = float(disp_norm * 3000.0)
                spatial_displacements_norm.append(disp_norm)
                spatial_displacements_world.append(disp_world)

                var_norm = float(np.mean(np.var(valid_hist, axis=0))) if len(valid_hist) > 1 else 0.0
                var_world = float(var_norm * (3000.0 ** 2))
                temporal_variances_norm.append(var_norm)
                temporal_variances_world.append(var_world)

                split_stats[split_name]["total"] += 1

                record = {
                    "sample_index": global_sample_idx,
                    "split": split_name,
                    "sequence_id": seq_id,
                    "demo_id": demo_id,
                    "npz_path": raw_info["path"],
                    "npz_sha256": raw_info["sha256"],
                    "round_index": round_idx,
                    "slot": slot,
                    "frame_index": f_idx,
                    "start_frame": start_f,
                    "end_frame": end_f,
                    "k_frames_in_round": k,
                    "is_padded": is_padded,
                    "padding_frames": padding_len,
                    "temporal_mask_sum": float(np.sum(dl_m)),
                    "unmasked_padding_count": unmasked_pad_count,
                    "is_tolerance_match": is_tolerance_match,
                    "is_synthetic_window": is_synthetic,
                    "is_round_boundary_violation": is_round_viol,
                    "is_future_leakage": is_future_leak,
                    "teammate_slots": expected_tm_slots,
                    "teammate_matches": matching_tm_count,
                    "max_diff_history": max_diff_hist,
                    "max_diff_teammates": max_diff_tm,
                    "max_diff_mask": max_diff_m,
                    "spatial_displacement_norm": disp_norm,
                    "spatial_displacement_world": disp_world,
                    "temporal_variance_norm": var_norm,
                    "temporal_variance_world": var_world
                }
                sample_audit_records.append(record)
                global_sample_idx += 1

    # 4. Cálculo das taxas e consolidação de resultados
    print(f"\n[Passo 4/4] Consolidando métricas e gerando relatórios de auditoria...")

    tolerance_match_rate = (tolerance_matches / total_samples) * 100.0
    synthetic_window_rate = (synthetic_windows / total_samples) * 100.0
    unmasked_padding_rate = (unmasked_paddings / total_samples) * 100.0
    round_boundary_violation_rate = (round_boundary_violations / total_samples) * 100.0
    future_leakage_rate = (future_leakage_violations / total_samples) * 100.0
    teammate_real_slot_match_rate = (teammate_slot_matches / total_teammates_evaluated) * 100.0

    mean_disp_norm = float(np.mean(spatial_displacements_norm))
    mean_disp_world = float(np.mean(spatial_displacements_world))
    mean_var_norm = float(np.mean(temporal_variances_norm))
    mean_var_world = float(np.mean(temporal_variances_world))

    total_padded_samples = sum(s["padded"] for s in split_stats.values())

    # Verificação de metas
    all_targets_met = bool(
        tolerance_match_rate == 100.0 and
        synthetic_window_rate == 0.0 and
        unmasked_padding_rate == 0.0 and
        round_boundary_violation_rate == 0.0 and
        future_leakage_rate == 0.0 and
        teammate_real_slot_match_rate == 100.0
    )

    metrics_summary = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_seed": seed,
        "total_samples_evaluated": total_samples,
        "splits_composition": {
            "train": n_train,
            "validation": n_val,
            "test": n_test
        },
        "padded_samples_count": total_padded_samples,
        "padded_samples_rate_pct": (total_padded_samples / total_samples) * 100.0,
        "metrics": {
            "ToleranceMatchRate": {
                "value_pct": tolerance_match_rate,
                "target_pct": 100.0,
                "formula": f"({tolerance_matches}/{total_samples})",
                "status": "PASS" if tolerance_match_rate == 100.0 else "FAIL"
            },
            "SyntheticWindowRate": {
                "value_pct": synthetic_window_rate,
                "target_pct": 0.0,
                "formula": f"({synthetic_windows}/{total_samples})",
                "status": "PASS" if synthetic_window_rate == 0.0 else "FAIL"
            },
            "UnmaskedPaddingRate": {
                "value_pct": unmasked_padding_rate,
                "target_pct": 0.0,
                "formula": f"({unmasked_paddings}/{total_samples})",
                "status": "PASS" if unmasked_padding_rate == 0.0 else "FAIL"
            },
            "RoundBoundaryViolationRate": {
                "value_pct": round_boundary_violation_rate,
                "target_pct": 0.0,
                "formula": f"({round_boundary_violations}/{total_samples})",
                "status": "PASS" if round_boundary_violation_rate == 0.0 else "FAIL"
            },
            "FutureLeakageRate": {
                "value_pct": future_leakage_rate,
                "target_pct": 0.0,
                "formula": f"({future_leakage_violations}/{total_samples})",
                "status": "PASS" if future_leakage_rate == 0.0 else "FAIL"
            },
            "TeammateRealSlotMatchRate": {
                "value_pct": teammate_real_slot_match_rate,
                "target_pct": 100.0,
                "formula": f"({teammate_slot_matches}/{total_teammates_evaluated})",
                "status": "PASS" if teammate_real_slot_match_rate == 100.0 else "FAIL"
            },
            "MeanSpatialDisplacement": {
                "world_units": mean_disp_world,
                "normalized_units": mean_disp_norm,
                "unit": "CS2 game units"
            },
            "MeanTemporalVariance": {
                "world_units_squared": mean_var_world,
                "normalized_units": mean_var_norm,
                "unit": "CS2 game units^2"
            }
        },
        "metrics_by_split": {
            s_name: {
                "total_samples": s_data["total"],
                "tolerance_matches": s_data["matches"],
                "tolerance_match_rate_pct": (s_data["matches"] / s_data["total"]) * 100.0,
                "synthetic_rate_pct": (s_data["synthetic"] / s_data["total"]) * 100.0,
                "unmasked_padding_rate_pct": (s_data["unmasked_pad"] / s_data["total"]) * 100.0,
                "round_boundary_violation_rate_pct": (s_data["round_viol"] / s_data["total"]) * 100.0,
                "future_leakage_rate_pct": (s_data["future_leak"] / s_data["total"]) * 100.0,
                "teammate_match_rate_pct": (s_data["tm_matches"] / s_data["tm_total"]) * 100.0 if s_data["tm_total"] > 0 else 100.0,
                "padded_samples": s_data["padded"]
            }
            for s_name, s_data in split_stats.items()
        },
        "all_targets_met": all_targets_met,
        "verdict": "CANONICAL_TEMPORAL_DATALOADER_AUDIT_PASS" if all_targets_met else "CANONICAL_TEMPORAL_DATALOADER_AUDIT_FAIL"
    }

    out_batch_path = runs_dir / "npz_window_batch_audit.json"
    with open(out_batch_path, "w", encoding="utf-8") as f:
        json.dump(sample_audit_records, f, indent=2)

    batch_sha256 = compute_sha256(out_batch_path)

    metrics_summary["artifacts"] = {
        "npz_window_batch_audit_json": {
            "path": str(out_batch_path.relative_to(BASE_DIR)).replace("\\", "/"),
            "sha256": batch_sha256,
            "bytes": out_batch_path.stat().st_size
        }
    }

    out_metrics_path = runs_dir / "temporal_dataloader_metrics.json"
    with open(out_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    metrics_sha256 = compute_sha256(out_metrics_path)

    print("\n" + "=" * 80)
    print("RESULTADOS DA AUDITORIA FORENSE:")
    print("=" * 80)
    print(f"Total de Amostras: {total_samples} (Train={n_train}, Val={n_val}, Test={n_test})")
    print(f"Amostras Padded (Início de Round): {total_padded_samples} ({total_padded_samples/total_samples*100:.2f}%)")
    print(f"ToleranceMatchRate:             {tolerance_match_rate:.2f}% (Meta: 100.0%) [{metrics_summary['metrics']['ToleranceMatchRate']['status']}]")
    print(f"SyntheticWindowRate:            {synthetic_window_rate:.2f}% (Meta: 0.0%) [{metrics_summary['metrics']['SyntheticWindowRate']['status']}]")
    print(f"UnmaskedPaddingRate:            {unmasked_padding_rate:.2f}% (Meta: 0.0%) [{metrics_summary['metrics']['UnmaskedPaddingRate']['status']}]")
    print(f"RoundBoundaryViolationRate:     {round_boundary_violation_rate:.2f}% (Meta: 0.0%) [{metrics_summary['metrics']['RoundBoundaryViolationRate']['status']}]")
    print(f"FutureLeakageRate:              {future_leakage_rate:.2f}% (Meta: 0.0%) [{metrics_summary['metrics']['FutureLeakageRate']['status']}]")
    print(f"TeammateRealSlotMatchRate:      {teammate_real_slot_match_rate:.2f}% (Meta: 100.0%) [{metrics_summary['metrics']['TeammateRealSlotMatchRate']['status']}]")
    print(f"MeanSpatialDisplacement:        {mean_disp_world:.2f} game units (norm: {mean_disp_norm:.4f})")
    print(f"MeanTemporalVariance:           {mean_var_world:.2f} game units^2 (norm: {mean_var_norm:.6f})")
    print(f"Veredito Global:                {metrics_summary['verdict']}")
    print("=" * 80)
    print(f"Artefato 1: {out_metrics_path} (SHA-256: {metrics_sha256})")
    print(f"Artefato 2: {out_batch_path} (SHA-256: {batch_sha256})")
    print("=" * 80)

    return metrics_summary, sample_audit_records


if __name__ == "__main__":
    run_audit(seed=42026)
