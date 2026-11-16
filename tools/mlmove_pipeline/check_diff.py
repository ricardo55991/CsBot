from PIL import Image
import os

img0 = Image.open(r"H:\CS2_AI_Server\game\csgo\screenshots\shot_0000.tga")
img1 = Image.open(r"H:\CS2_AI_Server\game\csgo\screenshots\shot_0001.tga")
img2 = Image.open(r"H:\CS2_AI_Server\game\csgo\screenshots\shot_0002.tga")

print(f"img0: size={img0.size}")
print(f"img1: size={img1.size}")
print(f"img2: size={img2.size}")

diff01 = sum(abs(a - b) for a, b in zip(img0.tobytes()[:1000], img1.tobytes()[:1000]))
diff12 = sum(abs(a - b) for a, b in zip(img1.tobytes()[:1000], img2.tobytes()[:1000]))
print(f"Diff sample 0 vs 1: {diff01}")
print(f"Diff sample 1 vs 2: {diff12}")
