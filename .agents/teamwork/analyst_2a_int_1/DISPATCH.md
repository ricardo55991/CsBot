# DISPATCH — analyst_2a_int_1

## 2026-11-09T01:07:52Z

Remetente: Orchestrator (`a7196ff0-cf47-4d79-a99f-eaf19c722649`)
Papel: **Analista Espacial e Estatístico (M5 + M6)** da FASE 2A-INTERMEDIATE.
Escreve artefatos de análise; **não** implementa código de produção.

- Project root: `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`
- Working dir: `.agents/teamwork/analyst_2a_int_1/`
- Idioma: Português Brasileiro.

### Contexto obrigatório
1. `.agents/teamwork/ORIGINAL_REQUEST.md` — integral; foco em §12, §13, §14, §15, §16, §17, §18, §21, §22.
2. `AGENTS.md` — Regras 01–09 (Regra 01 hash 64 hex / caminhos relativos / `(N/D)`; Regra 03 `support=0` → `N/A`; Regra 04 rótulos de natureza; Regra 05).
3. Skills `csbot-math-logic-auditor` e `csbot-dataset-forensics`.

### Fato estabelecido (não negociável)
Não existe nenhum dado intermediário: 0 `.dem`, 0 NPZ intermediários, 0 partidas. Veredito de aquisição: `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`. Toda métrica de §12/§13/§14/§15(coluna intermediária)/§16/§17 tem denominador zero no lado intermediário → `status: "NOT_EXECUTABLE_NO_INTERMEDIATE_DATA"`, `numerator: 0`, `denominator: 0`, valor `N/A` (nunca `0.0`, nunca `0.0%`). Proibido inventar números.

### Escopo — 8 arquivos, exclusivamente meus (em `training_runs/intermediate_domain_study/`)
1. `ct_standardization_analysis.json` (§12)
2. `tr_standardization_analysis.json` (§13)
3. `professional_vs_intermediate.json` (§14)
4. `spot_domain_coverage.json` (§15, 53 spots, 14 estatísticas, 7 classificações, 26 spots sem suporte profissional)
5. `unmapped_intermediate_clusters.json` (§16, 7 classificações, `catalog_append_requires_human_review: true`)
6. `pilot_corpus_quality.json` (§17, 8 critérios + 7 problemas, `hypothesis_status: UNPROVEN_PENDING_DATA`)
7. `domain_training_strategy.md` (§18, 350+ linhas, estratégias A–E, recomendação condicional, `DECISION_DEFERRED_PENDING_INTERMEDIATE_DATA`)
8. `scale_up_recommendation.md` (60–140 linhas, 20–50 → 200+ demos, pré-condições, riscos, critérios de parada, §8 não escalar antes do piloto)

### Regras de dados
- `support = 0` → `N/A`; macro-médias com denominador de classes ativas; percentuais com `(N/D)`.
- Raciocínio não medido → `INFERRED`. Não incluir valor hipotético sem rótulo.
- Caminhos relativos ao repo; SHA-256 completos de 64 hex ao citar artefatos.
- Leitura somente-leitura; não recalcular corpus; métrica profissional ausente em artefato pronto → `NOT_AVAILABLE_IN_EXISTING_ARTIFACTS`.

### Proibições
Não escrever fora dos 8 arquivos. Não tocar em manifests, splits, testes, `tools/**`, `datasets/**`, `src/**`, `models/**`. Não modificar `datasets/mirage_v2/**`, `training_runs/positioning_v2_real_temporal/**`, catálogo de 53 spots. Não executar treinamento/Test/Holdout/ONNX/C#/shadow/MLMove V2/Jump Head. Não baixar demos. Não usar `VALIDATED`/`APPROVED`/`PASS` como veredito. Sem arquivo vazio ou placeholder cosmético.

### Aviso de integridade (verbatim)
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Verificação obrigatória (executar e reportar)
1. `json.load` de cada JSON.
2. Bytes + SHA-256 (64 hex) de cada um dos 8 arquivos, do disco.
3. Varredura provando ausência de métrica inventada: todo campo de métrica `N/A` + `0/0` ou `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`; **zero** ocorrências de `0.0%`.
4. Contagem de 53 spots lida do catálogo real (caminho + hash) e tipos 30/13/3/2/5.

### Handoff
`handoff.md` com Observation / Logic Chain / Caveats / Conclusion / Verification Method + `## Labels de verificação`; atualizar `progress.md` com `Last visited: <UTC>`; mensagem final ao Orchestrator (`d7c79efa-81cf-40df-b317-b27a0d0506b8`), **não** ao Sentinel.
