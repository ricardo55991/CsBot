import json
from pathlib import Path
import pandas as pd

base_dir = Path(__file__).resolve().parents[2]
out_dir = base_dir / "datasets" / "mirage_v2"
jump_dir = out_dir / "jump"

df_jumps = pd.read_parquet(jump_dir / "jump_episodes_v2.parquet")
train_split = set(json.loads((out_dir / "train_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])
val_split = set(json.loads((out_dir / "validation_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])
test_split = set(json.loads((out_dir / "test_split_v2.json").read_text(encoding="utf-8"))["demo_ids"])

# Classify each jump into train / val / test by demo_id
df_jumps["split"] = df_jumps["demo_id"].apply(lambda d: "train" if d in train_split else ("validation" if d in val_split else "test"))

reasons = df_jumps["jump_reason"].unique().tolist()
train_counts = df_jumps[df_jumps["split"] == "train"]["jump_reason"].value_counts().to_dict()
val_counts = df_jumps[df_jumps["split"] == "validation"]["jump_reason"].value_counts().to_dict()
test_counts = df_jumps[df_jumps["split"] == "test"]["jump_reason"].value_counts().to_dict()

manifest = json.loads((jump_dir / "jump_episode_manifest_v2.json").read_text(encoding="utf-8"))

payload = {
    "distribution_name": "jump_episode_distribution_v2",
    "generated_at_utc": manifest["generated_at_utc"],
    "total_episodes": len(df_jumps),
    "splits": {
        "train": train_counts,
        "validation": val_counts,
        "test": test_counts
    },
    "totals": df_jumps["jump_reason"].value_counts().to_dict(),
    "ballistic_stats": manifest["stats"]
}

(out_dir / "jump_episode_distribution_v2.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
(out_dir / "reports" / "jump_episode_distribution_v2.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print("jump_episode_distribution_v2.json written successfully!")
