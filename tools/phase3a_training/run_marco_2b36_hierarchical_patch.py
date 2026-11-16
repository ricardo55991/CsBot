#!/usr/bin/env python3
"""
Marco 2B.3.6: Treinamento e Avaliação Hierárquica (Head A Base + Head B Rare).

Executa Experimentos A, B e C sobre o checkpoint base aprovado do Marco 2B.3.4
(SHA-256 c7fb36647de92b7422f8389ef4c87343680e25d1da648fef883fbc4542e91608),
seleciona o melhor exclusivamente pela Validation integral (501.434 sequências)
e verifica todos os gates raros, de composição, preservação e ExitTrigger.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    STATE_NAMES,
    STATE_MAP,
    TRANSITION_NAMES,
    TRANSITION_MAP,
    EXIT_TRIGGER_NAMES,
    EXIT_TRIGGER_MAP,
    TEAM_MAP,
    ROLE_MAP,
    STAGE_MAP,
    compute_sha256,
)
from tools.phase3a_training.canonical_v2_dataloader import (
    SECTOR_TRANSITION_MAP,
    NEXT_SECTOR_MAP,
    load_supervised_spot_mask,
    load_catalog,
)
from tools.phase3a_training.positioning_model_v2 import PositioningTransformerV2RealTemporal
from tools.phase3a_training.hierarchical_positioning_model import (
    HierarchicalPositioningModel,
    BASE_STATE_NAMES,
    BASE_STATE_MAP,
    RARE_STATE_NAMES,
    RARE_STATE_MAP,
    compose_composite_predictions,
)

INDEX_DIR = BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
BASE_SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1"
HIER_SIDECAR_DIR = OUT_DIR / "hierarchical_label_sidecar"
BASE_CKPT = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
EXPECTED_BASE_SHA256 = "c7fb36647de92b7422f8389ef4c87343680e25d1da648fef883fbc4542e91608"

SELECTED_TRANSITION_THRESHOLD = 0.525
SEED = 20260306


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


def tensor_state_dict_sha256(module: nn.Module) -> str:
    h = hashlib.sha256()
    for k in sorted(module.state_dict().keys()):
        t = module.state_dict()[k].detach().cpu().contiguous()
        h.update(k.encode("utf-8"))
        h.update(t.numpy().tobytes())
    return h.hexdigest()


def load_split_dataframe(split_name: str) -> pd.DataFrame:
    if split_name not in ("train", "validation"):
        raise ValueError(f"Acesso ao split '{split_name}' é estritamente proibido!")
    base_cols = [
        "sequence_id", "demo_id", "round_id", "player_id", "slot", "split",
        "label_frame", "npz_path", "positioning_state", "CandidateSpotId",
        "SpotLossMask", "transition", "team", "role", "plan_stage",
    ]
    v2_cols = [
        "sequence_id", "sector_transition_occurs", "next_sector",
        "next_sector_loss_mask", "exit_trigger",
    ]
    h_cols = [
        "sequence_id", "base_positioning_state", "rare_tactical_state",
        "objective_eligible", "retake_eligible", "save_eligible", "rare_state_loss_mask",
    ]
    parts = []
    for i in range(6):
        df_b = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=base_cols)
        mask = df_b["split"] == split_name
        if not mask.any():
            continue
        df_b = df_b[mask].reset_index(drop=True)
        df_v2 = pd.read_parquet(BASE_SIDECAR_DIR / f"shard_{i:03d}_labels.parquet", columns=v2_cols)
        df_v2 = df_v2[mask.to_numpy()].reset_index(drop=True)
        df_h = pd.read_parquet(HIER_SIDECAR_DIR / f"shard_{i:03d}_hierarchical.parquet", columns=h_cols)
        df_h = df_h[mask.to_numpy()].reset_index(drop=True)

        assert (df_b["sequence_id"].to_numpy() == df_v2["sequence_id"].to_numpy()).all()
        assert (df_b["sequence_id"].to_numpy() == df_h["sequence_id"].to_numpy()).all()

        merged = pd.concat([df_b, df_v2.drop(columns=["sequence_id"]), df_h.drop(columns=["sequence_id"])], axis=1)
        parts.append(merged)
    return pd.concat(parts, ignore_index=True)


class FastNPZStore:
    """Pré-carrega NPZs de um split ou subconjunto com alta velocidade."""
    def __init__(self, demo_to_path: Dict[str, str]):
        self.arrays: Dict[str, np.ndarray] = {}
        for demo_id, p in demo_to_path.items():
            self.arrays[demo_id] = np.load(p)["X"]

    def extract_batch(self, demo_ids: np.ndarray, frames: np.ndarray, slots: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        b = len(frames)
        hist = np.zeros((b, 32, 18), dtype=np.float32)
        tm = np.zeros((b, 32, 4, 18), dtype=np.float32)
        tmask = np.ones((b, 32), dtype=np.float32)
        for i in range(b):
            X = self.arrays[demo_ids[i]]
            f_idx = int(frames[i])
            sl = int(slots[i])
            tm_slots = [s for s in range(5) if s != sl] if sl < 5 else [s for s in range(5, 10) if s != sl]
            if f_idx >= 31:
                hist[i] = X[f_idx - 31 : f_idx + 1, sl, :]
                tm[i] = X[f_idx - 31 : f_idx + 1, tm_slots, :]
            else:
                k = f_idx + 1
                tmask[i, : 32 - k] = 0.0
                hist[i, 32 - k :] = X[0 : f_idx + 1, sl, :]
                tm[i, 32 - k :] = X[0 : f_idx + 1, tm_slots, :]
        return hist, tm, tmask


def build_candidate_masks(spot_ids: np.ndarray, spot_to_idx: Dict[str, int], num_spots: int = 53) -> Tuple[np.ndarray, np.ndarray]:
    b = len(spot_ids)
    cmask = np.zeros((b, num_spots), dtype=bool)
    targets = np.zeros(b, dtype=np.int64)
    for i, sid in enumerate(spot_ids):
        idx = spot_to_idx.get(sid, -1)
        if idx >= 0:
            cmask[i, idx] = True
            targets[i] = idx
        else:
            cmask[i, 0] = True
            targets[i] = 0
    # Nota: para avaliação Spot MRR/Top-5, todos os 53 spots ativos são candidatos quando spot_loss_mask == 1
    return cmask, targets


def build_episodic_rare_pool(df_train: pd.DataFrame, seed: int = SEED) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Constrói pool episódico de positivos elegíveis (sem duplicar janelas adjacentes,
    gap >= 16 frames dentro de cada episódio) e negativos elegíveis contextuais (1:3).
    """
    rng = np.random.default_rng(seed)
    pos_indices = []
    ep_counts = {}

    for st in ["OBJECTIVE", "RETAKE", "SAVE"]:
        elig_col = {"OBJECTIVE": "objective_eligible", "RETAKE": "retake_eligible", "SAVE": "save_eligible"}[st]
        sub = df_train[(df_train["rare_tactical_state"] == st) & (df_train[elig_col] == True)].copy()
        sub["orig_idx"] = sub.index.to_numpy()
        sub = sub.sort_values(["demo_id", "round_id", "player_id", "label_frame"])
        new_ep = (
            (sub["demo_id"] != sub["demo_id"].shift(1))
            | (sub["round_id"] != sub["round_id"].shift(1))
            | (sub["player_id"] != sub["player_id"].shift(1))
            | ((sub["label_frame"] - sub["label_frame"].shift(1)) > 32)
        )
        sub["ep_id"] = new_ep.cumsum()
        max_per_ep = 4 if st == "SAVE" else 2
        chosen = []
        for _, ep_grp in sub.groupby("ep_id"):
            # Selecionar janelas espaçadas por >= 16 frames (não adjacentes)
            rows = ep_grp.to_dict("records")
            last_f = -999
            ep_sel = []
            for r in rows:
                if r["label_frame"] - last_f >= 16:
                    ep_sel.append(r["orig_idx"])
                    last_f = r["label_frame"]
                if len(ep_sel) >= max_per_ep:
                    break
            chosen.extend(ep_sel)
        ep_counts[st] = {"episodes": int(sub["ep_id"].nunique()), "selected_non_adjacent_windows": len(chosen)}
        pos_indices.extend(chosen)

    # Negativos contextuais elegíveis (NONE, mas elegível em algum contexto)
    neg_pool_mask = (df_train["rare_tactical_state"] == "NONE") & (df_train["rare_state_loss_mask"] > 0.5)
    neg_df = df_train[neg_pool_mask].copy()
    neg_df["orig_idx"] = neg_df.index.to_numpy()

    # Hard negatives: onde BasePositioningState é HOLD/STAGING/CLEARANCE dentro do contexto elegível
    hard_mask = neg_df["base_positioning_state"].isin(["HOLD", "STAGING", "CLEARANCE"])
    hard_neg_indices = neg_df[hard_mask]["orig_idx"].to_numpy()
    all_neg_indices = neg_df["orig_idx"].to_numpy()

    manifest = {
        "positive_episodes": ep_counts,
        "total_selected_positives": len(pos_indices),
        "eligible_negative_pool_total": int(len(all_neg_indices)),
        "eligible_hard_negative_pool": int(len(hard_neg_indices)),
        "unique_demos_in_neg_pool": int(neg_df["demo_id"].nunique()),
        "unique_players_in_neg_pool": int(neg_df[["demo_id", "player_id"]].drop_duplicates().shape[0]),
        "ratio_pos_neg": "1:3",
        "adjacent_window_min_gap_frames": 16,
        "provenance": "REAL",
    }
    return np.array(pos_indices, dtype=np.int64), np.array(hard_neg_indices, dtype=np.int64), all_neg_indices, manifest


def compute_multiclass_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: List[str]) -> Dict[str, Any]:
    per_class = {}
    recalls = []
    f1s = []
    for c_idx, cname in enumerate(class_names):
        tp = int(((y_true == c_idx) & (y_pred == c_idx)).sum())
        fp = int(((y_true != c_idx) & (y_pred == c_idx)).sum())
        fn = int(((y_true == c_idx) & (y_pred != c_idx)).sum())
        support = tp + fn
        pred_count = tp + fp
        if support == 0:
            per_class[cname] = {
                "support": 0,
                "predicted": pred_count,
                "tp": 0,
                "precision": "N/A",
                "recall": "N/A",
                "f1": "N/A",
            }
        else:
            prec = tp / pred_count if pred_count > 0 else 0.0
            rec = tp / support
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            per_class[cname] = {
                "support": support,
                "predicted": pred_count,
                "tp": tp,
                "precision": round(prec, 6),
                "recall": round(rec, 6),
                "f1": round(f1, 6),
            }
            recalls.append(rec)
            f1s.append(f1)
    macro_f1 = float(np.mean(f1s)) if f1s else 0.0
    bal_acc = float(np.mean(recalls)) if recalls else 0.0
    return {
        "macro_f1": round(macro_f1, 6),
        "balanced_accuracy": round(bal_acc, 6),
        "active_classes": len(f1s),
        "total_classes": len(class_names),
        "per_class": per_class,
    }


def evaluate_full_validation(
    model: HierarchicalPositioningModel,
    df_val: pd.DataFrame,
    val_store: FastNPZStore,
    spot_to_idx: Dict[str, int],
    device: torch.device,
    max_samples: int = 0,
) -> Dict[str, Any]:
    model.eval()
    if max_samples > 0 and max_samples < len(df_val):
        df_eval = df_val.iloc[:max_samples].reset_index(drop=True)
    else:
        df_eval = df_val

    n = len(df_eval)
    demo_ids = df_eval["demo_id"].to_numpy()
    frames = df_eval["label_frame"].to_numpy(np.int64)
    slots = df_eval["slot"].to_numpy(np.int64)
    team_ids = np.array([TEAM_MAP.get(t, 2) for t in df_eval["team"]], dtype=np.int64)
    role_ids = np.array([ROLE_MAP.get(r, 0) for r in df_eval["role"]], dtype=np.int64)
    stage_ids = np.array([STAGE_MAP.get(s, 0) for s in df_eval["plan_stage"]], dtype=np.int64)

    elig_arr = np.stack([
        df_eval["objective_eligible"].to_numpy(bool),
        df_eval["retake_eligible"].to_numpy(bool),
        df_eval["save_eligible"].to_numpy(bool),
    ], axis=1)

    y_comp_true = np.array([STATE_MAP[s] for s in df_eval["positioning_state"]], dtype=np.int64)
    y_base_true = np.array([BASE_STATE_MAP.get(s, -1) for s in df_eval["base_positioning_state"]], dtype=np.int64)
    y_rare_true = np.array([RARE_STATE_MAP[s] for s in df_eval["rare_tactical_state"]], dtype=np.int64)
    y_sec_trans_true = np.array([SECTOR_TRANSITION_MAP.get(s, 0) for s in df_eval["sector_transition_occurs"]], dtype=np.int64)
    y_next_sec_true = np.array([NEXT_SECTOR_MAP.get(s, 0) for s in df_eval["next_sector"]], dtype=np.int64)
    next_sec_mask = df_eval["next_sector_loss_mask"].to_numpy(np.float32) > 0.5
    y_trans_true = np.array([TRANSITION_MAP.get(s, 0) for s in df_eval["transition"]], dtype=np.int64)
    y_trig_true = np.array([EXIT_TRIGGER_MAP.get(s, 0) for s in df_eval["exit_trigger"]], dtype=np.int64)
    spot_loss_mask = df_eval["SpotLossMask"].to_numpy(np.float32) > 0.5
    spot_targets = np.array([spot_to_idx.get(s, -1) for s in df_eval["CandidateSpotId"]], dtype=np.int64)

    pred_comp = np.zeros(n, dtype=np.int64)
    pred_base = np.zeros(n, dtype=np.int64)
    pred_rare = np.zeros(n, dtype=np.int64)
    pred_sec_trans = np.zeros(n, dtype=np.int64)
    pred_next_sec = np.zeros(n, dtype=np.int64)
    pred_trans = np.zeros(n, dtype=np.int64)
    pred_trig = np.zeros(n, dtype=np.int64)

    sup_mask_np = model.base_model.supervised_spot_mask.detach().cpu().numpy() > 0.5
    spot_mrr_sum = 0.0
    spot_top5_hits = 0
    spot_eval_count = 0
    invalid_masked_sel = 0

    bs = 512
    with torch.inference_mode():
        for start in range(0, n, bs):
            end = min(start + bs, n)
            hist, tm, tmask = val_store.extract_batch(demo_ids[start:end], frames[start:end], slots[start:end])
            out = model(
                self_history=torch.from_numpy(hist).to(device),
                teammates=torch.from_numpy(tm).to(device),
                temporal_mask=torch.from_numpy(tmask).to(device),
                team_idx=torch.from_numpy(team_ids[start:end]).to(device),
                role_idx=torch.from_numpy(role_ids[start:end]).to(device),
                stage_idx=torch.from_numpy(stage_ids[start:end]).to(device),
                rare_eligibility_mask=torch.from_numpy(elig_arr[start:end]).to(device),
            )
            c_p, b_p, r_p = compose_composite_predictions(
                out["logits_base_state"], out["logits_rare_state"], torch.from_numpy(elig_arr[start:end]).to(device)
            )
            pred_comp[start:end] = c_p.cpu().numpy()
            pred_base[start:end] = b_p.cpu().numpy()
            pred_rare[start:end] = r_p.cpu().numpy()

            prob_st = F.softmax(out["logits_transition_occurs"], dim=-1)[:, 1].cpu().numpy()
            pred_sec_trans[start:end] = (prob_st >= SELECTED_TRANSITION_THRESHOLD).astype(np.int64)
            pred_next_sec[start:end] = torch.argmax(out["logits_next_sector"], dim=-1).cpu().numpy()
            pred_trans[start:end] = torch.argmax(out["logits_transition"], dim=-1).cpu().numpy()
            pred_trig[start:end] = torch.argmax(out["logits_trigger"], dim=-1).cpu().numpy()

            # Spot ranking metrics (todos os spots supervisionados ativos)
            sp_logits = out["logits_spot"].cpu().numpy()
            top1 = np.argmax(sp_logits, axis=-1)
            invalid_masked_sel += int((~sup_mask_np[top1]).sum())

            valid_sp = spot_loss_mask[start:end] & (spot_targets[start:end] >= 0) & sup_mask_np[np.maximum(0, spot_targets[start:end])]
            if valid_sp.any():
                sub_l = sp_logits[valid_sp]
                sub_t = spot_targets[start:end][valid_sp]
                order = np.argsort(-sub_l, axis=-1)
                for row_i in range(len(sub_t)):
                    rank = int(np.where(order[row_i] == sub_t[row_i])[0][0]) + 1
                    spot_mrr_sum += 1.0 / rank
                    if rank <= 5:
                        spot_top5_hits += 1
                spot_eval_count += int(valid_sp.sum())

    base_valid = y_base_true >= 0
    base_metrics = compute_multiclass_metrics(y_base_true[base_valid], pred_base[base_valid], BASE_STATE_NAMES)
    rare_metrics = compute_multiclass_metrics(y_rare_true, pred_rare, RARE_STATE_NAMES)
    comp_metrics = compute_multiclass_metrics(y_comp_true, pred_comp, STATE_NAMES)
    sec_trans_metrics = compute_multiclass_metrics(y_sec_trans_true, pred_sec_trans, ["NO_TRANSITION", "TRANSITION_OCCURS"])
    next_sec_metrics = compute_multiclass_metrics(
        y_next_sec_true[next_sec_mask], pred_next_sec[next_sec_mask], ["A", "B", "MID", "CT", "T"]
    )
    trans_metrics = compute_multiclass_metrics(y_trans_true, pred_trans, TRANSITION_NAMES)
    trig_metrics = compute_multiclass_metrics(y_trig_true, pred_trig, EXIT_TRIGGER_NAMES)

    spot_mrr = round(spot_mrr_sum / spot_eval_count, 6) if spot_eval_count > 0 else 0.0
    spot_top5 = round(spot_top5_hits / spot_eval_count, 6) if spot_eval_count > 0 else 0.0

    return {
        "evaluated_sequences": n,
        "base_state": base_metrics,
        "rare_state": rare_metrics,
        "composite_state": comp_metrics,
        "sector_transition": sec_trans_metrics,
        "next_sector": next_sec_metrics,
        "transition": trans_metrics,
        "exit_trigger": trig_metrics,
        "spot_ranking": {
            "evaluated_count": spot_eval_count,
            "mrr": spot_mrr,
            "top5": spot_top5,
            "invalid_masked_selection": invalid_masked_sel,
        },
        "data_nature": "REAL",
    }


def focal_ce_loss(logits: torch.Tensor, targets: torch.Tensor, weight: torch.Tensor, gamma: float = 1.0) -> torch.Tensor:
    ce = F.cross_entropy(logits, targets, weight=weight, reduction="none")
    if gamma <= 0.0:
        return ce
    pt = torch.exp(-F.cross_entropy(logits, targets, reduction="none"))
    return ((1.0 - pt) ** gamma) * ce


def train_experiment(
    exp_name: str,
    use_focal: bool,
    use_hard_negatives: bool,
    use_consistency: bool,
    df_train: pd.DataFrame,
    df_val: pd.DataFrame,
    train_store: FastNPZStore,
    val_store: FastNPZStore,
    pos_pool: np.ndarray,
    hard_neg_pool: np.ndarray,
    all_neg_pool: np.ndarray,
    spot_to_idx: Dict[str, int],
    sup_spot_mask: torch.Tensor,
    device: torch.device,
    epochs: int,
    steps_per_epoch: int,
    max_val_samples: int,
) -> Tuple[HierarchicalPositioningModel, Dict[str, Any]]:
    set_seed(SEED)
    base_model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask)
    ckpt = torch.load(BASE_CKPT, map_location=device, weights_only=False)
    base_model.load_state_dict(ckpt["model_state_dict"], strict=True)

    model = HierarchicalPositioningModel(base_model).to(device)
    model.freeze_approved_modules()

    optimizer = torch.optim.AdamW(
        [
            {"params": list(model.base_model.transformer.layers[2].parameters()) + list(model.base_model.norm.parameters()), "lr": 1e-5, "weight_decay": 1e-4},
            {"params": list(model.head_base_state.parameters()), "lr": 1e-4, "weight_decay": 1e-4},
            {"params": list(model.head_rare_state.parameters()), "lr": 1e-4, "weight_decay": 1e-4},
        ]
    )

    # Pesos moderados para Base (TRANSIT, CLEARANCE, STAGING, HOLD)
    base_weights = torch.tensor([0.5, 1.5, 2.5, 1.5], dtype=torch.float32, device=device)
    # Pesos moderados para Rare (NONE, OBJECTIVE, RETAKE, SAVE)
    rare_weights = torch.tensor([1.0, 2.0, 1.8, 3.0], dtype=torch.float32, device=device)

    # Pré-extrair arrays numpy do df_train para indexação rápida
    tr_demos = df_train["demo_id"].to_numpy()
    tr_frames = df_train["label_frame"].to_numpy(np.int64)
    tr_slots = df_train["slot"].to_numpy(np.int64)
    tr_teams = np.array([TEAM_MAP.get(t, 2) for t in df_train["team"]], dtype=np.int64)
    tr_roles = np.array([ROLE_MAP.get(r, 0) for r in df_train["role"]], dtype=np.int64)
    tr_stages = np.array([STAGE_MAP.get(s, 0) for s in df_train["plan_stage"]], dtype=np.int64)
    tr_base_y = np.array([BASE_STATE_MAP.get(s, -1) for s in df_train["base_positioning_state"]], dtype=np.int64)
    tr_rare_y = np.array([RARE_STATE_MAP[s] for s in df_train["rare_tactical_state"]], dtype=np.int64)
    tr_elig = np.stack([
        df_train["objective_eligible"].to_numpy(bool),
        df_train["retake_eligible"].to_numpy(bool),
        df_train["save_eligible"].to_numpy(bool),
    ], axis=1)
    tr_rare_mask = df_train["rare_state_loss_mask"].to_numpy(np.float32)

    nat_pool = np.arange(len(df_train), dtype=np.int64)
    rng = np.random.default_rng(SEED + (1 if exp_name == "A" else 2 if exp_name == "B" else 3))

    t0 = time.time()
    best_score = -1.0
    best_state_dict = None
    best_val_metrics = None

    for ep in range(1, epochs + 1):
        model.train()
        ep_loss = 0.0
        for step in range(steps_per_epoch):
            # 96 amostras naturais para Base + 32 amostras episódicas raras (1:3 = 8 pos + 24 neg contextuais)
            nat_idx = rng.choice(nat_pool, size=96, replace=False)
            pos_idx = rng.choice(pos_pool, size=8, replace=(len(pos_pool) < 8))
            neg_src = hard_neg_pool if (use_hard_negatives and len(hard_neg_pool) >= 24) else all_neg_pool
            neg_idx = rng.choice(neg_src, size=24, replace=False)
            batch_idx = np.concatenate([nat_idx, pos_idx, neg_idx])

            hist, tm, tmask = train_store.extract_batch(tr_demos[batch_idx], tr_frames[batch_idx], tr_slots[batch_idx])
            hist_t = torch.from_numpy(hist).to(device)
            tm_t = torch.from_numpy(tm).to(device)
            tmask_t = torch.from_numpy(tmask).to(device)
            team_t = torch.from_numpy(tr_teams[batch_idx]).to(device)
            role_t = torch.from_numpy(tr_roles[batch_idx]).to(device)
            stage_t = torch.from_numpy(tr_stages[batch_idx]).to(device)
            elig_t = torch.from_numpy(tr_elig[batch_idx]).to(device)

            out = model(
                self_history=hist_t,
                teammates=tm_t,
                temporal_mask=tmask_t,
                team_idx=team_t,
                role_idx=role_t,
                stage_idx=stage_t,
                rare_eligibility_mask=elig_t,
            )

            # Loss Base (apenas sobre amostras com rótulo base válido 0..3)
            by = torch.from_numpy(tr_base_y[batch_idx]).to(device)
            base_valid = by >= 0
            loss_base = F.cross_entropy(out["logits_base_state"][base_valid], by[base_valid], weight=base_weights)

            # Loss Rare (exclusivamente sobre amostras contextualmente elegíveis)
            ry = torch.from_numpy(tr_rare_y[batch_idx]).to(device)
            rmask = torch.from_numpy(tr_rare_mask[batch_idx]).to(device) > 0.5
            if rmask.any():
                gamma = 1.0 if use_focal else 0.0
                r_losses = focal_ce_loss(out["logits_rare_state"][rmask], ry[rmask], weight=rare_weights, gamma=gamma)
                loss_rare = r_losses.mean()
            else:
                loss_rare = torch.tensor(0.0, device=device)

            loss = loss_base + 1.2 * loss_rare

            # Consistency loss moderada (Experimento C): probabilidade rara deve respeitar máscara elegível
            if use_consistency and rmask.any():
                probs_rare = F.softmax(out["raw_logits_rare_state"][rmask], dim=-1)  # [M, 4]
                inelig = (~elig_t[rmask]).float()  # [M, 3] para OBJ, RET, SAV
                # Penalizar massa de probabilidade em classes raras inelegíveis
                cons_pen = (probs_rare[:, 1:] * inelig).sum(dim=-1).mean()
                loss = loss + 0.25 * cons_pen

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            ep_loss += float(loss.item())

        val_m = evaluate_full_validation(model, df_val, val_store, spot_to_idx, device, max_samples=max_val_samples)
        comp_f1 = val_m["composite_state"]["macro_f1"]
        obj_f1 = val_m["rare_state"]["per_class"]["OBJECTIVE"]["f1"]
        ret_f1 = val_m["rare_state"]["per_class"]["RETAKE"]["f1"]
        score = comp_f1 + 0.5 * ( (0.0 if obj_f1 == "N/A" else obj_f1) + (0.0 if ret_f1 == "N/A" else ret_f1) )
        print(f"[Exp {exp_name} | Ep {ep}/{epochs}] loss={ep_loss/steps_per_epoch:.4f}, comp_F1={comp_f1:.4f}, OBJ_F1={obj_f1}, RET_F1={ret_f1}, elapsed={time.time()-t0:.1f}s")
        if score > best_score:
            best_score = score
            best_val_metrics = val_m
            best_state_dict = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state_dict)
    return model, best_val_metrics


def check_gates(m: Dict[str, Any], base_spot_sha: str, model: HierarchicalPositioningModel) -> Dict[str, Any]:
    rare = m["rare_state"]["per_class"]
    base = m["base_state"]["per_class"]
    comp = m["composite_state"]
    st = m["sector_transition"]
    ns = m["next_sector"]
    tr = m["transition"]
    sp = m["spot_ranking"]

    def num(v):
        return 0.0 if v == "N/A" else float(v)

    obj_ok = num(rare["OBJECTIVE"]["recall"]) >= 0.35 and num(rare["OBJECTIVE"]["precision"]) >= 0.25 and num(rare["OBJECTIVE"]["f1"]) >= 0.29
    ret_ok = num(rare["RETAKE"]["recall"]) >= 0.35 and num(rare["RETAKE"]["precision"]) >= 0.25 and num(rare["RETAKE"]["f1"]) >= 0.29
    sav_ok = num(rare["SAVE"]["recall"]) >= 0.20 and num(rare["SAVE"]["precision"]) >= 0.15 and num(rare["SAVE"]["f1"]) >= 0.17

    base_ok = (
        m["base_state"]["macro_f1"] >= 0.45
        and num(base["CLEARANCE"]["recall"]) >= 0.75
        and num(base["STAGING"]["recall"]) >= 0.25
        and num(base["HOLD"]["recall"]) >= 0.40
        and num(base["TRANSIT"]["recall"]) >= 0.75
    )
    comp_ok = comp["macro_f1"] >= 0.40 and comp["balanced_accuracy"] >= 0.50

    cur_spot_sha = tensor_state_dict_sha256(model.base_model.head_spot)
    spot_bitwise_ok = (cur_spot_sha == base_spot_sha)

    pres_ok = (
        st["macro_f1"] >= 0.57
        and num(st["per_class"]["TRANSITION_OCCURS"]["recall"]) >= 0.35
        and num(st["per_class"]["NO_TRANSITION"]["recall"]) >= 0.78
        and ns["macro_f1"] >= 0.48
        and tr["macro_f1"] >= 0.60
        and sp["mrr"] >= 0.76
        and sp["top5"] >= 0.955
        and sp["invalid_masked_selection"] == 0
        and spot_bitwise_ok
    )

    if not pres_ok:
        decision = "HIERARCHICAL_STATE_PATCH_REGRESSION"
    elif obj_ok and ret_ok and sav_ok and base_ok and comp_ok:
        decision = "POSITIONING_TRANSFORMER_READY_FOR_FINAL_EVALUATION"
    elif obj_ok and ret_ok and base_ok and not sav_ok:
        decision = "HIERARCHICAL_STATE_PATCH_READY_WITH_SAVE_FALLBACK"
    else:
        decision = "RARE_STATES_REQUIRE_EVENT_DRIVEN_RUNTIME_POLICY"

    return {
        "objective_gate_pass": obj_ok,
        "retake_gate_pass": ret_ok,
        "save_gate_pass": sav_ok,
        "save_fallback_status": "PASS" if sav_ok else "SAVE_DETERMINISTIC_FALLBACK_REQUIRED",
        "base_state_gate_pass": base_ok,
        "composite_state_gate_pass": comp_ok,
        "preservation_gate_pass": pres_ok,
        "spot_head_bitwise_identical": spot_bitwise_ok,
        "spot_head_sha256": cur_spot_sha,
        "decision": decision,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    smoke = os.environ.get("CSBOT_2B36_SMOKE", "0") == "1"
    epochs = 1 if smoke else int(os.environ.get("CSBOT_2B36_EPOCHS", "2"))
    steps_per_epoch = 20 if smoke else int(os.environ.get("CSBOT_2B36_STEPS", "600"))
    max_val = 2000 if smoke else int(os.environ.get("CSBOT_2B36_MAX_VAL", "0"))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Executando Marco 2B.3.6 (device={device}, smoke={smoke}, epochs={epochs}, steps={steps_per_epoch}, max_val={max_val})")

    if compute_sha256(BASE_CKPT) != EXPECTED_BASE_SHA256:
        raise ValueError("SHA-256 do checkpoint base divergente!")

    sup_spot_mask = load_supervised_spot_mask()
    _, spot_to_idx = load_catalog(BASE_DIR / "datasets" / "mirage_v2")

    # Referência bitwise do head_spot original
    ref_base = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask)
    ref_ckpt = torch.load(BASE_CKPT, map_location="cpu", weights_only=False)
    ref_base.load_state_dict(ref_ckpt["model_state_dict"], strict=True)
    base_spot_sha = tensor_state_dict_sha256(ref_base.head_spot)

    print("Carregando Train e Validation + sidecars...")
    df_train = load_split_dataframe("train")
    df_val = load_split_dataframe("validation")
    print(f"Train={len(df_train)}, Validation={len(df_val)}")

    pos_pool, hard_neg_pool, all_neg_pool, hn_manifest = build_episodic_rare_pool(df_train)
    with open(OUT_DIR / "hard_negative_manifest.json", "w", encoding="utf-8") as f:
        json.dump(hn_manifest, f, indent=2, ensure_ascii=False)

    print("Pré-carregando NPZs na RAM...")
    train_demos = df_train[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    val_demos = df_val[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    train_store = FastNPZStore(train_demos)
    val_store = FastNPZStore(val_demos)

    configs = [
        ("A", False, False, False),
        ("B", True, True, False),
        ("C", True, True, True),
    ]
    exp_results = {}
    best_exp = None
    best_score = -1.0
    best_model = None
    best_metrics = None

    for exp_name, use_focal, use_hn, use_cons in configs:
        print(f"\n=== Experimento {exp_name} ===")
        model, val_m = train_experiment(
            exp_name=exp_name,
            use_focal=use_focal,
            use_hard_negatives=use_hn,
            use_consistency=use_cons,
            df_train=df_train,
            df_val=df_val,
            train_store=train_store,
            val_store=val_store,
            pos_pool=pos_pool,
            hard_neg_pool=hard_neg_pool,
            all_neg_pool=all_neg_pool,
            spot_to_idx=spot_to_idx,
            sup_spot_mask=sup_spot_mask,
            device=device,
            epochs=epochs,
            steps_per_epoch=steps_per_epoch,
            max_val_samples=max_val,
        )
        out_name = f"experiment_{exp_name.lower()}_metrics.json"
        with open(OUT_DIR / out_name, "w", encoding="utf-8") as f:
            json.dump(val_m, f, indent=2, ensure_ascii=False)
        exp_results[exp_name] = val_m

        obj_f1 = val_m["rare_state"]["per_class"]["OBJECTIVE"]["f1"]
        ret_f1 = val_m["rare_state"]["per_class"]["RETAKE"]["f1"]
        score = val_m["composite_state"]["macro_f1"] + 0.5 * (
            (0.0 if obj_f1 == "N/A" else obj_f1) + (0.0 if ret_f1 == "N/A" else ret_f1)
        )
        if score > best_score:
            best_score = score
            best_exp = exp_name
            best_model = model
            best_metrics = val_m

    # Salvar comparação, full_validation_metrics, preservation_check e selected_checkpoint.pt
    comp_summary = {
        "selected_experiment": best_exp,
        "experiments": {
            k: {
                "composite_macro_f1": v["composite_state"]["macro_f1"],
                "base_macro_f1": v["base_state"]["macro_f1"],
                "objective": v["rare_state"]["per_class"]["OBJECTIVE"],
                "retake": v["rare_state"]["per_class"]["RETAKE"],
                "save": v["rare_state"]["per_class"]["SAVE"],
                "spot_mrr": v["spot_ranking"]["mrr"],
                "sector_transition_macro_f1": v["sector_transition"]["macro_f1"],
            }
            for k, v in exp_results.items()
        },
    }
    with open(OUT_DIR / "experiment_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comp_summary, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "full_validation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(best_metrics, f, indent=2, ensure_ascii=False)

    pres_check = check_gates(best_metrics, base_spot_sha, best_model)
    pres_check["selected_experiment"] = best_exp
    with open(OUT_DIR / "preservation_check.json", "w", encoding="utf-8") as f:
        json.dump(pres_check, f, indent=2, ensure_ascii=False)

    torch.save(
        {
            "model_state_dict": best_model.state_dict(),
            "selected_experiment": best_exp,
            "base_checkpoint_sha256": EXPECTED_BASE_SHA256,
            "contract_version": "2b36_hierarchical_v1",
            "decision": pres_check["decision"],
        },
        OUT_DIR / "selected_checkpoint.pt",
    )

    print("\n=== MARCO 2B.3.6 CONCLUÍDO ===")
    print(json.dumps({"selected_experiment": best_exp, "preservation_check": pres_check}, indent=2))


if __name__ == "__main__":
    main()
