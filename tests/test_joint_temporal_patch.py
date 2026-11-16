"""
Suite de Testes Direcionados do Marco 2B.3.4: Ajuste Multitarefa Conjunto das Heads Temporais Raras.
16 testes cobrindo congelamento seletivo, amostragem, consistência, proveniência e governança.
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

PATCH_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1"
BASE_PATCH_CKPT = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "selected_patch_checkpoint.pt"
ROOT_CANDIDATE_CKPT = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training" / "selected_candidate.pt"

@pytest.fixture(scope="module")
def input_snapshot():
    p = PATCH_DIR / "input_snapshot.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def frozen_score():
    p = PATCH_DIR / "frozen_temporal_score.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def preservation_data():
    p = PATCH_DIR / "preservation_check.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def comparison_data():
    p = PATCH_DIR / "experiment_comparison.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def selected_thresholds():
    p = PATCH_DIR / "selected_thresholds.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def full_val_metrics():
    p = PATCH_DIR / "full_validation_metrics.json"
    assert p.exists(), f"Arquivo inexistente: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# 1. SpotRankingHeadIsBitwiseFrozen
def test_01_SpotRankingHeadIsBitwiseFrozen(preservation_data):
    assert preservation_data["spot_ranking_head_bitwise_identical"] is True
    before = preservation_data["hashes_before"]["head_spot"]
    after = preservation_data["hashes_after"]["head_spot"]
    assert before == after

# 2. EarlyTemporalBlocksRemainFrozen
def test_02_EarlyTemporalBlocksRemainFrozen(preservation_data):
    assert preservation_data["early_blocks_bitwise_identical"] is True
    assert preservation_data["hashes_before"]["transformer_layer_0"] == preservation_data["hashes_after"]["transformer_layer_0"]
    assert preservation_data["hashes_before"]["transformer_layer_1"] == preservation_data["hashes_after"]["transformer_layer_1"]
    assert preservation_data["hashes_before"]["player_proj"] == preservation_data["hashes_after"]["player_proj"]
    assert preservation_data["hashes_before"]["teammate_proj"] == preservation_data["hashes_after"]["teammate_proj"]

# 3. LastTemporalBlockReceivesGradient
def test_03_LastTemporalBlockReceivesGradient(preservation_data):
    assert preservation_data["last_block_received_gradient"] is True
    assert preservation_data["hashes_before"]["transformer_layer_2"] != preservation_data["hashes_after"]["transformer_layer_2"]

# 4. TestIsNeverLoaded
def test_04_TestIsNeverLoaded():
    from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset
    with pytest.raises(ValueError, match="estritamente proibido"):
        CanonicalV2PositioningDataset(split="test")

# 5. FinalHoldoutIsNeverLoaded
def test_05_FinalHoldoutIsNeverLoaded():
    from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset
    with pytest.raises(ValueError, match="estritamente proibido"):
        CanonicalV2PositioningDataset(split="final_holdout")

# 6. SamplingRatioIsModerate
def test_06_SamplingRatioIsModerate(comparison_data):
    ratio_b = comparison_data["experiments"]["experiment_b"]["effective_sampling_ratio"]
    ratio_c = comparison_data["experiments"]["experiment_c"]["effective_sampling_ratio"]
    assert ratio_b <= 0.40, f"Ratio {ratio_b} > 0.40"
    assert ratio_c <= 0.40, f"Ratio {ratio_c} > 0.40"

# 7. NoAdjacentWindowDuplication
def test_07_NoAdjacentWindowDuplication(comparison_data):
    duplication_rate = comparison_data["sampling"]["adjacent_window_duplication_rate"]
    assert duplication_rate == 0.0

# 8. ClassWeightsAreClamped
def test_08_ClassWeightsAreClamped(comparison_data):
    weights = comparison_data["loss_config"]["clamped_weights"]
    for head_name, w_list in weights.items():
        for w in w_list:
            assert 0.1 <= w <= 10.0, f"Peso {w} fora do range clampado para {head_name}"

# 9. ConsistencyLossIsFinite
def test_09_ConsistencyLossIsFinite(comparison_data):
    exp_c_loss = comparison_data["experiments"]["experiment_c"]["final_loss"]["consistency_loss"]
    assert np.isfinite(exp_c_loss)
    assert exp_c_loss >= 0.0

# 10. NoTransitionMasksNextSector
def test_10_NoTransitionMasksNextSector():
    # Verifica invariante contratual do dataloader: se sector_transition_occurs == 0, next_sector_loss_mask == 0
    from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset
    ds = CanonicalV2PositioningDataset(split="validation", max_samples=500, seed=42028)
    no_trans_indices = np.where(ds.trans_occurs_vals == 0)[0]
    if len(no_trans_indices) > 0:
        assert np.all(ds.next_sec_mask_vals[no_trans_indices] == 0.0)

# 11. ObjectiveUsesRealEvidence
def test_11_ObjectiveUsesRealEvidence(full_val_metrics):
    obj_sup = full_val_metrics["positioning_state"]["per_class"]["OBJECTIVE"]["support"]
    assert obj_sup > 0
    assert full_val_metrics["positioning_state"]["per_class"]["OBJECTIVE"]["precision"] != "N/A"

# 12. SupportedRareClassesAreReported
def test_12_SupportedRareClassesAreReported(full_val_metrics):
    st_classes = full_val_metrics["positioning_state"]["per_class"]
    for c in ["HOLD", "OBJECTIVE", "STAGING", "RETAKE", "SAVE"]:
        assert c in st_classes
        assert st_classes[c]["support"] > 0
        assert "recall" in st_classes[c]

# 13. ZeroSupportIsNA
def test_13_ZeroSupportIsNA(full_val_metrics):
    tr_classes = full_val_metrics["transition"]["per_class"]
    if "LURK" in tr_classes and tr_classes["LURK"]["support"] == 0:
        assert tr_classes["LURK"]["recall"] == "N/A"
        assert tr_classes["LURK"]["f1"] == "N/A"

# 14. TemporalScoreFormulaIsFrozen
def test_14_TemporalScoreFormulaIsFrozen(frozen_score):
    weights = frozen_score["weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-6
    assert weights["state_macro_f1"] == 0.20
    assert weights["sector_transition_macro_f1"] == 0.20
    assert weights["next_sector_macro_f1"] == 0.15
    assert weights["transition_macro_f1"] == 0.20
    assert weights["exit_trigger_macro_f1"] == 0.15
    assert weights["rare_state_recall_mean"] == 0.10

# 15. BaseCheckpointsRemainUnchanged
def test_15_BaseCheckpointsRemainUnchanged():
    assert BASE_PATCH_CKPT.exists()
    h_patch = hashlib.sha256(BASE_PATCH_CKPT.read_bytes()).hexdigest()
    assert h_patch == "e0a1c5d5d9727e4986d647fb3fcd2a164de269642c078c850c6667bb55fd9e03"

    assert ROOT_CANDIDATE_CKPT.exists()
    h_root = hashlib.sha256(ROOT_CANDIDATE_CKPT.read_bytes()).hexdigest()
    assert h_root == "4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352"

# 16. SelectedCheckpointIsRestorable
def test_16_SelectedCheckpointIsRestorable():
    p = PATCH_DIR / "selected_checkpoint.pt"
    assert p.exists()
    sd = torch.load(p, map_location="cpu")
    assert "model_state_dict" in sd
    assert len(sd["model_state_dict"]) > 0
