#!/usr/bin/env python3
"""
Compila e gera os artefatos de evidência canônicos do Marco 2B.3:
1. training_runs/positioning_v2_real_temporal/full_training/milestone_2b3_evidence_matrix.json
2. training_runs/positioning_v2_real_temporal/full_training/deliverable_evidence.json
3. deliverable_evidence.json (raiz)
"""

import os
import json
import hashlib
from datetime import datetime, timezone

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_file_info(rel_path):
    norm_path = rel_path.replace("\\", "/")
    if not os.path.exists(norm_path):
        return {
            "relative_path": norm_path,
            "size_bytes": 0,
            "sha256": "PENDING_REPORT_COMPILATION",
            "verified_on_disk": False,
            "nature": "REAL"
        }
    return {
        "relative_path": norm_path,
        "size_bytes": os.path.getsize(norm_path),
        "sha256": compute_sha256(norm_path),
        "verified_on_disk": True,
        "nature": "REAL"
    }

timestamp_now = "2026-11-08T22:15:00Z"

# 21 Entregáveis da Seção 17 do ORIGINAL_REQUEST.md
deliverable_paths = [
    "training_runs/positioning_v2_real_temporal/full_training/input_snapshot.json",
    "training_runs/positioning_v2_real_temporal/full_training/compute_preflight.json",
    "training_runs/positioning_v2_real_temporal/full_training/frozen_training_config.json",
    "training_runs/positioning_v2_real_temporal/full_training/frozen_composite_formula.json",
    "training_runs/positioning_v2_real_temporal/full_training/class_weights.json",
    "training_runs/positioning_v2_real_temporal/full_training/seed_42026/best_checkpoint.pt",
    "training_runs/positioning_v2_real_temporal/full_training/seed_42027/best_checkpoint.pt",
    "training_runs/positioning_v2_real_temporal/full_training/seed_42028/best_checkpoint.pt",
    "training_runs/positioning_v2_real_temporal/full_training/three_seed_comparison.json",
    "training_runs/positioning_v2_real_temporal/full_training/baseline_comparison.json",
    "training_runs/positioning_v2_real_temporal/full_training/temporal_gain_report.json",
    "training_runs/positioning_v2_real_temporal/full_training/collapse_monitoring.json",
    "training_runs/positioning_v2_real_temporal/full_training/best_model_selection.json",
    "training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt",
    "training_runs/positioning_v2_real_temporal/full_training/mathematical_training_audit.json",
    "training_runs/positioning_v2_real_temporal/full_training/data_provenance_training_audit.json",
    "training_runs/positioning_v2_real_temporal/full_training/ml_generalization_audit.json",
    "training_runs/positioning_v2_real_temporal/full_training/adversarial_training_audit.json",
    "training_runs/positioning_v2_real_temporal/full_training/milestone_2b3_evidence_matrix.json",
    "training_runs/positioning_v2_real_temporal/full_training/deliverable_evidence.json",
    "training_runs/positioning_v2_real_temporal/full_training/marco_2b3_final_report.md"
]

deliverables = []
for p in deliverable_paths:
    info = get_file_info(p)
    deliverables.append(info)

evidence_matrix = {
    "schema_version": "1.0.0",
    "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
    "milestone": "Marco 2B.3 - Treinamento Completo do Positioning Transformer Temporal Real",
    "generated_at_utc": timestamp_now,
    "review_stamp": "AGENT_REVIEWED",
    "verdict": "REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL",
    "canonical_milestone_verdict": "REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL",
    "auditor": "Report Author and Evidence Compiler",
    "deliverables_count": len(deliverables),
    "deliverables": deliverables,
    "independent_audits_summary": {
        "data_provenance_and_temporal_integrity": {
            "auditor": "Data and Temporal Auditor (data_auditor_2b3_1)",
            "verdict": "PASS",
            "artifact_path": "training_runs/positioning_v2_real_temporal/full_training/data_provenance_training_audit.json",
            "sha256": "8fda7fca66b40974c53243c20c81752ab3a14db5fc457e4915ddaa61397ff01b"
        },
        "mathematical_and_statistical_integrity": {
            "auditor": "Mathematical and Statistical Auditor (math_auditor_2b3_1)",
            "verdict": "PASS_MATHEMATICAL_INTEGRITY_CONDITIONAL_TARGETS",
            "artifact_path": "training_runs/positioning_v2_real_temporal/full_training/mathematical_training_audit.json",
            "sha256": "8a10f516a82934128dd9dfbfb11e3576bead866a1ae885d1fd9c69548e2180a9"
        },
        "ml_generalization_and_temporal_stability": {
            "auditor": "ML Generalization Auditor (generalization_auditor_2b3_1)",
            "verdict": "CONDITIONAL",
            "artifact_path": "training_runs/positioning_v2_real_temporal/full_training/ml_generalization_audit.json",
            "sha256": "7570e56d8c6437e138e5f0c1123257b7c18a6702bbb793dc53b2b4540f8fe8e0"
        },
        "adversarial_success_and_skeptic": {
            "auditor": "Adversarial Success Auditor (adversarial_auditor_2b3_1)",
            "verdict": "CONDITIONAL",
            "artifact_path": "training_runs/positioning_v2_real_temporal/full_training/adversarial_training_audit.json",
            "sha256": "99a2a0f6af2c78f6d63a1e751c2a2e6a8bb38ec6013339c12cef7bef807209ba"
        }
    },
    "seed_checkpoints": {
        "seed_42026": {
            "path": "training_runs/positioning_v2_real_temporal/full_training/seed_42026/best_checkpoint.pt",
            "sha256": "ac6a528d6a7e05a9a0258fa25c807d57202227ce0b2307848a2692e00d33c319",
            "best_epoch": 8,
            "composite_score": 0.4694
        },
        "seed_42027": {
            "path": "training_runs/positioning_v2_real_temporal/full_training/seed_42027/best_checkpoint.pt",
            "sha256": "20a1de5df732b9dc67a37ce6be3efe111808f0f481df7617aa5af7a0c790bd46",
            "best_epoch": 8,
            "composite_score": 0.4623
        },
        "seed_42028": {
            "path": "training_runs/positioning_v2_real_temporal/full_training/seed_42028/best_checkpoint.pt",
            "sha256": "4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352",
            "best_epoch": 6,
            "composite_score": 0.4700
        },
        "selected_candidate": {
            "path": "training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt",
            "sha256": "4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352",
            "source_seed": 42028,
            "selected_epoch": 6,
            "validation_composite_score": 0.4700
        }
    },
    "validation_gates_matrix": {
        "PositioningState_MacroF1": {
            "threshold": ">= 0.45",
            "achieved": 0.2250,
            "status": "NOT_MET"
        },
        "PositioningState_BalancedAcc": {
            "threshold": ">= 0.50",
            "achieved": 0.2397,
            "status": "NOT_MET"
        },
        "SectorTransitionOccurs_MacroF1": {
            "threshold": ">= 0.55",
            "achieved": 0.4649,
            "status": "NOT_MET"
        },
        "SectorTransitionOccurs_BalancedAcc": {
            "threshold": ">= 0.55",
            "achieved": 0.5000,
            "status": "NOT_MET"
        },
        "NextSector_MacroF1": {
            "threshold": ">= 0.50",
            "achieved": 0.3652,
            "status": "NOT_MET"
        },
        "NextSector_SupportedSectors": {
            "threshold": ">= 4",
            "achieved": 5,
            "status": "MET"
        },
        "CandidateSpotRanking_MRR": {
            "threshold": ">= 0.60",
            "achieved": 0.7604,
            "status": "MET"
        },
        "CandidateSpotRanking_Top1": {
            "threshold": ">= 0.45 (45.0%)",
            "achieved": "0.6229 (62.29%, 3189/5120)",
            "status": "MET"
        },
        "CandidateSpotRanking_Top5": {
            "threshold": ">= 0.80 (80.0%)",
            "achieved": "0.9555 (95.55%, 4892/5120)",
            "status": "MET"
        },
        "CandidateSpotRanking_InvalidMaskedSelections": {
            "threshold": "== 0",
            "achieved": 0,
            "status": "MET"
        },
        "CandidateSpotRanking_UnsupportedSelections": {
            "threshold": "== 0",
            "achieved": 0,
            "status": "MET"
        },
        "Transition_MacroF1": {
            "threshold": ">= 0.60",
            "achieved": 0.5637,
            "status": "NOT_MET"
        },
        "ExitTrigger_MacroF1": {
            "threshold": ">= 0.45",
            "achieved": 0.2613,
            "status": "NOT_MET"
        }
    },
    "conditional_reasons": [
        "Reprovação em 5 dos 6 gates contratuais de validação (PositioningState, SectorTransitionOccurs, NextSector, Transition e ExitTrigger)",
        "Colapso total da classe minoritária TRANSITION_OCCURS (recall = 0.000) e colapso das 5 classes raras de PositioningState",
        "Superioridade temporal global contestada: CompositeScore do modelo temporal (0.4700) é inferior ao baseline estático de último frame real (0.4712)",
        "Omissão da comparação formal com baseline logístico prevista no contrato da Seção 12 item 4"
    ],
    "prohibitions_enforced": {
        "test_split_sealed": True,
        "final_holdout_sealed": True,
        "no_test_inference": True,
        "no_onnx_export": True,
        "no_csharp_integration": True,
        "no_deploy": True,
        "stop_and_await_human_approval": True
    }
}

matrix_out_path = "training_runs/positioning_v2_real_temporal/full_training/milestone_2b3_evidence_matrix.json"
with open(matrix_out_path, "w", encoding="utf-8") as f:
    json.dump(evidence_matrix, f, indent=2, ensure_ascii=False)
print("Saved:", matrix_out_path)

deliverable_evidence = {
    "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
    "milestone": "Marco 2B.3 - Treinamento Completo do Positioning Transformer Temporal Real",
    "verdict": "CONDITIONAL",
    "canonical_milestone_verdict": "REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL",
    "generated_at_utc": timestamp_now,
    "review_stamp": "AGENT_REVIEWED",
    "auditor": "Report Author and Evidence Compiler",
    "claims": [
        {
            "claim_id": "M2B3-C1-MultiSeedConvergenceAndCandidateSelection",
            "claim": "Treinamento multi-seed convergente nas 3 seeds canônicas (42026, 42027, 42028) com 8 épocas cada; Seed 42028 selecionada na Época 6 por critério exclusivo de CompositeScore de Validação (0.4700); independência estocástica verificada (distância L2 > 6.4, similaridade cosseno < 0.06).",
            "evidence_files": [
                "training_runs/positioning_v2_real_temporal/full_training/three_seed_comparison.json",
                "training_runs/positioning_v2_real_temporal/full_training/best_model_selection.json",
                "training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt"
            ],
            "raw_sources": [
                "training_runs/positioning_v2_real_temporal/full_training/seed_42028/best_checkpoint.pt",
                "training_runs/positioning_v2_real_temporal/full_training/seed_42028/validation_metrics.jsonl"
            ],
            "reproduction_command": "pytest tests/test_phase3a3_b_milestone2b3_full_training.py -k \"ThreeSeedsAreIndependent or BestCheckpointUsesValidationOnly\" -v",
            "validator": "Mathematical and Statistical Auditor",
            "sha256": "4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352",
            "data_nature": "REAL"
        },
        {
            "claim_id": "M2B3-C2-SpotRankingExemplaryPerformance",
            "claim": "Head de CandidateSpotRanking superou amplamente todas as metas dos gates de validação (MRR 0.7604 vs meta 0.60; Top-1 62.29% [3189/5120] vs meta 45%; Top-5 95.55% [4892/5120] vs meta 80%; 0 seleções inválidas mascaradas e 0 seleções não supervisionadas entre os 26 spots mask=0).",
            "evidence_files": [
                "training_runs/positioning_v2_real_temporal/full_training/mathematical_training_audit.json",
                "training_runs/positioning_v2_real_temporal/full_training/best_model_selection.json"
            ],
            "raw_sources": [
                "datasets/mirage_v2/positioning_v2_full_temporal/supervised_spot_mask_v1.json",
                "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json"
            ],
            "reproduction_command": "pytest tests/test_phase3a3_b_milestone2b3_full_training.py -k \"UnsupportedSpotCannotWinNeuralSelection or SupportedTargetIsPresentInCandidateMask\" -v",
            "validator": "Mathematical and Statistical Auditor",
            "sha256": "8a10f516a82934128dd9dfbfb11e3576bead866a1ae885d1fd9c69548e2180a9",
            "data_nature": "REAL"
        },
        {
            "claim_id": "M2B3-C3-ValidationGatesShortfallAndConditionalVerdict",
            "claim": "Reprovação formal em 5 dos 6 gates contratuais de validação da Seção 11 do ORIGINAL_REQUEST.md (PositioningState Macro-F1 0.2250 vs 0.45; SectorTransition Macro-F1 0.4649 vs 0.55; NextSector Macro-F1 0.3652 vs 0.50; Transition Macro-F1 0.5637 vs 0.60; ExitTrigger Macro-F1 0.2613 vs 0.45); imposição mandatória do veredito REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL conforme Seção 19.",
            "evidence_files": [
                "training_runs/positioning_v2_real_temporal/full_training/ml_generalization_audit.json",
                "training_runs/positioning_v2_real_temporal/full_training/adversarial_training_audit.json"
            ],
            "raw_sources": [
                "training_runs/positioning_v2_real_temporal/full_training/seed_42028/confusion_counts_validation.json",
                "training_runs/positioning_v2_real_temporal/full_training/seed_42028/support_validation.json"
            ],
            "reproduction_command": "pytest tests/test_phase3a3_b_milestone2b3_full_training.py -k \"ZeroSupportIsNA or MetricsUseEligibleDenominators\" -v",
            "validator": "Adversarial Success Auditor",
            "sha256": "99a2a0f6af2c78f6d63a1e751c2a2e6a8bb38ec6013339c12cef7bef807209ba",
            "data_nature": "REAL"
        },
        {
            "claim_id": "M2B3-C4-ForensicCollapseAndBaselineContradictionExposed",
            "claim": "Identificação pericial e desconstrução de contradições internas: (1) colapso total da classe minoritária TRANSITION_OCCURS (0 de 671 transições detectadas, recall 0.000) e de estados raros erroneamente assinalados como anti-collapse false; (2) CompositeScore do modelo temporal (0.4700) inferior ao baseline estático de último frame real (0.4712); (3) omissão formal do baseline logístico contratual.",
            "evidence_files": [
                "training_runs/positioning_v2_real_temporal/full_training/collapse_monitoring.json",
                "training_runs/positioning_v2_real_temporal/full_training/baseline_comparison.json",
                "training_runs/positioning_v2_real_temporal/full_training/temporal_gain_report.json"
            ],
            "raw_sources": [
                "training_runs/positioning_v2_real_temporal/full_training/seed_42028/validation_metrics.jsonl"
            ],
            "reproduction_command": "pytest tests/test_phase3a3_b_milestone2b3_full_training.py -k \"test_15_three_seeds_are_independent\" -v",
            "validator": "ML Generalization Auditor",
            "sha256": "7570e56d8c6437e138e5f0c1123257b7c18a6702bbb793dc53b2b4540f8fe8e0",
            "data_nature": "REAL"
        },
        {
            "claim_id": "M2B3-C5-TestSplitSealedAndZeroContamination",
            "claim": "Split Test contendo 67 demos (545.508 sequências) permaneceu 100% (545508/545508) lacrado e intocado; zero leituras para treino, tuning, seleção de checkpoint ou inferência; zero modelos ONNX exportados; zero alterações em runtime C#; parada imediata conforme Regra 08 aguardando homologação do usuário humano.",
            "evidence_files": [
                "training_runs/positioning_v2_real_temporal/full_training/data_provenance_training_audit.json",
                "training_runs/positioning_v2_real_temporal/full_training/input_snapshot.json"
            ],
            "raw_sources": [
                "datasets/mirage_v2/canonical_temporal_splits_v1.json",
                "datasets/mirage_v2/positioning_v2_full_temporal/shard_005.parquet"
            ],
            "reproduction_command": "pytest tests/test_phase3a3_b_milestone2b3_full_training.py -k \"TestIsNeverOpenedByTrainer or FinalHoldoutIsNeverOpened or NoONNXExport or NoFinalEvaluation\" -v",
            "validator": "Data and Temporal Auditor",
            "sha256": "8fda7fca66b40974c53243c20c81752ab3a14db5fc457e4915ddaa61397ff01b",
            "data_nature": "REAL"
        }
    ]
}

full_train_dev_path = "training_runs/positioning_v2_real_temporal/full_training/deliverable_evidence.json"
with open(full_train_dev_path, "w", encoding="utf-8") as f:
    json.dump(deliverable_evidence, f, indent=2, ensure_ascii=False)
print("Saved:", full_train_dev_path)

root_dev_path = "deliverable_evidence.json"
with open(root_dev_path, "w", encoding="utf-8") as f:
    json.dump(deliverable_evidence, f, indent=2, ensure_ascii=False)
print("Saved:", root_dev_path)
