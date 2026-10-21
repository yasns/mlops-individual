"""NFR-08: TPR gap between genres must be <= 0.20."""

import json
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
THRESHOLD, MIN_N, MIN_HITS = 0.20, 100, 10  # small genres are too noisy to compare

model = joblib.load(ROOT / "models/model.pkl")
test = pd.read_csv(ROOT / "data/processed/test.csv")
x = test.drop(columns="target")

genre_cols = [c for c in x.columns if c.startswith("track_genre_")]
df = pd.DataFrame(
    {
        "genre": x[genre_cols]
        .idxmax(axis=1)
        .str.removeprefix("track_genre_"),  # one-hot -> name
        "y": test["target"],
        "pred": model.predict(x),
    }
)

hits = df[df.y == 1]
g = pd.DataFrame(
    {
        "n": df.groupby("genre").size(),
        "hits": hits.groupby("genre").size(),
        "tpr": (hits.pred == 1).groupby(hits.genre).mean(),
    }
)
g = g[(g.n >= MIN_N) & (g.hits >= MIN_HITS)].astype({"hits": int}).sort_values("tpr")

gap = g.tpr.max() - g.tpr.min()
print(g.round(2).to_string())
print(f"\n{len(g)} genres, {(g.tpr == 0).sum()} with TPR = 0")
print(
    f"TPR gap: {gap:.2f} ({g.index[0]} {g.tpr.iloc[0]:.2f} .. {g.index[-1]} {g.tpr.iloc[-1]:.2f})"
)
passed = bool(gap <= THRESHOLD)
print("NFR-07:", "PASS" if passed else "FAIL")

sha = subprocess.check_output(
    ["git", "rev-parse", "--short=8", "HEAD"], cwd=ROOT, text=True
).strip()
report = {
    "git_commit": sha,
    "mlflow_run_id": (ROOT / "models/run_id.txt").read_text().strip(),
    "threshold": THRESHOLD,
    "min_n": MIN_N,
    "min_hits": MIN_HITS,
    "genres_compared": len(g),
    "genres_tpr_zero": int((g.tpr == 0).sum()),
    "tpr_gap": round(float(gap), 4),
    "tpr_by_genre": g.tpr.round(4).to_dict(),
    "passed": passed,
}
path = ROOT / "docs/fairness-report.json"
path.write_text(json.dumps(report, indent=2) + "\n")
print(f"wrote {path}")
sys.exit(0 if passed else 1)
