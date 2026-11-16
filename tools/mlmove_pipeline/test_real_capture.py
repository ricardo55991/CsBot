import subprocess
import time
import os
import glob
import ctypes
from ctypes import wintypes
from PIL import Image

user32 = ctypes.windll.user32

class KeyBdInput(ctypes.Structure):
    _fields_ = [('wVk', wintypes.WORD),
                ('wScan', wintypes.WORD),
                ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.c_size_t)]

class HardwareInput(ctypes.Structure):
    _fields_ = [('uMsg', wintypes.DWORD),
                ('wParamL', wintypes.WORD),
                ('wParamH', wintypes.WORD)]

class MouseInput(ctypes.Structure):
    _fields_ = [('dx', wintypes.LONG),
                ('dy', wintypes.LONG),
                ('mouseData', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.c_size_t)]

class Input_I(ctypes.Union):
    _fields_ = [('ki', KeyBdInput),
                ('mi', MouseInput),
                ('hi', HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [('type', wintypes.DWORD),
                ('ii', Input_I)]

INPUT_KEYBOARD = 1
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

def send_key_scan(scan_code):
    extra = ctypes.c_size_t(0)
    ii_down = Input_I()
    ii_down.ki = KeyBdInput(0, scan_code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYDOWN, 0, extra)
    inp_down = Input(INPUT_KEYBOARD, ii_down)
    user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))
    time.sleep(0.08)
    ii_up = Input_I()
    ii_up.ki = KeyBdInput(0, scan_code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, extra)
    inp_up = Input(INPUT_KEYBOARD, ii_up)
    user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")
cfg_dir = os.path.join(server_dir, r"game\csgo\cfg")
screenshots_dir = os.path.join(server_dir, r"game\csgo\screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

# Limpa screenshots anteriores
for pat in ["*.jpg", "*.png", "*.tga"]:
    for f in glob.glob(os.path.join(screenshots_dir, pat)):
        try: os.remove(f)
        except: pass
    for f in glob.glob(os.path.join(server_dir, r"game\csgo", pat)):
        try: os.remove(f)
        except: pass

autoexec_path = os.path.join(cfg_dir, "autoexec_capture.cfg")
with open(autoexec_path, "w", encoding="utf-8") as f:
    f.write("""sv_cheats 1
mp_warmup_end 1
mp_freezetime 0
mp_roundtime_defuse 60
bot_kick
bind "u" "jointeam 3"
bind "v" "exec capture_current.cfg"
echo "=== READY TO CAPTURE ==="
""")

capture_cfg = os.path.join(cfg_dir, "capture_current.cfg")
with open(capture_cfg, "w", encoding="utf-8") as f:
    f.write("""sv_cheats 1
setpos -1530.0 280.0 -160.0
setang 4.0 125.0 0.0
jpeg_screenshot real_spot_01 95
echo "=== SPOT 01 COMMANDS EXECUTED ==="
""")

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "-condebug",
    "+sv_lan", "1",
    "+sv_cheats", "1",
    "+map", "de_mirage",
    "+exec", "autoexec_capture.cfg"
]

print("[*] Launching CS2...")
proc = subprocess.Popen(args, cwd=server_dir)

try:
    print("[*] Waiting 26s for de_mirage to load...")
    time.sleep(26)
    
    hwnd = user32.FindWindowW(None, "Counter-Strike 2")
    if not hwnd:
        hwnd = user32.FindWindowW("SDL_app", None)
    print(f"[*] CS2 HWND: {hwnd}")
    
    if hwnd:
        user32.SetForegroundWindow(hwnd)
        time.sleep(1)
        
        # Pressiona 'u' (jointeam 3) - ScanCode 0x16 (PS/2 Set 1 para 'U')
        # MapVirtualKey for 'U' (0x55) is 0x16
        print("[*] Sending 'u' (jointeam 3) with scan 0x16...")
        send_key_scan(0x16)
        
        print("[*] Waiting 6s for player to spawn...")
        time.sleep(6)
        
        # Pressiona Espaço
        send_key_scan(0x39)
        time.sleep(1)
        
        # Pressiona 'v' (exec capture_current.cfg) - ScanCode 0x2F (PS/2 Set 1 para 'V' é 0x2F!)
        print("[*] Sending 'v' (exec capture_current.cfg) with scan 0x2F...")
        send_key_scan(0x2F)
        time.sleep(3)
        
        send_key_scan(0x2F)
        time.sleep(2)
        
    print("[*] Checking console.log...")
    log_file = os.path.join(server_dir, r"game\csgo\addons\metamod\console.log")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for l in lines[-35:]:
            print("  [LOG]", l.strip())
            
    print("\n[*] Searching for new screenshot files...")
    new_files = []
    start_time = time.time() - 120
    for root, dirs, files in os.walk(os.path.join(server_dir, "game")):
        for file in files:
            if file.endswith((".jpg", ".png", ".tga")):
                full_p = os.path.join(root, file)
                if os.path.getmtime(full_p) >= start_time:
                    new_files.append(full_p)
                    print(f"  [+] Found: {full_p} ({os.path.getsize(full_p)} bytes)")
                    try:
                        img = Image.open(full_p)
                        print(f"      Resolution: {img.size}, Extrema: {img.getextrema()}")
                    except Exception as e:
                        print(f"      Error reading image: {e}")
                        
    if not new_files:
        print("  [-] No new screenshot files found.")

finally:
    print("[*] Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[*] Done.")
