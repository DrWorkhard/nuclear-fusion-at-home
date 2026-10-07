"""Worker and environment inventory for the separately supervised joint-target solve."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from fusion_baselines.joint_equilibrium import identity, save, worker  # noqa: E402

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--request', type=Path)
    mode.add_argument('--describe', type=Path)
    args = parser.parse_args()
    if args.describe:
        if args.describe.exists():
            raise FileExistsError('fresh environment inventory required')
        save(args.describe, identity())
    else:
        raise SystemExit(worker(args.request))
