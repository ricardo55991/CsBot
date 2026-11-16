#!/usr/bin/env python3
"""
Marco 2B.4: Avaliação Final Congelada do Positioning Transformer (Passagem Única no Test).

NÃO treina, NÃO ajusta thresholds, NÃO seleciona checkpoints, NÃO reage ao Test.
Executa uma única inferência canônica sobre o split `test` e gera todos os entregáveis
brutos e verificáveis da Seção 10.
"""
import hashlib
import json
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
    EXIT_TRIGGER_NAMES,
    EXIT_TRIGGER_MAP,
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
from tools.phase3a_training.hierarchical_positioning_model import HierarchicalPositioningModel
from tools.phase3a_training.build_2b36_hierarchical_sidecar import compute_causal_eligibility_for_demo
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import (
    FastNPZStore,
    compute_multiclass_metrics,
    SELECTED_TRANSITION_THRESHOLD,
)

DS_DIR = BASE_DIR / "datasets" / "mirage_v2"
INDEX_DIR = DS_DIR / "positioning_v2_full_temporal"
BASE_SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "final_evaluation"

CKPT_2B34 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
CKPT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "selected_checkpoint.pt"


def verify_frozen_snapshot() -> Dict[str, Any]:
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    with open(OUT_DIR / "pre_evaluation_test_result.json", "r", encoding="utf-8") as f:
        pre_t = json.load(f)
    if pre_t["passed"] != 16 or pre_t["failed"] != 0:
        raise RuntimeError("Pre-evaluation tests não estão 100% aprovados!")
    for rel_path, expected_sha in snap["hashes"].items():
        actual_sha = compute_sha256(BASE_DIR / rel_path)
        if actual_sha != expected_sha:
            raise RuntimeError(f"Hash divergente no snapshot congelado para {rel_path}!")
    return snap


def load_test_dataframe() -> pd.DataFrame:
    base_cols = [
        "sequence_id", "demo_id", "match_id", "round_id", "player_id", "slot", "split",
        "label_frame", "npz_path", "positioning_state", "CandidateSpotId",
        "SpotLossMask", "transition", "team", "role", "plan_stage", "provenance_type",
    ]
    v2_cols = [
        "sequence_id", "sector_transition_occurs", "next_sector",
        "next_sector_loss_mask", "exit_trigger",
    ]
    parts = []
    for i in range(6):
        df_b = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=base_cols)
        mask = df_b["split"] == "test"
        if not mask.any():
            continue
        df_b = df_b[mask].reset_index(drop=True)
        df_v2 = pd.read_parquet(BASE_SIDECAR_DIR / f"shard_{i:03d}_labels.parquet", columns=v2_cols)
        df_v2 = df_v2[mask.to_numpy()].reset_index(drop=True)
        assert (df_b["sequence_id"].to_numpy() == df_v2["sequence_id"].to_numpy()).all()
        parts.append(pd.concat([df_b, df_v2.drop(columns=["sequence_id"])], axis=1))
    return pd.concat(parts, ignore_index=True)


def compute_train_spot_support(spot_to_idx: Dict[str, int]) -> np.ndarray:
    counts = np.zeros(len(spot_to_idx), dtype=np.int64)
    for i in range(6):
        df = pd.read_parquet(
            INDEX_DIR / f"shard_{i:03d}.parquet",
            columns=["split", "SpotLossMask", "CandidateSpotId"],
        )
        m = (df["split"] == "train") & (df["SpotLossMask"] > 0.5)
        for sid, cnt in df.loc[m, "CandidateSpotId"].value_counts().items():
            idx = spot_to_idx.get(sid, -1)
            if idx >= 0:
                counts[idx] += int(cnt)
    return counts


def main():
    t0 = time.time()
    snap = verify_frozen_snapshot()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    sup_spot_mask = load_supervised_spot_mask()
    spot_ids, spot_to_idx = load_catalog(DS_DIR)
    train_spot_support = compute_train_spot_support(spot_to_idx)

    model_2b34 = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask).to(device)
    model_2b34.load_state_dict(torch.load(CKPT_2B34, map_location=device, weights_only=False)["model_state_dict"], strict=True)
    model_2b34.eval()

    model_2b36 = HierarchicalPositioningModel(PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask)).to(device)
    model_2b36.load_state_dict(torch.load(CKPT_2B36, map_location=device, weights_only=False)["model_state_dict"], strict=True)
    model_2b36.eval()

    print("Abrindo split Test (passagem única congelada)...")
    df_test = load_test_dataframe()
    n = len(df_test)
    print(f"Test carregado: {n} sequências em {df_test['demo_id'].nunique()} demos.")

    test_demos = df_test[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    test_store = FastNPZStore(test_demos)

    # Calcular máscaras causais determinísticas exatamente com a função congelada do Marco 2B.3.6
    obj_elig = np.zeros(n, dtype=bool)
    ret_elig = np.zeros(n, dtype=bool)
    for demo_id, grp in df_test.groupby("demo_id", sort=False):
        res = compute_causal_eligibility_for_demo(
            X=test_store.arrays[demo_id],
            frames=grp["label_frame"].to_numpy(np.int64),
            slots=grp["slot"].to_numpy(np.int64),
            plan_stages=grp["plan_stage"].to_numpy(),
        )
        idx = grp.index.to_numpy()
        obj_elig[idx] = res["objective_eligible"]
        ret_elig[idx] = res["retake_eligible"]

    elig_arr = np.stack([obj_elig, ret_elig, np.zeros(n, dtype=bool)], axis=1)

    demo_ids = df_test["demo_id"].to_numpy()
    frames = df_test["label_frame"].to_numpy(np.int64)
    slots = df_test["slot"].to_numpy(np.int64)
    team_ids = np.array([TEAM_MAP.get(t, 2) for t in df_test["team"]], dtype=np.int64)
    role_ids = np.array([ROLE_MAP.get(r, 0) for r in df_test["role"]], dtype=np.int64)
    stage_ids = np.array([STAGE_MAP.get(s, 0) for s in df_test["plan_stage"]], dtype=np.int64)

    y_state_true = np.array([STATE_MAP[s] for s in df_test["positioning_state"]], dtype=np.int64)
    y_sec_trans_true = np.array([SECTOR_TRANSITION_MAP.get(s, 0) for s in df_test["sector_transition_occurs"]], dtype=np.int64)
    y_next_sec_true = np.array([NEXT_SECTOR_MAP.get(s, 0) for s in df_test["next_sector"]], dtype=np.int64)
    next_sec_mask = df_test["next_sector_loss_mask"].to_numpy(np.float32) > 0.5
    y_trans_true = np.array([TRANSITION_MAP.get(s, 0) for s in df_test["transition"]], dtype=np.int64)
    y_trig_true = np.array([EXIT_TRIGGER_MAP.get(s, 0) for s in df_test["exit_trigger"]], dtype=np.int64)

    spot_loss_mask = df_test["SpotLossMask"].to_numpy(np.float32) > 0.5
    spot_targets = np.array([spot_to_idx.get(s, -1) for s in df_test["CandidateSpotId"]], dtype=np.int64)
    sup_mask_np = model_2b34.supervised_spot_mask.detach().cpu().numpy() > 0.5

    base_preds = np.zeros(n, dtype=np.int64)
    rare_preds = np.zeros(n, dtype=np.int64)
    y_sec_trans_pred = np.zeros(n, dtype=np.int64)
    y_next_sec_pred = np.zeros(n, dtype=np.int64)
    y_trans_pred = np.zeros(n, dtype=np.int64)
    y_trig_pred = np.zeros(n, dtype=np.int64)

    spot_top1_arr = np.zeros(n, dtype=np.int64)
    spot_rank_arr = np.zeros(n, dtype=np.int64)  # 1-based rank para elegíveis, 0 caso contrário

    bs = 512
    with torch.inference_mode():
        for start in range(0, n, bs):
            end = min(start + bs, n)
            hist, tm, tmask = test_store.extract_batch(demo_ids[start:end], frames[start:end], slots[start:end])
            hist_t = torch.from_numpy(hist).to(device)
            tm_t = torch.from_numpy(tm).to(device)
            tmask_t = torch.from_numpy(tmask).to(device)
            team_t = torch.from_numpy(team_ids[start:end]).to(device)
            role_t = torch.from_numpy(role_ids[start:end]).to(device)
            stage_t = torch.from_numpy(stage_ids[start:end]).to(device)
            elig_t = torch.from_numpy(elig_arr[start:end]).to(device)

            out34 = model_2b34(
                self_history=hist_t, teammates=tm_t, temporal_mask=tmask_t,
                team_idx=team_t, role_idx=role_t, stage_idx=stage_t,
            )
            base_preds[start:end] = torch.argmax(out34["logits_state"][:, :4], dim=-1).cpu().numpy()
            prob_st = F.softmax(out34["logits_transition_occurs"], dim=-1)[:, 1].cpu().numpy()
            y_sec_trans_pred[start:end] = (prob_st >= SELECTED_TRANSITION_THRESHOLD).astype(np.int64)
            y_next_sec_pred[start:end] = torch.argmax(out34["logits_next_sector"], dim=-1).cpu().numpy()
            y_trans_pred[start:end] = torch.argmax(out34["logits_transition"], dim=-1).cpu().numpy()
            y_trig_pred[start:end] = torch.argmax(out34["logits_trigger"], dim=-1).cpu().numpy()

            sp_logits = out34["logits_spot"].cpu().numpy()
            spot_top1_arr[start:end] = np.argmax(sp_logits, axis=-1)

            valid_sp = spot_loss_mask[start:end] & (spot_targets[start:end] >= 0) & sup_mask_np[np.maximum(0, spot_targets[start:end])]
            if valid_sp.any():
                sub_l = sp_logits[valid_sp]
                sub_t = spot_targets[start:end][valid_sp]
                order = np.argsort(-sub_l, axis=-1)
                ranks = np.array([int(np.where(order[r_i] == sub_t[r_i])[0][0]) + 1 for r_i in range(len(sub_t))], dtype=np.int64)
                spot_rank_arr[start:end][valid_sp] = ranks

            out36 = model_2b36(
                self_history=hist_t, teammates=tm_t, temporal_mask=tmask_t,
                team_idx=team_t, role_idx=role_t, stage_idx=stage_t,
                rare_eligibility_mask=elig_t,
            )
            rare_preds[start:end] = torch.argmax(out36["logits_rare_state"], dim=-1).cpu().numpy()

    # Composição final congelada (Seção 3: SAVE desativado)
    y_state_pred = base_preds.copy()
    y_state_pred = np.where((rare_preds == 2) & ret_elig, 5, y_state_pred)
    y_state_pred = np.where((rare_preds == 1) & obj_elig, 4, y_state_pred)

    # Salvar arrays brutos completos
    spot_elig_mask = spot_loss_mask & (spot_targets >= 0) & sup_mask_np[np.maximum(0, spot_targets)]
    np.savez_compressed(
        OUT_DIR / "raw_predictions.npz",
        y_state_true=y_state_true,
        y_state_pred=y_state_pred,
        y_sec_trans_true=y_sec_trans_true,
        y_sec_trans_pred=y_sec_trans_pred,
        y_next_sec_true=y_next_sec_true,
        y_next_sec_pred=y_next_sec_pred,
        next_sec_mask=next_sec_mask,
        spot_targets=spot_targets,
        spot_top1=spot_top1_arr,
        spot_rank=spot_rank_arr,
        spot_elig_mask=spot_elig_mask,
        y_trans_true=y_trans_true,
        y_trans_pred=y_trans_pred,
        y_trig_true=y_trig_true,
        y_trig_pred=y_trig_pred,
        obj_eligible=obj_elig,
        ret_eligible=ret_elig,
    )

    # Função para calcular métricas de estado neural (6 classes) mantendo SAVE separado
    def compute_neural_state_metrics(mask: np.ndarray) -> Dict[str, Any]:
        yt = y_state_true[mask]
        yp = y_state_pred[mask]
        neural_mask = yt != 6
        yt_n = yt[neural_mask]
        yp_n = yp[neural_mask]
        m6 = compute_multiclass_metrics(yt_n, yp_n, STATE_NAMES[:6])
        save_sup = int((yt == 6).sum())
        cm7 = np.zeros((7, 7), dtype=np.int64)
        np.add.at(cm7, (yt, yp), 1)
        m6["save_unserved_fallback"] = {
            "support": save_sup,
            "predicted": int((yp == 6).sum()),
            "precision": "N/A",
            "recall": "N/A",
            "f1": "N/A",
            "status": "NOT_APPLICABLE_RUNTIME_FALLBACK",
            "neural_predictions_on_save_rows": {STATE_NAMES[c]: int(cm7[6, c]) for c in range(6) if cm7[6, c] > 0},
        }
        m6["confusion_matrix_7x7"] = {"labels": STATE_NAMES, "matrix": cm7.tolist()}
        return m6

    all_mask = np.ones(n, dtype=bool)
    state_m = compute_neural_state_metrics(all_mask)
    sec_trans_m = compute_multiclass_metrics(y_sec_trans_true, y_sec_trans_pred, ["NO_TRANSITION", "TRANSITION_OCCURS"])
    next_sec_m = compute_multiclass_metrics(y_next_sec_true[next_sec_mask], y_next_sec_pred[next_sec_mask], ["A", "B", "MID", "CT", "T"])
    trans_m = compute_multiclass_metrics(y_trans_true, y_trans_pred, TRANSITION_NAMES)
    trig_m = compute_multiclass_metrics(y_trig_true, y_trig_pred, EXIT_TRIGGER_NAMES)

    # Spot ranking metrics (incluindo NDCG@5)
    elig_ranks = spot_rank_arr[spot_elig_mask]
    mrr = float(np.mean(1.0 / elig_ranks)) if len(elig_ranks) > 0 else 0.0
    top1 = float(np.mean(elig_ranks == 1)) if len(elig_ranks) > 0 else 0.0
    top3 = float(np.mean(elig_ranks <= 3)) if len(elig_ranks) > 0 else 0.0
    top5 = float(np.mean(elig_ranks <= 5)) if len(elig_ranks) > 0 else 0.0
    ndcg5 = float(np.mean(np.where(elig_ranks <= 5, 1.0 / np.log2(elig_ranks + 1.0), 0.0))) if len(elig_ranks) > 0 else 0.0
    invalid_masked = int((~sup_mask_np[spot_top1_arr]).sum())
    spot_m = {
        "eligible_count": int(spot_elig_mask.sum()),
        "mrr": round(mrr, 6),
        "top1": round(top1, 6),
        "top3": round(top3, 6),
        "top5": round(top5, 6),
        "ndcg5": round(ndcg5, 6),
        "invalid_masked_selection": invalid_masked,
        "unsupported_spot_selection": invalid_masked,
    }

    # Salvar JSONs individuais de métricas
    with open(OUT_DIR / "state_metrics.json", "w", encoding="utf-8") as f:
        json.dump(state_m, f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / "confusion_counts.json", "w", encoding="utf-8") as f:
        json.dump(state_m["confusion_matrix_7x7"], f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / "sector_transition_metrics.json", "w", encoding="utf-8") as f:
        json.dump(sec_trans_m, f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / "next_sector_metrics.json", "w", encoding="utf-8") as f:
        json.dump(next_sec_m, f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / "spot_ranking_metrics.json", "w", encoding="utf-8") as f:
        json.dump(spot_m, f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / "transition_metrics.json", "w", encoding="utf-8") as f:
        json.dump(trans_m, f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / "exit_trigger_metrics.json", "w", encoding="utf-8") as f:
        json.dump({**trig_m, "note": "Head F congelada; dependência causal de eventos futuros de round limita classes raras como BOMB_PLANTED/TACTIC_REVISION."}, f, indent=2, ensure_ascii=False)

    # Auditoria por spot (27 supervisionados + 26 sem supervisão)
    per_spot = []
    match_arr = df_test["match_id"].to_numpy()
    for idx, sid in enumerate(spot_ids):
        is_sup = bool(sup_mask_np[idx])
        if not is_sup:
            per_spot.append({
                "spot_id": sid,
                "supervised": False,
                "policy": "UTILITY_AI_ONLY",
                "train_support": int(train_spot_support[idx]),
                "test_support": 0,
                "mrr": "N/A",
                "top1": "N/A",
                "top5": "N/A",
                "tier": "UTILITY_AI_ONLY",
            })
            continue
        m_sp = spot_elig_mask & (spot_targets == idx)
        t_sup = int(m_sp.sum())
        if t_sup == 0:
            per_spot.append({
                "spot_id": sid, "supervised": True, "train_support": int(train_spot_support[idx]),
                "test_support": 0, "unique_matches": 0, "mrr": "N/A", "top1": "N/A", "top5": "N/A", "tier": "N/A_ZERO_TEST_SUPPORT",
            })
        else:
            rk = spot_rank_arr[m_sp]
            sp_mrr = float(np.mean(1.0 / rk))
            sp_t1 = float(np.mean(rk == 1))
            sp_t5 = float(np.mean(rk <= 5))
            tier = "WEAK_SUPPORT" if t_sup < 50 else ("STRONG" if sp_mrr >= 0.70 else "MODERATE")
            per_spot.append({
                "spot_id": sid, "supervised": True,
                "train_support": int(train_spot_support[idx]),
                "test_support": t_sup,
                "unique_matches": int(len(np.unique(match_arr[m_sp]))),
                "mrr": round(sp_mrr, 6), "top1": round(sp_t1, 6), "top5": round(sp_t5, 6), "tier": tier,
            })
    with open(OUT_DIR / "per_spot_metrics.json", "w", encoding="utf-8") as f:
        json.dump({"supervised_count": int(sup_mask_np.sum()), "unsupervised_count": int((~sup_mask_np).sum()), "spots": per_spot}, f, indent=2, ensure_ascii=False)

    # Holdouts de generalização congelados (Seção 5)
    holdout_names = ["test_unseen_teams_v2.json", "test_unseen_players_v2.json", "test_unseen_events_v2.json", "test_recent_meta_v2.json"]
    holdout_res = {}
    for hname in holdout_names:
        with open(DS_DIR / hname, "r", encoding="utf-8") as f:
            hdata = json.load(f)
        hdemos = set(hdata["demo_ids"])
        hmask = np.isin(demo_ids, list(hdemos))
        h_state = compute_neural_state_metrics(hmask)
        h_sp = spot_rank_arr[hmask & spot_elig_mask]
        holdout_res[hdata["split_name"]] = {
            "purpose": hdata.get("purpose", ""),
            "manifest_demo_count": len(hdemos),
            "evaluated_sequences": int(hmask.sum()),
            "supported_state_macro_f1": h_state["macro_f1"],
            "balanced_accuracy": h_state["balanced_accuracy"],
            "spot_mrr": round(float(np.mean(1.0 / h_sp)), 6) if len(h_sp) > 0 else "N/A",
            "spot_top5": round(float(np.mean(h_sp <= 5)), 6) if len(h_sp) > 0 else "N/A",
        }
    with open(OUT_DIR / "holdout_metrics.json", "w", encoding="utf-8") as f:
        json.dump(holdout_res, f, indent=2, ensure_ascii=False)

    # Gates finais (Seção 6 & 11)
    pc = state_m["per_class"]
    g_comp = (
        state_m["macro_f1"] >= 0.42 and state_m["balanced_accuracy"] >= 0.52
        and pc["TRANSIT"]["recall"] >= 0.75 and pc["CLEARANCE"]["recall"] >= 0.70
        and pc["STAGING"]["recall"] >= 0.20 and pc["HOLD"]["recall"] >= 0.35
        and pc["OBJECTIVE"]["precision"] >= 0.20 and pc["OBJECTIVE"]["recall"] >= 0.30 and pc["OBJECTIVE"]["f1"] >= 0.24
        and pc["RETAKE"]["precision"] >= 0.20 and pc["RETAKE"]["recall"] >= 0.30 and pc["RETAKE"]["f1"] >= 0.24
    )
    g_st = (
        sec_trans_m["macro_f1"] >= 0.55 and sec_trans_m["balanced_accuracy"] >= 0.55
        and sec_trans_m["per_class"]["TRANSITION_OCCURS"]["recall"] >= 0.30
        and sec_trans_m["per_class"]["NO_TRANSITION"]["recall"] >= 0.75
    )
    g_ns = next_sec_m["macro_f1"] >= 0.45 and next_sec_m["balanced_accuracy"] >= 0.45
    g_sp = mrr >= 0.72 and top1 >= 0.55 and top5 >= 0.92 and invalid_masked == 0
    g_tr = trans_m["macro_f1"] >= 0.55

    all_pass = g_comp and g_st and g_ns and g_sp and g_tr
    if all_pass:
        decision = "POSITIONING_TRANSFORMER_OFFLINE_APPROVED_WITH_SAVE_FALLBACK"
    elif (g_st and g_sp and g_tr) and (state_m["macro_f1"] >= 0.38):
        decision = "POSITIONING_TRANSFORMER_FINAL_EVALUATION_CONDITIONAL"
    else:
        decision = "POSITIONING_TRANSFORMER_FINAL_EVALUATION_FAILED"

    gen_summary = {
        "decision": decision,
        "gates": {
            "composite_neural": g_comp,
            "sector_transition": g_st,
            "next_sector": g_ns,
            "spot_ranking": g_sp,
            "transition": g_tr,
            "save_fallback_declared": True,
        },
        "test_sequences": n,
        "test_demos": int(df_test["demo_id"].nunique()),
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    with open(OUT_DIR / "generalization_summary.json", "w", encoding="utf-8") as f:
        json.dump(gen_summary, f, indent=2, ensure_ascii=False)

    # Reprodução matemática independente a partir de raw_predictions.npz
    raw = np.load(OUT_DIR / "raw_predictions.npz")
    repro_m = compute_multiclass_metrics(raw["y_state_true"][raw["y_state_true"] != 6], raw["y_state_pred"][raw["y_state_true"] != 6], STATE_NAMES[:6])
    repro = {
        "raw_npz_sha256": compute_sha256(OUT_DIR / "raw_predictions.npz"),
        "macro_f1_matches_exact": repro_m["macro_f1"] == state_m["macro_f1"],
        "balanced_acc_matches_exact": repro_m["balanced_accuracy"] == state_m["balanced_accuracy"],
        "spot_mrr_matches_exact": round(float(np.mean(1.0 / raw["spot_rank"][raw["spot_elig_mask"]])), 6) == spot_m["mrr"],
    }
    with open(OUT_DIR / "mathematical_reproduction.json", "w", encoding="utf-8") as f:
        json.dump(repro, f, indent=2, ensure_ascii=False)

    print("\n=== MARCO 2B.4 AVALIAÇÃO FINAL CONCLUÍDA ===")
    print(json.dumps(gen_summary, indent=2))


if __name__ == "__main__":
    main()
