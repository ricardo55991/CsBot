#!/usr/bin/env python3
"""
Marco 2B.3.7 - Seção 7: 12 Testes Direcionados da Composição Híbrida.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import STATE_NAMES
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import (
    load_split_dataframe,
    EXPECTED_BASE_SHA256,
)
from tools.phase3a_training.run_marco_2b37_hybrid_composition import (
    compose_hybrid_predictions,
    CKPT_2B34,
    CKPT_2B36,
    OUT_DIR,
)


def test_01_BaseStateUsesApprovedJointCheckpoint():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    assert snap["base_2b34_checkpoint_sha256"] == EXPECTED_BASE_SHA256
    assert snap["training_executed"] is False


def test_02_ObjectiveOverrideRequiresEligibility():
    base = np.array([0, 0])
    rare = np.array([1, 1])  # OBJECTIVE
    obj_elig = np.array([True, False])
    ret_elig = np.array([False, False])
    sav_rule = np.array([False, False])
    out = compose_hybrid_predictions(base, rare, obj_elig, ret_elig, sav_rule)
    assert int(out[0]) == 4  # OBJECTIVE
    assert int(out[1]) == 0  # Sem elegibilidade -> mantém base


def test_03_RetakeOverrideRequiresEligibility():
    base = np.array([3, 3])  # HOLD
    rare = np.array([2, 2])  # RETAKE
    obj_elig = np.array([False, False])
    ret_elig = np.array([True, False])
    sav_rule = np.array([False, False])
    out = compose_hybrid_predictions(base, rare, obj_elig, ret_elig, sav_rule)
    assert int(out[0]) == 5  # RETAKE
    assert int(out[1]) == 3  # Sem elegibilidade -> mantém HOLD


def test_04_SaveRequiresMultipleCausalSignals():
    with open(OUT_DIR / "save_policy_candidate.json", "r", encoding="utf-8") as f:
        sp = json.load(f)
    for token in ["own_alive<enemy_alive", "round_time<=22.0", "min_site_dist>=650.0", "weapon>=0.7"]:
        assert token in sp["rule"]


def test_05_SurvivalAloneDoesNotProduceSave():
    base = np.array([0])
    rare = np.array([0])
    out = compose_hybrid_predictions(base, rare, np.array([False]), np.array([False]), np.array([False]))
    assert int(out[0]) == 0


def test_06_RareOverridePrecedenceIsDeterministic():
    # Precedência: OBJECTIVE > RETAKE > SAVE > BASE
    base = np.array([0, 0, 0])
    rare = np.array([1, 2, 0])
    obj_e = np.array([True, False, False])
    ret_e = np.array([True, True, False])
    sav_r = np.array([True, True, True])
    out = compose_hybrid_predictions(base, rare, obj_e, ret_e, sav_r)
    assert list(out) == [4, 5, 6]


def test_07_TestIsNeverLoaded():
    with pytest.raises(ValueError, match="estritamente proibido"):
        load_split_dataframe("test")


def test_08_FinalHoldoutIsNeverLoaded():
    with pytest.raises(ValueError, match="estritamente proibido"):
        load_split_dataframe("final_holdout")


def test_09_CheckpointsRemainUnchanged():
    with open(OUT_DIR / "preservation_check.json", "r", encoding="utf-8") as f:
        p = json.load(f)
    assert p["checkpoints_unchanged"] is True

    h = hashlib.sha256()
    with open(CKPT_2B34, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == EXPECTED_BASE_SHA256
    assert CKPT_2B36.exists()


def test_10_SpotMetricsRemainPreserved():
    with open(OUT_DIR / "full_validation_metrics.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["spot_ranking"]["mrr"] >= 0.76
    assert m["spot_ranking"]["top5"] >= 0.955
    assert m["spot_ranking"]["invalid_masked_selection"] == 0


def test_11_CompositeMetricsUseFullValidation():
    with open(OUT_DIR / "full_validation_metrics.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["evaluated_sequences"] == 501434


def test_12_ConfusionCountsCloseExactly():
    with open(OUT_DIR / "full_validation_metrics.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    cm = np.array(m["composite_state"]["confusion_matrix"]["matrix"], dtype=np.int64)
    assert cm.shape == (7, 7)
    assert int(cm.sum()) == 501434
    per_cls = m["composite_state"]["per_class"]
    for i, name in enumerate(STATE_NAMES):
        assert int(cm[i, :].sum()) == per_cls[name]["support"]
        assert int(cm[:, i].sum()) == per_cls[name]["predicted"]
        assert int(cm[i, i]) == per_cls[name]["tp"]
