#!/usr/bin/env python3
"""
Auditoria Física de Hashes SHA-256 dos 20 Entregáveis do Marco 2B.1
"""

import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

ARTIFACTS = [
    # 12 de datasets/mirage_v2/positioning_v2_full_temporal/
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_000.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_001.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_002.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_003.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_004.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_005.parquet",
    "datasets/mirage_v2/positioning_v2_full_temporal/dataset_manifest.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/demo_inventory.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/excluded_demos_manifest.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/next_sector_relabeling.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/objective_save_integration.json",
    "datasets/mirage_v2/positioning_v2_full_temporal/pilot_preservation_catalog.json",

    # Artefatos de training_runs/positioning_v2_real_temporal/
    "training_runs/positioning_v2_real_temporal/full_index_accounting_reconciliation.json",
    "training_runs/positioning_v2_real_temporal/full_index_distribution.json",
    "training_runs/positioning_v2_real_temporal/full_index_jensen_shannon_divergence.json",
    "training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json",
    "training_runs/positioning_v2_real_temporal/full_index_dataloader_gates.json",
    "training_runs/positioning_v2_real_temporal/data_provenance_temporal_audit.json",
]


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    results = {}
    print("=== AUDITORIA FÍSICA DE ARTEFATOS ===")
    for rel_path in ARTIFACTS:
        p = BASE_DIR / rel_path
        if not p.exists():
            print(f"[MISSING] {rel_path}")
            results[rel_path] = {"exists": False}
        else:
            size = p.stat().st_size
            sha = compute_sha256(p)
            print(f"[EXISTS] {rel_path} | {size} bytes | SHA-256: {sha}")
            assert len(sha) == 64
            results[rel_path] = {"exists": True, "size_bytes": size, "sha256": sha}

    with open(Path(__file__).parent / "physical_hashes.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
