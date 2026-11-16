#!/usr/bin/env python3
"""
audit_parquet_rows.py — Auditoria forense de arquivos Parquet, NPZ e sequências do dataset CsBot.

Governança CsBot:
- 01-evidence-before-claims: Registra caminho exato, hash SHA-256 completo e contagem real de linhas.
  Em modo --dry-run (sem artefatos reais), emite obrigatoriamente verdict="CONDITIONAL" e data_nature="SIMULATED".
- 04-synthetic-data-labeling: Identifica modo REAL vs SIMULATED.

Verificações realizadas:
1. Contagem real de linhas (> 0) e presença de colunas obrigatórias.
2. Ausência de valores NaN, +Inf, -Inf ou null em colunas obrigatórias.
3. Coordenadas espaciais (x, y, z) dentro do bounding box de de_mirage:
   - X in [-3400.0, 1900.0]
   - Y in [-3600.0, 1000.0]
   - Z in [-500.0, 1000.0]
4. Monotonicidade de `tick` dentro de cada sequência `(demo_id, round_id, player_steamid)`.
5. Alinhamento cardinal 1:1 entre registros `.parquet` e dimensão N (axis 0) dos arrays em `.npz` (`--npz-dir`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_REQUIRED_COLUMNS = (
    "demo_id",
    "round_id",
    "tick",
    "x",
    "y",
    "z",
)

MIRAGE_BOUNDS = {
    "x": (-3400.0, 1900.0),
    "y": (-3600.0, 1000.0),
    "z": (-500.0, 1000.0),
}


def compute_sha256(filepath: Path) -> str:
    """Calcula o hash SHA-256 completo (64 caracteres hexadecimais) de um arquivo."""
    hasher = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_parquet_records(filepath: Path) -> Tuple[List[str], List[Dict[str, Any]], str]:
    """Lê colunas e linhas de um arquivo Parquet via pyarrow ou pandas."""
    try:
        import pyarrow.parquet as pq  # type: ignore

        table = pq.read_table(filepath)
        cols = list(table.column_names)
        rows = table.to_pylist()
        return cols, rows, "pyarrow"
    except ImportError:
        pass

    try:
        import pandas as pd  # type: ignore

        df = pd.read_parquet(filepath)
        cols = [str(c) for c in df.columns]
        rows = df.to_dict(orient="records")
        return cols, rows, "pandas"
    except ImportError as exc:
        raise RuntimeError(
            "Nem 'pyarrow' nem 'pandas' estão instalados no ambiente Python para leitura real de Parquet."
        ) from exc


def is_null_or_nan(val: Any) -> bool:
    """Verifica se um valor é None, NaN ou Inf."""
    if val is None:
        return True
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return True
    return False


def resolve_coord(row: Dict[str, Any], axis: str) -> Optional[float]:
    """Busca coordenada x, y ou z em nomes de colunas usuais."""
    candidates = {
        "x": ("x", "pos_x", "player_x", "position_x"),
        "y": ("y", "pos_y", "player_y", "position_y"),
        "z": ("z", "pos_z", "player_z", "position_z"),
    }[axis]
    for c in candidates:
        if c in row:
            val = row[c]
            if is_null_or_nan(val):
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
    return None


def audit_npz_alignment(parquet_files: List[Path], npz_dir: Path) -> Dict[str, Any]:
    """
    Verifica alinhamento cardinal 1:1 entre arquivos .parquet e arrays .npz (axis 0)
    e sanidade numérica (ausência de NaN/Inf nos tensores NPZ).
    """
    import numpy as np  # type: ignore

    npz_files = sorted(npz_dir.rglob("*.npz")) if npz_dir.is_dir() else ([npz_dir] if npz_dir.is_file() else [])
    npz_by_stem = {f.stem: f for f in npz_files}

    mismatches: List[Dict[str, Any]] = []
    npz_details: List[Dict[str, Any]] = []
    total_npz_rows = 0

    for nf in npz_files:
        sha = compute_sha256(nf)
        with np.load(nf, allow_pickle=False) as npz:
            shapes = {k: list(npz[k].shape) for k in npz.files}
            axis0_set = {npz[k].shape[0] for k in npz.files if npz[k].ndim >= 1}
            nan_inf_keys: List[str] = []
            for k in npz.files:
                arr = npz[k]
                if np.issubdtype(arr.dtype, np.floating):
                    if not np.all(np.isfinite(arr)):
                        nan_inf_keys.append(k)

            n_axis0 = next(iter(axis0_set)) if len(axis0_set) == 1 else -1
            if n_axis0 > 0:
                total_npz_rows += n_axis0

            if len(axis0_set) > 1:
                mismatches.append(
                    {
                        "type": "internal_npz_axis0_mismatch",
                        "npz_path": str(nf.resolve()),
                        "shapes": shapes,
                    }
                )
            if nan_inf_keys:
                mismatches.append(
                    {
                        "type": "npz_nan_or_inf_detected",
                        "npz_path": str(nf.resolve()),
                        "keys_with_nan_or_inf": nan_inf_keys,
                    }
                )
            npz_details.append(
                {
                    "path": str(nf.resolve()),
                    "sha256": sha,
                    "axis0_count": n_axis0,
                    "shapes": shapes,
                    "nan_or_inf_keys": nan_inf_keys,
                }
            )

    return {
        "npz_files_count": len(npz_files),
        "total_npz_axis0_rows": total_npz_rows,
        "npz_by_stem": {k: str(v.resolve()) for k, v in npz_by_stem.items()},
        "npz_files_audited": npz_details,
        "alignment_mismatches": mismatches,
    }


def audit_single_parquet(
    filepath: Path,
    required_cols: List[str],
    bounds: Dict[str, Tuple[float, float]],
    strict_tick_increasing: bool,
) -> Dict[str, Any]:
    """Audita um único arquivo Parquet e retorna diagnóstico detalhado."""
    sha256_hex = compute_sha256(filepath)
    columns, rows, engine = load_parquet_records(filepath)
    row_count = len(rows)

    missing_columns = [c for c in required_cols if c not in columns]
    null_counts: Dict[str, int] = {c: 0 for c in required_cols if c in columns}
    out_of_bounds_counts: Dict[str, int] = {"x": 0, "y": 0, "z": 0}
    out_of_bounds_examples: List[Dict[str, Any]] = []
    monotonicity_violations: List[Dict[str, Any]] = []

    last_tick_by_seq: Dict[Tuple[str, str, str], int] = {}

    for idx, row in enumerate(rows):
        for col in null_counts:
            if is_null_or_nan(row.get(col)):
                null_counts[col] += 1

        for axis in ("x", "y", "z"):
            val = resolve_coord(row, axis)
            if val is not None:
                low, high = bounds[axis]
                if val < low or val > high:
                    out_of_bounds_counts[axis] += 1
                    if len(out_of_bounds_examples) < 20:
                        out_of_bounds_examples.append(
                            {
                                "row_index": idx,
                                "axis": axis,
                                "value": val,
                                "allowed_range": [low, high],
                            }
                        )

        tick_val = row.get("tick")
        if not is_null_or_nan(tick_val):
            try:
                current_tick = int(tick_val)
                demo_id = str(row.get("demo_id", row.get("match_id", "default_demo")))
                round_id = str(row.get("round_id", "default_round"))
                player_id = str(
                    row.get(
                        "player_steamid",
                        row.get("steamid", row.get("player_id", row.get("sequence_id", "default_player"))),
                    )
                )
                seq_key = (demo_id, round_id, player_id)
                if seq_key in last_tick_by_seq:
                    prev_tick = last_tick_by_seq[seq_key]
                    violated = (
                        (current_tick <= prev_tick)
                        if strict_tick_increasing
                        else (current_tick < prev_tick)
                    )
                    if violated:
                        if len(monotonicity_violations) < 25:
                            monotonicity_violations.append(
                                {
                                    "row_index": idx,
                                    "sequence_key": {
                                        "demo_id": demo_id,
                                        "round_id": round_id,
                                        "player_id": player_id,
                                    },
                                    "previous_tick": prev_tick,
                                    "current_tick": current_tick,
                                }
                            )
                last_tick_by_seq[seq_key] = current_tick
            except (ValueError, TypeError):
                pass

    total_nulls = sum(null_counts.values())
    total_oob = sum(out_of_bounds_counts.values())
    total_mono_violations = len(monotonicity_violations)

    file_passed = (
        row_count > 0
        and len(missing_columns) == 0
        and total_nulls == 0
        and total_oob == 0
        and total_mono_violations == 0
    )

    return {
        "path": str(filepath.resolve()),
        "sha256": sha256_hex,
        "engine": engine,
        "row_count": row_count,
        "columns_present": columns,
        "missing_required_columns": missing_columns,
        "null_or_nan_counts": null_counts,
        "total_null_or_nan": total_nulls,
        "mirage_bounds_applied": {k: list(v) for k, v in bounds.items()},
        "out_of_bounds_counts": out_of_bounds_counts,
        "out_of_bounds_examples": out_of_bounds_examples,
        "sequences_checked": len(last_tick_by_seq),
        "tick_monotonicity_violations_count": total_mono_violations,
        "tick_monotonicity_violation_examples": monotonicity_violations,
        "file_verdict": "PASS" if file_passed else "FAIL",
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="audit_parquet_rows.py",
        description=(
            "Audita arquivos Parquet e NPZ verificando contagem real de linhas, colunas obrigatórias, "
            "NaN/Inf/nulls, limites espaciais de de_mirage, monotonicidade de ticks e alinhamento cardinal Parquet <-> NPZ."
        ),
    )
    parser.add_argument(
        "--input",
        "--parquet-dir",
        "--manifest",
        "--target",
        "-i",
        dest="input",
        type=str,
        required=False,
        help="Caminho para um arquivo .parquet ou diretório contendo arquivos .parquet.",
    )
    parser.add_argument(
        "--npz-dir",
        type=str,
        default=None,
        help="Opcional: caminho para arquivo .npz ou diretório .npz para validar alinhamento cardinal 1:1 com Parquet.",
    )
    parser.add_argument(
        "--required-columns",
        type=str,
        default=",".join(DEFAULT_REQUIRED_COLUMNS),
        help=f"Lista de colunas obrigatórias separadas por vírgula (padrão: {','.join(DEFAULT_REQUIRED_COLUMNS)}).",
    )
    parser.add_argument(
        "--strict-tick-increasing",
        action="store_true",
        help="Exige tick[i] > tick[i-1] estrito dentro de cada sequência (padrão: tick[i] >= tick[i-1]).",
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
        help="Executa validação de configuração em modo --dry-run (emite verdict=CONDITIONAL e data_nature=SIMULATED).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    req_cols = [c.strip() for c in args.required_columns.split(",") if c.strip()]

    if args.dry_run:
        report: Dict[str, Any] = {
            "script": "audit_parquet_rows.py",
            "mode": "DRY_RUN",
            "data_nature": "SIMULATED",
            "governance_rules": [
                "01-evidence-before-claims",
                "04-synthetic-data-labeling",
            ],
            "required_columns": req_cols,
            "mirage_bounds": {k: list(v) for k, v in MIRAGE_BOUNDS.items()},
            "files_audited": [],
            "npz_cardinal_alignment": None,
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
        print("ERRO: Informe --input / --parquet-dir com o arquivo ou diretório Parquet (ou use --dry-run).", file=sys.stderr)
        return 2

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"ERRO: Caminho não encontrado: {in_path}", file=sys.stderr)
        return 2

    parquet_files: List[Path] = []
    if in_path.is_file():
        parquet_files.append(in_path)
    else:
        parquet_files.extend(sorted(in_path.rglob("*.parquet")))

    if not parquet_files:
        print(f"ERRO: Nenhum arquivo .parquet encontrado em: {in_path}", file=sys.stderr)
        return 1

    file_reports: List[Dict[str, Any]] = []
    npz_alignment_report: Optional[Dict[str, Any]] = None

    try:
        for pf in parquet_files:
            file_reports.append(
                audit_single_parquet(
                    pf,
                    required_cols=req_cols,
                    bounds=MIRAGE_BOUNDS,
                    strict_tick_increasing=args.strict_tick_increasing,
                )
            )
        total_rows = sum(r["row_count"] for r in file_reports)

        if args.npz_dir:
            npz_path = Path(args.npz_dir).resolve()
            if not npz_path.exists():
                print(f"ERRO: Caminho --npz-dir não encontrado: {npz_path}", file=sys.stderr)
                return 2
            npz_alignment_report = audit_npz_alignment(parquet_files, npz_path)
            if npz_alignment_report["total_npz_axis0_rows"] != total_rows:
                npz_alignment_report["alignment_mismatches"].append(
                    {
                        "type": "parquet_vs_npz_total_row_count_mismatch",
                        "parquet_total_rows": total_rows,
                        "npz_total_axis0_rows": npz_alignment_report["total_npz_axis0_rows"],
                    }
                )
    except Exception as exc:
        print(f"ERRO durante auditoria de Parquet/NPZ: {exc}", file=sys.stderr)
        return 2

    failed_files = [r["path"] for r in file_reports if r["file_verdict"] != "PASS"]
    npz_mismatches = len(npz_alignment_report["alignment_mismatches"]) if npz_alignment_report else 0
    verdict = "PASS" if (len(failed_files) == 0 and total_rows > 0 and npz_mismatches == 0) else "FAIL"

    report = {
        "script": "audit_parquet_rows.py",
        "mode": "REAL_AUDIT",
        "data_nature": "REAL",
        "governance_rules": [
            "01-evidence-before-claims",
            "04-synthetic-data-labeling",
        ],
        "total_files_audited": len(file_reports),
        "total_rows_audited": total_rows,
        "failed_files_count": len(failed_files),
        "npz_cardinal_alignment": npz_alignment_report,
        "aggregation_formula": (
            "PASS iff all files have (row_count > 0 AND missing_required_columns == 0 "
            "AND total_null_or_nan == 0 AND out_of_bounds == 0 AND tick_monotonicity_violations == 0) "
            "AND (npz_alignment_mismatches == 0 when --npz-dir is provided)"
        ),
        "files_audited": file_reports,
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
