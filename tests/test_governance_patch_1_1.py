#!/usr/bin/env python3
"""
tests/test_governance_patch_1_1.py
Suíte de Testes Canônica para o Patch de Governança 1.1 do CsBot.

Cobre 100% dos requisitos e critérios de aceitação estipulados em ORIGINAL_REQUEST.md,
DISPATCH.md e explorer_1/analysis.md:

1. FP-01: Regex de SHA-256 com boundaries explícitas e isolamento de code fences:
   - test_valid_sha256_with_64_chars_passes
   - test_truncated_63_char_sha_fails
   - test_truncated_sha_with_ellipsis_fails
   - test_valid_sha_inside_markdown_table_passes
   - test_example_violation_inside_code_fence_does_not_block_report

2. FP-02: Unpacking de toolResponse/tool_response e canonical_summary UNKNOWN em post_test_audit:
   - test_camel_case_tool_response_is_parsed
   - test_snake_case_tool_response_is_parsed
   - test_dotnet_summary_is_parsed (fixtures inglês e português de VSTest)
   - test_pytest_summary_is_parsed (fixtures pytest com pass, skip e fail)
   - test_unittest_summary_is_parsed (fixtures unittest com OK e FAILED)
   - test_missing_summary_produces_unknown_not_zero
   - test_failed_exit_code_cannot_produce_pass

3. FP-03: Distinção estrutural entre afirmação executiva, exemplo documental e payload adversarial:
   - test_distinguish_executive_claim_from_doc_example_and_adversarial_fixture
   - test_executive_claim_outside_code_fence_is_audited
   - test_adversarial_fixture_inside_code_fence_does_not_block_report

4. MISS-S1-02: Parser estrutural de tabelas Markdown e HTML para Support = 0:
   - test_table_3_columns_support_zero_numeric_fails
   - test_table_4_columns_support_zero_numeric_fails
   - test_table_8_columns_support_zero_numeric_fails
   - test_html_table_support_zero_numeric_fails
   - test_escaped_pipes_and_reordered_columns
   - test_comma_and_point_decimal_support_zero_numeric_fails
   - test_table_support_zero_na_or_dash_passes

5. MISS-S4-01: Validação de IDs de demos contra o catálogo formal datasets/mirage_v2/manifests/demo_inventory_v2.json:
   - test_templated_demo_ids_validated_against_catalog
   - test_authentic_catalog_demo_id_passes
   - test_unprovenanced_demo_id_fails_outside_code_fence
   - test_templated_demo_id_inside_code_fence_allowed

6. MISS-S3-01: Separação de responsabilidades Hook (formato) vs Phase Gate (criptográfico no disco):
   - test_layered_responsibility_hook_vs_phase_gate
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Inserção de diretórios de hooks e skills no sys.path para resolução determinística
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = WORKSPACE_ROOT / ".agents" / "hooks"
REPORT_SKEPTIC_SCRIPTS = WORKSPACE_ROOT / ".agents" / "skills" / "csbot-report-skeptic" / "scripts"
PHASE_GATE_SCRIPTS = WORKSPACE_ROOT / ".agents" / "skills" / "csbot-phase-gate" / "scripts"
DATASET_FORENSICS_SCRIPTS = WORKSPACE_ROOT / ".agents" / "skills" / "csbot-dataset-forensics" / "scripts"

for p in (HOOKS_DIR, REPORT_SKEPTIC_SCRIPTS, PHASE_GATE_SCRIPTS, DATASET_FORENSICS_SCRIPTS, WORKSPACE_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import common_hook_utils
import post_test_audit
import run_phase_gate
import validate_generated_report


class BaseGovernanceTestCase(unittest.TestCase):
    """Classe base que isola diretórios de auditoria e garante ausência de efeitos colaterais no workspace."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Mock dos caminhos de persistência para evitar sobrescrita em .agents/audit/
        self.mock_report_validation_file = self.temp_path / "last_report_validation.json"
        self.mock_test_execution_file = self.temp_path / "last_test_execution.json"
        self.mock_audit_log_file = self.temp_path / "hooks_audit.jsonl"

        self.patchers = [
            patch.object(validate_generated_report, "LAST_REPORT_VALIDATION_FILE", self.mock_report_validation_file),
            patch.object(post_test_audit, "LAST_TEST_EXECUTION_FILE", self.mock_test_execution_file),
            patch.object(common_hook_utils, "AUDIT_LOG_PATH", self.mock_audit_log_file),
        ]
        for p in self.patchers:
            p.start()

    def tearDown(self) -> None:
        for p in self.patchers:
            p.stop()
        self.temp_dir.cleanup()


# ==============================================================================
# FP-01: Validação de SHA-256 (64 hexadecimais, rejeição de truncados e isolamento)
# ==============================================================================
class TestFP01Sha256RegexAndCodeFences(BaseGovernanceTestCase):
    """Testes para o falso positivo FP-01: Regex de SHA-256 e boundaries."""

    def test_valid_sha256_with_64_chars_passes(self) -> None:
        """Um hash SHA-256 completo com exatamente 64 caracteres hexadecimais DEVE ser aprovado."""
        full_sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        report_text = (
            "# Relatório de Avaliação Canônica\n"
            "Artefato gerado: `artifacts/evaluation_metrics.json`\n"
            f"SHA-256: {full_sha}\n"
            "Veredito: PASS\n"
        )
        payload = {
            "Path": "reports/canonical_eval_report.md",
            "Content": report_text,
        }

        # 1. Verificação da função específica de hash truncado
        violations = validate_generated_report.check_truncated_hashes(report_text)
        trunc_violations = [v for v in violations if "Hash Truncado" in v or "truncado" in v or "incompleto" in v]
        self.assertEqual(
            trunc_violations,
            [],
            f"Hash válido de 64 caracteres não pode gerar violação de hash truncado. Encontrado: {trunc_violations}",
        )

        # 2. Verificação pelo handler completo do Hook
        resp = validate_generated_report.handle_validate_generated_report(payload, mode="blocking", event="PreToolUse")
        self.assertEqual(resp.get("decision"), "allow", f"Hook bloqueou relatório com hash de 64 chars: {resp}")

    def test_truncated_63_char_sha_fails(self) -> None:
        """Um hash com 63 caracteres hexadecimais (< 64) DEVE ser categoricamente rejeitado."""
        truncated_sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcde"
        self.assertEqual(len(truncated_sha), 63)

        report_text = (
            "# Relatório de Avaliação\n"
            "Artefato: `artifacts/model.json`\n"
            f"SHA-256: {truncated_sha}\n"
        )
        violations = validate_generated_report.check_truncated_hashes(report_text)
        trunc_violations = [v for v in violations if "Hash Truncado" in v or "64" in v or "incompleto" in v]
        self.assertGreater(
            len(trunc_violations),
            0,
            "Hash com 63 caracteres deve falhar na auditoria de SHA-256.",
        )

    def test_truncated_sha_with_ellipsis_fails(self) -> None:
        """Hashes truncados com reticências ('...' ou '..') DEVEM ser sumariamente reprovados."""
        sample_with_ellipsis = (
            "# Relatório com hash truncado\n"
            "O checkpoint gerado possui SHA-256: `7f36eff885de...`\n"
            "Outro hash anterior: 0123456789abcdef...9abc\n"
        )
        violations = validate_generated_report.check_truncated_hashes(sample_with_ellipsis)
        self.assertGreater(
            len(violations),
            0,
            "Hashes com reticências devem ser detectados e reprovados.",
        )
        self.assertTrue(any("Hash Truncado" in v or "reticências" in v or "truncado" in v for v in violations))

    def test_valid_sha_inside_markdown_table_passes(self) -> None:
        """Hashes SHA-256 de 64 caracteres inseridos em colunas de tabelas Markdown DEVEM passar."""
        table_report = (
            "# Relatório de Entrega de Modelos\n"
            "| Artefato | Caminho | SHA-256 | Status |\n"
            "|:---|:---|:---|:---:|\n"
            "| Checkpoint PT | `models/positioning.pt` | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | PASS |\n"
            "| Modelo ONNX | `models/positioning.onnx` | 9557bfa168a64936d892dd55dc693441a1796bebb1ff9fb2f342b585dd1ef40e | PASS |\n"
            "\n"
            "Veredito: PASS\n"
        )
        violations = validate_generated_report.check_truncated_hashes(table_report)
        trunc_violations = [v for v in violations if "Hash Truncado" in v or "truncado" in v or "incompleto" in v]
        self.assertEqual(
            trunc_violations,
            [],
            f"Hashes válidos de 64 caracteres dentro de tabela Markdown geraram falso positivo: {trunc_violations}",
        )

    def test_example_violation_inside_code_fence_does_not_block_report(self) -> None:
        """Exemplos ilustrativos de violações dentro de fenced code blocks (```) NÃO devem bloquear o relatório."""
        full_sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        report_with_doc_fence = (
            "# Relatório Canônico de Governança\n"
            "Artefato gerado: `artifacts/clean_eval.json`\n"
            f"SHA-256: {full_sha}\n"
            "Veredito: PASS\n"
            "\n"
            "Abaixo está um exemplo de padrão proibido que nossa governança rejeita:\n"
            "```markdown\n"
            "# Exemplo Proibido (Violação Didática de Hash)\n"
            "SHA-256: 7f36eff885de...\n"
            "```\n"
            "O exemplo documental acima nunca deve ser utilizado em relatórios executivos reais.\n"
        )
        payload = {
            "Path": "reports/doc_with_fences.md",
            "Content": report_with_doc_fence,
        }
        resp = validate_generated_report.handle_validate_generated_report(payload, mode="blocking", event="PreToolUse")
        self.assertEqual(
            resp.get("decision"),
            "allow",
            f"Exemplo ilustrativo de hash dentro de code fence bloqueou indevidamente o relatório: {resp.get('reason')}",
        )


# ==============================================================================
# FP-02: Unpacking de toolResponse/tool_response e canonical_summary UNKNOWN
# ==============================================================================
class TestFP02PostTestAuditAndSummary(BaseGovernanceTestCase):
    """Testes e fixtures reais para FP-02: Parsing de métricas de teste em dotnet test, pytest e unittest."""

    DOTNET_VSTEST_EN_FIXTURE = (
        "Determining projects to restore...\n"
        "All projects are up-to-date for restore.\n"
        "CsBot.Tests -> C:\\Users\\ricar\\OneDrive\\Documentos\\Dev\\CsBot\\tests\\CsBotManager.Tests\\bin\\Debug\\net8.0\\CsBot.Tests.dll\n"
        "Test run for C:\\Users\\ricar\\OneDrive\\Documentos\\Dev\\CsBot\\tests\\CsBotManager.Tests\\bin\\Debug\\net8.0\\CsBot.Tests.dll (.NETCoreApp,Version=v8.0)\n"
        "Microsoft (R) Test Execution Command Line Tool Version 17.10.0\n"
        "Copyright (c) Microsoft Corporation.  All rights reserved.\n\n"
        "Starting test execution, please wait...\n"
        "A total of 1 test files matched the specified pattern.\n\n"
        "Passed!  - Failed:     0, Passed:   340, Skipped:     0, Total:   340, Duration: 1 s - CsBot.Tests.dll (net8.0)\n"
    )

    DOTNET_VSTEST_PT_FIXTURE = (
        "Execução de teste para C:\\Users\\ricar\\OneDrive\\Documentos\\Dev\\CsBot\\tests\\CsBotManager.Tests\\bin\\Debug\\net8.0\\CsBot.Tests.dll (.NETCoreApp,Version=v8.0)\n"
        "Microsoft (R) Ferramenta de Linha de Comando de Execução de Teste Versão 17.10.0\n\n"
        "Iniciando execução de teste, aguarde...\n"
        "Um total de 1 arquivos de teste corresponderam ao padrão especificado.\n\n"
        "Aprovado!  - Com falha:     0, Aprovado:   340, Ignorado:     0, Total:   340, Duração: 2 s - CsBot.Tests.dll (net8.0)\n"
    )

    DOTNET_VSTEST_ALT_FIXTURE = (
        "Total tests: 340\n"
        "     Passed: 340\n"
        "     Failed: 0\n"
        "    Skipped: 0\n"
    )

    PYTEST_CLEAN_FIXTURE = (
        "============================= test session starts =============================\n"
        "platform win32 -- Python 3.11.9, pytest-9.1.1\n"
        "collected 24 items\n\n"
        "tests/test_movement_contract_v2.py ........                             [ 33%]\n"
        "tests/test_phase2_2_training_inputs.py ................                 [100%]\n\n"
        "============================== 24 passed in 1.10s ==============================\n"
    )

    PYTEST_WITH_SKIPPED_FIXTURE = (
        "============================= test session starts =============================\n"
        "collected 13 items\n\n"
        "============================== 12 passed, 1 skipped in 0.45s ===================\n"
    )

    PYTEST_WITH_FAILURES_FIXTURE = (
        "============================= test session starts =============================\n"
        "collected 12 items\n\n"
        "======================== 2 failed, 10 passed in 0.85s ========================\n"
    )

    UNITTEST_CLEAN_FIXTURE = (
        "........................................\n"
        "----------------------------------------------------------------------\n"
        "Ran 40 tests in 0.125s\n\n"
        "OK\n"
    )

    UNITTEST_FAILURE_FIXTURE = (
        "...................................F....\n"
        "======================================================================\n"
        "FAIL: test_metric (test_sample.TestCase)\n"
        "----------------------------------------------------------------------\n"
        "Traceback (most recent call last):\n"
        "AssertionError: 1 != 2\n\n"
        "----------------------------------------------------------------------\n"
        "Ran 40 tests in 0.150s\n\n"
        "FAILED (failures=1)\n"
    )

    def test_camel_case_tool_response_is_parsed(self) -> None:
        """A chave 'toolResponse' (camelCase entregue pelo Antigravity) DEVE ser desembalada e processada."""
        payload = {
            "CommandLine": "dotnet test tests/CsBotManager.Tests",
            "toolResponse": {
                "output": self.DOTNET_VSTEST_EN_FIXTURE,
                "exitCode": 0,
            },
        }
        post_test_audit.handle_post_test_audit(payload, mode="blocking", event="PostToolUse")

        self.assertTrue(self.mock_test_execution_file.exists(), "Arquivo last_test_execution.json não foi gerado.")
        record = json.loads(self.mock_test_execution_file.read_text(encoding="utf-8"))

        self.assertEqual(record["passed"], 340)
        self.assertEqual(record["discovered"], 340)
        self.assertEqual(record["canonical_summary"], "340/340")
        self.assertEqual(record["status"], "PASSED")
        self.assertFalse(record["block_pass_verdict"])

        # Validação adicional: extração via .system_generated/steps/<stepIdx>/output.txt quando output inline está ausente
        step_dir = self.temp_path / ".system_generated" / "steps" / "42"
        step_dir.mkdir(parents=True, exist_ok=True)
        (step_dir / "output.txt").write_text(
            f"Command exited with code 0.\n\nCommand output:\n{self.DOTNET_VSTEST_EN_FIXTURE}",
            encoding="utf-8",
        )
        step_payload = {
            "CommandLine": "dotnet test tests/CsBotManager.Tests",
            "artifactDirectoryPath": str(self.temp_path),
            "stepIdx": 42,
        }
        post_test_audit.handle_post_test_audit(step_payload, mode="blocking", event="PostToolUse")
        rec_step = json.loads(self.mock_test_execution_file.read_text(encoding="utf-8"))
        self.assertEqual(rec_step["canonical_summary"], "340/340")
        self.assertEqual(rec_step["status"], "PASSED")
        self.assertFalse(rec_step["block_pass_verdict"])

    def test_snake_case_tool_response_is_parsed(self) -> None:
        """A chave 'tool_response' (snake_case) DEVE ser desembalada e processada identicamente."""
        payload = {
            "CommandLine": "dotnet test tests/CsBotManager.Tests",
            "tool_response": {
                "output": self.DOTNET_VSTEST_EN_FIXTURE,
                "exit_code": 0,
            },
        }
        post_test_audit.handle_post_test_audit(payload, mode="blocking", event="PostToolUse")

        record = json.loads(self.mock_test_execution_file.read_text(encoding="utf-8"))
        self.assertEqual(record["passed"], 340)
        self.assertEqual(record["canonical_summary"], "340/340")

        # Validação adicional: extração via transcriptPath quando output inline e step file estão ausentes
        transcript_file = self.temp_path / "transcript_full.jsonl"
        transcript_file.write_text(
            json.dumps({"step_index": 88, "type": "GENERIC", "content": self.PYTEST_CLEAN_FIXTURE}) + "\n",
            encoding="utf-8",
        )
        trans_payload = {
            "CommandLine": "pytest tests/CsBotManager.Tests",
            "transcriptPath": str(transcript_file),
            "stepIdx": 88,
        }
        post_test_audit.handle_post_test_audit(trans_payload, mode="blocking", event="PostToolUse")
        rec_trans = json.loads(self.mock_test_execution_file.read_text(encoding="utf-8"))
        self.assertEqual(rec_trans["canonical_summary"], "24/24")
        self.assertEqual(rec_trans["status"], "PASSED")
        self.assertFalse(rec_trans["block_pass_verdict"])

    def test_dotnet_summary_is_parsed(self) -> None:
        """Fixtures em inglês, português e formato alternativo de VSTest devem ser extraídas corretamente."""
        # 1. Inglês
        m_en = post_test_audit.parse_test_metrics(self.DOTNET_VSTEST_EN_FIXTURE, {})
        self.assertEqual(m_en["passed"], 340)
        self.assertEqual(m_en["failed"], 0)
        self.assertEqual(m_en["discovered"], 340)
        self.assertEqual(m_en["canonical_summary"], "340/340")

        # 2. Português
        m_pt = post_test_audit.parse_test_metrics(self.DOTNET_VSTEST_PT_FIXTURE, {})
        self.assertEqual(m_pt["passed"], 340)
        self.assertEqual(m_pt["failed"], 0)
        self.assertEqual(m_pt["discovered"], 340)
        self.assertEqual(m_pt["canonical_summary"], "340/340")

        # 3. Formato alternativo
        m_alt = post_test_audit.parse_test_metrics(self.DOTNET_VSTEST_ALT_FIXTURE, {})
        self.assertEqual(m_alt["passed"], 340)
        self.assertEqual(m_alt["failed"], 0)
        self.assertEqual(m_alt["canonical_summary"], "340/340")

    def test_pytest_summary_is_parsed(self) -> None:
        """Fixtures do pytest com passed, skipped e failed devem ser extraídas com precisão."""
        # 1. 24 passed
        m1 = post_test_audit.parse_test_metrics(self.PYTEST_CLEAN_FIXTURE, {})
        self.assertEqual(m1["passed"], 24)
        self.assertEqual(m1["discovered"], 24)
        self.assertEqual(m1["canonical_summary"], "24/24")

        # 2. 12 passed, 1 skipped
        m2 = post_test_audit.parse_test_metrics(self.PYTEST_WITH_SKIPPED_FIXTURE, {})
        self.assertEqual(m2["passed"], 12)
        self.assertEqual(m2["skipped"], 1)
        self.assertEqual(m2["discovered"], 13)
        self.assertEqual(m2["canonical_summary"], "12/13")

        # 3. 2 failed, 10 passed
        m3 = post_test_audit.parse_test_metrics(self.PYTEST_WITH_FAILURES_FIXTURE, {})
        self.assertEqual(m3["passed"], 10)
        self.assertEqual(m3["failed"], 2)
        self.assertEqual(m3["discovered"], 12)
        self.assertEqual(m3["canonical_summary"], "10/12")

    def test_unittest_summary_is_parsed(self) -> None:
        """Fixtures de python -m unittest devem ser extraídas fielmente."""
        # 1. OK
        m_ok = post_test_audit.parse_test_metrics(self.UNITTEST_CLEAN_FIXTURE, {})
        self.assertEqual(m_ok["passed"], 40)
        self.assertEqual(m_ok["failed"], 0)
        self.assertEqual(m_ok["canonical_summary"], "40/40")

        # 2. FAILED
        m_fail = post_test_audit.parse_test_metrics(self.UNITTEST_FAILURE_FIXTURE, {})
        self.assertEqual(m_fail["passed"], 39)
        self.assertEqual(m_fail["failed"], 1)
        self.assertEqual(m_fail["canonical_summary"], "39/40")

    def test_missing_summary_produces_unknown_not_zero(self) -> None:
        """Saídas não parseáveis ou sem sumário DEVEM produzir 'UNKNOWN', e NUNCA '0/0 PASS'."""
        unparsed_cli_output = (
            "Building project CsBot.Tests...\n"
            "CSC : warning CS8618: Non-nullable field must contain a non-null value.\n"
            "Command executed with exit code 0.\n"
        )
        payload = {
            "CommandLine": "pytest tests/nonexistent_tests.py",
            "output": unparsed_cli_output,
            "exit_code": 0,
        }
        post_test_audit.handle_post_test_audit(payload, mode="blocking", event="PostToolUse")

        record = json.loads(self.mock_test_execution_file.read_text(encoding="utf-8"))
        self.assertNotEqual(
            record["canonical_summary"],
            "0/0",
            "Saída sem sumário de teste jamais pode registrar '0/0'!",
        )
        self.assertEqual(record["canonical_summary"], "UNKNOWN")
        self.assertNotEqual(
            record["status"],
            "PASSED",
            "Saída com sumário UNKNOWN não pode ser aprovada com status PASSED!",
        )
        self.assertTrue(record["block_pass_verdict"])

    def test_failed_exit_code_cannot_produce_pass(self) -> None:
        """Comando de teste que encerra com exit code != 0 NUNCA pode produzir status PASSED."""
        payload = {
            "CommandLine": "dotnet test tests/CsBotManager.Tests",
            "output": "Starting test run...\nFailed: 1, Passed: 9, Total: 10",
            "exitCode": 1,
        }
        post_test_audit.handle_post_test_audit(payload, mode="blocking", event="PostToolUse")

        record = json.loads(self.mock_test_execution_file.read_text(encoding="utf-8"))
        self.assertEqual(record["exit_code"], 1)
        self.assertEqual(record["status"], "FAILED")
        self.assertTrue(record["block_pass_verdict"])


# ==============================================================================
# FP-03: Distinção Estrutural de Executive Claim vs Documentation Example vs Adversarial Fixture
# ==============================================================================
class TestFP03StructuralDistinction(BaseGovernanceTestCase):
    """Testes para FP-03: Distinção estrutural entre afirmação executiva e blocos de código."""

    def test_distinguish_executive_claim_from_doc_example_and_adversarial_fixture(self) -> None:
        """Valida que violações dentro de blocos de código (exemplos ou fixtures) são ignoradas pelo linter."""
        full_sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        report_text = (
            "# Relatório Executivo de Auditoria do CsBot\n"
            "Artefato verificado: `artifacts/master_eval.json`\n"
            f"SHA-256: {full_sha}\n"
            "Veredito: PASS\n"
            "\n"
            "### Seção 1: Exemplo de Violação Documental (DOCUMENTATION_EXAMPLE)\n"
            "A seguir apresentamos a tabela inválida que rejeitamos em governança:\n"
            "```markdown\n"
            "| Classe | Support | Recall |\n"
            "| OBJECTIVE | 0 | 0.0% |\n"
            "Hash truncado didático: `7f36eff885de...`\n"
            "```\n"
            "\n"
            "### Seção 2: Fixture Adversarial de Teste (ADVERSARIAL_FIXTURE)\n"
            "```python\n"
            "# ADVERSARIAL_FIXTURE: caso de teste para testar o linter\n"
            "bad_dict = {'support': 0, 'recall': '85%', 'demo_id': 'demo_m01'}\n"
            "```\n"
            "\n"
            "Conclusão: Todo o conteúdo executivo fora dos blocos está em conformidade.\n"
        )
        payload = {
            "Path": "reports/executive_report_with_fences.md",
            "Content": report_text,
        }
        resp = validate_generated_report.handle_validate_generated_report(payload, mode="blocking", event="PreToolUse")
        self.assertEqual(
            resp.get("decision"),
            "allow",
            f"Linter rejeitou indevidamente relatório contendo exemplos documentais ou fixtures: {resp.get('reason')}",
        )

    def test_executive_claim_outside_code_fence_is_audited(self) -> None:
        """Afirmação executiva fora de blocos de código contendo violação DEVE ser estritamente bloqueada."""
        full_sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        unfenced_violation = (
            "# Relatório Executivo de Auditoria\n"
            "Artefato: `artifacts/master_eval.json`\n"
            f"SHA-256: {full_sha}\n"
            "Veredito: PASS\n"
            "\n"
            "Abaixo estão os resultados reais observados:\n"
            "| Classe | Support | Recall |\n"
            "| OBJECTIVE | 0 | 0.0% |\n"
        )
        payload = {
            "Path": "reports/executive_report_with_violation.md",
            "Content": unfenced_violation,
        }
        resp = validate_generated_report.handle_validate_generated_report(payload, mode="blocking", event="PreToolUse")
        self.assertEqual(
            resp.get("decision"),
            "deny",
            "Violação em afirmação executiva fora de code fences deve ser bloqueada.",
        )

    def test_adversarial_fixture_inside_code_fence_does_not_block_report(self) -> None:
        """Blocos de código contendo payloads de teste adversariais não devem disparar bloqueio."""
        full_sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        payload_text = (
            "# Relatório de Testes Automatizados\n"
            "Artefato: `tests/test_results.json`\n"
            f"SHA-256: {full_sha}\n"
            "Veredito: PASS\n"
            "\n"
            "```json\n"
            "{\n"
            '  "adversarial_payload": true,\n'
            '  "mock_hash": "a1b2c3...",\n'
            '  "support": 0,\n'
            '  "f1": 0.95\n'
            "}\n"
            "```\n"
        )
        payload = {
            "Path": "reports/test_adversarial_report.md",
            "Content": payload_text,
        }
        resp = validate_generated_report.handle_validate_generated_report(payload, mode="blocking", event="PreToolUse")
        self.assertEqual(resp.get("decision"), "allow")


# ==============================================================================
# MISS-S1-02: Parser Estrutural de Tabelas Markdown e HTML para Support = 0
# ==============================================================================
class TestMISSS102SupportZeroTableParser(BaseGovernanceTestCase):
    """Testes para MISS-S1-02: Parser estrutural de tabelas Markdown e HTML rejeitando métricas numéricas em support=0."""

    FULL_SHA = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    def test_table_3_columns_support_zero_numeric_fails(self) -> None:
        """Tabela de 3 colunas (| Class | Support | F1-Score |) com support=0 e métrica numérica DEVE falhar."""
        table_3col = (
            "# Relatório de Métricas por Classe\n"
            "Artefato: `artifacts/metrics.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "| Class | Support | F1-Score |\n"
            "|:---|:---:|:---:|\n"
            "| ACTIVE_SPOT | 150 | 0.92 |\n"
            "| RARE_SPOT | 0 | 0.80 |\n"
        )
        violations = validate_generated_report.check_support_zero_violation(table_3col)
        self.assertGreater(
            len(violations),
            0,
            "Tabela de 3 colunas com support=0 e F1=0.80 deve ser rejeitada.",
        )
        self.assertTrue(any("Support=0" in v or "support=0" in v.lower() for v in violations))

    def test_table_4_columns_support_zero_numeric_fails(self) -> None:
        """Tabela de 4 colunas (| State | Support | Precision | Recall |) com support=0 e 0.0% DEVE falhar."""
        table_4col = (
            "# Relatório de Estados FSM\n"
            "Artefato: `artifacts/states.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "| State | Support | Precision | Recall |\n"
            "|:---|:---:|:---:|:---:|\n"
            "| RETAKE | 45 | 0.88 | 0.85 |\n"
            "| OBJECTIVE | 0 | 0.0 | 0.0% |\n"
        )
        violations = validate_generated_report.check_support_zero_violation(table_4col)
        self.assertGreater(
            len(violations),
            0,
            "Tabela de 4 colunas com support=0 e Recall=0.0% deve ser rejeitada.",
        )

    def test_table_8_columns_support_zero_numeric_fails(self) -> None:
        """Tabela de 8 colunas com support=0 e métricas numéricas DEVE falhar."""
        table_8col = (
            "# Benchmark Completo de Spots\n"
            "Artefato: `artifacts/spots.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "| Spot | Support | TP | FP | FN | Precision | Recall | F1 |\n"
            "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n"
            "| MIRAGE_A_DEFAULT | 200 | 180 | 10 | 10 | 0.947 | 0.947 | 0.947 |\n"
            "| MIRAGE_B_APARTMENTS | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 |\n"
        )
        violations = validate_generated_report.check_support_zero_violation(table_8col)
        self.assertGreater(
            len(violations),
            0,
            "Tabela de 8 colunas com support=0 e métricas numéricas 0.00 deve falhar.",
        )

    def test_html_table_support_zero_numeric_fails(self) -> None:
        """Tabela em formato HTML <table> com support=0 e métrica numérica DEVE falhar."""
        html_table = (
            "# Relatório Executivo em HTML\n"
            "Artefato: `artifacts/html_metrics.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "<table>\n"
            "  <thead>\n"
            "    <tr><th>Classe</th><th>Support</th><th>Recall</th></tr>\n"
            "  </thead>\n"
            "  <tbody>\n"
            "    <tr><td>CT_SPAWN</td><td>100</td><td>0.95</td></tr>\n"
            "    <tr><td>PALACE_CORNER</td><td>0</td><td>0.0%</td></tr>\n"
            "  </tbody>\n"
            "</table>\n"
        )
        violations = validate_generated_report.check_support_zero_violation(html_table)
        self.assertGreater(
            len(violations),
            0,
            "Tabela HTML com support=0 e métrica numérica 0.0% deve falhar.",
        )

    def test_escaped_pipes_and_reordered_columns(self) -> None:
        """Tabelas com colunas reordenadas e pipes escapados (\\|) devem ser parseadas e validadas corretamente."""
        reordered_table = (
            "# Relatório com Colunas Reordenadas\n"
            "Artefato: `artifacts/reordered.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "| Precision | Support | Classe \\| Descrição | Recall | Balanced Accuracy |\n"
            "|:---:|:---:|:---|:---:|:---:|\n"
            "| 0.85 | 100 | B_SITE \\| Bombsite B | 0.80 | 0.82 |\n"
            "| 0.0 | 0 | MID \\| Mid Window | 0.0 | 0.0 |\n"
        )
        violations = validate_generated_report.check_support_zero_violation(reordered_table)
        self.assertGreater(
            len(violations),
            0,
            "Tabela reordenada com Support=0 e Precision/Recall numéricos deve falhar.",
        )

    def test_comma_and_point_decimal_support_zero_numeric_fails(self) -> None:
        """Decimais com vírgula (padrão pt-BR: '0,80') ou ponto ('0.80') DEVEM ambos ser reprovados quando support=0."""
        # Vírgula
        comma_table = (
            "# Relatório Formato pt-BR\n"
            "Artefato: `artifacts/ptbr.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "| Classe | Support | F1-Score |\n"
            "|:---|:---:|:---:|\n"
            "| UNDERPASS | 0 | 0,75 |\n"
        )
        v_comma = validate_generated_report.check_support_zero_violation(comma_table)
        self.assertGreater(
            len(v_comma),
            0,
            "Métrica decimal com vírgula '0,75' para support=0 deve falhar.",
        )

        # Ponto
        point_table = (
            "# Relatório Formato en-US\n"
            "Artefato: `artifacts/enus.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "| Classe | Support | F1-Score |\n"
            "|:---|:---:|:---:|\n"
            "| UNDERPASS | 0 | 0.75 |\n"
        )
        v_point = validate_generated_report.check_support_zero_violation(point_table)
        self.assertGreater(
            len(v_point),
            0,
            "Métrica decimal com ponto '0.75' para support=0 deve falhar.",
        )

    def test_table_support_zero_na_or_dash_passes(self) -> None:
        """Tabela onde classes com support=0 exibem estritamente 'N/A' ou '-' DEVE passar com 0 violações."""
        clean_table = (
            "# Relatório em Conformidade Estrita com a Regra 03\n"
            "Artefato: `artifacts/clean_table.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "\n"
            "| Classe | Support | Precision | Recall | F1-Score | Balanced Accuracy |\n"
            "|:---|:---:|:---:|:---:|:---:|:---:|\n"
            "| ACTIVE_A | 250 | 0.91 | 0.89 | 0.90 | 0.90 |\n"
            "| RARE_B | 0 | N/A | N/A | N/A | N/A |\n"
            "| DORMANT_C | 0 | - | - | - | - |\n"
            "\n"
            "Veredito: PASS\n"
        )
        violations = validate_generated_report.check_support_zero_violation(clean_table)
        self.assertEqual(
            violations,
            [],
            f"Tabela com 'N/A' e '-' para support=0 gerou falso positivo: {violations}",
        )


# ==============================================================================
# MISS-S4-01: Validação de IDs de Demos contra Catálogo Formal
# ==============================================================================
class TestMISSS401DemoIdCatalogValidation(BaseGovernanceTestCase):
    """Testes para MISS-S4-01: Verificação cruzada contra demo_inventory_v2.json."""

    FULL_SHA = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    CATALOG_PATH = WORKSPACE_ROOT / "datasets" / "mirage_v2" / "manifests" / "demo_inventory_v2.json"

    def test_templated_demo_ids_validated_against_catalog(self) -> None:
        """IDs do catálogo formal passam; IDs sintéticos como 'demo_m01' falham como UNPROVENANCED_TEMPLATE_ID."""
        # 1. ID real do catálogo de Mirage
        real_demo_id = "100-thieves-vs-magic-m2-mirage"
        real_report = (
            "# Relatório de Proveniência de Amostras\n"
            f"Artefato: `{self.CATALOG_PATH.relative_to(WORKSPACE_ROOT)}`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            f"Demos validadas: {real_demo_id}\n"
            "Veredito: PASS\n"
        )
        violations_real = validate_generated_report.check_templated_ids(real_report)
        self.assertEqual(
            violations_real,
            [],
            f"Demo ID autêntica do catálogo gerou falso positivo: {violations_real}",
        )

        # 2. ID sintético/templado não catalogado
        synthetic_demo_id = "demo_m01"
        synth_report = (
            "# Relatório de Avaliação\n"
            "Artefato: `artifacts/eval.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            f"Demos utilizadas: {synthetic_demo_id}, demo_m02\n"
            "Veredito: PASS\n"
        )
        violations_synth = validate_generated_report.check_templated_ids(synth_report)
        self.assertGreater(
            len(violations_synth),
            0,
            "Demo ID sintética 'demo_m01' deve ser reprovada como dado templado/não catalogado.",
        )

    def test_authentic_catalog_demo_id_passes(self) -> None:
        """Garante que IDs autênticos presentes no catálogo formal demo_inventory_v2.json são aceitos."""
        self.assertTrue(self.CATALOG_PATH.exists(), f"Catálogo formal não encontrado em {self.CATALOG_PATH}")
        with open(self.CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        self.assertGreater(len(catalog), 0)
        first_demo_id = catalog[0]["demo_id"]

        report_text = (
            "# Relatório de Proveniência Autêntica\n"
            "Artefato: `datasets/mirage_v2/manifests/demo_inventory_v2.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            f"Demo de referência: {first_demo_id}\n"
            "Veredito: PASS\n"
        )
        violations = validate_generated_report.check_templated_ids(report_text)
        self.assertEqual(violations, [])

    def test_unprovenanced_demo_id_fails_outside_code_fence(self) -> None:
        """IDs como 'demo_m01', 'demo_m99' ou 'synthetic_demo_test' fora de fences geram violação."""
        for bad_id in ("demo_m01", "demo_m99", "synthetic_demo_01"):
            report = (
                "# Relatório Não Homologado\n"
                "Artefato: `artifacts/out.json`\n"
                f"SHA-256: {self.FULL_SHA}\n"
                f"Série de demos: {bad_id}\n"
            )
            v = validate_generated_report.check_templated_ids(report)
            self.assertGreater(
                len(v),
                0,
                f"Identificador não comprovado '{bad_id}' deveria ter sido reprovado.",
            )

    def test_templated_demo_id_inside_code_fence_allowed(self) -> None:
        """Menção de 'demo_m01' dentro de code fences como documentação NÃO bloqueia o relatório."""
        report = (
            "# Relatório de Regras\n"
            "Artefato: `artifacts/rules.json`\n"
            f"SHA-256: {self.FULL_SHA}\n"
            "Veredito: PASS\n"
            "\n"
            "Exemplo didático de padrão proibido:\n"
            "```text\n"
            "demo_id = demo_m01\n"
            "```\n"
        )
        payload = {
            "Path": "reports/rules_report.md",
            "Content": report,
        }
        resp = validate_generated_report.handle_validate_generated_report(payload, mode="blocking", event="PreToolUse")
        self.assertEqual(
            resp.get("decision"),
            "allow",
            "Menção de demo_m01 dentro de code fence não pode bloquear o relatório.",
        )


# ==============================================================================
# MISS-S3-01: Separação de Responsabilidades (Hook vs Phase Gate) Fim a Fim
# ==============================================================================
class TestMISSS301LayeredResponsibilityEndToEnd(BaseGovernanceTestCase):
    """Teste fim a fim para MISS-S3-01: Arquitetura em camadas (Hook valida formato, Phase Gate valida disco)."""

    def test_layered_responsibility_hook_vs_phase_gate(self) -> None:
        """
        Cenário fim a fim:
        1. Cria arquivo A e arquivo B com conteúdos distintos.
        2. Obtém o SHA-256 de 64 caracteres real do arquivo B.
        3. Elabora um relatório que cita o arquivo A, mas declara o hash do arquivo B.
        4. O Hook (validate_generated_report) analisa o relatório:
           - O hash tem 64 hexadecimais (sintaxe válida).
           - O caminho relativo do artefato existe no texto.
           -> O Hook APROVA (decision = allow), pois sua responsabilidade é validação leve de formato.
        5. O Phase Gate (run_phase_gate / load_and_validate_evidences) analisa as evidências:
           - Recalcula byte a byte o hash de arquivo A diretamente no disco.
           - Constata a divergência entre o hash real e o hash declarado (arquivo B).
           -> O Phase Gate REPROVA com status valid=False e 'sha256_mismatch'.
        """
        # 1. Criação dos arquivos temporários físicos
        file_a = self.temp_path / "artifact_a.json"
        file_a.write_text('{"module": "Positioning", "status": "active", "epoch": 10}\n', encoding="utf-8")

        file_b = self.temp_path / "artifact_b.json"
        file_b.write_text('{"module": "Movement", "status": "deprecated", "epoch": 99}\n', encoding="utf-8")

        # 2. Hash SHA-256 do arquivo B
        hash_b = hashlib.sha256(file_b.read_bytes()).hexdigest()
        real_hash_a = hashlib.sha256(file_a.read_bytes()).hexdigest()
        self.assertNotEqual(hash_b, real_hash_a, "Hashes de A e B devem ser estritamente diferentes.")
        self.assertEqual(len(hash_b), 64)

        # 3. Relatório declarando arquivo A com o hash de B
        rel_path_a = file_a.relative_to(WORKSPACE_ROOT) if file_a.is_relative_to(WORKSPACE_ROOT) else Path("artifacts/artifact_a.json")
        report_content = (
            "# Relatório de Homologação de Checkpoint\n"
            f"Artefato gerado: `{rel_path_a}`\n"
            f"SHA-256: {hash_b}\n"
            "Veredito: PASS\n"
        )

        # 4. Execução do Hook (camada leve de formato)
        payload = {
            "Path": "reports/checkpoint_homologation_report.md",
            "Content": report_content,
        }
        hook_resp = validate_generated_report.handle_validate_generated_report(
            payload, mode="blocking", event="PreToolUse"
        )
        self.assertEqual(
            hook_resp.get("decision"),
            "allow",
            "O Hook deve aprovar o formato (hash de 64 hexadecimais e artefato relativo presente).",
        )

        # 5. Execução do Phase Gate (camada criptográfica determinística no disco)
        snapshot = {
            "workspace_root": str(self.temp_path),
            "total_files": 1,
            "missing_files_count": 0,
            "files": [
                {
                    "path": str(file_a),
                    "relative_path": str(rel_path_a),
                    "exists": True,
                    "sha256": real_hash_a,
                }
            ],
        }

        # Criação do arquivo de evidências declarando hash_b para file_a
        evidences_manifest_file = self.temp_path / "declared_evidences.json"
        evidences_data = {
            "schema_version": "1.0.0",
            "evidences": [
                {
                    "evidence_id": "EV-001",
                    "artifact_path": str(file_a),
                    "sha256": hash_b,  # Hash incompatível com file_a no disco!
                    "reproducible_command": "python tools/evaluate.py",
                    "aggregation_formula": "1/1",
                    "data_nature": "REAL",
                }
            ],
        }
        evidences_manifest_file.write_text(json.dumps(evidences_data, indent=2), encoding="utf-8")

        # Avaliação determinística pelo Phase Gate
        validation_result = run_phase_gate.load_and_validate_evidences(
            evidences_json=evidences_manifest_file,
            snapshot=snapshot,
            workspace_root=self.temp_path,
            dry_run=False,
        )

        self.assertEqual(
            validation_result["invalid_evidences"],
            1,
            "Phase Gate deve detectar e reprovar a divergência física entre o hash declarado e o disco.",
        )
        self.assertEqual(
            validation_result["valid_evidences"],
            0,
            "Nenhuma evidência com hash divergente no disco pode ser aprovada pelo Phase Gate.",
        )
        issues = validation_result["evidences"][0]["issues"]
        self.assertTrue(
            any("sha256_mismatch" in str(issue) for issue in issues),
            f"Phase Gate deve emitir 'sha256_mismatch'. Issues encontradas: {issues}",
        )


if __name__ == "__main__":
    unittest.main()
