#!/usr/bin/env python3
"""
Hook B: validate_generated_report.py
Eventos suportados: PreToolUse, PostToolUse e Stop.
Executa as 9 verificações forenses do csbot-report-skeptic sobre relatórios gerados (.md, .json, .pdf):
1) support=0 acompanhado de métrica numérica (F1 > 0, recall > 0, etc. em vez de N/A);
2) números incompatíveis (passed > discovered ou concatenação sem barra ex: 340340);
3) IDs templados (TEMPLATE_ID, DUMMY_SPOT, PLACEHOLDER_, TODO_FILL);
4) classe inexistente fora do contrato (ex: SUPER_SECRET_STATE);
5) hash inconsistente ou truncado (ex: sha256: a1b2c3... com reticências ou < 64 hex);
6) indicação de Test usado em tuning / escolha de checkpoint / threshold / calibração;
7) claim PASS sem fonte / sem artefato bruto citado;
8) "manual" ou APPROVED_BY_USER / HUMAN_CAPTURE_IN_GAME gerado por pipeline sem aprovação humana;
9) relatório executivo sem artefato bruto verificável.
"""

from __future__ import annotations

import datetime
from html.parser import HTMLParser
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from common_hook_utils import (
    AUDIT_DIR,
    WORKSPACE_ROOT,
    extract_tool_input,
    fail_safe_main,
    format_hook_response,
    sanitize_text,
    write_json_atomic,
)

HOOK_NAME = "validate-generated-report"
LAST_REPORT_VALIDATION_FILE = AUDIT_DIR / "last_report_validation.json"

REPORT_NAME_KEYWORDS = (
    "report",
    "relatorio",
    "relatório",
    "summary",
    "resumo",
    "audit",
    "auditoria",
    "verdict",
    "veredito",
    "evaluation",
    "avaliacao",
    "avaliação",
    "phase_gate",
    "handoff",
    "walkthrough",
    "deliverable",
)

EXEMPT_FILES = {
    "agents.md",
    "skill.md",
    "readme.md",
    "hooks_config.json",
    "hook_mode.json",
    "hooks.json",
    "skills.json",
    "last_report_validation.json",
    "last_test_execution.json",
    "sensitive_file_authorization.json",
    "pre_training_gate_manifest.json",
    "input_snapshot.json",
}

INVALID_CLASS_PATTERNS = [
    re.compile(r"\bSUPER_SECRET_STATE\b", re.IGNORECASE),
    re.compile(r"\bUNKNOWN_FICTIONAL_CLASS\b", re.IGNORECASE),
    re.compile(r"\bINVALID_STATE_CLASS\b", re.IGNORECASE),
    re.compile(r"\bNON_EXISTENT_CLASS\b", re.IGNORECASE),
]

TEMPLATED_ID_PATTERNS = [
    re.compile(r"\bTEMPLATE_ID\b", re.IGNORECASE),
    re.compile(r"\bDUMMY_SPOT\b", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER_[A-Z0-9_]*\b", re.IGNORECASE),
    re.compile(r"\bTODO_FILL\b", re.IGNORECASE),
    re.compile(r"\bMOCK_ARTIFACT\b", re.IGNORECASE),
    re.compile(r"\bFAKE_HASH\b", re.IGNORECASE),
    re.compile(r"\bdemo_m\d+\b", re.IGNORECASE),
    re.compile(r"\bsynthetic_demo_\w+\b", re.IGNORECASE),
]

DEMO_CATALOG_FILE = WORKSPACE_ROOT / "datasets" / "mirage_v2" / "manifests" / "demo_inventory_v2.json"
_KNOWN_DEMOS_CACHE: Optional[Set[str]] = None


def get_known_demo_ids() -> Set[str]:
    global _KNOWN_DEMOS_CACHE
    if _KNOWN_DEMOS_CACHE is None:
        _KNOWN_DEMOS_CACHE = set()
        if DEMO_CATALOG_FILE.exists():
            try:
                with DEMO_CATALOG_FILE.open("r", encoding="utf-8") as f:
                    cat_data = json.load(f)
                if isinstance(cat_data, list):
                    for item in cat_data:
                        if isinstance(item, dict):
                            if "demo_id" in item:
                                _KNOWN_DEMOS_CACHE.add(str(item["demo_id"]).strip())
                            if "file_path" in item:
                                _KNOWN_DEMOS_CACHE.add(Path(item["file_path"]).stem)
            except Exception:
                pass
    return _KNOWN_DEMOS_CACHE


def segment_markdown(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Segmenta o documento Markdown isolando blocos de código (fenced code blocks ``` ou ~~~).
    Retorna:
      - executive_text: texto com o conteúdo de blocos de código substituído por linhas em branco
        (preservando a contagem de linhas original).
      - segments: lista de metadados dos blocos (tipo: DOCUMENTATION_EXAMPLE ou ADVERSARIAL_FIXTURE, linhas, linguagem).
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


def is_report_target(file_path: str, content: str) -> bool:
    """Determina se o arquivo ou payload em análise é um relatório ou artefato de conclusão."""
    if not file_path and content:
        return True
    norm = file_path.strip().strip("\"'").replace("\\", "/")
    basename = os.path.basename(norm).lower()
    if basename in EXEMPT_FILES:
        return False
    if "/.agents/skills/" in norm.lower() or "/.agents/rules/" in norm.lower() or "/.agents/hooks/" in norm.lower():
        return False

    ext = os.path.splitext(basename)[1].lower()
    if ext not in (".md", ".json", ".pdf", ".txt"):
        return False

    if any(kw in basename for kw in REPORT_NAME_KEYWORDS):
        return True

    # Se o conteúdo possui estrutura explícita de relatório executivo ou veredito
    lower_content = content.lower()
    if any(
        marker in lower_content
        for marker in ("# relatorio", "# relatório", "## veredito", "executive report", "verdict:", '"verdict"')
    ):
        return True

    return False


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


def _parse_markdown_tables_support_zero(text: str) -> List[str]:
    violations: List[str] = []
    lines = text.splitlines()
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
                                        violations.append(
                                            f"[Regra 03 / Support=0] Tabela possui classe com support=0 exibindo métrica numérica na coluna '{col_name}': '{mval.strip()}' (exigido 'N/A' ou '-')."
                                        )
                    row_idx += 1
                i = row_idx
                continue
        i += 1
    return violations


class _HTMLTableExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: List[List[List[str]]] = []
        self._cur_table: List[List[str]] = []
        self._cur_row: List[str] = []
        self._cur_cell: List[str] = []
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        tag_l = tag.lower()
        if tag_l == "table":
            self._cur_table = []
        elif tag_l == "tr":
            self._cur_row = []
        elif tag_l in ("th", "td"):
            self._cur_cell = []
            self._in_cell = True

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cur_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()
        if tag_l in ("th", "td"):
            self._in_cell = False
            self._cur_row.append("".join(self._cur_cell).strip())
        elif tag_l == "tr":
            if self._cur_row:
                self._cur_table.append(self._cur_row)
        elif tag_l == "table":
            if self._cur_table:
                self.tables.append(self._cur_table)


def _parse_html_tables_support_zero(text: str) -> List[str]:
    violations: List[str] = []
    if "<table" not in text.lower():
        return violations
    parser = _HTMLTableExtractor()
    try:
        parser.feed(text)
    except Exception:
        return violations

    for tbl in parser.tables:
        if len(tbl) < 2:
            continue
        raw_headers = tbl[0]
        headers = [re.sub(r"[*_`]", "", h).strip() for h in raw_headers]
        header_lower = [h.lower() for h in headers]
        support_idx = None
        for idx, h in enumerate(header_lower):
            if "support" in h or h in ("suporte", "support_count"):
                support_idx = idx
                break
        if support_idx is None:
            continue

        metric_indices: List[Tuple[int, str]] = []
        for idx, h in enumerate(header_lower):
            for kw in METRIC_COLUMN_KEYWORDS:
                if kw == h or f" {kw}" in f" {h}" or f"{kw} " in f"{h} " or f"({kw})" in f"({h})":
                    metric_indices.append((idx, headers[idx]))
                    break

        for row in tbl[1:]:
            if len(row) > support_idx:
                sup_clean = re.sub(r"[*_`]", "", row[support_idx]).strip().replace(" ", "")
                if re.match(r"^0(?:\.0+|,0+)?$", sup_clean):
                    for midx, col_name in metric_indices:
                        if len(row) > midx:
                            mval = row[midx]
                            if _is_numeric_metric_value(mval):
                                violations.append(
                                    f"[Regra 03 / Support=0] Tabela HTML possui classe com support=0 exibindo métrica numérica na coluna '{col_name}': '{mval.strip()}' (exigido 'N/A' ou '-')."
                                )
    return violations


def check_support_zero_violation(text: str) -> List[str]:
    """Regra 1: support=0 acompanhado de métrica numérica em vez de N/A."""
    exec_text, _ = segment_markdown(text)
    violations: List[str] = []

    # 1. Parsing estrutural de tabelas Markdown
    violations.extend(_parse_markdown_tables_support_zero(exec_text))

    # 2. Parsing estrutural de tabelas HTML
    violations.extend(_parse_html_tables_support_zero(exec_text))

    # 3. Verificações linha a linha fora de tabela ou inline
    for line in exec_text.splitlines():
        if re.search(r'("support"\s*:\s*0\b|\bsupport\s*=\s*0\b)', line, re.IGNORECASE):
            metric_match = re.search(
                r'(?:f1(?:-score)?|recall|precision|balanced[_\s]accuracy)\s*["\']?\s*[:=]\s*([0-9]+(?:\.[0-9]+)?%?)',
                line,
                re.IGNORECASE,
            )
            if metric_match:
                violations.append(
                    f"[Regra 03 / Support=0] Linha com support=0 exibe métrica numérica ({metric_match.group(0)}) em vez de 'N/A'."
                )
            elif re.search(r"\bsupport\s*=\s*0\b", line, re.IGNORECASE) and re.search(
                r"\b(0\.[0-9]+|1\.00?|100(?:\.0+)?%|0\.0+%)\b", line
            ):
                violations.append(
                    f"[Regra 03 / Support=0] Classe com support=0 acompanhada de valor numérico na linha: '{line.strip()[:120]}'."
                )

    # 4. Objetos JSON estruturados se for JSON
    try:
        parsed = json.loads(text)
        violations.extend(_scan_json_support_zero(parsed))
    except Exception:
        pass

    return violations


def _scan_json_support_zero(node: Any) -> List[str]:
    found: List[str] = []
    if isinstance(node, dict):
        if node.get("support") == 0:
            for mkey in ("f1", "f1_score", "recall", "precision", "balanced_accuracy"):
                if mkey in node and node[mkey] != "N/A" and node[mkey] is not None:
                    found.append(
                        f"[Regra 03 / Support=0] Objeto JSON com support=0 possui '{mkey}': {node[mkey]} (deve ser 'N/A')."
                    )
        for v in node.values():
            found.extend(_scan_json_support_zero(v))
    elif isinstance(node, list):
        for item in node:
            found.extend(_scan_json_support_zero(item))
    return found


def check_incompatible_numbers(text: str) -> List[str]:
    """Regra 2: números incompatíveis (passed > discovered ou concatenação duplicada tipo 340340)."""
    violations: List[str] = []

    # Detecta números de 3 dígitos repetidos colados (ex: 340340, 226226)
    for m in re.finditer(r"\b(\d{3})\1\b", text):
        num = m.group(0)
        half = m.group(1)
        violations.append(
            f"[Números Incompatíveis] Contagem concatenada corrompida '{num}' detectada (provável '{half}/{half}' sem barra)."
        )

    # Detecta passed > discovered/total em texto ou JSON
    passed_matches = re.findall(r'"?passed"?\s*[:=]\s*(\d+)', text, re.IGNORECASE)
    disc_matches = re.findall(r'"?(?:discovered|total_tests|total)"?\s*[:=]\s*(\d+)', text, re.IGNORECASE)
    if passed_matches and disc_matches:
        try:
            passed_val = int(passed_matches[0])
            disc_val = int(disc_matches[0])
            if passed_val > disc_val:
                violations.append(
                    f"[Números Incompatíveis] Contagem impossível: passed ({passed_val}) > discovered/total ({disc_val})."
                )
        except ValueError:
            pass

    # Detecta fração X/Y onde X > Y em resumo de testes (ex: 350/340 passed)
    for m in re.finditer(r"\b(\d+)\s*/\s*(\d+)\s+(?:passed|aprovados|testes)\b", text, re.IGNORECASE):
        num, den = int(m.group(1)), int(m.group(2))
        if num > den:
            violations.append(f"[Números Incompatíveis] Resumo de testes impossível: {num}/{den} (aprovados > total).")

    return violations


def check_templated_ids(text: str) -> List[str]:
    """Regra 3: IDs templados ou placeholders, com validação cruzada contra catálogo formal."""
    exec_text, _ = segment_markdown(text)
    violations: List[str] = []

    # 1. Identificadores templados e formatos sintéticos conhecidos
    for pat in TEMPLATED_ID_PATTERNS:
        for m in pat.finditer(exec_text):
            violations.append(
                f"[Dados Templados / Regra 04] Identificador templado proibido detectado: '{m.group(0)}' (UNPROVENANCED_TEMPLATE_ID)."
            )

    # 2. Verificação de menções a demos contra o catálogo formal demo_inventory_v2.json
    known_demos = get_known_demo_ids()
    if known_demos:
        demo_ctx_matches = re.finditer(
            r"(?:demos?\s*(?:utilizadas?|validadas?|de\s+refer[êe]ncia|avaliadas?|testadas?)?\s*[:=]\s*|\bdemo_id\s*[:=]\s*)([^\n;]+)",
            exec_text,
            re.IGNORECASE,
        )
        for ctx in demo_ctx_matches:
            raw_tokens = ctx.group(1).split(",")
            for tok in raw_tokens:
                cand = tok.strip().strip("`*\"' \t")
                if not cand or any(w in cand.lower() for w in ("pass", "fail", "true", "false", "none", "ok")):
                    continue
                if re.match(r"^[a-zA-Z0-9_\-]+$", cand):
                    if cand not in known_demos and not any(cand in v for v in violations):
                        violations.append(
                            f"[Dados Templados / Regra 04] Identificador de demo não catalogado em demo_inventory_v2.json: '{cand}' (UNPROVENANCED_TEMPLATE_ID)."
                        )

    return violations


def check_nonexistent_classes(text: str) -> List[str]:
    """Regra 4: Classe inexistente fora do contrato."""
    violations: List[str] = []
    for pat in INVALID_CLASS_PATTERNS:
        m = pat.search(text)
        if m:
            violations.append(f"[Contrato de Classes] Classe inexistente no contrato detectada: '{m.group(0)}'.")
    return violations


TRUNCATED_HASH_PATTERN = re.compile(
    r'(?:sha-?256|previous_sha256|catalog_hash|hash)\s*["\'`]?\s*[:=]\s*["\'`]?([0-9a-fA-F]{4,63}(?![0-9a-fA-F])(?:\.\.\.)?|[0-9a-fA-F]*\.{2,}[0-9a-fA-F]*)["\'`]?',
    re.IGNORECASE,
)
ELLIPSIS_HASH_PATTERN = re.compile(
    r"[`\"']?([0-9a-fA-F]{4,64}\.{2,}[0-9a-fA-F]*|\.{2,}[0-9a-fA-F]{4,64})[`\"']?"
)
FULL_HASH_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")


def check_truncated_hashes(text: str) -> List[str]:
    """Regra 5: Hash SHA-256 truncado ou com reticências."""
    exec_text, _ = segment_markdown(text)
    violations: List[str] = []

    # 1. Hashes com reticências em qualquer posição fora de code fence
    for m in ELLIPSIS_HASH_PATTERN.finditer(exec_text):
        token = m.group(1).strip()
        violations.append(
            f"[Regra 01 / Hash Truncado] Hash SHA-256 truncado com reticências detectado: '{token}' (exigido 64 hex completos)."
        )

    # 2. Hashes incompletos (4 a 63 caracteres) precedidos de chave sha256/hash
    for m in TRUNCATED_HASH_PATTERN.finditer(exec_text):
        candidate = m.group(1).strip()
        if ".." in candidate:
            continue
        if len(candidate) != 64:
            violations.append(
                f"[Regra 01 / Hash Truncado] Hash SHA-256 inválido ou truncado detectado: '{candidate}' ({len(candidate)} chars; exigido 64 hex completos)."
            )

    return violations


def check_test_set_contamination(text: str) -> List[str]:
    """Regra 6: Indicação de Test set usado em tuning, threshold, calibração ou escolha de checkpoint."""
    violations: List[str] = []
    contamination_patterns = [
        re.compile(
            r"\b(?:tuned|tuning|calibrat(?:ed|ion)|threshold\s+selected|best[_\s]checkpoint|early[_\s]stopping|hyperparameter)\b[^\n.;]{0,80}\b(?:on|using|from|no|com\s+o)\s+(?:the\s+)?(?:test(?:\s+set|\s+split)?|conjunto\s+de\s+teste|holdout)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:test\s+set|test\s+split|conjunto\s+de\s+teste)\b[^\n.;]{0,80}\b(?:used\s+for|usado\s+para|utilizado\s+para)\s+(?:tuning|calibra[çc][ãa]o|threshold|checkpoint|sele[çc][ãa]o\s+de\s+época)\b",
            re.IGNORECASE,
        ),
        re.compile(r'"(?:tuning_split|checkpoint_selection_split|calibration_split)"\s*:\s*"test"', re.IGNORECASE),
    ]
    for pat in contamination_patterns:
        m = pat.search(text)
        if m:
            violations.append(
                f"[Regra 02 / Contaminação do Test Set] Indicação de uso do conjunto Test em decisões de tuning/calibração/checkpoint: '{m.group(0)}'."
            )
    return violations


def check_human_review_forgery(text: str, payload: Dict[str, Any]) -> List[str]:
    """Regra 8: Selo APPROVED_BY_USER / HUMAN_CAPTURE_IN_GAME ou 'manual' gerado por pipeline sem aprovação humana."""
    violations: List[str] = []
    human_confirmed = bool(payload.get("human_verified") or os.environ.get("CSBOT_HUMAN_VERIFIED") == "1")
    if human_confirmed:
        return violations

    if re.search(r"\b(APPROVED_BY_USER|REJECTED_BY_USER|HUMAN_CAPTURE_IN_GAME)\b", text):
        # Permite apenas se estiver negando ou explicando a regra, bloqueia se atribuído como status/selo
        if re.search(
            r'(?:status|seal|selo|review|homologacao|homologação|approval|capture_type|origin)\s*["\']?\s*[:=]\s*["\']?(APPROVED_BY_USER|REJECTED_BY_USER|HUMAN_CAPTURE_IN_GAME)',
            text,
            re.IGNORECASE,
        ) or re.search(r"^\s*[-*]?\s*\**(?:Status|Selo|Homologação)\**\s*:\s*`?(APPROVED_BY_USER|HUMAN_CAPTURE_IN_GAME)", text, re.IGNORECASE | re.MULTILINE):
            violations.append(
                "[Regra 05 / Revisão Humana] Selo exclusivo humano (APPROVED_BY_USER / HUMAN_CAPTURE_IN_GAME) emitido por agente/pipeline sem confirmação humana."
            )

    if re.search(
        r'(?:generated_by|pipeline|automated|script_generated)[^\n]{0,60}(?:review_type|origin|capture)\s*["\']?\s*[:=]\s*["\']?manual\b',
        text,
        re.IGNORECASE,
    ) or re.search(r'"source"\s*:\s*"pipeline"\s*,\s*"review"\s*:\s*"manual"', text, re.IGNORECASE):
        violations.append(
            "[Regra 05 / Revisão Humana] Artefato gerado por pipeline rotulado falsamente como revisão/captura 'manual'."
        )
    return violations


def check_unbacked_pass_and_raw_artifacts(text: str) -> List[str]:
    """Regras 7 e 9: Claim PASS sem fonte/artefato bruto citado; relatório executivo sem artefato bruto verificável."""
    violations: List[str] = []
    has_pass_claim = bool(
        re.search(r"\b(?:verdict|veredito|status|conclusão|conclusao)\b[^\n]{0,40}\bPASS\b", text, re.IGNORECASE)
        or re.search(r'"verdict"\s*:\s*"PASS"', text)
    )
    is_exec_report = bool(
        re.search(r"(?:relat[óo]rio\s+executivo|executive\s+report|#\s+relat[óo]rio)", text, re.IGNORECASE)
    )

    if not (has_pass_claim or is_exec_report):
        return violations

    # Verifica se há referência a pelo menos um artefato bruto verificável (.json, .jsonl, .parquet, .npz, .pt, .onnx, .log, .csv) ou SHA-256 de 64 chars
    has_raw_artifact_ref = bool(
        re.search(r"[\w./\\-]+\.(?:jsonl|json|parquet|npz|pt|onnx|csv|log|py|cs)\b", text, re.IGNORECASE)
    )
    has_full_sha = bool(re.search(r"\b[0-9a-fA-F]{64}\b", text))

    if has_pass_claim and not has_raw_artifact_ref:
        violations.append(
            "[Regra 01 / Claim PASS Sem Fonte] Afirmação de veredito 'PASS' sem citação de nenhum artefato bruto verificável (.json, .jsonl, .parquet, .npz, .pt, .log)."
        )
    elif is_exec_report and not (has_raw_artifact_ref or has_full_sha):
        violations.append(
            "[Regra 01 / Relatório Sem Lastro] Relatório executivo não aponta para nenhum artefato bruto verificável nem hash SHA-256."
        )

    return violations


def analyze_report_content(text: str, payload: Dict[str, Any]) -> List[str]:
    """Executa todas as 9 verificações céticas sobre afirmações executivas do relatório."""
    executive_text, _ = segment_markdown(text)
    violations: List[str] = []
    violations.extend(check_support_zero_violation(executive_text))
    violations.extend(check_incompatible_numbers(executive_text))
    violations.extend(check_templated_ids(executive_text))
    violations.extend(check_nonexistent_classes(executive_text))
    violations.extend(check_truncated_hashes(executive_text))
    violations.extend(check_test_set_contamination(executive_text))
    violations.extend(check_human_review_forgery(executive_text, payload))
    violations.extend(check_unbacked_pass_and_raw_artifacts(executive_text))
    return violations


def extract_report_target_and_text(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Extrai o caminho do arquivo e o conteúdo do relatório do payload."""
    tool_input = extract_tool_input(payload)
    file_path = ""
    for k in ("TargetFile", "Path", "file_path", "filepath", "AbsolutePath", "report_path"):
        val = tool_input.get(k) or payload.get(k)
        if isinstance(val, str) and val.strip():
            file_path = val.strip()
            break

    content_parts: List[str] = []
    for k in ("CodeContent", "Content", "ReplacementContent", "Replacement", "content", "report_content", "text", "summary"):
        val = tool_input.get(k) or payload.get(k)
        if isinstance(val, str) and val.strip():
            content_parts.append(val)

    if isinstance(tool_input.get("ReplacementChunks"), list):
        for chunk in tool_input["ReplacementChunks"]:
            if isinstance(chunk, dict) and isinstance(chunk.get("ReplacementContent"), str):
                content_parts.append(chunk["ReplacementContent"])

    content = "\n".join(content_parts)

    # Se não veio conteúdo inline (ex: PostToolUse ou Stop apontando para arquivo no disco), lê do disco
    if not content and file_path:
        p = Path(file_path)
        if not p.is_absolute():
            p = WORKSPACE_ROOT / p
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

    return file_path, content


def handle_validate_generated_report(payload: Dict[str, Any], mode: str, event: str) -> Dict[str, Any]:
    file_path, content = extract_report_target_and_text(payload)

    if not is_report_target(file_path, content):
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=False,
            reason="Operação não envolve geração de relatório executivo ou de avaliação.",
            payload=payload,
        )

    violations = analyze_report_content(content, payload)

    validation_state = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": event,
        "mode": mode,
        "target_file": sanitize_text(file_path or "<inline_report>"),
        "status": "FAILED" if violations else "PASSED",
        "violations_count": len(violations),
        "violations": violations,
    }
    write_json_atomic(LAST_REPORT_VALIDATION_FILE, validation_state)

    if not violations:
        return format_hook_response(
            hook_name=HOOK_NAME,
            event=event,
            mode=mode,
            is_violation=False,
            reason="Relatório validado com sucesso pelo csbot-report-skeptic (0 violações).",
            payload=payload,
            extra=validation_state,
        )

    joined_violations = " | ".join(violations)
    reason = (
        f"BLOQUEIO [{HOOK_NAME}]: Relatório reprovado pela auditoria cética ({len(violations)} violação(ões)): "
        f"{joined_violations} "
        "Ação corretiva: 1) Substitua métricas de classes com support=0 por 'N/A'; "
        "2) Corrija contagens incompatíveis (use '<passed>/<discovered>'); "
        "3) Remova IDs templados, classes fora do contrato e selos humanos não autorizados; "
        "4) Cite os artefatos brutos reais e hashes SHA-256 completos de 64 caracteres."
    )
    return format_hook_response(
        hook_name=HOOK_NAME,
        event=event,
        mode=mode,
        is_violation=True,
        reason=reason,
        payload=payload,
        extra=validation_state,
    )


if __name__ == "__main__":
    fail_safe_main(HOOK_NAME, "PreToolUse", handle_validate_generated_report)
