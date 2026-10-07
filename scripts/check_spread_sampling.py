"""One frozen spatial-sampling pilot; original case and evaluator stay unchanged."""

import time

START, WALL = time.monotonic(), time.time()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import shutil  # noqa: E402
import signal  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from fusion_public.data import load, load_case, require, validate_candidate  # noqa: E402
from fusion_public.dense import boundary_grid, load_input  # noqa: E402
from fusion_public.field import field, physical_curves  # noqa: E402

HELPER_SHA = 'dfc4e8cb750e28aa8d399f6c64691659674a874a1c2f1126133424d82b3cd15b'
CANDIDATES = (
    ('seed', 'examples/clear-coil-samples-v1/candidate.json'),
    ('headroom', 'submissions/length-headroom-six-coil/candidate.json'),
    ('counterexample', 'submissions/millimetre-ranking-counterexample/candidate.json'),
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def indices():
    return [64*j+i for j in range(2, 32, 4) for i in range(4, 64, 8)]


def metric(errors, weights, selected):
    total = sum(weights[i] for i in selected)
    require(total > 0, 'Positive area weight required')
    return math.sqrt(sum(weights[i]*errors[i]**2 for i in selected)/total)


def clean(revision):
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    require(head == revision and not dirty.strip(), 'Exact clean committed revision required')


def source_paths():
    return [Path(__file__), ROOT/'docs/optimization/ISSUE8_SPREAD_SAMPLING.md',
            ROOT/'evidence/plasma-design-v2/reference-input-401.json',
            *sorted((ROOT/'src/fusion_public').glob('*.py')),
            *sorted((ROOT/'examples/clear-coil-samples-v1').glob('*.json')),
            *(ROOT/name for _, name in CANDIDATES), Path(sys.executable)]


def worker(output, revision):
    output.mkdir(exist_ok=False)
    clean(revision)
    sources = {str(p): digest(p) for p in source_paths()}
    report = dict(completed=False, revision=revision, python=sys.version,
                  sources_before=sources, candidates=[], physical_admission=False)

    def guard():
        elapsed, wall = time.monotonic()-START, time.time()-WALL
        require(max(elapsed, wall) < 300 and abs(elapsed-wall) <= 5, 'Driver time limit')
        require(shutil.disk_usage(output).free >= 2*1024**3, 'Live disk reserve')
        require(sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
                < 31*1024**2, 'Driver storage limit')

    def save(name, value):
        guard()
        raw = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
        require(sum(p.stat().st_size for p in output.rglob('*') if p.is_file())+len(raw)
                < 31*1024**2, 'Output write exceeds driver limit')
        with (output/name).open('xb') as stream:
            stream.write(raw)
        guard()

    try:
        case, case_sha = load_case()
        points, normals, weights = boundary_grid(load_input(case))
        sparse, spread = case['groups']['boundary']['indices'], indices()
        require(len(set(spread)) == 64, 'Distinct spread points required')
        report.update(case_sha256=case_sha, sparse_indices=sparse, spread_indices=spread)
        save('geometry.json', dict(points_m=points, unit_normals=normals, weights=weights))
        for name, relative in CANDIDATES:
            candidate = validate_candidate(load(ROOT/relative))
            row = dict(name=name, path=relative, candidate_sha256=digest(ROOT/relative), levels=[])
            for count in (256, 512):
                curves = physical_curves(candidate, case, count)
                magnetic = []
                for start in range(0, len(points), 128):
                    guard()
                    magnetic.extend(field(points[start:start+128], curves)['B_T'])
                    guard()
                errors = []
                for b, n in zip(magnetic, normals, strict=True):
                    norm = math.sqrt(sum(x*x for x in b))
                    require(norm > 0, 'Nonzero boundary field required')
                    errors.append(sum(x*y for x, y in zip(b, n, strict=True))/norm)
                level = dict(ncoil=count, dense_rms=metric(errors, weights, range(4096)),
                             sparse_rms=metric(errors, weights, sparse),
                             spread_rms=metric(errors, weights, spread))
                for kind in ('sparse', 'spread'):
                    level[kind+'_relative_error'] = abs(level[kind+'_rms']/level['dense_rms']-1)
                save(f'{name}-{count}.json', dict(**level, B_T=magnetic, normal_errors=errors))
                row['levels'].append(level)
            row['max_quadrature_relative_change'] = max(
                abs(row['levels'][0][key]/row['levels'][1][key]-1)
                for key in ('dense_rms', 'sparse_rms', 'spread_rms'))
            report['candidates'].append(row)
            save(f'{name}-complete.json', row)
        headroom, counter = [row['levels'][-1] for row in report['candidates'][1:]]
        checks = dict(
            quadrature=all(row['max_quadrature_relative_change'] <= .001
                           for row in report['candidates']),
            spread_accuracy=all(row['levels'][-1]['spread_relative_error'] <= .05
                                for row in report['candidates']),
            improves_error=all(row['levels'][-1]['spread_relative_error']
                               < row['levels'][-1]['sparse_relative_error']
                               for row in report['candidates']),
            dense_counterexample=counter['dense_rms'] > headroom['dense_rms'],
            legacy_counterexample=counter['sparse_rms'] < headroom['sparse_rms'],
            spread_counterexample=counter['spread_rms'] > headroom['spread_rms'],
        )
        report.update(checks=checks, promote_to_case_work=all(checks.values()))
        report['sources_after'] = {p: digest(p) for p in sources}
        require(report['sources_after'] == sources, 'Source/input identity changed')
        clean(revision)
        guard()
        report['completed'] = True
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'[:1024]
    report.update(elapsed_s=time.monotonic()-START, wall_elapsed_s=time.time()-WALL)
    # Retain a failure record even after a driver guard fails; outer watchdog remains active.
    raw = (json.dumps(report, indent=2, allow_nan=False)+'\n').encode()
    require(sum(p.stat().st_size for p in output.rglob('*') if p.is_file())+len(raw)
            < 32*1024**2-128*1024, 'Failure report exceeds reserved space')
    (output/'result.json').write_bytes(raw)
    if report['completed']:
        guard()
    return 0 if report['completed'] else 1


def supervise(output, revision, helper):
    require(digest(helper) == HELPER_SHA, 'Exact reviewed supervisor required')
    spec = importlib.util.spec_from_file_location('reviewed_supervisor', helper)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    supervisor.ROOT, supervisor.START, supervisor.WALL = ROOT, START, WALL
    supervisor.MAX_BYTES = 32*1024**2
    clean(revision)
    require(shutil.disk_usage(output.parent).free >= 3*1024**3, 'Initial disk reserve')
    output.mkdir(exist_ok=False)
    sources = {str(p): digest(p) for p in [*source_paths(), helper]}
    receipt = dict(completed=False, revision=revision, sources_before=sources,
                   physical_admission=False, python=sys.version)
    terminated = [False]

    def stop_requested(signum, frame):
        terminated[0] = True

    def guard():
        require(not terminated[0], 'Termination requested')
        require(max(time.monotonic()-START, time.time()-WALL) < 360, '360 s outer limit')
        supervisor.guard(output)

    prior = signal.signal(signal.SIGTERM, stop_requested)
    try:
        command = [sys.executable, '-I', '-S', '-B', str(Path(__file__)), '--worker',
                   '--output', str(output/'run'), '--revision', revision]
        environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', TMPDIR='/private/tmp',
                           OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                           VECLIB_MAXIMUM_THREADS='1', MKL_NUM_THREADS='1')
        receipt['command'] = command
        (output/'start.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
        supervisor.supervise(command, environment, output, receipt, guard)
        report = json.loads((output/'run/result.json').read_bytes())
        require(report['completed'], 'Diagnostic did not complete')
        receipt['sources_after'] = {p: digest(p) for p in sources}
        require(receipt['sources_after'] == sources, 'Source/input identity changed')
        clean(revision)
        guard()
        receipt.update(completed=True, promote_to_case_work=report['promote_to_case_work'])
    except Exception as error:
        receipt['error'] = f'{type(error).__name__}: {error}'[:1024]
    finally:
        try:
            receipt = supervisor.finish_receipt(output, receipt, guard)
        finally:
            signal.signal(signal.SIGTERM, prior)
    print(json.dumps({k: v for k, v in receipt.items()
                      if k not in ('sources_before', 'sources_after', 'command')}, indent=2))
    return 0 if receipt['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--supervisor', type=Path)
    args = parser.parse_args()
    if args.worker:
        raise SystemExit(worker(args.output.resolve(), args.revision))
    require(args.supervisor is not None, 'Reviewed supervisor path required')
    raise SystemExit(supervise(args.output.resolve(), args.revision, args.supervisor.resolve()))
