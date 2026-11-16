"""Auditoria da matriz de aquisição + ausência de dados intermediários + marcador de pausa."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".").resolve()
IC = ROOT / "datasets/mirage_domains/intermediate_competitive"

matrix = json.loads((IC / "acquisition_source_matrix.json").read_text(encoding="utf-8"))
print("top keys:", list(matrix.keys()))
sources = matrix.get("sources") or matrix.get("source_matrix") or []
print("n sources:", len(sources))
if sources:
    print("source keys:", list(sources[0].keys()))
    for src in sources:
        sid = src.get("source_id") or src.get("id")
        crit = src.get("criteria") or src.get("gate_a_criteria") or {}
        if isinstance(crit, dict):
            summary = {k: (v.get("status") if isinstance(v, dict) else v) for k, v in crit.items()}
            passes = sum(1 for v in summary.values() if str(v).upper().startswith("PASS"))
            print(f"  {sid}: n={len(summary)} PASS={passes} :: {summary}")
        else:
            print(f"  {sid}: criteria tipo {type(crit)} -> {str(crit)[:200]}")

for key in ("gate_a_summary", "summary", "gate_a_evaluation", "overall"):
    if key in matrix:
        print(f"\n{key}: {json.dumps(matrix[key], ensure_ascii=False)[:1500]}")

print("\n=== ausência de dados intermediários ===")
patterns = ("*.dem", "*.dem.gz", "*.rar", "*.npz", "*.parquet", "*.zip")
found = []
for pattern in patterns:
    found += [p.as_posix() for p in IC.rglob(pattern) if p.is_file()]
print(f"arquivos de dados encontrados: {len(found)} -> {found[:10]}")

print("\n=== marcador de pausa ===")
marker_path = ROOT / "training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json"
print("existe:", marker_path.is_file(), "bytes:", marker_path.stat().st_size if marker_path.is_file() else None)
marker = json.loads(marker_path.read_text(encoding="utf-8"))
for key in ("marker", "resumption_requires_human_authorization", "training_prohibited", "prohibited_during_pause"):
    if key in marker:
        print(f"  {key}: {json.dumps(marker[key], ensure_ascii=False)[:300]}")

print("\n=== professional_vs_intermediate: contagem de métricas ===")
pvi = json.loads((ROOT / "training_runs/intermediate_domain_study/professional_vs_intermediate.json").read_text(encoding="utf-8"))
metrics = pvi.get("metrics")
if isinstance(metrics, list):
    print("metrics é lista, n =", len(metrics))
    for m in metrics:
        print("   -", m.get("metric_id") or m.get("name"), "|", m.get("value"), "|", m.get("metric_status") or m.get("status"))
elif isinstance(metrics, dict):
    print("metrics é dict, n =", len(metrics))
    for k, v in metrics.items():
        print(f"   - {k}: {json.dumps(v, ensure_ascii=False)[:160]}")
print("comparison_status:", pvi.get("comparison_status"))
print("execution_status:", pvi.get("execution_status"))
