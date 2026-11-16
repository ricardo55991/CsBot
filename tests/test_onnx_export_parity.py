#!/usr/bin/env python3
"""
Marco 2B.5 - Seção 10: 18 Testes Direcionados de Exportação ONNX e Paridade.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_v2_dataloader import load_supervised_spot_mask
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import EXPECTED_BASE_SHA256

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_export"
CKPT_2B34 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
CKPT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "selected_checkpoint.pt"


def test_01_ExportUsesFrozenCheckpoints():
    with open(OUT_DIR / "positioning_export_manifest.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["frozen"] is True
    assert m["artifacts"]["training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1/selected_checkpoint.pt"] == EXPECTED_BASE_SHA256


def test_02_ExportUsesEvalMode():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        s = json.load(f)
    assert s["training_executed"] is False


def test_03_InputContractMatchesModel():
    with open(OUT_DIR / "positioning_runtime_contract_v1.json", "r", encoding="utf-8") as f:
        c = json.load(f)
    sess = ort.InferenceSession(str(OUT_DIR / "positioning_transformer_hybrid_v1.onnx"), providers=["CPUExecutionProvider"])
    ort_inputs = [i.name for i in sess.get_inputs()]
    assert ort_inputs == list(c["inputs"].keys())


def test_04_OutputContractMatchesRuntime():
    with open(OUT_DIR / "positioning_runtime_contract_v1.json", "r", encoding="utf-8") as f:
        c = json.load(f)
    sess = ort.InferenceSession(str(OUT_DIR / "positioning_transformer_hybrid_v1.onnx"), providers=["CPUExecutionProvider"])
    ort_outputs = [o.name for o in sess.get_outputs()]
    assert ort_outputs == list(c["outputs"].keys())


def test_05_OnnxCheckerPasses():
    m = onnx.load(str(OUT_DIR / "positioning_transformer_hybrid_v1.onnx"))
    onnx.checker.check_model(m)


def test_06_OnnxRuntimeLoadsModel():
    sess = ort.InferenceSession(str(OUT_DIR / "positioning_transformer_hybrid_v1.onnx"), providers=["CPUExecutionProvider"])
    assert len(sess.get_outputs()) == 13


def test_07_LogitsMeetTolerance():
    with open(OUT_DIR / "numerical_parity.json", "r", encoding="utf-8") as f:
        np_j = json.load(f)
    assert np_j["all_pass"] is True


def test_08_FinalStateAgreementIsExact():
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dp = json.load(f)
    assert dp["agreements"]["final_state_id"]["agreement"] == 1.0


def test_09_SpotAgreementIsExact():
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dp = json.load(f)
    assert dp["agreements"]["selected_spot_id"]["agreement"] == 1.0


def test_10_InvalidMaskedSpotCannotWin():
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dp = json.load(f)
    assert dp["mask_invariants"]["invalid_masked_spot_selection"] == 0


def test_11_UnsupportedSpotCannotWin():
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dp = json.load(f)
    assert dp["mask_invariants"]["unsupported_spot_selection"] == 0


def test_12_ObjectiveRequiresEligibility():
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dp = json.load(f)
    assert dp["mask_invariants"]["objective_without_eligibility"] == 0


def test_13_RetakeRequiresEligibility():
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dp = json.load(f)
    assert dp["mask_invariants"]["retake_without_eligibility"] == 0


def test_14_NeuralSaveIsDisabled():
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dp = json.load(f)
    assert dp["mask_invariants"]["neural_save_output"] == 0


def test_15_MetricsMatchPyTorch():
    with open(OUT_DIR / "metric_parity.json", "r", encoding="utf-8") as f:
        mp = json.load(f)
    assert mp["all_pass"] is True


def test_16_PreviousCheckpointsRemainUnchanged():
    h = hashlib.sha256()
    with open(CKPT_2B34, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == EXPECTED_BASE_SHA256
    assert CKPT_2B36.exists()


def test_17_ExportManifestContainsHashes():
    with open(OUT_DIR / "positioning_export_manifest.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    assert len(m["artifacts"]) >= 8
    for v in m["artifacts"].values():
        assert len(v) == 64


def test_18_NoRuntimeIntegrationOccurs():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        s = json.load(f)
    assert s["runtime_integration_executed"] is False
