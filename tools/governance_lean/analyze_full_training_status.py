"""
Script de análise analítica determinística dos resultados do Marco 2B.3
Local: training_runs/positioning_v2_real_temporal/full_training/
Consolida métricas de seeds, blockers, gates, classes, spots e seleção de checkpoint.
"""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FT_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    candidate_pt = FT_DIR / "selected_candidate.pt"
    pt_sha256 = sha256_file(candidate_pt) if candidate_pt.exists() else "NOT_FOUND"
    pt_size = candidate_pt.stat().st_size if candidate_pt.exists() else 0

    with open(FT_DIR / "best_model_selection.json", "r", encoding="utf-8") as f:
        best_selection = json.load(f)

    with open(FT_DIR / "three_seed_comparison.json", "r", encoding="utf-8") as f:
        three_seeds = json.load(f)

    with open(FT_DIR / "baseline_comparison.json", "r", encoding="utf-8") as f:
        baseline_comp = json.load(f)

    with open(FT_DIR / "temporal_gain_report.json", "r", encoding="utf-8") as f:
        temporal_gain = json.load(f)

    with open(FT_DIR / "collapse_monitoring.json", "r", encoding="utf-8") as f:
        collapse_mon = json.load(f)

    with open(FT_DIR / "mathematical_training_audit.json", "r", encoding="utf-8") as f:
        math_audit = json.load(f)

    with open(FT_DIR / "ml_generalization_audit.json", "r", encoding="utf-8") as f:
        ml_audit = json.load(f)

    with open(FT_DIR / "adversarial_training_audit.json", "r", encoding="utf-8") as f:
        adv_audit = json.load(f)

    summary = {
        "candidate_pt": {
            "path": "training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt",
            "size_bytes": pt_size,
            "sha256": pt_sha256
        },
        "best_selection": best_selection,
        "three_seeds": three_seeds,
        "baseline_comparison": baseline_comp,
        "temporal_gain": temporal_gain,
        "collapse_monitoring": collapse_mon,
        "math_verdict": math_audit.get("verdict"),
        "ml_verdict": ml_audit.get("verdict"),
        "adv_verdict": adv_audit.get("verdict")
    }

    out_json = FT_DIR.parent / "consolidated_analysis_cache.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"ANALYSIS_COMPLETE: seed={best_selection.get('selected_seed')} epoch={best_selection.get('selected_epoch')}")
    print(f"PT_SHA256: {pt_sha256}")
    print(f"VERDICTS: math={math_audit.get('verdict')} ml={ml_audit.get('verdict')} adv={adv_audit.get('verdict')}")

if __name__ == "__main__":
    main()
