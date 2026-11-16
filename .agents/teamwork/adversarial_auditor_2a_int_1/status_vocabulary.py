"""Distribuição exata dos tokens de status 'não executável' entre os artefatos."""
from __future__ import annotations

import collections
import re
from pathlib import Path

BASE = Path("training_runs/intermediate_domain_study")
IC = Path("datasets/mirage_domains/intermediate_competitive")
FILES = sorted(BASE.glob("*.json")) + sorted(IC.glob("*.json")) + [Path("datasets/mirage_domains/domain_contract_v1.json")]

pattern = re.compile(r"\bNOT_(?:EXECUTABLE|EXECUTED|EVALUABLE|EVALUATED)[A-Z_]*")
global_counts: collections.Counter[str] = collections.Counter()
for path in FILES:
    text = path.read_text(encoding="utf-8", errors="replace")
    counts = collections.Counter(pattern.findall(text))
    if counts:
        print(f"{path.as_posix()}: {dict(counts)}")
        global_counts.update(counts)
print("\nTOTAL GLOBAL:", dict(global_counts))
