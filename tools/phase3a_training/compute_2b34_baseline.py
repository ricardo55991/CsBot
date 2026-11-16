"""Calcula o TemporalScore do BASELINE (checkpoint de 2B.3.3) a partir do cache
val_extracted.npz, sem executar inferencia nova.

O cache contem as preds argmax do modelo base de 2B.3.3 nas 501.434 sequencias
de Validation, alem do pooled feature usado pela head de transicao.
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.phase3a_training.positioning_model_v2 import (  # noqa: E402
    PositioningTransformerV2RealTemporal, STATE_NAMES, NEXT_SECTOR_NAMES,
    TRANSITION_NAMES, EXIT_TRIGGER_NAMES,
)
from tools.phase3a_training.canonical_v2_dataloader import load_supervised_spot_mask  # noqa: E402

CACHE = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/transition_head_patch_v2/val_extracted.npz"
BASE = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/selected_patch_checkpoint.pt"

W = {
    "state_macro_f1": 0.20,
    "sector_transition_macro_f1": 0.20,
    "next_sector_macro_f1": 0.15,
    "transition_macro_f1": 0.20,
    "exit_trigger_macro_f1": 0.15,
    "rare_state_recall_mean": 0.10,
}
RARE = ["HOLD", "OBJECTIVE", "STAGING", "RETAKE", "SAVE"]


def cls_metrics(preds, targets, names):
    per, f1s, recs = {}, [], []
    for i, n in enumerate(names):
        sup = int((targets == i).sum())
        if sup == 0:
            per[n] = {"support": 0, "precision": "N/A", "recall": "N/A", "f1": "N/A"}
            continue
        tp = int(((preds == i) & (targets == i)).sum())
        fp = int(((preds == i) & (targets != i)).sum())
        fn = int(((preds != i) & (targets == i)).sum())
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        per[n] = {"support": sup, "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4)}
        f1s.append(f)
        recs.append(r)
    return {
        "macro_f1": round(float(np.mean(f1s)) if f1s else 0.0, 4),
        "balanced_accuracy": round(float(np.mean(recs)) if recs else 0.0, 4),
        "per_class": per,
    }


c = np.load(CACHE)
pooled = torch.from_numpy(c["val_pooled"])

sup = load_supervised_spot_mask()
model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup)
ck = torch.load(BASE, map_location="cpu")
model.load_state_dict(ck["model_state_dict"] if "model_state_dict" in ck else ck)
model.eval()

with torch.no_grad():
    logits_to = model.head_transition_occurs(pooled).numpy()
prob_to = np.exp(logits_to[:, 1] - np.logaddexp(logits_to[:, 0], logits_to[:, 1]))
pred_to = (prob_to >= 0.5).astype(np.int64)
targ_to = c["val_targets_to"]

st = cls_metrics(c["val_preds_st"], c["val_targets_st"], STATE_NAMES)
to = cls_metrics(pred_to, targ_to, ["NO_TRANSITION", "TRANSITION_OCCURS"])
ns_mask = c["val_ns_mask"]
ns = cls_metrics(c["val_preds_ns"][ns_mask], c["val_targets_ns"][ns_mask], NEXT_SECTOR_NAMES)
tr = cls_metrics(c["val_preds_tr"], c["val_targets_tr"], TRANSITION_NAMES)
tg = cls_metrics(c["val_preds_tg"], c["val_targets_tg"], EXIT_TRIGGER_NAMES)

rare = [st["per_class"][k]["recall"] for k in RARE
        if isinstance(st["per_class"][k]["recall"], (int, float))]
rare_mean = float(np.mean(rare)) if rare else 0.0

score = (W["state_macro_f1"] * st["macro_f1"]
         + W["sector_transition_macro_f1"] * to["macro_f1"]
         + W["next_sector_macro_f1"] * ns["macro_f1"]
         + W["transition_macro_f1"] * tr["macro_f1"]
         + W["exit_trigger_macro_f1"] * tg["macro_f1"]
         + W["rare_state_recall_mean"] * rare_mean)

print("=== BASELINE 2B.3.3 (cache, threshold 0.50) ===")
print(f"state_macro_f1             = {st['macro_f1']}")
print(f"sector_transition_macro_f1 = {to['macro_f1']}")
print(f"next_sector_macro_f1       = {ns['macro_f1']}")
print(f"transition_macro_f1        = {tr['macro_f1']}")
print(f"exit_trigger_macro_f1      = {tg['macro_f1']}")
print(f"rare_state_recall_mean     = {round(rare_mean, 4)}")
print(f"TEMPORAL_SCORE             = {round(score, 6)}")
print("\nrare recalls:", {k: st["per_class"][k]["recall"] for k in RARE})
print("next_sector:", {k: v["recall"] for k, v in ns["per_class"].items()})
print("transition:", {k: v["recall"] for k, v in tr["per_class"].items()})
print("exit_trigger:", {k: v["recall"] for k, v in tg["per_class"].items()})
print("\nstate supports:", {k: v["support"] for k, v in st["per_class"].items()})

out = {
    "schema": "csbot.joint_temporal_patch.baseline_score.v1",
    "source": "transition_head_patch_v2/val_extracted.npz + base head_transition_occurs",
    "threshold_transition_occurs": 0.5,
    "validation_total_evaluated": int(len(targ_to)),
    "positioning_state": st,
    "sector_transition_occurs": to,
    "next_sector": ns,
    "transition": tr,
    "exit_trigger": tg,
    "rare_state_recall_mean": round(rare_mean, 6),
    "temporal_score": round(score, 6),
}
p = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1/baseline_score.json"
json.dump(out, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\nsalvo em", p)
