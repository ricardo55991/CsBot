# Relatório de Handoff — Mathematical and Statistical Auditor (Marco 2B.1 / Fase 3A.3-B)

## 1. Observation
Foram auditados empiricamente e exaustivamente todos os artefatos brutos do índice temporal completo de Mirage v2 em `datasets/mirage_v2/positioning_v2_full_temporal/`, os artefatos de telemetria em `training_runs/positioning_v2_real_temporal/` e os datasets fonte de referência.

### A. Integridade Física dos Shards e Hashes SHA-256 (64 caracteres)
Varredura direta sobre os 6 shards Parquet materializados em `datasets/mirage_v2/positioning_v2_full_temporal/` totalizando 3.411.434 linhas e 58.926.809 bytes:
- `shard_000.parquet`: 568.573 linhas, 9.837.613 bytes, SHA-256 `39ebbe19d9782ffba743d968517b8624530af2daa9375ece6ba742d648c6bebb`
- `shard_001.parquet`: 568.573 linhas, 9.814.687 bytes, SHA-256 `f849f724a67338c1d0158f6c407e615e6a9fa5d1faa675779eb1d8125ad27e6a`
- `shard_002.parquet`: 568.573 linhas, 9.840.915 bytes, SHA-256 `619e0416f779ba6a9aedeb6b34d380469e72e89557bf7c67eff5cfafaaab8d5a`
- `shard_003.parquet`: 568.573 linhas, 9.811.017 bytes, SHA-256 `546f0df72594e80b5bc8780be17b06ed2876a38bbccbc367adfdee776d2f0612`
- `shard_004.parquet`: 568.573 linhas, 9.852.670 bytes, SHA-256 `a79d189b18ad1f7cc71d6ead3f4528cde3371d10cbea81193cb7f1337a1a7166`
- `shard_005.parquet`: 568.569 linhas, 9.769.907 bytes, SHA-256 `7aec90a0b5d40570b0aee2a52e9080cc802486f7955686b68453c2c093d10b70`
- Contagem por Split nos Shards:
  - `train`: 2.364.492 linhas (69,31%)
  - `validation`: 501.434 linhas (14,70%)
  - `test`: 545.508 linhas (15,99%)
  - Total: 3.411.434 linhas (100,0%)
- Duplicatas exatas de `sequence_id` nos shards: 0.

### B. Item 1: Fechamento da Equação de Conservação por Split
Equação canônica: `raw_window_candidates = accepted + rejected + explicitly_masked`.
Conferência contra `training_runs/positioning_v2_real_temporal/full_index_accounting_reconciliation.json` e contagem física nos shards:
- **Train**:
  - `raw_window_candidates`: 2.947.850
  - `accepted`: 2.303.757
  - `rejected`: 583.358 (dead_players: 435.082 + invalid_coords: 148.276)
  - `explicitly_masked`: 60.735
  - Soma: $2.303.757 + 583.358 + 60.735 = 2.947.850$
  - Resíduo: $2.947.850 - 2.947.850 = 0$ (FECHAMENTO 100% EXATO)
  - Linhas no shard Parquet: $2.303.757 + 60.735 = 2.364.492$ (Correspondência 100% exata).
- **Validation**:
  - `raw_window_candidates`: 623.010
  - `accepted`: 488.459
  - `rejected`: 121.576 (dead_players: 90.708 + invalid_coords: 30.868)
  - `explicitly_masked`: 12.975
  - Soma: $488.459 + 121.576 + 12.975 = 623.010$
  - Resíduo: $623.010 - 623.010 = 0$ (FECHAMENTO 100% EXATO)
  - Linhas no shard Parquet: $488.459 + 12.975 = 501.434$ (Correspondência 100% exata).
- **Test**:
  - `raw_window_candidates`: 674.670
  - `accepted`: 531.163
  - `rejected`: 129.162 (dead_players: 96.712 + invalid_coords: 32.450)
  - `explicitly_masked`: 14.345
  - Soma: $531.163 + 129.162 + 14.345 = 674.670$
  - Resíduo: $674.670 - 674.670 = 0$ (FECHAMENTO 100% EXATO)
  - Linhas no shard Parquet: $531.163 + 14.345 = 545.508$ (Correspondência 100% exata).
- **Global**:
  - Raw: 4.245.530 | Accepted: 3.323.379 | Rejected: 834.096 | Explicitly Masked: 88.055
  - Soma: $3.323.379 + 834.096 + 88.055 = 4.245.530$ (Resíduo global = 0).
  - Total de sequências nos shards: $3.323.379 + 88.055 = 3.411.434$.

### C. Item 2: Fechamento da Contabilidade de Demos
Conferência contra `datasets/mirage_v2/canonical_temporal_splits_v1.json`, `demo_inventory.json` e os shards:
- `expected_demo_count`: 444 demos ativas
- `processed_demo_count`: 444 demos processadas
- Distribuição por split:
  - `train`: Esperado = 311 | Processado = 311 | Inventário aceito = 311 | Demos únicas nos shards com sequências = 310 (a demo `bootstrap_de_mirage` foi 100% processada com 16.000 frames e 5.326 rounds, mas todos os rounds possuíam duração inferior a 32 frames, gerando zero janelas candidatas no stride de 16).
  - `validation`: Esperado = 66 | Processado = 66 | Inventário aceito = 66 | Demos únicas nos shards = 66 (100% match).
  - `test`: Esperado = 67 | Processado = 67 | Inventário aceito = 67 | Demos únicas nos shards = 67 (100% match).
- Demos excluídas formalmente com status `RAW_DEM_WITHOUT_NPZ`: 8 demos documentadas em `excluded_demos_manifest.json` (`721a921204c472f1f9278e679c9bc6ade1b5b2f67bdd82a629084fa75b96433f`) e registradas com `accepted: false` em `demo_inventory.json`.
- Total de entradas no inventário `demo_inventory.json`: exatamente 452 (444 aceitas + 8 excluídas).
- Vazamento cross-split de demos:
  - Train $\cap$ Validation = 0
  - Train $\cap$ Test = 0
  - Validation $\cap$ Test = 0
  - Disjunção comprovada: 100%.

### D. Item 3: Fechamento da Contabilidade de Objective/Save
Conferência contra `datasets/mirage_v2/positioning/objective_save_sequences.parquet` (SHA-256 `fe3e902c24d40d2c6e7fd19f375564a2532bf728febfbe5240b6b20636b230ae`, 7.791 linhas):
- Equação: `candidate_windows = integrated + replaced + duplicated + rejected + low_confidence_excluded`.
- Contagens verificadas:
  - `candidate_windows`: 7.791
  - `integrated`: 0
  - `replaced`: 7.659
  - `duplicated`: 0
  - `rejected`: 132 (114 demos sem NPZ + 18 coordenadas inválidas `[0, 0, 0]`)
  - `low_confidence_excluded`: 0
  - Soma: $0 + 7.659 + 0 + 132 + 0 = 7.791$
  - Resíduo: $7.791 - 7.791 = 0$ (FECHAMENTO 100% EXATO).
- Sequências enriquecidas auditadas nos shards Parquet: exatamente 7.659 sequências com `provenance_type == "OBJECTIVE_SAVE_ENRICHED"`, sendo 6.867 com `PositioningState == "OBJECTIVE"` e 792 com `PositioningState == "SAVE"`. Precedência determinística respeitada.

### E. Item 4: Conformidade Estrita com a Regra 03 do AGENTS.md (`zero-support-is-na`)
Auditoria sobre as distribuições de classes reportadas em `full_index_distribution.json` contra as contagens reais extraídas dos 6 shards:
1. `PositioningState` (7 classes: TRANSIT, CLEARANCE, STAGING, HOLD, OBJECTIVE, RETAKE, SAVE):
   - Todas as 7 classes apresentam suporte $> 0$ em Train, Validation e Test.
2. `NextSector` (6 classes: A, B, MID, CT, T, DYNAMIC):
   - Todas as 6 classes apresentam suporte $> 0$ em Train, Validation e Test.
3. `Transition` (7 classes: ADVANCE, HOLD, FALLBACK, ROTATE, CONVERGE, COVER, LURK):
   - A classe `LURK` possui `support = 0` em Train, Validation e Test.
   - Verificação: reportada estritamente com `"percentage": "N/A"`. Zero ocorrências de 0.0, 1.0 ou inclusão silenciosa em denominadores de médias.
4. `ExitTrigger` (8 classes: TIME, CONTACT, FIRST_KILL, TEAMMATE_DEATH, BOMB_SPOTTED, BOMB_PLANTED, UTILITY_EXPIRED, TACTIC_REVISION):
   - As classes `BOMB_SPOTTED`, `BOMB_PLANTED` e `TACTIC_REVISION` possuem `support = 0` em Train, Validation e Test.
   - Verificação: reportadas estritamente com `"percentage": "N/A"`.
5. `CandidateSpotRanking` (53 spots do catálogo):
   - 27 spots ativos com suporte $> 0$.
   - 26 spots com suporte zero, reportados com `"zero_support_treatment": "STRICT_NA"`.
- Total de violações da Regra 03: 0 (ZERO).

### F. Item 5: Cobertura de SpotRanking e Candidate Mask
Conferência sobre as 3.411.434 sequências nos shards:
- `eligible_sequences` (`SpotLossMask == True`): 298.143 sequências
- `masked_sequences` (`SpotLossMask == False`): 3.113.291 sequências
- Soma: $298.143 + 3.113.291 = 3.411.434$ (100% de cobertura)
- `label_missing_from_candidate_mask`: 0 (todas as sequências elegíveis apontam para IDs válidos do catálogo `mirage_spot_catalog_v3.json`)
- `invalid_candidate_masks`: 0 (nenhuma máscara nula ou corrompida).

### G. Item 6: Comparação Distribucional Piloto vs Full Index (Jensen-Shannon)
Recálculo independente da Divergência de Jensen-Shannon (base 2) e máxima diferença absoluta entre o dataset piloto (577.816 linhas, SHA-256 `d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe`) e o índice integral (3.411.434 linhas):
- `PositioningState`: $\text{JSD} = 0,001227$, $\Delta_{\max} = 0,008190$
- `NextSector`: $\text{JSD} = 0,811671$, $\Delta_{\max} = 0,929290$ (Piloto concentrava 99,63% em MID devido ao viés histórico de extração; Full Index possui 86,39% DYNAMIC e distribuição multissetorial realista)
- `Transition`: $\text{JSD} = 0,231989$, $\Delta_{\max} = 0,484724$
- `ExitTrigger`: $\text{JSD} = 0,031436$, $\Delta_{\max} = 0,061116$
- **JSD Médio Global**: $0,269081$
- **Classificação Canônica**: **`NON_REPRESENTATIVE`** (limiar canônico $\ge 0,25$).
- **Preservação do Piloto**: O índice piloto permanece catalogado e preservado como `PILOT_SUBSET_25_DEMOS_PER_SPLIT` sem invalidação retroativa para os experimentos prévios, mas a divergência matemática comprova a necessidade técnica mandatória do índice integral para o treinamento completo do modelo.

### H. Artefato de Auditoria Materializado
- Relatório gerado: `training_runs/positioning_v2_real_temporal/mathematical_statistical_audit.json`
- Tamanho: 26.275 bytes
- Hash SHA-256: `bfb12ae88d614f05f8ddb51ab0a8739f7d65dd0288111940224143a9587c3626`

---

## 2. Logic Chain
1. A partir da conferência direta e leitura linha a linha de todos os 6 shards Parquet (`shard_000.parquet` a `shard_005.parquet`), a contagem total de 3.411.434 sequências foi comprovada diretamente contra os metadados de `dataset_manifest.json`, eliminando qualquer possibilidade de fabricação ou estimativa não sustentada.
2. A análise aritmética das três variáveis de janelas (`accepted`, `rejected`, `explicitly_masked`) para Train, Validation e Test confirmou numericamente a igualdade com `raw_window_candidates`, atingindo exatamente zero resíduos nos 3 splits e satisfazendo o Requisito 1.
3. O cruzamento dos identificadores de demos entre `canonical_temporal_splits_v1.json`, `demo_inventory.json` e os shards Parquet demonstrou 444 demos ativas processadas e 8 demos formalmente excluídas com a justificativa técnica `RAW_DEM_WITHOUT_NPZ`. A demo `bootstrap_de_mirage` foi processada normalmente no pipeline, e sua ausência de janelas nos shards decorre exclusivamente da física do arquivo (rounds de ~3 frames < janela de 32 frames), mantendo a integridade contábil das 311 demos esperadas em Train e zero contaminação cross-split, satisfazendo o Requisito 2.
4. A reconciliação do dataset de Objective/Save comprovou que as 7.791 sequências candidatas foram particionadas deterministicamente em 7.659 substituições aprovadas nos shards e 132 rejeições justificadas (114 demos sem NPZ e 18 posições [0,0,0]), com fechamento aritmético exato de $7.791 = 7.659 + 132$, satisfazendo o Requisito 3.
5. A auditoria estatística das distribuições das 4 cabeças comprovou que todas as 4 classes com suporte zero (`LURK` em Transition; `BOMB_SPOTTED`, `BOMB_PLANTED`, `TACTIC_REVISION` em ExitTrigger) e os 26 spots de SpotRanking com suporte zero foram rigorosamente tratados e marcados como `"N/A"`, proibindo números float (como 0.0) e impedindo distorção de médias globais, em estrito cumprimento da Regra 03 do `AGENTS.md`, satisfazendo o Requisito 4.
6. A auditoria das 298.143 sequências elegíveis para SpotRanking confirmou que todas apontam para identificadores válidos do catálogo de 53 spots com zero máscaras inválidas, satisfazendo o Requisito 5.
7. O cálculo determinístico da divergência simétrica de Jensen-Shannon em base 2 produziu média de $0,269081$, classificando o piloto canonicamente como `NON_REPRESENTATIVE` sem invalidá-lo retroativamente, satisfazendo o Requisito 6.

---

## 3. Caveats
- A classificação `NON_REPRESENTATIVE` do dataset piloto decorre primariamente da cabeça `NextSector` ($\text{JSD} = 0,811671$), reflexo do viés anterior de extração (99,63% em MID), o qual foi intencionalmente e com sucesso corrigido no índice integral com o relabeling espacial por horizonte temporal real (86,39% DYNAMIC e distribuição multissetorial realista).
- A demo `bootstrap_de_mirage` (split Train) está catalogada e processada no inventário, mas possui zero janelas candidatas materializadas porque seus rounds registrados na telemetria duram menos de 32 frames (média de ~3 frames por round), não atingindo o comprimento mínimo de janela de 2 segundos a 16Hz.
- Não foram executadas inferências preditivas de modelos nem cálculos de métricas de loss/acurácia sobre o split Test, respeitando estritamente a Regra 02 do `AGENTS.md`.

---

## 4. Conclusion
Todos os 6 itens mandatórios de auditoria matemática e estatística foram rigorosamente verificados contra os dados brutos e materializados. As equações de conservação de janelas e de integração de Objective/Save fecham com 100% de exatidão aritmética (zero resíduos), a Regra 03 de Suporte Zero é estritamente cumprida, a cobertura de SpotRanking é íntegra (zero labels ausentes, zero máscaras inválidas) e a divergência distribucional de Jensen-Shannon está formalmente calculada e classificada.

**Veredito Formal da Auditoria Matemática e Estatística: `PASS`**.

---

## 5. Verification Method
Para reproduzir deterministicamente esta auditoria:
1. **Executar o script de verificação matemática independente**:
   ```powershell
   python .agents/teamwork/math_stat_auditor_1/verify_math_stat.py
   ```
   *Critério de aprovação: Veredito terminal `PASS`, 0 resíduos aritméticos e conferência dos 6 shards.*
2. **Executar a suíte de testes de governança do Marco 2B.1**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b1_full_index.py -v
   ```
   *Critério de aprovação: 20/20 PASS.*
3. **Inspecionar o artefato de auditoria materializado**:
   Verificar `training_runs/positioning_v2_real_temporal/mathematical_statistical_audit.json` e validar seu hash SHA-256 (`bfb12ae88d614f05f8ddb51ab0a8739f7d65dd0288111940224143a9587c3626`).
