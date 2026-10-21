"""
Fase 6B / 6C: Pipeline em Lotes de Mineração, Extração e Treinamento Incremental MLMove 16Hz.
Orquestra o ciclo contínuo em lotes:
1. Minera demos reais da Web (HuggingFace, HLTV, URLs) ou ingere demos locais/CSTV.
2. Filtra cabeçalho Source 2 (PBDEMS2).
3. Extrai tensores 16Hz com demoparser2, salvando .npz em D:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\.
4. Limpeza de Disco: se --keep-raw-demos for False, apaga o arquivo .dem bruto de 200MB logo após extrair o .npz!
5. Executa fine-tuning incremental do transformer na GPU AMD RX 6600M (DirectML) ou CPU multi-thread.
6. Exporta o novo modelo ONNX para H:\CS2_AI_Server\models\mlmove_de_mirage.onnx (acionando hot-swap no CS2).
7. Gera relatório completo de precisão Top-1 e Top-3 nos 3 horizontes (0ms, 125ms, 250ms).
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
import site
import sys
import time
from typing import Dict, List, Optional, Tuple

# Inclusão de caminhos de site-packages para compatibilidade com o venv
for extra_path in [
    site.getusersitepackages(),
    r"C:\Users\ricar\AppData\Local\Programs\Python\Python311\Lib\site-packages",
    r"C:\Users\ricar\AppData\Roaming\Python\Python311\site-packages",
]:
    if os.path.exists(extra_path) and extra_path not in sys.path:
        sys.path.append(extra_path)

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from contract_spec import (
    ACTION_SPACE_SIZE,
    CHECKPOINTS_DIR_D,
    EXTRACTED_TENSORS_DIR_D,
    FEATURE_DIM,
    HORIZONS_COUNT,
    MAX_PLAYERS,
    ONNX_INPUT_NAME,
    ONNX_OUTPUT_NAME,
    RAW_DEMOS_DIR_D,
    SERVER_MODELS_DIR_H,
)
from extract_16hz_tensors import extract_single_demo
from model_mlmove import MLMoveTransformer, count_parameters
from real_demo_miner import (
    MinerState,
    compute_file_sha256,
    run_miner,
    validate_cs2_demo_header,
)
from train_and_export_onnx import (
    DirectMLAdamW,
    export_to_server_onnx,
    load_dataset_for_map,
    load_state_dict_safe,
    save_state_dict_safe,
    select_training_device,
)


def evaluate_top1_top3_metrics(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> Dict[str, float]:
    """Calcula Top-1 e Top-3 Accuracy nos 3 horizontes (0ms, 125ms, 250ms)."""
    model.eval()
    correct_top1 = [0, 0, 0]
    correct_top3 = [0, 0, 0]
    total_tokens = 0

    with torch.no_grad():
        for bx, by in loader:
            bx = bx.to(device)
            by = by.to(device)
            bsz = bx.size(0)
            total_tokens += bsz * MAX_PLAYERS

            logits = model(bx)  # [B, 10, 3, 97]
            for h in range(HORIZONS_COUNT):
                h_logits = logits[:, :, h, :].reshape(-1, ACTION_SPACE_SIZE)
                h_targets = by[:, :, h].reshape(-1).long()

                # Top-1
                preds = h_logits.argmax(dim=-1)
                correct_top1[h] += int((preds == h_targets).sum().item())

                # Top-3
                _, top3_preds = h_logits.topk(3, dim=-1)
                in_top3 = top3_preds.eq(h_targets.unsqueeze(-1)).any(dim=-1)
                correct_top3[h] += int(in_top3.sum().item())

    denom = max(1, total_tokens)
    return {
        "h0_top1": (correct_top1[0] / denom) * 100.0,
        "h0_top3": (correct_top3[0] / denom) * 100.0,
        "h1_top1": (correct_top1[1] / denom) * 100.0,
        "h1_top3": (correct_top3[1] / denom) * 100.0,
        "h2_top1": (correct_top2[2] if False else correct_top1[2] / denom) * 100.0,
        "h2_top1": (correct_top1[2] / denom) * 100.0,
        "h2_top3": (correct_top3[2] / denom) * 100.0,
    }


def process_single_batch_extraction(
    raw_dir: Path,
    out_dir: Path,
    state: MinerState,
    batch_size: int = 25,
    keep_raw_demos: bool = False,
) -> Tuple[int, int]:
    """
    Processa um lote de arquivos .dem em raw_dir:
    1. Filtra cabeçalho Source 2 PBDEMS2
    2. Extrai tensores com demoparser2
    3. Registra hash no miner_state.json
    4. Se keep_raw_demos for False, remove o .dem para economizar ~200MB de disco NVMe
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    dem_files = sorted(list(raw_dir.glob("*.dem")))
    if not dem_files:
        return 0, 0

    batch = dem_files[:batch_size]
    extracted_demos = 0
    total_steps = 0

    print(f"\n[Pipeline Lote] Iniciando extração de lote ({len(batch)} demos)...")

    for dem_path in tqdm(batch, desc="Extraindo tensores 16Hz"):
        # 1. Validação Source 2 PBDEMS2
        is_valid, reason = validate_cs2_demo_header(dem_path)
        if not is_valid:
            print(f"[Header Check] Descartando {dem_path.name}: {reason}")
            try:
                dem_path.unlink(missing_ok=True)
            except Exception:
                pass
            continue

        # 2. Amostragem de hash anti-duplicação
        demo_hash = compute_file_sha256(dem_path, sample_fast=True)
        if state.is_hash_processed(demo_hash):
            print(f"[Anti-Duplicação] Demo {dem_path.name} já processada anteriormente. Ignorando.")
            if not keep_raw_demos:
                dem_path.unlink(missing_ok=True)
            continue

        out_npz = out_dir / f"{dem_path.stem}_16hz.npz"
        try:
            X, Y = extract_single_demo(dem_path)
            if len(X) > 0:
                np.savez_compressed(out_npz, X=X, Y=Y)
                steps_count = len(X)
                total_steps += steps_count
                extracted_demos += 1
                size_mb = dem_path.stat().st_size / (1024 * 1024)
                state.record_processed_demo(demo_hash, dem_path.name, "pipeline_batch", size_mb)
                print(f"  -> {dem_path.name}: {steps_count} steps 16Hz extraídos ({out_npz.stat().st_size // 1024} KB)")

            # 3. Limpeza de Disco NVMe
            if not keep_raw_demos:
                dem_path.unlink(missing_ok=True)
                print(f"  [Limpeza] Demo bruta removida para economia de disco: {dem_path.name}")

        except Exception as exc:
            print(f"[Pipeline Lote] Erro ao extrair {dem_path.name}: {exc}")

    return extracted_demos, total_steps


def train_incremental_batch(
    map_name: str = "de_mirage",
    epochs: int = 15,
    batch_size: int = 256,
    lr: float = 6e-4,
    cpu_only: bool = False,
    base_dir: str = DEFAULT_BASE_DIR,
) -> Dict[str, float]:
    """Treina ou refina incrementalmente o transformer PyTorch nos tensores disponíveis e exporta ONNX."""
    base_path = Path(base_dir)
    ckpt_dir = base_path / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_path = ckpt_dir / f"mlmove_{map_name}_best.pt"

    device, dev_label = select_training_device(prefer_dml=not cpu_only)
    print(f"\n[Treinador Incremental] Dispositivo de Treinamento: {dev_label}")

    X, Y = load_dataset_for_map(map_name)
    if len(X) == 0:
        print("[Treinador Incremental] Nenhum tensor disponível para treinamento.")
        return {}

    dataset = TensorDataset(X, Y)
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, drop_last=False)

    model = MLMoveTransformer()
    params = count_parameters(model)
    print(f"[Treinador Incremental] MLMoveTransformer: {params:,} parâmetros (~{(params * 4) / (1024**2):.2f} MB)")

    # Carrega melhor checkpoint anterior se existir (Fine-tuning contínuo)
    best_loss = float("inf")
    if best_ckpt_path.exists():
        try:
            state = load_state_dict_safe(best_ckpt_path)
            model.load_state_dict(state)
            print(f"[Treinador Incremental] Checkpoint anterior carregado para fine-tuning: {best_ckpt_path}")
        except Exception as exc:
            print(f"[Treinador Incremental] Aviso ao carregar checkpoint: {exc}")

    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = DirectMLAdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    print(f"[Treinador Incremental] Iniciando {epochs} épocas de ajuste fino...")
    best_cpu_state = None

    for epoch in range(1, epochs + 1):
        t0 = time.perf_counter()
        model.train()
        running_loss = 0.0

        for bx, by in train_loader:
            bx = bx.to(device)
            by = by.to(device).long()
            optimizer.zero_grad()

            logits = model(bx)
            l0 = criterion(logits[:, :, 0, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 0].reshape(-1))
            l1 = criterion(logits[:, :, 1, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 1].reshape(-1))
            l2 = criterion(logits[:, :, 2, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 2].reshape(-1))
            loss = l0 + l1 + l2

            loss.backward()
            for p in model.parameters():
                if p.grad is not None:
                    p.grad.clamp_(-1.0, 1.0)
            optimizer.step()
            running_loss += float(loss.item()) * bx.size(0)

        scheduler.step()
        ep_loss = running_loss / max(1, len(train_ds))
        dt = time.perf_counter() - t0

        if ep_loss < best_loss:
            best_loss = ep_loss
            best_cpu_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

        print(f"  [Época {epoch:02d}/{epochs:02d}] Loss: {ep_loss:.4f} | Tempo: {dt:.2f}s")

    if best_cpu_state is not None:
        save_state_dict_safe(best_cpu_state, best_ckpt_path)
        print(f"[Treinador Incremental] Novo melhor checkpoint salvo: {best_ckpt_path} (Loss: {best_loss:.4f})")
        model.to("cpu")
        model.load_state_dict(best_cpu_state)
    else:
        model.to("cpu")

    # Exporta para o servidor CS2 (Hot-swap ativo)
    export_to_server_onnx(model, map_name)

    # Avaliação final de Top-1 e Top-3 Accuracy nos 3 horizontes temporais
    eval_device = torch.device("cpu")
    model.to(eval_device)
    metrics = evaluate_top1_top3_metrics(model, val_loader, eval_device)

    print("\n" + "=" * 65)
    print("      📊 RELATÓRIO DE PRECISÃO MULTI-HORIZONTE (MLMove 16Hz)")
    print("=" * 65)
    print(f"  * Horizonte 0ms   (Imediato) : Top-1: {metrics['h0_top1']:5.2f}% | Top-3: {metrics['h0_top3']:5.2f}%")
    print(f"  * Horizonte +125ms (Curto)    : Top-1: {metrics['h1_top1']:5.2f}% | Top-3: {metrics['h1_top3']:5.2f}%")
    print(f"  * Horizonte +250ms (Médio)    : Top-1: {metrics['h2_top1']:5.2f}% | Top-3: {metrics['h2_top3']:5.2f}%")
    print("=" * 65 + "\n")

    return metrics


def run_mining_and_training_loop(
    source: str = "all",
    batch_size: int = 25,
    epochs: int = 15,
    keep_raw_demos: bool = False,
    max_batches: int = 10,
    base_dir: str = DEFAULT_BASE_DIR,
    map_name: str = "de_mirage",
    cpu_only: bool = False,
) -> None:
    """Orquestrador do ciclo completo de mineração, extração em lotes e fine-tuning."""
    base_path = Path(base_dir)
    raw_dir = base_path / "raw_demos" / map_name
    out_dir = base_path / "extracted_tensors" / map_name
    state_path = base_path / "miner_state.json"

    # Fallback seguro caso D:\ esteja temporariamente indisponível
    try:
        raw_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        fallback_base = Path("D:/CS2_MLMove_Pipeline") if os.path.exists("D:/") else Path("tools/mlmove_pipeline/storage")
        print(f"[Loop] Aviso: {base_path} indisponível ({exc}). Usando fallback: {fallback_base}")
        base_path = fallback_base
        raw_dir = base_path / "raw_demos" / map_name
        out_dir = base_path / "extracted_tensors" / map_name
        state_path = base_path / "miner_state.json"
        raw_dir.mkdir(parents=True, exist_ok=True)

    state = MinerState(state_path)

    print("=" * 70)
    print("   CsBot - Pipeline em Lotes de Mineração e Treinamento MLMove")
    print("=" * 70)
    print(f"Pasta Base: {base_path}")
    print(f"Lote por Rodada: {batch_size} demos | Épocas por Lote: {epochs}")
    print(f"Manter Demos Brutas (.dem): {'SIM' if keep_raw_demos else 'NÃO (Limpeza Automática de Disco)'}")
    print("=" * 70)

    for batch_num in range(1, max_batches + 1):
        print(f"\n>>> [LOTE {batch_num}/{max_batches}] Iniciando ciclo de mineração...")

        # 1. Minera novas demos
        run_miner(
            source=source,
            base_dir=str(base_path),
            max_demos=batch_size,
            map_name=map_name,
        )

        # 2. Extrai tensores com demoparser2 e limpa .dem brutos
        demos_extracted, steps_extracted = process_single_batch_extraction(
            raw_dir=raw_dir,
            out_dir=out_dir,
            state=state,
            batch_size=batch_size,
            keep_raw_demos=keep_raw_demos,
        )

        # 3. Treinamento e Exportação ONNX
        npz_files = list(out_dir.glob("*.npz"))
        if len(npz_files) > 0:
            print(f"[Loop] Encontrados {len(npz_files)} arquivos .npz para treinamento. Disparando GPU...")
            train_incremental_batch(
                map_name=map_name,
                epochs=epochs,
                batch_size=256,
                lr=6e-4,
                cpu_only=cpu_only,
                base_dir=str(base_path),
            )
        else:
            print("[Loop] Nenhum tensor disponível ainda. Adicione demos ou URLs para iniciar.")

        # Se não houve novas demos neste lote e já processamos todas as pendentes
        remaining_raw = list(raw_dir.glob("*.dem"))
        if demos_extracted == 0 and len(remaining_raw) == 0:
            print("[Loop] Nenhuma nova demo pendente. Lote concluído.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Orquestrador em Lotes de Mineração e Treinamento MLMove")
    parser.add_argument("--source", type=str, default="all", choices=["all", "hf", "huggingface", "urls", "hltv", "local"])
    parser.add_argument("--batch-size", type=int, default=25, help="Quantidade de demos por lote (default: 25)")
    parser.add_argument("--epochs", type=int, default=15, help="Épocas de fine-tuning por lote (default: 15)")
    parser.add_argument("--keep-raw-demos", action="store_true", help="Mantém arquivos .dem brutos após extrair (default: False)")
    parser.add_argument("--max-batches", type=int, default=10, help="Quantidade máxima de lotes a executar (default: 10)")
    parser.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR, help="Diretório raiz no NVMe")
    parser.add_argument("--map", type=str, default="de_mirage", help="Mapa competitivo alvo")
    parser.add_argument("--cpu-only", action="store_true", help="Força treino em CPU em vez de AMD DirectML")
    args = parser.parse_args()

    run_mining_and_training_loop(
        source=args.source,
        batch_size=args.batch_size,
        epochs=args.epochs,
        keep_raw_demos=args.keep_raw_demos,
        max_batches=args.max_batches,
        base_dir=args.base_dir,
        map_name=args.map,
        cpu_only=args.cpu_only,
    )


if __name__ == "__main__":
    main()
