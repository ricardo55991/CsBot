# Handoff — analyst_2a_int_1 (M5 + M6, FASE 2A-INTERMEDIATE)

**Tipo:** Hard (tarefa concluída)
**Papel:** Analista Espacial e Estatístico — não implementa código de produção
**Data (UTC):** 2026-11-09
**Rótulos de revisão:** `AGENT_REVIEWED`
**Rótulo de verificação automatizada:** `AUTOMATED_CHECK_PASS`

---

## 1. Observation

### 1.1 Artefatos materializados (medição direta do disco)

Todos em `training_runs/intermediate_domain_study/`. Bytes e SHA-256 completos calculados pelo
verificador `scratch/2a_int_analyst_generators/verify.py` a partir dos arquivos em disco.

| # | Arquivo | Bytes | Linhas | SHA-256 (64 hex) |
|---|---|---|---|---|
| 1 | `ct_standardization_analysis.json` | 55267 | 706 | `ee3a674aef6fb172d7255e4ef56a0b1e1a5a90c50d43cd88766f18bcbf289494` |
| 2 | `tr_standardization_analysis.json` | 58793 | 827 | `f15d12fa7a1e50e2ee00b9684d8d116f3e1467f8be94b4a3f75dcd37102bcc7f` |
| 3 | `professional_vs_intermediate.json` | 68615 | 1232 | `a552ea2dc15edc73d4c6e324d9035bf0d79e3a8dc04079a44a14addbb20aad96` |
| 4 | `spot_domain_coverage.json` | 472843 | 14215 | `91d410e8dc9bb2d72b85d8ae803e69948eb03cc6d5c6b111524f4d5c9d9a5a13` |
| 5 | `unmapped_intermediate_clusters.json` | 13280 | 274 | `0c5c035e8b5c22574695d5b786c5225776cdc3aaf11f40b5d4b13d60f05c5b23` |
| 6 | `pilot_corpus_quality.json` | 17021 | 361 | `c1a50cab6cc292dd5471d0a1b72620870700bb5e36f6871ecdf448a26ab73dc0` |
| 7 | `domain_training_strategy.md` | 33998 | 621 | `f8f3f402ddeba73ac62e1f591458d770bb18dce591d3e8e1c02ff720ac0605cf` |
| 8 | `scale_up_recommendation.md` | 7195 | 114 | `f6d4a74ab8aac53d7e5bea20242c0f7c01df0812295006f9a3c021623e8decf9` |

Soma de bytes dos 8 artefatos: 727012.

### 1.2 Resultado da verificação obrigatória

Saída literal do verificador (`python scratch/2a_int_analyst_generators/verify.py`), campos
relevantes:

```
"verdict": {
  "all_files_present": true,
  "all_json_parse": true,
  "forbidden_hits_total": 0,
  "structural_violations_total": 0,
  "spots_confirmed_53": true,
  "type_distribution_confirmed": true
}
```

- **Parse:** os 6 JSON carregam com `json.load` sem exceção (`json_load: OK` em todos).
- **Varredura do literal proibido:** `forbidden_hits_total = 0` para os tokens `0\.0` e `0\.0%`,
  varrendo os 8 arquivos em modo binário (não apenas por linha).
- **Auditoria estrutural:** `structural_violations_total = 0`. Regra aplicada: todo bloco com
  `metric_status` ou `status` pertencente a {`NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`,
  `NOT_AVAILABLE_IN_EXISTING_ARTIFACTS`, `STRICT_NA`, `NOT_EVALUABLE_NO_INTERMEDIATE_DATA`} deve ter
  `value == "N/A"` quando o campo existe e `numerator == 0` e `denominator == 0`. Foram auditados
  1671 blocos nesse estado: 958 `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`, 373
  `NOT_AVAILABLE_IN_EXISTING_ARTIFACTS`, 338 `STRICT_NA`, 2 `NOT_EVALUABLE_NO_INTERMEDIATE_DATA`.
  Nenhum bloco apresentou valor numérico.

### 1.3 Catálogo de spots — contagem confirmada

| Verificação | Valor |
|---|---|
| Caminho | `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json` |
| SHA-256 | `8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9` |
| Campo `total_spots` | 53 |
| Comprimento do array `spots` | 53 |
| Linhas no artefato `spot_domain_coverage.json` | 53 |
| Tipos (via `datasets/mirage_v2/contracts/spot_semantic_classification.json`, SHA-256 `cc88bd09f2586bd0f977285f3347a9a42707b5ce4839c67bb59f5c6ad9ac736b`) | `POSITION_PROFILE` 30, `CLEARANCE_WAYPOINT` 13, `STAGING_POSITION` 3, `PLANT_POSITION` 2, `TRANSITION_POINT` 5 |
| Soma dos tipos | 53 |
| Igualdade dos conjuntos de IDs (catálogo vs classificação vs supervisão) | verdadeira nas três comparações |

A distribuição 30/13/3/2/5 declarada no dispatch foi **confirmada** contra o catálogo real.

### 1.4 Spots sem suporte profissional

- Identificados: **26** (`spots_without_professional_support.count = 26`), com
  `unidentified_count = 0`.
- Fonte: `training_runs/positioning_v2_real_temporal/revised_spot_supervision_report.json`
  (SHA-256 `1afcc3fe5f18f253079eb64c487ec84858aacb57583b79a77e7536a9babc2e89`), campos
  `unsupported_spot_ids` e `per_spot_support[*].metric_status = STRICT_NA`.
- Contraprova independente: a lista coincide item a item com `zero_support_classes` de
  `training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json`.
- Distribuição de classificação resultante: `PROFESSIONAL_CONFIRMED` 27, `INSUFFICIENT_SUPPORT` 26,
  denominador 53.

### 1.5 Identidades aritméticas verificadas nos artefatos de origem

- Soma de suporte por spot nos três splits = 206888 (train) + 44019 (validation) + 47236 (test) =
  **298143**, que é exatamente o campo `eligible_sequences` de
  `full_index_spot_ranking_coverage.json`. `sum_equals_eligible_sequences = true`.
- Divergência entre eras de rotulagem detectada: o spot `ct_retake_a_mid_clear_under_window` tem
  suporte maior que zero no relatório do `label_contract_v2` e **não aparece** em
  `datasets/mirage_v2/reports/spot_distribution_v2.json`. Registrado em
  `artifact_consistency_check` com `discrepancy_status = "ERA_DIFFERENCE_DOCUMENTED"`. Nenhum dos
  dois artefatos foi recalculado.

### 1.6 Estado físico do domínio intermediário (medição própria)

Varredura recursiva de `datasets/mirage_domains/intermediate_competitive/` executada pelo gerador:

```
dem_files: 0
npz_files: 0
archive_files: 0
other_files: 11  (README.md operacionais de subdiretórios)
```

Confirmado de forma independente por contagem de arquivos com extensões `.dem/.npz/.rar/.zip/.gz`
= 0. Consequência: todo denominador intermediário é zero.

### 1.7 Bloqueio de hook observado e forma de leitura usada

O hook `protect-sensitive-files` (blocking) interceptou um `run_command` que citava
`datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json` junto de cmdlets de formatação, emitindo
`BLOQUEIO [protect-sensitive-files]: Modificação em artefato sensível bloqueada`. O hook classifica
como leitura permitida apenas comandos que **iniciam** por `Get-Content`/`Get-FileHash`/`Test-Path`
etc. e não contêm indicadores de escrita (`>`, `--output`, `tee`, `New-Item`, ...). A leitura foi
refeita nessa forma canônica e a geração programática roda a partir de script que apenas abre os
insumos em modo leitura. Nenhum arquivo de autorização
(`.agents/audit/sensitive_file_authorization.json`) foi criado e nenhuma escrita em artefato sensível
foi tentada.

---

## 2. Logic Chain

1. **Da evidência 1.6 para o status de todas as métricas.** Como não existe demo, nem NPZ, nem
   partida intermediária (contagem medida igual a zero), o denominador de qualquer métrica do lado
   intermediário é zero. Pela Regra 03, denominador zero não produz valor: produz `N/A`. Logo cada
   métrica de §12, §13, §14, §15 (coluna intermediária), §16 e §17 recebe
   `value = "N/A"`, `numerator = 0`, `denominator = 0` e `status = NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`.
   Isso está materializado e auditado (1.2), não apenas declarado.

2. **Da evidência 1.3 para a cobertura de spots.** O catálogo tem 53 spots com 30/13/3/2/5 por tipo.
   O artefato `spot_domain_coverage.json` contém exatamente 53 linhas, uma por `spot_id`, com o tipo
   lido da classificação semântica — ou seja, o tipo não foi inventado, foi copiado do artefato de
   contrato com hash registrado.

3. **Da evidência 1.4 para a classificação dos spots.** 27 spots têm suporte profissional maior que
   zero → `PROFESSIONAL_CONFIRMED`. 26 têm `support = 0` → `INSUFFICIENT_SUPPORT` (a classe
   `HUMAN_VALIDATED_ONLY` não foi atribuída porque o selo humano pertence ao usuário, Regra 05; o
   campo `HUMAN_LIVE_CALIBRATED` do catálogo é citado verbatim como registro pré-existente, não como
   atribuição deste artefato). As categorias `CROSS_DOMAIN_CONFIRMED`, `INTERMEDIATE_CONFIRMED` e
   `DOMAIN_SPECIFIC_INTERMEDIATE` foram explicitamente bloqueadas por exigirem dado intermediário.

4. **Da evidência 1.5 para a credibilidade das fontes.** A soma de suporte por spot reproduz
   exatamente o total de sequências elegíveis do índice, o que indica que o relatório de supervisão e
   a auditoria de cobertura foram produzidos a partir do mesmo índice. Isso autoriza usar o relatório
   de supervisão como fonte da coluna PROFESSIONAL. A divergência de um spot entre eras de rotulagem
   (1.5) obriga a registrar a diferença em vez de escolher silenciosamente um dos artefatos — e a
   escolha feita foi explícita: `label_contract_v2` é a fonte autoritativa desta fase.

5. **Do status de não-execução para a ausência de números.** Se nenhuma métrica foi executada, a
   única forma de preencher §14 seria inventar distribuições. O artefato
   `professional_vs_intermediate.json` mantém `comparison_status =
   NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` e registra que a JSD entre uma distribuição real e uma
   população vazia é **indefinida**, não igual a um nem a zero. Essa observação é o que impede um
   leitor de interpretar ausência de divergência como divergência nula.

6. **Da ausência de dados para a estrutura de §18.** Como a escolha entre A–E depende de comparar
   qualidade de supervisão entre domínios e um domínio não existe, a decisão é diferida. Para tornar
   a dilação auditável em vez de evasiva, o relatório publica uma árvore de decisão com variáveis
   mensuráveis (`N_demos`, `Q01`–`Q08`, `COV26`, `ESS_int`, `PR_flag`) e regras de precedência. Isso
   converte "não decidimos" em "decidiremos assim, com estes dados".

7. **Da árvore de decisão para o plano de escala.** A etapa que libera a escala para 200+ demos é a
   aprovação em Gates C e D do piloto de 20–50 demos. Portanto a recomendação de escala é condicional
   e escalonada (E0→E3), com critérios de parada — coerente com o §8 ("não escalar para 200 demos
   nesta fase") e com a Regra 08.

---

## 3. Caveats

1. **Contagens do dispatch divergem da enumeração literal da spec em três seções.** O dispatch pede
   "18 métricas" em §12, "14 estatísticas" em §15 e "7 problemas" em §17; a enumeração literal do
   `ORIGINAL_REQUEST.md` contém 17, 15 e 8 itens respectivamente. Adotei a enumeração da spec como
   autoritativa e registrei a divergência dentro de cada artefato (`metric_count`,
   `statistic_count`, `problem_count`), com `resolution = SPEC_ENUMERATION_AUTHORITATIVE`. Não criei
   o 18º item nem removi um problema para "fechar" a contagem. **Esta divergência deve ser decidida
   pelo Orchestrator**, não por mim.

2. **A coluna PROFESSIONAL de §15 é quase toda `N/A`.** Apenas 3 dos 15 itens têm valor real:
   `support_sequences` (contagem por split, do relatório de supervisão), `side` e `bombsite` (campos
   estruturais do catálogo). Os outros 12 exigem reprocessar NPZ/shards, o que a fase proíbe. Não
   tentei derivar median dwell, variância de posição ou distribuição de mira a partir de artefatos
   agregados, porque nenhum artefato existente os materializa por spot.

3. **A coluna PROFESSIONAL de §14 é integralmente `N/A`.** Nenhum dos 15 indicadores do §14 existe
   com a definição operacional exigida em artefato do repositório. Forneci três fatos contextuais
   lidos verbatim (cobertura de mapeamento, suporte por spot, contagem de 511 clusters profissionais)
   com caminho, hash e fórmula `(N/D)`, explicitamente marcados como contexto e não como métrica
   comparável.

4. **Os 511 clusters profissionais não são baseline do §16.** Os critérios do artefato profissional
   (20 episódios / 8 demos / 5 jogadores) diferem dos critérios do piloto (10 episódios / 5 partidas /
   10 jogadores). Registrei a diferença em `criteria_difference_note` e marquei o uso como
   `REFERENCE_ONLY_NOT_A_BASELINE`.

5. **Coordenadas e o texto de versão do catálogo não foram reproduzidos.** O invariante operacional
   exigido pelo Orchestrator foi "zero ocorrências do literal decimal com ponto" nos meus arquivos, e
   tanto coordenadas/raios do catálogo (p.ex. valores terminados em zero decimal) quanto o campo
   textual de versão (`v3` seguido de dois grupos decimais) introduziriam esse literal. A geometria
   permanece exclusivamente no catálogo canônico, cujo SHA-256 está registrado; a versão maior (`v3`)
   está registrada com nota explicando a omissão da forma textual. **Nada foi alterado no catálogo.**

6. **A identificação dos 26 spots depende de artefato de marco anterior.** Não recalculei suporte a
   partir dos shards. Se a auditoria de proveniência concluir que
   `revised_spot_supervision_report.json` não é confiável, a lista dos 26 deve ser refeita — e o
   artefato 4 fica inválido nesse ponto específico, não no restante.

7. **`unnecessary_rotation_proxy` e os arquetipos TR são construtos declarados.** Limiares como
   96 u (co-locação), 150–700 u (banda de dispersão), 400 u e 500 u (isolamento), 8 s, 10 s, 15 s,
   20 s, 45 s são herdados de raciocínio de domínio e do §16, **não calibrados por dados**. Estão
   rotulados `INFERRED`/política declarada, e a calibração exigirá registro prévio antes de qualquer
   leitura de resultado.

8. **`validation_status` do catálogo é registro humano pré-existente.** Todos os 53 spots trazem
   `HUMAN_LIVE_CALIBRATED`. Citei o campo verbatim e **não** atribuí `HUMAN_VALIDATED_ONLY`, para não
   fabricar chancela humana (Regra 05).

9. **Não investigatei** o conteúdo dos seis shards temporais nem dos 444 NPZ: a fase é somente
   leitura e não exige recálculo, e qualquer varredura pesada seria desproporcional ao escopo.

10. **Scripts de geração são efêmeros e ficam fora do repositório de entregáveis.** Estão em
    `scratch/2a_int_analyst_generators/` (`common.py`, `gen_ct.py`, `gen_tr.py`, `gen_pvsi.py`,
    `gen_spots.py`, `gen_unmapped_quality.py`, `verify.py`). São meio, não entregável; os 8 artefatos
    são o entregável. A reprodutibilidade semântica está descrita dentro de cada JSON (fórmula,
    insumos e fonte com hash).

---

## 4. Conclusion

Os 8 artefatos do escopo M5 + M6 estão materializados, com conteúdo substantivo, JSON válidos,
hashes calculados do disco e verificação automatizada aprovada (`AUTOMATED_CHECK_PASS`).

**Status canônicos:**

- `hypothesis_status: UNPROVEN_PENDING_DATA` — a hipótese do §0 não está confirmada nem refutada;
  reconhecer nomes familiares de spot não é evidência.
- `comparison_status: NOT_EXECUTABLE_NO_INTERMEDIATE_DATA` — nenhuma comparação profissional vs
  intermediário foi executada; JSD, Wasserstein, bootstrap e tamanho efetivo de amostra permanecem
  `N/A (0/0)`.
- `unmapped_intermediate_clusters.clusters_found: 0` com `catalog_append_requires_human_review: true`.
- `pilot_corpus_quality`: 8 critérios de confirmação e 8 problemas, todos
  `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`.
- `spot_domain_coverage`: 53 spots, 27 `PROFESSIONAL_CONFIRMED`, 26 `INSUFFICIENT_SUPPORT`,
  `catalog_modified: false`, `spots_promoted: 0`, `coordinates_modified: false`.
- `domain_training_strategy.md`: cinco estratégias avaliadas, árvore de decisão condicional publicada,
  `DECISION_DEFERRED_PENDING_INTERMEDIATE_DATA`.
- `scale_up_recommendation.md`: escala em quatro etapas, condicionada a acesso legítimo, licença de
  uso para ML e aprovação nos Gates C e D do piloto.

**O que este trabalho não faz e não afirmou:** não treinou modelo, não executou inferência, não
consultou Test nem Final Holdout, não modificou o catálogo, não promoveu spot, não baixou demo, não
alterou nenhum artefato de `datasets/mirage_v2/**` ou
`training_runs/positioning_v2_real_temporal/**`.

**Bloqueios remanescentes (para o Orchestrator):**

1. Decidir a divergência de contagem entre dispatch e spec em §12 (18 vs 17), §15 (14 vs 15) e §17
   (7 vs 8).
2. O veredito da fase continua sendo `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`; os artefatos
   aqui produzidos não podem mudá-lo, apenas descrevê-lo.
3. Qualquer avanço para aquisição, escala ou treinamento exige autorização humana explícita
   (Regra 08).

---

## 5. Verification Method

### 5.1 Comandos executados e saída esperada

```powershell
cd scratch/2a_int_analyst_generators
python verify.py
```

Saída esperada: `all_files_present: true`, `all_json_parse: true`, `forbidden_hits_total: 0`,
`structural_violations_total: 0`, `spots_confirmed_53: true`,
`type_distribution_confirmed: true`. Os bytes e SHA-256 de cada um dos 8 arquivos aparecem no bloco
`files` da saída.

### 5.2 Comandos de verificação independente (sem depender dos meus scripts)

```powershell
Get-ChildItem "training_runs/intermediate_domain_study" -File | Select-Object Name,Length
```

```powershell
Get-FileHash "training_runs/intermediate_domain_study/ct_standardization_analysis.json" -Algorithm SHA256
Get-FileHash "training_runs/intermediate_domain_study/tr_standardization_analysis.json" -Algorithm SHA256
Get-FileHash "training_runs/intermediate_domain_study/professional_vs_intermediate.json" -Algorithm SHA256
Get-FileHash "training_runs/intermediate_domain_study/spot_domain_coverage.json" -Algorithm SHA256
Get-FileHash "training_runs/intermediate_domain_study/unmapped_intermediate_clusters.json" -Algorithm SHA256
Get-FileHash "training_runs/intermediate_domain_study/pilot_corpus_quality.json" -Algorithm SHA256
Get-FileHash "training_runs/intermediate_domain_study/domain_training_strategy.md" -Algorithm SHA256
Get-FileHash "training_runs/intermediate_domain_study/scale_up_recommendation.md" -Algorithm SHA256
```

Cada hash deve coincidir com a tabela 1.1.

```powershell
Select-String -Path "training_runs/intermediate_domain_study/*" -Pattern "0\.0" -AllMatches
```

Saída esperada: nenhuma linha. Mesma varredura para `0\.0%`.

```powershell
Get-Content "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json" -Raw | ConvertFrom-Json |
  ForEach-Object { $_.spots } | Measure-Object
```

Saída esperada: contagem 53.

```powershell
Get-Content "datasets/mirage_v2/contracts/spot_semantic_classification.json" -Raw |
  ConvertFrom-Json | ForEach-Object { $_ } | Group-Object semantic_type
```

Saída esperada: `POSITION_PROFILE` 30, `CLEARANCE_WAYPOINT` 13, `STAGING_POSITION` 3,
`PLANT_POSITION` 2, `TRANSITION_POINT` 5.

### 5.3 Arquivos a inspecionar para conferir método (não só resultado)

- `ct_standardization_analysis.json` — bloco `metrics` (17 entradas, cada uma com
  `operational_definition`, `unit`, `inputs_required`, `formula`, `numerator`, `denominator`,
  `value`), bloco `global_rules.two_one_two_definition` e
  `global_rules.round_outcome_leakage_prohibition`.
- `tr_standardization_analysis.json` — bloco `round_archetype_classification.archetypes` (6 classes)
  e `global_rules.slow_round_is_not_default.operational_criterion`.
- `professional_vs_intermediate.json` — blocos `divergence_methods.jensen_shannon` (base 2
  declarada), `divergence_methods.wasserstein`, `bootstrap_policy.units_declared_per_metric` e
  `methodological_warnings`.
- `spot_domain_coverage.json` — blocos `catalog_reconciliation`,
  `spots_without_professional_support.spot_ids`, `classification_policy` e `spots` (53 linhas).
- `unmapped_intermediate_clusters.json` — `mining_pipeline` (8 estágios), `pilot_criteria` (6
  critérios) e `classification_taxonomy` (7 classes).
- `pilot_corpus_quality.json` — `hypothesis_state`, `confirmation_criteria` (8),
  `problems_to_evaluate` (8), `gate_mapping`.
- `domain_training_strategy.md` — seções 3 a 7 (estratégias A–E), seção 8 (tabela comparativa),
  seção 9 (árvore de decisão), seção 10 (domain averaging).
- `scale_up_recommendation.md` — seções 3 (pré-condições), 4 (etapas), 7 (critérios de parada).

### 5.4 Condições de invalidação

Este handoff deve ser rejeitado se qualquer das condições abaixo se verificar:

1. Qualquer um dos 8 arquivos estiver ausente, com zero bytes, ou com SHA-256 diferente do tabelado.
2. Qualquer JSON falhar em `json.load`.
3. Qualquer ocorrência dos literais `0\.0` ou `0\.0%` nos 8 arquivos.
4. Qualquer bloco com status de não-execução apresentar `value` numérico ou
   `numerator`/`denominator` diferente de zero.
5. O catálogo tiver SHA-256 diferente de
   `8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9` (indica alteração indevida).
6. A contagem de spots do artefato 4 diferir de 53, ou a lista dos 26 spots divergir de
   `zero_support_classes` do artefato de cobertura de SpotRanking.
7. Aparecer qualquer número de posição, cluster, entropia, JSD, Wasserstein ou contagem de jogador
   sem caminho de artefato de origem e hash, ou que não esteja rotulado `INFERRED`.
8. Algum artefato afirmar selo humano (`APPROVED_BY_USER`, `HUMAN_CAPTURE_IN_GAME`) ou veredito de
   fase sem evidência bruta correspondente.

---

## 6. Labels de verificação

- `AGENT_REVIEWED` — artefatos produzidos e revisados pelo próprio papel analista, com escopo
  conferido contra o dispatch.
- `AUTOMATED_CHECK_PASS` — verificação executada por
  `scratch/2a_int_analyst_generators/verify.py`: parse de 6 JSON, hashes de 8 arquivos, varredura
  binária dos literais proibidos (zero ocorrências), auditoria estrutural de 1671 blocos de status
  (zero violações), contagem de 53 spots e distribuição 30/13/3/2/5 confirmada.
- `NOT_VALIDATED_BY_INDEPENDENT_AUDITOR` — este papel não substitui a auditoria independente
  exigida pelas Regras 07 e 09. Os auditores somente leitura (matemático/estatístico, proveniência,
  adversarial, CS2 domain reviewer) devem revisar os 8 artefatos.
- `NO_HUMAN_APPROVAL_CLAIMED` — nenhum selo humano é reivindicado. O campo
  `HUMAN_LIVE_CALIBRATED` do catálogo é citação de registro pré-existente.
