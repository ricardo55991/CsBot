# Diferencial Arquitetural: Governança CsBot 1.1 vs. Governança 1.2 Lean (`governance_1_2_lean_diff.md`)

**Versão Anterior:** `1.1.0-full`  
**Nova Versão:** `1.2.0-lean`  
**Data:** 2026-11-09  
**Status:** `MIGRATED_AND_VERIFIED`

---

## 1. Resumo Comparativo das Mudanças

| Componente | Governança 1.1 (Anterior) | Governança 1.2 Lean (Atual) |
|---|---|---|
| **Ponto de Partida** | Criação imediata de orquestrador + subagentes | **Single-Agent First:** Início direto no agente principal |
| **Default Subagents** | 4 a 5 subagentes instanciados por tarefa | **0 subagentes** (`default_subagents = 0`) |
| **Subsubagentes** | Não expressamente proibidos em profundidade | **Estritamente proibidos** (`NESTED_SUBAGENT_BLOCKED`) |
| **Leitura de Arquivos** | Cada subagente relia arquivos de 800+ linhas | **Cache por hash** + **Evidence Packet** (extratos <= 200 linhas) |
| **Seleção de Testes** | `dotnet test` e suíte completa executados a cada passo | **Smart Testing:** Condicionado estritamente ao blast radius |
| **Modo de Hooks** | Hooks com bloqueio global frequente por avisos cosméticos | **Audit-only para relatórios/estilo**; bloqueio apenas em falhas críticas |
| **Loops de Hooks** | Múltiplas reescritas forçadas por warnings de baixa relevância | **Hook Warning Budget:** Máximo 1 tentativa, warning não bloqueia |
| **Relatórios** | 4 a 5 relatórios narrativos intermediários + consolidador | Apenas JSON estruturado em runtime + **1 Markdown consolidado** |

---

## 2. Detalhamento dos Novos Contratos e Regras

### A. Novas Regras Adicionadas em `.agents/rules/`
1. `10-single-agent-first.md`: Princípio de execução direta pelo agente principal para tarefas documentais, relatórios, JSON e testes específicos.
2. `11-no-nested-subagents.md`: Proibição absoluta de subagentes chamarem `invoke_subagent` ou delegarem.
3. `12-no-redundant-file-reads.md`: Proibição de reabertura integral de arquivos já conhecidos sem mutação física de hash.
4. `13-smart-testing.md`: Seleção estrita de testes por blast radius (ex: Proibido `dotnet test` em alterações de Markdown).
5. `14-lean-reporting.md`: Limitação de comunicação em runtime a JSON e 1 relatório final.

### B. Regras Atualizadas
- `07-independent-validation.md`: Reestruturada para a Matriz de Tiers Lean (Tier 1 = 0 subagentes; Tier 2 = 0 ou 1; Tier 3 = máx 2; Tier 4 = máx 4).
- `AGENTS.md`: Atualizado para versão `1.2.0-lean` incorporando as regras 10 a 14.

### C. Novos Contratos Estruturados
- `.agents/contracts/evidence_packet_v1.schema.json`: Schema formal para pacotes de evidência.
- `.agents/contracts/test_impact_matrix.json`: Matriz de impacto de teste.
- `.agents/cache/artifact_digest_index.json`: Índice de digest e metadados por hash.
- `.agents/audit/execution_efficiency.json`: Telemetria de eficiência de execução.
- `.agents/hooks/update_artifact_digest.py`: Script determinístico de atualização de cache.
