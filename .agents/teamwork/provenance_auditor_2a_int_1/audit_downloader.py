"""Auditoria de conformidade do downloader (§9) — 14 requisitos, por evidência textual no código.

SOMENTE LEITURA. Cada requisito exige >=1 evidência concreta (padrão regex) e é
reportado com os arquivos:linhas que o sustentam.
"""
import json
import os
import re
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
TOOLS = "tools/intermediate_demo_acquisition"

REQS = [
    ("1_resumable_downloads", [r"Range", r"\.part", r"resume", r"Content-Range", r"If-Range"]),
    ("2_exponential_backoff", [r"backoff", r"2\s*\*\*\s*attempt", r"exponential", r"sleep\("]),
    ("3_rate_limiting", [r"rate_limit", r"RateLimiter", r"token_bucket", r"burst", r"requests_per_second"]),
    ("4_checksum", [r"sha256", r"checksum", r"hashlib"]),
    ("5_archive_validation", [r"magic", r"PK\\\\x03", r"zipfile", r"tarfile", r"is_zipfile"]),
    ("6_secure_decompression_path_traversal", [r'"\.\."', r"'\.\.'", r"resolve\(\)", r"is_absolute\(\)", r"OUTSIDE_DEST_ROOT", r"path traversal", r"traversal"]),
    ("7_duplicate_detection_by_hash", [r"dedup", r"duplicate", r"known_hashes", r"seen_hashes"]),
    ("8_dry_run_default", [r"dry.run", r"dry_run", r"--execute", r"DRY_RUN"]),
    ("9_domain_allowlist", [r"allowed_domains", r"allowlist", r"RECUSADO_DOMINIO", r"DOMAIN_NOT_ALLOWED", r"urlsplit|urlparse"]),
    ("10_audit_log", [r"audit_log", r"jsonl", r"append", r"event"]),
    ("11_credential_redaction", [r"redact", r"REDACTED", r"mask"]),
    ("12_retry_limit", [r"retry_limit", r"max_retries", r"MAX_RETRIES", r"retry"]),
    ("13_quarantine", [r"quarantine", r"QUARANTINE"]),
    ("14_secrets_from_env_or_secret_store", [r"os\.environ|os\.getenv|getenv", r"secret_source", r"secret_env_vars", r"ENV"]),
]

files = {}
for dp, dn, fn in os.walk(os.path.join(ROOT, TOOLS)):
    dn[:] = [x for x in dn if x != "__pycache__"]
    for f in fn:
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            files[rel] = open(p, "rb").read().decode("utf-8", "replace")
        except OSError:
            pass

print("### ARQUIVOS DE tools/intermediate_demo_acquisition (excluindo __pycache__)")
for rel in sorted(files):
    print(f"   {rel}  ({len(files[rel].encode('utf-8', 'ignore'))} bytes)")

result = {"requirements": [], "files": sorted(files)}
for name, pats in REQS:
    evid = []
    for rel, text in files.items():
        for pat in pats:
            for m in re.finditer(pat, text):
                line = text.count("\n", 0, m.start()) + 1
                ln = text.splitlines()[line - 1].strip()[:150]
                evid.append({"path": rel, "line": line, "pattern": pat, "text": ln})
                break
    files_hit = sorted({e["path"] for e in evid})
    result["requirements"].append({
        "requirement": name, "satisfied": len(evid) > 0,
        "files": files_hit, "evidence_count": len(evid), "evidence": evid[:6],
    })
    print()
    print(f"[{'OK  ' if evid else 'FAIL'}] {name}  files={files_hit}")
    for e in evid[:4]:
        print(f"        {e['path']}:{e['line']}  {e['text'][:120]}")

sat = sum(1 for r in result["requirements"] if r["satisfied"])
result["ratio"] = f"({sat}/{len(REQS)})"
print()
print(f"REQUISITOS §9 ATENDIDOS: {result['ratio']}")

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "downloader_compliance.json"), "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=1, ensure_ascii=False)
