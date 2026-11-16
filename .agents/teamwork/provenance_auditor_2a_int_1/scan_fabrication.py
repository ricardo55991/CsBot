"""Varredura anti-fabricação: procura IDs de demo/partida e hashes de demo inventados.

SOMENTE LEITURA. Distingue hashes de artefato documentados (sha256 de arquivos reais)
de hashes apresentados como demo_sha256/archive_sha256 sem arquivo correspondente.
"""
import hashlib
import json
import os
import re

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
BASE = "datasets/mirage_domains"

DEMO_ID = re.compile(r"\b1-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
DEMO_HASH_KEY = re.compile(r'"(demo_sha256|archive_sha256|demo_hash)"\s*:\s*"([^"]*)"')

files = []
for dp, dn, fn in os.walk(os.path.join(ROOT, BASE)):
    for f in fn:
        files.append(os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/"))

print(f"arquivos varridos: {len(files)}")
demo_ids, demo_hashes, hex64_all = [], [], []
for rel in files:
    text = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
    for m in DEMO_ID.finditer(text):
        ln = text.count("\n", 0, m.start()) + 1
        demo_ids.append((rel, ln, m.group(0)))
    for m in DEMO_HASH_KEY.finditer(text):
        ln = text.count("\n", 0, m.start()) + 1
        demo_hashes.append((rel, ln, m.group(1), m.group(2)))
    # hashes de 64 hex cujo dono (chave) não seja de artefato
    for line in text.splitlines():
        if re.search(r"(?i)sha256|checksum|digest|hash", line) and HEX64.search(line):
            hex64_all.append((rel, line.strip()[:150]))

print("\n=== demo_ids no formato FACEIT (1-uuid) ===")
print(f"ocorrencias: {len(demo_ids)}")
for x in demo_ids[:10]:
    print("  ", x)

print("\n=== campos demo_sha256 / archive_sha256 / demo_hash com valor ===")
print(f"ocorrencias: {len(demo_hashes)}")
nonempty = [x for x in demo_hashes if x[3].strip()]
print(f"com valor NAO vazio: {len(nonempty)}")
for x in nonempty[:10]:
    print("  ", x)

print("\n=== contagem de linhas de hash de 64 hex (contexto sha/hash) ===")
print(f"linhas: {len(hex64_all)}")
byfile = {}
for rel, _ in hex64_all:
    byfile[rel] = byfile.get(rel, 0) + 1
for k, v in sorted(byfile.items()):
    print(f"   {k}: {v}")
