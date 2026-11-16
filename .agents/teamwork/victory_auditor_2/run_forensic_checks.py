import os
import hashlib
import json
import pyarrow.parquet as pq

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def check_file(path, expected_hash=None):
    if not os.path.exists(path):
        return {"path": path, "exists": False, "size": 0, "sha256": None, "hash_match": False}
    size = os.path.getsize(path)
    actual_hash = sha256_file(path)
    match = True if expected_hash is None else (actual_hash.lower() == expected_hash.lower())
    return {
        "path": path,
        "exists": True,
        "size": size,
        "sha256": actual_hash,
        "expected_hash": expected_hash,
        "hash_match": match
    }

print("=== CHECKING PILOT DATASET ===")
pilot_path = r"datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet"
pilot_expected = "d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe"
res_pilot = check_file(pilot_path, pilot_expected)
print(json.dumps(res_pilot, indent=2))

print("\n=== CHECKING 12 ARTIFACTS IN datasets/mirage_v2/positioning_v2_full_temporal/ ===")
expected_12 = {
    "shard_000.parquet": "39ebbe19d9782ffba743d968517b8624530af2daa9375ece6ba742d648c6bebb",
    "shard_001.parquet": "f849f724a67338c1d0158f6c407e615e6a9fa5d1faa675779eb1d8125ad27e6a",
    "shard_002.parquet": "619e0416f779ba6a9aedeb6b34d380469e72e89557bf7c67eff5cfafaaab8d5a",
    "shard_003.parquet": "546f0df72594e80b5bc8780be17b06ed2876a38bbccbc367adfdee776d2f0612",
    "shard_004.parquet": "a79d189b18ad1f7cc71d6ead3f4528cde3371d10cbea81193cb7f1337a1a7166",
    "shard_005.parquet": "7aec90a0b5d40570b0aee2a52e9080cc802486f7955686b68453c2c093d10b70",
    "dataset_manifest.json": "cd7d8ea2435e5b45936d869eb190eb9b0f32b6ee9f1bf45d7bba47cc8f8f6d4c",
    "demo_inventory.json": "01d68490ff60098c4775b6f94156043c2474cffa10da9deb5743ccb31e4a450f",
    "excluded_demos_manifest.json": "721a921204c472f1f9278e679c9bc6ade1b5b2f67bdd82a629084fa75b96433f",
    "next_sector_relabeling.json": "601b88d8ef5ee3d2cc22e980fb6eaa276850a563e7833685e03a14caa6c45b89",
    "objective_save_integration.json": "f978a2489f847613f218706456ad65ea3c54845dc7472fbab2a36375e89c35c7",
    "pilot_preservation_catalog.json": "60990c026548a2472fe63edaa1a1aa4a392b9fba6a7f42d37a6bf4472871253e"
}

results_12 = []
for name, exp_h in expected_12.items():
    p = os.path.join("datasets/mirage_v2/positioning_v2_full_temporal", name)
    r = check_file(p, exp_h)
    results_12.append(r)
    print(f"[{'PASS' if r['hash_match'] and r['exists'] else 'FAIL'}] {name} (size: {r['size']}, sha256: {r['sha256']})")

print("\n=== CHECKING 8 ARTIFACTS IN training_runs/positioning_v2_real_temporal/ ===")
expected_8 = {
    "full_index_accounting_reconciliation.json": "43ee5e23894180539bc4c4482148fbb583e918e8859acb9851a2443e0ad8871a",
    "full_index_distribution.json": "0ffb0a5b91339c5159d65b59c70b725bc209991e405dd4a32a5ff7cc232f5f2a",
    "full_index_jensen_shannon_divergence.json": "cf46f84a77ee95a41c89abe5cec66fadf49f0c42b7e6fd77b83c3d17bcad4aae",
    "full_index_spot_ranking_coverage.json": "3b67b40087b683d73237c02a9c21bbb84f11d415809d2b486da759a7b203ab01",
    "full_index_dataloader_gates.json": "7bef3c9b44aba7ae789e85a996a5bc4341f20b0f3e5de96fc177c390e33c8d76",
    "data_provenance_temporal_audit.json": "84ceeaa8ba35d92850b9dda85b6783ce59203505e09acd1fda2832b2ae16d3d1",
    "adversarial_success_audit.json": "fd0b9f99da5089887e86422cc3413ec1a50faa5475fb81dd0aeeda06ee4bf0ad",
    "marco_2b1_final_report.md": "2ba12d27e571074526ffa4937582b80db416d3499d18b4580219b311ded57c56"
}

results_8 = []
for name, exp_h in expected_8.items():
    p = os.path.join("training_runs/positioning_v2_real_temporal", name)
    r = check_file(p, exp_h)
    results_8.append(r)
    print(f"[{'PASS' if r['hash_match'] and r['exists'] else 'FAIL'}] {name} (size: {r['size']}, sha256: {r['sha256']})")

print("\n=== PARQUET SCHEMA & SHARD SUMMARY ===")
total_rows = 0
for i in range(6):
    sp = f"datasets/mirage_v2/positioning_v2_full_temporal/shard_{i:03d}.parquet"
    pf = pq.read_table(sp)
    total_rows += pf.num_rows
    if i == 0:
        print("Schema columns:", pf.column_names)
        print("Num columns:", len(pf.column_names))
    print(f"shard_{i:03d}.parquet rows: {pf.num_rows}")
print("Total rows across all 6 shards:", total_rows)
