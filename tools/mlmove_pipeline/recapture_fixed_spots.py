import subprocess
import time
import os
import glob
import shutil
from PIL import Image
import sys

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("tools/mlmove_pipeline"))

from cs2_vconsole_bridge import send_tcp, build_cmnd_packet, DEFAULT_HANDSHAKE_HEX

server_dir = "H:/CS2_AI_Server"
cs2_exe = "H:/CS2_AI_Server/game/bin/win64/cs2.exe"
screenshots_dir = "H:/CS2_AI_Server/game/csgo/screenshots"
out_dir = os.path.join(os.path.abspath("."), "docs", "fase_1_7", "screenshots")

# Limpar screenshots anteriores do CS2
for pat in ["*.jpg", "*.png", "*.tga"]:
    for f in glob.glob(os.path.join(screenshots_dir, pat)):
        try: os.remove(f)
        except: pass

# Spots to recapture
targets = [
    {
        "num": 7,
        "id": "b_site_default_plant_box",
        "coords": [-1980.0, 300.0, -160.0],
        "pitch": 4.0,
        "yaw": 115.0
    },
    {
        "num": 31,
        "id": "a_palace_deep_room",
        "coords": [350.0, -2050.0, -104.0],
        "pitch": 0.0,
        "yaw": 152.0
    },
    {
        "num": 47,
        "id": "a_tetris_top_control",
        "coords": [-180.0, -1620.0, -60.0],
        "pitch": 0.0,
        "yaw": 145.0
    },
    {
        "num": 48,
        "id": "a_tetris_corner_ramp_palace",
        "coords": [-360.0, -1570.0, -168.0],
        "pitch": 2.0,
        "yaw": -20.0
    },
    {
        "num": 49,
        "id": "a_default_plant_headshot",
        "coords": [-460.0, -2180.0, -168.0],
        "pitch": 2.0,
        "yaw": 55.0
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

print("[*] Iniciando CS2...")
proc = subprocess.Popen(args, cwd=server_dir)

try:
    print("[*] Aguardando 25s carregamento do mapa...")
    time.sleep(25)
    handshake = bytes.fromhex(DEFAULT_HANDSHAKE_HEX)
    
    init_cmds = [
        "sv_cheats 1",
        "god 1",
        "buddha 1",
        "sv_falldamage_scale 0",
        "sv_regeneration_force_on 1",
        "bot_kick",
        "mp_warmup_end 1",
        "mp_freezetime 0",
        "mp_roundtime_defuse 60",
        "jointeam 3 0"
    ]
    print("[*] Enviando init commands...")
    send_tcp(build_cmnd_packet("; ".join(init_cmds)), "127.0.0.1", 29000, handshake, 0.2, 0.5)
    
    print("[*] Aguardando 10s para spawn completo...")
    time.sleep(10)
    
    view_cmds = [
        "give weapon_m4a1_silencer",
        "slot1",
        "cl_draw_only_deathnotices 1",
        "crosshair 1"
    ]
    send_tcp(build_cmnd_packet("; ".join(view_cmds)), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(1.0)
    
    for t in targets:
        num = t["num"]
        sid = t["id"]
        x, y, z = t["coords"]
        yaw = t["yaw"]
        pitch = t["pitch"]
        shot_tag = f"spot_{num:02d}_{sid}"
        
        print(f"[*] Capturando Spot #{num:02d} ({sid}) em [{x}, {y}, {z}] Yaw {yaw}...")
        tp_cmd = f"setpos {x:.1f} {y:.1f} {z:.1f}; setang {pitch:.1f} {yaw:.1f} 0.0"
        send_tcp(build_cmnd_packet(tp_cmd), "127.0.0.1", 29000, handshake, 0.1, 0.4)
        time.sleep(0.4)
        
        shot_cmd = f"jpeg_screenshot {shot_tag} 95"
        send_tcp(build_cmnd_packet(shot_cmd), "127.0.0.1", 29000, handshake, 0.1, 0.4)
        time.sleep(0.4)
        
    print("[*] Aguardando 5s para gravacao em disco...")
    time.sleep(5)
    
except Exception as e:
    print(f"[-] Erro: {e}")
    
finally:
    print("[*] Encerrando CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("[*] Verificando e copiando screenshots...")
for t in targets:
    num = t["num"]
    sid = t["id"]
    shot_tag = f"spot_{num:02d}_{sid}"
    matches = glob.glob(os.path.join(screenshots_dir, f"{shot_tag}*.jpg"))
    if matches:
        dest = os.path.join(out_dir, f"{shot_tag}.jpg")
        matches.sort(key=os.path.getmtime, reverse=True)
        shutil.copyfile(matches[0], dest)
        img = Image.open(dest)
        print(f"[+] Spot #{num:02d} ATUALIZADO: {dest} (extrema {img.getextrema()})")
    else:
        print(f"[-] Spot #{num:02d} nao encontrado em {screenshots_dir}")
