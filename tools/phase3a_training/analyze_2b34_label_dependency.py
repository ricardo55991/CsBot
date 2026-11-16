"""Verifica dependencia deterministica entre as labels das heads temporais.

Observacao que motivou o script: os supports por classe em Validation (exp C)
sao numericamente identicos entre heads diferentes:
    PositioningState.HOLD       = 14171  ==  ExitTrigger.FIRST_KILL  = 14171
    PositioningState.STAGING    =  7141  ==  ExitTrigger.UTILITY_EXPIRED = 7141
    PositioningState.SAVE       =   144  ==  Transition.FALLBACK   =   144
    PositioningState.CLEARANCE  = 20289  ==  Transition.COVER      = 20289
Igualdade exata de support em 501.434 linhas sugere que essas labels derivam
deterministicamente do estado. Este script mede isso explicitamente com
entropia condicional e taxa de determinismo (nao e inferencia: le apenas os
arrays de label do split de Validation).

Saida: label_dependency.json no diretorio do patch.
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.phase3a_training.canonical_v2_dataloader import (  # noqa: E402
    CanonicalV2PositioningDataset, STATE_MAP, TRANSITION_MAP, EXIT_TRIGGER_MAP,
)

PATCH = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1"
STATE_NAMES = list(STATE_MAP.keys())
TR_NAMES = list(TRANSITION_MAP.keys())
TG_NAMES = list(EXIT_TRIGGER_MAP.keys())


def entropy(p: np.ndarray) -> float:
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def dependency(child: np.ndarray, parent: np.ndarray, n_child: int, n_parent: int,
               child_names, parent_names) -> dict:
    """H(child|parent) e taxa de determinismo = sum_j max_i P(child=i|parent=j) * P(parent=j)."""
    table = np.zeros((n_parent, n_child), dtype=np.int64)
    np.add.at(table, (parent, child), 1)
    p_j = table.sum(axis=1) / table.sum()
    det = 0.0
    rows = {}
    for j in range(n_parent):
        tot = table[j].sum()
        if tot == 0:
            continue
        pcond = table[j] / tot
        det += pcond.max() * p_j[j]
        top = int(np.argmax(pcond))
        n_distinct = int((table[j] > 0).sum())
        rows[parent_names[j]] = {
            "support": int(tot),
            "dominant_child": child_names[top],
            "p_dominant": round(float(pcond.max()), 4),
            "distinct_children": n_distinct,
            "entropy_bits": round(entropy(pcond), 4),
            "distribution": {child_names[k]: int(table[j, k]) for k in range(n_child) if table[j, k] > 0},
        }
    p_i = table.sum(axis=0) / table.sum()
    h_child = entropy(p_i)
    h_cond = sum(rows[k]["entropy_bits"] * 0  for k in [])  # placeholder, computado abaixo
    h_cond = 0.0
    for j in range(n_parent):
        tot = table[j].sum()
        if tot == 0:
            continue
        h_cond += entropy(table[j] / tot) * (tot / table.sum())
    return {
        "parent": "positioning_state",
        "child_n_classes": n_child,
        "h_child_bits": round(h_child, 4),
        "h_child_given_parent_bits": round(h_cond, 4),
        "mutual_information_bits": round(h_child - h_cond, 4),
        "determinism_rate": round(det, 6),
        "determinism_formula": "sum_j max_i P(child=i|parent=j) * P(parent=j)",
        "by_parent_class": rows,
    }


print("Carregando labels do split de Validation (sem imagens)...")
ds = CanonicalV2PositioningDataset("validation", preload_demos=False)
state = np.asarray(ds.state_vals)
trans = np.asarray(ds.trans_vals)
trig = np.asarray(ds.trig_vals)
to = np.asarray(ds.trans_occurs_vals)
ns = np.asarray(ds.next_sec_vals)
nsm = np.asarray(ds.next_sec_mask_vals) > 0.5
print(f"  n={len(state)}  demos=66 (split validation)")

# conferir NULLs
print(f"  state unicos: {sorted(set(state.tolist()))}")
print(f"  trigger unicos: {sorted(set(trig.tolist()))}")

res = {
    "schema": "csbot.joint_temporal_patch.label_dependency.v1",
    "split": "validation",
    "n_rows": int(len(state)),
    "transition_given_state": dependency(trans, state, len(TR_NAMES), len(STATE_NAMES), TR_NAMES, STATE_NAMES),
    "exit_trigger_given_state": dependency(trig, state, len(TG_NAMES), len(STATE_NAMES), TG_NAMES, STATE_NAMES),
}

# NextSector so e supervisionado quando TRANSITION_OCCURS=1 e mask=1
sel = (to == 1) & nsm
NS_NAMES = ["A", "B", "MID", "CT", "T"]
res["next_sector_given_state"] = dependency(
    ns[sel], state[sel], len(NS_NAMES), len(STATE_NAMES), NS_NAMES, STATE_NAMES)
res["next_sector_given_state"]["conditioning_note"] = "apenas linhas com TRANSITION_OCCURS=1 e next_sector_loss_mask=1"

# Co-ocorrencia direta state<->trigger para os pares com support identico
pairs = []
for i, sn in enumerate(STATE_NAMES):
    for j, tn in enumerate(TG_NAMES):
        n = int(((state == i) & (trig == j)).sum())
        if n > 0 and n == int((state == i).sum()):
            pairs.append({"state": sn, "trigger": tn, "n": n,
                          "share_of_state": round(n / int((state == i).sum()), 6)})
res["state_implies_trigger"] = pairs

res_pairs_tr = []
for i, sn in enumerate(STATE_NAMES):
    for j, tn in enumerate(TR_NAMES):
        n = int(((state == i) & (trans == j)).sum())
        if n > 0 and n == int((state == i).sum()):
            res_pairs_tr.append({"state": sn, "transition": tn, "n": n,
                                 "share_of_state": round(n / int((state == i).sum()), 6)})
res["state_implies_transition"] = res_pairs_tr

p = PATCH / "label_dependency.json"
json.dump(res, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print("\n=== DEPENDENCIA DAS LABELS (Validation integral) ===")
print(f"{'head':<16} {'H(child)':>9} {'H(c|state)':>11} {'MI':>8} {'determinismo':>13}")
for k, lab in [("transition_given_state", "transition"),
               ("exit_trigger_given_state", "exit_trigger"),
               ("next_sector_given_state", "next_sector")]:
    r = res[k]
    print(f"{lab:<16} {r['h_child_bits']:>9.4f} {r['h_child_given_parent_bits']:>11.4f} "
          f"{r['mutual_information_bits']:>8.4f} {r['determinism_rate']:>13.4f}")

print("\nstate implica 100% em exit_trigger:")
for x in pairs:
    print(f"  {x['state']:<12} -> {x['trigger']:<18} n={x['n']}")
print("state implica 100% em transition:")
for x in res_pairs_tr:
    print(f"  {x['state']:<12} -> {x['transition']:<12} n={x['n']}")

print(f"\nsalvo em {p.relative_to(REPO)}")
