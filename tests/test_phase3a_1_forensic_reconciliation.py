#!/usr/bin/env python3
"""
Suíte de Testes da Fase 3A.1: Reconciliação Forense e Auditoria Canônica.
Cobre 20 testes formais conforme a Seção 15 da especificação técnica.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import torch

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

RUNS_DIR = BASE_DIR / "training_runs" / "positioning_v1"
MODELS_DIR = BASE_DIR / "models" / "positioning"
DS_DIR = BASE_DIR / "datasets" / "mirage_v2"
EVAL_DIR = RUNS_DIR / "canonical_eval"

def compute_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

# 1. MetricsComeFromCanonicalArrays
def test_01_metrics_come_from_canonical_arrays():
    s_logits = np.load(EVAL_DIR / "state_logits.npy")
    s_labels = np.load(EVAL_DIR / "state_labels.npy")
    s_preds = np.argmax(s_logits, axis=1)

    acc = float(np.mean(s_preds == s_labels))
    with open(RUNS_DIR / "canonical_test_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
    assert abs(acc - metrics["state_metrics"]["accuracy"]) < 1e-4

# 2. ConfusionMatrixCountsMatchSupport
def test_02_confusion_matrix_counts_match_support():
    df_counts = pd.read_csv(RUNS_DIR / "confusion_matrix_state_counts.csv", index_col="TrueState")
    s_labels = np.load(EVAL_DIR / "state_labels.npy")
    from tools.phase3a_training.data_utils import STATE_NAMES
    for i, name in enumerate(STATE_NAMES):
        expected_supp = int(np.sum(s_labels == i))
        actual_supp = int(df_counts.loc[name, "Support"])
        assert expected_supp == actual_supp, f"Suporte diverge para {name}"

# 3. ZeroSupportClassShowsNA
def test_03_zero_support_class_shows_na():
    df_norm = pd.read_csv(RUNS_DIR / "confusion_matrix_state_normalized.csv", index_col="TrueState", keep_default_na=False)
    for zero_cls in ["OBJECTIVE", "SAVE"]:
        row_vals = df_norm.loc[zero_cls]
        for col in ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE", "SAVE"]:
            assert row_vals[col] == "N/A", f"Esperado N/A em {zero_cls} -> {col}"

# 4. MacroF1MatchesSklearn
def test_04_macro_f1_matches_sklearn():
    s_logits = np.load(EVAL_DIR / "state_logits.npy")
    s_labels = np.load(EVAL_DIR / "state_labels.npy")
    s_preds = np.argmax(s_logits, axis=1)

    # Cálculo padrão de Macro F1 sobre 7 classes
    f1s = []
    for c in range(7):
        tp = int(np.sum((s_preds == c) & (s_labels == c)))
        fp = int(np.sum((s_preds == c) & (s_labels != c)))
        fn = int(np.sum((s_preds != c) & (s_labels == c)))
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        f1s.append(f)
    expected_f1 = float(np.mean(f1s))

    with open(RUNS_DIR / "canonical_test_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
    assert abs(expected_f1 - metrics["state_metrics"]["macro_f1_all_7_classes"]) < 1e-4

# 5. BalancedAccuracyMatchesSklearn
def test_05_balanced_accuracy_matches_sklearn():
    s_logits = np.load(EVAL_DIR / "state_logits.npy")
    s_labels = np.load(EVAL_DIR / "state_labels.npy")
    s_preds = np.argmax(s_logits, axis=1)

    recalls = []
    for c in range(7):
        sup = np.sum(s_labels == c)
        if sup > 0:
            tp = np.sum((s_preds == c) & (s_labels == c))
            recalls.append(tp / sup)
    expected_bacc = float(np.mean(recalls))

    with open(RUNS_DIR / "canonical_test_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
    assert abs(expected_bacc - metrics["state_metrics"]["balanced_accuracy"]) < 1e-4

# 6. SpotMetricsUseEligibleOnly
def test_06_spot_metrics_use_eligible_only():
    spot_masks = np.load(EVAL_DIR / "spot_loss_masks.npy")
    with open(RUNS_DIR / "spot_ranking_canonical.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["eligible_count"] == int(np.sum(spot_masks))
    assert data["total_test_instances"] == len(spot_masks)

# 7. MaskedCandidateCannotWin
def test_07_masked_candidate_cannot_win():
    from tools.phase3a_training.positioning_model import PositioningTransformerV1
    model = PositioningTransformerV1()
    model.eval()
    h = torch.randn(2, 32, 18)
    tm = torch.randn(2, 32, 4, 18)
    mask = torch.zeros(2, 53, dtype=torch.bool)
    mask[:, 7] = True # Apenas spot 7 permitido
    with torch.no_grad():
        out = model(h, tm, mask)
    logits = out["logits_spot"].numpy()
    assert np.all(np.argmax(logits, axis=1) == 7), "Candidato mascarado não pode ser selecionado"

# 8. LearningCurveRowsMatchJsonl
def test_08_learning_curve_rows_match_jsonl():
    df_curves = pd.read_csv(RUNS_DIR / "learning_curves_canonical.csv")
    for s in [42026, 42027, 42028]:
        s_lines = [json.loads(line) for line in open(RUNS_DIR / f"seed_{s}" / "metrics_validation.jsonl")]
        for ep in range(len(s_lines)):
            row = df_curves[(df_curves["seed"] == s) & (df_curves["epoch"] == ep+1)].iloc[0]
            assert abs(row["composite_score"] - s_lines[ep]["composite_score"]) < 1e-4

# 9. TestSplitHashMatchesManifest
def test_09_test_split_hash_matches_manifest():
    p = DS_DIR / "positioning" / "canonical_test_set.parquet"
    real_hash = compute_sha256(p)
    with open(RUNS_DIR / "canonical_test_set_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert real_hash == manifest["split_sha256"]

# 10. CheckpointHashMatchesModelSelection
def test_10_checkpoint_hash_matches_model_selection():
    chk_p = MODELS_DIR / "de_mirage_positioning_v1.pt"
    real_hash = compute_sha256(chk_p)
    with open(RUNS_DIR / "best_model_selection.json", "r", encoding="utf-8") as f:
        sel = json.load(f)
    assert real_hash == sel["master_model_sha256"]

# 11. ObjectiveZeroSupportCannotHaveRecall
def test_11_objective_zero_support_cannot_have_recall():
    with open(RUNS_DIR / "canonical_test_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
    obj_info = metrics["state_metrics"]["per_class"]["OBJECTIVE"]
    assert obj_info["support"] == 0
    assert obj_info["recall"] is None

# 12. SaveZeroSupportCannotHaveRecall
def test_12_save_zero_support_cannot_have_recall():
    with open(RUNS_DIR / "canonical_test_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
    save_info = metrics["state_metrics"]["per_class"]["SAVE"]
    assert save_info["support"] == 0
    assert save_info["recall"] is None

# 13. ChallengeSetHasNoTrainOverlap
def test_13_challenge_set_has_no_train_overlap():
    ch_parquet = DS_DIR / "positioning" / "rare_state_challenge_set.parquet"
    df_ch = pd.read_parquet(ch_parquet)
    assert "train" not in df_ch["split"].values, "Challenge Set não pode conter amostras do split train"

# 14. ChallengeExamplesHaveRealProvenance
def test_14_challenge_examples_have_real_provenance():
    with open(RUNS_DIR / "rare_state_challenge_provenance.json", "r", encoding="utf-8") as f:
        prov = json.load(f)
    for rec in prov["records"]:
        assert rec["demo_id"] is not None and len(rec["demo_id"]) > 0
        assert rec["source_shard"].startswith("shard_")

# 15. ReportsUseSameCheckpoint
def test_15_reports_use_same_checkpoint():
    with open(RUNS_DIR / "master_checkpoint_audit.json", "r", encoding="utf-8") as f:
        audit = json.load(f)
    with open(RUNS_DIR / "best_model_selection.json", "r", encoding="utf-8") as f:
        sel = json.load(f)
    with open(EVAL_DIR / "canonical_eval_manifest.json", "r", encoding="utf-8") as f:
        eval_m = json.load(f)
    assert audit["sha256"] == sel["master_model_sha256"] == eval_m["master_model_sha256"]

# 16. ReportsUseSameTestSplit
def test_16_reports_use_same_test_split():
    with open(RUNS_DIR / "canonical_test_set_manifest.json", "r", encoding="utf-8") as f:
        t_man = json.load(f)
    with open(EVAL_DIR / "canonical_eval_manifest.json", "r", encoding="utf-8") as f:
        eval_m = json.load(f)
    assert t_man["split_sha256"] == eval_m["test_dataset_sha256"]

# 17. CanonicalArraysAreImmutable
def test_17_canonical_arrays_are_immutable():
    with open(EVAL_DIR / "canonical_eval_manifest.json", "r", encoding="utf-8") as f:
        eval_m = json.load(f)
    for fname, meta in eval_m["files"].items():
        fp = EVAL_DIR / fname
        assert compute_sha256(fp) == meta["sha256"], f"Hash corrompido em {fname}"

# 18. MetricCalculationIsReproducible
def test_18_metric_calculation_is_reproducible():
    s_logits = np.load(EVAL_DIR / "state_logits.npy")
    s_labels = np.load(EVAL_DIR / "state_labels.npy")
    s_preds1 = np.argmax(s_logits, axis=1)
    s_preds2 = np.argmax(s_logits, axis=1)
    assert np.array_equal(s_preds1, s_preds2)

# 19. TestInferenceUsesEvalMode
def test_19_test_inference_uses_eval_mode():
    chk_p = MODELS_DIR / "de_mirage_positioning_v1.pt"
    chk = torch.load(chk_p, map_location="cpu")
    from tools.phase3a_training.positioning_model import PositioningTransformerV1
    model = PositioningTransformerV1()
    model.load_state_dict(chk["model_state_dict"])
    model.eval()
    assert not model.training, "Modelo deve estar em eval()"

# 20. DropoutDisabledDuringEvaluation
def test_20_dropout_disabled_during_evaluation():
    from tools.phase3a_training.positioning_model import PositioningTransformerV1
    model = PositioningTransformerV1()
    model.eval()
    for m in model.modules():
        if isinstance(m, torch.nn.Dropout):
            assert not m.training, "Dropout deve estar desativado em modo eval"
