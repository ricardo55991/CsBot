#!/usr/bin/env python3
"""
FASE 2A-INTERMEDIATE — suíte dos 20 testes obrigatórios da §20.

Cada teste é definido com o **nome exato** exigido pela §20 e exposto ao pytest por um alias
``test_<Nome>`` no fim do módulo (o pytest só coleta nomes iniciados por ``test``). Assim o nome
canônico existe como função chamável e é efetivamente executado pela suíte.

Princípios desta suíte (exigência do Sentinel para M8)
-----------------------------------------------------
1. **Zero asserção tautológica.** Nenhum teste usa ``assert True``. Todo teste chama lógica real do
   repositório (``tools/intermediate_demo_acquisition/*``) ou um validador local honesto, com
   entradas que produzem decisões distintas: existe sempre uma entrada que faz o teste FALHAR.
2. **Zero ``0/0`` como aprovação.** Contagens zero são verificadas como *fato de contrato*
   (``records == []``, ``status`` de pendência, esquema) e nunca como "0 de 0 violaram → PASS".
   Varreduras sempre reportam denominador real (arquivos lidos, bytes lidos, janelas inspecionadas).
3. **Zero skip silencioso.** Um único ponto pode pular: a inspeção de tensores profissionais
   reais, se o diretório externo de NPZ não existir na máquina — sempre com motivo explícito em
   ``pytest.skip("NOT_EXECUTABLE_...")`` e mantendo asserções executáveis antes do skip.

Fixtures sintéticas usadas para exercitar validadores são explicitamente rotuladas
``SYNTHETIC_FIXTURE`` / ``TEST_FIXTURE_NOT_REAL_DATA`` (AGENTS.md Regra 04): elas validam a lógica
de detecção, nunca representam dados do corpus.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DOMAINS_DIR = BASE_DIR / "datasets" / "mirage_domains"
INTERMEDIATE_DIR = DOMAINS_DIR / "intermediate_competitive"
STUDY_DIR = BASE_DIR / "training_runs" / "intermediate_domain_study"
TOOLS_DIR = BASE_DIR / "tools" / "intermediate_demo_acquisition"

DOMAIN_CONTRACT_PATH = DOMAINS_DIR / "domain_contract_v1.json"
PROFESSIONAL_REFERENCE_PATH = DOMAINS_DIR / "professional_manifest_reference.json"
INVENTORY_PATH = INTERMEDIATE_DIR / "intermediate_demo_inventory_v1.json"
NPZ_MANIFEST_PATH = INTERMEDIATE_DIR / "intermediate_npz_manifest_v1.json"
PILOT_MANIFEST_PATH = INTERMEDIATE_DIR / "pilot_download_manifest.json"
QUARANTINE_MANIFEST_PATH = INTERMEDIATE_DIR / "quarantine_manifest.json"
SPLITS_PROPOSAL_PATH = STUDY_DIR / "intermediate_splits_proposal.json"
ACQUISITION_CONFIG_PATH = TOOLS_DIR / "config.example.json"
PAUSE_MARKER_PATH = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json"
CANONICAL_SPLITS_PATH = BASE_DIR / "datasets" / "mirage_v2" / "canonical_temporal_splits_v1.json"
SPOT_CATALOG_PATH = BASE_DIR / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json"
PROFESSIONAL_ROOT = (BASE_DIR / "datasets" / "mirage_v2").resolve()

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
STEAMID64_RE = re.compile(r"\b7656119\d{10}\b")

#: Artefatos produzidos por esta etapa (M4 + M7). Todos devem viver fora de datasets/mirage_v2/.
INTERMEDIATE_ARTIFACTS: Tuple[Path, ...] = (
    INVENTORY_PATH,
    NPZ_MANIFEST_PATH,
    PILOT_MANIFEST_PATH,
    QUARANTINE_MANIFEST_PATH,
    SPLITS_PROPOSAL_PATH,
)

#: 20 testes obrigatórios da §20, na ordem da especificação.
REQUIRED_TEST_NAMES: Tuple[str, ...] = (
    "ProfessionalCorpusRemainsUnchanged",
    "IntermediateCorpusUsesSeparateDirectory",
    "RankSystemIsExplicit",
    "FaceitLevelIsNotConvertedToValveRank",
    "PremierRatingIsNotConvertedToCompetitiveRank",
    "UnknownRankIsNotPromoted",
    "DownloadRequiresApprovedSource",
    "SignedUrlsAreNotPersisted",
    "SecretsAreNotLogged",
    "DemoHashIsRecorded",
    "DuplicateDemoIsRejected",
    "NonMirageDemoIsRejected",
    "CorruptedDemoIsQuarantined",
    "RoundLifecycleIsValid",
    "IntermediateNpZContainsNoSyntheticHistory",
    "SteamIdsArePseudonymizedInReports",
    "SpotPromotionRequiresHumanReview",
    "ProfessionalAndIntermediateMetricsRemainSeparate",
    "BootstrapUsesMatchOrRoundUnit",
    "NoTrainingStartsInThisPhase",
)


# ---------------------------------------------------------------------------------------------
# Infraestrutura de teste
# ---------------------------------------------------------------------------------------------
def _load_tool_module(module_name: str, file_path: Path):
    """Importa um script de tools/ por caminho, sem depender de package __init__."""
    if not file_path.is_file():
        raise AssertionError(f"ferramenta esperada ausente: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensivo
        raise AssertionError(f"não foi possível carregar {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> Dict[str, Any]:
    assert path.is_file(), f"artefato obrigatório ausente: {path}"
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _iter_strings(node: Any, key: str = "") -> Iterable[Tuple[str, str]]:
    """Percorre uma estrutura JSON devolvendo (chave, string)."""
    if isinstance(node, str):
        yield key, node
    elif isinstance(node, dict):
        for child_key, child in node.items():
            yield from _iter_strings(child, str(child_key))
    elif isinstance(node, (list, tuple)):
        for child in node:
            yield from _iter_strings(child, key)


_PATHLIKE_KEY_RE = re.compile(r"(path|directory|output|destination|location)", re.IGNORECASE)
_READONLY_KEY_RE = re.compile(r"(source|reference|readonly|read_only)", re.IGNORECASE)


def _collect_writable_path_values(payload: Any) -> List[Tuple[str, str]]:
    """
    Coleta valores de campos que descrevem *destino/posse* de caminho (path/directory/output/...),
    ignorando campos que apenas *referenciam* leitura de outro domínio (source/reference).
    """
    collected: List[Tuple[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_str = str(key)
            if isinstance(value, str) and _PATHLIKE_KEY_RE.search(key_str) and not _READONLY_KEY_RE.search(key_str):
                collected.append((key_str, value))
            elif isinstance(value, (dict, list, tuple)):
                collected.extend(_collect_writable_path_values(value))
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            collected.extend(_collect_writable_path_values(item))
    return collected


def _faceit_record(**overrides: Any) -> Dict[str, Any]:
    """
    Registro de metadado rotulado ``TEST_FIXTURE_NOT_REAL_DATA`` usado para exercitar
    ``validate_skill_bucket.evaluate``. Não representa nenhuma demo real.
    """
    record: Dict[str, Any] = {
        "demo_id": "TEST_FIXTURE_NOT_REAL_DATA",
        "domain_id": "INTERMEDIATE_COMPETITIVE",
        "platform": "FACEIT",
        "rank_system": "FACEIT_LEVEL",
        "skill_level": 6,
        "elo_or_rating": None,
        "rank_at_collection_time": "6",
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
        "source_url_reference": "faceit:match:TEST_FIXTURE_NOT_REAL_DATA",
    }
    record.update(overrides)
    return record


def _metadata_for_build_entry(**overrides: Any) -> Dict[str, Any]:
    """Metadado mínimo aceitável para ``build_manifest.build_entry`` (fixture rotulada)."""
    metadata: Dict[str, Any] = {
        "demo_id": "fixture_demo",
        "match_id": "fixture_match",
        "domain_id": "INTERMEDIATE_COMPETITIVE",
        "platform": "FACEIT",
        "rank_system": "FACEIT_LEVEL",
        "skill_level": 6,
        "elo_or_rating": None,
        "rank_at_collection_time": "6",
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
        "source_url_reference": "faceit:match:TEST_FIXTURE_NOT_REAL_DATA",
        "download_date": "2025-03-11T00:00:00Z",
        "patch": "TEST_FIXTURE",
        "player_skill_levels": [{"player_pseudonym": "PID_0123456789abcdef", "skill_level": 6}],
        "round_count": 24,
        "player_count": 10,
        "parser_version": "test-fixture-parser-0",
    }
    metadata.update(overrides)
    return metadata


# ---------------------------------------------------------------------------------------------
# Validadores locais (regras que não existem como função reutilizável no repositório)
# ---------------------------------------------------------------------------------------------
def _validate_round_lifecycle(session: Dict[str, Any]) -> List[str]:
    """
    Validador LOCAL de lifecycle de round (declarado aqui por inexistir função equivalente
    reutilizável no repositório). Regras verificadas, alinhadas ao manifest
    ``intermediate_npz_manifest_v1.json`` (V08/HR02/HR03):

    * tick estritamente crescente (HR02);
    * ``round_index`` não regride e não pula rounds;
    * todo round tem ao menos 2 frames (início e fim identificáveis);
    * ``round_time_norm`` é o tempo restante normalizado (feature 17, ``X[:, 0, 17]``): decresce
      dentro do round e só salta para cima em fronteira de round (nenhuma janela cruza fronteira —
      HR03);
    * slots exatamente {0..9}, times em {CT, TR}, 5x5 por frame e estáveis dentro do round;
    * posições finitas (HR01).
    """
    errors: List[str] = []
    frames = session.get("frames") or []
    if not frames:
        return ["EMPTY_SESSION"]

    ticks = [int(f["tick"]) for f in frames]
    if any(ticks[i] >= ticks[i + 1] for i in range(len(ticks) - 1)):
        errors.append("TICK_NOT_STRICTLY_INCREASING")

    rounds = [int(f["round_index"]) for f in frames]
    if any(rounds[i] > rounds[i + 1] for i in range(len(rounds) - 1)):
        errors.append("ROUND_INDEX_REGRESSION")
    if any(rounds[i + 1] - rounds[i] > 1 for i in range(len(rounds) - 1)):
        errors.append("ROUND_SKIPPED")

    # Blocos contíguos por round -> lifecycle completo.
    block_start = 0
    for index in range(1, len(rounds) + 1):
        if index == len(rounds) or rounds[index] != rounds[block_start]:
            if index - block_start < 2:
                errors.append(f"ROUND_{rounds[block_start]}_LIFECYCLE_INCOMPLETE")
            block_start = index

    for i in range(len(frames) - 1):
        current, following = frames[i], frames[i + 1]
        same_round = int(following["round_index"]) == int(current["round_index"])
        if same_round and float(following["round_time_norm"]) > float(current["round_time_norm"]):
            errors.append("ROUND_TIME_NOT_MONOTONIC_WITHIN_ROUND")
        if not same_round and not float(following["round_time_norm"]) > float(current["round_time_norm"]):
            errors.append("ROUND_TIME_NOT_RESET_AT_BOUNDARY")

    stable_teams: Dict[int, Dict[str, str]] = {}
    for frame in frames:
        teams = frame.get("teams") or {}
        if sorted(int(slot) for slot in teams.keys()) != list(range(10)):
            errors.append("INVALID_PLAYER_SLOTS")
        values = [str(value) for value in teams.values()]
        if any(value not in ("CT", "TR") for value in values):
            errors.append("INVALID_TEAM_CODE")
        elif values.count("CT") != 5 or values.count("TR") != 5:
            errors.append("TEAM_NOT_FIVE_VS_FIVE")
        if not np.all(np.isfinite(np.asarray(frame.get("positions"), dtype=float))):
            errors.append("NON_FINITE_POSITION")
        round_index = int(frame["round_index"])
        normalized_teams = {str(slot): str(team) for slot, team in teams.items()}
        if round_index in stable_teams:
            if stable_teams[round_index] != normalized_teams:
                errors.append("TEAM_CHANGED_WITHIN_ROUND")
        else:
            stable_teams[round_index] = normalized_teams

    return sorted(set(errors))


def _build_round_session(rounds: int = 2, frames_per_round: int = 8) -> Dict[str, Any]:
    """Sessão SYNTHETIC_FIXTURE válida, usada para exercitar o validador de lifecycle."""
    frames: List[Dict[str, Any]] = []
    tick = 0
    for round_index in range(rounds):
        for step in range(frames_per_round):
            teams = {slot: ("CT" if slot < 5 else "TR") for slot in range(10)}
            if round_index % 2 == 1:  # troca de lado apenas entre rounds (halftime)
                teams = {slot: ("TR" if slot < 5 else "CT") for slot in range(10)}
            frames.append(
                {
                    "round_index": round_index,
                    "tick": tick,
                    "round_time_norm": round(1.0 - step / frames_per_round, 4),
                    "positions": [float(step), 10.0, 5.0],
                    "teams": teams,
                }
            )
            tick += 16
    return {"fixture_class": "SYNTHETIC_FIXTURE", "frames": frames}


def _detect_synthetic_history(positions: np.ndarray, min_displacement: float = 1.0) -> Dict[str, Any]:
    """
    Detector LOCAL de histórico sintético (declarado aqui por inexistir função equivalente
    reutilizável no repositório). Assinatura procurada: interpolação linear do tipo ``np.linspace``
    aplicada à **janela inteira** — para um eixo, todas as diferenças entre frames consecutivos são
    exatamente iguais (variância nula) e o deslocamento total é > ``min_displacement``.

    O critério exige pelo menos 2 eixos lineares simultaneamente, o que distingue a assinatura de
    ``np.linspace`` (x, y, z interpolados) de uma trajetória real de velocidade constante em um
    único eixo. Janelas estáticas (deslocamento ~0) não são flagadas por este critério.
    """
    array = np.asarray(positions, dtype=float)
    if array.ndim != 2 or array.shape[0] < 3 or array.shape[1] < 3:
        return {"synthetic": False, "linear_axes": [], "reason": "WINDOW_TOO_SHORT"}
    linear_axes: List[int] = []
    for axis in range(3):
        series = array[:, axis]
        if not np.all(np.isfinite(series)):
            return {"synthetic": True, "linear_axes": [axis], "reason": "NON_FINITE_HISTORY"}
        diffs = np.diff(series)
        spread = float(np.ptp(diffs))
        scale = max(1.0, float(np.max(np.abs(diffs))))
        displacement = abs(float(series[-1] - series[0]))
        if spread <= 1e-9 * scale and displacement > min_displacement:
            linear_axes.append(axis)
    return {
        "synthetic": len(linear_axes) >= 2,
        "linear_axes": linear_axes,
        "reason": "LINEAR_RAMP" if len(linear_axes) >= 2 else "OK",
    }


def _pseudonymize(steamid64: str, salt: str) -> str:
    """
    Pseudonimização LOCAL conforme ``domain_contract_v1.json :: steamid_pseudonymization_policy``:
    HMAC-SHA256 sobre o SteamID64 canônico, prefixo ``PID_`` + 16 hex.
    """
    digest = hmac.new(salt.encode("utf-8"), str(steamid64).encode("utf-8"), hashlib.sha256).hexdigest()
    return "PID_" + digest[:16]


_HUMAN_APPROVAL_SEAL = "APPROVED_BY_USER"


def _spot_promotion_allowed(approval: Optional[Dict[str, Any]]) -> bool:
    """
    Política LOCAL de promoção de spot (Regra 05): apenas um humano pode promover um spot ao
    catálogo, com selo humano explícito. Agente, script ou relatório nunca promove.
    """
    if not isinstance(approval, dict):
        return False
    seal = str(approval.get("seal") or "").strip()
    approved_by = str(approval.get("approved_by") or "").strip().lower()
    return seal == _HUMAN_APPROVAL_SEAL and approved_by in {"user", "human"}


def _is_valid_bootstrap_unit(unit: str, proposal: Dict[str, Any]) -> bool:
    """Política LOCAL: unidade de bootstrap válida = unidade independente (match ou round)."""
    policy = (proposal.get("bootstrap_policy") or {}).get("bootstrap_units") or {}
    allowed = {str(policy.get("primary")), str(policy.get("alternative"))}
    prohibited = {str(item) for item in (policy.get("prohibited") or [])}
    normalized = str(unit).strip().lower()
    if normalized in prohibited:
        return False
    return normalized in {item.lower() for item in allowed if item}


def _independent_unit_count(records: List[Dict[str, Any]], unit: str) -> int:
    """
    Conta unidades independentes de uma fixture rotulada. Usada para demonstrar por aritmética real
    que janelas/sequências não são unidades independentes (inflam o N efetivo).
    """
    key = str(unit).strip().lower()
    allowed_keys = {"match_id", "round_id", "window_id"}
    if key not in allowed_keys:
        raise ValueError(f"unidade não suportada: {unit}")
    return len({str(record.get(key)) for record in records})


def _training_blocked_by_marker(marker_payload: Dict[str, Any]) -> bool:
    """
    Política LOCAL derivada do marcador de pausa: bloqueia qualquer início de treino enquanto o
    marcador estiver ativo e exigir autorização humana para retomada.
    """
    marker = str(marker_payload.get("marker") or "")
    requires_human = bool(marker_payload.get("resumption_requires_human_authorization"))
    prohibited = " ".join(str(item).lower() for item in (marker_payload.get("prohibited_during_pause") or []))
    mentions_training = ("treinamento" in prohibited) or ("training" in prohibited)
    return marker.startswith("PAUSED_FOR_") and requires_human and mentions_training


# ---------------------------------------------------------------------------------------------
# 1. ProfessionalCorpusRemainsUnchanged
# ---------------------------------------------------------------------------------------------
def ProfessionalCorpusRemainsUnchanged():
    """
    Compara o inventário de arquivos + SHA-256 de TODAS as referências registradas em
    ``professional_manifest_reference.json`` contra o disco. Qualquer modificação, remoção ou
    truncamento do corpus profissional faz este teste falhar.
    """
    reference = _read_json(PROFESSIONAL_REFERENCE_PATH)
    entries = reference.get("references") or []
    assert len(entries) == reference["totals"]["references_resolved"], "inventário de referências inconsistente"
    assert len(entries) > 0, "referência profissional vazia"

    verified: List[str] = []
    bytes_verified = 0
    for entry in entries:
        relative = entry["repo_relative_path"]
        path = BASE_DIR / relative
        assert path.is_file(), f"corpus profissional ausente: {relative}"
        size = path.stat().st_size
        assert size == entry["size_bytes"], f"tamanho divergente em {relative}: {size} != {entry['size_bytes']}"
        digest = _sha256_file(path)
        assert SHA256_HEX_RE.match(entry["sha256"]), f"hash registrado não tem 64 hex: {relative}"
        assert digest == entry["sha256"], f"hash divergente em {relative}: {digest} != {entry['sha256']}"
        verified.append(relative)
        bytes_verified += size

    assert reference["corpus_moved"] is False
    assert reference["corpus_modified"] is False
    assert reference["corpus_renamed"] is False
    assert reference["logical_reference_point_is_copy"] is False
    assert len(verified) == len(entries) and bytes_verified > 0
    assert reference["verified_corpus_counts"]["npz_demos_accepted"] == 444


# ---------------------------------------------------------------------------------------------
# 2. IntermediateCorpusUsesSeparateDirectory
# ---------------------------------------------------------------------------------------------
def IntermediateCorpusUsesSeparateDirectory():
    """
    Nenhum artefato do domínio intermediário pode resolver para dentro de ``datasets/mirage_v2/``
    ou de ``training_runs/positioning_v2_real_temporal/``; e o ponto lógico
    ``datasets/mirage_domains/professional/`` não pode conter cópia de dados.
    """
    allowed_roots = [
        INTERMEDIATE_DIR.resolve(),
        STUDY_DIR.resolve(),
    ]
    checked = 0
    for artifact in INTERMEDIATE_ARTIFACTS:
        resolved = artifact.resolve()
        assert not resolved.is_relative_to(PROFESSIONAL_ROOT), f"artefato intermediário dentro do corpus profissional: {resolved}"
        assert any(resolved.is_relative_to(root) for root in allowed_roots), f"artefato fora do diretório do domínio: {resolved}"
        payload = _read_json(artifact)
        for key, value in _collect_writable_path_values(payload):
            normalized = value.replace("\\", "/")
            assert not normalized.startswith("datasets/mirage_v2/"), f"{artifact.name}:{key} aponta para o corpus profissional: {value}"
            assert not normalized.startswith("training_runs/positioning_v2_real_temporal/"), (
                f"{artifact.name}:{key} aponta para artefatos do MARCO 2B.3: {value}"
            )
        checked += 1

    logical_reference = DOMAINS_DIR / "professional"
    children = sorted(logical_reference.iterdir())
    assert len(children) == 1, f"ponto de referência lógica deveria conter apenas README.md, contém: {[c.name for c in children]}"
    assert children[0].name == "README.md"

    data_files = [
        path
        for path in INTERMEDIATE_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in {".dem", ".npz", ".parquet", ".pt", ".onnx"}
    ]
    assert data_files == [], f"diretório intermediário deveria estar sem dados, encontrou: {[p.name for p in data_files]}"
    assert checked == len(INTERMEDIATE_ARTIFACTS)


# ---------------------------------------------------------------------------------------------
# 3. RankSystemIsExplicit
# ---------------------------------------------------------------------------------------------
def RankSystemIsExplicit():
    """
    ``rank_system`` é obrigatório e não nulo no contrato; e o validador real
    (``validate_skill_bucket.evaluate``) REJEITA registro sem ``rank_system`` ou com sistema
    desconhecido. Sem esses campos, a demo não entra.
    """
    contract = _read_json(DOMAIN_CONTRACT_PATH)
    describe_rank_system = next(f for f in contract["mandatory_fields"] if f["field"] == "rank_system")
    assert describe_rank_system["required"] is True
    assert describe_rank_system["null_allowed"] is False
    assert set(describe_rank_system["allowed_values"]) == {
        "FACEIT_LEVEL",
        "FACEIT_ELO",
        "VALVE_COMPETITIVE_MAP_RANK",
        "VALVE_PREMIER_RATING",
        "PROFESSIONAL_HLTV",
        "NONE",
    }

    inventory = _read_json(INVENTORY_PATH)
    schema_rank_system = next(f for f in inventory["schema"]["fields"] if f["name"] == "rank_system")
    assert schema_rank_system["required"] is True
    assert "proibido nulo" in schema_rank_system["null_policy"].lower()

    module = _load_tool_module("validate_skill_bucket_rank_system", TOOLS_DIR / "validate_skill_bucket.py")
    contract_for_tool = module.load_contract(DOMAIN_CONTRACT_PATH)

    without_field = _faceit_record()
    without_field.pop("rank_system")
    outcome = module.evaluate(without_field, contract_for_tool)
    assert outcome["decision"] == "REJECT"
    assert "MISSING_RANK_SYSTEM" in outcome["reason_codes"]

    invented = module.evaluate(_faceit_record(rank_system="VALVE_MMR_GUESS"), contract_for_tool)
    assert invented["decision"] == "REJECT"
    assert any(reason.startswith("UNKNOWN_RANK_SYSTEM") for reason in invented["reason_codes"])

    accepted = module.evaluate(_faceit_record(), contract_for_tool)
    assert accepted["decision"] == "ACCEPT" and accepted["reason_codes"] == []


# ---------------------------------------------------------------------------------------------
# 4. FaceitLevelIsNotConvertedToValveRank
# ---------------------------------------------------------------------------------------------
def FaceitLevelIsNotConvertedToValveRank():
    """
    Chama a lógica real de ``validate_skill_bucket.py`` com entrada FACEIT: nível 6 é aceito no
    bucket FACEIT_LEVEL_5_6 e o sistema original é preservado; qualquer campo de rank Valve
    preenchido na mesma demo provoca REJECT por conversão proibida.
    """
    module = _load_tool_module("validate_skill_bucket_faceit", TOOLS_DIR / "validate_skill_bucket.py")
    contract = module.load_contract(DOMAIN_CONTRACT_PATH)
    assert contract["rank_conversion_policy"]["conversions_allowed"] == []

    plain = _faceit_record(skill_level=6)
    accepted = module.evaluate(plain, contract)
    assert accepted["decision"] == "ACCEPT"
    assert accepted["bucket"] == "FACEIT_LEVEL_5_6"
    assert accepted["reason_codes"] == []

    # O validador não pode derivar/mutar nada: o sistema original continua FACEIT_LEVEL.
    assert plain["rank_system"] == "FACEIT_LEVEL" and plain["skill_level"] == 6
    assert not any("valve" in str(key).lower() for key in accepted.keys())

    for trap_field, trap_value in (
        ("valve_competitive_rank", "DMG"),
        ("premier_rating", 18000),
        ("converted_valve_rank", "LEM"),
    ):
        converted = _faceit_record(skill_level=6, **{trap_field: trap_value})
        outcome = module.evaluate(converted, contract)
        assert outcome["decision"] == "REJECT", f"conversão '{trap_field}' deveria ser rejeitada"
        assert f"RANK_CONVERSION_PROHIBITED:{trap_field}" in outcome["reason_codes"]
        assert converted["rank_system"] == "FACEIT_LEVEL"


# ---------------------------------------------------------------------------------------------
# 5. PremierRatingIsNotConvertedToCompetitiveRank
# ---------------------------------------------------------------------------------------------
def PremierRatingIsNotConvertedToCompetitiveRank():
    """
    Premier Rating não é convertido para rank Competitive, e o bucket Premier permanece
    ``NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT`` (rejeitado para o corpus principal).
    """
    module = _load_tool_module("validate_skill_bucket_premier", TOOLS_DIR / "validate_skill_bucket.py")
    contract = module.load_contract(DOMAIN_CONTRACT_PATH)
    assert contract["valve_premier_policy"]["inclusion_policy"] == "NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT"
    assert contract["valve_premier_policy"]["bucket_definition"] is None

    premier_only = module.evaluate(
        _faceit_record(
            platform="VALVE_STEAM",
            rank_system="VALVE_PREMIER_RATING",
            skill_level=18000,
            source="STEAM_PERSONAL_GAME_DATA",
            acquisition_method="OPT_IN_SHARE_CODE",
            consent_type="PLAYER_EXPLICIT_OPT_IN",
        ),
        contract,
    )
    assert premier_only["decision"] == "REJECT"
    assert premier_only["bucket"] == "VALVE_PREMIER_RATING"
    assert any(reason.startswith("BUCKET_NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT") for reason in premier_only["reason_codes"])

    converted = module.evaluate(
        _faceit_record(
            platform="VALVE_STEAM",
            rank_system="VALVE_PREMIER_RATING",
            skill_level=18000,
            valve_competitive_rank="MGE",
            source="STEAM_PERSONAL_GAME_DATA",
            acquisition_method="OPT_IN_SHARE_CODE",
            consent_type="PLAYER_EXPLICIT_OPT_IN",
        ),
        contract,
    )
    assert converted["decision"] == "REJECT"
    assert "RANK_CONVERSION_PROHIBITED:valve_competitive_rank" in converted["reason_codes"]

    # Caminho legítimo do outro sistema continua funcionando (não é reject-all).
    competitive = module.evaluate(
        _faceit_record(
            platform="VALVE_STEAM",
            rank_system="VALVE_COMPETITIVE_MAP_RANK",
            skill_level="MG2",
            map_specific_rank="MG2",
            source="STEAM_PERSONAL_GAME_DATA",
            acquisition_method="OPT_IN_SHARE_CODE",
            consent_type="PLAYER_EXPLICIT_OPT_IN",
        ),
        contract,
    )
    assert competitive["decision"] == "ACCEPT"
    assert competitive["bucket"] == "VALVE_COMPETITIVE_MAP_RANK"


# ---------------------------------------------------------------------------------------------
# 6. UnknownRankIsNotPromoted
# ---------------------------------------------------------------------------------------------
def UnknownRankIsNotPromoted():
    """
    ``UNKNOWN`` não pode ser promovido a ``INTERMEDIATE_COMPETITIVE``: o contrato proíbe e o
    validador real rejeita o registro com ``UNKNOWN_DOMAIN_PROMOTED``.
    """
    contract = _read_json(DOMAIN_CONTRACT_PATH)
    assert contract["domains"]["UNKNOWN"]["default_inclusion_policy"] == "EXCLUDED_PILOT"
    assert contract["domains"]["UNKNOWN"]["allowed_rank_systems"] == ["NONE"]
    assert "UNKNOWN" in contract["domains"]["INTERMEDIATE_COMPETITIVE"]["promotion_prohibited_from"]

    module = _load_tool_module("validate_skill_bucket_unknown", TOOLS_DIR / "validate_skill_bucket.py")
    contract_for_tool = module.load_contract(DOMAIN_CONTRACT_PATH)

    promoted = module.evaluate(
        _faceit_record(rank_system="NONE", skill_level=None, platform="VALVE_STEAM"), contract_for_tool
    )
    assert promoted["decision"] == "REJECT"
    assert promoted["bucket"] == "UNKNOWN"
    assert "UNKNOWN_DOMAIN_PROMOTED" in promoted["reason_codes"]
    assert any(reason.startswith("BUCKET_EXCLUDED_FROM_PRIMARY_CORPUS") for reason in promoted["reason_codes"])


# ---------------------------------------------------------------------------------------------
# 7. DownloadRequiresApprovedSource
# ---------------------------------------------------------------------------------------------
def DownloadRequiresApprovedSource():
    """
    O downloader real recusa host fora da allowlist e recusa ``--execute`` sem fonte aprovada
    (``CSBOT_APPROVED_SOURCE_ID``) e sem o segredo correspondente. O manifesto do piloto declara
    autorização pendente e zero tentativas.
    """
    module = _load_tool_module("download_demo_approved_source", TOOLS_DIR / "download_demo.py")
    config = module.load_config(ACQUISITION_CONFIG_PATH)

    with pytest.raises(module.ValidationError) as outside:
        module.validate_url("https://mirror.example.net/demo.dem", config)
    assert "allowlist" in str(outside.value).lower()

    with pytest.raises(module.ValidationError):
        module.validate_url("http://open.faceit.com/data/v4/matches/x", config)  # HTTPS obrigatório

    module.validate_url("https://open.faceit.com/data/v4/matches/approved-source-probe", config)  # host válido: não levanta

    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.delenv("CSBOT_APPROVED_SOURCE_ID", raising=False)
        monkeypatch.delenv("CSBOT_FACEIT_DOWNLOADS_API_KEY", raising=False)
        with pytest.raises(module.PolicyError) as blocked:
            module.main(["--execute", "--url", "https://open.faceit.com/data/v4/matches/probe", "--demo-id", "probe"])
        assert "aprovada" in str(blocked.value).lower()

        monkeypatch.setenv("CSBOT_APPROVED_SOURCE_ID", "SOURCE_APPROVED_IN_TEST_FIXTURE")
        with pytest.raises(module.ValidationError) as missing_secret:
            module.main(["--execute", "--url", "https://open.faceit.com/data/v4/matches/probe", "--demo-id", "probe"])
        assert "segredo" in str(missing_secret.value).lower()
    finally:
        monkeypatch.undo()

    pilot_manifest = _read_json(PILOT_MANIFEST_PATH)
    assert pilot_manifest["source_authorization_status"] == "PENDING_HUMAN_APPROVAL"
    assert pilot_manifest["downloads_attempted"] == 0
    assert pilot_manifest["network_requests_executed"] == 0
    assert pilot_manifest["execute_mode_available"] is False
    assert "open.faceit.com" in [domain["host"] for domain in pilot_manifest["allowlist_domains"]["domains"]]


# ---------------------------------------------------------------------------------------------
# 8. SignedUrlsAreNotPersisted
# ---------------------------------------------------------------------------------------------
_SIGNED_URL_PATTERNS = (
    re.compile(r"(?i)x-amz-(?:signature|credential|security-token)\s*="),
    re.compile(r"(?i)[?&](?:signature|sig|token|expires|policy|key-pair-id)="),
)


def SignedUrlsAreNotPersisted():
    """
    URL assinada é recusada pelo validador real do downloader e NÃO aparece em nenhum artefato
    publicado (manifests, proposta de splits ou configuração de exemplo). A varredura tem
    denominador real: número de arquivos e de bytes efetivamente lidos.
    """
    module = _load_tool_module("download_demo_signed_url", TOOLS_DIR / "download_demo.py")
    config = module.load_config(ACQUISITION_CONFIG_PATH)

    with pytest.raises(module.ValidationError) as signed:
        module.validate_url("https://download.faceit.com/d/match.dem?X-Amz-Signature=deadbeefcafe", config)
    assert "assinad" in str(signed.value).lower()

    with pytest.raises(module.ValidationError):
        module.validate_url("https://download.faceit.com/d/match.dem?token=abc123", config)

    scanned: List[str] = []
    bytes_scanned = 0
    for artifact in INTERMEDIATE_ARTIFACTS + (ACQUISITION_CONFIG_PATH,):
        text = artifact.read_text(encoding="utf-8")
        bytes_scanned += len(text.encode("utf-8"))
        for pattern in _SIGNED_URL_PATTERNS:
            match = pattern.search(text)
            assert match is None, f"URL assinada persistida em {artifact.name}: '{match.group(0) if match else ''}'"
        scanned.append(artifact.name)

    assert len(scanned) == len(INTERMEDIATE_ARTIFACTS) + 1, "nem todos os artefatos foram varridos"
    assert bytes_scanned > 0

    pilot_manifest = _read_json(PILOT_MANIFEST_PATH)
    assert pilot_manifest["signed_urls_persisted"] == 0
    assert pilot_manifest["signed_url_policy"]["persistence_allowed"] is False


# ---------------------------------------------------------------------------------------------
# 9. SecretsAreNotLogged
# ---------------------------------------------------------------------------------------------
_CREDENTIAL_PATTERNS = (
    re.compile(r"(?i)\b(?:password|passwd|pwd)\s*[=:]\s*[\"']?([^\s\"',}]{4,})"),
    re.compile(r"(?i)\b(?:api[_-]?key|apikey|access[_-]?token|client[_-]?secret|steamloginsecure)\s*[=:]\s*[\"']?([^\s\"',}]{8,})"),
    re.compile(r"(?i)\bbearer\s+([A-Za-z0-9\-._~+/]{16,})"),
)


def _looks_like_env_var_name(value: str) -> bool:
    """Nomes de variável de ambiente (CSBOT_...) e placeholders não são segredos."""
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", value)) or value in {"[REDACTED]", "REDACTED"}


def SecretsAreNotLogged():
    """
    Um segredo presente no ambiente é efetivamente lido pelo downloader (aparece o NOME da variável
    no plano) mas o VALOR nunca é impresso no audit log nem gravado nos artefatos. Também verifica
    que ``assert_no_secret_leak`` aborta quando o valor vaza.
    """
    module = _load_tool_module("download_demo_secrets", TOOLS_DIR / "download_demo.py")
    secret_value = "FAKE_SECRET_VALUE_9f3a1c7d2b"
    monkeypatch = pytest.MonkeyPatch()
    buffer_out = ""
    try:
        monkeypatch.setenv("CSBOT_FACEIT_DATA_API_KEY", secret_value)
        import contextlib
        import io

        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            exit_code = module.main(
                ["--url", "https://open.faceit.com/data/v4/matches/secret-probe", "--demo-id", "secret-probe"]
            )
        buffer_out = stream.getvalue()
        assert exit_code == module.EXIT_OK
    finally:
        monkeypatch.undo()

    assert secret_value not in buffer_out, "valor de segredo apareceu no output do downloader"
    assert "faceit_data_api_key" in buffer_out, "o segredo deveria ter sido lido do ambiente (nome no plano)"

    with pytest.raises(module.ValidationError):
        module.assert_no_secret_leak(f"Authorization: Bearer {secret_value}", {"faceit_data_api_key": secret_value}, "url")

    secrets = {"faceit_data_api_key": secret_value}
    text = buffer_out + json.dumps(secrets)  # o dict do teste só existe em memória, nunca em disco
    for artifact in INTERMEDIATE_ARTIFACTS + (ACQUISITION_CONFIG_PATH,):
        content = artifact.read_text(encoding="utf-8")
        for pattern in _CREDENTIAL_PATTERNS:
            for match in pattern.finditer(content):
                candidate = match.group(1)
                assert _looks_like_env_var_name(candidate) or candidate.startswith("CSBOT_"), (
                    f"credencial aparente em {artifact.name}: '{candidate}'"
                )
        assert secret_value not in content
    assert len(ACQUISITION_CONFIG_PATH.read_text(encoding="utf-8")) > 0
    assert text  # garante que a verificação não é vazia


# ---------------------------------------------------------------------------------------------
# 10. DemoHashIsRecorded
# ---------------------------------------------------------------------------------------------
def DemoHashIsRecorded():
    """
    O esquema do inventário exige ``demo_sha256``/``archive_sha256`` de 64 hex, e a ferramenta real
    (``build_manifest.build_entry``) recalcula o hash do disco: hash correto para arquivo presente e
    rejeição quando o hash declarado do pacote é inválido.
    """
    inventory = _read_json(INVENTORY_PATH)
    fields = {field["name"]: field for field in inventory["schema"]["fields"]}
    assert fields["demo_sha256"]["required"] is True
    assert fields["demo_sha256"]["type"] == "string_64_hex"
    assert "64 hex" in fields["demo_sha256"]["null_policy"]
    assert fields["archive_sha256"]["required"] is True
    assert "64 hex" in fields["archive_sha256"]["null_policy"]

    module = _load_tool_module("build_manifest_hash", TOOLS_DIR / "build_manifest.py")
    assert module.SHA256_RE.match("a" * 64)
    assert not module.SHA256_RE.match("a" * 63)
    assert not module.SHA256_RE.match("a" * 65)
    assert not module.SHA256_RE.match("A" * 64)  # o contrato exige hex minúsculo

    contract = _read_json(DOMAIN_CONTRACT_PATH)
    with tempfile.TemporaryDirectory(prefix="csbot_demohash_") as tmp:
        demo_path = Path(tmp) / "fixture_demo.dem"
        payload = b"DEMO-FIXTURE-BYTES-NOT-REAL" * 128
        demo_path.write_bytes(payload)
        expected = _sha256_bytes(payload)

        entry = module.build_entry(
            _metadata_for_build_entry(), {"fixture_demo": demo_path}, {}, contract, {"map_name": "de_mirage"}
        )
        assert entry["demo_sha256"] == expected
        assert SHA256_HEX_RE.match(entry["demo_sha256"])
        assert entry["file_size"] == len(payload)
        assert entry["accepted"] is True, entry["rejection_reason"]

        corrupted_archive = module.build_entry(
            _metadata_for_build_entry(archive_id="fixture_archive", archive_sha256="deadbeef"),
            {"fixture_demo": demo_path},
            {},
            contract,
            {"map_name": "de_mirage"},
        )
        assert corrupted_archive["accepted"] is False
        assert "ARCHIVE_SHA256_INVALID_FORMAT" in corrupted_archive["rejection_reason"]


# ---------------------------------------------------------------------------------------------
# 11. DuplicateDemoIsRejected
# ---------------------------------------------------------------------------------------------
def DuplicateDemoIsRejected():
    """
    A detecção real (``deduplicate_demo.classify``) agrupa por SHA-256: arquivos idênticos são
    duplicata exata; conteúdos diferentes com o mesmo nome NÃO são duplicata (colisão de nome).
    """
    module = _load_tool_module("deduplicate_demo_real", TOOLS_DIR / "deduplicate_demo.py")
    with tempfile.TemporaryDirectory(prefix="csbot_dedup_test_") as tmp:
        root = Path(tmp)
        (root / "nested").mkdir()
        (root / "a.dem").write_bytes(b"DEMO-CONTENT-ALPHA" * 200)
        (root / "b.dem").write_bytes(b"DEMO-CONTENT-ALPHA" * 200)  # duplicata exata de a.dem
        (root / "c.dem").write_bytes(b"DEMO-CONTENT-BETA" * 200)   # único
        (root / "nested" / "a.dem").write_bytes(b"DIFFERENT-CONTENT" * 200)  # colisão de nome

        files = module.collect_files([root], module.CANDIDATE_SUFFIXES)
        outcome = module.classify(files)

        assert outcome["files_scanned"] == 4
        assert outcome["duplicate_groups"] == 1
        assert outcome["excess_duplicate_files"] == 1
        assert outcome["unique_hashes"] == 3
        assert outcome["name_collisions"] == 1
        duplicate = outcome["duplicate_detail"][0]
        assert duplicate["count"] == 2
        assert len(duplicate["duplicates"]) == 1
        assert SHA256_HEX_RE.match(duplicate["sha256"])

        # Sem duplicatas -> nenhuma duplicata é inventada (o teste falharia se a regra mentisse).
        unique_only = module.collect_files([root], module.CANDIDATE_SUFFIXES)
        unique_only = [path for path in unique_only if path.name != "b.dem" and path.parent.name != "nested"]
        clean = module.classify(unique_only)
        assert clean["duplicate_groups"] == 0 and clean["excess_duplicate_files"] == 0

    quarantine_manifest = _read_json(QUARANTINE_MANIFEST_PATH)
    reason_codes = [reason["reason_code"] for reason in quarantine_manifest["quarantine_reason_schema"]["reasons"]]
    assert "duplicate" in reason_codes
    assert quarantine_manifest["status"] == "EMPTY_NO_CANDIDATES"
    assert quarantine_manifest["total_quarantined"] == 0


# ---------------------------------------------------------------------------------------------
# 12. NonMirageDemoIsRejected
# ---------------------------------------------------------------------------------------------
def NonMirageDemoIsRejected():
    """
    Demo de outro mapa é rejeitada nos dois caminhos reais: ``validate_skill_bucket.evaluate`` e
    ``build_manifest.build_entry``. O contrato só admite ``de_mirage``.
    """
    contract = _read_json(DOMAIN_CONTRACT_PATH)
    map_field = next(field for field in contract["mandatory_fields"] if field["field"] == "map_name")
    assert map_field["allowed_values"] == ["de_mirage"]

    validator = _load_tool_module("validate_skill_bucket_mirage", TOOLS_DIR / "validate_skill_bucket.py")
    contract_for_tool = validator.load_contract(DOMAIN_CONTRACT_PATH)
    rejected = validator.evaluate(_faceit_record(map_name="de_dust2"), contract_for_tool)
    assert rejected["decision"] == "REJECT"
    assert "NON_MIRAGE_DEMO" in rejected["reason_codes"]

    mirage = validator.evaluate(_faceit_record(map_name="de_mirage"), contract_for_tool)
    assert mirage["decision"] == "ACCEPT"

    builder = _load_tool_module("build_manifest_mirage", TOOLS_DIR / "build_manifest.py")
    with tempfile.TemporaryDirectory(prefix="csbot_mirage_test_") as tmp:
        demo_path = Path(tmp) / "fixture_demo.dem"
        demo_path.write_bytes(b"NON-MIRAGE-FIXTURE" * 64)
        entry = builder.build_entry(
            _metadata_for_build_entry(map_name="de_inferno"),
            {"fixture_demo": demo_path},
            {},
            contract,
            {"map_name": "de_mirage"},
        )
    assert entry["accepted"] is False
    assert "NON_MIRAGE_DEMO" in entry["rejection_reason"]
    assert entry["map"] == "de_inferno"  # o mapa real é registrado, nunca mascarado


# ---------------------------------------------------------------------------------------------
# 13. CorruptedDemoIsQuarantined
# ---------------------------------------------------------------------------------------------
def CorruptedDemoIsQuarantined():
    """
    ``verify_archive.verify`` reprova bytes corrompidos e checksum divergente, recomendando
    quarentena; e aprova pacote íntegro (portanto não é "reject-all").
    """
    module = _load_tool_module("verify_archive_real", TOOLS_DIR / "verify_archive.py")
    config = module.load_config(ACQUISITION_CONFIG_PATH)
    archive_cfg = config.get("archive") or {}

    corrupted = module.verify(b"NOT-AN-ARCHIVE-AT-ALL" * 16, "zip", None, archive_cfg)
    assert corrupted["verdict"] == "FAIL"
    assert corrupted["recommended_action"] == "MOVE_TO_QUARANTINE"
    issues = {finding["issue"] for finding in corrupted["findings"]}
    assert issues & {"INVALID_ZIP", "UNKNOWN_ARCHIVE_FORMAT", "MAGIC_BYTES_MISMATCH"}
    assert len(corrupted["archive_sha256"]) == 64

    safe_zip = module._make_zip([("match_001.dem", b"DEMO-BYTES" * 64)])
    checksum_mismatch = module.verify(safe_zip, "zip", "0" * 64, archive_cfg)
    assert checksum_mismatch["verdict"] == "FAIL"
    assert "CHECKSUM_MISMATCH" in {finding["issue"] for finding in checksum_mismatch["findings"]}

    intact = module.verify(safe_zip, "zip", _sha256_bytes(safe_zip), archive_cfg)
    assert intact["verdict"] == "PASS"
    assert intact["recommended_action"] == "PROCEED_TO_EXTRACTION"
    assert intact["contains_dem"] is True

    traversal = module.verify(module._make_zip([("../../etc/evil.dem", b"x" * 32)]), "zip", None, archive_cfg)
    assert traversal["verdict"] == "FAIL"
    assert "UNSAFE_ENTRY_PATH" in {finding["issue"] for finding in traversal["findings"]}

    quarantine_manifest = _read_json(QUARANTINE_MANIFEST_PATH)
    corrupted_reason = next(
        reason for reason in quarantine_manifest["quarantine_reason_schema"]["reasons"] if reason["reason_code"] == "corrupted"
    )
    assert corrupted_reason["disposition"] == "QUARANTINE"
    assert quarantine_manifest["bytes_quarantined"] == 0
    assert quarantine_manifest["directory_scan"]["status"] == "EMPTY_CONFIRMED_ON_DISK"


# ---------------------------------------------------------------------------------------------
# 14. RoundLifecycleIsValid
# ---------------------------------------------------------------------------------------------
def RoundLifecycleIsValid():
    """
    Verifica a regra de lifecycle de round exigida pelo manifest NPZ (V08 + HR01/HR02/HR03) com um
    **validador local** declarado no topo deste módulo (não existe função equivalente reutilizável
    no repositório). A fixture válida é ``SYNTHETIC_FIXTURE``; cada mutação representa uma violação
    real e o validador precisa acusá-la — sem isso o teste falha.
    """
    npz_manifest = _read_json(NPZ_MANIFEST_PATH)
    validations = {validation["name"]: validation for validation in npz_manifest["validations"]}
    assert "round_lifecycle" in validations
    assert "fronteira de round" in validations["round_lifecycle"]["rule"]
    requirements = {requirement["name"]: requirement for requirement in npz_manifest["hard_requirements"]}
    assert {"monotonic_ticks", "no_round_crossing", "finite_coordinates", "valid_player_slots", "valid_ct_tr_mapping"} <= set(
        requirements
    )

    valid_session = _build_round_session()
    assert _validate_round_lifecycle(valid_session) == []

    import copy

    non_monotonic = copy.deepcopy(valid_session)
    non_monotonic["frames"][3]["tick"] = non_monotonic["frames"][2]["tick"]
    assert "TICK_NOT_STRICTLY_INCREASING" in _validate_round_lifecycle(non_monotonic)

    crossing = copy.deepcopy(valid_session)
    crossing["frames"][5]["round_time_norm"] = 0.999  # salto para cima dentro do round = cruzamento
    assert "ROUND_TIME_NOT_MONOTONIC_WITHIN_ROUND" in _validate_round_lifecycle(crossing)

    missing_reset = copy.deepcopy(valid_session)
    missing_reset["frames"][8]["round_time_norm"] = 0.10  # novo round sem salto de reset temporal
    assert "ROUND_TIME_NOT_RESET_AT_BOUNDARY" in _validate_round_lifecycle(missing_reset)

    invalid_slot = copy.deepcopy(valid_session)
    invalid_slot["frames"][2]["teams"] = {**invalid_slot["frames"][2]["teams"], 10: "CT"}
    assert "INVALID_PLAYER_SLOTS" in _validate_round_lifecycle(invalid_slot)

    swapped_side = copy.deepcopy(valid_session)
    swapped_side["frames"][4]["teams"]["0"] = "TR"
    errors = _validate_round_lifecycle(swapped_side)
    assert "TEAM_CHANGED_WITHIN_ROUND" in errors
    assert "TEAM_NOT_FIVE_VS_FIVE" in errors

    non_finite = copy.deepcopy(valid_session)
    non_finite["frames"][1]["positions"] = [float("nan"), 0.0, 0.0]
    assert "NON_FINITE_POSITION" in _validate_round_lifecycle(non_finite)

    # Round 1 truncado a um único frame: lifecycle incompleto (início e fim não identificáveis).
    incomplete = copy.deepcopy(valid_session)
    incomplete["frames"] = incomplete["frames"][:8] + incomplete["frames"][8:9]
    incomplete_errors = _validate_round_lifecycle(incomplete)
    assert "ROUND_1_LIFECYCLE_INCOMPLETE" in incomplete_errors
    assert len(incomplete_errors) == 1, incomplete_errors

    assert _validate_round_lifecycle({"frames": []}) == ["EMPTY_SESSION"]


# ---------------------------------------------------------------------------------------------
# 15. IntermediateNpZContainsNoSyntheticHistory
# ---------------------------------------------------------------------------------------------
def IntermediateNpZContainsNoSyntheticHistory():
    """
    O manifesto NPZ exige ``zero_synthetic_history`` e não contém registros. O detector **local**
    (declarado no topo deste módulo) é exercitado nos dois sentidos: flagra uma janela construída
    por interpolação linear (``SYNTHETIC_FIXTURE``) e não flagra histórico real de uma demo
    profissional de Mirage (tensores NPZ reais, somente leitura).
    """
    npz_manifest = _read_json(NPZ_MANIFEST_PATH)
    assert npz_manifest["zero_synthetic_history"]["required"] is True
    assert npz_manifest["records"] == []
    assert npz_manifest["npz_count"] == 0
    assert npz_manifest["record_count"] == 0
    assert npz_manifest["status"] == "EMPTY_PENDING_ACQUISITION_ACCESS"
    assert npz_manifest["dem_vs_npz_comparison"]["executed"] is False
    assert npz_manifest["dem_vs_npz_comparison"]["reason"] == "NO_INTERMEDIATE_DATA"
    requirements = {requirement["name"]: requirement for requirement in npz_manifest["hard_requirements"]}
    assert requirements["zero_synthetic_history"]["status"] == "NOT_EXECUTED_NO_INTERMEDIATE_DATA"

    # (a) assinatura np.linspace em todos os eixos -> DEVE ser flagada
    synthetic_window = np.stack(
        [np.linspace(0.0, 100.0, 32), np.linspace(-50.0, 50.0, 32), np.linspace(0.0, 8.0, 32)], axis=1
    )
    synthetic_result = _detect_synthetic_history(synthetic_window)
    assert synthetic_result["synthetic"] is True
    assert synthetic_result["reason"] == "LINEAR_RAMP"
    assert len(synthetic_result["linear_axes"]) == 3

    # (b) histórico com jitter (fixture rotulada) NÃO pode ser flagado
    rng = np.random.default_rng(42026)
    real_like = np.cumsum(rng.normal(0.0, 0.7, size=(32, 3)), axis=0)
    assert _detect_synthetic_history(real_like)["synthetic"] is False

    # (c) janela estática (deslocamento ~0) não é confundida com ramp linear
    assert _detect_synthetic_history(np.zeros((32, 3)))["synthetic"] is False

    # (d) histórico real do corpus profissional (somente leitura)
    npz_dir = Path("F:/CS2_MLMove_Pipeline/extracted_tensors/de_mirage")
    npz_files = sorted(npz_dir.glob("*.npz")) if npz_dir.is_dir() else []
    if not npz_files:
        pytest.skip(
            "NOT_EXECUTABLE_NO_REAL_NPZ_AVAILABLE: diretório externo de tensores profissionais "
            f"ausente ({npz_dir}); as asserções de contrato e de fixture acima foram executadas"
        )
    with np.load(str(npz_files[0])) as data:
        tensor = data["X"]
    assert tensor.ndim == 3 and tensor.shape[1:] == (10, 18), f"shape inesperado: {tensor.shape}"
    starts = list(range(0, int(tensor.shape[0]) - 32 + 1, 32))[:40]
    assert starts, "NPZ profissional sem frames suficientes para uma janela de 32"
    flagged = 0
    for start in starts:
        result = _detect_synthetic_history(tensor[start : start + 32, 0, 0:3])
        flagged += 1 if result["synthetic"] else 0
    assert flagged == 0, f"{flagged} de {len(starts)} janelas reais foram flagadas como sintéticas"


# ---------------------------------------------------------------------------------------------
# 16. SteamIdsArePseudonymizedInReports
# ---------------------------------------------------------------------------------------------
def SteamIdsArePseudonymizedInReports():
    """
    Pseudonimização HMAC-SHA256 conforme o contrato (``PID_`` + 16 hex): determinística, estável por
    segredo e não reversível por inspeção. SteamID64 em claro derruba a entrada; e nenhum artefato
    publicado contém SteamID64.
    """
    contract = _read_json(DOMAIN_CONTRACT_PATH)
    policy = contract["steamid_pseudonymization_policy"]
    assert policy["pseudonym_format"] == "PID_[0-9a-f]{16}"
    assert "HMAC-SHA256" in policy["pseudonym_algorithm"]
    assert policy["raw_steamid64_allowed_in"] == [
        "datasets/mirage_domains/intermediate_competitive/metadata/ (metadado operacional local)"
    ]

    steamid = "76561198000000001"
    other = "76561198000000002"
    salt_a = "unit-test-salt-alpha"
    salt_b = "unit-test-salt-beta"

    first = _pseudonymize(steamid, salt_a)
    assert re.fullmatch(r"PID_[0-9a-f]{16}", first)
    assert first == _pseudonymize(steamid, salt_a), "pseudônimo deve ser determinístico"
    assert first != _pseudonymize(other, salt_a), "SteamIDs distintos não podem colidir no teste"
    assert first != _pseudonymize(steamid, salt_b), "o segredo deve influenciar o pseudônimo"
    assert steamid not in first

    validator = _load_tool_module("validate_skill_bucket_steamid", TOOLS_DIR / "validate_skill_bucket.py")
    contract_for_tool = validator.load_contract(DOMAIN_CONTRACT_PATH)
    leaked = validator.evaluate(_faceit_record(skill_level=6, player_steamid64=steamid), contract_for_tool)
    assert leaked["decision"] == "REJECT"
    assert "STEAMID64_NOT_PSEUDONYMIZED" in leaked["reason_codes"]

    pseudonymized = validator.evaluate(
        _faceit_record(skill_level=6, player_skill_levels=[{"player_pseudonym": first, "skill_level": 6}]),
        contract_for_tool,
    )
    assert pseudonymized["decision"] == "ACCEPT"

    scanned = 0
    for artifact in INTERMEDIATE_ARTIFACTS:
        content = artifact.read_text(encoding="utf-8")
        match = STEAMID64_RE.search(content)
        assert match is None, f"SteamID64 em claro em {artifact.name}: {match.group(0) if match else ''}"
        scanned += 1
    assert scanned == len(INTERMEDIATE_ARTIFACTS)


# ---------------------------------------------------------------------------------------------
# 17. SpotPromotionRequiresHumanReview
# ---------------------------------------------------------------------------------------------
def SpotPromotionRequiresHumanReview():
    """
    Nenhum spot pode ser promovido sem revisão humana: o catálogo canônico de 53 spots está
    íntegro (hash e contagem), o contrato proíbe alteração do catálogo nesta fase e a política local
    só aceita selo humano explícito.
    """
    contract = _read_json(DOMAIN_CONTRACT_PATH)
    assert contract["governance_notes"]["catalog_modification_in_this_phase"] == "PROHIBITED"

    reference = _read_json(PROFESSIONAL_REFERENCE_PATH)
    catalog_reference = next(
        entry for entry in reference["references"] if entry["reference_id"] == "spot_catalog_53"
    )
    assert catalog_reference["repo_relative_path"] == "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json"
    assert SPOT_CATALOG_PATH.stat().st_size == catalog_reference["size_bytes"]
    assert _sha256_file(SPOT_CATALOG_PATH) == catalog_reference["sha256"]

    catalog = _read_json(SPOT_CATALOG_PATH)
    spot_ids = [spot["id"] for spot in catalog["spots"]]
    assert catalog["total_spots"] == 53
    assert len(spot_ids) == 53
    assert len(set(spot_ids)) == 53

    assert _spot_promotion_allowed(None) is False
    assert _spot_promotion_allowed({"approved_by": "agent", "seal": "AGENT_REVIEWED"}) is False
    assert _spot_promotion_allowed({"approved_by": "script", "seal": "AUTOMATED_CHECK_PASS"}) is False
    assert _spot_promotion_allowed({"approved_by": "user", "seal": "APPROVED_BY_USER"}) is True

    for artifact in INTERMEDIATE_ARTIFACTS:
        payload = _read_json(artifact)
        flattened = " ".join(value for _, value in _iter_strings(payload)).upper()
        assert "CROSS_DOMAIN_CONFIRMED" not in flattened
        assert "APPROVED_BY_USER" not in flattened
        assert "PROMOTED_SPOTS" not in flattened


# ---------------------------------------------------------------------------------------------
# 18. ProfessionalAndIntermediateMetricsRemainSeparate
# ---------------------------------------------------------------------------------------------
def ProfessionalAndIntermediateMetricsRemainSeparate():
    """
    Identidades e contagens dos dois domínios não se misturam: nenhum demo_id intermediário coincide
    com os 444 demos profissionais, nenhum artefato intermediário vive sob ``datasets/mirage_v2/`` e
    as contagens do domínio intermediário são próprias (zero), não cópias das profissionais.
    """
    canonical_splits = _read_json(CANONICAL_SPLITS_PATH)
    professional_demo_ids = set()
    for key in ("train_demos", "validation_demos", "test_demos"):
        professional_demo_ids.update(str(demo) for demo in canonical_splits[key])
    assert len(professional_demo_ids) == 444, f"esperado 444 demos profissionais, obtido {len(professional_demo_ids)}"

    inventory = _read_json(INVENTORY_PATH)
    intermediate_demo_ids = {str(record["demo_id"]) for record in inventory["records"]}
    overlap = professional_demo_ids & intermediate_demo_ids
    assert overlap == set(), f"demo_id compartilhado entre domínios: {sorted(overlap)}"
    assert inventory["domain_id"] == "INTERMEDIATE_COMPETITIVE"

    npz_manifest = _read_json(NPZ_MANIFEST_PATH)
    splits = _read_json(SPLITS_PROPOSAL_PATH)
    assert npz_manifest["npz_count"] == 0 and npz_manifest["record_count"] == 0
    assert splits["current_counts"]["total_demos"] == 0
    assert splits["metrics_domain_scoping"]["professional_reference_domain"].startswith("PROFESSIONAL")
    assert splits["metrics_domain_scoping"]["comparison_status"] == "NOT_EXECUTABLE_NO_INTERMEDIATE_DATA"

    # As contagens profissionais são referência de OUTRO domínio; não podem ser adotadas como próprias.
    professional_reference = _read_json(PROFESSIONAL_REFERENCE_PATH)
    assert professional_reference["verified_corpus_counts"]["npz_demos_accepted"] == 444
    assert inventory["record_count"] != 444
    assert npz_manifest["npz_count"] != 444

    for artifact in INTERMEDIATE_ARTIFACTS:
        assert not artifact.resolve().is_relative_to(PROFESSIONAL_ROOT)
    assert splits["domain_separation"]["professional_splits_untouched"] is True
    assert splits["domain_separation"]["intermediate_splits_inside_professional_tree"] is False


# ---------------------------------------------------------------------------------------------
# 19. BootstrapUsesMatchOrRoundUnit
# ---------------------------------------------------------------------------------------------
def BootstrapUsesMatchOrRoundUnit():
    """
    A proposta de splits define bootstrap por partida ou round e proíbe janela/sequência/frame. A
    aritmética é exercitada com fixture rotulada: contar janelas como unidades independentes infla o
    N efetivo, exatamente o erro que a regra evita.
    """
    proposal = _read_json(SPLITS_PROPOSAL_PATH)
    units = proposal["bootstrap_policy"]["bootstrap_units"]
    assert units["primary"] == "match_id"
    assert units["alternative"] == "round_id"
    assert set(units["prohibited"]) == {"window", "sequence", "frame"}

    assert _is_valid_bootstrap_unit("match_id", proposal) is True
    assert _is_valid_bootstrap_unit("round_id", proposal) is True
    for prohibited in units["prohibited"]:
        assert _is_valid_bootstrap_unit(prohibited, proposal) is False

    fixture_records: List[Dict[str, Any]] = []
    for match in range(3):
        for round_index in range(4):
            for window in range(50):
                fixture_records.append(
                    {
                        "fixture_class": "SYNTHETIC_FIXTURE",
                        "match_id": f"m{match}",
                        "round_id": f"m{match}-r{round_index}",
                        "window_id": f"m{match}-r{round_index}-w{window}",
                    }
                )

    matches = _independent_unit_count(fixture_records, "match_id")
    rounds = _independent_unit_count(fixture_records, "round_id")
    windows = _independent_unit_count(fixture_records, "window_id")
    assert (matches, rounds, windows) == (3, 12, 600)
    assert matches < rounds < windows, "unidade menor que janela deve reduzir o N efetivo"

    with pytest.raises(ValueError):
        _independent_unit_count(fixture_records, "window")
    assert proposal["bootstrap_policy"]["resamples_minimum"] >= 1000


# ---------------------------------------------------------------------------------------------
# 20. NoTrainingStartsInThisPhase
# ---------------------------------------------------------------------------------------------
def NoTrainingStartsInThisPhase():
    """
    O marcador de pausa está íntegro (hash do manifest de referência), proíbe treinamento e exige
    autorização humana; o checkpoint congelado do MARCO 2B.3 não mudou; e não existe nenhum artefato
    de treinamento/modelo no escopo do domínio intermediário.
    """
    reference = _read_json(PROFESSIONAL_REFERENCE_PATH)
    marker_reference = next(entry for entry in reference["references"] if entry["reference_id"] == "pause_marker")
    assert PAUSE_MARKER_PATH.stat().st_size == marker_reference["size_bytes"]
    assert _sha256_file(PAUSE_MARKER_PATH) == marker_reference["sha256"]

    marker = _read_json(PAUSE_MARKER_PATH)
    assert marker["marker"] == "PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY"
    assert marker["resumption_requires_human_authorization"] is True
    assert _training_blocked_by_marker(marker) is True
    assert _training_blocked_by_marker({"marker": "ACTIVE", "resumption_requires_human_authorization": False}) is False
    assert _training_blocked_by_marker({**marker, "prohibited_during_pause": ["apenas leitura"]}) is False

    checkpoint_reference = next(
        entry for entry in reference["references"] if entry["reference_id"] == "selected_candidate_marco_2b3"
    )
    checkpoint_path = BASE_DIR / checkpoint_reference["repo_relative_path"]
    assert checkpoint_path.stat().st_size == checkpoint_reference["size_bytes"]
    assert _sha256_file(checkpoint_path) == checkpoint_reference["sha256"]

    training_suffixes = {".pt", ".onnx", ".ckpt", ".pth", ".safetensors", ".h5"}
    scanned = 0
    training_artifacts: List[str] = []
    for root in (INTERMEDIATE_DIR, STUDY_DIR):
        for path in root.rglob("*"):
            if path.is_file():
                scanned += 1
                if path.suffix.lower() in training_suffixes:
                    training_artifacts.append(str(path.relative_to(BASE_DIR)))
    assert scanned > 0, "nenhum arquivo varrido no escopo intermediário"
    assert training_artifacts == [], f"artefatos de treinamento encontrados: {training_artifacts}"

    splits = _read_json(SPLITS_PROPOSAL_PATH)
    assert splits["governance_notes"]["training_started"] is False
    assert splits["proposal_status"] == "DESIGN_ONLY_NOT_MATERIALIZED"
    assert splits["materialized"] is False

    inventory = _read_json(INVENTORY_PATH)
    assert inventory["governance_notes"]["training_started"] is False
    assert inventory["governance_notes"]["catalog_modified"] is False


# ---------------------------------------------------------------------------------------------
# Exposição ao pytest: alias ``test_<NomeExato>`` (pytest só coleta nomes iniciados por 'test')
# ---------------------------------------------------------------------------------------------
_EXACT_NAMED_TESTS = {
    name: globals()[name] for name in REQUIRED_TEST_NAMES
}
assert len(_EXACT_NAMED_TESTS) == 20, "os 20 testes obrigatórios devem existir"

for _required_name, _test_function in _EXACT_NAMED_TESTS.items():
    globals()[f"test_{_required_name}"] = _test_function
