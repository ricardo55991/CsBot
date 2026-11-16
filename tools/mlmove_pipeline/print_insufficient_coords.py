import json

with open("src/CsBotManager/MapProfiles/de_mirage.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for s in d["spots"]:
    if s["id"] in ["tr_staging_top_mid_boxes", "tr_staging_t_roof", "tr_spawn_safe", "tr_exec_b_van_clear", "ct_retake_b_entry", "ct_retake_b_awp_cover"]:
        print(f"[\"{s['id']}\"] = ({s['x']}f, {s['y']}f, {s['z']}f),")
