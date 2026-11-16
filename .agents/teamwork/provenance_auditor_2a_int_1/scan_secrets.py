"""Scanner de segredos próprio (auditoria de proveniência/compliance) — CsBot FASE 2A-INTERMEDIATE.

Escrito e executado integralmente dentro de `.agents/teamwork/provenance_auditor_2a_int_1/`.
Não escreve nada fora do diretório do auditor. SOMENTE LEITURA no repositório.

Uso:
    python scan_secrets.py --self-test                # autoteste de fixtures (obrigatório)
    python scan_secrets.py --scan --out secrets_scan_result.json

Regras de detecção (11 detetores positivos) + supressores (5 regras negativas).
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"

# ---------------------------------------------------------------------------
# DETECTORES POSITIVOS
# ---------------------------------------------------------------------------
DETECTORS = [
    ("OPENAI_SK", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("GITHUB_PAT_CLASSIC", re.compile(r"\bghp_[A-Za-z0-9]{30,}\b")),
    ("GITHUB_PAT_FINE", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("AWS_AKIA", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")),
    ("STEAM_LOGIN_SECURE_ASSIGN", re.compile(r"steamLoginSecure\s*[:=]\s*[\"']?([^\s\"',;}]{8,})", re.I)),
    ("PASSWORD_ASSIGN", re.compile(r"(?i)\b[A-Za-z0-9_\-]*(?:password|passwd|pwd)\b\s*[:=]\s*[\"']?([^\s\"',;}]{8,})")),
    ("TOKEN_ASSIGN", re.compile(r"(?i)\b[A-Za-z0-9_\-]*token\b\s*[:=]\s*[\"']?([A-Za-z0-9_\-\.+/]{16,})")),
    ("AWS_SIGNATURE", re.compile(r"X-Amz-Signature\s*=\s*([0-9a-fA-F]{16,})")),
    ("AUTH_HEADER", re.compile(r"(?i)authorization\s*[:=]\s*[\"']?(?:Bearer|Basic)\s+([A-Za-z0-9_\-\.=+/]{12,})", re.I)),
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
]

# ---------------------------------------------------------------------------
# SUPRESSORES (regras negativas)
# ---------------------------------------------------------------------------
VALUE_PLACEHOLDER = re.compile(r"^(<.*>|\{\{.*\}\}|\$\{.*\}|%.*%|\[.*\]|\.\.\.|<.*|.*>)$")
PLACEHOLDER_WORDS = re.compile(
    r"(?i)(your|my_|my-|example|sample|dummy|changeme|change_me|placeholder|redacted|"
    r"replace|insert|todo|xxxx|fake|not_a_real|no_|none|null|n/?a|set_in|from_env|env)"
)
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
NAMED_EXAMPLE_VALUES = {"deadbeef", "deadbeefdeadbeef", "akiaiosfodnn7example"}
SHA_CONTEXT = re.compile(r"(?i)(sha256|sha-256|checksum|hash|digest|fingerprint)")
CODE_CONTEXT_SAFE = re.compile(r"(?i)(os\.environ|os\.getenv|getenv|ENV\[|environ\[|secret_store|SecretStore|-----BEGIN [A-Z ]*PUBLIC KEY)")


STRUCTURAL_DETECTORS = {
    "OPENAI_SK", "GITHUB_PAT_CLASSIC", "GITHUB_PAT_FINE", "AWS_AKIA",
    "JWT", "AWS_SIGNATURE", "PRIVATE_KEY_BLOCK",
}


def _suppress(value, line, detname):
    """Retorna motivo de supressão, ou None se deve disparar."""
    v = (value or "").strip().strip('"\'').strip()
    low = v.lower()
    if not v:
        return "EMPTY_VALUE"
    if VALUE_PLACEHOLDER.match(v):
        return "PLACEHOLDER_ANGLE_BRACE"
    if low in NAMED_EXAMPLE_VALUES:
        return "NAMED_EXAMPLE_LITERAL"
    if detname in STRUCTURAL_DETECTORS:
        # formato estrutural inequívoco: sem supressão por palavra de placeholder
        return None
    if ENV_NAME.match(v) and not HEX64.match(v):
        return "ENV_VAR_NAME_REFERENCE"
    if HEX64.match(v) and SHA_CONTEXT.search(line):
        return "DOCUMENTED_SHA256"
    if PLACEHOLDER_WORDS.search(v) and not HEX64.match(v):
        return "PLACEHOLDER_WORD"
    if CODE_CONTEXT_SAFE.search(line):
        return "SAFE_CODE_REFERENCE"
    return None


def scan_text(text, origin="<mem>"):
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for detname, rx in DETECTORS:
            for m in rx.finditer(line):
                value = m.group(1) if m.groups() else m.group(0)
                reason = _suppress(value, line, detname)
                if reason:
                    continue
                hits.append({
                    "line": lineno,
                    "detector": detname,
                    "value_sha256_prefix": hashlib.sha256(value.encode("utf-8", "ignore")).hexdigest()[:12],
                    "value_length": len(value),
                    "context": line.strip()[:200],
                    "origin": origin,
                })
    return hits


# ---------------------------------------------------------------------------
# FIXTURES DE AUTOTESTE
# ---------------------------------------------------------------------------
POSITIVE_FIXTURES = [
    ("P01_OPENAI_SK", "OPENAI_SK", 'openai_key = "sk-liveAAAAAAAAAAAAAAAAAAAAAAAA123456"'),
    ("P02_GHP", "GITHUB_PAT_CLASSIC", "gh_token: ghp_Aa1Bb2Cc3Dd4Ee5Ff6Gg7Hh8Ii9Jj0Kk1Ll2"),
    ("P03_GITHUB_PAT_FINE", "GITHUB_PAT_FINE", "github_pat_11ABCDEFG0abcdefghijklmnopqrstuv"),
    ("P04_AKIA", "AWS_AKIA", "key = AKIA4T7Q2XK9PLM3NRVZ"),
    ("P05_JWT", "JWT", "bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"),
    ("P06_STEAM", "STEAM_LOGIN_SECURE_ASSIGN", "Cookie: steamLoginSecure=76561198000000000%7C%7C8f4a2b1c9d3e5f7a"),
    ("P07_PASSWORD", "PASSWORD_ASSIGN", 'db_password: "Sup3rS3cretValue!"'),
    ("P08_TOKEN", "TOKEN_ASSIGN", "token=4f9a2b7c1d8e3f6a9b0c5d2e7f1a8b3c9d0e1f2a"),
    ("P09_AMZ", "AWS_SIGNATURE", "https://x.example/y?X-Amz-Signature=3f8a9c2b1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f80"),
    ("P10_AUTH_HEADER", "AUTH_HEADER", "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abcdefghijklmn"),
    ("P11_PRIVATE_KEY", "PRIVATE_KEY_BLOCK", "-----BEGIN RSA PRIVATE KEY-----"),
]

NEGATIVE_FIXTURES = [
    ("N01_VALUE_FROM_ENV", "api_token: <VALUE_FROM_ENV>"),
    ("N02_YOUR_TOKEN_HERE", '"token": "<YOUR_TOKEN_HERE>"'),
    ("N03_ENV_VAR_NAME", 'token: "FACEIT_API_TOKEN"'),
    ("N04_DOC_SHA256", '"artifact_sha256": "95df901801d0a96495c7d3b30d08862513563b1b790e202b0738369fec02ae28"'),
    ("N05_DEADBEEF_SIG", "X-Amz-Signature=deadbeef"),
    ("N06_STEAM_NAME_ONLY", 'prohibited_cookie_names: ["steamLoginSecure", "sessionid"]'),
]


def self_test():
    fired, silent_ok, failures = 0, 0, []
    print("=== AUTOTESTE DO DETECTOR ===")
    for name, expected, sample in POSITIVE_FIXTURES:
        hits = scan_text(sample, name)
        got = {h["detector"] for h in hits}
        ok = expected in got
        fired += 1 if ok else 0
        print(f"  [{'FIRED ' if ok else 'MISS  '}] {name}: esperado={expected} obtido={sorted(got)}")
        if not ok:
            failures.append(f"POSITIVE_NOT_FIRED:{name}")
    for name, sample in NEGATIVE_FIXTURES:
        hits = scan_text(sample, name)
        ok = len(hits) == 0
        silent_ok += 1 if ok else 0
        print(f"  [{'SILENT' if ok else 'NOISE '}] {name}: hits={[(h['detector'], h['context'][:60]) for h in hits]}")
        if not ok:
            failures.append(f"NEGATIVE_FIRED:{name}")
    total = len(POSITIVE_FIXTURES) + len(NEGATIVE_FIXTURES)
    print()
    print(f"RESULTADO AUTOTESTE: positivos que dispararam ({fired}/{len(POSITIVE_FIXTURES)}); "
          f"negativos silenciosos ({silent_ok}/{len(NEGATIVE_FIXTURES)}); "
          f"fixtures totais ({fired + silent_ok}/{total})")
    print(f"VEREDITO AUTOTESTE: {'PASS' if not failures else 'FAIL ' + str(failures)}")
    return {
        "fixtures_total": total,
        "positives_fired": f"({fired}/{len(POSITIVE_FIXTURES)})",
        "negatives_silent": f"({silent_ok}/{len(NEGATIVE_FIXTURES)})",
        "aggregate": f"({fired + silent_ok}/{total})",
        "failures": failures,
        "self_test_pass": not failures,
        "detectors": [d for d, _ in DETECTORS],
    }


# ---------------------------------------------------------------------------
# ALVOS DE VARREDURA
# ---------------------------------------------------------------------------
TARGET_DIRS = [
    "datasets/mirage_domains",
    "training_runs/intermediate_domain_study",
    "tools/intermediate_demo_acquisition",
]
TARGET_FILES = [
    "training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json",
]
TEXT_EXT = {".json", ".md", ".py", ".txt", ".env", ".cfg", ".ini", ".yaml", ".yml", ".toml", ".example"}


def collect():
    out = []
    for d in TARGET_DIRS:
        base = os.path.join(ROOT, d)
        for dp, dn, fn in os.walk(base):
            dn[:] = [x for x in dn if x != "__pycache__"]
            for f in sorted(fn):
                if os.path.splitext(f)[1].lower() in TEXT_EXT:
                    out.append(os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/"))
    for f in TARGET_FILES:
        if os.path.isfile(os.path.join(ROOT, f)):
            out.append(f)
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser(description="Scanner de segredos autotestado (somente leitura).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--out", default="secrets_scan_result.json")
    a = ap.parse_args()

    st = self_test()
    if not st["self_test_pass"]:
        print("\nABORTANDO: detector reprovado no autoteste -> SECRETS_SCAN_UNVERIFIED")
        return 2
    if not a.scan:
        return 0

    files = collect()
    all_hits, per_file = [], []
    for rel in files:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8", "replace")
        hits = scan_text(text, rel)
        per_file.append({
            "path": rel,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "hits": len(hits),
        })
        all_hits.extend(hits)

    result = {
        "scanner": ".agents/teamwork/provenance_auditor_2a_int_1/scan_secrets.py",
        "self_test": st,
        "files_scanned": len(files),
        "bytes_scanned": sum(x["size_bytes"] for x in per_file),
        "files_with_hits": f"({sum(1 for x in per_file if x['hits'] > 0)}/{len(files)})",
        "files_clean": f"({sum(1 for x in per_file if x['hits'] == 0)}/{len(files)})",
        "hits_total": len(all_hits),
        "hits": all_hits,
        "per_file": per_file,
    }
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, a.out)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)
    print()
    print(f"VARREDURA: {len(files)} arquivos, {result['bytes_scanned']} bytes, {len(all_hits)} hits")
    for h in all_hits:
        print(f"  HIT {h['origin']}:{h['line']} {h['detector']} :: {h['context'][:120]}")
    print(f"JSON de resultado: {path}")
    print(f"bytes={os.path.getsize(path)} sha256={hashlib.sha256(open(path,'rb').read()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
