"""Score VMEC++ boundaries with ConStellaration's frozen forward model (#112).

Runs only in a separate environment with constellaration==0.2.6, never the native one:

    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
      <venv>/bin/python scripts/constellaration_metrics.py --output <new-dir> [--confirm]

Use --input FILE --sha256 SHA256 [--target-id NAME] for a new boundary.
Without --input, replay both registered #76 targets. Only boundary geometry is used;
input pressure, current, flux and solver settings do not configure the forward model.

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
import math
import os
import platform
import re
import resource
import shutil
import signal
import sys
import time
import traceback
from pathlib import Path

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
PINNED_VERSION = "0.2.6"
GEOMETRY_RTOL = 1e-10  # coordinate differences / input R00; not a physics gate
RULE = 0.05  # issue #76: relative L∇B change that counts as measurable


def need(condition, message):
    if not condition:
        raise ValueError(message)


def load_input(path, sha):
    """Hash the exact bytes before parsing an explicitly identified boundary."""
    need(isinstance(sha, str) and re.fullmatch(r"[0-9a-fA-F]{64}", sha),
         "SHA-256 must contain exactly 64 hexadecimal characters")
    raw = Path(path).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == sha.lower(), f"source identity changed: {path}")
    data = json.loads(raw)
    validate_boundary(data)
    return data


def validate_boundary(data):
    """Validate named, finite stellarator-symmetric VMEC boundary coefficients."""
    need(isinstance(data, dict), "VMEC++ input must be a JSON object")
    need(data.get("lasym") is False and data.get("rbs") is None
         and data.get("zbc") is None, "stellarator-symmetric boundary required")
    need(type(data.get("nfp")) is int and data["nfp"] > 0, "nfp must be a positive integer")
    for key in ("rbc", "zbs"):
        entries = data.get(key)
        need(isinstance(entries, list) and entries, f"{key} must be a nonempty list")
        seen = set()
        for entry in entries:
            need(isinstance(entry, dict), f"invalid {key} coefficient")
            m, n, value = (entry.get(k) for k in ("m", "n", "value"))
            need(type(m) is int and m >= 0 and type(n) is int, "invalid mode indices")
            need((m, n) not in seen, f"duplicate {key} coefficient: {(m, n)}")
            seen.add((m, n))
            need(type(value) in (int, float) and math.isfinite(value),
                 "coefficient values must be finite numbers")
    r00 = next((e["value"] for e in data["rbc"] if (e["m"], e["n"]) == (0, 0)), None)
    need(r00 is not None and r00 > 0, "R00 must be finite and positive")


def load(target_id):
    """Verify the registered input without importing the native coil checker."""
    relative, sha = TARGETS[target_id]
    registry = (ROOT/"src/fusion_baselines/coil_check.py").read_text(encoding="utf-8")
    need(relative in registry and sha in registry, "input not registered in coil_check")
    return relative, sha, load_input(ROOT/relative, sha)


def convert(path, data):
    """VMEC++ input -> SurfaceRZFourier. Both use cos/sin(m theta - n nfp phi)."""
    import numpy as np
    import vmecpp
    from constellaration.geometry import surface_rz_fourier as srf

    validate_boundary(data)
    entries = data["rbc"] + data["zbs"]
    mpol = 1 + max(e["m"] for e in entries)
    ntor = max(abs(e["n"]) for e in entries)
    arrays = {}
    for key in ("rbc", "zbs"):
        arrays[key] = np.zeros((mpol, 2*ntor + 1))
        for e in data[key]:
            arrays[key][e["m"], e["n"] + ntor] = e["value"]
    r00 = arrays["rbc"][0, ntor]
    scale = 1.0/r00  # ConStellaration boundaries are normalized to R00 = 1
    surface = srf.SurfaceRZFourier(
        r_cos=arrays["rbc"]*scale, z_sin=arrays["zbs"]*scale,
        n_field_periods=int(data["nfp"]), is_stellarator_symmetric=True)
    # Cross-check against VMEC++'s own reader of the same file.
    indata = vmecpp.VmecInput.from_file(path)
    parser_errors = [float(np.max(np.abs(vmecpp.VmecInput.resize_2d_coeff(
        arrays[key], indata.mpol, indata.ntor) - getattr(indata, key))))
        for key in ("rbc", "zbs")]
    need(all(math.isfinite(error) for error in parser_errors),
         "non-finite coefficient conversion residual")
    parser = max(parser_errors)
    info = dict(mpol=mpol, ntor=ntor, n_field_periods=int(data["nfp"]), R00=r00,
                scale=scale, max_abs_difference_to_vmecpp_reader=parser)
    return surface, info


def direct_rz(data, theta, phi, flip=False):
    """Boundary R, Z straight from the JSON entries (VMEC convention)."""
    import numpy as np

    theta = -theta if flip else theta
    r = sum(e["value"]*np.cos(e["m"]*theta - e["n"]*data["nfp"]*phi) for e in data["rbc"])
    z = sum(e["value"]*np.sin(e["m"]*theta - e["n"]*data["nfp"]*phi) for e in data["zbs"])
    return r, z


def fourier_error_bound(data, m, k, r_cos, z_sin, scale):
    """Numerical full-torus coordinate bound for phase m*theta - k*phi.

    k is the physical toroidal mode: input n*nfp, but Wout xn already includes nfp.
    The coefficient L1 bound avoids sampled-grid aliasing; it is not interval arithmetic.
    """
    import numpy as np

    arrays = [np.asarray(value) for value in (m, k, r_cos, z_sin)]
    need(all(a.ndim == 1 and a.shape == arrays[0].shape for a in arrays),
         "Fourier mode and coefficient arrays must be matching vectors")
    need(all(np.isfinite(a).all() for a in arrays), "non-finite geometry residual: Fourier data")
    need(all(np.equal(a, np.rint(a)).all() for a in arrays[:2]),
         "Fourier mode indices must be integers")
    need(math.isfinite(scale) and scale > 0, "invalid boundary normalization")

    def collect(entries, sine):
        modes = {}
        for poloidal, toroidal, coefficient in entries:
            if coefficient == 0:
                continue
            poloidal, toroidal = int(poloidal), int(toroidal)
            if sine and poloidal == toroidal == 0:
                continue
            if poloidal < 0 or (poloidal == 0 and toroidal < 0):
                poloidal, toroidal = -poloidal, -toroidal
                if sine:
                    coefficient = -coefficient
            modes.setdefault((poloidal, toroidal), []).append(float(coefficient))
        return {mode: math.fsum(values) for mode, values in modes.items()}

    bounds = []
    for key, coefficients, sine in (("rbc", arrays[2], False), ("zbs", arrays[3], True)):
        original = collect(((e["m"], e["n"]*data["nfp"], e["value"])
                            for e in data[key]), sine)
        converted = collect(zip(arrays[0], arrays[1], coefficients/scale, strict=True), sine)
        bounds.append(math.fsum(abs(original.get(mode, 0.) - converted.get(mode, 0.))
                                for mode in original.keys() | converted.keys()))
    need(all(math.isfinite(bound) for bound in bounds), "non-finite geometry residual: bound")
    return max(bounds)


def geometry_check(data, surface, info, wout):
    """Max |ΔR|, |ΔZ| (in input units) on a full-torus 64×128 grid."""
    import numpy as np
    from constellaration.geometry import surface_rz_fourier as srf

    # Check the actual surface arrays and the outer Wout coefficients continuously.
    r_cos, z_sin = np.asarray(surface.r_cos), np.asarray(surface.z_sin)
    need(r_cos.ndim == 2 and r_cos.shape == z_sin.shape and r_cos.shape[1] % 2 == 1,
         "invalid surface Fourier coefficient shape")
    m, n = np.indices(r_cos.shape)
    k = (n - r_cos.shape[1]//2) * surface.n_field_periods
    surface_bound = fourier_error_bound(
        data, m.ravel(), k.ravel(), r_cos.ravel(), z_sin.ravel(), info["scale"])
    rmnc, zmns = np.asarray(wout.rmnc), np.asarray(wout.zmns)
    need(rmnc.ndim == 2 and rmnc.shape == zmns.shape and rmnc.shape[1] > 0,
         "invalid Wout Fourier coefficient shape")
    wout_bound = fourier_error_bound(
        data, wout.xm, wout.xn, rmnc[:, -1], zmns[:, -1], info["scale"])

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
    result = dict(grid=[64, 128], surface_vs_input=float(max(dr.max(), dz.max())),
                  surface_coefficient_bound=surface_bound,
                  vmec_boundary_coefficient_bound=wout_bound)
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


def check_geometry(conversion, geometry):
    """Reject incorrect conversion; the theta-flipped value is diagnostic only."""
    need(conversion["max_abs_difference_to_vmecpp_reader"] == 0.0,
         "coefficient conversion differs from VMEC++ reader")
    tolerance = GEOMETRY_RTOL * conversion["R00"]
    for key in ("surface_vs_input", "vmec_boundary_vs_input",
                "surface_coefficient_bound", "vmec_boundary_coefficient_bound"):
        value = geometry[key]
        need(math.isfinite(value) and value <= tolerance, f"geometry check failed: {key}")
    return dict(passed=True, absolute_tolerance=tolerance,
                relative_to_R00=GEOMETRY_RTOL)


def evaluate(target_id, output, confirm=False, source=None):
    record = dict(completed=False)
    wout = None
    try:
        import numpy as np
        from constellaration import forward_model

        if source is None:
            relative, sha = TARGETS[target_id]
            record.update(input=relative, input_sha256=sha)
            _, _, data = load(target_id)
            path = ROOT/relative
        else:
            path, sha = source
            record.update(input=str(path), input_sha256=sha.lower())
            data = load_input(path, sha)
        surface, record["conversion"] = convert(path, data)
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
        record["conversion_validation"] = check_geometry(
            record["conversion"], record["geometry_check"])
        record["benchmarks"] = benchmarks(metrics)
        if confirm:
            started = time.monotonic()
            record["evaluate_calls"] = leaderboard_path(output/f"boundary_{target_id}.json")
            record["evaluate_calls_seconds"] = time.monotonic() - started
        json.dumps(record, allow_nan=False)
        record["completed"] = True
    except Exception:
        record["error"] = traceback.format_exc()
    finally:
        if wout is not None:
            try:
                wout.save(str(output/f"wout_{target_id}.nc"))
            except Exception as error:  # retention must not erase a validation failure
                record["wout_save_error"] = repr(error)
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
    parser.add_argument("--input", type=Path, help="VMEC++ input JSON; boundary geometry only")
    parser.add_argument("--sha256", help="expected SHA-256 of the exact input bytes")
    parser.add_argument("--target-id", help="output name for --input (letters, digits, _ and -)")
    args = parser.parse_args()
    if (args.input is None) != (args.sha256 is None):
        parser.error("--input and --sha256 must be supplied together")
    if args.target_id and args.input is None:
        parser.error("--target-id requires --input")
    target_id = args.target_id or "custom"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", target_id):
        parser.error("invalid --target-id")
    need(importlib.metadata.version("constellaration") == PINNED_VERSION,
         f"constellaration=={PINNED_VERSION} required in a separate environment")
    need(all(os.environ.get(k) == "1" for k in THREADS), "one-thread execution required")
    args.output.mkdir(parents=True, exist_ok=False)
    need(shutil.disk_usage(args.output).free >= RESERVE, "3 GiB disk reserve required")

    def expire(*_):
        raise TimeoutError("30-minute compute budget exhausted")

    signal.signal(signal.SIGALRM, expire)
    signal.alarm(BUDGET_S)
    started = time.monotonic()
    kind = ("constellaration-metrics-custom-boundary" if args.input
            else "constellaration-metrics-issue76")
    report = dict(kind=kind, python=sys.version,
                  platform=platform.platform(), machine=platform.machine(),
                  threads={k: os.environ.get(k) for k in (*THREADS, "XLA_FLAGS")},
                  versions={}, targets={}, physical_admission=False,
                  geometry_relative_tolerance=GEOMETRY_RTOL,
                  boundary_only=True)
    targets = [target_id] if args.input is not None else list(TARGETS)
    for name in PACKAGES:
        try:
            report["versions"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            report["versions"][name] = None
    for target_id in targets:
        if time.monotonic() - started >= BUDGET_S:
            report["targets"][target_id] = dict(completed=False, error="budget exhausted")
            continue
        source = (args.input, args.sha256) if args.input is not None else None
        report["targets"][target_id] = evaluate(target_id, args.output, args.confirm, source)
        print(json.dumps({target_id: report["targets"][target_id].get("metrics")}), flush=True)
    signal.alarm(0)
    done = all(report["targets"][t].get("completed") for t in targets)
    if done and args.input is None:
        key = "minimum_normalized_magnetic_gradient_scale_length"
        report["rule"] = rule(*(report["targets"][t]["metrics"][key] for t in targets))
    report["wall_seconds"] = time.monotonic() - started
    report["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["free_disk_bytes_after"] = shutil.disk_usage(args.output).free
    (args.output/"report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report.get("rule")), flush=True)
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
