#!/usr/bin/env python3
"""
deduplicate_demo.py — Detecção de demos duplicadas por conteúdo (SHA-256).

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §9 (duplicate detection), §7
("múltiplas demos duplicadas" é critério de exclusão), §10 (`demo_sha256`).

O que faz
---------
Percorre os diretórios do corpus intermediário (`raw_demos/`, `archives/`, `processed_npz/`) e:

1. calcula SHA-256 de cada arquivo candidato (streaming, 1 MiB);
2. agrupa por hash e classifica como `UNIQUE` ou `DUPLICATE`;
3. distingue **duplicata exata** (mesmo hash, mesmo tamanho) de **colisão de nome** (nomes iguais,
   conteúdos diferentes — que NÃO é duplicata e é reportada separadamente);
4. opcionalmente cruza com uma lista de hashes conhecidos (`--known-hashes`), útil para detectar
   demo do domínio profissional reintroduzida como intermediária;
5. em `--execute`, move as duplicatas excedentes para `quarantine/` (mantendo a primeira ocorrência),
   nunca apagando nada.

Modo padrão: `--dry-run` — apenas relata, sem mover nem apagar.

`--self-test` cria arquivos temporários fora do repositório (`tempfile`), verifica que a detecção
realmente distingue único/duplicado/colisão-de-nome e falha com exit 1 se a classificação divergir.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação (ou self-test falho) · 2 = erro de uso
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
DEFAULT_CONFIG_PATH = TOOL_DIR / "config.example.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

CANDIDATE_SUFFIXES = {".dem", ".npz", ".zip", ".tar", ".gz", ".bz2", ".tgz"}
REDACTION_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)([^\s\"']+)"),
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


def collect_files(roots: List[Path], suffixes: set) -> List[Path]:
    files: List[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for entry in sorted(root.rglob("*")):
            if entry.is_file() and entry.suffix.lower() in suffixes and entry.name != "README.md":
                files.append(entry)
    return files


def classify(files: List[Path], known_hashes: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Agrupa arquivos por hash e produz a classificação de duplicatas."""
    by_hash: Dict[str, List[Dict[str, Any]]] = {}
    by_name: Dict[str, List[str]] = {}
    records: List[Dict[str, Any]] = []

    for path in files:
        digest = sha256_file(path)
        record = {
            "repo_relative_path": str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
            if REPO_ROOT in path.resolve().parents
            else str(path),
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": digest,
        }
        if known_hashes and digest in known_hashes:
            record["matches_known_hash"] = known_hashes[digest]
        records.append(record)
        by_hash.setdefault(digest, []).append(record)
        by_name.setdefault(path.name, []).append(digest)

    duplicate_groups: List[Dict[str, Any]] = []
    for digest, group in by_hash.items():
        if len(group) > 1:
            duplicate_groups.append(
                {
                    "sha256": digest,
                    "count": len(group),
                    "keep": group[0]["repo_relative_path"],
                    "duplicates": [g["repo_relative_path"] for g in group[1:]],
                    "size_bytes": group[0]["size_bytes"],
                }
            )

    name_collisions = [
        {"name": name, "distinct_hashes": sorted(set(hashes)), "count": len(set(hashes))}
        for name, hashes in by_name.items()
        if len(set(hashes)) > 1
    ]

    cross_domain_hits = [r for r in records if r.get("matches_known_hash")]

    return {
        "files_scanned": len(records),
        "unique_hashes": len(by_hash),
        "duplicate_groups": len(duplicate_groups),
        "excess_duplicate_files": sum(g["count"] - 1 for g in duplicate_groups),
        "name_collisions": len(name_collisions),
        "cross_domain_hash_matches": len(cross_domain_hits),
        "total_bytes_scanned": sum(r["size_bytes"] for r in records),
        "duplicate_detail": duplicate_groups,
        "name_collision_detail": name_collisions,
        "cross_domain_detail": cross_domain_hits,
        "records": records,
    }


def run_self_test() -> int:
    """Testa a classificação com arquivos reais em diretório temporário (fora do repositório)."""
    results: List[Dict[str, Any]] = []
    failures: List[str] = []

    with tempfile.TemporaryDirectory(prefix="csbot_dedup_selftest_") as tmp:
        root = Path(tmp)
        (root / "sub").mkdir()
        (root / "a.dem").write_bytes(b"DEMO-CONTENT-ALPHA" * 100)
        (root / "b.dem").write_bytes(b"DEMO-CONTENT-ALPHA" * 100)  # duplicata exata de a.dem
        (root / "c.dem").write_bytes(b"DEMO-CONTENT-BETA" * 100)   # único
        (root / "sub" / "a.dem").write_bytes(b"DIFFERENT-CONTENT" * 100)  # colisão de nome

        files = collect_files([root], CANDIDATE_SUFFIXES)
        outcome = classify(files)

        checks = [
            ("files_scanned_is_4", outcome["files_scanned"], 4),
            ("duplicate_groups_is_1", outcome["duplicate_groups"], 1),
            ("excess_duplicate_files_is_1", outcome["excess_duplicate_files"], 1),
            ("name_collisions_is_1", outcome["name_collisions"], 1),
            ("unique_hashes_is_3", outcome["unique_hashes"], 3),
        ]
        for name, actual, expected in checks:
            ok = actual == expected
            results.append({"case": name, "expected": expected, "actual": actual, "ok": ok})
            if not ok:
                failures.append(f"{name}: esperado {expected}, obtido {actual}")

        # Checagem de cruzamento com hashes conhecidos (cross-domain).
        known = {sha256_file(root / "c.dem"): "professional_corpus_demo_x"}
        outcome_known = classify(files, known_hashes=known)
        ok = outcome_known["cross_domain_hash_matches"] == 1
        results.append(
            {
                "case": "cross_domain_match_detected",
                "expected": 1,
                "actual": outcome_known["cross_domain_hash_matches"],
                "ok": ok,
            }
        )
        if not ok:
            failures.append("cross_domain_match_detected divergente")

    passed = len(results) - len(failures)
    print(
        json.dumps(
            {
                "self_test": "deduplicate_demo.py",
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


def load_known_hashes(path: Path) -> Dict[str, str]:
    """Carrega um mapa sha256 -> rótulo a partir de JSON {'sha256': 'label'} ou lista de objetos."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping: Dict[str, str] = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(key, str) and len(key) == 64:
                mapping[key.lower()] = str(value)
            elif isinstance(value, dict) and "sha256" in value:
                mapping[str(value["sha256"]).lower()] = str(value.get("demo_id", "known"))
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and item.get("sha256"):
                mapping[str(item["sha256"]).lower()] = str(item.get("demo_id") or item.get("label") or "known")
    return mapping


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="deduplicate_demo.py",
        description=(
            "Detecta demos duplicadas por SHA-256 nos diretórios do corpus intermediário, "
            "distingue colisão de nome de duplicata real e move excedentes para quarantine/ "
            "apenas com --execute."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação (ou self-test falho) | 2 erro de uso.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    parser.add_argument("--known-hashes", default="", help="JSON com hashes conhecidos (ex.: corpus profissional).")
    parser.add_argument("--self-test", action="store_true", help="Executa 6 casos em diretório temporário.")
    parser.add_argument("--out", default="", help="Grava o relatório em JSON.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) apenas relata.")
    mode.add_argument("--execute", action="store_true", help="Move duplicatas excedentes para quarantine/.")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))

    if args.self_test:
        return run_self_test()

    paths_cfg = config.get("paths") or {}
    roots = [
        REPO_ROOT / str(paths_cfg.get(key, ""))
        for key in ("raw_demos", "archives", "processed_npz")
        if paths_cfg.get(key)
    ]
    known: Optional[Dict[str, str]] = None
    if args.known_hashes:
        known_path = Path(args.known_hashes)
        if not known_path.is_absolute():
            known_path = REPO_ROOT / known_path
        if not known_path.is_file():
            raise ValidationError(f"arquivo de hashes conhecidos ausente: {known_path}")
        known = load_known_hashes(known_path)

    files = collect_files(roots, CANDIDATE_SUFFIXES)
    outcome = classify(files, known_hashes=known)
    outcome["mode"] = "EXECUTE" if args.execute else "DRY_RUN"
    outcome["directories_scanned"] = [
        str(root.resolve().relative_to(REPO_ROOT)).replace("\\", "/") for root in roots if root.is_dir()
    ]
    outcome["generated_utc"] = utc_now()
    outcome["network_requests_executed"] = 0

    moved: List[Dict[str, str]] = []
    if args.execute:
        quarantine_dir = REPO_ROOT / str(paths_cfg.get("quarantine", ""))
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        for group in outcome["duplicate_detail"]:
            for rel in group["duplicates"]:
                source = REPO_ROOT / rel
                if not source.is_file():
                    continue
                target = quarantine_dir / source.name
                if target.exists():
                    target = quarantine_dir / f"{source.stem}__{group['sha256'][:8]}{source.suffix}"
                source.replace(target)
                moved.append(
                    {
                        "from": rel,
                        "to": str(target.resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
                        "sha256": group["sha256"],
                    }
                )
    outcome["quarantined"] = moved
    outcome["quarantined_count"] = len(moved)

    # Saída resumida no stdout; detalhe completo fica em --out para não inundar o terminal.
    summary = {k: v for k, v in outcome.items() if k not in ("records",)}
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(outcome, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"relatório gravado em: {out_path}")
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
