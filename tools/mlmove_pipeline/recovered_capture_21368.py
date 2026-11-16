import subprocess
import time
import socket
import os
import glob
import shutil
from PIL import Image
import sys

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("tools/mlmove_pipeline"))

from build_complete_automated_spots_catalog import SPOTS_CATALOG
from cs2_vconsole_bridge import send_tcp, build_cmnd_packet, DEFAULT_HANDSHAKE_HEX

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
out_dir = r"docs\fase_1_7\screenshots"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(screenshots_dir, exist_ok=True)

# Limpar screenshots anteriores do CS2
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
    "+map", "de_mirage"
]

print("================================================================================")
print(f"[*] INICIANDO CAPTURA AUTOMATIZADA DOS 53 SPOTS NO CS2 SOURCE 2")
print(f"[*] Total de spots a capturar: {len(SPOTS_CATALOG)}")
print("================================================================================")

proc = subprocess.Popen(args, cwd=server_dir)

try:
    print("[*] Aguardando 24s para carregamento do mapa de_mirage...")
    time.sleep(24)
    
    handshake = bytes.fromhex(DEFAULT_HANDSHAKE_HEX)
    
    print("[*] Conectando ao VConsole e inicializando partida com regras limpas...")
    init_cmds = [
        "sv_cheats 1",
        "bot_kick",
        "mp_warmup_end 1",
        "mp_freezetime 0",
        "mp_roundtime_defuse 60",
        "jointeam 3 0"
    ]
    send_tcp(build_cmnd_packet("; ".join(init_cmds)), "127.0.0.1", 29000, handshake, 0.2, 0.5)
    
    print("[*] Aguardando 10s para spawn completo do jogador na base CT...")
    time.sleep(10)
    
    print("[*] Configurando visão cinematográfica profissional (M4A1-S, sem HUD poluído, mira cravada)...")
    view_cmds = [
        "give weapon_m4a1_silencer",
        "slot1",
        "cl_draw_only_deathnotices 1",
        "crosshair 1"
    ]
    send_tcp(build_cmnd_packet("; ".join(view_cmds)), "127.0.0.1", 29000, handshake, 0.1, 0.5)
    time.sleep(1.0)
    
    print("\n[*] Disparando sequência de teleportes e capturas 3D in-game...")
    for idx, spot in enumerate(SPOTS_CATALOG, 1):
        num = spot["num"]
        sid = spot["id"]
        x, y, z = spot["coords"]
        yaw = spot["primary_aim"]["yaw"]
        pitch = spot["primary_aim"]["pitch"]
        shot_tag = f"spot_{num:02d}_{sid}"
        
        # Ajuste especial de Van se for spot 6
        if num == 6:
            x, y, z = -2100.0, 660.0, -20.0
            yaw, pitch = -5.0, 1.0
            
        print(f"  [{idx:02d}/53] Spot #{num:02d} ({sid}) -> Coords [{x:.1f}, {y:.1f}, {z:.1f}] | Yaw {yaw:+.1f}°, Pitch {pitch:+.1f}°")
        
        # Teleporte
        tp_cmd = f"setpos {x:.1f} {y:.1f} {z:.1f}; setang {pitch:.1f} {yaw:.1f} 0.0"
        send_tcp(build_cmnd_packet(tp_cmd), "127.0.0.1", 29000, handshake, 0.05, 0.25)
        time.sleep(0.25)
        
        # Disparo da captura
        shot_cmd = f"jpeg_screenshot {shot_tag} 95"
        send_tcp(build_cmnd_packet(shot_cmd), "127.0.0.1", 29000, handshake, 0.05, 0.35)
        time.sleep(0.35)
        
    print("\n[*] Todas as 53 capturas foram enviadas ao motor CS2! Aguardando 3s para gravação em disco...")
    time.sleep(3)

finally:
    print("[*] Encerrando processo CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[*] CS2 encerrado com sucesso.")

# Processamento e validação dos arquivos gerados
print("\n================================================================================")
print("[*] PROCESSANDO E COPIANDO SCREENSHOTS CAPTURADAS...")
print("================================================================================")

captured_manifest = {}
success_count = 0

for spot in SPOTS_CATALOG:
    num = spot["num"]
    sid = spot["id"]
    shot_tag = f"spot_{num:02d}_{sid}"
    
    # Procura arquivos correspondentes
    matches = glob.glob(os.path.join(screenshots_dir, f"{shot_tag}*.jpg"))
    target_dest = os.path.join(out_dir, f"spot_{num:02d}_{sid}.jpg")
    
    if matches:
        source_file = matches[0]
        shutil.copyfile(source_file, target_dest)
        fsize = os.path.getsize(target_dest)
        
        try:
            img = Image.open(target_dest)
            extrema = img.getextrema()
            is_valid = fsize > 50000 and extrema[0][1] > 30 # Garante que tem luz e não é preto
            
            if is_valid:
                success_count += 1
                status_str = "VALID_3D_REAL"
                print(f"  [+] Spot #{num:02d} OK: {os.path.basename(target_dest)} ({fsize:,} bytes, Extrema {extrema})")
            else:
                status_str = "INVALID_IMAGE"
                print(f"  [-] Spot #{num:02d} INVALID: {os.path.basename(target_dest)} (Tamanho {fsize}b, Extrema {extrema})")
        except Exception as e:
            status_str = f"ERROR: {e}"
            print(f"  [-] Spot #{num:02d} READ ERROR: {e}")
            
        captured_manifest[num] = {
            "spot_id": sid,
            "file": target_dest,
            "status": status_str,
            "size": fsize
        }
    else:
        print(f"  [-] Spot #{num:02d} MISSING: Nenhum arquivo encontrado para {shot_tag}")
        captured_manifest[num] = {
            "spot_id": sid,
            "status": "MISSING"
        }

print("\n================================================================================")
print(f"[RESULTADO FINAL] Capturados com sucesso: {success_count}/{len(SPOTS_CATALOG)} spots 3D!")
print("================================================================================")
