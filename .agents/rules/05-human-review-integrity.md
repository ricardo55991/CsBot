# Regra 05: Human Review Integrity (`05-human-review-integrity`)

Apenas o usuário humano pode atribuir os seguintes selos de homologação:
- `APPROVED_BY_USER`
- `REJECTED_BY_USER`
- `HUMAN_CAPTURE_IN_GAME`

> **Regras de Bloqueio**:
> 1. Scripts automatizados, subagentes ou pipelines não podem emitir relatórios afirmando "inspecionado manualmente", "validado pelo operador humano" ou equivalentes.
> 2. Toda validação conduzida por subagentes ou scripts deve carregar os rótulos canônicos: `AGENT_REVIEWED`, `AUTOMATED_CHECK_PASS` ou `SCRIPT_CAPTURED`.
> 3. O auditor `csbot-report-skeptic` reprovará com `FAIL` qualquer entrega que contenha alegação de chancela humana sem confirmação explícita registrada na sessão.
