"""Harness: executa os --self-test dos scripts do downloader e conta casos ok/total.

NÃO executa download. Apenas subprocess --self-test dos 5 scripts que o expõem.
"""
import json
import os
import re
import subprocess
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
SCRIPTS = {
    "validate_skill_bucket.py": 14,
    "verify_archive.py": 8,
    "extract_demo.py": 8,
    "deduplicate_demo.py": 6,
    "resume_download.py": 4,
}

out = {"scripts": [], "totals": {}}
grand_ok = grand_total = 0
for s, expected_cases in SCRIPTS.items():
    p = os.path.join(ROOT, "tools/intermediate_demo_acquisition", s)
    r = subprocess.run([sys.executable, p, "--self-test"], capture_output=True, text=True, cwd=ROOT, timeout=180)
    body = r.stdout
    # isola o JSON do relatorio
    start = body.find("{")
    obj = None
    if start >= 0:
        try:
            obj = json.loads(body[start:])
        except Exception:
            obj = None
    cases = []
    if obj:
        for k, v in obj.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "ok" in v[0]:
                cases = v
    ok = sum(1 for c in cases if c.get("ok"))
    total = len(cases) if cases else 0
    grand_ok += ok
    grand_total += total
    out["scripts"].append({
        "script": s, "exit_code": r.returncode, "cases_ok": ok, "cases_total": total,
        "ratio": f"({ok}/{total})", "declared_cases": expected_cases,
        "all_ok": ok == total and r.returncode == 0 and total > 0,
    })
    print(f"{s}: exit={r.returncode} cases_ok={ok}/{total} declared={expected_cases}")

out["totals"] = {"cases_ok": grand_ok, "cases_total": grand_total, "ratio": f"({grand_ok}/{grand_total})"}
print("TOTAL:", out["totals"])
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "downloader_selftests.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)
