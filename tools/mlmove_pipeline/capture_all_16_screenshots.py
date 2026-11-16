import subprocess
import time
import os
import glob
from PIL import Image
from datetime import datetime
import json

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
cfg_dir = os.path.join(server_dir, r"game\csgo\cfg")
out_dir = r"docs\fase_1_7\screenshots"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(screenshots_dir, exist_ok=True)

# 8 spots com comandos em primeira pessoa e visão externa
spots_to_capture = [
    {
        "num": "01",
        "id": "ct_a_ticket_passive",
        "fp_pos": "-1011.5 -2479.9 -168.0",
        "fp_ang": "0.0 60.0 0.0",
        "ext_pos": "-1150.0 -2350.0 -80.0",
        "ext_ang": "25.0 -45.0 0.0"
    },
    {
        "num": "02",
        "id": "ct_a_firebox_oneanddone",
        "fp_pos": "-284.2 -2399.9 -164.0",
        "fp_ang": "0.0 110.0 0.0",
        "ext_pos": "-450.0 -2250.0 -60.0",
        "ext_ang": "30.0 -40.0 0.0"
    },
    {
        "num": "03",
        "id": "ct_a_ninja_hide",
        "fp_pos": "-439.8 -2337.7 -168.0",
        "fp_ang": "0.0 120.0 0.0",
        "ext_pos": "-600.0 -2200.0 -60.0",
        "ext_ang": "35.0 -45.0 0.0"
    },
    {
        "num": "04",
        "id": "ct_mid_window_crouch",
        "fp_pos": "-1139.4 -462.3 -168.0",
        "fp_ang": "-5.0 -20.0 0.0",
        "ext_pos": "-900.0 -400.0 -100.0",
        "ext_ang": "20.0 -170.0 0.0"
    },
    {
        "num": "05",
        "id": "ct_b_van_peek",
        "fp_pos": "-2191.6 712.6 -101.8",
        "fp_ang": "0.0 -85.0 0.0",
        "ext_pos": "-2000.0 550.0 0.0",
        "ext_ang": "25.0 140.0 0.0"
    },
    {
        "num": "06",
        "id": "tr_staging_a_ramp",
        "fp_pos": "321.1 -1708.1 -176.0",
        "fp_ang": "0.0 -135.0 0.0",
        "ext_pos": "180.0 -1850.0 -90.0",
        "ext_ang": "25.0 45.0 0.0"
    },
    {
        "num": "07",
        "id": "tr_staging_palace_room",
        "fp_pos": "288.1 -2373.4 -40.0",
        "fp_ang": "0.0 -140.0 0.0",
        "ext_pos": "450.0 -2250.0 20.0",
        "ext_ang": "20.0 -150.0 0.0"
    },
    {
        "num": "08",
        "id": "ct_retake_a_connector",
        "fp_pos": "-802.4 -1221.3 -168.0",
        "fp_ang": "0.0 0.0 0.0",
        "ext_pos": "-650.0 -1350.0 -80.0",
        "ext_ang": "25.0 135.0 0.0"
    }
]

def clean_screenshots_folder():
    for f in glob.glob(os.path.join(screenshots_dir, "*.*")):
        try:
            os.remove(f)
        except Exception:
            pass

manifest = []

def capture_single_shot(cfg_name, pos_cmd, ang_cmd, target_png_path, shot_type, spot_id):
    if os.path.exists(target_png_path) and os.path.getsize(target_png_path) > 50000:
        print(f"[*] Already exists: {os.path.basename(target_png_path)} ({os.path.getsize(target_png_path)} bytes)")
        manifest.append({
            "SpotId": spot_id,
            "Type": shot_type,
            "Path": target_png_path,
            "Position": pos_cmd,
            "Angles": ang_cmd,
            "Timestamp": datetime.utcnow().isoformat(),
            "Status": "CAPTURED_REAL_CS2"
        })
        return True

    cfg_path = os.path.join(cfg_dir, cfg_name)
    cfg_content = f"""sv_cheats 1
bot_kick
mp_warmup_end 1
mp_freezetime 0
mp_roundtime_defuse 60
setpos {pos_cmd}
setang {ang_cmd}
screenshot
echo "=== CAPTURE EXECUTED ==="
"""
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(cfg_content)

    clean_screenshots_folder()

    args = [
        cs2_exe,
        "-windowed",
        "-w", "1280",
        "-h", "720",
        "-novid",
        "-insecure",
        "+sv_lan", "1",
        "+map", "de_mirage",
        "+exec", cfg_name
    ]

    print(f"[*] [{datetime.now().strftime('%H:%M:%S')}] Launching CS2 for {os.path.basename(target_png_path)}...")
    try:
        proc = subprocess.Popen(args, cwd=server_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(22)
    finally:
        subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(2)
    tga_files = glob.glob(os.path.join(screenshots_dir, "*.tga"))
    if not tga_files:
        tga_files = glob.glob(os.path.join(screenshots_dir, "*.jpg")) + glob.glob(os.path.join(screenshots_dir, "*.png"))

    if tga_files:
        latest_file = max(tga_files, key=os.path.getmtime)
        img = Image.open(latest_file)
        img.save(target_png_path)
        print(f"[+] [{datetime.now().strftime('%H:%M:%S')}] SUCCESS: Saved {target_png_path} ({img.size}, {os.path.getsize(target_png_path)} bytes)")
        manifest.append({
            "SpotId": spot_id,
            "Type": shot_type,
            "Path": target_png_path,
            "Position": pos_cmd,
            "Angles": ang_cmd,
            "Timestamp": datetime.utcnow().isoformat(),
            "Status": "CAPTURED_REAL_CS2"
        })
        return True
    else:
        print(f"[-] [{datetime.now().strftime('%H:%M:%S')}] FAILED: No screenshot found for {target_png_path}")
        return False

print("==================================================")
print("CS2 REAL 3D ENGINE CAPTURE PIPELINE (16 SHOTS)")
print("==================================================")

total_success = 0
for sp in spots_to_capture:
    num = sp["num"]
    sid = sp["id"]
    
    # 1. First-person
    fp_png = os.path.join(out_dir, f"{num}_{sid}_first_person.png")
    cfg_fp = f"auto_{num}_fp.cfg"
    ok1 = capture_single_shot(cfg_fp, sp["fp_pos"], sp["fp_ang"], fp_png, "first_person", sid)
    if ok1: total_success += 1
    
    # 2. External
    ext_png = os.path.join(out_dir, f"{num}_{sid}_external.png")
    cfg_ext = f"auto_{num}_ext.cfg"
    ok2 = capture_single_shot(cfg_ext, sp["ext_pos"], sp["ext_ang"], ext_png, "external", sid)
    if ok2: total_success += 1

with open("docs/fase_1_7/screenshots/capture_manifest.json", "w", encoding="utf-8") as f:
    json.dump({"total_captured": total_success, "manifest": manifest}, f, indent=2)

print(f"\n[DONE] Pipeline finished: {total_success}/16 successful real engine captures.")
