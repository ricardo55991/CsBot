# DISPATCH — implementer_data_2a_int_1

Papel: **Dataset and Metadata Implementer (dados/manifests/testes)** da FASE 2A-INTERMEDIATE.
Project root: `c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`
Idioma: Português Brasileiro em todos os artefatos e no handoff.

## 2026-11-09T01:07:52Z — mensagem do Orchestrator (a7196ff0-cf47-4d79-a99f-eaf19c722649)

Conteúdo consolidado (resumo fiel; o texto completo está no histórico da conversa):

### TAREFA 1 — M4: MANIFESTS (4 arquivos em `datasets/mirage_domains/intermediate_competitive/`)
1. `intermediate_demo_inventory_v1.json` — 26 campos do §10 em bloco `schema`, `records: []`, `record_count: 0`,
   `expected_pilot_target {min:20,max:50,...,preference}`, `acquisition_status: INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`,
   `accounting {accepted,rejected,quarantined,total_expected,total_observed,formula}`, `steamid_pseudonymization_policy`,
   `generated_utc`, `blockers[]`, `acceptance_and_exclusion_criteria_applied` espelhando §7 com (0/0) explícito.
2. `intermediate_npz_manifest_v1.json` — schema §11, `records: []`, `record_count: 0`, `npz_count: 0`,
   `status: EMPTY_PENDING_ACQUISITION_ACCESS`, `dem_vs_npz_comparison {executed:false, reason: NO_INTERMEDIATE_DATA}`,
   `reused_pipeline_reference` apontando para o pipeline canônico real (caminho descoberto no repo, não inventado).
3. `pilot_download_manifest.json` — `dry_run:true`, `downloads_attempted:0`, `downloads_completed:0`, `bytes_downloaded:0`,
   alvos do §8, `source_authorization_status: PENDING_HUMAN_APPROVAL`, `signed_urls_persisted:0`, `secrets_persisted:0`,
   `resume_state:null`, `allowlist_domains` derivada da matriz de fontes, `audit_log_policy`, `generated_utc`.
4. `quarantine_manifest.json` — `records: []`, `record_count: 0`, esquema de 10 motivos, `total_quarantined:0`,
   `bytes_quarantined:0`, `status: EMPTY_NO_CANDIDATES`.

### TAREFA 2 — M7: `training_runs/intermediate_domain_study/intermediate_splits_proposal.json`
`proposal_status: DESIGN_ONLY_NOT_MATERIALIZED`; `materialization_blocked_reason: LESS_THAN_50_DEMOS_AVAILABLE`;
70/15/15 por partida completa; unidade de split = match_id/demo_id com grouping_keys; holdouts obrigatórios
(unseen_players, unseen_stacks, recent_matches, cross_domain_holdout) com definição/critério/teste; matriz de leakage
(mesma partida, mesma demo, squad recorrente, mesmos jogadores, sequências adjacentes) com regra + teste;
`current_counts` com (0/0) explícito; `minimum_viable_demo_count: 50`; pilot 20–50.

### TAREFA 3 — M8: `tests/test_phase2a_intermediate_domain.py` com os 20 testes nomeados da §20
Nomes exatos; nada de fachada; cada teste deve falhar se a regra for violada; skips apenas se fisicamente impossível
(com `pytest.skip("NOT_EXECUTABLE_NO_INTERMEDIATE_DATA")`), mantendo asserção executável sobre contrato.
Proibido alterar a suíte existente de 16 arquivos ou o runtime C#.

### Proibições
Sem dados fictícios; não tocar `datasets/mirage_v2/**`, `training_runs/positioning_v2_real_temporal/**`, `src/**`,
`models/**`, catálogo, shards, sidecars, manifests, checkpoints; não editar `domain_contract_v1.json`,
`professional_manifest_reference.json`, `acquisition_source_matrix.json`, os 4 relatórios do pesquisador,
`tools/intermediate_demo_acquisition/*`; não escrever artefatos de outro agente (ct/tr standardization,
professional_vs_intermediate, spot_domain_coverage, unmapped_intermediate_clusters, pilot_corpus_quality,
domain_training_strategy.md, scale_up_recommendation.md); não treinar/avaliar/ONNX/C#; não baixar demos;
sem selos humanos (usar AGENT_REVIEWED / AUTOMATED_CHECK_PASS).

### Verificação obrigatória
pytest do arquivo novo (-v, saída completa); `pytest tests -q`; parse+contagem+bytes+SHA-256 dos 5 JSONs;
varredura de segredos/URLs assinadas; prova de que `datasets/mirage_v2/**` e `full_training/**` não mudaram.

### Handoff
`.agents/teamwork/implementer_data_2a_int_1/handoff.md` com Observation / Logic Chain / Caveats / Conclusion /
Verification Method / Labels de verificação.

## 2026-11-09T01:10:13Z — mensagem do Orchestrator (exigências adicionais do Sentinel sobre M8)

1. **Proibido `assert True` / asserção tautológica.** Sem resultado verdadeiro independente do estado do repositório.
2. **Proibido skip sem justificativa** listada no handoff (teste, motivo, asserção executável remanescente). Meta: 0 skips.
3. **Proibido `0/0` como aprovação.** Contagem zero não pode gerar PASS disfarçado; deve gerar asserção sobre contrato
   (ou skip justificado). É a Regra 03 do AGENTS.md aplicada a testes.
4. **A suíte tem que falhar quando a regra é violada** — cada teste precisa de um cenário de entrada que o reprove.
5. Handoff deve conter o **output bruto e literal** de `python -m pytest tests/test_phase2a_intermediate_domain.py -v`,
   com a linha final de contagem real; confirmar `records: []` + contabilidade explícita com `numerator`/`denominator`
   `0`/`0` e `status`; e a contagem de 53 spots lida do catálogo real com caminho + hash.
