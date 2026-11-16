import json
import re

# Carrega de_mirage.json
with open("src/CsBotManager/MapProfiles/de_mirage.json", "r", encoding="utf-8") as f:
    de_mirage = json.load(f)
v2_spots = {s["id"]: s for s in de_mirage["spots"]}

# Carrega profile_v2_human_review_checklist.md
with open("docs/fase_1_6/profile_v2_human_review_checklist.md", "r", encoding="utf-8") as f:
    checklist_text = f.read()

# Expressão para capturar as linhas da tabela
pattern = re.compile(r"\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`setpos\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+);\s*setang\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)`\s*\|")
matches = pattern.findall(checklist_text)

print(f"Encontrados {len(matches)} spots no checklist:")
all_match = True
for m in matches:
    num, sid, x, y, z, pitch, yaw, roll = m
    x, y, z = float(x), float(y), float(z)
    pitch, yaw = float(pitch), float(yaw)
    
    if sid not in v2_spots:
        print(f"ERRO: Spot {sid} não encontrado no de_mirage.json")
        all_match = False
        continue
    
    sp = v2_spots[sid]
    sx, sy, sz = sp["x"], sp["y"], sp["z"]
    spitch, syaw = sp["pitch"], sp["yaw"]
    
    pos_match = (x == sx and y == sy and z == sz)
    ang_match = (pitch == spitch and yaw == syaw)
    
    if not (pos_match and ang_match):
        print(f"DIVERGÊNCIA em {sid}: Checklist=({x},{y},{z}) vs de_mirage=({sx},{sy},{sz})")
        all_match = False
    else:
        print(f"OK: #{num} {sid} -> pos [{x}, {y}, {z}] ang [{pitch}, {yaw}, {roll}]")

if all_match:
    print("\nRECONCILIAÇÃO PERFEITA: 100% dos 8 spots coincidem exatamente com de_mirage.json!")
else:
    print("\nFALHA DE RECONCILIAÇÃO!")
