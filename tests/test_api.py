import importlib

import mlflow.sklearn
import pandas as pd
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression


def test_health_and_predict(tmp_path, monkeypatch):
    x = pd.DataFrame({"danceability": [0.1, 0.9, 0.2, 0.8], "explicit": [0, 1, 0, 1]})
    model = LogisticRegression().fit(x, [0, 1, 0, 1])
    mlflow.sklearn.save_model(model, tmp_path / "m", input_example=x.head(2))
    monkeypatch.setenv("MODEL_URI", str(tmp_path / "m"))  # local model dir, no MLflow server in CI

    import serve

    client = TestClient(importlib.reload(serve).app)
    assert client.get("/health").json()["status"] == "ok"
    r = client.post("/predict", json=x.to_dict("records"))
    assert r.status_code == 200
    assert set(r.json()["predictions"]) <= {0, 1}
    assert client.post("/predict", json=[{"danceability": 0.5}]).status_code == 422
