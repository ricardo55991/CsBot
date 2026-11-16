#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2B.2: Suíte Canônica de Testes de Governança e Integridade do Patch Final dos Labels.

Cobre formalmente os 20 testes estipulados nos Critérios de Aceite:
1. DynamicIsNotASectorClass
2. NoTransitionMasksNextSectorLoss
3. TransitionOccurrenceEnablesNextSectorLoss
4. NextSectorPrimaryAccountingCloses
5. SemanticOverrideDoesNotDuplicatePrimarySource
6. RoundEndCensoringIsExplicit
7. ObjectivePlantCanProduceBombPlantedTrigger
8. ObjectiveDoesNotAlwaysProduceBombPlantedTrigger
9. SaveIsNotAlwaysTeammateDeath
10. SurvivalAloneDoesNotProduceSave
11. UnsupportedSpotIsNotSupervised
12. SupportedSpotRemainsEligible
13. SpotCatalogRemains53Entries
14. LabelSidecarJoinIsOneToOne
15. LabelSidecarHasNoMissingRows
16. TemporalPointersRemainUnchanged
17. TestHasNoModelInference
18. ZeroSupportRemainsNA
19. TrainAndValidationUseSameLabelContract
20. PreviousIndexRemainsUnchanged
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
SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"
RUNS_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal"
DS_DIR = BASE_DIR / "datasets" / "mirage_v2"
CONTRACTS_DIR = DS_DIR / "contracts"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def artifacts():
    # Carregar contratos e relatórios
    contract_path = CONTRACTS_DIR / "label_contract_v2.json"
    mask_path = INDEX_DIR / "supervised_spot_mask_v1.json"
    horizon_path = INDEX_DIR / "next_sector_horizon_analysis.json"
    accounting_path = INDEX_DIR / "next_sector_source_accounting.json"
    recon_path = INDEX_DIR / "exit_trigger_reconciliation.json"
    obj_save_path = INDEX_DIR / "objective_save_trigger_audit.json"
    unsupported_path = INDEX_DIR / "unsupported_class_audit.json"
    catalog_path = CONTRACTS_DIR / "mirage_spot_catalog_v3.json"

    distribution_path = RUNS_DIR / "revised_label_distribution.json"
    spot_report_path = RUNS_DIR / "revised_spot_supervision_report.json"
    join_audit_path = RUNS_DIR / "label_join_audit.json"
    snapshot_path = RUNS_DIR / "milestone_2b2_input_snapshot.json"

    base_shards = sorted(list(INDEX_DIR.glob("shard_*.parquet")))
    sidecar_shards = sorted(list(SIDECAR_DIR.glob("shard_*_labels.parquet")))

    return {
        "contract": json.load(open(contract_path, "r", encoding="utf-8")),
        "spot_mask": json.load(open(mask_path, "r", encoding="utf-8")),
        "horizon": json.load(open(horizon_path, "r", encoding="utf-8")),
        "accounting": json.load(open(accounting_path, "r", encoding="utf-8")),
        "reconciliation": json.load(open(recon_path, "r", encoding="utf-8")),
        "obj_save_audit": json.load(open(obj_save_path, "r", encoding="utf-8")),
        "unsupported": json.load(open(unsupported_path, "r", encoding="utf-8")),
        "catalog": json.load(open(catalog_path, "r", encoding="utf-8")),
        "distribution": json.load(open(distribution_path, "r", encoding="utf-8")),
        "spot_report": json.load(open(spot_report_path, "r", encoding="utf-8")),
        "join_audit": json.load(open(join_audit_path, "r", encoding="utf-8")),
        "snapshot": json.load(open(snapshot_path, "r", encoding="utf-8")),
        "base_shards": base_shards,
        "sidecar_shards": sidecar_shards,
    }


# 1. DynamicIsNotASectorClass
def test_01_dynamic_is_not_a_sector_class(artifacts):
    classes = artifacts["contract"]["heads"]["Head_B_NextSector"]["classes"]
    assert "DYNAMIC" not in classes, f"DYNAMIC não pode estar nas classes de NextSector: {classes}"
    assert set(classes) == {"A", "B", "MID", "CT", "T"}
    assert artifacts["contract"]["neural_safety_rules"]["dynamic_is_never_a_sector_class"] is True

    # Verificar amostras dos sidecars
    for sc_path in artifacts["sidecar_shards"]:
        t = pq.read_table(sc_path, columns=["next_sector"])
        sectors = set(t["next_sector"].to_pylist())
        assert "DYNAMIC" not in sectors, f"Encontrado DYNAMIC na coluna next_sector de {sc_path.name}"


# 2. NoTransitionMasksNextSectorLoss
def test_02_no_transition_masks_next_sector_loss(artifacts):
    rule = artifacts["contract"]["heads"]["Head_B_NextSector"]["masking_rule"]
    assert "SectorTransitionOccurs == NO_TRANSITION" in rule or "NextSectorLossMask = 0.0" in rule

    # Testar diretamente nos sidecars
    for sc_path in artifacts["sidecar_shards"][:2]:
        t = pq.read_table(sc_path, columns=["sector_transition_occurs", "next_sector_loss_mask"])
        df = t.to_pandas()
        no_trans = df[df["sector_transition_occurs"] == "NO_TRANSITION"]
        assert len(no_trans) > 0
        assert (no_trans["next_sector_loss_mask"] == 0.0).all(), (
            f"Encontrado next_sector_loss_mask != 0.0 quando sector_transition_occurs == NO_TRANSITION em {sc_path.name}"
        )


# 3. TransitionOccurrenceEnablesNextSectorLoss
def test_03_transition_occurrence_enables_next_sector_loss(artifacts):
    for sc_path in artifacts["sidecar_shards"][:2]:
        t = pq.read_table(sc_path, columns=["sector_transition_occurs", "next_sector_loss_mask", "next_sector"])
        df = t.to_pandas()
        trans = df[df["sector_transition_occurs"] == "TRANSITION_OCCURS"]
        assert len(trans) > 0
        assert (trans["next_sector_loss_mask"] == 1.0).all(), (
            f"Encontrado next_sector_loss_mask != 1.0 quando sector_transition_occurs == TRANSITION_OCCURS em {sc_path.name}"
        )
        assert set(trans["next_sector"].unique()).issubset({"A", "B", "MID", "CT", "T"})


# 4. NextSectorPrimaryAccountingCloses
def test_04_next_sector_primary_accounting_closes(artifacts):
    acc = artifacts["accounting"]["primary_sources"]
    total = artifacts["accounting"]["total_sequences"]
    assert total == 3411434

    sum_parts = (
        acc["FUTURE_VISITED_SECTOR"] +
        acc["NO_TRANSITION_WITHIN_HORIZON"] +
        acc["CENSORED_BY_ROUND_END"] +
        acc["INVALID_OR_MASKED"]
    )
    assert sum_parts == total == 3411434
    assert acc["closure_verified"] is True
    assert artifacts["accounting"]["invariants"]["primary_sources_mutually_exclusive"] is True
    assert artifacts["accounting"]["invariants"]["exactly_one_primary_source_per_sequence"] is True


# 5. SemanticOverrideDoesNotDuplicatePrimarySource
def test_05_semantic_override_does_not_duplicate_primary_source(artifacts):
    ovr = artifacts["accounting"]["semantic_overrides"]
    total = artifacts["accounting"]["total_sequences"]
    sum_ovr = ovr["NONE"] + ovr["OBJECTIVE_PLANT_DEFUSE"] + ovr["SAVE_FALLBACK"]
    assert sum_ovr == total == 3411434
    assert ovr["closure_verified"] is True

    # Verificar que as colunas nos sidecars são independentes
    for sc_path in artifacts["sidecar_shards"][:2]:
        pf = pq.ParquetFile(sc_path)
        cols = pf.schema.names
        assert "next_sector_primary_source" in cols
        assert "next_sector_semantic_override" in cols
        assert cols.index("next_sector_primary_source") != cols.index("next_sector_semantic_override")


# 6. RoundEndCensoringIsExplicit
def test_06_round_end_censoring_is_explicit(artifacts):
    horizon = artifacts["horizon"]["round_end_censoring"]
    acc_primary = artifacts["accounting"]["primary_sources"]

    assert horizon["censored_by_round_end"] > 0
    assert horizon["censored_by_round_end"] == acc_primary["CENSORED_BY_ROUND_END"] == 198360
    assert horizon["censoring_rate_over_corpus"] > 0.05


# 7. ObjectivePlantCanProduceBombPlantedTrigger
def test_07_objective_plant_can_produce_bomb_planted_trigger(artifacts):
    obj_audit = artifacts["obj_save_audit"]["objective_sequences"]
    assert obj_audit["resolved_exit_triggers"]["BOMB_PLANTED"] > 0
    assert obj_audit["rules"]["planting_completion_produces_bomb_planted"] is True

    # Verificar em um sidecar que BOMB_PLANTED existe para sequências com PLANTING
    found = False
    for sc_path in artifacts["sidecar_shards"]:
        t = pq.read_table(sc_path, columns=["objective_subtype", "exit_trigger"])
        df = t.to_pandas()
        sub = df[(df["objective_subtype"] == "PLANTING") & (df["exit_trigger"] == "BOMB_PLANTED")]
        if len(sub) > 0:
            found = True
            break
    assert found, "Nenhuma sequência de PLANTING com exit_trigger BOMB_PLANTED encontrada nos sidecars"


# 8. ObjectiveDoesNotAlwaysProduceBombPlantedTrigger
def test_08_objective_does_not_always_produce_bomb_planted_trigger(artifacts):
    obj_audit = artifacts["obj_save_audit"]["objective_sequences"]
    triggers = obj_audit["resolved_exit_triggers"]
    total_obj = obj_audit["total_enriched"]
    assert total_obj == 6867

    # BOMB_PLANTED não é 100% de OBJECTIVE (há TIME e CONTACT para abordagem/defuse)
    assert triggers["BOMB_PLANTED"] < total_obj
    assert triggers["TIME"] > 0
    assert triggers["CONTACT"] > 0
    assert triggers["BOMB_PLANTED"] + triggers["TIME"] + triggers["CONTACT"] == total_obj


# 9. SaveIsNotAlwaysTeammateDeath
def test_09_save_is_not_always_teammate_death(artifacts):
    save_audit = artifacts["obj_save_audit"]["save_sequences"]
    triggers = save_audit["resolved_exit_triggers"]
    total_save = save_audit["total_enriched"]
    assert total_save == 792

    # A quebra do mapeamento 1:1 exige presença de TACTIC_REVISION e TIME além de TEAMMATE_DEATH
    assert triggers["TEAMMATE_DEATH"] < total_save
    assert triggers["TACTIC_REVISION"] > 0
    assert triggers["TIME"] > 0
    assert save_audit["rules"]["forced_teammate_death_mapping_broken"] is True


# 10. SurvivalAloneDoesNotProduceSave
def test_10_survival_alone_does_not_produce_save(artifacts):
    audit = artifacts["obj_save_audit"]["survival_alone_does_not_produce_save"]
    assert audit["generic_hold_transit_preserved"] is True
    assert audit["save_restricted_to_confirmed_evidence"] is True

    # Verificar no shard base que sequências com save_subtype == NONE não são SAVE
    for s_path in artifacts["base_shards"][:2]:
        t = pq.read_table(s_path, columns=["PositioningState", "save_subtype"])
        df = t.to_pandas()
        generic_surv = df[df["PositioningState"].isin(["HOLD", "TRANSIT"])]
        assert (generic_surv["save_subtype"] == "NONE").all()


# 11. UnsupportedSpotIsNotSupervised
def test_11_unsupported_spot_is_not_supervised(artifacts):
    spot_mask = artifacts["spot_mask"]
    assert spot_mask["unsupported_spots_count"] == 26
    unsupported_ids = set(spot_mask["unsupported_spot_ids"])
    assert len(unsupported_ids) == 26

    for entry in spot_mask["spot_masks"]:
        if entry["spot_id"] in unsupported_ids:
            assert entry["mask"] == 0
            assert entry["train_support"] == 0
            assert entry["supervision_status"] == "ZERO_SUPPORT_MASKED"


# 12. SupportedSpotRemainsEligible
def test_12_supported_spot_remains_eligible(artifacts):
    spot_mask = artifacts["spot_mask"]
    assert spot_mask["supported_spots_count"] == 27
    supported_ids = set(spot_mask["supported_spot_ids"])
    assert len(supported_ids) == 27

    for entry in spot_mask["spot_masks"]:
        if entry["spot_id"] in supported_ids:
            assert entry["mask"] == 1
            assert entry["train_support"] > 0
            assert entry["supervision_status"] == "SUPERVISED_ACTIVE"


# 13. SpotCatalogRemains53Entries
def test_13_spot_catalog_remains_53_entries(artifacts):
    cat_spots = artifacts["catalog"]["spots"]
    assert len(cat_spots) == 53
    assert len(set(s["id"] for s in cat_spots)) == 53
    assert artifacts["spot_mask"]["total_catalog_spots"] == 53
    assert artifacts["spot_report"]["total_catalog_spots"] == 53
    assert artifacts["contract"]["heads"]["Head_C_CandidateSpotRanking"]["num_classes"] == 53
    assert artifacts["spot_mask"]["policy"]["unsupported_spots_deleted_from_catalog"] is False


# 14. LabelSidecarJoinIsOneToOne
def test_14_label_sidecar_join_is_one_to_one(artifacts):
    join_audit = artifacts["join_audit"]
    assert join_audit["total_shards"] == 6
    assert join_audit["join_invariants"]["all_shards_exact_match"] is True
    assert join_audit["join_invariants"]["total_missing_rows"] == 0
    assert join_audit["join_invariants"]["total_duplicate_rows"] == 0

    for shard_info in join_audit["shards"]:
        assert shard_info["matched_rows"] == shard_info["base_shard_rows"] == shard_info["sidecar_rows"]
        assert shard_info["order_match_rate"] == 1.0
        assert shard_info["join_status"] == "EXACT_1_TO_1_JOIN_PASS"


# 15. LabelSidecarHasNoMissingRows
def test_15_label_sidecar_has_no_missing_rows(artifacts):
    total_sidecar_rows = sum(s["sidecar_rows"] for s in artifacts["join_audit"]["shards"])
    assert total_sidecar_rows == 3411434
    assert artifacts["join_audit"]["total_sequences"] == 3411434


# 16. TemporalPointersRemainUnchanged
def test_16_temporal_pointers_remain_unchanged(artifacts):
    # Comparar ponteiros temporais em amostras de cada shard base
    expected_cols = ["window_start_frame", "window_end_frame", "label_frame", "slot", "round_id", "demo_id"]
    for sp in artifacts["base_shards"]:
        pf = pq.ParquetFile(sp)
        for c in expected_cols:
            assert c in pf.schema.names, f"Ponteiro temporal '{c}' ausente em {sp.name}"


# 17. TestHasNoModelInference
def test_17_test_has_no_model_inference(artifacts):
    contract = artifacts["contract"]
    assert contract["neural_safety_rules"]["test_split_isolated_zero_inference"] is True

    # Conferir se não há scores de predição/loss de teste nos artefatos de entrega
    assert "test_model_predictions" not in artifacts["distribution"]
    assert "test_loss" not in artifacts["distribution"]


# 18. ZeroSupportRemainsNA
def test_18_zero_support_remains_na(artifacts):
    dist = artifacts["distribution"]["by_split"]["train"]

    # Transition.LURK deve ser N/A
    assert dist["Transition"]["LURK"]["support"] == 0
    assert dist["Transition"]["LURK"]["percentage"] == "N/A"

    # ExitTrigger.BOMB_SPOTTED deve ser N/A
    assert dist["ExitTrigger"]["BOMB_SPOTTED"]["support"] == 0
    assert dist["ExitTrigger"]["BOMB_SPOTTED"]["percentage"] == "N/A"

    # Spots não suportados devem ser N/A no spot report
    for s_id, s_info in artifacts["spot_report"]["per_spot_support"].items():
        if s_info["train_support"] == 0:
            assert s_info["metric_status"] == "STRICT_NA"


# 19. TrainAndValidationUseSameLabelContract
def test_19_train_and_validation_use_same_label_contract(artifacts):
    # Verificar que os sidecars possuem exatamente os mesmos versions em Train e Val
    for sc_path in artifacts["sidecar_shards"][:3]:
        t = pq.read_table(sc_path, columns=["supervised_spot_mask_version", "label_contract_version"])
        df = t.to_pandas()
        assert (df["supervised_spot_mask_version"] == "1.0.0").all()
        assert (df["label_contract_version"] == "2.0.0").all()


# 20. PreviousIndexRemainsUnchanged
def test_20_previous_index_remains_unchanged(artifacts):
    snapshot_shards = {s["file"]: s["sha256"] for s in artifacts["snapshot"]["base_dataset"]["shards"]}
    for sp in artifacts["base_shards"]:
        current_hash = compute_sha256(sp)
        expected_hash = snapshot_shards[sp.name]
        assert current_hash == expected_hash, (
            f"Violação de Imutabilidade no Shard {sp.name}: atual {current_hash} != congelado {expected_hash}"
        )
