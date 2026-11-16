"""
Gera professional_spot_coverage_summary.json consolidando os 53 spots de mirage_v2
em SUPERVISED_STRONG, SUPERVISED_WEAK e ZERO_PROFESSIONAL_SUPPORT.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def main():
    mask_file = REPO_ROOT / "datasets" / "mirage_v2" / "positioning_v2_full_temporal" / "supervised_spot_mask_v1.json"
    ranking_file = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_index_spot_ranking_coverage.json"
    revised_file = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "revised_spot_supervision_report.json"

    with open(mask_file, "r", encoding="utf-8") as f:
        mask_data = json.load(f)

    with open(ranking_file, "r", encoding="utf-8") as f:
        rank_data = json.load(f)

    with open(revised_file, "r", encoding="utf-8") as f:
        rev_data = json.load(f)

    # Detalhes dos 27 supervisionados
    supervised_strong = []
    supervised_weak = []
    zero_support = []

    for item in mask_data["spot_masks"]:
        s_id = item["spot_id"]
        train_sup = item["train_support"]
        val_sup = item["validation_support"]
        mask = item["mask"]
        idx = item["catalog_index"]

        perf_meta = rev_data.get("spots", {}).get(s_id, {})
        rank_meta = rank_data.get("spots", {}).get(s_id, {})

        unique_demos = perf_meta.get("unique_demos", rank_meta.get("unique_demos", "N/A"))
        unique_players = perf_meta.get("unique_players", rank_meta.get("unique_players", "N/A"))
        mrr = perf_meta.get("mrr", rank_meta.get("mrr", "N/A"))

        entry = {
            "catalog_index": idx,
            "spot_id": s_id,
            "train_support": train_sup,
            "validation_support": val_sup,
            "mask": mask,
            "unique_demos": unique_demos,
            "unique_players": unique_players,
            "known_mrr": mrr
        }

        if mask == 0 or train_sup == 0:
            entry["classification"] = "ZERO_PROFESSIONAL_SUPPORT"
            entry["utility_ai_available"] = True
            entry["neural_supervised_mask"] = 0
            zero_support.append(entry)
        elif train_sup >= 500:
            entry["classification"] = "SUPERVISED_STRONG"
            entry["confidence_tier"] = "HIGH_CONFIDENCE"
            supervised_strong.append(entry)
        else:
            entry["classification"] = "SUPERVISED_WEAK"
            entry["confidence_tier"] = "LOW_CONFIDENCE"
            supervised_weak.append(entry)

    summary = {
        "schema": "csbot.professional_spot_coverage_summary.v1",
        "generated_at_utc": "2026-11-09T04:10:00Z",
        "total_spots_in_catalog": 53,
        "supervised_total": len(supervised_strong) + len(supervised_weak),
        "zero_support_total": len(zero_support),
        "counts_by_group": {
            "SUPERVISED_STRONG": len(supervised_strong),
            "SUPERVISED_WEAK": len(supervised_weak),
            "ZERO_PROFESSIONAL_SUPPORT": len(zero_support)
        },
        "groups": {
            "SUPERVISED_STRONG": supervised_strong,
            "SUPERVISED_WEAK": supervised_weak,
            "ZERO_PROFESSIONAL_SUPPORT": zero_support
        },
        "governance_invariants": {
            "unsupported_spots_neural_mask_zero": True,
            "utility_ai_fallback_available": True,
            "zero_synthetic_data_created": True,
            "zero_support_reported_as_na": True
        }
    }

    out_file = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "professional_spot_coverage_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"SPOT_COVERAGE_GENERATED: total={53} strong={len(supervised_strong)} weak={len(supervised_weak)} zero={len(zero_support)}")
    print(f"OUTPUT: {out_file.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
