import json, collections, sys

F = r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs\opening_canary_telemetry.jsonl"

recs = []
with open(F, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except Exception:
            pass

print("TOTAL_RECORDS=%d" % len(recs))

# distinct bots per (round, team)
g = collections.defaultdict(lambda: collections.defaultdict(set))
for r in recs:
    g[r.get("round")][r.get("team")].add(r.get("player_pseudonym"))

for rnd in sorted(g, key=lambda x: (x if x is not None else -1)):
    for team in sorted(g[rnd]):
        print("round=%s team=%s distinct_bots=%d bots=%s" % (
            rnd, team, len(g[rnd][team]), sorted(g[rnd][team])))

# terminal states per (round, team, bot) last record
term = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(str)))
for r in recs:
    key = (r.get("round"), r.get("team"), r.get("player_pseudonym"))
    term[r.get("round")][r.get("team")][r.get("player_pseudonym")] = (
        r.get("executor_state") or r.get("arrival_status") or "")

print("\n=== last executor_state / arrival_status per bot ===")
for rnd in sorted(term, key=lambda x: (x if x is not None else -1)):
    for team in sorted(term[rnd]):
        for bot in sorted(term[rnd][team]):
            print("round=%s team=%s bot=%s last=%s" % (rnd, team, bot, term[rnd][team][bot]))

# field names
fields = set()
for r in recs:
    fields.update(r.keys())
print("\nFIELDS=%s" % sorted(fields))

# executor_state / arrival_status value distribution
es = collections.Counter(r.get("executor_state") for r in recs)
ar = collections.Counter(r.get("arrival_status") for r in recs)
print("\nexecutor_state=%s" % dict(es))
print("arrival_status=%s" % dict(ar))
