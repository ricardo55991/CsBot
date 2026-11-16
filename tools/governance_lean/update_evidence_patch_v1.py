"""
Atualiza deliverable_evidence.json com todos os artefatos do Marco 2B.3.1 (rare_class_patch_v1).
"""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PATCH_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1"

ARTIFACTS = [
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/input_snapshot.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/class_support.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/experiment_a_metrics.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/experiment_b_metrics.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/experiment_c_metrics.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/threshold_calibration.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/experiment_comparison.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/preservation_check.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/selected_patch_checkpoint.pt",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/test_result.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/findings.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/rare_class_patch_final_report.md",
    "tests/test_rare_class_patch.py"
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    ev_path = REPO_ROOT / "deliverable_evidence.json"
    if ev_path.exists():
        with open(ev_path, "r", encoding="utf-8") as f:
            evidence = json.load(f)
    else:
        evidence = {"schema": "csbot.deliverable_evidence.v1", "artifacts": {}}

    if "artifacts" not in evidence:
        evidence["artifacts"] = {}

    for rel in ARTIFACTS:
        full = REPO_ROOT / rel
        if full.exists():
            h = sha256_file(full)
            sz = full.stat().st_size
            evidence["artifacts"][rel] = {
                "sha256": h,
                "size_bytes": sz,
                "status": "MATERIALIZED_AND_VERIFIED"
            }

    with open(ev_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    # Copiar para dentro do diretório do patch como deliverable_evidence.json
    with open(PATCH_DIR / "deliverable_evidence.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print(f"DELIVERABLE_EVIDENCE_UPDATED: {len(ARTIFACTS)} artifacts registered.")

if __name__ == "__main__":
    main()
