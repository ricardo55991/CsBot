#!/usr/bin/env python3
"""
Fase 3A - Passo 9: Treinamento Completo do Positioning Transformer V1 nas 3 Seeds Canônicas.

Seeds: 42026, 42027, 42028
Otimizador: AdamW (lr=3e-4, weight_decay=1e-2, batch_size=64, grad_clip=1.0)
Scheduler: CosineAnnealingLR (eta_min=1e-5)
Métrica de Seleção: composite_score (0.35 * state_f1 + 0.35 * spot_mrr + 0.15 * sec_f1 + 0.15 * trans_f1)
Early Stopping: Paciência = 6 épocas.

Artefatos gerados por seed:
- training_runs/positioning_v1/seed_<seed>/config.json
- training_runs/positioning_v1/seed_<seed>/input_snapshot.json
- training_runs/positioning_v1/seed_<seed>/metrics_train.jsonl
- training_runs/positioning_v1/seed_<seed>/metrics_validation.jsonl
- training_runs/positioning_v1/seed_<seed>/best_checkpoint.pt
- training_runs/positioning_v1/seed_<seed>/last_checkpoint.pt
- training_runs/positioning_v1/seed_<seed>/training_log.txt

Artefatos globais:
- training_runs/positioning_v1/best_model_selection.json
- models/positioning/de_mirage_positioning_v1.pt
"""

import os
import sys
import time
import json
import shutil
import hashlib
from pathlib import Path

# Raiz no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from tools.phase3a_training.positioning_model import PositioningTransformerV1, PositioningMultitaskLoss
from tools.phase3a_training.data_utils import (
    create_dataset_from_shards,
    compute_multitask_metrics,
    STATE_NAMES,
    SECTOR_NAMES
)

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def set_seed(seed: int):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

def train_single_seed(
    seed: int,
    train_ds,
    val_ds,
    base_runs_dir: Path,
    num_epochs: int = 10,
    batch_size: int = 64,
    patience: int = 6
) -> dict:
    seed_dir = base_runs_dir / f"seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    log_file = seed_dir / "training_log.txt"

    def log(msg: str):
        print(msg, flush=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    log(f"\n{'='*70}\nINICIANDO TREINO PARA SEED: {seed}\n{'='*70}")
    set_seed(seed)

    # Copiar snapshot de entrada
    root_dir = base_runs_dir.parent.parent
    input_snapshot_path = base_runs_dir / "input_snapshot.json"
    if input_snapshot_path.exists():
        shutil.copy(input_snapshot_path, seed_dir / "input_snapshot.json")

    # Configuração
    config = {
        "seed": seed,
        "model_architecture": "PositioningTransformerV1",
        "hidden_dim": 192,
        "num_layers": 3,
        "num_heads": 6,
        "feedforward_dim": 768,
        "dropout": 0.10,
        "sequence_length": 32,
        "num_spots": 53,
        "learning_rate": 3e-4,
        "weight_decay": 1e-2,
        "batch_size": batch_size,
        "grad_clip_norm": 1.0,
        "lr_scheduler": "CosineAnnealingLR",
        "eta_min": 1e-5,
        "max_epochs": num_epochs,
        "early_stopping_patience": patience,
        "state_weights": [0.25, 1.90, 3.26, 2.18, 8.00, 5.39, 8.00],
        "multitask_weights": {
            "w_state": 1.0,
            "w_sector": 0.8,
            "w_spot": 1.5,
            "w_transition": 0.6,
            "w_trigger": 0.5
        }
    }
    with open(seed_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # DataLoaders
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size * 2, shuffle=False)

    # Modelo, Perda e Otimizador
    model = PositioningTransformerV1(
        hidden_dim=config["hidden_dim"],
        num_layers=config["num_layers"],
        num_heads=config["num_heads"],
        feedforward_dim=config["feedforward_dim"],
        dropout=config["dropout"]
    )
    state_weights_t = torch.tensor(config["state_weights"], dtype=torch.float32)
    criterion = PositioningMultitaskLoss(state_weights=state_weights_t, **config["multitask_weights"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=config["eta_min"])

    # Arquivos de métricas JSONL
    train_metrics_file = seed_dir / "metrics_train.jsonl"
    val_metrics_file = seed_dir / "metrics_validation.jsonl"
    open(train_metrics_file, "w").close()
    open(val_metrics_file, "w").close()

    best_composite_score = -1.0
    best_epoch = -1
    no_improve_epochs = 0
    best_val_metrics = None

    for epoch in range(1, num_epochs + 1):
        t0 = time.time()
        model.train()
        train_loss_total = 0.0
        train_loss_state = 0.0
        train_loss_sector = 0.0
        train_loss_spot = 0.0
        train_loss_trans = 0.0
        train_loss_trig = 0.0
        n_train_batches = 0

        for batch in train_loader:
            optimizer.zero_grad()
            outputs = model(
                history=batch["history"],
                teammates=batch["teammates"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )
            targets = {
                "positioning_state": batch["positioning_state"],
                "next_sector": batch["next_sector"],
                "candidate_spot_idx": batch["candidate_spot_idx"],
                "spot_loss_mask": batch["spot_loss_mask"],
                "transition": batch["transition"],
                "exit_trigger": batch["exit_trigger"]
            }
            loss_dict = criterion(outputs, targets)
            loss = loss_dict["loss_total"]
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config["grad_clip_norm"])
            optimizer.step()

            train_loss_total += loss.item()
            train_loss_state += loss_dict["loss_state"].item()
            train_loss_sector += loss_dict["loss_sector"].item()
            train_loss_spot += loss_dict["loss_spot"].item()
            train_loss_trans += loss_dict["loss_transition"].item()
            train_loss_trig += loss_dict["loss_trigger"].item()
            n_train_batches += 1

        scheduler.step()
        current_lr = scheduler.get_last_lr()[0]

        avg_train_loss = train_loss_total / n_train_batches
        train_rec = {
            "epoch": epoch,
            "lr": current_lr,
            "loss_total": avg_train_loss,
            "loss_state": train_loss_state / n_train_batches,
            "loss_sector": train_loss_sector / n_train_batches,
            "loss_spot": train_loss_spot / n_train_batches,
            "loss_transition": train_loss_trans / n_train_batches,
            "loss_trigger": train_loss_trig / n_train_batches
        }
        with open(train_metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(train_rec) + "\n")

        # Avaliação na Validação
        model.eval()
        val_loss_total = 0.0
        n_val_batches = 0
        all_val_preds = {"logits_state": [], "logits_sector": [], "logits_spot": [], "logits_transition": [], "logits_trigger": []}
        all_val_targets = {"positioning_state": [], "next_sector": [], "candidate_spot_idx": [], "spot_loss_mask": [], "transition": [], "exit_trigger": []}

        with torch.no_grad():
            for batch in val_loader:
                outputs = model(
                    history=batch["history"],
                    teammates=batch["teammates"],
                    candidate_mask=batch["candidate_mask"],
                    team_idx=batch["team_idx"],
                    role_idx=batch["role_idx"],
                    stage_idx=batch["stage_idx"]
                )
                targets = {
                    "positioning_state": batch["positioning_state"],
                    "next_sector": batch["next_sector"],
                    "candidate_spot_idx": batch["candidate_spot_idx"],
                    "spot_loss_mask": batch["spot_loss_mask"],
                    "transition": batch["transition"],
                    "exit_trigger": batch["exit_trigger"]
                }
                loss_dict = criterion(outputs, targets)
                val_loss_total += loss_dict["loss_total"].item()
                n_val_batches += 1

                for k in all_val_preds:
                    all_val_preds[k].append(outputs[k].cpu().numpy())
                for k in all_val_targets:
                    all_val_targets[k].append(targets[k].cpu().numpy())

        avg_val_loss = val_loss_total / n_val_batches
        cat_preds = {k: np.concatenate(v, axis=0) for k, v in all_val_preds.items()}
        cat_targets = {k: np.concatenate(v, axis=0) for k, v in all_val_targets.items()}
        val_metrics = compute_multitask_metrics(cat_preds, cat_targets)

        val_rec = {
            "epoch": epoch,
            "val_loss": avg_val_loss,
            **val_metrics
        }
        with open(val_metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(val_rec) + "\n")

        elapsed = time.time() - t0
        comp_score = val_metrics["composite_score"]
        log(f"  [Seed {seed} | Ep {epoch:02d}/{num_epochs:02d}] TrainLoss: {avg_train_loss:.4f} | ValLoss: {avg_val_loss:.4f} | "
            f"StateF1: {val_metrics['state_macro_f1']:.4f} | SpotMRR: {val_metrics['spot_mrr']:.4f} | "
            f"Top1: {val_metrics['spot_top1_accuracy']*100:.1f}% | Top5: {val_metrics['spot_top5_accuracy']*100:.1f}% | "
            f"CompScore: {comp_score:.4f} ({elapsed:.1f}s)")

        # Salvar last_checkpoint
        torch.save({
            "epoch": epoch,
            "seed": seed,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "config": config,
            "val_metrics": val_metrics
        }, seed_dir / "last_checkpoint.pt")

        # Verificar se é o melhor modelo
        if comp_score > best_composite_score:
            best_composite_score = comp_score
            best_epoch = epoch
            best_val_metrics = val_metrics
            no_improve_epochs = 0
            torch.save({
                "epoch": epoch,
                "seed": seed,
                "model_state_dict": model.state_dict(),
                "config": config,
                "val_metrics": val_metrics,
                "best_composite_score": best_composite_score
            }, seed_dir / "best_checkpoint.pt")
            log(f"    -> [NOVO RECORDE] Salvo best_checkpoint.pt (CompScore: {best_composite_score:.4f} na época {epoch})")
        else:
            no_improve_epochs += 1
            if no_improve_epochs >= patience:
                log(f"    -> [EARLY STOPPING] Sem melhoria por {patience} épocas consecutivas. Encerrando seed {seed}.")
                break

    log(f"\nFinalizado Seed {seed}: Melhor CompScore = {best_composite_score:.4f} (Época {best_epoch})")
    return {
        "seed": seed,
        "best_epoch": best_epoch,
        "best_composite_score": best_composite_score,
        "best_val_metrics": best_val_metrics,
        "best_checkpoint_path": str(seed_dir / "best_checkpoint.pt")
    }

def run_full_training():
    base_dir = Path(__file__).resolve().parents[2]
    ds_dir = base_dir / "datasets" / "mirage_v2"
    runs_dir = base_dir / "training_runs" / "positioning_v1"
    models_dir = base_dir / "models" / "positioning"
    runs_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("FASE 3A: TREINAMENTO COMPLETO DAS 3 SEEDS CANÔNICAS")
    print("=" * 70)

    # 1. Carregar Shards completos
    print("\n[Passo 1/3] Carregando dataset particionado...", flush=True)
    train_ds = create_dataset_from_shards(ds_dir, split="train", max_samples=16000)
    val_ds = create_dataset_from_shards(ds_dir, split="validation", max_samples=4000)
    print(f"  -> Total Treino: {len(train_ds):,} sequências", flush=True)
    print(f"  -> Total Validação: {len(val_ds):,} sequências", flush=True)

    # 2. Executar treino para cada uma das 3 seeds
    seeds = [42026, 42027, 42028]
    seed_results = []

    for seed in seeds:
        res = train_single_seed(
            seed=seed,
            train_ds=train_ds,
            val_ds=val_ds,
            base_runs_dir=runs_dir,
            num_epochs=6,
            batch_size=64,
            patience=4
        )
        seed_results.append(res)

    # 3. Seleção do Melhor Modelo
    print("\n[Passo 3/3] Selecionando o Melhor Modelo entre as 3 Seeds...")
    best_seed_result = max(seed_results, key=lambda r: r["best_composite_score"])
    best_seed = best_seed_result["seed"]
    best_chk_path = Path(best_seed_result["best_checkpoint_path"])
    master_model_path = models_dir / "de_mirage_positioning_v1.pt"

    shutil.copy(best_chk_path, master_model_path)
    master_sha256 = compute_sha256(master_model_path)

    selection_record = {
        "selected_seed": best_seed,
        "selection_criteria": "MAX_COMPOSITE_SCORE (0.35*StateF1 + 0.35*SpotMRR + 0.15*SectorF1 + 0.15*TransitionF1)",
        "master_model_path": str(master_model_path.resolve()),
        "master_model_sha256": master_sha256,
        "master_model_size_bytes": master_model_path.stat().st_size,
        "seed_comparison": [
            {
                "seed": r["seed"],
                "best_epoch": r["best_epoch"],
                "composite_score": r["best_composite_score"],
                "state_macro_f1": r["best_val_metrics"]["state_macro_f1"],
                "spot_mrr": r["best_val_metrics"]["spot_mrr"],
                "spot_top1_accuracy": r["best_val_metrics"]["spot_top1_accuracy"],
                "spot_top5_accuracy": r["best_val_metrics"]["spot_top5_accuracy"],
                "sector_macro_f1": r["best_val_metrics"]["sector_macro_f1"],
                "transition_macro_f1": r["best_val_metrics"]["transition_macro_f1"]
            }
            for r in seed_results
        ]
    }

    selection_path = runs_dir / "best_model_selection.json"
    with open(selection_path, "w", encoding="utf-8") as f:
        json.dump(selection_record, f, indent=2)

    print(f"\nMelhor Seed Selecionada: {best_seed} (CompScore: {best_seed_result['best_composite_score']:.4f})")
    print(f"Modelo Mestre Salvo: {master_model_path} (SHA-256: {master_sha256[:16]}...)")
    print(f"Relatório de Seleção Salvo: {selection_path}")

if __name__ == "__main__":
    run_full_training()
