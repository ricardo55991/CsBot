"""
Fase 6C (Camada 3 - Parte 2): Treinador Multi-Horizonte PyTorch + Exportador ONNX Direto para o Servidor.
- Lê todos os arquivos `.npz` de `D:\CS2_MLMove_Pipeline\extracted_tensors\<map>\`.
- Treina a rede `MLMoveTransformer` (~5.47M parâmetros, ~21 MB) usando `CrossEntropyLoss` somada nos 3 horizontes:
    L = L_0ms + L_125ms + L_250ms
  com otimizador `AdamW` e agendador `CosineAnnealingLR`.
- Aceleração automática via `torch-directml` (AMD Radeon RX 6600M) ou CPU multi-thread.
- Salva checkpoints `.pt` em `D:\CS2_MLMove_Pipeline\checkpoints\`.
- Exporta `H:\CS2_AI_Server\models\mlmove_<map>.onnx` com validação `onnx.checker` + benchmark `onnxruntime`.
"""

from __future__ import annotations
import argparse
import copy
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import onnx
import onnxruntime as ort
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from contract_spec import (
    ACTION_SPACE_SIZE,
    CHECKPOINTS_DIR_D,
    EXTRACTED_TENSORS_DIR_D,
    FEATURE_DIM,
    HORIZONS_COUNT,
    MAX_PLAYERS,
    ONNX_INPUT_NAME,
    ONNX_OUTPUT_NAME,
    SERVER_MODELS_DIR_H,
)
from model_mlmove import MLMoveTransformer, count_parameters


class DirectMLAdamW(torch.optim.Optimizer):
    """
    Implementação de AdamW otimizada para AMD DirectML (RX 6600M) e CPU:
    Substitui `exp_avg.lerp_` (que causa fallback para CPU no DirectML) por `mul_` + `add_`,
    executando 100% dos shaders na GPU sem tráfego PCIe desnecessário.
    """

    def __init__(
        self,
        params,
        lr: float = 6e-4,
        betas: Tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 1e-4,
    ) -> None:
        defaults = dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            lr = group["lr"]
            beta1, beta2 = group["betas"]
            eps = group["eps"]
            wd = group["weight_decay"]

            for p in group["params"]:
                if p.grad is None:
                    continue
                grad = p.grad
                state = self.state[p]
                if len(state) == 0:
                    state["step"] = 0
                    state["exp_avg"] = torch.zeros_like(p)
                    state["exp_avg_sq"] = torch.zeros_like(p)

                state["step"] += 1
                step_t = state["step"]
                exp_avg = state["exp_avg"]
                exp_avg_sq = state["exp_avg_sq"]

                if wd != 0.0:
                    p.mul_(1.0 - lr * wd)

                exp_avg.mul_(beta1).add_(grad, alpha=1.0 - beta1)
                exp_avg_sq.mul_(beta2).add_(grad * grad, alpha=1.0 - beta2)

                bias_correction1 = 1.0 - (beta1 ** step_t)
                bias_correction2 = 1.0 - (beta2 ** step_t)
                step_size = lr / bias_correction1
                denom = (exp_avg_sq.sqrt() / (bias_correction2 ** 0.5)).add_(eps)
                p.add_(exp_avg / denom, alpha=-step_size)

        return loss


def select_training_device(prefer_dml: bool = True) -> Tuple[torch.device, str]:
    if prefer_dml:
        try:
            import torch_directml

            if torch_directml.is_available():
                dev = torch_directml.device()
                name = torch_directml.device_name(0)
                return dev, f"DirectML GPU ({name})"
        except Exception:
            pass
    if torch.cuda.is_available():
        return torch.device("cuda"), f"CUDA GPU ({torch.cuda.get_device_name(0)})"
    return torch.device("cpu"), f"CPU ({torch.get_num_threads()} threads)"


def load_dataset_for_map(map_name: str) -> Tuple[torch.Tensor, torch.Tensor]:
    tensor_dir = Path(EXTRACTED_TENSORS_DIR_D) / map_name
    npz_files: List[Path] = sorted(tensor_dir.glob("*.npz"))
    if not npz_files:
        raise FileNotFoundError(
            f"Nenhum arquivo .npz encontrado em {tensor_dir}. Rode generate_bootstrap_dataset.py ou extract_16hz_tensors.py primeiro."
        )

    X_chunks: List[np.ndarray] = []
    Y_chunks: List[np.ndarray] = []
    for f in npz_files:
        data = np.load(f)
        if "X" in data and "Y" in data and len(data["X"]) > 0:
            X_chunks.append(data["X"].astype(np.float32))
            Y_chunks.append(data["Y"].astype(np.int64))
            print(f"[train_and_export_onnx] Carregado {f.name}: {len(data['X']):,} amostras")

    X_all = np.concatenate(X_chunks, axis=0)
    Y_all = np.concatenate(Y_chunks, axis=0)
    return torch.from_numpy(X_all), torch.from_numpy(Y_all)


def export_to_server_onnx(model: MLMoveTransformer, map_name: str) -> Path:
    import io

    server_models_dir = Path(SERVER_MODELS_DIR_H)
    server_models_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = server_models_dir / f"mlmove_{map_name}.onnx"

    cpu_model = copy.deepcopy(model).to("cpu").eval()
    dummy_input = torch.zeros((2, MAX_PLAYERS, FEATURE_DIM), dtype=torch.float32)

    buf = io.BytesIO()
    torch.onnx.export(
        cpu_model,
        dummy_input,
        buf,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=[ONNX_INPUT_NAME],
        output_names=[ONNX_OUTPUT_NAME],
        dynamic_axes={
            ONNX_INPUT_NAME: {0: "batch_size"},
            ONNX_OUTPUT_NAME: {0: "batch_size"},
        },
    )

    onnx_bytes = buf.getvalue()
    # Verifica integridade do grafo ONNX em memória antes de gravar no servidor
    onnx_model = onnx.load_from_string(onnx_bytes)
    onnx.checker.check_model(onnx_model)

    # Grava em blocos de 256 KB para máxima estabilidade no Windows
    with open(onnx_path, "wb") as f:
        mv = memoryview(onnx_bytes)
        chunk_sz = 256 * 1024
        for offset in range(0, len(onnx_bytes), chunk_sz):
            f.write(mv[offset : offset + chunk_sz])

    size_mb = onnx_path.stat().st_size / (1024.0 * 1024.0)
    print(f"[train_and_export_onnx] Modelo ONNX exportado com sucesso: {onnx_path} ({size_mb:.2f} MB)")

    # Benchmark rápido no ONNX Runtime CPU (simulando o loop de 16Hz do C#)
    sess_opts = ort.SessionOptions()
    sess_opts.intra_op_num_threads = 4
    sess_opts.inter_op_num_threads = 1
    sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(str(onnx_path), sess_options=sess_opts, providers=["CPUExecutionProvider"])

    test_in = np.zeros((2, MAX_PLAYERS, FEATURE_DIM), dtype=np.float32)
    # Warmup L3 Cache
    for _ in range(25):
        sess.run([ONNX_OUTPUT_NAME], {ONNX_INPUT_NAME: test_in})

    latencies = []
    for _ in range(200):
        t0 = time.perf_counter()
        out = sess.run([ONNX_OUTPUT_NAME], {ONNX_INPUT_NAME: test_in})[0]
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = float(np.mean(latencies))
    p50_ms = float(np.median(latencies))
    print(
        f"[train_and_export_onnx] Validação ONNX Runtime CPU -> Output shape: {out.shape} | Latência mediana: {p50_ms:.3f} ms (média: {avg_ms:.3f} ms)"
    )
    return onnx_path


def save_state_dict_safe(state_dict: dict, path: Path) -> None:
    import io

    buf = io.BytesIO()
    torch.save(state_dict, buf)
    raw = buf.getvalue()
    with open(path, "wb") as f:
        mv = memoryview(raw)
        chunk = 256 * 1024
        for off in range(0, len(raw), chunk):
            f.write(mv[off : off + chunk])


def load_state_dict_safe(path: Path) -> dict:
    import io

    raw = path.read_bytes()
    return torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Treinador Transformer MLMove + Exportador ONNX")
    parser.add_argument("--map", type=str, default="de_mirage")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=6e-4)
    parser.add_argument("--cpu-only", action="store_true", help="Força treinamento em CPU")
    args = parser.parse_args()

    ckpt_dir = Path(CHECKPOINTS_DIR_D)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_path = ckpt_dir / f"mlmove_{args.map}_best.pt"

    device, dev_label = select_training_device(prefer_dml=not args.cpu_only)
    print(f"[train_and_export_onnx] Dispositivo selecionado: {dev_label}")

    X, Y = load_dataset_for_map(args.map)
    dataset = TensorDataset(X, Y)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=False)

    model = MLMoveTransformer()
    params = count_parameters(model)
    print(f"[train_and_export_onnx] MLMoveTransformer inicializado: {params:,} parâmetros (~{(params * 4) / (1024**2):.2f} MB)")

    if best_ckpt_path.exists():
        try:
            state = load_state_dict_safe(best_ckpt_path)
            model.load_state_dict(state)
            print(f"[train_and_export_onnx] Checkpoint anterior carregado para fine-tuning: {best_ckpt_path}")
        except Exception as exc:
            print(f"[train_and_export_onnx] Aviso ao ler checkpoint anterior (iniciando do zero): {exc}")

    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = DirectMLAdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, args.epochs), eta_min=1e-5)

    best_loss = float("inf")
    best_cpu_state = None
    start_train = time.perf_counter()

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        correct_h0 = 0
        total_tokens = 0
        t_ep = time.perf_counter()

        for bx, by in loader:
            bx = bx.to(device)
            by = by.to(device)

            optimizer.zero_grad()
            logits = model(bx)  # [B, 10, 3, 97]

            loss_0ms = criterion(logits[:, :, 0, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 0].reshape(-1))
            loss_125ms = criterion(logits[:, :, 1, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 1].reshape(-1))
            loss_250ms = criterion(logits[:, :, 2, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 2].reshape(-1))
            loss = loss_0ms + loss_125ms + loss_250ms

            loss.backward()
            for p in model.parameters():
                if p.grad is not None:
                    p.grad.clamp_(-1.0, 1.0)
            optimizer.step()

            bsz = bx.size(0)
            running_loss += float(loss.item()) * bsz
            preds_h0 = logits[:, :, 0, :].argmax(dim=-1)
            correct_h0 += int((preds_h0 == by[:, :, 0]).sum().item())
            total_tokens += bsz * MAX_PLAYERS

        scheduler.step()
        epoch_loss = running_loss / len(dataset)
        acc_h0 = (correct_h0 / max(1, total_tokens)) * 100.0
        dt = time.perf_counter() - t_ep
        print(
            f"  [Época {epoch:02d}/{args.epochs:02d}] Loss Multi-Horizonte: {epoch_loss:.4f} | Acc(t=0ms): {acc_h0:.2f}% | Tempo: {dt:.2f}s"
        )

        if epoch_loss < best_loss:
            best_loss = epoch_loss
            best_cpu_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    total_time = time.perf_counter() - start_train
    print(f"[train_and_export_onnx] Treinamento concluído em {total_time:.2f}s (Melhor Loss: {best_loss:.4f}).")

    if best_cpu_state is not None:
        save_state_dict_safe(best_cpu_state, best_ckpt_path)
        print(f"[train_and_export_onnx] Checkpoint salvo em: {best_ckpt_path}")
        model.to("cpu")
        model.load_state_dict(best_cpu_state)

    export_to_server_onnx(model, args.map)


if __name__ == "__main__":
    main()
