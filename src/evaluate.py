"""
Evaluate models/model.pkl on the test split -> metrics.json
MLflow metrics logged by train.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    model = joblib.load(ROOT / "models/model.pkl")
    test = pd.read_csv(ROOT / "data/processed/test.csv")
    x, y = test.drop("target", axis=1), test["target"]
    preds = model.predict(x)
    metrics = {
        "accuracy": accuracy_score(y, preds),
        "f1": f1_score(y, preds, average="weighted"),
        "precision": precision_score(y, preds),
        "recall": recall_score(y, preds),
    }
    (ROOT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
