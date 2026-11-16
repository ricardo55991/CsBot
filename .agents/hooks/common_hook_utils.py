#!/usr/bin/env python3
"""
Utilitário compartilhado de governança determinística para os Hooks do CsBot no Antigravity.
Fornece leitura segura de stdin JSON, sanitização de dados sensíveis e caminhos pessoais,
determinação de modo de operação (audit-only vs blocking), gravação de log forense em JSONL
e wrapper fail-safe para todos os 5 hooks.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = WORKSPACE_ROOT / ".agents" / "hooks"
AUDIT_DIR = WORKSPACE_ROOT / ".agents" / "audit"
AUDIT_LOG_PATH = AUDIT_DIR / "hooks_audit.jsonl"
HOOK_MODE_FILE = HOOKS_DIR / "hook_mode.json"

USER_HOME_PATTERNS = [
    re.compile(r"C:\\Users\\ricar", re.IGNORECASE),
    re.compile(r"C:/Users/ricar", re.IGNORECASE),
]

SECRET_PATTERNS = [
    re.compile(
        r'(?i)(api[_-]?key|token|secret|password|passwd|authorization|bearer)\s*([:=])\s*(["\']?)([A-Za-z0-9_\-\.~+/=]{8,})\3'
    ),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]


def sanitize_text(value: str) -> str:
    """Substitui caminhos pessoais de C:\\Users\\ricar por <USER_HOME> e mascara segredos/tokens."""
    if not isinstance(value, str):
        return str(value)
    result = value
    for pat in USER_HOME_PATTERNS:
        result = pat.sub("<USER_HOME>", result)
    result = SECRET_PATTERNS[0].sub(r"\1\2\3<REDACTED_SECRET>\3", result)
    for pat in SECRET_PATTERNS[1:]:
        result = pat.sub("<REDACTED_SECRET>", result)
    return result


def sanitize_data(data: Any) -> Any:
    """Sanitiza recursivamente dicionários, listas e strings."""
    if isinstance(data, str):
        return sanitize_text(data)
    if isinstance(data, dict):
        sanitized_dict = {}
        for k, v in data.items():
            key_str = str(k)
            if any(
                s in key_str.lower()
                for s in ("secret", "password", "passwd", "api_key", "apikey", "auth_token", "access_token")
            ):
                sanitized_dict[sanitize_text(key_str)] = "<REDACTED_SECRET>"
            else:
                sanitized_dict[sanitize_text(key_str)] = sanitize_data(v)
        return sanitized_dict
    if isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data


def get_hook_mode(argv: Optional[list[str]] = None, hook_name: Optional[str] = None) -> str:
    """
    Determina se o hook está operando em 'audit-only' ou 'blocking'.
    Prioridade:
    1. Argumentos de linha de comando (--audit-only ou --blocking)
    2. Variável de ambiente CSBOT_HOOK_MODE ('audit' / 'audit-only' vs 'blocking')
    3. Arquivo .agents/hooks/hook_mode.json (por hook individual ou global)
    4. Default seguro: 'blocking'
    """
    args = argv if argv is not None else sys.argv[1:]
    if "--audit-only" in args or "--mode=audit" in args or "--mode=audit-only" in args:
        return "audit-only"
    if "--blocking" in args or "--mode=blocking" in args:
        return "blocking"

    env_mode = os.environ.get("CSBOT_HOOK_MODE", "").strip().lower()
    if env_mode in ("audit", "audit-only", "audit_only"):
        return "audit-only"
    if env_mode in ("blocking", "block", "enforce"):
        return "blocking"

    if HOOK_MODE_FILE.exists():
        try:
            cfg = json.loads(HOOK_MODE_FILE.read_text(encoding="utf-8"))
            if hook_name and "hook_modes" in cfg and hook_name in cfg["hook_modes"]:
                return str(cfg["hook_modes"][hook_name]).strip().lower()
            file_mode = str(cfg.get("mode", cfg.get("global_mode", ""))).strip().lower()
            if file_mode in ("audit", "audit-only", "audit_only"):
                return "audit-only"
            if file_mode in ("blocking", "block", "enforce"):
                return "blocking"
        except Exception:
            pass

    return "blocking"


def read_stdin_payload() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Lê e faz o parse do JSON enviado via stdin.
    Retorna (payload_dict, error_message).
    """
    try:
        if sys.stdin.isatty():
            return {}, None
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return {}, None
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return None, "Payload JSON no stdin não é um objeto (dict) válido."
        return parsed, None
    except Exception as exc:
        return None, f"JSON malformado ou falha de leitura no stdin: {exc}"


def extract_event_type(payload: Dict[str, Any], default_event: str = "PreToolUse") -> str:
    """Extrai o tipo de evento do payload ou retorna o default do hook."""
    for key in ("hook_event_name", "event", "hookEventName", "type"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return default_event


def extract_tool_name(payload: Dict[str, Any]) -> str:
    """Extrai o nome da ferramenta chamada no payload (suporta toolCall.name nativo do Antigravity e tool_name)."""
    tc = payload.get("toolCall")
    if isinstance(tc, dict):
        tc_name = tc.get("name") or tc.get("toolName")
        if isinstance(tc_name, str) and tc_name.strip():
            return tc_name.strip()
    for key in ("tool_name", "toolName", "tool", "name"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def extract_tool_input(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai os argumentos de entrada da ferramenta (suporta toolCall.args nativo do Antigravity e tool_input)."""
    tc = payload.get("toolCall")
    if isinstance(tc, dict):
        tc_args = tc.get("args") or tc.get("arguments") or tc.get("parameters") or tc.get("input")
        if isinstance(tc_args, dict):
            return tc_args
    for key in ("tool_input", "toolInput", "args", "arguments", "parameters", "input"):
        val = payload.get(key)
        if isinstance(val, dict):
            return val
    return payload


def write_audit_log(
    hook_name: str,
    event: str,
    mode: str,
    decision: str,
    reason: str,
    payload: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Grava uma entrada estruturada e sanitizada em .agents/audit/hooks_audit.jsonl."""
    try:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        record: Dict[str, Any] = {
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "hook_name": hook_name,
            "event": event,
            "mode": mode,
            "decision": decision,
            "reason": sanitize_text(reason),
        }
        if payload is not None:
            record["payload_summary"] = sanitize_data(payload)
        if extra is not None:
            record["details"] = sanitize_data(extra)

        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Não deixar falha secundária de disco mascarar a saída principal do hook
        pass


def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    """Grava um arquivo JSON de estado em .agents/audit/ sanitizando caminhos pessoais."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sanitized = sanitize_data(data)
    path.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def format_hook_response(
    hook_name: str,
    event: str,
    mode: str,
    is_violation: bool,
    reason: str,
    payload: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Formata a resposta padronizada do hook respeitando o contrato do evento
    (PreToolUse, PostToolUse, Stop) e o modo de operação (audit-only vs blocking).
    """
    clean_reason = sanitize_text(reason)

    if not is_violation:
        decision = "allow" if event != "PostToolUse" else "observed"
        write_audit_log(hook_name, event, mode, decision, clean_reason, payload, extra)
        if event == "PostToolUse":
            return {}
        return {"decision": "allow", "reason": clean_reason}

    # Caso haja violação:
    if mode == "audit-only":
        audit_reason = f"[AUDIT-ONLY] Violação registrada sem bloqueio: {clean_reason}"
        write_audit_log(hook_name, event, mode, "audit_violation_allow", audit_reason, payload, extra)
        if event == "PostToolUse":
            return {}
        return {"decision": "allow", "reason": audit_reason}

    # Modo blocking:
    if event == "Stop":
        write_audit_log(hook_name, event, mode, "continue", clean_reason, payload, extra)
        return {"decision": "continue", "reason": clean_reason}
    if event == "PostToolUse":
        write_audit_log(hook_name, event, mode, "post_tool_flagged", clean_reason, payload, extra)
        return {}

    write_audit_log(hook_name, event, mode, "deny", clean_reason, payload, extra)
    return {"decision": "deny", "reason": clean_reason}


def fail_safe_main(
    hook_name: str,
    default_event: str,
    handler: Callable[[Dict[str, Any], str, str], Dict[str, Any]],
) -> None:
    """
    Wrapper de execução determinística e fail-safe (fail-closed para operações críticas).
    Se o JSON no stdin for malformado ou ocorrer exceção interna não tratada:
    - Em PreToolUse: retorna {"decision": "deny", "reason": ...} (ou allow com aviso se audit-only)
    - Em Stop: retorna {"decision": "continue", "reason": ...}
    - Em PostToolUse: grava erro de auditoria e retorna {}
    """
    mode = get_hook_mode(hook_name=hook_name)
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass
    payload, parse_error = read_stdin_payload()

    if parse_error is not None or payload is None:
        reason = (
            f"BLOQUEIO [{hook_name}]: Falha fail-safe na leitura do payload stdin ({parse_error}). "
            f"Ação corretiva: Envie um objeto JSON válido via stdin para o hook {hook_name}."
        )
        resp = format_hook_response(
            hook_name=hook_name,
            event=default_event,
            mode=mode,
            is_violation=True,
            reason=reason,
            payload={"raw_stdin_error": parse_error},
        )
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.exit(0)

    event = extract_event_type(payload, default_event=default_event)
    try:
        response = handler(payload, mode, event)
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.exit(0)
    except Exception as exc:
        tb = sanitize_text(traceback.format_exc())
        reason = (
            f"BLOQUEIO [{hook_name}]: Erro interno inesperado capturado pelo fail-safe ({exc}). "
            f"Ação corretiva: Verifique os parâmetros de entrada e consulte .agents/audit/hooks_audit.jsonl."
        )
        resp = format_hook_response(
            hook_name=hook_name,
            event=event,
            mode=mode,
            is_violation=True,
            reason=reason,
            payload=payload,
            extra={"traceback": tb},
        )
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.exit(0)
