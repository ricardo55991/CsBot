import json
import os
import math

# Leitura dos dados gravados ao vivo pelo usuario
LIVE_JSON = "docs/spot_recording/recorded_spots_live.json"
with open(LIVE_JSON, "r", encoding="utf-8") as f:
    live_records = json.load(f)

# Pega o registro mais recente para cada spot_number
user_recordings = {}
for entry in live_records:
    snum = entry.get("spot_number")
    user_recordings[snum] = entry

from build_rich_tactical_database import TACTICAL_DB

FULL_SPOTS_CATALOG = []

for num in range(1, 54):
    meta = TACTICAL_DB[num]
    if num in user_recordings:
        rec = user_recordings[num]
        coords = [round(float(x), 1) for x in rec["coords"]]
        yaw = round(float(rec["aim"]["yaw"]), 1)
        pitch = round(float(rec["aim"]["pitch"]), 1)
        stance = rec["stance"]
    else:
        # Spot 50: Homologado Staging TR
        coords = [320.0, -1590.0, -168.0]
        yaw = -155.0
        pitch = 0.0
        stance = "Em pé"
        
    recommended_stance = "PASSIVE_HOLD" if stance == "Agachado" else "AGGRESSIVE_POKE"
    
    spot_entry = {
        "num": num,
        "id": meta["id"],
        "name": meta["name"],
        "side": meta["side"],
        "sector": meta["sector"],
        "group": meta["group"],
        "coords": coords,
        "stance": stance,
        "recommended_stance": recommended_stance,
        "cover": meta["cover"],
        "primary_aim": {
            "name": meta["primary_aim_name"],
            "target": meta["primary_aim_target"],
            "yaw": yaw,
            "pitch": pitch,
            "desc": meta["primary_aim_desc"]
        },
        "secondary_aims": meta["secondary_aims"],
        "support_aim": meta["support_aim"],
        "fallback_route": meta["fallback_route"],
        "danger": meta["danger"],
        "objective": meta["objective"]
    }
    FULL_SPOTS_CATALOG.append(spot_entry)

print(f"Catalogo completo compilado: {len(FULL_SPOTS_CATALOG)} spots.")
out_json = "docs/spot_recording/mirage_spots_enriched_live_v3.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(FULL_SPOTS_CATALOG, f, indent=2, ensure_ascii=False)
print(f"Salvo em {out_json}")
