"""Load test /predict with rows from test.csv -> latency percentiles + throughput in docs/load-test.json.

python scripts/loadtest.py http://127.0.0.1:8000 [requests=200] [concurrency=10]
"""

import json
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
url = sys.argv[1].rstrip("/")
n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
workers = int(sys.argv[3]) if len(sys.argv) > 3 else 10

rows = pd.read_csv(ROOT / "data/processed/test.csv").drop(columns="target").head(n).to_dict("records")


def call(row: dict) -> float:
    req = urllib.request.Request(
        f"{url}/predict", json.dumps([row]).encode(), {"Content-Type": "application/json"}
    )
    start = time.perf_counter()
    urllib.request.urlopen(req, timeout=10).read()  # raises on non-2xx
    return (time.perf_counter() - start) * 1000


t0 = time.perf_counter()
with ThreadPoolExecutor(workers) as pool:
    lat = list(pool.map(call, rows))
elapsed = time.perf_counter() - t0

q = statistics.quantiles(lat, n=100)
result = {
    "requests": len(lat),
    "concurrency": workers,
    "p50_ms": round(q[49], 1),
    "p95_ms": round(q[94], 1),
    "p99_ms": round(q[98], 1),
    "throughput_rps": round(len(lat) / elapsed, 1),
    "url": url,
    "date": time.strftime("%Y-%m-%d %H:%M"),
}
(ROOT / "docs/load-test.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
