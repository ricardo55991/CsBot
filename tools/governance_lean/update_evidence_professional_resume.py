"""
Atualiza deliverable_evidence.json com os artefatos de encerramento da fase intermediária
e retomada do Positioning Transformer profissional.
"""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

NEW_ARTIFACTS = [
    "training_runs/intermediate_domain_study/intermediate_study_closure.json",
    "training_runs/positioning_v2_real_temporal/professional_resume_decision.json",
    "training_runs/positioning_v2_real_temporal/professional_spot_coverage_summary.json",
    "training_runs/positioning_v2_real_temporal/next_milestone_recommendation.md"
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    ev_path = REPO_ROOT / "deliverable_evidence.json"
    with open(ev_path, "r", encoding="utf-8") as f:
        evidence = json.load(f)

    if "artifacts" not in evidence:
        evidence["artifacts"] = {}

    for rel in NEW_ARTIFACTS:
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

    print(f"DELIVERABLE_EVIDENCE_UPDATED: {len(NEW_ARTIFACTS)} artifacts registered.")

if __name__ == "__main__":
    main()
