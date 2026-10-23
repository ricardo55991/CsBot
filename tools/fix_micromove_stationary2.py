with open(r'src/CsBotManager/MicroMoveEngine.cs', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if 'string weaponName = pawn.WeaponServices' in line and i < 1000:
        new_lines.append(line)
        skip = True
    elif skip:
        if 'targetTensor[i, 11] =' in line:
            skip = False
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(r'src/CsBotManager/MicroMoveEngine.cs', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Cleaned wrong stationary block from MicroMoveEngine.cs')
