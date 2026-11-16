import subprocess
import time
import socket
import os
import glob
from PIL import Image
import sys
sys.path.insert(0, os.path.abspath("tools/mlmove_pipeline"))
from cs2_vconsole_bridge import send_tcp, build_cmnd_packet, DEFAULT_HANDSHAKE_HEX

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

# Limpar screenshots
for pat in ["*.jpg", "*.png", "*.tga"]:
    for f in glob.glob(os.path.join(screenshots_dir, pat)):
        try: os.remove(f)
        except: pass

test_spots = [
    {
        "num": 1,
        "id": "b_short_pillar_hold_apps",
        "pos": "-1530.0 280.0 -160.0",
        "ang": "4.0 125.0 0.0"
    },
    {
        "num": 6,
        "id": "b_van_behind_apps_hold",
        "pos": "-2165.0 685.0 -42.0",
        "ang": "1.0 5.0 0.0"
    },
    {
        "num": 48,
        "id": "a_tetris_corner_ramp_palace",
        "pos": "-360.0 -1570.0 -168.0",
        "ang": "2.0 -20.0 0.0"
    },
    {
        "num": 53,
        "id": "ct_a_sand_pit_under_palace_hold_caverna",
        "pos": "-42.0 -1928.0 -168.0",
        "ang": "1.0 90.0 0.0"
    }
]

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "-vconsole",
    "+sv_lan", "1",
    "+map", "de_mirage"
]

print("[*] Launching CS2...")
proc = subprocess.Popen(args, cwd=server_dir)

try:
    print("[*] Waiting 24s for de_mirage to load...")
    time.sleep(24)
    
    handshake = bytes.fromhex(DEFAULT_HANDSHAKE_HEX)
    
    print("[*] Initializing match, cheats, joining CT and equipping rifle...")
    setup_cmds = [
        "sv_cheats 1",
        "bot_kick",
        "mp_warmup_end 1",
        "mp_freezetime 0",
        "mp_roundtime_defuse 60",
        "jointeam 3 0"
    ]
    send_tcp(build_cmnd_packet("; ".join(setup_cmds)), "127.0.0.1", 29000, handshake, 0.2, 0.5)
    
    print("[*] Waiting 10s for spawn...")
    time.sleep(10)
    
    # Configura visual limpo com mira e arma
    view_cmds = [
        "give weapon_m4a1_silencer",
        "slot1",
        "cl_draw_only_deathnotices 1",
        "crosshair 1"
    ]
    send_tcp(build_cmnd_packet("; ".join(view_cmds)), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(1)
    
    for sp in test_spots:
        num = sp["num"]
        sid = sp["id"]
        pos = sp["pos"]
        ang = sp["ang"]
        shot_name = f"spot_{num:02d}_{sid}"
        print(f"[*] Capturing Spot #{num:02d} ({sid}) at {pos}, ang {ang}...")
        
        tp_cmd = f"setpos {pos}; setang {ang}"
        send_tcp(build_cmnd_packet(tp_cmd), "127.0.0.1", 29000, handshake, 0.1, 0.4)
        time.sleep(0.4)
        
        shot_cmd = f"jpeg_screenshot {shot_name} 95"
        send_tcp(build_cmnd_packet(shot_cmd), "127.0.0.1", 29000, handshake, 0.1, 0.4)
        time.sleep(0.8)

finally:
    print("[*] Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[*] Done.")
