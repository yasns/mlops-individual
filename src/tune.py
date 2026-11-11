"""Optuna search over C: one parent run, one nested run per trial.

python src/tune.py              # 10 trials
N_TRIALS=20 python src/tune.py
Copy the printed best C into params.yaml, then `dvc repro`.
"""

import os

import mlflow
import optuna
import pandas as pd
import yaml
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

from train import ROOT, build_model, git_commit


def main() -> None:
    cfg = yaml.safe_load((ROOT / "params.yaml").read_text())
    seed, max_iter = cfg["data"]["seed"], cfg["train"]["max_iter"]
    n_trials = int(os.environ.get("N_TRIALS", "10"))

    train = pd.read_csv(ROOT / "data/processed/train.csv")
    # validation split from train only, test used for the final metrics
    fit, val = train_test_split(train, test_size=0.2, random_state=seed, stratify=train["target"])
    x_fit, y_fit = fit.drop("target", axis=1), fit["target"]
    x_val, y_val = val.drop("target", axis=1), val["target"]

    mlflow.set_experiment(os.environ.get("MLFLOW_EXPERIMENT_NAME", "spotify-hits"))
    with mlflow.start_run(run_name="optuna-C", log_system_metrics=True):
        mlflow.set_tags({"git_commit": git_commit(), "seed": seed, "hpo": "optuna"})
        mlflow.log_params({"n_trials": n_trials, "max_iter": max_iter})
        mlflow.log_input(
            mlflow.data.from_pandas(train, source="data/processed/train.csv", targets="target", name="train"),
            context="tuning",
        )

        def objective(trial: optuna.Trial) -> float:
            C = trial.suggest_float("C", 1e-4, 10.0, log=True)
            with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
                mlflow.log_params({"C": C, "max_iter": max_iter})
                preds = build_model(C, max_iter, seed).fit(x_fit, y_fit).predict(x_val)
                score = f1_score(y_val, preds, average="weighted")
                mlflow.log_metric("val_f1", score)
            return score

        study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
        study.optimize(
            objective,
            n_trials=n_trials,
            callbacks=[lambda s, t: mlflow.log_metric("best_val_f1", s.best_value, step=t.number)],
        )
        mlflow.log_params({"best_C": study.best_params["C"]})
        mlflow.log_metric("best_val_f1", study.best_value)
        print(f"best C={study.best_params['C']:.6g} val_f1={study.best_value:.4f}")


if __name__ == "__main__":
    main()
