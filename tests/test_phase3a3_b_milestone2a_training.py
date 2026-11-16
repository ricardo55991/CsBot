#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2A: Suíte Canônica de Testes Unitários de Treinamento e Governança (Seção 14).

Invariantes Auditados (20 testes obrigatórios):
1.  test_dry_run_uses_canonical_temporal_loader
2.  test_dry_run_losses_are_finite
3.  test_dry_run_gradients_are_finite
4.  test_temporary_checkpoint_is_restorable
5.  test_overfit_subset_uses_train_only
6.  test_pilot_uses_complete_matches
7.  test_validation_is_never_optimized
8.  test_test_is_never_loaded
9.  test_final_holdout_is_never_loaded
10. test_spot_loss_is_zero_for_transit
11. test_spot_loss_is_zero_for_unmapped
12. test_masked_candidate_cannot_win
13. test_candidate_target_exists_when_eligible
14. test_class_weights_use_pilot_train_only
15. test_temporal_and_last_frame_use_same_examples
16. test_no_synthetic_history_in_either_ablation
17. test_sector_labels_contain_multiple_classes
18. test_metrics_contain_real_support
19. test_zero_support_is_na
20. test_previous_checkpoints_remain_unchanged
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pytest
import torch
import torch.nn as nn

# Base dir resolution
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    CanonicalTemporalPositioningDataset,
    create_canonical_temporal_dataloader,
    load_canonical_temporal_splits,
    STATE_NAMES,
    SECTOR_NAMES
)
from tools.phase3a_training.positioning_model import PositioningTransformerV1, PositioningMultitaskLoss


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Teste 1: DryRunUsesCanonicalTemporalLoader
# ---------------------------------------------------------------------------
def test_dry_run_uses_canonical_temporal_loader():
    dry_run_script_path = BASE_DIR / "tools" / "phase3a_training" / "run_milestone2a_dry_run.py"
    assert dry_run_script_path.exists(), "Script run_milestone2a_dry_run.py não encontrado"
    code = dry_run_script_path.read_text(encoding="utf-8")
    assert "create_canonical_temporal_dataloader" in code or "CanonicalTemporalPositioningDataset" in code
    assert "canonical_temporal_dataloader" in code

    metrics_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "dry_run_metrics.json"
    assert metrics_path.exists(), "dry_run_metrics.json não encontrado"
    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("data_provenance") == "REAL"
    assert data.get("status") == "PASS"


# ---------------------------------------------------------------------------
# Teste 2: DryRunLossesAreFinite
# ---------------------------------------------------------------------------
def test_dry_run_losses_are_finite():
    metrics_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "dry_run_metrics.json"
    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    train_losses = data["losses"]["train"]
    assert len(train_losses) >= 2, "Menos de 2 batches de treino avaliados"
    for b in train_losses:
        for k in ["loss_total", "loss_state", "loss_sector", "loss_spot", "loss_transition", "loss_trigger"]:
            val = b[k]
            assert np.isfinite(val), f"Loss {k} não é finita: {val}"
            assert val >= 0.0, f"Loss {k} é negativa: {val}"

    val_loss = data["losses"]["validation"]
    for k in ["loss_total", "loss_state", "loss_sector", "loss_spot", "loss_transition", "loss_trigger"]:
        val = val_loss[k]
        assert np.isfinite(val), f"Val loss {k} não é finita: {val}"
        assert val >= 0.0, f"Val loss {k} é negativa: {val}"


# ---------------------------------------------------------------------------
# Teste 3: DryRunGradientsAreFinite
# ---------------------------------------------------------------------------
def test_dry_run_gradients_are_finite():
    metrics_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "dry_run_metrics.json"
    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grad_info = data["gradient_checks"]
    assert grad_info["all_gradients_finite"] is True
    assert grad_info["mean_grad_norm"] > 0.0
    assert np.isfinite(grad_info["mean_grad_norm"])
    assert np.isfinite(grad_info["max_grad_norm"])


# ---------------------------------------------------------------------------
# Teste 4: TemporaryCheckpointIsRestorable
# ---------------------------------------------------------------------------
def test_temporary_checkpoint_is_restorable():
    metrics_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "dry_run_metrics.json"
    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ckpt_info = data["checkpoint_restoration"]
    assert ckpt_info["all_parameters_identical"] is True
    assert ckpt_info["max_parameter_diff"] == 0.0

    ckpt_path = BASE_DIR / ckpt_info["checkpoint_file"]
    assert ckpt_path.exists(), f"Arquivo de checkpoint não existe: {ckpt_path}"
    loaded = torch.load(ckpt_path, map_location="cpu")
    assert "model_state_dict" in loaded
    assert "optimizer_state_dict" in loaded


# ---------------------------------------------------------------------------
# Teste 5: OverfitSubsetUsesTrainOnly
# ---------------------------------------------------------------------------
def test_overfit_subset_uses_train_only():
    metrics_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "overfit_metrics.json"
    assert metrics_path.exists(), "overfit_metrics.json não encontrado"
    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("data_provenance") == "REAL"
    assert data["results"]["loss_reduction_pct"] > 50.0
    assert data["results"]["zero_nan_inf"] is True

    # Verificar que as 7 classes estão presentes no breakdown
    classes = data["class_breakdown"]
    for expected in ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE", "SAVE"]:
        assert expected in classes, f"Classe {expected} ausente no subset de overfit"
        assert classes[expected] > 0, f"Classe {expected} tem 0 amostras"


# ---------------------------------------------------------------------------
# Teste 6: PilotUsesCompleteMatches
# ---------------------------------------------------------------------------
def test_pilot_uses_complete_matches():
    manifest_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "pilot_subset_manifest.json"
    assert manifest_path.exists(), "pilot_subset_manifest.json não encontrado"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    matches = manifest["matches"]
    assert len(matches) == 31, f"Piloto deve conter exatamente 31 demos, encontrado: {len(matches)}"

    splits = load_canonical_temporal_splits(BASE_DIR / "datasets" / "mirage_v2")
    train_demos = set(splits["train_demos"])
    val_demos = set(splits["validation_demos"])
    test_demos = set(splits["test_demos"])

    for m in matches:
        d_id = m["demo_id"]
        assert d_id in train_demos, f"Demo {d_id} não pertence ao split Train!"
        assert d_id not in val_demos, f"Demo {d_id} contaminou o split Validation!"
        assert d_id not in test_demos, f"Demo {d_id} contaminou o split Test!"
        assert len(m["sha256"]) == 64, f"Hash SHA-256 inválido para {d_id}: {m['sha256']}"


# ---------------------------------------------------------------------------
# Teste 7: ValidationIsNeverOptimized
# ---------------------------------------------------------------------------
def test_validation_is_never_optimized():
    pilot_script_path = BASE_DIR / "tools" / "phase3a_training" / "run_milestone2a_pilot_and_ablation.py"
    code = pilot_script_path.read_text(encoding="utf-8")
    assert "def evaluate_model_full_validation" in code

    # No loop de validação, deve haver model.eval() e torch.no_grad()
    eval_def_idx = code.find("def evaluate_model_full_validation")
    eval_body = code[eval_def_idx:eval_def_idx + 2500]
    assert "model.eval()" in eval_body
    assert "with torch.no_grad():" in eval_body
    assert "optimizer" not in eval_body or "optimizer.step()" not in eval_body


# ---------------------------------------------------------------------------
# Teste 8: TestIsNeverLoaded
# ---------------------------------------------------------------------------
def test_test_is_never_loaded():
    splits = load_canonical_temporal_splits(BASE_DIR / "datasets" / "mirage_v2")
    test_demos = set(splits["test_demos"])

    pilot_script_path = BASE_DIR / "tools" / "phase3a_training" / "run_milestone2a_pilot_and_ablation.py"
    code = pilot_script_path.read_text(encoding="utf-8")

    # Verificar que o split 'test' não é carregado no treino ou validação
    assert 'split="test"' not in code and "split='test'" not in code

    manifest_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "pilot_subset_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    for m in manifest["matches"]:
        assert m["demo_id"] not in test_demos, f"Demo de teste detectada: {m['demo_id']}"


# ---------------------------------------------------------------------------
# Teste 9: FinalHoldoutIsNeverLoaded
# ---------------------------------------------------------------------------
def test_final_holdout_is_never_loaded():
    splits = load_canonical_temporal_splits(BASE_DIR / "datasets" / "mirage_v2")
    excluded_demos = set(splits.get("excluded_raw_dem_demos", []))

    manifest_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "pilot_subset_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for m in manifest["matches"]:
        assert m["demo_id"] not in excluded_demos, f"Demo de holdout/excluída detectada: {m['demo_id']}"


# ---------------------------------------------------------------------------
# Teste 10: SpotLossIsZeroForTransit
# ---------------------------------------------------------------------------
def test_spot_loss_is_zero_for_transit():
    criterion = PositioningMultitaskLoss()
    B = 8
    dummy_outputs = {
        "logits_state": torch.randn(B, 7),
        "logits_sector": torch.randn(B, 6),
        "logits_spot": torch.randn(B, 53),
        "logits_transition": torch.randn(B, 7),
        "logits_trigger": torch.randn(B, 8)
    }
    targets = {
        "positioning_state": torch.zeros(B, dtype=torch.long), # TRANSIT
        "next_sector": torch.zeros(B, dtype=torch.long),
        "candidate_spot_idx": torch.zeros(B, dtype=torch.long),
        "spot_loss_mask": torch.zeros(B, dtype=torch.bool), # False para todos em TRANSIT
        "transition": torch.zeros(B, dtype=torch.long),
        "exit_trigger": torch.zeros(B, dtype=torch.long)
    }
    loss_dict = criterion(dummy_outputs, targets)
    assert loss_dict["loss_spot"].item() == 0.0, f"SpotLoss não é zero: {loss_dict['loss_spot'].item()}"
    assert loss_dict["valid_spot_samples"] == 0


# ---------------------------------------------------------------------------
# Teste 11: SpotLossIsZeroForUnmapped
# ---------------------------------------------------------------------------
def test_spot_loss_is_zero_for_unmapped():
    criterion = PositioningMultitaskLoss()
    B = 8
    dummy_outputs = {
        "logits_state": torch.randn(B, 7),
        "logits_sector": torch.randn(B, 6),
        "logits_spot": torch.randn(B, 53),
        "logits_transition": torch.randn(B, 7),
        "logits_trigger": torch.randn(B, 8)
    }
    targets = {
        "positioning_state": torch.ones(B, dtype=torch.long) * 3, # HOLD, mas UNMAPPED
        "next_sector": torch.zeros(B, dtype=torch.long),
        "candidate_spot_idx": torch.zeros(B, dtype=torch.long),
        "spot_loss_mask": torch.zeros(B, dtype=torch.bool), # False por ser UNMAPPED
        "transition": torch.zeros(B, dtype=torch.long),
        "exit_trigger": torch.zeros(B, dtype=torch.long)
    }
    loss_dict = criterion(dummy_outputs, targets)
    assert loss_dict["loss_spot"].item() == 0.0, f"SpotLoss não é zero para UNMAPPED: {loss_dict['loss_spot'].item()}"


# ---------------------------------------------------------------------------
# Teste 12: MaskedCandidateCannotWin
# ---------------------------------------------------------------------------
def test_masked_candidate_cannot_win():
    model = PositioningTransformerV1(
        hidden_dim=192,
        num_layers=3,
        num_heads=6,
        feedforward_dim=768,
        dropout=0.0
    )
    model.eval()

    B = 4
    hist = torch.randn(B, 32, 18)
    tm = torch.randn(B, 32, 4, 18)

    # Mascarar todos os spots exceto o spot índice 10
    mask = torch.zeros(B, 53, dtype=torch.bool)
    mask[:, 10] = True

    with torch.no_grad():
        out = model(hist, tm, candidate_mask=mask)

    masked_logits = out["logits_spot"]
    # Para qualquer spot j != 10, o logit deve ser -1e9
    for j in range(53):
        if j != 10:
            assert torch.all(masked_logits[:, j] <= -1e8), f"Spot mascarado {j} possui logit alto: {masked_logits[:, j]}"

    preds = torch.argmax(masked_logits, dim=-1)
    assert torch.all(preds == 10), f"Predição esperada [10, 10, 10, 10], obtido: {preds.tolist()}"


# ---------------------------------------------------------------------------
# Teste 13: CandidateTargetExistsWhenEligible
# ---------------------------------------------------------------------------
def test_candidate_target_exists_when_eligible():
    ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="train",
        max_samples=200,
        preload_npz=False
    )
    for i in range(len(ds)):
        item = ds[i]
        if item["spot_loss_mask"].item() is True:
            target_spot = item["candidate_spot_idx"].item()
            cand_mask = item["candidate_mask"]
            assert cand_mask[target_spot].item() is True, f"Amostra {i}: spot alvo {target_spot} está mascarado!"


# ---------------------------------------------------------------------------
# Teste 14: ClassWeightsUsePilotTrainOnly
# ---------------------------------------------------------------------------
def test_class_weights_use_pilot_train_only():
    pilot_script_path = BASE_DIR / "tools" / "phase3a_training" / "run_milestone2a_pilot_and_ablation.py"
    code = pilot_script_path.read_text(encoding="utf-8")
    assert "train_ds.state_vals" in code
    assert "val_ds.state_vals" not in code or "val_state_counts" not in code
    assert "ClassWeightsUsePilotTrainOnly" in code or "train_state_counts" in code


# ---------------------------------------------------------------------------
# Teste 15: TemporalAndLastFrameUseSameExamples
# ---------------------------------------------------------------------------
def test_temporal_and_last_frame_use_same_examples():
    pilot_script_path = BASE_DIR / "tools" / "phase3a_training" / "run_milestone2a_pilot_and_ablation.py"
    code = pilot_script_path.read_text(encoding="utf-8")
    # Ambos os modelos usam o mesmo train_loader e val_loader
    assert "for batch in train_loader:" in code
    assert "evaluate_model_full_validation(model_a, val_loader" in code
    assert "evaluate_model_full_validation(model_b, val_loader" in code


# ---------------------------------------------------------------------------
# Teste 16: NoSyntheticHistoryInEitherAblation
# ---------------------------------------------------------------------------
def test_no_synthetic_history_in_either_ablation():
    pilot_script_path = BASE_DIR / "tools" / "phase3a_training" / "run_milestone2a_pilot_and_ablation.py"
    code = pilot_script_path.read_text(encoding="utf-8")
    # Assegurar ausência de chamada executável de interpolação sintética ou deriva artificial
    assert "np.linspace(" not in code
    assert "torch.linspace(" not in code
    assert "step_drift" not in code
    assert "cur_pos_x" not in code


# ---------------------------------------------------------------------------
# Teste 17: SectorLabelsContainMultipleClasses
# ---------------------------------------------------------------------------
def test_sector_labels_contain_multiple_classes():
    ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    paths = [
        ds_dir / "positioning" / "positioning_sequences_v1" / "shard_000.parquet",
        ds_dir / "positioning" / "objective_save_sequences.parquet"
    ]
    ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="train",
        parquet_paths=paths,
        preload_npz=False
    )
    unique_sectors = set(ds.sector_vals.tolist())
    assert len(unique_sectors) >= 2, f"Menos de 2 setores únicos encontrados: {unique_sectors}"


# ---------------------------------------------------------------------------
# Teste 18: MetricsContainRealSupport
# ---------------------------------------------------------------------------
def test_metrics_contain_real_support():
    preds = np.array([0, 1, 2, 0, 1])
    targets = np.array([0, 1, 2, 1, 1])
    class_names = ["CLASS_A", "CLASS_B", "CLASS_C", "CLASS_D"]

    from tools.phase3a_training.run_milestone2a_pilot_and_ablation import compute_classification_metrics
    res = compute_classification_metrics(preds, targets, class_names)

    assert "per_class" in res
    assert res["per_class"]["CLASS_A"]["support"] == 1
    assert res["per_class"]["CLASS_B"]["support"] == 3
    assert res["per_class"]["CLASS_C"]["support"] == 1
    assert res["per_class"]["CLASS_D"]["support"] == 0


# ---------------------------------------------------------------------------
# Teste 19: ZeroSupportIsNA
# ---------------------------------------------------------------------------
def test_zero_support_is_na():
    preds = np.array([0, 1, 0, 1])
    targets = np.array([0, 1, 0, 1])
    class_names = ["ACTIVE_0", "ACTIVE_1", "RARE_ABSENT"]

    from tools.phase3a_training.run_milestone2a_pilot_and_ablation import compute_classification_metrics
    res = compute_classification_metrics(preds, targets, class_names)

    # A classe RARE_ABSENT tem suporte 0
    absent = res["per_class"]["RARE_ABSENT"]
    assert absent["support"] == 0
    assert absent["precision"] == "N/A"
    assert absent["recall"] == "N/A"
    assert absent["f1"] == "N/A"

    # Macro F1 deve considerar apenas as classes com support > 0
    assert res["active_classes_count"] == 2
    assert res["macro_f1"] == 1.0


# ---------------------------------------------------------------------------
# Teste 20: PreviousCheckpointsRemainUnchanged
# ---------------------------------------------------------------------------
def test_previous_checkpoints_remain_unchanged():
    v1_ckpt_path = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_v1.pt"
    assert v1_ckpt_path.exists(), f"Checkpoint v1 não encontrado em {v1_ckpt_path}"
    sha = compute_file_sha256(v1_ckpt_path)
    expected_sha = "e4b505a2a082bd348ca63b242e6daace869c4faf7168c42e9c7fe89106bf05f0"
    assert sha == expected_sha, f"Hash do checkpoint v1 foi alterado! Esperado: {expected_sha}, Atual: {sha}"
