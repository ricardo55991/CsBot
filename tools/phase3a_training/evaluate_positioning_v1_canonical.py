#!/usr/bin/env python3
"""
Fase 3A.1 - Passo 3 e 4: Reexecução Canônica da Inferência e Materialização dos Arrays Canônicos.

Garante:
- model.eval() e torch.no_grad()
- Zero shuffle, zero dropout, zero data augmentation
- Salvamento de todos os tensores/arrays brutos em canonical_eval/
- Cálculo de SHA-256 para cada arquivo gerado
- Proveniência completa em provenance.parquet
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path

# Raiz no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
from torch.utils.data import DataLoader

from tools.phase3a_training.positioning_model import PositioningTransformerV1
from tools.phase3a_training.data_utils import (
    load_catalog,
    load_and_preprocess_shard,
    InMemoryPositioningDataset,
    STATE_NAMES,
    SECTOR_NAMES,
    TRANSITION_NAMES,
    EXIT_TRIGGER_NAMES
)

def compute_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_canonical_inference():
    base_dir = Path(__file__).resolve().parents[2]
    ds_dir = base_dir / "datasets" / "mirage_v2"
    runs_dir = base_dir / "training_runs" / "positioning_v1"
    models_dir = base_dir / "models" / "positioning"
    eval_dir = runs_dir / "canonical_eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70, flush=True)
    print("FASE 3A.1: INFERÊNCIA CANÔNICA DO POSITIONING TRANSFORMER V1", flush=True)
    print("=" * 70, flush=True)

    # 1. Carregar Checkpoint Mestre
    master_model_path = models_dir / "de_mirage_positioning_v1.pt"
    print(f"Carregando checkpoint mestre: {master_model_path}", flush=True)
    checkpoint = torch.load(master_model_path, map_location="cpu")
    cfg = checkpoint.get("config", {})

    model = PositioningTransformerV1(
        hidden_dim=cfg.get("hidden_dim", 192),
        num_layers=cfg.get("num_layers", 3),
        num_heads=cfg.get("num_heads", 6),
        feedforward_dim=cfg.get("feedforward_dim", 768),
        dropout=cfg.get("dropout", 0.10)
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Desativar formalmente dropout e checar training mode
    assert not model.training, "O modelo deve estar estritamente em model.eval()"

    # 2. Carregar Test Set Canônico Congelado
    test_parquet_path = ds_dir / "positioning" / "canonical_test_set.parquet"
    print(f"Carregando Test Set Canônico: {test_parquet_path}", flush=True)
    spot_ids, spot_to_idx = load_catalog(ds_dir)

    prep = load_and_preprocess_shard(test_parquet_path, spot_to_idx)
    test_ds = InMemoryPositioningDataset(
        history=prep["history"],
        teammates=prep["teammates"],
        candidate_mask=prep["candidate_mask"],
        team_idx=prep["team_idx"],
        role_idx=prep["role_idx"],
        stage_idx=prep["stage_idx"],
        targets=prep["targets"],
        metadata=prep["metadata"]
    )
    print(f"Total de sequências carregadas: {len(test_ds)}", flush=True)

    test_loader = DataLoader(test_ds, batch_size=128, shuffle=False)

    # 3. Executar Inferência
    t0 = time.time()
    state_logits_list = []
    sector_logits_list = []
    spot_scores_list = []
    transition_logits_list = []
    trigger_logits_list = []

    state_labels_list = []
    sector_labels_list = []
    spot_labels_list = []
    candidate_masks_list = []
    spot_loss_masks_list = []
    transition_labels_list = []
    trigger_labels_list = []

    batch_count = 0
    with torch.no_grad():
        for batch in test_loader:
            outputs = model(
                history=batch["history"],
                teammates=batch["teammates"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )
            state_logits_list.append(outputs["logits_state"].cpu().numpy())
            sector_logits_list.append(outputs["logits_sector"].cpu().numpy())
            spot_scores_list.append(outputs["logits_spot"].cpu().numpy())
            transition_logits_list.append(outputs["logits_transition"].cpu().numpy())
            trigger_logits_list.append(outputs["logits_trigger"].cpu().numpy())

            state_labels_list.append(batch["positioning_state"].cpu().numpy())
            sector_labels_list.append(batch["next_sector"].cpu().numpy())
            spot_labels_list.append(batch["candidate_spot_idx"].cpu().numpy())
            candidate_masks_list.append(batch["candidate_mask"].cpu().numpy())
            spot_loss_masks_list.append(batch["spot_loss_mask"].cpu().numpy())
            transition_labels_list.append(batch["transition"].cpu().numpy())
            trigger_labels_list.append(batch["exit_trigger"].cpu().numpy())

            batch_count += 1

    inference_time = time.time() - t0
    print(f"Inferência concluída em {inference_time:.2f}s ({batch_count} batches)", flush=True)

    # Concatenar arrays
    state_logits = np.concatenate(state_logits_list, axis=0)
    state_labels = np.concatenate(state_labels_list, axis=0)
    sector_logits = np.concatenate(sector_logits_list, axis=0)
    sector_labels = np.concatenate(sector_labels_list, axis=0)
    spot_scores = np.concatenate(spot_scores_list, axis=0)
    spot_labels = np.concatenate(spot_labels_list, axis=0)
    candidate_masks = np.concatenate(candidate_masks_list, axis=0)
    spot_loss_masks = np.concatenate(spot_loss_masks_list, axis=0)
    transition_logits = np.concatenate(transition_logits_list, axis=0)
    transition_labels = np.concatenate(transition_labels_list, axis=0)
    trigger_logits = np.concatenate(trigger_logits_list, axis=0)
    trigger_labels = np.concatenate(trigger_labels_list, axis=0)

    # 4. Salvar Arrays Canônicos em canonical_eval/
    files_to_save = {
        "state_logits.npy": state_logits,
        "state_labels.npy": state_labels,
        "sector_logits.npy": sector_logits,
        "sector_labels.npy": sector_labels,
        "spot_scores.npy": spot_scores,
        "spot_labels.npy": spot_labels,
        "candidate_masks.npy": candidate_masks,
        "spot_loss_masks.npy": spot_loss_masks,
        "transition_logits.npy": transition_logits,
        "transition_labels.npy": transition_labels,
        "trigger_logits.npy": trigger_logits,
        "trigger_labels.npy": trigger_labels,
    }

    manifest_files = {}
    for fname, arr in files_to_save.items():
        fp = eval_dir / fname
        np.save(fp, arr)
        manifest_files[fname] = {
            "path": str(fp.resolve()),
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "size_bytes": fp.stat().st_size,
            "sha256": compute_sha256(fp)
        }

    # Salvar provenance.parquet
    prov_df = pd.DataFrame(prep["metadata"])
    prov_df["state_label"] = [STATE_NAMES[s] for s in state_labels]
    prov_df["sector_label"] = [SECTOR_NAMES[s] for s in sector_labels]
    prov_df["spot_loss_mask"] = spot_loss_masks
    prov_path = eval_dir / "provenance.parquet"
    prov_df.to_parquet(prov_path, index=False)
    manifest_files["provenance.parquet"] = {
        "path": str(prov_path.resolve()),
        "rows": len(prov_df),
        "columns": list(prov_df.columns),
        "size_bytes": prov_path.stat().st_size,
        "sha256": compute_sha256(prov_path)
    }

    # Manifesto Canônico da Avaliação
    manifest_eval = {
        "master_model_path": str(master_model_path.resolve()),
        "master_model_sha256": compute_sha256(master_model_path),
        "test_dataset_path": str(test_parquet_path.resolve()),
        "test_dataset_sha256": compute_sha256(test_parquet_path),
        "total_examples": len(state_labels),
        "batch_count": batch_count,
        "inference_time_seconds": float(np.round(inference_time, 4)),
        "files": manifest_files,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    manifest_eval_path = eval_dir / "canonical_eval_manifest.json"
    with open(manifest_eval_path, "w", encoding="utf-8") as f:
        json.dump(manifest_eval, f, indent=2)

    print(f"Manifesto canônico salvo: {manifest_eval_path}", flush=True)
    print("ETAPA 3 e 4 CONCLUÍDAS COM SUCESSO!", flush=True)

if __name__ == "__main__":
    run_canonical_inference()
