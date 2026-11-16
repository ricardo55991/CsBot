"""Verificação semântica do contrato de domínios (§4) — SOMENTE LEITURA.

Checa: domínios, subdomínios, campos obrigatórios, proibição de conversão,
exclusão de FACEIT 1-4 e 9-10, Premier NOT_DEFINED, UNKNOWN não promovido,
e presença integral dos critérios de aceitação/exclusão do §7.
"""
import json
import os
import re

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
d = json.loads(open(os.path.join(ROOT, "datasets/mirage_domains/domain_contract_v1.json"),
                    encoding="utf-8").read())

print("TOPKEYS:", list(d.keys()))
for k, v in d.items():
    t = type(v).__name__
    n = len(v) if hasattr(v, "__len__") else v
    print(f"  {k}: {t} ({n})")

print()
print("=== domains ===")
print(json.dumps(d.get("domains"), indent=1, ensure_ascii=False)[:1500])
print()
print("=== subdomains keys ===")
sub = d.get("subdomains")
if isinstance(sub, dict):
    for k, v in sub.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:220]}")
elif isinstance(sub, list):
    for v in sub:
        print("  ", json.dumps(v, ensure_ascii=False)[:220])
