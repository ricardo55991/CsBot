import json

with open("docs/fase_1_5/mirage_spot_audit.json", "r", encoding="utf-8") as f:
    audit = json.load(f)

print("Type of audit:", type(audit))
if isinstance(audit, dict):
    print("Keys:", list(audit.keys()))
    for k in audit:
        print(f"Key {k} type:", type(audit[k]))
        if isinstance(audit[k], list):
            print(f"Key {k} len:", len(audit[k]))
            if len(audit[k]) > 0:
                print("First item in list:", audit[k][0])
        elif isinstance(audit[k], dict):
            print(f"Key {k} subkeys:", list(audit[k].keys())[:5])
