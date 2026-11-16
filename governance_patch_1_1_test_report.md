# Governance Patch 1.1 — Canonical Test Execution & Verification Report

- **Date / Timestamp UTC**: `2026-11-07T21:52:00Z`
- **Auditor / Archetype**: Adversarial Reviewer (`empirical_challenger`) — Tier 3 Team
- **Governance Mandate**: Strict adherence to `01-evidence-before-claims` through `09-subagent-role-isolation`
- **Data Classification**: `REAL` (derived from disk files, terminal executions, and AST/regex inspection)
- **Status**: `FAIL` (Unit/e2e test suite 27/27 PASS (100.0%); Live runtime runner gap discovered in FP-02)

---

## 1. Executive Summary

This report delivers the empirical verification of the test suite accompanying Governance Patch 1.1 for the CsBot project. The comprehensive test suite implemented in `tests/test_governance_patch_1_1.py` addresses 100.0% (2/2) of the requirements defined in `ORIGINAL_REQUEST.md` (R1 and R5) and passes 27/27 tests under synthetic fixtures [SYNTHETIC] in isolated test harnesses.

However, during live runtime verification within the real Google Antigravity extension environment, the Adversarial Reviewer uncovered an empirical blocker in `post_test_audit.py`:
In live execution, Antigravity does not supply `toolResponse` directly inside the PostToolUse event payload dict. Instead, Antigravity delivers `artifactDirectoryPath` and `stepIdx`, writing the terminal stdout to `.system_generated/steps/<stepIdx>/output.txt`. Because `post_test_audit.py` only inspects inline dictionary keys, `output_text` defaults to empty, forcing every real test execution to be marked as `UNKNOWN` with `block_pass_verdict = True`. In accordance with `09-subagent-role-isolation`, this defect is reported with a `FAIL` verdict and returned to the Orchestrator for implementation remediation.

---

## 2. Inventory of Evaluated Artifacts

| Artifact Description | Relative Repository Path | SHA-256 (64 hex characters) | Data Nature |
|---|---|---|---|
| Governance Test Suite | `tests/test_governance_patch_1_1.py` | `dceb77882f91465fc13d817cb11f1a7d013ec9c3dc0f1dff81bb3237883bab98` | `REAL` |
| Hook B (Report Validator) | `.agents/hooks/validate_generated_report.py` | `e9a808df061df23b64e547e641f093b7932cba3827ef38d02aa8dba0d8cf02cd` | `REAL` |
| Hook D (Post-Test Auditor) | `.agents/hooks/post_test_audit.py` | `a779e54f1f2a452d5c62c9f4cba81925009d3b4e42359e16aedd42544b38b5c9` | `REAL` |
| Skeptic Auditor Script | `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py` | `0f722c93985db7de0b37b9a90bb1eea517a513d50b88aeb591d7e4738d26f99d` | `REAL` |
| Red Team Runner | `.agents/audit/run_governance_redteam.py` | `5551c438b9758cdddafbfaba1234411e722b988a4d68d4d1307be308469e40d5` | `REAL` |
| Missed Violations Catalog | `missed_violations.json` | `e04de643edb274696708c0ce9a9d93406fc2ca9b9c49b3f4f6e48ebe98d92237` | `REAL` |
| False Positives Catalog | `false_positives.json` | `0ccba00c01ef829c2c6eed5071ce3a800544c73239ac91a88148369dfa13927b` | `REAL` |

---

## 3. Test Execution Verification

### 3.1 Command and Reproducibility
- **Command**: `pytest -v tests/test_governance_patch_1_1.py`
- **Environment**: Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 on Windows
- **Execution Timestamp**: `2026-11-07T21:34:52Z`
- **Execution Duration**: `0.25s`
- **Exit Code**: `0` (clean pass)
- **Aggregation Formula**: `Passed / Total = 27 / 27 (100.0%)`

### 3.2 Verbatim Test Results Log
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ricar\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ricar\OneDrive\Documentos\Dev\CsBot
plugins: anyio-4.14.1
collecting ... collected 27 items

tests/test_governance_patch_1_1.py::TestFP01Sha256RegexAndCodeFences::test_example_violation_inside_code_fence_does_not_block_report PASSED [  3%]
tests/test_governance_patch_1_1.py::TestFP01Sha256RegexAndCodeFences::test_truncated_63_char_sha_fails PASSED [  7%]
tests/test_governance_patch_1_1.py::TestFP01Sha256RegexAndCodeFences::test_truncated_sha_with_ellipsis_fails PASSED [ 11%]
tests/test_governance_patch_1_1.py::TestFP01Sha256RegexAndCodeFences::test_valid_sha256_with_64_chars_passes PASSED [ 14%]
tests/test_governance_patch_1_1.py::TestFP01Sha256RegexAndCodeFences::test_valid_sha_inside_markdown_table_passes PASSED [ 18%]
tests/test_governance_patch_1_1.py::TestFP02PostTestAuditAndSummary::test_camel_case_tool_response_is_parsed PASSED [ 22%]
tests/test_governance_patch_1_1.py::TestFP02PostTestAuditAndSummary::test_dotnet_summary_is_parsed PASSED [ 25%]
tests/test_governance_patch_1_1.py::TestFP02PostTestAuditAndSummary::test_failed_exit_code_cannot_produce_pass PASSED [ 29%]
tests/test_governance_patch_1_1.py::TestFP02PostTestAuditAndSummary::test_missing_summary_produces_unknown_not_zero PASSED [ 33%]
tests/test_governance_patch_1_1.py::TestFP02PostTestAuditAndSummary::test_pytest_summary_is_parsed PASSED [ 37%]
tests/test_governance_patch_1_1.py::TestFP02PostTestAuditAndSummary::test_snake_case_tool_response_is_parsed PASSED [ 40%]
tests/test_governance_patch_1_1.py::TestFP02PostTestAuditAndSummary::test_unittest_summary_is_parsed PASSED [ 44%]
tests/test_governance_patch_1_1.py::TestFP03StructuralDistinction::test_adversarial_fixture_inside_code_fence_does_not_block_report PASSED [ 48%]
tests/test_governance_patch_1_1.py::TestFP03StructuralDistinction::test_distinguish_executive_claim_from_doc_example_and_adversarial_fixture PASSED [ 51%]
tests/test_governance_patch_1_1.py::TestFP03StructuralDistinction::test_executive_claim_outside_code_fence_is_audited PASSED [ 55%]
tests/test_governance_patch_1_1.py::TestMISSS102SupportZeroTableParser::test_comma_and_point_decimal_support_zero_numeric_fails PASSED [ 59%]
tests/test_governance_patch_1_1.py::TestMISSS102SupportZeroTableParser::test_escaped_pipes_and_reordered_columns PASSED [ 62%]
tests/test_governance_patch_1_1.py::TestMISSS102SupportZeroTableParser::test_html_table_support_zero_numeric_fails PASSED [ 66%]
tests/test_governance_patch_1_1.py::TestMISSS102SupportZeroTableParser::test_table_3_columns_support_zero_numeric_fails PASSED [ 70%]
tests/test_governance_patch_1_1.py::TestMISSS102SupportZeroTableParser::test_table_4_columns_support_zero_numeric_fails PASSED [ 74%]
tests/test_governance_patch_1_1.py::TestMISSS102SupportZeroTableParser::test_table_8_columns_support_zero_numeric_fails PASSED [ 77%]
tests/test_governance_patch_1_1.py::TestMISSS102SupportZeroTableParser::test_table_support_zero_na_or_dash_passes PASSED [ 81%]
tests/test_governance_patch_1_1.py::TestMISSS401DemoIdCatalogValidation::test_authentic_catalog_demo_id_passes PASSED [ 85%]
tests/test_governance_patch_1_1.py::TestMISSS401DemoIdCatalogValidation::test_templated_demo_id_inside_code_fence_allowed PASSED [ 88%]
tests/test_governance_patch_1_1.py::TestMISSS401DemoIdCatalogValidation::test_templated_demo_ids_validated_against_catalog PASSED [ 92%]
tests/test_governance_patch_1_1.py::TestMISSS401DemoIdCatalogValidation::test_unprovenanced_demo_id_fails_outside_code_fence PASSED [ 96%]
tests/test_governance_patch_1_1.py::TestMISSS301LayeredResponsibilityEndToEnd::test_layered_responsibility_hook_vs_phase_gate PASSED [100%]

============================= 27 passed in 0.25s ==============================
```

---

## 4. Test Matrix Coverage Against Requirements

| Category ID | Target Requirement / Bug ID | Test Methods | Outcome | Evidence & Invariant Validated |
|---|---|---|---|---|
| **FP-01** | SHA-256 Boundaries & Code Fence Isolation | 5 tests in `TestFP01Sha256RegexAndCodeFences` | `PASS` (5/5, 100.0%) | Valid 64-hex SHA-256 passes inside and outside tables; 4-63 char hashes fail; ellipses fail; didactic examples inside code fences ignored. |
| **FP-02** | Test Tool Unpacking & UNKNOWN Summary | 7 tests in `TestFP02PostTestAuditAndSummary` | `PASS` (7/7, 100.0%) under synthetic fixtures [SYNTHETIC]; `FAIL` in live runner | Both camelCase `toolResponse` and snake_case `tool_response` unpacked in test dicts; however, live Antigravity delivery lacks inline dictionary unpacking. |
| **FP-03** | Structural Segmentation of Markdown | 3 tests in `TestFP03StructuralDistinction` | `PASS` (3/3, 100.0%) | Distinguishes `EXECUTIVE_CLAIM` from `DOCUMENTATION_EXAMPLE` and `ADVERSARIAL_FIXTURE`; live claims strictly audited; fences isolated. |
| **MISS-S1-02** | Structural Table Parser for Zero Support | 7 tests in `TestMISSS102SupportZeroTableParser` | `PASS` (7/7, 100.0%) | Rejects numeric metrics when Support is zero across 3, 4, 8 column tables, HTML tables, reordered columns, escaped pipes, point/comma decimals; permits `N/A` and `-`. |
| **MISS-S4-01** | Demo ID Catalog Validation | 4 tests in `TestMISSS401DemoIdCatalogValidation` | `PASS` (4/4, 100.0%) | Validates demo IDs against `demo_inventory_v2.json`; approves authentic catalog IDs; flags unprovenanced IDs as `UNPROVENANCED_TEMPLATE_ID`; permits fixtures in code fences. |
| **MISS-S3-01** | Layered Responsibility End-to-End | 1 test in `TestMISSS301LayeredResponsibilityEndToEnd` | `PASS` (1/1, 100.0%) | Formally proves Hook performs fast syntax/format validation while Phase Gate performs byte-by-byte physical disk hash validation, detecting physical mismatch. |

---

## 5. Live Runtime Blocker in FP-02

### 5.1 Root Cause
In live Antigravity execution, PostToolUse events passed via stdin do not contain `toolResponse` or `output` in the top-level payload dictionary:
```json
{
  "artifactDirectoryPath": "<USER_HOME>/.gemini/antigravity/brain/<id>",
  "conversationId": "<id>",
  "stepIdx": 175,
  "toolCall": {
    "args": { "CommandLine": "pytest -v tests/test_governance_patch_1_1.py" },
    "name": "run_command"
  },
  "transcriptPath": "<USER_HOME>/.gemini/antigravity/brain/<id>/.system_generated/logs/transcript_full.jsonl",
  "workspacePaths": ["<USER_HOME>/OneDrive/Documentos/Dev/CsBot"]
}
```
The actual command stdout is written by the Antigravity runner to disk at:
`<artifactDirectoryPath>/.system_generated/steps/<stepIdx>/output.txt`
Because `post_test_audit.py` (lines 211-226) only inspects memory keys inside `payload` and `tool_input`, `output_text` is empty (`""`). Consequently, `summary_found` remains `False`, and `post_test_audit.py` records `status = UNKNOWN` and `block_pass_verdict = True` in `.agents/audit/last_test_execution.json` on every live test command.

### 5.2 Remediation Required for Implementer
Add fallback file reading in `post_test_audit.py` (following the exact pattern used in `validate_generated_report.py` lines 676-685):
```python
if not output_text and payload.get("artifactDirectoryPath") and payload.get("stepIdx") is not None:
    step_file = Path(payload["artifactDirectoryPath"]) / ".system_generated" / "steps" / str(payload["stepIdx"]) / "output.txt"
    if step_file.exists():
        try:
            output_text = step_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
```

---

## 6. Verification Method

To independently verify the test suite:
```powershell
pytest -v tests/test_governance_patch_1_1.py
```
Expected output: `27 passed in <0.50s`.
