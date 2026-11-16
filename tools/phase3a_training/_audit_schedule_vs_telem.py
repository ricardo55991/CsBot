import json, collections

SCHED = r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs\full_team_departure_rounds.jsonl"
TELEM = r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs\opening_canary_telemetry.jsonl"

# Parse schedule log (cumulative across runs)
sched_entries = []
with open(SCHED, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            sched_entries.append(json.loads(line))
        except Exception:
            pass

print("TOTAL_SCHED_ENTRIES=%d" % len(sched_entries))

# team inference: use Destination prefix (tr_ / ct_ / a_/b_/mid_ ambiguous)
def infer_team(assigns):
    tr = sum(1 for a in assigns if (a.get("Destination") or "").startswith("tr_"))
    ct = sum(1 for a in assigns if (a.get("Destination") or "").startswith("ct_"))
    if tr > 0 and ct == 0:
        return "TR"
    if ct > 0 and tr == 0:
        return "CT"
    return "?"

print("\n=== schedule entries (round, team, canary, utility, total) ===")
for e in sched_entries:
    assigns = e.get("assignments", [])
    team = infer_team(assigns)
    print("round=%s team=%s canary=%s utility=%s total=%s" % (
        e.get("round"), team, e.get("canary_controlled_count"),
        e.get("utility_observed_count"), len(assigns)))

# Telemetry distinct bots per round/team
tg = collections.defaultdict(lambda: collections.defaultdict(set))
with open(TELEM, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        tg[r.get("round")][r.get("team")].add(r.get("player_pseudonym"))

print("\n=== telemetry distinct bots ===")
for rnd in sorted(tg, key=lambda x: (x if x is not None else -1)):
    for team in sorted(tg[rnd]):
        print("round=%s team=%s distinct=%d" % (rnd, team, len(tg[rnd][team])))
