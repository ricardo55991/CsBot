import subprocess
import time
import os

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
log_path = os.path.join(server_dir, r"game\csgo\console.log")

if os.path.exists(log_path):
    try: os.remove(log_path)
    except: pass

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "-condebug",
    "+sv_lan", "1",
    "+map", "de_mirage"
]

print("[*] Launching CS2 with -condebug...")
proc = subprocess.Popen(args, cwd=server_dir)

try:
    print("[*] Waiting 15s...")
    time.sleep(15)
finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    print(f"[*] console.log has {len(lines)} lines. Last 20 lines:")
    for l in lines[-20:]:
        print("  ", l.strip())
else:
    print("[-] console.log was not created!")
