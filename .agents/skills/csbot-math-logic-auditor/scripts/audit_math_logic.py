#!/usr/bin/env python3
"""
scripts/audit_math_logic.py
Skill: csbot-math-logic-auditor

Runner unificado para a auditoria matemática e de lógica temporal do CsBot.
Combina auditoria de matrizes de confusão/calibração com auditoria de transições FSM.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Garante resolução determinística dos módulos da skill
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from audit_confusion_and_calibration import audit_confusion_matrix_invariants
from audit_temporal_transitions import audit_transitions


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Runner unificado da Skill csbot-math-logic-auditor (Matrizes, Calibração e FSM)."
    )
    parser.add_argument(
        "--confusion-counts",
        "--counts",
        dest="confusion_counts",
        type=str,
        default=None,
        help="Caminho do CSV de contagens brutas da matriz de confusão.",
    )
    parser.add_argument(
        "--confusion-normalized",
        "--normalized",
        dest="confusion_normalized",
        type=str,
        default=None,
        help="Caminho do CSV normalizado por linha da matriz de confusão.",
    )
    parser.add_argument(
        "--metrics-json",
        "--metrics",
        dest="metrics_json",
        type=str,
        default=None,
        help="Caminho do JSON de métricas canônicas de avaliação.",
    )
    parser.add_argument(
        "--transitions-json",
        "--transitions",
        dest="transitions_json",
        type=str,
        default=None,
        help="Caminho do JSON contendo histórico de transições de estados FSM.",
    )
    parser.add_argument(
        "--fsm-config",
        "--fsm",
        dest="fsm_config",
        type=str,
        default=None,
        help="Caminho do JSON de configuração de transições da FSM.",
    )
    parser.add_argument(
        "--output-json",
        "--out",
        dest="output_json",
        type=str,
        default="math_logic_audit_report.json",
        help="Caminho de saída para o relatório JSON consolidado de auditoria.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa em modo de autodiagnóstico não-destrutivo com veredito CONDITIONAL e data_nature=SIMULATED.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Encerra com exit code 1 caso violações sejam detectadas.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    output_path = Path(args.output_json).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    counts_p = Path(args.confusion_counts).resolve() if args.confusion_counts else None
    norm_p = Path(args.confusion_normalized).resolve() if args.confusion_normalized else None
    metrics_p = Path(args.metrics_json).resolve() if args.metrics_json else None
    trans_p = Path(args.transitions_json).resolve() if args.transitions_json else None
    fsm_p = Path(args.fsm_config).resolve() if args.fsm_config else None

    math_violations, math_details = audit_confusion_matrix_invariants(
        counts_path=counts_p,
        normalized_path=norm_p,
        metrics_path=metrics_p,
        dry_run=args.dry_run,
    )

    fsm_violations, fsm_details = audit_transitions(
        transitions_path=trans_p,
        fsm_config_path=fsm_p,
        dry_run=args.dry_run,
    )

    total_violations = math_violations + fsm_violations
    has_real_inputs = any((counts_p, norm_p, metrics_p, trans_p))

    if total_violations:
        verdict = "FAIL"
    elif args.dry_run or not has_real_inputs:
        verdict = "CONDITIONAL"
    else:
        verdict = "PASS"

    data_nature = "SIMULATED" if args.dry_run or not has_real_inputs else "REAL"

    consolidated_report = {
        "schema_version": "1.0.0",
        "skill": "csbot-math-logic-auditor",
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "data_nature": data_nature,
        "verdict": verdict,
        "total_violations_count": len(total_violations),
        "violations": total_violations,
        "suites": {
            "confusion_and_calibration": {
                "status": "PASS" if not math_violations else "FAIL",
                "violations_count": len(math_violations),
                "violations": math_violations,
                "details": math_details,
            },
            "temporal_transitions_and_fsm": {
                "status": "PASS" if not fsm_violations else "FAIL",
                "violations_count": len(fsm_violations),
                "violations": fsm_violations,
                "details": fsm_details,
            },
        },
    }

    output_path.write_text(json.dumps(consolidated_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(consolidated_report, indent=2, ensure_ascii=False))

    if verdict == "FAIL" and (args.strict or not args.dry_run):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
