# Estado anterior (ABSENT) dos artefatos-alvo — FASE 2A-INTERMEDIATE (M4/M7)

Este arquivo é o **backup/registro de estado anterior** exigido pela Regra 06 para os artefatos
abaixo, todos criados pela etapa M4/M7 pelo papel *Dataset and Metadata Implementer*.

Os quatro alvos **não existiam** no disco antes desta execução (estado `ABSENT`). Portanto não há
conteúdo anterior a copiar: o backup imutável do estado anterior é este registro datado, e o
`rollback` determinístico é a remoção dos arquivos criados, retornando ao estado `ABSENT`.

| Alvo (caminho relativo ao repo) | Estado anterior | Ação planejada |
|---|---|---|
| `datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json` | ABSENT | CREATE (novo artefato, 0 registros) |
| `datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json` | ABSENT | CREATE (novo artefato, plano dry-run) |
| `datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json` | ABSENT | CREATE (novo artefato, 0 registros) |
| `training_runs/intermediate_domain_study/intermediate_splits_proposal.json` | ABSENT | CREATE (proposta de splits, não materializada) |

Nenhum artefato existente é modificado, movido, renomeado ou sobrescrito por estas operações.
Nenhum arquivo sob `datasets/mirage_v2/` ou `training_runs/positioning_v2_real_temporal/` é tocado.

Registrado em UTC: 2026-11-09T01:13:00Z
