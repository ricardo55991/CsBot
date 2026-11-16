# Inventário dos Hooks de Governança do Workspace CsBot (`hooks_inventory.md`)

- **Data de Geração**: `2026-11-07`
- **Escopo**: Workspace Local (`c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\`)
- **Hooks Globais (`~/.gemini/config/hooks.json`)**: Intocados / Inexistentes (verificado pelo `Security Reviewer`)
- **Classificação de Natureza dos Dados**: `REAL`
- **Status de Revisão**: `AGENT_REVIEWED` (`Hook Schema Explorer`, `Hook Implementer`, `Security Reviewer`, `False-Positive Tester`, `Success Auditor`)
- **Comando Reprodutível de Verificação**:
  ```powershell
  Get-FileHash -Algorithm SHA256 .agents/hooks.json, hooks_config.json, .agents/hooks/*.py, .agents/hooks/hook_mode.json
  ```

---

## 1. Arquitetura e Localização dos 5 Hooks

Os hooks operam exclusivamente no escopo do workspace por meio do arquivo canônico [`.agents/hooks.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks.json) (espelhado em [`hooks_config.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/hooks_config.json)).

| # | Nome do Hook (Chave Top-Level) | Script Python Associado | Eventos Monitorados | Matcher Regex | Timeout (`s`) | Política em Erro |
|---|---|---|---|---|---:|---|
| **Hook A** | `protect-sensitive-files` | [protect_sensitive_files.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/protect_sensitive_files.py) | `PreToolUse` | `write_to_file\|replace_file_content\|multi_replace_file_content\|write_file\|edit_file\|run_command` | `15` | `Fail-Closed` (`deny`) |
| **Hook B** | `validate-generated-report` | [validate_generated_report.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/validate_generated_report.py) | `PreToolUse`, `PostToolUse`, `Stop` | Escrita/edição de arquivos + `Stop` (flat) | `15` | `Fail-Closed` (`deny` / `continue`) |
| **Hook C** | `pre-training-gate` | [pre_training_gate.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/pre_training_gate.py) | `PreToolUse` | `run_command` | `15` | `Fail-Closed` (`deny`) |
| **Hook D** | `post-test-audit` | [post_test_audit.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/post_test_audit.py) | `PostToolUse` | `run_command` | `15` | Registra estado em `.agents/audit/last_test_execution.json` |
| **Hook E** | `stop-condition-evidence-gate` | [stop_condition_evidence_gate.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/stop_condition_evidence_gate.py) | `Stop` | N/A (Estrutura Flat) | `15` | `Fail-Closed` (`continue`) |

---

## 2. Hashes SHA-256 Completos e Tamanhos dos Scripts (`REAL`)

| Arquivo | Caminho Relativo | Tamanho (Bytes) | Hash SHA-256 Completo (64 caracteres hexadecimais) |
|---|---|---:|---|
| Utilitário Comum e Fail-Safe | [`.agents/hooks/common_hook_utils.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/common_hook_utils.py) | `10.857` | `c8d538fda8bbc8e9fbb5ccd8dae892264229bc6873e2adc6c30e1f496ff26d12` |
| Hook A (`protect-sensitive-files`) | [`.agents/hooks/protect_sensitive_files.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/protect_sensitive_files.py) | `9.185` | `b9a3f22e511e1efff85601c491371f2c92cdf5e8a62e43171bd51dad4b7ebca3` |
| Hook B (`validate-generated-report`) | [`.agents/hooks/validate_generated_report.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/validate_generated_report.py) | `17.767` | `31f47e0cc487c22749c1369e16e9fd7f0d80bbc5a26c5a8cc0070a8baeab30ca` |
| Hook C (`pre-training-gate`) | [`.agents/hooks/pre_training_gate.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/pre_training_gate.py) | `9.693` | `923b1bdafb70bf561d5617cd5bb27dfdadd148998f12f12eb0ea62df64310b82` |
| Hook D (`post-test-audit`) | [`.agents/hooks/post_test_audit.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/post_test_audit.py) | `10.393` | `6f1e249bb60bc0bc04a575460f25d48ec91aa5768fd6c623f951ae51968d689d` |
| Hook E (`stop-condition-evidence-gate`) | [`.agents/hooks/stop_condition_evidence_gate.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/stop_condition_evidence_gate.py) | `8.931` | `34874ef26a839ea26d1c857fc2bf53607a8edf2e933caa3931852127db6147ee` |

---

## 3. Especificação Funcional Detalhada de Cada Hook

### 3.1 Hook A — `protect-sensitive-files`
- **Alvos protegidos**: `*.onnx`, `*.pt`, `de_mirage.json`, `*split*.json`, `*manifest*.json`, `*contract*.json`, `*catalog*.json`.
- **Requisito de liberação**: Presença do manifesto de autorização `sensitive_file_authorization` (ou variável `CSBOT_SENSITIVE_AUTH_FILE`) contendo obrigatoriamente:
  - `backup_path` (com arquivo de backup verificável);
  - `previous_sha256` (64 caracteres hexadecimais);
  - `planned_diff`;
  - `rollback_command`;
  - `approved_phase`.

### 3.2 Hook B — `validate-generated-report`
- **Gatilho**: Escrita/atualização de relatórios (`.md`, `.json`, `.pdf`) e fechamento de turno (`Stop`).
- **Regras verificadas (`csbot-report-skeptic`)**:
  1. classe sem suporte (`support` igual a zero) exibindo métrica numérica em vez de `N/A`;
  2. números incompatíveis ou concatenados (ex: `340340` em vez de `340/340`);
  3. IDs templados (`TEMPLATED` / `SIMULATED`);
  4. classe inexistente no schema tático;
  5. hash SHA-256 inconsistente ou truncado (`< 64` chars hex);
  6. indicação de `Test` usado em tuning / escolha de checkpoint / calibração / threshold;
  7. claim `PASS` sem fonte ou sem artefato bruto;
  8. atribuição de selo de aprovação humana por pipeline automatizado sem homologação humana;
  9. relatório executivo emitindo conclusão sem artefato bruto verificável.

### 3.3 Hook C — `pre-training-gate`
- **Gatilho**: Comandos `run_command` contendo `train`, `fit`, `finetune`, `torchrun`, `accelerate launch`.
- **Exigências verificadas no manifesto `input_snapshot`**:
  - `input_snapshot.json` presente;
  - `split_leakage == 0`;
  - `tests == "green"`;
  - `dry_run == "pass"`;
  - `dataset_hashes` (SHA-256 de 64 chars);
  - `catalog_hash` (SHA-256 de 64 chars);
  - `checkpoint_policy` definida;
  - `no_test_tuning == true` (e ausência de `test`/`holdout` em `tuning_split` ou `checkpoint_selection_split`).

### 3.4 Hook D — `post-test-audit`
- **Gatilho**: Execução de `dotnet test`, `pytest` ou scripts Python de teste.
- **Campos capturados em `.agents/audit/last_test_execution.json`**:
  `command`, `working_directory`, `discovered`, `passed`, `failed`, `skipped`, `duration`, `exit_code`, `test_assemblies`, e `canonical_summary` no formato estrito `<passed>/<discovered>` (impedindo erros como `340340`).

### 3.5 Hook E — `stop-condition-evidence-gate`
- **Gatilho**: Evento `Stop`.
- **Exigências**:
  1. Valida [`.agents/audit/deliverable_evidence.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/deliverable_evidence.json) (e `deliverable_evidence.json` na raiz) exigindo `phase`, `verdict` e lista `claims` onde cada claim possui `claim_id`, `claim`, `evidence_files`, `raw_sources`, `reproduction_command` e `validator`.
  2. Impede `verdict: "PASS"` se `last_test_execution.json` registrar teste falho (`status: "FAILED"`).
  3. Impede encerramento se `last_report_validation.json` registrar violação pendente.

---

## 4. Segurança, Sanitização e Modos de Operação

- **Modos**: Controlados por [`.agents/hooks/hook_mode.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/hooks/hook_mode.json) (`"mode": "audit-only"` ou `"mode": "blocking"`) ou variável `CSBOT_HOOK_MODE`.
- **Logs de Auditoria**: Gravados em [`.agents/audit/hooks_audit.jsonl`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/hooks_audit.jsonl) com sanitização automática de caminhos pessoais (`C:\Users\ricar` -> `<USER_HOME>`) e segredos (`<REDACTED_SECRET>`).
