import subprocess
import time
import ctypes
from ctypes import wintypes
import os
from PIL import ImageGrab

user32 = ctypes.windll.user32

def find_cs2_window():
    # Tenta por título
    hwnd = user32.FindWindowW(None, "Counter-Strike 2")
    if hwnd:
        return hwnd
    # Tenta por classe SDL_app
    hwnd = user32.FindWindowW("SDL_app", None)
    if hwnd:
        return hwnd
    return 0

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

print("Launching CS2 for window capture test...")
try:
    proc = subprocess.Popen(args, cwd=r"H:\CS2_AI_Server")
    print(f"Launched PID {proc.pid}. Waiting 22 seconds for map load...")
    time.sleep(22)
    
    hwnd = find_cs2_window()
    print(f"HWND found: {hwnd}")
    if hwnd:
        user32.SetForegroundWindow(hwnd)
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        print(f"Window Rect: ({rect.left}, {rect.top}, {rect.right}, {rect.bottom})")
        
        # Garante foco e captura
        time.sleep(1)
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        img = ImageGrab.grab(bbox)
        os.makedirs("docs/fase_1_7/screenshots", exist_ok=True)
        img.save("docs/fase_1_7/screenshots/test_window_capture.png")
        print(f"Saved test capture: size={img.size}")
    else:
        print("Window not found!")
finally:
    print("Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Done.")
