#!/usr/bin/env python3
"""
Marco 2B.4 - Etapa A: Congelamento do Candidato (SEM abrir o Test).
Gera:
- input_snapshot.json
- final_evaluation_contract.json
- save_fallback_declaration.json
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "final_evaluation"
DS_DIR = BASE_DIR / "datasets" / "mirage_v2"
INDEX_DIR = DS_DIR / "positioning_v2_full_temporal"

CKPT_2B34 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
CKPT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "selected_checkpoint.pt"
CONTRACT_2B37 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hybrid_state_composition_v1" / "composition_contract.json"
CONTRACT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "hierarchical_state_contract.json"

EXPECTED_2B34_SHA = "c7fb36647de92b7422f8389ef4c87343680e25d1da648fef883fbc4542e91608"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
    except Exception:
        return "UNKNOWN"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sha_2b34 = sha256_file(CKPT_2B34)
    if sha_2b34 != EXPECTED_2B34_SHA:
        raise ValueError(f"SHA-256 de 2B.3.4 divergente: {sha_2b34}")

    tracked_files = [
        CKPT_2B34,
        CKPT_2B36,
        CONTRACT_2B36,
        CONTRACT_2B37,
        BASE_DIR / "tools" / "phase3a_training" / "build_2b36_hierarchical_sidecar.py",
        BASE_DIR / "tools" / "phase3a_training" / "hierarchical_positioning_model.py",
        BASE_DIR / "tools" / "phase3a_training" / "positioning_model_v2.py",
        BASE_DIR / "tools" / "phase3a_training" / "canonical_v2_dataloader.py",
        BASE_DIR / "tools" / "phase3a_training" / "canonical_temporal_dataloader.py",
        DS_DIR / "canonical_temporal_splits_v1.json",
        DS_DIR / "test_unseen_teams_v2.json",
        DS_DIR / "test_unseen_players_v2.json",
        DS_DIR / "test_unseen_events_v2.json",
        DS_DIR / "test_recent_meta_v2.json",
        DS_DIR / "contracts" / "mirage_spot_catalog_v3.json",
        INDEX_DIR / "supervised_spot_mask_v1.json",
    ]
    for i in range(6):
        tracked_files.append(INDEX_DIR / f"shard_{i:03d}.parquet")
        tracked_files.append(INDEX_DIR / "label_sidecar_v2" / f"shard_{i:03d}_labels.parquet")

    hashes = {
        str(p.relative_to(BASE_DIR)).replace("\\", "/"): sha256_file(p)
        for p in tracked_files
    }

    snapshot = {
        "marco": "2B.4",
        "mode": "FINAL_EVALUATION",
        "checkpoint_frozen": True,
        "config_frozen": True,
        "thresholds_frozen": True,
        "git_commit": get_git_commit(),
        "hashes": hashes,
        "test_opened": False,
    }
    with open(OUT_DIR / "input_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    contract = {
        "contract_version": "2b4_final_evaluation_v1",
        "frozen": True,
        "base_state_source": "2B.3.4 (logits_state[:, :4] argmax -> TRANSIT, CLEARANCE, STAGING, HOLD)",
        "rare_override_source": "2B.3.6 (RareTacticalStateHead -> OBJECTIVE, RETAKE with causal eligibility)",
        "precedence": [
            "1. if objective_eligible and rare_pred == OBJECTIVE -> OBJECTIVE",
            "2. elif retake_eligible and rare_pred == RETAKE -> RETAKE",
            "3. else -> base_state",
        ],
        "thresholds": {
            "sector_transition_occurs": 0.525,
        },
        "neural_state_classes": ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE"],
        "save_policy": {
            "neural_save_disabled": True,
            "offline_candidate_disabled": True,
            "status": "RUNTIME_UTILITY_AI_FALLBACK",
            "excluded_from_neural_macro_f1": True,
        },
        "gates": {
            "composite_neural": {
                "supported_macro_f1_min": 0.42,
                "balanced_accuracy_min": 0.52,
                "TRANSIT_recall_min": 0.75,
                "CLEARANCE_recall_min": 0.70,
                "STAGING_recall_min": 0.20,
                "HOLD_recall_min": 0.35,
                "OBJECTIVE_min": {"precision": 0.20, "recall": 0.30, "f1": 0.24},
                "RETAKE_min": {"precision": 0.20, "recall": 0.30, "f1": 0.24},
            },
            "sector_transition": {
                "macro_f1_min": 0.55,
                "balanced_accuracy_min": 0.55,
                "TRANSITION_OCCURS_recall_min": 0.30,
                "NO_TRANSITION_recall_min": 0.75,
            },
            "next_sector": {"macro_f1_min": 0.45, "balanced_accuracy_min": 0.45},
            "spot_ranking": {"mrr_min": 0.72, "top1_min": 0.55, "top5_min": 0.92, "invalid_masked_eq": 0, "unsupported_eq": 0},
            "transition": {"supported_macro_f1_min": 0.55},
        },
    }
    with open(OUT_DIR / "final_evaluation_contract.json", "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)

    save_decl = {
        "FALLBACK_DECLARED": True,
        "NEURAL_SAVE_DISABLED": True,
        "UTILITY_AI_OWNS_SAVE": True,
        "status": "RUNTIME_UTILITY_AI_FALLBACK",
        "neural_metrics_reporting": "NOT_APPLICABLE_RUNTIME_FALLBACK",
        "reason": "Train episodes=43, Validation support=144, candidate policy precision=0.0397.",
    }
    with open(OUT_DIR / "save_fallback_declaration.json", "w", encoding="utf-8") as f:
        json.dump(save_decl, f, indent=2, ensure_ascii=False)

    print("Snapshot congelado e contrato 2B.4 gravados com sucesso (sem abrir o Test).")


if __name__ == "__main__":
    main()
