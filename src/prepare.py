"""Clean, label, encode, split"""

from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    p = yaml.safe_load((ROOT / "params.yaml").read_text())["data"]
    df = pd.read_parquet(ROOT / "data/raw/data.parquet")

    # drop duplicate songs if present, otherwise they leak into test
    df = df.drop_duplicates(subset="track_id")
    index_cols = [c for c in df.columns if c.startswith("Unnamed")]
    df = df.drop(columns=p["drop"] + index_cols, errors="ignore").dropna()

    y = (df[p["target"]] >= p["threshold"]).astype(int)
    x = pd.get_dummies(df.drop(columns=[p["target"]]), dtype=int)
    x = x.astype({c: int for c in x.select_dtypes("bool").columns})
    data = x.assign(target=y)

    train, test = train_test_split(
        data, test_size=p["test_size"], random_state=p["seed"], stratify=data["target"]
    )
    out = ROOT / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    train.to_csv(out / "train.csv", index=False)
    test.to_csv(out / "test.csv", index=False)
    print(
        f"train={len(train)} test={len(test)} features={x.shape[1]} hit_share={y.mean():.2f}"
    )


if __name__ == "__main__":
    main()
