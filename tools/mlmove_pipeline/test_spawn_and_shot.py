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

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "-vconsole",
    "+sv_lan", "1",
    "+mp_force_pick_time", "0",
    "+map", "de_mirage"
]

print("[*] Launching CS2...")
proc = subprocess.Popen(args, cwd=server_dir)

try:
    print("[*] Waiting 24s for de_mirage to load...")
    time.sleep(24)
    
    handshake = bytes.fromhex(DEFAULT_HANDSHAKE_HEX)
    
    print("[*] Setting up server rules and joining CT...")
    cmd1 = "sv_cheats 1; bot_kick; mp_warmup_end 1; mp_freezetime 0; mp_roundtime_defuse 60; mp_force_pick_time 0; jointeam 3 0"
    send_tcp(build_cmnd_packet(cmd1), "127.0.0.1", 29000, handshake, 0.2, 0.5)
    
    # Espera 10 segundos para o timer da tela de times expirar e spawnar o jogador!
    print("[*] Waiting 10s for team selection timer to expire and player to spawn...")
    time.sleep(10)
    
    # Envia comando para fechar menu e forçar spawn
    cmd_spawn = "slot1; mp_restartgame 1"
    send_tcp(build_cmnd_packet(cmd_spawn), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(3)
    
    # Teleporta para Spot #53 (Areia embaixo do Palácio)
    print("[*] Teleporting to Spot #53 (Areia embaixo do Palácio) at [-42.0, -1928.0, -168.0], Yaw +90.0...")
    cmd_tp = "sv_cheats 1; setpos -42.0 -1928.0 -168.0; setang 1.0 90.0 0.0"
    send_tcp(build_cmnd_packet(cmd_tp), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(1)
    
    # Tira screenshot
    print("[*] Taking screenshot of Spot #53...")
    cmd_shot = "jpeg_screenshot spot53_areia_test 95"
    send_tcp(build_cmnd_packet(cmd_shot), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(2)
    
    # Teleporta para Spot #01 (Pilar B)
    print("[*] Teleporting to Spot #01 at [-1530.0, 280.0, -160.0], Yaw +125.0...")
    cmd_tp1 = "sv_cheats 1; setpos -1530.0 280.0 -160.0; setang 4.0 125.0 0.0"
    send_tcp(build_cmnd_packet(cmd_tp1), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(1)
    
    print("[*] Taking screenshot of Spot #01...")
    cmd_shot1 = "jpeg_screenshot spot01_b_pillar_test 95"
    send_tcp(build_cmnd_packet(cmd_shot1), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(2)

finally:
    print("[*] Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[*] Done.")
