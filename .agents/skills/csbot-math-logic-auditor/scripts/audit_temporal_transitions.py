#!/usr/bin/env python3
"""
scripts/audit_temporal_transitions.py
Skill: csbot-math-logic-auditor

Audita a integridade da lógica temporal e da máquina de estados (FSM) do agente:
1. Valida conformidade das transições com o grafo de estados autorizados do CS2.
2. Detecta transições ilegais ou impossíveis (ex: SPAWN -> PLANT_C4, ENGAGE_COMBAT -> PLANT_C4).
3. Audita tempos físicos mínimos de motor (plant C4 >= 3.0s, defuse C4 >= 5.0s).
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

DEFAULT_ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "SPAWN": {"NAVIGATE", "HOLD_ANGLE", "SEARCH", "POST_ROUND", "SPAWN"},
    "NAVIGATE": {"NAVIGATE", "HOLD_ANGLE", "SEARCH", "ENGAGE_COMBAT", "PLANT_C4", "DEFUSE_C4", "RETAKE", "POST_ROUND"},
    "HOLD_ANGLE": {"HOLD_ANGLE", "NAVIGATE", "SEARCH", "ENGAGE_COMBAT", "POST_ROUND"},
    "SEARCH": {"SEARCH", "NAVIGATE", "HOLD_ANGLE", "ENGAGE_COMBAT", "RETAKE", "POST_ROUND"},
    "ENGAGE_COMBAT": {"ENGAGE_COMBAT", "NAVIGATE", "HOLD_ANGLE", "SEARCH", "RETAKE", "POST_ROUND"},
    "PLANT_C4": {"PLANT_C4", "NAVIGATE", "HOLD_ANGLE", "ENGAGE_COMBAT", "POST_ROUND"},
    "DEFUSE_C4": {"DEFUSE_C4", "NAVIGATE", "HOLD_ANGLE", "ENGAGE_COMBAT", "POST_ROUND"},
    "RETAKE": {"RETAKE", "NAVIGATE", "SEARCH", "ENGAGE_COMBAT", "DEFUSE_C4", "POST_ROUND"},
    "POST_ROUND": {"POST_ROUND", "SPAWN"},
}

MIN_DURATIONS: Dict[str, float] = {
    "PLANT_C4": 3.0,
    "DEFUSE_C4": 5.0,
}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audita transições temporais e FSM do CsBot contra invariantes físicas do CS2."
    )
    parser.add_argument(
        "--transitions-json",
        "--transitions",
        dest="transitions_json",
        type=str,
        default=None,
        help="Caminho do arquivo JSON de telemetria ou log contendo transições de estados.",
    )
    parser.add_argument(
        "--fsm-config",
        "--fsm",
        dest="fsm_config",
        type=str,
        default=None,
        help="Caminho opcional do arquivo de configuração do grafo de estados FSM.",
    )
    parser.add_argument(
        "--output-json",
        "--out",
        dest="output_json",
        type=str,
        default="temporal_transitions_audit.json",
        help="Caminho de saída para o relatório JSON de auditoria temporal.",
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


def audit_transitions(
    transitions_path: Optional[Path],
    fsm_config_path: Optional[Path],
    dry_run: bool,
) -> Tuple[List[str], Dict[str, Any]]:
    violations: List[str] = []
    details: Dict[str, Any] = {
        "total_transitions_evaluated": 0,
        "valid_transitions_count": 0,
        "illegal_transitions_count": 0,
        "timing_violations_count": 0,
        "fsm_graph_compliance": True,
    }

    if dry_run or not transitions_path:
        details.update(
            {
                "dry_run_simulation": True,
                "total_transitions_evaluated": 120,
                "valid_transitions_count": 120,
                "illegal_transitions_count": 0,
                "timing_violations_count": 0,
                "fsm_graph_compliance": True,
                "simulated_states": list(DEFAULT_ALLOWED_TRANSITIONS.keys()),
            }
        )
        return violations, details

    allowed_map = DEFAULT_ALLOWED_TRANSITIONS
    if fsm_config_path and fsm_config_path.exists():
        try:
            with fsm_config_path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg.get("allowed_transitions"), dict):
                allowed_map = {k: set(v) for k, v in cfg["allowed_transitions"].items()}
        except Exception as e:
            violations.append(f"Erro ao carregar configuração da FSM: {e}")

    try:
        with transitions_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        transitions = data if isinstance(data, list) else data.get("transitions", [])
        details["total_transitions_evaluated"] = len(transitions)

        for idx, trans in enumerate(transitions):
            from_st = trans.get("from_state") or trans.get("from")
            to_st = trans.get("to_state") or trans.get("to")
            duration = trans.get("duration_seconds") or trans.get("duration")

            if from_st and to_st:
                allowed_next = allowed_map.get(from_st, set())
                if to_st not in allowed_next:
                    details["illegal_transitions_count"] += 1
                    violations.append(
                        f"[Lógica Temporal / FSM] Transição ilegal detectada no passo {idx}: '{from_st}' -> '{to_st}' (não permitida pelo grafo de estados CS2)."
                    )
                else:
                    details["valid_transitions_count"] += 1

            if from_st in MIN_DURATIONS and duration is not None:
                min_req = MIN_DURATIONS[from_st]
                if float(duration) < min_req:
                    details["timing_violations_count"] += 1
                    violations.append(
                        f"[Lógica Temporal / CS2 Engine] Estado '{from_st}' com duração de {duration:.2f}s abaixo do mínimo físico permitido de {min_req:.2f}s no passo {idx}."
                    )

    except Exception as e:
        violations.append(f"Falha ao ler transições de {transitions_path}: {e}")

    details["fsm_graph_compliance"] = len(violations) == 0
    return violations, details


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    output_path = Path(args.output_json).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    t_path = Path(args.transitions_json).resolve() if args.transitions_json else None
    fsm_path = Path(args.fsm_config).resolve() if args.fsm_config else None

    violations, details = audit_transitions(t_path, fsm_path, args.dry_run)

    if violations:
        verdict = "FAIL"
    elif args.dry_run or not t_path:
        verdict = "CONDITIONAL"
    else:
        verdict = "PASS"

    data_nature = "SIMULATED" if args.dry_run or not t_path else "REAL"

    report = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "data_nature": data_nature,
        "verdict": verdict,
        "violations_count": len(violations),
        "violations": violations,
        "details": details,
    }

    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if verdict == "FAIL" and (args.strict or not args.dry_run):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
