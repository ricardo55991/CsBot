# Relatório Final Canônico: Homologação da Governança CsBot 1.2 Lean (`governance_1_2_lean_final_report.md`)

**Fase:** `GOVERNANCE_1_2_LEAN_MIGRATION`  
**Versão Homologada:** `1.2.0-lean`  
**Executor:** Agente Principal (Single-Agent First)  
**Data:** 2026-11-09  
**Veredito Canônico:** `CSBOT_GOVERNANCE_1_2_LEAN_READY`

---

## 1. Sumário Executivo

A Governança CsBot foi formalmente atualizada da versão `1.1.0-full` para a versão `1.2.0-lean`.
Esta atualização resolve o problema crítico de alto consumo de tokens, saturação de contexto e latência operacional, através da eliminação de sobrecargas redundantes (múltiplos subagentes em cascata, leituras repetidas dos mesmos arquivos, testes fora do blast radius e loops provocados por avisos cosméticos de hooks).

Todos os pilares inegociáveis de governança científica do projeto CsBot permanecem **100% intactos e ativos**:
- Proibição absoluta de contaminação do Test Set e Final Holdout (Regra 02);
- Invariante rigoroso de `support = 0 -> N/A` (Regra 03);
- Rotulagem mandatória de dados sintéticos ou templados (Regra 04);
- Integridade exclusiva de homologação humana (Regra 05);
- Proteção de artefatos sensíveis e contratos (Regra 06);
- Proibição de avanço automático de fase (Regra 08);
- Evidência bruta materializada antes de qualquer afirmação (Regra 01).

---

## 2. As Cinco Novas Regras Estruturantes

1. **`10-single-agent-first`:** Toda tarefa se inicia e é prioritariamente resolvida pelo agente principal. Subagentes só são instanciados sob necessidade estrita de responsabilidade independente. Default: `default_subagents = 0`.
2. **`11-no-nested-subagents`:** Proibição irrestrita de subagentes chamarem `invoke_subagent`, iniciarem sessões de Teamwork ou delegarem trabalho. Profundidade máxima de execução = 1.
3. **`12-no-redundant-file-reads`:** Eliminação da leitura em cascata dos mesmos arquivos extensos. Adoção obrigatória de **Evidence Packets** (extratos <= 200 linhas) e cache indexado por hash SHA-256 (`artifact_digest_index.json`).
4. **`13-smart-testing`:** Seleção inteligente de testes orientada pelo blast radius (`test_impact_matrix.json`). Alterações documentais e de relatórios proíbem expressamente a compilação de código C# ou execução de `dotnet test`.
5. **`14-lean-reporting`:** Proibição de relatórios narrativos duplicados por múltiplos subagentes. Comunicação em tempo de execução via JSONs estruturados concisos e apenas 1 relatório consolidado Markdown no encerramento.

---

## 3. Matriz de Tiers Reclassificada (Regra 07)

| Tier de Risco | Escopo / Tipos de Tarefas | Limite de Subagentes | Escopo de Testes Permitido |
|---|---|---|---|
| **Tier 1 (Baixo)** | Docs, Markdown, relatórios, JSON, pesquisas, minutas | **0 subagentes** | Verificação de sintaxe, links e caminhos relativos (sem `dotnet test`) |
| **Tier 2 (Moderado)** | Script Python de tooling, hook, parser, teste pontual | **0 ou 1 subagente** | `py_compile` e teste direcionado da ferramenta alterada |
| **Tier 3 (Alto)** | DataLoader, labels, splits, contratos de dataset | **Máximo 2 subagentes** | Testes de batch, leakage e contabilidade (sem testes C#) |
| **Tier 4 (Crítico)** | Treino mestre, checkpoint `.pt`, ONNX, deploy C# | **Máximo 4 subagentes** | Suíte C# completa (340 testes) e paridade estrita de inferência |

---

## 4. Reclassificação Granular de Hooks

- **Blocking Permanente (Invioláveis):**
  - `protect-sensitive-files`: Intercepta qualquer alteração em checkpoints, modelos, perfis e contratos sem autorização de 5 campos.
  - `pre-training-gate`: Aborta qualquer treinamento que tente consumir dados do split Test.
  - `secret-leakage-gate`: Bloqueia credenciais, tokens ou cookies persistidos.
  - `stop-condition-evidence-gate`: Bloqueia conclusão de fase sem comprovação de artefatos físicos brutos.
- **Audit-Only por Padrão com Orçamento de Avisos:**
  - `validate-generated-report`: Opera em modo `audit-only` para formatação e estilo. Mantém bloqueio estrito apenas para violações críticas (contaminação de Test, dados sintéticos sem label, suporte zero como número e segredos).
  - `hook_warning_budget`: Orçamento de no máximo 1 tentativa de reescrita; warnings cosméticos não bloqueiam a ferramenta.

---

## 5. Auditoria de Não-Mutação de Arquivos de Produto (§27)

Foi executada a verificação física em disco sobre os diretórios de produto:
- `src/` (Código C# de runtime): **0 arquivos alterados (339 arquivos de produto intactos)**;
- `datasets/mirage_v2/` (Corpus profissional): **0 arquivos alterados, 100% preservado**;
- `models/` e `checkpoints/`: **0 arquivos alterados**;
- `training_runs/positioning_v2_real_temporal/`: **Preservado sob o marcador imutável de pausa**.

---

## 6. Resultados dos Testes de Homologação

A suíte canônica de testes específicos da Governança Lean (`tests/test_governance_1_2_lean.py`) foi executada:
- **Comando:** `pytest tests/test_governance_1_2_lean.py -v`
- **Total de Testes:** 30
- **Aprovados:** 30 (100.00%)
- **Falhas / Erros:** 0
- **Duração:** 0.18s

---

## 7. Telemetria de Eficiência da Própria Execução (§28)

Conforme exigido pelo §28, a própria migração da governança foi conduzida sob o modelo lean:
- `subagents_spawned`: 0 (Meta: <= 1) -> **PASS**
- `nested_subagents`: 0 (Meta: 0) -> **PASS**
- `dotnet_test_runs`: 0 (Meta: 0) -> **PASS**
- `full_redteam_runs`: 0 (Meta: 0) -> **PASS**
- `repeated_reads` sem justificativa: 0 (Meta: 0) -> **PASS**
- `long_markdown_reports`: 1 (`governance_1_2_lean_final_report.md`) -> **PASS**
- `product_files_modified`: 0 (Meta: 0) -> **PASS**

---

## 8. Veredito Final

Com 100% dos 20 gates de aceitação satisfeitos, 30/30 testes automatizados aprovados e comprovação física de não-mutação dos arquivos de produto, emite-se o veredito:

```
CSBOT_GOVERNANCE_1_2_LEAN_READY
```

Conforme a Regra 08 (Proibição de Avanço Automático de Fase), nenhuma fase subsequente (como o retorno à pesquisa da Fase 2A-Intermediate ou retomada do treinamento da Fase 3A.3-B) será iniciada de forma autônoma. O turno é encerrado para comando e homologação do usuário humano.
