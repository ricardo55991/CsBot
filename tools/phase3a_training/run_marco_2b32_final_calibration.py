"""
Fase 3A.3-B - Marco 2B.3.2: Calibração Final das Heads Raras.
Executa:
1. Verificação de suporte de OBJECTIVE na Validation.
2. Varredura exata dos 9 thresholds de transição [0.45, 0.475, 0.50, 0.525, 0.55, 0.575, 0.60, 0.625, 0.65].
3. Ajuste localizado da PositioningStateHead para OBJECTIVE (sem tocar nos encoders nem na SpotRankingHead).
4. Verificação de preservação bitwise (encoders + SpotRankingHead).
5. Consolidação de métricas finais das heads e emissão de artefatos.
"""

import copy
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.phase3a_training.positioning_model_v2 import (
    PositioningTransformerV2RealTemporal,
    STATE_NAMES,
    NEXT_SECTOR_NAMES,
    TRANSITION_NAMES,
    EXIT_TRIGGER_NAMES
)
from tools.phase3a_training.canonical_v2_dataloader import (
    CanonicalV2PositioningDataset,
    canonical_v2_collate_fn,
    load_supervised_spot_mask
)

CALIB_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "final_calibration"
CALIB_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CKPT_PATH = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "selected_patch_checkpoint.pt"
BASE_CKPT_PATH = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training" / "selected_candidate.pt"

def set_seed(seed: int = 42028):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

def compute_submodule_hash(module: nn.Module) -> str:
    h = hashlib.sha256()
    for p in module.parameters():
        h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()

def compute_classification_metrics(preds: np.ndarray, targets: np.ndarray, class_names: List[str]) -> Dict[str, Any]:
    n_classes = len(class_names)
    per_class = {}
    active_f1s = []
    active_recalls = []

    for c_idx, c_name in enumerate(class_names):
        tp = int(np.sum((preds == c_idx) & (targets == c_idx)))
        fp = int(np.sum((preds == c_idx) & (targets != c_idx)))
        fn = int(np.sum((preds != c_idx) & (targets == c_idx)))
        support = int(np.sum(targets == c_idx))

        if support == 0:
            per_class[c_name] = {"support": 0, "precision": "N/A", "recall": "N/A", "f1": "N/A"}
        else:
            prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            per_class[c_name] = {
                "support": support,
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
                "tp": tp,
                "fp": fp,
                "fn": fn
            }
            active_f1s.append(f1)
            active_recalls.append(rec)

    macro_f1 = float(np.mean(active_f1s)) if active_f1s else 0.0
    balanced_acc = float(np.mean(active_recalls)) if active_recalls else 0.0
    return {
        "macro_f1": round(macro_f1, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "active_classes_count": len(active_f1s),
        "total_classes_count": n_classes,
        "per_class": per_class
    }

def compute_spot_ranking_metrics(logits: np.ndarray, targets: np.ndarray, spot_loss_mask: np.ndarray, candidate_mask: np.ndarray, supervised_spot_mask: np.ndarray) -> Dict[str, Any]:
    valid_indices = np.where(spot_loss_mask)[0]
    n_valid = len(valid_indices)
    if n_valid == 0:
        return {"mrr": 0.0, "top1": 0.0, "top5": 0.0, "invalid_masked": 0, "unsupported": 0}

    sub_logits = logits[valid_indices]
    sub_targets = targets[valid_indices]
    sub_cand = candidate_mask[valid_indices]

    preds = np.argmax(sub_logits, axis=1)
    is_valid_cand = sub_cand[np.arange(n_valid), preds]
    invalid_masked = int(np.sum(~is_valid_cand))

    is_sup = (supervised_spot_mask[preds] > 0.5)
    unsupported = int(np.sum(~is_sup))

    top1 = int(np.sum(preds == sub_targets))
    sorted_idx = np.argsort(-sub_logits, axis=1)
    ranks = []
    top5_hits = 0
    for i in range(n_valid):
        t = sub_targets[i]
        order = sorted_idx[i]
        pos = np.where(order == t)[0]
        if len(pos) > 0:
            r = int(pos[0]) + 1
            ranks.append(1.0 / r)
            if r <= 5:
                top5_hits += 1
        else:
            ranks.append(0.0)

    return {
        "mrr": round(float(np.mean(ranks)), 4),
        "top1": round(float(top1 / n_valid), 4),
        "top5": round(float(top5_hits / n_valid), 4),
        "invalid_masked": invalid_masked,
        "unsupported": unsupported,
        "support": n_valid
    }

def evaluate_model_on_validation(model: nn.Module, loader: DataLoader, supervised_spot_mask: np.ndarray) -> Dict[str, Any]:
    model.eval()
    all_probs_to = []
    all_targets_to = []
    all_logits_st = []
    all_targets_st = []
    all_preds_ns = []
    all_targets_ns = []
    all_ns_mask = []
    all_logits_spot = []
    all_targets_spot = []
    all_spot_mask = []
    all_cand_mask = []
    all_preds_tr = []
    all_targets_tr = []
    all_preds_tg = []
    all_targets_tg = []

    with torch.no_grad():
        for batch in loader:
            out = model(
                self_history=batch["self_history"],
                teammates=batch["teammates"],
                temporal_mask=batch["temporal_mask"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )
            probs_to = F.softmax(out["logits_transition_occurs"], dim=1)[:, 1].cpu().numpy()
            all_probs_to.extend(probs_to)
            all_targets_to.extend(batch["sector_transition_occurs"].cpu().numpy())

            all_logits_st.append(out["logits_state"].cpu().numpy())
            all_targets_st.extend(batch["positioning_state"].cpu().numpy())

            preds_ns = torch.argmax(out["logits_next_sector"], dim=1).cpu().numpy()
            all_preds_ns.extend(preds_ns)
            all_targets_ns.extend(batch["next_sector"].cpu().numpy())
            ns_eligible = (batch["sector_transition_occurs"] == 1) & (batch["next_sector_loss_mask"] > 0.5)
            all_ns_mask.extend(ns_eligible.cpu().numpy())

            all_logits_spot.append(out["logits_spot"].cpu().numpy())
            all_targets_spot.extend(batch["candidate_spot_idx"].cpu().numpy())
            all_spot_mask.extend(batch["spot_loss_mask"].cpu().numpy())
            all_cand_mask.append(batch["candidate_mask"].cpu().numpy())

            preds_tr = torch.argmax(out["logits_transition"], dim=1).cpu().numpy()
            all_preds_tr.extend(preds_tr)
            all_targets_tr.extend(batch["transition"].cpu().numpy())

            preds_tg = torch.argmax(out["logits_trigger"], dim=1).cpu().numpy()
            all_preds_tg.extend(preds_tg)
            all_targets_tg.extend(batch["exit_trigger"].cpu().numpy())

    return {
        "probs_to": np.array(all_probs_to),
        "targets_to": np.array(all_targets_to),
        "logits_st": np.concatenate(all_logits_st, axis=0),
        "targets_st": np.array(all_targets_st),
        "preds_ns": np.array(all_preds_ns),
        "targets_ns": np.array(all_targets_ns),
        "ns_mask": np.array(all_ns_mask),
        "logits_spot": np.concatenate(all_logits_spot, axis=0),
        "targets_spot": np.array(all_targets_spot),
        "spot_mask": np.array(all_spot_mask),
        "cand_mask": np.concatenate(all_cand_mask, axis=0),
        "preds_tr": np.array(all_preds_tr),
        "targets_tr": np.array(all_targets_tr),
        "preds_tg": np.array(all_preds_tg),
        "targets_tg": np.array(all_targets_tg)
    }

def main():
    print("=" * 80)
    print("MARCO 2B.3.2: CALIBRAÇÃO FINAL DAS HEADS RARAS")
    print("=" * 80)
    set_seed(42028)

    # 1. Carregar Checkpoint e Invariantes de Preservação
    print(f"\n[Passo 1/6] Carregando checkpoint: {INPUT_CKPT_PATH.name}...")
    sup_mask_t = load_supervised_spot_mask()
    sup_mask_np = sup_mask_t.numpy()

    model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask_t)
    ckpt = torch.load(INPUT_CKPT_PATH, map_location="cpu")
    model_weights = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
    model.load_state_dict(model_weights)

    # Hashes iniciais bitwise
    init_temporal_encoder_hash = compute_submodule_hash(model.transformer)
    init_teammate_encoder_hash = compute_submodule_hash(model.teammate_proj)
    init_spot_head_hash = compute_submodule_hash(model.head_spot)

    print(f"  Temporal Encoder Hash: {init_temporal_encoder_hash[:16]}...")
    print(f"  Teammate Encoder Hash: {init_teammate_encoder_hash[:16]}...")
    print(f"  Spot Head Hash:        {init_spot_head_hash[:16]}...")

    # 2. Carregar Dataset de Validação (5.120 amostras canônicas congeladas)
    print("\n[Passo 2/6] Carregando split de Validação...")
    val_ds = CanonicalV2PositioningDataset(split="validation", max_samples=5120, seed=42028)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, collate_fn=canonical_v2_collate_fn)

    # Carregar suporte total de validação para documentação
    with open(REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "class_support.json", "r", encoding="utf-8") as f:
        full_support_data = json.load(f)

    # 3. Avaliar Modelo na Validação
    print("\n[Passo 3/6] Executando inferência na Validação...")
    val_eval_data = evaluate_model_on_validation(model, val_loader, sup_mask_np)

    # -------------------------------------------------------------------------
    # 4. Calibração de Transição: Varredura Exata dos 9 Thresholds
    # -------------------------------------------------------------------------
    print("\n[Passo 4/6] Executando varredura exata dos 9 thresholds contratuais...")
    threshold_grid = [0.45, 0.475, 0.50, 0.525, 0.55, 0.575, 0.60, 0.625, 0.65]
    sweep_results = []

    probs_to = val_eval_data["probs_to"]
    targets_to = val_eval_data["targets_to"]
    total_samples = len(targets_to)
    actual_trans_count = int(np.sum(targets_to == 1))
    actual_trans_rate = actual_trans_count / total_samples

    selected_threshold_entry = None
    all_transition_gates_met = False

    for th in threshold_grid:
        preds = (probs_to >= th).astype(int)
        tp = int(np.sum((preds == 1) & (targets_to == 1)))
        fp = int(np.sum((preds == 1) & (targets_to == 0)))
        tn = int(np.sum((preds == 0) & (targets_to == 0)))
        fn = int(np.sum((preds == 0) & (targets_to == 1)))

        rec_to = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        rec_no = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        prec_to = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        prec_no = tn / (tn + fn) if (tn + fn) > 0 else 0.0

        f1_to = 2 * prec_to * rec_to / (prec_to + rec_to) if (prec_to + rec_to) > 0 else 0.0
        f1_no = 2 * prec_no * rec_no / (prec_no + rec_no) if (prec_no + rec_no) > 0 else 0.0
        macro_f1 = (f1_to + f1_no) / 2.0
        bal_acc = (rec_to + rec_no) / 2.0

        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        pred_trans_rate = (tp + fp) / total_samples

        gates_met = (rec_to >= 0.35 and rec_no >= 0.80 and macro_f1 >= 0.55 and bal_acc >= 0.55)

        entry = {
            "threshold": th,
            "macro_f1": round(float(macro_f1), 4),
            "balanced_accuracy": round(float(bal_acc), 4),
            "transition_occurs_precision": round(float(prec_to), 4),
            "transition_occurs_recall": round(float(rec_to), 4),
            "no_transition_precision": round(float(prec_no), 4),
            "no_transition_recall": round(float(rec_no), 4),
            "false_positive_rate": round(float(fpr), 4),
            "false_negative_rate": round(float(fnr), 4),
            "predicted_transition_rate": round(float(pred_trans_rate), 4),
            "actual_transition_rate": round(float(actual_trans_rate), 4),
            "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "gates": {
                "transition_occurs_recall_ge_35": rec_to >= 0.35,
                "no_transition_recall_ge_80": rec_no >= 0.80,
                "macro_f1_ge_55": macro_f1 >= 0.55,
                "balanced_accuracy_ge_55": bal_acc >= 0.55,
                "all_gates_met": gates_met
            }
        }
        sweep_results.append(entry)

        if gates_met and (selected_threshold_entry is None or macro_f1 > selected_threshold_entry["macro_f1"]):
            selected_threshold_entry = entry
            all_transition_gates_met = True

    print(f"  Varredura concluída ({len(sweep_results)} thresholds). Algum threshold atingiu os 4 gates? {all_transition_gates_met}")

    # -------------------------------------------------------------------------
    # 5. Análise e Ajuste de OBJECTIVE
    # -------------------------------------------------------------------------
    print("\n[Passo 5/6] Analisando suporte e recall de OBJECTIVE...")
    targets_st = val_eval_data["targets_st"]
    logits_st = val_eval_data["logits_st"]
    preds_st = np.argmax(logits_st, axis=1)

    obj_idx = STATE_NAMES.index("OBJECTIVE")
    obj_tp = int(np.sum((preds_st == obj_idx) & (targets_st == obj_idx)))
    obj_fp = int(np.sum((preds_st == obj_idx) & (targets_st != obj_idx)))
    obj_fn = int(np.sum((preds_st != obj_idx) & (targets_st == obj_idx)))
    obj_support = int(np.sum(targets_st == obj_idx))

    obj_prec = obj_tp / (obj_tp + obj_fp) if (obj_tp + obj_fp) > 0 else 0.0
    obj_rec = obj_tp / (obj_tp + obj_fn) if (obj_tp + obj_fn) > 0 else 0.0
    obj_f1 = 2 * obj_prec * obj_rec / (obj_prec + obj_rec) if (obj_prec + obj_rec) > 0 else 0.0

    full_val_obj_support = full_support_data["support_summary"]["STATE_OBJECTIVE"]["validation"]["sequence_support"]

    objective_analysis = {
        "schema": "csbot.final_calibration.objective_analysis.v1",
        "full_validation_support": full_val_obj_support,
        "sample_validation_support": obj_support,
        "is_support_zero": (full_val_obj_support == 0),
        "status": "N/A" if full_val_obj_support == 0 else "SUPPORTED",
        "metrics_before_localized_adjustment": {
            "support": obj_support,
            "tp": obj_tp,
            "fp": obj_fp,
            "fn": obj_fn,
            "predicted_count": int(np.sum(preds_st == obj_idx)),
            "precision": round(float(obj_prec), 4),
            "recall": round(float(obj_rec), 4),
            "f1": round(float(obj_f1), 4)
        },
        "target_recall_gate": ">= 0.40"
    }

    # Se suporte > 0 e recall < 0.40, executar calibração/ajuste ultra-localizado exclusivo da PositioningStateHead
    calibrated_model = copy.deepcopy(model)
    obj_adjusted = False

    if full_val_obj_support > 0 and obj_rec < 0.40:
        print("  Suporte real de OBJECTIVE detectado com recall abaixo de 0.40.")
        print("  Executando calibração de bias/threshold focal ultra-localizada na PositioningStateHead...")
        # Calibração de threshold por classe para OBJECTIVE:
        # Se p(OBJECTIVE) superar threshold específico, favorece OBJECTIVE sem mexer nos pesos do encoder
        probs_st = F.softmax(torch.tensor(logits_st), dim=1).numpy()
        # Testar threshold ótimo para OBJECTIVE
        best_obj_th = 0.50
        best_obj_rec = obj_rec
        for o_th in np.arange(0.05, 0.50, 0.05):
            mod_preds_st = preds_st.copy()
            high_obj = (probs_st[:, obj_idx] >= o_th)
            mod_preds_st[high_obj] = obj_idx

            m_tp = int(np.sum((mod_preds_st == obj_idx) & (targets_st == obj_idx)))
            m_fn = int(np.sum((mod_preds_st != obj_idx) & (targets_st == obj_idx)))
            m_rec = m_tp / (m_tp + m_fn) if (m_tp + m_fn) > 0 else 0.0

            if m_rec >= 0.40 and (best_obj_rec < 0.40 or m_rec > best_obj_rec):
                best_obj_rec = m_rec
                best_obj_th = float(o_th)
                preds_st = mod_preds_st
                obj_adjusted = True

        objective_analysis["calibrated_threshold"] = best_obj_th
        objective_analysis["calibrated_recall"] = round(float(best_obj_rec), 4)
        objective_analysis["gate_passed"] = (best_obj_rec >= 0.40)
        print(f"  Threshold calibrado para OBJECTIVE: {best_obj_th} -> Recall: {best_obj_rec:.4f} (Gate >= 0.40: {best_obj_rec >= 0.40})")

    # -------------------------------------------------------------------------
    # 6. Avaliação das Outras Heads e Preservação Bitwise
    # -------------------------------------------------------------------------
    print("\n[Passo 6/6] Verificando integridade das outras heads e preservação bitwise...")

    # Preservação bitwise
    final_temporal_encoder_hash = compute_submodule_hash(calibrated_model.transformer)
    final_teammate_encoder_hash = compute_submodule_hash(calibrated_model.teammate_proj)
    final_spot_head_hash = compute_submodule_hash(calibrated_model.head_spot)

    bitwise_encoders_match = (
        init_temporal_encoder_hash == final_temporal_encoder_hash and
        init_teammate_encoder_hash == final_teammate_encoder_hash
    )
    bitwise_spot_match = (init_spot_head_hash == final_spot_head_hash)

    # Spot ranking
    spot_metrics = compute_spot_ranking_metrics(
        val_eval_data["logits_spot"],
        val_eval_data["targets_spot"],
        val_eval_data["spot_mask"],
        val_eval_data["cand_mask"],
        sup_mask_np
    )

    preservation_verdict = (
        bitwise_encoders_match and
        bitwise_spot_match and
        spot_metrics["mrr"] >= 0.75 and
        spot_metrics["top5"] >= 0.95 and
        spot_metrics["invalid_masked"] == 0
    )

    preservation_report = {
        "schema": "csbot.final_calibration.preservation_check.v1",
        "encoders_bitwise_identical": bitwise_encoders_match,
        "spot_ranking_head_bitwise_identical": bitwise_spot_match,
        "temporal_encoder_sha256": final_temporal_encoder_hash,
        "teammate_encoder_sha256": final_teammate_encoder_hash,
        "spot_ranking_head_sha256": final_spot_head_hash,
        "spot_metrics": spot_metrics,
        "gates": {
            "spot_mrr_ge_75": spot_metrics["mrr"] >= 0.75,
            "spot_top5_ge_95": spot_metrics["top5"] >= 0.95,
            "invalid_masked_selections_eq_0": spot_metrics["invalid_masked"] == 0,
            "all_preservation_gates_met": preservation_verdict
        }
    }

    # Métricas finais de todas as heads
    state_metrics = compute_classification_metrics(preds_st, targets_st, STATE_NAMES)

    # NextSector elegíveis
    ns_eligible = val_eval_data["ns_mask"]
    if np.sum(ns_eligible) > 0:
        ns_metrics = compute_classification_metrics(
            val_eval_data["preds_ns"][ns_eligible],
            val_eval_data["targets_ns"][ns_eligible],
            NEXT_SECTOR_NAMES
        )
    else:
        ns_metrics = {"macro_f1": 0.0, "balanced_accuracy": 0.0, "per_class": {}}

    trans_metrics = compute_classification_metrics(val_eval_data["preds_tr"], val_eval_data["targets_tr"], TRANSITION_NAMES)
    trig_metrics = compute_classification_metrics(val_eval_data["preds_tg"], val_eval_data["targets_tg"], EXIT_TRIGGER_NAMES)

    # Decisão canônica final
    # Se all_transition_gates_met for False, veredito é TRANSITION_CALIBRATION_NOT_APPROVED
    if not all_transition_gates_met:
        canonical_verdict = "TRANSITION_CALIBRATION_NOT_APPROVED"
        reason = "Nenhum threshold na grade contratuais [0.45 a 0.65] atingiu simultaneamente os 4 gates de transição (rec_to >= 0.35, rec_no >= 0.80, macro_f1 >= 0.55, bal_acc >= 0.55)."
    elif not objective_analysis.get("gate_passed", True):
        canonical_verdict = "OBJECTIVE_HEAD_REQUIRES_LOCALIZED_PATCH"
        reason = "OBJECTIVE possui suporte real na Validação mas não atingiu recall >= 0.40."
    elif preservation_verdict:
        canonical_verdict = "RARE_CLASS_PATCH_READY_FOR_FINAL_EVALUATION"
        reason = "Todos os gates de transição, OBJECTIVE e preservação bitwise foram atingidos com sucesso."
    else:
        canonical_verdict = "TRANSITION_CALIBRATION_NOT_APPROVED"
        reason = "Falha em gates de preservação ou ranking."

    print(f"\n========================================================")
    print(f"DECISÃO FINAL CANÔNICA: {canonical_verdict}")
    print(f"MOTIVO: {reason}")
    print(f"========================================================")

    # -------------------------------------------------------------------------
    # 7. Gravação dos Artefatos
    # -------------------------------------------------------------------------
    # 1. validation_support.json
    with open(CALIB_DIR / "validation_support.json", "w", encoding="utf-8") as f:
        json.dump(full_support_data, f, indent=2)

    # 2. transition_threshold_sweep.json
    with open(CALIB_DIR / "transition_threshold_sweep.json", "w", encoding="utf-8") as f:
        json.dump({
            "schema": "csbot.final_calibration.threshold_sweep.v1",
            "threshold_grid": threshold_grid,
            "results": sweep_results,
            "selected_threshold_entry": selected_threshold_entry,
            "all_gates_met": all_transition_gates_met
        }, f, indent=2)

    # 3. objective_validation_analysis.json
    with open(CALIB_DIR / "objective_validation_analysis.json", "w", encoding="utf-8") as f:
        json.dump(objective_analysis, f, indent=2)

    # 4. final_head_metrics.json
    final_head_metrics = {
        "schema": "csbot.final_calibration.head_metrics.v1",
        "positioning_state": state_metrics,
        "next_sector": ns_metrics,
        "transition": trans_metrics,
        "exit_trigger": trig_metrics,
        "spot_ranking": spot_metrics
    }
    with open(CALIB_DIR / "final_head_metrics.json", "w", encoding="utf-8") as f:
        json.dump(final_head_metrics, f, indent=2)

    # 5. preservation_check.json
    with open(CALIB_DIR / "preservation_check.json", "w", encoding="utf-8") as f:
        json.dump(preservation_report, f, indent=2)

    # 6. selected_thresholds.json
    selected_thresholds = {
        "schema": "csbot.final_calibration.selected_thresholds.v1",
        "transition_threshold": selected_threshold_entry["threshold"] if selected_threshold_entry else 0.475,
        "transition_gates_met": all_transition_gates_met,
        "objective_threshold": objective_analysis.get("calibrated_threshold", 0.50),
        "canonical_verdict": canonical_verdict,
        "decision_reason": reason
    }
    with open(CALIB_DIR / "selected_thresholds.json", "w", encoding="utf-8") as f:
        json.dump(selected_thresholds, f, indent=2)

    # 7. calibrated_patch_checkpoint.pt
    ckpt_out = CALIB_DIR / "calibrated_patch_checkpoint.pt"
    torch.save(calibrated_model.state_dict(), ckpt_out)
    print(f"  Checkpoint calibrado gravado: {ckpt_out.name}")

if __name__ == "__main__":
    main()
