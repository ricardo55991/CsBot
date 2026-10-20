# Checklist Unificado de Testes em Jogo (Fases 2, 3 e 4)

Este roteiro unificado foi elaborado para validar todas as mecânicas das **Fases 2, 3 e 4** do **CsBot** em uma única sessão dentro do Counter-Strike 2.

---

## 1. Passo a Passo para Iniciar o Ambiente

1. **Verificar se o Ollama está rodando na GPU:**
   - Abra um terminal e verifique:
     ```powershell
     Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
     ```
   - O modelo `qwen2.5:3b` está carregado com `keep_alive: -1` na VRAM da GPU AMD RX 6600M.

2. **Iniciar o Servidor Dedicado e o Voice Client:**
   - Execute o script:
     ```text
     H:\CS2_AI_Server\start_cs2_ai_server.bat
     ```
     *(ou `iniciar_servidor.bat`)*
   - Esse script iniciará automaticamente:
     - O banco de dados MariaDB portátil (porta 3306).
     - A janela do **Voice IGL Client** (`[CsBot Voice IGL - Segure 'V' para falar]`).
     - O servidor dedicado do CS2 na porta `27016` com Metamod, CounterStrikeSharp e `CsBotManager`.

3. **Conectar pelo Cliente CS2 (Steam Vanilla):**
   - Abra o CS2 pela sua biblioteca da Steam normalmente.
   - Abra o console (`'` ou `~`) e digite:
     ```text
     connect 127.0.0.1:27016
     ```

---

## 2. Validação da Fase 2: Economia, Arquétipos & Chip HUD

| Teste | Ação no Jogo | Resultado Esperado | Status |
| :--- | :--- | :--- | :---: |
| **2.1 Chip HUD** | Olhe o topo/centro da tela no *Freeze Time*. | Exibe `[FULL BUY] [LENTO DEFAULT] [CONGELAMENTO] ⚡ Tática` com cores distintas. | [ ] |
| **2.2 Economia Determinística** | Jogue o Round 1 (pistol) e Round 2. | Bots compram armadura/pistola no pistol e forçam ou guardam conforme a média do time (sem compra aleatória do `BotBuy`). | [ ] |
| **2.3 Pedido de Drop** | No *Freeze Time*, digite no chat: `!drop ak` ou `!drop awp`. | O bot mais rico do time compra a arma e dropa nos seus pés com aviso no chat. | [ ] |
| **2.4 Call Tática Manual** | Digite no chat: `!tatica split meio e b`. | O Ollama processa a ordem em <1.5s e reorganiza as ordens de todos os bots. | [ ] |
| **2.5 Rejeição de Tática** | Digite no chat: `!rejeitar`. | O IGL descarta a call atual e propõe uma abordagem alternativa imediatamente. | [ ] |
| **2.6 Troca Manual de Posição** | Digite no chat: `!pos janela` ou `!pos b`. | O bot designado para a posição cede o setor para você e vai cobrir outra área. | [ ] |

---

## 3. Validação da Fase 3: Cadência, Staging & Sobrevivência

| Teste | Ação no Jogo | Resultado Esperado | Status |
| :--- | :--- | :--- | :---: |
| **3.1 Staging Hold** | Início de round armado como Terrorista. | Os bots **não rusham** de forma suicida. Eles aguardam em suas posições de Staging (Tapete, Caverna, Top Mid) com contagem regressiva no HUD. | [ ] |
| **3.2 Comando `!executar` / `!go`** | Durante a contagem de Staging, digite `!executar` ou `!go`. | A espera é cancelada na hora, o HUD muda para `[EXECUTE ATIVO]` e os bots invadem o bomb sincronizados. | [ ] |
| **3.3 Matriz de 35 Micro-Pixels** | Observe as posições dos CTs ao longo de 4 rounds. | Os bots variam entre Ticket mira fechada, Firebox off-angle, Degraus crossfire, Janela AWP, Degrau do Conector e Van/Banco B. | [ ] |
| **3.4 Recuo por Vida Crítica** | Dispare contra um bot até ele ficar com HP < 55. | O bot abandona a trocação, aciona `FALLBACK_ALIVE` e recua para cobertura segura com aviso no chat. | [ ] |
| **3.5 Mecânica `ONE_AND_DONE`** | Observe o bot em posições off-angle (Firebox, Rato, Canto do L). | O bot atira no primeiro contato e imediatamente bate em retirada com vida para o refúgio seguro. | [ ] |
| **3.6 Regra Anti-Rush** | Jogue um round em ritmo `FAST_CONTACT`. | No round seguinte, o IGL proíbe rush consecutivo e obriga `SLOW_DEFAULT` ou `TIMED_EXECUTE`. | [ ] |

---

## 4. Validação da Fase 4: Defesa Anti-Fake, Micro-Actions & Voz

### 4.1 Módulo 1: Domínio CT em Dupla & Rotação Cautelosa Anti-Fake
- **Teste do Alerta Nível 1 (Trava do Âncora B):**
  - Quando os TRs fizerem barulho ou jogarem granadas no Bomb A sem a C4 ser vista:
    - O `Rotator` (Ligação/Meio) apoia o Bomb A.
    - O `Anchor` do Bomb B permanece **100% TRAVADO no Bomb B** (`HoldSiteLocked`) para evitar ser ludibriado por fakes.
  - Se houver barulho em ambos os bombs nos últimos 5 segundos, o chat emite:
    `[CT Defesa] Pressão simultânea em A e B! ANTI-FAKE ATIVADO: Ninguém abandona seu setor!`
- **Teste do Alerta Nível 2 (C4 Confirmada):**
  - No instante em que a C4 for avistada no radar ou plantada (`EventBombPlanted`), o sistema destrava todos os bots para **Retake Coordenado**.
- **Teste de Domínio em Dupla (`CT_DUO_PLAY`):**
  - Em ~25% dos rounds armados de CT, observe a mensagem `[CT Duo Play] Jogada ensaiada ativada!`. O `Bot_Support` joga a pop-flash e o `Bot_Entry` avança agressivo em `ONE_AND_DONE`, recuando após o espaço ser garantido.
- **Teste de Pop-Flash em Dupla com o Humano:**
  - No chat, digite: `!flash caverna` (ou `!flash meio`, `!flash tapete`).
  - O bot CT mais próximo lança a pop-flash e avisa no centro da tela:
    `⚡ FLASH LANÇADA! ABRA O PIXEL AGORA! ⚡`

### 4.2 Módulo 2: Fake Real de TR (Divisão por C4) & Micro-Ações
- **Teste do `SPLIT_FAKE` de TR:**
  - Em rounds sorteados com Fake:
    - O **Grupo Barulho** (2 bots sem a C4) avança para a Caverna/Palácio do Bomb A, arremessa granadas, dispara rajadas e depois recua vivo.
    - O **Grupo Silencioso** (portador da C4 + escolta) caminha no Shift pelo Tapete B e invade o Bomb B 4 segundos após as bombas caírem no A!
- **Teste de Micro-Ações Reativas:**
  - Digite no chat `!miou` ou observe a morte do Entry em uma passagem fumegada:
    - O time cancela a entrada e aciona `ROTATE_SILENT` andando no Shift para o outro bomb.
  - Ao plantar a C4, 1 bot assume imediatamente `WATCH_FLANK` mirando 180° para proteger as costas.

### 4.3 Módulo 3: `Dynamic Swap` 100% Automático por Movimento
- **Teste Sem Digitar Nada:**
  - Logo após o congelamento abrir (nos primeiros 6 segundos):
    - Corra diretamente em direção à **Janela do Meio** ou suba para a **Varanda / Catwalk** ou entre no **Bomb B**.
    - Ao se aproximar do setor, o sistema detecta seu vetor de movimento e avisa no chat e no HUD:
      `🔄 [Swap Automático] Movimento detectado! Você assumiu VARANDA. Bots reorganizados!`
    - O bot que iria para aquela posição cede o setor para você autonomamente.

### 4.4 Módulo 4: Pipeline de Voz Local Push-to-Talk (`faster-whisper`)
- **Como Usar o Microfone:**
  - Com o jogo aberto, **segure a tecla `V`** (tecla Push-to-Talk padrão).
  - Fale uma ordem tática clara em português e solte a tecla `V`.
- **Exemplos de Ordens para Falar e Testar:**
  1. *"Vou jogar meio de AWP"* $\rightarrow$ O sistema detecta a intenção e executa o swap da Janela para você.
  2. *"Me dropa uma AK"* (ou *"dropa arma"*) $\rightarrow$ O bot mais rico dropa a arma solicitada.
  3. *"Miou o A, recua no shift pro B"* $\rightarrow$ Aciona `ROTATE_SILENT` com todos os bots caminhando no shift para o Bomb B.
  4. *"Executa agora, entra A!"* $\rightarrow$ Cancela o staging e dispara o avanço imediato.
  5. *"Me banga caverna"* $\rightarrow$ O bot companheiro prepara a pop-flash no setor.
  6. *"Esconde todo mundo, guarda a arma"* $\rightarrow$ Bots agacham e assumem postura `HIDE_COVER` furtiva.
- **Feedback em Tempo Real:**
  - A frase transcrita aparece no topo do Chip HUD: `🎙️ "Sua frase aqui"` e é anunciada no chat da equipe.

---

## 5. Critérios para Aprovação Geral
- [x] Compilação do `CsBotManager` sem erros (`0 avisos`, `0 erros`).
- [x] Binários atualizados em `H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\`.
- [x] Voice Bridge HTTP ativo em `http://127.0.0.1:27080/voice/`.
- [x] `faster-whisper` funcionando com vocabulário CS2.
- [x] Scripts de inicialização (`start_cs2_ai_server.bat` e `iniciar_servidor.bat`) integrados.
