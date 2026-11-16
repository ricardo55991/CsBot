# Relatório de Handoff — Dataset Index Implementer (Marco 2B.1 / Fase 3A.3-B)

## 1. Observation
- **Dataset Piloto Preservado Intacto**:
  - Caminho: `datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet`
  - Tamanho: 6.357.366 bytes
  - Hash SHA-256 verificado: `d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe`
  - Linhas: 577.816 linhas (Train: 189.944, Validation: 207.256, Test: 180.616; exatamente 25 demos por split, totalizando 75 demos)
  - Catalogado formalmente com status `PILOT_SUBSET_25_DEMOS_PER_SPLIT` em `datasets/mirage_v2/positioning_v2_full_temporal/pilot_preservation_catalog.json` (SHA-256: `60990c026548a2472fe63edaa1a1aa4a392b9fba6a7f42d37a6bf4472871253e`).
- **Splits Canônicos e Exclusão Formal**:
  - Fonte canônica consumida: `datasets/mirage_v2/canonical_temporal_splits_v1.json`
  - Total de demos ativas processadas: 444 demos (Train = 311, Validation = 66, Test = 67). Zero demos omitidas, zero truncamentos manuais.
  - Demos excluídas formalmente: 8 demos com status `RAW_DEM_WITHOUT_NPZ` (`charrados-vs-alka-m2-mirage`, `depo-vs-winners-m2-mirage`, `ding-cuts-vs-abyssal-m1-mirage`, `dnk-vs-winners-m1-mirage`, `mibr-academy-vs-bestia-academy-m2-mirage-p2`, `mouz-nxt-vs-ursa-m2-mirage`, `regain-vs-zomblers-m1-mirage`, `tnc-vs-phantom-academy-m1-mirage`), documentadas individualmente em `datasets/mirage_v2/positioning_v2_full_temporal/excluded_demos_manifest.json` (SHA-256: `721a921204c472f1f9278e679c9bc6ade1b5b2f67bdd82a629084fa75b96433f`).
  - Total no inventário `demo_inventory.json`: exatamente 452 demos (444 aceitas + 8 excluídas).
- **Materialização dos Shards Parquet**:
  - Diretório de produção: `datasets/mirage_v2/positioning_v2_full_temporal/`
  - Total de sequências no índice integral: 3.411.434 sequências distribuídas em 6 shards:
    - `shard_000.parquet`: 568.573 linhas, 9.837.613 bytes, SHA-256 `39ebbe19d9782ffba743d968517b8624530af2daa9375ece6ba742d648c6bebb`
    - `shard_001.parquet`: 568.573 linhas, 9.814.687 bytes, SHA-256 `f849f724a67338c1d0158f6c407e615e6a9fa5d1faa675779eb1d8125ad27e6a`
    - `shard_002.parquet`: 568.573 linhas, 9.840.915 bytes, SHA-256 `619e0416f779ba6a9aedeb6b34d380469e72e89557bf7c67eff5cfafaaab8d5a`
    - `shard_003.parquet`: 568.573 linhas, 9.811.017 bytes, SHA-256 `546f0df72594e80b5bc8780be17b06ed2876a38bbccbc367adfdee776d2f0612`
    - `shard_004.parquet`: 568.573 linhas, 9.852.670 bytes, SHA-256 `a79d189b18ad1f7cc71d6ead3f4528cde3371d10cbea81193cb7f1337a1a7166`
    - `shard_005.parquet`: 568.569 linhas, 9.769.907 bytes, SHA-256 `7aec90a0b5d40570b0aee2a52e9080cc802486f7955686b68453c2c093d10b70`
  - Todos os 21 campos canônicos mínimos presentes: `sequence_id`, `demo_id`, `match_id`, `round_id`, `player_id`, `slot`, `split`, `window_start_frame`, `window_end_frame`, `label_frame`, `npz_path`, `PositioningState`, `ObjectiveSubtype`, `SaveSubtype`, `NextSector`, `CandidateSpotId`, `SpotLossMask`, `Transition`, `ExitTrigger`, `confidence`, `provenance_type` e `next_sector_source` (além de aliases snake_case para backward-compatibility).
- **Contabilidade Integral de Janelas (Equação de Conservação)**:
  - `Train`: Raw Candidates = 2.947.850 | Accepted = 2.303.757 | Explicitly Masked = 60.735 | Rejected = 583.358 (583.358 = 579.522 dead + 3.836 invalid coords) -> `2.947.850 == 2.303.757 + 60.735 + 583.358` (100% FECHADO).
  - `Validation`: Raw Candidates = 623.010 | Accepted = 488.459 | Explicitly Masked = 12.975 | Rejected = 121.576 (120.768 dead + 808 invalid coords) -> `623.010 == 488.459 + 12.975 + 121.576` (100% FECHADO).
  - `Test`: Raw Candidates = 674.670 | Accepted = 531.163 | Explicitly Masked = 14.345 | Rejected = 129.162 (128.324 dead + 838 invalid coords) -> `674.670 == 531.163 + 14.345 + 129.162` (100% FECHADO).
- **Integração de Objective e Save**:
  - Fonte consumida: `datasets/mirage_v2/positioning/objective_save_sequences.parquet` (7.791 candidatos, SHA-256 `fe3e902c24d40d2c6e7fd19f375564a2532bf728febfbe5240b6b20636b230ae`)
  - Fechamento: `7.791 == 0 (integrated) + 7.659 (replaced) + 0 (duplicated) + 132 (rejected: 114 demos excluídas + 18 coords [0,0,0]) + 0 (low_confidence_excluded)`.
  - Regras de precedência aplicadas deterministicamente: direct plant/defuse > OBJECTIVE, confirmed save > SAVE, OBJECTIVE/SAVE > generic HOLD/TRANSIT.
- **Relabeling de NextSector com Horizonte Real**:
  - Horizonte congelado: 128 frames (8.0s a 16Hz).
  - Classes restritas a {A, B, MID, CT, T, DYNAMIC}.
  - Todas as 6 classes ativas com suporte real em todos os splits. Nenhuma classe com suporte zero.
  - Zero ocorrências de setor atual como futuro quando não há transição (classificado canonicamente como DYNAMIC com fonte NO_TRANSITION_DYNAMIC).
  - Zero dependência de target de Utility AI ou candidate spots futuros.
- **Auditoria de Duplicatas**:
  - `exact duplicate sequences` = 0
  - `cross-split duplicates` = 0 (Train, Validation e Test estritamente disjuntos)
  - `conflicting labels for same window` = 0
- **Execução dos Testes**:
  - `pytest tests/test_phase3a3_b_milestone2b1_full_index.py`: 20/20 PASS (100%).
  - `pytest tests/test_phase3a3_b_milestone1_dataloader.py`: 8/8 PASS (100%).
  - `pytest tests/test_phase3a3_b_milestone2b_preflight.py`: 20/20 PASS (100%).
  - `dotnet test`: 340/340 PASS (100%).

## 2. Logic Chain
1. A partir da conferência direta no disco (`d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe`), o dataset piloto foi confirmado intacto com 577.816 linhas e catalogado como imutável, atendendo ao Requisito 1.
2. A leitura exaustiva de `canonical_temporal_splits_v1.json` identificou 311 demos em Train, 66 em Validation, 67 em Test e 8 em excluded_demos. O pipeline iterou determinística e exclusivamente sobre as 444 demos ativas, isolando as 8 demos sem extração NPZ no manifesto de exclusão formal com razão `RAW_DEM_WITHOUT_NPZ`, atendendo ao Requisito 2.
3. Para cada demo, os limites de round foram detectados via resets de `round_time_norm` (diff > 0.15) e a política de janelas (16Hz, 32 frames, stride 16, overlap 50%) foi aplicada uniformemente. Jogadores mortos e coordenadas `[0, 0, 0]` foram filtrados, e o mascaramento de padding para k < 32 frames foi registrado na contabilidade como `explicitly_masked`, fechando aritmeticamente a equação de conservação `raw = accepted + masked + rejected` em todos os splits, atendendo ao Requisito 3 e 7.
4. Para NextSector, a vetorização espacial projetou a trajetória futura de cada jogador em até 128 frames. Ao detectar transição física para outro setor, a label foi gravada como o setor visitado; na ausência de transição, a label foi preenchida com `DYNAMIC` e fonte `NO_TRANSITION_DYNAMIC`, garantindo que o setor atual nunca seja atribuído sem deslocamento, atendendo ao Requisito 6.
5. As 7.791 sequências de `objective_save_sequences.parquet` foram integradas com regras de precedência (plant/defuse > OBJECTIVE, save > SAVE) com 7.659 substituições aprovadas e 132 rejeições justificadas (114 demos excluídas sem NPZ e 18 coordenadas [0,0,0]), fechando a equação de integração sem resíduos, atendendo ao Requisito 5.
6. Os registros foram particionados uniformemente em 6 shards Parquet de ~568.570 linhas (~9,8 MB cada), contendo os 21 campos canônicos sem tensores densos duplicados, acompanhados dos 6 companion JSONs no diretório `datasets/mirage_v2/positioning_v2_full_temporal/` e 5 artefatos de suporte em `training_runs/positioning_v2_real_temporal/`, atendendo ao Requisito 4, 8 e 10.
7. A validação via suíte de testes unitários (`test_phase3a3_b_milestone2b1_full_index.py`) e suíte C# confirmou 100% de conformidade técnica e metodológica com zero inferências de modelo no Test set, atendendo aos Requisitos 9 e 11.

## 3. Caveats
- O veredito de representatividade distribucional do dataset piloto em relação ao corpus integral foi classificado como `NON_REPRESENTATIVE` (divergência média de Jensen-Shannon = 0.2691), impulsionado primordialmente pela cabeça `NextSector` (JSD = 0.8117), decorrente do fato de que o piloto possuía 99,63% de instâncias MID devido ao viés de extração antigo na base TR, enquanto o índice completo corrigiu esse viés distribuindo as 6 classes de forma realista. Conforme os critérios do protocolo, essa divergência não invalida o piloto retroativamente, mas fundamenta a necessidade do índice integral para o treinamento canônico.
- No split Test, nenhum forward pass de modelo neural foi executado (apenas validação determinística de integridade de fatias NPZ pelo DataLoader), em estrito cumprimento da regra `02-no-test-contamination`.

## 4. Conclusion
O índice temporal canônico de posicionamento para o corpus completo de Mirage v2 está plenamente materializado no disco em `datasets/mirage_v2/positioning_v2_full_temporal/`, cobrindo 3.411.434 sequências distribuídas em 6 shards Parquet e 6 companion JSONs versionados. Todos os requisitos de proveniência, disjunção de splits, fechamento contábil, relabeling de NextSector e integração de Objective/Save foram atendidos sem violações de integridade e com aprovação em 20/20 testes unitários e 340/340 testes C#. O dataset está pronto para auditoria independente.

## 5. Verification Method
Para reproduzir e verificar independentemente a entrega:
1. **Executar a suíte completa de testes de governança do Marco 2B.1**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b1_full_index.py -v
   ```
   *Condição de invalidação: qualquer falha entre os 20 testes unitários.*
2. **Executar a suíte de testes C# do projeto**:
   ```powershell
   dotnet test
   ```
   *Condição de invalidação: qualquer regressão nos 340 testes C#.*
3. **Verificar os hashes físicos e existência dos 12 artefatos do dataset**:
   Inspecionar `datasets/mirage_v2/positioning_v2_full_temporal/` e calcular os hashes SHA-256 de 64 caracteres contra os valores declarados em `dataset_manifest.json`.
4. **Verificar o fechamento contábil e isolamento de splits**:
   Inspecionar `datasets/mirage_v2/positioning_v2_full_temporal/dataset_manifest.json`, `demo_inventory.json` e `objective_save_integration.json`.
