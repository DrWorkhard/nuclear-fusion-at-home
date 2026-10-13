"""Print v1 and v2 field-acceptance verdicts for saved coil fit/check run directories."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fusion_baselines.acceptance_v2 import evaluate  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path, help="run directories with result.json")
    args = parser.parse_args()
    print(json.dumps([evaluate(run) for run in args.runs], indent=1))
