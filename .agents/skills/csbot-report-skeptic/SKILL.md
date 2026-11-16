---
name: csbot-report-skeptic
description: Executa auditoria adversarial cética sobre relatórios executivos e entregas de fase do projeto CsBot para invalidar afirmações sem lastro e detectar os 12 padrões de falha metodológica ou documental. Use obrigatoriamente sobre toda entrega de fase antes da emissão do veredito no phase gate.
---

# CsBot Report Skeptic

Esta Skill atua como o **Auditor Adversarial** (`07-independent-validation`) do CsBot. Sua função é tentar invalidar relatórios executivos e entregas de fase confrontando cada afirmação com os artefatos brutos reais no disco.

## Os 12 Itens Obrigatórios de Verificação Cética

Todo relatório executivo deve ser auditado contra os 12 vetores abaixo. Qualquer violação resulta em veredito `FAIL`:

1. **Números conflitantes**: Divergência de valores (totais, médias, acurácia, contagens) entre texto, tabelas Markdown e JSONs/CSVs brutos.
2. **Métricas sem origem**: Números citados sem caminho de artefato bruto, hash SHA-256, comando e fórmula explícita (`01-evidence-before-claims`).
3. **Classes sem suporte**: Classes/spots com `support = 0` exibindo `0.0%`, `100.0%` ou `0.0` em vez de estritamente `N/A` (`03-zero-support-is-na`).
4. **Matriz incompatível**: Soma de `confusion_counts.csv` divergente do total do split ou linhas de `confusion_normalized.csv` não somando `1.0` (quando `support > 0`).
5. **Hashes divergentes**: Hash SHA-256 truncado (< 64 chars hex), inexistente ou divergente do arquivo real no disco.
6. **Relatório hardcoded**: Scripts que emitem `"PASS"` ou métricas por literais fixos no código em vez de computação dinâmica sobre artefatos brutos.
7. **Dados templados**: Dados sintéticos, repetitivos, interpolados ou simulados sem a etiqueta `SIMULATED`/`TEMPLATED`/`SYNTHETIC` (`04-synthetic-data-labeling`).
8. **Arquivos declarados que não existem**: Caminhos de checkpoints, parquets, logs ou relatórios referenciados que não existem no disco ou têm 0 bytes.
9. **Testes que não foram descobertos**: Alegação de suíte verde quando o runner executou `0 tests discovered/collected` ou filtrou testes silenciosamente.
10. **Test usado em tuning**: Uso do conjunto `Test` para escolher época, checkpoint, hiperparâmetro, calibração ou threshold (`02-no-test-contamination`).
11. **"100%" sem denominador**: Afirmações de `100%` sem explicitar `numerador / denominador` e a máscara/filtro aplicado.
12. **"Humano" sem aprovação humana**: Selos `APPROVED_BY_USER`, `REJECTED_BY_USER` ou `HUMAN_CAPTURE_IN_GAME` emitidos por agente ou script sem ação humana real (`05-human-review-integrity`).

Consulte o checklist forense detalhado em [skeptic_audit_checklist.md](./references/skeptic_audit_checklist.md).

## Procedimento Operacional Passo a Passo

1. **Localizar Alvos**: Identifique o relatório executivo Markdown (`--report-path`) e o manifesto de hashes/evidências (`--manifest-path`).
2. **Executar Auditoria Automatizada**: Rode [audit_executive_report.py](./scripts/audit_executive_report.py) com os argumentos canônicos:
   ```powershell
   python .agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py `
     --report-path artifacts/phase_gate/phase_gate_report.md `
     --manifest-path artifacts/phase_gate/phase_evidence_matrix.json `
     --workspace-root . `
     --output-json artifacts/phase_gate/skeptic_audit_report.json `
     --strict
   ```
   - **Regra de `--dry-run`**: Em modo `--dry-run`, o script executa autodiagnóstico estrutural e emite veredito **`CONDITIONAL`** com `data_nature: SIMULATED` (em respeito à Regra `01-evidence-before-claims`, pois `PASS` exige execução real sobre artefatos brutos).
3. **Inspeção Cruzada Manual**: Audite cada tabela e afirmação seguindo [skeptic_audit_checklist.md](./references/skeptic_audit_checklist.md) e bloqueie a fase caso haja qualquer falha nos 12 itens.
