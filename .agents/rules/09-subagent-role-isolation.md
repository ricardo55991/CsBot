# Regra 09: Subagent Role Isolation (`09-subagent-role-isolation`)

Regras estritas de isolamento entre papéis de subagentes:
1. **`Implementer` não pode editar relatório de auditoria**: O implementador opera com `EnableWriteTools = true`, mas é terminantemente proibido de editar ou sobrescrever relatórios de auditoria (`*audit*.md`, `*audit*.json`, `*skeptic*.json`, `phase_gate_report.md`, `deliverable_evidence.json`) ou declarar-se `validator`.
2. **`Auditor` não pode alterar implementação**: Todo auditor opera estritamente com `EnableWriteTools = false` e é proibido de tocar em código-fonte (`src/`, `tools/`, `tests/`) ou datasets.
3. **`Success Auditor` e `Adversarial Reviewer` não corrigem falhas**: Se encontrarem qualquer divergência ou pendência, eles não tentam consertar. Emitem veredito `FAIL` detalhando os bloqueadores e **devolvem imediatamente ao `Orchestrator`**.

**Ciclo de Devolução**:
`Orchestrator` -> despacha correção para `Implementer` / `Test Author` -> aciona `Metrics Reproducer` se necessário -> submete à nova rodada de auditoria independente.
