# Dispatch Task for Implementer

**Context**: Milestone 3 / Requirements R1 & R5 — Governance Patch 1.1 Implementation & Math Logic Skill Materialization
**Role**: Implementer (`teamwork_worker`)
**Working Directory**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\implementer_1
**Authoritative Request**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
**Explorer Findings**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1\analysis.md
**Test Suite**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\tests\test_governance_patch_1_1.py

## Objectives
1. Implement Governance Patch 1.1 across affected files:
   - `.agents/hooks/validate_generated_report.py`
   - `.agents/hooks/post_test_audit.py`
   - `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py`
   Fixing:
   - **FP-01**: SHA-256 regex with boundaries `(?![0-9a-fA-F])`, strip code blocks, handle markdown tables cleanly.
   - **FP-02**: In `post_test_audit.py`, unpack `toolResponse`, `tool_response`, `stdout`, `stderr`, `output`, `result`, `exitCode`, `exit_code`, assign `UNKNOWN` instead of `0/0 PASS` when counts cannot be extracted, prevent `PASS` on non-zero exit codes.
   - **FP-03**: Structural distinction between `EXECUTIVE_CLAIM`, `DOCUMENTATION_EXAMPLE`, `ADVERSARIAL_FIXTURE` in fenced code blocks.
   - **MISS-S1-02**: Structural parser for Markdown and HTML tables; reject any numeric metric when Support = 0 (only allow N/A or -).
   - **MISS-S4-01**: Detect templated demo IDs (e.g. `demo_m01`) and cross-reference with formal demo catalog `datasets/mirage_v2/manifests/demo_inventory_v2.json`. Reject uncatalogued IDs as `UNPROVENANCED_TEMPLATE_ID`.
   - **MISS-S3-01**: Ensure proper separation of concerns between Hook and Phase Gate.
2. Materialize the skill `csbot-math-logic-auditor` in `.agents/skills/csbot-math-logic-auditor/`:
   - `SKILL.md`
   - `references/math_logic_audit_contract.md`
   - `scripts/audit_confusion_and_calibration.py`
   - `scripts/audit_temporal_transitions.py`
   - `scripts/audit_math_logic.py`
   Follow specifications in `explorer_1/analysis.md § 4`.
3. Update `missed_violations.json` and `false_positives.json` with canonical statuses (FIXED, ACCEPTED_LAYERED_RESPONSIBILITY, etc.) preserving history.
4. Run tests:
   - `pytest -v tests/test_governance_patch_1_1.py` must achieve 27/27 PASS (100%).
   - `python .agents/audit/run_governance_redteam.py` must achieve 12/12 PASS.
   - `python -m py_compile` on all modified python files.
5. Materialize `governance_patch_1_1_diff.md` in workspace root.
6. Generate handoff report in `.agents/teamwork/implementer_1/handoff.md`.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
NUNCA altere runtime C#, modelos ONNX, checkpoints ou datasets canônicos.


## 2026-11-07T21:16:00Z
Você é o Implementer na equipe Tier 3 do projeto CsBot.
Seu diretório de trabalho exclusivo é: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\implementer_1
A requisição original imutável está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
As instruções detalhadas estão em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\implementer_1\DISPATCH.md
A análise técnica detalhada do Explorer 1 está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1\analysis.md
A suíte de testes TDD implementada pelo Test Author está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\tests\test_governance_patch_1_1.py


## 2026-11-07T21:32:17Z
**Context**: Monitoramento do Marco 3 (Implementação do Patch de Governança 1.1)
**Content**: Observamos que `governance_patch_1_1_diff.md` foi gerado e a skill `csbot-math-logic-auditor` foi materializada. Por favor, confirme o status da execução dos testes e envie seu relatório de `handoff.md` e a mensagem final de conclusão.
**Action**: Enviar relatório de handoff.md e mensagem de conclusão.
