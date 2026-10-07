"""Run the separately registered fixed-equilibrium phase/resolution check."""
import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reviewed-revision', required=True)
    args = parser.parse_args()
    if not all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS')):
        parser.error('set all four native thread limits to 1 before launching Python')
    origin = time.monotonic(), time.time()
    sys.modules['mpi4py'] = None
    sys.path.insert(0, str(ROOT/'src'))
    from fusion_baselines import joint_step_validation as validation

    result = validation.run(args.config.resolve(), args.output, args.reviewed_revision, origin)
    print(result['verdict'], flush=True)
    return 0 if result['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
