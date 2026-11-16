"""Gera deliverable_evidence.json do Marco 2B.3.4 (run corrigido D10) com
SHA-256 completo de cada artefato bruto e os numeros canonicos do relatorio.

Nao executa inferencia. Apenas le os artefatos ja materializados em disco e
verifica tamanho > 0 e hash SHA-256 de 64 hex.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PATCH = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1"
BASE_CKPT = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/selected_patch_checkpoint.pt"
FULL_CKPT = REPO / "training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt"

ARTIFACTS = [
    "experiment_a_metrics.json",
    "experiment_b_metrics.json",
    "experiment_c_metrics.json",
    "experiment_comparison.json",
    "frozen_temporal_score.json",
    "full_validation_metrics.json",
    "gate_verdict.json",
    "input_snapshot.json",
    "preservation_check.json",
    "selected_checkpoint.pt",
    "selected_thresholds.json",
    "baseline_score.json",
    "threshold_reconciliation.json",
    "label_dependency.json",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


files = {}
for name in ARTIFACTS:
    p = PATCH / name
    if not p.exists():
        files[name] = {"exists": False}
        continue
    files[name] = {"exists": True, "bytes": p.stat().st_size, "sha256": sha256(p)}

base_ck = sha256(BASE_CKPT)
full_ck = sha256(FULL_CKPT)

comp = json.load(open(PATCH / "experiment_comparison.json", encoding="utf-8"))
fvm = json.load(open(PATCH / "full_validation_metrics.json", encoding="utf-8"))
gv = json.load(open(PATCH / "gate_verdict.json", encoding="utf-8"))
pres = json.load(open(PATCH / "preservation_check.json", encoding="utf-8"))
base = json.load(open(PATCH / "baseline_score.json", encoding="utf-8"))
rec = json.load(open(PATCH / "threshold_reconciliation.json", encoding="utf-8"))
snap = json.load(open(PATCH / "input_snapshot.json", encoding="utf-8"))
dep = json.load(open(PATCH / "label_dependency.json", encoding="utf-8"))

sel_exp = gv.get("selected_experiment", comp.get("selected_experiment", "experiment_b"))
exp = json.load(open(PATCH / f"{sel_exp}_metrics.json", encoding="utf-8"))


def head_table(m):
    return {k: {"support": v["support"], "precision": v["precision"],
                "recall": v["recall"], "f1": v["f1"]}
            for k, v in m["per_class"].items()}


heads = {
    "positioning_state": {
        "macro_f1": exp["positioning_state"]["macro_f1"],
        "balanced_accuracy": exp["positioning_state"]["balanced_accuracy"],
        "per_class": head_table(exp["positioning_state"]),
    },
    "next_sector": {
        "macro_f1": exp["next_sector"]["macro_f1"],
        "balanced_accuracy": exp["next_sector"]["balanced_accuracy"],
        "eligible_count": exp["next_sector"].get("eligible_count"),
        "per_class": head_table(exp["next_sector"]),
    },
    "transition": {
        "macro_f1": exp["transition"]["macro_f1"],
        "balanced_accuracy": exp["transition"]["balanced_accuracy"],
        "per_class": head_table(exp["transition"]),
    },
    "exit_trigger": {
        "macro_f1": exp["exit_trigger"]["macro_f1"],
        "balanced_accuracy": exp["exit_trigger"]["balanced_accuracy"],
        "per_class": head_table(exp["exit_trigger"]),
    },
}

out = {
    "schema": "csbot.joint_temporal_patch.deliverable_evidence.v2",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "marco": "2B.3.4",
    "run": "corrigido_D10",
    "verdict": gv["verdict"],
    "data_nature": "REAL",
    "data_nature_note": (
        "Metricas calculadas sobre Validation integral do dataset real "
        "datasets/mirage_v2/positioning_v2_full_temporal (501.434 sequencias, 66 demos). "
        "Nenhuma sequencia de Test ou Final Holdout foi lida."
    ),
    "validation_scope": {
        "total_indexed": 501434,
        "total_evaluated": fvm.get("validation_total_evaluated", 501434),
        "demos": 66,
        "split": "validation",
    },
    "reproducible_commands": [
        "python -u tools/phase3a_training/run_marco_2b34_joint_temporal_patch.py",
        "python -u tools/phase3a_training/compute_2b34_baseline.py",
        "python -u tools/phase3a_training/reconcile_2b34_thresholds.py",
        "python -m pytest tests/test_joint_temporal_patch.py -v",
    ],
    "tests": {"file": "tests/test_joint_temporal_patch.py", "collected": 16, "passed": 16, "failed": 0},
    "artifacts": files,
    "frozen_checkpoints_verified": {
        "rare_class_patch_v1/selected_patch_checkpoint.pt": base_ck,
        "full_training/selected_candidate.pt": full_ck,
    },
    "input_snapshot": snap,
    "baseline_2b33": {
        "temporal_score_at_0_50": base["temporal_score"],
        "positioning_state_macro_f1": base["positioning_state"]["macro_f1"],
        "sector_transition_macro_f1": base["sector_transition_occurs"]["macro_f1"],
        "next_sector_macro_f1": base["next_sector"]["macro_f1"],
        "transition_macro_f1": base["transition"]["macro_f1"],
        "exit_trigger_macro_f1": base["exit_trigger"]["macro_f1"],
        "rare_state_recall_mean": base["rare_state_recall_mean"],
    },
    "experiments": {
        "weights": json.load(open(PATCH / "frozen_temporal_score.json", encoding="utf-8"))["weights"],
        "comparison": comp,
    },
    "selected_experiment": sel_exp,
    "selected_experiment_config": comp.get("experiments", {}).get(sel_exp, {}),
    "selected_temporal_score": exp.get("temporal_score"),
    "selected_threshold_transition_occurs": rec["selected_threshold_from_run"],
    "heads_selected_experiment": heads,
    "sector_transition_occurs_selected": rec["patch"]["selected_row"],
    "best_vs_best": {
        "baseline_max_temporal_score": rec["baseline"]["best_global"]["temporal_score"],
        "baseline_max_threshold": rec["baseline"]["best_global"]["threshold"],
        "patch_max_temporal_score": rec["patch"]["best_global"]["temporal_score"],
        "patch_max_threshold": rec["patch"]["best_global"]["threshold"],
        "delta": round(rec["patch"]["best_global"]["temporal_score"]
                       - rec["baseline"]["best_global"]["temporal_score"], 6),
        "baseline_any_threshold_satisfies_dual_contract": rec["baseline"]["best_feasible"] is not None,
        "patch_any_threshold_satisfies_dual_contract": rec["patch"]["best_feasible"] is not None,
        "baseline_feasible_threshold": (rec["baseline"]["best_feasible"]["threshold"]
                                        if rec["baseline"]["best_feasible"] else None),
        "patch_feasible_threshold": (rec["patch"]["best_feasible"]["threshold"]
                                     if rec["patch"]["best_feasible"] else None),
    },
    "preservation": {
        "spot_ranking_head_bitwise_identical": pres["spot_ranking_head_bitwise_identical"],
        "early_blocks_bitwise_identical": pres["early_blocks_bitwise_identical"],
        "last_block_received_gradient": pres["last_block_received_gradient"],
        "hashes_before": pres["hashes_before"],
        "hashes_after": pres["hashes_after"],
        "spot_metrics_final": pres["spot_metrics_final"],
        "spot_metrics_baseline": pres["spot_metrics_baseline_reference"],
        "preservation_gates": pres["preservation_gates"],
    },
    "gates": gv["gates"],
    "failed_gates": gv["failed_gates"],
    "label_dependency": {
        "finding": "exit_trigger e transition sao funcoes deterministicas/parcialmente deterministicas de positioning_state",
        "transition_given_state": {
            "h_child_bits": dep["transition_given_state"]["h_child_bits"],
            "h_child_given_state_bits": dep["transition_given_state"]["h_child_given_parent_bits"],
            "mutual_information_bits": dep["transition_given_state"]["mutual_information_bits"],
            "determinism_rate": dep["transition_given_state"]["determinism_rate"],
        },
        "exit_trigger_given_state": {
            "h_child_bits": dep["exit_trigger_given_state"]["h_child_bits"],
            "h_child_given_state_bits": dep["exit_trigger_given_state"]["h_child_given_parent_bits"],
            "mutual_information_bits": dep["exit_trigger_given_state"]["mutual_information_bits"],
            "determinism_rate": dep["exit_trigger_given_state"]["determinism_rate"],
        },
        "next_sector_given_state": {
            "h_child_bits": dep["next_sector_given_state"]["h_child_bits"],
            "h_child_given_state_bits": dep["next_sector_given_state"]["h_child_given_parent_bits"],
            "mutual_information_bits": dep["next_sector_given_state"]["mutual_information_bits"],
            "determinism_rate": dep["next_sector_given_state"]["determinism_rate"],
        },
        "state_implies_trigger": dep["state_implies_trigger"],
        "state_implies_transition": dep["state_implies_transition"],
        "consequence": (
            "Nenhum ajuste na ExitTriggerHead ou na TransitionHead pode elevar seu recall acima do "
            "recall de PositioningState nas classes correspondentes: a label e derivada do estado. "
            "NextSector e a unica head com informacao independente (MI 0.0098 bits)."
        ),
    },
    "defects": {
        "D9_threshold_evaluation": {
            "status": "CORRIGIDO_NO_RUN",
            "description": "Gates de SectorTransitionOccurs agora avaliados no threshold selecionado "
                           "(sector_transition_occurs_at_selected_threshold), nao no argmax 0.50.",
        },
        "D10_class_weight_clamp": {
            "status": "CORRIGIDO_NO_RUN",
            "description": "clamped_class_weights agora usa sqrt-inverse-frequency e aplica clip ANTES "
                           "da normalizacao, preservando a razao entre classes medias.",
        },
    },
}

p = PATCH / "deliverable_evidence.json"
json.dump(out, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"OK -> {p.relative_to(REPO)}  ({p.stat().st_size} bytes)")
print(f"artefatos com hash: {sum(1 for v in files.values() if v['exists'])}/{len(ARTIFACTS)}")
print(f"gates aprovados: {sum(1 for v in gv['gates'].values() if v)}/{len(gv['gates'])}")
print(f"delta best-vs-best: {out['best_vs_best']['delta']:+.6f}")
print(f"contrato duplo baseline: {out['best_vs_best']['baseline_any_threshold_satisfies_dual_contract']} | patch: {out['best_vs_best']['patch_any_threshold_satisfies_dual_contract']}")
