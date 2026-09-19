"""Four fresh synthetic block-native workers; immutable dense failures remain failures."""

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import qualify_sparse_coil_surface as legacy

from fusion_baselines.resource_guard import GIB, space_check

ROOT = Path(__file__).resolve().parents[1]
THREADS = legacy.THREADS
SCOPE = dict(legacy.SCOPE, startup_pass=False)
QUANTITIES = ("J", "position", "tangent", "minimum", "position_vjp", "tangent_vjp")
save, ref, checked, read = legacy.save, legacy.ref, legacy.checked, legacy.read
run_process = legacy.run_process


def sources(root):
    # Deferred so lightweight tests do not import or read the project predecessor.
    from block_native_reference_inputs import sources as bound_sources

    return bound_sources(root)


def matrix():
    return [
        dict(
            label=f"n{nbase}-q{ncoil}-block-native",
            nbase=nbase,
            order=order,
            ncoil=ncoil,
            backend="block-native",
        )
        for nbase, order in ((6, 5), (8, 7))
        for ncoil in (256, 512)
    ]


def zero_kernel_work():
    return {key: dict(attempted=0, completed=0) for key in QUANTITIES}


def expected_kernel_work(case, state_count):
    if type(state_count) is not int or not 0 <= state_count <= 13:
        raise ValueError("registered complete-state prefix required")
    states = legacy.states(np.zeros(case["nbase"] * 3 * (2 * case["order"] + 1)))[:state_count]
    nphysical = 4 * case["nbase"]
    gradients = sum(state["gradient"] for state in states)
    minima = sum(state["label"] in ("seed", "changed-base", "restored-seed") for state in states)
    totals = dict(
        J=state_count * nphysical * 64,
        position=gradients * nphysical * 64,
        tangent=gradients * nphysical * 64,
        minimum=minima * nphysical * 64,
        position_vjp=gradients * nphysical,
        tangent_vjp=gradients * nphysical,
    )
    return {key: dict(attempted=value, completed=value) for key, value in totals.items()}


def require_kernel_work(actual, expected):
    if (
        not isinstance(actual, dict)
        or set(actual) != set(expected)
        or any(
            not isinstance(actual[key], dict)
            or set(actual[key]) != {"attempted", "completed"}
            or any(
                type(actual[key][kind]) is not int
                or actual[key][kind] < 0
                or actual[key][kind] != value
                for kind, value in expected[key].items()
            )
            for key in expected
        )
    ):
        raise ValueError("exact typed kernel-work accounting required")


class ProgressLog:
    """Append-only history plus one atomic in-flight reservation, never a raw-state overwrite."""

    def __init__(self, directory, parent_pid=None, started=None):
        self.history = directory / "kernel-progress.jsonl"
        self.inflight = directory / "kernel-inflight.json"
        with self.history.open("x"):
            pass
        self.state_index, self.state_label, self.count = None, "model-initialization", 0
        self.last = None
        self.parent_pid, self.started = parent_pid, started

    def __call__(self, event):
        if event.get("status") == "reserved" and self.parent_pid is not None:
            live_parent(self.parent_pid, self.started)
        record = legacy.builtin(
            dict(
                state_index=self.state_index,
                state_label=self.state_label,
                event=event,
                monotonic=time.monotonic(),
            )
        )
        encoded = json.dumps(record, sort_keys=True, allow_nan=False) + "\n"
        with self.history.open("a") as stream:
            stream.write(encoded)
            stream.flush()
        self.count += 1
        self.last = copy.deepcopy(record)
        save(self.inflight, record)

    def references(self):
        result = dict(kernel_progress=ref(self.history), kernel_progress_events=self.count)
        if self.inflight.exists():
            result["kernel_inflight"] = ref(self.inflight)
        return result


def live_parent(parent_pid, started):
    if type(parent_pid) is not int or os.getppid() != parent_pid:
        raise RuntimeError("owned parent changed; no additional native work permitted")
    legacy.deadline(started)


def make_model(case, progress_callback):
    from simsopt.field.coil import apply_symmetries_to_curves
    from simsopt.geo import CurveCurveDistance, SurfaceRZFourier, create_equally_spaced_curves

    from fusion_baselines.block_native_coil_surface import BlockNativeCurveSurfaceDistance

    # Exact original numerical construction, with only the CP execution primitive changed.
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
    points, normals = (
        surface.gamma().reshape((-1, 3)).copy(),
        surface.normal().reshape((-1, 3)).copy(),
    )
    cp = BlockNativeCurveSurfaceDistance(
        physical,
        points,
        normals,
        minimum_distance=0.08,
        block_size=256,
        progress_callback=progress_callback,
    )
    cc = CurveCurveDistance(physical, 0.06, num_basecurves=len(physical))
    names = legacy.local_names(case["order"])
    if len(physical) != 4 * case["nbase"] or points.shape != (128**2, 3):
        raise ValueError("complete registered physical/grid matrix required")
    for curve in base:
        if set(curve.local_dof_names) != set(names) or len(curve.local_dof_names) != len(names):
            raise ValueError("all and only registered named Fourier DOFs required")
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


def metadata(case, model):
    return dict(
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
        names=[f"coil[{i}]/{name}" for i in range(case["nbase"]) for name in model["local_names"]],
        native_local_names=[list(curve.local_dof_names) for curve in model["base"]],
        physical=[
            dict(base_index=i, period=period, flip=flip)
            for period in range(2)
            for flip in (False, True)
            for i in range(case["nbase"])
        ],
        parameter_period=1.0,
        surface_normal="unnormalized parameter normal",
    )


def worker(config_path):
    config = read(config_path)
    case, output = config["case"], Path(config["output"])
    if (
        case not in matrix()
        or config["source"]["matrix"] != matrix()
        or type(config["parent_pid"]) is not int
        or config["parent_pid"] != os.getppid()
        or not output.is_absolute()
        or Path(config_path).resolve() != output / "config.json"
        or any(os.environ.get(key) != "1" for key in THREADS)
    ):
        raise ValueError("registered source matrix, owned parent and single-thread worker required")
    started = config["started_monotonic"]
    rows, attempts, model, progress = [], [], None, None
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
    try:
        legacy.deadline(started)
        if sources(ROOT) != config["source"]:
            raise ValueError("worker source binding changed before startup")
        live_parent(config["parent_pid"], started)
        progress = ProgressLog(output, config["parent_pid"], started)
        save(output / "model-attempt.json", dict(case=case, started_monotonic=time.monotonic()))
        model = make_model(case, progress)
        require_kernel_work(model["cp"].kernel_work(), zero_kernel_work())
        seed = legacy.get_x(model)
        save(output / "metadata.json", metadata(case, model))
        surface_ref = legacy.arrays(
            output / "surface.npz", dict(points=model["points"], normals=model["normals"])
        )
        save(
            output / "model.json",
            dict(
                metadata=ref(output / "metadata.json"),
                surface=surface_ref,
                block_size=256,
                blocks=64,
                block_weight=1 / 64,
                kernel_work=model["cp"].kernel_work(),
            ),
        )
        for index, state in enumerate(legacy.states(seed)):
            live_parent(config["parent_pid"], started)
            progress.state_index, progress.state_label = index, state["label"]
            attempt = dict(
                index=index,
                label=state["label"],
                gradient=state["gradient"],
                started_monotonic=time.monotonic(),
                work_before=work,
                kernel_work_before=model["cp"].kernel_work(),
                kernel_progress_events_before=progress.count,
            )
            path = output / f"attempt-{index:02d}.json"
            save(path, attempt)
            attempts.append(ref(path))
            metrics, raw = legacy.evaluate(
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
            raw_ref = legacy.arrays(output / f"raw-{index:02d}.npz", raw)
            row = dict(
                index=index,
                label=state["label"],
                gradient=state["gradient"],
                metrics=metrics,
                arrays=raw_ref,
                work=work,
                attempt=attempts[-1],
                kernel_work=model["cp"].kernel_work(),
                kernel_progress_events=progress.count,
                ended_monotonic=time.monotonic(),
            )
            save(output / f"raw-{index:02d}.json", row)
            legacy.deadline(started)
            rows.append(ref(output / f"raw-{index:02d}.json"))
            save(
                output / "checkpoint.json",
                dict(
                    rows=rows,
                    work=work,
                    kernel_work=model["cp"].kernel_work(),
                    kernel_progress_events=progress.count,
                ),
            )
        after = sources(ROOT)
        if after != config["source"]:
            raise ValueError("worker source binding changed during computation")
        elapsed, rss = legacy.deadline(started), legacy.peak_rss_bytes()
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
                model=ref(output / "model.json"),
                rows=rows,
                attempts=attempts,
                work=work,
                kernel_work=model["cp"].kernel_work(),
                **progress.references(),
                ended_monotonic=time.monotonic(),
                elapsed_seconds=elapsed,
                peak_rss_bytes=rss,
                rss_pass=rss <= legacy.MAX_RSS_BYTES,
                threads={key: os.environ[key] for key in THREADS},
                scope=SCOPE,
            ),
        )
        return 0
    except Exception as error:
        partial = dict(
            status="failed",
            error_type=type(error).__name__,
            error=str(error),
            work=work,
            completed_rows=rows,
            attempts=attempts,
            elapsed_seconds=time.monotonic() - started,
            peak_rss_bytes=legacy.peak_rss_bytes(),
            scope=SCOPE,
        )
        if model is not None:
            partial["kernel_work"] = model["cp"].kernel_work()
        if progress is not None:
            partial.update(progress.references())
        save(output / "worker-error.json", partial)
        return 1


def completed_worker(process, document, case, source, started):
    if document.get("scope") != SCOPE or any(
        type(document["scope"][key]) is not type(value) for key, value in SCOPE.items()
    ):
        raise ValueError("exact no-field/no-admission scope required")
    # All old timing/RSS/process gates remain intact; only this additive scope key differs.
    legacy.completed_worker(process, dict(document, scope=legacy.SCOPE), case, source, started)


def reservation(phase):
    result = dict.fromkeys(QUANTITIES, 0)
    if phase == "J":
        result["J"] = 64
    elif phase == "dJ":
        result.update(position=64, tangent=64, position_vjp=1, tangent_vjp=1)
    elif phase == "minimum":
        result["minimum"] = 64
    else:
        raise ValueError("registered native block phase required")
    return result


def kernel_checks(document):
    case = document["case"]
    rows = [read(checked(item)) for item in document["rows"]]
    require_kernel_work(document["kernel_work"], expected_kernel_work(case, 13))
    events = [
        json.loads(line) for line in checked(document["kernel_progress"]).read_text().splitlines()
    ]
    if (
        not events
        or document["kernel_progress_events"] != len(events)
        or read(checked(document["kernel_inflight"])) != events[-1]
    ):
        raise ValueError("complete bound kernel history and exact final in-flight record required")
    current, cursor, event_index, previous_clock = zero_kernel_work(), 0, 0, 0.0
    worker_end = document["ended_monotonic"]
    if type(worker_end) not in (float, int) or not np.isfinite(worker_end) or worker_end < 0:
        raise ValueError("finite nonnegative worker completion clock required")
    for index, row in enumerate(rows):
        attempt = read(checked(document["attempts"][index]))
        if (
            row["attempt"] != document["attempts"][index]
            or type(row["index"]) is not int
            or row["index"] != index
            or type(attempt["index"]) is not int
            or attempt["index"] != index
            or attempt["label"] != row["label"]
            or type(row["gradient"]) is not bool
            or attempt["gradient"] is not row["gradient"]
        ):
            raise ValueError("source-bound public attempt required")
        attempt_start, row_end = attempt["started_monotonic"], row["ended_monotonic"]
        if (
            any(
                type(value) not in (float, int) or not np.isfinite(value)
                for value in (attempt_start, row_end)
            )
            or not previous_clock <= attempt_start <= row_end <= worker_end
        ):
            raise ValueError("ordered attempt/raw/worker completion clocks required")
        require_kernel_work(attempt["kernel_work_before"], expected_kernel_work(case, index))
        if attempt["kernel_progress_events_before"] != cursor:
            raise ValueError("exact pre-state history prefix required")
        phases = ["J"] + (["dJ"] if row["gradient"] else [])
        if row["label"] in ("seed", "changed-base", "restored-seed"):
            phases.append("minimum")
        for phase in phases:
            reserved = reservation(phase)
            for curve_index in range(4 * case["nbase"]):
                upper = {
                    q: {kind: current[q][kind] + reserved[q] for kind in ("attempted", "completed")}
                    for q in QUANTITIES
                }
                for status in ("reserved", "completed"):
                    if cursor >= len(events):
                        raise ValueError("kernel history truncated")
                    record = events[cursor]
                    event = record["event"]
                    if (
                        type(record["state_index"]) is not int
                        or record["state_index"] != index
                        or record["state_label"] != row["label"]
                        or type(event["index"]) is not int
                        or event["index"] != event_index
                        or type(event["curve_index"]) is not int
                        or event["curve_index"] != curve_index
                        or event["phase"] != phase
                        or event["status"] != status
                        or event["reservation"] != reserved
                        or any(type(value) is not int for value in event["reservation"].values())
                    ):
                        raise ValueError(
                            "complete exact phase/curve reservation and outcome order required"
                        )
                    require_kernel_work(event["work_before"], current)
                    require_kernel_work(event["upper_work"], upper)
                    require_kernel_work(event["work"], current if status == "reserved" else upper)
                    if (
                        type(record["monotonic"]) not in (float, int)
                        or not np.isfinite(record["monotonic"])
                        or not max(previous_clock, attempt_start) <= record["monotonic"] <= row_end
                    ):
                        raise ValueError(
                            "finite monotone progress within attempt/raw completion required"
                        )
                    previous_clock = record["monotonic"]
                    cursor += 1
                current, event_index = upper, event_index + 1
        require_kernel_work(row["kernel_work"], expected_kernel_work(case, index + 1))
        if row["kernel_progress_events"] != cursor:
            raise ValueError("exact post-state kernel-history prefix required")
        previous_clock = row_end
    if cursor != len(events) or len(rows) != 13 or len(document["attempts"]) != 13:
        raise ValueError("all and only 13 complete states and their native block work required")
    return dict(
        all_pass=True,
        public_states=13,
        curve_phase_reservations=event_index,
        progress_events=cursor,
        kernel_work=current,
    )


def historical_comparisons(document, source):
    case = document["case"]
    result = []
    for backend in ("native", "sparse"):
        label = f"n{case['nbase']}-q{case['ncoil']}-{backend}"
        old_ref = source["old_workers"][label]
        old = read(checked(old_ref))
        comparison = legacy.compare_pair(old, document)
        if len(comparison["comparisons"]) != 42:
            raise ValueError("exactly 42 comparisons to each unchanged backend required")
        result.append(dict(backend=backend, old_worker=old_ref, **comparison))
    return result


def _qualify(output):
    before = sources(ROOT)
    if before["matrix"] != matrix():
        raise ValueError("source-bound four-cell matrix differs")
    save(output / "source-before.json", before)
    space_check(output, 3 * GIB)
    env = dict(os.environ, **{key: "1" for key in THREADS})
    env["PYTHONPATH"] = str(ROOT / "src")
    env.setdefault("MPLCONFIGDIR", "/private/tmp/fusion-mpl-cache")
    rows = []
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
        row = dict(
            index=index,
            case=case,
            process=ref(directory / "process.json"),
            config=ref(directory / "config.json"),
            launch=ref(directory / "launch.json"),
            status="failed",
        )
        try:
            document = read(directory / "worker.json")
            completed_worker(process, document, case, before, started)
            row.update(worker=ref(directory / "worker.json"))
            checks = legacy.worker_checks(document)
            kernel = kernel_checks(document)
            comparisons = historical_comparisons(document, before)
            row.update(
                status="completed",
                checks=checks,
                kernel_checks=kernel,
                comparisons=comparisons,
                peak_rss_bytes=document["peak_rss_bytes"],
                resource_pass=document["peak_rss_bytes"] <= legacy.MAX_RSS_BYTES,
            )
        except Exception as error:
            row.update(error_type=type(error).__name__, error=str(error))
        row["retained"] = [ref(path) for path in sorted(directory.iterdir()) if path.is_file()]
        save(directory / "result.json", row)
        rows.append(ref(directory / "result.json"))
        save(output / "checkpoint.json", dict(rows=rows))
    after = sources(ROOT)
    save(output / "source-after.json", after)
    reports = [read(checked(item)) for item in rows]
    passed = bool(
        before == after
        and len(reports) == 4
        and all(
            row["status"] == "completed"
            and row["checks"]["all_pass"]
            and row["kernel_checks"]["all_pass"]
            and row["resource_pass"]
            and all(pair["all_pass"] for pair in row["comparisons"])
            for row in reports
        )
    )
    result = dict(
        schema_version=1,
        status="completed",
        kind="block-native-reference-qualification",
        source_before=before,
        source_after=after,
        source_unchanged=before == after,
        matrix=matrix(),
        rows=rows,
        old_reference=before["old_reference"],
        producer_checks_pass=passed,
        all_pass=False,
        bounded_reference_pass=False,
        independent_audit_pass=False,
        admission_status="pending-independent-audit",
        scope=SCOPE,
        limits=dict(
            wall_seconds=legacy.WALL_SECONDS,
            peak_rss_bytes=legacy.MAX_RSS_BYTES,
            parent_poll_seconds=legacy.POLL_SECONDS,
            termination_grace_seconds=5,
        ),
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
        save(
            output / "terminal-error.json",
            dict(status="failed", error_type=type(error).__name__, error=str(error), scope=SCOPE),
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--raw", type=Path)
    group.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker is not None:
        return worker(args.worker)
    result = qualify(args.raw)
    print(
        json.dumps(
            dict(
                status=result["status"],
                producer_checks_pass=result["producer_checks_pass"],
                bounded_reference_pass=result["bounded_reference_pass"],
                run=ref(args.raw / "run.json"),
            ),
            allow_nan=False,
        )
    )
    return 0 if result["producer_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
