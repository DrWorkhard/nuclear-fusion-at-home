"""Independent saved-data admission of the bounded native reference follow-up.

No native objective, field, gradient or producer evaluation is called. Immutable
raw arrays supply all state/repeat/finite-difference/backend comparisons.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
RSS_LIMIT = 3 * 1024**3 // 2
THREADS = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}
OLD_SCOPE = dict(
    field_calls=0,
    equilibrium_solves=0,
    target_data_reads=0,
    physical_seed_pass=False,
    search_allowed=False,
    transfer_pass=False,
    step4_pass=False,
)
SCOPE = dict(OLD_SCOPE, startup_pass=False)
KERNELS = ("J", "position", "tangent", "minimum", "position_vjp", "tangent_vjp")


def sources(root):
    from block_native_reference_inputs import sources as bound_sources

    return bound_sources(root)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    result = np.asarray(value)
    require(
        result.dtype.kind in "iuf" and result.size and np.isfinite(result).all(),
        "finite real numerical data without coercion required",
    )
    return result.astype(float, copy=False)


def typed_equal(actual, expected):
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and set(actual) == set(expected)
            and all(typed_equal(actual[k], v) for k, v in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(typed_equal(a, b) for a, b in zip(actual, expected, strict=True))
        )
    return type(actual) is type(expected) and actual == expected


class Evidence:
    """Read/hash every reference once; never alter evidence or old outputs."""

    def __init__(self):
        self.references, self.documents, self.arrays = {}, {}, {}

    def check(self, ref):
        require(
            isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"},
            "exact immutable reference schema",
        )
        path = Path(ref["path"])
        require(
            path.is_absolute()
            and type(ref["sha256"]) is str
            and len(ref["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in ref["sha256"]),
            "absolute SHA256 reference",
        )
        key = str(path)
        if key not in self.references:
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            self.references[key] = dict(sha256=digest, bytes=path.stat().st_size)
        actual = self.references[key]
        require(actual["sha256"] == ref["sha256"], f"changed evidence hash: {path}")
        if "bytes" in ref:
            require(
                type(ref["bytes"]) is int and ref["bytes"] == actual["bytes"],
                f"changed byte count: {path}",
            )
        return path

    def read(self, ref):
        path = self.check(ref)
        key = str(path)
        if key not in self.documents:
            self.documents[key] = json.loads(path.read_text())
        return self.documents[key]

    def array(self, ref):
        path = self.check(ref)
        key = str(path)
        if key not in self.arrays:
            with np.load(path, allow_pickle=False) as archive:
                self.arrays[key] = {k: finite(archive[k]).copy() for k in archive.files}
        return self.arrays[key]

    def bind(self, value, expanded=None):
        expanded = set() if expanded is None else expanded
        if isinstance(value, dict):
            if "path" in value and "sha256" in value:
                path = self.check(value)
                if path.suffix == ".json" and str(path) not in expanded:
                    expanded.add(str(path))
                    self.bind(self.read(value), expanded)
            else:
                for item in value.values():
                    self.bind(item, expanded)
        elif isinstance(value, list):
            for item in value:
                self.bind(item, expanded)


def matrix(legacy=False):
    return [
        dict(label=f"n{n}-q{q}-{backend}", nbase=n, order=m, ncoil=q, backend=backend)
        for n, m in ((6, 5), (8, 7))
        for q in (256, 512)
        for backend in (("native", "sparse") if legacy else ("block-native",))
    ]


def local_names(order):
    return [
        f"{axis}{kind}({m})"
        for axis in "xyz"
        for kind, m in [("c", 0)] + [(kind, m) for m in range(1, order + 1) for kind in ("s", "c")]
    ]


def state_plan(seed):
    seed = finite(seed)
    require(seed.ndim == 1, "canonical parameter vector")
    result = [dict(label="seed", x=seed.copy(), gradient=True)]
    for name, function in (("sin", np.sin), ("cos", np.cos)):
        direction = function(np.arange(1, len(seed) + 1, dtype=float))
        direction /= np.linalg.norm(direction)
        for step in (1e-5, 5e-6):
            for sign in (1, -1):
                result.append(
                    dict(
                        label=f"{name}-{step:g}-{sign:+d}",
                        x=seed + sign * step * direction,
                        gradient=False,
                    )
                )
    changed = seed.copy()
    changed[0] += 0.002
    return result + [
        dict(label="seed-repeat", x=seed.copy(), gradient=True),
        dict(label="changed-base", x=changed.copy(), gradient=True),
        dict(label="changed-repeat", x=changed.copy(), gradient=True),
        dict(label="restored-seed", x=seed.copy(), gradient=True),
    ]


def tolerance(first, second, relative=5e-10, absolute=1e-12):
    first, second = finite(first), finite(second)
    require(first.shape == second.shape, "equal finite comparison shapes")
    error, scale = abs(first - second), np.maximum(abs(first), abs(second))
    return dict(
        passed=bool(np.all((error <= absolute) | (error <= relative * scale))),
        maximum_absolute_error=float(error.max()),
        maximum_component_scale=float(scale.max()),
    )


def zero_work():
    return {
        objective: dict(
            J_calls=0,
            dJ_calls=0,
            named_local_extractions=0,
            requested_physical_curve_vjp_pairs=0,
            shortest_distance_calls=0,
        )
        for objective in ("cp", "cc")
    }


def zero_kernels():
    return {key: dict(attempted=0, completed=0) for key in KERNELS}


def kernel_add(counter, reservation):
    require(
        set(reservation) == set(KERNELS)
        and all(type(v) is int and v >= 0 for v in reservation.values())
        and any(reservation.values()),
        "complete nonnegative kernel reservation",
    )
    return {
        key: {
            side: counter[key][side] + reservation.get(key, 0)
            for side in ("attempted", "completed")
        }
        for key in KERNELS
    }


def original_metadata(case):
    n, order = case["nbase"], case["order"]
    names = local_names(order)
    return dict(
        nbase=n,
        order=order,
        nfp=2,
        nphysical=4 * n,
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
        names=[f"coil[{i}]/{name}" for i in range(n) for name in names],
        native_local_names=[names.copy() for _ in range(n)],
        physical=[
            dict(base_index=i, period=p, flip=f)
            for p in range(2)
            for f in (False, True)
            for i in range(n)
        ],
        parameter_period=1.0,
        surface_normal="unnormalized parameter normal",
    )


def surface_identity(raw):
    phi, theta = np.meshgrid(
        2 * np.pi * np.arange(128) / 128, 2 * np.pi * np.arange(128) / 128, indexing="ij"
    )
    radius = 0.3 + 0.25 * np.cos(theta)
    points = np.stack((radius * np.cos(phi), radius * np.sin(phi), 0.25 * np.sin(theta)), axis=-1)
    dt = (
        2
        * np.pi
        * np.stack(
            (
                -0.25 * np.sin(theta) * np.cos(phi),
                -0.25 * np.sin(theta) * np.sin(phi),
                0.25 * np.cos(theta),
            ),
            axis=-1,
        )
    )
    dp = (
        2
        * np.pi
        * np.stack((-radius * np.sin(phi), radius * np.cos(phi), np.zeros_like(phi)), axis=-1)
    )
    expected = dict(points=points.reshape(-1, 3), normals=np.cross(dp, dt).reshape(-1, 3))
    require(set(raw) == set(expected), "complete original surface arrays")
    errors = {}
    for key, value in expected.items():
        errors[key] = tolerance(raw[key], value, relative=0, absolute=5e-12)
        require(errors[key]["passed"], "original128² unnormalized full-torus geometry")
    return errors


def curve_identity(raw, case):
    n, order, count = (case[k] for k in ("nbase", "order", "ncoil"))
    require(raw["x"].shape == (n * 3 * (2 * order + 1),), "complete canonical parameter dimension")
    coefficients = raw["x"].reshape(n, 3, 2 * order + 1)
    physical = []
    for period in range(2):
        c, s = np.cos(np.pi * period), np.sin(np.pi * period)
        rotation = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1.0]])
        for flip in (False, True):
            transform = rotation @ np.diag([1.0, -1.0, -1.0]) if flip else rotation
            physical.extend(transform.T @ row for row in coefficients)
    coefficients = np.asarray(physical)
    phase = 2 * np.pi * np.arange(count)[:, None] / count * np.arange(1, order + 1)
    frequency = 2 * np.pi * np.arange(1, order + 1)
    p = (
        coefficients[:, :, 0, None]
        + coefficients[:, :, 1::2] @ np.sin(phase).T
        + coefficients[:, :, 2::2] @ np.cos(phase).T
    ).transpose(0, 2, 1)
    t = (
        (coefficients[:, :, 1::2] * frequency) @ np.cos(phase).T
        - (coefficients[:, :, 2::2] * frequency) @ np.sin(phase).T
    ).transpose(0, 2, 1)
    errors = {}
    for key, expected in (("gamma", p), ("gammadash", t)):
        errors[key] = tolerance(raw[key], expected, relative=0, absolute=5e-12)
        require(errors[key]["passed"], "full physical Fourier geometry mismatch")
    return errors


def seed_identity(seed, case):
    n, order = case["nbase"], case["order"]
    expected = np.zeros((n, 3, 2 * order + 1))
    for i in range(n):
        angle = (i + 0.5) * 2 * np.pi / (4 * n)
        expected[i, :, 0] = [0.3 * np.cos(angle), 0.3 * np.sin(angle), 0]
        expected[i, :, 2] = [0.28 * np.cos(angle), 0.28 * np.sin(angle), 0]
        expected[i, 2, 1] = -0.28
    require(
        tolerance(seed, expected.ravel(), relative=0, absolute=5e-12)["passed"],
        "unchanged synthetic circular seed required",
    )


def progress_plan(nphysical, gradient, minimum):
    phases = [("J", dict.fromkeys(KERNELS, 0) | {"J": 64})]
    if gradient:
        phases.append(
            (
                "dJ",
                dict.fromkeys(KERNELS, 0)
                | dict(position=64, tangent=64, position_vjp=1, tangent_vjp=1),
            )
        )
    if minimum:
        phases.append(("minimum", dict.fromkeys(KERNELS, 0) | {"minimum": 64}))
    return [
        (curve, phase, reservation) for phase, reservation in phases for curve in range(nphysical)
    ]


def progress_audit(worker, plan, evidence):
    path = evidence.check(worker["kernel_progress"])
    events = [json.loads(line) for line in path.read_text().splitlines()]
    require(
        len(events) == 2 * len(plan)
        and type(worker["kernel_progress_events"]) is int
        and worker["kernel_progress_events"] == len(events),
        "complete paired kernel reservation/completion history",
    )
    counter = zero_kernels()
    previous_time = 0.0
    for index, ((state, label, start, stop, curve, phase, reservation), begin, end) in enumerate(
        zip(plan, events[::2], events[1::2], strict=True)
    ):
        upper = kernel_add(counter, reservation)
        for record, status in ((begin, "reserved"), (end, "completed")):
            require(
                type(record["state_index"]) is int
                and record["state_index"] == state
                and record["state_label"] == label,
                "kernel history public-state identity",
            )
            timestamp = record["monotonic"]
            require(
                type(timestamp) in (float, int)
                and np.isfinite(timestamp)
                and start <= timestamp <= stop
                and previous_time <= timestamp,
                "serial kernel events within persisted public-call clocks",
            )
            previous_time = timestamp
            event = record["event"]
            require(
                type(event["index"]) is int
                and event["index"] == index
                and type(event["curve_index"]) is int
                and event["curve_index"] == curve
                and event["phase"] == phase
                and event["status"] == status
                and typed_equal(event["reservation"], reservation)
                and typed_equal(event["work_before"], counter)
                and typed_equal(event["upper_work"], upper),
                "exact phase reservation and bound",
            )
        require(
            typed_equal(begin["event"]["work"], counter)
            and typed_equal(end["event"]["work"], upper),
            "all reserved kernels must synchronously complete",
        )
        counter = upper
    require(
        typed_equal(events[-1], evidence.read(worker["kernel_inflight"])),
        "last atomic kernel checkpoint",
    )
    require(typed_equal(counter, worker["kernel_work"]), "final exact kernel totals")
    return dict(events=len(events), reservations=len(plan), kernel_work=counter, passed=True)


def worker_audit(result, case, source, evidence, *, legacy=False):
    require(result["case"] == case and result["status"] == "completed", "completed expected worker")
    worker, process = evidence.read(result["worker"]), evidence.read(result["process"])
    folder = Path(result["worker"]["path"]).parent
    retained = {Path(ref["path"]).name: ref for ref in result["retained"]}
    require(len(retained) == len(result["retained"]), "unique retained artifact names")
    require(
        all(Path(ref["path"]).parent == folder for ref in retained.values()),
        "retained artifacts belong to their worker",
    )
    config, launch = [evidence.read(retained[k]) for k in ("config.json", "launch.json")]
    if not legacy:
        require(
            result["config"] == retained["config.json"]
            and result["launch"] == retained["launch.json"],
            "exact explicit configuration and launch references",
        )
    require(
        config["output"] == str(folder) and config["case"] == case,
        "exact worker path and configuration",
    )
    require(
        all(
            typed_equal(item, source)
            for item in (config["source"], worker["source_before"], worker["source_after"])
        ),
        "unchanged worker source bytes",
    )
    require(
        worker["case"] == case
        and worker["status"] == "completed"
        and typed_equal(worker["scope"], OLD_SCOPE if legacy else SCOPE)
        and worker["threads"] == THREADS,
        "worker status, scope and single-thread identity",
    )
    times = [
        config["started_monotonic"],
        worker["elapsed_seconds"],
        worker["ended_monotonic"],
        process["elapsed_seconds"],
    ]
    require(
        all(type(v) in (int, float) and np.isfinite(v) and v >= 0 for v in times),
        "finite nonnegative elapsed clocks",
    )
    start, elapsed, ended, parent_elapsed = times
    require(
        type(process["returncode"]) is int
        and process["returncode"] == 0
        and process["timed_out"] is False
        and not process.get("error_type")
        and 0 <= elapsed <= ended - start <= parent_elapsed < 120,
        "strict120s timely worker and parent completion with integer exit0",
    )
    require(
        launch["case"] == case
        and launch["started_monotonic"] == start
        and launch["command"][-2:] == ["--worker", str(folder / "config.json")],
        "bound actual launch",
    )
    require(
        type(process["minimum_observed_free_bytes"]) is int
        and process["minimum_observed_free_bytes"] >= 2 * 1024**3,
        "runtime disk reserve",
    )
    rss = worker["peak_rss_bytes"]
    require(type(rss) is int and rss > 0, "positive integer measured RSS bytes")
    resource_pass = rss <= RSS_LIMIT
    require(
        worker["rss_pass"] is resource_pass
        and result["resource_pass"] is resource_pass
        and result["peak_rss_bytes"] == rss,
        "recomputed measured RSS gate",
    )
    require(
        typed_equal(evidence.read(worker["metadata"]), original_metadata(case)),
        "all original synthetic geometry, names, copies and quadrature metadata",
    )
    surface = evidence.array(worker["surface"])
    surface_checks = surface_identity(surface)
    require(
        len(worker["rows"]) == 13 and (legacy or len(worker["attempts"]) == 13),
        "all13 registered states and attempts required",
    )
    rows = [evidence.read(ref) for ref in worker["rows"]]
    raw = [evidence.array(row["arrays"]) for row in rows]
    seed_identity(raw[0]["x"], case)
    plan = state_plan(raw[0]["x"])
    work, kernels, phases = zero_work(), zero_kernels(), []
    previous = start
    max_geometry_error = 0.0
    for i, (row, data, state) in enumerate(zip(rows, raw, plan, strict=True)):
        attempt_ref = retained[f"attempt-{i:02d}.json"]
        if not legacy:
            require(
                worker["attempts"][i] == attempt_ref and row["attempt"] == attempt_ref,
                "row and worker bind their exact public attempt",
            )
        attempt = evidence.read(attempt_ref)
        require(
            type(row["index"]) is int
            and row["index"] == i
            and row["label"] == state["label"]
            and row["gradient"] is state["gradient"]
            and np.array_equal(data["x"], state["x"]),
            "exact state sequence and canonical coefficients",
        )
        require(
            type(attempt["index"]) is int
            and attempt["index"] == i
            and attempt["label"] == state["label"]
            and attempt["gradient"] is state["gradient"]
            and typed_equal(attempt["work_before"], work),
            "persisted public-call work prefix",
        )
        require(
            all(
                type(t) in (int, float) and np.isfinite(t)
                for t in (attempt["started_monotonic"], row["ended_monotonic"])
            )
            and previous <= attempt["started_monotonic"] <= row["ended_monotonic"] <= ended,
            "serial timely row persistence",
        )
        previous = row["ended_monotonic"]
        expected_keys = {"x", "gamma", "gammadash"} | (
            {"cp_gradient", "cc_gradient"} if state["gradient"] else set()
        )
        require(set(data) == expected_keys, "complete raw geometry/gradient roles")
        checks = curve_identity(data, case)
        max_geometry_error = max(
            max_geometry_error, *(check["maximum_absolute_error"] for check in checks.values())
        )
        minimum = i in (0, 10, 12)
        require(set(row["metrics"]) == {"cp", "cc"}, "both raw objectives")
        for objective in ("cp", "cc"):
            require(
                set(row["metrics"][objective])
                == ({"J", "shortest_distance"} if minimum else {"J"}),
                "all and only prescribed objective metrics",
            )
            require(
                float(finite(row["metrics"][objective]["J"])) > 0,
                "active positive CP and CC control",
            )
            work[objective]["J_calls"] += 1
            if state["gradient"]:
                require(
                    data[objective + "_gradient"].shape == raw[0]["x"].shape, "full named gradient"
                )
                work[objective]["dJ_calls"] += 1
                work[objective]["named_local_extractions"] += case["nbase"]
                work[objective]["requested_physical_curve_vjp_pairs"] += 4 * case["nbase"]
            if minimum:
                require(
                    float(finite(row["metrics"][objective]["shortest_distance"])) > 0,
                    "positive complete sampled minimum",
                )
                work[objective]["shortest_distance_calls"] += 1
        require(typed_equal(row["work"], work), "exact public-call work after every state")
        if not legacy:
            require(
                typed_equal(attempt["kernel_work_before"], kernels),
                "kernel work before public calls",
            )
            require(
                type(attempt["kernel_progress_events_before"]) is int
                and attempt["kernel_progress_events_before"] == 2 * len(phases),
                "exact pre-state progress history prefix",
            )
            new_phases = progress_plan(4 * case["nbase"], state["gradient"], minimum)
            for _, _, reservation in new_phases:
                kernels = kernel_add(kernels, reservation)
            phases.extend(
                (i, state["label"], attempt["started_monotonic"], row["ended_monotonic"], *phase)
                for phase in new_phases
            )
            require(
                typed_equal(row["kernel_work"], kernels),
                "exact attempted/completed kernel state prefix",
            )
            require(
                type(row["kernel_progress_events"]) is int
                and row["kernel_progress_events"] == 2 * len(phases),
                "exact post-state progress history prefix",
            )
    require(typed_equal(worker["work"], work), "full final public-call counters")
    checkpoint = evidence.read(retained["checkpoint.json"])
    expected_checkpoint = dict(rows=worker["rows"], work=work)
    if not legacy:
        expected_checkpoint.update(kernel_work=kernels, kernel_progress_events=2 * len(phases))
        model = evidence.read(worker["model"])
        require(
            typed_equal(
                model,
                dict(
                    metadata=worker["metadata"],
                    surface=worker["surface"],
                    block_size=256,
                    blocks=64,
                    block_weight=1 / 64,
                    kernel_work=zero_kernels(),
                ),
            ),
            "unmodified full native block model",
        )
    require(typed_equal(checkpoint, expected_checkpoint), "exact final successful checkpoint")
    require(
        typed_equal(
            evidence.read(retained["work-inflight.json"]),
            dict(
                index=12,
                label="restored-seed",
                attempted_calls=work,
                partial_failure_accounting="attempts, not successful returns",
            ),
        ),
        "complete public-call final reservation",
    )
    repeat_checks = []
    for first, second in ((0, 9), (10, 11), (0, 12)):
        repeat_checks.append(
            bool(
                all(np.array_equal(raw[first][key], raw[second][key]) for key in raw[first])
                and all(
                    rows[first]["metrics"][obj][key] == rows[second]["metrics"][obj][key]
                    for obj in ("cp", "cc")
                    for key in rows[first]["metrics"][obj].keys()
                    & rows[second]["metrics"][obj].keys()
                )
            )
        )
    changed = [
        i
        for i, (a, b) in enumerate(zip(raw[0]["gamma"], raw[10]["gamma"], strict=True))
        if not np.array_equal(a, b)
    ]
    changed_pass = (
        changed == [i * case["nbase"] for i in range(4)]
        and rows[0]["metrics"]["cp"]["J"] != rows[10]["metrics"]["cp"]["J"]
    )
    fd = []
    for objective in ("cp", "cc"):
        for d, function in enumerate((np.sin, np.cos)):
            direction = function(np.arange(1, len(raw[0]["x"]) + 1, dtype=float))
            direction /= np.linalg.norm(direction)
            analytic = float(raw[0][objective + "_gradient"] @ direction)
            for j, step in enumerate((1e-5, 5e-6)):
                index = 1 + 4 * d + 2 * j
                numeric = float(
                    (
                        rows[index]["metrics"][objective]["J"]
                        - rows[index + 1]["metrics"][objective]["J"]
                    )
                    / (2 * step)
                )
                fd.append(
                    dict(
                        objective=objective,
                        direction=d,
                        step=step,
                        analytic=analytic,
                        finite_difference=numeric,
                        **tolerance(analytic, numeric, 2e-4, 1e-8),
                    )
                )
    kernel_report = None if legacy else progress_audit(worker, phases, evidence)
    math_pass = bool(all(repeat_checks) and changed_pass and all(row["passed"] for row in fd))
    report = dict(
        case=case,
        resource_pass=resource_pass,
        peak_rss_bytes=rss,
        worker_seconds=float(elapsed),
        parent_seconds=float(parent_elapsed),
        state_count=13,
        work=work,
        repetitions=repeat_checks,
        changed_copies=changed,
        changed_copies_pass=bool(changed_pass),
        finite_differences=fd,
        geometry_max_absolute_error=max_geometry_error,
        surface_checks=surface_checks,
        kernels=kernel_report,
        mathematical_pass=math_pass,
        passed=bool(resource_pass and math_pass),
    )
    return dict(
        report=report,
        worker=worker,
        rows=rows,
        arrays=raw,
        surface=surface,
        started=float(start),
        parent_ended=float(start + parent_elapsed),
    )


def pair_audit(left, right):
    require(
        set(left["surface"]) == set(right["surface"])
        and all(np.array_equal(left["surface"][k], right["surface"][k]) for k in left["surface"]),
        "exact unchanged backend surface",
    )
    comparisons = []
    for first, second, a, b in zip(
        left["rows"], right["rows"], left["arrays"], right["arrays"], strict=True
    ):
        require(
            first["label"] == second["label"]
            and all(np.array_equal(a[k], b[k]) for k in ("x", "gamma", "gammadash")),
            "exact original named backend geometry",
        )
        for objective in ("cp", "cc"):
            require(
                set(first["metrics"][objective]) == set(second["metrics"][objective]),
                "matching raw metric roles",
            )
            for metric in first["metrics"][objective]:
                comparisons.append(
                    dict(
                        state=first["label"],
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
                        state=first["label"],
                        quantity=f"{objective}.gradient",
                        **tolerance(a[objective + "_gradient"], b[objective + "_gradient"]),
                    )
                )
    require(len(comparisons) == 42, "all42 state/value/gradient/minimum comparisons")
    return dict(comparisons=comparisons, passed=all(row["passed"] for row in comparisons))


def audit(run, root=ROOT):
    current_binding = sources(root)
    binding = run["source_before"]
    evidence = Evidence()
    evidence.bind(current_binding)
    evidence.bind(binding)
    evidence.bind(run)
    require(
        type(run["schema_version"]) is int
        and run["schema_version"] == 1
        and run["kind"] == "block-native-reference-qualification"
        and run["status"] == "completed",
        "completed separate block-native reference schema",
    )
    require(
        typed_equal(run["source_before"], run["source_after"]) and run["source_unchanged"] is True,
        "exact unchanged sources for entire follow-up",
    )
    require(
        typed_equal(
            {k: v for k, v in binding.items() if k != "repository"},
            {k: v for k, v in current_binding.items() if k != "repository"},
        ),
        "unchanged current numerical sources; only root Git bookkeeping may differ",
    )
    require(
        typed_equal(run["scope"], SCOPE)
        and run["independent_audit_pass"] is False
        and run["bounded_reference_pass"] is False
        and run["all_pass"] is False
        and type(run["producer_checks_pass"]) is bool
        and run["admission_status"] == "pending-independent-audit",
        "no premature scientific admission",
    )
    require(
        run["old_reference"] == binding["old_reference"], "exact unchanged predecessor reference"
    )
    require(
        typed_equal(run["matrix"], matrix())
        and typed_equal(binding["matrix"], matrix())
        and len(run["rows"]) == 4,
        "fixed full four-worker matrix",
    )
    require(
        run["limits"]
        == dict(
            wall_seconds=120.0,
            peak_rss_bytes=RSS_LIMIT,
            parent_poll_seconds=0.5,
            termination_grace_seconds=5,
        ),
        "unchanged resources",
    )
    old = evidence.read(binding["old_reference"])
    require(
        old["status"] == "completed"
        and old["all_pass"] is False
        and old["source_unchanged"] is True
        and old["source_before"] == old["source_after"] == binding["legacy_source"]
        and typed_equal(old["scope"], OLD_SCOPE)
        and typed_equal(old["matrix"], matrix(True))
        and len(old["rows"]) == 8,
        "preserved complete negative legacy matrix",
    )
    old_workers = {}
    previous_ended = 0.0
    for i, (ref, case) in enumerate(zip(old["rows"], matrix(True), strict=True)):
        result = evidence.read(ref)
        require(
            type(result["index"]) is int
            and result["index"] == i
            and result["worker"] == binding["old_workers"][case["label"]],
            "exact historical worker identity",
        )
        old_workers[case["label"]] = worker_audit(
            result, case, binding["legacy_source"], evidence, legacy=True
        )
        require(
            old_workers[case["label"]]["started"] >= previous_ended,
            "serial historical worker execution",
        )
        previous_ended = old_workers[case["label"]]["parent_ended"]
    old_pairs = [
        pair_audit(old_workers[f"n{n}-q{q}-native"], old_workers[f"n{n}-q{q}-sparse"])
        for n in (6, 8)
        for q in (256, 512)
    ]
    old_math = all(row["report"]["mathematical_pass"] for row in old_workers.values())
    sparse_pass = all(
        row["report"]["passed"] for name, row in old_workers.items() if name.endswith("-sparse")
    )
    old_all = all(row["report"]["passed"] for row in old_workers.values()) and all(
        row["passed"] for row in old_pairs
    )
    require(old_all is False, "legacy negative decision must remain negative")
    require(
        {name for name, row in old_workers.items() if not row["report"]["resource_pass"]}
        == {"n6-q512-native", "n8-q256-native", "n8-q512-native"},
        "exact three unchanged historical dense RSS failures",
    )
    reports, comparisons = [], []
    previous_ended = 0.0
    for i, (ref, case) in enumerate(zip(run["rows"], matrix(), strict=True)):
        result = evidence.read(ref)
        require(type(result["index"]) is int and result["index"] == i, "ordered new matrix rows")
        checked = worker_audit(result, case, binding, evidence)
        require(checked["started"] >= previous_ended, "serial fresh worker execution")
        previous_ended = checked["parent_ended"]
        reports.append(checked["report"])
        for backend in ("native", "sparse"):
            old_label = f"n{case['nbase']}-q{case['ncoil']}-{backend}"
            comparisons.append(
                dict(case=case, old_label=old_label, **pair_audit(checked, old_workers[old_label]))
            )
    passed = bool(
        old_math
        and sparse_pass
        and all(row["passed"] for row in old_pairs)
        and all(row["passed"] for row in reports)
        and all(row["passed"] for row in comparisons)
    )
    return dict(
        status="completed",
        source=binding,
        auditor_repository=current_binding["repository"],
        arithmetic_and_source_pass=True,
        bounded_reference_pass=passed,
        all_pass=passed,
        legacy_all_pass=False,
        legacy_sparse_pass=bool(sparse_pass),
        legacy_workers=[row["report"] for row in old_workers.values()],
        legacy_pairs=old_pairs,
        workers=reports,
        comparisons=comparisons,
        compared_quantities=336,
        verified_reference_files=len(evidence.references),
        **SCOPE,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        args.run.is_absolute() and not args.output.exists(), "absolute saved run and fresh output"
    )
    result = dict(
        status="error",
        arithmetic_and_source_pass=False,
        bounded_reference_pass=False,
        all_pass=False,
        **SCOPE,
    )
    try:
        result.update(audit(json.loads(args.run.read_text())))
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    with args.run.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    result["run"] = dict(path=str(args.run), sha256=digest, bytes=args.run.stat().st_size)
    json.dumps(result, allow_nan=False)
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("status", "arithmetic_and_source_pass", "bounded_reference_pass")
            }
        ),
        flush=True,
    )
    return 0 if result["bounded_reference_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
