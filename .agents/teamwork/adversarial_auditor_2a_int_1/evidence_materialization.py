"""Mapeia as URLs citadas na §12 do relatório de viabilidade contra as capturas brutas em disco.

Produz (N/D) explícito: quantas URLs citadas têm artefato bruto materializado.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(".").resolve()
REPORT = ROOT / "training_runs/intermediate_domain_study/source_feasibility_report.md"
CACHE = ROOT / "scratch/2a_intermediate_research_cache"

lines = REPORT.read_text(encoding="utf-8").splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("## 12."))
cited: list[tuple[str, str, str]] = []
for line in lines[start:]:
    match = re.match(r"\|\s*(E\d+)\s*\|\s*(https?://\S+)\s*\|\s*([0-9T:Z-]+)\s*\|", line)
    if match:
        cited.append((match.group(1), match.group(2), match.group(3)))

recaptured = json.loads((CACHE / "_recapture_log.json").read_text(encoding="utf-8"))
recap_urls = {entry["url"]: entry["file"] for entry in recaptured}
recap_files = {entry["file"]: entry for entry in recaptured}

print(f"URLs citadas na §12: {len(cited)}")
materialized = []
not_materialized = []
for ident, url, utc in cited:
    if url in recap_urls:
        file = recap_urls[url]
        info = recap_files[file]
        materialized.append((ident, url, file, info["utc"], info["status"]))
    else:
        not_materialized.append((ident, url, utc))

print(f"\nCOM captura bruta em disco: {len(materialized)}/{len(cited)}")
for ident, url, file, utc, status in materialized:
    print(f"  {ident} {url}\n      -> {file} (captura {utc}, status {status})")

print(f"\nSEM captura bruta em disco: {len(not_materialized)}/{len(cited)}")
for ident, url, utc in not_materialized:
    print(f"  {ident} {url} (UTC declarado {utc})")

# URLs citadas que correspondem a capturas mas cujo UTC declarado difere do UTC da captura
print("\nVerificação de fidelidade temporal (UTC declarado na §12 vs UTC real da captura):")
declared_utc = {ident: utc for ident, _url, utc in cited}
for ident, url, file, utc, status in materialized:
    declared = declared_utc[ident]
    same = declared == utc
    print(f"  {ident}: declarado={declared}  captura={utc}  {'MESMO_INSTANTE' if same else 'DIFERENTE'}")

print(f"\nFORMULA: URLs com artefato bruto materializado = ({len(materialized)}/{len(cited)})")
print(f"FORMULA: URLs sem artefato bruto materializado = ({len(not_materialized)}/{len(cited)})")
