"""Extrator focado: contabilidade (0/0) e inventários vazios dos 4 manifests."""
import json
import os

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
FILES = [
    "datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json",
    "datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json",
    "datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json",
    "datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json",
]


def load(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


print("### KEYS CONTENDO 'record' / 'download' / listas top-level")
for rel in FILES:
    d = load(rel)
    print("-" * 90)
    print(rel.split("/")[-1])
    for k, v in d.items():
        if isinstance(v, list):
            print(f"   list  {k}: len={len(v)}")
        elif "record" in k.lower() or "download" in k.lower() or "count" in k.lower():
            print(f"   other {k}: {json.dumps(v, ensure_ascii=False)[:200]}")

print()
print("### ACCOUNTING BLOCKS")
for rel in FILES:
    d = load(rel)
    print("-" * 90)
    print(rel.split("/")[-1])
    acc = d.get("accounting")
    print(json.dumps(acc, indent=1, ensure_ascii=False))
