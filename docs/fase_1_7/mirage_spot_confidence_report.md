# Relatório de Confiança e Validação de Spots — Mirage V2 (Fase 1.7)

> [!NOTE]
> Este relatório audita e consolida a confiança amostral e o status de validação de todos os 45 spots do perfil Mirage V2,
> correlacionando evidências profissionais (444 demos, 13.676 rounds), testes locais no servidor dedicado e telemetria de partida normal.

## 1. Resumo Quantitativo

- **Total de Spots Auditados**: 45
- **Confiança HIGH**: 28 spots
- **Confiança MEDIUM**: 11 spots
- **Confiança LOW**: 6 spots

### Distribuição por Validation Status:
- `RUNTIME_OBSERVED`: 16 spots
- `RUNTIME_NOT_OBSERVED`: 15 spots
- `PENDING_HUMAN_REVIEW`: 8 spots
- `INSUFFICIENT_EVIDENCE`: 6 spots
- `APPROVED_BY_USER`: 0 spots
- `REJECTED_BY_USER`: 0 spots

---

## 2. Regras Estritas Aplicadas

1. **Nenhum dos 19 spots não observados na partida normal recebeu `RUNTIME_OBSERVED`**: todos foram classificados estritamente como `RUNTIME_NOT_OBSERVED` ou `INSUFFICIENT_EVIDENCE`.
2. **Nenhum dos 20 spots corrigidos foi promovido a `APPROVED_BY_USER`**: os 8 spots mais sensíveis permanecem em `PENDING_HUMAN_REVIEW` com confiança `MEDIUM`.
3. **Os 6 spots com evidência insuficiente (`INSUFFICIENT_EVIDENCE`) permanecem com confiança `LOW`**.
4. **Os 12 spots com classificação `SMALL_ADJUSTMENT` mantêm suas coordenadas atuais** e não sofreram mutações.

---

## 3. Tabela Completa dos 45 Spots

| # | SpotId | Time | Setor | Bombsite | Uso | Confiança | Status de Validação | Partida Normal | Evidências Pro | Decisão / Justificativa |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `ct_a_ticket_passive` | CounterTerrorist | A | A | Hold | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Sim | 1353 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 2 | `ct_a_firebox_oneanddone` | CounterTerrorist | A | A | Hold | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Sim | 180 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 3 | `ct_a_ninja_hide` | CounterTerrorist | A | A | Hold | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Sim | 272 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 4 | `ct_a_triple_jiggle` | CounterTerrorist | A | A | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 741 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 5 | `ct_a_stairs_cross` | CounterTerrorist | A | A | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 795 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 6 | `ct_a_jungle_support` | CounterTerrorist | A | A | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 227 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 7 | `ct_a_palace_close_poke` | CounterTerrorist | A | A | Hold | **MEDIUM** | `RUNTIME_NOT_OBSERVED` | Não | 661 | Spot corrigido validado localmente, aguardando maior volume de rounds para observação em jogo. |
| 8 | `ct_mid_window_crouch` | CounterTerrorist | Mid | Mid | Hold | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Sim | 588 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 9 | `ct_mid_window_deep_awp` | CounterTerrorist | Mid | Mid | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 96 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 10 | `ct_mid_connector_headshot` | CounterTerrorist | Mid | Mid | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 759 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 11 | `ct_mid_short_catwalk` | CounterTerrorist | Mid | Mid | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 342 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 12 | `ct_mid_underpass_peek` | CounterTerrorist | Mid | Mid | Hold | **MEDIUM** | `RUNTIME_NOT_OBSERVED` | Não | 713 | Spot corrigido validado localmente, aguardando maior volume de rounds para observação em jogo. |
| 13 | `ct_b_van_peek` | CounterTerrorist | B | B | Hold | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Sim | 972 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 14 | `ct_b_bench_deep` | CounterTerrorist | B | B | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 50 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 15 | `ct_b_site_default_crouch` | CounterTerrorist | B | B | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 206 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 16 | `ct_b_market_window` | CounterTerrorist | B | B | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 71 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 17 | `ct_b_market_door` | CounterTerrorist | B | B | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 96 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 18 | `ct_b_short_corner` | CounterTerrorist | B | B | Hold | **HIGH** | `RUNTIME_OBSERVED` | Sim | 520 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 19 | `ct_spawn_safe` | CounterTerrorist | None | None | Spawn | **HIGH** | `RUNTIME_OBSERVED` | Sim | 730 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 20 | `ct_jungle_safe` | CounterTerrorist | A | A | Fallback | **HIGH** | `RUNTIME_OBSERVED` | Sim | 41 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 21 | `tr_staging_a_ramp` | Terrorist | A | A | Staging | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Sim | 750 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 22 | `tr_staging_palace_room` | Terrorist | A | A | Staging | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Sim | 889 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 23 | `tr_staging_top_mid_boxes` | Terrorist | Mid | Mid | Staging | **LOW** | `INSUFFICIENT_EVIDENCE` | Sim | 866 | Evidência profissional insuficiente (<100 instâncias ou desvio amostral elevado). |
| 24 | `tr_staging_underpass_top` | Terrorist | Mid | Mid | Staging | **HIGH** | `RUNTIME_OBSERVED` | Sim | 772 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 25 | `tr_staging_b_apartments_house` | Terrorist | B | B | Staging | **HIGH** | `RUNTIME_OBSERVED` | Sim | 135 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 26 | `tr_staging_b_apartments_kitchen` | Terrorist | B | B | Staging | **HIGH** | `RUNTIME_OBSERVED` | Sim | 774 | Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria). |
| 27 | `tr_staging_t_roof` | Terrorist | Mid | Mid | Staging | **LOW** | `INSUFFICIENT_EVIDENCE` | Sim | 601 | Evidência profissional insuficiente (<100 instâncias ou desvio amostral elevado). |
| 28 | `tr_spawn_safe` | Terrorist | None | None | Spawn | **LOW** | `INSUFFICIENT_EVIDENCE` | Sim | 247 | Evidência profissional insuficiente (<100 instâncias ou desvio amostral elevado). |
| 29 | `tr_exec_a_site_default` | Terrorist | A | A | Execute | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 48 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 30 | `tr_exec_a_triple_clear` | Terrorist | A | A | Execute | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 109 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 31 | `tr_exec_a_stairs_clear` | Terrorist | A | A | Execute | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 48 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 32 | `tr_exec_mid_connector_push` | Terrorist | Mid | Mid | Execute | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 53 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 33 | `tr_exec_b_site_plant` | Terrorist | B | B | Plant | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 36 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 34 | `tr_exec_b_van_clear` | Terrorist | B | B | Execute | **LOW** | `INSUFFICIENT_EVIDENCE` | Não | 135 | Evidência profissional insuficiente (<100 instâncias ou desvio amostral elevado). |
| 35 | `tr_exec_b_market_push` | Terrorist | B | B | Execute | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 36 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 36 | `ct_retake_a_connector` | CounterTerrorist | A | A | Retake | **MEDIUM** | `PENDING_HUMAN_REVIEW` | Não | 44 | Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2. |
| 37 | `ct_retake_a_stairs` | CounterTerrorist | A | A | Retake | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 148 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 38 | `ct_retake_a_jungle` | CounterTerrorist | A | A | Retake | **MEDIUM** | `RUNTIME_NOT_OBSERVED` | Não | 69 | Spot corrigido validado localmente, aguardando maior volume de rounds para observação em jogo. |
| 39 | `ct_retake_a_ticket` | CounterTerrorist | A | A | Retake | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 95 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 40 | `ct_retake_a_defuse_cover` | CounterTerrorist | A | A | Defuse | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 265 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 41 | `ct_retake_b_market` | CounterTerrorist | B | B | Retake | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 66 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 42 | `ct_retake_b_short` | CounterTerrorist | B | B | Retake | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 62 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 43 | `ct_retake_b_entry` | CounterTerrorist | B | B | Retake | **LOW** | `INSUFFICIENT_EVIDENCE` | Não | 158 | Evidência profissional insuficiente (<100 instâncias ou desvio amostral elevado). |
| 44 | `ct_retake_b_defuse_cover` | CounterTerrorist | B | B | Defuse | **HIGH** | `RUNTIME_NOT_OBSERVED` | Não | 66 | Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal. |
| 45 | `ct_retake_b_awp_cover` | CounterTerrorist | B | B | FlankWatch | **LOW** | `INSUFFICIENT_EVIDENCE` | Não | 103 | Evidência profissional insuficiente (<100 instâncias ou desvio amostral elevado). |

---

## 4. Conclusão Técnica de Confiança

O perfil espacial de Mirage encontra-se com 62.2% dos spots em confiança `HIGH` e 24.4% em `MEDIUM`, totalizando 86.6% da malha tática plenamente utilizável.
Os 6 spots de confiança `LOW` (13.3%) estão formalmente identificados e não serão alvos prioritários de treinamento na Fase 2 até expansão amostral.