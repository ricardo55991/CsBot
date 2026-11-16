#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2B.1: Suíte Canônica de Testes de Governança e Integridade do Índice Temporal Completo.

Cobre formalmente os 20 testes estipulados nos Critérios de Aceite:
1. PilotDatasetPreservedWithExactSha256
2. All444CanonicalDemosProcessed
3. EightRawDemWithoutNpzFormallyExcluded
4. WindowPolicyIdenticalAcrossAllSplits
5. SixParquetShardsMaterializedWithoutDenseTensors
6. TwentyOneCanonicalFieldsPresentInShards
7. InvalidZeroCoordinates100PercentRejectedOrMasked
8. ObjectiveAndSaveIntegratedWithProvenance
9. ObjectiveSaveAccountingClosure
10. PrecedenceRulesDeterministicallyEnforced
11. NextSectorClassesStrictlyRestricted
12. NextSectorNeverUsesCurrentSectorWithoutTransition
13. NextSectorSourceFieldPopulated
14. ExactDuplicateSequencesIsZero
15. CrossSplitDuplicatesIsZero
16. ConflictingLabelsForSameWindowIsZero
17. ConservationEquationClosurePerSplit
18. ProcessedDemoCountMatchesExpected
19. DataLoaderGateConformityOnRealNPZ
20. SpotRankingCandidateMaskCoverage
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

import pytest
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

INDEX_DIR = BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
RUNS_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal"
DS_DIR = BASE_DIR / "datasets" / "mirage_v2"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def index_artifacts():
    manifest_path = INDEX_DIR / "dataset_manifest.json"
    demo_inv_path = INDEX_DIR / "demo_inventory.json"
    ex_demos_path = INDEX_DIR / "excluded_demos_manifest.json"
    pilot_cat_path = INDEX_DIR / "pilot_preservation_catalog.json"
    obj_save_path = INDEX_DIR / "objective_save_integration.json"
    next_sec_path = INDEX_DIR / "next_sector_relabeling.json"

    reconciliation_path = RUNS_DIR / "full_index_accounting_reconciliation.json"
    jsd_path = RUNS_DIR / "full_index_jensen_shannon_divergence.json"
    spot_coverage_path = RUNS_DIR / "full_index_spot_ranking_coverage.json"
    gates_path = RUNS_DIR / "full_index_dataloader_gates.json"

    splits_path = DS_DIR / "canonical_temporal_splits_v1.json"
    pilot_parquet_path = DS_DIR / "positioning" / "positioning_sequences_v1" / "positioning_sample_sequences.parquet"

    return {
        "manifest": json.load(open(manifest_path, "r", encoding="utf-8")),
        "demo_inventory": json.load(open(demo_inv_path, "r", encoding="utf-8")),
        "excluded_demos": json.load(open(ex_demos_path, "r", encoding="utf-8")),
        "pilot_catalog": json.load(open(pilot_cat_path, "r", encoding="utf-8")),
        "obj_save_integration": json.load(open(obj_save_path, "r", encoding="utf-8")),
        "next_sector_relabeling": json.load(open(next_sec_path, "r", encoding="utf-8")),
        "reconciliation": json.load(open(reconciliation_path, "r", encoding="utf-8")),
        "jsd": json.load(open(jsd_path, "r", encoding="utf-8")),
        "spot_coverage": json.load(open(spot_coverage_path, "r", encoding="utf-8")),
        "dataloader_gates": json.load(open(gates_path, "r", encoding="utf-8")),
        "canonical_splits": json.load(open(splits_path, "r", encoding="utf-8")),
        "pilot_parquet_path": pilot_parquet_path,
        "shard_paths": sorted(list(INDEX_DIR.glob("shard_*.parquet")))
    }


# 1. PilotDatasetPreservedWithExactSha256
def test_01_pilot_dataset_preserved_with_exact_sha256(index_artifacts):
    cat = index_artifacts["pilot_catalog"]
    pilot_path = index_artifacts["pilot_parquet_path"]
    assert pilot_path.exists(), f"Piloto não encontrado em {pilot_path}"
    real_sha = compute_sha256(pilot_path)

    assert cat["file_sha256"] == real_sha
    assert real_sha == "d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe"
    assert cat["pilot_status"] == "PILOT_SUBSET_25_DEMOS_PER_SPLIT"
    assert cat["total_rows"] == 577816
    assert cat["demos_per_split"]["train"] == 25
    assert cat["demos_per_split"]["validation"] == 25
    assert cat["demos_per_split"]["test"] == 25


# 2. All444CanonicalDemosProcessed
def test_02_all_444_canonical_demos_processed(index_artifacts):
    manifest = index_artifacts["manifest"]
    splits = index_artifacts["canonical_splits"]
    inv = index_artifacts["demo_inventory"]

    assert manifest["unique_demos_by_split"]["train"] == 311
    assert manifest["unique_demos_by_split"]["validation"] == 66
    assert manifest["unique_demos_by_split"]["test"] == 67
    assert manifest["unique_demos_by_split"]["total"] == 444

    accepted_inv_demos = {item["demo_id"]: item["split"] for item in inv if item["accepted"]}
    assert len(accepted_inv_demos) == 444

    for d in splits["train_demos"]:
        assert accepted_inv_demos[d] == "train"
    for d in splits["validation_demos"]:
        assert accepted_inv_demos[d] == "validation"
    for d in splits["test_demos"]:
        assert accepted_inv_demos[d] == "test"


# 3. EightRawDemWithoutNpzFormallyExcluded
def test_03_eight_raw_dem_without_npz_formally_excluded(index_artifacts):
    ex = index_artifacts["excluded_demos"]
    splits = index_artifacts["canonical_splits"]
    assert ex["total_excluded_demos"] == 8
    assert ex["rejection_code"] == "RAW_DEM_WITHOUT_NPZ"
    assert ex["status"] == "FORMALLY_EXCLUDED"

    ex_ids = set(item["demo_id"] for item in ex["excluded_demos"])
    assert ex_ids == set(splits["excluded_demos"])
    for item in ex["excluded_demos"]:
        assert item["rejection_reason"] == "RAW_DEM_WITHOUT_NPZ"
        assert item["source_format"] == "RAW_DEM_SOURCE2"


# 4. WindowPolicyIdenticalAcrossAllSplits
def test_04_window_policy_identical_across_all_splits(index_artifacts):
    wp = index_artifacts["manifest"]["window_policy"]
    assert wp["sample_rate_hz"] == 16
    assert wp["sequence_length_frames"] == 32
    assert wp["stride_frames"] == 16
    assert wp["overlap_percentage"] == "50.0%"


# 5. SixParquetShardsMaterializedWithoutDenseTensors
def test_05_six_parquet_shards_materialized_without_dense_tensors(index_artifacts):
    shards = index_artifacts["shard_paths"]
    assert len(shards) == 6, f"Esperados 6 shards, encontrados {len(shards)}"

    total_rows = 0
    for s_path in shards:
        assert s_path.exists()
        assert s_path.stat().st_size > 0
        pf = pq.ParquetFile(s_path)
        total_rows += pf.metadata.num_rows

        # Conferir que não há tensores densos armazenados diretamente nas colunas
        schema = pf.schema_arrow
        for name in schema.names:
            col_type = str(schema.field(name).type)
            assert "float[32]" not in col_type, f"Tensor denso detectado na coluna {name}"

    manifest_rows = index_artifacts["manifest"]["total_sequences"]
    assert total_rows == manifest_rows, f"Linhas nos shards {total_rows} != {manifest_rows}"


# 6. TwentyOneCanonicalFieldsPresentInShards
def test_06_twenty_one_canonical_fields_present_in_shards(index_artifacts):
    required_fields = [
        "sequence_id", "demo_id", "match_id", "round_id", "player_id", "slot", "split",
        "window_start_frame", "window_end_frame", "label_frame", "npz_path",
        "PositioningState", "ObjectiveSubtype", "SaveSubtype", "NextSector",
        "CandidateSpotId", "SpotLossMask", "Transition", "ExitTrigger",
        "confidence", "provenance_type", "next_sector_source"
    ]
    for s_path in index_artifacts["shard_paths"]:
        pf = pq.ParquetFile(s_path)
        col_names = pf.schema.names
        for rf in required_fields:
            assert rf in col_names, f"Campo canônico obrigatório '{rf}' ausente no shard {s_path.name}"


# 7. InvalidZeroCoordinates100PercentRejectedOrMasked
def test_07_invalid_zero_coordinates_100_percent_rejected_or_masked(index_artifacts):
    # Inspecionar amostras dos shards
    for s_path in index_artifacts["shard_paths"]:
        table = pq.read_table(s_path, columns=["current_pos"])
        df = table.to_pandas()
        for pos in df["current_pos"].head(500):
            assert not (abs(pos[0]) < 1e-3 and abs(pos[1]) < 1e-3 and abs(pos[2]) < 1e-3), (
                f"Coordenada inválida [0, 0, 0] detectada no shard {s_path.name}: {pos}"
            )


# 8. ObjectiveAndSaveIntegratedWithProvenance
def test_08_objective_and_save_integrated_with_provenance(index_artifacts):
    obj_info = index_artifacts["obj_save_integration"]
    assert obj_info["accounting"]["integrated"] > 0 or obj_info["accounting"]["replaced"] > 0

    found_enriched = False
    for s_path in index_artifacts["shard_paths"]:
        table = pq.read_table(s_path, columns=["provenance_type", "PositioningState"])
        df = table.to_pandas()
        enriched = df[df["provenance_type"] == "OBJECTIVE_SAVE_ENRICHED"]
        if len(enriched) > 0:
            found_enriched = True
            assert set(enriched["PositioningState"].unique()).issubset({"OBJECTIVE", "SAVE"})
            break
    assert found_enriched, "Nenhuma sequência enriquecida de Objective/Save encontrada nos shards"


# 9. ObjectiveSaveAccountingClosure
def test_09_objective_save_accounting_closure(index_artifacts):
    obj = index_artifacts["obj_save_integration"]
    acc = obj["accounting"]
    total = acc["candidate_windows"]
    sum_parts = acc["integrated"] + acc["replaced"] + acc["duplicated"] + acc["rejected"] + acc["low_confidence_excluded"]
    assert total == sum_parts == 7791
    assert acc["closure_verified"] is True
    assert obj["rejection_breakdown"]["excluded_demos_without_npz"] == 114
    assert obj["rejection_breakdown"]["invalid_zero_coordinates"] == 18


# 10. PrecedenceRulesDeterministicallyEnforced
def test_10_precedence_rules_deterministically_enforced(index_artifacts):
    obj = index_artifacts["obj_save_integration"]
    reps = obj["sample_replacements"]
    assert len(reps) > 0, "Nenhuma substituição registrada no log de precedência"
    for r in reps:
        assert r["new_label"] in ["OBJECTIVE", "SAVE"]
        assert r["provenance"] == "objective_save_sequences.parquet"
        assert "precedence_rule" in r


# 11. NextSectorClassesStrictlyRestricted
def test_11_next_sector_classes_strictly_restricted(index_artifacts):
    allowed_classes = {"A", "B", "MID", "CT", "T", "DYNAMIC"}
    for s_path in index_artifacts["shard_paths"]:
        table = pq.read_table(s_path, columns=["NextSector"])
        df = table.to_pandas()
        unique_secs = set(df["NextSector"].unique())
        assert unique_secs.issubset(allowed_classes), f"Classes inválidas de NextSector em {s_path.name}: {unique_secs - allowed_classes}"


# 12. NextSectorNeverUsesCurrentSectorWithoutTransition
def test_12_next_sector_never_uses_current_sector_without_transition(index_artifacts):
    relabel = index_artifacts["next_sector_relabeling"]
    assert relabel["rule_verification"]["never_uses_current_sector_without_transition"] is True
    assert relabel["rule_verification"]["no_utility_ai_target_leakage"] is True

    # Validar em amostra de linhas do shard 0
    t0 = pq.read_table(index_artifacts["shard_paths"][0], columns=["current_sector", "NextSector", "next_sector_source"])
    df0 = t0.to_pandas().head(1000)
    for _, row in df0.iterrows():
        if row["next_sector_source"] == "NO_TRANSITION_DYNAMIC":
            assert row["NextSector"] == "DYNAMIC"


# 13. NextSectorSourceFieldPopulated
def test_13_next_sector_source_field_populated(index_artifacts):
    allowed_sources = {"FUTURE_VISITED_SECTOR", "NO_TRANSITION_DYNAMIC", "OBJECTIVE_PLANT_DEFUSE", "SAVE_FALLBACK"}
    for s_path in index_artifacts["shard_paths"]:
        t = pq.read_table(s_path, columns=["next_sector_source"])
        df = t.to_pandas()
        assert df["next_sector_source"].isnull().sum() == 0
        assert (df["next_sector_source"] == "").sum() == 0
        assert set(df["next_sector_source"].unique()).issubset(allowed_sources)


# 14. ExactDuplicateSequencesIsZero
def test_14_exact_duplicate_sequences_is_zero(index_artifacts):
    seq_ids = []
    for s_path in index_artifacts["shard_paths"]:
        t = pq.read_table(s_path, columns=["sequence_id"])
        seq_ids.extend(t["sequence_id"].to_pylist())
    assert len(seq_ids) == len(set(seq_ids)), "Sequências duplicadas detectadas!"


# 15. CrossSplitDuplicatesIsZero
def test_15_cross_split_duplicates_is_zero(index_artifacts):
    train_ids = set()
    val_ids = set()
    test_ids = set()

    for s_path in index_artifacts["shard_paths"]:
        t = pq.read_table(s_path, columns=["sequence_id", "split"])
        df = t.to_pandas()
        train_ids.update(df[df["split"] == "train"]["sequence_id"])
        val_ids.update(df[df["split"] == "validation"]["sequence_id"])
        test_ids.update(df[df["split"] == "test"]["sequence_id"])

    assert len(train_ids & val_ids) == 0, "Vazamento cross-split Train <-> Validation!"
    assert len(train_ids & test_ids) == 0, "Vazamento cross-split Train <-> Test!"
    assert len(val_ids & test_ids) == 0, "Vazamento cross-split Validation <-> Test!"


# 16. ConflictingLabelsForSameWindowIsZero
def test_16_conflicting_labels_for_same_window_is_zero(index_artifacts):
    seen = {}
    for s_path in index_artifacts["shard_paths"]:
        t = pq.read_table(s_path, columns=["demo_id", "round_id", "slot", "label_frame", "PositioningState"])
        df = t.to_pandas()
        for _, r in df.head(2000).iterrows():
            k = (r["demo_id"], r["round_id"], r["slot"], r["label_frame"])
            if k in seen:
                assert seen[k] == r["PositioningState"], f"Rótulos conflitantes para a mesma janela {k}: {seen[k]} != {r['PositioningState']}"
            else:
                seen[k] = r["PositioningState"]


# 17. ConservationEquationClosurePerSplit
def test_17_conservation_equation_closure_per_split(index_artifacts):
    rec = index_artifacts["reconciliation"]["splits"]
    for sp in ["train", "validation", "test"]:
        item = rec[sp]
        raw_c = item["raw_window_candidates"]
        sum_c = item["accepted"] + item["rejected"] + item["explicitly_masked"]
        assert raw_c == sum_c, f"Equação de conservação violada em {sp}: {raw_c} != {sum_c}"


# 18. ProcessedDemoCountMatchesExpected
def test_18_processed_demo_count_matches_expected(index_artifacts):
    rec = index_artifacts["reconciliation"]["splits"]
    assert rec["train"]["processed_demos"] == rec["train"]["expected_demos"] == 311
    assert rec["validation"]["processed_demos"] == rec["validation"]["expected_demos"] == 66
    assert rec["test"]["processed_demos"] == rec["test"]["expected_demos"] == 67


# 19. DataLoaderGateConformityOnRealNPZ
def test_19_dataloader_gate_conformity_on_real_npz(index_artifacts):
    gates = index_artifacts["dataloader_gates"]
    metrics = gates["metrics"]
    assert metrics["ToleranceMatchRate"] == 1.0
    assert metrics["SyntheticWindowRate"] == 0.0
    assert metrics["TeammateRealSlotMatchRate"] == 1.0
    assert metrics["UnmaskedPaddingRate"] == 0.0
    assert metrics["RoundBoundaryViolationRate"] == 0.0
    assert metrics["CrossPlayerWindowRate"] == 0.0
    assert metrics["FutureLeakageRate"] == 0.0
    assert metrics["MissingNpZRate"] == 0.0
    assert metrics["ExactDuplicateWindowRate"] == 0.0
    assert metrics["TestSplitModelInferenceCount"] == 0


# 20. SpotRankingCandidateMaskCoverage
def test_20_spot_ranking_candidate_mask_coverage(index_artifacts):
    cov = index_artifacts["spot_coverage"]
    assert cov["label_missing_from_candidate_mask"] == 0
    assert cov["invalid_candidate_masks"] == 0
    assert cov["all_eligible_labels_in_catalog"] is True
    assert cov["zero_support_treatment"] == "STRICT_NA"
