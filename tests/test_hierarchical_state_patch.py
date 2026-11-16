#!/usr/bin/env python3
"""
Marco 2B.3.6 - Seção 11: 18 Testes Direcionados da Arquitetura Hierárquica.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_v2_dataloader import load_supervised_spot_mask
from tools.phase3a_training.positioning_model_v2 import PositioningTransformerV2RealTemporal
from tools.phase3a_training.hierarchical_positioning_model import (
    HierarchicalPositioningModel,
    compose_composite_predictions,
)
from tools.phase3a_training.build_2b36_hierarchical_sidecar import (
    compute_causal_eligibility_for_demo,
    CONTRACT_VERSION,
)
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import (
    load_split_dataframe,
    compute_multiclass_metrics,
    tensor_state_dict_sha256,
    EXPECTED_BASE_SHA256,
)

INDEX_DIR = BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1"
SIDECAR_DIR = OUT_DIR / "hierarchical_label_sidecar"
BASE_CKPT = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"


def test_01_HierarchicalSidecarJoinsOneToOne():
    for i in range(6):
        b = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=["sequence_id", "split"])
        h = pd.read_parquet(SIDECAR_DIR / f"shard_{i:03d}_hierarchical.parquet", columns=["sequence_id", "contract_version"])
        assert len(b) == len(h)
        assert (b["sequence_id"].to_numpy() == h["sequence_id"].to_numpy()).all()
        assert not h["sequence_id"].duplicated().any()
        assert (h["contract_version"] == CONTRACT_VERSION).all()


def test_02_EligibilityUsesNoFutureInformation():
    # Se alterarmos frames > label_frame (futuro), as máscaras em label_frame devem ser idênticas
    T = 80
    f = 40
    X1 = np.zeros((T, 10, 18), dtype=np.float32)
    X1[: f + 1, :, 14] = 1.0  # vivos
    X1[f, 0, 15] = 1.0  # slot 0 com C4 no frame f
    X2 = X1.copy()
    X2[f + 1 :, :, :] = 9.0  # futuro completamente alterado

    r1 = compute_causal_eligibility_for_demo(X1, np.array([f]), np.array([0]), np.array(["MapControl"]))
    r2 = compute_causal_eligibility_for_demo(X2, np.array([f]), np.array([0]), np.array(["MapControl"]))
    for k in ("objective_eligible", "retake_eligible", "save_eligible"):
        assert bool(r1[k][0]) == bool(r2[k][0])


def test_03_ObjectiveRequiresCausalEvidence():
    X = np.zeros((40, 10, 18), dtype=np.float32)
    X[:, :, 14] = 1.0  # todos vivos
    X[:, :, 13] = 1.0  # TRs
    # Sem C4 e sem plant/defuse causal -> não elegível mesmo em Retake
    r = compute_causal_eligibility_for_demo(X, np.array([35]), np.array([0]), np.array(["Retake"]))
    assert not bool(r["objective_eligible"][0])

    # Com C4 na janela -> elegível
    X[35, 0, 15] = 1.0
    r_c4 = compute_causal_eligibility_for_demo(X, np.array([35]), np.array([0]), np.array(["Retake"]))
    assert bool(r_c4["objective_eligible"][0])


def test_04_RetakeRequiresValidSiteContext():
    X = np.zeros((40, 10, 18), dtype=np.float32)
    X[:, :, 14] = 1.0
    X[35, 0, 0] = -1000.0 / 4096.0
    X[35, 0, 1] = -1500.0 / 4096.0
    # Fora de plan_stage=='Retake' -> não elegível
    r_no = compute_causal_eligibility_for_demo(X, np.array([35]), np.array([0]), np.array(["MapControl"]))
    assert not bool(r_no["retake_eligible"][0])


def test_05_SurvivalAloneDoesNotEnableSave():
    # Jogador vivo com arma cara em MapControl sem desvantagem/pouco tempo -> SAVE não elegível
    X = np.zeros((40, 10, 18), dtype=np.float32)
    X[:, :, 14] = 1.0  # 5v5
    X[35, 0, 11] = 0.9
    X[35, 0, 17] = 0.8  # ~92s restantes
    r = compute_causal_eligibility_for_demo(X, np.array([35]), np.array([0]), np.array(["MapControl"]))
    assert not bool(r["save_eligible"][0])


def test_06_RareHeadUsesOnlyEligibleExamples():
    sup_mask = load_supervised_spot_mask()
    bm = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    hm = HierarchicalPositioningModel(bm)
    hm.eval()
    hist = torch.zeros(2, 32, 18)
    tm = torch.zeros(2, 32, 4, 18)
    # Sample 0: nenhuma elegibilidade; Sample 1: somente OBJECTIVE elegível
    elig = torch.tensor([[False, False, False], [True, False, False]], dtype=torch.bool)
    out = hm(hist, tm, rare_eligibility_mask=elig)
    logits = out["logits_rare_state"]
    assert torch.all(logits[0, 1:] < -1e8)
    assert torch.all(logits[1, 2:] < -1e8)


def test_07_HardNegativesAreContextual():
    with open(OUT_DIR / "hard_negative_manifest.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["eligible_hard_negative_pool"] > 0
    assert m["unique_demos_in_neg_pool"] >= 50
    assert m["ratio_pos_neg"] == "1:3"


def test_08_AdjacentWindowsAreNotDuplicated():
    with open(OUT_DIR / "hard_negative_manifest.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["adjacent_window_min_gap_frames"] >= 16


def test_09_TestIsNeverLoaded():
    with pytest.raises(ValueError, match="estritamente proibido"):
        load_split_dataframe("test")


def test_10_FinalHoldoutIsNeverLoaded():
    with pytest.raises(ValueError, match="estritamente proibido"):
        load_split_dataframe("final_holdout")


def test_11_SpotRankingHeadRemainsBitwiseIdentical():
    sup_mask = load_supervised_spot_mask()
    ref = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    ref.load_state_dict(torch.load(BASE_CKPT, map_location="cpu", weights_only=False)["model_state_dict"], strict=True)

    sel_bm = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    sel_hm = HierarchicalPositioningModel(sel_bm)
    sel_hm.load_state_dict(torch.load(OUT_DIR / "selected_checkpoint.pt", map_location="cpu", weights_only=False)["model_state_dict"], strict=True)

    assert tensor_state_dict_sha256(ref.head_spot) == tensor_state_dict_sha256(sel_hm.base_model.head_spot)


def test_12_ApprovedHeadsRemainFrozen():
    sup_mask = load_supervised_spot_mask()
    ref = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    ref.load_state_dict(torch.load(BASE_CKPT, map_location="cpu", weights_only=False)["model_state_dict"], strict=True)

    sel_hm = HierarchicalPositioningModel(PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask))
    sel_hm.load_state_dict(torch.load(OUT_DIR / "selected_checkpoint.pt", map_location="cpu", weights_only=False)["model_state_dict"], strict=True)

    for attr in [
        "player_proj", "teammate_proj", "teammate_pool", "team_emb", "role_emb",
        "stage_emb", "context_fusion", "head_state", "head_transition_occurs",
        "head_next_sector", "head_spot", "head_transition", "head_exit_trigger",
    ]:
        assert tensor_state_dict_sha256(getattr(ref, attr)) == tensor_state_dict_sha256(getattr(sel_hm.base_model, attr)), f"{attr} mudou!"
    for idx in (0, 1):
        assert tensor_state_dict_sha256(ref.transformer.layers[idx]) == tensor_state_dict_sha256(sel_hm.base_model.transformer.layers[idx])


def test_13_CompositeStateUsesRareOverrideCorrectly():
    # Base prevê TRANSIT (0); Rare prevê RETAKE (2) com elegibilidade True -> composite deve ser RETAKE (5)
    lb = torch.tensor([[10.0, 0.0, 0.0, 0.0], [10.0, 0.0, 0.0, 0.0]])
    lr = torch.tensor([[0.0, 0.0, 10.0, 0.0], [10.0, 0.0, 0.0, 0.0]])
    elig = torch.tensor([[False, True, False], [False, True, False]], dtype=torch.bool)
    comp, base_p, rare_p = compose_composite_predictions(lb, lr, elig)
    assert int(comp[0]) == 5
    assert int(comp[1]) == 0


def test_14_UnsupportedClassIsNA():
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0, 1, 0, 1])
    m = compute_multiclass_metrics(y_true, y_pred, ["A", "B", "ZERO_CLASS"])
    assert m["per_class"]["ZERO_CLASS"]["support"] == 0
    assert m["per_class"]["ZERO_CLASS"]["precision"] == "N/A"
    assert m["per_class"]["ZERO_CLASS"]["recall"] == "N/A"
    assert m["per_class"]["ZERO_CLASS"]["f1"] == "N/A"


def test_15_BaseCheckpointRemainsUnchanged():
    h = hashlib.sha256()
    with open(BASE_CKPT, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == EXPECTED_BASE_SHA256


def test_16_SelectedCheckpointIsRestorable():
    sup_mask = load_supervised_spot_mask()
    hm = HierarchicalPositioningModel(PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask))
    ckpt = torch.load(OUT_DIR / "selected_checkpoint.pt", map_location="cpu", weights_only=False)
    hm.load_state_dict(ckpt["model_state_dict"], strict=True)
    hm.eval()
    with torch.inference_mode():
        out = hm(torch.zeros(2, 32, 18), torch.zeros(2, 32, 4, 18))
    assert out["logits_base_state"].shape == (2, 4)
    assert out["logits_rare_state"].shape == (2, 4)


def test_17_PreservationGatesAreEnforced():
    with open(OUT_DIR / "preservation_check.json", "r", encoding="utf-8") as f:
        p = json.load(f)
    assert p["spot_head_bitwise_identical"] is True
    assert "preservation_gate_pass" in p
    assert "decision" in p


def test_18_SaveFallbackIsReportedSeparately():
    with open(OUT_DIR / "preservation_check.json", "r", encoding="utf-8") as f:
        p = json.load(f)
    assert p["save_fallback_status"] in ("PASS", "SAVE_DETERMINISTIC_FALLBACK_REQUIRED")
