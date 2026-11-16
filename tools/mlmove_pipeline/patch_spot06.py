import re

path = "tools/mlmove_pipeline/build_complete_automated_spots_catalog.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Atualizar Spot 06 no SPOTS_CATALOG
old_spot6 = """    {   'coords': [-2280.0, 710.0, -38.0],
        'cover': 'Teto e para-brisa da Van B.',
        'danger': 'Ajuste V3.4: Posicionado exatamente em cima da Van (teto/capô) em Z=-38.',
        'group': 'Bomb B - Marcação & Plant',
        'id': 'b_van_behind_apps_hold',
        'name': 'Em Cima da Van - Marcação Saída do Tapete',
        'num': 6,
        'objective': 'Segurar push agressivo de Apartamentos para CT Anchor de B.',
        'primary_aim': {   'desc': 'Em pé em cima da Van cravado na boca do Tapete.',
                           'name': 'Saída de Apartamentos / Tapete',
                           'pitch': 0.0,
                           'target': 'Saída de Apartamentos / Tapete',
                           'yaw': 5.0},"""

new_spot6 = """    {   'coords': [-2100.0, 660.0, -20.0],
        'cover': 'Teto e lataria da Van B.',
        'danger': 'Ajuste V3.7: Posicionado no teto/capô da Van B cobrindo a Saída do Tapete.',
        'group': 'Bomb B - Marcação & Plant',
        'id': 'b_van_behind_apps_hold',
        'name': 'Em Cima da Van - Marcação Saída do Tapete',
        'num': 6,
        'objective': 'Segurar push agressivo de Apartamentos para CT Anchor de B.',
        'primary_aim': {   'desc': 'Em pé em cima da Van cravado na boca do Tapete.',
                           'name': 'Saída de Apartamentos / Tapete',
                           'pitch': 1.0,
                           'target': 'Saída de Apartamentos / Tapete',
                           'yaw': -5.0},"""

if old_spot6 in content:
    content = content.replace(old_spot6, new_spot6)
    print("[+] Spot 06 atualizado com sucesso no SPOTS_CATALOG!")
else:
    print("[-] Aviso: bloco exato de Spot 06 não encontrado, tentando regex...")
    pattern = r"\{\s*'coords':\s*\[-2280\.0,\s*710\.0,\s*-38\.0\].*?'id':\s*'b_van_behind_apps_hold'.*?'yaw':\s*5\.0\},"
    content = re.sub(pattern, new_spot6, content, flags=re.DOTALL)
    print("[+] Regex aplicado para Spot 06.")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("[+] Arquivo salvo.")
