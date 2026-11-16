# Relatório de Testes Funcionais dos Scripts Determinísticos (`scripts_test_report.md`)

- **Data de Geração**: `2026-11-07`
- **Diretório de Evidências Brutas**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\audit\skill_real_tests\` e `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\audit\skill_dry_runs\`
- **Classificação de Natureza dos Dados**:
  - Execução de processos, exit codes, tempos de resposta e auditoria sobre arquivos do repositório (`AGENTS.md`, `graphify-out/graph.json`, `src/CsBotManager/*.cs`): `REAL`
  - Inputs sintéticos de teste negativo/positivo controlado (`sample_valid_report.md`, `sample_invalid_report.md` e payloads `--dry-run`): `SIMULATED`
- **Status de Revisão**: `AGENT_REVIEWED` (`Script Implementer`, `Adversarial Skill Reviewer`, `Success Auditor`)
- **Fórmula de Agregação**:
  $$\text{Taxa de Aprovação dos Scripts} = \frac{\text{Testes de Scripts Aprovados}}{\text{Total de Testes Executados}} = \frac{16}{16} = 100.0\%$$

---

## 1. Testes de Compilação, CLI (`--help`) e Execução Determinística (11/11 Scripts)

Comando reproduzível:
```powershell
python -m py_compile .agents/skills/csbot-phase-gate/scripts/run_phase_gate.py .agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py .agents/skills/csbot-dataset-forensics/scripts/*.py .agents/skills/csbot-model-validator/scripts/validate_model_canonical.py .agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py .agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py
```

| # | Skill | Script | Hash SHA-256 Completo (64 hex) | `--help` Exit Code | `--dry-run` Exit Code | Veredito em `--dry-run` | Natureza em `--dry-run` |
|---|---|---|---|---:|---:|---|---|
| 1 | `csbot-phase-gate` | [run_phase_gate.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-phase-gate/scripts/run_phase_gate.py) | `0069c286ab7ff357b17f4f63d3fb507112a5121e2cba063cff4321ccd4838134` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 2 | `csbot-report-skeptic` | [audit_executive_report.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py) | `b316b8a2eea5e243c0683192088078b715dda53e618beb66e8dd0349b2a74f62` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 3 | `csbot-dataset-forensics` | [check_split_leakage.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/check_split_leakage.py) | `d29305f8852538ea826182295ed90d7b01ce5731df5be9383b5ec67cb5c16929` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 4 | `csbot-dataset-forensics` | [reconcile_dataset_counts.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/reconcile_dataset_counts.py) | `b7ffd2a9063fd1368578cbb10930c4428ad9a09d73e857a5291f4aa90926a687` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 5 | `csbot-dataset-forensics` | [audit_parquet_rows.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/audit_parquet_rows.py) | `59f92900b70f35a5f7155021933d1a3ab42dfc6faf433e808657e371c34393b5` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 6 | `csbot-dataset-forensics` | [verify_sample_provenance.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/verify_sample_provenance.py) | `e6da72636731064ba84004a11f0d86198c417dd3c1e26a55081e4e28cf5b57b8` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 7 | `csbot-dataset-forensics` | [detect_templated_outputs.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/detect_templated_outputs.py) | `2069a7bd7fb10b73a2434347e3e0bd331432aa4ab06fed192a6ab6c643247663` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 8 | `csbot-dataset-forensics` | [audit_label_support.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/scripts/audit_label_support.py) | `2f4c90954d3055ace527d2400bd995fc2cf4339bfe05a2421efceafe8b921feb` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 9 | `csbot-model-validator` | [validate_model_canonical.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-model-validator/scripts/validate_model_canonical.py) | `723e32394f7e81fd51e518801f1e541312936cfb3c3e84f91f9bd197a6b1242a` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 10 | `csbot-runtime-validation` | [verify_runtime_session.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py) | `fa0623a5552a7ab6f39c4e7633f8f33f0bf6b5832b3cf28cd5e71784e3c71106` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |
| 11 | `csbot-graph-impact` | [analyze_graph_impact.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py) | `8f618ab32766d196495683ac551674a71cf0689c047b46a058d4616542f3aa7b` | `0` | `0` | `CONDITIONAL` | `SIMULATED` |

---

## 2. Testes Funcionais com Entradas Reais e Casos Positivos/Negativos (5/5 Cenários)

| # | Cenário Funcional | Script Testado | Comando Reprodutível | Artefato Gerado | Resultado Observado | Status |
|---|---|---|---|---|---|---|
| 12 | Análise real do grafo `graphify-out/graph.json` e código C# (`src/CsBotManager/*.cs`) | `analyze_graph_impact.py` | `python .agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py --workspace-root . --graph-path graphify-out/graph.json --target-flow all --output-json .agents/audit/skill_real_tests/real_graph_impact.json` | [real_graph_impact.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_real_tests/real_graph_impact.json) | Exit Code `0`; 5 fluxos prioritários mapeados com verificação real de existência e SHA-256 dos arquivos C# em `src/CsBotManager/`. | `PASS` |
| 13 | Snapshot de entrada real (`AGENTS.md`, `.agents/skills.json`) | `run_phase_gate.py` | `python .agents/skills/csbot-phase-gate/scripts/run_phase_gate.py --phase-id GOV-REAL-TEST --workspace-root . --input-files AGENTS.md .agents/skills.json --output-dir .agents/audit/skill_real_tests/real_phase_gate` | [phase_input_snapshot.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_real_tests/real_phase_gate/phase_input_snapshot.json) | Exit Code `0`; 4 artefatos gerados com hashes SHA-256 de 64 chars verificados no disco. | `PASS` |
| 14 | Relatório válido submetido ao `csbot-report-skeptic` (Caso Positivo) | `audit_executive_report.py` | `python .agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py --report-path .agents/audit/skill_real_tests/sample_valid_report.md --workspace-root . --output-json .agents/audit/skill_real_tests/skeptic_valid_out.json` | [skeptic_valid_out.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_real_tests/skeptic_valid_out.json) | Exit Code `0`; `verdict: "PASS"`, `total_violations: 0`. | `PASS` |
| 15 | Relatório inválido com hash truncado, classe sem suporte com métrica numérica, percentual cheio sem denominador explícito (`0/1`), `Test` em tuning e arquivo inexistente (Caso Negativo `SIMULATED`) | `audit_executive_report.py` | `python .agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py --report-path .agents/audit/skill_real_tests/sample_invalid_report.md --workspace-root . --output-json .agents/audit/skill_real_tests/skeptic_invalid_out.json` | [skeptic_invalid_out.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_real_tests/skeptic_invalid_out.json) | Exit Code `1` (bloqueio determinístico); `verdict: "FAIL"` detectando as violações plantadas. | `PASS` |
| 16 | Verificação de sessão de runtime sem log de partida CS2 ativa (Proibição de inferir `0`) | `verify_runtime_session.py` | `python .agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py --workspace-root . --output-json .agents/audit/skill_real_tests/real_runtime_val.json` | [real_runtime_val.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_real_tests/real_runtime_val.json) | Exit Code `0`; reporta `ABSENT_TELEMETRY_NA` para telemetria ausente, sem jamais simular eventos ou preencher `0`. | `PASS` |
