import json
from pathlib import Path
import numpy as np
import onnxruntime as ort

from tools.phase3a_training.run_marco_2b5_onnx_export import (
    BASE_DIR,
    DS_DIR,
    OUTPUT_NAMES,
    build_parity_corpus,
    load_catalog,
    load_supervised_spot_mask,
)

OUT_PATH = (
    BASE_DIR
    / "training_runs"
    / "positioning_v2_real_temporal"
    / "csharp_shadow_integration"
    / "parity_reference_bundle.json"
)
MODEL_PATH = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx"


def main() -> None:
    _, spot_to_idx = load_catalog(DS_DIR)
    sup_mask_np = load_supervised_spot_mask().numpy() > 0.5

    inputs, _, meta = build_parity_corpus(spot_to_idx, sup_mask_np)
    # Amostra estratificada determinística: 100 sequências (passo 10) de 1000
    idx = np.arange(0, 1000, 10, dtype=np.int64)
    sub_inputs = {k: v[idx] for k, v in inputs.items()}

    sess = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    ort_list = sess.run(OUTPUT_NAMES, sub_inputs)
    onnx_outs = {name: arr for name, arr in zip(OUTPUT_NAMES, ort_list)}

    bundle = {
        "provenance": "REAL",
        "source_corpus": "training_runs/positioning_v2_real_temporal/onnx_export/parity_samples_manifest.json",
        "sample_count": int(len(idx)),
        "sample_indices": idx.tolist(),
        "supervised_spot_mask": sup_mask_np.tolist(),
        "inputs": {
            "self_history": sub_inputs["self_history"].astype(np.float32).ravel().tolist(),
            "teammates": sub_inputs["teammates"].astype(np.float32).ravel().tolist(),
            "temporal_mask": sub_inputs["temporal_mask"].astype(np.float32).ravel().tolist(),
            "teammate_mask": sub_inputs["teammate_mask"].astype(np.float32).ravel().tolist(),
            "candidate_mask": sub_inputs["candidate_mask"].astype(bool).ravel().tolist(),
            "objective_eligible": sub_inputs["objective_eligible"].astype(bool).ravel().tolist(),
            "retake_eligible": sub_inputs["retake_eligible"].astype(bool).ravel().tolist(),
        },
        "expected_outputs": {
            k: (
                v.astype(np.int64).ravel().tolist()
                if v.dtype == np.int64
                else v.astype(np.float32).ravel().tolist()
            )
            for k, v in onnx_outs.items()
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(bundle, f)
    print(f"PARITY_BUNDLE_OK samples={len(idx)} size_bytes={OUT_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
