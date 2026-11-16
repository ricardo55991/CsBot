#!/usr/bin/env python3
"""
Hook D: post_test_audit.py
Evento: PostToolUse (run_command).
Detecta execução de dotnet test, pytest ou scripts Python de teste.
Extrai do payload (CommandLine, output/result, error, workspacePaths) e grava em .agents/audit/last_test_execution.json:
command, working_directory, discovered, passed, failed, skipped, duration, exit_code, test_assemblies,
canonical_summary ("<passed>/<discovered>", impedindo 340340).
Se error estiver presente ou failed > 0 ou exit_code != 0, marca "status": "FAILED" e "block_pass_verdict": true.
Retorna {} no stdout (conforme contrato PostToolUse).
"""

from __future__ import annotations

import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from common_hook_utils import (
    AUDIT_DIR,
    WORKSPACE_ROOT,
    extract_tool_input,
    fail_safe_main,
    format_hook_response,
    sanitize_text,
    write_json_atomic,
)

HOOK_NAME = "post-test-audit"
LAST_TEST_EXECUTION_FILE = Path(os.environ.get("CSBOT_LAST_TEST_EXECUTION_FILE") or (AUDIT_DIR / "last_test_execution.json"))

TEST_CMD_PATTERNS = [
    re.compile(r"\bdotnet\s+test\b", re.IGNORECASE),
    re.compile(r"\bpytest\b", re.IGNORECASE),
    re.compile(r"\bpython(?:3)?\s+-m\s+unittest\b", re.IGNORECASE),
    re.compile(r"\bpython(?:3)?\s+[^\s;|&]*test[^\s;|&]*\.py\b", re.IGNORECASE),
]


def is_test_command(cmd: str) -> bool:
    """Verifica se o comando executado foi um runner de testes automatizados."""
    if not cmd or not cmd.strip():
        return False
    norm_cmd = cmd.replace("\\", "/")
    # Evita falsos positivos em scripts de hooks/auditoria internos que contenham a palavra 'test'
    if ".agents/hooks/post_test_audit.py" in norm_cmd:
        return False
    if "run_governance_redteam.py" in norm_cmd:
        return False
    if re.match(r"^\s*python(?:3)?(?:\.exe)?\s+-c\b", cmd, re.IGNORECASE):
        if not any(k in cmd for k in ("pytest", "unittest")):
            return False
    for pat in TEST_CMD_PATTERNS:
        if pat.search(cmd):
            return True
    return False


def parse_test_metrics(output: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai métricas canônicas de execução de testes de dotnet test / pytest / unittest."""
    passed: Optional[int] = None
    failed: Optional[int] = None
    skipped: Optional[int] = None
    discovered: Optional[int] = None
    duration: str = "0s"
    assemblies: List[str] = []
    summary_found = False

    # 1. Padrão VSTest / dotnet test (inglês e português)
    # Ex: Passed!  - Failed:     0, Passed:   340, Skipped:     0, Total:   340, Duration: 1 s - CsBot.Tests.dll (net8.0)
    # Ex: Aprovado!  - Com falha:     0, Aprovado:   340, Ignorado:     0, Total:   340, Duração: 2 s - CsBot.Tests.dll
    m_vstest = re.search(
        r"(?:Failed|Com falha)\s*:\s*(\d+)\s*,\s*(?:Passed|Aprovado)\s*:\s*(\d+)\s*,\s*(?:Skipped|Ignorado)\s*:\s*(\d+)\s*,\s*Total\s*:\s*(\d+)(?:\s*,\s*(?:Duration|Dura[çc][ãa]o)\s*:\s*([^-\r\n]+))?",
        output,
        re.IGNORECASE,
    )
    if m_vstest:
        failed = int(m_vstest.group(1))
        passed = int(m_vstest.group(2))
        skipped = int(m_vstest.group(3))
        discovered = int(m_vstest.group(4))
        if m_vstest.group(5):
            duration = m_vstest.group(5).strip()
        summary_found = True

    # Formato alternativo VSTest: Total tests: 340 / Passed: 340 / Failed: 0 / Skipped: 0
    if not summary_found:
        m_total = re.search(r"(?:Total\s+tests|Total\s+de\s+testes)\s*:\s*(\d+)", output, re.IGNORECASE)
        m_pass = re.search(r"(?:Passed|Aprovados?)\s*:\s*(\d+)", output, re.IGNORECASE)
        m_fail = re.search(r"(?:Failed|Com\s+falha)\s*:\s*(\d+)", output, re.IGNORECASE)
        m_skip = re.search(r"(?:Skipped|Ignorados?)\s*:\s*(\d+)", output, re.IGNORECASE)
        if m_total or m_pass or m_fail:
            passed = int(m_pass.group(1)) if m_pass else 0
            failed = int(m_fail.group(1)) if m_fail else 0
            skipped = int(m_skip.group(1)) if m_skip else 0
            discovered = int(m_total.group(1)) if m_total else (passed + failed + skipped)
            summary_found = True

    # 2. Padrão pytest (ex: "12 passed, 1 failed, 2 skipped in 0.45s" ou "340 passed in 1.20s")
    if not summary_found:
        p_pass = re.search(r"\b(\d+)\s+passed\b", output, re.IGNORECASE)
        p_fail = re.search(r"\b(\d+)\s+(?:failed|errors?)\b", output, re.IGNORECASE)
        p_skip = re.search(r"\b(\d+)\s+skipped\b", output, re.IGNORECASE)
        p_dur = re.search(r"\bin\s+([0-9.]+s)\b", output, re.IGNORECASE)
        if p_pass or p_fail or p_skip:
            passed = int(p_pass.group(1)) if p_pass else 0
            failed = int(p_fail.group(1)) if p_fail else 0
            skipped = int(p_skip.group(1)) if p_skip else 0
            discovered = passed + failed + skipped
            if p_dur:
                duration = p_dur.group(1)
            summary_found = True

    # 3. Padrão unittest (ex: "Ran 15 tests in 0.012s" ... "OK" ou "FAILED (failures=2)")
    if not summary_found:
        u_ran = re.search(r"Ran\s+(\d+)\s+tests?\s+in\s+([0-9.]+s)", output, re.IGNORECASE)
        if u_ran:
            discovered = int(u_ran.group(1))
            duration = u_ran.group(2)
            u_fail = re.search(r"FAILED\s*\([^)]*(?:failures|errors)\s*=\s*(\d+)", output, re.IGNORECASE)
            failed = int(u_fail.group(1)) if u_fail else 0
            skipped = 0
            passed = max(0, discovered - failed)
            summary_found = True

    # Extração de assemblies/arquivos de teste
    for m_dll in re.finditer(r"([\w.\-/\\]+(?:\.Tests?\.dll|test_[\w]+\.py|[\w]+_test\.py))", output, re.IGNORECASE):
        asm = sanitize_text(m_dll.group(1))
        if asm not in assemblies:
            assemblies.append(asm)

    # Fallback para campos explícitos no payload JSON
    for d in (payload, payload.get("toolResponse"), payload.get("tool_response")):
        if isinstance(d, dict):
            if passed is None and isinstance(d.get("passed"), int):
                passed = d["passed"]
                summary_found = True
            if failed is None and isinstance(d.get("failed"), int):
                failed = d["failed"]
                summary_found = True
            if skipped is None and isinstance(d.get("skipped"), int):
                skipped = d["skipped"]
                summary_found = True
            if discovered is None and isinstance(d.get("discovered"), int):
                discovered = d["discovered"]
                summary_found = True

    if not summary_found:
        return {
            "discovered": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration": duration,
            "test_assemblies": assemblies,
            "canonical_summary": "UNKNOWN",
        }

    passed = passed if passed is not None else 0
    failed = failed if failed is not None else 0
    skipped = skipped if skipped is not None else 0
    if discovered is None or discovered < (passed + failed + skipped):
        discovered = passed + failed + skipped

    return {
        "discovered": discovered,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
        "test_assemblies": assemblies,
        "canonical_summary": f"{passed}/{discovered}",
    }


def extract_exit_code(output: str, payload: Dict[str, Any], tool_input: Dict[str, Any], error_val: Any) -> int:
    """Determina o exit_code do comando a partir do payload ou da saída textual."""
    response_dicts = [payload, tool_input]
    for k in ("toolResponse", "tool_response", "result", "response", "data"):
        for src in (payload, tool_input):
            sub = src.get(k)
            if isinstance(sub, dict):
                response_dicts.append(sub)

    for d in response_dicts:
        for k in ("exit_code", "exitCode", "return_code", "returncode", "exit_status", "status_code"):
            if isinstance(d.get(k), int):
                return int(d[k])

    m_code = re.search(r"Command exited with code\s+(-?\d+)", output, re.IGNORECASE)
    if m_code:
        return int(m_code.group(1))

    if error_val:
        return 1
    return 0


def extract_output_from_step_file(artifact_dir_str: str, step_idx: Optional[int] = None) -> str:
    """Extrai a saída do comando do arquivo output.txt no diretório de steps gerado pelo Antigravity."""
    if not artifact_dir_str:
        return ""
    try:
        base_dir = Path(artifact_dir_str)
        # 1. Tenta stepIdx direto e vizinhos imediatos (offset de indexação do runner)
        if step_idx is not None:
            for idx in (step_idx, step_idx - 1, step_idx + 1):
                p = base_dir / ".system_generated" / "steps" / str(idx) / "output.txt"
                if p.exists() and p.is_file():
                    content = p.read_text(encoding="utf-8", errors="replace").strip()
                    if content:
                        return content
        # 2. Se stepIdx não foi fornecido ou não encontrou, busca nos steps numéricos mais recentes
        steps_dir = base_dir / ".system_generated" / "steps"
        if steps_dir.exists() and steps_dir.is_dir():
            subdirs = [d for d in steps_dir.iterdir() if d.is_dir() and d.name.isdigit()]
            if subdirs:
                subdirs.sort(key=lambda d: int(d.name), reverse=True)
                for sd in subdirs[:5]:
                    out_file = sd / "output.txt"
                    if out_file.exists() and out_file.is_file():
                        content = out_file.read_text(encoding="utf-8", errors="replace").strip()
                        if content:
                            return content
    except Exception:
        pass
    return ""


def extract_output_from_transcript(transcript_path_str: str, step_idx: Optional[int] = None) -> str:
    """Extrai a saída do comando do transcript_full.jsonl quando o runner Antigravity não a repassa diretamente no stdin."""
    if not transcript_path_str:
        return ""
    try:
        tp = Path(transcript_path_str)
        if not tp.exists():
            if tp.is_dir():
                cand = tp / "transcript_full.jsonl"
                if not cand.exists():
                    cand = tp / "transcript.jsonl"
                tp = cand
            if not tp.exists():
                return ""
        with tp.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if step_idx is not None:
            for line in reversed(lines):
                try:
                    record = json.loads(line)
                    if record.get("step_index") in (step_idx, step_idx + 1, step_idx - 1):
                        content = record.get("content") or record.get("text") or record.get("output") or ""
                        if content and isinstance(content, str):
                            return content
                except Exception:
                    continue
        for line in reversed(lines[-50:]):
            try:
                record = json.loads(line)
                content = record.get("content") or record.get("text") or record.get("output") or ""
                if isinstance(content, str) and content:
                    if any(kw in content for kw in ("Command output:", "test session starts", "Passed!", "Aprovado!", "Total tests:", "Ran ", "passed in", "failed in")):
                        return content
            except Exception:
                continue
    except Exception:
        pass
    return ""


def handle_post_test_audit(payload: Dict[str, Any], mode: str, event: str) -> Dict[str, Any]:
    try:
        (AUDIT_DIR / "raw_post_test_stdin.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass
    tool_input = extract_tool_input(payload)
    cmd = str(
        tool_input.get("CommandLine")
        or tool_input.get("command")
        or tool_input.get("cmd")
        or payload.get("CommandLine")
        or payload.get("command")
        or ""
    ).strip()

    if not is_test_command(cmd):
        return format_hook_response(
            hook_name=HOOK_NAME,
            event="PostToolUse",
            mode=mode,
            is_violation=False,
            reason="Comando executado não é uma suíte de testes.",
            payload=payload,
        )

    # Extrai texto de saída (output / result / stdout / stderr / toolResponse / tool_response)
    output_parts: List[str] = []
    response_dicts = [payload, tool_input]
    for k in ("toolResponse", "tool_response", "toolResult", "tool_result", "result", "response", "data"):
        for src in (payload, tool_input):
            sub = src.get(k)
            if isinstance(sub, dict):
                response_dicts.append(sub)

    for d in response_dicts:
        for k in ("output", "stdout", "stderr", "result", "text", "tool_output", "content"):
            val = d.get(k)
            if isinstance(val, str) and val.strip():
                if val not in output_parts:
                    output_parts.append(val)
    output_text = "\n".join(output_parts)

    if not output_text.strip():
        artifact_dir = str(payload.get("artifactDirectoryPath") or tool_input.get("artifactDirectoryPath") or "")
        step_idx = payload.get("stepIdx")
        if not isinstance(step_idx, int) and isinstance(tool_input.get("stepIdx"), int):
            step_idx = tool_input.get("stepIdx")
        if artifact_dir:
            output_text = extract_output_from_step_file(artifact_dir, step_idx if isinstance(step_idx, int) else None)

    if not output_text.strip():
        transcript_path_str = str(payload.get("transcriptPath") or tool_input.get("transcriptPath") or "")
        step_idx = payload.get("stepIdx")
        if not isinstance(step_idx, int) and isinstance(tool_input.get("stepIdx"), int):
            step_idx = tool_input.get("stepIdx")
        if transcript_path_str:
            output_text = extract_output_from_transcript(transcript_path_str, step_idx if isinstance(step_idx, int) else None)

    # Fallback determinístico para pytest em runtime Antigravity via .pytest_cache
    if not output_text.strip() and "pytest" in cmd.lower():
        pytest_cache_dir = WORKSPACE_ROOT / ".pytest_cache" / "v" / "cache"
        nodeids_file = pytest_cache_dir / "nodeids"
        lastfailed_file = pytest_cache_dir / "lastfailed"
        if nodeids_file.exists():
            try:
                import time
                if time.time() - nodeids_file.stat().st_mtime < 300:
                    with nodeids_file.open("r", encoding="utf-8") as f:
                        nodeids_list = json.load(f)
                    lastfailed_dict = {}
                    if lastfailed_file.exists():
                        with lastfailed_file.open("r", encoding="utf-8") as f:
                            lastfailed_dict = json.load(f)
                    if isinstance(nodeids_list, list) and nodeids_list:
                        target_match = re.search(r"([\w./\\-]+\.py)", cmd)
                        target_file = target_match.group(1).replace("\\", "/") if target_match else ""
                        if target_file and any(target_file in nid for nid in nodeids_list):
                            filtered_nodeids = [nid for nid in nodeids_list if target_file in nid]
                            filtered_failed = {k: v for k, v in lastfailed_dict.items() if target_file in k}
                        else:
                            filtered_nodeids = nodeids_list
                            filtered_failed = lastfailed_dict
                        failed_cnt = len(filtered_failed)
                        passed_cnt = max(0, len(filtered_nodeids) - failed_cnt)
                        discovered_cnt = len(filtered_nodeids)
                        output_text = f"============================= {passed_cnt} passed"
                        if failed_cnt > 0:
                            output_text += f", {failed_cnt} failed"
                        output_text += f" in 0.5s =============================\n"
                        for nid in filtered_nodeids:
                            asm_cand = nid.split("::")[0]
                            output_text += f"{asm_cand} PASSED\n"
            except Exception:
                pass

    error_val = payload.get("error") or tool_input.get("error")
    exit_code = extract_exit_code(output_text, payload, tool_input, error_val)
    metrics = parse_test_metrics(output_text, payload)

    is_unknown = (metrics["canonical_summary"] == "UNKNOWN")
    has_failure_text = bool(
        re.search(r"\b(?:Test Run Failed|Falha na execu[çc][ãa]o de teste|Build FAILED|FAILURES)\b", output_text, re.IGNORECASE)
    )
    is_failed = bool(error_val) or exit_code != 0 or metrics["failed"] > 0 or has_failure_text

    if is_failed:
        status = "FAILED"
        block_pass_verdict = True
    elif is_unknown:
        status = "UNKNOWN"
        block_pass_verdict = True
    else:
        status = "PASSED"
        block_pass_verdict = False

    workspace_paths = payload.get("workspacePaths") or tool_input.get("workspacePaths") or [str(WORKSPACE_ROOT)]
    working_dir = (
        payload.get("working_directory")
        or tool_input.get("working_directory")
        or tool_input.get("cwd")
        or (workspace_paths[0] if isinstance(workspace_paths, list) and workspace_paths else str(WORKSPACE_ROOT))
    )

    test_record = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": sanitize_text(cmd),
        "working_directory": sanitize_text(str(working_dir)),
        "discovered": metrics["discovered"],
        "passed": metrics["passed"],
        "failed": metrics["failed"],
        "skipped": metrics["skipped"],
        "duration": metrics["duration"],
        "exit_code": exit_code,
        "error": sanitize_text(str(error_val)) if error_val else None,
        "test_assemblies": metrics["test_assemblies"],
        "canonical_summary": metrics["canonical_summary"],
        "status": status,
        "block_pass_verdict": block_pass_verdict,
    }

    target_test_file = Path(
        os.environ.get("CSBOT_LAST_TEST_EXECUTION_FILE")
        or payload.get("last_test_execution_file")
        or tool_input.get("last_test_execution_file")
        or LAST_TEST_EXECUTION_FILE
    )

    write_json_atomic(target_test_file, test_record)

    reason = (
        f"Auditoria pós-teste registrada: status={test_record['status']}, "
        f"canonical_summary={test_record['canonical_summary']}, exit_code={exit_code}."
    )
    return format_hook_response(
        hook_name=HOOK_NAME,
        event="PostToolUse",
        mode=mode,
        is_violation=block_pass_verdict,
        reason=reason,
        payload=payload,
        extra=test_record,
    )


if __name__ == "__main__":
    fail_safe_main(HOOK_NAME, "PostToolUse", handle_post_test_audit)
