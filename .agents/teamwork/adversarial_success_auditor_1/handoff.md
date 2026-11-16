# Relatório Canônico de Handoff — Adversarial Success Auditor (Marco 2B.1)

- **Agente**: `adversarial_success_auditor_1`
- **Papel**: `teamwork_auditor` / `forensic_auditor` (somente-leitura)
- **Fase**: `FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER`
- **Marco**: `Marco 2B.1 — Materialização e Governança do Índice Temporal Completo (3.411.434 sequências)`
- **Data/Hora**: `2026-11-08T17:45:00Z`
- **Veredito Canônico**: `FULL_TEMPORAL_INDEX_READY_FOR_FULL_TRAINING`

---

## 1. Observation

1. **Gates Determinísticos do DataLoader sob Seed 42026**:
   - Comando executado: `python .agents/teamwork/adversarial_success_auditor_1/independent_dataloader_audit.py`
   - Amostras avaliadas: 1.000 janelas (500 Train, 250 Validation, 250 Test) diretamente contra os arrays brutos `.npz` em `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\`.
   - Resultados empíricos verificados:
     - `ToleranceMatchRate = 1.0` (100.0%, 1.000 / 1.000 sob atol=$10^{-5}$)
     - `SyntheticWindowRate = 0.0` (0.0%, 0 / 1.000)
     - `TeammateRealSlotMatchRate = 1.0` (100.0%, 1.000 / 1.000)
     - `UnmaskedPaddingRate = 0.0` (0.0%, 0 / 1.000)
     - `RoundBoundaryViolationRate = 0.0` (0.0%, 0 / 1.000)
     - `CrossPlayerWindowRate = 0.0` (0.0%, 0 / 1.000)
     - `FutureLeakageRate = 0.0` (0.0%, 0 / 1.000)
     - `MissingNpZRate = 0.0` (0.0%, 0 / 1.000)
     - `ExactDuplicateWindowRate = 0.0` (0.0%, 0 / 1.000)
     - `TestSplitModelInferenceCount = 0` (Zero forward passes de modelo neural no split Test)
   - Veredito dos Gates: `ALL_GATES_PASSED_100_PERCENT`.

2. **Suíte Canônica de Testes de Governança (20/20 PASS)**:
   - Comando executado: `pytest tests/test_phase3a3_b_milestone2b1_full_index.py -v`
   - Saída: `============================= 20 passed in 15.60s =============================`
   - Todos os 20 testes unitários obrigatórios (preservação do piloto, splits, exclusão de 8 demos, invariância de janelamento, ausência de tensores densos, 21 campos canônicos, rejeição de [0,0,0], integração de Objective/Save, fechamento contábil, NextSector, duplicatas zero, isolamento do teste e cobertura de SpotRanking) passaram com 100% de aprovação.

3. **Suíte de Testes de Regressão do DataLoader e Preflight (28/28 PASS)**:
   - Comando executado: `pytest tests/test_phase3a3_b_milestone1_dataloader.py tests/test_phase3a3_b_milestone2b_preflight.py -v`
   - Saída: `============================= 28 passed in 10.17s =============================`
   - Zero regressões em toda a cadeia de dados e preflight.

4. **Suíte de Compilação e Testes C# do CsBot (340/340 PASS)**:
   - Comando executado: `dotnet test`
   - Saída: `Aprovado! – Com falha: 0, Aprovado: 340, Ignorado: 0, Total: 340, Duração: 8 s - CsBotManager.Tests.dll (net10.0)`
   - 100% verde sem advertências nem quebras de contrato.

5. **Auditoria Física e Hashes SHA-256 de 64 Caracteres dos 20 Entregáveis**:
   - Todos os 20 arquivos existem fisicamente no disco com tamanho > 0 bytes:
     - 12 artefatos em `datasets/mirage_v2/positioning_v2_full_temporal/`:
       - `shard_000.parquet`: 9.837.613 bytes, SHA-256: `39ebbe19d9782ffba743d968517b8624530af2daa9375ece6ba742d648c6bebb`
       - `shard_001.parquet`: 9.814.687 bytes, SHA-256: `f849f724a67338c1d0158f6c407e615e6a9fa5d1faa675779eb1d8125ad27e6a`
       - `shard_002.parquet`: 9.840.915 bytes, SHA-256: `619e0416f779ba6a9aedeb6b34d380469e72e89557bf7c67eff5cfafaaab8d5a`
       - `shard_003.parquet`: 9.811.017 bytes, SHA-256: `546f0df72594e80b5bc8780be17b06ed2876a38bbccbc367adfdee776d2f0612`
       - `shard_004.parquet`: 9.852.670 bytes, SHA-256: `a79d189b18ad1f7cc71d6ead3f4528cde3371d10cbea81193cb7f1337a1a7166`
       - `shard_005.parquet`: 9.769.907 bytes, SHA-256: `7aec90a0b5d40570b0aee2a52e9080cc802486f7955686b68453c2c093d10b70`
       - `dataset_manifest.json`: 2.670 bytes, SHA-256: `cd7d8ea2435e5b45936d869eb190eb9b0f32b6ee9f1bf45d7bba47cc8f8f6d4c`
       - `demo_inventory.json`: 206.964 bytes, SHA-256: `01d68490ff60098c4775b6f94156043c2474cffa10da9deb5743ccb31e4a450f`
       - `excluded_demos_manifest.json`: 4.125 bytes, SHA-256: `721a921204c472f1f9278e679c9bc6ade1b5b2f67bdd82a629084fa75b96433f`
       - `next_sector_relabeling.json`: 1.482 bytes, SHA-256: `601b88d8ef5ee3d2cc22e980fb6eaa276850a563e7833685e03a14caa6c45b89`
       - `objective_save_integration.json`: 6.996 bytes, SHA-256: `f978a2489f847613f218706456ad65ea3c54845dc7472fbab2a36375e89c35c7`
       - `pilot_preservation_catalog.json`: 659 bytes, SHA-256: `60990c026548a2472fe63edaa1a1aa4a392b9fba6a7f42d37a6bf4472871253e`
     - 8 artefatos em `training_runs/positioning_v2_real_temporal/`:
       - `full_index_accounting_reconciliation.json`: 1.169 bytes, SHA-256: `43ee5e23894180539bc4c4482148fbb583e918e8859acb9851a2443e0ad8871a`
       - `full_index_distribution.json`: 8.515 bytes, SHA-256: `0ffb0a5b91339c5159d65b59c70b725bc209991e405dd4a32a5ff7cc232f5f2a`
       - `full_index_jensen_shannon_divergence.json`: 2.578 bytes, SHA-256: `cf46f84a77ee95a41c89abe5cec66fadf49f0c42b7e6fd77b83c3d17bcad4aae`
       - `full_index_spot_ranking_coverage.json`: 1.300 bytes, SHA-256: `3b67b40087b683d73237c02a9c21bbb84f11d415809d2b486da759a7b203ab01`
       - `full_index_dataloader_gates.json`: 663 bytes, SHA-256: `7bef3c9b44aba7ae789e85a996a5bc4341f20b0f3e5de96fc177c390e33c8d76`
       - `data_provenance_temporal_audit.json`: 12.596 bytes, SHA-256: `84ceeaa8ba35d92850b9dda85b6783ce59203505e09acd1fda2832b2ae16d3d1`
       - `adversarial_success_audit.json`: 11.894 bytes, SHA-256: `fd0b9f99da5089887e86422cc3413ec1a50faa5475fb81dd0aeeda06ee4bf0ad`
       - `marco_2b1_final_report.md`: 26.179 bytes, SHA-256: `2ba12d27e571074526ffa4937582b80db416d3499d18b4580219b311ded57c56`

6. **Descoberta e Documentação Forense sobre `bootstrap_de_mirage`**:
   - A demo `bootstrap_de_mirage` (Train) consta com 16.000 frames e 5.326 micro-rounds artificiais de inicialização (duração média ~3 frames, todos com $\text{round\_len} < 32$), o que resultou legitimamente em 0 janelas aceitas nos shards, sem impactar o fechamento contábil nem a reconciliação dos 311 arquivos de Train processados em `demo_inventory.json` e `full_index_accounting_reconciliation.json`.

---

## 2. Logic Chain

1. A partir da verificação física no disco (item 5 da observação), o dataset piloto original encontra-se intacto com hash `d505fd5a88ffb91cf5039a76a322fc970a55a7c4fb35c9c349efa783df1709fe` e catalogado sob status `PILOT_SUBSET_25_DEMOS_PER_SPLIT`, satisfazendo integralmente ao Requisito 1 de preservação.
2. A leitura de `canonical_temporal_splits_v1.json` e do inventário físico confirmou que todas as 444 demos ativas (311 Train, 66 Validation, 67 Test) foram processadas, e as 8 demos sem NPZ foram formalmente excluídas e justificadas sob código `RAW_DEM_WITHOUT_NPZ`, satisfazendo aos Requisitos 1 e 2.
3. A auditoria contábil demonstrou que a equação de conservação `raw = accepted + masked + rejected` fecha com exatidão matemática absoluta em todos os splits (4.245.530 candidatos brutos = 3.323.379 aceitas + 88.055 mascaradas + 834.096 rejeitadas), satisfazendo aos Requisitos 2 e 5.
4. A integração de Objective/Save processou todas as 7.791 sequências de `objective_save_sequences.parquet` com fechamento exato (7.659 substituições, 132 rejeições justificadas), aplicando deterministamente a hierarquia de precedência (`plant/defuse > OBJECTIVE`, `save > SAVE`, `OBJECTIVE/SAVE > generic`), satisfazendo ao Requisito 3.
5. O relabeling de NextSector utilizou horizonte futuro real de 128 frames (8.0s), aplicando DYNAMIC com fonte `NO_TRANSITION_DYNAMIC` na ausência de transição, sem setor atual sem deslocamento e sem metas da Utility AI, satisfazendo ao Requisito 4.
6. A execução empírica dos Gates Determinísticos do DataLoader (item 1 da observação) sob seed 42026 atestou 100% de concordância numérica contra os tensores brutos reais dos NPZs, com zero dados sintéticos, aliados autênticos e isolamento absoluto do split Test (zero inferências de modelo), satisfazendo aos Requisitos 2 e 5.
7. A execução de 388 testes automatizados (item 2, 3 e 4 da observação) atestou 100% de conformidade com zero falhas e zero regressões em Python e C#, satisfazendo ao Requisito 7.
8. Os 20 entregáveis foram materializados e verificados no disco com hashes de 64 caracteres, incluindo o único relatório Markdown canônico `marco_2b1_final_report.md` e o relatório adversarial `adversarial_success_audit.json`, satisfazendo integralmente às diretrizes do marco.

---

## 3. Caveats

- A divergência de Jensen-Shannon entre o índice piloto e o índice completo é de 0.2691, classificando o piloto como `NON_REPRESENTATIVE`. Conforme documentado no relatório técnico, essa divergência é decorrente da correção do viés histórico na cabeça NextSector (que continha 99,63% MID no piloto devido à extração exclusiva na base TR e agora distribui as 6 classes de forma realista com suporte real). Essa classificação não invalida o piloto retroativamente, mas fundamenta o treinamento completo no corpus integral.
- No split Test, nenhum forward pass de modelo neural foi executado (apenas validação determinística de fatias NPZ pelo DataLoader), preservando o split congelado e selado conforme a Regra 02 do `AGENTS.md`.

---

## 4. Conclusion

O índice temporal canônico de posicionamento para o corpus completo de Mirage v2 (3.411.434 sequências distribuídas em 6 shards Parquet de ~9,8 MB e 6 companion JSONs) está plenamente homologado com 100% de integridade física e metodológica. Todos os 20 entregáveis estão no disco com hashes SHA-256 verificados. Veredito canônico formal: **`FULL_TEMPORAL_INDEX_READY_FOR_FULL_TRAINING`**.

Em estrito cumprimento da Regra 08 (`no-automatic-phase-advance`), nenhuma rotina de treinamento neural foi disparada. O ambiente aguarda deliberação e autorização expressa do usuário humano para a entrada no Marco 2B.2.

---

## 5. Verification Method

Para reproduzir e auditar independentemente a entrega:
1. **Executar a auditoria empírica independente do DataLoader (seed 42026)**:
   ```powershell
   python .agents/teamwork/adversarial_success_auditor_1/independent_dataloader_audit.py
   ```
   *Critério de invalidação: qualquer taxa diferente de 100.0% em Tolerance/Teammates ou > 0.0% em violações.*
2. **Executar a suíte de testes de governança do Marco 2B.1**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b1_full_index.py -v
   ```
   *Critério de invalidação: qualquer falha entre os 20 testes unitários.*
3. **Executar as suítes de regressão do DataLoader e Preflight**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone1_dataloader.py tests/test_phase3a3_b_milestone2b_preflight.py -v
   ```
4. **Executar os testes C# do projeto**:
   ```powershell
   dotnet test
   ```
   *Critério de invalidação: qualquer falha entre os 340 testes C#.*
5. **Auditar os hashes físicos dos 20 entregáveis**:
   ```powershell
   python .agents/teamwork/adversarial_success_auditor_1/hash_audit.py
   ```
