import os
from pathlib import Path
import numpy as np

def scan_files():
    npz_dir = Path(r"F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage")
    dem_dir = Path(r"F:\CS2_MLMove_Pipeline\raw_demos")

    npz_files = list(npz_dir.glob("*.npz"))
    dem_files = list(dem_dir.glob("*.dem"))

    print(f"NPZ files found: {len(npz_files)}")
    print(f"DEM files found: {len(dem_files)}")

    total_frames = 0
    sample_npz = npz_files[0]
    print(f"Sample NPZ: {sample_npz.name}")
    d = np.load(sample_npz)
    print("Keys:", d.files)
    X = d["X"]
    Y = d["Y"]
    print("X shape:", X.shape, "dtype:", X.dtype)
    print("Y shape:", Y.shape, "dtype:", Y.dtype)

if __name__ == "__main__":
    scan_files()
