# Guia de Migração: Governança CsBot 1.2 Lean (`governance_1_2_lean_migration_guide.md`)

**Versão da Governança:** `1.2.0-lean`  
**Data:** 2026-11-09  
**Público-Alvo:** Desenvolvedores, Mantenedores e Agentes de IA do Projeto CsBot

---

## 1. Visão Geral da Mudança

A Governança 1.2 Lean substitui o modelo anterior de criação maciça de subagentes por um modelo ágil e parcimonioso denominado **Single-Agent First**.
O objetivo é reduzir em até 80% o consumo de tokens e a latência de execução sem enfraquecer nenhum dos pilares de governança (proibição de contaminação de Test, zero support como N/A, integridade de segredos e evidência física antes de afirmações).

---

## 2. Como Operar em Cada Tier

### Tier 1: Baixo Risco (Documentação, Relatórios, JSONs, Pesquisas)
- **Como era antes:** Criava-se Orquestrador, Implementer, Data Auditor e Success Auditor. Cada um relia os arquivos de 800 linhas e gastava 300.000 tokens.
- **Como operar agora:**
  - O **agente principal resolve tudo diretamente** no turno ativo.
  - Nenhum subagente é criado (`default_subagents = 0`).
  - **Não rodar `dotnet test` nem build C#**. Validar apenas JSON/Markdown localmente.
  - Produzir apenas 1 relatório consolidado Markdown ao final.

### Tier 2: Médio Risco (Scripts Python de Tooling, Hooks, Parsers)
- **Como operar:**
  - O agente principal implementa o script e executa `python -m py_compile <script.py>`.
  - Executa apenas o teste direcionado daquele script (`pytest tests/test_especifico.py`).
  - Se for estritamente necessária uma segunda opinião independente, instanciar no máximo **1 revisor** com um Evidence Packet cirúrgico (máximo 200 linhas de extrato).

### Tier 3: Alto Risco (DataLoader, Labels, Splits, Métricas)
- **Como operar:**
  - Máximo de **2 subagentes**: 1 Implementador e 1 Auditor combinado de Matemática, ML e Proveniência.
  - Testar apenas o módulo de dados e leakage. Não compilar C# se a alteração não tocar contratos compartilhados.

### Tier 4: Crítico (Novos Checkpoints Master .pt, ONNX, Deploy em Runtime C#)
- **Como operar:**
  - Permitidos até **4 subagentes especializados**.
  - Apenas neste momento executa-se a suíte completa de C# (`dotnet test` com 340 testes) e a verificação completa de paridade ONNX.

---

## 3. Guia de Procedimento para Rollback

Caso seja necessário reverter para a configuração anterior da Governança 1.1:
1. Consultar o manifesto de rollback: `governance_1_2_lean_rollback.json`;
2. Restaurar o arquivo `AGENTS.md` a partir do backup ou histórico do Git;
3. Restaurar `.agents/hooks/hook_mode.json` para `"mode": "blocking"`;
4. Remover as regras 10 a 14 de `.agents/rules/`;
5. Nenhuma alteração em código C# (`src/`) ou datasets (`datasets/`) foi realizada, garantindo 100% de integridade dos artefatos de produto.
