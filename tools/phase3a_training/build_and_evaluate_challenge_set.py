#!/usr/bin/env python3
"""
Fase 3A.1 - Passo 11 e 12: Construção e Avaliação Canônica do Rare State Challenge Set.

Regras Estritas:
- 100% dados reais (zero síntese)
- Proveniência de validação e holdout não usados no treino
- Declaração honesta de INSUFFICIENT_REAL_SUPPORT para classes ausentes
- Avaliação com o checkpoint mestre existente
- Verificação formal dos gates por estado raro
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
from torch.utils.data import DataLoader

from tools.phase3a_training.positioning_model import PositioningTransformerV1
from tools.phase3a_training.data_utils import (
    determine_state, determine_sector, determine_transition, determine_exit_trigger,
    load_catalog, load_and_preprocess_shard, InMemoryPositioningDataset,
    STATE_NAMES, np_per_class_prf
)

def compute_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    base_dir = Path(__file__).resolve().parents[2]
    runs_dir = base_dir / "training_runs" / "positioning_v1"
    ds_dir = base_dir / "datasets" / "mirage_v2"
    pos_dir = ds_dir / "positioning" / "positioning_sequences_v1"
    models_dir = base_dir / "models" / "positioning"

    print("=" * 70, flush=True)
    print("FASE 3A.1: CONSTRUÇÃO E AVALIAÇÃO DO RARE STATE CHALLENGE SET", flush=True)
    print("=" * 70, flush=True)

    spot_ids, spot_to_idx = load_catalog(ds_dir)

    # 1. Coleta de Amostras Reais (de shard_001 e shard_002 - Validation)
    # Não usamos nada do shard_000 (Train)
    shards_to_use = [pos_dir / "shard_001.parquet", pos_dir / "shard_002.parquet"]
    
    collected_rows = []
    for sf in shards_to_use:
        df = pq.read_table(sf).to_pandas()
        df_val = df[df["split"] == "validation"].copy()
        df_val["source_shard"] = sf.name
        collected_rows.append(df_val)

    pool_df = pd.concat(collected_rows, ignore_index=True)
    pool_df["state"] = pool_df.apply(
        lambda r: determine_state(r["assigned_catalog_id"], r["semantic_type"], r["plan_stage"], r["role"], r["team"]),
        axis=1
    )

    print("Pool real disponível para Challenge Set:", pool_df["state"].value_counts().to_dict(), flush=True)

    # Alvos reais:
    # CLEARANCE: 600, HOLD: 600, STAGING: 300, RETAKE: 200, TRANSIT: 300
    targets_quota = {
        "CLEARANCE": 600,
        "HOLD": 600,
        "STAGING": 300,
        "RETAKE": 200,
        "OBJECTIVE": 100, # Será verificado suporte
        "SAVE": 100,      # Será verificado suporte
        "TRANSIT": 300
    }

    selected_dfs = []
    support_status = {}

    for st_name, quota in targets_quota.items():
        subset = pool_df[pool_df["state"] == st_name]
        avail = len(subset)
        if avail >= quota:
            taken = subset.iloc[:quota]
            selected_dfs.append(taken)
            support_status[st_name] = {"target": quota, "actual": len(taken), "status": "ADEQUATE_REAL_SUPPORT"}
        elif avail > 0:
            taken = subset
            selected_dfs.append(taken)
            support_status[st_name] = {"target": quota, "actual": len(taken), "status": "PARTIAL_REAL_SUPPORT"}
        else:
            support_status[st_name] = {"target": quota, "actual": 0, "status": "INSUFFICIENT_REAL_SUPPORT"}

    challenge_df = pd.concat(selected_dfs, ignore_index=True)
    print(f"\nTotal selecionado para Challenge Set: {len(challenge_df)} sequências", flush=True)

    # Salvar Parquet do Challenge Set
    challenge_parquet = ds_dir / "positioning" / "rare_state_challenge_set.parquet"
    challenge_df.to_parquet(challenge_parquet, index=False)
    challenge_hash = compute_sha256(challenge_parquet)

    # 2. Manifesto e Proveniência
    manifest = {
        "dataset_name": "RARE_STATE_CHALLENGE_SET_MIRAGE_V2",
        "file_path": str(challenge_parquet.resolve()),
        "file_sha256": challenge_hash,
        "file_size_bytes": challenge_parquet.stat().st_size,
        "total_examples": len(challenge_df),
        "target_quotas": targets_quota,
        "support_status": support_status,
        "state_distribution": challenge_df["state"].value_counts().to_dict(),
        "source_shards": list(pool_df["source_shard"].unique()),
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    manifest_path = runs_dir / "rare_state_challenge_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Proveniência detalhada
    prov_data = challenge_df[["sequence_id", "demo_id", "round_index", "slot", "team", "role", "plan_stage", "state", "assigned_catalog_id", "source_shard"]].to_dict(orient="records")
    prov_path = runs_dir / "rare_state_challenge_provenance.json"
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump({"total_records": len(prov_data), "records": prov_data[:100], "all_records_sample_count": len(prov_data)}, f, indent=2)

    # 3. Avaliar Checkpoint Mestre no Challenge Set
    master_model_path = models_dir / "de_mirage_positioning_v1.pt"
    print(f"\nAvaliando Checkpoint Mestre: {master_model_path}", flush=True)
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

    prep = load_and_preprocess_shard(challenge_parquet, spot_to_idx)
    ch_ds = InMemoryPositioningDataset(
        history=prep["history"],
        teammates=prep["teammates"],
        candidate_mask=prep["candidate_mask"],
        team_idx=prep["team_idx"],
        role_idx=prep["role_idx"],
        stage_idx=prep["stage_idx"],
        targets=prep["targets"],
        metadata=prep["metadata"]
    )
    ch_loader = DataLoader(ch_ds, batch_size=128, shuffle=False)

    all_logits = []
    all_labels = []

    with torch.no_grad():
        for batch in ch_loader:
            out = model(
                history=batch["history"],
                teammates=batch["teammates"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )
            all_logits.append(out["logits_state"].cpu().numpy())
            all_labels.append(batch["positioning_state"].cpu().numpy())

    ch_logits = np.concatenate(all_logits, axis=0)
    ch_labels = np.concatenate(all_labels, axis=0)
    ch_preds = np.argmax(ch_logits, axis=1)

    # Matriz e Métricas
    cm_ch = np.zeros((7, 7), dtype=int)
    for t, p in zip(ch_labels, ch_preds):
        cm_ch[t, p] += 1

    p_ch, r_ch, f1_ch, sup_ch = np_per_class_prf(ch_labels, ch_preds, num_classes=7)

    # Gates de aprovação técnica
    gates = {
        "CLEARANCE": {"min_f1": 0.65, "f1": float(f1_ch[1]), "pass": bool(f1_ch[1] >= 0.65)},
        "HOLD": {"min_f1": 0.45, "f1": float(f1_ch[3]), "pass": bool(f1_ch[3] >= 0.45)},
        "STAGING": {"min_f1": 0.40, "f1": float(f1_ch[2]), "pass": bool(f1_ch[2] >= 0.40)},
        "RETAKE": {"min_f1": 0.35, "f1": float(f1_ch[5]), "pass": bool(f1_ch[5] >= 0.35)},
        "OBJECTIVE": {"min_f1": 0.35, "f1": None, "pass": False, "reason": "INSUFFICIENT_REAL_SUPPORT"},
        "SAVE": {"min_f1": 0.35, "f1": None, "pass": False, "reason": "INSUFFICIENT_REAL_SUPPORT"}
    }

    supp_mask = sup_ch > 0
    balanced_acc_ch = float(np.mean(r_ch[supp_mask]))
    macro_f1_ch = float(np.mean(f1_ch[supp_mask]))
    acc_ch = float(np.mean(ch_preds == ch_labels))

    per_class_ch = {}
    for i, name in enumerate(STATE_NAMES):
        if sup_ch[i] > 0:
            per_class_ch[name] = {
                "support": int(sup_ch[i]),
                "precision": round(float(p_ch[i]), 4),
                "recall": round(float(r_ch[i]), 4),
                "f1": round(float(f1_ch[i]), 4),
                "gate_criteria": gates.get(name, {}),
                "status": "PASS" if gates.get(name, {}).get("pass", False) else "FAIL"
            }
        else:
            per_class_ch[name] = {
                "support": 0,
                "precision": None,
                "recall": None,
                "f1": None,
                "gate_criteria": gates.get(name, {}),
                "status": "INSUFFICIENT_REAL_SUPPORT"
            }

    challenge_results = {
        "evaluation_name": "RARE_STATE_CHALLENGE_EVALUATION",
        "total_challenge_sequences": len(ch_labels),
        "overall_accuracy": round(acc_ch, 4),
        "balanced_accuracy": round(balanced_acc_ch, 4),
        "macro_f1_evaluated_classes": round(macro_f1_ch, 4),
        "per_class": per_class_ch,
        "gates_summary": gates,
        "confusion_matrix_raw": cm_ch.tolist(),
        "overall_challenge_verdict": "FAIL_REQUIRES_RARE_STATE_RETRAINING" if not all(g["pass"] for g in gates.values()) else "PASS"
    }

    out_metrics_path = runs_dir / "canonical_challenge_metrics.json"
    with open(out_metrics_path, "w", encoding="utf-8") as f:
        json.dump(challenge_results, f, indent=2)

    print(f"\ncanonical_challenge_metrics.json salvo: {out_metrics_path}", flush=True)
    print("Gates Summary:", flush=True)
    print(json.dumps(gates, indent=2), flush=True)

if __name__ == "__main__":
    main()
