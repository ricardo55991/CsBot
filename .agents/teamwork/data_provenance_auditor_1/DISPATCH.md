# Dispatch Task for Data Provenance Auditor

**Context**: Milestone 4 / Requirement R3 — Deterministic Comparison Between NPZ Slices and DataLoader Output
**Role**: Data Provenance Auditor (`teamwork_auditor`)
**Working Directory**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\data_provenance_auditor_1
**Authoritative Request**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
**Graph Analyst Findings**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\audit\pre3a3_temporal_history_graph.md and `.agents/audit/pre3a3_temporal_history_blast_radius.json`
**Domain Skill**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\skills\csbot-dataset-forensics\SKILL.md

## Objectives
1. Audit the authentic training path of seeds 42026, 42027, and 42028:
   - Training script, DataLoader class, dataset path, code hash, construction of self/teammate history, sequence source, length, feature dimensions, and tick source.
   - Materialize deliverables:
     - `training_runs/positioning_v1/pre3a3_history_provenance.json`
     - `training_runs/positioning_v1/pre3a3_history_provenance.md`
2. Deterministically extract 200 samples under seed 42026:
   - 100 Train samples, 50 Validation samples, 50 Test samples.
   - Compare `DataLoader history == NPZ temporal slice` under explicit numeric tolerance.
   - Calculate metrics:
     - `ExactMatchRate`
     - `ToleranceMatchRate`
     - `SyntheticWindowRate`
     - `StaticWindowRate`
     - `MeanTemporalVariance`
     - `MeanSpatialDisplacement`
   - Materialize deliverables:
     - `pre3a3_npz_batch_comparison.json` (at workspace root)
     - `pre3a3_npz_batch_comparison.md` (at workspace root)
3. Generate handoff report at `.agents/teamwork/data_provenance_auditor_1/handoff.md`.

Rules:
- Read-only on canonical artifacts (checkpoints, datasets, models, C# runtime).
- Write ONLY the specified audit JSON/MD deliverables and your handoff report.
- Zero modification to training code or checkpoints.

## 2026-11-07T21:05:06Z
Você é o Data Provenance Auditor na equipe Tier 3 do projeto CsBot.
Seu diretório de trabalho exclusivo é: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\data_provenance_auditor_1
A requisição original imutável está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
As instruções detalhadas estão em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\data_provenance_auditor_1\DISPATCH.md
Consulte a skill: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\skills\csbot-dataset-forensics\SKILL.md
Consulte as descobertas do Graph Analyst em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\audit\pre3a3_temporal_history_graph.md

Sua missão exclusiva para o Requisito R3:
1. Auditar o caminho real de treino das seeds 42026, 42027 e 42028 (script de treino, classe DataLoader, dataset path, code hash, construção de self/teammate history, sequence source, length, feature dimensions e tick source).
   Materializar no disco:
   - `training_runs/positioning_v1/pre3a3_history_provenance.json`
   - `training_runs/positioning_v1/pre3a3_history_provenance.md`
2. Extrair deterministicamente 200 amostras sob seed 42026 (100 Train, 50 Validation, 50 Test) e verificar se `DataLoader history == NPZ temporal slice` sob tolerância numérica explícita.
   Calcular:
   - ExactMatchRate
   - ToleranceMatchRate
   - SyntheticWindowRate
   - StaticWindowRate
   - MeanTemporalVariance
   - MeanSpatialDisplacement
   Materializar no disco (na raiz do workspace):
   - `pre3a3_npz_batch_comparison.json`
   - `pre3a3_npz_batch_comparison.md`
3. Gerar seu handoff report em:
   `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\data_provenance_auditor_1\handoff.md`

Regras inegociáveis:
- NUNCA altere código-fonte de treino, runtime C#, modelos ONNX, checkpoints ou datasets canônicos.
- Escreva exclusivamente os relatórios e arquivos JSON/MD de auditoria solicitados.
- Ao terminar, envie mensagem concisa ao orquestrador com os resultados e caminhos dos arquivos.
