import hashlib
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def check_file(rel_path: str, expected_hash: str = None):
    p = BASE_DIR / rel_path
    if not p.exists():
        return {"path": rel_path, "exists": False, "size": 0, "sha256": None, "hash_match": False}
    size = p.stat().st_size
    actual_hash = compute_sha256(p)
    match = (expected_hash is None or actual_hash.lower() == expected_hash.lower())
    return {
        "path": rel_path,
        "exists": True,
        "size": size,
        "sha256": actual_hash,
        "hash_match": match,
        "valid_64_hex": len(actual_hash) == 64 and all(c in "0123456789abcdef" for c in actual_hash.lower())
    }

print("=== CHECKING PILOT DATASET ===")
pilot_expected = "d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe"
pilot_res = check_file("datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet", pilot_expected)
print("Pilot:", pilot_res)

print("\n=== CHECKING 12 ARTIFACTS IN datasets/mirage_v2/positioning_v2_full_temporal/ ===")
dataset_artifacts = [
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_000.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_001.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_002.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_003.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_004.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_005.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/dataset_manifest.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/split_catalog.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/label_distribution.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/spot_ranking_coverage.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/accounting_reconciliation.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/dataloader_gates_telemetry.json"
]
for p in dataset_artifacts:
    print(check_file(p))

print("\n=== CHECKING 8 ARTIFACTS IN training_runs/positioning_v2_real_temporal/ ===")
training_artifacts = [
    "training_runs/positioning_v2_real_temporal/full_index_accounting_reconciliation.json",
    "training_runs/positioning_v2_real_temporal/full_index_distribution.json",
    "training_runs/positioning_v2_real_temporal/full_index_jensen_shannon_divergence.json",
    "training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json",
    "training_runs/positioning_v2_real_temporal/full_index_dataloader_gates.json",
    "training_runs/positioning_v2_real_temporal/data_provenance_temporal_audit.json",
    "training_runs/positioning_v2_real_temporal/adversarial_success_audit.json",
    "training_runs/positioning_v2_real_temporal/marco_2b1_final_report.md"
]
for p in training_artifacts:
    print(check_file(p))
