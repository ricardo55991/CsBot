# BRIEFING — 2026-11-09T01:40:00Z

## Mission
FASE 2A-INTERMEDIATE: estudo de viabilidade e aquisição do corpus Mirage intermediário. Estado atual: **Wave 4 — ciclo de correção** após 3 auditorias independentes interromperem o `PASS` (todas `CONDITIONAL`).

## 🔒 My Identity
- Archetype: teamwork orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\orchestrator_2a_intermediate`
- Original parent: Project Sentinel
- Original parent conversation ID: `05c70c07-2bfb-475d-b827-335e709cea6f` (morto — rodada anterior)

## 🔒 My Workflow
- **Pattern**: Project (sub-orchestrator de fase única; sem nesting de subagentes)
- **Scope document**: `SCOPE.md` (neste diretório)
1. **Decompose**: milestones M0–M8 + ondas W1 (pesquisa/implementação) → W2 (analista) → W3 (3 auditorias) → W4 (correção + reauditoria) → W5 (phase gate + 7 entregáveis + dossiê).
2. **Dispatch & Execute**: um agente por milestone, contexto limpo, sem reutilização após handoff.
3. **On failure**: Retry → Replace → Skip (só não-crítico) → Redistribute → Redesign → Escalate (Sentinel, último recurso). **Auditor nunca é Skip.**
4. **Succession**: self-succeed em 16 spawns; hoje **8/16**.
- **Work items**: M0 ✅ · M1 ✅ · M2 ✅ · M3 ✅ · M4 ✅ · M5/M6 ✅ (análises `NOT_EXECUTABLE` por ausência de dados) · M7 ✅ · M8 ✅ (20/20 pytest) · W3 ✅ (3× `CONDITIONAL`) · **W4.1 em execução**.
- **Current phase**: Wave 4.
- **Current focus**: worker de correção cirúrgica (`fix_corrections_2a_int_1`) sobre B1–B4.

## 🔒 Key Constraints
- **Nunca emitir `PASS`** enquanto as três auditorias novas (`W4.3`) não fecharem. Veredito vigente: `CONDITIONAL`; Gate A: `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`.
- **Nunca declarar fase concluída** — no máximo "alegação de vitória"; o auditor de vitória cego é disparado pelo Sentinel.
- Nada de treinamento, Test/Final Holdout, ONNX, integração C#, shadow mode, MLMove V2, Jump Head, 2B.3. Nada para o FACEIT (`application_submitted: false`).
- Preservar byte-a-byte: `datasets/mirage_v2/**` (95 artefatos, 212.960.002 B), catálogo V3 (53 spots, `8248adc1…`), marcador M0 (`465f4cb9…13efad`, 37114 B — **não reemitir**), 6 shards, checkpoints.
- Nenhum agente instala pacotes; `demoparser2` ausente ⇒ `PENDING_TOOLCHAIN`.
- **Nunca criar `.agents/audit/sensitive_file_authorization.json`** para driblar o hook `protect-sensitive-files`.
- `support = 0` ⇒ `N/A`, nunca `0.0`/`0.0%`; percentuais sempre `(N/D)`; caminhos relativos; SHA-256 sempre 64 hex.
- Rótulos permitidos a implementadores/workers: `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS`. Proibido `VALIDATED`/`APPROVED` e qualquer selo humano.
- Isolamento de papel: auditores `write_scope: OWN_AGENT_DIRECTORY_ONLY`; implementador nunca valida o próprio trabalho.
- Idioma: português do Brasil em mensagens e artefatos.

## Current Parent
- Conversation ID: `d7c79efa-81cf-40df-b317-b27a0d0506b8` (o ID `d65e2bde-…` é erro de dispatch e deve ser ignorado)
- Updated: 2026-11-09T01:40:00Z

## Key Decisions Made
- `SPEC_ENUMERATION_AUTHORITATIVE`: a enumeração literal da spec vence o meu dispatch; §12=17, §13=15, §14=15, §15=15, §16=6/7, §17=8/8, §20=20.
- `EVIDENCE_LOSS_EVENT` é **limitação de fase**, não falha disciplinar; fidelidade é `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`; cache é `RECAPTURED`, nunca evidência primária.
- R3, R6, R7, R8, `bombsite` 4/53 e F12: **registrar sem corrigir** (ver `GATE_STATUS.md`).
- Os 7 entregáveis do §21 são meus, não do worker.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| researcher_2a_int_1 | teamwork_worker | M2 (5 artefatos) | DONE / encerrado | 990159da-eb37-4582-b866-4accd423d210 |
| implementer_core_2a_int_1 | teamwork_worker | M0/M1/M3 | DONE / encerrado | adbf4597-05f6-4300-9790-d9280ab450d5 |
| implementer_data_2a_int_1 | teamwork_worker | M4/M7/M8 | DONE / encerrado | aa4df23e-… |
| analyst_2a_int_1 | teamwork_worker | M5/M6 (8 artefatos) | DONE / encerrado | e9907c4a-… |
| math_stat_auditor_2a_int_1 | teamwork_worker | Auditoria 1/3 | CONDITIONAL / encerrado | 611cb9f2-… |
| adversarial_auditor_2a_int_1 | teamwork_worker | Auditoria 2/3 | CONDITIONAL / encerrado | e58e5be4-… |
| provenance_auditor_2a_int_1 | teamwork_worker | Auditoria 3/3 | CONDITIONAL / encerrado | 43785c1a-… |
| fix_corrections_2a_int_1 | teamwork_worker | W4.1 correção B1–B4 | running | (registrado ao despachar) |

## Succession Status
- Succession required: **no**
- Spawn count: **8 / 16**
- Pending subagents: `fix_corrections_2a_int_1`
- Predecessor: rodada anterior interrompida por queda de energia
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: `task-49` (`*/10 * * * *`) — prompt desatualizado, mas funcional; cancelar quando não houver subagente vivo
- Safety timer: será criado no dispatch da W4.1

## Artifact Index
- `SCOPE.md` — decomposição em milestones
- `progress.md` — checkpoint/liveness (fonte mais atual)
- `GATE_STATUS.md` — gates M0, A, W3 e W4
- `ARTIFACT_INVENTORY.md` — 57 arquivos com selos `[CURRENT]` / `SUPERSEDED`
- `DISPATCH.md` — registro dos despachos do Sentinel
