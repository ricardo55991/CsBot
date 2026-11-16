import subprocess
import time
import os
import psutil

cs2_exe = r"H:\CS2_AI_Server\game\bin\win64\cs2.exe"
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

print("Launching CS2 client test...")
try:
    proc = subprocess.Popen(args, cwd=r"H:\CS2_AI_Server")
    print(f"Launched with PID {proc.pid}. Waiting 15s...")
    time.sleep(15)
    print("Checking if process is alive...")
    is_alive = proc.poll() is None
    print(f"Is alive: {is_alive}")
finally:
    print("Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Cleaned up.")
