"""Reconciliacao de thresholds e comparacao best-vs-best do Marco 2B.3.4.

NAO executa inferencia nova:
  - Baseline (2B.3.3): head_transition_occurs congelada + cache val_extracted.npz.
  - Patch (2B.3.4 corrigido): usa o sweep ja gravado do experimento selecionado.

Saida: threshold_reconciliation.json (mesmo diretorio do patch).
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
    PositioningTransformerV2RealTemporal,
)
from tools.phase3a_training.canonical_v2_dataloader import load_supervised_spot_mask  # noqa: E402

PATCH_DIR = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1"
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
GRID = [round(0.40 + 0.025 * i, 3) for i in range(13)]


def sweep_to(probs, targets):
    out = []
    for t in GRID:
        preds = (probs >= t).astype(np.int64)
        tp = int(np.sum((preds == 1) & (targets == 1)))
        fp = int(np.sum((preds == 1) & (targets == 0)))
        fn = int(np.sum((preds == 0) & (targets == 1)))
        tn = int(np.sum((preds == 0) & (targets == 0)))
        p1 = tp / (tp + fp) if (tp + fp) else 0.0
        r1 = tp / (tp + fn) if (tp + fn) else 0.0
        f1_1 = 2 * p1 * r1 / (p1 + r1) if (p1 + r1) else 0.0
        p0 = tn / (tn + fn) if (tn + fn) else 0.0
        r0 = tn / (tn + fp) if (tn + fp) else 0.0
        f1_0 = 2 * p0 * r0 / (p0 + r0) if (p0 + r0) else 0.0
        out.append({
            "threshold": t,
            "macro_f1": round((f1_0 + f1_1) / 2, 4),
            "balanced_accuracy": round((r0 + r1) / 2, 4),
            "NO_TRANSITION_precision": round(p0, 4),
            "NO_TRANSITION_recall": round(r0, 4),
            "TRANSITION_OCCURS_precision": round(p1, 4),
            "TRANSITION_OCCURS_recall": round(r1, 4),
            "false_positive_rate": round(fp / (fp + tn), 4) if (fp + tn) else 0.0,
            "false_negative_rate": round(fn / (fn + tp), 4) if (fn + tp) else 0.0,
            "predicted_transition_rate": round(float(preds.mean()), 4),
            "actual_transition_rate": round((tp + fn) / len(targets), 4) if len(targets) else 0.0,
        })
    return out


def rare_mean(state_metrics):
    vals = [state_metrics["per_class"][k]["recall"] for k in RARE
            if isinstance(state_metrics["per_class"].get(k, {}).get("recall"), (int, float))]
    return float(np.mean(vals)) if vals else 0.0


def score(state_f1, to_f1, ns_f1, tr_f1, tg_f1, rare):
    return round(
        W["state_macro_f1"] * state_f1 + W["sector_transition_macro_f1"] * to_f1
        + W["next_sector_macro_f1"] * ns_f1 + W["transition_macro_f1"] * tr_f1
        + W["exit_trigger_macro_f1"] * tg_f1 + W["rare_state_recall_mean"] * rare, 6)


def pick(sweep, others):
    rows = []
    for s in sweep:
        sc = score(others["state_macro_f1"], s["macro_f1"], others["next_sector_macro_f1"],
                   others["transition_macro_f1"], others["exit_trigger_macro_f1"],
                   others["rare_state_recall_mean"])
        rows.append({**s, "temporal_score": sc})
    feasible = [r for r in rows if r["TRANSITION_OCCURS_recall"] >= 0.35 and r["NO_TRANSITION_recall"] >= 0.78]
    best_feas = max(feasible, key=lambda r: (r["macro_f1"], r["temporal_score"])) if feasible else None
    best_all = max(rows, key=lambda r: r["temporal_score"])
    return rows, best_feas, best_all


def gates_at(row):
    return {
        "transition_occurs_macro_f1_ge_0_55": bool(row["macro_f1"] >= 0.55),
        "transition_occurs_recall_ge_0_35": bool(row["TRANSITION_OCCURS_recall"] >= 0.35),
        "no_transition_recall_ge_0_78": bool(row["NO_TRANSITION_recall"] >= 0.78),
    }


print("=" * 78)
print("1. BASELINE 2B.3.3 - sweep de threshold (cache, sem inferencia nova)")
print("=" * 78)

c = np.load(CACHE)
pooled = torch.from_numpy(c["val_pooled"])
model = PositioningTransformerV2RealTemporal(supervised_spot_mask=load_supervised_spot_mask())
ck = torch.load(BASE, map_location="cpu")
model.load_state_dict(ck["model_state_dict"] if "model_state_dict" in ck else ck)
model.eval()
with torch.no_grad():
    lo = model.head_transition_occurs(pooled).numpy()
prob_to = np.exp(lo[:, 1] - np.logaddexp(lo[:, 0], lo[:, 1]))
targ_to = c["val_targets_to"]
print(f"  val_targets_to: n={len(targ_to)}  positivos={int((targ_to == 1).sum())} ({(targ_to == 1).mean()*100:.2f}%)")

base_other = {
    "state_macro_f1": 0.2894,
    "next_sector_macro_f1": 0.3936,
    "transition_macro_f1": 0.5749,
    "exit_trigger_macro_f1": 0.2325,
    "rare_state_recall_mean": round(float(np.mean([0.4446, 0.0, 0.0, 0.0463, 0.0])), 6),
}
base_rows, base_best_feas, base_best_all = pick(sweep_to(prob_to, targ_to), base_other)

for r in base_rows:
    print(f"  {r['threshold']:>5.3f} mF1={r['macro_f1']:>8.4f} TO_rec={r['TRANSITION_OCCURS_recall']:>7.4f} "
          f"NT_rec={r['NO_TRANSITION_recall']:>7.4f} score={r['temporal_score']:>8.6f}")
print(f"  melhor global : thr={base_best_all['threshold']} score={base_best_all['temporal_score']}")
print(f"  melhor viavel : {'thr=' + str(base_best_feas['threshold']) if base_best_feas else 'NENHUM'}")

print()
print("=" * 78)
print("2. EXPERIMENTO SELECIONADO - sweep ja gravado, reavaliado")
print("=" * 78)

sel = json.load(open(PATCH_DIR / "selected_thresholds.json", encoding="utf-8"))
sel_exp = sel["selected_experiment"]
sel_thr = float(sel["sector_transition_occurs"]["threshold"])
exp = json.load(open(PATCH_DIR / f"{sel_exp}_metrics.json", encoding="utf-8"))
exp_other = {
    "state_macro_f1": exp["positioning_state"]["macro_f1"],
    "next_sector_macro_f1": exp["next_sector"]["macro_f1"],
    "transition_macro_f1": exp["transition"]["macro_f1"],
    "exit_trigger_macro_f1": exp["exit_trigger"]["macro_f1"],
    "rare_state_recall_mean": round(rare_mean(exp["positioning_state"]), 6),
}
exp_rows, exp_best_feas, exp_best_all = pick(exp["sector_transition_threshold_sweep"], exp_other)

for r in exp_rows:
    mark = "  <== SELECIONADO" if abs(r["threshold"] - sel_thr) < 1e-9 else ""
    print(f"  {r['threshold']:>5.3f} mF1={r['macro_f1']:>8.4f} TO_rec={r['TRANSITION_OCCURS_recall']:>7.4f} "
          f"NT_rec={r['NO_TRANSITION_recall']:>7.4f} score={r['temporal_score']:>8.6f}{mark}")
print(f"  melhor global : thr={exp_best_all['threshold']} score={exp_best_all['temporal_score']}")
print(f"  melhor viavel : {'thr=' + str(exp_best_feas['threshold']) if exp_best_feas else 'NENHUM'}")

sel_row = next(r for r in exp_rows if abs(r["threshold"] - sel_thr) < 1e-9)
g = gates_at(sel_row)
print(f"\n  3. GATES DE TRANSICAO @ thr selecionado ({sel_thr}):")
for k, v in g.items():
    print(f"    {k:<42} = {v}")

print()
print("=" * 78)
print("4. COMPARACAO BEST-VS-BEST")
print("=" * 78)
print(f"  baseline 2B.3.3      : score_max={base_best_all['temporal_score']:.6f} @thr={base_best_all['threshold']}")
print(f"  patch 2B.3.4 ({sel_exp}) : score_max={exp_best_all['temporal_score']:.6f} @thr={exp_best_all['threshold']}"
      f"  | score@{sel_thr}={sel_row['temporal_score']:.6f}")
if base_best_feas and exp_best_feas:
    print(f"  delta (viavel)      : {exp_best_feas['temporal_score'] - base_best_feas['temporal_score']:+.6f}")

out = {
    "schema": "csbot.joint_temporal_patch.threshold_reconciliation.v2",
    "purpose": "comparacao best-vs-best baseline 2B.3.3 vs patch 2B.3.4 corrigido",
    "validation_total_evaluated": int(len(targ_to)),
    "threshold_grid": GRID,
    "baseline": {
        "source": "2B.3.3 selected_patch_checkpoint.pt head_transition_occurs + val_extracted.npz",
        "other_heads_metrics": base_other,
        "sweep": base_rows,
        "best_global": base_best_all,
        "best_feasible": base_best_feas,
    },
    "selected_experiment": sel_exp,
    "selected_threshold_from_run": sel_thr,
    "patch": {
        "other_heads_metrics": exp_other,
        "sweep_with_score": exp_rows,
        "best_global": exp_best_all,
        "best_feasible": exp_best_feas,
        "gates_at_selected_threshold": g,
        "selected_row": sel_row,
    },
    "delta_temporal_score_best_vs_best": round(
        exp_best_all["temporal_score"] - base_best_all["temporal_score"], 6),
    "delta_temporal_score_feasible": (
        round(exp_best_feas["temporal_score"] - base_best_feas["temporal_score"], 6)
        if (base_best_feas and exp_best_feas) else None),
}
outp = PATCH_DIR / "threshold_reconciliation.json"
json.dump(out, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"\nsalvo em {outp.relative_to(REPO)}")
