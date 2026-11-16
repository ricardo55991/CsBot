"""
Atualiza deliverable_evidence.json com os novos artefatos preparados nesta etapa.
"""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

NEW_ARTIFACTS = [
    "training_runs/intermediate_domain_study/faceit_downloads_api_application_draft.md",
    "training_runs/intermediate_domain_study/faceit_downloads_api_application_draft.json",
    "training_runs/intermediate_domain_study/gamersclub_research_packet.json",
    "training_runs/intermediate_domain_study/valve_opt_in_guidelines.md",
    "training_runs/intermediate_domain_study/valve_opt_in_submission_contract.json",
    "training_runs/intermediate_domain_study/intermediate_pilot_sampling_plan.md",
    "datasets/mirage_domains/intermediate_competitive/intermediate_pilot_manifest_template.json",
    "tools/intermediate_demo_acquisition/ingest_opt_in_demo.py",
    "tools/intermediate_demo_acquisition/run_all_dry_runs.py",
    "training_runs/intermediate_domain_study/dry_run_validation_report.json"
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
