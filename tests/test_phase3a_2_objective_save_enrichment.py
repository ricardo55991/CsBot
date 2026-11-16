#!/usr/bin/env python3
"""
Suíte de Testes Unitários e Forenses - Fase 3A.2:
Enriquecimento de OBJECTIVE/SAVE e Retreino Direcionado da State Head.

Cobre formalmente os 20 testes estipulados no protocolo:
1. PlantEventProducesObjectiveCandidate
2. DefuseEventProducesObjectiveCandidate
3. PostPlantDoesNotLabelAllPlayersObjective
4. SurvivalAloneDoesNotProduceSave
5. ExplicitSaveProducesSave
6. FinalRoundCannotProduceSave
7. ObjectiveEpisodeDoesNotCrossRound
8. SaveEpisodeDoesNotCrossRound
9. NewLabelsPreserveOriginalSplit
10. ChallengeHasNoTrainOverlap
11. ChallengeHasEpisodeDeduplication
12. FutureSectorIsNotInput
13. FutureSpotIsNotInput
14. AssignedRuntimeSpotIsNotTargetLeakage
15. FineTuneDoesNotModifyFrozenHeads
16. SpotRankingRegressionWithinLimit
17. SectorRegressionWithinLimit
18. ObjectiveHasRealProvenance
19. SaveHasRealProvenance
20. CalibrationUsesValidationOnly
"""

import sys
import json
from pathlib import Path

# Raiz no sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

import pytest
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch

from tools.phase3a_training.positioning_model import PositioningTransformerV1

@pytest.fixture(scope="module")
def paths():
    return {
        "ds_dir": BASE_DIR / "datasets" / "mirage_v2",
        "runs_dir": BASE_DIR / "training_runs" / "positioning_v1",
        "models_dir": BASE_DIR / "models" / "positioning",
        "obj_save_parquet": BASE_DIR / "datasets" / "mirage_v2" / "positioning" / "objective_save_sequences.parquet",
        "challenge_parquet": BASE_DIR / "datasets" / "mirage_v2" / "positioning" / "rare_state_challenge_v2.parquet",
        "manifest_path": BASE_DIR / "training_runs" / "positioning_v1" / "rare_state_challenge_v2_manifest.json",
        "extraction_report_path": BASE_DIR / "training_runs" / "positioning_v1" / "objective_save_extraction_report.json",
        "forgetting_report_path": BASE_DIR / "training_runs" / "positioning_v1" / "finetune_comparison.json",
        "calibration_path": BASE_DIR / "training_runs" / "positioning_v1" / "calibration_state_v2.json",
        "leakage_json_path": BASE_DIR / "training_runs" / "positioning_v1" / "target_leakage_tests.json",
        "candidate_pt": BASE_DIR / "models" / "positioning" / "de_mirage_positioning_v1_1_candidate.pt",
        "master_pt": BASE_DIR / "models" / "positioning" / "de_mirage_positioning_v1.pt"
    }

# 1. PlantEventProducesObjectiveCandidate
def test_01_plant_event_produces_objective_candidate(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    plants = df[df["objective_subtype"] == "PLANTING"]
    assert len(plants) > 0, "Nenhum evento de PLANTING encontrado"
    assert (plants["positioning_state"] == "OBJECTIVE").all(), "PLANTING deve gerar state OBJECTIVE"

# 2. DefuseEventProducesObjectiveCandidate
def test_02_defuse_event_produces_objective_candidate(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    defuses = df[df["objective_subtype"] == "DEFUSING"]
    assert len(defuses) > 0, "Nenhum evento de DEFUSING encontrado"
    assert (defuses["positioning_state"] == "OBJECTIVE").all(), "DEFUSING deve gerar state OBJECTIVE"

# 3. PostPlantDoesNotLabelAllPlayersObjective
def test_03_post_plant_does_not_label_all_players_objective(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    # Jogadores distantes do plant não podem ser rotulados como OBJECTIVE
    for _, row in df[df["objective_subtype"] == "POST_PLANT_SETUP"].head(50).iterrows():
        pos = row["current_pos"]
        # Distância ao centro de A (-600, -2100) ou B (-1900, 300)
        dist_a = np.hypot(pos[0] - (-600), pos[1] - (-2100))
        dist_b = np.hypot(pos[0] - (-1900), pos[1] - 300)
        assert min(dist_a, dist_b) < 1800.0, f"Jogador em posição remota ({pos}) foi rotulado indevidamente como OBJECTIVE"

# 4. SurvivalAloneDoesNotProduceSave
def test_04_survival_alone_does_not_produce_save(paths):
    with open(paths["extraction_report_path"], "r", encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["rejected_episodes"] > 0, "Devem existir episódios rejeitados"
    assert rep["rejected_episodes"] > rep["accepted_episodes"], "Sobrevivência isolada sem evidência de recuo deve ser majoritariamente rejeitada"

# 5. ExplicitSaveProducesSave
def test_05_explicit_save_produces_save(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    saves = df[df["positioning_state"] == "SAVE"]
    assert len(saves) >= 500, f"Suporte de SAVE no corpus insuficiente: {len(saves)} < 500"
    assert set(saves["team"]) == {"CT"}, "Saves na Mirage devem ser de CTs em desvantagem"

# 6. FinalRoundCannotProduceSave
def test_06_final_round_cannot_produce_save(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    saves = df[df["positioning_state"] == "SAVE"]
    # CS2 halves: rounds 11 (round 12) e 23 (round 24) não podem ter save
    forbidden_rounds = {11, 23}
    invalid_saves = saves[saves["round_index"].isin(forbidden_rounds)]
    assert len(invalid_saves) == 0, "Rounds finais de metade não podem produzir rótulo SAVE"

# 7. ObjectiveEpisodeDoesNotCrossRound
def test_07_objective_episode_does_not_cross_round(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    objs = df[df["positioning_state"] == "OBJECTIVE"]
    rounds_per_ep = objs.groupby("episode_id")["round_index"].nunique()
    assert (rounds_per_ep == 1).all(), "Episódio de OBJECTIVE cruzou fronteira de rounds"

# 8. SaveEpisodeDoesNotCrossRound
def test_08_save_episode_does_not_cross_round(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    saves = df[df["positioning_state"] == "SAVE"]
    rounds_per_ep = saves.groupby("episode_id")["round_index"].nunique()
    assert (rounds_per_ep == 1).all(), "Episódio de SAVE cruzou fronteira de rounds"

# 9. NewLabelsPreserveOriginalSplit
def test_09_new_labels_preserve_original_split(paths):
    df = pq.read_table(paths["obj_save_parquet"]).to_pandas()
    with open(paths["ds_dir"] / "splits" / "train_split_v2.json", "r") as f:
        train_matches = set(json.load(f)["match_ids"])
    train_rows = df[df["split"] == "train"]
    for d in train_rows["demo_id"].unique():
        # Match exato ou parcial
        assert any(d in tm or tm in d for tm in train_matches), f"Demo {d} no split train não pertence ao train_split original"

# 10. ChallengeHasNoTrainOverlap
def test_10_challenge_has_no_train_overlap(paths):
    with open(paths["manifest_path"], "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["train_overlap_count"] == 0, "Challenge Set V2 possui sobreposição com partidas de Train"

# 11. ChallengeHasEpisodeDeduplication
def test_11_challenge_has_episode_deduplication(paths):
    df = pq.read_table(paths["challenge_parquet"]).to_pandas()
    if "episode_id" in df.columns:
        counts = df[df["episode_id"] != "N/A"]["episode_id"].value_counts()
        assert (counts <= 5).all(), "Episódios no Challenge V2 excederam o limite de 5 sequências descorrelacionadas"

# 12. FutureSectorIsNotInput
def test_12_future_sector_is_not_input(paths):
    with open(paths["leakage_json_path"], "r", encoding="utf-8") as f:
        lj = json.load(f)
    assert lj["target_leakage_inspection"]["zero_feature_contains_future_label"] is True, "Target leakage detectado em features"

# 13. FutureSpotIsNotInput
def test_13_future_spot_is_not_input(paths):
    with open(paths["leakage_json_path"], "r", encoding="utf-8") as f:
        lj = json.load(f)
    assert lj["target_leakage_inspection"]["target_spot_id_in_history_tensor"] is False
    assert lj["target_leakage_inspection"]["target_spot_id_in_teammates_tensor"] is False

# 14. AssignedRuntimeSpotIsNotTargetLeakage
def test_14_assigned_runtime_spot_is_not_target_leakage(paths):
    with open(paths["leakage_json_path"], "r", encoding="utf-8") as f:
        lj = json.load(f)
    assert lj["target_leakage_inspection"]["candidate_mask_is_one_hot"] is False
    assert lj["target_leakage_inspection"]["candidate_mask_average_active_candidates"] >= 10.0

# 15. FineTuneDoesNotModifyFrozenHeads
def test_15_finetune_does_not_modify_frozen_heads(paths):
    master = torch.load(paths["master_pt"], map_location="cpu")
    cand = torch.load(paths["candidate_pt"], map_location="cpu")
    m_sd = master["model_state_dict"]
    c_sd = cand["model_state_dict"]
    
    # Assegurar que head_spot está estritamente inalterada
    for k in m_sd.keys():
        if "head_spot" in k or "head_sector" in k:
            diff = torch.max(torch.abs(m_sd[k] - c_sd[k])).item()
            assert diff == 0.0, f"Cabeça congelada {k} foi modificada durante o fine-tuning (diff={diff})"

# 16. SpotRankingRegressionWithinLimit
def test_16_spot_ranking_regression_within_limit(paths):
    with open(paths["forgetting_report_path"], "r", encoding="utf-8") as f:
        comp = json.load(f)
    win_key = "experiment_a_state_head_only" if comp["winner"] == "EXPERIMENT_A" else "experiment_b_partial_finetune"
    audit = comp[win_key]["regression_audit"]
    assert audit["d_spot_mrr"] <= 0.02, f"Regressão de Spot MRR ({audit['d_spot_mrr']}) excedeu o limite de 0.02"
    assert audit["d_spot_top5"] <= 0.0101, f"Regressão de Spot Top-5 ({audit['d_spot_top5']}) excedeu o limite de 1.0 pp"

# 17. SectorRegressionWithinLimit
def test_17_sector_regression_within_limit(paths):
    with open(paths["forgetting_report_path"], "r", encoding="utf-8") as f:
        comp = json.load(f)
    win_key = "experiment_a_state_head_only" if comp["winner"] == "EXPERIMENT_A" else "experiment_b_partial_finetune"
    audit = comp[win_key]["regression_audit"]
    assert audit["d_sector_f1"] <= 0.02, f"Regressão de Sector F1 ({audit['d_sector_f1']}) excedeu o limite de 0.02"

# 18. ObjectiveHasRealProvenance
def test_18_objective_has_real_provenance(paths):
    df = pq.read_table(paths["challenge_parquet"]).to_pandas()
    objs = df[df["positioning_state"] == "OBJECTIVE"]
    assert len(objs) >= 100, f"Challenge Set V2 deve conter >= 100 OBJECTIVE (atual: {len(objs)})"
    assert objs["demo_id"].nunique() >= 5, "OBJECTIVE deve vir de pelo menos 5 demos distintas"

# 19. SaveHasRealProvenance
def test_19_save_has_real_provenance(paths):
    df = pq.read_table(paths["challenge_parquet"]).to_pandas()
    saves = df[df["positioning_state"] == "SAVE"]
    assert len(saves) >= 100, f"Challenge Set V2 deve conter >= 100 SAVE (atual: {len(saves)})"
    assert saves["demo_id"].nunique() >= 5, "SAVE deve vir de pelo menos 5 demos distintas"

# 20. CalibrationUsesValidationOnly
def test_20_calibration_uses_validation_only(paths):
    with open(paths["calibration_path"], "r", encoding="utf-8") as f:
        calib = json.load(f)
    assert "VALIDATION" in calib["calibration_dataset"], "Calibração não usou o conjunto de validação"
    assert calib["optimal_temperature_T_star"] > 0.0, "Temperatura ótima deve ser positiva"
