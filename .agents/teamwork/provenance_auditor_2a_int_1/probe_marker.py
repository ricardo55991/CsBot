"""Verifica a integridade byte-a-byte dos 95 artefatos preservados (marcador de pausa).

SOMENTE LEITURA. Enumera caminhos a partir do próprio JSON do marcador e recalcula
SHA-256 com hashlib em modo 'rb'.
"""
import hashlib
import json
import os
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
MARKER = "training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json"


def sha(ab):
    h = hashlib.sha256()
    with open(ab, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


marker_abs = os.path.join(ROOT, MARKER)
with open(marker_abs, "rb") as fh:
    raw = fh.read()
print("MARKER bytes =", len(raw))
print("MARKER sha256 =", hashlib.sha256(raw).hexdigest())
d = json.loads(raw.decode("utf-8"))
print("MARKER top keys =", list(d.keys()))
inv = d.get("preserved_artifacts_inventory")
print("inventory type =", type(inv).__name__, "len =", (len(inv) if hasattr(inv, "__len__") else None))
if isinstance(inv, dict):
    print("inventory keys =", list(inv.keys()))
    for k, v in inv.items():
        print("   ", k, "->", type(v).__name__, (len(v) if hasattr(v, "__len__") else v))
