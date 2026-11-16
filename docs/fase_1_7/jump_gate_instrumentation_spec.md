# Especificação de Instrumentação Forense do JumpExecutionGate (Fase 1.7)

> [!IMPORTANT]
> Esta especificação define os 8 eventos estruturados e os 21 campos obrigatórios para monitoramento forense do subsistema de salto no CS2, prevenindo spam de salto e detecção precoce de sequências acidentais de bunny hop.

---

## 1. Motivação e Objetivos

Nas fases anteriores (1.6 e 1.6.2), o sistema registrava telemetria simplificada de requisições de salto (`JUMP_REQUESTED`), resultando no diagnóstico `JUMP_METRICS_NOT_INSTRUMENTED`.

Para a Fase 2 (treinamento e execução do Positioning Transformer e MLMove V2), o `JumpExecutionGate` deve operar com rastreamento ponta a ponta sem alterar a física:
1. Proibição absoluta de bunny hop executável;
2. Deduplicação tick a tick (registro episódico de supressões e eventos terminais);
3. Auditoria transparente de 21 campos forenses por evento.

---

## 2. Catálogo de Eventos Estruturados (8 Tipos)

1. `JUMP_REQUESTED`: Emitido quando uma intenção ou predição de salto (ONNX ações 49..96 ou bypass de navegação) entra em avaliação.
2. `JUMP_EXECUTED`: Emitido quando o salto é autorizado e despachado para a camada de locomoção.
3. `JUMP_SUPPRESSED_AIRBORNE`: Emitido quando o salto é barrado porque o bot já se encontra no ar (`!Grounded`).
4. `JUMP_SUPPRESSED_COOLDOWN`: Emitido quando o salto é barrado porque o temporizador de resfriamento (3.5s) ainda está ativo.
5. `JUMP_SUPPRESSED_CONTEXT`: Emitido quando o bot está em estado de mira fechada, plant/defuse ou hold defensivo.
6. `JUMP_SUPPRESSED_NO_JUMP_ZONE`: Emitido caso o bot esteja em uma zona proibida de salto do perfil de mapa.
7. `JUMP_LANDED`: Emitido no tick exato da transição `Airborne -> Grounded`.
8. `REPEATED_JUMP_SEQUENCE_DETECTED`: Emitido quando múltiplos inputs de salto consecutivos são solicitados imediatamente após o pouso (< 5 ticks). O gate impede a execução da sequência para neutralizar bunny hop não intencional.

---

## 3. Os 21 Campos Obrigatórios

| # | Campo | Tipo | Descrição |
| :-: | :--- | :--- | :--- |
| 1 | `InternalRoundId` | `string` | GUID único da rodada corrente |
| 2 | `OfficialRoundNumber` | `int` | Número da rodada no placar oficial do CS2 |
| 3 | `Tick` | `int` | Tick do servidor dedicado no momento do evento |
| 4 | `Slot` | `int` | Índice do slot do jogador/bot (0..63) |
| 5 | `Team` | `string` | Time do bot (`CounterTerrorist` ou `Terrorist`) |
| 6 | `Role` | `string` | Papel tático do bot (`AWPer`, `EntryFragger`, etc.) |
| 7 | `Source` | `string` | Origem da requisição (`ONNX_Horizon0`, `Recovery_Stuck`, etc.) |
| 8 | `JumpReason` | `string` | Motivo semântico do salto (`ObstacleTraversal`, `Recovery`, etc.) |
| 9 | `Grounded` | `bool` | Indica se o bot está com os pés no chão firme |
| 10 | `Airborne` | `bool` | Indica se o bot está em trajetória aérea |
| 11 | `Falling` | `bool` | Indica se a velocidade vertical é negativa ($v_z < 0$) no ar |
| 12 | `LastJumpTick` | `int` | Tick do último salto executado |
| 13 | `LastLandingTick` | `int` | Tick do último pouso registrado |
| 14 | `CooldownRemaining` | `float` | Segundos restantes até a liberação do cooldown |
| 15 | `Allowed` | `bool` | `true` se o evento resultou em despacho físico; `false` se suprimido |
| 16 | `SuppressionReason` | `string` | Causa do bloqueio (`AlreadyAirborne`, `CooldownActive`, etc.) |
| 17 | `Position` | `Vector3` | Coordenadas $(X, Y, Z)$ exatas do bot no tick |
| 18 | `Velocity2D` | `float` | Velocidade horizontal planar ($\sqrt{v_x^2 + v_y^2}$) em unidades/s |
| 19 | `VelocityZ` | `float` | Velocidade vertical ($v_z$) em unidades/s |
| 20 | `TacticId` | `string` | Identificador da tática coletiva ativa |
| 21 | `PlanStage` | `string` | Estágio atual do plano tático (`Setup`, `Execution`, `PostPlant`) |

---

## 4. Política Anti-Bunny Hop e Deduplicação

- **Detecção de Sequência Repetida**: O `JumpGateState` rastreia o intervalo entre o `LastLandingTick` e uma nova solicitação `JUMP_REQUESTED`. Se o bot tentar emitir jump antes do tempo mínimo de compressão pós-pouso ou se registrar padrões oscilatórios rápidos, é disparado `REPEATED_JUMP_SEQUENCE_DETECTED` e a ação é coercitivamente rebaixada para marcha terrestre.
- **Deduplicação de Eventos**: Para evitar flood de telemetria (64 eventos por segundo durante saltos ou quedas longas), a supressão é registrada como um episódio no início da recusa, sem duplicatas em ticks intermediários.
