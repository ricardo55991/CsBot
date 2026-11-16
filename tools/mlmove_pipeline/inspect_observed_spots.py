import json

with open("docs/fase_1_6/profile_v2_observed_spots.json", "r", encoding="utf-8") as f:
    obs = json.load(f)

bd = obs.get("SpotBreakdown", {})
classifications = {}
for k, v in bd.items():
    c = v.get("Classification")
    classifications[c] = classifications.get(c, 0) + 1

print("Classifications in SpotBreakdown:", classifications)
