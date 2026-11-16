"""Inspeção estática independente da suíte M8 (somente leitura)."""
from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

P = Path("tests/test_phase2a_intermediate_domain.py")
SRC = P.read_text(encoding="utf-8")
LINES = SRC.splitlines()

print("bytes:", len(SRC.encode()), "lines:", len(LINES))

string_blocks = []
for tok in tokenize.generate_tokens(io.StringIO(SRC).readline):
    if tok.type == tokenize.STRING:
        string_blocks.append((tok.start[0], tok.end[0]))

doc_lines = set()
for start, end in string_blocks:
    if end - start >= 1:
        for ln in range(start, end + 1):
            doc_lines.add(ln)

print("\n=== ocorrencias de 'assert True' (com flag inside_string_block) ===")
hits = 0
for i, line in enumerate(LINES, 1):
    if re.search(r"assert\s+True\b", line):
        inside = i in doc_lines
        print(f"{i}: inside_string_block={inside} | {line.strip()[:140]}")
        hits += 1
print("total ocorrencias textuais:", hits)

print("\n=== ocorrencias de 'assert False' ===")
for i, line in enumerate(LINES, 1):
    if re.search(r"assert\s+False\b", line):
        print(f"{i}: inside_string_block={i in doc_lines} | {line.strip()[:140]}")

print("\n=== skip / xfail / markers ===")
for i, line in enumerate(LINES, 1):
    if re.search(r"pytest\.(skip|xfail)|@pytest\.(mark|fixture)|\.skip\(", line):
        print(f"{i}: {line.strip()[:150]}")

print("\n=== asserts executaveis (linhas fora de string) ===")
n = 0
for i, line in enumerate(LINES, 1):
    if re.match(r"^\s*assert\b", line) and i not in doc_lines:
        n += 1
print("assert statements executaveis:", n)

print("\n=== funcoes nomeadas exatamente / nomes de teste ===")
names = re.findall(r"^def ([A-Za-z_][A-Za-z0-9_]*)\(", SRC, flags=re.M)
print("total defs:", len(names))
caps = [x for x in names if x[0].isupper()]
print("defs com inicial maiuscula:", len(caps))
for c in caps:
    print("  -", c)

print("\n=== aliases expostos ao pytest ===")
print(re.findall(r'globals\(\)\[f"test_\{([^}]*)\}"\]', SRC))

print("\n=== risco de 0/0 em asserts ===")
for i, line in enumerate(LINES, 1):
    if "assert" in line and re.search(r"[/*]\s*(len\(|total|count)", line):
        print(f"{i}: {line.strip()[:150]}")
