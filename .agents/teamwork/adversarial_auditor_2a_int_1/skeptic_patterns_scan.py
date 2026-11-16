"""Caça adversarial de padrões do csbot-report-skeptic nos relatórios da fase (somente leitura)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(".").resolve()
STUDY = ROOT / "training_runs/intermediate_domain_study"
TARGETS = [
    STUDY / "source_feasibility_report.md",
    STUDY / "domain_training_strategy.md",
    STUDY / "scale_up_recommendation.md",
    STUDY / "legal_and_access_constraints.md",
    STUDY / "valve_opt_in_feasibility.md",
]

CHECKS = [
    ("HUMAN_SEAL", re.compile(r"APPROVED_BY_USER|REJECTED_BY_USER|HUMAN_CAPTURE_IN_GAME", re.I)),
    ("HUMAN_PROSE", re.compile(r"inspecionad[oa] manualmente|validado pelo operador|valida[cç][aã]o humana|aprova[cç][aã]o humana|revis[aã]o humana (conclu[ií]da|realizada)|homologad[oa] pelo usu[aá]rio", re.I)),
    ("VERIFIED_ONLINE", re.compile(r"VERIFIED_ONLINE|VERIFIED\b", re.I)),
    ("HYPOTHESIS_CONFIRMED", re.compile(r"hip[oó]tese (foi )?confirmada|hypothesis[_ ]status[\"':\s]+CONFIRMED|hypothesis_confirmed", re.I)),
    ("READY_TO_SCALE", re.compile(r"INTERMEDIATE_MIRAGE_CORPUS_READY_TO_SCALE", re.I)),
    ("GATE_PASS_CLAIM", re.compile(r"Gate [ABCD][^\n]{0,80}(passou|PASS\b|aprovad)", re.I)),
    ("F12_INTERFACE_CONFIRMED", re.compile(r"interface confirmada|confirmed interface|ICsgoplayers|ICSGOPlayers", re.I)),
    ("NUMERIC_RATE", re.compile(r"\b\d{1,3}(?:[.,]\d+)?\s*%")),
    ("URL_SIGNED", re.compile(r"X-Amz|signature=|token=", re.I)),
]

for path in TARGETS:
    if not path.is_file():
        print(f"MISSING: {path}")
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    print("=" * 110)
    print(f"{path.relative_to(ROOT).as_posix()}  ({len(text.encode())} B, {len(lines)} linhas)")
    print("=" * 110)
    for name, pattern in CHECKS:
        hits = [(i, l.strip()) for i, l in enumerate(lines, 1) if pattern.search(l)]
        print(f"\n-- {name}: {len(hits)} ocorrencia(s)")
        for i, l in hits[:25]:
            print(f"   L{i}: {l[:200]}")
        if len(hits) > 25:
            print(f"   ... (+{len(hits)-25})")
