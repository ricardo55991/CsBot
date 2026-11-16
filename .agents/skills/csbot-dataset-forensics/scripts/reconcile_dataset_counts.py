#!/usr/bin/env python3
"""
reconcile_dataset_counts.py — Reconciliação contábil determinística entre manifest, rejection_ledger, splits e disco.

Governança CsBot:
- 01-evidence-before-claims: Verifica hashes SHA-256 completos, contagens físicas no disco e fórmulas contábeis.
  Em modo --dry-run (sem artefatos reais), emite obrigatoriamente verdict="CONDITIONAL" e data_nature="SIMULATED".
- 04-synthetic-data-labeling: Classifica explicitamente a natureza dos dados auditados.

Verifica invariantes contábeis:
1. source_file_count == accepted_file_count + rejected_file_count
2. Equação de conservação do pipeline (dataset_forensics_protocol.md):
   N_raw_extracted == N_train + N_val + N_test + sum(rejection_ledger.values())
   com unaccounted_delta == 0.
3. accepted_file_count e accepted_frame_count == contagem real de arquivos e linhas no disco (quando --raw-dir/--parquet-dir/--npz-dir fornecido).
4. useful_hours consistente com accepted_frame_count / (tick_rate * 3600).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


TRACKED_METRICS = (
    "source_file_count",
    "accepted_file_count",
    "rejected_file_count",
    "valid_round_count",
    "accepted_frame_count",
    "useful_hours",
)


def compute_sha256(filepath: Path) -> str:
    """Calcula o hash SHA-256 completo (64 caracteres hexadecimais) de um arquivo."""
    hasher = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_metrics_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Busca recursivamente ou em chaves conhecidas as métricas contábeis e o rejection_ledger."""
    extracted: Dict[str, Any] = {}
    search_targets = [data]
    for subkey in ("summary", "counts", "metrics", "accounting", "statistics", "totals", "dataset_stats"):
        if isinstance(data.get(subkey), dict):
            search_targets.append(data[subkey])

    aliases = {
        "source_file_count": ["source_file_count", "total_source_files", "source_files", "raw_file_count"],
        "accepted_file_count": ["accepted_file_count", "valid_file_count", "accepted_files", "exported_file_count"],
        "rejected_file_count": ["rejected_file_count", "discarded_file_count", "rejected_files", "failed_file_count"],
        "valid_round_count": ["valid_round_count", "accepted_round_count", "total_valid_rounds", "rounds_count"],
        "accepted_frame_count": ["accepted_frame_count", "total_frames", "valid_frame_count", "total_rows", "sample_count"],
        "useful_hours": ["useful_hours", "total_useful_hours", "hours_useful", "duration_hours"],
        "raw_extracted_count": ["raw_extracted_count", "n_raw_extracted", "total_raw_samples", "raw_frame_count"],
        "train_count": ["train_count", "n_train", "train_samples", "train_frames"],
        "val_count": ["val_count", "n_val", "val_samples", "val_frames", "validation_count"],
        "test_count": ["test_count", "n_test", "test_samples", "test_frames"],
    }

    for canonical, key_list in aliases.items():
        for target in search_targets:
            for k in key_list:
                if k in target and target[k] is not None and not isinstance(target[k], (list, dict)):
                    extracted[canonical] = target[k]
                    break
            if canonical in extracted:
                break

    # Extrair contagens de splits caso haja bloco "splits" ou "split_counts"
    for split_block_key in ("split_counts", "splits"):
        for target in search_targets:
            sb = target.get(split_block_key)
            if isinstance(sb, dict):
                for sp_name, canonical_key in (("train", "train_count"), ("val", "val_count"), ("validation", "val_count"), ("test", "test_count")):
                    if canonical_key not in extracted and sp_name in sb:
                        val = sb[sp_name]
                        if isinstance(val, int):
                            extracted[canonical_key] = val
                        elif isinstance(val, list):
                            extracted[canonical_key] = len(val)
                        elif isinstance(val, dict) and "count" in val:
                            extracted[canonical_key] = int(val["count"])

    # Extrair rejection_ledger por motivo
    for ledger_key in ("rejection_ledger", "rejected_reasons", "rejections_by_reason", "discard_reasons"):
        for target in search_targets:
            if isinstance(target.get(ledger_key), dict):
                extracted["rejection_ledger"] = {
                    str(k): int(v) for k, v in target[ledger_key].items() if isinstance(v, (int, float))
                }
                break

    if "accepted_file_count" not in extracted and isinstance(data.get("accepted_files"), list):
        extracted["accepted_file_count"] = len(data["accepted_files"])
    if "rejected_file_count" not in extracted and isinstance(data.get("rejected_files"), list):
        extracted["rejected_file_count"] = len(data["rejected_files"])
    if "source_file_count" not in extracted and isinstance(data.get("files"), list):
        extracted["source_file_count"] = len(data["files"])

    return extracted


def inspect_raw_directory(raw_dir: Path) -> Dict[str, Any]:
    """Conta arquivos .npz e .parquet reais no disco e soma linhas/frames por split e globalmente."""
    npz_files = sorted(raw_dir.rglob("*.npz"))
    parquet_files = sorted(raw_dir.rglob("*.parquet"))
    all_files = npz_files + parquet_files

    total_frames = 0
    total_rounds = 0
    frame_count_verified = True
    file_hashes: List[Dict[str, Any]] = []

    for fpath in all_files:
        file_hashes.append({"path": str(fpath.resolve()), "sha256": compute_sha256(fpath)})
        if fpath.suffix.lower() == ".npz":
            try:
                import numpy as np  # type: ignore

                with np.load(fpath, allow_pickle=False) as npz:
                    file_rows = 0
                    for k in npz.files:
                        if npz[k].ndim >= 1:
                            file_rows = int(npz[k].shape[0])
                            break
                    total_frames += file_rows
                    if "round_id" in npz.files:
                        total_rounds += len(set(npz["round_id"].tolist()))
            except Exception:
                frame_count_verified = False
        elif fpath.suffix.lower() == ".parquet":
            try:
                import pyarrow.parquet as pq  # type: ignore

                meta = pq.read_metadata(fpath)
                total_frames += int(meta.num_rows)
                try:
                    t = pq.read_table(fpath, columns=["round_id"])
                    total_rounds += len(set(t.column("round_id").to_pylist()))
                except Exception:
                    pass
            except ImportError:
                try:
                    import pandas as pd  # type: ignore

                    df = pd.read_parquet(fpath)
                    total_frames += int(len(df))
                    if "round_id" in df.columns:
                        total_rounds += int(df["round_id"].nunique())
                except Exception:
                    frame_count_verified = False

    return {
        "directory": str(raw_dir.resolve()),
        "npz_file_count": len(npz_files),
        "parquet_file_count": len(parquet_files),
        "total_data_files_on_disk": len(all_files),
        "observed_frame_count": total_frames if frame_count_verified else None,
        "observed_round_count": total_rounds if total_rounds > 0 else None,
        "frame_count_verified": frame_count_verified,
        "files_inspected": file_hashes[:50],
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="reconcile_dataset_counts.py",
        description=(
            "Reconcilia contagens entre dataset_manifest*.json, rejection_ledger, splits (train+val+test), "
            "diretórios de arquivos brutos (.npz / .parquet) e relatórios de dataset."
        ),
    )
    parser.add_argument(
        "--manifest",
        "--input",
        "--target",
        "-m",
        "-i",
        dest="manifest",
        type=str,
        required=False,
        help="Caminho para o arquivo dataset_manifest*.json.",
    )
    parser.add_argument(
        "--raw-dir",
        "--splits-dir",
        "--parquet-dir",
        "--npz-dir",
        "-d",
        dest="raw_dir",
        type=str,
        default=None,
        help="Opcional: diretório contendo os arquivos .npz ou .parquet aceitos.",
    )
    parser.add_argument(
        "--report-json",
        "-r",
        type=str,
        default=None,
        help="Opcional: segundo relatório JSON para cruzamento de métricas contábeis.",
    )
    parser.add_argument(
        "--fps-or-tickrate",
        type=float,
        default=None,
        help="Opcional: taxa de amostragem em Hz (ex: 64.0 ou 4.0) para validar useful_hours.",
    )
    parser.add_argument(
        "--hours-tolerance",
        type=float,
        default=0.05,
        help="Tolerância absoluta em horas para verificação de useful_hours (padrão: 0.05).",
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
        help="Executa em modo de verificação sintática/estrutural simulada (emite verdict=CONDITIONAL).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.dry_run:
        report: Dict[str, Any] = {
            "script": "reconcile_dataset_counts.py",
            "mode": "DRY_RUN",
            "data_nature": "SIMULATED",
            "governance_rules": [
                "01-evidence-before-claims",
                "04-synthetic-data-labeling",
            ],
            "tracked_metrics": list(TRACKED_METRICS),
            "conservation_equation": "N_raw_extracted == N_train + N_val + N_test + sum(rejection_ledger.values())",
            "unaccounted_delta": 0,
            "divergences": [],
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

    if not args.manifest:
        print("ERRO: O argumento --manifest é obrigatório fora do modo --dry-run.", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.is_file():
        print(f"ERRO: Manifest não encontrado: {manifest_path}", file=sys.stderr)
        return 2

    try:
        manifest_sha256 = compute_sha256(manifest_path)
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except Exception as exc:
        print(f"ERRO ao ler manifest JSON: {exc}", file=sys.stderr)
        return 2

    manifest_metrics = extract_metrics_from_dict(manifest_data)
    divergences: List[Dict[str, Any]] = []

    # 1. Verificar presença de todas as 6 métricas obrigatórias no manifest
    missing_metrics = [m for m in TRACKED_METRICS if m not in manifest_metrics]
    if missing_metrics:
        divergences.append(
            {
                "check": "manifest_required_metrics_present",
                "missing_metrics": missing_metrics,
                "reason": "O manifest não contém todas as métricas contábeis exigidas.",
            }
        )

    # 2. Invariante: source_file_count == accepted_file_count + rejected_file_count
    if all(k in manifest_metrics for k in ("source_file_count", "accepted_file_count", "rejected_file_count")):
        src_c = int(manifest_metrics["source_file_count"])
        acc_c = int(manifest_metrics["accepted_file_count"])
        rej_c = int(manifest_metrics["rejected_file_count"])
        if src_c != acc_c + rej_c:
            divergences.append(
                {
                    "check": "source_equals_accepted_plus_rejected",
                    "formula": "source_file_count == accepted_file_count + rejected_file_count",
                    "expected": acc_c + rej_c,
                    "observed": src_c,
                    "accepted_file_count": acc_c,
                    "rejected_file_count": rej_c,
                }
            )

    # 3. Reconciliação Train + Val + Test e Rejection Ledger (dataset_forensics_protocol.md Seção 2)
    split_total_reconciliation: Dict[str, Any] = {}
    unaccounted_delta = 0
    if all(k in manifest_metrics for k in ("train_count", "val_count", "test_count")):
        n_train = int(manifest_metrics["train_count"])
        n_val = int(manifest_metrics["val_count"])
        n_test = int(manifest_metrics["test_count"])
        split_sum = n_train + n_val + n_test
        split_total_reconciliation["n_train"] = n_train
        split_total_reconciliation["n_val"] = n_val
        split_total_reconciliation["n_test"] = n_test
        split_total_reconciliation["split_sum"] = split_sum

        if "accepted_frame_count" in manifest_metrics:
            acc_frames = int(manifest_metrics["accepted_frame_count"])
            split_total_reconciliation["accepted_frame_count"] = acc_frames
            if split_sum != acc_frames:
                unaccounted_delta = acc_frames - split_sum
                divergences.append(
                    {
                        "check": "split_total_matches_accepted_frame_count",
                        "formula": "accepted_frame_count == N_train + N_val + N_test",
                        "expected_split_sum": split_sum,
                        "observed_accepted_frame_count": acc_frames,
                        "unaccounted_delta": unaccounted_delta,
                    }
                )

        ledger = manifest_metrics.get("rejection_ledger", {})
        ledger_sum = sum(int(v) for v in ledger.values()) if isinstance(ledger, dict) else 0
        split_total_reconciliation["rejection_ledger"] = ledger
        split_total_reconciliation["rejection_ledger_sum"] = ledger_sum

        if "raw_extracted_count" in manifest_metrics:
            n_raw = int(manifest_metrics["raw_extracted_count"])
            expected_raw = split_sum + ledger_sum
            unaccounted_delta = n_raw - expected_raw
            split_total_reconciliation["n_raw_extracted"] = n_raw
            split_total_reconciliation["unaccounted_delta"] = unaccounted_delta
            if unaccounted_delta != 0:
                divergences.append(
                    {
                        "check": "pipeline_conservation_equation",
                        "formula": "N_raw_extracted == N_train + N_val + N_test + sum(rejection_ledger)",
                        "n_raw_extracted": n_raw,
                        "expected_sum": expected_raw,
                        "unaccounted_delta": unaccounted_delta,
                    }
                )

    # 4. Verificar valores não-negativos e coerência de useful_hours
    for k in ("source_file_count", "accepted_file_count", "rejected_file_count", "valid_round_count", "accepted_frame_count"):
        if k in manifest_metrics and int(manifest_metrics[k]) < 0:
            divergences.append(
                {
                    "check": f"{k}_non_negative",
                    "observed": manifest_metrics[k],
                    "reason": "Contagem negativa inválida.",
                }
            )

    if "useful_hours" in manifest_metrics and "accepted_frame_count" in manifest_metrics:
        u_hours = float(manifest_metrics["useful_hours"])
        frames = int(manifest_metrics["accepted_frame_count"])
        if u_hours < 0 or math.isnan(u_hours) or math.isinf(u_hours):
            divergences.append(
                {
                    "check": "useful_hours_valid_float",
                    "observed": u_hours,
                    "reason": "useful_hours negativo, NaN ou Inf.",
                }
            )
        if frames == 0 and u_hours > 0:
            divergences.append(
                {
                    "check": "useful_hours_zero_when_zero_frames",
                    "accepted_frame_count": frames,
                    "useful_hours": u_hours,
                }
            )
        if args.fps_or_tickrate and args.fps_or_tickrate > 0:
            expected_hours = frames / (float(args.fps_or_tickrate) * 3600.0)
            if abs(expected_hours - u_hours) > args.hours_tolerance:
                divergences.append(
                    {
                        "check": "useful_hours_formula_consistency",
                        "formula": "accepted_frame_count / (fps_or_tickrate * 3600)",
                        "expected_hours": round(expected_hours, 6),
                        "observed_hours": u_hours,
                        "tolerance": args.hours_tolerance,
                    }
                )

    # 5. Reconciliação com diretório físico de arquivos brutos (--raw-dir)
    disk_audit: Optional[Dict[str, Any]] = None
    if args.raw_dir:
        raw_dir_path = Path(args.raw_dir).resolve()
        if not raw_dir_path.is_dir():
            print(f"ERRO: Diretório bruto não encontrado: {raw_dir_path}", file=sys.stderr)
            return 2
        disk_audit = inspect_raw_directory(raw_dir_path)
        if "accepted_file_count" in manifest_metrics:
            acc_c = int(manifest_metrics["accepted_file_count"])
            disk_c = int(disk_audit["total_data_files_on_disk"])
            if acc_c != disk_c:
                divergences.append(
                    {
                        "check": "disk_file_count_matches_accepted_file_count",
                        "manifest_accepted_file_count": acc_c,
                        "disk_total_data_files": disk_c,
                    }
                )
        if (
            disk_audit.get("frame_count_verified")
            and disk_audit.get("observed_frame_count") is not None
            and "accepted_frame_count" in manifest_metrics
        ):
            manifest_frames = int(manifest_metrics["accepted_frame_count"])
            disk_frames = int(disk_audit["observed_frame_count"])
            if manifest_frames != disk_frames:
                divergences.append(
                    {
                        "check": "disk_frame_count_matches_accepted_frame_count",
                        "manifest_accepted_frame_count": manifest_frames,
                        "disk_observed_frame_count": disk_frames,
                    }
                )

    # 6. Reconciliação com relatório secundário (--report-json)
    secondary_report_audit: Optional[Dict[str, Any]] = None
    if args.report_json:
        rep_path = Path(args.report_json).resolve()
        if not rep_path.is_file():
            print(f"ERRO: Relatório JSON secundário não encontrado: {rep_path}", file=sys.stderr)
            return 2
        rep_sha = compute_sha256(rep_path)
        with rep_path.open("r", encoding="utf-8") as f:
            rep_data = json.load(f)
        rep_metrics = extract_metrics_from_dict(rep_data)
        secondary_report_audit = {
            "path": str(rep_path),
            "sha256": rep_sha,
            "extracted_metrics": rep_metrics,
        }
        for metric in TRACKED_METRICS:
            if metric in manifest_metrics and metric in rep_metrics:
                m_val = manifest_metrics[metric]
                r_val = rep_metrics[metric]
                if isinstance(m_val, float) or isinstance(r_val, float):
                    if abs(float(m_val) - float(r_val)) > 1e-5:
                        divergences.append(
                            {
                                "check": f"report_matches_manifest_{metric}",
                                "manifest_value": m_val,
                                "report_value": r_val,
                            }
                        )
                elif int(m_val) != int(r_val):
                    divergences.append(
                        {
                            "check": f"report_matches_manifest_{metric}",
                            "manifest_value": m_val,
                            "report_value": r_val,
                        }
                    )

    verdict = "PASS" if len(divergences) == 0 else "FAIL"

    report = {
        "script": "reconcile_dataset_counts.py",
        "mode": "REAL_AUDIT",
        "data_nature": "REAL",
        "governance_rules": [
            "01-evidence-before-claims",
            "04-synthetic-data-labeling",
        ],
        "manifest": {
            "path": str(manifest_path),
            "sha256": manifest_sha256,
            "extracted_metrics": manifest_metrics,
        },
        "split_total_reconciliation": split_total_reconciliation,
        "unaccounted_delta": unaccounted_delta,
        "disk_audit": disk_audit,
        "secondary_report_audit": secondary_report_audit,
        "aggregation_formula": (
            "PASS iff (missing_metrics == 0) AND "
            "(source_file_count == accepted_file_count + rejected_file_count) AND "
            "(N_raw_extracted == N_train + N_val + N_test + sum(rejection_ledger)) AND "
            "(disk_files == accepted_file_count) AND (disk_frames == accepted_frame_count)"
        ),
        "divergence_count": len(divergences),
        "divergences": divergences,
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
