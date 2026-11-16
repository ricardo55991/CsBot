#!/usr/bin/env python3
"""Inspeciona sinais causais disponíveis no fim da janela (label_frame) nos Parquets e NPZs (Train + Validation apenas)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
INDEX_DIR = BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"

# Coordenadas aproximadas dos bombsites de Mirage (A e B) a partir do mapa / spots
# Vamos carregar do mirage_spot_catalog_v3.json ou usar centros aproximados e checar nos dados!
def main():
    cols = [
        "sequence_id", "demo_id", "split", "npz_path", "label_frame", "slot",
        "team", "plan_stage", "current_sector", "positioning_state",
        "objective_subtype", "save_subtype", "provenance_type"
    ]
    dfs = []
    for i in range(6):
        df = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=cols)
        df = df[df["split"].isin(["train", "validation"])].copy()
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)

    for sp in ["train", "validation"]:
        sub = df[df["split"] == sp]
        print(f"\n=== {sp.upper()} (N={len(sub)}) ===")
        print("plan_stage total:", sub["plan_stage"].value_counts().to_dict())
        ret_stage = sub[sub["plan_stage"] == "Retake"]
        print("  Inside plan_stage=='Retake':", ret_stage["positioning_state"].value_counts().to_dict())

    # Checar NPZ channels (has_c4 ch15, is_bomb_planted ch16, round_time ch17, speed, pos) em uma amostra de demos
    sample_demos = df["demo_id"].unique()[:20]
    sub_s = df[df["demo_id"].isin(sample_demos)]
    # Também pegar todos OBJECTIVE e SAVE de validation (ou até 500 de cada)
    val_rare = df[(df["split"] == "validation") & (df["positioning_state"].isin(["OBJECTIVE", "RETAKE", "SAVE"]))]
    
    npz_cache = {}
    def get_x(path):
        if path not in npz_cache:
            npz_cache[path] = np.load(path)["X"]
        return npz_cache[path]

    c4_counts = {"OBJECTIVE": 0, "RETAKE": 0, "SAVE": 0, "OTHER": 0}
    planted_counts = {"OBJECTIVE": 0, "RETAKE": 0, "SAVE": 0, "OTHER": 0}
    tot_counts = {"OBJECTIVE": 0, "RETAKE": 0, "SAVE": 0, "OTHER": 0}

    # Checar em 1000 amostras de cada tipo na validation
    for st in ["OBJECTIVE", "RETAKE", "SAVE"]:
        rows = val_rare[val_rare["positioning_state"] == st].head(500)
        xs = []
        for _, r in rows.iterrows():
            X = get_x(r["npz_path"])
            f = int(r["label_frame"])
            sl = int(r["slot"])
            vec = X[f, sl]
            xs.append(vec)
            tot_counts[st] += 1
            if vec[15] > 0.5:
                c4_counts[st] += 1
            if vec[16] > 0.5:
                planted_counts[st] += 1
        arr = np.array(xs)
        print(f"\nVal {st} (n={len(arr)}): has_c4={c4_counts[st]}, is_bomb_planted={planted_counts[st]}")
        print(f"  pos_x*4096 range=[{arr[:,0].min()*4096:.0f}, {arr[:,0].max()*4096:.0f}], pos_y*4096 range=[{arr[:,1].min()*4096:.0f}, {arr[:,1].max()*4096:.0f}]")
        print(f"  round_time*115 range=[{arr[:,17].min()*115:.1f}, {arr[:,17].max()*115:.1f}]")
        print(f"  is_terrorist(ch13) mean={arr[:,13].mean():.3f}, is_alive(ch14) mean={arr[:,14].mean():.3f}, weapon(ch11) mean={arr[:,11].mean():.3f}")
        print(f"  sectors: {rows['current_sector'].value_counts().to_dict()}")
        if st == "OBJECTIVE":
            print(f"  subtypes: {rows['objective_subtype'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()
