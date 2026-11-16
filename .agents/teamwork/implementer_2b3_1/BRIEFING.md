# BRIEFING — 2026-11-08T21:57:00Z

## Mission
Executar o treinamento completo do Positioning Transformer Temporal Real (Fase 3A.3-B, Marco 2B.3) cobrindo snapshot imutável, join de sidecars v2, arquitetura com máscaras condicionais, pesos Train-only, preflight, 3 seeds canônicas (42026, 42027, 42028), avaliação de validação, seleção de candidato, baselines e suíte de 22 testes.

## 🔒 My Identity
- Archetype: implementer
- Roles: implementer, qa, specialist
- Working directory: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\implementer_2b3_1
- Original parent: 5aa571f6-be49-4f7f-baff-92e5c3c7ec1a
- Milestone: Fase 3A.3-B Marco 2B.3

## 🔒 Key Constraints
- Proibição absoluta de contaminação do Test set (67 demos) e Final Holdout: jamais abrir ou inferir pelo treinador.
- Classes com support zero devem ser estritamente N/A.
- Todo percentual deve conter numerador/denominador explícitos (N/D).
- Zero cheats: lógica real, sem dummy/facade, sem hardcoded predictions.
- Join 1:1 rigoroso entre shards temporais base e sidecars v2 (3.411.434 linhas).
- Pesos de classe e sampler calculados exclusivamente no Train.
- Fórmula de CompositeScore congelada.
- Suíte C# do CsBot deve permanecer verde.

## Current Parent
- Conversation ID: 5aa571f6-be49-4f7f-baff-92e5c3c7ec1a
- Updated: 2026-11-08T21:57:00Z

## Task Summary
- **What to build**: PositioningTransformerV2RealTemporal, pipeline de treinamento multi-seed real, evaluation e seleção de modelo, testes unitários (22 testes mínimos).
- **Success criteria**: Todos os gates de validação atendidos, 22 testes unitários passando, suíte C# verde.
- **Interface contracts**: `datasets/mirage_v2/contracts/label_contract_v2.json`, `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json`, `datasets/mirage_v2/positioning_v2_full_temporal/supervised_spot_mask_v1.json`.
- **Code layout**: Scripts sob `tools/phase3a_training/`, artefatos sob `training_runs/positioning_v2_real_temporal/full_training/`, testes sob `tests/`.

## Key Decisions Made
- Join 1:1 validado determinísticamente em 3.411.434 linhas entre shards e sidecars.
- Pesos de classe computados exclusivamente sobre o split Train (311 demos, 2.364.492 linhas).
- Máscaras condicionais implementadas na loss: NextSector ativado apenas quando SectorTransitionOccurs == 1.
- Spots não supervisionados mascarados com valor grande negativo (-1e9) para impossibilitar seleção neural.
- Seleção de melhor checkpoint baseada exclusivamente no CompositeScore de validação (Seed 42028, Época 6, Score 0.4700).

## Artifact Index
- `tools/phase3a_training/positioning_model_v2.py` — Arquitetura neural e loss do Positioning Transformer v2.
- `tools/phase3a_training/canonical_v2_dataloader.py` — DataLoader com validação de join e isolamento de split.
- `tools/phase3a_training/run_full_training_marco_2b3.py` — Pipeline determinístico de ponta a ponta.
- `tests/test_phase3a3_b_milestone2b3_full_training.py` — Suíte de 22 testes automatizados.
- `training_runs/positioning_v2_real_temporal/full_training/` — Diretório com 11 artefatos canônicos e 3 diretórios de seeds (39 arquivos de seed).

## Change Tracker
- **Files modified**: `tests/test_phase3a3_b_milestone2b3_full_training.py` (ajustado modo eval no teste de determinismo de restauração).
- **Build status**: 22/22 pytest Marco 2B.3 PASS, 40/40 pytest regressão PASS, 340/340 C# PASS.
- **Pending issues**: None.

## Quality Status
- **Build/test result**: 100% PASS.
- **Lint status**: 0 violations.
- **Tests added/modified**: 22 testes em `tests/test_phase3a3_b_milestone2b3_full_training.py`.

## Loaded Skills
- None requested to load locally.
