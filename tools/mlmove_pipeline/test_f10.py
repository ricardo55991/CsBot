import subprocess
import time
import os
import glob
import ctypes
from ctypes import wintypes
from PIL import Image

user32 = ctypes.windll.user32
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_F10 = 0x79

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
cfg_dir = os.path.join(server_dir, r"game\csgo\cfg")

for f in glob.glob(os.path.join(screenshots_dir, "*.*")):
    try: os.remove(f)
    except: pass

# Cria CFG que faz bind do F10
cfg_path = os.path.join(cfg_dir, "test_bind_f10.cfg")
cfg_content = """sv_cheats 1
bot_kick
jointeam 3
bind F10 "screenshot"
setpos -1011.5 -2479.9 -168.0
setang 0.0 60.0 0.0
"""
with open(cfg_path, "w", encoding="utf-8") as f:
    f.write(cfg_content)

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "+sv_lan", "1",
    "+map", "de_mirage",
    "+exec", "test_bind_f10.cfg"
]

print("Launching CS2 for PostMessage F10 test...")
try:
    proc = subprocess.Popen(args, cwd=server_dir)
    print("Waiting 25s for map load...")
    time.sleep(25)
    
    hwnd = user32.FindWindowW(None, "Counter-Strike 2")
    if not hwnd:
        hwnd = user32.FindWindowW("SDL_app", None)
    print(f"HWND: {hwnd}")
    
    if hwnd:
        user32.SetForegroundWindow(hwnd)
        time.sleep(1)
        print("Sending F10 key...")
        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_F10, 0)
        time.sleep(0.1)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_F10, 0)
        time.sleep(3)
finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)
tgas = glob.glob(os.path.join(screenshots_dir, "*.tga"))
print(f"TGAs found: {len(tgas)}")
if tgas:
    img = Image.open(tgas[0])
    extrema = img.getextrema()
    print("Extrema RGBA:", extrema)
    img.save("docs/fase_1_7/screenshots/test_f10.png")
    print("Saved test_f10.png, size:", os.path.getsize("docs/fase_1_7/screenshots/test_f10.png"))
else:
    print("FAILED: No TGA found")
