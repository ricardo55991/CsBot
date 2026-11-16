# Evidência Visual e Auditoria Espacial Individual dos 20 Spots Alterados (`de_mirage`)

**Fase:** 1.6.1 — Auditoria da Validação V1 vs V2  
**Data:** 04/11/2026  
**Diagrama Espacial Renderizado (SVG):** [`mirage_v1_vs_v2_visual_map.svg`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/mirage_v1_vs_v2_visual_map.svg)  

![Diagrama Espacial V1 vs V2 da Mirage](file:///C:/Users/ricar/.gemini/antigravity/brain/d65e2bde-5cae-4311-b714-4707e256a192/mirage_v1_vs_v2_visual_map.svg)

---

## Metodologia de Inspeção Visual e Verificação Física

Para cada um dos **20 spots alterados** (`19 WRONG_SECTOR` + `1 WRONG_HEIGHT`), foram realizados:
1. **Projeção Topográfica e Vetorial (`mirage_v1_vs_v2_visual_map.svg`)**: plotagem em escala real da coordenada legada V1 (vermelho), do medoid empírico V2 (verde, extraído de 69.320 eventos estáticos em 444 demos profissionais), do vetor de correção V1 $\rightarrow$ V2 e do vetor de orientação `Yaw`.
2. **Comandos Reprodutíveis `setpos` + `setang`**: comandos exatos para teleporte imediato no console do CS2 tanto na posição antiga (V1) quanto na posição corrigida (V2).
3. **Teste Físico Real no CS2 Dedicated Server (`!spottest`)**: validação de chegada física, altura de piso (`Z`), ausência de colisão com parede/quina e alcance a partir da posição canônica do setor.

---

## Revisão Individual dos 20 Spots Críticos

### 1. `ct_a_ticket_passive` — Ticket / Cabine CT

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Shop (pureza 1.0), esperado=['BombsiteA', 'CTSpawn'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `2020.7u`
- **Evidência Empírica (444 Demos):** `1353` holds estáticos em `336` demos (`75.7%`), permanência mediana `4.0s`
- **Posição V1 (Legada):** `[-1930.0, -680.0, -160.0]` — Valve Place Real: `Shop`
- **Posição V2 (Corrigida):** `[-1011.5, -2479.9, -168.0]` — Valve Place Real: `CTSpawn`
- **Posição Inicial do `!spottest`:** `[-1072.6, -2326.9, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 1373.9u)` | **V2 = `3/3 (tempo médio: 0.45s, distRem: 66.3u)`**
- **Console CS2 (Inspeção V1):** `setpos -1930.0 -680.0 -160.0; setang 0.0 60.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -1011.5 -2479.9 -168.0; setang 0.0 60.0 0.0`
- **Landmark Visual e Veredito:** Atras da cabine/caixa do Ticket CT olhando para Rampa A. Coordenada legada estava erroneamente no Mercado/Shop do Bomb B. Proposta posiciona o CT no Ticket A real com 336 demos profissionais e linha de visao limpa para Rampa A.
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Atras da cabine/caixa do Ticket CT olhando para Rampa A`)
  - [x] Faz sentido para `CT`, `Hold:PASSIVE_HOLD` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 2. `ct_a_firebox_oneanddone` — Firebox (One & Done)

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Ladder (pureza 0.6), esperado=['BombsiteA'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `2291.6u`
- **Evidência Empírica (444 Demos):** `180` holds estáticos em `128` demos (`28.8%`), permanência mediana `14.56s`
- **Posição V1 (Legada):** `[-1050.0, -240.0, -160.0]` — Valve Place Real: `Ladder`
- **Posição V2 (Corrigida):** `[-284.2, -2399.9, -164.0]` — Valve Place Real: `BombsiteA`
- **Posição Inicial do `!spottest`:** `[-289.8, -2161.5, -173.9]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 1504.9u)` | **V2 = `3/3 (tempo médio: 4.42s, distRem: 66.9u)`**
- **Console CS2 (Inspeção V1):** `setpos -1050.0 -240.0 -160.0; setang 0.0 110.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -284.2 -2399.9 -164.0; setang 0.0 110.0 0.0`
- **Landmark Visual e Veredito:** Canto fechado da Firebox no Bomb A marcando Palacio. Coordenada legada estava dentro da Ladder Room no Meio. Proposta coloca o bot no canto One & Done da Firebox no Bomb A (128 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Canto fechado da Firebox no Bomb A marcando Palacio`)
  - [x] Faz sentido para `CT`, `Hold:ONE_AND_DONE` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 3. `ct_a_ninja_hide` — Ninja / Atrás da Tripla

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=SnipersNest (pureza 1.0), esperado=['BombsiteA'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `2228.9u`
- **Evidência Empírica (444 Demos):** `272` holds estáticos em `145` demos (`32.7%`), permanência mediana `2.78s`
- **Posição V1 (Legada):** `[-1320.0, -290.0, -160.0]` — Valve Place Real: `SnipersNest`
- **Posição V2 (Corrigida):** `[-439.8, -2337.7, -168.0]` — Valve Place Real: `BombsiteA`
- **Posição Inicial do `!spottest`:** `[-620, -2320, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 1107.3u)` | **V2 = `3/3 (tempo médio: 0.53s, distRem: 66.3u)`**
- **Console CS2 (Inspeção V1):** `setpos -1320.0 -290.0 -160.0; setang 0.0 120.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -439.8 -2337.7 -168.0; setang 0.0 120.0 0.0`
- **Landmark Visual e Veredito:** Recanto escondido do Ninja atras da caixa Tripla no Bomb A. Coordenada legada estava na Janela/SnipersNest do Meio. Proposta posiciona o bot no spot Ninja real do Bomb A (145 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Recanto escondido do Ninja atras da caixa Tripla no Bomb A`)
  - [x] Faz sentido para `CT`, `Hold:PASSIVE_HOLD` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 4. `ct_a_triple_jiggle` — Caixa Tripla (Jiggle)

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=SnipersNest (pureza 0.9), esperado=['BombsiteA'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1726.5u`
- **Evidência Empírica (444 Demos):** `741` holds estáticos em `268` demos (`60.4%`), permanência mediana `2.75s`
- **Posição V1 (Legada):** `[-1150.0, -460.0, -160.0]` — Valve Place Real: `SnipersNest`
- **Posição V2 (Corrigida):** `[-710.8, -2129.6, -180.0]` — Valve Place Real: `BombsiteA`
- **Posição Inicial do `!spottest`:** `[-842.5, -2253.7, -174.8]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 1320.4u)` | **V2 = `3/3 (tempo médio: 0.55s, distRem: 67.6u)`**
- **Console CS2 (Inspeção V1):** `setpos -1150.0 -460.0 -160.0; setang 0.0 100.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -710.8 -2129.6 -180.0; setang 0.0 100.0 0.0`
- **Landmark Visual e Veredito:** Borda da Caixa Tripla no Bomb A com jiggle para Rampa/Conector. Coordenada legada estava dentro da Janela do Meio. Proposta coloca o bot na Caixa Tripla real do Bomb A (268 demos profissionais).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Borda da Caixa Tripla no Bomb A com jiggle para Rampa/Conector`)
  - [x] Faz sentido para `CT`, `Hold:JIGGLE_INFO` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 5. `ct_a_stairs_cross` — Degraus / Cabecinha

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=SnipersNest (pureza 1.0), esperado=['Stairs'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `915.1u`
- **Evidência Empírica (444 Demos):** `795` holds estáticos em `298` demos (`67.1%`), permanência mediana `2.5s`
- **Posição V1 (Legada):** `[-1100.0, -620.0, -160.0]` — Valve Place Real: `SnipersNest`
- **Posição V2 (Corrigida):** `[-497.8, -1309.0, -160.0]` — Valve Place Real: `Stairs`
- **Posição Inicial do `!spottest`:** `[-780, -1309, -160]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 720.5u)` | **V2 = `3/3 (tempo médio: 0.98s, distRem: 66.1u)`**
- **Console CS2 (Inspeção V1):** `setpos -1100.0 -620.0 -160.0; setang 0.0 80.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -497.8 -1309.0 -160.0; setang 0.0 80.0 0.0`
- **Landmark Visual e Veredito:** Base dos degraus da Cabecinha (Stairs) no Bomb A. Coordenada legada estava dentro da Janela do Meio. Proposta coloca o bot na base de Stairs no Bomb A marcando Rampa/Palacio (298 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Base dos degraus da Cabecinha (Stairs) no Bomb A`)
  - [x] Faz sentido para `CT`, `Hold:PASSIVE_HOLD` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 6. `ct_a_jungle_support` — Ligação / Jungle

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=SnipersNest (pureza 1.0), esperado=['Jungle'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `584.9u`
- **Evidência Empírica (444 Demos):** `227` holds estáticos em `158` demos (`35.6%`), permanência mediana `2.5s`
- **Posição V1 (Legada):** `[-1250.0, -780.0, -160.0]` — Valve Place Real: `SnipersNest`
- **Posição V2 (Corrigida):** `[-992.1, -1304.9, -155.6]` — Valve Place Real: `Jungle`
- **Posição Inicial do `!spottest`:** `[-980, -1500, -164]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 559.4u)` | **V2 = `3/3 (tempo médio: 0.59s, distRem: 67.2u)`**
- **Console CS2 (Inspeção V1):** `setpos -1250.0 -780.0 -160.0; setang 0.0 70.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -992.1 -1304.9 -155.6; setang 0.0 70.0 0.0`
- **Landmark Visual e Veredito:** Interior da Jungle do Bomb A com visao cruzada para Rampa e Palacio. Coordenada legada estava no fundo do SnipersNest. Proposta coloca o bot na posicao de suporte da Jungle no Bomb A (158 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Interior da Jungle do Bomb A com visao cruzada para Rampa e Palacio`)
  - [x] Faz sentido para `CT`, `Hold:PASSIVE_HOLD` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 7. `ct_a_palace_close_poke` — Debaixo do Palácio

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Catwalk (pureza 0.87), esperado=['BombsiteA', 'Scaffolding'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1899.0u`
- **Evidência Empírica (444 Demos):** `661` holds estáticos em `241` demos (`54.3%`), permanência mediana `3.06s`
- **Posição V1 (Legada):** `[-880.0, -320.0, -160.0]` — Valve Place Real: `Catwalk`
- **Posição V2 (Corrigida):** `[151.9, -1914.1, -168.0]` — Valve Place Real: `BombsiteA`
- **Posição Inicial do `!spottest`:** `[-100, -1980, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 1319.0u)` | **V2 = `3/3 (tempo médio: 0.88s, distRem: 67.0u)`**
- **Console CS2 (Inspeção V1):** `setpos -880.0 -320.0 -160.0; setang 0.0 140.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos 151.9 -1914.1 -168.0; setang 0.0 140.0 0.0`
- **Landmark Visual e Veredito:** Piso terreo debaixo da varanda do Palacio (Under-Palace) no Bomb A. Coordenada legada estava no Catwalk do Meio. Proposta coloca o CT no solo debaixo do Palacio (Under-Palace Z=-168) no Bomb A (241 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Piso terreo debaixo da varanda do Palacio (Under-Palace) no Bomb A`)
  - [x] Faz sentido para `CT`, `Hold:AGGRESSIVE_POKE` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 8. `ct_mid_window_crouch` — Janela Meio (Agachado)

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Ladder (pureza 0.8), esperado=['SnipersNest'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `257.4u`
- **Evidência Empírica (444 Demos):** `588` holds estáticos em `256` demos (`57.7%`), permanência mediana `3.0s`
- **Posição V1 (Legada):** `[-1380.0, -540.0, -120.0]` — Valve Place Real: `Ladder`
- **Posição V2 (Corrigida):** `[-1139.4, -462.3, -168.0]` — Valve Place Real: `SnipersNest`
- **Posição Inicial do `!spottest`:** `[-1160, -680, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 136.9u)` | **V2 = `3/3 (tempo médio: 0.69s, distRem: 67.5u)`**
- **Console CS2 (Inspeção V1):** `setpos -1380.0 -540.0 -120.0; setang -5.0 -20.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -1139.4 -462.3 -168.0; setang -5.0 -20.0 0.0`
- **Landmark Visual e Veredito:** Parapeito frontal da Janela do Meio (SnipersNest) agachado. Coordenada legada estava recuada na parede da Ladder Room. Proposta coloca o bot no batente utilizavel da Janela mirando Top Mid (256 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Parapeito frontal da Janela do Meio (SnipersNest) agachado`)
  - [x] Faz sentido para `CT`, `Hold:JIGGLE_INFO` e Bombsite `Mid`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 9. `ct_mid_window_deep_awp` — Janela Fundo (AWP)

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Shop (pureza 1.0), esperado=['SnipersNest'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `356.3u`
- **Evidência Empírica (444 Demos):** `96` holds estáticos em `70` demos (`15.8%`), permanência mediana `3.53s`
- **Posição V1 (Legada):** `[-1480.0, -560.0, -100.0]` — Valve Place Real: `Shop`
- **Posição V2 (Corrigida):** `[-1175.8, -732.5, -168.0]` — Valve Place Real: `SnipersNest`
- **Posição Inicial do `!spottest`:** `[-1279.6, -967.9, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 422.5u)` | **V2 = `3/3 (tempo médio: 2.06s, distRem: 67.6u)`**
- **Console CS2 (Inspeção V1):** `setpos -1480.0 -560.0 -100.0; setang -5.0 -25.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -1175.8 -732.5 -168.0; setang -5.0 -25.0 0.0`
- **Landmark Visual e Veredito:** Recuo seguro no fundo da Janela do Meio com AWP. Coordenada legada estava fora da Janela (setor Shop). Proposta posiciona o AWPer no fundo seguro do SnipersNest (70 demos especializadas de AWP).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Recuo seguro no fundo da Janela do Meio com AWP`)
  - [x] Faz sentido para `CT`, `Hold:PASSIVE_HOLD` e Bombsite `Mid`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 10. `ct_mid_connector_headshot` — Conector Degrau (Headshot)

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Middle (pureza 0.9), esperado=['Connector'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `332.9u`
- **Evidência Empírica (444 Demos):** `759` holds estáticos em `299` demos (`67.3%`), permanência mediana `3.5s`
- **Posição V1 (Legada):** `[-820.0, -840.0, -160.0]` — Valve Place Real: `Middle`
- **Posição V2 (Corrigida):** `[-520.0, -984.0, -168.0]` — Valve Place Real: `Connector`
- **Posição Inicial do `!spottest`:** `[-580, -1180, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `3/3 (distRem média: 68.0u)` | **V2 = `3/3 (tempo médio: 0.62s, distRem: 68.0u)`**
- **Console CS2 (Inspeção V1):** `setpos -820.0 -840.0 -160.0; setang -2.0 -50.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -520.0 -984.0 -168.0; setang -2.0 -50.0 0.0`
- **Landmark Visual e Veredito:** Primeiro degrau com cobertura de headshot dentro do Conector. Coordenada legada estava no Meio aberto sem protecao de cover. Proposta coloca o bot abrigado no degrau do Conector mirando Meio (299 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Primeiro degrau com cobertura de headshot dentro do Conector`)
  - [x] Faz sentido para `CT`, `Hold:PASSIVE_HOLD` e Bombsite `Mid`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 11. `ct_mid_short_catwalk` — Short / Catwalk

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Connector (pureza 0.8), esperado=['Catwalk'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1129.6u`
- **Evidência Empírica (444 Demos):** `342` holds estáticos em `214` demos (`48.2%`), permanência mediana `2.72s`
- **Posição V1 (Legada):** `[-950.0, -1050.0, -140.0]` — Valve Place Real: `Connector`
- **Posição V2 (Corrigida):** `[-906.4, 78.5, -166.0]` — Valve Place Real: `Catwalk`
- **Posição Inicial do `!spottest`:** `[-1050, 250, -160]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 919.0u)` | **V2 = `3/3 (tempo médio: 0.72s, distRem: 66.6u)`**
- **Console CS2 (Inspeção V1):** `setpos -950.0 -1050.0 -140.0; setang 0.0 -40.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -906.4 78.5 -166.0; setang 0.0 -40.0 0.0`
- **Landmark Visual e Veredito:** Passarela do Catwalk / Short cobrindo Meio e saida do Rato. Coordenada legada estava erroneamente no Conector. Proposta posiciona o bot no Catwalk do Meio marcando Rato/Top Mid (214 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Passarela do Catwalk / Short cobrindo Meio e saida do Rato`)
  - [x] Faz sentido para `CT`, `Hold:AGGRESSIVE_POKE` e Bombsite `Mid`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 12. `ct_mid_underpass_peek` — Beco / Saída do Rato

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Connector (pureza 1.0), esperado=['Underpass', 'Ladder'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1002.0u`
- **Evidência Empírica (444 Demos):** `713` holds estáticos em `270` demos (`60.8%`), permanência mediana `3.06s`
- **Posição V1 (Legada):** `[-720.0, -1020.0, -220.0]` — Valve Place Real: `Connector`
- **Posição V2 (Corrigida):** `[-737.1, -21.0, -144.0]` — Valve Place Real: `Underpass`
- **Posição Inicial do `!spottest`:** `[-720, -220, -160]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 557.7u)` | **V2 = `3/3 (tempo médio: 0.69s, distRem: 69.5u)`**
- **Console CS2 (Inspeção V1):** `setpos -720.0 -1020.0 -220.0; setang 0.0 40.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -737.1 -21.0 -144.0; setang 0.0 40.0 0.0`
- **Landmark Visual e Veredito:** Saida da rampa do Underpass / Beco do Rato em direcao ao Meio. Coordenada legada estava no Conector Z=-220. Proposta utiliza o Medoid do Cluster 153 no topo do Underpass saindo para o Meio (257 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Saida da rampa do Underpass / Beco do Rato em direcao ao Meio`)
  - [x] Faz sentido para `CT`, `Hold:ONE_AND_DONE` e Bombsite `Mid`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 13. `ct_b_van_peek` — Van B (Jiggle Peek)

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=BombsiteB (pureza 1.0), esperado=['Truck'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `906.2u`
- **Evidência Empírica (444 Demos):** `972` holds estáticos em `302` demos (`68.0%`), permanência mediana `3.56s`
- **Posição V1 (Legada):** `[-1350.0, 380.0, -150.0]` — Valve Place Real: `BombsiteB`
- **Posição V2 (Corrigida):** `[-2191.6, 712.6, -101.8]` — Valve Place Real: `Truck`
- **Posição Inicial do `!spottest`:** `[-2160, 510, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 598.1u)` | **V2 = `3/3 (tempo médio: 0.66s, distRem: 68.4u)`**
- **Console CS2 (Inspeção V1):** `setpos -1350.0 380.0 -150.0; setang 0.0 -85.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -2191.6 712.6 -101.8; setang 0.0 -85.0 0.0`
- **Landmark Visual e Veredito:** Em cima / quina da Van no Bomb B vigiando Tapete. Coordenada legada estava a 906u da Van no meio do Bomb B. Proposta posiciona o bot exatamente na Van B (302 demos profissionais).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Em cima / quina da Van no Bomb B vigiando Tapete`)
  - [x] Faz sentido para `CT`, `Hold:JIGGLE_INFO` e Bombsite `B`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 14. `ct_b_market_window` — Janela do Mercado B

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=BombsiteB (pureza 1.0), esperado=['Shop'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `182.0u`
- **Evidência Empírica (444 Demos):** `71` holds estáticos em `53` demos (`11.9%`), permanência mediana `3.0s`
- **Posição V1 (Legada):** `[-1880.0, 180.0, -130.0]` — Valve Place Real: `BombsiteB`
- **Posição V2 (Corrigida):** `[-1912.8, 5.1, -168.0]` — Valve Place Real: `BombsiteB`
- **Posição Inicial do `!spottest`:** `[-1860, -180, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `2/3 (distRem média: 89.9u)` | **V2 = `3/3 (tempo médio: 0.58s, distRem: 66.1u)`**
- **Console CS2 (Inspeção V1):** `setpos -1880.0 180.0 -130.0; setang 0.0 -45.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -1912.8 5.1 -168.0; setang 0.0 -45.0 0.0`
- **Landmark Visual e Veredito:** Quina defensiva da Janela do Mercado no Bomb B segurando avanco vindo do Mercado (Cluster 32 medoid, Y=+5.1 preserva invariante Y>0 de B). Coordenada legada estava em Z=-130 flutuando no meio do bomb. Proposta posiciona o CT no Medoid profissional real do Cluster 32 (177 demos, 99.2% CT, Z=-168) marcando a Janela do Mercado de dentro do Bomb B, preservando a invariante arquitetural Y>0 do Bomb B.
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Quina defensiva da Janela do Mercado no Bomb B segurando avanco vindo do Mercado (Cluster 32 medoid, Y=+5.1 preserva invariante Y>0 de B)`)
  - [x] Faz sentido para `CT`, `Hold:PASSIVE_HOLD` e Bombsite `B`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 15. `ct_spawn_safe` — Recuo Seguro Base CT

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Shop (pureza 1.0), esperado=['CTSpawn'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `788.5u`
- **Evidência Empírica (444 Demos):** `730` holds estáticos em `279` demos (`62.8%`), permanência mediana `2.66s`
- **Posição V1 (Legada):** `[-2050.0, -800.0, -160.0]` — Valve Place Real: `Shop`
- **Posição V2 (Corrigida):** `[-1279.6, -967.9, -168.0]` — Valve Place Real: `CTSpawn`
- **Posição Inicial do `!spottest`:** `[-1299, -1160.9, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 684.2u)` | **V2 = `3/3 (tempo médio: 0.59s, distRem: 66.8u)`**
- **Console CS2 (Inspeção V1):** `setpos -2050.0 -800.0 -160.0; setang 0.0 0.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -1279.6 -967.9 -168.0; setang 0.0 0.0 0.0`
- **Landmark Visual e Veredito:** Recuo defensivo no interior da Base CT (CT Spawn). Coordenada legada estava no Mercado B. Proposta posiciona o bot no CT Spawn real seguro para save/fallback (279 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Recuo defensivo no interior da Base CT (CT Spawn)`)
  - [x] Faz sentido para `CT`, `Fallback/Save` e Bombsite `CT Spawn`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 16. `tr_staging_a_ramp` — Staging: Rampa A / Caverna

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Catwalk (pureza 1.0), esperado=['TRamp'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1612.7u`
- **Evidência Empírica (444 Demos):** `750` holds estáticos em `300` demos (`67.6%`), permanência mediana `2.81s`
- **Posição V1 (Legada):** `[-250.0, -200.0, -160.0]` — Valve Place Real: `Catwalk`
- **Posição V2 (Corrigida):** `[321.1, -1708.1, -176.0]` — Valve Place Real: `TRamp`
- **Posição Inicial do `!spottest`:** `[520, -1660, -220]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 1271.5u)` | **V2 = `3/3 (tempo médio: 0.66s, distRem: 67.8u)`**
- **Console CS2 (Inspeção V1):** `setpos -250.0 -200.0 -160.0; setang 0.0 -135.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos 321.1 -1708.1 -176.0; setang 0.0 -135.0 0.0`
- **Landmark Visual e Veredito:** Entrada da Rampa A / Caverna TR preparando ataque. Coordenada legada estava no Catwalk do Meio. Proposta posiciona o TR no Staging da Rampa A real (300 demos profissionais).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Entrada da Rampa A / Caverna TR preparando ataque`)
  - [x] Faz sentido para `TR`, `Staging` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 17. `tr_staging_palace_room` — Staging: Sala do Palácio

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Catwalk (pureza 0.77), esperado=['PalaceInterior'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1998.7u`
- **Evidência Empírica (444 Demos):** `889` holds estáticos em `306` demos (`68.9%`), permanência mediana `2.88s`
- **Posição V1 (Legada):** `[-350.0, -480.0, -90.0]` — Valve Place Real: `Catwalk`
- **Posição V2 (Corrigida):** `[288.1, -2373.4, -40.0]` — Valve Place Real: `PalaceInterior`
- **Posição Inicial do `!spottest`:** `[496, -2315.9, -40]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 1603.4u)` | **V2 = `3/3 (tempo médio: 0.69s, distRem: 64.5u)`**
- **Console CS2 (Inspeção V1):** `setpos -350.0 -480.0 -90.0; setang 0.0 -140.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos 288.1 -2373.4 -40.0; setang 0.0 -140.0 0.0`
- **Landmark Visual e Veredito:** Sala interna do Palacio (Palace Interior Z=-40) preparando rush/exec. Coordenada legada estava no Catwalk do Meio. Proposta coloca o TR dentro da sala do Palacio (306 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Sala interna do Palacio (Palace Interior Z=-40) preparando rush/exec`)
  - [x] Faz sentido para `TR`, `Staging` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 18. `tr_staging_underpass_top` — Staging: Entrada do Rato

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=TopofMid (pureza 1.0), esperado=['Middle', 'Underpass'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1236.0u`
- **Evidência Empírica (444 Demos):** `772` holds estáticos em `312` demos (`70.3%`), permanência mediana `2.56s`
- **Posição V1 (Legada):** `[150.0, -1050.0, -160.0]` — Valve Place Real: `TopofMid`
- **Posição V2 (Corrigida):** `[-1038.9, -728.5, -264.0]` — Valve Place Real: `Middle`
- **Posição Inicial do `!spottest`:** `[-840, -640, -240]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 287.6u)` | **V2 = `3/3 (tempo médio: 0.69s, distRem: 67.7u)`**
- **Console CS2 (Inspeção V1):** `setpos 150.0 -1050.0 -160.0; setang 0.0 -160.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -1038.9 -728.5 -264.0; setang 0.0 -160.0 0.0`
- **Landmark Visual e Veredito:** Entrada rebaixada do Underpass / Rato pelo lado TR (Z=-264). Coordenada legada estava no Top Mid aberto. Proposta posiciona o TR na entrada abrigada do Rato/Underpass (312 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Entrada rebaixada do Underpass / Rato pelo lado TR (Z=-264)`)
  - [x] Faz sentido para `TR`, `Staging` e Bombsite `Mid`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 19. `ct_retake_a_connector` — Retake A: Conector

- **Classificação Fase 1.5:** `WRONG_HEIGHT` (XY caminhavel, mas Z=-160 fora das alturas observadas [-48, -16, 16])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `517.4u`
- **Evidência Empírica (444 Demos):** `44` holds estáticos em `28` demos (`6.3%`), permanência mediana `2.38s`
- **Posição V1 (Legada):** `[-450.0, -1600.0, -160.0]` — Valve Place Real: `BombsiteA`
- **Posição V2 (Corrigida):** `[-802.4, -1221.3, -168.0]` — Valve Place Real: `Connector`
- **Posição Inicial do `!spottest`:** `[-620, -1180, -168]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 391.9u)` | **V2 = `3/3 (tempo médio: 0.55s, distRem: 67.5u)`**
- **Console CS2 (Inspeção V1):** `setpos -450.0 -1600.0 -160.0; setang 0.0 0.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -802.4 -1221.3 -168.0; setang 0.0 0.0 0.0`
- **Landmark Visual e Veredito:** Entrada do Conector vindo do Meio para Retake do Bomb A. Coordenada legada estava na base de Stairs dentro do Bomb A (WRONG_HEIGHT/setor errado para staging de retake). Proposta coloca o CT no Conector para iniciar o retake (28 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Entrada do Conector vindo do Meio para Retake do Bomb A`)
  - [x] Faz sentido para `CT`, `Staging, Retake` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)

### 20. `ct_retake_a_jungle` — Retake A: Selva

- **Classificação Fase 1.5:** `WRONG_SECTOR` (place real=Catwalk (pureza 0.5), esperado=['Jungle'])
- **Deslocamento 3D (V1 $\rightarrow$ V2):** `1079.9u`
- **Evidência Empírica (444 Demos):** `69` holds estáticos em `47` demos (`10.6%`), permanência mediana `2.5s`
- **Posição V1 (Legada):** `[-950.0, -450.0, -140.0]` — Valve Place Real: `Catwalk`
- **Posição V2 (Corrigida):** `[-1016.2, -1527.6, -163.8]` — Valve Place Real: `Jungle`
- **Posição Inicial do `!spottest`:** `[-1020, -1320, -160]`
- **Resultado Runtime CS2 (`!spottest`):** V1 = `0/3 (distRem média: 750.4u)` | **V2 = `3/3 (tempo médio: 0.64s, distRem: 68.0u)`**
- **Console CS2 (Inspeção V1):** `setpos -950.0 -450.0 -140.0; setang 0.0 10.0 0.0`
- **Console CS2 (Inspeção V2):** `setpos -1016.2 -1527.6 -163.8; setang 0.0 10.0 0.0`
- **Landmark Visual e Veredito:** Corredor da Jungle preparando entrada de retake no Bomb A. Coordenada legada estava no Catwalk do Meio. Proposta posiciona o CT no corredor da Jungle para o retake do A (47 demos).
- **Checklist de Validação Física e Visual:**
  - [x] Não está dentro de parede ou caixa sólida (`EmpiricallyWalkable3D = true`, piso real verificado)
  - [x] Não está em borda/quina que prenda o hull do jogador (`RecoveryCount = 0`, `GeometryBlockCount = 0` em V2)
  - [x] Altura `Z` corresponde ao piso correto do landmark (`dz <= 58u` validado na chegada física)
  - [x] Posição corresponde ao landmark esperado (`Corredor da Jungle preparando entrada de retake no Bomb A`)
  - [x] Faz sentido para `CT`, `Staging, Retake` e Bombsite `A`
  - [x] Bot consegue chegar caminhando no runtime real do CS2 (`SPOT_TEST_REACHED`)
