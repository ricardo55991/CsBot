---
name: csbot-graph-impact
description: Integra o grafo de conhecimento Graphify (graphify-out/) ao planejamento e auditoria de mudanças arquiteturais no CsBot, mapeando entry points, writers, readers, estado autoritativo, fallbacks, caches, side effects, telemetria, testes e blast radius nos fluxos críticos. Use antes de planejar ou modificar qualquer código C# ou pipeline Python do CsBot.
---

# CsBot Graph Impact

Esta Skill integra o grafo de conhecimento estrutural do **Graphify** (`graphify-out/graph.json` e `GRAPH_REPORT.md`) ao planejamento de engenharia e auditoria de impacto no projeto CsBot, prevenindo regressões silenciosas, estados concorrentes e quebras de contrato entre C# (`CsBotManager`) e Python (treinamento/ONNX).

## As 10 Dimensões Obrigatórias de Mapeamento de Impacto

Antes de aprovar um plano de implementação ou auditar uma alteração de código no CsBot, mapeie obrigatoriamente os 10 atributos abaixo para o fluxo afetado:

1. **`entry_points`**: Métodos de entrada de ciclo/evento (ex: `OnTick`, handlers de eventos CS2, comandos `!debug`, CLI entrypoints).
2. **`writers`**: Todas as classes/métodos que mutam ou sobrescrevem o estado ou propriedade alvo.
3. **`readers`**: Todos os consumidores downstream que leem o estado para tomada de decisão, movimentação ou inferência.
4. **`authoritative_state`**: Qual objeto/propriedade detém a verdade canônica única (Single Source of Truth) naquele instante do tick/round.
5. **`fallbacks`**: Caminhos de contingência acionados quando o modelo ONNX, navmesh ou estado principal falha ou retorna inválido.
6. **`caches`**: Buffers temporais, históricos de ticks, dicionários estáticos ou estados memoizados que podem reter valores obsoletos (stale state).
7. **`side_effects`**: Efeitos colaterais sobre outros subsistemas (ex: alterar movimento que cancela plant de C4 ou reseta cooldown de jump).
8. **`telemetry`**: Eventos de log e contadores emitidos pelo fluxo para permitir auditoria pela `csbot-runtime-validation`.
9. **`tests`**: Testes unitários e de integração existentes que cobrem os nós afetados (e lacunas de cobertura).
10. **`blast_radius`**: Lista completa de arquivos, classes, contratos JSON/ONNX e relatórios impactados direta ou transitivamente.

## Os 5 Grafos Prioritários do CsBot

Todo diagnóstico de mudança no runtime deve cruzar a análise com os 5 fluxos críticos catalogados em [priority_graphs_catalog.md](./references/priority_graphs_catalog.md):

1. `Positioning Transformer → GoalPosition`
2. `BombObjectiveState → C4 movement`
3. `ONNX Jump request → JumpExecutionGate → usercmd`
4. `Recovery request → MovementArbitrator → physical movement`
5. `Economy decision → buy command → inventory confirmation`

## Procedimento Operacional Passo a Passo

1. **Verificar o Grafo Graphify**: Confirme que `graphify-out/graph.json` existe e está atualizado no workspace.
2. **Executar a Análise de Impacto**: Rode [analyze_graph_impact.py](./scripts/analyze_graph_impact.py) com os argumentos canônicos:
   ```powershell
   python .agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py `
     --workspace-root . `
     --graph-path graphify-out/graph.json `
     --target-flow all `
     --output-json artifacts/graph_impact_report.json `
     --strict
   ```
   - **Regra de `--dry-run`**: A execução com `--dry-run` realiza validação estrutural e emite veredito **`CONDITIONAL`** com `data_nature: SIMULATED` (em respeito à Regra `01-evidence-before-claims`, pois `PASS` exige inspeção real sobre o grafo e artefatos brutos do workspace).
3. **Cruzar com o Catálogo Prioritário**: Consulte [priority_graphs_catalog.md](./references/priority_graphs_catalog.md) para mitigar riscos de múltiplos `writers` concorrentes ou `caches` sem invalidação.
