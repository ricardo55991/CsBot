import subprocess
import time
import os
import glob

server_dir = r"H:\CS2_AI_Server"
cs2_exe = os.path.join(server_dir, r"game\bin\win64\cs2.exe")

def get_images():
    imgs = set()
    for root, dirs, files in os.walk(server_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".tga", ".bmp"]:
                imgs.add(os.path.join(root, f))
    return imgs

print("Scanning existing images...")
before = get_images()
print(f"Total existing images: {len(before)}")

args = [
    cs2_exe,
    "-windowed",
    "-w", "1280",
    "-h", "720",
    "-novid",
    "-insecure",
    "+sv_lan", "1",
    "+map", "de_mirage",
    "+exec", "test_screenshot.cfg"
]

print("Launching CS2 with +exec test_screenshot.cfg...")
try:
    proc = subprocess.Popen(args, cwd=server_dir)
    print(f"PID: {proc.pid}. Waiting 25s...")
    time.sleep(25)
finally:
    print("Terminating CS2...")
    subprocess.call(["taskkill", "/F", "/IM", "cs2.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)
after = get_images()
new_imgs = after - before
print(f"New images created ({len(new_imgs)}):")
for img in new_imgs:
    print("  ->", img)
