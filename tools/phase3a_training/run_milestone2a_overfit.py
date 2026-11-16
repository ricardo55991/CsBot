#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2A: Overfit Controlado do Positioning Transformer V2.

Objetivo:
Demonstrar a capacidade de representação e memorização do Positioning Transformer V2
quando treinado em um subconjunto fixo de 512 sequências reais de Train com diversidade
completa de classes de PositioningState:
- TRANSIT (128 amostras)
- CLEARANCE (64 amostras)
- STAGING (64 amostras)
- HOLD (64 amostras)
- OBJECTIVE (64 amostras)
- RETAKE (64 amostras)
- SAVE (64 amostras)

Critérios de Aceitação Obrigatórios:
1. Treinamento por 40 épocas com AdamW (lr=5e-4, weight_decay=1e-2).
2. Queda da perda multitarefa total superior a 50% entre o início e a época 40.
3. Zero NaN ou Inf em qualquer loss ou gradiente ao longo de todo o treinamento.
4. Zero seleções mascaradas inválidas na predição de SpotId (argmax nunca seleciona spot com candidate_mask == False).
5. Salvar artefatos:
   - training_runs/positioning_v2_real_temporal/overfit_report.md
   - training_runs/positioning_v2_real_temporal/overfit_metrics.json
   - training_runs/positioning_v2_real_temporal/overfit_checkpoint.pt
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Subset, DataLoader

# Resolver diretório base
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.phase3a_training.canonical_temporal_dataloader import (
    CanonicalTemporalPositioningDataset,
    canonical_collate_fn,
    NPZCacheManager,
    STATE_MAP,
    STATE_NAMES
)
from tools.phase3a_training.positioning_model import PositioningTransformerV1, PositioningMultitaskLoss


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_overfit(epochs: int = 40, lr: float = 5e-4, seed: int = 42026) -> Dict[str, Any]:
    print("=" * 80)
    print("FASE 3A.3-B (MARCO 2A) - OVERFIT CONTROLADO DO POSITIONING TRANSFORMER V2")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Seed Determinística: {seed}")
    print(f"Épocas: {epochs} | Learning Rate: {lr}")
    print("=" * 80)

    torch.manual_seed(seed)
    np.random.seed(seed)

    runs_dir = BASE_DIR / "training_runs" / "positioning_v2_real_temporal"
    runs_dir.mkdir(parents=True, exist_ok=True)
    ds_dir = BASE_DIR / "datasets" / "mirage_v2"

    # 1. Carregar pool de Train e amostrar 512 sequências com diversidade de classes
    print("\n[Passo 1/5] Carregando dataset e amostrando 512 instâncias com as 7 classes...")
    cache_manager = NPZCacheManager()

    parquet_paths = [
        ds_dir / "positioning" / "positioning_sequences_v1" / "shard_000.parquet",
        ds_dir / "positioning" / "objective_save_sequences.parquet"
    ]

    base_train_ds = CanonicalTemporalPositioningDataset(
        ds_dir=ds_dir,
        split="train",
        parquet_paths=parquet_paths,
        preload_npz=False,
        cache_manager=cache_manager
    )

    # Amostragem estratificada controlada
    target_counts = {
        "TRANSIT": 128,
        "CLEARANCE": 64,
        "STAGING": 64,
        "HOLD": 64,
        "OBJECTIVE": 64,
        "RETAKE": 64,
        "SAVE": 64
    }

    rng = np.random.RandomState(seed)
    selected_indices = []
    class_breakdown = {}

    for state_name, count in target_counts.items():
        st_idx = STATE_MAP[state_name]
        matches = np.where(base_train_ds.state_vals == st_idx)[0]
        assert len(matches) >= count, f"Amostras insuficientes para classe {state_name}: {len(matches)} < {count}"
        chosen = rng.choice(matches, size=count, replace=False).tolist()
        selected_indices.extend(chosen)
        class_breakdown[state_name] = count

    assert len(selected_indices) == 512, f"Total esperado 512, obtido {len(selected_indices)}"

    # Pré-carregar na RAM as demos únicas do subset
    subset_demos = set([base_train_ds.demos[i] for i in selected_indices])
    print(f"  Subset selecionado: 512 amostras cobrindo {len(subset_demos)} demos únicas de Train.")
    cache_manager.preload(subset_demos)

    overfit_dataset = Subset(base_train_ds, selected_indices)
    batch_size = 64
    loader = DataLoader(
        overfit_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=canonical_collate_fn
    )

    # 2. Inicializar Modelo e Loss
    print("\n[Passo 2/5] Inicializando arquitetura PositioningTransformerV1...")
    # Pesos uniformes para state_head no overfit (o objetivo é memorização completa de todas as classes)
    model = PositioningTransformerV1(
        input_dim=18,
        hidden_dim=192,
        num_layers=3,
        num_heads=6,
        feedforward_dim=768,
        dropout=0.0, # Sem dropout no teste de memorização de overfit
        seq_len=32,
        num_spots=53
    )

    criterion = PositioningMultitaskLoss(
        state_weights=None,
        w_state=1.0,
        w_sector=0.8,
        w_spot=1.5,
        w_transition=0.6,
        w_trigger=0.5
    )

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)

    # 3. Loop de Treinamento por 40 épocas
    print(f"\n[Passo 3/5] Executando {epochs} épocas de Overfit Controlado...")
    history_records: List[Dict[str, Any]] = []

    model.train()
    start_time = time.time()

    initial_loss_total = None
    final_loss_total = None
    all_finite = True
    invalid_masked_selections_total = 0

    for epoch in range(1, epochs + 1):
        epoch_loss_total = 0.0
        epoch_loss_state = 0.0
        epoch_loss_sector = 0.0
        epoch_loss_spot = 0.0
        epoch_loss_transition = 0.0
        epoch_loss_trigger = 0.0

        correct_state = 0
        correct_sector = 0
        correct_spot = 0
        valid_spot_total = 0
        total_samples = 0

        for batch in loader:
            optimizer.zero_grad()
            outputs = model(
                history=batch["history"],
                teammates=batch["teammates"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )

            loss_dict = criterion(outputs, batch)
            loss_total = loss_dict["loss_total"]

            # Checagem de finitude
            if not torch.isfinite(loss_total):
                all_finite = False
                raise ValueError(f"Loss não finita na época {epoch}: {loss_total.item()}")

            loss_total.backward()

            # Grad clip e checagem de gradientes
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            for param in model.parameters():
                if param.grad is not None and not torch.isfinite(param.grad).all():
                    all_finite = False
                    raise ValueError(f"Gradiente não finito na época {epoch}")

            optimizer.step()

            bsz = len(batch["positioning_state"])
            total_samples += bsz
            epoch_loss_total += loss_total.item() * bsz
            epoch_loss_state += loss_dict["loss_state"].item() * bsz
            epoch_loss_sector += loss_dict["loss_sector"].item() * bsz
            epoch_loss_spot += loss_dict["loss_spot"].item() * bsz
            epoch_loss_transition += loss_dict["loss_transition"].item() * bsz
            epoch_loss_trigger += loss_dict["loss_trigger"].item() * bsz

            # Acurácias
            pred_state = torch.argmax(outputs["logits_state"], dim=1)
            correct_state += (pred_state == batch["positioning_state"]).sum().item()

            pred_sector = torch.argmax(outputs["logits_sector"], dim=1)
            correct_sector += (pred_sector == batch["next_sector"]).sum().item()

            # Checagem inegociável de mascara de Spot
            pred_spot = torch.argmax(outputs["logits_spot"], dim=1)
            cand_mask = batch["candidate_mask"]
            # Para cada amostra, o spot predito deve ter candidate_mask == True
            is_valid_candidate = torch.gather(cand_mask, 1, pred_spot.unsqueeze(1)).squeeze(1)
            invalid_masked_selections = (~is_valid_candidate).sum().item()
            invalid_masked_selections_total += invalid_masked_selections

            spot_mask = batch["spot_loss_mask"]
            if spot_mask.sum() > 0:
                correct_spot += ((pred_spot == batch["candidate_spot_idx"]) & spot_mask).sum().item()
                valid_spot_total += spot_mask.sum().item()

        avg_loss = epoch_loss_total / total_samples
        state_acc = correct_state / total_samples
        sector_acc = correct_sector / total_samples
        spot_acc = (correct_spot / valid_spot_total) if valid_spot_total > 0 else 0.0

        if epoch == 1:
            initial_loss_total = avg_loss
        if epoch == epochs:
            final_loss_total = avg_loss

        rec = {
            "epoch": epoch,
            "loss_total": round(avg_loss, 4),
            "loss_state": round(epoch_loss_state / total_samples, 4),
            "loss_sector": round(epoch_loss_sector / total_samples, 4),
            "loss_spot": round(epoch_loss_spot / total_samples, 4),
            "loss_transition": round(epoch_loss_transition / total_samples, 4),
            "loss_trigger": round(epoch_loss_trigger / total_samples, 4),
            "state_accuracy": round(state_acc, 4),
            "sector_accuracy": round(sector_acc, 4),
            "spot_accuracy": round(spot_acc, 4)
        }
        history_records.append(rec)

        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(f"  Época {epoch:02d}/{epochs}: Loss Total={avg_loss:.4f} | StateAcc={state_acc*100:.1f}% | SectorAcc={sector_acc*100:.1f}% | SpotAcc={spot_acc*100:.1f}%")

    total_training_time = time.time() - start_time
    loss_reduction_pct = ((initial_loss_total - final_loss_total) / initial_loss_total) * 100.0

    print(f"\n[Passo 4/5] Treinamento concluído em {total_training_time:.2f}s.")
    print(f"  Loss Inicial (Época 1): {initial_loss_total:.4f}")
    print(f"  Loss Final   (Época {epochs}): {final_loss_total:.4f}")
    print(f"  Redução de Loss: {loss_reduction_pct:.2f}% (Meta: >50.0%)")
    print(f"  Zero NaN/Inf: {all_finite} (PASS)")
    print(f"  Seleções Mascaradas Inválidas: {invalid_masked_selections_total} (PASS)")

    assert loss_reduction_pct > 50.0, f"Redução de loss insuficiente: {loss_reduction_pct:.2f}% <= 50%"
    assert invalid_masked_selections_total == 0, f"Seleções mascaradas inválidas detectadas: {invalid_masked_selections_total}"
    assert all_finite, "Presença de NaN ou Inf detectada durante o treino"

    # 4. Salvar Checkpoint de Overfit
    print("\n[Passo 5/5] Salvando checkpoint e relatórios...")
    ckpt_path = runs_dir / "overfit_checkpoint.pt"
    ckpt_data = {
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "config": {
            "hidden_dim": 192,
            "num_layers": 3,
            "num_heads": 6,
            "feedforward_dim": 768,
            "dropout": 0.0
        },
        "subset_size": 512,
        "seed": seed,
        "initial_loss": initial_loss_total,
        "final_loss": final_loss_total,
        "loss_reduction_pct": loss_reduction_pct
    }
    torch.save(ckpt_data, ckpt_path)
    ckpt_sha256 = compute_sha256(ckpt_path)

    # 5. Salvar JSON de Métricas
    metrics_path = runs_dir / "overfit_metrics.json"
    metrics_payload = {
        "schema_version": "1.0.0",
        "phase": "FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER",
        "milestone": "Marco 2A - Overfit Controlado (Seção 5)",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "data_provenance": "REAL",
        "configuration": {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": lr,
            "optimizer": "AdamW",
            "weight_decay": 1e-2,
            "seed": seed,
            "subset_size": 512
        },
        "class_breakdown": class_breakdown,
        "training_time_seconds": round(total_training_time, 2),
        "results": {
            "initial_loss": round(initial_loss_total, 4),
            "final_loss": round(final_loss_total, 4),
            "loss_reduction_pct": round(loss_reduction_pct, 2),
            "loss_reduction_met": bool(loss_reduction_pct > 50.0),
            "zero_nan_inf": all_finite,
            "invalid_masked_selections": invalid_masked_selections_total,
            "final_state_accuracy": history_records[-1]["state_accuracy"],
            "final_sector_accuracy": history_records[-1]["sector_accuracy"],
            "final_spot_accuracy": history_records[-1]["spot_accuracy"]
        },
        "history": history_records,
        "artifacts": {
            "checkpoint_file": str(ckpt_path.relative_to(BASE_DIR)),
            "checkpoint_sha256": ckpt_sha256
        }
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    metrics_sha256 = compute_sha256(metrics_path)

    # 6. Gerar Relatório Executivo Markdown
    report_path = runs_dir / "overfit_report.md"
    report_md = f"""# Relatório de Overfit Controlado - Marco 2A (Positioning Transformer V2)

**Fase**: FASE 3A.3-B: RECONSTRUÇÃO TEMPORAL CANÔNICA E RETREINO DO POSITIONING TRANSFORMER  
**Milestone**: Marco 2A - Overfit Controlado (Seção 5)  
**Gerado em UTC**: {datetime.now(timezone.utc).isoformat()}  
**Classificação do Dado**: `REAL` (autêntico, extraído diretamente de tensores NPZ e metadados Parquet)  
**Status**: `AUTOMATED_CHECK_PASS` (Em conformidade com AGENTS.md Regras 01, 04, 07 e 09)

---

## 1. Resumo Executivo e Critérios de Aceitação

O teste de Overfit Controlado demonstrou a plena capacidade do Positioning Transformer V2 de memorizar um conjunto de dados complexo e multitarefa contendo todas as 7 classes de `PositioningState`.

| Critério de Governança | Meta Exigida | Valor Observado | Veredito |
| :--- | :---: | :---: | :---: |
| **Tamanho do Subset** | 512 a 1024 sequências | **512 sequências** | **PASS** |
| **Origem dos Dados** | Split Train estrito | **Train Only** (`shard_000` + `objective_save`) | **PASS** |
| **Diversidade de Classes** | 7 classes presentes | **7 classes representadas** | **PASS** |
| **Redução da Loss Total** | > 50.0% | **{loss_reduction_pct:.2f}%** (`{initial_loss_total:.4f}` -> `{final_loss_total:.4f}`) | **PASS** |
| **Finitude Numérica** | Zero NaN / Zero Inf | **0 NaNs, 0 Infs** | **PASS** |
| **Seleções Mascaradas Inválidas** | Exatamente 0 | **0 violações** | **PASS** |

---

## 2. Composição e Estratificação do Subset (512 Amostras)

| Classe de Estado | Amostras Selecionadas | Proporção no Subset | Proveniência |
| :--- | :---: | :---: | :---: |
| `TRANSIT` | 128 | 25.0% | `REAL` |
| `CLEARANCE` | 64 | 12.5% | `REAL` |
| `STAGING` | 64 | 12.5% | `REAL` |
| `HOLD` | 64 | 12.5% | `REAL` |
| `OBJECTIVE` | 64 | 12.5% | `REAL` |
| `RETAKE` | 64 | 12.5% | `REAL` |
| `SAVE` | 64 | 12.5% | `REAL` |
| **Total** | **512** | **100.0%** | **REAL** |

---

## 3. Curva de Convergência e Memorização (Épocas Selecionadas)

| Época | Loss Total | State Loss | Sector Loss | Spot Loss | State Acc | Sector Acc | Spot Acc |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `{history_records[0]['loss_total']:.4f}` | `{history_records[0]['loss_state']:.4f}` | `{history_records[0]['loss_sector']:.4f}` | `{history_records[0]['loss_spot']:.4f}` | `{history_records[0]['state_accuracy']*100:.1f}%` | `{history_records[0]['sector_accuracy']*100:.1f}%` | `{history_records[0]['spot_accuracy']*100:.1f}%` |
| 5 | `{history_records[4]['loss_total']:.4f}` | `{history_records[4]['loss_state']:.4f}` | `{history_records[4]['loss_sector']:.4f}` | `{history_records[4]['loss_spot']:.4f}` | `{history_records[4]['state_accuracy']*100:.1f}%` | `{history_records[4]['sector_accuracy']*100:.1f}%` | `{history_records[4]['spot_accuracy']*100:.1f}%` |
| 10 | `{history_records[9]['loss_total']:.4f}` | `{history_records[9]['loss_state']:.4f}` | `{history_records[9]['loss_sector']:.4f}` | `{history_records[9]['loss_spot']:.4f}` | `{history_records[9]['state_accuracy']*100:.1f}%` | `{history_records[9]['sector_accuracy']*100:.1f}%` | `{history_records[9]['spot_accuracy']*100:.1f}%` |
| 20 | `{history_records[19]['loss_total']:.4f}` | `{history_records[19]['loss_state']:.4f}` | `{history_records[19]['loss_sector']:.4f}` | `{history_records[19]['loss_spot']:.4f}` | `{history_records[19]['state_accuracy']*100:.1f}%` | `{history_records[19]['sector_accuracy']*100:.1f}%` | `{history_records[19]['spot_accuracy']*100:.1f}%` |
| 30 | `{history_records[29]['loss_total']:.4f}` | `{history_records[29]['loss_state']:.4f}` | `{history_records[29]['loss_sector']:.4f}` | `{history_records[29]['loss_spot']:.4f}` | `{history_records[29]['state_accuracy']*100:.1f}%` | `{history_records[29]['sector_accuracy']*100:.1f}%` | `{history_records[29]['spot_accuracy']*100:.1f}%` |
| 40 | `{history_records[39]['loss_total']:.4f}` | `{history_records[39]['loss_state']:.4f}` | `{history_records[39]['loss_sector']:.4f}` | `{history_records[39]['loss_spot']:.4f}` | `{history_records[39]['state_accuracy']*100:.1f}%` | `{history_records[39]['sector_accuracy']*100:.1f}%` | `{history_records[39]['spot_accuracy']*100:.1f}%` |

---

## 4. Rastreabilidade de Artefatos Gerados

- **Relatório Executivo**: `training_runs/positioning_v2_real_temporal/overfit_report.md`
- **Métricas Brutas**: `training_runs/positioning_v2_real_temporal/overfit_metrics.json` (SHA-256: `{metrics_sha256}`)
- **Checkpoint de Overfit**: `training_runs/positioning_v2_real_temporal/overfit_checkpoint.pt` (SHA-256: `{ckpt_sha256}`)
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n[Concluído] Métricas salvas em: {metrics_path.relative_to(BASE_DIR)}")
    print(f"[Concluído] Checkpoint salvo em: {ckpt_path.relative_to(BASE_DIR)}")
    print(f"[Concluído] Relatório salvo em: {report_path.relative_to(BASE_DIR)}")

    return metrics_payload


if __name__ == "__main__":
    run_overfit()
