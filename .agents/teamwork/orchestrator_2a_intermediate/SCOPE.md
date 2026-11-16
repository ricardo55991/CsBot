# Scope: FASE 2A-INTERMEDIATE (estudo de viabilidade + aquisição corpus Mirage intermediário)

## Architecture
- Corpus profissional existente permanece em `datasets/mirage_v2/` (intocado).
- Novo domínio separado em `datasets/mirage_domains/` (professional_manifest_reference.json aponta para o corpus existente; intermediate_competitive/ é novo).
- Tooling em `tools/intermediate_demo_acquisition/`.
- Relatórios em `training_runs/intermediate_domain_study/`.

## Feature Inventory
| # | Feature | Descrição | Milestone | Source |
|---|---------|-----------|-----------|--------|
| 1 | Domain contract | domain_contract_v1.json com 3 domínios + subdomínios | M1 | Seção 4 |
| 2 | Professional manifest ref | professional_manifest_reference.json | M1 | Seção 4/21 |
| 3 | Source feasibility (FACEIT/Valve/público/voluntário) | 4 fontes investigadas | M2 | Seção 5 |
| 4 | Acquisition source matrix | acquisition_source_matrix.json | M2 | Seção 21 |
| 5 | Downloader seguro | 9 scripts dry-run | M3 | Seção 9 |
| 6 | Pilot manifests | inventory/npz/pilot/quarantine | M4 | Seções 8/10/11 |
| 7 | CT standardization metrics | métricas Seção 12 | M5 | Seção 12 |
| 8 | TR standardization metrics | métricas Seção 13 | M5 | Seção 13 |
| 9 | Professional vs intermediate comparison | Jensen-Shannon etc. | M5 | Seção 14 |
| 10 | 53-spot domain coverage | spot_domain_coverage.json | M5 | Seção 15 |
| 11 | New spot discovery | unmapped_intermediate_clusters.json | M5 | Seção 16 |
| 12 | Domain quality + training strategy | domain_training_strategy.md + escala | M6 | Seções 17/18 |
| 13 | Splits design | proposta 70/15/15 + holdouts | M7 | Seção 19 |
| 14 | 20 testes obrigatórios | suíte pytest | M8 | Seção 20 |
| 15 | 3 auditorias independentes | math/provenance/adversarial | M9 | Seção 21/22 |
| 16 | Phase gate + final report | evidence matrix + fase_2a_intermediate_final_report.md | M10 | Seção 22 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Domain contract & separation | domain_contract_v1.json + professional_manifest_reference.json + dirs | none | PLANNED |
| M2 | Source feasibility research | FACEIT/Valve/público/voluntário + matriz de fontes | none | PLANNED |
| M3 | Downloader tooling | tools/intermediate_demo_acquisition/ (dry-run) | M2 | PLANNED |
| M4 | Pilot manifests | inventory/npz/pilot/quarantine manifests | M2, M3 | PLANNED |
| M5 | Spatial analysis | CT/TR métricas + comparação + spots (só com dados) | M4 | PLANNED |
| M6 | Domain quality + training strategy | domain_training_strategy.md | M2, M5 | PLANNED |
| M7 | Splits design | proposta de splits + holdouts | M4 | PLANNED |
| M8 | Mandatory tests | 20 testes obrigatórios | M3, M4 | PLANNED |
| M9 | Independent audits | math/provenance/adversarial | M1–M8 | PLANNED |
| M10 | Phase gate + final report | evidence matrix + relatório final | M9 | PLANNED |

## Interface Contracts
### domain_contract_v1 ↔ downloader
- Campos obrigatórios: domain_id, platform, rank_system, skill_level, elo_or_rating, rank_at_collection_time, rank_at_match_time_if_available, map_specific_rank, map_name, match_date, region, source, source_license, acquisition_method, consent_type, metadata_confidence, exclusion_reason.
### inventory ↔ npz manifest
- demo_id 1:1; demo_sha256 + archive_sha256 registrados; round_count/player_count; accepted + rejection_reason.

## Code Layout
- `datasets/mirage_domains/` (novo), `tools/intermediate_demo_acquisition/` (novo), `training_runs/intermediate_domain_study/` (novo). `datasets/mirage_v2/` intocado.
