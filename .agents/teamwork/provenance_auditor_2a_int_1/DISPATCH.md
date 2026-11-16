# DISPATCH — provenance_auditor_2a_int_1

## 2026-11-09T01:24:56Z
[Fonte: sender=a7196ff0-cf47-4d79-a99f-eaf19c722649, priority=HIGH]

Você é o **Data Provenance and Compliance Auditor** da fase FASE 2A-INTERMEDIATE do CsBot (papel 5 do §3). Você é **SOMENTE LEITURA** sobre o projeto: pode ler qualquer arquivo, mas só pode **escrever dentro do seu próprio diretório** `.agents/teamwork/provenance_auditor_2a_int_1/` (já criado). Proibido criar/editar/apagar qualquer arquivo em `src/`, `tools/`, `tests/`, `datasets/`, `models/`, `training_runs/` ou `scratch/`. Proibido treinar, avaliar no Test, consultar Final Holdout, exportar ONNX, tocar C#. Proibido instalar pacotes. Proibido baixar demos.

- Project root: `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`
- Idioma: Português Brasileiro.
- Skill obrigatória: `.agents/skills/csbot-dataset-forensics/SKILL.md`. Leia também `.agents/skills/csbot-phase-gate/SKILL.md`.

### LEITURA OBRIGATÓRIA
1. `.agents/teamwork/ORIGINAL_REQUEST.md` — INTEGRAL. Foco em §1, §4, §5, §6, §7, §8, §9, §10, §11, §19, §21, §22 (Gates A e B).
2. `AGENTS.md` (Regras 01–09) — especialmente Regra 01, 02, 04, 06.

### OBJETO DA AUDITORIA
Artefatos de governança e dados:
- `datasets/mirage_domains/domain_contract_v1.json` (30587 B)
- `datasets/mirage_domains/professional_manifest_reference.json` (17225 B)
- `datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json` (31073 B)
- `datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json` (21749 B)
- `datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json` (14712 B)
- `datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json` (14026 B)
- `datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json` (9206 B)
- `training_runs/intermediate_domain_study/intermediate_splits_proposal.json` (15270 B)
- `tools/intermediate_demo_acquisition/` (11 arquivos) e `training_runs/intermediate_domain_study/{source_feasibility_report.md, legal_and_access_constraints.md, faceit_access_readiness.json, valve_opt_in_feasibility.md}`
- `training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json` (37114 B)

### VERIFICAÇÕES OBRIGATÓRIAS
A) Varredura de segredos PRÓPRIA (scanner autotestado com `--self-test`, fixtures positivas/negativas, reportar `(x/y)`), cobrindo acquisition_source_matrix.json, os 12 artefatos da Wave 2, os 8 artefatos analíticos e os 11 arquivos de tools/. Registrar caminho+bytes+SHA-256 do JSON de resultado. Detector não autotestado → `SECRETS_SCAN_UNVERIFIED`.
B) Integridade do corpus profissional (Regra 02/§1): recalcular amostra determinística >=30 arquivos incluindo os 6 shards e 6 sidecars; `(N/D)` de matches; `datasets/mirage_domains/professional/` só README.md.
C) Não-fabricação de dados intermediários: varrer `datasets/mirage_domains/**` por `*.dem`, `*.npz`, `*.parquet` (esperado 0); 4 manifests com `records: []` e contabilidade `(0/0)` com numerator/denominator explícitos.
D) Contrato de domínios (§4): 3 domínios + 7 subdomínios; 16 campos obrigatórios `(16/16)`; proibição de conversão de rank; FACEIT 1-4 e 9-10 excluídos; Valve Premier `NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT`; `UNKNOWN` não promovido; critérios de aceitação/exclusão do §7.
E) Downloader (§9): dry-run padrão, resumable, backoff, rate limiting, checksum, validação de arquivo, decompressão segura (path traversal), dedup por hash, allowlist, audit log, redação de credenciais, retry_limit, quarentena — `(N/14)`. Nenhuma URL assinada persistida; segredos só de env/secret store.
F) Gates A/B (§22) por critério: PASS/FAIL/N/A (0/0)/UNVERIFIED.
G) Fidelidade do relatório de viabilidade: cache recapturado não é evidência primária; `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`; UNVERIFIED não promovidas; `steam_icsgoplayers_730.txt` continua índice genérico (falha F12 preservada).

### FORMATO OBRIGATÓRIO DO PARECER
`.agents/teamwork/provenance_auditor_2a_int_1/parecer_provenance_audit.md` com VEREDITO (`PASS`/`CONDITIONAL`/`FAIL`), sumário 5 linhas, tabela verificação->comando->resultado->(N/D), hashes recalculados, varredura (caminho+bytes+SHA-256 + fixtures `(x/y)`), Gate A/B por critério, ressalvas numeradas com impacto, `## O que NÃO pude verificar`. Proibido `0.0%`.

Ao terminar: SHA-256 do próprio parecer, `handoff.md`, e mensagem ao Orchestrator (`d7c79efa-81cf-40df-b317-b27a0d0506b8`).

---

## 2026-11-09T01:26:48Z
[Fonte: sender=a7196ff0-cf47-4d79-a99f-eaf19c722649, priority=HIGH]

**Context**: FASE 2A-INTERMEDIATE — duas exigências do Sentinel que afetam diretamente o parecer.

**Content**:
1) Declare explicitamente o isolamento de papel (Regra 09). O parecer deve conter `## Isolamento de papel` com:
- confirmação de que operei como **leitor** sobre `datasets/`, `tools/`, `tests/`, `src/` e `training_runs/positioning_v2_real_temporal/` — **sem nenhuma escrita** nesses caminhos;
- o caminho exato onde escrevi (somente `.agents/teamwork/provenance_auditor_2a_int_1/`);
- a declaração literal: `write_scope: OWN_AGENT_DIRECTORY_ONLY`.
Se qualquer escrita ocorrer fora do meu diretório, o parecer inteiro é inválido. Scanner e JSONs de resultado vão no meu diretório, nunca em `scratch/` nem `tools/`.

2) Reconte as enumerações da spec eu mesmo, se tocar no assunto. Orchestrator decidiu `SPEC_ENUMERATION_AUTHORITATIVE`. A tabela do dispatcher não é fonte aceitável — contar do texto literal de `.agents/teamwork/ORIGINAL_REQUEST.md` e citar intervalo de linhas.

3) `tools/intermediate_demo_acquisition/__pycache__/` (5 `.pyc`) é `TRANSIENT_CACHE`, não entregável nem evidência; a contagem de "11 arquivos em tools/" deve considerar apenas os 11 entregáveis (README, `config.example.json`, 9 `.py`). Estado alvo ao encerramento: 11 arquivos e nenhum `.pyc`.

4) Confirmar por conta própria: (a) `demoparser2` AUSENTE → extração DEM→NPZ `PENDING_TOOLCHAIN`, sem tratar como falha da fase e sem instalar; (b) `EVIDENCE_LOSS_EVENT` (remoção dos 7 `_tmp_*` originais às 01:08:42Z, recaptura 01:09:09–01:09:17Z) → fidelidade `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` e cache `RECAPTURED`, nunca primário.

**Action**: aplicar 1–3 e enviar parecer com VEREDITO explícito, caminho/bytes/SHA-256, `(x/y)` de fixtures e resultado por critério de Gate A/B.

---

## 2026-11-09T01:27:42Z
[Fonte: sender=a7196ff0-cf47-4d79-a99f-eaf19c722649, priority=HIGH]

**Context**: requisito adicional do Sentinel, específico do meu papel. É **condição de PASS**.

**Content**: integridade byte-a-byte dos **95 artefatos preservados** inventariados em `preserved_artifacts_inventory` do marcador `PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json` (37114 B, `465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad`).
1. Ler o inventário do marcador (fonte de verdade, junto com `professional_manifest_reference.json`).
2. Recalcular SHA-256 de cada um dos 95 artefatos do disco e comparar.
3. Reportar `N/N`, lista de divergências (caminho + hash do marcador + recalculado + mtime) e total de bytes conferido.
4. Verificar que o marcador continua 37114 B e `465f4cb9…13efad`.
5. Cruzar com `.agents/teamwork/orchestrator_2a_intermediate/ARTIFACT_INVENTORY.md` **apenas** nos blocos `[CURRENT — VIGENTE]`; ignorar integralmente `SUPERSEDED — NÃO USAR`.
Se qualquer hash divergir → falha grave, veredito não pode ser `PASS`, mesmo que todo o resto esteja impecável.

**Action**: incluir seção `## Integridade dos 95 artefatos preservados` com tabela e `(N/N)`; enviar ao Orchestrator (`d7c79efa-81cf-40df-b317-b27a0d0506b8`).
