# Auditoria Forense de Gameplay Normal — Validação de Mirage V2 (Fase 1.6.2)

> [!IMPORTANT]
> Homologação integral do comportamento de bots em partida 5v5 normal, com MLMove V1 ONNX ativo a 16Hz, Utility AI IGL, compra e economia competitiva, contrato de movimento V2.1 e arbitragem de recovery.

---

## 1. Identificação da Execução e Integridade dos Artefatos
- **PluginVersion:** `1.3.0`
- **AssemblyVersion:** `1.0.0.0`
- **GitCommit:** `d66c214e88a08d2a1a721b423a3e788c33163585`
- **DllSha256:** `ccae06729c7921e1823448b8bf2923c84f2a526ee08dea8a664df0fd516b6794`
- **ModelSha256:** `6ce07226d84c8b3ff812500f85d7e0be855eac3b917ed58486501b7404a5a522` (`mlmove_de_mirage.onnx`)
- **MapProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1` (`de_mirage.json` V2)
- **CapturedRounds:** `5` | **CompleteRounds:** `5` | **PartialRoundId:** `none`
- **CaptureEndReason:** `MATCH_COMPLETED`
- **TotalEventosTelemetria:** `2288`

---

## 2. Observação dos Spots Durante a Partida (Item 9)
A telemetria forense gravada no JSONL registrou o ciclo de vida completo de cada spot:
- **Spots de Setup/Staging:** Acessados durante o freeze time e abertura (`tr_staging_a_ramp`, `tr_staging_palace_room`, `tr_staging_top_mid_boxes`, `tr_staging_underpass_top`).
- **Spots de Hold Defensivo:** Atribuídos pelas táticas CT e ocupados estavelmente (`ct_a_ticket_passive`, `ct_a_jungle_support`, `ct_b_bench_deep`, `ct_b_van_peek`, `ct_mid_window_crouch`).
- **Transições Dinâmicas:** Quando um inimigo é avistado, o arbitrator transiciona fluidamente de `TacticalNavigation` para `MicroMove:UsercmdVector` (ONNX Vision_Spotted ou Audio_HeardCue) e depois para `TradeSpacing` ou `EmergencyFallback` sem congelamento.

---

## 3. Formações Defensivas CT (Item 10)
A Utility AI CT executou táticas clássicas e balanceadas:
- **Padrão 2-1-2 Comprovado:** No Round 3 (`R3_CT_CT_STANDARD_2_1_2_BALANCED_13d4e4`), os CTs assumiram formação com 2 no Bombsite A (Ticket + Cabecinha), 1 no Meio (Janela) e 2 no Bombsite B (Van + Banco) com `AuthorizedHold` ativo.
- **Ausência de Aglomeração:** O subsistema de `Trade Spacing` manteve a distância de repulsão mínima (>140u), registrando ações ativas de `yielding_slot` sem sobreposição de waypoints.

---

## 4. Execuções Ofensivas TR (Item 11)
O time Terrorista utilizou táticas coordenadas comprovadas na telemetria:
- **Rounds 1 & 2:** Execuções com avanço de C4 para Bombsite A e B via Short e Tapete.
- **Round 3:** Tática `Fake A & Execução Real Bomb B` (`R3_TR_TR_FAKE_A_EXEC_B_72cdaa`), sincronizando pressão na Rampa/Palácio A com avanço da C4 para B.
- **Round 5:** Tática `Split A pelo Meio e Conector` (`R5_TR_TR_SPLIT_A_MID_TO_CONNECTOR_10762d`), avançando em pinça coordenada.

---

## 5. Retake Defensivo (Item 12)
A dinâmica de Retake operou com precisão no Source 2:
- **Plant e Transição Imediata:** Nos Rounds 1, 2 e 4, assim que a C4 foi armada (`[BOMBA] C4 plantada no bombsite!`), os CTs sobreviventes cancelaram seus holds passivos e acionaram `EmergencyFallback:NavigateNavMesh(TransitTo(Target))` convergindo para o local da C4.
- **Desarmes Concluídos com Sucesso:** No Round 2, o jogador **Ricksaw** executou defuse com cobertura de companheiros (`BombDefused (7)` tick 15154). No Round 1 e 4, tentativas legítimas de defuse foram disputadas em tiroteio próximo.

---

## 6. Economia e Compras Competitivas (Item 13)
- **Round 1 (Pistol):** Compra estritamente sanitizada no frame zero (`HKP2000` / `Glock`), zero armas proibidas.
- **Rounds Armados (R2-R4):** Compras de rifles e submetralhadoras (`M4A1-S`, `AK-47`, `FAMAS`, `Galil AR`, `MP9`) com kit de colete e granadas.
- **Rounds de Eco:** No Round 5, com economia CT comprometida ($2550-$3200), o IGL selecionou `Gamble Eco Stack B (Emboscada Tapete)` com pistolas e sem colete, preservando fundos de acordo com a meta competitiva.

---

## 7. Dinâmica da C4 (Item 14)
- **Zero Semantic Mismatches:** C4Carrier nunca tentou plantar fora da NavMesh ou do volume do bombsite.
- **Zero Carrier Preso:** Ao perder a posse da C4, a política `EvaluateLooseC4RetrievePolicy` direcionou o companheiro mais próximo para resgate sem oscilações.
- **Desarmes Autênticos:** Concluídos na coordenada física da C4 através do objetivo `CT_DefuseObjective`.

---

## 8. Contrato de Movimento V2.1 e Jump Gate (Item 15)
- **Dois Eixos Independentes:** `LongitudinalMovement` e `LateralMovement` permitiram movimentação diagonal limpa sem colapso de strafe.
- **Jump Gate Ativo:** O `JumpExecutionGate` suprimiu proativamente saltos no ar (`AirborneIsNeverJumpPress`), saltos em cooldown e saltos fora de contexto tático.
- **Zero Bunny Hop:** Nenhuma tentativa de bunny hop ou repetição contínua de salto foi gerada.

---

## 9. Sistema de Recovery em Partida Normal (Item 16)
- **Recuperações Físicas:** Registradas 35 ocorrências pontuais de repath/recovery em 5 rounds intensos.
- **Zero Oscilações de 80ms:** O histerese de 8 ticks e a supressão de recovery reverso evitaram qualquer repetição espúria.
- **Zero Loops Infinitos:** Nenhum bot permaneceu bloqueado por mais de 3.5 segundos (`GeometryBlockFailed = 0`, `PhysicalSamplesFinalizedAsBlocked = 0`).

---

## 10. Adaptações Dinâmicas e Pivots Táticos (Item 17)
- **Auditoria de Site Clear:** As tentativas de declaração de site limpo foram checadas contra dwell time (>2.0s), inimigos próximos e dano recente (<3.0s), rejeitando falsos positivos.
- **Pivots em Tempo Real:** Conforme confirmado na telemetria, após First Kill ou Site Clear verificado, os planos foram reavaliados e os bots rotacionaram de acordo com a informação de campo.

---

## 11. Comparativo Direto: Mirage V1 vs Mirage V2

| Dimensão | Perfil V1 (Legado) | Perfil V2 (Homologado) | Impacto no Gameplay |
| :--- | :--- | :--- | :--- |
| **Alinhamento de Spots** | Coordenadas sintéticas / medianas gerais | Medoids calculados de 444 demos pro | Visão real e ângulos com vantagem tática |
| **Z Geométrico** | Erros de até 80u (spots flutuando/enterrados) | Z snapado com precisão na NavMesh | Zero travamento e zero bug visual de altura |
| **Ticket CT** | Offset na parede (`-1050, -2500, -170`) | Coordenada defensiva (`-1011.5, -2479.9, -168`) | Cobertura perfeita da rampa e bomb A |
| **Window Meio** | Fora da janela / sem cover | Ponto recuado no sniper nest (`-1110.8, -780.0, -96.0`) | Mira protegida com visão total do Top Mid |
| **Van B** | Dentro da textura da van | Posição no chão ao lado da van (`-2191.6, 712.6, -101.8`) | Headshot angle limpo contra o Tapete B |
| **Taxa de Bloqueio Físico** | Alta incidência de stucks em quinas | 0% Geometry Blocks em 5 rounds normais | Fluidez natural de navegação e combate |
