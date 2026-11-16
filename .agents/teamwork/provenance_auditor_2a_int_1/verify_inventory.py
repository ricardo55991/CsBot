"""Cruza a ARTIFACT_INVENTORY.md (SOMENTE blocos [CURRENT — VIGENTE]) com o disco.

Ignora integralmente o bloco SUPERSEDED — NÃO USAR. Recalcula SHA-256 de cada linha
de tabela que contenha caminho + bytes + hash de 64 hex.
"""
import hashlib
import json
import os
import re
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
INV = ".agents/teamwork/orchestrator_2a_intermediate/ARTIFACT_INVENTORY.md"


def sha(ab):
    h = hashlib.sha256()
    with open(ab, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


raw = open(os.path.join(ROOT, INV), encoding="utf-8").read()
lines = raw.splitlines()

# delimita o bloco SUPERSEDED e o exclui
sup_start = next((i for i, l in enumerate(lines) if "SUPERSEDED" in l), len(lines))
current = lines[:sup_start]
print(f"linhas totais={len(lines)} | inicio do SUPERSEDED (excluido)={sup_start + 1}")

ROW = re.compile(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`\s*\|\s*([A-Z_]+)\s*\|")
rows = []
for i, l in enumerate(current, start=1):
    m = ROW.match(l.strip())
    if m:
        rows.append({"line": i, "path": m.group(1), "declared_bytes": int(m.group(2)),
                     "declared_sha256": m.group(3), "class": m.group(4)})
print(f"linhas de tabela reconhecidas no bloco CURRENT: {len(rows)}")

from collections import Counter
print("classes:", Counter(r["class"] for r in rows))

div, tot_bytes = [], 0
for r in rows:
    ab = os.path.join(ROOT, r["path"])
    if not os.path.isfile(ab):
        r["exists"] = False
        div.append({"path": r["path"], "issue": "MISSING"})
        continue
    st = os.stat(ab)
    tot_bytes += st.st_size
    a = sha(ab)
    r["exists"] = True
    r["actual_bytes"] = st.st_size
    r["actual_sha256"] = a
    r["ok"] = (st.st_size == r["declared_bytes"]) and (a == r["declared_sha256"])
    if not r["ok"]:
        div.append({"path": r["path"], "issue": "MISMATCH",
                    "declared_bytes": r["declared_bytes"], "actual_bytes": st.st_size,
                    "declared_sha256": r["declared_sha256"], "actual_sha256": a})

ok = sum(1 for r in rows if r.get("ok"))
print(f"MATCHES = ({ok}/{len(rows)})")
print("bytes conferidos =", tot_bytes)
print("divergencias =", json.dumps(div, indent=1, ensure_ascii=False))

out = {"inventory": INV, "rows": len(rows), "matches": ok, "ratio": f"({ok}/{len(rows)})",
       "bytes_checked": tot_bytes, "divergences": div,
       "classes": dict(Counter(r["class"] for r in rows))}
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "inventory_crosscheck.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)
