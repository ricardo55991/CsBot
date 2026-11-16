import subprocess
import time
import os
import glob
from PIL import Image

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")

for f in glob.glob(os.path.join(screenshots_dir, "*.*")):
    try: os.remove(f)
    except: pass

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

print("Launching CS2 to trigger de_mirage.cfg on map load...")
try:
    proc = subprocess.Popen(args, cwd=server_dir)
    print("Waiting 30s...")
    time.sleep(30)
finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)
tgas = glob.glob(os.path.join(screenshots_dir, "*.tga"))
print(f"TGAs found: {len(tgas)}")
if tgas:
    img = Image.open(tgas[0])
    extrema = img.getextrema()
    print("Extrema RGBA:", extrema)
    img.save("docs/fase_1_7/screenshots/test_demirage_cfg.png")
    print("Saved test_demirage_cfg.png, size:", os.path.getsize("docs/fase_1_7/screenshots/test_demirage_cfg.png"))
else:
    print("FAILED: No TGA found")
