# Progress ? researcher_2a_int_1

Last visited: 2026-11-09T01:10:11Z

## Estado

- [x] Leitura obrigat?ria: `ORIGINAL_REQUEST.md` ?2, ?4, ?5, ?6, ?7, ?8, ?21, ?22; `AGENTS.md`; skills
      `csbot-report-skeptic` e `csbot-phase-gate`.
- [x] Registro de dispatch e briefing inicial.
- [x] Pesquisa web: 38 consultas de URL (25 recuperadas + 13 falhas) e 5 buscas de descoberta, em
      `research_log.md`.
- [x] Entreg?vel 1: `training_runs/intermediate_domain_study/source_feasibility_report.md` (858 linhas).
- [x] Entreg?vel 2: `training_runs/intermediate_domain_study/legal_and_access_constraints.md` (98 linhas).
- [x] Entreg?vel 3: `training_runs/intermediate_domain_study/faceit_access_readiness.json` (JSON v?lido).
- [x] Entreg?vel 4: `training_runs/intermediate_domain_study/valve_opt_in_feasibility.md` (113 linhas).
- [x] Entreg?vel 5: `datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json` (JSON v?lido).
- [x] Verifica??o: exist?ncia + tamanho > 0 + SHA-256 (64 hex) + parse JSON + hook `validate_generated_report`
      (5/5 ALLOW, 0 viola??es) ? r?tulo `AUTOMATED_CHECK_PASS` (auto-checagem; **n?o** ? valida??o independente).
- [x] Handoff escrito.
- [x] Higiene de layout (`AGENTS.md` / layout compliance): em **2026-11-09T01:08:42Z** removi 7 dumps
      tempor?rios `_tmp_*.txt` do diret?rio de metadados. A pasta passou a conter apenas metadados
      (`BRIEFING.md`, `DISPATCH.md`, `handoff.md`, `progress.md`, `research_log.md`).
      Os hashes dos 5 entreg?veis foram recomputados ap?s a limpeza e permaneceram **id?nticos**.
- [x] **Corre??o do Orchestrator (2026-11-09T01:08:48Z) ? capturas devem ser preservadas, n?o apagadas.**
      Falha do agente: a remo??o (01:08:42Z) ocorreu **6 s antes** da instru??o de mover para `scratch/`;
      `Remove-Item -Force` ? definitivo e os 7 originais n?o puderam ser recuperados. Mitiga??o honesta:
      **recaptura** das p?ginas em 2026-11-09T01:09:09Z?01:09:17Z (GET ?nico por URL) em
      `scratch/2a_intermediate_research_cache/` (9 arquivos, 1.590.118 B), com
      `INDEX.md` (arquivo ? URL ? UTC ? url_status ? uso no ?N) e `_recapture_log.json`.
      Os arquivos est?o rotulados `RECAPTURED` ? **n?o** s?o os originais, e a diferen?a de bytes ? de
      marca??o (HTML bruto vs. extra??o textual). Bloqueios preservados como bloqueios: Termos FACEIT
      (403), artigo de Elo (403?404), wiki Valve (challenge Anubis 1.23.1) ? conclus?es seguem `UNVERIFIED`.

## Veredito

`INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`

## Pend?ncias / bloqueios que dependem de humano

1. Leitura dos Termos FACEIT (HTTP 403 para automa??o).
2. Submiss?o da aplica??o do FACEIT Downloads API (30 dias esperados; free tier 1500 requests ou 200 GB).
3. Aprova??o do instrumento de consentimento da Fonte D.
4. Decis?o sobre compatibilidade de CC BY-NC-SA 4.0 (PureSkill CS2 CSDS) com o projeto.

## Nota de auditoria de canal (2026-11-09T01:08Z)

Registro para precis?o do rastro: a mensagem de handoff das 2026-11-09T22:06:39Z foi endere?ada ao campo
`Recipient` com o ID **`a7196ff0-cf47-4d79-a99f-eaf19c722649`** (Orchestrator) e a ferramenta retornou
`Message sent to "a7196ff0-cf47-4d79-a99f-eaf19c722649"`. O ID misturado citado depois em prosa
(`a7196ff0-cf47-40df-...`) foi apenas um erro de transcri??o no texto narrativo, **n?o** no campo de
endere?amento ? n?o houve entrega a destinat?rio inv?lido. Conforme orienta??o do Sentinel, n?o houve
reenvio: a coordena??o do canal ? dele.
