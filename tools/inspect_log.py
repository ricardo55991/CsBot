import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

log_path = r'H:\CS2_AI_Server\debug_logs\debug_match_20261023_012334.md'
with open(log_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
    text = f.read()

round_blocks = re.split(r'\n(?=## .*?Round \d+)', text)
print(f"Total round sections: {len(round_blocks)}")

for r in round_blocks:
    if 'Round' not in r:
        continue
    first_line = r.strip().splitlines()[0]
    print(f"\n=======================================================")
    print(f"{first_line}")
    print(f"=======================================================")
    
    # 1. Loadouts and Buy State
    econ_match = re.search(r'### .*?Economia e Loadout Inicial(.*?)(?=####|###|\Z)', r, re.DOTALL)
    if econ_match:
        print("\n--- LOADOUTS & ECONOMIA ---")
        lines = econ_match.group(1).strip().splitlines()
        for l in lines:
            if '|' in l and not l.startswith('|---'):
                print(l)
            elif 'BuyState' in l or 'Status' in l:
                print(l)

    # 2. Ollama Tactical Decision & JSON
    json_match = re.search(r'#### .*?Decisão Estruturada da IA.*?(```json.*?```)', r, re.DOTALL)
    if json_match:
        print("\n--- PLANO TÁTICO IGL (JSON) ---")
        code_block = json_match.group(1).strip()
        print(f"Tamanho do JSON: {len(code_block)} chars")
        # preview
        lines_json = code_block.splitlines()
        for lj in lines_json[:12]:
            print("  ", lj)
        if len(lines_json) > 12:
            print("   ...")
            for lj in lines_json[-4:]:
                print("  ", lj)

    # 3. Round End / Motivo
    end_matches = re.findall(r'.*Fim do Round.*', r)
    if end_matches:
        print("\n--- FIM DO ROUND ---")
        for em in end_matches:
            print(em)
    else:
        # Check round end event in timeline
        timeline_end = re.findall(r'.*(?:venceu|detonada|desarmada|eliminados|expirou|Motivo).*', r)
        for te in timeline_end[-5:]:
            print("Timeline end event:", te)

