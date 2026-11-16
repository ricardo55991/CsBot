import json, hashlib, os, re, sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")

FILES = [
 "ct_standardization_analysis.json",
 "tr_standardization_analysis.json",
 "professional_vs_intermediate.json",
 "spot_domain_coverage.json",
 "unmapped_intermediate_clusters.json",
 "pilot_corpus_quality.json",
]

for f in FILES:
    p = os.path.join(STUDY, f)
    b = open(p, "rb").read()
    h = hashlib.sha256(b).hexdigest()
    d = json.loads(b.decode("utf-8"))
    print("="*100)
    print(f, "| bytes=", len(b), "| sha256=", h)
    print("TOP-LEVEL KEYS (%d):" % len(d))
    for k, v in d.items():
        t = type(v).__name__
        if isinstance(v, list):
            print("   -", k, ": list[%d]" % len(v))
        elif isinstance(v, dict):
            print("   -", k, ": dict{%d} -> %s" % (len(v), list(v.keys())[:25]))
        else:
            s = str(v)
            print("   -", k, ":", t, "=", s[:160].replace("\n", " "))
