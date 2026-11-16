import subprocess
import time
import os
import glob
import ctypes

user32 = ctypes.windll.user32

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
cfg_dir = os.path.join(server_dir, r"game\csgo\cfg")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

# Limpar screenshots anteriores
for f in glob.glob(os.path.join(screenshots_dir, "*.*")):
    try: os.remove(f)
    except: pass

# Escrever cfg acionada pelo F8
capture_cfg_path = os.path.join(cfg_dir, "test_f8_capture.cfg")
with open(capture_cfg_path, "w", encoding="utf-8") as f:
    f.write("""sv_cheats 1
bot_kick
mp_warmup_end 1
mp_freezetime 0
jointeam 3
setpos -1011.5 -2479.9 -168.0
setang 0.0 60.0 0.0
jpeg_screenshot
screenshot
echo "=== F8 SPOT CAPTURED ==="
""")

# Configurar autoexec para bindar F8
autoexec_path = os.path.join(cfg_dir, "autoexec.cfg")
with open(autoexec_path, "w", encoding="utf-8") as f:
    f.write("""bind F8 "exec test_f8_capture.cfg"
""")

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "+sv_lan", "1",
    "+map", "de_mirage"
]

print("[*] Launching CS2...")
proc = subprocess.Popen(args, cwd=server_dir)

def find_cs2_hwnd():
    hwnd = user32.FindWindowW(None, "Counter-Strike 2")
    if not hwnd:
        hwnd = user32.FindWindowW("SDL_app", None)
    return hwnd

try:
    print("[*] Waiting 25 seconds for map to load...")
    time.sleep(25)
    
    hwnd = find_cs2_hwnd()
    print(f"[*] HWND: {hwnd}")
    if hwnd:
        user32.SetForegroundWindow(hwnd)
        time.sleep(1)
        
        # Enviar F8 (VK_F8 = 0x77)
        print("[*] Sending F8 keypress to CS2...")
        user32.keybd_event(0x77, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(0x77, 0, 2, 0) # KEYEVENTF_KEYUP
        
        time.sleep(3)
        
        # Segunda tentativa para garantir (caso estivesse no menu de times)
        user32.keybd_event(0x77, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(0x77, 0, 2, 0)
        time.sleep(2)
        
    shots = glob.glob(os.path.join(screenshots_dir, "*.*"))
    print(f"[*] Screenshots found in screenshots_dir: {len(shots)}")
    for s in shots:
        print(f"  -> {s} ({os.path.getsize(s)} bytes)")
finally:
    print("[*] Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[*] Finished.")
