import glob
import os
from PIL import Image

pngs = sorted(glob.glob("docs/fase_1_7/screenshots/*.png"))
print(f"Total PNGs found: {len(pngs)}")
for p in pngs:
    img = Image.open(p)
    print(f"  -> {os.path.basename(p):45} : size={img.size}, mode={img.mode}, file_size={os.path.getsize(p)} bytes")
