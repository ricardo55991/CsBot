#!/usr/bin/env python3
"""
Hook C: pre_training_gate.py
Evento: PreToolUse (run_command).
Detecta comandos de treinamento (train, fit, finetune, torchrun, accelerate launch),
ignorando comandos de listagem (Get-ChildItem, dir, ls, git status), testes unitários (pytest, dotnet test)
ou --help / --dry-run.
Valida o manifesto de prontidão (CSBOT_PRETRAINING_GATE_FILE ou .agents/audit/input_snapshot.json
ou .agents/audit/pre_training_gate_manifest.json).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common_hook_utils import (
    AUDIT_DIR,
    WORKSPACE_ROOT,
    extract_tool_input,
    fail_safe_main,
    format_hook_response,
    sanitize_text,
)

HOOK_NAME = "pre-training-gate"
DEFAULT_SNAPSHOT_PATH = AUDIT_DIR / "input_snapshot.json"
DEFAULT_MANIFEST_PATH = AUDIT_DIR / "pre_training_gate_manifest.json"

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

NON_TRAINING_PREFIXES = [
    r"^\s*get-childitem\b",
    r"^\s*get-content\b",
    r"^\s*get-filehash\b",
    r"^\s*test-path\b",
    r"^\s*select-string\b",
    r"^\s*(dir|ls|cat|type|echo|Write-Output)\b",
    r"^\s*git\s+(status|diff|log|show|branch)\b",
    r"^\s*dotnet\s+(test|build|restore|clean)\b",
    r"^\s*(pytest|python\s+-m\s+pytest|python\s+-m\s+unittest|python\s+-m\s+py_compile)\b",
]

TRAINING_PATTERNS = [
    re.compile(r"\b(?:torchrun|accelerate\s+launch|deepspeed)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:python|python3|py|uv\s+run|poetry\s+run)\b[^\n;|]*\b(?:train[a-z0-9_]*\.py|finetune[a-z0-9_]*\.py|fit[a-z0-9_]*\.py|[a-z0-9_]*_train\.py)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:python|python3|py)\s+-m\s+[a-z0-9_.]*(?:train|finetune|fit)[a-z0-9_.]*\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:train\.py|run_training\.py|train_model\.py|finetune\.py)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:--train|--do_train|--finetune|--epochs\s+\d+)\b",
        re.IGNORECASE,
    ),
]


def is_training_command(cmd: str) -> bool:
    """Detecta se o CommandLine inicia ou executa um job de treinamento."""
    if not cmd or not cmd.strip():
        return False
    stripped = cmd.strip()
    lower = stripped.lower()

    if "--help" in lower or " -h" in lower or "--dry-run" in lower or "--version" in lower:
        return False

    for prefix in NON_TRAINING_PREFIXES:
        if re.search(prefix, lower, re.IGNORECASE):
            return False

    for pat in TRAINING_PATTERNS:
        if pat.search(stripped):
            return True

    return False


def cmd_uses_test_for_tuning(cmd: str) -> Optional[str]:
    """Detecta se a própria linha de comando tenta passar o split Test para tuning/validação/calibração."""
    patterns = [
        r"(?:--val[-_]split|--eval[-_]split|--tuning[-_]split|--checkpoint[-_]split|--calibration[-_]split)\s*[=\s]\s*['\"]?test['\"]?\b",
        r"(?:--val[-_]data|--eval[-_]data|--tuning[-_]data)\s*[=\s]\s*[^\s]*test[^\s]*",
    ]
    for pat in patterns:
        m = re.search(pat, cmd, re.IGNORECASE)
        if m:
            return f"Argumento de linha de comando contamina o conjunto Test no treinamento/tuning: '{m.group(0)}'."
    return None


def is_test_split_authorized_for_evaluation(manifest_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Verifica se o uso do split Test está formalmente liberado para avaliação canônica final.
    Permite Test exclusivamente quando:
    - mode = FINAL_EVALUATION
    - checkpoint_frozen = true
    - config_frozen = true
    - thresholds_frozen = true
    """
    mode = str(manifest_data.get("mode", "")).strip().upper()
    ckpt_frozen = manifest_data.get("checkpoint_frozen") is True
    cfg_frozen = manifest_data.get("config_frozen") is True
    thresh_frozen = manifest_data.get("thresholds_frozen") is True

    missing: List[str] = []
    if mode != "FINAL_EVALUATION":
        missing.append(f"mode='{mode}' (exigido 'FINAL_EVALUATION')")
    if not ckpt_frozen:
        missing.append("checkpoint_frozen deve ser true")
    if not cfg_frozen:
        missing.append("config_frozen deve ser true")
    if not thresh_frozen:
        missing.append("thresholds_frozen deve ser true")

    if not missing:
        return True, []
    return False, missing


def resolve_manifest_path(payload: Dict[str, Any]) -> Tuple[Path, bool]:
    """Resolve qual arquivo de manifesto/snapshot de pré-treinamento deve ser validado."""
    tool_input = extract_tool_input(payload)
    explicit = (
        tool_input.get("pretraining_gate_file")
        or payload.get("pretraining_gate_file")
        or os.environ.get("CSBOT_PRETRAINING_GATE_FILE", "").strip()
    )
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = WORKSPACE_ROOT / p
        return p, p.exists()

    if DEFAULT_SNAPSHOT_PATH.exists():
        return DEFAULT_SNAPSHOT_PATH, True
    if DEFAULT_MANIFEST_PATH.exists():
        return DEFAULT_MANIFEST_PATH, True

    return DEFAULT_SNAPSHOT_PATH, False


def validate_pretraining_manifest(cmd: str, payload: Dict[str, Any]) -> List[str]:
    """Valida todos os pré-requisitos formais do Pre-Training Gate."""
    errors: List[str] = []

    cmd_contamination = cmd_uses_test_for_tuning(cmd)
    if cmd_contamination:
        errors.append(cmd_contamination)

    manifest_path, exists = resolve_manifest_path(payload)
    if not exists:
        errors.append(
            f"Manifesto de prontidão 'input_snapshot.json' ausente em '{sanitize_text(str(manifest_path))}'."
        )
        return errors

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Falha ao ler JSON do manifesto '{sanitize_text(str(manifest_path))}': {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append("O manifesto de pré-treinamento deve ser um objeto JSON.")
        return errors

    # 1. split_leakage == 0
    if data.get("split_leakage") != 0:
        errors.append(f"Campo 'split_leakage' deve ser exatamente 0 (atual: {data.get('split_leakage')!r}).")

    # 2. tests == "green"
    if str(data.get("tests", "")).strip().lower() != "green":
        errors.append(f"Campo 'tests' deve ser 'green' (atual: {data.get('tests')!r}).")

    # 3. dry_run == "pass"
    if str(data.get("dry_run", "")).strip().lower() != "pass":
        errors.append(f"Campo 'dry_run' deve ser 'pass' (atual: {data.get('dry_run')!r}).")

    # 4. dataset_hashes (dict ou list não vazio com SHA-256 de 64 chars)
    ds_hashes = data.get("dataset_hashes")
    if isinstance(ds_hashes, dict) and ds_hashes:
        for k, v in ds_hashes.items():
            if not SHA256_RE.match(str(v).strip()):
                errors.append(f"Hash inválido em dataset_hashes['{k}']: '{v}' (exigido 64 hex).")
    elif isinstance(ds_hashes, list) and ds_hashes:
        for idx, item in enumerate(ds_hashes):
            h = item.get("sha256", "") if isinstance(item, dict) else str(item)
            if not SHA256_RE.match(str(h).strip()):
                errors.append(f"Hash inválido em dataset_hashes[{idx}]: '{h}' (exigido 64 hex).")
    else:
        errors.append("Campo 'dataset_hashes' ausente ou vazio (exigido dicionário ou lista com hashes SHA-256 de 64 caracteres).")

    # 5. catalog_hash (64 chars hex)
    cat_hash = str(data.get("catalog_hash", "")).strip()
    if not SHA256_RE.match(cat_hash):
        errors.append(f"Campo 'catalog_hash' ausente ou inválido ('{cat_hash}'): exigido SHA-256 de 64 caracteres hexadecimais.")

    # 6. checkpoint_policy definida
    ckpt_policy = data.get("checkpoint_policy")
    if not ckpt_policy or (isinstance(ckpt_policy, str) and not ckpt_policy.strip()):
        errors.append("Campo 'checkpoint_policy' ausente ou vazio.")
    elif "test" in str(ckpt_policy).lower():
        errors.append(f"Regra 02 violada: 'checkpoint_policy' faz referência ao conjunto Test ({ckpt_policy!r}).")

    # 7. no_test_tuning == true e nenhuma referência ao split test em tuning_split / checkpoint_selection_split
    if data.get("no_test_tuning") is not True:
        errors.append(f"Campo 'no_test_tuning' deve ser booleano true (atual: {data.get('no_test_tuning')!r}).")

    for split_field in ("tuning_split", "checkpoint_selection_split", "calibration_split", "early_stopping_split"):
        val = str(data.get(split_field, "")).strip().lower()
        if "test" in val or "holdout" in val:
            errors.append(
                f"Regra 02 violada: '{split_field}' está configurado como '{data.get(split_field)}' (proibido usar Test/Holdout em tuning ou seleção de checkpoint)."
            )

    # 8. Verificação condicional de liberação do conjunto Test
    target_split = str(data.get("split") or data.get("eval_split") or "").strip().lower()
    if target_split in ("test", "holdout"):
        authorized, missing = is_test_split_authorized_for_evaluation(data)
        if not authorized:
            errors.append(
                f"Regra 02 violada: uso do conjunto Test permitido exclusivamente quando mode=FINAL_EVALUATION, checkpoint_frozen=true, config_frozen=true e thresholds_frozen=true. Pendências: {', '.join(missing)}."
            )

    return errors


def handle_pre_training_gate(payload: Dict[str, Any], mode: str, event: str) -> Dict[str, Any]:
    tool_input = extract_tool_input(payload)
    cmd = str(
        tool_input.get("CommandLine")
        or tool_input.get("command")
        or tool_input.get("cmd")
        or payload.get("CommandLine")
        or payload.get("command")
        or ""
    ).strip()

    if not is_training_command(cmd):
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=False,
            reason="Comando não inicia execução de treinamento de modelo.",
            payload=payload,
        )

    errors = validate_pretraining_manifest(cmd, payload)
    if not errors:
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=False,
            reason="Pre-training gate aprovado: input_snapshot.json íntegro, split_leakage=0, hashes SHA-256 válidos e Test set isolado.",
            payload=payload,
        )

    joined_errors = " | ".join(errors)
    reason = (
        f"BLOQUEIO [{HOOK_NAME}]: Execução de treinamento bloqueada por falha nos pré-requisitos de governança. "
        f"Motivo: {joined_errors} "
        "Ação corretiva: 1) Gere '.agents/audit/input_snapshot.json' antes de treinar; "
        "2) Garanta split_leakage=0, tests='green', dry_run='pass', dataset_hashes (SHA-256 64 hex), "
        "catalog_hash (64 hex), checkpoint_policy definida e no_test_tuning=true; "
        "3) Nunca utilize o split 'test' em tuning_split ou checkpoint_selection_split."
    )
    return format_hook_response(
        hook_name=HOOK_NAME,
        event=event,
        mode=mode,
        is_violation=True,
        reason=reason,
        payload=payload,
        extra={"validation_errors": errors},
    )


if __name__ == "__main__":
    fail_safe_main(HOOK_NAME, "PreToolUse", handle_pre_training_gate)
