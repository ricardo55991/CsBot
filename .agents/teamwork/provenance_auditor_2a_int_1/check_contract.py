"""Checagem semântica do contrato de domínios vs §4/§6/§7 do ORIGINAL_REQUEST.

Enumerações da spec são recontadas AQUI a partir do texto literal do ORIGINAL_REQUEST
(intervalos de linhas citados), nunca copiadas de tabela de terceiros.
"""
import json
import os
import re

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"

# ---- Enumerações recontadas do texto literal de ORIGINAL_REQUEST.md -------------
# §4 "Campos obrigatórios:" linhas 1139-1157 -> 17 itens (contados abaixo por regex)
# §7 "Uma demo candidata deve possuir:" linhas 1288-1302 -> 13 itens
# §7 "Excluir ou sinalizar:" linhas 1304-1317 -> 11 itens
SPEC = r".agents/teamwork/ORIGINAL_REQUEST.md"
lines = open(os.path.join(ROOT, SPEC), encoding="utf-8").read().splitlines()


def block(a, b):
    return [ln for ln in lines[a - 1:b]]


fields_block = block(1139, 1157)
FIELDS = []
for ln in fields_block:
    t = ln.strip()
    if not t or t.startswith("#") or t.startswith("Campos"):
        continue
    FIELDS.append(t)
accept_block = [ln.strip() for ln in block(1288, 1302) if ln.strip() and not ln.strip().endswith(":")]
excl_block = [ln.strip() for ln in block(1304, 1317) if ln.strip() and not ln.strip().startswith("Excluir") and not ln.strip().endswith(":")]

print(f"§4 campos obrigatórios (linhas 1139-1157) recontados: {len(FIELDS)}")
for f in FIELDS:
    print("   -", f)
print(f"§7 aceitação (linhas 1288-1302) recontados: {len(accept_block)}")
print(f"§7 exclusão (linhas 1304-1317) recontados: {len(excl_block)}")

# ---- Contrato -----------------------------------------------------------------
c = json.loads(open(os.path.join(ROOT, "datasets/mirage_domains/domain_contract_v1.json"),
                   encoding="utf-8").read())
flat = json.dumps(c, ensure_ascii=False)
mand = [m.get("field") if isinstance(m, dict) else m for m in c["mandatory_fields"]]
print()
print("contrato: mandatory_fields_count =", c["mandatory_fields_count"], "| len(lista) =", len(mand))
missing = [f for f in FIELDS if f not in mand]
print("campos do §4 ausentes no contrato:", missing)
print("ratio campos:", f"({len([f for f in FIELDS if f in mand])}/{len(FIELDS)})")

print()
print("=== rank_conversion_policy ===")
print(json.dumps(c["rank_conversion_policy"], indent=1, ensure_ascii=False))
print()
print("=== faceit_buckets ===")
print(json.dumps(c["faceit_buckets"], indent=1, ensure_ascii=False)[:1800])
print()
print("=== valve_premier_policy ===")
print(json.dumps(c["valve_premier_policy"], indent=1, ensure_ascii=False))
print()
print("=== excluded_from_primary_corpus ===")
print(json.dumps(c["excluded_from_primary_corpus"], indent=1, ensure_ascii=False)[:1500])
print()
print("=== demo_acceptance_criteria (", len(c["demo_acceptance_criteria"]), ") ===")
for x in c["demo_acceptance_criteria"]:
    print("   ", json.dumps(x, ensure_ascii=False)[:200])
print()
print("=== demo_exclusion_criteria (", len(c["demo_exclusion_criteria"]), ") ===")
for x in c["demo_exclusion_criteria"]:
    print("   ", json.dumps(x, ensure_ascii=False)[:200])
print()
print("=== UNKNOWN domain ===")
print(json.dumps(c["domains"].get("UNKNOWN"), indent=1, ensure_ascii=False)[:1600])
