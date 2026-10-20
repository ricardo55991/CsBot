# Checklist de Testes e Validação - Fase 2 (Maestro Tático, Economia, Arquétipos & Chip HUD)

Este documento estabelece todos os critérios práticos para homologar a **Fase 2 (CsBotManager + Qwen 2.5 3B na GPU)** no servidor dedicado local de CS2 (`H:\CS2_AI_Server`).

---

## 1. Verificações Prévias de Inicialização

- [ ] **Executar o Batch**: Dê um duplo-clique em `start_cs2_ai_server.bat` (em `H:\CS2_AI_Server` ou na raiz do projeto).
- [ ] **Prompt do CMD Limpo e Automatizado**:
  - `[+] Metamod verificado com sucesso no gameinfo.gi.`
  - `[+] MariaDB ja esta em execucao na porta 3306.`
  - `[+] Ollama iniciado na porta 11434.`
  - `[+] Qwen 2.5 3B aquecido e mantido na VRAM (keep_alive: -1).`
- [ ] **Console do CS2 Dedicado**:
  - Exibe o carregamento de todos os plugins: `BotController`, `BotHider`, `BotVision`, `CounterStrikeSharp`.
  - Exibe `Finished loading plugin CsBotManager` e `Finished loading plugin WeaponPaints`.
  - Servidor entra em modo 5v5 com 10 bots (`Server tick rate: 64.0`).

---

## 2. Conexão e Validação do Chip HUD no Freeze Time

- [ ] **Entrar no Servidor**: No seu CS2 oficial da Steam, abra o console (`'`) e digite `connect 127.0.0.1:27016`.
- [ ] **Exibição do Chip HUD (Centro Superior da Tela)**:
  - Durante os 15 segundos de Freeze Time de cada round, verifique se aparece o Chip de Tática formatado:
    * **Badge Econômico**: `[FULL BUY]` (Verde Neon), `[FORCE BUY]` (Laranja), `[HALF BUY]` (Dourado) ou `[FULL ECO]` (Vermelho).
    * **Nome da Tática**: `⚡ Nome da Tática Gerada pela IA` (em Ciano brilhante).
    * **Resumo da Tática**: Objetivo tático em texto branco.
    * **Distribuição dos 4 Bots**: `AWP`, `Entry`, `Rotator` e `Anchor` com seus respectivos setores designados (ex: Janela, Palácio, Conector, Bomb B).
    * **Dica de Comandos**: `[!tatica <call> | !rejeitar | !drop | !pos <setor>]`.

---

## 3. Comandos Interativos do Capitão Humano

Durante o Freeze Time (entre os segundos `1.5s` e `10.5s`), abra o chat do jogo (`Y`) e teste os seguintes comandos:

### A. Comando `!tatica <sua call>`
- [ ] Digite no chat:
  ```text
  !tatica rush b rápido pelo tapete com smokes van
  ```
- [ ] **Resultado Esperado**:
  - O chat avisa: `[CsBot IGL] Processando call com IA: "rush b rápido pelo tapete com smokes van"...`
  - Em menos de 1 segundo, o Qwen 2.5 3B recalcula os objetivos dos 4 bots.
  - O **Chip HUD** atualiza instantaneamente no topo da tela refletindo a nova tática ordenada por você!

### B. Comando `!rejeitar`
- [ ] Digite no chat:
  ```text
  !rejeitar
  ```
- [ ] **Resultado Esperado**:
  - O IGL avisa no chat que a tática foi rejeitada.
  - A IA gera uma nova estratégia alternativa para aquele mesmo estado econômico e o HUD atualiza.

### C. Comando `!drop` (Pedido Inteligente de Armas)
- [ ] Quando um round estiver em `FULL BUY`, digite no chat:
  ```text
  !drop ak
  ```
  *(Ou `!drop m4`, `!drop awp`, `!drop`)*
- [ ] **Resultado Esperado**:
  - O bot aliado com maior saldo financeiro compra a arma solicitada e a dropa diretamente para você durante o Freeze Time!
  - O chat exibe a confirmação: `[CsBot Economy] <NomeDoBot> comprou e dropou AK47 para você!`.

### D. Comando `!pos <setor>` (Dynamic Swap)
- [ ] No lado CT, digite no chat:
  ```text
  !pos janela
  ```
  *(Ou `!pos b`, `!pos conector`, `!pos a`)*
- [ ] **Resultado Esperado**:
  - O bot que estava designado para a Janela cede a posição para você e assume automaticamente a cobertura de outro setor desfalcado (ex: Conector ou Bomb A).
  - O chat exibe: `[CsBot Dynamic Swap] Posição JANELA assumida por você. Os bots reorganizaram a defesa!`.

---

## 4. Bate do Martelo e Execução Determinística (Segundo 11.0s)

- [ ] **Aos 11 segundos do Freeze Time**:
  - O chat anuncia: `[CsBot IGL] Tática confirmada: <NomeDaTatica>!`.
  - Os bots executam suas compras calculadas (colete/capacete, rifles/SMGs adequados e utilitárias de acordo com a função).
  - Nenhuma compra aleatória ou duplicada ocorre (o `BotBuy` padrão foi substituído pelo nosso `EconomyManager`).
- [ ] **Ao Final do Freeze Time (Segundo 15.0s)**:
  - Os bots saem em direção aos setores definidos no plano tático.
  - O Chip HUD permanece visível por mais 6 segundos do round ativo e depois desaparece suavemente para liberar a visão de combate.

---

## 5. Critérios de Rejeição (O que NÃO pode acontecer)
- [ ] O servidor não pode travar ou cair ao consultar a IA no Freeze Time (chamada 100% assíncrona).
- [ ] Bots não podem ficar parados na base sem avançar (pathfinding ativo).
- [ ] Bots não podem gastar dinheiro em Eco rounds (o `EconomyManager` trava o saldo em no mínimo $2000 no Half Buy e zero no Full Eco).
