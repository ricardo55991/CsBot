# Regra 13: Seleção Inteligente de Testes (`13-smart-testing`)

**A execução de testes automatizados é estritamente condicionada ao blast radius e aos componentes físicos alterados.**

---

## 1. Mapeamento por Tipo de Modificação
Seguindo a matriz formal de impacto (`.agents/contracts/test_impact_matrix.json`):

1. **Documentação, Markdown, Pesquisas e Relatórios**:
   - Executar apenas validação de sintaxe, existência, tamanho, integridade de links e caminhos relativos.
   - **É terminantemente proibido executar `dotnet test`, compilar o projeto C# ou rodar a suíte Python completa.**

2. **JSONs Estáticos, Manifests e Contratos Não Executáveis**:
   - Executar validação de schema (`jsonschema`), parsing e consistência de chaves.
   - Não executar testes de runtime sem consumidor alterado.

3. **Scripts Python Isolados de Tooling ou Hooks**:
   - Executar validação de compilação sintática (`python -m py_compile`) e os testes unitários do módulo afetado.
   - Não executar suíte completa de ML ou C#.

4. **DataLoader, Datasets ou Labels**:
   - Executar testes de integridade de batches, leakage e contabilidade de classes.
   - Não executar compilação ou testes de C# se nenhum contrato compartilhado com o C# foi alterado.

5. **Código C# Localizado (`src/CsBotManager/`)**:
   - Executar compilação do projeto e testes com filtro de categoria/classe (`--filter`).
   - A suíte completa de 340 testes de C# é reservada exclusivamente para o fechamento canônico de fase (Phase Gate Tier 4) ou alterações transversais no core da FSM.

---

## 2. Test Plan Obrigatório
Antes de rodar qualquer teste em tarefas de Tier 2 ou superior, documentar o plano de teste (`test_plan.json`) justificando os testes selecionados e as suítes puladas.
