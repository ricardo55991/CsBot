#!/usr/bin/env python3
"""
Script de verificação determinística de sessão de runtime e artefatos de deploy (csbot-runtime-validation).

Verifica:
- Hashes SHA-256 de artefatos reais (`CsBotManager.dll`, `.onnx`, `de_mirage.json`) quando presentes;
- Log de telemetria real (`!debug`, C4, economia, Jump, recovery, spots, adaptações, selamento da partida).

Regra crítica inegociável:
- NUNCA simula runtime;
- NUNCA cria eventos fictícios;
- Quando não há log de telemetria real ou evento observado, marca explicitamente
  `"status": "ABSENT_TELEMETRY_NA"` (nunca infere `0` por ausência de telemetria).
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict


TELEMETRY_DOMAINS = {
    "debug_command": r"(!debug|\[Debug\]|DebugOverlay)",
    "c4_objective": r"(BombObjective|C4|PlantedBomb|BombCarrier|Defuse)",
    "economy_buy": r"(Economy|BuyDecision|BuyCommand|InventoryConfirm|EconomyManager)",
    "jump_gate": r"(JumpExecutionGate|OnnxJump|JumpRequest|usercmd.*jump)",
    "movement_recovery": r"(MovementArbitrator|RecoveryRequest|StuckRecovery|MicroMoveEngine)",
    "tactical_spots": r"(TacticalSpot|SpotAnchor|GoalPosition|de_mirage|GameplaySpotTelemetry)",
    "online_adaptation": r"(Adaptation|StratAdapter|RoundAdaptation|MidRoundAdapter)",
    "match_sealing": r"(MatchSealed|RoundEnd|SessionSealed|MatchSummary)",
}


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def inspect_artifact(path: Path) -> Dict[str, Any]:
    if path.exists() and path.is_file():
        return {
            "path": str(path),
            "exists": True,
            "size_bytes": path.stat().st_size,
            "sha256": compute_sha256(path),
            "data_nature": "REAL",
        }
    return {
        "path": str(path),
        "exists": False,
        "size_bytes": None,
        "sha256": None,
        "status": "ARTIFACT_NOT_FOUND",
    }


def collect_workspace_artifacts(workspace_root: Path, dll_path_arg: str | None) -> Dict[str, Any]:
    if dll_path_arg:
        dll_candidate = Path(dll_path_arg).resolve()
    else:
        dll_matches = list((workspace_root / "src" / "CsBotManager" / "bin").rglob("CsBotManager.dll"))
        dll_candidate = (
            dll_matches[0].resolve()
            if dll_matches
            else (
                workspace_root
                / "src"
                / "CsBotManager"
                / "bin"
                / "Release"
                / "net8.0"
                / "CsBotManager.dll"
            )
        )

    mirage_profile = workspace_root / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json"
    onnx_files = sorted(workspace_root.rglob("*.onnx"))[:10]

    return {
        "csbot_manager_dll": inspect_artifact(dll_candidate),
        "de_mirage_profile": inspect_artifact(mirage_profile),
        "onnx_models": [inspect_artifact(p.resolve()) for p in onnx_files],
    }


def analyze_telemetry_log(log_path: Path | None, dry_run: bool) -> Dict[str, Any]:
    """Analisa log real de telemetria sem jamais inferir 0 quando o log ou domínio está ausente."""
    if log_path is None or not log_path.exists() or not log_path.is_file():
        return {
            "telemetry_present": False,
            "log_path": str(log_path) if log_path else None,
            "log_sha256": None,
            "status": "ABSENT_TELEMETRY_NA",
            "data_nature": "SIMULATED" if dry_run else "REAL",
            "note": "Nenhum arquivo de log de telemetria real foi fornecido ou encontrado. Proibido simular eventos ou inferir contagem 0.",
            "domains": {
                domain: {
                    "status": "ABSENT_TELEMETRY_NA",
                    "observed_events": "N/A",
                }
                for domain in TELEMETRY_DOMAINS
            },
        }

    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    log_sha256 = compute_sha256(log_path)

    if len(lines) == 0:
        return {
            "telemetry_present": False,
            "log_path": str(log_path),
            "log_sha256": log_sha256,
            "status": "ABSENT_TELEMETRY_NA",
            "data_nature": "SIMULATED" if dry_run else "REAL",
            "note": "Arquivo de log está vazio (0 linhas). Marcado como ABSENT_TELEMETRY_NA.",
            "domains": {
                domain: {
                    "status": "ABSENT_TELEMETRY_NA",
                    "observed_events": "N/A",
                }
                for domain in TELEMETRY_DOMAINS
            },
        }

    domain_report: Dict[str, Any] = {}
    for domain, pattern_str in TELEMETRY_DOMAINS.items():
        regex = re.compile(pattern_str, re.IGNORECASE)
        matched_lines = [idx for idx, line in enumerate(lines, start=1) if regex.search(line)]
        if matched_lines:
            domain_report[domain] = {
                "status": "OBSERVED_IN_REAL_LOG",
                "observed_events": len(matched_lines),
                "first_seen_line": matched_lines[0],
                "last_seen_line": matched_lines[-1],
            }
        else:
            domain_report[domain] = {
                "status": "ABSENT_TELEMETRY_NA",
                "observed_events": "N/A",
            }

    return {
        "telemetry_present": True,
        "log_path": str(log_path),
        "log_sha256": log_sha256,
        "total_lines": len(lines),
        "status": "REAL_LOG_ANALYZED",
        "data_nature": "SIMULATED" if dry_run else "REAL",
        "domains": domain_report,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auditoria determinística de artefatos de build e telemetria real de runtime do servidor CS2."
    )
    parser.add_argument(
        "--workspace-root",
        type=str,
        default=".",
        help="Caminho raiz do workspace CsBot (default: '.').",
    )
    parser.add_argument(
        "--session-dir",
        type=str,
        default=None,
        help="Diretório opcional da sessão de runtime (procura logs *.log/*.txt e grava o relatório nele se --output-json não for informado).",
    )
    parser.add_argument(
        "--telemetry-log",
        type=str,
        default=None,
        help="Caminho opcional para log real de sessão do servidor CS2.",
    )
    parser.add_argument(
        "--dll-path",
        type=str,
        default=None,
        help="Caminho opcional explícito para CsBotManager.dll.",
    )
    parser.add_argument(
        "--output-json",
        "--out",
        dest="output_json",
        type=str,
        default=None,
        help="Caminho para salvar o resultado JSON da auditoria de runtime (default: runtime_validation_report.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa verificação não-destrutiva marcada como data_nature=SIMULATED e veredito CONDITIONAL.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Retorna código 1 se a telemetria real estiver ausente ou artefatos principais não existirem.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace_root = Path(args.workspace_root).resolve()

    session_dir = Path(args.session_dir).resolve() if args.session_dir else None

    if args.output_json:
        output_path = Path(args.output_json).resolve()
    elif session_dir:
        output_path = session_dir / "runtime_validation_report.json"
    else:
        output_path = Path("runtime_validation_report.json").resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log_path: Path | None = None
    if args.telemetry_log:
        log_path = Path(args.telemetry_log).resolve()
    elif session_dir and session_dir.exists():
        candidates = sorted(list(session_dir.glob("*.log")) + list(session_dir.glob("*.txt")))
        if candidates:
            log_path = candidates[0].resolve()

    artifacts = collect_workspace_artifacts(workspace_root, args.dll_path)
    telemetry = analyze_telemetry_log(log_path, args.dry_run)

    mirage_exists = artifacts["de_mirage_profile"]["exists"]
    telemetry_ok = telemetry["status"] == "REAL_LOG_ANALYZED"

    if args.dry_run:
        verdict = "CONDITIONAL"
        data_nature = "SIMULATED"
    elif telemetry_ok and mirage_exists:
        verdict = "PASS"
        data_nature = "REAL"
    elif mirage_exists:
        verdict = "CONDITIONAL"
        data_nature = "REAL"
    else:
        verdict = "FAIL"
        data_nature = "REAL"

    payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "workspace_root": str(workspace_root),
        "session_dir": str(session_dir) if session_dir else None,
        "dry_run": args.dry_run,
        "data_nature": data_nature,
        "simulation_prohibition_enforced": True,
        "status": telemetry["status"],
        "verdict": verdict,
        "artifacts": artifacts,
        "telemetry": telemetry,
    }

    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.strict and (verdict == "FAIL" or telemetry["status"] == "ABSENT_TELEMETRY_NA"):
        return 1
    return 0 if verdict in {"PASS", "CONDITIONAL"} else 1


if __name__ == "__main__":
    sys.exit(main())
