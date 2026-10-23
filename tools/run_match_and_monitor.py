import os
import sys
import time
import subprocess
import glob

print("==================================================")
print("CS2 BOT MATCH RUNNER & MONITOR (5-8 Rounds)")
print("==================================================")

logs_dir = r"H:\CS2_AI_Server\debug_logs"
flag_path = os.path.join(logs_dir, "auto_debug.flag")
with open(flag_path, "w") as f:
    f.write("1")
print(f"[*] Verified {flag_path}")

# Record existing logs
existing_logs = set(glob.glob(os.path.join(logs_dir, "debug_match_*.md")))
print(f"[*] Existing logs count: {len(existing_logs)}")

# Launch CS2 Dedicated Server
cs2_exe = r"H:\CS2_AI_Server\game\bin\win64\cs2.exe"
server_dir = r"H:\CS2_AI_Server"
args = [
    cs2_exe,
    "-dedicated",
    "-insecure",
    "+sv_lan", "1",
    "-port", "27016",
    "+game_type", "0",
    "+game_mode", "1",
    "+map", "de_mirage",
    "+bot_quota", "10",
    "+bot_quota_mode", "fill",
    "+exec", "ai_competitive.cfg"
]

print(f"[*] Launching CS2 Dedicated Server: {' '.join(args)}")
proc = subprocess.Popen(args, cwd=server_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"[*] Process launched with PID: {proc.pid}")

# Wait for new log file
new_log = None
start_time = time.time()
print("[*] Waiting for new debug_match_*.md to appear...")

while time.time() - start_time < 90:
    current_logs = set(glob.glob(os.path.join(logs_dir, "debug_match_*.md")))
    diff = current_logs - existing_logs
    if diff:
        new_log = list(diff)[0]
        print(f"[+] Found new match log: {new_log}")
        break
    time.sleep(2)

if not new_log:
    print("[-] Timeout waiting for new match log! Killing process...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(1)

# Monitor rounds in the log
print("[*] Monitoring match progression in real time...")
rounds_completed = 0
last_report_time = time.time()
max_runtime = 600 # 10 minutes maximum

while time.time() - start_time < max_runtime:
    time.sleep(4)
    if not os.path.exists(new_log):
        continue

    try:
        with open(new_log, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        continue

    # Count rounds
    round_headers = [line for line in content.splitlines() if line.startswith("## Round ")]
    count = len(round_headers)
    if count > rounds_completed:
        rounds_completed = count
        print(f"[+] {time.strftime('%H:%M:%S')} - Detected {round_headers[-1]} (Total: {rounds_completed} rounds recorded)")

    # Stop after 7 rounds (satisfies 'de 5 a 8 rounds')
    if rounds_completed >= 7:
        # Check if round 7 has sufficient logs
        last_round_idx = content.rfind(f"## Round {rounds_completed}")
        if last_round_idx != -1 and len(content) - last_round_idx > 1000:
            print(f"[!] Goal achieved: {rounds_completed} rounds completed successfully!")
            print("[*] Waiting 6 seconds for disk flush before stopping CS2...")
            time.sleep(6)
            break

print("[*] Stopping CS2 Dedicated Server...")
subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("[+] CS2 Dedicated Server terminated.")
print(f"[+] Final Log Path: {new_log}")
print(f"[+] Final Log Size: {os.path.getsize(new_log)} bytes")
print("==================================================")
