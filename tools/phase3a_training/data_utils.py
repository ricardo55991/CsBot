#!/usr/bin/env python3
"""
Módulo de Utilidades de Dados e Métricas para Treinamento do Positioning Transformer V1.
Fornece:
1. Vetorização e Carregamento Rápido em Memória.
2. Mapeamento formal de categorias e catalog IDs.
3. Cálculo completo e rigoroso de métricas multitarefa (Macro F1, MRR, Top-k, Balanced Acc) em NumPy puro.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
from torch.utils.data import Dataset, DataLoader

from tools.phase3a_training.canonical_temporal_dataloader import (
    NPZCacheManager,
    CanonicalTemporalPositioningDataset,
    create_canonical_temporal_dataloader,
    canonical_collate_fn,
    load_canonical_temporal_splits,
    DEFAULT_NPZ_DIR,
    FALLBACK_NPZ_DIR
)

_DEFAULT_NPZ_CACHE: Optional[NPZCacheManager] = None

def get_default_npz_cache(npz_dir: Optional[Path] = None) -> NPZCacheManager:
    global _DEFAULT_NPZ_CACHE
    if _DEFAULT_NPZ_CACHE is None or (npz_dir is not None and _DEFAULT_NPZ_CACHE.npz_dir != Path(npz_dir)):
        _DEFAULT_NPZ_CACHE = NPZCacheManager(npz_dir=npz_dir)
    return _DEFAULT_NPZ_CACHE


STATE_NAMES = ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE", "SAVE"]
STATE_MAP = {name: i for i, name in enumerate(STATE_NAMES)}

SECTOR_NAMES = ["A", "B", "MID", "CT", "T", "DYNAMIC"]
SECTOR_MAP = {name: i for i, name in enumerate(SECTOR_NAMES)}

TRANSITION_NAMES = ["ADVANCE", "HOLD", "FALLBACK", "ROTATE", "CONVERGE", "COVER", "LURK"]
TRANSITION_MAP = {name: i for i, name in enumerate(TRANSITION_NAMES)}

EXIT_TRIGGER_NAMES = ["TIME", "CONTACT", "FIRST_KILL", "TEAMMATE_DEATH", "BOMB_SPOTTED", "BOMB_PLANTED", "UTILITY_EXPIRED", "TACTIC_REVISION"]
EXIT_TRIGGER_MAP = {name: i for i, name in enumerate(EXIT_TRIGGER_NAMES)}

TEAM_MAP = {"CT": 0, "TR": 1, "ANY": 2}
ROLE_NAMES = ["SUPPORT", "BOMB_CARRIER", "SECOND_ENTRY", "ANCHOR", "RETAKE_ENTRY", "ENTRY", "LURKER", "AWPER", "ROTATOR", "RETAKE_COVER"]
ROLE_MAP = {name: i for i, name in enumerate(ROLE_NAMES)}
STAGE_NAMES = ["MapControl", "Staging", "Contact", "Setup", "PostPlant", "Retake"]
STAGE_MAP = {name: i for i, name in enumerate(STAGE_NAMES)}

def determine_state(cat_id: str, sem_type: str, p_stage: str, role: str, team: str, explicit_state: Optional[str] = None) -> str:
    if explicit_state and explicit_state in STATE_NAMES:
        return explicit_state
    if sem_type == "PLANT_POSITION" or p_stage == "Planting":
        return "OBJECTIVE"
    if cat_id == "UNMAPPED_POSITION":
        return "TRANSIT"
    if sem_type == "CLEARANCE_WAYPOINT":
        return "CLEARANCE"
    if sem_type == "STAGING_POSITION":
        return "STAGING"
    if role in ["RETAKE_ENTRY", "RETAKE_COVER"] or p_stage == "Retake":
        return "RETAKE"
    if p_stage == "PostPlant" and team == "CT":
        return "SAVE"
    return "HOLD"

def determine_sector(sec: str) -> str:
    s = str(sec).upper()
    if "A" in s and "B" not in s:
        return "A"
    if "B" in s and "A" not in s:
        return "B"
    if "MID" in s:
        return "MID"
    if "CT" in s:
        return "CT"
    if "TR" in s or "T" in s:
        return "T"
    return "DYNAMIC"

def determine_transition(state: str, role: str) -> str:
    if state == "TRANSIT":
        if role in ["ENTRY", "RETAKE_ENTRY"]:
            return "ADVANCE"
        if role in ["ROTATOR", "SUPPORT"]:
            return "ROTATE"
        if role == "LURKER":
            return "LURK"
        return "CONVERGE"
    if state in ["HOLD", "OBJECTIVE"]:
        return "HOLD"
    if state == "SAVE":
        return "FALLBACK"
    if state == "CLEARANCE":
        return "COVER"
    return "ADVANCE"

def determine_exit_trigger(state: str, p_stage: str) -> str:
    if p_stage == "PostPlant":
        return "BOMB_PLANTED"
    if state == "CLEARANCE":
        return "CONTACT"
    if state == "HOLD":
        return "FIRST_KILL"
    if state == "SAVE":
        return "TEAMMATE_DEATH"
    if state == "STAGING":
        return "UTILITY_EXPIRED"
    return "TIME"

# Funções de Métricas em NumPy puro
def np_accuracy_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) == 0:
        return 0.0
    return float(np.mean(y_true == y_pred))

def np_per_class_prf(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    precisions = np.zeros(num_classes, dtype=np.float32)
    recalls = np.zeros(num_classes, dtype=np.float32)
    f1s = np.zeros(num_classes, dtype=np.float32)
    supports = np.zeros(num_classes, dtype=np.int64)

    for c in range(num_classes):
        tp = int(np.sum((y_pred == c) & (y_true == c)))
        fp = int(np.sum((y_pred == c) & (y_true != c)))
        fn = int(np.sum((y_pred != c) & (y_true == c)))
        sup = int(np.sum(y_true == c))
        supports[c] = sup

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = (2.0 * p * r) / (p + r) if (p + r) > 0 else 0.0

        precisions[c] = p
        recalls[c] = r
        f1s[c] = f

    return precisions, recalls, f1s, supports

def np_macro_f1(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> float:
    _, _, f1s, _ = np_per_class_prf(y_true, y_pred, num_classes)
    return float(np.mean(f1s))

def np_balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> float:
    _, recalls, _, supports = np_per_class_prf(y_true, y_pred, num_classes)
    # média apenas sobre classes com suporte > 0
    valid_mask = supports > 0
    if np.sum(valid_mask) == 0:
        return 0.0
    return float(np.mean(recalls[valid_mask]))

class InMemoryPositioningDataset(Dataset):
    """
    Dataset vetorizado de alto desempenho mantido em memória RAM.
    Elimina sobrecargas de I/O por batch e preserva histórico temporal autêntico.
    """
    def __init__(
        self,
        history: torch.Tensor,
        teammates: torch.Tensor,
        candidate_mask: torch.Tensor,
        team_idx: torch.Tensor,
        role_idx: torch.Tensor,
        stage_idx: torch.Tensor,
        targets: Dict[str, torch.Tensor],
        metadata: Optional[List[Dict[str, Any]]] = None,
        temporal_mask: Optional[torch.Tensor] = None
    ):
        self.history = history
        self.teammates = teammates
        self.candidate_mask = candidate_mask
        self.team_idx = team_idx
        self.role_idx = role_idx
        self.stage_idx = stage_idx
        self.targets = targets
        self.metadata = metadata or []
        if temporal_mask is None:
            self.temporal_mask = torch.ones((history.size(0), history.size(1)), dtype=torch.float32)
        else:
            self.temporal_mask = temporal_mask

    def __len__(self) -> int:
        return self.history.size(0)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = {
            "history": self.history[idx],
            "teammates": self.teammates[idx],
            "temporal_mask": self.temporal_mask[idx],
            "candidate_mask": self.candidate_mask[idx],
            "team_idx": self.team_idx[idx],
            "role_idx": self.role_idx[idx],
            "stage_idx": self.stage_idx[idx],
            "positioning_state": self.targets["positioning_state"][idx],
            "next_sector": self.targets["next_sector"][idx],
            "candidate_spot_idx": self.targets["candidate_spot_idx"][idx],
            "spot_loss_mask": self.targets["spot_loss_mask"][idx],
            "transition": self.targets["transition"][idx],
            "exit_trigger": self.targets["exit_trigger"][idx],
        }
        if self.metadata and idx < len(self.metadata):
            item["metadata"] = self.metadata[idx]
        return item

def load_catalog(ds_dir: Path) -> Tuple[List[str], Dict[str, int]]:
    catalog_path = ds_dir / "contracts" / "mirage_spot_catalog_v3.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    spot_ids = [s["id"] for s in data["spots"]]
    spot_to_idx = {s_id: i for i, s_id in enumerate(spot_ids)}
    return spot_ids, spot_to_idx

def load_and_preprocess_shard(
    parquet_path: Path,
    spot_to_idx: Dict[str, int],
    split_filter: Optional[str] = None,
    max_samples: Optional[int] = None,
    cache_manager: Optional[NPZCacheManager] = None,
    npz_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Lê um arquivo parquet e converte colunas para tensores NumPy/PyTorch
    extraindo janelas temporais canônicas autênticas [32, 18] e aliados reais [32, 4, 18]
    diretamente dos tensores NPZ correspondentes.
    """
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    
    if split_filter:
        split_val = "validation" if split_filter in ["val", "validation"] else split_filter
        if "split" in df.columns:
            df = df[df["split"] == split_val].reset_index(drop=True)
        # Consultar canonical_temporal_splits_v1.json formal
        ds_dir = parquet_path.parent
        for _ in range(4):
            if (ds_dir / "canonical_temporal_splits_v1.json").exists():
                break
            ds_dir = ds_dir.parent
        splits_data = load_canonical_temporal_splits(ds_dir)
        demo_key = f"{split_val}_demos"
        if splits_data and demo_key in splits_data:
            allowed_demos = set(splits_data[demo_key])
            df = df[df["demo_id"].isin(allowed_demos)].reset_index(drop=True)
        
    if max_samples and len(df) > max_samples:
        df = df.iloc[:max_samples].reset_index(drop=True)
        
    n = len(df)
    if n == 0:
        return {}

    # Extração temporal canônica e determinística dos tensores NPZ
    cache = cache_manager or get_default_npz_cache(npz_dir)
    history_arr = np.zeros((n, 32, 18), dtype=np.float32)
    teammates_arr = np.zeros((n, 32, 4, 18), dtype=np.float32)
    temporal_mask_arr = np.zeros((n, 32), dtype=np.float32)

    demos = df["demo_id"].tolist()
    rounds = df["round_index"].tolist()
    slots = df["slot"].tolist()
    seq_ids = df["sequence_id"].tolist()

    for i in range(n):
        s_id = str(seq_ids[i])
        f_idx = int(s_id.split("_f")[-1])
        h, tm, m = cache.extract_window(
            demo_id=demos[i],
            round_idx=int(rounds[i]),
            slot=int(slots[i]),
            f_idx=f_idx
        )
        history_arr[i] = h
        teammates_arr[i] = tm
        temporal_mask_arr[i] = m

    # Categorias de entrada
    team_vals = [TEAM_MAP.get(t, 2) for t in df["team"]]
    role_vals = [ROLE_MAP.get(r, 0) for r in df["role"]]
    stage_vals = [STAGE_MAP.get(s, 0) for s in df["plan_stage"]]

    # Targets e Labels
    state_vals = []
    sector_vals = []
    spot_vals = []
    spot_mask_vals = []
    trans_vals = []
    trig_vals = []
    
    # Candidate mask: [N, 53]
    candidate_mask_arr = np.ones((n, 53), dtype=bool)

    cat_ids = df["assigned_catalog_id"].tolist()
    sem_types = df["semantic_type"].tolist()
    p_stages = df["plan_stage"].tolist()
    roles = df["role"].tolist()
    teams = df["team"].tolist()
    next_secs = df["next_sector"].tolist()

    has_explicit_state = "positioning_state" in df.columns
    explicit_states = df["positioning_state"].tolist() if has_explicit_state else [None] * n

    for i in range(n):
        c_id = str(cat_ids[i])
        s_type = str(sem_types[i])
        stg = str(p_stages[i])
        rl = str(roles[i])
        tm = str(teams[i])
        nxt_s = str(next_secs[i])
        exp_st = str(explicit_states[i]) if has_explicit_state and explicit_states[i] is not None else None

        st_name = determine_state(c_id, s_type, stg, rl, tm, explicit_state=exp_st)
        state_vals.append(STATE_MAP[st_name])

        sec_name = determine_sector(nxt_s)
        sector_vals.append(SECTOR_MAP[sec_name])

        is_valid_spot = (c_id != "UNMAPPED_POSITION") and (c_id in spot_to_idx)
        sp_idx = spot_to_idx.get(c_id, 0)
        spot_vals.append(sp_idx)

        # Máscara estrita de perda de Spot: ativa se e somente se não for TRANSIT e tiver spot válido
        spot_mask_vals.append(bool(is_valid_spot and st_name != "TRANSIT"))

        tr_name = determine_transition(st_name, rl)
        trans_vals.append(TRANSITION_MAP[tr_name])

        ex_name = determine_exit_trigger(st_name, stg)
        trig_vals.append(EXIT_TRIGGER_MAP[ex_name])

    return {
        "history": torch.from_numpy(history_arr),
        "teammates": torch.from_numpy(teammates_arr),
        "temporal_mask": torch.from_numpy(temporal_mask_arr),
        "candidate_mask": torch.from_numpy(candidate_mask_arr),
        "team_idx": torch.tensor(team_vals, dtype=torch.long),
        "role_idx": torch.tensor(role_vals, dtype=torch.long),
        "stage_idx": torch.tensor(stage_vals, dtype=torch.long),
        "targets": {
            "positioning_state": torch.tensor(state_vals, dtype=torch.long),
            "next_sector": torch.tensor(sector_vals, dtype=torch.long),
            "candidate_spot_idx": torch.tensor(spot_vals, dtype=torch.long),
            "spot_loss_mask": torch.tensor(spot_mask_vals, dtype=torch.bool),
            "transition": torch.tensor(trans_vals, dtype=torch.long),
            "exit_trigger": torch.tensor(trig_vals, dtype=torch.long),
        },
        "metadata": df[["sequence_id", "demo_id", "round_index", "slot", "team", "role", "plan_stage", "assigned_catalog_id", "next_sector"]].to_dict(orient="records")
    }

def create_dataset_from_shards(
    ds_dir: Path,
    split: str,
    max_samples: Optional[int] = None,
    cache_manager: Optional[NPZCacheManager] = None,
    npz_dir: Optional[Path] = None
) -> InMemoryPositioningDataset:
    spot_ids, spot_to_idx = load_catalog(ds_dir)
    pos_dir = ds_dir / "positioning" / "positioning_sequences_v1"
    shards = sorted(list(pos_dir.glob("shard_*.parquet")))
    
    parts = []
    collected_samples = 0
    
    for shard in shards:
        limit = None
        if max_samples:
            limit = max_samples - collected_samples
            if limit <= 0:
                break
        res = load_and_preprocess_shard(shard, spot_to_idx, split_filter=split, max_samples=limit, cache_manager=cache_manager, npz_dir=npz_dir)
        if res and res["history"].size(0) > 0:
            parts.append(res)
            collected_samples += res["history"].size(0)

    if not parts:
        raise ValueError(f"Nenhum dado encontrado para o split '{split}' em {pos_dir}")

    # Concatenar tensores
    all_history = torch.cat([p["history"] for p in parts], dim=0)
    all_teammates = torch.cat([p["teammates"] for p in parts], dim=0)
    all_temporal_mask = torch.cat([p["temporal_mask"] for p in parts], dim=0)
    all_candidate_mask = torch.cat([p["candidate_mask"] for p in parts], dim=0)
    all_team_idx = torch.cat([p["team_idx"] for p in parts], dim=0)
    all_role_idx = torch.cat([p["role_idx"] for p in parts], dim=0)
    all_stage_idx = torch.cat([p["stage_idx"] for p in parts], dim=0)

    all_targets = {
        "positioning_state": torch.cat([p["targets"]["positioning_state"] for p in parts], dim=0),
        "next_sector": torch.cat([p["targets"]["next_sector"] for p in parts], dim=0),
        "candidate_spot_idx": torch.cat([p["targets"]["candidate_spot_idx"] for p in parts], dim=0),
        "spot_loss_mask": torch.cat([p["targets"]["spot_loss_mask"] for p in parts], dim=0),
        "transition": torch.cat([p["targets"]["transition"] for p in parts], dim=0),
        "exit_trigger": torch.cat([p["targets"]["exit_trigger"] for p in parts], dim=0),
    }
    
    all_meta = []
    for p in parts:
        all_meta.extend(p["metadata"])

    return InMemoryPositioningDataset(
        history=all_history,
        teammates=all_teammates,
        candidate_mask=all_candidate_mask,
        team_idx=all_team_idx,
        role_idx=all_role_idx,
        stage_idx=all_stage_idx,
        targets=all_targets,
        metadata=all_meta,
        temporal_mask=all_temporal_mask
    )

def compute_multitask_metrics(all_preds: Dict[str, np.ndarray], all_targets: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Calcula métricas detalhadas de todas as 5 Heads com foco nas classes raras e ranking de spots.
    """
    # 1. Head A: PositioningState
    y_true_state = all_targets["positioning_state"]
    y_pred_state = np.argmax(all_preds["logits_state"], axis=1)

    state_acc = np_accuracy_score(y_true_state, y_pred_state)
    state_macro_f1 = np_macro_f1(y_true_state, y_pred_state, num_classes=7)
    state_balanced_acc = np_balanced_accuracy(y_true_state, y_pred_state, num_classes=7)

    # Per-class metrics para State
    p_c, r_c, f_c, s_c = np_per_class_prf(y_true_state, y_pred_state, num_classes=7)
    per_class_state = {}
    for i, name in enumerate(STATE_NAMES):
        per_class_state[name] = {
            "precision": float(p_c[i]),
            "recall": float(r_c[i]),
            "f1": float(f_c[i]),
            "support": int(s_c[i])
        }

    # 2. Head B: NextSector
    y_true_sec = all_targets["next_sector"]
    y_pred_sec = np.argmax(all_preds["logits_sector"], axis=1)
    sector_acc = np_accuracy_score(y_true_sec, y_pred_sec)
    sector_macro_f1 = np_macro_f1(y_true_sec, y_pred_sec, num_classes=6)

    # 3. Head C: CandidateSpotRanking (avaliado somente onde spot_loss_mask == True)
    spot_mask = all_targets["spot_loss_mask"].astype(bool)
    n_eligible_spots = int(np.sum(spot_mask))
    
    if n_eligible_spots > 0:
        spot_logits_sub = all_preds["logits_spot"][spot_mask]
        spot_true_sub = all_targets["candidate_spot_idx"][spot_mask]

        # Ranking ordenado decrescente de logits
        ranked_indices = np.argsort(-spot_logits_sub, axis=1) # [N, 53]

        top1_hits = 0
        top3_hits = 0
        top5_hits = 0
        mrr_sum = 0.0
        ndcg_sum = 0.0

        for idx in range(n_eligible_spots):
            true_spot = spot_true_sub[idx]
            rank_list = ranked_indices[idx]
            rank_pos = np.where(rank_list == true_spot)[0]
            if len(rank_pos) > 0:
                pos = rank_pos[0] + 1 # 1-based rank
                mrr_sum += 1.0 / pos
                if pos == 1:
                    top1_hits += 1
                if pos <= 3:
                    top3_hits += 1
                if pos <= 5:
                    top5_hits += 1
                    ndcg_sum += 1.0 / np.log2(pos + 1)

        spot_mrr = float(mrr_sum / n_eligible_spots)
        spot_top1 = float(top1_hits / n_eligible_spots)
        spot_top3 = float(top3_hits / n_eligible_spots)
        spot_top5 = float(top5_hits / n_eligible_spots)
        spot_ndcg5 = float(ndcg_sum / n_eligible_spots)
    else:
        spot_mrr = 0.0
        spot_top1 = 0.0
        spot_top3 = 0.0
        spot_top5 = 0.0
        spot_ndcg5 = 0.0

    # 4. Head D: Transition
    y_true_trans = all_targets["transition"]
    y_pred_trans = np.argmax(all_preds["logits_transition"], axis=1)
    trans_acc = np_accuracy_score(y_true_trans, y_pred_trans)
    trans_macro_f1 = np_macro_f1(y_true_trans, y_pred_trans, num_classes=7)

    # 5. Head E: ExitTrigger
    y_true_trig = all_targets["exit_trigger"]
    y_pred_trig = np.argmax(all_preds["logits_trigger"], axis=1)
    trig_acc = np_accuracy_score(y_true_trig, y_pred_trig)
    trig_macro_f1 = np_macro_f1(y_true_trig, y_pred_trig, num_classes=8)

    # Métrica Composta balanceada para seleção de checkpoint
    composite_score = (
        0.35 * state_macro_f1 +
        0.35 * spot_mrr +
        0.15 * sector_macro_f1 +
        0.15 * trans_macro_f1
    )

    return {
        "state_accuracy": state_acc,
        "state_macro_f1": state_macro_f1,
        "state_balanced_accuracy": state_balanced_acc,
        "per_class_state": per_class_state,
        "sector_accuracy": sector_acc,
        "sector_macro_f1": sector_macro_f1,
        "eligible_spot_count": n_eligible_spots,
        "spot_mrr": spot_mrr,
        "spot_top1_accuracy": spot_top1,
        "spot_top3_accuracy": spot_top3,
        "spot_top5_accuracy": spot_top5,
        "spot_ndcg5": spot_ndcg5,
        "transition_accuracy": trans_acc,
        "transition_macro_f1": trans_macro_f1,
        "trigger_accuracy": trig_acc,
        "trigger_macro_f1": trig_macro_f1,
        "composite_score": float(composite_score)
    }
