import json

with open("src/CsBotManager/MapProfiles/de_mirage.json", "r", encoding="utf-8") as f:
    de_mirage = json.load(f)

print("First spot in de_mirage.json:")
print(json.dumps(de_mirage["spots"][0], indent=2))
print("\nSpot properties across all 45 spots:")
keys = set()
for s in de_mirage["spots"]:
    keys.update(s.keys())
print(sorted(list(keys)))
