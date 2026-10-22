# RELATÓRIO DE AUDITORIA FORENSE TÉCNICA V3 — CsBotManager

Data: 2026-10-21  
Escopo auditado: `src/CsBotManager/*.cs`, `tools/mlmove_pipeline/*.py` e pasta raiz de execução `F:\CS2_MLMove_Pipeline`.

---

## Premissas desta auditoria

- Auditoria estática e forense, focada em **falha real**, **risco de crash**, **corrida de estado**, **leak**, **lock de arquivo** e **desincronia tensorial**.
- Não foi usada confiança em nome de método/comentário.
- Onde aplicável, os achados trazem evidência com arquivo/linha.

---

## Achados estruturais imediatos (antes dos vetores)

1. **Código morto no bootstrap de ONNX no plugin**  
   Em `Load`, existe chamada nula antes da instanciação:
   - `src/CsBotManager/CsBotManagerPlugin.cs:112`
   - `_microMoveEngine?.TryLoadMapModel(Server.MapName);`  
   Nessa linha, `_microMoveEngine` ainda não foi criado (`new MicroMoveEngine(...)` só ocorre em `:130`).

2. **Pasta de produção F: incompleta para execução real do pipeline**  
   Em `F:\CS2_MLMove_Pipeline`, só há:
   - `minerar_e_treinar.bat`
   - `treinar_lote_demos.bat`
   - `checkpoints/mlmove_de_mirage_best.pt`
   - `checkpoints/mlmove_de_mirage_staging.onnx` (**0 bytes**)
   - `extracted_tensors/de_mirage/bootstrap_de_mirage_16hz.npz`
   - `raw_demos/de_mirage` vazio

   Não há scripts Python de pipeline nessa raiz (`run_mining_and_training_loop.py`, `extract_16hz_tensors.py`, etc.).

3. **Scripts BAT da pasta F: com caminhos inválidos/hardcoded**
   - `F:\CS2_MLMove_Pipeline\minerar_e_treinar.bat:21` aponta para `D:\CS2_MLMove_Pipeline\venv\Scripts\python.exe`.
   - `F:\CS2_MLMove_Pipeline\minerar_e_treinar.bat:34` chama `run_mining_and_training_loop.py` no diretório local, mas o arquivo não existe na pasta F.
   - `F:\CS2_MLMove_Pipeline\treinar_lote_demos.bat:12` hardcoded para `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\tools\mlmove_pipeline`.

---

# Vetor 1 — Resolução física dos 7 bugs de gameplay

## 1.1 Moonwalk (desacoplamento LookAtSpot)

### Evidência
- `src/CsBotManager/BotLocomotionDriver.cs:660-667`

### Achado
O desacoplamento de `LookAtSpot` em trânsito (`distSq > 85²`) só ocorre sob `if (!bot.IsEnemyVisible)`.  
Se houver visibilidade de inimigo, a limpeza não ocorre — e o `LookAtSpot` prévio pode permanecer.

### Risco
**Comportamento residual de corrida “de costas”/travada de cabeça** em transições de estado sob contato visual.

---

## 1.2 Pulo para trás / hold real / limpeza de IN_JUMP

### Evidências
- Injeção de pulo no unstuck: `src/CsBotManager/BotLocomotionDriver.cs:636`
- IN_JUMP em micro engine: `src/CsBotManager/MicroMoveEngine.cs:103`
- Não há rotina explícita de “clear IN_JUMP” em hold/save.

### Achado
A limpeza explícita da flag `IN_JUMP` não existe como passo dedicado quando entra em `IsHoldingSpot`, `IsStopping` ou `SAVE`.  
O fluxo depende de duração de pulso/injeção e sobrescritas indiretas.

### Risco
**Comportamento residual intermitente** (saltos curtos/arrasto após transição para hold/save), especialmente quando unstuck + micro movimento ocorrem próximos.

---

## 1.3 Hold pixel vs arrasto por BotAI/micro

### Evidências
- Hold força `IsStopping` + `WaitTimer`: `src/CsBotManager/BotLocomotionDriver.cs:439-447`
- MicroMove update roda antes da lógica de nav/hold: `src/CsBotManager/BotLocomotionDriver.cs:410-412`

### Achado
`MicroMoveEngine.UpdateTick(...)` executa antes da semântica de hold no `BotLocomotionDriver`.  
Não existe exclusão rígida por `IsHoldingSpot` no micro engine antes de injetar movimento.

### Risco
**Hold não determinístico**: bot recebe comando de micro movimento no mesmo frame de estado de trava.

---

## 1.4 Animação de granadas em ThrowUtility

### Evidências
- Troca + delay fixo + ataque: `src/CsBotManager/BotLocomotionDriver.cs:879-889`

### Achado
O fluxo não valida:
1. se `SwitchBotWeapon` realmente equipou granada;
2. se deploy terminou;
3. se o ataque ocorreu com a arma correta.

### Risco
**Animação/execução artificial e falhas silenciosas** (arremesso não sair ou sair inconsistido em timing real).

---

## 1.5 COMBAT_THREAT_FOCUS (death/hurt)

### Evidências
- Trigger só em death: `src/CsBotManager/CsBotManagerPlugin.cs:640-644`
- `OnPlayerHurt` não chama `AlertNearbyTeammatesOfThreat`.

### Achado
A lógica de ameaça imediata não cobre `OnPlayerHurt` para foco espacial no agressor (só `OnPlayerDeath`).

### Risco
**Resposta tardia de trade/foco** em trocas onde ainda não houve abate.

---

# Vetor 2 — Integridade de estado e economia (5 bugs de log)

## 2.1 Bloqueio da XM1014 (frame 0)

### Evidências
- Sanitização em 0.05s: `src/CsBotManager/CsBotManagerPlugin.cs:268-273`
- Nova sanitização em 0.3s: `src/CsBotManager/CsBotManagerPlugin.cs:291-293`
- Reembolso/remoção: `src/CsBotManager/EconomyManager.cs:29-57`

### Achado
Existe bloqueio e reembolso, mas:
- é baseado em inspeção de inventário em janelas temporais fixas (0.05 e 0.3);
- sem trilha de idempotência por origem da arma.

### Risco
**Lacuna temporal** para compras/trocas fora da janela e **reembolso indevido** em cenários não previstos.

---

## 2.2 Destravamento no plant (OnBombPlanted)

### Evidências
- Limpeza de hold/state: `src/CsBotManager/BotLocomotionDriver.cs:104-119`
- Limpeza de stop/timers nativos: `src/CsBotManager/BotLocomotionDriver.cs:128-133`
- Ordem crítica de pivot: `src/CsBotManager/BotLocomotionDriver.cs:145`

### Achado
O desbloqueio foi implementado e há uso de `Critical_SaveOrPivot`.  
**Ponto residual**: somente bots em `_botStates` recebem reset de navegação detalhado; bots fora do dicionário dependem do estado nativo naquele instante.

### Risco
**Destravamento parcial** em cenários onde bot não estava rastreado no estado local.

---

## 2.3 Stuck detector (PositionDelta)

### Evidências
- Cálculo e persistência: `src/CsBotManager/BotLocomotionDriver.cs:607-654`
- Unstuck com jump+strafe: `src/CsBotManager/BotLocomotionDriver.cs:636-639`

### Achado
Não foi encontrado `NullReference` óbvio no cálculo de `PositionDelta`.  
Porém, o fluxo de unstuck injeta movimento e **não usa barreira de ownership** com outros controladores/micro engine.

### Risco
**Conflito de injeção**: correção de stuck disputa comando com nav/micro e pode virar comportamento oscilatório.

---

## 2.4 Bug do 5º bot / arquétipos multi-time

### Evidências
- Atribuição de papéis: `src/CsBotManager/RoleManager.cs:27-42`
- Chamada para CT e TR: `src/CsBotManager/CsBotManagerPlugin.cs:295-296`

### Achado
Atribuição depende da ordem de `List<CCSPlayerController>` recebida (não há ordenação explícita por slot).  
Se houver entrada inválida no índice inicial, o `continue` preserva incremento de índice e pode deslocar o ciclo, deixando time sem AWPer naquela rodada.

### Risco
**Distribuição de função inconsistente** (residual do problema do “bot sem arquétipo”).

---

# Vetor 3 — Estabilidade ONNX em runtime C# (MicroMoveEngine)

## 3.1 Memory leak / recurso não descartado

### Evidências
- `FileSystemWatcher` criado: `src/CsBotManager/MicroMoveEngine.cs:296-303`
- Sem `Dispose` no unload do plugin (`CsBotManagerPlugin.Unload` não descarta `_microMoveEngine`).
- `InferenceSession` só é descartada no swap, não no ciclo final de vida do plugin.

### Achado
Há **vazamento de recursos por lifecycle** (watcher/session) em hot reloads/reloads de plugin.

### Risco
🔴 **Risco de leak cumulativo** e handlers duplicados após recargas.

---

## 3.2 File lock / hot-swap

### Evidências
- Reload com debounce fixo 1200ms: `src/CsBotManager/MicroMoveEngine.cs:314`
- Carga de bytes em leitura compartilhada: `src/CsBotManager/MicroMoveEngine.cs:359-370`
- Em erro, desativa ONNX: `src/CsBotManager/MicroMoveEngine.cs:405-407`

### Achado
Não existe política real de retry/backoff por arquivo parcialmente escrito.  
Se a leitura ocorrer durante escrita, o parse pode falhar e o motor cai para fallback, sem garantia de recuperação imediata.

### Risco
🔴 **Risco de crash lógico/queda de backend neural** no momento de atualização do modelo.

---

## 3.3 Corrida entre UpdateTick e swap

### Evidências
- Locks em inferência e swap: `src/CsBotManager/MicroMoveEngine.cs:418`, `:382`

### Achado
Há lock de exclusão mútua para sessão ONNX. Corrida crítica de ponteiro da sessão está mitigada.

### Risco residual
Baixo para ponteiro; médio para latência/pausa durante swap.

---

## 3.4 Mapeamento logits -> ActionId -> UserCmd

### Evidências
- Parse por “primeira saída”: `src/CsBotManager/MicroMoveEngine.cs:449`
- Nome de output não utilizado na leitura, apesar de constante existir.

### Achado
A saída ONNX é lida por posição (`FirstOrDefault`) e não por nome (`output_logits`).  
Se ordem de outputs mudar, o parse pode consumir tensor errado sem erro de compilação.

### Risco
🟠 **Tensor mismatch silencioso**.

---

# Vetor 4 — Integridade Python e treinamento (`tools/mlmove_pipeline`)

## 4.1 Contrato C# vs Python (Fog of War e normalização)

### Evidências de desincronia

1. **Percepção divergente**
   - C#: `TacticalCalloutSystem.CanBotPerceiveEnemy` usa FOV ~95°, `SpottedByMask`, adjacência setorial e bloqueio por smoke (`src/CsBotManager/TacticalCalloutSystem.cs:56-133`).
   - Python: `can_team_perceive_enemy_2d` usa heurística própria por distância/ângulo/velocidade (`tools/mlmove_pipeline/contract_spec.py:118-154`).

2. **Features dinâmicas congeladas no extractor**
   - `round_time_remaining=75.0`, `has_c4=False`, `is_bomb_planted=False` fixos na extração (`tools/mlmove_pipeline/extract_16hz_tensors.py:210-213`).
   - No C#, esses campos são reais por tick (`src/CsBotManager/MicroMoveEngine.cs:753-755`, `:829`).

3. **Papel tático sintético**
   - `role_cycle` fixo (`tools/mlmove_pipeline/extract_16hz_tensors.py:105`).
   - C# usa `RoleManager` por slot/round (`src/CsBotManager/MicroMoveEngine.cs:819-827`).

### Conclusão
🟠 **Desincronia tensorial material** entre treino e inferência online.

---

## 4.2 PBDEMS2 e OOM

### Evidências
- Validação PBDEMS2 existe no miner (`tools/mlmove_pipeline/real_demo_miner.py:86-112`) e no loop batch (`run_mining_and_training_loop.py:140`).
- **Não existe** validação em `extract_16hz_tensors.py` quando usado standalone.
- `parse_ticks` carrega tabela inteira por demo sem chunking (`extract_16hz_tensors.py:70`) e sem rotina explícita de liberação/GC entre arquivos.

### Risco
🔴 Em lote grande, **risco de OOM** por retenção/fragmentação durante parse de múltiplas demos extensas.

---

## 4.3 DirectML AdamW

### Evidência
- Implementação sem `lerp_` e com `mul_ + add_`: `tools/mlmove_pipeline/train_and_export_onnx.py:89-90`.

### Avaliação
A correção para evitar fallback clássico de `aten::lerp` está implementada.

---

## 4.4 Shapes ONNX e nomes I/O

### Evidências
- Export com `input_state`/`output_logits`: `tools/mlmove_pipeline/train_and_export_onnx.py:157-158`
- C# espera os mesmos nomes: `src/CsBotManager/MicroMoveEngine.cs:207-208`

### Avaliação
Nomes estão alinhados entre export e consumo.

---

## 4.5 Bugs críticos de pipeline (código morto/mock/erro fatal)

### 4.5.1 `DEFAULT_BASE_DIR` indefinido (erro fatal)
- `tools/mlmove_pipeline/run_mining_and_training_loop.py:186`, `:298`, `:379` usa `DEFAULT_BASE_DIR`.
- Esse símbolo não é definido nem importado no arquivo.

**Impacto:** script pode quebrar no load do módulo (NameError).

### 4.5.2 Configuração de `base_dir` parcialmente mock
- O loop recebe `base_dir`, mas funções centrais usam constantes globais D:\ (`load_dataset_for_map` usa `EXTRACTED_TENSORS_DIR_D`) em `tools/mlmove_pipeline/train_and_export_onnx.py:117-123`.

**Impacto:** trocar base para F:\ não migra de fato todo o pipeline.

### 4.5.3 Código morto em métrica
- `tools/mlmove_pipeline/run_mining_and_training_loop.py:105-106` tem chave duplicada `h2_top1`; uma sobrescreve a outra.
- Linha `:105` contém expressão artificial com `if False`.

**Impacto:** ruído lógico, manutenção insegura e sinal de trecho não revisado.

---

# Vetor 5 — Tabela de vulnerabilidades críticas (priorizada)

| Severidade | Categoria | Achado | Evidência | Impacto |
|---|---|---|---|---|
| 🔴 | Crash/OOM | `DEFAULT_BASE_DIR` indefinido em `run_mining_and_training_loop.py` | `tools/mlmove_pipeline/run_mining_and_training_loop.py:186,298,379` | Pipeline de treino/mineração pode nem iniciar |
| 🔴 | Crash/OOM | `mlmove_de_mirage_staging.onnx` com 0 bytes na pasta de produção | `F:\CS2_MLMove_Pipeline\checkpoints\mlmove_de_mirage_staging.onnx` | Artefato inválido para validação/deploy |
| 🔴 | Crash/OOM | `FileSystemWatcher`/`InferenceSession` sem descarte explícito no lifecycle | `src/CsBotManager/MicroMoveEngine.cs:296-303`, `src/CsBotManager/CsBotManagerPlugin.cs:198-207` | Leak em hot reload e potencial degradação progressiva |
| 🔴 | Crash/OOM | Extração de demos sem chunking/GC explícito em lotes grandes | `tools/mlmove_pipeline/extract_16hz_tensors.py:70-100`, `:243-257` | Risco de OOM em extração massiva |
| 🔴 | Crash/OOM | Hot-swap ONNX sem retry real para arquivo em escrita parcial | `src/CsBotManager/MicroMoveEngine.cs:314-407` | Queda para fallback neural e instabilidade de atualização |
| 🟠 | Lógica/Tensor mismatch | Fog of War/percepção Python diferente do C# | `contract_spec.py:118-154` vs `TacticalCalloutSystem.cs:56-133` | Modelo treinado com “visão” diferente da inferência real |
| 🟠 | Lógica/Tensor mismatch | Features de treino congeladas (`round_time`, `c4`, `bomb_planted`) | `extract_16hz_tensors.py:210-213` | Desalinhamento de distribuição de entrada |
| 🟠 | Lógica/Tensor mismatch | Leitura de output ONNX por posição, não por nome | `MicroMoveEngine.cs:449` | Consumo de tensor errado se ordem mudar |
| 🟠 | Lógica/Tensor mismatch | Ameaça imediata não reage a `OnPlayerHurt` | `CsBotManagerPlugin.cs:598-625` | Trade/foco atrasado em combate vivo |
| 🟠 | Lógica/Tensor mismatch | Distribuição de role dependente da ordem da lista sem sort estável | `RoleManager.cs:36-40` | Regressão de arquétipo em cenários de lista irregular |
| 🟡 | Comportamento residual | Moonwalk mitigado parcialmente (condicional por visibilidade) | `BotLocomotionDriver.cs:660-667` | Resíduo de look lock em transição |
| 🟡 | Comportamento residual | ThrowUtility sem validação de equip/deploy real | `BotLocomotionDriver.cs:879-889` | Arremesso artificial/intermitente |
| 🟡 | Comportamento residual | Código morto/duplicidade em cálculo de métricas | `run_mining_and_training_loop.py:105-106` | Telemetria de treino inconsistente |

---

## Trechos de código críticos encontrados

### A) Erro fatal de constante indefinida
```python
# tools/mlmove_pipeline/run_mining_and_training_loop.py:186
def train_incremental_batch(..., base_dir: str = DEFAULT_BASE_DIR,):
```

### B) Chave duplicada e código morto
```python
# tools/mlmove_pipeline/run_mining_and_training_loop.py:105-106
"h2_top1": (correct_top2[2] if False else correct_top1[2] / denom) * 100.0,
"h2_top1": (correct_top1[2] / denom) * 100.0,
```

### C) Chamada morta de inicialização ONNX
```csharp
// src/CsBotManager/CsBotManagerPlugin.cs:112
_microMoveEngine?.TryLoadMapModel(Server.MapName);
```

### D) Hot-swap sem backoff robusto
```csharp
// src/CsBotManager/MicroMoveEngine.cs:314
Interlocked.Exchange(ref _pendingModelReloadAtMs, Environment.TickCount64 + 1200L);
```

### E) Leitura de output ONNX por ordem, não por nome
```csharp
// src/CsBotManager/MicroMoveEngine.cs:449
var firstOutput = results.FirstOrDefault()?.AsTensor<float>();
```

---

## Auditoria específica da pasta `F:\CS2_MLMove_Pipeline`

## Estado encontrado

- `raw_demos/de_mirage`: **0 arquivos**.
- `extracted_tensors/de_mirage`: apenas `bootstrap_de_mirage_16hz.npz` (4.5 MB).
- `checkpoints/mlmove_de_mirage_staging.onnx`: **0 bytes**.
- Scripts de pipeline Python ausentes nessa raiz.

## Correções obrigatórias no host raiz

1. **Eliminar hardcode de D:\ e OneDrive nos BATs**.  
2. **Incluir scripts Python reais na própria pasta F** (ou corrigir para caminho versionado existente).  
3. **Falhar rápido se ONNX exportado tiver tamanho 0** (abort + rollback do arquivo anterior).  
4. **Padronizar `base_dir` único** (F:\) em toda cadeia Python (coletor, extrator, treino, export).  
5. **Adicionar verificação de pré-condição nos BATs**:
   - script existe;
   - venv existe no caminho correto;
   - dataset não vazio;
   - checkpoint/onnx com tamanho > limiar mínimo.

---

## Conclusão técnica (sem atenuação)

O estado atual ainda contém riscos reais de:
- **quebra de pipeline de treino** (erro fatal de variável, caminhos hardcoded inválidos);
- **inconsistência de inferência** (desincronia C# vs Python no contrato de percepção/features);
- **instabilidade de hot-swap ONNX** (sem estratégia robusta de retry/rollback);
- **vazamento de recursos em lifecycle de plugin** (watcher/session sem descarte explícito);
- **comportamento residual de gameplay** em cenários de transição (hold/micro/throw/threat focus).

A base não está em condição forense de “100% lisa” para operação contínua no host raiz F:\ sem corrigir os pontos acima.
