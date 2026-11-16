from PIL import ImageGrab

try:
    img = ImageGrab.grab(all_screens=True)
    print(f"ImageGrab successful! Size: {img.size}")
except Exception as e:
    print(f"ImageGrab failed: {e}")
