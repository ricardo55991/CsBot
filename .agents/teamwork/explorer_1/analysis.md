# Technical Analysis: Governance Patch 1.1 (R1 and R5 Investigation)

- **Author**: Explorer 1 (Codebase Investigator — Tier 3 Team)
- **Timestamp UTC**: 2026-11-07T21:05:00Z
- **Working Directory**: `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1`
- **Scope**: Read-only codebase investigation of governance hooks, tools, tests, catalogs, and skill specifications for Requirements R1 and R5.
- **Data Classification**: `REAL` (derived from disk files, AST/regex inspection, and runtime session verification).

---

## 1. Overview and Core Findings

A thorough read-only investigation was conducted across `.agents/hooks/`, `.agents/skills/`, `tools/`, `tests/`, and root governance artifacts (`hooks_config.json`, `false_positives.json`, `missed_violations.json`, `governance_red_team_report.md`, `skills_inventory.md`).

The governance architecture consists of 5 synchronized hooks in `.agents/hooks/` and 6 operational skills in `.agents/skills/`. The investigation identified the exact lines of code, root causes, contracts, and necessary adjustments for each item of Requirement R1 (FP-01, FP-02, FP-03, MISS-S1-02, MISS-S4-01, MISS-S3-01) and Requirement R5 (formal technical specification of `csbot-math-logic-auditor`).

---

## 2. Component Inventory of Governance Infrastructure

### 2.1 Hooks (`.agents/hooks/`) and Configurations

| Component | Relative Path | Target Lines | Event / Role | Current State & Governance Role |
|---|---|---:|---|---|
| Hook Config | `hooks_config.json` | 1-92 | Configuration | Defines workspace-level matcher rules for all 5 hooks. |
| Master Hook Config | `.agents/hooks.json` | 1-92 | Configuration | Canonical workspace mirror in `.agents/`. |
| Shared Utilities | `.agents/hooks/common_hook_utils.py` | 1-307 | Shared Library | Implements `fail_safe_main`, stdin parser, path/secret sanitization, hook mode handling (`blocking` vs `audit-only`), and atomic json logging. |
| Hook A | `.agents/hooks/protect_sensitive_files.py` | 55, 202-221 | `PreToolUse` | Intercepts modifications to `*.onnx`, `*.pt`, map profiles (`de_mirage.json`), splits, and catalogs. Requires authorization manifest with verifiable backup and 64-char SHA-256. |
| Hook B | `.agents/hooks/validate_generated_report.py` | 119-140, 203-210, 223-237, 292-336 | `PreToolUse`, `PostToolUse`, `Stop` | Audits generated reports against 9 skeptic rules. Contains FP-01, FP-03, MISS-S1-02, MISS-S4-01 root causes. |
| Hook C | `.agents/hooks/pre_training_gate.py` | 33, 100-240 | `PreToolUse` | Blocks model training commands unless `input_snapshot.json` exists with valid hashes and zero test contamination. |
| Hook D | `.agents/hooks/post_test_audit.py` | 50-142, 145-163, 186-215 | `PostToolUse` | Parses `dotnet test`, `pytest`, `unittest` execution outputs. Contains FP-02 root causes. |
| Hook E | `.agents/hooks/stop_condition_evidence_gate.py` | 80-160 | `Stop` | Blocks conclusion if tests failed or `deliverable_evidence.json` is missing/empty. |

### 2.2 Existing Skills (`.agents/skills/`)

| Skill Directory | Main Script | Relative Path | Function in Project |
|---|---|---|---|
| `csbot-phase-gate` | `run_phase_gate.py` | `.agents/skills/csbot-phase-gate/scripts/run_phase_gate.py` | Orchestrates phase transitions, validates requirement matrix, recomputes physical SHA-256 hashes against disk. |
| `csbot-report-skeptic` | `audit_executive_report.py` | `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py` | Adversarial audit over 12 invalidation vectors in reports. |
| `csbot-dataset-forensics` | `verify_sample_provenance.py` | `.agents/skills/csbot-dataset-forensics/scripts/verify_sample_provenance.py` | Verifies sample provenance and checks IDs against catalog. |
| `csbot-dataset-forensics` | `detect_templated_outputs.py` | `.agents/skills/csbot-dataset-forensics/scripts/detect_templated_outputs.py` | Detects zero variance, linear stepping, placeholder tokens. |
| `csbot-dataset-forensics` | `audit_label_support.py` | `.agents/skills/csbot-dataset-forensics/scripts/audit_label_support.py` | Enforces `metrics_policy: "N/A_REQUIRED"` for classes with support equal to zero. |
| `csbot-model-validator` | `validate_model_canonical.py` | `.agents/skills/csbot-model-validator/scripts/validate_model_canonical.py` | Deterministic model evaluation invariants (`model_eval=True`, `torch_no_grad=True`, `support=0 -> N/A`). |
| `csbot-runtime-validation` | `verify_runtime_session.py` | `.agents/skills/csbot-runtime-validation/scripts/verify_runtime_session.py` | Audits real CS2 runtime telemetry without simulation. |
| `csbot-graph-impact` | `analyze_graph_impact.py` | `.agents/skills/csbot-graph-impact/scripts/analyze_graph_impact.py` | Computes 10-axis blast radius from `graphify-out/graph.json`. |

### 2.3 Formal Demo Catalog

- **Catalog Path**: `datasets/mirage_v2/manifests/demo_inventory_v2.json`
- **Catalog Size**: 564,986 bytes (14,014 lines)
- **Catalog Hash**: `9557bfa168a64936d892dd55dc693441a1796bebb1ff9fb2f342b585dd1ef40e`
- **Structure**: Array of demo descriptors with `demo_id` (e.g. `100-thieves-vs-magic-m2-mirage`, `1win-vs-nemiga-m1-mirage`), `file_path`, `file_sha256`, `map`, `match_id`, `round_count`, `frame_count`, `accepted`.
- **Reference Loader**: Already implemented in `verify_sample_provenance.py` lines 52-84 (`load_known_demos(catalog_path: Path) -> Set[str]`).

---

## 3. Detailed Technical Analysis for Requirement R1

### 3.1 FP-01: SHA-256 Regex Boundaries and Code Fence Isolation

#### Exact Locations
1. `.agents/hooks/validate_generated_report.py`: lines 223–237 (`check_truncated_hashes`) and line 310 (`has_full_sha`).
2. `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py`: lines 143–173 (`check_divergent_or_truncated_hashes`).
3. `.agents/hooks/protect_sensitive_files.py`: line 55 (`SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")`).
4. `.agents/hooks/pre_training_gate.py`: line 33 (`SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")`).
5. `.agents/skills/csbot-dataset-forensics/scripts/verify_sample_provenance.py`: line 24 (`SHA256_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")`).

#### Root Cause
In `validate_generated_report.py` line 228, the regex quantifier `[0-9a-fA-F]{4,63}` has no trailing lookahead boundary `(?![0-9a-fA-F])`. When evaluating a genuine 64-character hex hash, the regex engine greedily captures the first 63 hex digits. Line 233 then evaluates `if len(candidate) != 64` (where candidate has length 63 != 64), erroneously triggering a hash truncation violation.
Additionally, fenced code blocks are currently not stripped, causing illustrative documentation examples or test fixtures to be parsed as live claims.

#### Implementation Specification for Implementer
1. Update regex in `validate_generated_report.py`:
   ```python
   TRUNCATED_HASH_PATTERN = re.compile(
       r'(?:sha-?256|previous_sha256|catalog_hash|hash)\s*["\']?\s*[:=]\s*["\']?(`?)([0-9a-fA-F]{4,63}(?![0-9a-fA-F])(?:\.\.\.)?|[0-9a-fA-F]*\.{2,}[0-9a-fA-F]*)\1',
       re.IGNORECASE
   )
   FULL_HASH_PATTERN = re.compile(r'\b[0-9a-fA-F]{64}\b')
   ```
2. Strip or isolate fenced code blocks (` ```...``` `) before analyzing executive hash claims.
3. Support hashes in table cells cleanly.

#### Unit Test Cases for Test Author
- `test_valid_sha256_with_64_chars_passes`
- `test_truncated_63_char_sha_fails`
- `test_truncated_sha_with_ellipsis_fails`
- `test_valid_sha_inside_markdown_table_passes`
- `test_example_violation_inside_code_fence_does_not_block_report`

---

### 3.2 FP-02: Robust `toolResponse` Unpacking and `UNKNOWN` Status in `post_test_audit.py`

#### Exact Locations
1. `.agents/hooks/post_test_audit.py`: lines 50–142 (`parse_test_metrics`), lines 145–163 (`extract_exit_code`), lines 186–215 (`handle_post_test_audit`).

#### Root Cause
1. `post_test_audit.py` only inspects snake_case keys (`tool_response`, `output`, `result`). Antigravity delivers command execution results under camelCase `toolResponse`.
2. When `toolResponse` was omitted, `output_text` was empty string.
3. In `parse_test_metrics`, unparsed outputs defaulted to `passed = 0`, `failed = 0`, `discovered = 0`, generating `canonical_summary = "0/0"`.
4. In `handle_post_test_audit`, zero exit code and zero failures produced `status = "PASSED"`, falsely certifying unparsed runs as `0/0 PASS`.

#### Implementation Specification for Implementer
1. Unify unpacking of `toolResponse`, `tool_response`, `stdout`, `stderr`, `output`, `result`, `exitCode`, `exit_code` from both `payload` and `tool_input`.
2. In `parse_test_metrics`, track `summary_found = False`. If no summary regex matches:
   - Return `canonical_summary = "UNKNOWN"`.
3. In `handle_post_test_audit`:
   - If summary is unknown: set `status = "UNKNOWN"` and `block_pass_verdict = True`.
   - If exit code is non-zero: set `status = "FAILED"` and `block_pass_verdict = True`.
   - Strictly prohibit emission of `0/0 PASS`.

#### Unit Test Cases for Test Author
- `test_camel_case_tool_response_is_parsed`
- `test_snake_case_tool_response_is_parsed`
- `test_dotnet_summary_is_parsed` (VSTest English and Portuguese)
- `test_pytest_summary_is_parsed`
- `test_missing_summary_produces_unknown_not_zero`
- `test_failed_exit_code_cannot_produce_pass`

---

### 3.3 FP-03: Structural Separation of Executive Claims vs Code Block Examples

#### Exact Locations
1. `.agents/hooks/validate_generated_report.py`: lines 324–336 (`analyze_report_content`).
2. `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py`.

#### Root Cause
Validators treat documents as flat text. When authors explain rules with code block examples, the linter treats the example as an executive claim made by the author.

#### Implementation Specification for Implementer
Implement a structural markdown segmenter:
1. Parse text into:
   - `EXECUTIVE_CLAIM`: Regular paragraphs, table rows, headers, and bullet points outside fenced code blocks.
   - `DOCUMENTATION_EXAMPLE`: Fenced code blocks (` ```...``` `).
   - `ADVERSARIAL_FIXTURE`: Blocks or sections marked with fixture comments.
2. Filter text so blocking skeptic checks only evaluate `EXECUTIVE_CLAIM` blocks.

#### Unit Test Cases for Test Author
- `test_executive_claim_with_violation_is_blocked`
- `test_documentation_example_inside_code_fence_does_not_block_report`
- `test_adversarial_fixture_does_not_block_report`

---

### 3.4 MISS-S1-02: Structural Markdown & HTML Table Parser for Support 0

#### Exact Locations
1. `.agents/hooks/validate_generated_report.py`: lines 119–140 (`check_support_zero_violation`).
2. `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py`: lines 101–121 (`check_zero_support_numeric_metrics`).

#### Root Cause
In `validate_generated_report.py`, the regex checks line-by-line for metric names on the same line as the support count. In standard markdown tables, metric names are in the header row, so data rows slip through.
In `audit_executive_report.py`, the regex assumes a 3-column table and fails on 4, 5, or 8-column tables, reordered columns, HTML tables, or escaped pipes.

#### Implementation Specification for Implementer
Implement a structural table parser:
1. Scan for Markdown table headers (`|---|---|`) and HTML `<table>` structures.
2. Map column headers: locate `support` column index and metric column indices (`precision`, `recall`, `f1`, `accuracy`, `balanced_accuracy`).
3. For each data row: if support cell is 0, check all metric cells.
   - **Allowed**: strictly `"N/A"`, `"NA"`, `"-"`, `"—"`, `"None"`, or empty.
   - **Forbidden**: any numeric integer, float, percentage, or comma-decimal.

#### Unit Test Cases for Test Author
- `test_table_3_columns_support_zero_numeric_fails`
- `test_table_4_columns_support_zero_numeric_fails`
- `test_table_8_columns_support_zero_numeric_fails`
- `test_table_support_zero_na_passes`
- `test_html_table_support_zero_numeric_fails`
- `test_escaped_pipes_and_reordered_columns_parsed_correctly`
- `test_comma_decimal_support_zero_numeric_fails`

---

### 3.5 MISS-S4-01: Demo ID Pattern Detection and Formal Catalog Cross-Check

#### Exact Locations
1. `.agents/hooks/validate_generated_report.py`: lines 80–87 (`TEMPLATED_ID_PATTERNS`) and lines 203–210 (`check_templated_ids`).
2. `.agents/skills/csbot-report-skeptic/scripts/audit_executive_report.py`: lines 213–230 (`check_templated_data_unlabeled`).
3. Catalog location: `datasets/mirage_v2/manifests/demo_inventory_v2.json`.

#### Root Cause
`TEMPLATED_ID_PATTERNS` checks only static placeholder names (`TOKEN_TEMPLATE_ID`, `TOKEN_DUMMY_SPOT`, etc.) and omits synthetic demo patterns like `demo_m01` or `demo_m\d+`. It also does not cross-reference demo IDs against the catalog.

#### Implementation Specification for Implementer
1. Add regex patterns to placeholder checks:
   `re.compile(r"\bdemo_m\d+\b", re.IGNORECASE)` and `re.compile(r"\bsynthetic_demo_\w+\b", re.IGNORECASE)`.
2. Cross-reference demo IDs cited in reports against `datasets/mirage_v2/manifests/demo_inventory_v2.json`. If a cited demo is absent outside documentation/fixtures, flag as `UNPROVENANCED_TEMPLATE_ID`.

#### Unit Test Cases for Test Author
- `test_synthetic_demo_id_demo_m01_fails`
- `test_real_demo_id_from_catalog_passes`
- `test_unprovenanced_demo_id_generates_error`

---

### 3.6 MISS-S3-01: Architectural Separation of Responsibilities (Hook vs Phase Gate)

#### Analysis and Architecture
1. **Hook Responsibility (`validate_generated_report.py`)**:
   - Fast synchronous format validation.
   - Confirms SHA-256 string is 64 hex characters and `artifact_path` is relative to workspace root.
   - Does not perform multi-gigabyte disk hash recomputation.
2. **Phase Gate Responsibility (`run_phase_gate.py` & Provenance Skills)**:
   - Batch gate execution at milestone milestones.
   - Recomputes `hashlib.sha256()` byte by byte from physical disk.
   - Emits `sha256_mismatch` and fails if hashes diverge.

#### Unit & End-to-End Test Case for Test Author
- `test_layered_responsibility_hash_verification`:
  - A report with a valid 64-hex hash of another file passes the Hook, but is rejected with `sha256_mismatch` during Phase Gate disk evaluation.

---

## 4. Technical Specification for Skill `csbot-math-logic-auditor` (R5)

### 4.1 Requirement Foundations
Mandated in `AGENTS.md` (lines 130–131, 143–145) and `.agents/subagents/subagent_roles_spec.json` (lines 136–156):
- Mathematical & Statistical Auditor (`audit_confusion_and_calibration`)
- Temporal Logic & FSM Auditor (`audit_temporal_transitions`)

### 4.2 File Architecture to Materialize

```
.agents/skills/csbot-math-logic-auditor/
├── SKILL.md
├── references/
│   └── math_logic_audit_contract.md
└── scripts/
    ├── audit_confusion_and_calibration.py
    ├── audit_temporal_transitions.py
    └── audit_math_logic.py
```

### 4.3 Script Specifications

#### 1. `scripts/audit_confusion_and_calibration.py`
- **CLI Options**: `--confusion-counts <csv>`, `--confusion-normalized <csv>`, `--metrics-json <json>`, `--output-json <json>`, `--dry-run`.
- **Invariants Audited**:
  - Raw confusion counts row sum equals support.
  - Normalized confusion row sum equals 1.0 (or 100.0%) for active classes.
  - Classes with support equal to zero have normalized row as `"N/A"`.
  - Metrics for support equal to zero must be `"N/A"`.
  - Macro-F1 calculated over active classes only.
  - Deterministic ECE and Brier score computation.
- **Dry-run**: Returns status `CONDITIONAL`, `data_nature: "SIMULATED"`, exit code 0.

#### 2. `scripts/audit_temporal_transitions.py`
- **CLI Options**: `--transitions-json <json>`, `--fsm-config <json>`, `--output-json <json>`, `--dry-run`.
- **Invariants Audited**:
  - State transitions obey valid CS2 transition adjacency graph.
  - C4 planting/defusing state timings are physically feasible.
- **Dry-run**: Returns status `CONDITIONAL`, `data_nature: "SIMULATED"`, exit code 0.

#### 3. `scripts/audit_math_logic.py` (Unified Runner)
- Executes both audit suites and outputs consolidated JSON report with status `PASS`, `CONDITIONAL` (dry-run), or `FAIL`.

---

## 5. Preliminary Inventory of `np.linspace` Occurrences

To assist Graph Analyst and Provenance Auditors:
1. `tools/phase3a_training/reconcile_ablation_and_calibration.py`: line 37:
   `bins = np.linspace(0.0, 1.0, num_bins + 1)` in `compute_ece_and_brier`.
   Classification: `LEGITIMATE_INTERPOLATION` (calibration binning, not training input).
2. `.agents/audit/run_governance_redteam.py`: line 43:
   `np.savez(p_npz, self_history=np.linspace(0, 1, 32).astype(np.float32))`.
   Classification: `ADVERSARIAL_FIXTURE` (red-team test fixture).

---

## 6. Implementation Guidance

1. **Test Author (Milestone 2 - TDD)**:
   Implement `tests/test_governance_patch_1_1.py` with the 6 unit and e2e test groups.
2. **Implementer (Milestone 3)**:
   - Patch `validate_generated_report.py`.
   - Patch `post_test_audit.py`.
   - Patch `audit_executive_report.py`.
   - Materialize `.agents/skills/csbot-math-logic-auditor/` and verify with `py_compile`.
