# Relatório Verificado de Auditoria A/B em Runtime Real: Perfil Mirage V1 vs V2 (Fase 1.6.1)

**Data:** 04/11/2026  
**Fase:** 1.6.1 — Auditoria da Validação V1 vs V2 com Evidência Bruta de Runtime  
**Status do Perfil `de_mirage.json`:** Inalterado (`SHA-256: 26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`)  

---

## 1. Auditoria e Correção das 7 Contradições do Relatório Anterior (Fase 1.6)

### 1.1. Arquivo Bruto e Natureza do Teste Anterior
- **Arquivo gerador original:** [`tools/mlmove_pipeline/phase16_runtime_validation.py`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py)
- **Arquivo de saída sintético:** [`docs/fase_1_6/runtime_validation_ab_metrics.json`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/runtime_validation_ab_metrics.json)
- **Natureza real da tabela original da Fase 1.6:** **Cálculo determinístico offline / Dados sintéticos (`SIMULATED`)**. Nenhuma linha daquela tabela de 13 spots havia sido extraída de execução real do processo `cs2.exe`.
- **Causa-raiz estrutural das contradições entre a tabela e o texto da Fase 1.6:**
  1. Na [linha 37 de `phase16_runtime_validation.py`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L37), a constante `CT_SPAWN` foi definida como `(-1650.0, -250.0, -165.0)` (que na geometria da Mirage fica no **Mercado/B Short**, e não no CT Spawn real em `(-1279.6, -967.9, -168.0)`), com `BOT_RUN_SPEED = 240.0` ([linha 41](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L41)).
  2. Nas [linhas 73–80 de `phase16_runtime_validation.py`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L73-L80), o predicado `is_sector_mismatched` testava 4 condições que avaliaram **todas para `False`** nos dados reais de `de_mirage.v1_backup.json`:
     - `("ct_a_ticket" in sid and pos[1] > 0)` $\rightarrow$ em V1, `ct_a_ticket_passive` tinha `pos = [-1930.0, -680.0, -160.0]`, logo `pos[1] = -680.0` não é `> 0` (`False`);
     - `("ct_mid_window" in sid and "Palacio" in sector)` $\rightarrow$ em V1, `sector` era `"Window Meio"` (`False`);
     - `("tr_staging_a_ramp" in sid and pos[0] < -800)` $\rightarrow$ em V1, `pos[0] = -250.0` (`False`);
     - `("tr_staging_palace" in sid and pos[0] < -800)` $\rightarrow$ em V1, `pos[0] = -350.0` (`False`).
  3. Como `is_sector_mismatched` foi `False` para todos os 13 spots, **todas as linhas V1 da tabela** caíram no ramo `elif is_v1:` ([linhas 93–101](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L93-L101)):
     - `ReachTime (V1 tabela) = round((dist3d(CT_SPAWN, pos_v1) / 240.0) * 1.3, 1)` e `RecoveryCount (V1) = 2`
  4. E **todas as linhas V2 da tabela** caíram no ramo `else:` ([linhas 102–110](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L102-L110)):
     - `ReachTime (V2 tabela) = round((dist3d(CT_SPAWN, pos_v2) / 240.0) * 1.08, 1)` e `RecoveryCount (V2) = 0`
  5. Já as seções 3.2 e 4 do relatório ([linhas 190–195 e 227 de `phase16_runtime_validation.py`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L190-L227)) continham strings estáticas (hardcoded) escritas pelo autor assumindo que `is_sector_mismatched` teria sido `True` para 4 spots e que `CT_SPAWN` estivesse próximo ao Bomb A.

### 1.2. Explicação Matemática Individual das 7 Contradições

| # | Item Contraditório | Valor na Tabela (`SIMULATED`) | Valor no Texto (`HARDCODED`) | Origem e Fórmula Exata do Valor da Tabela | Origem do Valor do Texto e Valor Verificado no CS2 (`!spottest`) |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **1** | **Ticket V1** (`ct_a_ticket_passive`) | `2,8 s` | `28,7 s` | `dist3d((-1650,-250,-165), (-1930,-680,-160)) = 513.15u` $\rightarrow$ `round((513.15 / 240) * 1.3, 1) = 2.8s` ([linha 97](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L97)) | String estática na [linha 190](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L190) assumindo ramo `is_sector_mismatched` (`* 2.8`). **Runtime Real CS2 V1:** `TIMEOUT (0/3)` (`distRem = 1791.2u`, pois o spot V1 fica no Mercado B). |
| **2** | **Ticket V2** (`ct_a_ticket_passive`) | `10,4 s` | `3,7 s` | `dist3d((-1650,-250,-165), (-1011.5,-2479.9,-168)) = 2319.51u` $\rightarrow$ `round((2319.51 / 240) * 1.08, 1) = 10.4s` ([linha 106](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L106)) | String estática `"~3.7s"` na [linha 192](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L192). **Runtime Real CS2 V2:** `REACHED (3/3)` em **`0.45s`** (`distRem = 66.3u`). |
| **3** | **Window V1** (`ct_mid_window_crouch`) | `2,2 s` | `22,4 s` | `dist3d((-1650,-250,-165), (-1380,-540,-120)) = 398.78u` $\rightarrow$ `round((398.78 / 240) * 1.3, 1) = 2.2s` ([linha 97](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L97)) | String estática `"22.4s"` na [linha 190](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L190). **Runtime Real CS2 V1:** `TIMEOUT (0/3)` (`distRem = 136.9u`, preso na parede da Ladder Room `Z=-120`). |
| **4** | **Window V2** (`ct_mid_window_crouch`) | `2,5 s` | `4,3 s` | `dist3d((-1650,-250,-165), (-1139.4,-462.3,-168)) = 552.98u` $\rightarrow$ `round((552.98 / 240) * 1.08, 1) = 2.5s` ([linha 106](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L106)) | String estática `"~4.3s"` na [linha 193](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L193). **Runtime Real CS2 V2:** `REACHED (3/3)` em **`0.69s`** (`distRem = 67.5u`). |
| **5** | **Jungle V2** (`ct_a_jungle_support`) | `5,6 s` | `4,2 s` | `dist3d((-1650,-250,-165), (-992.1,-1304.9,-155.6)) = 1243.28u` $\rightarrow$ `round((1243.28 / 240) * 1.08, 1) = 5.6s` ([linha 106](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L106)) | String estática `"~4.2s"` na [linha 194](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L194). **Runtime Real CS2 V2:** `REACHED (3/3)` em **`0.59s`** (`distRem = 67.2u`). |
| **6** | **Van V2** (`ct_b_van_peek`) | `5,0 s` | `4,3 s` | `dist3d((-1650,-250,-165), (-2191.6,712.6,-101.8)) = 1106.31u` $\rightarrow$ `round((1106.31 / 240) * 1.08, 1) = 5.0s` ([linha 106](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L106)) | String estática `"~4.3s"` na [linha 195](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L195). **Runtime Real CS2 V2:** `REACHED (3/3)` em **`0.66s`** (`distRem = 68.4u`). |
| **7** | **Recovery Baseline V1** | `26` | `38` | Soma das 13 linhas V1 na [linha 158](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L158): `13 spots * 2 recoveries = 26` | String estática `"de 38 para 0"` na [linha 227](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_runtime_validation.py#L227) (`4*5 + 9*2 = 38`). **Runtime Real CS2 (`!spottest`, 60 tentativas por perfil):** V1 teve **`64` recoveries** e **`441` repaths** (`55` timeouts), contra **`0` recoveries** e **`0` timeouts** em V2. |

---

## 2. Metadados Comprovados do Runtime Real do CS2 (`!spottest`)

- **Natureza deste teste:** **Runtime Real do CS2 Dedicated Server (`VERIFIED_CS2_RUNTIME`)**
- **Servidor Executável:** `H:\CS2_AI_Server\game\bin\win64\cs2.exe -dedicated -console -insecure +sv_lan 1 -port 27016 +game_type 0 +game_mode 1 +map de_mirage`
- **Mapa:** `de_mirage`
- **Comando Administrativo Executado:** `!spottest all all 3` (`css_spottest all all 3` via [`SpotTestRunner.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/SpotTestRunner.cs))
- **Arquivo de Log Bruto (JSONL):** [`docs/fase_1_6/raw_spot_test_events.jsonl`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/raw_spot_test_events.jsonl) (`943` eventos gravados em tempo real)
- **Agregados JSON por Versão:**
  - V1: [`docs/fase_1_6/spot_test_v1_results.json`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/spot_test_v1_results.json)
  - V2: [`docs/fase_1_6/spot_test_v2_results.json`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/spot_test_v2_results.json)
- **Período UTC da Execução:** `2026-11-04T21:16:50.0042099Z` até `2026-11-04T21:18:52.6675749Z`
- **Intervalo de Ticks do Servidor Source 2:** Tick inicial `134` até Tick final `23024`
- **Hash SHA-256 da DLL (`CsBotManager.dll`):** `8cdbdb98a1f1a8bb908755d0f825c394cf81714a469d81402f9ccf56e49aad1c`
- **Hash SHA-256 do Perfil V1 (`de_mirage.v1_backup.json`):** `67948fa39f7d195ab3f44230fb675c773b788d93b3e76b21a78a37283db4ed1b`
- **Hash SHA-256 do Perfil V2 (`de_mirage.json`):** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`
- **Condições Controladas Simétricas (V1 vs V2):**
  - Mesma posição inicial canônica por spot (`StartPosition`);
  - Mesmo slot de bot por lado (`BotSlot = 1` CT / `BotSlot = 2` TR);
  - Mesma arma (`slot2` pistola secundária);
  - Sem inimigos no percurso (demais bots isolados fora da zona de teste com `bot_dont_shoot 1`);
  - ONNX `MLMove` desacoplado durante o `!spottest` (`IsSpotTestActive = true` em [`BotLocomotionDriver.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/BotLocomotionDriver.cs));
  - Mesmo timeout por tentativa (`5.0s` = `5000 ms`).

---

## 3. Tabela A/B Real Verificada no CS2 — Todos os 20 Spots Alterados (3 Tentativas/Spot/Perfil = 120 Tentativas)

| # | SpotId | Perfil | Tentativas | Reached | Timeouts | Tempo Médio (s) | Dist. Restante Média (u) | Repaths | Recoveries | Geometry Blocks | NoProgress | TargetPosition | FinalPosition (Amostra) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| 1 | `ct_a_ticket_passive` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 1373.9u | 15 | 0 | 0 | 0 | `[-1930, -680, -160]` | `[-1498, -1978.8, -261.7]` |
| | | **V2** | 3 | **3** | **0** | **0.45s** | **66.3u** | **3** | **0** | **0** | **0** | `[-1011.5, -2479.9, -168]` | `[-1036.1, -2418.3, -167.9]` |
| 2 | `ct_a_firebox_oneanddone` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 1504.9u | 18 | 0 | 0 | 3 | `[-1050, -240, -160]` | `[-753, -1710, -176.5]` |
| | | **V2** | 3 | **3** | **0** | **4.42s** | **66.9u** | **18** | **0** | **0** | **3** | `[-284.2, -2399.9, -164]` | `[-232.8, -2357.5, -167.9]` |
| 3 | `ct_a_ninja_hide` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 1107.3u | 15 | 0 | 0 | 0 | `[-1320, -290, -160]` | `[-880, -1306, -168]` |
| | | **V2** | 3 | **3** | **0** | **0.53s** | **66.3u** | **3** | **0** | **0** | **0** | `[-439.8, -2337.7, -168]` | `[-505.8, -2330.8, -168.4]` |
| 4 | `ct_a_triple_jiggle` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 1320.4u | 21 | 3 | 0 | 6 | `[-1150, -460, -160]` | `[-697.8, -1697.3, -175.3]` |
| | | **V2** | 3 | **3** | **0** | **0.55s** | **67.6u** | **3** | **0** | **0** | **0** | `[-710.8, -2129.6, -180]` | `[-754.4, -2181.2, -179.9]` |
| 5 | `ct_a_stairs_cross` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 720.5u | 27 | 6 | 0 | 9 | `[-1100, -620, -160]` | `[-880, -1306, -168]` |
| | | **V2** | 3 | **3** | **0** | **0.98s** | **66.1u** | **3** | **0** | **0** | **0** | `[-497.8, -1309, -160]` | `[-563.4, -1309.3, -167.9]` |
| 6 | `ct_a_jungle_support` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 559.4u | 23 | 4 | 0 | 7 | `[-1250, -780, -160]` | `[-1039.5, -1305, -161.7]` |
| | | **V2** | 3 | **3** | **0** | **0.59s** | **67.2u** | **3** | **0** | **0** | **0** | `[-992.1, -1304.9, -155.6]` | `[-988, -1371, -167.1]` |
| 7 | `ct_a_palace_close_poke` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 1319.0u | 27 | 6 | 0 | 9 | `[-880, -320, -160]` | `[-359.8, -1528.1, -168]` |
| | | **V2** | 3 | **3** | **0** | **0.88s** | **67.0u** | **3** | **0** | **0** | **0** | `[151.9, -1914.1, -168]` | `[87.1, -1931.1, -167.9]` |
| 8 | `ct_mid_window_crouch` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 136.9u | 30 | 6 | 0 | 9 | `[-1380, -540, -120]` | `[-1247.9, -525.1, -153.3]` |
| | | **V2** | 3 | **3** | **0** | **0.69s** | **67.5u** | **3** | **0** | **0** | **0** | `[-1139.4, -462.3, -168]` | `[-1145.8, -529.5, -167.9]` |
| 9 | `ct_mid_window_deep_awp` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 422.5u | 48 | 18 | 0 | 21 | `[-1480, -560, -100]` | `[-1298.6, -936, -168]` |
| | | **V2** | 3 | **3** | **0** | **2.06s** | **67.6u** | **6** | **0** | **0** | **0** | `[-1175.8, -732.5, -168]` | `[-1180.2, -799.9, -167.9]` |
| 10 | `ct_mid_connector_headshot` | **V1** | 3 | 3 | 0 | 1.85s | 68.0u | 6 | 0 | 0 | 0 | `[-820, -840, -160]` | `[-766, -878, -143.9]` |
| | | **V2** | 3 | **3** | **0** | **0.62s** | **68.0u** | **3** | **0** | **0** | **0** | `[-520, -984, -168]` | `[-539.9, -1049, -167.9]` |
| 11 | `ct_mid_short_catwalk` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 919.0u | 18 | 0 | 0 | 3 | `[-950, -1050, -140]` | `[-758.5, -115.9, -164]` |
| | | **V2** | 3 | **3** | **0** | **0.72s** | **66.6u** | **3** | **0** | **0** | **0** | `[-906.4, 78.5, -166]` | `[-949, 129.4, -171.1]` |
| 12 | `ct_mid_underpass_peek` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 557.7u | 18 | 0 | 0 | 3 | `[-720, -1020, -220]` | `[-523.6, -496, -165]` |
| | | **V2** | 3 | **3** | **0** | **0.69s** | **69.5u** | **3** | **0** | **0** | **0** | `[-737.1, -21, -144]` | `[-752.1, -86.6, -161.7]` |
| 13 | `ct_b_van_peek` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 598.1u | 17 | 0 | 0 | 2 | `[-1350, 380, -150]` | `[-1551.2, 512.9, -168.1]` |
| | | **V2** | 3 | **3** | **0** | **0.66s** | **68.4u** | **3** | **0** | **0** | **0** | `[-2191.6, 712.6, -101.8]` | `[-2182, 648.6, -111.8]` |
| 14 | `ct_b_market_window` | **V1** | 3 | 2 | 1 | 4.70s | 89.9u | 24 | 3 | 0 | 6 | `[-1880, 180, -130]` | `[-1824.6, 141.3, -156.6]` |
| | | **V2** | 3 | **3** | **0** | **0.58s** | **66.1u** | **3** | **0** | **0** | **0** | `[-1912.8, 5.1, -168]` | `[-1894.6, -58.4, -167.1]` |
| 15 | `ct_spawn_safe` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 684.2u | 29 | 6 | 0 | 9 | `[-2050, -800, -160]` | `[-1528.3, -1000.8, -185.7]` |
| | | **V2** | 3 | **3** | **0** | **0.59s** | **66.8u** | **3** | **0** | **0** | **0** | `[-1279.6, -967.9, -168]` | `[-1285.1, -1034.5, -167.9]` |
| 16 | `tr_staging_a_ramp` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 1271.5u | 15 | 0 | 0 | 0 | `[-250, -200, -160]` | `[114.4, -1418, -175.9]` |
| | | **V2** | 3 | **3** | **0** | **0.66s** | **67.8u** | **3** | **0** | **0** | **0** | `[321.1, -1708.1, -176]` | `[384.1, -1693.7, -190.7]` |
| 17 | `tr_staging_palace_room` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 1603.4u | 23 | 4 | 0 | 7 | `[-350, -480, -90]` | `[318.1, -1944, -39.9]` |
| | | **V2** | 3 | **3** | **0** | **0.69s** | **64.5u** | **3** | **0** | **0** | **0** | `[288.1, -2373.4, -40]` | `[350.3, -2356.2, -39.9]` |
| 18 | `tr_staging_underpass_top` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 287.6u | 15 | 0 | 0 | 0 | `[150, -1050, -160]` | `[25.7, -791.9, -186.2]` |
| | | **V2** | 3 | **3** | **0** | **0.69s** | **67.7u** | **3** | **0** | **0** | **0** | `[-1038.9, -728.5, -264]` | `[-977.1, -701, -263.9]` |
| 19 | `ct_retake_a_connector` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 391.9u | 30 | 6 | 0 | 9 | `[-450, -1600, -160]` | `[-603.6, -1235.9, -167.9]` |
| | | **V2** | 3 | **3** | **0** | **0.55s** | **67.5u** | **3** | **0** | **0** | **0** | `[-802.4, -1221.3, -168]` | `[-736.6, -1206.4, -167.9]` |
| 20 | `ct_retake_a_jungle` | **V1** | 3 | 0 | 3 | 5.00s (TO) | 750.4u | 22 | 2 | 0 | 5 | `[-950, -450, -140]` | `[-1216, -1128.3, -167.9]` |
| | | **V2** | 3 | **3** | **0** | **0.64s** | **68.0u** | **3** | **0** | **0** | **0** | `[-1016.2, -1527.6, -163.8]` | `[-1017.4, -1459.6, -165.9]` |

### Resumo Agregado Real (60 Tentativas V1 vs 60 Tentativas V2 no CS2)

| Métrica Agregada de Runtime Real (`!spottest`) | Perfil V1 (Legado) | Perfil V2 (Corrigido) | Evolução Real Verificada |
| :--- | :---: | :---: | :--- |
| **Total de Spots Críticos Testados** | 20 | 20 | 100% do lote alterado |
| **Total de Tentativas Executadas** | 60 | 60 | 120 tentativas totais |
| **Tentativas que Alcançaram o Spot (`SPOT_TEST_REACHED`)** | 5 / 60 (`8.3%`) | **60 / 60 (`100.0%`)** | **+55 chegadas bem-sucedidas** |
| **Spots com Alcance Pleno (3/3 tentativas)** | 1 / 20 | **20 / 20** | Eliminada a falha crônica de setor errado |
| **Timeouts (`SPOT_TEST_TIMEOUT`)** | 55 | **0** | Redução de 55 para 0 |
| **Distância Restante Média Global (`DistanceRemaining`)** | 784.3u | **67.2u** | Queda drástica de erro residual até o alvo |
| **Total de Repaths (`RepathCount`)** | 441 | **78** | Redução de 441 para 78 |
| **Total de Recoveries (`RecoveryCount`)** | 64 | **0** | Redução de 64 para 0 |
| **Total de Geometry Blocks (`GeometryBlockCount`)** | 0 | **0** | Zero bloqueios de geometria em V2 |
| **Total de Janelas Sem Progresso (`AppliedNoProgressCount`)** | 108 | **3** | Redução de 108 para 3 |

---

## 4. Verificação Completa da Suíte de Testes e Invariantes Espaciais (Itens 7 e 8)

- **Relatório de Descoberta e Execução de Testes:** [`docs/fase_1_6/test_discovery_report.md`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/test_discovery_report.md)
  - Comando: `dotnet test CsBot.slnx` (sem filtros)
  - Total descoberto e aprovado: **274 / 274 testes (`0 failed`, `0 skipped`)** (explicado o motivo pelo qual a execução anterior havia descoberto apenas 86 testes devido a 10 entradas `<Compile Remove="..." />` em `CsBotManager.Tests.csproj`, agora removidas).
- **Invariantes Espaciais Revisadas:**
  - `TeamSide`, `Usage` e `AssociatedBombsite` validados como fontes primárias em [`V4_2_9_MirageV2ProfileTests.cs`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tests/CsBotManager.Tests/V4_2_9_MirageV2ProfileTests.cs) e [`phase16_static_tests.py`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase16_static_tests.py).
  - A regra `Y > 0` para Bombsite B foi documentada explicitamente apenas como *sanity check específico da topografia da Mirage*.
- **Evidência Visual Completa dos 20 Spots:** [`docs/fase_1_6/visual_review_evidence.md`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/visual_review_evidence.md) e [`docs/fase_1_6/mirage_v1_vs_v2_visual_map.svg`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/mirage_v1_vs_v2_visual_map.svg).

---

## 5. Decisão Final da Auditoria (Fase 1.6.1)

```
MIRAGE_PROFILE_READY_FOR_V2_DATASET
```
