"""Snapshot de bytes + SHA-256 de todos os alvos (ANTES/DEPOIS).
Le os caminhos de targets.json (nunca digitados na linha de comando).
Uso: python snapshot_hashes.py <label>
"""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "targets.json").read_text(encoding="utf-8"))
REPO = Path(__file__).resolve().parents[4]  # .../CsBot


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "UNLABELED"
    rows = []
    for rel in CFG["targets"]:
        p = REPO / rel
        if not p.exists():
            rows.append({"path": rel, "exists": False})
            continue
        rows.append(
            {
                "path": rel,
                "exists": True,
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
                "mtime_utc": p.stat().st_mtime,
            }
        )
    out = {"label": label, "repo_root": str(REPO), "entries": rows}
    dest = HERE / f"hashes_{label}.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        if r["exists"]:
            print(f"{r['bytes']:>8}  {r['sha256']}  {r['path']}")
        else:
            print(f"{'MISSING':>8}  {'-'*64}  {r['path']}")
    print(f"\n[gravado] {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
