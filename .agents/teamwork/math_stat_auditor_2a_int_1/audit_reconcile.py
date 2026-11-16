import json, os, hashlib, collections

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")
def jl(p): return json.loads(open(p, "rb").read().decode("utf-8"))

print("#"*90)
print("CHECK J — RECONCILIACAO PER-SPOT CONTRA revised_spot_supervision_report.json (fonte autoritativa)")
print("#"*90)
sup_p = os.path.join(ROOT, "training_runs/positioning_v2_real_temporal/revised_spot_supervision_report.json")
b = open(sup_p, "rb").read()
print("bytes =", len(b), "| sha256 =", hashlib.sha256(b).hexdigest())
sup = json.loads(b.decode("utf-8"))
print("top keys:", list(sup.keys()))
for k, v in sup.items():
    if isinstance(v, (int, float, str, bool)):
        print("   %-40s = %s" % (k, v))
    elif isinstance(v, list):
        print("   %-40s list[%d] %s" % (k, len(v), json.dumps(v[0], ensure_ascii=False)[:250] if v else ""))
    elif isinstance(v, dict):
        print("   %-40s dict{%d} -> %s" % (k, len(v), list(v.keys())[:12]))
