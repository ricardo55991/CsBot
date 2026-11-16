# Relatório Canônico do DataLoader Temporal Real — Marco 1

**Fase:** FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER  
**Marco:** Marco 1 — Reconstrução Temporal Canônica e Homologação do DataLoader Real  
**Data/Hora UTC:** 2026-11-07T23:35:00Z  
**Classificação de Homologação:** `AGENT_REVIEWED`  
**Natureza dos Dados Auditados:** `REAL` (444 arquivos `.npz` gravados a 16Hz em `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\`)  
**Veredito Canônico do Gate 1:** **`CANONICAL_TEMPORAL_DATALOADER_READY_FOR_PILOT`**

---

## 1. Sumário Executivo

O Marco 1 da **FASE 3A.3-B** teve como objetivo central eliminar em definitivo todo histórico sintético, rampas lineares (`np.linspace` / `step_drift`) e clones de aliados do pipeline do Positioning Transformer, substituindo-os por um DataLoader canônico de alta performance que reconstrói janelas temporais de 32 frames ($2,0$ segundos a 16 Hz) consumindo diretamente os tensores brutos dos **444 arquivos `.npz` físicos** de Mirage gravados em disco.

A auditoria forense independente — composta pelo **Data Provenance and Temporal Auditor** e pelo **Adversarial Success Auditor** — avaliou a implementação em duas rodadas:
1. Na primeira rodada, o Adversarial Success Auditor detectou uma vulnerabilidade de fronteira de round baseada em índice ordinal de parquet e a ausência de manifest formal disjunto para os 444 NPZs, emitindo `TEMPORAL_DATALOADER_NOT_READY`.
2. O ciclo devolutivo de governança (`09-subagent-role-isolation`) foi acionado, despachando correções para o Implementador, que substituiu o índice ordinal por busca determinística via `np.searchsorted` no frame físico `f_idx`, materializou [`datasets/mirage_v2/canonical_temporal_splits_v1.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/datasets/mirage_v2/canonical_temporal_splits_v1.json) e criou a suíte de testes [`tests/test_phase3a3_b_milestone1_dataloader.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tests/test_phase3a3_b_milestone1_dataloader.py).
3. Na re-auditoria, todos os 7 gates foram aprovados categoricamente com **100.0% de conformidade estrita** sobre 500 amostras sob seed 42026, resultando na emissão formal de:

$$\mathbf{CANONICAL\_TEMPORAL\_DATALOADER\_READY\_FOR\_PILOT}$$

---

## 2. Reconciliação dos Splits e Inventário Primário (311 / 66 / 67)

Em conformidade com a determinação do usuário humano, os números de splits foram formalmente esclarecidos e reconciliados diretamente contra o acervo de tensores e os manifests de divisão:

- O acervo físico bruto em `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\` contém exatamente **444 arquivos `.npz`**, cada um correspondendo a uma `demo_id` única de Mirage.
- O inventário anterior `demo_inventory_v2.json` continha 452 entradas porque registrava 8 partidas também no formato bruto `RAW_DEM_SOURCE2` (`.dem`).
- Essas 8 demos não extraídas em formato NPZ foram formalmente catalogadas como `excluded_demos` no novo arquivo canônico de splits: [`datasets/mirage_v2/canonical_temporal_splits_v1.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/datasets/mirage_v2/canonical_temporal_splits_v1.json).

### Tabela Canônica de Reconciliação de Splits:

| Split Canônico | Demos Únicas (NPZ) | Partidas Únicas | Formato Físico | Percentual do Corpus | Sobreposição com outros Splits |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Train** | **311** | 305 | `NPZ_16HZ_TENSOR` | 70.05% `(311 / 444)` | 0 demos `(0 / 444)` |
| **Validation** | **66** | 65 | `NPZ_16HZ_TENSOR` | 14.86% `(66 / 444)` | 0 demos `(0 / 444)` |
| **Test** | **67** | 66 | `NPZ_16HZ_TENSOR` | 15.09% `(67 / 444)` | 0 demos `(0 / 444)` |
| **Total Conforme** | **444** | **436** | `NPZ_16HZ_TENSOR` | **100.0%** `(444 / 444)` | **Disjunção Estrita (Zero Leakage)** |
| *Excluídas (.dem)* | *8* | *8* | `RAW_DEM_SOURCE2` | *N/A (sem NPZ)* | *Isoladas no manifest* |

---

## 3. Matriz Definitiva dos 7 Gates do Marco 1

A avaliação foi executada pelo script de auditoria determinística [`tools/phase3a_training/audit_canonical_temporal_dataloader.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/phase3a_training/audit_canonical_temporal_dataloader.py) comparando 500 sequências aleatórias sob seed determinística `42026` (250 Train, 125 Validation, 125 Test) contra os tensores brutos cru lidos diretamente de `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\`:

| # | Gate Obrigatório do Marco 1 | Meta | Valor Medido | Fórmula Exata (N / D) | Tolerância | Veredito |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: |
| **G1** | **`ToleranceMatchRate`** | **100.0%** | **100.00%** | `(500 / 500)` | $\Delta < 10^{-5}$ | ✅ **PASS** |
| **G2** | **`SyntheticWindowRate`** | **0.0%** | **0.00%** | `(0 / 500)` | Exata ($0$) | ✅ **PASS** |
| **G3** | **`UnmaskedPaddingRate`** | **0.0%** | **0.00%** | `(0 / 500)` | Exata ($0$) | ✅ **PASS** |
| **G4** | **`RoundBoundaryViolationRate`** | **0.0%** | **0.00%** | `(0 / 500)` | Exata ($0$) | ✅ **PASS** |
| **G5** | **`FutureLeakageRate`** | **0.0%** | **0.00%** | `(0 / 500)` | Exata ($0$) | ✅ **PASS** |
| **G6** | **`TeammateRealSlotMatchRate`** | **100.0%** | **100.00%** | `(2000 / 2000)` | $\Delta < 10^{-5}$ | ✅ **PASS** |
| **G7** | **`np.linspace / drift ausentes`** | **0** | **0** | `(0 / 500)` | Varredura AST | ✅ **PASS** |

### Métricas Físicas Complementares de Dinamismo:
- **`MeanSpatialDisplacement`**: **317.45 CS2 game units** (deslocamento espacial médio nos 32 frames comprovando que os jogadores estão se movimentando ativamente na partida e não são tensores estáticos).
- **`MeanTemporalVariance`**: **34.179,01 CS2 game units²** (variância temporal dinâmica sobre as 3 coordenadas espaciais, contrastando com $\sigma = 0$ do histórico sintético anterior).
- **Amostras com Padding (Início de Round)**: 13 amostras em 500 ($2,60\%$). Em 100% delas, `temporal_mask[:32-k] == 0.0` e `temporal_mask[32-k:] == 1.0`, garantindo zero padding desmascarado.

---

## 4. Arquitetura do Novo DataLoader Canônico

O novo pipeline reside em [`tools/phase3a_training/canonical_temporal_dataloader.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/phase3a_training/canonical_temporal_dataloader.py) e introduz três avanços estruturais:

1. **`NPZCacheManager` Thread-Safe:**
   - Gerencia o carregamento sob demanda dos arquivos `.npz` com cache LRU em memória, atingindo throughput superior a 100.000 sequências/segundo.
2. **Determinação Determinística de Fronteira por `f_idx`:**
   - Detecta resets da feature `round_time_norm` ($X[:, 0, 17]$) com `diff > 0.15` para mapear `round_bounds`.
   - Localiza o round ativo estritamente via:
     ```python
     r_detected = int(np.searchsorted(round_bounds, f_idx, side="right") - 1)
     r_detected = max(0, min(r_detected, len(round_bounds) - 2))
     start_f = int(round_bounds[r_detected])
     end_f = int(round_bounds[r_detected + 1])
     ```
   - Garante $start\_f \le f\_idx < end\_f$ com zero leitura de frames de rounds anteriores.
3. **Extração de Aliados Reais por Slot:**
   - Para CT (`slot < 5`): aliados são estritamente `[s for s in range(5) if s != slot]`.
   - Para TR (`slot >= 5`): aliados são estritamente `[s for s in range(5, 10) if s != slot]`.
   - Elimina clones transladados por `offset` e fornece as trajetórias e features genuínas dos 4 companheiros em $[32, 4, 18]$.
4. **Mascaramento Temporal de Início de Round:**
   - Se $k = f\_idx - start\_f + 1 < 32$, os primeiros $32-k$ frames recebem zeros e `temporal_mask[:32-k] = 0.0`. Os $k$ frames autênticos do round recebem `temporal_mask[32-k:] = 1.0`.

---

## 5. Suíte de Testes Unitários de Governança

Criada a suíte [`tests/test_phase3a3_b_milestone1_dataloader.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tests/test_phase3a3_b_milestone1_dataloader.py), executada com pytest:

```bash
pytest -v tests/test_phase3a3_b_milestone1_dataloader.py
```

Resultados dos 8 testes unitários:
- `test_deterministic_round_search_by_frame_index`: **PASSED**
- `test_adversarial_round_idx_immunity`: **PASSED**
- `test_masked_padding_early_round`: **PASSED**
- `test_zero_future_leakage`: **PASSED**
- `test_real_teammate_slots_no_clones`: **PASSED**
- `test_no_linspace_or_step_drift`: **PASSED**
- `test_canonical_splits_materialization_and_filtering`: **PASSED**
- `test_dataloader_batch_integration`: **PASSED**

**Consolidado:** **`8 passed in 4.15s (100.0% PASS)`**

---

## 6. Inventário Criptográfico de Artefatos do Marco 1

Todos os artefatos foram conferidos diretamente no disco em tempo de execução. Hashes SHA-256 completos de 64 caracteres hexadecimais:

| Arquivo (Caminho Relativo ao Repositório) | Natureza do Dado | Tamanho (Bytes) | Hash SHA-256 Completo (64 caracteres) | Papel no Pipeline |
| :--- | :---: | :---: | :--- | :--- |
| `datasets/mirage_v2/canonical_temporal_splits_v1.json` | `REAL` | 33.670 | `9bd9d18362601d5416a7cb3b0292b3c31d0054ffa16b14214d195f4c6d9b3918` | Divisão formal disjunta dos 444 tensores NPZ |
| `tools/phase3a_training/canonical_temporal_dataloader.py` | `CODE` | 22.464 | `584ae21254272cc3c08e1866a41586391f0847edb714601494ea89f764612d6e` | Módulo do DataLoader Temporal Canônico 32 frames |
| `tools/phase3a_training/data_utils.py` | `CODE` | 20.025 | `d0121161f1fd2eb85353734ab41fb29f371486c3107d75266905ab089d62b5d9` | Adaptador com remoção total de linspace/drift |
| `tools/phase3a_training/audit_canonical_temporal_dataloader.py` | `CODE` | 24.171 | `2bbfccf16d73a4ea4ac234dc90a2461a022f88d050698a31829bec519c5a948e` | Script determinístico de auditoria forense amostral |
| `tests/test_phase3a3_b_milestone1_dataloader.py` | `CODE` | 13.987 | `8012a66ab4e0b2508e0dc78a7b422af73e5bb2458ea7a6ddc646dcd78ac6477e` | Suíte unitária e adversarial do Marco 1 (8 testes) |
| `training_runs/positioning_v1/temporal_dataloader_metrics.json` | `REAL` | 2.959 | `9d5b950294442272fe6be227764d4bda4b745b68c60715ca3da80f5b97fd4285` | Telemetria agregada das métricas dos 7 gates |
| `training_runs/positioning_v1/npz_window_batch_audit.json` | `REAL` | 591.332 | `826d66b72207437fa533e2a4bfcd7ce67ebc7150459fa2af3c670b3602880ecd` | Registro forense detalhado das 500 amostras |

---

## 7. Decisões dos Auditores Independentes

- **Data Provenance and Temporal Auditor:**
  - Veredito: **`CANONICAL_TEMPORAL_DATALOADER_AUDIT_PASS`**
  - Confirmação de 100% de proveniência autêntica a partir dos 444 arquivos `.npz` em `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\`, descontinuação formal de `step_drift` e isolamento dos splits.
- **Adversarial Success Auditor:**
  - Veredito Final: **`CANONICAL_TEMPORAL_DATALOADER_READY_FOR_PILOT`**
  - Confirmação de que todas as fragilidades apontadas na primeira rodada foram eliminadas, a busca por `f_idx` blinda contra desvios de round, e os 7 gates foram matematicamente cumpridos.

---

## 8. Conclusão e Parada Obrigatória (Regra 08)

O Marco 1 da Fase 3A.3-B está oficialmente **CONCLUÍDO E HOMOLOGADO**.

Em estrito cumprimento à **Regra `08-no-automatic-phase-advance`** e à instrução expressa do usuário humano:
- O **Marco 2 NÃO foi iniciado automaticamente**.
- Nenhum dry-run, piloto ou treinamento foi disparado.
- Todos os subagentes foram encerrados via `kill_all`.
- O workspace aguarda aprovação e comando humano para prosseguir.
