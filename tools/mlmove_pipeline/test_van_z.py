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

# Limpar screenshots da van
for f in glob.glob(os.path.join(screenshots_dir, "*van_test*")):
    try: os.remove(f)
    except: pass

van_variants = [
    {"name": "van_z_plus20", "pos": "-2170.0 680.0 20.0", "ang": "1.0 12.0 0.0"},
    {"name": "van_z_plus05", "pos": "-2170.0 680.0 5.0", "ang": "1.0 12.0 0.0"},
    {"name": "van_z_minus15", "pos": "-2170.0 680.0 -15.0", "ang": "1.0 12.0 0.0"},
]

args = [
    cs2_exe,
    "-windowed", "-w", "1280", "-h", "720",
    "-novid", "-insecure", "-vconsole",
    "+sv_lan", "1", "+map", "de_mirage"
]

proc = subprocess.Popen(args, cwd=server_dir)

try:
    print("[*] Waiting 24s for CS2...")
    time.sleep(24)
    handshake = bytes.fromhex(DEFAULT_HANDSHAKE_HEX)
    send_tcp(build_cmnd_packet("sv_cheats 1; bot_kick; mp_warmup_end 1; mp_freezetime 0; jointeam 3 0"), "127.0.0.1", 29000, handshake, 0.2, 0.5)
    time.sleep(10)
    send_tcp(build_cmnd_packet("give weapon_m4a1_silencer; slot1; cl_draw_only_deathnotices 1; crosshair 1"), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(1)
    
    for v in van_variants:
        print(f"[*] Testing {v['name']} at {v['pos']}...")
        send_tcp(build_cmnd_packet(f"setpos {v['pos']}; setang {v['ang']}"), "127.0.0.1", 29000, handshake, 0.1, 0.4)
        time.sleep(0.5)
        send_tcp(build_cmnd_packet(f"jpeg_screenshot {v['name']} 95"), "127.0.0.1", 29000, handshake, 0.1, 0.4)
        time.sleep(0.8)

finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
