import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v4"
OUT_DIR = CAP / "forensic_contract_fix_v1"
OUT = OUT_DIR / "export_2b912_audit_bundle.txt"
SERVER_LOGS = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\logs")
DLL_PATH = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\CsBotManager.dll")

parts = []

def slice_lines(rel_path: str, start: int, end: int, label: str):
    lines = (BASE / rel_path).read_text(encoding="utf-8", errors="replace").splitlines()
    parts.append(f"\n--- {label} ({rel_path}:{start}-{end}) ---")
    for i in range(max(1, start), min(len(lines), end) + 1):
        parts.append(f"{i}: {lines[i-1]}")

# 1. TeamOpeningRouteScheduler.cs
parts.append("=" * 80)
parts.append("1. TeamOpeningRouteScheduler.cs")
parts.append("=" * 80)
slice_lines("src/CsBotManager/TeamOpeningRouteScheduler.cs", 7, 75, "Enums e OpeningAssignmentTerminalRecord")

# 2. CsBotManagerPlugin.cs
parts.append("\n" + "=" * 80)
parts.append("2. CsBotManagerPlugin.cs")
parts.append("=" * 80)
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2387, 2508, "Follower release, expiração e lifecycle")
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2730, 2945, "Schedule, emission de SCHEDULED/STATE_CHANGED/TERMINAL e EmitAssignmentLifecycleRecord")

# 3. OpeningRouteCanaryController.cs
parts.append("\n" + "=" * 80)
parts.append("3. OpeningRouteCanaryController.cs")
parts.append("=" * 80)
slice_lines("src/CsBotManager/OpeningRouteCanaryController.cs", 215, 250, "ActiveCanarySession")
slice_lines("src/CsBotManager/OpeningRouteCanaryController.cs", 820, 895, "Criação session_id e CANARY_SESSION_STARTED")
slice_lines("src/CsBotManager/OpeningRouteCanaryController.cs", 1775, 1900, "FinishAndRecord e RecordTick")

# 4. Logger real de assignment lifecycle
parts.append("\n" + "=" * 80)
parts.append("4. Logger real de assignment lifecycle")
parts.append("=" * 80)
parts.append("Caminho: Path.Combine(ModuleDirectory, \"logs\", \"opening_assignment_lifecycle.jsonl\")")
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2940, 2960, "EmitAssignmentLifecycleRecord")

# 5. finalize_2b912_deliverables.py (não existe; incluir finalize_2b911_deliverables.py)
parts.append("\n" + "=" * 80)
parts.append("5. finalize_2b912_deliverables.py (NÃO EXISTE; incluindo finalize_2b911_deliverables.py)")
parts.append("=" * 80)
parts.append((BASE / "tools/phase3a_training/finalize_2b911_deliverables.py").read_text(encoding="utf-8"))

# 6. Trecho do auditor
parts.append("\n" + "=" * 80)
parts.append("6. Auditor offline v3 (audit_2b912_offline_v3.py)")
parts.append("=" * 80)
parts.append((BASE / "tools/phase3a_training/audit_2b912_offline_v3.py").read_text(encoding="utf-8"))

# 7. opening_assignment_lifecycle.jsonl
parts.append("\n" + "=" * 80)
parts.append("7. opening_assignment_lifecycle.jsonl (servidor, rodada curta mais recente)")
parts.append("=" * 80)
src_life = SERVER_LOGS / "opening_assignment_lifecycle.jsonl"
parts.append(src_life.read_text(encoding="utf-8", errors="replace") if src_life.exists() else "[NOT_FOUND]")

# 8. opening_canary_telemetry.jsonl filtrado para r1_T_s9_1474
parts.append("\n" + "=" * 80)
parts.append("8. opening_canary_telemetry.jsonl (sessão r1_T_s9_1474)")
parts.append("=" * 80)
telem_v4 = CAP / "opening_route_telemetry.jsonl"
r1_lines = [l for l in telem_v4.read_text(encoding="utf-8", errors="replace").splitlines() if "r1_T_s9_1474" in l]
parts.append(f"[INFO] Total linhas r1_T_s9_1474 em v4: {len(r1_lines)}")
parts.extend(r1_lines)

# 9. short_assignment_telemetry.jsonl
parts.append("\n" + "=" * 80)
parts.append("9. short_assignment_telemetry.jsonl")
parts.append("=" * 80)
dst_life = OUT_DIR / "short_assignment_telemetry.jsonl"
parts.append(dst_life.read_text(encoding="utf-8", errors="replace") if dst_life.exists() else "[NOT_FOUND]")

# 10. Metadados
parts.append("\n" + "=" * 80)
parts.append("10. Metadados da execução")
parts.append("=" * 80)
dll_sha = hashlib.sha256(DLL_PATH.read_bytes()).hexdigest() if DLL_PATH.exists() else "MISSING"
parts.append(f"DLL SHA-256: {dll_sha}")
parts.append(f"opening_assignment_lifecycle.jsonl mtime: {datetime.fromtimestamp(src_life.stat().st_mtime, timezone.utc).isoformat() if src_life.exists() else 'MISSING'}")
parts.append(f"short_assignment_telemetry.jsonl mtime: {datetime.fromtimestamp(dst_life.stat().st_mtime, timezone.utc).isoformat() if dst_life.exists() else 'MISSING'}")
parts.append(f"Diretório origem logs: {SERVER_LOGS}")

OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print("WROTE", OUT, "bytes=", OUT.stat().st_size)
