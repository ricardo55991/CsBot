import numpy as np

def check_rounds():
    d = np.load(r"F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\100-thieves-vs-magic-m2-mirage_16hz.npz")
    X = d["X"]
    # Feature 16 is round_time_remaining
    # Shape is [N, 10, 18]
    r_time = X[:, 0, 16]
    
    # Detect round resets: when round_time jumps from a lower value to a higher value (e.g. from 10s to 115s)
    diff = np.diff(r_time)
    resets = np.where(diff > 15.0)[0]
    print(f"Total frames: {len(r_time)}")
    print(f"Detected round transitions: {len(resets)}")
    print(f"Sample reset ticks: {resets[:5]}")
    for idx in resets[:5]:
        print(f"Before: {r_time[idx]:.1f}s, After: {r_time[idx+1]:.1f}s")

if __name__ == "__main__":
    check_rounds()
