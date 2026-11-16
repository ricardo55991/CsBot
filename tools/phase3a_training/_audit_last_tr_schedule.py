import json

SCHED = r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs\full_team_departure_rounds.jsonl"

entries = []
with open(SCHED, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass

# Print last 12 entries with full TR assignment detail
print("=== LAST 12 SCHEDULE ENTRIES ===")
for e in entries[-12:]:
    assigns = e.get("assignments", [])
    tr = sum(1 for a in assigns if (a.get("Destination") or "").startswith("tr_"))
    ct = sum(1 for a in assigns if (a.get("Destination") or "").startswith("ct_"))
    team = "TR" if tr > 0 and ct == 0 else ("CT" if ct > 0 and tr == 0 else "?")
    print("\nround=%s team=%s canary=%s utility=%s" % (e.get("round"), team, e.get("canary_controlled_count"), e.get("utility_observed_count")))
    for a in assigns:
        mode = "CANARY" if a.get("ControlMode") == 0 else "UTILITY"
        print("  slot=%s role=%s dest=%s mode=%s fallback=%s" % (
            a.get("BotSlot"), a.get("Role"), a.get("Destination"), mode, a.get("FallbackReason")))
