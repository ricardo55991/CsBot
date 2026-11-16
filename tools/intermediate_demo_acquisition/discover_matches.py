#!/usr/bin/env python3
"""
discover_matches.py — Descoberta de partidas candidatas do domínio intermediário.

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §5 (Fonte A/B), §6, §9.

O que faz
---------
Monta o *plano de consulta* de partidas candidatas em `de_mirage` para os buckets de skill
marcados `INCLUDED_PILOT` no `domain_contract_v1.json` e, quando houver autorização explícita
(`--execute`) e fonte aprovada, executa as requisições contra a API oficial.

Modo padrão: `--dry-run` (seguro). Em dry-run NÃO há nenhuma abertura de socket, NÃO há
requisição HTTP e NÃO há gravação em `datasets/`. O script apenas valida a configuração,
valida a allowlist de domínio, monta o plano determinístico e imprime o resultado.

Garantias de segurança implementadas
-------------------------------------
- allowlist de domínio obrigatória (exata ou subdomínio), somente HTTPS, sem IP literal,
  sem `user:pass@` na URL;
- detecção e recusa de URL assinada (token/signature/expires/Policy) em qualquer payload
  que se pretenda persistir;
- segredos lidos exclusivamente de variáveis de ambiente; nunca de config, nunca impressos;
- redaction de credenciais em todo texto emitido (stdout e audit log);
- audit log append-only (ou stdout quando `audit_log.path` está vazio);
- política de limites respeitada: rate limit e retry limit vêm da config e são proibitivos
  de contornar por flag.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação · 2 = erro de uso
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
DEFAULT_CONFIG_PATH = TOOL_DIR / "config.example.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

REDACTION_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(x-api-key\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(cookie\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(steamloginsecure\s*=\s*)([^\s;\"']+)"),
    re.compile(r"(?i)(steamguard\s*=\s*)([^\s;\"']+)"),
    re.compile(r"(?i)\b(access_token|refresh_token|id_token|api_key|apikey|token|password|passwd|secret)\b(\s*[=:]\s*)([^\s&\"',}]+)"),
    re.compile(r"(?i)(\bBearer\s+)([A-Za-z0-9\-._~+/]+=*)"),
]

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
    "awsaccesskeyid",
    "x-goog-signature",
)

IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


class ValidationError(Exception):
    """Erro de validação de configuração, política ou payload (exit code 1)."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str) -> str:
    """Mascara credenciais em texto livre (stdout, logs, mensagens de erro)."""
    out = str(text)
    for pattern in REDACTION_PATTERNS:
        if pattern.groups >= 3:
            out = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", out)
        else:
            out = pattern.sub(lambda m: f"{m.group(1)}[REDACTED]", out)
    return out


def detect_signed_url(text: str) -> Optional[str]:
    """Retorna o marcador encontrado se o texto contiver URL/parâmetro assinado."""
    lower = str(text).lower()
    for marker in SIGNED_URL_MARKERS:
        if marker in lower:
            return marker.strip("=")
    return None


def assert_no_signed_url(value: Any, where: str = "$") -> None:
    """Percorre recursivamente um payload e falha se houver URL assinada a persistir."""
    if isinstance(value, str):
        marker = detect_signed_url(value)
        if marker:
            raise ValidationError(
                f"URL assinada detectada em {where} (marcador '{marker}'). "
                "Persistir URL assinada é proibido (teste 8: SignedUrlsAreNotPersisted)."
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_no_signed_url(item, f"{where}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_no_signed_url(item, f"{where}[{index}]")


def load_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"config não encontrada: {path}")
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValidationError("config deve ser um objeto JSON.")
    if config.get("signed_url_persistence_allowed") is True:
        raise ValidationError(
            "config inválida: 'signed_url_persistence_allowed' = true. "
            "Persistir URL assinada é proibido; o valor deve ser false."
        )
    for key, value in (config.get("credentials") or {}).items():
        if str(value).strip():
            raise ValidationError(
                f"config inválida: credencial '{key}' não vazia. Segredos devem vir exclusivamente "
                "de variáveis de ambiente (secret_source = ENV)."
            )
    assert_no_signed_url(config, "config")
    return config


def get_secret(config: Dict[str, Any], name: str) -> Optional[str]:
    """Lê segredo exclusivamente do ambiente, conforme config.secret_env_vars[name]."""
    env_name = (config.get("secret_env_vars") or {}).get(name)
    if not env_name:
        return None
    value = os.environ.get(env_name, "").strip()
    return value or None


def validate_url(url: str, config: Dict[str, Any]) -> None:
    """Valida esquema, host contra allowlist, ausência de userinfo e de IP literal."""
    network = config.get("network") or {}
    if network.get("require_https", True) and not url.lower().startswith("https://"):
        raise ValidationError(f"URL recusada (exige HTTPS): {redact(url)}")
    remainder = url.split("://", 1)[1] if "://" in url else url
    authority = remainder.split("/", 1)[0]
    if "@" in authority and network.get("reject_userinfo_in_url", True):
        raise ValidationError("URL recusada: contém userinfo (user:pass@) — credencial em URL é proibida.")
    host = authority.split(":", 1)[0].lower()
    if network.get("reject_ip_literals", True) and IPV4_RE.match(host):
        raise ValidationError(f"URL recusada: IP literal ('{host}') não é permitido.")
    allowed = [d.lower() for d in (network.get("allowed_domains") or [])]
    if not allowed:
        raise ValidationError("config inválida: 'network.allowed_domains' vazio — allowlist é obrigatória.")
    allow_sub = network.get("allow_subdomains", True)
    host_ok = host in allowed or any(allow_sub and host.endswith("." + d) for d in allowed)
    if not host_ok:
        raise ValidationError(
            f"URL recusada: host '{host}' fora da allowlist ({', '.join(allowed)})."
        )
    marker = detect_signed_url(url)
    if marker:
        raise ValidationError(
            f"URL recusada: contém parâmetro assinado ('{marker}'). Nenhuma URL assinada pode ser "
            "usada, impressa ou persistida (teste 8)."
        )


class RateLimiter:
    """Token bucket simples: garante respeitar requests_per_second e burst da config."""

    def __init__(self, requests_per_second: float, burst: int) -> None:
        self.rate = max(0.1, float(requests_per_second))
        self.capacity = max(1, int(burst))
        self._tokens = float(self.capacity)
        self._last = time.monotonic()

    def acquire(self, dry_run: bool) -> float:
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return 0.0
        wait = (1.0 - self._tokens) / self.rate
        if not dry_run:
            time.sleep(wait)
        self._tokens = 0.0
        return wait


def emit_audit(config: Dict[str, Any], event: str, payload: Dict[str, Any]) -> None:
    """Registra evento de auditoria append-only, com redaction obrigatória."""
    audit_cfg = config.get("audit_log") or {}
    if not audit_cfg.get("enabled", True):
        return
    record = {"timestamp_utc": utc_now(), "script": "discover_matches.py", "event": event}
    record.update(payload)
    assert_no_signed_url(record, "audit_record")
    line = redact(json.dumps(record, ensure_ascii=False, sort_keys=True))
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


def build_query_plan(config: Dict[str, Any], contract: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """Constrói o plano determinístico de descoberta (sem rede)."""
    map_name = config.get("map_name", "de_mirage")
    if map_name != "de_mirage":
        raise ValidationError(f"map_name deve ser 'de_mirage'; recebido '{map_name}'.")

    included = [
        name
        for name, sub in (contract.get("subdomains") or {}).items()
        if sub.get("inclusion_policy") == "INCLUDED_PILOT"
    ]
    if not included:
        raise ValidationError("contrato sem nenhum subdomínio INCLUDED_PILOT.")

    pending = [
        name
        for name, sub in (contract.get("subdomains") or {}).items()
        if sub.get("inclusion_policy") == "NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT"
    ]

    # Endpoint oficial da FACEIT Data API (somente leitura de metadado; NÃO autoriza download).
    endpoints = [
        {
            "source": "FACEIT_DATA_API",
            "url_template": "https://open.faceit.com/data/v4/matches/{match_id}",
            "requires_secret": "faceit_data_api_key",
            "purpose": "metadado da partida (mapa, data, região, 10 jogadores)",
            "executed": False,
        },
        {
            "source": "FACEIT_DATA_API",
            "url_template": "https://open.faceit.com/data/v4/players/{player_id}/history",
            "requires_secret": "faceit_data_api_key",
            "purpose": "histórico de Elo/level para reconstruir skill na data da partida",
            "executed": False,
        },
    ]
    for endpoint in endpoints:
        validate_url(endpoint["url_template"].replace("{match_id}", "00000000-0000-0000-0000-000000000000").replace("{player_id}", "0"), config)

    targets = {
        "FACEIT_LEVEL_5_6": (contract.get("faceit_buckets") or {}).get("FACEIT_LEVEL_5_6", {}).get(
            "pilot_target_demos", {}
        ),
        "FACEIT_LEVEL_7_8": (contract.get("faceit_buckets") or {}).get("FACEIT_LEVEL_7_8", {}).get(
            "pilot_target_demos", {}
        ),
    }

    plan = {
        "mode": "DRY_RUN" if not args.execute else "EXECUTE",
        "generated_utc": utc_now(),
        "map_name": map_name,
        "buckets_included_pilot": included,
        "buckets_pending_distribution_audit": pending,
        "pilot_target_demos": targets,
        "region_filter": args.region,
        "date_from": args.date_from,
        "date_to": args.date_to,
        "endpoints": endpoints,
        "max_candidates_requested": args.max_candidates,
        "network_requests_planned": 0 if not args.execute else args.max_candidates * len(endpoints),
        "network_requests_executed": 0,
        "network_disabled_in_dry_run": True,
        "signed_urls_persisted": 0,
        "secrets_read": [],
        "notes": [
            "A FACEIT Data API comum NÃO autoriza download de demo; descoberta de metadado não implica acesso ao .dem.",
            "Nenhuma requisição é executada em --dry-run.",
            "Nenhum rank é convertido entre sistemas: cada candidato preserva o rank_system de origem.",
        ],
    }
    assert_no_signed_url(plan, "plan")
    return plan


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="discover_matches.py",
        description=(
            "Descobre partidas candidatas de de_mirage nos buckets INCLUDED_PILOT. "
            "Modo padrão: --dry-run (nenhuma requisição de rede)."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação | 2 erro de uso.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) valida e monta o plano; nenhuma rede.")
    mode.add_argument("--execute", action="store_true", help="Executa requisições reais. Exige fonte aprovada e segredo em ENV.")
    parser.add_argument("--region", default="EU", help="Região alvo (default: EU).")
    parser.add_argument("--date-from", default="2025-01-01", help="Data mínima da partida (YYYY-MM-DD).")
    parser.add_argument("--date-to", default="2025-12-31", help="Data máxima da partida (YYYY-MM-DD).")
    parser.add_argument("--max-candidates", type=int, default=50, help="Máximo de candidatos a listar (default: 50, nunca acima do piloto).")
    parser.add_argument("--out", default="", help="Caminho opcional para gravar o plano em JSON.")
    args = parser.parse_args(argv)

    if args.max_candidates < 1 or args.max_candidates > 50:
        print("ERRO de uso: --max-candidates deve estar entre 1 e 50 (o piloto não escala acima de 50 demos).", file=sys.stderr)
        return EXIT_USAGE

    config = load_config(Path(args.config))
    contract_path = REPO_ROOT / str(config.get("domain_contract_path") or "datasets/mirage_domains/domain_contract_v1.json")
    if not contract_path.is_file():
        raise ValidationError(f"contrato de domínios ausente: {contract_path}")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    plan = build_query_plan(config, contract, args)

    limiter = RateLimiter(
        (config.get("rate_limit") or {}).get("requests_per_second", 1.0),
        (config.get("rate_limit") or {}).get("burst", 3),
    )
    plan["rate_limit"] = {
        "requests_per_second": limiter.rate,
        "burst": limiter.capacity,
        "retry_limit": (config.get("retry") or {}).get("retry_limit", 4),
        "enforced": True,
    }

    if args.execute:
        # Caminho real: exige segredo em ambiente e fonte aprovada por humano.
        secret = get_secret(config, "faceit_data_api_key")
        if secret is None:
            raise ValidationError(
                "modo --execute exige o segredo 'faceit_data_api_key' em variável de ambiente "
                f"({(config.get('secret_env_vars') or {}).get('faceit_data_api_key')}). Nada foi executado."
            )
        plan["secrets_read"] = ["faceit_data_api_key"]
        # A execução real de rede NÃO é realizada nesta fase (proibida pelo dispatch e pela §8).
        raise ValidationError(
            "execução real de rede desabilitada nesta fase: a fonte oficial ainda não está aprovada "
            "por autorização humana. Use --dry-run. Veredito esperado da fase: "
            "INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING."
        )

    waited = limiter.acquire(dry_run=True)
    plan["rate_limit"]["simulated_wait_seconds"] = round(waited, 3)

    emit_audit(
        config,
        "DISCOVERY_PLAN_BUILT",
        {
            "mode": plan["mode"],
            "buckets": plan["buckets_included_pilot"],
            "network_requests_executed": 0,
            "map_name": plan["map_name"],
        },
    )

    print(json.dumps(plan, indent=2, ensure_ascii=False))

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        assert_no_signed_url(plan, "plan_out")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"plano gravado em: {out_path}")
    return EXIT_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except ValidationError as exc:
        print(f"ERRO de validação: {redact(str(exc))}", file=sys.stderr)
        raise SystemExit(EXIT_VALIDATION)
    except KeyboardInterrupt:
        print("interrompido pelo usuário", file=sys.stderr)
        raise SystemExit(EXIT_VALIDATION)
