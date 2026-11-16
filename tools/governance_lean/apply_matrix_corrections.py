import json
from pathlib import Path

matrix_path = Path("datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json")
data = json.loads(matrix_path.read_text(encoding="utf-8"))

# Ajuste 1: FACEIT Downloads API - Quota de download
for s in data["sources"]:
    if s["source_id"] == "A":
        for sub in s["sub_sources"]:
            if sub["sub_source_id"] == "A2":
                sub["application_process"]["tiers"] = "DOWNLOAD_QUOTA_UNVERIFIED"
                sub["application_process"]["proven_features"] = [
                    "Downloads API com URL assinada temporaria",
                    "Token exclusivo com scope de download",
                    "Candidatura obrigatoria por formulario (fce.gg/downloads-api-application)",
                    "Prazo esperado de resposta de 30 dias documentado"
                ]
            if sub["sub_source_id"] == "A1":
                sub["rank_classification"] = {
                    "bucket": "FACEIT_LEVEL_4_7 = INTERMEDIATE_CANDIDATE_BUCKET",
                    "cross_platform_equivalence": "CROSS_PLATFORM_EQUIVALENCE = UNVERIFIED"
                }

# Ajuste 3, 4, 5: Gamers Club
for s in data["sources"]:
    if s["source_id"] == "E":
        for sub in s["sub_sources"]:
            sub["rank_classification"] = {
                "bucket": "GC_LEVEL_8_15 = INTERMEDIATE_CANDIDATE_BUCKET",
                "equivalence_to_valve_ranks": "EQUIVALENCE_TO_VALVE_RANKS = UNVERIFIED"
            }
            sub["access_status"] = {
                "research_batch": "GAMERSCLUB_RESEARCH_BATCH = PARTNERSHIP_HYPOTHESIS",
                "public_bulk_api": "PUBLIC_BULK_API = NOT_FOUND_IN_OFFICIAL_DOCUMENTATION"
            }
            sub["tactical_standardization"] = {
                "setup_2_1_2_claim": "HYPOTHESIS_TO_TEST (Requer medicao empirica sobre partidas reais)"
            }

# Atualiza justificativa da recomendacao estrategica
data["weighted_scoring_matrix"]["strategic_recommendation"]["candidate_buckets"] = {
    "faceit_level_4_7": "INTERMEDIATE_CANDIDATE_BUCKET (CROSS_PLATFORM_EQUIVALENCE = UNVERIFIED)",
    "gc_level_8_15": "INTERMEDIATE_CANDIDATE_BUCKET (EQUIVALENCE_TO_VALVE_RANKS = UNVERIFIED)",
    "tactical_hypothesis": "HYPOTHESIS_TO_TEST",
    "faceit_quota": "DOWNLOAD_QUOTA_UNVERIFIED",
    "gamersclub_api": "GAMERSCLUB_RESEARCH_BATCH = PARTNERSHIP_HYPOTHESIS / PUBLIC_BULK_API = NOT_FOUND_IN_OFFICIAL_DOCUMENTATION"
}

matrix_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"status": "PASS", "matrix_corrected": True}, indent=2))
