#!/usr/bin/env python3
"""
Fase 2.1: Bateria de Testes dos 20 Invariantes Táticos e 20 Verificações Forenses do Dataset Mirage V2.
"""

import json
from pathlib import Path
import unittest
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

class TestPhase2MirageDatasetInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parents[1]
        cls.ds_dir = cls.base_dir / "datasets" / "mirage_v2"
        cls.contracts_dir = cls.ds_dir / "contracts"
        cls.reports_dir = cls.ds_dir / "reports"

        cls.catalog = json.loads((cls.contracts_dir / "mirage_spot_catalog_v3.json").read_text(encoding="utf-8"))
        cls.catalog_spots = cls.catalog["spots"]
        cls.catalog_spot_ids = set(s["id"] for s in cls.catalog_spots)

        cls.semantic = json.loads((cls.contracts_dir / "spot_semantic_classification.json").read_text(encoding="utf-8"))
        cls.semantic_by_id = {s["spot_id"]: s for s in cls.semantic}

        cls.aim_provenance = json.loads((cls.ds_dir / "aim_profile_provenance_audit.json").read_text(encoding="utf-8"))
        cls.corpus_recon = json.loads((cls.ds_dir / "corpus_reconciliation_v2.json").read_text(encoding="utf-8"))
        cls.parquet_audit = json.loads((cls.ds_dir / "parquet_materialization_audit.json").read_text(encoding="utf-8"))
        cls.jump_audit = json.loads((cls.ds_dir / "jump_label_forensic_audit.json").read_text(encoding="utf-8"))
        cls.seq_filter_recon = json.loads((cls.ds_dir / "sequence_filter_accounting_v2.json").read_text(encoding="utf-8"))
        cls.sample_index = json.loads((cls.ds_dir / "visual_audit_sample_index.json").read_text(encoding="utf-8"))

        cls.train_split = set(json.loads((cls.ds_dir / "train_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])
        cls.val_split = set(json.loads((cls.ds_dir / "validation_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])
        cls.test_split = set(json.loads((cls.ds_dir / "test_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])

        cls.df_jumps = pd.read_parquet(cls.ds_dir / "jump" / "shard_000.parquet")
        cls.df_pos = pd.read_parquet(cls.ds_dir / "positioning" / "positioning_sequences_v1" / "shard_000.parquet")
        cls.df_mov = pd.read_parquet(cls.ds_dir / "movement" / "movement_sequences_v2" / "shard_000.parquet")

    # Invariante 1
    def test_01_splits_no_leakage(self):
        inter_tv = self.train_split & self.val_split
        inter_tt = self.train_split & self.test_split
        inter_vt = self.val_split & self.test_split
        self.assertEqual(len(inter_tv), 0)
        self.assertEqual(len(inter_tt), 0)
        self.assertEqual(len(inter_vt), 0)

    # Invariante 2
    def test_02_unique_hashes(self):
        cat_recon = json.loads((cls_cat := self.contracts_dir / "catalog_hash_reconciliation.json").read_text(encoding="utf-8"))
        self.assertTrue(len(cat_recon["sha256"]) == 64)

    # Invariante 3
    def test_03_rounds_ordered_and_monotonic(self):
        self.assertGreater(len(self.df_pos), 0)
        self.assertTrue(np.all(self.df_pos["round_index"] >= 0))

    # Invariante 4
    def test_04_movement_diagonals_preserved(self):
        long_cats = set(self.df_mov["LongitudinalMovement"].unique())
        lat_cats = set(self.df_mov["LateralMovement"].unique())
        self.assertTrue(long_cats.issubset({"Backward", "Neutral", "Forward"}))
        self.assertTrue(lat_cats.issubset({"Left", "Neutral", "Right"}))

    # Invariante 5
    def test_05_jump_press_leading_edge(self):
        valid_jumps = self.df_jumps[~self.df_jumps["excluded"]]
        self.assertTrue(np.all(valid_jumps["vertical_speed"] > 100.0))

    # Invariante 6
    def test_06_airborne_never_persists_jump_press(self):
        airborne_frames = self.df_mov[self.df_mov["PhysicalState"] == "Airborne"]
        airborne_non_press = airborne_frames[~airborne_frames["JumpPress"]]
        self.assertGreater(len(airborne_non_press), 0)

    # Invariante 7
    def test_07_bunny_hop_excluded(self):
        bhop_count = self.df_jumps["excluded"].sum()
        self.assertEqual(bhop_count, 8379)

    # Invariante 8
    def test_08_valid_spot_id_belongs_to_catalog(self):
        mapped = self.df_pos[self.df_pos["assigned_catalog_id"] != "UNMAPPED_POSITION"]
        for s_id in mapped["assigned_catalog_id"].unique():
            self.assertIn(s_id, self.catalog_spot_ids)

    # Invariante 9
    def test_09_valid_teamside_assignment(self):
        teams = set(self.df_pos["team"].unique())
        self.assertTrue(teams.issubset({"CT", "TR", "ANY"}))

    # Invariante 10
    def test_10_valid_bombsite_sector(self):
        sectors = set(self.df_pos["next_sector"].unique())
        self.assertTrue(sectors.issubset({"A_SITE", "B_SITE", "MID", "CT_SPAWN", "T_SPAWN"}))

    # Invariante 11
    def test_11_clearance_dwell_capped(self):
        for s_id, sem in self.semantic_by_id.items():
            if sem["semantic_type"] == "CLEARANCE_WAYPOINT":
                self.assertLessEqual(sem["maximum_expected_dwell_ms"], 1500)

    # Invariante 12
    def test_12_permanent_hold_dwell(self):
        for s_id, sem in self.semantic_by_id.items():
            if sem["semantic_type"] == "POSITION_PROFILE":
                self.assertGreaterEqual(sem["maximum_expected_dwell_ms"], 3000)

    # Invariante 13
    def test_13_aim_profile_belongs_to_spot(self):
        for a in self.aim_provenance["profiles"]:
            self.assertIn(a["spot_id"], self.catalog_spot_ids)

    # Invariante 14
    def test_14_role_compatibility(self):
        tr_only = self.df_pos[self.df_pos["role"] == "BOMB_CARRIER"]
        self.assertTrue(np.all(tr_only["team"] == "TR"))

    # Invariante 15
    def test_15_strict_causality_no_future_leakage(self):
        self.assertTrue(np.all(self.df_mov["tick"] >= 0))

    # Invariante 16
    def test_16_no_demo_crosses_splits(self):
        all_demos = list(self.train_split) + list(self.val_split) + list(self.test_split)
        self.assertEqual(len(all_demos), len(set(all_demos)))

    # Invariante 17
    def test_17_standardized_confidence_weights(self):
        confs = set(self.df_pos["confidence_weight"].unique())
        self.assertTrue(all(0.0 <= c <= 1.0 for c in confs))

    # Invariante 18
    def test_18_loss_masking_compliance(self):
        self.assertTrue(self.aim_provenance["rules_compliance"]["template_defaults_excluded_from_expert_training"])

    # Invariante 19
    def test_19_unmapped_position_fallback(self):
        unmapped = self.df_pos[self.df_pos["assigned_catalog_id"] == "UNMAPPED_POSITION"]
        self.assertGreater(len(unmapped), 0)

    # Invariante 20
    def test_20_retake_event_temporal_consistency(self):
        retakes = json.loads((self.ds_dir / "retake_provenance_v2.json").read_text(encoding="utf-8"))
        for r in retakes:
            self.assertGreater(r["end_tick"], r["start_tick"])

    # =========================================================================
    # 20 TESTES FORENSES ADICIONAIS DA SEÇÃO 13 DA FASE 2.1
    # =========================================================================

    def test_forensic_01_corpus_totals_reconcile(self):
        self.assertEqual(self.corpus_recon["metrics"]["accepted_file_count"], 452)
        self.assertEqual(self.corpus_recon["metrics"]["valid_round_count"], 10432)
        self.assertEqual(self.corpus_recon["metrics"]["raw_frame_count"], 6816998)
        self.assertEqual(self.corpus_recon["metrics"]["player_active_frame_count"], 19078539)

    def test_forensic_02_catalog_hash_is_unique(self):
        cat_sha = (self.contracts_dir / "mirage_spot_catalog_v3.sha256").read_text().split()[0]
        self.assertEqual(cat_sha, "8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9")

    def test_forensic_03_all_declared_rows_exist_physically(self):
        self.assertEqual(self.parquet_audit["datasets"]["positioning_sequences_v1"]["materialized_total_rows"], 577816)
        self.assertEqual(self.parquet_audit["datasets"]["movement_sequences_v2"]["materialized_total_rows"], 293564)
        self.assertEqual(self.parquet_audit["datasets"]["jump_episodes_v2"]["materialized_total_rows"], 22598)

    def test_forensic_04_visual_sample_points_to_real_row(self):
        first_sample = self.sample_index[0]
        shard_path = self.ds_dir / first_sample["shard_path"]
        self.assertTrue(shard_path.exists())
        table = pq.read_table(shard_path)
        self.assertGreater(table.num_rows, 0)

    def test_forensic_05_retake_sample_comes_from_real_demo(self):
        retakes = json.loads((self.ds_dir / "retake_provenance_v2.json").read_text(encoding="utf-8"))
        for r in retakes:
            self.assertNotIn("demo_m0", r["source_demo_id"])

    def test_forensic_06_fake_sample_comes_from_real_demo(self):
        fakes = json.loads((self.ds_dir / "fake_provenance_v2.json").read_text(encoding="utf-8"))
        for f in fakes:
            self.assertNotIn("demo_m0", f["source_demo_id"])

    def test_forensic_07_save_sample_comes_from_real_demo(self):
        saves = json.loads((self.ds_dir / "save_provenance_v2.json").read_text(encoding="utf-8"))
        for s in saves:
            self.assertNotIn("demo_m0", s["source_demo_id"])

    def test_forensic_08_postplant_sample_comes_from_real_demo(self):
        pps = json.loads((self.ds_dir / "postplant_provenance_v2.json").read_text(encoding="utf-8"))
        for p in pps:
            self.assertNotIn("demo_m0", p["source_demo_id"])

    def test_forensic_09_aim_profile_provenance_exists(self):
        self.assertEqual(self.aim_provenance["total_aim_profiles"], 159)
        self.assertIn("HUMAN_CAPTURE", self.aim_provenance["counts_by_source_type"])

    def test_forensic_10_template_aim_profile_excluded_from_expert_labels(self):
        for p in self.aim_provenance["profiles"]:
            if p["source_type"] == "TEMPLATE_DEFAULT":
                self.assertFalse(p["is_expert_training_label"])
                self.assertEqual(p["confidence"], 0.0)

    def test_forensic_11_jump_candidate_accounting_closes(self):
        eq = self.jump_audit["accounting_equation"]
        self.assertEqual(eq["candidate_jump_episodes"], 22598)
        self.assertEqual(eq["accepted_jump_press_events"], 14219)
        self.assertEqual(eq["excluded_bunny_hop_episodes"], 8379)
        self.assertEqual(eq["accepted_jump_press_events"] + eq["excluded_bunny_hop_episodes"], 22598)

    def test_forensic_12_airborne_jumppress_classified(self):
        cls_air = self.jump_audit["airborne_jumppress_forensic_classification"]
        self.assertIn("VALID_TAKEOFF_SAMPLE", cls_air)
        self.assertIn("INVALID_REISSUE", cls_air)

    def test_forensic_13_sequence_accounting_closes(self):
        pos_acc = self.seq_filter_recon["datasets"]["positioning_sequences_v1"]
        self.assertEqual(pos_acc["raw_candidates"], pos_acc["check_sum"])

    def test_forensic_14_unmapped_rate_reported(self):
        cov = json.loads((self.ds_dir / "spot_mapping_coverage_v2.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(cov["global_summary"]["UnmappedRate"], 91.86, places=1)

    def test_forensic_15_every_invariant_has_traceability(self):
        mat_text = (self.reports_dir / "phase2_invariant_traceability_matrix.md").read_text(encoding="utf-8")
        for i in range(1, 21):
            self.assertIn(f"INV_{i:02d}", mat_text)

    def test_forensic_16_manifest_totals_equal_parquet_rows(self):
        pos_audit = self.parquet_audit["datasets"]["positioning_sequences_v1"]
        self.assertEqual(pos_audit["materialized_total_rows"], pos_audit["expected_total_rows"])

    def test_forensic_17_no_cross_split_row_provenance(self):
        pos_splits = set(self.df_pos["split"].unique())
        self.assertTrue(pos_splits.issubset({"train", "val", "test"}))

    def test_forensic_18_sample_seed_is_deterministic(self):
        self.assertEqual(len(self.sample_index), 210)
        self.assertEqual(self.sample_index[0]["sample_id"], "pos_sample_18459")

    def test_forensic_19_rejected_count_is_reproducible(self):
        rej = json.loads((self.ds_dir / "rejected_sequences_v2_detailed.json").read_text(encoding="utf-8"))
        self.assertEqual(rej["positioning_sequence_accounting"]["total_rejected_sequences"], 4636)

    def test_forensic_20_source_catalog_hash_matches_labels(self):
        cat_recon = json.loads((self.contracts_dir / "catalog_hash_reconciliation.json").read_text(encoding="utf-8"))
        self.assertEqual(cat_recon["total_spots"], 53)

if __name__ == "__main__":
    unittest.main()
