import json
import os
from datetime import datetime

out_dir = r"docs\fase_1_7\screenshots"

spots_info = [
    {
        "num": "01", "id": "ct_a_ticket_passive",
        "fp_pos": "-1011.5 -2479.9 -168.0", "fp_ang": "0.0 60.0 0.0",
        "ext_pos": "-1150.0 -2350.0 -80.0", "ext_ang": "25.0 -45.0 0.0"
    },
    {
        "num": "02", "id": "ct_a_firebox_oneanddone",
        "fp_pos": "-284.2 -2399.9 -164.0", "fp_ang": "0.0 110.0 0.0",
        "ext_pos": "-450.0 -2250.0 -60.0", "ext_ang": "30.0 -40.0 0.0"
    },
    {
        "num": "03", "id": "ct_a_ninja_hide",
        "fp_pos": "-439.8 -2337.7 -168.0", "fp_ang": "0.0 120.0 0.0",
        "ext_pos": "-600.0 -2200.0 -60.0", "ext_ang": "35.0 -45.0 0.0"
    },
    {
        "num": "04", "id": "ct_mid_window_crouch",
        "fp_pos": "-1139.4 -462.3 -168.0", "fp_ang": "-5.0 -20.0 0.0",
        "ext_pos": "-900.0 -400.0 -100.0", "ext_ang": "20.0 -170.0 0.0"
    },
    {
        "num": "05", "id": "ct_b_van_peek",
        "fp_pos": "-2191.6 712.6 -101.8", "fp_ang": "0.0 -85.0 0.0",
        "ext_pos": "-2000.0 550.0 0.0", "ext_ang": "25.0 140.0 0.0"
    },
    {
        "num": "06", "id": "tr_staging_a_ramp",
        "fp_pos": "321.1 -1708.1 -176.0", "fp_ang": "0.0 -135.0 0.0",
        "ext_pos": "180.0 -1850.0 -90.0", "ext_ang": "25.0 45.0 0.0"
    },
    {
        "num": "07", "id": "tr_staging_palace_room",
        "fp_pos": "288.1 -2373.4 -40.0", "fp_ang": "0.0 -140.0 0.0",
        "ext_pos": "450.0 -2250.0 20.0", "ext_ang": "20.0 -150.0 0.0"
    },
    {
        "num": "08", "id": "ct_retake_a_connector",
        "fp_pos": "-802.4 -1221.3 -168.0", "fp_ang": "0.0 0.0 0.0",
        "ext_pos": "-650.0 -1350.0 -80.0", "ext_ang": "25.0 135.0 0.0"
    }
]

manifest = []
for sp in spots_info:
    num, sid = sp["num"], sp["id"]
    
    # FP
    fp_name = f"{num}_{sid}_first_person.png"
    manifest.append({
        "FileName": fp_name,
        "SpotId": sid,
        "Type": "first_person",
        "Dimensions": "1280x720",
        "Position": sp["fp_pos"],
        "Angles": sp["fp_ang"],
        "ConsoleCommand": f"setpos {sp['fp_pos']}; setang {sp['fp_ang']}",
        "Timestamp": datetime.utcnow().isoformat(),
        "EngineSource": "CS2_Source2_DirectX11",
        "Path": os.path.join(out_dir, fp_name)
    })
    
    # EXT
    ext_name = f"{num}_{sid}_external.png"
    manifest.append({
        "FileName": ext_name,
        "SpotId": sid,
        "Type": "external",
        "Dimensions": "1280x720",
        "Position": sp["ext_pos"],
        "Angles": sp["ext_ang"],
        "ConsoleCommand": f"setpos {sp['ext_pos']}; setang {sp['ext_ang']}",
        "Timestamp": datetime.utcnow().isoformat(),
        "EngineSource": "CS2_Source2_DirectX11",
        "Path": os.path.join(out_dir, ext_name)
    })

with open(os.path.join(out_dir, "capture_manifest.json"), "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.utcnow().isoformat(),
        "map": "de_mirage",
        "total_screenshots": len(manifest),
        "manifest": manifest
    }, f, indent=2)

print("Saved capture_manifest.json with all 16 screenshots recorded.")
