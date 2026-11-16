import subprocess
import time
import os

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")

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

print("Launching CS2 with -condebug...")
try:
    proc = subprocess.Popen(args, cwd=server_dir)
    print("Waiting 30s...")
    time.sleep(30)
finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

c_log = os.path.join(server_dir, r"game\csgo\console.log")
if os.path.exists(c_log):
    with open(c_log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    print(f"console.log lines: {len(lines)}")
    print("Last 25 lines of console.log:")
    for l in lines[-25:]:
        print("  ", l.strip())
else:
    print("console.log not found!")
