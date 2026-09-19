"""Fresh-process synthetic CP equivalence/resource qualification; no fields/targets.

The registered full matrix is deliberately available only through the explicit
``--raw ABS_FRESH_DIRECTORY`` CLI, not through the ordinary unit tests.
"""

import argparse
import importlib.metadata
import importlib.util
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check, stop_owned_process

ROOT = Path(__file__).resolve().parents[1]
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
WALL_SECONDS = 120.0
MAX_RSS_BYTES = 3 * GIB // 2
POLL_SECONDS = 0.5
SOURCE_FILES = (
    "docs/optimization/CLEAR_COIL_FIELD_START_PROTOCOL.md",
    "scripts/qualify_sparse_coil_surface.py",
    "src/fusion_baselines/sparse_coil_surface.py",
    "src/fusion_baselines/provenance.py",
    "src/fusion_baselines/resource_guard.py",
    "external/simsopt/src/simsopt/__init__.py",
    "external/simsopt/src/simsopt/geo/__init__.py",
    "external/simsopt/src/simsopt/geo/curveobjectives.py",
    "external/simsopt/src/simsopt/geo/curve.py",
    "external/simsopt/src/simsopt/geo/curvexyzfourier.py",
    "external/simsopt/src/simsopt/geo/surface.py",
    "external/simsopt/src/simsopt/geo/surfacerzfourier.py",
    "external/simsopt/src/simsopt/field/coil.py",
    "external/simsopt/src/simsopt/_core/optimizable.py",
    "external/simsopt/src/simsopt/_core/derivative.py",
)
SCOPE = dict(
    field_calls=0,
    equilibrium_solves=0,
    target_data_reads=0,
    physical_seed_pass=False,
    search_allowed=False,
    transfer_pass=False,
    step4_pass=False,
)


def builtin(value):
    if isinstance(value, np.ndarray):
        return builtin(value.tolist())
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise TypeError("string JSON keys required")
        return {key: builtin(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [builtin(item) for item in value]
    if value is None or type(value) in (int, str, bool):
        return value
    if type(value) is float and np.isfinite(value):
        return value
    raise TypeError("finite builtin JSON data required")


def save(path, document):
    document = builtin(document)
    json.dumps(document, allow_nan=False)
    write_json_atomic(Path(path), document)


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=sha256_file(path), bytes=path.stat().st_size)


def checked(reference):
    path = Path(reference["path"])
    if ref(path) != reference:
        raise ValueError("source or artifact bytes changed")
    return path


def read(path):
    return json.loads(Path(path).read_text())


def arrays(path, data):
    data = {key: np.asarray(value) for key, value in data.items()}
    if any(
        value.dtype.kind not in "bifu" or not np.isfinite(value).all() for value in data.values()
    ):
        raise ValueError("finite real numerical arrays required")
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream, **data)
    return ref(path)


def sources():
    native = importlib.util.find_spec("simsoptpp")
    package = importlib.util.find_spec("simsopt")
    if native is None or native.origin is None:
        raise ValueError("native simsoptpp binary required")
    if package is None or package.origin is None:
        raise ValueError("installed native Python package required")
    package_root = Path(package.origin).parent
    installed = []
    for path in SOURCE_FILES:
        prefix = "external/simsopt/src/simsopt/"
        if path.startswith(prefix):
            actual = ref(package_root / path.removeprefix(prefix))
            if actual["sha256"] != sha256_file(ROOT / path):
                raise ValueError("installed native Python source differs from pinned checkout")
            installed.append(actual)
    return dict(
        code=[ref(ROOT / path) for path in SOURCE_FILES],
        installed_native_python=installed,
        native_binary=ref(native.origin),
        python=ref(sys.executable),
        python_version=sys.version,
        platform=sys.platform,
        packages={
            name: importlib.metadata.version(name)
            for name in ("numpy", "scipy", "jax", "jaxlib", "simsopt")
        },
        repository=git_state(ROOT),
        external_repository=git_state(ROOT / "external/simsopt"),
    )


def matrix():
    return [
        dict(
            label=f"n{nbase}-q{ncoil}-{backend}",
            nbase=nbase,
            order=order,
            ncoil=ncoil,
            backend=backend,
        )
        for nbase, order in ((6, 5), (8, 7))
        for ncoil in (256, 512)
        for backend in ("native", "sparse")
    ]


def local_names(order):
    return [
        f"{axis}{kind}({mode})"
        for axis in "xyz"
        for kind, mode in [("c", 0)]
        + [(kind, mode) for mode in range(1, order + 1) for kind in "sc"]
    ]


def states(seed):
    seed = np.asarray(seed, dtype=float)
    result = [dict(label="seed", x=seed.copy(), gradient=True)]
    for name, fun in (("sin", np.sin), ("cos", np.cos)):
        direction = fun(np.arange(seed.size) + 1.0)
        direction /= np.linalg.norm(direction)
        for h in (1e-5, 5e-6):
            for sign in (1, -1):
                result.append(
                    dict(
                        label=f"{name}-{h:g}-{sign:+d}",
                        x=seed + sign * h * direction,
                        gradient=False,
                        direction=name,
                        step=h,
                        sign=sign,
                    )
                )
    result.append(dict(label="seed-repeat", x=seed.copy(), gradient=True))
    changed = seed.copy()
    changed[0] += 0.002  # canonical coil[0]/xc(0), not a native object-number index.
    result.extend(
        [
            dict(label="changed-base", x=changed.copy(), gradient=True),
            dict(label="changed-repeat", x=changed.copy(), gradient=True),
            dict(label="restored-seed", x=seed.copy(), gradient=True),
        ]
    )
    return result


def peak_rss_bytes(raw=None, platform=None):
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if raw is None else raw
    platform = sys.platform if platform is None else platform
    if not np.isfinite(raw) or raw < 0:
        raise ValueError("finite nonnegative ru_maxrss required")
    if platform == "darwin":
        return int(raw)
    if platform.startswith("linux"):
        return int(raw * 1024)
    raise ValueError("unqualified ru_maxrss platform units")


def deadline(started, now=None):
    elapsed = (time.monotonic() if now is None else now) - started
    if not np.isfinite(elapsed) or elapsed < 0:
        raise ValueError("finite forward wall clock required")
    if elapsed >= WALL_SECONDS:
        raise TimeoutError("registered 120 s synthetic worker budget exceeded")
    return float(elapsed)


def make_model(case):
    # Native imports/compilation are deliberately inside the timed child.
    from simsopt.field.coil import apply_symmetries_to_curves
    from simsopt.geo import (
        CurveCurveDistance,
        CurveSurfaceDistance,
        SurfaceRZFourier,
        create_equally_spaced_curves,
    )

    base = create_equally_spaced_curves(
        case["nbase"], 2, True, R0=0.3, R1=0.28, order=case["order"], numquadpoints=case["ncoil"]
    )
    physical = apply_symmetries_to_curves(base, 2, True)
    surface = SurfaceRZFourier.from_nphi_ntheta(
        nphi=128, ntheta=128, range="full torus", nfp=2, mpol=1, ntor=0
    )
    surface.set_rc(0, 0, 0.3)
    surface.set_rc(1, 0, 0.25)
    surface.set_zs(1, 0, 0.25)
    surface.fix_all()
    points = surface.gamma().reshape((-1, 3)).copy()
    normals = surface.normal().reshape((-1, 3)).copy()
    if case["backend"] == "native":
        cp = CurveSurfaceDistance(physical, surface, 0.08)
    else:
        from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance

        cp = SparseCurveSurfaceDistance(physical, points, normals, minimum_distance=0.08)
    cc = CurveCurveDistance(physical, 0.06, num_basecurves=len(physical))
    names = local_names(case["order"])
    if len(physical) != 4 * case["nbase"] or points.shape != (128**2, 3):
        raise ValueError("complete registered physical/grid matrix required")
    for curve in base:
        if set(curve.local_dof_names) != set(names) or len(curve.local_dof_names) != len(names):
            raise ValueError("all and only the registered free named Fourier DOFs required")
    return dict(
        base=base,
        physical=physical,
        surface=surface,
        points=points,
        normals=normals,
        cp=cp,
        cc=cc,
        local_names=names,
    )


def get_x(model):
    names = model["local_names"]
    return np.concatenate(
        [
            np.asarray(curve.local_full_x)[
                [list(curve.local_full_dof_names).index(name) for name in names]
            ]
            for curve in model["base"]
        ]
    )


def set_x(model, x):
    names = model["local_names"]
    for curve, values in zip(model["base"], np.asarray(x).reshape((-1, len(names))), strict=True):
        native = list(curve.local_full_dof_names)
        curve.local_full_x = values[[names.index(name) for name in native]]


def named_gradient(objective, model, work=None, record_work=lambda: None):
    derivative = objective.dJ(partials=True)
    values = []
    for curve in model["base"]:
        native = list(curve.local_dof_names)
        if work is not None:
            work["named_local_extractions"] += 1
            record_work()
        local = np.asarray(derivative(curve), dtype=float)
        if local.shape != (len(native),):
            raise ValueError("complete local VJP shape required")
        values.append(local[[native.index(name) for name in model["local_names"]]])
    result = np.concatenate(values)
    if not np.isfinite(result).all():
        raise ValueError("finite native named VJP required")
    return result


def evaluate(model, state, work, case, record_work=lambda work: None):
    if state["label"] == "changed-repeat":
        if not np.array_equal(get_x(model), state["x"]):
            raise ValueError("unchanged state required for cache-access repeat")
    else:
        set_x(model, state["x"])
    raw = dict(
        x=get_x(model),
        gamma=np.asarray([c.gamma() for c in model["physical"]]),
        gammadash=np.asarray([c.gammadash() for c in model["physical"]]),
    )
    metrics = {}
    # Ledger entries precede the corresponding calls, including failed attempts.
    for name in ("cp", "cc"):
        objective = model[name]
        work[name]["J_calls"] += 1
        record_work(work)
        metrics[name] = dict(J=float(objective.J()))
        if state["gradient"]:
            work[name]["dJ_calls"] += 1
            work[name]["requested_physical_curve_vjp_pairs"] += 4 * case["nbase"]
            record_work(work)
            raw[name + "_gradient"] = named_gradient(
                objective, model, work[name], lambda: record_work(work)
            )
        if state["label"] in ("seed", "changed-base", "restored-seed"):
            work[name]["shortest_distance_calls"] += 1
            record_work(work)
            metrics[name]["shortest_distance"] = float(objective.shortest_distance())
    builtin(metrics)
    return metrics, raw


def worker(config_path):
    config = read(config_path)
    case, output = config["case"], Path(config["output"])
    if (
        case not in matrix()
        or config["parent_pid"] != os.getppid()
        or any(os.environ.get(key) != "1" for key in THREADS)
    ):
        raise ValueError("registered cell, owned parent and one thread required")
    if sources() != config["source"]:
        raise ValueError("worker source binding changed before startup")
    started = config["started_monotonic"]
    work = {
        name: dict(
            J_calls=0,
            dJ_calls=0,
            named_local_extractions=0,
            requested_physical_curve_vjp_pairs=0,
            shortest_distance_calls=0,
        )
        for name in ("cp", "cc")
    }
    rows = []
    try:
        deadline(started)
        save(output / "model-attempt.json", dict(case=case, started_monotonic=time.monotonic()))
        model = make_model(case)
        seed = get_x(model)
        metadata = dict(
            nbase=case["nbase"],
            order=case["order"],
            nfp=2,
            nphysical=4 * case["nbase"],
            ncoil=case["ncoil"],
            surface_shape=[128, 128],
            surface_range="full torus",
            R0=0.3,
            R1=0.28,
            surface_R=0.3,
            surface_r=0.25,
            cp_threshold=0.08,
            cc_threshold=0.06,
            objective_weights="raw",
            names=[
                f"coil[{i}]/{name}" for i in range(case["nbase"]) for name in model["local_names"]
            ],
            native_local_names=[list(c.local_dof_names) for c in model["base"]],
            physical=[
                dict(base_index=i, period=period, flip=flip)
                for period in range(2)
                for flip in (False, True)
                for i in range(case["nbase"])
            ],
            parameter_period=1.0,
            surface_normal="unnormalized parameter normal",
        )
        save(output / "metadata.json", metadata)
        surface_ref = arrays(
            output / "surface.npz", dict(points=model["points"], normals=model["normals"])
        )
        save(
            output / "model.json", dict(metadata=ref(output / "metadata.json"), surface=surface_ref)
        )
        for index, state in enumerate(states(seed)):
            deadline(started)
            attempt = dict(
                index=index,
                label=state["label"],
                gradient=state["gradient"],
                started_monotonic=time.monotonic(),
                work_before=work,
            )
            save(output / f"attempt-{index:02d}.json", attempt)
            metrics, raw = evaluate(
                model,
                state,
                work,
                case,
                record_work=lambda counts, index=index, label=state["label"]: save(
                    output / "work-inflight.json",
                    dict(
                        index=index,
                        label=label,
                        attempted_calls=counts,
                        partial_failure_accounting="attempts, not successful returns",
                    ),
                ),
            )
            raw_ref = arrays(output / f"raw-{index:02d}.npz", raw)
            row = dict(
                index=index,
                label=state["label"],
                gradient=state["gradient"],
                metrics=metrics,
                arrays=raw_ref,
                work=work,
                ended_monotonic=time.monotonic(),
            )
            # Preserve successful numerical output even if its completion was late.
            save(output / f"raw-{index:02d}.json", row)
            deadline(started)
            rows.append(ref(output / f"raw-{index:02d}.json"))
            save(output / "checkpoint.json", dict(rows=rows, work=work))
        after = sources()
        if after != config["source"]:
            raise ValueError("worker source bytes changed during computation")
        elapsed = deadline(started)
        rss = peak_rss_bytes()
        save(
            output / "worker.json",
            dict(
                schema_version=1,
                status="completed",
                case=case,
                source_before=config["source"],
                source_after=after,
                metadata=ref(output / "metadata.json"),
                surface=surface_ref,
                rows=rows,
                work=work,
                ended_monotonic=time.monotonic(),
                elapsed_seconds=elapsed,
                peak_rss_bytes=rss,
                rss_pass=rss <= MAX_RSS_BYTES,
                threads={key: os.environ[key] for key in THREADS},
                scope=SCOPE,
            ),
        )
        return 0
    except Exception as error:
        save(
            output / "worker-error.json",
            dict(
                status="failed",
                error_type=type(error).__name__,
                error=str(error),
                work=work,
                completed_rows=rows,
                elapsed_seconds=time.monotonic() - started,
                peak_rss_bytes=peak_rss_bytes(),
                scope=SCOPE,
            ),
        )
        return 1


def run_process(command, *, output, env, started):
    minimum = space_check(output, 2 * GIB)["free_bytes"]
    result = dict(returncode=None, timed_out=False, elapsed_seconds=0.0)
    process = None
    try:
        with (output / "stdout.txt").open("x") as stdout:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=env,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            while process.poll() is None:
                deadline(started)
                minimum = min(minimum, space_check(output, 2 * GIB)["free_bytes"])
                time.sleep(POLL_SECONDS)
            result["returncode"] = process.returncode
            deadline(started)
    except Exception as error:
        result.update(
            error_type=type(error).__name__,
            error=str(error),
            timed_out=isinstance(error, TimeoutError),
        )
    finally:
        if process is not None:
            stop_owned_process(process)
            result["returncode"] = process.returncode
        result.update(
            elapsed_seconds=time.monotonic() - started, minimum_observed_free_bytes=minimum
        )
    return result


def tolerance(left, right, *, relative=5e-10, absolute=1e-12):
    left, right = np.asarray(left), np.asarray(right)
    if left.shape != right.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
        return dict(pass_=False, reason="shape or nonfinite mismatch")
    difference = np.abs(left - right)
    scale = np.maximum(np.abs(left), np.abs(right))
    return dict(
        pass_=bool(np.all((difference <= absolute) | (difference <= relative * scale))),
        maximum_absolute_error=float(np.max(difference, initial=0.0)),
        maximum_component_scale=float(np.max(scale, initial=0.0)),
    )


def row_arrays(row):
    with np.load(checked(row["arrays"]), allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def worker_checks(document):
    rows = [read(checked(item)) for item in document["rows"]]
    raw = [row_arrays(row) for row in rows]
    expected = states(raw[0]["x"])
    nbase, ncoil = document["case"]["nbase"], document["case"]["ncoil"]
    ndof = nbase * 3 * (2 * document["case"]["order"] + 1)
    if raw[0]["x"].shape != (ndof,) or any(
        item["gamma"].shape != (4 * nbase, ncoil, 3)
        or item["gammadash"].shape != (4 * nbase, ncoil, 3)
        for item in raw
    ):
        raise ValueError("registered complete node/DOF counts required")
    if len(rows) != len(expected) or any(
        row["index"] != i
        or row["label"] != state["label"]
        or row["gradient"] is not state["gradient"]
        or not np.array_equal(raw[i]["x"], state["x"])
        for i, (row, state) in enumerate(zip(rows, expected, strict=True))
    ):
        raise ValueError("complete exact registered state sequence required")
    checks = dict(
        active=all(rows[0]["metrics"][name]["J"] > 0 for name in ("cp", "cc")),
        finite_differences=[],
        exact_repeats=True,
        changed_copies=True,
    )
    for first, second in ((0, 9), (10, 11), (0, 12)):
        checks["exact_repeats"] &= all(
            np.array_equal(raw[first][key], raw[second][key]) for key in raw[first]
        )
        checks["exact_repeats"] &= all(
            rows[first]["metrics"][name]["J"] == rows[second]["metrics"][name]["J"]
            for name in ("cp", "cc")
        )
    changed = [
        i
        for i, (a, b) in enumerate(zip(raw[0]["gamma"], raw[10]["gamma"], strict=True))
        if not np.array_equal(a, b)
    ]
    checks["changed_copies"] = changed == [j * nbase for j in range(4)]
    checks["changed_cp_value"] = rows[0]["metrics"]["cp"]["J"] != rows[10]["metrics"]["cp"]["J"]
    for name in ("cp", "cc"):
        for direction_index, fun in enumerate((np.sin, np.cos)):
            vector = fun(np.arange(raw[0]["x"].size) + 1.0)
            vector /= np.linalg.norm(vector)
            analytic = float(raw[0][name + "_gradient"] @ vector)
            for step_index, h in enumerate((1e-5, 5e-6)):
                plus = 1 + 4 * direction_index + 2 * step_index
                numeric = (
                    rows[plus]["metrics"][name]["J"] - rows[plus + 1]["metrics"][name]["J"]
                ) / (2 * h)
                check = tolerance(analytic, numeric, relative=2e-4, absolute=1e-8)
                checks["finite_differences"].append(
                    dict(
                        objective=name,
                        direction=("sin", "cos")[direction_index],
                        h=h,
                        analytic=analytic,
                        finite_difference=numeric,
                        **check,
                    )
                )
    expected_work = {
        name: dict(
            J_calls=13,
            dJ_calls=5,
            named_local_extractions=5 * nbase,
            requested_physical_curve_vjp_pairs=20 * nbase,
            shortest_distance_calls=3,
        )
        for name in ("cp", "cc")
    }
    checks["work_exact"] = document["work"] == expected_work
    checks["all_pass"] = bool(
        checks["active"]
        and checks["exact_repeats"]
        and checks["changed_copies"]
        and checks["changed_cp_value"]
        and checks["work_exact"]
        and all(item["pass_"] for item in checks["finite_differences"])
    )
    return checks


def compare_pair(native, sparse):
    if read(checked(native["metadata"])) != read(checked(sparse["metadata"])):
        raise ValueError("native/sparse geometry metadata differ")
    with (
        np.load(checked(native["surface"]), allow_pickle=False) as first,
        np.load(checked(sparse["surface"]), allow_pickle=False) as second,
    ):
        if first.files != second.files or any(
            not np.array_equal(first[key], second[key]) for key in first.files
        ):
            raise ValueError("native/sparse full surface arrays differ")
    comparisons = []
    for first_ref, second_ref in zip(native["rows"], sparse["rows"], strict=True):
        first, second = read(checked(first_ref)), read(checked(second_ref))
        a, b = row_arrays(first), row_arrays(second)
        if first["label"] != second["label"] or any(
            not np.array_equal(a[key], b[key]) for key in ("x", "gamma", "gammadash")
        ):
            raise ValueError("native/sparse named geometry differs")
        for objective in ("cp", "cc"):
            for metric in first["metrics"][objective]:
                comparisons.append(
                    dict(
                        label=first["label"],
                        quantity=f"{objective}.{metric}",
                        **tolerance(
                            first["metrics"][objective][metric],
                            second["metrics"][objective][metric],
                        ),
                    )
                )
            if first["gradient"]:
                comparisons.append(
                    dict(
                        label=first["label"],
                        quantity=objective + ".gradient",
                        **tolerance(a[objective + "_gradient"], b[objective + "_gradient"]),
                    )
                )
    return dict(comparisons=comparisons, all_pass=all(item["pass_"] for item in comparisons))


def completed_worker(process, document, case, source, started):
    def nonnegative_number(value):
        return type(value) in (float, int) and np.isfinite(value) and value >= 0

    clocks = [
        process.get("elapsed_seconds"),
        document.get("elapsed_seconds"),
        document.get("ended_monotonic"),
        started,
    ]
    if not all(nonnegative_number(value) for value in clocks):
        raise ValueError("finite nonnegative process/worker clocks required")
    rss = document.get("peak_rss_bytes")
    if type(rss) is not int or rss < 0:
        raise ValueError("exact nonnegative integer peak-RSS bytes required")
    ended_elapsed = document["ended_monotonic"] - started
    if (
        type(process.get("returncode")) is not int
        or process["returncode"] != 0
        or process.get("error_type")
        or process.get("timed_out") is not False
        or document.get("status") != "completed"
        or document.get("case") != case
        or not 0 <= ended_elapsed < WALL_SECONDS
        or process["elapsed_seconds"] >= WALL_SECONDS
        or document["elapsed_seconds"] >= WALL_SECONDS
        or document.get("source_before") != source
        or document.get("source_after") != source
        or document.get("scope") != SCOPE
        or document.get("threads") != {key: "1" for key in THREADS}
        or document.get("rss_pass") is not (rss <= MAX_RSS_BYTES)
    ):
        raise ValueError("successful timely source-bound worker completion required")


def _qualify(output):
    before = sources()
    save(output / "source-before.json", before)
    space_check(output, 3 * GIB)
    env = dict(os.environ, **{key: "1" for key in THREADS})
    env["PYTHONPATH"] = str(ROOT / "src")
    env.setdefault("MPLCONFIGDIR", "/private/tmp/fusion-mpl-cache")
    rows, completed = [], {}
    for index, case in enumerate(matrix()):
        space_check(output, 3 * GIB)
        directory = output / case["label"]
        directory.mkdir()
        started = time.monotonic()
        config = dict(
            case=case,
            output=str(directory),
            parent_pid=os.getpid(),
            started_monotonic=started,
            source=before,
        )
        save(directory / "config.json", config)
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            str(directory / "config.json"),
        ]
        save(directory / "launch.json", dict(command=command, case=case, started_monotonic=started))
        process = run_process(command, output=directory, env=env, started=started)
        save(directory / "process.json", process)
        row = dict(index=index, case=case, process=ref(directory / "process.json"), status="failed")
        try:
            document = read(directory / "worker.json")
            completed_worker(process, document, case, before, started)
            checks = worker_checks(document)
            row.update(
                status="completed",
                worker=ref(directory / "worker.json"),
                checks=checks,
                peak_rss_bytes=document["peak_rss_bytes"],
                resource_pass=document["peak_rss_bytes"] <= MAX_RSS_BYTES,
            )
            completed[case["label"]] = document
        except Exception as error:
            row.update(error_type=type(error).__name__, error=str(error))
        row["retained"] = [ref(path) for path in sorted(directory.iterdir()) if path.is_file()]
        save(directory / "result.json", row)
        rows.append(ref(directory / "result.json"))
        save(output / "checkpoint.json", dict(rows=rows))
    pairs = []
    for nbase in (6, 8):
        for ncoil in (256, 512):
            stem = f"n{nbase}-q{ncoil}"
            try:
                pair = compare_pair(completed[stem + "-native"], completed[stem + "-sparse"])
            except Exception as error:
                pair = dict(all_pass=False, error_type=type(error).__name__, error=str(error))
            pairs.append(dict(nbase=nbase, ncoil=ncoil, **pair))
    after = sources()
    save(output / "source-after.json", after)
    reports = [read(checked(item)) for item in rows]
    passed = bool(
        before == after
        and all(
            row["status"] == "completed" and row["resource_pass"] and row["checks"]["all_pass"]
            for row in reports
        )
        and all(pair["all_pass"] for pair in pairs)
    )
    result = dict(
        schema_version=1,
        status="completed",
        kind="synthetic-resource-qualification",
        source_before=before,
        source_after=after,
        source_unchanged=before == after,
        matrix=matrix(),
        rows=rows,
        pairs=pairs,
        all_pass=passed,
        limits=dict(
            wall_seconds=WALL_SECONDS,
            peak_rss_bytes=MAX_RSS_BYTES,
            parent_poll_seconds=POLL_SECONDS,
            termination_grace_seconds=5,
        ),
        scope=SCOPE,
    )
    save(output / "run.json", result)
    return result


def qualify(output):
    output = Path(output)
    if not output.is_absolute():
        raise ValueError("absolute fresh output path required")
    output.mkdir(parents=True, exist_ok=False)
    try:
        return _qualify(output)
    except Exception as error:
        # A terminal record never replaces the last successfully saved checkpoint.
        save(
            output / "terminal-error.json",
            dict(status="failed", error_type=type(error).__name__, error=str(error), scope=SCOPE),
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--raw", "--output", dest="output", type=Path)
    group.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker is not None:
        return worker(args.worker)
    result = qualify(args.output)
    print(
        json.dumps(
            dict(
                status=result["status"],
                all_pass=result["all_pass"],
                run=ref(args.output / "run.json"),
            ),
            allow_nan=False,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
