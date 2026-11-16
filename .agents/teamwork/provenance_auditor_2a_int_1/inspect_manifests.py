"""Inspeção detalhada (somente leitura) dos 4 manifests intermediários + contabilidade."""
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


for rel in FILES:
    d = load(rel)
    print("=" * 100)
    print(rel)
    print("TOPKEYS:", list(d.keys()))
    for k in d:
        v = d[k]
        if isinstance(v, list):
            print(f"  [{k}] list len={len(v)} sample={v[:2]}")
        elif isinstance(v, dict):
            print(f"  [{k}] dict keys={list(v.keys())}")
        else:
            s = str(v)
            print(f"  [{k}] = {s[:160]}")
