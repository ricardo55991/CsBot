# Proposta Controlada de Revisão Espacial — `de_mirage.json` (Fase 1.5)

> [!IMPORTANT]
> **Nenhuma alteração foi aplicada ao arquivo `src/CsBotManager/MapProfiles/de_mirage.json`.**
> Este documento apresenta a auditoria individual dos **45 TacticalSpots** atuais da Mirage contra os **176 clusters 3D de permanência real** (`69.320` episódios de hold estático com `v2d < 35 u/s`, duração $\ge 1,5\text{s}$ e deriva $\le 64\text{u}$) extraídos das **444 demos profissionais** e validados contra os `last_place_name` oficiais da Valve.

## 1. Resumo Executivo da Auditoria dos 45 Spots

| Classificação | Quantidade | Significado e Ação Recomendada |
| :--- | :---: | :--- |
| `WRONG_SECTOR` | **19** | Coordenada atual cai em outro `last_place_name` da Valve (erro crasso de setor). **Substituir pelo Medoid do cluster compatível.** |
| `WRONG_HEIGHT` | **1** | Coordenada XY caminhável, mas cota `Z` incompatível com os pisos observados ou setor errado. **Substituir pelo Medoid 3D correto.** |
| `SMALL_ADJUSTMENT` | **12** | Setor correto, mas deslocado entre `65u` e `260u` do pico real de hold profissional. **Ajuste fino opcional para o Medoid.** |
| `INSUFFICIENT_EVIDENCE` | **6** | Setor correto, porém poucos holds estáticos $\ge 1,5\text{s}$ em raio de `96u` (comum em spots de passagem/entry/plant). **Revisar candidato mais próximo ou manter.** |
| `VALID` | **7** | Setor, altura, caminhabilidade empírica e evidência profissional confirmados ($\le 64\text{u}$ de cluster ou $\ge 40$ demos locais). **Manter inalterado.** |
| `AMBIGUOUS` | **0** | Fronteira entre dois places da Valve com pureza kNN $< 0,55$. **Inspecionar via `setpos`.** |
| `UNREACHABLE` | **0** | Nenhum pé de jogador vivo observado em raio de `32u` em qualquer altura. **Substituir obrigatoriamente.** |

---

## 2. Tabela Completa de Auditoria e Coordenadas Propostas (45 Spots)

| # | SpotId | Side | Usage | Bomb | CurrentPosition | Place Real (kNN) | Place Esperado | Classificação | ProposedPosition (Medoid) | $\Delta$ (u) | Evidência (Holds / Demos / Players) | Dwell Mediano | Conf. |
| :-: | :--- | :-: | :--- | :-: | :--- | :--- | :--- | :--- | :--- | :-: | :---: | :-: | :-: |
| 1 | `ct_a_ticket_passive` | CT | Hold:PASSIVE_HOLD | A | `[-1930.0, -680.0, -160.0]` | `Shop` (1.00) | `BombsiteA`, `CTSpawn` | `WRONG_SECTOR` | `[-1011.5, -2479.9, -168.0]` | 2021u | 1353 / 336d / 499p | 4.00s | 0.94 |
| 2 | `ct_a_firebox_oneanddone` | CT | Hold:ONE_AND_DONE | A | `[-1050.0, -240.0, -160.0]` | `Ladder` (0.60) | `BombsiteA` | `WRONG_SECTOR` | `[-284.2, -2399.9, -164.0]` | 2292u | 180 / 128d / 140p | 14.56s | 0.77 |
| 3 | `ct_a_ninja_hide` | CT | Hold:PASSIVE_HOLD | A | `[-1320.0, -290.0, -160.0]` | `SnipersNest` (1.00) | `BombsiteA` | `WRONG_SECTOR` | `[-439.8, -2337.7, -168.0]` | 2229u | 272 / 145d / 175p | 2.78s | 0.78 |
| 4 | `ct_a_triple_jiggle` | CT | Hold:JIGGLE_INFO | A | `[-1150.0, -460.0, -160.0]` | `SnipersNest` (0.90) | `BombsiteA` | `WRONG_SECTOR` | `[-710.8, -2129.6, -180.0]` | 1726u | 741 / 268d / 389p | 2.75s | 0.94 |
| 5 | `ct_a_stairs_cross` | CT | Hold:PASSIVE_HOLD | A | `[-1100.0, -620.0, -160.0]` | `SnipersNest` (1.00) | `Stairs` | `WRONG_SECTOR` | `[-497.8, -1309.0, -160.0]` | 915u | 795 / 298d / 441p | 2.50s | 0.92 |
| 6 | `ct_a_jungle_support` | CT | Hold:PASSIVE_HOLD | A | `[-1250.0, -780.0, -160.0]` | `SnipersNest` (1.00) | `Jungle` | `WRONG_SECTOR` | `[-992.1, -1304.9, -155.6]` | 585u | 227 / 158d / 187p | 2.50s | 0.84 |
| 7 | `ct_a_palace_close_poke` | CT | Hold:AGGRESSIVE_POKE | A | `[-880.0, -320.0, -160.0]` | `Catwalk` (0.87) | `BombsiteA`, `Scaffolding` | `WRONG_SECTOR` | `[151.9, -1914.1, -168.0]` | 1899u | 661 / 241d / 318p | 3.06s | 0.94 |
| 8 | `ct_mid_window_crouch` | CT | Hold:JIGGLE_INFO | Mid | `[-1380.0, -540.0, -120.0]` | `Ladder` (0.80) | `SnipersNest` | `WRONG_SECTOR` | `[-1139.4, -462.3, -168.0]` | 257u | 588 / 256d / 367p | 3.00s | 0.92 |
| 9 | `ct_mid_window_deep_awp` | CT | Hold:PASSIVE_HOLD | Mid | `[-1480.0, -560.0, -100.0]` | `Shop` (1.00) | `SnipersNest` | `WRONG_SECTOR` | `[-1175.8, -732.5, -168.0]` | 356u | 96 / 70d / 73p | 3.53s | 0.61 |
| 10 | `ct_mid_connector_headshot` | CT | Hold:PASSIVE_HOLD | Mid | `[-820.0, -840.0, -160.0]` | `Middle` (0.90) | `Connector` | `WRONG_SECTOR` | `[-520.0, -984.0, -168.0]` | 333u | 759 / 299d / 438p | 3.50s | 0.95 |
| 11 | `ct_mid_short_catwalk` | CT | Hold:AGGRESSIVE_POKE | Mid | `[-950.0, -1050.0, -140.0]` | `Connector` (0.80) | `Catwalk` | `WRONG_SECTOR` | `[-906.4, 78.5, -166.0]` | 1130u | 342 / 214d / 269p | 2.72s | 0.73 |
| 12 | `ct_mid_underpass_peek` | CT | Hold:ONE_AND_DONE | Mid | `[-720.0, -1020.0, -220.0]` | `Connector` (1.00) | `Underpass`, `Ladder` | `WRONG_SECTOR` | `[-983.5, 289.8, -166.7]` | 1337u | 713 / 270d / 372p | 3.06s | 0.73 |
| 13 | `ct_b_van_peek` | CT | Hold:JIGGLE_INFO | B | `[-1350.0, 380.0, -150.0]` | `BombsiteB` (1.00) | `Truck` | `WRONG_SECTOR` | `[-2191.6, 712.6, -101.8]` | 906u | 972 / 302d / 450p | 3.56s | 0.96 |
| 14 | `ct_b_bench_deep` | CT | Hold:PASSIVE_HOLD | B | `[-1950.0, 450.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB` | `VALID` | — (manter atual) | 0u | 50 / 38d / 44p | 2.56s | 0.68 |
| 15 | `ct_b_site_default_crouch` | CT | Hold:PASSIVE_HOLD | B | `[-1750.0, 300.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB` | `SMALL_ADJUSTMENT` | `[-1927.1, 319.3, -160.0]` | 178u | 206 / 87d / 100p | 2.56s | 0.63 |
| 16 | `ct_b_market_window` | CT | Hold:PASSIVE_HOLD | B | `[-1880.0, 180.0, -130.0]` | `BombsiteB` (1.00) | `Shop` | `WRONG_SECTOR` | `[-1756.8, -560.2, -128.0]` | 750u | 71 / 53d / 55p | 3.00s | 0.30 |
| 17 | `ct_b_market_door` | CT | Hold:PASSIVE_HOLD | B | `[-1650.0, 220.0, -160.0]` | `BombsiteB` (1.00) | `Shop`, `BombsiteB` | `SMALL_ADJUSTMENT` | `[-1428.3, 116.8, -164.2]` | 245u | 96 / 56d / 61p | 2.88s | 0.47 |
| 18 | `ct_b_short_corner` | CT | Hold:ONE_AND_DONE | B | `[-1050.0, 250.0, -160.0]` | `Catwalk` (0.77) | `BombsiteB`, `Catwalk` | `VALID` | — (manter atual) | 0u | 520 / 229d / 306p | 2.88s | 1.00 |
| 19 | `ct_spawn_safe` | CT | Fallback/Save | CT Spawn | `[-2050.0, -800.0, -160.0]` | `Shop` (1.00) | `CTSpawn` | `WRONG_SECTOR` | `[-1279.6, -967.9, -168.0]` | 788u | 730 / 279d / 397p | 2.66s | 0.73 |
| 20 | `ct_jungle_safe` | CT | Fallback/Save | Jungle | `[-1350.0, -850.0, -160.0]` | `CTSpawn` (0.93) | `Jungle`, `CTSpawn` | `VALID` | — (manter atual) | 0u | 41 / 37d / 38p | 2.75s | 0.67 |
| 21 | `tr_staging_a_ramp` | TR | Staging | A | `[-250.0, -200.0, -160.0]` | `Catwalk` (1.00) | `TRamp` | `WRONG_SECTOR` | `[321.1, -1708.1, -176.0]` | 1613u | 750 / 300d / 471p | 2.81s | 0.93 |
| 22 | `tr_staging_palace_room` | TR | Staging | A | `[-350.0, -480.0, -90.0]` | `Catwalk` (0.77) | `PalaceInterior` | `WRONG_SECTOR` | `[288.1, -2373.4, -40.0]` | 1999u | 889 / 306d / 484p | 2.88s | 0.71 |
| 23 | `tr_staging_top_mid_boxes` | TR | Staging | Mid | `[450.0, -950.0, -160.0]` | `TopofMid` (1.00) | `TopofMid` | `INSUFFICIENT_EVIDENCE` | `[176.4, -206.6, -152.0]` | 792u | 866 / 336d / 566p | 2.69s | 0.74 |
| 24 | `tr_staging_underpass_top` | TR | Staging | Mid | `[150.0, -1050.0, -160.0]` | `TopofMid` (1.00) | `Middle`, `Underpass` | `WRONG_SECTOR` | `[-1038.9, -728.5, -264.0]` | 1236u | 772 / 312d / 521p | 2.56s | 0.92 |
| 25 | `tr_staging_b_apartments_house` | TR | Staging | B | `[-350.0, 650.0, -60.0]` | `BackAlley` (1.00) | `House`, `BackAlley`, `Apartments` | `SMALL_ADJUSTMENT` | `[-464.0, 654.0, -72.0]` | 115u | 135 / 94d / 110p | 2.75s | 0.60 |
| 26 | `tr_staging_b_apartments_kitchen` | TR | Staging | B | `[-850.0, 600.0, -60.0]` | `BackAlley` (1.00) | `Apartments`, `BackAlley` | `VALID` | — (manter atual) | 0u | 774 / 274d / 463p | 2.69s | 1.00 |
| 27 | `tr_staging_t_roof` | TR | Staging | Mid | `[750.0, -750.0, -100.0]` | `TopofMid` (1.00) | `PalaceAlley`, `TSpawn`, `TopofMid` | `INSUFFICIENT_EVIDENCE` | `[814.9, -1549.0, -109.0]` | 802u | 601 / 293d / 419p | 4.94s | 0.76 |
| 28 | `tr_spawn_safe` | TR | Fallback/Save | TR Spawn | `[1100.0, -200.0, -160.0]` | `TSpawn` (1.00) | `TSpawn` | `INSUFFICIENT_EVIDENCE` | `[1240.0, -1159.9, -246.4]` | 974u | 247 / 140d / 167p | 4.44s | 0.62 |
| 29 | `tr_exec_a_site_default` | TR | Execute | A | `[-400.0, -2100.0, -170.0]` | `BombsiteA` (1.00) | `BombsiteA` | `SMALL_ADJUSTMENT` | `[-418.8, -2010.5, -180.0]` | 92u | 48 / 43d / 45p | 3.25s | 0.49 |
| 30 | `tr_exec_a_triple_clear` | TR | Execute | A | `[-550.0, -2000.0, -170.0]` | `BombsiteA` (1.00) | `BombsiteA` | `VALID` | — (manter atual) | 0u | 109 / 99d / 107p | 3.25s | 0.80 |
| 31 | `tr_exec_a_stairs_clear` | TR | Execute | A | `[-300.0, -1900.0, -170.0]` | `BombsiteA` (1.00) | `BombsiteA`, `Stairs`, `Jungle` | `SMALL_ADJUSTMENT` | `[-418.8, -2010.5, -180.0]` | 163u | 48 / 43d / 45p | 3.25s | 0.49 |
| 32 | `tr_exec_mid_connector_push` | TR | Execute | Mid | `[-750.0, -850.0, -160.0]` | `Connector` (0.53) | `Connector`, `Middle` | `SMALL_ADJUSTMENT` | `[-801.5, -916.9, -168.0]` | 85u | 53 / 39d / 40p | 2.62s | 0.53 |
| 33 | `tr_exec_b_site_plant` | TR | Execute | B | `[-1850.0, 350.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB` | `SMALL_ADJUSTMENT` | `[-1927.1, 319.3, -160.0]` | 83u | 36 / 33d / 33p | 2.56s | 0.49 |
| 34 | `tr_exec_b_van_clear` | TR | Execute | B | `[-1350.0, 350.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB`, `Truck` | `INSUFFICIENT_EVIDENCE` | `[-1987.8, 431.4, -160.0]` | 643u | 135 / 99d / 113p | 3.25s | 0.48 |
| 35 | `tr_exec_b_market_push` | TR | Execute | B | `[-1750.0, 200.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB`, `Shop` | `SMALL_ADJUSTMENT` | `[-1927.1, 319.3, -160.0]` | 214u | 36 / 33d / 33p | 2.56s | 0.49 |
| 36 | `ct_retake_a_connector` | CT | Staging, Retake | A | `[-450.0, -1600.0, -160.0]` | `BombsiteA` (1.00) | `Connector` | `WRONG_HEIGHT` | `[-802.4, -1221.3, -168.0]` | 517u | 44 / 28d / 28p | 2.38s | 0.52 |
| 37 | `ct_retake_a_stairs` | CT | Staging, Retake | A | `[-300.0, -1700.0, -160.0]` | `BombsiteA` (1.00) | `Stairs`, `BombsiteA` | `SMALL_ADJUSTMENT` | `[-264.0, -1504.0, -164.0]` | 199u | 148 / 67d / 71p | 3.91s | 0.63 |
| 38 | `ct_retake_a_jungle` | CT | Staging, Retake | A | `[-950.0, -450.0, -140.0]` | `Catwalk` (0.50) | `Jungle` | `WRONG_SECTOR` | `[-1016.2, -1527.6, -163.8]` | 1080u | 69 / 47d / 48p | 2.50s | 0.52 |
| 39 | `ct_retake_a_ticket` | CT | Staging, Retake | A | `[-700.0, -2200.0, -180.0]` | `BombsiteA` (1.00) | `BombsiteA`, `CTSpawn` | `VALID` | — (manter atual) | 0u | 95 / 55d / 60p | 2.62s | 0.71 |
| 40 | `ct_retake_a_defuse_cover` | CT | Execute, Defuse, Retake | A | `[-400.0, -2100.0, -170.0]` | `BombsiteA` (1.00) | `BombsiteA` | `SMALL_ADJUSTMENT` | `[-289.8, -2161.5, -173.9]` | 126u | 265 / 132d / 147p | 3.50s | 0.77 |
| 41 | `ct_retake_b_market` | CT | Staging, Retake | B | `[-1750.0, 200.0, -160.0]` | `BombsiteB` (1.00) | `Shop`, `BombsiteB` | `SMALL_ADJUSTMENT` | `[-1927.1, 319.3, -160.0]` | 214u | 66 / 32d / 34p | 2.62s | 0.49 |
| 42 | `ct_retake_b_short` | CT | Staging, Retake | B | `[-1100.0, 250.0, -160.0]` | `Catwalk` (1.00) | `Catwalk`, `BombsiteB` | `VALID` | — (manter atual) | 0u | 62 / 48d / 49p | 2.56s | 0.70 |
| 43 | `ct_retake_b_entry` | CT | Execute, Retake | B | `[-1550.0, 350.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB` | `INSUFFICIENT_EVIDENCE` | `[-2494.8, 266.4, -168.0]` | 948u | 158 / 91d / 102p | 2.91s | 0.47 |
| 44 | `ct_retake_b_defuse_cover` | CT | Execute, Defuse, Retake | B | `[-1750.0, 320.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB` | `SMALL_ADJUSTMENT` | `[-1927.1, 319.3, -160.0]` | 177u | 66 / 32d / 34p | 2.62s | 0.49 |
| 45 | `ct_retake_b_awp_cover` | CT | Staging, Retake, FlankWatch | B | `[-1950.0, 250.0, -160.0]` | `BombsiteB` (1.00) | `BombsiteB`, `Shop` | `INSUFFICIENT_EVIDENCE` | `[-2017.4, -599.8, -168.0]` | 852u | 103 / 65d / 67p | 3.44s | 0.41 |

---

## 3. Comandos `setpos` para Inspeção Visual no CS2 (Antes vs. Depois)

Para inspecionar manualmente no servidor local ou cliente CS2 (`sv_cheats 1`), copie e cole os comandos abaixo no console (`~`):

### 3.1. Spots Críticos com `WRONG_SECTOR` ou `WRONG_HEIGHT` (Substituição Obrigatória)

#### `ct_a_ticket_passive` — Ticket / Cabine CT (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Shop (pureza 1.0), esperado=['BombsiteA', 'CTSpawn'] | Deslocamento proposto: **2020.7u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `1353` holds em `336` demos (`75.7%`), `499` jogadores, dwell mediano `4.0s`, confiança `0.945`.
```text
// ATUAL (cai em Shop):
setpos -1930.0 -680.0 -160.0; setang 0 60.0 0
// PROPOSTO (Medoid real em BombsiteA):
setpos -1011.5 -2479.9 -168.0; setang 0 60.0 0
```

#### `ct_a_firebox_oneanddone` — Firebox (One & Done) (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Ladder (pureza 0.6), esperado=['BombsiteA'] | Deslocamento proposto: **2291.6u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `180` holds em `128` demos (`28.8%`), `140` jogadores, dwell mediano `14.56s`, confiança `0.769`.
```text
// ATUAL (cai em Ladder):
setpos -1050.0 -240.0 -160.0; setang 0 110.0 0
// PROPOSTO (Medoid real em BombsiteA):
setpos -284.2 -2399.9 -164.0; setang 0 110.0 0
```

#### `ct_a_ninja_hide` — Ninja / Atrás da Tripla (`WRONG_SECTOR`)
- **Diagnóstico**: place real=SnipersNest (pureza 1.0), esperado=['BombsiteA'] | Deslocamento proposto: **2228.9u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `272` holds em `145` demos (`32.7%`), `175` jogadores, dwell mediano `2.78s`, confiança `0.779`.
```text
// ATUAL (cai em SnipersNest):
setpos -1320.0 -290.0 -160.0; setang 0 120.0 0
// PROPOSTO (Medoid real em BombsiteA):
setpos -439.8 -2337.7 -168.0; setang 0 120.0 0
```

#### `ct_a_triple_jiggle` — Caixa Tripla (Jiggle) (`WRONG_SECTOR`)
- **Diagnóstico**: place real=SnipersNest (pureza 0.9), esperado=['BombsiteA'] | Deslocamento proposto: **1726.5u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `741` holds em `268` demos (`60.4%`), `389` jogadores, dwell mediano `2.75s`, confiança `0.935`.
```text
// ATUAL (cai em SnipersNest):
setpos -1150.0 -460.0 -160.0; setang 0 100.0 0
// PROPOSTO (Medoid real em BombsiteA):
setpos -710.8 -2129.6 -180.0; setang 0 100.0 0
```

#### `ct_a_stairs_cross` — Degraus / Cabecinha (`WRONG_SECTOR`)
- **Diagnóstico**: place real=SnipersNest (pureza 1.0), esperado=['Stairs'] | Deslocamento proposto: **915.1u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `795` holds em `298` demos (`67.1%`), `441` jogadores, dwell mediano `2.5s`, confiança `0.916`.
```text
// ATUAL (cai em SnipersNest):
setpos -1100.0 -620.0 -160.0; setang 0 80.0 0
// PROPOSTO (Medoid real em Stairs):
setpos -497.8 -1309.0 -160.0; setang 0 80.0 0
```

#### `ct_a_jungle_support` — Ligação / Jungle (`WRONG_SECTOR`)
- **Diagnóstico**: place real=SnipersNest (pureza 1.0), esperado=['Jungle'] | Deslocamento proposto: **584.9u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `227` holds em `158` demos (`35.6%`), `187` jogadores, dwell mediano `2.5s`, confiança `0.836`.
```text
// ATUAL (cai em SnipersNest):
setpos -1250.0 -780.0 -160.0; setang 0 70.0 0
// PROPOSTO (Medoid real em Jungle):
setpos -992.1 -1304.9 -155.6; setang 0 70.0 0
```

#### `ct_a_palace_close_poke` — Debaixo do Palácio (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Catwalk (pureza 0.87), esperado=['BombsiteA', 'Scaffolding'] | Deslocamento proposto: **1899.0u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `661` holds em `241` demos (`54.3%`), `318` jogadores, dwell mediano `3.06s`, confiança `0.935`.
```text
// ATUAL (cai em Catwalk):
setpos -880.0 -320.0 -160.0; setang 0 140.0 0
// PROPOSTO (Medoid real em BombsiteA):
setpos 151.9 -1914.1 -168.0; setang 0 140.0 0
```

#### `ct_mid_window_crouch` — Janela Meio (Agachado) (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Ladder (pureza 0.8), esperado=['SnipersNest'] | Deslocamento proposto: **257.4u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `588` holds em `256` demos (`57.7%`), `367` jogadores, dwell mediano `3.0s`, confiança `0.919`.
```text
// ATUAL (cai em Ladder):
setpos -1380.0 -540.0 -120.0; setang 0 -20.0 0
// PROPOSTO (Medoid real em SnipersNest):
setpos -1139.4 -462.3 -168.0; setang 0 -20.0 0
```

#### `ct_mid_window_deep_awp` — Janela Fundo (AWP) (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Shop (pureza 1.0), esperado=['SnipersNest'] | Deslocamento proposto: **356.3u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `96` holds em `70` demos (`15.8%`), `73` jogadores, dwell mediano `3.53s`, confiança `0.608`.
```text
// ATUAL (cai em Shop):
setpos -1480.0 -560.0 -100.0; setang 0 -25.0 0
// PROPOSTO (Medoid real em SnipersNest):
setpos -1175.8 -732.5 -168.0; setang 0 -25.0 0
```

#### `ct_mid_connector_headshot` — Conector Degrau (Headshot) (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Middle (pureza 0.9), esperado=['Connector'] | Deslocamento proposto: **332.9u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `759` holds em `299` demos (`67.3%`), `438` jogadores, dwell mediano `3.5s`, confiança `0.947`.
```text
// ATUAL (cai em Middle):
setpos -820.0 -840.0 -160.0; setang 0 -50.0 0
// PROPOSTO (Medoid real em Connector):
setpos -520.0 -984.0 -168.0; setang 0 -50.0 0
```

#### `ct_mid_short_catwalk` — Short / Catwalk (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Connector (pureza 0.8), esperado=['Catwalk'] | Deslocamento proposto: **1129.6u** | Resolução: `NEEDS_VISUAL_CONFIRMATION`
- **Evidência do Medoid Proposto**: `342` holds em `214` demos (`48.2%`), `269` jogadores, dwell mediano `2.72s`, confiança `0.727`.
```text
// ATUAL (cai em Connector):
setpos -950.0 -1050.0 -140.0; setang 0 -40.0 0
// PROPOSTO (Medoid real em Catwalk):
setpos -906.4 78.5 -166.0; setang 0 -40.0 0
```

#### `ct_mid_underpass_peek` — Beco / Saída do Rato (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Connector (pureza 1.0), esperado=['Underpass', 'Ladder'] | Deslocamento proposto: **1337.1u** | Resolução: `NEEDS_VISUAL_CONFIRMATION`
- **Evidência do Medoid Proposto**: `713` holds em `270` demos (`60.8%`), `372` jogadores, dwell mediano `3.06s`, confiança `0.729`.
```text
// ATUAL (cai em Connector):
setpos -720.0 -1020.0 -220.0; setang 0 40.0 0
// PROPOSTO (Medoid real em Underpass):
setpos -983.5 289.8 -166.7; setang 0 40.0 0
```

#### `ct_b_van_peek` — Van B (Jiggle Peek) (`WRONG_SECTOR`)
- **Diagnóstico**: place real=BombsiteB (pureza 1.0), esperado=['Truck'] | Deslocamento proposto: **906.2u** | Resolução: `RESOLVED_UNIQUE_PLACE`
- **Evidência do Medoid Proposto**: `972` holds em `302` demos (`68.0%`), `450` jogadores, dwell mediano `3.56s`, confiança `0.958`.
```text
// ATUAL (cai em BombsiteB):
setpos -1350.0 380.0 -150.0; setang 0 -85.0 0
// PROPOSTO (Medoid real em Truck):
setpos -2191.6 712.6 -101.8; setang 0 -85.0 0
```

#### `ct_b_market_window` — Janela do Mercado B (`WRONG_SECTOR`)
- **Diagnóstico**: place real=BombsiteB (pureza 1.0), esperado=['Shop'] | Deslocamento proposto: **750.4u** | Resolução: `NEEDS_VISUAL_CONFIRMATION`
- **Evidência do Medoid Proposto**: `71` holds em `53` demos (`11.9%`), `55` jogadores, dwell mediano `3.0s`, confiança `0.303`.
```text
// ATUAL (cai em BombsiteB):
setpos -1880.0 180.0 -130.0; setang 0 -45.0 0
// PROPOSTO (Medoid real em Shop):
setpos -1756.8 -560.2 -128.0; setang 0 -45.0 0
```

#### `ct_spawn_safe` — Recuo Seguro Base CT (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Shop (pureza 1.0), esperado=['CTSpawn'] | Deslocamento proposto: **788.5u** | Resolução: `NEEDS_VISUAL_CONFIRMATION`
- **Evidência do Medoid Proposto**: `730` holds em `279` demos (`62.8%`), `397` jogadores, dwell mediano `2.66s`, confiança `0.727`.
```text
// ATUAL (cai em Shop):
setpos -2050.0 -800.0 -160.0; setang 0 0.0 0
// PROPOSTO (Medoid real em CTSpawn):
setpos -1279.6 -967.9 -168.0; setang 0 0.0 0
```

#### `tr_staging_a_ramp` — Staging: Rampa A / Caverna (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Catwalk (pureza 1.0), esperado=['TRamp'] | Deslocamento proposto: **1612.7u** | Resolução: `RESOLVED_UNIQUE_PLACE`
- **Evidência do Medoid Proposto**: `750` holds em `300` demos (`67.6%`), `471` jogadores, dwell mediano `2.81s`, confiança `0.926`.
```text
// ATUAL (cai em Catwalk):
setpos -250.0 -200.0 -160.0; setang 0 -135.0 0
// PROPOSTO (Medoid real em TRamp):
setpos 321.1 -1708.1 -176.0; setang 0 -135.0 0
```

#### `tr_staging_palace_room` — Staging: Sala do Palácio (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Catwalk (pureza 0.77), esperado=['PalaceInterior'] | Deslocamento proposto: **1998.7u** | Resolução: `NEEDS_VISUAL_CONFIRMATION`
- **Evidência do Medoid Proposto**: `889` holds em `306` demos (`68.9%`), `484` jogadores, dwell mediano `2.88s`, confiança `0.715`.
```text
// ATUAL (cai em Catwalk):
setpos -350.0 -480.0 -90.0; setang 0 -140.0 0
// PROPOSTO (Medoid real em PalaceInterior):
setpos 288.1 -2373.4 -40.0; setang 0 -140.0 0
```

#### `tr_staging_underpass_top` — Staging: Entrada do Rato (`WRONG_SECTOR`)
- **Diagnóstico**: place real=TopofMid (pureza 1.0), esperado=['Middle', 'Underpass'] | Deslocamento proposto: **1236.0u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `772` holds em `312` demos (`70.3%`), `521` jogadores, dwell mediano `2.56s`, confiança `0.916`.
```text
// ATUAL (cai em TopofMid):
setpos 150.0 -1050.0 -160.0; setang 0 -160.0 0
// PROPOSTO (Medoid real em Middle):
setpos -1038.9 -728.5 -264.0; setang 0 -160.0 0
```

#### `ct_retake_a_connector` — Retake A: Conector (`WRONG_HEIGHT`)
- **Diagnóstico**: XY caminhavel, mas Z=-160 fora das alturas observadas [-48, -16, 16] | Deslocamento proposto: **517.4u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `44` holds em `28` demos (`6.3%`), `28` jogadores, dwell mediano `2.38s`, confiança `0.515`.
```text
// ATUAL (cai em BombsiteA):
setpos -450.0 -1600.0 -160.0; setang 0 0.0 0
// PROPOSTO (Medoid real em Connector):
setpos -802.4 -1221.3 -168.0; setang 0 0.0 0
```

#### `ct_retake_a_jungle` — Retake A: Selva (`WRONG_SECTOR`)
- **Diagnóstico**: place real=Catwalk (pureza 0.5), esperado=['Jungle'] | Deslocamento proposto: **1079.9u** | Resolução: `RESOLVED_LANDMARK_SUBREGION`
- **Evidência do Medoid Proposto**: `69` holds em `47` demos (`10.6%`), `48` jogadores, dwell mediano `2.5s`, confiança `0.518`.
```text
// ATUAL (cai em Catwalk):
setpos -950.0 -450.0 -140.0; setang 0 10.0 0
// PROPOSTO (Medoid real em Jungle):
setpos -1016.2 -1527.6 -163.8; setang 0 10.0 0
```

### 3.2. Spots com `SMALL_ADJUSTMENT` ou `INSUFFICIENT_EVIDENCE` (Ajuste Fino / Revisão)

#### `ct_b_site_default_crouch` — Caixa Plant B (Default) (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 178.1u com 87 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteB):
setpos -1750.0 300.0 -160.0; setang 0 -80.0 0
// CANDIDATO PROPOSTO (shift 178.1u, 87 demos):
setpos -1927.1 319.3 -160.0; setang 0 -80.0 0
```

#### `ct_b_market_door` — Porta do Mercado B (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 244.7u com 56 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteB):
setpos -1650.0 220.0 -160.0; setang 0 -60.0 0
// CANDIDATO PROPOSTO (shift 244.6u, 56 demos):
setpos -1428.3 116.8 -164.2; setang 0 -60.0 0
```

#### `tr_staging_top_mid_boxes` — Staging: Caixas Top Mid (`INSUFFICIENT_EVIDENCE`)
- **Diagnóstico**: apenas 4 demos com hold compativel em 96u | Resolução: `PROPOSED_NEAREST_CLUSTER_FOR_LOW_EVIDENCE`
```text
// ATUAL (TopofMid):
setpos 450.0 -950.0 -160.0; setang 0 -170.0 0
// CANDIDATO PROPOSTO (shift 792.2u, 336 demos):
setpos 176.4 -206.6 -152.0; setang 0 -170.0 0
```

#### `tr_staging_b_apartments_house` — Staging: Fundo dos Apartamentos B (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 116.6u com 94 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BackAlley):
setpos -350.0 650.0 -60.0; setang 0 180.0 0
// CANDIDATO PROPOSTO (shift 114.7u, 94 demos):
setpos -464.0 654.0 -72.0; setang 0 180.0 0
```

#### `tr_staging_t_roof` — Staging: Telhado TR (`INSUFFICIENT_EVIDENCE`)
- **Diagnóstico**: apenas 0 demos com hold compativel em 96u | Resolução: `PROPOSED_NEAREST_CLUSTER_FOR_LOW_EVIDENCE`
```text
// ATUAL (TopofMid):
setpos 750.0 -750.0 -100.0; setang 0 175.0 0
// CANDIDATO PROPOSTO (shift 801.7u, 293 demos):
setpos 814.9 -1549.0 -109.0; setang 0 175.0 0
```

#### `tr_spawn_safe` — Recuo Seguro Base TR (`INSUFFICIENT_EVIDENCE`)
- **Diagnóstico**: apenas 3 demos com hold compativel em 96u | Resolução: `PROPOSED_NEAREST_CLUSTER_FOR_LOW_EVIDENCE`
```text
// ATUAL (TSpawn):
setpos 1100.0 -200.0 -160.0; setang 0 180.0 0
// CANDIDATO PROPOSTO (shift 973.9u, 140 demos):
setpos 1240.0 -1159.9 -246.4; setang 0 180.0 0
```

#### `tr_exec_a_site_default` — Exec: Plant Default A (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 93.6u com 43 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteA):
setpos -400.0 -2100.0 -170.0; setang 0 -90.0 0
// CANDIDATO PROPOSTO (shift 92.0u, 43 demos):
setpos -418.8 -2010.5 -180.0; setang 0 -90.0 0
```

#### `tr_exec_a_stairs_clear` — Exec: Domínio Degraus / Jungle (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 163.5u com 43 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteA):
setpos -300.0 -1900.0 -170.0; setang 0 -150.0 0
// CANDIDATO PROPOSTO (shift 162.6u, 43 demos):
setpos -418.8 -2010.5 -180.0; setang 0 -150.0 0
```

#### `tr_exec_mid_connector_push` — Exec: Avanço Conector Meio (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 85.9u com 39 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (Connector):
setpos -750.0 -850.0 -160.0; setang 0 -140.0 0
// CANDIDATO PROPOSTO (shift 84.8u, 39 demos):
setpos -801.5 -916.9 -168.0; setang 0 -140.0 0
```

#### `tr_exec_b_site_plant` — Exec: Plant Default B (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 83.0u com 33 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteB):
setpos -1850.0 350.0 -160.0; setang 0 45.0 0
// CANDIDATO PROPOSTO (shift 83.0u, 33 demos):
setpos -1927.1 319.3 -160.0; setang 0 45.0 0
```

#### `tr_exec_b_van_clear` — Exec: Limpeza da Van B (`INSUFFICIENT_EVIDENCE`)
- **Diagnóstico**: apenas 5 demos com hold compativel em 96u | Resolução: `PROPOSED_NEAREST_CLUSTER_FOR_LOW_EVIDENCE`
```text
// ATUAL (BombsiteB):
setpos -1350.0 350.0 -160.0; setang 0 120.0 0
// CANDIDATO PROPOSTO (shift 643.0u, 99 demos):
setpos -1987.8 431.4 -160.0; setang 0 120.0 0
```

#### `tr_exec_b_market_push` — Exec: Pressão Janela/Porta Mercado (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 213.5u com 33 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteB):
setpos -1750.0 200.0 -160.0; setang 0 80.0 0
// CANDIDATO PROPOSTO (shift 213.5u, 33 demos):
setpos -1927.1 319.3 -160.0; setang 0 80.0 0
```

#### `ct_retake_a_stairs` — Retake A: Degraus / Jungle (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 199.4u com 67 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteA):
setpos -300.0 -1700.0 -160.0; setang 0 -30.0 0
// CANDIDATO PROPOSTO (shift 199.3u, 67 demos):
setpos -264.0 -1504.0 -164.0; setang 0 -30.0 0
```

#### `ct_retake_a_defuse_cover` — Retake A: Defuse Cover Site (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 126.4u com 132 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteA):
setpos -400.0 -2100.0 -170.0; setang 0 -90.0 0
// CANDIDATO PROPOSTO (shift 126.3u, 132 demos):
setpos -289.8 -2161.5 -173.9; setang 0 -90.0 0
```

#### `ct_retake_b_market` — Retake B: Mercado / Cozinha (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 213.5u com 32 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteB):
setpos -1750.0 200.0 -160.0; setang 0 0.0 0
// CANDIDATO PROPOSTO (shift 213.5u, 32 demos):
setpos -1927.1 319.3 -160.0; setang 0 0.0 0
```

#### `ct_retake_b_entry` — Retake B: Entrada do Site (`INSUFFICIENT_EVIDENCE`)
- **Diagnóstico**: apenas 4 demos com hold compativel em 96u | Resolução: `PROPOSED_NEAREST_CLUSTER_FOR_LOW_EVIDENCE`
```text
// ATUAL (BombsiteB):
setpos -1550.0 350.0 -160.0; setang 0 -60.0 0
// CANDIDATO PROPOSTO (shift 948.5u, 91 demos):
setpos -2494.8 266.4 -168.0; setang 0 -60.0 0
```

#### `ct_retake_b_defuse_cover` — Retake B: Cobertura Defuse (`SMALL_ADJUSTMENT`)
- **Diagnóstico**: pico profissional a 177.1u com 32 demos | Resolução: `RESOLVED_NEAREST_PEAK`
```text
// ATUAL (BombsiteB):
setpos -1750.0 320.0 -160.0; setang 0 -80.0 0
// CANDIDATO PROPOSTO (shift 177.1u, 32 demos):
setpos -1927.1 319.3 -160.0; setang 0 -80.0 0
```

#### `ct_retake_b_awp_cover` — Retake B: Suporte AWP (`INSUFFICIENT_EVIDENCE`)
- **Diagnóstico**: apenas 0 demos com hold compativel em 96u | Resolução: `PROPOSED_NEAREST_CLUSTER_FOR_LOW_EVIDENCE`
```text
// ATUAL (BombsiteB):
setpos -1950.0 250.0 -160.0; setang 0 -30.0 0
// CANDIDATO PROPOSTO (shift 852.5u, 65 demos):
setpos -2017.4 -599.8 -168.0; setang 0 -30.0 0
```

### 3.3. Spots `VALID` (Confirmados — Manter Inalterados)

- **`ct_b_bench_deep`** (Banco / Floreira B): `[-1950.0, 450.0, -160.0]` em `BombsiteB` — cluster profissional 31 a 42.1u (`setpos -1950.0 450.0 -160.0; setang 0 -60.0 0`)
- **`ct_b_short_corner`** (Canto do L (Short)): `[-1050.0, 250.0, -160.0]` em `Catwalk` — posicao propria com evidencia (229 demos) mesmo fora de pico (`setpos -1050.0 250.0 -160.0; setang 0 -100.0 0`)
- **`ct_jungle_safe`** (Recuo Seguro Jungle): `[-1350.0, -850.0, -160.0]` em `CTSpawn` — evidencia local moderada (37 demos) (`setpos -1350.0 -850.0 -160.0; setang 0 45.0 0`)
- **`tr_staging_b_apartments_kitchen`** (Staging: Cozinha do Tapete B): `[-850.0, 600.0, -60.0]` em `BackAlley` — cluster profissional 211 a 59.1u (`setpos -850.0 600.0 -60.0; setang 0 170.0 0`)
- **`tr_exec_a_triple_clear`** (Exec: Limpeza Tripla A): `[-550.0, -2000.0, -170.0]` em `BombsiteA` — cluster profissional 65 a 56.0u (`setpos -550.0 -2000.0 -170.0; setang 0 -120.0 0`)
- **`ct_retake_a_ticket`** (Retake A: CT Spawn / Cabine): `[-700.0, -2200.0, -180.0]` em `BombsiteA` — posicao propria com evidencia (55 demos) mesmo fora de pico (`setpos -700.0 -2200.0 -180.0; setang 0 45.0 0`)
- **`ct_retake_b_short`** (Retake B: Catwalk / L): `[-1100.0, 250.0, -160.0]` em `Catwalk` — posicao propria com evidencia (48 demos) mesmo fora de pico (`setpos -1100.0 250.0 -160.0; setang 0 -45.0 0`)
