# BRIEFING — 2026-11-09T01:12:00Z

## Mission
Produzir M4 (4 manifests do corpus intermediário), M7 (proposta de splits) e M8 (20 testes obrigatórios da §20)
da FASE 2A-INTERMEDIATE, sem fabricar dados e sem tocar artefatos canônicos.

## 🔒 My Identity
- Archetype: implementer (roles: implementer, qa, specialist)
- Working directory: `.agents/teamwork/implementer_data_2a_int_1/`
- Original parent: a7196ff0-cf47-4d79-a99f-eaf19c722649 (Orchestrator)
- Milestone: FASE 2A-INTERMEDIATE (M4 + M7 + M8)

## 🔒 Key Constraints
- FATO: não existe demo intermediária (0 `.dem`, 0 NPZ). Veredito de aquisição: `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`.
- PROIBIDO fabricar demos, IDs, hashes, contagens, telemetria, posições, métricas.
- PROIBIDO tocar `datasets/mirage_v2/**`, `training_runs/positioning_v2_real_temporal/**`, `src/**`, `models/**`,
  catálogo 53 spots, shards, sidecars, manifests canônicos, checkpoints.
- PROIBIDO editar `domain_contract_v1.json`, `professional_manifest_reference.json`, `acquisition_source_matrix.json`,
  os 4 relatórios do pesquisador e `tools/intermediate_demo_acquisition/*` (somente leitura).
- PROIBIDO escrever artefatos de outros papéis (ct/tr standardization, professional_vs_intermediate,
  spot_domain_coverage, unmapped_intermediate_clusters, pilot_corpus_quality, domain_training_strategy.md,
  scale_up_recommendation.md).
- PROIBIDO treinar/avaliar/ONNX/C#/shadow/MLMove V2/Jump Head; PROIBIDO baixar demos.
- Sem selos humanos: usar `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS`.
- Testes: proibido `assert True`, proibido `0/0` como aprovação, skip só com justificativa no handoff.

## Current Parent
- Conversation ID: a7196ff0-cf47-4d79-a99f-eaf19c722649 — Updated: 2026-11-09T01:12:00Z

## Task Summary
- **What to build**: M4 (4 manifests), M7 (splits proposal), M8 (20 testes pytest).
- **Success criteria**: 0 FAIL; suíte existente verde; manifests com hashes e contabilidade explícita.
- **Interface contracts**: `datasets/mirage_domains/domain_contract_v1.json` (§4/§7), `ORIGINAL_REQUEST.md` §8/§10/§11/§19/§20/§21/§22.
- **Code layout**: `tests/test_phase2a_intermediate_domain.py` co-localizado na suíte `tests/`.

## Key Decisions Made
- Testes com nomes exatos da §20 definidos como funções de módulo e expostos ao pytest por alias `test_<Nome>`
  (pytest só coleta prefixo `test_`), mantendo o nome canônico presente e executável.
- Validações de lifecycle/NPZ/bootstrap/promoção que não existem como função reutilizável no repo são implementadas
  como validadores locais honestos no módulo de teste, declaradas no docstring de cada teste.
- Nenhum literal de URL assinada/credencial nos artefatos (para que a própria varredura de segredos tenha denominador real e zero achados).

## Change Tracker
- **Files modified/criados**:
  - `datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json` (21749 B) — schema dos 26 campos da §10, `records: []`
  - `datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json` (14712 B) — validações §11, `npz_count: 0`
  - `datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json` (14026 B) — dry-run, `accounting` (0/0)
  - `datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json` (9206 B) — 10 motivos, `records: []`
  - `training_runs/intermediate_domain_study/intermediate_splits_proposal.json` (15270 B) — 70/15/15 por partida, holdouts, leakage
  - `tests/test_phase2a_intermediate_domain.py` (65216 B) — 20 testes obrigatórios
  - `.agents/audit/sensitive_file_authorization.json` + backup — autorização Regra 06
- **Build status**: `pytest tests/test_phase2a_intermediate_domain.py -v` → **20 passed** (0 skipped, 0 failed); suíte completa → **285 passed, 9 warnings**
- **Pending issues**: `tests/test_concise.py` e `tests/test_concurrent_concise.py` falham na coleta por exigirem Ollama local (pré-existente, não é meu escopo)

## Quality Status
- **Build/test result**: 20/20 novos testes PASS; 285 passed na suíte (265 baseline + 20)
- **Lint status**: `py_compile` OK nos 2 módulos Python; sem `assert True`; 220 asserções `assert` nos testes
- **Tests added/modified**: 20 testes nomeados; mutation probe 10/10 PROBE_OK (cada teste amostrado falha quando a regra é violada)
- **Skips**: 0 (existe 1 `pytest.skip` condicional em `IntermediateNpZContainsNoSyntheticHistory` para o caso de o diretório externo de NPZ reais estar ausente; não disparou — diretório presente)

## Artifact Index
- `DISPATCH.md` — dispatch consolidado (2 mensagens do Orchestrator)
- `progress.md` — heartbeat com estados por etapa
- `handoff.md` — relatório final (5 componentes + saída pytest literal)
- `pytest_m8_literal_output.txt` — saída bruta e literal do pytest
- `baseline_suite_run.txt` — baseline pré-existente da suíte
- `verify_artifacts.py` — verificação mecânica (bytes, SHA-256, (N/D))
- `mutation_probe.py` — prova de que os testes não são fachada
