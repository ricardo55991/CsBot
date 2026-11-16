# Diferencial da Otimização Operacional e Limpeza (`operational_optimization_diff.md`)

**Versão da Governança:** `1.2.0-lean`  
**Data:** 2026-11-09  
**Status:** `APPLIED_AND_VERIFIED`

---

## 1. Otimização de Eventos dos Hooks (`.agents/hooks.json`)

- **PreToolUse:**
  - Removido `validate-generated-report` (economizando execuções de Python a cada comando e gravação de arquivos).
  - Mantidos exclusivamente bloqueios preventivos: `protect-sensitive-files` e `pre-training-gate`.
- **PostToolUse:**
  - Removido `validate-generated-report`.
  - Em `post-test-audit`, adicionado retorno imediato quando o comando não for um runner de teste automatizado (`pytest`, `unittest`, `dotnet test`).
- **Stop:**
  - Mantido `validate-generated-report` (em modo audit-only para estilo e bloqueio apenas em falhas críticas).
  - Mantido `stop-condition-evidence-gate`.

---

## 2. Novas Políticas Adicionadas em `AGENTS.md` e `.agents/rules/`

- **Regra 15 (`15-analytics-script-first.md`):** Processamento local determinístico via scripts Python para dados volumosos (JSONs grandes, Parquet, NPZ, contagens e reconciliações). Proibido despejar dumps no contexto.
- **Regra 16 (`16-surgical-terminal-output.md`):** Limitação de comandos no terminal para saídas concisas (status, contagem, log path). Proibidas listagens recursivas desnecessárias.

---

## 3. Gestão de MCPs e Compactação

- **`workspace_mcp_inventory.json`:**
  - `sequential-thinking`: Mantido ativo para raciocínio estruturado complexo sob demanda.
  - `godot-mcp-toolkit`: Desabilitado no escopo exclusivo do CsBot, preservando configuração global para o projeto `Vaelun`.
- **`compact_policy.md`:** Checklist operacional de 7 itens mandatórios para o disparo de `/compact`.

---

## 4. Quarentena Controlada Local

- Adicionado `.cleanup/quarantine/` ao `.gitignore`.
- Movidos 11 arquivos efêmeros (.tmp, .bak) para `.cleanup/quarantine/cache/` com manifesto reverso.
- Zero arquivos de histórico ou produto excluídos permanentemente.
