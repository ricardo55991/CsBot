"""
Analisa detalhadamente a cobertura dos 53 spots profissionais no corpus mirage_v2.
Gera a estratificacao em SUPERVISED_STRONG, SUPERVISED_WEAK e ZERO_PROFESSIONAL_SUPPORT.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def main():
    revised_rep = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "revised_spot_supervision_report.json"
    spot_mask_file = REPO_ROOT / "datasets" / "mirage_v2" / "positioning_v2_full_temporal" / "supervised_spot_mask_v1.json"
    full_index_spot = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_index_spot_ranking_coverage.json"
    spot_catalog_file = REPO_ROOT / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json"

    with open(revised_rep, "r", encoding="utf-8") as f:
        rev_data = json.load(f)

    with open(spot_mask_file, "r", encoding="utf-8") as f:
        mask_data = json.load(f)

    with open(full_index_spot, "r", encoding="utf-8") as f:
        idx_data = json.load(f)

    with open(spot_catalog_file, "r", encoding="utf-8") as f:
        cat_data = json.load(f)

    print(f"MASK_DATA: total={len(mask_data['mask'])} supervised_count={sum(mask_data['mask'])}")
    print(f"REV_DATA keys: {list(rev_data.keys())[:5]}")
    print(f"IDX_DATA keys: {list(idx_data.keys())[:5]}")

    out = {
        "rev_sample": {k: rev_data[k] for k in list(rev_data.keys())[:3]},
        "idx_summary": {k: idx_data[k] for k in list(idx_data.keys()) if isinstance(idx_data[k], (int, float, str, bool, list))}
    }
    with open(REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "temp_spot_check.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
