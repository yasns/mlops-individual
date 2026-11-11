"""Inference API: loads MODEL_URI (models:/spotify-hits@champion) from the cluster MLflow at start-up.

MLFLOW_TRACKING_URI=http://127.0.0.1:5000 uvicorn src.serve:app --port 8000
"""

import os

import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException
from mlflow import MlflowClient

MODEL_URI = os.environ.get("MODEL_URI", "models:/spotify-hits@champion")
model = mlflow.pyfunc.load_model(MODEL_URI)  # pyfunc enforces the logged signature
info = {"model_uri": MODEL_URI}
if MODEL_URI.startswith("models:/") and "@" in MODEL_URI:
    name, alias = MODEL_URI.removeprefix("models:/").split("@")
    mv = MlflowClient().get_model_version_by_alias(name, alias)
    info |= {"version": mv.version, "run_id": mv.run_id}

app = FastAPI()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", **info}


@app.post("/predict")
def predict(rows: list[dict]) -> dict:
    try:
        preds = model.predict(pd.DataFrame(rows))
    except Exception as exc:  # missing / mistyped columns
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"predictions": [int(p) for p in preds], "version": info.get("version")}
