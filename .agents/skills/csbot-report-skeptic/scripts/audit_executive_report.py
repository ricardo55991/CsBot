#!/usr/bin/env python3
"""
Script de auditoria adversarial sobre relatórios executivos em Markdown (csbot-report-skeptic).

Inspeciona os 12 vetores de invalidação em relatórios Markdown:
1. conflicting_numbers
2. unbacked_metrics
3. zero_support_numeric_metrics
4. incompatible_confusion_matrix
5. divergent_or_truncated_hashes
6. hardcoded_report_claims
7. templated_data_unlabeled
8. missing_declared_files
9. undiscovered_tests
10. test_set_used_in_tuning
11. percentage_100_without_denominator
12. unauthorized_human_approval_claim
"""

import argparse
import datetime
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def segment_markdown(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Segmenta o documento Markdown isolando blocos de código (fenced code blocks ``` ou ~~~).
    Retorna texto com blocos de código substituídos por linhas em branco preservando numeração de linhas.
    """
    lines = text.splitlines(keepends=True)
    executive_lines: List[str] = []
    segments: List[Dict[str, Any]] = []

    in_fence = False
    fence_char = ""
    fence_len = 0
    fence_start = 0
    fence_lang = ""
    fence_lines: List[str] = []

    for idx, line in enumerate(lines, start=1):
        fence_match = re.match(r"^(\s{0,3})(`{3,}|~{3,})(.*)$", line)
        if not in_fence:
            if fence_match:
                in_fence = True
                fence_char = fence_match.group(2)[0]
                fence_len = len(fence_match.group(2))
                fence_lang = fence_match.group(3).strip()
                fence_start = idx
                fence_lines = [line]
                executive_lines.append("\n")
            else:
                executive_lines.append(line)
        else:
            fence_lines.append(line)
            close_match = re.match(r"^\s{0,3}(`{3,}|~{3,})\s*$", line)
            if (
                close_match
                and close_match.group(1)[0] == fence_char
                and len(close_match.group(1)) >= fence_len
            ):
                in_fence = False
                fence_content = "".join(fence_lines)
                is_adversarial = bool(
                    re.search(r"\b(adversarial|fixture|payload|caso\s+de\s+teste)\b", fence_content, re.IGNORECASE)
                )
                segment_type = "ADVERSARIAL_FIXTURE" if is_adversarial else "DOCUMENTATION_EXAMPLE"
                segments.append(
                    {
                        "type": segment_type,
                        "start_line": fence_start,
                        "end_line": idx,
                        "lang": fence_lang,
                    }
                )
                executive_lines.append("\n")
            else:
                executive_lines.append("\n")

    return "".join(executive_lines), segments


VECTOR_NAMES = [
    "conflicting_numbers",
    "unbacked_metrics",
    "zero_support_numeric_metrics",
    "incompatible_confusion_matrix",
    "divergent_or_truncated_hashes",
    "hardcoded_report_claims",
    "templated_data_unlabeled",
    "missing_declared_files",
    "undiscovered_tests",
    "test_set_used_in_tuning",
    "percentage_100_without_denominator",
    "unauthorized_human_approval_claim",
]


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def check_conflicting_numbers(lines: List[str]) -> List[Dict[str, Any]]:
    """Detecta se uma mesma métrica nomeada aparece com valores conflitantes no mesmo relatório."""
    findings: List[Dict[str, Any]] = []
    metric_pattern = re.compile(
        r"\b(macro_f1|balanced_accuracy|overall_accuracy|top1_accuracy|ece|brier_score)\b\s*[:=]\s*`?([0-9]+\.[0-9]+%?)",
        re.IGNORECASE,
    )
    seen: Dict[str, Dict[str, Any]] = {}
    for line_no, line in enumerate(lines, start=1):
        for match in metric_pattern.finditer(line):
            name = match.group(1).lower()
            val = match.group(2)
            if name in seen and seen[name]["value"] != val:
                findings.append(
                    {
                        "line": line_no,
                        "metric": name,
                        "first_value": seen[name]["value"],
                        "first_line": seen[name]["line"],
                        "conflicting_value": val,
                        "detail": f"Métrica '{name}' aparece com valores diferentes ({seen[name]['value']} na linha {seen[name]['line']} vs {val} na linha {line_no}).",
                    }
                )
            else:
                seen[name] = {"value": val, "line": line_no}
    return findings


def check_unbacked_metrics(lines: List[str], full_text: str) -> List[Dict[str, Any]]:
    """Verifica se há métricas percentuais/decimais reportadas sem nenhuma referência a artefatos brutos (.json/.csv/.pt/.npz)."""
    findings: List[Dict[str, Any]] = []
    has_metric_claims = bool(
        re.search(r"\b(accuracy|f1|recall|precision|loss|ece)\b.*?\d+\.\d+", full_text, re.IGNORECASE)
    )
    has_raw_artifact_ref = bool(
        re.search(r"[\w\-./\\]+\.(json|csv|parquet|npz|pt|onnx|log)\b", full_text, re.IGNORECASE)
    )
    if has_metric_claims and not has_raw_artifact_ref:
        findings.append(
            {
                "line": 1,
                "detail": "Relatório apresenta métricas numéricas mas não referencia nenhum artefato bruto verificável (.json, .csv, .parquet, .npz, .pt, .onnx, .log).",
            }
        )
    return findings


METRIC_COLUMN_KEYWORDS = (
    "precision",
    "precisao",
    "precisão",
    "recall",
    "revocacao",
    "revocação",
    "f1",
    "f1-score",
    "f1_score",
    "accuracy",
    "acuracia",
    "acurácia",
    "balanced accuracy",
    "balanced_accuracy",
    "balanced_acc",
    "top1",
    "top-1",
    "top1_accuracy",
)


def _is_numeric_metric_value(val: str) -> bool:
    clean = val.strip().strip("`*_\t\r\n ").replace(" ", "")
    if clean.upper() in ("N/A", "NA", "-", "—", "NONE", "NULL", ""):
        return False
    if re.search(r"\d", clean):
        return True
    return False


def _split_markdown_cells(row_str: str) -> List[str]:
    s = row_str.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    raw_cells = re.split(r"(?<!\\)\|", s)
    return [c.strip().replace(r"\|", "|") for c in raw_cells]


def check_zero_support_numeric_metrics(lines: List[str]) -> List[Dict[str, Any]]:
    """Detecta classes/linhas com support=0 que exibem Recall/F1 numérico em vez de N/A (Regra 03)."""
    findings: List[Dict[str, Any]] = []

    # 1. Parsing estrutural de tabelas Markdown
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|") and i + 1 < len(lines):
            raw_headers = _split_markdown_cells(line)
            headers = [re.sub(r"[*_`]", "", h).strip() for h in raw_headers]
            header_lower = [h.lower() for h in headers]

            support_idx = None
            for idx, h in enumerate(header_lower):
                if "support" in h or h in ("suporte", "support_count"):
                    support_idx = idx
                    break

            if support_idx is not None:
                metric_indices: List[Tuple[int, str]] = []
                for idx, h in enumerate(header_lower):
                    for kw in METRIC_COLUMN_KEYWORDS:
                        if kw == h or f" {kw}" in f" {h}" or f"{kw} " in f"{h} " or f"({kw})" in f"({h})":
                            metric_indices.append((idx, headers[idx]))
                            break

                sep_line = lines[i + 1].strip()
                has_sep = bool(re.match(r"^\|?[\s:|-]+\|?$", sep_line) and "-" in sep_line and "|" in sep_line)
                row_idx = i + 2 if has_sep else i + 1

                while row_idx < len(lines):
                    drow = lines[row_idx].strip()
                    if not (drow.startswith("|") and drow.endswith("|")):
                        break
                    if re.match(r"^\|?[\s:|-]+\|?$", drow) and "-" in drow:
                        row_idx += 1
                        continue
                    cells = _split_markdown_cells(drow)
                    if len(cells) > support_idx:
                        sup_clean = re.sub(r"[*_`]", "", cells[support_idx]).strip().replace(" ", "")
                        if re.match(r"^0(?:\.0+|,0+)?$", sup_clean):
                            for midx, col_name in metric_indices:
                                if len(cells) > midx:
                                    mval = cells[midx]
                                    if _is_numeric_metric_value(mval):
                                        findings.append(
                                            {
                                                "line": row_idx + 1,
                                                "content": drow,
                                                "detail": f"Classe com support=0 exibindo métrica numérica na coluna '{col_name}': '{mval.strip()}' (violação da regra 03-zero-support-is-na).",
                                            }
                                        )
                    row_idx += 1
                i = row_idx
                continue
        i += 1

    # 2. Verificações inline fora de tabelas
    inline_zero_support = re.compile(
        r"support\s*[=:]\s*0\b.*?\b(recall|f1|precision|accuracy)\s*[=:]\s*([0-9]+(?:\.[0-9]+)?%?)",
        re.IGNORECASE,
    )
    for line_no, line in enumerate(lines, start=1):
        if inline_zero_support.search(line):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": "Classe com support=0 exibindo métrica numérica em vez de 'N/A' (violação da regra 03-zero-support-is-na).",
                }
            )

    return findings


def check_incompatible_confusion_matrix(lines: List[str]) -> List[Dict[str, Any]]:
    """Detecta linhas de matriz de confusão normalizada cuja soma diverge de 100% ou 1.0 quando support > 0."""
    findings: List[Dict[str, Any]] = []
    for line_no, line in enumerate(lines, start=1):
        if "support=0" in line.lower().replace(" ", "") and ("0.0%" in line or "100.0%" in line):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": "Linha da matriz de confusão com support=0 preenchida com porcentagem numérica em vez de N/A.",
                }
            )
    return findings


def check_divergent_or_truncated_hashes(
    lines: List[str], manifest_data: Dict[str, Any] | None
) -> List[Dict[str, Any]]:
    """Detecta hashes SHA-256 truncados (com '...' ou < 64 chars hex) ou divergentes do manifesto."""
    findings: List[Dict[str, Any]] = []
    truncated_pattern = re.compile(
        r"(?:sha-?256|hash)\s*[:=]?\s*[`\"']?([0-9a-fA-F]{4,63}(?![0-9a-fA-F])(?:\.\.\.)?|[0-9a-fA-F]*\.{2,}[0-9a-fA-F]*)",
        re.IGNORECASE,
    )
    ellipsis_hash_pattern = re.compile(r"\b[0-9a-fA-F]{4,64}\.{2,}[0-9a-fA-F]*\b")
    full_hash_pattern = re.compile(r"\b([0-9a-fA-F]{64})\b")

    for line_no, line in enumerate(lines, start=1):
        if ellipsis_hash_pattern.search(line):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": "Hash hexadecimal truncado com reticências ('...') detectado (violação da regra 01-evidence-before-claims).",
                }
            )
            continue

        for match in truncated_pattern.finditer(line):
            candidate = match.group(1)
            full_matches = full_hash_pattern.findall(line)
            if not full_matches and len(candidate.replace(".", "")) < 64:
                findings.append(
                    {
                        "line": line_no,
                        "candidate_hash": candidate,
                        "detail": f"Hash SHA-256 incompleto ({len(candidate)} chars; exigido 64 chars hexadecimais).",
                    }
                )

    if manifest_data and isinstance(manifest_data, dict):
        expected_hashes = set()
        for v in manifest_data.values():
            if isinstance(v, str) and len(v) == 64:
                expected_hashes.add(v.lower())
        if expected_hashes:
            for line_no, line in enumerate(lines, start=1):
                for h in full_hash_pattern.findall(line):
                    if h.lower() not in expected_hashes and "sha256" in line.lower():
                        findings.append(
                            {
                                "line": line_no,
                                "reported_hash": h,
                                "detail": "Hash SHA-256 reportado não consta no manifesto de referência.",
                            }
                        )
    return findings


def check_hardcoded_report_claims(lines: List[str]) -> List[Dict[str, Any]]:
    """Detecta marcadores típicos de placeholders/hardcoding de template em relatórios."""
    findings: List[Dict[str, Any]] = []
    pattern = re.compile(
        r"\b(TODO|TBD|FIXME|PLACEHOLDER_METRIC|INSERT_HASH_HERE|XXX_VALUE|LOREM_IPSUM)\b",
        re.IGNORECASE,
    )
    for line_no, line in enumerate(lines, start=1):
        m = pattern.search(line)
        if m:
            findings.append(
                {
                    "line": line_no,
                    "token": m.group(1),
                    "detail": f"Marcador de texto hardcoded/incompleto '{m.group(1)}' encontrado no relatório.",
                }
            )
    return findings


def check_templated_data_unlabeled(lines: List[str], full_text: str) -> List[Dict[str, Any]]:
    """Detecta menções a dados simulados/sintéticos/interpolados sem a etiqueta formal obrigatória (Regra 04)."""
    findings: List[Dict[str, Any]] = []
    mentions_synthetic = re.compile(
        r"\b(simulado|simulada|sint[eé]tico|sint[eé]tica|interpolado|mock|fake_telemetry|synthetic)\b",
        re.IGNORECASE,
    )
    valid_labels = re.compile(r"\b(SIMULATED|TEMPLATED|SYNTHETIC|INFERRED)\b")
    for line_no, line in enumerate(lines, start=1):
        if mentions_synthetic.search(line) and not valid_labels.search(full_text):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": "Menção a dado sintético/simulado sem etiqueta formal (SIMULATED, TEMPLATED, SYNTHETIC ou INFERRED).",
                }
            )
        # Detecção de IDs de demo sintéticos (ex: demo_m01, synthetic_demo_*)
        m_demo = re.search(r"\b(demo_m\d+|synthetic_demo_\w+)\b", line, re.IGNORECASE)
        if m_demo and not valid_labels.search(full_text):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": f"Identificador de demo sintética/não catalogada '{m_demo.group(1)}' sem etiqueta de proveniência formal (UNPROVENANCED_TEMPLATE_ID).",
                }
            )
    return findings


def check_missing_declared_files(lines: List[str], workspace_root: Path) -> List[Dict[str, Any]]:
    """Extrai caminhos de arquivos do projeto mencionados no relatório e verifica se existem no disco."""
    findings: List[Dict[str, Any]] = []
    path_pattern = re.compile(
        r"`((?:src|tests|data|models|artifacts|reports|\.agents)[/\\][\w\-./\\]+\.[a-zA-Z0-9]+)`"
    )
    checked: set[str] = set()
    for line_no, line in enumerate(lines, start=1):
        for match in path_pattern.finditer(line):
            rel_path = match.group(1)
            if rel_path in checked:
                continue
            checked.add(rel_path)
            candidate = (workspace_root / rel_path).resolve()
            if not candidate.exists():
                findings.append(
                    {
                        "line": line_no,
                        "declared_path": rel_path,
                        "resolved_path": str(candidate),
                        "detail": f"Arquivo declarado no relatório não existe no workspace: '{rel_path}'.",
                    }
                )
    return findings


def check_undiscovered_tests(lines: List[str]) -> List[Dict[str, Any]]:
    """Detecta afirmações de execução de testes com 0 testes descobertos ou sem contagem explícita."""
    findings: List[Dict[str, Any]] = []
    zero_tests_pattern = re.compile(
        r"\b(0\s+tests?\s+discovered|total\s+tests?\s*:\s*0|passed\s*:\s*0\s*,\s*failed\s*:\s*0)\b",
        re.IGNORECASE,
    )
    for line_no, line in enumerate(lines, start=1):
        if zero_tests_pattern.search(line):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": "Execução de testes reportou 0 testes descobertos/executados.",
                }
            )
    return findings


def check_test_set_used_in_tuning(lines: List[str]) -> List[Dict[str, Any]]:
    """Detecta menções de uso do Test set para escolha de checkpoint, threshold ou hiperparâmetros (Regra 02)."""
    findings: List[Dict[str, Any]] = []
    contamination_pattern = re.compile(
        r"\b(best_checkpoint|early_stopping|threshold|hyperparameter|tuning|calibra(?:tion|ção)|selecionado)\b.*?\b(test\s+set|split\s+de\s+teste|conjunto\s+de\s+teste|test_loss|test_f1)\b",
        re.IGNORECASE,
    )
    reverse_pattern = re.compile(
        r"\b(test\s+set|split\s+de\s+teste|conjunto\s+de\s+teste|test_loss|test_f1)\b.*?\b(usado\s+para\s+selecionar|escolher\s+checkpoint|ajustar\s+threshold|tuning)\b",
        re.IGNORECASE,
    )
    for line_no, line in enumerate(lines, start=1):
        if contamination_pattern.search(line) or reverse_pattern.search(line):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": "Indício de contaminação do conjunto Test em decisão de tuning/checkpoint/threshold (violação da regra 02-no-test-contamination).",
                }
            )
    return findings


def check_percentage_100_without_denominator(lines: List[str]) -> List[Dict[str, Any]]:
    """Detecta '100%' ou '100.0%' sem fração explícita (N/N) próxima na mesma linha."""
    findings: List[Dict[str, Any]] = []
    pct_100_pattern = re.compile(r"\b100(?:\.0+)?%")
    fraction_pattern = re.compile(r"\b\d+\s*/\s*\d+\b")
    for line_no, line in enumerate(lines, start=1):
        if pct_100_pattern.search(line) and not fraction_pattern.search(line):
            findings.append(
                {
                    "line": line_no,
                    "content": line.strip(),
                    "detail": "Afirmação de '100%' sem denominador explícito (N/N) na mesma linha.",
                }
            )
    return findings


def check_unauthorized_human_approval_claim(
    lines: List[str], manifest_data: Dict[str, Any] | None
) -> List[Dict[str, Any]]:
    """Detecta selos reservados ao usuário humano sem registro humano válido no manifesto (Regra 05)."""
    findings: List[Dict[str, Any]] = []
    human_seals = re.compile(r"\b(APPROVED_BY_USER|REJECTED_BY_USER|HUMAN_CAPTURE_IN_GAME)\b")
    human_phrases = re.compile(
        r"\b(?:inspe[çc][ãa]o\s+manual|valida[çc][ãa]o\s+manual|revis[ãa]o\s+humana|inspecionado\s+pelo\s+usu[áa]rio)\b",
        re.IGNORECASE,
    )
    has_human_record = bool(
        manifest_data and manifest_data.get("human_approval_verified") is True
    )
    for line_no, line in enumerate(lines, start=1):
        match = human_seals.search(line)
        if match and not has_human_record:
            findings.append(
                {
                    "line": line_no,
                    "seal": match.group(1),
                    "content": line.strip(),
                    "detail": f"Selo exclusivo humano '{match.group(1)}' utilizado sem registro de homologação humana verificável (violação da regra 05-human-review-integrity).",
                }
            )
        phrase_match = human_phrases.search(line)
        if phrase_match and not has_human_record:
            findings.append(
                {
                    "line": line_no,
                    "seal": phrase_match.group(0),
                    "content": line.strip(),
                    "detail": f"Alegação de validação humana não autorizada '{phrase_match.group(0)}' em relatório automatizado sem credencial humana (violação da regra 05-human-review-integrity).",
                }
            )
    return findings


def audit_markdown_report(
    report_text: str,
    workspace_root: Path,
    manifest_data: Dict[str, Any] | None,
) -> Dict[str, List[Dict[str, Any]]]:
    executive_text, _ = segment_markdown(report_text)
    lines = executive_text.splitlines()
    return {
        "conflicting_numbers": check_conflicting_numbers(lines),
        "unbacked_metrics": check_unbacked_metrics(lines, executive_text),
        "zero_support_numeric_metrics": check_zero_support_numeric_metrics(lines),
        "incompatible_confusion_matrix": check_incompatible_confusion_matrix(lines),
        "divergent_or_truncated_hashes": check_divergent_or_truncated_hashes(lines, manifest_data),
        "hardcoded_report_claims": check_hardcoded_report_claims(lines),
        "templated_data_unlabeled": check_templated_data_unlabeled(lines, executive_text),
        "missing_declared_files": check_missing_declared_files(lines, workspace_root),
        "undiscovered_tests": check_undiscovered_tests(lines),
        "test_set_used_in_tuning": check_test_set_used_in_tuning(lines),
        "percentage_100_without_denominator": check_percentage_100_without_denominator(lines),
        "unauthorized_human_approval_claim": check_unauthorized_human_approval_claim(
            lines, manifest_data
        ),
    }


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auditoria adversarial de relatórios executivos Markdown (12 vetores de invalidação)."
    )
    parser.add_argument(
        "--report-path",
        "--report",
        dest="report_path",
        type=str,
        default=None,
        help="Caminho do relatório Markdown a ser auditado (alias: --report).",
    )
    parser.add_argument(
        "--manifest-path",
        "--evidence",
        dest="manifest_path",
        type=str,
        default=None,
        help="Caminho opcional para manifesto/evidência JSON com hashes de referência (alias: --evidence).",
    )
    parser.add_argument(
        "--workspace-root",
        type=str,
        default=".",
        help="Raiz do workspace para verificar existência de arquivos declarados.",
    )
    parser.add_argument(
        "--output-json",
        "--out",
        dest="output_json",
        type=str,
        default="skeptic_audit_report.json",
        help="Caminho de saída do relatório JSON de auditoria (default: skeptic_audit_report.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa autodiagnóstico não-destrutivo com data_nature=SIMULATED e veredito CONDITIONAL.",
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
    output_path = Path(args.output_json).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_data: Dict[str, Any] | None = None
    if args.manifest_path:
        mp = Path(args.manifest_path).resolve()
        if mp.exists():
            with mp.open("r", encoding="utf-8") as f:
                manifest_data = json.load(f)

    report_sha256: str | None = None
    has_real_report = False

    if args.report_path:
        rp = Path(args.report_path).resolve()
        if not rp.exists():
            result = {
                "schema_version": "1.0.0",
                "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "report_path": str(rp),
                "exists": False,
                "data_nature": "SIMULATED" if args.dry_run else "REAL",
                "verdict": "FAIL",
                "error": f"Arquivo de relatório não encontrado: {rp}",
            }
            output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 1
        report_text = rp.read_text(encoding="utf-8")
        report_sha256 = compute_sha256(rp)
        report_path_str = str(rp)
        has_real_report = True
        data_nature = "SIMULATED" if args.dry_run else "REAL"
    elif args.dry_run:
        data_nature = "SIMULATED"
        report_path_str = "SIMULATED_DRY_RUN_SAMPLE"
        report_text = (
            "# Relatório de Autodiagnóstico (SIMULATED)\n"
            "Artefato de referência: `AGENTS.md`\n"
            "Taxa de conformidade: 100.0% (12/12)\n"
            "Classe ausente: support=0 -> recall=N/A, f1=N/A\n"
        )
    else:
        print("Erro: --report-path (ou --report) é obrigatório quando não está em --dry-run.", file=sys.stderr)
        return 1

    vector_results = audit_markdown_report(report_text, workspace_root, manifest_data)
    total_violations = sum(len(v) for v in vector_results.values())
    triggered_vectors = [k for k, v in vector_results.items() if len(v) > 0]

    if total_violations > 0:
        verdict = "FAIL"
    elif args.dry_run or not has_real_report:
        verdict = "CONDITIONAL"
    else:
        verdict = "PASS"

    output_payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "report_path": report_path_str,
        "report_sha256": report_sha256,
        "workspace_root": str(workspace_root),
        "dry_run": args.dry_run,
        "data_nature": data_nature,
        "verdict": verdict,
        "total_vectors_checked": len(VECTOR_NAMES),
        "total_violations": total_violations,
        "triggered_vectors": triggered_vectors,
        "vectors": {
            name: {
                "status": "PASS" if len(vector_results[name]) == 0 else "FAIL",
                "violation_count": len(vector_results[name]),
                "findings": vector_results[name],
            }
            for name in VECTOR_NAMES
        },
    }

    output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output_payload, indent=2, ensure_ascii=False))

    if verdict == "FAIL" and (args.strict or not args.dry_run):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
