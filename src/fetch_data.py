"""Download the raw dataset once at a fixed revision."""

from pathlib import Path

from datasets import load_dataset

DATASET = "maharshipandya/spotify-tracks-dataset"
REVISION = "635b034f69257814eff850a5c2b3346fe458134f"

out = Path("data/raw/data.parquet")
out.parent.mkdir(parents=True, exist_ok=True)
ds = load_dataset(DATASET, revision=REVISION, split="train")
ds.to_parquet(str(out))
print(f"saved {len(ds)} rows -> {out}")
