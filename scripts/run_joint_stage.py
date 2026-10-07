"""Internal native operation worker; launched only by the reviewed joint parent."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.modules['mpi4py'] = None
sys.path.insert(0, str(ROOT/'src'))

from fusion_baselines.joint_native import NATIVE_PACKAGES, solver, worker  # noqa: E402

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--request', type=Path)
    mode.add_argument('--describe-native', type=Path)
    args = parser.parse_args()
    if args.describe_native:
        if args.describe_native.exists():
            raise FileExistsError('fresh environment inventory required')
        solver.save(args.describe_native, solver.identity(NATIVE_PACKAGES))
    else:
        raise SystemExit(worker(args.request))
