"""Suite de Testes Direcionados do Marco 2B.3.5: Recuperacao Episodica de OBJECTIVE, RETAKE e SAVE.
16 testes cobrindo sampler episodico, congelamentos bitwise, RareStateScore, metricas e governanca.
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PATCH_DIR = (
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal"
    / "rare_class_patch_v1" / "rare_episode_patch_v1"
)
BASE_CKPT = (
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal"
    / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
)
EXPECTED_BASE_SHA256 = "c7fb36647de92b7422f8389ef4c87343680e25d1da648fef883fbc4542e91608"


@pytest.fixture(scope="module")
def input_snapshot():
    return json.loads((PATCH_DIR / "input_snapshot.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sampler_cfg():
    return json.loads((PATCH_DIR / "sampler_configuration.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def preservation():
    return json.loads((PATCH_DIR / "preservation_check.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def full_val():
    return json.loads((PATCH_DIR / "full_validation_metrics.json").read_text(encoding="utf-8"))


def test_01_EpisodeSamplerUsesUniqueEpisodes(sampler_cfg):
    for exp_key, meta in sampler_cfg["experiments"].items():
        assert meta["unique_episodes_drawn"] > 0, f"{exp_key}: sem episodios"
        assert meta["unique_demos_drawn"] >= 10, f"{exp_key}: baixa diversidade de demos"
        assert meta["unique_players_drawn"] >= 10, f"{exp_key}: baixa diversidade de jogadores"


def test_02_AdjacentWindowsAreNotDuplicated(sampler_cfg):
    for exp_key, meta in sampler_cfg["experiments"].items():
        assert meta["adjacent_window_duplications"] == 0, f"{exp_key} duplicou janelas adjacentes"
        assert meta["adjacent_window_duplication_rate"] == 0.0


def test_03_SamplingRatioIsBounded(sampler_cfg):
    for exp_key, meta in sampler_cfg["experiments"].items():
        # Nunca 50/50: fracao rara deve ser <= 0.36 (maximo alvo 1:2 = 0.333...)
        assert meta["effective_rare_fraction"] <= 0.36, (
            f"{exp_key}: fracao rara {meta['effective_rare_fraction']} > 0.36"
        )
        assert meta["effective_rare_to_common_ratio"] <= 0.56


def test_04_TestIsNeverLoaded():
    from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset
    with pytest.raises(ValueError, match="estritamente proibido"):
        CanonicalV2PositioningDataset(split="test")


def test_05_FinalHoldoutIsNeverLoaded():
    from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset
    with pytest.raises(ValueError, match="estritamente proibido"):
        CanonicalV2PositioningDataset(split="final_holdout")


def test_06_SpotRankingHeadRemainsBitwiseIdentical(preservation):
    assert preservation["spot_ranking_head_bitwise_identical"] is True
    assert preservation["hashes_before"]["head_spot"] == preservation["hashes_after"]["head_spot"]


def test_07_SectorTransitionHeadRemainsFrozen(preservation):
    assert preservation["sector_transition_head_bitwise_identical"] is True
    assert (
        preservation["hashes_before"]["head_transition_occurs"]
        == preservation["hashes_after"]["head_transition_occurs"]
    )


def test_08_NextSectorHeadRemainsFrozen(preservation):
    assert preservation["next_sector_head_bitwise_identical"] is True
    assert (
        preservation["hashes_before"]["head_next_sector"]
        == preservation["hashes_after"]["head_next_sector"]
    )


def test_09_RareStateScoreFormulaIsFrozen(input_snapshot):
    w = input_snapshot["rare_state_score_weights"]
    assert abs(sum(w.values()) - 1.0) < 1e-6
    assert w["OBJECTIVE_F1"] == 0.30
    assert w["RETAKE_F1"] == 0.25
    assert w["SAVE_F1"] == 0.20
    assert w["HOLD_F1"] == 0.10
    assert w["STAGING_F1"] == 0.10
    assert w["PositioningStateMacroF1"] == 0.05


def test_10_ObjectiveMetricsAreReported(full_val):
    obj = full_val["positioning_state"]["per_class"]["OBJECTIVE"]
    assert obj["support"] > 0
    for k in ("precision", "recall", "f1", "predicted_count", "actual_count", "fp", "fn"):
        assert k in obj


def test_11_RetakeMetricsAreReported(full_val):
    ret = full_val["positioning_state"]["per_class"]["RETAKE"]
    assert ret["support"] > 0
    for k in ("precision", "recall", "f1", "predicted_count", "actual_count", "fp", "fn"):
        assert k in ret


def test_12_SaveMetricsAreReported(full_val):
    sav = full_val["positioning_state"]["per_class"]["SAVE"]
    assert sav["support"] > 0
    for k in ("precision", "recall", "f1", "predicted_count", "actual_count", "fp", "fn"):
        assert k in sav


def test_13_PreservationGatesAreEnforced(full_val):
    gates = full_val["gates"]["preservation_gates"]
    expected_keys = {
        "sector_transition_macro_f1_ge_0_57",
        "transition_occurs_recall_ge_0_35",
        "no_transition_recall_ge_0_78",
        "next_sector_macro_f1_ge_0_48",
        "transition_macro_f1_ge_0_60",
        "spot_mrr_ge_0_76",
        "spot_top5_ge_0_955",
        "invalid_masked_eq_0",
        "spot_head_bitwise_identical",
        "frozen_heads_and_early_blocks_bitwise_identical",
    }
    assert expected_keys.issubset(set(gates.keys()))
    if not all(gates.values()):
        assert full_val["decision"] == "RARE_EPISODE_PATCH_REGRESSION"


def test_14_BaseCheckpointRemainsUnchanged():
    assert BASE_CKPT.exists()
    h = hashlib.sha256(BASE_CKPT.read_bytes()).hexdigest()
    assert h == EXPECTED_BASE_SHA256


def test_15_SelectedCheckpointIsRestorable():
    p = PATCH_DIR / "selected_checkpoint.pt"
    assert p.exists()
    sd = torch.load(p, map_location="cpu")
    assert "model_state_dict" in sd
    assert len(sd["model_state_dict"]) > 0


def test_16_ZeroSupportIsNA(full_val):
    tr_lurk = full_val["transition"]["per_class"].get("LURK")
    if tr_lurk and tr_lurk["support"] == 0:
        assert tr_lurk["precision"] == "N/A"
        assert tr_lurk["recall"] == "N/A"
        assert tr_lurk["f1"] == "N/A"
    tg_bomb = full_val["exit_trigger"]["per_class"].get("BOMB_SPOTTED")
    if tg_bomb and tg_bomb["support"] == 0:
        assert tg_bomb["precision"] == "N/A"
        assert tg_bomb["recall"] == "N/A"
        assert tg_bomb["f1"] == "N/A"
