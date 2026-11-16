import json, os, sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")

def load(f):
    return json.loads(open(os.path.join(STUDY, f), "rb").read().decode("utf-8"))

def dump(obj, indent=0, maxs=400):
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                print("%s%s:" % (pad, k))
                dump(v, indent + 1, maxs)
            else:
                s = str(v)
                if len(s) > maxs:
                    s = s[:maxs] + "...[TRUNC]"
                print("%s%s = %s" % (pad, k, s))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                print("%s[%d]:" % (pad, i))
                dump(v, indent + 1, maxs)
            else:
                s = str(v)
                if len(s) > maxs:
                    s = s[:maxs] + "...[TRUNC]"
                print("%s[%d] = %s" % (pad, i, s))
    else:
        print(pad + str(obj))

f = sys.argv[1]
d = load(f)
d2 = sys.argv[2] if len(sys.argv) > 2 else None
if d2:
    for path in d2.split(","):
        cur = d
        for part in path.split("."):
            cur = cur[part]
        print("### " + path)
        dump(cur, 1)
        print()
else:
    dump(d)
