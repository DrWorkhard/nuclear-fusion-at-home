"""Run the fixed joint feasibility comparison from a reviewed, frozen configuration."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True,
                        help='JSON with the exact joint_native.Operations constructor fields')
    parser.add_argument('--output', type=Path, required=True, help='fresh output directory')
    parser.add_argument('--reviewed-revision', required=True,
                        help='full reviewed implementation commit; must equal config revision')
    args = parser.parse_args()
    if not all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS')):
        parser.error('set all four native thread limits to 1 before launching Python')
    sys.modules['mpi4py'] = None
    sys.path.insert(0, str(ROOT/'src'))
    from fusion_baselines import joint_native as native

    config = native.solver.read(args.config)
    if config['revision'] != args.reviewed_revision or len(args.reviewed_revision) != 40:
        parser.error('configuration must name the exact reviewed implementation commit')
    result = native.schedule.run(native.Operations(**config), args.output.resolve())
    print(result['verdict'], flush=True)
    return 0 if result['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
