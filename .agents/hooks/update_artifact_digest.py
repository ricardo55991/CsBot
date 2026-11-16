#!/usr/bin/env python3
"""
Utilitario de cache de resumos e metadados de artefatos baseado em hash SHA-256 e tamanho físico.
Se SHA-256 e tamanho não mudaram, reutiliza o digest existente sem releitura integral.
Se mudaram, invalida o digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
CACHE_FILE = WORKSPACE_ROOT / ".agents" / "cache" / "artifact_digest_index.json"


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_digest_index() -> Dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "schema": "csbot.artifact_digest_index.v1",
        "governance_version": "1.2.0-lean",
        "digests": {}
    }


def save_digest_index(data: Dict[str, Any]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = CACHE_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_file.replace(CACHE_FILE)


def get_or_update_digest(
    rel_path: str,
    summary: Optional[str] = None,
    key_sections: Optional[list[str]] = None,
    producer: str = "main_agent",
    schema: Optional[str] = None
) -> Dict[str, Any]:
    abs_path = WORKSPACE_ROOT / rel_path
    if not abs_path.exists() or abs_path.is_dir():
        return {"error": "FILE_NOT_FOUND", "rel_path": rel_path}

    current_size = abs_path.stat().st_size
    current_hash = compute_sha256(abs_path)
    
    index_data = load_digest_index()
    digests = index_data.setdefault("digests", {})
    cached = digests.get(rel_path)

    if cached and cached.get("sha256") == current_hash and cached.get("file_size") == current_size:
        return {
            "status": "CACHE_HIT",
            "digest": cached,
            "reused": True
        }

    # Hash mudou ou novo artefato
    new_digest = {
        "relative_path": rel_path.replace("\\", "/"),
        "sha256": current_hash,
        "file_size": current_size,
        "last_modified": abs_path.stat().st_mtime,
        "summary": summary or (cached.get("summary") if cached and cached.get("sha256") == current_hash else "No summary provided"),
        "key_sections": key_sections or [],
        "schema": schema,
        "producer": producer,
        "safe_for_reuse": True
    }
    digests[rel_path] = new_digest
    save_digest_index(index_data)

    return {
        "status": "CACHE_MISS_UPDATED",
        "digest": new_digest,
        "reused": False
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        res = get_or_update_digest(target)
        print(json.dumps(res, indent=2))
    else:
        print("Usage: python update_artifact_digest.py <relative_path>")
