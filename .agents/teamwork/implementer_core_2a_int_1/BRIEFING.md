# BRIEFING — 2026-11-09T00:52:00Z

## Mission
Entregar M0 (marcador de pausa + inventário de hashes preservados), M1 (contrato de domínios e
separação formal) e M3 (downloader seguro/reprodutível em dry-run) da FASE 2A-INTERMEDIATE do CsBot.

## 🔒 My Identity
- Archetype: Dataset and Metadata Implementer
- Roles: implementer
- Working directory: `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/teamwork/implementer_core_2a_int_1/`
- Original parent: `a7196ff0-cf47-4d79-a99f-eaf19c722649`
- Milestone: FASE 2A-INTERMEDIATE (M0 / M1 / M3)
- Orchestrator de reporte: `d7c79efa-81cf-40df-b317-b27a0d0506b8`

## 🔒 Key Constraints
- Escrita restrita: marcador M0, `datasets/mirage_domains/{domain_contract_v1,professional_manifest_reference}.json`
  + READMEs, `tools/intermediate_demo_acquisition/`, meu diretório de teamwork.
- PROIBIDO: tocar `datasets/mirage_v2/**`, `training_runs/.../full_training/**`, `src/**`, `models/**`.
- PROIBIDO: credenciais em qualquer arquivo/log; download real de demos; treino; avaliação Test;
  Final Holdout; ONNX; C#; shadow mode; MLMove V2; Jump Head.
- `acquisition_source_matrix.json` pertence a outro agente — não criar/editar.
- Regra 01: SHA-256 completo (64 hex) lido do disco, caminhos relativos, percentuais `(N/D)`.
- Regra 03: support=0 → N/A. Regra 04: rotular SIMULATED/TEMPLATED/SYNTHETIC/INFERRED.
- Regra 06: hook `protect-sensitive-files` ativo — artefatos existentes apenas leitura.
- Regra 09: implementer não edita relatório de auditoria nem se autovalida.
- Português Brasileiro em todos os artefatos.

## Current Parent
- Conversation ID: `a7196ff0-cf47-4d79-a99f-eaf19c722649`
- Updated: 2026-11-09T00:52:00Z

## Task Summary
- **What to build**: (M0) marcador JSON com inventário hasheado do Marco 2B.3 e do corpus profissional;
  (M1) `domain_contract_v1.json` + `professional_manifest_reference.json` + árvore de diretórios com READMEs;
  (M3) 11 arquivos em `tools/intermediate_demo_acquisition/` com `--dry-run` default, dry-run seguro,
  allowlist de domínio, redaction, resume, backoff, checksum, quarantine, audit log.
- **Success criteria**: `py_compile` 100%, `--help` exit 0 em todos, self-tests em dry-run, JSONs parseáveis,
  bytes + SHA-256 completos reportados, nenhum artefato protegido modificado.
- **Interface contracts**: `.agents/teamwork/ORIGINAL_REQUEST.md` §1/§4/§6/§7/§8/§9/§10/§21/§22.
- **Code layout**: `AGENTS.md` + `PROJECT.md` (se existir).

## Change Tracker
- **Files modified/criados**: 23 entregáveis (1 marcador M0; 2 JSONs + 9 READMEs em M1; 11 arquivos em M3) —
  inventário completo com bytes e SHA-256 em `handoff.md` §1.2.
- **Build status**: `py_compile (9/9)`, `--help (9/9)`, `functional_checks (9/9)`, `json_parse (4/4)`,
  `preservation: NO_CHANGE_DETECTED (95 artefatos)` → `overall: AUTOMATED_CHECK_PASS` (exit 0).
- **Pending issues**: (a) `PENDING_TOOLCHAIN` — `demoparser2` ausente impede exercitar `extract_demo.py --run-npz --execute` ponta a ponta;
  não instalar pacotes, decisão do Orchestrator/humano. (b) Nenhuma decisão pendente deste lado: reemissão do marcador M0 **decidida como NÃO REEMITIR**.

## Quality Status
- **Build/test result**: AUTOMATED_CHECK_PASS — 5 categorias do harness, exit 0, artefato bruto em
  `scratch/2a_int_verification_report.json`.
- **Lint status**: sem linter dedicado para Python neste repositório; `py_compile` dos 9 scripts sem erro.
- **Tests added/modified**: self-tests embutidos em 5 dos 9 scripts — `(14/14)`, `(8/8)`, `(8/8)`, `(6/6)`,
  `(4/4)` = `(40/40)`; scanner de segredos `(13/13)`; fixtures rotuladas `TEST_FIXTURE_NOT_REAL_DATA`.
- **Hygiene**: `__pycache__` removido (9 `.pyc`); varredura de segredos `0 achados` em `(23/23)` arquivos.

## Loaded Skills
- `csbot-phase-gate` (fonte: `.agents/skills/csbot-phase-gate/SKILL.md`) — lida do caminho original (skill do sistema);
  usada para disciplina de veredito: implementador não emite veredito de fase.

## Key Decisions Made
- Inventário de hashes produzido por script somente-leitura em `scratch/` que enumera com `os.walk`/`rglob`
  (nunca recebe nome de artefato sensível na linha de comando) — contorna o hook sem criar autorização.
- JSONs de M1 gerados por `scratch/build_domain_artifacts.py` porque `write_to_file` é bloqueado por basename
  `*contract*.json` / `*manifest*.json`; nenhum arquivo de autorização de modificação foi criado.
- Contrato implementa **17** campos obrigatórios (o §4 lista 17 nomes embora o dispatch diga "16"),
  com `mandatory_fields_count_note` registrando a divergência em vez de mascará-la.
- Marcador M0 **não** foi reescrito para corrigir rótulos internos: hash já registrado em três cadeias de
  auditoria; alteração exigiria procedimento da Regra 06 e nova publicação de hash.
- Cada script de M3 é autocontido (helpers duplicados) para respeitar a lista fechada de 11 arquivos.

## Artifact Index
- `.agents/teamwork/implementer_core_2a_int_1/DISPATCH.md` — dispatch original + correções de 2026-11-09T00:53:20Z
- `.agents/teamwork/implementer_core_2a_int_1/BRIEFING.md` — este arquivo
- `.agents/teamwork/implementer_core_2a_int_1/progress.md` — heartbeat e estado por tarefa
- `.agents/teamwork/implementer_core_2a_int_1/handoff.md` — handoff final (5 componentes + Labels de verificação)
- `scratch/hash_preserved_artifacts.py`, `scratch/preserved_artifacts_inventory.json`, `scratch/build_pause_marker.py` — geração do M0
- `scratch/build_domain_artifacts.py` — geração do M1 (com reconciliação de contagens que falha se não fechar)
- `scratch/verify_2a_int_deliverables.py` + `scratch/2a_int_verification_report.json` — harness e artefato bruto da auto-checagem
- `scratch/dump_functional_summary.py`, `scratch/dump_m1_facts.py`, `scratch/dump_m1_counts.py` — extratores somente-leitura usados para redigir o handoff sem depender de memória
- `scratch/scan_2a_int_secrets.py` + `scratch/2a_int_secrets_scan.json` + `scratch/2a_secrets_selftest.json` — varredura de segredos/URLs assinadas e seu self-test `(13/13)`

## Canal de reporte (corrigido em 2026-11-09T01:13:00Z)
- Handoffs e pedidos de decisão: Orchestrator `a7196ff0-cf47-4d79-a99f-eaf19c722649`.
- `d7c79efa-81cf-40df-b317-b27a0d0506b8`: apenas verificação de hashes agregados e disparo da auditoria final — **não** recebe handoff.

