# BRIEFING — 2026-11-09T01:40:10Z

## Mission
Aplicar correções cirúrgicas de fidelidade epistêmica (T1–T5) nos entregáveis do pesquisador da FASE 2A-INTERMEDIATE, sem fabricar evidência nem criar números novos.

## 🔒 My Identity
- Archetype: Implementer (correção cirúrgica / QA de fidelidade documental)
- Roles: implementer
- Working directory: `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/teamwork/fix_corrections_2a_int_1/`
- Original parent: `a7196ff0-cf47-4d79-a99f-eaf19c722649` (Orchestrator)
- Milestone: FASE 2A-INTERMEDIATE / WAVE 4

## 🔒 Key Constraints
- Nunca enviar mensagem ao Sentinel.
- Não fabricar captura; não criar URL/hash/contagem/número medido novo.
- Não tocar: `datasets/mirage_v2/**`, `positioning_v2_real_temporal/**`, `src/**`, `models/**`, `full_training/**`, `tests/test_phase2a_intermediate_domain.py`, manifests, pareceres de auditores, `ARTIFACT_INVENTORY.md`/`GATE_STATUS.md`, 7 entregáveis do §21.
- Não criar `.agents/audit/sensitive_file_authorization.json`.
- Não remover `tools/intermediate_demo_acquisition/__pycache__/`.
- Rode Python com `PYTHONDONTWRITEBYTECODE=1` e `PYTHONPYCACHEPREFIX`.
- JSON: `ensure_ascii=False`, indent=2, parseável.
- Hash + bytes ANTES/DEPOIS de cada arquivo tocado.

## Current Parent
- Conversation ID: `a7196ff0-cf47-4d79-a99f-eaf19c722649`
- Updated: 2026-11-09T01:40:10Z

## Task Summary
- **What to build**: rotulagem de fidelidade (T1), rebaixamento de evidências sem captura (T2), desambiguação §14 (T3), campo `round_outcome_dependency` (T4), rótulo `dispatch_declared` (T5).
- **Success criteria**: `(0/163)` deixa de existir como omissão; contagens antes/depois explícitas; 7 métricas com estado único não circular; 32/32 campos T4; pytest 20 passed.
- **Interface contracts**: `.agents/teamwork/ORIGINAL_REQUEST.md` (§12, §14, regras de rótulo)
- **Code layout**: PROJECT.md § Code Layout

## Key Decisions Made
- (pendente) estados §14 serão decisão metodológica, declarada como tal.

## Artifact Index
- `DISPATCH.md` — registro do dispatch
- `progress.md` — heartbeat
- `handoff.md` — entrega final
- `scripts/` — scripts de correção (Python, no meu dir)
