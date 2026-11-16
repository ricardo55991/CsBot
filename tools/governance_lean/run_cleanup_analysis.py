#!/usr/bin/env python3
"""
Script First: Análise Forense de Referências, Duplicatas e Quarentena Controlada (Governança 1.2 Lean)
Gera:
- cleanup_reference_graph.json
- cleanup_duplicate_groups.json
- cleanup_deletion_proposal.json
- .cleanup/quarantine_manifest.json
- archive_manifest.json
"""

import hashlib
import json
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

PROTECTED_EXPLICIT_PREFIXES = [
    "src/",
    "datasets/",
    "models/",
    "checkpoints/",
    "training_runs/positioning_v2_real_temporal/full_training/",
    "training_runs/intermediate_domain_study/",
    "datasets/mirage_domains/",
    "tools/intermediate_demo_acquisition/",
    ".agents/teamwork/orchestrator_2a_intermediate/",
    "PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json"
]

IGNORE_SCAN_DIRS = {".git", ".cleanup"}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def is_explicitly_protected(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    for pfx in PROTECTED_EXPLICIT_PREFIXES:
        if norm == pfx.rstrip("/") or norm.startswith(pfx):
            return True
    return False


def collect_evidence_references() -> Set[str]:
    referenced: Set[str] = set()
    evidence_files = list(WORKSPACE_ROOT.glob("**/deliverable_evidence.json"))
    evidence_files.extend(WORKSPACE_ROOT.glob("**/*evidence*.json"))
    evidence_files.extend(WORKSPACE_ROOT.glob("**/*snapshot*.json"))
    evidence_files.extend(WORKSPACE_ROOT.glob("**/*hashes*.json"))
    evidence_files.extend(WORKSPACE_ROOT.glob("**/manifest*.json"))

    for ef in evidence_files:
        try:
            data = json.loads(ef.read_text(encoding="utf-8"))
            text = json.dumps(data)
            # Extrai potenciais caminhos
            for part in text.split('"'):
                if "/" in part or "\\" in part:
                    p = part.replace("\\", "/").strip()
                    if (WORKSPACE_ROOT / p).exists():
                        referenced.add(p)
        except Exception:
            pass
    return referenced


def scan_and_analyze() -> Dict[str, Any]:
    evidence_refs = collect_evidence_references()
    files_by_hash = defaultdict(list)
    all_files: List[Tuple[str, int, str]] = []

    for p in WORKSPACE_ROOT.rglob("*"):
        try:
            rel = p.relative_to(WORKSPACE_ROOT)
            rel_str = str(rel).replace("\\", "/")
            parts = rel.parts
            if any(i in parts for i in IGNORE_SCAN_DIRS):
                continue
            if p.is_file():
                sz = p.stat().st_size
                all_files.append((rel_str, sz, p.suffix.lower()))
                # Calcula hash apenas para docs, scripts, JSONs e logs
                if p.suffix.lower() in [".md", ".json", ".pdf", ".txt", ".py", ".ps1", ".tmp", ".bak", ".old", ".cache"]:
                    h = compute_sha256(p)
                    files_by_hash[h].append((rel_str, sz))
        except Exception:
            pass

    # Recalcula grupos de duplicatas reais por hash SHA-256 e tamanho
    duplicate_groups = {h: flist for h, flist in files_by_hash.items() if len(flist) > 1}

    # Classificação rigorosa dos arquivos
    classified = {
        "PROTECTED_PRODUCT": [],
        "KEEP_CANONICAL": [],
        "KEEP_HISTORICAL": [],
        "SUPERSEDED_QUARANTINE": [],
        "DUPLICATE_QUARANTINE": [],
        "TEMPORARY_DELETE_CANDIDATE": [],
        "ORPHAN_REVIEW_REQUIRED": []
    }

    quarantine_manifest_items = []
    quarantine_base = WORKSPACE_ROOT / ".cleanup" / "quarantine"

    for rel_str, sz, suffix in all_files:
        if is_explicitly_protected(rel_str):
            classified["PROTECTED_PRODUCT"].append({"path": rel_str, "size": sz})
            continue

        if rel_str in evidence_refs:
            classified["KEEP_HISTORICAL"].append({"path": rel_str, "size": sz, "reason": "Referenced in evidence index/manifest"})
            continue

        # Arquivos temporários e caches efêmeros
        if "__pycache__" in rel_str or suffix == ".pyc":
            classified["TEMPORARY_DELETE_CANDIDATE"].append({
                "path": rel_str,
                "size": sz,
                "reason": "Python bytecode cache",
                "safe_to_delete": True
            })
            continue
        if ".pytest_cache" in rel_str:
            classified["TEMPORARY_DELETE_CANDIDATE"].append({
                "path": rel_str,
                "size": sz,
                "reason": "Pytest temporary cache",
                "safe_to_delete": True
            })
            continue
        if suffix in [".tmp", ".bak", ".old", ".cache"]:
            classified["TEMPORARY_DELETE_CANDIDATE"].append({
                "path": rel_str,
                "size": sz,
                "reason": "Temporary or backup file",
                "safe_to_delete": True
            })
            continue

        # Scripts de tooling e governança ativos
        if rel_str.startswith(".agents/") or rel_str.startswith("tools/"):
            classified["KEEP_CANONICAL"].append({"path": rel_str, "size": sz, "reason": "Active tooling or governance asset"})
            continue

        # Relatórios finais canônicos
        if rel_str.endswith("_final_report.md") or rel_str == "AGENTS.md" or rel_str.endswith("_report.md"):
            classified["KEEP_CANONICAL"].append({"path": rel_str, "size": sz, "reason": "Canonical report"})
            continue

        # Se não for temporário nem expressamente referenciado
        classified["ORPHAN_REVIEW_REQUIRED"].append({
            "path": rel_str,
            "size": sz,
            "reason": "Unreferenced or historical document requiring manual review"
        })

    # Mover itens temporários descartáveis (.tmp, .bak, .old) para quarentena local
    moved_count = 0
    reclaimed_bytes = 0

    for item in classified["TEMPORARY_DELETE_CANDIDATE"]:
        rel_str = item["path"]
        orig_p = WORKSPACE_ROOT / rel_str
        if orig_p.exists() and orig_p.is_file() and orig_p.suffix in [".tmp", ".bak", ".old", ".cache"]:
            target_p = quarantine_base / "cache" / orig_p.name
            target_p.parent.mkdir(parents=True, exist_ok=True)
            sha = compute_sha256(orig_p)
            try:
                shutil.move(str(orig_p), str(target_p))
                moved_count += 1
                reclaimed_bytes += item["size"]
                quarantine_manifest_items.append({
                    "original_path": rel_str,
                    "quarantine_path": str(target_p.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                    "sha256": sha,
                    "size_bytes": item["size"],
                    "classification": "TEMPORARY_DELETE_CANDIDATE",
                    "rationale": item["reason"],
                    "rollback_command": f"Move-Item -Path '{target_p.relative_to(WORKSPACE_ROOT)}' -Destination '{rel_str}'"
                })
            except Exception:
                pass

    # Gravar manifestos
    (WORKSPACE_ROOT / "cleanup_reference_graph.json").write_text(
        json.dumps({
            "schema": "csbot.cleanup_reference_graph.v1",
            "total_referenced_files": len(evidence_refs),
            "referenced_paths": sorted(list(evidence_refs))
        }, indent=2), encoding="utf-8"
    )

    (WORKSPACE_ROOT / "cleanup_duplicate_groups.json").write_text(
        json.dumps({
            "schema": "csbot.cleanup_duplicate_groups.v1",
            "total_duplicate_groups": len(duplicate_groups),
            "groups": [
                {"sha256": h, "file_count": len(flist), "files": flist}
                for h, flist in duplicate_groups.items()
            ]
        }, indent=2), encoding="utf-8"
    )

    (WORKSPACE_ROOT / ".cleanup" / "quarantine_manifest.json").write_text(
        json.dumps({
            "schema": "csbot.quarantine_manifest.v1",
            "governance_version": "1.2.0-lean",
            "total_quarantined_items": len(quarantine_manifest_items),
            "reclaimed_space_bytes": reclaimed_bytes,
            "items": quarantine_manifest_items
        }, indent=2), encoding="utf-8"
    )

    (WORKSPACE_ROOT / "archive_manifest.json").write_text(
        json.dumps({
            "schema": "csbot.archive_manifest.v1",
            "governance_version": "1.2.0-lean",
            "archived_items": [],
            "note": "Nenhum arquivo historico foi movido para archive/ sem autorizacao expressa; todos os historicos foram preservados in situ sob KEEP_HISTORICAL."
        }, indent=2), encoding="utf-8"
    )

    (WORKSPACE_ROOT / "cleanup_deletion_proposal.json").write_text(
        json.dumps({
            "schema": "csbot.cleanup_deletion_proposal.v1",
            "governance_version": "1.2.0-lean",
            "summary": {
                "safe_to_delete_cache_items": len(classified["TEMPORARY_DELETE_CANDIDATE"]),
                "quarantined_items": len(quarantine_manifest_items),
                "keep_canonical_count": len(classified["KEEP_CANONICAL"]),
                "keep_historical_count": len(classified["KEEP_HISTORICAL"]),
                "protected_product_count": len(classified["PROTECTED_PRODUCT"]),
                "orphan_review_required_count": len(classified["ORPHAN_REVIEW_REQUIRED"])
            },
            "permanent_deletion_requires_human_approval": True,
            "items_quarantined": quarantine_manifest_items
        }, indent=2), encoding="utf-8"
    )

    return {
        "status": "PASS",
        "total_files_scanned": len(all_files),
        "protected_product_files": len(classified["PROTECTED_PRODUCT"]),
        "keep_canonical": len(classified["KEEP_CANONICAL"]),
        "keep_historical": len(classified["KEEP_HISTORICAL"]),
        "duplicate_groups_recalculated": len(duplicate_groups),
        "items_quarantined": len(quarantine_manifest_items),
        "reclaimed_bytes": reclaimed_bytes,
        "permanent_deletions": 0
    }


if __name__ == "__main__":
    res = scan_and_analyze()
    print(json.dumps(res, indent=2))
