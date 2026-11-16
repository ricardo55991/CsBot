import json

with open('src/CsBotManager/MapProfiles/de_mirage.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

targets = [
    'ct_b_bench_deep', 'ct_b_market_window', 'ct_b_market_door', 
    'ct_mid_short_catwalk', 'ct_b_short_corner', 'ct_mid_connector_headshot', 
    'ct_a_stairs_cross', 'ct_a_palace_close_poke', 'ct_mid_window_deep_awp'
]

print("=== SPOTS JÁ EXISTENTES NO PERFIL CITADOS PELO USUÁRIO ===")
for s in d['spots']:
    if s['id'] in targets:
        print(f"{s['id']:28} | {s['name']:28} | pos=({s['x']:.1f}, {s['y']:.1f}, {s['z']:.1f}) | yaw={s['yaw']:.1f} | {s.get('description','')}")
