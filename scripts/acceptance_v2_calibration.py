"""Reproduce the acceptance-v2 thresholds from the pinned public CoilStellaration split.

Needs pyarrow and numpy in a separate environment, e.g.
`uvx --with pyarrow --with numpy python scripts/acceptance_v2_calibration.py`.
"""

import hashlib
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

REVISION = "286a268c664938519af6ceacfb4ec8143f64e20e"
URL = ("https://huggingface.co/datasets/proxima-fusion/coilstellaration/resolve/"
       f"{REVISION}/results/eval-part-0.parquet")
SHA256 = "5425524969d6ae7f844195e00bae0ec313228aadb27d905549791f6251695a37"
MEAN, MAX = "desc_metrics/normalized_field_error/mean", "desc_metrics/normalized_field_error/max"

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "eval-part-0.parquet"
    urllib.request.urlretrieve(URL, path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SHA256, "unexpected file"
    table = pq.read_table(path, columns=[MEAN, MAX]).to_pandas().dropna()
mean, peak = table[MEAN].to_numpy(), table[MAX].to_numpy()


def joint(q):
    a, b = np.quantile(mean, q), np.quantile(peak, q)
    return a, b, float(np.mean((mean <= a) & (peak <= b)))


lo, hi = 0.10, 0.5  # common percentile for both statistics, joint pass fraction 10%
for _ in range(60):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if joint(mid)[2] < 0.10 else (lo, mid)
a, b, _ = joint(hi)
a, b = float(f"{a:.2g}"), float(f"{b:.2g}")
passing = int(np.sum((mean <= a) & (peak <= b)))
print(f"cases={len(mean)} common_percentile={hi:.4f} mean<={a} max<={b} "
      f"passing={passing} ({passing/len(mean):.2%})")
