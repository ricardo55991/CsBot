# Relatório de Execução de Dry-Run das 6 Skills (`skill_dry_run_report.md`)

- **Data de Geração**: `2026-11-07`
- **Artefato Bruto Consolidado**: [dry_run_summary.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/dry_run_summary.json)
- **Diretório de Saídas do Dry-Run**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\audit\skill_dry_runs\`
- **Classificação de Natureza dos Dados**:
  - Métricas de execução de processo (`exit_code`, `duration_ms`, hashes de scripts): `REAL`
  - Payloads internos de autodiagnóstico gerados com a flag `--dry-run`: `SIMULATED` (com veredito estrito `CONDITIONAL`, em respeito à Regra `01-evidence-before-claims`)
- **Status de Revisão**: `AGENT_REVIEWED`
- **Fórmula de Agregação**:
  $$\text{Dry-Runs Concluídos com Sucesso} = \frac{\text{Scripts com Exit Code } 0 \text{ e Veredito CONDITIONAL}}{\text{Total de Scripts nas 6 Skills}} = \frac{11}{11} = 100.0\%$$

---

## 1. Resumo de Execução do Dry-Run por Skill e Script

| # | Skill | Script Executado | Comando Reprodutível | Exit Code | Duração (`ms`) | Artefato Gerado no Dry-Run | Veredito Emitido | Natureza Declarada |
|---|---|---|---|---:|---:|---|---|---|
| 1 | `csbot-phase-gate` | `run_phase_gate.py` | `python .agents/skills/csbot-phase-gate/scripts/run_phase_gate.py --phase-id GOV-DRYRUN --output-dir .agents/audit/skill_dry_runs/phase_gate --dry-run` | `0` | `150.65` | [phase_gate_report.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/phase_gate/phase_gate_report.md) + 3 arquivos | `CONDITIONAL` | `SIMULATED` |
| 2 | `csbot-report-skeptic` | `audit_executive_report.py` | `python .agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py --output-json .agents/audit/skill_dry_runs/skeptic_audit.json --dry-run` | `0` | `152.35` | [skeptic_audit.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/skeptic_audit.json) | `CONDITIONAL` | `SIMULATED` |
| 3 | `csbot-dataset-forensics` | `check_split_leakage.py` | `python .agents/skills/csbot-dataset-forensics/scripts/check_split_leakage.py --output-json .agents/audit/skill_dry_runs/leakage.json --dry-run` | `0` | `144.38` | [leakage.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/leakage.json) | `CONDITIONAL` | `SIMULATED` |
| 4 | `csbot-dataset-forensics` | `reconcile_dataset_counts.py` | `python .agents/skills/csbot-dataset-forensics/scripts/reconcile_dataset_counts.py --output-json .agents/audit/skill_dry_runs/reconcile.json --dry-run` | `0` | `142.07` | [reconcile.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/reconcile.json) | `CONDITIONAL` | `SIMULATED` |
| 5 | `csbot-dataset-forensics` | `audit_parquet_rows.py` | `python .agents/skills/csbot-dataset-forensics/scripts/audit_parquet_rows.py --output-json .agents/audit/skill_dry_runs/parquet_audit.json --dry-run` | `0` | `140.96` | [parquet_audit.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/parquet_audit.json) | `CONDITIONAL` | `SIMULATED` |
| 6 | `csbot-dataset-forensics` | `verify_sample_provenance.py` | `python .agents/skills/csbot-dataset-forensics/scripts/verify_sample_provenance.py --output-json .agents/audit/skill_dry_runs/provenance.json --dry-run` | `0` | `142.04` | [provenance.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/provenance.json) | `CONDITIONAL` | `SIMULATED` |
| 7 | `csbot-dataset-forensics` | `detect_templated_outputs.py` | `python .agents/skills/csbot-dataset-forensics/scripts/detect_templated_outputs.py --output-json .agents/audit/skill_dry_runs/templated.json --dry-run` | `0` | `156.40` | [templated.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/templated.json) | `CONDITIONAL` | `SIMULATED` |
| 8 | `csbot-dataset-forensics` | `audit_label_support.py` | `python .agents/skills/csbot-dataset-forensics/scripts/audit_label_support.py --output-json .agents/audit/skill_dry_runs/label_support.json --dry-run` | `0` | `140.47` | [label_support.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/label_support.json) | `CONDITIONAL` | `SIMULATED` |
| 9 | `csbot-model-validator` | `validate_model_canonical.py` | `python .agents/skills/csbot-model-validator/scripts/validate_model_canonical.py --output-dir .agents/audit/skill_dry_runs/model_eval --dry-run` | `0` | `154.02` | [canonical_metrics.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/model_eval/canonical_metrics.json) + 5 arquivos | `CONDITIONAL` | `SIMULATED` |
| 10 | `csbot-runtime-validation` | `verify_runtime_session.py` | `python .agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py --output-json .agents/audit/skill_dry_runs/runtime_val.json --dry-run` | `0` | `261.17` | [runtime_val.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/runtime_val.json) | `CONDITIONAL` | `SIMULATED` |
| 11 | `csbot-graph-impact` | `analyze_graph_impact.py` | `python .agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py --output-json .agents/audit/skill_dry_runs/graph_impact.json --dry-run` | `0` | `1007.61` | [graph_impact.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/graph_impact.json) | `CONDITIONAL` | `SIMULATED` |

---

## 2. Verificação dos Artefatos Gerados pelas Skills multi-arquivo em Dry-Run

1. **`csbot-phase-gate` (`4/4` artefatos gerados em `.agents/audit/skill_dry_runs/phase_gate/`)**:
   - [phase_input_snapshot.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/phase_gate/phase_input_snapshot.json)
   - [phase_requirement_matrix.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/phase_gate/phase_requirement_matrix.md)
   - [phase_evidence_matrix.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/phase_gate/phase_evidence_matrix.json)
   - [phase_gate_report.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/phase_gate/phase_gate_report.md)
2. **`csbot-model-validator` (`6/6` artefatos gerados em `.agents/audit/skill_dry_runs/model_eval/`)**:
   - [canonical_eval_manifest.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/model_eval/canonical_eval_manifest.json)
   - [canonical_metrics.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/model_eval/canonical_metrics.json) (com classes `OBJECTIVE` e `SAVE` de `support=0` reportadas estritamente como `"N/A"`)
   - [confusion_counts.csv](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/model_eval/confusion_counts.csv)
   - [confusion_normalized.csv](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/model_eval/confusion_normalized.csv) (linhas com `support=0` preenchidas com `N/A`)
   - [calibration.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/model_eval/calibration.json)
   - [checkpoint_comparison.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/skill_dry_runs/model_eval/checkpoint_comparison.json)
