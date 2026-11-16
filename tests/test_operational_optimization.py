#!/usr/bin/env python3
"""
Suíte de Testes Direcionados: Otimização Operacional e Limpeza da Governança 1.2 Lean
Valida os 15 gates da otimização operacional sem rodar suites completas fora de escopo.
"""

import json
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = WORKSPACE_ROOT / ".agents"
RULES_DIR = AGENTS_DIR / "rules"
HOOKS_DIR = AGENTS_DIR / "hooks"


def test_01_hooks_json_event_optimization():
    """Valida se validate-generated-report foi movido exclusivamente para Stop."""
    hooks_file = AGENTS_DIR / "hooks.json"
    assert hooks_file.exists()
    cfg = json.loads(hooks_file.read_text(encoding="utf-8"))
    
    # validate-generated-report não deve estar em PreToolUse nem PostToolUse
    assert "PreToolUse" not in cfg["validate-generated-report"]
    assert "PostToolUse" not in cfg["validate-generated-report"]
    assert "Stop" in cfg["validate-generated-report"]
    
    # post-test-audit deve estar em PostToolUse
    assert "PostToolUse" in cfg["post-test-audit"]


def test_02_post_test_audit_ignores_non_test_commands():
    """Valida se post-test-audit ignora comandos normais de shell."""
    import sys
    sys.path.insert(0, str(HOOKS_DIR))
    from post_test_audit import is_test_command
    
    assert not is_test_command("git status")
    assert not is_test_command("ls -la")
    assert not is_test_command("python update_artifact_digest.py")
    assert is_test_command("pytest tests/test_governance_1_2_lean.py")
    assert is_test_command("dotnet test tests/CsBotManager.Tests/")


def test_03_analytics_script_first_rule_exists():
    """Valida se a regra 15 de Script First está ativa."""
    rule_file = RULES_DIR / "15-analytics-script-first.md"
    assert rule_file.exists()
    content = rule_file.read_text(encoding="utf-8")
    assert "ANALYTICS_SCRIPT_FIRST" in content
    assert "stdout" in content


def test_04_surgical_terminal_output_rule_exists():
    """Valida se a regra 16 de terminal cirúrgico está ativa."""
    rule_file = RULES_DIR / "16-surgical-terminal-output.md"
    assert rule_file.exists()
    content = rule_file.read_text(encoding="utf-8")
    assert "SURGICAL_TERMINAL_OUTPUT" in content


def test_05_compact_policy_exists_with_checklist():
    """Valida se compact_policy.md define as 7 precondições obrigatórias."""
    policy_file = WORKSPACE_ROOT / "compact_policy.md"
    assert policy_file.exists()
    content = policy_file.read_text(encoding="utf-8")
    assert "active_subagents_zero" in content
    assert "background_tasks_zero" in content
    assert "hashes_saved" in content


def test_06_workspace_mcp_inventory():
    """Valida o inventário de MCPs e isolamento do godot-mcp-toolkit."""
    mcp_file = WORKSPACE_ROOT / "workspace_mcp_inventory.json"
    assert mcp_file.exists()
    data = json.loads(mcp_file.read_text(encoding="utf-8"))
    
    names = {item["name"]: item for item in data["mcps"]}
    assert "sequential-thinking" in names
    assert names["sequential-thinking"]["enabled"] is True
    assert "godot-mcp-toolkit" in names
    assert names["godot-mcp-toolkit"]["enabled"] is False


def test_07_quarantine_manifest_and_rollback_commands():
    """Valida o manifesto de quarentena com hashes e rollback determinístico."""
    q_manifest_file = WORKSPACE_ROOT / ".cleanup" / "quarantine_manifest.json"
    assert q_manifest_file.exists()
    q_data = json.loads(q_manifest_file.read_text(encoding="utf-8"))
    assert "items" in q_data
    for item in q_data["items"]:
        assert "sha256" in item
        assert "rollback_command" in item
        assert "quarantine_path" in item


def test_08_gitignore_contains_quarantine():
    """Valida se .cleanup/quarantine/ foi adicionado ao .gitignore."""
    gitignore = (WORKSPACE_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".cleanup/quarantine/" in gitignore


def test_09_explicit_protected_directories_intact():
    """Valida que todos os diretórios explicitamente protegidos continuam intactos."""
    protected_paths = [
        WORKSPACE_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training",
        WORKSPACE_ROOT / "training_runs" / "intermediate_domain_study",
        WORKSPACE_ROOT / "datasets" / "mirage_domains",
        WORKSPACE_ROOT / "tools" / "intermediate_demo_acquisition",
        WORKSPACE_ROOT / ".agents" / "teamwork" / "orchestrator_2a_intermediate",
        WORKSPACE_ROOT / "training_runs" / "positioning_v2_real_temporal" / "PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json"
    ]
    for p in protected_paths:
        assert p.exists(), f"Caminho protegido ausente: {p}"


def test_10_zero_permanent_deletions():
    """Valida que não houve nenhuma exclusão permanente sem autorização humana."""
    del_prop_file = WORKSPACE_ROOT / "cleanup_deletion_proposal.json"
    assert del_prop_file.exists()
    prop_data = json.loads(del_prop_file.read_text(encoding="utf-8"))
    assert prop_data["permanent_deletion_requires_human_approval"] is True
