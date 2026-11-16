"""Checagens finais: nomes dos 20 testes vs §20 literal; métricas N/A; URLs inline fora da §12."""
from __future__ import annotations

import json
import re
from difflib import unified_diff
from pathlib import Path

ROOT = Path(".").resolve()
TEST = ROOT / "tests/test_phase2a_intermediate_domain.py"
SPEC = ROOT / ".agents/teamwork/ORIGINAL_REQUEST.md"
REPORT = ROOT / "training_runs/intermediate_domain_study/source_feasibility_report.md"

# 1) nomes exigidos pela §20, extraídos do texto literal da especificação
spec_lines = SPEC.read_text(encoding="utf-8", errors="replace").splitlines()
start = next(i for i, l in enumerate(spec_lines) if l.startswith("# 20."))
end = next(i for i, l in enumerate(spec_lines) if l.startswith("# 21."))
spec_names = []
for line in spec_lines[start:end]:
    match = re.match(r"^(\d{1,2})\.\s+([A-Za-z][A-Za-z0-9]+)\s*$", line.strip())
    if match:
        spec_names.append(match.group(2))
print(f"§20 nomes extraídos da especificação: {len(spec_names)}")

test_src = TEST.read_text(encoding="utf-8")
block = re.search(r"REQUIRED_TEST_NAMES: Tuple\[str, \.\.\.\] = \((.*?)\)\n", test_src, re.S).group(1)
impl_names = re.findall(r'"([A-Za-z][A-Za-z0-9]+)"', block)
print(f"REQUIRED_TEST_NAMES na suíte: {len(impl_names)}")

missing = [n for n in spec_names if n not in impl_names]
extra = [n for n in impl_names if n not in spec_names]
print(f"faltando na suíte: {missing}")
print(f"sobrando na suíte: {extra}")
print(f"ORDEM idêntica: {spec_names == impl_names}")
if spec_names != impl_names:
    print("\n".join(unified_diff(spec_names, impl_names, "spec", "impl", lineterm="")))

# funções realmente definidas
defined = set(re.findall(r"^def ([A-Z][A-Za-z0-9]*)\(\):", test_src, re.M))
print(f"funções definidas com nome canônico: {len(defined)}  todas as 20 presentes: {set(spec_names) <= defined}")
print(f"definidas que não estão na §20: {sorted(defined - set(spec_names))}")

# 2) métricas N/A em professional_vs_intermediate.json
pvi = json.loads((ROOT / "training_runs/intermediate_domain_study/professional_vs_intermediate.json").read_text(encoding="utf-8"))
print("\n=== professional_vs_intermediate: 15 métricas ===")
print("chaves de metrics[0]:", list(pvi["metrics"][0].keys()))
bad = []
for metric in pvi["metrics"]:
    mid = metric.get("metric_id")
    blob = json.dumps(metric, ensure_ascii=False)
    has_na = "N/A" in blob or '"(0/0)"' in blob
    numeric_values = [k for k, v in metric.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if not has_na or numeric_values:
        bad.append((mid, has_na, numeric_values))
print(f"métricas sem rótulo N/A ou com número bruto: {len(bad)} -> {bad}")

# 3) URLs citadas inline no relatório fora da tabela §12
text = REPORT.read_text(encoding="utf-8")
table_block = text[text.index("## 12."):]
table_urls = set(re.findall(r"https?://\S+", table_block))
inline_urls = set(re.findall(r"https?://[^\s`)\]\"']+", text[:text.index("## 12.")]))
norm = lambda u: u.rstrip(".,;)]`\"'")
table_norm = {norm(u) for u in table_urls}
outside = sorted({norm(u) for u in inline_urls} - table_norm)
print(f"\n=== URLs citadas no corpo fora da tabela §12: {len(outside)} ===")
for u in outside:
    print("  -", u)
