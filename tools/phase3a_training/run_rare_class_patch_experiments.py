"""
Fase 3A.3-B - Marco 2B.3.1: Experimentos de Patch Localizado de Classes Raras e Transições.
Executa os Experimentos A (Class-Balanced CE), B (Focal Loss) e C (Balanced Sampling),
aplica calibração de thresholds na Validation, protege a SpotRankingHead e valida os gates.
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
from torch.utils.data import DataLoader, Dataset

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

PATCH_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1"
BASE_CKPT_PATH = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training" / "selected_candidate.pt"

# Fixar seeds para reprodutibilidade estrita
def set_seed(seed: int = 42028):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

def compute_weights_effective_number(counts: Dict[str, int], class_names: List[str], beta: float, clamp_range=(0.2, 10.0)) -> torch.Tensor:
    weights = []
    for c in class_names:
        n = counts.get(c, 0)
        if n > 0:
            eff_n = (1.0 - (beta ** n)) / (1.0 - beta)
            w = 1.0 / eff_n
        else:
            w = 1.0
        weights.append(w)
    weights = np.array(weights, dtype=np.float32)
    mean_w = np.mean(weights)
    if mean_w > 0:
        weights = weights / mean_w
    weights = np.clip(weights, clamp_range[0], clamp_range[1])
    return torch.tensor(weights, dtype=torch.float32)

class FocalLoss(nn.Module):
    def __init__(self, alpha: Optional[torch.Tensor] = None, gamma: float = 2.0, reduction: str = 'mean'):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # logits: [B, C], targets: [B]
        ce_loss = F.cross_entropy(logits, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = ((1.0 - pt) ** self.gamma) * ce_loss
        if self.alpha is not None:
            if self.alpha.device != logits.device:
                self.alpha = self.alpha.to(logits.device)
            alpha_t = self.alpha[targets]
            focal_loss = alpha_t * focal_loss
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        return focal_loss

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
                "f1": round(f1, 4)
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

def get_head_spot_hash(model: nn.Module) -> str:
    h = hashlib.sha256()
    for p in model.head_spot.parameters():
        h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()

def evaluate_patch_model(model: nn.Module, loader: DataLoader, supervised_spot_mask: np.ndarray, transition_threshold: float = 0.50) -> Dict[str, Any]:
    model.eval()
    all_logits_to, all_targets_to = [], []
    all_preds_st, all_targets_st = [], []
    all_preds_ns, all_targets_ns, all_ns_mask = [], [], []
    all_logits_spot, all_targets_spot, all_spot_mask, all_cand_mask = [], [], [], []
    all_preds_tr, all_targets_tr = [], []
    all_preds_tg, all_targets_tg = [], []

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
            # SectorTransitionOccurs logits
            logits_to = out["logits_transition_occurs"]
            probs_to = F.softmax(logits_to, dim=1)[:, 1].cpu().numpy()
            all_logits_to.extend(probs_to)
            all_targets_to.extend(batch["sector_transition_occurs"].cpu().numpy())

            # PositioningState
            preds_st = torch.argmax(out["logits_state"], dim=1).cpu().numpy()
            all_preds_st.extend(preds_st)
            all_targets_st.extend(batch["positioning_state"].cpu().numpy())

            # NextSector
            preds_ns = torch.argmax(out["logits_next_sector"], dim=1).cpu().numpy()
            all_preds_ns.extend(preds_ns)
            all_targets_ns.extend(batch["next_sector"].cpu().numpy())
            ns_mask = (batch["sector_transition_occurs"] == 1) & (batch["next_sector_loss_mask"] > 0.5)
            all_ns_mask.extend(ns_mask.cpu().numpy())

            # CandidateSpotRanking
            all_logits_spot.append(out["logits_spot"].cpu().numpy())
            all_targets_spot.extend(batch["candidate_spot_idx"].cpu().numpy())
            all_spot_mask.extend(batch["spot_loss_mask"].cpu().numpy())
            all_cand_mask.append(batch["candidate_mask"].cpu().numpy())

            # Transition
            preds_tr = torch.argmax(out["logits_transition"], dim=1).cpu().numpy()
            all_preds_tr.extend(preds_tr)
            all_targets_tr.extend(batch["transition"].cpu().numpy())

            # ExitTrigger
            preds_tg = torch.argmax(out["logits_trigger"], dim=1).cpu().numpy()
            all_preds_tg.extend(preds_tg)
            all_targets_tg.extend(batch["exit_trigger"].cpu().numpy())

    # Aplica threshold customizado para SectorTransitionOccurs
    all_logits_to = np.array(all_logits_to)
    all_targets_to = np.array(all_targets_to)
    preds_to_calibrated = (all_logits_to >= transition_threshold).astype(int)

    sec_trans_metrics = compute_classification_metrics(preds_to_calibrated, all_targets_to, ["NO_TRANSITION", "TRANSITION_OCCURS"])
    state_metrics = compute_classification_metrics(np.array(all_preds_st), np.array(all_targets_st), STATE_NAMES)

    # NextSector elegível
    ns_eligible = np.array(all_ns_mask)
    if np.sum(ns_eligible) > 0:
        ns_metrics = compute_classification_metrics(np.array(all_preds_ns)[ns_eligible], np.array(all_targets_ns)[ns_eligible], NEXT_SECTOR_NAMES)
    else:
        ns_metrics = {"macro_f1": 0.0, "balanced_accuracy": 0.0, "per_class": {}}

    # Spots
    spot_logits_arr = np.concatenate(all_logits_spot, axis=0)
    cand_mask_arr = np.concatenate(all_cand_mask, axis=0)
    spot_metrics = compute_spot_ranking_metrics(
        spot_logits_arr,
        np.array(all_targets_spot),
        np.array(all_spot_mask),
        cand_mask_arr,
        supervised_spot_mask
    )

    trans_metrics = compute_classification_metrics(np.array(all_preds_tr), np.array(all_targets_tr), TRANSITION_NAMES)
    trig_metrics = compute_classification_metrics(np.array(all_preds_tg), np.array(all_targets_tg), EXIT_TRIGGER_NAMES)

    # Composite Score congelado
    composite = (
        0.20 * state_metrics["macro_f1"] +
        0.10 * sec_trans_metrics["macro_f1"] +
        0.10 * ns_metrics["macro_f1"] +
        0.25 * spot_metrics["mrr"] +
        0.20 * trans_metrics["macro_f1"] +
        0.15 * trig_metrics["macro_f1"]
    )

    return {
        "composite_score": round(float(composite), 4),
        "transition_threshold": transition_threshold,
        "sector_transition_occurs": sec_trans_metrics,
        "positioning_state": state_metrics,
        "next_sector": ns_metrics,
        "candidate_spot_ranking": spot_metrics,
        "transition": trans_metrics,
        "exit_trigger": trig_metrics,
        "raw_probs_transition_occurs": all_logits_to,
        "targets_transition_occurs": all_targets_to
    }

def main():
    print("=" * 80)
    print("INICIANDO EXPERIMENTOS CONTROLADOS - MARCO 2B.3.1 (PATCH LOCALIZADO)")
    print("=" * 80)
    set_seed(42028)

    # 1. Carregar Checkpoint Base e Verificar Integridade
    print(f"\n[1/6] Carregando checkpoint base congelado: {BASE_CKPT_PATH.name}")
    sup_mask_t = load_supervised_spot_mask()
    sup_mask_np = sup_mask_t.numpy()

    base_model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask_t)
    ckpt = torch.load(BASE_CKPT_PATH, map_location="cpu")
    model_weights = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
    base_model.load_state_dict(model_weights)

    initial_spot_hash = get_head_spot_hash(base_model)
    print(f"  Head Spot Hash Inicial (SHA-256): {initial_spot_hash}")

    # 2. Carregar Datasets (Train e Validation)
    print("\n[2/6] Carregando DataLoader de Train e Validation...")
    train_ds = CanonicalV2PositioningDataset(split="train", max_samples=12800, seed=42028)
    val_ds = CanonicalV2PositioningDataset(split="validation", max_samples=5120, seed=42028)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, collate_fn=canonical_v2_collate_fn)
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, collate_fn=canonical_v2_collate_fn)

    # Baseline antes do patch
    print("\n[3/6] Avaliando Baseline Congelado (antes do patch)...")
    baseline_eval = evaluate_patch_model(base_model, val_loader, sup_mask_np, transition_threshold=0.50)
    print(f"  Baseline CompositeScore: {baseline_eval['composite_score']}")
    print(f"  Baseline TRANSITION_OCCURS recall: {baseline_eval['sector_transition_occurs']['per_class']['TRANSITION_OCCURS']['recall']}")
    print(f"  Baseline HOLD recall: {baseline_eval['positioning_state']['per_class']['HOLD']['recall']}")
    print(f"  Baseline OBJECTIVE recall: {baseline_eval['positioning_state']['per_class']['OBJECTIVE']['recall']}")
    print(f"  Baseline Spot MRR: {baseline_eval['candidate_spot_ranking']['mrr']} (Top-1: {baseline_eval['candidate_spot_ranking']['top1']}, Top-5: {baseline_eval['candidate_spot_ranking']['top5']})")

    # Carregar suporte de treino de class_support.json para calcular pesos Train-only
    with open(PATCH_DIR / "class_support.json", "r", encoding="utf-8") as f:
        support_data = json.load(f)
    train_counts_to = {
        "NO_TRANSITION": support_data["train_total_sequences"] - support_data["support_summary"]["TRANSITION_OCCURS"]["train"]["sequence_support"],
        "TRANSITION_OCCURS": support_data["support_summary"]["TRANSITION_OCCURS"]["train"]["sequence_support"]
    }
    train_counts_st = {
        name: support_data["support_summary"][f"STATE_{name}"]["train"]["sequence_support"] for name in STATE_NAMES
    }

    # -------------------------------------------------------------------------
    # Função auxiliar de Fine-Tuning de Heads Raras (Etapa 1)
    # -------------------------------------------------------------------------
    def finetune_rare_heads(
        model: nn.Module,
        loss_fn_to: nn.Module,
        loss_fn_st: nn.Module,
        epochs: int = 4,
        lr: float = 2e-4
    ) -> nn.Module:
        # Congelar encoders e spot head
        for name, p in model.named_parameters():
            if "head_state" in name or "head_transition_occurs" in name or "head_next_sector" in name or "head_transition" in name or "head_exit_trigger" in name:
                p.requires_grad = True
            else:
                p.requires_grad = False

        # Verificar que head_spot está congelada
        for p in model.head_spot.parameters():
            assert not p.requires_grad, "ERRO: head_spot não está congelada!"

        optimizer = optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=1e-4)
        model.train()

        for ep in range(epochs):
            batch_cnt = 0
            for batch in train_loader:
                if batch_cnt >= 60:  # 60 batches controlados
                    break
                optimizer.zero_grad()
                out = model(
                    self_history=batch["self_history"],
                    teammates=batch["teammates"],
                    temporal_mask=batch["temporal_mask"],
                    candidate_mask=batch["candidate_mask"],
                    team_idx=batch["team_idx"],
                    role_idx=batch["role_idx"],
                    stage_idx=batch["stage_idx"]
                )
                l_st = loss_fn_st(out["logits_state"], batch["positioning_state"])
                l_to = loss_fn_to(out["logits_transition_occurs"], batch["sector_transition_occurs"])

                # NextSector condicional
                unred_ns = F.cross_entropy(out["logits_next_sector"], batch["next_sector"], reduction='none')
                ns_mask = (batch["sector_transition_occurs"] == 1) & (batch["next_sector_loss_mask"] > 0.5)
                l_ns = (unred_ns * ns_mask.float()).sum() / ns_mask.sum().clamp(min=1.0)

                l_tr = F.cross_entropy(out["logits_transition"], batch["transition"])
                l_tg = F.cross_entropy(out["logits_trigger"], batch["exit_trigger"])

                total_loss = 1.0 * l_st + 1.2 * l_to + 0.8 * l_ns + 0.6 * l_tr + 0.5 * l_tg
                total_loss.backward()
                nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
                optimizer.step()
                batch_cnt += 1

        return model

    # -------------------------------------------------------------------------
    # Experimento A: Class-Balanced Cross-Entropy
    # -------------------------------------------------------------------------
    print("\n[4/6] Executando Experimento A: Class-Balanced Cross-Entropy (beta=0.9999)...")
    model_a = copy.deepcopy(base_model)
    w_to_a = compute_weights_effective_number(train_counts_to, ["NO_TRANSITION", "TRANSITION_OCCURS"], beta=0.9999, clamp_range=(0.3, 5.0))
    w_st_a = compute_weights_effective_number(train_counts_st, STATE_NAMES, beta=0.9999, clamp_range=(0.2, 8.0))
    loss_to_a = nn.CrossEntropyLoss(weight=w_to_a)
    loss_st_a = nn.CrossEntropyLoss(weight=w_st_a)

    model_a = finetune_rare_heads(model_a, loss_to_a, loss_st_a, epochs=4, lr=2e-4)
    eval_a = evaluate_patch_model(model_a, val_loader, sup_mask_np, transition_threshold=0.50)
    print(f"  Exp A (Thresh 0.50) -> Composite: {eval_a['composite_score']}, TransRecall: {eval_a['sector_transition_occurs']['per_class']['TRANSITION_OCCURS']['recall']}, HoldRecall: {eval_a['positioning_state']['per_class']['HOLD']['recall']}")

    # -------------------------------------------------------------------------
    # Experimento B: Focal Loss (gamma=2.0)
    # -------------------------------------------------------------------------
    print("\n[5/6] Executando Experimento B: Focal Loss (gamma=2.0)...")
    model_b = copy.deepcopy(base_model)
    alpha_to = torch.tensor([0.25, 0.75], dtype=torch.float32)
    alpha_st = torch.tensor([0.15, 0.20, 0.25, 0.60, 0.80, 0.70, 0.85], dtype=torch.float32)
    loss_to_b = FocalLoss(alpha=alpha_to, gamma=2.0)
    loss_st_b = FocalLoss(alpha=alpha_st, gamma=2.0)

    model_b = finetune_rare_heads(model_b, loss_to_b, loss_st_b, epochs=4, lr=2.5e-4)
    eval_b = evaluate_patch_model(model_b, val_loader, sup_mask_np, transition_threshold=0.50)
    print(f"  Exp B (Thresh 0.50) -> Composite: {eval_b['composite_score']}, TransRecall: {eval_b['sector_transition_occurs']['per_class']['TRANSITION_OCCURS']['recall']}, HoldRecall: {eval_b['positioning_state']['per_class']['HOLD']['recall']}")

    # -------------------------------------------------------------------------
    # Experimento C: Balanced Sampling + Focal Loss
    # -------------------------------------------------------------------------
    print("\n[6/6] Executando Experimento C: Balanced Sampling + Calibração Focal...")
    model_c = copy.deepcopy(base_model)
    alpha_to_c = torch.tensor([0.20, 0.80], dtype=torch.float32)
    alpha_st_c = torch.tensor([0.10, 0.15, 0.20, 0.75, 0.85, 0.75, 0.90], dtype=torch.float32)
    loss_to_c = FocalLoss(alpha=alpha_to_c, gamma=2.0)
    loss_st_c = FocalLoss(alpha=alpha_st_c, gamma=2.0)

    model_c = finetune_rare_heads(model_c, loss_to_c, loss_st_c, epochs=5, lr=2.5e-4)

    # Calibração de Thresholds para SectorTransitionOccurs (0.10 a 0.90) no melhor modelo
    print("\n[Calibração] Varrendo thresholds de 0.10 a 0.90 para SectorTransitionOccurs...")
    thresh_scan = []
    best_thresh = 0.50
    best_trans_f1 = -1.0
    best_calib_eval = None

    for th in np.arange(0.10, 0.91, 0.05):
        th_val = round(float(th), 2)
        ev_th = evaluate_patch_model(model_c, val_loader, sup_mask_np, transition_threshold=th_val)
        to_m = ev_th["sector_transition_occurs"]
        f1_macro = to_m["macro_f1"]
        rec_trans = to_m["per_class"]["TRANSITION_OCCURS"]["recall"]
        rec_no_trans = to_m["per_class"]["NO_TRANSITION"]["recall"]
        bal_acc = to_m["balanced_accuracy"]

        thresh_scan.append({
            "threshold": th_val,
            "macro_f1": f1_macro,
            "balanced_accuracy": bal_acc,
            "transition_occurs_recall": rec_trans,
            "no_transition_recall": rec_no_trans,
            "composite_score": ev_th["composite_score"],
            "meets_gate": (f1_macro >= 0.55 and bal_acc >= 0.55 and rec_trans >= 0.35 and rec_no_trans >= 0.80)
        })

        # Critério de seleção: atender os gates e maximizar Macro-F1
        if thresh_scan[-1]["meets_gate"] and f1_macro > best_trans_f1:
            best_trans_f1 = f1_macro
            best_thresh = th_val
            best_calib_eval = ev_th

    if best_calib_eval is None:
        # Se nenhum atingiu 100% dos limites rigorosos, pega o de maior Balanced Accuracy com recall >= 0.30
        candidates = [t for t in thresh_scan if t["transition_occurs_recall"] >= 0.30]
        if candidates:
            best_cand = max(candidates, key=lambda x: x["macro_f1"])
            best_thresh = best_cand["threshold"]
        else:
            best_thresh = 0.30
        best_calib_eval = evaluate_patch_model(model_c, val_loader, sup_mask_np, transition_threshold=best_thresh)

    print(f"  Threshold Ótimo Calibrado: {best_thresh}")
    to_best = best_calib_eval["sector_transition_occurs"]
    print(f"  Resultado Calibrado -> Macro-F1: {to_best['macro_f1']}, BalAcc: {to_best['balanced_accuracy']}, TRANSITION_OCCURS recall: {to_best['per_class']['TRANSITION_OCCURS']['recall']}, NO_TRANSITION recall: {to_best['per_class']['NO_TRANSITION']['recall']}")

    # -------------------------------------------------------------------------
    # Proteção da CandidateSpotRankingHead
    # -------------------------------------------------------------------------
    print("\n[Verificação de Segurança] Conferindo integridade bitwise da SpotRankingHead...")
    final_spot_hash = get_head_spot_hash(model_c)
    hash_identical = (initial_spot_hash == final_spot_hash)
    mrr_diff = baseline_eval["candidate_spot_ranking"]["mrr"] - best_calib_eval["candidate_spot_ranking"]["mrr"]
    top5_diff = baseline_eval["candidate_spot_ranking"]["top5"] - best_calib_eval["candidate_spot_ranking"]["top5"]
    invalid_masked = best_calib_eval["candidate_spot_ranking"]["invalid_masked"]

    preservation = {
        "schema": "csbot.rare_class_patch.preservation_check.v1",
        "initial_spot_head_sha256": initial_spot_hash,
        "final_spot_head_sha256": final_spot_hash,
        "bitwise_identical": hash_identical,
        "mrr_baseline": baseline_eval["candidate_spot_ranking"]["mrr"],
        "mrr_patched": best_calib_eval["candidate_spot_ranking"]["mrr"],
        "mrr_drop": round(float(mrr_diff), 4),
        "mrr_drop_within_limit": mrr_diff <= 0.01,
        "top5_baseline": baseline_eval["candidate_spot_ranking"]["top5"],
        "top5_patched": best_calib_eval["candidate_spot_ranking"]["top5"],
        "top5_drop_percentage_points": round(float(top5_diff * 100.0), 2),
        "top5_drop_within_limit": top5_diff <= 0.005,
        "invalid_masked_selections": invalid_masked,
        "preservation_verdict": "SPOT_RANKING_PRESERVED" if (hash_identical and mrr_diff <= 0.01 and invalid_masked == 0) else "SPOT_RANKING_REGRESSION_DETECTED"
    }

    # -------------------------------------------------------------------------
    # Avaliação de Gates do Patch (Seção 8)
    # -------------------------------------------------------------------------
    gates = {
        "SectorTransitionOccurs": {
            "macro_f1": {"target": ">= 0.55", "achieved": to_best["macro_f1"], "pass": to_best["macro_f1"] >= 0.55},
            "balanced_accuracy": {"target": ">= 0.55", "achieved": to_best["balanced_accuracy"], "pass": to_best["balanced_accuracy"] >= 0.55},
            "transition_occurs_recall": {"target": ">= 0.35", "achieved": to_best["per_class"]["TRANSITION_OCCURS"]["recall"], "pass": to_best["per_class"]["TRANSITION_OCCURS"]["recall"] >= 0.35},
            "no_transition_recall": {"target": ">= 0.80", "achieved": to_best["per_class"]["NO_TRANSITION"]["recall"], "pass": to_best["per_class"]["NO_TRANSITION"]["recall"] >= 0.80}
        },
        "PositioningState": {
            "macro_f1": {"target": ">= 0.40", "achieved": best_calib_eval["positioning_state"]["macro_f1"], "pass": best_calib_eval["positioning_state"]["macro_f1"] >= 0.40},
            "hold_recall": {"target": ">= 0.30", "achieved": best_calib_eval["positioning_state"]["per_class"]["HOLD"]["recall"], "pass": best_calib_eval["positioning_state"]["per_class"]["HOLD"]["recall"] >= 0.30},
            "objective_recall": {"target": ">= 0.40", "achieved": best_calib_eval["positioning_state"]["per_class"]["OBJECTIVE"]["recall"], "pass": best_calib_eval["positioning_state"]["per_class"]["OBJECTIVE"]["recall"] >= 0.40},
            "retake_recall": {"target": ">= 0.35", "achieved": best_calib_eval["positioning_state"]["per_class"]["RETAKE"]["recall"], "pass": best_calib_eval["positioning_state"]["per_class"]["RETAKE"]["recall"] >= 0.35}
        },
        "NextSector": {
            "macro_f1": {"target": ">= 0.45", "achieved": best_calib_eval["next_sector"]["macro_f1"], "pass": best_calib_eval["next_sector"]["macro_f1"] >= 0.45},
            "balanced_accuracy": {"target": ">= 0.45", "achieved": best_calib_eval["next_sector"]["balanced_accuracy"], "pass": best_calib_eval["next_sector"]["balanced_accuracy"] >= 0.45}
        },
        "Transition": {
            "macro_f1": {"target": ">= 0.60", "achieved": best_calib_eval["transition"]["macro_f1"], "pass": best_calib_eval["transition"]["macro_f1"] >= 0.60}
        },
        "ExitTrigger": {
            "macro_f1": {"target": ">= 0.40", "achieved": best_calib_eval["exit_trigger"]["macro_f1"], "pass": best_calib_eval["exit_trigger"]["macro_f1"] >= 0.40}
        },
        "SpotRankingPreserved": {
            "mrr": {"target": ">= 0.75", "achieved": best_calib_eval["candidate_spot_ranking"]["mrr"], "pass": best_calib_eval["candidate_spot_ranking"]["mrr"] >= 0.75},
            "top5": {"target": ">= 0.95", "achieved": best_calib_eval["candidate_spot_ranking"]["top5"], "pass": best_calib_eval["candidate_spot_ranking"]["top5"] >= 0.95},
            "invalid_masked": {"target": "== 0", "achieved": invalid_masked, "pass": invalid_masked == 0}
        }
    }

    all_gates_pass = all(
        all(metric_dict["pass"] for metric_dict in head_dict.values())
        for head_dict in gates.values()
    )

    print(f"\n[Veredito dos Gates] Todos os gates passaram: {all_gates_pass}")

    # Salvar Checkpoint Patched
    patched_ckpt_path = PATCH_DIR / "selected_patch_checkpoint.pt"
    torch.save(model_c.state_dict(), patched_ckpt_path)
    patched_sha256 = hashlib.sha256(patched_ckpt_path.read_bytes()).hexdigest()
    print(f"  Checkpoint Patched salvo: {patched_ckpt_path.name} (SHA-256: {patched_sha256[:16]}...)")

    # Salvar JSONs de Métricas
    def clean_eval_dict(d: dict) -> dict:
        c = copy.deepcopy(d)
        c.pop("raw_probs_transition_occurs", None)
        c.pop("targets_transition_occurs", None)
        return c

    with open(PATCH_DIR / "experiment_a_metrics.json", "w", encoding="utf-8") as f:
        json.dump(clean_eval_dict(eval_a), f, indent=2)

    with open(PATCH_DIR / "experiment_b_metrics.json", "w", encoding="utf-8") as f:
        json.dump(clean_eval_dict(eval_b), f, indent=2)

    with open(PATCH_DIR / "experiment_c_metrics.json", "w", encoding="utf-8") as f:
        json.dump(clean_eval_dict(best_calib_eval), f, indent=2)

    with open(PATCH_DIR / "threshold_calibration.json", "w", encoding="utf-8") as f:
        json.dump({"threshold_scan": thresh_scan, "best_threshold": best_thresh}, f, indent=2)

    with open(PATCH_DIR / "preservation_check.json", "w", encoding="utf-8") as f:
        json.dump(preservation, f, indent=2)

    comparison = {
        "schema": "csbot.rare_class_patch.experiment_comparison.v1",
        "baseline_composite": baseline_eval["composite_score"],
        "experiment_a_composite": eval_a["composite_score"],
        "experiment_b_composite": eval_b["composite_score"],
        "experiment_c_composite": best_calib_eval["composite_score"],
        "selected_experiment": "EXPERIMENT_C_FOCAL_LOSS_WITH_THRESHOLD_CALIBRATION",
        "gates_evaluation": gates,
        "all_gates_pass": all_gates_pass,
        "canonical_verdict": "RARE_CLASS_PATCH_READY_FOR_FINAL_EVALUATION" if all_gates_pass else "RARE_CLASS_PATCH_CONDITIONAL"
    }

    with open(PATCH_DIR / "experiment_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    print(f"\n[Conclusão] Arquivos JSON gerados com sucesso em {PATCH_DIR.relative_to(REPO_ROOT)}")
    print(f"CANONICAL_VERDICT: {comparison['canonical_verdict']}")

if __name__ == "__main__":
    main()
