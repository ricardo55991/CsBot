import json

with open('docs/spot_recording/recorded_spots_live.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

latest_spots = {}
counts = {}
for entry in data:
    snum = entry.get('spot_number')
    counts[snum] = counts.get(snum, 0) + 1
    latest_spots[snum] = entry

print(f"Total entries: {len(data)}, Unique spots: {len(latest_spots)}")
for snum in sorted(latest_spots.keys()):
    e = latest_spots[snum]
    c = counts[snum]
    repeat_str = f"({c}x)" if c > 1 else "    "
    coords = [round(x, 1) for x in e["coords"]]
    yaw = round(e["aim"]["yaw"], 1)
    pitch = round(e["aim"]["pitch"], 1)
    stance = e["stance"]
    print(f"Spot #{snum:02d} {repeat_str}: coords={coords}, yaw={yaw:+6.1f}, pitch={pitch:+5.1f}, stance='{stance}'")
