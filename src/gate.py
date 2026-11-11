"""Quality gate: exit 1 unless every metric in params.yaml `gate` meets its minimum in metrics.json."""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def check(metrics: dict, gate: dict) -> list[str]:
    return [f"{k}={metrics[k]:.4f} < {v}" for k, v in gate.items() if metrics[k] < v]


if __name__ == "__main__":
    gate = yaml.safe_load((ROOT / "params.yaml").read_text())["gate"]
    metrics = json.loads((ROOT / "metrics.json").read_text())
    failed = check(metrics, gate)
    print(f"GATE FAIL: {'; '.join(failed)}" if failed else f"GATE PASS: {metrics}")
    sys.exit(1 if failed else 0)
