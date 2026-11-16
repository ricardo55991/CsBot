import json, os, re, hashlib, collections, math

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")

EXPECTED = {
 "ct_standardization_analysis.json": ("ee3a674aef6fb172d7255e4ef56a0b1e1a5a90c50d43cd88766f18bcbf289494", 55267),
 "tr_standardization_analysis.json": ("f15d12fa7a1e50e2ee00b9684d8d116f3e1467f8be94b4a3f75dcd37102bcc7f", 58793),
 "professional_vs_intermediate.json": ("a552ea2dc15edc73d4c6e324d9035bf0d79e3a8dc04079a44a14addbb20aad96", 68615),
 "spot_domain_coverage.json": ("91d410e8dc9bb2d72b85d8ae803e69948eb03cc6d5c6b111524f4d5c9d9a5a13", 472843),
 "unmapped_intermediate_clusters.json": ("0c5c035e8b5c22574695d5b786c5225776cdc3aaf11f40b5d4b13d60f05c5b23", 13280),
 "pilot_corpus_quality.json": ("c1a50cab6cc292dd5471d0a1b72620870700bb5e36f6871ecdf448a26ab73dc0", 17021),
}
CONTRACTS = {
 "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json": ("8248adc181a6341929f5d916d9ea98322cc8e791156201f8015563a0d8b293f9", 43151),
 "datasets/mirage_v2/contracts/spot_semantic_classification.json": ("cc88bd09f2586bd0f977285f3347a9a42707b5ce4839c67bb59f5c6ad9ac736b", 42391),
}

print("#"*90)
print("CHECK A — HASHES SHA-256 + TAMANHO")
print("#"*90)
ok = 0; tot = 0
for f, (h, sz) in EXPECTED.items():
    p = os.path.join(STUDY, f)
    b = open(p, "rb").read()
    a = hashlib.sha256(b).hexdigest()
    tot += 1
    m = (a == h and len(b) == sz)
    ok += m
    print("%-38s bytes=%-7d (esperado %-7d) %s  sha256=%s  %s" % (f, len(b), sz, "SZ_OK" if len(b)==sz else "SZ_MISMATCH", a, "MATCH" if a==h else "MISMATCH"))
for f, (h, sz) in CONTRACTS.items():
    p = os.path.join(ROOT, f)
    b = open(p, "rb").read()
    a = hashlib.sha256(b).hexdigest()
    tot += 1
    m = (a == h and len(b) == sz)
    ok += m
    print("%-38s bytes=%-7d (esperado %-7d) %s  sha256=%s  %s" % (os.path.basename(f), len(b), sz, "SZ_OK" if len(b)==sz else "SZ_MISMATCH", a, "MATCH" if a==h else "MISMATCH"))
print("RESULTADO HASHES: (%d/%d) MATCH" % (ok, tot))

print()
print("#"*90)
print("CHECK B — INVARIANTE DE SUPPORT ZERO (varredura recursiva numerator/denominator/value)")
print("#"*90)

NONEXEC = re.compile(r"NOT_EXECUTABLE|STRICT_NA|NOT_MATERIALIZED|NOT_AVAILABLE|NO_INTERMEDIATE|NOT_MEASURED", re.I)

def walk(node, path="", out=None):
    if out is None: out = []
    if isinstance(node, dict):
        out.append((path, node))
        for k, v in node.items():
            walk(v, path + "." + k, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + "[%d]" % i, out)
    return out

viol = []
blocks = 0
by_status = collections.Counter()
for f in EXPECTED:
    d = json.loads(open(os.path.join(STUDY, f), "rb").read().decode("utf-8"))
    for path, node in walk(d):
        if isinstance(node, dict) and "numerator" in node and "denominator" in node:
            blocks += 1
            st = node.get("metric_status") or node.get("status") or ""
            by_status[st] += 1
            if NONEXEC.search(str(st)):
                if node.get("value") != "N/A" or node.get("numerator") != 0 or node.get("denominator") != 0:
                    viol.append((f, path, node.get("value"), node.get("numerator"), node.get("denominator"), st))
            # tipo dos campos
            if not isinstance(node.get("numerator"), int) or not isinstance(node.get("denominator"), int):
                viol.append((f, path, "NON_INT", repr(node.get("numerator")), repr(node.get("denominator")), st))
print("Blocos com numerator+denominator encontrados: %d" % blocks)
print("Distribuicao por metric_status:")
for k, v in by_status.most_common():
    print("   %-55s %d" % (k if k else "(vazio)", v))
print("VIOLACOES: %d" % len(viol))
for v in viol[:40]:
    print("   !", v)

print()
print("#"*90)
print("CHECK C — LITERAIS DECIMAIS AUTONOMOS 0.0 / 0.0% (regex com lookbehind)")
print("#"*90)
# (?<![\d.])0\.0(?![\d])  -> nao captura 10.0, 96.0, 100.0, 0.05, 20.0
pat = re.compile(r"(?<![\d.])0\.0(?![0-9])")
pat_pct = re.compile(r"(?<![\d.])0\.0%")
pat_neg = re.compile(r"(?<![\d.])-0\.0(?![0-9])")
tot_hits = 0
for f in EXPECTED:
    txt = open(os.path.join(STUDY, f), "rb").read().decode("utf-8")
    hits = pat.findall(txt)
    hp = pat_pct.findall(txt)
    hn = pat_neg.findall(txt)
    tot_hits += len(hits) + len(hp) + len(hn)
    print("%-38s hits_0.0=%d hits_0.0%%=%d hits_-0.0=%d" % (f, len(hits), len(hp), len(hn)))
    for m in pat.finditer(txt):
        s = max(0, m.start()-70); e = min(len(txt), m.end()+40)
        print("      ctx:", txt[s:e].replace("\n", " "))
print("TOTAL LITERAIS 0.0 AUTONOMOS: %d" % tot_hits)

print()
print("#"*90)
print("CHECK D — QUALQUER LITERAL DECIMAL SEGUIDO DE % EM TODOS OS ARTEFATOS")
print("#"*90)
pct = re.compile(r"(?<![\d.])\d+\.?\d*%")
for f in EXPECTED:
    txt = open(os.path.join(STUDY, f), "rb").read().decode("utf-8")
    ms = pct.findall(txt)
    print("%-38s ocorrencias de '%%': %d %s" % (f, len(ms), collections.Counter(ms).most_common(6)))
