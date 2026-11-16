# Scope: Marco 2B.3 - Treinamento Completo do Positioning Transformer Temporal Real

## Architecture
- **Modelo**: `PositioningTransformerV2RealTemporal`
- **Entradas**:
  - `self_history`: [batch, 32, 18]
  - `teammates`: [batch, 32, 4, 18]
  - `temporal_mask`: [batch, 32]
  - `teammate_mask`: [batch, 32, 4]
  - `candidate_mask`: [batch, 53]
- **Heads**:
  - `Head A`: PositioningState (7 classes: TRANSIT, CLEARANCE, STAGING, HOLD, OBJECTIVE, RETAKE, SAVE)
  - `Head B`: SectorTransitionOccurs (2 classes: NO_TRANSITION, TRANSITION_OCCURS)
  - `Head C`: NextSector (5 classes: A, B, MID, CT, T) - ativa somente com TRANSITION_OCCURS e next_sector_loss_mask = 1
  - `Head D`: CandidateSpotRanking (53 logits) - ativa somente com spot_loss_mask = 1, target em candidate_mask e supervised_spot_mask = 1
  - `Head E`: Transition (7 classes: ADVANCE, HOLD, FALLBACK, ROTATE, CONVERGE, COVER, LURK)
  - `Head F`: ExitTrigger (8 classes: TIME, CONTACT, FIRST_KILL, TEAMMATE_DEATH, BOMB_SPOTTED, BOMB_PLANTED, UTILITY_EXPIRED, TACTIC_REVISION)

## Milestones & Work Breakdown
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Snapshot & Data Integrity | Snapshot imutável, validação de hashes e validação do join 1:1 base + sidecar v2 (3.411.434 linhas) | none | DONE |
| M2 | Model V2 & Compute Preflight | Arquitetura V2, máscaras condicionais de loss, pesos Train-only, 100 batches train + 20 batches val preflight | M1 | DONE |
| M3 | Multi-Seed Full Training | Treinamento determinístico em 3 seeds (42026, 42027, 42028), monitoramento anti-colapso e métricas por época | M2 | DONE |
| M4 | Validation, Selection & Baselines | Avaliação estrita em Validation, cálculo de CompositeScore, seleção de candidato e baselines (último frame, frequency, logístico) | M3 | DONE |
| M5 | Automated Test Suite | Implementação e passagem dos 22 testes de integridade e regressão; suíte C# verde | M4 | DONE |
| M6 | Independent Quadruple Audits | Math/Stat, Data Provenance, ML Generalization, Adversarial Success | M5 | DONE |
| M7 | Final Report & Closure | Emissão de marco_2b3_final_report.md e matriz de evidências canônicas | M6 | DONE |

## Interface Contracts
- **Entrada do Treinador**: Somente Train (311 demos, 2.364.492 linhas) e Validation (66 demos, 501.434 linhas). Test (67 demos, 545.508 linhas) e Final Holdout estritamente proibidos de leitura/inferência.
- **Join de Dados**: `sequence_id` 1:1 exato entre shards temporais base e sidecars v2. 0 missing, 0 duplicates, 0 conflicts.
- **Zero Support**: Toda classe com suporte zero reportada estritamente como N/A.
- **Candidate Selection**: Seleção do checkpoint baseada unicamente no maior CompositeScore em Validation (`seed_42028`, época 6, CompositeScore: 0.4700).
- **Veredito Canônico**: `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL` (conforme Seção 19 do ORIGINAL_REQUEST.md).

## Code Layout
- Modelos e scripts de treino: `tools/phase3a_training/`
- Checkpoints e métricas: `training_runs/positioning_v2_real_temporal/full_training/`
- Testes: `tests/test_phase3a3_b_milestone2b3_full_training.py`
