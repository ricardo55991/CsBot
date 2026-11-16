"""Backup imutavel dos artefatos bugados (run D10) do Marco 2B.3.4 antes de
sobrescrever com o run corrigido. Registra SHA-256 anterior de cada arquivo.

Regra 06: backup + hash anterior + justificativa antes de sobrescrever *.pt e
artefatos de telemetria.
"""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PATCH = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1"
STAMP = "buggy_D10_20261109"
BACKUP = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1" / f"joint_temporal_patch_v1_{STAMP}"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# arquivos que o run de treino SOBRESCREVE
OVERWRITTEN = [
    "experiment_a_metrics.json",
    "experiment_b_metrics.json",
    "experiment_c_metrics.json",
    "experiment_comparison.json",
    "full_validation_metrics.json",
    "gate_verdict.json",
    "preservation_check.json",
    "selected_checkpoint.pt",
    "selected_thresholds.json",
]

BACKUP.mkdir(parents=True, exist_ok=False)

manifest = {
    "schema": "csbot.joint_temporal_patch.backup_manifest.v1",
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "reason": (
        "Run anterior do Marco 2B.3.4 continha o defeito D10 em clamped_class_weights "
        "(clip apos normalizar apagava o balanceamento). Artefatos preservados como "
        "auditoria antes de sobrescrever com o run corrigido (sqrt-inverse-frequency)."
    ),
    "source_dir": str(PATCH.relative_to(REPO)),
    "backup_dir": str(BACKUP.relative_to(REPO)),
    "files": {},
}

for name in OVERWRITTEN:
    src = PATCH / name
    if not src.exists():
        manifest["files"][name] = {"exists": False}
        continue
    h = sha256(src)
    manifest["files"][name] = {
        "bytes": src.stat().st_size,
        "sha256_before": h,
    }
    shutil.copy2(src, BACKUP / name)
    # verifica integridade da copia
    h_copy = sha256(BACKUP / name)
    assert h_copy == h, f"backup divergente: {name}"

out = BACKUP / "backup_manifest.json"
json.dump(manifest, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print(f"backup concluido em {BACKUP.relative_to(REPO)}")
print(f"manifesto: {out.relative_to(REPO)}")
for name, info in manifest["files"].items():
    if info["exists"]:
        print(f"  {name:<32} {info['bytes']:>9}  {info['sha256_before']}")
    else:
        print(f"  {name:<32} AUSENTE")
