# DISPATCH

## 2026-11-09T00:39:04Z — Project Sentinel

FASE 2A-INTERMEDIATE: ESTUDO DE VIABILIDADE E AQUISIÇÃO DO CORPUS MIRAGE INTERMEDIÁRIO.

Resumo fiel do comando (spec completo de 22 seções entregue pelo Sentinel, preservado no histórico da conversa):

1. **Pausa formal do treinamento** (FASE 3A.3-B, MARCO 2B.3). Criar marcador `PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY`. Preservar `datasets/mirage_v2/`, `training_runs/positioning_v2_real_temporal/`, catálogo Mirage V3, 6 shards, sidecars label_contract_v2, manifests, checkpoints.
2. **Objetivo**: responder 9 perguntas de viabilidade sobre fontes legais de demos Mirage intermediárias (FACEIT, Valve Competitive/Premier, datasets públicos, contribuições voluntárias). NÃO executar treinamento.
3. **Orquestração compacta**: max_active_subagents=6, nested_subagents=false, only_orchestrator_can_delegate=true, reuse_agents_within_milestone=true, spawn_only_when_required=true, kill_all_on_completion=true. Papéis: Orchestrator, Data Acquisition Researcher, Dataset and Metadata Implementer, Mathematical and Statistical Auditor, Data Provenance and Compliance Auditor, Adversarial Success Auditor (+ CS2 Domain Reviewer só na análise espacial final).
4. **Separação formal de domínios**: `datasets/mirage_domains/domain_contract_v1.json`; domínios PROFESSIONAL / INTERMEDIATE_COMPETITIVE / UNKNOWN; subdomínios PROFESSIONAL_HLTV, FACEIT_LEVEL_5_6, FACEIT_LEVEL_7_8, FACEIT_LEVEL_9_10, VALVE_COMPETITIVE_MAP_RANK, VALVE_PREMIER_RATING, VALVE_OPT_IN_UNKNOWN_RANK. Não converter automaticamente entre sistemas de rank. Campos obrigatórios do contrato listados.
5–7. Fontes a investigar (FACEIT Data/Downloads API; Valve opt-in; datasets públicos; contribuições voluntárias) + definição do domínio intermediário (FACEIT 5–6 intermediate, 7–8 upper-intermediate; Valve MG1–LEM candidatos) + critérios de aceitação de demo.
8–11. Piloto de 20–50 demos; organização de diretórios; downloader seguro (`tools/intermediate_demo_acquisition/` com 9 componentes); manifests (inventory, npz manifest, pilot download manifest, quarantine); extração piloto reutilizando pipeline NPZ canônico.
12–16. Métricas de padronização CT/TR; comparação com corpus profissional (Jensen-Shannon, Wasserstein, bootstrap por match/round); análise dos 53 spots (classificação CROSS_DOMAIN_CONFIRMED etc.); descoberta de novos spots.
17–19. Análise de qualidade do domínio; estratégias futuras de treino (A–E); splits do novo domínio (70/15/15 + unseen_players/unseen_stacks/recent_matches/cross-domain holdout).
20. 20 testes obrigatórios (lista na Seção 20). Manter suíte C# verde.
21. Entregáveis: `datasets/mirage_domains/*`, `tools/intermediate_demo_acquisition/*`, `training_runs/intermediate_domain_study/*` (3 relatórios Markdown extensos: source_feasibility_report.md, domain_training_strategy.md, fase_2a_intermediate_final_report.md; demais JSON/markdown curto).
22. Gates A–D + estados: INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING / INTERMEDIATE_CORPUS_HYPOTHESIS_NOT_CONFIRMED / INTERMEDIATE_CORPUS_REQUIRES_MORE_PILOT_DATA / INTERMEDIATE_MIRAGE_CORPUS_READY_TO_SCALE. Não iniciar treinamento, não alterar catálogo, não retomar 2B.3 automaticamente. kill_all ao encerrar.

Skills obrigatórias: csbot-phase-gate, csbot-report-skeptic, csbot-dataset-forensics, csbot-graph-impact, csbot-math-logic-auditor. Hooks em blocking mode.

Regra de ouro do Sentinel: ao concluir, handoff.md + veredito final + artefatos com caminhos relativos e SHA-256 + kill_all. NÃO declarar "fase concluída" como sucesso final — determinação pertence ao Sentinel após auditoria independente de vitória.

## 2026-11-09T00:48:23Z — Project Sentinel (RETOMADA PÓS-QUEDA DE ENERGIA)

Dispatch de retomada. Conteúdo integral preservado em `.agents/teamwork/ORIGINAL_REQUEST.md` §"Follow-up — 2026-11-09T00:47:05Z (RESUME-AFTER-POWER-OUTAGE)" e no corpo §0–§22 da FASE 2A-INTERMEDIATE.

Pontos mandatórios deste dispatch:
1. Retomar da Iteration 0 / Wave 1; preservar BRIEFING.md, SCOPE.md, DISPATCH.md e atualizar (não recriar) progress.md.
2. Primeira ação concreta: criar `training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json` com marcador, timestamp UTC, motivo `FASE_2A_INTERMEDIATE`, veredito `REAL_TEMPORAL_POSITIONING_CANDIDATE_CONDITIONAL`, inventário de artefatos preservados com SHA-256 de 64 hex verificados no disco, e declaração explícita de que a pausa não invalida o trabalho existente.
3. Hook `protect-sensitive-files` em blocking mode: hashear via script Python somente-leitura que enumere diretórios (sem citar nomes sensíveis na linha de comando); nunca modificar/mover/renomear; registrar bloqueios; não criar autorização de modificação para leitura; não inventar hashes.
4. Orquestração: max_active_subagents=6, nested_subagents=false, only_orchestrator_can_delegate=true, reuse_agents_within_milestone=true, spawn_only_when_required=true, kill_all_on_completion=true. Papéis §3; CS2 Domain Reviewer só na análise espacial final. Auditores somente leitura; implementador não valida o próprio trabalho.
5. Cumprir §8, §9, §10, §11, §20, §21, §22 integralmente (entregáveis, 20 testes, Gates A–D).
6. NÃO executar treinamento/Test/Final Holdout/ONNX/C#/shadow/MLMove V2/Jump Head; NÃO retomar nem alterar Marco 2B.3; NÃO alterar catálogo de 53 spots; NÃO mover/renomear corpus profissional.
7. PROIBIDO fabricar dados intermediários. Sem demos reais → veredito `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING` e comparação rotulada `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`. Todos os artefatos de análise devem existir com conteúdo real, tamanho > 0 e hash verificável — nada de diretórios vazios cosméticos.
8. `support = 0` → `N/A`; rotular `SIMULATED`/`TEMPLATED`/`SYNTHETIC`/`INFERRED`; SHA-256 completos; caminhos relativos; percentuais com `(N/D)`.
9. Atualizar `progress.md` continuamente (Iteration N/32, Wave, concluídos, bloqueios).
10. Ao encerrar: veredito canônico + `deliverable_evidence.json`, `phase_evidence_matrix.json`, `fase_2a_intermediate_final_report.md`, handoff, e reportar vitória ao Sentinel com artefatos + hashes + comandos reproduzíveis. Sentinel disparará `teamwork_victory_auditor` cego. Não executar `kill_all` (o Sentinel coordena); matar apenas subagentes ociosos.
