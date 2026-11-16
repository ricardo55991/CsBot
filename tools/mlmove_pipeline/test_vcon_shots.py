import subprocess
import time
import socket
import os
import glob
from PIL import Image
import sys
import os
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("tools/mlmove_pipeline"))
from cs2_vconsole_bridge import send_tcp, build_cmnd_packet, DEFAULT_HANDSHAKE_HEX

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

# Limpa screenshots anteriores
for pat in ["*.jpg", "*.png", "*.tga"]:
    for f in glob.glob(os.path.join(screenshots_dir, pat)):
        try: os.remove(f)
        except: pass
    for f in glob.glob(os.path.join(server_dir, r"game\csgo", pat)):
        try: os.remove(f)
        except: pass

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
    print("[*] Waiting 22s for de_mirage to load...")
    time.sleep(22)
    
    handshake = bytes.fromhex(DEFAULT_HANDSHAKE_HEX)
    
    # 1. Spawn player as CT
    print("[*] Sending jointeam 3 and game setup...")
    cmd1 = "sv_cheats 1; bot_kick; mp_warmup_end 1; mp_freezetime 0; mp_roundtime_defuse 60; jointeam 3"
    send_tcp(build_cmnd_packet(cmd1), "127.0.0.1", 29000, handshake, 0.2, 0.5)
    
    # Espera 5 segundos para o jogador spawnar vivo na base CT
    print("[*] Waiting 5s for player spawn...")
    time.sleep(5)
    
    # 2. Teleporta para Spot #01 e tira screenshot
    print("[*] Teleporting to Spot #01 and capturing...")
    cmd2 = "setpos -1530.0 280.0 -160.0; setang 4.0 125.0 0.0"
    send_tcp(build_cmnd_packet(cmd2), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(0.5)
    
    cmd3 = "jpeg_screenshot test_vcon_spot01 95"
    send_tcp(build_cmnd_packet(cmd3), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(0.5)
    
    cmd4 = "screenshot"
    send_tcp(build_cmnd_packet(cmd4), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(2)
    
    # 3. Teleporta para Spot #53 (Areia embaixo do Palácio)
    print("[*] Teleporting to Spot #53 (Areia embaixo do Palácio) and capturing...")
    cmd5 = "setpos -42.0 -1928.0 -168.0; setang 1.0 90.0 0.0"
    send_tcp(build_cmnd_packet(cmd5), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(0.5)
    
    cmd6 = "jpeg_screenshot test_vcon_spot53 95"
    send_tcp(build_cmnd_packet(cmd6), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(2)
    
    print("\n[*] Searching for generated screenshot files...")
    start_time = time.time() - 60
    found_any = False
    for root, dirs, files in os.walk(os.path.join(server_dir, "game")):
        for file in files:
            if file.endswith((".jpg", ".png", ".tga")) and "test_vcon" in file or file.startswith("screenshot"):
                full_p = os.path.join(root, file)
                if os.path.getmtime(full_p) >= start_time:
                    found_any = True
                    print(f"\n[+] SUCCESS! Found screenshot: {full_p} ({os.path.getsize(full_p)} bytes)")
                    try:
                        img = Image.open(full_p)
                        print(f"    Dimensions: {img.size}")
                        extrema = img.getextrema()
                        print(f"    Pixel Extrema: {extrema}")
                        # Verifica se não é preto
                        is_black = (isinstance(extrema[0], tuple) and extrema[0][1] == 0) or extrema[0] == 0
                        if is_black and ((isinstance(extrema[1], tuple) and extrema[1][1] == 0) or extrema[1] == 0):
                            print("    [!] WARNING: Image appears to be completely black.")
                        else:
                            print("    [***] VALID REAL 3D IN-GAME SCREENSHOT! NOT BLACK! [***]")
                    except Exception as e:
                        print(f"    Error reading image: {e}")
                        
    if not found_any:
        print("[-] No screenshots found yet. Checking screenshots_dir...")
        all_shots = glob.glob(os.path.join(screenshots_dir, "*.*"))
        print(f"Total files in screenshots_dir: {len(all_shots)}")
        for s in all_shots:
            print("  ->", s)

finally:
    print("\n[*] Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[*] Done.")
