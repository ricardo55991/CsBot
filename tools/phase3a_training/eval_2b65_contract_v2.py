import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict

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

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_contract_v2"
ONNX_PATH = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx"


def build_v2_mask_for_sample(
    contract_spots: list,
    sup_mask: np.ndarray,
    is_t: bool,
    state_name: str,
    obj_elig: bool,
    ret_elig: bool,
) -> tuple[np.ndarray, Counter]:
    mask = sup_mask.copy()
    exclusions = Counter()
    for sp in contract_spots:
        i = int(sp["index"])
        if not mask[i]:
            exclusions["UNSUPERVISED"] += 1
            continue
        cls = sp["classification"]
        ct_rule = sp["ct_rule"]
        t_rule = sp["t_rule"]
        rule = t_rule if is_t else ct_rule

        if rule == "FORBIDDEN":
            mask[i] = False
            exclusions["WRONG_SIDE"] += 1
        elif cls == "CONTEXTUAL":
            if rule == "RETAKE_ONLY" and not ret_elig:
                mask[i] = False
                exclusions["RETAKE_INELIGIBLE"] += 1
            elif rule == "OBJECTIVE_OR_POSTPLANT" and not obj_elig and state_name not in ("OBJECTIVE", "HOLD"):
                mask[i] = False
                exclusions["OBJECTIVE_INELIGIBLE"] += 1
            elif rule == "RETAKE_OR_HOLD" and not ret_elig and state_name not in ("HOLD", "STAGING", "CLEARANCE"):
                mask[i] = False
                exclusions["WRONG_STATE"] += 1
    return mask, exclusions


def eval_split_v2(
    split_name: str,
    sess: ort.InferenceSession,
    spot_to_idx: Dict[str, int],
    sup_mask: np.ndarray,
    contract_spots: list,
    max_samples: int = 8000,
) -> Dict[str, Any]:
    base_cols = ["demo_id", "npz_path", "label_frame", "slot", "split", "CandidateSpotId", "SpotLossMask", "PositioningState"]
    parts = []
    for p in sorted(INDEX_DIR.glob("shard_*.parquet")):
        df_b = pd.read_parquet(p, columns=base_cols)
        m = (df_b["split"] == split_name) & (df_b["SpotLossMask"].astype(bool))
        if m.any():
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
    states = df["PositioningState"].astype(str).tolist()
    targets = df["spot_idx"].to_numpy(np.int64)

    cand_v2 = np.zeros((n, 53), dtype=bool)
    excl_total = Counter()
    removed_targets_by_spot = Counter()
    removed_targets_by_state = Counter()
    removed_targets_ct_in_t_only = 0
    removed_targets_t_in_ct_only = 0

    for i in range(n):
        st = states[i]
        obj_e = (st == "OBJECTIVE")
        ret_e = (st == "RETAKE")
        m_i, ex_i = build_v2_mask_for_sample(contract_spots, sup_mask, bool(is_t_feat[i]), st, obj_e, ret_e)
        cand_v2[i] = m_i
        excl_total += ex_i
        tgt = int(targets[i])
        if not m_i[tgt]:
            removed_targets_by_spot[df.loc[i, "CandidateSpotId"]] += 1
            removed_targets_by_state[st] += 1
            cls = contract_spots[tgt]["classification"]
            if not is_t_feat[i] and cls == "T_ONLY":
                removed_targets_ct_in_t_only += 1
            elif is_t_feat[i] and cls == "CT_ONLY":
                removed_targets_t_in_ct_only += 1

    # Inferência em mini-batches de 256
    spot_logits_list, sel_list = [], []
    bs = 256
    for start in range(0, n, bs):
        end = min(n, start + bs)
        inputs = {
            "self_history": hist[start:end].astype(np.float32),
            "teammates": tm[start:end].astype(np.float32),
            "temporal_mask": tmask[start:end].astype(np.float32),
            "teammate_mask": tmask_tm[start:end].astype(np.float32),
            "candidate_mask": cand_v2[start:end].astype(bool),
            "objective_eligible": np.array([states[k] == "OBJECTIVE" for k in range(start, end)], dtype=bool),
            "retake_eligible": np.array([states[k] == "RETAKE" for k in range(start, end)], dtype=bool),
        }
        outs = {name: arr for name, arr in zip(OUTPUT_NAMES, sess.run(OUTPUT_NAMES, inputs))}
        spot_logits_list.append(outs["spot_logits"])
        sel_list.append(outs["selected_spot_id"])

    spot_logits = np.concatenate(spot_logits_list, axis=0)
    sel = np.concatenate(sel_list, axis=0)

    wrong_side = 0
    unsupported = 0
    invalid_masked = 0
    mrr_sum = 0.0
    top1_ok = 0
    top5_ok = 0

    for i in range(n):
        s_idx = int(sel[i])
        if not sup_mask[s_idx]:
            unsupported += 1
        if not cand_v2[i, s_idx]:
            invalid_masked += 1
        rule = contract_spots[s_idx]["t_rule"] if is_t_feat[i] else contract_spots[s_idx]["ct_rule"]
        if rule == "FORBIDDEN":
            wrong_side += 1

        tgt = int(targets[i])
        if cand_v2[i, tgt]:
            order = np.argsort(-spot_logits[i])
            rank = int(np.where(order == tgt)[0][0]) + 1
            mrr_sum += 1.0 / rank
            if rank == 1:
                top1_ok += 1
            if rank <= 5:
                top5_ok += 1

    return {
        "samples": n,
        "spot_mrr": round(mrr_sum / max(1, n), 6),
        "spot_top1": round(top1_ok / max(1, n), 6),
        "spot_top5": round(top5_ok / max(1, n), 6),
        "wrong_side_neural_selection": wrong_side,
        "unsupported_neural_selection": unsupported,
        "invalid_masked_selection": invalid_masked,
        "targets_removed_total": int(sum(removed_targets_by_spot.values())),
        "targets_removed_ct_in_t_only": removed_targets_ct_in_t_only,
        "targets_removed_t_in_ct_only": removed_targets_t_in_ct_only,
        "targets_removed_by_spot": dict(removed_targets_by_spot),
        "targets_removed_by_state": dict(removed_targets_by_state),
        "mask_exclusion_counts": dict(excl_total),
    }


def main() -> None:
    with open(OUT_DIR / "spot_side_contract_v2.json", "r", encoding="utf-8") as f:
        c2 = json.load(f)
    contract_spots = c2["spots"]
    _, spot_to_idx = load_catalog(DS_DIR)
    sup_mask = load_supervised_spot_mask().numpy() > 0.5
    sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])

    val_v2 = eval_split_v2("validation", sess, spot_to_idx, sup_mask, contract_spots)
    test_v2 = eval_split_v2("test", sess, spot_to_idx, sup_mask, contract_spots)

    gates_ok = (
        val_v2["spot_mrr"] >= 0.72
        and test_v2["spot_mrr"] >= 0.72
        and val_v2["spot_top5"] >= 0.92
        and test_v2["spot_top5"] >= 0.92
        and val_v2["wrong_side_neural_selection"] == 0
        and test_v2["wrong_side_neural_selection"] == 0
    )

    with open(OUT_DIR / "side_mask_impact_metrics_v2.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "provenance": "REAL",
                "validation_v2": val_v2,
                "test_v2": test_v2,
                "preservation_gates_pass": gates_ok,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(OUT_DIR / "candidate_mask_composition.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "composition_layers": [
                    "supervised_spot_mask",
                    "side_mask",
                    "state_mask",
                    "phase_mask",
                ],
                "exclusion_reasons": [
                    "UNSUPERVISED",
                    "WRONG_SIDE",
                    "WRONG_STATE",
                    "WRONG_PHASE",
                    "OBJECTIVE_INELIGIBLE",
                    "RETAKE_INELIGIBLE",
                ],
                "validation_exclusions": val_v2["mask_exclusion_counts"],
                "test_exclusions": test_v2["mask_exclusion_counts"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"EVAL_V2_OK gates_ok={gates_ok} "
        f"val_mrr={val_v2['spot_mrr']} val_top5={val_v2['spot_top5']} val_wrong={val_v2['wrong_side_neural_selection']} "
        f"test_mrr={test_v2['spot_mrr']} test_top5={test_v2['spot_top5']} test_wrong={test_v2['wrong_side_neural_selection']} "
        f"val_removed={val_v2['targets_removed_total']} test_removed={test_v2['targets_removed_total']}"
    )


if __name__ == "__main__":
    main()
