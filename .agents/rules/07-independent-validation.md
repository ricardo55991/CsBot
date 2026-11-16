# Regra 07: Independent Validation (`07-independent-validation`)

O agente ou subagente implementador **nunca pode ser o único validador de seu próprio trabalho quando houver responsabilidade independente que não possa ser atendida adequadamente por script determinístico, teste direcionado ou Hook**.

---

### Matriz de Risco para Alocação de Auditores (Governança 1.2 Lean):

A alocação de subagentes e auditores segue estritamente os limites operacionais por Tier para evitar explosão de tokens:

1. **Tier 1 (Baixo Risco - Documentação, Markdown, JSON simples, inventários, relatórios, pesquisa, minutas, formatação)**:
   - Limite: **0 subagentes** (executado diretamente pelo agente principal com validação determinística de sintaxe, schema e links).

2. **Tier 2 (Risco Moderado - Script Python isolado, Hook localizado, Skill localizada, parser, teste específico sem impacto em runtime)**:
   - Limite: **0 ou 1 subagente** (agente principal como implementador e, se necessário, 1 revisor independente somente-leitura com Evidence Packet cirúrgico).

3. **Tier 3 (Alto Risco - DataLoader, labels, índices temporais, contratos de dataset, métricas, calibração, fine-tuning localizado, splits)**:
   - Limite: **Máximo 2 subagentes** (ex: `Implementer` + `Auditor combinado de matemática, ML e proveniência`).

4. **Tier 4 (Crítico - Treinamento completo, arquitetura ampla, checkpoint mestre, ONNX, integração C#, deploy, runtime, homologação final de fase)**:
   - Limite: **Máximo 4 subagentes** especializados com responsabilidades distintas e sem sobreposição:
     1. *Implementer / Executor*;
     2. *Mathematical, ML and Provenance Auditor*;
     3. *Runtime, Security or Domain Auditor* (quando aplicável);
     4. *Adversarial Final Auditor*.
