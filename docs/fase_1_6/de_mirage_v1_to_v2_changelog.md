# Changelog de Atualização — Perfil Mirage V1 -> V2 (Fase 1.6)

- **Arquivo**: `src/CsBotManager/MapProfiles/de_mirage.json`
- **Versão Anterior**: `1` | **SHA-256 V1**: `f105573d0a62a9f0b140c01ad6a5b24b7ae40a03c2ec6c2feb9d787b9a6e0fff`
- **Versão Nova**: `2` | **SHA-256 V2**: `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`
- **Backup**: `src/CsBotManager/MapProfiles/backups/de_mirage.v1_backup.json`
- **Spots Atualizados**: **20** (apenas `APPROVED`)
- **Spots Mantidos Inalterados**: **25** (7 `VALID` + 12 `SMALL_ADJUSTMENT` + 6 `INSUFFICIENT_EVIDENCE`)

## Tabela de Modificações dos Spots Aprovados

| SpotId | Nome | OldPosition | NewPosition | Valve Place (Old -> New) | Landmark Visual |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ct_a_ticket_passive` | Ticket / Cabine CT | `[-1011.5, -2479.9, -168.0]` | `[-1011.5, -2479.9, -168.0]` | `Shop` -> `CTSpawn` | Atras da cabine/caixa do Ticket CT olhando para Rampa A |
| `ct_a_firebox_oneanddone` | Firebox (One & Done) | `[-284.2, -2399.9, -164.0]` | `[-284.2, -2399.9, -164.0]` | `Ladder` -> `BombsiteA` | Canto fechado da Firebox no Bomb A marcando Palacio |
| `ct_a_ninja_hide` | Ninja / Atrás da Tripla | `[-439.8, -2337.7, -168.0]` | `[-439.8, -2337.7, -168.0]` | `SnipersNest` -> `BombsiteA` | Recanto escondido do Ninja atras da caixa Tripla no Bomb A |
| `ct_a_triple_jiggle` | Caixa Tripla (Jiggle) | `[-710.8, -2129.6, -180.0]` | `[-710.8, -2129.6, -180.0]` | `SnipersNest` -> `BombsiteA` | Borda da Caixa Tripla no Bomb A com jiggle para Rampa/Conector |
| `ct_a_stairs_cross` | Degraus / Cabecinha | `[-497.8, -1309.0, -160.0]` | `[-497.8, -1309.0, -160.0]` | `SnipersNest` -> `Stairs` | Base dos degraus da Cabecinha (Stairs) no Bomb A |
| `ct_a_jungle_support` | Ligação / Jungle | `[-992.1, -1304.9, -155.6]` | `[-992.1, -1304.9, -155.6]` | `SnipersNest` -> `Jungle` | Interior da Jungle do Bomb A com visao cruzada para Rampa e Palacio |
| `ct_a_palace_close_poke` | Debaixo do Palácio | `[151.9, -1914.1, -168.0]` | `[151.9, -1914.1, -168.0]` | `Catwalk` -> `BombsiteA` | Piso terreo debaixo da varanda do Palacio (Under-Palace) no Bomb A |
| `ct_mid_window_crouch` | Janela Meio (Agachado) | `[-1139.4, -462.3, -168.0]` | `[-1139.4, -462.3, -168.0]` | `Ladder` -> `SnipersNest` | Parapeito frontal da Janela do Meio (SnipersNest) agachado |
| `ct_mid_window_deep_awp` | Janela Fundo (AWP) | `[-1175.8, -732.5, -168.0]` | `[-1175.8, -732.5, -168.0]` | `Shop` -> `SnipersNest` | Recuo seguro no fundo da Janela do Meio com AWP |
| `ct_mid_connector_headshot` | Conector Degrau (Headshot) | `[-520.0, -984.0, -168.0]` | `[-520.0, -984.0, -168.0]` | `Middle` -> `Connector` | Primeiro degrau com cobertura de headshot dentro do Conector |
| `ct_mid_short_catwalk` | Short / Catwalk | `[-906.4, 78.5, -166.0]` | `[-906.4, 78.5, -166.0]` | `Connector` -> `Catwalk` | Passarela do Catwalk / Short cobrindo Meio e saida do Rato |
| `ct_mid_underpass_peek` | Beco / Saída do Rato | `[-737.1, -21.0, -144.0]` | `[-737.1, -21.0, -144.0]` | `Connector` -> `Underpass` | Saida da rampa do Underpass / Beco do Rato em direcao ao Meio |
| `ct_b_van_peek` | Van B (Jiggle Peek) | `[-2191.6, 712.6, -101.8]` | `[-2191.6, 712.6, -101.8]` | `BombsiteB` -> `Truck` | Em cima / quina da Van no Bomb B vigiando Tapete |
| `ct_b_market_window` | Janela do Mercado B | `[-2017.4, -599.8, -168.0]` | `[-1912.8, 5.1, -168.0]` | `BombsiteB` -> `BombsiteB` | Quina defensiva da Janela do Mercado no Bomb B segurando avanco vindo do Mercado (Cluster 32 medoid, Y=+5.1 preserva invariante Y>0 de B) |
| `ct_spawn_safe` | Recuo Seguro Base CT | `[-1279.6, -967.9, -168.0]` | `[-1279.6, -967.9, -168.0]` | `Shop` -> `CTSpawn` | Recuo defensivo no interior da Base CT (CT Spawn) |
| `tr_staging_a_ramp` | Staging: Rampa A / Caverna | `[321.1, -1708.1, -176.0]` | `[321.1, -1708.1, -176.0]` | `Catwalk` -> `TRamp` | Entrada da Rampa A / Caverna TR preparando ataque |
| `tr_staging_palace_room` | Staging: Sala do Palácio | `[288.1, -2373.4, -40.0]` | `[288.1, -2373.4, -40.0]` | `Catwalk` -> `PalaceInterior` | Sala interna do Palacio (Palace Interior Z=-40) preparando rush/exec |
| `tr_staging_underpass_top` | Staging: Entrada do Rato | `[-1038.9, -728.5, -264.0]` | `[-1038.9, -728.5, -264.0]` | `TopofMid` -> `Middle` | Entrada rebaixada do Underpass / Rato pelo lado TR (Z=-264) |
| `ct_retake_a_connector` | Retake A: Conector | `[-802.4, -1221.3, -168.0]` | `[-802.4, -1221.3, -168.0]` | `BombsiteA` -> `Connector` | Entrada do Conector vindo do Meio para Retake do Bomb A |
| `ct_retake_a_jungle` | Retake A: Selva | `[-1016.2, -1527.6, -163.8]` | `[-1016.2, -1527.6, -163.8]` | `Catwalk` -> `Jungle` | Corredor da Jungle preparando entrada de retake no Bomb A |
