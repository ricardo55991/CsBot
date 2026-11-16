# Relatório da Bateria de 10 Testes Obrigatórios dos Hooks (`hooks_test_report.md`)

- **Data de Geração**: `2026-11-07`
- **Artefato Bruto de Resultados**: [hooks_test_results.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/hooks_test_results.json)
- **Hash SHA-256 Completo de `hooks_test_results.json`**: `71ecf5676b622090145ad4acd88b9271f9adadfc93a27929bc457e5fafa7e583`
- **Log Forense de Auditoria**: [hooks_audit.jsonl](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/hooks_audit.jsonl) (SHA-256: `66f9bbb0d1d25cf448244c589795b95d35d501e4aed1bfa37ae04e1b3899cc08`)
- **Classificação de Natureza dos Dados**:
  - Execuções dos processos Python, exit codes, tempos de resposta e saídas JSON de `stdout`: `REAL`
  - Payloads de eventos injetados via `stdin`: `SIMULATED` (para testar bloqueios sem destruir ou tocar arquivos reais do projeto)
- **Status de Revisão**: `AGENT_REVIEWED` (`False-Positive Tester`, `Security Reviewer`, `Success Auditor`)
- **Comando Reprodutível**:
  ```powershell
  python "C:\Users\ricar\.gemini\antigravity\brain\e5a6711f-cc28-4cb7-a8ae-96689fa0294d\scratch\execute_hook_tests.py"
  ```
- **Fórmula de Agregação**:
  $$\text{Taxa de Sucesso (Testes Obrigatórios)} = \frac{\text{Cenários Aprovados em Audit-Only (10) + Cenários Aprovados em Blocking (10)}}{\text{Total de Execuções Obrigatórias (20)}} = \frac{20}{20} = 100.0\%$$

---

## 1. Sequência Metodológica Executada

Conforme exigido pelas diretrizes:
1. **Fase 1 (`audit-only`)**: Os 5 hooks foram configurados inicialmente com `"mode": "audit-only"` em `.agents/hooks/hook_mode.json`. Todos os 10 cenários foram executados, comprovando que as violações são registradas em `.agents/audit/hooks_audit.jsonl` com `"would_block": true` enquanto retornam `"decision": "allow"` com prefixo `[AUDIT-ONLY]`.
2. **Fase 2 (`blocking`)**: Em seguida, os mesmos 10 cenários foram executados em modo `"blocking"`, comprovando bloqueio determinístico imediato (`"decision": "deny"` em `PreToolUse` e `"decision": "continue"` em `Stop`) com explicação clara do motivo e ação corretiva.

---

## 2. Resultados Detalhados dos 10 Testes Obrigatórios

| # | Cenário Obrigatório | Hook Executado | Resultado em `audit-only` | Tempo (`audit-only`) | Resultado em `blocking` | Tempo (`blocking`) | Exit Code | Status |
|---|---|---|---|---:|---|---:|---:|---|
| **1** | **Alteração comum não é bloqueada** (`write_file` em `src/CsBotManager/BotLocomotionDriver.cs`) | `protect-sensitive-files` | `{"decision": "allow"}` (`would_block: false`) | `126.68 ms` | `{"decision": "allow", "reason": "Nenhum artefato sensível afetado pela operação."}` | `119.52 ms` | `0` | `PASS` |
| **2** | **Alteração em ONNX sem autorização é bloqueada** (`write_file` simulado `SIMULATED` em alvo `.onnx`) | `protect-sensitive-files` | `{"decision": "allow", "reason": "[AUDIT-ONLY] Violação registrada..."}` (`would_block: true`) | `121.53 ms` | `{"decision": "deny", "reason": "BLOQUEIO [protect-sensitive-files]: Modificação em artefato sensível bloqueada..."}` | `123.67 ms` | `0` | `PASS` |
| **3** | **Alteração com hash e backup é permitida** (`write_file` em `.onnx` com `backup_path` e `previous_sha256` de 64 hex) | `protect-sensitive-files` | `{"decision": "allow"}` (`would_block: false`) | `134.96 ms` | `{"decision": "allow", "reason": "Autorização de artefato sensível verificada com hash e backup."}` | `134.32 ms` | `0` | `PASS` |
| **4** | **Relatório com classe sem suporte e métrica numérica é bloqueado** (violação da Regra 03 `SIMULATED`) | `validate-generated-report` | `{"decision": "allow", "reason": "[AUDIT-ONLY] Violação registrada..."}` (`would_block: true`) | `132.31 ms` | `{"decision": "deny", "reason": "BLOQUEIO [validate-generated-report]: ... [Regra 03] Linha sem suporte exibe métrica numérica em vez de 'N/A'..."}` | `134.90 ms` | `0` | `PASS` |
| **5** | **Relatório correto passa** (`support=0 -> N/A`, SHA-256 64 hex, `340/340`, `AGENT_REVIEWED`) | `validate-generated-report` | `{"decision": "allow"}` (`would_block: false`) | `128.58 ms` | `{"decision": "allow", "reason": "Relatório validado com sucesso pelo csbot-report-skeptic (0 violações)."}` | `137.89 ms` | `0` | `PASS` |
| **6** | **Treino sem snapshot é bloqueado** (`python train_positioning.py --epochs 20` sem `input_snapshot.json`) | `pre-training-gate` | `{"decision": "allow", "reason": "[AUDIT-ONLY] Violação registrada..."}` (`would_block: true`) | `129.53 ms` | `{"decision": "deny", "reason": "BLOQUEIO [pre-training-gate]: ... Manifesto de prontidão 'input_snapshot.json' ausente..."}` | `144.15 ms` | `0` | `PASS` |
| **7** | **Treino com `Test` em tuning é bloqueado** (`torchrun train.py` com `tuning_split: "test"`, `no_test_tuning: false`) | `pre-training-gate` | `{"decision": "allow", "reason": "[AUDIT-ONLY] Violação registrada..."}` (`would_block: true`) | `130.32 ms` | `{"decision": "deny", "reason": "BLOQUEIO [pre-training-gate]: ... Regra 02 violada: 'tuning_split' está configurado como 'test'..."}` | `134.62 ms` | `0` | `PASS` |
| **8** | **Teste falho impede `PASS`** (`pytest` com 2 falhas registrado por `post-test-audit` seguido de `Stop` com `verdict: "PASS"`) | `post-test-audit` + `stop-condition-evidence-gate` | `post_test`: `{}`<br>`stop`: `{"decision": "allow", "reason": "[AUDIT-ONLY]..."}` (`would_block: true`) | `257.71 ms` | `post_test`: `{}` (`status: FAILED`, `10/12`)<br>`stop`: `{"decision": "continue", "reason": "BLOQUEIO [stop-condition-evidence-gate]: ... Teste falho impede emissão de veredito PASS (summary=10/12)..."}` | `259.39 ms` | `0` | `PASS` |
| **9** | **Claim sem evidência impede encerramento** (`deliverable_evidence.json` com `evidence_files: []`) | `stop-condition-evidence-gate` | `{"decision": "allow", "reason": "[AUDIT-ONLY] Violação registrada..."}` (`would_block: true`) | `123.15 ms` | `{"decision": "continue", "reason": "BLOQUEIO [stop-condition-evidence-gate]: ... claims[0]: 'evidence_files' deve ser uma lista não-vazia..."}` | `121.36 ms` | `0` | `PASS` |
| **10** | **Hook em erro falha de modo seguro** (payload truncado `{invalid_json` enviado via `stdin`) | `protect-sensitive-files` & `stop-condition-evidence-gate` | `{"decision": "allow", "reason": "[AUDIT-ONLY] ... Falha fail-safe na leitura do payload stdin..."}` | `239.74 ms` | `PreToolUse`: `{"decision": "deny", "reason": "BLOQUEIO [protect-sensitive-files]: Falha fail-safe na leitura do payload stdin..."}`<br>`Stop`: `{"decision": "continue", "reason": "BLOQUEIO [stop-condition-evidence-gate]: Falha fail-safe..."}` | `240.23 ms` | `0` | `PASS` |
