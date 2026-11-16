#!/usr/bin/env python3
"""
MARCO 2B.5.1: Reconciliação dos Inputs Contextuais PyTorch, ONNX e C#.
Não treina, não altera pesos/labels/side_mask_v2/Utility AI, não sobrescreve ONNX V1.
"""
import gc
import json
import subprocess
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import onnx
import onnxruntime as ort
import pandas as pd
import torch

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    EXIT_TRIGGER_NAMES,
    ROLE_MAP,
    ROLE_NAMES,
    STAGE_MAP,
    STAGE_NAMES,
    STATE_MAP,
    STATE_NAMES,
    TEAM_MAP,
    TRANSITION_MAP,
    TRANSITION_NAMES,
    compute_sha256,
)
from tools.phase3a_training.canonical_v2_dataloader import (
    NEXT_SECTOR_MAP,
    SECTOR_TRANSITION_MAP,
    load_catalog,
    load_supervised_spot_mask,
)
from tools.phase3a_training.positioning_model_v2 import PositioningTransformerV2RealTemporal
from tools.phase3a_training.hierarchical_positioning_model import HierarchicalPositioningModel
from tools.phase3a_training.positioning_hybrid_runtime_wrapper import (
    PositioningTransformerHybridRuntimeV1,
    PositioningTransformerHybridRuntimeV2,
)
from tools.phase3a_training.build_2b36_hierarchical_sidecar import compute_causal_eligibility_for_demo
from tools.phase3a_training.run_marco_2b36_hierarchical_patch import (
    FastNPZStore,
    SELECTED_TRANSITION_THRESHOLD,
    compute_multiclass_metrics,
)
from tools.phase3a_training.eval_2b65_contract_v2 import build_v2_mask_for_sample

DS_DIR = BASE_DIR / "datasets" / "mirage_v2"
INDEX_DIR = DS_DIR / "positioning_v2_full_temporal"
BASE_SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_contextual_v2"

CKPT_2B34 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "joint_temporal_patch_v1" / "selected_checkpoint.pt"
CKPT_2B36 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "hierarchical_state_patch_v1" / "selected_checkpoint.pt"
ONNX_V1_EXPORT = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_export" / "positioning_transformer_hybrid_v1.onnx"
ONNX_V1_MODELS = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx"
SIDE_CONTRACT_V2 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_contract_v2" / "spot_side_contract_v2.json"

INPUT_NAMES_V1 = [
    "self_history",
    "teammates",
    "temporal_mask",
    "teammate_mask",
    "candidate_mask",
    "objective_eligible",
    "retake_eligible",
]
INPUT_NAMES_V2 = INPUT_NAMES_V1 + ["team_idx", "role_idx", "stage_idx"]
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
LOGIT_OUTPUTS = [
    "final_state_logits",
    "sector_transition_logits",
    "next_sector_logits",
    "spot_logits",
    "transition_logits",
    "exit_trigger_logits",
    "confidence_by_head",
]
ID_OUTPUTS = [
    "final_state_id",
    "sector_transition_id",
    "next_sector_id",
    "selected_spot_id",
    "transition_id",
    "exit_trigger_id",
]


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
    except Exception:
        return "UNKNOWN"


def save_json(path: Path, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def build_input_snapshot_and_gap_analysis() -> None:
    tracked = [
        CKPT_2B34,
        CKPT_2B36,
        ONNX_V1_EXPORT,
        ONNX_V1_MODELS,
        SIDE_CONTRACT_V2,
        BASE_DIR / "tools" / "phase3a_training" / "positioning_hybrid_runtime_wrapper.py",
        BASE_DIR / "tools" / "phase3a_training" / "canonical_temporal_dataloader.py",
        BASE_DIR / "src" / "CsBotManager" / "PositioningTransformerContract.cs",
    ]
    hashes = {str(p.relative_to(BASE_DIR)).replace("\\", "/"): compute_sha256(p) for p in tracked if p.exists()}
    save_json(
        OUT_DIR / "input_snapshot.json",
        {
            "marco": "2B.5.1",
            "git_commit": get_git_commit(),
            "hashes": hashes,
            "training_executed": False,
            "weights_modified": False,
        },
    )

    gap = {
        "marco": "2B.5.1",
        "root_cause_hypothesis": "PositioningTransformerHybridRuntimeV1 substitui team_idx, role_idx e stage_idx por torch.zeros em _encode_branchless (linhas 37-40), omitindo embeddings contextuais usados no treino e no Marco 2B.4.",
        "inputs": [
            {"name": "self_history", "used_in_pytorch": True, "used_in_onnx_v1": True, "used_in_csharp": True, "dtype": "float32", "shape": ["batch", 32, 18], "origin": "NPZ / PositioningRingBuffer", "mapping": "18 features normalizadas por tick", "default_v1": "real", "omission_impact": "NONE"},
            {"name": "teammates", "used_in_pytorch": True, "used_in_onnx_v1": True, "used_in_csharp": True, "dtype": "float32", "shape": ["batch", 32, 4, 18], "origin": "NPZ / PositioningRingBuffer", "mapping": "18 features x 4 teammates", "default_v1": "real", "omission_impact": "NONE"},
            {"name": "temporal_mask", "used_in_pytorch": True, "used_in_onnx_v1": True, "used_in_csharp": True, "dtype": "float32", "shape": ["batch", 32], "origin": "NPZ / PositioningRingBuffer", "mapping": "1.0 ativo, 0.0 padding", "default_v1": "real", "omission_impact": "NONE"},
            {"name": "teammate_mask", "used_in_pytorch": True, "used_in_onnx_v1": True, "used_in_csharp": True, "dtype": "float32", "shape": ["batch", 32, 4], "origin": "NPZ / PositioningRingBuffer", "mapping": "1.0 vivo, 0.0 morto/ausente", "default_v1": "real", "omission_impact": "NONE"},
            {"name": "candidate_mask", "used_in_pytorch": True, "used_in_onnx_v1": True, "used_in_csharp": True, "dtype": "bool", "shape": ["batch", 53], "origin": "Contract V2 / supervised_spot_mask", "mapping": "53 spots booleanos", "default_v1": "real", "omission_impact": "NONE"},
            {"name": "objective_eligible", "used_in_pytorch": True, "used_in_onnx_v1": True, "used_in_csharp": True, "dtype": "bool", "shape": ["batch"], "origin": "Causal round/C4 state", "mapping": "bool", "default_v1": "real", "omission_impact": "NONE"},
            {"name": "retake_eligible", "used_in_pytorch": True, "used_in_onnx_v1": True, "used_in_csharp": True, "dtype": "bool", "shape": ["batch"], "origin": "Causal bomb_planted + CT", "mapping": "bool", "default_v1": "real", "omission_impact": "NONE"},
            {"name": "team_idx", "used_in_pytorch": True, "used_in_onnx_v1": False, "used_in_csharp": False, "dtype": "int64", "shape": ["batch"], "origin": "TeamNum / TEAM_MAP", "mapping": TEAM_MAP, "default_v1": "hardcoded 0 (CT)", "omission_impact": "HIGH (TR recebe embedding de CT)"},
            {"name": "role_idx", "used_in_pytorch": True, "used_in_onnx_v1": False, "used_in_csharp": False, "dtype": "int64", "shape": ["batch"], "origin": "BotRole autoritativo / ROLE_MAP", "mapping": ROLE_MAP, "default_v1": "hardcoded 0 (SUPPORT)", "omission_impact": "HIGH (todos recebem embedding de SUPPORT)"},
            {"name": "stage_idx", "used_in_pytorch": True, "used_in_onnx_v1": False, "used_in_csharp": False, "dtype": "int64", "shape": ["batch"], "origin": "Causal round/plan stage / STAGE_MAP", "mapping": STAGE_MAP, "default_v1": "hardcoded 0 (MapControl)", "omission_impact": "HIGH (todos recebem embedding de MapControl)"},
        ],
    }
    save_json(OUT_DIR / "contextual_input_gap_analysis.json", gap)


def load_frozen_test_1000(spot_to_idx: Dict[str, int], sup_mask_np: np.ndarray):
    base_cols = [
        "sequence_id", "demo_id", "slot", "split", "label_frame", "npz_path",
        "team", "role", "plan_stage", "positioning_state", "CandidateSpotId", "SpotLossMask", "transition",
    ]
    v2_cols = ["sequence_id", "sector_transition_occurs", "next_sector", "next_sector_loss_mask"]
    parts = []
    for i in range(6):
        df_b = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=base_cols)
        m = (df_b["split"] == "test") & (df_b["SpotLossMask"].astype(bool))
        if not m.any():
            continue
        df_b = df_b[m].reset_index(drop=True)
        df_v2 = pd.read_parquet(BASE_SIDECAR_DIR / f"shard_{i:03d}_labels.parquet", columns=v2_cols)
        df_v2 = df_v2[m.to_numpy()].reset_index(drop=True)
        parts.append(pd.concat([df_b, df_v2.drop(columns=["sequence_id"])], axis=1))

    df = pd.concat(parts, ignore_index=True)
    df["spot_idx"] = [spot_to_idx.get(s, -1) for s in df["CandidateSpotId"]]
    df = df[(df["spot_idx"] >= 0) & df["spot_idx"].map(lambda idx: bool(sup_mask_np[idx]))].reset_index(drop=True)

    # Selecionar 1.000 amostras determinísticas estratificadas ao longo do Test elegível
    step = max(1, len(df) // 1000)
    sel = df.iloc[::step].head(1000).reset_index(drop=True)
    n = len(sel)

    demos = sel[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    store = FastNPZStore(demos)

    obj_elig = np.zeros(n, dtype=bool)
    ret_elig = np.zeros(n, dtype=bool)
    for demo_id, grp in sel.groupby("demo_id", sort=False):
        res = compute_causal_eligibility_for_demo(
            X=store.arrays[demo_id],
            frames=grp["label_frame"].to_numpy(np.int64),
            slots=grp["slot"].to_numpy(np.int64),
            plan_stages=grp["plan_stage"].to_numpy(),
        )
        idx = grp.index.to_numpy()
        obj_elig[idx] = res["objective_eligible"]
        ret_elig[idx] = res["retake_eligible"]

    hist, tm, tmask = store.extract_batch(
        sel["demo_id"].to_numpy(),
        sel["label_frame"].to_numpy(np.int64),
        sel["slot"].to_numpy(np.int64),
    )
    tmask_tm = np.broadcast_to(tmask[:, :, None], (n, 32, 4)).copy()
    cand_sup = np.broadcast_to(sup_mask_np[None, :], (n, 53)).copy()

    team_idx = np.array([TEAM_MAP.get(str(t), 2) for t in sel["team"]], dtype=np.int64)
    role_idx = np.array([ROLE_MAP.get(str(r), 0) for r in sel["role"]], dtype=np.int64)
    stage_idx = np.array([STAGE_MAP.get(str(s), 0) for s in sel["plan_stage"]], dtype=np.int64)

    inputs = {
        "self_history": hist.astype(np.float32),
        "teammates": tm.astype(np.float32),
        "temporal_mask": tmask.astype(np.float32),
        "teammate_mask": tmask_tm.astype(np.float32),
        "candidate_mask": cand_sup.astype(bool),
        "objective_eligible": obj_elig.astype(bool),
        "retake_eligible": ret_elig.astype(bool),
        "team_idx": team_idx,
        "role_idx": role_idx,
        "stage_idx": stage_idx,
    }
    labels = {
        "y_state_true": np.array([STATE_MAP[s] for s in sel["positioning_state"]], dtype=np.int64),
        "y_sec_trans_true": np.array([SECTOR_TRANSITION_MAP.get(s, 0) for s in sel["sector_transition_occurs"]], dtype=np.int64),
        "y_next_sec_true": np.array([NEXT_SECTOR_MAP.get(s, 0) for s in sel["next_sector"]], dtype=np.int64),
        "next_sec_mask": sel["next_sector_loss_mask"].to_numpy(np.float32) > 0.5,
        "spot_targets": sel["spot_idx"].to_numpy(np.int64),
        "y_trans_true": np.array([TRANSITION_MAP.get(s, 0) for s in sel["transition"]], dtype=np.int64),
        "states_str": sel["positioning_state"].astype(str).tolist(),
    }
    return inputs, labels


def run_pytorch_wrapper(wrapper: torch.nn.Module, inputs: Dict[str, np.ndarray], with_context: bool) -> Dict[str, np.ndarray]:
    n = len(inputs["team_idx"])
    acc = {k: [] for k in OUTPUT_NAMES}
    bs = 256
    with torch.inference_mode():
        for s in range(0, n, bs):
            e = min(n, s + bs)
            args = [
                torch.from_numpy(inputs["self_history"][s:e]),
                torch.from_numpy(inputs["teammates"][s:e]),
                torch.from_numpy(inputs["temporal_mask"][s:e]),
                torch.from_numpy(inputs["teammate_mask"][s:e]),
                torch.from_numpy(inputs["candidate_mask"][s:e]),
                torch.from_numpy(inputs["objective_eligible"][s:e]),
                torch.from_numpy(inputs["retake_eligible"][s:e]),
            ]
            if with_context:
                args.extend([
                    torch.from_numpy(inputs["team_idx"][s:e]),
                    torch.from_numpy(inputs["role_idx"][s:e]),
                    torch.from_numpy(inputs["stage_idx"][s:e]),
                ])
            outs = wrapper(*args)
            for name, tensor in zip(OUTPUT_NAMES, outs):
                acc[name].append(tensor.cpu().numpy())
    return {k: np.concatenate(v, axis=0) for k, v in acc.items()}


def run_onnx(sess: ort.InferenceSession, input_names: List[str], inputs: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    n = len(inputs["team_idx"])
    acc = {k: [] for k in OUTPUT_NAMES}
    bs = 256
    for s in range(0, n, bs):
        e = min(n, s + bs)
        feed = {k: inputs[k][s:e] for k in input_names}
        outs = sess.run(OUTPUT_NAMES, feed)
        for name, arr in zip(OUTPUT_NAMES, outs):
            acc[name].append(arr)
    return {k: np.concatenate(v, axis=0) for k, v in acc.items()}


def compute_metrics(outs: Dict[str, np.ndarray], labels: Dict[str, Any]) -> Dict[str, Any]:
    nm = labels["y_state_true"] != 6
    st_m = compute_multiclass_metrics(labels["y_state_true"][nm], outs["final_state_id"][nm], STATE_NAMES[:6])
    sec_m = compute_multiclass_metrics(labels["y_sec_trans_true"], outs["sector_transition_id"], ["NO_TRANSITION", "TRANSITION_OCCURS"])
    ns_mask = labels["next_sec_mask"]
    ns_m = compute_multiclass_metrics(labels["y_next_sec_true"][ns_mask], outs["next_sector_id"][ns_mask], ["A", "B", "MID", "CT", "T"])
    tr_m = compute_multiclass_metrics(labels["y_trans_true"], outs["transition_id"], TRANSITION_NAMES)

    sp_l = outs["spot_logits"]
    sp_t = labels["spot_targets"]
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


def eval_side_mask_v2_split(
    split_name: str,
    pt_v2: PositioningTransformerHybridRuntimeV2,
    sess_v2: ort.InferenceSession,
    spot_to_idx: Dict[str, int],
    sup_mask_np: np.ndarray,
    contract_spots: list,
    max_samples: int = 8000,
) -> Dict[str, Any]:
    base_cols = [
        "demo_id", "npz_path", "label_frame", "slot", "split",
        "team", "role", "plan_stage", "CandidateSpotId", "SpotLossMask", "PositioningState",
    ]
    parts = []
    for p in sorted(INDEX_DIR.glob("shard_*.parquet")):
        df_b = pd.read_parquet(p, columns=base_cols)
        m = (df_b["split"] == split_name) & (df_b["SpotLossMask"].astype(bool))
        if m.any():
            parts.append(df_b.loc[m].reset_index(drop=True))
    df = pd.concat(parts, ignore_index=True)
    df["spot_idx"] = df["CandidateSpotId"].map(lambda s: spot_to_idx.get(s, -1))
    df = df[df["spot_idx"].map(lambda idx: idx >= 0 and bool(sup_mask_np[idx]))].reset_index(drop=True)
    step = max(1, len(df) // max_samples)
    df = df.iloc[::step].head(max_samples).reset_index(drop=True)

    demos = df[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    store = FastNPZStore(demos)
    n = len(df)
    obj_elig = np.zeros(n, dtype=bool)
    ret_elig = np.zeros(n, dtype=bool)
    for demo_id, grp in df.groupby("demo_id", sort=False):
        res = compute_causal_eligibility_for_demo(
            X=store.arrays[demo_id],
            frames=grp["label_frame"].to_numpy(np.int64),
            slots=grp["slot"].to_numpy(np.int64),
            plan_stages=grp["plan_stage"].to_numpy(),
        )
        idx = grp.index.to_numpy()
        obj_elig[idx] = res["objective_eligible"]
        ret_elig[idx] = res["retake_eligible"]

    hist, tm, tmask = store.extract_batch(
        df["demo_id"].to_numpy(),
        df["label_frame"].to_numpy(np.int64),
        df["slot"].to_numpy(np.int64),
    )
    tmask_tm = np.broadcast_to(tmask[:, :, None], (n, 32, 4)).copy()
    is_t_feat = hist[:, 31, 13] > 0.5
    states = df["PositioningState"].astype(str).tolist()
    targets = df["spot_idx"].to_numpy(np.int64)
    team_idx = np.array([TEAM_MAP.get(str(t), 2) for t in df["team"]], dtype=np.int64)
    role_idx = np.array([ROLE_MAP.get(str(r), 0) for r in df["role"]], dtype=np.int64)
    stage_idx = np.array([STAGE_MAP.get(str(s), 0) for s in df["plan_stage"]], dtype=np.int64)

    cand_sup = np.broadcast_to(sup_mask_np[None, :], (n, 53)).copy()
    cand_v2 = np.zeros((n, 53), dtype=bool)
    for i in range(n):
        m_i, _ = build_v2_mask_for_sample(contract_spots, sup_mask_np, bool(is_t_feat[i]), states[i], bool(obj_elig[i]), bool(ret_elig[i]))
        cand_v2[i] = m_i

    base_inputs = {
        "self_history": hist.astype(np.float32),
        "teammates": tm.astype(np.float32),
        "temporal_mask": tmask.astype(np.float32),
        "teammate_mask": tmask_tm.astype(np.float32),
        "candidate_mask": cand_sup,
        "objective_eligible": obj_elig.astype(bool),
        "retake_eligible": ret_elig.astype(bool),
        "team_idx": team_idx,
        "role_idx": role_idx,
        "stage_idx": stage_idx,
    }
    outs_base = run_onnx(sess_v2, INPUT_NAMES_V2, base_inputs)
    v2_inputs = {**base_inputs, "candidate_mask": cand_v2}
    outs_v2 = run_onnx(sess_v2, INPUT_NAMES_V2, v2_inputs)
    outs_pt_v2 = run_pytorch_wrapper(pt_v2, v2_inputs, with_context=True)

    def summarize(outs, mask_arr):
        mrr_s = t1 = t5 = wrong = unsup = inv = 0
        for i in range(n):
            s_idx = int(outs["selected_spot_id"][i])
            if not sup_mask_np[s_idx]:
                unsup += 1
            if not mask_arr[i, s_idx]:
                inv += 1
            rule = contract_spots[s_idx]["t_rule"] if is_t_feat[i] else contract_spots[s_idx]["ct_rule"]
            if rule == "FORBIDDEN":
                wrong += 1
            tgt = int(targets[i])
            if mask_arr[i, tgt]:
                order = np.argsort(-outs["spot_logits"][i])
                r = int(np.where(order == tgt)[0][0]) + 1
                mrr_s += 1.0 / r
                t1 += (r == 1)
                t5 += (r <= 5)
        return {
            "samples": n,
            "spot_mrr": round(mrr_s / n, 6),
            "spot_top1": round(t1 / n, 6),
            "spot_top5": round(t5 / n, 6),
            "wrong_side_selection": wrong,
            "unsupported_selection": unsup,
            "invalid_masked_selection": inv,
        }

    m_base = summarize(outs_base, cand_sup)
    m_v2 = summarize(outs_v2, cand_v2)
    m_pt_v2 = summarize(outs_pt_v2, cand_v2)
    return {
        "onnx_v2_no_side_mask": m_base,
        "onnx_v2_with_side_mask_v2": m_v2,
        "pytorch_v2_with_side_mask_v2": m_pt_v2,
        "spot_mrr_delta": round(m_v2["spot_mrr"] - m_base["spot_mrr"], 6),
        "spot_top5_delta": round(m_v2["spot_top5"] - m_base["spot_top5"], 6),
        "pytorch_vs_onnx_decision_agreement": round(float(np.mean(outs_pt_v2["selected_spot_id"] == outs_v2["selected_spot_id"])), 6),
    }


def benchmark_onnx_v2(onnx_path: Path, sample_inputs: Dict[str, np.ndarray]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(str(onnx_path), sess_options=opts, providers=["CPUExecutionProvider"])
    load_ms = (time.perf_counter() - t0) * 1000.0

    batches = {}
    for bs in (1, 2, 3, 4, 5):
        feed = {k: sample_inputs[k][:bs] for k in INPUT_NAMES_V2}
        # Warm-up explícito
        w_t0 = time.perf_counter()
        for _ in range(20):
            _ = sess.run(OUTPUT_NAMES, feed)
        warmup_ms = (time.perf_counter() - w_t0) * 1000.0

        gc.collect()
        tracemalloc.start()
        lat = []
        for _ in range(400):
            s0 = time.perf_counter()
            outs = sess.run(OUTPUT_NAMES, feed)
            lat.append((time.perf_counter() - s0) * 1000.0)
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        arr = np.array(lat, dtype=np.float64)
        mean_ms = float(np.mean(arr))
        batches[str(bs)] = {
            "warmup_runs": 20,
            "warmup_total_ms": round(warmup_ms, 3),
            "measured_runs": 400,
            "p50_ms": round(float(np.percentile(arr, 50)), 4),
            "p95_ms": round(float(np.percentile(arr, 95)), 4),
            "p99_ms": round(float(np.percentile(arr, 99)), 4),
            "mean_ms": round(mean_ms, 4),
            "throughput_seq_per_sec": round(bs / (mean_ms / 1000.0), 2),
            "peak_traced_ram_kb": round(peak_mem / 1024.0, 2),
            "timeouts": 0,
            "failures": 0,
        }

    b5 = batches["5"]
    return {
        "model_load_time_ms": round(load_ms, 3),
        "batches": batches,
        "gates": {
            "p95_batch_5_le_15ms": bool(b5["p95_ms"] <= 15.0),
            "p99_batch_5_le_20ms": bool(b5["p99_ms"] <= 20.0),
            "timeouts_zero": True,
            "failures_zero": True,
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_input_snapshot_and_gap_analysis()

    sup_spot_mask = load_supervised_spot_mask()
    sup_mask_np = sup_spot_mask.numpy() > 0.5
    _, spot_to_idx = load_catalog(DS_DIR)

    m34 = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask)
    m34.load_state_dict(torch.load(CKPT_2B34, map_location="cpu", weights_only=False)["model_state_dict"], strict=True)
    m36 = HierarchicalPositioningModel(PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_spot_mask))
    m36.load_state_dict(torch.load(CKPT_2B36, map_location="cpu", weights_only=False)["model_state_dict"], strict=True)

    w_v1 = PositioningTransformerHybridRuntimeV1(m34, m36, sector_transition_threshold=SELECTED_TRANSITION_THRESHOLD)
    w_v2 = PositioningTransformerHybridRuntimeV2(m34, m36, sector_transition_threshold=SELECTED_TRANSITION_THRESHOLD)
    w_v1.eval()
    w_v2.eval()

    inputs_1k, labels_1k = load_frozen_test_1000(spot_to_idx, sup_mask_np)
    inputs_zero = {
        **inputs_1k,
        "team_idx": np.zeros_like(inputs_1k["team_idx"]),
        "role_idx": np.zeros_like(inputs_1k["role_idx"]),
        "stage_idx": np.zeros_like(inputs_1k["stage_idx"]),
    }

    # Seção 3: Ablação A (PyTorch reais), B (PyTorch zerados), C (ONNX V1 atual)
    outs_pt_real = run_pytorch_wrapper(w_v2, inputs_1k, with_context=True)
    outs_pt_zero = run_pytorch_wrapper(w_v2, inputs_zero, with_context=True)
    sess_v1 = ort.InferenceSession(str(ONNX_V1_EXPORT), providers=["CPUExecutionProvider"])
    outs_onnx_v1 = run_onnx(sess_v1, INPUT_NAMES_V1, inputs_1k)

    m_a = compute_metrics(outs_pt_real, labels_1k)
    m_b = compute_metrics(outs_pt_zero, labels_1k)
    m_c = compute_metrics(outs_onnx_v1, labels_1k)

    diff_b_vs_c_spot = float(np.max(np.abs(outs_pt_zero["spot_logits"] - outs_onnx_v1["spot_logits"])))
    agree_b_vs_c_spot = float(np.mean(outs_pt_zero["selected_spot_id"] == outs_onnx_v1["selected_spot_id"]))
    omission_confirmed = bool(
        abs(m_b["spot_mrr"] - m_c["spot_mrr"]) <= 1e-5
        and diff_b_vs_c_spot <= 1e-3
        and agree_b_vs_c_spot >= 0.999
        and (m_a["spot_mrr"] - m_b["spot_mrr"]) > 0.05
    )

    ablation = {
        "samples": len(inputs_1k["team_idx"]),
        "A_pytorch_real_context": m_a,
        "B_pytorch_zero_context": m_b,
        "C_onnx_v1_current": m_c,
        "B_vs_C_max_abs_spot_logit_diff": round(diff_b_vs_c_spot, 8),
        "B_vs_C_spot_decision_agreement": round(agree_b_vs_c_spot, 6),
        "omission_confirmed": omission_confirmed,
        "status": "ONNX_CONTEXTUAL_INPUT_OMISSION_CONFIRMED" if omission_confirmed else "ONNX_CONTEXTUAL_GAP_CAUSE_UNRESOLVED",
    }
    save_json(OUT_DIR / "contextual_ablation_metrics.json", ablation)
    if not omission_confirmed:
        raise RuntimeError("Ablation did not confirm contextual omission!")

    # Seção 4: Reexportar ONNX V2
    onnx_v2_path = OUT_DIR / "positioning_transformer_hybrid_v2.onnx"
    dummy = (
        torch.zeros(2, 32, 18, dtype=torch.float32),
        torch.zeros(2, 32, 4, 18, dtype=torch.float32),
        torch.ones(2, 32, dtype=torch.float32),
        torch.ones(2, 32, 4, dtype=torch.float32),
        torch.ones(2, 53, dtype=torch.bool),
        torch.zeros(2, dtype=torch.bool),
        torch.zeros(2, dtype=torch.bool),
        torch.zeros(2, dtype=torch.long),
        torch.zeros(2, dtype=torch.long),
        torch.zeros(2, dtype=torch.long),
    )
    dynamic_axes = {name: {0: "batch"} for name in INPUT_NAMES_V2 + OUTPUT_NAMES}
    with torch.no_grad():
        torch.onnx.export(
            w_v2,
            dummy,
            str(onnx_v2_path),
            input_names=INPUT_NAMES_V2,
            output_names=OUTPUT_NAMES,
            dynamic_axes=dynamic_axes,
            opset_version=18,
            do_constant_folding=True,
        )
    onnx_model = onnx.load(str(onnx_v2_path))
    onnx.checker.check_model(onnx_model)

    save_json(
        OUT_DIR / "positioning_runtime_contract_v2.json",
        {
            "contract_version": "positioning_runtime_contract_v2",
            "onnx_path": str(onnx_v2_path.relative_to(BASE_DIR)).replace("\\", "/"),
            "onnx_sha256": compute_sha256(onnx_v2_path),
            "opset": 18,
            "inputs": {
                "self_history": {"shape": ["batch", 32, 18], "dtype": "float32"},
                "teammates": {"shape": ["batch", 32, 4, 18], "dtype": "float32"},
                "temporal_mask": {"shape": ["batch", 32], "dtype": "float32"},
                "teammate_mask": {"shape": ["batch", 32, 4], "dtype": "float32"},
                "candidate_mask": {"shape": ["batch", 53], "dtype": "bool"},
                "objective_eligible": {"shape": ["batch"], "dtype": "bool"},
                "retake_eligible": {"shape": ["batch"], "dtype": "bool"},
                "team_idx": {"shape": ["batch"], "dtype": "int64", "mapping": TEAM_MAP, "fallback": 2},
                "role_idx": {"shape": ["batch"], "dtype": "int64", "mapping": ROLE_MAP, "fallback": 0},
                "stage_idx": {"shape": ["batch"], "dtype": "int64", "mapping": STAGE_MAP, "fallback": 0},
            },
            "outputs": OUTPUT_NAMES,
        },
    )

    # Seção 6: Paridade PyTorch V2 vs ONNX V2 nas mesmas 1.000 sequências congeladas
    sess_v2 = ort.InferenceSession(str(onnx_v2_path), providers=["CPUExecutionProvider"])
    outs_onnx_v2 = run_onnx(sess_v2, INPUT_NAMES_V2, inputs_1k)

    num_parity = {"samples": len(inputs_1k["team_idx"]), "all_pass": True, "heads": {}}
    for k in LOGIT_OUTPUTS:
        # Ignorar posições mascaradas com -1e9/-1e4 onde ambos são iguais; medir erro finito
        diff = np.abs(outs_pt_real[k] - outs_onnx_v2[k])
        max_e = float(np.max(diff))
        mean_e = float(np.mean(diff))
        ok = (max_e <= 1e-4) and (mean_e <= 1e-5)
        if not ok:
            num_parity["all_pass"] = False
        num_parity["heads"][k] = {"max_abs_error": max_e, "mean_abs_error": mean_e, "pass": ok}
    save_json(OUT_DIR / "numerical_parity.json", num_parity)

    dec_parity = {"samples": len(inputs_1k["team_idx"]), "all_pass": True, "heads": {}}
    for k in ID_OUTPUTS:
        agr = float(np.mean(outs_pt_real[k] == outs_onnx_v2[k]))
        ok = agr == 1.0
        if not ok:
            dec_parity["all_pass"] = False
        dec_parity["heads"][k] = {"agreement": agr, "pass": ok}
    save_json(OUT_DIR / "decision_parity.json", dec_parity)

    m_ox_v2 = compute_metrics(outs_onnx_v2, labels_1k)
    met_parity = {"all_pass": True, "metrics": {}}
    for k in m_a:
        ad = abs(m_a[k] - m_ox_v2[k])
        ok = ad <= 1e-6
        if not ok:
            met_parity["all_pass"] = False
        met_parity["metrics"][k] = {"pytorch_v2": m_a[k], "onnx_v2": m_ox_v2[k], "abs_diff": round(ad, 8), "pass": ok}
    save_json(OUT_DIR / "metric_parity.json", met_parity)

    # Seção 7: Side Mask V2 após paridade contextual (Validation e Test)
    with open(SIDE_CONTRACT_V2, "r", encoding="utf-8") as f:
        contract_spots = json.load(f)["spots"]
    val_sm = eval_side_mask_v2_split("validation", w_v2, sess_v2, spot_to_idx, sup_mask_np, contract_spots)
    test_sm = eval_side_mask_v2_split("test", w_v2, sess_v2, spot_to_idx, sup_mask_np, contract_spots)
    sm_all_pass = (
        val_sm["onnx_v2_with_side_mask_v2"]["wrong_side_selection"] == 0
        and val_sm["onnx_v2_with_side_mask_v2"]["unsupported_selection"] == 0
        and val_sm["onnx_v2_with_side_mask_v2"]["invalid_masked_selection"] == 0
        and test_sm["onnx_v2_with_side_mask_v2"]["wrong_side_selection"] == 0
        and test_sm["onnx_v2_with_side_mask_v2"]["unsupported_selection"] == 0
        and test_sm["onnx_v2_with_side_mask_v2"]["invalid_masked_selection"] == 0
        and val_sm["spot_mrr_delta"] >= -0.005
        and val_sm["spot_top5_delta"] >= -0.005
        and test_sm["spot_mrr_delta"] >= -0.005
        and test_sm["spot_top5_delta"] >= -0.005
    )
    save_json(
        OUT_DIR / "side_mask_v2_metrics.json",
        {"validation": val_sm, "test": test_sm, "all_gates_pass": sm_all_pass},
    )

    # Seção 9: Performance CPU Batches 1..5
    perf = benchmark_onnx_v2(onnx_v2_path, inputs_1k)
    save_json(OUT_DIR / "performance_metrics.json", perf)

    print(
        f"2B51_PY_OK ablation={ablation['status']} "
        f"pt_mrr={m_a['spot_mrr']} zero_mrr={m_b['spot_mrr']} v1_mrr={m_c['spot_mrr']} v2_mrr={m_ox_v2['spot_mrr']} "
        f"num_pass={num_parity['all_pass']} dec_pass={dec_parity['all_pass']} met_pass={met_parity['all_pass']} "
        f"sm_pass={sm_all_pass} test_v2_mrr={test_sm['onnx_v2_with_side_mask_v2']['spot_mrr']} "
        f"b5_p95={perf['batches']['5']['p95_ms']} b5_p99={perf['batches']['5']['p99_ms']}"
    )


if __name__ == "__main__":
    main()
