# -*- coding: utf-8 -*-
import os
import re

cat_path = "tools/mlmove_pipeline/build_complete_automated_spots_catalog.py"
with open(cat_path, "r", encoding="utf-8") as f:
    text = f.read()

# Spot 7
text = text.replace(
    "[-1950.0, 380.0, -160.0]",
    "[-1980.0, 300.0, -160.0]"
)

# Spot 31
text = text.replace(
    "[220.0, -2040.0, -40.0]",
    "[350.0, -2050.0, -104.0]"
)

# Spot 47
text = text.replace(
    "[-180.0, -1620.0, -110.0]",
    "[-180.0, -1620.0, -60.0]"
)

# screenshots_dir fix
text = re.sub(
    r'screenshots_dir\s*=\s*r"docs.*?screenshots"',
    'screenshots_dir = os.path.join(BASE_DIR, "docs", "fase_1_7", "screenshots")',
    text
)

with open(cat_path, "w", encoding="utf-8") as f:
    f.write(text)

print("[+] build_complete_automated_spots_catalog.py patched successfully!")

# Update capture_all_53_spots.py with god 1 and buddha 1
cap_path = "tools/mlmove_pipeline/capture_all_53_spots.py"
with open(cap_path, "r", encoding="utf-8") as f:
    cap_text = f.read()

old_init = """    init_cmds = [
        "sv_cheats 1",
        "bot_kick",
        "mp_warmup_end 1",
        "mp_freezetime 0",
        "mp_roundtime_defuse 60",
        "jointeam 3 0"
    ]"""

new_init = """    init_cmds = [
        "sv_cheats 1",
        "god 1",
        "buddha 1",
        "sv_falldamage_scale 0",
        "sv_regeneration_force_on 1",
        "bot_kick",
        "mp_warmup_end 1",
        "mp_freezetime 0",
        "mp_roundtime_defuse 60",
        "jointeam 3 0"
    ]"""

if old_init in cap_text:
    cap_text = cap_text.replace(old_init, new_init)
    with open(cap_path, "w", encoding="utf-8") as f:
        f.write(cap_text)
    print("[+] capture_all_53_spots.py patched with godmode and fall protection!")
else:
    print("[-] init_cmds not found in capture_all_53_spots.py")
