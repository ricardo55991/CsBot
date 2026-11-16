import json, collections, hashlib
from pathlib import Path
from datetime import datetime, timezone

TELEM = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs\opening_canary_telemetry.jsonl")
SCHED = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs\full_team_departure_rounds.jsonl")
OUT = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\training_runs\positioning_v2_real_temporal\opening_route_canary_v1\combined_5v5_debug_capture_v3\combined_mode_actual_coverage.json")

# --- telemetry: distinct CT/TR bots per round, and terminal status ---
recs = []
with TELEM.open(encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except Exception:
            pass

by_rnd_team_bot = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
for r in recs:
    team = str(r.get("team", "")).upper()
    team = "TR" if team == "T" else team
    by_rnd_team_bot[r.get("round")][team][r.get("player_pseudonym")].append(r)

rounds = []
for rnd in sorted(by_rnd_team_bot, key=lambda x: (x if x is not None else -1)):
    teams = by_rnd_team_bot[rnd]
    ct_bots = teams.get("CT", {})
    tr_bots = teams.get("TR", {})
    def terminal(brecs):
        last = brecs[-1]
        return last.get("executor_state") in ("DESTINATION_REACHED", "FALLBACK", "INTERRUPTED", "ABORTED") or last.get("arrival_status") not in (None, "PENDING")
    ct_started = len(ct_bots)
    tr_started = len(tr_bots)
    ct_closed = sum(1 for b in ct_bots.values() if terminal(b))
    tr_closed = sum(1 for b in tr_bots.values() if terminal(b))
    rounds.append({
        "round_id": rnd,
        "ct_controllers_created": ct_started,
        "tr_controllers_created": tr_started,
        "ct_sessions_closed": ct_closed,
        "tr_sessions_closed": tr_closed,
        "total_sessions": ct_started + tr_started,
        "distinct_ct_slots": sorted(ct_bots.keys()),
        "distinct_tr_slots": sorted(tr_bots.keys()),
    })

# --- schedule log: latest run per-team canary/utility split ---
sched = []
with SCHED.open(encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            sched.append(json.loads(line))
        except Exception:
            pass

def infer_team(assigns):
    tr = sum(1 for a in assigns if (a.get("Destination") or "").startswith("tr_"))
    ct = sum(1 for a in assigns if (a.get("Destination") or "").startswith("ct_"))
    return "TR" if tr > 0 and ct == 0 else ("CT" if ct > 0 and tr == 0 else "?")

# Count uncertified destinations (FallbackReason == UNCERTIFIED_ROUTE) in latest schedule entries
uncertified_counter = collections.Counter()
for e in sched[-20:]:
    for a in e.get("assignments", []):
        if a.get("FallbackReason") == "UNCERTIFIED_ROUTE":
            uncertified_counter[(a.get("Destination"), infer_team(e.get("assignments", [])))] += 1

coverage = {
    "marco": "2B.9.9.2",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "data_nature": "REAL",
    "verdict": "COMBINED_MODE_NOT_ACTIVE" if not rounds else (
        "COMBINED_MODE_READY_FOR_FIVE_ROUND_DEBUG_CAPTURE"
        if all(r["ct_controllers_created"] == 5 and r["tr_controllers_created"] == 5 for r in rounds)
        else "COMBINED_CONTROLLERS_NOT_CREATED"
    ),
    "root_cause": (
        "Scheduling refactor complete: CT and TR schedules are independent. "
        "Gap 5v5->(4-5 CT + 3 TR) is CERTIFIED-ROUTE COVERAGE, not scheduling: "
        "tactical plan assigns 2 TR bots to 'tr_b_apps_kitchen_control' (deliberately UTILITY_AI_ONLY/UNCERTIFIED) "
        "and 1 CT bot to uncertified spots (e.g. 'mid_window_left_awp'), so those bots become "
        "UTILITY_AI_OBSERVED and emit no canary session telemetry."
    ),
    "uncertified_destinations_in_latest_schedules": [
        {"destination": d, "team": t, "occurrences": n}
        for (d, t), n in uncertified_counter.most_common()
    ],
    "rounds": rounds,
}

OUT.write_text(json.dumps(coverage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("WROTE", OUT)
print("VERDICT", coverage["verdict"])
print("SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())
