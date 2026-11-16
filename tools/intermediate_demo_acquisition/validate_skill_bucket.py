#!/usr/bin/env python3
"""
validate_skill_bucket.py — Validação do bucket de habilidade contra o contrato de domínios.

FASE 2A-INTERMEDIATE · `tools/intermediate_demo_acquisition/` · §4, §6, §9, §20 (testes 3, 4, 5, 6).

O que faz
---------
Lê `datasets/mirage_domains/domain_contract_v1.json` e decide, para cada demo candidata, se ela pode
entrar no corpus principal do piloto intermediário. Implementa literalmente as regras da §6:

- bucket de skill resolvido a partir do sistema de rank ORIGINAL (sem conversão);
- aceitação apenas de buckets com `inclusion_policy = INCLUDED_PILOT`;
- rejeição de bucket `EXCLUDED_PILOT`;
- rejeição de bucket `NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT` (Premier);
- rejeição de partida que misture bucket incluído com bucket excluído;
- rejeição de promoção de `UNKNOWN` para `INTERMEDIATE_COMPETITIVE`;
- rejeição de rank derivado por conversão (teste 4: FACEIT ≠> Valve; teste 5: Premier ≠> Competitive);
- rejeição de mapa diferente de `de_mirage`;
- rejeição de campo obrigatório ausente;
- rejeição de URL assinada em `source_url_reference`.

Modos
-----
`--records PATH`  valida um JSON/JSONL real de candidatas.
`--self-test`     executa 14 casos determinísticos embutidos e falha (exit 1) se qualquer decisão
                  divergir do esperado. Nenhuma rede, nenhuma escrita em `datasets/`.
(padrão)          lista as regras carregadas do contrato, sem processar registros.

Códigos de saída
---------------------
0 = sucesso · 1 = erro de validação · 2 = erro de uso
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
DEFAULT_CONTRACT_PATH = REPO_ROOT / "datasets" / "mirage_domains" / "domain_contract_v1.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

MANDATORY_FIELDS = [
    "domain_id",
    "platform",
    "rank_system",
    "skill_level",
    "elo_or_rating",
    "rank_at_collection_time",
    "rank_at_match_time_if_available",
    "map_specific_rank",
    "map_name",
    "match_date",
    "region",
    "source",
    "source_license",
    "acquisition_method",
    "consent_type",
    "metadata_confidence",
    "exclusion_reason",
]

FACEIT_BUCKET_BY_LEVEL = {
    1: "FACEIT_LEVEL_1_4",
    2: "FACEIT_LEVEL_1_4",
    3: "FACEIT_LEVEL_1_4",
    4: "FACEIT_LEVEL_1_4",
    5: "FACEIT_LEVEL_5_6",
    6: "FACEIT_LEVEL_5_6",
    7: "FACEIT_LEVEL_7_8",
    8: "FACEIT_LEVEL_7_8",
    9: "FACEIT_LEVEL_9_10",
    10: "FACEIT_LEVEL_9_10",
}

CONVERSION_TRAP_FIELDS = {
    "FACEIT_LEVEL": ["valve_competitive_rank", "premier_rating", "converted_valve_rank"],
    "FACEIT_ELO": ["valve_competitive_rank", "premier_rating", "converted_valve_rank"],
    "VALVE_COMPETITIVE_MAP_RANK": ["faceit_level", "faceit_elo", "converted_faceit_level"],
    "VALVE_PREMIER_RATING": ["faceit_level", "faceit_elo", "valve_competitive_rank", "converted_competitive_rank"],
}

SIGNED_URL_MARKERS = ("x-amz-signature", "signature=", "sig=", "token=", "expires=", "policy=", "key-pair-id")
STEAMID64_RE = re.compile(r"\b7656119\d{10}\b")
REDACTION_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)(cookie\s*:\s*)([^\s\"']+)"),
    re.compile(r"(?i)\b(access_token|api_key|apikey|token|password|secret)\b(\s*[=:]\s*)([^\s&\"',}]+)"),
]


class ValidationError(Exception):
    """Erro de validação (exit code 1)."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str) -> str:
    out = str(text)
    for pattern in REDACTION_PATTERNS:
        out = pattern.sub(lambda m: f"{m.group(1)}[REDACTED]", out)
    return out


def load_contract(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"contrato de domínios ausente: {path}")
    contract = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict) or "subdomains" not in contract:
        raise ValidationError("contrato inválido: campo 'subdomains' ausente.")
    conversions = (contract.get("rank_conversion_policy") or {}).get("conversions_allowed")
    if conversions not in ([], None):
        raise ValidationError("contrato inválido: conversions_allowed deve ser lista vazia.")
    return contract


def resolve_bucket(record: Dict[str, Any], contract: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    """Resolve o bucket a partir do sistema ORIGINAL. Retorna (bucket, problemas)."""
    problems: List[str] = []
    rank_system = str(record.get("rank_system") or "").strip()
    if not rank_system:
        return None, ["MISSING_RANK_SYSTEM"]

    known_systems = {
        "FACEIT_LEVEL",
        "FACEIT_ELO",
        "VALVE_COMPETITIVE_MAP_RANK",
        "VALVE_PREMIER_RATING",
        "PROFESSIONAL_HLTV",
        "NONE",
    }
    if rank_system not in known_systems:
        return None, [f"UNKNOWN_RANK_SYSTEM:{rank_system}"]

    if rank_system == "NONE":
        return "UNKNOWN", problems

    if rank_system == "PROFESSIONAL_HLTV":
        return "PROFESSIONAL_HLTV", problems

    if rank_system in ("FACEIT_LEVEL", "FACEIT_ELO"):
        level = record.get("skill_level")
        try:
            level_int = int(level)
        except (TypeError, ValueError):
            return None, ["MISSING_OR_INVALID_FACEIT_LEVEL"]
        bucket = FACEIT_BUCKET_BY_LEVEL.get(level_int)
        if bucket is None:
            return None, [f"FACEIT_LEVEL_OUT_OF_RANGE:{level_int}"]
        return bucket, problems

    if rank_system == "VALVE_COMPETITIVE_MAP_RANK":
        candidates = {
            item["rank_code"]
            for item in (contract.get("valve_competitive_candidates") or {}).get("candidate_ranks", [])
        }
        level = str(record.get("skill_level") or "").strip().upper()
        if level not in candidates:
            return None, [f"VALVE_COMPETITIVE_RANK_OUTSIDE_CANDIDATE_SET:{level or 'EMPTY'}"]
        if not record.get("map_specific_rank"):
            return None, ["MISSING_MAP_SPECIFIC_RANK"]
        return "VALVE_COMPETITIVE_MAP_RANK", problems

    if rank_system == "VALVE_PREMIER_RATING":
        return "VALVE_PREMIER_RATING", problems

    return None, ["UNRESOLVED_BUCKET"]


def evaluate(record: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
    """Decide ACCEPT/REJECT para um registro de metadado, com rastro dos motivos."""
    reasons: List[str] = []

    # (1) Campos obrigatórios: a chave precisa existir (null é permitido quando o contrato permite).
    for field in MANDATORY_FIELDS:
        if field not in record:
            reasons.append(f"MISSING_MANDATORY_FIELD:{field}")

    # (2) Mapa.
    if record.get("map_name") != "de_mirage":
        reasons.append("NON_MIRAGE_DEMO")

    # (3) Conversão de rank — proibida.
    rank_system = str(record.get("rank_system") or "")
    for trap in CONVERSION_TRAP_FIELDS.get(rank_system, []):
        if record.get(trap) not in (None, "", 0):
            reasons.append(f"RANK_CONVERSION_PROHIBITED:{trap}")

    # (4) Promoção de UNKNOWN.
    if record.get("domain_id") == "INTERMEDIATE_COMPETITIVE" and rank_system in ("", "NONE"):
        reasons.append("UNKNOWN_DOMAIN_PROMOTED")

    # (5) Bucket e política de inclusão.
    bucket, bucket_problems = resolve_bucket(record, contract)
    reasons.extend(bucket_problems)

    subdomains = contract.get("subdomains") or {}
    faceit_buckets = contract.get("faceit_buckets") or {}
    policy = None
    if bucket and bucket in subdomains:
        policy = subdomains[bucket].get("inclusion_policy")
    elif bucket and bucket in faceit_buckets:
        # Buckets como FACEIT_LEVEL_1_4 são declarados apenas em faceit_buckets (não são subdomínio
        # formal), mas trazem inclusion_policy explícita — respeitá-la evita falso "política não resolvida".
        policy = faceit_buckets[bucket].get("inclusion_policy")
    elif bucket == "UNKNOWN":
        policy = "EXCLUDED_PILOT"

    if bucket and policy != "INCLUDED_PILOT":
        if policy == "NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT":
            reasons.append(f"BUCKET_NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT:{bucket}")
        elif policy == "EXCLUDED_PILOT":
            reasons.append(f"BUCKET_EXCLUDED_FROM_PRIMARY_CORPUS:{bucket}")
        else:
            reasons.append(f"BUCKET_POLICY_UNRESOLVED:{bucket}:{policy}")

    # (6) Mistura de buckets entre jogadores: incluído + excluído é rejeitado.
    players = record.get("player_skill_levels") or []
    if isinstance(players, list) and players and rank_system in ("FACEIT_LEVEL", "FACEIT_ELO"):
        player_buckets = set()
        for player in players:
            if not isinstance(player, dict):
                continue
            try:
                level = int(player.get("skill_level"))
            except (TypeError, ValueError):
                continue
            mapped = FACEIT_BUCKET_BY_LEVEL.get(level)
            if mapped:
                player_buckets.add(mapped)
        included = {
            name for name, sub in subdomains.items() if sub.get("inclusion_policy") == "INCLUDED_PILOT"
        }
        if (player_buckets & included) and (player_buckets - included):
            reasons.append("BUCKET_MIXED_INCLUDED_EXCLUDED")

    # (7) URL assinada.
    reference = str(record.get("source_url_reference") or "")
    for marker in SIGNED_URL_MARKERS:
        if marker in reference.lower():
            reasons.append(f"SIGNED_URL_REFERENCE_PROHIBITED:{marker.strip('=')}")

    # (8) SteamID64 em claro.
    if STEAMID64_RE.search(json.dumps(record, ensure_ascii=False)):
        reasons.append("STEAMID64_NOT_PSEUDONYMIZED")

    decision = "ACCEPT" if not reasons else "REJECT"
    return {
        "record_id": record.get("demo_id") or record.get("match_id") or record.get("_case") or "<sem-id>",
        "decision": decision,
        "bucket": bucket,
        "inclusion_policy": policy,
        "reason_codes": reasons,
        "reason_count": len(reasons),
    }


def load_records(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("["):
        records = json.loads(text)
    elif stripped.startswith("{"):
        payload = json.loads(text)
        records = payload.get("records") or payload.get("candidates") or [payload]
    else:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(records, list):
        raise ValidationError("arquivo de registros deve conter lista JSON ou JSONL.")
    return [r for r in records if isinstance(r, dict)]


def _base_record(**overrides: Any) -> Dict[str, Any]:
    """Registro sintético usado APENAS pelo --self-test (fixture rotulada, não dado real)."""
    record: Dict[str, Any] = {
        "demo_id": "selftest",
        "domain_id": "INTERMEDIATE_COMPETITIVE",
        "platform": "FACEIT",
        "rank_system": "FACEIT_LEVEL",
        "skill_level": 5,
        "elo_or_rating": None,
        "rank_at_collection_time": None,
        "rank_at_match_time_if_available": None,
        "map_specific_rank": None,
        "map_name": "de_mirage",
        "match_date": "2025-03-10",
        "region": "EU",
        "source": "FACEIT_DATA_API",
        "source_license": "TEST_FIXTURE_NOT_A_REAL_SOURCE",
        "acquisition_method": "OFFICIAL_API",
        "consent_type": "PLATFORM_TERMS",
        "metadata_confidence": "HIGH",
        "exclusion_reason": None,
        "source_url_reference": "faceit:match:00000000-0000-0000-0000-000000000000",
    }
    record.update(overrides)
    return record


def _valve_record(**overrides: Any) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "platform": "VALVE_STEAM",
        "rank_system": "VALVE_COMPETITIVE_MAP_RANK",
        "skill_level": "MG2",
        "map_specific_rank": "MG2",
        "source": "STEAM_PERSONAL_GAME_DATA",
        "acquisition_method": "OPT_IN_SHARE_CODE",
        "consent_type": "PLAYER_EXPLICIT_OPT_IN",
    }
    defaults.update(overrides)
    return _base_record(**defaults)


SELF_TEST_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    ("faceit_level_5_accepted", _base_record(skill_level=5), "ACCEPT"),
    ("faceit_level_8_accepted", _base_record(skill_level=8), "ACCEPT"),
    ("faceit_level_3_rejected_excluded_bucket", _base_record(skill_level=3), "REJECT"),
    ("faceit_level_10_rejected_excluded_bucket", _base_record(skill_level=10), "REJECT"),
    (
        "faceit_with_valve_rank_rejected_conversion",
        _base_record(skill_level=6, valve_competitive_rank="DMG"),
        "REJECT",
    ),
    (
        "premier_with_competitive_rank_rejected_conversion",
        _base_record(
            platform="VALVE_STEAM",
            rank_system="VALVE_PREMIER_RATING",
            skill_level=15000,
            valve_competitive_rank="MGE",
        ),
        "REJECT",
    ),
    (
        "premier_bucket_pending_audit_rejected",
        _base_record(
            platform="VALVE_STEAM",
            rank_system="VALVE_PREMIER_RATING",
            skill_level=15000,
            source="STEAM_PERSONAL_GAME_DATA",
            acquisition_method="OPT_IN_SHARE_CODE",
            consent_type="PLAYER_EXPLICIT_OPT_IN",
        ),
        "REJECT",
    ),
    (
        "unknown_promoted_to_intermediate_rejected",
        _base_record(rank_system="NONE", skill_level=None, platform="VALVE_STEAM"),
        "REJECT",
    ),
    ("missing_rank_system_rejected", {k: v for k, v in _base_record().items() if k != "rank_system"}, "REJECT"),
    ("non_mirage_rejected", _base_record(map_name="de_dust2"), "REJECT"),
    ("valve_mg2_accepted", _valve_record(skill_level="MG2"), "ACCEPT"),
    ("valve_lem_without_map_specific_rank_rejected", _valve_record(skill_level="LEM", map_specific_rank=None), "REJECT"),
    (
        "missing_mandatory_field_rejected",
        {k: v for k, v in _base_record().items() if k != "match_date"},
        "REJECT",
    ),
    (
        "signed_url_reference_rejected",
        _base_record(source_url_reference="https://download.faceit.com/demo?X-Amz-Signature=deadbeef"),
        "REJECT",
    ),
]


def run_self_test(contract: Dict[str, Any]) -> int:
    failures: List[str] = []
    results: List[Dict[str, Any]] = []
    for name, record, expected in SELF_TEST_CASES:
        outcome = evaluate(record, contract)
        ok = outcome["decision"] == expected
        results.append(
            {
                "case": name,
                "expected": expected,
                "actual": outcome["decision"],
                "bucket": outcome["bucket"],
                "reason_codes": outcome["reason_codes"],
                "ok": ok,
            }
        )
        if not ok:
            failures.append(f"{name}: esperado {expected}, obtido {outcome['decision']} ({outcome['reason_codes']})")

    passed = len(results) - len(failures)
    print(
        json.dumps(
            {
                "self_test": "validate_skill_bucket.py",
                "generated_utc": utc_now(),
                "contract_loaded_from": "datasets/mirage_domains/domain_contract_v1.json",
                "cases_total": len(results),
                "cases_passed": passed,
                "cases_failed": len(failures),
                "aggregation": f"({passed}/{len(results)})",
                "fixture_class": "TEST_FIXTURE_NOT_REAL_DATA",
                "network_requests_executed": 0,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if failures:
        print("SELF-TEST FALHOU:\n- " + "\n- ".join(failures), file=sys.stderr)
        return EXIT_VALIDATION
    return EXIT_OK


def describe_rules(contract: Dict[str, Any]) -> Dict[str, Any]:
    subdomains = contract.get("subdomains") or {}
    return {
        "contract_source": "datasets/mirage_domains/domain_contract_v1.json",
        "generated_utc": utc_now(),
        "network_requests_executed": 0,
        "rule_set": {
            "accepted_policies": ["INCLUDED_PILOT"],
            "excluded_policies": ["EXCLUDED_PILOT"],
            "pending_policies": ["NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT"],
            "conversions_allowed": (contract.get("rank_conversion_policy") or {}).get("conversions_allowed"),
            "prohibited_conversions": (contract.get("rank_conversion_policy") or {}).get("prohibited_conversions"),
        },
        "buckets": {
            name: {
                "parent_domain": sub.get("parent_domain"),
                "rank_system": sub.get("rank_system"),
                "inclusion_policy": sub.get("inclusion_policy"),
            }
            for name, sub in subdomains.items()
        },
        "valve_competitive_candidate_ranks": [
            item.get("rank_code")
            for item in (contract.get("valve_competitive_candidates") or {}).get("candidate_ranks", [])
        ],
        "valve_premier_policy": (contract.get("valve_premier_policy") or {}).get("inclusion_policy"),
        "mandatory_fields": MANDATORY_FIELDS,
        "mandatory_fields_count": len(MANDATORY_FIELDS),
        "enforced_tests": [3, 4, 5, 6],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_skill_bucket.py",
        description=(
            "Valida se uma demo candidata pertence a um bucket INCLUDED_PILOT do contrato de domínios, "
            "recusando conversão de rank, promoção de UNKNOWN e buckets pendentes de auditoria."
        ),
        epilog="Exit codes: 0 sucesso | 1 erro de validação | 2 erro de uso.",
    )
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH), help="Caminho do contrato de domínios.")
    parser.add_argument("--records", default="", help="JSON/JSONL de candidatas a validar.")
    parser.add_argument("--self-test", action="store_true", help="Executa 14 casos determinísticos embutidos.")
    parser.add_argument("--out", default="", help="Grava o laudo de validação em JSON.")
    args = parser.parse_args(argv)

    contract = load_contract(Path(args.contract))

    if args.self_test:
        code = run_self_test(contract)
        if args.out:
            out_path = Path(args.out)
            if not out_path.is_absolute():
                out_path = REPO_ROOT / out_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(describe_rules(contract), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        return code

    if not args.records:
        print(json.dumps(describe_rules(contract), indent=2, ensure_ascii=False))
        return EXIT_OK

    records_path = Path(args.records)
    if not records_path.is_absolute():
        records_path = REPO_ROOT / records_path
    if not records_path.is_file():
        raise ValidationError(f"arquivo de registros ausente: {records_path}")

    records = load_records(records_path)
    outcomes = [evaluate(record, contract) for record in records]
    accepted = [o for o in outcomes if o["decision"] == "ACCEPT"]
    rejected = [o for o in outcomes if o["decision"] == "REJECT"]

    report = {
        "generated_utc": utc_now(),
        "records_evaluated": len(outcomes),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "accept_rate_percent": (round(100.0 * len(accepted) / len(outcomes), 4) if outcomes else None),
        "accept_rate_aggregation": f"({len(accepted)}/{len(outcomes)})",
        "network_requests_executed": 0,
        "outcomes": outcomes,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"laudo gravado em: {out_path}")
    return EXIT_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except ValidationError as exc:
        print(f"ERRO de validação: {redact(str(exc))}", file=sys.stderr)
        raise SystemExit(EXIT_VALIDATION)
    except KeyboardInterrupt:
        raise SystemExit(EXIT_VALIDATION)
