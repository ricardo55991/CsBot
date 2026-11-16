"""MARCO 2B.3.5: Recuperacao Episodica de OBJECTIVE, RETAKE e SAVE.

Regras operacionais:
- Checkpoint-base: joint_temporal_patch_v1/selected_checkpoint.pt (SHA-256 verificado)
- Nao consulta Test nem Final Holdout (DataLoader bloqueia com ValueError)
- Nao altera DataLoader, labels, splits, catalogo ou runtime C#
- Congela bitwise: projecoes de entrada, teammate encoder, blocos temporais 0 e 1,
  CandidateSpotRankingHead, SectorTransitionOccursHead, NextSectorHead,
  TransitionHead e ExitTriggerHead
- Treina: ultimo bloco temporal (layers.2 + norm, lr=1e-5) e PositioningStateHead (lr=1e-4)
- Sampler episodico por (demo_id, round_id, player_id, positioning_state, contiguous_tick_range)
  com teto de janelas por episodio (nao adjacentes), episodios por round e contribuicao por demo
- Tres experimentos: A (1:4, CE balanceada moderada), B (1:3, focal gamma=1.0),
  C (1:2, focal gamma=1.0 + consistency loss)
- Selecao por RareStateScore + gates de preservacao na Validation integral (501.434 seqs)
"""
import copy
import hashlib
import json
import os
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
from torch.utils.data import DataLoader, Subset

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.phase3a_training.canonical_v2_dataloader import (  # noqa: E402
    CanonicalV2PositioningDataset,
    EXIT_TRIGGER_MAP,
    NEXT_SECTOR_MAP,
    STATE_MAP,
    TRANSITION_MAP,
    canonical_v2_collate_fn,
    load_supervised_spot_mask,
)
from tools.phase3a_training.positioning_model_v2 import (  # noqa: E402
    EXIT_TRIGGER_NAMES,
    NEXT_SECTOR_NAMES,
    PositioningTransformerV2RealTemporal,
    STATE_NAMES,
    TRANSITION_NAMES,
)

SEED = 42035
CONTIGUOUS_GAP_MAX = 32
EXPECTED_VAL_SIZE = 501434

BASE_CKPT = (
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal"
    / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
)
EXPECTED_BASE_SHA256 = "c7fb36647de92b7422f8389ef4c87343680e25d1da648fef883fbc4542e91608"
PRIOR_PATCH_CKPT = (
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal"
    / "rare_class_patch_v1" / "selected_patch_checkpoint.pt"
)
ROOT_CANDIDATE_CKPT = (
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal"
    / "full_training" / "selected_candidate.pt"
)

INDEX_DIR = REPO_ROOT / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"

_OUT_OVERRIDE = os.environ.get("CSBOT_2B35_OUT_DIR", "").strip()
OUT_DIR = (
    Path(_OUT_OVERRIDE) if _OUT_OVERRIDE else
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal"
    / "rare_class_patch_v1" / "rare_episode_patch_v1"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

EPOCHS = int(os.environ.get("CSBOT_2B35_EPOCHS", "3"))
MAX_VAL = os.environ.get("CSBOT_2B35_MAX_VAL")
EXPERIMENT_FILTER = os.environ.get("CSBOT_2B35_EXPERIMENTS", "").strip()
TARGET_SAMPLES = int(os.environ.get("CSBOT_2B35_TARGET_SAMPLES", "12000"))

SELECTED_TRANSITION_THRESHOLD = 0.525  # threshold selecionado do checkpoint-base 2B.3.4

RARE_TARGET_STATES = ["OBJECTIVE", "RETAKE", "SAVE"]
COMMON_STATES = ["TRANSIT", "CLEARANCE", "STAGING", "HOLD"]

RARE_STATE_SCORE_WEIGHTS = {
    "OBJECTIVE_F1": 0.30,
    "RETAKE_F1": 0.25,
    "SAVE_F1": 0.20,
    "HOLD_F1": 0.10,
    "STAGING_F1": 0.10,
    "PositioningStateMacroF1": 0.05,
}

FROZEN_MODULES = (
    "player_proj",
    "teammate_proj",
    "teammate_pool",
    "team_emb",
    "role_emb",
    "stage_emb",
    "context_fusion",
    "pos_encoder",
    "head_spot",
    "head_transition_occurs",
    "head_next_sector",
    "head_transition",
    "head_exit_trigger",
)


def set_seed(seed: int = SEED) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_submodule_hash(module: nn.Module) -> str:
    h = hashlib.sha256()
    for name, tensor in sorted(module.state_dict().items()):
        h.update(name.encode("utf-8"))
        h.update(tensor.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def module_hashes(model: PositioningTransformerV2RealTemporal) -> Dict[str, str]:
    out = {}
    for name in (
        "player_proj", "teammate_proj", "teammate_pool",
        "team_emb", "role_emb", "stage_emb", "context_fusion", "pos_encoder",
        "norm", "head_state", "head_transition_occurs", "head_next_sector",
        "head_spot", "head_transition", "head_exit_trigger",
    ):
        out[name] = compute_submodule_hash(getattr(model, name))
    for i, layer in enumerate(model.transformer.layers):
        out[f"transformer_layer_{i}"] = compute_submodule_hash(layer)
    return out


def apply_selective_freeze(model: PositioningTransformerV2RealTemporal) -> Dict[str, int]:
    for p in model.parameters():
        p.requires_grad = False
    for p in model.transformer.layers[2].parameters():
        p.requires_grad = True
    for p in model.norm.parameters():
        p.requires_grad = True
    for p in model.head_state.parameters():
        p.requires_grad = True

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen = sum(p.numel() for p in model.parameters() if not p.requires_grad)
    return {"trainable_params": int(trainable), "frozen_params": int(frozen)}


def assert_frozen_invariants(model: PositioningTransformerV2RealTemporal) -> None:
    for idx in (0, 1):
        for pname, p in model.transformer.layers[idx].named_parameters():
            assert not p.requires_grad, f"transformer.layers.{idx}.{pname} deveria estar congelado"
    for mname in FROZEN_MODULES:
        mod = getattr(model, mname)
        for pname, p in mod.named_parameters():
            assert not p.requires_grad, f"{mname}.{pname} deveria estar congelado"


# ------------------------------------------------------------------------------
# Episodios e Sampler Episodico (Secao 3)
# ------------------------------------------------------------------------------

def assign_contiguous_episodes(df: pd.DataFrame) -> pd.Series:
    ordered = df.sort_values(
        ["demo_id", "round_id", "player_id", "positioning_state", "label_frame"],
        kind="mergesort",
    )
    same_key = (
        (ordered["demo_id"] == ordered["demo_id"].shift(1))
        & (ordered["round_id"] == ordered["round_id"].shift(1))
        & (ordered["player_id"] == ordered["player_id"].shift(1))
        & (ordered["positioning_state"] == ordered["positioning_state"].shift(1))
    )
    gap = ordered["label_frame"] - ordered["label_frame"].shift(1)
    new_ep = (~same_key) | (gap > CONTIGUOUS_GAP_MAX)
    return new_ep.cumsum().reindex(df.index)


def build_train_dataframe() -> pd.DataFrame:
    cols = [
        "sequence_id", "demo_id", "match_id", "round_id", "player_id",
        "split", "window_start_frame", "label_frame", "positioning_state",
        "objective_subtype", "save_subtype", "semantic_type", "provenance_type",
    ]
    parts = []
    for sh in sorted(INDEX_DIR.glob("shard_*.parquet")):
        df_b = pd.read_parquet(sh, columns=cols)
        sub = df_b[df_b["split"] == "train"].copy()
        if len(sub) > 0:
            parts.append(sub)
    df = pd.concat(parts, ignore_index=True)
    df["global_index"] = df.index.astype(np.int64)
    df["episode_uid"] = assign_contiguous_episodes(df)
    return df


def _pick_non_adjacent_windows_from_episode(
    ep_df: pd.DataFrame,
    max_windows: int,
    rng: np.random.RandomState,
) -> np.ndarray:
    """Seleciona ate max_windows janelas de um episodio sem nunca pegar janelas adjacentes
    (|label_frame_a - label_frame_b| <= CONTIGUOUS_GAP_MAX).
    """
    if len(ep_df) == 0:
        return np.empty(0, dtype=np.int64)
    if max_windows <= 1 or len(ep_df) == 1:
        pos = int(rng.randint(0, len(ep_df)))
        return np.array([int(ep_df["global_index"].iloc[pos])], dtype=np.int64)

    order = rng.permutation(len(ep_df))
    chosen_idx: List[int] = []
    chosen_frames: List[int] = []
    for row_i in order:
        lf = int(ep_df["label_frame"].iloc[row_i])
        if all(abs(lf - prev) > CONTIGUOUS_GAP_MAX for prev in chosen_frames):
            chosen_idx.append(int(ep_df["global_index"].iloc[row_i]))
            chosen_frames.append(lf)
            if len(chosen_idx) >= max_windows:
                break
    return np.array(chosen_idx, dtype=np.int64)


def episodic_balanced_sampler(
    train_df: pd.DataFrame,
    rare_ratio_denom: int,  # 4 -> 1:4, 3 -> 1:3, 2 -> 1:2
    target_total: int,
    rng: np.random.RandomState,
    max_windows_per_rare_ep: int = 2,
    max_episodes_per_round: int = 2,
    max_rare_ep_per_demo: int = 6,
    max_common_ep_per_demo: int = 12,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Seleciona primeiro episodios (limitados por round e demo) e depois janelas nao adjacentes."""
    want_rare = max(1, target_total // (1 + rare_ratio_denom))
    want_common = target_total - want_rare

    # --- Selecao de episodios raros (OBJECTIVE, RETAKE, SAVE) ----------------
    # Alocacao equilibrada entre as 3 classes raras dentro do budget want_rare
    per_rare_target = max(1, want_rare // 3)
    rare_indices: List[int] = []
    rare_ep_selected: Dict[str, int] = {}
    rare_win_selected: Dict[str, int] = {}

    for cls_name in RARE_TARGET_STATES:
        sub = train_df[train_df["positioning_state"] == cls_name]
        # Resumo de episodios: 1 linha representativa por episode_uid
        ep_meta = sub[["episode_uid", "demo_id", "round_id"]].drop_duplicates("episode_uid")
        ep_meta = ep_meta.iloc[rng.permutation(len(ep_meta))].reset_index(drop=True)

        # Limite por round e por demo para preservar diversidade
        round_counts: Dict[Tuple[str, int], int] = {}
        demo_counts: Dict[str, int] = {}
        picked_eps: List[int] = []

        # Para SAVE (apenas 43 episodios totais), afrouxa limite por demo se necessario
        demo_cap = max_rare_ep_per_demo if cls_name != "SAVE" else max(max_rare_ep_per_demo, 10)
        for row in ep_meta.itertuples(index=False):
            rk = (str(row.demo_id), int(row.round_id))
            dk = str(row.demo_id)
            if round_counts.get(rk, 0) >= max_episodes_per_round:
                continue
            if demo_counts.get(dk, 0) >= demo_cap:
                continue
            picked_eps.append(int(row.episode_uid))
            round_counts[rk] = round_counts.get(rk, 0) + 1
            demo_counts[dk] = demo_counts.get(dk, 0) + 1
            if len(picked_eps) * max_windows_per_rare_ep >= per_rare_target:
                # Continua ate atingir per_rare_target janelas se possivel
                pass

        # Extrair janelas nao-adjacentes dos episodios sorteados
        sub_picked = sub[sub["episode_uid"].isin(picked_eps)]
        ep_groups = {int(k): g for k, g in sub_picked.groupby("episode_uid", sort=False)}
        cls_win: List[int] = []
        used_ep = 0
        for eid in picked_eps:
            w = _pick_non_adjacent_windows_from_episode(
                ep_groups[eid], max_windows=max_windows_per_rare_ep, rng=rng
            )
            if len(w) > 0:
                cls_win.extend(w.tolist())
                used_ep += 1
            if len(cls_win) >= per_rare_target:
                break
        rare_ep_selected[cls_name] = used_ep
        rare_win_selected[cls_name] = len(cls_win)
        rare_indices.extend(cls_win)

    # --- Selecao de episodios comuns (TRANSIT, CLEARANCE, STAGING, HOLD) -----
    # Garante presenca controlada de todas as comuns (evita colapso em TRANSIT)
    common_alloc = {
        "TRANSIT": int(round(want_common * 0.55)),
        "CLEARANCE": int(round(want_common * 0.15)),
        "HOLD": int(round(want_common * 0.18)),
        "STAGING": 0,
    }
    common_alloc["STAGING"] = want_common - sum(common_alloc.values())

    common_indices: List[int] = []
    common_win_selected: Dict[str, int] = {}
    for cls_name, cls_target in common_alloc.items():
        sub = train_df[train_df["positioning_state"] == cls_name]
        ep_meta = sub[["episode_uid", "demo_id", "round_id"]].drop_duplicates("episode_uid")
        ep_meta = ep_meta.iloc[rng.permutation(len(ep_meta))].reset_index(drop=True)

        round_counts: Dict[Tuple[str, int], int] = {}
        demo_counts: Dict[str, int] = {}
        picked_eps: List[int] = []
        for row in ep_meta.itertuples(index=False):
            rk = (str(row.demo_id), int(row.round_id))
            dk = str(row.demo_id)
            if round_counts.get(rk, 0) >= max_episodes_per_round:
                continue
            if demo_counts.get(dk, 0) >= max_common_ep_per_demo:
                continue
            picked_eps.append(int(row.episode_uid))
            round_counts[rk] = round_counts.get(rk, 0) + 1
            demo_counts[dk] = demo_counts.get(dk, 0) + 1
            if len(picked_eps) >= cls_target:
                break

        # 1 janela por episodio comum
        sub_picked = sub[sub["episode_uid"].isin(picked_eps)]
        order = rng.permutation(len(sub_picked))
        one_per = sub_picked.iloc[order].drop_duplicates("episode_uid", keep="first")
        wins = one_per["global_index"].to_numpy(dtype=np.int64)[:cls_target]
        common_win_selected[cls_name] = int(len(wins))
        common_indices.extend(wins.tolist())

    all_idx = np.sort(np.array(rare_indices + common_indices, dtype=np.int64))
    sel_df = train_df.iloc[all_idx]

    # Auditoria de nao-adjacencia no proprio lote amostrado
    adj_dups = 0
    if len(sel_df) > 1:
        s = sel_df.sort_values(["episode_uid", "label_frame"])
        same_ep = s["episode_uid"] == s["episode_uid"].shift(1)
        gap = s["label_frame"] - s["label_frame"].shift(1)
        adj_dups = int((same_ep & (gap <= CONTIGUOUS_GAP_MAX)).sum())

    n_rare = len(rare_indices)
    n_common = len(common_indices)
    meta = {
        "ratio_target": f"1:{rare_ratio_denom}",
        "total_samples": int(len(all_idx)),
        "rare_samples": int(n_rare),
        "common_samples": int(n_common),
        "effective_rare_fraction": round(n_rare / max(len(all_idx), 1), 6),
        "effective_rare_to_common_ratio": round(n_rare / max(n_common, 1), 6),
        "unique_episodes_drawn": int(sel_df["episode_uid"].nunique()),
        "unique_demos_drawn": int(sel_df["demo_id"].nunique()),
        "unique_matches_drawn": int(sel_df["match_id"].nunique()),
        "unique_players_drawn": int(sel_df["player_id"].nunique()),
        "rare_episodes_drawn": rare_ep_selected,
        "rare_windows_drawn": rare_win_selected,
        "common_windows_drawn": common_win_selected,
        "adjacent_window_duplications": adj_dups,
        "adjacent_window_duplication_rate": round(adj_dups / max(len(all_idx), 1), 6),
        "max_windows_per_rare_episode": max_windows_per_rare_ep,
        "max_episodes_per_round": max_episodes_per_round,
        "max_rare_episodes_per_demo": max_rare_ep_per_demo,
        "max_common_episodes_per_demo": max_common_ep_per_demo,
    }
    return all_idx, meta


# ------------------------------------------------------------------------------
# Losses
# ------------------------------------------------------------------------------

def moderate_class_weights(
    counts: np.ndarray, lo: float = 0.3, hi: float = 3.0
) -> np.ndarray:
    """Pesos moderados (cap 10x menor que o normal, para nao combinar oversampling
    com pesos extremos): sqrt(cmax / c_i), clip em [lo, hi], normalizados pela media.
    """
    counts = np.asarray(counts, dtype=np.float64)
    safe = np.maximum(counts, 1.0)
    raw = np.sqrt(safe.max() / safe)
    w = np.clip(raw, lo, hi)
    if w.mean() > 0:
        w = w / w.mean()
    return w


class FocalCE(nn.Module):
    def __init__(self, weight: Optional[torch.Tensor] = None, gamma: float = 0.0):
        super().__init__()
        self.register_buffer("weight", weight if weight is not None else None)
        self.gamma = float(gamma)

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        logp = F.log_softmax(logits, dim=-1)
        logp_t = logp.gather(1, target.unsqueeze(1)).squeeze(1)
        p_t = logp_t.exp()
        loss = -((1.0 - p_t) ** self.gamma) * logp_t
        if self.weight is not None:
            loss = loss * self.weight[target]
        return loss.mean()


# ------------------------------------------------------------------------------
# Metricas e Score (Secoes 6-9)
# ------------------------------------------------------------------------------

def compute_classification_metrics(
    preds: np.ndarray, targets: np.ndarray, class_names: List[str]
) -> Dict[str, Any]:
    per_class: Dict[str, Any] = {}
    f1s: List[float] = []
    recalls: List[float] = []
    for idx, name in enumerate(class_names):
        sup = int(np.sum(targets == idx))
        if sup == 0:
            per_class[name] = {
                "support": 0, "actual_count": 0, "predicted_count": int(np.sum(preds == idx)),
                "precision": "N/A", "recall": "N/A", "f1": "N/A",
                "tp": 0, "fp": int(np.sum(preds == idx)), "fn": 0,
            }
            continue
        tp = int(np.sum((preds == idx) & (targets == idx)))
        fp = int(np.sum((preds == idx) & (targets != idx)))
        fn = int(np.sum((preds != idx) & (targets == idx)))
        pred_cnt = int(np.sum(preds == idx))
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
        per_class[name] = {
            "support": sup,
            "actual_count": sup,
            "predicted_count": pred_cnt,
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f1), 4),
            "tp": tp, "fp": fp, "fn": fn,
        }
        f1s.append(f1)
        recalls.append(r)
    return {
        "macro_f1": round(float(np.mean(f1s)) if f1s else 0.0, 4),
        "balanced_accuracy": round(float(np.mean(recalls)) if recalls else 0.0, 4),
        "active_classes_count": len(f1s),
        "total_classes_count": len(class_names),
        "per_class": per_class,
    }


def compute_spot_ranking_metrics(
    logits: np.ndarray,
    targets: np.ndarray,
    spot_mask: np.ndarray,
    cand_mask: np.ndarray,
    sup_spot: np.ndarray,
) -> Dict[str, Any]:
    elig = spot_mask.astype(bool)
    n_elig = int(elig.sum())
    if n_elig == 0:
        return {"mrr": 0.0, "top1": 0.0, "top5": 0.0, "invalid_masked": 0, "support": 0}
    lo = logits[elig]
    tg = targets[elig]
    valid = cand_mask[elig] & sup_spot[None, :]
    preds_top1 = np.argmax(lo, axis=1)
    invalid = int(np.sum(~valid[np.arange(n_elig), preds_top1]))
    top1 = float(np.mean(preds_top1 == tg))
    order = np.argsort(-lo, axis=1)
    ranks = np.argmax(order == tg[:, None], axis=1) + 1
    mrr = float(np.mean(1.0 / ranks))
    top5 = float(np.mean(ranks <= 5))
    return {
        "mrr": round(mrr, 4),
        "top1": round(top1, 4),
        "top5": round(top5, 4),
        "invalid_masked": invalid,
        "support": n_elig,
    }


def compute_rare_state_score(st: Dict[str, Any]) -> float:
    pc = st["per_class"]
    def f1_of(c: str) -> float:
        v = pc.get(c, {}).get("f1", 0.0)
        return float(v) if isinstance(v, (int, float)) else 0.0
    return round(
        RARE_STATE_SCORE_WEIGHTS["OBJECTIVE_F1"] * f1_of("OBJECTIVE")
        + RARE_STATE_SCORE_WEIGHTS["RETAKE_F1"] * f1_of("RETAKE")
        + RARE_STATE_SCORE_WEIGHTS["SAVE_F1"] * f1_of("SAVE")
        + RARE_STATE_SCORE_WEIGHTS["HOLD_F1"] * f1_of("HOLD")
        + RARE_STATE_SCORE_WEIGHTS["STAGING_F1"] * f1_of("STAGING")
        + RARE_STATE_SCORE_WEIGHTS["PositioningStateMacroF1"] * float(st["macro_f1"]),
        6,
    )


def state_consistent_exit_trigger(
    pred_state: np.ndarray, raw_pred_tg: np.ndarray
) -> np.ndarray:
    """Mapeamento deterministico estado -> exit_trigger onde a dependencia eh 100%,
    mantendo a head neural onde o estado admite multiplos gatilhos (OBJECTIVE/SAVE).
    """
    out = raw_pred_tg.copy()
    st_to_tg = {
        STATE_MAP["TRANSIT"]: EXIT_TRIGGER_MAP["TIME"],
        STATE_MAP["CLEARANCE"]: EXIT_TRIGGER_MAP["CONTACT"],
        STATE_MAP["STAGING"]: EXIT_TRIGGER_MAP["UTILITY_EXPIRED"],
        STATE_MAP["HOLD"]: EXIT_TRIGGER_MAP["FIRST_KILL"],
        STATE_MAP["RETAKE"]: EXIT_TRIGGER_MAP["TIME"],
    }
    for s_idx, tg_idx in st_to_tg.items():
        out[pred_state == s_idx] = tg_idx
    return out


def evaluate_full_validation(
    model: PositioningTransformerV2RealTemporal,
    val_ds: CanonicalV2PositioningDataset,
    batch_size: int = 256,
    label: str = "val",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        collate_fn=canonical_v2_collate_fn, num_workers=0,
    )
    model.eval()
    total = len(val_ds)

    pred = {k: [] for k in ["state", "to", "ns", "tr", "tg", "spot", "spot_mask", "cand_mask"]}
    targ = {k: [] for k in ["state", "to", "ns", "tr", "tg", "spot"]}
    ns_mask: List[np.ndarray] = []

    t0 = time.time()
    done = 0
    with torch.no_grad():
        for b in loader:
            out = model(
                self_history=b["self_history"], teammates=b["teammates"],
                temporal_mask=b["temporal_mask"], candidate_mask=b["candidate_mask"],
                team_idx=b["team_idx"], role_idx=b["role_idx"], stage_idx=b["stage_idx"],
            )
            pred["state"].append(torch.argmax(out["logits_state"], 1).numpy())
            targ["state"].append(b["positioning_state"].numpy())

            lo = out["logits_transition_occurs"].numpy()
            p1 = np.exp(lo[:, 1] - np.logaddexp(lo[:, 0], lo[:, 1]))
            pred["to"].append((p1 >= SELECTED_TRANSITION_THRESHOLD).astype(np.int64))
            targ["to"].append(b["sector_transition_occurs"].numpy())

            pred["ns"].append(torch.argmax(out["logits_next_sector"], 1).numpy())
            targ["ns"].append(b["next_sector"].numpy())
            ns_mask.append((
                (b["sector_transition_occurs"] == 1)
                & (b["next_sector_loss_mask"] > 0.5)
            ).numpy())

            pred["spot"].append(out["logits_spot"].numpy())
            targ["spot"].append(b["candidate_spot_idx"].numpy())
            pred["spot_mask"].append(b["spot_loss_mask"].numpy())
            pred["cand_mask"].append(b["candidate_mask"].numpy())

            pred["tr"].append(torch.argmax(out["logits_transition"], 1).numpy())
            targ["tr"].append(b["transition"].numpy())

            pred["tg"].append(torch.argmax(out["logits_trigger"], 1).numpy())
            targ["tg"].append(b["exit_trigger"].numpy())

            done += len(b["positioning_state"])
            if done % 102400 == 0:
                el = time.time() - t0
                print(f"    [{label}] {done}/{total} ({done/el:.0f} amostras/s)", flush=True)

    elapsed = time.time() - t0
    print(f"  [{label}] Validation: {total} sequencias em {elapsed:.1f}s ({total/elapsed:.0f}/s)", flush=True)

    p_st = np.concatenate(pred["state"])
    t_st = np.concatenate(targ["state"])
    p_tg_raw = np.concatenate(pred["tg"])
    t_tg = np.concatenate(targ["tg"])
    p_tg_cons = state_consistent_exit_trigger(p_st, p_tg_raw)

    ns_m = np.concatenate(ns_mask)
    ns_metrics = compute_classification_metrics(
        np.concatenate(pred["ns"])[ns_m], np.concatenate(targ["ns"])[ns_m], NEXT_SECTOR_NAMES
    )
    ns_metrics["eligible_count"] = int(ns_m.sum())

    sup_spot = load_supervised_spot_mask().numpy().astype(bool)
    spot_metrics = compute_spot_ranking_metrics(
        np.concatenate(pred["spot"]),
        np.concatenate(targ["spot"]),
        np.concatenate(pred["spot_mask"]).astype(bool),
        np.concatenate(pred["cand_mask"]).astype(bool),
        sup_spot,
    )

    st_metrics = compute_classification_metrics(p_st, t_st, STATE_NAMES)
    to_metrics = compute_classification_metrics(
        np.concatenate(pred["to"]), np.concatenate(targ["to"]),
        ["NO_TRANSITION", "TRANSITION_OCCURS"],
    )
    tr_metrics = compute_classification_metrics(
        np.concatenate(pred["tr"]), np.concatenate(targ["tr"]), TRANSITION_NAMES
    )
    tg_raw_metrics = compute_classification_metrics(p_tg_raw, t_tg, EXIT_TRIGGER_NAMES)
    tg_cons_metrics = compute_classification_metrics(p_tg_cons, t_tg, EXIT_TRIGGER_NAMES)

    metrics = {
        "validation_total_indexed": total,
        "validation_total_evaluated": total,
        "transition_threshold_applied": SELECTED_TRANSITION_THRESHOLD,
        "rare_state_score": compute_rare_state_score(st_metrics),
        "positioning_state": st_metrics,
        "sector_transition_occurs": to_metrics,
        "next_sector": ns_metrics,
        "transition": tr_metrics,
        "exit_trigger": tg_raw_metrics,
        "spot_ranking": spot_metrics,
    }
    exit_dep = {
        "raw_neural_exit_trigger": tg_raw_metrics,
        "state_consistent_exit_trigger": tg_cons_metrics,
    }
    return metrics, exit_dep


def evaluate_gates(
    metrics: Dict[str, Any],
    spot_ok: bool,
    frozen_ok: bool,
) -> Dict[str, Any]:
    st = metrics["positioning_state"]
    to = metrics["sector_transition_occurs"]
    ns = metrics["next_sector"]
    tr = metrics["transition"]
    sp = metrics["spot_ranking"]

    def get_m(block: Dict[str, Any], cls: str, key: str) -> Optional[float]:
        v = block["per_class"].get(cls, {}).get(key)
        return float(v) if isinstance(v, (int, float)) else None

    # Secao 8: Gates de preservacao
    pres_gates = {
        "sector_transition_macro_f1_ge_0_57": to["macro_f1"] >= 0.57,
        "transition_occurs_recall_ge_0_35": (get_m(to, "TRANSITION_OCCURS", "recall") or 0.0) >= 0.35,
        "no_transition_recall_ge_0_78": (get_m(to, "NO_TRANSITION", "recall") or 0.0) >= 0.78,
        "next_sector_macro_f1_ge_0_48": ns["macro_f1"] >= 0.48,
        "transition_macro_f1_ge_0_60": tr["macro_f1"] >= 0.60,
        "spot_mrr_ge_0_76": sp["mrr"] >= 0.76,
        "spot_top5_ge_0_955": sp["top5"] >= 0.955,
        "invalid_masked_eq_0": sp["invalid_masked"] == 0,
        "spot_head_bitwise_identical": bool(spot_ok),
        "frozen_heads_and_early_blocks_bitwise_identical": bool(frozen_ok),
    }

    # Secao 7: Gates das classes raras e globais de PositioningState
    rare_gates = {
        "objective_recall_ge_0_30": (get_m(st, "OBJECTIVE", "recall") or 0.0) >= 0.30,
        "objective_precision_ge_0_20": (get_m(st, "OBJECTIVE", "precision") or 0.0) >= 0.20,
        "objective_f1_ge_0_24": (get_m(st, "OBJECTIVE", "f1") or 0.0) >= 0.24,
        "retake_recall_ge_0_25": (get_m(st, "RETAKE", "recall") or 0.0) >= 0.25,
        "retake_precision_ge_0_20": (get_m(st, "RETAKE", "precision") or 0.0) >= 0.20,
        "retake_f1_ge_0_22": (get_m(st, "RETAKE", "f1") or 0.0) >= 0.22,
        "save_recall_ge_0_20": (get_m(st, "SAVE", "recall") or 0.0) >= 0.20,
        "save_precision_ge_0_15": (get_m(st, "SAVE", "precision") or 0.0) >= 0.15,
        "save_f1_ge_0_17": (get_m(st, "SAVE", "f1") or 0.0) >= 0.17,
        "positioning_state_macro_f1_ge_0_40": st["macro_f1"] >= 0.40,
        "positioning_state_balanced_acc_ge_0_45": st["balanced_accuracy"] >= 0.45,
        "hold_recall_ge_0_40": (get_m(st, "HOLD", "recall") or 0.0) >= 0.40,
        "staging_recall_ge_0_25": (get_m(st, "STAGING", "recall") or 0.0) >= 0.25,
        "clearance_recall_ge_0_75": (get_m(st, "CLEARANCE", "recall") or 0.0) >= 0.75,
    }
    return {
        "preservation_gates": pres_gates,
        "rare_and_state_gates": rare_gates,
        "all_preservation_passed": all(pres_gates.values()),
        "all_rare_passed": all(rare_gates.values()),
    }


# ------------------------------------------------------------------------------
# Treino de um experimento
# ------------------------------------------------------------------------------

def train_experiment(
    base_state: Dict[str, torch.Tensor],
    train_ds: CanonicalV2PositioningDataset,
    indices: np.ndarray,
    state_weights: torch.Tensor,
    gamma: float,
    use_consistency: bool,
    consistency_lambda: float,
    epochs: int,
    label: str,
) -> Tuple[PositioningTransformerV2RealTemporal, Dict[str, Any]]:
    sup = load_supervised_spot_mask()
    model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup)
    model.load_state_dict(copy.deepcopy(base_state))
    freeze_info = apply_selective_freeze(model)
    assert_frozen_invariants(model)

    layer2_norm, heads = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if name.startswith("transformer.layers.2.") or name.startswith("norm."):
            layer2_norm.append(p)
        else:
            heads.append(p)

    opt = optim.AdamW(
        [{"params": layer2_norm, "lr": 1e-5},
         {"params": heads, "lr": 1e-4}],
        weight_decay=1e-4,
    )
    criterion = FocalCE(weight=state_weights, gamma=gamma)
    loader = DataLoader(
        Subset(train_ds, indices.tolist()),
        batch_size=128, shuffle=True,
        collate_fn=canonical_v2_collate_fn, num_workers=0,
    )

    last_block_grad = False
    epoch_logs: List[Dict[str, Any]] = []
    t0 = time.time()

    for ep in range(epochs):
        model.train()
        tot_loss = 0.0
        tot_cons = 0.0
        n_seen = 0
        for b in loader:
            opt.zero_grad(set_to_none=True)
            kw = dict(
                self_history=b["self_history"], teammates=b["teammates"],
                temporal_mask=b["temporal_mask"], candidate_mask=b["candidate_mask"],
                team_idx=b["team_idx"], role_idx=b["role_idx"], stage_idx=b["stage_idx"],
            )
            out = model(**kw)
            loss = criterion(out["logits_state"], b["positioning_state"])
            l_cons = torch.zeros((), dtype=torch.float32)
            if use_consistency:
                out_b = model(**kw)
                pa = F.softmax(out["logits_state"], dim=-1)
                pb = F.softmax(out_b["logits_state"], dim=-1)
                l_cons = F.mse_loss(pa, pb)
                loss = loss + consistency_lambda * l_cons

            loss.backward()
            if not last_block_grad:
                g = next(model.transformer.layers[2].parameters()).grad
                last_block_grad = bool(g is not None and float(g.abs().sum()) > 0.0)
            opt.step()

            bs = len(b["positioning_state"])
            tot_loss += float(loss.item()) * bs
            tot_cons += float(l_cons.item()) * bs
            n_seen += bs

        entry = {
            "epoch": ep + 1,
            "train_loss_mean": round(tot_loss / max(n_seen, 1), 6),
            "consistency_loss_mean": round(tot_cons / max(n_seen, 1), 6),
            "samples_seen": n_seen,
        }
        epoch_logs.append(entry)
        print(
            f"  [{label}] epoca {ep+1}/{epochs} loss={entry['train_loss_mean']:.4f} "
            f"consist={entry['consistency_loss_mean']:.6f}",
            flush=True,
        )

    model.eval()
    return model, {
        "epochs_executed": epochs,
        "epoch_logs": epoch_logs,
        "final_loss": {
            "total_train_mean": epoch_logs[-1]["train_loss_mean"],
            "consistency_loss": epoch_logs[-1]["consistency_loss_mean"],
        },
        "train_seconds": round(time.time() - t0, 1),
        **freeze_info,
        "last_block_received_gradient": last_block_grad,
    }


def main() -> int:
    print("=" * 80)
    print("MARCO 2B.3.5: RECUPERACAO EPISODICA DE OBJECTIVE, RETAKE E SAVE")
    print("=" * 80)
    set_seed(SEED)

    # 1. Integridade dos checkpoints base
    sha_base = sha256_file(BASE_CKPT)
    assert sha_base == EXPECTED_BASE_SHA256, f"base checkpoint divergente: {sha_base}"
    sha_prior = sha256_file(PRIOR_PATCH_CKPT)
    sha_root = sha256_file(ROOT_CANDIDATE_CKPT)

    input_snap = {
        "schema": "csbot.rare_episode_patch.input_snapshot.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "milestone": "2B.3.5",
        "base_checkpoint": str(BASE_CKPT.relative_to(REPO_ROOT)),
        "base_checkpoint_sha256": sha_base,
        "prior_patch_checkpoint_sha256": sha_prior,
        "root_candidate_checkpoint_sha256": sha_root,
        "rare_state_score_weights": RARE_STATE_SCORE_WEIGHTS,
        "selected_transition_threshold": SELECTED_TRANSITION_THRESHOLD,
        "test_and_final_holdout_touched": False,
    }
    (OUT_DIR / "input_snapshot.json").write_text(
        json.dumps(input_snap, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Base checkpoint SHA-256: {sha_base}")

    # 2. Verificar suporte episodico pre-calculado
    ep_support_path = OUT_DIR / "episode_support.json"
    if not ep_support_path.exists():
        raise FileNotFoundError(f"Execute audit_2b35_episodes.py antes: {ep_support_path}")
    ep_support = json.loads(ep_support_path.read_text(encoding="utf-8"))
    if not ep_support.get("train_minimum_support_satisfied", False):
        print("INSUFFICIENT_EPISODE_SUPPORT -> abortando treino conforme Secao 2/12.")
        return 2

    # 3. Datasets e sampler episodico
    sup_mask = load_supervised_spot_mask()
    train_ds = CanonicalV2PositioningDataset(split="train", preload_demos=False)
    val_ds = (
        CanonicalV2PositioningDataset(split="validation", preload_demos=False, max_samples=int(MAX_VAL), seed=SEED)
        if MAX_VAL else CanonicalV2PositioningDataset(split="validation", preload_demos=False)
    )
    if not MAX_VAL:
        assert len(val_ds) == EXPECTED_VAL_SIZE, f"validation {len(val_ds)} != {EXPECTED_VAL_SIZE}"

    train_df = build_train_dataframe()
    assert len(train_df) == len(train_ds), f"train_df {len(train_df)} != {len(train_ds)}"

    idx_a, meta_a = episodic_balanced_sampler(train_df, 4, TARGET_SAMPLES, np.random.RandomState(SEED + 1))
    idx_b, meta_b = episodic_balanced_sampler(train_df, 3, TARGET_SAMPLES, np.random.RandomState(SEED + 2))
    idx_c, meta_c = episodic_balanced_sampler(train_df, 2, TARGET_SAMPLES, np.random.RandomState(SEED + 3))

    sampler_cfg = {
        "schema": "csbot.rare_episode_patch.sampler_configuration.v1",
        "grouping_keys": ["demo_id", "round_id", "player_id", "positioning_state", "contiguous_tick_range"],
        "contiguous_gap_max_frames": CONTIGUOUS_GAP_MAX,
        "target_samples_per_experiment": TARGET_SAMPLES,
        "experiments": {
            "experiment_a": meta_a,
            "experiment_b": meta_b,
            "experiment_c": meta_c,
        },
    }
    (OUT_DIR / "sampler_configuration.json").write_text(
        json.dumps(sampler_cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Sampler A(1:4)={meta_a['total_samples']} | B(1:3)={meta_b['total_samples']} | C(1:2)={meta_c['total_samples']}")

    # 4. Pesos de classe (calculados sobre o split Train e moderados para nao somar extremos ao sampler)
    vc = train_df["positioning_state"].value_counts()
    train_counts = np.array([int(vc.get(n, 0)) for n in STATE_NAMES], dtype=np.float64)
    # Exp A usa pesos de classe atuais (sqrt clip [0.1, 10.0]); Exp B e C usam pesos moderados ([0.3, 3.0])
    w_current = np.clip(np.sqrt(train_counts.max() / np.maximum(train_counts, 1.0)), 0.1, 10.0)
    w_current = w_current / w_current.mean()
    w_moderate = moderate_class_weights(train_counts, lo=0.3, hi=3.0)

    print("Pesos A (atuais)   :", [round(float(x), 4) for x in w_current])
    print("Pesos B/C (moderad):", [round(float(x), 4) for x in w_moderate])

    # 5. Hashes antes
    ckpt = torch.load(BASE_CKPT, map_location="cpu")
    base_state = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
    base_model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    base_model.load_state_dict(base_state)
    base_model.eval()
    hashes_before = module_hashes(base_model)

    # 6. Tres experimentos
    plan = [
        ("experiment_a", "Exp A (1:4 + CE balanceada)", idx_a, meta_a, torch.tensor(w_current, dtype=torch.float32), 0.0, False, 0.0),
        ("experiment_b", "Exp B (1:3 + focal gamma=1.0)", idx_b, meta_b, torch.tensor(w_moderate, dtype=torch.float32), 1.0, False, 0.0),
        ("experiment_c", "Exp C (1:2 + focal + consistency)", idx_c, meta_c, torch.tensor(w_moderate, dtype=torch.float32), 1.0, True, 0.2),
    ]
    if EXPERIMENT_FILTER:
        wanted = {x.strip() for x in EXPERIMENT_FILTER.split(",") if x.strip()}
        plan = [p for p in plan if p[0] in wanted]

    exp_results: Dict[str, Any] = {}
    exp_models: Dict[str, PositioningTransformerV2RealTemporal] = {}
    exp_exit_deps: Dict[str, Any] = {}
    exp_gates: Dict[str, Any] = {}
    comparison_summary: Dict[str, Any] = {}

    for key, label, idx, meta, weights, gamma, use_cons, lam in plan:
        print(f"\n=== {label} ===")
        model, train_info = train_experiment(
            base_state=base_state,
            train_ds=train_ds,
            indices=idx,
            state_weights=weights,
            gamma=gamma,
            use_consistency=use_cons,
            consistency_lambda=lam,
            epochs=EPOCHS,
            label=key,
        )
        metrics, exit_dep = evaluate_full_validation(model, val_ds, label=key)
        hashes_after = module_hashes(model)
        spot_ok = hashes_before["head_spot"] == hashes_after["head_spot"]
        frozen_ok = all(
            hashes_before[m] == hashes_after[m]
            for m in (*FROZEN_MODULES, "transformer_layer_0", "transformer_layer_1")
        )
        g_res = evaluate_gates(metrics, spot_ok=spot_ok, frozen_ok=frozen_ok)

        payload = {
            "schema": "csbot.rare_episode_patch.experiment_metrics.v1",
            "experiment": label,
            "config": {
                "sampler_ratio": meta["ratio_target"],
                "gamma": gamma,
                "consistency_loss": use_cons,
                "consistency_lambda": lam,
                "weights": [round(float(x), 6) for x in weights.tolist()],
                "epochs": EPOCHS,
                "lr_last_block": 1e-5,
                "lr_state_head": 1e-4,
                "seed": SEED,
            },
            "sampling": meta,
            "train": train_info,
            "gates": g_res,
            **metrics,
        }
        (OUT_DIR / f"{key}_metrics.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        exp_results[key] = payload
        exp_models[key] = model
        exp_exit_deps[key] = exit_dep
        exp_gates[key] = g_res

        pc = metrics["positioning_state"]["per_class"]
        comparison_summary[key] = {
            "name": label,
            "rare_state_score": metrics["rare_state_score"],
            "all_preservation_passed": g_res["all_preservation_passed"],
            "all_rare_passed": g_res["all_rare_passed"],
            "objective": pc["OBJECTIVE"],
            "retake": pc["RETAKE"],
            "save": pc["SAVE"],
            "hold": pc["HOLD"],
            "staging": pc["STAGING"],
            "clearance": pc["CLEARANCE"],
            "positioning_state_macro_f1": metrics["positioning_state"]["macro_f1"],
            "sector_transition_macro_f1": metrics["sector_transition_occurs"]["macro_f1"],
            "next_sector_macro_f1": metrics["next_sector"]["macro_f1"],
            "transition_macro_f1": metrics["transition"]["macro_f1"],
            "spot_ranking": metrics["spot_ranking"],
        }

    # 7. Selecao: priorizar quem passa nos gates de preservacao; dentro disso, maior RareStateScore
    preserved_keys = [k for k, g in exp_gates.items() if g["all_preservation_passed"]]
    pool = preserved_keys if preserved_keys else list(exp_results.keys())
    selected_key = max(pool, key=lambda k: exp_results[k]["rare_state_score"])
    sel_res = exp_results[selected_key]
    sel_model = exp_models[selected_key]
    sel_gates = exp_gates[selected_key]
    sel_exit = exp_exit_deps[selected_key]

    # 8. Decisao canonica (Secao 12)
    def _num(v: Any) -> float:
        return float(v) if isinstance(v, (int, float)) else 0.0

    pc = sel_res["positioning_state"]["per_class"]
    obj_rec = _num(pc["OBJECTIVE"]["recall"])
    ret_rec = _num(pc["RETAKE"]["recall"])
    sav_rec = _num(pc["SAVE"]["recall"])

    if not sel_gates["all_preservation_passed"]:
        decision = "RARE_EPISODE_PATCH_REGRESSION"
    elif sel_gates["all_rare_passed"]:
        decision = "POSITIONING_TRANSFORMER_READY_FOR_FINAL_EVALUATION"
    elif (obj_rec < 0.05 and ret_rec < 0.05 and sav_rec < 0.05):
        # Nenhum experimento recuperou minimamente OBJECTIVE, RETAKE e SAVE
        any_recovered = any(
            (_num(r["positioning_state"]["per_class"]["OBJECTIVE"]["recall"]) >= 0.05
             or _num(r["positioning_state"]["per_class"]["RETAKE"]["recall"]) >= 0.05
             or _num(r["positioning_state"]["per_class"]["SAVE"]["recall"]) >= 0.05)
            for r in exp_results.values()
        )
        decision = "RARE_EPISODE_PATCH_CONDITIONAL" if any_recovered else "RARE_STATES_REQUIRE_DEDICATED_ARCHITECTURE"
    else:
        decision = "RARE_EPISODE_PATCH_CONDITIONAL"

    # 9. Salvar artefatos finais
    (OUT_DIR / "experiment_comparison.json").write_text(
        json.dumps({
            "schema": "csbot.rare_episode_patch.experiment_comparison.v1",
            "selected_experiment": selected_key,
            "decision": decision,
            "rare_state_score_weights": RARE_STATE_SCORE_WEIGHTS,
            "experiments": comparison_summary,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    hashes_after = module_hashes(sel_model)
    pres_check = {
        "schema": "csbot.rare_episode_patch.preservation_check.v1",
        "selected_experiment": selected_key,
        "spot_ranking_head_bitwise_identical": hashes_before["head_spot"] == hashes_after["head_spot"],
        "sector_transition_head_bitwise_identical": hashes_before["head_transition_occurs"] == hashes_after["head_transition_occurs"],
        "next_sector_head_bitwise_identical": hashes_before["head_next_sector"] == hashes_after["head_next_sector"],
        "transition_head_bitwise_identical": hashes_before["head_transition"] == hashes_after["head_transition"],
        "exit_trigger_head_bitwise_identical": hashes_before["head_exit_trigger"] == hashes_after["head_exit_trigger"],
        "early_blocks_bitwise_identical": (
            hashes_before["transformer_layer_0"] == hashes_after["transformer_layer_0"]
            and hashes_before["transformer_layer_1"] == hashes_after["transformer_layer_1"]
            and hashes_before["player_proj"] == hashes_after["player_proj"]
            and hashes_before["teammate_proj"] == hashes_after["teammate_proj"]
        ),
        "last_block_received_gradient": sel_res["train"]["last_block_received_gradient"],
        "last_block_weights_changed": hashes_before["transformer_layer_2"] != hashes_after["transformer_layer_2"],
        "state_head_weights_changed": hashes_before["head_state"] != hashes_after["head_state"],
        "hashes_before": hashes_before,
        "hashes_after": hashes_after,
        "preservation_gates": sel_gates["preservation_gates"],
    }
    (OUT_DIR / "preservation_check.json").write_text(
        json.dumps(pres_check, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    (OUT_DIR / "exit_trigger_dependency_metrics.json").write_text(
        json.dumps({
            "schema": "csbot.rare_episode_patch.exit_trigger_dependency.v1",
            "selected_experiment": selected_key,
            **sel_exit,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    full_val = {
        "schema": "csbot.rare_episode_patch.full_validation_metrics.v1",
        "selected_experiment": selected_key,
        "decision": decision,
        "validation_total_indexed": sel_res["validation_total_indexed"],
        "validation_total_evaluated": sel_res["validation_total_evaluated"],
        "rare_state_score": sel_res["rare_state_score"],
        "positioning_state": sel_res["positioning_state"],
        "sector_transition_occurs": sel_res["sector_transition_occurs"],
        "next_sector": sel_res["next_sector"],
        "transition": sel_res["transition"],
        "exit_trigger": sel_res["exit_trigger"],
        "spot_ranking": sel_res["spot_ranking"],
        "gates": sel_gates,
    }
    (OUT_DIR / "full_validation_metrics.json").write_text(
        json.dumps(full_val, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    torch.save({
        "schema": "csbot.checkpoint.positioning_v2.rare_episode_patch_v1",
        "milestone": "2B.3.5",
        "selected_experiment": selected_key,
        "decision": decision,
        "rare_state_score": sel_res["rare_state_score"],
        "selected_threshold_transition_occurs": SELECTED_TRANSITION_THRESHOLD,
        "base_checkpoint_sha256": sha_base,
        "model_state_dict": sel_model.state_dict(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, OUT_DIR / "selected_checkpoint.pt")

    print("\n" + "=" * 80)
    print(f"MARCO 2B.3.5 CONCLUIDO | DECISAO: {decision}")
    print(f"  Selecionado: {selected_key} | RareStateScore={sel_res['rare_state_score']:.6f}")
    print(f"  OBJECTIVE: P={pc['OBJECTIVE']['precision']} R={pc['OBJECTIVE']['recall']} F1={pc['OBJECTIVE']['f1']}")
    print(f"  RETAKE   : P={pc['RETAKE']['precision']} R={pc['RETAKE']['recall']} F1={pc['RETAKE']['f1']}")
    print(f"  SAVE     : P={pc['SAVE']['precision']} R={pc['SAVE']['recall']} F1={pc['SAVE']['f1']}")
    print(f"  Preservacao OK: {sel_gates['all_preservation_passed']} | Raras OK: {sel_gates['all_rare_passed']}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
