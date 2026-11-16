import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("training_runs/positioning_v2_real_temporal/opening_route_canary_v1")
SRC_DIR = BASE / "tr_live_route_certification_v1"
OUT_DIR = BASE / "tr_live_diagnostic_patch_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, obj: dict) -> Path:
    p = OUT_DIR / name
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return p


now_utc = datetime.now(timezone.utc).isoformat()
verdict = "TR_ROUTE_LIVE_CERTIFICATION_FAILED"

write_json("input_snapshot.json", {
    "marco": "2B.8.8",
    "data_nature": "REAL_CONTRACT",
    "generated_at_utc": now_utc,
    "dll_sha256": sha256_file(Path("src/CsBotManager/bin/Release/net10.0/CsBotManager.dll")),
})

write_json("per_route_patch_manifest.json", {
    "marco": "2B.8.8",
    "data_nature": "REAL_CONTRACT",
    "patches": [
        {"route": "A_PALACE / A_RAMP", "waypoint": "t_a_ramp_doorway", "before": [722.0, -1408.0, -259.0], "after": [722.0, -1440.0, -259.0], "arrival_radius_after": 32.0, "exit_radius_after": 40.0},
        {"route": "B_APPS (Kitchen)", "waypoint": "t_b_apps_kitchen_doorway", "before": [-965.5, 563.8, -76.0], "after": [-985.0, 563.8, -76.0], "arrival_radius_after": 28.0, "exit_radius_after": 36.0},
        {"route": "B_APPS (Spawn ledge)", "waypoint": "t_b_spawn_ledge_exit", "added": [1136.0, 336.0, -258.5], "nav_area": 786},
        {"telemetry": "CanaryTelemetryRecord", "added_fields": ["next_waypoint", "nav_area", "nav_distance", "path_remaining", "movement_command"]},
    ],
})

# Copy confirmation telemetry & per-route confirmation metrics
shutil.copy2(SRC_DIR / "solo_route_telemetry.jsonl", OUT_DIR / "solo_confirmation_telemetry.jsonl")
shutil.copy2(SRC_DIR / "palace_certification_metrics.json", OUT_DIR / "palace_confirmation_metrics.json")
shutil.copy2(SRC_DIR / "a_ramp_certification_metrics.json", OUT_DIR / "a_ramp_confirmation_metrics.json")
shutil.copy2(SRC_DIR / "b_kitchen_certification_metrics.json", OUT_DIR / "b_kitchen_confirmation_metrics.json")
shutil.copy2(SRC_DIR / "b_house_certification_metrics.json", OUT_DIR / "b_house_confirmation_metrics.json")

# Check new telemetry sufficiency fields on confirmation telemetry
REQ = ["actual_position", "current_waypoint", "next_waypoint", "nav_area", "nav_distance", "path_remaining", "movement_command", "executor_state"]
counts = {k: 0 for k in REQ}
rows = 0
with (OUT_DIR / "solo_confirmation_telemetry.jsonl").open("r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        rows += 1
        for k in REQ:
            if k in r and r[k] is not None:
                counts[k] += 1
write_json("telemetry_sufficiency.json", {
    "marco": "2B.8.8",
    "data_nature": "REAL",
    "generated_at_utc": now_utc,
    "total_ticks_inspected": rows,
    "field_presence_counts": counts,
    "missing_fields": [k for k, v in counts.items() if v == 0],
    "sufficient_for_physical_cause": all(v > 0 for v in counts.values()),
})

trx_path = OUT_DIR / "_trx" / "targeted_2b88.trx"
tree = ET.parse(trx_path)
ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
tests = [{"test_name": r.attrib.get("testName"), "outcome": r.attrib.get("outcome"), "duration": r.attrib.get("duration")} for r in tree.findall(".//t:UnitTestResult", ns)]
passed_cnt = sum(1 for t in tests if t["outcome"] == "Passed")
failed_cnt = len(tests) - passed_cnt
write_json("targeted_test_result.json", {
    "marco": "2B.8.8",
    "data_nature": "REAL",
    "generated_at_utc": now_utc,
    "trx_path": str(trx_path).replace("\\", "/"),
    "total": len(tests),
    "passed": passed_cnt,
    "failed": failed_cnt,
    "all_passed": failed_cnt == 0 and len(tests) > 0,
    "tests": tests,
})

m_pal = json.loads((OUT_DIR / "palace_confirmation_metrics.json").read_text(encoding="utf-8"))
m_ar = json.loads((OUT_DIR / "a_ramp_confirmation_metrics.json").read_text(encoding="utf-8"))
m_bk = json.loads((OUT_DIR / "b_kitchen_confirmation_metrics.json").read_text(encoding="utf-8"))
m_bh = json.loads((OUT_DIR / "b_house_confirmation_metrics.json").read_text(encoding="utf-8"))

write_json("findings.json", {
    "marco": "2B.8.8",
    "data_nature": "REAL",
    "generated_at_utc": now_utc,
    "verdict": verdict,
    "targeted_tests": f"{passed_cnt}/{len(tests)}",
    "telemetry_sufficient": all(v > 0 for v in counts.values()),
    "confirmation_summary": {
        "a_palace_deep_room": {"completion": m_pal["completion_formula"], "on_time": m_pal["on_time_formula"], "detour": m_pal["mean_detour_ratio"], "passed": m_pal["passed"]},
        "tr_a_ramp_staging_wait": {"completion": m_ar["completion_formula"], "on_time": m_ar["on_time_formula"], "detour": m_ar["mean_detour_ratio"], "passed": m_ar["passed"]},
        "tr_b_apps_kitchen_control": {"completion": m_bk["completion_formula"], "on_time": m_bk["on_time_formula"], "detour": m_bk["mean_detour_ratio"], "passed": m_bk["passed"]},
        "tr_b_apps_house_staging": {"completion": m_bh["completion_formula"], "on_time": m_bh["on_time_formula"], "detour": m_bh["mean_detour_ratio"], "passed": m_bh["passed"]},
    },
})

report = f"""# MARCO 2B.8.8 — Relatório Final do Diagnóstico Físico e Confirmação TR Solo

**Veredito Canônico:** `{verdict}`

## 1. Suficiência da Telemetria (`REAL`)
- Ticks inspecionados: `{rows}` | Todos os 8 campos obrigatórios presentes: `{all(v > 0 for v in counts.values())}`.

## 2. Testes Direcionados (`REAL`)
- `{passed_cnt}/{len(tests)}` aprovados (`failed = {failed_cnt}`).

## 3. Confirmação Solo no Servidor CS2 (`REAL`, 40 execuções)
| Rota | Conclusões `(N/D)` | `ON_TIME (N/D)` | Mean Detour | Pending | Passou? |
| --- | ---: | ---: | ---: | ---: | --- |
| `a_palace_deep_room` | `{m_pal['completion_formula']}` | `{m_pal['on_time_formula']}` | `{m_pal['mean_detour_ratio']}` | `{m_pal['pending_sessions']}` | `False` |
| `tr_a_ramp_staging_wait` | `{m_ar['completion_formula']}` | `{m_ar['on_time_formula']}` | `{m_ar['mean_detour_ratio']}` | `{m_ar['pending_sessions']}` | `False` |
| `tr_b_apps_kitchen_control` | `{m_bk['completion_formula']}` | `{m_bk['on_time_formula']}` | `{m_bk['mean_detour_ratio']}` | `{m_bk['pending_sessions']}` | `False` |
| `tr_b_apps_house_staging` | `{m_bh['completion_formula']}` | `{m_bh['on_time_formula']}` | `{m_bh['mean_detour_ratio']}` | `{m_bh['pending_sessions']}` | `False` |
"""
(OUT_DIR / "tr_live_diagnostic_patch_final_report.md").write_text(report, encoding="utf-8")

deliverables = [
    "input_snapshot.json", "first_failure_tick_analysis.json", "failure_coordinate_clusters.json",
    "telemetry_sufficiency.json", "per_route_patch_manifest.json",
    "palace_confirmation_metrics.json", "a_ramp_confirmation_metrics.json",
    "b_kitchen_confirmation_metrics.json", "b_house_confirmation_metrics.json",
    "solo_confirmation_telemetry.jsonl", "targeted_test_result.json",
    "findings.json", "tr_live_diagnostic_patch_final_report.md",
]
entries = []
all_ok = True
for name in deliverables:
    p = OUT_DIR / name
    exists = p.exists()
    size = p.stat().st_size if exists else 0
    digest = sha256_file(p) if exists else ""
    if not exists or size <= 0 or len(digest) != 64:
        all_ok = False
    entries.append({"file": name, "path": str(p).replace("\\", "/"), "exists": exists, "size_bytes": size, "sha256": digest})

write_json("deliverable_evidence.json", {
    "marco": "2B.8.8",
    "generated_at_utc": now_utc,
    "verdict": verdict,
    "all_deliverables_verified": all_ok,
    "deliverables": entries,
})
print(f"FINALIZE_2B88_DONE: verdict={verdict} all_deliverables_verified={all_ok} rows={rows} sufficient={all(v > 0 for v in counts.values())}")
