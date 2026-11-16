import json

with open("src/CsBotManager/MapProfiles/de_mirage.json", "r", encoding="utf-8") as f:
    de_mirage = json.load(f)

with open("docs/fase_1_5/mirage_spot_audit.json", "r", encoding="utf-8") as f:
    audit = json.load(f)["audit"]
audit_map = {x["SpotId"]: x for x in audit}

with open("docs/fase_1_6/profile_v2_observed_spots.json", "r", encoding="utf-8") as f:
    obs = json.load(f)["SpotBreakdown"]

print(f"Total spots in de_mirage: {len(de_mirage['spots'])}")

for s in de_mirage["spots"]:
    sid = s["id"]
    a = audit_map.get(sid, {})
    o = obs.get(sid, {})
    print(f"ID: {sid:30} | Side: {s.get('side')} | Sector: {s.get('sector'):15} | Bombsite: {s.get('associated_bombsite')} | Usage: {s.get('usage')} | AuditClass: {a.get('CurrentClassification')} | Gameplay: {o.get('Classification')}")
