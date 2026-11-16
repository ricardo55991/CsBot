import subprocess
import time
import os
import ctypes
from ctypes import wintypes
from PIL import Image, ImageGrab

user32 = ctypes.windll.user32

cs2_exe = r"H:\CS2_AI_Server\game\bin\win64\cs2.exe"
cfg_dir = r"H:\CS2_AI_Server\game\csgo\cfg"

# Escrever cfg de teste
test_cfg = os.path.join(cfg_dir, "test_render.cfg")
with open(test_cfg, "w", encoding="utf-8") as f:
    f.write("""sv_cheats 1
bot_kick
mp_warmup_end 1
mp_freezetime 0
mp_roundtime_defuse 60
jointeam 3
setpos -1011.5 -2479.9 -168.0
setang 0.0 60.0 0.0
""")

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "+sv_lan", "1",
    "+map", "de_mirage",
    "+exec", "test_render.cfg"
]

print("[*] Launching CS2 for render test...")
proc = subprocess.Popen(args, cwd=r"H:\CS2_AI_Server")

def find_cs2_hwnd():
    hwnd = user32.FindWindowW(None, "Counter-Strike 2")
    if not hwnd:
        hwnd = user32.FindWindowW("SDL_app", None)
    return hwnd

try:
    print("[*] Waiting 25 seconds for CS2 to load map and spawn...")
    time.sleep(25)
    
    hwnd = find_cs2_hwnd()
    print(f"[*] HWND: {hwnd}")
    if hwnd:
        user32.SetForegroundWindow(hwnd)
        time.sleep(2)
        
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        print(f"[*] Window bounds: ({rect.left}, {rect.top}, {rect.right}, {rect.bottom})")
        
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        shot = ImageGrab.grab(bbox)
        out_path = r"docs\fase_1_7\screenshots\test_render_grab.png"
        shot.save(out_path)
        print(f"[+] Saved {out_path}, size: {shot.size}, extrema: {shot.getextrema()}")
    else:
        print("[-] CS2 window not found!")
finally:
    print("[*] Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[*] Finished.")
