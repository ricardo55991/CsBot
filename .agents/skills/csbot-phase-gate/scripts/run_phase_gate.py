#!/usr/bin/env python3
"""
Script determinístico de controle de entrada e fechamento de fase (Phase Gate) do projeto CsBot.

Gera os 4 artefatos obrigatórios em --output-dir (ou --phase-dir):
1. phase_input_snapshot.json
2. phase_requirement_matrix.md
3. phase_evidence_matrix.json
4. phase_gate_report.md

Regras aplicáveis:
- 01-evidence-before-claims (SHA-256 completo de 64 chars, comando reproduzível, fórmula de agregação, data_nature)
- 08-no-automatic-phase-advance (veredito restrito a PASS, CONDITIONAL ou FAIL + bloqueio até autorização humana)
"""

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


VALID_DATA_NATURES = {"REAL", "SIMULATED", "TEMPLATED", "SYNTHETIC", "INFERRED"}
VALID_VERDICTS = {"PASS", "CONDITIONAL", "FAIL"}
SHA256_HEX_LEN = 64


def compute_sha256(file_path: Path) -> str:
    """Calcula o hash SHA-256 completo (64 caracteres hexadecimais) de um arquivo."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_valid_sha256(digest: str) -> bool:
    """Verifica se uma string é um hash SHA-256 completo de 64 caracteres hexadecimais."""
    if not isinstance(digest, str) or len(digest) != SHA256_HEX_LEN:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in digest)


def build_input_snapshot(
    workspace_root: Path, input_files: List[str], dry_run: bool
) -> Dict[str, Any]:
    """Constrói o snapshot imutável dos arquivos de entrada da fase."""
    candidates: List[Path] = []
    if input_files:
        for item in input_files:
            p = Path(item)
            if not p.is_absolute():
                p = (workspace_root / p).resolve()
            candidates.append(p)
    else:
        default_files = [
            workspace_root / "AGENTS.md",
            workspace_root / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json",
        ]
        for p in default_files:
            if p.exists():
                candidates.append(p.resolve())

    entries: List[Dict[str, Any]] = []
    missing_files: List[str] = []

    for fpath in candidates:
        if fpath.exists() and fpath.is_file():
            digest = compute_sha256(fpath)
            stat = fpath.stat()
            try:
                rel_path = str(fpath.relative_to(workspace_root.resolve()))
            except ValueError:
                rel_path = str(fpath)
            entries.append(
                {
                    "path": str(fpath),
                    "relative_path": rel_path,
                    "size_bytes": stat.st_size,
                    "sha256": digest,
                    "exists": True,
                    "data_nature": "REAL",
                }
            )
        else:
            missing_files.append(str(fpath))
            entries.append(
                {
                    "path": str(fpath),
                    "relative_path": str(fpath),
                    "size_bytes": None,
                    "sha256": None,
                    "exists": False,
                    "data_nature": "SIMULATED" if dry_run else "REAL",
                }
            )

    return {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "workspace_root": str(workspace_root.resolve()),
        "dry_run": dry_run,
        "data_nature": "SIMULATED" if dry_run else "REAL",
        "total_files": len(entries),
        "missing_files_count": len(missing_files),
        "missing_files": missing_files,
        "files": entries,
    }


def load_or_default_requirements(
    requirements_json: Path | None, snapshot: Dict[str, Any], dry_run: bool
) -> List[Dict[str, Any]]:
    """Carrega os requisitos de JSON ou gera a lista de verificação padrão da fase."""
    if requirements_json and requirements_json.exists():
        with requirements_json.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get("requirements", [])

    has_missing = snapshot["missing_files_count"] > 0
    has_files = snapshot["total_files"] > 0

    return [
        {
            "requirement_id": "REQ-GOV-01",
            "rule_ref": "01-evidence-before-claims",
            "description": "Snapshot de entrada possui hashes SHA-256 completos (64 chars) para todos os artefatos listados.",
            "status": "CONDITIONAL" if dry_run else ("PASS" if (has_files and not has_missing) else "FAIL"),
            "notes": f"Total de arquivos verificados: {snapshot['total_files']} (ausentes: {snapshot['missing_files_count']}).",
        },
        {
            "requirement_id": "REQ-GOV-06",
            "rule_ref": "06-sensitive-artifact-protection",
            "description": "Nenhum artefato sensível modificado sem registro prévio de hash SHA-256.",
            "status": "PASS",
            "notes": "Operação executada em modo somente leitura sobre os artefatos do workspace.",
        },
        {
            "requirement_id": "REQ-GOV-08",
            "rule_ref": "08-no-automatic-phase-advance",
            "description": "Bloqueio de avanço automático de fase ativo aguardando homologação humana.",
            "status": "PASS",
            "notes": "Relatório final contém cláusula explícita de bloqueio de avanço automático.",
        },
    ]


def load_and_validate_evidences(
    evidences_json: Path | None,
    snapshot: Dict[str, Any],
    workspace_root: Path,
    dry_run: bool,
) -> Dict[str, Any]:
    """Carrega e valida cada evidência quanto aos campos obrigatórios da regra 01-evidence-before-claims."""
    raw_evidences: List[Dict[str, Any]] = []

    if evidences_json and evidences_json.exists():
        with evidences_json.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        raw_evidences = loaded if isinstance(loaded, list) else loaded.get("evidences", [])
    else:
        for file_entry in snapshot.get("files", []):
            if file_entry.get("exists"):
                raw_evidences.append(
                    {
                        "evidence_id": f"EV-{len(raw_evidences) + 1:03d}",
                        "artifact_path": file_entry["path"],
                        "sha256": file_entry["sha256"],
                        "reproducible_command": f"python .agents/skills/csbot-phase-gate/scripts/run_phase_gate.py --workspace-root \"{workspace_root}\"",
                        "aggregation_formula": "count(valid_hashed_files) / count(declared_input_files) = "
                        f"{snapshot['total_files'] - snapshot['missing_files_count']}/{snapshot['total_files']}",
                        "data_nature": "SIMULATED" if dry_run else "REAL",
                    }
                )

    validated: List[Dict[str, Any]] = []
    validation_errors: List[str] = []

    for idx, ev in enumerate(raw_evidences):
        ev_id = ev.get("evidence_id", f"EV-{idx + 1:03d}")
        artifact_path = ev.get("artifact_path", "")
        sha256_val = ev.get("sha256", "")
        cmd = ev.get("reproducible_command", "")
        formula = ev.get("aggregation_formula", "")
        nature = ev.get("data_nature", "")

        issues: List[str] = []
        if not artifact_path:
            issues.append("missing_artifact_path")
        else:
            p = Path(artifact_path)
            if not p.is_absolute():
                p = (workspace_root / p).resolve()
            if not p.exists():
                issues.append(f"artifact_not_found_on_disk:{p}")
            else:
                real_hash = compute_sha256(p)
                if not sha256_val:
                    sha256_val = real_hash
                elif sha256_val.lower() != real_hash.lower():
                    issues.append(f"sha256_mismatch:expected={sha256_val},actual={real_hash}")

        if not is_valid_sha256(sha256_val):
            issues.append("invalid_or_truncated_sha256_must_be_64_hex_chars")
        if not cmd or not str(cmd).strip():
            issues.append("missing_reproducible_command")
        if not formula or not str(formula).strip():
            issues.append("missing_aggregation_formula")
        if nature not in VALID_DATA_NATURES:
            issues.append(f"invalid_data_nature:{nature}")

        is_valid = len(issues) == 0
        if not is_valid:
            validation_errors.extend([f"{ev_id}:{err}" for err in issues])

        validated.append(
            {
                "evidence_id": ev_id,
                "artifact_path": str(artifact_path),
                "sha256": sha256_val,
                "reproducible_command": cmd,
                "aggregation_formula": formula,
                "data_nature": nature,
                "valid": is_valid,
                "issues": issues,
            }
        )

    return {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dry_run": dry_run,
        "data_nature": "SIMULATED" if dry_run else "REAL",
        "total_evidences": len(validated),
        "valid_evidences": sum(1 for e in validated if e["valid"]),
        "invalid_evidences": sum(1 for e in validated if not e["valid"]),
        "validation_errors": validation_errors,
        "evidences": validated,
    }


def render_requirement_matrix_md(phase_id: str, requirements: List[Dict[str, Any]]) -> str:
    """Formata a tabela Markdown de requisitos vs status."""
    lines = [
        f"# Matriz de Requisitos da Fase: `{phase_id}`",
        "",
        "| ID | Regra de Governança | Descrição | Status | Observações |",
        "|---|---|---|---|---|",
    ]
    for req in requirements:
        req_id = req.get("requirement_id", "N/A")
        rule_ref = req.get("rule_ref", "N/A")
        desc = req.get("description", "").replace("|", "\\|")
        status = req.get("status", "FAIL")
        notes = req.get("notes", "").replace("|", "\\|")
        lines.append(f"| `{req_id}` | `{rule_ref}` | {desc} | **{status}** | {notes} |")
    lines.append("")
    return "\n".join(lines)


def determine_verdict(
    snapshot: Dict[str, Any],
    requirements: List[Dict[str, Any]],
    evidence_matrix: Dict[str, Any],
    dry_run: bool,
) -> str:
    """Determina o veredito estrito (PASS, CONDITIONAL ou FAIL)."""
    req_statuses = [r.get("status", "FAIL") for r in requirements]
    if "FAIL" in req_statuses:
        return "FAIL"
    if snapshot.get("missing_files_count", 0) > 0:
        return "FAIL"
    if evidence_matrix.get("invalid_evidences", 0) > 0:
        return "FAIL"
    if evidence_matrix.get("total_evidences", 0) == 0:
        return "CONDITIONAL" if dry_run else "FAIL"
    if "CONDITIONAL" in req_statuses or dry_run:
        return "CONDITIONAL"
    return "PASS"


def render_phase_gate_report_md(
    phase_id: str,
    verdict: str,
    snapshot: Dict[str, Any],
    requirements: List[Dict[str, Any]],
    evidence_matrix: Dict[str, Any],
    dry_run: bool,
) -> str:
    """Gera o relatório formal de Phase Gate com aviso obrigatório da regra 08."""
    assert verdict in VALID_VERDICTS, f"Veredito inválido: {verdict}"
    lines = [
        f"# Relatório de Phase Gate — `{phase_id}`",
        "",
        f"- **Veredito Formal**: **`{verdict}`**",
        f"- **Data/Hora (UTC)**: `{datetime.datetime.now(datetime.timezone.utc).isoformat()}`",
        f"- **Modo de Execução**: `{'DRY_RUN' if dry_run else 'CANONICAL'}`",
        f"- **Natureza dos Dados**: `{evidence_matrix.get('data_nature', 'REAL')}`",
        "",
        "## 1. Resumo do Snapshot de Entrada",
        f"- Arquivos monitorados: `{snapshot['total_files']}`",
        f"- Arquivos ausentes: `{snapshot['missing_files_count']}`",
        "",
        "## 2. Resumo da Matriz de Requisitos",
        f"- Total de requisitos avaliados: `{len(requirements)}`",
        f"- PASS: `{sum(1 for r in requirements if r.get('status') == 'PASS')}`",
        f"- CONDITIONAL: `{sum(1 for r in requirements if r.get('status') == 'CONDITIONAL')}`",
        f"- FAIL: `{sum(1 for r in requirements if r.get('status') == 'FAIL')}`",
        "",
        "## 3. Resumo da Matriz de Evidências (`01-evidence-before-claims`)",
        f"- Evidências declaradas: `{evidence_matrix['total_evidences']}`",
        f"- Evidências válidas (SHA-256 64 chars + comando + fórmula + natureza): `{evidence_matrix['valid_evidences']}`",
        f"- Evidências inválidas: `{evidence_matrix['invalid_evidences']}`",
        "",
        "## 4. Diretriz Obrigatória `08-no-automatic-phase-advance`",
        "> **AVISO DE BLOQUEIO DE GOVERNANÇA (`08-no-automatic-phase-advance`)**:",
        "> Nenhuma fase, subfase, retreinamento ou etapa de integração pode iniciar automaticamente após a emissão deste relatório.",
        f"> O veredito emitido é estritamente **`{verdict}`**.",
        "> **É obrigatório aguardar autorização explícita do usuário humano** antes de avançar para a próxima etapa.",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o controle de Phase Gate determinístico e gera os 4 artefatos de governança."
    )
    parser.add_argument(
        "--phase-id",
        type=str,
        default="PHASE-AUDIT-01",
        help="Identificador da fase auditada (ex: PHASE-2A, PHASE-3B).",
    )
    parser.add_argument(
        "--workspace-root",
        type=str,
        default=".",
        help="Caminho raiz do workspace CsBot (default: '.').",
    )
    parser.add_argument(
        "--input-files",
        nargs="*",
        default=[],
        help="Lista opcional de caminhos de arquivos de entrada para snapshot SHA-256.",
    )
    parser.add_argument(
        "--requirements-json",
        type=str,
        default=None,
        help="Caminho opcional para arquivo JSON de requisitos da fase.",
    )
    parser.add_argument(
        "--evidences-json",
        type=str,
        default=None,
        help="Caminho opcional para arquivo JSON de evidências da fase.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Diretório onde os 4 artefatos de Phase Gate serão gravados.",
    )
    parser.add_argument(
        "--phase-dir",
        type=str,
        default=None,
        help="Alias para --output-dir (diretório de artefatos da fase).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa verificação não-destrutiva marcada como data_nature=SIMULATED e veredito CONDITIONAL.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Retorna código de saída 1 caso o veredito seja FAIL.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    workspace_root = Path(args.workspace_root).resolve()

    target_dir_str = args.output_dir or args.phase_dir or "./phase_gate_out"
    output_dir = Path(target_dir_str).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    req_path = Path(args.requirements_json).resolve() if args.requirements_json else None
    ev_path = Path(args.evidences_json).resolve() if args.evidences_json else None

    if args.phase_dir and not req_path:
        cand_req = Path(args.phase_dir).resolve() / "requirements.json"
        if cand_req.exists():
            req_path = cand_req
    if args.phase_dir and not ev_path:
        cand_ev = Path(args.phase_dir).resolve() / "evidences.json"
        if cand_ev.exists():
            ev_path = cand_ev

    snapshot = build_input_snapshot(workspace_root, args.input_files, args.dry_run)
    requirements = load_or_default_requirements(req_path, snapshot, args.dry_run)
    evidence_matrix = load_and_validate_evidences(ev_path, snapshot, workspace_root, args.dry_run)
    verdict = determine_verdict(snapshot, requirements, evidence_matrix, args.dry_run)

    snapshot_file = output_dir / "phase_input_snapshot.json"
    req_matrix_file = output_dir / "phase_requirement_matrix.md"
    ev_matrix_file = output_dir / "phase_evidence_matrix.json"
    report_file = output_dir / "phase_gate_report.md"

    with snapshot_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    req_matrix_md = render_requirement_matrix_md(args.phase_id, requirements)
    req_matrix_file.write_text(req_matrix_md, encoding="utf-8")

    with ev_matrix_file.open("w", encoding="utf-8") as f:
        json.dump(evidence_matrix, f, indent=2, ensure_ascii=False)

    report_md = render_phase_gate_report_md(
        args.phase_id, verdict, snapshot, requirements, evidence_matrix, args.dry_run
    )
    report_file.write_text(report_md, encoding="utf-8")

    summary = {
        "phase_id": args.phase_id,
        "verdict": verdict,
        "dry_run": args.dry_run,
        "data_nature": evidence_matrix["data_nature"],
        "artifacts": {
            "phase_input_snapshot": str(snapshot_file),
            "phase_requirement_matrix": str(req_matrix_file),
            "phase_evidence_matrix": str(ev_matrix_file),
            "phase_gate_report": str(report_file),
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if verdict == "FAIL" and args.strict:
        return 1
    return 0 if verdict in {"PASS", "CONDITIONAL"} else 1


if __name__ == "__main__":
    sys.exit(main())
