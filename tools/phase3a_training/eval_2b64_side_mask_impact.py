import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import onnxruntime as ort
import pandas as pd

from tools.phase3a_training.run_marco_2b5_onnx_export import (
    BASE_DIR,
    BASE_SIDECAR_DIR,
    DS_DIR,
    INDEX_DIR,
    OUTPUT_NAMES,
    FastNPZStore,
    load_catalog,
    load_supervised_spot_mask,
)

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_mask_route_fix"
ONNX_PATH = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx"


def eval_split(
    split_name: str,
    sess: ort.InferenceSession,
    spot_to_idx: Dict[str, int],
    sup_mask: np.ndarray,
    ct_allowed: np.ndarray,
    t_allowed: np.ndarray,
    max_samples: int = 8000,
) -> Dict[str, Any]:
    base_cols = [
        "demo_id", "npz_path", "label_frame", "slot", "split",
        "team", "CandidateSpotId", "SpotLossMask",
    ]
    parts = []
    for p in sorted(INDEX_DIR.glob("shard_*.parquet")):
        df_b = pd.read_parquet(p, columns=base_cols)
        m = (df_b["split"] == split_name) & (df_b["SpotLossMask"].astype(bool))
        if not m.any():
            continue
        parts.append(df_b.loc[m].reset_index(drop=True))
    df = pd.concat(parts, ignore_index=True)
    df["spot_idx"] = df["CandidateSpotId"].map(lambda s: spot_to_idx.get(s, -1))
    df = df[df["spot_idx"].map(lambda idx: idx >= 0 and bool(sup_mask[idx]))].reset_index(drop=True)

    if len(df) > max_samples:
        step = max(1, len(df) // max_samples)
        df = df.iloc[::step].head(max_samples).reset_index(drop=True)

    demos = df[["demo_id", "npz_path"]].drop_duplicates().set_index("demo_id")["npz_path"].to_dict()
    store = FastNPZStore(demos)
    hist, tm, tmask = store.extract_batch(
        df["demo_id"].to_numpy(),
        df["label_frame"].to_numpy(np.int64),
        df["slot"].to_numpy(np.int64),
    )
    n = len(df)
    tmask_tm = np.broadcast_to(tmask[:, :, None], (n, 32, 4)).copy()
    is_t_feat = hist[:, 31, 13] > 0.5

    def run_mode(use_side_mask: bool) -> Dict[str, Any]:
        cand_mask = np.broadcast_to(sup_mask[None, :], (n, 53)).copy()
        if use_side_mask:
            for i in range(n):
                cand_mask[i] &= (t_allowed if is_t_feat[i] else ct_allowed)

        spot_logits_list = []
        sel_list = []
        bs = 256
        for start in range(0, n, bs):
            end = min(n, start + bs)
            inputs = {
                "self_history": hist[start:end].astype(np.float32),
                "teammates": tm[start:end].astype(np.float32),
                "temporal_mask": tmask[start:end].astype(np.float32),
                "teammate_mask": tmask_tm[start:end].astype(np.float32),
                "candidate_mask": cand_mask[start:end].astype(bool),
                "objective_eligible": np.zeros((end - start,), dtype=bool),
                "retake_eligible": np.zeros((end - start,), dtype=bool),
            }
            outs = {name: arr for name, arr in zip(OUTPUT_NAMES, sess.run(OUTPUT_NAMES, inputs))}
            spot_logits_list.append(outs["spot_logits"])
            sel_list.append(outs["selected_spot_id"])
        spot_logits = np.concatenate(spot_logits_list, axis=0)
        sel = np.concatenate(sel_list, axis=0)
        targets = df["spot_idx"].to_numpy(np.int64)

        wrong_side = 0
        unsupported = 0
        invalid_masked = 0
        mrr_sum = 0.0
        top1_ok = 0
        top5_ok = 0
        ct_n, t_n = 0, 0
        ct_top1, t_top1 = 0, 0

        for i in range(n):
            s_idx = int(sel[i])
            allowed_vec = t_allowed if is_t_feat[i] else ct_allowed
            if not allowed_vec[s_idx]:
                wrong_side += 1
            if not sup_mask[s_idx]:
                unsupported += 1
            if not cand_mask[i, s_idx]:
                invalid_masked += 1

            # Ranking apenas entre candidatos permitidos pela máscara
            tgt = int(targets[i])
            if cand_mask[i, tgt]:
                order = np.argsort(-spot_logits[i])
                rank = int(np.where(order == tgt)[0][0]) + 1
                mrr_sum += 1.0 / rank
                if rank == 1:
                    top1_ok += 1
                if rank <= 5:
                    top5_ok += 1
            if is_t_feat[i]:
                t_n += 1
                if s_idx == tgt:
                    t_top1 += 1
            else:
                ct_n += 1
                if s_idx == tgt:
                    ct_top1 += 1

        return {
            "samples": n,
            "spot_mrr": round(mrr_sum / max(1, n), 6),
            "spot_top1": round(top1_ok / max(1, n), 6),
            "spot_top5": round(top5_ok / max(1, n), 6),
            "wrong_side_selected_spot": wrong_side,
            "unsupported_spot_selection": unsupported,
            "invalid_masked_selection": invalid_masked,
            "side_distribution": {
                "ct_samples": ct_n,
                "ct_top1": round(ct_top1 / max(1, ct_n), 6),
                "t_samples": t_n,
                "t_top1": round(t_top1 / max(1, t_n), 6),
            },
        }

    return {
        "baseline_no_side_mask": run_mode(False),
        "with_side_mask": run_mode(True),
    }


def main() -> None:
    with open(OUT_DIR / "spot_side_contract_v1.json", "r", encoding="utf-8") as f:
        sc = json.load(f)
    ct_allowed = np.array(sc["ct_allowed_mask"], dtype=bool)
    t_allowed = np.array(sc["t_allowed_mask"], dtype=bool)

    _, spot_to_idx = load_catalog(DS_DIR)
    sup_mask = load_supervised_spot_mask().numpy() > 0.5
    sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])

    val_res = eval_split("validation", sess, spot_to_idx, sup_mask, ct_allowed, t_allowed)
    test_res = eval_split("test", sess, spot_to_idx, sup_mask, ct_allowed, t_allowed)

    out = {
        "provenance": "REAL",
        "training_executed": False,
        "tuning_executed": False,
        "validation": val_res,
        "test": test_res,
    }
    with open(OUT_DIR / "side_mask_impact_metrics.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(
        f"SIDE_MASK_EVAL_OK val_wrong_before={val_res['baseline_no_side_mask']['wrong_side_selected_spot']} "
        f"val_wrong_after={val_res['with_side_mask']['wrong_side_selected_spot']} "
        f"val_mrr={val_res['baseline_no_side_mask']['spot_mrr']}->{val_res['with_side_mask']['spot_mrr']} "
        f"test_wrong_before={test_res['baseline_no_side_mask']['wrong_side_selected_spot']} "
        f"test_wrong_after={test_res['with_side_mask']['wrong_side_selected_spot']} "
        f"test_mrr={test_res['baseline_no_side_mask']['spot_mrr']}->{test_res['with_side_mask']['spot_mrr']}"
    )


if __name__ == "__main__":
    main()
