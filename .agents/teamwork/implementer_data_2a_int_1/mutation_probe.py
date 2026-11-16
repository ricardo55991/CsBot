"""Sonda de mutacao (mutation probe) da suite M8 — FASE 2A-INTERMEDIATE.

Objetivo: provar que os testes NAO sao fachada. Para cada teste amostrado, aplica-se uma
violacao conhecida sobre um COPIA em diretorio temporario e verifica-se que o teste falha
(AssertionError). Nenhum arquivo do repositorio e escrito ou modificado.

Uso:
    python .agents/teamwork/implementer_data_2a_int_1/mutation_probe.py

Saida: uma linha por sonda com PROBE_OK (teste detectou a violacao) ou PROBE_FAIL
(teste passou apesar da violacao -> fachada).
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TEST_FILE = BASE / "tests" / "test_phase2a_intermediate_domain.py"
IC = BASE / "datasets" / "mirage_domains" / "intermediate_competitive"


def load_suite():
    spec = importlib.util.spec_from_file_location("suite_m8", TEST_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["suite_m8"] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    suite = load_suite()
    results = []

    def probe(name, mutate, test_function):
        """Aplica `mutate(suite, tmp)` e exige que `test_function()` falhe."""
        with tempfile.TemporaryDirectory(prefix="csbot_probe_") as tmp:
            originals = mutate(suite, Path(tmp))
            try:
                test_function()
            except AssertionError as error:
                message = str(error).strip().splitlines()
                detail = message[0] if message else "AssertionError (sem mensagem — asserção booleana)"
                results.append((name, "PROBE_OK", detail[:110]))
            except Exception as error:  # noqa: BLE001 - qualquer erro diferente de AssertionError e suspeito
                results.append((name, "PROBE_ERROR", f"{type(error).__name__}: {error}"[:110]))
            else:
                results.append((name, "PROBE_FAIL", "teste passou com a regra violada"))
            finally:
                for attribute, value in originals.items():
                    setattr(suite, attribute, value)

    # 1) Corpo profissional adulterado: hash registrado trocado por zeros -> ProfessionalCorpusRemainsUnchanged deve falhar.
    def mutate_professional(suite, tmp):
        payload = json.loads(suite.PROFESSIONAL_REFERENCE_PATH.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(payload)
        mutated["references"][0]["sha256"] = "0" * 64
        target = _write(tmp / "professional_tampered.json", mutated)
        original = suite.PROFESSIONAL_REFERENCE_PATH
        suite.PROFESSIONAL_REFERENCE_PATH = target
        return {"PROFESSIONAL_REFERENCE_PATH": original}

    probe("ProfessionalCorpusRemainsUnchanged", mutate_professional, suite.ProfessionalCorpusRemainsUnchanged)

    # 2) Arquivo .dem plantado no diretorio intermediario -> IntermediateCorpusUsesSeparateDirectory deve falhar.
    def mutate_intermediate_dir(suite, tmp):
        planted = tmp / "intermediate_with_demo"
        planted.mkdir(parents=True, exist_ok=True)
        (planted / "planted_probe.dem").write_bytes(b"NOT-A-REAL-DEMO")
        original = suite.INTERMEDIATE_DIR
        suite.INTERMEDIATE_DIR = planted
        return {"INTERMEDIATE_DIR": original}

    probe("IntermediateCorpusUsesSeparateDirectory", mutate_intermediate_dir, suite.IntermediateCorpusUsesSeparateDirectory)

    # 8) URL assinada persistida no manifesto do piloto -> SignedUrlsAreNotPersisted deve falhar.
    def mutate_signed_url(suite, tmp):
        payload = json.loads(suite.PILOT_MANIFEST_PATH.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(payload)
        mutated["signed_urls_persisted"] = 1
        target = _write(tmp / "pilot_signed.json", mutated)
        original = suite.PILOT_MANIFEST_PATH
        suite.PILOT_MANIFEST_PATH = target
        return {"PILOT_MANIFEST_PATH": original}

    probe("SignedUrlsAreNotPersisted", mutate_signed_url, suite.SignedUrlsAreNotPersisted)

    # 18) demo_id intermediario copiado do dominio profissional -> ProfessionalAndIntermediateMetricsRemainSeparate deve falhar.
    def mutate_overlap(suite, tmp):
        inventory = json.loads(suite.INVENTORY_PATH.read_text(encoding="utf-8"))
        splits = json.loads(suite.CANONICAL_SPLITS_PATH.read_text(encoding="utf-8"))
        leaked_demo = str(splits["test_demos"][0])
        mutated = copy.deepcopy(inventory)
        mutated["records"] = [{"demo_id": leaked_demo, "fixture_class": "SYNTHETIC_FIXTURE"}]
        mutated["record_count"] = 1
        target = _write(tmp / "inventory_overlap.json", mutated)
        originals = {"INVENTORY_PATH": suite.INVENTORY_PATH}
        suite.INVENTORY_PATH = target
        return originals

    probe(
        "ProfessionalAndIntermediateMetricsRemainSeparate",
        mutate_overlap,
        suite.ProfessionalAndIntermediateMetricsRemainSeparate,
    )

    # 19) bootstrap por janela declarado na proposta -> BootstrapUsesMatchOrRoundUnit deve falhar.
    def mutate_bootstrap(suite, tmp):
        payload = json.loads(suite.SPLITS_PROPOSAL_PATH.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(payload)
        mutated["bootstrap_policy"]["bootstrap_units"]["primary"] = "window"
        target = _write(tmp / "splits_window_unit.json", mutated)
        original = suite.SPLITS_PROPOSAL_PATH
        suite.SPLITS_PROPOSAL_PATH = target
        return {"SPLITS_PROPOSAL_PATH": original}

    probe("BootstrapUsesMatchOrRoundUnit", mutate_bootstrap, suite.BootstrapUsesMatchOrRoundUnit)

    # 20) treinamento declarado como iniciado -> NoTrainingStartsInThisPhase deve falhar.
    def mutate_training(suite, tmp):
        payload = json.loads(suite.SPLITS_PROPOSAL_PATH.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(payload)
        mutated["governance_notes"]["training_started"] = True
        target = _write(tmp / "splits_training_started.json", mutated)
        original = suite.SPLITS_PROPOSAL_PATH
        suite.SPLITS_PROPOSAL_PATH = target
        return {"SPLITS_PROPOSAL_PATH": original}

    probe("NoTrainingStartsInThisPhase", mutate_training, suite.NoTrainingStartsInThisPhase)

    # 14) lifecycle de round com salto temporal dentro do round -> RoundLifecycleIsValid deve falhar.
    def mutate_round_time(suite, tmp):
        # A violacao e injetada interceptando o construtor da fixture valida.
        original_builder = suite._build_round_session
        original_validator = suite._validate_round_lifecycle

        def tampered_builder(rounds=2, frames_per_round=8):
            session = original_builder(rounds=rounds, frames_per_round=frames_per_round)
            session["frames"][4]["round_time_norm"] = 0.999  # salto para cima dentro do round
            return session

        def strict_validator(session):
            errors = original_validator(session)
            if "ROUND_TIME_NOT_MONOTONIC_WITHIN_ROUND" not in errors:
                raise AssertionError("validador nao detectou o salto temporal injetado")
            return ["ROUND_TIME_NOT_MONOTONIC_WITHIN_ROUND"]

        suite._build_round_session = tampered_builder
        suite._validate_round_lifecycle = strict_validator
        return {"_build_round_session": original_builder, "_validate_round_lifecycle": original_validator}

    probe("RoundLifecycleIsValid", mutate_round_time, suite.RoundLifecycleIsValid)

    # 15) detector de historico sintetico cego -> IntermediateNpZContainsNoSyntheticHistory deve falhar.
    def mutate_detector(suite, tmp):
        def blind_detector(positions, min_displacement=1.0):
            return {"synthetic": False, "linear_axes": [], "reason": "OK"}

        original = suite._detect_synthetic_history
        suite._detect_synthetic_history = blind_detector
        return {"_detect_synthetic_history": original}

    probe("IntermediateNpZContainsNoSyntheticHistory", mutate_detector, suite.IntermediateNpZContainsNoSyntheticHistory)

    # 16) pseudonimizacao sem segredo (identidade reversivel) -> SteamIdsArePseudonymizedInReports deve falhar.
    def mutate_pseudonym(suite, tmp):
        def identity_pseudonym(steamid64, salt):
            return steamid64  # SteamID64 em claro: violacao direta da politica

        original = suite._pseudonymize
        suite._pseudonymize = identity_pseudonym
        return {"_pseudonymize": original}

    probe("SteamIdsArePseudonymizedInReports", mutate_pseudonym, suite.SteamIdsArePseudonymizedInReports)

    # 17) promocao de spot liberada para agente -> SpotPromotionRequiresHumanReview deve falhar.
    def mutate_promotion(suite, tmp):
        def permissive(record):
            return True

        original = suite._spot_promotion_allowed
        suite._spot_promotion_allowed = permissive
        return {"_spot_promotion_allowed": original}

    probe("SpotPromotionRequiresHumanReview", mutate_promotion, suite.SpotPromotionRequiresHumanReview)

    width = max(len(name) for name, _, _ in results)
    print("=" * 118)
    print("MUTATION PROBE — suite M8 (cada linha aplica uma violacao e exige que o teste FALHE)")
    print("=" * 118)
    for name, status, detail in results:
        print(f"{name.ljust(width)}  {status:<11}  {detail}")

    failures = [row for row in results if row[1] != "PROBE_OK"]
    print("=" * 118)
    print(f"sondas={len(results)}  PROBE_OK={len(results) - len(failures)}  falhas={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
