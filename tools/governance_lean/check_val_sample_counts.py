"""
Verifica quantidade de OBJECTIVE e distribuição nas 5120 amostras canônicas de validação.
"""
import sys
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset, canonical_v2_collate_fn
from tools.phase3a_training.positioning_model_v2 import STATE_NAMES

def main():
    val_ds = CanonicalV2PositioningDataset(split="validation", max_samples=5120, seed=42028)
    pos_states = val_ds.df_b["PositioningState"].value_counts()
    print("Contagem em 5120 amostras de validação (seed 42028):")
    for s, c in pos_states.items():
        print(f"  {s}: {c}")

if __name__ == "__main__":
    main()
