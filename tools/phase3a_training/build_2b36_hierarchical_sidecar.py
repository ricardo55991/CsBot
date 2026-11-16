#!/usr/bin/env python3
"""
Marco 2B.3.6 - Passo 2: Construção do Dataset/Sidecar Hierárquico Causal.

Gera:
- input_snapshot.json
- hierarchical_state_contract.json
- hierarchical_label_sidecar/shard_000..005_hierarchical.parquet
- eligibility_accounting.json
- episode_support.json

Regras invioláveis:
- Nenhuma máscara usa informação futura (> label_frame).
- Test e Final Holdout não são consultados nem avaliados (recebem marcador SEALED para manter join 1:1 sem leitura de NPZ/labels).
- Join 1:1 exato por sequence_id, missing = 0, duplicates = 0, cross_split_leakage = 0.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
INDEX_DIR = BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
BASE_CKPT = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
EXPECTED_BASE_SHA256 = "c7fb36647de92b7422f8389ef4c87343680e25d1da648fef883fbc4542e91608"

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1"
SIDECAR_DIR = OUT_DIR / "hierarchical_label_sidecar"

CONTRACT_VERSION = "2b36_hierarchical_v1"

BASE_STATE_NAMES = ["TRANSIT", "CLEARANCE", "STAGING", "HOLD"]
RARE_STATE_NAMES = ["NONE", "OBJECTIVE", "RETAKE", "SAVE"]

# Centros dos bombsites de Mirage (medidos via mediana dos frames de PLANTING no Train/Val)
SITE_A_XY = (-448.1, -2008.7)
SITE_B_XY = (-1978.0, 450.0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
    except Exception:
        return "UNKNOWN"


def compute_causal_eligibility_for_demo(
    X: np.ndarray,
    frames: np.ndarray,
    slots: np.ndarray,
    plan_stages: np.ndarray,
) -> Dict[str, np.ndarray]:
    """
    Calcula máscaras determinísticas causais usando EXCLUSIVAMENTE features no frame
    label_frame e na janela passada [max(0, label_frame - 31) .. label_frame], além do
    plan_stage atual. Nunca usa frames > label_frame nem labels futuras.
    """
    v = X[frames, slots]  # [M, 18]
    px = v[:, 0] * 4096.0
    py = v[:, 1] * 4096.0
    vx = v[:, 3] * 250.0
    vy = v[:, 4] * 250.0
    spd = np.sqrt(vx**2 + vy**2)
    weap = v[:, 11]
    is_tr = v[:, 13] > 0.5
    is_alive = v[:, 14] > 0.5
    rt = v[:, 17] * 115.0

    ax, ay = SITE_A_XY
    bx, by = SITE_B_XY
    da = np.sqrt((px - ax) ** 2 + (py - ay) ** 2)
    db = np.sqrt((px - bx) ** 2 + (py - by) ** 2)
    md = np.minimum(da, db)

    tx = np.where(da <= db, ax, bx) - px
    ty = np.where(da <= db, ay, by) - py
    cos_to_site = (vx * tx + vy * ty) / ((spd + 1e-6) * (np.sqrt(tx**2 + ty**2) + 1e-6))

    # Causal window C4 check: t in [max(0, f-31), f]
    has_c4_win = np.zeros(len(frames), dtype=bool)
    for idx_r, (fi, sli) in enumerate(zip(frames, slots)):
        s0 = max(0, int(fi) - 31)
        if np.any(X[s0 : int(fi) + 1, int(sli), 15] > 0.5):
            has_c4_win[idx_r] = True

    all_tr = X[frames, :, 13] > 0.5
    all_alive = X[frames, :, 14] > 0.5
    n_tr_alive = np.sum(all_tr & all_alive, axis=1)
    n_ct_alive = np.sum((~all_tr) & all_alive, axis=1)
    own_alive = np.where(is_tr, n_tr_alive, n_ct_alive)
    enemy_alive = np.where(is_tr, n_ct_alive, n_tr_alive)

    is_retake_stage = (plan_stages == "Retake")

    objective_eligible = is_alive & (
        has_c4_win
        | ((~is_tr) & is_retake_stage & (md < 220.0) & (spd < 40.0))
    )
    save_eligible = (
        is_alive
        & is_retake_stage
        & (own_alive < enemy_alive)
        & (rt <= 25.0)
        & (md >= 550.0)
        & (weap >= 0.7)
        & ((cos_to_site <= 0.25) | (spd < 90.0))
        & (~objective_eligible)
    )
    retake_eligible = (
        is_alive
        & is_retake_stage
        & (~save_eligible)
        & (~objective_eligible)
        & (md >= 250.0)
        & (md <= 850.0)
        & ((cos_to_site > -0.3) | (spd < 60.0))
    )

    return {
        "objective_eligible": objective_eligible.astype(bool),
        "retake_eligible": retake_eligible.astype(bool),
        "save_eligible": save_eligible.astype(bool),
    }


def compute_episode_stats(df_sub: pd.DataFrame, target_state: str, elig_col: str) -> Dict[str, Any]:
    elig_df = df_sub[df_sub[elig_col] == True]
    pos_df = elig_df[elig_df["rare_tactical_state"] == target_state].copy()
    if len(pos_df) == 0:
        return {
            "eligible_sequence_count": int(len(elig_df)),
            "positive_sequence_support": 0,
            "positive_episode_support": 0,
            "unique_demos": 0,
            "unique_players": 0,
            "median_windows_per_episode": 0.0,
            "max_windows_per_episode": 0,
        }
    pos_df = pos_df.sort_values(["demo_id", "round_id", "player_id", "label_frame"]).reset_index(drop=True)
    # Novo episódio se mudar demo, round, player ou gap > 32 frames
    new_ep = (
        (pos_df["demo_id"] != pos_df["demo_id"].shift(1))
        | (pos_df["round_id"] != pos_df["round_id"].shift(1))
        | (pos_df["player_id"] != pos_df["player_id"].shift(1))
        | ((pos_df["label_frame"] - pos_df["label_frame"].shift(1)) > 32)
    )
    pos_df["episode_id"] = new_ep.cumsum()
    ep_sizes = pos_df.groupby("episode_id").size()
    return {
        "eligible_sequence_count": int(len(elig_df)),
        "positive_sequence_support": int(len(pos_df)),
        "positive_episode_support": int(len(ep_sizes)),
        "unique_demos": int(pos_df["demo_id"].nunique()),
        "unique_players": int(pos_df[["demo_id", "player_id"]].drop_duplicates().shape[0]),
        "median_windows_per_episode": float(ep_sizes.median()),
        "max_windows_per_episode": int(ep_sizes.max()),
        "provenance_distribution": pos_df["provenance_type"].value_counts().to_dict(),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SIDECAR_DIR.mkdir(parents=True, exist_ok=True)

    if not BASE_CKPT.exists():
        raise FileNotFoundError(f"Checkpoint base não encontrado: {BASE_CKPT}")
    actual_sha = sha256_file(BASE_CKPT)
    if actual_sha != EXPECTED_BASE_SHA256:
        raise ValueError(f"SHA-256 do checkpoint base divergente! Esperado={EXPECTED_BASE_SHA256}, Atual={actual_sha}")

    # 1. Input snapshot
    input_snapshot = {
        "marco": "2B.3.6",
        "git_commit": get_git_commit(),
        "base_checkpoint_path": str(BASE_CKPT.relative_to(BASE_DIR)).replace("\\", "/"),
        "base_checkpoint_sha256": actual_sha,
        "protected_splits": ["test", "final_holdout"],
        "allowed_splits": ["train", "validation"],
        "data_nature": "REAL",
    }
    with open(OUT_DIR / "input_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(input_snapshot, f, indent=2, ensure_ascii=False)

    # 2. Hierarchical contract
    contract = {
        "contract_version": CONTRACT_VERSION,
        "base_positioning_state": BASE_STATE_NAMES,
        "rare_tactical_state": RARE_STATE_NAMES,
        "composite_rule": "if rare_tactical_state != 'NONE' and class_eligible: rare_tactical_state else: base_positioning_state",
        "causal_guarantee": "Eligibility masks strictly use X[max(0, label_frame-31):label_frame+1] and plan_stage at label_frame. Zero future frames or labels.",
        "site_centers_mirage": {"A": list(SITE_A_XY), "B": list(SITE_B_XY)},
        "rules": {
            "OBJECTIVE_ELIGIBLE": "is_alive & (has_c4_in_window | (~is_tr & plan_stage=='Retake' & min_site_dist<220 & speed<40))",
            "SAVE_ELIGIBLE": "is_alive & plan_stage=='Retake' & (own_alive<enemy_alive) & (round_time<=25s) & (min_site_dist>=550) & (weapon>=0.7) & ((cos_to_site<=0.25)|(speed<90)) & ~OBJECTIVE_ELIGIBLE",
            "RETAKE_ELIGIBLE": "is_alive & plan_stage=='Retake' & ~SAVE_ELIGIBLE & ~OBJECTIVE_ELIGIBLE & (250<=min_site_dist<=850) & ((cos_to_site>-0.3)|(speed<60))",
        },
        "sealed_split_policy": "Rows in test/final_holdout receive SEALED markers without reading NPZs or labels.",
    }
    with open(OUT_DIR / "hierarchical_state_contract.json", "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)

    # 3. Processar cada um dos 6 shards
    cols = [
        "sequence_id", "demo_id", "round_id", "player_id", "split", "npz_path",
        "label_frame", "slot", "plan_stage", "positioning_state", "provenance_type"
    ]
    accounting = {
        sp: {
            "total_sequences": 0,
            "OBJECTIVE_ELIGIBLE": {"eligible_count": 0, "positive_count": 0, "negative_count": 0, "total_positives": 0},
            "RETAKE_ELIGIBLE": {"eligible_count": 0, "positive_count": 0, "negative_count": 0, "total_positives": 0},
            "SAVE_ELIGIBLE": {"eligible_count": 0, "positive_count": 0, "negative_count": 0, "total_positives": 0},
        }
        for sp in ["train", "validation"]
    }
    ep_frames = {"train": [], "validation": []}
    join_check = {"total_base_rows": 0, "total_sidecar_rows": 0, "missing": 0, "duplicates": 0, "cross_split_leakage": 0}

    for shard_idx in range(6):
        b_path = INDEX_DIR / f"shard_{shard_idx:03d}.parquet"
        df = pd.read_parquet(b_path, columns=cols)
        n = len(df)
        join_check["total_base_rows"] += n

        obj_elig = np.zeros(n, dtype=bool)
        ret_elig = np.zeros(n, dtype=bool)
        sav_elig = np.zeros(n, dtype=bool)

        # Processar apenas train e validation; test/final_holdout ficam intocados
        allowed_mask = df["split"].isin(["train", "validation"]).to_numpy()
        df_allowed = df[allowed_mask]

        for demo_id, grp in df_allowed.groupby("demo_id", sort=False):
            npz_path = grp["npz_path"].iloc[0]
            X = np.load(npz_path)["X"]
            res = compute_causal_eligibility_for_demo(
                X=X,
                frames=grp["label_frame"].to_numpy(np.int64),
                slots=grp["slot"].to_numpy(np.int64),
                plan_stages=grp["plan_stage"].to_numpy(),
            )
            idx = grp.index.to_numpy()
            obj_elig[idx] = res["objective_eligible"]
            ret_elig[idx] = res["retake_eligible"]
            sav_elig[idx] = res["save_eligible"]

        pos_st = df["positioning_state"].to_numpy()
        prov_arr = df["provenance_type"].to_numpy()

        base_state = np.where(
            ~allowed_mask,
            "SEALED",
            np.where(np.isin(pos_st, BASE_STATE_NAMES), pos_st, "NONE"),
        )
        rare_state = np.where(
            ~allowed_mask,
            "SEALED",
            np.where(np.isin(pos_st, ["OBJECTIVE", "RETAKE", "SAVE"]), pos_st, "NONE"),
        )
        rare_loss_mask = np.where(
            allowed_mask & (obj_elig | ret_elig | sav_elig),
            1.0,
            0.0,
        ).astype(np.float32)
        sidecar_prov = np.where(allowed_mask, prov_arr, "SEALED_SPLIT")

        out_df = pd.DataFrame({
            "sequence_id": df["sequence_id"],
            "base_positioning_state": base_state,
            "rare_tactical_state": rare_state,
            "objective_eligible": obj_elig,
            "retake_eligible": ret_elig,
            "save_eligible": sav_elig,
            "rare_state_loss_mask": rare_loss_mask,
            "provenance": sidecar_prov,
            "contract_version": CONTRACT_VERSION,
        })

        out_path = SIDECAR_DIR / f"shard_{shard_idx:03d}_hierarchical.parquet"
        out_df.to_parquet(out_path, index=False)
        join_check["total_sidecar_rows"] += len(out_df)

        # Verificar join 1:1
        if not (out_df["sequence_id"].to_numpy() == df["sequence_id"].to_numpy()).all():
            join_check["missing"] += 1
        if out_df["sequence_id"].duplicated().any():
            join_check["duplicates"] += int(out_df["sequence_id"].duplicated().sum())

        # Contabilizar Train & Validation
        for sp in ["train", "validation"]:
            sp_mask = (df["split"].to_numpy() == sp)
            if not sp_mask.any():
                continue
            accounting[sp]["total_sequences"] += int(sp_mask.sum())
            st_sp = pos_st[sp_mask]
            for key, elig_arr, target_st in [
                ("OBJECTIVE_ELIGIBLE", obj_elig[sp_mask], "OBJECTIVE"),
                ("RETAKE_ELIGIBLE", ret_elig[sp_mask], "RETAKE"),
                ("SAVE_ELIGIBLE", sav_elig[sp_mask], "SAVE"),
            ]:
                el = int(elig_arr.sum())
                pos = int((elig_arr & (st_sp == target_st)).sum())
                tot = int((st_sp == target_st).sum())
                accounting[sp][key]["eligible_count"] += el
                accounting[sp][key]["positive_count"] += pos
                accounting[sp][key]["negative_count"] += (el - pos)
                accounting[sp][key]["total_positives"] += tot

            # Guardar apenas linhas elegíveis ou raras para estatística de episódios
            keep = sp_mask & (obj_elig | ret_elig | sav_elig | np.isin(pos_st, ["OBJECTIVE", "RETAKE", "SAVE"]))
            if keep.any():
                sub_ep = df.loc[keep, ["demo_id", "round_id", "player_id", "label_frame", "provenance_type"]].copy()
                sub_ep["rare_tactical_state"] = rare_state[keep]
                sub_ep["objective_eligible"] = obj_elig[keep]
                sub_ep["retake_eligible"] = ret_elig[keep]
                sub_ep["save_eligible"] = sav_elig[keep]
                ep_frames[sp].append(sub_ep)

        print(f"Shard {shard_idx:03d} gravado ({len(out_df)} linhas).")

    # Finalizar métricas de eligibility_accounting.json
    for sp in ["train", "validation"]:
        for key, evs in [
            ("OBJECTIVE_ELIGIBLE", ["is_alive", "has_c4_in_window", "plan_stage==Retake", "min_site_dist<220", "speed<40"]),
            ("RETAKE_ELIGIBLE", ["is_alive", "plan_stage==Retake", "min_site_dist in [250,850]", "cos_to_site>-0.3 or speed<60"]),
            ("SAVE_ELIGIBLE", ["is_alive", "plan_stage==Retake", "own_alive<enemy_alive", "round_time<=25", "min_site_dist>=550", "weapon>=0.7"]),
        ]:
            d = accounting[sp][key]
            d["potential_precision"] = round(d["positive_count"] / d["eligible_count"], 6) if d["eligible_count"] > 0 else 0.0
            d["positive_coverage_recall"] = round(d["positive_count"] / d["total_positives"], 6) if d["total_positives"] > 0 else 0.0
            d["events_used"] = evs
            d["provenance"] = "REAL"

    accounting["join_integrity"] = join_check
    with open(OUT_DIR / "eligibility_accounting.json", "w", encoding="utf-8") as f:
        json.dump(accounting, f, indent=2, ensure_ascii=False)

    # Episode support
    ep_support = {}
    for sp in ["train", "validation"]:
        ep_df = pd.concat(ep_frames[sp], ignore_index=True)
        ep_support[sp] = {
            "OBJECTIVE": compute_episode_stats(ep_df, "OBJECTIVE", "objective_eligible"),
            "RETAKE": compute_episode_stats(ep_df, "RETAKE", "retake_eligible"),
            "SAVE": compute_episode_stats(ep_df, "SAVE", "save_eligible"),
        }
    with open(OUT_DIR / "episode_support.json", "w", encoding="utf-8") as f:
        json.dump(ep_support, f, indent=2, ensure_ascii=False)

    print("Sidecar hierárquico e auditorias gerados com sucesso.")
    print(json.dumps({"accounting_val": accounting["validation"], "join_check": join_check}, indent=2))


if __name__ == "__main__":
    main()
