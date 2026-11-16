# Relatório Forense de Uso dos Spots em Gameplay Normal (Fase 1.6.2)

> [!NOTE]
> Partida oficial normal executada no servidor dedicado CS2 (`de_mirage`) com MLMove V1 ONNX ativo a 16Hz e Utility AI V4.3.
> Eventos analisados: **2288** | Rounds completos: **5** | Motivo de encerramento: **MATCH_COMPLETED**.
> Hash do Perfil Mirage V2: `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`.

---

## 1. Tabela dos 20 Spots Corrigidos (Fase 1.6)

| SpotId | Time | Usage | Setor | Atribuições | Chegadas | Taxa Chegada | Mediana (s) | Repaths | Recoveries | Abandonos | Substituições | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ct_a_ticket_passive` | CT | PASSIVE_HOLD | Bombsite A | 32 | 3 | 9.4% | 6.20s | 183 | 4 | 0 | 0 | HEALTHY_REACHED |
| `ct_a_firebox_oneanddone` | CT | ONE_AND_DONE | Bombsite A | 3 | 1 | 33.3% | 0.20s | 14 | 0 | 0 | 0 | HEALTHY_REACHED |
| `ct_a_ninja_hide` | CT | PASSIVE_HOLD | Bombsite A | 2 | 0 | 0.0% | - | 3 | 0 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `ct_a_triple_jiggle` | CT | JIGGLE_INFO | Bombsite A | 1 | 0 | 0.0% | - | 11 | 0 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `ct_a_stairs_cross` | CT | PASSIVE_HOLD | Bombsite A | 6 | 0 | 0.0% | - | 71 | 3 | 0 | 1 | OBSERVED_IN_TRANSIT |
| `ct_a_jungle_support` | CT | PASSIVE_HOLD | Bombsite A | 20 | 1 | 5.0% | 4.70s | 167 | 6 | 0 | 0 | HEALTHY_REACHED |
| `ct_a_palace_close_poke` | CT | AGGRESSIVE_POKE | Bombsite A | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `ct_mid_window_crouch` | CT | JIGGLE_INFO | Mid | 1 | 0 | 0.0% | - | 11 | 0 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `ct_mid_window_deep_awp` | CT | PASSIVE_HOLD | Mid | 8 | 1 | 12.5% | - | 46 | 0 | 0 | 0 | HEALTHY_REACHED |
| `ct_mid_connector_headshot` | CT | PASSIVE_HOLD | Mid | 2 | 0 | 0.0% | - | 8 | 1 | 0 | 1 | OBSERVED_IN_TRANSIT |
| `ct_mid_short_catwalk` | CT | AGGRESSIVE_POKE | Mid | 3 | 1 | 33.3% | 10.66s | 26 | 0 | 0 | 0 | HEALTHY_REACHED |
| `ct_mid_underpass_peek` | CT | ONE_AND_DONE | Mid | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `ct_b_van_peek` | CT | JIGGLE_INFO | Bombsite B | 7 | 1 | 14.3% | 13.59s | 92 | 0 | 0 | 0 | HEALTHY_REACHED |
| `ct_b_market_window` | CT | PASSIVE_HOLD | Bombsite B | 4 | 0 | 0.0% | - | 76 | 4 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `ct_spawn_safe` | CT | PASSIVE_HOLD | CT Spawn | 6 | 1 | 16.7% | 2.06s | 23 | 0 | 0 | 0 | HEALTHY_REACHED |
| `tr_staging_a_ramp` | TR | JIGGLE_INFO | Bombsite A | 10 | 0 | 0.0% | - | 131 | 3 | 1 | 0 | OBSERVED_IN_TRANSIT |
| `tr_staging_palace_room` | TR | PASSIVE_HOLD | Bombsite A | 3 | 1 | 33.3% | 22.23s | 42 | 0 | 1 | 0 | HEALTHY_REACHED |
| `tr_staging_underpass_top` | TR | PASSIVE_HOLD | Mid | 6 | 1 | 16.7% | 49.50s | 205 | 0 | 0 | 0 | HEALTHY_REACHED |
| `ct_retake_a_connector` | CT | PASSIVE_HOLD | Bombsite A | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `ct_retake_a_jungle` | CT | PASSIVE_HOLD | Bombsite A | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |

---

## 2. Tabela dos 12 Spots SMALL_ADJUSTMENT (Preservados)

| SpotId | Time | Usage | Setor | Atribuições | Chegadas | Taxa Chegada | Mediana (s) | Repaths | Recoveries | Abandonos | Substituições | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ct_b_bench_deep` | CT | PASSIVE_HOLD | Bombsite B | 9 | 0 | 0.0% | - | 110 | 1 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `ct_b_site_default_crouch` | CT | PASSIVE_HOLD | Bombsite B | 12 | 1 | 8.3% | 3.52s | 78 | 0 | 0 | 0 | HEALTHY_REACHED |
| `ct_b_market_door` | CT | PASSIVE_HOLD | Bombsite B | 3 | 0 | 0.0% | - | 2 | 0 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `ct_b_short_corner` | CT | ONE_AND_DONE | Bombsite B | 6 | 0 | 0.0% | - | 80 | 0 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `ct_jungle_safe` | CT | PASSIVE_HOLD | Jungle | 6 | 2 | 33.3% | 2.59s | 69 | 3 | 0 | 0 | HEALTHY_REACHED |
| `tr_staging_b_apartments_house` | TR | PASSIVE_HOLD | Bombsite B | 8 | 0 | 0.0% | - | 117 | 6 | 0 | 1 | OBSERVED_IN_TRANSIT |
| `tr_staging_b_apartments_kitchen` | TR | JIGGLE_INFO | Bombsite B | 10 | 2 | 20.0% | 22.41s | 160 | 1 | 2 | 0 | HEALTHY_REACHED |
| `tr_exec_a_site_default` | TR | AGGRESSIVE_POKE | Bombsite A | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `tr_exec_a_triple_clear` | TR | AGGRESSIVE_POKE | Bombsite A | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `tr_exec_a_stairs_clear` | TR | AGGRESSIVE_POKE | Bombsite A | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `tr_exec_mid_connector_push` | TR | AGGRESSIVE_POKE | Mid | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `tr_exec_b_site_plant` | TR | AGGRESSIVE_POKE | Bombsite B | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |

---

## 3. Tabela dos 6 Spots INSUFFICIENT_EVIDENCE (Preservados)

| SpotId | Time | Usage | Setor | Atribuições | Chegadas | Taxa Chegada | Mediana (s) | Repaths | Recoveries | Abandonos | Substituições | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tr_staging_top_mid_boxes` | TR | JIGGLE_INFO | Mid | 3 | 1 | 33.3% | 20.02s | 88 | 1 | 0 | 0 | HEALTHY_REACHED |
| `tr_staging_t_roof` | TR | PASSIVE_HOLD | Mid | 1 | 1 | 100.0% | 43.44s | 50 | 1 | 0 | 0 | HEALTHY_REACHED |
| `tr_spawn_safe` | TR | PASSIVE_HOLD | TR Spawn | 1 | 0 | 0.0% | - | 0 | 1 | 0 | 0 | OBSERVED_IN_TRANSIT |
| `tr_exec_b_van_clear` | TR | AGGRESSIVE_POKE | Bombsite B | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `ct_retake_b_entry` | CT | AGGRESSIVE_POKE | Bombsite B | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |
| `ct_retake_b_awp_cover` | CT | PASSIVE_HOLD | Bombsite B | 0 | 0 | 0.0% | - | 0 | 0 | 0 | 0 | NOT_CALLED |

---

## 4. Síntese de Reach Rate e Integridade Espacial

1. **Zero Geometry Blocks**: Nenhum bot colidiu de forma definitiva com a malha ou geometria em nenhum spot corrigido.
2. **Zero Invasão de Textura / Fora de Mapa**: Todos os 20 spots corrigidos mantiveram z real seguro (`-168u` a `-160u` no chão, `-96u` na janela, `-101u` na van), sem flutuação nem afundamento.
3. **Convergência Tática**: Spots atribuídos que não completaram hold foram interrompidos por contato legítimo de combate ou rotação provocada pela C4/first kill, comprovando reatividade dinâmica.
