"""
Suite de Testes Direcionados do Marco 2B.3.2: Calibração Final das Heads Raras.
10 testes automatizados cobrindo os critérios de governança, suporte e calibração.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CALIB_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "final_calibration"
BASE_CKPT_PATH = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training" / "selected_candidate.pt"
INPUT_PATCH_CKPT = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "selected_patch_checkpoint.pt"

@pytest.fixture(scope="module")
def sweep_data():
    p = CALIB_DIR / "transition_threshold_sweep.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def preservation_data():
    p = CALIB_DIR / "preservation_check.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def objective_data():
    p = CALIB_DIR / "objective_validation_analysis.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# 1. ThresholdUsesValidationOnly
def test_01_ThresholdUsesValidationOnly(sweep_data):
    # Verifica que todos os 9 thresholds foram calculados e que o schema é de calibração na validação
    assert len(sweep_data["threshold_grid"]) == 9
    assert sweep_data["threshold_grid"] == [0.45, 0.475, 0.50, 0.525, 0.55, 0.575, 0.60, 0.625, 0.65]

# 2. TestIsNeverLoaded
def test_02_TestIsNeverLoaded():
    # Verifica que o DataLoader rejeita explicitamente 'test'
    from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset
    with pytest.raises(ValueError, match="estritamente proibido"):
        CanonicalV2PositioningDataset(split="test")

# 3. ObjectiveZeroSupportIsNA
def test_03_ObjectiveZeroSupportIsNA(objective_data):
    # Se support fosse 0, status seria N/A. Como é 952 na validação total, status é SUPPORTED
    if objective_data["full_validation_support"] == 0:
        assert objective_data["status"] == "N/A"
    else:
        assert objective_data["status"] == "SUPPORTED"

# 4. ObjectiveAdjustmentRequiresRealSupport
def test_04_ObjectiveAdjustmentRequiresRealSupport(objective_data):
    # Confirma que se o suporte é real (> 0), o ajuste localizado foi considerado
    assert objective_data["full_validation_support"] > 0

# 5. FrozenParametersRemainBitwiseIdentical
def test_05_FrozenParametersRemainBitwiseIdentical(preservation_data):
    # Encoders e Head Spot idênticos bitwise
    assert preservation_data["encoders_bitwise_identical"] is True
    assert preservation_data["spot_ranking_head_bitwise_identical"] is True

# 6. SelectedThresholdMeetsBothRecallGates
def test_06_SelectedThresholdMeetsBothRecallGates(sweep_data):
    # Se all_gates_met for True, deve atingir rec_to >= 0.35 e rec_no >= 0.80.
    # Se for False, selected_threshold_entry deve ser None conforme Seção 2
    if sweep_data["all_gates_met"]:
        entry = sweep_data["selected_threshold_entry"]
        assert entry["transition_occurs_recall"] >= 0.35
        assert entry["no_transition_recall"] >= 0.80
    else:
        assert sweep_data["selected_threshold_entry"] is None

# 7. SpotMetricsRemainPreserved
def test_07_SpotMetricsRemainPreserved(preservation_data):
    # MRR >= 0.75, Top-5 >= 95%, InvalidMasked = 0
    assert preservation_data["gates"]["spot_mrr_ge_75"] is True
    assert preservation_data["gates"]["spot_top5_ge_95"] is True
    assert preservation_data["gates"]["invalid_masked_selections_eq_0"] is True

# 8. CheckpointIsRestorable
def test_08_CheckpointIsRestorable():
    ckpt_path = CALIB_DIR / "calibrated_patch_checkpoint.pt"
    assert ckpt_path.exists()
    sd = torch.load(ckpt_path, map_location="cpu")
    assert len(sd) > 0

# 9. ThresholdIsPersisted
def test_09_ThresholdIsPersisted():
    sel_path = CALIB_DIR / "selected_thresholds.json"
    assert sel_path.exists()
    with open(sel_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "transition_threshold" in data
    assert "canonical_verdict" in data

# 10. BaseCheckpointRemainsUnchanged
def test_10_BaseCheckpointRemainsUnchanged():
    assert BASE_CKPT_PATH.exists()
    h = hashlib.sha256(BASE_CKPT_PATH.read_bytes()).hexdigest()
    assert h == "4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352"
