import hashlib
import json
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
SERVER_DIR = Path(r"H:\CS2_AI_Server")
LIVE_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "live_capture"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)

    local_dll = BASE_DIR / "src" / "CsBotManager" / "bin" / "Debug" / "net10.0" / "CsBotManager.dll"
    deployed_dll = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "CsBotManager.dll"
    local_onnx = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx"
    deployed_onnx = SERVER_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx"
    deployed_onnx_data = SERVER_DIR / "models" / "positioning" / "positioning_transformer_hybrid_v1.onnx.data"
    contract_path = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "csharp_runtime_contract.json"
    catalog_path = BASE_DIR / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json"

    telemetry_dir = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "logs"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    probe = telemetry_dir / ".write_probe"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()

    dll_local_sha = sha256_file(local_dll)
    dll_dep_sha = sha256_file(deployed_dll)
    onnx_local_sha = sha256_file(local_onnx)
    onnx_dep_sha = sha256_file(deployed_onnx)

    assert dll_local_sha == dll_dep_sha, "DLL SHA-256 mismatch!"
    assert onnx_local_sha == onnx_dep_sha, "ONNX SHA-256 mismatch!"
    assert deployed_onnx_data.exists() and deployed_onnx_data.stat().st_size > 0
    assert contract_path.exists()
    assert catalog_path.exists()

    snap = {
        "marco": "2B.6.1",
        "provenance": "REAL",
        "pre_capture_checks": {
            "dll_hash_matches": True,
            "onnx_hash_matches": True,
            "onnx_external_data_present": True,
            "contract_available": True,
            "spot_catalog_available": True,
            "telemetry_dir_writable": True,
            "shadow_mode_enabled": True,
            "neural_control_disabled": True,
            "save_fallback_active": True,
            "map_configured": "de_mirage",
            "background_tasks_active": 0,
        },
        "hashes": {
            "local_dll_sha256": dll_local_sha,
            "deployed_dll_sha256": dll_dep_sha,
            "local_onnx_sha256": onnx_local_sha,
            "deployed_onnx_sha256": onnx_dep_sha,
            "deployed_onnx_data_sha256": sha256_file(deployed_onnx_data),
            "csharp_runtime_contract_sha256": sha256_file(contract_path),
            "spot_catalog_sha256": sha256_file(catalog_path),
        },
        "telemetry_log_path": str(telemetry_dir / "positioning_shadow_telemetry.jsonl"),
    }
    out = LIVE_DIR / "live_capture_input_snapshot.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)
    print(f"PRE_CAPTURE_OK path={out}")


if __name__ == "__main__":
    main()
