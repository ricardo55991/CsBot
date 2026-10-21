# 🎮 CsBot — Autonomous & Tactical AI System for Counter-Strike 2

[![.NET 10.0](https://img.shields.io/badge/.NET-10.0-purple.svg)](https://dotnet.microsoft.com/)
[![CounterStrikeSharp](https://img.shields.io/badge/CounterStrikeSharp-API%20v300+-blue.svg)](https://github.com/roflmuffin/CounterStrikeSharp)
[![Source 2](https://img.shields.io/badge/Engine-Source%202-orange.svg)](https://www.counter-strike.net/)
[![Ollama LLM](https://img.shields.io/badge/LLM-qwen2.5%3A3b-green.svg)](https://ollama.com/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

> **CsBot** é um ecossistema de Inteligência Artificial Competitiva e Orgânica para o **Counter-Strike 2 (Source 2)** desenvolvido em C# sobre o framework **CounterStrikeSharp**. O sistema transforma bots nativos em companheiros de equipe e adversários inteligentes com leitura de jogo Tier-1, sem o uso de hacks ou scripts estáticos, integrando comandos de voz em tempo real e decisões estratégicas geradas por IA local.

---

## ⚡ Destaques da Arquitetura

* **Controle Físico Real via NavMesh (64Hz):** Conexão direta com a engine via `BotControllerApi.dll`, eliminando o conflito com a IA nativa da Valve e operando com coordenadas tridimensionais reais, ângulos de pitch/yaw e stances táticas (`PASSIVE_HOLD`, `AGGRESSIVE_POKE`, `JIGGLE_INFO`, `ONE_AND_DONE`).
* **Comandante IGL por LLM Local:** Tomada de decisão tática assíncrona com Ollama local (`qwen2.5:3b` via Vulkan/GPU), aliada a uma Pirâmide de Probabilidade (Tier 1 Padrão, Tier 2 Variações e Tier 3 Cheese Plays).
* **Ponte de Voz em Tempo Real (Voice IGL):** Listener HTTP local na porta `27080` com reconhecimento de voz via Whisper para comandos instantâneos por microfone (*"Executa"*, *"Miou"*, *"Banga meio"*, *"Me dá drop"*, *"Tô na cabine"*).
* **Economia Determinística & Setup Double AWP:** Cálculo do Loss Bonus real ($1400 a $3400), trava de gastos em Eco, drops coordenados entre bots mantendo reserva segura ($2000), disciplina da C4 no freeze time, looting de rifles caídos e 35% de chance de Double AWP no CT rico.
* **Comunicação Orgânica & Callouts:** Chat de equipe e rádio nativo sincronizados para contato visual, alerta instantâneo de rush (3+ inimigos em 3.5s), callout pós-morte com delay humano informando dano ("MUITO MIADO -82 HP") e audição de passos através da parede.
* **Inteligência de Combate & Mobilidade:**
  - *Faca na mão (250 u/s)* em rotas seguras com *Freio Tático* (saca a primária imediatamente antes de chokepoints ou contato).
  - *Pistol Swap Rápido* ao zerar o pente em curta distância (< 500u) vs. *Recuo para Cobertura Furtiva* para recarregar com segurança em média/longa distância (>= 500u).
* **Protocolos de Bombsite & Prioridade de Kit:**
  - *Plant Limpo:* Entrada de rifle em punho com varredura prévia de cantos críticos e escolha entre plant aberto e fechado.
  - *Smoke Defuse & Fake Roulette:* Lança smoke na bomba antes de desarmar e varia entre fake clássico, tap & step out, half defuse e stick a frio.
  - *Prioridade Inteligente de Defuse:* CT sem kit cede imediatamente a vez para aliado com kit a até 400u, reduzindo o tempo de 10s para 5s enquanto o bot sem kit dá cobertura agachado.
* **Macro-Pivôs TR de Mid-Round:** Reação a paredão de utilitárias (*Brick Wall Pivot* com 60% espera, 34% default, 6% giro pro outro bomb), oportunidade de invasão rápida com abate do Lurker isolado e conversão de first-kill em split.
* **Arsenal Web UI & Launcher Unificado (`abrir_arsenal_skins.bat`):** Painel web visual (FastAPI + JS) conectado ao banco MariaDB portátil local (`weaponpaints`) na porta `8080`. Conta com catálogo completo de 20 modelos de facas (556 pinturas mapeadas com preview global simultâneo de acabamentos), 35 armas convencionais (1.456 skins completas), 94 luvas, 15 presets de acabamentos (Doppler Phases 1-4, Ruby, Sapphire, Black Pearl, Emerald, Gamma, Fade 100%, Fire & Ice, Blue Gem), resolução inteligente de Paint IDs específicos da Valve, aviso visual para skins inexistentes no CS2 e aba "Arsenal Equipado" com fotos em alta definição, StatTrak, NameTags, desgaste de float e filtro dinâmico em tempo real por equipe (CT / TR / AMBOS).
* **Telemetria Forense sob Demanda (`!debug` e `!nota`):** Gravação de relatórios de partida estruturados em Markdown com snapshots instantâneos de coordenadas, vida, inventário e detector automático de anomalias.

---

## 📂 Estrutura do Repositório

```text
CsBot/
├── .gitignore                      # Regras otimizadas para .NET 10, Python e CS2
├── README.md                       # Documentação principal do projeto
├── abrir_arsenal_skins.bat         # Launcher unificado do Arsenal Web UI (FastAPI + MariaDB + Navegador)
├── start_cs2_ai_server.bat         # Inicializador do servidor dedicado isolado
│
├── docs/                           # Documentação detalhada e relatórios técnicos
│   ├── MANUAL_DO_JOGADOR_E_COMANDOS.md   # Guia definitivo para jogadores (Voz, Chat, Calls)
│   ├── GUIA_PROJETO_CSBOT.md             # Especificação técnica completa de todas as fases
│   ├── PLANO_IMPLANTACAO_CORRECOES.md    # Arquitetura e resoluções do motor NavMesh
│   ├── RELATORIO_AUDITORIA_TECNICA.md    # Auditoria forense linha a linha
│   └── CHECKLIST_TESTE_COMPLETO_JOGO.md  # Roteiro de testes in-game
│
├── scripts/                        # Utilitários de setup, inspeção e testes PowerShell
│   ├── check_env.ps1               # Validação de ambiente e portas
│   ├── setup_junctions_and_links.ps1# Configuração de links simbólicos para CS2
│   ├── test_ollama.ps1             # Teste de inferência do modelo local
│   └── inspect_*.ps1               # Inspetores de entidades e memória Source 2
│
└── src/
    └── CsBotManager/               # Plugin CounterStrikeSharp (C# .NET 10.0)
        ├── CsBotManagerPlugin.cs   # Orquestrador central, ciclo de vida e eventos
        ├── BotLocomotionDriver.cs  # Driver motor NavMesh e injeção de usercmd 64Hz
        ├── CombatAdapter.cs        # Pistol swap <500u vs. recuo para cobertura >=500u
        ├── MobilityController.cs   # Faca na mão (250 u/s) e freio tático
        ├── EconomyManager.cs       # BuyStates, auto-drop, Double AWP e C4 discipline
        ├── RoleManager.cs          # AWPer, Entry, Rotator, Anchor e troca de posições
        ├── CtDefenseController.cs  # Posições de spawn, defesa e pop-flash em dupla
        ├── CtRetakeAndDefuseBrain.cs# Smoke defuse, fake roulette e prioridade de kit
        ├── SiteClearAndPlantController.cs # Varredura de bomb e plant aberto/fechado
        ├── TrMacroPivotController.cs # Brick Wall Pivot, Lurker call e Mid-Round exploit
        ├── TacticalCalloutSystem.cs# Spot info, rush alert, dead call e passos
        ├── ContextualSmokeAndAudioBrain.cs # Roleta dinâmica de reação a smokes
        ├── PacingAndFallbackController.cs  # Staging, temporização e recuo com vida
        ├── TacticalProbabilityEngine.cs    # Pirâmide de táticas e jogadas raras
        ├── TacticalHudRenderer.cs  # Renderizador HTML da Chip HUD no topo da tela
        ├── MatchTelemetryLogger.cs # Gravador forense Markdown (!debug / !nota)
        ├── VoiceCommandBridge.cs   # Listener HTTP porta 27080 para comandos de voz
        ├── OllamaIglService.cs     # Cliente HTTP assíncrono para LLM local
        ├── MapProfileManager.cs    # Carregador de perfis JSON multi-mapa
        ├── Models.cs               # Estruturas de dados, enums e DTOs
        └── MapProfiles/            # Perfis táticos e chokepoints dos mapas
            ├── de_mirage.json
            ├── de_dust2.json
            └── de_inferno.json
```

---

## 🚀 Como Executar

### 1. Pré-Requisitos
- **Windows 10/11 x64**
- **.NET 10.0 SDK**
- **Counter-Strike 2** instalado
- **Servidor Dedicado Isolado** (ex: `H:\CS2_AI_Server`) com **Metamod:Source** e **CounterStrikeSharp**
- **Ollama** com o modelo `qwen2.5:3b` baixado (`ollama run qwen2.5:3b`)

### 2. Compilação do Plugin
O projeto utiliza compilação orientada a compilador (*Compiler-Driven Development*). A compilação implanta automaticamente o binário na pasta de plugins do servidor:

```powershell
dotnet build src/CsBotManager/CsBotManager.csproj
```

### 3. Inicialização do Servidor
Execute o inicializador na raiz:

```cmd
start_cs2_ai_server.bat
```

No console do seu cliente CS2 Vanilla, conecte-se via:
```text
connect 127.0.0.1:27016
```

### 4. Personalização de Skins e Arsenal (Web UI)
Para abrir o catálogo visual de facas, luvas e skins a qualquer momento:

```cmd
abrir_arsenal_skins.bat
```

O launcher verifica a conectividade com o MariaDB, sobe o backend FastAPI na porta `8080` e abre seu navegador padrão automaticamente. No CS2, basta digitar `!wp` no chat para sincronizar suas novas facas e pinturas instantaneamente.

---

## 📖 Manuais e Referências

* Para aprender todos os comandos de texto e chamadas por voz: [**Manual do Jogador & Guia de Comandos**](docs/MANUAL_DO_JOGADOR_E_COMANDOS.md).
* Para a especificação técnica aprofundada de todas as fases: [**Guia de Arquitetura do Projeto**](docs/GUIA_PROJETO_CSBOT.md).
* Para a auditoria técnica aprofundada do motor físico e regras de integridade: [**Relatório de Auditoria Técnica V2**](docs/RELATORIO_AUDITORIA_TECNICA_V2.md) e [**Bateria de Ajuste e Validação**](docs/BATERIA_SEGUNDO_AJUSTE_VALIDACAO.md).
* Para a auditoria forense inicial do código: [**Relatório de Auditoria Técnica**](docs/RELATORIO_AUDITORIA_TECNICA.md).

---

## 📄 Licença

Distribuído sob licença de desenvolvimento privado para propósitos educacionais e de pesquisa em IA de jogos.
