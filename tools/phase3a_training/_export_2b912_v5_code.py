import json
import re
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v5"
OUT = CAP / "export_2b912_v5_code_and_round5.txt"

parts = []

def slice_lines(rel_path: str, start: int, end: int, label: str):
    lines = (BASE / rel_path).read_text(encoding="utf-8", errors="replace").splitlines()
    parts.append(f"\n--- {label} ({rel_path}:{start}-{end}) ---")
    for i in range(max(1, start), min(len(lines), end) + 1):
        parts.append(f"{i}: {lines[i-1]}")

def grep_lines(rel_path: str, pattern: str, label: str):
    lines = (BASE / rel_path).read_text(encoding="utf-8", errors="replace").splitlines()
    rx = re.compile(pattern)
    parts.append(f"\n--- {label} ({rel_path} /{pattern}/) ---")
    for i, l in enumerate(lines, 1):
        if rx.search(l):
            parts.append(f"{i}: {l}")

# 1. CsBotManagerPlugin.cs: ctEnabled .. TryCreateTeamOpeningSchedule
parts.append("=" * 80)
parts.append("1. CsBotManagerPlugin.cs: ctEnabled .. TryCreateTeamOpeningSchedule")
parts.append("=" * 80)
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2215, 2410, "UpdateOpeningRouteControlAndShadowTick")

# 2. TryCreateTeamOpeningSchedule completo
parts.append("\n" + "=" * 80)
parts.append("2. TryCreateTeamOpeningSchedule completo")
parts.append("=" * 80)
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2770, 3035, "TryCreateTeamOpeningSchedule")

# 3. OpeningRouteCanaryController.cs
parts.append("\n" + "=" * 80)
parts.append("3. OpeningRouteCanaryController.cs")
parts.append("=" * 80)
slice_lines("src/CsBotManager/OpeningRouteCanaryController.cs", 595, 675, "HasStartedRound, HasStartedTeamRound, MarkTeamRoundStarted, GetSessionsForRoundAndTeam")
slice_lines("src/CsBotManager/OpeningRouteCanaryController.cs", 965, 1005, "FinalizeActiveSession, FinalizeAllOpenSessions")

# 4 & 5. Ocorrências e limpeza das estruturas
parts.append("\n" + "=" * 80)
parts.append("4 & 5. Ocorrências e limpeza das estruturas")
parts.append("=" * 80)
pat = r"_startedTeamRounds|_fullTeamScheduleByRound|_pendingCanaryFollowers|_terminatedAssignments|OnRoundStart|OnFreezeTimeEnd|OnRoundEnd|Unload"
grep_lines("src/CsBotManager/CsBotManagerPlugin.cs", pat, "CsBotManagerPlugin.cs")
grep_lines("src/CsBotManager/OpeningRouteCanaryController.cs", pat, "OpeningRouteCanaryController.cs")

# 6. run_2b98_combined_5v5_debug.py (detecção, flush, encerramento)
parts.append("\n" + "=" * 80)
parts.append("6. run_2b98_combined_5v5_debug.py (detecção, flush, encerramento)")
parts.append("=" * 80)
slice_lines("tools/phase3a_training/run_2b98_combined_5v5_debug.py", 60, 125, "run_combined_5v5_live")

# 7. _debugTargetRounds, _debugRoundsSealed, match_completed.flag, !debug 5
parts.append("\n" + "=" * 80)
parts.append("7. CsBotManagerPlugin.cs: _debugTargetRounds, _debugRoundsSealed, match_completed.flag, !debug")
parts.append("=" * 80)
grep_lines("src/CsBotManager/CsBotManagerPlugin.cs", r"_debugTargetRounds|_debugRoundsSealed|match_completed|!debug", "Debug flags")

# 8. Positioning Shadow
parts.append("\n" + "=" * 80)
parts.append("8. Positioning Shadow (utility_state, utility_sector, utility_spot, neural_sector, neural_spot)")
parts.append("=" * 80)
grep_lines("src/CsBotManager/CsBotManagerPlugin.cs", r"utility_state|utility_sector|utility_spot|RunPositioningShadowBatch|BuildShadow", "Positioning Shadow")

# 9. Resumo determinístico do round 5
parts.append("\n" + "=" * 80)
parts.append("9. Resumo determinístico do round 5 (v5)")
parts.append("=" * 80)
life_r5 = [json.loads(l) for l in (CAP / "opening_assignment_lifecycle.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
r5_tr_sched = [r for r in life_r5 if r.get("RoundId") == 5 and r.get("Team") == "TR" and r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED"]
r5_tr_ticks = sorted({r.get("ScheduledTick") for r in r5_tr_sched})
telem_r5 = [json.loads(l) for l in (CAP / "opening_route_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
r5_tr_sess = {r.get("session_id") for r in telem_r5 if r.get("round") == 5 and str(r.get("team", "")).upper() in ("T", "TR") and r.get("session_id")}

parts.append(f"Round 5 TR SCHEDULED events: {len(r5_tr_sched)}")
parts.append(f"Primeiro tick de schedule TR (round 5): {r5_tr_ticks[0] if r5_tr_ticks else None}")
parts.append(f"Último tick de schedule TR (round 5): {r5_tr_ticks[-1] if r5_tr_ticks else None}")
parts.append(f"Quantidade de sessões TR distintas (round 5): {len(r5_tr_sess)} ({sorted(r5_tr_sess)})")

OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print("WROTE", OUT, "bytes=", OUT.stat().st_size)
