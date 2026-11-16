import sys
sys.path.append('tools/mlmove_pipeline')
import build_complete_automated_spots_catalog as cat
import pprint

for s in cat.SPOTS_CATALOG:
    if s["num"] == 53:
        s["primary_aim"] = {
            "name": "Quina do Tetris (Reto ao Tetris)",
            "target": "Quina do Tetris",
            "pitch": 1.0,
            "yaw": 90.0,
            "desc": "Mira reta ao Tetris e passagem da Caverna (exatamente como desenhado no print)."
        }
        s["secondary_aims"] = [
            {"name": "Subida da Caverna / Rampa A", "target": "Subida da Caverna / Rampa A", "pitch": 1.0, "yaw": 70.0, "desc": "Visão da boca da Caverna pela fresta da madeira."},
            {"name": "Cabecinha / Stairs", "target": "Cabecinha / Stairs", "pitch": 0.0, "yaw": 135.0, "desc": "Suporte a avanço pelo Conector e Cabecinha."}
        ]
        print("[+] Spot #53 mira ajustada para Yaw +90.0 (reta ao Tetris)!")
        break

with open('tools/mlmove_pipeline/build_complete_automated_spots_catalog.py', 'r', encoding='utf-8') as f:
    orig_code = f.read()

idx1 = orig_code.find('SPOTS_CATALOG = [')
idx2 = orig_code.find('def generate_spot_card')

if idx1 != -1 and idx2 != -1:
    formatted_catalog = "SPOTS_CATALOG = " + pprint.pformat(cat.SPOTS_CATALOG, indent=4, width=120) + "\n\n"
    new_code = orig_code[:idx1] + formatted_catalog + orig_code[idx2:]
    with open('tools/mlmove_pipeline/build_complete_automated_spots_catalog.py', 'w', encoding='utf-8') as f:
        f.write(new_code)
    print("[+] build_complete_automated_spots_catalog.py salvo!")
