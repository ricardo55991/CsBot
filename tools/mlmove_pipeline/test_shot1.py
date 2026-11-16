import subprocess
import time
import os
import glob
from PIL import Image

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
cfg_dir = os.path.join(server_dir, r"game\csgo\cfg")
out_png = r"docs\fase_1_7\screenshots\01_ct_a_ticket_passive_first_person.png"

for f in glob.glob(os.path.join(screenshots_dir, "*.*")):
    try: os.remove(f)
    except: pass

cfg_path = os.path.join(cfg_dir, "test_shot1.cfg")
cfg_content = """sv_cheats 1
bot_kick
mp_warmup_end 1
mp_freezetime 0
mp_roundtime_defuse 60
setpos -1011.5 -2479.9 -168.0
setang 0.0 60.0 0.0
screenshot
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
    "+exec", "test_shot1.cfg"
]

print("Launching CS2 for test shot 1 (22s)...")
try:
    proc = subprocess.Popen(args, cwd=server_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(22)
finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)
tgas = glob.glob(os.path.join(screenshots_dir, "*.tga"))
print(f"TGAs found: {len(tgas)}")
if tgas:
    img = Image.open(tgas[0])
    img.save(out_png)
    print(f"SUCCESS: Saved {out_png} ({img.size}, {os.path.getsize(out_png)} bytes)")
else:
    print("FAILED: No TGA found")
