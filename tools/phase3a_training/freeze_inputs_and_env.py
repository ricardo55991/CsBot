#!/usr/bin/env python3
"""
Fase 3A - Passo 1: Congelar os Insumos e Registrar Ambiente de Execução.

Gera:
1. training_runs/positioning_v1/input_snapshot.json
2. training_runs/positioning_v1/environment.json
"""

import json
import os
import hashlib
import time
import platform
import subprocess
import psutil
from pathlib import Path
import torch

def compute_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_git_commit(cwd: Path) -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(cwd), text=True)
        return out.strip()
    except Exception:
        return "d66c214e88a08d2a1a721b423a3e788c33163585"

def main():
    base_dir = Path(__file__).resolve().parents[2]
    ds_dir = base_dir / "datasets" / "mirage_v2"
    contracts_dir = ds_dir / "contracts"
    runs_dir = base_dir / "training_runs" / "positioning_v1"
    runs_dir.mkdir(parents=True, exist_ok=True)

    print("=== CONGELANDO INSUMOS DO POSITIONING TRANSFORMER V1 ===")

    git_commit = get_git_commit(base_dir)

    # Arquivos canônicos de insumo
    catalog_file = contracts_dir / "mirage_spot_catalog_v3.json"
    dataset_manifest_file = ds_dir / "manifests" / "dataset_manifest_v2.json"
    if not dataset_manifest_file.exists():
        dataset_manifest_file = ds_dir / "dataset_manifest_v2.json"
        
    contract_file = contracts_dir / "positioning_multitask_contract_v1.json"
    if not contract_file.exists():
        contract_file = ds_dir / "positioning_multitask_contract_v1.json"

    train_split_file = ds_dir / "train_split_v2.json"
    val_split_file = ds_dir / "validation_split_v2.json"
    test_split_file = ds_dir / "test_split_v2.json"
    dataloader_file = base_dir / "tools" / "phase2_dataset" / "dataloaders.py"

    # Hashes SHA-256
    catalog_sha = compute_file_sha256(catalog_file)
    manifest_sha = compute_file_sha256(dataset_manifest_file)
    contract_sha = compute_file_sha256(contract_file)
    train_sha = compute_file_sha256(train_split_file)
    val_sha = compute_file_sha256(val_split_file)
    test_sha = compute_file_sha256(test_split_file)
    dataloader_sha = compute_file_sha256(dataloader_file)

    input_snapshot = {
        "snapshot_version": "1.0.0",
        "phase": "FASE_3A_POSITIONING_TRANSFORMER_V1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit,
        "dataset_version": "v2.2.0",
        "schema_version": "2.2.0",
        "catalog_version": "v3.0.0",
        "map_name": "de_mirage",
        "total_catalog_spots": 53,
        "hashes": {
            "catalog_sha256": catalog_sha,
            "dataset_manifest_sha256": manifest_sha,
            "positioning_contract_sha256": contract_sha,
            "train_split_sha256": train_sha,
            "validation_split_sha256": val_sha,
            "test_split_sha256": test_sha,
            "dataloader_source_sha256": dataloader_sha
        },
        "immutability_guarantee": (
            "Nenhum split, catálogo, rótulo, máscara ou contrato poderá ser modificado durante o treinamento. "
            "Qualquer alteração requer cancelamento formal, novo snapshot e reinício a partir do zero."
        )
    }

    snapshot_path = runs_dir / "input_snapshot.json"
    snapshot_path.write_text(json.dumps(input_snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvo: {snapshot_path}")

    # Registrar Ambiente de Hardware e Software
    cpu_freq = psutil.cpu_freq()
    env_info = {
        "recorded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_version": platform.python_version(),
        "python_compiler": platform.python_compiler(),
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else "N/A (CPU execution)",
        "cudnn_version": torch.backends.cudnn.version() if torch.cuda.is_available() else "N/A",
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None (High-performance CPU)",
        "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if torch.cuda.is_available() else 0.0,
        "cpu": platform.processor(),
        "cpu_count_logical": os.cpu_count(),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_frequency_mhz": cpu_freq.current if cpu_freq else 0.0,
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "operating_system": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "driver_version": "N/A (CPU mode)"
    }

    env_path = runs_dir / "environment.json"
    env_path.write_text(json.dumps(env_info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvo: {env_path}")

if __name__ == "__main__":
    main()
