"""Prova funcional das barreiras de segurança do downloader (sem rede, sem escrita).

Importa o módulo com sys.dont_write_bytecode=True para NÃO criar __pycache__ em tools/,
e exercita as funções puras de validação.
"""
import importlib.util
import json
import os
import sys

sys.dont_write_bytecode = True
ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
MOD = os.path.join(ROOT, "tools/intermediate_demo_acquisition/download_demo.py")


def load_mod():
    spec = importlib.util.spec_from_file_location("download_demo_probe", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


dd = load_mod()
cfg = json.loads(open(os.path.join(ROOT, "tools/intermediate_demo_acquisition/config.example.json"),
                      encoding="utf-8").read())
print("allowed_domains =", cfg["network"]["allowed_domains"])
print("signed_url_persistence_allowed =", cfg.get("signed_url_persistence_allowed"))
print("secret_source =", cfg.get("secret_source"))

CASES = [
    ("allowlisted_https_ok", "https://api.faceit.com/data/v4/matches/1-abc", True),
    ("http_rejected", "http://api.faceit.com/data/v4/matches/1-abc", False),
    ("ip_literal_rejected", "https://93.184.216.34/x", False),
    ("userinfo_rejected", "https://user:pass@api.faceit.com/x", False),
    ("offallowlist_rejected", "https://evil.example.com/x", False),
    ("signed_url_rejected", "https://api.faceit.com/x?X-Amz-Signature=3f8a9c2b1d4e5f6a7b8c9d0e1f2a3b4c", False),
]

rows = []
for name, url, should_accept in CASES:
    try:
        dd.validate_url(url, cfg)
        verdict = "ACCEPT"
        msg = ""
    except Exception as e:  # ValidationError
        verdict = "REJECT"
        msg = str(e)[:120]
    ok = (verdict == "ACCEPT") == should_accept
    rows.append({"case": name, "url": url, "verdict": verdict, "ok": ok, "message": msg})
    print(f"[{'ok  ' if ok else 'FAIL'}] {name}: {verdict}  {msg}")

# allowlist vazia deve ser erro
cfg2 = json.loads(json.dumps(cfg))
cfg2["network"]["allowed_domains"] = []
try:
    dd.validate_url("https://api.faceit.com/x", cfg2)
    verdict, msg = "ACCEPT", ""
except Exception as e:
    verdict, msg = "REJECT", str(e)[:120]
ok = verdict == "REJECT"
rows.append({"case": "empty_allowlist_rejected", "url": "https://api.faceit.com/x", "verdict": verdict, "ok": ok, "message": msg})
print(f"[{'ok  ' if ok else 'FAIL'}] empty_allowlist_rejected: {verdict}  {msg}")

passed = sum(1 for r in rows if r["ok"])
print()
print(f"BARREIRAS FUNCIONAIS: ({passed}/{len(rows)})")
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "downloader_functional_probe.json"), "w", encoding="utf-8") as fh:
    json.dump({"cases": rows, "ratio": f"({passed}/{len(rows)})"}, fh, indent=1, ensure_ascii=False)
