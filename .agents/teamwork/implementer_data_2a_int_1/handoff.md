# handoff.md — FASE 2A-INTERMEDIATE (M4 + M7 + M8)

**Papel**: Dataset and Metadata Implementer (dados/manifests/testes)
**Agente**: `implementer_data_2a_int_1`
**Data UTC de encerramento**: 2026-11-09T01:21:34Z
**Tipo de handoff**: HARD (tarefa concluída no escopo atribuído)
**Labels de verificação**: `AGENT_REVIEWED`, `AUTOMATED_CHECK_PASS`
**Veredito de aquisição do corpus (inalterado, herdado)**: `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`

> Nenhum selo humano (`APPROVED_BY_USER`, `REJECTED_BY_USER`, `HUMAN_CAPTURE_IN_GAME`) foi emitido por este agente.
> Nenhum treinamento, avaliação de Test, export ONNX, alteração C# ou download de demo foi executado.

---

## 1. Observation (observações diretas)

### 1.1 Artefatos entregues — caminho relativo, bytes e SHA-256 completo (64 hex, lidos do disco)

| # | Caminho (relativo à raiz do repo) | Bytes | SHA-256 |
|---|---|---|---|
| 1 | `datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json` | 21749 | `2dff36579e263456cdf1f3b51c7d8e500218c079071d5f06f090c59ce2ffb93e` |
| 2 | `datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json` | 14712 | `f6742f4854c73f55bd343a702cf5db9c805ba61250c0c92a52c92955ade3f99f` |
| 3 | `datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json` | 14026 | `e600404c4427f51b31cf524b42af966fa1911f25e36b3efb60e9e5ff6c35d8dc` |
| 4 | `datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json` | 9206 | `f3dbd17be5e7e436e3ae9f97a2749278e80c74d16670af4edb153b0c38f8e815` |
| 5 | `training_runs/intermediate_domain_study/intermediate_splits_proposal.json` | 15270 | `bbb611feeeeba64f3cd6ff0e3d7810b60341b0ab113e08538f6a86ff7119cb3a` |
| 6 | `tests/test_phase2a_intermediate_domain.py` | 65216 | `c3fbf0dc7f3f2c23072c37c57c0aeef61ec81380ddc0b53ee5cea054960691fd` |

Todos os arquivos existem no disco com tamanho > 0 e são carregáveis por `json.load` / `py_compile` (ver §5).
Comando que produziu a tabela (executado no terminal, saída colada literalmente):

```
python -c "
import hashlib,pathlib
for p in [...]:
    q=pathlib.Path(p); print(q.stat().st_size, hashlib.sha256(q.read_bytes()).hexdigest(), p, sep=' | ')
"
```

### 1.2 Contabilidade `(N/D)` explícita nos 4 manifests — NENHUM `0` apresentado como métrica

Os 4 manifests exigidos têm `records: []` (ou plano vazio equivalente) e bloco de contabilidade com
`numerator`/`denominator`/`aggregation`/`aggregation_value: null`/`aggregation_status`:

| Manifest | `records` | `record_count` | Bloco de contabilidade | `(N/D)` | `aggregation_status` |
|---|---|---|---|---|---|
| `intermediate_demo_inventory_v1.json` | `[]` | `0` | `accounting` (+ `corpus_accounting`) | `(0/0)` | `N/A_ZERO_DENOMINATOR` |
| `intermediate_npz_manifest_v1.json` | `[]` | `0` (`npz_count: 0`) | `accounting` | `(0/0)` | `N/A_ZERO_DENOMINATOR` |
| `pilot_download_manifest.json` | plano sem registros | `downloads_attempted: 0` | `accounting` | `(0/0)` | `N/A_ZERO_DENOMINATOR` |
| `quarantine_manifest.json` | `[]` | `0` (`total_quarantined: 0`) | `accounting` | `(0/0)` | `N/A_ZERO_DENOMINATOR` |
| `intermediate_splits_proposal.json` (M7) | — | `current_counts.total_demos: 0` | `current_counts` | `(0/0)` | `N/A_ZERO_DENOMINATOR` |

Exemplo literal (inventário):
```json
"accounting": {
  "accepted": 0, "rejected": 0, "quarantined": 0,
  "total_expected": 20, "total_observed": 0,
  "formula": "accepted+rejected+quarantined = total_observed (0+0+0=0)",
  "numerator": 0, "denominator": 0, "aggregation": "(0/0)", "aggregation_value": null,
  "aggregation_status": "N/A_ZERO_DENOMINATOR",
  "aggregation_note": "(0/0) NÃO é taxa de aprovação, NÃO é evidência de qualidade e NÃO autoriza nenhuma conclusão sobre o corpus. Expressa apenas que zero candidatas foram submetidas ao inventário."
}
```

Verificação mecânica (script `verify_artifacts.py`, saída literal resumida):

```
datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json
  bytes=21749  sha256=2dff36579e263456cdf1f3b51c7d8e500218c079071d5f06f090c59ce2ffb93e
  record_count=0  npz_count=None
  agregacao explicita: (0/0) status='N/A_ZERO_DENOMINATOR'   (x2)

datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json
  bytes=14712  sha256=f6742f4854c73f55bd343a702cf5db9c805ba61250c0c92a52c92955ade3f99f
  record_count=0  npz_count=0
  agregacao explicita: (0/0) status='N/A_ZERO_DENOMINATOR'   (x2)
  agregacao explicita: (0/0) status='NOT_EXECUTED_NO_INTERMEDIATE_DATA'

datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json
  bytes=14026  sha256=e600404c4427f51b31cf524b42af966fa1911f25e36b3efb60e9e5ff6c35d8dc
  agregacao explicita: (0/0) status='N/A_ZERO_DENOMINATOR'

datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json
  bytes=9206  sha256=f3dbd17be5e7e436e3ae9f97a2749278e80c74d16670af4edb153b0c38f8e815
  record_count=0
  agregacao explicita: (0/0) status='N/A_ZERO_DENOMINATOR'

training_runs/intermediate_domain_study/intermediate_splits_proposal.json
  bytes=15270  sha256=bbb611feeeeba64f3cd6ff0e3d7810b60341b0ab113e08538f6a86ff7119cb3a
  agregacao explicita: (0/0) status='N/A_ZERO_DENOMINATOR'

TODOS OS 5 ARTEFATOS PRESENTES, NAO VAZIOS, JSON VALIDO E COM SHA-256 DE 64 HEX.
```

### 1.3 Contagem de 53 spots lida do catálogo real (caminho + hash)

```
CATALOGO datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json
  bytes = 43151
  sha256= 8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9
  total_spots = 53 | len(spots) = 53 | ids unicos = 53
```
Caminho e hash conferem com a referência `spot_catalog_53` de
`datasets/mirage_domains/professional_manifest_reference.json` (asserção executada em
`test_SpotPromotionRequiresHumanReview`, linhas 1157–1170).

### 1.4 Corpus intermediário está vazio (0 dados; nada fabricado)

```
DIRETORIOS DO DOMINIO INTERMEDIARIO (contagem de arquivos de dados)
  raw_demos      existe=True arquivos=1 nomes=['README.md']
  archives       existe=True arquivos=1 nomes=['README.md']
  processed_npz  existe=True arquivos=1 nomes=['README.md']
  quarantine     existe=True arquivos=1 nomes=['README.md']
  manifests      existe=True arquivos=1 nomes=['README.md']
  metadata       existe=True arquivos=1 nomes=['README.md']
  reports        existe=True arquivos=1 nomes=['README.md']

VARREDURA GLOBAL DE DADOS NO DIRETORIO INTERMEDIARIO
  .dem/.npz/.parquet encontrados = []
```

### 1.5 Saída BRUTA e LITERAL de `python -m pytest tests/test_phase2a_intermediate_domain.py -v`

Comando exato executado:
```
cd c:/Users/ricar/OneDrive/Documentos/Dev/CsBot
python -m pytest tests/test_phase2a_intermediate_domain.py -v
```
Saída literal (exit code 0), também persistida em `.agents/teamwork/implementer_data_2a_int_1/pytest_m8_literal_output.txt`:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ricar\OneDrive\Documentos\Dev\CsBot
plugins: anyio-4.14.1
collecting ... collected 20 items

tests/test_phase2a_intermediate_domain.py::test_ProfessionalCorpusRemainsUnchanged PASSED [  5%]
tests/test_phase2a_intermediate_domain.py::test_IntermediateCorpusUsesSeparateDirectory PASSED [ 10%]
tests/test_phase2a_intermediate_domain.py::test_RankSystemIsExplicit PASSED [ 15%]
tests/test_phase2a_intermediate_domain.py::test_FaceitLevelIsNotConvertedToValveRank PASSED [ 20%]
tests/test_phase2a_intermediate_domain.py::test_PremierRatingIsNotConvertedToCompetitiveRank PASSED [ 25%]
tests/test_phase2a_intermediate_domain.py::test_UnknownRankIsNotPromoted PASSED [ 30%]
tests/test_phase2a_intermediate_domain.py::test_DownloadRequiresApprovedSource PASSED [ 35%]
tests/test_phase2a_intermediate_domain.py::test_SignedUrlsAreNotPersisted PASSED [ 40%]
tests/test_phase2a_intermediate_domain.py::test_SecretsAreNotLogged PASSED [ 45%]
tests/test_phase2a_intermediate_domain.py::test_DemoHashIsRecorded PASSED [ 50%]
tests/test_phase2a_intermediate_domain.py::test_DuplicateDemoIsRejected PASSED [ 55%]
tests/test_phase2a_intermediate_domain.py::test_NonMirageDemoIsRejected PASSED [ 60%]
tests/test_phase2a_intermediate_domain.py::test_CorruptedDemoIsQuarantined PASSED [ 65%]
tests/test_phase2a_intermediate_domain.py::test_RoundLifecycleIsValid PASSED [ 70%]
tests/test_phase2a_intermediate_domain.py::test_IntermediateNpZContainsNoSyntheticHistory PASSED [ 75%]
tests/test_phase2a_intermediate_domain.py::test_SteamIdsArePseudonymizedInReports PASSED [ 80%]
tests/test_phase2a_intermediate_domain.py::test_SpotPromotionRequiresHumanReview PASSED [ 85%]
tests/test_phase2a_intermediate_domain.py::test_ProfessionalAndIntermediateMetricsRemainSeparate PASSED [ 90%]
tests/test_phase2a_intermediate_domain.py::test_BootstrapUsesMatchOrRoundUnit PASSED [ 95%]
tests/test_phase2a_intermediate_domain.py::test_NoTrainingStartsInThisPhase PASSED [100%]

============================= 20 passed in 0.78s ==============================
```

**Contagem final real: `20 passed` — 0 skipped, 0 failed, 0 errors.**

### 1.6 Lista de skips (exigida pelo Sentinel)

**Skips ocorridos: NENHUM (`0`).**

Existe no arquivo **um único** `pytest.skip` condicional, em
`IntermediateNpZContainsNoSyntheticHistory`, que **não disparou** nesta execução:

| Teste | Motivo do skip | Condição | Disparou? | Asserções executáveis que permanecem no mesmo teste mesmo se disparar |
|---|---|---|---|---|
| `IntermediateNpZContainsNoSyntheticHistory` | `NOT_EXECUTABLE_NO_REAL_NPZ_AVAILABLE` — o diretório externo `F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage` não existiria nesta máquina | `not npz_files` (linhas 1077–1082) | **NÃO** — o diretório existe com 444 `.npz` | (a) contrato do manifest (`zero_synthetic_history.required is True`, `records == []`, `npz_count == 0`, `dem_vs_npz_comparison.executed is False`); (b) detector flagra `np.linspace` em 3 eixos; (c) detector NÃO flagra jitter real (`std > 0`); (d) detector NÃO flagra janela estática |

### 1.7 Prova anti-fachada (mutation probe) — 10/10 violações detectadas

`mutation_probe.py` aplica uma violação real sobre **cópias em diretório temporário** (nenhum arquivo do
repo é escrito) e exige que o teste correspondente **falhe**. Saída literal:

```
MUTATION PROBE — suite M8 (cada linha aplica uma violacao e exige que o teste FALHE)
ProfessionalCorpusRemainsUnchanged                PROBE_OK     hash divergente em datasets/mirage_v2/canonical_temporal_splits_v1.json: 9bd9d18362601d5416a7cb3b0292b3c31d005
IntermediateCorpusUsesSeparateDirectory           PROBE_OK     artefato fora do diret¢rio do dom¡nio: C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\datasets\mirage_domains\in
SignedUrlsAreNotPersisted                         PROBE_OK     AssertionError (sem mensagem — asserção booleana)
ProfessionalAndIntermediateMetricsRemainSeparate  PROBE_OK     demo_id compartilhado entre domínios: ['acrobats-vs-b8-academy-m1-mirage']
BootstrapUsesMatchOrRoundUnit                     PROBE_OK     AssertionError (sem mensagem — asserção booleana)
NoTrainingStartsInThisPhase                       PROBE_OK     AssertionError (sem mensagem — asserção booleana)
RoundLifecycleIsValid                             PROBE_OK     AssertionError (sem mensagem — asserção booleana)
IntermediateNpZContainsNoSyntheticHistory         PROBE_OK     AssertionError (sem mensagem — asserção booleana)
SteamIdsArePseudonymizedInReports                 PROBE_OK     AssertionError (sem mensagem — asserção booleana)
SpotPromotionRequiresHumanReview                  PROBE_OK     AssertionError (sem mensagem — asserção booleana)
sondas=10  PROBE_OK=10  falhas=0
```

### 1.8 Regressão — suíte completa

```
python -m pytest tests -q --ignore=tests/test_concise.py --ignore=tests/test_concurrent_concise.py
285 passed, 9 warnings in 32.05s
```
Baseline registrada ANTES deste trabalho: `265 passed, 9 warnings in 37.52s` (`.agents/teamwork/implementer_data_2a_int_1/baseline_suite_run.txt`).
265 + 20 = 285 → **nenhuma regressão introduzida; nenhum teste pré-existente alterado**.

### 1.9 Corpus profissional inalterado (33 referências, 0 divergências)

```
references = 33 | totals.references_resolved = 33
bytes somados = 98491183
referencias divergentes = []
```
Cobre `datasets/mirage_v2/**` (splits, 6 shards, 6 sidecars, contratos, catálogo, checksum),
`training_runs/positioning_v2_real_temporal/**` (pause marker, `selected_candidate.pt` de 19022035 B,
matrizes e relatórios) e os 4 scripts de pipeline — todos com tamanho e SHA-256 idênticos aos registrados.

---

## 2. Logic Chain (cadeia de raciocínio)

1. **Da observação 1.4** (`.dem/.npz/.parquet encontrados = []`) conclui-se que o corpus intermediário é
   fisicamente vazio. Logo, qualquer registro, métrica, posição ou hash de demo seria **fabricação**.
2. **Da observação 1.2** decorre a forma correta de representar zero: os manifests descrevem o
   **esquema completo** (26 campos da §10 no inventário; validações e hard requirements da §11 no manifest
   NPZ; 10 motivos de quarentena; política de bootstrap/holdouts em M7) e registram `0` **apenas** dentro
   de blocos `numerator/denominator` = `0/0` com `aggregation_value: null` e
   `aggregation_status: N/A_ZERO_DENOMINATOR`. Assim o zero não vira métrica (Regra 03) nem aprovação disfarçada.
3. **Da observação 1.1** (arquivos > 0 B, JSON válido, SHA-256 de 64 hex) conclui-se que os artefatos são
   evidência materializada e verificável, não apenas declarada (Regra 01).
4. **A escolha de nomes de teste** segue a §20 literalmente: 20 funções de módulo com o CamelCase exato,
   expostas ao pytest por alias `test_<NomeExato>` (pytest só coleta prefixos `test_`). O bloco final faz
   `assert len(_EXACT_NAMED_TESTS) == 20`, o que **falha em tempo de coleta** se algum nome desaparecer —
   portanto o requisito "exatamente os 20 nomes" é auto-verificável.
5. **A ausência de fachada** é sustentada por dois fatos independentes: (i) cada teste exercita lógica real
   do repositório — `validate_skill_bucket.evaluate/load_contract`, `build_manifest.build_entry`,
   `deduplicate_demo.collect_files/classify`, `verify_archive.verify/_make_zip`,
   `download_demo.validate_url/main/assert_no_secret_leak` —, além de 33 hashes do corpus profissional,
   do catálogo de 53 spots, dos 444 demos canônicos e de um NPZ real somente-leitura; (ii) a observação 1.7
   mostra que **todos os 10 testes amostrados falham** quando a regra correspondente é violada.
6. **Da observação 1.5** (20 passed, 0 skipped) conclui-se que nenhum teste foi aprovado por `0/0`: os testes
   que verificam ausência de dados o fazem por **asserção de contrato** (`records == []`, `npz_count == 0`,
   `dem_vs_npz_comparison.executed is False`, `training_started is False`), e os que verificam regras
   operacionais o fazem por **entrada negativa real** (mutação, URL fora da allowlist, host HTTP, zip
   corrompido, checksum divergente, mapa `de_dust2`, hash inválido, duplicata exata).
7. **Da observação 1.9** conclui-se que a Regra 06 e a proibição de tocar artefatos canônicos foram
   respeitadas: 33/33 referências com hash intacto.
8. **Da observação 1.8** conclui-se ausência de regressão: 265 → 285 sem alterar nenhum teste existente.

---

## 3. Caveats (ressalvas e limites)

1. **Zero dados reais de domínio intermediário.** Nenhuma validação de *qualidade* de demo, comparação
   `dem` vs `npz` intermediária, distribuição de ranks, cobertura de spots intermediária ou ganho de
   generalização foi — nem poderia ser — medida. `dem_vs_npz_comparison.executed: false` e
   `comparison_status: NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` registram isso explicitamente.
2. **Dois arquivos de teste pré-existentes falham na coleta** (`tests/test_concise.py`,
   `tests/test_concurrent_concise.py`) por exigirem um servidor Ollama local
   (`urllib.error.URLError: [WinError 10061]`). São **pré-existentes**, não foram modificados e por isso a
   suíte completa foi executada com `--ignore` nesses dois arquivos. Log do baseline em `baseline_suite_run.txt`.
3. **Um teste depende de um diretório externo** (`F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage`) para a
   porção (d) de `IntermediateNpZContainsNoSyntheticHistory`. Nesta máquina o diretório existe (444 `.npz`),
   então **não houve skip**; em outra máquina ele produziria skip **com motivo explícito**, mantendo as
   asserções de contrato e de fixture (a–c) já executadas antes do skip.
4. **Validador de lifecycle de round, detector de histórico sintético, pseudonimização, política de promoção
   de spot, contagem de unidade independente e checagem do pause marker são locais ao módulo de teste** —
   declarados nos docstrings — porque o repositório não expõe funções reutilizáveis equivalentes. O
   comportamento testado nesses pontos é o **contrato** escrito nos manifests, não uma função de produção.
5. **`git status` não serve como prova de imutabilidade** aqui: `datasets/` e `training_runs/` estão
   integralmente não rastreados (`?? datasets/`). A prova usada é a comparação de 33 tamanhos + SHA-256
   contra `professional_manifest_reference.json` (observação 1.9).
6. **`aggregation` `(0/8)`** aparece em `pilot_download_manifest.json::source_authorization_detail`
   (0 de 8 sub-fontes com `.dem` acessível). Esse denominador **não é zero** e é uma contagem de sub-fontes
   da matriz de aquisição, não taxa de download; está rotulado como tal no próprio campo `aggregation_note`.
7. **Não foi executado** nada de: treino, avaliação de Test, export ONNX, alteração C#, shadow mode,
   MLMove V2, Jump Head, download de demo. O modo do downloader permanece `dry_run`.

---

## 4. Conclusion

M4, M7 e M8 estão **concluídos** no escopo atribuído, com evidência materializada:

- **M4 (4 manifests)**: criados com o esquema canônico da §10/§11 e contabilidade `(0/0)` explícita, sem
  nenhum registro de demo, nenhum ID, hash ou métrica fabricados. `acquisition_status` =
  `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`; `pilot_download_manifest` em `dry_run` com
  `source_authorization_status: PENDING_HUMAN_APPROVAL`, `signed_urls_persisted: 0`, `secrets_persisted: 0`,
  `resume_state: null`; `quarantine_manifest` com `status: EMPTY_NO_CANDIDATES` e 10 motivos de quarentena.
- **M7 (proposta de splits)**: `proposal_status: DESIGN_ONLY_NOT_MATERIALIZED`,
  `materialization_blocked_reason: LESS_THAN_50_DEMOS_AVAILABLE`, 70/15/15 **por partida completa**, unidade
  `match_id` (alternativa `round_id`), 4 holdouts desenhados e matriz de leakage com teste automatizado por
  risco, `current_counts` `(0/0)`, `minimum_viable_demo_count: 50`.
- **M8 (20 testes)**: **20 passed, 0 skipped, 0 failed** — nenhum `assert True`, nenhum `0/0` como aprovação,
  nenhum skip executado, e cada teste tem cenário de entrada que o faz falhar (demonstrado em 10/10 sondas).

**Bloqueio remanescente é externo a este papel e permanece aberto**: não existe nenhuma demo intermediária
acessível. Nada neste trabalho autoriza materializar splits, iniciar treinamento ou promover spots.

---

## 5. Verification Method (como verificar de forma independente)

Executar, a partir da raiz `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`:

```powershell
# 1) Suíte M8 — deve imprimir exatamente "20 passed"
python -m pytest tests/test_phase2a_intermediate_domain.py -v

# 2) Regressão — deve imprimir "285 passed"
python -m pytest tests -q --ignore=tests/test_concise.py --ignore=tests/test_concurrent_concise.py

# 3) Integridade mecânica dos 5 JSON (bytes, SHA-256 64 hex, blocos (N/D))
python .agents/teamwork/implementer_data_2a_int_1/verify_artifacts.py

# 4) Prova anti-fachada — deve imprimir "sondas=10  PROBE_OK=10  falhas=0"
python .agents/teamwork/implementer_data_2a_int_1/mutation_probe.py

# 5) Compilação
python -m py_compile tests/test_phase2a_intermediate_domain.py
```

Conferências pontuais:

- **Nenhum `assert True`**: `Select-String -Path tests/test_phase2a_intermediate_domain.py -Pattern "assert True"` → só a menção em comentário/docstring de cabeçalho.
- **Nenhum skip executado**: a linha final do pytest deve ser `20 passed`, **sem** `skipped`.
- **53 spots**: `python -c "import json;c=json.load(open('datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json',encoding='utf-8'));print(c['total_spots'],len(c['spots']))"` → `53 53`; SHA-256 `8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9`.
- **Corpus profissional intacto**: `python -c` comparando as 33 entradas de `professional_manifest_reference.json` → `referencias divergentes = []`.
- **Manifests sem dados fabricados**: `python -c "import json;print(json.load(open('datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json',encoding='utf-8'))['records'])"` → `[]`.

**Condições de invalidação** (qualquer uma derruba esta entrega):
1. `record_count`/`records` de qualquer manifest deixar de ser vazio sem que exista demo física correspondente.
2. Qualquer SHA-256 de `datasets/mirage_v2/**` ou `training_runs/positioning_v2_real_temporal/**` divergir do registrado.
3. A suíte M8 passar a reportar `skipped` > 0 ou contagem final diferente de `20 passed`.
4. `mutation_probe.py` retornar `PROBE_FAIL` (teste passando com a regra violada).
5. Aparecer `.dem`/`.npz` sob `datasets/mirage_domains/intermediate_competitive/` sem proveniência aprovada por humano.
