import hashlib
import json
import os
import sys

def verify_artifacts():
    ev_path = '.agents/audit/phase_evidence_matrix.json'
    with open(ev_path, 'r', encoding='utf-8') as f:
        matrix = json.load(f)

    all_matched = True
    print(f"Total evidences declared: {len(matrix['evidences'])}")
    print("-" * 80)
    for ev in matrix['evidences']:
        path = ev['artifact_path']
        expected_sha = ev['sha256']
        if not os.path.exists(path):
            print(f"[MISSING] {ev['evidence_id']} -> {path}")
            all_matched = False
            continue
        size = os.path.getsize(path)
        with open(path, 'rb') as f_art:
            content = f_art.read()
        actual_sha = hashlib.sha256(content).hexdigest()
        if actual_sha == expected_sha:
            print(f"[MATCH]   {ev['evidence_id']} (size: {size:>7} B) {path}")
        else:
            print(f"[MISMATCH] {ev['evidence_id']} -> {path}")
            print(f"  Expected: {expected_sha}")
            print(f"  Actual:   {actual_sha}")
            all_matched = False

    print("-" * 80)
    if all_matched:
        print("ALL 20 ARTIFACTS VERIFIED SUCCESSFULLY WITH EXACT SHA-256 MATCH.")
    else:
        print("FAILED: ONE OR MORE ARTIFACTS MISMATCHED OR MISSING.")
        sys.exit(1)

if __name__ == '__main__':
    verify_artifacts()
