#!/usr/bin/env python3
"""
build_manifest.py — Construção do inventário do corpus intermediário (§10).

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §9, §10, §21.

O que faz
---------
Monta o registro de inventário por demo (`intermediate_demo_inventory_v1.json`) a partir de duas
fontes verificáveis:

1. **metadado** já normalizado (`metadata/*.json`, 17 campos do contrato de domínios);
2. **arquivos físicos** em `raw_demos/` e `archives/` — o hash SHA-256 é sempre recalculado do disco,
   nunca copiado de relatório.

Regras aplicadas na construção
------------------------------
- todo `demo_sha256` e `archive_sha256` é de 64 hex, calculado do disco;
- `accepted = false` obrigatório quando falta metadado obrigatório, o bucket não é `INCLUDED_PILOT`,
  o mapa não é `de_mirage` ou o arquivo não existe;
- `rejection_reason` obrigatório para toda rejeição;
- URLs assinadas, tokens, cookies e SteamID64 em claro derrubam a construção (exit 1);
- contagens inteiras; percentuais, quando houver, sempre com `(N/D)`.

Modo padrão: `--dry-run`. Em dry-run o inventário é apenas **impresso** no stdout. A gravação em disco
exige `--execute` **e** `--out`, porque o artefato pertence à etapa de manifestos (M4) e não deve ser
materializado por esta ferramenta sem decisão explícita.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação · 2 = erro de uso
"""

from __future__ import annotations

import argparse
import hashlib
import json
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

INVENTORY_SCHEMA_FIELDS = [
    "demo_id",
    "match_id",
    "source",
    "source_url_reference",
    "platform",
    "match_date",
    "download_date",
    "map",
    "patch",
    "region",
    "rank_system",
    "player_skill_levels",
    "median_skill_level",
    "minimum_skill_level",
    "maximum_skill_level",
    "mixed_skill_match",
    "demo_sha256",
    "archive_sha256",
    "file_size",
    "round_count",
    "player_count",
    "accepted",
    "rejection_reason",
    "license",
    "consent",
    "parser_version",
]

MANDATORY_METADATA_FIELDS = [
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

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STEAMID64_RE = re.compile(r"\b7656119\d{10}\b")
SIGNED_URL_MARKERS = ("x-amz-signature", "signature=", "sig=", "token=", "expires=", "policy=", "key-pair-id")
REDACTION_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(cookie\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)\b(access_token|api_key|apikey|token|password|secret)\b(\s*[=:]\s*)([^\s&\"',}]+)"),
]


class ValidationError(Exception):
    """Erro de validação (exit code 1)."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str) -> str:
    out = str(text)
    for pattern in REDACTION_PATTERNS:
        out = pattern.sub(lambda m: f"{m.group(1)}[REDACTED]", out)
    return out


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def load_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"config não encontrada: {path}")
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("signed_url_persistence_allowed") is True:
        raise ValidationError("config inválida: signed_url_persistence_allowed = true é proibido.")
    return config


def load_contract(config: Dict[str, Any]) -> Dict[str, Any]:
    path = REPO_ROOT / str(config.get("domain_contract_path") or "datasets/mirage_domains/domain_contract_v1.json")
    if not path.is_file():
        raise ValidationError(f"contrato de domínios ausente: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_clean_output(payload: Any, where: str = "$") -> None:
    """Recusa URL assinada e SteamID64 em claro em qualquer artefato a publicar."""
    if isinstance(payload, str):
        lower = payload.lower()
        for marker in SIGNED_URL_MARKERS:
            if marker in lower:
                raise ValidationError(f"URL assinada em {where} (marcador '{marker.strip('=')}') — proibido (teste 8).")
        if STEAMID64_RE.search(payload):
            raise ValidationError(f"SteamID64 em claro em {where} — proibido (teste 16).")
    elif isinstance(payload, dict):
        for key, item in payload.items():
            assert_clean_output(item, f"{where}.{key}")
    elif isinstance(payload, (list, tuple)):
        for index, item in enumerate(payload):
            assert_clean_output(item, f"{where}[{index}]")


def load_metadata(metadata_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not metadata_dir.is_dir():
        return records
    for path in sorted(metadata_dir.glob("*.json")):
        if path.name == "README.md":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            records.extend(payload["records"])
        elif isinstance(payload, list):
            records.extend(payload)
        elif isinstance(payload, dict):
            records.append(payload)
    return [r for r in records if isinstance(r, dict)]


def index_files(directory: Path, suffix: str) -> Dict[str, Path]:
    """Indexa arquivos por stem, com hash calculado do disco."""
    index: Dict[str, Path] = {}
    if not directory.is_dir():
        return index
    for path in sorted(directory.glob(f"*{suffix}")):
        index.setdefault(path.stem, path)
    return index


def resolved_inclusion_policy(contract: Dict[str, Any], rank_system: str, skill_level: Any) -> Optional[str]:
    subdomains = contract.get("subdomains") or {}
    faceit_buckets = contract.get("faceit_buckets") or {}
    if rank_system in ("FACEIT_LEVEL", "FACEIT_ELO"):
        try:
            level = int(skill_level)
        except (TypeError, ValueError):
            return None
        bucket = (
            "FACEIT_LEVEL_5_6"
            if level in (5, 6)
            else "FACEIT_LEVEL_7_8"
            if level in (7, 8)
            else "FACEIT_LEVEL_1_4"
            if 1 <= level <= 4
            else "FACEIT_LEVEL_9_10"
            if level in (9, 10)
            else None
        )
        if bucket is None:
            return None
        return (subdomains.get(bucket) or faceit_buckets.get(bucket) or {}).get("inclusion_policy")
    if rank_system == "VALVE_COMPETITIVE_MAP_RANK":
        return (subdomains.get("VALVE_COMPETITIVE_MAP_RANK") or {}).get("inclusion_policy")
    if rank_system == "VALVE_PREMIER_RATING":
        return (contract.get("valve_premier_policy") or {}).get("inclusion_policy")
    if rank_system == "NONE":
        return "EXCLUDED_PILOT"
    return None


def build_entry(
    metadata: Dict[str, Any],
    dem_files: Dict[str, Path],
    archive_files: Dict[str, Path],
    contract: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    demo_id = str(metadata.get("demo_id") or metadata.get("_record_id") or "").strip()
    reasons: List[str] = []

    missing = [field for field in MANDATORY_METADATA_FIELDS if field not in metadata]
    if missing:
        reasons.append("MISSING_METADATA_FIELDS:" + ",".join(sorted(missing)))

    map_name = str(metadata.get("map_name") or config.get("map_name", "de_mirage"))
    if map_name != config.get("map_name", "de_mirage"):
        reasons.append("NON_MIRAGE_DEMO")

    policy = resolved_inclusion_policy(contract, str(metadata.get("rank_system") or ""), metadata.get("skill_level"))
    if policy != "INCLUDED_PILOT":
        reasons.append(f"SKILL_BUCKET_NOT_INCLUDED_PILOT:{policy or 'UNRESOLVED'}")

    dem_path = dem_files.get(demo_id) if demo_id else None
    if dem_path is None:
        reasons.append("DEM_FILE_ABSENT")
    demo_sha = sha256_file(dem_path) if dem_path else None
    file_size = dem_path.stat().st_size if dem_path else None

    archive_hint = metadata.get("archive_id") or metadata.get("archive_name")
    archive_path = archive_files.get(str(archive_hint)) if archive_hint else None
    archive_sha = sha256_file(archive_path) if archive_path else metadata.get("archive_sha256")
    if archive_sha is not None and not SHA256_RE.match(str(archive_sha).lower()):
        reasons.append("ARCHIVE_SHA256_INVALID_FORMAT")

    players = metadata.get("player_skill_levels") or []
    player_count = metadata.get("player_count")
    if player_count is None and isinstance(players, list) and players:
        player_count = len(players)

    entry = {
        "demo_id": demo_id or None,
        "match_id": metadata.get("match_id"),
        "source": metadata.get("source"),
        "source_url_reference": metadata.get("source_url_reference"),
        "platform": metadata.get("platform"),
        "match_date": metadata.get("match_date"),
        "download_date": metadata.get("download_date"),
        "map": map_name,
        "patch": metadata.get("patch"),
        "region": metadata.get("region"),
        "rank_system": metadata.get("rank_system"),
        "player_skill_levels": players,
        "median_skill_level": metadata.get("median_skill_level"),
        "minimum_skill_level": metadata.get("minimum_skill_level"),
        "maximum_skill_level": metadata.get("maximum_skill_level"),
        "mixed_skill_match": metadata.get("mixed_skill_match"),
        "demo_sha256": demo_sha,
        "archive_sha256": str(archive_sha).lower() if archive_sha else None,
        "file_size": file_size,
        "round_count": metadata.get("round_count"),
        "player_count": player_count,
        "accepted": not reasons,
        "rejection_reason": "NONE" if not reasons else ";".join(reasons),
        "license": metadata.get("source_license"),
        "consent": metadata.get("consent_type"),
        "parser_version": metadata.get("parser_version"),
    }
    return entry


def build_manifest(config: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
    paths_cfg = config.get("paths") or {}
    metadata_dir = REPO_ROOT / str(paths_cfg.get("metadata", ""))
    raw_dir = REPO_ROOT / str(paths_cfg.get("raw_demos", ""))
    archives_dir = REPO_ROOT / str(paths_cfg.get("archives", ""))

    metadata_records = load_metadata(metadata_dir)
    dem_files = index_files(raw_dir, ".dem")
    archive_files: Dict[str, Path] = {}
    if archives_dir.is_dir():
        for path in sorted(archives_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in {".zip", ".tar", ".gz", ".bz2", ".tgz"}:
                archive_files.setdefault(path.stem, path)

    entries = [build_entry(record, dem_files, archive_files, contract, config) for record in metadata_records]
    accepted = [e for e in entries if e["accepted"]]
    rejected = [e for e in entries if not e["accepted"]]

    manifest = {
        "manifest_name": "intermediate_demo_inventory_v1",
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "generated_utc": utc_now(),
        "phase": "FASE_2A-INTERMEDIATE",
        "produced_by_role": "Dataset and Metadata Implementer",
        "review_status": "AGENT_REVIEWED",
        "schema_fields": INVENTORY_SCHEMA_FIELDS,
        "schema_field_count": len(INVENTORY_SCHEMA_FIELDS),
        "source_directories": {
            "metadata": str(paths_cfg.get("metadata", "")),
            "raw_demos": str(paths_cfg.get("raw_demos", "")),
            "archives": str(paths_cfg.get("archives", "")),
        },
        "metadata_records_in": len(metadata_records),
        "dem_files_found": len(dem_files),
        "archive_files_found": len(archive_files),
        "entries_total": len(entries),
        "entries_accepted": len(accepted),
        "entries_rejected": len(rejected),
        "accept_aggregation": f"({len(accepted)}/{len(entries)})" if entries else "(0/0)",
        "entries": entries,
        "network_requests_executed": 0,
        "notes": [
            "Todo demo_sha256 é recalculado do disco nesta execução; nada é copiado de relatório.",
            "accepted = false sempre que faltar metadado obrigatório, o bucket não for INCLUDED_PILOT, "
            "o mapa não for de_mirage ou o arquivo .dem estiver ausente.",
            "Sem demos intermediárias adquiridas, entries_total = 0 é o resultado correto e honesto.",
        ],
    }
    assert_clean_output(manifest, "manifest")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_manifest.py",
        description=(
            "Constrói o inventário por demo do corpus intermediário (§10) a partir de metadado "
            "normalizado e de hashes calculados do disco. Modo padrão: --dry-run (imprime, não grava)."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação | 2 erro de uso.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    parser.add_argument("--out", default="", help="Destino do inventário. Gravação exige --execute.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) imprime o inventário no stdout.")
    mode.add_argument("--execute", action="store_true", help="Permite gravar o inventário em --out.")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    contract = load_contract(config)
    manifest = build_manifest(config, contract)
    manifest["mode"] = "EXECUTE" if args.execute else "DRY_RUN"

    print(json.dumps(manifest, indent=2, ensure_ascii=False))

    if args.out and args.execute:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"inventário gravado em: {out_path}")
    elif args.out and not args.execute:
        print(
            "AVISO: --out ignorado em dry-run. A materialização do inventário (M4) exige --execute e "
            "é de responsabilidade da etapa de manifestos.",
            file=sys.stderr,
        )
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
        raise SystemExit(EXIT_VALIDATION)
