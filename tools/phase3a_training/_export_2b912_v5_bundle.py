import json
from collections import Counter
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v5"
OUT = CAP / "export_2b912_v5_forensic_bundle.txt"

parts = []

def slice_lines(rel_path: str, start: int, end: int, label: str):
    lines = (BASE / rel_path).read_text(encoding="utf-8", errors="replace").splitlines()
    parts.append(f"\n--- {label} ({rel_path}:{start}-{end}) ---")
    for i in range(max(1, start), min(len(lines), end) + 1):
        parts.append(f"{i}: {lines[i-1]}")

# 1. audit_2b912_final_5round_capture.py completo
parts.append("=" * 80)
parts.append("1. audit_2b912_final_5round_capture.py COMPLETO")
parts.append("=" * 80)
parts.append((BASE / "tools/phase3a_training/audit_2b912_final_5round_capture.py").read_text(encoding="utf-8"))

# 2-4. Método C# que emite OPENING_ASSIGNMENT_SCHEDULED, call sites e trava
parts.append("\n" + "=" * 80)
parts.append("2-4. C#: Emissão de OPENING_ASSIGNMENT_SCHEDULED, call sites e trava")
parts.append("=" * 80)
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2895, 2965, "TryCreateTeamOpeningSchedule -> OPENING_ASSIGNMENT_SCHEDULED")
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2390, 2410, "Call sites de TryCreateTeamOpeningSchedule")
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 3165, 3270, "Trava _terminatedAssignments e EmitAssignmentLifecycleRecord")

# 5. opening_assignment_lifecycle.jsonl filtrado
parts.append("\n" + "=" * 80)
parts.append("5. opening_assignment_lifecycle.jsonl")
parts.append("=" * 80)
life_lines = [l for l in (CAP / "opening_assignment_lifecycle.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
life_objs = [json.loads(l) for l in life_lines]
sched_counts = Counter(r.get("AssignmentId") for r in life_objs if r.get("EventType") == "OPENING_ASSIGNMENT_SCHEDULED")
parts.append(f"Contagem OPENING_ASSIGNMENT_SCHEDULED por AssignmentId: {dict(sched_counts.most_common())}")
if sched_counts:
    top_aid, top_cnt = sched_counts.most_common(1)[0]
    parts.append(f"\n--- Todas as linhas do AssignmentId mais repetido ({top_aid}, count={top_cnt}) ---")
    for l in life_lines:
        if f'"{top_aid}"' in l:
            parts.append(l)
parts.append("\n--- Primeiras 100 linhas ---")
parts.extend(life_lines[:100])
parts.append("\n--- Últimas 100 linhas ---")
parts.extend(life_lines[-100:])

# 6-7. tr_route_metrics.json e ct_route_metrics.json
parts.append("\n" + "=" * 80)
parts.append("6. tr_route_metrics.json atual")
parts.append("=" * 80)
parts.append((CAP / "tr_route_metrics.json").read_text(encoding="utf-8"))

parts.append("\n" + "=" * 80)
parts.append("7. ct_route_metrics.json atual")
parts.append("=" * 80)
parts.append((CAP / "ct_route_metrics.json").read_text(encoding="utf-8"))

# 8. Linhas CANARY_SESSION_STARTED e terminais de todas as sessões TR
parts.append("\n" + "=" * 80)
parts.append("8. Linhas CANARY_SESSION_STARTED e terminais de todas as sessões TR")
parts.append("=" * 80)
for l in (CAP / "opening_route_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
    if not l.strip():
        continue
    try:
        r = json.loads(l)
    except Exception:
        continue
    if str(r.get("team", "")).upper() in ("T", "TR") and r.get("event_type") in ("CANARY_SESSION_STARTED", "COMPLETED", "INTERRUPTED", "ABORTED"):
        parts.append(l)

# 9. positioning_agreement_metrics.json
parts.append("\n" + "=" * 80)
parts.append("9. positioning_agreement_metrics.json")
parts.append("=" * 80)
parts.append((CAP / "positioning_agreement_metrics.json").read_text(encoding="utf-8"))

# 10. Trecho do auditor
parts.append("\n" + "=" * 80)
parts.append("10. Trecho do auditor (CT/TR, arrivals, ON_TIME, sector_agreement)")
parts.append("=" * 80)
slice_lines("tools/phase3a_training/audit_2b912_final_5round_capture.py", 125, 225, "Auditor")

# 11. Definições de setor
parts.append("\n" + "=" * 80)
parts.append("11. Definições de setor (Utility AI vs Transformer vs Auditor)")
parts.append("=" * 80)
parts.append("Auditor compara diretamente sr.get('utility_sector') == sr.get('neural_sector') em positioning_shadow_telemetry.jsonl.")
shadow_lines = (CAP / "positioning_shadow_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines()[:5]
parts.append("Amostra de 5 linhas de positioning_shadow_telemetry.jsonl:")
parts.extend(shadow_lines)

# 12. findings.json e representative_failures.json
parts.append("\n" + "=" * 80)
parts.append("12. findings.json e representative_failures.json")
parts.append("=" * 80)
parts.append((CAP / "findings.json").read_text(encoding="utf-8"))
parts.append((CAP / "representative_failures.json").read_text(encoding="utf-8"))

OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print("WROTE", OUT, "bytes=", OUT.stat().st_size)
