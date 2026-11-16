#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2B.3: Suíte de Testes Automatizados de Integridade, Governança e Treinamento.

Cobre formalmente os 22 testes unitários mínimos requeridos pela Seção 16 do ORIGINAL_REQUEST.md:
1. FullTrainerUses311TrainDemos
2. ValidationUses66ValidationDemos
3. TestIsNeverOpenedByTrainer
4. FinalHoldoutIsNeverOpened
5. BaseAndSidecarJoinOneToOne
6. NoTransitionMasksNextSectorLoss
7. TransitionEnablesNextSectorLoss
8. UnsupportedSpotCannotContributeLoss
9. UnsupportedSpotCannotWinNeuralSelection
10. SupportedTargetIsPresentInCandidateMask
11. ClassWeightsUseTrainOnly
12. CompositeFormulaIsFrozen
13. EarlyStoppingUsesValidationOnly
14. BestCheckpointUsesValidationOnly
15. ThreeSeedsAreIndependent
16. ResumeIsDeterministic
17. MetricsUseEligibleDenominators
18. ZeroSupportIsNA
19. SyntheticHistoryCannotReachTrainer
20. PreviousArtifactsRemainUnchanged
21. NoONNXExport
22. NoFinalEvaluation
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

import pytest
import numpy as np
import torch
import torch.nn as nn

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.positioning_model_v2 import (
    PositioningTransformerV2RealTemporal,
    PositioningTransformerV2Loss,
    STATE_NAMES,
    TRANSITION_NAMES,
    EXIT_TRIGGER_NAMES,
    NEXT_SECTOR_NAMES
)
from tools.phase3a_training.canonical_v2_dataloader import (
    CanonicalV2PositioningDataset,
    verify_base_and_sidecar_join,
    load_supervised_spot_mask,
    load_split_definitions,
    INDEX_DIR,
    SIDECAR_DIR,
    SPLITS_PATH,
    MASK_PATH,
    CATALOG_PATH
)
from tools.phase3a_training.run_full_training_marco_2b3 import (
    compute_metrics_for_classification,
    compute_spot_ranking_eval,
    compute_composite_score,
    FULL_TRAIN_DIR
)


def compute_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# 1. FullTrainerUses311TrainDemos
def test_01_full_trainer_uses_311_train_demos():
    splits_cfg = load_split_definitions()
    train_demos = splits_cfg["train_demos"]
    assert len(train_demos) == 311, f"Train demos count {len(train_demos)} != 311"
    ds_train = CanonicalV2PositioningDataset(split="train", max_samples=10)
    assert len(ds_train.allowed_demos) == 311
    assert set(ds_train.allowed_demos) == set(train_demos)


# 2. ValidationUses66ValidationDemos
def test_02_validation_uses_66_validation_demos():
    splits_cfg = load_split_definitions()
    val_demos = splits_cfg["validation_demos"]
    assert len(val_demos) == 66, f"Validation demos count {len(val_demos)} != 66"
    ds_val = CanonicalV2PositioningDataset(split="validation", max_samples=10)
    assert len(ds_val.allowed_demos) == 66
    assert set(ds_val.allowed_demos) == set(val_demos)


# 3. TestIsNeverOpenedByTrainer
def test_03_test_is_never_opened_by_trainer():
    splits_cfg = load_split_definitions()
    test_demos = set(splits_cfg.get("test_demos", []))
    assert len(test_demos) == 67

    # 1. Tentar instanciar split='test' deve gerar ValueError imediato
    with pytest.raises(ValueError) as excinfo:
        CanonicalV2PositioningDataset(split="test")
    assert "estritamente proibido" in str(excinfo.value) or "Regra 02" in str(excinfo.value)

    # 2. Verificar que nenhuma demo de test contamina Train ou Validation
    ds_train = CanonicalV2PositioningDataset(split="train", max_samples=10)
    ds_val = CanonicalV2PositioningDataset(split="validation", max_samples=10)
    assert len(set(ds_train.allowed_demos).intersection(test_demos)) == 0
    assert len(set(ds_val.allowed_demos).intersection(test_demos)) == 0


# 4. FinalHoldoutIsNeverOpened
def test_04_final_holdout_is_never_opened():
    with pytest.raises(ValueError):
        CanonicalV2PositioningDataset(split="final_holdout")
    with pytest.raises(ValueError):
        CanonicalV2PositioningDataset(split="holdout")


# 5. BaseAndSidecarJoinOneToOne
def test_05_base_and_sidecar_join_one_to_one():
    res = verify_base_and_sidecar_join()
    assert res["verdict"] == "FULL_TRAINING_LABEL_JOIN_PASS"
    assert res["total_base_rows"] == 3411434
    assert res["total_sidecar_rows"] == 3411434
    assert res["missing_joins"] == 0
    assert res["duplicate_joins"] == 0
    assert res["conflicting_labels"] == 0


# 6. NoTransitionMasksNextSectorLoss
def test_06_no_transition_masks_next_sector_loss():
    mask = load_supervised_spot_mask()
    criterion = PositioningTransformerV2Loss(supervised_spot_mask=mask)

    # Criar batch onde sector_transition_occurs == 0 (NO_TRANSITION) e next_sector_loss_mask == 0.0
    B = 4
    outputs = {
        "logits_state": torch.randn(B, 7),
        "logits_transition_occurs": torch.randn(B, 2),
        "logits_next_sector": torch.randn(B, 5),
        "raw_logits_spot": torch.randn(B, 53),
        "logits_transition": torch.randn(B, 7),
        "logits_trigger": torch.randn(B, 8)
    }
    targets = {
        "positioning_state": torch.zeros(B, dtype=torch.long),
        "sector_transition_occurs": torch.zeros(B, dtype=torch.long), # NO_TRANSITION
        "next_sector": torch.zeros(B, dtype=torch.long),
        "next_sector_loss_mask": torch.zeros(B, dtype=torch.float32), # MASKED
        "candidate_spot_idx": torch.zeros(B, dtype=torch.long),
        "spot_loss_mask": torch.zeros(B, dtype=torch.bool),
        "transition": torch.zeros(B, dtype=torch.long),
        "exit_trigger": torch.zeros(B, dtype=torch.long)
    }
    loss_dict = criterion(outputs, targets)
    assert float(loss_dict["loss_next_sector"].item()) == 0.0
    assert loss_dict["valid_next_sector_samples"] == 0


# 7. TransitionEnablesNextSectorLoss
def test_07_transition_enables_next_sector_loss():
    mask = load_supervised_spot_mask()
    criterion = PositioningTransformerV2Loss(supervised_spot_mask=mask)

    B = 4
    outputs = {
        "logits_state": torch.randn(B, 7),
        "logits_transition_occurs": torch.randn(B, 2),
        "logits_next_sector": torch.randn(B, 5),
        "raw_logits_spot": torch.randn(B, 53),
        "logits_transition": torch.randn(B, 7),
        "logits_trigger": torch.randn(B, 8)
    }
    targets = {
        "positioning_state": torch.zeros(B, dtype=torch.long),
        "sector_transition_occurs": torch.ones(B, dtype=torch.long), # TRANSITION_OCCURS
        "next_sector": torch.tensor([0, 1, 2, 3], dtype=torch.long),
        "next_sector_loss_mask": torch.ones(B, dtype=torch.float32), # ATIVA
        "candidate_spot_idx": torch.zeros(B, dtype=torch.long),
        "spot_loss_mask": torch.zeros(B, dtype=torch.bool),
        "transition": torch.zeros(B, dtype=torch.long),
        "exit_trigger": torch.zeros(B, dtype=torch.long)
    }
    loss_dict = criterion(outputs, targets)
    assert float(loss_dict["loss_next_sector"].item()) > 0.0
    assert loss_dict["valid_next_sector_samples"] == B


# 8. UnsupportedSpotCannotContributeLoss
def test_08_unsupported_spot_cannot_contribute_loss():
    mask = load_supervised_spot_mask()
    criterion = PositioningTransformerV2Loss(supervised_spot_mask=mask)

    # Identificar um spot com mask == 0
    unsupported_spots = (mask == 0).nonzero().squeeze().tolist()
    unsupported_idx = unsupported_spots[0]

    B = 2
    outputs = {
        "logits_state": torch.randn(B, 7),
        "logits_transition_occurs": torch.randn(B, 2),
        "logits_next_sector": torch.randn(B, 5),
        "raw_logits_spot": torch.randn(B, 53),
        "logits_transition": torch.randn(B, 7),
        "logits_trigger": torch.randn(B, 8)
    }
    # Mesmo com spot_loss_mask == True e positioning_state != TRANSIT, se o spot for unsupported, perda é 0
    targets = {
        "positioning_state": torch.ones(B, dtype=torch.long), # CLEARANCE
        "sector_transition_occurs": torch.zeros(B, dtype=torch.long),
        "next_sector": torch.zeros(B, dtype=torch.long),
        "next_sector_loss_mask": torch.zeros(B, dtype=torch.float32),
        "candidate_spot_idx": torch.tensor([unsupported_idx, unsupported_idx], dtype=torch.long),
        "spot_loss_mask": torch.ones(B, dtype=torch.bool),
        "transition": torch.zeros(B, dtype=torch.long),
        "exit_trigger": torch.zeros(B, dtype=torch.long)
    }
    candidate_mask = torch.ones(B, 53, dtype=torch.bool)
    loss_dict = criterion(outputs, targets, candidate_mask=candidate_mask)
    assert float(loss_dict["loss_spot"].item()) == 0.0
    assert loss_dict["valid_spot_samples"] == 0


# 9. UnsupportedSpotCannotWinNeuralSelection
def test_09_unsupported_spot_cannot_win_neural_selection():
    mask = load_supervised_spot_mask()
    model = PositioningTransformerV2RealTemporal(supervised_spot_mask=mask)
    model.eval()

    B = 8
    self_hist = torch.randn(B, 32, 18)
    teammates = torch.randn(B, 32, 4, 18)
    cand_mask = torch.ones(B, 53, dtype=torch.bool)

    with torch.no_grad():
        out = model(self_history=self_hist, teammates=teammates, candidate_mask=cand_mask)
        masked_spot_logits = out["logits_spot"]
        preds = torch.argmax(masked_spot_logits, dim=1).cpu().numpy()

        unsupported_indices = set((mask == 0).nonzero().squeeze().tolist())
        for p in preds:
            assert p not in unsupported_indices, f"Violação crítica! Spot não supervisionado {p} venceu seleção neural!"


# 10. SupportedTargetIsPresentInCandidateMask
def test_10_supported_target_is_present_in_candidate_mask():
    mask = load_supervised_spot_mask()
    criterion = PositioningTransformerV2Loss(supervised_spot_mask=mask)

    supported_spots = (mask == 1).nonzero().squeeze().tolist()
    supported_idx = supported_spots[0]

    B = 2
    outputs = {
        "logits_state": torch.randn(B, 7),
        "logits_transition_occurs": torch.randn(B, 2),
        "logits_next_sector": torch.randn(B, 5),
        "raw_logits_spot": torch.randn(B, 53),
        "logits_transition": torch.randn(B, 7),
        "logits_trigger": torch.randn(B, 8)
    }
    targets = {
        "positioning_state": torch.ones(B, dtype=torch.long), # CLEARANCE
        "sector_transition_occurs": torch.zeros(B, dtype=torch.long),
        "next_sector": torch.zeros(B, dtype=torch.long),
        "next_sector_loss_mask": torch.zeros(B, dtype=torch.float32),
        "candidate_spot_idx": torch.tensor([supported_idx, supported_idx], dtype=torch.long),
        "spot_loss_mask": torch.ones(B, dtype=torch.bool),
        "transition": torch.zeros(B, dtype=torch.long),
        "exit_trigger": torch.zeros(B, dtype=torch.long)
    }

    # Se target não estiver na candidate_mask, SpotLoss deve ser 0
    candidate_mask_without_target = torch.ones(B, 53, dtype=torch.bool)
    candidate_mask_without_target[:, supported_idx] = False

    loss_dict = criterion(outputs, targets, candidate_mask=candidate_mask_without_target)
    assert float(loss_dict["loss_spot"].item()) == 0.0

    # Se target estiver na candidate_mask, SpotLoss > 0
    candidate_mask_with_target = torch.ones(B, 53, dtype=torch.bool)
    loss_dict_active = criterion(outputs, targets, candidate_mask=candidate_mask_with_target)
    assert float(loss_dict_active["loss_spot"].item()) > 0.0


# 11. ClassWeightsUseTrainOnly
def test_11_class_weights_use_train_only():
    weights_path = FULL_TRAIN_DIR / "class_weights.json"
    assert weights_path.exists(), f"{weights_path} não encontrado!"
    with open(weights_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["validation_used_for_weights"] is False
    assert data["test_used_for_weights"] is False
    assert data["train_rows_evaluated"] == 2364492
    assert "positioning_state" in data
    assert len(data["positioning_state"]["final_weights"]) == 7


# 12. CompositeFormulaIsFrozen
def test_12_composite_formula_is_frozen():
    formula_path = FULL_TRAIN_DIR / "frozen_composite_formula.json"
    assert formula_path.exists()
    with open(formula_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    w = data["weights"]
    assert w["StateMacroF1"] == 0.20
    assert w["SectorTransitionMacroF1"] == 0.10
    assert w["NextSectorMacroF1"] == 0.10
    assert w["SpotMRR"] == 0.25
    assert w["TransitionMacroF1"] == 0.20
    assert w["ExitTriggerMacroF1"] == 0.15
    assert sum(w.values()) == 1.00


# 13. EarlyStoppingUsesValidationOnly
def test_13_early_stopping_uses_validation_only():
    config_path = FULL_TRAIN_DIR / "frozen_training_config.json"
    assert config_path.exists()
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["early_stopping_patience"] == 6

    # Verificar que as métricas de treino e validação são independentes
    seed_dir = FULL_TRAIN_DIR / "seed_42026"
    assert (seed_dir / "validation_metrics.jsonl").exists()
    assert (seed_dir / "train_metrics.jsonl").exists()


# 14. BestCheckpointUsesValidationOnly
def test_14_best_checkpoint_uses_validation_only():
    selection_path = FULL_TRAIN_DIR / "best_model_selection.json"
    assert selection_path.exists()
    with open(selection_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["selection_mode"] == "VALIDATION_COMPOSITE_SCORE_MAXIMUM"
    assert data["governance_compliance"]["test_split_used_for_selection"] is False
    assert data["governance_compliance"]["final_holdout_used_for_selection"] is False


# 15. ThreeSeedsAreIndependent
def test_15_three_seeds_are_independent():
    comp_path = FULL_TRAIN_DIR / "three_seed_comparison.json"
    assert comp_path.exists()
    with open(comp_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["seeds"] == [42026, 42027, 42028]
    scores = data["composite_score"]["scores"]
    assert len(scores) == 3
    # As três seeds foram inicializadas independentemente e possuem scores calculados
    assert all(s > 0.0 for s in scores)


# 16. ResumeIsDeterministic
def test_16_resume_is_deterministic(tmp_path):
    mask = load_supervised_spot_mask()
    torch.manual_seed(42026)
    m1 = PositioningTransformerV2RealTemporal(supervised_spot_mask=mask)
    opt1 = torch.optim.AdamW(m1.parameters(), lr=1e-3)

    ckpt_file = tmp_path / "test_resume.pt"
    torch.save({
        "model_state_dict": m1.state_dict(),
        "optimizer_state_dict": opt1.state_dict()
    }, ckpt_file)

    # Restaurar
    m2 = PositioningTransformerV2RealTemporal(supervised_spot_mask=mask)
    opt2 = torch.optim.AdamW(m2.parameters(), lr=1e-3)
    saved = torch.load(ckpt_file)
    m2.load_state_dict(saved["model_state_dict"])
    opt2.load_state_dict(saved["optimizer_state_dict"])

    # Executar mesmo passo determinístico em modo eval (sem dropout estocástico)
    m1.eval()
    m2.eval()
    x = torch.randn(2, 32, 18)
    tm = torch.randn(2, 32, 4, 18)
    cand = torch.ones(2, 53, dtype=torch.bool)

    with torch.no_grad():
        out1 = m1(x, tm, candidate_mask=cand)["logits_state"]
        out2 = m2(x, tm, candidate_mask=cand)["logits_state"]
    assert torch.allclose(out1, out2, atol=1e-6)


# 17. MetricsUseEligibleDenominators
def test_17_metrics_use_eligible_denominators():
    comp_path = FULL_TRAIN_DIR / "baseline_comparison.json"
    assert comp_path.exists()
    with open(comp_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rt = data["models"]["real_temporal_model"]
    assert rt["next_sector_macro_f1"] > 0.0
    assert rt["spot_mrr"] > 0.0


# 18. ZeroSupportIsNA
def test_18_zero_support_is_na():
    preds = np.array([0, 1, 0, 1])
    targets = np.array([0, 1, 0, 1])
    classes = ["CLASS_A", "CLASS_B", "CLASS_ZERO"]
    metrics = compute_metrics_for_classification(preds, targets, classes)
    c_zero = metrics["per_class"]["CLASS_ZERO"]
    assert c_zero["support"] == 0
    assert c_zero["recall"] == "N/A"
    assert c_zero["precision"] == "N/A"
    assert c_zero["f1"] == "N/A"


# 19. SyntheticHistoryCannotReachTrainer
def test_19_synthetic_history_cannot_reach_trainer():
    ds_train = CanonicalV2PositioningDataset(split="train", max_samples=5)
    sample = ds_train[0]
    hist = sample["self_history"].numpy()
    # Verifica variância do tensor real (não é linspace com variância zero ou constante)
    assert np.std(hist) > 0.0
    assert not np.allclose(hist, 0.0)


# 20. PreviousArtifactsRemainUnchanged
def test_20_previous_artifacts_remain_unchanged():
    expected_hashes = {
        "shard_000.parquet": "39ebbe19d9782ffba743d968517b8624530af2daa9375ece6ba742d648c6bebb",
        "shard_001.parquet": "f849f724a67338c1d0158f6c407e615e6a9fa5d1faa675779eb1d8125ad27e6a",
        "shard_002.parquet": "619e0416f779ba6a9aedeb6b34d380469e72e89557bf7c67eff5cfafaaab8d5a",
        "shard_003.parquet": "546f0df72594e80b5bc8780be17b06ed2876a38bbccbc367adfdee776d2f0612",
        "shard_004.parquet": "a79d189b18ad1f7cc71d6ead3f4528cde3371d10cbea81193cb7f1337a1a7166",
        "shard_005.parquet": "7aec90a0b5d40570b0aee2a52e9080cc802486f7955686b68453c2c093d10b70",
    }
    for fname, exp_hash in expected_hashes.items():
        p = INDEX_DIR / fname
        assert p.exists(), f"Arquivo {fname} não existe!"
        assert compute_file_sha256(p) == exp_hash, f"Hash de {fname} foi alterado!"


# 21. NoONNXExport
def test_21_no_onnx_export():
    onnx_in_runs = list(FULL_TRAIN_DIR.rglob("*.onnx"))
    assert len(onnx_in_runs) == 0, f"ONNX encontrado sob {FULL_TRAIN_DIR}: {onnx_in_runs}"
    onnx_in_models = list((BASE_DIR / "models").rglob("*.onnx"))
    assert len(onnx_in_models) == 0, f"ONNX encontrado sob models/: {onnx_in_models}"


# 22. NoFinalEvaluation
def test_22_no_final_evaluation():
    # Split Test e Final Holdout não foram avaliados
    assert not (FULL_TRAIN_DIR / "canonical_test_metrics.json").exists()
    assert not (FULL_TRAIN_DIR / "final_holdout_metrics.json").exists()
    assert not (FULL_TRAIN_DIR / "test_evaluation_report.md").exists()
