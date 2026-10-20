# Checklist de Testes e Validação - Fase 3: Dinâmica Tática, Matriz de Variações & Sobrevivência

Este documento contém o roteiro prático e detalhado para testar e aprovar a **Fase 3** do projeto **CsBot** no servidor dedicado isolado (`H:\CS2_AI_Server`).

---

## 1. Pré-Requisitos de Inicialização

1. **Ollama ativo com o modelo na GPU:**
   - O Ollama deve estar rodando na porta `11434` com o modelo `qwen2.5:3b` alocado na VRAM da GPU AMD RX 6600M.
2. **Banco MariaDB ativo:**
   - MariaDB rodando na porta `3306` (para `weaponpaints`).
3. **Inicialização do Servidor Dedicado:**
   - Execute o script `H:\CS2_AI_Server\iniciar_servidor.bat` (ou PowerShell).
   - Verifique no console se `CsBotManager` e `WeaponPaints` foram carregados sem erros.
4. **Conexão do Cliente CS2:**
   - Abra o CS2 da Steam normalmente e no console digite:
     ```text
     connect 127.0.0.1:27016
     ```

---

## 2. Testes de Cadência e Ritmo de Round (`RoundTempo`)

### Teste 2.1: Visualização do Chip HUD Atualizado
- **O que observar:** Durante o *Freeze Time* (congelamento inicial), observe o centro da tela:
  - Badge de economia: `[FULL BUY]`, `[FORCE BUY]`, etc.
  - Badge de ritmo: `[LENTO DEFAULT]`, `[TESTE & ROTAÇÃO]`, `[EXEC SINCRONIZADA]` ou `[CONTATO RÁPIDO]`.
  - Badge de fase: `[CONGELAMENTO]` passando para `[STAGING: XXs]` ao liberar o round.
  - Micro-posições e posturas dos bots: ex: `AWP: Janela Fundo (Passivo) | Entry: Palácio (Poke)`.
- **Critério de Aprovação:** O HUD exibe cores distintas, o ritmo do round e a contagem regressiva em segundos do Staging.

### Teste 2.2: Staging Hold (Eliminação do Rush Suicida)
- **O que observar:** Ao abrir a porteira do round:
  - Em rounds com ritmo `SLOW_DEFAULT` ou `TIMED_EXECUTE`, os bots **NÃO** correm desenfreados para morrer nos primeiros 5 segundos.
  - Eles se posicionam em suas áreas de *Staging* (ex: caixas top mid, fundo tapete B, caverna A) e mantêm postura de checagem/jiggle.
- **Critério de Aprovação:** Bots aguardam a preparação das utilitárias e o esgotamento do relógio de staging antes da invasão final.

---

## 3. Teste de Intervenção do Jogador Humano: `!executar` / `!go`

- **Como testar:**
  1. Durante a fase de *Staging* (enquanto os bots estão aguardando), abra o chat e digite:
     ```text
     !executar
     ```
     *(ou utilize o alias `!go`)*.
  2. Verifique o aviso no chat:
     `[CsBot Maestro] ⚡ EXECUTE DISPARADO! (Ordem do Capitão Humano) Avanço total para os bombsites!`
  3. Observe que o relógio de Staging no HUD é imediatamente encerrado para `[EXECUTE ATIVO]` e os bots avançam para os pontos de `tr_exec_*` ou contestação do bomb.
- **Critério de Aprovação:** O jogador tem poder total como IGL para acelerar o round no momento exato em que desejar.

---

## 4. Teste da Matriz de 20+ Variações Orgânicas dos Adversários

- **O que observar ao longo de 4 a 6 rounds:**
  - No time adversário (ex: CTs defendendo Mirage):
    - Em um round: um bot marca de *Ticket* e outro de *Degraus A*.
    - No round seguinte: um bot joga no off-angle do *Firebox (One&Done)* ou *Debaixo do Palácio*, enquanto outro joga de *Caixa Tripla*.
    - No meio: variações entre *Janela Baixa*, *Janela Fundo AWP*, *Degrau do Conector* e *Saída do Rato*.
    - No Bomb B: variações entre *Van (Jiggle)*, *Banco Fundo*, *Caixa Plant* e *Canto do L (Short)*.
- **Critério de Aprovação:** O time adversário não mantém posições idênticas e robóticas todos os rounds, criando surpresas táticas reais a cada partida.

---

## 5. Teste de Sobrevivência e Recuo Tático (`FALLBACK_ALIVE` & `ONE_AND_DONE`)

### Teste 5.1: Recuo por Dano Crítico (HP < 55)
- **Como testar:**
  - Acompanhe um bot em trocação ou dispute contra um bot inimigo.
  - Quando a vida do bot cai para menos de 55 HP, o bot prioriza a própria sobrevivência em vez de ficar parado trocando até a morte.
  - O sistema emite no chat:
    `[CsBot Sobrevivência] <BotName> tomou dano (<X> HP) e recuou para <Spot de Recuo>!`
  - O bot recua para uma posição de cobertura (ex: Jungle, Base CT, Fundo de Tapete).
- **Critério de Aprovação:** Preservação de armamento e vida do bot ao sofrer dano considerável.

### Teste 5.2: Mecânica de `ONE_AND_DONE`
- **Como testar:**
  - Posicionamentos marcados como `ONE_AND_DONE` (como *Firebox*, *Beco/Rato* ou *Canto do Short*).
  - Assim que o bot engaja ou sofre o primeiro disparo, ele não insiste no duelo estático e bate em retirada para a posição secundária (`ct_a_ninja_hide`, `ct_mid_connector_headshot`, etc.).
  - Mensagem no chat:
    `[CsBot One&Done] <BotName> disparou de surpresa e recuou com vida para <Spot>!`
- **Critério de Aprovação:** Comportamento similar a jogadores de nível avançado que punem o avanço e fogem sem dar o *re-peek*.

---

## 6. Teste da Regra Anti-Rush (Cadência Estrita)

- **O que observar:**
  - Se um round for jogado em ritmo `FAST_CONTACT`, o Maestro Tático proíbe estritamente outro `FAST_CONTACT` em sequência no round armado seguinte.
  - O IGL forçará `SLOW_DEFAULT` (15-22s de staging) ou `TIMED_EXECUTE` para recompor a cadência e economizar utilitárias.
- **Critério de Aprovação:** Impossibilidade de o servidor entrar em loop de rushes consecutivos.

---

## 7. Matriz de Comandos Disponíveis na Fase 3

| Comando | Onde usar | Função |
| :--- | :--- | :--- |
| `!executar` ou `!go` | Chat do Jogo | Cancela o staging atual e ordena invasão imediata de todos os bots |
| `!tatica <call>` | Chat do Jogo | Passa uma estratégia personalizada para o Ollama adaptar na hora |
| `!rejeitar` | Chat do Jogo | Rejeita a estratégia atual e pede para a IA gerar uma proposta alternativa |
| `!pos <setor>` | Chat do Jogo | Assume uma posição (`janela`, `b`, `conector`, `a`) e o bot cede o setor |
| `!drop [arma]` | Chat do Jogo | Solicita drop de arma para o bot mais rico durante o Freeze Time |
| `!ws` / `!knife` | Chat do Jogo | Selecionador de skins e facas pelo WeaponPaints |

---

## 8. Critérios Finais para Conclusão da Fase 3
- [x] Solução compilada com `0 erros` e `0 avisos`.
- [x] Binários (`CsBotManager.dll`) e base de micro-posições (`TacticalSpots_de_mirage.json`) implantados em `H:\CS2_AI_Server`.
- [x] Inferência assíncrona do Ollama com `keep_alive: -1` respondendo no tempo de Freeze Time sem travar o jogo.
- [x] Staging Hold eliminando rush desgovernado.
- [x] Fallback preservando vida com anúncio visual no chat.
- [x] Comando `!executar` funcionando com resposta instantânea.
