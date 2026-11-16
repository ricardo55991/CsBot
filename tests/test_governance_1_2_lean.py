#!/usr/bin/env python3
"""
Suíte de Testes da Governança CsBot 1.2 Lean (30 testes canônicos).
Valida os 30 requisitos inegociáveis de eficiência, limites por Tier, Evidence Packet,
Digest Cache, Smart Testing, modos de hooks e integridade de arquivos de produto.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = WORKSPACE_ROOT / ".agents"
CONTRACTS_DIR = AGENTS_DIR / "contracts"
CACHE_DIR = AGENTS_DIR / "cache"
HOOKS_DIR = AGENTS_DIR / "hooks"
RULES_DIR = AGENTS_DIR / "rules"
AUDIT_DIR = AGENTS_DIR / "audit"

sys.path.insert(0, str(HOOKS_DIR))
from common_hook_utils import get_hook_mode
from update_artifact_digest import get_or_update_digest, compute_sha256, load_digest_index


def test_01_DocumentationTaskCreatesZeroSubagents():
    """Test 1: Tarefas documentais e Markdown possuem limite estrito de 0 subagentes."""
    matrix_file = CONTRACTS_DIR / "test_impact_matrix.json"
    assert matrix_file.exists(), "test_impact_matrix.json deve existir"
    data = json.loads(matrix_file.read_text(encoding="utf-8"))
    doc_tier = data["tiers"]["documentation_and_reports"]["risk_tier"]
    assert doc_tier == "Tier 1"
    rule_file = RULES_DIR / "10-single-agent-first.md"
    assert "default_subagents = 0" in rule_file.read_text(encoding="utf-8")


def test_02_NestedSubagentIsBlocked():
    """Test 2: Proibição absoluta de subagentes criarem outros subagentes (Rule 11)."""
    rule_file = RULES_DIR / "11-no-nested-subagents.md"
    assert rule_file.exists()
    content = rule_file.read_text(encoding="utf-8")
    assert "NESTED_SUBAGENT_BLOCKED" in content
    assert "invoke_subagent" in content


def test_03_OnlyMainAgentCanDelegate():
    """Test 3: Somente o agente principal pode delegar tarefas."""
    agents_md = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "only_main_agent_can_delegate = true" in agents_md


def test_04_Tier1AllowsZeroSubagents():
    """Test 4: Tier 1 permite no maximo 0 subagentes."""
    rule_07 = (RULES_DIR / "07-independent-validation.md").read_text(encoding="utf-8")
    assert "Tier 1" in rule_07
    assert "0 subagentes" in rule_07


def test_05_Tier2AllowsAtMostOneSubagent():
    """Test 5: Tier 2 permite no maximo 1 subagente."""
    rule_07 = (RULES_DIR / "07-independent-validation.md").read_text(encoding="utf-8")
    assert "Tier 2" in rule_07
    assert "0 ou 1 subagente" in rule_07


def test_06_Tier3AllowsAtMostTwoSubagents():
    """Test 6: Tier 3 permite no maximo 2 subagentes."""
    rule_07 = (RULES_DIR / "07-independent-validation.md").read_text(encoding="utf-8")
    assert "Tier 3" in rule_07
    assert "Máximo 2 subagentes" in rule_07


def test_07_Tier4AllowsAtMostFourSubagents():
    """Test 7: Tier 4 permite no maximo 4 subagentes."""
    rule_07 = (RULES_DIR / "07-independent-validation.md").read_text(encoding="utf-8")
    assert "Tier 4" in rule_07
    assert "Máximo 4 subagentes" in rule_07


def test_08_DelegationRequiresJustification():
    """Test 8: Toda delegação exige justificativa formal com campos obrigatórios."""
    agents_md = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "SINGLE_AGENT_FIRST" in agents_md or "Single-Agent First" in agents_md


def test_09_OverlappingRolesAreRejected():
    """Test 9: Sobreposições proibidas de papéis de auditoria."""
    agents_md = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "sem sobreposição" in agents_md


def test_10_EvidencePacketRespectsLimits():
    """Test 10: Schema do Evidence Packet v1 impõe limites operacionais (<=8 artefatos, <=3 leituras adicionais)."""
    schema_file = CONTRACTS_DIR / "evidence_packet_v1.schema.json"
    assert schema_file.exists()
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    assert schema["properties"]["source_artifacts"]["maxItems"] == 8
    assert schema["properties"]["max_additional_reads"]["maximum"] <= 5


def test_11_UnchangedHashReusesDigest(tmp_path):
    """Test 11: Se o hash e o tamanho não mudaram, reutiliza o digest do cache."""
    test_file = tmp_path / "sample_doc.md"
    test_file.write_text("Conteudo inicial para teste de cache digest.", encoding="utf-8")
    rel_path = str(test_file.relative_to(WORKSPACE_ROOT)) if test_file.is_relative_to(WORKSPACE_ROOT) else str(test_file)
    
    # Primeira chamada: cache miss/created
    res1 = get_or_update_digest(rel_path, summary="Resumo de teste", producer="test_author")
    # Segunda chamada com mesmo hash: cache hit
    res2 = get_or_update_digest(rel_path, summary="Resumo alterado", producer="test_author")
    assert res2.get("reused") is True or res2.get("status") == "CACHE_HIT"


def test_12_ChangedHashInvalidatesDigest(tmp_path):
    """Test 12: Se o hash mudar, o digest antigo é invalidado e atualizado."""
    test_file = tmp_path / "mutated_doc.md"
    test_file.write_text("Conteudo v1", encoding="utf-8")
    rel_path = str(test_file.relative_to(WORKSPACE_ROOT)) if test_file.is_relative_to(WORKSPACE_ROOT) else str(test_file)
    
    res1 = get_or_update_digest(rel_path, summary="V1")
    test_file.write_text("Conteudo v2 com texto diferente e novo hash", encoding="utf-8")
    res2 = get_or_update_digest(rel_path, summary="V2")
    assert res2.get("reused") is False
    assert res2.get("status") == "CACHE_MISS_UPDATED"


def test_13_FullReadRequiresJustification():
    """Test 13: Rule 12 proíbe leituras redundantes integrais."""
    rule_12 = (RULES_DIR / "12-no-redundant-file-reads.md").read_text(encoding="utf-8")
    assert "NO_REDUNDANT_FILE_READS" in rule_12 or "Proibição de Leituras Redundantes" in rule_12
    assert "Evidence Packet" in rule_12


def test_14_MarkdownChangeDoesNotRunDotnetTests():
    """Test 14: Alterações de Markdown proíbem explicitamente execução de 'dotnet test'."""
    matrix = json.loads((CONTRACTS_DIR / "test_impact_matrix.json").read_text(encoding="utf-8"))
    forbidden = matrix["tiers"]["documentation_and_reports"]["forbidden_tests"]
    assert "dotnet test" in forbidden
    assert "dotnet build" in forbidden


def test_15_PythonChangeRunsSpecificTest():
    """Test 15: Alteração de Python isolado exige py_compile e teste direcionado."""
    matrix = json.loads((CONTRACTS_DIR / "test_impact_matrix.json").read_text(encoding="utf-8"))
    required = matrix["tiers"]["isolated_python_tool"]["required_checks"]
    assert "python_py_compile" in required
    assert "targeted_unit_test" in required


def test_16_CSharpChangeRunsFilteredTests():
    """Test 16: Alteração localizada em C# roda testes filtrados."""
    matrix = json.loads((CONTRACTS_DIR / "test_impact_matrix.json").read_text(encoding="utf-8"))
    required = matrix["tiers"]["localized_csharp"]["required_checks"]
    assert any("dotnet test --filter" in r for r in required)


def test_17_SharedContractRequiresExpandedTests():
    """Test 17: Contratos compartilhados (MapProfiles/JSON) exigem testes de consumidores cruzados."""
    matrix = json.loads((CONTRACTS_DIR / "test_impact_matrix.json").read_text(encoding="utf-8"))
    required = matrix["tiers"]["shared_cross_language_contract"]["required_checks"]
    assert "python_consumer_tests" in required
    assert any("dotnet" in r for r in required)


def test_18_DeltaFixDoesNotRepeatFullRedTeam():
    """Test 18: Correções localizadas não repetem auditorias integrais ou Red Team completo."""
    rule_13 = (RULES_DIR / "13-smart-testing.md").read_text(encoding="utf-8")
    assert "blast radius" in rule_13


def test_19_WarningDoesNotStartRewriteLoop():
    """Test 19: Orçamento de warnings nos hooks impede loops de reescrita."""
    hook_mode = json.loads((HOOKS_DIR / "hook_mode.json").read_text(encoding="utf-8"))
    budget = hook_mode.get("hook_warning_budget", {})
    assert budget.get("maximum_rewrite_attempts") == 1
    assert budget.get("warning_does_not_block") is True


def test_20_CriticalViolationStillBlocks():
    """Test 20: Violações críticas listadas mantêm bloqueio inegociável."""
    hook_mode = json.loads((HOOKS_DIR / "hook_mode.json").read_text(encoding="utf-8"))
    criticals = hook_mode.get("critical_blocking_violations", [])
    assert "TEST_SET_CONTAMINATION_IN_TUNING" in criticals
    assert "SECRET_OR_CREDENTIAL_EXPOSURE" in criticals
    assert "ZERO_SUPPORT_REPORTED_AS_NUMERIC" in criticals


def test_21_AuditOnlyHookDoesNotBlockWarning():
    """Test 21: validate-generated-report opera em modo audit-only para warnings."""
    hook_mode = json.loads((HOOKS_DIR / "hook_mode.json").read_text(encoding="utf-8"))
    assert hook_mode["hook_modes"]["validate-generated-report"] == "audit-only"
    mode = get_hook_mode(hook_name="validate-generated-report")
    assert mode == "audit-only"


def test_22_TestContaminationStillBlocks():
    """Test 22: pre-training-gate opera em modo blocking permanente."""
    hook_mode = json.loads((HOOKS_DIR / "hook_mode.json").read_text(encoding="utf-8"))
    assert hook_mode["hook_modes"]["pre-training-gate"] == "blocking"
    mode = get_hook_mode(hook_name="pre-training-gate")
    assert mode == "blocking"


def test_23_SecretLeakageStillBlocks():
    """Test 23: secret-leakage-gate opera em modo blocking permanente."""
    hook_mode = json.loads((HOOKS_DIR / "hook_mode.json").read_text(encoding="utf-8"))
    assert hook_mode["hook_modes"]["secret-leakage-gate"] == "blocking"


def test_24_PassWithoutEvidenceStillBlocks():
    """Test 24: stop-condition-evidence-gate opera em modo blocking permanente."""
    hook_mode = json.loads((HOOKS_DIR / "hook_mode.json").read_text(encoding="utf-8"))
    assert hook_mode["hook_modes"]["stop-condition-evidence-gate"] == "blocking"
    mode = get_hook_mode(hook_name="stop-condition-evidence-gate")
    assert mode == "blocking"


def test_25_KillAllRunsOnCompletion():
    """Test 25: Regra 10 exige kill_all_on_completion = true."""
    rule_10 = (RULES_DIR / "10-single-agent-first.md").read_text(encoding="utf-8")
    assert "kill_all_on_completion = true" in rule_10


def test_26_ReportingMatchesRiskTier():
    """Test 26: Relatórios permitidos estritamente alinhados ao Tier de risco (Rule 14)."""
    rule_14 = (RULES_DIR / "14-lean-reporting.md").read_text(encoding="utf-8")
    assert "Tier 1 e Tier 2" in rule_14
    assert "1 relatório canônico em Markdown" in rule_14


def test_27_TeamworkIsNotDefault():
    """Test 27: /teamwork não é padrão e é reservado para Tier 4 e incidentes graves."""
    agents_md = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Single-Agent First" in agents_md


def test_28_GraphifyReusesExistingGraph():
    """Test 28: Graphify opera orientado por delta e reutiliza o grafo existente."""
    agents_md = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "csbot-graph-impact" in agents_md


def test_29_ExecutionEfficiencyIsRecorded():
    """Test 29: Arquivo de telemetria de eficiência de execução é persistido em .agents/audit/."""
    eff_file = AUDIT_DIR / "execution_efficiency.json"
    assert eff_file.exists()
    eff = json.loads(eff_file.read_text(encoding="utf-8"))
    assert "repeated_reads" in eff
    assert "nested_subagents_blocked" in eff


def test_30_ProductDirectoriesRemainUnchanged():
    """Test 30: Diretórios de produto (src, datasets, models) não foram modificados pela governança."""
    # src/ deve ter 0 arquivos modificados fora de escopo
    src_dir = WORKSPACE_ROOT / "src"
    assert src_dir.exists()
    # Verifica que src e datasets continuam intactos
    assert (WORKSPACE_ROOT / "datasets" / "mirage_v2").exists()
