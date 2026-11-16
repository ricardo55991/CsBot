import json
import os
from datetime import datetime

# Carrega de_mirage.json
with open("src/CsBotManager/MapProfiles/de_mirage.json", "r", encoding="utf-8") as f:
    de_mirage = json.load(f)

# Carrega auditoria da Fase 1.5
with open("docs/fase_1_5/mirage_spot_audit.json", "r", encoding="utf-8") as f:
    fase15_audit = json.load(f)["audit"]
audit_map = {x["SpotId"]: x for x in fase15_audit}

# Carrega observações de gameplay da Fase 1.6.2
with open("docs/fase_1_6/profile_v2_observed_spots.json", "r", encoding="utf-8") as f:
    obs_data = json.load(f)["SpotBreakdown"]

# 8 spots sensíveis para homologação presencial
SENSITIVE_8_SPOTS = {
    "ct_a_ticket_passive",
    "ct_a_firebox_oneanddone",
    "ct_a_ninja_hide",
    "ct_mid_window_crouch",
    "ct_b_van_peek",
    "tr_staging_a_ramp",
    "tr_staging_palace_room",
    "ct_retake_a_connector"
}

# 6 spots com evidência insuficiente
INSUFFICIENT_6_SPOTS = {
    "tr_staging_top_mid_boxes",
    "tr_staging_t_roof",
    "tr_spawn_safe",
    "tr_exec_b_van_clear",
    "ct_retake_b_entry",
    "ct_retake_b_awp_cover"
}

# 12 spots classificados como SMALL_ADJUSTMENT
SMALL_ADJUSTMENT_12_SPOTS = {
    "ct_b_site_default_crouch",
    "ct_b_market_door",
    "tr_staging_b_apartments_house",
    "tr_exec_a_site_default",
    "tr_exec_a_stairs_clear",
    "tr_exec_mid_connector_push",
    "tr_exec_b_site_plant",
    "tr_exec_b_market_push",
    "ct_retake_a_stairs",
    "ct_retake_a_defuse_cover",
    "ct_retake_b_market",
    "ct_retake_b_defuse_cover"
}

# Mapeamento semântico explícito de todos os 45 spots (sem dedução por prefixo ou substring)
# side: CounterTerrorist / Terrorist
# associated_bombsite: None, A, B, Mid, Dynamic
# usage: Spawn, Staging, Execute, Hold, Fallback, Plant, Retake, Lurk, Cover, FlankWatch, Defuse, Save
# allowed_roles: AWPer, EntryFragger, Rotator, Anchor
spot_semantic_defs = {
    "ct_a_ticket_passive": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Hold",
        "allowed_roles": ["AWPer", "Anchor", "Rotator"]
    },
    "ct_a_firebox_oneanddone": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Hold",
        "allowed_roles": ["Anchor", "EntryFragger"]
    },
    "ct_a_ninja_hide": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Hold",
        "allowed_roles": ["Anchor", "Rotator"]
    },
    "ct_a_triple_jiggle": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Hold",
        "allowed_roles": ["AWPer", "Anchor", "Rotator"]
    },
    "ct_a_stairs_cross": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Hold",
        "allowed_roles": ["Anchor", "Rotator"]
    },
    "ct_a_jungle_support": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Hold",
        "allowed_roles": ["AWPer", "Rotator", "Anchor"]
    },
    "ct_a_palace_close_poke": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Hold",
        "allowed_roles": ["Anchor", "EntryFragger"]
    },
    "ct_mid_window_crouch": {
        "side": "CounterTerrorist", "associated_bombsite": "Mid", "usage": "Hold",
        "allowed_roles": ["AWPer", "Rotator"]
    },
    "ct_mid_window_deep_awp": {
        "side": "CounterTerrorist", "associated_bombsite": "Mid", "usage": "Hold",
        "allowed_roles": ["AWPer"]
    },
    "ct_mid_connector_headshot": {
        "side": "CounterTerrorist", "associated_bombsite": "Mid", "usage": "Hold",
        "allowed_roles": ["AWPer", "Rotator", "Anchor"]
    },
    "ct_mid_short_catwalk": {
        "side": "CounterTerrorist", "associated_bombsite": "Mid", "usage": "Hold",
        "allowed_roles": ["Rotator", "Anchor"]
    },
    "ct_mid_underpass_peek": {
        "side": "CounterTerrorist", "associated_bombsite": "Mid", "usage": "Hold",
        "allowed_roles": ["Rotator", "EntryFragger"]
    },
    "ct_b_van_peek": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Hold",
        "allowed_roles": ["AWPer", "Anchor", "Rotator"]
    },
    "ct_b_bench_deep": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Hold",
        "allowed_roles": ["Anchor", "Rotator"]
    },
    "ct_b_site_default_crouch": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Hold",
        "allowed_roles": ["Anchor", "Rotator"]
    },
    "ct_b_market_window": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Hold",
        "allowed_roles": ["AWPer", "Rotator"]
    },
    "ct_b_market_door": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Hold",
        "allowed_roles": ["Anchor", "Rotator"]
    },
    "ct_b_short_corner": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Hold",
        "allowed_roles": ["Anchor", "Rotator"]
    },
    "ct_spawn_safe": {
        "side": "CounterTerrorist", "associated_bombsite": "None", "usage": "Spawn",
        "allowed_roles": ["AWPer", "EntryFragger", "Rotator", "Anchor"]
    },
    "ct_jungle_safe": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Fallback",
        "allowed_roles": ["AWPer", "Rotator", "Anchor"]
    },
    "tr_staging_a_ramp": {
        "side": "Terrorist", "associated_bombsite": "A", "usage": "Staging",
        "allowed_roles": ["AWPer", "EntryFragger", "Rotator", "Anchor"]
    },
    "tr_staging_palace_room": {
        "side": "Terrorist", "associated_bombsite": "A", "usage": "Staging",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "tr_staging_top_mid_boxes": {
        "side": "Terrorist", "associated_bombsite": "Mid", "usage": "Staging",
        "allowed_roles": ["AWPer", "EntryFragger", "Rotator"]
    },
    "tr_staging_underpass_top": {
        "side": "Terrorist", "associated_bombsite": "Mid", "usage": "Staging",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "tr_staging_b_apartments_house": {
        "side": "Terrorist", "associated_bombsite": "B", "usage": "Staging",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "tr_staging_b_apartments_kitchen": {
        "side": "Terrorist", "associated_bombsite": "B", "usage": "Staging",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "tr_staging_t_roof": {
        "side": "Terrorist", "associated_bombsite": "Mid", "usage": "Staging",
        "allowed_roles": ["AWPer", "Rotator"]
    },
    "tr_spawn_safe": {
        "side": "Terrorist", "associated_bombsite": "None", "usage": "Spawn",
        "allowed_roles": ["AWPer", "EntryFragger", "Rotator", "Anchor"]
    },
    "tr_exec_a_site_default": {
        "side": "Terrorist", "associated_bombsite": "A", "usage": "Execute",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "tr_exec_a_triple_clear": {
        "side": "Terrorist", "associated_bombsite": "A", "usage": "Execute",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "tr_exec_a_stairs_clear": {
        "side": "Terrorist", "associated_bombsite": "A", "usage": "Execute",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "tr_exec_mid_connector_push": {
        "side": "Terrorist", "associated_bombsite": "Mid", "usage": "Execute",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "tr_exec_b_site_plant": {
        "side": "Terrorist", "associated_bombsite": "B", "usage": "Plant",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "tr_exec_b_van_clear": {
        "side": "Terrorist", "associated_bombsite": "B", "usage": "Execute",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "tr_exec_b_market_push": {
        "side": "Terrorist", "associated_bombsite": "B", "usage": "Execute",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "ct_retake_a_connector": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Retake",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "ct_retake_a_stairs": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Retake",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "ct_retake_a_jungle": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Retake",
        "allowed_roles": ["AWPer", "Rotator", "Anchor"]
    },
    "ct_retake_a_ticket": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Retake",
        "allowed_roles": ["AWPer", "Rotator", "Anchor"]
    },
    "ct_retake_a_defuse_cover": {
        "side": "CounterTerrorist", "associated_bombsite": "A", "usage": "Defuse",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "ct_retake_b_market": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Retake",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "ct_retake_b_short": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Retake",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "ct_retake_b_entry": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Retake",
        "allowed_roles": ["EntryFragger", "Rotator"]
    },
    "ct_retake_b_defuse_cover": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "Defuse",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"]
    },
    "ct_retake_b_awp_cover": {
        "side": "CounterTerrorist", "associated_bombsite": "B", "usage": "FlankWatch",
        "allowed_roles": ["AWPer", "Anchor"]
    }
}

uniform_spots = []
confidence_records = []

for s in de_mirage["spots"]:
    sid = s["id"]
    s_meta = spot_semantic_defs[sid]
    audit_item = audit_map.get(sid, {})
    obs_item = obs_data.get(sid, {})
    is_observed_in_gameplay = (obs_item.get("Classification") == "OBSERVED_IN_GAMEPLAY")
    
    # Determinação de ValidationStatus e Confidence
    if sid in SENSITIVE_8_SPOTS:
        val_status = "PENDING_HUMAN_REVIEW"
        confidence = "MEDIUM" # Cluster forte e runtime local OK, mas aprovação humana pendente
        conf_reason = "Cluster profissional e navegação local aprovados, porém pendente de inspeção visual humana no CS2."
    elif sid in INSUFFICIENT_6_SPOTS:
        val_status = "INSUFFICIENT_EVIDENCE"
        confidence = "LOW"
        conf_reason = "Evidência profissional insuficiente (<100 instâncias ou desvio amostral elevado)."
    elif is_observed_in_gameplay:
        val_status = "RUNTIME_OBSERVED"
        confidence = "HIGH"
        conf_reason = "Cluster profissional validado e observado com sucesso em partida normal (zero bloqueio de geometria)."
    else:
        # Não observado na partida normal
        val_status = "RUNTIME_NOT_OBSERVED"
        if audit_item.get("CurrentClassification") in ["VALID", "SMALL_ADJUSTMENT"]:
            confidence = "HIGH"
            conf_reason = "Cluster profissional e navegação estática válidos, porém não acionado na amostragem da partida normal."
        else:
            confidence = "MEDIUM"
            conf_reason = "Spot corrigido validado localmente, aguardando maior volume de rounds para observação em jogo."

    uniform_spot = {
        "id": sid,
        "name": s["name"],
        "sector": s["sector"],
        "side": s_meta["side"],
        "associated_bombsite": s_meta["associated_bombsite"],
        "usage": s_meta["usage"],
        "allowed_roles": s_meta["allowed_roles"],
        "x": s["x"],
        "y": s["y"],
        "z": s["z"],
        "pitch": s["pitch"],
        "yaw": s["yaw"],
        "recommended_stance": s["recommended_stance"],
        "is_off_angle": s["is_off_angle"],
        "fallback_spot_id": s.get("fallback_spot_id"),
        "confidence": confidence,
        "validation_status": val_status
    }
    uniform_spots.append(uniform_spot)
    
    confidence_records.append({
        "SpotId": sid,
        "Name": s["name"],
        "Side": s_meta["side"],
        "AssociatedBombsite": s_meta["associated_bombsite"],
        "Usage": s_meta["usage"],
        "Confidence": confidence,
        "ValidationStatus": val_status,
        "ObservedInMatch": is_observed_in_gameplay,
        "AuditClassification": audit_item.get("CurrentClassification", "UNKNOWN"),
        "EvidenceCount": audit_item.get("EvidenceCount", 0),
        "DemoDiversity": audit_item.get("DemoDiversity", 0),
        "PlayerDiversity": audit_item.get("PlayerDiversity", 0),
        "DecisionReason": conf_reason
    })

# Salva mirage_uniform_spot_schema.json
uniform_schema_payload = {
    "generated_at": datetime.now().isoformat(),
    "map": "de_mirage",
    "total_spots": len(uniform_spots),
    "schema_version": "2.0_UNIFORM",
    "spots": uniform_spots
}

with open("docs/fase_1_7/mirage_uniform_spot_schema.json", "w", encoding="utf-8") as f:
    json.dump(uniform_schema_payload, f, indent=2)

print("Saved docs/fase_1_7/mirage_uniform_spot_schema.json")

# Salva mirage_spot_confidence.json
confidence_payload = {
    "generated_at": datetime.now().isoformat(),
    "map": "de_mirage",
    "total_spots": len(confidence_records),
    "confidence_summary": {
        "HIGH": sum(1 for x in confidence_records if x["Confidence"] == "HIGH"),
        "MEDIUM": sum(1 for x in confidence_records if x["Confidence"] == "MEDIUM"),
        "LOW": sum(1 for x in confidence_records if x["Confidence"] == "LOW")
    },
    "validation_status_summary": {
        "RUNTIME_OBSERVED": sum(1 for x in confidence_records if x["ValidationStatus"] == "RUNTIME_OBSERVED"),
        "RUNTIME_NOT_OBSERVED": sum(1 for x in confidence_records if x["ValidationStatus"] == "RUNTIME_NOT_OBSERVED"),
        "PENDING_HUMAN_REVIEW": sum(1 for x in confidence_records if x["ValidationStatus"] == "PENDING_HUMAN_REVIEW"),
        "INSUFFICIENT_EVIDENCE": sum(1 for x in confidence_records if x["ValidationStatus"] == "INSUFFICIENT_EVIDENCE"),
        "APPROVED_BY_USER": sum(1 for x in confidence_records if x["ValidationStatus"] == "APPROVED_BY_USER"),
        "REJECTED_BY_USER": sum(1 for x in confidence_records if x["ValidationStatus"] == "REJECTED_BY_USER")
    },
    "spots": confidence_records
}

with open("docs/fase_1_7/mirage_spot_confidence.json", "w", encoding="utf-8") as f:
    json.dump(confidence_payload, f, indent=2)

print("Saved docs/fase_1_7/mirage_spot_confidence.json")
