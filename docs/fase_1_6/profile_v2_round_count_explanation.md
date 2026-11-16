# Esclarecimento Técnico da Contagem de Rounds (Fase 1.6.3)

> [!NOTE]
> Auditoria da arquitetura de captura de telemetria entre Warmup e Rounds Oficiais no CounterStrikeSharp / CS2.

## 1. Dados Canônicos da Execução

| Variável | Valor Registrado | Descrição Técnica |
| :--- | :--- | :--- |
| **WarmupCaptured** | `1` | 1 seção de Warmup executada e capturada na inicialização do servidor dedicado |
| **OfficialRoundsRequested** | `5` | Valor configurado em `auto_debug.flag = 5` |
| **OfficialRoundsCompleted** | `5` | 5 rounds oficiais competitivos completos (Rounds 1 a 5) |
| **TotalCapturedSections** | `6` | 1 Warmup + 5 Rounds Oficiais = 6 seções agregadas no ciclo do servidor |
| **CaptureEndReason** | `MATCH_COMPLETED` | Encerramento automático via flag ao selar o 5º round oficial |

---

## 2. Por que o arquivo `debug_match_20261104_221312.md` registra 5 e não 6 rounds?

1. **Ciclo de Reinicialização do CS2 no Warmup End**:
   - Ao iniciar o servidor com `ai_competitive.cfg`, o CS2 entra inicialmente em modo de aquecimento (`Warmup`).
   - Em `CsBotManagerPlugin.cs`, o watchdog de auto-debug detecta `isWarmup && File.Exists(autoDebugFlag)` e programa a execução de `mp_warmup_end; mp_freezetime 2;` após 4 segundos.
   - No motor Source 2, o comando `mp_warmup_end` encerra o aquecimento reiniciando a sessão de jogo (`CGameSystem::BuildGameSessionManifest`).

2. **Divisão de Arquivos de Telemetria**:
   - O encerramento do aquecimento provocou o descarregamento da sessão pré-jogo do plugin, gravada em `H:\CS2_AI_Server\debug_logs\debug_match_20261104_221143.md` (que encerrou com `capture_end_reason: PLUGIN_UNLOAD` e `captured_rounds: 3` de testes prévios/warmup).
   - Imediatamente após o reinício, o CounterStrikeSharp inicializou uma nova sessão limpa de partida em `H:\CS2_AI_Server\debug_logs\debug_match_20261104_221312.md`.

3. **Execução Estrita dos 5 Rounds Oficiais**:
   - Nesta nova sessão, o jogo já iniciou direto no **Round Oficial 1** (Live), sem passar por novo warmup.
   - Foram jogados de ponta a ponta os rounds oficiais 1, 2, 3, 4 e 5.
   - Ao selar o round 5, `_debugRoundsSealed` atingiu 5 (`_debugRoundsSealed >= _debugTargetRounds`), invocando `_telemetryLogger.CloseCapture(CaptureEndReason.MATCH_COMPLETED)`.
   - O buffer do histórico daquela sessão continha estritamente os **5 rounds oficiais selados**, gerando:
     ```markdown
     - capture_end_reason: MATCH_COMPLETED
     - captured_rounds: 5 | complete_rounds: 5 | partial_round_id: none
     ```

4. **Conclusão Forense**:
   - A contagem de 5 rounds no arquivo ativo é **100% correta e fidedigna** ao ciclo de vida da sessão.
   - Somando a seção de Warmup inicial (executada no primeiro arquivo) com os 5 rounds oficiais (no segundo arquivo), o servidor executou exatamente **6 seções completas**.
   - Os logs históricos permanecem estritamente preservados sem qualquer alteração sintética.
