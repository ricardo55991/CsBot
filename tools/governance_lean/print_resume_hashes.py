import json

with open("deliverable_evidence.json", "r") as f:
    d = json.load(f)

targets = [
    "training_runs/intermediate_domain_study/intermediate_study_closure.json",
    "training_runs/positioning_v2_real_temporal/professional_resume_decision.json",
    "training_runs/positioning_v2_real_temporal/professional_spot_coverage_summary.json",
    "training_runs/positioning_v2_real_temporal/next_milestone_recommendation.md"
]

for t in targets:
    info = d["artifacts"][t]
    print(f"{t} | {info['size_bytes']} | {info['sha256']}")
