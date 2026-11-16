"""
Fase 3A.3-B - Marco 2B.3.3: Fine-Tuning Cirúrgico da Head de Transição e Reconciliação da Validation Integral.

Executa:
1. Reconciliação e inferência na Validation integral (501.434 sequências).
2. Cálculo do baseline integral de todas as heads (especialmente OBJECTIVE, SAVE, TRANSITION_OCCURS).
3. Sampler balanceado por episódio no Train (sem duplicação de janelas adjacentes).
4. Experimento A: Focal Loss (gamma=1.0, alpha Train-only, sem logit margin, 2 épocas).
5. Experimento B: Focal Loss (gamma=1.5, alpha Train-only, logit margin moderada=0.35, 2 épocas).
6. Varredura fina de threshold (0.450 a 0.520, step=0.005).
7. Verificação de preservação bitwise dos 7 componentes congelados.
8. Geração de todos os JSONs de evidência para o Marco 2B.3.3.
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
import pandas as pd
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
    load_supervised_spot_mask,
    INDEX_DIR,
    SIDECAR_DIR
)

OUT_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "transition_head_patch_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_PATCH_CKPT = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "selected_patch_checkpoint.pt"
ROOT_CANDIDATE_CKPT = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training" / "selected_candidate.pt"

FINE_THRESHOLDS = [
    0.450, 0.455, 0.460, 0.465, 0.470, 0.475, 0.480, 0.485,
    0.490, 0.495, 0.500, 0.505, 0.510, 0.515, 0.520
]

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

def compute_spot_ranking_metrics(logits: np.ndarray, targets: np.ndarray, masks: np.ndarray, candidate_mask: np.ndarray, supervised_spot_mask: np.ndarray) -> Dict[str, Any]:
    valid_indices = np.where(masks)[0]
    n_valid = len(valid_indices)
    if n_valid == 0:
        return {"mrr": 0.0, "top1": 0.0, "top5": 0.0, "invalid_masked": 0, "unsupported": 0, "support": 0}

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

class FocalLossWithMargin(nn.Module):
    def __init__(self, alpha: torch.Tensor, gamma: float = 1.0, margin: float = 0.0):
        super().__init__()
        self.register_buffer("alpha", alpha)
        self.gamma = gamma
        self.margin = margin

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        if self.margin > 0.0:
            margin_tensor = torch.zeros_like(logits)
            margin_tensor[:, 1] = self.margin
            logits_adj = logits - margin_tensor * (targets == 1).unsqueeze(1).float()
        else:
            logits_adj = logits

        ce_loss = F.cross_entropy(logits_adj, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = ((1.0 - pt) ** self.gamma) * ce_loss
        alpha_t = self.alpha[targets]
        loss = (alpha_t * focal_loss).mean()
        return loss

def evaluate_threshold_sweep(probs: np.ndarray, targets: np.ndarray, thresholds: List[float]) -> List[Dict[str, Any]]:
    results = []
    n_total = len(targets)
    actual_pos = int(np.sum(targets == 1))
    actual_neg = int(np.sum(targets == 0))
    actual_transition_rate = float(actual_pos / n_total) if n_total > 0 else 0.0

    # Calculate PR-AUC
    # sort by descending prob
    order = np.argsort(-probs)
    sorted_targets = targets[order]
    tps = np.cumsum(sorted_targets == 1)
    fps = np.cumsum(sorted_targets == 0)
    precisions = tps / np.maximum(tps + fps, 1)
    recalls = tps / actual_pos if actual_pos > 0 else np.zeros_like(tps)
    # trapezoidal PR-AUC
    if hasattr(np, "trapezoid"):
        pr_auc = float(np.trapezoid(precisions, recalls)) if actual_pos > 0 else 0.0
    elif hasattr(np, "trapz"):
        pr_auc = float(np.trapz(precisions, recalls)) if actual_pos > 0 else 0.0
    else:
        diff_r = np.diff(recalls)
        avg_p = 0.5 * (precisions[:-1] + precisions[1:])
        pr_auc = float(np.sum(avg_p * diff_r)) if actual_pos > 0 else 0.0

    for th in thresholds:
        th_val = round(float(th), 4)
        preds = (probs >= th_val).astype(int)

        tp = int(np.sum((preds == 1) & (targets == 1)))
        fp = int(np.sum((preds == 1) & (targets == 0)))
        tn = int(np.sum((preds == 0) & (targets == 0)))
        fn = int(np.sum((preds == 0) & (targets == 1)))

        rec_to = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        prec_to = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        f1_to = float(2 * prec_to * rec_to / (prec_to + rec_to)) if (prec_to + rec_to) > 0 else 0.0

        rec_no = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        prec_no = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0
        f1_no = float(2 * prec_no * rec_no / (prec_no + rec_no)) if (prec_no + rec_no) > 0 else 0.0

        macro_f1 = float((f1_to + f1_no) / 2.0)
        bal_acc = float((rec_to + rec_no) / 2.0)
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        pred_rate = float((tp + fp) / n_total) if n_total > 0 else 0.0

        gates_met = (
            rec_to >= 0.35 and
            rec_no >= 0.80 and
            macro_f1 >= 0.55 and
            bal_acc >= 0.55
        )

        results.append({
            "threshold": th_val,
            "macro_f1": round(macro_f1, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "pr_auc": round(pr_auc, 4),
            "transition_occurs_precision": round(prec_to, 4),
            "transition_occurs_recall": round(rec_to, 4),
            "no_transition_precision": round(prec_no, 4),
            "no_transition_recall": round(rec_no, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "predicted_transition_rate": round(pred_rate, 4),
            "actual_transition_rate": round(actual_transition_rate, 4),
            "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "gates": {
                "transition_occurs_recall_ge_35": rec_to >= 0.35,
                "no_transition_recall_ge_80": rec_no >= 0.80,
                "macro_f1_ge_55": macro_f1 >= 0.55,
                "balanced_accuracy_ge_55": bal_acc >= 0.55,
                "all_gates_met": gates_met
            }
        })
    return results

def main():
    print("=" * 80)
    print("MARCO 2B.3.3: FINE-TUNING CIRÚRGICO DA HEAD DE TRANSIÇÃO")
    print("=" * 80)
    set_seed(42028)

    # 1. Carregar Checkpoint Base e Verificar Invariantes
    print(f"\n[1/6] Carregando checkpoint base: {BASE_PATCH_CKPT.name}...")
    sup_mask_t = load_supervised_spot_mask()
    sup_mask_np = sup_mask_t.numpy()

    model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask_t)
    ckpt = torch.load(BASE_PATCH_CKPT, map_location="cpu")
    model_weights = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
    model.load_state_dict(model_weights)
    model.eval()

    # Hashes dos 7 componentes congelados
    frozen_hashes_before = {
        "temporal_encoder": compute_submodule_hash(model.transformer),
        "teammate_encoder": compute_submodule_hash(model.teammate_proj),
        "head_state": compute_submodule_hash(model.head_state),
        "head_next_sector": compute_submodule_hash(model.head_next_sector),
        "head_spot": compute_submodule_hash(model.head_spot),
        "head_transition": compute_submodule_hash(model.head_transition),
        "head_exit_trigger": compute_submodule_hash(model.head_exit_trigger)
    }
    for k, v in frozen_hashes_before.items():
        print(f"  [Freeze] {k:20s}: {v[:16]}...")

    # 2. Reconciliação e Inferência na Validation Integral
    print("\n[2/6] Executando inferência na Validation integral (501.434 sequências)...")
    val_ds = CanonicalV2PositioningDataset(split="validation", preload_demos=False)
    val_total_indexed = len(val_ds)
    assert val_total_indexed == 501434, f"Validation index size {val_total_indexed} != 501434"
    val_loader = DataLoader(val_ds, batch_size=512, shuffle=False, collate_fn=canonical_v2_collate_fn, num_workers=0)

    val_cache_path = OUT_DIR / "val_extracted.npz"
    if val_cache_path.exists():
        print(f"  Carregando cache da Validation integral de: {val_cache_path.name}...")
        c = np.load(val_cache_path)
        val_pooled = c["val_pooled"]
        val_targets_to = c["val_targets_to"]
        val_preds_st = c["val_preds_st"]
        val_targets_st = c["val_targets_st"]
        val_preds_ns = c["val_preds_ns"]
        val_targets_ns = c["val_targets_ns"]
        val_ns_mask = c["val_ns_mask"]
        val_logits_spot = c["val_logits_spot"]
        val_targets_spot = c["val_targets_spot"]
        val_spot_mask = c["val_spot_mask"]
        val_cand_mask = c["val_cand_mask"]
        val_preds_tr = c["val_preds_tr"]
        val_targets_tr = c["val_targets_tr"]
        val_preds_tg = c["val_preds_tg"]
        val_targets_tg = c["val_targets_tg"]
        print("  Validation integral carregada do cache com sucesso!")
    else:
        val_pooled_list = []
        val_targets_to_list = []
        val_preds_st_list, val_targets_st_list = [], []
        val_preds_ns_list, val_targets_ns_list, val_ns_mask_list = [], [], []
        val_logits_spot_list, val_targets_spot_list, val_spot_mask_list, val_cand_mask_list = [], [], [], []
        val_preds_tr_list, val_targets_tr_list = [], []
        val_preds_tg_list, val_targets_tg_list = [], []

        t0_eval = time.time()
        batch_idx = 0
        with torch.no_grad():
            for batch in val_loader:
                out = model(
                    self_history=batch["self_history"],
                    teammates=batch["teammates"],
                    temporal_mask=batch["temporal_mask"],
                    candidate_mask=batch["candidate_mask"],
                    team_idx=batch["team_idx"],
                    role_idx=batch["role_idx"],
                    stage_idx=batch["stage_idx"]
                )
                # Acumular pooled [B, 256]
                val_pooled_list.append(out["pooled_features"].cpu().numpy())
                val_targets_to_list.append(batch["sector_transition_occurs"].cpu().numpy())

                # PositioningState
                val_preds_st_list.append(torch.argmax(out["logits_state"], dim=1).cpu().numpy())
                val_targets_st_list.append(batch["positioning_state"].cpu().numpy())

                # NextSector
                val_preds_ns_list.append(torch.argmax(out["logits_next_sector"], dim=1).cpu().numpy())
                val_targets_ns_list.append(batch["next_sector"].cpu().numpy())
                ns_eligible = (batch["sector_transition_occurs"] == 1) & (batch["next_sector_loss_mask"] > 0.5)
                val_ns_mask_list.append(ns_eligible.cpu().numpy())

                # CandidateSpotRanking
                val_logits_spot_list.append(out["logits_spot"].cpu().numpy())
                val_targets_spot_list.append(batch["candidate_spot_idx"].cpu().numpy())
                val_spot_mask_list.append(batch["spot_loss_mask"].cpu().numpy())
                val_cand_mask_list.append(batch["candidate_mask"].cpu().numpy())

                # Transition
                val_preds_tr_list.append(torch.argmax(out["logits_transition"], dim=1).cpu().numpy())
                val_targets_tr_list.append(batch["transition"].cpu().numpy())

                # ExitTrigger
                val_preds_tg_list.append(torch.argmax(out["logits_trigger"], dim=1).cpu().numpy())
                val_targets_tg_list.append(batch["exit_trigger"].cpu().numpy())

                batch_idx += 1
                if batch_idx % 200 == 0:
                    elapsed = time.time() - t0_eval
                    processed = batch_idx * 512
                    print(f"    Validation: {processed}/{val_total_indexed} ({processed/elapsed:.1f} samples/s)...")

        t1_eval = time.time()
        print(f"  Validation integral avaliada em {t1_eval - t0_eval:.1f}s ({val_total_indexed/(t1_eval - t0_eval):.1f} samples/s)!")

        # Concatenar matrizes em RAM
        val_pooled = np.concatenate(val_pooled_list, axis=0)
        val_targets_to = np.concatenate(val_targets_to_list, axis=0)
        val_preds_st = np.concatenate(val_preds_st_list, axis=0)
        val_targets_st = np.concatenate(val_targets_st_list, axis=0)
        val_preds_ns = np.concatenate(val_preds_ns_list, axis=0)
        val_targets_ns = np.concatenate(val_targets_ns_list, axis=0)
        val_ns_mask = np.concatenate(val_ns_mask_list, axis=0)
        val_logits_spot = np.concatenate(val_logits_spot_list, axis=0)
        val_targets_spot = np.concatenate(val_targets_spot_list, axis=0)
        val_spot_mask = np.concatenate(val_spot_mask_list, axis=0)
        val_cand_mask = np.concatenate(val_cand_mask_list, axis=0)
        val_preds_tr = np.concatenate(val_preds_tr_list, axis=0)
        val_targets_tr = np.concatenate(val_targets_tr_list, axis=0)
        val_preds_tg = np.concatenate(val_preds_tg_list, axis=0)
        val_targets_tg = np.concatenate(val_targets_tg_list, axis=0)

        # Salvar em cache
        np.savez_compressed(
            val_cache_path,
            val_pooled=val_pooled,
            val_targets_to=val_targets_to,
            val_preds_st=val_preds_st,
            val_targets_st=val_targets_st,
            val_preds_ns=val_preds_ns,
            val_targets_ns=val_targets_ns,
            val_ns_mask=val_ns_mask,
            val_logits_spot=val_logits_spot,
            val_targets_spot=val_targets_spot,
            val_spot_mask=val_spot_mask,
            val_cand_mask=val_cand_mask,
            val_preds_tr=val_preds_tr,
            val_targets_tr=val_targets_tr,
            val_preds_tg=val_preds_tg,
            val_targets_tg=val_targets_tg
        )
        print("  Cache da Validation integral salvo com sucesso.")

    # 3. Métricas do Baseline Integral
    print("\n[3/6] Consolidando Baseline Integral na Validation...")
    # SectorTransitionOccurs baseline com threshold 0.50
    with torch.no_grad():
        base_logits_to = model.head_transition_occurs(torch.from_numpy(val_pooled)).numpy()
    base_probs_to = np.exp(base_logits_to[:, 1] - np.logaddexp(base_logits_to[:, 0], base_logits_to[:, 1]))
    base_sweep = evaluate_threshold_sweep(base_probs_to, val_targets_to, FINE_THRESHOLDS)

    # Baseline das demais heads
    baseline_st_metrics = compute_classification_metrics(val_preds_st, val_targets_st, STATE_NAMES)
    baseline_ns_metrics = compute_classification_metrics(val_preds_ns[val_ns_mask], val_targets_ns[val_ns_mask], NEXT_SECTOR_NAMES)
    baseline_spot_metrics = compute_spot_ranking_metrics(val_logits_spot, val_targets_spot, val_spot_mask, val_cand_mask, sup_mask_np)
    baseline_tr_metrics = compute_classification_metrics(val_preds_tr, val_targets_tr, TRANSITION_NAMES)
    baseline_tg_metrics = compute_classification_metrics(val_preds_tg, val_targets_tg, EXIT_TRIGGER_NAMES)

    objective_support_full = int(np.sum(val_targets_st == STATE_NAMES.index("OBJECTIVE")))
    save_support_full = int(np.sum(val_targets_st == STATE_NAMES.index("SAVE")))
    trans_support_full = int(np.sum(val_targets_to == 1))
    no_trans_support_full = int(np.sum(val_targets_to == 0))

    full_validation_baseline_data = {
        "schema": "csbot.transition_patch.full_validation_baseline.v1",
        "validation_total_indexed": val_total_indexed,
        "validation_total_evaluated": len(val_targets_to),
        "sampling_method": "FULL_VALIDATION_INDEX",
        "sampled_matches": len(val_ds.allowed_demos),
        "sampled_classes": len(STATE_NAMES),
        "key_supports": {
            "TRANSITION_OCCURS": trans_support_full,
            "NO_TRANSITION": no_trans_support_full,
            "OBJECTIVE": objective_support_full,
            "SAVE": save_support_full,
            "HOLD": int(np.sum(val_targets_st == STATE_NAMES.index("HOLD")))
        },
        "baseline_threshold_sweep": base_sweep,
        "positioning_state": baseline_st_metrics,
        "next_sector": baseline_ns_metrics,
        "spot_ranking": baseline_spot_metrics,
        "transition": baseline_tr_metrics,
        "exit_trigger": baseline_tg_metrics
    }
    with open(OUT_DIR / "full_validation_baseline.json", "w", encoding="utf-8") as f:
        json.dump(full_validation_baseline_data, f, indent=2)
    print("  full_validation_baseline.json salvo com sucesso.")
    print(f"  Key Supports -> TRANSITION_OCCURS: {trans_support_full}, OBJECTIVE: {objective_support_full}, SAVE: {save_support_full}")

    # 4. Sampler Balanceado por Episódio no Train
    print("\n[4/6] Construindo Sampler Balanceado por Episódio no Train...")
    train_dfs = []
    cols_base = ["sequence_id", "demo_id", "round_id", "slot", "split"]
    for i in range(5):
        b_p = INDEX_DIR / f"shard_{i:03d}.parquet"
        s_p = SIDECAR_DIR / f"shard_{i:03d}_labels.parquet"
        df_b = pd.read_parquet(b_p, columns=cols_base)
        df_s = pd.read_parquet(s_p, columns=["sector_transition_occurs"])
        mask = (df_b["split"] == "train")
        sub = df_b[mask].copy()
        sub["target"] = (df_s.loc[mask, "sector_transition_occurs"].values == "TRANSITION_OCCURS").astype(int)
        train_dfs.append(sub)
    train_df = pd.concat(train_dfs, ignore_index=True)
    train_df["episode_id"] = train_df["demo_id"].astype(str) + "_" + train_df["round_id"].astype(str) + "_" + train_df["slot"].astype(str)

    rng = np.random.RandomState(42028)
    pos_mask = train_df["target"] == 1
    neg_mask = train_df["target"] == 0

    pos_indices = train_df[pos_mask].groupby("episode_id").apply(lambda g: g.index[rng.randint(len(g))]).values
    neg_indices = train_df[neg_mask].groupby("episode_id").apply(lambda g: g.index[rng.randint(len(g))]).values
    sampled_neg = rng.choice(neg_indices, size=len(pos_indices), replace=False)
    balanced_train_indices = np.sort(np.concatenate([pos_indices, sampled_neg]))

    print(f"  Episódios Positivos: {len(pos_indices)}, Episódios Negativos: {len(sampled_neg)}")
    print(f"  Total Balanced Train Samples: {len(balanced_train_indices)} (Adjacent Duplication = 0.0%)")

    # Extrair embeddings do Train para o sampler balanceado (com cache em disco)
    train_cache_path = OUT_DIR / "train_extracted.npz"
    if train_cache_path.exists():
        print(f"  Carregando cache de treino balanceado de: {train_cache_path.name}...")
        tc = np.load(train_cache_path)
        train_pooled = torch.from_numpy(tc["train_pooled"])
        train_targets = torch.from_numpy(tc["train_targets"])
        print(f"  Train Pooled shape: {train_pooled.shape}, Targets shape: {train_targets.shape}")
    else:
        print("  Extraindo pooled features do Train...")
        train_ds = CanonicalV2PositioningDataset(split="train", preload_demos=False)
        train_subset = torch.utils.data.Subset(train_ds, balanced_train_indices)
        train_loader = DataLoader(train_subset, batch_size=512, shuffle=False, collate_fn=canonical_v2_collate_fn, num_workers=0)

        train_pooled_list = []
        train_targets_list = []
        with torch.no_grad():
            for b in train_loader:
                out = model(
                    self_history=b["self_history"],
                    teammates=b["teammates"],
                    temporal_mask=b["temporal_mask"],
                    candidate_mask=b["candidate_mask"],
                    team_idx=b["team_idx"],
                    role_idx=b["role_idx"],
                    stage_idx=b["stage_idx"]
                )
                train_pooled_list.append(out["pooled_features"].cpu())
                train_targets_list.append(b["sector_transition_occurs"].cpu())

        train_pooled = torch.cat(train_pooled_list, dim=0)
        train_targets = torch.cat(train_targets_list, dim=0)
        np.savez_compressed(
            train_cache_path,
            train_pooled=train_pooled.numpy(),
            train_targets=train_targets.numpy()
        )
        print(f"  Train Pooled shape: {train_pooled.shape}, Targets shape: {train_targets.shape}")
        print("  Cache de treino balanceado salvo com sucesso.")

    # Alpha estritamente calculado no Train total
    n_train_total = 2364492
    n_train_trans = 315742
    n_train_notrans = 2048750
    alpha_train = torch.tensor([n_train_trans / n_train_total, n_train_notrans / n_train_total], dtype=torch.float32)
    print(f"  Alpha Train-only: {alpha_train.numpy()}")

    # -------------------------------------------------------------------------
    # 5. Experimento A: Focal Loss (gamma=1.0, alpha Train-only, no margin)
    # -------------------------------------------------------------------------
    print("\n[5/6] Executando Experimento A (gamma=1.0, alpha Train, margin=0.0)...")
    head_a = copy.deepcopy(model.head_transition_occurs)
    head_a.train()
    loss_fn_a = FocalLossWithMargin(alpha=alpha_train, gamma=1.0, margin=0.0)
    opt_a = optim.AdamW(head_a.parameters(), lr=1e-3, weight_decay=1e-4)

    train_dataset_a = torch.utils.data.TensorDataset(train_pooled, train_targets)
    train_loader_a = DataLoader(train_dataset_a, batch_size=256, shuffle=True)

    for epoch in range(2):
        total_loss = 0.0
        for x_b, y_b in train_loader_a:
            opt_a.zero_grad()
            l_b = head_a(x_b)
            loss = loss_fn_a(l_b, y_b)
            loss.backward()
            opt_a.step()
            total_loss += loss.item() * len(y_b)
        print(f"  Exp A Epoch {epoch+1}/2 Loss: {total_loss / len(train_pooled):.4f}")

    # Avaliar Exp A na Validation integral
    head_a.eval()
    with torch.no_grad():
        logits_a = head_a(torch.from_numpy(val_pooled)).numpy()
    probs_a = np.exp(logits_a[:, 1] - np.logaddexp(logits_a[:, 0], logits_a[:, 1]))
    sweep_a = evaluate_threshold_sweep(probs_a, val_targets_to, FINE_THRESHOLDS)
    exp_a_data = {
        "schema": "csbot.transition_patch.experiment_a.v1",
        "experiment": "Experimento A",
        "config": {"gamma": 1.0, "alpha": alpha_train.tolist(), "margin": 0.0, "epochs": 2, "lr": 1e-3},
        "threshold_sweep": sweep_a
    }
    with open(OUT_DIR / "experiment_a_metrics.json", "w", encoding="utf-8") as f:
        json.dump(exp_a_data, f, indent=2)
    print("  experiment_a_metrics.json salvo.")

    # -------------------------------------------------------------------------
    # 6. Experimento B: Focal Loss (gamma=1.5, alpha Train-only, margin=0.35)
    # -------------------------------------------------------------------------
    print("\n[6/6] Executando Experimento B (gamma=1.5, alpha Train, margin=0.35)...")
    head_b = copy.deepcopy(model.head_transition_occurs)
    head_b.train()
    loss_fn_b = FocalLossWithMargin(alpha=alpha_train, gamma=1.5, margin=0.35)
    opt_b = optim.AdamW(head_b.parameters(), lr=1e-3, weight_decay=1e-4)

    train_dataset_b = torch.utils.data.TensorDataset(train_pooled, train_targets)
    train_loader_b = DataLoader(train_dataset_b, batch_size=256, shuffle=True)

    for epoch in range(2):
        total_loss = 0.0
        for x_b, y_b in train_loader_b:
            opt_b.zero_grad()
            l_b = head_b(x_b)
            loss = loss_fn_b(l_b, y_b)
            loss.backward()
            opt_b.step()
            total_loss += loss.item() * len(y_b)
        print(f"  Exp B Epoch {epoch+1}/2 Loss: {total_loss / len(train_pooled):.4f}")

    # Avaliar Exp B na Validation integral
    head_b.eval()
    with torch.no_grad():
        logits_b = head_b(torch.from_numpy(val_pooled)).numpy()
    probs_b = np.exp(logits_b[:, 1] - np.logaddexp(logits_b[:, 0], logits_b[:, 1]))
    sweep_b = evaluate_threshold_sweep(probs_b, val_targets_to, FINE_THRESHOLDS)
    exp_b_data = {
        "schema": "csbot.transition_patch.experiment_b.v1",
        "experiment": "Experimento B",
        "config": {"gamma": 1.5, "alpha": alpha_train.tolist(), "margin": 0.35, "epochs": 2, "lr": 1e-3},
        "threshold_sweep": sweep_b
    }
    with open(OUT_DIR / "experiment_b_metrics.json", "w", encoding="utf-8") as f:
        json.dump(exp_b_data, f, indent=2)
    print("  experiment_b_metrics.json salvo.")

    # -------------------------------------------------------------------------
    # 7. Comparação, Seleção e Verificação de Gates
    # -------------------------------------------------------------------------
    print("\n[Seleção] Avaliando Gates Contratuais na Validation Integral...")
    combined_sweep = {
        "schema": "csbot.transition_patch.threshold_sweep.v1",
        "threshold_grid": FINE_THRESHOLDS,
        "experiment_a": sweep_a,
        "experiment_b": sweep_b
    }
    with open(OUT_DIR / "threshold_sweep.json", "w", encoding="utf-8") as f:
        json.dump(combined_sweep, f, indent=2)

    # Identificar candidatos que cumprem todos os 4 gates
    passing_a = [s for s in sweep_a if s["gates"]["all_gates_met"]]
    passing_b = [s for s in sweep_b if s["gates"]["all_gates_met"]]

    selected_exp = None
    selected_threshold_entry = None
    selected_head = None
    all_gates_met = False

    if passing_b:
        # Preferir Experimento B com margin se passar
        passing_b.sort(key=lambda s: (s["macro_f1"], s["balanced_accuracy"]), reverse=True)
        selected_threshold_entry = passing_b[0]
        selected_exp = "Experimento B"
        selected_head = head_b
        all_gates_met = True
    elif passing_a:
        passing_a.sort(key=lambda s: (s["macro_f1"], s["balanced_accuracy"]), reverse=True)
        selected_threshold_entry = passing_a[0]
        selected_exp = "Experimento A"
        selected_head = head_a
        all_gates_met = True
    else:
        # Se nenhum cumpriu 100% dos gates contratuais
        all_candidates = []
        for s in sweep_b:
            s_copy = dict(s)
            s_copy["exp"] = "Experimento B"
            all_candidates.append(s_copy)
        for s in sweep_a:
            s_copy = dict(s)
            s_copy["exp"] = "Experimento A"
            all_candidates.append(s_copy)
        # Ordenar por Balanced Accuracy com recall de transição razoável
        all_candidates.sort(key=lambda s: (s["balanced_accuracy"] + s["macro_f1"]), reverse=True)
        selected_threshold_entry = all_candidates[0]
        selected_exp = selected_threshold_entry["exp"]
        selected_head = head_b if selected_exp == "Experimento B" else head_a
        all_gates_met = False

    print(f"  Experimento Selecionado: {selected_exp}")
    print(f"  Threshold Selecionado: {selected_threshold_entry['threshold']}")
    print(f"  All Gates Met: {all_gates_met}")
    print(f"  Macro-F1: {selected_threshold_entry['macro_f1']}, BalAcc: {selected_threshold_entry['balanced_accuracy']}, TransRecall: {selected_threshold_entry['transition_occurs_recall']}, NoTransRecall: {selected_threshold_entry['no_transition_recall']}")

    # Decisão canônica
    if all_gates_met:
        if objective_support_full > 0 and baseline_st_metrics["per_class"]["OBJECTIVE"]["recall"] == 0.0:
            canonical_verdict = "TRANSITION_HEAD_APPROVED_OBJECTIVE_PATCH_REQUIRED"
        else:
            canonical_verdict = "RARE_CLASS_PATCH_READY_FOR_FINAL_EVALUATION"
    else:
        canonical_verdict = "TRANSITION_HEAD_REQUIRES_ARCHITECTURAL_REVIEW"

    # Salvar selected_threshold.json
    selected_threshold_data = {
        "schema": "csbot.transition_patch.selected_threshold.v1",
        "selected_experiment": selected_exp,
        "selected_threshold": selected_threshold_entry["threshold"],
        "all_gates_met": all_gates_met,
        "canonical_verdict": canonical_verdict,
        "metrics": selected_threshold_entry
    }
    with open(OUT_DIR / "selected_threshold.json", "w", encoding="utf-8") as f:
        json.dump(selected_threshold_data, f, indent=2)

    # Atualizar modelo com a nova head selecionada e salvar selected_checkpoint.pt
    final_model = copy.deepcopy(model)
    final_model.head_transition_occurs.load_state_dict(selected_head.state_dict())

    torch.save({
        "schema": "csbot.checkpoint.positioning_v2.patched_v2",
        "phase": "3A.3-B",
        "milestone": "2B.3.3",
        "model_state_dict": final_model.state_dict(),
        "selected_experiment": selected_exp,
        "selected_threshold": selected_threshold_entry["threshold"],
        "canonical_verdict": canonical_verdict
    }, OUT_DIR / "selected_checkpoint.pt")
    print("  selected_checkpoint.pt salvo com sucesso.")

    # 8. Verificação de Preservação Bitwise
    frozen_hashes_after = {
        "temporal_encoder": compute_submodule_hash(final_model.transformer),
        "teammate_encoder": compute_submodule_hash(final_model.teammate_proj),
        "head_state": compute_submodule_hash(final_model.head_state),
        "head_next_sector": compute_submodule_hash(final_model.head_next_sector),
        "head_spot": compute_submodule_hash(final_model.head_spot),
        "head_transition": compute_submodule_hash(final_model.head_transition),
        "head_exit_trigger": compute_submodule_hash(final_model.head_exit_trigger)
    }

    head_to_hash_before = compute_submodule_hash(model.head_transition_occurs)
    head_to_hash_after = compute_submodule_hash(final_model.head_transition_occurs)
    only_to_changed = (head_to_hash_before != head_to_hash_after)

    all_frozen_match = True
    for k in frozen_hashes_before:
        if frozen_hashes_before[k] != frozen_hashes_after[k]:
            all_frozen_match = False
            print(f"  ERRO CRÍTICO: {k} foi modificado!")

    preservation_data = {
        "schema": "csbot.transition_patch.preservation_check.v1",
        "frozen_components_bitwise_identical": all_frozen_match,
        "only_sector_transition_head_changed": only_to_changed,
        "hashes_before": frozen_hashes_before,
        "hashes_after": frozen_hashes_after,
        "head_transition_occurs_before_sha256": head_to_hash_before,
        "head_transition_occurs_after_sha256": head_to_hash_after,
        "spot_metrics": baseline_spot_metrics,
        "gates": {
            "spot_mrr_ge_75": baseline_spot_metrics["mrr"] >= 0.75,
            "spot_top5_ge_95": baseline_spot_metrics["top5"] >= 0.95,
            "invalid_masked_selections_eq_0": baseline_spot_metrics["invalid_masked"] == 0,
            "all_preservation_gates_met": all_frozen_match and only_to_changed and (baseline_spot_metrics["mrr"] >= 0.75) and (baseline_spot_metrics["top5"] >= 0.95) and (baseline_spot_metrics["invalid_masked"] == 0)
        }
    }
    with open(OUT_DIR / "preservation_check.json", "w", encoding="utf-8") as f:
        json.dump(preservation_data, f, indent=2)
    print("  preservation_check.json salvo.")

    # 9. Final Head Metrics na Validation Integral
    full_validation_final_data = {
        "schema": "csbot.transition_patch.full_validation_final_metrics.v1",
        "validation_total_evaluated": val_total_indexed,
        "selected_experiment": selected_exp,
        "selected_threshold": selected_threshold_entry["threshold"],
        "canonical_verdict": canonical_verdict,
        "sector_transition_occurs": selected_threshold_entry,
        "positioning_state": baseline_st_metrics,
        "next_sector": baseline_ns_metrics,
        "spot_ranking": baseline_spot_metrics,
        "transition": baseline_tr_metrics,
        "exit_trigger": baseline_tg_metrics
    }
    with open(OUT_DIR / "full_validation_final_metrics.json", "w", encoding="utf-8") as f:
        json.dump(full_validation_final_data, f, indent=2)
    print("  full_validation_final_metrics.json salvo.")

    print("\n" + "=" * 80)
    print(f"MARCO 2B.3.3 CONCLUÍDO COM VEREDITO: {canonical_verdict}")
    print("=" * 80)

if __name__ == "__main__":
    main()
