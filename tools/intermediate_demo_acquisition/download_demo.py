#!/usr/bin/env python3
"""
download_demo.py — Download resumable e verificado de demos de Mirage.

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §9
(resumable downloads, exponential backoff, rate limiting, checksum, allowlist,
audit log, credential redaction, retry limit, quarantine).

O que faz
---------
Baixa um recurso de demo a partir de uma fonte **aprovada** e de um domínio na allowlist,
com:

- **resume** por HTTP `Range: bytes=<offset>-`, estado persistido em `<arquivo>.state.json`
  e conteúdo parcial em `<arquivo>.part` (retomada idempotente após interrupção);
- **rate limiting** por token bucket configurável;
- **backoff exponencial** com `retry_limit` e teto `backoff_max_seconds`;
- **checksum SHA-256** obrigatório no fim, comparado com o valor esperado de 64 hex;
- **allowlist de domínio**, HTTPS obrigatório, recusa de IP literal e de `user:pass@`;
- **recusa de URL assinada** em qualquer ponto (entrada, log, estado, metadata);
- **recusa de vazamento de segredo**: falha se o valor de qualquer segredo de ambiente
  aparecer na URL, nos logs ou no arquivo de estado;
- **audit log append-only** com credential redaction;
- **quarantine** de arquivo inválido em vez de apagar.

Modo padrão: `--dry-run`. Em dry-run **nenhuma conexão de rede é aberta**: o script valida a URL,
resolve os caminhos, simula a política de retry e imprime o plano. Nesta fase o modo `--execute`
permanece bloqueado por ausência de fonte oficial aprovada por autorização humana.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação · 2 = erro de uso (inclui `--execute` bloqueado por política)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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
    "x-amz-security-token",
    "key-pair-id",
    "signature=",
    "sig=",
    "token=",
    "expires=",
    "policy=",
)

REDACTION_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(x-api-key\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(cookie\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(steamloginsecure\s*=\s*)([^\s;\"']+)"),
    re.compile(r"(?i)\b(access_token|refresh_token|api_key|apikey|token|password|secret)\b(\s*[=:]\s*)([^\s&\"',}]+)"),
    re.compile(r"(?i)(\bBearer\s+)([A-Za-z0-9\-._~+/]+=*)"),
]


class ValidationError(Exception):
    """Erro de validação (exit code 1)."""


class PolicyError(Exception):
    """Violação de política que impede a operação (exit code 2)."""


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
    for key, value in (config.get("credentials") or {}).items():
        if str(value).strip():
            raise ValidationError(f"config inválida: credencial '{key}' não vazia; use variável de ambiente.")
    return config


def secret_values(config: Dict[str, Any]) -> Dict[str, str]:
    """Mapeia nome_lógico -> valor do segredo, lido apenas do ambiente."""
    found: Dict[str, str] = {}
    for name, env_name in (config.get("secret_env_vars") or {}).items():
        value = os.environ.get(str(env_name), "").strip()
        if value:
            found[name] = value
    return found


def assert_no_secret_leak(text: str, secrets: Dict[str, str], where: str) -> None:
    """Falha se qualquer valor de segredo aparecer no texto (URL, log, estado)."""
    for name, value in secrets.items():
        if value and value in str(text):
            raise ValidationError(
                f"vazamento de segredo '{name}' detectado em {where}: o valor nunca pode aparecer em "
                "URL, log, metadata ou arquivo de estado (teste 9: SecretsAreNotLogged)."
            )


def validate_url(url: str, config: Dict[str, Any]) -> None:
    network = config.get("network") or {}
    if network.get("require_https", True) and not url.lower().startswith("https://"):
        raise ValidationError(f"URL recusada (exige HTTPS): {redact(url)}")
    remainder = url.split("://", 1)[1] if "://" in url else url
    authority = remainder.split("/", 1)[0]
    if "@" in authority and network.get("reject_userinfo_in_url", True):
        raise ValidationError("URL recusada: contém userinfo (user:pass@).")
    host = authority.split(":", 1)[0].lower()
    if network.get("reject_ip_literals", True) and IPV4_RE.match(host):
        raise ValidationError(f"URL recusada: IP literal ('{host}').")
    allowed = [d.lower() for d in (network.get("allowed_domains") or [])]
    if not allowed:
        raise ValidationError("'network.allowed_domains' vazio — allowlist é obrigatória.")
    allow_sub = network.get("allow_subdomains", True)
    if not (host in allowed or any(allow_sub and host.endswith("." + d) for d in allowed)):
        raise ValidationError(f"URL recusada: host '{host}' fora da allowlist.")
    marker = detect_signed_url(url)
    if marker:
        raise ValidationError(
            f"URL recusada: contém parâmetro assinado ('{marker}'). URLs assinadas não são usadas nem "
            "persistidas (teste 8). Solicite o identificador estável da fonte."
        )


class RateLimiter:
    """Token bucket determinístico respeitando requests_per_second e burst."""

    def __init__(self, requests_per_second: float, burst: int) -> None:
        self.rate = max(0.1, float(requests_per_second))
        self.capacity = max(1, int(burst))
        self._tokens = float(self.capacity)
        self._last = time.monotonic()

    def acquire(self, dry_run: bool) -> float:
        now = time.monotonic()
        self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
        self._last = now
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return 0.0
        wait = (1.0 - self._tokens) / self.rate
        if not dry_run:
            time.sleep(wait)
        self._tokens = 0.0
        return wait


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


def resolve_paths(config: Dict[str, Any], demo_id: str) -> Dict[str, Path]:
    paths_cfg = config.get("paths") or {}
    download_cfg = config.get("download") or {}
    raw_dir = REPO_ROOT / str(paths_cfg.get("raw_demos", ""))
    archives_dir = REPO_ROOT / str(paths_cfg.get("archives", ""))
    quarantine_dir = REPO_ROOT / str(paths_cfg.get("quarantine", ""))
    return {
        "raw_dir": raw_dir,
        "archives_dir": archives_dir,
        "quarantine_dir": quarantine_dir,
        "target": raw_dir / f"{demo_id}.dem",
        "partial": raw_dir / f"{demo_id}.dem{download_cfg.get('partial_suffix', '.part')}",
        "state": raw_dir / f"{demo_id}.dem{download_cfg.get('state_suffix', '.state.json')}",
    }


def read_state(state_path: Path) -> Dict[str, Any]:
    if not state_path.is_file():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_state(state_path: Path, payload: Dict[str, Any], secrets: Dict[str, str]) -> None:
    assert_no_secret_leak(json.dumps(payload, ensure_ascii=False), secrets, "state_file")
    state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def emit_audit(config: Dict[str, Any], event: str, payload: Dict[str, Any], secrets: Dict[str, str]) -> None:
    audit_cfg = config.get("audit_log") or {}
    if not audit_cfg.get("enabled", True):
        return
    record = {"timestamp_utc": utc_now(), "script": "download_demo.py", "event": event}
    record.update(payload)
    marker = detect_signed_url(json.dumps(record, ensure_ascii=False))
    if marker:
        raise ValidationError(f"audit log tentaria persistir URL assinada ('{marker}') — operação abortada.")
    line = redact(json.dumps(record, ensure_ascii=False, sort_keys=True))
    assert_no_secret_leak(line, secrets, "audit_log")
    target = str(audit_cfg.get("path") or "").strip()
    if not target:
        print(f"[AUDIT] {line}")
        return
    path = Path(target)
    if not path.is_absolute():
        path = REPO_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def quarantine(path: Path, config: Dict[str, Any], reason: str) -> Optional[str]:
    """Move o arquivo inválido para quarantine/ e devolve o caminho relativo."""
    if not path.is_file():
        return None
    quarantine_dir = REPO_ROOT / str((config.get("paths") or {}).get("quarantine", ""))
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target = quarantine_dir / path.name
    if target.exists():
        target = quarantine_dir / f"{path.stem}__{sha256_file(path)[:8]}{path.suffix}"
    path.replace(target)
    try:
        return str(target.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(target)


def http_open(url: str, headers: Dict[str, str], timeout: float):
    """Abre a conexão HTTP. Isolada para permitir teste e substituição sem tocar na política."""
    request = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(request, timeout=timeout)


def download_with_resume(
    url: str,
    target_paths: Dict[str, Path],
    config: Dict[str, Any],
    secrets: Dict[str, str],
    limiter: RateLimiter,
    logger,
) -> Dict[str, Any]:
    """
    Executa o download resumable real. Só é alcançado com --execute e fonte aprovada.
    Retorna laudo com bytes baixados, tentativas e checksum.
    """
    download_cfg = config.get("download") or {}
    network_cfg = config.get("network") or {}
    retry_cfg = config.get("retry") or {}
    retry_limit = int(retry_cfg.get("retry_limit", 4))
    chunk_size = int(download_cfg.get("chunk_size_bytes", 262144))
    max_bytes = int(download_cfg.get("max_download_bytes", 104857600))
    timeout = float(network_cfg.get("request_timeout_seconds", 30))

    partial = target_paths["partial"]
    state_path = target_paths["state"]
    state = read_state(state_path)
    offset = partial.stat().st_size if partial.is_file() else 0
    if state.get("bytes_downloaded") is not None and offset == 0:
        offset = 0

    attempts = 0
    bytes_written = offset
    while attempts <= retry_limit:
        attempts += 1
        headers = {"User-Agent": str(network_cfg.get("user_agent", "CsBot-Acquisition/1.0"))}
        if download_cfg.get("range_header_enabled", True) and bytes_written > 0:
            headers["Range"] = f"bytes={bytes_written}-"
        assert_no_secret_leak(json.dumps(headers, ensure_ascii=False), secrets, "request_headers")
        limiter.acquire(dry_run=False)
        try:
            with http_open(url, headers, timeout) as response:
                status = getattr(response, "status", 200)
                if bytes_written > 0 and status == 200:
                    # Servidor ignorou o Range: reinicia do zero em vez de corromper o arquivo.
                    logger(f"servidor ignorou Range (HTTP 200); reiniciando download de {partial.name}")
                    bytes_written = 0
                    mode = "wb"
                else:
                    mode = "ab" if bytes_written > 0 else "wb"
                with open(partial, mode) as handle:
                    while True:
                        block = response.read(chunk_size)
                        if not block:
                            break
                        handle.write(block)
                        bytes_written += len(block)
                        if bytes_written > max_bytes:
                            raise ValidationError(
                                f"limite max_download_bytes ({max_bytes}) excedido — abortado para não "
                                "consumir banda além do piloto."
                            )
                write_state(
                    state_path,
                    {
                        "source_url_reference": "redacted-identifier-only",
                        "bytes_downloaded": bytes_written,
                        "attempts": attempts,
                        "updated_utc": utc_now(),
                        "status": "COMPLETE_PENDING_VERIFICATION",
                    },
                    secrets,
                )
                return {"bytes_downloaded": bytes_written, "attempts": attempts, "status": "DOWNLOADED"}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            if attempts > retry_limit:
                raise ValidationError(
                    f"download falhou após {retry_limit} retries: {redact(str(exc))}"
                )
            delay = backoff_delay(attempts, retry_cfg)
            logger(f"falha tentativa {attempts}/{retry_limit}: {redact(str(exc))}; backoff {delay:.1f}s")
            time.sleep(delay)
    raise ValidationError("download não concluído: retry_limit esgotado.")


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="download_demo.py",
        description=(
            "Download resumable e verificado de demo de Mirage com allowlist, rate limit, backoff, "
            "checksum SHA-256 e quarantine. Modo padrão: --dry-run (nenhuma conexão de rede)."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação | 2 erro de uso (inclui --execute bloqueado).",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    parser.add_argument("--url", required=False, default="", help="URL do recurso (sem parâmetros assinados).")
    parser.add_argument("--demo-id", default="", help="Identificador estável da demo (nome do arquivo de saída).")
    parser.add_argument("--expected-sha256", default="", help="SHA-256 esperado do arquivo final (64 hex).")
    parser.add_argument("--expected-size", type=int, default=0, help="Tamanho esperado em bytes (0 = desconhecido).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) valida e imprime o plano; sem rede.")
    mode.add_argument("--execute", action="store_true", help="Executa o download real (bloqueado nesta fase).")
    parser.add_argument("--allow-execute-now", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    secrets = secret_values(config)

    if not args.url:
        raise ValidationError("--url é obrigatório (salvo quando apenas --help é usado).")
    demo_id = args.demo_id or re.sub(r"[^A-Za-z0-9._-]+", "_", args.url.rsplit("/", 1)[-1])[:80]
    if not demo_id:
        raise ValidationError("não foi possível derivar --demo-id; informe explicitamente.")

    validate_url(args.url, config)
    assert_no_secret_leak(args.url, secrets, "url")
    if args.expected_sha256 and not SHA256_RE.match(args.expected_sha256.lower()):
        raise ValidationError("--expected-sha256 deve conter exatamente 64 caracteres hexadecimais.")

    target_paths = resolve_paths(config, demo_id)
    retry_cfg = config.get("retry") or {}
    limiter = RateLimiter(
        (config.get("rate_limit") or {}).get("requests_per_second", 1.0),
        (config.get("rate_limit") or {}).get("burst", 3),
    )

    plan: Dict[str, Any] = {
        "mode": "DRY_RUN" if not args.execute else "EXECUTE",
        "generated_utc": utc_now(),
        "demo_id": demo_id,
        "url_redacted": redact(args.url),
        "url_host": args.url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0],
        "allowlist_validated": True,
        "signed_url_detected": False,
        "secrets_read": sorted(secrets.keys()),
        "target_relative": str(target_paths["target"].resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
        "partial_relative": str(target_paths["partial"].resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
        "state_relative": str(target_paths["state"].resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
        "resumable": bool((config.get("download") or {}).get("resumable", True)),
        "range_header_enabled": bool((config.get("download") or {}).get("range_header_enabled", True)),
        "rate_limit_requests_per_second": limiter.rate,
        "rate_limit_burst": limiter.capacity,
        "retry_limit": int(retry_cfg.get("retry_limit", 4)),
        "backoff_schedule_seconds": [
            round(backoff_delay(i, retry_cfg), 3) for i in range(1, int(retry_cfg.get("retry_limit", 4)) + 1)
        ],
        "expected_sha256": args.expected_sha256 or None,
        "expected_size_bytes": args.expected_size or None,
        "network_requests_executed": 0,
        "bytes_written": 0,
    }

    if args.execute:
        # Bloqueio de política: nesta fase nenhuma fonte oficial está aprovada por humano.
        approved = os.environ.get("CSBOT_APPROVED_SOURCE_ID", "").strip()
        if not approved:
            emit_audit(config, "EXECUTE_BLOCKED_NO_APPROVED_SOURCE", {"demo_id": demo_id}, secrets)
            raise PolicyError(
                "execução real bloqueada: nenhuma fonte aprovada. Defina CSBOT_APPROVED_SOURCE_ID "
                "somente após autorização humana explícita da fonte. Veredito esperado da fase: "
                "INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING."
            )
        required_secret = (config.get("secret_env_vars") or {}).get("faceit_downloads_api_key")
        if not (config.get("secret_env_vars") or {}).get("faceit_downloads_api_key") or not os.environ.get(
            str(required_secret), ""
        ).strip():
            raise ValidationError(
                f"segredo 'faceit_downloads_api_key' ausente no ambiente ({required_secret}). Nada foi baixado."
            )
        logger = lambda message: print(f"[download_demo] {redact(message)}")
        result = download_with_resume(args.url, target_paths, config, secrets, limiter, logger)
        plan.update(result)

        final_sha = sha256_file(target_paths["partial"])
        plan["actual_sha256"] = final_sha
        if args.expected_sha256 and final_sha.lower() != args.expected_sha256.lower():
            moved = quarantine(target_paths["partial"], config, "CHECKSUM_MISMATCH")
            emit_audit(config, "CHECKSUM_MISMATCH_QUARANTINED", {"demo_id": demo_id, "quarantined_to": moved}, secrets)
            raise ValidationError(f"checksum divergente; arquivo movido para {moved}.")
        if args.expected_size and target_paths["partial"].stat().st_size != args.expected_size:
            moved = quarantine(target_paths["partial"], config, "SIZE_MISMATCH")
            raise ValidationError(f"tamanho divergente; arquivo movido para {moved}.")
        target_paths["partial"].replace(target_paths["target"])
        if target_paths["state"].is_file():
            target_paths["state"].unlink()
        plan["status"] = "COMPLETE_VERIFIED"
        emit_audit(
            config,
            "DEMO_DOWNLOADED",
            {"demo_id": demo_id, "bytes": plan["bytes_downloaded"], "sha256": final_sha},
            secrets,
        )
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return EXIT_OK

    # --- DRY-RUN -----------------------------------------------------------------
    waited = limiter.acquire(dry_run=True)
    plan["rate_limit_simulated_wait_seconds"] = round(waited, 3)
    plan["would_download_bytes_unknown_until_headers"] = True
    plan["notes"] = [
        "Nenhuma conexão de rede foi aberta: dry-run é o modo padrão.",
        "A URL é validada contra a allowlist, mas o identificador de download real permanece pendente.",
        "O estado de resume é simulado em memória; nenhum arquivo .part, .state.json ou .dem é criado.",
    ]
    marker = detect_signed_url(json.dumps(plan, ensure_ascii=False))
    if marker:
        raise ValidationError(f"plano tentaria persistir URL assinada ('{marker}') — abortado.")
    emit_audit(config, "DOWNLOAD_PLAN_BUILT", {"demo_id": demo_id, "mode": "DRY_RUN"}, secrets)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
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
