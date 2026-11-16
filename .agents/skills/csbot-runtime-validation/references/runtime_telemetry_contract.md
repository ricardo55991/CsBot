# Contrato de Telemetria e Validação de Runtime Real (`csbot-runtime-validation`)

Este documento especifica os requisitos de verificação para build, deploy e auditoria dos 8 domínios de telemetria em runtime do servidor CS2.

---

## 1. Regras de Integridade de Sessão

1. **Verificação de Identidade de Binários e Modelos (`Deploy Parity`)**:
   - Todo log de sessão deve ser acompanhado de `runtime_deploy_manifest.json` comprovando que:
     - $\text{SHA256}(\text{Workspace } \texttt{CsBotManager.dll}) == \text{SHA256}(\text{Server } \texttt{CsBotManager.dll})$
     - $\text{SHA256}(\text{Workspace } \texttt{*.onnx}) == \text{SHA256}(\text{Server } \texttt{*.onnx})$
     - $\text{SHA256}(\text{Workspace } \texttt{MapProfiles/*.json}) == \text{SHA256}(\text{Server } \texttt{MapProfiles/*.json})$
2. **Proibição de Inferência de Sucesso por Silêncio**:
   - Se o contador de eventos observados de um domínio for `0` (`events_count == 0`), o status daquele domínio deve ser reportado como `"UNOBSERVED_IN_SESSION"` (`N/A`) e nunca como `"PASS"` ou `"0 falhas"`.
3. **Separação Estrita de Selos de Captura (`05-human-review-integrity`)**:
   - Sessões iniciadas/monitoradas por script RCON ou partida bot-vs-bot autônoma recebem `"capture_mode": "SCRIPT_CAPTURED"`.
   - Apenas sessões onde o usuário humano entrou no servidor ou inspecionou visualmente e declarou aprovação recebem `"capture_mode": "HUMAN_CAPTURE_IN_GAME"`.

---

## 2. Contrato de Auditoria por Subsistema

| Domínio de Runtime | Eventos Brutos Exigidos no Log | Invariante de Validação Física / Lógica |
| :--- | :--- | :--- |
| **1. Captura `!debug`** | `debug_snapshot`, `tick_heartbeat`, `onnx_inference_latency_ms` | Ticks monotônicos, bots ativos $> 0$, latência p99 dentro do orçamento de tick. |
| **2. Objetivo C4** | `c4_state_change`, `c4_carrier_move`, `c4_plant_attempt`, `c4_planted`, `c4_defuse_attempt` | Consistência entre `BombObjectiveState` e a posse/posição real do C4 no round. |
| **3. Economia** | `econ_decision`, `buy_command_issued`, `inventory_post_buy` | Todo `buy_command_issued` com saldo suficiente deve refletir item correspondente em `inventory_post_buy`. |
| **4. Execução de Jump** | `onnx_jump_request`, `jump_gate_decision`, `usercmd_jump_bit` | Quando `jump_gate_decision == APPROVED`, `usercmd` subsequente deve conter bit `IN_JUMP`; quando `BLOCKED`, `IN_JUMP` não deve ser acionado pelo modelo. |
| **5. Recovery e Movimento** | `recovery_triggered`, `arbitrator_source_selected`, `bot_position_delta` | Após `recovery_triggered`, o `MovementArbitrator` assume controle e produz deslocamento físico real $\|\Delta \mathbf{p}\| > d_{\min}$. |
| **6. Spots Táticos** | `spot_assigned`, `spot_reached`, `spot_hold_duration` | Coordenada do bot ao atingir `spot_reached` deve estar dentro do raio válido do spot em `MapProfiles/*.json`. |
| **7. Adaptações Táticas** | `tactical_adaptation_event`, `role_or_sector_transition` | Transição tática deve referenciar o evento gatilho real do round (`teammate_death`, `bomb_spotted`, `time_low`). |
| **8. Selamento da Partida** | `session_seal_manifest.json` | Contém `session_id`, timestamps de início/fim, contagem de rounds/ticks e SHA-256 de todos os arquivos de log da partida. |

---

## 3. Schema do `session_seal_manifest.json`

```json
{
  "session_id": "cs2_runtime_20261107_162000",
  "map_name": "de_mirage",
  "data_nature": "REAL",
  "capture_stamp": "SCRIPT_CAPTURED",
  "rounds_observed": 12,
  "ticks_observed": 46080,
  "deployed_artifacts_sha256": {
    "CsBotManager.dll": "64_hex_chars...",
    "positioning_model.onnx": "64_hex_chars...",
    "de_mirage.json": "64_hex_chars..."
  },
  "telemetry_logs": [
    {
      "path": "logs/session_telemetry.jsonl",
      "sha256": "64_hex_chars...",
      "size_bytes": 1845200
    }
  ],
  "domain_observability": {
    "debug_capture": "OBSERVED",
    "c4_objective": "OBSERVED",
    "economy": "OBSERVED",
    "jump_execution": "OBSERVED",
    "recovery_movement": "OBSERVED",
    "tactical_spots": "OBSERVED",
    "tactical_adaptations": "OBSERVED"
  }
}
```
