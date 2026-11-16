import json

with open("deliverable_evidence.json", "r") as f:
    d = json.load(f)

targets = [
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/input_snapshot.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/class_support.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/experiment_c_metrics.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/threshold_calibration.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/experiment_comparison.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/preservation_check.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/selected_patch_checkpoint.pt",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/test_result.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/findings.json",
    "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/rare_class_patch_final_report.md"
]

for t in targets:
    info = d["artifacts"][t]
    print(f"{t} | {info['size_bytes']} | {info['sha256']}")
