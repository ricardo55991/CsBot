import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("training_runs/positioning_v2_real_temporal/opening_route_canary_v1/tr_live_route_certification_v1")
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
    "marco": "2B.8.7",
    "data_nature": "REAL_CONTRACT",
    "generated_at_utc": now_utc,
    "dll_sha256": sha256_file(Path("src/CsBotManager/bin/Release/net10.0/CsBotManager.dll")),
})

write_json("certification_contract.json", {
    "marco": "2B.8.7",
    "data_nature": "REAL_CONTRACT",
    "environment": "de_mirage, 1 TR bot, 0 CT bots, mp_ignore_round_win_conditions=1",
    "gates": {"completion_min": "9/10", "on_time_min": "8/10", "mean_detour_max": 1.20, "pending": 0, "teammate_blocks": 0},
})

write_json("solo_route_matrix.json", {
    "marco": "2B.8.7",
    "data_nature": "REAL_CONTRACT",
    "routes": ["a_palace_deep_room", "tr_a_ramp_staging_wait", "tr_b_apps_kitchen_control", "tr_b_apps_house_staging"],
    "repetitions_per_route": 10,
    "total_executions": 40,
})

write_json("route_patch_manifest.json", {
    "marco": "2B.8.7",
    "data_nature": "REAL_CONTRACT",
    "patches": [
        {"waypoint": "t_a_ramp_doorway", "before": [675.5, -1425.0, -259.3], "after": [722.0, -1408.0, -259.0], "arrival_radius_after": 36.0},
        {"waypoint": "t_b_apps_kitchen_doorway", "before": [-925.4, 587.4, -77.0], "after": [-965.5, 563.8, -76.0], "arrival_radius_after": 32.0},
        {"contract": "OnRoundEnd & Unload session finalization", "before": "missing FinalizeActiveSession", "after": "AUTHORITY_RELEASED / CAPTURE_ENDED recorded"},
    ],
})

trx_path = OUT_DIR / "_trx" / "targeted_2b87.trx"
tree = ET.parse(trx_path)
ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
tests = [{"test_name": r.attrib.get("testName"), "outcome": r.attrib.get("outcome"), "duration": r.attrib.get("duration")} for r in tree.findall(".//t:UnitTestResult", ns)]
passed_cnt = sum(1 for t in tests if t["outcome"] == "Passed")
failed_cnt = len(tests) - passed_cnt
write_json("targeted_test_result.json", {
    "marco": "2B.8.7",
    "data_nature": "REAL",
    "generated_at_utc": now_utc,
    "trx_path": str(trx_path).replace("\\", "/"),
    "total": len(tests),
    "passed": passed_cnt,
    "failed": failed_cnt,
    "all_passed": failed_cnt == 0 and len(tests) > 0,
    "tests": tests,
})

# 5v5 confirmation not executed because solo certification gate failed (Section 10)
(OUT_DIR / "full_canary_telemetry.jsonl").write_text("", encoding="utf-8")
write_json("full_canary_metrics.json", {
    "marco": "2B.8.7",
    "data_nature": "REAL_CONTRACT",
    "executed": False,
    "reason": "BLOCKED_BY_SOLO_CERTIFICATION_GATE_FAILURE",
})

m_palace = json.loads((OUT_DIR / "palace_certification_metrics.json").read_text(encoding="utf-8"))
m_aramp = json.loads((OUT_DIR / "a_ramp_certification_metrics.json").read_text(encoding="utf-8"))
m_bkit = json.loads((OUT_DIR / "b_kitchen_certification_metrics.json").read_text(encoding="utf-8"))
m_bhouse = json.loads((OUT_DIR / "b_house_certification_metrics.json").read_text(encoding="utf-8"))

write_json("findings.json", {
    "marco": "2B.8.7",
    "data_nature": "REAL",
    "generated_at_utc": now_utc,
    "verdict": verdict,
    "targeted_tests": f"{passed_cnt}/{len(tests)}",
    "solo_summary": {
        "a_palace_deep_room": {"completion": m_palace["completion_formula"], "on_time": m_palace["on_time_formula"], "detour": m_palace["mean_detour_ratio"], "pending": m_palace["pending_sessions"], "passed": m_palace["passed"]},
        "tr_a_ramp_staging_wait": {"completion": m_aramp["completion_formula"], "on_time": m_aramp["on_time_formula"], "detour": m_aramp["mean_detour_ratio"], "pending": m_aramp["pending_sessions"], "passed": m_aramp["passed"]},
        "tr_b_apps_kitchen_control": {"completion": m_bkit["completion_formula"], "on_time": m_bkit["on_time_formula"], "detour": m_bkit["mean_detour_ratio"], "pending": m_bkit["pending_sessions"], "passed": m_bkit["passed"]},
        "tr_b_apps_house_staging": {"completion": m_bhouse["completion_formula"], "on_time": m_bhouse["on_time_formula"], "detour": m_bhouse["mean_detour_ratio"], "pending": m_bhouse["pending_sessions"], "passed": m_bhouse["passed"]},
    },
    "five_v_five_executed": False,
})

report = f"""# MARCO 2B.8.7 — Relatório Final da Certificação ao Vivo TR Solo

**Veredito Canônico:** `{verdict}`

## 1. Testes Direcionados (`REAL`)
- `{passed_cnt}/{len(tests)}` aprovados (`failed = {failed_cnt}`).

## 2. Certificação Solo no Servidor CS2 (`REAL`, 40 execuções)
| Rota | Conclusões `(N/D)` | `ON_TIME (N/D)` | Mean Detour | Pending | Passou? |
| --- | ---: | ---: | ---: | ---: | --- |
| `a_palace_deep_room` | `{m_palace['completion_formula']}` | `{m_palace['on_time_formula']}` | `{m_palace['mean_detour_ratio']}` | `{m_palace['pending_sessions']}` | `False` |
| `tr_a_ramp_staging_wait` | `{m_aramp['completion_formula']}` | `{m_aramp['on_time_formula']}` | `{m_aramp['mean_detour_ratio']}` | `{m_aramp['pending_sessions']}` | `False` |
| `tr_b_apps_kitchen_control` | `{m_bkit['completion_formula']}` | `{m_bkit['on_time_formula']}` | `{m_bkit['mean_detour_ratio']}` | `{m_bkit['pending_sessions']}` | `False` |
| `tr_b_apps_house_staging` | `{m_bhouse['completion_formula']}` | `{m_bhouse['on_time_formula']}` | `{m_bhouse['mean_detour_ratio']}` | `{m_bhouse['pending_sessions']}` | `False` (`8/10`, meta `>= 9/10`) |

## 3. Confirmação 5v5
- Não executada (`BLOCKED_BY_SOLO_CERTIFICATION_GATE_FAILURE`), conforme Seção 10.
"""
(OUT_DIR / "tr_live_route_certification_final_report.md").write_text(report, encoding="utf-8")

deliverables = [
    "input_snapshot.json", "certification_contract.json", "solo_route_matrix.json",
    "solo_route_telemetry.jsonl", "palace_certification_metrics.json", "a_ramp_certification_metrics.json",
    "b_kitchen_certification_metrics.json", "b_house_certification_metrics.json", "live_failure_root_causes.json",
    "route_patch_manifest.json", "targeted_test_result.json", "full_canary_telemetry.jsonl",
    "full_canary_metrics.json", "findings.json", "tr_live_route_certification_final_report.md",
]
entries = []
all_ok = True
for name in deliverables:
    p = OUT_DIR / name
    exists = p.exists()
    size = p.stat().st_size if exists else 0
    digest = sha256_file(p) if exists else ""
    if not exists or len(digest) != 64 or (size == 0 and name != "full_canary_telemetry.jsonl"):
        all_ok = False
    entries.append({"file": name, "path": str(p).replace("\\", "/"), "exists": exists, "size_bytes": size, "sha256": digest})

write_json("deliverable_evidence.json", {
    "marco": "2B.8.7",
    "generated_at_utc": now_utc,
    "verdict": verdict,
    "all_deliverables_verified": all_ok,
    "deliverables": entries,
})
print(f"FINALIZE_2B87_DONE: verdict={verdict} all_deliverables_verified={all_ok} tests={passed_cnt}/{len(tests)}")
