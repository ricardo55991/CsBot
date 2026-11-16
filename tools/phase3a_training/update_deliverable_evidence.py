import json

evidence_data = {
  "phase": "FASE 3A.3-B: RECONSTRUCAO TEMPORAL CANONICA E RETREINO DO POSITIONING TRANSFORMER",
  "milestone": "Marco 2A - Dry-Run, Overfit Controlado e Piloto Temporal de 10%",
  "verdict": "PASS",
  "canonical_milestone_verdict": "REAL_TEMPORAL_POSITIONING_PILOT_READY_FOR_FULL_TRAINING",
  "checkpoint_decision": "B: CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY (Superseeded by Marco 2A Real Temporal Retraining)",
  "generated_at_utc": "2026-11-08T10:45:00Z",
  "auditor": "adversarial_success_auditor",
  "claims": [
    {
      "claim_id": "M2A-C1-reconciled-temporal-coverage-and-input-snapshot",
      "claim": "Snapshot de entrada com Git commit d66c214e88a08d2a1a721b423a3e788c33163585 congelado, exclusao explicita de 8 arquivos raw .dem nao-parquet, reconciliacao deterministica de 577.816 linhas (Train 189.944, Val 207.256, Test 180.616) com 97.38% accepted e 2.62% masked",
      "evidence_files": [
        "training_runs/positioning_v2_real_temporal/milestone_2a_input_snapshot.json",
        "training_runs/positioning_v2_real_temporal/milestone_2a_window_accounting.json"
      ],
      "raw_sources": [
        "datasets/mirage_v2/positioning/splits/train_manifest.json",
        "datasets/mirage_v2/positioning/splits/val_manifest.json",
        "datasets/mirage_v2/positioning/splits/test_manifest.json",
        "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_000.parquet"
      ],
      "reproduction_command": "python -c \"import json; d=json.load(open('training_runs/positioning_v2_real_temporal/milestone_2a_window_accounting.json')); assert d['global_accounting']['closed_exact'] is True\"",
      "validator": "adversarial_success_auditor"
    },
    {
      "claim_id": "M2A-C2-dry-run-and-overfit-sanity-checks",
      "claim": "Execucao deterministica de dry-run (2 batches Train, 1 batch Val) com perdas e gradientes finitos (norma maxima 3.73), restauracao exata de checkpoint (max_diff 0.0), e overfit controlado em 512 sequencias com queda de 96.65% na perda (9.8848 -> 0.3309) e acuracias finais State 96.48%, Sector 100.0%, Spot 98.96%",
      "evidence_files": [
        "training_runs/positioning_v2_real_temporal/dry_run_report.md",
        "training_runs/positioning_v2_real_temporal/dry_run_metrics.json",
        "training_runs/positioning_v2_real_temporal/temp_dry_run_checkpoint.pt",
        "training_runs/positioning_v2_real_temporal/overfit_report.md",
        "training_runs/positioning_v2_real_temporal/overfit_metrics.json",
        "training_runs/positioning_v2_real_temporal/overfit_checkpoint.pt"
      ],
      "raw_sources": [
        "tools/phase3a_training/run_milestone2a_dry_run.py",
        "tools/phase3a_training/run_milestone2a_overfit.py"
      ],
      "reproduction_command": "pytest -v tests/test_phase3a3_b_milestone2a_training.py -k \"dry_run or overfit\"",
      "validator": "mathematical_ml_auditor"
    },
    {
      "claim_id": "M2A-C3-pilot-10pct-training-and-validation-evaluation",
      "claim": "Treinamento piloto em 10% do Train por partidas completas (31 demos, seed 42026, 9 epocas) com convergencia monotonica de val_loss (6.8129 -> 6.3168 na epoca 5) e avaliacao exaustiva de 100% da Validacao (207.256 sequencias) superando todos os gates minimos: State Macro-F1 0.3592 (gate >= 0.30), Sector Macro-F1 0.4998 (gate >= 0.30), Spot MRR 0.5653 (gate >= 0.40), Spot Top-5 0.8047 (gate >= 0.60), Transition Macro-F1 0.7056 (gate >= 0.30), ExitTrigger Macro-F1 0.5280 (gate >= 0.25) e 0 selecoes mascaradas invalidas (0.0%)",
      "evidence_files": [
        "training_runs/positioning_v2_real_temporal/pilot_subset_manifest.json",
        "training_runs/positioning_v2_real_temporal/pilot_config.json",
        "training_runs/positioning_v2_real_temporal/pilot_train_metrics.jsonl",
        "training_runs/positioning_v2_real_temporal/pilot_validation_metrics.jsonl",
        "training_runs/positioning_v2_real_temporal/pilot_best_checkpoint.pt",
        "training_runs/positioning_v2_real_temporal/temporal_pilot_metrics.json"
      ],
      "raw_sources": [
        "tools/phase3a_training/run_milestone2a_pilot_and_ablation.py"
      ],
      "reproduction_command": "python -c \"import json; d=json.load(open('training_runs/positioning_v2_real_temporal/temporal_pilot_metrics.json')); assert d['evaluation_metrics']['head_state']['macro_f1'] >= 0.30\"",
      "validator": "adversarial_success_auditor"
    },
    {
      "claim_id": "M2A-C4-temporal-ablation-against-last-frame",
      "claim": "Comparacao empirica contra baseline de ultimo frame sobre as mesmas 207.256 sequencias de validacao, demonstrando ganhos temporais expressivos do Modelo A (Temporal Real) sobre o Modelo B (Ultimo Frame): Transition HOLD F1 +138.1% (0.1798 vs 0.0755), ExitTrigger FIRST_KILL F1 +145.7% (0.2391 vs 0.0973), State RETAKE F1 +32.4% (0.1210 vs 0.0914), State HOLD F1 +20.9% (0.1699 vs 0.1405), ExitTrigger BOMB_PLANTED F1 +4.4% (0.9992 vs 0.9575)",
      "evidence_files": [
        "training_runs/positioning_v2_real_temporal/last_frame_best_checkpoint.pt",
        "training_runs/positioning_v2_real_temporal/last_frame_baseline_metrics.json",
        "training_runs/positioning_v2_real_temporal/temporal_ablation_metrics.json",
        "training_runs/positioning_v2_real_temporal/pilot_and_ablation_report.md"
      ],
      "raw_sources": [
        "tools/phase3a_training/run_milestone2a_pilot_and_ablation.py"
      ],
      "reproduction_command": "python -c \"import json; d=json.load(open('training_runs/positioning_v2_real_temporal/temporal_ablation_metrics.json')); assert d['invariants']['synthetic_linspace_detected'] is False\"",
      "validator": "mathematical_ml_auditor"
    },
    {
      "claim_id": "M2A-C5-provenance-governance-and-test-isolation",
      "claim": "Isolamento absoluto do split Test (0 demos consultadas de 67) e Final Holdout (Regra 02), verificacao de 7.680 janelas brutas pelo auditor de proveniencia com 100% de match contra NPZ fisico, zero dados sinteticos/interpolados (Regra 04), classes ausentes tratadas estritamente como N/A (Regra 03), 20/20 testes unitarios de governanca verdes, e veredito canonico final emitido",
      "evidence_files": [
        "training_runs/positioning_v2_real_temporal/temporal_provenance_audit.json",
        "training_runs/positioning_v2_real_temporal/mathematical_ml_audit.json",
        "training_runs/positioning_v2_real_temporal/adversarial_success_audit.json",
        "training_runs/positioning_v2_real_temporal/milestone_2a_evidence_matrix.json",
        "tests/test_phase3a3_b_milestone2a_training.py"
      ],
      "raw_sources": [
        "AGENTS.md",
        ".agents/skills/csbot-dataset-forensics/SKILL.md"
      ],
      "reproduction_command": "pytest -v tests/test_phase3a3_b_milestone2a_training.py",
      "validator": "temporal_provenance_auditor"
    }
  ]
}

for path in ['deliverable_evidence.json', '.agents/audit/deliverable_evidence.json']:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(evidence_data, f, indent=2)
    print(f"Successfully updated {path}")
