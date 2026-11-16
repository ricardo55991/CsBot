import json
from pathlib import Path
from collections import defaultdict

ROOT = Path("training_runs/positioning_v2_real_temporal/opening_route_canary_v1")
TELEM = ROOT / "tr_canary_v1" / "tr_canary_telemetry.jsonl"
OUT_DIR = ROOT / "tr_geometric_patch_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TARGET_ROUNDS = {2, 3, 5, 7, 9, 10, 11}

by_round = defaultdict(list)
with TELEM.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        r = rec.get("round")
        if r in TARGET_ROUNDS:
            by_round[r].append(rec)

results = []
for r in sorted(TARGET_ROUNDS):
    recs = by_round[r]
    if not recs:
        results.append({"round": r, "found": False, "root_cause": "UNKNOWN"})
        continue
    first = recs[0]
    last = recs[-1]
    dest = last.get("intended_destination", "")
    status = last.get("arrival_status", "")
    reason = last.get("completion_reason", "")
    state = last.get("executor_state", "")
    planned_site = last.get("planned_bombsite", "")
    route_site = last.get("route_bombsite", "")
    is_c4 = bool(last.get("canary_is_bomb_carrier", False))
    expected_d = float(last.get("expected_distance", 0) or 0)
    traveled_d = float(last.get("traveled_distance", 0) or 0)
    detour = round(traveled_d / expected_d, 4) if expected_d > 0 else 0.0
    elapsed = float(last.get("elapsed_seconds", 0) or 0)

    # Sample key ticks (start, mid, last 3)
    sample_indices = sorted(set([0, len(recs)//4, len(recs)//2, (3*len(recs))//4, max(0, len(recs)-2), len(recs)-1]))
    samples = []
    for idx in sample_indices:
        t = recs[idx]
        samples.append({
            "tick": t.get("tick"),
            "elapsed_s": t.get("elapsed_seconds"),
            "pos": [t.get("pos_x"), t.get("pos_y"), t.get("pos_z")],
            "speed": t.get("speed"),
            "nav_area": t.get("nav_area"),
            "wp_idx": t.get("waypoint_index"),
            "wp_name": t.get("current_waypoint"),
            "next_wp": t.get("next_waypoint"),
            "traveled_d": t.get("traveled_distance"),
            "expected_d": t.get("expected_distance"),
            "state": t.get("executor_state"),
            "authority": t.get("authority_owner"),
            "blocker": t.get("blocker"),
            "transition_type": t.get("transition_type"),
            "deadline_s": t.get("deadline_seconds"),
            "weapon": t.get("active_weapon"),
        })

    if dest == "a_palace_deep_room" and status == "PENDING":
        root_cause = "SESSION_FINALIZATION_FAILURE" if detour < 1.3 else "PATH_DETOUR"
        secondary = "SESSION_FINALIZATION_FAILURE"
        if planned_site == "B" and route_site == "A" and not is_c4:
            secondary = "PLAN_ROUTE_MISMATCH"
    elif dest == "tr_a_ramp_staging_wait" and reason == "TIMEOUT":
        root_cause = "PATH_DETOUR"
        secondary = "WAYPOINT_MISALIGNED"
    elif dest == "tr_b_apps_kitchen_control" and reason == "CANARY_BLOCKED_FALLBACK":
        root_cause = "FALSE_BLOCK" if "TEAMMATE" in str(last.get("blocker", "")) else "WAYPOINT_MISALIGNED"
        secondary = "REAL_BLOCK"
    elif dest == "tr_b_apps_house_staging" and status == "LATE":
        root_cause = "DEADLINE_TOO_SHORT"
        secondary = "PATH_DETOUR"
    else:
        root_cause = "UNKNOWN"
        secondary = ""

    results.append({
        "round": r,
        "tick_count": len(recs),
        "intended_destination": dest,
        "arrival_status": status,
        "completion_reason": reason,
        "executor_state": state,
        "planned_bombsite": planned_site,
        "route_bombsite": route_site,
        "canary_is_bomb_carrier": is_c4,
        "expected_distance": expected_d,
        "traveled_distance": traveled_d,
        "detour_ratio": detour,
        "elapsed_seconds": elapsed,
        "deadline_seconds": last.get("deadline_seconds"),
        "last_pos": [last.get("pos_x"), last.get("pos_y"), last.get("pos_z")],
        "last_wp": last.get("current_waypoint"),
        "last_blocker": last.get("blocker"),
        "root_cause": root_cause,
        "secondary_cause": secondary,
        "sample_ticks": samples,
    })

out = {
    "marco": "2B.8.6",
    "data_nature": "REAL",
    "source_telemetry": str(TELEM).replace("\\", "/"),
    "rounds_analyzed": sorted(TARGET_ROUNDS),
    "sessions": results,
}
(OUT_DIR / "failed_session_root_causes.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
for s in results:
    print(f"R{s['round']} {s['intended_destination']}: status={s['arrival_status']} reason={s['completion_reason']} detour={s['detour_ratio']} elapsed={s['elapsed_seconds']}s last_pos={s['last_pos']} wp={s['last_wp']} root={s['root_cause']}")
