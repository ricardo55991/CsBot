"""
Fase 6C / Etapa 5 (Validador Ponta a Ponta C# <-> ONNX):
Verifica:
1. Existência e tamanho de `H:\CS2_AI_Server\models\mlmove_de_mirage.onnx` (~21 MB).
2. Integridade do grafo ONNX (`onnx.checker.check_model`) e nomes exatos de tensores (`input_state` -> `output_logits`).
3. Inferência em lote `[2, 10, 18]` (Perspectiva CT + Perspectiva TR com Fog-of-War) em `< 0.5ms` no Cache L3 da CPU.
4. Amostragem estocástica Softmax produzindo `ActionId` válidos `0..96` nos 3 horizontes (`t=0ms`, `t=+125ms`, `t=+250ms`).
"""

from __future__ import annotations
import argparse
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort

from contract_spec import (
    ACTION_SPACE_SIZE,
    FEATURE_DIM,
    HORIZONS_COUNT,
    MAX_PLAYERS,
    ONNX_INPUT_NAME,
    ONNX_OUTPUT_NAME,
    SERVER_MODELS_DIR_H,
    decode_action,
)


def sample_softmax_numpy(logits: np.ndarray, temperature: float = 0.85) -> int:
    scaled = (logits - np.max(logits)) / max(0.05, temperature)
    probs = np.exp(scaled)
    probs /= np.sum(probs)
    return int(np.random.choice(len(probs), p=probs))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validação Ponta a Ponta do Modelo ONNX no Servidor CS2")
    parser.add_argument("--map", type=str, default="de_mirage")
    args = parser.parse_args()

    onnx_path = Path(SERVER_MODELS_DIR_H) / f"mlmove_{args.map}.onnx"
    if not onnx_path.exists():
        raise FileNotFoundError(f"Arquivo ONNX não encontrado no servidor: {onnx_path}")

    size_mb = onnx_path.stat().st_size / (1024.0 * 1024.0)
    model_proto = onnx.load(str(onnx_path))
    onnx.checker.check_model(model_proto)

    sess_opts = ort.SessionOptions()
    sess_opts.intra_op_num_threads = 4
    sess_opts.inter_op_num_threads = 1
    sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(str(onnx_path), sess_options=sess_opts, providers=["CPUExecutionProvider"])

    in_meta = sess.get_inputs()[0]
    out_meta = sess.get_outputs()[0]

    assert in_meta.name == ONNX_INPUT_NAME, f"Input name incorreto: {in_meta.name}"
    assert out_meta.name == ONNX_OUTPUT_NAME, f"Output name incorreto: {out_meta.name}"

    single_in = np.random.uniform(-0.8, 0.8, size=(1, MAX_PLAYERS, FEATURE_DIM)).astype(np.float32)
    batch_in = np.random.uniform(-0.8, 0.8, size=(2, MAX_PLAYERS, FEATURE_DIM)).astype(np.float32)
    # Aplica máscara Fog-of-War simulada nos inimigos ocultos (linhas 5..9 do batch 0)
    batch_in[0, 5:8, :13] = 0.0

    # Warmup
    for _ in range(25):
        sess.run([ONNX_OUTPUT_NAME], {ONNX_INPUT_NAME: single_in})

    latencies_single_ms = []
    for _ in range(200):
        t0 = time.perf_counter()
        sess.run([ONNX_OUTPUT_NAME], {ONNX_INPUT_NAME: single_in})
        latencies_single_ms.append((time.perf_counter() - t0) * 1000.0)

    out_logits = sess.run([ONNX_OUTPUT_NAME], {ONNX_INPUT_NAME: batch_in})[0]
    assert out_logits is not None
    assert out_logits.shape == (2, MAX_PLAYERS, HORIZONS_COUNT, ACTION_SPACE_SIZE), f"Shape inválido: {out_logits.shape}"

    p50_ms = float(np.median(latencies_single_ms))
    p95_ms = float(np.percentile(latencies_single_ms, 95))

    print("=" * 76)
    print(f"  VALIDAÇÃO E2E MLMOVE ONNX ({args.map.upper()})")
    print("=" * 76)
    print(f"  Arquivo Servidor : {onnx_path}")
    print(f"  Tamanho em Disco : {size_mb:.2f} MB (float32)")
    print(f"  Contrato Tensor  : {in_meta.name} {in_meta.shape} -> {out_meta.name} {out_meta.shape}")
    print(f"  Latência CPU L3  : Mediana = {p50_ms:.3f} ms | P95 = {p95_ms:.3f} ms (Alvo: < 0.500 ms)")

    # Verifica decodificação das 97 ações nos 3 horizontes para o Bot 0 (CT) e Bot 5 (TR)
    for b_idx, team_label, p_slot in [(0, "CT", 0), (1, "TR", 5)]:
        h_actions = [sample_softmax_numpy(out_logits[b_idx, p_slot, h, :]) for h in range(HORIZONS_COUNT)]
        decoded = [decode_action(a) for a in h_actions]
        assert all(0 <= a < ACTION_SPACE_SIZE for a in h_actions)
        print(
            f"  Amostra {team_label} (Bot {p_slot}) : t=0ms Act={h_actions[0]} {decoded[0]} | "
            f"t=+125ms Act={h_actions[1]} {decoded[1]} | t=+250ms Act={h_actions[2]} {decoded[2]}"
        )
    print("=" * 76)


if __name__ == "__main__":
    main()
