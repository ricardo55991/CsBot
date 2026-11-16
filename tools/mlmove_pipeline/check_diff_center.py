from PIL import Image

img0 = Image.open(r"H:\CS2_AI_Server\game\csgo\screenshots\shot_0000.tga")
img1 = Image.open(r"H:\CS2_AI_Server\game\csgo\screenshots\shot_0001.tga")
img2 = Image.open(r"H:\CS2_AI_Server\game\csgo\screenshots\shot_0002.tga")

# Compara o centro da tela (onde fica o cenário 3D)
b0 = img0.tobytes()
b1 = img1.tobytes()
b2 = img2.tobytes()

print("Tamanho total bytes:", len(b0))
mid_start = len(b0) // 2
mid_end = mid_start + 100000

diff01 = sum(abs(a - b) for a, b in zip(b0[mid_start:mid_end], b1[mid_start:mid_end]))
diff12 = sum(abs(a - b) for a, b in zip(b1[mid_start:mid_end], b2[mid_start:mid_end]))
print(f"Diff no centro da imagem (100.000 pixels centrais) 0 vs 1: {diff01}")
print(f"Diff no centro da imagem 1 vs 2: {diff12}")
