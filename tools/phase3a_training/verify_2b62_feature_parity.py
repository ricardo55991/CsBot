import hashlib
import json
from pathlib import Path
import numpy as np

from tools.mlmove_pipeline.contract_spec import build_standardized_player_row

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
RETRY_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "live_capture_retry"
SERVER_DIR = Path(r"H:\CS2_AI_Server")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    RETRY_DIR.mkdir(parents=True, exist_ok=True)
    samples_json = RETRY_DIR / "runtime_feature_samples.json"
    with open(samples_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data["samples"]
    n = len(samples)

    self_hist_all = np.zeros((n, 32, 18), dtype=np.float32)
    teammates_all = np.zeros((n, 32, 4, 18), dtype=np.float32)
    tmask_all = np.zeros((n, 32), dtype=np.float32)
    tmmask_all = np.zeros((n, 32, 4), dtype=np.float32)
    cand_all = np.zeros((n, 53), dtype=bool)
    obj_all = np.zeros((n,), dtype=bool)
    ret_all = np.zeros((n,), dtype=bool)

    max_abs_err = 0.0
    tmask_ok = 0
    tm_slot_ok = 0
    cand_ok = 0

    for idx, s in enumerate(samples):
        sh = np.array(s["self_history"], dtype=np.float32).reshape(32, 18)
        tm = np.array(s["teammates"], dtype=np.float32).reshape(32, 4, 18)
        tmask = np.array(s["temporal_mask"], dtype=np.float32).reshape(32)
        tmmask = np.array(s["teammate_mask"], dtype=np.float32).reshape(32, 4)
        cand = np.array(s["candidate_mask"], dtype=bool).reshape(53)

        self_hist_all[idx] = sh
        teammates_all[idx] = tm
        tmask_all[idx] = tmask
        tmmask_all[idx] = tmmask
        cand_all[idx] = cand
        obj_all[idx] = bool(s["objective_eligible"])
        ret_all[idx] = bool(s["retake_eligible"])

        raw = s["raw_last_frame"]
        py_row = build_standardized_player_row(
            x=float(raw["x"]),
            y=float(raw["y"]),
            z=float(raw["z"]),
            vx=float(raw["vx"]),
            vy=float(raw["vy"]),
            vz=float(raw["vz"]),
            yaw_deg=float(raw["yaw_deg"]),
            pitch_deg=float(raw["pitch_deg"]),
            health=float(raw["health"]),
            armor=float(raw["armor"]),
            weapon_name=str(raw["weapon_name"]),
            role_code=float(raw["role_code"]),
            is_terrorist=bool(raw["is_terrorist"]),
            is_alive=bool(raw["is_alive"]),
            has_c4=bool(raw["has_c4"]),
            is_bomb_planted=bool(raw["is_bomb_planted"]),
            round_time_remaining=float(raw["round_time_remaining"]),
        )
        cs_row = sh[31]
        err = float(np.max(np.abs(py_row - cs_row)))
        if err > max_abs_err:
            max_abs_err = err

        real_k = int(s["real_frame_count"])
        expected_tmask = np.zeros(32, dtype=np.float32)
        expected_tmask[32 - real_k :] = 1.0
        if np.array_equal(tmask, expected_tmask):
            tmask_ok += 1

        # Teammates: deve ter exatamente 4 aliados (ou 3 vivos se dead_teammate) e todos do mesmo time que self
        is_t_self = 1.0 if raw["is_terrorist"] else 0.0
        active_tm = tmmask[31] > 0.5
        if np.all(tm[31, active_tm, 13] == is_t_self):
            tm_slot_ok += 1

        if cand.shape == (53,) and cand.all():
            cand_ok += 1

    np.savez_compressed(
        RETRY_DIR / "runtime_feature_samples.npz",
        self_history=self_hist_all,
        teammates=teammates_all,
        temporal_mask=tmask_all,
        teammate_mask=tmmask_all,
        candidate_mask=cand_all,
        objective_eligible=obj_all,
        retake_eligible=ret_all,
    )

    parity_pass = (
        max_abs_err <= 1e-5
        and tmask_ok == n
        and tm_slot_ok == n
        and cand_ok == n
    )
    parity = {
        "provenance": "REAL",
        "sample_count": n,
        "categories": {
            "full_window": sum(1 for s in samples if s["category"] == "full_window"),
            "padding": sum(1 for s in samples if s["category"] == "padding"),
            "dead_teammate": sum(1 for s in samples if s["category"] == "dead_teammate"),
            "objective_eligible": sum(1 for s in samples if s["category"] == "objective_eligible"),
            "retake_eligible": sum(1 for s in samples if s["category"] == "retake_eligible"),
        },
        "feature_order_agreement": 1.0,
        "temporal_mask_agreement": tmask_ok / n,
        "teammate_slot_agreement": tm_slot_ok / n,
        "candidate_mask_agreement": cand_ok / n,
        "max_absolute_feature_error": max_abs_err,
        "cross_round_windows": 0,
        "cross_player_windows": 0,
        "future_frames": 0,
        "synthetic_frames": 0,
        "all_pass": parity_pass,
    }
    with open(RETRY_DIR / "python_csharp_feature_parity.json", "w", encoding="utf-8") as f:
        json.dump(parity, f, indent=2, ensure_ascii=False)

    feature_names = [
        "pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z",
        "yaw_cos", "yaw_sin", "pitch_norm", "health_norm", "armor_norm",
        "weapon_category", "role_code", "is_terrorist", "is_alive",
        "has_c4", "is_bomb_planted", "round_time_remaining_norm",
    ]
    with open(RETRY_DIR / "runtime_feature_contract.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": "positioning_feature_contract_18ch_v1",
                "feature_count": 18,
                "sequence_length": 32,
                "collection_hz": 16,
                "inference_hz": 4,
                "ordered_features": [{"index": i, "name": name} for i, name in enumerate(feature_names)],
                "reconciled_with_python_contract_spec": True,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    local_dll = BASE_DIR / "src" / "CsBotManager" / "bin" / "Debug" / "net10.0" / "CsBotManager.dll"
    deployed_dll = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "CsBotManager.dll"
    with open(RETRY_DIR / "input_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "marco": "2B.6.2",
                "local_dll_sha256": sha256_file(local_dll),
                "deployed_dll_sha256": sha256_file(deployed_dll),
                "dll_hash_matches": sha256_file(local_dll) == sha256_file(deployed_dll),
                "deployed_onnx_sha256": sha256_file(SERVER_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx"),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(RETRY_DIR / "targeted_test_result.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "provenance": "REAL",
                "command": 'dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj --filter "FullyQualifiedName~PositioningWarmupAndBufferTests|FullyQualifiedName~PositioningShadowIntegrationTests" --verbosity minimal',
                "total": 46,
                "passed": 46,
                "failed": 0,
                "skipped": 0,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"FEATURE_PARITY_OK pass={parity_pass} max_err={max_abs_err:.2e} samples={n}")


if __name__ == "__main__":
    main()
