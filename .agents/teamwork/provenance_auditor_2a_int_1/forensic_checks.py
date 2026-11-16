"""Verificador forense (SOMENTE LEITURA) — FASE 2A-INTERMEDIATE / CsBot.

Não escreve fora do próprio diretório do auditor. Recalcula hashes e contagens
diretamente do disco. Uso:
    python forensic_checks.py --out checks_result.json
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
RESULT = {"generated_by": "provenance_auditor_2a_int_1", "read_only": True}


def sha256_of(abspath, bufsize=1 << 20):
    h = hashlib.sha256()
    with open(abspath, "rb") as fh:
        while True:
            b = fh.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


# --------------------------------------------------------------------------
# B) Integridade do corpus profissional — recálculo SHA-256 das referências
# --------------------------------------------------------------------------
def check_b_professional_corpus():
    man = load("datasets/mirage_domains/professional_manifest_reference.json")
    rows = []
    for r in man["references"]:
        rel = r["repo_relative_path"].replace("\\", "/")
        ab = os.path.join(ROOT, rel)
        exists = os.path.isfile(ab)
        size = os.path.getsize(ab) if exists else None
        digest = sha256_of(ab) if exists else None
        rows.append({
            "reference_id": r["reference_id"],
            "repo_relative_path": rel,
            "declared_size": r["size_bytes"],
            "actual_size": size,
            "declared_sha256": r["sha256"],
            "actual_sha256": digest,
            "size_match": size == r["size_bytes"],
            "hash_match": digest == r["sha256"].lower() if digest else False,
            "exists": exists,
        })
    matched = sum(1 for x in rows if x["hash_match"] and x["size_match"])
    ids = [x["reference_id"] for x in rows]
    paths = [x["repo_relative_path"] for x in rows]
    shards = [p for p in paths if re.search(r"shard_00[0-5]\.parquet$", p)]
    sidecars = [p for p in paths if re.search(r"label_sidecar_v2/shard_00[0-5]_labels\.parquet$", p)]
    out = {
        "references_total": len(rows),
        "references_hash_and_size_match": matched,
        "ratio": f"({matched}/{len(rows)})",
        "all_match": matched == len(rows),
        "reference_ids": ids,
        "shards_in_sample": shards,
        "sidecars_in_sample": sidecars,
        "shards_n": len(shards),
        "sidecars_n": len(sidecars),
        "rows": rows,
    }
    # contagem de arquivos em datasets/mirage_v2 (read-only enumeration)
    base = os.path.join(ROOT, "datasets/mirage_v2")
    n_files = 0
    n_bytes = 0
    for dp, _dn, fn in os.walk(base):
        for f in fn:
            n_files += 1
            n_bytes += os.path.getsize(os.path.join(dp, f))
    out["mirage_v2_enumeration"] = {"files": n_files, "bytes": n_bytes}

    # full_training
    ft = os.path.join(ROOT, "training_runs/positioning_v2_real_temporal/full_training")
    ft_files = []
    if os.path.isdir(ft):
        for dp, _dn, fn in os.walk(ft):
            for f in fn:
                p = os.path.join(dp, f)
                ft_files.append({
                    "path": os.path.relpath(p, ROOT).replace("\\", "/"),
                    "size_bytes": os.path.getsize(p),
                })
    out["full_training"] = {
        "n_files": len(ft_files),
        "files_nonzero": sum(1 for x in ft_files if x["size_bytes"] > 0),
        "ratio_nonzero": f"({sum(1 for x in ft_files if x['size_bytes'] > 0)}/{len(ft_files)})",
    }
    RESULT["B_professional_corpus"] = out

    # professional/ contém apenas README.md
    pdir = os.path.join(ROOT, "datasets/mirage_domains/professional")
    entries = sorted(os.listdir(pdir))
    RESULT["B_professional_dir_only_readme"] = {
        "entries": entries,
        "only_readme": entries == ["README.md"],
    }
    return out


# --------------------------------------------------------------------------
# C) Não-fabricação: manifests vazios + contabilidade (0/0)
# --------------------------------------------------------------------------
def find_key(obj, key, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k == key:
                hits.append((p, v))
            hits.extend(find_key(v, key, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(find_key(v, key, f"{path}[{i}]"))
    return hits


def check_c_no_fabrication():
    manifests = [
        "datasets/mirage_domains/intermediate_competitive/intermediate_demo_inventory_v1.json",
        "datasets/mirage_domains/intermediate_competitive/intermediate_npz_manifest_v1.json",
        "datasets/mirage_domains/intermediate_competitive/pilot_download_manifest.json",
        "datasets/mirage_domains/intermediate_competitive/quarantine_manifest.json",
    ]
    out = {"manifests": []}
    for rel in manifests:
        d = load(rel)
        rec = {k: v for k, v in d.items() if k.lower() in ("records", "demos", "entries", "items", "quarantine_records", "downloaded", "npz_records")}
        rec_lens = {k: len(v) for k, v in rec.items() if isinstance(v, list)}
        nums = [(p, v) for p, v in find_key(d, "numerator")]
        dens = [(p, v) for p, v in find_key(d, "denominator")]
        ratios = [(p, v) for p, v in find_key(d, "ratio")]
        counts = [(p, v) for p, v in find_key(d, "count")]
        entries = {
            "path": rel,
            "top_keys": list(d.keys()),
            "record_lists": rec_lens,
            "all_records_empty": all(v == 0 for v in rec_lens.values()) if rec_lens else None,
            "numerator_fields": [(p, v) for p, v in nums],
            "denominator_fields": [(p, v) for p, v in dens],
            "ratio_fields": [(p, v) for p, v in ratios],
            "zero_counts": [(p, v) for p, v in counts if v == 0][:20],
            "nonzero_counts": [(p, v) for p, v in counts if v not in (0, None)][:20],
        }
        out["manifests"].append(entries)
    RESULT["C_no_fabrication"] = out
    return out


# --------------------------------------------------------------------------
# D) Contrato de domínios (§4)
# --------------------------------------------------------------------------
REQUIRED_FIELDS_4 = [
    "domain_id", "platform", "rank_system", "skill_level", "elo_or_rating",
    "rank_at_collection_time", "rank_at_match_time_if_available",
    "map_specific_rank", "map_name", "match_date", "region", "source",
    "source_license", "acquisition_method", "consent_type",
    "metadata_confidence", "exclusion_reason",
]
REQUIRED_DOMAINS = ["PROFESSIONAL", "INTERMEDIATE_COMPETITIVE", "UNKNOWN"]
REQUIRED_SUBDOMAINS = [
    "PROFESSIONAL_HLTV", "FACEIT_LEVEL_5_6", "FACEIT_LEVEL_7_8",
    "FACEIT_LEVEL_9_10", "VALVE_COMPETITIVE_MAP_RANK", "VALVE_PREMIER_RATING",
    "VALVE_OPT_IN_UNKNOWN_RANK",
]


def check_d_domain_contract():
    d = load("datasets/mirage_domains/domain_contract_v1.json")
    flat = json.dumps(d, ensure_ascii=False)
    out = {"top_keys": list(d.keys())}
    out["domains_present"] = {x: (x in flat) for x in REQUIRED_DOMAINS}
    out["subdomains_present"] = {x: (x in flat) for x in REQUIRED_SUBDOMAINS}
    out["fields"] = {x: (x in flat) for x in REQUIRED_FIELDS_4}
    out["fields_ratio"] = f"({sum(1 for v in out['fields'].values() if v)}/{len(REQUIRED_FIELDS_4)})"
    out["faceit_1_4_excluded_mention"] = len(re.findall(r"1[–\-]4|1-4", flat))
    out["premier_status_mentions"] = re.findall(r"NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT", flat)
    RESULT["D_domain_contract"] = out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="checks_result.json")
    a = ap.parse_args()
    check_b_professional_corpus()
    check_c_no_fabrication()
    check_d_domain_contract()
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, a.out), "w", encoding="utf-8") as fh:
        json.dump(RESULT, fh, indent=1, ensure_ascii=False)
    print("wrote", os.path.join(here, a.out))


if __name__ == "__main__":
    main()
