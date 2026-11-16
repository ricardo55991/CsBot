"""Rastreabilidade de números: procura números citados nos 3 relatórios que NÃO aparecem
em nenhum outro artefato materializado (JSONs, MDs auxiliares, cache de pesquisa, código).

Heurística adversarial: um número que só existe no relatório não tem artefato de origem rastreável.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(".").resolve()
STUDY = ROOT / "training_runs/intermediate_domain_study"

REPORTS = [
    STUDY / "source_feasibility_report.md",
    STUDY / "domain_training_strategy.md",
    STUDY / "scale_up_recommendation.md",
]

# corpus de referência: tudo que existe materializado na fase (exceto os próprios relatórios)
CORPUS_PATHS: list[Path] = []
for pattern in ("*.json",):
    CORPUS_PATHS += sorted(STUDY.glob(pattern))
CORPUS_PATHS += [STUDY / "legal_and_access_constraints.md", STUDY / "valve_opt_in_feasibility.md"]
CORPUS_PATHS += sorted((ROOT / "datasets/mirage_domains").rglob("*.json"))
CORPUS_PATHS += sorted((ROOT / "tools/intermediate_demo_acquisition").glob("*.py"))
CORPUS_PATHS += sorted((ROOT / "scratch/2a_intermediate_research_cache").glob("*.txt"))
CORPUS_PATHS += [ROOT / "scratch/2a_intermediate_research_cache/INDEX.md"]
CORPUS_PATHS += [ROOT / "datasets/mirage_v2/canonical_temporal_splits_v1.json"]
CORPUS_PATHS += [ROOT / "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json"]
CORPUS_PATHS += [ROOT / "training_runs/positioning_v2_real_temporal/revised_spot_supervision_report.json"]

corpus_parts: list[str] = []
for path in CORPUS_PATHS:
    if path.is_file():
        corpus_parts.append(path.read_text(encoding="utf-8", errors="replace"))
CORPUS = "\n".join(corpus_parts)

# normaliza dígitos: aceita 51.498.527.411 ou 51498527411 ou 51,498,527,411
def variants(token: str) -> list[str]:
    digits = re.sub(r"\D", "", token)
    out = {digits, f"{int(digits):,}", f"{int(digits):,}".replace(",", "."), f"{int(digits):,}".replace(",", " ")}
    return [v for v in out if v]

SALIENT = re.compile(r"(?<![\w.])(\d[\d.,]{3,}\d)(?![\w])|(\d{1,3}(?:[.,]\d+)?)\s*%")

print(f"corpus de referência: {len([p for p in CORPUS_PATHS if p.is_file()])} arquivos, {len(CORPUS)} chars")

for report in REPORTS:
    text = report.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    untraceable: list[tuple[int, str, str]] = []
    total = 0
    for lineno, line in enumerate(lines, 1):
        if line.strip().startswith("|") and set(line.strip()) <= set("|-: "):
            continue
        for match in SALIENT.finditer(line):
            token = match.group(1) or match.group(2)
            if not token:
                continue
            total += 1
            if not any(v in CORPUS for v in variants(token)):
                untraceable.append((lineno, token, line.strip()[:160]))
    print("\n" + "=" * 100)
    print(f"{report.name}: números salientes={total}  sem rastro no corpus={len(untraceable)}")
    print("=" * 100)
    for lineno, token, context in untraceable[:40]:
        print(f"  L{lineno} [{token}] {context}")
    if len(untraceable) > 40:
        print(f"  ... (+{len(untraceable)-40})")
