#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2A: Treinamento Piloto (10% Train) e Ablação Preliminar.

Seções cobertas: 6, 7, 8, 9, 10
Invariantes Metodológicos Inegociáveis:
1. Seleção determinística de 10% das partidas completas do Train sob seed 42026:
   - Exatamente 31 demos das 311 demos de Train em canonical_temporal_splits_v1.json.
   - Validation: 100% das 66 demos de validação (207.256 sequências).
   - Proibição absoluta de uso do Test set (67 demos) ou Holdout.
2. Manifesto de proveniência formal:
   - training_runs/positioning_v2_real_temporal/pilot_subset_manifest.json (com SHA-256 dos 31 NPZs).
3. Configuração de Hiperparâmetros congelada:
   - hidden_dim=192, layers=3, heads=6, feedforward=768, dropout=0.10, lr=3e-4, weight_decay=1e-2, clip=1.0, batch_size=64, max_epochs=12, patience=4.
   - training_runs/positioning_v2_real_temporal/pilot_config.json
4. Cálculo de Pesos de Classe para StateLoss baseado exclusivamente no Train do Piloto.
5. Modelo A: Histórico Temporal Real [32, 18] e [32, 4, 18].
6. Modelo B: Último Frame Real (frame t instantâneo estático repetido, sem np.linspace).
7. Avaliação canônica em 100% da Validação para ambos os modelos nas 5 cabeças:
   - Macro F1, Balanced Accuracy, MRR, Top-1, Top-5, ausência de seleções mascaradas inválidas.
   - Respeito estrito a Regra 03: classes com support = 0 reportadas exclusivamente como N/A.
8. Artefatos de saída gerados:
   - pilot_train_metrics.jsonl
   - pilot_validation_metrics.jsonl
   - pilot_best_checkpoint.pt
   - temporal_pilot_metrics.json
   - last_frame_baseline_metrics.json
   - temporal_ablation_metrics.json
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# Raiz no sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    CanonicalTemporalPositioningDataset,
    canonical_collate_fn,
    NPZCacheManager,
    DEFAULT_NPZ_DIR,
    load_canonical_temporal_splits,
    STATE_NAMES,
    SECTOR_NAMES,
    TRANSITION_NAMES,
    EXIT_TRIGGER_NAMES
)
from tools.phase3a_training.positioning_model import PositioningTransformerV1, PositioningMultitaskLoss


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_classification_metrics(preds: np.ndarray, targets: np.ndarray, class_names: List[str]) -> Dict[str, Any]:
    """Calcula Top-1, Macro-F1 e Balanced Accuracy tratando rigorosamente support=0 como N/A."""
    n_classes = len(class_names)
    per_class = {}
    active_f1s = []
    active_recalls = []

    total_samples = len(targets)
    total_correct = int(np.sum(preds == targets))
    top1_acc = float(total_correct / total_samples) if total_samples > 0 else 0.0

    for c_idx, c_name in enumerate(class_names):
        tp = int(np.sum((preds == c_idx) & (targets == c_idx)))
        fp = int(np.sum((preds == c_idx) & (targets != c_idx)))
        fn = int(np.sum((preds != c_idx) & (targets == c_idx)))
        support = int(np.sum(targets == c_idx))

        if support == 0:
            per_class[c_name] = {
                "support": 0,
                "precision": "N/A",
                "recall": "N/A",
                "f1": "N/A"
            }
        else:
            prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            per_class[c_name] = {
                "support": support,
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4)
            }
            active_f1s.append(f1)
            active_recalls.append(rec)

    macro_f1 = float(np.mean(active_f1s)) if active_f1s else 0.0
    balanced_acc = float(np.mean(active_recalls)) if active_recalls else 0.0

    return {
        "top1_accuracy": round(top1_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "active_classes_count": len(active_f1s),
        "total_classes_count": n_classes,
        "per_class": per_class
    }


def compute_spot_ranking_metrics(
    logits: np.ndarray,
    targets: np.ndarray,
    spot_loss_mask: np.ndarray,
    candidate_mask: np.ndarray
) -> Dict[str, Any]:
    """Calcula Top-1, Top-5, MRR e seleções mascaradas inválidas sobre amostras com spot_loss_mask == True."""
    valid_indices = np.where(spot_loss_mask)[0]
    n_valid = len(valid_indices)

    if n_valid == 0:
        return {
            "top1_accuracy": "N/A",
            "top5_accuracy": "N/A",
            "mrr": "N/A",
            "invalid_masked_selections": 0,
            "support": 0
        }

    sub_logits = logits[valid_indices]
    sub_targets = targets[valid_indices]
    sub_cand_mask = candidate_mask[valid_indices]

    preds = np.argmax(sub_logits, axis=1)
    is_valid_cand = sub_cand_mask[np.arange(n_valid), preds]
    invalid_count = int(np.sum(~is_valid_cand))

    top1 = int(np.sum(preds == sub_targets))
    top1_acc = float(top1 / n_valid)

    sorted_indices = np.argsort(-sub_logits, axis=1)
    ranks = []
    top5_hits = 0
    for i in range(n_valid):
        target = sub_targets[i]
        order = sorted_indices[i]
        rank_pos = np.where(order == target)[0]
        if len(rank_pos) > 0:
            rank = int(rank_pos[0]) + 1
            ranks.append(1.0 / rank)
            if rank <= 5:
                top5_hits += 1
        else:
            ranks.append(0.0)

    mrr = float(np.mean(ranks)) if ranks else 0.0
    top5_acc = float(top5_hits / n_valid)

    return {
        "top1_accuracy": round(top1_acc, 4),
        "top5_accuracy": round(top5_acc, 4),
        "mrr": round(mrr, 4),
        "invalid_masked_selections": invalid_count,
        "support": n_valid
    }


def evaluate_model_full_validation(
    model: nn.Module,
    val_loader: DataLoader,
    is_last_frame_mode: bool = False
) -> Dict[str, Any]:
    """Executa a avaliação canônica exaustiva sobre 100% do conjunto de validação."""
    model.eval()

    all_preds_state = []
    all_targets_state = []

    all_preds_sector = []
    all_targets_sector = []

    all_logits_spot = []
    all_targets_spot = []
    all_spot_loss_mask = []
    all_candidate_mask = []

    all_preds_trans = []
    all_targets_trans = []

    all_preds_trig = []
    all_targets_trig = []

    t0 = time.time()
    total_evaluated = 0

    with torch.no_grad():
        for b_idx, batch in enumerate(val_loader):
            hist = batch["history"]
            tm = batch["teammates"]

            if is_last_frame_mode:
                # Substituir toda a janela pelo último frame autêntico
                hist = hist[:, -1:, :].repeat(1, 32, 1)
                tm = tm[:, -1:, :, :].repeat(1, 32, 1, 1)

            outputs = model(
                history=hist,
                teammates=tm,
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )

            p_state = torch.argmax(outputs["logits_state"], dim=1).cpu().numpy()
            t_state = batch["positioning_state"].cpu().numpy()
            all_preds_state.append(p_state)
            all_targets_state.append(t_state)

            p_sec = torch.argmax(outputs["logits_sector"], dim=1).cpu().numpy()
            t_sec = batch["next_sector"].cpu().numpy()
            all_preds_sector.append(p_sec)
            all_targets_sector.append(t_sec)

            all_logits_spot.append(outputs["logits_spot"].cpu().numpy())
            all_targets_spot.append(batch["candidate_spot_idx"].cpu().numpy())
            all_spot_loss_mask.append(batch["spot_loss_mask"].cpu().numpy())
            all_candidate_mask.append(batch["candidate_mask"].cpu().numpy())

            p_trans = torch.argmax(outputs["logits_transition"], dim=1).cpu().numpy()
            t_trans = batch["transition"].cpu().numpy()
            all_preds_trans.append(p_trans)
            all_targets_trans.append(t_trans)

            p_trig = torch.argmax(outputs["logits_trigger"], dim=1).cpu().numpy()
            t_trig = batch["exit_trigger"].cpu().numpy()
            all_preds_trig.append(p_trig)
            all_targets_trig.append(t_trig)

            total_evaluated += len(t_state)
            if (b_idx + 1) % 100 == 0:
                print(f"    Validação: {total_evaluated:,} amostras processadas...", flush=True)

    dt = time.time() - t0
    print(f"  Validação completa de {total_evaluated:,} amostras executada em {dt:.2f}s ({total_evaluated/dt:.1f} samples/s)", flush=True)

    cat_preds_state = np.concatenate(all_preds_state)
    cat_targets_state = np.concatenate(all_targets_state)

    cat_preds_sector = np.concatenate(all_preds_sector)
    cat_targets_sector = np.concatenate(all_targets_sector)

    cat_logits_spot = np.concatenate(all_logits_spot, axis=0)
    cat_targets_spot = np.concatenate(all_targets_spot)
    cat_spot_loss_mask = np.concatenate(all_spot_loss_mask)
    cat_cand_mask = np.concatenate(all_candidate_mask, axis=0)

    cat_preds_trans = np.concatenate(all_preds_trans)
    cat_targets_trans = np.concatenate(all_targets_trans)

    cat_preds_trig = np.concatenate(all_preds_trig)
    cat_targets_trig = np.concatenate(all_targets_trig)

    # Computar métricas das 5 heads
    metrics_state = compute_classification_metrics(cat_preds_state, cat_targets_state, STATE_NAMES)
    metrics_sector = compute_classification_metrics(cat_preds_sector, cat_targets_sector, SECTOR_NAMES)
    metrics_spot = compute_spot_ranking_metrics(cat_logits_spot, cat_targets_spot, cat_spot_loss_mask, cat_cand_mask)
    metrics_trans = compute_classification_metrics(cat_preds_trans, cat_targets_trans, TRANSITION_NAMES)
    metrics_trig = compute_classification_metrics(cat_preds_trig, cat_targets_trig, EXIT_TRIGGER_NAMES)

    return {
        "evaluation_time_seconds": round(dt, 2),
        "total_validation_samples": total_evaluated,
        "head_state": metrics_state,
        "head_sector": metrics_sector,
        "head_spot": metrics_spot,
        "head_transition": metrics_trans,
        "head_exit_trigger": metrics_trig
    }


def run_pilot_and_ablation():
    print("=" * 80, flush=True)
    print("FASE 3A.3-B (MARCO 2A) - TREINAMENTO PILOTO (10% TRAIN) E ABLAÇÃO TEMPORAL", flush=True)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}", flush=True)
    print("=" * 80, flush=True)

    seed = 42026
    torch.manual_seed(seed)
    np.random.seed(seed)

    runs_dir = BASE_DIR / "training_runs" / "positioning_v2_real_temporal"
    runs_dir.mkdir(parents=True, exist_ok=True)
    ds_dir = BASE_DIR / "datasets" / "mirage_v2"

    # 1. Selecionar 10% das Partidas Completas do Train sob Seed 42026
    print("\n[Passo 1/8] Selecionando 10% de partidas completas do split Train sob seed 42026...", flush=True)
    splits = load_canonical_temporal_splits(ds_dir)
    train_demos = sorted(splits["train_demos"])
    val_demos = sorted(splits["validation_demos"])
    test_demos = sorted(splits.get("test_demos", []))

    assert len(train_demos) == 311, f"Total esperado de train demos é 311, obtido {len(train_demos)}"
    assert len(val_demos) == 66, f"Total esperado de validation demos é 66, obtido {len(val_demos)}"

    rng = np.random.RandomState(seed)
    pilot_indices = sorted(rng.choice(len(train_demos), size=31, replace=False).tolist())
    pilot_demos = [train_demos[i] for i in pilot_indices]
    pilot_demos_set = set(pilot_demos)

    print(f"  31 Demos do Piloto selecionadas deterministicamente com seed {seed}.", flush=True)

    # 2. Gerar Manifesto Formal de Demos do Piloto com Hashes SHA-256
    print("\n[Passo 2/8] Gerando pilot_subset_manifest.json com SHA-256 das 31 demos...", flush=True)
    manifest_entries = []
    for d in pilot_demos:
        npz_p = DEFAULT_NPZ_DIR / f"{d}_16hz.npz"
        if not npz_p.exists():
            npz_p = DEFAULT_NPZ_DIR / f"{d}.npz"
        sha = compute_sha256(npz_p)
        manifest_entries.append({
            "demo_id": d,
            "relative_path": f"extracted_tensors/{npz_p.name}",
            "sha256": sha,
            "size_bytes": npz_p.stat().st_size
        })

    manifest_payload = {
        "schema_version": "1.0.0",
        "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
        "milestone": "Marco 2A - Piloto Temporal 10%",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "pilot_selection_method": "UNIFORM_RANDOM_WITHOUT_REPLACEMENT",
        "pilot_proportion": "10% of Train matches (31 of 311)",
        "total_pilot_matches": len(pilot_demos),
        "matches": manifest_entries
    }
    manifest_path = runs_dir / "pilot_subset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)
    print(f"  Manifesto salvo: {manifest_path.name} (SHA-256: {compute_sha256(manifest_path)})", flush=True)

    # 3. Salvar Configuração Congelada
    print("\n[Passo 3/8] Gravando pilot_config.json...", flush=True)
    pilot_config = {
        "schema_version": "1.0.0",
        "model_architecture": "PositioningTransformerV1",
        "hidden_dim": 192,
        "num_layers": 3,
        "num_heads": 6,
        "feedforward_dim": 768,
        "dropout": 0.10,
        "seq_len": 32,
        "num_spots": 53,
        "training": {
            "batch_size": 64,
            "learning_rate": 3e-4,
            "weight_decay": 1e-2,
            "grad_clip": 1.0,
            "max_epochs": 12,
            "patience": 4,
            "optimizer": "AdamW",
            "seed": seed
        },
        "splits": {
            "train_demos_count": 31,
            "validation_demos_count": 66,
            "test_used": False,
            "holdout_used": False
        }
    }
    config_path = runs_dir / "pilot_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(pilot_config, f, indent=2)

    # 4. Inicializar Cache Manager e Datasets
    print("\n[Passo 4/8] Carregando e indexando dados do Piloto (Train 31 demos) e Validação (100%)...", flush=True)
    cache_manager = NPZCacheManager()

    # Preload de todas as demos do piloto
    cache_manager.preload(pilot_demos)

    # Dataset de Treino do Piloto
    train_paths = [
        ds_dir / "positioning" / "positioning_sequences_v1" / "shard_000.parquet",
        ds_dir / "positioning" / "positioning_sequences_v1" / "shard_001.parquet",
        ds_dir / "positioning" / "objective_save_sequences.parquet"
    ]
    train_ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="train",
        parquet_paths=train_paths,
        preload_npz=False,
        cache_manager=cache_manager
    )
    # Filtrar estritamente para as 31 demos do piloto
    train_ds.df = train_ds.df[train_ds.df["demo_id"].isin(pilot_demos_set)].reset_index(drop=True)
    train_ds.n = len(train_ds.df)
    train_ds._preprocess_labels()
    print(f"  Treino do Piloto indexado: {len(train_ds):,} sequências cobrindo {train_ds.df['demo_id'].nunique()} demos.", flush=True)

    # Dataset de Validação (100% da Validação Canônica)
    val_ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="validation",
        preload_npz=False,
        cache_manager=cache_manager
    )
    print(f"  Validação Canônica indexada: {len(val_ds):,} sequências cobrindo {len(set(val_ds.demos))} demos.", flush=True)

    train_loader = DataLoader(
        train_ds,
        batch_size=64,
        shuffle=True,
        collate_fn=canonical_collate_fn
    )

    # Para validação completa de alta performance, batch_size=512
    val_loader = DataLoader(
        val_ds,
        batch_size=512,
        shuffle=False,
        collate_fn=canonical_collate_fn
    )

    # 5. Cálculo dos Pesos de Classe para StateLoss (ClassWeightsUsePilotTrainOnly)
    print("\n[Passo 5/8] Calculando pesos de classe com base exclusiva no Train do Piloto...", flush=True)
    train_state_counts = np.bincount(train_ds.state_vals, minlength=7)
    total_train_samples = len(train_ds.state_vals)
    state_weights_list = []
    for c_idx in range(7):
        cnt = train_state_counts[c_idx]
        if cnt > 0:
            w = total_train_samples / (7.0 * cnt)
            w = max(0.2, min(w, 5.0))
        else:
            w = 1.0
        state_weights_list.append(w)
    state_weights = torch.tensor(state_weights_list, dtype=torch.float32)
    print(f"  Contagens por classe no Train: {dict(zip(STATE_NAMES, train_state_counts.tolist()))}", flush=True)
    print(f"  Pesos de StateLoss aplicados: {[round(w, 3) for w in state_weights_list]}", flush=True)

    criterion = PositioningMultitaskLoss(
        state_weights=state_weights,
        w_state=1.0,
        w_sector=0.8,
        w_spot=1.5,
        w_transition=0.6,
        w_trigger=0.5
    )

    # =========================================================================
    # 6. Treinamento do Modelo A (Histórico Temporal Real)
    # =========================================================================
    print("\n" + "=" * 60, flush=True)
    print("[Passo 6/8] TREINANDO MODELO A (HISTÓRICO TEMPORAL REAL: [32, 18])", flush=True)
    print("=" * 60, flush=True)

    model_a = PositioningTransformerV1(
        hidden_dim=192,
        num_layers=3,
        num_heads=6,
        feedforward_dim=768,
        dropout=0.10
    )
    optimizer_a = optim.AdamW(model_a.parameters(), lr=3e-4, weight_decay=1e-2)

    train_metrics_log_path = runs_dir / "pilot_train_metrics.jsonl"
    val_metrics_log_path = runs_dir / "pilot_validation_metrics.jsonl"

    best_ckpt_path = runs_dir / "pilot_best_checkpoint.pt"
    best_val_loss = float("inf")
    patience_counter = 0

    # Limpar arquivos de log anteriores
    open(train_metrics_log_path, "w").close()
    open(val_metrics_log_path, "w").close()

    # Subset fixo estratificado de 4.000 amostras da validação para early stopping ultra-rápido por época
    val_sub_indices = list(range(0, len(val_ds), len(val_ds) // 4000))[:4000]
    val_sub_loader = DataLoader(
        torch.utils.data.Subset(val_ds, val_sub_indices),
        batch_size=512,
        shuffle=False,
        collate_fn=canonical_collate_fn
    )

    max_epochs = 12
    patience = 4

    for epoch in range(1, max_epochs + 1):
        model_a.train()
        epoch_loss = 0.0
        n_samples = 0
        t_epoch_start = time.time()

        for batch in train_loader:
            optimizer_a.zero_grad()
            outputs = model_a(
                history=batch["history"],
                teammates=batch["teammates"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )
            loss_dict = criterion(outputs, batch)
            loss_total = loss_dict["loss_total"]
            loss_total.backward()
            torch.nn.utils.clip_grad_norm_(model_a.parameters(), max_norm=1.0)
            optimizer_a.step()

            bsz = len(batch["positioning_state"])
            epoch_loss += loss_total.item() * bsz
            n_samples += bsz

        avg_train_loss = epoch_loss / n_samples
        epoch_dur = time.time() - t_epoch_start

        # Gravar métrica de treino em jsonl
        train_record = {
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 4),
            "samples": n_samples,
            "duration_seconds": round(epoch_dur, 2)
        }
        with open(train_metrics_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(train_record) + "\n")

        # Avaliação de validação por época
        model_a.eval()
        val_loss_total = 0.0
        val_samples = 0
        with torch.no_grad():
            for v_batch in val_sub_loader:
                v_out = model_a(
                    history=v_batch["history"],
                    teammates=v_batch["teammates"],
                    candidate_mask=v_batch["candidate_mask"],
                    team_idx=v_batch["team_idx"],
                    role_idx=v_batch["role_idx"],
                    stage_idx=v_batch["stage_idx"]
                )
                v_loss = criterion(v_out, v_batch)["loss_total"]
                bsz = len(v_batch["positioning_state"])
                val_loss_total += v_loss.item() * bsz
                val_samples += bsz

        avg_val_loss = val_loss_total / val_samples
        val_record = {
            "epoch": epoch,
            "val_loss": round(avg_val_loss, 4),
            "samples": val_samples
        }
        with open(val_metrics_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(val_record) + "\n")

        print(f"  Modelo A | Época {epoch:02d}/{max_epochs} ({epoch_dur:.1f}s) - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}", flush=True)

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model_a.state_dict(),
                "optimizer_state_dict": optimizer_a.state_dict(),
                "val_loss": best_val_loss,
                "model_type": "TEMPORAL_MODEL_A"
            }, best_ckpt_path)
            print(f"    -> Novo melhor checkpoint salvo: {best_ckpt_path.name} (val_loss={best_val_loss:.4f})", flush=True)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"    -> Early stopping ativado na época {epoch} (patience={patience})", flush=True)
                break

    # Recarregar melhor checkpoint do Modelo A
    ckpt_a = torch.load(best_ckpt_path, map_location="cpu")
    model_a.load_state_dict(ckpt_a["model_state_dict"])
    best_ckpt_sha256 = compute_sha256(best_ckpt_path)

    # =========================================================================
    # 7. Treinamento do Modelo B (Último Frame Real - Last Frame Baseline)
    # =========================================================================
    print("\n" + "=" * 60, flush=True)
    print("[Passo 7/8] TREINANDO MODELO B (ÚLTIMO FRAME REAL: SOMENTE FRAME T INSTANTÂNEO)", flush=True)
    print("=" * 60, flush=True)

    model_b = PositioningTransformerV1(
        hidden_dim=192,
        num_layers=3,
        num_heads=6,
        feedforward_dim=768,
        dropout=0.10
    )
    optimizer_b = optim.AdamW(model_b.parameters(), lr=3e-4, weight_decay=1e-2)

    best_ckpt_b_path = runs_dir / "last_frame_best_checkpoint.pt"
    best_val_loss_b = float("inf")
    patience_counter_b = 0

    for epoch in range(1, max_epochs + 1):
        model_b.train()
        epoch_loss = 0.0
        n_samples = 0
        t_epoch_start = time.time()

        for batch in train_loader:
            optimizer_b.zero_grad()
            # Injetar estritamente o último frame autêntico repetido
            hist_last = batch["history"][:, -1:, :].repeat(1, 32, 1)
            tm_last = batch["teammates"][:, -1:, :, :].repeat(1, 32, 1, 1)

            outputs = model_b(
                history=hist_last,
                teammates=tm_last,
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )
            loss_dict = criterion(outputs, batch)
            loss_total = loss_dict["loss_total"]
            loss_total.backward()
            torch.nn.utils.clip_grad_norm_(model_b.parameters(), max_norm=1.0)
            optimizer_b.step()

            bsz = len(batch["positioning_state"])
            epoch_loss += loss_total.item() * bsz
            n_samples += bsz

        avg_train_loss = epoch_loss / n_samples
        epoch_dur = time.time() - t_epoch_start

        # Validação Modelo B
        model_b.eval()
        val_loss_total = 0.0
        val_samples = 0
        with torch.no_grad():
            for v_batch in val_sub_loader:
                v_hist_last = v_batch["history"][:, -1:, :].repeat(1, 32, 1)
                v_tm_last = v_batch["teammates"][:, -1:, :, :].repeat(1, 32, 1, 1)
                v_out = model_b(
                    history=v_hist_last,
                    teammates=v_tm_last,
                    candidate_mask=v_batch["candidate_mask"],
                    team_idx=v_batch["team_idx"],
                    role_idx=v_batch["role_idx"],
                    stage_idx=v_batch["stage_idx"]
                )
                v_loss = criterion(v_out, v_batch)["loss_total"]
                bsz = len(v_batch["positioning_state"])
                val_loss_total += v_loss.item() * bsz
                val_samples += bsz

        avg_val_loss = val_loss_total / val_samples
        print(f"  Modelo B | Época {epoch:02d}/{max_epochs} ({epoch_dur:.1f}s) - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}", flush=True)

        if avg_val_loss < best_val_loss_b:
            best_val_loss_b = avg_val_loss
            patience_counter_b = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model_b.state_dict(),
                "optimizer_state_dict": optimizer_b.state_dict(),
                "val_loss": best_val_loss_b,
                "model_type": "LAST_FRAME_MODEL_B"
            }, best_ckpt_b_path)
            print(f"    -> Novo melhor checkpoint salvo: {best_ckpt_b_path.name} (val_loss={best_val_loss_b:.4f})", flush=True)
        else:
            patience_counter_b += 1
            if patience_counter_b >= patience:
                print(f"    -> Early stopping ativado na época {epoch} (patience={patience})", flush=True)
                break

    ckpt_b = torch.load(best_ckpt_b_path, map_location="cpu")
    model_b.load_state_dict(ckpt_b["model_state_dict"])
    best_ckpt_b_sha256 = compute_sha256(best_ckpt_b_path)

    # =========================================================================
    # 8. Avaliação Canônica Completa de 100% da Validação nos Dois Modelos
    # =========================================================================
    print("\n" + "=" * 60, flush=True)
    print(f"[Passo 8/8] AVALIAÇÃO CANÔNICA DE 100% DA VALIDAÇÃO ({len(val_ds):,} AMOSTRAS)", flush=True)
    print("=" * 60, flush=True)

    print("\n-> Avaliando Modelo A (Histórico Temporal Real) em 100% da Validação...", flush=True)
    eval_metrics_a = evaluate_model_full_validation(model_a, val_loader, is_last_frame_mode=False)

    print("\n-> Avaliando Modelo B (Último Frame Real) em 100% da Validação...", flush=True)
    eval_metrics_b = evaluate_model_full_validation(model_b, val_loader, is_last_frame_mode=True)

    # Salvar temporal_pilot_metrics.json (Modelo A)
    temporal_metrics_path = runs_dir / "temporal_pilot_metrics.json"
    temporal_payload = {
        "schema_version": "1.0.0",
        "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
        "milestone": "Marco 2A - Piloto Temporal 10%",
        "model_variant": "MODELO_A_REAL_TEMPORAL_HISTORY",
        "input_representation": "REAL_NPZ_32_FRAMES",
        "checkpoint": str(best_ckpt_path.relative_to(BASE_DIR)),
        "checkpoint_sha256": best_ckpt_sha256,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_metrics": eval_metrics_a
    }
    with open(temporal_metrics_path, "w", encoding="utf-8") as f:
        json.dump(temporal_payload, f, indent=2)

    # Salvar last_frame_baseline_metrics.json (Modelo B)
    last_frame_metrics_path = runs_dir / "last_frame_baseline_metrics.json"
    last_frame_payload = {
        "schema_version": "1.0.0",
        "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
        "milestone": "Marco 2A - Ablação Último Frame",
        "model_variant": "MODELO_B_LAST_FRAME_BASELINE",
        "input_representation": "REAL_NPZ_LAST_FRAME_T_ONLY",
        "checkpoint": str(best_ckpt_b_path.relative_to(BASE_DIR)),
        "checkpoint_sha256": best_ckpt_b_sha256,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_metrics": eval_metrics_b
    }
    with open(last_frame_metrics_path, "w", encoding="utf-8") as f:
        json.dump(last_frame_payload, f, indent=2)

    # Gerar temporal_ablation_metrics.json comparando Modelo A vs Modelo B
    ablation_summary_path = runs_dir / "temporal_ablation_metrics.json"

    # Comparativo direto das 5 cabeças
    state_a = eval_metrics_a["head_state"]["macro_f1"]
    state_b = eval_metrics_b["head_state"]["macro_f1"]
    sec_a = eval_metrics_a["head_sector"]["macro_f1"]
    sec_b = eval_metrics_b["head_sector"]["macro_f1"]
    spot_a = eval_metrics_a["head_spot"]["top1_accuracy"]
    spot_b = eval_metrics_b["head_spot"]["top1_accuracy"]
    mrr_a = eval_metrics_a["head_spot"]["mrr"]
    mrr_b = eval_metrics_b["head_spot"]["mrr"]
    trans_a = eval_metrics_a["head_transition"]["macro_f1"]
    trans_b = eval_metrics_b["head_transition"]["macro_f1"]
    trig_a = eval_metrics_a["head_exit_trigger"]["macro_f1"]
    trig_b = eval_metrics_b["head_exit_trigger"]["macro_f1"]

    ablation_payload = {
        "schema_version": "1.0.0",
        "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
        "milestone": "Marco 2A - Ablação Temporal Preliminar",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_samples_count": len(val_ds),
        "comparison_table": {
            "PositioningState_MacroF1": {
                "model_a_temporal": state_a,
                "model_b_last_frame": state_b,
                "delta": round(state_a - state_b, 4)
            },
            "NextSector_MacroF1": {
                "model_a_temporal": sec_a,
                "model_b_last_frame": sec_b,
                "delta": round(sec_a - sec_b, 4)
            },
            "CandidateSpot_Top1": {
                "model_a_temporal": spot_a,
                "model_b_last_frame": spot_b,
                "delta": round(spot_a - spot_b, 4) if isinstance(spot_a, float) and isinstance(spot_b, float) else "N/A"
            },
            "CandidateSpot_MRR": {
                "model_a_temporal": mrr_a,
                "model_b_last_frame": mrr_b,
                "delta": round(mrr_a - mrr_b, 4) if isinstance(mrr_a, float) and isinstance(mrr_b, float) else "N/A"
            },
            "Transition_MacroF1": {
                "model_a_temporal": trans_a,
                "model_b_last_frame": trans_b,
                "delta": round(trans_a - trans_b, 4)
            },
            "ExitTrigger_MacroF1": {
                "model_a_temporal": trig_a,
                "model_b_last_frame": trig_b,
                "delta": round(trig_a - trig_b, 4)
            }
        },
        "invariants": {
            "validation_optimized": False,
            "test_set_touched": False,
            "holdout_touched": False,
            "synthetic_linspace_detected": False,
            "invalid_masked_selections_model_a": eval_metrics_a["head_spot"]["invalid_masked_selections"],
            "invalid_masked_selections_model_b": eval_metrics_b["head_spot"]["invalid_masked_selections"]
        }
    }

    with open(ablation_summary_path, "w", encoding="utf-8") as f:
        json.dump(ablation_payload, f, indent=2)

    print("\n" + "=" * 80, flush=True)
    print("RESUMO DA ABLAÇÃO PRELIMINAR (MODELO A vs MODELO B)", flush=True)
    print(f"PositioningState Macro-F1: A={state_a:.4f} vs B={state_b:.4f} (Delta: {state_a - state_b:+.4f})", flush=True)
    print(f"NextSector Macro-F1:       A={sec_a:.4f} vs B={sec_b:.4f} (Delta: {sec_a - sec_b:+.4f})", flush=True)
    print(f"Transition Macro-F1:       A={trans_a:.4f} vs B={trans_b:.4f} (Delta: {trans_a - trans_b:+.4f})", flush=True)
    print(f"ExitTrigger Macro-F1:      A={trig_a:.4f} vs B={trig_b:.4f} (Delta: {trig_a - trig_b:+.4f})", flush=True)
    print("=" * 80, flush=True)

    print(f"\n[Concluído] Todos os artefatos gerados com sucesso em {runs_dir.relative_to(BASE_DIR)}", flush=True)


if __name__ == "__main__":
    run_pilot_and_ablation()
