#!/usr/bin/env python3
"""
verify_dataset_materialization.py
Skill: csbot-dataset-forensics

Verifica a materialização física dos datasets declarados em manifests, catálogos e relatórios:
1. Existência física do arquivo no disco com tamanho em bytes > 0;
2. Integridade de leitura (Parquet via pyarrow ou NPZ via numpy);
3. Reconciliação exata de contagens (linhas ou sequências declaradas vs reais);
4. Detecção de padrões regulares, baixa variância ou interpolação linear (np.linspace):
   - Se rotulado como SYNTHETIC/TEMPLATED/SIMULATED/INFERRED: emite WARNING_REQUIRES_PROVENANCE_REVIEW (não FAIL automático).
   - Se NÃO rotulado ou apresentado como REAL: emite FAIL imediato.
5. Caminhos versionados devem ser relativos à raiz do repositório.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_linear_or_zero_variance(arr: np.ndarray, feature_name: str) -> Optional[Dict[str, Any]]:
    """Detecta interpolação linear (ex: np.linspace) ou variância nula."""
    if arr.size < 4:
        return None

    # Check flat variance
    std = float(np.std(arr))
    if std < 1e-7:
        return {
            "feature": feature_name,
            "pattern": "ZERO_VARIANCE",
            "std": std,
            "sample_head": [float(x) for x in arr.ravel()[:5]],
        }

    # Check linear diffs if 1D or sequential along axis
    flat = arr.ravel()[:64]
    diffs = np.diff(flat)
    diff_std = float(np.std(diffs))
    if diff_std < 1e-6 and len(diffs) > 3 and abs(float(np.mean(diffs))) > 1e-7:
        return {
            "feature": feature_name,
            "pattern": "LINEAR_INTERPOLATION_DETECTED",
            "step": float(np.mean(diffs)),
            "diff_std": diff_std,
            "sample_head": [float(x) for x in flat[:5]],
        }

    return None


def verify_file_materialization(
    file_rel_or_abs: str,
    expected_rows: Optional[int] = None,
    expected_sha256: Optional[str] = None,
    declared_nature: str = "REAL",
) -> Dict[str, Any]:
    """Verifica um único arquivo de dataset físico."""
    res: Dict[str, Any] = {
        "declared_path": file_rel_or_abs,
        "is_relative": not Path(file_rel_or_abs).is_absolute(),
        "declared_nature": declared_nature.upper(),
        "exists": False,
        "size_bytes": 0,
        "sha256": None,
        "actual_rows": None,
        "row_count_match": None,
        "hash_match": None,
        "findings": [],
        "warnings": [],
        "status": "PASS",
    }

    path = Path(file_rel_or_abs)
    if not path.is_absolute():
        path = WORKSPACE_ROOT / path

    if not path.exists():
        res["status"] = "FAIL"
        res["findings"].append(f"Arquivo físico não materializado no disco: '{path}'.")
        return res

    res["exists"] = True
    size = path.stat().st_size
    res["size_bytes"] = size

    if size == 0:
        res["status"] = "FAIL"
        res["findings"].append(f"Arquivo físico está vazio (size = 0 bytes): '{path}'.")
        return res

    actual_hash = compute_sha256(path)
    res["sha256"] = actual_hash
    if expected_sha256:
        res["hash_match"] = (actual_hash.lower() == expected_sha256.lower())
        if not res["hash_match"]:
            res["status"] = "FAIL"
            res["findings"].append(
                f"Hash SHA-256 divergente: esperado '{expected_sha256}', calculado no disco '{actual_hash}'."
            )

    # Inspect contents
    lower_ext = path.suffix.lower()
    if lower_ext == ".npz":
        try:
            with np.load(path, allow_pickle=False) as npz:
                keys = list(npz.keys())
                res["npz_keys"] = keys
                first_arr = npz[keys[0]]
                actual_rows = int(first_arr.shape[0])
                res["actual_rows"] = actual_rows

                # Check linear/variance patterns
                for k in keys:
                    arr = npz[k]
                    if np.issubdtype(arr.dtype, np.number):
                        pat = check_linear_or_zero_variance(arr, k)
                        if pat:
                            if declared_nature.upper() in ("SYNTHETIC", "TEMPLATED", "SIMULATED", "INFERRED"):
                                res["warnings"].append({
                                    "status": "WARNING_REQUIRES_PROVENANCE_REVIEW",
                                    "detail": f"Padrão regular detectado na feature '{k}' ({pat['pattern']}), devidamente rotulado como {declared_nature.upper()}.",
                                    "pattern_info": pat,
                                })
                            else:
                                res["status"] = "FAIL"
                                res["findings"].append(
                                    f"Dado sintético/linear detectado na feature '{k}' ({pat['pattern']}) mas não rotulado ou apresentado como {declared_nature.upper()}."
                                )
        except Exception as exc:
            res["status"] = "FAIL"
            res["findings"].append(f"Falha ao ler arquivo .npz: {exc}")

    elif lower_ext == ".parquet":
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(path)
            res["actual_rows"] = table.num_rows
            res["columns"] = table.column_names
        except Exception as exc:
            res["status"] = "FAIL"
            res["findings"].append(f"Falha ao ler arquivo .parquet: {exc}")

    if expected_rows is not None and res["actual_rows"] is not None:
        res["row_count_match"] = (res["actual_rows"] == expected_rows)
        if not res["row_count_match"]:
            res["status"] = "FAIL"
            res["findings"].append(
                f"Contagem de linhas incompatível: declarado {expected_rows}, encontrado {res['actual_rows']}."
            )

    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica materialização física de datasets do CsBot.")
    parser.add_argument("--manifest-path", help="Caminho do manifesto/catálogo JSON contendo lista de arquivos.")
    parser.add_argument("--file-path", help="Caminho de um arquivo individual de dataset a verificar.")
    parser.add_argument("--expected-rows", type=int, help="Número esperado de linhas.")
    parser.add_argument("--expected-sha256", help="Hash SHA-256 esperado.")
    parser.add_argument("--declared-nature", default="REAL", choices=["REAL", "SIMULATED", "TEMPLATED", "SYNTHETIC", "INFERRED"])
    parser.add_argument("--output-json", help="Caminho para salvar o relatório de auditoria JSON.")

    args = parser.parse_args()
    results: List[Dict[str, Any]] = []

    if args.file_path:
        res = verify_file_materialization(
            file_rel_or_abs=args.file_path,
            expected_rows=args.expected_rows,
            expected_sha256=args.expected_sha256,
            declared_nature=args.declared_nature,
        )
        results.append(res)

    elif args.manifest_path:
        m_path = Path(args.manifest_path)
        if not m_path.is_absolute():
            m_path = WORKSPACE_ROOT / m_path

        if not m_path.exists():
            print(f"Manifesto não encontrado: {m_path}", file=sys.stderr)
            return 1

        with open(m_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        files_list = manifest_data.get("files") or manifest_data.get("shards") or []
        for item in files_list:
            if isinstance(item, str):
                res = verify_file_materialization(item, declared_nature=args.declared_nature)
            elif isinstance(item, dict):
                p = item.get("path") or item.get("file_path") or item.get("relative_path")
                exp_rows = item.get("row_count") or item.get("sequences") or item.get("count")
                exp_hash = item.get("sha256")
                nat = item.get("nature") or item.get("data_nature") or args.declared_nature
                res = verify_file_materialization(p, expected_rows=exp_rows, expected_sha256=exp_hash, declared_nature=nat)
            else:
                continue
            results.append(res)
    else:
        print("Erro: Forneça --file-path ou --manifest-path.", file=sys.stderr)
        return 1

    overall_verdict = "PASS"
    total_warnings = 0
    total_failures = 0

    for r in results:
        if r["status"] == "FAIL":
            overall_verdict = "FAIL"
            total_failures += 1
        total_warnings += len(r.get("warnings", []))

    if overall_verdict == "PASS" and total_warnings > 0:
        overall_verdict = "WARNING_REQUIRES_PROVENANCE_REVIEW"

    report = {
        "schema_version": "1.0.0",
        "verdict": overall_verdict,
        "total_files_checked": len(results),
        "total_failures": total_failures,
        "total_warnings": total_warnings,
        "results": results,
    }

    if args.output_json:
        out_p = Path(args.output_json)
        if not out_p.is_absolute():
            out_p = WORKSPACE_ROOT / out_p
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if overall_verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
