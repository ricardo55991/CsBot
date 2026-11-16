# Regra 14: Relatórios Enxutos e Canônicos (`14-lean-reporting`)

**É proibida a proliferação de relatórios intermediários narrativos, relatórios repetidos por subagente e relatórios de vitória desnecessários.**

---

## 1. Artefatos Permitidos Durante a Execução
Durante o ciclo de trabalho de uma tarefa, as comunicações entre agentes e o registro de progresso ocorrem exclusivamente via JSONs concisos e estruturados:
- `progress.json`
- `findings.json`
- `test_result.json`
- `blocker.json`
- `execution_efficiency.json`

---

## 2. Artefatos de Encerramento por Tier
No encerramento da tarefa ou marco:
- **Tier 1 e Tier 2:** Apenas **1 relatório canônico em Markdown** (`final_report.md` ou equivalente de fase) e `deliverable_evidence.json` caso haja conclusão formal.
- **Tier 3:** `findings.json`, `test_result.json`, `final_report.md` e `deliverable_evidence.json`.
- **Tier 4:** Relatório separado de auditor independente somente quando a independência for estritamente exigida pela governança.

---

## 3. Proibições Específicas
- Não gerar relatórios narrativos redundantes (ex: relatório do implementador + relatório do revisor + consolidação que repete os dois anteriores);
- Não gerar "Victory Reports" ou celebrações textuais vazias;
- Citar sempre os hashes e caminhos dos dados brutos, sem duplicar tabelas imensas no Markdown.
