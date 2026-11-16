import json

with open('src/CsBotManager/MapProfiles/de_mirage.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f"Total spots: {len(d['spots'])}\n")
for s in d['spots']:
    desc = s.get('description', '')
    print(f"{s['id']:32} | {s['name']:30} | ({s['x']:7.1f}, {s['y']:7.1f}, {s['z']:6.1f}) | yaw={s['yaw']:6.1f} | {desc}")
