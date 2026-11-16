#!/usr/bin/env python3
"""
resume_download.py — Retomada determinística de downloads interrompidos.

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §9 (resumable downloads,
exponential backoff, rate limiting, checksum, retry limit, audit log, credential redaction).

O que faz
---------
Retoma um download a partir do estado persistido por `download_demo.py`:

- `<arquivo>.part`  conteúdo parcial já baixado (a origem do offset);
- `<arquivo>.state.json`  estado da tentativa anterior (offset, tentativas, status).

O offset de retomada é sempre `os.path.getsize(.part)` — o arquivo parcial é a fonte de verdade, não
o número gravado no estado (que pode estar desatualizado após interrupção abrupta).

**A URL não é persistida.** O estado guarda apenas um identificador estável
(`source_url_reference`), nunca a URL assinada nem parâmetro de autenticação. Por isso a retomada
exige que o operador re-resolva a URL e a informe em `--url` — o que preserva o teste 8
(`SignedUrlsAreNotPersisted`) sem impedir a retomada.

Modos
-----
`--scan`     lista os pares `.part` + `.state.json` encontrados e o que falta baixar.
`--execute`  executa a retomada real (bloqueada nesta fase por ausência de fonte aprovada).
(padrão)     `--dry-run`: calcula e imprime o plano de retomada, sem rede e sem tocar em arquivos.

`--self-test` exercita a lógica de offset/estado em diretório temporário.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação (ou self-test falho) · 2 = erro de uso / política
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
DEFAULT_CONFIG_PATH = TOOL_DIR / "config.example.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SIGNED_URL_MARKERS = (
    "x-amz-signature",
    "x-amz-credential",
    "key-pair-id",
    "signature=",
    "sig=",
    "token=",
    "expires=",
    "policy=",
)
REDACTION_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(cookie\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)\b(access_token|api_key|apikey|token|password|secret)\b(\s*[=:]\s*)([^\s&\"',}]+)"),
]


class ValidationError(Exception):
    """Erro de validação (exit code 1)."""


class PolicyError(Exception):
    """Violação de política (exit code 2)."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str) -> str:
    out = str(text)
    for pattern in REDACTION_PATTERNS:
        out = pattern.sub(lambda m: f"{m.group(1)}[REDACTED]", out)
    return out


def detect_signed_url(text: str) -> Optional[str]:
    lower = str(text).lower()
    for marker in SIGNED_URL_MARKERS:
        if marker in lower:
            return marker.strip("=")
    return None


def load_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"config não encontrada: {path}")
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("signed_url_persistence_allowed") is True:
        raise ValidationError("config inválida: signed_url_persistence_allowed = true é proibido.")
    return config


def validate_url(url: str, config: Dict[str, Any]) -> None:
    network = config.get("network") or {}
    if network.get("require_https", True) and not url.lower().startswith("https://"):
        raise ValidationError(f"URL recusada (exige HTTPS): {redact(url)}")
    authority = url.split("://", 1)[1].split("/", 1)[0] if "://" in url else url
    if "@" in authority and network.get("reject_userinfo_in_url", True):
        raise ValidationError("URL recusada: contém userinfo (user:pass@).")
    host = authority.split(":", 1)[0].lower()
    if network.get("reject_ip_literals", True) and IPV4_RE.match(host):
        raise ValidationError("URL recusada: IP literal.")
    allowed = [d.lower() for d in (network.get("allowed_domains") or [])]
    if not allowed:
        raise ValidationError("allowlist vazia — obrigatória.")
    if not (host in allowed or (network.get("allow_subdomains", True) and any(host.endswith("." + d) for d in allowed))):
        raise ValidationError(f"URL recusada: host '{host}' fora da allowlist.")
    marker = detect_signed_url(url)
    if marker:
        raise ValidationError(
            f"URL recusada: parâmetro assinado ('{marker}'). Re-resolva a URL pela fonte em vez de "
            "reutilizar link assinado (teste 8)."
        )


def secret_values(config: Dict[str, Any]) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for name, env_name in (config.get("secret_env_vars") or {}).items():
        value = os.environ.get(str(env_name), "").strip()
        if value:
            found[name] = value
    return found


def assert_no_secret_leak(text: str, secrets: Dict[str, str], where: str) -> None:
    for name, value in secrets.items():
        if value and value in str(text):
            raise ValidationError(
                f"vazamento de segredo '{name}' em {where} (teste 9: SecretsAreNotLogged)."
            )


def read_state(state_path: Path) -> Dict[str, Any]:
    if not state_path.is_file():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"estado de resume inválido ({state_path.name}): {exc}")


def compute_resume_plan(partial_path: Path, state: Dict[str, Any], expected_size: int = 0) -> Dict[str, Any]:
    """
    Calcula o plano de retomada a partir do arquivo parcial (fonte de verdade) e do estado.
    Retorna offset, bytes restantes e diagnóstico de consistência.
    """
    offset = partial_path.stat().st_size if partial_path.is_file() else 0
    state_offset = state.get("bytes_downloaded")
    inconsistent = state_offset is not None and int(state_offset) != offset
    remaining = None
    if expected_size and expected_size > 0:
        remaining = max(0, expected_size - offset)
    return {
        "partial_exists": partial_path.is_file(),
        "offset_bytes_on_disk": offset,
        "state_recorded_bytes": state_offset,
        "state_vs_disk_inconsistent": inconsistent,
        "expected_size_bytes": expected_size or None,
        "remaining_bytes": remaining,
        "completion_ratio": (
            round(offset / expected_size, 6) if expected_size and expected_size > 0 else None
        ),
        "completion_aggregation": (
            f"({offset}/{expected_size})" if expected_size and expected_size > 0 else None
        ),
        "previous_attempts": state.get("attempts"),
        "previous_status": state.get("status"),
        "range_header": f"bytes={offset}-" if offset > 0 else None,
    }


def backoff_delay(attempt: int, retry_cfg: Dict[str, Any]) -> float:
    initial = float(retry_cfg.get("backoff_initial_seconds", 2.0))
    factor = float(retry_cfg.get("backoff_factor", 2.0))
    ceiling = float(retry_cfg.get("backoff_max_seconds", 60.0))
    return min(ceiling, initial * (factor ** attempt))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def scan_resumable(raw_dir: Path, partial_suffix: str, state_suffix: str) -> List[Dict[str, Any]]:
    """Lista pares (.part, .state.json) em raw_demos, com o plano de retomada de cada um."""
    findings: List[Dict[str, Any]] = []
    if not raw_dir.is_dir():
        return findings
    for partial in sorted(raw_dir.glob(f"*{partial_suffix}")):
        state_path = partial.with_suffix(partial.suffix + state_suffix) if state_suffix.startswith(".") else Path(
            str(partial) + state_suffix
        )
        if not state_path.is_file():
            state_path = Path(str(partial).replace(partial_suffix, state_suffix))
        state = read_state(state_path) if state_path.is_file() else {}
        plan = compute_resume_plan(partial, state)
        findings.append(
            {
                "partial_repo_relative_path": str(partial.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
                if REPO_ROOT in partial.resolve().parents
                else str(partial),
                "state_repo_relative_path": (
                    str(state_path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
                    if ROOT_SAFE(state_path)
                    else str(state_path)
                ),
                "state_file_present": state_path.is_file(),
                **plan,
            }
        )
    return findings


def ROOT_SAFE(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def execute_resume(
    url: str,
    partial: Path,
    state_path: Path,
    config: Dict[str, Any],
    secrets: Dict[str, str],
    expected_sha256: str,
    logger,
) -> Dict[str, Any]:
    """Executa a retomada real via HTTP Range, com rate limit, backoff e verificação final."""
    download_cfg = config.get("download") or {}
    network_cfg = config.get("network") or {}
    retry_cfg = config.get("retry") or {}
    retry_limit = int(retry_cfg.get("retry_limit", 4))
    chunk_size = int(download_cfg.get("chunk_size_bytes", 262144))
    timeout = float(network_cfg.get("request_timeout_seconds", 30))
    rate = max(0.1, float((config.get("rate_limit") or {}).get("requests_per_second", 1.0)))

    offset = partial.stat().st_size if partial.is_file() else 0
    attempts = 0
    written = offset
    while attempts <= retry_limit:
        attempts += 1
        headers = {"User-Agent": str(network_cfg.get("user_agent", "CsBot-Acquisition/1.0"))}
        if offset > 0 and download_cfg.get("range_header_enabled", True):
            headers["Range"] = f"bytes={offset}-"
        assert_no_secret_leak(json.dumps(headers), secrets, "request_headers")
        if attempts > 1 or written == offset:
            time.sleep(1.0 / rate)
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                mode = "ab" if (offset > 0 and status == 206) else "wb"
                if offset > 0 and status == 200:
                    logger("servidor não suportou Range (HTTP 200): reiniciando do zero")
                    written = 0
                with open(partial, mode) as handle:
                    while True:
                        block = response.read(chunk_size)
                        if not block:
                            break
                        handle.write(block)
                        written += len(block)
            break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            if attempts > retry_limit:
                raise ValidationError(f"retomada falhou após {retry_limit} retries: {redact(str(exc))}")
            delay = backoff_delay(attempts, retry_cfg)
            logger(f"falha tentativa {attempts}/{retry_limit}: {redact(str(exc))}; backoff {delay:.1f}s")
            time.sleep(delay)

    final_sha = sha256_file(partial)
    if expected_sha256 and final_sha.lower() != expected_sha256.lower():
        quarantine_dir = REPO_ROOT / str((config.get("paths") or {}).get("quarantine", ""))
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        target = quarantine_dir / partial.name
        partial.replace(target)
        raise ValidationError(
            f"checksum divergente após retomada; arquivo movido para "
            f"{str(target.resolve().relative_to(REPO_ROOT)).replace(chr(92), '/')}."
        )

    final_target = partial.with_suffix("") if partial.suffix == (download_cfg.get("partial_suffix", ".part")) else partial
    partial.replace(final_target)
    if state_path.is_file():
        state_path.unlink()
    return {
        "attempts": attempts,
        "bytes_total": written,
        "final_sha256": final_sha,
        "final_repo_relative_path": (
            str(final_target.resolve().relative_to(REPO_ROOT)).replace("\\", "/") if ROOT_SAFE(final_target) else str(final_target)
        ),
        "state_file_removed": True,
    }


def run_self_test() -> int:
    results: List[Dict[str, Any]] = []
    failures: List[str] = []

    with tempfile.TemporaryDirectory(prefix="csbot_resume_selftest_") as tmp:
        root = Path(tmp)
        partial = root / "demo.part"
        state_path = root / "demo.state.json"

        # Caso 1: sem arquivo parcial nem estado -> offset 0.
        plan = compute_resume_plan(partial, {})
        ok = plan["offset_bytes_on_disk"] == 0 and plan["range_header"] is None
        results.append({"case": "no_partial_offset_zero", "ok": ok, **{k: plan[k] for k in ("offset_bytes_on_disk", "range_header")}})
        if not ok:
            failures.append("no_partial_offset_zero")

        # Caso 2: parcial de 100 bytes + estado coerente -> Range bytes=100-.
        partial.write_bytes(b"x" * 100)
        state_path.write_text(json.dumps({"bytes_downloaded": 100, "attempts": 2, "status": "IN_PROGRESS"}), encoding="utf-8")
        plan = compute_resume_plan(partial, read_state(state_path), expected_size=1000)
        ok = (
            plan["offset_bytes_on_disk"] == 100
            and plan["range_header"] == "bytes=100-"
            and plan["remaining_bytes"] == 900
            and plan["state_vs_disk_inconsistent"] is False
        )
        results.append({"case": "coherent_state_resume", "ok": ok, "range_header": plan["range_header"], "remaining_bytes": plan["remaining_bytes"]})
        if not ok:
            failures.append("coherent_state_resume")

        # Caso 3: estado diz 500 mas disco tem 100 -> inconsistência detectada, disco vence.
        state_path.write_text(json.dumps({"bytes_downloaded": 500}), encoding="utf-8")
        plan = compute_resume_plan(partial, read_state(state_path), expected_size=1000)
        ok = plan["state_vs_disk_inconsistent"] is True and plan["offset_bytes_on_disk"] == 100
        results.append({"case": "inconsistent_state_detected", "ok": ok, "state_vs_disk_inconsistent": plan["state_vs_disk_inconsistent"]})
        if not ok:
            failures.append("inconsistent_state_detected")

        # Caso 4: parcial maior que o esperado -> remaining 0 (não negativo).
        partial.write_bytes(b"x" * 1200)
        plan = compute_resume_plan(partial, {}, expected_size=1000)
        ok = plan["remaining_bytes"] == 0
        results.append({"case": "partial_larger_than_expected_clamped", "ok": ok, "remaining_bytes": plan["remaining_bytes"]})
        if not ok:
            failures.append("partial_larger_than_expected_clamped")

    passed = len(results) - len(failures)
    print(
        json.dumps(
            {
                "self_test": "resume_download.py",
                "generated_utc": utc_now(),
                "cases_total": len(results),
                "cases_passed": passed,
                "cases_failed": len(failures),
                "aggregation": f"({passed}/{len(results)})",
                "fixture_class": "TEST_FIXTURE_IN_TEMPDIR_NOT_REAL_DATA",
                "files_written_inside_repository": 0,
                "network_requests_executed": 0,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if failures:
        print("SELF-TEST FALHOU:\n- " + "\n- ".join(failures), file=sys.stderr)
        return EXIT_VALIDATION
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="resume_download.py",
        description=(
            "Retoma downloads interrompidos usando o arquivo .part como fonte de verdade, com Range, "
            "backoff, rate limit e checksum. A URL nunca é persistida: deve ser re-resolvida."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação (ou self-test falho) | 2 erro de uso/política.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    parser.add_argument("--partial", default="", help="Caminho do arquivo .part a retomar.")
    parser.add_argument("--url", default="", help="URL re-resolvida (sem parâmetros assinados).")
    parser.add_argument("--expected-sha256", default="", help="SHA-256 esperado do arquivo final (64 hex).")
    parser.add_argument("--expected-size", type=int, default=0, help="Tamanho esperado em bytes.")
    parser.add_argument("--scan", action="store_true", help="Lista pares .part/.state.json com o plano de retomada.")
    parser.add_argument("--self-test", action="store_true", help="Executa 4 casos de offset/estado em diretório temporário.")
    parser.add_argument("--out", default="", help="Grava o plano/relatório em JSON.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) calcula e imprime o plano.")
    mode.add_argument("--execute", action="store_true", help="Executa a retomada real (bloqueada nesta fase).")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    secrets = secret_values(config)
    download_cfg = config.get("download") or {}
    partial_suffix = str(download_cfg.get("partial_suffix", ".part"))
    state_suffix = str(download_cfg.get("state_suffix", ".state.json"))

    if args.self_test:
        return run_self_test()

    raw_dir = REPO_ROOT / str((config.get("paths") or {}).get("raw_demos", ""))

    if args.scan:
        findings = scan_resumable(raw_dir, partial_suffix, state_suffix)
        report = {
            "mode": "SCAN",
            "generated_utc": utc_now(),
            "raw_demos_scanned": str(raw_dir.resolve().relative_to(REPO_ROOT)).replace("\\", "/") if raw_dir.is_dir() else str(raw_dir),
            "resumable_found": len(findings),
            "resumable": findings,
            "network_requests_executed": 0,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if args.out:
            out_path = Path(args.out)
            if not out_path.is_absolute():
                out_path = REPO_ROOT / out_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"relatório gravado em: {out_path}")
        return EXIT_OK

    if not args.partial:
        print("ERRO de uso: informe --partial (ou use --scan / --self-test).", file=sys.stderr)
        return EXIT_USAGE

    partial = Path(args.partial)
    if not partial.is_absolute():
        partial = REPO_ROOT / partial
    if not partial.is_file():
        raise ValidationError(f"arquivo parcial ausente: {partial}")
    if not partial.name.endswith(partial_suffix):
        raise ValidationError(f"arquivo informado não tem sufixo de parcial '{partial_suffix}'.")

    state_path = Path(str(partial).replace(partial_suffix, state_suffix))
    state = read_state(state_path)
    plan = compute_resume_plan(partial, state, expected_size=args.expected_size)

    report: Dict[str, Any] = {
        "mode": "EXECUTE" if args.execute else "DRY_RUN",
        "generated_utc": utc_now(),
        "partial_repo_relative_path": str(partial.resolve().relative_to(REPO_ROOT)).replace("\\", "/") if ROOT_SAFE(partial) else str(partial),
        "state_file_present": state_path.is_file(),
        "resume_plan": plan,
        "url_persisted_in_state": bool(state.get("source_url") or state.get("url")),
        "signed_url_in_state": detect_signed_url(json.dumps(state, ensure_ascii=False)) if state else None,
        "network_requests_executed": 0,
    }
    if report["url_persisted_in_state"] or report["signed_url_in_state"]:
        raise ValidationError(
            "estado de resume contém URL persistida/assinada — proibido (teste 8). Apague o estado e "
            "re-resolva a URL pela fonte."
        )

    if not args.execute:
        report["notes"] = [
            "Dry-run: nenhuma conexão aberta, nenhum byte escrito.",
            "O offset é lido do arquivo .part; o campo do estado é apenas diagnóstico.",
        ]
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return EXIT_OK

    approved = os.environ.get("CSBOT_APPROVED_SOURCE_ID", "").strip()
    if not approved:
        raise PolicyError(
            "retomada real bloqueada: nenhuma fonte aprovada. Defina CSBOT_APPROVED_SOURCE_ID somente "
            "após autorização humana da fonte."
        )
    if not args.url:
        raise ValidationError("retomada real exige --url re-resolvida (a URL nunca é persistida).")
    validate_url(args.url, config)
    assert_no_secret_leak(args.url, secrets, "url")
    if args.expected_sha256 and not SHA256_RE.match(args.expected_sha256.lower()):
        raise ValidationError("--expected-sha256 deve ter 64 hex.")

    result = execute_resume(
        args.url,
        partial,
        state_path,
        config,
        secrets,
        args.expected_sha256,
        logger=lambda message: print(f"[resume_download] {redact(message)}"),
    )
    report.update(result)
    report["status"] = "RESUMED_AND_VERIFIED"
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except PolicyError as exc:
        print(f"POLÍTICA: {redact(str(exc))}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)
    except ValidationError as exc:
        print(f"ERRO de validação: {redact(str(exc))}", file=sys.stderr)
        raise SystemExit(EXIT_VALIDATION)
    except KeyboardInterrupt:
        raise SystemExit(EXIT_VALIDATION)
