"""Score the registered plasma targets with ConStellaration's frozen forward model (#76).

Runs only in a separate environment with constellaration==0.2.6, never the native one:

    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
      <venv>/bin/python scripts/constellaration_metrics.py --output <new-dir> [--confirm]

Each VMEC++ input JSON is converted to ConStellaration's SurfaceRZFourier, the
conversion is checked against the original geometry, and the default high-fidelity
forward model is evaluated once per target. Benchmark feasibility and scores use the
problem classes' own methods on those metrics; --confirm also calls each problem's
public evaluate() on the saved boundary JSON. Writes report.json and Wout files.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import shutil
import signal
import sys
import time
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {  # must match coil_check.TARGETS; checked below without importing it
    "reference401": ("evidence/plasma-design-v2/reference-input-401.json",
                     "57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f"),
    "selected401": ("evidence/plasma-balanced-v1/selected-input-401.json",
                    "6bec3483eaced499bafe7ee94b16aa960d219ec1fec86cc0690012f8ebdb033e"),
}
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS")
PACKAGES = ("constellaration", "vmecpp", "booz-xform", "simsopt", "desc-opt", "jax",
            "jaxlib", "numpy", "scipy", "pymoo", "netCDF4")
BUDGET_S, RESERVE = 1800, 3 * 1024**3
RULE = 0.05  # issue #76: relative L∇B change that counts as measurable


def need(condition, message):
    if not condition:
        raise ValueError(message)


def load(target_id):
    """Verify the input against the registered hash and return its parsed JSON."""
    relative, sha = TARGETS[target_id]
    registry = (ROOT/"src/fusion_baselines/coil_check.py").read_text(encoding="utf-8")
    need(relative in registry and sha in registry, "input not registered in coil_check")
    data = (ROOT/relative).read_bytes()
    need(hashlib.sha256(data).hexdigest() == sha, f"source identity changed: {relative}")
    return relative, sha, json.loads(data)


def convert(path, data):
    """VMEC++ input -> SurfaceRZFourier. Both use cos/sin(m theta - n nfp phi)."""
    import vmecpp
    from constellaration.geometry import surface_rz_fourier as srf

    need(not data["lasym"] and data["rbs"] is None and data["zbc"] is None,
         "stellarator-symmetric boundary required")
    entries = data["rbc"] + data["zbs"]
    mpol = 1 + max(e["m"] for e in entries)
    ntor = max(abs(e["n"]) for e in entries)
    arrays = {}
    for key in ("rbc", "zbs"):
        arrays[key] = np.zeros((mpol, 2*ntor + 1))
        for e in data[key]:
            need(arrays[key][e["m"], e["n"] + ntor] == 0.0, "duplicate coefficient")
            arrays[key][e["m"], e["n"] + ntor] = e["value"]
    r00 = arrays["rbc"][0, ntor]
    scale = 1.0/r00  # ConStellaration boundaries are normalized to R00 = 1
    surface = srf.SurfaceRZFourier(
        r_cos=arrays["rbc"]*scale, z_sin=arrays["zbs"]*scale,
        n_field_periods=int(data["nfp"]), is_stellarator_symmetric=True)
    # Cross-check against VMEC++'s own reader of the same file.
    indata = vmecpp.VmecInput.from_file(path)
    parser = max(
        float(np.max(np.abs(vmecpp.VmecInput.resize_2d_coeff(
            arrays[key], indata.mpol, indata.ntor) - getattr(indata, key))))
        for key in ("rbc", "zbs"))
    info = dict(mpol=mpol, ntor=ntor, n_field_periods=int(data["nfp"]), R00=r00,
                scale=scale, max_abs_difference_to_vmecpp_reader=parser)
    return surface, info


def direct_rz(data, theta, phi, flip=False):
    """Boundary R, Z straight from the JSON entries (VMEC convention)."""
    theta = -theta if flip else theta
    r = sum(e["value"]*np.cos(e["m"]*theta - e["n"]*data["nfp"]*phi) for e in data["rbc"])
    z = sum(e["value"]*np.sin(e["m"]*theta - e["n"]*data["nfp"]*phi) for e in data["zbs"])
    return r, z


def geometry_check(data, surface, info, wout):
    """Max |ΔR|, |ΔZ| (in input units) on a full-torus 64×128 grid."""
    from constellaration.geometry import surface_rz_fourier as srf

    theta, phi = np.meshgrid(np.linspace(0, 2*np.pi, 64, endpoint=False),
                             np.linspace(0, 2*np.pi, 128, endpoint=False), indexing="ij")
    r0, z0 = direct_rz(data, theta, phi)
    rz = srf.evaluate_points_rz(surface, np.stack([theta, phi], axis=-1))/info["scale"]
    angle = (wout.xm[:, None, None]*theta - wout.xn[:, None, None]*phi)
    rw = np.einsum("k,kij->ij", wout.rmnc[:, -1], np.cos(angle))/info["scale"]
    zw = np.einsum("k,kij->ij", wout.zmns[:, -1], np.sin(angle))/info["scale"]
    dr, dz = np.abs(rz[..., 0]-r0), np.abs(rz[..., 1]-z0)
    need(np.isfinite(dr).all() and np.isfinite(dz).all(),
         "non-finite geometry residual: surface versus input")
    result = dict(grid=[64, 128], surface_vs_input=float(max(dr.max(), dz.max())))
    for label, flip in (("vmec_boundary_vs_input", False),
                        ("vmec_boundary_vs_input_theta_flipped", True)):
        r1, z1 = direct_rz(data, theta, phi, flip)
        dr, dz = np.abs(rw-r1), np.abs(zw-z1)
        need(np.isfinite(dr).all() and np.isfinite(dz).all(),
             f"non-finite geometry residual: {label}")
        result[label] = float(max(dr.max(), dz.max()))
    return result


def benchmarks(metrics):
    """Feasibility and score of one design for the three benchmark problems."""
    from constellaration import problems

    out = {}
    for name, problem in (("geometrical", problems.GeometricalProblem()),
                          ("simple_to_build_qi", problems.SimpleToBuildQIStellarator())):
        feasible = problem.is_feasible(metrics)
        out[name] = dict(
            objective=problem.get_objective(metrics)[0], feasible=feasible,
            feasibility=problem.compute_feasibility(metrics),
            score=float(problem._score(metrics)) if feasible else 0.0,
            normalized_violations=problem._normalized_constraint_violations(metrics).tolist())
    problem = problems.MHDStableQIStellarator()
    out["mhd_stable_qi"] = dict(
        objectives=[v for v, _ in problem.get_objectives(metrics)],
        feasible=problem.is_feasible(metrics),
        feasibility=problem.compute_feasibility(metrics),
        score_as_single_design_set=float(problem._score([metrics])),
        normalized_violations=problem._normalized_constraint_violations(metrics).tolist())
    return out


def leaderboard_path(path):
    """Each problem's public evaluate() on the saved boundary JSON; reruns the model."""
    from constellaration import problems
    from constellaration.geometry import surface_rz_fourier as srf

    surface = srf.SurfaceRZFourier.model_validate_json(path.read_text(encoding="utf-8"))
    return dict(
        geometrical=problems.GeometricalProblem().evaluate(surface).model_dump(),
        simple_to_build_qi=problems.SimpleToBuildQIStellarator().evaluate(surface).model_dump(),
        mhd_stable_qi=problems.MHDStableQIStellarator().evaluate([surface]).model_dump())


def evaluate(target_id, output, confirm=False):
    from constellaration import forward_model

    relative, sha, data = load(target_id)
    record = dict(input=relative, input_sha256=sha, completed=False)
    try:
        surface, record["conversion"] = convert(ROOT/relative, data)
        (output/f"boundary_{target_id}.json").write_text(
            surface.model_dump_json(), encoding="utf-8")
        settings = forward_model.ConstellarationSettings.default_high_fidelity()
        try:
            record["settings"] = json.loads(settings.model_dump_json())
        except Exception:
            record["settings"] = repr(settings)
        started = time.monotonic()
        metrics, wout = forward_model.forward_model(surface, settings=settings)
        record["forward_model_seconds"] = time.monotonic() - started
        record["metrics"] = metrics.model_dump()
        record["vmec"] = {k: np.asarray(getattr(wout, k, np.nan)).item() for k in (
            "ns", "mpol", "ntor", "fsqr", "fsqz", "fsql", "ier_flag", "aspect", "Aminor_p",
            "Rmajor_p")}
        record["geometry_check"] = geometry_check(data, surface, record["conversion"], wout)
        record["benchmarks"] = benchmarks(metrics)
        if confirm:
            started = time.monotonic()
            record["evaluate_calls"] = leaderboard_path(output/f"boundary_{target_id}.json")
            record["evaluate_calls_seconds"] = time.monotonic() - started
        try:
            wout.save(str(output/f"wout_{target_id}.nc"))
        except Exception as error:  # retention is optional, the metrics are not
            record["wout_save_error"] = repr(error)
        record["completed"] = True
    except Exception:
        record["error"] = traceback.format_exc()
    return record


def rule(reference, selected):
    change = (selected - reference)/reference
    if change < -RULE:
        outcome = "cost: Step 3 gain costs coil simplicity by this proxy"
    elif change > RULE:
        outcome = "gain"
    else:
        outcome = "no measurable cost"
    return dict(relative_change=change, outcome=outcome)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true",
                        help="also call each problem's evaluate() (three more model runs)")
    args = parser.parse_args()
    need(all(os.environ.get(k) == "1" for k in THREADS), "one-thread execution required")
    args.output.mkdir(parents=True, exist_ok=False)
    need(shutil.disk_usage(args.output).free >= RESERVE, "3 GiB disk reserve required")

    def expire(*_):
        raise TimeoutError("30-minute compute budget exhausted")

    signal.signal(signal.SIGALRM, expire)
    signal.alarm(BUDGET_S)
    started = time.monotonic()
    report = dict(kind="constellaration-metrics-issue76", python=sys.version,
                  platform=platform.platform(), machine=platform.machine(),
                  threads={k: os.environ.get(k) for k in (*THREADS, "XLA_FLAGS")},
                  versions={}, targets={})
    for name in PACKAGES:
        try:
            report["versions"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            report["versions"][name] = None
    for target_id in TARGETS:
        if time.monotonic() - started >= BUDGET_S:
            report["targets"][target_id] = dict(completed=False, error="budget exhausted")
            continue
        report["targets"][target_id] = evaluate(target_id, args.output, args.confirm)
        print(json.dumps({target_id: report["targets"][target_id].get("metrics")}), flush=True)
    signal.alarm(0)
    done = [report["targets"][t].get("metrics") for t in TARGETS]
    if all(done):
        key = "minimum_normalized_magnetic_gradient_scale_length"
        report["rule"] = rule(done[0][key], done[1][key])
    report["wall_seconds"] = time.monotonic() - started
    report["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["free_disk_bytes_after"] = shutil.disk_usage(args.output).free
    (args.output/"report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report.get("rule")), flush=True)
    return 0 if all(done) else 1


if __name__ == "__main__":
    raise SystemExit(main())
