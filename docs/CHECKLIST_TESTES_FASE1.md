# Checklist de Testes e Validação - Fase 1 (Servidor & Mecânica Base)

Este documento estabelece todos os critérios de aceite para homologar a **Fase 1 (Ambiente, Servidor Dedicado e Base Mecânica)** antes de iniciarmos o desenvolvimento da **Fase 2 (Maestro Tático, Economia, HUD e IA com Ollama)**.

---

## 1. O Que Você Deve Testar e Aprovar (Critérios de Sucesso)

### A. Inicialização do Servidor e Banco de Dados
- [ ] **Execução do Batch**: Clicar duas vezes em `start_cs2_ai_server.bat` (em `H:\CS2_AI_Server` ou no atalho do workspace).
- [ ] **Prompt do CMD Limpo**: O script valida a injeção do Metamod no `gameinfo.gi` (em `H:\CS2_AI_Server`) e inicia o MariaDB portátil sem nenhum erro de sintaxe.
- [ ] **Console do CS2 Ativo**: A janela do servidor dedicado do CS2 abre, exibe o carregamento dos módulos (`BotController`, `BotHider`, `BotVision`, `CounterStrikeSharp`) e carrega o mapa `de_mirage`.
- [ ] **Finalização do Carregamento**: O console deve exibir `Server tick rate: 64.0` e ficar aguardando conexões.

### B. Conexão do Cliente (Steam)
- [ ] **Conexão Direta**: No CS2 oficial (aberto pela Steam), abrir o console (`'`) e digitar `connect 127.0.0.1:27016`.
- [ ] **Entrada no Servidor**: O carregamento da Mirage deve ser concluído rapidamente e você deve entrar na partida sem ser desconectado.
- [ ] **Reconhecimento de Admin**: No console do cliente ou do servidor, você possui privilégios de administrador vinculados à sua SteamID64 (`@css/root`).

### C. Sistema de Skins e Cosméticos (`WeaponPaints`)
- [ ] **Menu de Facas**: Digitar no chat `!knife` e selecionar uma faca (ex: Karambit, Butterfly). Digitar `!kill` ou esperar o próximo round para ver a faca equipada na sua mão.
- [ ] **Menu de Skins**: Digitar `!wp` ou `!skins` no chat e verificar se o menu de armas e pinturas responde normalmente.
- [ ] **Persistência no MariaDB**: Ao reconectar ou trocar de time, suas skins selecionadas continuam salvas no banco de dados local.

### D. Mecânica e Comportamento dos Bots (`CS2-Bot-Improver`)
- [ ] **Preenchimento de Bots**: A partida deve conter 10 jogadores no total (você + 9 bots, ou 5v5 se você estiver no espectador).
- [ ] **Mira Humanizada (Sem Snap Robótico)**:
  - Observar os bots atirando: eles devem ter tempo de reação humano (~200ms a 280ms) ao avistar um inimigo.
  - A mira não deve "teletransportar" para a cabeça através de paredes.
  - Ao disparar em rajadas (spray), os bots devem compensar o recuo para baixo como um jogador real.
- [ ] **Execução de Granadas Pré-Programadas (`NadeSystem`)**:
  - No início do round de TR na Mirage, observar se bots de suporte param em posições específicas e lançam smokes/flashes sincronizadas (ex: smoke na Janela, smoke no Conector, smoke na Cabecinha).
- [ ] **Cosméticos nos Bots (`BotRandomizer`)**:
  - Verificar se os bots aparecem equipados com skins aleatórias, luvas e facas personalizadas.
- [ ] **Movimentação Natural**: Os bots percorrem o mapa utilizando os caminhos do NavMesh, abrindo ângulos e fazendo checagens de quinas, sem ficarem travados correndo contra a parede na base.

---

## 2. O Que NÃO Pode Estar Acontecendo (Sinais de Alerta)

| O que NÃO pode acontecer | Causa Provável | Ação de Correção |
| :--- | :--- | :--- |
| **Servidor fechar sozinho após 5 segundos** | Conflito em alguma DLL ou porta `27016` ocupada. | Verificar se outra instância do `cs2.exe` ficou presa no Gerenciador de Tarefas. |
| **Mensagem de erro de conexão com MySQL no chat ao digitar `!wp`** | MariaDB não subiu na porta 3306. | Verificar se o processo `mysqld.exe` está ativo ou reiniciar o batch. |
| **Bots parados na base sem se mover ou pulando em círculos** | Módulo `BotController` ou `BotAI` não carregou. | Digitar `meta list` e `css_plugins list` no console do servidor para verificar se todos os plugins estão `[loaded]`. |
| **Bots com mira teletransportando e dando headshot instantâneo através da smoke** | `BotVision` ou `BotAimImprover` inativo (caindo na IA padrão da Valve). | Verificar se os `.vdf` do Metamod estão em `game/csgo/addons/metamod/`. |
| **Qualquer arquivo modificado na pasta `H:\...` da Steam** | Vazamento de diretório ou junção invertida. | A pasta `H:` deve permanecer 100% limpa e inalterada. |

---

## 3. Comandos Úteis de Diagnóstico no Console do Servidor

No console do servidor dedicado (janela preta aberta pelo `start_cs2_ai_server.bat`), digite:

```text
// 1. Verificar se o Metamod e os módulos C++ estão ativos
meta list

// 2. Verificar se todos os plugins C# (.NET) do CounterStrikeSharp estão carregados
css_plugins list

// 3. Checar status da rede e jogadores conectados
status
```

> **Critério de Conclusão da Fase 1**:  
> Se `meta list` listar os módulos do BotController/BotHider/BotVision, `css_plugins list` listar o WeaponPaints e os módulos do BotImprover, você conseguir jogar normalmente com faca/skins e os bots jogarem com granadas e mira humanizada, a **Fase 1 está 100% concluída e aprovada**.
