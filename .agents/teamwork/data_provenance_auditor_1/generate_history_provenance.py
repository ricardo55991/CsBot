#!/usr/bin/env python3
"""
Gera os entregáveis pre3a3_history_provenance.json e pre3a3_history_provenance.md
em training_runs/positioning_v1/ cobrindo as seeds 42026, 42027 e 42028.
Data Provenance Auditor.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
RUNS_DIR = ROOT_DIR / "training_runs" / "positioning_v1"

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("GERANDO PRE3A3_HISTORY_PROVENANCE (.JSON e .MD)")
    print("=" * 80)

    # 1. Mapeamento de Hashes SHA-256
    files_to_hash = {
        "train_script": ROOT_DIR / "tools/phase3a_training/train_full.py",
        "data_utils": ROOT_DIR / "tools/phase3a_training/data_utils.py",
        "positioning_model": ROOT_DIR / "tools/phase3a_training/positioning_model.py",
        "canonical_eval": ROOT_DIR / "tools/phase3a_training/evaluate_positioning_v1_canonical.py",
        "phase2_dataloaders": ROOT_DIR / "tools/phase2_dataset/dataloaders.py",
        "phase2_builder": ROOT_DIR / "tools/phase2_dataset/step9_to_18_build_datasets.py",
        "master_model": ROOT_DIR / "models/positioning/de_mirage_positioning_v1.pt",
        "seed_42026_best": RUNS_DIR / "seed_42026/best_checkpoint.pt",
        "seed_42026_last": RUNS_DIR / "seed_42026/last_checkpoint.pt",
        "seed_42027_best": RUNS_DIR / "seed_42027/best_checkpoint.pt",
        "seed_42027_last": RUNS_DIR / "seed_42027/last_checkpoint.pt",
        "seed_42028_best": RUNS_DIR / "seed_42028/best_checkpoint.pt",
        "seed_42028_last": RUNS_DIR / "seed_42028/last_checkpoint.pt",
        "canonical_test_parquet": ROOT_DIR / "datasets/mirage_v2/positioning/canonical_test_set.parquet",
        "shard_000": ROOT_DIR / "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_000.parquet",
        "shard_001": ROOT_DIR / "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_001.parquet",
        "shard_002": ROOT_DIR / "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_002.parquet",
        "shard_003": ROOT_DIR / "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_003.parquet",
        "shard_004": ROOT_DIR / "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_004.parquet",
        "shard_005": ROOT_DIR / "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_005.parquet"
    }

    hashes = {k: compute_sha256(v) for k, v in files_to_hash.items()}

    # 2. Estrutura JSON
    provenance_json = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-11-07T21:40:00Z",
        "auditor": "Data Provenance Auditor (teamwork_auditor)",
        "validation_classification": "AGENT_REVIEWED",
        "data_nature": "REAL",
        "provenance_verdict": "CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY",
        "training_pipeline": {
            "training_script": {
                "file_path": "tools/phase3a_training/train_full.py",
                "sha256": hashes["train_script"],
                "entry_points": [
                    "run_full_training (L302-L378)",
                    "train_single_seed (L62-L300)"
                ]
            },
            "actual_dataloader": {
                "class_name": "InMemoryPositioningDataset",
                "module": "tools/phase3a_training/data_utils.py",
                "sha256": hashes["data_utils"],
                "dataset_builder": "create_dataset_from_shards (L311-L364)",
                "shard_loader": "load_and_preprocess_shard (L191-L309)",
                "pattern": "Pré-carregamento vetorizado em tensores PyTorch na memória RAM"
            },
            "declared_dataloader_in_snapshot": {
                "class_name": "PositioningDatasetV1",
                "module": "tools/phase2_dataset/dataloaders.py",
                "sha256": hashes["phase2_dataloaders"],
                "status": "DISCREPANCY_DETECTED (Registrado no input_snapshot.json mas substituído por InMemoryPositioningDataset no código de treino)"
            },
            "dataset_paths": {
                "dataset_directory": "datasets/mirage_v2",
                "positioning_shards_directory": "datasets/mirage_v2/positioning/positioning_sequences_v1",
                "training_shards": [
                    {"shard": "shard_000.parquet", "sha256": hashes["shard_000"]},
                    {"shard": "shard_001.parquet", "sha256": hashes["shard_001"]},
                    {"shard": "shard_002.parquet", "sha256": hashes["shard_002"]},
                    {"shard": "shard_003.parquet", "sha256": hashes["shard_003"]},
                    {"shard": "shard_004.parquet", "sha256": hashes["shard_004"]},
                    {"shard": "shard_005.parquet", "sha256": hashes["shard_005"]}
                ],
                "canonical_test_set": {
                    "file_path": "datasets/mirage_v2/positioning/canonical_test_set.parquet",
                    "sha256": hashes["canonical_test_parquet"]
                },
                "split_sample_limits": {
                    "train": 16000,
                    "validation": 4000,
                    "test": 20000
                }
            },
            "code_hashes": {
                "tools/phase3a_training/train_full.py": hashes["train_script"],
                "tools/phase3a_training/data_utils.py": hashes["data_utils"],
                "tools/phase3a_training/positioning_model.py": hashes["positioning_model"],
                "tools/phase3a_training/evaluate_positioning_v1_canonical.py": hashes["canonical_eval"],
                "tools/phase2_dataset/dataloaders.py": hashes["phase2_dataloaders"],
                "tools/phase2_dataset/step9_to_18_build_datasets.py": hashes["phase2_builder"]
            },
            "checkpoint_hashes": {
                "models/positioning/de_mirage_positioning_v1.pt": hashes["master_model"],
                "training_runs/positioning_v1/seed_42026/best_checkpoint.pt": hashes["seed_42026_best"],
                "training_runs/positioning_v1/seed_42026/last_checkpoint.pt": hashes["seed_42026_last"],
                "training_runs/positioning_v1/seed_42027/best_checkpoint.pt": hashes["seed_42027_best"],
                "training_runs/positioning_v1/seed_42027/last_checkpoint.pt": hashes["seed_42027_last"],
                "training_runs/positioning_v1/seed_42028/best_checkpoint.pt": hashes["seed_42028_best"],
                "training_runs/positioning_v1/seed_42028/last_checkpoint.pt": hashes["seed_42028_last"]
            }
        },
        "tensor_construction": {
            "self_history": {
                "tensor_name": "history",
                "tensor_shape": "[B, 32, 18]",
                "dtype": "torch.float32",
                "construction_function": "tools/phase3a_training/data_utils.py:load_and_preprocess_shard (L217-L228)",
                "construction_logic": {
                    "base_position": "pos_arr[:, 0:3] / 3000.0 (current_pos repetido em todos os 32 timesteps)",
                    "drift_application": "step_drift = np.linspace(-0.01, 0.0, 32, dtype=np.float32).reshape(1, 32, 1); history_arr[:, :, 0] += step_drift[:, :, 0]",
                    "feature_0_x": "cur_pos_x / 3000.0 + np.linspace(-0.01, 0.0, 32)",
                    "feature_1_y": "cur_pos_y / 3000.0 (estático, var=0)",
                    "feature_2_z": "cur_pos_z / 3000.0 (estático, var=0)",
                    "feature_3_health": "1.0 (estático)",
                    "feature_4_is_alive": "1.0 (estático)",
                    "features_5_to_17": "0.0 (totalmente zeradas)"
                },
                "data_nature": "TEMPLATED_AND_SYNTHETIC",
                "reaches_training_loss": True,
                "reaches_validation_loss": True,
                "reaches_test_evaluation": True
            },
            "teammate_history": {
                "tensor_name": "teammates",
                "tensor_shape": "[B, 32, 4, 18]",
                "dtype": "torch.float32",
                "construction_function": "tools/phase3a_training/data_utils.py:load_and_preprocess_shard (L230-L238)",
                "construction_logic": {
                    "ally_offset_formula": "offset = (i + 1) * 0.05",
                    "ally_x": "(pos_arr[:, 0:1] / 3000.0) + offset",
                    "ally_y": "(pos_arr[:, 1:2] / 3000.0) - offset",
                    "ally_z": "pos_arr[:, 2:3] / 3000.0",
                    "ally_health": "1.0",
                    "ally_is_alive": "1.0",
                    "features_5_to_17": "0.0"
                },
                "data_nature": "SYNTHETIC",
                "temporal_variance": 0.0
            },
            "sequence_source": {
                "storage_format": "Apache Parquet (SNAPPY compression)",
                "file_location": "datasets/mirage_v2/positioning/positioning_sequences_v1/shard_*.parquet",
                "extraction_script": "tools/phase2_dataset/step9_to_18_build_datasets.py (L268)",
                "saved_content": "Apenas o vetor pontual current_pos: [round(cur_x, 1), round(cur_y, 1), round(cur_z, 1)]. Nenhuma janela temporal pregressa foi gravada no Parquet."
            },
            "sequence_length": 32,
            "feature_dimensions": 18,
            "tick_source": {
                "in_parquet": "NENHUMA coluna de tick existe no schema de sequências de posicionamento.",
                "in_temporal_sample_json": "Sintetizado artificialmente por fórmula: base_tick = round_idx * 1920 + 320 (tools/phase2_dataset/forensic_step4_temporal_windows.py:L56).",
                "in_npz_files": "Frame index f_idx de tensores contínuos a 16Hz (F:\\CS2_MLMove_Pipeline\\extracted_tensors\\de_mirage\\*.npz)."
            }
        },
        "seeds_training_records": {
            "seed_42026": {
                "seed": 42026,
                "best_epoch": 4,
                "composite_score": 0.5305,
                "best_val_metrics": {
                    "state_macro_f1": 0.3451,
                    "spot_mrr": 0.8072,
                    "spot_top1_accuracy": 0.6690,
                    "spot_top5_accuracy": 0.9890
                },
                "best_checkpoint_sha256": hashes["seed_42026_best"],
                "last_checkpoint_sha256": hashes["seed_42026_last"]
            },
            "seed_42027": {
                "seed": 42027,
                "best_epoch": 6,
                "composite_score": 0.5589,
                "best_val_metrics": {
                    "state_macro_f1": 0.3828,
                    "spot_mrr": 0.8529,
                    "spot_top1_accuracy": 0.7560,
                    "spot_top5_accuracy": 0.9890
                },
                "best_checkpoint_sha256": hashes["seed_42027_best"],
                "last_checkpoint_sha256": hashes["seed_42027_last"],
                "status": "SELECTED_AS_MASTER_MODEL (Copiado para models/positioning/de_mirage_positioning_v1.pt)"
            },
            "seed_42028": {
                "seed": 42028,
                "best_epoch": 5,
                "composite_score": 0.5524,
                "best_val_metrics": {
                    "state_macro_f1": 0.3625,
                    "spot_mrr": 0.8483,
                    "spot_top1_accuracy": 0.7370,
                    "spot_top5_accuracy": 0.9890
                },
                "best_checkpoint_sha256": hashes["seed_42028_best"],
                "last_checkpoint_sha256": hashes["seed_42028_last"]
            }
        }
    }

    output_json = RUNS_DIR / "pre3a3_history_provenance.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(provenance_json, f, indent=2)
    print(f"Salvo: {output_json}")

    # 3. Gerar pre3a3_history_provenance.md
    output_md = RUNS_DIR / "pre3a3_history_provenance.md"
    md_content = f"""# Relatório Forense de Proveniência do Histórico Temporal de Treinamento

- **Fase**: Pré-Fase 3A.3 / Requisito R3
- **Auditor**: Data Provenance Auditor (`teamwork_auditor`)
- **Modo**: Somente Leitura (Read-Only Data Provenance & Training Pipeline Audit)
- **Classificação Canônica da Validação**: `AGENT_REVIEWED`
- **Classificação da Natureza dos Dados**: `REAL`
- **Veredito Canônico de Proveniência**: **`CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`**
- **Data e Hora UTC**: 2026-11-07T21:40:00Z
- **Artefato JSON Complementar**: `training_runs/positioning_v1/pre3a3_history_provenance.json`
- **Escopo Auditado**: Seeds Canônicas `42026`, `42027` e `42028`

---

## 1. Sumário da Auditoria de Proveniência

A auditoria forense do caminho físico e lógico de treinamento do `PositioningTransformerV1` para as três seeds canônicas (42026, 42027 e 42028) revelou conclusivamente:

1. **Substituição Estrutural de DataLoader**:
   - O arquivo `input_snapshot.json` de cada seed registrou formalmente o hash `921836c8a9c4590f91a2ed3aa8da090a4470878bb8f6e66a8dc25997d198183d`, correspondente ao DataLoader `PositioningDatasetV1` em `tools/phase2_dataset/dataloaders.py`.
   - No entanto, o script real de treino (`tools/phase3a_training/train_full.py:L42-L43`) importou e executou `tools/phase3a_training/data_utils.py:InMemoryPositioningDataset` (SHA-256: `{hashes['data_utils']}`).
2. **Injeção de Drift Linear Sintético (`np.linspace`)**:
   - O DataLoader real da Fase 3A introduziu a injeção artificial de `step_drift = np.linspace(-0.01, 0.0, 32)` no eixo X (`tools/phase3a_training/data_utils.py:L226-L227`).
   - Essa inclinação artificial alcançou a projeção linear de entrada `player_proj`, a atenção do Transformer, e as perdas de treinamento e validação de todas as três seeds.
3. **Clonagem Fictícia de Companheiros de Equipe**:
   - Quatro aliados sintéticos foram fabricados aplicando offsets determinísticos `(i+1)*0.05` sobre as coordenadas do jogador próprio (`tools/phase3a_training/data_utils.py:L231-L238`), com variância temporal rigorosamente nula (`std == 0`).
4. **Ausência Física de Fatias NPZ no Dataset Parquet**:
   - Os arquivos Parquet de treino e teste (`shard_*.parquet`) contêm exclusivamente o ponto instantâneo `current_pos: [x, y, z]` (amostrado em `tools/phase2_dataset/step9_to_18_build_datasets.py:L268`). Nenhuma janela temporal pregresso de 32 passos jamais existiu na base tabular do repositório.
5. **Universalidade do Vício Temporal**:
   - As três seeds canônicas foram treinadas sob exatamente o mesmo regime de dados sintéticos. O modelo mestre final (`models/positioning/de_mirage_positioning_v1.pt`, proveniente da seed 42027) compartilha integralmente esse vício de representação.

---

## 2. Inventário Completo do Caminho de Treinamento

| Componente | Especificação Físico-Lógica | Caminho do Arquivo | Hash SHA-256 Completo (64 caracteres) |
| :--- | :--- | :--- | :--- |
| **Script de Treino** | `train_full.py:run_full_training` | `tools/phase3a_training/train_full.py` | `{hashes['train_script']}` |
| **DataLoader Real** | `InMemoryPositioningDataset` | `tools/phase3a_training/data_utils.py` | `{hashes['data_utils']}` |
| **DataLoader Declarado** | `PositioningDatasetV1` (Fase 2.2) | `tools/phase2_dataset/dataloaders.py` | `{hashes['phase2_dataloaders']}` |
| **Arquitetura Neural** | `PositioningTransformerV1` | `tools/phase3a_training/positioning_model.py` | `{hashes['positioning_model']}` |
| **Script de Avaliação** | `evaluate_positioning_v1_canonical.py` | `tools/phase3a_training/evaluate_positioning_v1_canonical.py` | `{hashes['canonical_eval']}` |
| **Construtor do Dataset** | `step9_to_18_build_datasets.py` | `tools/phase2_dataset/step9_to_18_build_datasets.py` | `{hashes['phase2_builder']}` |
| **Modelo Mestre** | Melhor modelo (Seed 42027) | `models/positioning/de_mirage_positioning_v1.pt` | `{hashes['master_model']}` |
| **Checkpoint Seed 42026** | Melhor Época 4 (Score 0.5305) | `training_runs/positioning_v1/seed_42026/best_checkpoint.pt` | `{hashes['seed_42026_best']}` |
| **Checkpoint Seed 42027** | Melhor Época 6 (Score 0.5589) | `training_runs/positioning_v1/seed_42027/best_checkpoint.pt` | `{hashes['seed_42027_best']}` |
| **Checkpoint Seed 42028** | Melhor Época 5 (Score 0.5524) | `training_runs/positioning_v1/seed_42028/best_checkpoint.pt` | `{hashes['seed_42028_best']}` |
| **Shard 000 Parquet** | Split Train / Val | `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_000.parquet` | `{hashes['shard_000']}` |
| **Shard 001 Parquet** | Split Train / Val | `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_001.parquet` | `{hashes['shard_001']}` |
| **Shard 002 Parquet** | Split Train / Val | `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_002.parquet` | `{hashes['shard_002']}` |
| **Shard 003 Parquet** | Split Train / Val | `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_003.parquet` | `{hashes['shard_003']}` |
| **Shard 004 Parquet** | Split Train / Val | `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_004.parquet` | `{hashes['shard_004']}` |
| **Shard 005 Parquet** | Split Train / Val | `datasets/mirage_v2/positioning/positioning_sequences_v1/shard_005.parquet` | `{hashes['shard_005']}` |
| **Test Set Canônico** | Test Set Congelado (20k seqs) | `datasets/mirage_v2/positioning/canonical_test_set.parquet` | `{hashes['canonical_test_parquet']}` |

---

## 3. Construção Matemática dos Tensores de Histórico

### 3.1 Histórico do Jogador (`self_history`)
- **Assinatura e Shape**: `[B, 32, 18]` em `torch.float32`.
- **Fórmula Exata** (`data_utils.py:L218-L227`):
  $$\\text{{history}}[n, t, 0] = \\frac{{\\text{{cur\\_pos\\_x}}[n]}}{{3000.0}} + \\text{{linspace}}(-0.01, 0.0, 32)[t]$$
  $$\\text{{history}}[n, t, 1] = \\frac{{\\text{{cur\\_pos\\_y}}[n]}}{{3000.0}}$$
  $$\\text{{history}}[n, t, 2] = \\frac{{\\text{{cur\\_pos\\_z}}[n]}}{{3000.0}}$$
  $$\\text{{history}}[n, t, 3] = 1.0 \\quad (\\text{{Health}})$$
  $$\\text{{history}}[n, t, 4] = 1.0 \\quad (\\text{{IsAlive}})$$
  $$\\text{{history}}[n, t, 5..17] = 0.0$$
- **Classificação**: `UNLABELED_SYNTHETIC_INPUT`.

### 3.2 Histórico dos Aliados (`teammate_history`)
- **Assinatura e Shape**: `[B, 32, 4, 18]` em `torch.float32`.
- **Fórmula Exata** (`data_utils.py:L231-L238`):
  Para cada aliado $i \\in \\{{0, 1, 2, 3\\}}$:
  $$\\text{{teammates}}[n, t, i, 0] = \\frac{{\\text{{cur\\_pos\\_x}}[n]}}{{3000.0}} + (i + 1) \\times 0.05$$
  $$\\text{{teammates}}[n, t, i, 1] = \\frac{{\\text{{cur\\_pos\\_y}}[n]}}{{3000.0}} - (i + 1) \\times 0.05$$
  $$\\text{{teammates}}[n, t, i, 2] = \\frac{{\\text{{cur\\_pos\\_z}}[n]}}{{3000.0}}$$
  $$\\text{{teammates}}[n, t, i, 3..4] = 1.0, \\quad \\text{{teammates}}[n, t, i, 5..17] = 0.0$$
- **Classificação**: `SYNTHETIC`.

---

## 4. Origem das Sequências, Comprimento, Dimensões e Ticks

1. **Sequence Source**:
   - Originada de `tools/phase2_dataset/step9_to_18_build_datasets.py` através da leitura de arrays `X` e `Y` dos 444 arquivos `.npz` em `F:\\CS2_MLMove_Pipeline\\extracted_tensors\\de_mirage\\`.
   - Na linha 268, o script gravou unicamente a coordenada instantânea `current_pos`. Os dados contínuos de locomoção foram descartados para o dataset de posicionamento.
2. **Sequence Length**:
   - Estritamente **32 timesteps** (a 16Hz representa 2,0 segundos de histórico).
3. **Feature Dimensions**:
   - **18 canais de features** por timestep.
4. **Tick Source**:
   - **No Parquet**: Nenhuma coluna de tick físico está presente nas tabelas de sequências de posicionamento.
   - **Nos Relatórios/JSON da Fase 2.2**: O script forense `tools/phase2_dataset/forensic_step4_temporal_windows.py:L56` fabricou ticks fictícios através da expressão determinística `base_tick = round_idx * 1920 + 320`.
   - **Nos Arquivos NPZ**: O índice contínuo de frame `f_idx` registra a taxa real de amostragem de 16Hz.

---

## 5. Comparativo de Treinamento das Seeds 42026, 42027 e 42028

As três seeds canônicas foram executadas sob parâmetros uniformes:
- **Otimizador**: AdamW ($lr=3\\times 10^{{-4}}$, $weight\\_decay=10^{{-2}}$, $batch\\_size=64$, $grad\\_clip=1.0$)
- **Scheduler**: CosineAnnealingLR ($\\eta_{{min}}=10^{{-5}}$)
- **Tamanho de Treino**: 16.000 sequências sintéticas
- **Tamanho de Validação**: 4.000 sequências sintéticas

| Dimensão de Comparação | Seed 42026 | Seed 42027 (Mestre) | Seed 42028 |
| :--- | :---: | :---: | :---: |
| **Melhor Época** | Época 4 | **Época 6** | Época 5 |
| **Composite Score Máximo** | `0.5305` | **`0.5589`** | `0.5524` |
| **State Macro-F1 na Validação** | `0.3451` | **`0.3828`** | `0.3625` |
| **Spot MRR na Validação** | `0.8072` | **`0.8529`** | `0.8483` |
| **Spot Top-1 Accuracy** | `66.9%` | **`75.6%`** | `73.7%` |
| **Spot Top-5 Accuracy** | `98.9%` | **`98.9%`** | `98.9%` |
| **Hash SHA-256 do Checkpoint** | `{hashes['seed_42026_best'][:16]}...` | `{hashes['seed_42027_best'][:16]}...` | `{hashes['seed_42028_best'][:16]}...` |
| **Status na Seleção Final** | Descartado | **Vencedor (Modelo Mestre)** | Descartado |

---

## 6. Veredito Canônico de Proveniência

Com base na auditoria ininterrupta de código, na checagem dos hashes SHA-256 de todos os artefatos e na inspeção física linha a linha do pipeline de dados:

1. **Veredito**: **`CHECKPOINT_TRAINED_WITH_SYNTHETIC_HISTORY`** (Opção B do Requisito R4).
2. **Justificativa**: O modelo mestre e todos os checkpoints intermediários das seeds 42026, 42027 e 42028 consumiram tensores de histórico construídos por interpolação linear artificial (`np.linspace`) e companheiros clonados por deslocamento fixo.
3. **Preservação e Ação Futura**: Os checkpoints devem ser preservados como artefatos de pesquisa experimental. Para aplicação em runtime real do CS2, o modelo deverá ser retreinado a partir dos 444 arquivos `.npz` físicos que contêm a locomoção contínua e as trajetórias reais dos jogadores.
"""

    with open(output_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Salvo: {output_md}")

if __name__ == "__main__":
    main()
