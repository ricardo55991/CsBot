"""
Verificação rápida do suporte de OBJECTIVE no split de validação.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = REPO_ROOT / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"

def main():
    print("Inspecionando OBJECTIVE nos shards 4 e 5 (Validação)...")
    total_val = 0
    obj_val = 0
    obj_indices = []

    for i in [4, 5]:
        b_path = INDEX_DIR / f"shard_{i:03d}.parquet"
        table = pq.read_table(b_path, columns=["split", "PositioningState", "sequence_id"])
        split_arr = table["split"].to_numpy(zero_copy_only=False)
        pos_arr = table["PositioningState"].to_numpy(zero_copy_only=False)
        seq_arr = table["sequence_id"].to_numpy(zero_copy_only=False)

        val_mask = (split_arr == "validation")
        total_val += int(np.sum(val_mask))
        obj_mask = val_mask & (pos_arr == "OBJECTIVE")
        obj_val += int(np.sum(obj_mask))
        
        found_seqs = seq_arr[obj_mask]
        if len(found_seqs) > 0:
            obj_indices.extend(found_seqs[:5])

    print(f"Total Validation rows: {total_val}")
    print(f"Total OBJECTIVE rows in Validation: {obj_val}")
    print(f"Sample OBJECTIVE sequence_ids: {obj_indices[:3]}")

if __name__ == "__main__":
    main()
