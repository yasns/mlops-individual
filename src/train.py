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

# defaults are 10 s, batches of 10. our runs are shorter than that
mlflow.set_system_metrics_sampling_interval(1)
mlflow.set_system_metrics_samples_before_logging(1)


def git_commit() -> str:
    if "GIT_COMMIT" in os.environ:
        return os.environ["GIT_COMMIT"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=8", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):  # no git / no .git in the image
        return "unknown"


def dvc_md5(dvc_file: Path) -> str:
    """md5 of the raw dataset as recorded by `dvc add` - the join key to dvc.lock."""
    try:
        return yaml.safe_load(dvc_file.read_text())["outs"][0]["md5"]
    except (OSError, KeyError, TypeError):
        return "untracked"


def build_model(C: float, max_iter: int, seed: int):
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(C=C, max_iter=max_iter, random_state=seed),
    )


def main() -> None:
    cfg = yaml.safe_load((ROOT / "params.yaml").read_text())
    params, seed = cfg["train"], cfg["data"]["seed"]
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
    with mlflow.start_run(run_name=run_name, log_system_metrics=True) as run:
        mlflow.log_params(params)  # config
        mlflow.set_tags(
            {  # identities
                "git_commit": git_commit(),
                "dvc_raw_md5": dvc_md5(ROOT / "data/raw/data.parquet.dvc"),
                "model_family": "LogisticRegression",
                "seed": seed,
            }
        )
        mlflow.log_input(  # data provenance (name + digest)
            mlflow.data.from_pandas(
                train, source="data/processed/train.csv", targets="target", name="train"
            ),
            context="training",
        )

        # learning curve: step = training rows seen
        for frac in (0.1, 0.25, 0.5, 0.75):
            n = int(len(train) * frac)
            m = build_model(params["C"], params["max_iter"], seed).fit(x_train[:n], y_train[:n])
            mlflow.log_metric("test_f1", f1_score(y_test, m.predict(x_test), average="weighted"), step=n)

        model = build_model(params["C"], params["max_iter"], seed)
        model.fit(x_train, y_train)
        preds = model.predict(x_test)
        metrics = {
            "accuracy": accuracy_score(y_test, preds),
            "f1": f1_score(y_test, preds, average="weighted"),
            "precision": precision_score(y_test, preds, zero_division=0),
            "recall": recall_score(y_test, preds),
        }
        mlflow.log_metric("test_f1", metrics["f1"], step=len(train))

        info = mlflow.sklearn.log_model(  # model + environment files
            model,
            name="model",
            input_example=x_train.head(3),
        )
        mlflow.log_metrics(metrics, model_id=info.model_id)  # metric <-> model link

        os.makedirs(ROOT / "models", exist_ok=True)
        joblib.dump(
            model, ROOT / "models/model.pkl"
        )
        (ROOT / "models/run_id.txt").write_text(run.info.run_id + "\n")
        print(
            f"run_id={run.info.run_id} model_id={info.model_id} accuracy={metrics['accuracy']:.4f} f1={metrics['f1']:.4f}"
        )


if __name__ == "__main__":
    main()
