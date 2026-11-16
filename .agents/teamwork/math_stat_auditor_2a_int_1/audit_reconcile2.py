import json, os, collections

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")
def jl(p): return json.loads(open(p, "rb").read().decode("utf-8"))

sup = jl(os.path.join(ROOT, "training_runs/positioning_v2_real_temporal/revised_spot_supervision_report.json"))
cov = jl(os.path.join(STUDY, "spot_domain_coverage.json"))

per = sup["per_spot_support"]
print("tipo de per_spot_support: %s len=%d" % (type(per).__name__, len(per)))
k0 = next(iter(per))
print("exemplo:", k0, "->", json.dumps(per[k0], ensure_ascii=False)[:400])

def get_split(entry):
    if isinstance(entry, dict):
        if all("%s_support" % x in entry for x in ("train", "validation", "test")):
            return {"train": entry["train_support"], "validation": entry["validation_support"], "test": entry["test_support"]}
        if "per_split" in entry:
            return entry["per_split"]
        if all(x in entry for x in ("train", "validation", "test")):
            return {x: entry[x] for x in ("train", "validation", "test")}
        for kk in ("support_sequences", "support", "counts"):
            if kk in entry and isinstance(entry[kk], dict):
                return get_split(entry[kk])
    return None

ok = 0; bad = []
sp = collections.Counter()
for s in cov["spots"]:
    sid = s["spot_id"]
    exp = s["professional"]["support_sequences"]["per_split"]
    src = get_split(per.get(sid))
    if src is None:
        bad.append((sid, "UNPARSEABLE", json.dumps(per.get(sid), ensure_ascii=False)[:150])); continue
    if all(int(src[k]) == int(exp[k]) for k in ("train", "validation", "test")):
        ok += 1
        for k in ("train", "validation", "test"):
            sp[k] += int(src[k])
    else:
        bad.append((sid, exp, src))

print("\nspots reconciliados per-split contra a fonte: (%d/%d)" % (ok, len(cov["spots"])))
print("divergencias: %d" % len(bad))
for x in bad[:10]:
    print("   !", x)
print("soma a partir da FONTE (nao do artefato):", dict(sp), "total =", sum(sp.values()))

# cobertura de ids
sup_ids = set(sup["per_spot_support"].keys())
cov_ids = set(s["spot_id"] for s in cov["spots"])
print("\nids iguais (supervision vs coverage)?", sup_ids == cov_ids)
print("unsupported_spot_ids == spots INSUFFICIENT_SUPPORT do artefato??")
ins = set(s["spot_id"] for s in cov["spots"] if s["classification"] == "INSUFFICIENT_SUPPORT")
print("  igual?", ins == set(sup["unsupported_spot_ids"]), "| n ins=", len(ins), "| n unsup=", len(sup["unsupported_spot_ids"]))
print("supported_spot_ids == PROFESSIONAL_CONFIRMED?")
pc = set(s["spot_id"] for s in cov["spots"] if s["classification"] == "PROFESSIONAL_CONFIRMED")
print("  igual?", pc == set(sup["supported_spot_ids"]), "| n pc=", len(pc), "| n sup=", len(sup["supported_spot_ids"]))
print("\ngovernance_compliance:", json.dumps(sup["governance_compliance"], ensure_ascii=False))
