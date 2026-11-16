# PARECER DE AUDITORIA MATEMÁTICA E ESTATÍSTICA
## FASE 2A-INTERMEDIATE — 6 artefatos analíticos de `training_runs/intermediate_domain_study/`

- **Auditor**: Mathematical and Statistical Auditor (papel 4 do §3), instância `math_stat_auditor_2a_int_1`
- **Data UTC da auditoria**: 2026-11-09T01:32:00Z
- **Raiz do repositório**: `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`
- **Skills aplicadas**: `.agents/skills/csbot-math-logic-auditor/SKILL.md` (cópia local `SKILL_math_logic_auditor.md`), `.agents/skills/csbot-phase-gate/SKILL.md` (cópia local `SKILL_phase_gate.md`)
- **Natureza da auditoria**: `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS` (nenhum selo humano é emitido nem inferido — Regra `05-human-review-integrity`)

---

# VEREDITO

## `CONDITIONAL`

**Justificativa do veredito em uma frase**: todos os dez itens de integridade matemática e estatística auditados passam com zero falha grave — nenhuma fabricação de número, nenhuma ocorrência de literal decimal zero, invariante de support zero íntegro em (1600/1600) blocos, reconciliação aritmética exata e cobertura de spec exata — mas existe **1 defeito metodológico material** (§14: atribuição da medida de divergência ausente e com justificativas mutuamente contraditórias em (7/15) métricas), que impede o carimbo `PASS` sem correção.

---

## Sumário (5 linhas)

1. Os 6 artefatos e os 2 contratos-âncora foram recalculados do disco: **(8/8) SHA-256 MATCH** com tamanho exato.
2. O invariante de support zero está íntegro: **(1600/1600)** blocos com `numerator`+`denominator` têm `value = "N/A"`, `numerator = 0`, `denominator = 0`, `0` exceção; **`0` ocorrência** de literal decimal autônomo zero-ponto-zero em (6/6) arquivos.
3. A cobertura da spec é exata na enumeração literal: **(104/104)** itens das 10 enumerações materiais — (62/62) métricas/estatísticas (17 CT + 15 TR + 15 §14 + 15 §15) e (42/42) classificações/critérios (6 §13 + 7 §15 + 6 §16 + 7 §16 + 8 §17 + 8 §17) —, **`0` item inventado** e **`0` item omitido**; `SPEC_ENUMERATION_AUTHORITATIVE` respeitado em (3/3) divergências de contagem.
4. A aritmética fecha exatamente: **(53/53)** spots reconciliados per-spot contra a fonte, soma **(298143/298143)** de `eligible_sequences`, **(27/53)** com suporte e **(26/53)** `N/A`, **(0/53)** classificações proibidas, **(0/795)** números no bloco intermediário.
5. `CONDITIONAL` por **(1/1)** defeito metodológico material (§14) + **(7/7)** ressalvas documentais não bloqueantes, todas listadas e endereçáveis sem recomputar corpus.

---

## Tabela de verificação

> Todos os comandos foram executados a partir de `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`.
> Todos os scripts auxiliares residem **exclusivamente** em `.agents/teamwork/math_stat_auditor_2a_int_1/` (ver *Isolamento de papel*).

| # | Item verificado | Comando executado | Resultado | Contagem (N/D) |
|---|---|---|---|---|
| 1 | SHA-256 dos 6 artefatos + 2 contratos | `python .agents/teamwork/math_stat_auditor_2a_int_1/audit_core.py` (CHECK A) e `Get-FileHash -Algorithm SHA256 -Path <8 arquivos>` | Todos batem byte a byte | **(8/8) MATCH** |
| 2a | Invariante `status de não-execução ⇒ value=N/A ∧ num=0 ∧ den=0` | `python .../audit_core.py` (CHECK B — varredura recursiva de todo dict com `numerator`+`denominator`) | 917 `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` + 371 `NOT_AVAILABLE_IN_EXISTING_ARTIFACTS` + 312 `STRICT_NA` | **(1600/1600) conformes**, **(0/1600) violações** |
| 2b | Zero literal decimal autônomo (zero-ponto-zero) e sua forma percentual | `python .../audit_core.py` (CHECK C) — regex `(?<![\d.])0[.]0(?![0-9])`, a mesma expressão seguida de `[%]`, e `(?<![\d.])-0[.]0(?![0-9])` | Nenhuma ocorrência; `10.0`, `96.0`, `200.0`, `150.0`, `700.0` corretamente não capturados | **(0/6) arquivos com hit** |
| 2c | Percentuais sem `(N/D)` | `python .../audit_core.py` (CHECK D) — regex `(?<![\d.])\d+\.?\d*%` | 2 ocorrências, ambas legítimas: `50%` (overlap stride16/janela32, verificado em `professional_manifest_reference.json`) e `8.14%` com `(47028/577816)` explícito | **(2/2) com (N/D) ou constante verificada** |
| 2d | Macro-médias declaram denominador de classes ativas | `python .../audit_core.py` + inspeção de `aggregate_summary` | `N/A (0 de 0 classes com suporte > 0)` em CT e TR; `N/A (0/0)` em §14, §15, §16, §17 | **(6/6) artefatos** |
| 3 | Contagem literal da spec | `python .../count_spec.py` (extrai blocos indentados por intervalo de linhas de `ORIGINAL_REQUEST.md`) | **(62/62)** métricas/estatísticas (17+15+15+15) e **(42/42)** classificações/critérios (6+7+6+7+8+8) | **= (104/104)** — detalhe em *Divergências de spec* |
| 3b | Artefato cobre exatamente a enumeração | `python .../audit_spec_count.py` (pareamento posicional nome-a-nome) | CT 17/17, TR 15/15, §14 15/15, §15 15/15, extras 0, faltantes 0, duplicatas 0 | **(62/62) métricas**, **(0) extra**, **(0) omissão** |
| 4 | Correção estatística §14 | inspeção de `divergence_methods`, `bootstrap_policy`, `effective_sample_size_policy` + `python` sobre os 15 blocos `bootstrap`/`effective_sample_size` | JSD com `base = 2` e `0 log 0 = 0`; Wasserstein com métrica (euclidiana 3D em u) e unidade (u / s); unidade de bootstrap ∈ {`match`,`round`} | **(15/15)** unidades válidas (`match` 7/15, `round` 8/15); **(0/15)** janela; **(15/15)** ESS presente; **(0/15)** intervalo publicado |
| 4b | Atribuição JS × Wasserstein por métrica | tabela `js_applicable` × `wasserstein_applicable` | JSD atribuída a 6/15, Wasserstein a 2/15, **ambas `false` em 7/15** com razões contraditórias | **(8/15) resolvidas**, **(7/15) irresolutas** → **Ressalva 1** |
| 5 | 53 spots no catálogo real | `python .../audit_spots.py` (CHECK E, lê `mirage_spot_catalog_v3.json`) | `total_spots = 53`, `len(spots) = 53`, duplicatas 0 | **(53/53)** |
| 5b | Cobertura 53 sem duplicata/omissão | `python .../audit_spots.py` (CHECK F) | conjunto de ids igual ao catálogo; 0 faltando; 0 extra | **(53/53) cobertos**, **(0/53) duplicados**, **(0/53) ausentes** |
| 5c | Decomposição por tipo | `python .../audit_spots.py` + leitura de `spot_semantic_classification.json` | 30 + 13 + 3 + 2 + 5; divergência de tipo artefato × fonte = 0 | **(53/53)**; soma **(53/53)** |
| 6 | Classificações proibidas (§15) | `python .../audit_spots.py` (CHECK G) | `CROSS_DOMAIN_CONFIRMED` 0, `INTERMEDIATE_CONFIRMED` 0, `DOMAIN_SPECIFIC_INTERMEDIATE` 0, `DOMAIN_SPECIFIC_PRO` 0, `HUMAN_VALIDATED_ONLY` 0 | **(0/53)** proibidas |
| 6b | Flags de proteção do catálogo | leitura direta de `catalog_protection` e de `unmapped_intermediate_clusters.json` | `spots_promoted = 0`, `catalog_modified = false`, `spots_added = 0`, `spots_removed = 0`, `catalog_append_requires_human_review = true` | **(5/5) conformes** |
| 6c | Coerência classificação × suporte | `python .../audit_spots.py` | `INSUFFICIENT_SUPPORT ⟺ support_total = 0`; `PROFESSIONAL_CONFIRMED ⟺ support_total > 0` | **(53/53) coerentes**, **(0/53) incoerências** |
| 7 | Os 26 spots sem suporte profissional | `python .../audit_reconcile2.py` (compara conjuntos de ids) | `unsupported_spot_ids` (26) == `INSUFFICIENT_SUPPORT` (26); `supported_spot_ids` (27) == `PROFESSIONAL_CONFIRMED` (27); igualdade de conjuntos com `zero_support_classes` do índice | **(26/26) identificados**, **(0/26) não identificados** — sustentado por **2** artefatos independentes |
| 8 | Fabricação de números no lado intermediário | `python .../audit_spots.py` (CHECK I — 53 spots × 15 campos = 795 blocos) + `python .../audit_numbers.py` (CHECK K/L) | Nenhum campo numérico inesperado; 795 blocos com `value="N/A"`, `0/0` | **(0/795) números**; **(0/6) arquivos** com valor medido inventado |
| 9 | Coerência aritmética | `python .../audit_reconcile2.py` + `audit_spots.py` (CHECK H) | Soma reconstruída **da fonte**, não do artefato: 206888 + 44019 + 47236 = 298143 = `eligible_sequences`; 298143 + 3113291 = 3411434 | **(298143/298143)** exato; **(53/53)** spots per-spot exatos |
| 9b | Outras identidades declaradas | `python` sobre fontes citadas | 47028/577816 = 8.1389% → `8.14%`; legacy `spot_distribution_v2` 26 ids positivos, soma 47028, diferença de conjunto = exatamente `ct_retake_a_mid_clear_under_window`; 511 = 485 + 26 | **(5/5) identidades verificadas** |
| 9c | Hashes citados *dentro* dos artefatos | `python .../audit_cited_hashes.py` | 13 triplas (path, sha256, size) — todas batem com o disco | **(13/13) MATCH**, **(0)** ausente |
| 10 | Domínio/época e não-vazamento de resultado | `python` sobre `hypothesis_state`, `comparison_status`, `inputs_required`, `round_outcome_dependency` | `hypothesis_status = UNPROVEN_PENDING_DATA`; `comparison_status = NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`; resultado do round usado apenas em CT_15/TR_13 e sempre rotulado "uso analítico posterior apenas" | **(1/1) hypothesis**; **(15/15) metrics §14** `NOT_EXECUTABLE`; **(2/32) métricas** com dependência de resultado, ambas rotuladas |
| 11 | Ausência física de corpus intermediário | `Get-ChildItem datasets/mirage_domains -Recurse -File -Include *.dem` / `*.npz` / `*.zip,*.rar,*.gz,*.bz2,*.7z,*.tar` | 0, 0, 0; 13 arquivos não-demo (confere com `other_files: 13` do artefato CT) | **(0) .dem**, **(0) .npz**, **(0) arquivos compactados** |

---

## Lista de todos os hashes recalculados

### A) Os 6 artefatos auditados — SHA-256 recalculado do disco

| Caminho (relativo ao repo) | Bytes (disco) | SHA-256 recalculado | vs. dispatch |
|---|---|---|---|
| `training_runs/intermediate_domain_study/ct_standardization_analysis.json` | 55267 | `ee3a674aef6fb172d7255e4ef56a0b1e1a5a90c50d43cd88766f18bcbf289494` | **MATCH** |
| `training_runs/intermediate_domain_study/tr_standardization_analysis.json` | 58793 | `f15d12fa7a1e50e2ee00b9684d8d116f3e1467f8be94b4a3f75dcd37102bcc7f` | **MATCH** |
| `training_runs/intermediate_domain_study/professional_vs_intermediate.json` | 68615 | `a552ea2dc15edc73d4c6e324d9035bf0d79e3a8dc04079a44a14addbb20aad96` | **MATCH** |
| `training_runs/intermediate_domain_study/spot_domain_coverage.json` | 472843 | `91d410e8dc9bb2d72b85d8ae803e69948eb03cc6d5c6b111524f4d5c9d9a5a13` | **MATCH** |
| `training_runs/intermediate_domain_study/unmapped_intermediate_clusters.json` | 13280 | `0c5c035e8b5c22574695d5b786c5225776cdc3aaf11f40b5d4b13d60f05c5b23` | **MATCH** |
| `training_runs/intermediate_domain_study/pilot_corpus_quality.json` | 17021 | `c1a50cab6cc292dd5471d0a1b72620870700bb5e36f6871ecdf448a26ab73dc0` | **MATCH** |

### B) Os 2 contratos-âncora — SHA-256 recalculado do disco

| Caminho | Bytes (disco) | SHA-256 recalculado | vs. dispatch |
|---|---|---|---|
| `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json` | 43151 | `8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9` | **MATCH** |
| `datasets/mirage_v2/contracts/spot_semantic_classification.json` | 42391 | `cc88bd09f2586bd0f977285f3347a9a42707b5ce4839c67bb59f5c6ad9ac736b` | **MATCH** |

### C) As 13 triplas (path + sha256 + size) citadas *dentro* dos 6 artefatos — todas reconferidas contra o disco

| Caminho citado | Bytes | SHA-256 citado (= disco) |
|---|---|---|
| `datasets/mirage_v2/reports/positioning_head_distribution_v1.json` | 20499 | `b70af499ad5225b29faf25e0eef5b8815a1eb258dfeeb09a940723e2dea3b6a1` |
| `training_runs/positioning_v2_real_temporal/revised_spot_supervision_report.json` | 12239 | `1afcc3fe5f18f253079eb64c487ec84858aacb57583b79a77e7536a9babc2e89` |
| `datasets/mirage_v2/reports/spot_distribution_v2.json` | 4104 | `3c9633049714a86d284098eaeeb111ee6d80f9e15616fa656a0d3377b7edcfdf` |
| `datasets/mirage_v2/reports/spot_mapping_coverage_v2.json` | 36554 | `bf8fe83c80a5dd3bbcbff7d1a3a9dfcd46407696bdc9fb7111bcaefffbe60aa0` |
| `datasets/mirage_v2/reports/retake_provenance_v2.json` | 22153 | `fbc83e3020fa3a8a34edf343c207862f360e1453349accb6975f1954eb215ccd` |
| `datasets/mirage_v2/reports/plan_stage_distribution_v2.json` | 916 | `bd8fa018d87e0725509fb74cb8e4ce6ae441e32d51b0cb103947236c72331f3c` |
| `datasets/mirage_v2/reports/postplant_provenance_v2.json` | 10941 | `106648c7c8fbba34e3d587da3ac5d7adbc94d8e71e8350a2675d9c2b4c7e2ec7` |
| `datasets/mirage_v2/reports/clearance_waypoint_distribution_v2.json` | 1100 | `d72fd68df68cd805d770fb340f712d4773bad3996e9ac0133a11f9022a3327f3` |
| `datasets/mirage_v2/reports/unmapped_professional_clusters_v1.json` | 207405 | `0ff59741d847a2d24d9d3f08e6a9bd50b25cd1af0490e710d089ba3529c5adfd` |
| `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json` | 43151 | `8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9` |
| `datasets/mirage_v2/contracts/spot_semantic_classification.json` | 42391 | `cc88bd09f2586bd0f977285f3347a9a42707b5ce4839c67bb59f5c6ad9ac736b` |
| `training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json` | 1300 | `3b67b40087b683d73237c02a9c21bbb84f11d415809d2b486da759a7b203ab01` |
| `datasets/mirage_domains/domain_contract_v1.json` | 30587 | `95df901801d0a96495c7d3b30d08862513563b1b790e202b0738369fec02ae28` |

**Total**: **(21/21) hashes recalculados com MATCH** (6 artefatos + 2 contratos + 13 citados), **(0/21) MISMATCH**, **(0/21) truncados** (todos com 64 hex).

---

## Ressalvas

> Nenhuma ressalva abaixo envolve número fabricado, contaminação de Test, violação de support zero ou hash divergente. Todas são falhas de **materialização de declaração** ou de **coerência metodológica interna**, e nenhuma altera um único valor emitido — porque todos os valores emitidos são `N/A (0/0)`.

### Ressalva 1 — `MAJOR` — Atribuição da medida de divergência indefinida e contraditória em (7/15) métricas do §14
- **Onde**: `training_runs/intermediate_domain_study/professional_vs_intermediate.json` → `metrics[].jensen_shannon.applicable` / `metrics[].wasserstein.applicable`.
- **Observação**: em PVSI_01, PVSI_04, PVSI_09, PVSI_10, PVSI_12, PVSI_14, PVSI_15 **ambas** as medidas estão `applicable = false` e as justificativas se contradizem sobre a mesma métrica: JSD diz *"Representacao continua; ver wasserstein"* e Wasserstein diz *"Representacao categorica; ver jensen_shannon"*. Exemplo literal (PVSI_04, `distribution_representation = "proporcao (adimensional)"`): as duas razões são falsas para uma proporção e cada uma aponta para a outra, também marcada inaplicável. Não existe campo alternativo (`applicable_method`, `divergence_method`) que resolva a atribuição — verifiquei o conjunto completo de chaves: `['bootstrap','comparison_status','distribution_representation','effective_sample_size','groups','jensen_shannon','methodological_notes','metric_id','metric_name','operational_definition','spec_line_verbatim','wasserstein']`.
- **Distribuição**: JSD atribuída a **(6/15)**, Wasserstein a **(2/15)**, irresolutas **(7/15)**.
- **Por que importa**: o artefato declara `divergence_methods.definitions_locked = true`, mas em (7/15) métricas não há medida de divergência atribuída. Quando existir dado intermediário, (7/15) comparações não poderão ser executadas sem uma nova decisão metodológica — ou seja, a especificação é incompleta justamente na dimensão que esta fase se propõe a congelar.
- **Impacto no veredito**: é a **única** razão do `CONDITIONAL`. Sem ela, o veredito seria `PASS`.
- **Correção sugerida**: declarar, por métrica, um terceiro estado (`NOT_A_DISTRIBUTION` / `SCALAR_PER_DOMAIN`) ou atribuir exatamente uma das duas medidas; remover a referência cruzada circular.

### Ressalva 2 — `MINOR` — `round_outcome_dependency = true` é declarado em texto, mas o campo não existe no JSON
- **Onde**: `ct_standardization_analysis.json:578` e `tr_standardization_analysis.json:536` (strings `edge_cases_and_rejection`).
- **Observação**: o texto afirma "esta métrica **é marcada com** `round_outcome_dependency = true`", porém `grep -c round_outcome_dependency` retorna apenas essas 2 ocorrências, ambas **dentro de string**; `metrics[].round_outcome_dependency` é ausente em **(32/32)** métricas (17 CT + 15 TR). A informação existe apenas no bloco global `global_rules.round_outcome_leakage_prohibition.affected_metrics = ["CT_15"]`.
- **Impacto**: não bloqueia — a proibição de vazamento está declarada e o resultado do round é citado como insumo apenas em CT_15 e TR_13, ambos rotulados "uso analítico posterior apenas". Mas é uma afirmação estrutural sem lastro materializado (Regra `01-evidence-before-claims`).
- **Correção sugerida**: materializar o booleano por métrica.

### Ressalva 3 — `MINOR` — `dispatch_declared` não corroborável no dispatch persistido
- **Onde**: `ct_standardization_analysis.json` → `metric_count.dispatch_declared = 18`; `tr_standardization_analysis.json` → `metric_count.dispatch_declared = 15`.
- **Observação**: `.agents/teamwork/analyst_2a_int_1/DISPATCH.md` L22 e L23 registram §12 e §13 **sem contagem**. As contagens declaradas no dispatch só aparecem para §15 (`14 estatísticas, 7 classificações`, L25) e §17 (`8 critérios + 7 problemas`, L27) — e essas **(3/3)** estão corretas no artefato. Os valores 18 e 15 vêm apenas da paráfrase do próprio analista (`BRIEFING.md:37`, `handoff.md:174-177`).
- **Impacto**: não bloqueia — a resolução adotada é `SPEC_ENUMERATION_AUTHORITATIVE` e a contagem final está correta (17 e 15). Mas o rótulo atribui ao Orchestrator uma afirmação que não é reproduzível a partir do artefato citado.
- **Correção sugerida**: citar a mensagem-fonte com timestamp, ou substituir por `dispatch_declared: NOT_VERIFIABLE_FROM_PERSISTED_DISPATCH`.

### Ressalva 4 — `MINOR` — (4/53) spots com `associated_bombsite` divergente entre os dois contratos que o artefato diz reconciliar
- **Onde**: `spot_domain_coverage.json` → `catalog_reconciliation`; spots `tr_b_apps_house_staging`, `tr_b_apps_kitchen_control`, `tr_b_tapete_window_bomb_curve`, `tr_b_tapete_window_market_awp`.
- **Observação**: `mirage_spot_catalog_v3.json` registra `associated_bombsite = "B"` (e `sector = "Apartamentos B"`) para os quatro; `spot_semantic_classification.json` registra `associated_bombsite = "A"` para os mesmos quatro. O artefato adota o **catálogo** (`bombsite = "B"`), que é a escolha correta e coerente com o setor, mas **não declara** essa divergência de campo: `catalog_reconciliation` só prova igualdade de conjuntos de **ids** (`id_sets_equal`), não de campos.
- **Verificação complementar**: `dwell` declarado **(53/53)** idêntico à fonte, `primary_aim_profile` **(53/53)** idêntico, `side` **(53/53)** idêntico; `bombsite` diverge em **(4/53)** por valor e em **(10/53)** por caixa (`Mid` vs `MID`, semanticamente idêntico).
- **Impacto**: não bloqueia o lado matemático (nenhum número depende disso e a escolha é a correta), mas é uma reconciliação incompleta entre dois artefatos sensíveis (Regra `06-sensitive-artifact-protection` — o contrato defeituoso é `spot_semantic_classification.json`, **fora do meu escopo de escrita**).
- **Correção sugerida**: acrescentar bloco `field_level_divergences` com os 4 ids e encaminhar o defeito do contrato semântico ao Orchestrator.

### Ressalva 5 — `MINOR` — Rótulos de `data_nature` fora da taxonomia canônica de 5 rótulos
- **Onde**: os 6 artefatos. Ocorrências: `NONE_AVAILABLE` **(868/884)**, `NONE_MATERIALIZED_FOR_THIS_INDICATOR` **(15/884)**, `READ_FROM_EXISTING_ARTIFACTS_ONLY` **(1/884)**.
- **Observação**: `ct_standardization_analysis.json` → `global_rules.data_nature_policy.allowed_labels` declara os 5 rótulos canônicos (`REAL`, `SIMULATED`, `TEMPLATED`, `SYNTHETIC`, `INFERRED`) e, no campo imediatamente seguinte, `labels_used_in_this_artifact = ["NONE_AVAILABLE"]` — rótulo que **não pertence à própria lista que o bloco declara**. Regra `04-synthetic-data-labeling` usa o mesmo conjunto de 5.
- **Impacto**: não bloqueia — os rótulos usados significam "não há dado", o que é mais honesto do que reutilizar `SIMULATED`; nada é apresentado como `REAL`. É inconformidade formal de taxonomia.
- **Correção sugerida**: incluir `NONE_AVAILABLE` na lista de rótulos permitidos da fase, ou renomear para `NOT_APPLICABLE_NO_DATA`.

### Ressalva 6 — `MINOR` — `n_units_available = 0` também para o lado PROFESSIONAL, que possui 444 demos
- **Onde**: `professional_vs_intermediate.json` → `metrics[].bootstrap.n_units_available = 0` em **(15/15)** métricas; `effective_sample_size.value = "N/A"` em **(15/15)**.
- **Observação**: o lado profissional existe e tem **444 demos** (verificado em `datasets/mirage_domains/professional_manifest_reference.json`: `demo_inventory_accepted = 444`; 2364492 + 501434 + 545508 = 3411434 sequências). O valor `0` é correto como "comparação não executável", mas ambíguo como "0 unidades disponíveis".
- **Impacto**: não bloqueia; nenhum intervalo é publicado. Risco de leitura errada por auditor futuro.
- **Correção sugerida**: separar `n_units_available_professional` (444) de `n_units_available_intermediate` (0) e manter `comparison_status` como razão da não-execução.

### Ressalva 7 — `MINOR` — Rótulo `RETAKE` citado em critério negativo do §13 sem existir na taxonomia de 6 classes
- **Onde**: `tr_standardization_analysis.json:770` (`TR_CLASS_06.negative_criteria[0]`): *"Rotação tardia para retake após plant é RETAKE, não adaptação tardia; as duas classes são mutuamente exclusivas com precedência declarada."*
- **Observação**: `global_rules.six_mandatory_distinctions.categories` tem exatamente 6 rótulos (`DEFAULT_ORGANIZADO`, `DISPERSAO_ALEATORIA`, `EXECUTE`, `RUSH`, `FAKE`, `LATE_ROUND_ADAPTATION`) e `tie_break_precedence` tem 6. `RETAKE` não está em nenhuma das duas listas, nem existe slug `TR_CLASS_07`. A frase cria um destino de classificação não definido.
- **Impacto**: não bloqueia (nenhum round é classificado; `classes_defined = 6` e a distribuição é `N/A (0/0)`). É ambiguidade de especificação.
- **Correção sugerida**: trocar "é RETAKE" por "não recebe `LATE_ROUND_ADAPTATION` e é registrado em `secondary_flags` (retake), fora da taxonomia de 6".

### Ressalva 8 — `MINOR` — `CANDIDATE_NEW_POSITION` (485) citado de artefato profissional sem nota de divergência de taxonomia
- **Onde**: `unmapped_intermediate_clusters.json` → `professional_reference_for_methodology.classification_counts`.
- **Observação**: o rótulo `CANDIDATE_NEW_POSITION` não pertence às 7 classificações do §16 (`CANDIDATE_STANDARD_POSITION`, `CANDIDATE_CLEARANCE_WAYPOINT`, `CANDIDATE_POST_PLANT`, `CANDIDATE_RETAKE`, `CANDIDATE_AIM_VARIANT`, `PASSING_TRAJECTORY`, `NOISE`). O bloco declara corretamente `usage = REFERENCE_ONLY_NOT_A_BASELINE` e detalha a divergência de **limiares** (`criteria_difference_note`), mas não a divergência de **rótulos**.
- **Verificação**: os números citados são reais — `unmapped_professional_clusters_v1.json` tem 511 registros = 485 `CANDIDATE_NEW_POSITION` + 26 `CANDIDATE_CLEARANCE_WAYPOINT` **(511/511) conferidos**.
- **Impacto**: não bloqueia. Risco de o leitor supor que as 7 classes do §16 já foram aplicadas no lado profissional.
- **Correção sugerida**: acrescentar `taxonomy_divergence_note` listando o mapeamento esperado `CANDIDATE_NEW_POSITION → CANDIDATE_STANDARD_POSITION`.

---

## Divergências de spec

> **Método**: contagem própria, executada por `python .agents/teamwork/math_stat_auditor_2a_int_1/count_spec.py`, que lê `.agents/teamwork/ORIGINAL_REQUEST.md`, isola o intervalo de linhas indicado e conta as linhas de item (indentação de 4 espaços ou `N.`). **Nenhuma** das contagens abaixo foi copiada da tabela do dispatch; a tabela acima e esta seção foram produzidas por leitura literal do arquivo.

### Contagens que eu mesmo fiz

| Bloco da spec | Intervalo de linhas | Itens contados por mim (N/D) | Declarado no artefato | Veredito |
|---|---|---|---|---|
| §12 métricas CT | **1497–1513** | **17** (17/17) | `spec_enumerated = 17` | **CONFORME** |
| §13 métricas TR | **1527–1541** | **15** (15/15) | `spec_enumerated = 15` | **CONFORME** |
| §13 distinções obrigatórias | **1545–1550** | **6** (6/6) | `six_mandatory_distinctions.categories` = 6 | **CONFORME** |
| §14 grupos comparados | **1560–1562** | **3** (3/3) | `groups` = 3 (`PROFESSIONAL`, `FACEIT_LEVEL_5_6`, `FACEIT_LEVEL_7_8`) | **CONFORME** |
| §14 métricas | **1566–1580** | **15** (15/15) | `metrics` = 15 | **CONFORME** |
| §14 procedimentos estatísticos | **1584–1588** | **5** (5/5) | JSD, Wasserstein, IC, bootstrap-match, ESS — todos presentes | **CONFORME** |
| §15 estatísticas por spot | **1601–1615** | **15** (15/15) | `spec_enumerated = 15` | **CONFORME** |
| §15 classificações | **1619–1625** | **7** (7/7) | `classification_policy.spec_categories` = 7 | **CONFORME** |
| §16 critérios piloto | **1641–1646** | **6** (6/6) | `pilot_criteria` = 6 (`C16-01`…`C16-06`) | **CONFORME** |
| §16 classificações | **1650–1656** | **7** (7/7) | `classification_taxonomy` = 7 | **CONFORME** |
| §17 critérios de confirmação | **1666–1673** | **8** (8/8) | `criteria_count.spec_enumerated = 8`, lista com 8 | **CONFORME** |
| §17 problemas a avaliar | **1679–1686** | **8** (8/8) | `problem_count.spec_enumerated = 8`, lista com 8 | **CONFORME** |
| §19 leakage a evitar (controle) | **1739–1743** | **5** (5/5) | (fora dos 6 artefatos auditados) | N/A |
| §19 artefatos de split (controle) | **1753–1756** | **4** (4/4) | (fora dos 6 artefatos auditados) | N/A |
| §20 testes obrigatórios (controle) | **1766–1785** | **20** (20/20) | (fora dos 6 artefatos auditados) | N/A |
| §22 Gate A / B / C (controle) | **1854–1859 / 1863–1869 / 1873–1877** | **6 / 7 / 5** (6/6, 7/7, 5/5) | `pilot_corpus_quality.gate_mapping` cobre Gate C (5) e Gate D (3) | **CONFORME** (Gate C 5/5) |

### Divergências entre a contagem do dispatch e a enumeração literal, e como os artefatos as trataram

| Seção | Dispatch declarado no artefato | Contagem literal (minha, com linhas) | Tratamento no artefato | Avaliação |
|---|---|---|---|---|
| §12 | `dispatch_declared = 18` | **17** (17/17) — linhas 1497–1513 | `resolution = SPEC_ENUMERATION_AUTHORITATIVE`; 17 métricas materializadas; nenhuma 18ª inventada | **CORRETO** (autoridade da spec respeitada) |
| §15 | `dispatch_declared = 14` | **15** (15/15) — linhas 1601–1615 | `resolution = SPEC_ENUMERATION_AUTHORITATIVE`; 15 estatísticas materializadas | **CORRETO** |
| §17 problemas | `dispatch_declared = 7` | **8** (8/8) — linhas 1679–1686 | `resolution = SPEC_ENUMERATION_AUTHORITATIVE`; 8 problemas materializados | **CORRETO** |
| §13 | `dispatch_declared = 15` | **15** (15/15) — linhas 1527–1541 | `resolution = MATCH` | **CORRETO** (mas ver Ressalva 3) |
| §17 critérios | `dispatch_declared = 8` | **8** (8/8) — linhas 1666–1673 | `resolution = MATCH` | **CORRETO** |

**Conclusão das divergências**: **`SPEC_ENUMERATION_AUTHORITATIVE` foi respeitado em (3/3) casos de divergência**. Das 15 linhas da tabela anterior, **12 são enumerações materiais conformes** e **3 são controles fora de escopo** (§19 leakage, §19 splits, §20 testes). As 12 conformes somam **(112/112)** itens literalmente presentes nos artefatos, decompostos como (62/62) métricas e estatísticas + (42/42) classificações e critérios + (3/3) grupos do §14 + (5/5) procedimentos estatísticos do §14 — com **(0) extras**, **(0) omissões** e **(0) duplicatas**. O Gate C do §22 cobre (5/5) requisitos. A recomendação de correção dos 3 números no dispatch já foi adotada pelos artefatos.

---

## O que NÃO pude verificar

1. **A mensagem original do Orchestrator que originou o dispatch.** Só existe o consolidado `.agents/teamwork/analyst_2a_int_1/DISPATCH.md`. Por isso não posso afirmar que `dispatch_declared: 18` (§12) é falso — apenas que **não é reproduzível** a partir do texto persistido (Ressalva 3).
2. **A execução futura das métricas definidas.** Nenhum denominador existe; todos os `formula` dos artefatos são especificações não executadas. Não posso verificar se `2-1-2`, `anchor dwell`, DBSCAN com `eps = 96 u` ou JSD produzirão os resultados pretendidos quando houver dado — apenas que as definições são internamente coerentes e declaradas antes de ver os dados (o que é o requisito desta fase).
3. **A geometria interna do mapa.** Não reabri os 444 NPZ nem os 6 shards Parquet (proibido nesta fase e pelo meu escopo somente-leitura). As coordenadas dos 53 spots foram tratadas como dadas pelo catálogo; não recalculei centroides nem raios.
4. **Os valores de `mask` por spot** (`revised_spot_supervision_report.json` tem `mask: 0/1`). Usei `*_support` por split, que é o que os artefatos citam; não auditei o significado semântico de `mask`.
5. **A correspondência entre `eligible_sequences = 298143` e a contagem real dos shards.** Verifiquei a identidade `soma_suporte_por_spot = eligible_sequences` e a identidade `eligible + masked = total = 3411434`; **não** recontei linhas dos Parquet.
6. **Conformidade das métricas do lado C# / runtime / ONNX / testes do §20.** Fora do meu papel (papel 4 do §3; Regra `09-subagent-role-isolation`).
7. **A qualidade tática/CS2 das definições** (ex.: se `heavy-A = 3+` é o corte correto). Meu papel é auditor matemático; a plausibilidade física de domínio é do revisor de domínio CS2.
8. **Calibração probabilística (ECE / Brier)** prevista na skill `csbot-math-logic-auditor`: não há modelo, probabilidade nem matriz de confusão nesta fase — a skill foi aplicada apenas nos seus invariantes de support zero e de macro-média, que são os únicos aplicáveis.

---

## Isolamento de papel

- **Papel exercido**: auditor **somente-leitura** (Regra `09-subagent-role-isolation`, item 2: auditor opera com escrita desabilitada sobre implementação).
- **Caminhos lidos, sem nenhuma escrita**: `datasets/` (incl. `datasets/mirage_v2/contracts/`, `datasets/mirage_v2/reports/`, `datasets/mirage_domains/`), `training_runs/positioning_v2_real_temporal/`, `training_runs/intermediate_domain_study/`, `.agents/skills/`, `.agents/teamwork/ORIGINAL_REQUEST.md`, `.agents/teamwork/analyst_2a_int_1/`, `.agents/teamwork/orchestrator_2a_intermediate/`, `AGENTS.md`. **Nenhuma escrita** em `src/`, `tools/`, `tests/`, `datasets/`, `models/`, `training_runs/`, `scratch/`, nem em `training_runs/positioning_v2_real_temporal/`.
- **Caminho onde escrevi (único)**: `.agents/teamwork/math_stat_auditor_2a_int_1/` — arquivos `BRIEFING.md`, `progress.md`, `SKILL_math_logic_auditor.md`, `SKILL_phase_gate.md`, `explore.py`, `dump.py`, `spot_shape.py`, `audit_core.py`, `audit_spec_count.py`, `audit_spots.py`, `audit_reconcile.py`, `audit_reconcile2.py`, `audit_cited_hashes.py`, `audit_numbers.py`, `count_spec.py`, `parecer_mathematical_audit.md`, `handoff.md`.
- **Nada foi escrito em `%TEMP%`, `scratch/`, `tools/` ou qualquer diretório de biblioteca de terceiros.** Nenhum pacote foi instalado. Nenhum treinamento, avaliação no Test/Final Holdout, export ONNX, build C# ou shadow mode foi executado.
- **Achado do Orchestrator registrado, não auditado**: `tools/intermediate_demo_acquisition/__pycache__/` (5 `.pyc`) é `TRANSIENT_CACHE` e **não** foi usado como evidência em nenhuma parte deste parecer.

`write_scope: OWN_AGENT_DIRECTORY_ONLY`

---

## Comandos de reprodução (bloco único)

```powershell
cd c:/Users/ricar/OneDrive/Documentos/Dev/CsBot
$env:PYTHONIOENCODING='utf-8'
python .agents/teamwork/math_stat_auditor_2a_int_1/count_spec.py          # contagens literais da spec com intervalos de linha
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_core.py           # CHECK A hashes | B support-zero | C literais de zero decimal | D percentuais
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_spec_count.py     # spec x artefato, item a item
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_spots.py          # CHECK E-L: 53 spots, classificacoes, somas, blocos intermediate
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_reconcile2.py     # reconciliacao per-spot contra revised_spot_supervision_report
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_cited_hashes.py   # 13 triplas citadas: path+sha256+size
python .agents/teamwork/math_stat_auditor_2a_int_1/audit_numbers.py        # CHECK K/L: nenhum campo numerico medido
Get-ChildItem datasets/mirage_domains -Recurse -File -Include *.dem,*.npz,*.zip,*.rar,*.gz,*.bz2,*.7z,*.tar | Measure-Object
```

## Condição de invalidação deste parecer

Este parecer é inválido se qualquer um dos **(21/21)** SHA-256 divergir do disco, ou se for demonstrado que algum dos **(1600/1600)** blocos de status de não-execução contém valor numérico, ou se for apresentado um artefato intermediário (`.dem`/`.npz`) materializado após 2026-11-09T01:32:00Z — neste último caso todas as métricas hoje `N/A (0/0)` deixariam de ser `N/A` e a auditoria inteira precisa ser refeita.
