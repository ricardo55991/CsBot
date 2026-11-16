"""
Fase 3A.3-B - Marco 2B.3.4: Ajuste Multitarefa Conjunto das Heads Temporais Raras.

Executa:
 1. Snapshot e verificacao dos hashes dos checkpoints base (congelados).
 2. Congelamento bitwise de player_proj/teammate_proj/teammate_pool/team_emb/
    role_emb/stage_emb/context_fusion/pos_encoder/transformer.layers[0..1]/head_spot.
 3. Descongelamento de transformer.layers[2], norm e das 5 heads temporais.
 4. Sampler por episodio (1 janela por episodio -> duplicacao adjacente = 0).
 5. Tres experimentos (A: CE balanceada clampada; B: focal balanceada clampada;
    C: B + loss de consistencia lambda=0.2), no maximo 3 epocas cada.
 6. Avaliacao na Validation INTEGRAL (501.434 sequencias) para cada experimento.
 7. Selecao pelo TemporalScore congelado (SpotRanking excluida da selecao).
 8. Verificacao de preservacao bitwise e geracao de todos os JSONs de evidencia.

Governanca:
 - Nao toca em Test nem Final Holdout (o dataloader levanta ValueError por design).
 - Classes com support=0 sao reportadas como "N/A" (nunca 0.0).
 - Nao sobrescreve nenhum checkpoint base.
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
from torch.utils.data import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.phase3a_training.positioning_model_v2 import (  # noqa: E402
    PositioningTransformerV2RealTemporal,
    STATE_NAMES,
    NEXT_SECTOR_NAMES,
    TRANSITION_NAMES,
    EXIT_TRIGGER_NAMES,
)
from tools.phase3a_training.canonical_v2_dataloader import (  # noqa: E402
    CanonicalV2PositioningDataset,
    canonical_v2_collate_fn,
    load_supervised_spot_mask,
    INDEX_DIR,
    SIDECAR_DIR,
)

SEED = 42028
_OUT_OVERRIDE = os.environ.get("CSBOT_2B34_OUT_DIR", "").strip()
OUT_DIR = (
    Path(_OUT_OVERRIDE) if _OUT_OVERRIDE else
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" /
    "rare_class_patch_v1" / "joint_temporal_patch_v1"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_PATCH_CKPT = (
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" /
    "rare_class_patch_v1" / "selected_patch_checkpoint.pt"
)
ROOT_CANDIDATE_CKPT = (
    REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" /
    "full_training" / "selected_candidate.pt"
)

EXPECTED_PATCH_SHA256 = "e0a1c5d5d9727e4986d647fb3fcd2a164de269642c078c850c6667bb55fd9e03"
EXPECTED_ROOT_SHA256 = "4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352"
EXPECTED_VAL_SIZE = 501434

RARE_STATES = ["HOLD", "OBJECTIVE", "STAGING", "RETAKE", "SAVE"]

# Overrides de execucao (smoke test). Ausentes => valores canonicos do marco.
EPOCHS = int(os.environ.get("CSBOT_2B34_EPOCHS", "3"))
MAX_TRAIN = os.environ.get("CSBOT_2B34_MAX_TRAIN")
MAX_VAL = os.environ.get("CSBOT_2B34_MAX_VAL")
EXPERIMENT_FILTER = os.environ.get("CSBOT_2B34_EXPERIMENTS", "").strip()
TARGET_SAMPLES = int(os.environ.get("CSBOT_2B34_TARGET_SAMPLES", "48000"))

# Pesos congelados do TemporalScore (frozen_temporal_score.json)
SCORE_WEIGHTS = {
    "state_macro_f1": 0.20,
    "sector_transition_macro_f1": 0.20,
    "next_sector_macro_f1": 0.15,
    "transition_macro_f1": 0.20,
    "exit_trigger_macro_f1": 0.15,
    "rare_state_recall_mean": 0.10,
}

THRESHOLD_GRID = [round(0.40 + 0.025 * i, 3) for i in range(13)]  # 0.400 .. 0.700

HEAD_KEYS = {
    "state": "positioning_state",
    "transition_occurs": "sector_transition_occurs",
    "next_sector": "next_sector",
    "transition": "transition",
    "exit_trigger": "exit_trigger",
}

FROZEN_HASH_KEYS = [
    "head_spot",
    "transformer_layer_0",
    "transformer_layer_1",
    "transformer_layer_2",
    "player_proj",
    "teammate_proj",
]


# ------------------------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------------------------

def set_seed(seed: int = SEED) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_submodule_hash(module: nn.Module) -> str:
    h = hashlib.sha256()
    for p in module.parameters():
        h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def module_hashes(model: PositioningTransformerV2RealTemporal) -> Dict[str, str]:
    return {
        "head_spot": compute_submodule_hash(model.head_spot),
        "transformer_layer_0": compute_submodule_hash(model.transformer.layers[0]),
        "transformer_layer_1": compute_submodule_hash(model.transformer.layers[1]),
        "transformer_layer_2": compute_submodule_hash(model.transformer.layers[2]),
        "player_proj": compute_submodule_hash(model.player_proj),
        "teammate_proj": compute_submodule_hash(model.teammate_proj),
        "teammate_pool": compute_submodule_hash(model.teammate_pool),
        "context_fusion": compute_submodule_hash(model.context_fusion),
        "pos_encoder": compute_submodule_hash(model.pos_encoder),
        "norm": compute_submodule_hash(model.norm),
        "head_state": compute_submodule_hash(model.head_state),
        "head_transition_occurs": compute_submodule_hash(model.head_transition_occurs),
        "head_next_sector": compute_submodule_hash(model.head_next_sector),
        "head_transition": compute_submodule_hash(model.head_transition),
        "head_exit_trigger": compute_submodule_hash(model.head_exit_trigger),
    }


# ------------------------------------------------------------------------------
# Congelamento seletivo
# ------------------------------------------------------------------------------

UNFROZEN_PREFIXES = (
    "transformer.layers.2.",
    "norm.",
    "head_state.",
    "head_transition_occurs.",
    "head_next_sector.",
    "head_transition.",
    "head_exit_trigger.",
)


def apply_selective_freeze(model: PositioningTransformerV2RealTemporal) -> Dict[str, int]:
    """Congela tudo e reabilita somente o ultimo bloco + heads temporais."""
    for p in model.parameters():
        p.requires_grad = False

    n_train, n_frozen = 0, 0
    for name, p in model.named_parameters():
        if name.startswith(UNFROZEN_PREFIXES):
            p.requires_grad = True
            n_train += p.numel()
        else:
            n_frozen += p.numel()
    return {"trainable_params": n_train, "frozen_params": n_frozen}


def assert_frozen_below_layer2(model: PositioningTransformerV2RealTemporal) -> None:
    """Garante que nenhum parametro dos blocos 0 e 1 esteja treinavel."""
    for layer_idx in (0, 1):
        for name, p in model.transformer.layers[layer_idx].named_parameters():
            assert not p.requires_grad, f"bloco {layer_idx}.{name} deveria estar congelado"
    for name in ("player_proj", "teammate_proj", "teammate_pool", "team_emb",
                 "role_emb", "stage_emb", "context_fusion", "pos_encoder", "head_spot"):
        mod = getattr(model, name)
        for pname, p in mod.named_parameters():
            assert not p.requires_grad, f"{name}.{pname} deveria estar congelado"


# ------------------------------------------------------------------------------
# Losses
# ------------------------------------------------------------------------------

def clamped_class_weights(
    counts: np.ndarray, lo: float = 0.1, hi: float = 10.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Pesos balanceados por classe via sqrt-inverse-frequency, clampados ANTES
    da normalizacao final.

    Correcao do defeito D10: a versao anterior normalizava por media 1 e DEPOIS
    aplicava clip em [lo, hi]. Com desequilibrio extremo, as classes de
    frequencia media colapsavam todas no piso lo (razao 1:1), apagando o
    balanceamento que deveriam preservar.

    Nova regra:
      raw_i = sqrt(count_max / count_i)
      w_i   = clip(raw_i, lo, hi)          # clip ANTES de normalizar
      w     = w / mean(w)                  # normalizacao nao altera a razao

    Como raw_i >= 1 para todo i (sqrt de uma razao >= 1), a normalizacao final
    mantem w_i em [1/mean, hi/mean], contido em [lo, hi] porque mean <= hi.
    A razao maxima entre classes fica limitada a hi/lo (10:1), mas as classes
    medias nao colapsam mais no piso.

    Retorna (pesos_finais_normalizados, pesos_sqrt_brutos_antes_do_clamp).
    """
    counts = np.asarray(counts, dtype=np.float64)
    safe = np.maximum(counts, 1.0)
    cmax = safe.max()
    raw_sqrt = np.sqrt(cmax / safe)
    clamped = np.clip(raw_sqrt, lo, hi)
    if clamped.mean() > 0:
        clamped = clamped / clamped.mean()
    return clamped, raw_sqrt


class MaskedFocalCE(nn.Module):
    """Cross-entropy focal com pesos por classe e mascara opcional por amostra."""

    def __init__(self, weight: Optional[torch.Tensor] = None, gamma: float = 0.0):
        super().__init__()
        self.register_buffer("weight", weight if weight is not None else None)
        self.gamma = float(gamma)

    def forward(
        self,
        logits: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        logp = F.log_softmax(logits, dim=-1)
        logp_t = logp.gather(1, target.unsqueeze(1)).squeeze(1)
        p_t = logp_t.exp()
        loss = -((1.0 - p_t) ** self.gamma) * logp_t
        if self.weight is not None:
            loss = loss * self.weight[target]
        if mask is not None:
            m = mask.float()
            denom = m.sum().clamp(min=1.0)
            return (loss * m).sum() / denom
        return loss.mean()


CONSISTENCY_KEYS = ("logits_state", "logits_transition_occurs",
                    "logits_next_sector", "logits_transition", "logits_trigger")


def consistency_loss(out_a: Dict[str, torch.Tensor],
                     out_b: Dict[str, torch.Tensor]) -> torch.Tensor:
    """Divergencia simetrica entre duas passadas estocasticas (dropout)."""
    total = None
    for k in CONSISTENCY_KEYS:
        pa = F.softmax(out_a[k], dim=-1)
        pb = F.softmax(out_b[k], dim=-1)
        term = F.mse_loss(pa, pb)
        total = term if total is None else total + term
    return total / len(CONSISTENCY_KEYS)


# ------------------------------------------------------------------------------
# Metricas
# ------------------------------------------------------------------------------

def compute_classification_metrics(
    preds: np.ndarray, targets: np.ndarray, class_names: List[str]
) -> Dict[str, Any]:
    per_class: Dict[str, Any] = {}
    active_f1s: List[float] = []
    active_recalls: List[float] = []

    for c_idx, c_name in enumerate(class_names):
        support = int(np.sum(targets == c_idx))
        if support == 0:
            per_class[c_name] = {
                "support": 0, "precision": "N/A", "recall": "N/A", "f1": "N/A",
            }
            continue
        tp = int(np.sum((preds == c_idx) & (targets == c_idx)))
        fp = int(np.sum((preds == c_idx) & (targets != c_idx)))
        fn = int(np.sum((preds != c_idx) & (targets == c_idx)))
        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        per_class[c_name] = {
            "support": support,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "tp": tp, "fp": fp, "fn": fn,
        }
        active_f1s.append(f1)
        active_recalls.append(rec)

    macro_f1 = float(np.mean(active_f1s)) if active_f1s else 0.0
    balanced_acc = float(np.mean(active_recalls)) if active_recalls else 0.0
    return {
        "macro_f1": round(macro_f1, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "active_classes_count": len(active_f1s),
        "total_classes_count": len(class_names),
        "per_class": per_class,
    }


def compute_spot_ranking_metrics(
    logits: np.ndarray, targets: np.ndarray, masks: np.ndarray,
    candidate_mask: np.ndarray, supervised_spot_mask: np.ndarray,
) -> Dict[str, Any]:
    valid = np.where(masks)[0]
    n_valid = len(valid)
    if n_valid == 0:
        return {"mrr": 0.0, "top1": 0.0, "top5": 0.0,
                "invalid_masked": 0, "support": 0}

    sub_logits = logits[valid].copy()
    sub_targets = targets[valid]
    invalid_masked = 0
    for i, row in enumerate(valid):
        allowed = candidate_mask[row] & supervised_spot_mask
        if not allowed.any():
            allowed = candidate_mask[row]
        if not allowed.any():
            invalid_masked += 1
            continue
        sub_logits[i, ~allowed] = -1e9

    order = np.argsort(-sub_logits, axis=1)
    ranks = np.empty(len(valid), dtype=np.int64)
    for i in range(len(valid)):
        pos = np.where(order[i] == sub_targets[i])[0]
        ranks[i] = int(pos[0]) + 1 if len(pos) else 10 ** 6

    mrr = float(np.mean(1.0 / ranks))
    top1 = float(np.mean(ranks <= 1))
    top5 = float(np.mean(ranks <= 5))
    return {
        "mrr": round(mrr, 4),
        "top1": round(top1, 4),
        "top5": round(top5, 4),
        "invalid_masked": int(invalid_masked),
        "support": int(n_valid),
    }


def threshold_sweep(
    probs: np.ndarray, targets: np.ndarray, thresholds: List[float],
    names: Tuple[str, str] = ("NO_TRANSITION", "TRANSITION_OCCURS"),
) -> List[Dict[str, Any]]:
    out = []
    for t in thresholds:
        preds = (probs >= t).astype(np.int64)
        tp = int(np.sum((preds == 1) & (targets == 1)))
        fp = int(np.sum((preds == 1) & (targets == 0)))
        fn = int(np.sum((preds == 0) & (targets == 1)))
        tn = int(np.sum((preds == 0) & (targets == 0)))
        surv = int(np.sum(targets == 1))
        nosurv = int(np.sum(targets == 0))

        p1 = tp / (tp + fp) if (tp + fp) else 0.0
        r1 = tp / (tp + fn) if (tp + fn) else 0.0
        f1_1 = 2 * p1 * r1 / (p1 + r1) if (p1 + r1) else 0.0
        p0 = tn / (tn + fn) if (tn + fn) else 0.0
        r0 = tn / (tn + fp) if (tn + fp) else 0.0
        f1_0 = 2 * p0 * r0 / (p0 + r0) if (p0 + r0) else 0.0

        out.append({
            "threshold": t,
            "macro_f1": round(float((f1_0 + f1_1) / 2), 4),
            "balanced_accuracy": round(float((r0 + r1) / 2), 4),
            f"{names[0]}_precision": round(p0, 4),
            f"{names[0]}_recall": round(r0, 4),
            f"{names[1]}_precision": round(p1, 4),
            f"{names[1]}_recall": round(r1, 4),
            "false_positive_rate": round(fp / (fp + tn), 4) if (fp + tn) else 0.0,
            "false_negative_rate": round(fn / (fn + tp), 4) if (fn + tp) else 0.0,
            "predicted_transition_rate": round(float(preds.mean()), 4),
            "actual_transition_rate": round(surv / (surv + nosurv), 4) if (surv + nosurv) else 0.0,
        })
    return out


def temporal_score(metrics: Dict[str, Any]) -> float:
    m = metrics
    rare_recalls = []
    for c in RARE_STATES:
        entry = m["positioning_state"]["per_class"].get(c)
        if entry and isinstance(entry.get("recall"), (int, float)):
            rare_recalls.append(float(entry["recall"]))
    rare_mean = float(np.mean(rare_recalls)) if rare_recalls else 0.0
    return round(
        SCORE_WEIGHTS["state_macro_f1"] * m["positioning_state"]["macro_f1"]
        + SCORE_WEIGHTS["sector_transition_macro_f1"] * m["sector_transition_occurs"]["macro_f1"]
        + SCORE_WEIGHTS["next_sector_macro_f1"] * m["next_sector"]["macro_f1"]
        + SCORE_WEIGHTS["transition_macro_f1"] * m["transition"]["macro_f1"]
        + SCORE_WEIGHTS["exit_trigger_macro_f1"] * m["exit_trigger"]["macro_f1"]
        + SCORE_WEIGHTS["rare_state_recall_mean"] * rare_mean,
        6,
    )


# ------------------------------------------------------------------------------
# Amostragem por episodio
# ------------------------------------------------------------------------------

def build_train_frames() -> pd.DataFrame:
    """Le index + sidecar de todos os shards e devolve o DataFrame do split train."""
    index_cols = ["sequence_id", "demo_id", "round_id", "slot", "split",
                  "positioning_state", "next_sector", "transition", "exit_trigger"]
    side_cols = ["sector_transition_occurs"]

    parts = []
    shards = sorted(INDEX_DIR.glob("shard_*.parquet"))
    if not shards:
        raise FileNotFoundError(f"nenhum shard em {INDEX_DIR}")
    for i, shard in enumerate(shards):
        side = SIDECAR_DIR / f"{shard.stem}_labels.parquet"
        if not side.exists():
            continue
        df_b = pd.read_parquet(shard, columns=index_cols)
        df_s = pd.read_parquet(side, columns=side_cols)
        if len(df_b) != len(df_s):
            raise ValueError(f"desalinhamento em {shard.name}: {len(df_b)} != {len(df_s)}")
        mask = df_b["split"] == "train"
        if not mask.any():
            continue
        sub = df_b.loc[mask].copy()
        sub["sector_transition_occurs"] = df_s.loc[mask, "sector_transition_occurs"].values
        sub["shard_idx"] = i
        parts.append(sub)

    if not parts:
        raise ValueError("nenhum registro de train encontrado")

    df = pd.concat(parts, ignore_index=True)
    df["global_index"] = df.index.astype(np.int64)
    df["episode_id"] = (
        df["demo_id"].astype(str) + "_" + df["round_id"].astype(str)
        + "_" + df["slot"].astype(str)
    )
    df["is_transition"] = (
        df["sector_transition_occurs"] == "TRANSITION_OCCURS"
    ).astype(np.int8)
    return df


def _one_window_per_episode(df: pd.DataFrame, rng: np.random.RandomState) -> np.ndarray:
    """Sorteia exatamente uma janela por episodio, de forma vetorizada.

    Embaralha as linhas e mantem a primeira ocorrencia de cada episode_id.
    Garante duplicacao de janelas adjacentes do mesmo episodio = 0.
    """
    if len(df) == 0:
        return np.empty(0, dtype=np.int64)
    order = rng.permutation(len(df))
    picked = df.iloc[order].drop_duplicates(subset="episode_id", keep="first")
    return picked["global_index"].to_numpy(dtype=np.int64)


def episode_sampler(
    train_df: pd.DataFrame,
    mode: str,
    rng: np.random.RandomState,
    target_total: int = TARGET_SAMPLES,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Retorna indices globais de amostra e metadados de amostragem.

    mode='natural': uma janela por episodio, prevalencia natural (com teto de
                    target_total amostras para manter custo computacional fixo).
    mode='1_to_3' : uma janela por episodio positivo + 3x episodios negativos.

    Em ambos os modos nenhuma janela adjacente do mesmo episodio entra:
    a duplicacao adjacente e estruturalmente zero.
    """
    pos = train_df[train_df["is_transition"] == 1]
    neg = train_df[train_df["is_transition"] == 0]

    pos_windows = _one_window_per_episode(pos, rng)
    neg_windows = _one_window_per_episode(neg, rng)

    n_pos_episodes = len(pos_windows)
    n_neg_episodes = len(neg_windows)
    natural_ratio = (
        n_pos_episodes / (n_pos_episodes + n_neg_episodes)
        if (n_pos_episodes + n_neg_episodes) else 0.0
    )

    if mode == "natural":
        want_pos = int(round(target_total * natural_ratio))
        want_neg = target_total - want_pos
    elif mode == "1_to_3":
        want_pos = target_total // 4
        want_neg = target_total - want_pos
    else:
        raise ValueError(f"modo de amostragem desconhecido: {mode}")

    n_pos = min(want_pos, n_pos_episodes)
    n_neg = min(want_neg, n_neg_episodes)

    pos_pick = rng.choice(pos_windows, size=n_pos, replace=False) if n_pos else np.empty(0, np.int64)
    neg_pick = rng.choice(neg_windows, size=n_neg, replace=False) if n_neg else np.empty(0, np.int64)

    idx = np.sort(np.concatenate([pos_pick, neg_pick]))
    n_total = len(idx)
    meta = {
        "sampler": mode,
        "target_total": int(target_total),
        "episodes_positive_available": int(n_pos_episodes),
        "episodes_negative_available": int(n_neg_episodes),
        "natural_episode_ratio": round(float(natural_ratio), 6),
        "row_level_natural_ratio": round(
            float(len(pos) / (len(pos) + len(neg))) if (len(pos) + len(neg)) else 0.0, 6),
        "episodes_positive_drawn": int(n_pos),
        "episodes_negative_drawn": int(n_neg),
        "samples_total": int(n_total),
        "samples_positive": int(n_pos),
        "effective_sampling_ratio": round(n_pos / n_total, 6) if n_total else 0.0,
        "adjacent_window_duplication_rate": 0.0,
        "window_policy": "one_window_per_episode_draw",
        "rng_seed": SEED,
    }
    return idx, meta



# ------------------------------------------------------------------------------
# Avaliacao
# ------------------------------------------------------------------------------

def evaluate_full_validation(
    model: PositioningTransformerV2RealTemporal,
    val_ds: CanonicalV2PositioningDataset,
    batch_size: int = 256,
    label: str = "val",
) -> Dict[str, Any]:
    loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        collate_fn=canonical_v2_collate_fn, num_workers=0,
    )
    model.eval()
    total = len(val_ds)

    pred = {k: [] for k in [
        "state", "to", "ns", "tr", "tg", "spot", "spot_mask", "cand_mask",
    ]}
    targ = {k: [] for k in ["state", "to", "ns", "tr", "tg", "spot"]}
    probs_to: List[np.ndarray] = []
    ns_mask: List[np.ndarray] = []

    t0 = time.time()
    done = 0
    with torch.no_grad():
        for batch in loader:
            out = model(
                self_history=batch["self_history"],
                teammates=batch["teammates"],
                temporal_mask=batch["temporal_mask"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"],
            )
            pred["state"].append(torch.argmax(out["logits_state"], 1).numpy())
            targ["state"].append(batch["positioning_state"].numpy())

            lo = out["logits_transition_occurs"].numpy()
            p1 = np.exp(lo[:, 1] - np.logaddexp(lo[:, 0], lo[:, 1]))
            probs_to.append(p1)
            pred["to"].append((p1 >= 0.5).astype(np.int64))
            targ["to"].append(batch["sector_transition_occurs"].numpy())

            pred["ns"].append(torch.argmax(out["logits_next_sector"], 1).numpy())
            targ["ns"].append(batch["next_sector"].numpy())
            ns_mask.append((
                (batch["sector_transition_occurs"] == 1)
                & (batch["next_sector_loss_mask"] > 0.5)
            ).numpy())

            pred["spot"].append(out["logits_spot"].numpy())
            targ["spot"].append(batch["candidate_spot_idx"].numpy())
            pred["spot_mask"].append(batch["spot_loss_mask"].numpy())
            pred["cand_mask"].append(batch["candidate_mask"].numpy())

            pred["tr"].append(torch.argmax(out["logits_transition"], 1).numpy())
            targ["tr"].append(batch["transition"].numpy())

            pred["tg"].append(torch.argmax(out["logits_trigger"], 1).numpy())
            targ["tg"].append(batch["exit_trigger"].numpy())

            done += len(batch["positioning_state"])
            if done % 51200 == 0:
                el = time.time() - t0
                print(f"    [{label}] {done}/{total} ({done/el:.0f} amostras/s)", flush=True)

    elapsed = time.time() - t0
    print(f"  [{label}] Validation integral: {total} sequencias em {elapsed:.1f}s "
          f"({total/elapsed:.0f} amostras/s)", flush=True)

    pred_to = np.concatenate(pred["to"])
    prob_to = np.concatenate(probs_to)
    targ_to = np.concatenate(targ["to"])
    sweep = threshold_sweep(prob_to, targ_to, THRESHOLD_GRID)

    ns_mask_cat = np.concatenate(ns_mask)
    pred_ns = np.concatenate(pred["ns"])
    targ_ns = np.concatenate(targ["ns"])
    ns_metrics = compute_classification_metrics(
        pred_ns[ns_mask_cat], targ_ns[ns_mask_cat], NEXT_SECTOR_NAMES
    )
    ns_metrics["eligible_count"] = int(ns_mask_cat.sum())

    sup_spot = load_supervised_spot_mask().numpy().astype(bool)
    cand_mask_np = np.concatenate(pred["cand_mask"]).astype(bool)
    spot_metrics = compute_spot_ranking_metrics(
        np.concatenate(pred["spot"]),
        np.concatenate(targ["spot"]),
        np.concatenate(pred["spot_mask"]).astype(bool),
        cand_mask_np,
        sup_spot,
    )

    return {
        "validation_total_indexed": total,
        "validation_total_evaluated": total,
        "positioning_state": compute_classification_metrics(
            np.concatenate(pred["state"]), np.concatenate(targ["state"]), STATE_NAMES),
        "sector_transition_occurs": compute_classification_metrics(
            pred_to, targ_to, ["NO_TRANSITION", "TRANSITION_OCCURS"]),
        "sector_transition_threshold_sweep": sweep,
        "next_sector": ns_metrics,
        "transition": compute_classification_metrics(
            np.concatenate(pred["tr"]), np.concatenate(targ["tr"]), TRANSITION_NAMES),
        "exit_trigger": compute_classification_metrics(
            np.concatenate(pred["tg"]), np.concatenate(targ["tg"]), EXIT_TRIGGER_NAMES),
        "spot_ranking": spot_metrics,
    }


def select_threshold(sweep: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Escolhe threshold que maximiza Macro-F1 sujeito aos pisos contratuais."""
    feasible = [
        s for s in sweep
        if s["TRANSITION_OCCURS_recall"] >= 0.35 and s["NO_TRANSITION_recall"] >= 0.78
    ]
    pool = feasible if feasible else sweep
    best = max(pool, key=lambda s: (s["macro_f1"], s["balanced_accuracy"]))
    best = dict(best)
    best["constraint_satisfied"] = bool(feasible)
    return best


# ------------------------------------------------------------------------------
# Treino
# ------------------------------------------------------------------------------

def train_experiment(
    base_state: Dict[str, torch.Tensor],
    train_ds: CanonicalV2PositioningDataset,
    indices: np.ndarray,
    class_weights: Dict[str, torch.Tensor],
    gamma: float,
    use_consistency: bool,
    consistency_lambda: float,
    epochs: int,
    lr_layer2: float,
    lr_heads: float,
    label: str,
) -> Tuple[PositioningTransformerV2RealTemporal, Dict[str, Any]]:
    sup = load_supervised_spot_mask()
    model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup)
    model.load_state_dict(copy.deepcopy(base_state))
    info = apply_selective_freeze(model)
    assert_frozen_below_layer2(model)

    layer2_norm, heads = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if name.startswith("transformer.layers.2.") or name.startswith("norm."):
            layer2_norm.append(p)
        else:
            heads.append(p)

    opt = optim.AdamW(
        [{"params": layer2_norm, "lr": lr_layer2},
         {"params": heads, "lr": lr_heads}],
        weight_decay=1e-4,
    )

    criterion = {
        "state": MaskedFocalCE(class_weights["state"], gamma),
        "transition_occurs": MaskedFocalCE(class_weights["transition_occurs"], gamma),
        "next_sector": MaskedFocalCE(class_weights["next_sector"], gamma),
        "transition": MaskedFocalCE(class_weights["transition"], gamma),
        "exit_trigger": MaskedFocalCE(class_weights["exit_trigger"], gamma),
    }

    loader = DataLoader(
        torch.utils.data.Subset(train_ds, indices.tolist()),
        batch_size=128, shuffle=True,
        collate_fn=canonical_v2_collate_fn, num_workers=0,
    )

    last_block_grad = False
    epoch_logs: List[Dict[str, Any]] = []
    t_start = time.time()

    for epoch in range(epochs):
        model.train()
        sums = {"total": 0.0, "consistency": 0.0}
        n_seen = 0
        for step, b in enumerate(loader):
            opt.zero_grad(set_to_none=True)
            kw = dict(
                self_history=b["self_history"], teammates=b["teammates"],
                temporal_mask=b["temporal_mask"], candidate_mask=b["candidate_mask"],
                team_idx=b["team_idx"], role_idx=b["role_idx"],
                stage_idx=b["stage_idx"],
            )
            out = model(**kw)

            l_state = criterion["state"](out["logits_state"], b["positioning_state"])
            l_to = criterion["transition_occurs"](
                out["logits_transition_occurs"], b["sector_transition_occurs"])
            l_tr = criterion["transition"](out["logits_transition"], b["transition"])
            l_tg = criterion["exit_trigger"](out["logits_trigger"], b["exit_trigger"])

            ns_mask = (
                (b["sector_transition_occurs"] == 1)
                & (b["next_sector_loss_mask"] > 0.5)
            )
            if int(ns_mask.sum()) > 0:
                l_ns = criterion["next_sector"](
                    out["logits_next_sector"], b["next_sector"], ns_mask)
            else:
                l_ns = torch.zeros((), dtype=torch.float32)

            loss = l_state + l_to + l_ns + l_tr + l_tg
            l_cons = torch.zeros((), dtype=torch.float32)
            if use_consistency:
                out_b = model(**kw)
                l_cons = consistency_loss(out, out_b)
                loss = loss + consistency_lambda * l_cons

            loss.backward()

            if not last_block_grad:
                g = model.transformer.layers[2].parameters().__next__().grad
                last_block_grad = bool(g is not None and float(g.abs().sum()) > 0.0)

            opt.step()
            sums["total"] += float(loss.item()) * len(b["positioning_state"])
            sums["consistency"] += float(l_cons.item()) * len(b["positioning_state"])
            n_seen += len(b["positioning_state"])

        entry = {
            "epoch": epoch + 1,
            "train_loss_mean": round(sums["total"] / max(n_seen, 1), 6),
            "consistency_loss_mean": round(sums["consistency"] / max(n_seen, 1), 6),
            "samples_seen": n_seen,
        }
        epoch_logs.append(entry)
        print(f"  [{label}] epoca {epoch+1}/{epochs} loss={entry['train_loss_mean']:.4f} "
              f"consist={entry['consistency_loss_mean']:.6f}", flush=True)

    model.eval()
    final = {
        "epochs_executed": epochs,
        "epoch_logs": epoch_logs,
        "final_loss": {
            "total_train_mean": epoch_logs[-1]["train_loss_mean"],
            "consistency_loss": epoch_logs[-1]["consistency_loss_mean"],
        },
        "train_seconds": round(time.time() - t_start, 1),
        "trainable_params": info["trainable_params"],
        "frozen_params": info["frozen_params"],
        "last_block_received_gradient": last_block_grad,
    }
    return model, final


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def main() -> int:
    print("=" * 80)
    print("MARCO 2B.3.4: AJUSTE MULTITAREFA CONJUNTO DAS HEADS TEMPORAIS RARAS")
    print("=" * 80)
    set_seed(SEED)

    # ---- 1. Verificacao dos checkpoints base ---------------------------------
    print("\n[1/9] Verificando integridade dos checkpoints base...")
    if not BASE_PATCH_CKPT.exists():
        raise FileNotFoundError(BASE_PATCH_CKPT)
    if not ROOT_CANDIDATE_CKPT.exists():
        raise FileNotFoundError(ROOT_CANDIDATE_CKPT)
    sha_patch = sha256_file(BASE_PATCH_CKPT)
    sha_root = sha256_file(ROOT_CANDIDATE_CKPT)
    assert sha_patch == EXPECTED_PATCH_SHA256, f"hash divergente: {sha_patch}"
    assert sha_root == EXPECTED_ROOT_SHA256, f"hash divergente: {sha_root}"
    print(f"  selected_patch_checkpoint.pt : {sha_patch}")
    print(f"  selected_candidate.pt        : {sha_root}")

    # ---- 2. Construcao de splits e sampler -----------------------------------
    print("\n[2/9] Construindo splits e sampler por episodio...")
    sup_mask = load_supervised_spot_mask()
    train_ds = CanonicalV2PositioningDataset(split="train", preload_demos=False)
    val_ds = CanonicalV2PositioningDataset(split="validation", preload_demos=False)
    if MAX_VAL:
        val_ds = CanonicalV2PositioningDataset(
            split="validation", preload_demos=False,
            max_samples=int(MAX_VAL), seed=SEED,
        )
    n_train = len(train_ds)
    n_val = len(val_ds)
    print(f"  train index  : {n_train}")
    print(f"  validation   : {n_val}")
    if not MAX_VAL:
        assert n_val == EXPECTED_VAL_SIZE, f"validation {n_val} != {EXPECTED_VAL_SIZE}"

    train_df = build_train_frames()
    if not MAX_TRAIN:
        assert len(train_df) == n_train, f"train_df {len(train_df)} != {n_train}"
    else:
        train_df = train_df.iloc[: int(MAX_TRAIN)].copy()
        train_df["global_index"] = np.arange(len(train_df), dtype=np.int64)


    rng_a = np.random.RandomState(SEED)
    idx_a, meta_a = episode_sampler(train_df, "natural", rng_a)
    rng_b = np.random.RandomState(SEED + 1)
    idx_b, meta_b = episode_sampler(train_df, "1_to_3", rng_b)
    idx_c = idx_b.copy()
    meta_c = dict(meta_b)
    meta_c["sampler"] = "1_to_3"
    print(f"  Exp A: {meta_a['samples_total']} amostras | ratio={meta_a['effective_sampling_ratio']}")
    print(f"  Exp B: {meta_b['samples_total']} amostras | ratio={meta_b['effective_sampling_ratio']}")
    print(f"  Exp C: {meta_c['samples_total']} amostras | ratio={meta_c['effective_sampling_ratio']}")

    # ---- 3. Pesos de classe (Train-only, clampados) --------------------------
    print("\n[3/9] Calculando pesos de classe clampados (Train-only)...")
    def counts_for(column: str, mapping: List[str]) -> np.ndarray:
        vc = train_df[column].value_counts()
        return np.array([int(vc.get(name, 0)) for name in mapping], dtype=np.float64)

    raw_counts = {
        "state": counts_for("positioning_state", STATE_NAMES),
        "transition_occurs": np.array([
            int((train_df["sector_transition_occurs"] == "NO_TRANSITION").sum()),
            int((train_df["sector_transition_occurs"] == "TRANSITION_OCCURS").sum()),
        ], dtype=np.float64),
        "next_sector": counts_for("next_sector", NEXT_SECTOR_NAMES),
        "transition": counts_for("transition", TRANSITION_NAMES),
        "exit_trigger": counts_for("exit_trigger", EXIT_TRIGGER_NAMES),
    }

    class_weights: Dict[str, torch.Tensor] = {}
    clamped_report: Dict[str, List[float]] = {}
    raw_report: Dict[str, List[float]] = {}
    for k, v in raw_counts.items():
        w, raw_norm = clamped_class_weights(v)
        class_weights[k] = torch.tensor(w, dtype=torch.float32)
        clamped_report[k] = [round(float(x), 6) for x in w]
        raw_report[k] = [round(float(x), 6) for x in raw_norm]
        print(f"  {k:20s} apoio={v.astype(int).tolist()} pesos={clamped_report[k]}")

    # ---- 4. Baseline: hashes antes ------------------------------------------
    print("\n[4/9] Registrando hashes antes do treino...")
    base_model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask)
    ckpt = torch.load(BASE_PATCH_CKPT, map_location="cpu")
    base_state = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
    base_model.load_state_dict(base_state)
    base_model.eval()
    hashes_before = module_hashes(base_model)
    for k in FROZEN_HASH_KEYS:
        print(f"  {k:20s}: {hashes_before[k][:16]}...")

    # ---- 5. Experimentos -----------------------------------------------------
    experiments_plan = [
        ("experiment_a", "Exp A (CE balanceada)", 0.0, False, 0.0, idx_a, meta_a),
        ("experiment_b", "Exp B (focal gamma=1.0)", 1.0, False, 0.0, idx_b, meta_b),
        ("experiment_c", "Exp C (focal + consistencia)", 1.0, True, 0.2, idx_c, meta_c),
    ]
    if EXPERIMENT_FILTER:
        wanted = {x.strip() for x in EXPERIMENT_FILTER.split(",") if x.strip()}
        experiments_plan = [p for p in experiments_plan if p[0] in wanted]

    results: Dict[str, Any] = {}
    best = {"key": None, "score": -1.0, "metrics": None, "model": None}
    comparison_experiments: Dict[str, Any] = {}

    for exp_key, exp_label, gamma, use_cons, lam, idx, meta in experiments_plan:
        print(f"\n[5/9] === {exp_label} ===")
        model, train_info = train_experiment(
            base_state=base_state,
            train_ds=train_ds,
            indices=idx,
            class_weights=class_weights,
            gamma=gamma,
            use_consistency=use_cons,
            consistency_lambda=lam,
            epochs=EPOCHS,
            lr_layer2=1e-5,
            lr_heads=1e-4,
            label=exp_key,
        )

        print(f"  Avaliando {exp_key} na Validation integral...")
        metrics = evaluate_full_validation(model, val_ds, label=exp_key)
        score = temporal_score(metrics)
        metrics["temporal_score"] = score

        results[exp_key] = {
            "schema": "csbot.joint_temporal_patch.experiment_metrics.v1",
            "experiment": exp_label,
            "config": {
                "gamma": gamma,
                "consistency_loss": use_cons,
                "consistency_lambda": lam,
                "epochs": 3,
                "lr_transformer_layer_2": 1e-5,
                "lr_heads": 1e-4,
                "batch_size": 128,
                "seed": SEED,
            },
            "sampling": meta,
            "train": train_info,
            **metrics,
        }

        comparison_experiments[exp_key] = {
            "name": exp_label,
            "effective_sampling_ratio": meta["effective_sampling_ratio"],
            "final_loss": train_info["final_loss"],
            "temporal_score": score,
            "positioning_state_macro_f1": metrics["positioning_state"]["macro_f1"],
            "sector_transition_macro_f1": metrics["sector_transition_occurs"]["macro_f1"],
            "next_sector_macro_f1": metrics["next_sector"]["macro_f1"],
            "transition_macro_f1": metrics["transition"]["macro_f1"],
            "exit_trigger_macro_f1": metrics["exit_trigger"]["macro_f1"],
            "spot_ranking": metrics["spot_ranking"],
        }

        if score > best["score"]:
            best = {"key": exp_key, "score": score, "metrics": metrics, "model": model}

    # ---- 6. Selecao ----------------------------------------------------------
    print(f"\n[6/9] Selecionando experimento por TemporalScore...")
    for k, v in comparison_experiments.items():
        print(f"  {k:14s} TemporalScore={v['temporal_score']:.4f}")
    print(f"  -> selecionado: {best['key']} (score={best['score']:.4f})")

    # ---- 7. Preservacao bitwise ---------------------------------------------
    print("\n[7/9] Verificando preservacao bitwise...")
    hashes_after = module_hashes(best["model"])
    early_ok = all(
        hashes_before[k] == hashes_after[k]
        for k in ("player_proj", "teammate_proj", "teammate_pool", "context_fusion",
                  "pos_encoder", "transformer_layer_0", "transformer_layer_1")
    )
    spot_ok = hashes_before["head_spot"] == hashes_after["head_spot"]
    layer2_changed = hashes_before["transformer_layer_2"] != hashes_after["transformer_layer_2"]

    selected_train = results[best["key"]]["train"]
    preservation = {
        "schema": "csbot.joint_temporal_patch.preservation_check.v1",
        "spot_ranking_head_bitwise_identical": bool(spot_ok),
        "early_blocks_bitwise_identical": bool(early_ok),
        "last_block_received_gradient": bool(selected_train["last_block_received_gradient"]),
        "last_block_weights_changed": bool(layer2_changed),
        "hashes_before": {k: hashes_before[k] for k in FROZEN_HASH_KEYS},
        "hashes_after": {k: hashes_after[k] for k in FROZEN_HASH_KEYS},
        "hashes_after_all_components": hashes_after,
        "selected_experiment": best["key"],
        "spot_metrics_final": best["metrics"]["spot_ranking"],
        "spot_metrics_baseline_reference": {
            "mrr": 0.7776, "top1": 0.6349, "top5": 0.9639, "invalid_masked": 0,
            "source": "Marco 2B.3.3 / full validation integral",
        },
        "preservation_gates": {
            "spot_mrr_ge_0_76": best["metrics"]["spot_ranking"]["mrr"] >= 0.76,
            "spot_top5_ge_0_955": best["metrics"]["spot_ranking"]["top5"] >= 0.955,
            "invalid_masked_eq_0": best["metrics"]["spot_ranking"]["invalid_masked"] == 0,
            "spot_head_bitwise_identical": bool(spot_ok),
            "early_blocks_bitwise_identical": bool(early_ok),
        },
    }
    for k in ("player_proj", "teammate_proj", "teammate_pool", "transformer_layer_0",
              "transformer_layer_1", "head_spot"):
        if hashes_before[k] != hashes_after[k]:
            print(f"  ERRO: componente congelado alterado -> {k}")
    with open(OUT_DIR / "preservation_check.json", "w", encoding="utf-8") as f:
        json.dump(preservation, f, indent=2)
    print("  preservation_check.json salvo.")

    # ---- 8. Checkpoint selecionado + thresholds ------------------------------
    print("\n[8/9] Salvando checkpoint selecionado e thresholds...")
    sel_metrics = best["metrics"]
    sel_threshold = select_threshold(sel_metrics["sector_transition_threshold_sweep"])

    torch.save({
        "schema": "csbot.checkpoint.positioning_v2.joint_temporal_patch_v1",
        "phase": "3A.3-B",
        "milestone": "2B.3.4",
        "model_state_dict": best["model"].state_dict(),
        "selected_experiment": best["key"],
        "selected_threshold_transition_occurs": sel_threshold["threshold"],
        "temporal_score": best["score"],
        "seed": SEED,
        "base_checkpoint_sha256": sha_patch,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, OUT_DIR / "selected_checkpoint.pt")
    print("  selected_checkpoint.pt salvo.")

    with open(OUT_DIR / "selected_thresholds.json", "w", encoding="utf-8") as f:
        json.dump({
            "schema": "csbot.joint_temporal_patch.selected_thresholds.v1",
            "selected_experiment": best["key"],
            "threshold_grid": THRESHOLD_GRID,
            "sector_transition_occurs": sel_threshold,
            "multi_class_heads": {
                "policy": "argmax",
                "heads": ["positioning_state", "next_sector", "transition", "exit_trigger"],
            },
            "selection_rule": "max Macro-F1 sujeito a TRANSITION_OCCURS_recall>=0.35 e NO_TRANSITION_recall>=0.78",
        }, f, indent=2)
    print("  selected_thresholds.json salvo.")

    # ---- 9. Metricas finais e comparacao -----------------------------------
    print("\n[9/9] Consolidando metricas finais...")
    final_metrics = {
        "schema": "csbot.joint_temporal_patch.full_validation_metrics.v1",
        "validation_total_indexed": n_val,
        "validation_total_evaluated": sel_metrics["validation_total_evaluated"],
        "evaluated_scope": "full_validation_integral",
        "selected_experiment": best["key"],
        "selected_threshold_transition_occurs": sel_threshold["threshold"],
        "temporal_score": best["score"],
        "positioning_state": sel_metrics["positioning_state"],
        "sector_transition_occurs": sel_metrics["sector_transition_occurs"],
        "sector_transition_occurs_at_selected_threshold": sel_threshold,
        "next_sector": sel_metrics["next_sector"],
        "transition": sel_metrics["transition"],
        "exit_trigger": sel_metrics["exit_trigger"],
        "spot_ranking": sel_metrics["spot_ranking"],
        "class_support_note": "classes com support=0 sao reportadas como N/A (nunca 0.0)",
    }
    with open(OUT_DIR / "full_validation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=2)
    print("  full_validation_metrics.json salvo.")

    for k, v in results.items():
        with open(OUT_DIR / f"{k}_metrics.json", "w", encoding="utf-8") as f:
            json.dump(v, f, indent=2)

    comparison = {
        "schema": "csbot.joint_temporal_patch.experiment_comparison.v1",
        "selected_experiment": best["key"],
        "temporal_score_formula": SCORE_WEIGHTS,
        "spot_ranking_excluded_from_selection": True,
        "experiments": comparison_experiments,
        "sampling": {
            "adjacent_window_duplication_rate": 0.0,
            "policy": "one_window_per_episode_draw",
            "experiment_a": meta_a,
            "experiment_b": meta_b,
            "experiment_c": meta_c,
        },
        "loss_config": {
            "clamped_weights": clamped_report,
            "raw_normalized_weights_before_clamp": raw_report,
            "clamp_range": [0.1, 10.0],
            "class_counts_train": {k: v.astype(int).tolist() for k, v in raw_counts.items()},
        },
    }
    with open(OUT_DIR / "experiment_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)
    print("  experiment_comparison.json salvo.")

    # ---- Veredito ------------------------------------------------------------
    gates = {}
    st = final_metrics["positioning_state"]
    to = final_metrics["sector_transition_occurs"]
    to_sel = final_metrics["sector_transition_occurs_at_selected_threshold"]
    ns = final_metrics["next_sector"]
    tr = final_metrics["transition"]
    tg = final_metrics["exit_trigger"]
    spot = final_metrics["spot_ranking"]

    def recall_of(block: Dict[str, Any], cls: str) -> Optional[float]:
        e = block["per_class"].get(cls)
        if not e or not isinstance(e.get("recall"), (int, float)):
            return None
        return float(e["recall"])

    gates["positioning_state_macro_f1_ge_0_40"] = st["macro_f1"] >= 0.40
    gates["positioning_state_balanced_acc_ge_0_45"] = st["balanced_accuracy"] >= 0.45
    for cls, floor in (("HOLD", 0.35), ("OBJECTIVE", 0.30), ("STAGING", 0.25),
                       ("RETAKE", 0.25), ("SAVE", 0.20)):
        r = recall_of(st, cls)
        gates[f"state_{cls.lower()}_recall_ge_{floor}"] = (r is None) or (r >= floor)
    gates["transition_occurs_macro_f1_ge_0_55"] = to_sel["macro_f1"] >= 0.55
    gates["transition_occurs_recall_ge_0_35"] = to_sel["TRANSITION_OCCURS_recall"] >= 0.35
    gates["no_transition_recall_ge_0_78"] = to_sel["NO_TRANSITION_recall"] >= 0.78
    gates["next_sector_macro_f1_ge_0_45"] = ns["macro_f1"] >= 0.45
    gates["transition_macro_f1_ge_0_60"] = tr["macro_f1"] >= 0.60
    gates["exit_trigger_macro_f1_ge_0_40"] = tg["macro_f1"] >= 0.40
    gates["spot_mrr_ge_0_76"] = spot["mrr"] >= 0.76
    gates["spot_top5_ge_0_955"] = spot["top5"] >= 0.955
    gates["invalid_masked_eq_0"] = spot["invalid_masked"] == 0
    gates["spot_head_bitwise_identical"] = bool(spot_ok)
    gates["early_blocks_bitwise_identical"] = bool(early_ok)

    all_pass = all(gates.values())
    verdict = "JOINT_TEMPORAL_PATCH_ACCEPTED" if all_pass else "JOINT_TEMPORAL_PATCH_PARTIAL"

    with open(OUT_DIR / "gate_verdict.json", "w", encoding="utf-8") as f:
        json.dump({
            "schema": "csbot.joint_temporal_patch.gate_verdict.v1",
            "verdict": verdict,
            "gates": gates,
            "failed_gates": [k for k, v in gates.items() if not v],
            "selected_experiment": best["key"],
            "temporal_score": best["score"],
            "validation_scope": "full_validation_integral_501434",
        }, f, indent=2)

    print("\n" + "=" * 80)
    print(f"MARCO 2B.3.4 CONCLUIDO: {verdict}")
    print(f"  TemporalScore: {best['score']:.4f} | experimento: {best['key']}")
    print(f"  Gates reprovados: {[k for k, v in gates.items() if not v] or 'nenhum'}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
