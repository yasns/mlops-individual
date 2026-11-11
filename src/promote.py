"""Model Registry: register a run's model and point @champion at it, or roll @champion back.

python src/promote.py [run_id]     # default run id: models/run_id.txt
python src/promote.py rollback     # @champion -> previous version
"""

import sys
from pathlib import Path

import mlflow
from mlflow import MlflowClient

NAME = "spotify-hits"
ROOT = Path(__file__).resolve().parents[1]


def promote(run_id: str) -> None:
    mv = mlflow.register_model(f"runs:/{run_id}/model", NAME)
    MlflowClient().set_registered_model_alias(NAME, "champion", mv.version)
    print(f"{NAME} v{mv.version} (run {run_id}) -> @champion")


def rollback() -> None:
    client = MlflowClient()
    current = int(client.get_model_version_by_alias(NAME, "champion").version)
    older = [int(v.version) for v in client.search_model_versions(f"name='{NAME}'") if int(v.version) < current]
    if not older:
        sys.exit(f"v{current} is the oldest version, nothing to roll back to")
    client.set_registered_model_alias(NAME, "champion", max(older))
    print(f"{NAME} @champion: v{current} -> v{max(older)}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else (ROOT / "models/run_id.txt").read_text().strip()
    rollback() if arg == "rollback" else promote(arg)
