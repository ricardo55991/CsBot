# DISPATCH — researcher_2a_int_1 (Data Acquisition Researcher, FASE 2A-INTERMEDIATE)

## 2026-11-09T00:50:31Z

Remetente: Orchestrator (`a7196ff0-cf47-4d79-a99f-eaf19c722649`). Prioridade: HIGH.

Papel: **Data Acquisition Researcher** — papel 2 do §3 da especificação da FASE 2A-INTERMEDIATE.

Missão M2 (Source Feasibility Research): responder com evidência verificável às 9 perguntas do §2
sobre existência de fontes legais e tecnicamente acessíveis de demos Mirage de nível intermediário,
investigando as 4 fontes do §5 (A: FACEIT Data/Downloads API; B: Valve opt-in via Steam personal game
data / share codes / match-history auth codes / CS2 GC; C: datasets públicos; D: contribuições voluntárias).

Método: ferramentas web (search_web, read_url_content) sobre documentação pública oficial.
Rotulagem obrigatória por afirmação: `VERIFIED_ONLINE` (URL citada + data/hora UTC) /
`VERIFIED_IN_REPO` (caminho relativo) / `INFERRED` (conhecimento prévio não verificado).
Proibido inventar URLs, endpoints, prazos, rate limits, hashes, contagens.

Entregáveis (exclusivos deste agente):
1. `training_runs/intermediate_domain_study/source_feasibility_report.md` (relatório longo, 400+ linhas)
2. `training_runs/intermediate_domain_study/legal_and_access_constraints.md` (curto, 50–120 linhas)
3. `training_runs/intermediate_domain_study/faceit_access_readiness.json`
4. `training_runs/intermediate_domain_study/valve_opt_in_feasibility.md` (curto, 60–140 linhas)
5. `datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json`

Proibições: não baixar demos; não fazer scraping; não contornar auth/ToS/rate limits; não enviar
solicitação à FACEIT; não escrever credenciais; não tocar em `datasets/mirage_v2/**`,
`training_runs/positioning_v2_real_temporal/**`, `src/**`, `models/**`; não treinar; sem arquivos cosméticos.

Verificação obrigatória: existência + tamanho > 0 dos 5 entregáveis; SHA-256 completo (64 hex) lido do
disco via hashlib; JSONs parseáveis; linter/hook de relatório se aplicável.

AVISO DE INTEGRIDADE (obrigatório, verbatim):
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade
implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work.
Integrity violations WILL be detected and your work WILL be rejected.
