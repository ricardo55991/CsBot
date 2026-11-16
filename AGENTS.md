# Diretrizes e Regras de Governança do Projeto CsBot (AGENTS.md)

**Versão da Governança:** `1.2.0-lean`  
**Escopo:** Regras inegociáveis de governança, integridade científica, parcimônia operacional, economia de tokens, auditoria forense e validação de engenharia para o projeto **CsBot** no Google Antigravity. Todas as regras abaixo têm escopo `always_on` em todo o repositório.

---

## `01-evidence-before-claims` — Evidência Bruta Antes de Qualquer Afirmação

Nenhuma conclusão `PASS` pode ser emitida sem a apresentação explícita de:
- **Artefato bruto materializado** gerado pela execução real (o arquivo DEVE existir no disco com tamanho > 0 bytes e ser carregável);
- **Caminho do artefato**: em relatórios versionados/documentos canônicos, os caminhos devem ser estritamente relativos à raiz do repositório (ex: `tools/...`, `src/...`, `reports/...`). Caminhos absolutos são permitidos apenas em logs temporários/locais de execução não publicados;
- **Hash SHA-256 completo** (exatamente 64 caracteres hexadecimais, sem truncamento, conferido em tempo de execução diretamente no disco);
- **Comando reproduzível** exato executado no terminal;
- **Fórmula de agregação** explícita com numerador e denominador explícitos `(N/D)` para qualquer percentual ou proporção;
- **Classificação de natureza do dado**: `REAL`, `SIMULATED`, `TEMPLATED`, `SYNTHETIC` ou `INFERRED`.

> **Regras de Bloqueio**:
> 1. Relatório executivo em Markdown ou PDF nunca é evidência suficiente por si só. Toda afirmação em relatório deve apontar para o artefato bruto verificável que a sustenta.
> 2. Relatórios com tabelas hardcoded sem script gerador e artefato `.json` de telemetria equivalente são sumariamente rejeitados como `FAIL`.
> 3. Datasets ou splits apenas planejados ou declarados sem arquivos físicos `.parquet`/`.npz` materializados no disco não podem compor manifests nem relatórios de prontidão.

---

## `02-no-test-contamination` — Proibição Absoluta de Contaminação do Test Set

Os conjuntos `Test` e `Holdout Final` são estritamente reservados para avaliação canônica final e **não podem participar** de:
- Treinamento direto ou indireto;
- Escolha de época ou seleção de checkpoint (`best_checkpoint`);
- Seleção entre experimentos, hiperparâmetros ou seeds;
- Calibração de probabilidades, dropout ou temperatura;
- Definição ou ajuste de thresholds operacionais;
- Tuning de pesos de loss ou curriculum;
- Escolha de arquitetura, cabeças (heads) ou features.

> **Exceção e Liberação Condicional Canônica**:
> O conjunto `Test` pode ser referenciado e executado **exclusivamente** quando TODAS as seguintes condições forem verdadeiras simultaneamente:
> 1. `mode = FINAL_EVALUATION`;
> 2. `checkpoint_frozen = true`;
> 3. `config_frozen = true`;
> 4. `thresholds_frozen = true`.
>
> **Regra de Bloqueio**: O hook `pre-training-gate` abortará qualquer comando de treinamento, fit, fine-tuning ou busca de hiperparâmetros se houver tentativa de uso do split `Test`. Qualquer violação invalida imediatamente a avaliação final e exige descarte do experimento.

---

## `03-zero-support-is-na` — Classe com Support Zero é Estritamente `N/A`

Qualquer classe, estado, setor ou spot que apresente `support = 0` no split avaliado deve ser reportado exclusivamente como **`N/A`**.

Para qualquer classe com `support = 0`, **é estritamente proibido calcular, exibir como número ou incluir em médias globais sem ressalva**:
- `Recall` (é estritamente proibido exibir `0.0%`, `100.0%` ou qualquer float);
- `F1-Score` (nunca substituir `0/0` por `0.0` ou `1.0`);
- `Balanced Accuracy` sobre classes ausentes;
- Percentual normalizado de linha na matriz de confusão (`confusion_normalized.csv`).

> **Regras de Bloqueio**:
> 1. Macro-médias devem explicitar o denominador de classes ativas: ex: `Macro-F1 = 0.7845 (sobre 3 de 5 classes com suporte > 0; classes raras N/A)`.
> 2. Substituir `0 / 0` por número, preencher classes ausentes copiando de outros splits ou mascarar silenciosamente o suporte zero invalida metodologicamente o relatório e resulta em veredito `FAIL`.

---

## `04-synthetic-data-labeling` — Rotulagem Obrigatória de Dados Sintéticos ou Templados

Todo dado, log, coordenada, vetor de histórico, mira geométrica, métrica ou artefato que seja sintético, simulado, templado, interpolado linearmente ou hardcoded deve ser explicitamente marcado com sua etiqueta de origem (`SIMULATED`, `TEMPLATED`, `SYNTHETIC` ou `INFERRED`).

**É terminantemente proibido apresentá-lo como**:
- Telemetria de runtime real do servidor CS2 (`REAL`);
- Extração de demo profissional real;
- Avaliação canônica de modelo;
- Inspeção ou captura humana;
- Métrica observada em partida.

> **Tratamento de Padrões e Variância**:
> - A detecção estática de `np.linspace`, baixa variância (`std == 0`) ou passo regular em tensores emite status **`WARNING_REQUIRES_PROVENANCE_REVIEW`**, exigindo auditoria de proveniência.
> - O veredito **`FAIL`** ocorre obrigatoriamente quando o dado sintético/templado **não estiver rotulado explicitamente** (`UNLABELED_SYNTHETIC`) ou quando for apresentado falsamente como `REAL`.
> - Em tabelas de benchmark, métricas sobre tensores sintéticos devem exibir a etiqueta visual `[SYNTHETIC_FEATURE]`.

---

## `05-human-review-integrity` — Integridade Exclusiva da Revisão Humana

Apenas o usuário humano pode atribuir os seguintes selos de homologação:
- `APPROVED_BY_USER`
- `REJECTED_BY_USER`
- `HUMAN_CAPTURE_IN_GAME`

> **Regras de Bloqueio**:
> 1. Scripts automatizados, subagentes ou pipelines não podem emitir relatórios afirmando "inspecionado manualmente", "validado pelo operador humano" ou equivalentes.
> 2. Toda validação conduzida por subagentes ou scripts deve carregar os rótulos canônicos: `AGENT_REVIEWED`, `AUTOMATED_CHECK_PASS` ou `SCRIPT_CAPTURED`. Nenhum agente ou script pode falsificar aprovação humana.
> 3. O auditor `csbot-report-skeptic` reprovará com `FAIL` qualquer entrega que contenha alegação de chancela humana sem confirmação explícita registrada na sessão.

---

## `06-sensitive-artifact-protection` — Proteção de Artefatos Sensíveis e Contratos

Antes de criar nova versão, sobrescrever ou modificar qualquer artefato sensível:
- Modelos e pesos exportados (`*.onnx`, `*.pt`);
- Perfil tático de mapa (`src/CsBotManager/MapProfiles/*.json`);
- Arquivos de divisão de dados (`*split*.json`, `*split*.parquet`, `*split*.npz`);
- Manifests (`*manifest*.json`);
- Catálogos (`*catalog*.json`);
- Contratos de schema (`*contract*.json`);
- Checkpoints de treinamento;

**É obrigatório registrar previamente**:
1. **Hash SHA-256 anterior completo** (64 caracteres) verificado diretamente no disco;
2. **Caminho do backup** imutável criado antes da alteração;
3. **Diff planejado** exato;
4. **Procedimento de rollback** determinístico;
5. **Justificativa técnica** documentada.

> **Regra de Bloqueio**: O hook `protect-sensitive-files` intercepta e bloqueia modificações nesses alvos sem arquivo de autorização formal contendo esses 5 campos válidos.

---

## `07-independent-validation` — Validação Independente Proporcional (Matriz Lean)

O agente ou subagente implementador **nunca pode ser o único validador de seu próprio trabalho**, mas a equipe de auditoria deve ser estritamente dimensionada de acordo com o Tier de risco para evitar desperdício de tokens:

1. **Tier 1 (Baixo Risco - Documentação, Markdown, JSON simples, inventário, relatórios, pesquisa, minutas, formatação)**:
   - Limite: **0 subagentes**. Executado e auto-validado diretamente pelo agente principal via scripts determinísticos e checagem de schema.
2. **Tier 2 (Médio Risco - Scripts Python isolados, Hooks localizados, Skills localizadas, parsers, testes unitários sem impacto em runtime)**:
   - Limite: **0 ou 1 subagente** (revisor pontual somente-leitura com Evidence Packet cirúrgico).
3. **Tier 3 (Alto Risco - DataLoader, labels, índices temporais, contratos de dataset, métricas, calibração, fine-tuning localizado, splits)**:
   - Limite: **Máximo 2 subagentes** (`Implementer` + `Auditor combinado de matemática, ML e proveniência`).
4. **Tier 4 (Crítico - Treinamento mestre, arquitetura ampla, checkpoint mestre, ONNX, integração C#, deploy, runtime, homologação final)**:
   - Limite: **Máximo 4 subagentes** com responsabilidades distintas e sem sobreposição:
     1. *Implementer / Executor*;
     2. *Mathematical, ML and Provenance Auditor*;
     3. *Runtime, Security or Domain Auditor* (quando aplicável);
     4. *Adversarial Final Auditor*.

---

## `08-no-automatic-phase-advance` — Proibição Absoluta de Avanço Automático de Fase

Nenhuma fase, subfase, retreinamento, exportação ou etapa de deploy pode ser iniciada imediatamente após o encerramento da anterior de maneira autônoma.

Ao emitir o veredito canônico:
- `PASS`
- `CONDITIONAL`
- `FAIL`

O assistente/agente DEVE **encerrar o turno de ferramentas imediatamente** e solicitar expressamente a aprovação e comando do usuário humano antes de executar qualquer passo da fase subsequente.

---

## `09-subagent-role-isolation` — Isolamento Estrito de Papéis e Devolução ao Orchestrator

Regras estritas de isolamento entre papéis de subagentes:
1. **`Implementer` não pode editar relatório de auditoria**: O implementador opera com `EnableWriteTools = true`, mas é terminantemente proibido de editar ou sobrescrever relatórios de auditoria (`*audit*.md`, `*audit*.json`, `*skeptic*.json`, `phase_gate_report.md`, `deliverable_evidence.json`) ou declarar-se `validator`.
2. **`Auditor` não pode alterar implementação**: Todo auditor opera estritamente com `EnableWriteTools = false` e é proibido de tocar em código-fonte (`src/`, `tools/`, `tests/`) ou datasets.
3. **`Success Auditor` e `Adversarial Reviewer` não corrigem falhas**: Se encontrarem qualquer divergência ou pendência, eles não tentam consertar. Emitem veredito `FAIL` detalhando os bloqueadores e **devolvem imediatamente ao `Orchestrator`**.

---

## `10-single-agent-first` — Princípio Single-Agent First

Toda tarefa começa e é preferencialmente resolvida pelo agente principal.
O agente principal executa diretamente tarefas de pesquisa, documentação, relatórios, manifests, JSONs, inventários, minutas, scripts de teste específicos e auditorias reproduzíveis por script.
Subagentes só podem ser instanciados quando houver responsabilidade independente que não possa ser atendida adequadamente por script determinístico ou teste local.
- `default_subagents = 0`
- `spawn_only_when_required = true`
- `nested_subagents = false`
- `only_main_agent_can_delegate = true`
- `kill_all_on_completion = true`

---

## `11-no-nested-subagents` — Proibição de Subsubagentes

Nenhum subagente pode chamar `invoke_subagent`, criar outro agente, iniciar Teamwork ou delegar tarefas. A profundidade da árvore de execução é estritamente 1 (Usuário -> Agente Principal -> Subagente).
Qualquer tentativa adicional resulta em `NESTED_SUBAGENT_BLOCKED`.

---

## `12-no-redundant-file-reads` — Proibição de Leituras Redundantes

Antes de abrir qualquer arquivo físico com `read_file`, o agente deve:
1. Consultar o `Evidence Packet` (`evidence_packet_v1`);
2. Consultar o índice de cache de digests (`artifact_digest_index.json`);
3. Reutilizar o conteúdo já carregado na sessão;
4. Utilizar intervalos pontuais de linhas (`StartLine`/`EndLine`).
Releitura integral é autorizada apenas em caso de mutação física de hash SHA-256 ou contestação explícita de dados.

---

## `13-smart-testing` — Seleção Inteligente de Testes por Blast Radius

A execução de testes automatizados é estritamente condicionada ao blast radius (`.agents/contracts/test_impact_matrix.json`):
- **Tarefas Documentais e de Relatórios:** Verificação de existência, Markdown/JSON válido e caminhos relativos. **Proibido executar `dotnet test` ou suíte completa de ML.**
- **Scripts Python Isolados:** `python -m py_compile` e teste específico do script.
- **DataLoader e Datasets:** Testes de lote, leakage e suporte de labels. Sem testes C#.
- **Código C# Localizado:** Build específico e testes com filtro de classe (`--filter`). Suíte de 340 testes apenas no gate final Tier 4.

---

## `14-lean-reporting` — Relatórios Enxutos e Canônicos

Durante a execução da tarefa, o registro de progresso ocorre exclusivamente via JSONs concisos (`progress.json`, `findings.json`, `test_result.json`, `execution_efficiency.json`).
No encerramento da fase, produz-se apenas **1 relatório canônico em Markdown** (`final_report.md` ou equivalente) acompanhado de `deliverable_evidence.json`. É proibida a criação de múltiplos relatórios narrativos por subagente ou relatórios de vitória vazios.

---

## `15-analytics-script-first` — Script First para Análise de Dados Volumosos

Para qualquer análise estatística, contagem, reconciliação ou validação volumosa de dados, é obrigatório utilizar scripts determinísticos locais em vez de despejar dados brutos na janela de contexto.
- Scripts processam os dados diretamente no disco e gravam relatórios JSON detalhados;
- O stdout no terminal deve emitir apenas resumo curto (status, contagem e caminho do relatório).

---

## `16-surgical-terminal-output` — Saídas Cirúrgicas no Terminal

Comandos executados no terminal devem emitir respostas cirúrgicas e compactas, evitando poluição de contexto e consumo desnecessário de tokens.
- Preferir contagens, filtros e resumos estruturados;
- Redirecionar logs extensos para arquivos em disco.

---

## Mapa de Skills de Governança do Workspace (`.agents/skills/`)

As diretrizes acima são operacionalizadas pelas seis Skills instaladas em `.agents/skills/`, com triggers estritamente restritos:
1. `csbot-phase-gate`: Controle de entrada, matriz de requisitos/evidências e emissão de veredito canônico. Invocada apenas no encerramento formal de fase ou gates de treino/ONNX/deploy.
2. `csbot-report-skeptic`: Auditoria adversarial sobre relatórios executivos. Invocada apenas em relatórios executivos de fase ou claims quantitativos relevantes (não a cada Markdown simples).
3. `csbot-dataset-forensics`: Auditoria forense de splits, leakage, Parquet, NPZ, proveniência e suporte de labels.
4. `csbot-model-validator`: Reprodução determinística de avaliação diretamente de checkpoints (`*.pt`), tratando classes com support zero como N/A.
5. `csbot-runtime-validation`: Padronização de build, testes, deploy, hashes e telemetria real do servidor CS2. Invocada apenas quando houver alteração de runtime C# ou deploy.
6. `csbot-graph-impact`: Mapeamento de impacto arquitetural e blast radius integrado ao Graphify. Invocada apenas em mudanças estruturais ou blast radius incerto.
