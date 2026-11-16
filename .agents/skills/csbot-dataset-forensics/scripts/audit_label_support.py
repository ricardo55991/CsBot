#!/usr/bin/env python3
"""
audit_label_support.py — Auditoria determinística de suporte (support) de labels e amostragem visual estratificada.

Governança CsBot:
- 01-evidence-before-claims: Registra caminho exato, hash SHA-256 completo e contagens brutas por classe e split.
  Em modo --dry-run (sem artefatos reais), emite obrigatoriamente verdict="CONDITIONAL" e data_nature="SIMULATED".
- 02-no-test-contamination: Audita o suporte de `train`, `val` e `test` de forma isolada e somente-leitura.
- 03-zero-support-is-na: Qualquer classe em qualquer cabeçote (`PositioningState`, `NextSector`, `SpotId`,
  `Transition`, `ExitTrigger`, `JumpPress`) que apresente `support == 0` no split avaliado recebe
  obrigatoriamente `"metrics_policy": "N/A_REQUIRED"` e `"eval_status": "N/A_ZERO_SUPPORT"`.
- Exporta subconjunto determinístico de amostras estratificadas (`visual_audit_samples`) com coordenadas `(x, y, z)`,
  spot atribuído e estado do jogo para inspeção visual.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


CANONICAL_LABEL_HEADS: Dict[str, List[str]] = {
    "PositioningState": ["PositioningState", "positioning_state", "state_label", "pos_state"],
    "NextSector": ["NextSector", "next_sector", "sector_label", "target_sector"],
    "SpotId": ["SpotId", "spot_id", "target_spot_id", "spot_label"],
    "Transition": ["Transition", "transition", "transition_label", "is_transition"],
    "ExitTrigger": ["ExitTrigger", "exit_trigger", "exit_label"],
    "JumpPress": ["JumpPress", "jump_press", "jump_label", "is_jump"],
}


def compute_sha256(filepath: Path) -> str:
    """Calcula o hash SHA-256 completo (64 caracteres hexadecimais) de um arquivo."""
    hasher = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def normalize_split_name(raw_split: str) -> str:
    """Normaliza o identificador do split para train, val ou test."""
    s = str(raw_split).strip().lower()
    if s in ("train", "training", "trn"):
        return "train"
    if s in ("val", "valid", "validation", "dev"):
        return "val"
    if s in ("test", "testing", "tst", "holdout", "holdout_final"):
        return "test"
    return s


def load_known_classes_schema(schema_path: Optional[Path]) -> Dict[str, List[str]]:
    """Carrega o catálogo de classes conhecidas para cada head (opcional)."""
    default_catalog: Dict[str, List[str]] = {
        "Transition": ["0", "1"],
        "ExitTrigger": ["0", "1"],
        "JumpPress": ["0", "1"],
    }
    if not schema_path:
        return default_catalog

    with schema_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        for head in CANONICAL_LABEL_HEADS:
            if head in data:
                val = data[head]
                if isinstance(val, list):
                    default_catalog[head] = [str(x) for x in val]
                elif isinstance(val, dict):
                    default_catalog[head] = [str(k) for k in val.keys()]
    return default_catalog


def extract_rows_from_file(filepath: Path, default_split: Optional[str] = None) -> List[Dict[str, Any]]:
    """Extrai registros contendo split, coordenadas e colunas de labels a partir de JSON, Parquet ou NPZ."""
    suffix = filepath.suffix.lower()
    if suffix == ".json":
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        if isinstance(data, dict):
            if "records" in data and isinstance(data["records"], list):
                return [r for r in data["records"] if isinstance(r, dict)]
            if "samples" in data and isinstance(data["samples"], list):
                return [r for r in data["samples"] if isinstance(r, dict)]
            rows: List[Dict[str, Any]] = []
            for sp in ("train", "val", "validation", "test"):
                if sp in data and isinstance(data[sp], list):
                    for item in data[sp]:
                        if isinstance(item, dict):
                            rec = dict(item)
                            rec.setdefault("split", sp)
                            rows.append(rec)
            return rows

    if suffix == ".parquet":
        try:
            import pyarrow.parquet as pq  # type: ignore

            table = pq.read_table(filepath)
            rows = table.to_pylist()
        except ImportError:
            import pandas as pd  # type: ignore

            df = pd.read_parquet(filepath)
            rows = df.to_dict(orient="records")
        if default_split:
            for r in rows:
                r.setdefault("split", default_split)
        return rows

    if suffix == ".npz":
        import numpy as np  # type: ignore

        rows = []
        with np.load(filepath, allow_pickle=False) as npz:
            keys = set(npz.files)
            n = 0
            for k in sorted(keys):
                if npz[k].ndim >= 1:
                    n = int(npz[k].shape[0])
                    break
            for i in range(n):
                rec: Dict[str, Any] = {
                    "split": str(npz["split"][i]) if "split" in keys else (default_split or "train")
                }
                for meta_k in ("demo_id", "round_id", "tick", "x", "y", "z"):
                    if meta_k in keys:
                        val = npz[meta_k][i]
                        rec[meta_k] = float(val) if meta_k in ("x", "y", "z") else str(val)
                for head, aliases in CANONICAL_LABEL_HEADS.items():
                    for al in aliases:
                        if al in keys:
                            rec[head] = str(npz[al][i])
                            break
                rows.append(rec)
        return rows

    raise ValueError(f"Formato de arquivo não suportado: {filepath}")


def audit_support_and_sample_visual(
    rows: List[Dict[str, Any]],
    known_catalog: Dict[str, List[str]],
    max_visual_samples_per_class: int = 2,
) -> Dict[str, Any]:
    """
    Calcula o support por classe e por split para cada um dos 6 cabeçotes de label e extrai
    um subconjunto determinístico de amostras estratificadas (`visual_audit_samples`).
    """
    splits = ("train", "val", "test")
    counters: Dict[str, Dict[str, Counter[str]]] = {
        head: {sp: Counter() for sp in splits} for head in CANONICAL_LABEL_HEADS
    }
    observed_classes: Dict[str, Set[str]] = {
        head: set(known_catalog.get(head, [])) for head in CANONICAL_LABEL_HEADS
    }
    split_row_counts: Dict[str, int] = {"train": 0, "val": 0, "test": 0}
    visual_samples_by_key: Dict[str, List[Dict[str, Any]]] = {}

    for idx, row in enumerate(rows):
        raw_sp = row.get("split", row.get("subset", "train"))
        sp = normalize_split_name(str(raw_sp))
        if sp not in splits:
            continue
        split_row_counts[sp] += 1

        resolved_labels: Dict[str, str] = {}
        for head, aliases in CANONICAL_LABEL_HEADS.items():
            val = None
            for al in aliases:
                if al in row and row[al] is not None:
                    val = str(row[al]).strip()
                    break
            if val is not None and val != "":
                counters[head][sp][val] += 1
                observed_classes[head].add(val)
                resolved_labels[head] = val

        # Amostragem estratificada determinística por (SpotId ou PositioningState)
        strat_key = resolved_labels.get("SpotId", resolved_labels.get("PositioningState", "unlabeled"))
        bucket = visual_samples_by_key.setdefault(f"{sp}:{strat_key}", [])
        if len(bucket) < max_visual_samples_per_class:
            bucket.append(
                {
                    "row_index": idx,
                    "split": sp,
                    "demo_id": row.get("demo_id", row.get("source_demo", "unknown")),
                    "round_id": row.get("round_id", "unknown"),
                    "tick": row.get("tick", None),
                    "coordinates": {
                        "x": row.get("x", row.get("pos_x", None)),
                        "y": row.get("y", row.get("pos_y", None)),
                        "z": row.get("z", row.get("pos_z", None)),
                    },
                    "labels": resolved_labels,
                }
            )

    head_reports: Dict[str, Any] = {}
    support_table: List[Dict[str, Any]] = []
    zero_support_registry: List[Dict[str, Any]] = []

    for head in CANONICAL_LABEL_HEADS:
        all_cls = sorted(observed_classes[head])
        per_split_report: Dict[str, Any] = {}
        for cls_idx, cls_name in enumerate(all_cls):
            tr_c = int(counters[head]["train"].get(cls_name, 0))
            va_c = int(counters[head]["val"].get(cls_name, 0))
            te_c = int(counters[head]["test"].get(cls_name, 0))
            eval_status = "N/A_ZERO_SUPPORT" if (va_c == 0 or te_c == 0) else "EVALUABLE"
            support_table.append(
                {
                    "head": head,
                    "class_id": cls_idx,
                    "class_name": cls_name,
                    "train_count": tr_c,
                    "val_count": va_c,
                    "test_count": te_c,
                    "eval_status": eval_status,
                    "metrics_policy": "N/A_REQUIRED" if (va_c == 0 or te_c == 0) else "STANDARD_METRICS_ALLOWED",
                }
            )

        for sp in splits:
            total_in_split = sum(counters[head][sp].values())
            classes_detail: Dict[str, Any] = {}
            for cls_name in all_cls:
                sup = int(counters[head][sp].get(cls_name, 0))
                policy = "N/A_REQUIRED" if sup == 0 else "STANDARD_METRICS_ALLOWED"
                eval_status = "N/A_ZERO_SUPPORT" if sup == 0 else "EVALUABLE"
                proportion = round(sup / total_in_split, 6) if total_in_split > 0 else None
                classes_detail[cls_name] = {
                    "support": sup,
                    "proportion": proportion,
                    "metrics_policy": policy,
                    "eval_status": eval_status,
                    "recall_when_zero_support": "N/A" if sup == 0 else "COMPUTABLE",
                    "f1_when_zero_support": "N/A" if sup == 0 else "COMPUTABLE",
                }
                if sup == 0:
                    zero_support_registry.append(
                        {
                            "head": head,
                            "split": sp,
                            "class": cls_name,
                            "support": 0,
                            "metrics_policy": "N/A_REQUIRED",
                            "eval_status": "N/A_ZERO_SUPPORT",
                        }
                    )
            per_split_report[sp] = {
                "total_labeled_samples": total_in_split,
                "num_classes_cataloged": len(all_cls),
                "num_classes_with_positive_support": sum(
                    1 for c in all_cls if counters[head][sp].get(c, 0) > 0
                ),
                "num_classes_with_zero_support": sum(
                    1 for c in all_cls if counters[head][sp].get(c, 0) == 0
                ),
                "classes": classes_detail,
            }
        head_reports[head] = per_split_report

    visual_audit_samples: List[Dict[str, Any]] = []
    for k in sorted(visual_samples_by_key.keys()):
        visual_audit_samples.extend(visual_samples_by_key[k])

    return {
        "split_row_counts": split_row_counts,
        "support_table": support_table,
        "heads": head_reports,
        "zero_support_classes_count": len(zero_support_registry),
        "zero_support_classes": zero_support_registry,
        "visual_audit_samples_count": len(visual_audit_samples),
        "visual_audit_samples": visual_audit_samples[:200],
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="audit_label_support.py",
        description=(
            "Audita a distribuição e o suporte (support) de cada classe de label "
            "(PositioningState, NextSector, SpotId, Transition, ExitTrigger, JumpPress) "
            "por split (train, val, test), aplicando a regra 03-zero-support-is-na e exportando amostras visuais."
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
        help="Caminho para arquivo (.parquet, .npz, .json) ou diretório contendo os splits do dataset.",
    )
    parser.add_argument(
        "--schema-json",
        "-s",
        type=str,
        default=None,
        help="Opcional: arquivo JSON listando todas as classes possíveis por head.",
    )
    parser.add_argument(
        "--visual-samples-out",
        type=str,
        default=None,
        help="Opcional: caminho para exportar o arquivo visual_audit_samples.json separadamente.",
    )
    parser.add_argument(
        "--fail-on-empty-head",
        action="store_true",
        help="Se definido, emite veredito FAIL caso algum dos 6 cabeçotes não possua nenhuma amostra em nenhum split.",
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
        help="Executa validação estrutural em modo --dry-run (emite verdict=CONDITIONAL e data_nature=SIMULATED).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.dry_run:
        report: Dict[str, Any] = {
            "script": "audit_label_support.py",
            "mode": "DRY_RUN",
            "data_nature": "SIMULATED",
            "governance_rules": [
                "01-evidence-before-claims",
                "02-no-test-contamination",
                "03-zero-support-is-na",
                "04-synthetic-data-labeling",
            ],
            "audited_heads": list(CANONICAL_LABEL_HEADS.keys()),
            "zero_support_policy": "N/A_REQUIRED",
            "eval_status_when_zero_support": "N/A_ZERO_SUPPORT",
            "visual_audit_samples": [],
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
        print("ERRO: Informe --input / --splits-dir com o arquivo ou diretório do dataset (ou use --dry-run).", file=sys.stderr)
        return 2

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"ERRO: Caminho de entrada não encontrado: {in_path}", file=sys.stderr)
        return 2

    schema_path = Path(args.schema_json).resolve() if args.schema_json else None
    if schema_path and not schema_path.is_file():
        print(f"ERRO: Schema JSON não encontrado: {schema_path}", file=sys.stderr)
        return 2

    artifacts_info: List[Dict[str, str]] = []
    all_rows: List[Dict[str, Any]] = []

    try:
        known_catalog = load_known_classes_schema(schema_path)
        if in_path.is_file():
            artifacts_info.append({"path": str(in_path), "sha256": compute_sha256(in_path)})
            all_rows.extend(extract_rows_from_file(in_path))
        else:
            for f in sorted(in_path.rglob("*")):
                if f.is_file() and f.suffix.lower() in (".parquet", ".npz", ".json"):
                    artifacts_info.append({"path": str(f), "sha256": compute_sha256(f)})
                    inferred_split = None
                    for part in f.parts:
                        norm = normalize_split_name(part)
                        if norm in ("train", "val", "test"):
                            inferred_split = norm
                    all_rows.extend(extract_rows_from_file(f, default_split=inferred_split))
    except Exception as exc:
        print(f"ERRO ao carregar dados para auditoria de suporte: {exc}", file=sys.stderr)
        return 2

    if not all_rows:
        report = {
            "script": "audit_label_support.py",
            "mode": "REAL_AUDIT",
            "data_nature": "REAL",
            "input_artifacts": artifacts_info,
            "total_rows_loaded": 0,
            "verdict": "FAIL",
            "error": "Nenhum registro encontrado nos artefatos informados.",
        }
        if args.output_json:
            out_path = Path(args.output_json).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    support_analysis = audit_support_and_sample_visual(all_rows, known_catalog)

    empty_heads: List[str] = []
    for head, sp_dict in support_analysis["heads"].items():
        total_head = sum(sp_dict[sp]["total_labeled_samples"] for sp in ("train", "val", "test"))
        if total_head == 0:
            empty_heads.append(head)

    verdict = "PASS"
    if len(all_rows) == 0 or (args.fail_on_empty_head and len(empty_heads) > 0):
        verdict = "FAIL"

    visual_samples_path_str: Optional[str] = None
    if args.visual_samples_out:
        vs_path = Path(args.visual_samples_out).resolve()
        vs_path.parent.mkdir(parents=True, exist_ok=True)
        vs_path.write_text(
            json.dumps(support_analysis["visual_audit_samples"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        visual_samples_path_str = str(vs_path)
    elif args.output_json:
        vs_path = Path(args.output_json).resolve().parent / "visual_audit_samples.json"
        vs_path.parent.mkdir(parents=True, exist_ok=True)
        vs_path.write_text(
            json.dumps(support_analysis["visual_audit_samples"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        visual_samples_path_str = str(vs_path)

    report = {
        "script": "audit_label_support.py",
        "mode": "REAL_AUDIT",
        "data_nature": "REAL",
        "governance_rules": [
            "01-evidence-before-claims",
            "02-no-test-contamination",
            "03-zero-support-is-na",
            "04-synthetic-data-labeling",
        ],
        "input_artifacts": artifacts_info,
        "total_rows_loaded": len(all_rows),
        "empty_heads": empty_heads,
        "visual_audit_samples_file": visual_samples_path_str,
        "aggregation_formula": (
            "support(head, split, class) = count(rows where split == s and label[head] == class); "
            "if support == 0 then metrics_policy = 'N/A_REQUIRED' and eval_status = 'N/A_ZERO_SUPPORT' (Rule 03-zero-support-is-na)"
        ),
        **support_analysis,
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
