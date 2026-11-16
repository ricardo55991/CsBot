#!/usr/bin/env python3
"""
fetch_match_metadata.py — Coleta e normalização do metadado de habilidade por partida.

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §4 (17 campos), §5 (Fonte A/B/D), §9.

O que faz
---------
Transforma o metadado bruto de uma fonte aprovada no registro canônico de 17 campos exigido por
`datasets/mirage_domains/domain_contract_v1.json` (seção `mandatory_fields`) e recusa qualquer
registro que tente:

  - converter rank entre sistemas (Competitive ⇄ Premier ⇄ FACEIT level ⇄ FACEIT Elo);
  - promover domínio `UNKNOWN` para `INTERMEDIATE_COMPETITIVE`;
  - preencher bucket de Premier Rating enquanto a política for
    `NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT`;
  - persistir URL assinada, token, cookie ou SteamID64 não pseudonimizado em saída publicada.

Modo padrão: `--dry-run`. Sem `--candidates`, o script NÃO inventa dado algum: ele apenas deriva do
contrato o *esqueleto de metadado* (nomes, tipos, obrigatoriedade) — que é esquema, não observação.
Com `--candidates`, processa apenas o arquivo informado, sem rede.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação · 2 = erro de uso
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
DEFAULT_CONFIG_PATH = TOOL_DIR / "config.example.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

MANDATORY_FIELDS_FALLBACK = [
    "domain_id",
    "platform",
    "rank_system",
    "skill_level",
    "elo_or_rating",
    "rank_at_collection_time",
    "rank_at_match_time_if_available",
    "map_specific_rank",
    "map_name",
    "match_date",
    "region",
    "source",
    "source_license",
    "acquisition_method",
    "consent_type",
    "metadata_confidence",
    "exclusion_reason",
]

FACEIT_SYSTEMS = {"FACEIT_LEVEL", "FACEIT_ELO"}
VALVE_COMPETITIVE_SYSTEMS = {"VALVE_COMPETITIVE_MAP_RANK"}
VALVE_PREMIER_SYSTEMS = {"VALVE_PREMIER_RATING"}

# Campos derivados que NUNCA podem coexistir com um sistema de origem diferente.
CONVERSION_TRAP_FIELDS = {
    "FACEIT_LEVEL": ["valve_competitive_rank", "premier_rating", "converted_valve_rank"],
    "FACEIT_ELO": ["valve_competitive_rank", "premier_rating", "converted_valve_rank"],
    "VALVE_COMPETITIVE_MAP_RANK": ["faceit_level", "faceit_elo", "converted_faceit_level"],
    "VALVE_PREMIER_RATING": ["faceit_level", "faceit_elo", "valve_competitive_rank", "converted_competitive_rank"],
}

REDACTION_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(x-api-key\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(cookie\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(steamloginsecure\s*=\s*)([^\s;\"']+)"),
    re.compile(r"(?i)\b(access_token|refresh_token|api_key|apikey|token|password|secret)\b(\s*[=:]\s*)([^\s&\"',}]+)"),
]

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

STEAMID64_RE = re.compile(r"\b7656119\d{10}\b")


class ValidationError(Exception):
    """Erro de validação (exit code 1)."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str) -> str:
    out = str(text)
    for pattern in REDACTION_PATTERNS:
        out = pattern.sub(lambda m: f"{m.group(1)}[REDACTED]", out)
    return out


def detect_signed_url(value: str) -> Optional[str]:
    lower = str(value).lower()
    for marker in SIGNED_URL_MARKERS:
        if marker in lower:
            return marker.strip("=")
    return None


def assert_no_signed_url(value: Any, where: str = "$") -> None:
    if isinstance(value, str):
        marker = detect_signed_url(value)
        if marker:
            raise ValidationError(
                f"URL assinada detectada em {where} (marcador '{marker}'): persistir é proibido (teste 8)."
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_no_signed_url(item, f"{where}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_no_signed_url(item, f"{where}[{index}]")


def pseudonymize_steamid(steamid64: str, salt: Optional[str]) -> str:
    """Pseudonimiza SteamID64 como PID_<16 hex>. Sem salt, recusa (nunca publica em claro)."""
    if not salt:
        raise ValidationError(
            "salt de pseudonimização ausente: defina a variável de ambiente indicada em "
            "config.secret_env_vars.corpus_pseudonym_salt. SteamID64 nunca é publicado em claro."
        )
    digest = hashlib.sha256((salt + str(steamid64)).encode("utf-8")).hexdigest()
    return "PID_" + digest[:16]


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


def load_contract(config: Dict[str, Any]) -> Dict[str, Any]:
    path = REPO_ROOT / str(config.get("domain_contract_path") or "datasets/mirage_domains/domain_contract_v1.json")
    if not path.is_file():
        raise ValidationError(f"contrato de domínios ausente: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def metadata_skeleton(contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Deriva o esqueleto dos campos do contrato (esquema, não observação de dado)."""
    fields = contract.get("mandatory_fields") or []
    if not fields:
        return [{"field": name, "source": "fallback_list"} for name in MANDATORY_FIELDS_FALLBACK]
    skeleton: List[Dict[str, Any]] = []
    for spec in fields:
        skeleton.append(
            {
                "field": spec.get("field"),
                "type": spec.get("type"),
                "required": spec.get("required"),
                "null_allowed": spec.get("null_allowed"),
                "allowed_values": spec.get("allowed_values"),
                "purpose": spec.get("purpose"),
            }
        )
    return skeleton


def guard_no_rank_conversion(record: Dict[str, Any], record_id: str) -> None:
    """Impede que um registro carregue rank derivado de outro sistema (testes 4 e 5)."""
    rank_system = record.get("rank_system")
    traps = CONVERSION_TRAP_FIELDS.get(str(rank_system), [])
    for trap in traps:
        value = record.get(trap)
        if value not in (None, "", "NONE", 0):
            raise ValidationError(
                f"{record_id}: campo derivado '{trap}' preenchido com rank_system='{rank_system}'. "
                "Conversão entre sistemas de rank é proibida (conversions_allowed = [])."
            )


def normalize_record(raw: Dict[str, Any], contract: Dict[str, Any], config: Dict[str, Any], salt: Optional[str]) -> Dict[str, Any]:
    """Normaliza um registro bruto para os 17 campos canônicos, sem inventar valores."""
    if not isinstance(raw, dict):
        raise ValidationError("cada candidato deve ser um objeto JSON.")
    record_id = str(raw.get("demo_id") or raw.get("match_id") or "<sem-id>")

    field_names = [f.get("field") for f in (contract.get("mandatory_fields") or [])] or MANDATORY_FIELDS_FALLBACK
    normalized: Dict[str, Any] = {}
    for name in field_names:
        normalized[name] = raw.get(name, None)

    guard_no_rank_conversion(raw, record_id)

    # Regra de conversão: se o registro declara FACEIT, nenhum campo Valve derivado é aceito.
    if normalized.get("rank_system") in FACEIT_SYSTEMS:
        for trap in ("premier_rating", "valve_competitive_rank"):
            if raw.get(trap) not in (None, "", 0):
                raise ValidationError(f"{record_id}: FACEIT não pode carregar '{trap}' (teste 4).")
    if normalized.get("rank_system") in VALVE_PREMIER_SYSTEMS:
        for trap in ("valve_competitive_rank", "faceit_level"):
            if raw.get(trap) not in (None, "", 0):
                raise ValidationError(f"{record_id}: Premier não pode carregar '{trap}' (teste 5).")

    # Domínio: nunca promover UNKNOWN.
    declared_domain = raw.get("domain_id")
    if declared_domain == "INTERMEDIATE_COMPETITIVE" and str(normalized.get("rank_system")) == "NONE":
        raise ValidationError(
            f"{record_id}: domínio INTERMEDIATE_COMPETITIVE com rank_system = NONE é promoção de UNKNOWN "
            "(teste 6: UnknownRankIsNotPromoted)."
        )

    # Mapa obrigatório.
    if normalized.get("map_name") != config.get("map_name", "de_mirage"):
        normalized["exclusion_reason"] = "NON_MIRAGE_DEMO"
        normalized["accepted"] = False

    # Bucket de Premier bloqueado por política.
    if normalized.get("rank_system") in VALVE_PREMIER_SYSTEMS:
        policy = (contract.get("valve_premier_policy") or {}).get("inclusion_policy")
        if policy == "NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT":
            normalized["exclusion_reason"] = normalized.get("exclusion_reason") or "PREMIER_BUCKET_NOT_DEFINED_PENDING_AUDIT"
            normalized["accepted"] = False

    # SteamID64: pseudonimizar em saída publicada.
    players = raw.get("player_skill_levels") or []
    pseudonymized_players = []
    for player in players:
        if not isinstance(player, dict):
            continue
        entry = dict(player)
        sid = str(entry.pop("steamid64", "") or "")
        if sid:
            entry["player_pseudonym"] = pseudonymize_steamid(sid, salt)
        pseudonymized_players.append(entry)
    normalized["player_skill_levels"] = pseudonymized_players

    # Estatística de nível (só calculada quando há níveis numéricos reais).
    levels = [
        float(p["skill_level"])
        for p in pseudonymized_players
        if str(p.get("skill_level", "")).replace(".", "", 1).isdigit()
    ]
    if levels:
        levels.sort()
        normalized["median_skill_level"] = levels[len(levels) // 2]
        normalized["minimum_skill_level"] = levels[0]
        normalized["maximum_skill_level"] = levels[-1]
        normalized["mixed_skill_match"] = len(set(levels)) > 1
    else:
        normalized["median_skill_level"] = None
        normalized["minimum_skill_level"] = None
        normalized["maximum_skill_level"] = None
        normalized["mixed_skill_match"] = None

    # source_url_reference: apenas identificador estável, nunca link assinado.
    reference = raw.get("source_url_reference")
    if reference is not None:
        marker = detect_signed_url(str(reference))
        if marker:
            raise ValidationError(
                f"{record_id}: source_url_reference contém URL assinada ('{marker}'). "
                "Use identificador estável (ex.: faceit:match:<uuid>)."
            )

    assert_no_signed_url(normalized, f"record[{record_id}]")

    # SteamID64 não pode sobreviver em texto livre do registro.
    leaked = STEAMID64_RE.findall(json.dumps(normalized, ensure_ascii=False))
    if leaked:
        raise ValidationError(f"{record_id}: SteamID64 em claro no registro publicável (teste 16).")

    normalized["_record_id"] = record_id
    return normalized


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fetch_match_metadata.py",
        description=(
            "Normaliza metadado de habilidade nos 17 campos do contrato de domínios, recusando "
            "conversão de rank, promoção de UNKNOWN e persistência de URL assinada. "
            "Modo padrão: --dry-run (nenhuma requisição de rede)."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação | 2 erro de uso.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) valida e normaliza sem rede.")
    mode.add_argument("--execute", action="store_true", help="Buscaria metadado real. Desabilitado nesta fase.")
    parser.add_argument("--candidates", default="", help="JSON com candidatos brutos já obtidos (sem rede).")
    parser.add_argument("--out", default="", help="Grava o resultado normalizado em JSON.")
    parser.add_argument("--audit-log", default="", help="Caminho do audit log append-only (default: stdout).")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    contract = load_contract(config)
    salt = os.environ.get(str((config.get("secret_env_vars") or {}).get("corpus_pseudonym_salt", "")), "") or None

    if args.execute:
        raise ValidationError(
            "coleta real de metadado desabilitada nesta fase: a fonte oficial não está aprovada por "
            "autorização humana. Use --dry-run. O resultado correto da fase é "
            "INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING."
        )

    skeleton = metadata_skeleton(contract)
    result: Dict[str, Any] = {
        "mode": "DRY_RUN",
        "generated_utc": utc_now(),
        "network_requests_executed": 0,
        "mandatory_field_count": len(skeleton),
        "mandatory_fields": skeleton,
        "records_in": 0,
        "records_out": 0,
        "records_rejected": 0,
        "rejected_records": [],
        "records": [],
        "notes": [
            "Sem --candidates o script não produz observação alguma: apenas o esquema derivado do contrato.",
            "Nenhum valor de rank é inferido, interpolado ou convertido.",
        ],
    }

    if args.candidates:
        path = Path(args.candidates)
        if not path.is_absolute():
            path = REPO_ROOT / path
        if not path.is_file():
            raise ValidationError(f"arquivo de candidatos ausente: {path}")
        raw_records = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw_records, dict):
            raw_records = raw_records.get("candidates") or raw_records.get("records") or []
        if not isinstance(raw_records, list):
            raise ValidationError("--candidates deve conter uma lista JSON de objetos.")
        result["records_in"] = len(raw_records)
        for raw in raw_records:
            try:
                normalized = normalize_record(raw, contract, config, salt)
                result["records"].append(normalized)
                result["records_out"] += 1
            except ValidationError as exc:
                result["records_rejected"] += 1
                result["rejected_records"].append({"error": redact(str(exc))})

    assert_no_signed_url(result, "result")

    line = redact(
        json.dumps(
            {
                "timestamp_utc": utc_now(),
                "script": "fetch_match_metadata.py",
                "event": "METADATA_NORMALIZED",
                "records_in": result["records_in"],
                "records_out": result["records_out"],
                "records_rejected": result["records_rejected"],
                "network_requests_executed": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if args.audit_log:
        target = Path(args.audit_log)
        if not target.is_absolute():
            target = REPO_ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    print(f"[AUDIT] {line}")

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"resultado gravado em: {out_path}")

    return EXIT_OK if result["records_rejected"] == 0 else EXIT_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except ValidationError as exc:
        print(f"ERRO de validação: {redact(str(exc))}", file=sys.stderr)
        raise SystemExit(EXIT_VALIDATION)
    except KeyboardInterrupt:
        raise SystemExit(EXIT_VALIDATION)
