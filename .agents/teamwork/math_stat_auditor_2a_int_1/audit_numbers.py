import json, os, collections

STUDY = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/training_runs/intermediate_domain_study"
FILES = ["ct_standardization_analysis.json","tr_standardization_analysis.json","professional_vs_intermediate.json",
         "spot_domain_coverage.json","unmapped_intermediate_clusters.json","pilot_corpus_quality.json"]

ALLOWED_NUMERIC_FIELDS = {
  "numerator","denominator","size_bytes","metric_count","spec_enumerated","dispatch_declared",
  "metrics_total","metrics_executable","metrics_not_executable","metrics_compared",
  "jsd_computed","wasserstein_computed","bootstrap_intervals_computed","effective_sample_size_computed",
  "clusters_found","classification_counts_denominator","spots_promoted","spots_removed","spots_added",
  "spots_appended_to_catalog","criteria_total","criteria_passed","criteria_failed","criteria_not_executable",
  "problems_total","problems_flagged","problems_not_executable","classes_defined","classes_with_computed_support",
  "spot_type_distribution_sum","semantic_entries","supervision_entries","spots_array_length",
  "catalog_total_spots_field","spots_with_support","spots_with_strict_na","sum_support_sequences_total",
  "eligible_sequences_artifact_value","support_ids_in_supervision_report","support_ids_in_legacy_v2_distribution",
  "count","unidentified_count","expected_count_from_dispatch","denominator","catalog_size_bytes",
  "sample_rate_hz","frame_interval_ms","n_resamples_declared","n_units_available","threshold",
  "total","train","validation","test","value_total","dem_files","npz_files","archive_files","other_files",
  "demos_available","rounds_available","matches_available","players_with_verified_rank_available",
  "clusters_recorded","minimum_episodes","minimum_matches","minimum_players","maximum_radius_units",
  "preferred_radius_units","minimum_demos","total_episodes","unique_demos","unique_players","radius",
  "POSITION_PROFILE","CLEARANCE_WAYPOINT","STAGING_POSITION","PLANT_POSITION","TRANSITION_POINT",
  "PROFESSIONAL_CONFIRMED","INSUFFICIENT_SUPPORT","denominator_active_classes",
}

print("="*100)
print("CHECK K — TODO CAMPO NUMERICO FORA DA LISTA DE CAMPOS ESTRUTURAIS (procura de valor medido)")
print("="*100)
findings = collections.Counter()
examples = {}
for f in FILES:
    d = json.loads(open(os.path.join(STUDY, f), "rb").read().decode("utf-8"))
    def walk(n, path):
        if isinstance(n, dict):
            for k, v in n.items():
                p = path + "." + k
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if k not in ALLOWED_NUMERIC_FIELDS:
                        findings[(f, k)] += 1
                        examples.setdefault((f, k), (p, v))
                walk(v, p)
        elif isinstance(n, list):
            for i, v in enumerate(n):
                walk(v, path + "[%d]" % i)
    walk(d, "")
if not findings:
    print("NENHUM campo numerico fora da lista estrutural.")
for (f, k), c in sorted(findings.items()):
    print("  %-38s campo='%s' ocorrencias=%d  exemplo=%s" % (f, k, c, examples[(f, k)]))

print()
print("="*100)
print("CHECK L — CAMPOS 'value' NUMERICOS (fora de numerator/denominator) E SEU STATUS")
print("="*100)
cnt = collections.Counter()
for f in FILES:
    d = json.loads(open(os.path.join(STUDY, f), "rb").read().decode("utf-8"))
    def walk(n, path, parentkey):
        if isinstance(n, dict):
            if "value" in n and isinstance(n["value"], (int, float)) and not isinstance(n["value"], bool):
                st = n.get("metric_status") or n.get("status") or n.get("reason_code") or "(sem status)"
                cnt[(f, parentkey, st)] += 1
            for k, v in n.items():
                walk(v, path + "." + k, k)
        elif isinstance(n, list):
            for i, v in enumerate(n):
                walk(v, path + "[%d]" % i, parentkey)
    walk(d, "", "")
for (f, pk, st), c in sorted(cnt.items()):
    print("  %-38s bloco='%-42s' status='%s' -> %d" % (f, pk, st, c))
