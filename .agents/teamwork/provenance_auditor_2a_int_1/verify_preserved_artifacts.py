"""Recalcula SHA-256 dos 95 artefatos preservados a partir do inventário do marcador.

SOMENTE LEITURA. Saída: preserved_artifacts_verify.json (no diretório do auditor).
"""
import hashlib
import json
import os
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
MARKER = "training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json"
EXPECTED_MARKER_SHA = "465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad"
EXPECTED_MARKER_BYTES = 37114


def sha(ab):
    h = hashlib.sha256()
    with open(ab, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    marker_abs = os.path.join(ROOT, MARKER)
    with open(marker_abs, "rb") as fh:
        raw = fh.read()
    marker_sha = hashlib.sha256(raw).hexdigest()
    d = json.loads(raw.decode("utf-8"))
    inv = d["preserved_artifacts_inventory"]

    keysets = {}
    for e in inv:
        keysets.setdefault(tuple(sorted(e.keys())), 0)
        keysets[tuple(sorted(e.keys()))] += 1
    print("entry key schemas:", {k: v for k, v in keysets.items()})

    rows, divergences = [], []
    total_bytes_checked = 0
    for e in inv:
        rel = (e.get("repo_relative_path") or e.get("path") or "").replace("\\", "/")
        declared_sha = (e.get("sha256") or "").lower()
        declared_size = e.get("size_bytes")
        ab = os.path.join(ROOT, rel)
        exists = os.path.isfile(ab)
        if not exists:
            rows.append({"path": rel, "exists": False})
            divergences.append({"path": rel, "issue": "MISSING_FILE",
                                "declared_sha256": declared_sha, "actual_sha256": None})
            continue
        st = os.stat(ab)
        actual_sha = sha(ab)
        total_bytes_checked += st.st_size
        ok = (actual_sha == declared_sha) and (st.st_size == declared_size)
        rows.append({
            "path": rel, "exists": True, "size_match": st.st_size == declared_size,
            "hash_match": actual_sha == declared_sha,
        })
        if not ok:
            divergences.append({
                "path": rel, "issue": "HASH_OR_SIZE_MISMATCH",
                "declared_sha256": declared_sha, "actual_sha256": actual_sha,
                "declared_size": declared_size, "actual_size": st.st_size,
                "mtime_utc": __import__("datetime").datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z",
            })

    matches = sum(1 for r in rows if r.get("hash_match") and r.get("size_match"))
    out = {
        "marker_path": MARKER,
        "marker_bytes": len(raw),
        "marker_sha256": marker_sha,
        "marker_bytes_match": len(raw) == EXPECTED_MARKER_BYTES,
        "marker_sha_match": marker_sha == EXPECTED_MARKER_SHA,
        "inventory_entries": len(inv),
        "total_artifacts_enumerated_declared": d.get("total_artifacts_enumerated"),
        "total_bytes_declared": d.get("total_bytes"),
        "total_bytes_rechecked": total_bytes_checked,
        "matches": matches,
        "ratio": f"({matches}/{len(inv)})",
        "divergences": divergences,
        "all_match": matches == len(inv),
        "verification_status_declared": d.get("verification_status"),
        "artifact_class_counts_declared": d.get("artifact_class_counts"),
        "hashing_method": d.get("hashing_method"),
        "sample_rows": rows[:5],
    }
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "preserved_artifacts_verify.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    print("marker sha256 =", marker_sha, "| match:", out["marker_sha_match"])
    print("marker bytes  =", len(raw), "| match:", out["marker_bytes_match"])
    print("declared total_artifacts_enumerated =", d.get("total_artifacts_enumerated"))
    print("declared total_bytes =", d.get("total_bytes"))
    print("rechecked total_bytes =", total_bytes_checked)
    print("MATCHES =", out["ratio"], "| all_match =", out["all_match"])
    print("divergences =", json.dumps(divergences, indent=1, ensure_ascii=False))
    print("declared verification_status =", json.dumps(d.get("verification_status"), ensure_ascii=False)[:600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
