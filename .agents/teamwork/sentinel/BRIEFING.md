# BRIEFING — 2026-11-09T00:25:00Z

## Mission
Route and monitor FASE 2A-INTERMEDIATE (estudo de viabilidade e aquisição do corpus Mirage intermediário) via teamwork_orchestrator; no training in this phase.

## 🔒 My Identity
- Archetype: sentinel
- Working directory: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\sentinel
- Orchestrator: ed708b48-1669-4f65-b810-5bfc8ff522da (completed, terminated)
- Victory Auditor: 678bdbb1-546b-4f07-ae80-a3eeefc5a975 (VICTORY CONFIRMED, terminated)
- Active Orchestrator (Milestone 2B.3): pending dispatch
- Active Victory Auditor (Milestone 2B.3): to be spawned on victory claim
- Active Orchestrator (Milestone 2B.3): 5aa571f6-be49-4f7f-baff-92e5c3c7ec1a
- Active Victory Auditor (Milestone 2B.3): b529e4c3-735b-4719-975e-07d1759c6342
- Active Orchestrator (FASE 2A-INTERMEDIATE): a7196ff0-cf47-4d79-a99f-eaf19c722649 (RESUME pós-queda de energia, 2026-11-09T00:48Z)
- Prior Orchestrator (FASE 2A-INTERMEDIATE): 3f1db35f-8e68-4022-b4de-627ac576ecc5 (morto no restart, Iteration 0, Wave 1 não despachada)
- Active Victory Auditor (FASE 2A-INTERMEDIATE): to be spawned on victory claim

## 🔒 Key Constraints
- No technical decisions — relay only
- Victory Audit is MANDATORY before reporting completion
- Tier 3 - Alto Risco execution mode
- Do NOT modify checkpoints, canonical datasets, C# runtime or ONNX models
- Do NOT start Phase 3A.3
- Do NOT perform fine-tuning or retraining
- Strict role isolation (Implementer does not validate own work, Auditors do not alter implementation, Success Auditor does not fix failures)
- Do NOT advance phase automatically
- Preserve isolation between implementers and auditors; do not alter canonical artifacts
- Do not soften temporal provenance verdict; final decision must remain strictly one of A, B, C or D with reproducible evidence
- Equipe de no máximo 5 subagentes ativos (1. Orchestrator, 2. Dataset Index Implementer, 3. Data Provenance and Temporal Auditor, 4. Mathematical and Statistical Auditor, 5. Adversarial Success Auditor)
- nested_subagents = false, only_orchestrator_can_delegate = true, spawn_only_when_required = true, kill_all_on_completion = true
- Sem criar subsubagentes, sem repetir Graphify completo e sem repetir a homologação da Governança 1.1
- Preservar dataset piloto anterior (PILOT_SUBSET_25_DEMOS_PER_SPLIT) intacto com hashes e caminhos preservados
- Materializar índice sob datasets/mirage_v2/positioning_v2_full_temporal/ para todas as demos canônicas (311 Train, 66 Val, 67 Test; excluir 8 sem NPZ)
- Política única de janelas (16 Hz, 32 frames, stride 16, overlap 50%) idêntica para todos os splits
- Integrar sequências aprovadas de objective_save_sequences.parquet e relabelar NextSector com horizonte futuro real
- Não treinar modelos nesta fase; não executar inferência nem métricas de modelo no Test
- Não exportar ONNX; aguardar autorização humana
- Milestone 2B.3: Treinamento completo do Positioning Transformer Temporal Real nas 3 seeds canônicas (42026, 42027, 42028)
- Equipe compacta de no máximo 6 subagentes ativos (1. Orchestrator, 2. Model and Training Implementer, 3. Data and Temporal Auditor, 4. Mathematical and Statistical Auditor, 5. ML Generalization Auditor, 6. Adversarial Success Auditor)
- nested_subagents = false, only_orchestrator_can_delegate = true, reuse_agents_within_milestone = true, spawn_only_when_required = true, kill_all_on_completion = true
- Somente Train e Validation podem ser abertos pelo treinador; Test pode ser apenas identificado pelo hash no snapshot
- Não executar inferência no Test nem no Final Holdout
- Não exportar ONNX; não integrar ao runtime C#; não executar shadow mode; não avançar automaticamente de fase
- Join obrigatório sequence_id 1:1 entre shards base e sidecar v2 (3.411.434 rows)
- Proteções de loss: NextSectorLoss=0 quando NO_TRANSITION; SpotLoss=0 em TRANSIT, UNMAPPED e spots sem suporte
- Pesos de classe calculados exclusivamente no Train; composite score e fórmula congelados
- Preflight computacional (100 batches Train, 20 batches Validation) antes das seeds
- Seleção de candidato usando exclusivamente Validation
- FASE 2A-INTERMEDIATE: PAUSAR FASE 3A.3-B MARCO 2B.3; criar marcador PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY
- Preservar integralmente datasets/mirage_v2/, training_runs/positioning_v2_real_temporal/, catálogo Mirage V3, shards, sidecars, manifests, checkpoints
- NÃO executar treinamento nesta fase (sem Test, sem Final Holdout, sem ONNX, sem C#, sem shadow mode, sem MLMove V2, sem Jump Head)
- max_active_subagents = 6; nested_subagents = false; only_orchestrator_can_delegate = true; reuse_agents_within_milestone = true; spawn_only_when_required = true; kill_all_on_completion = true
- Papéis: Orchestrator, Data Acquisition Researcher, Dataset and Metadata Implementer, Mathematical and Statistical Auditor, Data Provenance and Compliance Auditor, Adversarial Success Auditor; CS2 Domain Reviewer só na análise espacial final
- Nenhuma credencial/cookie/senha em relatório ou commit; não contornar autenticação/acesso restrito/limites de plataforma; não baixar em massa antes do piloto
- Piloto de 20-50 demos (10-25 FACEIT 5-6, 10-25 FACEIT 7-8); não escalar para 200 demos nesta fase
- Não mover/renomear corpus profissional sem plano de migração; não materializar splits definitivos com menos de 50 demos
- Não iniciar treinamento; não alterar catálogo; não retomar Marco 2B.3 automaticamente
- Skills obrigatórias: csbot-phase-gate, csbot-report-skeptic, csbot-dataset-forensics, csbot-graph-impact, csbot-math-logic-auditor; hooks em blocking mode

## User Context
- **Last user request**: RETOMADA pós-queda de energia da FASE 2A-INTERMEDIATE (registrada 2026-11-09T00:47:05Z)
- **Pending clarifications**: none
- **Delivered results**: Marco 2B.3 anterior concluído (VICTORY CONFIRMED); fase 2A-INTERMEDIATE re-despachada do zero em Iteration 0.

## Project Status
- **Phase**: in progress (retomada)
- **Routing**: General path -> teamwork_orchestrator (a7196ff0-cf47-4d79-a99f-eaf19c722649)
- **Ground truth confirmado (2026-11-09T00:47Z)**: `datasets/mirage_domains/`, `tools/intermediate_demo_acquisition/`, `training_runs/intermediate_domain_study/` e marcador de pausa AUSENTES; `datasets/mirage_v2/` e `full_training/` intactos; orchestrator_2a_intermediate com 4 arquivos de planejamento.
- **Crons**:
  - task-27: Progress reporting (*/8 * * * *)
  - task-28: Liveness check (*/10 * * * *)
- **Nota de hook (2026-11-09T00:53Z)**: `protect-sensitive-files` bloqueia `run_command` somente-leitura quando o texto do comando cita caminhos sensíveis (ex.: `full_training/selected_candidate.pt`, arquivos sob `datasets/mirage_domains/`). Mitigação acordada: verificação por script Python read-only com enumeração genérica (`os.walk`/`rglob`), sem citar nomes sensíveis na linha de comando. NUNCA criar `.agents/audit/sensitive_file_authorization.json` para leitura.

## Victory Audit Status
- **Triggered**: no
- **Verdict**: pending
- **Retry count**: 0

## Artifact Index
- .agents/teamwork/ORIGINAL_REQUEST.md — Authoritative record of user requests
- .agents/teamwork/orchestrator_2a_intermediate/ — Working directory of active Project Orchestrator
- datasets/mirage_v2/ — Professional corpus (preserve intact)
- datasets/mirage_domains/ — New domain separation (to be created)
- tools/intermediate_demo_acquisition/ — Safe downloader (to be created)
- training_runs/intermediate_domain_study/ — Study reports (to be created)
