#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 1: Suíte de Testes Unitários de Governança do DataLoader Temporal Canônico.

Valida os 5 pilares do Marco 1:
1. Busca determinística de round por frame_index (garantindo zero violações de fronteira mesmo com warmup pulado).
2. Mascaramento estrito de padding para k < 32 frames (zero unmasked padding).
3. Ausência total de vazamento temporal futuro (t <= f_idx).
4. Slots reais de aliados sem clones transladados.
5. Ausência absoluta de np.linspace ou step_drift.
6. Materialização formal dos splits dos 444 NPZs em canonical_temporal_splits_v1.json.
"""

import os
import sys
import json
import inspect
from pathlib import Path

import pytest
import numpy as np
import torch
from torch.utils.data import DataLoader

# Raiz no sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    NPZCacheManager,
    CanonicalTemporalPositioningDataset,
    create_canonical_temporal_dataloader,
    canonical_collate_fn,
    load_canonical_temporal_splits,
    DEFAULT_NPZ_DIR
)
import tools.phase3a_training.data_utils as data_utils


@pytest.fixture(scope="module")
def npz_cache():
    return NPZCacheManager(npz_dir=DEFAULT_NPZ_DIR)


@pytest.fixture(scope="module")
def sample_demo_info(npz_cache):
    # Carregar uma demo real para validação
    demo_id = "100-thieves-vs-magic-m2-mirage"
    return npz_cache.load_demo(demo_id)


def test_deterministic_round_search_by_frame_index(sample_demo_info):
    """
    Bloqueador 1: Verifica que a determinação de start_f e end_f usando
    searchsorted por f_idx garante matematicamente start_f <= f_idx < end_f,
    mesmo que o round_idx seja arbitrário ou corrompido (ex: warmup rounds descartados).
    """
    round_bounds = sample_demo_info["round_bounds"]
    n_frames = sample_demo_info["n_frames"]

    assert len(round_bounds) >= 2, "A demo deve possuir ao menos 1 round delimitado."

    # Testar em vários pontos no interior de cada round
    for r_idx in range(len(round_bounds) - 1):
        s_f = round_bounds[r_idx]
        e_f = round_bounds[r_idx + 1]

        test_frames = [
            s_f,                       # Primeiro frame do round
            s_f + 1,                   # Segundo frame
            (s_f + e_f) // 2,          # Meio do round
            e_f - 1                    # Último frame do round
        ]

        for f_idx in test_frames:
            # Algoritmo determinístico canônico
            r_det = int(np.searchsorted(round_bounds, f_idx, side="right") - 1)
            r_det = max(0, min(r_det, len(round_bounds) - 2))
            det_start = int(round_bounds[r_det])
            det_end = int(round_bounds[r_det + 1])

            # Invariante 1: O frame pertence estritamente ao round detectado
            assert det_start <= f_idx < det_end, (
                f"Fronteira violada: frame {f_idx} fora de [{det_start}, {det_end})"
            )
            # Invariante 2: O round detectado bate com o round real
            assert r_det == r_idx, f"Round detectado {r_det} != round real {r_idx}"


def test_adversarial_round_idx_immunity(npz_cache):
    """
    Verifica que passar um round_idx propositadamente falso / dessincronizado
    NÃO causa vazamento de fronteira de round, pois o loader usa f_idx.
    """
    demo_id = "100-thieves-vs-magic-m2-mirage"
    demo_entry = npz_cache.load_demo(demo_id)
    round_bounds = demo_entry["round_bounds"]

    # Frame do round 2 (ex: round_bounds[2] + 10)
    round_2_start = round_bounds[2]
    f_idx = round_2_start + 10
    adversarial_round_idx = 0 # Tentativa de forçar round 0

    h, tm, mask = npz_cache.extract_window(
        demo_id=demo_id,
        round_idx=adversarial_round_idx, # Ignorado em favor de f_idx
        slot=0,
        f_idx=f_idx
    )

    # Como f_idx - round_2_start = 10 (< 32), k = 11
    k = f_idx - round_2_start + 1
    assert k == 11
    # Deve estar com padding nos primeiros 32 - 11 = 21 frames
    assert np.all(mask[: 32 - k] == 0.0), "Padding inicial deve estar mascarado como 0.0"
    assert np.all(mask[32 - k :] == 1.0), "Frames válidos devem estar mascarados como 1.0"
    assert np.all(h[: 32 - k] == 0.0), "Frames de padding devem ser estritamente zero"
    # E o frame 31 deve bater com o frame f_idx do round 2
    raw_X = demo_entry["X"]
    assert np.allclose(h[31], raw_X[f_idx, 0], atol=1e-5), "Frame f_idx deve ser autêntico"


def test_masked_padding_early_round(npz_cache, sample_demo_info):
    """
    Bloqueador 1 & Requisito R1:
    Testa que para k = f_idx - start_f + 1 < 32:
    - temporal_mask[:32-k] == 0.0
    - temporal_mask[32-k:] == 1.0
    - history[:32-k] == 0.0
    - history[32-k:] == X[start_f : f_idx + 1]
    - UnmaskedPaddingRate = 0.0%
    """
    round_bounds = sample_demo_info["round_bounds"]
    raw_X = sample_demo_info["X"]
    demo_id = sample_demo_info["demo_id"]

    start_f = round_bounds[1]

    for k in [1, 5, 16, 31]:
        f_idx = start_f + k - 1
        pad_len = 32 - k

        h, tm, mask = npz_cache.extract_window(
            demo_id=demo_id,
            round_idx=1,
            slot=0,
            f_idx=f_idx
        )

        assert mask.shape == (32,)
        assert h.shape == (32, 18)
        assert tm.shape == (32, 4, 18)

        # Máscara temporal
        assert np.all(mask[:pad_len] == 0.0), f"Unmasked padding detectado para k={k}!"
        assert np.all(mask[pad_len:] == 1.0), f"Frames válidos desmascarados para k={k}!"
        assert np.isclose(np.sum(mask), float(k)), f"Soma da máscara ({np.sum(mask)}) != k ({k})"

        # Zeros em padding
        assert np.all(h[:pad_len] == 0.0), f"Padding do jogador não-nulo para k={k}!"
        assert np.all(tm[:pad_len] == 0.0), f"Padding dos aliados não-nulo para k={k}!"

        # Conteúdo autêntico nos frames válidos
        expected_h = raw_X[start_f : f_idx + 1, 0, :]
        assert np.allclose(h[pad_len:], expected_h, atol=1e-5), f"Dados autênticos divergiram para k={k}!"


def test_zero_future_leakage(npz_cache, sample_demo_info):
    """
    Bloqueador 1 & Requisito R1:
    Verifica que nenhum frame posterior a f_idx (t > f_idx) é lido.
    A janela termina exatamente em f_idx.
    """
    demo_id = sample_demo_info["demo_id"]
    raw_X = sample_demo_info["X"]
    f_idx = 500

    h, tm, mask = npz_cache.extract_window(
        demo_id=demo_id,
        round_idx=0,
        slot=2,
        f_idx=f_idx
    )

    # O frame final do histórico deve ser exatamente f_idx
    assert np.allclose(h[31], raw_X[f_idx, 2], atol=1e-5), "Último frame deve ser exatamente f_idx!"

    # O frame futuro f_idx + 1 NÃO pode estar no histórico
    if f_idx + 1 < len(raw_X):
        future_frame = raw_X[f_idx + 1, 2]
        # Se houve movimento entre f_idx e f_idx + 1
        if not np.allclose(raw_X[f_idx, 2, :3], future_frame[:3], atol=1e-4):
            # Garante que o frame futuro não foi inserido
            assert not np.allclose(h[31, :3], future_frame[:3], atol=1e-4), (
                "Detectado Future Leakage: frame futuro presente no histórico!"
            )


def test_real_teammate_slots_no_clones(npz_cache, sample_demo_info):
    """
    Bloqueador 1 & Requisito R1:
    Verifica que os 4 companheiros de equipe são extraídos dos slots reais
    sem translações artificiais nem clones.
    """
    demo_id = sample_demo_info["demo_id"]
    raw_X = sample_demo_info["X"]
    f_idx = 1000

    # Teste para Time 1 (slot < 5)
    for slot in range(5):
        h, tm, mask = npz_cache.extract_window(demo_id=demo_id, round_idx=1, slot=slot, f_idx=f_idx)
        expected_tm_slots = [s for s in range(5) if s != slot]
        for tm_i, expected_slot in enumerate(expected_tm_slots):
            # Deve ser idêntico ao NPZ cru do slot real
            expected_raw = raw_X[f_idx - 31 : f_idx + 1, expected_slot, :]
            assert np.allclose(tm[:, tm_i, :], expected_raw, atol=1e-5), (
                f"Aliado {tm_i} (slot {expected_slot}) divergiu do NPZ cru!"
            )
            # Não pode ser clone com offset artificial
            for offset_mul in [1, 2, 3, 4]:
                fake_offset = offset_mul * 0.05
                assert not np.allclose(tm[:, tm_i, 0] - h[:, 0], fake_offset, atol=1e-4), (
                    f"Detectado clone sintético com offset {fake_offset}!"
                )

    # Teste para Time 2 (slot >= 5)
    for slot in range(5, 10):
        h, tm, mask = npz_cache.extract_window(demo_id=demo_id, round_idx=1, slot=slot, f_idx=f_idx)
        expected_tm_slots = [s for s in range(5, 10) if s != slot]
        for tm_i, expected_slot in enumerate(expected_tm_slots):
            expected_raw = raw_X[f_idx - 31 : f_idx + 1, expected_slot, :]
            assert np.allclose(tm[:, tm_i, :], expected_raw, atol=1e-5), (
                f"Aliado {tm_i} (slot {expected_slot}) divergiu do NPZ cru!"
            )


def test_no_linspace_or_step_drift():
    """
    Regra Inegociável & Requisito R1:
    Verifica que nenhum arquivo de código em tools/phase3a_training/ utiliza
    np.linspace ou step_drift para síntese artificial de trajetória temporal.
    """
    import tools.phase3a_training.canonical_temporal_dataloader as ctd
    import tools.phase3a_training.data_utils as du

    src_ctd = inspect.getsource(ctd)
    src_du = inspect.getsource(du)

    assert "step_drift =" not in src_ctd, "canonical_temporal_dataloader atribui step_drift!"
    assert "step_drift =" not in src_du, "data_utils atribui step_drift!"
    assert "np.linspace(" not in src_ctd, "canonical_temporal_dataloader chama np.linspace!"
    assert "np.linspace(" not in src_du, "data_utils chama np.linspace!"


def test_canonical_splits_materialization_and_filtering():
    """
    Bloqueador 2:
    Verifica a materialização formal de datasets/mirage_v2/canonical_temporal_splits_v1.json:
    - schema_version: "1.0.0"
    - total_npz_demos: 444
    - train_demos: 311
    - validation_demos: 66
    - test_demos: 67
    - excluded_demos: 8 (entradas com source_format RAW_DEM_SOURCE2 em demo_inventory_v2.json)
    - Zero vazamento entre splits (Train, Validation e Test estritamente disjuntos)
    """
    ds_dir = BASE_DIR / "datasets" / "mirage_v2"
    splits_file = ds_dir / "canonical_temporal_splits_v1.json"

    assert splits_file.exists(), f"Arquivo {splits_file} não foi materializado!"

    with open(splits_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema_version"] == "1.0.0"
    assert data["total_npz_demos"] == 444
    assert len(data["train_demos"]) == 311
    assert len(data["validation_demos"]) == 66
    assert len(data["test_demos"]) == 67
    assert len(data["excluded_demos"]) == 8

    tr_set = set(data["train_demos"])
    va_set = set(data["validation_demos"])
    te_set = set(data["test_demos"])

    # Disjunção estrita entre splits de modelagem
    assert len(tr_set & va_set) == 0, "Vazamento detectado entre Train e Validation!"
    assert len(tr_set & te_set) == 0, "Vazamento detectado entre Train e Test!"
    assert len(va_set & te_set) == 0, "Vazamento detectado entre Validation e Test!"
    assert len(tr_set | va_set | te_set) == 444, "Total de demos ativas difere de 444!"

    # Demos excluídas correspondem exatamente às 8 entradas RAW_DEM_SOURCE2
    expected_excluded = {
        "charrados-vs-alka-m2-mirage",
        "depo-vs-winners-m2-mirage",
        "ding-cuts-vs-abyssal-m1-mirage",
        "dnk-vs-winners-m1-mirage",
        "mibr-academy-vs-bestia-academy-m2-mirage-p2",
        "mouz-nxt-vs-ursa-m2-mirage",
        "regain-vs-zomblers-m1-mirage",
        "tnc-vs-phantom-academy-m1-mirage"
    }
    assert set(data["excluded_demos"]) == expected_excluded, "Demos excluídas divergiram do inventário RAW_DEM!"


def test_dataloader_batch_integration():
    """
    Verifica que o create_canonical_temporal_dataloader emite lotes válidos
    com todas as chaves requeridas pelo PositioningTransformer e pelos auditores.
    """
    loader = create_canonical_temporal_dataloader(
        split="validation",
        batch_size=8,
        max_samples=16,
        preload_npz=True
    )

    batch = next(iter(loader))

    assert "history" in batch
    assert "teammates" in batch
    assert "temporal_mask" in batch
    assert "candidate_mask" in batch
    assert "positioning_state" in batch
    assert "metadata" in batch

    assert batch["history"].shape == (8, 32, 18)
    assert batch["teammates"].shape == (8, 32, 4, 18)
    assert batch["temporal_mask"].shape == (8, 32)
    assert batch["candidate_mask"].shape == (8, 53)
    assert len(batch["metadata"]) == 8
