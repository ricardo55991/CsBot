import numpy as np

d = np.load(r"F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\100-thieves-vs-magic-m2-mirage_16hz.npz")
X = d["X"]
r_time_norm = X[:, 0, 17]

# Where does r_time_norm increase significantly?
diff = np.diff(r_time_norm)
resets = np.where(diff > 0.15)[0]
print(f"Total frames: {len(r_time_norm)}")
print(f"Rounds detected in this demo: {len(resets) + 1}")
print(f"Reset frames: {resets[:10]}")
for idx in resets[:5]:
    print(f"Frame {idx}: before={r_time_norm[idx]:.3f}, after={r_time_norm[idx+1]:.3f}")
