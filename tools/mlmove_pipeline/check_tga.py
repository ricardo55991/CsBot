from PIL import Image
import os

tga_path = r"H:\CS2_AI_Server\game\csgo\screenshots\shot_0000.tga"
if os.path.exists(tga_path):
    img = Image.open(tga_path)
    print(f"TGA Image loaded successfully! Size: {img.size}, Format: {img.format}, Mode: {img.mode}")
    out_png = "docs/fase_1_7/screenshots/test_tga_converted.png"
    img.save(out_png)
    print(f"Converted and saved to {out_png}")
else:
    print(f"File {tga_path} does not exist!")
