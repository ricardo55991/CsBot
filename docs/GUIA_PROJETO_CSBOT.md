# Guia do Projeto: IA para Bots no CS2 (CsBot)

Este documento é a transcrição estruturada e detalhada da conversa inicial de planejamento técnico. Ele funciona como o **Guia Mestre de Arquitetura e Virtudes** do projeto, servindo de bússola para todas as fases de implementação.

---

## 1. Visão Geral e Filosofia (As Virtudes da Ideia)

### Motivação
- Proporcionar uma experiência **offline competitiva, imersiva e de alto nível** no Counter-Strike 2.
- Evitar o ambiente tóxico das filas ranqueadas online, mas sem a frustração dos bots nativos da Valve (que são passivos, sem táticas, sem movimentação tática e previsíveis).
- Permitir que o jogador atue como líder ou membro de um time que se comunica, executa estratégias sincronizadas e respeita os padrões do CS competitivo real.

### Os Pilares Inegociáveis (Virtudes)
1. **Comportamento Humano e Justo (Sem Trapaças Nativas)**:
   - Bots não possuem wallhack nem mira teletransportada.
   - Visão via Raycasting (`TraceRay`) com FOV realista (~90°), respeitando paredes e fumaça de smokes.
   - Audição baseada em eventos do motor (`player_footstep`, `weapon_fire`, `grenade_bounce`) em raios de distância calculados.
   - Mira humanizada com curva suave (ruído de interpolação matemática/Perlin Noise), taxa de headshot controlada e compensação de recuo (spray) calibrada em estatísticas reais (patentes Xerife/Águia; tempo de reação entre 220ms e 280ms).
2. **Orquestração Estratégica Macro vs. Micro**:
   - A inteligência tática do time é centralizada em um modelo de linguagem leve (SLM local), agindo como o **In-Game Leader (IGL)**.
   - A execução motora em tempo real roda diretamente no motor do jogo a 64 ticks por segundo através do `BotLocomotionDriver` integrado ao `BotControllerApi.dll`.
3. **Comunicação Tática e Feedback Visual**:
   - Um **Chip HUD** visível no topo da tela indica a tática decidida para a rodada.
   - O jogador pode aceitar a tática sugerida, alterá-la via chat (`!tatica`, `!rejeitar`) ou falar no microfone (Push-to-Talk).
4. **Economia Real e Drops Inteligentes**:
   - Inteligência de compra matemática determinística em C# (Full Buy, Force Buy, Half-Buy/Bonus, Full Eco).
   - Compra inteligente de utilitárias estritamente alinhadas com a função do bot na tática.
   - Sistema de drops mútuos: bot dropa arma para o AWPer, bot dropa arma para o jogador mediante comando ou carência financeira.
5. **Arquétipos Competitivos e Troca Dinâmica (Dynamic Swap)**:
   - Divisão clássica de funções: **AWPer**, **Entry Fragger**, **Rotator / Rifler**, **Anchor / Lurker**.
   - CT com setores e micro-variações; TR guiado por setups dinâmicos.
   - Detecção da intenção do jogador: se o jogador se deslocar para um setor no Freeze Time, o bot desse setor cede a posição e assume outra função livre.
6. **Ambiente Seguro e Liberdade Cosmética**:
   - Execução em Servidor Dedicado Local (`cs2.exe -dedicated -insecure`), permitindo carregar facas, luvas, skins e agentes sem risco de banimento VAC.

---

## 2. Arquitetura Técnica: O Padrão dos "Dois Cérebros"

Um servidor de CS2 opera a 64 ticks por segundo (~15.6 ms por tick). Nenhum modelo de linguagem (LLM/SLM) possui tempo de inferência inferior a 15 ms para controlar inputs de mira ou teclas tick-a-tick. Por isso, a arquitetura divide estritamente as responsabilidades:

| Camada | Tecnologia / Componente | Frequência de Execução | Responsabilidades |
| :--- | :--- | :--- | :--- |
| **Cérebro 1: Macro**<br>*(O Capitão / IGL)* | SLM Local via Ollama<br>(**Qwen 2.5 3B Instruct** Q4_K_M) | Apenas em **Eventos**<br>(Freeze Time, mortes críticas, plant/drop da C4, comando de voz) | Lê o estado do jogo (placar, economia, mortes, mapa), interpreta comandos do jogador e retorna um JSON estruturado com os papéis e metas de cada bot para a rodada ou situação. |
| **Cérebro 2: Micro**<br>*(O Soldado / Mecânica)* | Plugin C# (.NET) no **CounterStrikeSharp** + **BotControllerApi** / Heurísticas | A cada **Tick** (15.6 ms), latência < 1ms na CPU | Traduz as metas em movimentação física no NavMesh (`FollowPath`, `MoveToPoint`), arremesso parabólico de granadas, TraceRay, spray humanizado e strafes. |

---

## 3. Ecossistema Open-Source e Bibliotecas Base

1. **CounterStrikeSharp (CSS)**:
   - Framework open-source em C# (.NET) sobre Metamod:Source.
   - Permite interceptar eventos (`OnPlayerRunCmd`, `OnPlayerDeath`, etc.), teleportar/mover bots, controlar inputs virtuais, interagir com serviços de dinheiro e desenhar no HUD do cliente.
2. **BotControllerApi (`BotControllerApi.dll`)**:
   - Ponte C# nativa para a Source 2 com suporte a `FollowPath`, `MoveToPoint`, controle de `WaitTimer` e injeção de inputs físicos.
3. **cs2-WeaponPaints (`Nereziel`)**:
   - Plugin para CounterStrikeSharp que libera todas as skins, facas, luvas e agentes via servidor local com segurança através do banco MariaDB.
4. **Ollama + Qwen 2.5 3B Instruct (Q4_K_M)**:
   - Modelo de ~1.9 GB que roda confortavelmente na GPU com tempo de resposta de 200–400ms em modo estruturado (JSON Schema).
5. **faster-whisper**:
   - Modelo Whisper (small/base int8) para transcrição de áudio via Push-to-Talk na GPU, capturando comandos em português brasileiro.
6. **Arsenal Web UI & Launcher Unificado (FastAPI + Vanilla JS)**:
   - Painel web moderno rodando na porta `8080` conectado ao banco MariaDB local (`weaponpaints`). Inicializado de forma autônoma via `abrir_arsenal_skins.bat` ou pelo servidor. Oferece catálogo completo de 20 modelos de facas, 1.456 skins de armas, 94 luvas, 15 presets de acabamentos com preview global simultâneo, resolução de Paint IDs da Valve e aba visual de itens equipados com filtro em tempo real (CT/TR).

---

## 4. Estrutura dos Arquétipos dos Bots

| Bot / Arquétipo | Prioridade de Compra | Comportamento CT | Comportamento TR |
| :--- | :--- | :--- | :--- |
| **Bot 1: AWPer** | AWP > Scout > Rifle.<br>1 Smoke + 1 Flash. | Joga em setores de longa distância (Janela/Meio na Mirage, Ticket, Liga). | Suporte de longa distância, pick inicial (ex: Palácio/Meio), cobertura pós-plant. |
| **Bot 2: Entry Fragger / Spawner** | AK-47 / M4A1-S + Colete/Capacete + Flash/Molotov. | Posições de contato antecipado (Caverna/Conector). | Primeiro na fila do rush/execução; abre os ângulos e busca o first kill. |
| **Bot 3: Rotator / Rifler (Estrela)** | AK-47 / M4A4 + Kit de Granadas Completo + Defuse Kit. | Joga em posições de rotação rápida (Ligação, Short/L) para apoiar A ou B. | Segundo homem da fila (garante o trade kill) ou suporte tático imediato. Portador da C4 aos 11.5s. |
| **Bot 4: Anchor (CT) / Lurker (TR)** | Rifle ou MP9/XM1014 + Molotov/Smoke/Kit. | Âncora do Bomb B (não rotaciona precocemente até confirmação da C4; gasta utilitárias de atraso). | Lurk nas costas/extremidades opostas do mapa, punindo rotações CT. |

---

## 5. Inteligência Econômica Determinística (`EconomyManager.cs`)

O cálculo econômico **nunca** é delegado ao LLM. O C# avalia as carteiras e o histórico do Loss Bonus no início do Freeze Time:
- **FULL_BUY**: Carteira média > $4100 (TR) ou > $4700 (CT). Coletes completos, rifles principais e utilitárias completas.
- **FORCE_BUY**: Situações críticas (pós-pistol round, round 12 do half, ou inimigo em Match Point).
- **HALF_BUY**: Economia intermediária (~$3100). Preserva pelo menos $2000 por jogador para garantir Full Buy no round seguinte.
- **FULL_ECO**: Carteira baixa (~$1900). Economia total para resetar o potencial financeiro.
- **Sistema de Drops e Saque**:
  - Detecção de carência de AWPer e jogador humano (`!drop`).
  - **Looting Tático Pós-Round**: Bots com SMG/Pistola varrem o chão em um raio de até 600 unidades para roubar AK-47, M4A1-S ou AWP de inimigos caídos, celebrando via comando de rádio `cheer`.

---

## 6. O Ciclo do Freeze Time (15 Segundos)

1. **Segundo 0.0 - 0.5**: `EconomyManager.cs` lê dados financeiros do time, determina o `BuyState` e calcula orçamento de utilitárias.
2. **Segundo 0.5 - 1.4**: O plugin C# envia requisição local ao Ollama (Qwen 2.5 3B) com mapa, lado, economia e histórico recente. A IA responde em formato JSON estruturado com o nome da tática e papéis dos 4 bots.
3. **Segundo 1.4**: O **Chip de Tática** aparece fixado no topo da tela do jogador (ex: `[HALF-BUY] Rush Contato Caverna + Pop-Flash`).
4. **Segundo 1.4 - 10.0**: Janela de decisão do jogador humano (chat ou microfone).
5. **Segundo 11.0**: O plugin C# executa a compra de armas e utilitárias.
6. **Segundo 11.5 (Disciplina da C4)**: Se a C4 tiver nascido nas mãos do Entry Fragger ou do Lurker, ela é repassada automaticamente para o Rotator/Suporte com call no rádio e chat de equipe.

---

## 7. Status de Implementação das Fases (100% Concluídas)

### Fase 1 (Concluída): Ambiente Base & Infraestrutura Isolada
- Servidor Dedicado CS2 local no Windows (`-dedicated -insecure +map de_mirage`) no disco `H:\CS2_AI_Server`.
- Isolamento total da pasta vanilla da Steam (risco ZERO de VAC Ban).
- Instalação e validação do Metamod:Source e CounterStrikeSharp.
- Instalação do pacote `WeaponPaints` com banco de dados MariaDB portátil (porta 3306).

### Fase 2 (Concluída): O Maestro Tático, Economia Determinística, Arquétipos & Chip HUD
- Criação da solução C# do plugin principal (`CsBotManager`).
- Implementação do `EconomyManager.cs` (cálculo de BuyState, regras de economia, trava de gastos e drops inteligentes com `!drop`).
- Implementação do `RoleManager.cs` (4 arquétipos: AWPer, Entry Fragger, Rotator, Anchor e Dynamic Swap com `!pos`).
- Integração assíncrona HTTP com Ollama local (`qwen2.5:3b` na GPU via Vulkan).
- Exibição do Chip HUD em tempo real no topo da tela (`PrintToCenterHtml`) e comandos `!tatica` e `!rejeitar`.

### Fase 3 (Concluída): Dinâmica Tática, Matriz de Variações, Ritmos de Round & Sobrevivência
- Implementação dos ritmos de round (`SLOW_DEFAULT`, `POKE_AND_ROTATE`, `TIMED_EXECUTE`, `FAST_CONTACT`).
- Matriz de 35 micro-pixels para a `de_mirage` (`TacticalSpotsManager.cs` + `TacticalSpots_de_mirage.json`).
- Ordem tática em 2 estágios por bot (Staging, Engagement Stance, Execute e Fallback).
- Randomização inteligente de micro-posições para o time adversário a cada round.
- Controlador de ritmo e sobrevivência (`PacingAndFallbackController.cs`): recuo tático de preservação de vida (`FALLBACK_ALIVE`).

### Fase 4 (Concluída): Inteligência Comportamental Avançada, Anti-Enjoador & Controle Físico Real
- **Módulo 1: Pirâmide de Probabilidade e Frequência (`TacticalProbabilityEngine.cs`)**:
  - Tier 1 (72% Padrão), Tier 2 (23% Variações com cooldown de 5 rounds), Tier 3 (5% Jogadas Raras 1x por partida).
- **Módulo 2: Coordenador de Utilitárias e Senso de Relógio (`UtilityAndClockCoordinator.cs`)**:
  - Chokepoint Lock (Anti-Duplicação de smokes), Molotov Reativa CT, Silêncio de Late-Round e Desespero de Relógio.
- **Módulo 3: Arquitetura Multi-Mapa Universal (`MapProfileManager.cs`)**:
  - Perfis em JSON (`de_mirage.json`, `de_dust2.json`, `de_inferno.json`) e Fallback Universal.
- **Módulo 4: Driver Motor Físico Source 2 (`BotLocomotionDriver.cs`)**:
  - Integração profunda com `BotControllerApi.dll` (`FollowPath`, `MoveToPoint`), eliminando o conflito com a IA nativa da Valve.
  - Salvaguarda física de Plant e Defuse (prioridade absoluta do objetivo).
  - Cálculo de arco parabólico vertical no arremesso de granadas (`ThrowUtility`).
- **Módulo 5: Inteligência Orgânica Competitiva**:
  - Chat de equipe e rádio nativo sincronizados (`PrintTeamChatAndRadio`).
  - Lógica orgânica de Save vs. Clutch Heroico (6% de tentativa heroica no TR e CT).
  - Anti-Fake Defuse inteligente no pós-plant (delay de 1.8s a 2.4s com abertura única e cobertura passiva).
  - Disciplina da C4 no freeze time (11.5s) e Looting pós-round de armas Tier-1.
- **Módulo 6: Comunicação Tática, Detecção de Rush & Callout Pós-Morte (`TacticalCalloutSystem.cs`)**:
  - *Spot & Fallback Info*: Bots informam quantidade exata de inimigos avistados, se portam AWP ou se a C4 foi avistada (`C4 VISTA na Rampa A!`), disparando rádio e chat de equipe antes do recuo.
  - *Detecção Instantânea de Rush*: Reconhece 3 ou mais inimigos rasgando o mesmo chokepoint em <= 3.5s (visão ou passos + granadas), emitindo alerta de emergência com rádio `needbackup` e convocando rotação imediata antes mesmo de cair em combate.
  - *Death & Damage Callout*: Call pós-morte com delay humano de 1.0s informando setor da morte, quantos inimigos estavam juntos e se deixou o assassino "MUITO MIADO" (-X HP) ou se foi AWP cravado, exibido com formato autêntico `(Morto) BotName: ...`.
  - *Audio Cue Callout*: Rastreia passos (`EventPlayerFootstep`) de inimigos correndo em raio de até 750 unidades sem linha de visão, avisando com cooldown anti-spam de 15s por setor.
- **Módulo 7: Matriz Contextual e Probabilística de Reação a Smokes e Sons (`ContextualSmokeAndAudioBrain.cs`)**:
  - Roleta ponderada dinâmica cruzando 4 variáveis em tempo real (som em setor vizinho nos últimos 5s, aliados no bomb, arma equipada e postura da equipe) para qualquer ponto do mapa:
    - *Cenário A (Smoke na Posição + Barulho Adjacente + 2+ Aliados no Bomb)*: 55% virar mira para a ameaça sonora (`takingfire`), 25% recuo para ângulo longo limpo (80% se AWP) e 20% pedido de pop-flash para abrir no som.
    - *Cenário B (Smoke na Posição + Silêncio Total)*: 45% segurar a borda da fumaça em postura passiva, 30% varrer o centro da smoke (50% se rifle silenciado), 15% buscar elevação/pixel alto e 10% rasgar a smoke de surpresa.
    - *Cenário C (Smoke na Posição + Bot Sozinho no Bomb)*: 75% recuo de sobrevivência para o fundo do bomb chamando rotação, e 25% marotagem furtiva de "rato" (Ninja/Firebox/Banco) para pegar o plantador de costas!
- **Módulo 8: Protocolo de Limpeza de Bomb e Plant Inteligente (`SiteClearAndPlantController.cs`)**:
  - *Entrada com Rifle em Mãos (`SiteClearing`)*: O portador da C4 entra no bomb com arma de fogo em punho sem puxar a bomba no aberto, enquanto o Entry e Support limpam os micro-pixels críticos do site.
  - *Validação de Segurança (`IsSiteSafeToPlant`)*: Só autoriza o plant se nenhum inimigo estiver no bomb, nenhum aliado tiver tomado dano nos últimos 2.0s, e houver cobertura ativa ou 3.5s de varredura (desespero com relógio < 12s).
  - *Pixel Safe vs. Aberto*: Escolhe dinamicamente entre plant fechado seguro (atrás de cobertura) e plant aberto para as posições dominadas pela equipe, com aviso no chat (`Bomb limpo! Plantando aberto pra Caverna/Palácio, me cobre!`).
- **Módulo 9: Cérebro de Retake CT — Smoke na Bomba e Fake Defuse (`CtRetakeAndDefuseBrain.cs`)**:
  - *Smoke Defuse*: Lança smoke diretamente na C4 antes de iniciar o desarme quando o tempo permitir (> 8s com kit ou > 13s sem kit), com aviso tático no chat.
  - *Roleta de Fake vs. Stick Defuse*:
    - Sob Smoke: 55% Stick Defuse ("Pros Don't Fake") e 45% Smoke Tap & Step-Out (toca 0.5s e dá passo lateral com rifle).
    - No Aberto: 60% Fake Defuse Clássico (tap 0.5s + bait de mira no chokepoint por 2.5s), 25% Half-Defuse Bait (segura 2.8s) e 15% Cold Stick (100% se tempo crítico < 7.5s com kit / < 11.5s sem kit).
- **Módulo 10: Telemetria Forense de Partida sob Demanda (`MatchTelemetryLogger.cs`)**:
  - Ativação sob demanda via comandos `!debug` (`!debug on/off`) e marcadores `!nota <texto>` (com suporte a comando de voz *"Nota de debug: ..."*).
  - 100% desligado por padrão (zero impacto de CPU e I/O).
  - Gera logs Markdown estruturados em `H:\CS2_AI_Server\debug_logs\` com resumo de round, linha do tempo `[MM:SS]`, utilitárias com origem/mira/destino, snapshots a cada 3.0s e detector automático de anomalias (`[⚠️ AUTO-ANOMALY]`).
- **Módulo 11: Macro-Pivô e Inteligência Tática TR de Mid-Round (`TrMacroPivotController.cs`)**:
  - *Brick Wall Pivot*: Diante de contenção massiva por fumaça/fogo ou queda do Entry sem trade na entrada do bomb, o IGL reavalia o plano com 3 saídas estatísticas:
    - **60% `HOLD_AND_RE_EXECUTE`**: O time recua para a Staging Area em `PASSIVE_HOLD` por ~16s aguardando as utilitárias CT dissiparem para repicar.
    - **34% `RESET_TO_DEFAULT`**: Aborta a invasão, cancela o Execute e espalha o time em rotas neutras buscando duelos isolados e abrindo espaço.
    - **6% `HARD_PIVOT_SILENT`**: Abandona o bomb atual e realiza um giro surpresa total para o outro bomb no Shift, punindo a super-rotação dos CTs.
  - *Oportunismo do Lurker (`Site Clearance Call`)*: Quando o Lurker abate um CT no bomb oposto ou isolado, valida a limpeza por 2.5s sem dano/contato, assume controle da rota de retake dos CTs com rádio `sectorclear`, e a equipe TR inteira converge com a C4 para o bomb limpo.
  - *Conversão de Pick em Execução (`Mid-Round Exploit`)*: Em rounds de jogo padrão (`SLOW_DEFAULT`), ao obter o First Kill em setor chave (Meio/Janela/Ligação), o IGL transita imediatamente de Staging para `Executing` em Split.
  - *Integração com `!debug`*: Todo pivô tático registra uma linha destacada `[MM:SS] 🔄 [PIVOT TÁTICO TR] ...` no log de telemetria.
- **Módulo 12: Setup de "Double AWP" Rico no CT (`EconomyManager.cs` / `RoleManager.cs`)**:
  - Quando o time CT atinge economia excelente (`TeamAverageMoney >= $7500`) em round de `FULL_BUY`, há 35% de chance de ativar a formação de duas snipers.
  - O bot Anchor (ex: âncora do Bomb B) é autorizado a comprar a 2ª AWP (ou recebe drop coordenado de um colega rico), sendo alocado em posições de mira longa (Van B ou Ticket A) com callout no chat: `"(Contraterrorista) IGL: Economia alta! Vamos de DOUBLE AWP, domina as pontas!"`.
- **Módulo 13: Prioridade Inteligente de Defuse (`CtRetakeAndDefuseBrain.cs`)**:
  - Intercepta `EventBombBegindefuse`: se o CT que começou o desarme não possuir Kit de Defuse, mas houver um aliado com Kit em um raio de até 400 unidades da C4, a ordem é transferida de imediato.
  - O bot sem kit cancela o uso, recua e adota postura de cobertura protegendo a C4 agachado, enquanto o portador do kit assume a defuse rápida (5 segundos) avisando no chat e rádio: `"(Contraterrorista) NomeDoBot: Deixa pra mim que eu tenho Kit! Cobre a defuse!"`.
- **Módulo 14: Mobilidade Inteligente com Faca & Freio Tático (`MobilityController.cs`)**:
  - Durante saídas de base para Staging, ritmo `FAST_CONTACT` ou rotações `ROTATE_SILENT`, se o bot estiver a mais de 600 unidades do chokepoint/alvo e nenhum inimigo tiver sido avistado na rota nos últimos 6.0 segundos, empunha a faca (`slot3`) para correr na velocidade máxima de 250 u/s.
  - *Freio Tático*: Ao se aproximar a <= 600u do chokepoint/spot de perigo, ou ao detectar inimigos visíveis, sofrer dano ou ouvir passos próximos, saca imediatamente a arma primária (`slot1`) em fração de segundos antes do contato.
- **Módulo 15: Swap para Pistola vs. Recarga Segura em Combate (`CombatAdapter.cs`)**:
  - Quando a arma primária do bot zera o pente (`clip1 == 0`) durante um combate ativo:
    - *Curta Distância (< 500u)*: Aborta a recarga no aberto, saca a pistola imediatamente (`slot2`) e continua disparando ("switching to your pistol is always faster than reloading").
    - *Média / Longa Distância (>= 500u)*: Aborta a exposição, aciona recuo imediato para cobertura furtiva (`MidRoundAction.HIDE_COVER`), recarrega em segurança atrás da parede e repica com Jiggle Peek após o tempo de recarga.

### Fase 5 (Concluída): Arsenal Web UI (Painel Visual de Skins & Gemas Doppler)
- **Servidor Web FastAPI (`H:\CS2_AI_Server\arsenal_web\app.py`) & Launcher Unificado**:
  - Porta `8080` com inicialização independente via `abrir_arsenal_skins.bat` na raiz do projeto ou automática via `start_cs2_ai_server.bat`.
  - Verificação e ativação autônoma do serviço MariaDB portátil (`H:\CS2_AI_Server\database\mariadb\bin\mysqld.exe`, porta 3306).
  - Conexão direta com MariaDB (`weaponpaints`) nas tabelas `wp_player_knife`, `wp_player_skins`, `wp_player_gloves`.
- **Catálogo Visual e Mapeamento Completo**:
  - **20 Modelos de Facas**: Karambit, Butterfly, M9 Bayonet, Bayonet, Flip, Gut, Huntsman, Falchion, Shadow Daggers, Bowie, Ursus, Navaja, Stiletto, Talon, Classic Knife, Skeleton, Survival, Nomad, Paracord e Kukri.
  - **556 Pinturas de Facas Mapeadas**: Incluindo as 14 variantes de Doppler/Gamma Doppler, Fade, Marble Fade, Tiger Tooth, Lore, Autotronic, Crimson Web, Slaughter e Case Hardened.
  - **35 Categorias de Armas e 1.456 Skins Reais**: Catálogo completo sem cortes artificiais, com busca instantânea por nome da arma e nome da skin renderizadas via CDN Nereziel.
  - **94 Luvas Reais**: Sport Gloves, Specialist, Driver, Moto, Hand Wraps, Broken Fang, Hydra e Bloodhound.
- **Preview Global Simultâneo de Acabamentos**:
  - Ao clicar em qualquer um dos 15 presets de acabamentos (ex: Doppler Ruby, Sapphire, Black Pearl, Emerald, Fade 100%, Tiger Tooth, Lore), a imagem de visualização e o badge de todos os 20 cards de facas no grid se atualizam simultaneamente em tempo real.
- **Resolução Inteligente de Paint IDs Específicos da Valve**:
  - Tratamento nativo das idiossincrasias do CS2 da Valve:
    - Butterfly e Shadow Daggers Phase 2 utilizam Paint ID `618` (e não `419`).
    - Butterfly e Shadow Daggers Sapphire utilizam Paint ID `619` (e não `416`).
    - Butterfly e Shadow Daggers Black Pearl utilizam Paint ID `617` (e não `417`).
    - Talon Knife Phase 2 utiliza Paint ID `853` (e não `419`).
    - Pinturas de Lore e Autotronic mapeadas conforme a tabela de identificadores por modelo de faca.
- **Salvaguarda Visual de Incompatibilidade Nativas da Valve**:
  - Facas que a Valve nunca lançou em determinadas famílias de pinturas no CS2 (como *Kukri Doppler* ou *Classic Knife Doppler*) exibem visualmente o badge **"NÃO DISPONÍVEL NO CS2"**, mantendo a imagem base do modelo e alertando o usuário de forma transparente que se trata de uma limitação do próprio jogo da Valve, e não de falha de carregamento.
- **Aba "Arsenal Equipado" com Renders Visuais e Filtro em Tempo Real**:
  - Inspeção visual de todos os itens configurados no banco de dados para o jogador: facas, luvas e armas convencionais.
  - Cards detalhados com foto HD da skin, nome oficial, selo de StatTrak (com contador de kills ativo), etiqueta NameTag personalizada e barra de desgaste de Float Wear (FN, MW, FT, WW, BS).
  - **Filtro em Tempo Real por Equipe**: Botões rápidos `TODOS`, `CT (Contraterroristas)` e `TR (Terroristas)` que filtram instantaneamente o inventário renderizado no grid sem recarregar a página.
- **Sincronização In-Game**:
  - Qualquer alteração salva na Web UI reflete instantaneamente no servidor CS2 ativo digitando `!wp` no chat do jogo.

### Fase 6 (Concluída): Arquitetura MLMove em 3 Camadas (Micro-Movimento Coordenado a 16Hz + Pipeline de Treinamento)
Inspirada no artigo acadêmico *MLMove (Dr. David Durst, Stanford / `csknow`)*, une o nosso cérebro Macro (Ollama IGL + Setups Táticos) a um motor de Micro-Locomoção Multi-Agente operando a **16 Hz (a cada 62.5ms / 4 ticks)**:
- **Camada 1 (`MicroMoveEngine.cs` — Concluída e Ativa no Servidor)**:
  - **Espaço de 97 Ações Discretas**: Codifica e decodifica `StandStill` (Ação `0`) + `96 combinações dinâmicas` (16 direções angulares de 22.5° × 3 velocidades [Run 250u/s, Walk/Shift 130u/s, Crouch 85u/s] × 2 estados de pulo), convertendo vetores globais para coordenadas relativas ao `EyeAngles.Y` do bot no `UserCmd`.
  - **Buffer de Inércia Multi-Horizonte (`0ms`, `+125ms`, `+250ms`)**: Estrutura `MicroMoveTrajectory` que armazena `Step0_Now`, `Step1_125ms` e `Step2_250ms` para eliminar tremedeiras (*jitter*) de mudanças de direção a cada tick isolado.
  - **Campos Potenciais Multi-Agente ($N \times N$)**:
    1. *Wall-Hugging / Geometria como Cover*: Ao cruzar chokepoints ou áreas de risco, puxa o vetor de movimento tangencialmente para as bordas/paredes, evitando caminhar exposto no meio do aberto.
    2. *Trade Spacing ($N \times N$ Attention entre Aliados)*: Aplica força de repulsão lateral quando dois aliados estão muito colados (`< 140 unidades`) para evitar bloqueio de strafe e morte dupla no mesmo spray; e posiciona o suporte na janela ideal de **250 a 400 unidades** com abertura escalonada (*Wide Swing* coordenado após `0.6s` de contato do Entry) para garantir o *trade kill*.
    3. *Counter-Strafe no Ápice do Movimento (`Velocity Zeroing`)*: Ao entrar em duelo de tiro com rifle/AWP em movimento (`>= 65 u/s`), injeta em `t=0ms` um pulso reverso de `80ms–120ms` exatamente oposto ao vetor velocidade atual seguido de `StandStill` em `+125ms` e `+250ms`, zerando a velocidade horizontal no disparo.
  - **Conector Pronto para Modelo Neural `.onnx` (`IMicroMovePredictor`)**: Monta a cada 62.5ms o tensor padronizado `[10, 18]` dos 10 jogadores (Posição normalizada, Velocidade, Direção de Visão, HP, Armor, Categoria da Arma, Role, Estado da C4 e Tempo) e monitora `H:\CS2_AI_Server\models\mlmove_<mapname>.onnx` com hot-swap automático via `FileSystemWatcher`.
  - **Integração com Telemetria Forense (`!debug`)**: Registra automaticamente eventos de `[MLMOVE - COUNTER-STRAFE]` e `[MLMOVE - TRADE SPACING]` nos logs de partida.
- **Camada 2 (Minerador e Extrator de Demos Reais a 16Hz — Concluído)**:
  - **Minerador Multi-Fonte (`tools/mlmove_pipeline/real_demo_miner.py`)**:
    * Controle de Estado Anti-Duplicação (`miner_state.json`) com hashing SHA256.
    * Validação Estrita de Header Source 2 (`PBDEMS2`), rejeitando demos antigas de CS:GO (`HL2DEMO`) e arquivos HTML de erro para proteger o parser.
    * Fonte 1: HuggingFace Datasets (`huggingface_hub`).
    * Fonte 2: Crawler HLTV / Faceit / URLs com `cloudscraper` (download streaming + barra `tqdm`).
    * Fonte 3: Ingestão de pasta local e gravações CSTV automáticas (`H:\CS2_AI_Server\game\csgo\csbot_*.dem`).
    * Descompactador seletivo: extrai apenas `*mirage*.dem` de pacotes `.zip`, `.rar`, `.7z`, `.zst` e apaga o arquivo bruto compactado imediatamente.
  - **Extrator `demoparser2` (`tools/mlmove_pipeline/extract_16hz_tensors.py`)**: Extrai a 16Hz tensores `X [N, 10, 18]` (com máscara Fog of War anti-wallhack) e rótulos `Y [N, 10, 3]` (`0..96`).
- **Camada 3 (Treinamento PyTorch -> Exportação `.onnx` — Concluído)**:
  - Treinador PyTorch (`tools/mlmove_pipeline/train_and_export_onnx.py`) com **Transformer Encoder Multi-Agente** (~5.47M parâmetros, ~21 MB) otimizado com `DirectMLAdamW` na GPU **AMD Radeon RX 6600M** e fallback para CPU multi-thread.
  - Exportação direta para `H:\CS2_AI_Server\models\mlmove_de_mirage.onnx` com validação de consistência via `onnx.checker` e benchmark de latência.
- **Orquestrador em Lotes Contínuo com Limpeza de Disco (`run_mining_and_training_loop.py` e `minerar_e_treinar.bat`)**:
  - Processamento em lotes configuráveis (`--batch-size 25`, `--epochs 15`).
  - Limpeza automática de disco: apaga o arquivo `.dem` de 200MB logo após extrair o `.npz` de ~4MB, economizando dezenas de gigabytes de armazenamento.
  - Fine-tuning incremental a partir do melhor checkpoint (`mlmove_de_mirage_best.pt`).
  - Relatório de precisão com cálculo de **Top-1 e Top-3 Accuracy** nos horizontes `0ms`, `+125ms` e `+250ms`.

---

## 8. Ambiente Local e Alocação de Hardware

- **GPU**: AMD Radeon RX 6600M (8 GB VRAM dedicado).
- **Memória RAM**: 32 GB de RAM física do sistema.
- **Cliente CS2 (Steam - Vanilla)**: Localizado em `H:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive` (100% original, sem mods, risco ZERO de VAC Ban).
- **Servidor Dedicado e IA (Instância Isolada)**: Localizado em `H:\CS2_AI_Server` (instância segregada, Metamod, CounterStrikeSharp, WeaponPaints, CsBotManager, Voice IGL, Arsenal Web UI e modelos neurais `H:\CS2_AI_Server\models\mlmove_de_mirage.onnx`).
- **Pipeline Pesado de Demos e Treinamento MLMove (NVMe 1 TB Isolado)**: Localizado em `D:\CS2_MLMove_Pipeline\` (`venv\`, `raw_demos\de_mirage\`, `extracted_tensors\de_mirage\`, `checkpoints\mlmove_de_mirage_best.pt` e atalho `treinar_lote_demos.bat`), mantendo o repositório Git (`tools/mlmove_pipeline/`) leve apenas com código-fonte (`contract_spec.py`, `demo_collector.py`, `extract_16hz_tensors.py`, `model_mlmove.py`, `generate_bootstrap_dataset.py`, `train_and_export_onnx.py` e `validate_e2e_onnx.py`).
