#!/usr/bin/env python3
"""
Fase 2.2 - Passo 3: Correção da Proveniência dos AimProfiles e Matriz de Elegibilidade de Treino.

Categorias permitidas:
- HUMAN_CAPTURE_IN_GAME: 0 (sem captura manual com gravador individual in-game)
- HUMAN_VISUAL_APPROVAL: 53 perfis (miras primárias aprovadas visualmente no PDF e no Source 2)
- GEOMETRIC_DERIVATION: 53 perfis (miras secundárias de ângulo e crossfire derivadas geometricamente)
- TEMPLATE_DEFAULT: 53 perfis (pitch fixo -25.0° para suporte de utilitárias, FORA do treino expert)
- DEMO_ANGLE_CLUSTER: 0

Gera:
1. aim_profile_provenance_v2.json
2. aim_profile_training_eligibility_v2.json
"""

import json
import time
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parents[2]
    ds_dir = base_dir / "datasets" / "mirage_v2"
    contracts_dir = ds_dir / "contracts"
    reports_dir = ds_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("=== RECLASSIFICANDO PROVENIÊNCIA DOS 159 AIMPROFILES ===")

    aims_raw = json.load(open(contracts_dir / "aim_profiles_v1.json", "r", encoding="utf-8"))

    provenance_list = []
    eligibility_list = []
    
    counts_by_type = {
        "HUMAN_CAPTURE_IN_GAME": 0,
        "HUMAN_VISUAL_APPROVAL": 0,
        "DEMO_ANGLE_CLUSTER": 0,
        "GEOMETRIC_DERIVATION": 0,
        "TEMPLATE_DEFAULT": 0
    }

    for a in aims_raw:
        a_id = a["aim_profile_id"]
        spot_id = a["spot_id"]
        priority = a["priority"]
        pitch = a["captured_pitch"]
        yaw = a["captured_yaw"]

        if priority == 1 or a_id.endswith("_primary"):
            source_type = "HUMAN_VISUAL_APPROVAL"
            source_desc = "Mira primária do spot validada e aprovada visualmente pelo usuário no catálogo PDF e no Source 2."
            is_eligible = True
            confidence = 0.95
            allowed_tasks = ["AIM_ORIENTATION_HEAD", "SPOT_CROSSHAIR_PLACEMENT"]
        elif priority == 2 or a_id.endswith("_secondary"):
            source_type = "GEOMETRIC_DERIVATION"
            source_desc = "Ângulo derivado geometricamente pelo pipeline para checagem de corner e cobertura de crossfire."
            is_eligible = True
            confidence = 0.85
            allowed_tasks = ["CORNER_CLEAR_ORIENTATION", "SECONDARY_CROSSFIRE_HEAD"]
        else: # priority == 3 ou pitch == -25.0
            source_type = "TEMPLATE_DEFAULT"
            source_desc = "Pitch parabólico fixo heurístico (-25.0°) para suporte de utilitária. NÃO provém de arremesso humano ou demo."
            is_eligible = False
            confidence = 0.0
            allowed_tasks = []

        counts_by_type[source_type] += 1

        p_entry = {
            "aim_profile_id": a_id,
            "spot_id": spot_id,
            "provenance_category": source_type,
            "description": source_desc,
            "captured_pitch": pitch,
            "captured_yaw": yaw,
            "target_landmark": a["target_landmark"],
            "target_position": a["target_position"],
            "has_in_game_recorder_event": False,
            "human_visual_approval_confirmed": (source_type == "HUMAN_VISUAL_APPROVAL")
        }
        provenance_list.append(p_entry)

        e_entry = {
            "aim_profile_id": a_id,
            "spot_id": spot_id,
            "provenance_category": source_type,
            "training_eligibility": "ELIGIBLE" if is_eligible else "INELIGIBLE_TEMPLATE",
            "is_expert_training_label": is_eligible,
            "confidence_weight": confidence,
            "allowed_training_heads": allowed_tasks,
            "exclusion_reason": "NONE" if is_eligible else "TEMPLATE_DEFAULT_GENERIC_PITCH_MINUS_25_EXCLUDED_FROM_EXPERT_TRAINING"
        }
        eligibility_list.append(e_entry)

    prov_json = {
        "audit_version": "2.2.0",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_aim_profiles": len(aims_raw),
        "counts_by_provenance": counts_by_type,
        "forensic_correction_note": (
            "Correção formal do Bloqueador 3: a categoria HUMAN_CAPTURE_IN_GAME foi zerada pois não houve "
            "captura manual in-game individual com o Tactical Spot Recorder para cada uma das 53 miras. "
            "As 53 miras primárias foram corretamente reclassificadas como HUMAN_VISUAL_APPROVAL, refletindo "
            "a homologação e aprovação visual do catálogo PDF/Source 2."
        ),
        "profiles": provenance_list
    }

    (ds_dir / "aim_profile_provenance_v2.json").write_text(json.dumps(prov_json, indent=2, ensure_ascii=False), encoding="utf-8")
    (reports_dir / "aim_profile_provenance_v2.json").write_text(json.dumps(prov_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Salvo: aim_profile_provenance_v2.json")

    elig_json = {
        "contract_version": "2.2.0",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_profiles": len(eligibility_list),
        "total_eligible_for_training": sum(1 for e in eligibility_list if e["is_expert_training_label"]),
        "total_ineligible_templates": sum(1 for e in eligibility_list if not e["is_expert_training_label"]),
        "rules": {
            "visual_approval_is_not_human_capture": True,
            "human_capture_requires_capture_event": True,
            "template_aim_is_not_expert_eligible": True,
            "lineup_utility_requires_ballistic_capture_or_demo_cluster": True
        },
        "profiles": eligibility_list
    }

    (ds_dir / "aim_profile_training_eligibility_v2.json").write_text(json.dumps(elig_json, indent=2, ensure_ascii=False), encoding="utf-8")
    (reports_dir / "aim_profile_training_eligibility_v2.json").write_text(json.dumps(elig_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Salvo: aim_profile_training_eligibility_v2.json")

if __name__ == "__main__":
    main()
