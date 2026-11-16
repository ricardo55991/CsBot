"""Contagens exatas de rótulos epistêmicos nos relatórios e na matriz de aquisição."""
from __future__ import annotations

from pathlib import Path

BASE = Path("training_runs/intermediate_domain_study")
FILES = [
    "source_feasibility_report.md",
    "domain_training_strategy.md",
    "scale_up_recommendation.md",
    "legal_and_access_constraints.md",
    "valve_opt_in_feasibility.md",
]
TOKENS = ["VERIFIED_ONLINE", "RECAPTURED", "FIDELITY", "EVIDENCE_LOSS", "REPORT_TO_SOURCE"]

total_verified = 0
for name in FILES:
    text = (BASE / name).read_text(encoding="utf-8", errors="replace")
    counts = {token: text.count(token) for token in TOKENS}
    total_verified += counts["VERIFIED_ONLINE"]
    print(f"{name}: {counts}")

print(f"TOTAL VERIFIED_ONLINE nos 5 MD: {total_verified}")

matrix_path = Path("datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json")
matrix_text = matrix_path.read_text(encoding="utf-8")
print(f"\nacquisition_source_matrix.json: VERIFIED_ONLINE={matrix_text.count('VERIFIED_ONLINE')} "
      f"RECAPTURED={matrix_text.count('RECAPTURED')} FIDELITY={matrix_text.count('FIDELITY')}")

for other in ("faceit_access_readiness.json", "professional_vs_intermediate.json", "spot_domain_coverage.json",
              "pilot_corpus_quality.json", "ct_standardization_analysis.json", "tr_standardization_analysis.json",
              "unmapped_intermediate_clusters.json", "intermediate_splits_proposal.json"):
    text = (BASE / other).read_text(encoding="utf-8")
    print(f"{other}: VERIFIED_ONLINE={text.count('VERIFIED_ONLINE')} RECAPTURED={text.count('RECAPTURED')}")
