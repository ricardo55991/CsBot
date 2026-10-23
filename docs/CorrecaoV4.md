# Investigação e Correção Profunda do CsBot

Atue como **Engenheiro de Software Sênior e Arquiteto de Sistemas especializado em Source 2, CounterStrikeSharp, C# .NET 10 e ONNX Runtime**.

Executamos uma bateria de validação que gerou o relatório:

`H:\CS2_AI_Server\debug_logs\debug_match_20261023_012334.md`

A última implementação trouxe avanços importantes:

- o watchdog de granadas e facas aparentemente funcionou;
- os bots voltaram a receber rifles e armas primárias;
- coletes foram entregues;
- o ONNX permaneceu ativo;
- a inferência ONNX operou com média aproximada de 0,64 ms;
- não foram observados crashes durante a captura;
- Counter-Strafe e Trade Spacing passaram a possuir telemetria;
- decisões estruturadas da IA apareceram nos rounds posteriores.

Entretanto, a auditoria do log revelou problemas estruturais envolvendo:

- ciclo de vida de round;
- sincronização durante Freeze Time;
- arbitragem de movimento;
- colisão entre sistemas de controle;
- recuperação de bots travados;
- Trade Spacing;
- Counter-Strafe;
- decisões táticas;
- telemetria temporal;
- classificação econômica;
- dano;
- velocidade;
- setores geográficos;
- atribuição de armas por função.

---

# Regras obrigatórias da investigação

## 1. Investigue antes de modificar

Antes de editar qualquer arquivo, inspecione prioritariamente:

- `src/CsBotManager/CsBotManagerPlugin.cs`
- `src/CsBotManager/EconomyManager.cs`
- `src/CsBotManager/BotLocomotionDriver.cs`
- `src/CsBotManager/MicroMoveEngine.cs`
- `src/CsBotManager/OllamaIglService.cs`
- `src/CsBotManager/MatchTelemetryLogger.cs`

Inspecione também quaisquer classes relacionadas encontradas durante a análise, incluindo:

- gerenciador de rounds;
- gerenciador de roles;
- sistema de waypoints;
- controlador de NavMesh;
- detector de stuck;
- planejador tático;
- serviço de percepção;
- adaptador do BotControllerApi;
- cache de decisões;
- manipuladores de eventos do CounterStrikeSharp;
- tabelas de preços de equipamentos;
- classificadores de setores do mapa.

As hipóteses descritas neste documento foram derivadas da telemetria. Elas **não devem ser tratadas automaticamente como causa raiz confirmada**.

Para cada bug:

1. localize o fluxo real no código;
2. identifique os escritores e leitores do estado envolvido;
3. confirme ou refute a hipótese;
4. documente a causa raiz real;
5. somente depois implemente a correção;
6. adicione testes;
7. valide no novo log.

Não implemente correções paliativas apenas para esconder alertas ou alterar mensagens.

---

## 2. Preserve os avanços já obtidos

As correções não podem causar regressão em:

- watchdog de granadas e facas;
- entrega de rifles;
- entrega de coletes;
- entrega de utilitárias;
- funcionamento do ONNX;
- latência de inferência;
- Counter-Strafe válido;
- Trade Spacing válido;
- decisões estruturadas;
- placar;
- geração dos relatórios Markdown;
- estabilidade do plugin.

---

## 3. Não faça alterações cegas nos offsets ou propriedades nativas

Antes de alterar propriedades do bot, comandos, offsets, estados de movimento ou APIs nativas:

- confirme a API usada pela versão atual do CounterStrikeSharp;
- preserve compatibilidade com a versão instalada;
- evite dependência de comportamento indefinido;
- não escreva diretamente em propriedades concorrentes sem arbitragem;
- documente qualquer acesso de baixo nível;
- preserve segurança de thread e execução no game thread.

---

# Entrega obrigatória antes das alterações

Apresente primeiro um relatório chamado:

## Diagnóstico de verificação

Para cada bug principal, informe:

- evidência do log;
- hipótese inicial;
- arquivos investigados;
- métodos encontrados;
- estado compartilhado envolvido;
- causa raiz confirmada;
- hipótese confirmada, parcialmente confirmada ou refutada;
- impacto técnico;
- correção proposta;
- riscos de regressão;
- testes necessários.

Somente depois desse diagnóstico inicie a implementação.

---

# BLOCO CRÍTICO

## Bug 1: divergência entre ação prevista e movimento real

### Evidências

Em diversos snapshots, o bot aparece assim:

- `Vel: 0.0 u/s`;
- `Status Locomotion: Parado`;
- ação registrada como `Avanco(250u)`, `Strafe`, `Recuo` ou ação de Trade Spacing.

Exemplos aparecem no Round 2, incluindo Delrow e McCoy.

Foram registrados nove alertas `AUTO-ANOMALY` de bots com velocidade horizontal aparente igual a zero por seis segundos em postura `AGGRESSIVE_POKE`.

Nos Rounds 5 e 6:

- McCoy ficou repetidamente próximo de `(1423, 71)`;
- Shark ficou repetidamente próximo de `(744, -1719)`;
- ambos apresentaram variação vertical sem deslocamento horizontal suficiente.

### Hipóteses a verificar

#### Hipótese 1A

O `MicroMoveEngine` registra a intenção, mas ela não é efetivamente executada porque:

- `IsStopping` permanece verdadeiro;
- `IsHoldingSpot` permanece ativo;
- um comando de navegação tática sobrescreve o micro movimento;
- `BotLocomotionDriver.UpdateTick` escreve depois do ONNX;
- outro subsistema modifica os botões no mesmo tick;
- o comando expira antes de ser aplicado;
- a ação é emitida fora do game thread;
- o NavMesh mantém uma meta incompatível.

#### Hipótese 1B

O detector de stuck usa velocidade 3D. Saltos no eixo Z impedem a confirmação do travamento, embora o deslocamento no plano XY continue praticamente nulo.

#### Hipótese 1C

O mecanismo de unstuck apenas salta ou injeta movimento temporário, sem substituir o waypoint ou a posição-alvo responsável por puxar o bot de volta à mesma quina.

#### Hipótese 1D

`Vision_Spotted` renova ações `Parado(0u)` indefinidamente, sem limite acumulado de StandStill e sem progresso tático mínimo.

---

## Correção arquitetural obrigatória: autoridade única de movimento

Não resolva o conflito simplesmente fazendo vários subsistemas alterarem diretamente:

- `IsStopping`;
- botões;
- velocidade;
- direção;
- posição-alvo;
- waypoint;
- temporizador de rota.

Implemente ou confirme uma camada única de arbitragem de movimento por bot e por tick.

Cada módulo deve publicar uma intenção de movimento, mas somente o arbitrador pode selecionar e aplicar o comando final.

As fontes mínimas de intenção são:

- `RoundLifecycle`;
- `TacticalNavigation`;
- `MicroMove`;
- `TradeSpacing`;
- `CounterStrafe`;
- `Unstuck`;
- `BombObjective`;
- `EmergencyFallback`.

Cada intenção deve possuir:

- identificador;
- bot;
- origem;
- ação;
- prioridade;
- tick de criação;
- tick de expiração;
- duração máxima;
- posição-alvo opcional;
- velocidade desejada;
- postura;
- motivo;
- alvo inimigo opcional;
- possibilidade de interrupção;
- confirmação de aplicação.

Prioridade inicial sugerida:

1. `RoundLifecycle`
2. `BombObjective` crítico
3. `Unstuck`
4. `CounterStrafe` com disparo iminente confirmado
5. `EmergencyFallback`
6. `TradeSpacing`
7. `MicroMove` em combate
8. `TacticalNavigation`

Confirme no código se essa ordem faz sentido antes de aplicá-la.

Requisitos:

- exatamente um comando final de movimento por bot em cada tick;
- nenhum módulo deve sobrescrever o comando após a arbitragem;
- intenções expiradas devem ser removidas;
- ações de parada devem possuir tempo máximo explícito;
- `Unstuck` deve conseguir interromper uma intenção bloqueada;
- o sistema deve evitar alternância de autoridade a cada tick;
- aplicar histerese ou janela mínima quando necessário.

### Telemetria obrigatória da arbitragem

Registrar:

- `intents_received`;
- `winning_intent`;
- `rejected_intents`;
- `arbitration_priority`;
- `arbitration_reason`;
- `predicted_action`;
- `issued_action`;
- `actual_velocity_2d`;
- `actual_velocity_z`;
- `execution_result`;
- `blocked_by`;
- `target_position`;
- `distance_to_target`;
- `path_status`.

Resultados mínimos de execução:

- `APPLIED`;
- `BLOCKED_BY_NAV`;
- `BLOCKED_BY_STOP_STATE`;
- `REPLACED_BY_HIGHER_PRIORITY`;
- `EXPIRED`;
- `NO_PATH`;
- `INVALID_TARGET`;
- `ROUND_SEALED`;
- `PLAYER_NOT_VALID`;
- `NO_PROGRESS`.

---

## Detector de stuck

Use deslocamento horizontal real, não apenas velocidade instantânea ou velocidade 3D.

Condição inicial sugerida:

- o bot recebeu intenção de movimento;
- o deslocamento 2D acumulado em 3,5 segundos foi menor que 40 unidades;
- a distância para o destino não reduziu de forma relevante;
- o bot não está plantando;
- o bot não está desarmando;
- o bot não está em escada;
- o bot não está em queda;
- o bot não está intencionalmente segurando uma posição;
- o round está ativo.

Após detectar stuck:

1. cancelar a intenção bloqueada;
2. limpar estado de parada indevido;
3. selecionar waypoint alternativo acessível;
4. impedir a reutilização imediata do waypoint problemático;
5. redefinir o temporizador de repath;
6. solicitar nova rota;
7. registrar a razão;
8. validar deslocamento depois da recuperação;
9. escalar para outro waypoint se continuar sem progresso.

Não use teleporte como primeira ação de recuperação.

Quando possível, selecionar um ponto seguro no setor atual ou adjacente validado pelo sistema de navegação.

Adicionar cooldown por waypoint problemático e contagem de falhas por destino.

### Limite de StandStill

Quando uma ação ONNX de `StandStill` ultrapassar o tempo permitido:

- reavaliar percepção;
- cancelar a renovação automática;
- liberar navegação;
- ou substituir por uma ação segura.

O limite deve ser configurável por contexto, pois uma parada defensiva válida não é igual a um bot agressivo preso.

---

## Bug 2: BuyState incorreto e loadout divergente

### Evidências

- Round 2 classificado como `FORCE_BUY`, embora seja aparentemente o pistol round oficial.
- Rounds 4 e 6 classificados como `FULL_ECO`, embora haja rifles, AWP, SMGs, coletes e utilitárias.
- Round 4 mostra MP9 na tabela inicial para alguns jogadores, mas o primeiro snapshot mostra M4A1 ou FAMAS sem evento intermediário.

### Hipótese a verificar

O cálculo e a emissão da tabela podem ocorrer:

- durante o Freeze Time;
- antes de `ExecuteDeterministicBuys`;
- depois de reduzir o dinheiro, mas antes de equipar a arma;
- usando somente dinheiro restante;
- usando inventário stale;
- usando estado do round anterior;
- calculando CT e TR por uma variável compartilhada;
- antes de processar pickups ou substituições.

### Correção

Calcular o estado separadamente para CT e TR depois da estabilização das compras.

Não classificar `BuyState` apenas por:

- dinheiro restante;
- dinheiro gasto;
- ou `Cash + EquipmentValue`.

Considere separadamente:

- `equipment_value_before_buy`;
- `equipment_value_after_buy`;
- `cash_before_buy`;
- `cash_after_buy`;
- `spent_during_freeze_time`;
- `primary_weapon_count`;
- `rifle_count`;
- `smg_count`;
- `shotgun_count`;
- `awp_count`;
- `armor_count`;
- `helmet_count`;
- `defuse_kit_count`;
- `utility_value`;
- `saved_weapon_count`;
- `round_number_in_half`;
- `pistol_round`;
- `team_side`;
- `loss_bonus`;
- `purchase_intent`;
- `buy_completion_state`.

Estados mínimos:

- `PISTOL_ROUND`;
- `FULL_ECO`;
- `LIGHT_BUY`;
- `FORCE_BUY`;
- `HALF_BUY`;
- `FULL_BUY`;
- `SAVE_WITH_WEAPONS`;
- `UNKNOWN_INCOMPLETE_BUY`.

Defina os limites em configuração ou constantes centralizadas e documentadas.

### Estabilização do loadout

A tabela de economia e loadout só deve ser emitida quando:

- todas as compras determinísticas terminarem;
- as armas estiverem equipadas;
- o inventário estiver estável;
- ou um timeout explícito tiver sido atingido.

Se houver timeout:

- registrar `buy_completion_state: TIMEOUT`;
- informar quais jogadores ainda estavam pendentes;
- não classificar silenciosamente como `FULL_ECO`.

Registrar eventos explícitos de:

- compra;
- arma concedida;
- pickup;
- drop;
- troca;
- arma removida;
- substituição;
- transferência entre jogadores.

O primeiro snapshot deve ser coerente com a tabela inicial, exceto quando um desses eventos justificar a diferença.

---

## Bug 3: ciclo de vida dos rounds

### Evidências

- o primeiro bloco aparece como Round 1, com dinheiro alto e loadouts de warmup;
- não existe `FIM_ROUND` para esse bloco;
- o round seguinte começa em `0 x 0`;
- existem eventos depois de `FIM_ROUND`;
- códigos de motivo aparecem somente como números;
- o arquivo termina durante o Round 6 sem informar se a captura foi encerrada de forma limpa.

### Hipótese a verificar

- warmup está sendo contado como round oficial;
- `mp_restartgame` ou `mp_warmup_end` reinicia o estado sem fechar adequadamente o bloco;
- `OnTick` continua escrevendo durante `mp_round_restart_delay`;
- não existe flag de round selado;
- callbacks tardios são escritos fora de ordem;
- o logger não possui identificador interno de round;
- o shutdown do plugin não finaliza os metadados de captura.

### Correção

Diferenciar explicitamente:

- `WARMUP`;
- `LIVE`;
- `RESTART_PENDING`;
- `ROUND_ACTIVE`;
- `ROUND_ENDED`;
- `POST_ROUND`;
- `MATCH_ENDED`;
- `MAP_CHANGE`;
- `PLUGIN_SHUTDOWN`.

Cada round deve possuir:

- `internal_round_id`;
- `official_round_number`;
- `round_number_in_half`;
- `match_phase`;
- `round_phase`;
- `started_at_tick`;
- `ended_at_tick`;
- `round_end_received`;
- `sealed`;
- `official_score_before`;
- `official_score_after`.

Warmup não pode consumir o número do primeiro round oficial.

Ele pode:

- ser ignorado pelo relatório principal;
- ou aparecer em uma seção separada claramente identificada como `WARMUP`.

### Selamento do round

Ao processar `FIM_ROUND`:

1. registrar o resultado;
2. registrar placar;
3. traduzir o motivo;
4. marcar o round como selado;
5. impedir novos eventos normais;
6. suspender ONNX, Trade Spacing e Counter-Strafe até o próximo round ativo;
7. limpar intenções de movimento;
8. preservar apenas callbacks administrativos necessários.

Eventos recebidos depois do selamento não podem aparecer como eventos normais.

---

## Ordenação temporal e eventos atrasados

Cada evento deve possuir:

- `round_id`;
- `game_tick`;
- `monotonic_timestamp_ms`;
- `event_sequence`;
- `round_time`;
- `event_phase`;
- `late_event`;
- `source_component`.

`event_sequence` deve ser incremental e único dentro da captura.

Se um callback chegar depois do round ter sido selado:

1. não atribuir ao round seguinte;
2. não escrever após `FIM_ROUND` como evento normal;
3. descartar ou armazenar em seção separada;
4. marcar como `late_event: true`;
5. registrar o `round_id` original quando identificável;
6. registrar `late_event_reason`;
7. contabilizar para diagnóstico.

Possíveis motivos:

- `CALLBACK_DELAY`;
- `ASYNC_COMPLETION`;
- `QUEUE_BACKLOG`;
- `TICK_AFTER_SEAL`;
- `UNKNOWN_ROUND`;
- `LOGGER_FLUSH_DELAY`.

---

## Motivos de fim do round

Mapear o enum real utilizado pela versão atual da API.

Não dependa apenas de números mágicos.

Registrar:

- código numérico;
- nome do enum;
- descrição legível;
- vencedor;
- placar anterior;
- placar posterior.

Se o código não estiver mapeado, registrar `UNKNOWN_<codigo>` sem inventar significado.

---

## Metadados de encerramento da captura

Ao fechar o relatório, registrar:

- `capture_closed_cleanly`;
- `capture_end_reason`;
- `last_round_complete`;
- `last_round_id`;
- `last_game_tick`;
- `plugin_shutdown_received`;
- `match_still_live`;
- `pending_event_count`;
- `late_event_count`;
- `unflushed_event_count`.

Valores possíveis para `capture_end_reason`:

- `MATCH_COMPLETED`;
- `MANUAL_STOP`;
- `PLUGIN_UNLOAD`;
- `SERVER_SHUTDOWN`;
- `MAP_CHANGE`;
- `PROCESS_CRASH_RECOVERY`;
- `IO_FAILURE`;
- `UNKNOWN`.

---

# BLOCO ALTO

## Bug 4: Wide Swing fora da faixa e Trade Spacing recíproco

### Evidências

Wide Swing:

- Round 2, distância `597u`, texto `janela 250-400u`;
- Round 4, distância `581u`, texto `janela 250-400u`.

Trade Spacing:

- distância de `1u`;
- distância de `0u`;
- bots compartilhando o mesmo XY;
- dois bots aplicando repulsão um ao outro em sequência.

### Hipóteses a verificar

#### Hipótese 4A

A condição real aceita até 600 unidades, enquanto o texto está fixo em 400.

#### Hipótese 4B

A elegibilidade é calculada com uma distância e o relatório imprime outra.

#### Hipótese 4C

A distância é recalculada depois do atraso de 0,6 segundo.

#### Hipótese 4D

Dois bots recebem o mesmo waypoint e o NavMesh tenta recolocá-los no mesmo destino depois da repulsão.

#### Hipótese 4E

A escolha de quem deve ceder não é determinística, criando ping-pong.

### Correção

Utilizar explicitamente:

- `evaluated_distance`;
- `minimum_distance`;
- `maximum_distance`;
- `distance_dimension`, como 2D ou 3D;
- `evaluation_tick`;
- `execution_tick`.

A condição e o texto devem usar os mesmos valores.

Não registrar que uma distância está na janela quando estiver fora dela.

### Arbitragem do Trade Spacing

Adicionar estado por par de jogadores:

- chave ordenada do par;
- último agente que cedeu;
- último tick de correção;
- cooldown;
- offset aplicado;
- tempo de expiração;
- destino original;
- destino ajustado.

Aplicar cooldown inicial sugerido de 2,5 segundos, configurável.

Apenas um bot do par deve corrigir a posição por ciclo.

O critério deve ser determinístico e considerar, quando aplicável:

- função;
- prioridade tática;
- portador da C4;
- jogador em combate;
- proximidade do objetivo;
- slot;
- espaço disponível;
- rota mais curta;
- quem possui maior liberdade para ceder.

Não usar apenas o maior slot sem verificar a função tática.

O bot escolhido deve receber offset válido no NavMesh, e não apenas impulso temporário.

Se a distância 2D for zero:

- registrar sobreposição;
- verificar se os waypoints são idênticos;
- calcular offset seguro;
- impedir reatribuição imediata ao mesmo ponto;
- registrar `shared_target_detected`.

---

## Bug 5: Counter-Strafe excessivo

### Evidências

Foram observadas 35 ativações.

No Round 3, vários bots ativam Counter-Strafe repetidamente durante navegação sem evento aparente de disparo ou dano.

### Hipótese a verificar

A rotina pode estar baseada em uma condição ampla de percepção ou visão, sem exigir:

- linha de visão real;
- alinhamento de mira;
- arma pronta;
- intenção de ataque;
- alvo válido;
- cooldown;
- janela iminente de disparo.

### Correção

Counter-Strafe pode ocorrer antes do dano ou do disparo registrado. Portanto, não use somente `[COMBATE]` posterior como critério.

Exigir evidência de engajamento iminente:

- inimigo válido;
- inimigo vivo;
- linha de visão confirmada;
- erro angular abaixo do limite;
- arma apropriada;
- munição disponível;
- arma pronta;
- bot fora de recarga;
- intenção de ataque;
- previsão de disparo;
- ausência de obstáculo;
- cooldown respeitado;
- velocidade acima do limite que comprometeria a precisão.

Adicionar cooldown inicial sugerido de 2,5 segundos por bot, configurável por arma e contexto.

Registrar:

- `target_entity`;
- `target_distance`;
- `aim_error_degrees`;
- `has_line_of_sight`;
- `weapon_ready`;
- `ammo_available`;
- `attack_intent`;
- `anticipated_fire_tick`;
- `actual_fire_tick`;
- `counter_strafe_tick`;
- `cooldown_remaining`;
- `cancellation_reason`;
- `accuracy_before`;
- `accuracy_after`, quando disponível.

Cancelar Counter-Strafe se a intenção de disparo deixar de existir.

---

## Bug 6: pivôs táticos incorretos e setores hardcoded

### Evidências

- mensagens de First Kill indicam `"setor o Meio"` mesmo quando a morte e os jogadores estão em outra região;
- o sistema anuncia `EXECUTE no Bomb A` sem coerência com o local da vantagem;
- `"Limpou Bomb B"` é disparado quando o bot ainda parece estar em Tapete/Apartamentos B;
- snapshots posteriores continuam mostrando apenas a tática inicial.

### Hipóteses a verificar

- textos e destinos hardcoded;
- bounding boxes excessivamente amplas;
- setor do killer confundido com setor da vítima;
- coordenadas do bombsite incorretas;
- pivô baseado apenas na primeira morte;
- evento disparado sem confirmação da C4;
- plano tático mantido em cache sem versionamento.

### Correção

Usar dados reais:

- `killer_sector`;
- `victim_sector`;
- `killer_position`;
- `victim_position`;
- `victim_role`;
- `bomb_carrier`;
- `bomb_position`;
- `bomb_sector`;
- `site_control_evidence`;
- `alive_count`;
- `known_enemy_distribution`;
- `current_tactic`;
- `current_target_site`.

Não assumir automaticamente que um First Kill exige execução no bombsite oposto ou em A.

A decisão deve ser recalculada com base no estado real.

### Detecção de bombsite limpo

Não use apenas uma bounding box ampla.

Exigir combinação configurável de evidências, por exemplo:

- lurker dentro do perímetro real do bombsite;
- permanência mínima;
- ausência de inimigo visível;
- ausência de dano recebido recente;
- cobertura mínima de pontos relevantes;
- informação de áudio;
- confiança mínima;
- C4 disponível;
- rota viável;
- round ainda em estado adequado.

As coordenadas sugeridas no prompt são apenas indícios. Confirme os volumes reais no sistema do mapa antes de fixá-las.

---

## Versionamento obrigatório do plano tático

Diferenciar:

- `initial_tactic`;
- `current_tactic`;
- `tactic_revision`;
- `tactic_source`;
- `changed_at_tick`;
- `changed_at_round_time`;
- `change_reason`;
- `triggering_event`;
- `previous_target_site`;
- `current_target_site`;
- `confidence`;
- `candidate_tactics`.

Todo pivô deve incrementar `tactic_revision`.

Snapshots posteriores devem mostrar a tática vigente.

O evento de pivô deve registrar a decisão anterior e a nova decisão.

---

## Bug 7: JSON vazio ou repetitivo

### Evidências

- Rounds 1 e 2 mostram objetos CT e TR vazios;
- Rounds posteriores repetem praticamente o mesmo plano;
- não está claro se ocorreu resposta do Ollama, cache ou fallback.

### Hipóteses a verificar

- o logger escreve antes da conclusão da chamada assíncrona;
- o resultado chega depois da emissão do cabeçalho;
- existe race condition;
- cache sem chave adequada;
- fallback permanente;
- erro de parsing silencioso;
- plano anterior reutilizado;
- timeout não registrado.

### Correção

O JSON nunca deve conter CT ou TR vazios sem explicação.

Se a decisão ainda não estiver disponível:

- aplicar imediatamente um preset válido;
- registrar a origem;
- atualizar a decisão quando permitido pelo ciclo do round;
- ou aguardar dentro de um limite que não bloqueie o game thread.

Registrar:

- `decision_id`;
- `requested_at_tick`;
- `completed_at_tick`;
- `latency_ms`;
- `source`;
- `cache_hit`;
- `cache_key`;
- `fallback_used`;
- `fallback_reason`;
- `parse_status`;
- `model_response_status`;
- `selected_tactic`;
- `candidate_tactics`;
- `selection_scores`;
- `selection_reason`.

Fontes possíveis:

- `OLLAMA`;
- `FALLBACK_PRESET`;
- `CACHE`;
- `STATIC_DEFAULT`;
- `RECOVERED_PREVIOUS_VALID_PLAN`.

### Não forçar rotação artificial

Não proíba a repetição da mesma tática em rounds consecutivos.

Uma repetição pode ser correta.

O objetivo é impedir repetição causada por:

- cache incorreto;
- fallback permanente;
- resposta stale;
- chave de contexto incompleta;
- ausência de nova avaliação.

Se a mesma tática for selecionada novamente:

- executar nova avaliação;
- registrar candidatas e scores;
- registrar justificativa;
- registrar se houve penalidade de repetição;
- confirmar que não foi apenas reutilização indevida.

Pode existir penalidade configurável de repetição, mas não proibição absoluta.

---

# BLOCO MÉDIO

## Bug 8: dano bruto, dano aplicado e dano zero

### Evidências

- eventos de 122 e 126 HP;
- evento de zero HP;
- HP final nem sempre corresponde claramente ao dano textual.

### Correção

Registrar:

- `hp_before`;
- `raw_damage`;
- `applied_health_damage`;
- `armor_damage`;
- `hp_after`;
- `victim_alive_before`;
- `victim_alive_after`;
- `damage_event_id`;
- `source_event_id`;
- `duplicate_event`;
- `round_sealed`.

O texto principal deve exibir o dano efetivamente aplicado.

Exemplo esperado:

`Delrow causou 64 HP aplicados em McCoy com m4a1, dano bruto 126, vítima 64 -> 0 HP.`

Para dano zero, determine primeiro a causa real:

- `ARMOR_ONLY`;
- `DUPLICATE_DAMAGE_EVENT`;
- `DAMAGE_CANCELLED`;
- `TARGET_ALREADY_DEAD`;
- `ROUND_ALREADY_SEALED`;
- `ROUNDING_ARTIFACT`;
- `INVALID_EVENT`;
- `UNKNOWN_ZERO_DAMAGE`.

Não classificar automaticamente todo dano zero como `ARMOR_ONLY`.

Eventos de zero HP não devem aparecer como combate normal sem classificação.

Deduplicar callbacks por identidade do evento quando possível.

---

## Bug 9: velocidade acima do esperado

### Evidências

Foram observadas velocidades como:

- 535,1 u/s;
- 488,3 u/s;
- 453,2 u/s;
- 433,3 u/s;
- 424,5 u/s.

### Hipóteses a verificar

- magnitude 3D incluindo queda;
- uso incorreto de componente vertical;
- impulso de unstuck;
- salto;
- escada;
- knockback;
- cálculo entre snapshots com intervalo incorreto;
- velocidade acumulada;
- leitura de propriedade errada.

### Correção

A coluna principal deve mostrar `Velocity2D`.

Registrar separadamente:

- `velocity_2d`;
- `velocity_z`;
- `velocity_3d`;
- `airborne`;
- `on_ladder`;
- `falling`;
- `jumping`;
- `external_impulse`;
- `max_weapon_speed`;
- `speed_limit_applied`.

Qualquer impulso artificial deve respeitar o limite definido para o contexto.

Não aplique clamp indiscriminado à física real do jogo. Limite apenas comandos artificiais produzidos pelo plugin.

---

## Bug 10: excesso de setor Transição

### Correção

Revisar o classificador geográfico de `de_mirage`.

Cobrir pelo menos:

- CT Spawn;
- TR Spawn;
- Bomb A;
- Bomb B;
- Rampa A;
- Palácio A;
- Escadas A;
- Jungle;
- Conector;
- Janela;
- Top Mid;
- Meio;
- Underpass;
- Short;
- Catwalk;
- Apartamentos B;
- Tapete;
- Beco;
- Mercado;
- Kitchen;
- Van;
- Banco;
- Bench;
- Saída B;
- áreas de rotação relevantes.

Usar polígonos, volumes ou regiões adequadas, evitando apenas caixas amplas e sobrepostas.

Quando duas regiões coincidirem:

- utilizar prioridade;
- altura Z;
- conectividade do NavMesh;
- setor anterior;
- direção de deslocamento.

Registrar:

- `sector_id`;
- `sector_name`;
- `classification_method`;
- `classification_confidence`;
- `fallback_reason`.

Meta de validação:

- pelo menos 80% dos snapshots em posições conhecidas devem possuir setor específico diferente de `Transição`;
- `Transição` deve permanecer apenas como fallback legítimo.

---

## Bug 11: função do jogador e arma atribuída

### Evidências

- bots identificados como AWPer aparecem com MP9 ou FAMAS;
- EntryFragger recebe AWP;
- o relatório não separa função de perfil e função ativa.

### Correção

Diferenciar:

- `profile_role`;
- `round_role`;
- `assigned_weapon_role`;
- `current_weapon`;
- `role_assignment_reason`;
- `economy_override`;
- `pickup_override`.

Quando houver AWP:

- priorizar o bot com `BotRole.AWPer`;
- verificar recursos;
- verificar se o bot está vivo;
- verificar se outro jogador salvou a AWP;
- evitar compra duplicada;
- permitir exceção apenas com motivo registrado.

Não force transferência se isso criar perda de arma, duplicidade, drop inseguro ou conflito com o estado real.

---

# Testes automatizados obrigatórios

Adicione ou atualize testes para, no mínimo:

## Economia

- pistol round;
- full eco;
- force buy;
- half buy;
- full buy;
- save com armas;
- dinheiro alto com equipamento baixo;
- dinheiro baixo com equipamento alto;
- classificação independente de CT e TR;
- loadout estabilizado depois da compra;
- timeout de compra.

## Rounds

- warmup não contado como round oficial;
- restart;
- round end único;
- evento atrasado;
- evento após selamento;
- início do round seguinte;
- shutdown durante round;
- map change;
- captura parcial.

## Arbitragem de movimento

- múltiplas intenções no mesmo tick;
- prioridade;
- expiração;
- Counter-Strafe contra navegação;
- Unstuck contra ONNX;
- RoundLifecycle bloqueando movimento;
- ausência de sobrescrita depois da arbitragem;
- StandStill expirado.

## Stuck

- salto sem deslocamento XY;
- waypoint inalcançável;
- alvo idêntico para dois bots;
- repath;
- troca de waypoint;
- cooldown de waypoint problemático;
- recuperação bem-sucedida;
- recuperação falha e escalada.

## Trade Spacing

- distância zero;
- distância abaixo do limite;
- distância fora da faixa de Wide Swing;
- cooldown do par;
- apenas um bot cedendo;
- portador da C4 protegido;
- offset validado no NavMesh;
- ausência de ping-pong.

## Counter-Strafe

- inimigo sem linha de visão;
- inimigo fora do FOV;
- arma recarregando;
- sem munição;
- sem intenção de ataque;
- engajamento válido;
- cooldown;
- cancelamento antes do tiro.

## Telemetria

- dano bruto maior que HP;
- dano aplicado;
- dano zero;
- evento duplicado;
- velocidade 2D, Z e 3D;
- snapshots no mesmo segundo com sequência diferente;
- JSON vazio;
- fallback;
- captura encerrada parcialmente;
- pivô tático;
- mudança de revisão.

---

# Requisitos de implementação

- Evitar código duplicado.
- Centralizar constantes configuráveis.
- Não usar strings mágicas para estados, razões e origens.
- Preferir enums ou tipos estruturados.
- Manter compatibilidade com a versão atual do projeto.
- Não bloquear o game thread esperando Ollama.
- Tratar cancelamento e timeout de tarefas assíncronas.
- Proteger estados compartilhados.
- Limpar estado por round e por mapa.
- Manter logs suficientes para diagnóstico, sem gerar spam por tick.
- Aplicar rate limit e agregação na telemetria repetitiva.
- Não alterar mensagens apenas para mascarar inconsistências.
- Não desabilitar AUTO-ANOMALY para fazer a validação passar.

---

# Build e deploy

Depois das correções:

1. executar limpeza do projeto;
2. restaurar dependências;
3. compilar em configuração adequada para deploy;
4. executar testes automatizados;
5. verificar artefatos;
6. realizar backup dos binários instalados;
7. fazer deploy em `H:\CS2_AI_Server`;
8. registrar os arquivos implantados e seus hashes;
9. confirmar que o servidor carregou a nova versão;
10. confirmar que não restaram binários antigos conflitantes.

Comandos e processo devem respeitar a estrutura real da solução.

Meta:

- zero erros de compilação;
- zero testes falhando;
- zero exceções não tratadas.

A meta também é zero avisos. Caso exista aviso externo ou inevitável, não o oculte. Documente:

- código do aviso;
- projeto;
- origem;
- justificativa;
- risco;
- motivo pelo qual não foi corrigido.

Não use supressão indiscriminada de warnings.

---

# Nova captura de validação

Após o deploy, rode uma captura de pelo menos quatro a cinco rounds oficiais.

A captura deve incluir, quando possível:

- pistol round;
- round de eco;
- force ou half buy;
- full buy;
- combate em A;
- combate em B;
- pivô tático;
- Counter-Strafe válido;
- Trade Spacing;
- situação potencial de stuck;
- encerramento limpo da captura.

Não use dados sintéticos como substituição da validação no servidor.

Se não for possível rodar a partida automaticamente no ambiente do agente:

- não invente resultados;
- finalize build e testes;
- forneça comandos e checklist exatos para a execução;
- marque a validação em servidor como pendente.

---

# Critérios obrigatórios de aceitação

A correção somente poderá ser considerada aprovada se o novo log demonstrar:

1. Nenhum warmup contado como round oficial.
2. Primeiro round oficial identificado corretamente como pistol round quando aplicável.
3. Todo round oficial concluído possui exatamente um `FIM_ROUND`.
4. Nenhum evento normal aparece depois de `FIM_ROUND`.
5. Eventos atrasados são descartados ou classificados separadamente.
6. Todo evento possui `round_id`.
7. Todo evento possui `game_tick`.
8. Todo evento possui timestamp monotônico em milissegundos.
9. Todo evento possui `event_sequence`.
10. Não existem snapshots indistinguíveis apenas porque ocorreram no mesmo segundo.
11. O arquivo informa se a captura terminou completa ou parcialmente.
12. Nenhum JSON possui CT ou TR vazio sem diagnóstico.
13. Toda decisão informa `source`.
14. Todo fallback informa `fallback_reason`.
15. Repetição de tática possui nova avaliação e justificativa.
16. `BuyState` corresponde ao inventário pós-compra.
17. CT e TR são classificados independentemente.
18. Pistol round não é rotulado como Force Buy.
19. Full Buy não é rotulado como Full Eco.
20. A tabela de loadout corresponde ao primeiro snapshot.
21. Toda divergência de loadout possui evento explícito de compra, pickup, drop ou troca.
22. Nenhum Wide Swing ocorre fora da faixa configurada.
23. A distância usada na condição é a mesma mostrada no log.
24. Nenhum par executa repulsão recíproca dentro do cooldown.
25. Distância zero no Trade Spacing gera diagnóstico de waypoint compartilhado ou sobreposição.
26. Apenas um bot do par cede espaço por ciclo.
27. Nenhum bot que deveria mover permanece com deslocamento 2D menor que 40u por 3,5 segundos sem recuperação.
28. A recuperação troca efetivamente a rota ou waypoint quando necessário.
29. Saltos verticais não mascaram ausência de deslocamento XY.
30. Toda intenção de movimento informa se foi aplicada, bloqueada, substituída ou expirada.
31. Existe apenas um comando final de movimento por bot e por tick.
32. Counter-Strafe ocorre somente com evidência de engajamento iminente.
33. Counter-Strafe respeita cooldown.
34. Nenhum dano aplicado ultrapassa o HP anterior da vítima.
35. Nenhum dano zero aparece como combate normal sem classificação.
36. A velocidade principal dos snapshots é horizontal, `Velocity2D`.
37. Eventos airborne registram também `VelocityZ`.
38. Nenhum impulso artificial excede o limite configurado sem justificativa.
39. Todo pivô atualiza `current_tactic`.
40. Todo pivô incrementa `tactic_revision`.
41. Nenhum pivô usa setor ou bombsite hardcoded.
42. A detecção de bombsite limpo utiliza evidência real e confiança.
43. Pelo menos 80% das posições conhecidas recebem setor específico.
44. A AWP é priorizada para o AWPer, salvo justificativa registrada.
45. ONNX continua funcional.
46. A média de inferência permanece abaixo de 1 ms no mesmo ambiente, salvo justificativa objetiva.
47. O watchdog de granada e faca continua funcional.
48. Rifles e coletes continuam sendo entregues.
49. Não existem crashes ou exceções não tratadas.
50. Build termina com zero erros.
51. Todos os testes passam.
52. O deploy contém os binários novos e não mantém artefatos conflitantes.

---

# Requisitos de não regressão

Teste e confirme explicitamente:

- nenhum bot permanece segurando granada ou faca por período indevido;
- entrega de M4A1, AK-47, Galil, FAMAS, AWP e SMGs continua funcionando;
- coletes continuam sendo aplicados;
- utilitárias continuam sendo entregues;
- o ONNX continua ativo;
- a latência do ONNX não sofre regressão relevante;
- Counter-Strafe válido continua funcionando;
- Trade Spacing válido continua funcionando;
- placar continua sequencial;
- decisões táticas continuam sendo produzidas;
- relatório Markdown continua válido;
- nenhuma correção desativa silenciosamente componentes para reduzir alertas.

---

# Entrega final obrigatória

Apresente o resultado no seguinte formato:

## 1. Resumo executivo

- bugs confirmados;
- hipóteses refutadas;
- causas raiz;
- correções;
- riscos restantes;
- status geral.

## 2. Diagnóstico por bug

### Bug N

- Evidência original:
- Hipótese inicial:
- Arquivos investigados:
- Métodos investigados:
- Causa raiz confirmada:
- Hipótese confirmada, parcial ou refutada:
- Correção aplicada:
- Testes adicionados:
- Risco de regressão:
- Evidência de validação:
- Status: `CORRIGIDO`, `PARCIAL`, `NÃO CORRIGIDO` ou `NÃO REPRODUZIDO`

## 3. Arquivos alterados

Para cada arquivo:

- caminho;
- métodos alterados;
- finalidade;
- impacto;
- testes correspondentes.

## 4. Alterações arquiteturais

Descrever:

- arbitragem de movimento;
- ciclo de vida de round;
- ordenação de eventos;
- política de eventos atrasados;
- versionamento tático;
- classificação econômica;
- recuperação de stuck.

## 5. Build

- comando executado;
- configuração;
- resultado;
- erros;
- avisos;
- duração;
- artefatos gerados.

## 6. Testes

- comando executado;
- quantidade total;
- aprovados;
- falhos;
- ignorados;
- testes novos;
- cobertura dos bugs.

## 7. Deploy

- destino;
- backup;
- arquivos copiados;
- hashes;
- versão carregada;
- confirmação de inicialização.

## 8. Validação no novo log

Para cada critério de aceitação:

- critério;
- evidência;
- round;
- tick;
- resultado.

## 9. Não regressão

- watchdog de armas;
- rifles;
- coletes;
- utilitárias;
- ONNX;
- Counter-Strafe;
- Trade Spacing;
- placar;
- relatório;
- estabilidade.

## 10. Pendências

Não esconda pendências.

Para cada pendência:

- motivo;
- impacto;
- ação necessária;
- responsável;
- forma de validação.

---

# Restrições finais

- Não invente evidências do código.
- Não invente resultados de build.
- Não invente resultados da nova partida.
- Não declare um bug corrigido apenas porque a mensagem desapareceu.
- Não remova telemetria para fazer os critérios passarem.
- Não altere todos os módulos simultaneamente sem identificar a causa raiz.
- Não force diversidade tática artificial.
- Não classifique dano zero automaticamente como dano de armadura.
- Não use velocidade 3D para detectar progresso horizontal.
- Não permita múltiplos escritores finais de movimento no mesmo tick.
- Não considere a tarefa concluída se houver regressão nos avanços já confirmados.

A correção deve resolver as causas estruturais e deixar no novo relatório evidências suficientes para comprovar objetivamente cada resultado.