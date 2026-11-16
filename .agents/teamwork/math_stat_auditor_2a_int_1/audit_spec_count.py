import json, os

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")
def load(f):
    return json.loads(open(os.path.join(STUDY, f), "rb").read().decode("utf-8"))

SPEC = {
 "ct_standardization_analysis.json": ([
  "initial setup after freeze time","A occupancy","Mid occupancy","B occupancy","2-1-2 setup rate",
  "heavy-A rate","heavy-B rate","empty-site rate","double-stack rate","anchor dwell",
  "first rotation tick","rotation distance","unnecessary rotation proxy","retake frequency",
  "save frequency","sector stability","spot recurrence"], 1497, 1513),
 "tr_standardization_analysis.json": ([
  "default spread","grouped execute rate","solo lurk rate","bomb carrier isolation",
  "entry order consistency","trade spacing","site commitment time","mid-control rate",
  "split-A rate","split-B rate","fake rate","post-plant convergence","save rate",
  "spot recurrence","transition recurrence"], 1527, 1541),
 "professional_vs_intermediate.json": ([
  "unique position clusters","cluster radius","cluster entropy","recurring spot rate",
  "top-spot concentration","sector occupancy","dwell distribution","transition diversity",
  "2-1-2 rate","retake rate","post-plant pattern diversity","role stability",
  "setup stability","player diversity","team diversity"], 1566, 1580),
 "spot_domain_coverage.json": ([
  "support sequences","support episodes","unique demos","unique matches","unique players",
  "unique teams/stacks","median dwell","position variance","approach direction","exit direction",
  "primary aim distribution","state distribution","role distribution","side","bombsite"], 1601, 1615),
}

def norm(s):
    return " ".join(str(s).lower().replace("_", " ").replace("-", " ").split())

for f, (spec_list, l0, l1) in SPEC.items():
    d = load(f)
    if f == "spot_domain_coverage.json":
        got = [x["statistic_name"] if "statistic_name" in x else x.get("name") for x in d["statistic_definitions"]]
        key = "statistic_definitions"
    else:
        got = [m["metric_name"] for m in d["metrics"]]
        key = "metrics"
    print("="*95)
    print(f, "->", key, "len =", len(got), "| spec itens =", len(spec_list), "(linhas %d-%d)" % (l0, l1))
    print("  declara metric_count/statistic_count:", json.dumps(d.get("metric_count") or d.get("statistic_count"), ensure_ascii=False)[:400])
    ng = [norm(x) for x in got]; ns = [norm(x) for x in spec_list]
    print("  -- ordem/pareamento --")
    for i, s in enumerate(spec_list):
        g = got[i] if i < len(got) else "<AUSENTE>"
        mark = "OK  " if i < len(ng) and ng[i] == norm(s) else ("DIFF")
        print("   %2d %s spec='%s'  artefato='%s'" % (i+1, mark, s, g))
    print("  extras no artefato (nao na spec):", [g for g in got if norm(g) not in ns])
    print("  faltando no artefato:", [s for s in spec_list if norm(s) not in ng])
    print("  duplicatas no artefato:", [k for k, v in __import__("collections").Counter(ng).items() if v > 1])
