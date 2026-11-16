import json

with open("src/CsBotManager/MapProfiles/de_mirage.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Keys in de_mirage.json:", list(data.keys()))
if "chokepoints" in data:
    print("Chokepoints:", json.dumps(data["chokepoints"], indent=2))
elif "Chokepoints" in data:
    print("Chokepoints:", json.dumps(data["Chokepoints"], indent=2))
else:
    for k, v in data.items():
        if "choke" in k.lower():
            print(f"Found {k}:", v)
