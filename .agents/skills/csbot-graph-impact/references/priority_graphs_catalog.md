# Catálogo dos 5 Grafos Prioritários e Mapeamento de Impacto (`csbot-graph-impact`)

Este documento detalha a estrutura arquitetural e as 10 dimensões de impacto (`entry_points`, `writers`, `readers`, `authoritative_state`, `fallbacks`, `caches`, `side_effects`, `telemetry`, `tests`, `blast_radius`) para os 5 fluxos críticos do projeto CsBot.

---

## 1. `Positioning Transformer → GoalPosition`

Fluxo responsável por traduzir a inferência do modelo tático ONNX em coordenadas de destino (`GoalPosition`) para navegação do bot.

- **`entry_points`**: Ciclo de atualização tática do bot / tick de inferência de posicionamento.
- **`writers`**: Inferência do `Positioning Transformer` (ONNX), resolvedor de spots de `MapProfiles/*.json`, overrides de objetivo tático.
- **`readers`**: Sistema de pathfinding/navegação, `MovementArbitrator`, logger de telemetria de spots.
- **`authoritative_state`**: `GoalPosition` validada e associada ao spot ativo do bot no tick corrente.
- **`fallbacks`**: Fallback para heurística tática / spot padrão do `MapProfile` caso o modelo ONNX retorne classe sem suporte, spot inválido ou falha de inferência.
- **`caches`**: Cache de último spot atribuído, timers de hysteresis/permanência mínima em spot (`spot_hold_timer`) e tensores de histórico temporal de entrada do Transformer.
- **`side_effects`**: Mudança prematura de `GoalPosition` pode interromper hold de ângulo, abandonar cobertura de C4 ou causar oscilação (ping-pong) entre dois setores.
- **`telemetry`**: Eventos de inferência ONNX, `spot_assigned`, `spot_reached`, `fallback_activated`.
- **`tests`**: Testes de resolução de spots, validação de contrato de entrada/saída ONNX e testes de fallback de posicionamento.
- **`blast_radius`**: Pipeline de features de posicionamento, `MapProfiles/*.json`, classes de decisão tática e navegação física.

---

## 2. `BombObjectiveState → C4 movement`

Fluxo que coordena a posse da C4, deslocamento do carrier até o bombsite, plant, proteção pós-plant (TR) e retake/defuse (CT).

- **`entry_points`**: Atualização de estado da partida/round e eventos de C4 (`bomb_dropped`, `bomb_pickup`, `bomb_planted`, `bomb_defused`).
- **`writers`**: Gerenciador de estado de objetivo de bomba (`BombObjectiveState`), handlers de eventos do servidor CS2.
- **`readers`**: Seletor de comportamento do bot carrier, escolta TR, coordenador de retake CT e override de `GoalPosition`.
- **`authoritative_state`**: `BombObjectiveState` sincronizado com a entidade real da C4 no mundo do jogo.
- **`fallbacks`**: Reatribuição de carrier quando o portador morre (`dropped C4 pickup`) ou fallback para rota direta ao bombsite.
- **`caches`**: Estado cacheado do portador da C4, posição da C4 caída e timers de plant/defuse.
- **`side_effects`**: Conflito entre `Positioning Transformer` genérico e prioridade de plant/defuse se o override de `BombObjectiveState` for sobrescrito por outro `writer` no mesmo tick.
- **`telemetry`**: `c4_state_change`, `c4_carrier_move`, `c4_plant_attempt`, `c4_planted`, `c4_defuse_attempt`.
- **`tests`**: Testes de máquina de estados de C4, transição de carrier e prioridade de defuse/plant.
- **`blast_radius`**: Subsistema de objetivos táticos, árvore de decisão de round, movimentação rumo a bombsites A/B e telemetria de C4.

---

## 3. `ONNX Jump request → JumpExecutionGate → usercmd`

Fluxo que filtra predições de pulo da rede neural antes de injetar o bit `IN_JUMP` no comando físico do motor Source 2 (`usercmd`).

- **`entry_points`**: Saída da head de ação/movimento do modelo ONNX no tick atual.
- **`writers`**: Preditor ONNX (`jump_prob`), `JumpExecutionGate` (aprovação/bloqueio e estado de cooldown) e montador final do `usercmd`.
- **`readers`**: `JumpExecutionGate`, `MovementArbitrator` e aplicador de botões `usercmd`.
- **`authoritative_state`**: Decisão final do `JumpExecutionGate` no tick corrente antes da escrita no `usercmd`.
- **`fallbacks`**: Bloqueio seguro do pulo (`IN_JUMP = 0`) durante plant/defuse, em combate crítico de mira, no ar (`!IsGrounded`) ou durante cooldown.
- **`caches`**: Timers de cooldown entre pulos, histórico recente de pulos por bot e estado de contato com o solo (`grounded_state`).
- **`side_effects`**: Pulo aprovado em momento indevido destrói precisão de tiro (spread), cancela interações ou prende o bot em geometria baixa.
- **`telemetry`**: `onnx_jump_request`, `jump_gate_decision` (com razão de bloqueio), `usercmd_jump_bit`.
- **`tests`**: Testes unitários do `JumpExecutionGate` (cooldown, grounded check, combat/objective lock).
- **`blast_radius`**: Head de jump ONNX, `JumpExecutionGate`, `MovementArbitrator` e geração de `usercmd`.

---

## 4. `Recovery request → MovementArbitrator → physical movement`

Fluxo de detecção de travamento físico (stuck/colisão) e arbitragem de prioridade sobre o controle de movimento do bot.

- **`entry_points`**: Detector de stuck/progresso espacial insuficiente ao longo de uma janela de ticks.
- **`writers`**: Detector de recovery (`RecoveryRequest`), `MovementArbitrator` e controlador de direção/velocidade física.
- **`readers`**: `MovementArbitrator`, executor de movimento de baixo nível (`usercmd` forwardmove/sidemove/yaw).
- **`authoritative_state`**: Fonte de movimento selecionada pelo `MovementArbitrator` (ex: `Recovery` > `ObjectiveOverride` > `TacticalNavigation`).
- **`fallbacks`**: Manobra de desbloqueio progressiva (strafe reverso, repath ou mudança de waypoint) quando o caminho primário falha.
- **`caches`**: Janela deslizante de posições históricas do bot (`position_history_ring_buffer`), contador de tentativas de recovery e timer de lock de arbitragem.
- **`side_effects`**: Se o `MovementArbitrator` não tiver precedência exclusiva, o navegador normal sobrescreve o vetor de recovery no mesmo tick, anulando o deslocamento físico.
- **`telemetry`**: `recovery_triggered`, `arbitrator_source_selected`, `bot_position_delta`, `recovery_resolved`.
- **`tests`**: Testes de precedência no `MovementArbitrator` e testes de detecção/saída de estado stuck.
- **`blast_radius`**: Detector de stuck, `MovementArbitrator`, controlador de navegação e métricas de saúde de movimento em runtime.

---

## 5. `Economy decision → buy command → inventory confirmation`

Fluxo de decisão de compra no início do round (freeze time), execução de comandos de compra e verificação real no inventário do bot.

- **`entry_points`**: Evento `round_start` / `buytime_start` no servidor CS2.
- **`writers`**: Motor de decisão econômica (cálculo de tier de compra: eco, force, full buy), emissor de comandos de compra e sincronizador de inventário do motor CS2.
- **`readers`**: Emissor de compra, verificador de loadout pós-compra e planejador tático do round.
- **`authoritative_state`**: Inventário real e saldo (`account_balance`) reportados pela entidade do jogador no servidor CS2 após a tentativa de compra.
- **`fallbacks`**: Fallback para arma secundária/alternativa compatível com o saldo real caso o item primário falhe ou o slot já esteja ocupado.
- **`caches`**: Estado de compra já realizada no round atual (`has_bought_this_round`) e snapshot de equipamento inicial.
- **`side_effects`**: Compras repetidas em loop durante freeze time esgotam dinheiro indevidamente ou dropam armas no spawn se a confirmação de inventário não atualizar o cache.
- **`telemetry`**: `econ_decision`, `buy_command_issued`, `inventory_post_buy`, `buy_discrepancy_detected`.
- **`tests`**: Testes de regras de economia por saldo/loss bonus e testes de reconciliação entre comando emitido e inventário resultante.
- **`blast_radius`**: Módulo de economia, integração de comandos de compra CS2, leitura de entidades de inventário e telemetria econômica.
