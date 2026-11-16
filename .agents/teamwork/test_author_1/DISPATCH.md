# Dispatch Task for Test Author

**Context**: Milestone 2 / Requirement R1 & Acceptance Criteria — Test Authoring (TDD)
**Role**: Test Author (`teamwork_test_writer`)
**Working Directory**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\test_author_1
**Authoritative Request**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
**Explorer Findings**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1\analysis.md

## Objectives
Write comprehensive unit and integration tests in `tests/test_governance_patch_1_1.py` covering all acceptance criteria for Governance Patch 1.1:
1. **FP-01 Tests**:
   - `test_valid_sha256_with_64_chars_passes`
   - `test_truncated_63_char_sha_fails`
   - `test_truncated_sha_with_ellipsis_fails`
   - `test_valid_sha_inside_markdown_table_passes`
   - `test_example_violation_inside_code_fence_does_not_block_report`
2. **FP-02 Tests & Fixtures**:
   - `test_camel_case_tool_response_is_parsed`
   - `test_snake_case_tool_response_is_parsed`
   - `test_dotnet_summary_is_parsed` (with real dotnet test output fixture)
   - `test_pytest_summary_is_parsed` (with real pytest output fixture)
   - `test_missing_summary_produces_unknown_not_zero`
   - `test_failed_exit_code_cannot_produce_pass`
3. **FP-03 Tests**:
   - `test_distinguish_executive_claim_from_doc_example_and_adversarial_fixture`
   - Validate that examples inside fenced code blocks do not trigger blocker violations, while executive claims outside fences are strictly audited.
4. **MISS-S1-02 Tests**:
   - `test_table_3_columns_support_zero_numeric_fails`
   - `test_table_4_columns_support_zero_numeric_fails`
   - `test_table_8_columns_support_zero_numeric_fails`
   - `test_html_table_support_zero_numeric_fails`
   - `test_escaped_pipes_and_reordered_columns`
   - `test_comma_and_point_decimal_support_zero_numeric_fails`
   - Confirm that only `"N/A"`, `"-"`, or empty are permitted when Support = 0.
5. **MISS-S4-01 Tests**:
   - `test_templated_demo_ids_validated_against_catalog`
   - Pass for authentic catalog IDs in `datasets/mirage_v2/manifests/demo_inventory_v2.json`.
   - Fail as `UNPROVENANCED_TEMPLATE_ID` for synthetic/unprovenanced IDs like `demo_m01` outside doc/fixture blocks.
6. **MISS-S3-01 Tests**:
   - `test_layered_responsibility_hook_vs_phase_gate`
   - End-to-end scenario: a report with a valid 64-char hash of another file passes the Hook format check, but fails Phase Gate physical disk verification (`sha256_mismatch`).

Rules:
- DO NOT modify production source code in `.agents/hooks/` or `tools/`. You only write test code in `tests/` and test fixtures.
- Produce `handoff.md` with test inventory, command to run, and verification details.


## 2026-11-07T21:04:56Z
Você é o Test Author na equipe Tier 3 do projeto CsBot.
Seu diretório de trabalho exclusivo é: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\test_author_1
A requisição original imutável está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
As instruções detalhadas estão em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\test_author_1\DISPATCH.md
A análise técnica detalhada do Explorer 1 com causas-raiz e cenários está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1\analysis.md

Sua missão exclusiva é implementar a suite completa de testes em `tests/test_governance_patch_1_1.py`:
- Testes para FP-01: ValidSha256With64CharsPasses, Truncated63CharShaFails, TruncatedShaWithEllipsisFails, ValidShaInsideMarkdownTablePasses, ExampleViolationInsideCodeFenceDoesNotBlockReport.
- Testes e fixtures para FP-02: CamelCaseToolResponseIsParsed, SnakeCaseToolResponseIsParsed, DotnetSummaryIsParsed, PytestSummaryIsParsed, MissingSummaryProducesUNKNOWNNotZero, FailedExitCodeCannotProducePASS, com fixtures reais para dotnet test, pytest e unittest.
- Testes para FP-03: Distinção estrutural entre afirmação executiva, exemplo documental e payload adversarial em blocos de código.
- Testes para MISS-S1-02: Parser estrutural de tabelas Markdown (3, 4 e 8 colunas, HTML table, Markdown escapado, ordem alterada de colunas, números com vírgula e ponto com Support=0 e rejeição de métricas numéricas, permitindo apenas N/A ou -).
- Testes para MISS-S4-01: Validação de IDs de demos suspeitas/templadas contra o catálogo formal datasets/mirage_v2/manifests/demo_inventory_v2.json (PASS para IDs reais do catálogo, FAIL como UNPROVENANCED_TEMPLATE_ID para IDs inexistentes fora de fixtures/documentação).
- Teste fim a fim para MISS-S3-01: Separação de responsabilidades (relatório com hash válido de outro arquivo aprovado no Hook e reprovado pelo Phase Gate na validação física do disco).

Regras inegociáveis:
- NÃO altere código de produção em `.agents/hooks/` ou `tools/`. Você escreve apenas arquivos de teste em `tests/`.
- Ao terminar, envie mensagem concisa ao orquestrador informando o caminho do arquivo de teste e handoff.md.
