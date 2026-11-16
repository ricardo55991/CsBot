# DISPATCH — fix_corrections_2a_int_1

## 2026-11-09T01:40:07Z

Remetente: Orchestrator `a7196ff0-cf47-4d79-a99f-eaf19c722649`
Papel: worker de correção cirúrgica da WAVE 4 (FASE 2A-INTERMEDIATE, CsBot).

Escopo: 5 tarefas (T1..T5) sobre 9 arquivos-alvo de posse exclusiva + 1 append-only.

T1 — Rotulagem de fidelidade (B1+R1): `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` no topo do §12 e em cada uma das 25 linhas E1–E25 de `source_feasibility_report.md`; qualificar as 163 ocorrências de `VERIFIED_ONLINE` nos 4 entregáveis; seção `## Nota de proveniência — EVIDENCE_LOSS_EVENT`; corrigir linha 812 do report e linhas 7–8 do INDEX.md; rótulo em `legal_and_access_constraints.md`; append `## CORRIGENDA` no research_log.md; registrar divergência R6 (403 vs 404) sem escolher lado.
T2 — Rebaixamento das 20 evidências sem captura para `UNVERIFIED_NO_MATERIALIZED_CAPTURE`; marcar/remover afirmações sem lastro (`Last updated July 2010`, `~1.300`, `9.651`, `3.624.699.821`). Proibido substituir por números novos.
T3 — §14: 7 métricas PVSI com circularidade (JSD x Wasserstein) → atribuir exatamente um estado: `JSD_APPLICABLE` / `WASSERSTEIN_APPLICABLE` / `NOT_A_DISTRIBUTION`.
T4 — `round_outcome_dependency` em cada uma das 32 métricas CT+TR.
T5 — `dispatch_declared` §12 (18 → `NOT_REPRODUCIBLE_FROM_WRITTEN_RECORD`); §13 (15 = literal, OK).

Proibições-chave: não fabricar captura; não criar números novos; não tocar em `datasets/mirage_v2/**`, `positioning_v2_real_temporal/**`, `src/**`, `models/**`, `tests/test_phase2a_intermediate_domain.py`, manifests; não criar autorização de hook; não remover `__pycache__`; não tocar nos pareceres dos auditores.

Entrega: `.agents/teamwork/fix_corrections_2a_int_1/handoff.md` + mensagem curta ao Orchestrator.
