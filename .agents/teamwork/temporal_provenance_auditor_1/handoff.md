# Relatório de Handoff — Data Provenance and Temporal Auditor (Marco 2B.1 / Fase 3A.3-B)

## 1. Observation

A auditoria forense independente de proveniência de dados e lógica temporal foi executada diretamente contra o disco e artefatos brutos, com as seguintes observações verificadas:

1. **Preservação Estrita do Dataset Piloto**:
   - Caminho físico: `datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet`
   - Hash SHA-256 verificado: `d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe`
   - Tamanho do arquivo: 6.357.366 bytes
   - Total de linhas no arquivo: 577.816 linhas (Train: 189.944, Validation: 207.256, Test: 180.616)
   - Demos por split no arquivo do piloto: 25 Train, 25 Validation, 25 Test (exatamente 75 demos no total)
   - Status catalogado em `datasets/mirage_v2/positioning_v2_full_temporal/pilot_preservation_catalog.json` (SHA-256: `60990c026548a2472fe63edaa1a1aa4a392b9fba6a7f42d37a6bf4472871253e`): `PILOT_SUBSET_25_DEMOS_PER_SPLIT`, `immutable = true`, `preserved_intact = true`.

2. **Splits Canônicos e Exclusão Formal**:
   - Fonte consumida: `datasets/mirage_v2/canonical_temporal_splits_v1.json`
   - Contagens canônicas conferidas:
     - `train_demos`: 311 demos
     - `validation_demos`: 66 demos
     - `test_demos`: 67 demos
     - `total_active_demos`: 444 demos
     - `excluded_demos`: 8 demos
   - Disjunção estrita entre splits de modelagem:
     - `train ∩ validation` = 0 demos (taxa de vazamento: 0,0% — 0/311)
     - `train ∩ test` = 0 demos (taxa de vazamento: 0,0% — 0/311)
     - `validation ∩ test` = 0 demos (taxa de vazamento: 0,0% — 0/66)
   - Exclusão formal documentada em `datasets/mirage_v2/positioning_v2_full_temporal/excluded_demos_manifest.json` (SHA-256: `721a921204c472f1f9278e679c9bc6ade1b5b2f67bdd82a629084fa75b96433f`):
     - Total: 8 demos
     - `status`: `FORMALLY_EXCLUDED`
     - `rejection_code`: `RAW_DEM_WITHOUT_NPZ`
     - Justificativa individual apresentada para as 8 demos (`source_format: RAW_DEM_SOURCE2` sem extração NPZ 16Hz).
   - Inventário em `datasets/mirage_v2/positioning_v2_full_temporal/demo_inventory.json` (SHA-256: `01d68490ff60098c4775b6f94156043c2474cffa10da9deb5743ccb31e4a450f`):
     - Total de registros: exatamente 452 demos (444 aceitas com `accepted: true` + 8 excluídas com `accepted: false` e razão `RAW_DEM_WITHOUT_NPZ`).

3. **Política Única e Idêntica de Janelas e Tratamento de Coordenadas Inválidas**:
   - Parâmetros declarados em `dataset_manifest.json` (SHA-256: `cd7d8ea2435e5b45936d869eb190eb9b0f32b6ee9f1bf45d7bba47cc8f8f6d4c`):
     - `sample_rate_hz`: 16 Hz
     - `sequence_length_frames`: 32 frames
     - `stride_frames`: 16 frames
     - `overlap_percentage`: 50.0%
   - Integridade temporal auditada em todos os 6 shards Parquet (`shard_000.parquet` a `shard_005.parquet`):
     - Comprimento da janela: `window_end_frame - window_start_frame == 31` (32 frames) verificado em 100% das 3.411.434 sequências.
     - Ausência de target leakage intra-janela: `label_frame == window_end_frame` em 100% das sequências auditadas (0 violações de leakage futuro).
     - Coordenadas inválidas [0, 0, 0]: 0 ocorrências encontradas entre as 3.411.434 sequências materializadas nos shards (taxa de rejeição de [0,0,0] no índice aceito: 100,0%).
   - Fechamento da Equação de Conservação por Split (`raw_window_candidates = accepted + rejected + explicitly_masked`):
     - `Train`: 2.947.850 == 2.303.757 (accepted) + 583.358 (rejected) + 60.735 (explicitly_masked) -> **100% FECHADO**.
     - `Validation`: 623.010 == 488.459 (accepted) + 121.576 (rejected) + 12.975 (explicitly_masked) -> **100% FECHADO**.
     - `Test`: 674.670 == 531.163 (accepted) + 129.162 (rejected) + 14.345 (explicitly_masked) -> **100% FECHADO**.

4. **Auditoria Forense de Duplicatas**:
   - Total de sequências materializadas no corpus: 3.411.434 sequências.
   - Total de sequências únicas (`sequence_id`): 3.411.434 sequências.
   - `exact duplicate sequences`: 0 (0,0% — 0/3.411.434).
   - `cross-split duplicates` (`train ∩ val`, `train ∩ test`, `val ∩ test`): 0 sequências compartilhadas entre splits (0,0% — 0/3.411.434).
   - `conflicting labels for same window` `(demo_id, round_id, slot, label_frame)`: 0 conflitos detectados.

5. **Integração e Precedência de Objective e Save**:
   - Fonte original: `datasets/mirage_v2/positioning/objective_save_sequences.parquet`
     - Hash SHA-256: `fe3e902c24d40d2c6e7fd19f375564a2532bf728febfbe5240b6b20636b230ae`
     - Total de janelas candidatas: 7.791 candidatos
   - Contabilidade de integração em `datasets/mirage_v2/positioning_v2_full_temporal/objective_save_integration.json` (SHA-256: `f978a2489f847613f218706456ad65ea3c54845dc7472fbab2a36375e89c35c7`):
     - `candidate_windows` (7.791) == `integrated` (0) + `replaced` (7.659) + `duplicated` (0) + `rejected` (132) + `low_confidence_excluded` (0).
     - Breakdown de rejeições: 114 pertencentes às 8 demos excluídas sem NPZ + 18 com coordenadas inválidas [0, 0, 0]. Total: 132 rejeitados (100% justificados).
   - Verificação nos shards:
     - Total de sequências com `provenance_type == "OBJECTIVE_SAVE_ENRICHED"` nos shards: exatamente 7.659 sequências.
     - Classes de `PositioningState` das sequências enriquecidas: estritamente restritas a `{"OBJECTIVE", "SAVE"}`.
     - Regras de precedência aplicadas: `direct plant/defuse > OBJECTIVE`, `confirmed save evidence > SAVE`, `OBJECTIVE/SAVE > generic HOLD/TRANSIT`.

6. **Relabeling de NextSector com Horizonte Futuro Real**:
   - Contrato canônico: `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json`
   - Parâmetros do horizonte: 128 frames (8,0 segundos a 16 Hz).
   - Metadados em `datasets/mirage_v2/positioning_v2_full_temporal/next_sector_relabeling.json` (SHA-256: `601b88d8ef5ee3d2cc22e980fb6eaa276850a563e7833685e03a14caa6c45b89`):
     - Classes permitidas e observadas: exatamente `{"A", "B", "MID", "CT", "T", "DYNAMIC"}`.
     - Suporte por split: todas as 6 classes possuem suporte real > 0 em Train, Validation e Test (0 classes com suporte zero em qualquer split).
     - Fontes registradas em `next_sector_source`: `FUTURE_VISITED_SECTOR` (457.715), `NO_TRANSITION_DYNAMIC` (2.953.719), `OBJECTIVE_PLANT_DEFUSE` (6.867), `SAVE_FALLBACK` (792).
     - Invariante de transição: 0 ocorrências de setor atual utilizado como rótulo futuro quando não há transição física (todas as sequências sem transição recebem `DYNAMIC` com fonte `NO_TRANSITION_DYNAMIC`).
     - Zero vazamento de targets da Utility AI e zero candidate spots futuros injetados na janela.

7. **Execução Independente das Suítes de Testes**:
   - `pytest tests/test_phase3a3_b_milestone2b1_full_index.py -v`: 20/20 PASS (100%) em 11,30s.
   - `pytest tests/test_phase3a3_b_milestone1_dataloader.py tests/test_phase3a3_b_milestone2b_preflight.py -v`: 28/28 PASS (100%) em 6,48s.
   - `dotnet test`: 340/340 PASS (100%) em 8s (0 falhas, 0 regressões).

## 2. Logic Chain

1. A preservação física do dataset piloto foi comprovada diretamente pelo cálculo do SHA-256 de `positioning_sample_sequences.parquet` (`d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe`), conferência das 577.816 linhas e checagem do status `PILOT_SUBSET_25_DEMOS_PER_SPLIT` em `pilot_preservation_catalog.json`, comprovando a observação 1 e satisfazendo o Requisito 1 de R1.
2. A leitura determinística de `canonical_temporal_splits_v1.json` contra `demo_inventory.json` e `excluded_demos_manifest.json` comprovou a disjunção mútua dos 3 splits ativos de modelagem (311 Train, 66 Validation, 67 Test; interseções = 0) e o isolamento formal das 8 demos `RAW_DEM_WITHOUT_NPZ`, comprovando a observação 2 e satisfazendo o Requisito 2 de R1 e R5.
3. A inspeção dos 6 shards Parquet e a auditoria das equações de reconciliação demonstraram que o comprimento das janelas (32 frames a 16Hz), o stride (16 frames com 50% de overlap) e a relação `label_frame == window_end_frame` são estritamente uniformes entre splits, sem coordenadas [0,0,0] aceitas e com conservação contábil exata (`raw == accepted + rejected + masked`), comprovando a observação 3 e satisfazendo o Requisito R2.
4. A extração exaustiva dos identificadores `sequence_id` em todos os shards confirmou zero duplicatas exatas e zero duplicatas cruzadas entre splits (`train ∩ val = 0`, `train ∩ test = 0`, `val ∩ test = 0`), além de zero inconsistências de rótulos para a mesma chave espaço-temporal `(demo_id, round_id, slot, label_frame)`, comprovando a observação 4 e satisfazendo o Requisito R5.
5. O cruzamento das 7.791 sequências candidatas de `objective_save_sequences.parquet` com o manifesto de integração comprovou o fechamento aritmético exato (7.659 substituídas com precedência plant/defuse > OBJECTIVE e save > SAVE, 114 rejeitadas por demos sem NPZ e 18 rejeitadas por coordenadas [0,0,0]), comprovando a observação 5 e satisfazendo o Requisito R3.
6. A auditoria espacial do relabeling de `NextSector` comprovou que o horizonte futuro real de 128 frames (8s) determina o próximo setor semântico visitado pertencente a {A, B, MID, CT, T, DYNAMIC}, eliminando o uso do setor atual sem transição e garantindo suporte positivo em todas as 6 classes nos 3 splits, comprovando a observação 6 e satisfazendo o Requisito R4.
7. A aprovação verde em 48/48 testes unitários Python e 340/340 testes C# sem executar inferência nem avaliação no split Test consolida a conformidade metodológica e técnica com as regras `01-evidence-before-claims`, `02-no-test-contamination`, `03-zero-support-is-na` e `09-subagent-role-isolation`.

## 3. Caveats

- As 8 demos excluídas formalmente por ausência de extração NPZ (`RAW_DEM_WITHOUT_NPZ`) continuam registradas no catálogo de splits original e no inventário geral com status `accepted: false`. Caso venham a ser extraídas no futuro para formato NPZ 16Hz, elas poderão ser incorporadas a um novo índice versionado (`positioning_v3`) sem violar os contratos vigentes do `positioning_v2`.
- No split Test, em estrita observância da regra `02-no-test-contamination`, a auditoria verificou exclusivamente a conformidade estrutural, integridade de fatias NPZ, ausência de duplicatas e fechamento contábil, sem submeter sequências a forward passes de modelos neurais.

## 4. Conclusion

A entrega do Marco 2B.1 (Fase 3A.3-B) referente à materialização dos índices temporais reais e canônicos de posicionamento em `datasets/mirage_v2/positioning_v2_full_temporal/` está plenamente aprovada em todos os critérios de proveniência de dados, integridade dos tensores NPZ, preservação do piloto anterior, política de janelamento temporal, ausência de duplicatas, integração com precedência de Objective/Save e relabeling de NextSector com horizonte futuro real.

Veredito formal canônico emitido: **`DATA_PROVENANCE_AND_TEMPORAL_AUDIT_PASS`** (`PASS`).

O artefato canônico de auditoria está materializado no disco em:
`training_runs/positioning_v2_real_temporal/data_provenance_temporal_audit.json`

## 5. Verification Method

Para reproduzir deterministicamente e validar de forma independente esta auditoria:

1. **Executar o script canônico de auditoria forense**:
   ```powershell
   python .agents/teamwork/temporal_provenance_auditor_1/run_forensic_audit.py
   ```
   *Critério de aprovação: exit code 0 e emissão do veredito PASS.*

2. **Executar a suíte completa de 20 testes unitários do Marco 2B.1**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b1_full_index.py -v
   ```
   *Critério de aprovação: 20 passed em ~11 segundos.*

3. **Executar os testes de preflight e dataloader temporal**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone1_dataloader.py tests/test_phase3a3_b_milestone2b_preflight.py -v
   ```
   *Critério de aprovação: 28 passed em ~7 segundos.*

4. **Executar a suíte de testes C# do projeto**:
   ```powershell
   dotnet test
   ```
   *Critério de aprovação: 340 passed, 0 com falha.*

5. **Inspecionar o relatório JSON de evidências**:
   Verificar `training_runs/positioning_v2_real_temporal/data_provenance_temporal_audit.json` e conferir os hashes SHA-256 calculados para os 12 artefatos do dataset.
