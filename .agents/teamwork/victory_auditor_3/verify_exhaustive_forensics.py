import json
from pathlib import Path
import pyarrow.parquet as pq
import numpy as np

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")

def run_exhaustive_forensics():
    results = {}
    
    # 1. Pilot Dataset Verification
    pilot_path = BASE_DIR / "datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet"
    pilot_table = pq.read_table(pilot_path)
    results["pilot_rows"] = pilot_table.num_rows
    results["pilot_cols"] = pilot_table.column_names
    
    # 2. Shards Analysis
    shard_dir = BASE_DIR / "datasets/mirage_v2/positioning_v2_full_temporal"
    shards = sorted(list(shard_dir.glob("shard_*.parquet")))
    results["shard_count"] = len(shards)
    
    expected_cols = {
        "sequence_id", "demo_id", "match_id", "round_id", "player_id", "slot", "split",
        "window_start_frame", "window_end_frame", "label_frame", "npz_path",
        "PositioningState", "ObjectiveSubtype", "SaveSubtype", "NextSector",
        "CandidateSpotId", "SpotLossMask", "Transition", "ExitTrigger",
        "confidence", "provenance_type", "next_sector_source"
    }
    
    total_rows = 0
    split_counts = {}
    unique_seq_ids = set()
    zero_coords = 0
    bad_window_lens = 0
    leakages = 0
    allowed_sectors = {"A", "B", "MID", "CT", "T", "DYNAMIC"}
    invalid_sectors = 0
    sources = set()
    
    for sp in shards:
        table = pq.read_table(sp)
        total_rows += table.num_rows
        
        # Check cols
        cols = set(table.column_names)
        missing_cols = expected_cols - cols
        if missing_cols:
            results[f"missing_cols_{sp.name}"] = list(missing_cols)
            
        seq_ids = table["sequence_id"].to_pylist()
        unique_seq_ids.update(seq_ids)
        
        for s in table["split"].to_pylist():
            split_counts[s] = split_counts.get(s, 0) + 1
            
        starts = table["window_start_frame"].to_numpy()
        ends = table["window_end_frame"].to_numpy()
        labels = table["label_frame"].to_numpy()
        
        bad_window_lens += int(np.sum((ends - starts) != 31))
        leakages += int(np.sum(labels != ends))
        
        for sec in table["NextSector"].to_pylist():
            if sec not in allowed_sectors:
                invalid_sectors += 1
                
        sources.update(table["next_sector_source"].to_pylist())
        
        poss = table["current_pos"].to_pylist()
        for p in poss:
            if abs(p[0]) < 1e-3 and abs(p[1]) < 1e-3 and abs(p[2]) < 1e-3:
                zero_coords += 1

    results["total_rows"] = total_rows
    results["unique_sequence_ids"] = len(unique_seq_ids)
    results["duplicate_sequence_ids"] = total_rows - len(unique_seq_ids)
    results["split_counts"] = split_counts
    results["zero_coords_in_accepted"] = zero_coords
    results["bad_window_lens"] = bad_window_lens
    results["leakages"] = leakages
    results["invalid_sectors"] = invalid_sectors
    results["next_sector_sources"] = list(sources)
    
    # 3. Test Set Isolation Verification
    adv_path = BASE_DIR / "training_runs/positioning_v2_real_temporal/adversarial_success_audit.json"
    with open(adv_path, "r", encoding="utf-8") as f:
        adv = json.load(f)
    
    front1 = adv.get("adversarial_fronts_audit", {}).get("front_1_test_set_isolation", {})
    results["test_split_model_inferences"] = front1.get("test_split_model_inferences")
    results["test_split_metrics_computed"] = front1.get("test_split_metrics_computed")
    results["test_split_touched_by_trainer"] = front1.get("test_split_touched_by_trainer")
    results["final_holdout_touched"] = front1.get("final_holdout_touched")
    
    # Check pilot_gates_evaluation block
    results["pilot_gates_evaluation"] = adv.get("pilot_gates_evaluation")
    
    # 4. Zero Support Treatment (Rule 03)
    dist_path = BASE_DIR / "training_runs/positioning_v2_real_temporal/full_index_distribution.json"
    with open(dist_path, "r", encoding="utf-8") as f:
        dist = json.load(f)
    results["dist_rule_03"] = dist.get("rule_03_zero_support_is_na")
    
    spot_cov_path = BASE_DIR / "training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json"
    with open(spot_cov_path, "r", encoding="utf-8") as f:
        spot_cov = json.load(f)
    results["spot_ranking_treatment"] = spot_cov.get("zero_support_treatment")
    results["label_missing_from_candidate_mask"] = spot_cov.get("label_missing_from_candidate_mask")
    results["invalid_candidate_masks"] = spot_cov.get("invalid_candidate_masks")

    # 5. Dataloader gates telemetry
    dl_path = BASE_DIR / "training_runs/positioning_v2_real_temporal/full_index_dataloader_gates.json"
    with open(dl_path, "r", encoding="utf-8") as f:
        dl_gates = json.load(f)
    results["dataloader_gates"] = dl_gates

    # 6. Accounting reconciliation
    acc_path = BASE_DIR / "training_runs/positioning_v2_real_temporal/full_index_accounting_reconciliation.json"
    with open(acc_path, "r", encoding="utf-8") as f:
        acc = json.load(f)
    results["accounting_closure"] = acc.get("closure_verified")
    results["processed_demos"] = acc.get("demo_counts")
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_exhaustive_forensics()
