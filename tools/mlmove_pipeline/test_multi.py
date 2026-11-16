import subprocess
import time
import os
import glob

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
    "+map", "de_mirage",
    "+exec", "test_multi_screenshot.cfg"
]

print("Launching CS2 with multi screenshot cfg...")
try:
    proc = subprocess.Popen(args, cwd=server_dir)
    time.sleep(25)
finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

files = glob.glob(os.path.join(screenshots_dir, "*.*"))
print(f"Screenshots generated ({len(files)}):")
for f in files:
    print("  ->", f, os.path.getsize(f))
