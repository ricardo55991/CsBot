# HANDOFF — math_stat_auditor_2a_int_1

**Tipo**: Hard (tarefa concluída)
**Data UTC**: 2026-11-09T01:35:00Z
**Papel**: Mathematical and Statistical Auditor (papel 4 do §3), somente-leitura
**Parecer**: `.agents/teamwork/math_stat_auditor_2a_int_1/parecer_mathematical_audit.md`

---

## 1. Observation

Todas as observações abaixo foram produzidas por execução real no repositório `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`. Scripts em `.agents/teamwork/math_stat_auditor_2a_int_1/`.

### 1.1 Hashes (recalculados do disco)

| Arquivo | Bytes | SHA-256 | vs. dispatch |
|---|---|---|---|
| `training_runs/intermediate_domain_study/ct_standardization_analysis.json` | 55267 | `ee3a674aef6fb172d7255e4ef56a0b1e1a5a90c50d43cd88766f18bcbf289494` | MATCH |
| `training_runs/intermediate_domain_study/tr_standardization_analysis.json` | 58793 | `f15d12fa7a1e50e2ee00b9684d8d116f3e1467f8be94b4a3f75dcd37102bcc7f` | MATCH |
| `training_runs/intermediate_domain_study/professional_vs_intermediate.json` | 68615 | `a552ea2dc15edc73d4c6e324d9035bf0d79e3a8dc04079a44a14addbb20aad96` | MATCH |
| `training_runs/intermediate_domain_study/spot_domain_coverage.json` | 472843 | `91d410e8dc9bb2d72b85d8ae803e69948eb03cc6d5c6b111524f4d5c9d9a5a13` | MATCH |
| `training_runs/intermediate_domain_study/unmapped_intermediate_clusters.json` | 13280 | `0c5c035e8b5c22574695d5b786c5225776cdc3aaf11f40b5d4b13d60f05c5b23` | MATCH |
| `training_runs/intermediate_domain_study/pilot_corpus_quality.json` | 17021 | `c1a50cab6cc292dd5471d0a1b72620870700bb5e36f6871ecdf448a26ab73dc0` | MATCH |
| `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json` | 43151 | `8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9` | MATCH |
| `datasets/mirage_v2/contracts/spot_semantic_classification.json` | 42391 | `cc88bd09f2586bd0f977285f3347a9a42707b5ce4839c67bb59f5c6ad9ac736b` | MATCH |

**(8/8) MATCH**. Mais **(13/13)** triplas (path, sha256, size) citadas *dentro* dos artefatos, reconferidas contra o disco: **(21/21) hashes totais MATCH, (0) MISMATCH**.

### 1.2 Invariante de support zero

`python .agents/teamwork/math_stat_auditor_2a_int_1/audit_core.py` (CHECK B) varreu recursivamente todo `dict` contendo `numerator` **e** `denominator` nos 6 artefatos:

```
Blocos com numerator+denominator encontrados: 1600
   NOT_EXECUTABLE_NO_INTERMEDIATE_DATA                     917
   NOT_AVAILABLE_IN_EXISTING_ARTIFACTS                     371
   STRICT_NA                                               312
VIOLACOES: 0
```

**(1600/1600) conformes**, sendo conforme = `value == "N/A"` **e** `numerator == 0` **e** `denominator == 0` (tipo `int`, não float).

### 1.3 Literais decimais autônomos

Regex `(?<![\d.])0\.0(?![0-9])` (mais a variante percentual e a negativa), aplicada aos 6 arquivos: **0 ocorrências** (0/6 arquivos com hit). `10.0`, `96.0`, `150.0`, `200.0`, `700.0`, `4500` corretamente **não** capturados.

### 1.4 Contagem literal da spec (`count_spec.py`)

| Bloco | Linhas de `ORIGINAL_REQUEST.md` | Contagem própria |
|---|---|---|
| §12 métricas CT | 1497–1513 | **17** |
| §13 métricas TR | 1527–1541 | **15** |
| §13 distinções | 1545–1550 | **6** |
| §14 grupos | 1560–1562 | **3** |
| §14 métricas | 1566–1580 | **15** |
| §14 procedimentos | 1584–1588 | **5** |
| §15 estatísticas | 1601–1615 | **15** |
| §15 classificações | 1619–1625 | **7** |
| §16 critérios piloto | 1641–1646 | **6** |
| §16 classificações | 1650–1656 | **7** |
| §17 critérios | 1666–1673 | **8** |
| §17 problemas | 1679–1686 | **8** |
| §20 testes (controle) | 1766–1785 | **20** |
| Gate A / B / C (controle) | 1854–1859 / 1863–1869 / 1873–1877 | **6 / 7 / 5** |

Métricas/estatísticas: 17+15+15+15 = **62**. Classificações/critérios: 6+7+6+7+8+8 = **42**. Total material **104**.

### 1.5 Catálogo e cobertura de spots

```
total_spots_field = 53 | len(spots) = 53 | duplicatas no catalogo: []
semantic (spot_semantic_classification.json) = list[53]
distribuicao spot_type: {POSITION_PROFILE: 30, CLEARANCE_WAYPOINT: 13,
                         STAGING_POSITION: 3, PLANT_POSITION: 2, TRANSITION_POINT: 5} -> soma 53
catalog_ids == sem_ids (conjuntos)? True
spot_domain_coverage: len=53, unicos=53, igual ao catalogo? True, faltando [], extra []
divergencias tipo artefato vs fonte: 0
classificacoes: {INSUFFICIENT_SUPPORT: 26, PROFESSIONAL_CONFIRMED: 27} -> soma 53
categorias proibidas: CROSS_DOMAIN_CONFIRMED 0, INTERMEDIATE_CONFIRMED 0, DOMAIN_SPECIFIC_INTERMEDIATE 0 -> (0/53)
coerencia classification x support: incoerencias: 0
```

### 1.6 Reconciliação aritmética (reconstruída da FONTE, não do artefato)

```
spots reconciliados per-split contra a fonte: (53/53)   divergencias: 0
soma a partir da FONTE: {'train': 206888, 'validation': 44019, 'test': 47236} total = 298143
eligible_sequences (indice): 298143 | igual? True
total_sequences 3411434 = eligible 298143 + masked 3113291 -> True
47028/577816 = 8.138923...% -> 8.14% (citado no artefato com (N/D) explicito) ✓
511 = 485 CANDIDATE_NEW_POSITION + 26 CANDIDATE_CLEARANCE_WAYPOINT ✓
legacy spot_distribution_v2: 26 ids positivos, soma 47028; diff de conjunto com supervision = exatamente ['ct_retake_a_mid_clear_under_window'] ✓
```

### 1.7 Bloco intermediário

`audit_spots.py` CHECK I: 53 spots × 15 campos = **795 blocos** `intermediate`, todos com `value = "N/A"`, `numerator = 0`, `denominator = 0`, `data_nature = "NONE_AVAILABLE"`. **0 problemas**, **0 números**.

`audit_numbers.py`: todos os campos numéricos do conjunto são estruturais (`numerator`, `denominator`, `size_bytes`, contagens declaradas, `base = 2` do JSD, `samples = 0`, `sum = 53`, `contract_declared_max_expected_dwell_ms = 4500` rotulado `CONTRACT_CONSTANT_NOT_MEASUREMENT`). **Nenhum valor medido** no lado intermediário.

### 1.8 Corpus intermediário inexistente (verificação própria)

```
Get-ChildItem datasets/mirage_domains -Recurse -File -Include *.dem  -> 0
Get-ChildItem datasets/mirage_domains -Recurse -File -Include *.npz  -> 0
Get-ChildItem datasets/mirage_domains -Recurse -File -Include *.zip,*.rar,*.gz,*.bz2,*.7z,*.tar -> 0
13 arquivos não-demo (confere com other_files: 13 do artefato CT)
```

### 1.9 Achado material (Ressalva 1)

```
id        metric                        js_app w_app  js_reason                          w_reason
PVSI_01   unique_position_clusters      False  False  Representacao continua; ver w...   Representacao categorica; ver j...
PVSI_04   recurring_spot_rate           False  False  Representacao continua; ver w...   Representacao categorica; ver j...
PVSI_09   2-1-2_rate                    False  False  Representacao continua; ver w...   Representacao categorica; ver j...
PVSI_10   retake_rate                   False  False  Representacao continua; ver w...   Representacao categorica; ver j...
PVSI_12   role_stability                False  False  Representacao continua; ver w...   Representacao categorica; ver j...
PVSI_14   player_diversity              False  False  Representacao continua; ver w...   Representacao categorica; ver j...
PVSI_15   team_diversity                False  False  Representacao continua; ver w...   Representacao categorica; ver j...
JSD aplicavel: 6 | W aplicavel: 2 | ambas false: 7 | soma 15
```

### 1.10 Outros achados

- `round_outcome_dependency` aparece **somente dentro de strings** (`ct:578`, `tr:536`), nunca como campo: **(0/32)** métricas CT+TR têm o booleano.
- `analyst_2a_int_1/DISPATCH.md` L22 (§12) e L23 (§13) **não contêm contagem**; L25 (§15) contém `14 estatísticas, 7 classificações`; L27 (§17) contém `8 critérios + 7 problemas`. Logo `dispatch_declared = 18` (CT) e `= 15` (TR) não são reproduzíveis do texto persistido; `14`, `7`, `8` são.
- (4/53) spots com `associated_bombsite` divergente entre contratos: `tr_b_apps_house_staging`, `tr_b_apps_kitchen_control`, `tr_b_tapete_window_bomb_curve`, `tr_b_tapete_window_market_awp` — catálogo = `"B"`, `spot_semantic_classification.json` = `"A"`. O artefato segue o catálogo (correto) e não declara a divergência.
- `data_nature`: `NONE_AVAILABLE` 868, `NONE_MATERIALIZED_FOR_THIS_INDICATOR` 15, `READ_FROM_EXISTING_ARTIFACTS_ONLY` 1 (884 total) — fora da taxonomia de 5 rótulos que o próprio `ct_standardization_analysis.json` declara permitida.
- `bootstrap.unit_of_resampling`: `match` (7/15), `round` (8/15), janela (0/15). `bootstrap.n_units_available = 0` inclusive no lado profissional (444 demos).

---

## 2. Logic Chain

1. O dispatch afirma que "não existe corpus intermediário". **Observação 1.8** confirma por varredura própria: 0 `.dem`, 0 `.npz`, 0 arquivos compactados. → O lado intermediário de toda métrica tem denominador estrutural 0.
2. Se o denominador é 0, a Regra `03-zero-support-is-na` exige `N/A` e proíbe qualquer forma numérica nula. **Observação 1.2** mostra que (1600/1600) blocos obedecem; **1.3** mostra que não há literal decimal zero autônomo; **1.7** mostra que os 795 blocos do lado intermediário por spot não contêm nenhum número além de `numerator = 0` / `denominator = 0`. → Não há fabricação no lado intermediário (item 8 do escopo **passa**).
3. Se não há fabricação, os únicos números presentes devem ser (a) contagens estruturais e (b) leituras de artefatos pré-existentes. **Observação 1.6** reconstrói a identidade crítica **da fonte** (`revised_spot_supervision_report.json`) em vez de aceitar a soma declarada: (53/53) spots batem per-spot e a soma é 298143, exatamente `eligible_sequences`. **1.6** também confirma 47028/577816 = 8.14 e 511 = 485+26. → Toda aritmética declarada fecha (item 9 **passa**).
4. Se os números de suporte são exatos, a classificação por spot deve ser função determinística deles. **Observação 1.5** mostra `INSUFFICIENT_SUPPORT ⟺ suporte = 0` em (53/53) e **(0/53)** categorias proibidas. → Os 26 spots sem suporte estão identificados e sustentados por 2 artefatos independentes (itens 6 e 7 **passam**).
5. Se os números de hash permitem ligar artefato↔fonte, então a proveniência é verificável. **Observação 1.1**: (21/21) hashes. → Nenhuma citação de fonte é fictícia (Regra `01` na dimensão de proveniência **passa**).
6. Resta verificar a dimensão que não depende de dado: a metodologia declarada. **Observação 1.4** confirma cobertura exata da enumeração (104/104). Mas **1.9** mostra que em (7/15) métricas do §14 **ambas** as medidas de divergência estão `applicable = false` e as duas justificativas se contradizem sobre a mesma métrica, sem campo alternativo que resolva. → A especificação do §14 é **incompleta em (7/15)**, o que é um defeito material em um artefato cuja única função é congelar metodologia.
7. Se (7/15) métodos não estão atribuídos mas nenhum valor é emitido, o defeito é de completude, não de falseamento. **1.9** + **1.2** confirmam `value = "N/A"` em todos. → O defeito **não** invalida o parecer como `FAIL`; impede `PASS`.
8. Os achados menores (**1.10**) são todos do tipo "declaração sem materialização" (`round_outcome_dependency`, `dispatch_declared`, `data_nature`, `n_units_available`) ou "reconciliação incompleta" (bombsite, taxonomia). Nenhum altera valor emitido. → `CONDITIONAL`, não `FAIL`.

---

## 3. Caveats

- Não tive acesso à **mensagem original** do Orchestrator que gerou o dispatch do analista; só ao consolidado `analyst_2a_int_1/DISPATCH.md`. Por isso `dispatch_declared: 18` é reportado como **não reproduzível**, não como falso.
- **Não** recontei linhas dos 6 shards Parquet nem dos 444 NPZ (proibido nesta fase). A identidade `298143` foi verificada contra o relatório de supervisão e o índice, não contra os tensores.
- **Não** auditei o significado de `mask: 0/1` por spot em `revised_spot_supervision_report.json`; usei apenas `train_support`/`validation_support`/`test_support`.
- **Não** auditei plausibilidade tática/CS2 das definições (ex.: se `heavy-A = ≥3` é o corte correto) — é do revisor de domínio.
- **Não** apliquei ECE/Brier/matriz de confusão da skill `csbot-math-logic-auditor`: não há modelo, probabilidade nem matriz nesta fase. Apliquei apenas as seções 1 (invariantes) na parte de support zero e macro-média.
- A Ressalva 4 aponta um defeito em `spot_semantic_classification.json` (artefato sensível, Regra `06`). **Não** o corrigi e **não** poderia: meu escopo de escrita é só o meu diretório.
- Interpretação alternativa considerada e descartada para a Ressalva 1: a de que os pares de razões seriam "por métrica, um método aponta para o outro de propósito". Não se sustenta porque, nas (8/15) métricas resolvidas, a razão do método inaplicável é coerente com a do aplicável (contínua→Wasserstein, categórica→JSD); nas (7/15) irresolutas as duas razões descrevem a mesma métrica como contínua **e** categórica ao mesmo tempo.

---

## 4. Conclusion

**VEREDITO: `CONDITIONAL`**

- Os 10 itens de escopo auditados **passam**: (8/8) + (13/13) hashes; (1600/1600) blocos de support zero conformes; (0/6) arquivos com literal decimal zero; (104/104) itens de spec; (53/53) spots; (0/53) classificações proibidas; (26/26) spots sem suporte identificados; (0/795) números intermediários; (298143/298143) identidade aritmética exata; `hypothesis_status = UNPROVEN_PENDING_DATA` e `comparison_status = NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` confirmados.
- A única razão de não ser `PASS` é a **Ressalva 1** (`MAJOR`): (7/15) métricas do §14 sem medida de divergência atribuída, com justificativas mutuamente contraditórias e `definitions_locked = true` afirmado.
- As outras **(7/7)** ressalvas são `MINOR` e não bloqueiam.
- **Ação recomendada ao Orchestrator**: devolver ao implementador a correção da Ressalva 1 (exige apenas atribuir um estado `NOT_A_DISTRIBUTION` ou uma das duas medidas por métrica, e remover a referência circular), e registrar as 7 menores. Não é necessário recomputar corpus, nem tocar em dataset, modelo ou código C#.
- **Achado colateral para o Orchestrator**: `spot_semantic_classification.json` tem `associated_bombsite = "A"` para 4 spots que o catálogo canônico designa como `"B"` — defeito pré-existente em artefato sensível, fora do escopo de escrita dos auditores.

---

## 5. Verification Method

Reprodução completa, a partir de `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`:

```powershell
$env:PYTHONIOENCODING='utf-8'
python .agents/teamwork/math_stat_auditor_2a_int_1/count_spec.py        # contagens literais + intervalos de linha
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_core.py        # A hashes | B support-zero | C literais | D percentuais
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_spec_count.py  # spec x artefato, item a item
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_spots.py       # E catalog | F cobertura | G classes | H somas | I intermediate
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_reconcile2.py  # per-spot contra a fonte autoritativa
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_cited_hashes.py# 13 triplas citadas
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_numbers.py     # nenhum valor medido
```

Arquivo para inspecionar: `.agents/teamwork/math_stat_auditor_2a_int_1/parecer_mathematical_audit.md`.

**Condições de invalidação**:
1. Qualquer um dos (21/21) SHA-256 divergir do disco.
2. Ser demonstrado que algum dos (1600/1600) blocos de não-execução contém valor numérico.
3. Surgir artefato `.dem`/`.npz` intermediário materializado após 2026-11-09T01:35:00Z — nesse caso todos os `N/A (0/0)` deixam de ser `N/A` e a auditoria inteira deve ser refeita.
4. Ser apresentada a mensagem original do Orchestrator que **de fato** declare 18 métricas no §12 — isso reclassificaria a Ressalva 3 de "não reproduzível" para "correta", sem mudar o veredito.
