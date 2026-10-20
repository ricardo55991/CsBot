# 🎮 Manual do Jogador & Guia Completo de Comandos: CsBot AI

Bem-vindo ao **CsBot AI**, o ecossistema de inteligência artificial tática avançada para o Counter-Strike 2 (CS2), desenvolvido sobre a Source 2 com **CounterStrikeSharp** C# e integração com LLM local.

Neste sistema, os bots não seguem rotinas cegas ou scripts rígidos: eles possuem **senso de sobrevivência, leitura de economia real, coordenação motora via NavMesh, comunicação em tempo real via chat/rádio e obediência total às chamadas do jogador humano** (por chat de texto ou comandos de voz no microfone).

Este manual serve como o guia definitivo para jogadores que estão ingressando no servidor entenderem todas as mecânicas, comandos e comportamentos possíveis.

---

## 📋 Sumário
1. [Referência Rápida de Comandos de Chat de Texto](#1-referência-rápida-de-comandos-de-chat-de-texto)
2. [Guia de Comandos de Voz (Voice IGL & Microfone)](#2-guia-de-comandos-de-voz-voice-igl--microfone)
3. [Dinâmica de Equipe & Reivindicação de Posições (!pos)](#3-dinâmica-de-equipe--reivindicação-de-posições-pos)
4. [Economia, Drops Inteligentes & Setup Double AWP](#4-economia-drops-inteligentes--setup-double-awp)
5. [Como os Bots se Comunicam (Chat de Equipe & Rádio Nativo)](#5-como-os-bots-se-comunicam-chat-de-equipe--rádio-nativo)
6. [Inteligência de Combate & Mobilidade (Faca, Pistola e Cobertura)](#6-inteligência-de-combate--mobilidade-faca-pistola-e-cobertura)
7. [Protocolos de Bombsite: Plant Limpo, Retake, Fake e Prioridade de Kit](#7-protocolos-de-bombsite-plant-limpo-retake-fake-e-prioridade-de-kit)
8. [Adaptações Táticas de Mid-Round (Pivôs TR e Reações a Granadas)](#8-adaptações-táticas-de-mid-round-pivôs-tr-e-reações-a-granadas)
9. [Interface Visual (Chip HUD) & Painel Web de Skins (Arsenal Web UI)](#9-interface-visual-chip-hud--painel-web-de-skins-arsenal-web-ui)
10. [Ferramentas de Diagnóstico e Telemetria (!debug e !nota)](#10-ferramentas-de-diagnóstico-e-telemetria-debug-e-nota)

---

## 1. Referência Rápida de Comandos de Chat de Texto

Todos os comandos abaixo podem ser digitados diretamente no chat de texto do jogo (pressionando `Y` ou `U`) com prefixo `!` ou no console (`say !comando`).

| Comando | Parâmetros / Exemplos | Descrição e Efeito no Jogo |
| :--- | :--- | :--- |
| `!tatica` | `!tatica rush b`, `!tatica split a` | Força manualmente a equipe de bots a adotar uma tática específica para o round. |
| `!rejeitar` | *(sem argumentos)* | Rejeita a tática proposta pelo IGL no freeze time e solicita imediatamente uma estratégia alternativa à LLM local. |
| `!drop` | `!drop`, `!drop awp`, `!drop ak`, `!drop m4`, `!drop deagle` | Pede arma para o bot mais rico da equipe. O bot transfere a arma diretamente para o jogador preservando saldo seguro (mínimo $2000). |
| `!pos` | `!pos cabine`, `!pos caverna`, `!pos b`, `!pos meio`, `!pos janela` | Reivindica um setor do mapa. O bot que estava escalado para a posição cede o pixel e se reposiciona em uma área complementar. |
| `!executar` / `!go` | *(sem argumentos)* | Cancela a fase de espera (*Staging Area*) e comanda a invasão/execução imediata da equipe ao bombsite alvo. |
| `!flash` | *(sem argumentos)* | Solicita um pop-flash em dupla. O bot parceiro mais próximo lança uma flashbang por cima com arco calculado para você abrir o pixel cego. |
| `!miou` | *(sem argumentos)* | Dispara rotação silenciosa no Shift para o bomb alternativo (`ROTATE_SILENT`), abortando a entrada que sofreu contenção. |
| `!respawn` | *(sem argumentos)* | Ordena que os bots joguem pela proximidade dos seus spawns (cada um corre para o chokepoint mais perto do seu nascimento). |
| `!debug` | `!debug on`, `!debug off` | Liga ou desliga a telemetria forense da partida em tempo real, gerando relatórios Markdown estruturados no servidor. |
| `!nota` | `!nota Bot ficou preso na rampa` | Insere uma anotação do jogador no log forense com snapshot fotográfico instantâneo de posições, vidas e ordens. |
| `!wp` | *(sem argumentos)* | Abre o menu do WeaponPaints para escolher facas, luvas e skins salvas localmente. |

---

## 2. Guia de Comandos de Voz (Voice IGL & Microfone)

O servidor possui uma ponte de reconhecimento de voz ativa na porta `27080` conectada ao modelo Whisper local. Você pode falar naturalmente no seu microfone enquanto joga. A IA transcreve sua voz e dispara a ação física imediata nos bots.

### Principais Intenções e Sinônimos Reconhecidos:

#### ⚡ 1. Ataque e Entrada Imediata (Executar)
* **O que falar:** *"Executa"*, *"Entra"*, *"Bora entrar"*, *"Vai, vai, vai"*, *"Go go go"*, *"Rasga o bomb"*.
* **O que os bots fazem:** Cancelam qualquer tempo restante de contenção na Staging Area e disparam a invasão sincronizada com abertura de mira e utilitárias.

#### 🔄 2. Rotação Silenciosa e Abortar Entrada (Miou)
* **O que falar:** *"Miou"*, *"Miou a call"*, *"Recua todo mundo"*, *"Gira no shift"*, *"Rotaciona pro B"*, *"Vamos pro A"*.
* **O que os bots fazem:** Abaixam as armas de ataque, colocam no modo silencioso (`ROTATE_SILENT`) e contornam o mapa pelas costas para o bomb alternativo sem fazer barulho de passos.

#### 💥 3. Pop-Flash em Dupla
* **O que falar:** *"Banga pra mim"*, *"Faz uma flash"*, *"Banga a caverna"*, *"Flash no meio"*, *"Banga tapete"*, *"Flash palácio"*.
* **O que os bots fazem:** O bot mais próximo do setor citado saca uma flashbang, calcula o arco parabólico vertical sobre a parede e solta a granada perfeitamente no chokepoint para você repicar com vantagem.

#### 🛡️ 4. Preservação de Armas (Save)
* **O que falar:** *"Guarda arma"*, *"Salva as armas"*, *"Esconde"*, *"Não dá a cara"*, *"Fica safe"*.
* **O que os bots fazem:** Adotam postura defensiva imediata (`HIDE_COVER`), recuam para áreas profundas (Base CT, fundo de bomb) e congelam agachados para salvar os fuzis e kits.

#### 💰 5. Pedido de Drop Financeiro
* **O que falar:** *"Me dá um drop"*, *"Dropa uma arma"*, *"Me compra uma AK"*, *"Me dá uma AWP"*, *"Dropa M4"*.
* **O que os bots fazem:** O bot com maior saldo bancário deduz o dinheiro de sua conta e entrega o armamento nas suas mãos instantaneamente.

#### 🏃 6. Jogar pelo Respawn
* **O que falar:** *"Vamos jogar respawn"*, *"Joga pelo respawn"*, *"Cada um no spawn mais próximo"*.
* **O que os bots fazem:** Em vez de cruzarem o mapa, cada bot analisa sua distância para os 3 chokepoints principais (A, Meio, B) e assume o pixel mais próximo da sua saída de base com postura consciente (AWP cravando longo alcance, rifles cobrindo com jiggle).

#### 📍 7. Reivindicação de Posições por Voz
* **O que falar para posição temporária (1 round):** *"Tô na cabine"*, *"Vou meio"*, *"Vou caverna"*, *"Meu tapete"*, *"Vou janela"*, *"Seguro mercado"*.
* **O que falar para posição FIXA (travada para todo o jogo):** *"Estou fixo na cabine"*, *"Meu pixel fixo é caverna"*, *"Fico fixo na janela"*, *"A partir de agora eu jogo no meio"*.
* **O que os bots fazem:** O bot que iria para aquele pixel cede o lugar com aviso no chat e vai cobrir uma rota de apoio. Se você travou como fixa, mesmo após morrer ou trocar de round, o sistema lembrará da sua escolha.

#### 📝 8. Registro de Anotação Forense por Voz
* **O que falar:** *"Nota de debug: o bot travou na caixa"*, *"Anota aí: o retake no B demorou pra entrar"*.
* **O que os bots fazem:** Grava sua frase diretamente no arquivo de telemetria Markdown do round.

---

## 3. Dinâmica de Equipe & Reivindicação de Posições (!pos)

No CS tradicional, bots costumam se amontoar nos mesmos pixels ou atrapalhar a mira do jogador. No **CsBot AI**, o sistema de **Resolução de Conflitos de Posição** (`RoleManager.cs`) garante harmonia total:

1. **Troca Dinâmica de Setor:**
   - Ao digitar `!pos <setor>` (ex: `!pos caverna`), o bot designado para aquele chokepoint reconhece sua autoridade.
   - O bot cede a coordenada física e altera sua ordem na engine para reforçar um setor vizinho desprotegido (ex: cede Janela do Meio e assume Ligação/Conector).
2. **Memória de Posição Travada:**
   - Se você declarar uma posição fixa por voz (*"Meu pixel fixo é cabine"*), o `RoleManager` grava a trava. No início de cada novo round, durante o cálculo das rotas, o sistema reserva automaticamente o seu lugar e distribui os bots ao redor de você.
3. **Deslocamento Físico Real:**
   - O bot não some nem se teleporta: ele gira a mira e caminha via NavMesh para a nova coordenada de forma 100% natural.

---

## 4. Economia, Drops Inteligentes & Setup Double AWP

O gerenciamento econômico (`EconomyManager.cs`) opera sob as regras oficiais do CS competitivo, analisando o saldo bancário da equipe e o **Loss Bonus Real** (de $1400 a $3400):

* **Estados Econômicos:**
  * **FULL_BUY (Compra Total):** Fuzis Tier-1 (AK-47 / M4A1-S / AWP), colete com capacete, kit de defuse para CTs e kit completo de utilitárias (Smokes, Flashes, Molotovs).
  * **FORCE_BUY (Compra Forçada):** Famas / Galil / MP9 / Mac-10 com colete para disputar rounds críticos ou pós-pistol.
  * **HALF_BUY (Compra Parcial):** Preserva saldo mínimo de $2000 por jogador para garantir Full Buy no round seguinte, comprando pistolas fortes (Deagle, Five-Seven, Tec-9) e colete leve.
  * **FULL_ECO (Eco Total):** Bloqueio determinístico de compras via `SetBuySkip` na engine da Valve para garantir fuzis completos na sequência.
* **Auto-Drop de Sniper:** Se o sniper designado (`AWPer`) não possui $4750 mas a equipe tem saldo sobrando, o bot mais rico compra e entrega a AWP para o sniper automaticamente no freeze time.
* **Setup de Double AWP no CT Rico:**
  - Quando a equipe CT atinge saldo médio `>= $7500` em um `FULL_BUY`, o sistema ativa **35% de chance de Double AWP**.
  - O bot `Anchor` (âncora) compra a 2ª sniper da equipe, posiciona-se em ângulos longos (Van do B ou Ticket da A) e o IGL avisa no chat: `"(Contraterrorista) IGL: Economia alta! Vamos de DOUBLE AWP, domina as pontas!"`.
* **Disciplina da C4 no Freeze Time:**
  - Se a engine da Valve sortear a C4 para o `Entry Fragger` ou para o `Anchor`, o sistema intercepta aos 11.5s do freeze time e transfere a bomba para o bot `Rotator` (Suporte), garantindo que os abridores de mira entrem leves no combate.
* **Looting Inteligente Pós-Round:**
  - Ao término do round, bots sobreviventes que estejam com armas inferiores (pistolas ou submetralhadoras) escaneiam o chão num raio de até 600 unidades. Se encontrarem AK-47, M4A1-S ou AWP caídas de inimigos mortos, caminham até a arma, dropam a sua e pegam o rifle superior para o round seguinte.

---

## 5. Como os Bots se Comunicam (Chat de Equipe & Rádio Nativo)

Os bots utilizam o chat de equipe formatado e comandos de rádio autênticos do CS2 (`takingfire`, `needbackup`, `affirmative`, `coverme`, `cheer`, `holdpos`):

### 👁️ 1. Contato Visual e Recuo (Spot & Fallback)
Quando um bot avança para coletar informação ou sofre pressão e precisa recuar (`FALLBACK_ALIVE`), ele emite a callout precisa com a contagem de oponentes:
* `"(Contraterrorista) Bot_A: Vi 2 na Caverna! Dei uns tiros e recuei pro Bomb."`
* Se avistar um sniper: `"(Contraterrorista) Bot_A: Cuidado, AWP cravado no Topo do Meio!"`
* Se avistar o portador da C4: `"(Contraterrorista) Bot_A: C4 VISTA na Rampa A!"`

### 🚨 2. Alerta Instantâneo de Rush (Rush Alert)
Se 3 ou mais adversários rasgarem o mesmo chokepoint em um intervalo de até `3.5 segundos` (detectado por visão direta ou combinação de passos + granadas), o bot detecta o rush agressivo e dispara o alerta antes mesmo de morrer:
* `"(Contraterrorista) Bot_B: RUSH B! RUSH B! Tão rasgando o Tapete com granadas! Gira todo mundo agora!"`
* Acompanhado do comando de rádio nativo `needbackup`.

### 💀 3. Callout Pós-Morte & Dano Causado (Death & Damage)
Com um delay humano natural de `1.0 segundo` após ser abatido, o bot informa onde morreu, se deixou o inimigo miado e quantos estavam juntos:
* `"(Morto) Bot_C: Caí na Ligação! O cara tá MUITO MIADO (-82 HP)! Tinha mais 1 com ele!"`
* Se morreu para AWP: `"(Morto) Bot_C: AWP cravada na Janela do Meio, não dá a cara aberto!"`

### 👂 4. Audição de Passos e Som Ambiente (Audio Cue)
Os bots possuem ouvidos virtuais a 64Hz (`EventPlayerFootstep`). Se ouvirem adversários correndo em um raio de até `750 unidades` através de paredes (ex: barulho no Rato/Underpass ou no Tapete):
* `"(Contraterrorista) Bot_D: Ouvi passos correndo perto do Rato/Underpass! Fica esperto no Meio!"`
* Possui cooldown inteligente anti-spam de 15 segundos por setor para não poluir a tela.

### 💨 5. Reação Contextual a Smokes na Cara
Quando uma smoke estoura exatamente na posição em que o bot está marcando, ele não fica travado cego:
* **Com barulho por perto e aliados no bomb:** Vira a mira na ameaça sonora ou pede pop-flash para abrir na fumaça.
* **Com AWP equipada:** Recua para um ângulo longo limpo onde a smoke não bloqueie a mira.
* **Em silêncio total:** Crava a borda da fumaça em postura passiva ou varre o centro com disparos controlados (se estiver com rifle silenciado M4A1-S).
* **Sozinho no bomb:** Recua para o fundo do bomb chamando rotação, ou se esconde de "rato" (Ninja/Banco) para pegar o adversário pelas costas durante o plant.

---

## 6. Inteligência de Combate & Mobilidade (Faca, Pistola e Cobertura)

### 🏃 Mobilidade Inteligente com Faca (250 u/s) & Freio Tático
* **Corrida Rápida:** No deslocamento inicial da base para a Staging Area, em rotações silenciosas (`ROTATE_SILENT`) ou em ritmos acelerados (`FAST_CONTACT`), se a distância até o alvo for superior a `600 unidades` e nenhum perigo foi avistado nos últimos 6 segundos, o bot saca a faca (`slot3`) para correr na velocidade máxima do jogo (250 u/s).
* **Freio Tático:** Ao se aproximar a `<= 600 unidades` do chokepoint ou ao detectar passos de inimigos, sofrer dano ou obter linha de visão, o bot puxa imediatamente o rifle primário (`slot1`) frações de segundo antes de abrir o ângulo, evitando ser pego desprevenido de faca na mão.

### 🔫 Swap para Pistola vs. Recarga Segura
Bots novatos costumam tentar recarregar no meio de tiroteios abertos. O módulo `CombatAdapter.cs` corrige isso:
* **Curta Distância (`< 500u`):** Se a arma primária zerar a munição no pente (`clip1 == 0`) durante a trocação a queima-roupa, o bot cancela o reload, puxa a pistola na hora (`slot2`) e continua atirando (*"switching to your pistol is always faster than reloading"*).
* **Média / Longa Distância (`>= 500u`):** Se o pente zerar com o inimigo à distância, o bot não fica parado no aberto: ele recua para trás da parede mais próxima (`MidRoundAction.HIDE_COVER`), recarrega o rifle em segurança e só repica no ângulo com `Jiggle Peek` após a arma estar pronta.

---

## 7. Protocolos de Bombsite: Plant Limpo, Retake, Fake e Prioridade de Kit

### 💣 Entrada Limpa e Plant Inteligente (Terroristas)
* **Varredura Prévia (Site Clearing):** Ao invadirem o bombsite na fase de execução, o portador da C4 **NÃO puxa a bomba imediatamente**. Ele mantém o rifle em mãos e dá cobertura enquanto o Entry Fragger limpa os cantos críticos (Ninja, Firebox, Ticket na A; Van, Banco, Mercado na B).
* **Validação de Segurança:** O plant só se inicia quando nenhum adversário estiver visível no bomb e nenhum aliado tiver sofrido dano nos últimos 2.0 segundos (ou se o relógio estiver em desespero crítico, abaixo de 12s).
* **Plant Aberto vs. Fechado:** Se o time dominar o bomb completamente, o bot planta aberto para as posições dos aliados (ex: aberto para Caverna/Palácio na A). Se houver risco, planta protegido na caixa central (Default/Safe).

### 🛠️ Retake CT, Smoke Defuse e Prioridade de Kit
* **Smoke na C4 (Smoke Defuse):** Se o tempo restante da bomba permitir (> 8s com kit ou > 13s sem kit), o bot CT lança uma smoke na C4 antes de iniciar o desarme para bloquear a visão dos TRs.
* **Prioridade Inteligente de Defuse:**
  - Se um CT sem kit começar a desarmar (desarme de 10 segundos) e um aliado com kit estiver por perto (`<= 400u`), o sistema cancela o desarme do bot sem kit.
  - O bot sem kit se afasta e fica agachado de mira cravada dando cobertura.
  - O bot com Kit assume a bomba para o desarme rápido de 5 segundos, avisando no rádio: `"(Contraterrorista) Nome: Deixa pra mim que eu tenho Kit! Cobre a defuse!"`.
* **Roleta de Fake Defuse vs. Stick Defuse:**
  - **Sob Smoke:** 55% de chance de segurar até o fim (*"Pros Don't Fake"*) e 45% de chance de tocar por 0.5s e dar passo lateral de rifle em punho para pegar quem atirar na fumaça.
  - **No Aberto:** 60% de Fake Defuse clássico (toca 0.5s e crava o chokepoint por 2.5s), 25% de Half-Defuse Bait (segura até a metade e solta) e 15% de Cold Stick.

---

## 8. Adaptações Táticas de Mid-Round (Pivôs TR e Reações a Granadas)

No CS moderno, planos iniciais raramente sobrevivem ao primeiro contato. O módulo `TrMacroPivotController.cs` monitora o mid-round e executa 3 macro-adaptações inteligentes:

1. **Reação ao "Paredão de Utilitárias" (Brick Wall Pivot):**
   - Se o chokepoint de entrada sofrer bloqueio massivo de utilitárias CT (Molotov + Smoke) ou o Entry Fragger for eliminado sem troca de abates nos primeiros 2s da invasão:
     - **60% `HOLD_AND_RE_EXECUTE`:** O time congela na Staging Area, protege costas em postura passiva por ~16s e aguarda as granadas abrirem para repicar juntas.
     - **34% `RESET_TO_DEFAULT`:** Aborta o avanço, cancela a execução e espalha os jogadores no mapa para buscar trocas isoladas.
     - **6% `HARD_PIVOT_SILENT`:** Abandona o bomb atual e realiza uma rotação total e silenciosa no Shift para o bomb oposto.
2. **Oportunismo do Lurker (Site Clearance Call):**
   - Quando o Lurker abate o defensor solitário do bomb oposto e valida que a área está limpa por 2.5s, ele emite o comando de rádio `sectorclear`. A equipe inteira converge imediatamente com a C4 para o bomb livre.
3. **Conversão de First-Kill em Split:**
   - Em rounds cadenciados (`SLOW_DEFAULT`), se um terrorista obtiver o first-kill em uma posição central (ex: Janela ou Conector), a equipe converte automaticamente a tática para um Split rápido aproveitando a brecha criada.

---

## 9. Interface Visual (Chip HUD) & Painel Web de Skins (Arsenal Web UI)

### 🖥️ Chip HUD no Topo da Tela
Durante toda a partida, uma barra visual leve é renderizada no topo central da tela via HTML (`PrintToCenterHtml`):
* **Fase do Round:** `FREEZE TIME`, `STAGING (Aguardando timing)`, `EXECUTING (Invasão ativa)` ou `PÓS-PLANT / RETAKE`.
* **Tática & Ritmo:** Nome da jogada ativa (ex: *Split A*, *Rush B*, *Cheese Caverna*) e ritmo (`SLOW_DEFAULT`, `FAST_CONTACT`, etc.).
* **Papéis Individuais:** Exibe qual bot é o `AWPer`, `Entry`, `Rotator` e `Anchor`.
* **Economia:** Status econômico do round (`FULL_BUY`, `FORCE`, `ECO`).

### 🎨 Arsenal Web UI (Painel de Skins & Facas na Porta 8080)
Conectado ao banco MariaDB portátil local (`weaponpaints`), o servidor disponibiliza uma interface web no navegador (`http://localhost:8080`):
* **Facas e Luvas:** Escolha entre Karambit, Butterfly, M9 Bayonet, Skeleton, Talon e luvas Specialist, Sport, Moto, etc.
* **Gemas Doppler Raras (1 Clique):** Presets automáticos para **Ruby (415)**, **Sapphire (416)**, **Black Pearl (417)**, **Emerald (568)**, **Fade 100% (38)** e **Blue Gem (44 / Seed 661)**.
* **Float Wear:** Slider de desgaste de 0.0001 (Factory New) a 0.9999 (Battle-Scarred).
* **StatTrak & NameTag:** Contador de abates e personalização de nomes.
* **Sincronização no Jogo:** As escolhas feitas na Web UI refletem imediatamente no jogo através do comando `!wp`.

---

## 10. Ferramentas de Diagnóstico e Telemetria (!debug e !nota)

Para desenvolvedores, analistas de partidas ou jogadores curiosos que desejam auditar as decisões dos bots:

* **Ativar/Desativar Telemetria:**
  - Digite `!debug on` para começar a gravar.
  - Digite `!debug off` para desligar (zero consumo de CPU e disco quando desligado).
* **Inserir Notas com Snapshot:**
  - Digite `!nota <texto>` no chat ou fale no microfone *"Anota aí: ..."*.
  - O sistema captura instantaneamente a posição `(X, Y, Z)`, ângulo de mira, vida, arma ativa, postura e anomalias de todos os jogadores naquele exato milissegundo.
* **Onde os Relatórios Ficam Salvos:**
  - Os logs são gerados em formato Markdown em: `H:\CS2_AI_Server\debug_logs\match_telemetry_AAAAMMDD_HHMMSS.md`.
  - Contém linha do tempo `[MM:SS]`, inventário e saldo de ambos os times, rastreamento de utilitárias arremessadas (origem, ângulo e destino), matriz de dano e abates, e o detector automático de anomalias (`[⚠️ AUTO-ANOMALY]`).

---

Divirta-se jogando no servidor! Se tiver dúvidas durante a partida, lembre-se: basta dar a ordem por chat ou falar no microfone que sua equipe responderá na hora. 🎯🔥
