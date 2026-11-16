#!/usr/bin/env python3
"""
detect_templated_outputs.py — Detecção forense de dados templados, placeholders ou repetição sintética.

Governança CsBot:
- 01-evidence-before-claims: Registra caminho exato e hash SHA-256 completo dos arquivos inspecionados.
  Em modo --dry-run (sem artefatos reais), emite obrigatoriamente verdict="CONDITIONAL" e data_nature="SIMULATED".
- 04-synthetic-data-labeling: Detecta dados sintéticos, simulados, templados ou interpolados que não
  estejam explicitamente rotulados como `SIMULATED`, `TEMPLATED`, `SYNTHETIC` ou `INFERRED`.

Padrões detectados (dataset_forensics_protocol.md Seção 5):
1. Strings de placeholder (`TODO`, `TBD`, `PLACEHOLDER`, `DUMMY`, `MOCK_DATA`, `FAKE_DATA`, `lorem ipsum`).
2. Hashes SHA-256 truncados ou forjados (`00000000...`, `deadbeef...`, `12345678...`, `abcdef...`).
3. Taxa de colisão e variância zero em canais dinâmicos (coordenadas, velocidade, viewangles) ou passo linear
   aritmético constante (Delta_x = c, Delta_y = c).
4. Padrões ciclicamente repetidos em sequências de labels (`A -> B -> C -> A -> B -> C`) ou carimbos textuais.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER\b", re.IGNORECASE),
    re.compile(r"\bDUMMY\b", re.IGNORECASE),
    re.compile(r"\bMOCK_DATA\b", re.IGNORECASE),
    re.compile(r"\bFAKE_DATA\b", re.IGNORECASE),
    re.compile(r"\bLOREM\s+IPSUM\b", re.IGNORECASE),
    re.compile(r"<insert[\s_-]?[^>]*>", re.IGNORECASE),
    re.compile(r"\{\{[^{}]+\}\}"),
]

FAKE_HASH_PATTERNS = [
    re.compile(r"^0{16,64}$"),
    re.compile(r"^f{16,64}$", re.IGNORECASE),
    re.compile(r"^(deadbeef)+", re.IGNORECASE),
    re.compile(r"^(12345678)+"),
    re.compile(r"^[0-9a-fA-F]{7,12}\.\.\.$"),
]

SYNTHETIC_LABELS = {"SIMULATED", "TEMPLATED", "SYNTHETIC", "INFERRED"}


def compute_sha256(filepath: Path) -> str:
    """Calcula o hash SHA-256 completo (64 caracteres hexadecimais) de um arquivo."""
    hasher = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def has_explicit_synthetic_label(content_or_obj: Any) -> bool:
    """Verifica se o objeto ou texto já declara explicitamente etiqueta de dado sintético."""
    if isinstance(content_or_obj, dict):
        for k in ("data_nature", "origin", "nature", "source_type", "label_origin", "classification"):
            val = str(content_or_obj.get(k, "")).strip().upper()
            if val in SYNTHETIC_LABELS:
                return True
    elif isinstance(content_or_obj, str):
        upper = content_or_obj.upper()
        for label in SYNTHETIC_LABELS:
            if f"DATA_NATURE: {label}" in upper or f'"DATA_NATURE": "{label}"' in upper:
                return True
    return False


def scan_numeric_series(name: str, values: List[float], min_len: int = 10) -> List[Dict[str, Any]]:
    """Analisa uma série numérica em busca de variância zero ou passo linear artificial constante."""
    anomalies: List[Dict[str, Any]] = []
    clean_vals = [float(v) for v in values if v is not None]
    if len(clean_vals) < min_len:
        return anomalies

    variance = statistics.pvariance(clean_vals)
    if variance == 0.0:
        anomalies.append(
            {
                "type": "zero_variance_numeric_series",
                "field": name,
                "sample_count": len(clean_vals),
                "constant_value": clean_vals[0],
                "reason": "Variância exatamente zero em série numérica contínua/coordenada.",
            }
        )
        return anomalies

    diffs = [round(clean_vals[i + 1] - clean_vals[i], 6) for i in range(len(clean_vals) - 1)]
    if len(diffs) >= min_len and len(set(diffs)) == 1 and diffs[0] != 0.0:
        anomalies.append(
            {
                "type": "perfect_linear_interpolation_series",
                "field": name,
                "sample_count": len(clean_vals),
                "constant_step": diffs[0],
                "reason": "Série numérica com passo constante perfeito (interpolação sintética).",
            }
        )
    return anomalies


def scan_cyclic_label_pattern(field: str, labels: List[str], min_len: int = 12) -> List[Dict[str, Any]]:
    """Detecta sequências ciclicamente repetidas (ex: A -> B -> C -> A -> B -> C) sem variação orgânica."""
    if len(labels) < min_len or len(set(labels)) < 2:
        return []
    for period in range(2, min(8, len(labels) // 3 + 1)):
        pattern = labels[:period]
        matches = all(labels[i] == pattern[i % period] for i in range(len(labels)))
        if matches:
            return [
                {
                    "type": "cyclic_periodic_label_sequence",
                    "field": field,
                    "period": period,
                    "repeated_pattern": pattern,
                    "sequence_length": len(labels),
                    "reason": "Sequência de labels repete exatamente um ciclo periódico sintético.",
                }
            ]
    return []


def audit_json_file(filepath: Path, repetition_threshold: int) -> List[Dict[str, Any]]:
    """Inspeciona um arquivo JSON em busca de placeholders, hashes falsos, repetição e variância zero."""
    findings: List[Dict[str, Any]] = []
    raw_text = filepath.read_text(encoding="utf-8", errors="replace")
    data = json.loads(raw_text)
    explicitly_labeled = has_explicit_synthetic_label(data)

    for pat in PLACEHOLDER_PATTERNS:
        match = pat.search(raw_text)
        if match and not explicitly_labeled:
            findings.append(
                {
                    "type": "unlabeled_placeholder_string",
                    "pattern": pat.pattern,
                    "matched_text": match.group(0),
                }
            )

    records: List[Dict[str, Any]] = []
    if isinstance(data, list):
        records = [r for r in data if isinstance(r, dict)]
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                records.extend([r for r in v if isinstance(r, dict)])

    if records and not explicitly_labeled:
        for coord_col in ("x", "y", "z", "pos_x", "pos_y", "pos_z", "vx", "vy", "vz", "yaw", "pitch", "loss", "val_loss", "accuracy"):
            series = [r[coord_col] for r in records if coord_col in r and isinstance(r[coord_col], (int, float))]
            findings.extend(scan_numeric_series(coord_col, series))

        for label_col in ("PositioningState", "positioning_state", "NextSector", "next_sector", "SpotId", "spot_id"):
            lbl_series = [str(r[label_col]) for r in records if label_col in r and r[label_col] is not None]
            findings.extend(scan_cyclic_label_pattern(label_col, lbl_series))

        for text_col in ("note", "description", "rationale", "comment", "justification", "diagnosis"):
            texts = [str(r[text_col]).strip() for r in records if text_col in r and r[text_col]]
            counts = Counter(texts)
            for txt, count in counts.items():
                if count >= repetition_threshold and len(txt) > 15:
                    findings.append(
                        {
                            "type": "templated_repeated_text_stamp",
                            "field": text_col,
                            "repetition_count": count,
                            "sample_text": txt[:120],
                        }
                    )

        for r in records:
            for hk in ("sha256", "file_sha256", "source_sha256", "hash"):
                if hk in r and r[hk]:
                    hval = str(r[hk]).strip()
                    for fpat in FAKE_HASH_PATTERNS:
                        if fpat.match(hval):
                            findings.append(
                                {
                                    "type": "forged_or_truncated_hash",
                                    "field": hk,
                                    "value": hval,
                                }
                            )
    return findings


def audit_markdown_or_text_file(filepath: Path) -> List[Dict[str, Any]]:
    """Inspeciona relatórios Markdown/texto em busca de placeholders e templates não rotulados."""
    findings: List[Dict[str, Any]] = []
    raw_text = filepath.read_text(encoding="utf-8", errors="replace")
    explicitly_labeled = has_explicit_synthetic_label(raw_text)

    if not explicitly_labeled:
        for pat in PLACEHOLDER_PATTERNS:
            for match in pat.finditer(raw_text):
                findings.append(
                    {
                        "type": "unlabeled_placeholder_in_document",
                        "pattern": pat.pattern,
                        "matched_text": match.group(0),
                    }
                )
    return findings


def audit_parquet_or_npz_file(filepath: Path) -> List[Dict[str, Any]]:
    """Verifica variância zero suspeita ou interpolação linear em coordenadas de Parquet ou NPZ."""
    findings: List[Dict[str, Any]] = []
    suffix = filepath.suffix.lower()

    if suffix == ".npz":
        import numpy as np  # type: ignore

        with np.load(filepath, allow_pickle=False) as npz:
            for col in ("x", "y", "z", "pos_x", "pos_y", "pos_z", "vx", "vy", "vz", "yaw", "pitch"):
                if col in npz.files and npz[col].ndim == 1 and len(npz[col]) >= 10:
                    vals = [float(v) for v in npz[col].tolist()]
                    findings.extend(scan_numeric_series(col, vals))
    elif suffix == ".parquet":
        try:
            import pyarrow.parquet as pq  # type: ignore

            table = pq.read_table(filepath)
            for col in ("x", "y", "z", "pos_x", "pos_y", "pos_z", "vx", "vy", "vz", "yaw", "pitch"):
                if col in table.column_names and table.num_rows >= 10:
                    vals = [float(v) for v in table.column(col).to_pylist() if v is not None]
                    findings.extend(scan_numeric_series(col, vals))
        except ImportError:
            import pandas as pd  # type: ignore

            df = pd.read_parquet(filepath)
            for col in ("x", "y", "z", "pos_x", "pos_y", "pos_z", "vx", "vy", "vz", "yaw", "pitch"):
                if col in df.columns and len(df) >= 10:
                    vals = [float(v) for v in df[col].dropna().tolist()]
                    findings.extend(scan_numeric_series(col, vals))
    return findings


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="detect_templated_outputs.py",
        description=(
            "Detecta labels, coordenadas, curvas ou relatórios gerados por templates ou repetição "
            "sintética artificial não rotulada como TEMPLATED/SYNTHETIC/SIMULATED."
        ),
    )
    parser.add_argument(
        "--input",
        "--target",
        "--manifest",
        "--parquet-dir",
        "--npz-dir",
        "--raw-dir",
        "-i",
        dest="input",
        type=str,
        required=False,
        help="Caminho para arquivo (.json, .md, .parquet, .npz) ou diretório a ser auditado.",
    )
    parser.add_argument(
        "--repetition-threshold",
        type=int,
        default=5,
        help="Número mínimo de repetições idênticas de carimbo textual para acionar alerta (padrão: 5).",
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
            "script": "detect_templated_outputs.py",
            "mode": "DRY_RUN",
            "data_nature": "SIMULATED",
            "governance_rules": [
                "01-evidence-before-claims",
                "04-synthetic-data-labeling",
            ],
            "templated_detected": False,
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
        print("ERRO: Informe --input / --target com o arquivo ou diretório a inspecionar (ou use --dry-run).", file=sys.stderr)
        return 2

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"ERRO: Caminho não encontrado: {in_path}", file=sys.stderr)
        return 2

    target_files: List[Path] = []
    if in_path.is_file():
        target_files.append(in_path)
    else:
        for f in sorted(in_path.rglob("*")):
            if f.is_file() and f.suffix.lower() in (".json", ".md", ".txt", ".parquet", ".npz"):
                target_files.append(f)

    if not target_files:
        print(f"ERRO: Nenhum arquivo suportado encontrado em: {in_path}", file=sys.stderr)
        return 1

    file_results: List[Dict[str, Any]] = []
    total_anomalies = 0

    try:
        for fpath in target_files:
            sha = compute_sha256(fpath)
            suf = fpath.suffix.lower()
            if suf == ".json":
                anomalies = audit_json_file(fpath, args.repetition_threshold)
            elif suf in (".md", ".txt"):
                anomalies = audit_markdown_or_text_file(fpath)
            elif suf in (".parquet", ".npz"):
                anomalies = audit_parquet_or_npz_file(fpath)
            else:
                anomalies = []

            total_anomalies += len(anomalies)
            file_results.append(
                {
                    "path": str(fpath),
                    "sha256": sha,
                    "anomaly_count": len(anomalies),
                    "anomalies": anomalies,
                }
            )
    except Exception as exc:
        print(f"ERRO durante inspeção de dados templados: {exc}", file=sys.stderr)
        return 2

    templated_detected = total_anomalies > 0
    verdict = "FAIL" if templated_detected else "PASS"

    report = {
        "script": "detect_templated_outputs.py",
        "mode": "REAL_AUDIT",
        "data_nature": "REAL",
        "governance_rules": [
            "01-evidence-before-claims",
            "04-synthetic-data-labeling",
        ],
        "files_inspected_count": len(file_results),
        "total_anomalies_count": total_anomalies,
        "templated_detected": templated_detected,
        "aggregation_formula": (
            "PASS iff total_anomalies_count == 0 across all inspected files "
            "(no unlabeled placeholders, zero-variance coordinate series, cyclic synthetic labels, or forged hashes)"
        ),
        "files": file_results,
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
