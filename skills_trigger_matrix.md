# Matriz de Triggers e Progressive Disclosure das Skills (`skills_trigger_matrix.md`)

- **Data de Geração**: `2026-11-07`
- **Escopo**: `.agents/skills/*` no workspace `CsBot`
- **Natureza do Dado**: `REAL` (extraído diretamente do frontmatter YAML dos 6 arquivos `SKILL.md` ativos)
- **Status de Revisão**: `AGENT_REVIEWED`

---

## 1. Matriz de Gatilhos de Ativação (Triggers)

No Antigravity `2.29.0`, apenas os campos `name` e `description` são injetados inicialmente no bloco `<skills>` do prompt de sistema. O modelo principal avalia a `description` (redigida em 3ª pessoa) para decidir quando carregar o `SKILL.md` correspondente.

| # | Nome da Skill (`name`) | Descrição Oficial de Trigger (`description`) | Eventos / Intenções que Disparam a Skill | Invocação Explícita (Slash / Menção) |
|---|---|---|---|---|
| 1 | `csbot-phase-gate` | *"Controla a entrada, execução e encerramento formal de fases do projeto CsBot, gerando snapshots de entrada, matrizes de requisitos/evidências e emitindo veredito canônico (PASS, CONDITIONAL ou FAIL). Use sempre ao iniciar, auditar ou encerrar qualquer fase, subfase, retreinamento ou entrega de engenharia no CsBot."* | Abertura de fase (`Fase 2.x`, `Fase 3A.x`), validação de pré-requisitos de etapa, fechamento de entrega ou emissão de veredito final. | `/csbot-phase-gate` ou menção a `csbot-phase-gate` |
| 2 | `csbot-report-skeptic` | *"Executa auditoria adversarial cética sobre relatórios executivos e entregas de fase do projeto CsBot para invalidar afirmações sem lastro e detectar os 12 padrões de falha metodológica ou documental. Use obrigatoriamente sobre toda entrega de fase antes da emissão do veredito no phase gate."* | Geração ou revisão de qualquer relatório executivo (`*report*.md`, `*report*.pdf`), reconciliação de métricas conflitantes ou auditoria pré-fechamento. | `/csbot-report-skeptic` ou acionamento automático pelo Hook B (`validate-generated-report`) |
| 3 | `csbot-dataset-forensics` | *"Audita forensemente datasets do CsBot (Parquet, NPZ, manifests e catálogos), verificando vazamento entre splits (leakage), reconciliação de contagens, integridade de linhas/sequências, proveniência de amostras, detecção de dados templados e suporte de labels. Use sempre ao construir, transformar, filtrar ou validar datasets de treinamento, validação e teste."* | Extração de demos, geração de `.parquet`/`.npz`, criação de splits `train/val/test`, auditoria de suporte de classes (`OBJECTIVE`, `SAVE`, spots) ou suspeita de leakage. | `/csbot-dataset-forensics` |
| 4 | `csbot-model-validator` | *"Reproduz deterministicamente a avaliação canônica de modelos PyTorch/ONNX do CsBot diretamente a partir de checkpoints e arrays brutos, garantindo invariantes de inferência e tratando classes com support zero como N/A. Use sempre para avaliar modelos, comparar checkpoints ou gerar métricas oficiais de Validation e Test."* | Avaliação offline de checkpoints `.pt` ou `.onnx`, cálculo de `MRR`, `Top-K`, `Macro F1`, matrizes de confusão ou comparação de seeds. | `/csbot-model-validator` |
| 5 | `csbot-runtime-validation` | *"Padroniza e audita o ciclo completo de validação em runtime real do servidor CS2 para o CsBot, cobrindo build, testes, deploy, verificação de hashes, captura !debug, C4, economia, Jump, recovery, spots, adaptações táticas e selamento da sessão. Use sempre para validar alterações de código C#/.NET ou modelos ONNX no servidor CS2."* | Build/deploy de `CsBotManager.dll`, testes em partida real no CS2, captura de logs `!debug`, validação de C4/economia/Jump/recovery. | `/csbot-runtime-validation` |
| 6 | `csbot-graph-impact` | *"Integra o grafo de conhecimento Graphify (graphify-out/) ao planejamento e auditoria de mudanças arquiteturais no CsBot, mapeando entry points, writers, readers, estado autoritativo, fallbacks, caches, side effects, telemetria, testes e blast radius nos fluxos críticos. Use antes de planejar ou modificar qualquer código C# ou pipeline Python do CsBot."* | Planejamento de refatoração ou feature em `src/CsBotManager/*.cs` ou `tools/`, análise de impacto (*blast radius*) ou rastreamento dos 5 fluxos prioritários. | `/csbot-graph-impact` |

---

## 2. Arquitetura de Progressive Disclosure

| Skill | Nível 1: Injetado no Contexto (`name` + `description`) | Nível 2: Carregado ao Ativar (`SKILL.md`) | Nível 3: Lido Sob Demanda (`references/*.md`) | Nível 4: Executado Fora da Janela (`scripts/*.py`) |
|---|---:|---:|---:|---:|
| `csbot-phase-gate` | ~310 bytes | `3.712 bytes` | `5.193 bytes` ([phase_gate_contract.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-phase-gate/references/phase_gate_contract.md)) | `17.712 bytes` ([run_phase_gate.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-phase-gate/scripts/run_phase_gate.py)) |
| `csbot-report-skeptic` | ~305 bytes | `3.906 bytes` | `5.368 bytes` ([skeptic_audit_checklist.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-report-skeptic/references/skeptic_audit_checklist.md)) | `20.425 bytes` ([audit_executive_report.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py)) |
| `csbot-dataset-forensics` | ~375 bytes | `3.938 bytes` | `4.185 bytes` ([dataset_forensics_protocol.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-dataset-forensics/references/dataset_forensics_protocol.md)) | `112.933 bytes` (6 scripts em `scripts/`) |
| `csbot-model-validator` | ~335 bytes | `3.547 bytes` | `3.916 bytes` ([model_eval_invariants.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-model-validator/references/model_eval_invariants.md)) | `18.658 bytes` ([validate_model_canonical.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-model-validator/scripts/validate_model_canonical.py)) |
| `csbot-runtime-validation` | ~355 bytes | `3.698 bytes` | `4.137 bytes` ([runtime_telemetry_contract.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-runtime-validation/references/runtime_telemetry_contract.md)) | `9.749 bytes` ([verify_runtime_session.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py)) |
| `csbot-graph-impact` | ~360 bytes | `3.835 bytes` | `7.869 bytes` ([priority_graphs_catalog.md](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-graph-impact/references/priority_graphs_catalog.md)) | `23.792 bytes` ([analyze_graph_impact.py](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py)) |
