import json, os, sys, re, collections

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")
def load(p):
    return json.loads(open(p, "rb").read().decode("utf-8"))

cov = load(os.path.join(STUDY, "spot_domain_coverage.json"))
spots = cov["spots"]
print("N spots =", len(spots))

print("\n--- chaves de um spot (primeiro) ---")
print(json.dumps(spots[0], ensure_ascii=False, indent=1)[:6000])
