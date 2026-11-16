#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 1: Reconstrução Temporal Canônica e DataLoader Autêntico de 32 Frames.

Substitui qualquer interpolação artificial (np.linspace, step_drift) e clones de aliados
por extração direta, exata e determinística dos 444 tensores NPZ autênticos gravados a 16Hz
em F:\\CS2_MLMove_Pipeline\\extracted_tensors\\de_mirage\\{demo_id}_16hz.npz.

Garante os invariantes metodológicos inegociáveis:
1. Janela temporal de 32 timesteps (2.0s a 16Hz) para o jogador alvo [32, 18].
2. Respeito estrito às fronteiras de round: RoundBoundaryViolationRate = 0.0%.
   Limites detectados via resets de round_time_norm (X[:, 0, 17] com diff > 0.15).
3. Ausência total de target leakage temporal: FutureLeakageRate = 0.0%.
   Janela termina estritamente em f_idx (frames t' <= f_idx).
4. Mascaramento temporal estrito de padding: UnmaskedPaddingRate = 0.0%.
   Quando o início do round start_f está a menos de 31 frames (k = f_idx - start_f + 1 < 32),
   os primeiros (32 - k) frames são preenchidos com zeros e temporal_mask[:32-k] = 0.0,
   enquanto temporal_mask[32-k:] = 1.0.
5. Aliados autênticos reais: TeammateRealSlotMatchRate = 100.0%.
   Time 1 (slot < 5): aliados são [s for s in range(5) if s != slot].
   Time 2 (slot >= 5): aliados são [s for s in range(5, 10) if s != slot].
   Zero clones transladados, zero offsets arbitrários.
6. Caching eficiente na memória RAM para alto throughput de treinamento.
"""

import os
import sys
import json
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Iterable

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
from torch.utils.data import Dataset, DataLoader

# Base dir resolution
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Caminho canônico dos tensores brutos NPZ
DEFAULT_NPZ_DIR = Path(r"F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage")
FALLBACK_NPZ_DIR = BASE_DIR / "extracted_tensors"

# Mapeamentos canônicos compartilhados
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


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class NPZCacheManager:
    """
    Gerenciador thread-safe de cache em RAM para tensores brutos NPZ (16Hz) de partidas CS2.
    Detecta limites exatos de rounds usando round_time_norm (X[:, 0, 17]) com diff > 0.15.
    Extrai janelas de 32 frames com mascaramento rigoroso de padding e fronteiras de round.
    """
    def __init__(self, npz_dir: Optional[Path] = None):
        if npz_dir is not None:
            self.npz_dir = Path(npz_dir)
        elif DEFAULT_NPZ_DIR.exists():
            self.npz_dir = DEFAULT_NPZ_DIR
        else:
            self.npz_dir = FALLBACK_NPZ_DIR

        self._lock = threading.Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def resolve_npz_path(self, demo_id: str) -> Path:
        stem = demo_id.replace("_16hz", "")
        candidate_1 = self.npz_dir / f"{stem}_16hz.npz"
        if candidate_1.exists():
            return candidate_1
        candidate_2 = self.npz_dir / f"{demo_id}.npz"
        if candidate_2.exists():
            return candidate_2
        # Tentar fallback
        fallback_1 = FALLBACK_NPZ_DIR / f"{stem}_16hz.npz"
        if fallback_1.exists():
            return fallback_1
        raise FileNotFoundError(f"Arquivo NPZ para demo '{demo_id}' não encontrado em {self.npz_dir} nem em {FALLBACK_NPZ_DIR}")

    def load_demo(self, demo_id: str) -> Dict[str, Any]:
        with self._lock:
            if demo_id in self._cache:
                return self._cache[demo_id]

        npz_path = self.resolve_npz_path(demo_id)
        sha256_hash = compute_sha256(npz_path)

        with np.load(npz_path) as data:
            X = data["X"] # [total_frames, 10, 18], float32

        n_frames = X.shape[0]
        # Feature 17 é round_time_norm [0.0, 1.0]
        r_time = X[:, 0, 17]
        diffs = np.diff(r_time)
        resets = np.where(diffs > 0.15)[0]
        round_bounds = [0] + [int(r + 1) for r in resets] + [n_frames]

        entry = {
            "demo_id": demo_id,
            "path": str(npz_path),
            "sha256": sha256_hash,
            "X": X,
            "n_frames": n_frames,
            "round_bounds": round_bounds
        }

        with self._lock:
            self._cache[demo_id] = entry

        return entry

    def preload(self, demo_ids: Iterable[str]):
        """Pré-carrega um conjunto de demos na RAM para throughput máximo."""
        unique_ids = set(demo_ids)
        for d in unique_ids:
            self.load_demo(d)

    def extract_window(
        self,
        demo_id: str,
        round_idx: int,
        slot: int,
        f_idx: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extrai deterministicamente:
        - history: [32, 18] float32
        - teammates: [32, 4, 18] float32
        - temporal_mask: [32] float32 (1.0 = frame autêntico, 0.0 = padding pré-round)

        Invariantes:
        - Nunca lê frames anteriores ao início do round (start_f): RoundBoundaryViolationRate = 0%.
        - Nunca lê frames posteriores a f_idx: FutureLeakageRate = 0%.
        - Padding preenchido com zeros e mascarado com 0.0: UnmaskedPaddingRate = 0%.
        - Companheiros de equipe obtidos dos 4 slots reais do mesmo time.
        """
        demo_entry = self.load_demo(demo_id)
        X = demo_entry["X"]
        round_bounds = demo_entry["round_bounds"]

        # Determinar SEMPRE e OBRIGATORIAMENTE a fronteira usando f_idx via busca determinística
        r_detected = int(np.searchsorted(round_bounds, f_idx, side="right") - 1)
        r_detected = max(0, min(r_detected, len(round_bounds) - 2))
        start_f = int(round_bounds[r_detected])
        end_f = int(round_bounds[r_detected + 1])

        # Determinar slots dos 4 aliados reais
        if slot < 5:
            teammate_slots = [s for s in range(5) if s != slot]
        else:
            teammate_slots = [s for s in range(5, 10) if s != slot]

        k = f_idx - start_f + 1

        if k >= 32:
            # Janela completa de 32 frames autênticos do round
            history = X[f_idx - 31 : f_idx + 1, slot, :].copy()
            teammates = X[f_idx - 31 : f_idx + 1, teammate_slots, :].copy()
            temporal_mask = np.ones(32, dtype=np.float32)
        else:
            # Início de round: k frames válidos [start_f : f_idx + 1]
            # (32 - k) frames de padding inicial rigorosamente mascarados
            history = np.zeros((32, 18), dtype=np.float32)
            teammates = np.zeros((32, 4, 18), dtype=np.float32)
            temporal_mask = np.zeros(32, dtype=np.float32)

            if k > 0:
                history[32 - k :] = X[start_f : f_idx + 1, slot, :]
                teammates[32 - k :] = X[start_f : f_idx + 1, teammate_slots, :]
                temporal_mask[32 - k :] = 1.0

        return history, teammates, temporal_mask


def load_catalog(ds_dir: Path) -> Tuple[List[str], Dict[str, int]]:
    """Carrega o catálogo formal de 53 spots de Mirage."""
    catalog_path = ds_dir / "contracts" / "mirage_spot_catalog_v3.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    spot_ids = [s["id"] for s in data["spots"]]
    spot_to_idx = {s_id: i for i, s_id in enumerate(spot_ids)}
    return spot_ids, spot_to_idx


def load_canonical_temporal_splits(ds_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Carrega o arquivo formal de divisões dos 444 tensores NPZ autênticos."""
    if ds_dir is None:
        ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    splits_path = Path(ds_dir) / "canonical_temporal_splits_v1.json"
    if not splits_path.exists():
        return {}
    with open(splits_path, "r", encoding="utf-8") as f:
        return json.load(f)


class CanonicalTemporalPositioningDataset(Dataset):
    """
    Dataset canônico de alta fidelidade para treinamento e avaliação do Positioning Transformer.
    Conecta as sequências dos Parquets da Fase 2 diretamente aos 444 tensores NPZ originais,
    eliminando todo dado sintético/interpolado.
    """
    def __init__(
        self,
        ds_dir: Optional[Path] = None,
        split: Optional[str] = None,
        parquet_paths: Optional[Union[Path, str, List[Path], List[str]]] = None,
        spot_to_idx: Optional[Dict[str, int]] = None,
        npz_dir: Optional[Path] = None,
        max_samples: Optional[int] = None,
        preload_npz: bool = True,
        cache_manager: Optional[NPZCacheManager] = None,
        filter_split: bool = True
    ):
        if ds_dir is None:
            ds_dir = BASE_DIR / "datasets" / "mirage_v2"
        self.ds_dir = Path(ds_dir)

        if spot_to_idx is None:
            _, self.spot_to_idx = load_catalog(self.ds_dir)
        else:
            self.spot_to_idx = spot_to_idx

        # Carregar divisão canônica formal de 444 demos
        self.splits_data = load_canonical_temporal_splits(self.ds_dir)
        allowed_split_demos = None
        if split and filter_split and self.splits_data:
            split_key = "validation" if split in ["val", "validation"] else split
            demo_key = f"{split_key}_demos"
            if demo_key in self.splits_data:
                allowed_split_demos = set(self.splits_data[demo_key])

        # Resolver cache manager
        if cache_manager is not None:
            self.cache_manager = cache_manager
        else:
            self.cache_manager = NPZCacheManager(npz_dir=npz_dir)

        # Resolver arquivos parquet
        if parquet_paths is not None:
            if isinstance(parquet_paths, (str, Path)):
                resolved_paths = [Path(parquet_paths)]
            else:
                resolved_paths = [Path(p) for p in parquet_paths]
        else:
            v2_dir = self.ds_dir / "positioning_v2_full_temporal"
            if v2_dir.exists() and list(v2_dir.glob("shard_*.parquet")):
                resolved_paths = sorted(list(v2_dir.glob("shard_*.parquet")))
            elif split in ["test", "canonical_test"]:
                resolved_paths = [self.ds_dir / "positioning" / "canonical_test_set.parquet"]
            else:
                pos_dir = self.ds_dir / "positioning" / "positioning_sequences_v1"
                resolved_paths = sorted(list(pos_dir.glob("shard_*.parquet")))

        self.split = split
        self.resolved_paths = resolved_paths

        # Carregar metadados dos parquets
        dfs = []
        collected = 0
        for p in self.resolved_paths:
            if not p.exists():
                continue
            table = pq.read_table(p)
            df = table.to_pandas()

            if split and filter_split:
                split_val = "validation" if split in ["val", "validation"] else split
                if "split" in df.columns:
                    df = df[df["split"] == split_val].reset_index(drop=True)
                if allowed_split_demos is not None:
                    df = df[df["demo_id"].isin(allowed_split_demos)].reset_index(drop=True)

            if max_samples:
                remaining = max_samples - collected
                if remaining <= 0:
                    break
                if len(df) > remaining:
                    df = df.iloc[:remaining].reset_index(drop=True)

            if len(df) > 0:
                dfs.append(df)
                collected += len(df)

        if not dfs:
            raise ValueError(f"Nenhum dado encontrado para o split '{split}' nos arquivos {resolved_paths}")

        self.df = pd.concat(dfs, ignore_index=True)
        self.n = len(self.df)

        # Vetorização e pré-processamento de labels
        self._preprocess_labels()

        # Pré-carregar demos em cache se solicitado
        if preload_npz:
            unique_demos = self.df["demo_id"].unique()
            self.cache_manager.preload(unique_demos)

    def _preprocess_labels(self):
        n = self.n
        df = self.df

        cat_ids = df["CandidateSpotId"].tolist() if "CandidateSpotId" in df.columns else (df["assigned_catalog_id"].tolist() if "assigned_catalog_id" in df.columns else ["UNMAPPED_POSITION"] * n)
        sem_types = df["semantic_type"].tolist() if "semantic_type" in df.columns else ["POSITION_PROFILE"] * n
        p_stages = df["plan_stage"].tolist() if "plan_stage" in df.columns else ["Setup"] * n
        roles = df["role"].tolist() if "role" in df.columns else ["SUPPORT"] * n
        teams = df["team"].tolist() if "team" in df.columns else ["CT"] * n
        next_secs = df["NextSector"].tolist() if "NextSector" in df.columns else (df["next_sector"].tolist() if "next_sector" in df.columns else ["DYNAMIC"] * n)
        seq_ids = df["sequence_id"].tolist()
        demos = df["demo_id"].tolist()
        r_indices = df["round_id"].tolist() if "round_id" in df.columns else (df["round_index"].tolist() if "round_index" in df.columns else [0] * n)
        slots = df["slot"].tolist()

        has_explicit_state = "positioning_state" in df.columns or "PositioningState" in df.columns
        explicit_states = df["PositioningState"].tolist() if "PositioningState" in df.columns else (df["positioning_state"].tolist() if "positioning_state" in df.columns else [None] * n)

        self.team_vals = np.array([TEAM_MAP.get(t, 2) for t in teams], dtype=np.int64)
        self.role_vals = np.array([ROLE_MAP.get(r, 0) for r in roles], dtype=np.int64)
        self.stage_vals = np.array([STAGE_MAP.get(s, 0) for s in p_stages], dtype=np.int64)

        state_vals = []
        sector_vals = []
        spot_vals = []
        spot_mask_vals = []
        trans_vals = []
        trig_vals = []
        f_indices = []

        for i in range(n):
            c_id = str(cat_ids[i])
            s_type = str(sem_types[i])
            stg = str(p_stages[i])
            rl = str(roles[i])
            tm = str(teams[i])
            nxt_s = str(next_secs[i])
            exp_st = str(explicit_states[i]) if has_explicit_state and explicit_states[i] is not None else None

            # Frame index parsed de seq_id (formato pos_{demo}_r{r}_s{s}_f{f_idx})
            s_id = str(seq_ids[i])
            f_str = s_id.split("_f")[-1]
            f_indices.append(int(f_str))

            st_name = determine_state(c_id, s_type, stg, rl, tm, explicit_state=exp_st)
            state_vals.append(STATE_MAP[st_name])

            sec_name = determine_sector(nxt_s)
            sector_vals.append(SECTOR_MAP[sec_name])

            is_valid_spot = (c_id != "UNMAPPED_POSITION") and (c_id in self.spot_to_idx)
            sp_idx = self.spot_to_idx.get(c_id, 0)
            spot_vals.append(sp_idx)

            spot_mask_vals.append(bool(is_valid_spot and st_name != "TRANSIT"))

            tr_name = determine_transition(st_name, rl)
            trans_vals.append(TRANSITION_MAP[tr_name])

            ex_name = determine_exit_trigger(st_name, stg)
            trig_vals.append(EXIT_TRIGGER_MAP[ex_name])

        self.state_vals = np.array(state_vals, dtype=np.int64)
        self.sector_vals = np.array(sector_vals, dtype=np.int64)
        self.spot_vals = np.array(spot_vals, dtype=np.int64)
        self.spot_mask_vals = np.array(spot_mask_vals, dtype=bool)
        self.trans_vals = np.array(trans_vals, dtype=np.int64)
        self.trig_vals = np.array(trig_vals, dtype=np.int64)
        self.f_indices = np.array(f_indices, dtype=np.int64)
        self.demos = demos
        self.r_indices = np.array(r_indices, dtype=np.int64)
        self.slots = np.array(slots, dtype=np.int64)
        self.candidate_mask_arr = np.ones((n, 53), dtype=bool)

        # Metadados estruturados
        self.metadata = []
        for i in range(n):
            self.metadata.append({
                "sequence_id": seq_ids[i],
                "demo_id": demos[i],
                "round_index": int(r_indices[i]),
                "slot": int(slots[i]),
                "frame_index": int(f_indices[i]),
                "team": teams[i],
                "role": roles[i],
                "plan_stage": p_stages[i],
                "assigned_catalog_id": cat_ids[i],
                "next_sector": next_secs[i]
            })

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        demo_id = self.demos[idx]
        round_idx = int(self.r_indices[idx])
        slot = int(self.slots[idx])
        f_idx = int(self.f_indices[idx])

        # Extração temporal autêntica do NPZ
        history, teammates, temporal_mask = self.cache_manager.extract_window(
            demo_id=demo_id,
            round_idx=round_idx,
            slot=slot,
            f_idx=f_idx
        )

        return {
            "history": torch.from_numpy(history).float(),
            "teammates": torch.from_numpy(teammates).float(),
            "temporal_mask": torch.from_numpy(temporal_mask).float(),
            "candidate_mask": torch.from_numpy(self.candidate_mask_arr[idx]),
            "team_idx": torch.tensor(self.team_vals[idx], dtype=torch.long),
            "role_idx": torch.tensor(self.role_vals[idx], dtype=torch.long),
            "stage_idx": torch.tensor(self.stage_vals[idx], dtype=torch.long),
            "positioning_state": torch.tensor(self.state_vals[idx], dtype=torch.long),
            "next_sector": torch.tensor(self.sector_vals[idx], dtype=torch.long),
            "candidate_spot_idx": torch.tensor(self.spot_vals[idx], dtype=torch.long),
            "spot_loss_mask": torch.tensor(self.spot_mask_vals[idx], dtype=torch.bool),
            "transition": torch.tensor(self.trans_vals[idx], dtype=torch.long),
            "exit_trigger": torch.tensor(self.trig_vals[idx], dtype=torch.long),
            "metadata": self.metadata[idx]
        }


def canonical_collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collate function canônica empilhando tensores e agregando metadados em lista."""
    return {
        "history": torch.stack([item["history"] for item in batch], dim=0),
        "teammates": torch.stack([item["teammates"] for item in batch], dim=0),
        "temporal_mask": torch.stack([item["temporal_mask"] for item in batch], dim=0),
        "candidate_mask": torch.stack([item["candidate_mask"] for item in batch], dim=0),
        "team_idx": torch.stack([item["team_idx"] for item in batch], dim=0),
        "role_idx": torch.stack([item["role_idx"] for item in batch], dim=0),
        "stage_idx": torch.stack([item["stage_idx"] for item in batch], dim=0),
        "positioning_state": torch.stack([item["positioning_state"] for item in batch], dim=0),
        "next_sector": torch.stack([item["next_sector"] for item in batch], dim=0),
        "candidate_spot_idx": torch.stack([item["candidate_spot_idx"] for item in batch], dim=0),
        "spot_loss_mask": torch.stack([item["spot_loss_mask"] for item in batch], dim=0),
        "transition": torch.stack([item["transition"] for item in batch], dim=0),
        "exit_trigger": torch.stack([item["exit_trigger"] for item in batch], dim=0),
        "metadata": [item["metadata"] for item in batch]
    }


def create_canonical_temporal_dataloader(
    ds_dir: Optional[Path] = None,
    split: str = "train",
    parquet_paths: Optional[Union[Path, str, List[Path], List[str]]] = None,
    batch_size: int = 64,
    shuffle: Optional[bool] = None,
    num_workers: int = 0,
    max_samples: Optional[int] = None,
    npz_dir: Optional[Path] = None,
    preload_npz: bool = True,
    cache_manager: Optional[NPZCacheManager] = None
) -> DataLoader:
    """
    Cria e retorna o DataLoader Temporal Canônico oficial.
    Configuração determinística e alta performance em PyTorch.
    """
    dataset = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split=split,
        parquet_paths=parquet_paths,
        npz_dir=npz_dir,
        max_samples=max_samples,
        preload_npz=preload_npz,
        cache_manager=cache_manager
    )

    if shuffle is None:
        shuffle = True if split == "train" else False

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=canonical_collate_fn,
        pin_memory=torch.cuda.is_available()
    )


if __name__ == "__main__":
    print("Testando inicialização rápida do CanonicalTemporalPositioningDataset...")
    ds = CanonicalTemporalPositioningDataset(split="validation", max_samples=10, preload_npz=True)
    loader = DataLoader(ds, batch_size=4, collate_fn=canonical_collate_fn)
    sample_batch = next(iter(loader))
    print(f"Batch carregado com sucesso!")
    print(f"  history shape: {sample_batch['history'].shape}")
    print(f"  teammates shape: {sample_batch['teammates'].shape}")
    print(f"  temporal_mask shape: {sample_batch['temporal_mask'].shape}")
    print(f"  candidate_mask shape: {sample_batch['candidate_mask'].shape}")
    print(f"  metadata count: {len(sample_batch['metadata'])}")
