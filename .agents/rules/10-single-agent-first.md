# Regra 10: Single-Agent First (`10-single-agent-first`)

**Toda tarefa começa e é preferencialmente resolvida pelo agente principal.**

---

## 1. Princípio de Execução Direta

O agente principal executa diretamente tarefas de:
- Pesquisa de fontes e viabilidade;
- Documentação e relatórios Markdown;
- Manifests e estruturas JSON;
- Inventários e catálogos;
- Minutas e propostas textuais;
- Correções localizadas de código e formatação;
- Scripts simples de tooling;
- Testes específicos e direcionados;
- Análise de arquivos materializados;
- Atualização pequena de Hooks ou Skills;
- Extração e verificação de evidências;
- Comparação de artefatos;
- Auditoria reproduzível por script determinístico.

---

## 2. Condição de Criação de Subagente

Subagente só pode ser criado quando houver responsabilidade independente que **não** possa ser atendida adequadamente por:
1. Script determinístico;
2. Teste direcionado;
3. Hook de governança;
4. Revisão direta do agente principal;
5. Reprodução local.

## 3. Defaults Operacionais
- `default_subagents = 0`
- `spawn_only_when_required = true`
- `nested_subagents = false`
- `only_main_agent_can_delegate = true`
- `kill_all_on_completion = true`
