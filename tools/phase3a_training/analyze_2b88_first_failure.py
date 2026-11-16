import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("training_runs/positioning_v2_real_temporal/opening_route_canary_v1")
SRC_DIR = BASE / "tr_live_route_certification_v1"
TELEM = SRC_DIR / "solo_route_telemetry.jsonl"
OUT_DIR = BASE / "tr_live_diagnostic_patch_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_FIELDS = [
    "actual_position",
    "current_waypoint",
    "next_waypoint",
    "nav_area",
    "nav_distance",
    "path_remaining",
    "movement_command",
    "executor_state",
]

by_session = defaultdict(list)
field_present = {k: 0 for k in REQUIRED_FIELDS}
total_rows = 0

with TELEM.open("r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        total_rows += 1
        for k in REQUIRED_FIELDS:
            if k in r and r[k] is not None:
                field_present[k] += 1
        key = (r.get("cert_route", ""), int(r.get("round", 0) or 0))
        by_session[key].append(r)

missing_fields = [k for k, cnt in field_present.items() if cnt == 0]
sufficiency = {
    "marco": "2B.8.8",
    "data_nature": "REAL",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "total_ticks_inspected": total_rows,
    "field_presence_counts": field_present,
    "missing_fields": missing_fields,
    "sufficient_for_physical_cause": len(missing_fields) == 0,
}
(OUT_DIR / "telemetry_sufficiency.json").write_text(json.dumps(sufficiency, indent=2), encoding="utf-8")

analyses = []
clusters = []

def dist3(a, b):
    if not a or not b:
        return 0.0
    return math.sqrt(sum((float(a[i]) - float(b[i])) ** 2 for i in range(3)))

for (route, rnd), recs in sorted(by_session.items()):
    if rnd < 1 or rnd > 10:
        continue
    last = recs[-1]
    status = last.get("arrival_status", "")
    reason = last.get("completion_reason", "")
    arrived = status in ("ON_TIME", "LATE") or reason == "DESTINATION_REACHED"

    # Find last tick with valid progress (traveled_distance increased or waypoint changed) and first tick without progress
    last_prog_idx = 0
    first_stall_idx = len(recs) - 1
    for i in range(1, len(recs)):
        prev_pos = recs[i - 1].get("actual_position")
        cur_pos = recs[i].get("actual_position")
        moved = dist3(prev_pos, cur_pos)
        if moved >= 1.5 or recs[i].get("current_waypoint") != recs[i - 1].get("current_waypoint"):
            last_prog_idx = i
        elif i > last_prog_idx + 8 and first_stall_idx == len(recs) - 1:
            first_stall_idx = i

    lp = recs[last_prog_idx]
    fs = recs[first_stall_idx]
    pos = fs.get("actual_position") or last.get("actual_position")
    wp = fs.get("current_waypoint") or last.get("current_waypoint")
    state = last.get("executor_state", "")

    if arrived:
        cause = "NONE_ARRIVED"
    elif reason == "UTILITY_PLAN_CHANGED" or status == "TACTICAL_REDIRECT":
        cause = "SESSION_FINALIZED_EARLY"
    elif reason == "CANARY_BLOCKED_FALLBACK":
        cause = "STATIC_COLLISION"
    elif reason == "TIMEOUT":
        cause = "WAYPOINT_NEVER_ADVANCED"
    elif reason == "AUTHORITY_RELEASED":
        cause = "EXECUTOR_STATE_STUCK"
    else:
        cause = "UNKNOWN"

    analyses.append({
        "route": route,
        "round": rnd,
        "arrived": arrived,
        "status": status,
        "completion_reason": reason,
        "last_progress_tick": lp.get("tick"),
        "first_no_progress_tick": fs.get("tick"),
        "pos_at_stall": pos,
        "velocity_at_stall": fs.get("velocity_xy"),
        "current_waypoint": wp,
        "next_waypoint": fs.get("next_waypoint"),
        "executor_state": state,
        "weapon": fs.get("active_weapon"),
        "cause": cause,
    })

# Cluster failures within 32 units
failed = [a for a in analyses if not a["arrived"]]
cluster_groups = []
for f_item in failed:
    placed = False
    for cg in cluster_groups:
        if cg["route"] == f_item["route"] and cg["waypoint"] == f_item["current_waypoint"] and cg["executor_state"] == f_item["executor_state"] and dist3(cg["center_pos"], f_item["pos_at_stall"]) <= 32.0:
            cg["rounds"].append(f_item["round"])
            cg["count"] += 1
            placed = True
            break
    if not placed:
        cluster_groups.append({
            "route": f_item["route"],
            "waypoint": f_item["current_waypoint"],
            "executor_state": f_item["executor_state"],
            "center_pos": f_item["pos_at_stall"],
            "count": 1,
            "rounds": [f_item["round"]],
            "deterministic_portal_or_executor_failure": False,
        })

for cg in cluster_groups:
    cg["deterministic_portal_or_executor_failure"] = cg["count"] >= 8

(OUT_DIR / "first_failure_tick_analysis.json").write_text(json.dumps({
    "marco": "2B.8.8",
    "data_nature": "REAL",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "total_sessions": len(analyses),
    "failed_sessions": len(failed),
    "sessions": analyses,
}, indent=2), encoding="utf-8")

(OUT_DIR / "failure_coordinate_clusters.json").write_text(json.dumps({
    "marco": "2B.8.8",
    "data_nature": "REAL",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "clusters": cluster_groups,
}, indent=2), encoding="utf-8")

print("SUFFICIENCY:", json.dumps(sufficiency))
print("CLUSTERS:")
for cg in cluster_groups:
    print(f"  {cg['route']} wp={cg['waypoint']} state={cg['executor_state']} center={cg['center_pos']} count={cg['count']} det={cg['deterministic_portal_or_executor_failure']}")
