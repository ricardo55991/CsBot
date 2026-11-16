# Regra 11: Proibição Absoluta de Subsubagentes (`11-no-nested-subagents`)

**Nenhum subagente pode criar outros subagentes, iniciar Teamwork ou delegar tarefas.**

---

## 1. Proibições Estritas para Subagentes
Nenhum subagente tem permissão para:
- Chamar a ferramenta `invoke_subagent`;
- Criar outro agente ou subagente;
- Iniciar sessões de `/teamwork` ou `/boost`;
- Delegar tarefas a terceiros;
- Criar auditor próprio ou facilitador sucessor;
- Iniciar outro Orchestrator.

---

## 2. Profundidade Máxima de Execução
A profundidade da árvore de execução no projeto CsBot é estritamente de nível 1:
```
Usuário
  └── Agente Principal (Orchestrator)
        └── Subagente Especialista (Apenas se Tier exigir)
```

Qualquer tentativa de invocação aninhada deve ser imediatamente abortada com o status:
`NESTED_SUBAGENT_BLOCKED`

Registrando no log:
- `agent_id`
- `parent_agent_id`
- `requested_role`
- `blocked_reason = "Nested subagents are strictly prohibited by Rule 11"`
