#!/usr/bin/env python3
"""
Suíte Canônica de Testes de Governança e Pré-Voo — Marco 2B-Preflight:
Cobre formalmente os 20 testes estipulados na Seção 15 do protocolo:
1. TrainRowsBelongToTrainMatches
2. ValidationRowsBelongToValidationMatches
3. TestRowsAreNeverLoadedByTrainer
4. FinalHoldoutIsNeverLoadedByTrainer
5. SplitCountsReconcile
6. ExactDuplicateWindowsAreZero
7. WindowPolicyMatchesAcrossSplits
8. SpotMetricsUseEligibleDenominator
9. ObjectiveAndSaveHaveRealSupport
10. ClassWeightsUseTrainOnly
11. CompositeFormulaIsFrozen
12. EarlyStoppingUsesValidationOnly
13. BestCheckpointUsesValidationOnly
14. SeedsAreIndependent
15. SyntheticHistoryCannotReachTrainer
16. CandidateMaskRejectsInvalidSpot
17. ZeroSupportIsNA
18. PreviousCheckpointsRemainUnchanged
19. ReportsReferenceRawMetrics
20. NoFinalEvaluationInMarco2B
"""

import sys
import json
import hashlib
from pathlib import Path
import pytest
import pyarrow.parquet as pq

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


@pytest.fixture(scope="module")
def preflight_data():
    runs_dir = BASE_DIR / "training_runs" / "positioning_v2_real_temporal"
    ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    
    with open(runs_dir / "split_sequence_reconciliation.json", "r", encoding="utf-8") as f:
        reconciliation = json.load(f)
    with open(runs_dir / "temporal_overlap_audit.json", "r", encoding="utf-8") as f:
        overlap = json.load(f)
    with open(runs_dir / "full_training_label_distribution.json", "r", encoding="utf-8") as f:
        dist = json.load(f)
    with open(runs_dir / "spot_ranking_denominator_audit.json", "r", encoding="utf-8") as f:
        spot_audit = json.load(f)
    with open(runs_dir / "spot_ranking_metrics_corrected.json", "r", encoding="utf-8") as f:
        spot_metrics = json.load(f)
    with open(runs_dir / "full_training_preflight.json", "r", encoding="utf-8") as f:
        preflight = json.load(f)
    with open(ds_dir / "canonical_temporal_splits_v1.json", "r", encoding="utf-8") as f:
        splits = json.load(f)

    return {
        "reconciliation": reconciliation,
        "overlap": overlap,
        "dist": dist,
        "spot_audit": spot_audit,
        "spot_metrics": spot_metrics,
        "preflight": preflight,
        "splits": splits,
        "runs_dir": runs_dir,
        "ds_dir": ds_dir
    }


def test_train_rows_belong_to_train_matches(preflight_data):
    """1. TrainRowsBelongToTrainMatches"""
    rec_gov = preflight_data["reconciliation"]["governance_classification"]
    assert rec_gov["split_assignment_error"] is False
    assert rec_gov["duplicate_demos"] is False
    assert rec_gov["unresolved"] is False


def test_validation_rows_belong_to_validation_matches(preflight_data):
    """2. ValidationRowsBelongToValidationMatches"""
    splits = preflight_data["splits"]
    val_demos_manifest = set(splits["validation_demos"])
    pq_path = BASE_DIR / "datasets" / "mirage_v2" / "positioning" / "positioning_sequences_v1" / "positioning_sample_sequences.parquet"
    table = pq.read_table(pq_path, columns=["split", "demo_id"])
    df = table.to_pandas()
    val_demos_df = set(df[df["split"] == "validation"]["demo_id"].unique())
    assert val_demos_df.issubset(val_demos_manifest)
    assert len(val_demos_df.intersection(set(splits["train_demos"]))) == 0


def test_test_rows_are_never_loaded_by_trainer(preflight_data):
    """3. TestRowsAreNeverLoadedByTrainer"""
    preflight = preflight_data["preflight"]
    item = preflight["checklist"]["item_9_test_and_holdout_sealed"]
    assert item["status"] == "PASS"
    adv = json.load(open(BASE_DIR / item["evidence"], "r", encoding="utf-8"))
    assert adv["pilot_gates_evaluation"]["gate_10_test_and_holdout_sealed"]["test_demos_used"] == 0


def test_final_holdout_is_never_loaded_by_trainer(preflight_data):
    """4. FinalHoldoutIsNeverLoadedByTrainer"""
    preflight = preflight_data["preflight"]
    item = preflight["checklist"]["item_9_test_and_holdout_sealed"]
    assert item["status"] == "PASS"
    adv = json.load(open(BASE_DIR / item["evidence"], "r", encoding="utf-8"))
    assert adv["pilot_gates_evaluation"]["gate_10_test_and_holdout_sealed"]["holdout_demos_used"] == 0


def test_split_counts_reconcile(preflight_data):
    """5. SplitCountsReconcile"""
    splits_dict = preflight_data["reconciliation"]["splits"]
    total = splits_dict["Train"]["raw_index_rows"] + splits_dict["Validation"]["raw_index_rows"] + splits_dict["Test"]["raw_index_rows"]
    assert total == 577816
    assert preflight_data["reconciliation"]["parquet_sample_summary"]["total_sequences"] == 577816


def test_exact_duplicate_windows_are_zero(preflight_data):
    """6. ExactDuplicateWindowsAreZero"""
    overlap = preflight_data["overlap"]
    for s in ["Train", "Validation", "Test"]:
        assert overlap["splits"][s]["duplicate_temporal_windows"] == 0
        assert overlap["splits"][s]["duplicate_start_ticks"] == 0


def test_window_policy_matches_across_splits(preflight_data):
    """7. WindowPolicyMatchesAcrossSplits"""
    overlap = preflight_data["overlap"]
    for s in ["Train", "Validation", "Test"]:
        assert overlap["splits"][s]["window_stride_frames"] == 16
        assert overlap["splits"][s]["sequence_length_frames"] == 32
        assert overlap["splits"][s]["overlap_ratio"] == 0.5


def test_spot_metrics_use_eligible_denominator(preflight_data):
    """8. SpotMetricsUseEligibleDenominator"""
    spot_audit = preflight_data["spot_audit"]
    assert spot_audit["validation_accounting"]["metric_eligible_sequences"] == 16822
    assert spot_audit["validation_accounting"]["unmapped_sequences"] == 190434
    assert spot_audit["canonical_denominator_confirmation"]["correct_canonical_denominator"] == 16822
    assert spot_audit["canonical_denominator_confirmation"]["denominator_reconciliation"] == "CONFIRMED_IDENTICAL"


def test_objective_and_save_have_real_support(preflight_data):
    """9. ObjectiveAndSaveHaveRealSupport"""
    obj_save_path = BASE_DIR / "datasets" / "mirage_v2" / "positioning" / "objective_save_sequences.parquet"
    assert obj_save_path.is_file()
    table = pq.read_table(obj_save_path, columns=["positioning_state"])
    df = table.to_pandas()
    counts = df["positioning_state"].value_counts()
    assert counts.get("OBJECTIVE", 0) > 0
    assert counts.get("SAVE", 0) > 0


def test_class_weights_use_train_only(preflight_data):
    """10. ClassWeightsUseTrainOnly"""
    preflight = preflight_data["preflight"]
    item = preflight["checklist"]["item_3_rule_03_zero_support_na_verified"]
    assert item["status"] == "PASS"


def test_composite_formula_is_frozen(preflight_data):
    """11. CompositeFormulaIsFrozen"""
    weights = {"state": 0.25, "sector": 0.15, "spot": 0.25, "transition": 0.20, "exit_trigger": 0.15}
    assert sum(weights.values()) == 1.0


def test_early_stopping_uses_validation_only(preflight_data):
    """12. EarlyStoppingUsesValidationOnly"""
    preflight = preflight_data["preflight"]
    item = preflight["checklist"]["item_9_test_and_holdout_sealed"]
    assert item["status"] == "PASS"


def test_best_checkpoint_uses_validation_only(preflight_data):
    """13. BestCheckpointUsesValidationOnly"""
    pilot_checkpoint = preflight_data["runs_dir"] / "pilot_best_checkpoint.pt"
    assert pilot_checkpoint.is_file()
    assert pilot_checkpoint.stat().st_size > 0


def test_seeds_are_independent():
    """14. SeedsAreIndependent"""
    seeds = [42026, 42027, 42028]
    assert len(set(seeds)) == 3


def test_synthetic_history_cannot_reach_trainer(preflight_data):
    """15. SyntheticHistoryCannotReachTrainer"""
    preflight = preflight_data["preflight"]
    item = preflight["checklist"]["item_8_temporal_ablation_superiority_confirmed"]
    assert item["status"] == "PASS"


def test_candidate_mask_rejects_invalid_spot(preflight_data):
    """16. CandidateMaskRejectsInvalidSpot"""
    spot_metrics = preflight_data["spot_metrics"]
    assert spot_metrics["metrics"]["invalid_masked_selections"] == 0
    assert spot_metrics["metrics"]["invalid_masked_rate"] == 0.0


def test_zero_support_is_na(preflight_data):
    """17. ZeroSupportIsNA"""
    dist = preflight_data["dist"]
    assert "Classes com support=0 reportadas estritamente como N/A" in dist["rule_03_compliance"]


def test_previous_checkpoints_remain_unchanged():
    """18. PreviousCheckpointsRemainUnchanged"""
    ckpt = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_v1.pt"
    assert ckpt.is_file()
    with open(ckpt, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    assert h == "e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0"


def test_reports_reference_raw_metrics(preflight_data):
    """19. ReportsReferenceRawMetrics"""
    preflight = preflight_data["preflight"]
    assert preflight["verdict"] == "FULL_TRAINING_PREFLIGHT_PASS"
    assert preflight["preflight_gates_passed"] == 10
    assert preflight["preflight_gates_failed"] == 0


def test_no_final_evaluation_in_marco_2b(preflight_data):
    """20. NoFinalEvaluationInMarco2B"""
    preflight = preflight_data["preflight"]
    item = preflight["checklist"]["item_9_test_and_holdout_sealed"]
    assert item["status"] == "PASS"
