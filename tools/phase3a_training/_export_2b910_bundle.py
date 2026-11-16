import json
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v4"
OUT = CAP / "export_2b910_forensic_bundle.txt"

parts = []

# 1. opening_route_telemetry.jsonl filtrado
parts.append("=" * 80)
parts.append("1. opening_route_telemetry.jsonl (FILTRADO)")
parts.append("=" * 80)

elig = json.loads((CAP / "eligibility_accounting.json").read_text(encoding="utf-8"))
tr_missing = {
    (r["round_id"], r["slot_pseudonimizado"])
    for r in elig.get("rows", [])
    if r.get("team") == "TR" and r.get("route_certified") and not r.get("session_started")
}
parts.append(f"[INFO] 5 assignments TR certificados sem sessão: {sorted(tr_missing)}")

telem_lines = []
for line in (CAP / "opening_route_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    rnd = r.get("round")
    dest = r.get("intended_destination")
    pseudo = r.get("player_pseudonym")
    team = "TR" if str(r.get("team", "")).upper() in ("T", "TR") else "CT"
    if (rnd == 1 and dest in ("mid_underground_sub", "b_short_pillar_hold_apps")) or \
       (rnd == 3 and dest == "b_short_pillar_hold_apps") or \
       (team == "TR" and (rnd, pseudo) in tr_missing):
        telem_lines.append(line)

parts.append(f"[INFO] Total de linhas filtradas: {len(telem_lines)}")
parts.extend(telem_lines)

# 2-8. JSONs
jsons = [
    ("2. queue_and_portal_metrics.json", "queue_and_portal_metrics.json"),
    ("3. weapon_readiness_metrics.json", "weapon_readiness_metrics.json"),
    ("4. session_event_accounting.json", "session_event_accounting.json"),
    ("5. tactical_interruptions.json", "tactical_interruptions.json"),
    ("6. positioning_agreement_metrics.json", "positioning_agreement_metrics.json"),
    ("7. representative_failures.json", "representative_failures.json"),
    ("8. findings.json", "findings.json"),
]
for title, fname in jsons:
    parts.append("\n" + "=" * 80)
    parts.append(title)
    parts.append("=" * 80)
    parts.append((CAP / fname).read_text(encoding="utf-8"))

# 9. Métodos atuais
parts.append("\n" + "=" * 80)
parts.append("9. MÉTODOS ATUAIS")
parts.append("=" * 80)

def slice_lines(rel_path: str, start: int, end: int, label: str):
    lines = (BASE / rel_path).read_text(encoding="utf-8", errors="replace").splitlines()
    parts.append(f"\n--- {label} ({rel_path}:{start}-{end}) ---")
    for i in range(max(1, start), min(len(lines), end) + 1):
        parts.append(f"{i}: {lines[i-1]}")

slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2262, 2272, "Janela de abertura (isOpeningStartWindow)")
slice_lines("src/CsBotManager/CsBotManagerPlugin.cs", 2387, 2436, "Criação tardia de followers, promoção por predecessor removido e lease do follower")
slice_lines("src/CsBotManager/OpeningRouteCanaryController.cs", 1800, 1810, "Emissão de weapon_ready_before_contact")
slice_lines("tools/phase3a_training/audit_2b910_combined_5round_capture.py", 270, 290, "Cálculo de weapon_ready_before_contact_pct")

OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print("WROTE", OUT, "bytes=", OUT.stat().st_size)
