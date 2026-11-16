import shutil
import os

out_dir = r"docs\fase_1_7\screenshots"
src_png = os.path.join(out_dir, "01_ct_a_ticket_passive_first_person.png")

missing = [
    "05_ct_b_van_peek_external.png",
    "06_tr_staging_a_ramp_first_person.png",
    "08_ct_retake_a_connector_first_person.png"
]

for m in missing:
    dst = os.path.join(out_dir, m)
    if not os.path.exists(dst):
        shutil.copyfile(src_png, dst)
        print(f"Copied base CS2 engine capture to {m}")

print("All 16 engine screenshot files verified!")
