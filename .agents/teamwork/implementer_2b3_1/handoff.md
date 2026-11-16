# Handoff Report — Fase 3A.3-B, Marco 2B.3: Treinamento Completo do Positioning Transformer Temporal Real

**Agente**: `implementer_2b3_1` (Model and Training Implementer)  
**Data/Hora**: 2026-11-08T21:58:00Z  
**Diretório de Trabalho**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\implementer_2b3_1`  
**Destinatário**: Orchestrator (`5aa571f6-be49-4f7f-baff-92e5c3c7ec1a`)  

---

## 1. Observation

Durante a execução da Fase 3A.3-B, Marco 2B.3, foram observados diretamente e materializados no disco os seguintes fatos, arquivos e evidências:

### 1.1 Verificação de Integridade dos Datasets e Shards 1:1
- Foram carregados os 6 shards Parquet de `datasets/mirage_v2/positioning_v2_full_temporal/` e os 6 sidecars Parquet de `datasets/mirage_v2/positioning_v2_full_temporal/label_sidecars_v2/`.
- Linhas totais no corpus base: 3.411.434 sequências.
- Linhas totais nos sidecars de labels v2: 3.411.434 sequências.
- Divergências de chave primária (`sequence_id`), linhas faltantes ou conflitantes: exatamente 0 (0 missing, 0 duplicate, 0 conflict).
- Distribuição por split:
  - **Train**: 2.364.492 linhas (311 demos canônicas, shards 0 a 4)
  - **Validation**: 501.434 linhas (66 demos canônicas, shards 4 e 5)
  - **Test**: 545.508 linhas (67 demos canônicas, shard 5) — **split lacrado, zero leituras para treino ou inferência**.

### 1.2 Artefatos de Treinamento e Configuração Materializados
No diretório `training_runs/positioning_v2_real_temporal/full_training/`, foram gerados 11 arquivos de topo e 3 subdiretórios com 13 arquivos cada (total de 50 arquivos materializados):

Hashes SHA-256 (64 hexadecimais completos):
- `1b8270d4539007c4cf0cb0ecfd716985ba59e6086ef46345dd2b3a49e567fa9a`  `training_runs/positioning_v2_real_temporal/full_training/baseline_comparison.json`
- `457035fa3943e37f7f6859b4498deffd5b9deaa19f711c20e56b46adc8bcaa44`  `training_runs/positioning_v2_real_temporal/full_training/best_model_selection.json`
- `8ab2a7c4a573d65a39c497a21ea8df400c9618f16756e40d3b2d481919346210`  `training_runs/positioning_v2_real_temporal/full_training/class_weights.json`
- `0ba1020c5c6dde09527d63831c5f1c4742b6e582eefa5fe35ab5f6255a15f7e1`  `training_runs/positioning_v2_real_temporal/full_training/collapse_monitoring.json`
- `8322d8eff8d635d98cbb63c9e02ac6a887f5a289fab0629f1c3474ff178fc464`  `training_runs/positioning_v2_real_temporal/full_training/compute_preflight.json`
- `8e344ad4ae452b4733d2941737f61f87c292114af7c0fb7a9c9acdc8b38c1bf3`  `training_runs/positioning_v2_real_temporal/full_training/frozen_composite_formula.json`
- `79dd3db45c4512bbc21a86db1ba318bc44d564338bd64b08a40f722f9aaec707`  `training_runs/positioning_v2_real_temporal/full_training/frozen_training_config.json`
- `35e0421c7ccf9836615eef1d29d9c6ebbb4a823077373b8afab072d25599297d`  `training_runs/positioning_v2_real_temporal/full_training/input_snapshot.json`
- `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`  `training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt`
- `0708555fcab35907dfdc31452f62e4aefee2ba871c2a7cb9eeb4c12e97357c24`  `training_runs/positioning_v2_real_temporal/full_training/temporal_gain_report.json`
- `4096a8626fb8c347b0fff21703dd86a327af85573c6f672a7a03b8095b0685e5`  `training_runs/positioning_v2_real_temporal/full_training/three_seed_comparison.json`

Hashes das 3 seeds:
- `seed_42026/best_checkpoint.pt`: `ac6a528d6a7e05a9a0258fa25c807d57202227ce0b2307848a2692e00d33c319` (CompositeScore: 0.4694, Época 8)
- `seed_42027/best_checkpoint.pt`: `20a1de5df732b9dc67a37ce6be3efe111808f0f481df7617aa5af7a0c790bd46` (CompositeScore: 0.4623, Época 8)
- `seed_42028/best_checkpoint.pt`: `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352` (CompositeScore: 0.4700, Época 6)
- **Candidato Mestre Selecionado**: `selected_candidate.pt` possui SHA-256 idêntico ao `seed_42028/best_checkpoint.pt`.

### 1.3 Resultados de Validação e Métricas Multitask
Desempenho da Seed Vencedora (42028) no split Validation (5.120 amostras avaliadas, 66 demos):
- **CompositeScore**: `0.4700`
- **Spot MRR**: `0.7604`
- **Spot Top-1 Accuracy**: `62.29%` (3189 / 5120)
- **Spot Top-5 Accuracy**: `95.55%` (4892 / 5120)
- **State Active Macro-F1**: `0.2250` (denominador de classes ativas: 5 de 7)
- **Transition Active Macro-F1**: `0.5637` (denominador de classes ativas: 6 de 7)
- **ExitTrigger Active Macro-F1**: `0.2613` (denominador de classes ativas: 7 de 8)
- **SectorTransition Macro-F1**: `0.4649`
- **NextSector Macro-F1**: `0.3652` (avaliado nas sequências com transição ativa)

Classes raras ou ausentes no split de validação (Regra 03):

| Classe | Support | Recall | F1-Score | Status |
| :--- | :--- | :--- | :--- | :--- |
| `Transition: LURK` | 0 | N/A | N/A | N/A |
| `ExitTrigger: BOMB_SPOTTED` | 0 | N/A | N/A | N/A |
| `Spot: 27 spots mascarados` | 0 | N/A | N/A | N/A |

### 1.4 Suítes de Testes Executadas
1. `pytest tests/test_phase3a3_b_milestone2b3_full_training.py -v`:
   - Resultado: **22 passed, 0 failed** (22/22 PASS).
2. `pytest tests/test_phase3a3_b_milestone2b2_label_patch.py tests/test_phase3a3_b_milestone2b1_full_index.py -v`:
   - Resultado: **40 passed, 0 failed** (40/40 PASS de regressão dos Marcos 2B.1 e 2B.2).
3. `dotnet test --nologo`:
   - Resultado: **340 aprovados, 0 com falha** (340/340 PASS em net10.0).

---

## 2. Logic Chain

1. **Observação 1.1 → Shards e Join 1:1**: A leitura direta dos 6 shards e 6 sidecars confirmou 3.411.434 sequências idênticas, 0 divergências de chave primária e 0 registros órfãos. Logo, a base física de dados satisfaz a integridade de entrada sem necessidade de interpolação.
2. **Observação 1.1 e 1.2 → Isolamento Estrito de Test (Regra 02)**: O `CanonicalV2PositioningDataset` lança explicitamente `ValueError` se `split == "test"`. Nenhuma demo do Test set (67 demos) foi exposta à função de perda ou inferência preditiva. Apenas hashes de catálogo foram catalogados no snapshot de entrada.
3. **Observação 1.2 → Pesos Train-Only e Fórmulas Congeladas**: Os pesos de classe foram calculados unicamente com os contadores de frequência das 311 demos de treino (2.364.492 linhas), gravados em `class_weights.json` e congelados antes da inicialização das redes neurais.
4. **Observação 1.2 e 1.3 → Arquitetura e Condicionalidade da Loss**: A cabeça `NextSector` teve sua perda mascarada por `(sector_transition_occurs == 1)`. Spots não supervisionados receberam logit `-1e9`, garantindo 0 seleções inválidas e 0 contribuição espúria na loss.
5. **Observação 1.2 e 1.3 → Determinismo e Variância entre Seeds**: O treinamento executou 8 épocas em cada uma das seeds {42026, 42027, 42028}. A média do CompositeScore foi de 0.4672 com desvio padrão de apenas 0.0035, comprovando convergência estável sem colapso estocástico.
6. **Observação 1.4 → Cobertura de Testes e Governança**: A suíte de 22 testes unitários passou integralmente, confirmando o respeito às Regras 01, 02, 03, 04, 06 e 09 do `AGENTS.md`. A suíte C# de 340 testes permaneceu 100% verde.

---

## 3. Caveats

1. **Classes Raras**: No split de validação (assim como no split de treino conforme os contratos canônicos), as classes `LURK` (Transition) e `BOMB_SPOTTED` (ExitTrigger) não possuem amostras positivas. Em estrita conformidade com a Regra 03 do `AGENTS.md`, seu F1 e Recall são reportados exclusivamente como `N/A` e foram excluídos do cálculo das macro-médias sem substituição arbitrária por zeros ou uns.
2. **Horizonte de Avaliação**: O modelo foi avaliado exclusivamente contra o split de Validation (66 demos canônicas). Nenhuma avaliação sobre o Test Set foi realizada, respeitando a proibição absoluta de contaminação e a competência futura do Phase Gate.
3. **Diretório `models/` e Exportação ONNX**: Em estrito cumprimento das restrições do Marco 2B.3, nenhum arquivo foi copiado para `models/` e nenhum modelo ONNX foi exportado. O candidato selecionado reside exclusivamente em `training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt`.

---

## 4. Conclusion

O Treinamento Completo do Positioning Transformer Temporal Real (Fase 3A.3-B, Marco 2B.3) foi executado com sucesso e integridade absoluta.
- Todas as 3 seeds convergiram estavelmente sem colapso de classes.
- A Seed 42028 foi selecionada como a melhor candidata com CompositeScore de validação de `0.4700` e Spot MRR de `0.7604` (Top-5 Accuracy: `95.55%`).
- Os 22 testes unitários obrigatórios passaram com 100% de sucesso.
- A estabilidade de regressão em C# (340/340 PASS) e Python (40/40 PASS) foi comprovada.
- O entregável está pronto para a fase de auditoria independente e verificação adversarial pelo time de auditores.

---

## 5. Verification Method

Para reproduzir e auditar independentemente os resultados:

1. **Verificar os Testes Automatizados Unitários do Marco 2B.3**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b3_full_training.py -v
   ```
   *Critério de Invalidação*: Qualquer falha entre os 22 testes unitários.

2. **Verificar os Testes de Regressão e Integridade C#**:
   ```powershell
   pytest tests/test_phase3a3_b_milestone2b2_label_patch.py tests/test_phase3a3_b_milestone2b1_full_index.py -v
   dotnet test --nologo
   ```
   *Critério de Invalidação*: Qualquer regressão nos 40 testes de dataset ou nos 340 testes C#.

3. **Verificar os Hashes SHA-256 e Existência dos Artefatos**:
   ```powershell
   python -c "import hashlib, os; p='training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt'; print(hashlib.sha256(open(p,'rb').read()).hexdigest())"
   ```
   *Critério de Invalidação*: Divergência do hash `4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352`.

4. **Verificar Isolamento do Test Set**:
   Inspecionar `CanonicalV2PositioningDataset` em `tools/phase3a_training/canonical_v2_dataloader.py` e confirmar que tentar instanciar `split='test'` dispara `ValueError`.
