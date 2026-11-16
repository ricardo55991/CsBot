#!/usr/bin/env python3
"""
verify_archive.py — Verificação de integridade e segurança de pacotes de demo.

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §9
(archive validation, checksum, decompression segura, quarantine).

O que faz
---------
Verifica um pacote (`.zip`, `.tar`, `.tar.gz`, `.tgz`, `.gz`, `.bz2`) antes de qualquer extração:

1. **magic bytes** — recusa arquivo cujo conteúdo não corresponda ao formato declarado;
2. **checksum** — recusa `archive_sha256` divergente (SHA-256 completo, 64 hex, calculado do disco);
3. **entradas perigosas** — recusa path traversal (`..`), caminho absoluto, unidade Windows
   (`C:\\`), symlink, hardlink e device file;
4. **limites de bomba de descompressão** — número de entradas, bytes descomprimidos totais e razão
   de compressão acima do configurado;
5. **conteúdo esperado** — o pacote precisa conter ao menos uma extensão aceita (`.dem`).

Em `--self-test` o script constrói casos embutidos em memória (zip seguro, zip com `..`, zip com
caminho absoluto, zip com symlink, bytes corrompidos, checksum divergente) e falha com exit 1 se
qualquer decisão divergir. Nenhum arquivo é gravado em disco pelo self-test.

Modo padrão de operação: `--dry-run` (relata o que faria, inclusive o destino de quarentena).

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação (ou self-test falho) · 2 = erro de uso
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
DEFAULT_CONFIG_PATH = TOOL_DIR / "config.example.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

ZIP_MAGIC = b"PK\x03\x04"
GZIP_MAGIC = b"\x1f\x8b"
BZ2_MAGIC = b"BZh"
TAR_USTAR_OFFSET = (257, b"ustar")

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_format(head: bytes) -> str:
    """Detecta o formato pelos magic bytes. Retorna 'zip'|'gzip'|'bzip2'|'tar'|'unknown'."""
    if head.startswith(ZIP_MAGIC):
        return "zip"
    if head.startswith(GZIP_MAGIC):
        return "gzip"
    if head.startswith(BZ2_MAGIC):
        return "bzip2"
    offset, signature = TAR_USTAR_OFFSET
    if len(head) > offset + len(signature) and head[offset : offset + len(signature)] == signature:
        return "tar"
    return "unknown"


def is_unsafe_entry(name: str) -> Tuple[bool, str]:
    """Detecta caminho absoluto, traversal e unidade Windows em nome de entrada de arquivo."""
    normalized = str(name).replace("\\", "/").strip()
    if not normalized:
        return True, "EMPTY_ENTRY_NAME"
    if normalized.startswith("/"):
        return True, "ABSOLUTE_PATH"
    if WINDOWS_DRIVE_RE.match(normalized):
        return True, "WINDOWS_ABSOLUTE_PATH"
    parts = [p for p in normalized.split("/") if p]
    if any(part == ".." for part in parts):
        return True, "PARENT_TRAVERSAL"
    return False, "OK"


def analyze_zip(buffer: bytes, cfg: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    entries: List[str] = []
    total_uncompressed = 0
    dem_found = False
    try:
        with zipfile.ZipFile(io.BytesIO(buffer)) as archive:
            infos = archive.infolist()
            if len(infos) > int(cfg.get("max_entries", 5000)):
                findings.append({"issue": "TOO_MANY_ENTRIES", "detail": str(len(infos))})
            for info in infos:
                unsafe, reason = is_unsafe_entry(info.filename)
                if unsafe:
                    findings.append({"issue": "UNSAFE_ENTRY_PATH", "detail": f"{reason}:{info.filename}"})
                if info.is_dir():
                    continue
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    findings.append({"issue": "SYMLINK_ENTRY", "detail": info.filename})
                if mode in (0o020000, 0o060000):
                    findings.append({"issue": "DEVICE_ENTRY", "detail": info.filename})
                entries.append(info.filename)
                total_uncompressed += int(info.file_size)
                if info.filename.lower().endswith(".dem"):
                    dem_found = True
    except zipfile.BadZipFile as exc:
        findings.append({"issue": "INVALID_ZIP", "detail": str(exc)})

    compressed = max(1, len(buffer))
    ratio = total_uncompressed / compressed
    if total_uncompressed > int(cfg.get("max_uncompressed_bytes", 2097152000)):
        findings.append({"issue": "UNCOMPRESSED_SIZE_LIMIT_EXCEEDED", "detail": str(total_uncompressed)})
    if ratio > float(cfg.get("max_compression_ratio", 200)):
        findings.append({"issue": "SUSPICIOUS_COMPRESSION_RATIO", "detail": f"{ratio:.2f}"})
    return {
        "entries": len(entries),
        "total_uncompressed_bytes": total_uncompressed,
        "compression_ratio": round(ratio, 3),
        "contains_dem": dem_found,
        "findings": findings,
    }


def analyze_tar(buffer: bytes, cfg: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    entries: List[str] = []
    total_uncompressed = 0
    dem_found = False
    try:
        with tarfile.open(fileobj=io.BytesIO(buffer), mode="r:*") as archive:
            members = archive.getmembers()
            if len(members) > int(cfg.get("max_entries", 5000)):
                findings.append({"issue": "TOO_MANY_ENTRIES", "detail": str(len(members))})
            for member in members:
                unsafe, reason = is_unsafe_entry(member.name)
                if unsafe:
                    findings.append({"issue": "UNSAFE_ENTRY_PATH", "detail": f"{reason}:{member.name}"})
                if member.issym() or member.islnk():
                    findings.append({"issue": "LINK_ENTRY", "detail": member.name})
                if member.ischr() or member.isblk() or member.isfifo():
                    findings.append({"issue": "DEVICE_ENTRY", "detail": member.name})
                if member.isfile():
                    entries.append(member.name)
                    total_uncompressed += int(member.size)
                    if member.name.lower().endswith(".dem"):
                        dem_found = True
    except tarfile.TarError as exc:
        findings.append({"issue": "INVALID_TAR", "detail": str(exc)})

    compressed = max(1, len(buffer))
    ratio = total_uncompressed / compressed
    if total_uncompressed > int(cfg.get("max_uncompressed_bytes", 2097152000)):
        findings.append({"issue": "UNCOMPRESSED_SIZE_LIMIT_EXCEEDED", "detail": str(total_uncompressed)})
    if ratio > float(cfg.get("max_compression_ratio", 200)):
        findings.append({"issue": "SUSPICIOUS_COMPRESSION_RATIO", "detail": f"{ratio:.2f}"})
    return {
        "entries": len(entries),
        "total_uncompressed_bytes": total_uncompressed,
        "compression_ratio": round(ratio, 3),
        "contains_dem": dem_found,
        "findings": findings,
    }


def verify(buffer: bytes, declared_format: str, expected_sha256: Optional[str], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Executa todas as verificações sobre o conteúdo em memória e retorna o laudo."""
    findings: List[Dict[str, str]] = []
    detected = detect_format(buffer[:512])

    declared = (declared_format or "").lower().lstrip(".")
    if declared in ("zip",) and detected != "zip":
        findings.append({"issue": "MAGIC_BYTES_MISMATCH", "detail": f"declarado zip, detectado {detected}"})
    elif declared in ("tar", "gz", "tgz", "tar.gz") and detected not in ("tar", "gzip"):
        findings.append({"issue": "MAGIC_BYTES_MISMATCH", "detail": f"declarado {declared}, detectado {detected}"})
    elif declared in ("bz2", "tar.bz2") and detected not in ("bzip2", "tar"):
        findings.append({"issue": "MAGIC_BYTES_MISMATCH", "detail": f"declarado {declared}, detectado {detected}"})
    if detected == "unknown":
        findings.append({"issue": "UNKNOWN_ARCHIVE_FORMAT", "detail": "magic bytes não reconhecidos"})

    actual_sha = sha256_bytes(buffer)
    if expected_sha256 is not None:
        if not SHA256_RE.match(str(expected_sha256)):
            findings.append({"issue": "INVALID_EXPECTED_SHA256_FORMAT", "detail": str(expected_sha256)[:16]})
        elif actual_sha != str(expected_sha256).lower():
            findings.append({"issue": "CHECKSUM_MISMATCH", "detail": "sha256 divergente"})

    if detected == "zip":
        detail = analyze_zip(buffer, cfg)
    elif detected in ("tar", "gzip", "bzip2"):
        detail = analyze_tar(buffer, cfg)
    else:
        detail = {
            "entries": 0,
            "total_uncompressed_bytes": 0,
            "compression_ratio": 0.0,
            "contains_dem": False,
            "findings": [],
        }

    findings.extend(detail.pop("findings", []))

    if detail["entries"] > 0 and not detail["contains_dem"]:
        findings.append({"issue": "NO_DEM_ENTRY", "detail": "pacote não contém nenhum .dem"})

    verdict = "PASS" if not findings else "FAIL"
    return {
        "verdict": verdict,
        "declared_format": declared or None,
        "detected_format": detected,
        "archive_sha256": actual_sha,
        "archive_sha256_length": len(actual_sha),
        "expected_sha256": expected_sha256,
        "bytes_analyzed": len(buffer),
        "entries": detail["entries"],
        "total_uncompressed_bytes": detail["total_uncompressed_bytes"],
        "compression_ratio": detail["compression_ratio"],
        "contains_dem": detail["contains_dem"],
        "findings": findings,
        "finding_count": len(findings),
        "recommended_action": "PROCEED_TO_EXTRACTION" if verdict == "PASS" else "MOVE_TO_QUARANTINE",
    }


def _make_zip(entries: List[Tuple[str, bytes]], symlink_names: Optional[List[str]] = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries:
            archive.writestr(name, payload)
        for link_name in symlink_names or []:
            info = zipfile.ZipInfo(link_name)
            info.external_attr = 0o120777 << 16
            archive.writestr(info, "/etc/passwd")
    return buffer.getvalue()


def run_self_test(cfg: Dict[str, Any]) -> int:
    cases: List[Dict[str, Any]] = []

    safe_zip = _make_zip([("match_001.dem", b"DEMO-BYTES" * 64)])
    traversal_zip = _make_zip([("../../etc/evil.dem", b"x" * 32)])
    absolute_zip = _make_zip([("/abs/path/evil.dem", b"x" * 32)])
    windows_abs_zip = _make_zip([("C:/windows/evil.dem", b"x" * 32)])
    symlink_zip = _make_zip([("ok.dem", b"x" * 32)], symlink_names=["link.dem"])
    corrupt = b"NOT-AN-ARCHIVE-AT-ALL" * 8

    sha_safe = sha256_bytes(safe_zip)

    scenarios = [
        ("safe_zip_passes", safe_zip, "zip", sha_safe, "PASS"),
        ("traversal_zip_rejected", traversal_zip, "zip", None, "FAIL"),
        ("absolute_path_zip_rejected", absolute_zip, "zip", None, "FAIL"),
        ("windows_absolute_zip_rejected", windows_abs_zip, "zip", None, "FAIL"),
        ("symlink_zip_rejected", symlink_zip, "zip", None, "FAIL"),
        ("corrupt_bytes_rejected", corrupt, "zip", None, "FAIL"),
        ("checksum_mismatch_rejected", safe_zip, "zip", "0" * 64, "FAIL"),
        ("invalid_expected_sha_format_rejected", safe_zip, "zip", "abc123", "FAIL"),
    ]

    failures: List[str] = []
    for name, payload, declared, expected_sha, expected_verdict in scenarios:
        report = verify(payload, declared, expected_sha, cfg)
        ok = report["verdict"] == expected_verdict
        cases.append(
            {
                "case": name,
                "expected_verdict": expected_verdict,
                "actual_verdict": report["verdict"],
                "detected_format": report["detected_format"],
                "finding_count": report["finding_count"],
                "issues": sorted({f["issue"] for f in report["findings"]}),
                "ok": ok,
            }
        )
        if not ok:
            failures.append(f"{name}: esperado {expected_verdict}, obtido {report['verdict']}")

    passed = len(cases) - len(failures)
    print(
        json.dumps(
            {
                "self_test": "verify_archive.py",
                "generated_utc": utc_now(),
                "cases_total": len(cases),
                "cases_passed": passed,
                "cases_failed": len(failures),
                "aggregation": f"({passed}/{len(cases)})",
                "fixture_class": "TEST_FIXTURE_NOT_REAL_DATA",
                "network_requests_executed": 0,
                "files_written_to_disk": 0,
                "results": cases,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if failures:
        print("SELF-TEST FALHOU:\n- " + "\n- ".join(failures), file=sys.stderr)
        return EXIT_VALIDATION
    return EXIT_OK


def load_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"config não encontrada: {path}")
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("signed_url_persistence_allowed") is True:
        raise ValidationError("config inválida: signed_url_persistence_allowed = true é proibido.")
    return config


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify_archive.py",
        description=(
            "Verifica magic bytes, checksum SHA-256, entradas perigosas (path traversal, absoluto, "
            "symlink) e limites de descompressão de um pacote de demos. Modo padrão: --dry-run."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação (ou self-test falho) | 2 erro de uso.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    parser.add_argument("--path", default="", help="Caminho do pacote a verificar.")
    parser.add_argument("--format", default="", help="Formato declarado (zip|tar|gz|bz2).")
    parser.add_argument("--sha256", dest="expected_sha256", default=None, help="SHA-256 esperado (64 hex).")
    parser.add_argument("--self-test", action="store_true", help="Executa 8 casos embutidos em memória.")
    parser.add_argument("--out", default="", help="Grava o laudo em JSON.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) verifica e relata; não move nada.")
    mode.add_argument("--execute", action="store_true", help="Em falha, move o arquivo para quarantine/.")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    archive_cfg = config.get("archive") or {}

    if args.self_test:
        return run_self_test(archive_cfg)

    if not args.path:
        print("ERRO de uso: informe --path ou --self-test.", file=sys.stderr)
        return EXIT_USAGE

    archive_path = Path(args.path)
    if not archive_path.is_absolute():
        archive_path = REPO_ROOT / archive_path
    if not archive_path.is_file():
        raise ValidationError(f"pacote ausente: {archive_path}")

    buffer = archive_path.read_bytes()
    declared = args.format or "".join(archive_path.suffixes).lstrip(".")
    report = verify(buffer, declared, args.expected_sha256, archive_cfg)
    try:
        report["archive_path"] = str(archive_path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        report["archive_path"] = str(archive_path)
    report["archive_size_bytes"] = archive_path.stat().st_size
    report["mode"] = "EXECUTE" if args.execute else "DRY_RUN"

    if report["verdict"] == "FAIL" and args.execute:
        quarantine_dir = REPO_ROOT / str((config.get("paths") or {}).get("quarantine", ""))
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        target = quarantine_dir / archive_path.name
        if target.exists():
            target = quarantine_dir / f"{archive_path.stem}__{report['archive_sha256'][:8]}{archive_path.suffix}"
        archive_path.replace(target)
        report["quarantined_to"] = str(target.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    elif report["verdict"] == "FAIL":
        report["quarantine_target_would_be"] = (
            str((config.get("paths") or {}).get("quarantine", "")) + "/" + archive_path.name
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"laudo gravado em: {out_path}")
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
