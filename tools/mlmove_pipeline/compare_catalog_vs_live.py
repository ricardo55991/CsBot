import sys
import json
sys.path.insert(0, 'tools/mlmove_pipeline')
from build_complete_automated_spots_catalog import SPOTS_CATALOG

with open('docs/spot_recording/recorded_spots_live.json', 'r', encoding='utf-8') as f:
    live = json.load(f)

latest = {}
for entry in live:
    latest[entry['spot_number']] = entry

print("================================================================================")
print("COMPARISON: Current SPOTS_CATALOG vs User Live Recording")
print("================================================================================")
diff_count = 0
for s in SPOTS_CATALOG:
    num = s['num']
    sid = s['id']
    if num in latest:
        rec = latest[num]
        c_old = [round(x, 1) for x in s['coords']]
        c_new = [round(x, 1) for x in rec['coords']]
        y_old = round(s['primary_aim']['yaw'], 1)
        y_new = round(rec['aim']['yaw'], 1)
        p_old = round(s['primary_aim']['pitch'], 1)
        p_new = round(rec['aim']['pitch'], 1)
        st_old = s.get('stance', 'Em pé')
        st_new = rec['stance']
        diff_c = (abs(c_old[0]-c_new[0]) > 2 or abs(c_old[1]-c_new[1]) > 2 or abs(c_old[2]-c_new[2]) > 2)
        diff_y = abs(y_old - y_new) > 2
        diff_p = abs(p_old - p_new) > 2
        diff_s = st_old != st_new
        if diff_c or diff_y or diff_p or diff_s:
            diff_count += 1
            print(f"#{num:02d} {sid:<30} [DIFF]: coords {c_old} -> {c_new} | yaw: {y_old:+.1f} -> {y_new:+.1f} | pitch: {p_old:+.1f} -> {p_new:+.1f} | stance: {st_old} -> {st_new}")
        else:
            print(f"#{num:02d} {sid:<30} [MATCH]")
    else:
        print(f"#{num:02d} {sid:<30} [RETAIN_HOMOLOGATED: Spot #50 Staging TR]")

print("================================================================================")
print(f"Total spots: {len(SPOTS_CATALOG)}, Different from user recordings: {diff_count}")
print("================================================================================")
