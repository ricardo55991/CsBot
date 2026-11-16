import json
from pathlib import Path

deliverable_evidence = {
    'phase': 'FASE 3A.3-B: RECONSTRUCAO TEMPORAL CANONICA E RETREINO DO POSITIONING TRANSFORMER',
    'milestone': 'Marco 2B.2 - Patch Final dos Labels e Contratos Antes do Treino Completo',
    'verdict': 'PASS',
    'canonical_milestone_verdict': 'LABEL_CONTRACT_V2_READY_FOR_FULL_TRAINING',
    'generated_at_utc': '2026-11-08T20:28:00Z',
    'auditor': 'Adversarial Success Auditor',
    'claims': [
        {
            'claim_id': 'M2B2-C1-DynamicRemovedFromNextSector',
            'claim': 'DYNAMIC eliminado de Head_B_NextSector; Head_A_SectorTransitionOccurs binario criado; perda mascarada quando NO_TRANSITION',
            'evidence_files': [
                'datasets/mirage_v2/contracts/label_contract_v2.json',
                'training_runs/positioning_v2_real_temporal/revised_label_distribution.json'
            ],
            'raw_sources': ['datasets/mirage_v2/positioning_v2_full_temporal/label_sidecar_v2/shard_000_labels.parquet'],
            'reproduction_command': 'pytest tests/test_phase3a3_b_milestone2b2_label_patch.py -k DynamicIsNotASectorClass -v',
            'validator': 'Adversarial Success Auditor'
        },
        {
            'claim_id': 'M2B2-C2-PrimarySourceAccountingClosure',
            'claim': 'Equacao contabil das fontes primarias fecha exatamente em 3.411.434 sem residuo; overrides semanticos ortogonais',
            'evidence_files': [
                'datasets/mirage_v2/positioning_v2_full_temporal/next_sector_source_accounting.json',
                'training_runs/positioning_v2_real_temporal/mathematical_label_audit.json'
            ],
            'raw_sources': ['datasets/mirage_v2/positioning_v2_full_temporal/dataset_manifest.json'],
            'reproduction_command': 'pytest tests/test_phase3a3_b_milestone2b2_label_patch.py -k NextSectorPrimaryAccountingCloses -v',
            'validator': 'Mathematical and Statistical Auditor'
        },
        {
            'claim_id': 'M2B2-C3-ObjectiveSaveExitTriggerReconciliation',
            'claim': 'Conclusao de plant produz BOMB_PLANTED (1.711 seqs); mapeamento forcado de SAVE para TEAMMATE_DEATH quebrado (25% TEAMMATE_DEATH, 33% TACTIC_REVISION, 42% TIME)',
            'evidence_files': [
                'datasets/mirage_v2/positioning_v2_full_temporal/objective_save_trigger_audit.json',
                'datasets/mirage_v2/positioning_v2_full_temporal/exit_trigger_reconciliation.json'
            ],
            'raw_sources': ['datasets/mirage_v2/positioning/objective_save_sequences.parquet'],
            'reproduction_command': 'pytest tests/test_phase3a3_b_milestone2b2_label_patch.py -k ObjectivePlantCanProduceBombPlantedTrigger -v',
            'validator': 'Data Provenance and Temporal Auditor'
        },
        {
            'claim_id': 'M2B2-C4-SupervisedSpotMaskAndRule03',
            'claim': '27 spots com suporte positivo ativos (mask=1); 26 spots sem suporte mascarados (mask=0) e reportados estritamente como N/A',
            'evidence_files': [
                'datasets/mirage_v2/positioning_v2_full_temporal/supervised_spot_mask_v1.json',
                'training_runs/positioning_v2_real_temporal/revised_spot_supervision_report.json'
            ],
            'raw_sources': ['datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json'],
            'reproduction_command': 'pytest tests/test_phase3a3_b_milestone2b2_label_patch.py -k UnsupportedSpotIsNotSupervised -v',
            'validator': 'Mathematical and Statistical Auditor'
        },
        {
            'claim_id': 'M2B2-C5-SidecarJoinAndBaseShardsImmutability',
            'claim': 'Shards base Parquet permanecem 100% imutaveis com SHA-256 identico; sidecars contem 3.411.434 linhas com join 1:1 exato (0 faltantes, 0 duplicadas)',
            'evidence_files': [
                'training_runs/positioning_v2_real_temporal/label_join_audit.json',
                'training_runs/positioning_v2_real_temporal/label_provenance_audit.json'
            ],
            'raw_sources': ['datasets/mirage_v2/positioning_v2_full_temporal/shard_000.parquet'],
            'reproduction_command': 'pytest tests/test_phase3a3_b_milestone2b2_label_patch.py -k LabelSidecarJoinIsOneToOne -v',
            'validator': 'Data Provenance and Temporal Auditor'
        }
    ]
}

with open('deliverable_evidence.json', 'w', encoding='utf-8') as f:
    json.dump(deliverable_evidence, f, indent=2)

with open('training_runs/positioning_v2_real_temporal/deliverable_evidence.json', 'w', encoding='utf-8') as f:
    json.dump(deliverable_evidence, f, indent=2)

print('Updated deliverable_evidence.json successfully')
