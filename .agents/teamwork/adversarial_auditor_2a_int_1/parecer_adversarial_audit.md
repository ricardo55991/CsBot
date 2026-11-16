# PARECER ADVERSARIAL — FASE 2A-INTERMEDIATE (CsBot)

**Papel:** Adversarial Success Auditor (papel 6 de 6 do §3)
**Agente:** `adversarial_auditor_2a_int_1`
**Data UTC:** 2026-11-09T01:34Z
**Regime:** somente leitura sobre `src/`, `tools/`, `tests/`, `datasets/`, `models/`, `training_runs/`, `scratch/`
**Skills aplicadas:** `csbot-report-skeptic` (12 padrões), `csbot-phase-gate`
**Rótulos emitidos por este parecer:** `AGENT_REVIEWED`, `AUTOMATED_CHECK_PASS`. **Nenhum** selo humano foi emitido ou presumido (Regra 05).

---

## VEREDITO

# `CONDITIONAL`

A base factual da fase é **sólida e empiricamente reproduzida** (20/20 testes não-fachada, 10/10 mutações detectadas, 0 dados fabricados, Gate A corretamente `ACCESS_PENDING`, hipótese `UNPROVEN_PENDING_DATA`). **Não há PASS** porque duas violações de integridade de rotulagem de evidência foram verificadas empiricamente e a correção é obrigatória antes do fechamento (ver §6).

---

## 1. Sumário (5 linhas)

1. Recontagem própria: **20 passed / 0 skipped / 0 failed** em 20 coletados (`2 passed` do log do implementador conferido e igual; tempo difere: 0.78 s vs 0.82 s).
2. Mutation probe re-executado por mim com prova antes/depois: **10/10 PROBE_OK**, `VIOLACOES_DE_ISOLAMENTO = 0`.
3. Regressão própria: **285 passed**; baseline sem o arquivo novo **265 passed** ⇒ 265+20=285 exato; os 2 erros de coleta são **pré-existentes e comprovados documentalmente**.
4. Varredura de segredos autotestada (**10/10** fixtures positivas, **9/9** negativas) sobre 43 arquivos / 1.290.016 bytes: **0 segredos reais** (6 hits brutos classificados como fixture/nome de variável).
5. **Violações encontradas: 2** (V1 materialização de evidência 5/25; V2 promoção de fidelidade — 163 ocorrências textuais de `VERIFIED_ONLINE` com 0 de `RECAPTURED`/`REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`).

---

## 2. Tabela de ataques (comando → resultado → N/D)

| # | Ataque | Comando executado | Resultado | (N/D) |
|---|---|---|---|---|
| A1 | Recontagem própria da suíte M8 | `python -m pytest tests/test_phase2a_intermediate_domain.py -v` | `collected 20 items` → **20 passed, 0 skipped, 0 failed, 0 errors** em 0.82 s | **(20/20)** passed |
| A2 | Prova anti-fachada | `python .agents/teamwork/adversarial_auditor_2a_int_1/run_mutation_probe_audited.py` (wrapper que executa o probe do implementador com `%TEMP%` fixo e contagem antes/depois) | `sondas=10 PROBE_OK=10 falhas=0`; `PROBE_EXIT_CODE=0` | **(10/10)** PROBE_OK |
| A3 | Asserção tautológica | `python .agents/.../static_inspect_tests.py` | 1 ocorrência textual de `assert True`, **dentro de bloco de string** (docstring de cabeçalho, linha 11); 0 executável; 0 `assert False`; **221 asserts executáveis** | **(0/221)** tautologias |
| A4 | Skip silencioso | idem + `python -X utf8 -c "..."` sobre `F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage` | 1 único `pytest.skip` (L1079); diretório existe com **444 `.npz`** ⇒ não disparou (confirmado por `0 skipped` em A1) | **(0/1)** skips disparados |
| A5 | Aprovação por `0/0` | inspeção de A3 + `audit_json_artifacts.py` | zero assert do tipo "0 de 0 violaram ⇒ PASS"; contagens zero aparecem como contrato (`records == []`, `metric_status: STRICT_NA`, `aggregation_value: null`) | **(0/221)** asserts de razão sem denominador |
| A6 | Regressão | `python -m pytest tests -q --ignore=tests/test_concise.py --ignore=tests/test_concurrent_concise.py` | **285 passed, 9 warnings in 32.25 s** | **(285/285)** passed |
| A7 | Baseline real (não declarável) | idem `--ignore` + `--ignore=tests/test_phase2a_intermediate_domain.py` | **265 passed, 9 warnings in 31.71 s** | **265 + 20 = 285** ✔ |
| A8 | Pré-existência dos 2 erros de coleta | `git ls-files`, `git log --oneline -3 --`, `git status --porcelain --`, mtime, `pytest` nos 2 arquivos | ambos **rastreados** no commit `5175b38`, **sem modificação** (`git status` vazio), mtime **2026-10-24T12:05Z** (2 semanas antes da fase), erro real `urllib.error.URLError: [WinError 10061]` (servidor Ollama local ausente) | **(2/2)** pré-existentes comprovados |
| A9 | Varredura de segredos | `python .agents/.../secrets_scan.py` | autoteste **10/10** positivas + **9/9** negativas; 43 arquivos / **1.290.016 bytes**; **0 achados reais** (6 hits brutos: 3 fixtures `deadbeef*`, 2 SteamID sintéticos, 1 nome de variável de ambiente) | **(0/43)** arquivos com segredo |
| A10 | Cobertura dos 20 testes do §20 | `python .agents/.../final_checks.py` (extrai nomes do texto literal do `ORIGINAL_REQUEST.md` ¶#20) | **20 nomes extraídos da spec**, 20 em `REQUIRED_TEST_NAMES`, 20 funções definidas, **ordem idêntica**, faltando `[]`, sobrando `[]` | **(20/20)** nomes exatos |
| A11 | Gate C / Gate D | leitura de `pilot_corpus_quality.json::gate_mapping` | `Gate_C_qualidade: NOT_EVALUABLE_NO_INTERMEDIATE_DATA`; `Gate_D_valor_incremental: NOT_EVALUABLE_NO_INTERMEDIATE_DATA`; `scorecard.pass_rate: "N/A (0/0)"` | **(2/2)** não executáveis, **(0/2)** alegados como PASS |
| A12 | Vazamento de dado intermediário | `audit_misc_artifacts.py` sobre `datasets/mirage_domains/` | `.dem/.dem.gz/.rar/.npz/.parquet/.zip` encontrados em `datasets/mirage_domains/intermediate_competitive` = **[]** | **(0 arquivos)** |
| A13 | F12 preservada (ausência ≠ confirmação) | contagem no cache `steam_icsgoplayers_730.txt` (116.831 B, sha256 `017aab21…c994a68`) | `ICSGOPlayers`=0, `IGCVersion_730`=0, `icsgo`=0, `csgo`=0, `730`=0, `Access Match History`=0; relatório L484-485 diz **"não serve conteúdo da interface"** | **(0/6)** termos de interface; sem promoção indevida |
| A14 | Números sem origem (super-relatório) | `number_traceability.py` | `source_feasibility_report.md`: **0/17** números sem rastro; `domain_training_strategy.md`: 6/16 sem rastro, **todos** rotulados `INFERRED` ou são seeds de design (42026/42027/42028) | **(0/17)** e **(6/16 rotulados)** |
| A15 | Métrica intermediária numérica | `audit_json_artifacts.py` sobre 8 JSONs | caminhos com `intermediate` + chave de métrica numérica = **0**; `professional_vs_intermediate.json` tem `metrics` = **15** com `N/A (0/0)`, `comparison_status: NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` | **(0/15)** métricas numéricas |
| A16 | Selo humano | `skeptic_patterns_scan.py` sobre os 5 MD | 1 única menção literal (`APPROVED_BY_USER`, L773 de `source_feasibility_report.md`), em contexto de **passo futuro a ser executado pelo humano**; nenhuma alegação de aprovação concedida; `scale_up_recommendation.md` usa só `AGENT_REVIEWED`/`AUTOMATED_CHECK_PASS` | **(0/5)** relatórios com selo humano |
| A17 | Hipótese confirmada | idem | `hypothesis_status: UNPROVEN_PENDING_DATA`, `confirmed: false`, `refuted: false`; 0 ocorrências de "hipótese confirmada"/`HYPOTHESIS_CONFIRMED`/`READY_TO_SCALE` nos 5 MD | **(0/5)** alegações de confirmação |
| A18 | Materialização de evidência | `evidence_materialization.py` | §12 cita **25** URLs; **5/25** têm captura bruta; **20/25** não têm; **0/25** têm captura no UTC declarado | **(5/25)** materializadas |
| A19 | Fidelidade pós-`EVIDENCE_LOSS` | `label_counts.py` + varredura de 360 arquivos | `VERIFIED_ONLINE` textual: 81 (MD principal) + 6 (valve_opt_in) + 36 (matrix) + 40 (faceit_readiness) = **163**; `RECAPTURED`/`FIDELITY`/`REPORT_TO_SOURCE`/`EVIDENCE_LOSS` = **0** em **todos** os entregáveis | **(0/163)** rótulos corrigidos |
| A20 | `demoparser2` / toolchain | `importlib.util.find_spec('demoparser2')` | `None` ⇒ **AUSENTE**; `demoparser`/`awpy` ausentes; `pandas`/`numpy`/`torch` presentes | **`PENDING_TOOLCHAIN`** confirmado |
| A21 | Cache recapturado (tamanho declarado) | soma dos 10 arquivos de `scratch/2a_intermediate_research_cache/` | **1.590.118 B** — idêntico ao declarado em `GATE_STATUS.md` L35 | **(1.590.118/1.590.118)** ✔ |

---

## 3. Contagem pytest própria + log bruto

**Comando:** `python -m pytest tests/test_phase2a_intermediate_domain.py -v`
**Contagem própria:** `collected 20 items` → **`20 passed in 0.82s`** — **20 passed / 0 skipped / 0 failed / 0 errors**.
**Log bruto:** `.agents/teamwork/adversarial_auditor_2a_int_1/pytest_own_output.txt`

Comparação com o log do implementador (`.agents/teamwork/implementer_data_2a_int_1/pytest_m8_literal_output.txt`, 4614 B):
- Mesma contagem (20 passed, 0 skipped) e mesma lista/ordem de testes ⇒ **convergente**;
- Tempo diverge (0.78 s vs 0.82 s) — esperado, carga de máquina. **Não tratei o log dele como verificação**: a contagem acima é minha.

Regressão completa:
- `python -m pytest tests -q --ignore=tests/test_concise.py --ignore=tests/test_concurrent_concise.py` → **285 passed, 9 warnings in 32.25 s** → log: `full_regression_own_output.txt`
- Mesmo comando acrescido de `--ignore=tests/test_phase2a_intermediate_domain.py` → **265 passed, 9 warnings in 31.71 s**
- **Fórmula (N/D): `265 + 20 = 285` — (285/285) passed, 0 failed.**

---

## 4. `mutation_probe`: **10/10**

**Comando exato executado (com prefixo de cache fora do repositório):**

```powershell
cd c:/Users/ricar/OneDrive/Documentos/Dev/CsBot
$env:PYTHONPYCACHEPREFIX="C:\Users\ricar\AppData\Local\Temp\csbot_2a_int_pycache"
python .agents/teamwork/adversarial_auditor_2a_int_1/run_mutation_probe_audited.py
```

**Caminho concreto de `%TEMP%` usado:** `C:\Users\ricar\AppData\Local\Temp\csbot_2a_int_mutation_probe\` (fixado em `tempfile.tempdir`). As 10 cópias temporárias criadas foram:

```
csbot_probe_gg6iokum, csbot_probe_j1nvio8y, csbot_probe_7tfruu6r, csbot_probe_9sb8knh5,
csbot_probe_ykqstxx5, csbot_probe_wit_9dox, csbot_probe_fyxa83gb, csbot_probe_z30l5bum,
csbot_probe_lkg1h_ha, csbot_probe_60hkywhe
```
Todas sob `C:\Users\ricar\AppData\Local\Temp\csbot_2a_int_mutation_probe\`; todas com `existe_apos_limpeza=False` (removidas pelo próprio probe).

**Prova de não-contaminação (antes → depois, contagem de arquivos):**

| Diretório | Antes | Depois | Δ | `.pyc` antes → depois | Adicionados | Removidos |
|---|---|---|---|---|---|---|
| `datasets/` | 192 | 192 | **+0** | 0 → 0 | `[]` | `[]` |
| `tools/` | 235 | 235 | **+0** | 34 → 34 | `[]` | `[]` |
| `training_runs/` | 212 | 212 | **+0** | 0 → 0 | `[]` | `[]` |
| `tests/` | 413 | 413 | **+0** | 25 → 25 | `[]` | `[]` |
| `src/` | 147 | 147 | **+0** | 1 → 1 | `[]` | `[]` |

`VIOLACOES_DE_ISOLAMENTO = 0`. **Declaração separada de `__pycache__`:** em `tools/intermediate_demo_acquisition/__pycache__/` existiam **5** `.pyc` (142.079 B) antes e **5** depois (34 `.pyc` no total de `tools/`, inalterado) — a importação **não** recriou nada porque usei `PYTHONPYCACHEPREFIX` em `%TEMP%`. Nenhum `.pyc` foi removido por mim.

**Confirmação de que as violações foram aplicadas só em cópias temporárias:** inspeção de código do `mutation_probe.py` (linhas 36-193) antes de rodar — toda adulteração é escrita via `_write(tmp / ...)` dentro de `tempfile.TemporaryDirectory(...)`; os alvos do repositório só são **lidos** (`read_text`) e as referências são restauradas em `finally` (linhas 59-61). Nenhum `open(..., 'w')` aponta para o repositório.

**As 10 violações testadas e o resultado de cada uma:**

| # | Violação injetada | Teste exigido a falhar | Resultado |
|---|---|---|---|
| 1 | Hash de referência profissional trocado por `"0"*64` | `ProfessionalCorpusRemainsUnchanged` | **PROBE_OK** (falhou: "hash divergente em datasets/mirage_v2/canonical_temporal_splits_v1.json") |
| 2 | `.dem` plantado no diretório intermediário (ou `INTERMEDIATE_DIR` redirecionado) | `IntermediateCorpusUsesSeparateDirectory` | **PROBE_OK** (falhou: "artefato fora do diretório do domínio") |
| 3 | `signed_urls_persisted = 1` no manifesto do piloto | `SignedUrlsAreNotPersisted` | **PROBE_OK** (AssertionError) |
| 4 | `demo_id` intermediário = `test_demos[0]` profissional | `ProfessionalAndIntermediateMetricsRemainSeparate` | **PROBE_OK** (falhou: "demo_id compartilhado entre domínios") |
| 5 | `bootstrap_units.primary = "window"` | `BootstrapUsesMatchOrRoundUnit` | **PROBE_OK** (AssertionError) |
| 6 | `governance_notes.training_started = true` | `NoTrainingStartsInThisPhase` | **PROBE_OK** (AssertionError) |
| 7 | Salto temporal dentro do round (`round_time_norm = 0.999`) | `RoundLifecycleIsValid` | **PROBE_OK** (AssertionError) |
| 8 | Detector de histórico sintético cego | `IntermediateNpZContainsNoSyntheticHistory` | **PROBE_OK** (AssertionError) |
| 9 | Pseudonimização identidade (SteamID64 em claro) | `SteamIdsArePseudonymizedInReports` | **PROBE_OK** (AssertionError) |
| 10 | Política de promoção de spot permissiva | `SpotPromotionRequiresHumanReview` | **PROBE_OK** (AssertionError) |

**`X/10 = 10/10`** ⇒ **M8 não reprovado** por este critério. Log bruto: `mutation_probe_audited_output.txt`.

**Ressalva metodológica (não invalida o 10/10):** as sondas 7-10 monkey-patcham **helpers locais do módulo de teste** (`_validate_round_lifecycle`, `_detect_synthetic_history`, `_pseudonymize`, `_spot_promotion_allowed`), declarados no próprio docstring da suíte como validadores locais (o repositório não expõe funções equivalentes). Logo, elas provam que **as asserções do teste reagem** à regra violada — não que exista um componente de produção sob teste. Das 10, as sondas 1-6 adulteram **artefatos/JSON reais** (mais fortes que 7-10). As sondas 1-6 usam cópias temporárias de JSON reais do repositório (mesmo conteúdo, path trocado), o que é legítimo sob bloqueio de escrita.

---

## 5. Inspeção própria: `assert True`, skip e `0/0`

**Arquivo:** `tests/test_phase2a_intermediate_domain.py` — 65.216 B, 1.327 linhas, SHA-256 `c3fbf0dc7f3f2c23072c37c57c0aeef61ec81380ddc0b53ee5cea054960691fd` (recalculado por mim, confere com o alegado).

**(a) Zero asserção tautológica — CONFIRMADO.** Existe **1** ocorrência textual de `assert True` (L11) e ela está **dentro de um bloco de string** (docstring de cabeçalho, identificado por `tokenize`): `"Nenhum teste usa ``assert True``."`. Fora de strings: **0**. Também **0** ocorrências de `assert False`. Total de `assert` executáveis: **221** → **`(0/221)` tautológicas**.

**(b) O único `pytest.skip` não dispara — CONFIRMADO.** Há exatamente **1** chamada (L1079-1082), condicional a `not npz_files` com `npz_dir = Path("F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage")`. Verifiquei de forma independente: `dir exists: True`, `npz count: 444`. Minha execução registrou **0 skipped**. O docstring do teste é honesto ao dizer que, se disparar, restam asserções de contrato e de fixture já executadas antes (L1048-1073).

**(c) Nenhum teste aprova por `0/0` — CONFIRMADO.** Os testes que lidam com ausência de dados usam **asserção de contrato sobre o valor**, não razão vazia: `npz_manifest["records"] == []`, `npz_count == 0`, `status == "EMPTY_PENDING_ACQUISITION_ACCESS"`, `dem_vs_npz_comparison["executed"] is False`, `training_started is False`, `quarantine_manifest["status"] == "EMPTY_NO_CANDIDATES"`, `proposal_status == "DESIGN_ONLY_NOT_MATERIALIZED"`. Nos JSONs, todo zero aparece em bloco `numerator/denominator = 0/0` com `aggregation_value: null` e `aggregation_status: N/A_ZERO_DENOMINATOR` (ou `metric_status: STRICT_NA`). Varredura automática de asserts com divisão por contador: **0** ocorrências. → **`(0/221)` aprovações por razão vazia**.

**(d) Cobertura dos 20 nomes do §20 — CONFIRMADO `(20/20)`.** Extraí os nomes do texto literal de `.agents/teamwork/ORIGINAL_REQUEST.md`, seção `# 20. TESTES OBRIGATÓRIOS` (linhas 1762-1785): 20 nomes. A suíte declara `REQUIRED_TEST_NAMES` com os mesmos 20, na mesma ordem (`ORDEM idêntica: True`), define 20 funções com o nome canônico e as expõe ao pytest por alias `test_<Nome>` (L1318-1327), com `assert len(_EXACT_NAMED_TESTS) == 20` em tempo de coleta. **Nenhum teste é fachada** no sentido de corpo vazio: 221 asserts executáveis, 6 testes exercitam módulos reais de `tools/intermediate_demo_acquisition/` (`validate_skill_bucket`, `build_manifest`, `deduplicate_demo`, `verify_archive`, `download_demo`), 1 lê **444 NPZ reais** do corpus profissional e 1 recalcula **33 hashes** profissionais.

---

## 6. Violações encontradas

### V1 — `HIGH` — 20 de 25 evidências citadas não têm artefato bruto materializado em disco

- **Arquivo/campo:** `training_runs/intermediate_domain_study/source_feasibility_report.md`, **L812** —
  > "Todas as URLs abaixo foram recuperadas nesta sessão. UTC = horário da consulta."
  
  seguido da tabela **L814-840** (E1–E25) e da definição em **L103** (`VERIFIED_ONLINE` = "A página foi recuperada nesta sessão e o texto citado foi lido do conteúdo recuperado").
- **Evidência empírica** (`evidence_materialization.py`): das **25** URLs da §12, apenas **5** têm captura bruta em disco — **`(5/25)`**: E5→`faceit_downloads_api_guide.txt`, E9→`faceit_data_api.txt`, E16→`steam_ssa.txt`, E21→`pureskill_cs2_spec.txt`, E22→`pureskill_csgo_spec.txt`. **`(20/25)`** não têm captura alguma (E1, E2, E3, E4, E6, E7, E8, E10, E11, E12, E13, E14, E15, E17, E18, E19, E20, E23, E24, E25).
- **Prova adicional por busca textual:** a citação literal mais forte da E15 — `"Last updated July 2010"` — **não existe em nenhum arquivo de texto do repositório** (0 hits em 436 arquivos de `.agents/`, `scratch/`, `artifacts/`). A citação da E17 — `"largely deprecated"` — existe apenas em anotações do próprio agente (`research_log.md`, `handoff.md`), não em captura bruta.
- **Números dependentes de fontes sem captura:** `~1.300 partidas`, `9.651 partidas` e `3.624.699.821 bytes` (E20/E23/E24, Kaggle) aparecem **exclusivamente no relatório** — os endpoints Kaggle não têm captura em disco. (O número `51.498.527.411` reaparece em `acquisition_source_matrix.json`, mas esse JSON é derivado da mesma sessão, não é captura bruta — circularidade.)
- **Atenuante verificada (honestidade):** as 25 URLs têm **linha correspondente** em `.agents/teamwork/researcher_2a_int_1/research_log.md` (registro de agente com URL + UTC + resumo) ⇒ rastreabilidade `(25/25)` a um log, mas apenas `(5/25)` a um artefato bruto, como exige a Regra 01.
- **Consequência normativa:** `AGENTS.md` Regra 01 exige artefato bruto materializado + caminho + hash. Não é uma alegação de `PASS` (o veredito da fase é de pendência), mas as 20 afirmações rotuladas `VERIFIED_ONLINE` não têm o lastro que o rótulo promete.

### V2 — `HIGH` — Promoção de fidelidade: 163 ocorrências de `VERIFIED_ONLINE` sem `RECAPTURED`/`REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`

- **Regra violada (registrada e vinculante):** `.agents/teamwork/orchestrator_2a_intermediate/GATE_STATUS.md` **L40** —
  > "`REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`: toda afirmação de `source_feasibility_report.md` dependente dos `_tmp_*` originais fica com fidelidade **não demonstrável**; **nenhuma pode ser promovida a `VERIFIED_ONLINE`**."
  
  e **L41** ("o cache é sempre rotulado `RECAPTURED` … nunca evidência primária").
- **Fato de base (verificado por mim, não por relato):** `scratch/2a_intermediate_research_cache/INDEX.md` L17-30 documenta `EVIDENCE_LOSS_EVENT`: os 7 `_tmp_*` originais foram removidos em **01:08:42Z** (`Remove-Item -Force`), a ordem de preservação chegou **6 s depois**, e as páginas foram **recapturadas** em **01:09:09–01:09:17Z** (confirmado por `_recapture_log.json`, 8 registros, hashes conferidos).
- **Evidência da violação** (`label_counts.py`): ocorrências textuais de `VERIFIED_ONLINE` nos **entregáveis** = **81** (`source_feasibility_report.md`) + **6** (`valve_opt_in_feasibility.md`) + **36** (`acquisition_source_matrix.json`) + **40** (`faceit_access_readiness.json`) = **163**. Ocorrências de `RECAPTURED`, `FIDELITY`, `REPORT_TO_SOURCE` ou `EVIDENCE_LOSS` nesses mesmos arquivos = **0** (`(0/163)`).
- **Varredura de 360 arquivos** (`.agents/teamwork/`, `training_runs/intermediate_domain_study/`, `datasets/mirage_domains/`, `scratch/`): a palavra `RECAPTURED` aparece em **6** arquivos — todos em `.agents/teamwork/` (`orchestrator_2a_intermediate/{ARTIFACT_INVENTORY,GATE_STATUS,progress}.md`, `provenance_auditor_2a_int_1/inventory_crosscheck.json`, `researcher_2a_int_1/progress.md`) ou em `scratch/…/INDEX.md`. **Nenhum entregável** de `training_runs/` ou `datasets/` a registra. O `handoff.md` do próprio pesquisador também **não** a registra.
- **Incoerência temporal específica:** as capturas sobreviventes são todas de **01:09:09–01:09:17Z**, mas a §12 declara UTCs de **00:51–00:56Z**. Verificação par a par (`evidence_materialization.py`): E5 `declarado=00:52Z / captura=01:09:11Z`; E9 `00:52Z / 01:09:09Z`; E16 `00:53Z / 01:09:14Z`; E21 `00:55Z / 01:09:12Z`; E22 `00:55Z / 01:09:13Z` — **`(0/5)`** capturas no instante declarado. Ou seja: mesmo as 5 evidências materializadas **não** provam que o texto citado foi lido naquele instante.
- **Auto-incoerência do índice:** `INDEX.md` L7-8 afirma que o diretório "preserva as capturas brutas … que sustentam **cada** afirmação `VERIFIED_ONLINE`" — mas há 8 capturas para 163 rótulos / 25 URLs. A frase é hiperbólica e não sobrevive à contagem.

### Observações de severidade menor (não bloqueiam isoladamente)

| # | Item | Arquivo/campo | Evidência |
|---|---|---|---|
| m1 | Vocabulário de status divergente para o mesmo estado | `pilot_corpus_quality.json::gate_mapping.Gate_C/D.status` = `NOT_EVALUABLE_NO_INTERMEDIATE_DATA`; `intermediate_npz_manifest_v1.json` = `NOT_EXECUTED_NO_INTERMEDIATE_DATA`; demais = `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` | contagem própria em 9 JSONs (`status_vocabulary.py`): `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` **990**, `NOT_EXECUTED_NO_INTERMEDIATE_DATA` **21**, `NOT_EVALUABLE_NO_INTERMEDIATE_DATA` **2**, `NOT_EXECUTED` **3**, `NOT_EXECUTED_FOR_WRITING` **1** — três variantes do mesmo conceito, todas semanticamente corretas, mas não canônicas entre si |
| m2 | Menção literal de selo humano | `source_feasibility_report.md` **L773**: "não é selo de revisão humana automática — é o `APPROVED_BY_USER` real sobre a política" | **não** é emissão de selo: descreve passo futuro do humano. Não viola a Regra 05 |
| m3 | 3 URLs citadas no corpo fora da §12 | `source_feasibility_report.md` (corpo): `https://demos.faceit.com/csgo/<arquivo>.dem.gz`, `https://open.faceit.com/data/v4`, `https://open.faceit.com/data/v4/matches/{match_id}` | padrões de endpoint/placeholder documentados na E9; não são fontes independentes sem lastro |
| m4 | 6 números sem rastro externo em `domain_training_strategy.md` | L142-144 (`7.683`, `1.536.600`, `384.150`), L393 (seeds `42026/42027/42028`) | **rotulados**: os três primeiros com `INFERRED` explícito e derivação aritmética verificada (`3.411.434/444 = 7.683`; `7.683×200 = 1.536.600`; `7.683×50 = 384.150`); as seeds são escolha de design. `3.411.434` **é** rastreável a `datasets/mirage_v2/positioning_v2_full_temporal/dataset_manifest.json` |

---

## 7. Gate C e Gate D (§22)

| Gate | Requisitos (§22) | Status verificado | Veredito |
|---|---|---|---|
| **Gate C — Qualidade** | diversidade suficiente; recorrência espacial mensurável; setups padrão detectáveis; spots relevantes; ausência de concentração extrema em poucos jogadores | `pilot_corpus_quality.json::gate_mapping.Gate_C_qualidade.status = NOT_EVALUABLE_NO_INTERMEDIATE_DATA`; `hypothesis_scorecard.pass_rate = "N/A (0/0)"`; `criteria_passed=0`, `criteria_not_executable=8` | **`NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` / `N/A (0/0)`** — correto |
| **Gate D — Valor incremental** | cobertura adicional dos 53 spots; novo comportamento padrão útil; melhor generalização para matchmaking | `gate_mapping.Gate_D_valor_incremental.status = NOT_EVALUABLE_NO_INTERMEDIATE_DATA`; nota explícita: "Nenhum dos três é verificável sem dado; nenhum é considerado satisfeito por analogia" | **`NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` / `N/A (0/0)`** — correto |

**Nenhum artefato alega que Gate C ou D passaram** (`READY_TO_SCALE`: 0 ocorrências; `INTERMEDIATE_CORPUS_READY_TO_SCALE`: 0 ocorrências). Gate A está corretamente em `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING` com contabilidade conferida por mim: `8` sub-fontes × `6` critérios = `48` avaliações, **`0/8`** sub-fontes com 6/6 — e a tabela do relatório (L63-70: 3/6, 3/6, 0/6, 4/6, 5/6, 4/6, 4/6, 4/6) **bate** com `gate_a_summary.per_sub_source_counts` do JSON (sem contradição entre artefatos). Gate B é `PENDING` por ausência de DEM (correto: não há demo alguma).

---

## 8. Isolamento de papel (Regra 09)

- Operei como **leitor** sobre `datasets/`, `tools/`, `tests/`, `src/` e `training_runs/positioning_v2_real_temporal/` — **nenhuma escrita** nesses caminhos. Verificação objetiva: minha execução do probe mediu as contagens de arquivos antes/depois com **Δ = +0** em `datasets/` (192), `tools/` (235), `training_runs/` (212), `tests/` (413) e `src/` (147); `git status --porcelain` filtrado por `test_phase2a|mirage_domains|intermediate_domain_study` não mostrou nenhum artefato novo além do arquivo de teste já existente (`?? tests/test_phase2a_intermediate_domain.py`, pré-existente ao meu turno).
- **Onde escrevi:** **somente** `.agents/teamwork/adversarial_auditor_2a_int_1/` (parecer, handoff, BRIEFING/DISPATCH/progress, 9 scripts de verificação e 8 logs brutos) e `%TEMP%` (`C:\Users\ricar\AppData\Local\Temp\csbot_2a_int_mutation_probe\` e `…\csbot_2a_int_pycache\`).
- **Não corrigi nenhuma falha** encontrada (Regra 09): V1/V2 seguem intocadas e são devolvidas ao Orchestrator.
- **Não emiti selo humano** (Regra 05).
- **Não instalei pacotes**, não baixei demos, não toquei C#, não treinei, não avaliei no Test, não consultei o Final Holdout, não exportei ONNX.
- **Declaração literal:** `write_scope: OWN_AGENT_DIRECTORY_ONLY`

---

## 9. Afirmações que NÃO consegui refutar

1. `20 passed / 0 skipped / 0 failed` — reproduzido por mim, com prova de que o único skip é inalcançável nesta máquina (444 `.npz` em F:).
2. Ausência de fachada nos testes — 10/10 mutações detectadas + 221 asserts executáveis + uso de 5 módulos reais de `tools/`.
3. `265 → 285` sem regressão — confirmado pela execução com e sem o arquivo novo.
4. Pré-existência dos 2 erros de coleta — `git` (rastreados, sem modificação) + mtime 2026-10-24 + erro de rede `WinError 10061` (Ollama local ausente). Não há como serem causados pela fase.
5. Corpus intermediário fisicamente vazio — varredura própria: `0` arquivos `.dem/.npz/.parquet/.zip` em `datasets/mirage_domains/`.
6. Zero segredo persistido — varredura autotestada (10/10 + 9/9) sobre 43 arquivos, 1.290.016 bytes, **0** achados reais; `signed_urls_persisted: 0`, `secrets_persisted: 0`.
7. F12 preservada — contagem própria: `ICSGOPlayers`/`IGCVersion_730`/`icsgo`/`csgo`/`730` = 0 no arquivo de 116.831 B; o relatório diz explicitamente que a página **não** serve a interface. A ausência de prova **não** foi convertida em confirmação.
8. Nenhuma métrica intermediária numérica — 0 em 8 JSONs; 15 métricas de `professional_vs_intermediate.json` todas `N/A (0/0)`.
9. Zero suporte → `N/A` — `spot_domain_coverage.json`: 27 `PROFESSIONAL_CONFIRMED` + 26 `INSUFFICIENT_SUPPORT` = **53/53**; categorias que exigiriam dado intermediário estão em `categories_forbidden_this_phase` e **não** foram atribuídas; `support` zero sempre com `metric_status: STRICT_NA` + `numerator/denominator = 0/0` + `reason_code`.
10. Nenhuma aprovação humana falsa e nenhuma alegação de "hipótese confirmada" (`UNPROVEN_PENDING_DATA`, `confirmed: false`).
11. Integridade do corpus profissional — 33 referências com hash/tamanho conferidos na suíte; e o hash do marcador de pausa/dos splits foi recalculado nos testes (`professional_manifest_reference.json`).
12. `demoparser2` ausente — `find_spec` → `None`; `PENDING_TOOLCHAIN` é o rótulo correto, e nenhum agente instalou pacote.
13. Cache recapturado = 1.590.118 B em 10 arquivos — soma própria confirmada.
14. Arimética de Gate A: 8 × 6 = 48 avaliações; `0/8`; contagens por sub-fonte do relatório = do JSON.

---

## 10. O que NÃO pude verificar

1. **Fidelidade relatório↔fonte original** (`REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`): os 7 `_tmp_*` foram apagados às 01:08:42Z; nenhum agente pode demonstrar que o texto citado é o que foi lido às 00:51–00:56Z. Minha verificação das 5 capturas só alcança o conteúdo de **01:09**.
2. **Conteúdo das 20 URLs sem captura** (E1-E4, E6-E8, E10-E15, E17-E20, E23-E25): exigiria rede; está fora do meu mandato (proibido baixar/rede) e não tentei "confirmar por leitura de memória".
3. **Conversas de terceiros / decisões humanas**: não verifiquei se houve aprovação humana real em outros canais — apenas confirmei que **nenhum artefato da fase a alega**.
4. **`tools/intermediate_demo_acquisition/extract_demo.py` end-to-end (DEM→NPZ)**: `PENDING_TOOLCHAIN` por ausência de `demoparser2` — não executável por construção. Não testei extração real.
5. **Downloader em modo real** (`--execute`): permanece `dry_run`; nenhuma requisição de rede foi feita por mim. Não validei comportamento contra a API viva do FACEIT.
6. **SHA-256 dos 5 `.pyc`** de `__pycache__`: não os tratei como evidência (são `TRANSIENT_CACHE`) e não os removi.
7. **Equivalência byte-a-byte das cópias temporárias do probe**: verifiquei por código que as escritas vão para `%TEMP%`, não que o conteúdo seja idêntico ao de origem — o resultado `PROBE_OK` em 1, 2, 4 (que dependem de conteúdo real) sugere que sejam.
8. Não reexecutei os testes **xUnit C#** (`tests/CsBotManager.Tests`) — fora do escopo desta fase Python e proibido tocar C#; o §20 exige manter a suíte C# verde, o que não foi medido por mim. **`CSHARP_SUITE_UNVERIFIED_BY_THIS_AUDITOR`**.

---

## 11. Condições de bloqueio para conversão em `PASS`

1. **V2 (obrigatório):** inserir nos 4 entregáveis afetados (`source_feasibility_report.md`, `valve_opt_in_feasibility.md`, `acquisition_source_matrix.json`, `faceit_access_readiness.json`) a divulgação do `EVIDENCE_LOSS_EVENT` e reclassificar cada afirmação dependente dos `_tmp_*` como `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` (ou rótulo equivalente que **não** seja `VERIFIED_ONLINE`), com o caminho + SHA-256 da captura **`RECAPTURED`** ao lado.
2. **V1 (obrigatório):** para as `20/25` URLs sem captura, ou (a) materializar captura bruta com hash, ou (b) rebaixar o rótulo para `UNVERIFIED_NO_MATERIALIZED_CAPTURE` e ajustar a frase do L812 ("Todas as URLs abaixo foram recuperadas nesta sessão"), que hoje é falsa quanto a lastro material.
3. **m1 (recomendado):** unificar o vocabulário de status (`NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`) entre `pilot_corpus_quality.json` e os demais artefatos.
4. **`INDEX.md` L7-8 (recomendado):** corrigir a afirmação de que o cache sustenta "cada" `VERIFIED_ONLINE` (são 8 capturas para 25 URLs citadas).

Nada aqui exige novo dado, novo treino ou alteração de código: são correções de rotulagem em artefatos de documentação.

---

## 12. Hashes e artefatos deste parecer

Ver `handoff.md` (§Verificação) para a lista completa com SHA-256 dos logs e scripts, e o SHA-256 deste parecer.
