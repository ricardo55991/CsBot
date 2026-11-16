# handoff.md — Adversarial Success Auditor — FASE 2A-INTERMEDIATE

**Agente:** `adversarial_auditor_2a_int_1` (papel 6 do §3)
**Data UTC:** 2026-11-09T01:35Z
**Tipo:** HARD
**Veredito:** **`CONDITIONAL`**
**Parecer:** `parecer_adversarial_audit.md` — **31.490 B** — SHA-256 `12b9f16f88129b3bc1768934ae66e42f50ff4e8d1e35e118f61781567229cad7`
**Rótulos deste parecer:** `AGENT_REVIEWED`, `AUTOMATED_CHECK_PASS`. Nenhum selo humano emitido/presumido.
**`write_scope: OWN_AGENT_DIRECTORY_ONLY`**

---

## 1. Observation

### 1.1 Contagem pytest própria (re-execução, não leitura de log)

Comando: `python -m pytest tests/test_phase2a_intermediate_domain.py -v` (cwd = raiz do repo).
Saída literal (fim):
```
collecting ... collected 20 items
tests/test_phase2a_intermediate_domain.py::test_ProfessionalCorpusRemainsUnchanged PASSED [  5%]
... (20 PASSED)
============================= 20 passed in 0.82s ==============================
```
**Contagem própria: `20 passed` / `0 skipped` / `0 failed` / `0 errors` de 20 coletados.**
Log bruto: `pytest_own_output.txt` (4.614 B). O log do implementador alega `20 passed in 0.78s` — **mesma contagem/ordem, tempo diferente (carga)**, convergente. Não tratei o log dele como verificação.

### 1.2 Regressão própria + baseline real

```
python -m pytest tests -q --ignore=tests/test_concise.py --ignore=tests/test_concurrent_concise.py
→ 285 passed, 9 warnings in 32.25s                      (log: full_regression_own_output.txt)

python -m pytest tests -q --ignore=tests/test_concise.py \
    --ignore=tests/test_concurrent_concise.py --ignore=tests/test_phase2a_intermediate_domain.py
→ 265 passed, 9 warnings in 31.71s
```
**265 + 20 = 285** — nenhuma regressão.

### 1.3 Prova documental de pré-existência dos 2 erros de coleta

```
git ls-files tests/test_concise.py tests/test_concurrent_concise.py
  → tests/test_concise.py
  → tests/test_concurrent_concise.py          (AMBOS RASTREADOS)

git log --oneline -3 -- tests/test_concise.py tests/test_concurrent_concise.py
  → 5175b38 feat(v4.2.8): ...                 (commit ANTERIOR a esta fase; HEAD = d66c214)

git status --porcelain -- tests/test_concise.py tests/test_concurrent_concise.py
  → (vazio: nenhuma modificação)

mtime: tests/test_concise.py            2026-10-24T12:05:07Z  (1.561 B)
       tests/test_concurrent_concise.py 2026-10-24T12:05:38Z  (2.162 B)
       tests/test_phase2a_intermediate_domain.py 2026-11-08T22:18:46Z (65.216 B)
```
Reprodução do erro: `python -m pytest tests/test_concise.py tests/test_concurrent_concise.py -q` →
`urllib.error.URLError: <urlopen error [WinError 10061] ...>` em **coleta** (os módulos fazem HTTP a um Ollama local no import).
**Conclusão: `PREEXISTENCE_PROVEN` (2/2)** — arquivos rastreados, não modificados, com mtime 15 dias anterior à fase e falha por dependência de serviço local.

### 1.4 Inspeção própria do arquivo de teste

`tests/test_phase2a_intermediate_domain.py` — 65.216 B / 1.327 linhas / SHA-256 `c3fbf0dc7f3f2c23072c37c57c0aeef61ec81380ddc0b53ee5cea054960691fd` (recalculado).
- `assert True`: **1 ocorrência textual (L11) DENTRO de bloco de string** (docstring); **0** executável; `assert False`: 0; asserts executáveis: **221** → **(0/221)**.
- `pytest.skip`: **1** (L1079), condicionado a `F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage`; verifiquei `dir exists: True`, `npz count: 444` ⇒ **não dispara**. Minha execução: 0 skipped.
- `0/0` como aprovação: **0/221** — zeros aparecem como contrato (`records == []`, `metric_status: STRICT_NA`, `aggregation_value: null`).
- Nomes do §20: extraí do texto literal do `ORIGINAL_REQUEST.md` (L1762-1785) → **20 nomes, ordem idêntica** aos `REQUIRED_TEST_NAMES` (L76-97); 20 funções definidas; alias `test_<Nome>` (L1318-1327); `assert len(_EXACT_NAMED_TESTS) == 20` na coleta.

### 1.5 Mutation probe re-executado com prova de isolamento

```
$env:PYTHONPYCACHEPREFIX="C:\Users\ricar\AppData\Local\Temp\csbot_2a_int_pycache"
python .agents/teamwork/adversarial_auditor_2a_int_1/run_mutation_probe_audited.py
→ sondas=10  PROBE_OK=10  falhas=0   (PROBE_EXIT_CODE=0)
```
TEMP concreto: `C:\Users\ricar\AppData\Local\Temp\csbot_2a_int_mutation_probe\` (10 subdirs `csbot_probe_*`, todos removidos: `existe_apos_limpeza=False`).

Contagem antes → depois: `datasets/` 192→192; `tools/` 235→235 (`.pyc` 34→34); `training_runs/` 212→212; `tests/` 413→413; `src/` 147→147. **Δ = +0 em todos; `VIOLACOES_DE_ISOLAMENTO = 0`.**
`__pycache__` de `tools/intermediate_demo_acquisition/`: **5 `.pyc` antes e 5 depois** (não recriados, graças a `PYTHONPYCACHEPREFIX`); não removi nenhum, não os citei como evidência.
Inspeção prévia do código (L36-193): toda adulteração é `_write(tmp / ...)` em `TemporaryDirectory`; o repositório só é **lido**.

### 1.6 Varredura de segredos autotestada

`python .agents/teamwork/adversarial_auditor_2a_int_1/secrets_scan.py`
Autoteste: **10/10** fixtures positivas dispararam; **9/9** negativas sem falso-positivo.
Varredura: **43 arquivos / 1.290.016 bytes** (`datasets/mirage_domains/**`, `training_runs/intermediate_domain_study/*`, `tools/intermediate_demo_acquisition/*`, marcador de pausa, suíte de testes, `_recapture_log.json`) → **0 segredos reais**. Hits brutos = 6, todos classificados: 2× `"requires_secret": "faceit_data_api_key"` (nome de variável), 3× `X-Amz-Signature=deadbeef*` (fixture de teste), 2× SteamID64 sintéticos `7656119800000000x` (fixture).

### 1.7 Evidência: materialização e fidelidade

- §12 do relatório cita **25 URLs**; **5/25** têm captura bruta em disco; **20/25** não têm; **0/25** têm captura no UTC declarado (capturas reais 01:09:09-01:09:17Z vs declarados 00:51-00:56Z).
- `VERIFIED_ONLINE` textual nos entregáveis: **81** (relatório) + **6** (`valve_opt_in_feasibility.md`) + **36** (`acquisition_source_matrix.json`) + **40** (`faceit_access_readiness.json`) = **163**; `RECAPTURED`/`FIDELITY`/`REPORT_TO_SOURCE`/`EVIDENCE_LOSS` = **0** nesses arquivos.
- `EVIDENCE_LOSS_EVENT` (01:08:42Z, `Remove-Item -Force`, ordem 6 s depois, recaptura 01:09:09-01:09:17Z) documentado **apenas** em `.agents/teamwork/**` e `scratch/…/INDEX.md` — **nenhum entregável**.
- `"Last updated July 2010"` (citação da E15): **0 ocorrências em 436 arquivos** de `.agents/`, `scratch/`, `artifacts/`.
- `~1.300`, `9.651`, `3.624.699.821` (E20/E23/E24): **exclusivos do relatório** (endpoints Kaggle sem captura).
- `demoparser2`: `importlib.util.find_spec` → `None` (**AUSENTE**) ⇒ `PENDING_TOOLCHAIN` correto.
- F12: no `steam_icsgoplayers_730.txt` (116.831 B, sha256 `017aab2121…c994a68`): `ICSGOPlayers`=0, `IGCVersion_730`=0, `icsgo`=0, `csgo`=0, `730`=0 → **ausência preservada, sem virar "interface confirmada"**.

---

## 2. Logic Chain

1. **De 1.1** — a contagem é minha, não de log alheio; 20 passed/0 skipped/0 failed ⇒ M8 verde e **sem skip silencioso**.
2. **De 1.4** — 0 tautologias executáveis (a única ocorrência de `assert True` está em docstring, provado por `tokenize`), 0 aprovação por razão vazia, 20/20 nomes exatos ⇒ os testes do §20 existem e têm corpo real (221 asserts).
3. **De 1.5** — 10/10 violações detectadas com Δ de arquivos = 0 no repositório ⇒ os testes **não são fachada** e a execução **não contaminou** o repo. Ressalva: 4 das 10 sondas (7-10) atacam helpers locais do módulo de teste, logo provam reação das asserções, não existência de componente de produção.
4. **De 1.2 e 1.3** — 265+20=285 e os 2 erros de coleta são rastreados, não modificados, com mtime anterior e falha por serviço local ausente ⇒ **`PREEXISTENCE_PROVEN`**, não "pré-existente por alegação".
5. **De 1.6** — detector autotestado (10/10 + 9/9) e 0 achados reais em 43 arquivos ⇒ **`SECRETS_SCAN_VERIFIED`**, não `SECRETS_SCAN_UNVERIFIED`.
6. **De 1.7** — (a) 20/25 evidências citadas sem artefato bruto contradizem a Regra 01 e a própria frase do L812; (b) 163 rótulos `VERIFIED_ONLINE` sem `RECAPTURED`/`REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` violam a regra vinculante registrada em `GATE_STATUS.md` L40; logo há violação documental **real**, não hipotética.
7. **Consequência de 6** — as violações são de **rotulagem/rastreabilidade**, não de fabricação: não há dado inventado (0 `.dem/.npz` no domínio intermediário), os gates não foram declarados `PASS` (Gate A = `ACCESS_PENDING`; C/D `NOT_EXECUTABLE`), a hipótese está `UNPROVEN_PENDING_DATA` e não há selo humano. Portanto o veredito não pode ser `PASS` (há violação verificada e não corrigida) nem `FAIL` (a base factual se sustenta e a correção é de documentação) ⇒ **`CONDITIONAL`**.

---

## 3. Caveats

1. **Fidelidade relatório↔fonte original é impossível de verificar**: os 7 `_tmp_*` foram apagados (01:08:42Z). Tudo o que verifiquei das 5 capturas refere-se ao conteúdo de **01:09**, não ao lido às 00:51–00:56Z. —
2. **Não verifiquei online as 20 URLs sem captura** (proibido rede/download no meu mandato). Não inferi conteúdo por memória.
3. **Não medi a suíte C# (xUnit)** — fora do escopo desta fase Python e proibido tocar C#. Registro `CSHARP_SUITE_UNVERIFIED_BY_THIS_AUDITOR`; o §20 pede mantê-la verde, o que não foi verificado por mim.
4. **`extract_demo.py` DEM→NPZ end-to-end não é executável** (`demoparser2` ausente) — `PENDING_TOOLCHAIN`; não testei extração real nem downloader em `--execute` (permanece `dry_run`).
5. **Sondas 7-10 do mutation probe** monkey-patcham helpers locais do módulo de teste. Elas provam que as asserções reagem, não que exista código de produção equivalente. Declarado no próprio docstring da suíte.
6. **`__pycache__` de `tools/intermediate_demo_acquisition/`**: 5 `.pyc` existiam antes da minha execução e continuam existindo (34 `.pyc` em todo `tools/`, inalterado). Usei `PYTHONPYCACHEPREFIX` em `%TEMP%` para não recriar nada; não removi nada (remoção é do encerramento, pelo Orchestrator).
7. **Não confirmei equivalência byte-a-byte das cópias temporárias** do probe; verifiquei por código que as escritas vão para `%TEMP%`, e os `PROBE_OK` que dependem de conteúdo real (1, 2, 4) sugerem fidelidade.
8. **Enumerações do §12/§13/§15/§17**: **não** citei contagens dessas seções da spec; as contagens que uso (20 testes, 25 URLs, 53 spots, 444 demos, 67 test) foram medidas por mim com o intervalo/arquivo indicado.

---

## 4. Conclusion

**`CONDITIONAL`.** M8 (os 20 testes) **não é fachada**: 20/20 passam, 10/10 mutações são detectadas, 221 asserts executáveis, 0 tautologia, 0 skip, 0 aprovação por `0/0`, 20/20 nomes exatos. Regressão íntegra (265+20=285) e os 2 erros de coleta são **comprovadamente** pré-existentes. Varredura de segredos independente e autotestada: **0** segredos. Gates C e D corretamente `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA / N/A (0/0)`; nenhum artefato alega PASS; hipótese `UNPROVEN_PENDING_DATA`; nenhum selo humano.

**Bloqueiam o PASS — 2 violações verificadas:**
- **V1 (`HIGH`)**: `source_feasibility_report.md` L812 + tabela L814-840 — **20/25** URLs citadas não têm artefato bruto em disco (Regra 01); números das E20/E23/E24 só existem no relatório.
- **V2 (`HIGH`)**: **163** ocorrências de `VERIFIED_ONLINE` (81+6+36+40) com **0** de `RECAPTURED`/`REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`, violando regra vinculante registrada em `GATE_STATUS.md` L40; nenhum entregável divulga o `EVIDENCE_LOSS_EVENT`.

**Correção exigida** (não exige dado novo, treino ou código): rotular as afirmações dependentes dos `_tmp_*` como `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED` com caminho+hash da captura `RECAPTURED`, e rebaixar as 20 URLs sem captura para `UNVERIFIED_NO_MATERIALIZED_CAPTURE` (ou materializar captura bruta).

---

## 5. Verification Method

Reprodução completa (cwd = `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`), tudo abaixo é **somente leitura**:

```powershell
# 1) contagem pytest própria — deve imprimir "20 passed" e nenhum "skipped"
python -m pytest tests/test_phase2a_intermediate_domain.py -v

# 2) regressão e baseline
python -m pytest tests -q --ignore=tests/test_concise.py --ignore=tests/test_concurrent_concise.py
python -m pytest tests -q --ignore=tests/test_concise.py --ignore=tests/test_concurrent_concise.py `
    --ignore=tests/test_phase2a_intermediate_domain.py        # deve imprimir "265 passed"

# 3) pré-existência dos 2 erros
git ls-files tests/test_concise.py tests/test_concurrent_concise.py
git status --porcelain -- tests/test_concise.py tests/test_concurrent_concise.py   # vazio
git log --oneline -3 -- tests/test_concise.py tests/test_concurrent_concise.py

# 4) mutation probe com prova antes/depois (TEMP fixo, pycache fora do repo)
$env:PYTHONPYCACHEPREFIX="C:\Users\ricar\AppData\Local\Temp\csbot_2a_int_pycache"
python .agents/teamwork/adversarial_auditor_2a_int_1/run_mutation_probe_audited.py

# 5) varredura de segredos autotestada
python .agents/teamwork/adversarial_auditor_2a_int_1/secrets_scan.py

# 6) inspeção estática da suíte (assert True / skip / asserts executáveis)
python .agents/teamwork/adversarial_auditor_2a_int_1/static_inspect_tests.py

# 7) materialização de evidência (5/25) e fidelidade temporal
python .agents/teamwork/adversarial_auditor_2a_int_1/evidence_materialization.py

# 8) contagem de rótulos VERIFIED_ONLINE vs RECAPTURED
python .agents/teamwork/adversarial_auditor_2a_int_1/label_counts.py

# 9) rastreabilidade de números / nomes do §20 / métricas N/A
python .agents/teamwork/adversarial_auditor_2a_int_1/number_traceability.py
python .agents/teamwork/adversarial_auditor_2a_int_1/final_checks.py
python .agents/teamwork/adversarial_auditor_2a_int_1/audit_json_artifacts.py
```

**Arquivos para inspeção direta:** `parecer_adversarial_audit.md`; `source_feasibility_report.md` L103, L812-840; `GATE_STATUS.md` L27-43; `scratch/2a_intermediate_research_cache/INDEX.md` L15-46; `acquisition_source_matrix.json::gate_a_summary`.

**Condições de invalidação deste parecer:**
1. `python -m pytest tests/test_phase2a_intermediate_domain.py -v` deixar de dar `20 passed` ou passar a reportar `skipped` > 0.
2. `run_mutation_probe_audited.py` retornar `PROBE_OK < 10` ou `VIOLACOES_DE_ISOLAMENTO > 0`.
3. Aparecer captura bruta das 20 URLs faltantes datada de 00:51–00:56Z (derruba V1) ou surgirem os 7 `_tmp_*` originais (derruba V2).
4. Qualquer `.dem/.npz/.parquet` aparecer em `datasets/mirage_domains/intermediate_competitive/` (derruba a conclusão de "0 dados fabricados").
5. Divergência de SHA-256 em qualquer arquivo listado em 5.1.

### 5.1 Artefatos deste parecer (bytes | SHA-256 | arquivo)

| Bytes | SHA-256 | Arquivo |
|---|---|---|
| 31490 | `12b9f16f88129b3bc1768934ae66e42f50ff4e8d1e35e118f61781567229cad7` | `parecer_adversarial_audit.md` |
| 4614 | `fbad5a9398c9a0eb8d91fc7f091d1b8d68e31c0b5cb2710974b7752b42e23729` | `pytest_own_output.txt` |
| 3816 | `d8f1fe94c993f1b03ce3cbaff2c1bc8b2e1e24f7595731ec3f45e75621e0088d` | `full_regression_own_output.txt` |
| 8478 | `6fa84487de157464aa5036bce2958e2e8794493b2d235306bb6c6e40620ba88f` | `mutation_probe_audited_output.txt` |
| 3536 | `348212422f3720510540ded01914d54da1f58dfd15708d7fcf7d63df9b1f8e28` | `mutation_probe_own_output.txt` |
| 4026 | `a51c6e7020734fbe779be3fb39c601cc4213694d18a09153148800673a9cba6b` | `secrets_scan_output.txt` |
| 2894 | `74f2b92feed8e45365850f87a4015217b040f7fc10458cacf5ccb8cbff942b22` | `static_inspect_tests_output.txt` |
| 6620 | `82611bc9b13b59a3e80dafc59f6bb45d10f5ebda6506bdeadafc9ce4e139a6ea` | `evidence_materialization_output.txt` |
| 2552 | `772d4eed18de88b1efc4f6ac980fdd7f69304046d786aa6560894db9c04076c3` | `label_counts_output.txt` |
| 10460 | `9633cde041631866a44b303407fa2b806639a173bc00c417a9bd3b9cee9a6644` | `skeptic_patterns_output.txt` |
| 897 | `a3249d64d8195b818c7feabf80d7c13f48dfa5268806454ac70f939a39ef763c` | `recapture_grep.txt` |

Scripts de verificação (código, reexecutável): `secrets_scan.py`, `static_inspect_tests.py`, `run_mutation_probe_audited.py`, `evidence_materialization.py`, `number_traceability.py`, `skeptic_patterns_scan.py`, `audit_json_artifacts.py`, `audit_misc_artifacts.py`, `final_checks.py`, `label_counts.py`, `status_vocabulary.py`.
