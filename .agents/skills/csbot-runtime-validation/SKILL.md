---
name: csbot-runtime-validation
description: Padroniza e audita o ciclo completo de validação em runtime real do servidor CS2 para o CsBot, cobrindo build, testes, deploy, verificação de hashes, captura !debug, C4, economia, Jump, recovery, spots, adaptações táticas e selamento da sessão. Use sempre para validar alterações de código C#/.NET ou modelos ONNX no servidor CS2.
---

# CsBot Runtime Validation

Esta Skill padroniza a validação em runtime real do servidor CS2 para o `CsBotManager`, garantindo conformidade com `01-evidence-before-claims`, `04-synthetic-data-labeling`, `05-human-review-integrity` e `06-sensitive-artifact-protection`.

## Proibições Explícitas e Inegociáveis

1. **Não simular runtime**: Scripts ou testes jamais podem gerar logs falsos fingindo ser telemetria `REAL` do servidor CS2.
2. **Não criar eventos fictícios**: É proibido injetar eventos sintéticos de C4, economia, jump, recovery ou spots nos logs de sessão.
3. **Não inferir zero por ausência de telemetria**: Se um subsistema não emitiu telemetria na sessão, seu status é **`N/A (UNOBSERVED_IN_SESSION)`** ou **`FAIL (MISSING_TELEMETRY)`**, nunca `"0 falhas / 100% de sucesso"`.

Consulte o contrato completo de telemetria em [runtime_telemetry_contract.md](./references/runtime_telemetry_contract.md).

## Procedimento Operacional Passo a Passo

### 1. Build, Testes, Deploy e Paridade de Hashes
1. Compile a solução e execute os testes verificando descoberta real (`total_discovered > 0`):
   ```powershell
   dotnet build CsBot.sln -c Release
   dotnet test CsBot.sln -c Release --logger "trx;LogFileName=test_results.trx"
   ```
2. Faça o deploy para o servidor CS2 e confirme que o SHA-256 (64 hex chars) de `CsBotManager.dll`, `*.onnx` e `MapProfiles/*.json` no servidor coincide com o build local.

### 2. Captura e Auditoria dos 8 Domínios em Servidor CS2 Real
Durante a sessão real no servidor CS2, capture e audite obrigatoriamente:
1. **Captura `!debug`**: Snapshots de estado, heartbeat de ticks e latência de inferência ONNX.
2. **Objetivo C4**: Transições de `BombObjectiveState`, posse do carrier, deslocamento ao bombsite, plant e defuse.
3. **Economia**: Decisão econômica por round → comando de compra emitido → confirmação real no inventário pós-compra.
4. **Jump (`ONNX Jump → JumpExecutionGate → usercmd`)**: Requisição de pulo ONNX, decisão do gate (aprovado/bloqueado) e bit `IN_JUMP` no `usercmd`.
5. **Recovery e Movimento**: Gatilho de stuck/recovery, seleção no `MovementArbitrator` e deslocamento físico efetivo ($\Delta \text{pos} > \text{threshold}$).
6. **Spots Táticos**: Atribuição, chegada e permanência nos spots definidos em `MapProfiles/*.json`.
7. **Adaptações Táticas**: Transições de papel/setor em resposta a eventos reais do round.
8. **Selamento da Partida**: Registro de hashes SHA-256 dos logs brutos e carimbo honesto (`SCRIPT_CAPTURED` vs `HUMAN_CAPTURE_IN_GAME`).

### 3. Verificação Automatizada da Sessão
Execute [verify_runtime_session.py](./scripts/verify_runtime_session.py) com os argumentos canônicos:
```powershell
python .agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py `
  --workspace-root . `
  --telemetry-log logs/cs2_runtime_session.log `
  --dll-path src/CsBotManager/bin/Release/net8.0/CsBotManager.dll `
  --output-json artifacts/runtime/runtime_validation_report.json `
  --strict
```
- **Regra de `--dry-run`**: Em modo `--dry-run` (ou sem `--telemetry-log` real), o script emite veredito **`CONDITIONAL`** com `data_nature: SIMULATED` (em respeito à Regra `01-evidence-before-claims`, pois `PASS` exige telemetria real de sessão CS2).
