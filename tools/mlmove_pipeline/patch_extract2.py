from pathlib import Path

p = Path("tools/mlmove_pipeline/extract_16hz_tensors.py")
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

target = """    for dem_path in tqdm(demos, desc=f"Extraindo 16Hz ({map_name})"):
        out_npz = out_dir / f"{dem_path.stem}_16hz.npz"
        try:
            X, Y = extract_single_demo(dem_path)"""

replacement = """    for dem_path in tqdm(demos, desc=f"Extraindo 16Hz ({map_name})"):
        out_npz = out_dir / f"{dem_path.stem}_16hz.npz"
        if out_npz.exists() and out_npz.stat().st_size > 100_000:
            try:
                with np.load(out_npz) as existing_data:
                    c = len(existing_data["X"])
                    total_samples += c
                    print(f"\\n[extract_16hz_tensors] {out_npz.name} já extraído ({c} steps 16Hz).", flush=True)
                    if delete_after_extract:
                        dem_path.unlink(missing_ok=True)
                    continue
            except Exception:
                pass

        try:
            X, Y = extract_single_demo(dem_path)"""

text = text.replace(target, replacement)
text = text.replace('print(', 'print(').replace(') # flush', ', flush=True)')

# Ensure flush=True on extraction print
text = text.replace(
    'print(\n                    f"[extract_16hz_tensors] {dem_path.name} -> {out_npz.name} ({len(X)} steps 16Hz, {out_npz.stat().st_size // 1024} KB)"\n                )',
    'print(f"\\n[extract_16hz_tensors] {dem_path.name} -> {out_npz.name} ({len(X)} steps 16Hz, {out_npz.stat().st_size // 1024} KB)", flush=True)'
)

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

print("extract_16hz_tensors.py updated with cache check and flush.")
