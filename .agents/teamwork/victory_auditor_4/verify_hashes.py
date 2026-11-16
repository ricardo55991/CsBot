import json
import hashlib
from pathlib import Path

matrix_path = Path("training_runs/positioning_v2_real_temporal/full_training/milestone_2b3_evidence_matrix.json")
with open(matrix_path, "r", encoding="utf-8") as f:
    data = json.load(f)

deliverables = data.get("deliverables", [])
print(f"Checking {len(deliverables)} deliverables from evidence matrix:")
all_ok = True
for item in deliverables:
    p = Path(item["relative_path"])
    if not p.exists():
        print(f"MISSING: {p}")
        all_ok = False
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest().lower()
    exp = item["sha256"].lower()
    if h == exp:
        print(f"MATCH: {item['relative_path']} (bytes={p.stat().st_size})")
    else:
        print(f"MISMATCH: {item['relative_path']} (disk={h}, exp={exp})")
        all_ok = False

print(f"\nVerdict for milestone_2b3_evidence_matrix: {'ALL_21_MATCH' if all_ok else 'HAS_MISMATCH'}")
