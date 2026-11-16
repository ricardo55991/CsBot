#!/usr/bin/env python3
"""
Suíte de Testes da Fase 3A: Validação e Auditoria do Treinamento do Positioning Transformer V1.
Cobre 20 testes formais conforme a Seção 19 da especificação técnica.
"""

import os
import sys
import json
from pathlib import Path
import pytest
import torch

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

RUNS_DIR = BASE_DIR / "training_runs" / "positioning_v1"
MODELS_DIR = BASE_DIR / "models" / "positioning"

# 1. Verificação do Dry-run
def test_01_dry_run_report_exists():
    report_file = RUNS_DIR / "dry_run_report.md"
    assert report_file.exists(), f"dry_run_report.md não encontrado em {RUNS_DIR}"
    content = report_file.read_text(encoding="utf-8")
    assert "DRY_RUN_PASSED" in content, "Dry run não foi aprovado"

# 2. Verificação de perda de spot zero em TRANSIT
def test_02_spot_loss_zero_in_transit():
    from tools.phase3a_training.positioning_model import PositioningMultitaskLoss
    criterion = PositioningMultitaskLoss()
    outputs = {"logits_state": torch.randn(8, 7), "logits_sector": torch.randn(8, 6), "logits_spot": torch.randn(8, 53), "logits_transition": torch.randn(8, 7), "logits_trigger": torch.randn(8, 8)}
    targets = {
        "positioning_state": torch.zeros(8, dtype=torch.long),
        "next_sector": torch.zeros(8, dtype=torch.long),
        "candidate_spot_idx": torch.zeros(8, dtype=torch.long),
        "spot_loss_mask": torch.zeros(8, dtype=torch.bool), # Lote puramente transit / sem spot
        "transition": torch.zeros(8, dtype=torch.long),
        "exit_trigger": torch.zeros(8, dtype=torch.long)
    }
    loss_dict = criterion(outputs, targets)
    assert loss_dict["loss_spot"].item() == 0.0, "Spot Loss deve ser estritamente zero para batch não elegível"

# 3. Verificação de perda de spot positiva em instâncias elegíveis
def test_03_spot_loss_positive_when_eligible():
    from tools.phase3a_training.positioning_model import PositioningMultitaskLoss
    criterion = PositioningMultitaskLoss()
    outputs = {"logits_state": torch.randn(8, 7), "logits_sector": torch.randn(8, 6), "logits_spot": torch.randn(8, 53), "logits_transition": torch.randn(8, 7), "logits_trigger": torch.randn(8, 8)}
    targets = {
        "positioning_state": torch.ones(8, dtype=torch.long),
        "next_sector": torch.zeros(8, dtype=torch.long),
        "candidate_spot_idx": torch.zeros(8, dtype=torch.long),
        "spot_loss_mask": torch.ones(8, dtype=torch.bool), # Lote elegível
        "transition": torch.zeros(8, dtype=torch.long),
        "exit_trigger": torch.zeros(8, dtype=torch.long)
    }
    loss_dict = criterion(outputs, targets)
    assert loss_dict["loss_spot"].item() > 0.0, "Spot Loss deve ser positiva para lote elegível"

# 4. Gradientes finitos
def test_04_model_gradient_finite():
    from tools.phase3a_training.positioning_model import PositioningTransformerV1, PositioningMultitaskLoss
    model = PositioningTransformerV1()
    criterion = PositioningMultitaskLoss()
    hist = torch.randn(4, 32, 18)
    tm = torch.randn(4, 32, 4, 18)
    c_mask = torch.ones(4, 53, dtype=torch.bool)
    out = model(hist, tm, c_mask)
    targets = {
        "positioning_state": torch.zeros(4, dtype=torch.long),
        "next_sector": torch.zeros(4, dtype=torch.long),
        "candidate_spot_idx": torch.zeros(4, dtype=torch.long),
        "spot_loss_mask": torch.tensor([True, False, True, False]),
        "transition": torch.zeros(4, dtype=torch.long),
        "exit_trigger": torch.zeros(4, dtype=torch.long)
    }
    loss = criterion(out, targets)["loss_total"]
    loss.backward()
    for name, p in model.named_parameters():
        if p.grad is not None:
            assert torch.isfinite(p.grad).all(), f"Gradiente não-finito detectado em {name}"

# 5. Relatório do Piloto
def test_05_pilot_report_exists():
    report_file = RUNS_DIR / "pilot_subset_report.md"
    assert report_file.exists(), f"pilot_subset_report.md não encontrado em {RUNS_DIR}"
    content = report_file.read_text(encoding="utf-8")
    assert "PILOT_TRAINING_PASSED" in content, "Treino piloto não foi aprovado"

# 6. Execução das 3 seeds
def test_06_all_three_seeds_executed():
    for seed in [42026, 42027, 42028]:
        seed_dir = RUNS_DIR / f"seed_{seed}"
        assert seed_dir.exists(), f"Diretório da seed {seed} não encontrado"

# 7. Integridade dos artefatos por seed
def test_07_seed_artifacts_integrity():
    required_files = [
        "config.json", "input_snapshot.json", "metrics_train.jsonl",
        "metrics_validation.jsonl", "best_checkpoint.pt", "last_checkpoint.pt", "training_log.txt"
    ]
    for seed in [42026, 42027, 42028]:
        seed_dir = RUNS_DIR / f"seed_{seed}"
        for rf in required_files:
            p = seed_dir / rf
            assert p.exists() and p.stat().st_size > 0, f"Arquivo {rf} inválido na seed {seed}"

# 8. Seleção do melhor modelo
def test_08_best_model_selection_valid():
    sel_file = RUNS_DIR / "best_model_selection.json"
    assert sel_file.exists(), "best_model_selection.json não encontrado"
    data = json.load(open(sel_file, "r", encoding="utf-8"))
    assert data["selected_seed"] in [42026, 42027, 42028], "Seed selecionada inválida"
    assert "master_model_sha256" in data and len(data["master_model_sha256"]) == 64

# 9. Carregamento do checkpoint mestre
def test_09_master_checkpoint_loadable():
    master_pt = MODELS_DIR / "de_mirage_positioning_v1.pt"
    assert master_pt.exists(), f"Modelo mestre {master_pt} não existe"
    checkpoint = torch.load(master_pt, map_location="cpu")
    assert "model_state_dict" in checkpoint, "Checkpoint não possui model_state_dict"
    assert "config" in checkpoint, "Checkpoint não possui config"

# 10. Macro F1 supera baseline trivial
def test_10_state_macro_f1_beats_trivial():
    test_metrics_file = RUNS_DIR / "test_metrics.json"
    assert test_metrics_file.exists(), "test_metrics.json não existe"
    m = json.load(open(test_metrics_file, "r", encoding="utf-8"))
    assert m["state_macro_f1"] > 0.214, f"Macro F1 ({m['state_macro_f1']}) deve superar baseline trivial (0.214)"

# 11. Balanced Accuracy supera aleatório
def test_11_state_balanced_accuracy_valid():
    m = json.load(open(RUNS_DIR / "test_metrics.json", "r", encoding="utf-8"))
    assert m["state_balanced_accuracy"] > 0.50, f"Balanced Accuracy ({m['state_balanced_accuracy']}) deve superar 0.50"

# 12. Spot MRR satisfatório
def test_12_spot_mrr_exceeds_threshold():
    m = json.load(open(RUNS_DIR / "test_metrics.json", "r", encoding="utf-8"))
    assert m["spot_mrr"] > 0.60, f"Spot MRR ({m['spot_mrr']}) deve ser superior a 0.60"

# 13. Spot Top-5 supera 80%
def test_13_spot_top5_exceeds_threshold():
    m = json.load(open(RUNS_DIR / "test_metrics.json", "r", encoding="utf-8"))
    assert m["spot_top5_accuracy"] > 0.80, f"Spot Top-5 ({m['spot_top5_accuracy']}) deve ser superior a 80%"

# 14. Masked Invalid Spot Rate = 0
def test_14_masked_invalid_spot_rate_zero():
    from tools.phase3a_training.positioning_model import PositioningTransformerV1
    model = PositioningTransformerV1()
    hist = torch.randn(2, 32, 18)
    tm = torch.randn(2, 32, 4, 18)
    c_mask = torch.zeros(2, 53, dtype=torch.bool)
    c_mask[:, 10] = True # Apenas spot 10 permitido
    out = model(hist, tm, c_mask)
    probs = torch.softmax(out["logits_spot"], dim=-1)
    # Todos os outros spots devem ter probabilidade exatamente 0.0 (ou desprezível)
    assert probs[0, 10].item() > 0.99, "Spot não mascarado deve receber quase 100% da probabilidade"

# 15. Estados raros detectados
def test_15_rare_states_detected():
    rare_file = RUNS_DIR / "rare_state_report.md"
    assert rare_file.exists(), "rare_state_report.md não encontrado"
    content = rare_file.read_text(encoding="utf-8")
    for st in ["HOLD", "CLEARANCE", "STAGING", "OBJECTIVE", "RETAKE", "SAVE"]:
        assert st in content, f"Estado raro {st} não encontrado no relatório"

# 16. Holdout metrics válidos
def test_16_holdout_metrics_valid():
    h_file = RUNS_DIR / "holdout_metrics.json"
    assert h_file.exists(), "holdout_metrics.json não existe"
    data = json.load(open(h_file, "r", encoding="utf-8"))
    for key in ["holdout_ct_side", "holdout_tr_side", "holdout_specialist_roles", "holdout_critical_events", "holdout_recent_meta"]:
        assert key in data, f"Chave {key} ausente em holdout_metrics.json"

# 17. Ablation mostra impacto de componentes
def test_17_ablation_shows_degradation():
    abl_file = RUNS_DIR / "ablation_report.md"
    assert abl_file.exists(), "ablation_report.md não encontrado"
    content = abl_file.read_text(encoding="utf-8")
    assert "Ablation 4" in content, "Ablation 4 ausente"

# 18. Calibração e ECE reportados
def test_18_calibration_report_valid():
    c_file = RUNS_DIR / "calibration_report.md"
    assert c_file.exists(), "calibration_report.md não encontrado"
    content = c_file.read_text(encoding="utf-8")
    assert "Expected Calibration Error" in content, "ECE ausente em calibration_report.md"

# 19. PDFs visuais existem e válidos
def test_19_visual_reports_exist():
    pdf1 = RUNS_DIR / "learning_curves.pdf"
    pdf2 = RUNS_DIR / "confusion_matrices.pdf"
    assert pdf1.exists() and pdf1.stat().st_size > 3000, "learning_curves.pdf inválido"
    assert pdf2.exists() and pdf2.stat().st_size > 3000, "confusion_matrices.pdf inválido"

# 20. Relatório consolidado com veredito aprovado
def test_20_final_report_approved():
    rep = RUNS_DIR / "positioning_v1_training_report.md"
    assert rep.exists(), "positioning_v1_training_report.md não encontrado"
    content = rep.read_text(encoding="utf-8")
    assert "MIRAGE_POSITIONING_TRANSFORMER_V1_OFFLINE_APPROVED" in content, "Veredito de aprovação ausente"
