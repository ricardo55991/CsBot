# PROJETO BÔNUS: TREINAMENTO DE TRANSFORMERS ESPECIALIZADOS POR MAPA

## 0. DESCRIÇÃO DO PROJETO

### 0.1 O que é este projeto

Este projeto criará uma nova geração de modelos neurais especializados por mapa para o CsBotManager.

O sistema atual já possui:

- planejamento macro em C#;
- Utility AI IGL;
- catálogo de táticas;
- papéis por bot;
- materialização determinística de spots;
- navegação por NavMesh;
- MovementArbitrator;
- MovementExecutionTracker;
- modelo ONNX de micromovimento;
- recuperação de stuck;
- controle de economia;
- lógica de C4;
- retakes;
- saves;
- fakes;
- adaptações durante o round;
- telemetria forense.

A evolução proposta não substituirá essas camadas.

Serão criados dois modelos neurais especializados para cada mapa:

1. `Positioning Transformer`
2. `MLMove Transformer V2`

O `Positioning Transformer` aprenderá onde cada bot deve se posicionar e qual deve ser o próximo subobjetivo tático.

O `MLMove Transformer V2` aprenderá como o bot deve se movimentar localmente até esse objetivo.

A arquitetura permanecerá hierárquica:

    TacticalUtilityIglEngine
        ↓
    Tática, ritmo, papéis e bombsite
        ↓
    Positioning Transformer
        ↓
    Próximo setor, spot ou subobjetivo
        ↓
    NavMesh e validação determinística
        ↓
    MLMove Transformer V2
        ↓
    Movimento local
        ↓
    MovementArbitrator
        ↓
    Safety Gates
        ↓
    Source 2

### 0.2 Objetivo principal

Aprender comportamentos profissionais específicos de cada mapa utilizando demos de jogadores profissionais.

O sistema deverá aprender:

- posições defensivas;
- entradas em bombsites;
- staging;
- execuções;
- defaults;
- splits;
- fakes;
- lurkers;
- cobertura de AWPer;
- suporte ao Entry;
- proteção da C4;
- pós-plant;
- retakes;
- saves;
- rotações;
- crossfires;
- trade spacing;
- abertura de ângulos;
- micromovimentos;
- saltos pontuais e contextualizados.

### 0.3 O que os modelos não podem decidir

Os modelos neurais não podem alterar diretamente:

- `CurrentTactic`;
- `CurrentTargetSite`;
- `TacticRevision`;
- `BombObjectiveState.CommittedSite`;
- lado CT/TR;
- economia;
- compra;
- papel do bot;
- plano coletivo;
- C4 real site;
- OwnerTeam;
- lifecycle do round.

Essas autoridades permanecem no C#.

### 0.4 Casos de uso

#### Caso 1: Entry em Rush B

Contexto:

    tactic_id = TR_EXEC_B_APARTMENTS_RUSH
    role = ENTRY
    plan_stage = EXECUTING
    pace = FAST_CONTACT
    target_site = B

O Positioning Transformer pode escolher:

    próximo subgoal = entrada de Apartamentos B

O MLMove Transformer pode escolher:

    avanço acelerado;
    abertura lateral;
    Counter-Strafe;
    Duck;
    salto pontual contextualizado;
    recuo diante de molotov.

#### Caso 2: AWPer no mesmo Rush B

Contexto:

    tactic_id = TR_EXEC_B_APARTMENTS_RUSH
    role = AWPER
    plan_stage = COVERING
    target_site = B

O Positioning Transformer pode escolher:

    spot de cobertura;
    ângulo de rotação;
    posição atrás do Entry.

O MLMove Transformer pode escolher:

    shift;
    jiggle;
    parada;
    Counter-Strafe.

O AWPer não deve copiar o comportamento do Entry.

#### Caso 3: defesa CT 2-1-2

Contexto:

    tactic_id = CT_STANDARD_2_1_2_BALANCED

O modelo deve distribuir:

    2 CTs no A;
    1 CT no Meio;
    2 CTs no B.

Os CTs podem adaptar posições após informação, mas não podem abandonar responsabilidades sem trigger.

#### Caso 4: Fake A e execução B

Contexto:

    fake_site = A
    real_site = B
    bomb_carrier_group = B

O Positioning Transformer pode sugerir:

    grupo fake em A;
    grupo real em B;
    AWPer cobrindo rotação;
    lurker controlando Meio.

A C4 permanece obrigatoriamente no grupo real.

#### Caso 5: salto legítimo

O modelo detecta:

    obstáculo à frente;
    grounded;
    velocidade adequada;
    JumpZone válida.

O modelo produz:

    JumpPress = true
    JumpReason = ObstacleTraversal

O runtime emite `IN_JUMP` durante um único tick.

#### Caso 6: caminhada normal

O bot corre por piso plano.

O modelo não deve produzir saltos repetidos.

Resultado esperado:

    movimento contínuo;
    JumpPress = false.

### 0.5 Bunny hop

Bunny hop será removido do comportamento dos bots.

Não treinar nem executar:

- bunny hop;
- sequência automática de saltos na aterrissagem;
- manutenção contínua de `IN_JUMP`;
- salto repetido para ganho de velocidade;
- salto renovado enquanto airborne.

Se demos profissionais contiverem bunny hop:

- identificar o episódio;
- rotular como `BunnyHopAttempt`;
- excluir os frames de bunny hop da loss de `JumpPress`;
- não usar esses episódios como exemplos positivos de salto;
- manter opcionalmente os metadados apenas para auditoria;
- não expor `BunnyHopAttempt` como ação executável no runtime.

Saltos permitidos:

- travessia de obstáculo;
- jump peek;
- salto de entrada contextual;
- evasão pontual;
- recovery jump;
- drop transition;
- salto em NavLink homologado.

---

# 1. ARQUITETURA POR MAPA

Criar inicialmente dois modelos por mapa:

    de_mirage_positioning_v1.onnx
    de_mirage_mlmove_v2.onnx

Depois, repetir para outros mapas:

    de_inferno_positioning_v1.onnx
    de_inferno_mlmove_v2.onnx

Não criar um modelo multi-map nesta fase.

Cada mapa terá um pacote próprio:

    MapPolicyPacks/
      de_mirage/
        map_profile.json
        tactic_catalog.json
        positioning_feature_contract_v1.json
        mlmove_feature_contract_v2.json
        positioning_v1.onnx
        mlmove_v2.onnx
        model_manifest.json
        positioning_metrics.json
        mlmove_metrics.json
        jump_metrics.json

O manifesto deverá conter:

    map
    map_profile_version
    feature_contract_version
    positioning_model_version
    movement_model_version
    positioning_sha256
    movement_sha256
    demo_count
    match_count
    round_count
    trained_at_utc
    commit_hash
    parser_version
    dataset_version

---

# 2. AUTORIDADE ENTRE AS CAMADAS

## TacticalUtilityIglEngine

Decide:

- `tactic_id`;
- ritmo;
- formação;
- bombsite;
- papéis;
- fake site;
- real site;
- decisões econômicas;
- adaptação macro.

## Positioning Transformer

Sugere:

- próximo setor;
- tipo de subgoal;
- próximo spot entre candidatos válidos;
- duração de hold;
- trigger de saída;
- transição tática individual.

## C# determinístico

Valida e materializa:

- TeamSide;
- AssociatedBombsite;
- Usage;
- AllowedRoles;
- bounds;
- NavMesh;
- C4 committed site;
- OwnerTeam;
- ObjectiveRevision;
- SpotId real.

## MLMove Transformer

Sugere:

- avanço;
- recuo;
- strafe;
- velocidade;
- shift;
- duck;
- stop;
- `JumpPress`;
- `JumpReason`;
- pedido de repath;
- pedido de cancelamento de utilitária.

## MovementArbitrator

Decide qual intenção vence.

## Safety Gates

Validam:

- jump;
- lifecycle;
- arma;
- utilitária;
- faca;
- posição;
- bounds;
- entidade;
- objetivo de bomba.

---

# 3. FASE 0: CONGELAR O BASELINE ATUAL

Antes de alterar o treinamento:

1. registrar versão atual do plugin;
2. registrar SHA-256 da DLL;
3. registrar SHA-256 do ONNX V1;
4. registrar versão do perfil da Mirage;
5. registrar contratos atuais;
6. guardar build estável;
7. guardar configuração;
8. executar partida completa;
9. guardar log;
10. guardar métricas;
11. guardar vídeo ou demo de referência.

Criar:

    baseline_runtime_manifest.json
    baseline_metrics.json
    baseline_full_match.md
    baseline_model_manifest.json

Critério:

- baseline reproduzível;
- build atual recuperável;
- rollback disponível.

Não iniciar o pipeline V2 sem baseline congelado.

---

# 4. FASE 1: INVENTÁRIO DAS 449 DEMOS

Antes de baixar novas demos, inventariar as demos existentes.

Criar ferramenta:

    DemoInventoryTool

Extrair:

- hash;
- mapa;
- data;
- evento;
- times;
- jogadores;
- placar;
- duração;
- tickrate;
- rounds;
- versão/parser;
- integridade;
- duplicidade;
- quantidade de frames;
- posições;
- eventos disponíveis.

Gerar:

    demo_inventory.json
    demo_inventory_report.md
    duplicate_demos.json
    rejected_demos.json

## Distribuições obrigatórias

Por mapa:

    demos
    partidas
    rounds
    CT rounds
    TR rounds

Por tática:

    rushes
    defaults
    execuções
    splits
    fakes
    retakes
    saves
    clutches

Por papel:

    Entry
    SecondEntry
    Support
    AWPer
    Lurker
    Anchor
    Rotator
    BombCarrier
    Defuser

Por arma:

    rifles
    SMGs
    AWP
    pistols
    shotguns
    utility-heavy rounds

Por economia:

    pistol
    eco
    half-buy
    force-buy
    full-buy

### Critério de conclusão

Não baixar mais demos antes de conhecer:

- cobertura;
- classes raras;
- mapas insuficientes;
- distribuição por temporada;
- distribuição por time;
- distribuição por jogador.

---

# 5. FASE 2: COLETA ADICIONAL DE DEMOS

Após o inventário, baixar novas demos apenas para preencher lacunas.

Meta inicial por mapa:

    mínimo experimental: 200 a 300 demos
    cobertura boa: 500 a 800 demos
    cobertura forte: 1.000 ou mais demos diversas

Quantidade não é suficiente.

Diversificar:

- eventos;
- temporadas;
- times;
- jogadores;
- estilos;
- lados;
- economia;
- táticas;
- papéis;
- resultados;
- versões do jogo.

Recusar:

- demo corrompida;
- mapa errado;
- duplicada;
- incompleta;
- parser incompatível;
- dados insuficientes;
- tickrate desconhecido;
- arquivo sem rounds válidos.

Criar manifesto por demo contendo:

    demo_id
    source
    source_url, se permitido
    map
    event
    match_date
    team_ct
    team_tr
    parser_version
    file_sha256
    accepted
    rejection_reason

Não misturar licenças ou fontes sem registrar origem e permissão de uso.

---

# 6. FASE 3: SPLITS SEM VAZAMENTO

Nunca dividir frames aleatoriamente.

Separar por:

    evento
    partida
    demo
    round
    sequência

Criar:

    train_split.json
    validation_split.json
    test_split.json
    test_unseen_events.json
    test_unseen_teams.json
    test_unseen_players.json
    test_recent_meta.json

Distribuição inicial:

    train = 70%
    validation = 15%
    test = 15%

Garantias:

- nenhuma demo em mais de uma divisão;
- nenhuma partida dividida;
- nenhum round dividido;
- hashes auditados;
- distribuição comparável.

Teste obrigatório:

    NoDataLeakageAcrossSplits

---

# 7. FASE 4: EXTRAÇÃO BRUTA

Extrair por tick:

- posição;
- velocidade;
- view angles;
- grounded;
- airborne;
- botões;
- arma;
- munição;
- vida;
- armadura;
- utility inventory;
- posse da C4;
- inimigo visível;
- distância do inimigo;
- tiros;
- dano;
- mortes;
- plant;
- defuse;
- smoke;
- molotov;
- flash;
- som disponível;
- setor;
- NavMesh;
- round time;
- economia;
- score.

Não utilizar informações impossíveis no runtime.

Exemplos proibidos:

- posição exata de inimigo nunca observado;
- plano privado do adversário;
- informação futura;
- resultado do round;
- posição futura usada como feature atual.

Criar validação contra leakage temporal.

---

# 8. FASE 5: AMOSTRAGEM TEMPORAL

Frequências:

    Positioning Transformer: inicialmente 4 Hz
    MLMove Transformer: 16 Hz
    Jump/Event Head: 16 Hz

Não gerar decisões de posicionamento a 16 Hz.

Criar sequência temporal para posicionamento:

    8 a 32 amostras
    2 a 8 segundos

Criar sequência temporal para movimento:

    16 a 64 amostras
    1 a 4 segundos

Registrar:

    source_tickrate
    sample_rate
    interpolation_method
    dropped_samples
    time_alignment_error

---

# 9. FASE 6: RECONSTRUÇÃO DO ROUND

Gerar eventos tipados:

    RoundStart
    FreezeEnd
    FirstContact
    FirstKill
    EntryDeath
    TradeKill
    UtilityBlock
    SiteCommit
    Rotation
    Pivot
    BombDropped
    BombRecovered
    PlantStarted
    BombPlanted
    PostPlant
    RetakeStarted
    DefuseStarted
    SaveDecision
    RoundEnd

Cada evento deve conter:

    round_id
    tick
    time
    team
    players
    site
    confidence
    source

---

# 10. FASE 7: SEGMENTAÇÃO TÁTICA

Dividir cada round em segmentos:

    SETUP
    STAGING
    MAP_CONTROL
    CONTACT
    EXECUTING
    PLANTING
    POST_PLANT
    ROTATING
    RETAKE
    SAVE

Cada segmento deve conter:

    segment_id
    start_tick
    end_tick
    plan_stage
    tactic_label
    target_site
    pace
    confidence
    label_source

Não rotular frame isoladamente sem contexto da sequência.

Permitir:

    OTHER_STRUCTURED
    UNCLASSIFIED

Não forçar todo round em uma tática conhecida.

---

# 11. FASE 8: ROTULAGEM DE TÁTICAS

Utilizar os mesmos `tactic_id` do runtime.

CT Mirage:

    CT_STANDARD_2_1_2_BALANCED
    CT_2_1_2_HEAVY_ANCHOR_B
    CT_2_1_2_HEAVY_PALACE_RAMP_A
    CT_MID_AGGRESSIVE_DOMINANCE
    CT_ECO_STACK_GAMBLE_A
    CT_ECO_STACK_GAMBLE_B
    CT_RETAKE_PASSIVE_SETUP

TR Mirage:

    TR_SLOW_DEFAULT_MAP_CONTROL
    TR_EXEC_A_PALACE_RAMP_SPLIT
    TR_EXEC_B_APARTMENTS_RUSH
    TR_SPLIT_A_MID_TO_CONNECTOR
    TR_SPLIT_B_MID_TO_SHORT_CATWALK
    TR_FAKE_A_EXEC_B
    TR_FAKE_B_EXEC_A

Campos:

    tactic_id
    tactic_confidence
    label_source
    initial_site
    committed_site
    fake_site
    real_site
    tactic_revision

Fontes:

    deterministic_rules
    trajectory_classifier
    cluster_assisted
    human_reviewed

Não usar somente nome textual.

---

# 12. FASE 9: ROTULAGEM DE PAPÉIS

Papéis por round:

    ENTRY
    SECOND_ENTRY
    SUPPORT
    AWPER
    LURKER
    ANCHOR
    ROTATOR
    BOMB_CARRIER
    DEFUSER
    RETAKE_ENTRY
    RETAKE_COVER
    SAVE_PLAYER

Inferir por:

- ordem de entrada;
- arma;
- posição;
- distância do núcleo;
- primeiro contato;
- utilitárias;
- posse da C4;
- trajetória;
- posição pós-plant;
- função no retake;
- função de cobertura.

Campos:

    profile_role
    round_role
    is_bomb_carrier
    formation_position
    role_confidence
    label_source

Um jogador pode acumular flags.

---

# 13. FASE 10: DATASET DE POSICIONAMENTO

## Entrada individual

- posição normalizada;
- setor;
- subsector;
- velocidade;
- yaw;
- vida;
- armadura;
- arma;
- utilitárias;
- papel;
- estado da C4;
- economia.

## Entrada coletiva

- posições dos aliados;
- centroide;
- team spread;
- formação;
- ordem de entrada;
- distância ao Entry;
- distância à C4;
- setores ocupados;
- aliados vivos;
- inimigos vivos.

## Informação adversária permitida

- inimigo visível;
- última posição conhecida;
- tempo desde informação;
- áudio permitido;
- mortes;
- site pressure.

## Contexto macro

- `tactic_id`;
- pace;
- plan_stage;
- assigned_site;
- economy_state;
- round_time;
- score;
- match_history_summary;
- OwnerTeam;
- ObjectiveRevision.

## Geometria

- setor atual;
- setores adjacentes;
- spots candidatos;
- NavMesh;
- cover score;
- visibility score;
- distância;
- altura;
- bombsite.

## Saídas

- `NextSectorId`;
- `SemanticSubgoalType`;
- `CandidateSpotScores`;
- `TransitionType`;
- `HoldDurationBucket`;
- `ExitTrigger`;
- `Confidence`.

TransitionType:

    HOLD
    ADVANCE
    FALLBACK
    ROTATE
    CONVERGE
    LURK
    COVER
    RETAKE
    SAVE

ExitTrigger:

    TIME
    CONTACT
    FIRST_KILL
    BOMB_SPOTTED
    BOMB_PLANTED
    TEAMMATE_DEATH
    UTILITY_EXPIRED
    TACTIC_REVISION

---

# 14. FASE 11: NÃO PREVER SPOTID LIVRE

O modelo não deve emitir texto ou SpotId arbitrário.

Fluxo:

    modelo escolhe:
    semantic subgoal
    sector
    usage
    candidate scores

    C# filtra:
    TeamSide correto
    bombsite correto
    usage correto
    role compatível
    NavMesh válido
    bounds válidos
    OwnerTeam correto

    modelo ranqueia:
    candidatos homologados

    MapProfileManager materializa:
    SpotId real

Nunca permitir:

- SpotId inventado;
- spot CT para TR;
- spot TR para CT;
- spot do site falso para C4;
- goal fora de bounds.

---

# 15. FASE 12: MLMOVE V2

## Entradas

Preservar features úteis da V1.

Adicionar:

- macro tactic;
- pace;
- plan stage;
- role;
- assigned site;
- semantic subgoal;
- distance to subgoal;
- formation position;
- authorized hold;
- objective urgency;
- grounded;
- airborne;
- vertical velocity;
- time since grounded;
- time since last jump;
- obstacle ahead;
- obstacle height;
- floor delta;
- NavLink requires jump;
- drop ahead.

## Saídas contínuas

- forward magnitude;
- side magnitude;
- speed scale;
- shift;
- duck;
- stop probability.

## Saídas discretas

- `JumpPress`;
- `JumpReason`;
- `RepathRequest`;
- `UtilityCancelRequest`.

Não incluir bunny hop como saída executável.

---

# 16. FASE 13: EXTRAÇÃO DE EPISÓDIOS DE SALTO

Criar:

    JumpEpisodeExtractor

Cada episódio:

    JumpEpisodeId
    PlayerId
    RoundId
    PressTick
    TakeoffTick
    LandingTick
    StartPosition
    LandingPosition
    HorizontalSpeed
    VerticalSpeed
    JumpReason
    Confidence
    LabelSource

Detectar `JumpPress` somente na borda:

    previousJumpButton = false
    currentJumpButton = true
    grounded = true

Frames airborne:

    JumpPress = false
    Airborne = true

---

# 17. FASE 14: REMOVER BUNNY HOP

Criar detector:

    BunnyHopEpisodeDetector

Critérios possíveis:

- novo salto imediatamente após landing;
- sequência de múltiplos saltos;
- aumento ou manutenção de velocidade;
- ausência de obstáculo;
- trajetória longa;
- intervalos regulares.

Rotular:

    ExcludedTechnique.BunnyHop

Regras:

- excluir episódios da loss de `JumpPress`;
- excluir de oversampling;
- excluir de hard-positive mining;
- não exportar classe executável;
- manter contagem no relatório;
- permitir auditoria;
- não apagar a demo inteira;
- preservar frames anteriores e posteriores que não pertencem ao episódio.

Métrica:

    BunnyHopEpisodesExcluded
    BunnyHopFramesExcluded
    AffectedDemos
    AffectedPlayers

Teste:

    BunnyHopSequenceDoesNotCreateJumpPressTrainingTargets

---

# 18. FASE 15: CATEGORIZAR MOTIVO DO SALTO

Taxonomia executável:

    None
    ObstacleTraversal
    JumpPeek
    AggressiveEntry
    Evasion
    Recovery
    DropTransition
    Unknown

Não incluir `BunnyHopAttempt` na saída do modelo.

Sinais:

## ObstacleTraversal

- obstáculo;
- diferença de altura;
- NavLink;
- landing region;
- progressão após landing.

## JumpPeek

- quina;
- exposição curta;
- mudança de yaw;
- retorno à cobertura.

## AggressiveEntry

- Entry;
- chokepoint;
- execução;
- alta velocidade;
- bombsite.

## Evasion

- dano;
- tiro próximo;
- inimigo;
- strafe brusco.

## Recovery

- progresso anterior baixo;
- colisão;
- saída de bloqueio.

## DropTransition

- mudança de altura;
- NavLink;
- região de landing.

## Unknown

- confiança insuficiente.

Campos:

    JumpReason
    JumpConfidence
    LabelSource

Loss do motivo ponderada por confiança.

---

# 19. FASE 16: MAPA DE SALTOS

Criar por mapa:

    JumpZones
    TraversalLinks
    DropZones
    NoJumpZones

Cada JumpZone:

    zone_id
    bounds
    allowed_reason
    preferred_direction
    landing_region
    min_speed
    max_speed
    role_compatibility

NoJumpZones:

- plant;
- defuse;
- AWP hold;
- save hold;
- utility alignment;
- posições estreitas;
- staging passivo.

NoJumpZone reduz ou bloqueia `JumpPress`, exceto em emergência/recovery validado.

---

# 20. FASE 17: JUMP HEAD

Saídas:

    JumpPressProbability
    JumpReasonLogits
    ExpectedLandingTime
    ExpectedLandingRegion

Loss:

    L_jump_press
    L_jump_reason
    L_landing_time
    L_landing_region
    L_airborne_reissue
    L_temporal_consistency

Penalizar:

- JumpPress enquanto airborne;
- novo JumpPress sem landing;
- salto sem contexto;
- salto em NoJumpZone sem exceção;
- sequência parecida com bunny hop.

Não tornar penalidade absoluta para ações legítimas.

---

# 21. FASE 18: JUMPEXECUTIONGATE

Criar gate determinístico no C#.

Entrada:

    JumpPressProbability
    JumpReason
    JumpConfidence
    grounded
    airborne
    cooldown
    current context
    JumpZone
    NoJumpZone

Regras:

- emitir `IN_JUMP` por um único tick;
- edge-trigger;
- bloquear renovação airborne;
- exigir landing antes de novo salto;
- aplicar cooldown;
- impedir salto em plant;
- impedir salto em defuse;
- impedir salto em hold;
- impedir salto em cobertura de AWP;
- impedir salto em UtilityWait;
- permitir recovery;
- permitir obstáculo;
- permitir jump peek contextual.

Não implementar bunny hop.

Métricas:

    JumpRequested
    JumpExecuted
    JumpSuppressedAirborne
    JumpSuppressedCooldown
    JumpSuppressedContext
    JumpSuppressedNoJumpZone
    JumpByReason
    RepeatedJumpSequences

---

# 22. FASE 19: BALANCEAMENTO

Balancear por episódio, não por frames repetidos.

Dimensões:

- papel;
- tática;
- etapa;
- site;
- economia;
- arma;
- setor;
- evento raro.

Não fazer oversampling agressivo de Jump.

Usar moderadamente:

- class weights;
- focal loss;
- hard-negative mining;
- event sampling;
- confidence weighting.

Hard negatives para Jump:

- corrida em piso plano;
- saída do spawn;
- entrada normal;
- Counter-Strafe;
- shift;
- AWPer hold;
- staging;
- smoke wait;
- molotov wait;
- save rotation.

---

# 23. FASE 20: ARQUITETURA DOS MODELOS

## Positioning Transformer

Configuração inicial experimental:

    layers: 2 a 4
    hidden dimension: 128 a 256
    attention heads: 4 a 8
    sample rate: 4 Hz
    sequence: 8 a 32 tokens

Tokens:

    player
    teammates
    objective
    tactic
    role
    sectors
    candidate spots

## MLMove Transformer

Configuração inicial experimental:

    layers: 2 a 4
    hidden dimension: 128 a 256
    attention heads: 4 a 8
    sample rate: 16 Hz
    sequence: 16 a 64 tokens

Não escolher arquitetura máxima antes do benchmark.

---

# 24. FASE 21: LOSSES

## Positioning

    L_positioning =
        w1 * NextSectorLoss
      + w2 * SpotRankingLoss
      + w3 * TransitionLoss
      + w4 * HoldDurationLoss
      + w5 * ExitTriggerLoss
      + w6 * TeamSpacingLoss
      + w7 * RoleConsistencyLoss

## Movimento

    L_movement =
        forward loss
      + side loss
      + speed loss
      + shift loss
      + duck loss
      + stop loss

## Jump

    L_jump =
        jump press loss
      + jump reason loss
      + landing time loss
      + landing region loss
      + airborne reissue penalty
      + temporal consistency penalty

## Total

    L_total =
        L_movement
      + alpha * L_positioning, se treino conjunto futuro
      + beta * L_jump
      + gamma * auxiliary losses

Não iniciar com treino conjunto completo.

---

# 25. FASE 22: TREINAMENTO EM ETAPAS

## A. Baseline V1

Reproduzir o modelo atual.

## B. Positioning Transformer

Treinar isoladamente.

## C. MLMove contínuo

Sem Jump Head.

## D. Jump Head

Apenas episódios válidos e de alta confiança.

## E. Contexto macro

Adicionar tokens da Utility AI.

## F. Fine-tuning

Fine-tuning moderado, evitando destruir movimento aprendido.

## G. Exportação

Exportar ONNX.

## H. Shadow mode

Modelos não controlam inicialmente.

## I. Canary

Controle gradual.

Não avançar de fase com regressão.

---

# 26. FASE 23: MÉTRICAS OFFLINE

## Positioning

- Top-1 setor;
- Top-3 setor;
- Top-1 spot;
- Top-5 spot;
- MRR;
- Transition F1;
- ExitTrigger F1;
- HoldDuration MAE;
- RoleConsistency;
- SiteConsistency.

## Movimento

- Forward MAE;
- Side MAE;
- Stop F1;
- Shift F1;
- Duck F1;
- Action Top-1;
- Action Top-3.

## Jump

- JumpPress Precision;
- JumpPress Recall;
- JumpPress F1;
- FalseJumpRate;
- AirborneReissueRate;
- RepeatedJumpRate;
- ObstacleJumpSuccess;
- JumpPeekSuccess;
- RecoveryJumpSuccess;
- BunnyHopEpisodesExcluded.

## Coletivo

- trade distance;
- C4 protection;
- formation correctness;
- crossfire coverage;
- site convergence time;
- spacing.

---

# 27. FASE 24: VALIDAÇÃO VISUAL

Criar protocolo visual:

    20 entradas A
    20 entradas B
    20 defaults
    20 defesas 2-1-2
    10 Fake A → B
    10 Fake B → A
    20 retakes
    20 saves
    20 saltos
    20 recoveries

Classificação:

    Natural
    Acceptable
    Strange
    Bug

Registrar:

    mapa
    demo
    round
    bot
    papel
    tática
    timestamp
    observação

Aprovação exige métricas e revisão visual.

---

# 28. FASE 25: PARIDADE PYTORCH E ONNX

Para amostras representativas:

- executar PyTorch;
- executar ONNX Runtime;
- comparar logits;
- comparar ações;
- comparar rankings;
- comparar JumpPress;
- comparar latência.

Gerar:

    max_absolute_error
    mean_absolute_error
    top1_agreement
    top3_overlap
    jump_decision_agreement

Não implantar modelo sem paridade.

---

# 29. FASE 26: SHADOW MODE

## Positioning

Utility AI continua controlando.

Transformer sugere paralelamente.

Registrar:

    UtilityAiSpot
    TransformerSpot
    TransformerSector
    Divergence
    Validity
    Latency

## MLMove V2

V1 controla.

V2 prediz paralelamente.

Registrar:

    V1Action
    V2Action
    JumpPress
    JumpReason
    GateResult
    Latency

Critérios:

- sem SpotId inválido;
- sem bombsite incorreto;
- sem owner team incorreto;
- sem bunny hop;
- Jump controlado;
- latência aceitável;
- generalização.

---

# 30. FASE 27: CANARY E ROLLBACK

Etapas:

1. Positioning V1 em um bot;
2. MLMove V2 em um bot;
3. um time;
4. todos os bots;
5. partida completa;
6. múltiplas partidas.

Flags:

    EnablePositioningTransformer
    EnableMlMoveV2
    EnableJumpHead
    EnableShadowInference
    PositioningModelVersion
    MlMoveModelVersion

Rollback:

    EnablePositioningTransformer=false
    EnableMlMoveV2=false
    MlMoveModelVersion=v1

Rollback deve ser testado antes do canary.

---

# 31. FASE 28: NOVOS MAPAS E CONCLUSÃO

Depois da Mirage:

1. escolher segundo mapa;
2. criar perfil;
3. criar catálogo;
4. criar bounds;
5. criar spots;
6. criar JumpZones;
7. inventariar demos;
8. treinar modelos separados;
9. validar;
10. fazer shadow;
11. canary;
12. homologar.

Somente avaliar modelo multi-map depois de pelo menos dois ou três mapas homologados.

---

# 32. TESTES OBRIGATÓRIOS

## Dataset

- splits sem leakage;
- hashes;
- duplicidade;
- ordem temporal;
- features finitas;
- labels válidos;
- informação futura ausente.

## Táticas

- tactic ID válido;
- site coerente;
- papel coerente;
- fake site diferente do real site;
- C4 no grupo real.

## Positioning

- spot candidato válido;
- TeamSide correto;
- bombsite correto;
- role permitido;
- bounds;
- NavMesh;
- nenhum SpotId inventado.

## Jump

- borda cria um JumpPress;
- frames airborne não criam JumpPress;
- landing libera próximo salto válido;
- bunny hop é excluído;
- obstáculo preserva salto;
- JumpPeek preservado;
- recovery preservado;
- piso plano gera hard negative;
- NoJumpZone suprime;
- runtime emite um tick;
- airborne não renova;
- bunny hop nunca é executado.

## Exportação

- PyTorch/ONNX parity;
- shapes;
- contratos;
- versões;
- hashes;
- latência.

## Runtime

- shadow não controla;
- canary controla apenas bot autorizado;
- rollback funciona;
- falha do modelo usa fallback;
- Utility AI permanece autoritativa;
- C4 permanece autoritativa no C#.

---

# 33. CRITÉRIOS DE APROVAÇÃO

## Dataset

- sem leakage;
- cobertura documentada;
- labels auditados;
- baixa taxa de desconhecidos;
- distribuição aceitável.

## Positioning

- melhora sobre baseline;
- nenhum spot inválido;
- formações coerentes;
- papéis preservados;
- C4 protegida.

## MLMove

- movimento natural;
- baixo jitter;
- bom progresso;
- saltos ocasionais;
- zero bunny hop;
- baixo AirborneReissueRate.

## Runtime

- sem crash;
- latência aceitável;
- sem regressão de lifecycle;
- sem regressão de economia;
- sem regressão de táticas;
- sem regressão de retake;
- sem regressão de C4.

---

# 34. ENTREGÁVEIS

Criar:

    demo_inventory_report.md
    dataset_quality_report.md
    duplicate_demos.json
    rejected_demos.json
    tactic_distribution.json
    role_distribution.json
    jump_episode_distribution.json
    bunnyhop_exclusion_report.json
    positioning_feature_contract_v1.json
    mlmove_feature_contract_v2.json
    dataset_manifest_v2.json
    train_split_v2.json
    validation_split_v2.json
    test_split_v2.json
    positioning_transformer_v1.pt
    mlmove_transformer_v2.pt
    de_mirage_positioning_v1.onnx
    de_mirage_mlmove_v2.onnx
    pytorch_onnx_parity_report.md
    shadow_evaluation_report.md
    canary_report.md
    visual_evaluation_report.md

---

# 35. ORDEM PRÁTICA DE IMPLEMENTAÇÃO

Executar primeiro:

1. congelar baseline;
2. inventariar 449 demos;
3. auditar demos;
4. criar splits;
5. implementar extrator bruto;
6. implementar reconstrução de round;
7. implementar segmentação tática;
8. implementar rotulagem de papéis;
9. implementar JumpEpisodeExtractor;
10. implementar BunnyHopEpisodeDetector;
11. gerar relatórios de distribuição;
12. revisar dataset;
13. decidir se novas demos são necessárias;
14. coletar demos adicionais;
15. criar contratos;
16. treinar Positioning Transformer;
17. treinar MLMove contínuo;
18. treinar Jump Head;
19. exportar;
20. validar paridade;
21. shadow mode;
22. canary;
23. homologar Mirage;
24. iniciar segundo mapa.

---

# 36. PRIMEIRA ENTREGA DO AGENTE

Não treinar modelo imediatamente.

A primeira entrega deve conter somente:

1. diagnóstico do pipeline atual;
2. inventário das 449 demos;
3. distribuição por mapa;
4. distribuição por tática;
5. distribuição por papel;
6. distribuição por estágio;
7. distribuição de saltos;
8. quantidade de bunny hops excluíveis;
9. análise de qualidade;
10. análise de duplicidade;
11. proposta de splits;
12. lacunas de dados;
13. recomendação objetiva sobre novas demos;
14. arquitetura das ferramentas de extração;
15. contratos preliminares;
16. riscos;
17. cronograma por fases.

Decisão final da primeira entrega:

    DATASET_READY_FOR_V2_PIPELINE

ou:

    DATASET_NOT_READY_FOR_V2_PIPELINE

Não iniciar treinamento sem essa decisão.

---

# 37. REGRAS FINAIS

Não:

- treinar tudo de uma vez;
- criar modelo multi-map agora;
- permitir SpotId livre;
- substituir Utility AI;
- remover fallback;
- permitir bunny hop;
- tratar Jump como ação contínua;
- usar frames do mesmo round em splits diferentes;
- usar informação futura;
- baixar demos sem inventário;
- implantar modelo sem shadow;
- implantar sem rollback;
- validar apenas por accuracy;
- ignorar revisão visual.

O projeto estará concluído quando:

- cada mapa possuir modelos especializados;
- Positioning Transformer escolher subgoals válidos;
- MLMove V2 produzir movimento natural;
- Jump ocorrer apenas como evento contextual;
- nenhum bunny hop for executado;
- papéis, táticas e C4 permanecerem sob autoridade do C#;
- o sistema passar por shadow, canary e partida completa.