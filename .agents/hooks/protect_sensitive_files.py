#!/usr/bin/env python3
"""
Hook A: protect_sensitive_files.py
Evento: PreToolUse (write_to_file|replace_file_content|multi_replace_file_content|write_file|edit_file|run_command)
Protege: *.onnx, *.pt, de_mirage.json, *split*.json, *manifest*.json, *contract*.json, *catalog*.json
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common_hook_utils import (
    AUDIT_DIR,
    WORKSPACE_ROOT,
    extract_tool_input,
    extract_tool_name,
    fail_safe_main,
    format_hook_response,
    sanitize_text,
)

HOOK_NAME = "protect-sensitive-files"
DEFAULT_AUTH_FILE = AUDIT_DIR / "sensitive_file_authorization.json"

SENSITIVE_BASENAME_PATTERNS = [
    "*.onnx",
    "*.pt",
    "de_mirage.json",
    "*split*.json",
    "*split*.parquet",
    "*split*.npz",
    "*manifest*.json",
    "*contract*.json",
    "*catalog*.json",
]

# Arquivos de auditoria interna gerenciados pelos próprios hooks não são artefatos de modelo/dataset
INTERNAL_EXEMPT_NAMES = {
    "pre_training_gate_manifest.json",
    "sensitive_file_authorization.json",
    "last_test_execution.json",
    "last_report_validation.json",
    "deliverable_evidence.json",
    "hooks_config.json",
    "hook_mode.json",
    "hooks.json",
    "skills.json",
}

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

READ_ONLY_CMD_PATTERNS = [
    r"^\s*get-filehash\b",
    r"^\s*get-content\b",
    r"^\s*test-path\b",
    r"^\s*select-object\b",
    r"^\s*get-item\b",
    r"^\s*get-childitem\b",
    r"^\s*git\s+(status|diff|log|show)\b",
    r"^\s*(dir|ls|cat|type|head|tail)\b",
    r"^\s*pytest\b",
    r"^\s*(?:python|py|python3)\s+[^\n;|]*\b(?:audit_|verify_|check_|inspect_|test_|analyze_|create_)[a-z0-9_]*\.py\b",
]

WRITE_CMD_INDICATORS = [
    r"\bcopy-item\b",
    r"\bmove-item\b",
    r"\bremove-item\b",
    r"\bset-content\b",
    r"\badd-content\b",
    r"\bout-file\b",
    r"\bnew-item\b",
    r"\bcp\b",
    r"\bmv\b",
    r"\brm\b",
    r"\bdel\b",
    r">",
    r"\btee\b",
    r"--output",
    r"\bexport\b",
]


def is_sensitive_path(path_str: str) -> bool:
    """Verifica se um caminho corresponde a um artefato sensível protegido pela regra 06."""
    if not path_str or not isinstance(path_str, str):
        return False
    norm = path_str.strip().strip("\"'").replace("\\", "/")
    basename = os.path.basename(norm).lower()
    if not basename or basename in {n.lower() for n in INTERNAL_EXEMPT_NAMES}:
        return False

    if "src/csbotmanager/mapprofiles/" in norm.lower() and basename.endswith(".json"):
        return True

    for pat in SENSITIVE_BASENAME_PATTERNS:
        if fnmatch.fnmatch(basename, pat.lower()):
            return True
    return False


def is_read_only_command(cmd: str) -> bool:
    """Detecta se um comando shell é puramente de leitura ou dry-run."""
    if not cmd or not cmd.strip():
        return True
    lower = cmd.strip().lower()
    if "--dry-run" in lower or "--help" in lower or "py_compile" in lower:
        return True

    # Se possui redirecionamento de escrita ou cmdlets de mutação explícitos, não é read-only
    for wpat in WRITE_CMD_INDICATORS:
        if re.search(wpat, lower, re.IGNORECASE):
            return False

    for rpat in READ_ONLY_CMD_PATTERNS:
        if re.search(rpat, lower, re.IGNORECASE):
            return True

    return False


def extract_sensitive_targets_from_command(cmd: str) -> List[str]:
    """Extrai possíveis referências a arquivos sensíveis em um comando shell de escrita."""
    if is_read_only_command(cmd):
        return []

    targets: List[str] = []
    tokens = re.findall(r'[^\s"\';|&><]+|"[^"]+"|\'[^\']+\'', cmd)
    for tok in tokens:
        cleaned = tok.strip("\"'")
        if is_sensitive_path(cleaned):
            targets.append(cleaned)
    return targets


def extract_target_files(payload: Dict[str, Any]) -> Tuple[List[str], bool]:
    """
    Extrai os arquivos-alvo da operação.
    Retorna (lista_de_arquivos_sensiveis, is_read_only_op).
    """
    tool_name = extract_tool_name(payload).lower()
    tool_input = extract_tool_input(payload)

    # Verifica se é um comando de terminal
    cmd = (
        tool_input.get("CommandLine")
        or tool_input.get("command")
        or tool_input.get("cmd")
        or payload.get("CommandLine")
        or payload.get("command")
    )
    if isinstance(cmd, str) and (tool_name in ("run_command", "bash", "powershell", "") and not any(
        k in tool_input for k in ("TargetFile", "Path", "file_path", "AbsolutePath")
    )):
        if is_read_only_command(cmd):
            return [], True
        return extract_sensitive_targets_from_command(cmd), False

    # Ferramentas de edição/escrita de arquivo
    candidate_paths: List[str] = []
    for key in ("TargetFile", "Path", "file_path", "filepath", "AbsolutePath", "target_file", "file"):
        val = tool_input.get(key) or payload.get(key)
        if isinstance(val, str) and val.strip():
            candidate_paths.append(val.strip())

    sensitive = [p for p in candidate_paths if is_sensitive_path(p)]
    return sensitive, False


def validate_authorization_file(target_files: List[str]) -> Tuple[bool, str]:
    """
    Valida o arquivo de autorização prévia para artefatos sensíveis:
    Exige backup_path, previous_sha256 (64 hex), planned_diff, rollback_command, approved_phase.
    """
    env_auth = os.environ.get("CSBOT_SENSITIVE_AUTH_FILE", "").strip()
    auth_path = Path(env_auth) if env_auth else DEFAULT_AUTH_FILE

    if not auth_path.exists():
        return (
            False,
            f"Arquivo de autorização ausente em '{sanitize_text(str(auth_path))}' para modificar {target_files}.",
        )

    try:
        data = json.loads(auth_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"Arquivo de autorização inválido (JSON malformado): {exc}"

    if not isinstance(data, dict):
        return False, "Conteúdo do arquivo de autorização deve ser um objeto JSON."

    required_fields = ["backup_path", "previous_sha256", "planned_diff", "rollback_command", "approved_phase"]
    missing = [f for f in required_fields if not str(data.get(f, "")).strip()]
    if missing:
        return False, f"Campos obrigatórios ausentes ou vazios na autorização: {', '.join(missing)}."

    prev_sha = str(data.get("previous_sha256", "")).strip()
    if not SHA256_RE.match(prev_sha):
        return (
            False,
            f"Campo 'previous_sha256' inválido ('{prev_sha}'): deve conter exatamente 64 caracteres hexadecimais sem truncamento.",
        )

    backup_str = str(data.get("backup_path", "")).strip()
    backup_verified = bool(data.get("backup_verified", False))
    backup_path = Path(backup_str)
    if not backup_path.is_absolute():
        backup_path = WORKSPACE_ROOT / backup_path

    if not backup_verified and not backup_path.exists():
        return (
            False,
            f"O arquivo de backup declarado em 'backup_path' ('{sanitize_text(backup_str)}') não foi encontrado no disco.",
        )

    return True, "Autorização de artefato sensível verificada com hash SHA-256 completo e backup."


def check_role_isolation(payload: Dict[str, Any]) -> Optional[str]:
    """
    Regra 09 (Subagent Role Isolation):
    - Implementer não pode editar relatório do auditor (*audit*.md, *audit*.json, *skeptic*.json, *validation_report*.md, phase_gate_report.md, deliverable_evidence.json).
    - Auditor / Adversarial Reviewer / Success Auditor / Explorer não podem alterar implementação nem corrigir falhas (devem devolver ao Orchestrator).
    """
    role = (
        str(payload.get("activeRole") or payload.get("role") or os.environ.get("CSBOT_ACTIVE_ROLE", ""))
        .strip()
        .lower()
    )
    if not role:
        return None

    tool_input = extract_tool_input(payload)
    candidate_paths: List[str] = []
    for key in ("TargetFile", "Path", "file_path", "filepath", "AbsolutePath", "target_file", "file"):
        val = tool_input.get(key) or payload.get(key)
        if isinstance(val, str) and val.strip():
            candidate_paths.append(val.strip().replace("\\", "/").lower())

    read_only_roles = {
        "explorer",
        "csbot-explorer",
        "auditor",
        "adversarial-reviewer",
        "csbot-adversarial-reviewer",
        "success-auditor",
        "csbot-success-auditor",
    }
    if role in read_only_roles and candidate_paths:
        return (
            f"Violação de Isolamento de Papéis (Regra 09): O papel '{role}' é estritamente somente leitura e "
            "não pode alterar implementação nem corrigir falhas. Devolva os achados ao Orchestrator."
        )

    if role in {"implementer", "csbot-implementer"}:
        auditor_patterns = [
            "*audit*.md",
            "*audit*.json",
            "*skeptic*.json",
            "*validation_report*.md",
            "phase_gate_report.md",
            "deliverable_evidence.json",
        ]
        for p in candidate_paths:
            bname = os.path.basename(p)
            if any(fnmatch.fnmatch(bname, pat) for pat in auditor_patterns):
                return (
                    f"Violação de Isolamento de Papéis (Regra 09): O Implementer ('{role}') não pode editar ou "
                    f"sobrescrever relatório/evidência do auditor ('{bname}')."
                )
    return None


def handle_protect_sensitive_files(payload: Dict[str, Any], mode: str, event: str) -> Dict[str, Any]:
    role_err = check_role_isolation(payload)
    if role_err:
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=True,
            reason=f"BLOQUEIO [{HOOK_NAME}]: {role_err} Ação corretiva: Respeite a separação de papéis (Regra 09) e devolva ao Orchestrator.",
            payload=payload,
            extra={"role_isolation_error": role_err},
        )

    sensitive_targets, is_readonly = extract_target_files(payload)

    if is_readonly:
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=False,
            reason="Operação de leitura ou dry-run permitida.",
            payload=payload,
        )

    if not sensitive_targets:
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=False,
            reason="Nenhum artefato sensível afetado pela operação.",
            payload=payload,
        )

    is_valid, detail = validate_authorization_file(sensitive_targets)
    if is_valid:
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=False,
            reason="Autorização de artefato sensível verificada com hash e backup.",
            payload=payload,
            extra={"sensitive_targets": sensitive_targets},
        )

    reason = (
        f"BLOQUEIO [{HOOK_NAME}]: Modificação em artefato sensível bloqueada ({', '.join(sensitive_targets)}). "
        f"Motivo: {detail} "
        "Ação corretiva: 1) Crie um backup imutável do arquivo original; "
        "2) Calcule o SHA-256 completo (64 caracteres hexadecimais); "
        "3) Registre backup_path, previous_sha256 (64 hex), planned_diff, rollback_command e approved_phase "
        "em .agents/audit/sensitive_file_authorization.json antes de modificar o artefato."
    )
    return format_hook_response(
        hook_name=HOOK_NAME,
        event=event,
        mode=mode,
        is_violation=True,
        reason=reason,
        payload=payload,
        extra={"sensitive_targets": sensitive_targets, "validation_detail": detail},
    )


if __name__ == "__main__":
    fail_safe_main(HOOK_NAME, "PreToolUse", handle_protect_sensitive_files)
