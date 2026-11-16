import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")

files_to_check = [
    Path("datasets/mirage_v2/canonical_temporal_splits_v1.json"),
    Path("datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet"),
    Path("tools/phase3a_training/materialize_full_temporal_index.py"),
    Path("tests/test_phase3a3_b_milestone2b1_full_index.py"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/shard_000.parquet"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/shard_005.parquet"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/dataset_manifest.json"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/demo_inventory.json"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/excluded_demos_manifest.json"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/next_sector_relabeling.json"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/objective_save_integration.json"),
    Path("datasets/mirage_v2/positioning_v2_full_temporal/pilot_preservation_catalog.json"),
    Path("training_runs/positioning_v2_real_temporal/full_index_accounting_reconciliation.json"),
    Path("training_runs/positioning_v2_real_temporal/full_index_distribution.json"),
    Path("training_runs/positioning_v2_real_temporal/full_index_jensen_shannon_divergence.json"),
    Path("training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json"),
    Path("training_runs/positioning_v2_real_temporal/full_index_dataloader_gates.json"),
    Path("training_runs/positioning_v2_real_temporal/data_provenance_temporal_audit.json"),
    Path("training_runs/positioning_v2_real_temporal/adversarial_success_audit.json"),
    Path("training_runs/positioning_v2_real_temporal/marco_2b1_final_report.md"),
    Path(".agents/teamwork/victory_auditor_2/handoff.md")
]

records = []
for rel in files_to_check:
    f = BASE_DIR / rel
    if f.exists():
        stat = f.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        records.append((mtime, rel))
    else:
        print(f"MISSING: {rel}")

records.sort(key=lambda x: x[0])
print("=== TIMELINE OF MODIFICATIONS (UTC) ===")
for mtime, rel in records:
    print(f"{mtime.isoformat()} -> {rel}")
