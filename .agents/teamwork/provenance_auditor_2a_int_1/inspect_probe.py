"""Sonda de inspeção (somente leitura) dos artefatos da FASE 2A-INTERMEDIATE.
Gravado em .agents/teamwork/provenance_auditor_2a_int_1/ ; lê apenas.
"""
import json
import os
import sys

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"


def load(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def show(rel):
    d = load(rel)
    print("=" * 90)
    print("FILE:", rel)
    print("TOPKEYS:", list(d.keys()) if isinstance(d, dict) else type(d).__name__)
    return d


if __name__ == "__main__":
    d = show("datasets/mirage_domains/professional_manifest_reference.json")
    print("verified_corpus_counts:", json.dumps(d["verified_corpus_counts"], indent=1, ensure_ascii=False))
    print("totals:", json.dumps(d["totals"], indent=1, ensure_ascii=False))
    print("n_references:", len(d["references"]))
    print("ref[0]:", json.dumps(d["references"][0], indent=1, ensure_ascii=False))
    keysets = {}
    for r in d["references"]:
        keysets.setdefault(tuple(sorted(r.keys())), 0)
        keysets[tuple(sorted(r.keys()))] += 1
    print("ref_keysets:", keysets)
    print("logical_reference_point:", d["logical_reference_point"])
    print("counts_verification_method:", d["counts_verification_method"])
    print("percentages_note:", d["percentages_note"])
    print("governance_notes:", json.dumps(d["governance_notes"], indent=1, ensure_ascii=False)[:1500])
