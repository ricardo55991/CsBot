import json
from collections import defaultdict
from pathlib import Path

BASE = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAP = BASE / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "combined_5v5_debug_capture_v6"
OUT = CAP / "export_2b912_v6_analysis_bundle.txt"

parts = []

def add_file(title: str, fname: str):
    parts.append("\n" + "=" * 80)
    parts.append(title)
    parts.append("=" * 80)
    p = CAP / fname
    parts.append(p.read_text(encoding="utf-8", errors="replace") if p.exists() else "[NOT_FOUND]")

# 1-9
add_file("1. combined_5v5_debug_final_report.md", "combined_5v5_debug_final_report.md")
add_file("2. findings.json", "findings.json")
add_file("3. representative_failures.json", "representative_failures.json")
add_file("4. positioning_agreement_metrics.json", "positioning_agreement_metrics.json")
add_file("5. tr_failure_analysis.json", "tr_failure_analysis.json")
add_file("6. abort_root_causes.json", "abort_root_causes.json")
add_file("7. tactical_interruptions.json", "tactical_interruptions.json")
add_file("8. c4_runtime_metrics.json", "c4_runtime_metrics.json")
add_file("9. queue_and_portal_metrics.json", "queue_and_portal_metrics.json")

# Carregar JSONLs
debug_recs = [json.loads(l) for l in (CAP / "debug_match.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
shadow_recs = [json.loads(l) for l in (CAP / "positioning_shadow_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
opening_recs = [json.loads(l) for l in (CAP / "opening_route_telemetry.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]

aborts_json = json.loads((CAP / "abort_root_causes.json").read_text(encoding="utf-8"))
abort_sids = {a["session_id"] for a in aborts_json.get("aborts", [])}
readiness_json = json.loads((CAP / "weapon_readiness_metrics.json").read_text(encoding="utf-8"))
insuff_sids = {s["session_id"] for s in readiness_json.get("sessions", []) if s.get("classification") == "INSUFFICIENT_TELEMETRY"}
q_to_sids = {r.get("session_id") for r in opening_recs if r.get("fallback_reason") == "CORRIDOR_QUEUE_TIMEOUT" and r.get("session_id")}

# 10. debug_match.jsonl filtrado (divergências alta confiança, mudanças de setor, janelas +-100 ticks)
parts.append("\n" + "=" * 80)
parts.append("10. debug_match.jsonl (FILTRADO: divergências alta confiança + mudanças de setor + janelas +-100 ticks)")
parts.append("=" * 80)

event_windows = []
prev_sector = {}
for r in debug_recs:
    rnd = r.get("round")
    tick = r.get("tick") or 0
    slot = r.get("player_pseudonym")
    confs = r.get("confidence_by_head") or []
    sec_conf = confs[1] if len(confs) > 1 else 0.0
    u_sec = r.get("utility_sector")
    n_sec = r.get("neural_sector")
    avail = r.get("utility_decision_available")
    is_hi_div = avail and u_sec not in (None, "", "UNKNOWN") and n_sec not in (None, "", "UNKNOWN") and u_sec != n_sec and sec_conf >= 0.70
    sec_changed = (rnd, slot) in prev_sector and prev_sector[(rnd, slot)] != u_sec
    prev_sector[(rnd, slot)] = u_sec
    if is_hi_div or sec_changed:
        event_windows.append((rnd, slot, tick - 100, tick + 100))

# Mesclar intervalos para não explodir
selected_debug = []
for r in debug_recs:
    rnd = r.get("round")
    tick = r.get("tick") or 0
    slot = r.get("player_pseudonym")
    if any(w[0] == rnd and w[1] == slot and w[2] <= tick <= w[3] for w in event_windows[:40]):
        selected_debug.append(json.dumps(r))
parts.append(f"[INFO] Janelas selecionadas: {len(event_windows)} (amostrando primeiras 40 janelas -> {len(selected_debug)} linhas)")
parts.extend(selected_debug[:600])

# 11. positioning_shadow_telemetry.jsonl filtrado
parts.append("\n" + "=" * 80)
parts.append("11. positioning_shadow_telemetry.jsonl (FILTRADO)")
parts.append("=" * 80)
hi_disagree = []
spot_flips = []
agree_sample = []
prev_spot = {}
for r in shadow_recs:
    confs = r.get("confidence_by_head") or []
    sec_conf = confs[1] if len(confs) > 1 else 0.0
    avail = r.get("utility_decision_available")
    u_sec = r.get("utility_sector")
    n_sec = r.get("neural_sector")
    n_spot = r.get("neural_spot")
    key = (r.get("round_id"), r.get("player_slot"))
    if key in prev_spot and prev_spot[key] != n_spot and len(spot_flips) < 50:
        spot_flips.append(json.dumps(r))
    prev_spot[key] = n_spot
    if avail and u_sec != "UNKNOWN" and n_sec != "UNKNOWN":
        if u_sec != n_sec and sec_conf >= 0.70 and len(hi_disagree) < 100:
            hi_disagree.append(json.dumps(r))
        elif u_sec == n_sec and len(agree_sample) < 30:
            agree_sample.append(json.dumps(r))

parts.append(f"--- Discordâncias alta confiança (>=0.70): {len(hi_disagree)} ---")
parts.extend(hi_disagree)
parts.append(f"\n--- Mudanças de spot (amostra): {len(spot_flips)} ---")
parts.extend(spot_flips)
parts.append(f"\n--- Concordâncias corretas (amostra): {len(agree_sample)} ---")
parts.extend(agree_sample)

# 12. opening_route_telemetry.jsonl filtrado
parts.append("\n" + "=" * 80)
parts.append("12. opening_route_telemetry.jsonl (abortos CT/TR, timeout de fila, readiness insuficiente)")
parts.append("=" * 80)
target_sids = abort_sids | q_to_sids | insuff_sids
parts.append(f"[INFO] abort_sids={sorted(abort_sids)} q_to_sids={sorted(q_to_sids)} insuff_sids={sorted(insuff_sids)}")
filtered_open = [json.dumps(r) for r in opening_recs if r.get("session_id") in target_sids]
parts.append(f"[INFO] Linhas filtradas: {len(filtered_open)}")
parts.extend(filtered_open)

# 13. Mapeamentos
parts.append("\n" + "=" * 80)
parts.append("13. Mapeamentos usados na auditoria (PositioningTransformerContract.cs)")
parts.append("=" * 80)
contract_lines = (BASE / "src/CsBotManager/PositioningTransformerContract.cs").read_text(encoding="utf-8", errors="replace").splitlines()
for i in range(1, min(140, len(contract_lines) + 1)):
    parts.append(f"{i}: {contract_lines[i-1]}")

OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print("WROTE", OUT, "bytes=", OUT.stat().st_size)
