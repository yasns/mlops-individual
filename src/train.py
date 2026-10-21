"""Train the Spotify hit-prediction model with MLflow tracking.

python src/train.py                    # hyper-parameters from params.yaml
python src/train.py --C 0.1            # override one of them
dvc repro                              # via the pipeline: records hashes in dvc.lock, produces an MLflow run
"""

import argparse
import os
import subprocess
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=8", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def dvc_md5(dvc_file: Path) -> str:
    """md5 of the raw dataset as recorded by `dvc add` - the join key to dvc.lock."""
    try:
        return yaml.safe_load(dvc_file.read_text())["outs"][0]["md5"]
    except Exception:
        return "untracked"


def main() -> None:
    params = yaml.safe_load((ROOT / "params.yaml").read_text())["train"]
    parser = argparse.ArgumentParser()
    for key, value in params.items():
        parser.add_argument(f"--{key}", type=type(value))
    for key, value in vars(parser.parse_args()).items():
        if value is not None:
            params[key] = value

    mlflow.set_experiment(os.environ.get("MLFLOW_EXPERIMENT_NAME", "spotify-hits"))

    train = pd.read_csv(ROOT / "data/processed/train.csv")
    test = pd.read_csv(ROOT / "data/processed/test.csv")
    x_train, y_train = train.drop("target", axis=1), train["target"]
    x_test, y_test = test.drop("target", axis=1), test["target"]

    run_name = f"logreg-C{params['C']}"
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)  # config
        mlflow.set_tags(
            {  # identities
                "git_commit": git_commit(),
                "dvc_raw_md5": dvc_md5(ROOT / "data/raw/data.parquet.dvc"),
                "model_family": "LogisticRegression",
            }
        )
        mlflow.log_input(  # data provenance (name + digest)
            mlflow.data.from_pandas(
                train, source="data/processed/train.csv", targets="target", name="train"
            ),
            context="training",
        )

        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(C=params["C"], max_iter=params["max_iter"]),
        )
        model.fit(x_train, y_train)
        preds = model.predict(x_test)
        metrics = {
            "accuracy": accuracy_score(y_test, preds),
            "f1": f1_score(y_test, preds, average="weighted"),
            "precision": precision_score(y_test, preds),
            "recall": recall_score(y_test, preds),
        }

        info = mlflow.sklearn.log_model(  # model + environment files
            model,
            name="model",
            input_example=x_train.head(3),
        )
        mlflow.log_metrics(metrics, model_id=info.model_id)  # metric <-> model link

        os.makedirs(ROOT / "models", exist_ok=True)
        joblib.dump(
            model, ROOT / "models/model.pkl"
        )  # DVC-tracked artefact for later weeks
        (ROOT / "models/run_id.txt").write_text(run.info.run_id + "\n")
        print(
            f"run_id={run.info.run_id} model_id={info.model_id} accuracy={metrics['accuracy']:.4f} f1={metrics['f1']:.4f}"
        )


if __name__ == "__main__":
    main()
