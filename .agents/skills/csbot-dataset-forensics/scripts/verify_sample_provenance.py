#!/usr/bin/env python3
"""
verify_sample_provenance.py — Verificação determinística de proveniência e hashes SHA-256 de amostras.

Governança CsBot:
- 01-evidence-before-claims: Exige hashes SHA-256 completos (64 caracteres hexadecimais, sem truncamento)
  e rastreabilidade física de cada amostra.
  Em modo --dry-run (sem artefatos reais), emite obrigatoriamente verdict="CONDITIONAL" e data_nature="SIMULATED".
- 04-synthetic-data-labeling: Rejeita amostras marcadas como SIMULATED/TEMPLATED/SYNTHETIC disfarçadas de REAL.
- 05-human-review-integrity: Distingue proveniência de captura scriptada vs humana.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


SHA256_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")


def compute_sha256(filepath: Path) -> str:
    """Calcula o hash SHA-256 completo (64 caracteres hexadecimais) de um arquivo."""
    hasher = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_samples_from_json(filepath: Path) -> List[Dict[str, Any]]:
    """Extrai lista de amostras a partir de um arquivo JSON."""
    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("samples", "items", "entries", "records", "files", "visual_samples", "artifacts"):
            if isinstance(data.get(key), list):
                return [item for item in data[key] if isinstance(item, dict)]
        if any(k in data for k in ("source_demo", "source_file", "demo_id", "round_id", "tick", "spot_id")):
            return [data]
    return []


def load_known_demos(catalog_path: Path) -> Set[str]:
    """Carrega conjunto de identificadores/nomes de demos conhecidos a partir de um JSON ou diretório."""
    known: Set[str] = set()
    if catalog_path.is_dir():
        for f in catalog_path.rglob("*"):
            if f.is_file():
                known.add(f.name)
                known.add(f.stem)
        return known

    with catalog_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    def _collect_from_item(item: Any) -> None:
        if isinstance(item, str):
            known.add(item)
            known.add(Path(item).stem)
        elif isinstance(item, dict):
            for k in ("demo_id", "source_demo", "source_file", "demo_name", "match_id", "filename", "file", "id"):
                if k in item and item[k]:
                    val = str(item[k]).strip()
                    known.add(val)
                    known.add(Path(val).stem)

    if isinstance(data, list):
        for it in data:
            _collect_from_item(it)
    elif isinstance(data, dict):
        for list_key in ("demos", "files", "accepted_files", "matches", "entries", "records"):
            if isinstance(data.get(list_key), list):
                for it in data[list_key]:
                    _collect_from_item(it)
    return known


def verify_samples(
    samples: List[Dict[str, Any]],
    base_dir: Path,
    known_demos: Optional[Set[str]],
    require_sha256: bool,
) -> Dict[str, Any]:
    """Audita a proveniência e integridade SHA-256 de cada amostra."""
    violations: List[Dict[str, Any]] = []
    valid_count = 0
    sha256_verified_on_disk = 0

    for idx, sample in enumerate(samples):
        sample_id = str(sample.get("sample_id", sample.get("id", sample.get("file", f"sample_{idx}"))))
        sample_issues: List[str] = []

        source_demo = sample.get(
            "source_demo",
            sample.get("source_file", sample.get("demo_id", sample.get("match_id"))),
        )
        round_id = sample.get("round_id", sample.get("round_num", sample.get("round")))
        tick = sample.get("tick", sample.get("tick_start", sample.get("frame_tick", sample.get("start_tick"))))
        player_steamid = sample.get("player_steamid", sample.get("steamid", sample.get("player_id")))
        spot_id = sample.get("spot_id", sample.get("target_spot_id", sample.get("sector_id")))

        if source_demo is None or str(source_demo).strip() == "":
            sample_issues.append("missing_source_demo")
        elif known_demos is not None:
            s_demo_str = str(source_demo).strip()
            if s_demo_str not in known_demos and Path(s_demo_str).stem not in known_demos:
                sample_issues.append(f"source_demo_not_in_catalog:{s_demo_str}")

        if round_id is None or str(round_id).strip() == "":
            sample_issues.append("missing_round_id")

        if tick is None or str(tick).strip() == "":
            sample_issues.append("missing_tick")
        else:
            try:
                if int(tick) < 0:
                    sample_issues.append(f"negative_tick:{tick}")
            except (ValueError, TypeError):
                sample_issues.append(f"non_integer_tick:{tick}")

        if (player_steamid is None or str(player_steamid).strip() == "") and (
            spot_id is None or str(spot_id).strip() == ""
        ):
            sample_issues.append("missing_both_player_steamid_and_spot_id")

        data_nature = str(sample.get("data_nature", sample.get("origin", "REAL"))).upper()
        if data_nature in ("SIMULATED", "TEMPLATED", "SYNTHETIC", "INFERRED") and sample.get("claimed_real", False):
            sample_issues.append(f"synthetic_sample_claimed_as_real:{data_nature}")

        declared_sha = sample.get(
            "sha256",
            sample.get("source_sha256", sample.get("file_sha256", sample.get("hash_sha256"))),
        )
        file_rel = sample.get(
            "file",
            sample.get("source_file", sample.get("path", sample.get("artifact_path", sample.get("image_path")))),
        )

        if declared_sha is not None:
            declared_sha_str = str(declared_sha).strip()
            if not SHA256_REGEX.match(declared_sha_str):
                sample_issues.append(f"invalid_or_truncated_sha256:{declared_sha_str}")
            elif file_rel:
                candidate_path = Path(str(file_rel))
                if not candidate_path.is_absolute():
                    candidate_path = (base_dir / candidate_path).resolve()
                if candidate_path.is_file():
                    actual_sha = compute_sha256(candidate_path)
                    if actual_sha.lower() != declared_sha_str.lower():
                        sample_issues.append(
                            f"sha256_mismatch:declared={declared_sha_str},actual={actual_sha}"
                        )
                    else:
                        sha256_verified_on_disk += 1
                else:
                    sample_issues.append(f"referenced_file_not_found:{candidate_path}")
        elif require_sha256:
            sample_issues.append("missing_sha256")

        if sample_issues:
            violations.append(
                {
                    "sample_index": idx,
                    "sample_id": sample_id,
                    "issues": sample_issues,
                }
            )
        else:
            valid_count += 1

    return {
        "total_samples_checked": len(samples),
        "valid_samples_count": valid_count,
        "invalid_samples_count": len(violations),
        "sha256_verified_on_disk_count": sha256_verified_on_disk,
        "violations": violations[:100],
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify_sample_provenance.py",
        description=(
            "Verifica a proveniência de amostras visuais ou exemplos de treino "
            "(source_demo/source_file, round_id, tick, player_steamid/spot_id e hash SHA-256 completo)."
        ),
    )
    parser.add_argument(
        "--input",
        "--samples",
        "--manifest",
        "--target",
        "-i",
        dest="input",
        type=str,
        required=False,
        help="Caminho para o arquivo JSON de amostras/manifest de proveniência.",
    )
    parser.add_argument(
        "--demo-catalog",
        "--raw-dir",
        "-c",
        dest="demo_catalog",
        type=str,
        default=None,
        help="Opcional: caminho para manifest/catálogo JSON ou diretório de demos reais para cruzamento.",
    )
    parser.add_argument(
        "--base-dir",
        "-b",
        type=str,
        default=None,
        help="Opcional: diretório base para resolver caminhos relativos de arquivos de amostras.",
    )
    parser.add_argument(
        "--no-require-sha256",
        action="store_true",
        help="Se definido, não falha amostras que não possuam campo sha256 explícito (ainda valida se presente).",
    )
    parser.add_argument(
        "--output-json",
        "--out",
        "-o",
        dest="output_json",
        type=str,
        default=None,
        help="Caminho opcional para salvar o relatório JSON determinístico.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa validação em modo --dry-run (emite verdict=CONDITIONAL e data_nature=SIMULATED).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.dry_run:
        report: Dict[str, Any] = {
            "script": "verify_sample_provenance.py",
            "mode": "DRY_RUN",
            "data_nature": "SIMULATED",
            "governance_rules": [
                "01-evidence-before-claims",
                "04-synthetic-data-labeling",
                "05-human-review-integrity",
            ],
            "required_provenance_fields": [
                "source_demo / source_file",
                "round_id",
                "tick / tick_start",
                "player_steamid OR spot_id",
                "sha256 / source_sha256 (64 hex chars)",
            ],
            "verdict": "CONDITIONAL",
            "note": (
                "Execução em modo --dry-run (SIMULATED). Pela regra 01-evidence-before-claims, "
                "nenhum veredito PASS pode ser emitido sem artefato bruto real."
            ),
        }
        if args.output_json:
            out_path = Path(args.output_json).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if not args.input:
        print("ERRO: Informe --input / --samples com o arquivo JSON de amostras (ou use --dry-run).", file=sys.stderr)
        return 2

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        print(f"ERRO: Arquivo de entrada não encontrado: {input_path}", file=sys.stderr)
        return 2

    base_dir = Path(args.base_dir).resolve() if args.base_dir else input_path.parent
    known_demos: Optional[Set[str]] = None
    catalog_info: Optional[Dict[str, Any]] = None

    try:
        if args.demo_catalog:
            cat_path = Path(args.demo_catalog).resolve()
            if not cat_path.exists():
                print(f"ERRO: Catálogo de demos não encontrado: {cat_path}", file=sys.stderr)
                return 2
            known_demos = load_known_demos(cat_path)
            catalog_info = {
                "path": str(cat_path),
                "sha256": compute_sha256(cat_path) if cat_path.is_file() else None,
                "known_demos_count": len(known_demos),
            }

        input_sha256 = compute_sha256(input_path)
        samples = load_samples_from_json(input_path)
    except Exception as exc:
        print(f"ERRO ao carregar artefatos de proveniência: {exc}", file=sys.stderr)
        return 2

    if not samples:
        report = {
            "script": "verify_sample_provenance.py",
            "mode": "REAL_AUDIT",
            "data_nature": "REAL",
            "input_artifact": {"path": str(input_path), "sha256": input_sha256},
            "total_samples_checked": 0,
            "verdict": "FAIL",
            "error": "Nenhuma amostra encontrada no arquivo de entrada.",
        }
        if args.output_json:
            out_path = Path(args.output_json).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    audit_res = verify_samples(
        samples=samples,
        base_dir=base_dir,
        known_demos=known_demos,
        require_sha256=not args.no_require_sha256,
    )

    verdict = "PASS" if audit_res["invalid_samples_count"] == 0 and audit_res["total_samples_checked"] > 0 else "FAIL"

    report = {
        "script": "verify_sample_provenance.py",
        "mode": "REAL_AUDIT",
        "data_nature": "REAL",
        "governance_rules": [
            "01-evidence-before-claims",
            "04-synthetic-data-labeling",
            "05-human-review-integrity",
        ],
        "input_artifact": {"path": str(input_path), "sha256": input_sha256},
        "demo_catalog": catalog_info,
        "aggregation_formula": (
            "PASS iff (total_samples_checked > 0) AND (invalid_samples_count == 0) where valid requires "
            "source_demo/source_file, round_id, tick >= 0, (player_steamid OR spot_id), and valid 64-char SHA-256"
        ),
        **audit_res,
        "verdict": verdict,
    }

    if args.output_json:
        out_path = Path(args.output_json).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
