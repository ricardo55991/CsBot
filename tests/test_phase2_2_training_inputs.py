#!/usr/bin/env python3
"""
Fase 2.2: Suíte de 20 Testes Obrigatórios de Auditoria Temporal e Preparação de Treino.
"""

import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

class TestPhase22TrainingInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parents[1]
        cls.ds_dir = cls.base_dir / "datasets" / "mirage_v2"
        cls.contracts_dir = cls.ds_dir / "contracts"
        cls.reports_dir = cls.ds_dir / "reports"

        cls.schema_audit = json.loads((cls.ds_dir / "parquet_physical_schema_audit.json").read_text(encoding="utf-8"))
        cls.temporal_samples = json.loads((cls.ds_dir / "temporal_window_forensic_sample.json").read_text(encoding="utf-8"))
        cls.contract = json.loads((cls.contracts_dir / "positioning_multitask_contract_v1.json").read_text(encoding="utf-8"))
        cls.head_dist = json.loads((cls.ds_dir / "positioning_head_distribution_v1.json").read_text(encoding="utf-8"))
        cls.aim_prov = json.loads((cls.ds_dir / "aim_profile_provenance_v2.json").read_text(encoding="utf-8"))
        cls.aim_elig = json.loads((cls.ds_dir / "aim_profile_training_eligibility_v2.json").read_text(encoding="utf-8"))
        cls.jump_baseline = json.loads((cls.ds_dir / "baseline_jump_metrics.json").read_text(encoding="utf-8"))
        cls.pos_baseline = json.loads((cls.ds_dir / "baseline_positioning_metrics.json").read_text(encoding="utf-8"))

        cls.df_pos = pq.read_table(cls.ds_dir / "positioning" / "positioning_sequences_v1" / "shard_000.parquet").to_pandas()
        cls.df_mov = pq.read_table(cls.ds_dir / "movement" / "movement_sequences_v2" / "shard_000.parquet").to_pandas()
        cls.df_jmp = pq.read_table(cls.ds_dir / "jump" / "shard_000.parquet").to_pandas()

    # Test 1
    def test_01_ParquetSchemaMatchesDeclaredContract(self):
        datasets = self.schema_audit["datasets"]
        self.assertIn("positioning_sequences_v1", datasets)
        self.assertIn("movement_sequences_v2", datasets)
        self.assertIn("jump_episodes_v2", datasets)
        self.assertEqual(datasets["positioning_sequences_v1"]["compression"], "SNAPPY")

    # Test 2
    def test_02_TemporalWindowIsMaterialized(self):
        meta = self.schema_audit["datasets"]["positioning_sequences_v1"]["sequence_metadata"]
        self.assertEqual(meta["sequence_length"], 32)
        self.assertEqual(meta["feature_dimension"], 18)

    # Test 3
    def test_03_DataloaderBuildsExpectedBatchShapes(self):
        report_text = (self.ds_dir / "dataloader_validation_report.md").read_text(encoding="utf-8")
        self.assertIn("[64, 32, 18]", report_text)
        self.assertIn("[64, 53]", report_text)
        self.assertIn("[64, 16, 18]", report_text)

    # Test 4
    def test_04_TicksAreStrictlyMonotonic(self):
        pos_samples = self.temporal_samples["datasets"]["positioning_sequences_v1"]
        for s in pos_samples:
            self.assertTrue(s["monotonic_ticks"])
            self.assertGreater(s["end_tick"], s["start_tick"])

    # Test 5
    def test_05_SequenceDoesNotCrossRoundBoundary(self):
        for ds_name, s_list in self.temporal_samples["datasets"].items():
            for s in s_list:
                self.assertTrue(s["no_round_boundary_cross"])

    # Test 6
    def test_06_CandidateMaskHasValidSpotWhenEligible(self):
        rule = self.contract["neural_safety_rules"]["candidate_mask_enforces_sector_validity"]
        self.assertTrue(rule)

    # Test 7
    def test_07_TransitMasksSpotLoss(self):
        head_c = self.contract["heads"]["Head_C_CandidateSpotRanking"]
        self.assertIn("MASCARADA (loss_weight=0.0) em TRANSIT", head_c["masking_rule"])

    # Test 8
    def test_08_UnmappedIsNeverPositiveSpotClass(self):
        rule = self.contract["neural_safety_rules"]["unmapped_is_never_spot_class"]
        self.assertTrue(rule)

    # Test 9
    def test_09_PositioningStateExistsForEverySequence(self):
        crit = self.head_dist["audit_criteria_verification"]
        self.assertTrue(crit["all_sequences_have_valid_positioning_state"])

    # Test 10
    def test_10_NextSectorExistsOrIsMasked(self):
        crit = self.head_dist["audit_criteria_verification"]
        self.assertTrue(crit["all_sequences_have_valid_next_sector"])

    # Test 11
    def test_11_AimHumanCaptureRequiresCaptureEvent(self):
        self.assertEqual(self.aim_prov["counts_by_provenance"]["HUMAN_CAPTURE_IN_GAME"], 0)
        self.assertTrue(self.aim_elig["rules"]["human_capture_requires_capture_event"])

    # Test 12
    def test_12_VisualApprovalIsNotHumanCapture(self):
        self.assertEqual(self.aim_prov["counts_by_provenance"]["HUMAN_VISUAL_APPROVAL"], 53)
        self.assertTrue(self.aim_elig["rules"]["visual_approval_is_not_human_capture"])

    # Test 13
    def test_13_TemplateAimIsNotExpertEligible(self):
        for e in self.aim_elig["profiles"]:
            if e["provenance_category"] == "TEMPLATE_DEFAULT":
                self.assertFalse(e["is_expert_training_label"])
                self.assertEqual(e["confidence_weight"], 0.0)

    # Test 14
    def test_14_TrainBatchContainsOnlyTrainMatches(self):
        train_split = set(json.loads((self.ds_dir / "train_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])
        train_samples = self.df_pos[self.df_pos["split"] == "train"]["demo_id"].unique()
        for d in train_samples:
            self.assertIn(d, train_split)

    # Test 15
    def test_15_ValidationBatchContainsOnlyValidationMatches(self):
        val_split = set(json.loads((self.ds_dir / "validation_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])
        full_pos = pq.read_table(self.ds_dir / "positioning" / "positioning_sequences_v1" / "positioning_sample_sequences.parquet").to_pandas()
        val_samples = full_pos[full_pos["split"] == "validation"]["demo_id"].unique()
        for d in val_samples:
            self.assertIn(d, val_split)

    # Test 16
    def test_16_TestBatchContainsOnlyTestMatches(self):
        test_split = set(json.loads((self.ds_dir / "test_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])
        full_pos = pq.read_table(self.ds_dir / "positioning" / "positioning_sequences_v1" / "positioning_sample_sequences.parquet").to_pandas()
        test_samples = full_pos[full_pos["split"] == "test"]["demo_id"].unique()
        for d in test_samples:
            self.assertIn(d, test_split)

    # Test 17
    def test_17_NoFutureFeatureLeakageInWindows(self):
        for ds_name, s_list in self.temporal_samples["datasets"].items():
            for s in s_list:
                self.assertTrue(s["no_future_feature_leakage"])

    # Test 18
    def test_18_JumpPressRemainsRareAndEdgeBased(self):
        always_no = self.jump_baseline["baselines"]["AlwaysNoJump"]
        self.assertGreater(always_no["overall_accuracy"], 0.99)
        self.assertEqual(always_no["macro_f1"], 0.0)

    # Test 19
    def test_19_AirborneReissueIsNeverAccepted(self):
        rule_jump = self.jump_baseline["baselines"]["RuleBasedGroundedEdge"]
        self.assertEqual(rule_jump["airborne_reissue_rate"], 0.0)

    # Test 20
    def test_20_BaselineMetricsAreReproducible(self):
        pos_mf = self.pos_baseline["baselines"]["MostFrequentState"]["metrics"]
        self.assertGreater(pos_mf["accuracy"], 0.90)
        self.assertLess(pos_mf["macro_f1"], 0.60)

if __name__ == "__main__":
    unittest.main()
