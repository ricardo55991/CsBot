#!/usr/bin/env python3
"""Audita e calibra regras determinísticas causais de elegibilidade (sem futuro) em Train e Validation."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
INDEX_DIR = BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"

# Centros aproximados dos bombsites de Mirage (unidades de mundo CS2):
# Vamos verificar as coordenadas reais dos PLANTING em A e B primeiro!
def main():
    cols = [
        "sequence_id", "demo_id", "split", "npz_path", "label_frame", "slot",
        "team", "plan_stage", "current_sector", "role", "positioning_state",
        "objective_subtype", "save_subtype"
    ]
    dfs = []
    for i in range(6):
        df = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=cols)
        df = df[df["split"] == "validation"].copy()
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    print(f"Validation total: {len(df)}")

    # Agrupar por demo_id para carregar cada NPZ uma única vez
    npz_cache = {}
    records = []
    for demo_id, grp in df.groupby("demo_id", sort=False):
        npz_path = grp["npz_path"].iloc[0]
        X = np.load(npz_path)["X"]  # [T, 10, 18]
        frames = grp["label_frame"].to_numpy(dtype=np.int64)
        slots = grp["slot"].to_numpy(dtype=np.int64)

        # Features no frame final f
        vec = X[frames, slots]  # [M, 18]
        pos_x = vec[:, 0] * 4096.0
        pos_y = vec[:, 1] * 4096.0
        vx = vec[:, 3] * 250.0
        vy = vec[:, 4] * 250.0
        speed = np.sqrt(vx**2 + vy**2)
        weapon = vec[:, 11]
        is_tr = vec[:, 13] > 0.5
        is_alive = vec[:, 14] > 0.5
        has_c4_now = vec[:, 15] > 0.5
        round_time = vec[:, 17] * 115.0

        # Checar se carregou C4 em qualquer frame da janela [max(0, f-31) .. f] (causal!)
        has_c4_win = np.zeros(len(frames), dtype=bool)
        for idx_r, (f, sl) in enumerate(zip(frames, slots)):
            s0 = max(0, f - 31)
            if np.any(X[s0:f+1, sl, 15] > 0.5):
                has_c4_win[idx_r] = True

        # Contagem de vivos por time no frame f (causal: estado atual de vida)
        all_tr = X[frames, :, 13] > 0.5     # [M, 10]
        all_alive = X[frames, :, 14] > 0.5  # [M, 10]
        n_tr_alive = np.sum(all_tr & all_alive, axis=1)
        n_ct_alive = np.sum((~all_tr) & all_alive, axis=1)
        own_alive = np.where(is_tr, n_tr_alive, n_ct_alive)
        enemy_alive = np.where(is_tr, n_ct_alive, n_tr_alive)

        # Algum aliado vivo carregando C4?
        c4_all = X[frames, :, 15] > 0.5
        any_c4_now = np.any(c4_all, axis=1)

        sub_df = grp[["positioning_state", "objective_subtype", "save_subtype", "plan_stage", "current_sector", "team", "role"]].copy()
        sub_df["pos_x"] = pos_x
        sub_df["pos_y"] = pos_y
        sub_df["vx"] = vx
        sub_df["vy"] = vy
        sub_df["speed"] = speed
        sub_df["weapon"] = weapon
        sub_df["is_tr"] = is_tr
        sub_df["is_alive"] = is_alive
        sub_df["has_c4_now"] = has_c4_now
        sub_df["has_c4_win"] = has_c4_win
        sub_df["any_c4_now"] = any_c4_now
        sub_df["round_time"] = round_time
        sub_df["own_alive"] = own_alive
        sub_df["enemy_alive"] = enemy_alive
        records.append(sub_df)

    res = pd.concat(records, ignore_index=True)

    # Descobrir centros de PLANTING em A e B
    for sec in ["A", "B"]:
        pl = res[(res["positioning_state"] == "OBJECTIVE") & (res["objective_subtype"] == "PLANTING") & (res["current_sector"] == sec)]
        if len(pl) > 0:
            print(f"PLANTING site {sec} (n={len(pl)}): mean=({pl['pos_x'].mean():.1f}, {pl['pos_y'].mean():.1f}), std=({pl['pos_x'].std():.1f}, {pl['pos_y'].std():.1f})")

    # Centros aproximados (A ~ (-450, -1950), B ~ (-2000, 350)) - calculados acima na hora
    ax = res[(res["positioning_state"] == "OBJECTIVE") & (res["current_sector"] == "A")]["pos_x"].median()
    ay = res[(res["positioning_state"] == "OBJECTIVE") & (res["current_sector"] == "A")]["pos_y"].median()
    bx = res[(res["positioning_state"] == "OBJECTIVE") & (res["current_sector"] == "B")]["pos_x"].median()
    by = res[(res["positioning_state"] == "OBJECTIVE") & (res["current_sector"] == "B")]["pos_y"].median()
    print(f"Site medians: A=({ax:.1f},{ay:.1f}), B=({bx:.1f},{by:.1f})")

    dist_a = np.sqrt((res["pos_x"] - ax)**2 + (res["pos_y"] - ay)**2)
    dist_b = np.sqrt((res["pos_x"] - bx)**2 + (res["pos_y"] - by)**2)
    min_site_dist = np.minimum(dist_a, dist_b)
    res["min_site_dist"] = min_site_dist

    # Direção de movimento em relação ao site mais próximo
    near_a = dist_a <= dist_b
    tx = np.where(near_a, ax, bx) - res["pos_x"]
    ty = np.where(near_a, ay, by) - res["pos_y"]
    tnorm = np.sqrt(tx**2 + ty**2) + 1e-6
    vnorm = res["speed"] + 1e-6
    cos_to_site = (res["vx"] * tx + res["vy"] * ty) / (vnorm * tnorm)
    res["cos_to_site"] = cos_to_site

    # Inspecionar características dos positivos de cada classe rara
    for st in ["OBJECTIVE", "RETAKE", "SAVE"]:
        s = res[res["positioning_state"] == st]
        print(f"\n--- Positives: {st} (N={len(s)}) ---")
        print(f"  has_c4_now={s['has_c4_now'].sum()}, has_c4_win={s['has_c4_win'].sum()}")
        print(f"  plan_stage=='Retake'={(s['plan_stage']=='Retake').sum()}")
        print(f"  min_site_dist quantiles: {s['min_site_dist'].quantile([0.1, 0.5, 0.9]).to_dict()}")
        print(f"  speed quantiles: {s['speed'].quantile([0.1, 0.5, 0.9]).to_dict()}")
        print(f"  round_time quantiles: {s['round_time'].quantile([0.1, 0.5, 0.9]).to_dict()}")
        print(f"  own_alive < enemy_alive: {(s['own_alive'] < s['enemy_alive']).sum()}/{len(s)}")
        print(f"  weapon >= 0.7: {(s['weapon'] >= 0.7).sum()}/{len(s)}")
        print(f"  cos_to_site > 0: {(s['cos_to_site'] > 0).sum()}/{len(s)}")
        print(f"  is_tr: {s['is_tr'].sum()}/{len(s)}")

    # Testar regras candidatas!
    def report(name, mask, target_state):
        elig = int(mask.sum())
        pos = int((mask & (res["positioning_state"] == target_state)).sum())
        tot_pos = int((res["positioning_state"] == target_state).sum())
        neg = elig - pos
        prec = pos / elig if elig > 0 else 0.0
        rec = pos / tot_pos if tot_pos > 0 else 0.0
        print(f"Rule [{name}] -> elig={elig}, pos={pos}/{tot_pos} (rec={rec:.4f}), neg={neg}, pot_prec={prec:.4f}")

    print("\n=== CANDIDATE RULES (VALIDATION) ===")
    # OBJECTIVE candidates
    report("OBJ_1: has_c4_win", res["has_c4_win"] & res["is_alive"], "OBJECTIVE")
    report("OBJ_2: has_c4_win OR (plan_stage=='Retake' & min_site_dist<450)",
           res["is_alive"] & (res["has_c4_win"] | ((res["plan_stage"] == "Retake") & (res["min_site_dist"] < 450))), "OBJECTIVE")
    report("OBJ_3: has_c4_win OR (plan_stage=='Retake' & min_site_dist<450 & ~is_tr)",
           res["is_alive"] & (res["has_c4_win"] | ((res["plan_stage"] == "Retake") & (res["min_site_dist"] < 450) & (~res["is_tr"]))), "OBJECTIVE")

    # SAVE candidates
    save_1 = res["is_alive"] & (res["own_alive"] < res["enemy_alive"]) & (res["round_time"] <= 35.0) & (res["min_site_dist"] >= 700.0) & (res["weapon"] >= 0.7)
    save_2 = save_1 & ((res["cos_to_site"] <= 0.1) | (res["speed"] < 80.0)) & (res["plan_stage"] == "Retake")
    report("SAVE_1: alive & disadv & rt<=35 & dist>=700 & weap>=0.7", save_1, "SAVE")
    report("SAVE_2: SAVE_1 & Retake & (away_or_slow)", save_2, "SAVE")

    # RETAKE candidates
    ret_1 = res["is_alive"] & (res["plan_stage"] == "Retake") & (~save_2)
    ret_2 = ret_1 & (res["min_site_dist"] >= 300.0) & (res["cos_to_site"] > 0.0)
    ret_3 = ret_1 & (res["min_site_dist"] >= 300.0) & (res["cos_to_site"] > 0.2) & (res["speed"] > 50.0)
    report("RET_1: alive & Retake & ~SAVE_2", ret_1, "RETAKE")
    report("RET_2: RET_1 & dist>=300 & cos>0", ret_2, "RETAKE")
    report("RET_3: RET_1 & dist>=300 & cos>0.2 & speed>50", ret_3, "RETAKE")

if __name__ == "__main__":
    main()
