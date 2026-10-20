# RELATÓRIO DE AUDITORIA FORENSE TÉCNICA V2 — CsBot

Data: 2026-10-20  
Repositório: `D:\Projetos\Future\CsBot`

## 1. Resumo executivo

Esta auditoria foi executada em **modo somente leitura**, com foco em evidência estática do conteúdo versionado.

Principais conclusões:
- O projeto possui **pipeline físico real** para movimentação/inputs de bot (nav + usercmd) em vários fluxos (`BotLocomotionDriver` + `BotControllerApi`), porém com conflitos de ownership entre controladores.
- Há riscos **críticos** de estado obsoleto no controle tático assíncrono (Ollama) e de inconsistência em inventário/C4 por uso de grants diretos (`GiveNamedItem`) sem acoplamento estrito ao fluxo físico de troca/drop.
- Há riscos **importantes** de concorrência/lifecycle (timers órfãos, ausência de cancelamento/ordenação de requests, possível race em perfil de mapa), percepção privilegiada por distância global e validação defensiva incompleta de handles/entidades.
- A infraestrutura está fortemente acoplada ao ambiente original (`H:\CS2_AI_Server`), o que reduz portabilidade; isso é um problema de operação/configuração, não necessariamente defeito funcional em runtime no host original.
- Não houve validação de runtime nesta máquina (CS2/Ollama/MariaDB/plugins externos não iniciados nesta etapa).

---

## 2. Escopo efetivamente disponível

- **Raiz analisada:** `D:\Projetos\Future\CsBot`
- **Branch:** `main`
- **Commit:** `cf85eeb873f81ccdaa2253470411d66ba2a5aec5`
- **Diretórios encontrados:** `.git/`, `docs/`, `scripts/`, `src/`
- **Diretórios esperados mas ausentes nesta cópia:** `arsenal_web/` (não presente)
- **Arquivos versionados encontrados:** 52 arquivos rastreados por git
- **Dependências externas presentes nesta cópia:** não comprovadas por artefato local versionado (apenas referências e paths)
- **Dependências externas ausentes/não verificadas localmente:** CS2 dedicado completo, CounterStrikeSharp runtime completo, `CounterStrikeSharp.API.dll` (fora do repo), `BotControllerApi.dll` (fora do repo), plugins externos (BotAI/BotState/NadeSystem/BotControllerImpl/WeaponPaints), MariaDB do servidor original, modelo `qwen2.5:3b` e demais modelos Ollama
- **Modelo Ollama:** não instalado/verificado nesta auditoria (sem pull/start)
- **Servidor CS2:** não iniciado
- **Banco:** não consultado
- **Build:** não executado
- **Testes runtime:** não executados
- **Motivo objetivo das limitações:** auditoria forense estática em clone do git, com proibição explícita de recriar ambiente original e de iniciar serviços externos.

---

## 3. Limitações e artefatos indisponíveis

1. `arsenal_web/` não está presente: **NÃO VERIFICÁVEL NESTA CÓPIA DO REPOSITÓRIO**.
2. DLLs e plugins referenciados por caminho absoluto (`H:`) não são artefatos versionados.
3. Sem servidor em execução, não é possível comprovar comportamento nativo da Source 2, competição entre BotAI/BotControllerImpl e este plugin no tick real.
4. Sem Ollama em execução/modelo disponível, não é possível validar distribuição real de respostas do LLM nem aderência empírica ao schema sob carga.
5. Sem banco do servidor original, não há verificação de schema/queries reais de arsenal web.

---

## 4. Branch e commit analisados

- Branch: `main`
- Commit: `cf85eeb873f81ccdaa2253470411d66ba2a5aec5`
- Working tree: limpa no início da sessão.

---

## 5. Inventário completo dos arquivos

Legenda de critérios (coluna “Critérios”):
- C1 controle físico
- C2 ownership/conflitos
- C3 percepção
- C4 economia/inventário/C4
- C5 plant/defuse
- C6 mobilidade/combate
- C7 async/thread/lifecycle
- C8 performance/telemetria
- C9 Ollama/prompt/DTO
- C10 identidade/timers/estado
- C11 arsenal web/schema
- C12 configuração/portabilidade

| Arquivo | Responsabilidade aparente | Classes/Módulos principais | Critérios | Auditado integralmente? | Observação |
|---|---|---|---|---|---|
| `.gitignore` | exclusões de build/log/cache | n/a | C12 | Sim | Sem riscos críticos diretos |
| `README.md` | visão geral/execução | n/a | C12 | Sim | Referências ao ambiente `H:` |
| `start_cs2_ai_server.bat` | bootstrap do servidor | batch startup | C12 | Sim | acoplado a `H:` + `ExecutionPolicy Bypass` |
| `docs/CHECKLIST_TESTES_FASE1.md` | checklist fase 1 | n/a | C12 | Sim | operacional/local |
| `docs/CHECKLIST_TESTES_FASE2.md` | checklist fase 2 | n/a | C12 | Sim | operacional/local |
| `docs/CHECKLIST_TESTES_FASE3.md` | checklist fase 3 | n/a | C12 | Sim | cita `iniciar_servidor.bat` ausente |
| `docs/CHECKLIST_TESTE_COMPLETO_JOGO.md` | checklist consolidado | n/a | C12 | Sim | cita Voice IGL e script ausente |
| `docs/GUIA_PROJETO_CSBOT.md` | guia técnico amplo | n/a | C12/C11 | Sim | cita `arsenal_web` ausente |
| `docs/MANUAL_DO_JOGADOR_E_COMANDOS.md` | manual do jogador | n/a | C12 | Sim | depende de runtime externo |
| `docs/PLANO_IMPLANTACAO_CORRECOES.md` | plano técnico | n/a | C12 | Sim | links absolutos locais |
| `docs/RELATORIO_AUDITORIA_TECNICA.md` | relatório anterior | n/a | C12 | Sim | parcialmente desatualizado frente ao csproj atual |
| `scripts/archive_botbuy.ps1` | arquiva plugin BotBuy | PowerShell | C12 | Sim | operação destrutiva local |
| `scripts/check_enums.cs` | inspeção API por reflexão | utilitário C# | C12 | Sim | path absoluto externo |
| `scripts/check_env.ps1` | valida/starta serviços locais | PowerShell | C12 | Sim | altera `gameinfo.gi`, sobe serviços |
| `scripts/check_ollama.ps1` | diagnóstico Ollama | PowerShell | C9/C12 | Sim | depende de serviço externo |
| `scripts/check_types.cs` | inspeção tipos API | utilitário C# | C12 | Sim | path absoluto externo |
| `scripts/inspect_botbuy.ps1` | inspeção de DLL externa | PowerShell | C12 | Sim | depende de `H:` |
| `scripts/inspect_bots.ps1` | inspeção de DLLs externas | PowerShell | C12 | Sim | depende de `H:` |
| `scripts/inspect_css_api.ps1` | inspeção CSS API | PowerShell | C12 | Sim | depende de `H:` |
| `scripts/inspect_nade.ps1` | reflexão NadeSystem | PowerShell | C12 | Sim | depende de `H:` |
| `scripts/inspect_rdr.ps1` | inspeção RoundDamageRecap | PowerShell | C12 | Sim | depende de `H:` |
| `scripts/inspect_wp.ps1` | inspeção WeaponPaints | PowerShell | C12/C11 | Sim | depende de DLL externa |
| `scripts/setup_junctions_and_links.ps1` | cria junctions/hardlinks | PowerShell | C12 | Sim | infra sensível |
| `scripts/test_ollama.ps1` | teste de inferência Ollama | PowerShell | C9/C12 | Sim | depende de modelo/serviço |
| `src/CsBotManager/CsBotManager.csproj` | build/referências/deploy | .NET project | C12 | Sim | `net10.0`, HintPath e deploy hardcoded |
| `src/CsBotManager/Models.cs` | DTOs/enums domínio | classes de modelo | C1-10 | Sim | base estrutural |
| `src/CsBotManager/CsBotManagerPlugin.cs` | orquestrador principal | plugin/eventos/comandos | C1-10/C12 | Sim | núcleo de lifecycle/async/timers |
| `src/CsBotManager/BotLocomotionDriver.cs` | navegação e usercmd | driver físico | C1/C2/C5/C6/C10 | Sim | núcleo de controle físico |
| `src/CsBotManager/PacingAndFallbackController.cs` | staging/execute/fallback | pacing controller | C1/C2/C10 | Sim | timers não rastreados |
| `src/CsBotManager/RoleManager.cs` | papéis/atribuição | role manager | C2/C10 | Sim | múltiplos writers de ordem |
| `src/CsBotManager/UtilityAndClockCoordinator.cs` | relógio/save/util | utility+clock | C2/C6/C8/C10 | Sim | gate de util não consumido |
| `src/CsBotManager/TrMacroPivotController.cs` | pivôs TR | macro pivot | C2/C10 | Sim | timers sem ownership central |
| `src/CsBotManager/MidRoundAdapter.cs` | ações mid-round/fake | midround | C2/C5/C6/C10 | Sim | timers aninhados |
| `src/CsBotManager/CtDefenseController.cs` | defesa CT/duo play | CT defense | C2/C5/C10 | Sim | timers aninhados |
| `src/CsBotManager/CtRetakeAndDefuseBrain.cs` | retake/defuse/smoke | retake brain | C5/C10 | Sim | validação parcial de handles |
| `src/CsBotManager/EconomyManager.cs` | compras/drop/C4/looting | economy manager | C4/C10 | Sim | grants diretos com risco de inconsistência |
| `src/CsBotManager/SiteClearAndPlantController.cs` | clear site/plant | plant controller | C3/C5 | Sim | critério por proximidade global |
| `src/CsBotManager/MobilityController.cs` | faca/mobilidade | mobility | C2/C6/C8 | Sim | troca de arma por comando |
| `src/CsBotManager/CombatAdapter.cs` | micro combate | combat | C3/C6/C8 | Sim | decisão por distância global |
| `src/CsBotManager/ContextualSmokeAndAudioBrain.cs` | reação a smoke/áudio | smoke/audio brain | C2/C3/C10 | Sim | integração com callout/defense |
| `src/CsBotManager/TacticalCalloutSystem.cs` | callouts contato/rush/áudio | callout system | C3/C8/C10 | Sim | usa scans globais/raio |
| `src/CsBotManager/PlayerIntentTracker.cs` | intenção por movimento | intent tracker | C2/C10 | Sim | suporte a swap dinâmico |
| `src/CsBotManager/TacticalHudRenderer.cs` | HUD HTML | renderer | C8/C9 | Sim | interpolação sem encoding |
| `src/CsBotManager/MatchTelemetryLogger.cs` | telemetria forense | logger | C8/C9/C10 | Sim | `rawIglJson` não alimentado em chamada principal |
| `src/CsBotManager/OllamaIglService.cs` | cliente Ollama + fallback | IGL service | C7/C9 | Sim | sem token/sem sequenciamento externo |
| `src/CsBotManager/TacticalProbabilityEngine.cs` | escolha de play | probability engine | C2/C8 | Sim | motor local de tier |
| `src/CsBotManager/MapProfileManager.cs` | perfis/chokepoints/spots | profile manager | C3/C7/C10/C12 | Sim | dicionário mutável sem sincronização explícita |
| `src/CsBotManager/TacticalSpotsManager.cs` | camada de compatibilidade | tactical spots facade | C12 | Sim | wrapper |
| `src/CsBotManager/VoiceCommandBridge.cs` | bridge HTTP local de voz | HTTP listener | C7/C9/C10 | Sim | sem limite explícito de payload |
| `src/CsBotManager/MapProfiles/de_mirage.json` | perfil Mirage | dados de mapa | C1-C5/C12 | Sim | consistente internamente |
| `src/CsBotManager/MapProfiles/de_dust2.json` | perfil Dust2 | dados de mapa | C1-C5/C12 | Sim | fallback ids inexistentes no próprio arquivo |
| `src/CsBotManager/MapProfiles/de_inferno.json` | perfil Inferno | dados de mapa | C1-C5/C12 | Sim | fallback ids inexistentes no próprio arquivo |
| `src/CsBotManager/TacticalSpots_de_mirage.json` | spots legado Mirage | dados de mapa | C12 | Sim | duplicata exata de `de_mirage.json::spots` |

Arquivos mencionados por docs/código e ausentes nesta cópia:
- `H:\CS2_AI_Server\iniciar_servidor.bat` (citado em docs)
- `H:\CS2_AI_Server\arsenal_web\app.py` (citado em docs)
- DLLs/plugins externos referenciados por `HintPath`/scripts

---

## 6. Dependências internas e externas

### Internas (versionadas)
- Núcleo do plugin (`CsBotManagerPlugin`) + controladores + modelos + profiles JSON.

### Externas (não versionadas no repo)
- `CounterStrikeSharp.API.dll` e `BotControllerApi.dll` (`HintPath` no csproj)
- Runtime CS2 dedicado e instalação em `H:\CS2_AI_Server`
- Plugins externos (`WeaponPaints`, `BotAI`, etc.)
- Ollama + modelo `qwen2.5:3b`
- MariaDB/armazenamento externo

Classificação: **COMPROVADO POR CONFIGURAÇÃO VERSIONADA** (dependência declarada) e **NÃO VERIFICÁVEL NESTA CÓPIA DO REPOSITÓRIO** (presença/versão real dos artefatos externos).

---

## 7. Configuração de projeto identificada

Fonte: `[src/CsBotManager/CsBotManager.csproj:L1-L43]`

- SDK: `Microsoft.NET.Sdk`
- TFM: `net10.0`
- `ImplicitUsings`: `enable`
- `Nullable`: `enable`
- `CopyLocalLockFileAssemblies`: `false`
- `PackageReference`: inexistente
- Referências locais por `HintPath`:
  - `CounterStrikeSharp.API.dll` em `H:\...\api\`
  - `BotControllerApi.dll` em `H:\...\shared\BotControllerApi\`
- `DeployPlugin` pós-build copia para `H:\...\plugins\CsBotManager\`
- JSONs copiados para output por `None Update`.

Classificação:
- Declaração técnica: **COMPROVADO POR CONFIGURAÇÃO VERSIONADA**
- Compatibilidade em máquina diferente: **EXIGE VALIDAÇÃO NO SERVIDOR ORIGINAL**

---

## 8. Mapa de arquitetura

Fluxo macro (estático):

`Eventos/Comandos` -> `CsBotManagerPlugin` -> `Role/Economy/Pacing/CT/MidRound/Retake/Plant` -> `BotLocomotionDriver` -> (`CCSBot GoalPosition/Timers` + `BotControllerApi usercmd`) -> entidade nativa

Fluxo de IA local:

`OnRoundStart / !tatica / !rejeitar` -> `Task.Run` -> `OllamaIglService.GetTacticalDecisionAsync` -> `Server.NextFrame` -> `_currentPlan` -> controladores aplicam ordens

Fluxo de voz:

`HTTP POST 127.0.0.1:27080/voice` -> `VoiceCommandBridge` -> `ProcessVoiceCommand` -> ações em controladores/locomotion/economy

---

## 9. Mapa de listeners, timers, Tasks e callbacks

### Listeners/eventos
- `RegisterEventHandler<EventRoundStart>` `[src/CsBotManager/CsBotManagerPlugin.cs:L103]`
- `EventRoundFreezeEnd` `[...:L104]`
- `EventRoundEnd` `[...:L105]`
- `EventPlayerHurt/Death/Footstep` `[...:L106-L108]`
- `EventBombPlanted/Begindefuse/SmokegrenadeDetonate` `[...:L109-L111]`
- `RegisterListener<Listeners.OnTick>` `[...:L113]`

### Tasks assíncronas
- `Task.Run` em decisão de IA no round start e comandos `[src/CsBotManager/CsBotManagerPlugin.cs:L250, L719, L761]`
- callback para game thread via `Server.NextFrame` `[...:L263, L732, L774]`

### Timers críticos (amostra)
- `_hudTimer`, `_buyTimer`, `_clockTimer` no plugin `[...:L291, L319, L394]`
- Pacing: staging repeat + flash 0.8s `[src/CsBotManager/PacingAndFallbackController.cs:L104-L112, L143-L151]`
- CT defense: 1.5s + 1.0s + 6.0s `[src/CsBotManager/CtDefenseController.cs:L131-L177]`
- MidRound fake chain: 6.0s + 4.0s `[src/CsBotManager/MidRoundAdapter.cs:L79-L101]`
- Retake fake defuse: múltiplos timers `[src/CsBotManager/CtRetakeAndDefuseBrain.cs:L177-L231]`

### Cancelamento/lifecycle
- Round end mata `_hudTimer/_buyTimer/_clockTimer`, reset pacing e locomotion `[src/CsBotManager/CsBotManagerPlugin.cs:L420-L441]`
- `Unload` para voice + locomotion reset `[src/CsBotManager/CsBotManagerPlugin.cs:L130-L135]`
- Falta cancelamento explícito para `Task.Run` de Ollama em voo.

---

## 10. Matriz dos controladores versus recursos disputados

| Controlador | Recurso controlado | Frequência | Cancela próprio estado? | Pode sobrescrever outros? | Evidência |
|---|---|---|---|---|---|
| `PacingAndFallbackController` | Staging/Execute, throws e nav | timers + eventos | Parcial | Sim | `[src/CsBotManager/PacingAndFallbackController.cs:L104-L157]` |
| `CtDefenseController` | hold/rotate/duo flash | timers | Parcial (timer raiz) | Sim | `[src/CsBotManager/CtDefenseController.cs:L131-L177,L203-L250]` |
| `MidRoundAdapter` | fake, rotate, hide, rush | timers + eventos | Parcial | Sim | `[src/CsBotManager/MidRoundAdapter.cs:L79-L101,L104-L144]` |
| `TrMacroPivotController` | pivôs macro | timers | Parcial | Sim | `[src/CsBotManager/TrMacroPivotController.cs]` |
| `UtilityAndClockCoordinator` | save/desespero/flags táticas | clock loop | Sim (flags) | Sim (orders) | `[src/CsBotManager/UtilityAndClockCoordinator.cs:L129-L213]` |
| `MobilityController` | knife/slot swap | OnTick | Sim | Sim | `[src/CsBotManager/MobilityController.cs:L99-L153]` |
| `CombatAdapter` | swap/reload/hide/jiggle | OnTick + timers | Parcial | Sim | `[src/CsBotManager/CombatAdapter.cs:L124-L183]` |
| `BotLocomotionDriver` | nav/usercmd/defuse/throw | OnTick | Parcial | Atua como executor final | `[src/CsBotManager/BotLocomotionDriver.cs:L320-L489]` |

Situação observada: **last-write-wins** em vários campos e ausência de ownership central com generation id/token por ordem.

---

## 11. Matriz de evidências

| Área | Fonte de evidência usada | Classificação |
|---|---|---|
| Controle físico/nav/usercmd | código-fonte C# | COMPROVADO POR ANÁLISE ESTÁTICA |
| Configuração build/deploy | `.csproj`, `.bat` | COMPROVADO POR CONFIGURAÇÃO VERSIONADA |
| Profiles/chokepoints/spots | JSON versionados | COMPROVADO POR ARTEFATO DISPONÍVEL |
| Concorrência/async/timers | código-fonte C# | COMPROVADO POR ANÁLISE ESTÁTICA |
| Performance (risco) | inspeção estática de loops/alocação | INFERIDO PELO FLUXO DE CÓDIGO |
| Ollama runtime real | não executado | EXIGE VALIDAÇÃO NO SERVIDOR ORIGINAL |
| Arsenal web/schema/banco | diretório ausente e sem DB | NÃO VERIFICÁVEL NESTA CÓPIA DO REPOSITÓRIO |
| Build/execução | não realizado | NÃO VERIFICÁVEL NESTA CÓPIA DO REPOSITÓRIO |

---

## 12. Achados detalhados por critério

> Formato: ID, título, severidade, classificação da evidência, arquivo/linhas, classe/método, trecho mínimo, fluxo, esperado vs implementado, impacto, reprodução, risco, dependência externa, confiança, recomendação, teste futuro.

### F-001
- **ID:** F-001
- **Título:** Resposta assíncrona do Ollama pode ser aplicada no round errado
- **Severidade:** 🔴 CRÍTICO
- **Classificação da evidência:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo / linhas:** `[src/CsBotManager/CsBotManagerPlugin.cs:L242-L287]`, `[src/CsBotManager/CsBotManagerPlugin.cs:L711-L785]`
- **Classe / método:** `CsBotManagerPlugin.OnRoundStart`, `CommandTatica`, `CommandRejeitar`
- **Trecho mínimo:** `int capturedRound = _currentRound; ... _currentPlan = plan/newPlan;` (sem checagem de round no callback)
- **Fluxo de chamada:** evento/comando -> `Task.Run` -> `GetTacticalDecisionAsync` -> `Server.NextFrame` -> `_currentPlan = ...`
- **Comportamento esperado:** revalidar `capturedRound` vs `_currentRound` antes de aplicar plano.
- **Comportamento implementado:** aplica plano diretamente no callback.
- **Impacto prático:** plano tardio pode controlar round posterior.
- **Cenário de reprodução:** disparar `!tatica` próximo da troca de round com latência de IA.
- **Risco de crash/conflito/estado inválido:** conflito tático de alto impacto.
- **Dependência externa relacionada:** latência/disponibilidade Ollama.
- **Nível de confiança:** Alto.
- **Recomendação técnica:** gate por `roundId` + rejeição de resposta obsoleta.
- **Teste futuro necessário:** no servidor original, forçar resposta > transição de round e validar descarte.

### F-002
- **ID:** F-002
- **Título:** Ausência de ordenação de respostas concorrentes do Ollama (race last completion wins)
- **Severidade:** 🟠 IMPORTANTE
- **Classificação da evidência:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo / linhas:** `[src/CsBotManager/CsBotManagerPlugin.cs:L250-L287]`, `[src/CsBotManager/CsBotManagerPlugin.cs:L719-L785]`
- **Classe / método:** `CsBotManagerPlugin` (fluxos de decisão)
- **Trecho mínimo:** múltiplos `Task.Run` escrevendo `_currentPlan`.
- **Fluxo:** round start + comandos manuais podem gerar requests simultâneas.
- **Esperado:** sequence/request id com commit monotônico.
- **Implementado:** nenhuma arbitragem de ordem de resposta.
- **Impacto:** tática mais nova pode ser sobrescrita por resposta antiga que chegou depois.
- **Cenário:** spam de `!tatica`/`!rejeitar` em freeze com latência variável.
- **Risco:** conflito de estado tático.
- **Dependência externa:** tempo de resposta do LLM.
- **Confiança:** Alto.
- **Recomendação:** token monotônico por request e compare-and-swap de plano.
- **Teste futuro:** 3 requests concorrentes com delays artificialmente diferentes e validação da ordenação final.

### F-003
- **ID:** F-003
- **Título:** Requests de IA sem cancelamento explícito e sem limite de concorrência
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/OllamaIglService.cs:L43-L51]`, `[src/CsBotManager/CsBotManagerPlugin.cs:L420-L441]`, `[src/CsBotManager/CsBotManagerPlugin.cs:L130-L135]`
- **Classe/método:** `OllamaIglService.GetTacticalDecisionAsync`, lifecycle plugin
- **Trecho mínimo:** assinatura sem `CancellationToken`; round end/unload não cancela task em voo.
- **Fluxo:** request inicia -> round termina -> callback ainda pode tentar aplicar plano.
- **Esperado:** cancel token por round/match + throttle (`SemaphoreSlim`/fila).
- **Implementado:** apenas timeout de `HttpClient` (4.5s).
- **Impacto:** consumo desnecessário + risco de estado obsoleto.
- **Cenário:** múltiplos comandos IA durante transição de fase.
- **Risco:** conflito de estado; pressão de threadpool sob spam.
- **Dependência externa:** Ollama.
- **Confiança:** Alto.
- **Recomendação:** cancelar em round end/unload e limitar requests simultâneas.
- **Teste futuro:** gerar burst de requests, encerrar round e observar callbacks descartados.

### F-004
- **ID:** F-004
- **Título:** Possível race de leitura/escrita em perfil de mapa compartilhado
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** INFERIDO PELO FLUXO DE CÓDIGO
- **Arquivo/linhas:** `[src/CsBotManager/MapProfileManager.cs:L11-L18]`, `[src/CsBotManager/MapProfileManager.cs:L95-L97]`, `[src/CsBotManager/CsBotManagerPlugin.cs:L189]`, `[src/CsBotManager/CsBotManagerPlugin.cs:L250-L260]`
- **Classe/método:** `MapProfileManager.LoadProfile/GetSpotsForTeam`, uso em task de IA
- **Trecho mínimo:** `_spotsById.Clear()` e enumeração de `_spotsById.Values` sem lock explícito.
- **Fluxo:** recarga de profile no round start + leitura em task assíncrona.
- **Esperado:** snapshot imutável ou sincronização de acesso.
- **Implementado:** dicionário mutável compartilhado.
- **Impacto:** inconsistência/exception sob timing adverso.
- **Cenário:** troca de mapa/round com request IA em curso.
- **Risco:** exceção e plano inválido.
- **Dependência externa:** thread scheduling.
- **Confiança:** Médio.
- **Recomendação:** snapshot copy-on-write para leitura assíncrona.
- **Teste futuro:** stress de recarga de profile com requests concorrentes.

### F-005
- **ID:** F-005
- **Título:** Estado de save CT pode não propagar ao guard de defuse no locomotion
- **Severidade:** 🔴 CRÍTICO
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/CsBotManagerPlugin.cs:L538-L559]`, `[src/CsBotManager/MidRoundAdapter.cs:L198-L237]`, `[src/CsBotManager/BotLocomotionDriver.cs:L74-L79]`, `[src/CsBotManager/BotLocomotionDriver.cs:L348-L399]`
- **Classe/método:** `OnBombPlanted`, `HandleBombPlanted`, `NotifyBombState`, `UpdateTick`
- **Trecho mínimo:** `NotifyBombState(... _currentPlan.IsTacticalSaveActive)` é chamado antes de `HandleBombPlanted` alterar `plan.IsTacticalSaveActive`.
- **Fluxo:** planta bomba -> cache de save no locomotion -> adapter decide save -> locomotion continua com estado antigo.
- **Esperado:** sincronização imediata do save após decisão CT.
- **Implementado:** cache potencialmente stale.
- **Impacto:** bot pode insistir em `IN_USE`/retake em cenário que a call mandou save.
- **Cenário:** CT em desvantagem severa com decisão de save.
- **Risco:** conflito estratégico/execução física contraditória.
- **Dependência externa:** estado da partida em runtime.
- **Confiança:** Alto.
- **Recomendação:** atualizar `NotifyBombState` após decisão de save ou ler flag live no loop.
- **Teste futuro:** cenário 2x4 com bomba plantada e verificação de injeção de defuse.

### F-006
- **ID:** F-006
- **Título:** Timers aninhados sem rastreamento completo podem disparar no contexto errado
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/PacingAndFallbackController.cs:L143-L151]`, `[src/CsBotManager/CtDefenseController.cs:L139-L177]`, `[src/CsBotManager/MidRoundAdapter.cs:L92-L101,L182-L189]`, `[src/CsBotManager/CsBotManagerPlugin.cs:L420-L433]`
- **Classe/método:** múltiplos controladores
- **Trecho mínimo:** timers secundários criados sem handle persistente para kill global.
- **Fluxo:** round muda antes do timer secundário executar.
- **Esperado:** registry central de timers por round + cancelamento em reset.
- **Implementado:** cancelamento parcial.
- **Impacto:** comandos tardios sobrescrevendo navegação/stance de nova fase.
- **Cenário:** fim abrupto de round durante sequência fake/duo/execute.
- **Risco:** conflito de estado.
- **Dependência externa:** runtime timer engine.
- **Confiança:** Alto.
- **Recomendação:** encapsular timers em scheduler com ownership de round.
- **Teste futuro:** encerrar round antes de callbacks e verificar que nenhum callback residual roda.

### F-007
- **ID:** F-007
- **Título:** Substituição de estado de navegação pode perder cancelamento de movimento usercmd ativo
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/BotLocomotionDriver.cs:L160-L190]`, `[src/CsBotManager/BotLocomotionDriver.cs:L476-L482]`
- **Classe/método:** `NavigateToSpot`, `NavigateToPosition`, `UpdateTick`
- **Trecho mínimo:** overwrite em `_botStates[slot] = state` com `ActiveMovementId = 0` sem cancelamento prévio garantido.
- **Fluxo:** stance JIGGLE ativa `StartUsercmdMovement` -> novo Navigate sobrescreve state.
- **Esperado:** cancelar `ActiveMovementId` antigo antes de overwrite.
- **Implementado:** cancelamento só em alguns caminhos.
- **Impacto:** movimento lateral órfão conflitando com nova ordem.
- **Cenário:** bot em jiggle recebe nova navegação imediata.
- **Risco:** desvio de controle físico.
- **Dependência externa:** BotControllerApi comportamento.
- **Confiança:** Alto.
- **Recomendação:** função única de transição de estado com cancelamento atômico.
- **Teste futuro:** script de alternância rápida de stances e validação de cancelamentos.

### F-008
- **ID:** F-008
- **Título:** Fluxos de economia/C4/looting usam grant direto e podem gerar inconsistência de inventário
- **Severidade:** 🔴 CRÍTICO
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/EconomyManager.cs:L118-L124]`, `[src/CsBotManager/EconomyManager.cs:L149-L153]`, `[src/CsBotManager/EconomyManager.cs:L442-L453]`, `[src/CsBotManager/EconomyManager.cs:L513-L537]`
- **Classe/método:** `DropWeaponForPlayer`, `TryCoordinateTeamAwpDrop`, `EnforceC4Discipline`, `PerformPostRoundLooting`
- **Trecho mínimo:** uso de `GiveNamedItem(...)` + `drop`/`Remove` parcial.
- **Fluxo:** débito monetário e grant direto, sem cadeia física completa de compra/equip/drop/pickup.
- **Esperado:** transições de inventário com validação de owner/slot/remoção antiga.
- **Implementado:** combinação de grant direto com checks parciais.
- **Impacto:** risco de duplicação (arma/C4), estado divergente entre lógica e engine.
- **Cenário:** doações consecutivas, looting simultâneo, troca de carrier C4 com falha parcial de remoção.
- **Risco:** inventário inválido/conflitos.
- **Dependência externa:** semântica de inventário na engine.
- **Confiança:** Alto.
- **Recomendação:** consolidar pipeline transacional de inventário com pós-condições verificáveis.
- **Teste futuro:** suíte de rounds com asserts de contagem de primárias e única C4 em runtime.

### F-009
- **ID:** F-009
- **Título:** Percepção tática baseada em scans globais por distância (risco de conhecimento privilegiado)
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/TacticalCalloutSystem.cs:L122-L127]`, `[src/CsBotManager/TacticalCalloutSystem.cs:L134-L140]`, `[src/CsBotManager/TacticalCalloutSystem.cs:L173-L178]`, `[src/CsBotManager/SiteClearAndPlantController.cs:L95-L103]`, `[src/CsBotManager/CombatAdapter.cs:L101-L119]`
- **Classe/método:** `HandlePlayerHurt`, `CheckInstantRushDetection`, `EvaluateSafePlantWindow`, `CombatAdapter.UpdateTick`
- **Trecho mínimo:** `Utilities.GetPlayers()` + filtro por raio para inferir presença e C4.
- **Fluxo:** callouts e decisões de plant/combate derivadas de posição global.
- **Esperado:** sinalização baseada em LoS/FOV/spotting/eventos legítimos.
- **Implementado:** contagem por proximidade geométrica.
- **Impacto:** vantagem informacional irreal (wall-awareness indireta).
- **Cenário:** inimigo atrás de parede dentro do raio ainda influencia callout/decisão.
- **Risco:** comportamento anti-natural e potencial unfairness.
- **Dependência externa:** APIs de visibilidade/spotting.
- **Confiança:** Alto.
- **Recomendação:** introduzir camada de percepção legitimada (visão/áudio validado/TTL de intel).
- **Teste futuro:** mapas com oclusão forte e telemetria de falsos positivos de callout.

### F-011
- **ID:** F-011
- **Título:** HUD HTML sem escaping de strings externas (voz/LLM)
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/TacticalHudRenderer.cs:L144-L150]`, `[src/CsBotManager/OllamaIglService.cs:L218-L222]`
- **Classe/método:** `BuildChipHudHtml`, parsing de plano
- **Trecho mínimo:** interpolação direta de `LastVoiceCommand`, `TacticName`, `TacticSummary` no HTML.
- **Fluxo:** voz/LLM -> plano/texto -> HUD center html.
- **Esperado:** encode HTML antes de render.
- **Implementado:** string crua.
- **Impacto:** forja visual/layout break na HUD.
- **Cenário:** comando de voz com marcação HTML.
- **Risco:** integridade de UI.
- **Dependência externa:** entrada de voz/LLM.
- **Confiança:** Alto.
- **Recomendação:** `HtmlEncode`/sanitização.
- **Teste futuro:** payload com tags e validação de escape.

### F-012
- **ID:** F-012
- **Título:** Validação incompleta de handles/entidades em loops de inventário e callbacks
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/CtRetakeAndDefuseBrain.cs:L320-L324]`, `[src/CsBotManager/TacticalCalloutSystem.cs:L428-L433]`, `[src/CsBotManager/TacticalCalloutSystem.cs:L217-L233]`, `[src/CsBotManager/MobilityController.cs:L176-L179]`
- **Classe/método:** `HasSmokeGrenade`, `HasC4Equipped`, callback de morte, `EquipCombatWeapon`
- **Trecho mínimo:** leitura de `DesignerName` sem `IsValid` em alguns loops; callback tardio usa `killer` sem revalidar tudo.
- **Fluxo:** eventos + timers + inventário.
- **Esperado:** validações defensivas completas dentro do callback, não só antes.
- **Implementado:** validação parcial.
- **Impacto:** risco de null/ref/estado inválido em bordas.
- **Cenário:** morte/disconnect entre captura e execução de timer.
- **Risco:** exceções e comportamento indefinido.
- **Dependência externa:** lifecycle de entidades da engine.
- **Confiança:** Médio-Alto.
- **Recomendação:** padrão único `IsValid` no ponto de uso.
- **Teste futuro:** cenários de disconnect/morte durante timers.

### F-014
- **ID:** F-014
- **Título:** Inconsistências documentais e referências a artefatos ausentes
- **Severidade:** 🟡 OTIMIZAÇÃO E POLIMENTO
- **Classificação:** COMPROVADO POR ARTEFATO DISPONÍVEL
- **Arquivo/linhas:** `[docs/CHECKLIST_TESTES_FASE3.md:L14]`, `[docs/CHECKLIST_TESTE_COMPLETO_JOGO.md:L21,L119]`, `[docs/GUIA_PROJETO_CSBOT.md:L187,L207]`
- **Classe/método:** documentação
- **Trecho mínimo:** menção a `iniciar_servidor.bat` e `arsenal_web/app.py` fora desta cópia.
- **Fluxo:** docs não refletem exatamente o clone atual.
- **Esperado:** docs com distinção clara entre artefato versionado e ambiente externo.
- **Implementado:** mistura de paths locais históricos.
- **Impacto:** ruído de operação e troubleshooting.
- **Cenário:** novo mantenedor seguindo checklist literalmente.
- **Risco:** erros de setup e diagnóstico incorreto.
- **Dependência externa:** repositório/infra original.
- **Confiança:** Alto.
- **Recomendação:** revisão documental com seção “pré-requisitos externos”.
- **Teste futuro:** dry-run de onboarding por terceiro sem conhecimento prévio.

### F-015
- **ID:** F-015
- **Título:** Gate anti-duplicação de utilitárias existe, mas não é consumido pelos lançadores
- **Severidade:** 🟠 IMPORTANTE
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/UtilityAndClockCoordinator.cs:L36-L54]`, busca de uso: apenas definição
- **Classe/método:** `CanThrowUtilityAt`
- **Trecho mínimo:** método implementado sem chamadas nos pontos de throw.
- **Fluxo:** controladores chamam `ThrowUtility` diretamente.
- **Esperado:** toda decisão de throw passar pelo gate de bloqueio/renovação.
- **Implementado:** gate órfão.
- **Impacto:** possibilidade de gasto redundante de utilitárias.
- **Cenário:** sequência de controladores acionando smokes/flashes no mesmo choke.
- **Risco:** ineficiência tática/conflito de recursos.
- **Dependência externa:** dinâmica de granadas da engine.
- **Confiança:** Alto.
- **Recomendação:** centralizar “permissionamento” de throw.
- **Teste futuro:** rodada com múltiplos triggers no mesmo choke e validação de supressão.

### F-016
- **ID:** F-016
- **Título:** Estado de hold não é consumido de forma consistente com duração solicitada
- **Severidade:** 🟡 OTIMIZAÇÃO E POLIMENTO
- **Classificação:** COMPROVADO POR ANÁLISE ESTÁTICA
- **Arquivo/linhas:** `[src/CsBotManager/BotLocomotionDriver.cs:L198-L217]`, `[src/CsBotManager/BotLocomotionDriver.cs:L458-L469]`, `[src/CsBotManager/MobilityController.cs:L106-L108]`
- **Classe/método:** `HoldPosition`, `UpdateTick`, `MobilityController.UpdateTick`
- **Trecho mínimo:** `HoldDurationRemaining` é setado, mas `WaitTimer` de stance sobrescreve continuamente para 2.5s/1.0s.
- **Fluxo:** ação de hold -> loop de locomotion -> override de wait por stance.
- **Esperado:** semântica de hold temporal determinística.
- **Implementado:** semântica parcialmente abstrata.
- **Impacto:** decisão de mobilidade pode usar sinal não representativo.
- **Cenário:** combinações repetidas de HIDE_COVER/JIGGLE/HOLD.
- **Risco:** comportamento errático leve.
- **Dependência externa:** timing da engine.
- **Confiança:** Médio.
- **Recomendação:** consolidar “state machine” de hold vs stance.
- **Teste futuro:** telemetria de duração real de hold por slot.

---

## 13. Achados adicionais fora dos critérios

1. `MapProfiles/de_dust2.json` e `de_inferno.json` contêm `fallback_spot_id` que referenciam IDs não presentes no mesmo arquivo (ex.: `ct_d2_spawn`, `tr_d2_spawn`, `ct_inf_spawn`, `tr_inf_spawn`).  
   - Evidência: `[src/CsBotManager/MapProfiles/de_dust2.json:L111,L126,L156,L171]`, `[src/CsBotManager/MapProfiles/de_inferno.json:L96,L111,L126]`.
2. `TacticalSpots_de_mirage.json` é duplicata exata de `MapProfiles/de_mirage.json::spots` (35 entradas), criando risco de drift.
3. Telemetria de round start passa `rawIglJson` vazio (`string.Empty`), reduzindo auditabilidade do output do LLM: `[src/CsBotManager/CsBotManagerPlugin.cs:L339-L347]`.
4. `HandleFootstep` registra sempre `isEnemy: true`, independente de perspectiva de equipe, potencializando ruído de heurística: `[src/CsBotManager/TacticalCalloutSystem.cs:L299-L301]`.

---

## 14. Problemas comprovados estaticamente

- F-001, F-002, F-003, F-005, F-006, F-007, F-008, F-009, F-011, F-012, F-015, F-016.

---

## 15. Problemas inferidos que exigem confirmação

- F-004 (race efetivo em `MapProfileManager` depende de interleaving real).
- Efeito exato de `GiveNamedItem` em cenários extremos de inventário (depende da semântica runtime da Source 2).
- Interferência de plugins externos (`BotAI/BotControllerImpl`) sobre `GoalPosition`/inputs no tick seguinte.

---

## 16. Itens não verificáveis nesta máquina

- Runtime de Source 2 dedicado e validação de mecânica física completa de plant/defuse/throw sob carga real.
- Comportamento real do modelo `qwen2.5:3b` (prompt adherence e payload malformed em produção).
- Arsenal Web e schema/banco (`arsenal_web` ausente; sem MariaDB read-only conectado).
- Compatibilidade de versão exata das DLLs externas referenciadas em `H:`.

---

## 17. Riscos de crash nativo

Classificação (estática):
- **Médio-Alto:** callbacks/timers tardios sobre entidades que podem ter mudado de validade (F-012).
- **Médio:** possível race de leitura/escrita de perfil em fluxo assíncrono (F-004).
- **Médio:** concorrência de ordens e timers órfãos produzindo estados inconsistentes em entidades ativas (F-006/F-007).

Observação: crash nativo definitivo depende de runtime engine e integrações externas.

---

## 18. Riscos de conflito de estado

- **Alto:** plano obsoleto de IA aplicando em round posterior (F-001/F-002/F-003).
- **Alto:** mismatch save/defuse no plant (F-005).
- **Alto:** múltiplos controladores escrevendo mesmos recursos sem ownership central (F-006/F-007/F-015).
- **Alto:** inventário/C4 com grants diretos e remoções parciais (F-008).

---

## 19. Riscos de performance

Sem profiling em ms (não executado). Análise por complexidade/frequência:
- `OnTick` em 64 Hz chama scans de jogadores em múltiplos módulos (`Utilities.GetPlayers`) e diversas LINQ/lambdas.
- Callouts/combat/mobility executam filtros por jogador em alta frequência.
- HUD: renderização final é cacheada a 1Hz (ponto positivo), mas há interpolações frequentes quando recompõe.
- Telemetria periódica a cada ~3s durante round ativo (`RecordPeriodicSnapshot`) adiciona overhead controlado.

Risco predominante: **stutter/GC moderado** sob servidor cheio, especialmente com múltiplos timers/eventos simultâneos.

---

## 20. Riscos da integração com o Ollama

- Aplicação de resposta em round errado (F-001).
- Corrida de respostas sem ordenação (F-002).
- Sem cancelamento/limite de concorrência (F-003).
- Parsing assume JSON em `response` com validação parcial sem trilha `rawIglJson` persistida (achado adicional).
- Segurança de prompt: entradas de voz/call podem influenciar texto; há fallback determinístico, porém não há sandbox semântico forte por request id.

Classificação geral: **🟠 Importante a 🔴 Crítico** para integridade de controle tático.

---

## 21. Riscos da Arsenal Web, se presente

**NÃO VERIFICÁVEL: DIRETÓRIO NÃO PRESENTE NESTA CÓPIA DO REPOSITÓRIO.**

Sem `arsenal_web/` e sem banco read-only disponível, não foi possível auditar:
- SQL injection/parametrização
- auth/authz por SteamID
- schema (`wp_player_skins`, `wp_player_knife`, `wp_player_gloves`)
- CSRF/secret/debug mode

Classificação exigida:
- Schema: **NÃO VERIFICÁVEL SEM O BANCO ORIGINAL**
- Código web: **NÃO VERIFICÁVEL NESTA CÓPIA DO REPOSITÓRIO**

---

## 22. Plano de Execução Definitivo (8 Blocos Cirúrgicos de Implementação)

### Bloco 1: Correção de Passos Aliados e Percepção Legítima Sem "Wallhack por Raio" (`F-009` e `Seção 13.4`)
1. **Filtro de Time em `HandleFootstep` (`TacticalCalloutSystem.cs`):** verificar obrigatoriamente se quem emitiu o passo pertence ao time adversário (`stepper.Team != listenerBot.Team`). Jamais registrar passos de aliados como `isEnemy: true`.
2. **Helper Central de Percepção Legítima (`CanBotPerceiveEnemy`):** implementar validação centralizada para `TacticalCalloutSystem`, `SiteClearAndPlantController` e `CombatAdapter`:
   - Um bot só percebe um inimigo se:
     a) O inimigo estiver dentro do cone de visão (FOV ~95° a partir do `EyeAngles` do bot), sem smoke ativa bloqueando o segmento entre ambos e com `SpottedByMask` / linha geométrica válida; **OU**
     b) O inimigo tiver emitido som audível (`Footstep`, `WeaponFire`, dano) naquele setor nos últimos `4.0 segundos`.
   - Substituir checagens cegas de distância global (`Utilities.GetPlayers()` + raio puro) por esse método.

### Bloco 2: Ativação Real do Gate Anti-Dupla Smoke (`F-015`)
- Conectar `UtilityAndClockCoordinator.CanThrowUtilityAt` e o registro de bloqueio de chokepoint diretamente no fluxo de arremesso (`BotLocomotionDriver.ThrowUtility` e controladores de utilitárias), garantindo que dois bots não joguem Smoke/Molotov repetida no mesmo chokepoint enquanto ele já estiver bloqueado.

### Bloco 3: Sincronia Imediata do Save CT com o Guard de Defuse (`F-005`)
- Em `CsBotManagerPlugin.cs` (`OnBombPlanted`), executar `_locomotionDriver.NotifyBombState(..., _currentPlan.IsTacticalSaveActive)` **após** `_midRoundAdapter.HandleBombPlanted(...)` definir se o time entrou em `SAVE TÁTICO`.
- Atualizar `NotifyBombState` sempre que `IsTacticalSaveActive` mudar para `true` no `MidRoundAdapter` ou `UtilityAndClockCoordinator`.
- Garantir que `IsTacticalSaveActive == true` bloqueie imediatamente qualquer tentativa de defuse ou corrida para a C4.

### Bloco 4: Hierarquia Leve de Prioridade e Cancelamento Atômico no `BotLocomotionDriver` (`F-007` e `F-016`)
1. **Cancelamento de `ActiveMovementId` (`F-007`):** em `NavigateToSpot`, `NavigateToPosition` e `HoldPosition`, antes de sobrescrever `_botStates[slot]`, verificar `ActiveMovementId != 0` no estado anterior e cancelar imediatamente na `BotControllerApi`.
2. **Semântica Real de `HoldDurationRemaining` (`F-016`):** respeitar `HoldDurationRemaining` no `UpdateTick` sem sobrescrita indevida pelo `WaitTimer` da stance.
3. **Prioridade de Ordem Enxuta (`BotOrderPriority`):** adicionar enum no `BotLocomotionDriver`:
   - `Low_Default = 10`
   - `Medium_Tactical = 30`
   - `High_CombatFallback = 50`
   - `Critical_SaveOrPivot = 80`
   - `Absolute_PlantOrDefuse = 100`

   e bloquear trocas para faca no `MobilityController` quando prioridade `>= High_CombatFallback`.

### Bloco 5: Guard de Round/Sequência do Ollama, Lock de Perfil e Registry de Timers por Round (`F-001`, `F-002`, `F-003`, `F-004`, `F-006`)
1. **Sequenciamento e cancelamento do Ollama (`F-001`, `F-002`, `F-003`):**
   - adicionar `_iglRequestSequence` monotônico e `CancellationTokenSource` por round em `CsBotManagerPlugin.cs` (cancelado em `OnRoundEnd` e `Unload`);
   - no callback `Server.NextFrame`, validar `if (capturedRound != _currentRound || requestSeq != _iglRequestSequence) return;` antes de aplicar `_currentPlan`.
2. **Thread-safety em `MapProfileManager` (`F-004`):** proteger leitura/escrita de `_spotsById` com `lock (_profileLock)`.
3. **Rastreamento central de timers de round (`F-006`):** criar helper `AddRoundTimer(float delay, Action callback)` no plugin para registrar timers do round (incluindo encadeados/aninhados de `CtDefenseController`, `MidRoundAdapter`, `PacingAndFallbackController`, `TrMacroPivotController` e `CtRetakeAndDefuseBrain`) em `_activeRoundTimers`, com `Kill()` global em `OnRoundEnd` e `OnRoundStart`.

### Bloco 6: Invariantes de Inventário e C4 Única (`F-008`)
- Em `EconomyManager.cs` (`DropWeaponForPlayer`, `TryCoordinateTeamAwpDrop`, `EnforceC4Discipline`, `PerformPostRoundLooting`):
  - implementar remoção segura por slot (`RemoveWeaponInSlot`) com validação `IsValid` antes de conceder nova primária;
  - em `EnforceC4Discipline`, conceder `weapon_c4` ao `Rotator` apenas após confirmar remoção física da C4 do portador anterior, garantindo invariante de **1 única C4**;
  - em `PerformPostRoundLooting`, remover entidade da arma no chão (`groundWeapon.Remove()`) e remover arma inferior antiga do bot antes de equipar arma coletada.

### Bloco 7: Escape HTML no HUD e Validação Defensiva de Entidades (`F-011` e `F-012`)
- Aplicar `System.Net.WebUtility.HtmlEncode(...)` em textos dinâmicos (`TacticName`, `TacticSummary`, `LastVoiceCommand`) em `TacticalHudRenderer.cs` (`F-011`).
- Garantir validação `IsValid` no ponto exato de uso dentro de loops de armas e callbacks tardios mapeados em `F-012` (`CtRetakeAndDefuseBrain`, `TacticalCalloutSystem`, `MobilityController`).

### Bloco 8: Correção dos JSONs (`de_dust2` / `de_inferno`), Limpeza de Legado e Log do `rawIglJson` (`Seção 13.1`, `13.2`, `13.3`)
1. Corrigir `fallback_spot_id` órfãos em `MapProfiles/de_dust2.json` (`ct_d2_spawn`, `tr_d2_spawn`) e `MapProfiles/de_inferno.json` (`ct_inf_spawn`, `tr_inf_spawn`), cadastrando spots ou apontando para IDs válidos do mesmo arquivo.
2. Remover arquivo legado duplicado `src/CsBotManager/TacticalSpots_de_mirage.json`, mantendo `MapProfiles/de_mirage.json` como fonte única.
3. Em `CsBotManagerPlugin.cs`, armazenar e repassar o `rawIglJson` real retornado pelo `OllamaIglService` para o `MatchTelemetryLogger.OnRoundStart` (substituindo `string.Empty`).

### Critério de aceite do plano definitivo

A próxima etapa de implementação deve seguir exclusivamente os 8 blocos acima, mantendo o foco em correções cirúrgicas e evitando reescritas arquiteturais amplas.

---

## 23. Checklist de testes futuros no servidor original

1. **Round stale guard IA:** atrasar resposta do Ollama para chegar no round seguinte e confirmar descarte.
2. **Race de requests:** disparar `!tatica`/`!rejeitar` em burst e confirmar ordenação correta.
3. **Cancelamento:** encerrar round/mapa durante request em voo e validar que callback não aplica plano.
4. **Save CT vs defuse:** cenário 2x4 pós-plant para verificar ausência de `IN_USE` quando save ativo.
5. **Inventory invariants:** bateria de doações/AWP/C4/looting com asserts de consistência.
6. **Timers órfãos:** finalizar round durante fake/duo/execute e confirmar zero callback residual.
7. **Percepção legítima:** validar callouts com inimigos ocultos por parede/smoke.
8. **HUD sanitization:** inserir payload com tags via voz e confirmar neutralização.
9. **Stress 64 Hz:** medir impacto de scans/linq/timers em partidas 10 bots + eventos intensos.
10. **Convivência com plugins externos:** observar sobrescrita de `GoalPosition`/inputs entre ticks.

---

## 24. Apêndice com arquivos e comandos somente leitura utilizados

### Comandos (read-only) usados na auditoria
- `git ls-files`
- `git rev-parse --abbrev-ref HEAD && git rev-parse HEAD`
- glob recursivo de arquivos
- buscas por padrões (`Task.Run`, `AddTimer`, `RegisterEventHandler`, `CanThrowUtilityAt`, referências de docs)
- leituras diretas de arquivos (`Read`) em `.cs`, `.csproj`, `.json`, `.bat`, `.md`
- verificação de duplicidade JSON Mirage por script local de leitura

### Observação
Nenhum comando de build, restore, inicialização de servidor, pull de modelo, escrita em banco ou script destrutivo foi executado nesta auditoria.

---

## 25. Tabela final consolidada

### 🔴 Crítico

| ID | Severidade | Componente | Arquivo e linhas | Descrição | Evidência | Impacto | Confiança | Dependência externa | Exige runtime | Prioridade |
|---|---|---|---|---|---|---|---|---|---|---|
| F-001 | 🔴 | Orquestração IA | `CsBotManagerPlugin.cs:L242-L287;L711-L785` | Plano Ollama obsoleto pode aplicar em round errado | Estática direta | Estratégia incorreta entre rounds | Alta | Ollama latência | Sim (confirmação) | P0 |
| F-005 | 🔴 | Defuse/Save sync | `CsBotManagerPlugin.cs:L538-L559`, `MidRoundAdapter.cs:L198-L237`, `BotLocomotionDriver.cs:L348-L399` | Save CT pode não sincronizar com guard de defuse | Estática direta | Bot executa retake/defuse contra call de save | Alta | Engine state | Sim | P0 |
| F-008 | 🔴 | Economia/Inventário | `EconomyManager.cs:L118-L124;L149-L153;L442-L453;L513-L537` | Grants diretos podem gerar inconsistência de arma/C4 | Estática direta | Duplicação/estado inválido de inventário | Alta | Semântica engine | Sim | P0 |

### 🟠 Importante

| ID | Severidade | Componente | Arquivo e linhas | Descrição | Evidência | Impacto | Confiança | Dependência externa | Exige runtime | Prioridade |
|---|---|---|---|---|---|---|---|---|---|---|
| F-002 | 🟠 | IA concorrente | `CsBotManagerPlugin.cs:L250-L287;L719-L785` | Sem ordenação de respostas concorrentes | Estática direta | Plano mais novo pode ser perdido | Alta | Ollama | Sim | P0 |
| F-003 | 🟠 | Lifecycle async | `OllamaIglService.cs:L43-L51`, `CsBotManagerPlugin.cs:L420-L441` | Sem cancelamento/throttle | Estática direta | Estado tardio e sobrecarga | Alta | Ollama | Sim | P0 |
| F-004 | 🟠 | Map profile threading | `MapProfileManager.cs:L11-L18;L95-L97` | Possível race leitura/escrita | Inferido | Inconsistência/exceção | Média | Scheduling | Sim | P1 |
| F-006 | 🟠 | Timers | múltiplos controladores | Timers aninhados sem cancelamento total | Estática direta | Ações tardias em fase errada | Alta | Engine timers | Sim | P1 |
| F-007 | 🟠 | Locomotion usercmd | `BotLocomotionDriver.cs:L160-L190;L476-L482` | Cancelamento de movimento pode ser perdido | Estática direta | Conflito físico de movimento | Alta | BotControllerApi | Sim | P1 |
| F-009 | 🟠 | Percepção tática | `TacticalCalloutSystem.cs`, `SiteClearAndPlantController.cs`, `CombatAdapter.cs` | Decisão por scans globais/raio | Estática direta | Conhecimento privilegiado | Alta | APIs de visão | Sim | P1 |
| F-011 | 🟠 | HUD | `TacticalHudRenderer.cs:L144-L150` | Texto externo sem escape em HTML | Estática direta | Forja visual/layout break | Alta | Voz/LLM | Sim | P1 |
| F-012 | 🟠 | Validação entidades | `CtRetakeAndDefuseBrain.cs:L320-L324`, etc. | Checks de validade incompletos | Estática direta | null/invalid handle em bordas | Médio-Alto | Engine lifecycle | Sim | P1 |
| F-015 | 🟠 | Utilidades | `UtilityAndClockCoordinator.cs:L36-L54` | Gate anti-duplicação não utilizado | Estática direta | Gasto redundante de util | Alta | Dinâmica round | Sim | P2 |

### 🟡 Otimização e polimento

| ID | Severidade | Componente | Arquivo e linhas | Descrição | Evidência | Impacto | Confiança | Dependência externa | Exige runtime | Prioridade |
|---|---|---|---|---|---|---|---|---|---|---|
| F-014 | 🟡 | Documentação | `docs/*.md` | Inconsistências e referências ausentes | Artefato | Ruído operacional | Alta | Repositório externo | Não | P3 |
| F-016 | 🟡 | Hold semantics | `BotLocomotionDriver.cs` | Duração de hold inconsistente | Estática direta | Comportamento tático menos previsível | Média | Timing engine | Sim | P3 |

---

### Conclusão

A auditoria extraiu evidência estática robusta do conteúdo versionado e separou defeitos comprováveis de hipóteses dependentes de runtime externo. O próximo passo recomendado é executar o checklist de validação no servidor original, priorizando os itens P0/P1.

---

# BÔNUS — Como evoluir os bots para uma experiência competitiva e orgânica

A evolução propositiva foi consolidada no **Plano de Execução Definitivo da Seção 22**.

Para manter foco e evitar dispersão, este documento passa a adotar como trilha oficial apenas os 8 blocos cirúrgicos, com a seguinte progressão prática:

1. **Estabilidade e integridade tática**: Blocos 3, 4, 5 e 6.
2. **Percepção legítima e utilitárias inteligentes**: Blocos 1 e 2.
3. **Qualidade de interface e robustez defensiva**: Bloco 7.
4. **Consistência de dados e telemetria forense**: Bloco 8.

## Critérios objetivos de sucesso (competitivo + orgânico)

- Queda de callouts falsos por leitura indevida de aliados/raio puro.
- Zero aplicação de plano de round antigo após troca de round.
- Zero conflito persistente de movimento órfão (`ActiveMovementId`) após troca de ordem.
- Invariante estrita de inventário: 1 C4 no lado TR e ausência de duplicação de primária por bot.
- Redução de utilitárias redundantes no mesmo chokepoint.
- Melhoria percebida de coordenação de time (trades, saves, retakes e rotações mais coerentes).

Em resumo: a experiência “mais competitiva e orgânica” será medida por **comportamento consistente em partida real**, não por aumento de complexidade arquitetural.

