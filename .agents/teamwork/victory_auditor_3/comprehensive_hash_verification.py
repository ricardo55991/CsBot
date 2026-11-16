import hashlib
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

declared_artifacts = {
    # 10.1 Artefatos sob datasets/mirage_v2/positioning_v2_full_temporal/ (12 Entregáveis)
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_000.parquet": "39ebbe19d9782ffba743d968517b8624530af2daa9375ece6ba742d648c6bebb",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_001.parquet": "f849f724a67338c1d0158f6c407e615e6a9fa5d1faa675779eb1d8125ad27e6a",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_002.parquet": "619e0416f779ba6a9aedeb6b34d380469e72e89557bf7c67eff5cfafaaab8d5a",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_003.parquet": "546f0df72594e80b5bc8780be17b06ed2876a38bbccbc367adfdee776d2f0612",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_004.parquet": "a79d189b18ad1f7cc71d6ead3f4528cde3371d10cbea81193cb7f1337a1a7166",
    "datasets/mirage_v2/positioning_v2_full_temporal/shard_005.parquet": "7aec90a0b5d40570b0aee2a52e9080cc802486f7955686b68453c2c093d10b70",
    "datasets/mirage_v2/positioning_v2_full_temporal/dataset_manifest.json": "cd7d8ea2435e5b45936d869eb190eb9b0f32b6ee9f1bf45d7bba47cc8f8f6d4c",
    "datasets/mirage_v2/positioning_v2_full_temporal/demo_inventory.json": "01d68490ff60098c4775b6f94156043c2474cffa10da9deb5743ccb31e4a450f",
    "datasets/mirage_v2/positioning_v2_full_temporal/excluded_demos_manifest.json": "721a921204c472f1f9278e679c9bc6ade1b5b2f67bdd82a629084fa75b96433f",
    "datasets/mirage_v2/positioning_v2_full_temporal/next_sector_relabeling.json": "601b88d8ef5ee3d2cc22e980fb6eaa276850a563e7833685e03a14caa6c45b89",
    "datasets/mirage_v2/positioning_v2_full_temporal/objective_save_integration.json": "f978a2489f847613f218706456ad65ea3c54845dc7472fbab2a36375e89c35c7",
    "datasets/mirage_v2/positioning_v2_full_temporal/pilot_preservation_catalog.json": "60990c026548a2472fe63edaa1a1aa4a392b9fba6a7f42d37a6bf4472871253e",

    # 10.2 Artefatos sob training_runs/positioning_v2_real_temporal/ (8 Entregáveis)
    "training_runs/positioning_v2_real_temporal/full_index_accounting_reconciliation.json": "43ee5e23894180539bc4c4482148fbb583e918e8859acb9851a2443e0ad8871a",
    "training_runs/positioning_v2_real_temporal/full_index_distribution.json": "0ffb0a5b91339c5159d65b59c70b725bc209991e405dd4a32a5ff7cc232f5f2a",
    "training_runs/positioning_v2_real_temporal/full_index_jensen_shannon_divergence.json": "cf46f84a77ee95a41c89abe5cec66fadf49f0c42b7e6fd77b83c3d17bcad4aae",
    "training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json": "3b67b40087b683d73237c02a9c21bbb84f11d415809d2b486da759a7b203ab01",
    "training_runs/positioning_v2_real_temporal/full_index_dataloader_gates.json": "7bef3c9b44aba7ae789e85a996a5bc4341f20b0f3e5de96fc177c390e33c8d76",
    "training_runs/positioning_v2_real_temporal/data_provenance_temporal_audit.json": "84ceeaa8ba35d92850b9dda85b6783ce59203505e09acd1fda2832b2ae16d3d1",
    "training_runs/positioning_v2_real_temporal/adversarial_success_audit.json": "e63ada070f5dd8ebe08eb88498348c0ba9e430aa6ba40f420f50cd3c5e51c924",
    # Item 20 is marco_2b1_final_report.md itself
}

all_ok = True
for rel_path, expected_hash in declared_artifacts.items():
    p = BASE_DIR / rel_path
    if not p.exists():
        print(f"FAIL - Missing file: {rel_path}")
        all_ok = False
        continue
    actual_hash = compute_sha256(p)
    if actual_hash.lower() != expected_hash.lower():
        print(f"FAIL - Hash mismatch: {rel_path}\n  Expected: {expected_hash}\n  Actual:   {actual_hash}")
        all_ok = False
    else:
        print(f"PASS - {rel_path} ({len(actual_hash)} hex chars match)")

p_report = BASE_DIR / "training_runs/positioning_v2_real_temporal/marco_2b1_final_report.md"
report_hash = compute_sha256(p_report)
print(f"PASS - marco_2b1_final_report.md exists, size={p_report.stat().st_size}, sha256={report_hash}")

print(f"\nOVERALL HASH VERIFICATION: {'PASS' if all_ok else 'FAIL'}")
