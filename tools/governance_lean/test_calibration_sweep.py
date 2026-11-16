"""
Exploração dos thresholds de transição no checkpoint rare_class_patch_v1/selected_patch_checkpoint.pt
"""
import sys
import json
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.phase3a_training.positioning_model_v2 import PositioningTransformerV2RealTemporal
from tools.phase3a_training.canonical_v2_dataloader import CanonicalV2PositioningDataset, canonical_v2_collate_fn, load_supervised_spot_mask

CKPT_PATH = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1" / "selected_patch_checkpoint.pt"

def main():
    print("Carregando modelo e dataset...")
    sup_mask_t = load_supervised_spot_mask()
    model = PositioningTransformerV2RealTemporal(supervised_spot_mask=sup_mask_t)
    state_dict = torch.load(CKPT_PATH, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    val_ds = CanonicalV2PositioningDataset(split="validation", max_samples=5120, seed=42028)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, collate_fn=canonical_v2_collate_fn)

    all_probs = []
    all_targets = []
    all_state_preds = []
    all_state_targets = []

    with torch.no_grad():
        for batch in val_loader:
            out = model(
                self_history=batch["self_history"],
                teammates=batch["teammates"],
                temporal_mask=batch["temporal_mask"],
                candidate_mask=batch["candidate_mask"],
                team_idx=batch["team_idx"],
                role_idx=batch["role_idx"],
                stage_idx=batch["stage_idx"]
            )
            probs = F.softmax(out["logits_transition_occurs"], dim=1)[:, 1].cpu().numpy()
            all_probs.extend(probs)
            all_targets.extend(batch["sector_transition_occurs"].cpu().numpy())

            preds_st = torch.argmax(out["logits_state"], dim=1).cpu().numpy()
            all_state_preds.extend(preds_st)
            all_state_targets.extend(batch["positioning_state"].cpu().numpy())

    probs = np.array(all_probs)
    targets = np.array(all_targets)
    state_preds = np.array(all_state_preds)
    state_targets = np.array(all_state_targets)

    print("\nVarredura de Thresholds de Transição:")
    thresholds = [0.45, 0.475, 0.50, 0.525, 0.55, 0.575, 0.60, 0.625, 0.65]
    for th in thresholds:
        preds = (probs >= th).astype(int)
        tp = int(np.sum((preds == 1) & (targets == 1)))
        fp = int(np.sum((preds == 1) & (targets == 0)))
        tn = int(np.sum((preds == 0) & (targets == 0)))
        fn = int(np.sum((preds == 0) & (targets == 1)))

        rec_to = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        rec_no = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        prec_to = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        prec_no = tn / (tn + fn) if (tn + fn) > 0 else 0.0

        f1_to = 2 * prec_to * rec_to / (prec_to + rec_to) if (prec_to + rec_to) > 0 else 0.0
        f1_no = 2 * prec_no * rec_no / (prec_no + rec_no) if (prec_no + rec_no) > 0 else 0.0
        macro_f1 = (f1_to + f1_no) / 2.0
        bal_acc = (rec_to + rec_no) / 2.0

        meets = (rec_to >= 0.35 and rec_no >= 0.80 and macro_f1 >= 0.55 and bal_acc >= 0.55)
        print(f"th={th:.3f} | rec_to={rec_to:.4f} | rec_no={rec_no:.4f} | bal_acc={bal_acc:.4f} | macro_f1={macro_f1:.4f} | MEETS={meets}")

    print("\nEstado de OBJECTIVE no checkpoint atual:")
    # OBJECTIVE é índice 4 em STATE_NAMES: ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE", "SAVE"]
    obj_tp = int(np.sum((state_preds == 4) & (state_targets == 4)))
    obj_fp = int(np.sum((state_preds == 4) & (state_targets != 4)))
    obj_fn = int(np.sum((state_preds != 4) & (state_targets == 4)))
    obj_sup = int(np.sum(state_targets == 4))
    print(f"OBJECTIVE: support={obj_sup}, tp={obj_tp}, fp={obj_fp}, fn={obj_fn}")

if __name__ == "__main__":
    main()
