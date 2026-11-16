---
name: csbot-dataset-forensics
description: Audita forensemente datasets do CsBot (Parquet, NPZ, manifests e catálogos), verificando vazamento entre splits (leakage), reconciliação de contagens, integridade de linhas/sequências, proveniência de amostras, detecção de dados templados e suporte de labels. Use sempre ao construir, transformar, filtrar ou validar datasets de treinamento, validação e teste.
---

# CsBot Dataset Forensics

Esta Skill audita forensemente os pipelines de dados do CsBot (`Parquet`, `NPZ`, splits, sequências, rejeições e manifests), garantindo integridade de splits (`02-no-test-contamination`), suporte zero como `N/A` (`03-zero-support-is-na`), detecção de dados templados (`04-synthetic-data-labeling`) e proteção de contratos (`06-sensitive-artifact-protection`). Veja [dataset_forensics_protocol.md](./references/dataset_forensics_protocol.md).

## Procedimento Operacional e Argumentos Canônicos

Execute os 6 scripts forenses abaixo e registre cada `--output-json` (`-o`) na matriz de evidências:

1. **Vazamento entre Splits** ([check_split_leakage.py](./scripts/check_split_leakage.py)):
   - Flags: `--input` (`-i`), `--train-input`, `--val-input`, `--test-input`, `--output-json` (`-o`), `--dry-run`.
   ```powershell
   python .agents/skills/csbot-dataset-forensics/scripts/check_split_leakage.py --input data/splits --output-json artifacts/leakage.json
   ```
2. **Contabilidade e Rejeições** ([reconcile_dataset_counts.py](./scripts/reconcile_dataset_counts.py)):
   - Flags: `--manifest` (`-m`), `--raw-dir` (`-d`), `--report-json` (`-r`), `--fps-or-tickrate`, `--hours-tolerance`, `--output-json` (`-o`), `--dry-run`.
   ```powershell
   python .agents/skills/csbot-dataset-forensics/scripts/reconcile_dataset_counts.py --manifest data/dataset_manifest.json --raw-dir data/raw --output-json artifacts/counts.json
   ```
3. **Linhas Parquet, NPZ e Sequências** ([audit_parquet_rows.py](./scripts/audit_parquet_rows.py)):
   - Flags: `--input` (`-i`), `--required-columns`, `--strict-tick-increasing`, `--output-json` (`-o`), `--dry-run`.
   ```powershell
   python .agents/skills/csbot-dataset-forensics/scripts/audit_parquet_rows.py --input data/parquet --strict-tick-increasing --output-json artifacts/parquet_rows.json
   ```
4. **Proveniência e Amostragem Visual** ([verify_sample_provenance.py](./scripts/verify_sample_provenance.py)):
   - Flags: `--input` (`-i`), `--demo-catalog` (`-c`), `--base-dir` (`-b`), `--no-require-sha256`, `--output-json` (`-o`), `--dry-run`.
   ```powershell
   python .agents/skills/csbot-dataset-forensics/scripts/verify_sample_provenance.py --input data/samples.json --demo-catalog data/demo_catalog.json --output-json artifacts/provenance.json
   ```
5. **Detecção de Dados Templados** ([detect_templated_outputs.py](./scripts/detect_templated_outputs.py)):
   - Flags: `--input` (`-i`), `--repetition-threshold`, `--output-json` (`-o`), `--dry-run`.
   ```powershell
   python .agents/skills/csbot-dataset-forensics/scripts/detect_templated_outputs.py --input data/splits --output-json artifacts/templated.json
   ```
6. **Suporte de Labels (`support=0 -> N/A`)** ([audit_label_support.py](./scripts/audit_label_support.py)):
   - Flags: `--input` (`-i`), `--schema-json` (`-s`), `--fail-on-empty-head`, `--output-json` (`-o`), `--dry-run`.
   ```powershell
   python .agents/skills/csbot-dataset-forensics/scripts/audit_label_support.py --input data/splits --schema-json data/schema.json --output-json artifacts/label_support.json
   ```

## Regra de `--dry-run` e Bloqueio (`FAIL`)

- **Regra de `--dry-run`**: Nos 6 scripts, `--dry-run` emite veredito **`CONDITIONAL`** com `data_nature: SIMULATED` (`01-evidence-before-claims`, pois `PASS` exige execução real sobre artefatos brutos).
- **Bloqueio (`FAIL`)**: Vazamento entre splits, divergência contábil ou preenchimento artificial de classes `support = 0` no `Test`.
