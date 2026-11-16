# Dispatch Task for ML Generalization Auditor

**Context**: Milestone 4 / Requirement R4 — np.linspace Audit & Canonical Checkpoint Decision
**Role**: ML Generalization Auditor (`teamwork_auditor`)
**Working Directory**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ml_generalization_auditor_1
**Authoritative Request**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
**Graph Analyst Findings**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\audit\pre3a3_temporal_history_graph.md and `.agents/audit/pre3a3_temporal_history_blast_radius.json`
**Domain Skill**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\skills\csbot-model-validator\SKILL.md

## Objectives
1. Audit all relevant occurrences of `np.linspace` across the codebase (e.g. `tools/phase3a_training/data_utils.py`, `reconcile_ablation_and_calibration.py`, test fixtures, etc.):
   - Record: file, line, function, purpose, source_type, output tensor, and whether it reaches the training, validation, or test loss calculation.
   - Classify each occurrence as:
     - `LEGITIMATE_INTERPOLATION`
     - `LABELED_SYNTHETIC_AUGMENTATION`
     - `UNLABELED_SYNTHETIC_INPUT`
     - `REPORT_ONLY`
     - `DEAD_CODE`
2. Formulate the canonical conclusion on checkpoint provenance based on physical code reality:
   - Must choose EXACTLY ONE of:
     - A: `CHECKPOINT_TEMPORAL_PROVENANCE_VERIFIED`
     - B: `CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`
     - C: `CHECKPOINT_HISTORY_PROVENANCE_MIXED`
     - D: `CHECKPOINT_HISTORY_PROVENANCE_UNRESOLVED`
   - Explicitly document that if B, C, or D, the current checkpoint is preserved as experimental without deletion, and future retraining with authentic temporal extraction from NPZ is recommended.
   - Materialize deliverable at workspace root:
     - `pre3a3_checkpoint_decision.md`
3. Generate handoff report at `.agents/teamwork/ml_generalization_auditor_1/handoff.md`.

Rules:
- Read-only on canonical artifacts (checkpoints, datasets, models, C# runtime).
- Write ONLY the specified deliverable `pre3a3_checkpoint_decision.md` and your handoff report.
- Do NOT delete, overwrite, or retrain the checkpoint.

## 2026-11-07T21:05:16Z
[Message] sender=eb8d3078-143d-4003-96cc-4d05d41fb8a9 priority=MESSAGE_PRIORITY_HIGH
Você é o ML Generalization Auditor na equipe Tier 3 do projeto CsBot.
Seu diretório de trabalho exclusivo é: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ml_generalization_auditor_1
A requisição original imutável está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
As instruções detalhadas estão em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ml_generalization_auditor_1\DISPATCH.md
Consulte a skill: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\skills\csbot-model-validator\SKILL.md
Consulte as descobertas do Graph Analyst em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\audit\pre3a3_temporal_history_graph.md

Sua missão exclusiva para o Requisito R4:
1. Para cada ocorrência relevante de `np.linspace` no código-fonte, scripts e testes:
   - Registrar arquivo, linha, função, propósito, source_type, output tensor e se alcança a loss de treino, validação ou teste.
   - Classificar rigorosamente como:
     - `LEGITIMATE_INTERPOLATION`
     - `LABELED_SYNTHETIC_AUGMENTATION`
     - `UNLABELED_SYNTHETIC_INPUT`
     - `REPORT_ONLY`
     - `DEAD_CODE`
2. Emitir a conclusão canônica fundamentada no arquivo entregável (na raiz do repositório):
   `pre3a3_checkpoint_decision.md`
   A decisão deve ser categoricamente uma entre:
   - A: `CHECKPOINT_TEMPORAL_PROVENANCE_VERIFIED`
   - B: `CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`
   - C: `CHECKPOINT_HISTORY_PROVENANCE_MIXED`
   - D: `CHECKPOINT_HISTORY_PROVENANCE_UNRESOLVED`
   Se a decisão for B, C ou D, especificar que o checkpoint atual deve ser preservado como experimental sem ser apagado ou sobrescrito, recomendando o retreino futuro com janelas reais extraídas dos arquivos NPZ físicos.
3. Gerar seu relatório de handoff em:
   `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ml_generalization_auditor_1\handoff.md`

Regras inegociáveis:
- NUNCA modifique ou apague checkpoints (`*.pt`), modelos ONNX, runtime C# ou código de treino.
- Escreva exclusivamente `pre3a3_checkpoint_decision.md` e os arquivos de handoff em seu diretório.
- Ao terminar, envie mensagem concisa ao orquestrador.
