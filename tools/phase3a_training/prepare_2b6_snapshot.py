#!/usr/bin/env python3
"""
Marco 2B.6 - Seção 2: Snapshot, Proteção e Cópia para Staging Versionado em models/positioning/.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
ONNX_SRC = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_export" / "positioning_transformer_hybrid_v1.onnx"
CONTRACT_SRC = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_export" / "positioning_runtime_contract_v1.json"
MODELS_POS_DIR = BASE_DIR / "models" / "positioning"
ONNX_DST = MODELS_POS_DIR / "de_mirage_positioning_hybrid_v1_candidate.onnx"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
    except Exception:
        return "UNKNOWN"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_POS_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ONNX_SRC, ONNX_DST)
    src_sha = sha256_file(ONNX_SRC)
    dst_sha = sha256_file(ONNX_DST)
    if src_sha != dst_sha:
        raise RuntimeError(f"SHA-256 divergente após cópia: src={src_sha}, dst={dst_sha}")

    tracked = [
        ONNX_SRC,
        ONNX_DST,
        CONTRACT_SRC,
        BASE_DIR / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json",
        BASE_DIR / "datasets" / "mirage_v2" / "positioning_v2_full_temporal" / "supervised_spot_mask_v1.json",
        BASE_DIR / "src" / "CsBotManager" / "CsBotManagerPlugin.cs",
        BASE_DIR / "src" / "CsBotManager" / "BotSystemConfig.cs",
        BASE_DIR / "src" / "CsBotManager" / "MicroMoveEngine.cs",
        BASE_DIR / "src" / "CsBotManager" / "CsBotManager.csproj",
    ]
    dll_path = BASE_DIR / "src" / "CsBotManager" / "bin" / "Debug" / "net10.0" / "CsBotManager.dll"
    if dll_path.exists():
        tracked.append(dll_path)

    hashes = {str(p.relative_to(BASE_DIR)).replace("\\", "/"): sha256_file(p) for p in tracked}

    snap = {
        "marco": "2B.6",
        "git_commit": get_git_commit(),
        "hashes": hashes,
        "shadow_mode_only": True,
    }
    with open(OUT_DIR / "input_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)

    dep_manifest = {
        "source_onnx": str(ONNX_SRC.relative_to(BASE_DIR)).replace("\\", "/"),
        "staged_onnx": str(ONNX_DST.relative_to(BASE_DIR)).replace("\\", "/"),
        "sha256": dst_sha,
        "hash_verified_identical": True,
        "shadow_mode_only": True,
        "bot_control_enabled": False,
    }
    with open(OUT_DIR / "model_deployment_manifest.json", "w", encoding="utf-8") as f:
        json.dump(dep_manifest, f, indent=2, ensure_ascii=False)

    with open(CONTRACT_SRC, "r", encoding="utf-8") as f:
        rc = json.load(f)
    rc["csharp_shadow_mode"] = {
        "shadow_mode_only": True,
        "bot_control_enabled": False,
        "cadence_hz": 4,
        "preferred_batch_size": 5,
        "maximum_batch_wait_ms": 5,
        "inference_timeout_ms": 25,
        "maximum_pending_requests": 4,
        "staged_model_relative_path": "models/positioning/de_mirage_positioning_hybrid_v1_candidate.onnx",
        "expected_model_sha256": dst_sha,
    }
    with open(OUT_DIR / "csharp_runtime_contract.json", "w", encoding="utf-8") as f:
        json.dump(rc, f, indent=2, ensure_ascii=False)

    print(f"Snapshot 2B.6 e staging em models/positioning/ concluídos (sha256={dst_sha[:16]}...).")


if __name__ == "__main__":
    main()
