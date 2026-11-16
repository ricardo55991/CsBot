import glob
import os
import sys
from pathlib import Path
import pyarrow.parquet as pq
import numpy as np

INDEX_DIR = Path("datasets/mirage_v2/positioning_v2_full_temporal")
shards = sorted(list(INDEX_DIR.glob("shard_*.parquet")))

print(f"Auditing {len(shards)} shards...")

total_rows = 0
zero_coords_count = 0
invalid_window_len_count = 0
leakage_count = 0
invalid_next_sector = 0
next_sector_sources = set()
unique_seq_ids = set()
allowed_sectors = {"A", "B", "MID", "CT", "T", "DYNAMIC"}
split_counts = {"train": 0, "validation": 0, "test": 0}
window_keys = set()
duplicate_windows = 0

for s_idx, sp in enumerate(shards):
    print(f"Reading {sp.name}...")
    table = pq.read_table(
        sp,
        columns=[
            "sequence_id", "demo_id", "round_id", "slot", "split",
            "window_start_frame", "window_end_frame", "label_frame",
            "NextSector", "next_sector_source", "current_pos"
        ]
    )
    n = table.num_rows
    total_rows += n

    seq_ids = table["sequence_id"].to_pylist()
    unique_seq_ids.update(seq_ids)

    splits = table["split"].to_pylist()
    for s in splits:
        split_counts[s] = split_counts.get(s, 0) + 1

    starts = table["window_start_frame"].to_numpy()
    ends = table["window_end_frame"].to_numpy()
    labels = table["label_frame"].to_numpy()

    # Window length check: 32 frames => ends - starts == 31
    diffs = ends - starts
    bad_lens = np.sum(diffs != 31)
    invalid_window_len_count += bad_lens

    # Leakage check: label_frame == window_end_frame
    bad_leak = np.sum(labels != ends)
    leakage_count += bad_leak

    # NextSector validation
    next_secs = table["NextSector"].to_pylist()
    bad_secs = [sec for sec in next_secs if sec not in allowed_sectors]
    invalid_next_sector += len(bad_secs)

    sources = table["next_sector_source"].to_pylist()
    next_sector_sources.update(sources)

    # current_pos invalid [0, 0, 0] check
    poss = table["current_pos"].to_pylist()
    for p in poss:
        if abs(p[0]) < 1e-3 and abs(p[1]) < 1e-3 and abs(p[2]) < 1e-3:
            zero_coords_count += 1

print("\n=== EXHAUSTIVE SHARDS AUDIT RESULTS ===")
print(f"Total rows: {total_rows}")
print(f"Unique sequence_ids: {len(unique_seq_ids)} (duplicates: {total_rows - len(unique_seq_ids)})")
print(f"Split counts: {split_counts}")
print(f"Zero coordinates [0, 0, 0] count: {zero_coords_count}")
print(f"Invalid window length (diff != 31): {invalid_window_len_count}")
print(f"Target leakage (label != end): {leakage_count}")
print(f"Invalid NextSector classes: {invalid_next_sector}")
print(f"NextSector sources found: {next_sector_sources}")
