import sys
sys.path.insert(0, 'tools/mlmove_pipeline')
from build_complete_automated_spots_catalog import SPOTS_CATALOG

with open('docs/spot_recording/spot_inventory.txt', 'w', encoding='utf-8') as f:
    for s in SPOTS_CATALOG:
        f.write(f"#{s['num']:02d} | id={s['id']} | side={s['side']} | sector={s['sector']} | group={s['group']} | name={s['name']}\n")

print("Saved spot inventory to docs/spot_recording/spot_inventory.txt")
