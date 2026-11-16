"""Auditoria adversarial dos artefatos JSON analíticos (somente leitura).

Verifica: (a) nenhuma métrica intermediária numérica; (b) support zero -> N/A;
(c) status de hipótese; (d) Gates C/D não executáveis; (e) contagens declaradas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(".").resolve()
STUDY = ROOT / "training_runs/intermediate_domain_study"

NUMERIC_METRIC_KEYS = re.compile(
    r"(?i)^(accuracy|precision|recall|f1|f1_score|auc|roc_auc|balanced_accuracy|ece|brier|mse|mae|loss|"
    r"mean|median|std|p50|p95|p99|value|score|rate|percentage|ratio|coverage_pct)"
)


def walk(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, f"{path}[{index}]")
    else:
        yield path, node


for name in ("professional_vs_intermediate.json", "spot_domain_coverage.json",
             "pilot_corpus_quality.json", "unmapped_intermediate_clusters.json",
             "ct_standardization_analysis.json", "tr_standardization_analysis.json",
             "faceit_access_readiness.json", "intermediate_splits_proposal.json"):
    path = STUDY / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 100)
    print(f"{name}  ({path.stat().st_size} B)")
    print("=" * 100)
    print("top-level keys:", list(payload.keys()))

    leaves = list(walk(payload))
    numeric = [(p, v) for p, v in leaves if isinstance(v, (int, float)) and not isinstance(v, bool)]
    print(f"total folhas={len(leaves)}  numericas={len(numeric)}")

    # folhas numericas cujo caminho sugere metrica de desempenho E cujo caminho menciona intermediate
    suspicious = [
        (p, v) for p, v in numeric
        if "intermediate" in p.lower() and NUMERIC_METRIC_KEYS.search(p.rsplit(".", 1)[-1])
    ]
    print(f"metricas numericas em caminho 'intermediate': {len(suspicious)}")
    for p, v in suspicious[:15]:
        print(f"   SUSPEITO {p} = {v}")

    # status / hypothesis presentes
    statuses = sorted({v for p, v in leaves if isinstance(v, str) and (
        v.isupper() or v.startswith("N/A") or "UNPROVEN" in v or "NOT_EXECUTABLE" in v)})
    interesting = [s for s in statuses if any(k in s for k in ("UNPROVEN", "NOT_EXECUTABLE", "N/A", "PENDING", "HYPOTHESIS", "VERIFIED", "UNVERIFIED", "CONFIRMED"))]
    print(f"status relevantes ({len(interesting)}):")
    for s in interesting:
        print(f"   - {s}")

    # N/A (0/0)
    texts = [v for p, v in leaves if isinstance(v, str)]
    na = [t for t in texts if "N/A" in t or "0/0" in t]
    print(f"strings com N/A ou (0/0): {len(na)}")
    for t in na[:10]:
        print(f"   - {t[:130]}")
