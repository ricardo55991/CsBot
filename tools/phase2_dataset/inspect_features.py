import numpy as np

d = np.load(r"F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\100-thieves-vs-magic-m2-mirage_16hz.npz")
X = d["X"]
print("X shape:", X.shape)
p0 = X[0, 0, :]
print("Frame 0 Player 0 features:")
for i, v in enumerate(p0):
    print(f"feat {i:02d}: {v}")

print("\nMin/Max across all frames for player 0:")
for i in range(18):
    vals = X[:, 0, i]
    print(f"feat {i:02d}: min={np.min(vals):.2f}, max={np.max(vals):.2f}, unique={len(np.unique(vals[:100]))}")
