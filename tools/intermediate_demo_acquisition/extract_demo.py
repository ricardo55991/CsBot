#!/usr/bin/env python3
"""
extract_demo.py — Extração segura de demos e integração com o pipeline NPZ canônico.

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §9 (decompression segura), §11.

O que faz
---------
1. **Extração segura** de um pacote (`.zip`/`.tar`) para `raw_demos/`, bloqueando:
   - path traversal (`../`), caminho absoluto POSIX e unidade Windows (`C:\\`);
   - symlink, hardlink e device file;
   - destino que escape da raiz de extração após `resolve()`;
   - excedente de bytes descomprimidos.
2. **Integração com o pipeline canônico DEM → NPZ** (`tools/mlmove_pipeline/extract_16hz_tensors.py`),
   que é **reutilizado, nunca reimplementado nem modificado**. O ponto de compatibilidade real é a
   variável de ambiente `CSBOT_PIPELINE_DIR`, lida em
   `tools/mlmove_pipeline/contract_spec.py` (linhas 53–65), que define
   `RAW_DEMOS_DIR_D = <CSBOT_PIPELINE_DIR>/raw_demos` e
   `EXTRACTED_TENSORS_DIR_D = <CSBOT_PIPELINE_DIR>/extracted_tensors`.
   Apontando `CSBOT_PIPELINE_DIR` para `datasets/mirage_domains/intermediate_competitive/`, o extrator
   canônico passa a ler de `.../intermediate_competitive/raw_demos` e a escrever em
   `.../intermediate_competitive/extracted_tensors/de_mirage`, de onde os `.npz` são relocados para
   `processed_npz/`. Nenhuma linha do pipeline canônico é alterada.

Modo padrão: `--dry-run`. Em dry-run nada é extraído, nada é executado como subprocesso e nenhum
arquivo é gravado.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação (ou self-test falho) · 2 = erro de uso
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
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


def load_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"config não encontrada: {path}")
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("signed_url_persistence_allowed") is True:
        raise ValidationError("config inválida: signed_url_persistence_allowed = true é proibido.")
    return config


def safe_target(dest_root: Path, member_name: str) -> Tuple[Optional[Path], str]:
    """
    Resolve o destino de uma entrada garantindo contenção dentro de `dest_root`.
    Retorna (caminho, 'OK') ou (None, motivo).
    """
    normalized = str(member_name).replace("\\", "/").strip()
    if not normalized:
        return None, "EMPTY_ENTRY_NAME"
    if normalized.startswith("/"):
        return None, "ABSOLUTE_PATH"
    if WINDOWS_DRIVE_RE.match(normalized):
        return None, "WINDOWS_ABSOLUTE_PATH"
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if any(part == ".." for part in parts):
        return None, "PARENT_TRAVERSAL"
    root = dest_root.resolve()
    candidate = (root / "/".join(parts)).resolve()
    if candidate != root and root not in candidate.parents:
        return None, "OUTSIDE_DEST_ROOT"
    return candidate, "OK"


def plan_zip(buffer_path: Path, dest_root: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    rejected: List[Dict[str, str]] = []
    total = 0
    with zipfile.ZipFile(buffer_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            mode = (info.external_attr >> 16) & 0o170000
            target, reason = safe_target(dest_root, info.filename)
            if mode == 0o120000:
                rejected.append({"entry": info.filename, "reason": "SYMLINK_ENTRY"})
                continue
            if reason != "OK":
                rejected.append({"entry": info.filename, "reason": reason})
                continue
            total += int(info.file_size)
            entries.append(
                {
                    "entry": info.filename,
                    "target": str(target.resolve().relative_to(REPO_ROOT)).replace("\\", "/") if target else None,
                    "declared_size_bytes": int(info.file_size),
                    "is_dem": info.filename.lower().endswith(".dem"),
                }
            )
    if total > int(cfg.get("max_uncompressed_bytes", 2097152000)):
        rejected.append({"entry": "<total>", "reason": f"UNCOMPRESSED_SIZE_LIMIT_EXCEEDED:{total}"})
    return {"format": "zip", "entries": entries, "rejected_entries": rejected, "total_uncompressed_bytes": total}


def plan_tar(buffer_path: Path, dest_root: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    rejected: List[Dict[str, str]] = []
    total = 0
    with tarfile.open(buffer_path, "r:*") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                if member.issym() or member.islnk():
                    rejected.append({"entry": member.name, "reason": "LINK_ENTRY"})
                elif member.ischr() or member.isblk() or member.isfifo():
                    rejected.append({"entry": member.name, "reason": "DEVICE_ENTRY"})
                continue
            target, reason = safe_target(dest_root, member.name)
            if reason != "OK":
                rejected.append({"entry": member.name, "reason": reason})
                continue
            total += int(member.size)
            entries.append(
                {
                    "entry": member.name,
                    "target": str(target.resolve().relative_to(REPO_ROOT)).replace("\\", "/") if target else None,
                    "declared_size_bytes": int(member.size),
                    "is_dem": member.name.lower().endswith(".dem"),
                }
            )
    if total > int(cfg.get("max_uncompressed_bytes", 2097152000)):
        rejected.append({"entry": "<total>", "reason": f"UNCOMPRESSED_SIZE_LIMIT_EXCEEDED:{total}"})
    return {"format": "tar", "entries": entries, "rejected_entries": rejected, "total_uncompressed_bytes": total}


def detect_container(path: Path) -> str:
    head = path.read_bytes()[:512]
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith(b"\x1f\x8b") or head.startswith(b"BZh") or head[257:262] == b"ustar":
        return "tar"
    return "unknown"


def do_extract(archive_path: Path, plan: Dict[str, Any], dest_root: Path, cfg: Dict[str, Any]) -> List[str]:
    """Executa a extração revalidando a contenção de cada destino (defesa em profundidade)."""
    written: List[str] = []
    budget = int(cfg.get("max_uncompressed_bytes", 2097152000))
    consumed = 0
    dest_root.mkdir(parents=True, exist_ok=True)
    allowed = {entry["entry"] for entry in plan["entries"]}

    if plan["format"] == "zip":
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.is_dir() or info.filename not in allowed:
                    continue
                target, reason = safe_target(dest_root, info.filename)
                if reason != "OK" or target is None:
                    raise ValidationError(f"entrada recusada na extração ({reason}): {info.filename}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, open(target, "wb") as sink:
                    while True:
                        block = source.read(262144)
                        if not block:
                            break
                        consumed += len(block)
                        if consumed > budget:
                            raise ValidationError("limite de bytes descomprimidos excedido durante a extração.")
                        sink.write(block)
                written.append(str(target.resolve().relative_to(REPO_ROOT)).replace("\\", "/"))
    elif plan["format"] == "tar":
        with tarfile.open(archive_path, "r:*") as archive:
            for member in archive.getmembers():
                if not member.isfile() or member.name not in allowed:
                    continue
                target, reason = safe_target(dest_root, member.name)
                if reason != "OK" or target is None:
                    raise ValidationError(f"entrada recusada na extração ({reason}): {member.name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    continue
                with source, open(target, "wb") as sink:
                    while True:
                        block = source.read(262144)
                        if not block:
                            break
                        consumed += len(block)
                        if consumed > budget:
                            raise ValidationError("limite de bytes descomprimidos excedido durante a extração.")
                        sink.write(block)
                written.append(str(target.resolve().relative_to(REPO_ROOT)).replace("\\", "/"))
    else:
        raise ValidationError("formato de pacote não suportado para extração.")
    return written


def canonical_pipeline_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    pipeline_cfg = config.get("canonical_pipeline") or {}
    return {
        name: REPO_ROOT / str(rel)
        for name, rel in pipeline_cfg.items()
        if isinstance(rel, str) and rel.endswith(".py")
    }


def run_npz_stage(config: Dict[str, Any], dry_run: bool, logger) -> Dict[str, Any]:
    """
    Executa o extrator canônico DEM → NPZ sem modificar o pipeline.

    Compatibilidade real: `contract_spec.py` lê `CSBOT_PIPELINE_DIR` do ambiente
    (linhas 53–59) e deriva `RAW_DEMOS_DIR_D` e `EXTRACTED_TENSORS_DIR_D` a partir dele.
    """
    extractor = REPO_ROOT / str(
        (config.get("canonical_pipeline") or {}).get("dem_to_npz_extractor", "")
    )
    if not extractor.is_file():
        raise ValidationError(f"extrator canônico ausente: {extractor}")

    stage_root = REPO_ROOT / str((config.get("paths") or {}).get("root", ""))
    raw_dir = stage_root / "raw_demos"
    npz_out = stage_root / "extracted_tensors" / "de_mirage"
    processed_dir = REPO_ROOT / str((config.get("paths") or {}).get("processed_npz", ""))
    command = [sys.executable, str(extractor), "--map", "de_mirage"]
    result: Dict[str, Any] = {
        "extractor_repo_relative_path": str(extractor.relative_to(REPO_ROOT)).replace("\\", "/"),
        "extractor_modified": False,
        "pipeline_dir_env_var": "CSBOT_PIPELINE_DIR",
        "pipeline_dir_value": str(stage_root.resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
        "raw_demos_seen_by_pipeline": str(raw_dir.resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
        "npz_written_by_pipeline": str(npz_out.resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
        "npz_final_directory": str(processed_dir.resolve().relative_to(REPO_ROOT)).replace("\\", "/"),
        "command": command,
        "executed": False,
        "delete_after_extract": False,
        "note": (
            "O pipeline canônico é reutilizado via override de CSBOT_PIPELINE_DIR; nunca é editado. "
            "--delete-after-extract NUNCA é usado, para preservar a cadeia de custódia do .dem."
        ),
    }
    if dry_run:
        result["would_execute"] = True
        return result

    env = dict(os.environ)
    env["CSBOT_PIPELINE_DIR"] = str(stage_root)
    logger(f"executando extrator canônico: {' '.join(command)} (CSBOT_PIPELINE_DIR={stage_root})")
    completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=3600)
    result["executed"] = True
    result["returncode"] = completed.returncode
    result["stdout_tail"] = redact(completed.stdout[-2000:])
    result["stderr_tail"] = redact(completed.stderr[-2000:])
    if completed.returncode != 0:
        raise ValidationError(
            f"extrator canônico falhou (returncode {completed.returncode}): {redact(completed.stderr[-500:])}"
        )

    moved: List[str] = []
    if npz_out.is_dir():
        processed_dir.mkdir(parents=True, exist_ok=True)
        for npz_file in sorted(npz_out.glob("*.npz")):
            destination = processed_dir / npz_file.name
            npz_file.replace(destination)
            moved.append(str(destination.relative_to(REPO_ROOT)).replace("\\", "/"))
    result["npz_relocated"] = moved
    result["npz_relocated_count"] = len(moved)
    return result


def run_self_test() -> int:
    dest = (REPO_ROOT / "datasets" / "mirage_domains" / "intermediate_competitive" / "raw_demos").resolve()
    scenarios = [
        ("plain_demo_ok", "match.dem", "OK"),
        ("nested_demo_ok", "match/set1.dem", "OK"),
        ("traversal_blocked", "../../etc/evil.dem", "PARENT_TRAVERSAL"),
        ("posix_absolute_blocked", "/etc/evil.dem", "ABSOLUTE_PATH"),
        ("windows_absolute_blocked", "C:/windows/evil.dem", "WINDOWS_ABSOLUTE_PATH"),
        ("empty_blocked", "", "EMPTY_ENTRY_NAME"),
        ("dot_only_ok", "./match.dem", "OK"),
        ("traversal_hidden_in_middle_blocked", "a/../../b.dem", "PARENT_TRAVERSAL"),
    ]
    failures: List[str] = []
    results: List[Dict[str, Any]] = []
    for name, member, expected in scenarios:
        target, reason = safe_target(dest, member)
        ok = reason == expected
        results.append(
            {
                "case": name,
                "entry": member,
                "expected": expected,
                "actual": reason,
                "resolved_target": (
                    str(target.relative_to(dest)).replace("\\", "/") if target is not None and reason == "OK" else None
                ),
                "ok": ok,
            }
        )
        if not ok:
            failures.append(f"{name}: esperado {expected}, obtido {reason}")

    passed = len(results) - len(failures)
    print(
        json.dumps(
            {
                "self_test": "extract_demo.py",
                "generated_utc": utc_now(),
                "cases_total": len(results),
                "cases_passed": passed,
                "cases_failed": len(failures),
                "aggregation": f"({passed}/{len(results)})",
                "fixture_class": "TEST_FIXTURE_NOT_REAL_DATA",
                "files_written_to_disk": 0,
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
        prog="extract_demo.py",
        description=(
            "Extração segura de pacotes de demo (bloqueia traversal, caminho absoluto, symlink) e "
            "integração com o pipeline NPZ canônico via CSBOT_PIPELINE_DIR. Modo padrão: --dry-run."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação (ou self-test falho) | 2 erro de uso.",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Configuração (default: config.example.json).")
    parser.add_argument("--archive", default="", help="Pacote a extrair.")
    parser.add_argument("--dest", default="", help="Diretório de destino (default: raw_demos da config).")
    parser.add_argument("--run-npz", action="store_true", help="Após extrair, executar o extrator canônico DEM→NPZ.")
    parser.add_argument("--self-test", action="store_true", help="Executa 8 casos de contenção de caminho.")
    parser.add_argument("--out", default="", help="Grava o laudo em JSON.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(Padrão) planeja a extração; não escreve nada.")
    mode.add_argument("--execute", action="store_true", help="Executa a extração real.")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    archive_cfg = config.get("archive") or {}

    if args.self_test:
        return run_self_test()

    if not args.archive:
        print("ERRO de uso: informe --archive ou --self-test.", file=sys.stderr)
        return EXIT_USAGE

    archive_path = Path(args.archive)
    if not archive_path.is_absolute():
        archive_path = REPO_ROOT / archive_path
    if not archive_path.is_file():
        raise ValidationError(f"pacote ausente: {archive_path}")

    if args.dest:
        dest_root = Path(args.dest)
        if not dest_root.is_absolute():
            dest_root = REPO_ROOT / dest_root
    else:
        dest_root = REPO_ROOT / str((config.get("paths") or {}).get("raw_demos", ""))

    container = detect_container(archive_path)
    if container == "zip":
        plan = plan_zip(archive_path, dest_root, archive_cfg)
    elif container == "tar":
        plan = plan_tar(archive_path, dest_root, archive_cfg)
    else:
        raise ValidationError("formato de pacote não reconhecido (esperado zip ou tar/gz/bz2).")

    plan["archive_path"] = str(archive_path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    plan["archive_size_bytes"] = archive_path.stat().st_size
    plan["dest_root"] = str(dest_root.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    plan["mode"] = "EXECUTE" if args.execute else "DRY_RUN"
    plan["entries_total"] = len(plan["entries"])
    plan["entries_dem"] = len([e for e in plan["entries"] if e["is_dem"]])
    plan["rejected_count"] = len(plan["rejected_entries"])
    plan["safe_to_extract"] = plan["rejected_count"] == 0

    if plan["rejected_entries"]:
        plan["recommended_action"] = "MOVE_TO_QUARANTINE"
    else:
        plan["recommended_action"] = "PROCEED"

    if args.execute and plan["rejected_entries"]:
        raise ValidationError(
            "extração abortada: pacote contém entradas inseguras ("
            + ", ".join(f"{r['entry']}:{r['reason']}" for r in plan["rejected_entries"])
            + "). Mova o pacote para quarantine/."
        )

    if args.execute:
        plan["written_files"] = do_extract(archive_path, plan, dest_root, archive_cfg)
        plan["written_files_count"] = len(plan["written_files"])

    if args.run_npz:
        plan["npz_stage"] = run_npz_stage(
            config,
            dry_run=not args.execute,
            logger=lambda message: print(f"[extract_demo] {message}"),
        )
        if not args.execute:
            plan["npz_stage"]["npz_relocated_count"] = 0

    print(json.dumps(plan, indent=2, ensure_ascii=False))
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
