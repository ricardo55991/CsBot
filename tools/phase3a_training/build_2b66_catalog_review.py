import hashlib
import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "onnx_v2_utility_patch_smoke"
SIDE_V2_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_contract_v2"
ONNX_V2 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_contextual_v2" / "positioning_transformer_hybrid_v2.onnx"
ONNX_V1 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_export" / "positioning_transformer_hybrid_v1.onnx"
CAT_PATH = BASE_DIR / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. input_snapshot.json
    tracked = [
        ONNX_V2,
        ONNX_V1,
        CAT_PATH,
        SIDE_V2_DIR / "spot_side_contract_v2.json",
        SIDE_V2_DIR / "spot_side_support_accounting.json",
        SIDE_V2_DIR / "utility_spot_assignment_audit.json",
        BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_contextual_v2" / "positioning_runtime_contract_v2.json",
        BASE_DIR / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json",
    ]
    snap = {
        "marco": "2B.6.6",
        "entry_verdict": "POSITIONING_ONNX_CONTEXTUAL_V2_READY_FOR_LIVE_SMOKE",
        "training_executed": False,
        "weights_modified": False,
        "hashes": {str(p.relative_to(BASE_DIR)).replace("\\", "/"): sha256_file(p) for p in tracked if p.exists()},
    }
    with open(OUT_DIR / "input_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=False)

    # 2. spot_catalog_review_resolution.json
    with open(CAT_PATH, "r", encoding="utf-8") as f:
        cat = json.load(f)
    cat_map = {s["id"]: s for s in cat["spots"]} if isinstance(cat["spots"], list) else cat["spots"]
    with open(SIDE_V2_DIR / "spot_side_support_accounting.json", "r", encoding="utf-8") as f:
        acc = json.load(f)
    acc_map = {s["spot_id"]: s for s in acc["spots"]}

    specs = {
        "tr_b_tapete_window_bomb_curve": {
            "compatible_states": {"T": ["HOLD", "OBJECTIVE", "STAGING"], "CT": ["RETAKE"]},
            "compatible_phases": {"T": ["PostPlant", "Contact", "Staging", "MapControl"], "CT": ["Retake", "PostPlant"]},
            "final_classification": "CONTEXTUAL",
            "ct_rule": "RETAKE_ONLY",
            "t_rule": "ALWAYS_ALLOWED",
            "justification": "Ângulo ofensivo/pós-plant TR na janela do Tapete B (T=25.685 total, Utility AI=0); uso CT nos dados (CT=1.091 total) ocorre em cenários de retake/flank pós-plant no bombsite B. Classificado conservadoramente como CONTEXTUAL (T permitido; CT restrito exclusivamente a RETAKE).",
        },
        "mid_connector_top_stairs": {
            "compatible_states": {"CT": ["HOLD", "STAGING", "RETAKE"], "T": ["HOLD", "CLEARANCE", "OBJECTIVE"]},
            "compatible_phases": {"CT": ["MapControl", "Setup", "Retake", "Contact"], "T": ["Contact", "PostPlant", "MapControl"]},
            "final_classification": "CONTEXTUAL",
            "ct_rule": "RETAKE_OR_HOLD",
            "t_rule": "HOLD_OR_POSTPLANT",
            "justification": "Posição de disputa de Meio no topo do Conector catalogada como CT, mas com predominância TR em demos (Train+Val T=154 vs CT=8). Classificada como CONTEXTUAL: permitida para CT em Setup/Hold/Retake e para T somente após entrada em Hold/Clearance/PostPlant.",
        },
        "mid_top_mid_boxes": {
            "compatible_states": {"T": ["HOLD", "STAGING", "CLEARANCE"], "CT": ["RETAKE", "CLEARANCE", "HOLD"]},
            "compatible_phases": {"T": ["MapControl", "Contact", "Staging"], "CT": ["Retake", "Contact"]},
            "final_classification": "CONTEXTUAL",
            "ct_rule": "RETAKE_OR_HOLD",
            "t_rule": "ALWAYS_ALLOWED",
            "justification": "Caixas do Top Mid catalogadas como TR e atribuídas pela Utility AI apenas a TR (T=2, CT=0), mas com ocupação CT em demos (Train+Val CT=60). Classificada como CONTEXTUAL: livre para TR no controle de Meio e restrita para CT apenas a CLEARANCE/HOLD/RETAKE.",
        },
        "mid_window_left_awp": {
            "compatible_states": {"CT": ["HOLD", "STAGING", "RETAKE"], "T": ["HOLD", "CLEARANCE"]},
            "compatible_phases": {"CT": ["Setup", "MapControl", "Retake", "Contact"], "T": ["PostPlant", "Contact"]},
            "final_classification": "CONTEXTUAL",
            "ct_rule": "RETAKE_OR_HOLD",
            "t_rule": "HOLD_OR_POSTPLANT",
            "justification": "Quina esquerda da Janela do Meio catalogada como CT AWP, porém frequentemente ocupada por TR após domínio do Meio em demos (Train+Val T=85 vs CT=2). Classificada como CONTEXTUAL para evitar bloqueio cego mantendo restrição estrita fora de contexto.",
        },
    }

    resolutions = []
    for sid, sp in specs.items():
        c_entry = cat_map[sid]
        a_entry = acc_map[sid]
        resolutions.append({
            "spot_id": sid,
            "physical_position": {"x": c_entry["x"], "y": c_entry["y"], "z": c_entry["z"], "sector": c_entry["sector"], "bombsite": c_entry["associated_bombsite"]},
            "tactical_purpose": c_entry["description"],
            "catalog_side": c_entry["side"],
            "train_side_support": {"CT": a_entry["train_support_ct"], "T": a_entry["train_support_t"]},
            "validation_side_support": {"CT": a_entry["validation_support_ct"], "T": a_entry["validation_support_t"]},
            "test_side_support": {"CT": a_entry["test_support_ct"], "T": a_entry["test_support_t"]},
            "utility_ai_assignments": {"CT": a_entry["assigned_by_utility_ct"], "T": a_entry["assigned_by_utility_t"]},
            "compatible_states": sp["compatible_states"],
            "compatible_phases": sp["compatible_phases"],
            "final_classification": sp["final_classification"],
            "ct_rule": sp["ct_rule"],
            "t_rule": sp["t_rule"],
            "justification": sp["justification"],
        })

    resolution_doc = {
        "marco": "2B.6.6",
        "resolved_count": len(resolutions),
        "unresolved_count": 0,
        "status": "ALL_CATALOG_REVIEW_SPOTS_RESOLVED",
        "resolutions": resolutions,
    }
    with open(OUT_DIR / "spot_catalog_review_resolution.json", "w", encoding="utf-8") as f:
        json.dump(resolution_doc, f, indent=2, ensure_ascii=False)
    print(f"CATALOG_REVIEW_RESOLVED count={len(resolutions)}")


if __name__ == "__main__":
    main()
