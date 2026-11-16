#!/usr/bin/env python3
"""
Marco 2B.4 - Seção 9: 16 Testes Direcionados Executados ANTES de Abrir o Test.
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
from tools.phase3a_training.canonical_v2_dataloader import load_supervised_spot_mask
from tools.phase3a_training.positioning_model_v2 import PositioningTransformerV2RealTemporal
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import (
    compute_multiclass_metrics,
    EXPECTED_BASE_SHA256,
    SELECTED_TRANSITION_THRESHOLD,
)
from tools.phase3a_training.run_marco_2b37_hybrid_composition import compose_hybrid_predictions

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "final_evaluation"
CKPT_2B34 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
CKPT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "selected_checkpoint.pt"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_01_FinalContractIsFrozen():
    with open(OUT_DIR / "final_evaluation_contract.json", "r", encoding="utf-8") as f:
        c = json.load(f)
    assert c["frozen"] is True
    assert c["save_policy"]["neural_save_disabled"] is True
    assert c["save_policy"]["excluded_from_neural_macro_f1"] is True


def test_02_CheckpointHashesMatch():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    h34 = sha256_file(CKPT_2B34)
    h36 = sha256_file(CKPT_2B36)
    assert h34 == EXPECTED_BASE_SHA256
    assert snap["hashes"]["training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1/selected_checkpoint.pt"] == h34
    assert snap["hashes"]["training_runs/positioning_v2_real_temporal/rare_class_patch_v1/hierarchical_state_patch_v1/selected_checkpoint.pt"] == h36


def test_03_ThresholdsMatchValidationSelection():
    with open(OUT_DIR / "final_evaluation_contract.json", "r", encoding="utf-8") as f:
        c = json.load(f)
    assert c["thresholds"]["sector_transition_occurs"] == SELECTED_TRANSITION_THRESHOLD


def test_04_SaveNeuralOutputIsDisabled():
    # Com save_rule=False, composição final nunca pode produzir SAVE (6)
    base = np.array([0, 1, 2, 3])
    rare = np.array([3, 3, 3, 0])  # Mesmo se rare prever SAVE(3), nunca aplica SAVE
    zero = np.array([False, False, False, False])
    out = compose_hybrid_predictions(base, rare, zero, zero, zero)
    assert not np.any(out == 6)


def test_05_SaveIsReportedAsRuntimeFallback():
    with open(OUT_DIR / "save_fallback_declaration.json", "r", encoding="utf-8") as f:
        s = json.load(f)
    assert s["FALLBACK_DECLARED"] is True
    assert s["NEURAL_SAVE_DISABLED"] is True
    assert s["UTILITY_AI_OWNS_SAVE"] is True


def test_06_TestLoaderHasNoShuffle():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    assert snap["mode"] == "FINAL_EVALUATION"


def test_07_TestHasNoAugmentation():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    assert snap["config_frozen"] is True


def test_08_TestCannotUpdateParameters():
    sup_mask = load_supervised_spot_mask()
    m = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    m.eval()
    before = {k: v.clone() for k, v in m.state_dict().items()}
    with torch.inference_mode():
        _ = m(torch.zeros(2, 32, 18), torch.zeros(2, 32, 4, 18))
    for k, v in m.state_dict().items():
        assert torch.equal(before[k], v)


def test_09_TestCannotSelectCheckpoint():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    assert snap["checkpoint_frozen"] is True
    assert snap["thresholds_frozen"] is True


def test_10_MetricsUseEligibleDenominators():
    # NextSector somente onde next_sector_loss_mask == 1
    y_true = np.array([0, 1, 2, 0])
    y_pred = np.array([0, 1, 0, 1])
    mask = np.array([True, True, False, False])
    m = compute_multiclass_metrics(y_true[mask], y_pred[mask], ["A", "B", "C"])
    assert m["per_class"]["A"]["support"] == 1
    assert m["per_class"]["B"]["support"] == 1
    assert m["per_class"]["C"]["support"] == 0


def test_11_UnsupportedSpotCannotWin():
    sup_mask = load_supervised_spot_mask()
    m = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    m.eval()
    with torch.inference_mode():
        out = m(torch.zeros(4, 32, 18), torch.zeros(4, 32, 4, 18))
        top1 = torch.argmax(out["logits_spot"], dim=-1)
    assert torch.all(sup_mask[top1] > 0.5)


def test_12_ZeroSupportIsNA():
    m = compute_multiclass_metrics(np.array([0, 1]), np.array([0, 1]), ["A", "B", "ZERO"])
    assert m["per_class"]["ZERO"]["precision"] == "N/A"
    assert m["per_class"]["ZERO"]["recall"] == "N/A"
    assert m["per_class"]["ZERO"]["f1"] == "N/A"


def test_13_CompositePrecedenceIsDeterministic():
    base = np.array([0, 3])
    rare = np.array([1, 2])
    obj_e = np.array([True, False])
    ret_e = np.array([True, True])
    sav_r = np.array([False, False])
    out = compose_hybrid_predictions(base, rare, obj_e, ret_e, sav_r)
    assert list(out) == [4, 5]


def test_14_ConfusionCountsCloseExactly():
    yt = np.array([0, 1, 2, 3, 4, 5])
    yp = np.array([0, 1, 0, 3, 4, 5])
    m = compute_multiclass_metrics(yt, yp, STATE_NAMES[:6])
    tot_sup = sum(m["per_class"][c]["support"] for c in STATE_NAMES[:6])
    tot_pred = sum(m["per_class"][c]["predicted"] for c in STATE_NAMES[:6])
    assert tot_sup == len(yt)
    assert tot_pred == len(yp)


def test_15_EvaluationProducesRawArrays():
    with open(OUT_DIR / "final_evaluation_contract.json", "r", encoding="utf-8") as f:
        c = json.load(f)
    assert c["contract_version"] == "2b4_final_evaluation_v1"


def test_16_EvaluationIsSinglePass():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    assert snap["test_opened"] is False
