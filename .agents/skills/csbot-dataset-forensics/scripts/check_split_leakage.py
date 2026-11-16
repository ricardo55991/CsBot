#!/usr/bin/env python3
"""
check_split_leakage.py — Auditoria determinística de vazamento entre splits (train, val, test).

Governança CsBot:
- 01-evidence-before-claims: Registra caminho exato, hash SHA-256 completo (64 hex) e fórmula de interseção.
  Em modo --dry-run (sem artefatos reais), emite obrigatoriamente verdict="CONDITIONAL" e data_nature="SIMULATED".
- 02-no-test-contamination: Verifica isolamento absoluto de demo_id/match_id, round_id, janelas temporais
  [start_tick, end_tick] (incluindo vizinhança Delta_tick < W) e hashes SHA-256 de feature vectors/janelas.
- 03-zero-support-is-na: Impede preenchimento artificial de suporte no Test com exemplos do Train/Val.
- 04-synthetic-data-labeling: Classifica a natureza do artefato inspecionado (REAL vs SIMULATED).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


METADATA_KEYS = {
    "split",
    "subset",
    "partition",
    "demo_id",
    "match_id",
    "source_demo",
    "demo_name",
    "round_id",
    "round_num",
    "round",
    "tick",
    "start_tick",
    "end_tick",
    "tick_start",
    "tick_end",
    "min_tick",
    "max_tick",
    "sample_id",
    "id",
}


def compute_sha256(filepath: Path) -> str:
    """Calcula o hash SHA-256 completo (64 caracteres hexadecimais) de um arquivo."""
    hasher = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_feature_row_sha256(rec: Dict[str, Any]) -> Optional[str]:
    """Calcula hash SHA-256 determinístico do vetor/janela de features de um registro."""
    if "feature_sha256" in rec and rec["feature_sha256"]:
        return str(rec["feature_sha256"]).strip().lower()
    if "_feature_bytes_sha256" in rec and rec["_feature_bytes_sha256"]:
        return str(rec["_feature_bytes_sha256"]).strip().lower()

    feature_payload: Dict[str, Any] = {}
    for k in sorted(rec.keys()):
        if k not in METADATA_KEYS and not k.startswith("_"):
            val = rec[k]
            if isinstance(val, float):
                feature_payload[k] = round(val, 6)
            else:
                feature_payload[k] = val

    if not feature_payload:
        return None

    serialized = json.dumps(feature_payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_split_name(raw_split: str) -> str:
    """Normaliza nomes de splits para train, val ou test."""
    s = str(raw_split).strip().lower()
    if s in ("train", "training", "trn"):
        return "train"
    if s in ("val", "valid", "validation", "dev"):
        return "val"
    if s in ("test", "testing", "tst", "holdout", "holdout_final"):
        return "test"
    return s


def extract_records_from_json(filepath: Path) -> List[Dict[str, Any]]:
    """Extrai registros de split a partir de um arquivo JSON (manifest ou split file)."""
    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    records: List[Dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                records.append(item)
    elif isinstance(data, dict):
        splits_dict = data.get("splits")
        if isinstance(splits_dict, dict):
            for split_key, items in splits_dict.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            rec = dict(item)
                            rec.setdefault("split", split_key)
                            records.append(rec)
                        elif isinstance(item, str):
                            records.append({"split": split_key, "demo_id": item})
        for split_key in ("train", "val", "validation", "test", "holdout"):
            if split_key in data and isinstance(data[split_key], list):
                for item in data[split_key]:
                    if isinstance(item, dict):
                        rec = dict(item)
                        rec.setdefault("split", split_key)
                        records.append(rec)
                    elif isinstance(item, str):
                        records.append({"split": split_key, "demo_id": item})
        for list_key in ("files", "samples", "entries", "records", "rounds"):
            if list_key in data and isinstance(data[list_key], list):
                for item in data[list_key]:
                    if isinstance(item, dict):
                        records.append(item)
    return records


def extract_records_from_parquet(filepath: Path) -> List[Dict[str, Any]]:
    """Extrai colunas de identificação e features de um arquivo Parquet."""
    try:
        import pyarrow.parquet as pq  # type: ignore

        table = pq.read_table(filepath)
        records = table.to_pylist()
        return [r for r in records if isinstance(r, dict)]
    except ImportError:
        pass

    try:
        import pandas as pd  # type: ignore

        df = pd.read_parquet(filepath)
        return df.to_dict(orient="records")
    except ImportError as exc:
        raise RuntimeError(
            "Nem 'pyarrow' nem 'pandas' estão disponíveis para ler arquivo Parquet."
        ) from exc


def extract_records_from_npz(filepath: Path, default_split: Optional[str] = None) -> List[Dict[str, Any]]:
    """Extrai metadados de demo_id, round_id, ticks e hash SHA-256 de janelas X de um arquivo NPZ."""
    import numpy as np  # type: ignore

    records: List[Dict[str, Any]] = []
    with np.load(filepath, allow_pickle=False) as npz:
        keys = set(npz.files)
        n_rows = 0
        for k in sorted(keys):
            if npz[k].ndim >= 1:
                n_rows = int(npz[k].shape[0])
                break

        splits = npz["split"] if "split" in keys else None
        demos = npz["demo_id"] if "demo_id" in keys else (npz["match_id"] if "match_id" in keys else None)
        rounds = npz["round_id"] if "round_id" in keys else None
        ticks = npz["tick"] if "tick" in keys else None
        feat_arr = npz["X"] if "X" in keys else (npz["features"] if "features" in keys else None)

        if n_rows == 0 and demos is None:
            return [
                {
                    "split": default_split or "unknown",
                    "demo_id": filepath.stem,
                    "round_id": "0",
                }
            ]

        for i in range(n_rows):
            rec: Dict[str, Any] = {}
            rec["split"] = str(splits[i]) if splits is not None else (default_split or "unknown")
            rec["demo_id"] = str(demos[i]) if demos is not None else filepath.stem
            if rounds is not None:
                rec["round_id"] = str(rounds[i])
            if ticks is not None:
                t_entry = ticks[i]
                if getattr(t_entry, "ndim", 0) >= 1 and len(t_entry) > 0:
                    rec["start_tick"] = int(t_entry[0])
                    rec["end_tick"] = int(t_entry[-1])
                else:
                    rec["tick"] = int(t_entry)
            if feat_arr is not None:
                row_bytes = np.ascontiguousarray(feat_arr[i]).tobytes()
                rec["_feature_bytes_sha256"] = hashlib.sha256(row_bytes).hexdigest()
            records.append(rec)

    return records


def load_records(input_path: Path, default_split: Optional[str] = None) -> List[Dict[str, Any]]:
    """Carrega registros de um arquivo ou diretório de forma somente-leitura."""
    if input_path.is_dir():
        all_records: List[Dict[str, Any]] = []
        for child in sorted(input_path.rglob("*")):
            if not child.is_file():
                continue
            inferred_split = default_split
            for part in child.parts:
                norm = normalize_split_name(part)
                if norm in ("train", "val", "test"):
                    inferred_split = norm
            if child.suffix.lower() == ".json":
                all_records.extend(extract_records_from_json(child))
            elif child.suffix.lower() == ".parquet":
                recs = extract_records_from_parquet(child)
                for r in recs:
                    if inferred_split and "split" not in r:
                        r["split"] = inferred_split
                all_records.extend(recs)
            elif child.suffix.lower() == ".npz":
                all_records.extend(extract_records_from_npz(child, inferred_split))
        return all_records

    suffix = input_path.suffix.lower()
    if suffix == ".json":
        return extract_records_from_json(input_path)
    if suffix == ".parquet":
        return extract_records_from_parquet(input_path)
    if suffix == ".npz":
        return extract_records_from_npz(input_path, default_split)
    raise ValueError(f"Formato de arquivo não suportado para auditoria de split: {input_path}")


def analyze_leakage(records: List[Dict[str, Any]], window_tolerance_ticks: int = 0) -> Dict[str, Any]:
    """
    Calcula interseções de demo_id/match_id, (demo_id, round_id), janelas temporais
    (com tolerância de vizinhança W) e hashes SHA-256 de feature vectors entre train, val e test.
    """
    demos_by_split: Dict[str, Set[str]] = {"train": set(), "val": set(), "test": set()}
    rounds_by_split: Dict[str, Set[Tuple[str, str]]] = {"train": set(), "val": set(), "test": set()}
    feature_hashes_by_split: Dict[str, Set[str]] = {"train": set(), "val": set(), "test": set()}
    windows_by_split: Dict[str, List[Tuple[str, str, int, int]]] = {
        "train": [],
        "val": [],
        "test": [],
    }
    tick_bounds: Dict[Tuple[str, str, str], List[int]] = {}
    record_counts: Dict[str, int] = {"train": 0, "val": 0, "test": 0, "unknown": 0}

    for rec in records:
        raw_split = rec.get("split", rec.get("subset", rec.get("partition", "unknown")))
        split = normalize_split_name(str(raw_split))
        if split not in ("train", "val", "test"):
            record_counts["unknown"] += 1
            continue
        record_counts[split] += 1

        f_hash = compute_feature_row_sha256(rec)
        if f_hash:
            feature_hashes_by_split[split].add(f_hash)

        demo_id = str(
            rec.get(
                "demo_id",
                rec.get("match_id", rec.get("source_demo", rec.get("demo_name", ""))),
            )
        ).strip()
        if not demo_id:
            continue
        demos_by_split[split].add(demo_id)

        round_val = rec.get("round_id", rec.get("round_num", rec.get("round", None)))
        round_id = str(round_val).strip() if round_val is not None else None
        if round_id is not None and round_id != "":
            rounds_by_split[split].add((demo_id, round_id))

        start_tick = rec.get("start_tick", rec.get("tick_start", rec.get("min_tick")))
        end_tick = rec.get("end_tick", rec.get("tick_end", rec.get("max_tick")))
        single_tick = rec.get("tick")

        r_key = round_id if round_id is not None else "*"
        if start_tick is not None and end_tick is not None:
            try:
                s_t, e_t = int(start_tick), int(end_tick)
                if s_t > e_t:
                    s_t, e_t = e_t, s_t
                windows_by_split[split].append((demo_id, r_key, s_t, e_t))
            except (ValueError, TypeError):
                pass
        elif single_tick is not None:
            try:
                t_val = int(single_tick)
                b_key = (split, demo_id, r_key)
                if b_key not in tick_bounds:
                    tick_bounds[b_key] = [t_val, t_val]
                else:
                    if t_val < tick_bounds[b_key][0]:
                        tick_bounds[b_key][0] = t_val
                    if t_val > tick_bounds[b_key][1]:
                        tick_bounds[b_key][1] = t_val
            except (ValueError, TypeError):
                pass

    for (split, demo_id, r_key), (min_t, max_t) in tick_bounds.items():
        windows_by_split[split].append((demo_id, r_key, min_t, max_t))

    pairs = [("train", "val"), ("train", "test"), ("val", "test")]
    intersections: Dict[str, Any] = {}
    total_demo_overlap = 0
    total_round_overlap = 0
    total_temporal_overlap = 0
    total_feature_hash_overlap = 0

    for s1, s2 in pairs:
        pair_key = f"{s1}_vs_{s2}"
        demo_inter = sorted(demos_by_split[s1].intersection(demos_by_split[s2]))
        round_inter = sorted(rounds_by_split[s1].intersection(rounds_by_split[s2]))
        feat_inter = sorted(feature_hashes_by_split[s1].intersection(feature_hashes_by_split[s2]))

        temporal_overlaps: List[Dict[str, Any]] = []
        w2_by_key: Dict[Tuple[str, str], List[Tuple[int, int]]] = {}
        for d_id, r_id, st, et in windows_by_split[s2]:
            w2_by_key.setdefault((d_id, r_id), []).append((st, et))

        for d_id, r_id, st1, et1 in windows_by_split[s1]:
            for st2, et2 in w2_by_key.get((d_id, r_id), []):
                overlap_start = max(st1 - window_tolerance_ticks, st2 - window_tolerance_ticks)
                overlap_end = min(et1 + window_tolerance_ticks, et2 + window_tolerance_ticks)
                if overlap_start <= overlap_end:
                    temporal_overlaps.append(
                        {
                            "demo_id": d_id,
                            "round_id": r_id,
                            f"{s1}_window": [st1, et1],
                            f"{s2}_window": [st2, et2],
                            "window_tolerance_ticks": window_tolerance_ticks,
                            "overlap_window": [overlap_start, overlap_end],
                        }
                    )

        total_demo_overlap += len(demo_inter)
        total_round_overlap += len(round_inter)
        total_temporal_overlap += len(temporal_overlaps)
        total_feature_hash_overlap += len(feat_inter)

        intersections[pair_key] = {
            "demo_id_overlap_count": len(demo_inter),
            "demo_id_overlap_examples": demo_inter[:25],
            "round_id_overlap_count": len(round_inter),
            "round_id_overlap_examples": [
                {"demo_id": d, "round_id": r} for d, r in round_inter[:25]
            ],
            "temporal_window_overlap_count": len(temporal_overlaps),
            "temporal_window_overlap_examples": temporal_overlaps[:25],
            "feature_window_sha256_overlap_count": len(feat_inter),
            "feature_window_sha256_overlap_examples": feat_inter[:25],
        }

    leakage_detected = (
        total_demo_overlap > 0
        or total_round_overlap > 0
        or total_temporal_overlap > 0
        or total_feature_hash_overlap > 0
        or record_counts["unknown"] > 0
    )

    return {
        "split_record_counts": record_counts,
        "unique_demos_per_split": {k: len(v) for k, v in demos_by_split.items()},
        "unique_rounds_per_split": {k: len(v) for k, v in rounds_by_split.items()},
        "unique_feature_hashes_per_split": {k: len(v) for k, v in feature_hashes_by_split.items()},
        "intersections": intersections,
        "totals": {
            "demo_id_overlap_total": total_demo_overlap,
            "round_id_overlap_total": total_round_overlap,
            "temporal_window_overlap_total": total_temporal_overlap,
            "feature_window_sha256_overlap_total": total_feature_hash_overlap,
            "unassigned_split_records": record_counts["unknown"],
        },
        "aggregation_formula": (
            "leakage_detected = (|Demos(A) n Demos(B)| > 0) OR "
            "(|Rounds(A) n Rounds(B)| > 0) OR "
            "(|Windows_W(A) n Windows_W(B)| > 0) OR "
            "(|FeatureSHA256(A) n FeatureSHA256(B)| > 0) OR (unassigned_split_records > 0) "
            "for (A,B) in {(train,val), (train,test), (val,test)}"
        ),
        "leakage_detected": leakage_detected,
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check_split_leakage.py",
        description=(
            "Audita vazamento de dados (demo_id, round_id, janelas temporais e SHA-256 de features) "
            "entre os splits train, val e test."
        ),
    )
    parser.add_argument(
        "--input",
        "--manifest",
        "--splits-dir",
        "--parquet-dir",
        "--npz-dir",
        "--target",
        "-i",
        dest="input",
        type=str,
        required=False,
        help="Caminho para arquivo de split/manifest (.json, .parquet, .npz) ou diretório de splits.",
    )
    parser.add_argument(
        "--train-input",
        type=str,
        default=None,
        help="Opcional: arquivo ou diretório específico do split train.",
    )
    parser.add_argument(
        "--val-input",
        type=str,
        default=None,
        help="Opcional: arquivo ou diretório específico do split val.",
    )
    parser.add_argument(
        "--test-input",
        type=str,
        default=None,
        help="Opcional: arquivo ou diretório específico do split test.",
    )
    parser.add_argument(
        "--window-tolerance",
        type=int,
        default=0,
        help="Vizinhança temporal em ticks (W) para detectar proximidade imediata entre splits (padrão: 0).",
    )
    parser.add_argument(
        "--output-json",
        "--out",
        "-o",
        dest="output_json",
        type=str,
        default=None,
        help="Caminho opcional para salvar o relatório JSON determinístico de auditoria.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa validação estrutural simulada (emite verdict=CONDITIONAL e data_nature=SIMULATED).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.dry_run:
        report: Dict[str, Any] = {
            "script": "check_split_leakage.py",
            "mode": "DRY_RUN",
            "data_nature": "SIMULATED",
            "governance_rules": [
                "01-evidence-before-claims",
                "02-no-test-contamination",
                "03-zero-support-is-na",
                "04-synthetic-data-labeling",
            ],
            "input_artifacts": [],
            "leakage_detected": False,
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

    if not args.input and not (args.train_input or args.val_input or args.test_input):
        print(
            "ERRO: Informe --input/--manifest/--splits-dir ou --train-input/--val-input/--test-input (ou use --dry-run).",
            file=sys.stderr,
        )
        return 2

    records: List[Dict[str, Any]] = []
    artifacts_info: List[Dict[str, str]] = []

    try:
        if args.input:
            in_path = Path(args.input).resolve()
            if not in_path.exists():
                print(f"ERRO: Caminho de entrada não encontrado: {in_path}", file=sys.stderr)
                return 2
            if in_path.is_file():
                artifacts_info.append(
                    {"path": str(in_path), "sha256": compute_sha256(in_path)}
                )
            else:
                for f in sorted(in_path.rglob("*")):
                    if f.is_file() and f.suffix.lower() in (".json", ".parquet", ".npz"):
                        artifacts_info.append({"path": str(f), "sha256": compute_sha256(f)})
            records.extend(load_records(in_path))

        for split_label, arg_val in (
            ("train", args.train_input),
            ("val", args.val_input),
            ("test", args.test_input),
        ):
            if arg_val:
                s_path = Path(arg_val).resolve()
                if not s_path.exists():
                    print(f"ERRO: Caminho para {split_label} não encontrado: {s_path}", file=sys.stderr)
                    return 2
                if s_path.is_file():
                    artifacts_info.append(
                        {"path": str(s_path), "sha256": compute_sha256(s_path)}
                    )
                else:
                    for f in sorted(s_path.rglob("*")):
                        if f.is_file() and f.suffix.lower() in (".json", ".parquet", ".npz"):
                            artifacts_info.append({"path": str(f), "sha256": compute_sha256(f)})
                loaded = load_records(s_path, default_split=split_label)
                for r in loaded:
                    r["split"] = split_label
                records.extend(loaded)
    except Exception as exc:
        print(f"ERRO ao ler artefatos de entrada: {exc}", file=sys.stderr)
        return 2

    if not records:
        report = {
            "script": "check_split_leakage.py",
            "mode": "REAL_AUDIT",
            "data_nature": "REAL",
            "input_artifacts": artifacts_info,
            "total_records_loaded": 0,
            "leakage_detected": True,
            "verdict": "FAIL",
            "error": "Nenhum registro de split encontrado nos artefatos informados.",
        }
        if args.output_json:
            out_path = Path(args.output_json).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    analysis = analyze_leakage(records, window_tolerance_ticks=args.window_tolerance)
    verdict = "FAIL" if analysis["leakage_detected"] else "PASS"

    report = {
        "script": "check_split_leakage.py",
        "mode": "REAL_AUDIT",
        "data_nature": "REAL",
        "governance_rules": [
            "01-evidence-before-claims",
            "02-no-test-contamination",
            "03-zero-support-is-na",
            "04-synthetic-data-labeling",
        ],
        "input_artifacts": artifacts_info,
        "total_records_loaded": len(records),
        **analysis,
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
