import json

with open("training_runs/positioning_v2_real_temporal/full_index_distribution.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Keys in full_index_distribution.json:", data.keys())
zero_supports = []
for split_name, heads in data.get("by_split", {}).items():
    for head_name, classes in heads.items():
        for cls_name, vals in classes.items():
            sup = vals.get("support")
            pct = vals.get("percentage")
            if sup == 0 or vals == "N/A" or pct == "N/A":
                zero_supports.append((split_name, head_name, cls_name, vals))

print("Zero supports found:", zero_supports)
