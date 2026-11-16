#!/usr/bin/env python3
"""
Hook E: stop_condition_evidence_gate.py
Evento: Stop.
Verifica antes do encerramento da tarefa/fase:
1) Se .agents/audit/last_test_execution.json tem "status": "FAILED" enquanto o encerramento/evidência declara "verdict": "PASS" -> Bloqueia o encerramento!
2) Se .agents/audit/last_report_validation.json tem "status": "FAILED" -> Bloqueia o encerramento!
3) Verifica o arquivo deliverable_evidence.json (via CSBOT_DELIVERABLE_EVIDENCE_FILE, ou .agents/audit/deliverable_evidence.json, ou deliverable_evidence.json na raiz):
   - Valida phase, verdict (PASS, CONDITIONAL, FAIL) e array não-vazio claims.
   - Para cada item em claims, exige claim_id, claim, evidence_files (lista não vazia), raw_sources (lista não vazia), reproduction_command (string não vazia) e validator (string não vazia).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common_hook_utils import (
    AUDIT_DIR,
    WORKSPACE_ROOT,
    fail_safe_main,
    format_hook_response,
    sanitize_text,
)

HOOK_NAME = "stop-condition-evidence-gate"
LAST_TEST_EXECUTION_FILE = AUDIT_DIR / "last_test_execution.json"
LAST_REPORT_VALIDATION_FILE = AUDIT_DIR / "last_report_validation.json"
DEFAULT_AUDIT_EVIDENCE_FILE = AUDIT_DIR / "deliverable_evidence.json"
ROOT_EVIDENCE_FILE = WORKSPACE_ROOT / "deliverable_evidence.json"

ALLOWED_VERDICTS = {"PASS", "CONDITIONAL", "FAIL"}


def resolve_evidence_file(payload: Dict[str, Any]) -> Tuple[Path, bool]:
    """Localiza o arquivo deliverable_evidence.json configurado ou nos caminhos canônicos."""
    explicit = (
        payload.get("deliverable_evidence_file")
        or os.environ.get("CSBOT_DELIVERABLE_EVIDENCE_FILE", "").strip()
    )
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = WORKSPACE_ROOT / p
        return p, p.exists()

    if DEFAULT_AUDIT_EVIDENCE_FILE.exists():
        return DEFAULT_AUDIT_EVIDENCE_FILE, True
    if ROOT_EVIDENCE_FILE.exists():
        return ROOT_EVIDENCE_FILE, True

    return DEFAULT_AUDIT_EVIDENCE_FILE, False


def check_last_report_validation() -> Optional[str]:
    """Verifica se a última validação de relatório falhou."""
    if not LAST_REPORT_VALIDATION_FILE.exists():
        return None
    try:
        data = json.loads(LAST_REPORT_VALIDATION_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and str(data.get("status", "")).upper() == "FAILED":
            v_list = data.get("violations", [])
            detail = "; ".join(str(x) for x in v_list[:3]) if isinstance(v_list, list) else "violações detectadas"
            return (
                f"Última validação de relatório em '.agents/audit/last_report_validation.json' está marcada como FAILED ({detail})."
            )
    except Exception as exc:
        return f"Erro ao ler '.agents/audit/last_report_validation.json': {exc}"
    return None


def check_last_test_execution(declared_verdict: str) -> Optional[str]:
    """Verifica se o último teste falhou enquanto tenta-se emitir veredito PASS."""
    if not LAST_TEST_EXECUTION_FILE.exists():
        return None
    try:
        data = json.loads(LAST_TEST_EXECUTION_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            status = str(data.get("status", "")).upper()
            block_pass = bool(data.get("block_pass_verdict", False))
            if (status == "FAILED" or block_pass) and declared_verdict.upper() == "PASS":
                summary = data.get("canonical_summary", "0/0")
                cmd = data.get("command", "<unknown>")
                return (
                    f"Teste falho impede emissão de veredito PASS (última execução '{cmd}' teve status=FAILED, summary={summary})."
                )
    except Exception as exc:
        return f"Erro ao ler '.agents/audit/last_test_execution.json': {exc}"
    return None


def validate_deliverable_evidence(evidence_path: Path) -> Tuple[Optional[str], List[str]]:
    """
    Valida a estrutura e completude de deliverable_evidence.json.
    Retorna (declared_verdict, list_of_errors).
    """
    errors: List[str] = []
    try:
        data = json.loads(evidence_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"JSON inválido em '{sanitize_text(str(evidence_path))}': {exc}"]

    if not isinstance(data, dict):
        return None, ["O conteúdo de deliverable_evidence.json deve ser um objeto JSON."]

    phase = str(data.get("phase", "")).strip()
    if not phase:
        errors.append("Campo obrigatório 'phase' está ausente ou vazio.")

    verdict = str(data.get("verdict", "")).strip().upper()
    if verdict not in ALLOWED_VERDICTS:
        errors.append(
            f"Campo 'verdict' inválido ('{data.get('verdict')}'): deve ser exclusivamente 'PASS', 'CONDITIONAL' ou 'FAIL'."
        )

    claims = data.get("claims")
    if not isinstance(claims, list) or len(claims) == 0:
        errors.append("Campo 'claims' deve ser uma lista não-vazia de afirmações verificáveis.")
        return verdict, errors

    for idx, item in enumerate(claims):
        prefix = f"claims[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve ser um objeto JSON.")
            continue

        claim_id = str(item.get("claim_id", "")).strip()
        if not claim_id:
            errors.append(f"{prefix}: campo 'claim_id' ausente ou vazio.")
        else:
            prefix = f"claims[{idx} ({claim_id})]"

        if not str(item.get("claim", "")).strip():
            errors.append(f"{prefix}: campo 'claim' ausente ou vazio.")

        ev_files = item.get("evidence_files")
        if not isinstance(ev_files, list) or len(ev_files) == 0 or not all(str(x).strip() for x in ev_files):
            errors.append(f"{prefix}: 'evidence_files' deve ser uma lista não-vazia de arquivos de evidência.")

        raw_sources = item.get("raw_sources")
        if not isinstance(raw_sources, list) or len(raw_sources) == 0 or not all(str(x).strip() for x in raw_sources):
            errors.append(f"{prefix}: 'raw_sources' deve ser uma lista não-vazia de fontes/artefatos brutos.")

        if not str(item.get("reproduction_command", "")).strip():
            errors.append(f"{prefix}: 'reproduction_command' ausente ou vazio.")

        validator_val = str(item.get("validator", "")).strip()
        if not validator_val:
            errors.append(f"{prefix}: 'validator' ausente ou vazio.")
        elif validator_val.lower() in {"implementer", "csbot-implementer", "self", "self-validated"}:
            errors.append(
                f"{prefix}: Violação das Regras 07 e 09 — o Implementer ('{validator_val}') não pode ser o validador do próprio claim."
            )

    return verdict, errors


def handle_stop_condition_evidence_gate(payload: Dict[str, Any], mode: str, event: str) -> Dict[str, Any]:
    errors: List[str] = []

    # 1. Valida deliverable_evidence.json
    evidence_path, exists = resolve_evidence_file(payload)
    declared_verdict = str(payload.get("verdict", "")).strip().upper()

    if not exists:
        errors.append(
            f"Arquivo 'deliverable_evidence.json' não encontrado em '{sanitize_text(str(evidence_path))}'."
        )
    else:
        ev_verdict, ev_errors = validate_deliverable_evidence(evidence_path)
        if ev_verdict and not declared_verdict:
            declared_verdict = ev_verdict
        errors.extend(ev_errors)

    if not declared_verdict:
        declared_verdict = "PASS"

    # 2. Verifica se o último teste falhou enquanto o veredito é PASS
    test_err = check_last_test_execution(declared_verdict)
    if test_err:
        errors.insert(0, test_err)

    # 3. Verifica se o último relatório validado falhou
    report_err = check_last_report_validation()
    if report_err:
        errors.append(report_err)

    if not errors:
        return format_hook_response(
            hook_name=HOOK_NAME,
            event="Stop",
            mode=mode,
            is_violation=False,
            reason=f"Stop condition evidence gate aprovado (veredito={declared_verdict}, evidências brutas e testes íntegros).",
            payload=payload,
            extra={"evidence_file": sanitize_text(str(evidence_path)), "verdict": declared_verdict},
        )

    joined_errors = " | ".join(errors)
    reason = (
        f"BLOQUEIO [{HOOK_NAME}]: Encerramento impedido pelo gate de evidências. "
        f"Motivo: {joined_errors} "
        "Ação corretiva: Preencha todos os campos obrigatórios (phase, verdict, e em cada claim: claim_id, claim, "
        "evidence_files, raw_sources, reproduction_command, validator) em .agents/audit/deliverable_evidence.json, "
        "corrija relatórios reprovados e garanta que nenhum veredito PASS seja emitido com teste falho."
    )
    return format_hook_response(
        hook_name=HOOK_NAME,
        event="Stop",
        mode=mode,
        is_violation=True,
        reason=reason,
        payload=payload,
        extra={"errors": errors},
    )


if __name__ == "__main__":
    fail_safe_main(HOOK_NAME, "Stop", handle_stop_condition_evidence_gate)
