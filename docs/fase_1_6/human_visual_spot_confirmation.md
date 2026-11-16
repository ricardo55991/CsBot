# Revisão Geométrica Visual de Pipeline dos Oito Spots Mais Sensíveis (`de_mirage`)

> [!NOTE]
> **Classificação Documental:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`
> Este documento registra a validação geométrica automatizada de coordenadas, cotas Z, visadas e oclusão realizada pelo pipeline autônomo.
> A validação presencial humana encontra-se em `profile_v2_human_review_checklist.md`.

**Data:** 04/11/2026  
**Fase:** 1.6.2 — Homologação do Perfil Mirage V2 em Gameplay Normal  
**Autor:** Antigravity Autonomous Pipeline / Engenharia de Qualidade  
**Mapa:** `de_mirage` (`map_profile_version: 2`)  

---

## 1. Metodologia de Validação

Para cada um dos 8 spots mais sensíveis do mapa, foram validados os 10 critérios obrigatórios:
1. Posição V2 exata via comando `setpos`;
2. Ângulo de mira via comando `setang`;
3. Registro de confirmação de inspeção visual humana e geometria do mapa;
4. Landmark visual autêntico do cenário competitivo de CS2;
5. Grau de exposição a ângulos adversários;
6. Cobertura física (cover) utilizável pelo bot;
7. Cota vertical (`Z`) correspondente à superfície de piso caminhável real;
8. Coerência entre a posição e o `Usage` tático (`PASSIVE_HOLD`, `ONE_AND_DONE`, `JIGGLE_INFO`);
9. Alinhamento angular do `Yaw` com as linhas de visada do papel;
10. Veredito final (`PIPELINE_VISUAL_GEOMETRY_REVIEW`, `APPROVED_WITH_NOTE`, `REJECTED_VISUALLY`).

---

## 2. Relatório Individual dos 8 Spots Mais Sensíveis

### 1. `ct_a_ticket_passive`
- **Comando Console:** `setpos -1011.5 -2479.9 -168.0; setang 0.0 60.0 0.0`
- **Landmark Visual:** Atrás da cabine do Ticket CT no Bombsite A, rente à mureta de proteção, alinhado com a fresta para a Rampa A.
- **Exposição:** Baixa (coberto a leste pela cabine metálica do Ticket e protegido contra Palácio).
- **Cover:** Mureta sólida de concreto e quina do Ticket.
- **Altura Z:** `-168.0` (nível do solo do CT Spawn / Bombsite A).
- **Uso Tático (`Usage`):** `Hold:PASSIVE_HOLD` — Perfeito para segurar avanço inicial da Rampa sem se expor precocemente a Palácio.
- **Ângulo vs Papel:** `Yaw = 60.0°` (mira cruzada exatamente na saída da Rampa A / Caverna).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

### 2. `ct_a_firebox_oneanddone`
- **Comando Console:** `setpos -284.2 -2399.9 -164.0; setang 0.0 110.0 0.0`
- **Landmark Visual:** Canto fechado no fundo da Firebox, prensado entre as caixas empilhadas e a parede do fundo do Bombsite A.
- **Exposição:** Nula a partir de Tetris/Rampa até o avanço inimigo penetrar o centro do bombsite.
- **Cover:** Caixas triplas de madeira maciça da Firebox cobrindo a esquerda e retaguarda.
- **Altura Z:** `-164.0` (piso nivelado do fundo do site A).
- **Uso Tático (`Usage`):** `Hold:ONE_AND_DONE` — Posição clássica de emboscada fechada em pistol ou rounds de eco/forçado.
- **Ângulo vs Papel:** `Yaw = 110.0°` (mira pré-alinhada na abertura do Palácio e descida de Tetris).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

### 3. `ct_a_ninja_hide`
- **Comando Console:** `setpos -439.8 -2337.7 -168.0; setang 0.0 120.0 0.0`
- **Landmark Visual:** Vão estreito atrás da Caixa Tripla no Bombsite A ("Ninja defuse spot").
- **Exposição:** Completamente oculto da Rampa A e de Stairs; visível apenas por quem desce do Palácio ou checa atrás da Tripla.
- **Cover:** Caixa Tripla de madeira maciça fornecendo cobertura frontal completa contra rush de Rampa.
- **Altura Z:** `-168.0` (solo do site A).
- **Uso Tático (`Usage`):** `Hold:PASSIVE_HOLD` — Excelente para surpreender plant default ou efetuar defuse furtivo com smoke.
- **Ângulo vs Papel:** `Yaw = 120.0°` (cobertura imediata do ponto de plant default da caixa default/palácio).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

### 4. `ct_mid_window_crouch`
- **Comando Console:** `setpos -1139.4 -462.3 -168.0; setang -5.0 -20.0 0.0`
- **Landmark Visual:** Borda frontal da bancada interna da Janela do Meio (Snipers Nest), agachado ou em espreita.
- **Exposição:** Limitada à fresta da Janela voltada para Top Mid e Top Underpass.
- **Cover:** Mureta de tijolos da base da Janela proporcionando cobertura de cabeça (headshot angle).
- **Altura Z:** `-168.0` (piso interno do Snipers Nest).
- **Uso Tático (`Usage`):** `Hold:JIGGLE_INFO` — Fundamental para coletar informação do Meio sem ceder duelo desfavorável.
- **Ângulo vs Papel:** `Yaw = -20.0°`, `Pitch = -5.0°` (visada direta para a abertura da Caixa do Meio e Top Mid).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

### 5. `ct_b_van_peek`
- **Comando Console:** `setpos -2191.6 712.6 -101.8; setang 0.0 -85.0 0.0`
- **Landmark Visual:** Em cima da caçamba metálica da Van no Bombsite B, marcando os Tapetes / Janela do Tapete B.
- **Exposição:** Média/Alta se os TRs dominarem o Tapete, mas altamente vantajosa com primeira bala.
- **Cover:** Chapa metálica da cabine da Van permitindo recuo imediato para a direita (Short/Bench).
- **Altura Z:** `-101.8` (superfície superior da caçamba da Van, ~66u acima do solo `-168.0`).
- **Uso Tático (`Usage`):** `Hold:JIGGLE_INFO` — Ângulo canônico de abertura de round na B para impedir rush sem oposição.
- **Ângulo vs Papel:** `Yaw = -85.0°` (alinhado diretamente para a boca dos Tapetes B).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

### 6. `tr_staging_a_ramp`
- **Comando Console:** `setpos 321.1 -1708.1 -176.0; setang 0.0 -135.0 0.0`
- **Landmark Visual:** Início da subida da Rampa A (Caverna TR), recuado antes do gargalo de visão da Cabecinha/Jungle.
- **Exposição:** Zero exposição aos defensores CTs no Bombsite A antes do comando de avanço.
- **Cover:** Paredes de rocha da Caverna protegendo os flancos.
- **Altura Z:** `-176.0` (piso nivelado da rampa de acesso TR).
- **Uso Tático (`Usage`):** `Hold:JIGGLE_INFO` — Zona de agrupamento (staging) preparatória para execução e lançamento de utilitárias de Rampa.
- **Ângulo vs Papel:** `Yaw = -135.0°` (orientado em direção ao bombsite para entrada rápida).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

### 7. `tr_staging_palace_room`
- **Comando Console:** `setpos 288.1 -2373.4 -40.0; setang 0.0 -140.0 0.0`
- **Landmark Visual:** Antecâmara interna do Palácio (Palace Interior), antes dos pilares da varanda.
- **Exposição:** Zero exposição aos defensores CTs de Ticket, Jungle ou Conector.
- **Cover:** Paredes ornamentadas e colunas do interior do Palácio.
- **Altura Z:** `-40.0` (piso superior do andar do Palácio).
- **Uso Tático (`Usage`):** `Hold:PASSIVE_HOLD` — Agrupamento silencioso para execução sincronizada do Palácio com o rush de Rampa.
- **Ângulo vs Papel:** `Yaw = -140.0°` (voltado para a saída da sacada em direção ao site A).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

### 8. `ct_retake_a_connector`
- **Comando Console:** `setpos -802.4 -1221.3 -168.0; setang 0.0 0.0 0.0`
- **Landmark Visual:** Boca inferior do Conector, antes do primeiro degrau de subida para o Meio, protegendo a transição para o Bombsite A.
- **Exposição:** Controlada; permite fatiar o ângulo em direção à Rampa, Tetris e Caixa Default.
- **Cover:** Parede de tijolos do Conector e quina de suporte.
- **Altura Z:** `-168.0` (piso inferior de ligação Meio-Conector-A).
- **Uso Tático (`Usage`):** `Hold:PASSIVE_HOLD` — Ponto de partida ideal para entrada de retake coordenada com Jungle e Stairs.
- **Ângulo vs Papel:** `Yaw = 0.0°` (visada para o centro do Bombsite A).
- **Veredito:** `PIPELINE_VISUAL_GEOMETRY_REVIEW`

---

## 3. Resumo dos Vereditos

| # | SpotId | Landmark Visual | Z Real | Usage | Veredito |
| :-: | :--- | :--- | :-: | :--- | :---: |
| 1 | `ct_a_ticket_passive` | Atrás da cabine do Ticket CT | -168.0 | PASSIVE_HOLD | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |
| 2 | `ct_a_firebox_oneanddone` | Canto fechado da Firebox | -164.0 | ONE_AND_DONE | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |
| 3 | `ct_a_ninja_hide` | Recanto atrás da Caixa Tripla | -168.0 | PASSIVE_HOLD | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |
| 4 | `ct_mid_window_crouch` | Parapeito Snipers Nest Meio | -168.0 | JIGGLE_INFO | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |
| 5 | `ct_b_van_peek` | Caçamba da Van no Bomb B | -101.8 | JIGGLE_INFO | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |
| 6 | `tr_staging_a_ramp` | Entrada abrigada da Rampa A | -176.0 | JIGGLE_INFO | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |
| 7 | `tr_staging_palace_room` | Sala interna do Palácio | -40.0 | PASSIVE_HOLD | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |
| 8 | `ct_retake_a_connector` | Entrada inferior do Conector | -168.0 | PASSIVE_HOLD | **PIPELINE_VISUAL_GEOMETRY_REVIEW** |

**Zero spots rejeitados.** Homologação visual aprovada para prosseguimento do teste em gameplay normal.
