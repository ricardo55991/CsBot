import hashlib
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "onnx_v2_utility_patch_smoke"
SRC = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_contextual_v2" / "positioning_transformer_hybrid_v2.onnx"
DST_REPO = BASE_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v2.onnx"
DST_SERVER = Path(r"H:\CS2_AI_Server\models\positioning\de_mirage_positioning_hybrid_v2.onnx")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DST_REPO.parent.mkdir(parents=True, exist_ok=True)
    DST_SERVER.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SRC, DST_REPO)
    shutil.copy2(SRC, DST_SERVER)
    src_data = SRC.with_name(SRC.name + ".data")
    if src_data.exists():
        shutil.copy2(src_data, DST_REPO.with_name(src_data.name))
        shutil.copy2(src_data, DST_SERVER.with_name(src_data.name))

    h_src = sha256_file(SRC)
    h_repo = sha256_file(DST_REPO)
    h_srv = sha256_file(DST_SERVER)
    assert h_src == h_repo == h_srv

    manifest = {
        "marco": "2B.6.6",
        "model_version": "positioning_transformer_hybrid_v2",
        "contract_version": "positioning_runtime_contract_v2",
        "source_onnx": str(SRC.relative_to(BASE_DIR)).replace("\\", "/"),
        "repo_staging_onnx": str(DST_REPO.relative_to(BASE_DIR)).replace("\\", "/"),
        "server_staging_onnx": str(DST_SERVER).replace("\\", "/"),
        "sha256": h_src,
        "source_equals_repo": h_src == h_repo,
        "source_equals_server": h_src == h_srv,
        "contextual_inputs": ["team_idx", "role_idx", "stage_idx"],
        "v1_preserved": (BASE_DIR / "models" / "positioning" / "de_mirage_positioning_hybrid_v1_candidate.onnx").exists(),
    }
    with open(OUT_DIR / "model_deployment_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    with open(BASE_DIR / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json", "r", encoding="utf-8") as f:
        prof = json.load(f)
    print(f"DEPLOY_V2_OK sha256={h_src}")
    for s in prof["spots"]:
        if any(k in s["id"] for k in ("a_stairs", "market", "b_", "plant")):
            print(f"{s['id']:35s} side={s['side']:4s} sec={s['sector']:18s} use={s.get('usage','')}")


if __name__ == "__main__":
    main()
