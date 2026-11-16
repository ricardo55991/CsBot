import subprocess
import time
import os
import glob
from source_rcon import SourceRcon

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "+sv_lan", "1",
    "-port", "27015",
    "+rcon_password", "csbot",
    "+map", "de_mirage"
]

print("Launching CS2 with RCON support...")
try:
    proc = subprocess.Popen(args, cwd=server_dir)
    print("Waiting 20s for map load...")
    time.sleep(20)
    
    print("Connecting to RCON 127.0.0.1:27015...")
    rcon = SourceRcon("127.0.0.1", 27015, "csbot")
    try:
        rcon.connect()
        print("[+] RCON Connected successfully!")
        resp = rcon.command("status")
        print("Status response:", resp[:200])
        rcon.command("sv_cheats 1; bot_kick; mp_warmup_end 1; mp_freezetime 0")
        time.sleep(1)
        rcon.command("setpos -1011.5 -2479.9 -168.0; setang 0.0 60.0 0.0")
        time.sleep(1)
        rcon.command("screenshot")
        print("[+] Screenshot 1 sent via RCON!")
        time.sleep(2)
        rcon.command("setpos -284.2 -2399.9 -164.0; setang 0.0 110.0 0.0")
        time.sleep(1)
        rcon.command("screenshot")
        print("[+] Screenshot 2 sent via RCON!")
        time.sleep(2)
    except Exception as e:
        print(f"[-] RCON Error: {e}")
    finally:
        rcon.close()
finally:
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
