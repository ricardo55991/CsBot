import json
with open('docs/spot_recording/mirage_spots_enriched_live_v3.json', 'r', encoding='utf-8') as f:
    spots = json.load(f)

for s in spots:
    if s['num'] in [6, 28, 47, 48, 53]:
        print(f"Spot #{s['num']:02d} ({s['id']}): coords={s['coords']}, yaw={s['primary_aim']['yaw']}, stance={s['stance']}")
        print(f"   Primary: {s['primary_aim']['name']}")
        print(f"   Support: {s['support_aim']['partner_spot']} -> {s['support_aim']['target']}")
        print(f"   Fallback: {s['fallback_route']['destination']}")
