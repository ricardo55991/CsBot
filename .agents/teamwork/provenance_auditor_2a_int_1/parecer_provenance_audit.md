# PARECER DE AUDITORIA DE PROVENIÊNCIA E COMPLIANCE

**Fase:** FASE 2A-INTERMEDIATE (Estudo de viabilidade e aquisição do corpus Mirage intermediário)
**Papel:** Data Provenance and Compliance Auditor (papel 5 do §3)
**Agente:** `provenance_auditor_2a_int_1`
**Data da auditoria (UTC):** 2026-11-09T01:24Z — 2026-11-09T01:35Z
**Raiz do repositório:** `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`
**Skills aplicadas:** `csbot-dataset-forensics`, `csbot-phase-gate`
**Modo de integridade (lido de `ORIGINAL_REQUEST.md :: Initial Request`, linha 13):** `development`

---

## VEREDITO

# `CONDITIONAL`

Não é `PASS` porque **uma marcação obrigatória de fidelidade está ausente de 100% dos entregáveis da fase** (Ressalva R1): o rótulo `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` tem **zero ocorrências** nos 13 arquivos de `training_runs/intermediate_domain_study/` e **zero ocorrências** em `research_log.md`, embora o §12 do relatório de viabilidade afirme que as URLs "foram recuperadas nesta sessão" com horários (00:51Z–00:56Z) de capturas que **foram fisicamente destruídas** às 01:08:42Z.

Não é `FAIL` porque **nenhum dos padrões proibidos foi encontrado**: zero arquivo de dado intermediário, zero identificador de demo inventado, zero hash de demo fabricado, zero segredo real, corpus profissional byte-idêntico (95/95 e 33/33), downloader íntegro (14/14 requisitos, 40/40 casos de autoteste, 7/7 barreiras funcionais) e o evento de perda de evidência está registrado e rotulado (`RECAPTURED`) no cache que sobreviveu.

---

## Sumário (5 linhas)

1. **Zero fabricação:** `datasets/mirage_domains/**` contém 16 arquivos, todos JSON/README; `.dem` = nenhum, `.npz` = nenhum, `.parquet` = nenhum; nenhum identificador de demo FACEIT e nenhum campo de hash de demo preenchido.
2. **Corpus profissional preservado:** 95/95 artefatos do marcador com SHA-256 idêntico (212.960.002 bytes), 33/33 referências do manifesto (incluindo os 6 shards e 6 sidecars), 57/57 no inventário (3.021.280 bytes), corpus externo 444 NPZ / 856.405.885 bytes recontado.
3. **Zero segredo real:** scanner próprio autotestado (11/11 positivos disparam, 6/6 negativos silenciam) em 41 arquivos / 1.224.167 bytes → 1 hit, triado como linha documental de `redact()` no `README.md`, sem credencial.
4. **Contrato e downloader conformes:** 3 domínios + 7 subdomínios, campos do §4 17/17, critérios do §7 25/25, proibição de conversão de rank explícita, FACEIT 1–4 e 9–10 excluídos, Premier `NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT`, `UNKNOWN` não promovido; downloader 14/14 com `--execute` bloqueado.
5. **Bloqueio do `PASS`:** falta o rótulo `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` nos entregáveis e o cache `RECAPTURED` vive só em `scratch/`; o Gate A está corretamente em `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING` e o Gate B é integralmente `N/A (0/0)`.

---

## Isolamento de papel

- Operei **exclusivamente como leitor** sobre `datasets/`, `tools/`, `tests/`, `src/` e `training_runs/positioning_v2_real_temporal/`. Nenhuma escrita, renomeação ou remoção foi executada nesses caminhos.
- Todo artefato que escrevi está em **`.agents/teamwork/provenance_auditor_2a_int_1/`** — scanner, scripts de verificação, JSONs de resultado, `BRIEFING.md`, `DISPATCH.md`, `progress.md`, este parecer e o `handoff.md`.
- O scanner de segredos e o JSON de resultado foram gravados **no meu próprio diretório**, nunca em `scratch/` nem em `tools/`.
- `tools/intermediate_demo_acquisition/__pycache__/` foi tratado como `TRANSIENT_CACHE`: não é entregável, não é evidência e não entra na contagem de arquivos da ferramenta. Para não gerar `.pyc` novo, a prova funcional do downloader foi executada com `sys.dont_write_bytecode = True` e a suíte de testes com `PYTHONDONTWRITEBYTECODE=1` e `-p no:cacheprovider`. A contagem permaneceu **5 `.pyc`** antes e depois da auditoria (nenhum arquivo criado por mim).
- Prova de não-perturbação: ao final da auditoria repeti as duas verificações mais sensíveis e obtive os mesmos resultados do início — **95/95** artefatos preservados e **57/57** linhas do inventário, com zero divergência.

```
write_scope: OWN_AGENT_DIRECTORY_ONLY
```

---

## Objeto auditado — hashes recalculados por mim

Comando: `Get-FileHash -Algorithm SHA256 <path>` sobre cada arquivo (leitura direta do disco).

| # | Caminho (relativo) | Bytes | SHA-256 recalculado | Confere com o despacho |
|---|---|---|---|---|
| 1 | `datasets/mirage_domains/domain_contract_v1.json` | 30587 | `95df901801d0a96495c7d3b30d08862513563b1b790e202b0738369fec02ae28` | SIM |
| 2 | `datasets/mirage_domains/professional_manifest_reference.json` | 17225 | `6584877374b917b29a0f43b70e5bfd5dd0999762765734cdaa4f28e5a15966dd` | SIM |
| 3 | `datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json` | 31073 | `f09ac2a5962bb69fb38361739200b7f656d29e25f0d3c68a2c1b82fde380f3e8` | SIM |
| 4 | `datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json` | 21749 | `2dff36579e263456cdf1f3b51c7d8e500218c079071d5f06f090c59ce2ffb93e` | SIM |
| 5 | `datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json` | 14712 | `f6742f4854c73f55bd343a702cf5db9c805ba61250c0c92a52c92955ade3f99f` | SIM |
| 6 | `datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json` | 14026 | `e600404c4427f51b31cf524b42af966fa1911f25e36b3efb60e9e5ff6c35d8dc` | SIM |
| 7 | `datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json` | 9206 | `f3dbd17be5e7e436e3ae9f97a2749278e80c74d16670af4edb153b0c38f8e815` | SIM |
| 8 | `training_runs/intermediate_domain_study/intermediate_splits_proposal.json` | 15270 | `bbb611feeeeba64f3cd6ff0e3d7810b60341b0ab113e08538f6a86ff7119cb3a` | SIM |
| 9 | `training_runs/intermediate_domain_study/source_feasibility_report.md` | 59871 | `55f1d9d2cda42297885d2a05471dc651ba63c17e4eabdeecc354d171109f2d4c` | (não declarado no despacho) |
| 10 | `training_runs/intermediate_domain_study/legal_and_access_constraints.md` | 6439 | `989ceb724f918da5d298a08452bc8eda6dbfd1d217c1a2cd7720ab7f7a26555a` | (não declarado) |
| 11 | `training_runs/intermediate_domain_study/faceit_access_readiness.json` | 15880 | `26739883cec11877c83ecb33bd821fa9fd478fa84847058d65d4f6e384b20712` | (não declarado) |
| 12 | `training_runs/intermediate_domain_study/valve_opt_in_feasibility.md` | 7987 | `f63ba568aa0fd9de456b7c8fd4ca9fb1b4e1f6e73ae0f91c56a8b60e91f8f61f` | (não declarado) |
| 13 | `training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json` | 37114 | `465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad` | SIM |

**Resultado: (13/13)** — bytes e SHA-256 coincidem exatamente com os declarados no despacho. Nenhum truncamento de hash, nenhum caminho absoluto.

---

## Tabela mestra — verificação → comando → resultado → `(N/D)`

| Verificação | Comando reproduzível | Resultado | `(N/D)` |
|---|---|---|---|
| A. Varredura de segredos (autoteste) | `python .agents/teamwork/provenance_auditor_2a_int_1/scan_secrets.py --self-test` | Autoteste `PASS` | `(11/11)` positivos dispararam; `(6/6)` negativos silenciaram; `(17/17)` fixtures |
| A. Varredura de segredos (varredura) | `python .agents/teamwork/provenance_auditor_2a_int_1/scan_secrets.py --scan --out secrets_scan_result.json` | 41 arquivos, 1.224.167 bytes, 1 hit documental, nenhuma credencial real | `(40/41)` arquivos sem hit; `(0/1)` segredo real |
| B. Corpus profissional vs manifesto | `python .agents/teamwork/provenance_auditor_2a_int_1/forensic_checks.py --out checks_result.json` | 33 referências com hash e bytes idênticos, incluindo 6 shards e 6 sidecars | `(33/33)` |
| B. `datasets/mirage_domains/professional/` | `Get-ChildItem datasets/mirage_domains/professional` | Apenas `README.md` (3093 B) | `(1/1)` |
| B. `full_training/` integridade | `forensic_checks.py` (enumeração) | 57 arquivos, todos com tamanho > 0 | `(57/57)` |
| B. Corpus externo de NPZ | `Get-ChildItem F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage -Filter *.npz` | 444 arquivos, 856.405.885 bytes — igual ao declarado | `(444/444)` |
| C. Varredura de dados intermediários | `Get-ChildItem -Recurse -File datasets/mirage_domains -Filter *.dem/.npz/.parquet` | nenhum em todas as três extensões; 16 arquivos no total | `(0/0)` |
| C. Contabilidade `(0/0)` nos 4 manifests | `python .agents/teamwork/provenance_auditor_2a_int_1/inspect_accounting.py` | 4/4 com `numerator` = 0, `denominator` = 0, `aggregation_value: null`, status `N/A_ZERO_DENOMINATOR` | `(4/4)` |
| C. Anti-fabricação de identificadores e hashes | `python .agents/teamwork/provenance_auditor_2a_int_1/scan_fabrication.py` | nenhum identificador de demo, nenhum campo de hash de demo preenchido | `(0/0)` |
| C. Hashes de referência do pipeline | `Get-FileHash` em 5 arquivos citados | 5 hashes conferem no disco | `(5/5)` |
| D. Contrato de domínios — campos §4 | `python .agents/teamwork/provenance_auditor_2a_int_1/check_contract.py` | 17 campos exigidos, todos declarados | `(17/17)` |
| D. Contrato de domínios — domínios/subdomínios | `check_contract.py` | 3 domínios + 7 subdomínios presentes | `(10/10)` |
| D. Critérios de aceitação e exclusão do §7 | `check_contract.py` (recontagem na spec) | 13 + 12 critérios da spec cobertos por AC01–AC13 e EX01–EX13 | `(25/25)` |
| E. Requisitos do downloader §9 | `python .agents/teamwork/provenance_auditor_2a_int_1/audit_downloader.py` | 14 requisitos com evidência arquivo:linha | `(14/14)` |
| E. Autotestes embutidos dos 9 scripts | `python .agents/teamwork/provenance_auditor_2a_int_1/run_selftests.py` | 5 scripts com `--self-test`, todos exit 0 | `(40/40)` casos |
| E. Barreiras funcionais (sem rede) | `python .agents/teamwork/provenance_auditor_2a_int_1/probe_downloader_functional.py` | HTTPS, allowlist, IP literal, userinfo, URL assinada, allowlist vazia | `(7/7)` |
| E. `--execute` bloqueado | `python tools/.../download_demo.py --help` + leitura de `download_demo.py:435` | Exige `CSBOT_APPROVED_SOURCE_ID`; sem ele, exit 2 | `(1/1)` |
| Integridade dos 95 preservados | `python .agents/teamwork/provenance_auditor_2a_int_1/verify_preserved_artifacts.py` | SHA-256 idêntico, 212.960.002 bytes | `(95/95)` |
| Cruzamento com `ARTIFACT_INVENTORY.md` | `python .agents/teamwork/provenance_auditor_2a_int_1/verify_inventory.py` | Somente blocos `[CURRENT — VIGENTE]`; 3.021.280 bytes | `(57/57)` |
| Suíte da fase (§20) | `python -m pytest tests/test_phase2a_intermediate_domain.py -q -p no:cacheprovider` | `20 passed in 0.80s` | `(20/20)` |
| G. Fidelidade relatório↔fonte | `Select-String -Pattern 'REPORT_TO_SOURCE_FIDELITY_UNVERIFIED'` nos 13 arquivos + `research_log.md` | zero ocorrências | `(0/13)` arquivos marcados |
| G. `steam_icsgoplayers_730.txt` é índice genérico | contagem no arquivo em disco | `ICSGOPlayers` sem ocorrência, `IGCVersion_730` sem ocorrência, `Access Match History` sem ocorrência | `(1/1)` falha F12 preservada |
| Gate 05. Selos humanos indevidos | `Select-String 'APPROVED_BY_USER','HUMAN_CAPTURE_IN_GAME'` | 2 menções, ambas de ressalva/atribuição ao humano | `(0/0)` selo indevido |

---

## A) Varredura de segredos PRÓPRIA, com detector autotestado

**Scanner:** `.agents/teamwork/provenance_auditor_2a_int_1/scan_secrets.py` (escrito integralmente no meu diretório; SHA-256 `4035ddf4b309cc053d38f2ed5e21b6fbfb833332d26cc70f1aa9de44e1146371`).

**Detetores (11):** `OPENAI_SK` (`sk-`), `GITHUB_PAT_CLASSIC` (`ghp_`), `GITHUB_PAT_FINE` (`github_pat_`), `AWS_AKIA` (`AKIA`), `JWT`, `STEAM_LOGIN_SECURE_ASSIGN`, `PASSWORD_ASSIGN`, `TOKEN_ASSIGN`, `AWS_SIGNATURE` (`X-Amz-Signature`), `AUTH_HEADER` (`Authorization: Bearer/Basic`), `PRIVATE_KEY_BLOCK`.

**Supressores (regras negativas):** placeholder angular `<...>`/`${...}`/`{{...}}`, palavra de placeholder (`your`, `example`, `changeme`, `redacted`, `from_env`…), nome de variável de ambiente (`^[A-Z][A-Z0-9_]{3,}$`), SHA-256 documentado de 64 hex em contexto `sha256|checksum|hash|digest`, literais de exemplo conhecidos (`deadbeef`, `AKIAIOSFODNN7EXAMPLE`) e referência segura a código (`os.environ`, `os.getenv`, `secret_store`).

### Autoteste — resultado `(17/17)`

```
=== AUTOTESTE DO DETECTOR ===
  [FIRED ] P01_OPENAI_SK                           OPENAI_SK
  [FIRED ] P02_GHP                                 GITHUB_PAT_CLASSIC
  [FIRED ] P03_GITHUB_PAT_FINE                     GITHUB_PAT_FINE
  [FIRED ] P04_AKIA                                AWS_AKIA
  [FIRED ] P05_JWT                                 JWT
  [FIRED ] P06_STEAM                               STEAM_LOGIN_SECURE_ASSIGN
  [FIRED ] P07_PASSWORD                            PASSWORD_ASSIGN
  [FIRED ] P08_TOKEN                               TOKEN_ASSIGN
  [FIRED ] P09_AMZ                                 AWS_SIGNATURE
  [FIRED ] P10_AUTH_HEADER                         AUTH_HEADER
  [FIRED ] P11_PRIVATE_KEY                         PRIVATE_KEY_BLOCK
  [SILENT] N01_VALUE_FROM_ENV                      hits=[]      (<VALUE_FROM_ENV>)
  [SILENT] N02_YOUR_TOKEN_HERE                     hits=[]      ("<YOUR_TOKEN_HERE>")
  [SILENT] N03_ENV_VAR_NAME                        hits=[]      (token: "FACEIT_API_TOKEN")
  [SILENT] N04_DOC_SHA256                          hits=[]      (artifact_sha256 de 64 hex)
  [SILENT] N05_DEADBEEF_SIG                        hits=[]      (X-Amz-Signature=deadbeef)
  [SILENT] N06_STEAM_NAME_ONLY                     hits=[]      (nome de cookie em lista de proibição)

RESULTADO AUTOTESTE: positivos que dispararam (11/11); negativos silenciosos (6/6); fixtures totais (17/17)
VEREDITO AUTOTESTE: PASS
```

**Transparência sobre o autoteste:** na primeira execução o autoteste **reprovou o meu próprio detector** em 2 de 11 positivos (`P04_AKIA` era mascarado por supressão de palavra-placeholder e `P07_PASSWORD` não casava chaves com prefixo como `db_password`). Corrigi o detector e reexecutei até `(17/17)`. Sem esse ciclo, o resultado teria de ser reportado como `SECRETS_SCAN_UNVERIFIED`.

### Varredura — 41 arquivos, 1.224.167 bytes

Cobertura efetiva (superconjunto dos conjuntos exigidos):

| Grupo | Arquivos | Coberto |
|---|---|---|
| `datasets/mirage_domains/**` (inclui `acquisition_source_matrix.json` e os 5 manifests) | 16 | SIM |
| `training_runs/intermediate_domain_study/**` (inclui os 8 artefatos analíticos) | 13 | SIM |
| `tools/intermediate_demo_acquisition/` (README + `config.example.json` + 9 `.py`) | 11 | SIM |
| Marcador de pausa | 1 | SIM |
| **Total** | **41** | — |

**Resultado:** `hits_total = 1`. Triagem do único hit:

- `tools/intermediate_demo_acquisition/README.md:146` — detetor `PASSWORD_ASSIGN`, casando o trecho documental dentro da frase que descreve quais pares o `redact()` mascara. **Classificação: `DOCUMENTATION_EXAMPLE`** — não há valor de credencial, não é chave, não é token. Nenhum arquivo com segredo real `(0/41)`.

**Artefato de resultado:**

| Campo | Valor |
|---|---|
| Caminho (relativo) | `.agents/teamwork/provenance_auditor_2a_int_1/secrets_scan_result.json` |
| Bytes | 9827 |
| SHA-256 | `eb8217f96dd82152929d1ead9be6e5eac2b1cd1be23b979dfb7b7078852e7186` |

**Confirmações complementares:** `config.example.json` tem `credentials` com strings vazias, `secret_source: "ENV"`, `secret_env_vars` mapeando nomes lógicos → nomes de variáveis (nenhum valor), `signed_url_persistence_allowed: false` e `load_config()` que **rejeita** `true` (`download_demo.py:114-115`). A única ocorrência da string `steamLoginSecure` em `acquisition_source_matrix.json:231` é uma **nota de proibição**, sem valor associado. Nenhuma URL assinada com valor real em nenhum dos 41 arquivos `(0/41)`.

---

## B) Integridade do corpus profissional (Regra 02 / §1)

**Método:** recálculo próprio de SHA-256 e bytes de todas as 33 referências de `datasets/mirage_domains/professional_manifest_reference.json`, sem reutilizar contagem de relatório.

- Referências com hash **e** tamanho idênticos: **`(33/33)`**. Entre elas estão os **6 shards** (`shard_000.parquet` … `shard_005.parquet`) e os **6 sidecars** (`label_sidecar_v2/shard_000_labels.parquet` … `shard_005_labels.parquet`) — `(12/12)`.
- `datasets/mirage_domains/professional/` contém **apenas** `README.md` (3093 B, SHA-256 `d0489a52d3e4731d1e19924214122aa0d43c39ec15890700b1ac207e14d753ac`) — nenhuma cópia nem movimentação do corpus: `(1/1)`.
- `training_runs/positioning_v2_real_temporal/full_training/`: 57 arquivos, todos com tamanho > 0 → `(57/57)`.
- Corpus externo recontado por enumeração de diretório: **444 arquivos `.npz`, 856.405.885 bytes** — idêntico ao declarado (`(444/444)` e bytes exatos).
- `datasets/mirage_v2/`: 176 arquivos, 102.952.120 bytes enumerados (sem modificação observada).

---

## C) Não-fabricação de dados intermediários

- `datasets/mirage_domains/**` → **nenhum `.dem`, nenhum `.npz`, nenhum `.parquet`**; total de 16 arquivos, todos `.json` ou `README.md`. As 7 subpastas de `intermediate_competitive/` contêm **somente** seu `README.md` (sem diretório cosmético vazio: cada uma tem conteúdo real).
- Os 4 manifests têm inventário vazio e contabilidade sem ambiguidade:

| Manifest | `records` | `numerator` / `denominator` | `aggregation` | `aggregation_status` |
|---|---|---|---|---|
| `intermediate_demo_inventory_v1.json` | lista vazia (len 0) | 0 / 0 | `(0/0)` | `N/A_ZERO_DENOMINATOR` |
| `intermediate_npz_manifest_v1.json` | lista vazia (len 0) | 0 / 0 | `(0/0)` | `N/A_ZERO_DENOMINATOR` |
| `pilot_download_manifest.json` | **chave ausente** — equivalente: `downloads_attempted` 0, `downloads_completed` 0, `downloads_failed` 0, `resume_state` nulo | 0 / 0 | `(0/0)` | `N/A_ZERO_DENOMINATOR` |
| `quarantine_manifest.json` | lista vazia (len 0) | 0 / 0 | `(0/0)` | `N/A_ZERO_DENOMINATOR` |

  Os quatro trazem `aggregation_value: null` e nota textual explícita de que `(0/0)` **não** é taxa de aprovação, sucesso ou rejeição. Nenhuma métrica é preenchida com valor numérico onde não há dado. `(4/4)` conformes; a assimetria de schema do `pilot_download_manifest.json` está registrada como R3.
- **Identificadores e hashes inventados:** nenhuma ocorrência de identificador no formato FACEIT (`1-<uuid>`) e nenhum campo `demo_sha256`/`archive_sha256`/`demo_hash` preenchido nos 16 arquivos `(0/0)`. Os únicos 64 hex sob `mirage_domains/` são: 33 no manifesto profissional (todos verificados no disco) e 5 no `intermediate_npz_manifest_v1.json`, que são **hashes de arquivos reais do pipeline** — recalculados por mim e conferidos `(5/5)`.
- **Splits (§19):** `intermediate_splits_proposal.json` declara `proposal_status: DESIGN_ONLY_NOT_MATERIALIZED`, `materialized: false`, `materialization_blocked_reason: LESS_THAN_50_DEMOS_AVAILABLE`, `current_demos_available` 0, `minimum_viable_demo_count` 50, `(0/50)` e `(0/6)` requisitos de materialização. Respeita a proibição de materializar splits com menos de 50 demos. `(1/1)`

---

## D) Contrato de domínios (§4) — verificação semântica

**Recontagem da spec feita por mim**, a partir do texto literal de `.agents/teamwork/ORIGINAL_REQUEST.md`:

- §4 "Campos obrigatórios:" — **linhas 1139–1157 → 17 itens**;
- §7 "Uma demo candidata deve possuir:" — **linhas 1288–1302 → 13 critérios** (a linha 1288 é cabeçalho e foi descontada);
- §7 "Excluir ou sinalizar:" — **linhas 1304–1317 → 12 critérios** (a linha 1304 é cabeçalho).

> Observação de fidelidade de instrução: o despacho menciona "16 campos obrigatórios do §4". A contagem do texto literal é **17** e o contrato declara `mandatory_fields_count: 17` com 17 entradas. O erro está na contagem do despacho, não no artefato (R7). Não repito números de tabela de terceiros; todos os valores acima foram contados por mim nas linhas citadas.

| Item | Evidência | `(N/D)` |
|---|---|---|
| Domínios `PROFESSIONAL`, `INTERMEDIATE_COMPETITIVE`, `UNKNOWN` | `contract.domains` (3 chaves) | `(3/3)` |
| Subdomínios exigidos | `contract.subdomains` = `PROFESSIONAL_HLTV`, `FACEIT_LEVEL_5_6`, `FACEIT_LEVEL_7_8`, `FACEIT_LEVEL_9_10`, `VALVE_COMPETITIVE_MAP_RANK`, `VALVE_PREMIER_RATING`, `VALVE_OPT_IN_UNKNOWN_RANK` | `(7/7)` |
| Campos do §4 | `contract.mandatory_fields` — nenhum ausente | `(17/17)` |
| Critérios de aceitação do §7 | `AC01`–`AC13` (map de_mirage, Source 2, data, patch, lifecycle, mínimo de 16 rounds com overtime, 10 jogadores, posições finitas, rounds identificáveis, CT/TR, C4/eventos, rank rastreável, fonte+licença) | `(13/13)` |
| Critérios de exclusão do §7 | `EX01`–`EX12` + `EX13` (`NOT_A_REJECTION_CRITERION`, que espelha a proibição de excluir por derrota/pontuação/estilo da linha 1319) | `(13/13)` |

**Proibição de conversão de rank — verificada semanticamente:**

- `rank_conversion_policy.automatic_conversion_prohibited: true` e `conversions_allowed: []` (lista **vazia**: nenhuma conversão é permitida).
- `prohibited_conversions` enumera explicitamente as 8 direções proibidas, incluindo `FACEIT level -> Valve Competitive map rank`, `FACEIT level -> Valve Premier rating`, `FACEIT Elo -> …`, `Valve Premier rating -> Valve Competitive map rank` e rejeição de bucketização por "semelhança visual, reputação, nome de time ou estimativa do pesquisador".
- `missing_rank_rule`: rank ausente → `null` + `exclusion_reason` + `domain_id = UNKNOWN`, "nunca preenchido por aproximação" — impede promoção de `UNKNOWN`. `domains.UNKNOWN.default_inclusion_policy: EXCLUDED_PILOT` com nota explícita "Proibido promover UNKNOWN a INTERMEDIATE_COMPETITIVE".
- `faceit_buckets`: `FACEIT_LEVEL_1_4` → `inclusion_policy: EXCLUDED_PILOT`; `FACEIT_LEVEL_9_10` → `EXCLUDED_PILOT`. `(2/2)` excluídos do piloto.
- `valve_premier_policy.inclusion_policy: NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT` com `bucket_definition: null` e 3 condições bloqueantes. `(1/1)`
- `excluded_from_primary_corpus` lista 5 buckets excluídos (incluindo `UNKNOWN_SKILL`, `FACEIT_LEVEL_1_4`, `FACEIT_LEVEL_9_10`). `(5/5)`
- `faceit_buckets.elo_usage_rule`: Elo "nunca usado para substituir o level nem para inferir level".

Enforcement corresponde ao código: `validate_skill_bucket.py --self-test` executa 14 casos incluindo `missing_mandatory_field_rejected` e `signed_url_reference_rejected`.

---

## E) Downloader (§9) — conformidade de segurança

Escopo: 11 entregáveis em `tools/intermediate_demo_acquisition/` (`README.md`, `config.example.json`, 9 `.py`). O `__pycache__` com 5 `.pyc` foi **excluído** da contagem por ser `TRANSIENT_CACHE` do interpretador (R4).

| # | Requisito §9 | Evidência (arquivo:linha) | Veredito |
|---|---|---|---|
| 1 | resumable downloads | `download_demo.py:14` (`Range: bytes=`), `.part`, `.state.json`; `resume_download.py` | PASS |
| 2 | exponential backoff | `config.example.json:41-43` (`backoff_initial_seconds`, `backoff_factor` 2.0, `backoff_max_seconds`); `discover_matches.py:204` | PASS |
| 3 | rate limiting | `RateLimiter` token bucket em `download_demo.py:167-175`; `config.example.json:35-37` | PASS |
| 4 | checksum | `hashlib` + `verify_sha256`; `build_manifest.py:18,37` | PASS |
| 5 | archive validation | magic bytes, `zipfile`/`tarfile`, `--self-test` com 8 casos (`verify_archive.py`) | PASS |
| 6 | decompressão segura (path traversal) | `verify_archive.py` + `extract_demo.py` com `Path.resolve()` e contenção em `dest_root` (`OUTSIDE_DEST_ROOT`); caso `a/../../b.dem` → `PARENT_TRAVERSAL` | PASS |
| 7 | duplicate detection por hash | `deduplicate_demo.py` (SHA-256, distingue duplicata real de colisão de nome) | PASS |
| 8 | dry-run como padrão | grupo mutuamente exclusivo `--dry-run`/`--execute` nos 9 scripts; `mode_default: "DRY_RUN"` | PASS |
| 9 | allowlist de domínio | `network.allowed_domains` obrigatório; `validate_url` (`download_demo.py:142-164`) | PASS |
| 10 | audit log | JSONL append-only; `assert_no_signed_url` + `assert_no_secret_leak` antes de gravar | PASS |
| 11 | credential redaction | `redact()` presente nos 9 scripts | PASS |
| 12 | retry limit | `retry_limit: 4` em `config.example.json:40`, aplicado em runtime | PASS |
| 13 | quarantine | `quarantine()`/`replace()`; `CHECKSUM_MISMATCH_QUARANTINED` (`download_demo.py:456`) | PASS |
| 14 | segredos só de ENV/secret store | `secret_source: "ENV"`; leitura por `os.environ`; `load_config` falha se `credentials` tiver valor | PASS |

**Total: `(14/14)`.**

**Provas funcionais executadas (sem rede, sem escrita em `tools/`):**

- Autotestes embutidos: `validate_skill_bucket` `(14/14)`, `verify_archive` `(8/8)`, `extract_demo` `(8/8)`, `deduplicate_demo` `(6/6)`, `resume_download` `(4/4)` → **`(40/40)`**, todos exit code 0.
- Barreiras de URL (`probe_downloader_functional.py`): URL https em allowlist **aceita**; `http://` **rejeitada**; IP literal **rejeitado**; `user:pass@` **rejeitado**; host fora da allowlist **rejeitado**; `X-Amz-Signature=…` **rejeitado**; allowlist vazia **rejeitada** → **`(7/7)`**.
- `--execute` **bloqueado por política**: sem `CSBOT_APPROVED_SOURCE_ID` o script emite `EXECUTE_BLOCKED_NO_APPROVED_SOURCE` e sai com código 2 (`download_demo.py:435-437`). Nenhum download real foi executado por mim.

**URL assinada jamais persistida:** nenhuma ocorrência de `X-Amz-Signature` com valor em qualquer artefato; `signed_url_persistence_allowed: false` é **imposto** por `load_config` (falha se `true`); `validate_url` recusa o parâmetro na entrada; `assert_no_signed_url` recusa no log/estado.

---

## F) Gates do §22 — por critério, sem inventar

### Gate A: Aquisição

| Critério | Veredito | Fundamentação (verificada por mim) |
|---|---|---|
| fonte legítima | **PASS** | Fontes avaliadas são documentação oficial (FACEIT developers, Steam, Valve wiki, PureSkill, Kaggle); nenhum contorno de autenticação/ToS executado; nenhuma demo baixada; allowlist de domínio impositiva; challenge anti-bot registrado como bloqueio, não resolvido |
| rank rastreável | **PASS no nível de política / N/A (0/0) no nível de dado** | `rank_system` obrigatório e explícito no contrato, conversão proibida; porém não existe demo alguma para verificar rank real |
| demo acessível | **FAIL** | `gate_a_summary`: nenhuma das 8 sub-fontes tem demo acessível aprovada `(0/8)`; nenhum arquivo `.dem` no repositório |
| licença ou autorização registrada | **FAIL** | Termos FACEIT devolveram HTTP 403 e não foram lidos; `ml_use_license_status = UNVERIFIED_REQUIRES_HUMAN_READ_OF_TERMS`; nenhuma autorização registrada |
| zero segredo persistido | **PASS** | Varredura própria: nenhum segredo real em 41 arquivos; `config.example.json` com credenciais vazias; nenhuma URL assinada |
| downloader reproduzível | **PASS** | `(14/14)` requisitos, `(40/40)` casos de autoteste, `(7/7)` barreiras, dry-run padrão, `--execute` bloqueado |

**Agregado do Gate A:** não pode ser `PASS` (2 de 6 critérios falham por ausência de autorização e de demo acessível) e não é `FAIL` definitivo (nenhuma violação legal detectada). O rótulo correto e efetivamente declarado é **`INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`**, previsto explicitamente no §22 como resultado válido e completo. **Correto.**

### Gate B: Integridade

| Critério | Veredito |
|---|---|
| DEM válido | **N/A (0/0)** — nenhum arquivo `.dem` |
| Mirage | **N/A (0/0)** — sem demo para verificar `de_mirage` |
| Source 2 | **N/A (0/0)** — sem demo; `demoparser2` **ausente** do ambiente |
| parser compatível | **N/A (0/0)** / `PENDING_TOOLCHAIN` — `importlib.util.find_spec('demoparser2')` retorna `None` |
| NPZ válido | **N/A (0/0)** — nenhum arquivo `.npz` no domínio intermediário |
| lifecycle válido | **N/A (0/0)** — sem dados de round |
| zero sintético | **N/A (0/0)** — vacuamente verdadeiro porque não existe nenhum dado; **não** é evidência de qualidade |

**Agregado do Gate B:** integralmente `N/A (0/0)`. Nenhum critério do Gate B pode ser declarado `PASS` nesta fase, e nenhum foi.

---

## G) Fidelidade do relatório de viabilidade — ressalva obrigatória

| Item verificado | Resultado |
|---|---|
| (a) o cache **não** é citado como evidência primária | **CUMPRIDO** — nenhuma ocorrência de `2a_intermediate_research_cache` nos 13 entregáveis `(0/13)` |
| (b) toda afirmação dependente dos originais marcada `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` | **NÃO CUMPRIDO** — **zero ocorrências** nos 13 entregáveis e **zero ocorrências** em `.agents/teamwork/researcher_2a_int_1/research_log.md` `(0/13)` → **R1** |
| (c) nenhuma afirmação `UNVERIFIED` promovida a `VERIFIED` | **CUMPRIDO** — Termos FACEIT seguem `HTTP 403` e `UNVERIFIED_REQUIRES_HUMAN_READ_OF_TERMS`; artigo de Elo segue bloqueado e as faixas de Elo por level foram **retratadas**; wiki da Valve registrada como bloqueio Anubis `(3/3)` |
| (d) `steam_icsgoplayers_730.txt` continua índice genérico (F12 preservada, não maquiada) | **CUMPRIDO** — contagem no arquivo em disco: `ICSGOPlayers` sem ocorrência, `IGCVersion_730` sem ocorrência, `Access Match History` sem ocorrência; o `INDEX.md` do cache rotula explicitamente "SERVE O ÍNDICE GENÉRICO … não é evidência da interface CS:GO"; o relatório declara a ausência em §5.2/§12 `(1/1)` |

**Fatos do evento de perda de evidência, reconstruídos do disco por mim:** `scratch/2a_intermediate_research_cache/INDEX.md` registra que os 7 arquivos `_tmp_*.txt` originais foram **removidos às 2026-11-09T01:08:42Z** e que a ordem para *mover* chegou 6 segundos depois; a recaptura ocorreu entre **01:09:09Z e 01:09:17Z**, com bytes e SHA-256 por arquivo em `_recapture_log.json`. O relatório de viabilidade **não menciona nada disso**.

**Agravação objetiva:** o §12 de `source_feasibility_report.md` (linha 812) afirma literalmente *"Todas as URLs abaixo foram recuperadas nesta sessão. UTC = horário da consulta."* e lista horários de **00:51Z a 00:56Z** para 25 evidências (E1–E25). Essas capturas **não existem mais**. O material que sobrevive é de 01:09Z. Portanto há afirmação apresentada como verificação daquele instante sem o rótulo obrigatório que a desqualificaria como tal.

**Atenuantes verificados por mim (não eliminam a ressalva, mas delimitam o impacto):** a recaptura **corrobora o conteúdo semântico** das afirmações. Conferi no disco as contagens de termos-chave declaradas: `demo_url` 4, `game_skill_level` 18, `Property of FACEIT` 1, `open.faceit.com/data/v4` 65 em `faceit_data_api.txt`; `/download/v2/demos/download` 1, `Downloads API scope` 1, `30 days` 2, `Match Demo Ready` 3 em `faceit_downloads_api_guide.txt` — todas idênticas às declaradas. Ou seja: **a substância é corroborável; a cadeia de custódia temporal não é.** `(8/8)` contagens conferidas.

---

## Integridade dos 95 artefatos preservados

Condição de `PASS` estabelecida pelo Sentinel. Método: li o `preserved_artifacts_inventory` **do próprio marcador** (caminho lido do JSON), recalculei cada SHA-256 com `hashlib` em modo `rb`.
Comando: `python .agents/teamwork/provenance_auditor_2a_int_1/verify_preserved_artifacts.py`

| Métrica | Declarado no marcador | Recalculado por mim | Veredito |
|---|---|---|---|
| Bytes do marcador | 37114 | **37114** | OK |
| SHA-256 do marcador | `465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad` | **`465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad`** | OK — não reemitido, não reformatado |
| Artefatos enumerados | 95 | **95 entradas, schema uniforme** (`artifact_class`, `hashed_utc`, `repo_relative_path`, `sha256`, `size_bytes`) | OK |
| SHA-256 coincidentes (e bytes) | — | **`(95/95)`** | OK |
| Total de bytes conferido | 212960002 | **212960002** | OK — exato |
| Divergências | — | **nenhuma** (nenhum arquivo ausente, nenhum hash divergente) | OK |

**Cruzamento com `.agents/teamwork/orchestrator_2a_intermediate/ARTIFACT_INVENTORY.md`** — usei **somente** os blocos `[CURRENT — VIGENTE]`; o bloco `SUPERSEDED — NÃO USAR` (linhas 135–137) foi integralmente descartado conforme instrução.
Comando: `python .agents/teamwork/provenance_auditor_2a_int_1/verify_inventory.py`

| Métrica | Declarado no bloco vigente | Recalculado | Veredito |
|---|---|---|---|
| Linhas de tabela | 57 | **57** | OK |
| Classes | 32 `DELIVERABLE` + 9 `SUPPORT` + 1 `TEST` + 10 `EVIDENCE_CACHE_RECAPTURED` + 5 `TRANSIENT_CACHE` = 57 | **32 + 9 + 1 + 10 + 5 = 57** | OK — reconciliação exata, sem resíduo |
| SHA-256 + bytes coincidentes | — | **`(57/57)`** | OK |
| Total de bytes | 3021280 | **3021280** | OK |
| Divergências | — | **nenhuma** | OK |

A pausa formal está **íntegra**: nenhum dos 95 artefatos preservados foi tocado, e o inventário de escopo fecha sem resíduo.

---

## Ressalvas numeradas com impacto

**R1 — `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` ausente dos entregáveis. IMPACTO: impede `PASS`.**
Marcação obrigatória com **zero ocorrências** em 13/13 arquivos de `training_runs/intermediate_domain_study/` e em `research_log.md`. O §12 do relatório de viabilidade apresenta 25 evidências com horários 00:51Z–00:56Z de capturas destruídas às 01:08:42Z, sem rotular a dependência. Corrigível sem refazer pesquisa: adicionar o rótulo na tabela E1–E25 e no topo do §12, apontando para `_recapture_log.json`.

**R2 — Transparência do `EVIDENCE_LOSS_EVENT` confinada a `scratch/`. IMPACTO: alto.**
O registro completo (perda, recaptura, `RECAPTURED`, hashes) existe em `scratch/2a_intermediate_research_cache/INDEX.md` e em `_recapture_log.json` — **fora** das três árvores de entregáveis do §21. Um auditor que leia apenas `training_runs/intermediate_domain_study/` não descobre o evento. O `ARTIFACT_INVENTORY.md` do Orchestrator **cobre** isso corretamente (linha 102, "Ressalva vinculante"), mas ele também vive em `.agents/teamwork/`. Recomendação: uma nota de proveniência dentro de `source_feasibility_report.md`, referenciando o índice do cache por caminho relativo.

**R3 — `pilot_download_manifest.json` sem a chave `records`. IMPACTO: médio (schema).**
Os outros 3 manifests expõem lista `records` vazia. Este usa `downloads_attempted`/`downloads_completed`/`downloads_failed`/`bytes_downloaded` + `resume_state` nulo. É "equivalente" no sentido do despacho e a contabilidade `(0/0)` está íntegra, mas a assimetria de schema impede validação uniforme por um único leitor de manifests.

**R4 — 5 `.pyc` `TRANSIENT_CACHE` ainda presentes. IMPACTO: médio (estado alvo não atingido).**
`tools/intermediate_demo_acquisition/` tem **11 entregáveis + 5 `.pyc`**. O estado alvo declarado ("exatamente 11 arquivos e nenhum `.pyc`") **não** havia sido atingido no instante desta auditoria. Os `.pyc` são cache do interpretador, não entregável nem evidência; a remoção física é o último passo e deve ser recontada depois. Não os tratei como artefato da fase.

**R5 — 7 entregáveis do §21 pendentes. IMPACTO: médio (fechamento da fase).**
Ausentes no momento da auditoria: `mathematical_audit.json`, `provenance_audit.json`, `adversarial_audit.json`, `cs2_domain_methodology_review.json`, `phase_evidence_matrix.json`, `deliverable_evidence.json`, `fase_2a_intermediate_final_report.md`. O `ARTIFACT_INVENTORY.md` (seção 7) os declara `PENDING_AUDIT`/`PENDING`. Este parecer é a origem do `provenance_audit.json`; os demais são de outros papéis e do Orchestrator. A fase **não pode** ser encerrada como completa antes disso.

**R6 — Imprecisão factual 403 vs 404 no artigo de Elo. IMPACTO: baixo.**
`source_feasibility_report.md:111` afirma que a verificação direta do artigo de Elo retornou `HTTP 403`; `_recapture_log.json` registra `404` na recaptura (o `INDEX.md` reconhece a mudança). Nenhuma das duas versões promove faixa de Elo a `VERIFIED`; a conclusão epistêmica permanece correta. Divergência de detalhe, não de conclusão.

**R7 — Contagem de campos do §4 no despacho. IMPACTO: baixo (não afeta o artefato).**
O despacho diz "16 campos obrigatórios"; a recontagem do texto literal (`ORIGINAL_REQUEST.md` linhas 1139–1157) e o contrato (`mandatory_fields_count: 17`, 17 entradas) dão **17**. O artefato está correto; a contagem do despacho é que está errada.

**R8 — Percentual de política de janelamento no manifesto profissional. IMPACTO: nenhum.**
`professional_manifest_reference.json` declara `overlap_percentage` como percentual de política de janelamento (`stride` 16 sobre `sequence_length` 32), não como métrica agregada de classe. Nenhum artefato auditado apresenta valor numérico de métrica para classe sem suporte: nesses casos o texto é explicitamente `N/A`. O formalismo proibido de percentual nulo não aparece em nenhum dos artefatos auditados, conforme confirmado por varredura textual nos 16 arquivos de `datasets/mirage_domains/`.

---

## O que NÃO pude verificar

1. **Conteúdo das páginas web no instante original (00:51Z–00:56Z).** As capturas originais não existem mais. Verifiquei o que sobreviveu (recaptura de 01:09Z) e conferi 8 contagens de termos-chave que batem com o declarado; isso corrobora a substância, **não** a simultaneidade da leitura original.
2. **Correspondência byte-a-byte dos originais vs recaptura.** Impossível: os originais foram destruídos e eram extração textual, enquanto a recaptura é HTML/JSON bruto (tamanhos diferem por marcação, como o `INDEX.md` explica).
3. **Extração DEM→NPZ end-to-end.** `demoparser2` está ausente do ambiente (`importlib.util.find_spec` retorna `None`), então o §11 é `PENDING_TOOLCHAIN`. Não tratei como falha da fase e **não** tentei instalar nada.
4. **Métricas do §12/§13/§15/§17** (padronização CT/TR, cobertura dos 53 spots, clusters não mapeados). Exigem dados intermediários que não existem; os JSONs correspondentes declaram `NOT_EXECUTABLE`. Não auditei sua semântica além de confirmar a ausência de dados e de contagens inventadas.
5. **Validade jurídica das licenças** (FACEIT, Valve, CC BY-NC-SA 4.0). Auditoria técnica de licença é `UNVERIFIED` por natureza aqui; a leitura dos termos FACEIT nem sequer foi possível (HTTP 403).
6. **Suíte C# do CsBot.** Fora do meu escopo e não executada.
7. **Conteúdo dos 444 NPZ externos.** Recontei arquivos e bytes (444 / 856.405.885, idênticos), mas não abri nenhum tensor nem recalculei hash de NPZ.
8. **Autorização humana real.** Nenhum selo `APPROVED_BY_USER` foi emitido e nenhum foi assumido; `human_seals_present: false` em todos os artefatos que o declaram.

---

## Conclusão

Os artefatos de governança e dados da FASE 2A-INTERMEDIATE são **autênticos e não fabricados**. A ausência de dados intermediários está declarada de forma contábil e verificável (`(0/0)` com numerador e denominador, `aggregation_value: null`, inventários vazios, nenhum `.dem`/`.npz`/`.parquet`, nenhum identificador ou hash de demo inventado). O corpus profissional está **byte-idêntico** em três verificações independentes e complementares (95/95 no marcador, 33/33 no manifesto, 57/57 no inventário, mais 444/444 nos NPZ externos). Não há segredo real persistido. O contrato de domínios implementa integralmente o §4/§6/§7, inclusive as três proibições críticas (conversão de rank, inclusão de FACEIT 1–4/9–10, promoção de `UNKNOWN`). O downloader cumpre os 14 requisitos do §9 com evidência funcional, não apenas textual.

O veredito é **`CONDITIONAL`** por um único bloqueio de compliance — a ausência da marcação `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` nos entregáveis (R1), agravada pelo confinamento da transparência do `EVIDENCE_LOSS_EVENT` a `scratch/` (R2) — somado a três pendências de fechamento (R4, R5) e duas assimetrias menores (R3, R6). Nenhuma dessas ressalvas exige refazer pesquisa, redownload, retreino ou reavaliação de dados: são correções documentais e de contagem.

**Condições objetivas para reclassificação a `PASS`:** (i) rótulo `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` aplicado às evidências E1–E25 em `source_feasibility_report.md`, com referência ao `_recapture_log.json`; (ii) nota de proveniência do evento de perda de evidência dentro de um entregável do §21; (iii) remoção física dos 5 `.pyc` com recontagem em 11 arquivos; (iv) materialização dos 7 entregáveis pendentes do §21.

**O veredito da fase (§22) permanece `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`** — correto e não deve ser alterado para cima. Nenhum treinamento foi iniciado, nenhuma inferência no Test foi executada, o Final Holdout não foi consultado, nenhum ONNX foi exportado e a fase não avançou automaticamente.

---

## Reprodutibilidade integral

```
python .agents/teamwork/provenance_auditor_2a_int_1/scan_secrets.py --scan --out secrets_scan_result.json
python .agents/teamwork/provenance_auditor_2a_int_1/forensic_checks.py --out checks_result.json
python .agents/teamwork/provenance_auditor_2a_int_1/inspect_accounting.py
python .agents/teamwork/provenance_auditor_2a_int_1/check_contract.py
python .agents/teamwork/provenance_auditor_2a_int_1/audit_downloader.py
python .agents/teamwork/provenance_auditor_2a_int_1/run_selftests.py
python .agents/teamwork/provenance_auditor_2a_int_1/probe_downloader_functional.py
python .agents/teamwork/provenance_auditor_2a_int_1/scan_fabrication.py
python .agents/teamwork/provenance_auditor_2a_int_1/verify_preserved_artifacts.py
python .agents/teamwork/provenance_auditor_2a_int_1/verify_inventory.py
python -m pytest tests/test_phase2a_intermediate_domain.py -q -p no:cacheprovider
```

**Natureza dos dados deste parecer:** `AGENT_REVIEWED` + `AUTOMATED_CHECK_PASS`. Nenhum selo humano (`APPROVED_BY_USER`, `HUMAN_CAPTURE_IN_GAME`) é emitido aqui; nenhum é reivindicado.
