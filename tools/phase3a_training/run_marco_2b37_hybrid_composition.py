#!/usr/bin/env python3
"""
Marco 2B.3.7: Composição Híbrida das Heads de Posicionamento (sem treinamento).

Combina:
1. BasePositioningState (TRANSIT, CLEARANCE, STAGING, HOLD) do checkpoint aprovado 2B.3.4
2. Overrides raros (OBJECTIVE, RETAKE) da RareTacticalStateHead hierárquica 2B.3.6 com elegibilidade causal
3. Política determinística offline candidata para SAVE

Avalia integralmente nas 501.434 sequências de Validation sem alterar pesos/checkpoints/shards.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    STATE_NAMES,
    STATE_MAP,
    TRANSITION_NAMES,
    TRANSITION_MAP,
    TEAM_MAP,
    ROLE_MAP,
    STAGE_MAP,
    compute_sha256,
)
from tools.phase3a_training.canonical_v2_dataloader import (
    SECTOR_TRANSITION_MAP,
    NEXT_SECTOR_MAP,
    load_supervised_spot_mask,
    load_catalog,
)
from tools.phase3a_training.positioning_model_v2 import PositioningTransformerV2RealTemporal
from tools.phase3a_training.hierarchical_positioning_model import (
    HierarchicalPositioningModel,
    RARE_STATE_NAMES,
)
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import (
    FastNPZStore,
    load_split_dataframe,
    compute_multiclass_metrics,
    SELECTED_TRANSITION_THRESHOLD,
    EXPECTED_BASE_SHA256,
)

CKPT_2B34 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
CKPT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "selected_checkpoint.pt"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hybrid_state_composition_v1"

SITE_A_XY = (-448.1, -2008.7)
SITE_B_XY = (-1978.0, 450.0)


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
    except Exception:
        return "UNKNOWN"


def compute_deterministic_save_rule(
    df_val: pd.DataFrame,
    val_store: FastNPZStore,
) -> np.ndarray:
    """
    Política determinística offline candidata para SAVE usando apenas sinais causais
    disponíveis no frame label_frame (sem futuro):
    - is_alive
    - plan_stage == 'Retake' (bomba plantada / pós-plant em curso)
    - own_alive < enemy_alive (desvantagem numérica)
    - round_time <= 22.0s (pouco tempo restante)
    - min_site_dist >= 650.0 (distância alta ao objetivo)
    - weapon >= 0.7 (valor relevante de equipamento)
    - cos_to_site <= 0.15 ou speed < 80.0 (afastamento ou preservação)
    """
    n = len(df_val)
    save_flag = np.zeros(n, dtype=bool)
    ax, ay = SITE_A_XY
    bx, by = SITE_B_XY

    for demo_id, grp in df_val.groupby("demo_id", sort=False):
        X = val_store.arrays[demo_id]
        f = grp["label_frame"].to_numpy(np.int64)
        sl = grp["slot"].to_numpy(np.int64)
        v = X[f, sl]

        px, py = v[:, 0] * 4096.0, v[:, 1] * 4096.0
        vx, vy = v[:, 3] * 250.0, v[:, 4] * 250.0
        spd = np.sqrt(vx**2 + vy**2)
        weap = v[:, 11]
        is_tr = v[:, 13] > 0.5
        is_alive = v[:, 14] > 0.5
        rt = v[:, 17] * 115.0

        da = np.sqrt((px - ax) ** 2 + (py - ay) ** 2)
        db = np.sqrt((px - bx) ** 2 + (py - by) ** 2)
        md = np.minimum(da, db)
        tx = np.where(da <= db, ax, bx) - px
        ty = np.where(da <= db, ay, by) - py
        cos_to_site = (vx * tx + vy * ty) / ((spd + 1e-6) * (np.sqrt(tx**2 + ty**2) + 1e-6))

        atr = X[f, :, 13] > 0.5
        aal = X[f, :, 14] > 0.5
        ntr = np.sum(atr & aal, axis=1)
        nct = np.sum((~atr) & aal, axis=1)
        own = np.where(is_tr, ntr, nct)
        ene = np.where(is_tr, nct, ntr)

        is_retake_stage = (grp["plan_stage"].to_numpy() == "Retake")
        rule = (
            is_alive
            & is_retake_stage
            & (own < ene)
            & (rt <= 22.0)
            & (md >= 650.0)
            & (weap >= 0.7)
            & ((cos_to_site <= 0.15) | (spd < 80.0))
        )
        save_flag[grp.index.to_numpy()] = rule
    return save_flag


def compose_hybrid_predictions(
    base_preds_4: np.ndarray,
    rare_preds_4: np.ndarray,
    obj_eligible: np.ndarray,
    ret_eligible: np.ndarray,
    save_rule: np.ndarray,
) -> np.ndarray:
    """
    Ordem canônica da Seção 3:
    1. se rare_state == OBJECTIVE (1) e objective_eligible -> OBJECTIVE (4)
    2. senão se rare_state == RETAKE (2) e retake_eligible -> RETAKE (5)
    3. senão se deterministic_save_rule -> SAVE (6)
    4. senão -> base_state (0..3)
    """
    final = base_preds_4.copy()
    is_save = save_rule
    is_ret = (rare_preds_4 == 2) & ret_eligible
    is_obj = (rare_preds_4 == 1) & obj_eligible

    final = np.where(is_save, 6, final)
    final = np.where(is_ret, 5, final)
    final = np.where(is_obj, 4, final)
    return final


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    sha_2b34 = compute_sha256(CKPT_2B34)
    sha_2b36 = compute_sha256(CKPT_2B36)
    if sha_2b34 != EXPECTED_BASE_SHA256:
        raise ValueError(f"SHA-256 de 2B.3.4 divergente: {sha_2b34}")

    # 1. Input snapshot & composition contract
    input_snapshot = {
        "marco": "2B.3.7",
        "git_commit": get_git_commit(),
        "base_2b34_checkpoint_path": str(CKPT_2B34.relative_to(BASE_DIR)).replace("\\", "/"),
        "base_2b34_checkpoint_sha256": sha_2b34,
        "hierarchical_2b36_checkpoint_path": str(CKPT_2B36.relative_to(BASE_DIR)).replace("\\", "/"),
        "hierarchical_2b36_checkpoint_sha256": sha_2b36,
        "protected_splits": ["test", "final_holdout"],
        "evaluated_split": "validation",
        "training_executed": False,
        "data_nature": "REAL",
    }
    with open(OUT_DIR / "input_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(input_snapshot, f, indent=2, ensure_ascii=False)

    contract = {
        "contract_version": "2b37_hybrid_v1",
        "composition_order": [
            "if rare_state == OBJECTIVE and objective_eligible -> OBJECTIVE",
            "elif rare_state == RETAKE and retake_eligible -> RETAKE",
            "elif deterministic_save_rule -> SAVE",
            "else -> base_state (argmax logits_state[:, :4] from 2B.3.4)",
        ],
        "base_states": ["TRANSIT", "CLEARANCE", "STAGING", "HOLD"],
        "rare_neural_overrides": ["OBJECTIVE", "RETAKE"],
        "save_policy": "deterministic_offline_candidate",
    }
    with open(OUT_DIR / "composition_contract.json", "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)

    # 2. Carregar modelos (somente inferência)
    sup_spot_mask = load_supervised_spot_mask()
    _, spot_to_idx = load_catalog(BASE_DIR / "datasets" / "mirage_v2")

    model_2b34 = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask).to(device)
    model_2b34.load_state_dict(torch.load(CKPT_2B34, map_location=device, weights_only=False)["model_state_dict"], strict=True)
    model_2b34.eval()

    model_2b36 = HierarchicalPositioningModel(PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask)).to(device)
    model_2b36.load_state_dict(torch.load(CKPT_2B36, map_location=device, weights_only=False)["model_state_dict"], strict=True)
    model_2b36.eval()

    # 3. Carregar Validation integral (501.434)
    print("Carregando Validation integral (501.434)...")
    df_val = load_split_dataframe("validation")
    # Adicionar match_id e provenance_type para contabilidade do SAVE
    extra_cols = []
    for i in range(6):
        df_ex = pd.read_parquet(
            BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal" / f"shard_{i:03d}.parquet",
            columns=["split", "match_id", "provenance_type"],
        )
        df_ex = df_ex[df_ex["split"] == "validation"].reset_index(drop=True)
        extra_cols.append(df_ex[["match_id", "provenance_type"]])
    df_extra = pd.concat(extra_cols, ignore_index=True)
    df_val["match_id"] = df_extra["match_id"]
    df_val["provenance_type"] = df_extra["provenance_type"]

    n = len(df_val)
    print(f"Validation carregada: {n} linhas. Pré-carregando NPZs...")
    val_demos = df_val[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    val_store = FastNPZStore(val_demos)

    # 4. Calcular regra determinística de SAVE
    save_rule = compute_deterministic_save_rule(df_val, val_store)

    # 5. Inferência em lote sobre 501.434 sequências
    demo_ids = df_val["demo_id"].to_numpy()
    frames = df_val["label_frame"].to_numpy(np.int64)
    slots = df_val["slot"].to_numpy(np.int64)
    team_ids = np.array([TEAM_MAP.get(t, 2) for t in df_val["team"]], dtype=np.int64)
    role_ids = np.array([ROLE_MAP.get(r, 0) for r in df_val["role"]], dtype=np.int64)
    stage_ids = np.array([STAGE_MAP.get(s, 0) for s in df_val["plan_stage"]], dtype=np.int64)

    obj_elig = df_val["objective_eligible"].to_numpy(bool)
    ret_elig = df_val["retake_eligible"].to_numpy(bool)
    sav_elig = df_val["save_eligible"].to_numpy(bool)
    elig_arr = np.stack([obj_elig, ret_elig, sav_elig], axis=1)

    y_true = np.array([STATE_MAP[s] for s in df_val["positioning_state"]], dtype=np.int64)
    y_sec_trans_true = np.array([SECTOR_TRANSITION_MAP.get(s, 0) for s in df_val["sector_transition_occurs"]], dtype=np.int64)
    y_next_sec_true = np.array([NEXT_SECTOR_MAP.get(s, 0) for s in df_val["next_sector"]], dtype=np.int64)
    next_sec_mask = df_val["next_sector_loss_mask"].to_numpy(np.float32) > 0.5
    y_trans_true = np.array([TRANSITION_MAP.get(s, 0) for s in df_val["transition"]], dtype=np.int64)
    spot_loss_mask = df_val["SpotLossMask"].to_numpy(np.float32) > 0.5
    spot_targets = np.array([spot_to_idx.get(s, -1) for s in df_val["CandidateSpotId"]], dtype=np.int64)

    base_preds = np.zeros(n, dtype=np.int64)
    rare_preds = np.zeros(n, dtype=np.int64)
    pred_sec_trans = np.zeros(n, dtype=np.int64)
    pred_next_sec = np.zeros(n, dtype=np.int64)
    pred_trans = np.zeros(n, dtype=np.int64)

    sup_mask_np = model_2b34.supervised_spot_mask.detach().cpu().numpy() > 0.5
    spot_mrr_sum = 0.0
    spot_top5_hits = 0
    spot_eval_count = 0
    invalid_masked_sel = 0

    bs = 512
    with torch.inference_mode():
        for start in range(0, n, bs):
            end = min(start + bs, n)
            hist, tm, tmask = val_store.extract_batch(demo_ids[start:end], frames[start:end], slots[start:end])
            hist_t = torch.from_numpy(hist).to(device)
            tm_t = torch.from_numpy(tm).to(device)
            tmask_t = torch.from_numpy(tmask).to(device)
            team_t = torch.from_numpy(team_ids[start:end]).to(device)
            role_t = torch.from_numpy(role_ids[start:end]).to(device)
            stage_t = torch.from_numpy(stage_ids[start:end]).to(device)
            elig_t = torch.from_numpy(elig_arr[start:end]).to(device)

            # 2B.3.4 aprovado -> Base states + Heads preservadas
            out34 = model_2b34(
                self_history=hist_t, teammates=tm_t, temporal_mask=tmask_t,
                team_idx=team_t, role_idx=role_t, stage_idx=stage_t,
            )
            base_preds[start:end] = torch.argmax(out34["logits_state"][:, :4], dim=-1).cpu().numpy()
            prob_st = F.softmax(out34["logits_transition_occurs"], dim=-1)[:, 1].cpu().numpy()
            pred_sec_trans[start:end] = (prob_st >= SELECTED_TRANSITION_THRESHOLD).astype(np.int64)
            pred_next_sec[start:end] = torch.argmax(out34["logits_next_sector"], dim=-1).cpu().numpy()
            pred_trans[start:end] = torch.argmax(out34["logits_transition"], dim=-1).cpu().numpy()

            sp_logits = out34["logits_spot"].cpu().numpy()
            top1 = np.argmax(sp_logits, axis=-1)
            invalid_masked_sel += int((~sup_mask_np[top1]).sum())
            valid_sp = spot_loss_mask[start:end] & (spot_targets[start:end] >= 0) & sup_mask_np[np.maximum(0, spot_targets[start:end])]
            if valid_sp.any():
                sub_l = sp_logits[valid_sp]
                sub_t = spot_targets[start:end][valid_sp]
                order = np.argsort(-sub_l, axis=-1)
                for r_i in range(len(sub_t)):
                    rk = int(np.where(order[r_i] == sub_t[r_i])[0][0]) + 1
                    spot_mrr_sum += 1.0 / rk
                    if rk <= 5:
                        spot_top5_hits += 1
                spot_eval_count += int(valid_sp.sum())

            # 2B.3.6 hierárquico -> Rare overrides (OBJECTIVE, RETAKE)
            out36 = model_2b36(
                self_history=hist_t, teammates=tm_t, temporal_mask=tmask_t,
                team_idx=team_t, role_idx=role_t, stage_idx=stage_t,
                rare_eligibility_mask=elig_t,
            )
            rare_preds[start:end] = torch.argmax(out36["logits_rare_state"], dim=-1).cpu().numpy()

    # 6. Composição híbrida determinística
    y_pred = compose_hybrid_predictions(base_preds, rare_preds, obj_elig, ret_elig, save_rule)

    # 7. Métricas + Confusion Matrix 7x7
    comp_metrics = compute_multiclass_metrics(y_true, y_pred, STATE_NAMES)
    cm = np.zeros((7, 7), dtype=np.int64)
    np.add.at(cm, (y_true, y_pred), 1)
    comp_metrics["confusion_matrix"] = {
        "labels": STATE_NAMES,
        "matrix": cm.tolist(),
    }

    sec_trans_metrics = compute_multiclass_metrics(y_sec_trans_true, pred_sec_trans, ["NO_TRANSITION", "TRANSITION_OCCURS"])
    next_sec_metrics = compute_multiclass_metrics(y_next_sec_true[next_sec_mask], pred_next_sec[next_sec_mask], ["A", "B", "MID", "CT", "T"])
    trans_metrics = compute_multiclass_metrics(y_trans_true, pred_trans, TRANSITION_NAMES)
    spot_mrr = round(spot_mrr_sum / spot_eval_count, 6) if spot_eval_count > 0 else 0.0
    spot_top5 = round(spot_top5_hits / spot_eval_count, 6) if spot_eval_count > 0 else 0.0

    full_val = {
        "evaluated_sequences": n,
        "composite_state": comp_metrics,
        "sector_transition": sec_trans_metrics,
        "next_sector": next_sec_metrics,
        "transition": trans_metrics,
        "spot_ranking": {
            "evaluated_count": spot_eval_count,
            "mrr": spot_mrr,
            "top5": spot_top5,
            "invalid_masked_selection": invalid_masked_sel,
        },
        "elapsed_seconds": round(time.time() - t0, 2),
        "data_nature": "REAL",
    }
    with open(OUT_DIR / "full_validation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(full_val, f, indent=2, ensure_ascii=False)

    # 8. Override accounting (false overrides / missed overrides)
    override_acc = {}
    for st_name, st_idx in [("OBJECTIVE", 4), ("RETAKE", 5), ("SAVE", 6)]:
        pred_m = (y_pred == st_idx)
        true_m = (y_true == st_idx)
        tp = int((pred_m & true_m).sum())
        fp = int((pred_m & (~true_m)).sum())
        fn = int(((~pred_m) & true_m).sum())
        override_acc[st_name] = {
            "actual_count": int(true_m.sum()),
            "predicted_count": int(pred_m.sum()),
            "true_positives": tp,
            "false_overrides": fp,
            "missed_overrides": fn,
            "false_override_breakdown_by_true_label": {
                STATE_NAMES[c]: int(((y_true == c) & pred_m).sum())
                for c in range(7) if c != st_idx and int(((y_true == c) & pred_m).sum()) > 0
            },
        }
    with open(OUT_DIR / "override_accounting.json", "w", encoding="utf-8") as f:
        json.dump(override_acc, f, indent=2, ensure_ascii=False)

    # 9. SAVE policy candidate evaluation (Seção 4)
    save_pred_m = (y_pred == 6)
    save_true_m = (y_true == 6)
    save_tp_df = df_val[save_pred_m & save_true_m]
    save_fp_df = df_val[save_pred_m & (~save_true_m)]
    save_true_df = df_val[save_true_m]

    def count_episodes(d: pd.DataFrame) -> int:
        if len(d) == 0:
            return 0
        s = d.sort_values(["demo_id", "round_id", "player_id", "label_frame"])
        ne = (
            (s["demo_id"] != s["demo_id"].shift(1))
            | (s["round_id"] != s["round_id"].shift(1))
            | (s["player_id"] != s["player_id"].shift(1))
            | ((s["label_frame"] - s["label_frame"].shift(1)) > 32)
        )
        return int(ne.cumsum().nunique())

    save_c = comp_metrics["per_class"]["SAVE"]
    save_policy = {
        "rule": "is_alive & plan_stage=='Retake' & (own_alive<enemy_alive) & (round_time<=22.0) & (min_site_dist>=650.0) & (weapon>=0.7) & ((cos_to_site<=0.15)|(speed<80.0))",
        "precision": save_c["precision"],
        "recall": save_c["recall"],
        "f1": save_c["f1"],
        "actual_sequences": int(save_true_m.sum()),
        "predicted_sequences": int(save_pred_m.sum()),
        "true_positives": int((save_pred_m & save_true_m).sum()),
        "false_positives": int((save_pred_m & (~save_true_m)).sum()),
        "actual_episodes": count_episodes(save_true_df),
        "tp_episodes": count_episodes(save_tp_df),
        "fp_episodes": count_episodes(save_fp_df),
        "unique_matches_actual": int(save_true_df["match_id"].nunique()),
        "unique_matches_tp": int(save_tp_df["match_id"].nunique()),
        "unique_matches_fp": int(save_fp_df["match_id"].nunique()),
        "provenance_actual": save_true_df["provenance_type"].value_counts().to_dict(),
        "provenance_predicted": df_val[save_pred_m]["provenance_type"].value_counts().to_dict(),
    }
    with open(OUT_DIR / "save_policy_candidate.json", "w", encoding="utf-8") as f:
        json.dump(save_policy, f, indent=2, ensure_ascii=False)

    # 10. Preservation & Gates (Seções 5, 6, 9)
    pc = comp_metrics["per_class"]
    comp_ok = comp_metrics["macro_f1"] >= 0.45 and comp_metrics["balanced_accuracy"] >= 0.52
    base_ok = (
        pc["TRANSIT"]["recall"] >= 0.75
        and pc["CLEARANCE"]["recall"] >= 0.75
        and pc["STAGING"]["recall"] >= 0.25
        and pc["HOLD"]["recall"] >= 0.40
    )
    obj_ok = pc["OBJECTIVE"]["precision"] >= 0.25 and pc["OBJECTIVE"]["recall"] >= 0.35 and pc["OBJECTIVE"]["f1"] >= 0.29
    ret_ok = pc["RETAKE"]["precision"] >= 0.25 and pc["RETAKE"]["recall"] >= 0.35 and pc["RETAKE"]["f1"] >= 0.29
    sav_ok = pc["SAVE"]["precision"] >= 0.20 and pc["SAVE"]["recall"] >= 0.20

    pres_ok = (
        spot_mrr >= 0.76
        and spot_top5 >= 0.955
        and invalid_masked_sel == 0
        and sec_trans_metrics["macro_f1"] >= 0.57
        and next_sec_metrics["macro_f1"] >= 0.48
        and trans_metrics["macro_f1"] >= 0.60
    )

    if not base_ok or not pres_ok:
        decision = "HYBRID_STATE_COMPOSITION_REGRESSION"
    elif obj_ok and ret_ok and sav_ok and comp_ok:
        decision = "POSITIONING_TRANSFORMER_READY_FOR_FINAL_EVALUATION"
    elif obj_ok and ret_ok and comp_ok:
        decision = "POSITIONING_TRANSFORMER_READY_WITH_SAVE_RUNTIME_FALLBACK"
    else:
        decision = "HYBRID_STATE_COMPOSITION_REGRESSION"

    pres_check = {
        "composite_gate_pass": comp_ok,
        "base_states_gate_pass": base_ok,
        "objective_gate_pass": obj_ok,
        "retake_gate_pass": ret_ok,
        "save_gate_pass": sav_ok,
        "save_status": "PASS" if sav_ok else "SAVE_RUNTIME_POLICY_REQUIRES_REFINEMENT",
        "preservation_gate_pass": pres_ok,
        "checkpoints_unchanged": (compute_sha256(CKPT_2B34) == sha_2b34 and compute_sha256(CKPT_2B36) == sha_2b36),
        "decision": decision,
    }
    with open(OUT_DIR / "preservation_check.json", "w", encoding="utf-8") as f:
        json.dump(pres_check, f, indent=2, ensure_ascii=False)

    print("\n=== MARCO 2B.3.7 CONCLUÍDO ===")
    print(json.dumps({"preservation_check": pres_check, "composite_macro_f1": comp_metrics["macro_f1"], "balanced_acc": comp_metrics["balanced_accuracy"]}, indent=2))


if __name__ == "__main__":
    main()
