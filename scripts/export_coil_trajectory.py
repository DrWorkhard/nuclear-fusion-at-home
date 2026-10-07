"""Export existing fitter records without NumPy, SIMSOPT, VMEC or network access."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from fusion_baselines.coil_trajectory import export  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="closed fitter output directory")
    parser.add_argument("--output", type=Path, required=True, help="fresh JSONL path")
    parser.add_argument("--artifact-base",
                        help="immutable URI for this run; recorded, never fetched")
    parser.add_argument("--max-mib", type=int, default=64, help="output ceiling, 1–256 MiB")
    args = parser.parse_args()
    try:
        print(json.dumps(export(args.run, args.output, args.artifact_base, args.max_mib*1024**2)))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")


if __name__ == "__main__":
    main()
