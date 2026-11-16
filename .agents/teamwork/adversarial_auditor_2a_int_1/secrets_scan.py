"""Varredura independente de segredos (autotestada) — FASE 2A-INTERMEDIATE.

Somente leitura sobre o repositório; escreve nada além de stdout.
Fase 1: autoteste do detector com fixtures positivas (devem disparar) e negativas (nao devem).
Fase 2: varredura dos alvos reais.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(".").resolve()

# --- padroes de segredo ------------------------------------------------------
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS_ACCESS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS_SECRET_LIKE", re.compile(r"(?i)aws_secret_access_key\s*[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{20,}")),
    ("GITHUB_TOKEN", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("SLACK_TOKEN", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("BASIC_AUTH_URL", re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]{1,64}:[^/\s:@]{1,64}@[a-z0-9.-]+")),
    ("SIGNED_URL_PARAM", re.compile(r"(?i)[?&](X-Amz-Signature|X-Amz-Credential|sig|signature|token|apikey|api_key|key)=[^&\s\"']{8,}")),
    ("ASSIGNED_SECRET", re.compile(
        r"(?i)[\"']?(api[_-]?key|apikey|secret|secret[_-]?key|access[_-]?token|auth[_-]?token|bearer|password|passwd|client[_-]?secret|data[_-]?api[_-]?key)[\"']?\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']"
    )),
    ("STEAMID64", re.compile(r"\b7656119\d{10}\b")),
]

# Valores que NAO sao segredo (placeholders, nomes de variavel de ambiente, redacoes).
SAFE_VALUE = re.compile(
    r"^(?:"
    r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+"          # ENV_VAR_NAME
    r"|[a-z][a-z0-9]*(?:_[a-z0-9]+)+"         # snake_case: nome de campo/variavel, nao valor
    r"|\$\{?[A-Za-z_]+\}?"                    # $VAR / ${VAR}
    r"|<[^>]*>"                               # <...>
    r"|(?i:your[_-].*|change[_-]?me|placeholder|redacted|example|dummy|sample|xxx+|none|null|todo|n/?a|empty)"
    r").*$"
)

#: Valores de fixture obviamente ficticios (hex "de brinquedo") nao sao segredo.
DUMMY_VALUE = re.compile(r"(?i)^(?:dead|beef|cafe|baadf00d|deadbeef|cafebabe|0{4,}|f{4,}|a{4,})(?:[0-9a-f]*)$")


def scan_text(text: str, label: str) -> list[tuple[str, str, str]]:
    findings: list[tuple[str, str, str]] = []
    for name, pattern in PATTERNS:
        for match in pattern.finditer(text):
            snippet = match.group(0)
            value = match.group(2) if match.lastindex and match.lastindex >= 2 else snippet
            value = value or ""
            if name == "ASSIGNED_SECRET" and (SAFE_VALUE.match(value) or DUMMY_VALUE.match(value)):
                continue
            if name == "SIGNED_URL_PARAM":
                tail = value.rsplit("=", 1)[-1]
                if DUMMY_VALUE.match(tail):
                    continue
            if name == "STEAMID64" and value.startswith("7656119800000000"):
                continue
            findings.append((name, label, snippet[:120]))
    return findings


# --- fase 1: autoteste ------------------------------------------------------
POSITIVE_FIXTURES = {
    "aws_key": "const k = 'AKIAIOSFODNN7EXAMPLE1';",
    "github": "token ghp_" + "A" * 36,
    "jwt": "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----",
    "basic_auth_url": "https://admin:S3cr3tP4ss@internal.example.com/x",
    "signed_url": "https://x.example.com/a.dem?X-Amz-Signature=9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "assigned_secret": "\"api_key\": \"a1b2c3d4e5f6g7h8i9j0\"",
    "steamid64": "steamid=76561198292471822",
    "slack": "xoxb-" + "1" * 12,
    "aws_secret": "aws_secret_access_key = wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY",
}
NEGATIVE_FIXTURES = {
    "env_var_name": "\"api_key_env_var\": \"FACEIT_DATA_API_KEY\"",
    "placeholder": "\"api_key\": \"YOUR_API_KEY_HERE\"",
    "redacted": "\"secret\": \"<REDACTED>\"",
    "shell_var": "\"token\": \"${FACEIT_TOKEN}\"",
    "null_value": "\"password\": \"null\"",
    "pid_pseudonym": "\"steamid_pseudonym\": \"PID_0123456789abcdef\"",
    "dummy_hex_signature": "https://x.example.com/a.dem?X-Amz-Signature=deadbeef",
    "snake_case_field_ref": "\"requires_secret\": \"faceit_data_api_key\"",
    "synthetic_steamid_range": "steamid=76561198000000001",
}

print("=" * 100)
print("FASE 1 — AUTOTESTE DO DETECTOR")
print("=" * 100)
pos_hits = 0
for label, payload in POSITIVE_FIXTURES.items():
    hits = scan_text(payload, label)
    ok = len(hits) > 0
    pos_hits += 1 if ok else 0
    print(f"  [{'OK ' if ok else 'MISS'}] positivo '{label}' -> {len(hits)} match(es) {[h[0] for h in hits]}")
neg_fp = 0
for label, payload in NEGATIVE_FIXTURES.items():
    hits = scan_text(payload, label)
    ok = len(hits) == 0
    neg_fp += 0 if ok else 1
    print(f"  [{'OK ' if ok else 'FP  '}] negativo '{label}' -> {len(hits)} match(es) {[h[0] for h in hits]}")

print(f"\nAUTOTESTE: fixtures positivas disparadas = ({pos_hits}/{len(POSITIVE_FIXTURES)})")
print(f"AUTOTESTE: fixtures negativas sem falso-positivo = ({len(NEGATIVE_FIXTURES)-neg_fp}/{len(NEGATIVE_FIXTURES)})")

# --- fase 2: alvos reais ----------------------------------------------------
TARGETS: list[Path] = []
for directory, globs in [
    ("datasets/mirage_domains", ["**/*.json", "**/*.md"]),
    ("training_runs/intermediate_domain_study", ["*.json", "*.md"]),
    ("tools/intermediate_demo_acquisition", ["*.py", "*.json", "*.md"]),
]:
    for pattern in globs:
        TARGETS.extend(sorted((ROOT / directory).glob(pattern)))
TARGETS.extend([
    ROOT / "training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json",
    ROOT / "tests/test_phase2a_intermediate_domain.py",
    ROOT / "scratch/2a_intermediate_research_cache/_recapture_log.json",
])

seen = set()
unique_targets = []
for t in TARGETS:
    if t.is_file() and t not in seen:
        seen.add(t)
        unique_targets.append(t)

print("\n" + "=" * 100)
print(f"FASE 2 — VARREDURA REAL ({len(unique_targets)} arquivos)")
print("=" * 100)
total_findings = 0
bytes_scanned = 0
for path in unique_targets:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:  # pragma: no cover
        print(f"  ERRO ao ler {path}: {exc}")
        continue
    bytes_scanned += len(text.encode("utf-8", errors="replace"))
    rel = path.relative_to(ROOT).as_posix()
    hits = scan_text(text, rel)
    if hits:
        total_findings += len(hits)
        print(f"  [!] {rel}")
        for name, _, snippet in hits[:10]:
            print(f"        {name}: {snippet}")
    elif "--verbose" in __import__("sys").argv:
        print(f"  [ok] {rel}")

print("\n" + "=" * 100)
print(f"RESULTADO: arquivos varridos = {len(unique_targets)}; bytes varridos = {bytes_scanned}")
print(f"RESULTADO: achados de segredo = {total_findings} em {len(unique_targets)} arquivos")
print("=" * 100)
