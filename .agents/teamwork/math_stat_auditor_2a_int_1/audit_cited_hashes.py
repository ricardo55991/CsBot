import json, os, hashlib, re, collections

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")
FILES = ["ct_standardization_analysis.json","tr_standardization_analysis.json","professional_vs_intermediate.json",
         "spot_domain_coverage.json","unmapped_intermediate_clusters.json","pilot_corpus_quality.json"]

# varre o JSON cru por triplas path/sha/size
triples = collections.OrderedDict()
for f in FILES:
    d = json.loads(open(os.path.join(STUDY, f), "rb").read().decode("utf-8"))
    def walk(n):
        if isinstance(n, dict):
            p = n.get("repo_relative_path")
            h = n.get("sha256")
            s = n.get("size_bytes")
            if isinstance(p, str) and isinstance(h, str):
                triples.setdefault((p, h, s), []).append(f)
            for v in n.values(): walk(v)
        elif isinstance(n, list):
            for v in n: walk(v)
    walk(d)
    # tambem pega pares path/sha no nivel superior (ex.: catalog_path + catalog_sha256)
    for k, v in d.items():
        if k.endswith("_path") and isinstance(v, str):
            base = k[:-5]
            h = d.get(base + "_sha256"); s = d.get(base + "_size_bytes")
            if isinstance(h, str):
                triples.setdefault((v, h, s), []).append(f + ":" + k)

print("Triplas (path, sha, size) citadas nos 6 artefatos: %d" % len(triples))
ok = bad = missing = 0
for (p, h, s), src in triples.items():
    fp = os.path.join(ROOT, p.replace("/", os.sep))
    if not os.path.exists(fp):
        print("  MISSING ON DISK: %s  (citado em %s)" % (p, ",".join(sorted(set(src)))))
        missing += 1; continue
    b = open(fp, "rb").read()
    a = hashlib.sha256(b).hexdigest()
    good = (a == h) and (s is None or int(s) == len(b))
    if good:
        ok += 1
    else:
        bad += 1
        print("  MISMATCH: %s\n     citado sha=%s size=%s\n     disco   sha=%s size=%d" % (p, h, s, a, len(b)))
print("RESULTADO: (%d/%d) triplas verificadas com hash+tamanho exatos; %d mismatch; %d ausentes"
      % (ok, len(triples), bad, missing))
