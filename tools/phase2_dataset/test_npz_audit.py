import json
import hashlib
from pathlib import Path
import numpy as np
from tqdm import tqdm

def audit_npz_files():
    npz_dir = Path(r"F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage")
    files = sorted(list(npz_dir.glob("*.npz")))
    print(f"Total NPZ files: {len(files)}")

    total_frames = 0
    corrupted_files = []
    
    # Check sample files
    frame_counts = []
    for f in files[:20]:
        try:
            d = np.load(f)
            X = d["X"]
            Y = d["Y"]
            n_frames = X.shape[0]
            frame_counts.append(n_frames)
            total_frames += n_frames
        except Exception as e:
            corrupted_files.append((f.name, str(e)))

    print(f"Sample 20 files average frames: {np.mean(frame_counts):.1f}")
    print(f"Corrupted in sample: {len(corrupted_files)}")

if __name__ == "__main__":
    audit_npz_files()
