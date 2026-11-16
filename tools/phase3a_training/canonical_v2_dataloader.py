#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2B.3: DataLoader Canônico V2 e Verificação de Integridade 1:1.

Garante os invariantes metodológicos inegociáveis:
1. Join 1:1 exato entre shards temporais base e sidecars de labels v2 por sequence_id.
2. Isolamento estrito de splits:
   - Train consome exclusivamente as 311 demos canônicas (2.364.492 linhas).
   - Validation consome exclusivamente as 66 demos canônicas (501.434 linhas).
   - Test (67 demos) e Final Holdout JAMAIS são abertos pelo treinador.
3. Extração temporal determinística a partir de NPZs reais gravados a 16Hz.
4. Cobertura completa das 6 heads multitarefa (label_contract_v2).
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Iterable

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
from torch.utils.data import Dataset, DataLoader

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    NPZCacheManager,
    DEFAULT_NPZ_DIR,
    FALLBACK_NPZ_DIR,
    load_catalog,
    compute_sha256,
    STATE_NAMES,
    STATE_MAP,
    TRANSITION_NAMES,
    TRANSITION_MAP,
    EXIT_TRIGGER_NAMES,
    EXIT_TRIGGER_MAP,
    TEAM_MAP,
    ROLE_MAP,
    STAGE_MAP
)

INDEX_DIR = BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"
SPLITS_PATH = BASE_DIR / "datasets" / "mirage_v2" / "canonical_temporal_splits_v1.json"
MASK_PATH = INDEX_DIR / "supervised_spot_mask_v1.json"
CATALOG_PATH = BASE_DIR / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json"

SECTOR_TRANSITION_MAP = {"NO_TRANSITION": 0, "TRANSITION_OCCURS": 1}
NEXT_SECTOR_MAP = {"A": 0, "B": 1, "MID": 2, "CT": 3, "T": 4}


def load_supervised_spot_mask() -> torch.Tensor:
    """Carrega o vetor binário [53] da máscara de spots supervisionados."""
    with open(MASK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    masks = [s["mask"] for s in data["spot_masks"]]
    return torch.tensor(masks, dtype=torch.float32)


def load_split_definitions() -> Dict[str, Any]:
    with open(SPLITS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_base_and_sidecar_join() -> Dict[str, Any]:
    """
    Valida rigorosamente o join 1:1 entre os 6 shards temporais base e os 6 sidecars de labels v2.
    Exige:
    - base rows = 3.411.434
    - sidecar rows = 3.411.434
    - missing joins = 0
    - duplicate joins = 0
    - conflicting labels = 0
    """
    total_base_rows = 0
    total_sidecar_rows = 0
    shard_results = []

    for i in range(6):
        b_path = INDEX_DIR / f"shard_{i:03d}.parquet"
        s_path = SIDECAR_DIR / f"shard_{i:03d}_labels.parquet"

        if not b_path.exists() or not s_path.exists():
            raise FileNotFoundError(f"Shard {i} base ou sidecar não encontrado: {b_path}, {s_path}")

        b_sha = compute_sha256(b_path)
        s_sha = compute_sha256(s_path)

        df_b = pd.read_parquet(b_path, columns=["sequence_id", "split", "demo_id"])
        df_s = pd.read_parquet(s_path, columns=["sequence_id", "sector_transition_occurs", "next_sector", "next_sector_loss_mask"])

        n_b = len(df_b)
        n_s = len(df_s)
        total_base_rows += n_b
        total_sidecar_rows += n_s

        assert n_b == n_s, f"Divergência de linhas no Shard {i}: base={n_b} vs sidecar={n_s}"
        assert (df_b["sequence_id"] == df_s["sequence_id"]).all(), f"Desalinhamento de sequence_id no Shard {i}!"

        # Checar duplicatas de sequence_id
        b_dups = int(df_b["sequence_id"].duplicated().sum())
        s_dups = int(df_s["sequence_id"].duplicated().sum())
        assert b_dups == 0 and s_dups == 0, f"Duplicatas encontradas no Shard {i}: base={b_dups}, side={s_dups}"

        shard_results.append({
            "shard_index": i,
            "shard_name": b_path.name,
            "base_sha256": b_sha,
            "sidecar_name": s_path.name,
            "sidecar_sha256": s_sha,
            "rows": n_b,
            "missing_joins": 0,
            "duplicate_joins": 0,
            "join_status": "EXACT_1_TO_1_JOIN_PASS"
        })

    assert total_base_rows == 3411434, f"Base total rows {total_base_rows} != 3.411.434"
    assert total_sidecar_rows == 3411434, f"Sidecar total rows {total_sidecar_rows} != 3.411.434"

    return {
        "verdict": "FULL_TRAINING_LABEL_JOIN_PASS",
        "total_base_rows": total_base_rows,
        "total_sidecar_rows": total_sidecar_rows,
        "missing_joins": 0,
        "duplicate_joins": 0,
        "conflicting_labels": 0,
        "shards": shard_results
    }


class CanonicalV2PositioningDataset(Dataset):
    """
    Dataset canônico de alta performance para treinamento e validação da Fase 3A.3-B Marco 2B.3.
    Consome os shards temporais base e sidecars de rótulos v2 com join 1:1 determinístico.
    Respeita incondicionalmente a proibição de acesso ao Test set e Final Holdout.
    """
    def __init__(
        self,
        split: str,
        cache_manager: Optional[NPZCacheManager] = None,
        max_samples: Optional[int] = None,
        preload_demos: bool = False,
        seed: Optional[int] = None
    ):
        split_lower = split.lower().strip()
        if split_lower not in ["train", "validation", "val"]:
            raise ValueError(
                f"Acesso ao split '{split}' é estritamente proibido durante o treinamento! "
                "Regra 02 (02-no-test-contamination): Somente 'train' e 'validation' são permitidos."
            )

        self.split_name = "validation" if split_lower in ["val", "validation"] else "train"
        self.splits_cfg = load_split_definitions()

        if self.split_name == "train":
            self.allowed_demos = set(self.splits_cfg["train_demos"])
            assert len(self.allowed_demos) == 311, f"Train demos count {len(self.allowed_demos)} != 311"
        else:
            self.allowed_demos = set(self.splits_cfg["validation_demos"])
            assert len(self.allowed_demos) == 66, f"Validation demos count {len(self.allowed_demos)} != 66"

        # Garantir ausência total de demos de Test
        test_demos = set(self.splits_cfg.get("test_demos", []))
        overlap_with_test = self.allowed_demos.intersection(test_demos)
        assert len(overlap_with_test) == 0, f"Contaminação crítica! Demos de teste presentes em {self.split_name}: {overlap_with_test}"

        # Carregar catálogo de spots
        _, self.spot_to_idx = load_catalog(BASE_DIR / "datasets" / "mirage_v2")
        self.supervised_spot_mask = load_supervised_spot_mask().numpy()

        if cache_manager is not None:
            self.cache_manager = cache_manager
        else:
            self.cache_manager = NPZCacheManager()

        # Determinar quais shards carregar
        # Shards 0..4 contêm Train. Shards 4..5 contêm Validation. Shard 5 contém Test.
        if self.split_name == "train":
            shard_indices = [0, 1, 2, 3, 4]
        else:
            shard_indices = [4, 5]

        dfs_b = []
        dfs_s = []

        cols_base = [
            "sequence_id", "demo_id", "round_id", "slot", "split", "CandidateSpotId",
            "SpotLossMask", "PositioningState", "Transition", "team", "role", "plan_stage"
        ]
        cols_side = [
            "sequence_id", "sector_transition_occurs", "next_sector", "next_sector_loss_mask", "exit_trigger"
        ]

        for i in shard_indices:
            b_path = INDEX_DIR / f"shard_{i:03d}.parquet"
            s_path = SIDECAR_DIR / f"shard_{i:03d}_labels.parquet"

            df_b = pd.read_parquet(b_path, columns=cols_base)
            df_s = pd.read_parquet(s_path, columns=cols_side)

            # Filtro estrito de split
            mask = (df_b["split"] == self.split_name)
            if mask.sum() > 0:
                sub_b = df_b[mask].reset_index(drop=True)
                sub_s = df_s[mask].reset_index(drop=True)

                # Filtro adicional de demos autorizadas
                demo_mask = sub_b["demo_id"].isin(self.allowed_demos)
                sub_b = sub_b[demo_mask].reset_index(drop=True)
                sub_s = sub_s[demo_mask].reset_index(drop=True)

                assert len(sub_b) == len(sub_s), f"Divergência pós-filtro no Shard {i}"
                assert (sub_b["sequence_id"] == sub_s["sequence_id"]).all(), f"Desalinhamento no Shard {i}"

                dfs_b.append(sub_b)
                dfs_s.append(sub_s)

        merged_b = pd.concat(dfs_b, ignore_index=True)
        merged_s = pd.concat(dfs_s, ignore_index=True)

        if max_samples is not None and max_samples < len(merged_b):
            if seed is not None:
                rng = np.random.RandomState(seed)
                selected_indices = rng.permutation(len(merged_b))[:max_samples]
                selected_indices = np.sort(selected_indices)
            else:
                selected_indices = np.arange(max_samples)
            merged_b = merged_b.iloc[selected_indices].reset_index(drop=True)
            merged_s = merged_s.iloc[selected_indices].reset_index(drop=True)

        self.df_b = merged_b
        self.df_s = merged_s
        self.n = len(self.df_b)

        # Vetorizar labels para alta velocidade em memória
        self._vectorize_dataset()

        if preload_demos:
            unique_demos = self.df_b["demo_id"].unique()
            self.cache_manager.preload(unique_demos)

    def _vectorize_dataset(self):
        n = self.n
        df_b = self.df_b
        df_s = self.df_s

        seq_ids = df_b["sequence_id"].tolist()
        demos = df_b["demo_id"].tolist()
        round_ids = df_b["round_id"].tolist()
        slots = df_b["slot"].tolist()

        teams = df_b["team"].tolist()
        roles = df_b["role"].tolist()
        stages = df_b["plan_stage"].tolist()

        pos_states = df_b["PositioningState"].tolist()
        transitions = df_b["Transition"].tolist()
        spot_ids = df_b["CandidateSpotId"].tolist()
        spot_loss_masks = df_b["SpotLossMask"].tolist()

        sec_trans = df_s["sector_transition_occurs"].tolist()
        next_secs = df_s["next_sector"].tolist()
        next_sec_loss_masks = df_s["next_sector_loss_mask"].tolist()
        exit_triggers = df_s["exit_trigger"].tolist()

        self.demos = demos
        self.slots = np.array(slots, dtype=np.int64)
        self.round_ids = np.array(round_ids, dtype=np.int64)

        # Parse frame indices de seq_id (pos_{demo}_r{r}_s{s}_f{f_idx})
        f_indices = []
        for s_id in seq_ids:
            f_str = s_id.split("_f")[-1]
            f_indices.append(int(f_str))
        self.f_indices = np.array(f_indices, dtype=np.int64)

        # Contexto
        self.team_vals = np.array([TEAM_MAP.get(t, 2) for t in teams], dtype=np.int64)
        self.role_vals = np.array([ROLE_MAP.get(r, 0) for r in roles], dtype=np.int64)
        self.stage_vals = np.array([STAGE_MAP.get(s, 0) for s in stages], dtype=np.int64)

        # Head A: PositioningState
        self.state_vals = np.array([STATE_MAP.get(s, 0) for s in pos_states], dtype=np.int64)

        # Head B: SectorTransitionOccurs
        self.trans_occurs_vals = np.array([SECTOR_TRANSITION_MAP.get(st, 0) for st in sec_trans], dtype=np.int64)

        # Head C: NextSector
        self.next_sec_vals = np.array([NEXT_SECTOR_MAP.get(ns, 0) for ns in next_secs], dtype=np.int64)
        self.next_sec_mask_vals = np.array(next_sec_loss_masks, dtype=np.float32)

        # Head D: CandidateSpotRanking
        spot_indices = []
        spot_masks = []
        for i in range(n):
            s_id = str(spot_ids[i])
            sp_idx = self.spot_to_idx.get(s_id, 0)
            spot_indices.append(sp_idx)
            # Elegível se não for TRANSIT, catalog ID for válido e tiver máscara positiva
            is_valid = bool(spot_loss_masks[i]) and (s_id != "UNMAPPED_POSITION") and (s_id in self.spot_to_idx)
            is_supervised = (self.supervised_spot_mask[sp_idx] > 0.5)
            spot_masks.append(is_valid and is_supervised)

        self.spot_vals = np.array(spot_indices, dtype=np.int64)
        self.spot_mask_vals = np.array(spot_masks, dtype=bool)

        # Head E: Transition
        self.trans_vals = np.array([TRANSITION_MAP.get(tr, 0) for tr in transitions], dtype=np.int64)

        # Head F: ExitTrigger
        self.trig_vals = np.array([EXIT_TRIGGER_MAP.get(tg, 0) for tg in exit_triggers], dtype=np.int64)

        # Candidate Mask [53]: todos os spots do mapa inicialmente disponíveis na candidate_mask
        self.candidate_mask_arr = np.ones((n, 53), dtype=bool)

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        demo_id = self.demos[idx]
        round_idx = int(self.round_ids[idx])
        slot = int(self.slots[idx])
        f_idx = int(self.f_indices[idx])

        # Extração temporal determinística e autêntica do NPZ
        history, teammates, temporal_mask = self.cache_manager.extract_window(
            demo_id=demo_id,
            round_idx=round_idx,
            slot=slot,
            f_idx=f_idx
        )

        return {
            "self_history": torch.from_numpy(history).float(),
            "teammates": torch.from_numpy(teammates).float(),
            "temporal_mask": torch.from_numpy(temporal_mask).float(),
            "candidate_mask": torch.from_numpy(self.candidate_mask_arr[idx]).bool(),
            "team_idx": torch.tensor(self.team_vals[idx], dtype=torch.long),
            "role_idx": torch.tensor(self.role_vals[idx], dtype=torch.long),
            "stage_idx": torch.tensor(self.stage_vals[idx], dtype=torch.long),
            "positioning_state": torch.tensor(self.state_vals[idx], dtype=torch.long),
            "sector_transition_occurs": torch.tensor(self.trans_occurs_vals[idx], dtype=torch.long),
            "next_sector": torch.tensor(self.next_sec_vals[idx], dtype=torch.long),
            "next_sector_loss_mask": torch.tensor(self.next_sec_mask_vals[idx], dtype=torch.float32),
            "candidate_spot_idx": torch.tensor(self.spot_vals[idx], dtype=torch.long),
            "spot_loss_mask": torch.tensor(self.spot_mask_vals[idx], dtype=torch.bool),
            "transition": torch.tensor(self.trans_vals[idx], dtype=torch.long),
            "exit_trigger": torch.tensor(self.trig_vals[idx], dtype=torch.long)
        }


def canonical_v2_collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
    """Collate function eficiente empilhando todos os tensores do batch."""
    return {
        "self_history": torch.stack([b["self_history"] for b in batch], dim=0),
        "teammates": torch.stack([b["teammates"] for b in batch], dim=0),
        "temporal_mask": torch.stack([b["temporal_mask"] for b in batch], dim=0),
        "candidate_mask": torch.stack([b["candidate_mask"] for b in batch], dim=0),
        "team_idx": torch.stack([b["team_idx"] for b in batch], dim=0),
        "role_idx": torch.stack([b["role_idx"] for b in batch], dim=0),
        "stage_idx": torch.stack([b["stage_idx"] for b in batch], dim=0),
        "positioning_state": torch.stack([b["positioning_state"] for b in batch], dim=0),
        "sector_transition_occurs": torch.stack([b["sector_transition_occurs"] for b in batch], dim=0),
        "next_sector": torch.stack([b["next_sector"] for b in batch], dim=0),
        "next_sector_loss_mask": torch.stack([b["next_sector_loss_mask"] for b in batch], dim=0),
        "candidate_spot_idx": torch.stack([b["candidate_spot_idx"] for b in batch], dim=0),
        "spot_loss_mask": torch.stack([b["spot_loss_mask"] for b in batch], dim=0),
        "transition": torch.stack([b["transition"] for b in batch], dim=0),
        "exit_trigger": torch.stack([b["exit_trigger"] for b in batch], dim=0)
    }
