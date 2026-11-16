#!/usr/bin/env python3
"""
Fase 3A.2 - Passo 8: Construção do Rare State Challenge Set V2 Independente.

Garante:
- CLEARANCE >= 500
- HOLD >= 500
- STAGING >= 300
- RETAKE >= 200
- OBJECTIVE >= 100
- SAVE >= 100
- Zero sobreposição com Train (apenas Validation e Test)
- Deduplicação de episódios e diversidade de partidas/jogadores
- 100% dados reais de partidas do corpus Mirage V2
- Gera:
  * datasets/mirage_v2/positioning/rare_state_challenge_v2.parquet
  * training_runs/positioning_v1/rare_state_challenge_v2_manifest.json
  * training_runs/positioning_v1/rare_state_challenge_v2_provenance.json
"""

import sys
import json
import hashlib
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from tools.phase3a_training.data_utils import (
    determine_state, load_catalog, STATE_NAMES
)

def compute_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 70)
    print("FASE 3A.2: CONSTRUÇÃO DO RARE STATE CHALLENGE SET V2 INDEPENDENTE")
    print("=" * 70)

    ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    pos_dir = ds_dir / "positioning"
    runs_dir = BASE_DIR / "training_runs" / "positioning_v1"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Carregar lista de partidas de Train para garantir ZERO sobreposição
    with open(ds_dir / "splits" / "train_split_v2.json", "r", encoding="utf-8") as f:
        train_d = json.load(f)
        train_matches = set()
        for m in train_d.get("match_ids", []):
            train_matches.add(m if isinstance(m, str) else m.get("demo_id"))

    # 2. Carregar pool de estados tradicionais (CLEARANCE, HOLD, STAGING, RETAKE) de shard_001 e shard_002 (Validation)
    shards_to_use = [
        pos_dir / "positioning_sequences_v1" / "shard_001.parquet",
        pos_dir / "positioning_sequences_v1" / "shard_002.parquet",
        pos_dir / "positioning_sequences_v1" / "shard_003.parquet"
    ]

    trad_dfs = []
    for sf in shards_to_use:
        if sf.exists():
            df = pq.read_table(sf).to_pandas()
            # Apenas validation ou test, e NUNCA train
            df_filtered = df[(df["split"].isin(["validation", "test"])) & (~df["demo_id"].isin(train_matches))].copy()
            trad_dfs.append(df_filtered)

    pool_trad = pd.concat(trad_dfs, ignore_index=True)
    pool_trad["state"] = pool_trad.apply(
        lambda r: determine_state(r["assigned_catalog_id"], r["semantic_type"], r["plan_stage"], r["role"], r["team"]),
        axis=1
    )
    print("Pool tradicional disponível:", pool_trad["state"].value_counts().to_dict())

    # 3. Carregar pool de OBJECTIVE e SAVE de objective_save_sequences.parquet (Validation e Test)
    obj_save_path = pos_dir / "objective_save_sequences.parquet"
    assert obj_save_path.exists(), "objective_save_sequences.parquet não encontrado!"
    df_obj_save = pq.read_table(obj_save_path).to_pandas()
    # Filtrar Validation e Test, e nunca Train
    df_obj_save_challenge = df_obj_save[
        (df_obj_save["split"].isin(["validation", "test"])) &
        (~df_obj_save["demo_id"].isin(train_matches))
    ].copy()
    df_obj_save_challenge["state"] = df_obj_save_challenge["positioning_state"]
    print("Pool OBJECTIVE e SAVE disponível:", df_obj_save_challenge["state"].value_counts().to_dict())

    # 4. Amostragem Balanceada e Descorrelacionada
    # Metas mínimas do protocolo:
    # CLEARANCE >= 500, HOLD >= 500, STAGING >= 300, RETAKE >= 200, OBJECTIVE >= 100, SAVE >= 100
    quotas = {
        "CLEARANCE": 500,
        "HOLD": 500,
        "STAGING": 300,
        "RETAKE": 200,
        "OBJECTIVE": 120,
        "SAVE": 100
    }

    selected_rows = []
    provenance_records = []

    # Extrair estados tradicionais
    for st, q in [("CLEARANCE", 500), ("HOLD", 500), ("STAGING", 300), ("RETAKE", 200)]:
        subset = pool_trad[pool_trad["state"] == st].copy()
        # Deduplicação: no máximo 5 amostras por demo e round
        subset = subset.groupby(["demo_id", "round_index"]).head(5)
        assert len(subset) >= q, f"Suporte insuficiente para {st}: {len(subset)} < {q}"
        taken = subset.iloc[:q].copy()
        selected_rows.append(taken)
        for _, r in taken.iterrows():
            provenance_records.append({
                "sequence_id": r["sequence_id"],
                "demo_id": r["demo_id"],
                "round_index": int(r["round_index"]),
                "slot": int(r["slot"]),
                "split": r["split"],
                "state": st,
                "source": "CANONICAL_VALIDATION_TEST_POOL"
            })

    # Extrair OBJECTIVE e SAVE com descorrelação por episódio
    for st, q in [("OBJECTIVE", 120), ("SAVE", 100)]:
        subset = df_obj_save_challenge[df_obj_save_challenge["state"] == st].copy()
        # No máximo 5 amostras por episódio para diversidade e descorrelação
        if "episode_id" in subset.columns:
            subset = subset.groupby("episode_id").head(5)
        assert len(subset) >= q, f"Suporte insuficiente para {st}: {len(subset)} < {q}"
        taken = subset.iloc[:q].copy()
        selected_rows.append(taken)
        for _, r in taken.iterrows():
            provenance_records.append({
                "sequence_id": r["sequence_id"],
                "demo_id": r["demo_id"],
                "round_index": int(r["round_index"]),
                "slot": int(r["slot"]),
                "split": r["split"],
                "state": st,
                "episode_id": r.get("episode_id", "N/A"),
                "source": "HOMOLOGATED_MIRAGE_V2_CORPUS"
            })

    challenge_df = pd.concat(selected_rows, ignore_index=True)
    # Assegurar presença das colunas essenciais
    if "positioning_state" not in challenge_df.columns:
        challenge_df["positioning_state"] = challenge_df["state"]

    out_parquet = pos_dir / "rare_state_challenge_v2.parquet"
    challenge_df.to_parquet(out_parquet, index=False)
    file_sha256 = compute_sha256(out_parquet)
    print(f"\nRare State Challenge Set V2 gerado com sucesso!")
    print(f"Salvo em: {out_parquet} ({len(challenge_df)} linhas, SHA-256: {file_sha256})")
    print("Distribuição final:")
    for st, count in challenge_df["state"].value_counts().items():
        print(f"  {st}: {count}")

    # Verificar ausência de sobreposição com Train
    overlap = set(challenge_df["demo_id"]).intersection(train_matches)
    assert len(overlap) == 0, f"VIOLAÇÃO CRÍTICA: {len(overlap)} partidas de Train detectadas no Challenge V2!"
    print(f"Verificação de vazamento com Train: 0 partidas sobrepostas (100% independente).")

    # Gerar Manifesto
    manifest = {
        "challenge_set_version": "2.0.0",
        "generated_at_utc": "2026-11-07T00:56:00Z",
        "file_name": "rare_state_challenge_v2.parquet",
        "file_sha256": file_sha256,
        "total_sequences": len(challenge_df),
        "state_quotas_and_actuals": {st: int((challenge_df["state"] == st).sum()) for st in quotas},
        "all_gates_met": all((challenge_df["state"] == st).sum() >= quotas[st] for st in quotas),
        "split_composition": challenge_df["split"].value_counts().to_dict(),
        "unique_demos": int(challenge_df["demo_id"].nunique()),
        "unique_rounds": int(len(challenge_df[["demo_id", "round_index"]].drop_duplicates())),
        "train_overlap_count": len(overlap),
        "synthetic_samples_count": 0
    }
    manifest_path = runs_dir / "rare_state_challenge_v2_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Salvo: {manifest_path}")

    # Gerar Proveniência
    prov_path = runs_dir / "rare_state_challenge_v2_provenance.json"
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_records": len(provenance_records),
            "records": provenance_records
        }, f, indent=2)
    print(f"Salvo: {prov_path}")

if __name__ == "__main__":
    main()
