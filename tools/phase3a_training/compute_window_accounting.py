#!/usr/bin/env python3
"""
Auditoria Rápida de Cobertura para o Marco 2A (Seção 3).
Calcula sobre todas as linhas de índice dos parquets, sem construir batches densos:
- valid_window_candidates (accepted)
- insufficient_history_candidates
- padded_window_candidates (explicitly_masked)
- invalid_round_candidates (rejected)
- invalid_slot_candidates (rejected)
- future_boundary_candidates (rejected)
- missing_npz_candidates (rejected)
- label_missing_candidates (rejected)

Separado por: Train, Validation e Test.
Garante fechamento: raw_candidates = accepted + rejected + explicitly_masked.
Gera: training_runs/positioning_v2_real_temporal/milestone_2a_window_accounting.json
"""

import json
import re
import time
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq

def main():
    t0 = time.time()
    splits_cfg = json.load(open("datasets/mirage_v2/canonical_temporal_splits_v1.json", "r", encoding="utf-8"))
    train_demos = set(splits_cfg["train_demos"])
    val_demos = set(splits_cfg["validation_demos"])
    test_demos = set(splits_cfg["test_demos"])
    all_demos = train_demos | val_demos | test_demos

    print(f"Carregando limites de round para {len(all_demos)} demos NPZ...")
    npz_dir = Path("F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage")
    cached_bounds = {}
    missing_npz_set = set()

    for d in all_demos:
        fpath = npz_dir / f"{d}_16hz.npz"
        if not fpath.exists():
            missing_npz_set.add(d)
            continue
        try:
            with np.load(fpath, mmap_mode="r") as data:
                X = data["X"]
                n_frames = X.shape[0]
                r_time = X[:, 0, 17]
                resets = np.where(np.diff(r_time) > 0.15)[0].tolist()
                bounds = [0] + [r + 1 for r in resets] + [n_frames]
                cached_bounds[d] = {"n_frames": n_frames, "bounds": bounds}
        except Exception:
            missing_npz_set.add(d)

    print(f"Limites carregados: {len(cached_bounds)} demos em {time.time() - t0:.2f}s.")

    seq_pattern = re.compile(r"pos_(.*)_r(\d+)_s(\d+)_f(\d+)")

    pos_dir = Path("datasets/mirage_v2/positioning/positioning_sequences_v1")
    shards = sorted(list(pos_dir.glob("shard_*.parquet")))

    accounting = {
        "Train": {
            "raw_candidates": 0,
            "valid_window_candidates": 0, # accepted (k >= 32)
            "insufficient_history_candidates": 0, # k < 32
            "padded_window_candidates": 0, # explicitly_masked (k < 32)
            "invalid_round_candidates": 0, # rejected
            "invalid_slot_candidates": 0, # rejected
            "future_boundary_candidates": 0, # rejected
            "missing_npz_candidates": 0, # rejected
            "label_missing_candidates": 0, # rejected
            "accepted": 0,
            "rejected": 0,
            "explicitly_masked": 0,
            "closure_check": False
        },
        "Validation": {
            "raw_candidates": 0,
            "valid_window_candidates": 0,
            "insufficient_history_candidates": 0,
            "padded_window_candidates": 0,
            "invalid_round_candidates": 0,
            "invalid_slot_candidates": 0,
            "future_boundary_candidates": 0,
            "missing_npz_candidates": 0,
            "label_missing_candidates": 0,
            "accepted": 0,
            "rejected": 0,
            "explicitly_masked": 0,
            "closure_check": False
        },
        "Test": {
            "raw_candidates": 0,
            "valid_window_candidates": 0,
            "insufficient_history_candidates": 0,
            "padded_window_candidates": 0,
            "invalid_round_candidates": 0,
            "invalid_slot_candidates": 0,
            "future_boundary_candidates": 0,
            "missing_npz_candidates": 0,
            "label_missing_candidates": 0,
            "accepted": 0,
            "rejected": 0,
            "explicitly_masked": 0,
            "closure_check": False
        }
    }

    cols = ["sequence_id", "split", "demo_id", "slot", "assigned_catalog_id", "next_sector", "plan_stage", "team", "role"]

    print("Processando shards de índices...")
    for shard in shards:
        table = pq.read_table(shard, columns=cols)
        pydict = table.to_pydict()
        n_rows = len(pydict["sequence_id"])

        for i in range(n_rows):
            split_raw = pydict["split"][i]
            if split_raw in ["train"]:
                s_key = "Train"
            elif split_raw in ["val", "validation"]:
                s_key = "Validation"
            elif split_raw in ["test"]:
                s_key = "Test"
            else:
                continue

            acc = accounting[s_key]
            acc["raw_candidates"] += 1

            demo_id = pydict["demo_id"][i]
            slot = pydict["slot"][i]
            seq_id = pydict["sequence_id"][i]

            # 1. Checar missing NPZ
            if demo_id not in cached_bounds:
                acc["missing_npz_candidates"] += 1
                acc["rejected"] += 1
                continue

            # 2. Checar slot inválido
            if slot is None or slot < 0 or slot > 9:
                acc["invalid_slot_candidates"] += 1
                acc["rejected"] += 1
                continue

            # 3. Checar labels obrigatórios
            if (pydict["assigned_catalog_id"][i] is None or 
                pydict["next_sector"][i] is None or 
                pydict["plan_stage"][i] is None or
                pydict["team"][i] is None or
                pydict["role"][i] is None):
                acc["label_missing_candidates"] += 1
                acc["rejected"] += 1
                continue

            # 4. Extrair frame da sequência
            m = seq_pattern.match(seq_id)
            if not m:
                acc["invalid_round_candidates"] += 1
                acc["rejected"] += 1
                continue

            f_idx = int(m.group(4))
            demo_info = cached_bounds[demo_id]
            bounds = demo_info["bounds"]
            n_frames = demo_info["n_frames"]

            # 5. Checar boundaries
            if f_idx >= n_frames:
                acc["future_boundary_candidates"] += 1
                acc["rejected"] += 1
                continue

            r_detected = int(np.searchsorted(bounds, f_idx, side="right") - 1)
            if r_detected < 0 or r_detected >= len(bounds) - 1:
                acc["invalid_round_candidates"] += 1
                acc["rejected"] += 1
                continue

            start_f = bounds[r_detected]
            end_f = bounds[r_detected + 1]

            if f_idx < start_f or f_idx >= end_f:
                acc["invalid_round_candidates"] += 1
                acc["rejected"] += 1
                continue

            # 6. Avaliar janela
            k = f_idx - start_f + 1
            if k >= 32:
                acc["valid_window_candidates"] += 1
                acc["accepted"] += 1
            else:
                acc["insufficient_history_candidates"] += 1
                acc["padded_window_candidates"] += 1
                acc["explicitly_masked"] += 1

    # Checagem de fechamento
    total_raw = 0
    total_accepted = 0
    total_rejected = 0
    total_masked = 0

    for s_key, acc in accounting.items():
        is_closed = (acc["raw_candidates"] == (acc["accepted"] + acc["rejected"] + acc["explicitly_masked"]))
        acc["closure_check"] = is_closed
        total_raw += acc["raw_candidates"]
        total_accepted += acc["accepted"]
        total_rejected += acc["rejected"]
        total_masked += acc["explicitly_masked"]

    out_data = {
        "schema_version": "1.0.0",
        "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
        "milestone": "Marco 2A - Auditoria Rápida de Cobertura (Seção 3)",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_index_rows": total_raw,
        "total_accepted": total_accepted,
        "total_rejected": total_rejected,
        "total_explicitly_masked": total_masked,
        "global_closure_check": (total_raw == total_accepted + total_rejected + total_masked),
        "accounting_by_split": accounting
    }

    out_file = Path("training_runs/positioning_v2_real_temporal/milestone_2a_window_accounting.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

    print(f"Salvo com sucesso em: {out_file}")
    print(f"Total rows: {total_raw}, Accepted: {total_accepted}, Masked: {total_masked}, Rejected: {total_rejected}")
    print(f"Fechamento global: {out_data['global_closure_check']}")

if __name__ == "__main__":
    main()
