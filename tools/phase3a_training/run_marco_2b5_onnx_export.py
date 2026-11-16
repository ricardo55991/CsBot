#!/usr/bin/env python3
"""
Marco 2B.5: Exportação ONNX, Paridade Numérica/Decisão/Métrica e Performance.

Não treina, não altera pesos/thresholds/masks/labels, não copia para models/ ou src/.
"""
import gc
import hashlib
import json
import os
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import onnx
import onnxruntime as ort
import pandas as pd
import torch

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    STATE_NAMES,
    STATE_MAP,
    TRANSITION_NAMES,
    TRANSITION_MAP,
    EXIT_TRIGGER_NAMES,
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
from tools.phase3a_training.positioning_hybrid_runtime_wrapper import PositioningTransformerHybridRuntimeV1
from tools.phase3a_training.build_2b36_hierarchical_sidecar import compute_causal_eligibility_for_demo
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import (
    FastNPZStore,
    compute_multiclass_metrics,
    SELECTED_TRANSITION_THRESHOLD,
)

DS_DIR = BASE_DIR / "datasets" / "mirage_v2"
INDEX_DIR = DS_DIR / "positioning_v2_full_temporal"
BASE_SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_export"

CKPT_2B34 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
CKPT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "selected_checkpoint.pt"
CONTRACT_2B37 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hybrid_state_composition_v1" / "composition_contract.json"
CONTRACT_2B4 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "final_evaluation" / "final_evaluation_contract.json"

INPUT_NAMES = [
    "self_history",
    "teammates",
    "temporal_mask",
    "teammate_mask",
    "candidate_mask",
    "objective_eligible",
    "retake_eligible",
]
OUTPUT_NAMES = [
    "final_state_logits",
    "final_state_id",
    "sector_transition_logits",
    "sector_transition_id",
    "next_sector_logits",
    "next_sector_id",
    "spot_logits",
    "selected_spot_id",
    "transition_logits",
    "transition_id",
    "exit_trigger_logits",
    "exit_trigger_id",
    "confidence_by_head",
]


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
    except Exception:
        return "UNKNOWN"


def freeze_export_manifest() -> Dict[str, Any]:
    tracked = [
        CKPT_2B34,
        CKPT_2B36,
        CONTRACT_2B37,
        CONTRACT_2B4,
        BASE_DIR / "tools" / "phase3a_training" / "build_2b36_hierarchical_sidecar.py",
        BASE_DIR / "tools" / "phase3a_training" / "positioning_hybrid_runtime_wrapper.py",
        BASE_DIR / "tools" / "phase3a_training" / "canonical_v2_dataloader.py",
        BASE_DIR / "tools" / "phase3a_training" / "canonical_temporal_dataloader.py",
        INDEX_DIR / "supervised_spot_mask_v1.json",
        DS_DIR / "contracts" / "mirage_spot_catalog_v3.json",
    ]
    hashes = {str(p.relative_to(BASE_DIR)).replace("\\", "/"): compute_sha256(p) for p in tracked}
    snap = {
        "marco": "2B.5",
        "git_commit": get_git_commit(),
        "hashes": hashes,
        "training_executed": False,
        "runtime_integration_executed": False,
    }
    with open(OUT_DIR / "input_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)

    manifest = {
        "manifest_version": "2b5_export_manifest_v1",
        "frozen": True,
        "artifacts": hashes,
        "thresholds": {"sector_transition_occurs": SELECTED_TRANSITION_THRESHOLD},
        "save_policy": "NEURAL_SAVE_DISABLED_UTILITY_AI_FALLBACK",
    }
    with open(OUT_DIR / "positioning_export_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return snap


def build_parity_corpus(spot_to_idx: Dict[str, int], sup_mask_np: np.ndarray) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray], Dict[str, Any]]:
    """
    Seleciona deterministicamente 1.000 sequências do Test já avaliado cobrindo:
    - holdouts congelados (250)
    - casos com padding (label_frame < 31)
    - OBJECTIVE elegíveis
    - RETAKE elegíveis
    - spots supervisionados com candidate_mask restritiva
    """
    base_cols = [
        "sequence_id", "demo_id", "slot", "split", "label_frame", "npz_path",
        "positioning_state", "CandidateSpotId", "SpotLossMask", "transition", "plan_stage",
    ]
    v2_cols = ["sequence_id", "sector_transition_occurs", "next_sector", "next_sector_loss_mask"]
    parts = []
    for i in range(6):
        df_b = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=base_cols)
        m = df_b["split"] == "test"
        if not m.any():
            continue
        df_b = df_b[m].reset_index(drop=True)
        df_v2 = pd.read_parquet(BASE_SIDECAR_DIR / f"shard_{i:03d}_labels.parquet", columns=v2_cols)
        df_v2 = df_v2[m.to_numpy()].reset_index(drop=True)
        parts.append(pd.concat([df_b, df_v2.drop(columns=["sequence_id"])], axis=1))
    df_test = pd.concat(parts, ignore_index=True)

    # Carregar holdouts para garantir ~250 amostras deles
    holdout_demos = set()
    for hn in ["test_unseen_teams_v2.json", "test_unseen_players_v2.json", "test_unseen_events_v2.json", "test_recent_meta_v2.json"]:
        with open(DS_DIR / hn, "r", encoding="utf-8") as f:
            holdout_demos.update(json.load(f)["demo_ids"])

    # Calcular elegibilidade causal nas demos selecionáveis
    test_demos = df_test[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    store = FastNPZStore(test_demos)

    n = len(df_test)
    obj_elig = np.zeros(n, dtype=bool)
    ret_elig = np.zeros(n, dtype=bool)
    for demo_id, grp in df_test.groupby("demo_id", sort=False):
        res = compute_causal_eligibility_for_demo(
            X=store.arrays[demo_id],
            frames=grp["label_frame"].to_numpy(np.int64),
            slots=grp["slot"].to_numpy(np.int64),
            plan_stages=grp["plan_stage"].to_numpy(),
        )
        idx = grp.index.to_numpy()
        obj_elig[idx] = res["objective_eligible"]
        ret_elig[idx] = res["retake_eligible"]

    df_test["obj_elig"] = obj_elig
    df_test["ret_elig"] = ret_elig
    df_test["is_holdout"] = df_test["demo_id"].isin(holdout_demos)
    df_test["is_padding"] = df_test["label_frame"] < 31
    df_test["spot_idx"] = [spot_to_idx.get(s, -1) for s in df_test["CandidateSpotId"]]
    df_test["spot_elig"] = (df_test["SpotLossMask"] > 0.5) & (df_test["spot_idx"] >= 0)

    rng = np.random.default_rng(20260307)
    chosen_idx = []

    def take(mask_series, count):
        avail = df_test.index[mask_series].to_numpy()
        avail = np.setdiff1d(avail, np.array(chosen_idx, dtype=np.int64), assume_unique=False)
        k = min(count, len(avail))
        if k > 0:
            sel = rng.choice(avail, size=k, replace=False)
            chosen_idx.extend(sel.tolist())
        return k

    c_pad = take(df_test["is_padding"], 100)
    c_obj = take(df_test["obj_elig"], 150)
    c_ret = take(df_test["ret_elig"], 150)
    c_sp = take(df_test["spot_elig"], 250)
    c_ho = take(df_test["is_holdout"], 250)
    c_rest = take(pd.Series(True, index=df_test.index), 1000 - len(chosen_idx))

    sel_df = df_test.loc[chosen_idx].reset_index(drop=True)
    m_n = len(sel_df)

    hist, tm, tmask = store.extract_batch(
        sel_df["demo_id"].to_numpy(),
        sel_df["label_frame"].to_numpy(np.int64),
        sel_df["slot"].to_numpy(np.int64),
    )
    tmask_teammates = np.broadcast_to(tmask[:, :, None], (m_n, 32, 4)).copy()

    # Candidate mask: metade todas supervisionadas, metade restritivas (incluindo target + 5 spots aleatórios)
    cand_mask = np.broadcast_to(sup_mask_np[None, :], (m_n, 53)).copy()
    restrictive_flags = np.zeros(m_n, dtype=bool)
    sup_indices = np.where(sup_mask_np)[0]
    for i in range(m_n):
        if i % 2 == 1:
            restrictive_flags[i] = True
            cm = np.zeros(53, dtype=bool)
            tgt = int(sel_df.loc[i, "spot_idx"])
            if tgt >= 0 and sup_mask_np[tgt]:
                cm[tgt] = True
            picks = rng.choice(sup_indices, size=5, replace=False)
            cm[picks] = True
            cand_mask[i] = cm

    inputs = {
        "self_history": hist.astype(np.float32),
        "teammates": tm.astype(np.float32),
        "temporal_mask": tmask.astype(np.float32),
        "teammate_mask": tmask_teammates.astype(np.float32),
        "candidate_mask": cand_mask.astype(bool),
        "objective_eligible": sel_df["obj_elig"].to_numpy(bool),
        "retake_eligible": sel_df["ret_elig"].to_numpy(bool),
    }
    labels = {
        "y_state_true": np.array([STATE_MAP[s] for s in sel_df["positioning_state"]], dtype=np.int64),
        "y_sec_trans_true": np.array([SECTOR_TRANSITION_MAP.get(s, 0) for s in sel_df["sector_transition_occurs"]], dtype=np.int64),
        "y_next_sec_true": np.array([NEXT_SECTOR_MAP.get(s, 0) for s in sel_df["next_sector"]], dtype=np.int64),
        "next_sec_mask": sel_df["next_sector_loss_mask"].to_numpy(np.float32) > 0.5,
        "spot_targets": sel_df["spot_idx"].to_numpy(np.int64),
        "spot_elig_mask": (sel_df["spot_elig"].to_numpy(bool)) & (np.array([sup_mask_np[max(0, t)] for t in sel_df["spot_idx"]])),
        "y_trans_true": np.array([TRANSITION_MAP.get(s, 0) for s in sel_df["transition"]], dtype=np.int64),
    }
    manifest = {
        "total_sequences": m_n,
        "counts": {
            "padding_edge_cases": c_pad,
            "objective_eligible": c_obj,
            "retake_eligible": c_ret,
            "supervised_spots": c_sp,
            "holdout_sequences": c_ho,
            "remaining_test": c_rest,
            "restrictive_candidate_masks": int(restrictive_flags.sum()),
        },
        "provenance": "REAL",
    }
    with open(OUT_DIR / "parity_samples_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return inputs, labels, manifest


def benchmark_onnx_cpu(onnx_path: Path, sample_inputs: Dict[str, np.ndarray]) -> Dict[str, Any]:
    t_load0 = time.perf_counter()
    sess_opts = ort.SessionOptions()
    sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(str(onnx_path), sess_options=sess_opts, providers=["CPUExecutionProvider"])
    load_ms = (time.perf_counter() - t_load0) * 1000.0

    results = {"model_load_time_ms": round(load_ms, 3), "batches": {}}
    for bs in (1, 5, 10):
        feed = {k: v[:bs] for k, v in sample_inputs.items()}
        for _ in range(100):
            _ = sess.run(OUTPUT_NAMES, feed)

        gc.collect()
        tracemalloc.start()
        lat_ms = []
        for _ in range(2000):
            t0 = time.perf_counter()
            outs = sess.run(OUTPUT_NAMES, feed)
            lat_ms.append((time.perf_counter() - t0) * 1000.0)
        cur_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        arr = np.array(lat_ms, dtype=np.float64)
        out_bytes = sum(int(o.nbytes) for o in outs)
        mean_ms = float(np.mean(arr))
        results["batches"][str(bs)] = {
            "warmup_runs": 100,
            "measured_runs": 2000,
            "p50_ms": round(float(np.percentile(arr, 50)), 4),
            "p95_ms": round(float(np.percentile(arr, 95)), 4),
            "p99_ms": round(float(np.percentile(arr, 99)), 4),
            "mean_ms": round(mean_ms, 4),
            "throughput_seq_per_sec": round(bs / (mean_ms / 1000.0), 2),
            "peak_traced_ram_kb": round(peak_mem / 1024.0, 2),
            "output_allocations_bytes": out_bytes,
        }
    p95_b10 = results["batches"]["10"]["p95_ms"]
    results["batch_10_p95_target_ms"] = 20.0
    results["batch_10_meets_target"] = bool(p95_b10 <= 20.0)
    return results


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = freeze_export_manifest()

    sup_spot_mask = load_supervised_spot_mask()
    sup_mask_np = sup_spot_mask.numpy() > 0.5
    spot_ids, spot_to_idx = load_catalog(DS_DIR)

    # 1. Carregar modelos congelados e montar wrapper
    m34 = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask)
    m34.load_state_dict(torch.load(CKPT_2B34, map_location="cpu", weights_only=False)["model_state_dict"], strict=True)
    m36 = HierarchicalPositioningModel(PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask))
    m36.load_state_dict(torch.load(CKPT_2B36, map_location="cpu", weights_only=False)["model_state_dict"], strict=True)

    wrapper = PositioningTransformerHybridRuntimeV1(m34, m36, sector_transition_threshold=SELECTED_TRANSITION_THRESHOLD)
    wrapper.eval()

    # 2. Exportar ONNX (opset 18, do_constant_folding=True, batch dinâmico)
    onnx_path = OUT_DIR / "positioning_transformer_hybrid_v1.onnx"
    dummy = (
        torch.zeros(2, 32, 18, dtype=torch.float32),
        torch.zeros(2, 32, 4, 18, dtype=torch.float32),
        torch.ones(2, 32, dtype=torch.float32),
        torch.ones(2, 32, 4, dtype=torch.float32),
        torch.ones(2, 53, dtype=torch.bool),
        torch.zeros(2, dtype=torch.bool),
        torch.zeros(2, dtype=torch.bool),
    )
    dynamic_axes = {name: {0: "batch"} for name in INPUT_NAMES + OUTPUT_NAMES}

    with torch.no_grad():
        try:
            torch.onnx.export(
                wrapper,
                dummy,
                str(onnx_path),
                input_names=INPUT_NAMES,
                output_names=OUTPUT_NAMES,
                dynamic_axes=dynamic_axes,
                opset_version=18,
                do_constant_folding=True,
                dynamo=False,
            )
        except Exception:
            torch.onnx.export(
                wrapper,
                dummy,
                str(onnx_path),
                input_names=INPUT_NAMES,
                output_names=OUTPUT_NAMES,
                dynamic_axes=dynamic_axes,
                opset_version=18,
                do_constant_folding=True,
            )

    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)
    onnx_sha = compute_sha256(onnx_path)
    print(f"ONNX exportado e validado via onnx.checker (opset 18, sha256={onnx_sha[:16]}...).")

    # 3. Contrato de runtime (Seção 4)
    runtime_contract = {
        "contract_version": "positioning_runtime_contract_v1",
        "model_file": "positioning_transformer_hybrid_v1.onnx",
        "model_sha256": onnx_sha,
        "opset": 18,
        "fixed_dimensions": {"sequence_length": 32, "feature_count": 18, "teammate_slots": 4, "candidate_spots": 53},
        "dynamic_axes": {"batch": 0},
        "inputs": {
            "self_history": {"shape": ["batch", 32, 18], "dtype": "float32"},
            "teammates": {"shape": ["batch", 32, 4, 18], "dtype": "float32"},
            "temporal_mask": {"shape": ["batch", 32], "dtype": "float32"},
            "teammate_mask": {"shape": ["batch", 32, 4], "dtype": "float32"},
            "candidate_mask": {"shape": ["batch", 53], "dtype": "bool"},
            "objective_eligible": {"shape": ["batch"], "dtype": "bool"},
            "retake_eligible": {"shape": ["batch"], "dtype": "bool"},
        },
        "outputs": {
            "final_state_logits": {"shape": ["batch", 6], "dtype": "float32"},
            "final_state_id": {"shape": ["batch"], "dtype": "int64"},
            "sector_transition_logits": {"shape": ["batch", 2], "dtype": "float32"},
            "sector_transition_id": {"shape": ["batch"], "dtype": "int64"},
            "next_sector_logits": {"shape": ["batch", 5], "dtype": "float32"},
            "next_sector_id": {"shape": ["batch"], "dtype": "int64"},
            "spot_logits": {"shape": ["batch", 53], "dtype": "float32"},
            "selected_spot_id": {"shape": ["batch"], "dtype": "int64"},
            "transition_logits": {"shape": ["batch", 7], "dtype": "float32"},
            "transition_id": {"shape": ["batch"], "dtype": "int64"},
            "exit_trigger_logits": {"shape": ["batch", 8], "dtype": "float32"},
            "exit_trigger_id": {"shape": ["batch"], "dtype": "int64"},
            "confidence_by_head": {"shape": ["batch", 6], "dtype": "float32"},
        },
        "class_order": {
            "final_state": ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE"],
            "sector_transition": ["NO_TRANSITION", "TRANSITION_OCCURS"],
            "next_sector": ["A", "B", "MID", "CT", "T"],
            "transition": TRANSITION_NAMES,
            "exit_trigger": EXIT_TRIGGER_NAMES,
        },
        "normalization": "18 standardized channels per contract_spec.py (x/4096, y/4096, z/1024, v/250, yaw_cos/sin, pitch/90, hp/100, armor/100, weapon, role, is_tr, is_alive, has_c4, bomb_planted, rt/115)",
        "masking": "spot_logits masked with -1e9 outside (candidate_mask & supervised_spot_mask); rare overrides gated by objective_eligible & retake_eligible",
        "thresholds": {"sector_transition_occurs": SELECTED_TRANSITION_THRESHOLD},
        "state_precedence": ["OBJECTIVE (if objective_eligible)", "RETAKE (if retake_eligible)", "BaseState (2B.3.4)"],
        "spot_catalog_version": "mirage_spot_catalog_v3.json",
        "save_fallback_declaration": {"neural_save_disabled": True, "utility_ai_owns_save": True},
    }
    with open(OUT_DIR / "positioning_runtime_contract_v1.json", "w", encoding="utf-8") as f:
        json.dump(runtime_contract, f, indent=2, ensure_ascii=False)

    # 4. Corpus de paridade (1.000 sequências do Test)
    inputs, labels, _ = build_parity_corpus(spot_to_idx, sup_mask_np)
    with torch.inference_mode():
        pt_tuple = wrapper(*(torch.from_numpy(inputs[k]) for k in INPUT_NAMES))
    pt_outs = {name: t.cpu().numpy() for name, t in zip(OUTPUT_NAMES, pt_tuple)}
    np.savez_compressed(OUT_DIR / "pytorch_outputs.npz", **pt_outs)

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    ort_list = sess.run(OUTPUT_NAMES, inputs)
    onnx_outs = {name: arr for name, arr in zip(OUTPUT_NAMES, ort_list)}
    np.savez_compressed(OUT_DIR / "onnx_outputs.npz", **onnx_outs)

    # 5. Paridade numérica (Seção 7)
    logit_keys = [
        "final_state_logits", "sector_transition_logits", "next_sector_logits",
        "spot_logits", "transition_logits", "exit_trigger_logits", "confidence_by_head",
    ]
    num_parity = {"all_pass": True, "heads": {}}
    for k in logit_keys:
        diff = np.abs(pt_outs[k] - onnx_outs[k])
        max_err = float(np.max(diff))
        mean_err = float(np.mean(diff))
        ok = (max_err <= 1e-4) and (mean_err <= 1e-5)
        if not ok:
            num_parity["all_pass"] = False
        num_parity["heads"][k] = {"max_abs_error": max_err, "mean_abs_error": mean_err, "pass": ok}
    with open(OUT_DIR / "numerical_parity.json", "w", encoding="utf-8") as f:
        json.dump(num_parity, f, indent=2, ensure_ascii=False)

    # 6. Paridade de decisão & masks (Seção 7)
    dec_keys = [
        "final_state_id", "sector_transition_id", "next_sector_id",
        "selected_spot_id", "transition_id", "exit_trigger_id",
    ]
    dec_parity = {"all_pass": True, "agreements": {}, "mask_invariants": {}}
    for k in dec_keys:
        agr = float(np.mean(pt_outs[k] == onnx_outs[k]))
        ok = (agr == 1.0)
        if not ok:
            dec_parity["all_pass"] = False
        dec_parity["agreements"][k] = {"agreement": agr, "mismatches": int(np.sum(pt_outs[k] != onnx_outs[k])), "pass": ok}

    sel_sp = onnx_outs["selected_spot_id"]
    inv_masked = int(np.sum(~inputs["candidate_mask"][np.arange(len(sel_sp)), sel_sp]))
    unsup_sp = int(np.sum(~sup_mask_np[sel_sp]))
    obj_no_elig = int(np.sum((onnx_outs["final_state_id"] == 4) & (~inputs["objective_eligible"])))
    ret_no_elig = int(np.sum((onnx_outs["final_state_id"] == 5) & (~inputs["retake_eligible"])))
    neural_save = int(np.sum(onnx_outs["final_state_id"] == 6))

    invs = {
        "invalid_masked_spot_selection": inv_masked,
        "unsupported_spot_selection": unsup_sp,
        "objective_without_eligibility": obj_no_elig,
        "retake_without_eligibility": ret_no_elig,
        "neural_save_output": neural_save,
    }
    if any(v != 0 for v in invs.values()):
        dec_parity["all_pass"] = False
    dec_parity["mask_invariants"] = invs
    with open(OUT_DIR / "decision_parity.json", "w", encoding="utf-8") as f:
        json.dump(dec_parity, f, indent=2, ensure_ascii=False)

    # 7. Regressão métrica (Seção 9)
    def eval_metrics_from_outs(outs_dict):
        nm = labels["y_state_true"] != 6
        st_m = compute_multiclass_metrics(labels["y_state_true"][nm], outs_dict["final_state_id"][nm], STATE_NAMES[:6])
        sec_m = compute_multiclass_metrics(labels["y_sec_trans_true"], outs_dict["sector_transition_id"], ["NO_TRANSITION", "TRANSITION_OCCURS"])
        ns_mask = labels["next_sec_mask"]
        ns_m = compute_multiclass_metrics(labels["y_next_sec_true"][ns_mask], outs_dict["next_sector_id"][ns_mask], ["A", "B", "MID", "CT", "T"])
        tr_m = compute_multiclass_metrics(labels["y_trans_true"], outs_dict["transition_id"], TRANSITION_NAMES)

        sp_mask = labels["spot_elig_mask"]
        sp_l = outs_dict["spot_logits"][sp_mask]
        sp_t = labels["spot_targets"][sp_mask]
        order = np.argsort(-sp_l, axis=-1)
        ranks = np.array([int(np.where(order[i] == sp_t[i])[0][0]) + 1 for i in range(len(sp_t))])
        return {
            "state_macro_f1": st_m["macro_f1"],
            "balanced_accuracy": st_m["balanced_accuracy"],
            "spot_mrr": round(float(np.mean(1.0 / ranks)), 6),
            "spot_top1": round(float(np.mean(ranks == 1)), 6),
            "spot_top5": round(float(np.mean(ranks <= 5)), 6),
            "sector_transition_macro_f1": sec_m["macro_f1"],
            "next_sector_macro_f1": ns_m["macro_f1"],
            "transition_macro_f1": tr_m["macro_f1"],
        }

    pt_m = eval_metrics_from_outs(pt_outs)
    ox_m = eval_metrics_from_outs(onnx_outs)
    m_parity = {"all_pass": True, "metrics": {}}
    for k in pt_m:
        diff = abs(pt_m[k] - ox_m[k])
        ok = diff <= 1e-6
        if not ok:
            m_parity["all_pass"] = False
        m_parity["metrics"][k] = {"pytorch": pt_m[k], "onnx": ox_m[k], "abs_diff": diff, "pass": ok}
    with open(OUT_DIR / "metric_parity.json", "w", encoding="utf-8") as f:
        json.dump(m_parity, f, indent=2, ensure_ascii=False)

    # 8. Performance CPU (Seção 8)
    perf = benchmark_onnx_cpu(onnx_path, inputs)
    with open(OUT_DIR / "performance_metrics.json", "w", encoding="utf-8") as f:
        json.dump(perf, f, indent=2, ensure_ascii=False)

    print("\n=== MARCO 2B.5 EXPORTAÇÃO & PARIDADE CONCLUÍDOS ===")
    print(json.dumps({
        "numerical_parity_pass": num_parity["all_pass"],
        "decision_parity_pass": dec_parity["all_pass"],
        "metric_parity_pass": m_parity["all_pass"],
        "batch_10_p95_ms": perf["batches"]["10"]["p95_ms"],
        "batch_10_meets_target": perf["batch_10_meets_target"],
    }, indent=2))


if __name__ == "__main__":
    main()
